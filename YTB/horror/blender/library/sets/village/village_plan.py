"""Haru's village (version 2, denser): a narrow village lane of small houses close together (metres at 1:10; +x
along the street, +y north).

    south back row              y < -1.25        (rooftops behind the street)
    south houses (face north)   y -1.10 .. -0.30
    south gardens               y -0.30 .. -0.14
    south sidewalk              y -0.14 .. 0.0   (raised 1.5 cm, curb at y 0)
    road (a lane, cars parked
    along the north curb)       y  0.0  .. 0.42  (z -0.015)
    north sidewalk              y  0.42 .. 0.56
    north gardens               y  0.56 .. 0.72
    north houses (face south)   y  0.72 .. (back)

Haru's house is the big home (../home): its front wall on y = 0.72, its left wall on x = 0. It is the biggest, oldest
house on the street; build home.build() and move it by HOME_AT to walk from the street into the real rooms.
"""
import random

UP = 0.26                       # one storey
ROAD = (-5.0, 0.0, 5.0, 0.42)   # x0, y0, x1, y1
ROAD_Z = -0.015
SIDEWALK_N = (0.42, 0.56)
SIDEWALK_S = (-0.14, 0.0)
FRONT_N, FRONT_S = 0.72, -0.30  # the house fronts
HOME_AT = (0.0, FRONT_N)        # where the big home's origin goes
HOME_DOOR_X = 0.50              # the middle of her front door

_r = random.Random(5)
def _lit(n, p=0.3): return tuple(int(_r.random() < p) for _ in range(n))

# houses: (name, x0, x1, side, depth, storeys, roof, facade, door colour, lit windows, porch light on)
# roof 'side' = ridge along the street, 'front' = gable facing the street
_N = [(-3.10, -2.45, 2, 'front', 'brick_wall', 'door_green'), (-2.37, -1.67, 2, 'side', 'plaster_cream', 'door_red'),
      (-1.59, -0.99, 1, 'front', 'siding_grey', 'door_blue'), (-0.91, -0.10, 2, 'side', 'brick_wall', 'door_black'),
      (1.10, 1.75, 2, 'front', 'plaster_blue', 'door_white'), (1.83, 2.48, 2, 'side', 'brick_wall', 'door_green'),
      (2.56, 3.26, 1, 'side', 'siding_cream', 'door_red'), (3.34, 3.98, 2, 'front', 'plaster_cream', 'door_black')]
_S = [(-4.30, -3.65, 2, 'front', 'brick_wall', 'door_red'), (-3.57, -2.92, 2, 'side', 'plaster_cream', 'door_green'),
      (-2.84, -2.14, 1, 'side', 'siding_grey', 'door_white'), (-2.06, -1.41, 2, 'front', 'brick_wall', 'door_blue'),
      (-1.33, -0.63, 2, 'side', 'plaster_blue', 'door_black'), (-0.55, 0.10, 2, 'front', 'siding_cream', 'door_red'),
      (0.18, 0.88, 1, 'side', 'brick_wall', 'door_green'), (0.96, 1.61, 2, 'front', 'plaster_cream', 'door_white'),
      (1.69, 2.39, 2, 'side', 'brick_wall', 'door_black'), (3.66, 4.31, 2, 'front', 'plaster_blue', 'door_green')]
HOUSES = []
for i, (x0, x1, st, roof, fac, door) in enumerate(_N):
    HOUSES.append((f'north_{i + 1}', x0, x1, 'N', _r.uniform(0.72, 0.85), st, roof, fac, door, _lit(2 * st + 1), _r.random() < 0.35))
for i, (x0, x1, st, roof, fac, door) in enumerate(_S):
    HOUSES.append((f'south_{i + 1}', x0, x1, 'S', _r.uniform(0.72, 0.85), st, roof, fac, door, _lit(2 * st + 1), _r.random() < 0.35))
HEDGED = {'north_4', 'south_2', 'south_5', 'south_9'}

# the hospital and the police station: (name, x0, x1, side, depth, storeys, facade, door x offset)
CIVIC = [
    ('hospital', -4.60, -3.20, 'N', 0.95, 2, 'plaster_pale', 0.0),
    ('police', 2.48, 3.56, 'S', 0.85, 2, 'brick_wall', 0.0),
]
LAMPS_N = (-3.16, -1.63, 1.05, 2.52, 4.1)       # on the north curb, in the gaps between houses
LAMPS_S = (-4.4, -2.1, -0.59, 0.92, 2.43, 3.62)  # on the south curb
POLES_S = (-4.6, -2.88, -1.37, 0.14, 1.65, 3.6)  # wooden power poles at the back of the south sidewalk
CARS = [(-2.75, 'N', 'car_red'), (-0.55, 'N', 'car_grey'), (1.95, 'N', 'car_cream'), (3.75, 'N', 'car_green'), (-1.75, 'S', 'car_blue')]
CROSS_X = (-3.95, -1.15, 0.5, 2.95)              # where she crosses the road (clear of the parked cars)


def door_x(i):
    """world x of house i's front door (left or right of the middle, alternating), and its local offset"""
    name, x0, x1, side = HOUSES[i][:4]
    du = (x1 - x0) * 0.2 * (1 if i % 2 == 0 else -1)
    return (x0 + x1) / 2 + (du if side == 'N' else -du), du


def door_y(side):
    return FRONT_N if side == 'N' else FRONT_S


def civic_door_x(name):
    c = next(c for c in CIVIC if c[0] == name)
    return (c[1] + c[2]) / 2 + c[7]
