"""The Sector B13 cast: Haru's friends Mika and Jun, the B13 handlers, and the B13 creature.

Mika, Jun and the handlers are Haru's own clay puppet (same rig, same face kit, same mocap and contact solver) with
their own colours and hair, so every motion clip and expression works on them unchanged:
    import cast_camp as CC
    mika = CC.Friend(CC.MIKA, name='mika', loc=(x, y, 0), yaw=0)
    jun  = CC.Friend(CC.JUN,  name='jun',  ...)
    hd   = CC.Handler(name='handler_a', loc=...)          # grey coverall, hood, black visor; 1.75 m (Haru x1.4)
The creature is its own puppet (3.4 m, thin, long arms, long fingers), posed by angles:
    c = CC.Creature(loc=(x, y, 0), yaw=0); c.walk(t, speed); c.reach(side, u); c.look(yaw, pitch); c.key(f)
    f = CC.fingers('zip_fingers')                         # its hand alone, for the close shot through the tent door
"""
import bpy, math, os, sys
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import haru_puppet as HP
import haru_clay as HC
from haru_puppet import Shape, CV
import claylib as C

R = math.radians


# ------------------------------------------------------------------ hair (1.26 m units, like haru_clay.hair_shape)
def mika_hair():
    """a chin-length bob with a straight fringe and two buns on top: her silhouette reads apart from Haru's"""
    s = Shape()
    s.ellipsoid((0, 0.035, 1.09), (0.152, 0.132, 0.162)); s.ellipsoid((0, 0.03, 1.15), (0.145, 0.125, 0.1))
    for sd in (1, -1):
        s.ellipsoid((sd * 0.14, 0.03, 1.0), (0.04, 0.1, 0.105))          # bob sides down to the jaw
        s.ball((sd * 0.105, 0.04, 1.235), 0.058)                          # buns
    s.ellipsoid((0, 0.07, 1.0), (0.155, 0.07, 0.115))                     # back, chin length
    s.ellipsoid((0, -0.082, 1.165), (0.13, 0.03, 0.045), rot=(R(-22), 0, 0))   # blunt fringe
    return s


def jun_hair():
    """short and messy, pushed up in a few soft spikes; the ears show"""
    s = Shape()
    s.ellipsoid((0, 0.035, 1.1), (0.146, 0.13, 0.142)); s.ellipsoid((0, 0.03, 1.17), (0.14, 0.12, 0.085))
    import random
    r = random.Random(4)
    for i in range(16):                                                 # small soft tufts all over the crown
        th = r.uniform(0, 2 * math.pi); ph = r.uniform(0.15, 0.95)
        base = Vector((0.12 * math.sin(ph) * math.cos(th), 0.03 + 0.11 * math.sin(ph) * math.sin(th), 1.1 + 0.13 * math.cos(ph)))
        out = (base - Vector((0, 0.03, 1.08))).normalized()
        s.capsule(base, base + out * r.uniform(0.022, 0.034) + Vector((0, 0, 0.008)), 0.024, 0.009, 10)
    s.ellipsoid((0.01, -0.088, 1.16), (0.11, 0.024, 0.032), rot=(R(-40), 0, R(6)))   # short fringe flicked to one side
    return s


def handler_hood():
    """a coverall hood drawn tight round a mask: the whole head hidden"""
    s = Shape()
    s.ellipsoid((0, 0.005, 1.065), (0.158, 0.145, 0.168))
    s.ellipsoid((0, 0.04, 0.95), (0.15, 0.12, 0.09))                      # the hood's neck, into the collar
    return s


MIKA = dict(pal={'hoodie': '#3d8c86', 'pants': '#3a3d4a', 'hair': '#3a2318', 'skin': '#efb08a', 'shoe': '#e9d9c8'}, hair=mika_hair)
JUN = dict(pal={'hoodie': '#5a6d3a', 'pants': '#9a8a6c', 'hair': '#121214', 'skin': '#c88a60', 'shoe': '#3a3b40', 'sole': '#e4e2de'}, hair=jun_hair)
HANDLER = dict(pal={'hoodie': '#5c605a', 'pants': '#5c605a', 'hair': '#535750', 'skin': '#232325', 'shoe': '#1c1c1e', 'sole': '#0e0e0f'},
               hair=handler_hood)


class Friend(HC.HaruClay):
    """Haru's puppet with another palette and hairstyle (look = MIKA / JUN / HANDLER)"""
    def __init__(self, look, **kw):
        self.look = look
        HC.HaruClay.__init__(self, **kw)

    def _materials(self):
        pal = dict(HC.PAL, **self.look['pal'])
        M = {k: CV.clay(f'{self.name}_{k}', pal[k], **kw) for k, kw in HC.LOOK.items()}
        M['eye'] = CV.clay(f'{self.name}_eye', (0.012, 0.01, 0.01), gloss=True)
        return M

    def _build(self):
        old = HC.hair_shape; HC.hair_shape = self.look['hair']
        try: HC.HaruClay._build(self)
        finally: HC.hair_shape = old


