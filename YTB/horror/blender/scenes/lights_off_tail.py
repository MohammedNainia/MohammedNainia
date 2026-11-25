# ------------------------------------------------------------------ Haru #3 "Lights Off": the story
import mocap as MC
LIB = MC.Library(os.path.join(HERE, '..', 'mocap', 'clips.npz'), h)
END = 11.5                      # then 1.5 s of black in post
F = int(END * FPS); sc.frame_end = F
for e in eyes: e.hide_render = True
hinge.rotation_euler = (0, 0, math.radians(-1))                    # the door is shut
for o in list(bpy.data.objects):                                    # no chair in this story: it stood where she stands
    if o.name.split('.')[0] in ('seat', 'chair_leg', 'chair_post', 'chair_rail', 'chair_rail2'):
        for c in list(o.users_collection): c.objects.unlink(o)


def ezs(u): return u * u * (3 - 2 * u)


# ------------------------------------------------------------------ set additions: ceiling + light, switch, rug
CEIL_Z = 0.25
box('ceiling', WX0 - 0.01, WX1, -0.45, WY + 0.005, CEIL_Z, CEIL_Z + 0.01, painted('ceiling', (0.2, 0.2, 0.19)), bevel=0.0005)
FIXTURE = emissive('fixture', (1.0, 0.85, 0.62), 2.0)
fix = sphere('fixture', 0.012, (0.0, 0.02, CEIL_Z - 0.004), scale=(1, 1, 0.5), mat=FIXTURE)
ceil_l = point_light('ceiling_light', (0.0, 0.02, CEIL_Z - 0.03), 2.5, radius=0.02, color=(1.0, 0.82, 0.6))
SWX, SWZ = 0.135, 0.078
box('switch_plate', SWX - 0.005, SWX + 0.005, WY - 0.0072, WY - 0.005, SWZ - 0.008, SWZ + 0.008, TRIM, bevel=0.0008)
toggle = box('switch_toggle', SWX - 0.0015, SWX + 0.0015, WY - 0.0095, WY - 0.007, SWZ - 0.003, SWZ + 0.003, TRIM, bevel=0.0005)
r2 = cylinder('rug_door', 0.05, 0.0012, (SWX - 0.02, WY - 0.05, 0.0006), mat=RUG, verts=48); cols.objects.link(r2)
fill_h = area_light('moon_bounce', (0.02, 0.0, 0.14), (SWX - 0.02, WY - 0.03, 0.1), 0.0, 0.15, (0.55, 0.65, 0.95))   # cold fill so her face reads in the dark

# ------------------------------------------------------------------ the figure (black clay, too tall, too thin), three poses
INK = painted('ink', (0.004, 0.004, 0.005), rough=0.85)
FEYE = emissive('figure_eye', (0.92, 0.94, 0.85), 2.5)


def limb(s, a, b, r0, r1): s.capsule(Vector(a), Vector(b), r0, r1, 12); return s


def hand_shape(s, wrist, d, up, n=4, ln=0.011):
    """long thin fingers from the wrist along d, spread along up"""
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


def eyes_for(name, head, look, r=0.012):
    look = Vector(look).normalized(); side = look.cross(Vector((0, 0, 1))).normalized()
    out = []
    for sx in (-1, 1):
        p = Vector(head) + look * (r * 0.85) + side * sx * 0.0045 + Vector((0, 0, 0.001))
        out.append(sphere(name + '_eye', 0.0017, tuple(p), scale=(1, 1, 0.7), mat=FEYE))
    return out


# 1) standing in the corner by the window, facing the room
cx_, cy_ = -0.085, WY - 0.025
s = HP.Shape().ball((cx_, cy_, 0.172), 0.012)
limb(s, (cx_, cy_, 0.065), (cx_, cy_, 0.155), 0.011, 0.014); limb(s, (cx_, cy_, 0.155), (cx_, cy_, 0.165), 0.006, 0.006)
for sx in (-1, 1):
    limb(s, (cx_ + sx * 0.016, cy_, 0.15), (cx_ + sx * 0.02, cy_ - 0.004, 0.09), 0.004, 0.0035)
    limb(s, (cx_ + sx * 0.02, cy_ - 0.004, 0.09), (cx_ + sx * 0.021, cy_ - 0.006, 0.035), 0.0035, 0.003)
    hand_shape(s, (cx_ + sx * 0.021, cy_ - 0.006, 0.033), (0, -0.1, -1), (1, 0, 0))
    limb(s, (cx_ + sx * 0.007, cy_, 0.07), (cx_ + sx * 0.008, cy_, 0.0), 0.005, 0.004)
