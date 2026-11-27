
# ------------------------------------------------------------------ Haru #7 "Don't Open Your Door": the story
# (dont_open.py = the first 235 lines of lights_off.py, the bedroom and the puppet, + this file)
import mocap as MC
sys.path.insert(0, os.path.join(HERE, '..', 'library', 'sets'))
import kit as KT
KT.materials()
for cname in ('Set', 'Lights', 'Marks'):                             # the kits file their pieces here
    if cname not in bpy.data.collections:
        c_ = bpy.data.collections.new(cname); sc.collection.children.link(c_)
import openings as OP
import practicals as PL
LIB = MC.Library(os.path.join(HERE, '..', 'mocap', 'clips.npz'), h)
END = 18.0                      # no black tail in the render: the last half second goes black in post, then the loop
F = int(END * FPS); sc.frame_end = F
SCREENS = os.path.join(HERE, '..', '..', 'dont_open')


def ezs(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


def turn2(v, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)); return Vector((c * v.x - s * v.y, s * v.x + c * v.y))


# ------------------------------------------------------------------ the room tonight: no chair, lamp off, the old door out
for o in list(bpy.data.objects):
    if o.name.split('.')[0] in ('seat', 'chair_leg', 'chair_post', 'chair_rail', 'chair_rail2', 'door', 'door_panel', 'knob',
                                'void', 'hall_l', 'hall_r', 'hall_top', 'void_eye', 'hall'):
        bpy.data.objects.remove(o, do_unlink=True)
lamp.data.energy = 0.0
SHADE.node_tree.nodes['Emission'].inputs[1].default_value = 0.0
key_l.data.energy = 0.3                                              # her face is lit by the phone, not by a front key
pv.inputs['Density'].default_value = 0.35
CEIL_Z = 0.25
box('ceiling', WX0 - 0.01, WX1, -0.45, WY + 0.005, CEIL_Z, CEIL_Z + 0.01, painted('ceiling', (0.2, 0.2, 0.19)), bevel=0.0005)
box('wall_right', 0.30, 0.31, -0.45, WY + 0.09, 0, CEIL_Z, WALL, bevel=0.0005)   # closes the room: no hall light round the end of the wall

# the working door (openings.py) in the old doorway, the hallway behind it lit, so a line of light shows under the door
d0, d1, dh = DOOR
door_h = empty('door_wall', (0, WY, 0))
D = OP.Door(door_h, d0, d1, h=dh, side=-1, hinge='end', color='white', beyond='lit', spill=(1.4, (1.0, 0.64, 0.34)),
            frame=False, undercut=0.0045)
DOOR_MOON = area_light('door_moon', (0.02, -0.12, 0.2), ((d0 + d1) / 2, WY, 0.08), 0.3, 0.15, (0.55, 0.68, 1.0))   # faint cold light on the door so it reads
HALL_LOW = point_light('hall_low', ((d0 + d1) / 2, WY + 0.038, 0.005), 0.8, radius=0.006, color=(1.0, 0.64, 0.34))

# whoever is outside: tall, dark, never seen; only its feet in the light under the door and darkness in the gap
VOIDM = emissive('outside_void', (0, 0, 0), 0.0)
who = empty('who', ((d0 + d1) / 2 + 0.004, WY + 0.026, 0.0))
bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.2, location=(0, 0, 0)); body = bpy.context.object
body.scale = (1.15, 0.6, 1); body.data.materials.append(VOIDM)
body.parent = who; body.location = (0, 0, 0.1 + 0.012)
for sx in (-1, 1):                                                   # two feet, flat on the hall floor
    ft = box('who_foot', -0.006, 0.006, -0.011, 0.004, 0.0, 0.009, VOIDM, bevel=0.002); ft.parent = who; ft.location = (sx * 0.009, -0.006, 0.0045)
    lg = box('who_leg', -0.004, 0.004, -0.004, 0.004, 0.006, 0.02, VOIDM, bevel=0.001); lg.parent = who; lg.location = (sx * 0.009, 0, 0.013)

