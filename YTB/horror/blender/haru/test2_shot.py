"""Test 2 (about 17 s): Haru asleep on the floor -> wakes -> sits up, looks around -> hugs her knees -> crouches -> stands ->
walks, glances back -> runs -> stops, turns to us -> camera zooms in -> expressions -> pulls out -> jumps, arms up.

Stop motion on twos with a clay boil. Every pose is put ON the floor: the lowest point of her evaluated meshes is measured
and the rig lifted or lowered to touch z = 0 (plus a lift for the run's flight and the jump).
Run after build_haru.build() and stage(width=8):  ns = {}; exec(open(PATH).read(), ns); ns['setup'](B, OUT_DIR)
"""
import bpy, math, random
import numpy as np
from mathutils import Vector

FPS = 24
END = 17.0
AX = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1)}

# ---------------------------------------------------------------- pose library
# {(bone, axis): degrees}, relative to the parent's frame, armature axes (her forward is -y, her left +x).
# x: +leans the spine/head forward, +moves a hanging limb back, +bends the knee; elbows bend with -x; foot -x = toes up.
# y on an upper arm: + brings the left arm in (-, the right).
STAND = {}
# on her back: legs lowered and head tipped back so heels, bottom, back and head all rest on the floor
LIE = {('hips', 'x'): -90, ('head', 'x'): -2, ('neck', 'x'): -4, ('thigh.L', 'x'): 3.5, ('thigh.R', 'x'): 3.5,
       ('upper_arm.L', 'y'): -8, ('upper_arm.R', 'y'): 8,
       ('forearm.L', 'x'): -8, ('forearm.R', 'x'): -8, ('foot.L', 'x'): 12, ('foot.R', 'x'): 12}
SIT = {('hips', 'x'): -8, ('thigh.L', 'x'): -82, ('thigh.R', 'x'): -82, ('chest', 'x'): 6, ('head', 'x'): 4,
       ('upper_arm.L', 'x'): 30, ('upper_arm.R', 'x'): 30, ('upper_arm.L', 'y'): -10, ('upper_arm.R', 'y'): 10,
       ('foot.L', 'x'): 10, ('foot.R', 'x'): 10}
# sitting ON the floor, knees up by the chest: thighs about 60 deg above horizontal, shins vertical, feet flat
HUG = {('hips', 'x'): 14, ('chest', 'x'): 10, ('head', 'x'): 6,
       ('thigh.L', 'x'): -162, ('thigh.R', 'x'): -162, ('shin.L', 'x'): 148, ('shin.R', 'x'): 148,
       ('thigh.L', 'y'): -4, ('thigh.R', 'y'): 4, ('foot.L', 'x'): 0, ('foot.R', 'x'): 0,
       ('upper_arm.L', 'x'): -42, ('upper_arm.R', 'x'): -42, ('upper_arm.L', 'y'): -6, ('upper_arm.R', 'y'): 6,
       ('forearm.L', 'x'): -30, ('forearm.R', 'x'): -30, ('forearm.L', 'z'): -62, ('forearm.R', 'z'): 62}   # forearms wrap round the shins
CROUCH = {('hips', 'x'): 38, ('spine', 'x'): 5, ('chest', 'x'): 5, ('head', 'x'): -28,
          ('thigh.L', 'x'): -125, ('thigh.R', 'x'): -125, ('shin.L', 'x'): 128, ('shin.R', 'x'): 128,
          ('foot.L', 'x'): -41, ('foot.R', 'x'): -41,
          ('upper_arm.L', 'x'): -38, ('upper_arm.R', 'x'): -38, ('forearm.L', 'x'): -25, ('forearm.R', 'x'): -25}
JUMP = {('upper_arm.L', 'y'): -150, ('upper_arm.R', 'y'): 150, ('forearm.L', 'x'): -12, ('forearm.R', 'x'): -12,
        ('thigh.L', 'x'): -28, ('thigh.R', 'x'): 12, ('shin.L', 'x'): 75, ('shin.R', 'x'): 88,
        ('foot.L', 'x'): 22, ('foot.R', 'x'): 22, ('head', 'x'): -10, ('chest', 'x'): -6}