fig_corner = figure_piece('fig_corner', s); fe_corner = eyes_for('corner', (cx_, cy_, 0.172), (0.15, -1, -0.15))

# 2) crouched upside down on the ceiling above the bed, head hanging, looking down at the pillow
gx, gy = -0.17, 0.12
s = HP.Shape().ball((gx - 0.01, gy, CEIL_Z - 0.06), 0.012)
limb(s, (gx + 0.02, gy, CEIL_Z - 0.02), (gx - 0.005, gy, CEIL_Z - 0.045), 0.012, 0.013)     # back pressed to the ceiling, hunched
for sy in (-1, 1):
    limb(s, (gx + 0.022, gy + sy * 0.008, CEIL_Z - 0.02), (gx + 0.035, gy + sy * 0.02, CEIL_Z - 0.045), 0.004, 0.0035)   # knees hang down
    limb(s, (gx + 0.035, gy + sy * 0.02, CEIL_Z - 0.045), (gx + 0.03, gy + sy * 0.024, CEIL_Z - 0.003), 0.0035, 0.003)    # feet on the ceiling
    limb(s, (gx - 0.002, gy + sy * 0.012, CEIL_Z - 0.04), (gx - 0.03, gy + sy * 0.03, CEIL_Z - 0.03), 0.0035, 0.003)      # arms spread
    limb(s, (gx - 0.03, gy + sy * 0.03, CEIL_Z - 0.03), (gx - 0.045, gy + sy * 0.035, CEIL_Z - 0.004), 0.003, 0.0026)
    hand_shape(s, (gx - 0.045, gy + sy * 0.035, CEIL_Z - 0.003), (-1, sy * 0.3, 0), (0, 1, 0))
fig_ceiling = figure_piece('fig_ceiling', s); fe_ceiling = eyes_for('ceiling', (gx - 0.01, gy, CEIL_Z - 0.06), (-0.4, -0.3, -1))

# 3) on her other side, by the door: tall, bent over her, its long fingers already on the switch
fx = SWX + 0.033
HD = Vector((fx - 0.017, WY - 0.026, 0.143))
s = HP.Shape().ball(HD, 0.012)
limb(s, (fx, WY - 0.022, 0.065), (fx - 0.008, WY - 0.024, 0.128), 0.011, 0.014)
limb(s, (fx - 0.008, WY - 0.024, 0.128), HD + Vector((0.004, 0, -0.006)), 0.006, 0.006)
for sx in (-1, 1): limb(s, (fx + sx * 0.007, WY - 0.022, 0.066), (fx + sx * 0.008, WY - 0.022, 0.0), 0.005, 0.004)
limb(s, (fx + 0.008, WY - 0.022, 0.124), (fx + 0.016, WY - 0.03, 0.07), 0.004, 0.0035)          # its far arm hangs
limb(s, (fx + 0.016, WY - 0.03, 0.07), (fx + 0.016, WY - 0.034, 0.03), 0.0035, 0.003)
EL = Vector((fx - 0.004, WY - 0.032, 0.1))                                                     # near arm: down to the switch
limb(s, (fx - 0.012, WY - 0.021, 0.124), EL, 0.004, 0.0035)
WR = Vector((SWX + 0.005, WY - 0.009, SWZ - 0.012))
limb(s, EL, WR, 0.0035, 0.003)
hand_shape(s, WR, (-0.25, 0.05, 1), (1, 0, 0.2), ln=0.013)
fig_side = figure_piece('fig_side', s); fe_side = eyes_for('side', HD, (-1, -0.45, -0.45))

# the dent it left in the bed: a pressed hollow with creases running out of it
DENT = Vector((-0.15, 0.115, MATT))
s = HP.Shape()
for k in range(11):
    a = 2 * math.pi * k / 11 + 0.3 * math.sin(k * 1.7)
    d = Vector((math.cos(a), math.sin(a), 0)); ln = 0.012 + 0.006 * ((k * 7) % 3) / 2
    s.capsule(DENT + d * 0.009 + Vector((0, 0, 0.0006)), DENT + d * (0.009 + ln) + Vector((0, 0, 0.0002)), 0.0011, 0.0004, 8)
dent = HP.piece('dent', s, painted('crease', (0.42, 0.41, 0.4)), 'top', bpy.context.collection, voxel=0.0005, smooth=2, lump=0)
dent.data.transform(Matrix.Scale(1 / HP.S, 4))
hollow = sphere('dent_hollow', 0.012, tuple(DENT + Vector((0, 0, 0.0003))), scale=(1.3, 1, 0.04), mat=painted('sheet_shadow', (0.35, 0.34, 0.33)))
hollow.hide_render = True
dent_parts = [dent]