# ------------------------------------------------------------------ the phone in her hands, with the chat on its screen
ph = PL.Phone(0, 0, 0.05, energy=0.004)
scr = [o for o in ph.h.children if o.name.startswith('phone_screen')][0]
m = bpy.data.materials.new('phone_chat'); m.use_nodes = True; N, Lk = m.node_tree.nodes, m.node_tree.links
pb = N['Principled BSDF']; pb.inputs['Base Color'].default_value = (0.005, 0.005, 0.006, 1); pb.inputs['Roughness'].default_value = 0.2
tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping')
mp.inputs['Scale'].default_value = (1 / 0.0062, 1 / 0.0136, 1); mp.inputs['Location'].default_value = (0.5, 0.5, 0)
Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
ims = []
for nm in ('msg1.png', 'msg2.png'):
    it = N.new('ShaderNodeTexImage'); it.image = bpy.data.images.load(os.path.join(SCREENS, nm)); it.extension = 'CLIP'
    Lk.new(mp.outputs['Vector'], it.inputs['Vector']); ims.append(it)
mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'
Lk.new(ims[0].outputs['Color'], mix.inputs[6]); Lk.new(ims[1].outputs['Color'], mix.inputs[7])
Lk.new(mix.outputs[2], pb.inputs['Emission Color'])
MSG = mix.inputs[0]; GLOW = pb.inputs['Emission Strength']; GLOW.default_value = 2.2
scr.data.materials.clear(); scr.data.materials.append(m)
PH_LIGHT = ph.lights[0][0]

# ------------------------------------------------------------------ Haru: sitting up in bed, the phone in both hands
P_LIE = Vector((-0.183, 0.12))
SEG = dict(t0=0.0, t1=END, clip='getup_from_back', c0=4.22, c1=4.3, yaw=90, at=P_LIE, mirror=False, loop=False)
SEG['start'] = Vector(SEG['at'])
DOOR_C = Vector(((d0 + d1) / 2, WY, 0.07))


def perf(t):
    u = min(1.0, t / END); c = SEG['c0'] + (SEG['c1'] - SEG['c0']) * u
    W, hp = LIB.sample(SEG['clip'], c, False, False)
    d = hp - LIB.hips(SEG['clip'], SEG['c0'], False, False)
    return MC.rotate(W, math.radians(SEG['yaw'])), SEG['start'] + turn2(Vector((d.x, d.y)) * LIB.k, SEG['yaw'])


ARM = {}
for sd in ('L', 'R'):
    ra, rf, rh = h.rest['upper_arm.' + sd], h.rest['forearm.' + sd], h.rest['hand.' + sd]
    ARM[sd] = ((rf - ra), (rh - rf))
POLE = {'L': Vector((0, 0.4, -1)), 'R': Vector((0, -0.4, -1))}      # elbows out and down (she faces +x: her left is +y)


def aim_arms(W, yaw, targets, w=1.0):
    MC.apply(h, W, yaw); bpy.context.view_layer.update()
    W = dict(W)
    for sd, T_ in targets.items():
        D_UP, D_FO = ARM[sd]; L_A, L_B = D_UP.length, D_FO.length
        S_ = h.P['upper_arm.' + sd].matrix_world.translation.copy()
        d = T_ - S_; dl = min(d.length, (L_A + L_B) * 0.999); u = d.normalized()
        ca = (L_A ** 2 + dl ** 2 - L_B ** 2) / (2 * L_A * dl); al = math.acos(max(-1, min(1, ca)))
        pole = POLE[sd]; v = (pole - u * pole.dot(u)).normalized()
        E = S_ + (u * math.cos(al) + v * math.sin(al)) * L_A; T2 = S_ + u * dl
        q_up = D_UP.normalized().rotation_difference((E - S_).normalized())
        q_fo = D_FO.normalized().rotation_difference((T2 - E).normalized())
        for pvn, q in (('upper_arm.' + sd, q_up), ('forearm.' + sd, q_fo), ('hand.' + sd, q_fo)):
            a = W[pvn]; b = q if a.dot(q) >= 0 else -q
            W[pvn] = a.slerp(b, w)
    return W


