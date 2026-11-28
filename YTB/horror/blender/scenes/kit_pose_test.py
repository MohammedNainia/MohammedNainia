"""Rig test for the cast kit: Mika and Jun (puppets/cast_kit.py) in five poses, three-quarter view.
blender -b -P scenes/kit_pose_test.py -- --still 1 --res 1920 1080 --samples 48 --out DIR
  1 rest (A-pose)   2 wave   3 walking step   4 sitting on a log   5 head turned, looking down"""
import bpy, sys, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import cast_kit as CK
from claylib import *

OPTS = cli('kit_pose_test')
reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=1)
world((0.5, 0.5, 0.52), 0.12)
sc.view_settings.exposure = -0.4
backdrop = clay('backdrop', (0.32, 0.3, 0.29), rough=0.9, sss=0.0, bump=0.15, thumb=0.1, scale=2.0)
rounded_box('floor', (1.4, 0.6, 0.01), loc=(0, 0.08, -0.005), bevel=0.002, mat=backdrop)
bpy.ops.mesh.primitive_plane_add(size=1.8, location=(0, 0.35, 0.4), rotation=(math.pi / 2, 0, 0)); assign(bpy.context.object, backdrop)
wood = clay('log', (0.25, 0.16, 0.1), rough=0.85, sss=0.0, bump=0.5)

MIKA = dict(hair_src='hair_mika', outfit=('#3d8c86', '#2f3a4f', '#eceae6'))
JUN = dict(hair_src='hair_jun', outfit=('#5a6d3a', '#9a8a6c', '#3a332c'))
X = [-0.3, -0.15, 0.0, 0.15, 0.3]
SEAT = 0.034                                                     # log seat height for a child

c1 = CK.character('head_girl', 'body_child', CK.CHILD, 'child', (X[0], 0, 0), 'mika_rest', **MIKA)

c2 = CK.character('head_girl', 'body_child', CK.CHILD, 'child', (X[1], 0, 0), 'mika_wave', **MIKA)
CK.turn(c2['rig'], 'upper_arm.R', 'Y', 0); CK.relax(c2['rig'])          # arms hang
CK.turn(c2['rig'], 'upper_arm.R', 'Y', 140)                     # right arm up and out, away from the head
CK.turn(c2['rig'], 'forearm.R', 'Y', 40)                        # forearm up: the wave
CK.pose(c2['rig'], **{'head': (0, 8, 0)})

c3 = CK.character('head_boy', 'body_child', CK.CHILD, 'child', (X[2], 0, 0), 'jun_walk', **JUN)
CK.relax(c3['rig'])
CK.pose(c3['rig'], **{'thigh.L': (-28, 0, 0), 'shin.L': (18, 0, 0), 'thigh.R': (18, 0, 0), 'shin.R': (30, 0, 0),
                      'foot.R': (-15, 0, 0), 'spine': (-4, 0, 0)})
CK.turn(c3['rig'], 'upper_arm.L', 'X', 22); CK.turn(c3['rig'], 'upper_arm.R', 'X', -22)   # arms swing against the legs

c4 = CK.character('head_boy', 'body_child', CK.CHILD, 'child', (X[3], 0, 0), 'jun_sit', **JUN)
hipz = CK.JOINTS['hip'] * max(v.co.z for v in c4['body'].data.vertices)
CK.pose(c4['rig'], **{'thigh.L': (-85, 0, 0), 'thigh.R': (-85, 0, 0), 'shin.L': (85, 0, 0), 'shin.R': (85, 0, 0),
                      'root_loc': (0, 0, -(hipz - SEAT))})
CK.relax(c4['rig'])
rounded_box('seat_log', (0.07, 0.03, SEAT), loc=(X[3], 0.006, SEAT / 2), bevel=0.006, mat=wood)

c5 = CK.character('head_girl', 'body_child', CK.CHILD, 'child', (X[4], 0, 0), 'mika_look', **MIKA)
CK.relax(c5['rig'])
CK.pose(c5['rig'], **{'neck': (12, 0, 0), 'head': (10, 35, 0), 'chest': (0, 10, 0)})

area_light('key', (-0.5, -0.6, 0.6), (0, 0, 0.08), 14.0, 0.4, (1.0, 0.9, 0.8))
area_light('fill', (0.6, -0.45, 0.3), (0, 0, 0.08), 4.0, 0.4, (0.75, 0.82, 1.0))
area_light('rim', (0.1, 0.45, 0.4), (0, 0, 0.1), 4.0, 0.3)
cam = camera((0.3, -0.85, 0.15), (0.02, 0, 0.06), lens=38, fstop=11.0, focus=0.9)
run(sc, OPTS)
