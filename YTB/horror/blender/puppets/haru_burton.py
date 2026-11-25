"""Haru as a Tim Burton style stop-motion puppet: silicone skin, real-fabric clothes, sculpted hair, glass eyes.

Built to YTB/channel_art/burton_turnaround.png (Artlist, Nov 2026): a big head on a thin neck, slim body, long thin
arms and legs, spindly fingers, huge wide-set glass eyes with dark rings, long straight black hair with a side
fringe, an oversized olive-mustard knitted hoodie, slim grey woven trousers, canvas sneakers.

Same rig as the clay puppet (puppets/haru_puppet.py): rigid pieces on pivot empties named root, hips, spine, chest,
neck, head, upper_arm/forearm/hand.L/R, thigh/shin/foot.L/R, so the pose library and the 12 fps shot code work
unchanged. 12.6 cm tall, built in metres. Differences: the face is mechanical like Corpse Bride (eyeballs that
look around, eyelids that rotate over them, pupils that widen or shrink), plus posable brows and replacement mouths.

    import haru_burton as HB; h = HB.HaruBurton(loc=(0, 0, 0)); h.pose({...}); h.ground(); h.expr('scared'); h.key(f)
"""
import bpy, bmesh, math, os, sys, importlib
import numpy as np
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import haru_puppet as HP
import burton_materials as BM
importlib.reload(BM)
from haru_puppet import Shape, piece, arc, soft_rest, S

# ---------------------------------------------------------------- proportions (1.26 m units, x0.1 when built)
HEAD_C, HEAD_R = Vector((0, 0, 1.095)), Vector((0.142, 0.12, 0.15))  # broad round face, chin as low as the sheet (audit)
SH = Vector((0.108, 0.01, 0.815)); A_REST = math.radians(9); L_UP, L_FORE = 0.19, 0.185
HEM = 0.488
EYE_X, EYE_Z, EYE_R = 0.062, 1.078, 0.03      # big Burton eyes, but a girl's, not an insect's

PAL = {'skin': '#d5c5b9', 'lid': '#b9a8a8', 'socket': '#665468', 'hoodie': '#a07c3c', 'pants': '#4d5153',
       'canvas': '#e9e6df', 'sole': '#d9d6cf', 'hair': '#0b0b0c', 'brow': '#2a2526', 'lips': '#c2a19c', 'lip_line': '#5b3b3b', 'rubber': '#ecebe6', 'stripe': '#8e9094', 'mouth_in': '#2a1210'}

EXPR = {  # upper lid (deg: -50 wide open .. 90 shut), lower lid (deg: 25 down .. -50 up), pupil, brow tilt (+ = inner up),
          # brow lift (1.26 m units), mouth, gaze (yaw, pitch deg)
    'neutral': (-52, 46, 1.0, 6, 0.0, 'line', (0, 0)),
    'sleep': (90, 10, 1.0, 0, -0.002, 'line', (0, 0)),
    'worried': (-40, 42, 1.0, 18, 0.004, 'frown', (0, 0)),
    'scared': (-62, 52, 0.7, 20, 0.006, 'o', (0, 0)),
    'terrified': (-68, 56, 0.55, 24, 0.009, 'scream', (0, 0)),
    'surprised': (-68, 54, 0.8, 0, 0.012, 'o', (0, 0)),
    'sad': (0, 40, 1.05, 22, 0.003, 'frown', (0, -8)),
    'smile': (-40, 20, 1.05, 4, 0.003, 'smile', (0, 0)),
    'happy': (-25, -5, 1.1, 0, 0.006, 'smile', (0, 0)),
    'suspicious': (5, 25, 0.9, -12, -0.003, 'line', (-18, 0)),
    'angry': (0, 30, 0.85, -22, -0.005, 'frown', (0, 0)),
    'relieved': (88, 5, 1.0, 8, 0.004, 'smile', (0, 0)),
    'stare': (-68, 56, 0.4, 0, 0.0, 'line', (0, 0)),
}
MOUTHS = ('line', 'smile', 'frown', 'o', 'scream')


