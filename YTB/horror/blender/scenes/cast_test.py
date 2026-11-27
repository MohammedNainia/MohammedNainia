"""Line-up of the Sector B13 cast in the woods at dawn (scale and look check).
blender -b -P scenes/cast_test.py -- --stills 1,2,3 --res 540 960 --samples 32 --out DIR
  1 everyone side by side   2 close on Mika, Haru and Jun   3 the creature mid-step between the handlers, its hand"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
SETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, os.path.join(SETS, 'outside')); sys.path.insert(0, SETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import kit as K
import woods as W
import haru_clay as HC, cast_camp as CC
from claylib import cli, run, camera, look_at, key, constant_interp

OPTS = cli('cast_test')
sc = K.begin('cast_test', res=OPTS['res'], samples=OPTS['samples'], frames=3)
W.materials(); W.ground(tufts=120); W.trees(n=60)
W.mood('dawn', haze=0.06)
key_l = K.area_light('cast_key', (0.25, -0.35, 0.3), (0, 0.1, 0.08), 6.0, 0.2, (1.0, 0.9, 0.8)); K._to(key_l, 'Lights')

def put(p): p.pose({}); p.ground(floor=0.0); return p
mika = put(CC.Friend(CC.MIKA, name='mika', loc=(-0.05, 0.1, 0), yaw=0)); mika.expr('smile')
haru = put(HC.HaruClay(name='haru', loc=(0.0, 0.1, 0), yaw=0)); haru.expr('worried')
jun = put(CC.Friend(CC.JUN, name='jun', loc=(0.05, 0.1, 0), yaw=0)); jun.expr('smile')
ha = put(CC.Handler(name='handler_a', loc=(-0.14, 0.14, 0), yaw=0)); hb = put(CC.Handler(name='handler_b', loc=(0.14, 0.14, 0), yaw=0))
cr = CC.Creature(loc=(0.0, 0.25, 0), yaw=0)
cr.walk(0.7); cr.look(15, 10); cr.reach(-1, 0.6)
fg = CC.fingers('zip_fingers'); fg.location = (0.09, 0.0, 0.03); fg.rotation_euler = (0, 0, math.radians(20))
for p in (mika, haru, jun, ha, hb): p.key(1)
cr.key(1)

SHOTS = {1: ((0.0, -0.45, 0.12), (0.0, 0.17, 0.12), 30), 2: ((0.0, -0.12, 0.105), (0.0, 0.1, 0.1), 40),
         3: ((0.12, -0.08, 0.12), (0.02, 0.25, 0.17), 30)}
cam = camera((0, 0, 0.1), (0, 1, 0), lens=30, fstop=11.0); cam.data.clip_start = 0.002
for f, (loc, tg, lens) in SHOTS.items():
    cam.location = loc; look_at(cam, Vector(tg)); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = lens; cam.data.keyframe_insert('lens', frame=f)
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (Vector(loc) - Vector(tg)).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
constant_interp()
run(sc, OPTS)
