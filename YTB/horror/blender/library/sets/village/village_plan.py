"""Haru's village: one quiet street of ordinary houses (metres at 1:10; +x along the street, +y north).

    south houses (face north)   y -1.62 .. -0.50
    south gardens               y -0.50 .. -0.20
    south sidewalk              y -0.20 .. 0.0   (raised 1.5 cm, curb at y 0)
    road                        y  0.0  .. 0.60  (z -0.015)
    north sidewalk              y  0.60 .. 0.80
    north gardens               y  0.80 .. 1.08
    north houses (face south)   y  1.08 .. (back)

Haru's house is the big home (../home) placed with its front wall on y = 1.08 and its left wall on x = 0: build it
there with home.build() and move it by HOME_AT to walk from the street through her front door into the real rooms.
"""
UP = 0.26                       # one storey
ROAD = (-3.4, 0.0, 4.4, 0.60)   # x0, y0, x1, y1
ROAD_Z = -0.015
SIDEWALK_N = (0.60, 0.80)
SIDEWALK_S = (-0.20, 0.0)
FRONT_N, FRONT_S = 1.08, -0.50  # the house fronts
HOME_AT = (0.0, FRONT_N)        # where the big home's origin goes
HOME_DOOR_X = 0.50              # the middle of her front door

# houses: (name, x0, x1, side, depth, storeys, roof, facade, door colour, lit windows, porch light on)
# roof 'side' = ridge along the street (gable ends at the sides), 'front' = gable facing the street
HOUSES = [
    ('north_1', -2.90, -1.80, 'N', 0.95, 2, 'side', 'brick_wall', 'door_green', (1, 0, 0, 1), False),
    ('north_2', -1.55, -0.30, 'N', 1.00, 1, 'front', 'plaster_cream', 'door_red', (0, 1, 0), True),
    ('north_4', 1.30, 2.35, 'N', 0.95, 2, 'front', 'siding_grey', 'door_blue', (0, 0, 0, 0), False),
    ('north_5', 2.65, 3.90, 'N', 1.05, 2, 'side', 'brick_wall', 'door_black', (0, 1, 1, 0), True),
    ('south_1', -2.95, -1.75, 'S', 1.00, 2, 'front', 'plaster_blue', 'door_white', (0, 0, 1, 0), False),
    ('south_2', -1.40, -0.25, 'S', 0.95, 2, 'side', 'brick_wall', 'door_green', (0, 0, 0, 0), False),
    ('south_3', 0.15, 1.35, 'S', 1.05, 1, 'side', 'siding_cream', 'door_red', (1, 0, 0), True),
    ('south_4', 1.65, 2.85, 'S', 1.00, 2, 'front', 'plaster_cream', 'door_black', (0, 0, 0, 1), False),
]
CORNER_TREES = (4.6, 5.6)       # past the police station on the south side: a few trees
LAMPS_N = (-4.6, -3.05, -2.05, -0.65, 1.22, 2.55, 4.05)     # street lamps on the north sidewalk, between the gardens (none at a door)
LAMPS_S = (-3.9, -2.7, -1.25, 0.0, 1.5, 3.0, 4.75)     # and the south sidewalk


def door_x(i):
    """world x of house i's front door (the doors alternate left and right of the middle; south houses face north,
    so their local left is world right)"""
    name, x0, x1, side = HOUSES[i][:4]
    du = (x1 - x0) * 0.22 * (1 if i % 2 == 0 else -1)
    return (x0 + x1) / 2 + (du if side == 'N' else -du), du


def door_y(side):
    return FRONT_N if side == 'N' else FRONT_S


# the hospital and the police station: (name, x0, x1, side, depth, storeys, facade, door x offset)
CIVIC = [
    ('hospital', -5.15, -3.20, 'N', 1.30, 3, 'plaster_pale', 0.0),
    ('police', 3.10, 4.45, 'S', 1.10, 2, 'brick_wall', 0.0),
]


def civic_door_x(name):
    c = next(c for c in CIVIC if c[0] == name)
    return (c[1] + c[2]) / 2 + c[7]