class Handler(Friend):
    """a Sector B13 handler: grey coverall, hood, a black visor where the face should be, black gloves and boots.
    Haru's rig scaled x1.4 (an adult, 1.75 m)"""
    SCALE = 1.4

    def __init__(self, **kw):
        Friend.__init__(self, HANDLER, **kw)
        self.root.scale = (self.SCALE,) * 3

    def _face(self):
        HC.HaruClay._face(self)
        v = HP.piece('visor', Shape().ellipsoid((0, -0.118, 1.05), (0.105, 0.04, 0.075)), self.M['eye'], 'skin', self.coll,
                     voxel=0.0015, smooth=3, lump=0)
        self._attach(v, 'head', False)
        s = Shape()
        for sd in (1, -1): s.ellipsoid((sd * 0.06, -0.12, 0.985), (0.03, 0.03, 0.025))   # filter cans under the visor
        self._attach(HP.piece('filters', s, self.M['skin'], 'skin', self.coll, voxel=0.0015, smooth=3, lump=0), 'head', False)


# ------------------------------------------------------------------ the creature
def _piece(name, s, mat, coll, voxel=0.0008, smooth=3, lump=0.0):
    ob = HP.piece(name, s, mat, 'skin', coll, voxel=voxel, smooth=smooth, lump=0)
    ob.data.transform(Matrix.Scale(1 / HP.S, 4))
    if lump: CV.geometry(ob, dents=lump * 4, pits=lump * 0.7, lumps=lump * 0.7)
    return ob


def creature_materials():
    return {'skin': CV.clay('b13_skin', '#6f6a62', rough=0.5, sss=0.25, bump=0.7, prints=0.6),
            'dark': CV.clay('b13_dark', '#1a1716', rough=0.6, bump=0.2, prints=0),
            'nail': CV.clay('b13_nail', '#3b3330', rough=0.35, bump=0.2, prints=0),
            'collar': CV.clay('b13_collar', '#3a3c3e', rough=0.35, bump=0.3, prints=0)}


def finger_shape(s, base, out, n=4, length=0.032, spread=0.006, r=0.0019, curl=0.25):
    """long jointed fingers fanned from `base` along `out` (metres): three bones each, the joints swollen"""
    out = Vector(out).normalized(); side = out.cross(Vector((0, 0, 1)))
    if side.length < 1e-4: side = Vector((1, 0, 0))
    side.normalize(); down = side.cross(out)
    tips = []
    for i in range(n):
        o = (i - (n - 1) / 2) * spread; L = length * (1 - 0.1 * abs(i - (n - 1) / 2))
        p = Vector(base) + side * o; d = out.copy()
        for k in range(3):
            q = p + d * L / 3; s.capsule(p, q, r * (1 - 0.15 * k), r * (0.85 - 0.15 * k), 12); s.ball(q, r * (1 - 0.12 * k) * 1.05, 10)
            d = (d + down * curl).normalized(); p = q
        tips.append(p)
    return tips


def fingers(name='b13_fingers', coll=None, mats=None):
    """the creature's hand alone, for the shot through the tent door: four long grey fingers and a thumb, dark nails.
    Its holder's -y is where the fingers point."""
    coll = coll or bpy.data.collections['Set']; M = mats or creature_materials()
    s = Shape().ellipsoid((0, 0.012, 0), (0.011, 0.016, 0.004))
    tips = finger_shape(s, (0, 0.0, 0), (0, -1, 0), n=4, length=0.04, spread=0.0055, r=0.0018, curl=0.18)
    tips += finger_shape(s, (0.011, 0.008, -0.001), (0.6, -1, 0), n=1, length=0.022, r=0.0019, curl=0.1)
    hand = _piece(name, s, M['skin'], coll, voxel=0.0005, smooth=2, lump=0.00008)
    nails = Shape()
    for t in tips: nails.ellipsoid(t + Vector((0, 0, 0.0008)), (0.0013, 0.002, 0.0006))
    nl = _piece(name + '_nails', nails, M['nail'], coll, voxel=0.0003, smooth=1)
    h = C.empty(name, (0, 0, 0))
    for c in list(h.users_collection): c.objects.unlink(h)
    coll.objects.link(h)
    for o in (hand, nl): o.parent = h
    return h


