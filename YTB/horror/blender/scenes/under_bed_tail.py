# ------------------------------------------------------------------ Haru #2 "Something Under the Bed": the story
import mocap as MC
LIB = MC.Library(os.path.join(HERE, '..', 'mocap', 'clips.npz'), h)
K = LIB.k
END = 15.5                      # then 1.5 s of black is added in post
F = int(END * FPS); sc.frame_end = F
for e in eyes: e.hide_render = True                               # the doorway eyes of room test 3 are not in this story


def turn2(v, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)); return Vector((c * v.x - s * v.y, s * v.x + c * v.y))


def measure(clip, c, yaw, mirror=False):
    """head and root offset (xy) of a pose with the root at the origin"""
    W, _ = LIB.sample(clip, c, mirror)
    h.root.location = (0, 0, 0); h.root.rotation_euler = (0, 0, math.radians(yaw))
    MC.apply(h, MC.rotate(W, math.radians(yaw)), math.radians(yaw)); bpy.context.view_layer.update()
    hd = h.P['head'].matrix_world.translation; hi = h.P['hips'].matrix_world.translation
    return Vector((hd.x, hd.y)), Vector((hi.x, hi.y))


def lie_yaw(clip, c, mirror=False):
    hd, hi = measure(clip, c, 0, mirror); v = hd - hi
    return math.degrees(math.pi - math.atan2(v.y, v.x))            # turns her so her head points at the pillow (-x)


bx0, bx1, by0, by1 = BED
HEAD_TGT = Vector((bx0 + 0.03, 0.12))                              # her head on the pillow
Y_LD, Y_SL = lie_yaw('lying_down', 4.6), lie_yaw('laying_sleeping', 0.0, True)   # mirrored: she sleeps facing us, not the wall
P_DOOR, P_IN = Vector(((d0 + d1) / 2, WY + 0.03)), Vector((0.125, 0.1))      # veers left, so the doorway behind her is clear
P_W0, P_BS = Vector((-0.02, 0.0)), Vector((-0.125, 0.035))
SEGS = [
    dict(t0=0.0, t1=1.5, clip='happy_walk', c0=0.0, loop=True, at=P_DOOR, to=P_IN, fade=0.0),     # in she comes, happy
    dict(t0=1.5, t1=3.0, clip='look_behind', c0=0.3, c1=2.6, yaw=0, fade=0.3),                     # she felt something
    dict(t0=3.0, t1=4.0, clip='shrug', c0=0.15, c1=1.75, yaw=0, fade=0.25),                        # ...nothing
    dict(t0=4.0, t1=5.2, clip='happy_walk', c0=0.0, loop=True, at=P_W0, to=P_BS, fade=0.0),        # to bed
    dict(t0=5.2, t1=7.0, clip='lying_down', c0=2.2, c1=4.6, yaw=Y_LD, fade=0.0),                   # in bed, lies back
    dict(t0=7.0, t1=END, clip='laying_sleeping', c0=0.0, c1=END - 7.0, loop=True, yaw=Y_SL, mirror=True, fade=0.0),
]
hd, _ = measure('lying_down', 4.6, Y_LD); SEGS[4]['end'] = HEAD_TGT - hd
hd, _ = measure('laying_sleeping', 0.0, Y_SL, True); SEGS[5]['at'] = HEAD_TGT - hd


def resolve():
    end = None
    for s in SEGS:
        s.setdefault('fade', 0.3); s.setdefault('mirror', False); s.setdefault('loop', False); s.setdefault('air', False)
        start = Vector(s['at']) if 'at' in s else end
        if 'to' in s:
            d = Vector(s['to']) - start
            s['yaw'] = math.degrees(math.atan2(d.x, -d.y))
            H = LIB.clips[s['clip']][1]; T = LIB.length(s['clip'])
            v = K * (Vector(H[-1][:2]) - Vector(H[0][:2])).length / T
            s['c1'] = s['c0'] + d.length / v
        s.setdefault('c1', s['c0'] + (s['t1'] - s['t0']))
        if 'end' in s:
            dh = LIB.hips(s['clip'], s['c1']) - LIB.hips(s['clip'], s['c0'])
            start = Vector(s['end']) - turn2(Vector((dh.x, dh.y)) * K, s['yaw'])
        s['start'] = start
        dh = LIB.hips(s['clip'], s['c1'], s['mirror'], s['loop']) - LIB.hips(s['clip'], s['c0'], s['mirror'], s['loop'])
        end = start + turn2(Vector((dh.x, dh.y)) * K, s['yaw'])


resolve()


