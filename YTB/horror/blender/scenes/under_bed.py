"""Haru #2 "Something Under the Bed" (wordless, 9:16, about 17 s with the black tail added in post).

Haru comes into her room happily; a dark shape darts across the lit hallway behind her. She looks back, shrugs it off,
goes to bed, lies back, the lamp goes off. Eyes closed. Under the bed two eyes light up; a long thin hand slides out
and reaches for her face, closer and closer; her eyes snap open, a fast push into her face; black.

Same set, lights and clay puppet as scenes/haru_room_mocap.py (this file is generated from it by splicing: the set and
puppet code above, the story from scenes/under_bed_tail.py), with the bed raised so there is room under it.
blender -b -P scenes/under_bed.py -- [--still F] [--range A B] [--res 1080 1920] [--samples 64] [--out DIR]
"""
import bpy, sys, os, math, random, importlib.util
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import haru_puppet as HP
import haru_burton as HB
import haru_clay as HC
import burton_materials as BM
from claylib import *
spec = importlib.util.spec_from_file_location('story', os.path.join(HERE, '..', 'haru', 'test2_shot.py'))
ST = importlib.util.module_from_spec(spec); spec.loader.exec_module(ST)
seg, mix, add = ST.seg, ST.mix, ST.add

OPTS = cli('under_bed')
FPS, END = 12, 26.5
F = int(END * FPS)
reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=F)
HP.fast_cycles(sc)
world((0.02, 0.025, 0.045), 0.12)
sc.view_settings.exposure = -0.25
try: sc.view_settings.look = 'AgX - High Contrast'      # horror grade: deep blacks, hard falloff
except TypeError: pass

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
MATT, SEAT = 0.058, 0.027                       # mattress top, chair seat top
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
for o in (sky, moon): o.visible_shadow = False      # the moonlight behind them shines in through the window
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
box('bed_frame', bx0 - 0.004, bx1 + 0.004, by0 - 0.004, by1 + 0.004, MATT - 0.024, MATT - 0.01, WOOD, bevel=0.002)   # raised: room under it
for lx in (bx0, bx1):
    for ly in (by0, by1): box('bed_leg', lx - 0.004, lx + 0.004, ly - 0.004, ly + 0.004, 0, MATT - 0.022, WOOD, bevel=0.001)
box('headboard', bx0 - 0.012, bx0 - 0.004, by0 - 0.004, by1 + 0.004, 0, 0.115, WOOD, bevel=0.003)
for i in range(5):
    yy = by0 + (i + 0.5) * (by1 - by0) / 5
    box('headboard_spindle', bx0 - 0.01, bx0 - 0.006, yy - 0.002, yy + 0.002, 0.115, 0.145, WOOD, bevel=0.001)
box('headboard_top', bx0 - 0.013, bx0 - 0.003, by0 - 0.006, by1 + 0.006, 0.143, 0.149, WOOD, bevel=0.002)
m = box('mattress', bx0, bx1, by0, by1, MATT - 0.012, MATT, SHEET, bevel=0.005, coll=True); add_lumps(m, 0.0008, size=0.02)
pw = box('pillow', bx0 + 0.006, bx0 + 0.048, by0 + 0.02, by1 - 0.02, MATT - 0.002, MATT + 0.003, SHEET, bevel=0.004, coll=True)
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
# horror light: one cold motivated source (the moon through the window) throwing hard window-bar shadows through a
# thin haze, the small warm lamp as the only comfort, a faint low cool fill so her face just reads, a cold rim that
# cuts her silhouette out of the dark; no even front light
moon_l = area_light('moonlight', (-0.2, 0.5, 0.36), (-0.15, 0.08, 0.0), 26, 0.05, (0.55, 0.68, 1.0))
KEY_E = 1.5
key_l = area_light('key', (-0.18, -0.32, 0.06), (0, 0.05, 0.07), KEY_E, 0.2, (0.62, 0.72, 0.95))   # low, from below eye level
fill = area_light('fill', (0.35, -0.3, 0.12), (0, 0.05, 0.04), 0.12, 0.4, (0.5, 0.6, 0.9))
rim = area_light('rim', (0.3, 0.35, 0.25), (0, 0.05, 0.06), 3.0, 0.12, (0.6, 0.75, 1.0))
haze = bpy.data.materials.new('haze'); haze.use_nodes = True; hn = haze.node_tree.nodes
hn.remove(hn['Principled BSDF']); pv = hn.new('ShaderNodeVolumePrincipled')
pv.inputs['Density'].default_value = 0.9; pv.inputs['Anisotropy'].default_value = 0.55; pv.inputs['Color'].default_value = (0.8, 0.85, 1.0, 1)
haze.node_tree.links.new(pv.outputs[0], hn['Material Output'].inputs['Volume'])
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, (WY - 0.45) / 2, 0.2)); hz = bpy.context.object; hz.name = 'haze'
hz.scale = (0.62, WY + 0.43, 0.4); hz.data.materials.append(haze)
sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4.0
door_l = area_light('hall', ((d0 + d1) / 2, WY + 0.15, 0.1), ((d0 + d1) / 2, 0.0, 0.0), 0.0, 0.05, (0.62, 0.8, 0.5))   # sickly hall light

# ------------------------------------------------------------------ the puppet
h = HC.HaruClay(loc=(0.21, 0.25, 0), yaw=0.0)
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
        press = 0.003 if i == 1 else 0.0                     # the soft mattress gives under her: she lies in it, not on it
        if m.any(): off = max(off, top - press - float(W[m, 2].min()))
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
