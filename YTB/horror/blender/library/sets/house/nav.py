"""Where Haru can walk in the house: named points in every room, at every doorway and at the top and bottom of the
stairs, joined by straight legs. route('bedroom', 'living_room') gives the points to walk through, with the kind of
each leg ('walk' on a floor, 'stairs_down' / 'stairs_up' on the flight). Points are (x, y, floor z).

Add a room: give it a point inside, a point in its doorway, and join the doorway to the point outside it.
"""
import heapq, math
from mathutils import Vector
import plan

U = plan.UP
P = {
    # upstairs
    'bedroom': (-0.105, 0.12, U), 'bedroom_door': (-0.065, 0.10, U),
    'bathroom': (-0.14, 0.42, U), 'bathroom_door': (-0.065, 0.42, U),
    'hallway_s': (0.0, 0.10, U), 'hallway_stairs': (0.015, 0.425, U), 'hallway_n': (0.0, 0.52, U),
    'stair_top': (0.115, 0.43, U),
    # ground floor
    'stair_bottom': (0.115, 0.13, 0.0), 'hall_s': (0.115, 0.075, 0.0), 'front_door': (0.138, 0.07, 0.0),
    'living_door': (0.065, 0.12, 0.0), 'living_room': (-0.06, 0.12, 0.0),
    'kitchen': (-0.09, 0.36, 0.0), 'kitchen_living_door': (-0.005, 0.25, 0.0), 'living_n': (0.012, 0.2, 0.0),
    'kitchen_s': (-0.005, 0.3, 0.0),
}
EDGES = [
    ('bedroom', 'bedroom_door'), ('bedroom_door', 'hallway_s'), ('hallway_s', 'hallway_stairs'),
    ('hallway_stairs', 'hallway_n'), ('hallway_stairs', 'bathroom_door'), ('bathroom_door', 'bathroom'),
    ('hallway_stairs', 'stair_top'), ('stair_top', 'stair_bottom'),
    ('stair_bottom', 'hall_s'), ('hall_s', 'front_door'), ('hall_s', 'living_door'), ('living_door', 'living_room'),
    ('living_room', 'living_n'), ('living_n', 'kitchen_living_door'), ('kitchen_living_door', 'kitchen_s'),
    ('kitchen_s', 'kitchen'),
]
STAIRS = {('stair_top', 'stair_bottom')}


def _nbrs():
    g = {k: [] for k in P}
    for a, b in EDGES:
        d = (Vector(P[a]) - Vector(P[b])).length
        g[a].append((b, d)); g[b].append((a, d))
    return g


def route(a, b):
    """shortest walk from point a to point b: [(Vector point, kind of the leg that ends here)], first kind None"""
    g = _nbrs(); dist = {a: 0.0}; prev = {}; q = [(0.0, a)]
    while q:
        d, n = heapq.heappop(q)
        if n == b: break
        if d > dist.get(n, 1e9): continue
        for m, w in g[n]:
            if d + w < dist.get(m, 1e9): dist[m] = d + w; prev[m] = n; heapq.heappush(q, (d + w, m))
    names = [b]
    while names[-1] != a: names.append(prev[names[-1]])
    names.reverse()
    out = [(Vector(P[names[0]]), None)]
    for x, y in zip(names, names[1:]):
        kind = 'walk'
        if (x, y) in STAIRS or (y, x) in STAIRS: kind = 'stairs_down' if P[y][2] < P[x][2] else 'stairs_up'
        out.append((Vector(P[y]), kind))
    return out, names