TAPER_X, TAPER_Y = 0.1, 0.04        # a soft, wide U-shaped jaw with full cheeks (like the sheet), no pointed chin


def taper_k(z):
    t = min(1.0, max(0.0, (HEAD_C.z - z) / HEAD_R.z))
    return 1 - TAPER_X * t * t, 1 - TAPER_Y * t * t


def taper_head(bm):
    for v in bm.verts:
        kx, ky = taper_k(v.co.z)
        v.co.x = HEAD_C.x + (v.co.x - HEAD_C.x) * kx; v.co.y = HEAD_C.y + (v.co.y - HEAD_C.y) * ky


def on_face(x, z, lift=0.0):
    """point (1.26 m units) on the front of the tapered head at (x, z), and its outward normal"""
    kx, ky = taper_k(z)
    u, w = (x / kx) / HEAD_R.x, (z - HEAD_C.z) / HEAD_R.z
    y0 = -HEAD_R.y * math.sqrt(max(0.0, 1 - u * u - w * w))
    p = Vector((x, HEAD_C.y + y0 * ky, z))
    n = Vector(((x / kx) / HEAD_R.x ** 2 / kx, y0 / HEAD_R.y ** 2 / ky, (z - HEAD_C.z) / HEAD_R.z ** 2)).normalized()
    return p + n * lift, n


def hair_block(seed=4):
    """the hair as one sculpted block (1.26 m units): a cap over the skull, flat sheets hanging in front of the
    shoulders and down the back, tapered locks at the ends, and a fringe swept from a part on her left across the
    forehead to her right. hair_grooves() then carves the strand grooves into it."""
    import random
    rnd = random.Random(seed); s = Shape()
    s.ellipsoid((0, 0.038, 1.122), (0.153, 0.137, 0.152))                  # over the whole skull, set back so the face shows
    for sd in (1, -1):
        s.ellipsoid((sd * 0.15, 0.06, 0.97), (0.02, 0.066, 0.2))          # flat sheets outside the cheeks, behind the ears
        for k in range(6):                                                # tapered locks at the ends
            y = 0.0 + 0.017 * k
            s.capsule((sd * 0.15, y, 0.86), (sd * (0.149 + rnd.uniform(-0.005, 0.005)), y + rnd.uniform(-0.004, 0.004),
                                              0.755 + rnd.uniform(-0.02, 0.02)), 0.011, 0.003)
    s.ellipsoid((0, 0.08, 0.95), (0.142, 0.05, 0.22))                      # one flat sheet down the back
    for k in range(13):
        x = -0.128 + 0.0213 * k
        s.capsule((x, 0.08, 0.82), (x + rnd.uniform(-0.006, 0.006), 0.084, 0.705 + rnd.uniform(-0.02, 0.02)), 0.014, 0.0035)
    s.ellipsoid((-0.01, -0.074, 1.19), (0.12, 0.018, 0.05), rot=(math.radians(-32), math.radians(-15), 0))  # fringe, flat on the forehead
    s.ellipsoid((-0.09, -0.06, 1.15), (0.045, 0.02, 0.07), rot=(math.radians(-20), 0, 0))
    s.ellipsoid((0.07, -0.05, 1.21), (0.06, 0.02, 0.035), rot=(math.radians(-35), 0, 0))
    return s


