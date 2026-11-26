"""Haru #5 "The Gathering" (wordless, 9:16, about 20 s with the black tail added in post). Set in the village.

Night. Every front door on the street stands open onto a lit, empty hall. Haru alone on the north sidewalk. Far-off
chanting. She turns her head to it, walks to the end of the street, creeps up the narrow gap beside the last house
and peeks round its back corner: in the back gardens the whole village stands in a ring with candles, swaying,
chanting round a sunflower taller than the houses, its head bowed. The chant stops. The head lifts: a face in the
seeds, a grin. Every villager's head turns round to look at her. Black.

Shot plan (cinematic-director, horror x vertical): 1 locked wide (hook: open doors, nobody) · 2 close, she hears it ·
3 follow from behind · 4 low in the gap, she creeps at us, warm glow on her face · 5 over her shoulder, the reveal,
slow push · 6 low under the flower, slow push, the face · 7 over her shoulder again, wider: every face turns to her.

    blender -b -P scenes/the_gathering.py -- [--stills a,b] [--range A B] [--res 1080 1920] [--samples 64] [--out DIR]
"""
import bpy, os, sys, math, random, time
T00 = time.time()
def tick(m): print(f'TIME {m} {time.time() - T00:.0f}s', flush=True)
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
SETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, os.path.join(SETS, 'village')); sys.path.insert(0, SETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import kit as K
import village, village_plan as VP
import haru_clay as HC, haru_puppet as HP, mocap as MC, walker as WK
from claylib import cli, run, key, look_at, camera, constant_interp, Boil, emissive

OPTS = cli('the_gathering')
FPS = 12
END = 19.6
F = int(END * FPS)
sc = K.begin('the_gathering', res=OPTS['res'], samples=OPTS['samples'], frames=1)
sc.frame_start, sc.frame_end = 1, F
village.OPEN_DOORS = True
village.build()
tick('village')
M = K.M


def ezs(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
def yaw_of(d): return math.atan2(d.x, -d.y)
def wrap(a): return (a + math.pi) % (2 * math.pi) - math.pi


# ------------------------------------------------------------------ the place: the last house on the north side, the gap beside it
I8 = [r[0] for r in VP.HOUSES].index('north_8')
N8 = VP.HOUSES[I8]; BACK = VP.FRONT_N + N8[4]                         # its back wall
X_GAP = N8[2] + 0.06                                                  # she walks up the gap 6 cm from its east wall
hb = K.block('side_hedge', X_GAP + 0.055, X_GAP + 0.09, VP.FRONT_N + 0.03, BACK - 0.05, 0.0, 0.11, M['hedge'], bevel=0.01)
K.add_lumps(hb, 0.005, size=0.02)                                     # the neighbour's hedge: the gap is a narrow passage
C = Vector((3.70, BACK + 0.31, 0.0))                                  # the ring, in the back gardens
K.block('trodden', C.x - 0.26, C.x + 0.26, C.y - 0.22, C.y + 0.22, -0.001, 0.0006, M['dirt'], bevel=0)   # trampled to earth
bpy.data.objects['haze'].location.y = 0.7; bpy.data.objects['haze'].scale.y = 5.6

# ------------------------------------------------------------------ the sunflower
STEM = K.painted('sf_stem', (0.05, 0.08, 0.03), rough=0.8)
SEEDS = K.painted('sf_seeds', (0.11, 0.065, 0.03), rough=0.9)
PETAL = K.painted('sf_petal', (0.42, 0.29, 0.05), rough=0.75)
VOID = K.painted('sf_void', (0.0, 0.0, 0.0), rough=1.0)
TOOTH = K.painted('sf_tooth', (0.5, 0.45, 0.33), rough=0.6)
GLINT = emissive('sf_glint', (1.0, 0.82, 0.55), 3.0)
coll = bpy.data.collections['Set']


def piece(name, s, mat, voxel=0.0012, smooth=3):
    ob = HP.piece(name, s, mat, 'top', coll, voxel=voxel, smooth=smooth, lump=0)
    ob.data.transform(Matrix.Scale(1 / HP.S, 4)); return ob


H_TOP = 0.86
sf = K.empty('sunflower', tuple(C)); K._to(sf)
s = HP.Shape()
pts = [Vector((0, 0, 0)), Vector((0.008, 0.004, 0.3)), Vector((-0.006, 0, 0.6)), Vector((0, 0, H_TOP))]
for a, b, r0, r1 in zip(pts, pts[1:], (0.016, 0.014, 0.012), (0.014, 0.012, 0.011)): s.capsule(a, b, r0, r1, 16)
stem = piece('sf_stem', s, STEM, voxel=0.002); K.attach(stem, sf)
rl = random.Random(3)
for i, z in enumerate((0.18, 0.3, 0.42, 0.54, 0.66)):                 # big drooping leaves up the stem
    a = i * 2.4 + rl.uniform(-0.3, 0.3); d = Vector((math.cos(a), math.sin(a), 0))
    s = HP.Shape().ellipsoid(d * 0.07 + Vector((0, 0, z - 0.02)), (0.065, 0.032, 0.006), rot=(0.5, -0.35, a))
    lf = piece(f'sf_leaf_{i}', s, STEM, voxel=0.0015); K.attach(lf, sf)
sf_head = K.empty('sf_head_pivot', (0, 0, 0)); K._to(sf_head); K.attach(sf_head, sf); sf_head.location = (0, 0, H_TOP)
sf_face = K.empty('sf_face', (0, 0, 0)); K._to(sf_face); K.attach(sf_face, sf_head); sf_face.location = (0, -0.075, 0)   # the head sits in front of the stem
# head (pivot local, the face looks down -y)
s = HP.Shape().ellipsoid((0, 0.03, 0), (0.12, 0.03, 0.12)).capsule((0, 0.03, 0), (0, 0.078, -0.012), 0.02, 0.014)
K.attach(piece('sf_back', s, STEM, voxel=0.002), sf_face)
s = HP.Shape().ellipsoid((0, -0.004, 0), (0.112, 0.026, 0.112))
disc = piece('sf_disc', s, SEEDS, voxel=0.0015); K.add_lumps(disc, 0.002, size=0.006); K.attach(disc, sf_face)
s = HP.Shape()
for layer, (n, rr, yy, droop) in enumerate(((24, 0.148, 0.006, 0.15), (24, 0.142, 0.016, 0.3))):
    for i in range(n):
        a = 2 * math.pi * (i + 0.5 * layer) / n + rl.uniform(-0.04, 0.04)
        c = Vector((math.cos(a) * rr, yy, math.sin(a) * rr))
        s.ellipsoid(c, (0.045 * rl.uniform(0.85, 1.1), 0.005, 0.015), rot=(droop * math.sin(a), -a, 0))
K.attach(piece('sf_petals', s, PETAL, voxel=0.0015), sf_face)
s = HP.Shape()                                                       # the face: slanted hollow eyes, a frowning brow
for sx in (-1, 1):
    s.ellipsoid((sx * 0.042, -0.027, 0.028), (0.024, 0.008, 0.011), rot=(0, sx * 0.45, 0))
K.attach(piece('sf_eyes', s, VOID, voxel=0.001), sf_face)
s = HP.Shape()
for sx in (-1, 1): s.capsule((sx * 0.012, -0.03, 0.045), (sx * 0.074, -0.026, 0.072), 0.006, 0.005, 12)
brow = piece('sf_brow', s, SEEDS, voxel=0.001); K.add_lumps(brow, 0.0015, size=0.004); K.attach(brow, sf_face)
PUPILS = []
for sx in (-1, 1):
    g = K.sphere('sf_pupil', 0.0032, (0, 0, 0), mat=GLINT); K._to(g); K.attach(g, sf_face); g.location = (sx * 0.036, -0.034, 0.026); PUPILS.append(g)


def grin(name, top, bot, rows, teeth):
    """a crescent mouth: black between a top and a bottom curve, pale seed-teeth along both edges"""
    s = HP.Shape()
    for k in range(rows + 1):
        for i in range(17):
            x = -0.075 + i * 0.15 / 16; u = k / rows
            z = top(x) * (1 - u) + bot(x) * u
            s.ball((x, -0.028, z), 0.006, 12)
    mouth = piece(name, s, VOID, voxel=0.001)
    t = HP.Shape()
    if teeth:
        for i in range(11):
            x = -0.06 + i * 0.012
            t.ellipsoid((x, -0.033, top(x) - 0.004), (0.004, 0.003, 0.007))
            t.ellipsoid((x + 0.006, -0.033, bot(x) + 0.004), (0.004, 0.003, 0.007))
        tt = piece(name + '_teeth', t, TOOTH, voxel=0.0008); K.attach(tt, sf_face)
    else: tt = None
    K.attach(mouth, sf_face); return mouth, tt


mouth_thin = grin('sf_mouth_thin', lambda x: -0.05 + 0.032 * (x / 0.075) ** 2, lambda x: -0.052 + 0.032 * (x / 0.075) ** 2, 1, False)[0]
mouth_wide = grin('sf_mouth_wide', lambda x: -0.035 + 0.025 * (x / 0.075) ** 2, lambda x: -0.085 + 0.055 * (x / 0.075) ** 2, 6, True)

tick('sunflower')
# ------------------------------------------------------------------ the villagers: ordinary people in coats, candles held in front
SKIN = K.painted('vl_skin', (0.46, 0.34, 0.27), rough=0.7)
HAIRS = [K.painted('vl_hair_dark', (0.025, 0.018, 0.014), rough=0.85), K.painted('vl_hair_grey', (0.28, 0.27, 0.26), rough=0.85),
         K.painted('vl_hair_brown', (0.09, 0.05, 0.03), rough=0.85)]
COATS = [K.painted(f'vl_coat_{i}', c, rough=0.9) for i, c in enumerate(((0.05, 0.05, 0.06), (0.15, 0.11, 0.08), (0.07, 0.09, 0.06),
                                                                         (0.18, 0.05, 0.04), (0.1, 0.1, 0.11), (0.12, 0.1, 0.06)))]
WAX = K.painted('vl_wax', (0.6, 0.56, 0.45), rough=0.5)
FLAME = emissive('vl_flame', (1.0, 0.62, 0.25), 18.0)


def body_shape(v):
    s = HP.Shape(); hunch = 0.007 if v == 2 else 0.0; top = 0.135 - (0.008 if v == 2 else 0.0)
    for sx in (-1, 1):
        s.capsule((sx * 0.008, 0, 0.004), (sx * 0.008, 0, 0.07), 0.005, 0.006, 12)
        s.ellipsoid((sx * 0.008, -0.004, 0.004), (0.005, 0.009, 0.004))
    if v == 1: s.capsule((0, 0, 0.03), (0, 0, top), 0.025, 0.018, 16)    # a long coat flaring at the hem
    else: s.capsule((0, 0, 0.06), (0, -hunch, top), 0.019, 0.021, 16)
    s.ellipsoid((0, -hunch, top), (0.024, 0.016, 0.012))
    s.capsule((0, -hunch, top), (0, -hunch * 1.4, top + 0.012), 0.005, 0.005, 12)
    for sx in (-1, 1):
        sh = Vector((sx * 0.022, -hunch, top - 0.003)); el = Vector((sx * 0.02, -0.012 - hunch, top - 0.035))
        hd = Vector((sx * 0.005, -0.031 - hunch, top - 0.03))
        s.capsule(sh, el, 0.0055, 0.005, 12).capsule(el, hd, 0.005, 0.0042, 12)
    return s, Vector((0, -hunch * 1.4, top + 0.012))


def head_shapes(v):
    sk = HP.Shape().ellipsoid((0, 0, 0.012), (0.0105, 0.0115, 0.0125)).ellipsoid((0, -0.0105, 0.009), (0.0022, 0.003, 0.0035))
    hr = HP.Shape()
    if v == 0: hr.ellipsoid((0, 0.002, 0.016), (0.0116, 0.0122, 0.0105))
    elif v == 1: hr.ellipsoid((0, 0.002, 0.016), (0.0118, 0.0124, 0.011)).ball((0, 0.011, 0.02), 0.006)
    else: hr.ellipsoid((0, 0.0, 0.022), (0.013, 0.014, 0.005)).ellipsoid((0, -0.008, 0.0205), (0.012, 0.01, 0.002))
    return sk, hr


PROTO = []
for v in range(3):
    s, neck = body_shape(v); b = piece(f'vl_body_{v}', s, COATS[0], voxel=0.0008)
    sk, hr = head_shapes(v); hs = piece(f'vl_head_{v}', sk, SKIN, voxel=0.0007); hh = piece(f'vl_hair_{v}', hr, HAIRS[v], voxel=0.0007)
    ey = HP.Shape()
    for sx in (-1, 1): ey.ellipsoid((sx * 0.0042, -0.0098, 0.0135), (0.0017, 0.0012, 0.0019))
    he = piece(f'vl_eyes_{v}', ey, VOID, voxel=0.0004, smooth=1)
    for o in (b, hs, hh, he): o.hide_render = True; o.hide_viewport = True
    PROTO.append((b, hs, hh, neck, he))

HARU_AT = Vector((X_GAP - 0.022, BACK + 0.012, 0.0))                   # where she ends up, peeking round the corner
dirH = (HARU_AT - C); dirH.z = 0; dirH.normalize()
a_h = math.atan2(dirH.y, dirH.x)
VILL = []
for k in range(9):
    a = a_h + math.radians(20 + k * 40)
    p = C + Vector((math.cos(a), math.sin(a), 0)) * 0.19
    yaw = yaw_of(C - p)
    v = (k * 2) % 3
    b0, hs0, hh0, neck, he0 = PROTO[v]
    holder = K.empty(f'villager_{k}', tuple(p)); K._to(holder); holder.rotation_euler = (0, 0, yaw)
    b = b0.copy(); coll.objects.link(b); b.hide_render = b.hide_viewport = False; K.attach(b, holder)
    b.material_slots[0].link = 'OBJECT'; b.material_slots[0].material = COATS[k % len(COATS)]
    piv = K.empty(f'villager_{k}_neck', (0, 0, 0)); K._to(piv); K.attach(piv, holder); piv.location = neck
    for o0 in (hs0, hh0, he0):
        o = o0.copy(); coll.objects.link(o); o.hide_render = o.hide_viewport = False
        o.data = o0.data; K.attach(o, piv)
        if o0 is hh0: o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = HAIRS[(k + 1) % 3]
    cz = neck.z - 0.04                                                 # the candle in both hands
    cdl = K.cylinder('candle', 0.0028, 0.02, (0, 0, 0), mat=WAX); K._to(cdl); K.attach(cdl, holder); cdl.location = (0, -0.033 + neck.y, cz + 0.008)
    fl = K.sphere('candle_flame', 0.0022, (0, 0, 0), scale=(1, 1, 1.8), mat=FLAME); K._to(fl); K.attach(fl, holder); fl.location = (0, -0.033 + neck.y, cz + 0.022)
    lt = K.point_light('candle_light', (0, 0, 0), 0.12, radius=0.002, color=(1.0, 0.6, 0.3)); K._to(lt, 'Lights')
    K.attach(lt, holder); lt.location = (0, -0.036 + neck.y, cz + 0.026)
    VILL.append(dict(h=holder, piv=piv, yaw=yaw, ph=k * 0.7, lt=lt))
ring_glow = K.point_light('ring_glow', tuple(C + Vector((0, 0, 0.12))), 4.0, radius=0.09, color=(1.0, 0.58, 0.28)); K._to(ring_glow, 'Lights')
face_up = K.point_light('flower_face_light', tuple(C + dirH * 0.24 + Vector((0, 0, 0.45))), 1.2, radius=0.05, color=(1.0, 0.6, 0.3)); K._to(face_up, 'Lights')
spill = K.point_light('corner_spill', tuple(HARU_AT + Vector((-0.07, 0.04, 0.07))), 0.45, radius=0.03, color=(1.0, 0.6, 0.3)); K._to(spill, 'Lights')

tick('villagers')
# ------------------------------------------------------------------ Haru
h = HC.HaruClay(name='haru')
LIB = MC.Library(os.path.join(HERE, '..', 'mocap', 'clips.npz'), h)
bpy.context.view_layer.update()
floor = WK.Floor()
P0 = Vector((3.42, VP.SIDEWALK_N[0] + 0.07, 0.0))
T_WALK, T4 = 3.3, 8.0
w1 = WK.Walker(LIB, [(P0, 'walk'), (Vector((X_GAP, P0.y, 0)), 'walk'), (Vector((X_GAP, VP.FRONT_N + 0.2, 0)), 'walk')], t0=T_WALK, pace=1.15)
probe = WK.Walker(LIB, [(Vector((0, 0, 0)), 'sneak'), (Vector((0, 1, 0)), 'sneak')], t0=0)
V_SNEAK = 1.0 / probe.t_end
CREEP_END = HARU_AT.y - 0.04
y_start = CREEP_END - V_SNEAK * 3.4
w2 = WK.Walker(LIB, [(Vector((X_GAP, y_start, 0)), 'sneak'), (Vector((X_GAP, CREEP_END, 0)), 'sneak')], t0=T4)
T_PEEK = w2.t_end
yaw_peek = yaw_of(C - HARU_AT)
print('WALK end', round(w1.t_end, 2), 'creep', round(y_start, 3), '->', round(CREEP_END, 3), 'arrive', round(T_PEEK, 2), 'v_sneak', round(V_SNEAK, 4))


def standing(c, yaw): return MC.rotate(LIB.sample('look_behind', c)[0], yaw)


T_TURN = 18.3                                                          # every head turns round to her


def pose(t):
    if t < T_WALK:                                                      # on the sidewalk, facing the road; then turns east
        yaw = math.radians(90) * ezs((t - 2.95) / 0.35)
        return P0, yaw, standing(0.1 + 0.03 * math.sin(t), yaw)
    if t < T4:
        W, xy, z, yaw = w1.at(t); return Vector((xy.x, xy.y, 0)), yaw, W
    if t < T_PEEK:
        W, xy, z, yaw = w2.at(t); return Vector((xy.x, xy.y, 0)), yaw, W
    u = ezs((t - T_PEEK) / 0.8)                                         # leans out round the corner
    yaw = w2.legs[-1]['yaw'] + wrap(yaw_peek - w2.legs[-1]['yaw']) * u
    p = Vector((X_GAP, CREEP_END, 0)).lerp(HARU_AT, u)
    W = MC.blend(w2.at(t)[0], standing(0.12, yaw), ezs((t - T_PEEK) / 0.4))
    if t > T_TURN: W = MC.blend(W, MC.rotate(LIB.sample('terrified', 0.2 + (t - T_TURN) * 0.5)[0], yaw), 0.6 * ezs((t - T_TURN) / 0.3))
    return p, yaw, W


def face(t):
    if t < 2.6: n, gz = 'worried', None
    elif t < 4.2: n, gz = 'suspicious', (20, 0)
    elif t < 11.3: n, gz = 'worried', None
    elif t < 13.0: n, gz = 'stare', None
    elif t < T_TURN + 0.1: n, gz = 'scared', (0, 8)
    else: n, gz = 'terrified', (0, 8)
    blink = any(abs(t - b) < 0.09 for b in (1.2, 5.6, 9.4, 12.6))
    return n, blink, gz


def head_pt(): return h.P['head'].matrix_world @ Vector((0, -0.012, 0.009))


tick('haru')
# ------------------------------------------------------------------ cameras (the shot list)
cam = camera((3.0, 0.2, 0.06), (3.5, 0.6, 0.1), lens=24, fstop=8.0); cam.data.clip_start = 0.003
fill = K.point_light('cam_fill', (0, 0, 0.2), 0.1, radius=0.03, color=(0.6, 0.68, 0.95)); K._to(fill, 'Lights')
SH = [2.0, 4.2, 8.0, 11.3, 15.0, 18.0]
def shot_no(t): return 1 + sum(t >= x for x in SH)


HEAD_W = C + Vector((0, 0, H_TOP))


def shot(t, p, hp):
    n = shot_no(t)
    if n == 1: return Vector((3.95, 0.47, 0.062)), Vector((3.1, 0.64, 0.1)), 22, P0 + Vector((0, 0, 0.08)), 8.0
    if n == 2: return P0 + Vector((-0.035, -0.16, 0.1)), P0 + Vector((0.0, 0, 0.092)), 40, P0 + Vector((0, 0, 0.1)), 5.6
    if n == 3:
        tg = p + Vector((0.07, 0.0, 0.075)); return p + Vector((-0.24, -0.05, 0.085)), tg, 26, p + Vector((0, 0, 0.07)), 8.0
    if n == 4:
        loc = Vector((X_GAP + 0.005, BACK + 0.09, 0.05)); return loc, hp + Vector((0, 0, -0.01)), 28, hp, 5.6
    if n == 5:
        u = ezs((t - 11.3) / 3.7)
        a = Vector((X_GAP + 0.13, BACK - 0.03, 0.08))                    # on her and the ring, then tilts up to the flower
        tg = (C.lerp(HARU_AT, 0.42) + Vector((0, 0, 0.14))).lerp(C + Vector((0, 0, 0.62)), ezs((t - 12.3) / 2.4))
        return a.lerp(tg, 0.12 * u), tg, 24, C + Vector((0, 0, 0.2)), 11.0
    if n == 6:
        u = ezs((t - 15.0) / 3.0)
        a = C + dirH * 0.45 + Vector((0, 0, 0.3)); tg = HEAD_W + dirH * 0.07 + Vector((0, 0, -0.03))
        return a.lerp(tg, 0.18 * u), tg, 24, HEAD_W, 8.0
    a = Vector((X_GAP + 0.16, BACK - 0.03, 0.07)); tg = C.lerp(HARU_AT, 0.35) + Vector((0, 0, 0.15))
    return a, tg, 26, C + Vector((0, 0, 0.14)), 11.0


# ------------------------------------------------------------------ animate
boil = Boil(5, amp=0.00012, rot=0.003)
chat = random.Random(5); flick = random.Random(9)
yaw_h = yaw_of(HARU_AT - C)
FRAMES = sorted(OPTS['stills']) if OPTS.get('stills') else range(1, F + 1)
for f in FRAMES:
    t = (f - 1) / FPS
    p, yaw, W = pose(t)
    h.root.location = (p.x, p.y, p.z); h.root.rotation_euler = (0, 0, yaw)
    MC.apply(h, W, yaw)
    turn = ezs((t - 2.6) / 0.5) * (1 - ezs((t - 2.95) / 0.35))       # she turns her head to the sound (her left, +x)
    h.P['neck'].rotation_euler.z += 0.5 * turn; h.P['head'].rotation_euler.z += 0.6 * turn
    if t >= T_PEEK:                                                     # leaning out, chin down a little
        lean = ezs((t - T_PEEK) / 0.8)
        h.P['chest'].rotation_euler.x += 0.12 * lean; h.P['head'].rotation_euler.x -= 0.05 * lean
    z = floor.place(h, W, yaw, p.z)
    nerves = 0.004 + (0.01 if t > 11.3 else 0.0) + (0.02 if t > T_TURN else 0.0)
    for pv in ('chest', 'neck', 'head'):
        e = h.P[pv]; e.rotation_euler = (e.rotation_euler.x + chat.uniform(-nerves, nerves), e.rotation_euler.y, e.rotation_euler.z + chat.uniform(-nerves, nerves))
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, yaw + je.z)
    n, bl_, gz = face(t); h.expr(n, blink=bl_, gaze=gz); h.key(f)

    for hg, nm in village.DOOR_HINGES:                                  # the open doors move a little in the wind
        ph = hash(nm) % 7
        hg.rotation_euler.z = math.radians(92 + 3 * math.sin(t * 0.9 + ph) + 1.5 * math.sin(t * 2.3 + ph * 2)); key(hg, f, rot=tuple(hg.rotation_euler))

    chanting = t < 15.0
    for vd in VILL:                                                     # sway while chanting; then still; then the heads turn
        sway = 0.035 * math.sin(t * 2.2 + vd['ph']) * (1.0 if chanting else max(0.0, 1 - (t - 15.0) / 0.4))
        vd['h'].rotation_euler = (0, sway, vd['yaw']); key(vd['h'], f, rot=tuple(vd['h'].rotation_euler))
        nod = 0.08 * max(0.0, math.sin(t * 4.4 + vd['ph'])) if chanting else 0.0
        hu = ezs((t - T_TURN) / 0.25)
        vd['piv'].rotation_euler = (nod * (1 - hu), 0, wrap(yaw_of(HARU_AT - vd['h'].location) - vd['yaw']) * hu)
        key(vd['piv'], f, rot=tuple(vd['piv'].rotation_euler))
        vd['lt'].data.energy = 0.12 * (0.85 + 0.3 * flick.random()); vd['lt'].data.keyframe_insert('energy', frame=f)
    ring_glow.data.energy = 4.0 * (0.9 + 0.2 * flick.random()); ring_glow.data.keyframe_insert('energy', frame=f)

    lift = ezs((t - 15.5) / 1.9)                                        # the flower: bowed, lifts its face, grins wider, turns a little
    sway = 0.01 * math.sin(t * 0.7)
    sf_head.rotation_euler = (math.radians(75 - 30 * lift) + sway, math.radians(-12 * ezs((t - T_TURN) / 0.3)), yaw_h + math.pi * (1 - lift))
    key(sf_head, f, rot=tuple(sf_head.rotation_euler))
    wide = t >= 17.3
    for g in PUPILS: g.scale = (1, 1, 1) if t >= 15.9 else (1e-4,) * 3; key(g, f, scale=tuple(g.scale))
    for o in (mouth_wide[0], mouth_wide[1]): o.scale = (1, 1, 1) if wide else (1e-4,) * 3; key(o, f, scale=tuple(o.scale))
    mouth_thin.scale = (1e-4,) * 3 if wide else (1, 1, 1); key(mouth_thin, f, scale=tuple(mouth_thin.scale))

    bpy.context.view_layer.update()
    loc, tgt, lens, fp, fs = shot(t, p, head_pt())
    cam.location = loc; look_at(cam, tgt); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (loc - fp).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    cam.data.dof.aperture_fstop = fs; cam.data.dof.keyframe_insert('aperture_fstop', frame=f)
    fill.location = loc; fill.keyframe_insert('location', frame=f)

tick('animated')
print('FRAMES', F, 'END', END, 'peek at', round(T_PEEK, 2))
constant_interp()
run(sc, OPTS)
