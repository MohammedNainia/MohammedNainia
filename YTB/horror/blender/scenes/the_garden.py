"""Haru #6 "The Sunflower in Our Garden" (wordless, 9:16, about 15.4 s, loops back to frame 0). Follows The Gathering.

Night, Haru's bedroom, the bedside lamp on. The giant sunflower's face is at the garden window. She gets up, crosses the
room and pulls the curtains shut. The streetlamp behind it throws its shadow on the curtains: the head tilts, like a dog
listening. Two more shadows rise beside it, villagers with candles. All three tilt their heads at once. She turns to us.

Same bedroom set and clay puppet as scenes/lights_off.py (this file is spliced: the set and puppet code from lights_off.py,
then the story from scenes/the_garden_tail.py, which adds the right-hand wall with the garden window).
blender -b -P scenes/the_garden.py -- [--stills a,b] [--range A B] [--res 1080 1920] [--samples 64] [--out DIR]
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

OPTS = cli('the_garden')
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
box('bed_frame', bx0 - 0.004, bx1 + 0.004, by0 - 0.004, by1 + 0.004, 0.008, MATT - 0.01, WOOD, bevel=0.002)
for lx in (bx0, bx1):
    for ly in (by0, by1): box('bed_leg', lx - 0.004, lx + 0.004, ly - 0.004, ly + 0.004, 0, 0.01, WOOD, bevel=0.001)
box('headboard', bx0 - 0.012, bx0 - 0.004, by0 - 0.004, by1 + 0.004, 0, 0.1, WOOD, bevel=0.003)
for i in range(5):
    yy = by0 + (i + 0.5) * (by1 - by0) / 5
    box('headboard_spindle', bx0 - 0.01, bx0 - 0.006, yy - 0.002, yy + 0.002, 0.1, 0.13, WOOD, bevel=0.001)
box('headboard_top', bx0 - 0.013, bx0 - 0.003, by0 - 0.006, by1 + 0.006, 0.128, 0.134, WOOD, bevel=0.002)
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
h = HC.HaruClay(loc=(0.11, 0.18, 0), yaw=3.14159)
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


# ------------------------------------------------------------------ Haru #6 "The Sunflower in Our Garden": the story
import bmesh
import mocap as MC
LIB = MC.Library(os.path.join(HERE, '..', 'mocap', 'clips.npz'), h)
K = LIB.k
END = 15.4                      # no black tail: the last frame cuts back to frame 0 (the loop)
F = int(END * FPS); sc.frame_end = F
for e in eyes: e.hide_render = True
hinge.rotation_euler = (0, 0, math.radians(-1))                    # the bedroom door is shut
for o in list(bpy.data.objects):                                    # no chair in this story
    if o.name.split('.')[0] in ('seat', 'chair_leg', 'chair_post', 'chair_rail', 'chair_rail2'):
        bpy.data.objects.remove(o, do_unlink=True)


def ezs(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


def turn2(v, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)); return Vector((c * v.x - s * v.y, s * v.x + c * v.y))


def attach(ob, par, local=(0, 0, 0)):
    ob.parent = par; ob.matrix_parent_inverse = Matrix.Identity(4); ob.location = local; return ob


# ------------------------------------------------------------------ the room: a ceiling, and a right-hand wall with the garden window
CEIL_Z = 0.25
box('ceiling', WX0 - 0.01, WX1, -0.45, WY + 0.005, CEIL_Z, CEIL_Z + 0.01, painted('ceiling', (0.2, 0.2, 0.19)), bevel=0.0005)
XW = 0.30                                                           # the right wall's inner face; outside is +x
GY0, GY1, GZ0, GZ1 = -0.02, 0.17, 0.075, 0.215                          # the garden window: y from, to; z from, to
GYC, GZC = (GY0 + GY1) / 2, (GZ0 + GZ1) / 2
WIN_C = Vector((XW, GYC, GZC))
for a in ((-0.45, GY0, 0, CEIL_Z), (GY1, WY + 0.005, 0, CEIL_Z), (GY0, GY1, 0, GZ0), (GY0, GY1, GZ1, CEIL_Z)):
    box('wall_right', XW, XW + 0.01, a[0], a[1], a[2], a[3], WALL, bevel=0.0005)
box('skirting_r', XW - 0.004, XW, -0.45, WY - 0.004, 0, 0.012, TRIM, bevel=0.001)
for a in ((GY0 - 0.006, GY0, GZ0 - 0.006, GZ1 + 0.006), (GY1, GY1 + 0.006, GZ0 - 0.006, GZ1 + 0.006),
          (GY0, GY1, GZ0 - 0.006, GZ0), (GY0, GY1, GZ1, GZ1 + 0.006), (GYC - 0.002, GYC + 0.002, GZ0, GZ1),
          (GY0, GY1, GZC - 0.002, GZC + 0.002)):
    box('gwin_frame', XW - 0.002, XW + 0.008, a[0], a[1], a[2], a[3], TRIM, bevel=0.0008)
box('gwin_sill', XW - 0.02, XW, GY0 - 0.012, GY1 + 0.012, GZ0 - 0.009, GZ0 - 0.005, TRIM, bevel=0.001)

# ------------------------------------------------------------------ curtains that close: thin cream cloth the streetlamp shines through
CURT = bpy.data.materials.new('curtain_thin'); CURT.use_nodes = True
cn, cl = CURT.node_tree.nodes, CURT.node_tree.links
pb = cn['Principled BSDF']; pb.inputs['Base Color'].default_value = (0.5, 0.4, 0.27, 1); pb.inputs['Roughness'].default_value = 0.95
tr = cn.new('ShaderNodeBsdfTranslucent'); tr.inputs['Color'].default_value = (0.95, 0.8, 0.55, 1)
mxs = cn.new('ShaderNodeMixShader'); mxs.inputs[0].default_value = 0.55
cl.new(pb.outputs[0], mxs.inputs[1]); cl.new(tr.outputs[0], mxs.inputs[2])
cl.new(mxs.outputs[0], cn['Material Output'].inputs['Surface'])
CW = (GY1 - GY0) / 2 + 0.016                                        # each panel, closed, reaches just past the middle
CZ0, CZ1 = GZ0 - 0.012, GZ1 + 0.012
ANC_A, ANC_B = GY1 + 0.012, GY0 - 0.012                             # fixed outer edges: A on her left (+y), B on her right
OPEN_A, OPEN_B = GY1 - 0.02, GY0 + 0.02                             # the leading edges when open


def curtain_panel(name, anchor, sign):
    """a hanging panel of soft vertical folds in the y-z plane; its origin is the fixed outer edge, it grows along y"""
    bm = bmesh.new(); nx, nz = 48, 10; rows = []
    for i in range(nx + 1):
        u = i / nx; yy = sign * u * CW; xx = 0.0022 * math.sin(u * CW * 2 * math.pi / 0.011)
        rows.append([bm.verts.new((xx, yy, CZ0 + (CZ1 - CZ0) * k / nz)) for k in range(nz + 1)])
    for i in range(nx):
        for k in range(nz):
            q = (rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1])
            bm.faces.new(q if sign < 0 else q[::-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); me.materials.append(CURT)
    ob.location = (XW - 0.015, anchor, 0.0)
    sol = ob.modifiers.new('cloth', 'SOLIDIFY'); sol.thickness = 0.0006
    return ob


cur_a, cur_b = curtain_panel('curtain_a', ANC_A, -1), curtain_panel('curtain_b', ANC_B, 1)
box('gcurtain_rod', XW - 0.02, XW - 0.016, GY0 - 0.025, GY1 + 0.025, GZ1 + 0.014, GZ1 + 0.018, WOOD, bevel=0.001)


def set_curtains(closed, f):
    """closed 0..1: the leading edges travel from open to just past the middle; returns their y"""
    ea = OPEN_A + (GYC - 0.004 - OPEN_A) * closed; eb = OPEN_B + (GYC + 0.004 - OPEN_B) * closed
    cur_a.scale = (1, (ANC_A - ea) / CW, 1); cur_b.scale = (1, (eb - ANC_B) / CW, 1)
    key(cur_a, f, scale=tuple(cur_a.scale)); key(cur_b, f, scale=tuple(cur_b.scale))
    return ea, eb


# ------------------------------------------------------------------ outside: night sky, the streetlamp behind the flower
gsky = box('garden_sky', XW + 0.75, XW + 0.76, -0.6, 0.7, -0.4, 0.6, emissive('garden_night', (0.04, 0.06, 0.16), 0.15), bevel=0); gsky.visible_shadow = False
LAMP_P = Vector((XW + 0.7, GYC, GZC - 0.005))
street = bpy.data.lights.new('streetlamp', 'SPOT'); street.energy = 200.0; street.spot_size = math.radians(34)
street.spot_blend = 0.25; street.shadow_soft_size = 0.002; street.color = (0.72, 0.82, 1.0)
st = bpy.data.objects.new('streetlamp', street); bpy.context.collection.objects.link(st); st.location = LAMP_P
look_at(st, WIN_C)
bulb = sphere('street_bulb', 0.008, tuple(LAMP_P + Vector((0.01, 0, 0))), mat=emissive('street_bulb', (0.8, 0.88, 1.0), 25.0))
bulb.visible_shadow = False
pv.inputs['Density'].default_value = 0.35                            # thinner haze than Lights Off: the window light stays clean
hair_l = area_light('hair_rim', (-0.11, 0.21, 0.16), (-0.175, 0.12, 0.1), 0.6, 0.05, (1.0, 0.68, 0.4))   # the lamp's warmth on her hair

# ------------------------------------------------------------------ the sunflower (the Gathering's flower, at about a quarter of the size)
import clay_v3 as CV                                                # real plasticine, not paint: prints, dents, a waxy film
def fclay(name, c, **kw): return CV.clay(name, c, size=SF, **kw)   # modelled big, shown at SF: keep the marks thumb-sized
SF = 0.24
STEM = fclay('sf_stem', (0.05, 0.08, 0.03), bump=0.7)
SEEDS = fclay('sf_seeds', (0.1, 0.058, 0.024), bump=0.9, specks=2.0)
PETAL = fclay('sf_petal', (0.45, 0.31, 0.05), bump=0.6)
VOIDC = painted('sf_void', (0.0, 0.0, 0.0), rough=1.0)
coll = bpy.context.collection


def piece(name, s, mat, voxel=0.0012, smooth=3):
    ob = HP.piece(name, s, mat, 'top', coll, voxel=voxel, smooth=smooth, lump=0)
    ob.data.transform(Matrix.Scale(1 / HP.S, 4)); return ob


HEAD_P = Vector((XW + 0.035, GYC, GZC + 0.005))                      # the head, just outside the window, looking in (-x)
sf = empty('sunflower', (HEAD_P.x + 0.075 * SF, HEAD_P.y, HEAD_P.z - 0.86 * SF))
sf.scale = (SF, SF, SF); sf.rotation_euler = (0, 0, -math.pi / 2)    # its local -y (the face) now looks along -x
s = HP.Shape()
pts = [Vector((0, 0, -0.4)), Vector((0.008, 0.004, 0.2)), Vector((-0.006, 0, 0.6)), Vector((0, 0, 0.86))]
for a, b, r0, r1 in zip(pts, pts[1:], (0.017, 0.015, 0.013), (0.015, 0.013, 0.011)): s.capsule(a, b, r0, r1, 16)
attach(piece('sf_stem', s, STEM, voxel=0.002), sf)
s = HP.Shape().ellipsoid((0.07, 0.0, -0.02), (0.065, 0.032, 0.006), rot=(0.5, -0.35, 0.3))
attach(piece('sf_leaf', s, STEM, voxel=0.0015), sf, (0, 0, 0.62))
sf_head = attach(empty('sf_head_pivot'), sf, (0, 0, 0.86))
sf_face = attach(empty('sf_face'), sf_head, (0, -0.075, 0))
s = HP.Shape().ellipsoid((0, 0.03, 0), (0.12, 0.03, 0.12)).capsule((0, 0.03, 0), (0, 0.078, -0.012), 0.02, 0.014)
attach(piece('sf_back', s, STEM, voxel=0.002), sf_face)
disc = piece('sf_disc', HP.Shape().ellipsoid((0, -0.004, 0), (0.112, 0.026, 0.112)), SEEDS, voxel=0.0015)
add_lumps(disc, 0.002, size=0.006); attach(disc, sf_face)
rl = random.Random(3); s = HP.Shape()
for layer, (n, rr, yy, droop) in enumerate(((24, 0.148, 0.006, 0.15), (24, 0.142, 0.016, 0.3))):
    for i in range(n):
        a = 2 * math.pi * (i + 0.5 * layer) / n + rl.uniform(-0.04, 0.04)
        c = Vector((math.cos(a) * rr, yy, math.sin(a) * rr))
        s.ellipsoid(c, (0.045 * rl.uniform(0.85, 1.1), 0.005, 0.015), rot=(droop * math.sin(a), -a, 0))
petals = piece('sf_petals', s, PETAL, voxel=0.0015); add_lumps(petals, 0.0025, size=0.012); attach(petals, sf_face)
s = HP.Shape()
for sx in (-1, 1): s.ellipsoid((sx * 0.042, -0.027, 0.028), (0.024, 0.008, 0.011), rot=(0, sx * 0.45, 0))
attach(piece('sf_eyes', s, VOIDC, voxel=0.001), sf_face)
s = HP.Shape()
for sx in (-1, 1): s.capsule((sx * 0.012, -0.03, 0.045), (sx * 0.074, -0.026, 0.072), 0.006, 0.005, 12)
brow = piece('sf_brow', s, SEEDS, voxel=0.001); add_lumps(brow, 0.0015, size=0.004); attach(brow, sf_face)
s = HP.Shape()
for i in range(17):
    xx = -0.075 + i * 0.15 / 16
    for zz in (-0.05 + 0.032 * (xx / 0.075) ** 2, -0.052 + 0.032 * (xx / 0.075) ** 2): s.ball((xx, -0.028, zz), 0.006, 12)
attach(piece('sf_mouth', s, VOIDC, voxel=0.001), sf_face)
face_warm = point_light('flower_face_light', (XW - 0.045, GYC + 0.01, GZC - 0.075), 0.45, radius=0.008, color=(1.0, 0.6, 0.3))   # low: lit from below
GLINT = emissive('sf_glint', (1.0, 0.82, 0.55), 4.0)
for sx in (-1, 1):                                                  # two glints in the hollow eyes: it is looking at her
    attach(sphere('sf_pupil', 0.0034, mat=GLINT), sf_face, (sx * 0.036, -0.035, 0.026))

# ------------------------------------------------------------------ two villagers from the Gathering, outside, below the sill
SKIN = CV.clay('vl_skin', (0.46, 0.34, 0.27), sss=0.1)
HAIR = CV.clay('vl_hair_dark', (0.025, 0.018, 0.014), grooves=0.3)
COAT = CV.clay('vl_coat', (0.05, 0.05, 0.06), bump=0.7)
WAX = painted('vl_wax', (0.6, 0.56, 0.45), rough=0.5)
FLAME = emissive('vl_flame', (1.0, 0.62, 0.25), 18.0)


def villager(name, p, v):
    s = HP.Shape(); top = 0.135
    if v == 1: s.capsule((0, 0, 0.03), (0, 0, top), 0.025, 0.018, 16)
    else: s.capsule((0, 0, 0.03), (0, 0, top), 0.019, 0.021, 16)
    s.ellipsoid((0, 0, top), (0.024, 0.016, 0.012)).capsule((0, 0, top), (0, 0, top + 0.012), 0.005, 0.005, 12)
    for sx in (-1, 1):
        sh = Vector((sx * 0.022, 0, top - 0.003)); el = Vector((sx * 0.02, -0.012, top - 0.035)); hd = Vector((sx * 0.005, -0.031, top - 0.03))
        s.capsule(sh, el, 0.0055, 0.005, 12).capsule(el, hd, 0.005, 0.0042, 12)
    hold = empty(name, tuple(p)); hold.rotation_euler = (0, 0, -math.pi / 2); hold.scale = (VS, VS, VS)   # facing the window (-x)
    body = piece(name + '_body', s, COAT, voxel=0.0008); add_lumps(body, 0.0008, size=0.008); attach(body, hold)
    neck = attach(empty(name + '_neck'), hold, (0, 0, top + 0.012))
    sk = HP.Shape().ellipsoid((0, 0, 0.012), (0.0105, 0.0115, 0.0125)).ellipsoid((0, -0.0105, 0.009), (0.0022, 0.003, 0.0035))
    hr = HP.Shape().ellipsoid((0, 0.002, 0.016), (0.0116, 0.0122, 0.0105)) if v == 0 else \
        HP.Shape().ellipsoid((0, 0.002, 0.016), (0.0118, 0.0124, 0.011)).ball((0, 0.011, 0.02), 0.006)
    attach(piece(name + '_head', sk, SKIN, voxel=0.0007), neck); attach(piece(name + '_hair', hr, HAIR, voxel=0.0007), neck)
    cz = top - 0.04
    attach(cylinder(name + '_candle', 0.0028, 0.02, mat=WAX), hold, (0, -0.033, cz + 0.008))
    attach(sphere(name + '_flame', 0.0022, scale=(1, 1, 1.8), mat=FLAME), hold, (0, -0.033, cz + 0.022))
    lt = point_light(name + '_candle_light', (0, 0, 0), 0.25, radius=0.002, color=(1.0, 0.6, 0.3)); attach(lt, hold, (0, -0.036, cz + 0.026))
    return hold, neck


VX, VS = XW + 0.06, 1.15                                            # a little bigger, so their shadows read as people
VZ_DOWN, VZ_UP = -0.22, GZC - 0.18                                  # below the sill -> heads and shoulders in the window
VILL = [villager('villager_a', (VX, GYC + 0.068, VZ_DOWN), 0), villager('villager_b', (VX, GYC - 0.068, VZ_DOWN), 1)]

# ------------------------------------------------------------------ Haru: sits up in bed, gets up, crosses to the window
P_LIE, P_EDGE = Vector((-0.183, 0.12)), Vector((-0.15, 0.074))
P_WIN = Vector((XW - 0.04, GYC - 0.004))
SEGS = [
    dict(t0=0.0, t1=1.3, clip='getup_from_back', c0=4.22, c1=4.35, yaw=90, at=P_LIE),         # sitting up in bed, facing the window
    dict(t0=1.3, t1=2.3, clip='sit_to_stand', c0=0.0, c1=0.0, yaw=0, at=P_EDGE, fade=0.9),      # swings round to the edge
    dict(t0=2.3, t1=3.9, clip='sit_to_stand', c0=0.0, c1=2.27, yaw=0, fade=0.0),
    dict(t0=3.9, t1=5.9, clip='walk', c0=0.0, loop=True, to=P_WIN, fade=0.35),
    dict(t0=5.9, t1=9.8, clip='look_behind', c0=0.1, c1=0.25, yaw=90, fade=0.4),             # at the window
    dict(t0=9.8, t1=10.8, clip='crouch_walk_back', c0=0.0, c1=1.0, yaw=90, fade=0.3),         # one step back
    dict(t0=10.8, t1=13.4, clip='look_behind', c0=0.1, c1=0.3, yaw=90, fade=0.3),
    dict(t0=13.4, t1=END, clip='terrified', c0=0.2, c1=1.4, yaw=-55, fade=0.5),                # turns to us
]


def resolve():
    end = None
    for s in SEGS:
        s.setdefault('fade', 0.3); s.setdefault('mirror', False); s.setdefault('loop', False)
        start = Vector(s['at']) if 'at' in s else end
        if 'to' in s:
            d = Vector(s['to']) - start
            s['yaw'] = math.degrees(math.atan2(d.x, -d.y))
            H = LIB.clips[s['clip']][1]; T = LIB.length(s['clip'])
            v = K * (Vector(H[-1][:2]) - Vector(H[0][:2])).length / T
            s['c1'] = s['c0'] + d.length / v
        s.setdefault('c1', s['c0'] + (s['t1'] - s['t0']))
        s['start'] = start
        dh = LIB.hips(s['clip'], s['c1'], s['mirror'], s['loop']) - LIB.hips(s['clip'], s['c0'], s['mirror'], s['loop'])
        end = start + turn2(Vector((dh.x, dh.y)) * K, s['yaw'])
        print('SEG', s['clip'], 'start', tuple(round(c, 3) for c in start), 'end', tuple(round(c, 3) for c in end), 'c1', round(s['c1'], 2))


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
    s = SEGS[i]; W, xy = eval_seg(s, t); yaw = s['yaw']
    if i > 0 and s['fade'] > 0 and t < s['t0'] + s['fade']:
        k = seg(t, s['t0'], s['t0'] + s['fade'])
        Wp, xyp = eval_seg(SEGS[i - 1], t)
        W = MC.blend(Wp, W, k); xy = xyp.lerp(xy, k)
        dy = (yaw - SEGS[i - 1]['yaw'] + 180) % 360 - 180; yaw = SEGS[i - 1]['yaw'] + dy * k
    return W, xy, yaw


# both hands to the curtain edges and pull them shut
T_REACH, T_YANK, T_YANK1, T_DROP = 6.2, 6.9, 7.2, 7.7


def closed_at(t): return ezs((t - T_YANK) / (T_YANK1 - T_YANK))


def reach_w(t): return ezs((t - T_REACH) / 0.5) * (1 - ezs((t - T_DROP) / 0.45))


ARM = {}
for sd in ('L', 'R'):
    ra, rf, rh = h.rest['upper_arm.' + sd], h.rest['forearm.' + sd], h.rest['hand.' + sd]
    ARM[sd] = ((rf - ra), (rh - rf))
POLE = {'L': Vector((0, 0.4, -1)), 'R': Vector((0, -0.4, -1))}      # elbows out and down (she faces +x: her left is +y)


def aim_arms(W, yaw, t, targets):
    w = reach_w(t)
    if w <= 0: return W
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
        for pv, q in (('upper_arm.' + sd, q_up), ('forearm.' + sd, q_fo), ('hand.' + sd, q_fo)):
            a = W[pv]; b = q if a.dot(q) >= 0 else -q
            W[pv] = a.slerp(b, w)
    return W


def face(t):
    if t < 1.3: n = 'stare'
    elif t < 5.9: n = 'worried'
    elif t < 7.7: n = 'scared'
    elif t < 8.3: n = 'worried'
    elif t < 13.4: n = 'stare' if t < 10.6 else 'scared'
    else: n = 'terrified'
    return n, any(abs(t - b) < 0.09 for b in (2.6, 5.0, 8.1, 10.2)), None


# ------------------------------------------------------------------ cameras
cam = camera((0, -0.3, 0.09), (0, 0, 0.06), lens=30, fstop=8.0)
cam.data.clip_start = 0.002


def head_pt(): return h.P['head'].matrix_world @ Vector((0, -0.012, 0.009))
def face_dir(): return (h.P['head'].matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def shot(t, hp):
    if t < 1.3:                         # frame 0: what she sees from her bed, the flower's face big in the window
        return Vector((-0.125, 0.115, 0.108)), HEAD_P + Vector((0, 0, -0.006)), 64, HEAD_P, 8.0
    if t < 6.2:                         # the room, wide from the front-left corner: the bed, the window; she crosses
        return Vector((-0.28, -0.3, 0.13)), Vector((0.0, 0.11, 0.09)), 22, Vector((0.05, 0.1, 0.08)), 8.0
    if t < 7.3:                         # over her right shoulder: hands on the curtains, the face behind them
        return Vector((XW - 0.13, GYC - 0.075, GZC - 0.005)), WIN_C + Vector((0, 0.005, -0.01)), 30, WIN_C, 8.0
    if t < 13.4:                        # behind her, high: the glowing curtains and the shadows, a slow push
        u = seg(t, 7.3, 13.4)
        return Vector((XW - 0.34 + 0.06 * u, GYC, 0.185)), WIN_C, 26, WIN_C, 8.0
    loc = hp + face_dir() * 0.085 + Vector((0, 0, 0.004))           # she turns: her face
    return loc, hp, 45, hp, 8.0


# ------------------------------------------------------------------ animate
boil = Boil(5, amp=0.00012, rot=0.003)
chat = random.Random(11)
for f in range(1, F + 1):
    t = (f - 1) / FPS
    W, xy, yawd = performance(t); yaw = math.radians(yawd)
    h.root.location = (xy.x, xy.y, h.root.location.z); h.root.rotation_euler = (0, 0, yaw)
    ea, eb = set_curtains(closed_at(t), f)
    hand_z = GZC + 0.002
    W = aim_arms(W, yaw, t, {'L': Vector((XW - 0.02, ea + 0.002, hand_z)), 'R': Vector((XW - 0.02, eb - 0.002, hand_z))})
    MC.apply(h, W, yaw)
    for pv in ('chest', 'neck', 'head'):
        e = h.P[pv]; a = 0.006 + (0.02 if t >= 8.3 else 0.0)
        e.rotation_euler = (e.rotation_euler.x + chat.uniform(-a, a), e.rotation_euler.y, e.rotation_euler.z + chat.uniform(-a, a))
    settle(SUPPORTS)
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, yaw + je.z)
    n, bl_, gz = face(t); h.expr(n, blink=bl_, gaze=gz); h.key(f)

    # the flower: taps the glass at once, later tilts its head like a dog listening, then all three tilt the other way
    tap = math.sin(math.pi * seg(t, 0.1, 0.4)) * math.radians(9)
    roll = math.radians(24) * ezs((t - 8.3) / 1.1) - math.radians(44) * ezs((t - 12.8) / 0.3)
    sf_head.rotation_euler = (tap, roll, 0); key(sf_head, f, rot=tuple(sf_head.rotation_euler))
    street.energy = 40.0 + 160.0 * closed_at(t); street.keyframe_insert('energy', frame=f)   # soft while the window is open
    hz.hide_render = t < 1.3; hz.keyframe_insert('hide_render', frame=f)                  # frame 0: no haze, the face crisp
    rise = ezs((t - 10.6) / 1.6)
    for k_, (hold, neck) in enumerate(VILL):
        hold.location.z = VZ_DOWN + (VZ_UP - VZ_DOWN) * rise + boil.r.uniform(-0.0004, 0.0004) * rise
        key(hold, f, loc=tuple(hold.location))
        neck.rotation_euler = (0, -math.radians(22) * ezs((t - 12.8) / 0.3) * (1 if k_ == 0 else 1.1), 0)
        key(neck, f, rot=tuple(neck.rotation_euler))
    lamp.data.energy = 0.6 * (1 + boil.r.uniform(-0.03, 0.03)); lamp.data.keyframe_insert('energy', frame=f)
    key_l.data.energy = KEY_E * (1 + boil.r.uniform(-0.012, 0.012)); key_l.data.keyframe_insert('energy', frame=f)

    bpy.context.view_layer.update()
    hp = head_pt()
    loc, tgt, lens, fp, fs = shot(t, hp)
    cam.location = loc; look_at(cam, tgt); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.focus_distance = (loc - fp).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    cam.data.dof.aperture_fstop = fs; cam.data.dof.keyframe_insert('aperture_fstop', frame=f)

constant_interp()
run(sc, OPTS)
