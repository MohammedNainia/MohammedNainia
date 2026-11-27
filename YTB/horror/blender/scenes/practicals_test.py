"""Test of the lights kit (library/sets/practicals.py), against refs/props/lamps_set.jpg and
refs/moods/mood_phone_light.jpg.
blender -b -P scenes/practicals_test.py -- --stills 1,2,3,4 --res 1080 1920 --samples 64 --out DIR
  1 every practical on (lamp, hanging bulb, candle, phone, TV snow)   2 only the ceiling light (the room readable)
  3 the dark: only the candle and the phone                            4 Haru close-up lit only by her phone, with
                                                                         the clay key aimed from the phone"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
LIBSETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, LIBSETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import kit as K
import practicals as PL
import haru_clay as HC
from claylib import cli, run, camera, constant_interp

OPTS = cli('practicals_test')
sc = K.begin('practicals_test', res=OPTS['res'], samples=OPTS['samples'], frames=10)
R = (-0.35, -0.3, 0.35, 0.25)
K.floor(R); K.ceiling(R)
K.wall((-0.35, 0.25), (0.35, 0.25), inward=-1)
K.wall((-0.35, -0.3), (-0.35, 0.25), inward=-1)
K.block('table', -0.17, 0.17, 0.1, 0.2, 0.04, 0.045, K.M['wood'], bevel=0.0015)
for x in (-0.16, 0.16):
    for y in (0.105, 0.195): K.block('table_leg', x - 0.003, x + 0.003, y - 0.003, y + 0.003, 0.0, 0.04, K.M['wood'], bevel=0.0008)

T = 0.045
lamp = PL.Lamp(-0.075, 0.15, T)
bulb = PL.Bulb(-0.045, 0.13, ceiling=K.H, drop=0.12)
cnd = PL.Candle(-0.03, 0.13, T)
ph1 = PL.Phone(0.0, 0.125, T, yaw=-20)
tv = PL.TV(0.06, 0.16, yaw=0, z=T, static=True, cabinet=False)
ceil = PL.CeilingLight(0.0, -0.02)
sw = PL.switch(0.25, 0.245, 0.12)

h = HC.HaruClay(loc=(-0.24, -0.08, 0), yaw=0, name='haru'); h.pose({}); h.ground(floor=0.0); h.expr('scared', gaze=(0, 20)); h.key(1)
HEAD = Vector((-0.24, -0.08, 0.104))
ph2 = PL.Phone(-0.24, -0.13, 0.075, tilt=-53)                         # held at her chest, screen tilted up to her face
rake = HC.ClayRake(energy=0.05, color=(0.75, 0.85, 1.0))

ALL = (lamp, bulb, cnd, ph1, tv, ceil, ph2)
STATE = {1: (1, 1, 1, 1, 1, 0, 0), 2: (0, 0, 0, 0, 0, 1, 0), 3: (0, 0, 1, 1, 0, 0, 0), 4: (0, 0, 0, 0, 0, 0, 1)}
for f, st in STATE.items():
    for L, v in zip(ALL, st): L.level(f, v)
tv.snow(1, 4); bulb.sway(1, 4, deg=0)
for f, st in STATE.items():                                             # snow() re-keys the TV: put its state back
    tv.level(f, st[4])
    sw.rotation_euler = (0.3 if st[5] else -0.3, 0, 0); sw.keyframe_insert('rotation_euler', frame=f)

cam = camera((0, -0.2, 0.09), (0, 0.15, 0.06), lens=30, fstop=8.0)
for f in range(1, 5):
    if f < 4: loc, tgt, lens = Vector((0.0, -0.2, 0.1)), Vector((0.0, 0.15, 0.075)), 24
    else: loc, tgt, lens = HEAD + Vector((0.012, -0.085, 0.004)), HEAD, 45
    d = tgt - loc; cam.location = loc; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
    cam.data.dof.focus_distance = d.length
    for p in ('location', 'rotation_euler'): cam.keyframe_insert(p, frame=f)
    cam.data.keyframe_insert('lens', frame=f); cam.data.keyframe_insert('dof.focus_distance', frame=f)
    rake.aim(f, HEAD, loc, ph2.src(), on=(f == 4))
cam.data.clip_start = 0.002
constant_interp()
run(sc, OPTS)
