"""Haru #7 "Don't Open Your Door" (generated: the bedroom and puppet from lights_off.py + scenes/dont_open_tail.py).

Haru at the light switch. Off: two pale eyes in the corner. On: nothing. Off: it is crouched on the ceiling above
her bed. On: only a dent in the bed. Off: nothing at all. She reaches for the switch in the dark and her fingers land
on long black fingers already resting on it. On: it is right beside her. Off. Black.

Same set, lights and clay puppet as scenes/haru_room_mocap.py (this file is generated from it by splicing: the set and
puppet code above, the story from scenes/lights_off_tail.py), plus a ceiling, a wall switch and a rug by the door.
blender -b -P scenes/lights_off.py -- [--still F] [--range A B] [--res 1080 1920] [--samples 64] [--out DIR]
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

OPTS = cli('lights_off')
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