# ------------------------------------------------------------------ Haru at the switch, facing the wall
ROOT = Vector((SWX - 0.022, WY - 0.038)); YAW = math.pi
OFF_ON = [0.85, 2.4, 3.9, 5.4, 6.9, 10.0, 11.4]               # each flick of the switch
def lit(t): return sum(t >= x for x in OFF_ON) % 2 == 0      # on at the start, then every flick toggles it


def base_pose(t):
    """world rotations (yaw included): standing, looking around over her right shoulder, then back over her left at the bed"""
    def at(c, mirror=False): return MC.rotate(LIB.sample('look_behind', c, mirror)[0], YAW)
    if t < 2.5: return at(0.1 + 0.1 * t / 2.5)
    if t < 4.0: return MC.blend(at(0.2), at(0.4 + (t - 2.5) / 1.5 * 2.0), ezs(min(1, (t - 2.5) / 0.3)))
    if t < 5.5: return at(min(3.6, 2.4 + (t - 4.0)))
    if t < 8.5:
        m = at(0.8 + (t - 5.5) / 3.0 * 1.4, True)
        return MC.blend(at(3.6), m, ezs(min(1, (t - 5.5) / 0.35)))
    if t < 10.3: return MC.blend(at(2.2, True), at(0.15), ezs(min(1, (t - 8.5) / 0.4)))
    return MC.blend(at(0.15), at(0.5 + (t - 10.3) * 1.1), ezs(min(1, (t - 10.3) / 0.4)))   # slowly turns her head to it


def reach_weight(t):
    if 8.5 <= t: return ezs(min(1.0, (t - 8.6) / 1.0))       # the slow reach in the dark, then she freezes there
    w = 0.0
    for x in OFF_ON[:5]: w = max(w, ezs(max(0.0, 1 - abs(t - x) / 0.35)))
    return w


REST = {k: h.rest[k] for k in ('upper_arm.R', 'forearm.R', 'hand.R')}
D_UP = (REST['forearm.R'] - REST['upper_arm.R']); D_FO = (REST['hand.R'] - REST['forearm.R'])
L_A, L_B = D_UP.length, D_FO.length


def aim_arm(W, t):
    w = reach_weight(t)
    if w <= 0: return W
    MC.apply(h, W, YAW); bpy.context.view_layer.update()
    S_ = h.P['upper_arm.R'].matrix_world.translation.copy()
    T_ = Vector((SWX + 0.001, WY - 0.012, SWZ + (0.002 if t < 10.0 else 0.004)))
    d = T_ - S_; dl = min(d.length, (L_A + L_B) * 0.999); u = d.normalized()
    ca = (L_A ** 2 + dl ** 2 - L_B ** 2) / (2 * L_A * dl); al = math.acos(max(-1, min(1, ca)))
    pole = Vector((0.4, 0, -1)); v = (pole - u * pole.dot(u)).normalized()
    E = S_ + (u * math.cos(al) + v * math.sin(al)) * L_A; T2 = S_ + u * dl
    q_up = D_UP.normalized().rotation_difference((E - S_).normalized())
    q_fo = D_FO.normalized().rotation_difference((T2 - E).normalized())
    W = dict(W)
    for pv, q in (('upper_arm.R', q_up @ LIB.A['upper_arm.R'].inverted() @ LIB.A['upper_arm.R']), ('forearm.R', q_fo), ('hand.R', q_fo)):
        a = W[pv]; b = q if a.dot(q) >= 0 else -q
        W[pv] = a.slerp(b, w)
    return W


def face(t):
    if t < 2.5: n = 'neutral'
    elif t < 4.0: n = 'worried'
    elif t < 6.2: n = 'suspicious'
    elif t < 8.5: n = 'scared'
    elif t < 10.0: n = 'worried'
    elif t < 10.8: n = 'stare'
    else: n = 'terrified'
    return n, any(abs(t - b) < 0.09 for b in (1.7, 4.6, 9.2)), None


# ------------------------------------------------------------------ cameras
cam = camera((0, -0.3, 0.09), (0, 0, 0.06), lens=24, fstop=5.6)
cam.data.clip_start = 0.002


