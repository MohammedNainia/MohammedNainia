"""Room test: the Burton Haru puppet moves around her bedroom (23 s, 276 frames at 12 fps, stop motion, vertical 9:16).

Asleep on her back in bed -> eyes open -> sits up -> swings her legs over the edge -> stands -> walks across the room,
glancing at the door -> sits on the chair -> close-up: six expressions -> the door creaks open behind her -> she jumps
up and runs back -> leaps onto the bed and hugs her knees -> the door swings wider -> two eyes in the dark doorway ->
she turns and stares into the lens.

Contact: every frame she is put on whatever is under her (floor, mattress, chair seat): for each support, the lowest
point of her meshes inside its footprint is found and she is lifted until nothing sinks into anything.
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
FPS, END = 12, 23.0
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
SUPPORTS = [((-9, 9, -9, 9), 0.0), (BED, MATT), (SEATR, SEAT)]


def world_verts():
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); out = []
    for ob in contact_obs:
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
        Mw = np.array(ev.matrix_world); out.append(co.reshape(-1, 3) @ Mw[:3, :3].T + Mw[:3, 3]); ev.to_mesh_clear()
    return np.concatenate(out)


def settle(supports=SUPPORTS, lift=0.0):
    """lift her so nothing sinks into any support under her"""
    h.root.location.z = 0.0
    W = world_verts(); best = -1.0
    for (x0, x1, y0, y1), top in supports:
        m = (W[:, 0] > x0) & (W[:, 0] < x1) & (W[:, 1] > y0) & (W[:, 1] < y1)
        if m.any(): best = max(best, top - float(W[m, 2].min()))
    h.root.location.z = best + lift


# poses (pivot, axis): degrees.  SITE: on an edge (bed or chair), thighs level, shins hanging
SITL = ST.SIT
SITE = {('thigh.L', 'x'): -90, ('thigh.R', 'x'): -90, ('shin.L', 'x'): 88, ('shin.R', 'x'): 88, ('chest', 'x'): 4,
        ('upper_arm.L', 'x'): -8, ('upper_arm.R', 'x'): -8, ('upper_arm.L', 'y'): -16, ('upper_arm.R', 'y'): 16,
        ('forearm.L', 'x'): -10, ('forearm.R', 'x'): -10, ('head', 'x'): 4}
SITC = {('thigh.L', 'x'): -90, ('thigh.R', 'x'): -90, ('shin.L', 'x'): 90, ('shin.R', 'x'): 90, ('chest', 'x'): 5,
        ('thigh.L', 'z'): 3, ('thigh.R', 'z'): -3,
        ('upper_arm.L', 'x'): -28, ('upper_arm.R', 'x'): -28, ('upper_arm.L', 'y'): 4, ('upper_arm.R', 'y'): -4,
        ('forearm.L', 'x'): -42, ('forearm.R', 'x'): -42, ('head', 'x'): 3}
PUSH = {('hips', 'x'): 32, ('thigh.L', 'x'): -100, ('thigh.R', 'x'): -100, ('shin.L', 'x'): 80, ('shin.R', 'x'): 80,
        ('foot.L', 'x'): -8, ('foot.R', 'x'): -8, ('head', 'x'): -22, ('chest', 'x'): 6,
        ('upper_arm.L', 'x'): -20, ('upper_arm.R', 'x'): -20, ('forearm.L', 'x'): -30, ('forearm.R', 'x'): -30}
STAND = {}
WALK_STRIDE, RUN_STRIDE = 0.072, 0.13           # puppet metres per cycle (two steps)


def trap(t, t0, t1, r=0.35):
    """0 -> 1 over [t0, t1] at constant speed with eased ramps (walks start and stop gently)"""
    if t <= t0: return 0.0
    if t >= t1: return 1.0
    T = t1 - t0; r = min(r, T / 2); v = 1.0 / (T - r)
    u = t - t0
    if u < r: return 0.5 * v / r * u * u
    if u > T - r: w = T - u; return 1.0 - 0.5 * v / r * w * w
    return 0.5 * v * r + v * (u - r)


def lerp2(a, b, u): return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


P_LIE, P_EDGE, P_UP = (-0.183, 0.12), (-0.15, 0.074), (-0.15, 0.035)
P_CHAIR_FRONT, P_CHAIR = (CHAIR[0], 0.004), (CHAIR[0], 0.05)
P_RUN0, P_RUN1, P_LAND = (0.08, -0.004), (-0.1, 0.03), (-0.165, 0.112)
TILTS = [(0, 0), (7, -3), (-6, 4), (0, -7), (5, 6), (-4, -5), (0, 0)]
PARADE = ['sad', 'smile', 'happy', 'surprised', 'suspicious', 'angry']


def beat(t, phase):
    """pose spec, root xy, yaw (deg), lift, supports override, stride"""
    sup, lift, stride = SUPPORTS, 0.0, WALK_STRIDE
    breath = math.sin(t * 2 * math.pi / 2.8)
    if t < 3.0: spec, xy, yaw = ST.LIE, P_LIE, 90
    elif t < 4.2: spec, xy, yaw = mix(ST.LIE, SITL, seg(t, 3.0, 4.1)), P_LIE, 90
    elif t < 5.4:
        u = seg(t, 4.2, 5.3); spec = mix(SITL, SITE, u); xy = lerp2(P_LIE, P_EDGE, u); yaw = 90 * (1 - u)
        spec = add(spec, {('head', 'z'): 20 * seg(t, 4.2, 4.6) - 20 * seg(t, 4.9, 5.3)})
    elif t < 6.5:
        spec = mix(SITE, PUSH, seg(t, 5.4, 5.8)) if t < 5.8 else mix(PUSH, STAND, seg(t, 5.8, 6.4))
        xy = lerp2(P_EDGE, P_UP, seg(t, 5.5, 6.3)); yaw = 0
    elif t < 7.0: spec, xy, yaw = STAND, P_UP, 90 * seg(t, 6.5, 6.95)
    elif t < 10.3:
        u = trap(t, 7.0, 10.3); xy = lerp2(P_UP, P_CHAIR_FRONT, u); yaw = 90
        w = seg(t, 7.0, 7.3) * (1 - seg(t, 10.0, 10.3))
        spec = mix(STAND, ST.walk(phase), w)
        g = seg(t, 8.3, 8.6) - seg(t, 9.1, 9.4)                           # glances at the door, ahead to her left
        spec = add(spec, {('head', 'z'): 38 * g, ('neck', 'z'): 12 * g, ('head', 'x'): -6 * g})
    elif t < 10.9: spec, xy, yaw = STAND, P_CHAIR_FRONT, 90 * (1 - seg(t, 10.3, 10.85))
    elif t < 11.9:
        u = seg(t, 10.95, 11.85); spec = mix(STAND, PUSH, min(1, u * 1.6)) if u < 0.6 else mix(PUSH, SITC, (u - 0.6) / 0.4)
        xy = lerp2(P_CHAIR_FRONT, P_CHAIR, seg(t, 11.0, 11.7)); yaw = 0
    elif t < 16.0:
        i = max(0, min(int((t - 12.4) / 0.6), len(TILTS) - 1)) if t >= 12.4 else 0
        spec = add(SITC, {('head', 'y'): TILTS[i][0], ('head', 'x'): TILTS[i][1]}); xy, yaw = P_CHAIR, 0
    elif t < 16.8:                                                         # creak: she twists toward the door
        g = seg(t, 16.05, 16.3)
        spec = add(SITC, {('head', 'z'): 62 * g, ('neck', 'z'): 18 * g, ('chest', 'z'): 16 * g, ('head', 'x'): -4 * g})
        xy, yaw = P_CHAIR, 0
    elif t < 17.4:
        u = seg(t, 16.8, 17.2); spec = mix(SITC, STAND, u); xy = lerp2(P_CHAIR, P_RUN0, u); yaw = -90 * seg(t, 16.9, 17.35)
    elif t < 18.6:
        u = trap(t, 17.4, 18.6, 0.25); xy = lerp2(P_RUN0, P_RUN1, u); yaw = -90; stride = RUN_STRIDE
        w = seg(t, 17.4, 17.6) * (1 - seg(t, 18.4, 18.6))
        spec = mix(STAND, ST.run(phase), w); lift = 0.0035 * abs(math.sin(2 * math.pi * phase)) * w
    elif t < 18.75: spec, xy, yaw = mix(STAND, ST.DIP, seg(t, 18.6, 18.75)), P_RUN1, -90
    elif t < 19.25:
        u = (t - 18.75) / 0.5
        spec = mix(ST.DIP, ST.JUMP, seg(u, 0, 0.3)) if u < 0.45 else mix(ST.JUMP, ST.HUG, seg(u, 0.45, 1.0))
        xy = lerp2(P_RUN1, P_LAND, seg(u, 0, 1)); yaw = -90 + 150 * seg(u, 0.1, 0.9)
        sup = [SUPPORTS[0]]; lift = 0.045 * 4 * u * (1 - u) + MATT * seg(u, 0, 1)
    else:
        spec, xy, yaw = ST.HUG, P_LAND, 60
        rock = math.sin((t - 19.3) * 2 * math.pi / 1.4) * (1 - seg(t, 21.9, 22.2))
        look = seg(t, 19.6, 19.9) * (1 - seg(t, 22.0, 22.25))             # watches the door, then turns to us
        spec = add(spec, {('hips', 'x'): 3 * rock, ('head', 'z'): 42 * look, ('neck', 'z'): 10 * look})
    spec = add(spec, {('chest', 'x'): 1.2 * breath * (0.6 if t < 4.2 else 1.0)})
    return spec, xy, yaw, lift, sup, stride


BLINKS = [4.6, 6.8, 9.6, 11.3, 16.9, 19.7, 22.6]


def face(t):
    if t < 2.2: n = 'sleep'
    elif t < 2.5: n = 'surprised'
    elif t < 5.4: n = 'worried'
    elif t < 8.4: n = 'neutral'
    elif t < 9.4: n = 'suspicious'
    elif t < 12.4: n = 'neutral' if t > 11.0 else 'relieved' if t > 10.4 else 'neutral'
    elif t < 16.0: n = PARADE[min(int((t - 12.4) / 0.6), len(PARADE) - 1)]
    elif t < 16.35: n = 'scared'
    elif t < 21.9: n = 'terrified' if (t < 19.6 or t > 21.0) else 'scared'
    else: n = 'stare'
    blink = any(abs(t - b) < 0.09 for b in BLINKS) and n not in ('sleep',)
    return n, blink


# ------------------------------------------------------------------ camera shots (stop-motion cuts)
cam = camera((0, -0.3, 0.09), (0, 0, 0.06), lens=35, fstop=5.6)
cam.data.clip_start = 0.005


def head_pt():
    return h.P['head'].matrix_world @ Vector((0, -0.012, 0.009))


def shot(t, hp, root, cx):
    """loc, target, lens, focus point, f-stop"""
    if t < 6.6:
        u = seg(t, 4.3, 6.4)
        tgt = Vector((-0.17, 0.11, 0.05)).lerp(hp + Vector((0, 0, -0.025)), u)
        return Vector((-0.13, -0.17, 0.08)).lerp(Vector((-0.12, -0.22, 0.085)), u), tgt, 38 - 4 * u, hp, 5.6
    if t < 12.4:
        tgt = Vector((cx, root.y + 0.02, 0.06)) if t < 10.9 else Vector((cx, root.y, 0.06)).lerp(hp + Vector((0, 0, -0.02)), seg(t, 10.9, 12.2))
        return Vector((cx + 0.02, -0.27, 0.088)), tgt, 32, hp, 5.6
    if t < 16.6:
        push = seg(t, 12.4, 16.0)
        return hp + Vector((0.012, -0.17, 0.003)), hp + Vector((0, 0, -0.006)), 58 + 12 * push, hp, 11.0
    if t < 19.4:
        return Vector((cx, -0.33, 0.1)), Vector((cx, 0.05, 0.05)), 30, hp, 6.0
    if t < 21.0:
        return Vector((0.0, -0.01, 0.085)), hp + Vector((0, 0, -0.02)), 40, hp, 5.6
    if t < 21.9:
        ep = Vector((d0 + 0.022, WY + 0.09, 0.112))
        return Vector((0.16, -0.05, 0.085)).lerp(Vector((0.175, -0.01, 0.09)), seg(t, 21.0, 21.9)), ep, 50, ep, 4.0
    d = Vector((math.sin(math.radians(60)), -math.cos(math.radians(60)), 0))
    return hp + d * 0.17 + Vector((0, 0, 0.004)), hp + Vector((0, 0, -0.006)), 62, hp, 11.0


# ------------------------------------------------------------------ animate
boil = Boil(5, amp=0.00018, rot=0.004)
chat = random.Random(7)
phase, prev_xy, cx, last_sid = 0.0, None, None, -1
for f in range(1, F + 1):
    t = (f - 1) / FPS
    spec0, xy, yaw, lift, sup, stride = beat(t, phase)
    if prev_xy is not None: phase += math.dist(xy, prev_xy) / stride
    prev_xy = xy
    spec, xy, yaw, lift, sup, stride = beat(t, phase)
    spec = add(spec, {(b, a): chat.uniform(-ST.CHATTER, ST.CHATTER) for b in ST.CHATTER_BONES for a in ('x', 'z')})
    h.place(loc=(xy[0], xy[1], 0), yaw=math.radians(yaw)); h.pose(spec); settle(sup, lift)
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, h.yaw + je.z)
    n, bl = face(t)
    h.expr(n, blink=bl)
    h.key(f)

    # set animation: the door creaks open, then wider; the hall light; eyes in the dark
    ang = -24 * seg(t, 16.0, 16.5) - 34 * seg(t, 19.8, 21.0)
    hinge.rotation_euler = (0, 0, math.radians(ang)); key(hinge, f, rot=tuple(hinge.rotation_euler))
    door_l.data.energy = 0.25 * seg(t, 16.0, 16.5) + 0.25 * seg(t, 19.8, 21.0); door_l.data.keyframe_insert('energy', frame=f)
    show = 1.0 if t >= 21.15 else 1e-4
    blink_e = 0.15 if abs(t - 21.6) < 0.06 else 1.0
    for e in eyes: e.scale = (show, show * 0.5, show * 0.75 * blink_e); key(e, f, scale=tuple(e.scale))
    lamp.data.energy = 0.6 * (1 + boil.r.uniform(-0.03, 0.03)); lamp.data.keyframe_insert('energy', frame=f)
    key_l.data.energy = 3.2 * (1 + boil.r.uniform(-0.012, 0.012)); key_l.data.keyframe_insert('energy', frame=f)

    bpy.context.view_layer.update()
    hp = head_pt(); root = h.root.location.copy()
    sid = sum(t >= c for c in (6.6, 12.4, 16.6, 19.4, 21.0, 21.9))       # which shot: snap the follow on each cut
    cx = root.x if (cx is None or sid != last_sid) else cx + (root.x - cx) * 0.35; last_sid = sid
    loc, tgt, lens, fp, fs = shot(t, hp, root, cx)
    cam.location = loc; look_at(cam, tgt); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.focus_distance = (loc - fp).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    cam.data.dof.aperture_fstop = fs; cam.data.dof.keyframe_insert('aperture_fstop', frame=f)

constant_interp()
run(sc, OPTS)
