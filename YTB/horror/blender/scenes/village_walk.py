"""Walking test in the village (library/sets/village): Haru walks a route from village_nav (default: out of her front
door, down her garden path, along the sidewalk, up a neighbour's path). Filmed with street setups: on the sidewalk
a fixed camera stands on the road ahead of her, she walks toward it and past, and it cuts to the next one; in a front
garden a camera at the curb looks up the path to the door.

    blender -b -P scenes/village_walk.py -- [--stills a,b] [--res 1080 1920] [--samples 64] [--out DIR] [--from haru_door] [--to north_4_door]
"""
import bpy, os, sys, random, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
SETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, os.path.join(SETS, 'village')); sys.path.insert(0, SETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
argv = sys.argv
def take(k, d):
    if k not in argv: return d
    i = argv.index(k); v = argv[i + 1]; del argv[i:i + 2]; return v
A, B_ = take('--from', 'haru_door'), take('--to', 'north_4_door')
import kit as K
import village, village_nav as NV, village_plan as VP
import haru_clay as HC, mocap as MC, walker as WK
from claylib import cli, run, key, look_at, camera, constant_interp, Boil

OPTS = cli('village_walk')
FPS = 12
sc = K.begin('village_walk', res=OPTS['res'], samples=OPTS['samples'], frames=1)
village.build()
h = HC.HaruClay(name='haru')
lib = MC.Library(os.path.join(HERE, '..', 'mocap', 'clips.npz'), h)
route, names = NV.route(A, B_)
print('ROUTE', ' > '.join(names))
w = WK.Walker(lib, route, t0=0.6)
END = w.t_end + 1.2
F = int(END * FPS); sc.frame_start, sc.frame_end = 1, F
floor = WK.Floor()


def shot_for(x, y, heading):
    """a street setup for where she is: (name, camera location, lens)"""
    if y > VP.SIDEWALK_N[1] - 0.01 or y < VP.SIDEWALK_S[0] + 0.01:            # in a front garden: from the curb, up the path
        north = y > 0.3
        gx = round(x * 20) / 20
        return f'garden_{gx:+.2f}', (gx + 0.16, 0.56 if north else 0.04, 0.115), 24
    step = 0.9; s = 1 if heading >= 0 else -1                                 # on the street: the next camera ahead of her
    k = math.floor(x / step) + (1 if s > 0 else 0)
    cx = k * step + s * 0.25
    side_y = 0.36 if y > 0.3 else 0.24
    return f'street_{k}_{s}', (cx, side_y, 0.105), 22


cam = camera((0, -0.4, 0.2), (0, 0, 0.1), lens=22, fstop=8.0); cam.data.clip_start = 0.004
fill = K.point_light('cam_fill', (0, 0, 0.2), 0.25, radius=0.03, color=(0.6, 0.68, 0.95)); K._to(fill, 'Lights')
boil = Boil(5, amp=0.00012, rot=0.003); chat = random.Random(4)
cur = None; pend = None; pend_n = 0; aim = None; cuts = []; last = None; heading = 1.0
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
    h.expr('neutral', blink=any(abs(t - b) < 0.09 for b in (1.5, 4.8, 8.2, 11.6, 15.0, 18.4, 21.8, 25.2)))
    h.key(f)
    if last is not None and abs(xy.x - last.x) > 1e-4: heading = xy.x - last.x
    last = xy.copy()
    s = shot_for(xy.x, xy.y, heading)
    if cur is None: cur = s
    elif s[0] != cur[0]:
        if pend == s[0]: pend_n += 1
        else: pend, pend_n = s[0], 1
        if pend_n >= 4: cur = s; aim = None; pend = None; cuts.append((f, s[0]))
    else: pend = None
    tgt = Vector((xy.x, xy.y, z + 0.08))
    aim = tgt.copy() if aim is None else aim.lerp(tgt, 0.3)
    loc = Vector(cur[1])
    cam.location = loc; look_at(cam, aim); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = cur[2]; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (loc - aim).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    fill.location = loc; fill.keyframe_insert('location', frame=f)
print('SHOTS', cuts)
print('FRAMES', F, 'END', round(END, 2))
constant_interp()
run(sc, OPTS)
