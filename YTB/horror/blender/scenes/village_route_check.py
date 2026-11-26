"""Check the village route map (library/sets/village/village_nav.py) against the built street, with no render: every leg clear
of fences, hedges, lamp posts, trees and walls by Haru's half-width (HIT), ground under every step (FLOOR), and
every door reachable from her own (UNREACHABLE).

    blender -b -P scenes/village_route_check.py
"""
import bpy, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
SETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, os.path.join(SETS, 'village')); sys.path.insert(0, SETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import kit as K
import village, village_nav as nav
import walker as WK

SKIP = ('road', 'sidewalk', 'curb', 'lawn', 'path', 'pave_joint', 'centre_line', 'haze', 'door_step', 'porch_roof', 'lamp_arm',
        'lamp_head', 'lamp_lens', 'tree_crown', 'roof', 'gable', 'chimney', 'win_', 'attic')
R = 0.011
K.begin('village_check', res=(64, 64), samples=1)
village.build()
bpy.context.view_layer.update()
obs = []
for o in bpy.data.objects:
    if o.type != 'MESH' or any(s in o.name for s in SKIP): continue
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    obs.append((o.name, min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts),
                min(p.z for p in pts), max(p.z for p in pts)))
floor = WK.Floor(); bad = 0
for a, b in nav.EDGES:
    p0, p1 = Vector(nav.P[a]), Vector(nav.P[b])
    n = max(2, int((p1 - p0).length / 0.006)); hit = set(); gap = []
    for k in range(n + 1):
        p = p0.lerp(p1, k / n)
        for (nm, x0, x1, y0, y1, z0, z1) in obs:
            if x0 - R < p.x < x1 + R and y0 - R < p.y < y1 + R and z0 < p.z + 0.12 and z1 > p.z + 0.02:
                hit.add(nm.split('.')[0])
        g = floor.below(p.x, p.y, p.z + 0.05, reach=0.12)
        if g is None or abs(g - p.z) > 0.02: gap.append((round(p.x, 3), round(p.y, 3), None if g is None else round(g, 3)))
    if hit: print('HIT', a, '>', b, sorted(hit)); bad += 1
    if gap: print('FLOOR', a, '>', b, gap[:3], len(gap)); bad += 1
for d in [k for k in nav.P if k.endswith('_door')]:
    try: nav.route('haru_door', d)
    except Exception as e: print('UNREACHABLE', d, e); bad += 1
r, names = nav.route('haru_door', 'south_3_door'); print('ROUTE', ' > '.join(names))
print('CHECKED', len(nav.EDGES), 'legs,', bad, 'problems')
