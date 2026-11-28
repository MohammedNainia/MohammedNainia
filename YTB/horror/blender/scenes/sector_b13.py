"""Haru #8 "Sector B13 · File 01" (narrated, about 47 s; script: YTB/horror/sector_b13/script.txt).

The picture runs 0..44 s (528 frames at 12 fps). The black FILE 01 card (44..46.5) and the cut back to frame 0 are
added in post. The timings below follow the script; once the voices are recorded, replace T with the time map built
from the real lines (every shot reads its start and end from T, so nothing else needs to change).

Cast: Haru (the new Tripo Haru, rigged by cast_kit.haru; poses in puppets/haru_poses.py), Mika and Jun (the cast kit: puppets/cast_kit.py), two B13
handlers and the creature (puppets/cast_camp.py). Set: the woods kit (library/sets/outside/woods.py).
blender -b -P scenes/sector_b13.py -- [--still F | --stills a,b | --range A B] [--res 1080 1920] [--samples 64] [--out DIR]
"""
import bpy, os, sys, math, random
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, os.path.join(SETS, 'outside')); sys.path.insert(0, SETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
sys.path.insert(0, os.path.join(HERE, '..', 'haru'))
import kit as K
import woods as W
import haru_clay as HC
import cast_camp as CC
import cast_kit as CK
import haru_poses as HPZ
import haru_face as HF
import importlib.util
spec = importlib.util.spec_from_file_location('poses', os.path.join(HERE, '..', 'haru', 'test2_shot.py'))
PO = importlib.util.module_from_spec(spec); spec.loader.exec_module(PO)
from claylib import cli, run, camera, look_at, key, constant_interp, area_light, point_light, Boil

FPS = 12
# ------------------------------------------------------------------ the time map (seconds): shot -> (start, end)
T = dict(
    face=(0.0, 4.0),        # ECU: Haru in her tent, torch under her face, breathing             n1
    fire=(4.0, 9.0),        # flashback: the three of them at the campfire, laughing             n2
    fence=(9.0, 15.0),      # dusk: the sign close, then back to the open gate and the kids      n3
    tents=(15.0, 18.0),     # night: three tents, the fire down to embers (screams in post)      n4
    wake=(18.0, 20.0),      # Haru asleep in the tent: her eyes snap open
    shadow=(20.0, 23.5),    # inside: a tall shadow passes along the wall, fingers drag on it
    voice=(23.5, 27.5),     # CU Haru: "Haru? It's okay..." outside (Mika's voice)
    zip=(27.5, 30.0),       # low: the zip opens by itself, grey fingertips in the gap            n5
    mouth=(30.0, 32.0),     # CU: both hands over her mouth
    withdraw=(32.0, 35.0),  # the fingers slide back out, hold on the gap                         n6
    dawn=(35.0, 41.0),      # dawn through the gap: handlers walk it back toward the fence       n7
    turn=(41.0, 43.0),      # behind the fence it stops and turns its head to her tent  "Bye, Haru."
    gate=(43.0, 44.0),      # the gate closes, a handler locks it
)
END = 44.0
F = int(END * FPS)


def fr(t): return int(round(t * FPS)) + 1
def shot_at(t): return next((k for k, (a, b) in T.items() if a <= t < b), 'gate')
def u_in(t, name): a, b = T[name]; return max(0.0, min(1.0, (t - a) / (b - a)))
def ez(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


OPTS = cli('sector_b13')
sc = K.begin('sector_b13', res=OPTS['res'], samples=OPTS['samples'], frames=F)
sc.render.fps = FPS

# ------------------------------------------------------------------ the set
W.materials(); W.ground(); W.trees()
fire = W.Campfire(0, 0)
SEAT_R, SEAT_TOP = 0.1, 0.034
SEATS = {'haru': 200, 'mika': 330, 'jun': 75}                     # angle round the fire
for i, a in enumerate(SEATS.values()):
    W.logs_seat(math.cos(math.radians(a)) * SEAT_R, math.sin(math.radians(a)) * SEAT_R, a + 90, length=0.1,
                r_=SEAT_TOP / 2, name=f'seat_log_{i}')
t_haru = W.Tent('tent_haru', 0.0, -0.3, 180, 'green')
t_mika = W.Tent('tent_mika', -0.27, -0.17, 235, 'red')
t_jun = W.Tent('tent_jun', 0.27, -0.15, 125, 'blue')
fence = W.Fence(y=0.8)
torch = W.Torch(0, 0, 0)
W.mood('night')

# extra light rigs, keyed on and off per shot
moon, sky_fill = bpy.data.objects['moon'], bpy.data.objects['sky_fill']
dawn_low = area_light('dawn_low', (1.6, 0.4, 0.18), (0, 0.2, 0.05), 220.0, 0.6, (0.75, 0.82, 1.0)); K._to(dawn_low, 'Lights')
dawn_sky = area_light('dawn_sky', (0, 0, 1.5), (0, 0, 0), 40.0, 2.0, (0.6, 0.7, 0.95)); K._to(dawn_sky, 'Lights')
dusk_low = area_light('dusk_low', (-1.4, 1.6, 0.16), (0, 0.6, 0.06), 160.0, 0.8, (1.0, 0.6, 0.38)); K._to(dusk_low, 'Lights')
dusk_sky = area_light('dusk_sky', (0, 0, 1.5), (0, 0, 0), 18.0, 2.0, (0.75, 0.6, 0.7)); K._to(dusk_sky, 'Lights')
shadow_moon = area_light('shadow_moon', (-0.55, -0.3, 0.85), (0.0, -0.3, 0.08), 0.0, 0.04, (0.6, 0.72, 1.0))   # high: its shadow lands on the low wall; K._to(shadow_moon, 'Lights')
tent_fill = point_light('tent_fill', (0.0, -0.3, 0.09), 0.0, radius=0.02, color=(0.5, 0.62, 1.0)); K._to(tent_fill, 'Lights')
fire_key = area_light('fire_key', (0.0, 0.0, 0.05), (0, 0, 0.05), 0.0, 0.05, (1.0, 0.55, 0.25)); K._to(fire_key, 'Lights')
BG = sc.world.node_tree.nodes['Background']
MIST = next(n for n in bpy.data.materials['mist'].node_tree.nodes if n.type == 'MAP_RANGE')

LOOK = {   # world colour, strength, mist density, light energies
    'night': ((0.015, 0.02, 0.04), 0.25, 0.14, dict(moon=70, sky_fill=0.6)),
    'warm': ((0.012, 0.012, 0.025), 0.15, 0.06, dict(moon=25, sky_fill=0.2)),          # the flashback: the fire leads
    'dusk': ((0.30, 0.2, 0.22), 0.45, 0.1, dict(dusk_low=160, dusk_sky=18)),
    'dawn': ((0.32, 0.38, 0.5), 0.9, 0.42, dict(dawn_low=220, dawn_sky=40)),
}
RIGS = dict(moon=moon, sky_fill=sky_fill, dawn_low=dawn_low, dawn_sky=dawn_sky, dusk_low=dusk_low, dusk_sky=dusk_sky)
TOD = dict(face='night', fire='warm', fence='dusk', tents='night', wake='night', shadow='night', voice='night',
           zip='night', mouth='night', withdraw='night', dawn='dawn', turn='dawn', gate='dawn')
FIRE = dict(face=0.22, fire=1.0, fence=0.0, tents=0.3, wake=0.25, shadow=0.25, voice=0.22, zip=0.22, mouth=0.22,
            withdraw=0.2, dawn=0.0, turn=0.0, gate=0.0)


def light_shot(f, name):
    col, st, dens, en = LOOK[TOD[name]]
    BG.inputs[0].default_value = (*col, 1); BG.inputs[1].default_value = st
    BG.inputs[0].keyframe_insert('default_value', frame=f); BG.inputs[1].keyframe_insert('default_value', frame=f)
    MIST.inputs['To Min'].default_value = dens; MIST.inputs['To Max'].default_value = dens * 0.15
    MIST.inputs['To Min'].keyframe_insert('default_value', frame=f); MIST.inputs['To Max'].keyframe_insert('default_value', frame=f)
    for k, ob in RIGS.items():
        ob.data.energy = en.get(k, 0.0); ob.data.keyframe_insert('energy', frame=f)
    tent_fill.data.energy = 0.04 if name == 'wake' else 0.012 if name == 'shadow' else 0.0
    shadow_moon.data.energy = 120.0 if name == 'shadow' else 0.0
    fire_key.data.energy = 1.2 if name == 'fire' else 0.0
    for ob in (tent_fill, shadow_moon, fire_key): ob.data.keyframe_insert('energy', frame=f)


fire.burn(1, F, level=lambda f: FIRE[shot_at((f - 1) / FPS)])

# ------------------------------------------------------------------ the cast
AWAY = Vector((40, 40, 0))                                          # off the set, for shots a puppet isn't in


def facing(frm, to):
    d = Vector(to) - Vector(frm); return math.atan2(d.x, -d.y)    # yaw that turns a puppet's -y toward `to`


def seat_pos(name):
    a = math.radians(SEATS[name]); return Vector((math.cos(a) * SEAT_R, math.sin(a) * SEAT_R, 0))


HARU = CK.haru((0, 0, 0), 'haru'); HRG = HARU['rig']
FACE = HF.Face(HARU, 'haru')                                         # dot eyes, replacement brows and mouths, tears, pallor
MIKA = CK.character('head_girl', 'body_child', CK.CHILD, 'child', (0, 0, 0), 'mika', hair_src='hair_mika',
                    outfit=('#3d8c86', '#2f3a4f', '#eceae6'))
JUN = CK.character('head_boy', 'body_child', CK.CHILD, 'child', (0, 0, 0), 'jun', hair_src='hair_jun',
                   outfit=('#5a6d3a', '#9a8a6c', '#3a332c'))
ha = CC.Handler(name='handler_a', loc=tuple(AWAY), yaw=0); hb = CC.Handler(name='handler_b', loc=tuple(AWAY), yaw=0)
cr = CC.Creature(loc=tuple(AWAY), yaw=0)
fingers = CC.fingers('zip_fingers')
pole_m = K.painted('pole_steel', (0.18, 0.18, 0.19), rough=0.4)
POLES = []
for i in range(2):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0012, depth=1.0, vertices=12); p = bpy.context.object
    p.name = f'catch_pole_{i}'; p.data.materials.append(pole_m); K._to(p); POLES.append(p)
# Mika's marshmallow on a stick, burning
stick = K.block('marsh_stick', -0.0006, 0.0006, -0.0006, 0.0006, 0.0, 0.06, K.painted('stick', (0.3, 0.2, 0.12)), bevel=0.0003)
marsh_m = bpy.data.materials.new('marsh_fire'); marsh_m.use_nodes = True
mb = marsh_m.node_tree.nodes['Principled BSDF']; mb.inputs['Base Color'].default_value = (0.08, 0.04, 0.02, 1)
mb.inputs['Emission Color'].default_value = (1.0, 0.45, 0.12, 1); mb.inputs['Emission Strength'].default_value = 25.0
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0028, segments=16, ring_count=8); marsh = bpy.context.object
marsh.name = 'marshmallow'; marsh.data.materials.append(marsh_m); K._to(marsh)
marsh_light = point_light('marsh_light', (0, 0, 0), 0.0, radius=0.002, color=(1.0, 0.5, 0.2)); K._to(marsh_light, 'Lights')

