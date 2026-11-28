"""Expression test for the new Haru's face (puppets/haru_face.py), laid out like the Artlist sheet (4 x 2):
neutral, sad, uncomfortable, worried / scared, crying, terrified, relieved (the dot-eye sheet).
blender -b -P scenes/haru_face_test.py -- --still 1 --res 1920 1080 --samples 48 --out DIR"""
import bpy, sys, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import cast_kit as CK
import haru_face as HF
from claylib import *
OPTS = cli('haru_face_test'); reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=1)
world((0.55, 0.55, 0.57), 0.15); sc.view_settings.exposure = -0.3
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0.2, 0.1), rotation=(math.pi / 2, 0, 0))
assign(bpy.context.object, clay('backdrop', (0.42, 0.4, 0.4), rough=0.9, sss=0.0, bump=0.1, thumb=0.05, scale=2.0))
ROW = [('neutral', {}), ('sad', {}), ('uncomfortable', {}), ('worried', {}),
       ('scared', {}), ('crying', dict(tears=1.0, t=0.3)), ('terrified', dict(pale=0.4)), ('relieved', {})]
if os.environ.get('FACE_ROW') == '2': ROW = ROW[4:]
elif os.environ.get('FACE_ROW') == '1': ROW = ROW[:4]
for i, (ex, kw) in enumerate(ROW):
    c = CK.haru((0, 0, 0), 'haru_' + ex)
    face = HF.Face(c, 'haru_' + ex)
    face.set(1, ex, **kw)
    c['rig'].location = ((i - (len(ROW) - 1) / 2) * 0.04, 0, 0)
area_light('key', (-0.4, -0.5, 0.35), (0, 0, 0.09), 9.0, 0.3, (1.0, 0.92, 0.85))
area_light('fill', (0.4, -0.4, 0.1), (0, 0, 0.09), 3.0, 0.4, (0.8, 0.85, 1.0))
cam = camera((0, -0.75, 0.108), (0, 0, 0.108), lens=140, fstop=16.0, focus=0.75)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.33 if len(ROW) > 4 else 0.165; cam.data.dof.use_dof = False
run(sc, OPTS)
