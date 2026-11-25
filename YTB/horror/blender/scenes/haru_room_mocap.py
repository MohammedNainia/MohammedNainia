"""Room test 3: Haru in her bedroom, moved by real motion capture (Mixamo clips, retargeted by puppets/mocap.py), cut
together like a horror beat and played as stop motion (12 poses a second, hand jitter, held frames). 32.5 s, 9:16.

She lies awake staring -> sits up -> swings round to the edge of the bed -> stands -> turns and creeps across the room ->
the door creaks: she cowers -> creeps on to the chair, turns, sits -> close-ups while she looks side to side -> the lamp
stutters, the door bangs open: she leaps out of the seat -> turns and runs -> jumps onto the bed and cowers facing the door
-> the lamp dies -> eyes in the doorway -> she turns her head to us.

Contact: settle() puts her on the floor, mattress or seat every frame (her body rests, hands and feet never prop her up);
the jump keeps its motion-capture height while she is in the air.
blender -b -P scenes/haru_room_mocap.py -- [--still F] [--range A B] [--res 1080 1920] [--samples 64] [--out DIR]
"""
import bpy, sys, os, math, random, importlib.util
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import haru_puppet as HP
import haru_burton as HB
import burton_materials as BM
from claylib import *
spec = importlib.util.spec_from_file_location('story', os.path.join(HERE, '..', 'haru', 'test2_shot.py'))
ST = importlib.util.module_from_spec(spec); spec.loader.exec_module(ST)
seg, mix, add = ST.seg, ST.mix, ST.add

OPTS = cli('haru_room')
FPS, END = 12, 26.5
F = int(END * FPS)
reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=F)
HP.fast_cycles(sc)
world((0.05, 0.06, 0.09), 0.25)
sc.view_settings.exposure = -0.2

# ------------------------------------------------------------------ materials
def nodes_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes['Principled BSDF']