# ------------------------------------------------------------------ Haru's poses (haru_poses names + extra world turns)
H_IN = t_haru.inside(0.0, 0.015, 0.0)                              # where she sits in her tent (facing the door, +y)
DOOR_IN = t_haru.door_point(0.03)


def haru_state(t):
    """(where, yaw, pose, floor, expression, torch) for this moment"""
    s = shot_at(t)
    breath = 3.5 * math.sin(2 * math.pi * 1.7 * t)                  # fast, shaky breathing (chest heaves)
    if s == 'fire':
        p = seat_pos('haru'); bounce = -4 * abs(math.sin(t * 9)) * (1 if (t % 1.6) < 0.9 else 0)   # laughing
        return p, facing(p, (0, 0, 0)), 'sit', {('chest', 'X'): bounce, ('head', 'X'): 6 + bounce}, 0.0
    if s == 'fence':
        return Vector((0.0, 0.6, 0)), math.pi, 'point', {('head', 'X'): -8}, 0.0
    if s in ('tents', 'wake'):
        lift = {('head', 'Z'): 25} if t >= T['wake'][0] + 0.7 else {}      # she wakes: her head snaps toward the wall
        return H_IN + Vector((-0.065, 0, 0)), -math.pi / 2, 'lie', lift, 0.013        # head toward +x, all of her inside
    if s == 'mouth' or (s == 'withdraw' and t < T['withdraw'][0] + 1.5):
        return H_IN, math.pi, 'mouth', {('chest', 'X'): breath * 0.4}, 0.0012
    if s in ('dawn', 'turn', 'gate'):
        return H_IN, math.pi, 'hug', {}, 0.0012
    return H_IN, math.pi, 'hug', {('chest', 'X'): breath, ('head', 'X'): -breath * 0.5}, 0.0012


