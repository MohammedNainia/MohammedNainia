"""Where Haru can walk in the village (village_plan.py): along the middle of both sidewalks, across the road at four
crossings, and up every garden path to a front door. Same shape as home/nav.py, so puppets/walker.py walks it.

    route('haru_door', 'south_3_door')  ->  ([(Vector point, leg kind)], names)

Points: 'haru_door' and '<house>_door' (on the doorstep), '<house>_gate' (where its path meets the sidewalk),
'n_<x>' / 's_<x>' sidewalk points, 'west_end_n', 'east_end_s' and so on at the ends of the street.
"""
import heapq
from mathutils import Vector
import village_plan as VP

WALK_N, WALK_S = 0.49, -0.07                 # the middle of each sidewalk (clear of the lamps, bins and poles)
CROSS_X = VP.CROSS_X                         # where she crosses the road (clear of the parked cars)
P, EDGES = {}, []


def _sidewalk(side, xs):
    y = WALK_N if side == 'N' else WALK_S
    pts = sorted(set(round(x, 3) for x in xs))
    names = []
    for x in pts:
        n = f"{'n' if side == 'N' else 's'}_{x:+.2f}"; P[n] = (x, y, 0.0); names.append(n)
    for a, b in zip(names, names[1:]): EDGES.append((a, b))
    return {x: n for x, n in zip(pts, names)}


gates = {'N': [], 'S': []}
for i, h in enumerate(VP.HOUSES):
    name, side = h[0], h[3]
    x, _ = VP.door_x(i); gates[side].append((name, x))
gates['N'].append(('haru', VP.HOME_AT[0] + VP.HOME_DOOR_X))
for c in VP.CIVIC: gates[c[3]].append((c[0], VP.civic_door_x(c[0])))          # the hospital, the police station
ends = (-4.9, 4.9)
for side in ('N', 'S'):
    xs = [x for _, x in gates[side]] + list(CROSS_X) + list(ends)
    at = _sidewalk(side, xs)
    for name, x in gates[side]:
        dy = VP.door_y(side) + (-0.045 if side == 'N' else 0.045)
        P[name + '_door'] = (x, dy, 0.0)
        EDGES.append((at[round(x, 3)], name + '_door'))
    for x in CROSS_X:                                              # the crossings join the two sidewalks
        if side == 'N': EDGES.append((at[round(x, 3)], f"s_{x:+.2f}"))
P['west_end'] = P[f"n_{ends[0]:+.2f}"]; P['east_end'] = P[f"s_{ends[1]:+.2f}"]
EDGES += [('west_end', f"n_{ends[0]:+.2f}"), ('east_end', f"s_{ends[1]:+.2f}")]
STAIRS = set()


def _nbrs():
    g = {k: [] for k in P}
    for a, b in EDGES:
        d = (Vector(P[a]) - Vector(P[b])).length
        g[a].append((b, d)); g[b].append((a, d))
    return g


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


def route(a, b, via=()):
    stops = [a, *via, b]; names = [a]
    for s, e in zip(stops, stops[1:]): names += _path(s, e)[1:]
    names = [n for i, n in enumerate(names) if i == 0 or P[n] != P[names[i - 1]]]
    out = [(Vector(P[names[0]]), None)] + [(Vector(P[y]), 'walk') for y in names[1:]]
    return out, names
