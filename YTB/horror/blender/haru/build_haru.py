"""Clay Haru for Blender (v1).

Builds Haru from soft primitives (each garment = one voxel union, smoothed), gives every part a matte clay material,
rigs her with a simple armature (weights computed here, sleeve vs torso decided per vertex), puts her in the rest pose,
and can render flat ID views to measure against the Artlist turnaround sheet (.claude/skills/clay-character/scripts/measure.py).

Run live (Blender MCP):  ns = {}; exec(open(PATH).read(), ns); ns['build']()
Run headless:            blender -b -P build_haru.py -- [--id OUTDIR] [--beauty OUT.png]

Coordinates: metres, z up, Haru faces -Y, her left is +X (bones .L). Built in an A-pose (arms 40 deg out) so the
sleeves stay separate from the body; rest() lowers the arms.
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix, Euler

H = 1.26
A = math.radians(40)                    # A-pose: arm angle from vertical
SH = Vector((0.12, 0.01, 0.835))       # left shoulder joint (low: the sheet's shoulders slope down from the collar)
L_UP, L_FORE = 0.175, 0.17
HEM = 0.50


def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


PAL = {'hoodie': '#c88e2c', 'skin': '#e2a07e', 'pants': '#56575c', 'hair': '#242528', 'shoe': '#ecebe6',
       'sole': '#9d9b98', 'eye': '#121010', 'white': '#ffffff', 'mouth': '#6b3328', 'brow': '#2b2321'}
ID = {'hair': (1, 0, 0), 'skin': (0, 1, 0), 'top': (0, 0, 1), 'pants': (1, 1, 0), 'shoes': (1, 0, 1)}


# ---------------------------------------------------------------- arm geometry (A-pose)
def arm(side):
    """shoulder, elbow, wrist, down-direction, palm-out axis for side +1 (left, +x) or -1"""
    s = Vector((side * SH.x, SH.y, SH.z))
    d = Vector((side * math.sin(A), 0, -math.cos(A)))
    out = Vector((side * math.cos(A), 0, math.sin(A)))
    return s, s + d * L_UP, s + d * (L_UP + L_FORE), d, out


# ---------------------------------------------------------------- soft primitives
class Shape:
    def __init__(self):
        self.bm = bmesh.new()

    def ellipsoid(self, c, r, rot=None, seg=32):
        R = Matrix.Identity(4) if rot is None else (rot.to_4x4() if isinstance(rot, Matrix) else Euler(rot).to_matrix().to_4x4())
        m = Matrix.Translation(Vector(c)) @ R @ Matrix.Diagonal((r[0], r[1], r[2], 1))
        bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=seg // 2, radius=1.0, matrix=m)
        return self

    def ball(self, c, r, seg=24):
        return self.ellipsoid(c, (r, r, r), seg=seg)

    def capsule(self, a, b, ra, rb=None, seg=24):
        rb = ra if rb is None else rb
        a, b = Vector(a), Vector(b); d = b - a
        R = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg, radius1=ra, radius2=rb,
                              depth=d.length, matrix=Matrix.Translation((a + b) / 2) @ R)
        self.ball(a, ra, seg); self.ball(b, rb, seg)
        return self

    def ring(self, c, rx, ry, r, n=20, tilt=0.0):
        """balls round an ellipse; tilt raises the back (+y) and lowers the front"""
        for i in range(n):
            t = 2 * math.pi * i / n; y = ry * math.sin(t)
            self.ball((c[0] + rx * math.cos(t), c[1] + y, c[2] + tilt * y), r, 16)
        return self


def bake(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data; ob.modifiers.clear(); ob.data = new; new.name = ob.name
    bpy.data.meshes.remove(old)


def cut(ob, z, keep='above', fill=True):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1),
                                 clear_inner=(keep == 'above'), clear_outer=(keep == 'below'))
    if fill:
        edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        if edges: bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    bm.to_mesh(ob.data); bm.free()


def make(name, shape, coll, mat, part, voxel=0.005, smooth=6, lumps=0.0025, cuts=()):
    me = bpy.data.meshes.new(name); shape.bm.to_mesh(me); shape.bm.free()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    rm = ob.modifiers.new('remesh', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = voxel
    if smooth:
        sm = ob.modifiers.new('smooth', 'SMOOTH'); sm.factor = 0.8; sm.iterations = smooth
    bake(ob)
    for z, keep in cuts: cut(ob, z, keep)
    for p in ob.data.polygons: p.use_smooth = True
    ob.data.materials.append(mat)
    ob['part'] = part; ob.color = (*ID[part], 1)
    if lumps:
        tex = bpy.data.textures.get('clay_lumps') or bpy.data.textures.new('clay_lumps', 'CLOUDS')
        tex.noise_scale = 0.05; tex.noise_depth = 1
        dm = ob.modifiers.new('lumps', 'DISPLACE'); dm.texture = tex; dm.strength = lumps
        dm.texture_coords = 'GLOBAL'; dm.mid_level = 0.5
    return ob


# ---------------------------------------------------------------- clay materials
def clay_mat(name, hexc, rough=0.86, sss=0.04, bump=0.35, grooves=0.0, gloss=False):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; N, Lk = nt.nodes, nt.links; N.clear()
    out = N.new('ShaderNodeOutputMaterial'); out.location = (900, 0)
    b = N.new('ShaderNodeBsdfPrincipled'); b.location = (600, 0)
    Lk.new(b.outputs['BSDF'], out.inputs['Surface'])
    c = lin(hexc)
    b.inputs['Roughness'].default_value = 0.25 if gloss else rough
    b.inputs['Specular IOR Level'].default_value = 0.5 if gloss else 0.32
    b.inputs['Subsurface Weight'].default_value = sss
    b.inputs['Subsurface Radius'].default_value = (1.0, 0.45, 0.25)
    b.inputs['Subsurface Scale'].default_value = 0.015
    b.inputs['Sheen Weight'].default_value = 0.0 if gloss else 0.12
    tc = N.new('ShaderNodeTexCoord'); tc.location = (-900, 0)
    mp = N.new('ShaderNodeMapping'); mp.name = mp.label = 'boil'; mp.location = (-700, 0)
    Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
    # mottled colour
    n1 = N.new('ShaderNodeTexNoise'); n1.location = (-400, 300)
    n1.inputs['Scale'].default_value = 7; n1.inputs['Detail'].default_value = 3
    Lk.new(mp.outputs['Vector'], n1.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB'); ramp.location = (-150, 300)
    e0, e1 = ramp.color_ramp.elements
    e0.position, e1.position = 0.3, 0.72
    e0.color = (*[v * 0.86 for v in c], 1); e1.color = (*[min(1, v * 1.1) for v in c], 1)
    Lk.new(n1.outputs['Fac'], ramp.inputs['Fac']); Lk.new(ramp.outputs['Color'], b.inputs['Base Color'])
    if bump <= 0: return m
    # height = soft dents + fingerprints + tool marks (+ hair grooves)
    n_dent = N.new('ShaderNodeTexNoise'); n_dent.location = (-400, 0)
    n_dent.inputs['Scale'].default_value = 16; n_dent.inputs['Detail'].default_value = 2
    n_fp = N.new('ShaderNodeTexWave'); n_fp.location = (-400, -250)
    n_fp.wave_type = 'RINGS'; n_fp.inputs['Scale'].default_value = 140
    n_fp.inputs['Distortion'].default_value = 6; n_fp.inputs['Detail'].default_value = 1
    vo = N.new('ShaderNodeTexVoronoi'); vo.location = (-400, -500)
    vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 22
    for t in (n_dent, n_fp, vo): Lk.new(mp.outputs['Vector'], t.inputs['Vector'])
    def madd(a, k, add, loc):
        n = N.new('ShaderNodeMath'); n.operation = 'MULTIPLY_ADD'; n.location = loc
        Lk.new(a, n.inputs[0]); n.inputs[1].default_value = k
        if isinstance(add, float): n.inputs[2].default_value = add
        else: Lk.new(add, n.inputs[2])
        return n.outputs[0]
    h = madd(n_dent.outputs['Fac'], 1.0, 0.0, (-150, 0))
    h = madd(n_fp.outputs['Fac'], 0.12, h, (-150, -200))
    vs = N.new('ShaderNodeMath'); vs.operation = 'SMOOTH_MIN'; vs.location = (-200, -500)
    Lk.new(vo.outputs['Distance'], vs.inputs[0]); vs.inputs[1].default_value = 0.08; vs.inputs[2].default_value = 0.05
    h = madd(vs.outputs[0], 0.6, h, (-150, -400))
    if grooves:
        wv = N.new('ShaderNodeTexWave'); wv.location = (-400, -750)
        wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 9
        wv.inputs['Distortion'].default_value = 3; wv.inputs['Detail Scale'].default_value = 1
        Lk.new(mp.outputs['Vector'], wv.inputs['Vector'])
        h = madd(wv.outputs['Fac'], grooves, h, (-150, -650))
    bp = N.new('ShaderNodeBump'); bp.location = (300, -300)
    bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.003
    Lk.new(h, bp.inputs['Height']); Lk.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


# ---------------------------------------------------------------- the puppet
HEAD_C, HEAD_R = Vector((0, 0, 1.056)), Vector((0.112, 0.105, 0.136))


def on_face(x, z, lift=0.0):
    """point on the front of the head ellipsoid at (x, z), plus the outward normal"""
    u, w = x / HEAD_R.x, (z - HEAD_C.z) / HEAD_R.z
    y = HEAD_C.y - HEAD_R.y * math.sqrt(max(0.0, 1 - u * u - w * w))
    p = Vector((x, y, z))
    n = Vector(((x - HEAD_C.x) / HEAD_R.x ** 2, (y - HEAD_C.y) / HEAD_R.y ** 2, (z - HEAD_C.z) / HEAD_R.z ** 2)).normalized()
    return p + n * lift, n


def build_parts(coll, M):
    parts = {}
    # --- hoodie: body, shoulders, sleeves, hem roll, hood collar, hood on the back, pocket
    s = Shape()
    s.ellipsoid((0, 0.012, 0.75), (0.135, 0.085, 0.14))
    s.ellipsoid((0, 0.0, 0.63), (0.155, 0.094, 0.14))
    s.ellipsoid((0, 0.0, HEM + 0.06), (0.158, 0.094, 0.065))
    s.ring((0, 0, HEM + 0.023), 0.15, 0.086, 0.024, 26)
    s.ring((0, 0.014, 0.918), 0.078, 0.068, 0.037, 22, tilt=0.9)    # hood collar: low at the front so the neck shows, high at the back
    s.ellipsoid((0, 0.075, 0.86), (0.095, 0.032, 0.08))             # the hood lying on the back
    s.ellipsoid((0, -0.088, 0.6), (0.095, 0.02, 0.055))             # kangaroo pocket
    for side in (1, -1):
        sh, el, wr, d, out = arm(side)
        s.ball((side * 0.105, 0.01, 0.795), 0.062)
        s.capsule(sh, el, 0.062, 0.059)
        s.capsule(el, wr - d * 0.012, 0.059, 0.058)
        s.ball(wr - d * 0.03, 0.062)                                  # sleeve bunching at the cuff
    parts['hoodie'] = make('haru_hoodie', s, coll, M['hoodie'], 'top', voxel=0.0045, smooth=8, cuts=[(HEM, 'above')])

    # drawstrings
    s = Shape()
    for side in (1, -1):
        s.capsule((side * 0.026, -0.072, 0.89), (side * 0.032, -0.093, 0.79), 0.0065)
        s.ball((side * 0.032, -0.093, 0.785), 0.0095)
    parts['strings'] = make('haru_drawstrings', s, coll, M['hoodie'], 'top', voxel=0.0016, smooth=3, lumps=0.0006)

    # --- trousers (cut just above the hoodie hem so nothing pokes through when she bends)
    s = Shape()
    s.ellipsoid((0, 0, 0.58), (0.135, 0.095, 0.08))
    for side in (1, -1):
        hip, knee, ank = Vector((side * 0.062, 0, 0.55)), Vector((side * 0.063, 0, 0.30)), Vector((side * 0.064, 0.005, 0.075))
        s.capsule(hip, knee, 0.06, 0.055); s.capsule(knee, ank, 0.055, 0.054)
    parts['pants'] = make('haru_trousers', s, coll, M['pants'], 'pants', voxel=0.0045, smooth=6,
                          cuts=[(HEM + 0.045, 'below'), (0.062, 'above')])

    # --- shoes: white upper, grey sole
    s = Shape(); so = Shape()
    for side in (1, -1):
        x = side * 0.074
        s.ellipsoid((x, -0.028, 0.044), (0.056, 0.094, 0.044))
        s.ellipsoid((x, -0.075, 0.034), (0.054, 0.05, 0.032))
        s.capsule((side * 0.068, 0.005, 0.06), (side * 0.068, 0.005, 0.085), 0.047)   # collar round the ankle
        so.ellipsoid((x, -0.03, 0.014), (0.061, 0.103, 0.017))
    parts['shoes'] = make('haru_shoes', s, coll, M['shoe'], 'shoes', voxel=0.003, smooth=5, cuts=[(0.016, 'above')])
    parts['soles'] = make('haru_soles', so, coll, M['sole'], 'shoes', voxel=0.003, smooth=4, lumps=0.001, cuts=[(0.0, 'above')])

    # --- neck and head (skin)
    s = Shape().capsule((0, 0.012, 0.84), (0, 0.012, 0.975), 0.043)
    parts['neck'] = make('haru_neck', s, coll, M['skin'], 'skin', voxel=0.003, smooth=4, lumps=0.001)
    s = Shape().ellipsoid(HEAD_C, HEAD_R, seg=48)
    parts['head'] = make('haru_head', s, coll, M['skin'], 'skin', voxel=0.003, smooth=6, lumps=0.0012)

    # --- hair: one clay mass (cap set back so the face shows, side panels, back panel, side-swept fringe)
    s = Shape()
    s.ellipsoid((0, 0.05, 1.09), (0.13, 0.112, 0.172))
    s.ellipsoid((0, 0.03, 1.16), (0.124, 0.11, 0.1))
    for side in (1, -1):                                      # thick straight panels framing the face, down onto the shoulders
        s.ellipsoid((side * 0.128, 0.045, 1.0), (0.03, 0.085, 0.165))
        s.ellipsoid((side * 0.126, 0.03, 0.89), (0.031, 0.07, 0.06))    # lies over the front of the shoulder
    s.ellipsoid((0, 0.075, 0.93), (0.15, 0.075, 0.13))        # back panel, down to the shoulder blades
    s.ellipsoid((0, 0.08, 0.86), (0.145, 0.06, 0.06))
    # side-swept fringe: a flat slab lying on the forehead, deeper on her right (-x), parted on her left
    s.ellipsoid((-0.015, -0.068, 1.17), (0.1, 0.022, 0.042), rot=(math.radians(-25), math.radians(-12), 0))
    s.ellipsoid((-0.07, -0.05, 1.135), (0.045, 0.025, 0.05), rot=(math.radians(-20), 0, 0))
    s.ellipsoid((0.05, -0.05, 1.19), (0.06, 0.03, 0.035), rot=(math.radians(-30), 0, 0))
    parts['hair'] = make('haru_hair', s, coll, M['hair'], 'hair', voxel=0.004, smooth=8, lumps=0.002)

    # --- hands
    for side, tag in ((1, 'L'), (-1, 'R')):
        sh, el, wr, d, out = arm(side)
        f = Vector((0, -1, 0))
        Mx = Matrix((out, f, -d)).transposed()                  # columns: palm normal (out), front, up the arm
        P = lambda u, v, w: wr + Mx @ Vector((u, v, w))
        s = Shape()
        s.capsule(P(0, 0, 0.02), P(0, 0, -0.012), 0.022, 0.021)
        s.ellipsoid(P(0, 0, -0.038), (0.02, 0.035, 0.037), rot=Mx)
        for vy in (-0.022, -0.0073, 0.0073, 0.022):
            ln = 0.034 if abs(vy) < 0.01 else 0.028
            s.capsule(P(0.001, vy, -0.062), P(-0.008, vy * 1.05, -0.062 - ln), 0.0088, 0.008, 16)
        s.capsule(P(-0.007, -0.029, -0.028), P(-0.018, -0.04, -0.058), 0.0095, 0.0088, 16)
        parts['hand_' + tag] = make('haru_hand.' + tag, s, coll, M['skin'], 'skin', voxel=0.0015, smooth=5, lumps=0.0008)

    # --- face pieces (on the head surface; expressions swap these later)
    face = []
    def piece(name, shape, mat, vox=0.001):
        ob = make(name, shape, coll, mat, 'skin', voxel=vox, smooth=3, lumps=0)
        face.append(ob); return ob
    for side, tag in ((1, 'L'), (-1, 'R')):
        p, n = on_face(side * 0.038, 1.045, -0.002)
        R = n.to_track_quat('-Y', 'Z').to_matrix()
        piece('haru_eye.' + tag, Shape().ellipsoid(p, (0.0115, 0.006, 0.0125), rot=R), M['eye'])
        cp, _ = on_face(side * 0.038 + 0.004, 1.051, 0.0035)
        piece('haru_catchlight.' + tag, Shape().ball(cp, 0.0024, 12), M['white'], 0.0006)
        a, na = on_face(side * 0.022, 1.097, 0.0005); b, nb = on_face(side * 0.058, 1.092, 0.0005)
        piece('haru_brow.' + tag, Shape().capsule(a, b, 0.0034, 0.0028, 12), M['brow'], 0.0008)
    p, n = on_face(0, 0.995, 0.004)
    piece('haru_nose', Shape().ellipsoid(p, (0.0105, 0.009, 0.0098), seg=24), M['skin'])
    a, _ = on_face(-0.013, 0.957, 0.0003); b, _ = on_face(0.013, 0.957, 0.0003)
    piece('haru_mouth', Shape().capsule(a, b, 0.0024, 0.0024, 12), M['mouth'], 0.0007)
    parts['face'] = face
    return parts


# ---------------------------------------------------------------- expressions (shape keys on the face pieces)
def face_keys(parts):
    """blink (eyes squash shut, catchlights sink), worried (inner brow ends up), frown (mouth corners down)"""
    def keyed(ob, name, fn):
        if not ob.data.shape_keys: ob.shape_key_add(name='Basis', from_mix=False)
        k = ob.shape_key_add(name=name, from_mix=False)
        for i, v in enumerate(ob.data.vertices): k.data[i].co = fn(v.co.copy())
    obs = {o.name: o for o in parts['face']}
    for side, tag in ((1, 'L'), (-1, 'R')):
        eye = obs['haru_eye.' + tag]
        c = sum((v.co for v in eye.data.vertices), Vector()) / len(eye.data.vertices)
        _, n = on_face(side * 0.038, 1.045)
        up = (Vector((0, 0, 1)) - n * n.z).normalized()
        keyed(eye, 'blink', lambda p: p - up * ((p - c).dot(up) * 0.88) - up * 0.004)
        cl = obs['haru_catchlight.' + tag]
        keyed(cl, 'blink', lambda p: c - n * 0.006 + (p - c) * 0.01)
        keyed(obs['haru_brow.' + tag], 'worried',
              lambda p: p + Vector((0, 0, 0.001 + 0.0065 * min(1, max(0, (0.058 - abs(p.x)) / 0.036)))))
    keyed(obs['haru_mouth'], 'frown', lambda p: p + Vector((0, 0, -0.0035 * (abs(p.x) / 0.013) ** 2 + 0.0008)))


def set_expr(parts_or_coll, **vals):
    """set shape key values on Haru's face pieces, e.g. set_expr(coll, blink=1, worried=0.5); returns the keys touched"""
    obs = parts_or_coll.objects if hasattr(parts_or_coll, 'objects') else parts_or_coll['face']
    touched = []
    for ob in obs:
        sk = ob.data.shape_keys if ob.type == 'MESH' else None
        if not sk: continue
        for name, v in vals.items():
            kb = sk.key_blocks.get(name)
            if kb: kb.value = v; touched.append(kb)
    return touched