def face_for(t):
    """(expression, look, blink, tears, pale) for this moment: the sheet's faces, timed to the story"""
    s = shot_at(t); bl = 1.0 if (t % 2.6) < 0.17 else 0.0          # a blink every 2.6 s, two frames long
    jit = (0.12 * math.sin(t * 7.3), 0.08 * math.sin(t * 5.1))      # eyes darting while she listens
    if s == 'face': return 'scared', jit, bl, 0.0, 0.35
    if s == 'fire': return ('laugh' if (t % 1.6) < 0.9 else 'happy'), (0, 0), 0.0, 0.0, 0.0
    if s == 'fence': return 'uncomfortable', (0.1, 0.35), bl, 0.0, 0.0
    if s == 'tents' or (s == 'wake' and t < T['wake'][0] + 0.7): return 'sleep', (0, 0), 0.0, 0.0, 0.0
    if s == 'wake': return 'stare', (0.7, 0.05), 0.0, 0.0, 0.25          # eyes snap open, cut to the wall
    if s == 'shadow': return 'scared', (0.65, 0.1), 0.0, 0.0, 0.4
    if s == 'voice':
        u = u_in(t, 'voice')
        return ('terrified' if u < 0.45 else 'crying'), jit, 0.0, max(0.0, (u - 0.3) / 0.7), 0.5
    if s in ('zip', 'mouth'): return 'muffled', (0.0, -0.35), bl, 1.0, 0.55     # crying without a sound
    if s == 'withdraw': return 'worried', (0.0, -0.3), 0.0, 0.8, 0.6
    return 'sad', (0.0, 0.0), bl, 0.5, 0.45


