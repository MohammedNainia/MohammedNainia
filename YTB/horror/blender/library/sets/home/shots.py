"""Camera setups for the big home, like a film crew's: one camera per room, set inside the room near its front corner
at a grown-up's eye height and looking deeper in, so behind her there is always a wall or the next room, never the
empty space round the house. A scene asks shot_for(x, y, z) where Haru is; the camera stays put and pans after her,
and cuts to the next setup when she walks into another room. On a flight the shot looks down the stairwell from the
floor she is leaving or arriving at.

    import shots; s = shots.shot_for(x, y, z)  ->  {'name', 'loc': (x, y, z), 'lens'}
"""
import plan as PL

G, U, B = PL.LEVEL['ground'], PL.LEVEL['upstairs'], PL.LEVEL['basement']
EYE = 0.155                                   # camera height over the floor (1.55 m)

# (name, floor level, room rect x0 y0 x1 y1, camera xy, lens); the first rect that holds her wins
ROOMS = [
    # ground floor
    ('living_room', G, (0.0, 0.0, 0.40, 0.45), (0.37, 0.03), 18),
    ('dining_room', G, (0.0, 0.45, 0.40, 0.80), (0.37, 0.48), 18),
    ('kitchen', G, (0.0, 0.80, 0.40, 1.20), (0.03, 0.83), 18),
    ('hall', G, (0.40, 0.0, 0.60, 0.80), (0.47, 0.025), 20),
    ('back_stairs', G, (0.40, 0.80, 0.48, 1.20), (0.03, 0.83), 18),          # seen from the kitchen, through its door
    ('pantry', G, (0.48, 0.80, 0.60, 1.20), (0.47, 0.6), 22),
    ('study', G, (0.60, 0.0, 1.0, 0.45), (0.63, 0.03), 18),
    ('garage', G, (0.60, 0.45, 1.0, 0.80), (0.97, 0.48), 18),
    ('laundry', G, (0.60, 0.80, 1.0, 1.20), (0.63, 0.83), 18),
    # basement
    ('basement', B, (0.40, 0.45, 1.0, 1.20), (0.43, 0.48), 18),
    # upstairs
    ('haru_bedroom', U, (0.0, 0.0, 0.40, 0.45), (0.37, 0.03), 18),
    ('bathroom', U, (0.0, 0.45, 0.40, 0.80), (0.37, 0.48), 18),
    ('guest_bedroom', U, (0.0, 0.80, 0.40, 1.20), (0.37, 0.83), 18),
    ('landing_front', U, (0.40, 0.0, 0.60, 0.50), (0.45, 0.03), 20),
    ('landing_mid', U, (0.40, 0.50, 0.60, 1.05), (0.55, 0.40), 20),           # up over the main stairwell, looking down the landing
    ('landing_back', U, (0.40, 1.05, 0.60, 1.20), (0.585, 1.10), 16),         # the far end, clear of the window curtains: she passes it, turns down the stairs
    ('mum_bedroom', U, (0.60, 0.0, 1.0, 0.80), (0.63, 0.03), 18),
    ('bathroom2', U, (0.60, 0.80, 1.0, 1.20), (0.63, 0.83), 18),
]
# on a flight: (rect, z split) -> the shot above the split, the shot below it
FLIGHTS = [
    ((0.50, 0.12, 0.60, 0.42), G, U, 0.13, 'landing_front', 'hall'),        # main stairs
    ((0.40, 0.84, 0.48, 1.14), G, U, 0.12, 'landing_back', 'kitchen'),      # back stairs
    ((0.88, 0.84, 0.98, 1.14), B, G, -0.13, 'laundry', 'basement'),         # basement stairs
]
BY_NAME = {r[0]: r for r in ROOMS}


# how each camera moves while she is in its room (the push-in, crane and dolly of github.com/kevinbadi/blender-skills,
# slowed down for horror): 'push' creeps toward her, 'crane' rises to look down on her, 'locked' stays still
MOVES = {'landing_back': 'crane', 'landing_mid': 'push', 'back_stairs': 'locked'}


def _shot(name):
    n, lvl, rect, (cx, cy), lens = BY_NAME[name]
    up = 0.05 if n in ('landing_mid', 'landing_back') else 0.0              # these two hang higher, looking down
    return {'name': n, 'loc': (cx, cy, lvl + EYE + up), 'lens': lens, 'move': MOVES.get(n, 'push')}


def moved(s, start, aim0, secs, near=0.09):
    """the camera position `secs` into shot s: a slow eased move from `start` (push: up to 30% of the way toward where
    she was at the cut, never nearer than `near`; crane: up 4 cm)"""
    from mathutils import Vector
    u = min(1.0, secs / 5.0); u = u * u * (3 - 2 * u)
    p = Vector(start)
    if s['move'] == 'push':
        d = Vector(aim0) - p; L = max(0.0, min(0.3 * d.length, d.length - near))
        p = p + d.normalized() * L * u
    elif s['move'] == 'crane':
        p = p + Vector((0, 0, 0.04 * u))
    return p


def floor_of(z):
    return U if z > U * 0.5 else G if z > -U * 0.5 else B


def shot_for(x, y, z):
    for (x0, y0, x1, y1), lo, hi, split, above, below in FLIGHTS:
        if x0 - 0.005 < x < x1 + 0.005 and y0 < y < y1 and lo + 0.015 < z < hi - 0.015:
            return _shot(above if z > split else below)
    lvl = floor_of(z)
    for n, l, (x0, y0, x1, y1), _, _ in ROOMS:
        if l == lvl and x0 <= x < x1 and y0 <= y < y1: return _shot(n)
    return _shot('hall')
