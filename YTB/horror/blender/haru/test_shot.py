"""5-second test shot: Haru stands facing the wall, breathes, looks back over her right shoulder at us, worried, and blinks.

Stop motion: a new pose every 2 frames (24 fps timeline, CONSTANT keys), and a clay boil (the bump pattern and the lumps
shift slightly on every new pose). Run after build_haru.build() and stage():
    ns = {}; exec(open(TEST_SHOT).read(), ns); ns['setup'](ns_build)
Render headless:  blender -b haru_test.blend -a   (frame_step 2; post with ffmpeg at 12 fps -> 24 fps)
"""
import bpy, math, random
from mathutils import Vector

FPS, SECONDS = 24, 5
TURN = [('hips', -10), ('spine', -22), ('chest', -36), ('neck', -48), ('head', -38)]  # degrees about z, over the right shoulder


def ease(t):
    t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)


def curve(f):
    """turn amount 0..1 with a small overshoot and settle (frames 30 to 76)"""
    if f < 30: return 0.0
    if f < 62: return ease((f - 30) / 32) * 1.04
    if f < 76: return 1.04 - 0.04 * ease((f - 62) / 14)
    return 1.0


def setup(B, out_dir):
    sc = bpy.context.scene
    rig = bpy.data.objects['haru_rig']
    rig.rotation_euler = (0, 0, math.pi)                     # she faces the wall; the camera sees her back three-quarters
    sc.frame_start, sc.frame_end, sc.frame_step = 1, FPS * SECONDS, 2
    sc.render.fps = FPS
    cam = bpy.data.objects['cam_main']
    cam.location = (0.72, -2.25, 1.0); B['look_at'](cam, (0.0, 0.0, 0.8))
    cam.data.lens = 50; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.8
    cam.data.dof.focus_distance = (Vector((0, 0, 1.05)) - cam.location).length
    sc.cycles.samples = 64

    if rig.animation_data: rig.animation_data_clear()
    face = [o for o in bpy.data.collections['Haru'].objects if o.type == 'MESH' and o.data.shape_keys]
    for o in face:
        if o.data.shape_keys.animation_data: o.data.shape_keys.animation_data_clear()
    mats = [m for m in bpy.data.materials if m.name.startswith('clay_') and m.node_tree and m.node_tree.nodes.get('boil')]
    for m in mats:
        if m.node_tree.animation_data: m.node_tree.animation_data_clear()
    lumps = [md for o in bpy.data.collections['Haru'].objects if o.type == 'MESH' for md in o.modifiers if md.type == 'DISPLACE']
    rnd = random.Random(7)

    for f in range(1, FPS * SECONDS + 1, 2):                 # on twos
        sc.frame_set(f)
        B['rest'](rig)
        t = curve(f)
        breath = math.sin(f / FPS * 2 * math.pi / 2.6)       # one breath every 2.6 s
        B['rot_arm_space'](rig, 'chest', (1, 0, 0), 1.2 * breath)
        B['rot_arm_space'](rig, 'head', (1, 0, 0), -0.8 * breath - 10 * t)   # chin lifts as she looks back, clear of the hood collar
        B['rot_arm_space'](rig, 'neck', (1, 0, 0), -4 * t)
        for bone, deg in TURN:
            B['rot_arm_space'](rig, bone, (0, 0, 1), deg * t)
        for side, tag in ((1, 'L'), (-1, 'R')):                             # arms hang, the right one swings back a bit with the turn
            B['rot_arm_space'](rig, 'upper_arm.' + tag, (1, 0, 0), (-6 if tag == 'R' else 3) * t)
        for pb in rig.pose.bones:
            pb.keyframe_insert('rotation_quaternion', frame=f)
        # face: worried as the turn lands, one blink while looking at us
        worried = ease((f - 48) / 16)
        blink = {81: 0.5, 83: 1.0, 85: 1.0, 87: 0.4}.get(f, 0.0)
        for kb in B['set_expr']({'face': face}, blink=blink, worried=worried, frown=worried * 0.7):
            kb.keyframe_insert('value', frame=f)
        # boil: the clay surface shifts a little on every new pose
        for m in mats:
            mp = m.node_tree.nodes['boil']
            mp.inputs['Location'].default_value = (rnd.uniform(-1, 1) * 0.004, rnd.uniform(-1, 1) * 0.004, rnd.uniform(-1, 1) * 0.004)
            mp.inputs['Location'].keyframe_insert('default_value', frame=f)
        for md in lumps:
            md.mid_level = 0.5 + rnd.uniform(-1, 1) * 0.08
            md.keyframe_insert('mid_level', frame=f)

    for idb in [rig] + [o.data.shape_keys for o in face] + [m.node_tree for m in mats] + \
               [o for o in bpy.data.collections['Haru'].objects if o.type == 'MESH']:
        ad = getattr(idb, 'animation_data', None)
        if ad and ad.action:
            for fc in action_fcurves(ad.action):
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    sc.frame_set(1)
    sc.render.filepath = out_dir.rstrip('\\/') + '/f_'
    sc.render.image_settings.file_format = 'PNG'
    return {'frames': len(range(1, FPS * SECONDS + 1, 2))}


def action_fcurves(action):
    """fcurves of an action in Blender 4.4+ (layered actions) and older versions"""
    if hasattr(action, 'fcurves') and len(action.fcurves): return list(action.fcurves)
    out = []
    for layer in getattr(action, 'layers', []):
        for strip in layer.strips:
            for bag in getattr(strip, 'channelbags', []):
                out += list(bag.fcurves)
    return out