def looking_at_phone(t): return t < 3.4 or 12.0 <= t < 14.0


def face(t):
    if t < 7.0: n = 'worried'
    elif t < 16.5: n = 'scared'
    else: n = 'terrified'
    blink = any(abs(t - b) < 0.09 for b in (1.6, 5.8, 13.1))
    gaze = (0, 22) if looking_at_phone(t) else (14, -4)                  # down at the screen / across at the door
    return n, blink, gaze


# ------------------------------------------------------------------ beats
T_FEET, T_HANDLE, T_HANDLE1, T_OPEN, T_OPEN1, T_DARK = 7.0, 10.2, 11.4, 14.0, 15.4, 16.5


def phone_on(t): return t < T_DARK


# ------------------------------------------------------------------ cameras
cam = camera((0, -0.3, 0.09), (0, 0, 0.06), lens=30, fstop=8.0)
cam.data.clip_start = 0.001
rake = HC.ClayRake(energy=0.05, color=(0.75, 0.85, 1.0))           # the clay key, from the phone


def head_pt(): return h.P['head'].matrix_world @ Vector((0, -0.012, 0.009))
def face_dir(): return (h.P['head'].matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def shot(t, hp, php, phn, left):
    if t < 2.5 or 12.0 <= t < 14.0:      # the phone, close, the chat readable (frame 0)
        loc = php + phn * 0.03 + Vector((0, 0, 0.004))                  # between her face and the screen, centred: her hair hangs either side
        return loc, php, 40, php, 11.0
    if t < 4.5 or 9.0 <= t < 10.0 or t >= T_DARK:   # her face, lit by the phone from below
        fw = turn2(Vector((1, 0)), 28)                                  # from her front, a little toward the door side
        loc = hp + Vector((fw.x, fw.y, 0)) * 0.085 + Vector((0, 0, -0.002))
        return loc, hp, 45, hp, 8.0
    if t < 10.0:                          # what she sees: the door across the dark room, the light under it
        u = seg(t, 4.5, 9.0)
        loc = hp + Vector((0.006 + 0.03 * u, -0.004, 0.004))
        return loc, DOOR_C + Vector((0, 0, -0.03)), 46 + 16 * u, DOOR_C, 8.0
    if t < 12.0:                          # the handle, close
        hd = D.handles[1][0].matrix_world.translation if D.handles[1][1] < 0 else D.handles[0][0].matrix_world.translation
        return hd + Vector((-0.05, -0.055, 0.012)), hd, 50, hd, 8.0
    loc = Vector((-0.3, 0.02, 0.19))  # behind her in bed: the door opens, light across the floor
    return loc, DOOR_C + Vector((-0.06, -0.02, -0.03)), 24, DOOR_C, 8.0


POV_HIDE = [o for o in h.coll.all_objects if o.type == 'MESH' and not any(k in o.name for k in ('hand', 'sleeve_lo', 'sleeve_up'))]

# ------------------------------------------------------------------ animate
boil = Boil(5, amp=0.00012, rot=0.003)
chat = random.Random(17)
for f in range(1, F + 1):
    t = (f - 1) / FPS
    W, xy = perf(t); yaw = math.radians(SEG['yaw'])
    h.root.location = (xy.x, xy.y, h.root.location.z); h.root.rotation_euler = (0, 0, yaw)
    MC.apply(h, W, yaw); settle(SUPPORTS); bpy.context.view_layer.update()
    ch = h.P['chest'].matrix_world.translation.copy(); hd0 = head_pt()
    fwd = Vector((math.sin(yaw), -math.cos(yaw), 0))
    php = ch + fwd * 0.036 + Vector((0, 0, -0.022)) + Vector((0, 0, 0.003)) * (1 if looking_at_phone(t) else 0)
    phn = (hd0 - php).normalized()
    ph.h.location = php; ph.h.rotation_euler = phn.to_track_quat('Z', 'Y').to_euler()
    ph.h.keyframe_insert('location', frame=f); ph.h.keyframe_insert('rotation_euler', frame=f)
    left = fwd.cross(Vector((0, 0, 1))) * -1                         # her left (+y when she faces +x)
    pup = ph.h.rotation_euler.to_matrix() @ Vector((0, 1, 0))         # up the phone: her hands hold its lower half
    W = aim_arms(W, yaw, {'L': php + left * 0.0062 - pup * 0.0045 - phn * 0.003, 'R': php - left * 0.0062 - pup * 0.0045 - phn * 0.003})
    MC.apply(h, W, yaw)
    look = looking_at_phone(t)
    hp_ = h.P['head']; nk = h.P['neck']
    pitch = math.radians(9 if look else 2); turn = math.radians(0 if look else 12)
    hp_.rotation_euler = (hp_.rotation_euler.x + pitch, hp_.rotation_euler.y, hp_.rotation_euler.z + turn)
    shrink = ezs((t - 9.0) / 0.6)                                     # she shrinks back against the headboard
    for pvn in ('chest', 'neck', 'head'):
        e = h.P[pvn]; a = 0.004 + (0.012 if t >= T_FEET else 0.0)
        e.rotation_euler = (e.rotation_euler.x + chat.uniform(-a, a), e.rotation_euler.y, e.rotation_euler.z + chat.uniform(-a, a))
    settle(SUPPORTS)
    j, je = boil.v(), boil.e()
    h.root.location += j + Vector((-0.006 * shrink, 0, 0)); h.root.rotation_euler = (je.x, je.y, yaw + je.z)
    n, bl_, gz = face(t); h.expr(n, blink=bl_, gaze=gz); h.key(f)

    # the phone: chat 1 until the second text arrives, then both; dark at the end
    MSG.default_value = 0.0 if t < 12.0 else 1.0; MSG.keyframe_insert('default_value', frame=f)
    on = phone_on(t)
    GLOW.default_value = 2.2 if on else 0.0; GLOW.keyframe_insert('default_value', frame=f)
    PH_LIGHT.data.energy = 0.004 if on else 0.0; PH_LIGHT.data.keyframe_insert('energy', frame=f)
    key_l.data.energy = 0.3 if on else 0.08; key_l.data.keyframe_insert('energy', frame=f)

    # outside the door: the feet arrive, the handle turns, the door opens a hand's width
    who.hide_render = t < T_FEET; who.keyframe_insert('hide_render', frame=f)
    for c_ in who.children: c_.hide_render = t < T_FEET; c_.keyframe_insert('hide_render', frame=f)
    D.turn(f, ezs((t - T_HANDLE) / (T_HANDLE1 - T_HANDLE)) * (1 - ezs((t - T_OPEN1) / 0.4)))
    D.swing(f, 14.0 * ezs((t - T_OPEN) / (T_OPEN1 - T_OPEN)))

    bpy.context.view_layer.update()
    hp = head_pt()
    loc, tgt, lens, fp, fs = shot(t, hp, php, phn, left)
    rake.aim(f, hp, loc, ph.src(), on=on and not (t < 2.5 or 12.0 <= t < 14.0))
    cam.location = loc; look_at(cam, tgt); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    insert = t < 2.5 or 12.0 <= t < 14.0
    cam.data.clip_start = 0.001
    for o in POV_HIDE:                                               # her POV on the phone: her own head is behind the camera
        o.hide_render = insert; o.keyframe_insert('hide_render', frame=f)
    cam.data.dof.focus_distance = (loc - fp).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    cam.data.dof.aperture_fstop = fs; cam.data.dof.keyframe_insert('aperture_fstop', frame=f)

constant_interp()
run(sc, OPTS)
