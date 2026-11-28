"""Modular cast kit test (puppets/cast_kit.py): kit heads on kit bodies at the standard sizes, in channel clay, beside
the Tripo Haru, then Mika and Jun built from the kit with their hairpieces and outfit colours.
blender -b -P scenes/kit_lineup.py -- --still 1 --res 1920 1080 --samples 64 --out DIR
KIT_CLOSE=1: close-up of Haru, Mika and Jun. Prints HAIR lines (the hair's scale onto each head)."""
import bpy, sys, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import haru_clay as HC
import cast_kit as CK
from claylib import *

OPTS = cli('kit_lineup')
reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=1)
world((0.5, 0.5, 0.52), 0.12)
sc.view_settings.exposure = -0.4
backdrop = clay('backdrop', (0.32, 0.3, 0.29), rough=0.9, sss=0.0, bump=0.15, thumb=0.1, scale=2.0)
rounded_box('floor', (1.6, 0.5, 0.01), loc=(0, 0.08, -0.005), bevel=0.002, mat=backdrop)
bpy.ops.mesh.primitive_plane_add(size=1.8, location=(0, 0.3, 0.4), rotation=(math.pi / 2, 0, 0)); assign(bpy.context.object, backdrop)

X = [-0.42, -0.29, -0.16, -0.05, 0.06, 0.18, 0.31]
CK.character('head_man', 'body_man', CK.MAN, 'adult', (X[0], 0, 0), 'man')
CK.character('head_woman', 'body_woman', CK.WOMAN, 'adult', (X[1], 0, 0), 'woman')
CK.character('head_girl', 'body_child', CK.CHILD, 'child', (X[2], 0, 0), 'girl')
CK.character('head_girl', 'body_child', CK.CHILD, 'child', (X[3], 0, 0), 'mika', hair_src='hair_mika',
             outfit=('#3d8c86', '#2f3a4f', '#eceae6'))                      # teal hoodie, dark jeans, white sneakers
haru = CK.load('haru_full'); CK.fit(haru, CK.CHILD); haru.location = (X[4], 0, 0)
HC.apply_textured_clay([haru], name='haru')
CK.character('head_boy', 'body_child', CK.CHILD, 'child', (X[5], 0, 0), 'jun', hair_src='hair_jun',
             outfit=('#5a6d3a', '#9a8a6c', '#3a332c'))                      # olive hoodie, khaki trousers, dark boots
CK.character('head_boy', 'body_child', CK.CHILD, 'child', (X[6], 0, 0), 'boy')

area_light('key', (-0.5, -0.6, 0.6), (0, 0, 0.08), 14.0, 0.4, (1.0, 0.9, 0.8))
area_light('fill', (0.6, -0.45, 0.3), (0, 0, 0.08), 4.0, 0.4, (0.75, 0.82, 1.0))
area_light('rim', (0.1, 0.45, 0.4), (0, 0, 0.1), 4.0, 0.3)
if os.environ.get('KIT_CLOSE') == '1':
    cam = camera((0.06, -0.42, 0.09), (0.06, 0, 0.075), lens=50, fstop=11.0, focus=0.42)
else:
    cam = camera((-0.05, -1.05, 0.1), (-0.05, 0, 0.085), lens=50, fstop=11.0, focus=1.05)
run(sc, OPTS)
