"""Haru #4 "One Step Closer" (wordless, 9:16, about 20 s with the black tail added in post). Set in the big home.

Night. Haru at the top of the main stairs. In the dark a black figure crouches on the bottom step. Light on: nothing.
She rubs her eyes. Off: it is one step up. On: nothing. Off: four steps higher. She flicks faster and faster; every
time it is dark it is closer, until it is two steps below her, head tilted up at her. Light on: she runs to her room,
shuts the door, leans on it and breathes out. She turns her head: it is standing at the foot of her bed. Black.

    blender -b -P scenes/one_step_closer.py -- [--still F] [--range A B] [--res 1080 1920] [--samples 64] [--out DIR]
"""
import bpy, os, sys, math, random
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
SETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, os.path.join(SETS, 'home')); sys.path.insert(0, SETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import kit as K
import home, plan as PL
import haru_clay as HC, haru_puppet as HP, mocap as MC, walker as WK
from claylib import cli, run, key, look_at, camera, constant_interp, Boil, emissive

OPTS = cli('one_step_closer')
FPS = 12
U = PL.UP
sc = K.begin('one_step_closer', res=OPTS['res'], samples=OPTS['samples'], frames=1)
floors = home.build()
bpy.context.view_layer.update()
M = K.M


def ezs(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


# ------------------------------------------------------------------ the doors: Mum's shut, Haru's open (she shuts it)
def hinge_at(p):
    best = None
    for o in bpy.data.objects:
        if o.name.startswith('door_hinge'):
            d = (o.matrix_world.translation - Vector(p)).length
            if best is None or d < best[0]: best = (d, o)
    return best[1]


mum_hinge = hinge_at((0.60, 0.44, U)); mum_hinge.rotation_euler.z = 0.0
haru_hinge = hinge_at((0.40, 0.32, U)); OPEN = haru_hinge.rotation_euler.z
haru_knob = next(c for c in haru_hinge.children_recursive if c.name.startswith('door_knob'))
bpy.context.view_layer.update()
print('DOORS', mum_hinge.matrix_world.translation, haru_hinge.matrix_world.translation, 'knob open at', haru_knob.matrix_world.translation)

# ------------------------------------------------------------------ the stair light, its switch, the moon down the stairs
SW = Vector((0.5935, 0.423, U + 0.078))
K.block('switch_plate', 0.5928, 0.5952, 0.418, 0.428, U + 0.070, U + 0.086, M['trim'], bevel=0.0006)
toggle = K.block('switch_toggle', 0.5912, 0.5930, 0.4215, 0.4245, U + 0.075, U + 0.081, M['trim'], bevel=0.0004)
PX, PY, PZ = 0.55, 0.30, U + K.H - 0.05
K._to(K.cylinder('stair_cord', 0.0005, 0.045, (PX, PY, U + K.H - 0.0225), mat=M['tape']))
BULB = emissive('stair_bulb_glow', (1.0, 0.85, 0.6), 0.0); bulb_em = BULB.node_tree.nodes['Emission'].inputs[1]
K._to(K.sphere('stair_bulb', 0.005, (PX, PY, PZ), scale=(1, 1, 1.3), mat=BULB))
stair_l = K.point_light('stair_light', (PX, PY, PZ - 0.006), 2.2, radius=0.006, color=(1.0, 0.8, 0.55)); K._to(stair_l, 'Lights')
moon_s = K.area_light('stair_moon', (0.5, -0.3, U + 0.16), (0.55, 0.22, 0.03), 9.0, 0.1, (0.55, 0.66, 1.0)); K._to(moon_s, 'Lights')
STAIR_BASE = 2.2
hall_glow = K.area_light('hall_glow', (0.55, 0.03, 0.17), (0.55, 0.22, 0.0), 2.5, 0.1, (0.5, 0.62, 1.0)); K._to(hall_glow, 'Lights')   # moonlight through the front door glass: the steps glow, it stands out black
# a faint cold fill on her face in the dark, so she still reads
face_fill = K.point_light('face_fill', (0.56, 0.36, U + 0.12), 0.0, radius=0.02, color=(0.55, 0.65, 0.95)); K._to(face_fill, 'Lights')

# ------------------------------------------------------------------ the figure: black clay, too thin, too long
INK = K.painted('ink', (0.004, 0.004, 0.005), rough=0.85)


def limb(s, a, b, r0, r1): s.capsule(Vector(a), Vector(b), r0, r1, 12); return s


def hand_shape(s, wrist, d, up, n=4, ln=0.011):
    d, up = Vector(d).normalized(), Vector(up).normalized()
    for k in range(n):
        o = (k - (n - 1) / 2) * 0.0016
        a = Vector(wrist) + up * o; m = a + d * ln * 0.55 + up * o * 0.4; e = m + d * ln * 0.45
        s.capsule(a, m, 0.0008, 0.0007, 8).capsule(m, e, 0.0007, 0.0005, 8)
    s.ellipsoid(Vector(wrist) - d * 0.002, (0.0028, 0.0028, 0.0028))
    return s


def figure_piece(name, s):
    ob = HP.piece(name, s, INK, 'top', bpy.context.collection, voxel=0.0007, smooth=3, lump=0)
    ob.data.transform(Matrix.Scale(1 / HP.S, 4)); return ob


# crouched on a step, facing up the stairs (+y), long hands already on the step above; origin at its feet
s = HP.Shape().ball(Vector((0, 0.017, 0.095)), 0.012)
limb(s, (0, -0.012, 0.03), (0, 0.003, 0.074), 0.011, 0.013)
limb(s, (0, 0.003, 0.074), (0, 0.012, 0.087), 0.006, 0.006)
for sx in (-1, 1):
    limb(s, (sx * 0.007, -0.012, 0.03), (sx * 0.011, 0.012, 0.048), 0.005, 0.0045)       # thigh up to the knee
    limb(s, (sx * 0.011, 0.012, 0.048), (sx * 0.009, 0.004, 0.004), 0.0045, 0.0035)      # shin down
    limb(s, (sx * 0.009, 0.002, 0.002), (sx * 0.009, 0.014, 0.002), 0.0035, 0.003)       # foot
    limb(s, (sx * 0.014, -0.002, 0.071), (sx * 0.021, 0.013, 0.05), 0.004, 0.0035)       # upper arm
    limb(s, (sx * 0.021, 0.013, 0.05), (sx * 0.015, 0.026, 0.026), 0.0035, 0.003)        # forearm to the step above
    hand_shape(s, (sx * 0.015, 0.027, 0.024), (0, 1, -0.6), (1, 0, 0))
crouch = figure_piece('fig_crouch', s)
RISE, RUN = U / 13, (PL.MAIN_STAIRS[3] - PL.MAIN_STAIRS[1]) / 13


def on_step(k):
    """tread k counted from the top (0 = the top step), its top surface; the figure stands back on it"""
    return Vector((0.55, PL.MAIN_STAIRS[3] - RUN * (k + 0.5) - 0.008, U - RISE * (k + 1)))


# standing at the foot of her bed, tall, arms hanging to its knees; origin at its feet, facing -y before turning
s = HP.Shape().ball((0, 0, 0.172), 0.012)
limb(s, (0, 0, 0.065), (0, 0, 0.155), 0.011, 0.014); limb(s, (0, 0, 0.155), (0, 0, 0.165), 0.006, 0.006)
for sx in (-1, 1):
    limb(s, (sx * 0.016, 0, 0.15), (sx * 0.02, -0.004, 0.09), 0.004, 0.0035)
    limb(s, (sx * 0.02, -0.004, 0.09), (sx * 0.021, -0.006, 0.035), 0.0035, 0.003)
    hand_shape(s, (sx * 0.021, -0.006, 0.033), (0, -0.1, -1), (1, 0, 0))
    limb(s, (sx * 0.007, 0, 0.07), (sx * 0.008, 0, 0.0), 0.005, 0.004)
stand = figure_piece('fig_stand', s)
FIG_ROOM = Vector((0.165, 0.115, U))
stand.location = FIG_ROOM
DOOR_IN = Vector((0.383, 0.36, U))
stand.rotation_euler = (0, 0, math.atan2((DOOR_IN - FIG_ROOM).x, -(DOOR_IN - FIG_ROOM).y))
stand.rotation_euler.x = math.radians(-4)                              # leaning toward her, a little


def show(ob, on, f):
    ob.scale = (1, 1, 1) if on else (1e-4,) * 3; key(ob, f, scale=tuple(ob.scale))


# ------------------------------------------------------------------ the story clock
FLICKS = [2.5, 6.3, 7.5, 8.0, 8.5, 8.8, 9.1, 9.4, 10.0]        # dark at the start; every flick toggles the light
def lit(t): return sum(t >= x for x in FLICKS) % 2 == 1
DARK_STEP = [(0.0, 11), (6.3, 10), (8.0, 6), (8.8, 4), (9.4, 1)]  # where it is each time the light goes off
def step_at(t): return [k for (s_, k) in DARK_STEP if t >= s_][-1]


# ------------------------------------------------------------------ Haru
h = HC.HaruClay(name='haru')
LIB = MC.Library(os.path.join(HERE, '..', 'mocap', 'clips.npz'), h)
floor = WK.Floor()
TOP = Vector((0.563, 0.452, U))
RUN_PTS = [TOP, Vector((0.46, 0.47, U)), Vector((0.43, 0.36, U)), Vector((0.40, 0.36, U)), Vector((0.355, 0.40, U))]   # clear of the door's swing
Hh = LIB.clips['run_scared'][1]
V_RUN = LIB.k * float(np.linalg.norm((Hh[-1] - Hh[0])[:2])) / LIB.length('run_scared')
SEGL = [(b - a).length for a, b in zip(RUN_PTS, RUN_PTS[1:])]
RUN_SPEED = 1.6                                                     # a real scared sprint
RUN0 = 11.0; A = RUN0 + sum(SEGL) / (V_RUN * RUN_SPEED)                          # A: she is in her room
END = A + 6.8
F = int(END * FPS); sc.frame_start, sc.frame_end = 1, F
print('RUN', round(V_RUN, 3), 'm/s, in her room at', round(A, 2), 'END', round(END, 2), 'frames', F)


def yaw_of(d): return math.atan2(d.x, -d.y)


def run_at(t):
    """where she is on the run, which way she faces"""
    dist = (t - RUN0) * V_RUN * RUN_SPEED
    for a, b, L in zip(RUN_PTS, RUN_PTS[1:], SEGL):
        if dist <= L: return a.lerp(b, dist / L), yaw_of(b - a)
        dist -= L
    return RUN_PTS[-1], yaw_of(RUN_PTS[-1] - RUN_PTS[-2])


def ang_lerp(a, b, u):
    d = (b - a + math.pi) % (2 * math.pi) - math.pi; return a + d * u


def standing(c, yaw): return MC.rotate(LIB.sample('look_behind', c)[0], yaw)


REST = {k: h.rest[k] for k in ('upper_arm.R', 'forearm.R', 'hand.R', 'upper_arm.L', 'forearm.L', 'hand.L')}


def aim_arm(W, yaw, side, target, w, pole_side=0.6):
    """two-bone IK: bend the arm on `side` ('L'/'R') so the hand reaches `target`, mixed in by weight w"""
    if w <= 0: return W
    MC.apply(h, W, yaw); bpy.context.view_layer.update()
    up, fo, ha = 'upper_arm.' + side, 'forearm.' + side, 'hand.' + side
    D_UP = REST[fo] - REST[up]; D_FO = REST[ha] - REST[fo]; La, Lb = D_UP.length, D_FO.length
    S_ = h.P[up].matrix_world.translation.copy()
    d = Vector(target) - S_; dl = min(d.length, (La + Lb) * 0.999); u = d.normalized()
    ca = (La ** 2 + dl ** 2 - Lb ** 2) / (2 * La * dl); al = math.acos(max(-1, min(1, ca)))
    out = Vector((math.cos(yaw), math.sin(yaw), 0)) * (1 if side == 'L' else -1)     # her left/right in the world
    pole = Vector((0, 0, -1)) + out * pole_side; v = (pole - u * pole.dot(u)).normalized()
    E = S_ + (u * math.cos(al) + v * math.sin(al)) * La; T2 = S_ + u * dl
    q_up = D_UP.normalized().rotation_difference((E - S_).normalized())
    q_fo = D_FO.normalized().rotation_difference((T2 - E).normalized())
    W = dict(W)
    for pv, q in ((up, q_up), (fo, q_fo), (ha, q_fo)):
        a = W[pv]; b = q if a.dot(q) >= 0 else -q
        W[pv] = a.slerp(b, w)
    return W


def switch_reach(t):
    if 7.3 <= t < 10.15: return ezs((t - 7.3) / 0.25) * (1 - ezs((t - 10.0) / 0.15))
    w = 0.0
    for x in (2.5, 6.3): w = max(w, ezs(1 - abs(t - x) / 0.4))
    return w


def head_pt(): return h.P['head'].matrix_world @ Vector((0, -0.012, 0.009))
def face_dir(): return (h.P['head'].matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def face(t):
    if t < 3.0: n = 'worried'
    elif t < 4.6: n = 'suspicious'
    elif t < 5.5: n = 'sleep'                     # squeezing her eyes shut
    elif t < 6.2: n = 'neutral'
    elif t < 10.0: n = 'scared'
    elif t < A + 0.4: n = 'terrified'
    elif t < A + 1.3: n = 'scared'
    elif t < A + 2.9: n = 'relieved'
    elif t < A + 3.6: n = 'neutral'
    elif t < A + 4.3: n = 'worried'
    else: n = 'stare'
    blink = any(abs(t - b) < 0.09 for b in (1.4, 3.6, 6.0, A + 3.0))
    gaze = (0, 10) if t < 11.0 else ((25 * ezs((t - A - 3.6) / 0.8), 0) if t > A + 3.6 else None)
    return n, blink, gaze


def pose(t):
    """root (x, y, z), yaw and world rotations for time t"""
    if t < RUN0:                                                        # at the top of the stairs
        yaw = 0.0
        W = standing(0.1 + 0.04 * math.sin(t * 0.9), yaw)
        if t >= 10.0: W = MC.blend(W, MC.rotate(LIB.sample('terrified', 0.25 + (t - 10.0) * 0.6)[0], yaw), 0.55 * ezs((t - 10.0) / 0.3))
        return TOP, yaw, W
    if t < A:                                                           # the run
        p, yaw = run_at(t)
        W = MC.rotate(LIB.sample('run_scared', (t - RUN0) * RUN_SPEED, loop=True)[0], yaw)
        if t - RUN0 < 0.2: W = MC.blend(MC.rotate(LIB.sample('terrified', 0.85)[0], 0.0), W, ezs((t - RUN0) / 0.2))
        return p, yaw, W
    y_in = yaw_of(RUN_PTS[-1] - RUN_PTS[-2])                            # running in: facing -x
    y_door = math.pi / 2                                                # turned round to face the door (+x)
    y_lean = -math.pi / 2                                               # back to the door, facing into the room
    if t < A + 0.35: yaw = ang_lerp(y_in, y_door, ezs((t - A) / 0.35)); p = RUN_PTS[-1]
    elif t < A + 0.95: yaw = y_door; p = RUN_PTS[-1]
    elif t < A + 1.3:
        u = ezs((t - A - 0.95) / 0.35); yaw = y_door - math.pi * u; p = RUN_PTS[-1].lerp(DOOR_IN, u)   # turns round to lean on it
    else: yaw = y_lean; p = DOOR_IN                                     # back against the door
    W = standing(0.12, yaw)
    if t < A + 0.3: W = MC.blend(MC.rotate(LIB.sample('run_scared', (A - RUN0) * RUN_SPEED, loop=True)[0], yaw), W, ezs((t - A) / 0.3))
    return p, yaw, W


def door_angle(t):
    return OPEN * (1 - ezs((t - A - 0.4) / 0.45))                     # she pushes it shut


# ------------------------------------------------------------------ cameras
cam = camera((0.58, 0.5, U + 0.16), (0.55, 0.16, 0.04), lens=24, fstop=5.6); cam.data.clip_start = 0.003


def shot(t, hp, fd):
    """camera location, target, lens, focus point, f-stop"""
    top = (Vector((0.522, 0.50, U + 0.228)), Vector((0.552, 0.16, 0.03)), 26)       # high behind her, the whole flight below
    sw = (Vector((0.566, 0.395, U + 0.098)), SW + Vector((-0.002, 0, 0)), 42)       # the switch, close
    if t < 2.0 or 3.0 <= t < 4.4 or 6.6 <= t < 10.0: loc, tg, lens = top
    elif t < 3.0 or 6.0 <= t < 6.6: loc, tg, lens = sw
    elif t < 6.0 or t < 11.0:                                           # her face, from down the stairs, a little below
        loc, tg, lens = hp + fd * 0.08 + Vector((0, 0, -0.012)), hp, 45
    elif t < A + 0.1:                                                   # the landing: she runs at us, turns into her door
        loc, tg, lens = Vector((0.45, 0.04, U + 0.15)), hp + Vector((0, 0, -0.02)), 22
    elif t < A + 2.8:                                                   # in her room: she shuts the door, leans on it
        loc, tg, lens = Vector((0.215, 0.245, U + 0.11)), Vector((0.385, 0.355, U + 0.075)), 24
    elif t < A + 4.6:                                                   # her face, as she turns her head
        loc, tg, lens = hp + fd * 0.075 + Vector((0, 0, -0.006)), hp, 45
    else:                                                               # the foot of her bed: slow push-in
        u = ezs((t - A - 4.6) / 2.2)
        head = FIG_ROOM + Vector((0, 0, 0.16))
        loc = Vector((0.355, 0.335, U + 0.118)).lerp(Vector((0.27, 0.235, U + 0.13)), u)
        return loc, head, 30, head, 4.0
    return loc, tg, lens, tg, 5.6


# ------------------------------------------------------------------ animate
boil = Boil(5, amp=0.00012, rot=0.003)
chat = random.Random(11)
for f in range(1, F + 1):
    t = (f - 1) / FPS
    p, yaw, W = pose(t)
    if t < RUN0:
        W = aim_arm(W, yaw, 'L', SW + Vector((-0.002, 0, 0.002 if lit(t) else -0.002)), switch_reach(t))
        if 4.6 <= t < 5.7:                                              # rubbing her eyes
            MC.apply(h, W, yaw); bpy.context.view_layer.update()
            eye = head_pt() + Vector((-0.004, -0.006, 0.0)) + Vector((math.cos(t * 14), 0, math.sin(t * 14))) * 0.0012
            W = aim_arm(W, yaw, 'R', eye, ezs((t - 4.6) / 0.3) * (1 - ezs((t - 5.4) / 0.3)), pole_side=0.9)
    elif A + 0.35 <= t < A + 1.0:                                       # her left hand on the door, pushing it shut
        haru_hinge.rotation_euler.z = door_angle(t); bpy.context.view_layer.update()
        W = aim_arm(W, yaw, 'L', haru_knob.matrix_world.translation, ezs((t - A - 0.35) / 0.15) * (1 - ezs((t - A - 0.85) / 0.15)))
    h.root.location = (p.x, p.y, p.z); h.root.rotation_euler = (0, 0, yaw)
    MC.apply(h, W, yaw)
    if t >= A + 1.3:                                                    # relief: head back, a long breath; then she turns her head
        rel = ezs((t - A - 1.4) / 0.5) * (1 - ezs((t - A - 2.6) / 0.4))
        turn = ezs((t - A - 3.5) / 1.0)
        h.P['head'].rotation_euler.x -= 0.25 * rel; h.P['chest'].rotation_euler.x -= 0.08 * rel
        h.P['neck'].rotation_euler.z += 0.35 * turn; h.P['head'].rotation_euler.z += 0.45 * turn; h.P['chest'].rotation_euler.z += 0.12 * turn
    z = floor.place(h, W, yaw, p.z)
    nerves = 0.004 + (0.012 if 6.3 <= t < A + 1.3 else 0.0) + (0.02 if t > A + 4.4 else 0.0)
    for pv in ('chest', 'neck', 'head'):
        e = h.P[pv]
        e.rotation_euler = (e.rotation_euler.x + chat.uniform(-nerves, nerves), e.rotation_euler.y, e.rotation_euler.z + chat.uniform(-nerves, nerves))
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, yaw + je.z)
    n, bl_, gz = face(t); h.expr(n, blink=bl_, gaze=gz); h.key(f)

    haru_hinge.rotation_euler.z = door_angle(t); key(haru_hinge, f, rot=tuple(haru_hinge.rotation_euler))
    on = lit(t) and t < A + 0.5
    toggle.rotation_euler = (0, math.radians(-14 if lit(t) else 14), 0); key(toggle, f, rot=tuple(toggle.rotation_euler))
    stair_l.data.energy = STAIR_BASE if on else 0.0; stair_l.data.keyframe_insert('energy', frame=f)
    bulb_em.default_value = 6.0 if on else 0.0; bulb_em.keyframe_insert('default_value', frame=f)
    face_fill.data.energy = 0.0 if on else 0.05; face_fill.data.keyframe_insert('energy', frame=f)
    crouch.location = on_step(step_at(t)); key(crouch, f, loc=tuple(crouch.location))
    show(crouch, (not lit(t)) and t < RUN0, f)
    show(stand, t >= A + 0.2, f)

    bpy.context.view_layer.update()
    hp, fd = head_pt(), face_dir()
    loc, tgt, lens, fp, fs = shot(t, hp, fd)
    cam.location = loc; look_at(cam, tgt); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (loc - fp).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    cam.data.dof.aperture_fstop = fs; cam.data.dof.keyframe_insert('aperture_fstop', frame=f)

constant_interp()
run(sc, OPTS)