class Creature:
    """The B13 creature: 3.4 m (34 cm), starved thin, a slight forward hunch, arms to below its knees, a long smooth head
    with two small black eye pits and a thin mouth. A metal collar for the handlers' pole. Pivots are empties
    (rotation YXZ) driven by walk / reach / look; everything is keyed with key(f)."""
    H = 0.34

    def __init__(self, loc=(0, 0, 0), yaw=0.0, name='b13', coll=None):
        self.name = name
        self.coll = coll or bpy.data.collections.new(name)
        if self.coll.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(self.coll)
        self.M = creature_materials(); self.P = {}; self.rest = {}
        P = [('root', None, (0, 0, 0)), ('hips', 'root', (0, 0, 0.17)), ('chest', 'hips', (0, -0.008, 0.265)),
             ('neck', 'chest', (0, -0.016, 0.295)), ('head', 'neck', (0, -0.02, 0.31))]
        for sd, t in ((1, 'L'), (-1, 'R')):
            P += [(f'arm.{t}', 'chest', (sd * 0.022, -0.01, 0.283)), (f'fore.{t}', f'arm.{t}', (sd * 0.03, -0.012, 0.2)),
                  (f'hand.{t}', f'fore.{t}', (sd * 0.032, -0.016, 0.115)),
                  (f'thigh.{t}', 'hips', (sd * 0.012, 0, 0.17)), (f'shin.{t}', f'thigh.{t}', (sd * 0.013, -0.004, 0.088)),
                  (f'foot.{t}', f'shin.{t}', (sd * 0.013, 0.0, 0.008))]
        for pn, par, pos in P: self._pivot(pn, par, pos)
        self._build()
        self.root = self.P['root']; self.root.location = loc; self.root.rotation_euler = (0, 0, yaw); self.yaw = yaw

    def _pivot(self, pn, par, pos):
        e = bpy.data.objects.new(f'{self.name}_{pn}', None); self.coll.objects.link(e)
        e.empty_display_size = 0.006; e.rotation_mode = 'YXZ'; self.rest[pn] = Vector(pos)
        if par: e.parent = self.P[par]; e.location = Vector(pos) - self.rest[par]
        else: e.location = Vector(pos)
        self.P[pn] = e

    def _attach(self, ob, pv):
        bpy.context.view_layer.update()
        ob.parent = self.P[pv]; ob.matrix_parent_inverse = self.P[pv].matrix_world.inverted(); return ob

    def _build(self):
        M, co, rs = self.M, self.coll, self.rest
        s = Shape()                                                         # a narrow chest over a pinched waist
        s.ellipsoid((0, -0.007, 0.257), (0.021, 0.014, 0.03)); s.capsule((0, -0.002, 0.19), (0, -0.006, 0.235), 0.0095, 0.015, 16)
        for k in range(4):                                                  # ribs pressing through the skin, each side
            for sd in (1, -1):
                s.ellipsoid((sd * 0.0128, -0.0125, 0.262 - k * 0.0095), (0.006, 0.0032, 0.0014), rot=(0, sd * R(-25), sd * R(-30)))
        for k in range(7): s.ball((0, 0.006, 0.2 + k * 0.012), 0.0032)       # spine knobs down the back
        for sd in (1, -1): s.ball((sd * 0.021, -0.009, 0.283), 0.0068)      # bony shoulders
        self._attach(_piece(f'{self.name}_torso', s, M['skin'], co, voxel=0.0005, lump=0.00012), 'chest')
        s = Shape().ellipsoid((0, -0.001, 0.174), (0.016, 0.011, 0.013))
        for sd in (1, -1): s.ball((sd * 0.011, 0, 0.17), 0.004)             # hip bones
        self._attach(_piece(f'{self.name}_pelvis', s, M['skin'], co, voxel=0.0005, lump=0.0001), 'hips')
        self._attach(_piece(f'{self.name}_neck', Shape().capsule((0, -0.012, 0.28), (0, -0.02, 0.315), 0.0042, 0.0038, 12),
                            M['skin'], co, voxel=0.0005), 'neck')
        s = Shape().ellipsoid((0, -0.024, 0.33), (0.0115, 0.0125, 0.021), rot=(R(-12), 0, 0))   # a long smooth head, tipped forward
        s.ellipsoid((0, -0.033, 0.318), (0.008, 0.006, 0.009))              # a long jaw
        self._attach(_piece(f'{self.name}_head', s, M['skin'], co, voxel=0.0005, lump=0.00008), 'head')
        s = Shape()
        for sd in (1, -1): s.ellipsoid((sd * 0.0048, -0.0352, 0.333), (0.0029, 0.0022, 0.0038), rot=(0, sd * R(-15), 0))   # small black eye pits
        s.ellipsoid((0, -0.0385, 0.313), (0.0062, 0.0014, 0.0007))           # a thin mouth
        self._attach(_piece(f'{self.name}_face', s, M['dark'], co, voxel=0.0003, smooth=1), 'head')
        ring = Shape().ring((0, -0.014, 0.296), 0.0062, 0.0062, 0.0014, 20)
        self._attach(_piece(f'{self.name}_collar', ring, M['collar'], co, voxel=0.0004, smooth=1), 'neck')
        for sd, t in ((1, 'L'), (-1, 'R')):
            a, b, c = rs[f'arm.{t}'], rs[f'fore.{t}'], rs[f'hand.{t}']
            self._attach(_piece(f'{self.name}_arm.{t}', Shape().capsule(a, b, 0.0052, 0.0036, 12).ball(b, 0.0045), M['skin'], co,
                                voxel=0.0005, lump=0.00008), f'arm.{t}')
            self._attach(_piece(f'{self.name}_fore.{t}', Shape().capsule(b, c, 0.0042, 0.0026, 12), M['skin'], co, voxel=0.0005,
                                lump=0.00008), f'fore.{t}')
            s = Shape().ellipsoid(c + Vector((0, 0, -0.006)), (0.004, 0.0028, 0.007))
            tips = finger_shape(s, c + Vector((0, 0, -0.011)), (0, -0.25, -1), n=4, length=0.03, spread=0.0028, r=0.0011, curl=0.2)
            self._attach(_piece(f'{self.name}_hand.{t}', s, M['skin'], co, voxel=0.0004, lump=0.00005), f'hand.{t}')
            h, k, f = rs[f'thigh.{t}'], rs[f'shin.{t}'], rs[f'foot.{t}']
            self._attach(_piece(f'{self.name}_thigh.{t}', Shape().capsule(h, k, 0.0068, 0.0042, 12).ball(k, 0.0052), M['skin'], co,
                                voxel=0.0005, lump=0.0001), f'thigh.{t}')
            self._attach(_piece(f'{self.name}_shin.{t}', Shape().capsule(k, f + Vector((0, 0, 0.004)), 0.0048, 0.0028, 12), M['skin'], co,
                                voxel=0.0005, lump=0.0001), f'shin.{t}')
            s = Shape().ellipsoid(f + Vector((0, -0.01, -0.003)), (0.0045, 0.016, 0.0028))   # long narrow feet
            self._attach(_piece(f'{self.name}_foot.{t}', s, M['skin'], co, voxel=0.0005, lump=0.00008), f'foot.{t}')

    # ---- posing (angles in degrees; everything resets each call)
    def rest_pose(self):
        for e in self.P.values():
            if e is not self.root: e.rotation_euler = (0, 0, 0)

    def walk(self, t, speed=0.6, hunch=10.0):
        """a slow, stilted walk: long steps, knees lifting high, arms hanging and swinging late. speed in steps/s"""
        ph = 2 * math.pi * speed * t / 2
        self.P['chest'].rotation_euler = (R(hunch + 2 * math.sin(2 * ph)), 0, R(4 * math.sin(ph)))
        self.P['hips'].rotation_euler = (0, R(3 * math.sin(ph)), R(-5 * math.sin(ph)))
        for sd, t_, o in ((1, 'L', 0.0), (-1, 'R', math.pi)):
            s = math.sin(ph + o); lift = max(0.0, math.sin(ph + o + math.pi / 2))
            self.P[f'thigh.{t_}'].rotation_euler = (R(-24 * s - 14 * lift), 0, 0)
            self.P[f'shin.{t_}'].rotation_euler = (R(40 * lift), 0, 0)
            self.P[f'foot.{t_}'].rotation_euler = (R(-12 * lift + 6 * s), 0, 0)
            self.P[f'arm.{t_}'].rotation_euler = (R(14 * math.sin(ph + o + math.pi - 0.5)), 0, R(sd * 4))
            self.P[f'fore.{t_}'].rotation_euler = (R(-10 - 8 * max(0.0, math.sin(ph + o))), 0, 0)
        return abs(math.sin(ph)) * 0.004                                    # hip bob (metres) for the caller

    def reach(self, side, u, up=0.0):
        """lift one arm forward to reach (u 0..1); up tilts the reach higher"""
        t_ = 'L' if side > 0 else 'R'
        self.P[f'arm.{t_}'].rotation_euler = (R(-(70 + up) * u), 0, R(side * 6 * u))
        self.P[f'fore.{t_}'].rotation_euler = (R(-15 * u), 0, 0)

    def look(self, yaw=0.0, pitch=0.0, tilt=0.0):
        self.P['neck'].rotation_euler = (R(pitch * 0.4), R(tilt * 0.5), R(yaw * 0.4))
        self.P['head'].rotation_euler = (R(pitch * 0.6), R(tilt * 0.5), R(yaw * 0.6))

    def key(self, f):
        for e in self.P.values():
            e.keyframe_insert('rotation_euler', frame=f)
        self.root.keyframe_insert('location', frame=f)