def head_pt(): return h.P['head'].matrix_world @ Vector((0, -0.012, 0.009))
def face_dir(): return (h.P['head'].matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def shot(t, hp):
    if t < 4.0:                         # the room from the front: her at the switch, the corner by the window
        return Vector((0.012, -0.17, 0.085)), Vector((0.012, 0.2, 0.08)), 24, Vector((0.012, 0.18, 0.09)), 5.6
    if t < 6.2:                         # looking up at the bed and the ceiling above it
        return Vector((-0.06, -0.1, 0.05)), Vector((-0.16, 0.12, 0.17 - 0.06 * seg(t, 5.4, 6.2))), 22, Vector((-0.16, 0.12, 0.12)), 5.6
    if t < 8.5:                         # her face, staring at the bed; then in the dark
        k = 0.1 if t < 7.0 else 0.075 - 0.01 * seg(t, 7.0, 8.5)
        loc = hp + face_dir() * k + Vector((0, 0, 0.006))
        return loc, hp, 45 if t < 7.0 else 55, hp, 8.0
    if t < 10.0:                        # the switch, close: her hand comes in; long black fingers are already there
        sw = Vector((SWX - 0.002, WY - 0.008, SWZ))
        return Vector((SWX + 0.012, WY - 0.075, SWZ + 0.012)), sw, 55, sw, 6.0
    if t < 10.9:                        # light: from the room, it towers right beside her, bent over her
        tg = Vector((SWX + 0.008, WY - 0.025, 0.11))
        return Vector((SWX - 0.025, WY - 0.2, 0.1)), tg, 38, tg, 5.0
    loc = hp + face_dir() * 0.075 + Vector((0, 0, 0.004))   # she turns her head to it: her face
    return loc, hp, 45, hp, 8.0


# ------------------------------------------------------------------ animate
shade_em = SHADE.node_tree.nodes['Emission'].inputs[1]
fix_em = FIXTURE.node_tree.nodes['Emission'].inputs[1]
boil = Boil(5, amp=0.00012, rot=0.003)
chat = random.Random(9)


def show(obs, on, f):
    for o in obs:
        o.scale = (1, 1, 1) if on else (1e-4,) * 3; key(o, f, scale=tuple(o.scale))


for f in range(1, F + 1):
    t = (f - 1) / FPS
    W = aim_arm(base_pose(t), t)
    h.root.location = (ROOT.x, ROOT.y, 0.0); h.root.rotation_euler = (0, 0, YAW)
    MC.apply(h, W, YAW)
    for pv in ('chest', 'neck', 'head'):
        e = h.P[pv]; a = 0.006 + (0.02 if 7.0 <= t < 8.5 or t >= 10.0 else 0.0)
        e.rotation_euler = (e.rotation_euler.x + chat.uniform(-a, a), e.rotation_euler.y, e.rotation_euler.z + chat.uniform(-a, a))
    settle(SUPPORTS)
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, YAW + je.z)
    n, bl_, gz = face(t); h.expr(n, blink=bl_, gaze=gz); h.key(f)

    on = lit(t)
    toggle.rotation_euler = (math.radians(14 if on else -14), 0, 0); key(toggle, f, rot=tuple(toggle.rotation_euler))
    ceil_l.data.energy = (2.5 if on else 0.0); ceil_l.data.keyframe_insert('energy', frame=f)
    fix_em.default_value = 4.0 if on else 0.0; fix_em.keyframe_insert('default_value', frame=f)
    lamp.data.energy = 0.5 if on else 0.0; lamp.data.keyframe_insert('energy', frame=f)
    shade_em.default_value = 3.0 if on else 0.02; shade_em.keyframe_insert('default_value', frame=f)
    key_l.data.energy = KEY_E * (0.9 if on else 0.35); key_l.data.keyframe_insert('energy', frame=f)
    fill_h.data.energy = 0.0 if on else (1.4 if 8.5 <= t < 10.0 else 0.35); fill_h.data.keyframe_insert('energy', frame=f)

    show([fig_corner] + fe_corner, t < 2.4, f)
    show([fig_ceiling] + fe_ceiling, 3.9 <= t < 5.4, f)
    show(dent_parts, t >= 5.4, f)
    show([fig_side] + fe_side, t >= 8.4, f)

    bpy.context.view_layer.update()
    hp = head_pt()
    loc, tgt, lens, fp, fs = shot(t, hp)
    cam.location = loc; look_at(cam, tgt); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.focus_distance = (loc - fp).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    cam.data.dof.aperture_fstop = fs; cam.data.dof.keyframe_insert('aperture_fstop', frame=f)

constant_interp()
run(sc, OPTS)