DIP = {('hips', 'x'): 22, ('thigh.L', 'x'): -55, ('thigh.R', 'x'): -55, ('shin.L', 'x'): 62, ('shin.R', 'x'): 62,
       ('foot.L', 'x'): -29, ('foot.R', 'x'): -29, ('upper_arm.L', 'x'): 35, ('upper_arm.R', 'x'): 35,
       ('head', 'x'): -12}


def walk(p):
    s, c = math.sin(2 * math.pi * p), math.cos(2 * math.pi * p)
    kl = 6 + 34 * max(0.0, c) ** 1.5; kr = 6 + 34 * max(0.0, -c) ** 1.5
    return {('thigh.L', 'x'): -22 * s, ('thigh.R', 'x'): 22 * s, ('shin.L', 'x'): kl, ('shin.R', 'x'): kr,
            ('foot.L', 'x'): -0.45 * (-22 * s + kl), ('foot.R', 'x'): -0.45 * (22 * s + kr),
            ('upper_arm.L', 'x'): 16 * s, ('upper_arm.R', 'x'): -16 * s, ('forearm.L', 'x'): -12, ('forearm.R', 'x'): -12,
            ('hips', 'z'): 5 * s, ('chest', 'z'): -6 * s, ('hips', 'x'): 3, ('head', 'x'): -2}


def run(p):
    s, c = math.sin(2 * math.pi * p), math.cos(2 * math.pi * p)
    kl = 25 + 85 * max(0.0, c) ** 1.2; kr = 25 + 85 * max(0.0, -c) ** 1.2
    tl, tr = -12 - 42 * s, -12 + 42 * s
    return {('thigh.L', 'x'): tl, ('thigh.R', 'x'): tr, ('shin.L', 'x'): kl, ('shin.R', 'x'): kr,
            ('foot.L', 'x'): -0.4 * (tl + kl) + 10, ('foot.R', 'x'): -0.4 * (tr + kr) + 10,
            ('upper_arm.L', 'x'): 38 * s, ('upper_arm.R', 'x'): -38 * s, ('forearm.L', 'x'): -80, ('forearm.R', 'x'): -80,
            ('upper_arm.L', 'y'): -8, ('upper_arm.R', 'y'): 8,
            ('hips', 'x'): 14, ('chest', 'x'): 6, ('head', 'x'): -14, ('hips', 'z'): 7 * s, ('chest', 'z'): -10 * s}


def mix(a, b, t):
    return {k: a.get(k, 0.0) * (1 - t) + b.get(k, 0.0) * t for k in set(a) | set(b)}


def add(a, b):
    out = dict(a)
    for k, v in b.items(): out[k] = out.get(k, 0.0) + v
    return out


def ease(t):
    t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)


def seg(t, t0, t1):
    return ease((t - t0) / (t1 - t0))


# ---------------------------------------------------------------- timeline
WALK_T, RUN_T = 1.0, 0.62           # seconds per cycle (two steps)
X0 = -3.4                           # where she lies


def speed(t):
    if t < 4.6: return 0.0
    if t < 7.0: return 0.72 * seg(t, 4.6, 4.9)
    if t < 8.9: return 0.72 + (2.1 - 0.72) * seg(t, 7.0, 7.5)
    if t < 9.5: return 2.1 * (1 - seg(t, 8.9, 9.5))
    return 0.0