def place_kid(c, f, where, yaw, sitting):
    rg = c['rig']; rg.location = where; rg.rotation_euler = (0, 0, yaw)
    rg.keyframe_insert('location', frame=f); rg.keyframe_insert('rotation_euler', frame=f)
    hipz = CK.JOINTS['hip'] * max(v.co.z for v in c['body'].data.vertices)
    if sitting:
        CK.pose(rg, f, **{'thigh.L': (-85, 0, 0), 'thigh.R': (-85, 0, 0), 'shin.L': (85, 0, 0), 'shin.R': (85, 0, 0),
                          'root_loc': (0, 0, -(hipz - SEAT_TOP))})
    else:
        CK.pose(rg, f, **{'thigh.L': (0, 0, 0), 'thigh.R': (0, 0, 0), 'shin.L': (0, 0, 0), 'shin.R': (0, 0, 0),
                          'root_loc': (0, 0, 0)})


for c in (MIKA, JUN): CK.relax(c['rig'], f=1)
# Mika holds her stick out to the fire: right arm forward and up
CK.turn(MIKA['rig'], 'upper_arm.R', 'X', -55, 1)

# ------------------------------------------------------------------ the camera
cam = camera((0, -1, 0.1), (0, 0, 0.05), lens=40, fstop=8.0); cam.data.clip_start = 0.0008
cam.data.dof.use_dof = True
rake = HC.ClayRake(energy=0.12, color=(0.85, 0.9, 1.0))
boil = Boil(5, amp=0.0001, rot=0.003)


def head_pt():
    b = HRG.pose.bones['head']; return HRG.matrix_world @ (b.head.lerp(b.tail, 0.45) + Vector((0, -0.006, 0)))


