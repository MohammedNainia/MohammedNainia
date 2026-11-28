"""The modular cast kit (library/kit, see library/MODULAR_CAST.md): build a character from a head, a body, a hairpiece
and outfit colours, all Tripo models in channel clay.

    import cast_kit as CK
    mika = CK.character('head_girl', 'body_child', CK.CHILD, 'child', (x, y, 0), 'mika',
                        hair='hair_mika', outfit=('#3d8c86', '#2f3a4f', '#eceae6'))

Standards: children 12.6 cm (Haru), women 16.5 cm, men 17.8 cm. The head model (crown to the bottom of its neck peg)
is 27% of the height for children and 19% for adults; 35% of it slides over the body's neck stump.
Hair: a hair source is a kit head wearing that hair (made from the head's own image in Artlist). The hair is cut out by
colour (dark texels), then moved onto the target head by matching the source head's skin bounds to the target head.
Outfit: the bodies wear a plain grey base; outfit=(top, trousers, shoes) recolours only the grey (low-saturation)
texels, by height, so skin (hands) keeps its colour."""
import bpy, bmesh, os, math
import mathutils
from mathutils import Vector
import haru_clay as HC
import clay_v3 as CV

KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'library', 'kit')
CHILD, WOMAN, MAN = 0.126, 0.165, 0.178
HEAD_FRAC = {'child': 0.27, 'adult': 0.19}
PEG = 0.35
SKIN = '#f3bf9f'              # Haru's rendered face: every kit head and hand is tinted to it
YAW = -90                     # Tripo GLBs import facing +x
# outfit zones as a share of the body's height (feet at 0): shoes below SHOE, trousers below WAIST, top above
SHOE, WAIST = 0.075, 0.52
HAIR_PUSH = 0.035           # hair sits this share of the head height further out than its source scalp