def hair_grooves(ob, n=70, depth=0.00035):
    """carve sculpted strand grooves into a hair piece (puppet scale): n wavy grooves running down from the crown,
    by angle round the vertical axis through the head (x = y = 0), with uneven depth. Geometry nodes, before
    soft_rest, so they squash with the hair."""
    ng = bpy.data.node_groups.get('hair_grooves')
    if not ng:
        ng = bpy.data.node_groups.new('hair_grooves', 'GeometryNodeTree')
        ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        N, L = ng.nodes, ng.links
        gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
        pos = N.new('GeometryNodeInputPosition').outputs[0]
        sep = N.new('ShaderNodeSeparateXYZ'); L.new(pos, sep.inputs[0])
        def m(op, a, b=None, c=None):
            x = N.new('ShaderNodeMath'); x.operation = op
            for i, v in enumerate((a, b, c)):
                if v is None: continue
                if isinstance(v, (int, float)): x.inputs[i].default_value = v
                else: L.new(v, x.inputs[i])
            return x.outputs[0]
        def noise(scale):
            t = N.new('ShaderNodeTexNoise'); L.new(pos, t.inputs['Vector']); t.inputs['Scale'].default_value = scale
            t.inputs['Detail'].default_value = 2; return t.outputs['Fac']
        ang = m('ARCTAN2', sep.outputs['X'], sep.outputs['Y'])
        ang = m('MULTIPLY_ADD', noise(60.0), 0.35, ang)                  # wavy, not ruler-straight
        g = m('POWER', m('ABSOLUTE', m('SINE', m('MULTIPLY', ang, n / 2.0))), 0.35)
        dep = m('MULTIPLY', m('MULTIPLY_ADD', noise(25.0), 1.3, -0.15), depth)
        off = m('MULTIPLY', m('SUBTRACT', 1.0, g), dep)                   # cut in between the locks
        nrm = N.new('GeometryNodeInputNormal').outputs[0]
        sc = N.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'; L.new(nrm, sc.inputs[0]); L.new(m('MULTIPLY', off, -1.0), sc.inputs['Scale'])
        sp = N.new('GeometryNodeSetPosition'); L.new(gi.outputs[0], sp.inputs['Geometry']); L.new(sc.outputs[0], sp.inputs['Offset'])
        L.new(sp.outputs[0], go.inputs[0])
    md = ob.modifiers.new('grooves', 'NODES'); md.node_group = ng
    return md


def eye_frame(side):
    """eye centre (1.26 m units) and a frame whose -Y looks out of the face, mostly forward"""
    p, n = on_face(side * EYE_X, EYE_Z)
    f = (n.lerp(Vector((0, -1, 0)), 0.6)).normalized()
    c = p - f * EYE_R * 0.6                                    # sunk in: ~40% of the eyeball shows, no bulging
    y = -f; z = (Vector((0, 0, 1)) - y * y.z).normalized(); x = y.cross(z)
    return c, Matrix((x, y, z)).transposed(), p