def body(t, phase):
    """pose spec, extra lift (m), facing angle (deg, +90 = toward +x)"""
    lift, face = 0.0, 90.0
    breath = math.sin(t * 2 * math.pi / 2.6)
    if t < 1.3: spec = LIE
    elif t < 2.1: spec = mix(LIE, SIT, seg(t, 1.3, 2.1))
    elif t < 2.9:
        spec = add(SIT, {('head', 'z'): 38 * seg(t, 2.15, 2.4) - 76 * seg(t, 2.5, 2.75) + 38 * seg(t, 2.78, 2.9),
                         ('neck', 'z'): 10 * seg(t, 2.15, 2.4) - 20 * seg(t, 2.5, 2.75) + 10 * seg(t, 2.78, 2.9)})
    elif t < 3.4: spec = mix(SIT, HUG, seg(t, 2.9, 3.4))
    elif t < 3.9: spec = mix(HUG, CROUCH, seg(t, 3.4, 3.9))
    elif t < 4.5: spec = mix(CROUCH, STAND, seg(t, 3.9, 4.5))
    elif t < 7.0:
        spec = mix(STAND, walk(phase), seg(t, 4.5, 4.8))
        g = seg(t, 6.15, 6.45) - seg(t, 6.7, 6.95)                       # glance back over the right shoulder
        spec = add(spec, {('head', 'z'): -62 * g, ('neck', 'z'): -25 * g, ('chest', 'z'): -12 * g, ('head', 'x'): -6 * g})
    elif t < 8.9: spec = mix(walk(phase), run(phase), seg(t, 7.0, 7.3)); lift = 0.035 * abs(math.sin(2 * math.pi * phase)) * seg(t, 7.2, 7.5)
    elif t < 9.5: spec = mix(run(phase), STAND, seg(t, 8.9, 9.5))
    elif t < 10.1: spec = STAND; face = 90 * (1 - seg(t, 9.5, 10.1))
    elif t < 15.35:
        face = 0
        tilts = [(0, 0), (6, 0), (-5, 4), (0, -8), (4, 6), (-3, -5), (6, 3), (-6, -4), (0, 8), (0, 0)]
        i = int((t - 11.3) / 0.45) if t >= 11.3 else 0; i = max(0, min(i, len(tilts) - 1))
        spec = {('head', 'y'): tilts[i][0], ('head', 'x'): tilts[i][1]}
    elif t < 15.9: face = 0; spec = mix(STAND, DIP, seg(t, 15.55, 15.9))
    elif t < 16.65:
        face = 0; u = (t - 15.9) / 0.75
        spec = mix(DIP, JUMP, seg(t, 15.9, 16.05)) if t < 16.4 else mix(JUMP, DIP, seg(t, 16.4, 16.65))
        lift = 0.3 * max(0.0, 4 * u * (1 - u)) if 0.08 < u < 0.92 else 0.0
    else: face = 0; spec = mix(DIP, STAND, seg(t, 16.65, 16.95))
    spec = add(spec, {('chest', 'x'): 1.2 * breath * (1 if t >= 1.3 else 0.6)})
    return spec, lift, face


EXPR_LIST = ['smile', 'happy', 'surprised', 'sad', 'angry', 'suspicious', 'scared', 'terrified', 'stare']
BLINKS = [3.15, 4.4, 5.6, 9.7, 10.4, 15.6]


def face(t):
    """(preset a, preset b, t) blend plus an extra blink"""
    if t < 0.9: e = ('sleep', None, 0)
    elif t < 1.3: e = ('sleep', 'surprised', seg(t, 0.9, 1.05))
    elif t < 2.1: e = ('surprised', 'worried', seg(t, 1.3, 1.8))
    elif t < 2.9: e = ('worried', None, 0)
    elif t < 3.9: e = ('worried', 'sad', seg(t, 2.9, 3.3))
    elif t < 4.5: e = ('sad', 'neutral', seg(t, 3.9, 4.4))
    elif t < 6.15: e = ('neutral', 'suspicious', seg(t, 5.2, 5.6))
    elif t < 7.0: e = ('suspicious', 'scared', seg(t, 6.3, 6.45))
    elif t < 8.9: e = ('scared', 'terrified', seg(t, 7.0, 7.25))
    elif t < 10.1: e = ('terrified', 'scared', seg(t, 8.9, 9.3))
    elif t < 11.3: e = ('scared', 'relieved', seg(t, 10.3, 10.8))
    elif t < 15.35:
        i = min(int((t - 11.3) / 0.45), len(EXPR_LIST) - 1)
        prev = EXPR_LIST[i - 1] if i else 'relieved'
        e = (prev, EXPR_LIST[i], seg(t, 11.3 + i * 0.45, 11.3 + i * 0.45 + 0.09))
    elif t < 15.9: e = ('stare', 'smile', seg(t, 15.35, 15.6))
    else: e = ('smile', 'happy', seg(t, 15.9, 16.0))
    bl = max([1.0 if abs(t - b) < 0.045 else (0.45 if abs(t - b) < 0.13 else 0.0) for b in BLINKS] + [0.0])
    return e, bl


