"""Room test: the Burton Haru puppet in her bedroom, played as a horror beat (26.5 s, 318 frames at 12 fps, stop motion, 9:16).

Frame one: she lies awake, frozen, staring; the door is already ajar. Her eyes slide to the door -> she sits up slowly
-> pulls her knees in, shivering -> inches to the edge and slips off -> creeps across the room on tiptoe, hunched,
hands clutched -> the door creaks: she freezes mid-step and stares -> creeps on, glances back at the bed -> sits on the
chair and pulls her knees up -> close-up: worry, eyes darting, sadness, a breath of relief, a small smile -> the lamp
stutters and the door bangs open -> she scrambles off the chair and runs, glancing back -> dives onto the bed and
shoves herself back into the corner -> the lamp dies -> two eyes in the dark doorway -> she turns and stares at us.

Contact: the floor holds everything; the mattress and the chair seat hold her body, and her hands and feet only count
when they are at their surface (see settle()).
blender -b -P scenes/haru_room.py -- [--still F] [--range A B] [--res 1080 1920] [--samples 64] [--out DIR]
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


def settle(supports=SUPPORTS, lift=0.0):
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
    for (x0, x1, y0, y1), top in supports[1:]:
        inr = (W[:, 0] > x0) & (W[:, 0] < x1) & (W[:, 1] > y0) & (W[:, 1] < y1)
        body = inr & (kind == 0)
        if body.any() and float(W[body, 2].min()) + off < top + 0.001: continue   # sitting on it: feet can't lift her
        for k in np.unique(kind[kind >= 100]):
            m = inr & (kind == k)
            if not m.any(): continue
            lo = float(W[m, 2].min()) + off
            if top - BAND < lo < top - SINK: off += top - SINK - lo        # a shoe may press 2.5 mm in, never lift her
    h.root.location.z = off + lift


# ------------------------------------------------------------------ poses (pivot, axis): degrees
SITL = ST.SIT
SITC = {('thigh.L', 'x'): -90, ('thigh.R', 'x'): -90, ('shin.L', 'x'): 90, ('shin.R', 'x'): 90, ('chest', 'x'): 5,
        ('thigh.L', 'z'): 3, ('thigh.R', 'z'): -3,
        ('upper_arm.L', 'x'): -28, ('upper_arm.R', 'x'): -28, ('upper_arm.L', 'y'): 4, ('upper_arm.R', 'y'): -4,
        ('forearm.L', 'x'): -42, ('forearm.R', 'x'): -42, ('head', 'x'): 3}
SITE = add(SITC, {('shin.L', 'x'): -4, ('shin.R', 'x'): -4, ('chest', 'x'): 4, ('head', 'x'): 6})   # bed edge, hands on her lap
PUSH = {('hips', 'x'): 32, ('thigh.L', 'x'): -100, ('thigh.R', 'x'): -100, ('shin.L', 'x'): 80, ('shin.R', 'x'): 80,
        ('foot.L', 'x'): -8, ('foot.R', 'x'): -8, ('head', 'x'): -22, ('chest', 'x'): 6,
        ('upper_arm.L', 'x'): -20, ('upper_arm.R', 'x'): -20, ('forearm.L', 'x'): -30, ('forearm.R', 'x'): -30}
CLUTCH = {('upper_arm.L', 'x'): -38, ('upper_arm.R', 'x'): -38, ('upper_arm.L', 'y'): 14, ('upper_arm.R', 'y'): -14,
          ('forearm.L', 'x'): -100, ('forearm.R', 'x'): -100, ('forearm.L', 'z'): -25, ('forearm.R', 'z'): 25}
HUNCH = add(CLUTCH, {('hips', 'x'): 14, ('chest', 'x'): 10, ('neck', 'x'): -4, ('head', 'x'): -14,
                     ('thigh.L', 'x'): -14, ('thigh.R', 'x'): -14, ('shin.L', 'x'): 26, ('shin.R', 'x'): 26,
                     ('foot.L', 'x'): -12, ('foot.R', 'x'): -12})
# knees hugged, curled forward, toes tipped down: measured so her bottom and her soles land within 2 mm of each other
HUG = add(ST.HUG, {('hips', 'x'): 12, ('thigh.L', 'x'): -28, ('thigh.R', 'x'): -28, ('shin.L', 'x'): 28, ('shin.R', 'x'): 28,
                  ('foot.L', 'x'): -10, ('foot.R', 'x'): -10, ('forearm.L', 'x'): 10, ('forearm.R', 'x'): 10, ('neck', 'x'): -6, ('head', 'x'): -20})   # chin up: eyes over her knees
HUGC = HUG                                                       # the same, with her feet up on the chair seat
SNEAK_STRIDE, RUN_STRIDE = 0.05, 0.13


def sneak(p):
    """creeping on tiptoe: short careful steps, hunched, hands clutched at her chest"""
    w = ST.walk(p)
    legs = {k: v * 0.75 for k, v in w.items() if k[0].startswith(('thigh', 'shin', 'foot')) or k == ('hips', 'z')}
    return add(HUNCH, legs)


def trap(t, t0, t1, r=0.35):
    if t <= t0: return 0.0
    if t >= t1: return 1.0
    T = t1 - t0; r = min(r, T / 2); v = 1.0 / (T - r); u = t - t0
    if u < r: return 0.5 * v / r * u * u
    if u > T - r: w = T - u; return 1.0 - 0.5 * v / r * w * w
    return 0.5 * v * r + v * (u - r)


def lerp2(a, b, u): return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


P_LIE, P_EDGE, P_UP = (-0.183, 0.12), (-0.15, 0.074), (-0.15, 0.035)
P_MID, P_CHAIR_FRONT, P_CHAIR = (-0.03, 0.022), (CHAIR[0], 0.004), (CHAIR[0], 0.052)
P_RUN0, P_RUN1, P_LAND, P_CORNER = (0.08, -0.004), (-0.09, 0.03), (-0.13, 0.11), (-0.19, 0.122)
PARADE = [('worried', None), ('suspicious', 'dart'), ('sad', None), ('relieved', None), ('smile', None)]
SHIVER = [(4.9, 7.6), (9.6, 10.6), (18.9, 19.3), (21.7, 24.0), (25.0, 26.5)]


def beat(t, phase):
    """pose spec, root xy, yaw (deg), lift, supports, stride"""
    sup, lift, stride = SUPPORTS, 0.0, SNEAK_STRIDE
    breath = math.sin(t * 2 * math.pi / 2.6)
    if t < 3.0:                                                           # awake, frozen, staring; then eyes to the door
        g = seg(t, 1.6, 2.6)
        spec, xy, yaw = add(ST.LIE, {('head', 'z'): 38 * g, ('neck', 'z'): 8 * g}), P_LIE, 90
    elif t < 4.8:                                                         # sits up slowly, still watching
        u = seg(t, 3.0, 4.8); spec = add(mix(ST.LIE, SITL, u), {('head', 'z'): 38 * (1 - u) + 20 * u}); xy, yaw = P_LIE, 90
    elif t < 5.6: spec, xy, yaw = add(mix(SITL, HUG, seg(t, 4.8, 5.5)), {('head', 'z'): 20}), P_LIE, 90
    elif t < 6.8:                                                         # inches to the edge
        u = seg(t, 5.6, 6.7); spec = mix(HUG, SITE, u); xy = lerp2(P_LIE, P_EDGE, u); yaw = 90 * (1 - u)
    elif t < 8.0:
        spec = mix(SITE, PUSH, seg(t, 6.8, 7.2)) if t < 7.2 else mix(PUSH, HUNCH, seg(t, 7.2, 7.8))
        xy = lerp2(P_EDGE, P_UP, seg(t, 6.9, 7.7)); yaw = 90 * seg(t, 7.6, 8.0)
    elif t < 12.4:                                                        # creeps across, freezes when the door creaks
        if t < 9.6: xy = lerp2(P_UP, P_MID, trap(t, 8.0, 9.6))
        elif t < 10.6: xy = P_MID
        else: xy = lerp2(P_MID, P_CHAIR_FRONT, trap(t, 10.6, 12.3))
        yaw = 90
        moving = seg(t, 8.0, 8.2) * (1 - seg(t, 9.45, 9.6)) + seg(t, 10.6, 10.8) * (1 - seg(t, 12.1, 12.3))
        spec = sneak(phase) if 9.6 <= t < 10.6 else mix(HUNCH, sneak(phase), moving)   # frozen mid-step
        g = seg(t, 9.7, 9.78) * (1 - seg(t, 10.3, 10.6))                  # head snaps to the door, stares, then on
        spec = add(spec, {('head', 'z'): 40 * g, ('neck', 'z'): 12 * g, ('chest', 'z'): 8 * g, ('head', 'x'): -8 * g})
        b = seg(t, 11.2, 11.4) * (1 - seg(t, 11.8, 12.0))                 # a look back over her shoulder at the bed
        spec = add(spec, {('head', 'z'): -55 * b, ('neck', 'z'): -15 * b})
    elif t < 12.9: spec, xy, yaw = HUNCH, P_CHAIR_FRONT, 90 * (1 - seg(t, 12.4, 12.85))
    elif t < 13.9:
        u = seg(t, 12.95, 13.85); spec = mix(HUNCH, PUSH, min(1, u * 1.6)) if u < 0.6 else mix(PUSH, SITC, (u - 0.6) / 0.4)
        xy = lerp2(P_CHAIR_FRONT, P_CHAIR, seg(t, 13.0, 13.7)); yaw = 0
    elif t < 14.6: spec, xy, yaw = mix(SITC, HUGC, seg(t, 13.95, 14.5)), P_CHAIR, 0
    elif t < 18.6:
        i = min(int((t - 14.6) / 0.8), 4); tilt = [(0, 0), (5, -3), (-6, 5), (0, -6), (4, 3)][i]
        sigh = math.sin(math.pi * seg(t, 17.0, 17.6))                      # 'relieved': a long breath out
        spec = add(HUGC, {('head', 'y'): tilt[0], ('head', 'x'): tilt[1] + 4 * sigh, ('chest', 'x'): 3 * sigh}); xy, yaw = P_CHAIR, 0
    elif t < 19.2:                                                        # the lamp stutters, the door bangs open
        g = seg(t, 18.9, 18.98)
        spec = add(HUGC, {('head', 'z'): 60 * g, ('neck', 'z'): 18 * g, ('chest', 'z'): 14 * g}); xy, yaw = P_CHAIR, 0
    elif t < 19.8:
        u = seg(t, 19.2, 19.7)
        spec = mix(HUGC, SITC, seg(t, 19.2, 19.4)) if t < 19.4 else mix(SITC, ST.run(0.25), seg(t, 19.4, 19.75))
        xy = lerp2(P_CHAIR, P_RUN0, u); yaw = -90 * seg(t, 19.35, 19.75); stride = RUN_STRIDE
    elif t < 21.0:
        u = trap(t, 19.8, 21.0, 0.2); xy = lerp2(P_RUN0, P_RUN1, u); yaw = -90; stride = RUN_STRIDE
        spec = ST.run(phase); lift = 0.0035 * abs(math.sin(2 * math.pi * phase))
        b = seg(t, 20.3, 20.4) * (1 - seg(t, 20.55, 20.65))               # a glance back mid-run
        spec = add(spec, {('head', 'z'): -60 * b, ('neck', 'z'): -15 * b})
    elif t < 21.15: spec, xy, yaw = mix(ST.run(phase), ST.DIP, seg(t, 21.0, 21.15)), P_RUN1, -90
    elif t < 21.65:                                                       # dives onto the bed
        u = (t - 21.15) / 0.5
        spec = mix(ST.DIP, ST.JUMP, seg(u, 0, 0.3)) if u < 0.45 else mix(ST.JUMP, HUG, seg(u, 0.45, 1.0))
        xy = lerp2(P_RUN1, P_LAND, seg(u, 0, 1)); yaw = -90 + 150 * seg(u, 0.1, 0.9)
        sup = [SUPPORTS[0]]; lift = 0.04 * 4 * u * (1 - u) + MATT * seg(u, 0, 1)
    elif t < 22.7:                                                        # shoves herself back into the corner
        k = min(int((t - 21.75) / 0.32), 2) if t >= 21.75 else -1
        t0 = 21.75 + 0.32 * max(k, 0)
        u = 0 if k < 0 else (k + seg(t, t0, t0 + 0.2)) / 3
        xy = lerp2(P_LAND, P_CORNER, u); yaw = 60
        hop = 0.0 if k < 0 else math.sin(math.pi * seg(t, t0, t0 + 0.2))
        spec = add(HUG, {('hips', 'x'): -6 * hop, ('chest', 'x'): 6 * hop}); lift = 0.002 * hop
    else:
        spec, xy, yaw = HUG, P_CORNER, 60
        rock = math.sin((t - 22.7) * 2 * math.pi / 1.3) * (1 - seg(t, 25.2, 25.5))
        look = seg(t, 22.8, 23.1) * (1 - seg(t, 25.25, 25.6))             # watches the door, then turns to us
        spec = add(spec, {('hips', 'x'): 3 * rock, ('head', 'z'): 42 * look, ('neck', 'z'): 10 * look})
    spec = add(spec, {('chest', 'x'): 1.2 * breath * (0.5 if t < 4.8 else 1.0)})
    return spec, xy, yaw, lift, sup, stride


BLINKS = [2.4, 6.3, 8.7, 11.9, 13.5, 16.3, 22.5, 26.0]


def face(t):
    gaze = None
    if t < 1.6: n = 'stare'
    elif t < 4.8: n = 'worried'
    elif t < 7.8: n = 'scared'
    elif t < 9.6: n = 'worried'
    elif t < 10.6: n = 'terrified' if t > 9.75 else 'scared'
    elif t < 12.4: n = 'suspicious'
    elif t < 14.6: n = 'worried'
    elif t < 18.6:
        n, mode = PARADE[min(int((t - 14.6) / 0.8), 4)]
        if mode == 'dart': gaze = ((-14, 0), (14, 0), (0, 0))[int((t - 15.4) / 0.27) % 3]
    elif t < 18.9: n = 'surprised'
    elif t < 21.7: n = 'terrified'
    elif t < 25.6: n = 'scared'
    else: n = 'stare'
    blink = any(abs(t - b) < 0.09 for b in BLINKS)
    return n, blink, gaze


def shiver(t): return 2.0 if any(a <= t < b for a, b in SHIVER) else 0.0


# ------------------------------------------------------------------ camera shots (stop-motion cuts)
CUTS = (5.6, 14.6, 19.2, 21.7, 24.0, 25.0)
cam = camera((0, -0.3, 0.09), (0, 0, 0.06), lens=35, fstop=5.6)
cam.data.clip_start = 0.005


def head_pt():
    return h.P['head'].matrix_world @ Vector((0, -0.012, 0.009))


def shot(t, hp, root, cx):
    if t < 5.6:                     # low by the bed
        u = seg(t, 3.0, 5.0)
        return Vector((-0.13, -0.16, 0.07)), Vector((-0.17, 0.11, 0.05)).lerp(hp + Vector((0, 0, -0.02)), u), 40, hp, 5.6
    if t < 14.6:                    # follows her across the room, low
        tgt = Vector((cx, root.y + 0.02, 0.055)) if t < 12.9 else Vector((cx, root.y, 0.055)).lerp(hp + Vector((0, 0, -0.02)), seg(t, 12.9, 14.0))
        return Vector((cx + 0.03, -0.26, 0.07)), tgt, 32, hp, 5.6
    if t < 19.2:                    # close: her face on the chair
        return hp + Vector((0.01, -0.16, 0.002)), hp + Vector((0, 0, -0.008)), 55 + 12 * seg(t, 14.6, 18.6), hp, 11.0
    if t < 21.7:                    # wide: she runs
        return Vector((cx, -0.33, 0.1)), Vector((cx, 0.05, 0.05)), 30, hp, 6.0
    if t < 24.0:                    # the bed, from the door side
        return Vector((0.0, -0.01, 0.085)), hp + Vector((0, 0, -0.02)), 38, hp, 5.6
    if t < 25.0:                    # the doorway
        ep = Vector((d0 + 0.022, WY + 0.09, 0.112))
        return Vector((0.16, -0.05, 0.085)).lerp(Vector((0.175, -0.01, 0.09)), seg(t, 24.0, 25.0)), ep, 50, ep, 4.0
    d = Vector((math.sin(math.radians(60)), -math.cos(math.radians(60)), 0))
    return hp + d * 0.16 + Vector((0, 0, 0.004)), hp + Vector((0, 0, -0.008)), 60 + 6 * seg(t, 25.0, 26.5), hp, 11.0


# ------------------------------------------------------------------ animate
shade_em = SHADE.node_tree.nodes['Emission'].inputs[1]
boil = Boil(5, amp=0.00018, rot=0.004)
chat = random.Random(7)
phase, prev_xy, cx, last_sid = 0.0, None, None, -1
for f in range(1, F + 1):
    t = (f - 1) / FPS
    _, xy, _, _, _, stride = beat(t, phase)
    if prev_xy is not None: phase += math.dist(xy, prev_xy) / stride
    prev_xy = xy
    spec, xy, yaw, lift, sup, stride = beat(t, phase)
    spec = add(spec, {(b, a): chat.uniform(-ST.CHATTER, ST.CHATTER) for b in ST.CHATTER_BONES for a in ('x', 'z')})
    sv = shiver(t)
    if sv: spec = add(spec, {(b, a): chat.uniform(-sv, sv) for b in ('chest', 'neck', 'head', 'upper_arm.L', 'upper_arm.R') for a in ('x', 'z')})
    h.place(loc=(xy[0], xy[1], 0), yaw=math.radians(yaw)); h.pose(spec); settle(sup, lift)
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, h.yaw + je.z)
    n, bl, gz = face(t)
    h.expr(n, blink=bl, gaze=gz)
    h.key(f)

    # the set acts too: door ajar from the first frame, a creak, then banging open; the lamp stutters and dies
    ang = -9 - 8 * seg(t, 9.6, 9.9) - 30 * seg(t, 18.85, 18.95) - 12 * seg(t, 23.2, 24.2)
    hinge.rotation_euler = (0, 0, math.radians(ang)); key(hinge, f, rot=tuple(hinge.rotation_euler))
    door_l.data.energy = 0.08 + 0.05 * seg(t, 9.6, 9.9) + 0.25 * seg(t, 18.85, 18.95); door_l.data.keyframe_insert('energy', frame=f)
    show = 1.0 if t >= 24.2 else 1e-4
    blink_e = 0.15 if abs(t - 24.6) < 0.06 else 1.0
    for e in eyes: e.scale = (show, show * 0.5, show * 0.75 * blink_e); key(e, f, scale=tuple(e.scale))
    lit = 0.0 if (18.6 <= t < 18.7 or 18.78 <= t < 18.86 or t >= 23.4) else 1.0
    lamp.data.energy = 0.6 * lit * (1 + boil.r.uniform(-0.03, 0.03)); lamp.data.keyframe_insert('energy', frame=f)
    shade_em.default_value = 3.0 * lit + 0.05; shade_em.keyframe_insert('default_value', frame=f)
    key_l.data.energy = 3.2 * (1 + boil.r.uniform(-0.012, 0.012)) * (0.8 if t >= 23.4 else 1.0); key_l.data.keyframe_insert('energy', frame=f)

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