def striped(name, c1, c2, scale, direction='X', rough=0.85, sharp=1.0, grain=0.0):
    """wallpaper stripes (direction X) or floor boards (direction Y), object space so they keep their size"""
    m, nt, b = nodes_mat(name); N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord')
    w = N.new('ShaderNodeTexWave'); w.bands_direction = direction; w.inputs['Scale'].default_value = scale
    w.inputs['Distortion'].default_value = 0.4; L.new(tc.outputs['Object'], w.inputs['Vector'])
    p = N.new('ShaderNodeMath'); p.operation = 'POWER'; L.new(w.outputs['Fac'], p.inputs[0]); p.inputs[1].default_value = sharp
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; L.new(p.outputs[0], mx.inputs[0])
    mx.inputs[6].default_value = c1 + (1,); mx.inputs[7].default_value = c2 + (1,)
    col = mx.outputs[2]
    if grain:
        nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900; L.new(tc.outputs['Object'], nz.inputs['Vector'])
        m2 = N.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs[0].default_value = grain
        L.new(col, m2.inputs[6]); L.new(nz.outputs['Color'], m2.inputs[7]); col = m2.outputs[2]
    L.new(col, b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.15; bump.inputs['Distance'].default_value = 0.0004
    L.new(p.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def painted(name, c, rough=0.55):
    return clay(name, c, rough=rough, sss=0.0, bump=0.12, thumb=0.05, scale=2.0)


WALL = striped('wallpaper', (0.10, 0.115, 0.10), (0.06, 0.07, 0.065), 70, 'X', sharp=3.0)
FLOOR = striped('boards', (0.11, 0.06, 0.035), (0.05, 0.026, 0.015), 38, 'Y', rough=0.5, sharp=0.6, grain=0.5)
WOOD = painted('wood_dark', (0.045, 0.025, 0.018))
TRIM = painted('trim', (0.16, 0.16, 0.15))
SHEET = BM.fabric('bedsheet', '#b9b4ad', 'weave', fuzz=0.6, scale=1500, dark=0.85)
BLANKET = BM.fabric('blanket', '#4b3a52', 'knit', fuzz=0.9)
CURTAIN = BM.fabric('curtain', '#3a2430', 'weave', fuzz=0.7, scale=900, dark=0.7)
RUG = BM.fabric('rug', '#5a2a26', 'knit', fuzz=0.15)
VOID = emissive('void', (0, 0, 0), 0.0)
SKY = emissive('night_sky', (0.08, 0.13, 0.3), 0.7)
MOON = emissive('moon', (0.9, 0.93, 1.0), 6.0)
SHADE = emissive('lampshade', (1.0, 0.62, 0.3), 3.0)
GLOW = emissive('eyes_glow', (0.85, 0.95, 0.5), 12.0)

# ------------------------------------------------------------------ the set (metres at puppet scale; she is 12.6 cm)
WX0, WX1, WY, WH = -0.32, 0.32, 0.22, 0.55     # back wall plane (its front face at WY - 0.005)
WIN = (-0.22, -0.12, 0.09, 0.18)               # window hole x0 x1 z0 z1, above the bed
DOOR = (0.17, 0.25, 0.16)                      # doorway x0 x1 height, back right
MATT, SEAT = 0.04, 0.027                       # mattress top, chair seat top
BED = (-0.275, -0.065, 0.065, 0.175)           # mattress footprint x0 x1 y0 y1
CHAIR = (0.09, 0.05)
SEATR = (0.065, 0.115, 0.0275, 0.0725)
cols = HP.colliders()


def box(name, x0, x1, y0, y1, z0, z1, mat, bevel=0.002, coll=False):
    ob = rounded_box(name, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), bevel=bevel, mat=mat)
    if coll: cols.objects.link(ob)
    return ob


box('floor', -0.45, 0.45, -0.6, WY, -0.01, 0.0, FLOOR, bevel=0.0005, coll=True)
for x0, x1, z0, z1 in ((WX0, WIN[0], 0, WH), (WIN[0], WIN[1], 0, WIN[2]), (WIN[0], WIN[1], WIN[3], WH),
                       (WIN[1], DOOR[0], 0, WH), (DOOR[0], DOOR[1], DOOR[2], WH), (DOOR[1], WX1, 0, WH)):
    box('wall', x0, x1, WY - 0.005, WY + 0.005, z0, z1, WALL, bevel=0.0005)
box('wall_left', WX0 - 0.01, WX0, -0.3, WY + 0.005, 0, WH, WALL, bevel=0.0005)
box('skirting', WX0, WIN[1], WY - 0.008, WY - 0.004, 0, 0.012, TRIM, bevel=0.001)
box('skirting2', WIN[1], DOOR[0] - 0.006, WY - 0.008, WY - 0.004, 0, 0.012, TRIM, bevel=0.001)
# window: frame, cross bars, curtains, sky and moon outside
x0, x1, z0, z1 = WIN
for a in ((x0 - 0.006, x0, z0 - 0.006, z1 + 0.006), (x1, x1 + 0.006, z0 - 0.006, z1 + 0.006),
          (x0, x1, z0 - 0.006, z0), (x0, x1, z1, z1 + 0.006), ((x0 + x1) / 2 - 0.002, (x0 + x1) / 2 + 0.002, z0, z1),
          (x0, x1, (z0 + z1) / 2 - 0.002, (z0 + z1) / 2 + 0.002)):
    box('win_frame', a[0], a[1], WY - 0.008, WY + 0.002, a[2], a[3], TRIM, bevel=0.0008)
box('sill', x0 - 0.012, x1 + 0.012, WY - 0.02, WY, z0 - 0.009, z0 - 0.005, TRIM, bevel=0.001)
for cx in (x0 - 0.012, x1 + 0.012):
    c = box('curtain', cx - 0.014, cx + 0.014, WY - 0.016, WY - 0.008, z0 - 0.04, z1 + 0.012, CURTAIN, bevel=0.004)
    add_lumps(c, 0.0015, size=0.01)
box('curtain_rod', x0 - 0.03, x1 + 0.03, WY - 0.014, WY - 0.01, z1 + 0.012, z1 + 0.016, WOOD, bevel=0.001)
sky = box('sky', -0.5, 0.2, 0.42, 0.43, -0.1, 0.5, SKY, bevel=0)
moon = sphere('moon', 0.022, (-0.205, 0.41, 0.165), mat=MOON)
# doorway: frame, the door on a hinge, darkness behind, two eyes that appear later
d0, d1, dh = DOOR
for a in ((d0 - 0.007, d0, 0, dh + 0.007), (d1, d1 + 0.007, 0, dh + 0.007), (d0, d1, dh, dh + 0.007)):
    box('door_frame', a[0], a[1], WY - 0.009, WY + 0.004, a[2], a[3], TRIM, bevel=0.0008)
hinge = empty('door_hinge', (d1 - 0.002, WY + 0.002, 0))
leaf = box('door', d0 - d1 + 0.003, -0.001, -0.003, 0.003, 0.001, dh - 0.001, WOOD, bevel=0.001)
for zz in (0.03, 0.1):
    p = box('door_panel', d0 - d1 + 0.012, -0.01, -0.0045, -0.003, zz, zz + 0.05, WOOD, bevel=0.0012)
    parent(p, leaf)
knob = sphere('knob', 0.003, (d0 - d1 + 0.012, -0.006, 0.075), mat=TRIM); parent(knob, leaf)
leaf.parent = hinge
box('void', d0 - 0.1, d1 + 0.1, WY + 0.13, WY + 0.2, -0.01, dh + 0.1, VOID, bevel=0)
box('hall_l', d0 - 0.1, d0 - 0.09, WY + 0.005, WY + 0.13, -0.01, dh + 0.1, VOID, bevel=0)
box('hall_r', d1 + 0.09, d1 + 0.1, WY + 0.005, WY + 0.13, -0.01, dh + 0.1, VOID, bevel=0)
box('hall_top', d0 - 0.1, d1 + 0.1, WY + 0.005, WY + 0.13, dh + 0.09, dh + 0.1, VOID, bevel=0)
eyes = []
for sx in (-1, 1):
    e = sphere('void_eye', 0.0045, (d0 + 0.022 + sx * 0.009, WY + 0.09, 0.112), scale=(1, 0.5, 0.75), mat=GLOW)
    eyes.append(e)
# bed: frame, headboard, mattress, pillow, folded blanket
bx0, bx1, by0, by1 = BED
box('bed_frame', bx0 - 0.004, bx1 + 0.004, by0 - 0.004, by1 + 0.004, 0.008, MATT - 0.01, WOOD, bevel=0.002)
for lx in (bx0, bx1):
    for ly in (by0, by1): box('bed_leg', lx - 0.004, lx + 0.004, ly - 0.004, ly + 0.004, 0, 0.01, WOOD, bevel=0.001)
box('headboard', bx0 - 0.012, bx0 - 0.004, by0 - 0.004, by1 + 0.004, 0, 0.1, WOOD, bevel=0.003)
for i in range(5):
    yy = by0 + (i + 0.5) * (by1 - by0) / 5
    box('headboard_spindle', bx0 - 0.01, bx0 - 0.006, yy - 0.002, yy + 0.002, 0.1, 0.13, WOOD, bevel=0.001)
box('headboard_top', bx0 - 0.013, bx0 - 0.003, by0 - 0.006, by1 + 0.006, 0.128, 0.134, WOOD, bevel=0.002)
m = box('mattress', bx0, bx1, by0, by1, MATT - 0.012, MATT, SHEET, bevel=0.005, coll=True); add_lumps(m, 0.0008, size=0.02)
pw = box('pillow', bx0 + 0.006, bx0 + 0.048, by0 + 0.02, by1 - 0.02, MATT - 0.002, MATT + 0.006, SHEET, bevel=0.004, coll=True)
add_lumps(pw, 0.001, size=0.012)
bl = box('blanket', bx1 - 0.03, bx1 + 0.002, by0 - 0.002, by1 + 0.002, MATT - 0.002, MATT + 0.007, BLANKET, bevel=0.004, coll=True)
add_lumps(bl, 0.0012, size=0.01)
# nightstand and lamp (a practical: warm glow)
box('nightstand', -0.055, -0.02, WY - 0.045, WY - 0.008, 0, 0.045, WOOD, bevel=0.002)
cylinder('lamp_base', 0.006, 0.018, (-0.038, WY - 0.026, 0.054), mat=TRIM)
shade = cylinder('lamp_shade', 0.011, 0.014, (-0.038, WY - 0.026, 0.069), mat=SHADE)
lamp = point_light('lamp', (-0.038, WY - 0.026, 0.069), 0.6, radius=0.006, color=(1.0, 0.66, 0.35))
# chair, facing the camera
cx, cy = CHAIR; sx0, sx1, sy0, sy1 = SEATR
box('seat', sx0, sx1, sy0, sy1, SEAT - 0.005, SEAT, WOOD, bevel=0.0015, coll=True)
for lx in (sx0 + 0.004, sx1 - 0.004):
    for ly in (sy0 + 0.004, sy1 - 0.004): box('chair_leg', lx - 0.0025, lx + 0.0025, ly - 0.0025, ly + 0.0025, 0, SEAT - 0.004, WOOD, bevel=0.0008)
    box('chair_post', lx - 0.0025, lx + 0.0025, sy1 - 0.0065, sy1 - 0.0015, SEAT, 0.085, WOOD, bevel=0.0008)
box('chair_rail', sx0 + 0.002, sx1 - 0.002, sy1 - 0.006, sy1 - 0.002, 0.07, 0.085, WOOD, bevel=0.001)
box('chair_rail2', sx0 + 0.002, sx1 - 0.002, sy1 - 0.0055, sy1 - 0.0025, 0.048, 0.054, WOOD, bevel=0.001)
# rug and a small frame on the wall
r = cylinder('rug', 0.085, 0.0012, (-0.01, 0.01, 0.0006), mat=RUG, verts=64); cols.objects.link(r)
box('picture', -0.005, 0.045, WY - 0.008, WY - 0.005, 0.12, 0.18, TRIM, bevel=0.001)
box('picture_in', 0.0, 0.04, WY - 0.0095, WY - 0.007, 0.125, 0.175, painted('picture_dark', (0.02, 0.02, 0.025)), bevel=0.0005)

# lights: moonlight through the window, the lamp, a soft front key so her face reads, a cool rim
moon_l = area_light('moonlight', (-0.2, 0.5, 0.36), (-0.15, 0.08, 0.0), 26, 0.12, (0.62, 0.74, 1.0))
key_l = area_light('key', (-0.25, -0.35, 0.22), (0, 0.05, 0.05), 3.2, 0.25, (1.0, 0.9, 0.8))
fill = area_light('fill', (0.35, -0.3, 0.12), (0, 0.05, 0.04), 0.7, 0.4, (0.6, 0.7, 1.0))
rim = area_light('rim', (0.3, 0.35, 0.25), (0, 0.05, 0.06), 2.0, 0.15, (0.7, 0.8, 1.0))
door_l = area_light('hall', ((d0 + d1) / 2, WY + 0.15, 0.1), ((d0 + d1) / 2, 0.0, 0.0), 0.0, 0.05, (0.7, 0.8, 0.6))

# ------------------------------------------------------------------ the puppet
h = HB.HaruBurton(loc=(-0.183, 0.12, 0), yaw=math.radians(90))
contact_obs = list(h.meshes)
LIMB = ('hand', 'sleeve', 'shin', 'ankle', 'sole', 'stripe', 'shoe', 'toecap', 'laces', 'eyelets')
SUPPORTS = [((-9, 9, -9, 9), 0.0), (BED, MATT), (SEATR, SEAT)]
BAND, SINK = 0.008, 0.0025      # a hand or foot counts as resting on a raised support only when it is within 8 mm of its top


FEET = ('sole', 'stripe', 'shoe', 'toecap')


def world_verts():
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); out, kind = [], []
    for i, ob in enumerate(contact_obs):
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
        k = (100 + i) if any(f in ob.name for f in FEET) else 1 if any(f in ob.name for f in LIMB) else 0
        kind.append(np.full(len(co) // 3, k))
        Mw = np.array(ev.matrix_world); out.append(co.reshape(-1, 3) @ Mw[:3, :3].T + Mw[:3, 3]); ev.to_mesh_clear()
    return np.concatenate(out), np.concatenate(kind)


def settle(supports=SUPPORTS, lift=0.0, feet_on=None):
    """Put her on what is under her. The floor holds everything. A raised support (mattress, seat) holds her body
    (bottom, thighs, back, head). Each shoe counts only when its lowest point over the support is near the surface
    (a foot standing on it), so legs hanging over an edge or tucked under a seat never lift her; hands and arms sink
    into the soft surfaces instead of propping her up."""
    h.root.location.z = 0.0
    W, kind = world_verts(); off = -1.0
    for i, ((x0, x1, y0, y1), top) in enumerate(supports):
        m = (W[:, 0] > x0) & (W[:, 0] < x1) & (W[:, 1] > y0) & (W[:, 1] < y1)
        if i > 0: m &= kind == 0
        if m.any(): off = max(off, top - float(W[m, 2].min()))
    for si, ((x0, x1, y0, y1), top) in enumerate(supports[1:], 1):
        inr = (W[:, 0] > x0) & (W[:, 0] < x1) & (W[:, 1] > y0) & (W[:, 1] < y1)
        body = inr & (kind == 0)
        sitting = body.any() and float(W[body, 2].min()) + off < top + 0.001
        for k in np.unique(kind[kind >= 100]):
            m = inr & (kind == k)
            if not m.any(): continue
            lo = float(W[m, 2].min()) + off
            if si == feet_on and m.sum() > 0.6 * (kind == k).sum():       # she is standing on this surface
                if lo < top - SINK: off += top - SINK - lo
            elif not sitting and top - BAND < lo < top - SINK: off += top - SINK - lo   # at an edge: only when near the top
    h.root.location.z = off + lift


# ------------------------------------------------------------------ the performance: Mixamo motion capture, cut together
import mocap as MC
LIB = MC.Library(os.path.join(HERE, '..', 'mocap', 'clips.npz'), h)
K = LIB.k
END = 32.5
F = int(END * FPS); sc.frame_end = F


def Rz(yaw): return Vector((0, 0, 1)), math.radians(yaw)


def turn2(v, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)); return Vector((c * v.x - s * v.y, s * v.x + c * v.y))


P_LIE, P_EDGE = Vector((-0.183, 0.12)), Vector((-0.15, 0.074))
P_MID, P_CHAIR = Vector((-0.03, 0.024)), Vector((CHAIR[0], 0.05))
P_RUN1 = Vector((-0.09, 0.03))
# clip seconds: getup_from_back lies still to 2.4 s and sits up by 4.4 s; scared_out_of_seat jumps up at 1.4-2.0 s
SEGS = [
    dict(t0=0.0, t1=2.5, clip='lie_awake_lookaround', c0=0.0, yaw=90, at=P_LIE),
    dict(t0=2.5, t1=4.5, clip='getup_from_back', c0=2.35, c1=4.35, yaw=90, at=P_LIE, fade=0.4),
    dict(t0=4.5, t1=5.7, clip='sit_to_stand', c0=0.0, c1=0.0, yaw=0, at=P_EDGE, fade=1.1),       # swings round to the edge
    dict(t0=5.7, t1=8.0, clip='sit_to_stand', c0=0.0, c1=2.27, yaw=0, fade=0.0),
    dict(t0=8.0, t1=9.0, clip='turn_left_90', c0=0.0, c1=0.93, yaw=0, fade=0.25),
    dict(t0=9.0, t1=11.2, clip='crouch_walk', c0=0.0, loop=True, to=P_MID, fade=0.35),
    dict(t0=11.2, t1=12.8, clip='terrified', c0=0.8, c1=2.4, yaw=90, fade=0.25),               # the door creaks: she cowers
    dict(t0=12.8, t1=15.0, clip='crouch_walk', c0=0.0, loop=True, to='chair_front', fade=0.35),
    dict(t0=15.0, t1=16.0, clip='turn_left_90', c0=0.0, c1=0.93, yaw=90, mirror=True, fade=0.25),
    dict(t0=16.0, t1=18.3, clip='stand_to_sit', c0=0.0, c1=2.23, yaw=0, end=P_CHAIR, fade=0.25),
    dict(t0=18.3, t1=21.5, clip='sit_look_side', c0=0.0, c1=3.2, yaw=0, at=P_CHAIR, fade=0.3),
    dict(t0=21.5, t1=23.6, clip='scared_out_of_seat', c0=1.0, c1=3.1, yaw=0, at=P_CHAIR, fade=0.2),
    dict(t0=23.6, t1=24.5, clip='turn_left_90', c0=0.0, c1=0.93, yaw=0, mirror=True, fade=0.2),
    dict(t0=24.5, t1=26.3, clip='run_scared', c0=0.0, loop=True, to=P_RUN1, fade=0.25),
    dict(t0=26.3, t1=27.6, clip='jump_onto_platform', c0=0.0, c1=1.23, yaw=180, air=True, fade=0.25, feet_on=1),
    dict(t0=27.6, t1=31.0, clip='terrified', c0=1.2, c1=3.6, yaw=110, fade=0.35, feet_on=1),
    dict(t0=31.0, t1=END, clip='terrified', c0=0.0, c1=0.6, yaw=110, fade=0.45, feet_on=1),       # straightens up, turns to us
]
# where the stand-to-sit clip starts, so that she ends up sitting on the chair
_s = SEGS[9]; _d = LIB.hips(_s['clip'], _s['c1']) - LIB.hips(_s['clip'], _s['c0'])
P_CHAIR_FRONT = P_CHAIR - turn2(Vector((_d.x, _d.y)) * K, _s['yaw'])
SEGS[7]['to'] = P_CHAIR_FRONT


def resolve():
    """start position, yaw and playback rate of every segment, chained from the one before"""
    end = None
    for s in SEGS:
        s.setdefault('fade', 0.3); s.setdefault('mirror', False); s.setdefault('loop', False); s.setdefault('air', False)
        start = Vector(s['at']) if 'at' in s else end
        if 'to' in s:                                       # a walk/run cycle played at the rate that reaches the target
            d = Vector(s['to']) - start
            s['yaw'] = math.degrees(math.atan2(d.x, -d.y))
            H = LIB.clips[s['clip']][1]; T = LIB.length(s['clip'])
            v = K * (Vector(H[-1][:2]) - Vector(H[0][:2])).length / T
            s['c1'] = s['c0'] + d.length / v
        s.setdefault('c1', s['c0'] + (s['t1'] - s['t0']))
        if 'end' in s:
            dh = LIB.hips(s['clip'], s['c1'], s['mirror']) - LIB.hips(s['clip'], s['c0'], s['mirror'])
            start = Vector(s['end']) - turn2(Vector((dh.x, dh.y)) * K, s['yaw'])
        s['start'] = start
        dh = LIB.hips(s['clip'], s['c1'], s['mirror'], s['loop']) - LIB.hips(s['clip'], s['c0'], s['mirror'], s['loop'])
        end = start + turn2(Vector((dh.x, dh.y)) * K, s['yaw'])


resolve()


def eval_seg(s, t):
    """world rotations (with yaw), root xy, and the mocap lift (air segments) for segment s at scene time t"""
    u = (t - s['t0']) / max(1e-6, s['t1'] - s['t0'])
    if not s['loop']: u = min(max(u, 0.0), 1.0)
    c = s['c0'] + (s['c1'] - s['c0']) * u
    W, hp = LIB.sample(s['clip'], c, s['mirror'], s['loop'])
    h0 = LIB.hips(s['clip'], s['c0'], s['mirror'], s['loop'])
    d = hp - h0
    xy = s['start'] + turn2(Vector((d.x, d.y)) * K, s['yaw'])
    lift = K * (hp.z - h0.z) if s['air'] else None
    return MC.rotate(W, math.radians(s['yaw'])), xy, lift


def performance(t):
    i = max(j for j, s in enumerate(SEGS) if t >= s['t0'] - 1e-9)
    s = SEGS[i]; W, xy, lift = eval_seg(s, t)
    if i > 0 and s['fade'] > 0 and t < s['t0'] + s['fade']:
        k = seg(t, s['t0'], s['t0'] + s['fade'])
        Wp, xyp, liftp = eval_seg(SEGS[i - 1], t)
        W = MC.blend(Wp, W, k); xy = xyp.lerp(xy, k)
        if lift is not None and liftp is not None: lift = liftp + (lift - liftp) * k
    return W, xy, lift, s


def face(t):
    gaze = None
    if t < 1.2: n = 'stare'
    elif t < 4.5: n = 'worried'
    elif t < 8.0: n = 'scared'
    elif t < 11.2: n = 'worried'
    elif t < 12.8: n = 'terrified'
    elif t < 15.0: n = 'suspicious'
    elif t < 18.3: n = 'worried'
    elif t < 21.5:
        n = ('sad', 'suspicious', 'relieved', 'smile')[min(int((t - 18.3) / 0.8), 3)]
        if n == 'suspicious': gaze = ((-14, 0), (14, 0), (0, 0))[int((t - 19.1) / 0.27) % 3]
    elif t < 21.8: n = 'surprised'
    elif t < 27.6: n = 'terrified'
    elif t < 31.6: n = 'scared'
    else: n = 'stare'
    blink = any(abs(t - b) < 0.09 for b in (2.0, 5.2, 9.6, 14.1, 17.4, 20.9, 28.9, 32.0))
    return n, blink, gaze


SHIVER = [(4.6, 7.0), (11.2, 12.8), (21.8, 22.6), (27.8, 30.0), (31.0, END)]
CUTS = (5.7, 18.3, 21.8, 27.6, 30.0, 31.0)
cam = camera((0, -0.3, 0.09), (0, 0, 0.06), lens=35, fstop=5.6)
cam.data.clip_start = 0.005


def head_pt():
    return h.P['head'].matrix_world @ Vector((0, -0.012, 0.009))


def shot(t, hp, root, cx):
    if t < 5.7:                     # low by the bed
        u = seg(t, 2.5, 5.0)
        return Vector((-0.13, -0.16, 0.07)), Vector((-0.17, 0.11, 0.05)).lerp(hp + Vector((0, 0, -0.02)), u), 40, hp, 5.6
    if t < 18.3:                    # follows her across the room, low
        tgt = Vector((cx, root.y + 0.02, 0.055)) if t < 16.0 else Vector((cx, root.y, 0.055)).lerp(hp + Vector((0, 0, -0.02)), seg(t, 16.0, 18.0))
        return Vector((cx + 0.03, -0.26, 0.07)), tgt, 32, hp, 5.6
    if t < 21.8:                    # close: her face on the chair
        return hp + Vector((0.01, -0.16, 0.002)), hp + Vector((0, 0, -0.008)), 55 + 12 * seg(t, 18.3, 21.5), hp, 11.0
    if t < 27.6:                    # wide: she bolts and leaps onto the bed
        return Vector((cx, -0.33, 0.1)), Vector((cx, 0.05, 0.05)), 30, hp, 6.0
    if t < 30.0:                    # the bed, from the door side
        return Vector((0.07, -0.12, 0.11)), hp + Vector((0, 0, -0.03)), 40, hp, 5.6
    if t < 31.0:                    # the doorway
        ep = Vector((d0 + 0.022, WY + 0.09, 0.112))
        return Vector((0.16, -0.05, 0.085)).lerp(Vector((0.175, -0.01, 0.09)), seg(t, 30.0, 31.0)), ep, 50, ep, 4.0
    d = Vector((math.sin(math.radians(60)), -math.cos(math.radians(60)), 0))
    return hp + d * 0.16 + Vector((0, 0, 0.004)), hp + Vector((0, 0, -0.008)), 60 + 6 * seg(t, 31.0, END), hp, 11.0


# ------------------------------------------------------------------ animate
shade_em = SHADE.node_tree.nodes['Emission'].inputs[1]
boil = Boil(5, amp=0.00018, rot=0.004)
chat = random.Random(7)
cx, last_sid = None, -1
for f in range(1, F + 1):
    t = (f - 1) / FPS
    W, xy, lift, s = performance(t)
    yaw = math.radians(s['yaw'])
    h.root.location = (xy.x, xy.y, 0.0); h.root.rotation_euler = (0, 0, yaw)
    MC.apply(h, W, yaw)
    # the animator's hand: tiny misses every pose; shivering when she is afraid; at the end she turns her head to us
    for pv in ('chest', 'neck', 'head', 'upper_arm.L', 'upper_arm.R'):
        e = h.P[pv]; a = 0.01 + (0.035 if any(a0 <= t < a1 for a0, a1 in SHIVER) else 0.0)
        e.rotation_euler = (e.rotation_euler.x + chat.uniform(-a, a), e.rotation_euler.y, e.rotation_euler.z + chat.uniform(-a, a))
    g = seg(t, 31.4, 31.75)
    if g: h.P['head'].rotation_euler.z -= math.radians(45) * g; h.P['neck'].rotation_euler.z -= math.radians(12) * g
    settle(SUPPORTS, feet_on=s.get('feet_on'))
    if lift is not None: h.root.location.z = max(h.root.location.z, lift)
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, yaw + je.z)
    n, bl, gz = face(t)
    h.expr(n, blink=bl, gaze=gz)
    h.key(f)

    # the set acts: door ajar from frame one, a creak, a bang; the lamp stutters and dies; eyes in the doorway
    ang = -9 - 8 * seg(t, 11.2, 11.5) - 30 * seg(t, 21.75, 21.85) - 12 * seg(t, 29.0, 30.0)
    hinge.rotation_euler = (0, 0, math.radians(ang)); key(hinge, f, rot=tuple(hinge.rotation_euler))
    door_l.data.energy = 0.08 + 0.05 * seg(t, 11.2, 11.5) + 0.25 * seg(t, 21.75, 21.85); door_l.data.keyframe_insert('energy', frame=f)
    show = 1.0 if t >= 30.2 else 1e-4
    blink_e = 0.15 if abs(t - 30.6) < 0.06 else 1.0
    for e in eyes: e.scale = (show, show * 0.5, show * 0.75 * blink_e); key(e, f, scale=tuple(e.scale))
    lit = 0.0 if (21.5 <= t < 21.6 or 21.68 <= t < 21.76 or t >= 28.5) else 1.0
    lamp.data.energy = 0.6 * lit * (1 + boil.r.uniform(-0.03, 0.03)); lamp.data.keyframe_insert('energy', frame=f)
    shade_em.default_value = 3.0 * lit + 0.05; shade_em.keyframe_insert('default_value', frame=f)
    key_l.data.energy = 3.2 * (1 + boil.r.uniform(-0.012, 0.012)) * (0.8 if t >= 28.5 else 1.0); key_l.data.keyframe_insert('energy', frame=f)

    bpy.context.view_layer.update()
    hp = head_pt(); root = h.root.location.copy()
    sid = sum(t >= c for c in CUTS)
    cx = root.x if (cx is None or sid != last_sid) else cx + (root.x - cx) * 0.35; last_sid = sid
    loc, tgt, lens, fp, fs = shot(t, hp, root, cx)
    cam.location = loc; look_at(cam, tgt); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.focus_distance = (loc - fp).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    cam.data.dof.aperture_fstop = fs; cam.data.dof.keyframe_insert('aperture_fstop', frame=f)

constant_interp()
run(sc, OPTS)
