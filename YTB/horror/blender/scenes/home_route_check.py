"""Check the big home's route map (library/sets/home/nav.py) against the built house, with no render:
  * every leg is clear of furniture and walls by Haru's half-width (HIT lines name what is in the way),
  * there is a floor under every step of every flat leg, at the leg's height (FLOOR lines show where not),
  * every room can reach every other room (UNREACHABLE lines).

    blender -b -P scenes/home_route_check.py
"""
import bpy, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
SETS = os.path.join(HERE, '..', 'library', 'sets')
sys.path.insert(0, os.path.join(SETS, 'home')); sys.path.insert(0, SETS); sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import kit as K
import home, nav
import walker as WK

SKIP = ('floor', 'ceiling', 'runner', 'rug', 'sky', 'haze', 'night_ground', 'tread', 'riser', 'stair_runner', 'moon',
        'bath_mat', 'cladding', 'skirting', 'picture', 'sconce', 'curtain_rail', 'frame', 'window', 'sill', 'lamp_cord',
        'bulb', 'cord', 'stringer', 'hatch', 'joist', 'pipe', 'clothes_line', 'roof', 'rafter', 'ridge', 'collar', 'gable', 'fill_')
R = 0.011                                   # Haru's half-width (shoulders), at 1:10

K.begin('home_check', res=(64, 64), samples=1)
home.build()
bpy.context.view_layer.update()
obs = []
for o in bpy.data.objects:
    if o.type != 'MESH' or any(s in o.name for s in SKIP): continue
    if o.hide_render: continue
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    obs.append((o.name, min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts),
                min(p.z for p in pts), max(p.z for p in pts)))
floor = WK.Floor()
bad = 0
for a, b in nav.EDGES:
    p0, p1 = Vector(nav.P[a]), Vector(nav.P[b]); stairs = (a, b) in nav.STAIRS
    n = max(2, int((p1 - p0).length / 0.004)); hit = set(); gap = []
    for k in range(n + 1):
        p = p0.lerp(p1, k / n)
        for (nm, x0, x1, y0, y1, z0, z1) in obs:
            if x0 - R < p.x < x1 + R and y0 - R < p.y < y1 + R and z0 < p.z + 0.12 and z1 > p.z + 0.008 + (0.03 if stairs else 0):
                hit.add(nm.split('.')[0])
        if not stairs:
            gs = [floor.below(p.x + dx, p.y + dy, p.z + 0.03, reach=0.06) for dx, dy in ((0, 0), (0.003, 0.002), (-0.003, -0.002))]
            g = max((v for v in gs if v is not None), default=None)   # a seam between two floor slabs is not a hole
            if g is None or abs(g - p.z) > 0.004: gap.append((round(p.x, 3), round(p.y, 3), None if g is None else round(g, 3)))
    if hit: print('HIT', a, '>', b, sorted(hit)); bad += 1
    if gap: print('FLOOR', a, '>', b, gap[:4], len(gap)); bad += 1
rooms = ['living_room', 'dining_room', 'kitchen', 'hall', 'pantry', 'study', 'garage', 'laundry', 'basement', 'haru_bedroom',
         'bathroom', 'guest_bedroom', 'mum_bedroom', 'bathroom2', 'front_door']
for r in rooms[1:]:
    try: nav.route(rooms[0], r)
    except Exception as e: print('UNREACHABLE', r, e); bad += 1
r, names = nav.route('haru_bedroom', 'basement'); print('ROUTE', ' > '.join(names))
print('CHECKED', len(nav.EDGES), 'legs,', bad, 'problems')