def cam_for(t, hp):
    """camera (loc, target, lens, fstop) for this moment"""
    s = shot_at(t)
    fwd = Vector((math.sin(HRG.rotation_euler.z), -math.cos(HRG.rotation_euler.z), 0))       # her forward
    if s in ('face', 'voice', 'mouth') or (s == 'withdraw' and t >= T['withdraw'][0] + 1.5):
        push = ez(u_in(t, s)) * 0.008
        return hp + fwd * (0.048 - push) + Vector((0.004, 0, 0.0)), hp + fwd * 0.011 + Vector((0, 0, -0.007)), 30, 11.0   # focus on her face, not the middle of her head; the tent is only 7 cm deep in front of her
    if s == 'fire':
        u = ez(u_in(t, 'fire')); a = math.radians(150)                  # from the trail side: Mika faces us, Haru in profile
        r = 0.3 - 0.05 * u
        return Vector((math.cos(a) * r, math.sin(a) * r, 0.1 - 0.02 * u)), Vector((0, 0.01, 0.028)), 30, 11.0
    if s == 'fence':
        u = ez((t - T['fence'][0] - 2.0) / 3.5)
        a, b = fence.sign_at + Vector((0, -0.12, 0.0)), Vector((0.03, 0.3, 0.1))
        ta, tb = fence.sign_at, Vector((0.0, 0.78, 0.09))
        return a.lerp(b, u), ta.lerp(tb, u), 50 - 18 * u, 11.0
    if s == 'tents':
        return Vector((0.12, 0.3, 0.09)), Vector((0.0, -0.22, 0.04)), 26, 11.0
    if s == 'wake':
        return hp + Vector((-0.075, 0.0, 0.07)), hp + Vector((-0.015, 0, 0)), 35, 8.0     # from her feet: her face upright
    if s == 'shadow':
        return t_haru.inside(-0.07, 0.035, 0.035), t_haru.inside(0.08, -0.02, 0.085), 18, 8.0
    if s in ('zip', 'withdraw'):
        return t_haru.door_point(0.02, -0.065), t_haru.door_point(0.025), 30, 8.0
    if s == 'dawn':
        return t_haru.door_point(0.04, 0.008), Vector((0.12, 0.55, 0.1)), 24, 11.0
    return t_haru.door_point(0.05, 0.004), Vector((0.0, 0.86, 0.2)), 70, 11.0        # turn, gate: long lens on the gate


# ------------------------------------------------------------------ the dawn walk (handlers lead it back)
WALK_A, WALK_B = Vector((0.36, -0.02, 0)), Vector((0.0, 0.9, 0))   # through the gate to the woods side
GATE_STOP = Vector((0.09, 0.73, 0))                                 # handler B stops at the gate to close it