def load(name):
    """import library/kit/<name>.glb as one mesh, transforms applied, facing -y"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(KIT, name + '.glb'))
    new = [o for o in bpy.data.objects if o not in before]
    o = [x for x in new if x.type == 'MESH'][0]
    mw = o.matrix_world.copy()
    for x in new:
        if x is not o: bpy.data.objects.remove(x)
    o.parent = None; o.matrix_world = mathutils.Matrix.Identity(4)
    o.data.transform(mathutils.Matrix.Rotation(math.radians(YAW), 4, 'Z') @ mw)
    # Tripo splits vertices along every UV seam: weld them (UVs live on the loops, so they survive) so the mesh is one
    # closed skin for skinning, and the only open edges are ones we cut
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6 * max(o.dimensions))
    bm.to_mesh(o.data); bm.free()
    o.name = name
    return o


def bounds(o, verts=None):
    vs = [v.co for v in (verts if verts is not None else o.data.vertices)]
    return (Vector([min(v[i] for v in vs) for i in range(3)]), Vector([max(v[i] for v in vs) for i in range(3)]))


def width_at(o, z0, z1):
    xs = [v.co.x for v in o.data.vertices if z0 <= v.co.z <= z1]
    return (max(xs) - min(xs)) if xs else 0.0


def fit(o, height):
    """scale uniformly to this height, lowest point at z=0, centred on x/y"""
    lo, hi = bounds(o); k = height / (hi.z - lo.z)
    o.data.transform(mathutils.Matrix.Scale(k, 4) @ mathutils.Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)))


def _texture(o):
    for m in o.data.materials:
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image and 'color' in n.image.name.lower(): return n.image
    for m in o.data.materials:
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image: return n.image
    return None


def _face_colours(o):
    """sRGB colour of each face, sampled from the model's colour texture at the face's UVs"""
    import numpy as np
    img = _texture(o); w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(px); px = px.reshape(h, w, 4)
    uv = o.data.uv_layers.active.data; out = []
    for p in o.data.polygons:
        acc = np.zeros(3)
        for li in p.loop_indices:
            u, v = uv[li].uv; acc += px[int((v % 1) * (h - 1)), int((u % 1) * (w - 1)), :3]
        out.append(acc / p.loop_total)
    out = np.array(out)
    if not img.colorspace_settings.name.lower().startswith('srgb'):
        out = np.where(out <= 0.0031308, out * 12.92, 1.055 * out ** (1 / 2.4) - 0.055)
    return out


def hair(src, head):
    """cut the hair out of library/kit/<src>.glb (a kit head wearing hair) and fit it onto `head` (a kit head already
    fitted and placed). Returns the hair object."""
    s = load(src)
    col = _face_colours(s)
    lum = col @ [0.2126, 0.7152, 0.0722]
    sat = col.max(axis=1) - col.min(axis=1)
    is_hair = (lum < 0.40) | ((lum < 0.48) & (sat < 0.10))        # dark brown / black clay and its highlights, not the skin
    bm = bmesh.new(); bm.from_mesh(s.data); bm.faces.ensure_lookup_table()
    # a few rounds of majority smoothing so the eyes and brows (dark) don't come along, and hair edges stay whole
    hair_set = {f.index for f in bm.faces if is_hair[f.index]}
    for _ in range(5):
        nxt = set()
        for f in bm.faces:
            nb = {g.index for e in f.edges for g in e.link_faces if g is not f}
            k = sum(1 for g in nb if g in hair_set) / max(len(nb), 1)
            if (f.index in hair_set and k >= 0.34) or (f.index not in hair_set and k >= 0.5): nxt.add(f.index)
        hair_set = nxt
    skin_verts = [v.co.copy() for f in bm.faces if f.index not in hair_set for v in f.verts]
    # drop small islands (the brows, the eye whites)
    islands, seen = [], set()
    for f in bm.faces:
        if f.index not in hair_set or f.index in seen: continue
        st, isl = [f], []; seen.add(f.index)
        while st:
            x = st.pop(); isl.append(x.index)
            for e in x.edges:
                for g in e.link_faces:
                    if g.index in hair_set and g.index not in seen: seen.add(g.index); st.append(g)
        islands.append(isl)
    keep = set()
    big = max((len(i) for i in islands), default=0)
    for i in islands:
        if len(i) >= 0.05 * big: keep |= set(i)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    bm.to_mesh(s.data); bm.free()
    # map the source head onto the target head through the neck peg, which the image edit left unchanged: scale by
    # the peg's width, put the peg bottoms together, centre on the peg
    def peg(vs, z0, zt):
        sl = [v for v in vs if v.z <= z0 + 0.10 * zt]
        lo = Vector([min(v[i] for v in sl) for i in range(3)]); hi = Vector([max(v[i] for v in sl) for i in range(3)])
        return lo, hi
    sv = skin_verts; szlo = min(v.z for v in sv); szhi = max(v.z for v in sv)
    slo, shi = peg(sv, szlo, szhi - szlo)
    tv = [v.co for v in head.data.vertices]; tzlo = min(v.z for v in tv); tzhi = max(v.z for v in tv)
    tlo, thi = peg(tv, tzlo, tzhi - tzlo)
    k = ((thi.x - tlo.x) + (thi.y - tlo.y)) / ((shi.x - slo.x) + (shi.y - slo.y))
    T = (mathutils.Matrix.Translation(((tlo.x + thi.x) / 2, (tlo.y + thi.y) / 2, tzlo)) @ mathutils.Matrix.Scale(k, 4)
         @ mathutils.Matrix.Translation((-(slo.x + shi.x) / 2, -(slo.y + shi.y) / 2, -szlo)))
    s.data.transform(T)
    # the target head's scalp is not the source's: push the hair out from the head centre a little so no bald clay
    # pokes through it (3% of the head height, less toward the face)
    c = Vector(((tlo.x + thi.x) / 2, (tlo.y + thi.y) / 2, tzlo + 0.62 * (tzhi - tzlo)))
    push = HAIR_PUSH * (tzhi - tzlo)
    for v in s.data.vertices:
        d = v.co - c
        if d.length > 1e-9: v.co += d.normalized() * push
    # tuck the cut edge onto the skin: the boundary ring lands on the head surface, the next two rings blend toward it,
    # so the hair meets the face as pressed-on clay instead of a floating edge with a dark line under it
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromPolygons([v.co.copy() for v in head.data.vertices], [list(p.vertices) for p in head.data.polygons])
    bm = bmesh.new(); bm.from_mesh(s.data)
    ring = {v for v in bm.verts if v.is_boundary}; done = set(ring)
    rings = [ring]
    for _ in range(2):
        nxt = {e.other_vert(v) for v in rings[-1] for e in v.link_edges} - done
        done |= nxt; rings.append(nxt)
    for w, rg in zip((1.0, 0.55, 0.2), rings):
        for v in rg:
            hit = tree.find_nearest(v.co)
            if hit[0] is not None and hit[3] < 0.08 * (tzhi - tzlo):            # only edges that sit near the head
                tgt = hit[0] + hit[1] * 0.00015
                v.co = v.co.lerp(tgt, w)
    bm.to_mesh(s.data); bm.free()
    print(f'HAIR {src} -> {head.name}: scale {k:.3f}, edge verts tucked {len(rings[0])}', flush=True)
    s.location = head.location.copy(); s.name = src + '_on_' + head.name
    sol = s.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.0006; sol.offset = -1       # close the cut edges
    return s


def outfit_colours(body, top, pants, shoes):
    """recolour the grey base clothes of a kit body (after apply_textured_clay): only low-saturation texels change"""
    import numpy as np
    lo, hi = bounds(body); H = hi.z - lo.z
    # rest height of every vertex as a share of the body (0 at the soles): the zones follow the clay when it is posed
    a = body.data.attributes.get('rest_z') or body.data.attributes.new('rest_z', 'FLOAT', 'POINT')
    a.data.foreach_set('value', [(v.co.z - lo.z) / H for v in body.data.vertices])
    for m in body.data.materials:
        nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
        if tex is None: continue
        src = b.inputs['Base Color'].links[0].from_socket
        # grey level of the base clothes, so the new colour lands at its true value
        px = np.empty(tex.image.size[0] * tex.image.size[1] * 4, dtype=np.float32); tex.image.pixels.foreach_get(px)
        px = px.reshape(-1, 4)[:, :3]; sat = px.max(1) - px.min(1)
        grey = float(px[sat < 0.04].mean()) if (sat < 0.04).any() else 0.6
        hsv = nt.nodes.new('ShaderNodeSeparateColor'); hsv.mode = 'HSV'; nt.links.new(tex.outputs['Color'], hsv.inputs[0])
        def op(kind, a, c, clamp=True):
            n = nt.nodes.new('ShaderNodeMath'); n.operation = kind; n.use_clamp = clamp
            for i, x in enumerate((a, c)):
                if isinstance(x, (int, float)): n.inputs[i].default_value = x
                else: nt.links.new(x, n.inputs[i])
            return n.outputs[0]
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'               # 1 on grey, 0 on skin
        nt.links.new(hsv.outputs[1], mr.inputs['Value']); mr.inputs['From Min'].default_value = 0.18
        mr.inputs['From Max'].default_value = 0.32; mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
        mask = mr.outputs['Result']
        at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'rest_z'      # height share, written below
        z = at.outputs['Fac']
        def rgb(hexc): c = CV._lin(hexc); return (*[v / max(grey, 1e-3) for v in c], 1)
        m1 = nt.nodes.new('ShaderNodeMix'); m1.data_type = 'RGBA'
        nt.links.new(op('GREATER_THAN', z, SHOE), m1.inputs['Factor'])
        m1.inputs[6].default_value = rgb(shoes); m1.inputs[7].default_value = rgb(pants)
        m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'
        nt.links.new(op('GREATER_THAN', z, WAIST), m2.inputs['Factor'])
        nt.links.new(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = rgb(top)
        tint = nt.nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'
        nt.links.new(mask, tint.inputs['Factor']); nt.links.new(src, tint.inputs[6]); nt.links.new(m2.outputs[2], tint.inputs[7])
        nt.links.new(tint.outputs[2], b.inputs['Base Color'])


def character(head, body, total, kind, loc, label, hair_src=None, outfit=None, rigged=True):
    """head + body (+ hair, + outfit colours) at loc (feet), rigged (see rig / pose).
    Returns dict(head=, body=, hair=, rig=)."""
    h, b = load(head), load(body)
    hh = HEAD_FRAC[kind] * total
    fit(h, hh); fit(b, total - hh * (1 - PEG))
    blo, bhi = bounds(b)
    x, y, z = loc
    h.location = (x, y, z + bhi.z - PEG * hh); b.location = (x, y, z)
    bpy.context.view_layer.update()
    HC.apply_textured_clay([h], name=label + '_head', height=total, skin=SKIN)
    HC.apply_textured_clay([b], name=label + '_body', height=total)
    if outfit: outfit_colours(b, *outfit)
    out = dict(head=h, body=b, hair=None)
    if hair_src:
        hr = hair(hair_src, h)
        HC.apply_textured_clay([hr], name=label + '_hair', height=total, lumps=False)
        out['hair'] = hr
    if rigged:
        bpy.context.view_layer.update(); rig(out, label)
    return out


# ---------------------------------------------------------------- rig
# joint heights as a share of the body mesh height (feet at 0, top of the neck stump at 1), measured on the kit
# bodies in A-pose; x positions are read from the mesh itself
JOINTS = dict(ankle=0.05, knee=0.27, hip=0.47, pelvis=0.50, chest=0.72, neck=0.88, shoulder=0.85)


def _slice(vs, z0, z1, side=0):
    sel = [v for v in vs if z0 <= v.z <= z1 and (side == 0 or v.x * side > 0)]
    return sel


def _centre(vs):
    n = max(len(vs), 1)
    return Vector((sum(v.x for v in vs) / n, sum(v.y for v in vs) / n, sum(v.z for v in vs) / n))


def rig(c, label):
    """give a kit character (dict from character()) a skeleton: root, hips, spine, chest, neck, head, and per side
    thigh, shin, foot, upper_arm, forearm, hand (.L is the character's left, +x). The body clay is skinned to it with
    automatic weights; head and hair ride on the head bone. Returns the armature object (also c['rig'])."""
    body, head = c['body'], c['head']
    vs = [v.co.copy() for v in body.data.vertices]
    H = c.get('neck_h') or max(v.z for v in vs)                    # one-piece models (Haru) give their neck height
    J = {k: f * H for k, f in JOINTS.items()}
    # legs: the centre of each leg's slice at knee and ankle height
    P = {}
    for side, s in (('L', 1), ('R', -1)):
        knee = _centre(_slice(vs, J['knee'] - 0.02 * H, J['knee'] + 0.02 * H, s))
        ank = _centre(_slice(vs, J['ankle'] - 0.02 * H, J['ankle'] + 0.02 * H, s))
        hip = Vector((knee.x * 1.05, 0, J['hip']))
        toe = Vector((ank.x, min(v.y for v in _slice(vs, 0, 0.06 * H, s)), 0.01 * H))
        # arms: the hand tip is the vertex furthest out to that side; the shoulder sits inside the top of the arm
        tip = max((v for v in vs if v.x * s > 0), key=lambda v: v.x * s)
        top = _slice(vs, J['shoulder'] - 0.03 * H, J['shoulder'], s)
        sx = max(v.x * s for v in top) * s
        sh = Vector((sx * 0.72, 0, J['shoulder']))
        arm = tip - sh
        P[side] = dict(hip=hip, knee=Vector((knee.x, knee.y + 0.005 * H, J['knee'])), ank=Vector((ank.x, ank.y, J['ankle'])),
                       toe=toe, sh=sh, elbow=sh + arm * 0.46 + Vector((0, 0.01 * H, 0)), wrist=sh + arm * 0.82, tip=tip)
    if head is not None:
        hlo, hhi = bounds(head); head_top = head.location.z - body.location.z + hhi.z
    else:
        head_top = max(v.z for v in vs)

    arm_ob = bpy.data.armatures.new(label + '_rig')
    rg = bpy.data.objects.new(label + '_rig', arm_ob); bpy.context.collection.objects.link(rg)
    rg.location = body.location.copy()
    for o in bpy.context.view_layer.objects: o.select_set(False)
    bpy.context.view_layer.objects.active = rg; rg.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_ob.edit_bones

    def bone(name, a, b, parent=None, connect=False):
        e = eb.new(name); e.head = a; e.tail = b
        if parent: e.parent = eb[parent]; e.use_connect = connect
        return e
    pel = Vector((0, 0, J['pelvis'])); chest = Vector((0, 0, J['chest'])); neck = Vector((0, 0, J['neck']))
    bone('root', Vector((0, 0, 0)), Vector((0, 0.15 * H, 0)))
    bone('hips', pel, pel - Vector((0, 0, 0.08 * H)), 'root')
    bone('spine', pel, chest, 'root')
    bone('chest', chest, neck, 'spine', True)
    bone('neck', neck, Vector((0, 0, H)), 'chest', True)
    bone('head', Vector((0, 0, H)), Vector((0, 0, head_top)), 'neck', True)
    for side, p in P.items():
        bone('thigh.' + side, p['hip'], p['knee'], 'hips')
        bone('shin.' + side, p['knee'], p['ank'], 'thigh.' + side, True)
        bone('foot.' + side, p['ank'], p['toe'], 'shin.' + side, True)
        bone('upper_arm.' + side, p['sh'], p['elbow'], 'chest')
        bone('forearm.' + side, p['elbow'], p['wrist'], 'upper_arm.' + side, True)
        bone('hand.' + side, p['wrist'], p['tip'], 'forearm.' + side, True)
    for e in eb: e.select = True
    bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Y')          # every bone's X axis lies flat: X turns = bend
    bpy.ops.object.mode_set(mode='OBJECT')

    # skin the body: bone heat, then any vertex it missed takes the nearest bone
    for o in bpy.context.view_layer.objects: o.select_set(False)
    body.select_set(True); rg.select_set(True); bpy.context.view_layer.objects.active = rg
    # bone heat fails on puppet-sized meshes (a few cm): skin at 20x, then shrink back (weights don't care about scale)
    arm_ob.bones['root'].use_deform = False
    arm_ob.bones['head'].use_deform = head is None                  # a one-piece model's head is skinned to the head bone
    body.scale = rg.scale = (20, 20, 20); bpy.context.view_layer.update()
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    body.matrix_parent_inverse.identity()
    rg.scale = (1, 1, 1); body.scale = (1, 1, 1); body.location = (0, 0, 0); bpy.context.view_layer.update()
    deform = [b for b in arm_ob.bones if b.use_deform]
    missing = [v.index for v in body.data.vertices if not any(g.weight > 1e-3 for g in v.groups)]
    if missing:
        def seg_d(p, b):
            a, t = b.head_local, b.tail_local; d = t - a
            u = max(0.0, min(1.0, (p - a).dot(d) / max(d.length_squared, 1e-12)))
            return (a + d * u - p).length
        for i in missing:
            p = body.data.vertices[i].co
            b = min(deform, key=lambda b: seg_d(p, b))
            g = body.vertex_groups.get(b.name) or body.vertex_groups.new(name=b.name)
            g.add([i], 1.0, 'REPLACE')
    print(f'RIG {label}: {len(arm_ob.bones)} bones, {len(missing)} of {len(body.data.vertices)} verts weighted by nearest bone', flush=True)
    # head and hair ride on the head bone
    for o in (head, c.get('hair')):
        if o is None: continue
        mw = o.matrix_world.copy()
        o.parent = rg; o.parent_type = 'BONE'; o.parent_bone = 'head'
        o.matrix_world = mw
    c['rig'] = rg
    return rg


def turn(rg, name, axis, deg, f=None):
    """turn a bone about a world axis ('X' nods forward, 'Y' swings sideways, 'Z' turns), on top of its current turn
    (so relax() then turn(..., 'X', 20) swings a hanging arm forward)"""
    pb = rg.pose.bones[name]; M = pb.bone.matrix_local.to_3x3()
    R = mathutils.Matrix.Rotation(math.radians(deg), 3, axis)
    cur = pb.rotation_quaternion.to_matrix() if pb.rotation_mode == 'QUATERNION' else pb.rotation_euler.to_matrix()
    pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (M.inverted() @ R @ M @ cur).to_quaternion()
    if f is not None: pb.keyframe_insert('rotation_quaternion', frame=f)


def relax(rg, gap=6, f=None):
    """bring the A-pose arms down to hang at the sides, `gap` degrees off the body (measured from the rest bones)"""
    for side, sgn in (('L', 1), ('R', -1)):
        b = rg.data.bones['upper_arm.' + side]; d = (b.tail_local - b.head_local).normalized()
        a = math.degrees(math.atan2(abs(d.x), -d.z))                 # the arm's angle out from straight down
        turn(rg, 'upper_arm.' + side, 'Y', sgn * max(0.0, a - gap), f)


def pose(rg, f=None, **turns):
    """turn bones by degrees in their own axes: pose(rig, **{'thigh.L': (-60, 0, 0)}); X bends, Y twists, Z swings.
    root=(x, y, z) in metres moves the whole character. f: also key this frame."""
    for name, v in turns.items():
        pb = rg.pose.bones['root' if name == 'root_loc' else name]
        if name == 'root_loc':
            pb.location = v
        else:
            pb.rotation_mode = 'XYZ'; pb.rotation_euler = [math.radians(a) for a in v]
        if f is not None:
            pb.keyframe_insert('location' if name == 'root_loc' else 'rotation_euler', frame=f)


def haru(loc=(0, 0, 0), label='haru'):
    """the new Haru (library/kit/haru_full.glb, Tripo): one piece, in channel clay, rigged like the kit characters.
    Her neck sits where a kit child's does, so the same joint shares and poses work on her."""
    o = load('haru_full'); fit(o, CHILD); o.location = loc
    bpy.context.view_layer.update()
    HC.apply_textured_clay([o], name=label, height=CHILD)
    c = dict(head=None, body=o, hair=None, neck_h=CHILD * (1 - HEAD_FRAC['child'] * (1 - PEG)))
    rig(c, label)
    return c
