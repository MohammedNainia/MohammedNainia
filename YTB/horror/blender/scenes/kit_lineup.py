"""Modular cast kit test: the Tripo heads snapped onto the Tripo bodies at the kit standard sizes, in channel clay
(haru_clay.apply_textured_clay), beside the Tripo Haru. Checks that every head fits every body at the neck.
blender -b -P scenes/kit_lineup.py -- --still 1 --res 1920 1080 --samples 64 --out DIR
Set KIT_CLOSE=1 for a close-up of the two child builds.
Prints NECK lines: head peg width / body neck width for each pair (1.0 = a perfect fit; under 0.85 or over 1.2 shows)."""
import bpy, sys, os, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, '..', 'library', 'kit')
sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import haru_clay as HC
from claylib import *

# kit standards (metres on our sets: Haru is 12.6 cm)
CHILD, WOMAN, MAN = 0.126, 0.165, 0.178
HEAD_FRAC = {'child': 0.27, 'adult': 0.19}     # head model (crown to the bottom of its neck peg) / total height
PEG = 0.35                                      # share of the head model's height that slides over the body's neck
SKIN = '#f3bf9f'                               # Haru's rendered face (her Tripo texture), lighter than PAL skin
YAW = -90                                       # Tripo GLBs import facing +x; turn them to face the camera (-y)


def load(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(KIT, name + '.glb'))
    obs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in [o for o in bpy.data.objects if o not in before and o.type != 'MESH']:
        bpy.data.objects.remove(o)
    o = obs[0]
    o.parent = None; o.rotation_euler = (0, 0, 0); o.location = (0, 0, 0); o.scale = (1, 1, 1)
    o.data.transform(o.matrix_basis); o.matrix_basis.identity()
    import mathutils
    o.data.transform(mathutils.Matrix.Rotation(math.radians(YAW), 4, 'Z'))
    o.name = name
    return o


def bounds(o):
    vs = [v.co for v in o.data.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)])
    return lo, hi


def width_at(o, z0, z1):
    xs = [v.co.x for v in o.data.vertices if z0 <= v.co.z <= z1]
    return (max(xs) - min(xs)) if xs else 0.0


def fit(o, height):
    """scale uniformly to this height, feet (lowest point) at z=0, centred on x/y"""
    lo, hi = bounds(o); k = height / (hi.z - lo.z)
    import mathutils
    o.data.transform(mathutils.Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)))
    o.data.transform(mathutils.Matrix.Scale(k, 4))


def character(head, body, total, kind, x, label):
    h, b = load(head), load(body)
    hh = HEAD_FRAC[kind] * total
    fit(h, hh)
    fit(b, total - hh * (1 - PEG))
    blo, bhi = bounds(b)
    neck_b = width_at(b, bhi.z - 0.04 * (bhi.z - blo.z), bhi.z)                 # body neck stump, top 4%
    neck_h = width_at(h, 0, 0.12 * hh)                                           # head peg, bottom 12%
    print(f'NECK {label}: head peg {neck_h * 1000:.1f} mm / body neck {neck_b * 1000:.1f} mm = {neck_h / max(neck_b, 1e-9):.2f}', flush=True)
    h.location = (x, 0, bhi.z - PEG * hh); b.location = (x, 0, 0)
    bpy.context.view_layer.update()
    HC.apply_textured_clay([h], name=label + '_head', height=total, skin=SKIN)   # one skin for every head (Haru's)
    HC.apply_textured_clay([b], name=label + '_body', height=total)
    return h, b


OPTS = cli('kit_lineup')
reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=1)
world((0.5, 0.5, 0.52), 0.12)
sc.view_settings.exposure = -0.4
backdrop = clay('backdrop', (0.32, 0.3, 0.29), rough=0.9, sss=0.0, bump=0.15, thumb=0.1, scale=2.0)
rounded_box('floor', (1.4, 0.5, 0.01), loc=(0, 0.08, -0.005), bevel=0.002, mat=backdrop)
bpy.ops.mesh.primitive_plane_add(size=1.6, location=(0, 0.3, 0.4), rotation=(math.pi / 2, 0, 0)); assign(bpy.context.object, backdrop)

X = [-0.36, -0.22, -0.075, 0.075, 0.22]
character('head_man', 'body_man', MAN, 'adult', X[0], 'man')
character('head_woman', 'body_woman', WOMAN, 'adult', X[1], 'woman')
haru = load('haru_full'); fit(haru, CHILD); haru.location = (X[2], 0, 0); HC.apply_textured_clay([haru], name='haru')
character('head_girl', 'body_child', CHILD, 'child', X[3], 'girl')
character('head_boy', 'body_child', CHILD, 'child', X[4], 'boy')

area_light('key', (-0.5, -0.6, 0.6), (0, 0, 0.08), 14.0, 0.4, (1.0, 0.9, 0.8))
area_light('fill', (0.6, -0.45, 0.3), (0, 0, 0.08), 4.0, 0.4, (0.75, 0.82, 1.0))
area_light('rim', (0.1, 0.45, 0.4), (0, 0, 0.1), 4.0, 0.3)
if os.environ.get('KIT_CLOSE') == '1':                         # close-up on the child heads and necks
    cam = camera((0.15, -0.32, 0.11), (0.15, 0, 0.1), lens=50, fstop=11.0, focus=0.32)
else:
    cam = camera((-0.07, -0.95, 0.1), (-0.07, 0, 0.085), lens=50, fstop=11.0, focus=0.95)
run(sc, OPTS)