# ---------------------------------------------------------------- helpers
def apply(B, rig, spec):
    B['rest'](rig)
    order = ['root', 'hips', 'spine', 'chest', 'neck', 'head']
    bones = order + [b.name for b in rig.pose.bones if b.name not in order]
    for bone in bones:
        for ax in ('y', 'x', 'z'):
            deg = spec.get((bone, ax))
            if deg: B['rot_arm_space'](rig, bone, AX[ax], deg)


def lowest(meshes):
    dg = bpy.context.evaluated_depsgraph_get(); lo = 9.0
    for ob in meshes:
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        n = len(me.vertices); co = np.empty(n * 3); me.vertices.foreach_get('co', co)
        M = np.array(ev.matrix_world)
        z = co.reshape(-1, 3) @ M[2, :3] + M[2, 3]
        lo = min(lo, float(z.min())); ev.to_mesh_clear()
    return lo


def action_fcurves(action):
    if hasattr(action, 'fcurves') and len(action.fcurves): return list(action.fcurves)
    out = []
    for layer in getattr(action, 'layers', []):
        for strip in layer.strips:
            for bag in getattr(strip, 'channelbags', []): out += list(bag.fcurves)
    return out


# ---------------------------------------------------------------- build the shot
def setup(B, out_dir, step=2):
    sc = bpy.context.scene; vl = bpy.context.view_layer
    col = bpy.data.collections['Haru']
    rig = bpy.data.objects['haru_rig']; cam = bpy.data.objects['cam_main']; lr = bpy.data.objects['light_rig']
    swing = bpy.data.objects.get('hair_swing')
    # what she rests on: everything but the face pieces and the soft parts (the hair squashes on the floor instead)
    meshes = [o for o in col.objects if o.type == 'MESH' and o.name not in B.get('SOFT', ()) and not o.name.startswith(
              ('haru_eye', 'haru_brow', 'haru_mouth', 'haru_catchlight', 'haru_nose'))]
    face_obs = [o for o in col.objects if o.type == 'MESH' and o.data.shape_keys]
    mats = [m for m in bpy.data.materials if m.name.startswith('clay_') and m.node_tree and m.node_tree.nodes.get('boil')]
    lumps = [md for o in col.objects if o.type == 'MESH' for md in o.modifiers if md.type == 'DISPLACE']
    anim_ids = [rig, cam, cam.data, lr] + ([swing] if swing else []) + [o.data.shape_keys for o in face_obs] + \
               [m.node_tree for m in mats] + [o for o in col.objects if o.type == 'MESH']
    for idb in anim_ids:
        if idb.animation_data: idb.animation_data_clear()

    frames = list(range(1, int(END * FPS) + 1, step))
    # pass 1: pose, put her on the floor, record everything (no keys yet, so nothing overrides the pose)
    rec = []; x = X0; phase = 0.0; prev_t = 0.0
    for f in frames:
        t = (f - 1) / FPS; dt = t - prev_t; prev_t = t
        v = speed(t); x += v * dt
        cyc = RUN_T if t >= 7.15 else WALK_T
        phase += dt / cyc
        spec, lift, facing = body(t, phase)
        rig.location = (x, 0, 0); rig.rotation_euler = (0, 0, math.radians(facing))
        apply(B, rig, spec); vl.update()
        z = -lowest(meshes) + lift
        rig.location.z = z; vl.update()
        head = rig.matrix_world @ rig.pose.bones['head'].head
        rec.append(dict(f=f, t=t, x=x, z=z, rot=math.radians(facing),
                        q={pb.name: pb.rotation_quaternion.copy() for pb in rig.pose.bones}, head=head.copy()))

    # camera: follows her x with a lag; wide (32 mm) -> zoom to her face (85 mm) -> back out for the jump
    lead = lambda t: -0.12 * (1 - seg(t, 1.3, 2.1)) + 0.22 * speed(t)    # centre the lying body; look ahead when moving
    cx = rec[0]['x'] + lead(0)
    rnd = random.Random(11)
    for r in rec:
        t = r['t']
        cx += (r['x'] + lead(t) - cx) * 0.45
        zoom = seg(t, 10.1, 11.3) - seg(t, 15.35, 15.75)
        h = r['head']
        low = 1 - seg(t, 1.6, 4.4)                       # low camera while she is on the floor, rising as she stands
        wide_loc = Vector((cx, -2.45, 0.8 - 0.3 * low)); wide_tgt = Vector((cx, 0, 0.62 - 0.37 * low))
        close_loc = Vector((h.x, -1.5, h.z + 0.02)); close_tgt = Vector((h.x, 0, h.z + 0.02))
        r['cam'] = wide_loc.lerp(close_loc, zoom); r['tgt'] = wide_tgt.lerp(close_tgt, zoom)
        r['lens'] = 32 + (85 - 32) * zoom
        r['focus'] = (r['cam'] - (h if zoom > 0.3 or t > 1.6 else Vector((r['x'], 0, 0.2)))).length

    # pass 2: keys (all CONSTANT: a new pose every `step` frames)
    for r in rec:
        f = r['f']
        rig.location = (r['x'], 0, r['z']); rig.rotation_euler = (0, 0, r['rot'])
        rig.keyframe_insert('location', frame=f); rig.keyframe_insert('rotation_euler', frame=f)
        for pb in rig.pose.bones:
            pb.rotation_quaternion = r['q'][pb.name]; pb.keyframe_insert('rotation_quaternion', frame=f)
        (a, b, tb), bl = face(r['t'])
        vals = B['expr_values'](a, b, tb, bl)
        for o in face_obs:
            for kb in o.data.shape_keys.key_blocks[1:]:
                kb.value = vals.get(kb.name, 0.0); kb.keyframe_insert('value', frame=f)
        cam.location = r['cam']; B['look_at'](cam, r['tgt'])
        cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
        cam.data.lens = r['lens']; cam.data.keyframe_insert('lens', frame=f)
        cam.data.dof.focus_distance = r['focus']; cam.data.dof.keyframe_insert('focus_distance', frame=f)
        lr.location = (cam.location.x if r['t'] < 10.1 else r['x'], 0, 0); lr.keyframe_insert('location', frame=f)
        if swing:   # hair ends trail behind when she moves, lag down on the way up of the jump, flick up on landing
            t = r['t']; u = (t - 15.9) / 0.75
            jz = (-0.05 if 0.1 < u < 0.5 else 0.035 if 0.5 <= u < 0.95 else 0.0) if 15.9 < t < 16.7 else 0.0
            wob = 0.006 * math.sin(t * 9.0) * min(1.0, speed(t))
            swing.location = (-0.045 * speed(t), wob, jz + 0.012 * min(1.0, speed(t) / 2.1))
            swing.keyframe_insert('location', frame=f)
        for m in mats:
            mp = m.node_tree.nodes['boil']
            mp.inputs['Location'].default_value = tuple(rnd.uniform(-1, 1) * 0.004 for _ in range(3))
            mp.inputs['Location'].keyframe_insert('default_value', frame=f)
        for md in lumps:
            md.mid_level = 0.5 + rnd.uniform(-1, 1) * 0.08; md.keyframe_insert('mid_level', frame=f)
    for idb in anim_ids:
        ad = getattr(idb, 'animation_data', None)
        if ad and ad.action:
            for fc in action_fcurves(ad.action):
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.8
    sc.camera = cam
    sc.frame_start, sc.frame_end, sc.frame_step = 1, frames[-1], step
    sc.render.fps = FPS
    sc.render.filepath = out_dir.rstrip('\\/') + '/f_'
    sc.render.image_settings.file_format = 'PNG'
    sc.frame_set(1)
    return {'poses': len(rec), 'x_end': round(rec[-1]['x'], 2), 'z_range': [round(min(r['z'] for r in rec), 3), round(max(r['z'] for r in rec), 3)]}
