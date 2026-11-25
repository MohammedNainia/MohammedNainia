"""Where Haru can walk in the big home (plan.py): named points in every room, in every doorway, and at the foot and
head of each flight, joined by straight legs that miss the furniture (checked by scenes/home_route_check.py).
route('haru_bedroom', 'kitchen') gives the points to walk through and the kind of each leg ('walk' on a floor,
'stairs_up' / 'stairs_down' on a flight), the same shape as the small house's nav, so puppets/walker.py walks both.
Points are (x, y, floor z) in world space, with the floors at plan.LEVEL.

Rooms you can ask for: living_room, dining_room, kitchen, hall, front_door, pantry, study, garage, laundry, basement,
haru_bedroom, haru_bed, bathroom, guest_bedroom, landing, mum_bedroom, bathroom2.
The chase loop of the plan is all here: hall > main stairs > landing > back stairs > kitchen > dining > living > hall.
The attic is not on the map yet (its hatch has no ladder down).
"""
import heapq
from mathutils import Vector
import plan as PL

G, U, B = PL.LEVEL['ground'], PL.LEVEL['upstairs'], PL.LEVEL['basement']
P = {
    # ---- ground floor: the hall spine (walkway x 0.40..0.50 beside the main stairs)
    'front_door': (0.50, 0.03, G), 'hall_front': (0.46, 0.07, G), 'hall': (0.45, 0.30, G), 'hall_mid': (0.47, 0.60, G),
    'hall_back': (0.48, 0.77, G), 'main_foot': (0.55, 0.08, G),
    'living_door_h': (0.43, 0.16, G), 'living_door': (0.40, 0.16, G), 'living_door_l': (0.37, 0.16, G),
    'living_room': (0.27, 0.27, G), 'living_n': (0.19, 0.39, G), 'living_dining_door': (0.19, 0.45, G),
    'dining_s_door': (0.19, 0.48, G), 'dining_s': (0.30, 0.505, G),
    'dining_door_h': (0.43, 0.59, G), 'dining_door': (0.40, 0.59, G), 'dining_door_d': (0.37, 0.59, G),
    'dining_room': (0.32, 0.62, G), 'dining_n': (0.30, 0.75, G),
    'kitchen_door_d': (0.19, 0.77, G), 'dining_kitchen_door': (0.19, 0.80, G), 'kitchen_s': (0.19, 0.835, G), 'kitchen': (0.30, 0.89, G),
    'kitchen_stairs_k': (0.37, 0.83, G), 'kitchen_stairs_door': (0.40, 0.83, G), 'back_foot': (0.44, 0.815, G),
    'hall_stairs_door': (0.44, 0.80, G),
    'pantry_out': (0.54, 0.77, G), 'pantry_door': (0.54, 0.80, G), 'pantry': (0.54, 0.92, G),
    'study_h': (0.57, 0.06, G), 'study_door': (0.60, 0.06, G), 'study_in': (0.64, 0.06, G), 'study': (0.76, 0.22, G),
    'garage_h': (0.57, 0.64, G), 'garage_door': (0.60, 0.64, G), 'garage_in': (0.63, 0.64, G), 'garage': (0.75, 0.66, G),
    'laundry_door_g': (0.74, 0.77, G), 'garage_laundry_door': (0.74, 0.80, G), 'laundry_door_l': (0.74, 0.83, G),
    'laundry': (0.76, 0.88, G), 'basement_head': (0.93, 0.82, G),
    # ---- basement
    'basement_foot': (0.93, 1.165, B), 'basement_n': (0.84, 1.12, B), 'basement': (0.75, 0.85, B),
    # ---- upstairs: the landing (walkway x 0.40..0.50 beside the main stairwell, then x 0.48..0.60 past the back one)
    'main_head': (0.55, 0.45, U), 'landing': (0.46, 0.47, U), 'landing_front': (0.45, 0.10, U), 'landing_mid': (0.52, 0.62, U),
    'landing_back': (0.53, 0.84, U), 'landing_far': (0.53, 1.165, U), 'back_head': (0.44, 1.165, U),
    'haru_h': (0.43, 0.36, U), 'haru_door': (0.40, 0.36, U), 'haru_l': (0.37, 0.36, U), 'haru_in': (0.36, 0.33, U),
    'haru_bedroom': (0.24, 0.23, U), 'haru_bed': (0.15, 0.17, U),
    'bath_h': (0.43, 0.59, U), 'bath_door': (0.40, 0.59, U), 'bath_in': (0.37, 0.59, U), 'bathroom': (0.22, 0.62, U),
    'guest_door': (0.40, 1.165, U), 'guest_in': (0.34, 1.165, U), 'guest_bedroom': (0.30, 1.0, U),
    'mum_h': (0.57, 0.48, U), 'mum_door': (0.60, 0.48, U), 'mum_in': (0.63, 0.48, U), 'mum_bedroom': (0.68, 0.50, U),
    'mum_bed': (0.70, 0.28, U),
    'bath2_h': (0.55, 0.94, U), 'bath2_door': (0.60, 0.94, U), 'bath2_in': (0.63, 0.94, U), 'bathroom2': (0.76, 0.94, U),
}
EDGES = [
    # ground floor
    ('front_door', 'hall_front'), ('front_door', 'main_foot'), ('hall_front', 'main_foot'), ('hall_front', 'hall'),
    ('hall', 'hall_mid'), ('hall_mid', 'hall_back'),
    ('hall', 'living_door_h'), ('hall_front', 'living_door_h'), ('living_door_h', 'living_door'), ('living_door', 'living_door_l'),
    ('living_door_l', 'living_room'), ('living_room', 'living_n'), ('living_n', 'living_dining_door'),
    ('living_dining_door', 'dining_s_door'), ('dining_s_door', 'dining_s'), ('dining_s', 'dining_room'),
    ('hall_mid', 'dining_door_h'), ('dining_door_h', 'dining_door'), ('dining_door', 'dining_door_d'), ('dining_door_d', 'dining_room'),
    ('dining_room', 'dining_n'), ('dining_n', 'kitchen_door_d'), ('kitchen_door_d', 'dining_kitchen_door'),
    ('dining_kitchen_door', 'kitchen_s'), ('kitchen_s', 'kitchen'), ('kitchen', 'kitchen_stairs_k'),
    ('kitchen_stairs_k', 'kitchen_stairs_door'), ('kitchen_stairs_door', 'back_foot'),
    ('hall_back', 'hall_stairs_door'), ('hall_stairs_door', 'back_foot'),
    ('hall_back', 'pantry_out'), ('pantry_out', 'pantry_door'), ('pantry_door', 'pantry'),
    ('hall_front', 'study_h'), ('study_h', 'study_door'), ('study_door', 'study_in'), ('study_in', 'study'),
    ('hall_mid', 'garage_h'), ('garage_h', 'garage_door'), ('garage_door', 'garage_in'), ('garage_in', 'garage'),
    ('garage', 'laundry_door_g'), ('laundry_door_g', 'garage_laundry_door'), ('garage_laundry_door', 'laundry_door_l'),
    ('laundry_door_l', 'laundry'), ('laundry', 'basement_head'),
    # flights
    ('main_foot', 'main_head'), ('back_foot', 'back_head'), ('basement_head', 'basement_foot'),
    # basement
    ('basement_foot', 'basement_n'), ('basement_n', 'basement'),
    # upstairs
    ('main_head', 'landing'), ('main_head', 'landing_mid'), ('landing', 'landing_front'), ('landing', 'landing_mid'),
    ('landing', 'haru_h'), ('haru_h', 'haru_door'), ('haru_door', 'haru_l'), ('haru_l', 'haru_in'), ('haru_in', 'haru_bedroom'),
    ('haru_bedroom', 'haru_bed'),
    ('landing', 'bath_h'), ('landing_mid', 'bath_h'), ('bath_h', 'bath_door'), ('bath_door', 'bath_in'), ('bath_in', 'bathroom'),
    ('main_head', 'mum_h'), ('mum_h', 'mum_door'), ('mum_door', 'mum_in'), ('mum_in', 'mum_bedroom'), ('mum_bedroom', 'mum_bed'),
    ('landing_mid', 'landing_back'), ('landing_back', 'bath2_h'), ('bath2_h', 'bath2_door'), ('bath2_door', 'bath2_in'),
    ('bath2_in', 'bathroom2'),
    ('landing_back', 'landing_far'), ('landing_far', 'back_head'), ('back_head', 'guest_door'),
    ('guest_door', 'guest_in'), ('guest_in', 'guest_bedroom'),
]
STAIRS = {('main_foot', 'main_head'), ('back_foot', 'back_head'), ('basement_head', 'basement_foot')}