def dawn_walk(t, f):
    s = shot_at(t)
    if s not in ('dawn', 'turn', 'gate', 'shadow'):
        cr.root.location = AWAY; cr.rest_pose(); cr.key(f)
        for p in (ha, hb): p.place(AWAY, 0); p.pose({}); p.key(f)
        for p in POLES: p.location = AWAY; p.keyframe_insert('location', frame=f)
        return
    if s == 'shadow':                                                # it passes along the west wall of her tent
        u = u_in(t, 'shadow'); cr.rest_pose()
        if u < 0.4:                                                  # it walks up the side of her tent
            pos = Vector((-0.2, -0.6 + 0.3 * ez(u / 0.4), 0)); bob = cr.walk(t, speed=0.5, hunch=16); yaw = math.pi
        else:                                                        # stops, turns to the tent, leans over the dome
            k = ez((u - 0.4) / 0.25); pos = Vector((-0.2, -0.3, 0)); bob = 0.0; yaw = math.pi + (math.pi / 2 - math.pi) * k
            cr.P['chest'].rotation_euler = (math.radians(12 + 38 * k), 0, 0); cr.look(0, 25 * k)
            drag = 0.15 * math.sin((u - 0.65) * 9) if u > 0.65 else 0.0      # its fingers drag across the nylon
            cr.reach(-1, 0.9 * k, up=-10 + 30 * drag); cr.reach(1, 0.6 * k, up=-25)
        cr.root.location = pos + Vector((0, 0, bob)); cr.root.rotation_euler = (0, 0, yaw)
        cr.key(f)
        for p in (ha, hb): p.place(AWAY, 0); p.pose({}); p.key(f)
        for p in POLES: p.location = AWAY; p.keyframe_insert('location', frame=f)
        return
    u = ez((t - T['dawn'][0]) / (T['turn'][0] - T['dawn'][0]))
    pos = WALK_A.lerp(WALK_B, u); d = WALK_B - WALK_A; yaw = math.atan2(d.x, -d.y)
    walking = u < 1.0
    cr.rest_pose(); bob = cr.walk(t, speed=0.45, hunch=14) if walking else 0.0
    if not walking:                                                  # behind the fence: it stops, turns to her tent
        k = ez((t - T['turn'][0]) / 0.8)
        cr.look(-70 * k, 6 * k, 8 * k)
    cr.root.location = pos + Vector((0, 0, bob)); cr.root.rotation_euler = (0, 0, yaw); cr.key(f)
    side = Vector((math.cos(yaw), math.sin(yaw), 0))                 # its right-left axis
    back = Vector((-math.sin(yaw), math.cos(yaw), 0))                # behind it
    pa = pos + side * 0.085 + back * 0.03
    pb_walk = pos - side * 0.085 + back * 0.03
    pb = pb_walk if pos.y < GATE_STOP.y - 0.02 else GATE_STOP
    for hd, p, wk in ((ha, pa, walking), (hb, pb, pos.y < GATE_STOP.y - 0.02)):
        ph = (t * 0.9) % 1.0
        hd.pose(PO.add(PO.walk(ph) if wk else {}, {('upper_arm.L', 'x'): -50, ('upper_arm.R', 'x'): -50,
                                                   ('forearm.L', 'x'): -30, ('forearm.R', 'x'): -30}))
        hd.place(p, yaw); hd.ground(0.0)
    if s == 'gate':                                                  # handler B swings the gate shut and locks it
        hb.place(GATE_STOP, math.pi); hb.pose({('upper_arm.R', 'x'): -70, ('upper_arm.L', 'x'): -40}); hb.ground(0.0)
    for hd in (ha, hb): hd.key(f)
    bpy.context.view_layer.update()
    collar = cr.P['neck'].matrix_world @ Vector((0, -0.014, 0.0))
    for hd, pole in zip((ha, hb), POLES):
        hand = hd.P['hand.R'].matrix_world.translation
        if s == 'gate' and hd is hb:
            pole.location = AWAY; pole.keyframe_insert('location', frame=f); continue
        d = collar - hand
        pole.location = (hand + collar) / 2; pole.scale = (1, 1, d.length)
        pole.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        for a in ('location', 'scale', 'rotation_euler'): pole.keyframe_insert(a, frame=f)