# ---------------------------------------------------------------- rig
BONES = {}   # name -> (head, tail, parent)


def bone_table():
    t = {'root': ((0, 0, 0), (0, 0, 0.12), None),
         'hips': ((0, 0, 0.55), (0, 0, 0.65), 'root'),
         'spine': ((0, 0, 0.65), (0, 0, 0.77), 'hips'),
         'chest': ((0, 0, 0.77), (0, 0.01, 0.87), 'spine'),
         'neck': ((0, 0.012, 0.87), (0, 0.012, 0.975), 'chest'),
         'head': ((0, 0.01, 0.975), (0, 0.01, 1.25), 'neck')}
    for side, tag in ((1, 'L'), (-1, 'R')):
        sh, el, wr, d, out = arm(side)
        t['shoulder.' + tag] = ((side * 0.03, 0.01, 0.85), tuple(sh), 'chest')
        t['upper_arm.' + tag] = (tuple(sh), tuple(el), 'shoulder.' + tag)
        t['forearm.' + tag] = (tuple(el), tuple(wr), 'upper_arm.' + tag)
        t['hand.' + tag] = (tuple(wr), tuple(wr + d * 0.09), 'forearm.' + tag)
        t['thigh.' + tag] = ((side * 0.062, 0, 0.55), (side * 0.063, 0, 0.30), 'hips')
        t['shin.' + tag] = ((side * 0.063, 0, 0.30), (side * 0.064, 0.005, 0.085), 'thigh.' + tag)
        t['foot.' + tag] = ((side * 0.064, 0.005, 0.085), (side * 0.07, -0.1, 0.03), 'shin.' + tag)
    return t