class HaruBurton(HP.Haru):
    PIVOTS = [('root', None, (0, 0, 0)), ('hips', 'root', (0, 0, 0.52)), ('spine', 'hips', (0, 0, 0.62)),
              ('chest', 'spine', (0, 0.01, 0.74)), ('neck', 'chest', (0, 0.012, 0.86)), ('head', 'neck', (0, 0.01, 0.985))]

    def __init__(self, loc=(0, 0, 0), yaw=0.0, name='haruB', coll=None):
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
            self._pivot('thigh.' + tag, 'hips', (side * 0.05, 0, 0.52)); self._pivot('shin.' + tag, 'thigh.' + tag, (side * 0.05, 0, 0.30))
            self._pivot('foot.' + tag, 'shin.' + tag, (side * 0.05, 0.005, 0.09))
        self.M = self._materials()
        self.meshes, self.soft = [], []
        self._build(); self._face()
        self.root = self.P['root']; self.base_loc = Vector(loc); self.yaw = yaw
        self.root.location = self.base_loc; self.root.rotation_euler = (0, 0, yaw)
        self.expr('neutral')

    def _materials(self):
        sockets = [tuple(eye_frame(s)[2] * S) for s in (1, -1)]
        n = self.name
        return {'face': BM.silicone(f'{n}_face', PAL['skin'], sockets=sockets, socket_color=PAL['socket'], socket_r=EYE_R * 1.7 * S),
                'skin': BM.silicone(f'{n}_skin', PAL['skin']), 'lid': BM.lid(f'{n}_lid', PAL['lid']),
                'hoodie': BM.fabric(f'{n}_hoodie', PAL['hoodie'], 'knit'), 'pants': BM.fabric(f'{n}_pants', PAL['pants'], 'weave'),
                'canvas': BM.fabric(f'{n}_canvas', PAL['canvas'], 'weave', fuzz=0.5, scale=2200, dark=0.85), 'sole': BM.silicone(f'{n}_sole', PAL['sole']),
                'hair': BM.hair(f'{n}_hair', PAL['hair']), 'eye': BM.glass_eye(f'{n}_eye'),
                'brow': BM.silicone(f'{n}_brow', PAL['brow']), 'lips': BM.silicone(f'{n}_lips', PAL['lips']),
                'lip_line': BM.silicone(f'{n}_lip_line', PAL['lip_line']), 'rubber': BM.silicone(f'{n}_rubber', PAL['rubber']),
                'stripe': BM.silicone(f'{n}_stripe', PAL['stripe']),
                'mouth_in': BM.silicone(f'{n}_mouth_in', PAL['mouth_in'])}

    # ---- body
    def _build(self):
        M, co = self.M, self.coll
        s = Shape()                                                              # oversized knitted hoodie
        s.ellipsoid((0, 0.01, 0.73), (0.118, 0.098, 0.13)); s.ellipsoid((0, 0, 0.6), (0.135, 0.106, 0.13))
        s.ellipsoid((0, 0, HEM + 0.07), (0.142, 0.106, 0.06))
        s.ring((0, 0, HEM + 0.017), 0.118, 0.09, 0.019, 60)                      # ribbed hem band, gathered under the body
        cowl = [(0.012, -0.088, 0.815), (0.045, -0.07, 0.85), (0.068, -0.035, 0.88), (0.075, 0.01, 0.9), (0.06, 0.05, 0.915),
                (0.0, 0.075, 0.925)]                                              # rolled hood edge, from the V round to the back
        for sd in (1, -1):
            pts = [Vector((sd * x, y, z)) for x, y, z in cowl]
            for i in range(len(pts) - 1):
                r0 = 0.02 + 0.012 * min(1.0, i / 2.0); r1 = 0.02 + 0.012 * min(1.0, (i + 1) / 2.0)
                s.capsule(pts[i], pts[i + 1], r0, r1, 16)
        s.capsule((0.0, -0.088, 0.81), (0.0, -0.095, 0.79), 0.012, 0.008, 12)       # where the two sides cross
        s.ellipsoid((0, 0.085, 0.83), (0.1, 0.032, 0.1))                          # the hood hangs down the back...
        s.capsule((0, 0.09, 0.79), (0, 0.098, 0.705), 0.045, 0.006, 16)           # ...to a point
        s.ellipsoid((0, -0.1, 0.575), (0.08, 0.015, 0.05))                       # kangaroo pocket
        s.ellipsoid((0, -0.104, 0.615), (0.08, 0.009, 0.006))                     # pocket top edge
        for side in (1, -1): s.ball((side * 0.094, 0.01, 0.8), 0.058)      # shoulders fill up under the hood
        self._attach(piece('hoodie', s, M['hoodie'], 'top', co, cuts=[(HEM, 'above')], smooth=8, lump=0.00008), 'spine')
        s = Shape()
        for side in (1, -1):
            s.capsule((side * 0.03, -0.1, 0.83), (side * 0.034, -0.112, 0.72), 0.005); s.ball((side * 0.034, -0.112, 0.715), 0.0075)  # from the V
        self._attach(piece('drawstrings', s, M['hoodie'], 'top', co, voxel=0.0014, smooth=3, lump=0), 'chest', False)
        self._attach(piece('pelvis', Shape().ellipsoid((0, 0, 0.54), (0.115, 0.078, 0.065)), M['pants'], 'pants', co,
                           cuts=[(HEM + 0.04, 'below')], lump=0), 'hips')
        self._attach(piece('neck', Shape().capsule((0, 0.012, 0.85), (0, 0.01, 1.0), 0.026), M['skin'], 'skin', co,
                           voxel=0.0025, smooth=4, lump=0), 'neck')
        head = Shape().ellipsoid(HEAD_C, HEAD_R, seg=64)
        taper_head(head.bm)                                                       # one smooth egg, narrow at the chin
        for side in (1, -1): head.ellipsoid((side * 0.148, -0.006, 1.07), (0.012, 0.024, 0.032))  # ears, peeking out of the hair
        self._attach(piece('head', head, M['face'], 'skin', co, voxel=0.0025, smooth=5, lump=0), 'head')
        for side, tag in ((1, 'L'), (-1, 'R')):
            d = Vector((side * math.sin(A_REST), 0, -math.cos(A_REST)))
            sh = Vector((side * SH.x, SH.y, SH.z)); el = sh + d * L_UP; wr = el + d * L_FORE
            s = Shape().capsule(sh, el, 0.052, 0.048).fold(sh, el, 0.6, 0.05, 0.016, 0.01, seed=1 + side)
            self._attach(piece('sleeve_up.' + tag, s, M['hoodie'], 'top', co, lump=0.00008), 'upper_arm.' + tag)
            s = Shape().capsule(el, wr - d * 0.03, 0.048, 0.053)       # sleeve widens before the cuff
            for k, t in enumerate((0.15, 0.5)): s.fold(el, wr, t, 0.048, 0.015, 0.01, seed=10 * k + side)
            s.fold(el, wr, 0.93, 0.036, 0.013, 0.0, seed=7, n=40)                  # gathered ribbed cuff
            self._attach(piece('sleeve_lo.' + tag, s, M['hoodie'], 'top', co, lump=0.00008), 'forearm.' + tag)
            out = Vector((math.cos(A_REST), 0, math.sin(A_REST))) if side > 0 else Vector((-math.cos(A_REST), 0, math.sin(A_REST)))
            Mx = Matrix((out, Vector((0, -1, 0)), -d)).transposed()
            Mx = Matrix.Rotation(math.radians(-side * 40), 3, d) @ Mx     # turned in: backs of the hands show from the front
            P = lambda u, v, w: wr + Mx @ Vector((u, v, w))
            s = Shape().capsule(P(0, 0, 0.02), P(0, 0, -0.012), 0.02, 0.019).ellipsoid(P(0, 0, -0.037), (0.017, 0.036, 0.04), rot=Mx)
            for vy, ln in ((-0.025, 0.048), (-0.0085, 0.06), (0.0085, 0.057), (0.025, 0.046)):     # long spindly fingers
                s.capsule(P(0.001, vy, -0.07), P(-0.008, vy * 1.08, -0.07 - ln), 0.0075, 0.006, 16)
            s.capsule(P(-0.007, -0.033, -0.03), P(-0.02, -0.046, -0.068), 0.0082, 0.0068, 16)
            self._attach(piece('hand.' + tag, s, M['skin'], 'skin', co, voxel=0.0011, smooth=4, lump=0), 'hand.' + tag)
            hip, knee, ank = Vector((side * 0.05, 0, 0.52)), Vector((side * 0.05, 0, 0.30)), Vector((side * 0.05, 0.005, 0.09))
            self._attach(piece('thigh.' + tag, Shape().capsule(hip, knee, 0.042, 0.038), M['pants'], 'pants', co, lump=0.00005), 'thigh.' + tag)
            s = Shape().capsule(knee, ank, 0.038, 0.035).fold(knee, ank, 0.86, 0.035, 0.011, 0.008, seed=30 + side)
            self._attach(piece('shin.' + tag, s, M['pants'], 'pants', co, cuts=[(0.112, 'above')], lump=0.00005), 'shin.' + tag)
            self._attach(piece('ankle.' + tag, Shape().capsule((side * 0.05, 0.005, 0.06), (side * 0.05, 0.005, 0.125), 0.021),
                               M['skin'], 'skin', co, voxel=0.0015, smooth=3, lump=0), 'foot.' + tag)
            x = side * 0.052
            sole = Shape().ellipsoid((x, -0.042, 0.013), (0.048, 0.126, 0.09))          # thick white rubber sole, flat top and bottom
            self._attach(piece('sole.' + tag, sole, M['rubber'], 'shoes', co, voxel=0.002, smooth=4, lump=0,
                               cuts=[(0.0, 'above'), (0.024, 'below')]), 'foot.' + tag)
            stripe = Shape()
            for i in range(240):                                                     # grey stripe round the sole
                t = 2 * math.pi * i / 240
                stripe.ball((x + 0.0485 * math.cos(t), -0.042 + 0.1265 * math.sin(t), 0.009), 0.0016, 8)
            self._attach(piece('stripe.' + tag, stripe, M['stripe'], 'shoes', co, voxel=0.0012, smooth=2, lump=0), 'foot.' + tag, False)
            UC, UR = (x, -0.032, 0.024), (0.039, 0.1, 0.05)                       # canvas upper: high instep, low toe
            up = Shape().ellipsoid(UC, UR).ellipsoid((x, 0.04, 0.045), (0.038, 0.04, 0.04))   # heel counter rises to the ankle
            self._attach(piece('shoe.' + tag, up, M['canvas'], 'shoes', co, voxel=0.0018, smooth=5, lump=0, cuts=[(0.022, 'above')]),
                         'foot.' + tag)
            toe = Shape().ellipsoid((x, -0.118, 0.022), (0.04, 0.024, 0.019))          # thin rubber toe cap on the very tip
            self._attach(piece('toecap.' + tag, toe, M['rubber'], 'shoes', co, voxel=0.0015, smooth=4, lump=0, cuts=[(0.022, 'above')]),
                         'foot.' + tag)

            def surf(dx, y, lift=0.0024):                                           # a point on top of the upper
                q = 1 - ((y - UC[1]) / UR[1]) ** 2 - (dx / UR[0]) ** 2
                return (x + dx, y, UC[2] + UR[2] * math.sqrt(max(q, 0.0)) + lift)
            s = Shape().ellipsoid((x, 0.004, 0.077), (0.017, 0.018, 0.005), rot=(math.radians(-35), 0, 0))   # tongue peeks out
            eye = Shape()
            for k in range(4):                                                      # criss-cross laces, lying on the canvas
                y0 = -0.008 - 0.017 * k
                for a in (1, -1):
                    pa, pm, pb = surf(a * 0.018, y0), surf(0, y0 - 0.006), surf(-a * 0.018, y0 - 0.012)
                    s.capsule(pa, pm, 0.0026, 0.0026, 10).capsule(pm, pb, 0.0026, 0.0026, 10)
                    eye.ball(surf(a * 0.02, y0, 0.0008), 0.0032, 10)             # eyelets
            self._attach(piece('eyelets.' + tag, eye, M['stripe'], 'shoes', co, voxel=0.0008, smooth=2, lump=0), 'foot.' + tag, False)
            self._attach(piece('laces.' + tag, s, M['canvas'], 'shoes', co, voxel=0.0009, smooth=2, lump=0), 'foot.' + tag, False)

        # the hair is ONE piece: the cap follows the head, the ends follow the chest, and the band between bends
        # smoothly, so it never splits in two when she turns her head
        hair = piece('hair', hair_block(), M['hair'], 'hair', co, voxel=0.0025, smooth=6, lump=0)
        hair_grooves(hair)
        def w_head(z):
            t = min(1.0, max(0.0, (z / S - 0.9) / 0.1)); return t * t * (3 - 2 * t)
        self._skin(hair, w_head)
        soft_rest(hair); self.soft.append(hair)

    def _skin(self, ob, w_head):
        """bend a piece between the head and chest pivots with a two-bone armature whose bones follow the pivots"""
        bpy.context.view_layer.update()
        ad = bpy.data.armatures.new(f'{self.name}_rig'); rig = bpy.data.objects.new(f'{self.name}_rig', ad)
        self.coll.objects.link(rig); rig.hide_render = True
        bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
        for pv in ('head', 'chest'):
            b = ad.edit_bones.new(pv); b.head = self.rest[pv]; b.tail = self.rest[pv] + Vector((0, 0, 0.01))
        bpy.ops.object.mode_set(mode='OBJECT')
        for pv in ('head', 'chest'):
            c = rig.pose.bones[pv].constraints.new('CHILD_OF'); c.target = self.P[pv]
            c.inverse_matrix = self.P[pv].matrix_world.inverted(); c.set_inverse_pending = False
        gh, gc = ob.vertex_groups.new(name='head'), ob.vertex_groups.new(name='chest')
        for v in ob.data.vertices:
            w = w_head(v.co.z)
            if w > 0: gh.add([v.index], w, 'REPLACE')
            if w < 1: gc.add([v.index], 1 - w, 'REPLACE')
        md = ob.modifiers.new('rig', 'ARMATURE'); md.object = rig; md.use_vertex_groups = True
        self.rig = rig

    # ---- mechanical face: eyeballs that look around, eyelids that rotate over them, brows, replacement mouths
    def _empty(self, name, loc, mat3=None, parent=None):
        e = bpy.data.objects.new(f'{self.name}_{name}', None); self.coll.objects.link(e)
        e.empty_display_size = 0.002
        e.matrix_world = Matrix.Translation(Vector(loc) * S) @ (mat3.to_4x4() if mat3 else Matrix.Identity(4))
        if parent is None: self._attach(e, 'head', False)
        else: self._put(e, parent)
        e.rotation_mode = 'XYZ'
        return e

    def _put(self, ob, h):
        bpy.context.view_layer.update(); ob.parent = h; ob.matrix_parent_inverse = h.matrix_world.inverted(); return ob

    def _face(self):
        M, co = self.M, self.coll
        self.eyeballs, self.lids_up, self.lids_lo, self.mouths, self.brows = [], [], [], {}, []
        for side, tag in ((1, 'L'), (-1, 'R')):
            c, F, p = eye_frame(side)
            frame = self._empty(f'eye_frame.{tag}', c, F)
            # eyeball: origin at its centre, looking down local -Y (the shader needs that)
            bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=EYE_R * S)
            me = bpy.data.meshes.new(f'eye.{tag}'); bm.to_mesh(me); bm.free()
            for pg in me.polygons: pg.use_smooth = True
            eye = bpy.data.objects.new(f'{self.name}_eye.{tag}', me); co.objects.link(eye); me.materials.append(M['eye'])
            eye.parent = frame; eye.location = (0, 0, 0); eye.rotation_mode = 'XYZ'; eye['pupil'] = 1.0; eye['part'] = 'skin'
            eye.color = (0, 1, 0, 1)
            self.eyeballs.append(eye)
            for kind, keep in (('up', lambda z: z > -0.06), ('lo', lambda z: z < 0.06)):   # eyelid shells
                bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=EYE_R * 1.04 * S)
                bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep(v.co.z / (EYE_R * 1.04 * S))], context='VERTS')
                bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.0004)
                me = bpy.data.meshes.new(f'lid_{kind}.{tag}'); bm.to_mesh(me); bm.free()
                for pg in me.polygons: pg.use_smooth = True
                lid = bpy.data.objects.new(f'{self.name}_lid_{kind}.{tag}', me); co.objects.link(lid); me.materials.append(M['lid'])
                lid.parent = frame; lid.location = (0, 0, 0); lid.rotation_mode = 'XYZ'; lid['part'] = 'skin'; lid.color = (0, 1, 0, 1)
                (self.lids_up if kind == 'up' else self.lids_lo).append(lid)
            bc = on_face(side * 0.07, 1.137, 0.0005)[0]
            h = self._empty(f'brow.{tag}', bc); h.rotation_mode = 'YXZ'
            self._put(arc(f'brow_arc.{tag}', [on_face(side * x_, 1.136 + 0.004 * (1 - ((x_ - 0.07) / 0.028) ** 2), 0.0006)[0]
                                              for x_ in (0.042, 0.056, 0.07, 0.084, 0.098)], 0.0026, M['brow'], co), h)
            self.brows.append((h, side, bc))
        p, n = on_face(0, 1.03, 0.0005)                                       # a soft button nose, mostly sunk into the face
        self._attach(piece('nose', Shape().ellipsoid(p, (0.0085, 0.008, 0.009), rot=(math.radians(-20), 0, 0), seg=24), M['skin'], 'skin', co,
                           voxel=0.0007, smooth=3, lump=0), 'head', False)
        mc, mn = on_face(0, 0.986, 0.0005); R = mn.to_track_quat('-Y', 'Z').to_matrix()
        def mline(nm, curve):
            return arc(nm, [on_face(x_, 0.986 + curve * (x_ / 0.013) ** 2, 0.0006)[0] for x_ in (-0.013, -0.0065, 0, 0.0065, 0.013)],
                       0.0018, M['lip_line'], co)
        h = self._empty('mouth_line', mc)                                         # small sculpted closed lips
        self._put(arc('lip_parting', [on_face(x_, 0.986 - 0.0012 * (x_ / 0.014) ** 2, 0.0008)[0] for x_ in (-0.014, -0.007, 0, 0.007, 0.014)],
                      0.0011, M['lip_line'], co), h)
        self._put(arc('lip_upper', [on_face(x_, 0.9885 + 0.0007 * (1 - (x_ / 0.012) ** 2), 0.0012)[0] for x_ in (-0.012, -0.006, 0, 0.006, 0.012)],
                      0.0019, M['lips'], co), h)
        lp, ln = on_face(0, 0.9815, 0.0008)
        self._put(piece('lip_lower', Shape().ellipsoid(lp, (0.0085, 0.0032, 0.0034), rot=ln.to_track_quat('-Y', 'Z').to_matrix(), seg=24),
                        M['lips'], 'skin', co, voxel=0.0006, smooth=3, lump=0), h)
        self.mouths['line'] = h
        for v, ob in (('smile', mline('mouth_smile', 0.004)), ('frown', mline('mouth_frown', -0.0035))):
            h = self._empty(f'mouth_{v}', mc); self._put(ob, h); self.mouths[v] = h
        for v, r, dz in (('o', (0.006, 0.0035, 0.0078), 0.0), ('scream', (0.017, 0.004, 0.022), -0.01)):
            h = self._empty(f'mouth_{v}', mc)
            self._put(piece(f'mouth_{v}_in', Shape().ellipsoid(mc + Vector((0, 0, dz)) - mn * 0.001, r, rot=R), M['mouth_in'], 'skin', co,
                            voxel=0.0007, smooth=3, lump=0), h)
            self.mouths[v] = h

    def expr(self, name, blink=False, gaze=None):
        up, lo, pupil, tilt, lift, mouth, gz = EXPR[name]
        if blink: up = 90
        gz = gaze or gz
        for eye in self.eyeballs:
            eye.rotation_euler = (math.radians(gz[1]), 0, math.radians(gz[0])); eye['pupil'] = pupil
        for lid in self.lids_up: lid.rotation_euler = (math.radians(up), 0, 0)
        for lid in self.lids_lo: lid.rotation_euler = (math.radians(lo), 0, 0)    # + tips the shell back: rim drops below
        for v, h in self.mouths.items(): h.scale = (1, 1, 1) if v == mouth else (1e-4,) * 3
        for h, side, bc in self.brows:
            h.rotation_euler = (0, math.radians(side * tilt), 0); h.delta_location = (0, 0, lift * S)

    def key(self, f):
        import claylib as C
        C.key(self.root, f, loc=tuple(self.root.location), rot=tuple(self.root.rotation_euler))
        for pn, e in self.P.items():
            if pn != 'root': C.key(e, f, rot=tuple(e.rotation_euler))
        for ob in self.eyeballs:
            C.key(ob, f, rot=tuple(ob.rotation_euler)); ob.keyframe_insert('["pupil"]', frame=f)
        for ob in self.lids_up + self.lids_lo: C.key(ob, f, rot=tuple(ob.rotation_euler))
        for h in self.mouths.values(): C.key(h, f, scale=tuple(h.scale))
        for h, _, _ in self.brows:
            C.key(h, f, rot=tuple(h.rotation_euler)); h.keyframe_insert('delta_location', frame=f)
