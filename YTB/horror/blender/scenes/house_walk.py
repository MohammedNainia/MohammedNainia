"""Walking test: Haru walks through the whole house (library/sets/house) from her bedroom, out of her door, along the
upstairs hallway, down the stairs, through the hall and into the living room. The camera follows her through the
open front of the doll's house. Proves the route map (nav.py), the walker (puppets/walker.py) and the feet finding
the floor, the stair treads and the rugs.

    blender -b -P scenes/house_walk.py -- [--still F] [--range A B] [--res 1080 1920] [--samples 64] [--out DIR]
        [--from bedroom] [--to living_room]
"""
import bpy, os, sys, math, random
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
LIBSETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, os.path.join(LIBSETS, 'house')); sys.path.insert(0, LIBSETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
argv = sys.argv
A = argv[argv.index('--from') + 1] if '--from' in argv else 'bedroom'
B = argv[argv.index('--to') + 1] if '--to' in argv else 'living_room'
for k in ('--from', '--to'):
    if k in argv: i = argv.index(k); del argv[i:i + 2]
import kit as K
import house, nav, plan
import haru_clay as HC, mocap as MC, walker as WK
from claylib import cli, run, key, look_at, camera, constant_interp, Boil, seg

OPTS = cli('house_walk')
FPS = 12
sc = K.begin('house_walk', res=OPTS['res'], samples=OPTS['samples'], frames=1)
house.build()
h = HC.HaruClay(name='haru')
lib = MC.Library(os.path.join(HERE, '..', 'mocap', 'clips.npz'), h)
route, names = nav.route(A, B)
print('ROUTE', ' > '.join(names))
w = WK.Walker(lib, route, t0=0.6)
END = w.t_end + 1.2
F = int(END * FPS); sc.frame_start, sc.frame_end = 1, F
floor = WK.Floor()

cam = camera((0, -0.4, 0.3), (0, 0, 0.3), lens=30, fstop=8.0); cam.data.clip_start = 0.005
boil = Boil(5, amp=0.00012, rot=0.003)
chat = random.Random(4)
cs = None
for f in range(1, F + 1):
    t = (f - 1) / FPS
    W, xy, zh, yaw = w.at(t)
    h.root.location = (xy.x, xy.y, zh); h.root.rotation_euler = (0, 0, yaw)
    MC.apply(h, W, yaw)
    z = floor.place(h, W, yaw, zh)                               # feet on the floor, the treads, the rugs (leg IK)
    for pv in ('chest', 'neck', 'head'):
        e = h.P[pv]; a = 0.005
        e.rotation_euler = (e.rotation_euler.x + chat.uniform(-a, a), e.rotation_euler.y, e.rotation_euler.z + chat.uniform(-a, a))
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, yaw + je.z)
    h.expr('neutral', blink=any(abs(t - b) < 0.09 for b in (1.5, 4.8, 8.2, 11.6, 15.0)))
    h.key(f)
    # the camera: outside the open front, following her (smoothed), a little above her eyes
    p = Vector((xy.x, xy.y, z))
    cs = p.copy() if cs is None else cs.lerp(p, 0.18)
    loc = Vector((cs.x, -0.3 - 0.25 * max(0.0, cs.y - 0.2), cs.z + 0.085))
    tgt = Vector((cs.x, cs.y, cs.z + 0.06))
    cam.location = loc; look_at(cam, tgt); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = 30 + 18 * max(0.0, cs.y - 0.15); cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (loc - tgt).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    cam.data.dof.aperture_fstop = 8.0
print('FRAMES', F, 'END', round(END, 2))
constant_interp()
run(sc, OPTS)