def make_rig(coll):
    t = bone_table(); BONES.clear(); BONES.update(t)
    ad = bpy.data.armatures.new('haru_rig'); arm_ob = bpy.data.objects.new('haru_rig', ad); coll.objects.link(arm_ob)
    ad.display_type = 'STICK'; arm_ob.show_in_front = True
    vl = bpy.context.view_layer
    for o in bpy.context.selected_objects: o.select_set(False)
    vl.objects.active = arm_ob; arm_ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, (h, tl, par) in t.items():
        b = ad.edit_bones.new(name); b.head, b.tail = h, tl
        b.roll = 0
        if par: b.parent = ad.edit_bones[par]; b.use_connect = False
        b.use_deform = name != 'root'
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_ob


def seg_dist(P, a, b):
    a, b = np.array(a), np.array(b); ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def inv_w(P, names, power=4):
    D = np.stack([np.maximum(seg_dist(P, *BONES[n][:2]), 0.004) for n in names], 1)
    W = 1 / D ** power; return W / W.sum(1, keepdims=True)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def set_weights(ob, table):
    """table: {bone: weights array}"""
    for n, w in table.items():
        vg = ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n)
        idx = np.where(w > 0.01)[0]
        for i in idx: vg.add([int(i)], float(w[i]), 'REPLACE')