def _nbrs():
    g = {k: [] for k in P}
    for a, b in EDGES:
        d = (Vector(P[a]) - Vector(P[b])).length
        g[a].append((b, d)); g[b].append((a, d))
    return g


def route(a, b, via=()):
    """shortest walk from point a to point b (through the points in `via`, in order):
    ([(Vector point, kind of the leg that ends here)], names); the first kind is None"""
    stops = [a, *via, b]; names = [a]
    for s, e in zip(stops, stops[1:]): names += _path(s, e)[1:]
    out = [(Vector(P[names[0]]), None)]
    for x, y in zip(names, names[1:]):
        kind = 'walk'
        if (x, y) in STAIRS or (y, x) in STAIRS: kind = 'stairs_down' if P[y][2] < P[x][2] else 'stairs_up'
        out.append((Vector(P[y]), kind))
    return out, names


def _path(a, b):
    g = _nbrs(); dist = {a: 0.0}; prev = {}; q = [(0.0, a)]
    while q:
        d, n = heapq.heappop(q)
        if n == b: break
        if d > dist.get(n, 1e9): continue
        for m, w in g[n]:
            if d + w < dist.get(m, 1e9): dist[m] = d + w; prev[m] = n; heapq.heappush(q, (d + w, m))
    names = [b]
    while names[-1] != a: names.append(prev[names[-1]])
    return names[::-1]