def eval_seg(s, t):
    u = (t - s['t0']) / max(1e-6, s['t1'] - s['t0'])
    if not s['loop']: u = min(max(u, 0.0), 1.0)
    c = s['c0'] + (s['c1'] - s['c0']) * u
    W, hp = LIB.sample(s['clip'], c, s['mirror'], s['loop'])
    d = hp - LIB.hips(s['clip'], s['c0'], s['mirror'], s['loop'])
    return MC.rotate(W, math.radians(s['yaw'])), s['start'] + turn2(Vector((d.x, d.y)) * K, s['yaw'])


def performance(t):
    i = max(j for j, s in enumerate(SEGS) if t >= s['t0'] - 1e-9)
    s = SEGS[i]; W, xy = eval_seg(s, t)
    if i > 0 and s['fade'] > 0 and t < s['t0'] + s['fade']:
        k = seg(t, s['t0'], s['t0'] + s['fade'])
        Wp, xyp = eval_seg(SEGS[i - 1], t)
        W = MC.blend(Wp, W, k); xy = xyp.lerp(xy, k)
    return W, xy, s


def face(t):
    if t < 1.55: n = 'happy'
    elif t < 2.9: n = 'suspicious'
    elif t < 3.2: n = 'neutral'
    elif t < 5.2: n = 'smile'
    elif t < 6.3: n = 'smile'
    elif t < 14.0: n = 'sleep'
    else: n = 'stare'
    blink = any(abs(t - b) < 0.09 for b in (3.6, 5.6))
    return n, blink, None


# ------------------------------------------------------------------ the hallway she comes from: warm and lit, so the
# shape that darts across it reads as a black silhouette
HALL = painted('hall_wall', (0.32, 0.25, 0.18))
for o in bpy.data.objects:
    if o.name.split('.')[0] in ('void', 'hall_l', 'hall_r', 'hall_top'): o.data.materials[0] = HALL
box('hall_floor', d0 - 0.1, d1 + 0.1, WY + 0.005, WY + 0.2, -0.002, 0.0, FLOOR, bevel=0.0003)
door_l.data.color = (1.0, 0.78, 0.55)

# the shape: tall, thin, too-long arms; crosses the doorway in three frames and slips behind the open door
INK = painted('ink', (0.004, 0.004, 0.005), rough=0.9)
s_ = HP.Shape().ball((0, 0, 0.165), 0.013).capsule((0, 0, 0.05), (0, 0, 0.15), 0.011, 0.014)
for sx in (-1, 1):
    s_.capsule((sx * 0.014, 0, 0.145), (sx * 0.02, -0.01, 0.03), 0.004, 0.003)     # arms hang to the knees
    s_.capsule((sx * 0.006, 0, 0.06), (sx * 0.008, 0.01, 0.0), 0.005, 0.004)
shape_ob = HP.piece('shape', s_, INK, 'top', bpy.context.collection, voxel=0.0008, smooth=4, lump=0)
shape_ob.data.transform(Matrix.Scale(1 / HP.S, 4))                                  # piece() builds x0.1; this is set scale
SHAPE_Y = WY + 0.07

