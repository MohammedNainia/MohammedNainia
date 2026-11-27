"""Test of the windows and doors kit (library/sets/openings.py) in a bedroom corner, against the refs:
refs/props/window_curtains.jpg, refs/props/door_ajar.jpg, refs/moods/mood_streetlamp_window.jpg.
blender -b -P scenes/openings_test.py -- --stills 1,2,3,11,12,13,21,22 --res 1080 1920 --samples 64 --out DIR
  1-3   window: curtains open, half, closed (a figure outside: its shadow lands on the closed curtains)
  11-13 door: shut, ajar 14 deg (handle down), open 55 deg (the lit room's light falls across the floor)
  21-22 the second window: heavy curtains half closed and the roller blind half down, the sash slid up"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
LIBSETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, LIBSETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import kit as K
from claylib import cli, run, camera, sphere, constant_interp

OPTS = cli('openings_test')
sc = K.begin('openings_test', res=OPTS['res'], samples=OPTS['samples'], frames=30)

R = (-0.3, -0.35, 0.3, 0.2)                                         # room: x -0.3..0.3, y -0.35..0.2 (back wall at y 0.2)
K.floor(R); K.ceiling(R)
win = K.window(0.22, 0.38, 0.075, 0.2, rig=True, curtains='thin', outside='streetlamp')
win2 = K.window(0.06, 0.16, 0.08, 0.19, rig=True, curtains='heavy', curtain_color='#2f3a5a', blind=True, sash=True, outside='moon')
door = K.door(0.25, 0.33, rig=True, beyond='lit', color='white', hinge='start')
K.wall((-0.3, 0.2), (0.3, 0.2), openings=[win], inward=-1)
K.wall((0.3, -0.35), (0.3, 0.2), openings=[door], inward=1)
K.wall((-0.3, -0.35), (-0.3, 0.2), openings=[win2], inward=-1)
W, D, W2 = win['obj'], door['obj'], win2['obj']

# a tall thin figure outside the window, between it and the streetlamp
FIG = Vector((0.01, 0.3, 0.0))                                     # close behind the glass, so its shadow is big
head = sphere('figure_head', 0.017, tuple(FIG + Vector((0, 0, 0.192))), scale=(1, 1, 1.25), mat=K.M['void']); K._to(head)
bpy.ops.mesh.primitive_cylinder_add(radius=0.017, depth=0.17, location=tuple(FIG + Vector((0, 0, 0.09)))); body = bpy.context.object
body.scale = (1.7, 0.6, 1); body.data.materials.append(K.M['void']); K._to(body)
for sd in (1, -1):                                                  # long arms hanging past the knees, splayed a little
    bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=0.16, location=tuple(FIG + Vector((sd * 0.038, 0, 0.1)))); arm = bpy.context.object
    arm.rotation_euler = (0, sd * 0.16, 0); arm.data.materials.append(K.M['void']); K._to(arm)

# dim cold fill so the room is readable; the streetlamp, the moon and the lit room do the rest
from claylib import area_light
fl = area_light('fill_cold', (0.0, -0.3, 0.2), (0, 0.1, 0.08), 0.35, 0.3, (0.5, 0.6, 0.9)); K._to(fl, 'Lights')

# states
for f, c in ((1, 0.0), (2, 0.5), (3, 1.0)): W.close(f, c)
for f in (11, 12, 13, 21, 22): W.close(f, 0.0)
for f, deg, t, e in ((1, 0, 0, 0.6), (11, 0, 0, 0.6), (12, 14, 1, 0.6), (13, 55, 0, 0.6), (21, 0, 0, 0.6)):
    D.swing(f, deg); D.turn(f, t); D.light(f, e)
for f, c, b, o in ((1, 0.0, 0.0, 0.0), (21, 0.5, 0.0, 0.0), (22, 0.3, 0.5, 0.6)):
    W2.close(f, c); W2.blind(f, b); W2.open(f, o)

# cameras per still
cam = camera((0, -0.3, 0.12), (0, 0.2, 0.135), lens=32, fstop=8.0)
SHOTS = {1: ((0.0, -0.22, 0.11), (0.0, 0.2, 0.14), 30), 11: ((0.05, -0.2, 0.1), (0.3, -0.01, 0.09), 30),
         21: ((-0.08, -0.1, 0.12), (-0.3, -0.24, 0.135), 32)}
for f0, (loc, tgt, lens) in SHOTS.items():
    for f in range(f0, f0 + 3):
        cam.location = loc; d = Vector(tgt) - Vector(loc); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = lens; cam.data.dof.focus_distance = d.length
        cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
        cam.data.keyframe_insert('lens', frame=f); cam.data.keyframe_insert('dof.focus_distance', frame=f)
cam.data.clip_start = 0.002
constant_interp()
run(sc, OPTS)
