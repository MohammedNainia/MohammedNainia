"""Walking test in the big home (library/sets/home): Haru walks a route from the route map (home/nav.py), for example
from her bed, out of her room, along the landing, down the main stairs and through the hall into the kitchen.
A high camera follows her from above and in front; the floors above her (and her own floor's ceiling) are hidden,
so she is always seen. Proves the route map, the walker (puppets/walker.py) and the feet on floors and treads.

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

# what to hide on each floor she is on: every floor above, and this floor's ceiling; the attic and roof always
ORDER = ['basement', 'ground', 'upstairs', 'attic']
hide_sets = {}
for i, fl in enumerate(ORDER[:3]):
    s = [o for f2 in ORDER[i + 1:] for o in floors[f2]]
    for o in floors[fl]:                                                 # the ceiling and what hangs from it (hatch, cords)
        if o.type != 'MESH': continue
        zlo = min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
        if o.name.startswith('ceiling') or zlo > PL.LEVEL[fl] + 0.17: s.append(o)
    hide_sets[fl] = s
everything = {o for f2 in ORDER for o in floors[f2]}
def on_floor(z):
    return 'upstairs' if z > PL.UP * 0.5 else 'ground' if z > -PL.UP * 0.5 else 'basement'

lift = K.area_light('follow_fill', (0, 0, 0.6), (0, 0, 0), 1.2, 0.3, (0.6, 0.68, 0.95)); K._to(lift, 'Lights')
cam = camera((0, -0.4, 0.6), (0, 0, 0), lens=30, fstop=11.0); cam.data.clip_start = 0.005
boil = Boil(5, amp=0.00012, rot=0.003)
chat = random.Random(4)
cs = None; last = None
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
    fl = on_floor(zh)
    if fl != last:                                                       # show her floor, hide what is over her
        hid = set(hide_sets[fl])
        for o in everything:
            o.hide_render = o in hid; o.keyframe_insert('hide_render', frame=f)
        last = fl
    p = Vector((xy.x, xy.y, z))
    cs = p.copy() if cs is None else cs.lerp(p, 0.15)
    loc = Vector((cs.x, cs.y - 0.22, cs.z + 0.55)); tgt = Vector((cs.x, cs.y + 0.01, cs.z + 0.03))
    cam.location = loc; look_at(cam, tgt); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (loc - tgt).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    lift.location = (cs.x, cs.y - 0.05, cs.z + 0.3); lift.keyframe_insert('location', frame=f)
print('FRAMES', F, 'END', round(END, 2))
constant_interp()
run(sc, OPTS)