# ------------------------------------------------------------------ animate
last = None
for f in range(1, F + 1):
    t = (f - 1) / FPS; s = shot_at(t)
    new_shot = s != last; last = s
    if new_shot: light_shot(f, s)

    # Haru
    p, yaw, pname, extra, lift = haru_state(t)
    j, je = boil.v(), boil.e()
    HRG.location = Vector(p) + Vector((0, 0, lift)) + j; HRG.rotation_euler = (je.x, je.y, yaw + je.z)
    HPZ.apply(HARU, pname, f=None, seat=SEAT_TOP, extra=extra)
    HPZ.key(HRG, f)
    FACE.set(f, *face_for(t), t=t)

    # Mika and Jun: at the fire, at the fence, otherwise away
    if new_shot:
        for c, nm in ((MIKA, 'mika'), (JUN, 'jun')):
            if s == 'fire':
                sp = seat_pos(nm); place_kid(c, f, sp, facing(sp, (0, 0, 0)), True)
            elif s == 'fence':
                sp = Vector((-0.075, 0.62, 0)) if nm == 'mika' else Vector((0.08, 0.58, 0)); place_kid(c, f, sp, math.pi, False)
            else:
                place_kid(c, f, AWAY, 0, False)
    if s == 'fire':                                                   # they laugh: chests bob, heads tip back
        for c, ph in ((MIKA, 0.0), (JUN, 1.3)):
            lv = 1 if ((t + ph) % 1.8) < 1.0 else 0
            CK.pose(c['rig'], f, chest=(-4 * lv * abs(math.sin(t * 10 + ph)), 0, 0), head=(-8 * lv, 0, 0))

    # the stick and its burning marshmallow
    bpy.context.view_layer.update()
    if s == 'fire':
        hand = MIKA['rig'].matrix_world @ MIKA['rig'].pose.bones['hand.R'].tail
        tip = hand.lerp(Vector((0, 0, 0.035)), 0.75)
        d = tip - hand; stick.location = hand; stick.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        stick.scale = (1, 1, d.length / 0.06); marsh.location = tip; marsh_light.location = tip
        marsh_light.data.energy = 0.05 * (0.8 + 0.4 * random.random())
    else:
        stick.location = AWAY; marsh.location = AWAY; marsh_light.data.energy = 0.0
    for o in (stick, marsh): o.keyframe_insert('location', frame=f)
    stick.keyframe_insert('rotation_euler', frame=f); stick.keyframe_insert('scale', frame=f)
    marsh_light.keyframe_insert('location', frame=f); marsh_light.data.keyframe_insert('energy', frame=f)

    # the torch: in her lap pointing up at her face, at the fence pointing at the sign, off while she sleeps
    hp = head_pt()
    if s == 'fence':
        hand = HRG.matrix_world @ HRG.pose.bones['hand.R'].head
        torch.h.location = hand; torch.h.rotation_euler = (0, 0, 0)
        d = (fence.sign_at - hand).normalized(); torch.h.rotation_euler = (-d).to_track_quat('Y', 'Z').to_euler()
        torch.level(f, 1.0)
    elif s in ('face', 'voice', 'zip', 'mouth', 'withdraw', 'dawn', 'turn', 'gate'):
        lap = HRG.matrix_world @ Vector((0, -0.034, 0.058))             # under her chin, in front of her knees
        torch.h.location = lap; d = (hp - lap).normalized()
        torch.h.rotation_euler = (-d).to_track_quat('Y', 'Z').to_euler()
        torch.level(f, 0.7 if s not in ('dawn', 'turn', 'gate') else 0.0)
    else:
        torch.h.location = AWAY; torch.level(f, 0.0)
    torch.h.keyframe_insert('location', frame=f); torch.h.keyframe_insert('rotation_euler', frame=f)

    # the zip and the fingers
    zu = 0.0
    if s == 'zip': zu = 0.5 * ez(u_in(t, 'zip'))
    elif s in ('mouth', 'withdraw', 'dawn', 'turn', 'gate'): zu = 0.5
    t_haru.zip(f, zu)
    if s in ('zip', 'mouth') or (s == 'withdraw' and t < T['withdraw'][0] + 1.2):
        out = 0.0 if s != 'withdraw' else 0.03 * ez((t - T['withdraw'][0]) / 1.2)
        reach = 0.012 * ez(u_in(t, 'zip')) if s == 'zip' else 0.012
        fingers.location = t_haru.door_point(0.012, 0.012 + out - reach)
        fingers.rotation_euler = (math.radians(-90), 0, math.radians(180))
    else:
        fingers.location = AWAY
    fingers.keyframe_insert('location', frame=f); fingers.keyframe_insert('rotation_euler', frame=f)

    # the gate: open until the end, shut and locked in the last second
    fence.gate(f, 35 if s != 'gate' else 35 * (1 - ez(u_in(t, 'gate') / 0.6)))

    # handlers and the creature
    dawn_walk(t, f)

    # camera
    bpy.context.view_layer.update(); hp = head_pt()
    loc, tg, lens, fstop = cam_for(t, hp)
    cam.location = loc; look_at(cam, Vector(tg))
    key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.focus_distance = (Vector(loc) - Vector(tg)).length; cam.data.dof.aperture_fstop = fstop
    cam.data.dof.keyframe_insert('focus_distance', frame=f); cam.data.dof.keyframe_insert('aperture_fstop', frame=f)
    close = s in ('face', 'voice', 'mouth', 'wake', 'fire') or (s == 'withdraw' and t >= T['withdraw'][0] + 1.5)
    src = torch.src() if s != 'fire' else Vector((0, 0, 0.03))
    rake.aim(f, hp, cam.location, src, on=close)

constant_interp()
if os.environ.get('B13_DEBUGCAM'):                                   # look-dev: a fixed camera from outside, x,y,z,tx,ty,tz
    v = [float(x) for x in os.environ['B13_DEBUGCAM'].split(',')]
    cam.animation_data_clear(); cam.data.animation_data_clear()
    cam.location = v[:3]; look_at(cam, Vector(v[3:])); cam.data.lens = 24; cam.data.dof.use_dof = False
run(sc, OPTS)
