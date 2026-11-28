"""Rig test for the new Haru (cast_kit.haru): rest, hug knees, sit on a log, hands over mouth, lying, head turn.
blender -b -P scenes/haru_rig_test.py -- --still 1 --res 1920 1080 --samples 32 --out DIR"""
import bpy, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import cast_kit as CK
import haru_poses as HPZ
from claylib import *
OPTS = cli('haru_rig_test'); reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=1)
world((0.5, 0.5, 0.52), 0.12); sc.view_settings.exposure = -0.4
bd = clay('backdrop', (0.32, 0.3, 0.29), rough=0.9, sss=0.0, bump=0.15, thumb=0.1, scale=2.0)
rounded_box('floor', (1.4, 0.6, 0.01), loc=(0, 0.08, -0.005), bevel=0.002, mat=bd)
bpy.ops.mesh.primitive_plane_add(size=1.8, location=(0, 0.35, 0.4), rotation=(math.pi / 2, 0, 0)); assign(bpy.context.object, bd)
wood = clay('log', (0.25, 0.16, 0.1), rough=0.85, sss=0.0, bump=0.5)
X = [-0.3, -0.18, -0.06, 0.06, 0.18, 0.3]
for i, name in enumerate(('rest', 'hug', 'sit', 'mouth', 'lie', 'point')):
    c = CK.haru((X[i], 0, 0), 'haru_' + name)
    HPZ.apply(c, name, f=None, seat=0.034)
    if name == 'lie': c['rig'].location.z += 0.012
    if name == 'sit': rounded_box('seat', (0.07, 0.03, 0.034), loc=(X[i], 0.008, 0.017), bevel=0.006, mat=wood)
area_light('key', (-0.5, -0.6, 0.6), (0, 0, 0.08), 14.0, 0.4, (1.0, 0.9, 0.8))
area_light('fill', (0.6, -0.45, 0.3), (0, 0, 0.08), 4.0, 0.4, (0.75, 0.82, 1.0))
cam = camera((0.3, -0.85, 0.15), (0.0, 0, 0.05), lens=38, fstop=11.0, focus=0.9)
run(sc, OPTS)
