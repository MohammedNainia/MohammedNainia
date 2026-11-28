"""Clay match check: an imported Haru model (Artlist GLB) beside the code puppet, both in THE Haru clay
(haru_clay.apply_haru_clay / haru_materials) under the same clay key. Run it on every new imported Haru.
blender -b -P scenes/haru_clay_match.py -- --still 1 --res 1080 1920 --samples 64 --out DIR [--glb PATH] [--yaw DEG] [--solo]
--glb: the model to check (default: the first Artlist Haru, YTB/horror/three/data/lib/chars/haru.glb)
--solo: only the imported model, close up.
Prints the face count per part so a wrong sort (skin read as hoodie, etc.) shows up before any render."""
import bpy, sys, os, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
argv = sys.argv
GLB = os.path.join(ROOT, 'YTB', 'horror', 'three', 'data', 'lib', 'chars', 'haru.glb')
if '--glb' in argv: i = argv.index('--glb'); GLB = argv[i + 1]; del argv[i:i + 2]
SOLO = '--solo' in argv
YAW = 0.0
if '--yaw' in argv: i = argv.index('--yaw'); YAW = float(argv[i + 1]); del argv[i:i + 2]
if SOLO: argv.remove('--solo')
import haru_clay as HC
from claylib import *

H = 0.126                                                     # Haru is 12.6 cm on our sets
OPTS = cli('haru_clay_match')
reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=1)
world((0.5, 0.5, 0.52), 0.12)
sc.view_settings.exposure = -0.4

backdrop = clay('backdrop', (0.32, 0.3, 0.29), rough=0.9, sss=0.0, bump=0.15, thumb=0.1, scale=2.0)
rounded_box('floor', (0.6, 0.4, 0.01), loc=(0, 0.05, -0.005), bevel=0.002, mat=backdrop)
bpy.ops.mesh.primitive_plane_add(size=0.8, location=(0, 0.25, 0.3), rotation=(math.pi / 2, 0, 0)); assign(bpy.context.object, backdrop)

# ---- the imported model: scale to 12.6 cm, feet on the floor, facing the camera (-y), then THE clay
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
imp = [o for o in bpy.data.objects if o not in before]
root = bpy.data.objects.new('imported_haru', None); bpy.context.collection.objects.link(root)
for o in imp:
    if o.parent is None: o.parent = root
root.rotation_euler.z = math.radians(YAW)                      # --yaw: turn a model that was exported facing sideways
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in imp if o.type == 'MESH' for c in o.bound_box]
lo, hi = Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
k = H / (hi.z - lo.z)
root.scale = (k, k, k)
X_IMP = 0.0 if SOLO else 0.055                                 # glTF front (+Z) imports as -y: already faces the camera
cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
root.location = (X_IMP - cx * k, -cy * k, -lo.z * k)
bpy.context.view_layer.update()
for o in imp:                                                  # bake the scale so the clay marks are sized in true metres
    if o.type == 'MESH':
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
        bpy.context.view_layer.objects.active = o
        for s in bpy.context.view_layer.objects: s.select_set(False)
        o.select_set(True); bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        o.data.shade_smooth() if hasattr(o.data, 'shade_smooth') else None
count = HC.apply_haru_clay(imp, name='haru_imp')
print('PARTS', count, flush=True)

# ---- the code puppet beside it, same recipe
head_pts = []
if not SOLO:
    h = HC.HaruClay(loc=(-0.055, 0, 0), yaw=0, name='haru'); h.pose({}); h.ground(floor=0.0); h.expr('neutral'); h.key(1)
    head_pts.append(Vector((-0.055, 0, 0.106)))
head_pts.append(Vector((X_IMP, 0, 0.106)))

# ---- lights: soft key + fill, and the clay key on each head from the lamp side (camera left)
area_light('key', (-0.35, -0.4, 0.45), (0, 0, 0.06), 6.0, 0.25, (1.0, 0.9, 0.8))
area_light('fill', (0.4, -0.3, 0.2), (0, 0, 0.06), 1.5, 0.3, (0.75, 0.82, 1.0))
area_light('rim', (0.1, 0.35, 0.3), (0, 0, 0.07), 2.0, 0.15)
if SOLO:
    cam = camera((0, -0.2, 0.1), (0, 0, 0.08), lens=70, fstop=5.6, focus=0.2)
else:
    cam = camera((0, -0.42, 0.085), (0, 0, 0.065), lens=50, fstop=8.0, focus=0.42)
for hp in head_pts:
    HC.ClayRake().aim(1, hp, cam.location, Vector((-0.3, -0.2, 0.2)), on=True)
run(sc, OPTS)