# ------------------------------------------------------------------ under the bed: two eyes and a long, thin arm
MON = painted('monster_skin', (0.03, 0.034, 0.03), rough=0.7)
MEYE = emissive('monster_eye', (1.0, 0.92, 0.62), 9.0)
m_eyes = [sphere('m_eye', 0.0032, (-0.205 + sx * 0.0075, 0.1, 0.017), scale=(1, 0.5, 0.6), mat=MEYE) for sx in (-1, 1)]
SHOULDER = Vector((-0.212, 0.1, 0.014))
NSEG, HAND_L = 12, 0.026
arm = []
for i in range(NSEG):
    r = 0.0034 - 0.0013 * i / (NSEG - 1) + (0.0007 if i == NSEG // 2 else 0.0)        # tapers; a bony elbow
    ob = HP.piece(f'arm_{i}', HP.Shape().capsule((0, 0, -0.5), (0, 0, 0.5), r / HP.S, None, 16), MON, 'top',
                  bpy.context.collection, voxel=0.008, smooth=3, lump=0)     # unit length (0.1 m), stretched per frame
    ob.rotation_mode = 'QUATERNION'; arm.append(ob)
joints = [sphere('arm_joint', 0.0034 - 0.0014 * i / NSEG, (0, 0, -1), mat=MON) for i in range(NSEG + 1)]


def build_hand():
    s = HP.Shape().ellipsoid((0, 0, 0.004), (0.0045, 0.0022, 0.006))               # narrow palm; reach is local +z
    for k, fx in enumerate((-0.0036, -0.0012, 0.0012, 0.0036)):
        ln = 0.0115 + (0.002 if 0 < k < 3 else 0.0)
        a = Vector((fx, 0, 0.009)); b = a + Vector((fx * 0.4, -0.001, ln * 0.55)); c = b + Vector((fx * 0.2, -0.003, ln * 0.45))
        s.capsule(a, b, 0.0011, 0.0009, 10).capsule(b, c, 0.0009, 0.0006, 10).ball(b, 0.0012, 10)   # knuckles
    s.capsule((-0.004, 0, 0.003), (-0.009, -0.002, 0.01), 0.001, 0.0007, 10)        # thumb
    ob = HP.piece('m_hand', s, MON, 'top', bpy.context.collection, voxel=0.00015, smooth=2, lump=0)
    ob.data.transform(Matrix.Scale(1 / HP.S, 4)); ob.rotation_mode = 'QUATERNION'; return ob


hand = build_hand()


def hand_tip(t):
    """where the fingertips are at time t"""
    cheek = Vector((HEAD_TGT.x + 0.004, 0.104, MATT + 0.017))
    P = [(10.0, Vector((-0.212, 0.05, 0.006))), (11.4, Vector((-0.214, 0.044, MATT + 0.012))),
         (13.0, Vector((-0.226, 0.08, MATT + 0.024))), (13.7, cheek + Vector((0, -0.006, 0.002))), (14.0, cheek + Vector((0, -0.0035, 0.001)))]
    if t <= P[0][0]: return P[0][1]
    for (ta, a), (tb, b) in zip(P, P[1:]):
        if t <= tb: return a.lerp(b, ease(seg(t, ta, tb)))
    return P[-1][1]


def place_arm(t):
    tip = hand_tip(t); prev = hand_tip(t - 0.25)
    z = (tip - prev); z = z.normalized() if z.length > 1e-5 else Vector((0, 0.6, 0.8)).normalized()
    z = (z + Vector((0, 0.3, 0.6))).normalized()                                     # the hand leads, fingers forward
    base = tip - z * HAND_L
    C = (SHOULDER + base) / 2 + Vector((0, -0.03, 0.012))                            # the arm bows out from under the bed
    pts = [((1 - u) ** 2) * SHOULDER + 2 * (1 - u) * u * C + (u ** 2) * base for u in [i / NSEG for i in range(NSEG + 1)]]
    for i, ob in enumerate(arm):
        a, b = pts[i], pts[i + 1]; d = b - a
        ob.location = (a + b) / 2
        ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
        ob.scale = (1, 1, d.length / 0.1)
    for p_, jo in zip(pts, joints): jo.location = p_                                  # knobbly joints hide the seams
    x = z.cross(Vector((0, 0, 1))); x = x.normalized() if x.length > 1e-4 else Vector((1, 0, 0)); y = z.cross(x)
    hand.matrix_world = Matrix.Translation(base) @ Matrix((x, y, z)).transposed().to_4x4()



# ------------------------------------------------------------------ cameras
cam = camera((0, -0.3, 0.09), (0, 0, 0.06), lens=35, fstop=5.6)
cam.data.clip_start = 0.002
CUTS = (4.0, 5.2, 7.0, 8.5, 10.0, 14.0)


def head_pt():
    return h.P['head'].matrix_world @ Vector((0, -0.012, 0.009))


def shot(t, hp):
    if t < 4.0:                     # facing the open door: she walks in toward us; the hall glows behind her
        u = seg(t, 1.5, 4.0)
        loc = Vector((0.235, -0.17, 0.075)).lerp(Vector((0.175, -0.07, 0.078)), ease(u))
        tgt = Vector((0.21, 0.22, 0.07)).lerp(hp + Vector((0, 0.03, -0.012)), ease(seg(t, 0.8, 2.2)))
        return loc, tgt, 35, hp, 5.6
    if t < 5.2:                     # wide: to the bed
        return Vector((0.04, -0.22, 0.1)), Vector((-0.13, 0.08, 0.05)), 30, hp, 6.0
    if t < 7.0:                     # in bed, lying back; the lamp goes off
        return Vector((-0.11, -0.1, 0.115)), Vector((-0.2, 0.115, 0.065)), 40, hp, 6.0
    if t < 8.5:                     # her face, eyes closed (framed upright: the camera rolls with her head)
        u = ease(seg(t, 7.0, 8.5))
        return hp + face_dir() * (0.085 - 0.015 * u), hp, 60, hp, 9.0
    if t < 10.0:                    # under the bed: dark, then two eyes
        ep = Vector((-0.205, 0.1, 0.017))
        return Vector((-0.195, -0.08, 0.011)), ep, 45, ep, 4.0
    if t < 14.0:                    # the hand comes up and reaches for her face; we follow it in
        u = ease(seg(t, 10.0, 14.0)); tip = hand_tip(t)
        loc = Vector((-0.175, -0.1, 0.08)).lerp(Vector((-0.208, -0.035, 0.083)), u)
        tgt = tip.lerp((tip + hp) / 2, seg(t, 12.5, 14.0))
        return loc, tgt, 45 + 12 * u, tip, 8.0
    u = ease(seg(t, 14.17, 14.55))  # her eyes snap open: fast push into her face
    return hp + face_dir() * (0.09 - 0.042 * u), hp, 50 + 12 * u, hp, 11.0


def face_dir():
    return (h.P['head'].matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def head_up():
    return (h.P['head'].matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()


# ------------------------------------------------------------------ animate
shade_em = SHADE.node_tree.nodes['Emission'].inputs[1]
boil = Boil(5, amp=0.00018, rot=0.004)
chat = random.Random(7)
for f in range(1, F + 1):
    t = (f - 1) / FPS
    W, xy, s = performance(t)
    yaw = math.radians(s['yaw'])
    h.root.location = (xy.x, xy.y, 0.0); h.root.rotation_euler = (0, 0, yaw)
    MC.apply(h, W, yaw)
    for pv in ('chest', 'neck', 'head', 'upper_arm.L', 'upper_arm.R'):
        e = h.P[pv]; a = 0.008
        e.rotation_euler = (e.rotation_euler.x + chat.uniform(-a, a), e.rotation_euler.y, e.rotation_euler.z + chat.uniform(-a, a))
    settle(SUPPORTS)
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, yaw + je.z)
    n, bl_, gz = face(t)
    h.expr(n, blink=bl_, gaze=gz)
    h.key(f)

    # the door: wide open while she comes in, shut by the time we see the bed
    ang = -85 if t < 4.0 else -1
    hinge.rotation_euler = (0, 0, math.radians(ang)); key(hinge, f, rot=tuple(hinge.rotation_euler))
    door_l.data.energy = 2.2 if t < 4.0 else 0.0; door_l.data.keyframe_insert('energy', frame=f)
    # the shape darts across the lit hall behind her (frames 5-7), smeared by its speed
    u = seg(t, 0.5, 0.77)
    vis = 0.0 < u < 1.0
    shape_ob.location = (d0 - 0.06 + (d1 - 0.005 - d0 + 0.06) * u, SHAPE_Y, 0.0)
    shape_ob.rotation_euler = (0, math.radians(14), 0)
    shape_ob.scale = (2.2, 1, 1) if vis else (1e-4,) * 3
    key(shape_ob, f, loc=tuple(shape_ob.location), rot=tuple(shape_ob.rotation_euler), scale=tuple(shape_ob.scale))
    # the lamp: on until she is in bed
    lit = 1.0 if t < 6.5 else 0.0
    lamp.data.energy = 0.6 * lit * (1 + boil.r.uniform(-0.03, 0.03)); lamp.data.keyframe_insert('energy', frame=f)
    shade_em.default_value = 3.0 * lit + 0.03; shade_em.keyframe_insert('default_value', frame=f)
    key_l.data.energy = KEY_E * (1 + boil.r.uniform(-0.012, 0.012)) * (1.0 if t < 6.5 else 0.75); key_l.data.keyframe_insert('energy', frame=f)
    # under the bed: eyes from 9.0 s (a blink at 9.7), the arm from 10.0 s
    show = 1.0 if t >= 9.0 else 1e-4
    bk = 0.12 if abs(t - 9.7) < 0.05 else 1.0
    for e in m_eyes: e.scale = (show, show * 0.5, show * 0.6 * bk); key(e, f, scale=tuple(e.scale))
    place_arm(t)
    on = 1.0 if t >= 10.0 else 1e-4
    for ob in arm + [hand]:
        if on < 1: ob.scale = (1e-4,) * 3
        key(ob, f, loc=tuple(ob.location), scale=tuple(ob.scale)); ob.keyframe_insert('rotation_quaternion', frame=f)
    for jo in joints:
        jo.scale = (1, 1, 1) if on == 1 else (1e-4,) * 3; key(jo, f, loc=tuple(jo.location), scale=tuple(jo.scale))

    bpy.context.view_layer.update()
    hp = head_pt()
    loc, tgt, lens, fp, fs = shot(t, hp)
    cam.location = loc; look_at(cam, tgt)
    if 7.0 <= t < 8.5 or t >= 14.0:                                 # roll so her face is upright in the frame
        zc = (loc - tgt).normalized(); yc = head_up(); yc = (yc - zc * yc.dot(zc)).normalized(); xc = yc.cross(zc)
        cam.rotation_euler = Matrix((xc, yc, zc)).transposed().to_euler('XYZ', cam.rotation_euler)
    key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.focus_distance = (loc - fp).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    cam.data.dof.aperture_fstop = fs; cam.data.dof.keyframe_insert('aperture_fstop', frame=f)

constant_interp()
run(sc, OPTS)