def verts(ob):
    P = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get('co', P); return P.reshape(-1, 3)


def skin(parts, rig):
    def rigid(ob, bone): set_weights(ob, {bone: np.ones(len(ob.data.vertices))})
    # hoodie: torso vs sleeve per vertex (whichever surface is nearer, soft band at the seam)
    ob = parts['hoodie']; P = verts(ob); table = {}
    torso_c, torso_r = np.array([0, 0.005, 0.68]), np.array([0.155, 0.094, 0.19])
    d_torso = (np.linalg.norm((P - torso_c) / torso_r, axis=1) - 1) * 0.094
    torso_share = np.ones(len(P))
    for side, tag in ((1, 'L'), (-1, 'R')):
        sh, el, wr, d, out = arm(side)
        d_arm = seg_dist(P, sh, wr) - 0.058
        t = smoothstep(-0.014, 0.014, d_torso - d_arm) * (P[:, 0] * side > 0.05)
        torso_share -= t
        W = inv_w(P, ['shoulder.' + tag, 'upper_arm.' + tag, 'forearm.' + tag])
        for k, n in enumerate(['shoulder.' + tag, 'upper_arm.' + tag, 'forearm.' + tag]): table[n] = W[:, k] * t
    torso_share = np.clip(torso_share, 0, 1)
    W = inv_w(P, ['hips', 'spine', 'chest'], 3)
    for k, n in enumerate(['hips', 'spine', 'chest']): table[n] = W[:, k] * torso_share
    # the hood collar turns partly with the neck, so the chin clears it when she looks over a shoulder
    rad = np.hypot(P[:, 0], P[:, 1] - 0.014)
    collar = smoothstep(0.855, 0.895, P[:, 2]) * (1 - smoothstep(0.11, 0.135, rad)) * 0.65
    for n in table: table[n] = table[n] * (1 - collar)
    table['neck'] = collar
    set_weights(ob, table)
    rigid(parts['strings'], 'chest')
    # trousers: hips above the crotch, then each leg (a leg never takes the other side)
    ob = parts['pants']; P = verts(ob); names = ['hips', 'thigh.L', 'shin.L', 'thigh.R', 'shin.R']
    W = inv_w(P, names, 4)
    W[:, 1:3] *= (P[:, 0] > -0.012)[:, None]; W[:, 3:5] *= (P[:, 0] < 0.012)[:, None]
    W[:, 0] += smoothstep(HEM - 0.03, HEM + 0.03, P[:, 2]) * 4
    W /= W.sum(1, keepdims=True)
    set_weights(ob, {n: W[:, k] for k, n in enumerate(names)})
    # shoes and soles: per foot
    for key in ('shoes', 'soles'):
        ob = parts[key]; P = verts(ob)
        set_weights(ob, {'foot.L': (P[:, 0] > 0).astype(float), 'foot.R': (P[:, 0] <= 0).astype(float)})
    rigid(parts['neck'], 'neck'); rigid(parts['head'], 'head')
    # hair: the crown follows the head, the ends resting on the shoulders stay with the chest (no cutting through the hoodie on a turn)
    ob = parts['hair']; P = verts(ob); wh = smoothstep(0.87, 1.0, P[:, 2])
    set_weights(ob, {'head': wh, 'neck': (1 - wh) * 0.4, 'chest': (1 - wh) * 0.6})
    for ob in parts['face']: rigid(ob, 'head')
    rigid(parts['hand_L'], 'hand.L'); rigid(parts['hand_R'], 'hand.R')
    for ob in all_meshes(parts):
        ob.parent = rig
        m = ob.modifiers.new('rig', 'ARMATURE'); m.object = rig


