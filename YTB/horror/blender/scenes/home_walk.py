"""Walking test in the big home (library/sets/home): Haru walks a route from the route map (home/nav.py), for example
from her bed, out of her room, along the landing, down the main stairs and through the hall into the kitchen.
Filmed like a movie: every room has its own camera (home/shots.py), set inside the room near its front corner andlooking deeper in; it pans after her and cuts to the next room's camera when she walks through a door.

    blender -b -P scenes/home_walk.py -- [--still F] [--range A B] [--res 1080 1920] [--samples 64] [--out DIR]
        [--from haru_bed] [--to kitchen] [--via a,b]
"""
import bpy, os, sys, random
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
SETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, os.path.join(SETS, 'home')); sys.path.insert(0, SETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
argv = sys.argv
def take(k, d):
    if k not in argv: return d
    i = argv.index(k); v = argv[i + 1]; del argv[i:i + 2]; return v
A, B_, VIA = take('--from', 'haru_bed'), take('--to', 'kitchen'), take('--via', '')
import kit as K
import home, nav, plan as PL
import haru_clay as HC, mocap as MC, walker as WK
from claylib import cli, run, key, look_at, camera, constant_interp, Boil

OPTS = cli('home_walk')
FPS = 12
sc = K.begin('home_walk', res=OPTS['res'], samples=OPTS['samples'], frames=1)
floors = home.build()
h = HC.HaruClay(name='haru')
lib = MC.Library(os.path.join(HERE, '..', 'mocap', 'clips.npz'), h)
route, names = nav.route(A, B_, via=[v for v in VIA.split(',') if v])
print('ROUTE', ' > '.join(names))
w = WK.Walker(lib, route, t0=0.6)
END = w.t_end + 1.2
F = int(END * FPS); sc.frame_start, sc.frame_end = 1, F
floor = WK.Floor()


# the camera crew (home/shots.py): one setup per room, inside it, panning after her; a cut when she changes room
import shots as SH
HOLD = 4                                           # a new room must hold for this many frames before the cut
lift = K.point_light('cam_fill', (0, 0, 0.2), 0.12, radius=0.03, color=(0.6, 0.68, 0.95)); K._to(lift, 'Lights')   # soft, all round: no horizon line
cam = camera((0.5, -0.6, 0.15), (0.5, 0.3, 0.1), lens=18, fstop=11.0); cam.data.clip_start = 0.004
boil = Boil(5, amp=0.00012, rot=0.003)
chat = random.Random(4)
cur = None; pend = None; pend_n = 0; aim = None; cuts = []
for f in range(1, F + 1):
    t = (f - 1) / FPS
    W, xy, zh, yaw = w.at(t)
    h.root.location = (xy.x, xy.y, zh); h.root.rotation_euler = (0, 0, yaw)
    MC.apply(h, W, yaw)
    z = floor.place(h, W, yaw, zh)
    for pv in ('chest', 'neck', 'head'):
        e = h.P[pv]; a = 0.005
        e.rotation_euler = (e.rotation_euler.x + chat.uniform(-a, a), e.rotation_euler.y, e.rotation_euler.z + chat.uniform(-a, a))
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, yaw + je.z)
    h.expr('neutral', blink=any(abs(t - b) < 0.09 for b in (1.5, 4.8, 8.2, 11.6, 15.0, 18.4, 21.8)))
    h.key(f)
    s = SH.shot_for(xy.x, xy.y, z)
    tgt = Vector((xy.x, xy.y, z + 0.085))                                 # her chest
    if cur is None: cur = s; f0 = f; aim0 = tgt.copy()
    elif s['name'] != cur['name']:
        if pend == s['name']: pend_n += 1
        else: pend, pend_n = s['name'], 1
        if pend_n >= HOLD: cur = s; aim = None; pend = None; cuts.append((f, s['name'])); f0 = f; aim0 = tgt.copy()
    else: pend = None
    aim = tgt.copy() if aim is None else aim.lerp(tgt, 0.3)               # the operator pans after her, a beat behind
    loc = SH.moved(cur, cur['loc'], aim0, (f - f0) / FPS)                 # and the camera creeps in (or rises)
    cam.location = loc; look_at(cam, aim); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = cur['lens']; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (loc - aim).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    lift.location = loc; lift.keyframe_insert('location', frame=f)
print('SHOTS', cuts[:1] and '', SH.shot_for(*route[0][0]).get('name'), cuts)
print('FRAMES', F, 'END', round(END, 2))
constant_interp()
run(sc, OPTS)
