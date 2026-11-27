"""Look-dev for the woods kit (library/sets/outside/woods.py): the clearing at night with the fire, three tents, Haru
for scale, the Sector B13 fence. Set WOODS_DAWN=1 for the dawn light.
blender -b -P scenes/woods_test.py -- --stills 1,2,3,4 --res 540 960 --samples 32 --out DIR
  1 wide over the fire to the tents   2 Haru's tent from outside, her torch on inside   3 inside her tent, looking at
  the door with the zip half open   4 the fence, gate and sign"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
SETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, os.path.join(SETS, 'outside')); sys.path.insert(0, SETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import kit as K
import woods as W
import haru_clay as HC
from claylib import cli, run, camera, look_at, key, constant_interp

DAWN = os.environ.get('WOODS_DAWN') == '1'
OPTS = cli('woods_test')
sc = K.begin('woods_test', res=OPTS['res'], samples=OPTS['samples'], frames=4)
W.materials()
W.ground(); W.trees()
fire = W.Campfire(0, 0)
for i, a in enumerate((200, 330, 75)):
    W.logs_seat(math.cos(math.radians(a)) * 0.1, math.sin(math.radians(a)) * 0.1, a + 90, name=f'seat_log_{i}')
t_haru = W.Tent('tent_haru', 0.0, -0.3, 180, 'green')
t_mika = W.Tent('tent_mika', -0.27, -0.17, 235, 'red')
t_jun = W.Tent('tent_jun', 0.27, -0.15, 125, 'blue')
fence = W.Fence(y=0.8)
fence.gate(None, 35)
torch = W.Torch(-0.03, -0.31, 0.004, yaw=200, pitch=55)
W.mood('dawn' if DAWN else 'night')

h = HC.HaruClay(loc=(0.07, 0.07, 0), yaw=200, name='haru'); h.pose({}); h.ground(floor=0.0); h.expr('worried'); h.key(1)

SHOTS = {1: ((0.08, 0.42, 0.12), (0.0, -0.12, 0.03), 24),
         2: ((0.02, 0.02, 0.05), (0.0, -0.3, 0.05), 32),
         3: ((0.035, -0.355, 0.045), (0.0, -0.23, 0.04), 18),
         4: ((0.12, 0.56, 0.075), (0.09, 0.796, 0.11), 30)}
cam = camera((0, 0, 0.1), (0, 1, 0), lens=24, fstop=8.0); cam.data.clip_start = 0.002
fire.burn(1, 4)
torch.on(1)
for f, (loc, tg, lens) in SHOTS.items():
    cam.location = loc; look_at(cam, Vector(tg)); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (Vector(loc) - Vector(tg)).length
    cam.data.dof.keyframe_insert('focus_distance', frame=f)
    t_haru.zip(f, 0.5 if f == 3 else 0.0)
constant_interp()
run(sc, OPTS)