def all_meshes(parts):
    out = []
    for v in parts.values(): out += v if isinstance(v, list) else [v]
    return out


# ---------------------------------------------------------------- poses
def rot_arm_space(rig, bone, axis, deg):
    """rotate a pose bone about an armature-space axis (parent assumed unposed in that axis frame)"""
    pb = rig.pose.bones[bone]; pb.rotation_mode = 'QUATERNION'
    Rl = rig.data.bones[bone].matrix_local.to_3x3()
    q = Matrix.Rotation(math.radians(deg), 3, Vector(axis)).to_quaternion()
    ql = (Rl.inverted() @ q.to_matrix() @ Rl).to_quaternion()
    pb.rotation_quaternion = ql @ pb.rotation_quaternion


def rest(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    for side, tag in ((1, 'L'), (-1, 'R')):
        rot_arm_space(rig, 'upper_arm.' + tag, (0, 1, 0), side * 29)        # arms down beside the body, a little away from it
        rot_arm_space(rig, 'forearm.' + tag, (1, 0, 0), 6)                   # a soft bend at the elbow
    bpy.context.view_layer.update()


# ---------------------------------------------------------------- scene, ID renders, beauty
def collection(name='Haru'):
    col = bpy.data.collections.get(name)
    if col:
        for o in list(col.objects): bpy.data.objects.remove(o, do_unlink=True)
    else:
        col = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(col)
    for me in [m for m in bpy.data.meshes if m.users == 0]: bpy.data.meshes.remove(me)
    for ad in [a for a in bpy.data.armatures if a.users == 0]: bpy.data.armatures.remove(ad)
    return col


def materials():
    return {'hoodie': clay_mat('clay_hoodie', PAL['hoodie'], sss=0.03, bump=0.4),
            'pants': clay_mat('clay_pants', PAL['pants'], sss=0.02, bump=0.35),
            'skin': clay_mat('clay_skin', PAL['skin'], sss=0.12, bump=0.22),
            'hair': clay_mat('clay_hair', PAL['hair'], rough=0.8, sss=0.0, bump=0.35, grooves=0.5),
            'shoe': clay_mat('clay_shoe', PAL['shoe'], sss=0.03, bump=0.25),
            'sole': clay_mat('clay_sole', PAL['sole'], bump=0.25),
            'eye': clay_mat('clay_eye', PAL['eye'], bump=0, gloss=True),
            'white': clay_mat('clay_white', PAL['white'], bump=0, sss=0.0),
            'mouth': clay_mat('clay_mouth', PAL['mouth'], bump=0.1),
            'brow': clay_mat('clay_brow', PAL['brow'], bump=0.1)}


def build():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    cube = bpy.data.objects.get('Cube')
    if cube: bpy.data.objects.remove(cube, do_unlink=True)
    coll = collection()
    parts = build_parts(coll, materials())
    face_keys(parts)
    rig = make_rig(coll)
    skin(parts, rig)
    rest(rig)
    dg = bpy.context.evaluated_depsgraph_get()
    lo, hi = Vector((9, 9, 9)), Vector((-9, -9, -9))
    for ob in all_meshes(parts):
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        for v in me.vertices:
            w = ev.matrix_world @ v.co
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
        ev.to_mesh_clear()
    return {'objects': len(coll.objects), 'bbox_min': [round(v, 3) for v in lo], 'bbox_max': [round(v, 3) for v in hi],
            'faces': sum(len(o.data.polygons) for o in all_meshes(parts))}


def id_renders(outdir, views=(0, 2, 4)):
    """flat ID colours, orthographic, one image per view: 0 front, 2 side (facing right), 4 back"""
    sc = bpy.context.scene; os.makedirs(outdir, exist_ok=True)
    keep = (sc.render.engine, sc.view_settings.view_transform, sc.camera, sc.render.resolution_x, sc.render.resolution_y)
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'OBJECT'
    sh.show_shadows = sh.show_cavity = sh.show_object_outline = sh.show_specular_highlight = False
    sc.view_settings.view_transform = 'Standard'
    if not sc.world: sc.world = bpy.data.worlds.new('World')
    wc = sc.world.color[:]; sc.world.color = (0.012, 0.012, 0.012)
    hidden = [o for o in sc.objects if o.users_collection[0].name != 'Haru' and o.type == 'MESH' and not o.hide_render]
    for o in hidden: o.hide_render = True
    cd = bpy.data.cameras.get('cam_id') or bpy.data.cameras.new('cam_id'); cd.type = 'ORTHO'; cd.ortho_scale = 1.4
    cam = bpy.data.objects.get('cam_id') or bpy.data.objects.new('cam_id', cd)
    if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
    sc.camera = cam; sc.render.resolution_x, sc.render.resolution_y = 1000, 1300
    poses = {0: ((0, -5, 0.63), (90, 0, 0)), 2: ((-5, 0, 0.63), (90, 0, -90)), 4: ((0, 5, 0.63), (90, 0, 180))}
    files = []
    for v in views:
        loc, rot = poses[v]; cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
        sc.render.filepath = os.path.join(outdir, f'id_view{v}.png'); bpy.ops.render.render(write_still=True)
        files.append(sc.render.filepath)
    for o in hidden: o.hide_render = False
    sc.world.color = wc
    sc.render.engine, sc.view_settings.view_transform, sc.camera, sc.render.resolution_x, sc.render.resolution_y = keep
    return files


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def stage(samples=128):
    """light grey seamless backdrop + soft studio lights (like the Artlist sheet), 9:16 camera, Cycles on the GPU"""
    sc = bpy.context.scene
    col = bpy.data.collections.get('Stage')
    if col:
        for o in list(col.objects): bpy.data.objects.remove(o, do_unlink=True)
    else:
        col = bpy.data.collections.new('Stage'); sc.collection.children.link(col)
    for n in ('Camera', 'Light'):
        o = bpy.data.objects.get(n)
        if o: bpy.data.objects.remove(o, do_unlink=True)
    # cyclorama: floor curving up into a wall behind her
    bm = bmesh.new(); prof = [(-3.0, 0.0)]
    for i in range(13):
        a = math.pi / 2 * i / 12; prof.append((1.2 + math.sin(a) * 1.0, 1.0 - math.cos(a) * 1.0))
    prof.append((2.2, 4.0))
    rows = []
    for x in (-4.0, 4.0): rows.append([bm.verts.new((x, y, z)) for y, z in prof])
    for i in range(len(prof) - 1): bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    me = bpy.data.meshes.new('backdrop'); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    bd = bpy.data.objects.new('backdrop', me); col.objects.link(bd)
    me.materials.append(clay_mat('backdrop', '#dcdad6', rough=0.95, sss=0.0, bump=0.05))
    def area(name, loc, energy, size, color, target=(0, 0, 0.75), spread=180):
        ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size; ld.color = color
        ld.spread = math.radians(spread)
        o = bpy.data.objects.new(name, ld); o.location = loc; col.objects.link(o); look_at(o, target); return o
    area('key', (-1.5, -2.2, 2.3), 190, 1.6, (1.0, 0.96, 0.9))
    area('fill', (2.2, -1.6, 1.1), 45, 2.0, (0.92, 0.95, 1.0))
    area('rim', (1.0, 1.6, 2.0), 120, 0.8, (1.0, 0.97, 0.92), (0, 0, 1.0), spread=50)
    if not sc.world: sc.world = bpy.data.worlds.new('World')
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get('Background')
    if bg: bg.inputs['Color'].default_value = (0.6, 0.6, 0.6, 1); bg.inputs['Strength'].default_value = 0.15
    cd = bpy.data.cameras.new('cam_main'); cd.lens = 70; cd.sensor_width = 36
    cd.dof.use_dof = True; cd.dof.aperture_fstop = 5.6
    cam = bpy.data.objects.new('cam_main', cd); col.objects.link(cam)
    cam.location = (0, -4.6, 0.72); look_at(cam, (0, 0, 0.64))
    cd.dof.focus_distance = 4.6
    sc.camera = cam
    r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
    r.fps = 24; r.engine = 'CYCLES'
    sc.cycles.samples = samples; sc.cycles.use_denoising = True
    try:
        pr = bpy.context.preferences.addons['cycles'].preferences
        pr.compute_device_type = 'OPTIX'; pr.get_devices()
        for d in pr.devices: d.use = d.type in ('OPTIX', 'CPU') and (d.type == 'OPTIX' or False)
        sc.cycles.device = 'GPU'
    except Exception as e:
        print('GPU setup:', e)
    sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - Punchy'
    except TypeError: pass
    return cam


def beauty(path, cam_loc=None, target=(0, 0, 0.64), lens=None, samples=None):
    sc = bpy.context.scene; cam = bpy.data.objects['cam_main']
    if cam_loc: cam.location = cam_loc; look_at(cam, target); cam.data.dof.focus_distance = (Vector(target) - Vector(cam_loc)).length
    if lens: cam.data.lens = lens
    if samples: sc.cycles.samples = samples
    sc.camera = cam; sc.render.filepath = path; bpy.ops.render.render(write_still=True); return path


if __name__ == '__main__' and '--' in sys.argv:
    args = sys.argv[sys.argv.index('--') + 1:]
    print(build())
    if '--id' in args: print(id_renders(args[args.index('--id') + 1]))
