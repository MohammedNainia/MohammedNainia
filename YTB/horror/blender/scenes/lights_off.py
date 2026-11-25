"""Haru #3 "Lights Off" (wordless, 9:16, about 13 s with the black tail added in post).

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
