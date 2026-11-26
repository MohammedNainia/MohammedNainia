"""Haru, the clay puppet (blender-claymation skill style).

A real tabletop puppet: 12.6 cm tall, built in metres. Rigid clay pieces hang under pivot empties (root at the feet,
hips, spine, chest, neck, head; shoulders, elbows, wrists; hips, knees, ankles), so a pose is only rotations and the
renderer only moves objects between frames (fast, no per-frame mesh deformation). Each piece is a voxel-merged
group of soft shapes (the proportions measured against the Artlist turnaround), smoothed, with lumpy displacement and
the skill's clay material. Faces are replacement parts swapped by scale, like stop-motion replacement faces.
The hair is soft: anything pushed under the floor or a bed (the Colliders collection) squashes flat onto it.

Use from a scene script:
    sys.path.insert(0, <this folder>); from haru_puppet import Haru
    h = Haru(loc=(0, 0, 0), yaw=0)         # builds everything
    h.pose({('thigh.L', 'x'): -20, ...}); h.ground(); h.expr('worried'); h.key(f)
Pose spec: {(pivot, axis): degrees}, axes in the parent's frame (her forward is -y, her left +x, applied y, x, z):
x: + leans the spine/head forward, + swings a hanging limb back, + bends the knee; elbows bend with -x; foot -x = toes up.
y on an upper arm: + brings the left arm in (-, the right).
"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', '.claude', 'skills', 'blender-claymation', 'scripts'))
sys.path.insert(0, SKILL)
import claylib as C
sys.path.insert(0, HERE)
import importlib, clay_v3 as CV
importlib.reload(CV)

CLAY_SCALE = 0.6          # claylib feature size for pieces built in true metres (soft finger-sized marks on a 12 cm puppet)
S = 0.1                     # puppet scale: everything below is authored in the measured 1.26 m units, built x0.1
A_REST = math.radians(11)   # arms hang 11 deg out from the body
SH = Vector((0.12, 0.01, 0.835)); L_UP, L_FORE = 0.175, 0.17
HEM = 0.50
HEAD_C, HEAD_R = Vector((0, 0, 1.056)), Vector((0.112, 0.105, 0.136))


def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


PAL = {'hoodie': '#b8791a', 'skin': '#e2a07e', 'pants': '#45464b', 'hair': '#242528', 'shoe': '#ecebe6',
       'sole': '#9d9b98', 'mouth': '#6b3328', 'mouth_in': '#3a1411', 'brow': '#2b2321', 'white': '#f2f0ea'}
ID = {'hair': (1, 0, 0), 'skin': (0, 1, 0), 'top': (0, 0, 1), 'pants': (1, 1, 0), 'shoes': (1, 0, 1)}


# ---------------------------------------------------------------- soft shapes, merged into one clay piece
class Shape:
    def __init__(self): self.bm = bmesh.new()

    def ellipsoid(self, c, r, rot=None, seg=32):
        R = Matrix.Identity(4) if rot is None else (rot.to_4x4() if isinstance(rot, Matrix) else Euler(rot).to_matrix().to_4x4())
        bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=seg // 2, radius=1.0,
                                  matrix=Matrix.Translation(Vector(c)) @ R @ Matrix.Diagonal((*r, 1)))
        return self

    def ball(self, c, r, seg=24): return self.ellipsoid(c, (r, r, r), seg=seg)

    def capsule(self, a, b, ra, rb=None, seg=24):
        rb = ra if rb is None else rb; a, b = Vector(a), Vector(b); d = b - a
        Rm = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg, radius1=ra, radius2=rb,
                              depth=d.length, matrix=Matrix.Translation((a + b) / 2) @ Rm)
        return self.ball(a, ra, seg).ball(b, rb, seg)

    def ring(self, c, rx, ry, r, n=20, tilt=0.0):
        for i in range(n):
            t = 2 * math.pi * i / n; y = ry * math.sin(t)
            self.ball((c[0] + rx * math.cos(t), c[1] + y, c[2] + tilt * y), r, 16)
        return self

    def fold(self, a, b, t, r_limb, bulge, wobble=0.0, seed=0, n=30):
        """a soft fold where a sleeve or trouser leg bunches: a ring of bulges round the limb a->b at fraction t"""
        import random
        rnd = random.Random(seed)
        a, b = Vector(a), Vector(b); d = (b - a).normalized()
        u = d.orthogonal().normalized(); v = d.cross(u)
        c = a + (b - a) * t
        for i in range(n):
            ang = 2 * math.pi * i / n
            off = d * wobble * math.sin(ang + rnd.uniform(0, 6.28))      # a wonky, hand-pressed fold, not a perfect ring
            p = c + (u * math.cos(ang) + v * math.sin(ang)) * (r_limb - bulge * 0.55) + off
            self.ball(p, bulge * rnd.uniform(0.9, 1.08), 12)
        return self


def piece(name, shape, mat, part, coll, voxel=0.0045, smooth=6, lump=0.00022, cuts=(), inset=None):
    """voxel-merge the shapes (authored in 1.26 m units), smooth, cut, scale to puppet size, add lumps"""
    me = bpy.data.meshes.new(name); shape.bm.to_mesh(me); shape.bm.free()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    rm = ob.modifiers.new('remesh', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = voxel
    if smooth: sm = ob.modifiers.new('smooth', 'SMOOTH'); sm.factor = 0.8; sm.iterations = smooth
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(ob.evaluated_get(dg)); old = ob.data
    ob.modifiers.clear(); ob.data = new; new.name = name; bpy.data.meshes.remove(old)
    for z, keep in cuts:
        bm = bmesh.new(); bm.from_mesh(ob.data)
        res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z), plane_no=(0, 0, 1),
                                     clear_inner=(keep == 'above'), clear_outer=(keep == 'below'))
        e = [x for x in res['geom_cut'] if isinstance(x, bmesh.types.BMEdge)]
        if e: bmesh.ops.holes_fill(bm, edges=e, sides=0)
        bm.to_mesh(ob.data); bm.free()
    if inset:   # pull the surface in along its normals by inset(z) (1.26 m units), e.g. to tuck one piece under another
        me = ob.data; me.update()
        for v in me.vertices: v.co -= v.normal * inset(v.co.z)
    ob.data.transform(Matrix.Scale(S, 4))
    C.smooth(ob); C.assign(ob, mat)
    ob['part'] = part; ob.color = (*ID[part], 1)
    if lump:   # hand-made shape: broad thumb dents, pressed pits, fine lumps (scaled by how lumpy this piece is)
        k = lump / 0.00022
        CV.geometry(ob, dents=0.0009 * k, pits=0.00016 * k, lumps=0.00016 * k)   # deep enough to read on a phone
    return ob


def on_face(x, z, lift=0.0):
    """point (1.26 m units) on the front of the head ellipsoid at (x, z), and the outward normal"""
    u, w = x / HEAD_R.x, (z - HEAD_C.z) / HEAD_R.z
    y = HEAD_C.y - HEAD_R.y * math.sqrt(max(0.0, 1 - u * u - w * w))
    p = Vector((x, y, z))
    n = Vector(((x - HEAD_C.x) / HEAD_R.x ** 2, (y - HEAD_C.y) / HEAD_R.y ** 2, (z - HEAD_C.z) / HEAD_R.z ** 2)).normalized()
    return p + n * lift, n


def arc(name, pts, radius, mat, coll):
    """a bevelled clay 'snake' through points (1.26 m units): brows, closed eyes, line mouths"""
    cd = bpy.data.curves.new(name, 'CURVE'); cd.dimensions = '3D'
    cd.bevel_depth = radius * S; cd.bevel_resolution = 3; cd.use_fill_caps = True
    sp = cd.splines.new('NURBS'); sp.points.add(len(pts) - 1)
    for pt, co in zip(sp.points, pts): pt.co = (*(Vector(co) * S), 1)
    sp.use_endpoint_u = True; sp.order_u = min(4, len(pts))
    ob = bpy.data.objects.new(name, cd); coll.objects.link(ob); cd.materials.append(mat)
    ob['part'] = 'skin'; ob.color = (*ID['skin'], 1)
    return ob


# ---------------------------------------------------------------- expressions
EXPR = {   # eyes variant, brow tilt (deg, + = inner ends up), brow lift (1.26 m units), mouth variant
    'neutral': ('open', 0, 0.0, 'line'), 'sleep': ('closed', 0, -0.002, 'line'),
    'worried': ('open', 14, 0.002, 'frown'), 'scared': ('wide', 16, 0.003, 'o'),
    'terrified': ('wide', 20, 0.005, 'scream'), 'surprised': ('wide', 0, 0.008, 'o'),
    'sad': ('half', 16, 0.001, 'frown'), 'smile': ('open', 0, 0.002, 'smile'),
    'happy': ('happy', 0, 0.004, 'smile'), 'suspicious': ('half', -10, -0.002, 'line'),
    'angry': ('open', -18, -0.003, 'frown'), 'relieved': ('closed', 6, 0.003, 'smile'),
    'stare': ('wide', 0, 0.0, 'line'),
}
EYES = ('open', 'half', 'closed', 'happy', 'wide')
MOUTHS = ('line', 'smile', 'frown', 'o', 'scream')


def fast_cycles(sc):
    """render settings benchmarked on the RTX 5090 laptop (scenes/haru_bench.py): 1.12 s per 1080x1920 frame vs
    3.37 s with the skill defaults, with no visible difference. Use after claylib.setup_render()."""
    c = sc.cycles
    c.adaptive_threshold = 0.03; c.adaptive_min_samples = 16
    c.max_bounces = 4; c.diffuse_bounces = 2; c.glossy_bounces = 2; c.transmission_bounces = 2
    c.transparent_max_bounces = 4; c.volume_bounces = 0
    c.use_light_tree = True; c.sample_clamp_indirect = 4.0
    try: c.denoising_use_gpu = True
    except AttributeError: pass
    sc.render.use_persistent_data = True


# ---------------------------------------------------------------- soft rest (hair squashes on floor / bed)
def colliders():
    c = bpy.data.collections.get('Colliders')
    if not c:
        c = bpy.data.collections.new('Colliders'); bpy.context.scene.collection.children.link(c)
    return c


def soft_rest(ob, offset=0.00015):
    """push any vertex that is under a support surface (Colliders) back up onto it, in WORLD space (works whatever
    the pivots do): a ray is cast straight down from 6 cm above each point"""
    ng = bpy.data.node_groups.get('soft_rest_world')
    if not ng:
        ng = bpy.data.node_groups.new('soft_rest_world', 'GeometryNodeTree')
        ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        N, L = ng.nodes, ng.links
        gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
        me = N.new('GeometryNodeObjectInfo'); me.transform_space = 'ORIGINAL'
        L.new(N.new('GeometryNodeSelfObject').outputs[0], me.inputs['Object'])
        inv = N.new('FunctionNodeInvertMatrix'); L.new(me.outputs['Transform'], inv.inputs[0])
        ci = N.new('GeometryNodeCollectionInfo'); ci.transform_space = 'ORIGINAL'; ci.inputs['Collection'].default_value = colliders()
        rz = N.new('GeometryNodeRealizeInstances'); L.new(ci.outputs[0], rz.inputs[0])
        pos = N.new('GeometryNodeInputPosition').outputs[0]
        tw = N.new('FunctionNodeTransformPoint'); L.new(pos, tw.inputs[0]); L.new(me.outputs['Transform'], tw.inputs[1])
        up = N.new('ShaderNodeVectorMath'); up.operation = 'ADD'; L.new(tw.outputs[0], up.inputs[0]); up.inputs[1].default_value = (0, 0, 0.06)
        rc = N.new('GeometryNodeRaycast'); L.new(rz.outputs[0], rc.inputs['Target Geometry']); L.new(up.outputs[0], rc.inputs['Source Position'])
        rc.inputs['Ray Direction'].default_value = (0, 0, -1); rc.inputs['Ray Length'].default_value = 0.12
        hz = N.new('ShaderNodeSeparateXYZ'); L.new(rc.outputs['Hit Position'], hz.inputs[0])
        wz = N.new('ShaderNodeSeparateXYZ'); L.new(tw.outputs[0], wz.inputs[0])
        top = N.new('ShaderNodeMath'); top.operation = 'ADD'; L.new(hz.outputs['Z'], top.inputs[0]); top.inputs[1].default_value = offset
        mx = N.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; L.new(wz.outputs['Z'], mx.inputs[0]); L.new(top.outputs[0], mx.inputs[1])
        sw = N.new('GeometryNodeSwitch'); sw.input_type = 'FLOAT'
        L.new(rc.outputs['Is Hit'], sw.inputs['Switch']); L.new(wz.outputs['Z'], sw.inputs['False']); L.new(mx.outputs[0], sw.inputs['True'])
        cb = N.new('ShaderNodeCombineXYZ'); L.new(wz.outputs['X'], cb.inputs['X']); L.new(wz.outputs['Y'], cb.inputs['Y']); L.new(sw.outputs[0], cb.inputs['Z'])
        back = N.new('FunctionNodeTransformPoint'); L.new(cb.outputs[0], back.inputs[0]); L.new(inv.outputs[0], back.inputs[1])
        sp = N.new('GeometryNodeSetPosition'); L.new(gi.outputs[0], sp.inputs['Geometry']); L.new(back.outputs[0], sp.inputs['Position'])
        L.new(sp.outputs[0], go.inputs[0])
    md = ob.modifiers.new('soft_rest', 'NODES'); md.node_group = ng
    return md


# ---------------------------------------------------------------- the puppet
class Haru:
    PIVOTS = [  # name, parent, rest position (1.26 m units)
        ('root', None, (0, 0, 0)), ('hips', 'root', (0, 0, 0.55)), ('spine', 'hips', (0, 0, 0.65)),
        ('chest', 'spine', (0, 0.01, 0.77)), ('neck', 'chest', (0, 0.012, 0.87)), ('head', 'neck', (0, 0.01, 0.975))]

    def __init__(self, loc=(0, 0, 0), yaw=0.0, name='haru', coll=None):
        self.name = name
        self.coll = coll or bpy.data.collections.new(name)
        if self.coll.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(self.coll)
        self.P = {}; self.rest = {}
        for pn, par, pos in self.PIVOTS: self._pivot(pn, par, pos)
        for side, tag in ((1, 'L'), (-1, 'R')):
            d = Vector((side * math.sin(A_REST), 0, -math.cos(A_REST)))
            sh = Vector((side * SH.x, SH.y, SH.z)); el = sh + d * L_UP; wr = el + d * L_FORE
            self._pivot('upper_arm.' + tag, 'chest', sh); self._pivot('forearm.' + tag, 'upper_arm.' + tag, el)
            self._pivot('hand.' + tag, 'forearm.' + tag, wr)
            self._pivot('thigh.' + tag, 'hips', (side * 0.062, 0, 0.55)); self._pivot('shin.' + tag, 'thigh.' + tag, (side * 0.063, 0, 0.30))
            self._pivot('foot.' + tag, 'shin.' + tag, (side * 0.064, 0.005, 0.085))
        self.M = self._materials()
        self.meshes = []                       # pieces that rest on things (ground contact)
        self.soft = []                         # pieces that squash instead
        self._build()
        self._face()
        self.root = self.P['root']; self.base_loc = Vector(loc); self.yaw = yaw
        self.root.location = self.base_loc; self.root.rotation_euler = (0, 0, yaw)
        self.expr('neutral')

    # ---- helpers
    def _pivot(self, pn, par, pos):
        e = bpy.data.objects.new(f'{self.name}_{pn}', None); self.coll.objects.link(e)
        e.empty_display_size = 0.004; e.rotation_mode = 'YXZ'
        wpos = Vector(pos) * S; self.rest[pn] = wpos
        if par: e.parent = self.P[par]; e.location = wpos - self.rest[par]
        else: e.location = wpos
        self.P[pn] = e

    def _attach(self, ob, pivot, contact=True):
        """parent a piece built at rest (world, puppet scale) to a pivot, keeping it where it is"""
        bpy.context.view_layer.update()
        ob.parent = self.P[pivot]; ob.matrix_parent_inverse = self.P[pivot].matrix_world.inverted()
        if contact: self.meshes.append(ob)
        return ob

    def _materials(self):
        def clay(n, key, **kw): return CV.clay(f'{self.name}_{n}', PAL[key], **kw)
        return {'hoodie': clay('hoodie', 'hoodie', sss=0.06, bump=0.7),
                'pants': clay('pants', 'pants', sss=0.04, bump=0.7),
                'skin': clay('skin', 'skin', rough=0.8, sss=0.12, bump=0.45, prints=0.7),
                'hair': clay('hair', 'hair', rough=0.72, sss=0.03, bump=0.7, prints=0.5, grooves=0.8, specks=0, film=0.2),
                'shoe': clay('shoe', 'shoe', sss=0.08, bump=0.55, specks=1.6),
                'sole': clay('sole', 'sole', bump=0.5),
                'mouth': clay('mouth', 'mouth', bump=0.2, prints=0, specks=0),
                'mouth_in': clay('mouth_in', 'mouth_in', bump=0.2, prints=0, specks=0),
                'brow': clay('brow', 'brow', bump=0.25, prints=0, specks=0),
                'white': clay('white', 'white', rough=0.6, sss=0.05, bump=0.2, prints=0, specks=0),
                'eye': CV.clay(f'{self.name}_eye', (0.012, 0.01, 0.01), gloss=True)}

    # ---- body
    def _build(self):
        M, co = self.M, self.coll
        s = Shape()                                                         # hoodie body (spine)
        s.ellipsoid((0, 0.012, 0.75), (0.135, 0.085, 0.14)); s.ellipsoid((0, 0, 0.63), (0.155, 0.094, 0.14))
        s.ellipsoid((0, 0, HEM + 0.06), (0.158, 0.094, 0.065)); s.ring((0, 0, HEM + 0.027), 0.15, 0.086, 0.022, 44)
        s.ring((0, 0.014, 0.918), 0.078, 0.068, 0.037, 22, tilt=0.9)       # hood collar, low at the front
        s.ellipsoid((0, 0.075, 0.86), (0.095, 0.032, 0.08))                 # hood on the back
        s.ellipsoid((0, -0.088, 0.6), (0.095, 0.02, 0.055))                 # kangaroo pocket
        for side in (1, -1): s.ball((side * 0.105, 0.01, 0.795), 0.062)     # shoulders
        self._attach(piece('hoodie', s, M['hoodie'], 'top', co, cuts=[(HEM, 'above')], smooth=8), 'spine')
        s = Shape()
        for side in (1, -1):
            s.capsule((side * 0.026, -0.066, 0.872), (side * 0.032, -0.093, 0.79), 0.0065); s.ball((side * 0.032, -0.093, 0.785), 0.0095)
        self._attach(piece('drawstrings', s, M['hoodie'], 'top', co, voxel=0.0016, smooth=3, lump=0.00006), 'chest', False)
        s = Shape().ellipsoid((0, 0, 0.58), (0.135, 0.095, 0.08))           # trousers' seat under the hoodie
        self._attach(piece('pelvis', s, M['pants'], 'pants', co, cuts=[(HEM + 0.045, 'below')]), 'hips')
        self._attach(piece('neck', Shape().capsule((0, 0.012, 0.84), (0, 0.012, 0.975), 0.043), M['skin'], 'skin', co,
                           voxel=0.003, smooth=4, lump=0.0001), 'neck')
        self._attach(piece('head', Shape().ellipsoid(HEAD_C, HEAD_R, seg=48), M['skin'], 'skin', co, voxel=0.003, lump=0.00012), 'head')
        for side, tag in ((1, 'L'), (-1, 'R')):
            d = Vector((side * math.sin(A_REST), 0, -math.cos(A_REST)))
            sh = Vector((side * SH.x, SH.y, SH.z)); el = sh + d * L_UP; wr = el + d * L_FORE
            s = Shape().capsule(sh, el, 0.062, 0.059).fold(sh, el, 0.62, 0.06, 0.02, 0.012, seed=1 + side)
            self._attach(piece('sleeve_up.' + tag, s, M['hoodie'], 'top', co), 'upper_arm.' + tag)
            s = Shape().capsule(el, wr - d * 0.012, 0.059, 0.058).ball(wr - d * 0.03, 0.062)
            for k, t in enumerate((0.12, 0.45, 0.72)):                          # the sleeve bunches toward the cuff
                s.fold(el, wr, t, 0.059, 0.019 + 0.003 * k, 0.01, seed=10 * k + side)
            self._attach(piece('sleeve_lo.' + tag, s, M['hoodie'], 'top', co), 'forearm.' + tag)
            out = Vector((math.cos(A_REST), 0, math.sin(A_REST))) if side > 0 else Vector((-math.cos(A_REST), 0, math.sin(A_REST)))
            Mx = Matrix((out, Vector((0, -1, 0)), -d)).transposed()
            P = lambda u, v, w: wr + Mx @ Vector((u, v, w))
            s = Shape().capsule(P(0, 0, 0.02), P(0, 0, -0.012), 0.022, 0.021).ellipsoid(P(0, 0, -0.038), (0.02, 0.035, 0.037), rot=Mx)
            for vy in (-0.022, -0.0073, 0.0073, 0.022):
                ln = 0.034 if abs(vy) < 0.01 else 0.028
                s.capsule(P(0.001, vy, -0.062), P(-0.008, vy * 1.05, -0.062 - ln), 0.0088, 0.008, 16)
            s.capsule(P(-0.007, -0.029, -0.028), P(-0.018, -0.04, -0.058), 0.0095, 0.0088, 16)
            self._attach(piece('hand.' + tag, s, M['skin'], 'skin', co, voxel=0.0015, smooth=5, lump=0.00006), 'hand.' + tag)
            hip, knee, ank = Vector((side * 0.062, 0, 0.55)), Vector((side * 0.063, 0, 0.30)), Vector((side * 0.064, 0.005, 0.075))
            s = Shape().capsule(hip, knee, 0.06, 0.055).fold(hip, knee, 0.9, 0.056, 0.017, 0.01, seed=20 + side)
            self._attach(piece('thigh.' + tag, s, M['pants'], 'pants', co), 'thigh.' + tag)
            s = Shape().capsule(knee, ank, 0.055, 0.054)
            for k, t in enumerate((0.7, 0.88)):                                 # the trousers bunch over the shoe
                s.fold(knee, ank, t, 0.054, 0.016 + 0.003 * k, 0.012, seed=30 + k + side)
            self._attach(piece('shin.' + tag, s, M['pants'], 'pants', co, cuts=[(0.062, 'above')]), 'shin.' + tag)
            x = side * 0.074
            s = Shape().ellipsoid((x, -0.028, 0.044), (0.056, 0.094, 0.044)).ellipsoid((x, -0.075, 0.034), (0.054, 0.05, 0.032))
            s.capsule((side * 0.068, 0.005, 0.06), (side * 0.068, 0.005, 0.085), 0.047)
            self._attach(piece('shoe.' + tag, s, M['shoe'], 'shoes', co, voxel=0.003, smooth=5, cuts=[(0.016, 'above')]), 'foot.' + tag)
            self._attach(piece('sole.' + tag, Shape().ellipsoid((x, -0.03, 0.014), (0.061, 0.103, 0.017)), M['sole'], 'shoes', co,
                               voxel=0.003, smooth=4, lump=0.00008, cuts=[(0.0, 'above')]), 'foot.' + tag)
        # hair: the crown follows the head, the lengths resting on the shoulders stay with the chest; they overlap
        def hair_shape():
            s = Shape()
            s.ellipsoid((0, 0.05, 1.09), (0.13, 0.112, 0.172)); s.ellipsoid((0, 0.03, 1.16), (0.124, 0.11, 0.1))
            for sd in (1, -1):
                s.ellipsoid((sd * 0.128, 0.045, 1.0), (0.03, 0.085, 0.165)); s.ellipsoid((sd * 0.126, 0.03, 0.89), (0.031, 0.07, 0.06))
            s.ellipsoid((0, 0.075, 0.93), (0.158, 0.08, 0.135)); s.ellipsoid((0, 0.08, 0.86), (0.155, 0.065, 0.065))   # one back slab over the side panels
            s.ellipsoid((-0.015, -0.068, 1.17), (0.1, 0.022, 0.042), rot=(math.radians(-25), math.radians(-12), 0))
            s.ellipsoid((-0.07, -0.05, 1.135), (0.045, 0.025, 0.05), rot=(math.radians(-20), 0, 0))
            s.ellipsoid((0.05, -0.05, 1.19), (0.06, 0.03, 0.035), rot=(math.radians(-30), 0, 0))
            return s
        top = piece('hair', hair_shape(), M['hair'], 'hair', co, voxel=0.004, smooth=8, lump=0.0002, cuts=[(0.94, 'above')])
        low = piece('hair_ends', hair_shape(), M['hair'], 'hair', co, voxel=0.004, smooth=8, lump=0.0002, cuts=[(0.985, 'below')],
                    inset=lambda z: 0.003 * min(1.0, max(0.0, (z - 0.93) / 0.03)))     # tucked under the crown piece
        for ob, pv in ((top, 'head'), (low, 'chest')):
            self._attach(ob, pv, contact=False); soft_rest(ob); self.soft.append(ob)

    # ---- face: replacement parts under variant empties, swapped by scale
    def _face(self):
        M, co = self.M, self.coll
        self.eyes = {v: [] for v in EYES}; self.mouths = {}; self.brows = []
        def holder(name, at):
            e = bpy.data.objects.new(f'{self.name}_{name}', None); co.objects.link(e)
            e.location = Vector(at) * S; e.empty_display_size = 0.002
            self._attach(e, 'head', False)
            return e
        def put(ob, h):
            bpy.context.view_layer.update(); ob.parent = h; ob.matrix_parent_inverse = h.matrix_world.inverted(); return ob
        for side, tag in ((1, 'L'), (-1, 'R')):
            ex = side * 0.038; p, n = on_face(ex, 1.045)
            R = n.to_track_quat('-Y', 'Z').to_matrix()
            def bead(nm, r, at=None, mat=None):
                return piece(nm, Shape().ellipsoid(at or p - n * 0.002, r, rot=R), mat or M['eye'], 'skin', co, voxel=0.0008, smooth=3, lump=0)
            h = holder(f'eye_open.{tag}', p); put(bead(f'eye_bead.{tag}', (0.0115, 0.006, 0.0125)), h); self.eyes['open'].append(h)
            h = holder(f'eye_half.{tag}', p); put(bead(f'eye_halfbead.{tag}', (0.0115, 0.005, 0.0056), at=p - n * 0.002 - Vector((0, 0, 0.003))), h)
            put(arc(f'eye_halflid.{tag}', [on_face(ex + k * 0.013, 1.048 + 0.0015 * (1 - k * k), 0.002)[0] for k in (-1, -0.5, 0, 0.5, 1)],
                    0.0028, M['skin'], co), h); self.eyes['half'].append(h)
            h = holder(f'eye_closed.{tag}', p)
            put(arc(f'eye_lid.{tag}', [on_face(ex + k * 0.013, 1.043 - 0.004 * (1 - k * k), 0.0015)[0] for k in (-1, -0.5, 0, 0.5, 1)],
                    0.0024, M['brow'], co), h); self.eyes['closed'].append(h)
            h = holder(f'eye_happy.{tag}', p)
            put(arc(f'eye_up.{tag}', [on_face(ex + k * 0.013, 1.041 + 0.005 * (1 - k * k), 0.0015)[0] for k in (-1, -0.5, 0, 0.5, 1)],
                    0.0024, M['brow'], co), h); self.eyes['happy'].append(h)
            h = holder(f'eye_wide.{tag}', p)
            put(piece(f'eye_white.{tag}', Shape().ellipsoid(p - n * 0.0006, (0.0195, 0.0028, 0.021), rot=R), M['white'], 'skin', co,
                      voxel=0.0008, smooth=3, lump=0), h)
            put(bead(f'eye_pupil.{tag}', (0.0068, 0.004, 0.0072), at=p + n * 0.0014), h); self.eyes['wide'].append(h)
            bc = on_face(side * 0.04, 1.095, 0.0005)[0]
            h = holder(f'brow.{tag}', bc); h.rotation_mode = 'YXZ'
            put(arc(f'brow_arc.{tag}', [on_face(side * x_, 1.096 + 0.0012 * (1 - ((x_ - 0.04) / 0.018) ** 2), 0.0005)[0]
                                         for x_ in (0.022, 0.031, 0.04, 0.049, 0.058)], 0.0032, M['brow'], co), h)
            self.brows.append((h, side, bc))
        p, n = on_face(0, 0.995, 0.004)
        self._attach(piece('nose', Shape().ellipsoid(p, (0.0105, 0.009, 0.0098), seg=24), M['skin'], 'skin', co,
                           voxel=0.0008, smooth=3, lump=0), 'head', False)
        mc, mn = on_face(0, 0.957, 0.0005)
        R = mn.to_track_quat('-Y', 'Z').to_matrix()
        def mline(nm, curve):
            return arc(nm, [on_face(x_, 0.957 + curve * (x_ / 0.014) ** 2, 0.0005)[0] for x_ in (-0.014, -0.007, 0, 0.007, 0.014)],
                       0.0024, M['mouth'], co)
        for v, ob in (('line', mline('mouth_line', 0.0)), ('smile', mline('mouth_smile', 0.0045)), ('frown', mline('mouth_frown', -0.0038))):
            h = holder(f'mouth_{v}', mc); put(ob, h); self.mouths[v] = h
        for v, r, dz in (('o', (0.0065, 0.004, 0.0085), 0.0), ('scream', (0.021, 0.005, 0.026), -0.012)):
            h = holder(f'mouth_{v}', mc)
            put(piece(f'mouth_{v}_in', Shape().ellipsoid(mc + Vector((0, 0, dz)) - mn * 0.001, r, rot=R), M['mouth_in'], 'skin', co,
                      voxel=0.0008, smooth=3, lump=0), h)
            self.mouths[v] = h

    # ---- posing
    def pose(self, spec):
        for pn, e in self.P.items():
            if pn == 'root': continue
            e.rotation_euler = (math.radians(spec.get((pn, 'x'), 0.0)), math.radians(spec.get((pn, 'y'), 0.0)),
                                math.radians(spec.get((pn, 'z'), 0.0)))

    def place(self, loc=None, yaw=None, lift=0.0):
        if loc is not None: self.base_loc = Vector(loc)
        if yaw is not None: self.yaw = yaw
        self.root.location = self.base_loc + Vector((0, 0, lift)); self.root.rotation_euler = (0, 0, self.yaw)

    def lowest(self):
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); lo = 9.0
        for ob in self.meshes:
            ev = ob.evaluated_get(dg); me = ev.to_mesh()
            co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
            Mw = np.array(ev.matrix_world); lo = min(lo, float((co.reshape(-1, 3) @ Mw[2, :3] + Mw[2, 3]).min()))
            ev.to_mesh_clear()
        return lo

    def ground(self, floor=0.0, lift=0.0):
        """put her lowest point exactly on the floor (plus an optional lift for hops)"""
        self.root.location.z = self.base_loc.z
        self.root.location.z += floor - self.lowest() + lift

    def expr(self, name, blink=False):
        eyes, tilt, lift, mouth = EXPR[name]
        if blink: eyes = 'closed'
        for v, hs in self.eyes.items():
            for h in hs: h.scale = (1, 1, 1) if v == eyes else (1e-4,) * 3
        for v, h in self.mouths.items(): h.scale = (1, 1, 1) if v == mouth else (1e-4,) * 3
        for h, side, bc in self.brows:
            h.rotation_euler = (0, math.radians(side * tilt), 0)   # about the face normal: + raises the inner end
            h.delta_location = (0, 0, lift * S)                      # up the face

    def key(self, f):
        C.key(self.root, f, loc=tuple(self.root.location), rot=tuple(self.root.rotation_euler))
        for pn, e in self.P.items():
            if pn != 'root': C.key(e, f, rot=tuple(e.rotation_euler))
        for hs in self.eyes.values():
            for h in hs: C.key(h, f, scale=tuple(h.scale))
        for h in self.mouths.values(): C.key(h, f, scale=tuple(h.scale))
        for h, _, _ in self.brows:
            C.key(h, f, rot=tuple(h.rotation_euler)); h.keyframe_insert('delta_location', frame=f)
