"""Haru's home, ground floor (see plan.py): walls for the whole floor from one list (so every door lines up and no wall
is doubled), then each room's furniture. Hiding places: behind the floor-length living-room curtains, behind the sofa
(it stands off the wall), under the dining table's long cloth, in the under-stairs cupboard, in the pantry, inside
the kitchen base cupboards, in the chest freezer, behind the
hanging sheets in the laundry.

    blender -b -P library/sets/home/ground.py -- [--out DIR] [--res W H] [--samples N] [--marks a,b] [--blend F]
"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import kit as K
import props as PR
import plan as PL

UP = PL.UP
D = K.door; WIN = K.window


def extra_materials():
    for k, (c, r) in {'concrete': ((0.16, 0.16, 0.15), 0.9), 'metal_shelf': ((0.3, 0.31, 0.32), 0.4), 'sack': ((0.4, 0.33, 0.22), 0.95),
                      'car_paint': ((0.18, 0.05, 0.04), 0.3), 'washer': ((0.72, 0.72, 0.7), 0.3), 'green_lamp': ((0.12, 0.3, 0.15), 0.3)}.items():
        if k not in K.M: K.M[k] = K.painted(k, c, rough=r)


WALLS = [  # (a, b, inward, openings, kw)
    # exterior
    ((0.0, 0.0), (0.0, 1.2), -1, [WIN(0.12, 0.28, 0.085, 0.19, moon=True), WIN(0.55, 0.7, 0.085, 0.19),
                                  D(0.95, 1.03, keep=True)], {}),                                 # west: living, dining, back door
    ((0.0, 1.2), (1.0, 1.2), -1, [WIN(0.12, 0.22, 0.1, 0.185, moon=True), WIN(0.74, 0.84, 0.1, 0.18)], {}),   # back: kitchen, laundry
    ((1.0, 0.0), (1.0, 1.2), 1, [WIN(0.15, 0.3, 0.085, 0.19), D(0.5, 0.74, h=0.19, keep=True, angle=0),
                                 D(0.95, 1.03, keep=True)], {}),                                  # east: study, garage, garden door
    ((0.40, 0.0), (0.60, 0.0), 1, [D(0.05, 0.15, keep=True)], {'wild': True}),                    # front of the hall + front door
    # interior
    ((0.40, 0.0), (0.40, 0.80), 1, [D(0.12, 0.20, angle=20), D(0.55, 0.63, angle=20)], {}),      # hall | living, dining
    ((0.60, 0.0), (0.60, 0.80), -1, [D(0.02, 0.10, angle=-20), D(0.60, 0.68, angle=-20)], {}),   # hall | study, garage
    ((0.0, 0.45), (0.40, 0.45), 1, [D(0.15, 0.23, angle=20)], {}),                                # living | dining
    ((0.0, 0.80), (0.40, 0.80), 1, [D(0.15, 0.23, angle=-20)], {}),                               # dining | kitchen
    ((0.40, 0.80), (0.60, 0.80), 1, [D(0.0, 0.08, leaf=False), D(0.10, 0.18, angle=20)], {}),    # hall | back stairs, pantry
    ((0.60, 0.80), (1.0, 0.80), 1, [D(0.10, 0.18, angle=20)], {}),                                # garage | laundry
    ((0.40, 0.80), (0.40, 1.2), -1, [D(0.0, 0.06, leaf=False)], {}),                               # kitchen | back stairs
    ((0.48, 0.80), (0.48, 1.2), -1, [], {}),                                                        # back stairs | pantry
    ((0.60, 0.80), (0.60, 1.2), -1, [], {}),                                                        # pantry | laundry
]
FLOORS = {'living_room': 'floor', 'dining_room': 'floor', 'kitchen': 'lino', 'hall': 'floor', 'back_stairs': 'floor',
          'pantry': 'lino', 'study': 'floor', 'garage': 'concrete', 'laundry': 'tiles_floor'}
MS, BS, BMS = PL.MAIN_STAIRS, PL.BACK_STAIRS, PL.BASEMENT_STAIRS


def flight(x0, y_bottom, x1, y_top, n=13):
    """stairs from this floor up one storey (built with the kit's downward flight, lifted by UP)"""
    before = set(bpy.data.objects)
    K.stairs_down(x0 + 0.003, x1 - 0.003, y_top, -1, n=n, rise=UP / n, run=(y_top - y_bottom) / n)
    for o in bpy.data.objects:
        if o not in before and o.parent is None: o.location.z += UP


def under_stairs_cupboard():
    """board the space under the main stairs off from the hall walkway, with a little door into it"""
    x = MS[0]; y0, y1 = MS[1], MS[3]; d0, d1 = PL.UNDER_STAIRS_DOOR
    def top(y): return (y - y0) / (y1 - y0) * UP - 0.012
    y = y0 + 0.04
    while y < y1 - 0.001:
        yb = min(y + 0.023, y1)
        if not (d0 - 0.001 < y < d1 + 0.001 and yb <= d1 + 0.001):
            K.block('under_stairs_panel', x - 0.004, x, y, yb, 0.0, top(y), K.M['door'], bevel=0.0004)
        else:
            K.block('under_stairs_panel', x - 0.004, x, y, yb, 0.135, top(y), K.M['door'], bevel=0.0004)
        y = yb
    hg = PR.hinge(PR.holder('under_stairs', x - 0.004, d0, 0), 'under_stairs_door', 0, 0)
    PR.part(hg, 'under_stairs_door', -0.003, 0.0, 0.0, d1 - d0 - 0.001, 0.002, 0.133, 'door', bevel=0.001)
    kn = K.sphere('under_stairs_knob', 0.0018, (0, 0, 0), mat=K.M['brass']); K._to(kn); K.attach(kn, hg); kn.location = (-0.004, d1 - d0 - 0.008, 0.07)
    PR.swing(hg, -12)                                                    # left a crack open
    K.block('under_stairs_coat', x + 0.01, x + 0.03, 0.36, 0.4, 0.06, 0.15, K.M['coat'], bevel=0.004)
    PR.boxes(x + 0.012, MS[2] - 0.006, 0.3, 0.42, seed=7)


def furnish():
    M = K.M; IN = K.WT / 2
    # --- living room (A front): sofa off the window wall, TV, armchair, coffee table, bookshelf, clock, long curtains
    PR.sofa(0.075, 0.2, 90)
    PR.table(0.17, 0.2, 0, w=0.045, d=0.065, hgt=0.026, mat='wood')
    PR.tv(0.40 - IN - 0.036, 0.26, -90)
    PR.armchair(0.27, 0.1, 60)
    PR.bookshelf(0.1, 0.45 - IN - 0.021, 0)
    PR.grandfather_clock(0.3, 0.45 - IN - 0.017, 0)
    for yy in (0.105, 0.295):                                            # floor-length curtains (someone could stand there)
        c = K.block('long_curtain', IN, IN + 0.012, yy - 0.016, yy + 0.016, 0.0, 0.205, M['curtain'], bevel=0.004); K.add_lumps(c, 0.0018, size=0.01)
    K.runner(0.11, 0.33, 0.06, 0.36)
    K.picture((0.40 - IN - 0.001, 0.08, 0.13), (0.026, 0.034), normal=(-1, 0, 0))
    # --- dining room (A middle): table with a long cloth, chairs, sideboard
    PR.table(0.19, 0.625, 0, w=0.13, d=0.075, hgt=0.06, cloth=True)
    for (cx, cy, yaw) in ((0.15, 0.575, 0), (0.23, 0.575, 0), (0.15, 0.675, 180), (0.23, 0.675, 180), (0.1, 0.625, -90)):
        K.chair(cx, cy - (0.02 if yaw == 0 else -0.02 if yaw == 180 else 0), facing=yaw)
    K.block('sideboard', IN, IN + 0.03, 0.47, 0.54, 0.0, 0.06, M['wood'], bevel=0.002)
    K._to(K.cylinder('candlestick', 0.002, 0.03, (IN + 0.015, 0.505, 0.075), mat=M['brass']))
    K.picture((0.40 - IN - 0.001, 0.7, 0.14), (0.03, 0.04), normal=(-1, 0, 0))
    # --- kitchen (A back): counter run under the back window, fridge, small table, door to the back stairs
    PR.counter_run(0.012, 0.3, 1.2 - IN, 0, sink_at=0.17, stove_at=0.05)
    PR.fridge(0.355, 1.2 - IN - 0.058, 0)
    PR.table(0.19, 0.97, 0, w=0.07, d=0.05, hgt=0.058)
    K.chair(0.17, 0.935, facing=0); K.chair(0.22, 1.0, facing=180)
    K._to(K.cylinder('cat_bowl', 0.008, 0.004, (0.3, 1.06, 0.002), mat=M['red']))
    # --- hall (B front): runner, coat rack by the front door, telephone table, the cupboard under the stairs
    K.runner(0.415, 0.485, 0.03, 0.78)
    K._to(K.cylinder('coat_rack_pole', 0.002, 0.17, (0.415, 0.04, 0.085), mat=M['wood']))
    for i, (dx, dy, hh) in enumerate(((0.004, 0.002, 0.11), (0.008, 0.012, 0.1))):
        c = K.sphere('coat', 0.012, (0.415 + dx, 0.04 + dy, 0.165 - hh / 2), scale=(0.9, 0.7, hh / 0.024), mat=M['coat']); K._to(c)
    K.block('phone_table', 0.42, 0.45, 0.70, 0.74, 0.05, 0.054, M['wood'], bevel=0.001)
    for xx in (0.423, 0.447):
        for yy in (0.703, 0.737): K.block('phone_table_leg', xx - 0.0015, xx + 0.0015, yy - 0.0015, yy + 0.0015, 0, 0.05, M['wood'], bevel=0.0005)
    K.block('telephone', 0.425, 0.44, 0.71, 0.725, 0.054, 0.062, M['red'], bevel=0.002)
    hl = K.point_light('hall_lamp', (0.445, 0.72, 0.075), 0.25, radius=0.006, color=(1.0, 0.66, 0.35)); K._to(hl, 'Lights')
    K._to(K.cylinder('hall_lamp_shade', 0.008, 0.011, (0.445, 0.72, 0.075), mat=M['shade']))
    under_stairs_cupboard()
    # --- pantry (B back): shelves of jars and tins, sacks on the floor
    for (x0, x1, y0, y1) in ((0.48 + IN, 0.48 + IN + 0.02, 0.84, 1.19), (0.60 - IN - 0.02, 0.60 - IN, 0.84, 1.19)):
        for zz in (0.04, 0.08, 0.12, 0.16):
            K.block('pantry_shelf', x0, x1, y0, y1, zz - 0.002, zz, M['wood'], bevel=0.0005)
            yy = y0 + 0.006
            while yy < y1 - 0.01:
                K._to(K.cylinder('jar', 0.004, 0.012, ((x0 + x1) / 2, yy, zz + 0.006), mat=M['glass' if int(yy * 300) % 2 else 'red']))
                yy += 0.012
    for i in range(3): K._to(K.sphere('sack', 0.012, (0.535 + (i - 1) * 0.012, 1.15 - i * 0.01, 0.01), scale=(1, 1, 0.9), mat=M['sack']))
    # --- study (C front): desk with a green lamp, bookshelves, a leather chair, a globe
    K.block('desk', 0.72, 0.84, 0.36, 0.42, 0.055, 0.06, M['wood'], bevel=0.0015, coll=True)
    for xx in (0.725, 0.835): K.block('desk_side', xx - 0.004, xx + 0.004, 0.36, 0.42, 0.0, 0.055, M['wood'], bevel=0.001)
    K._to(K.cylinder('desk_lamp_shade', 0.007, 0.006, (0.82, 0.4, 0.085), mat=M['green_lamp']))
    K._to(K.cylinder('desk_lamp_stem', 0.0012, 0.025, (0.82, 0.405, 0.072), mat=M['brass']))
    K.chair(0.78, 0.335, facing=180)
    PR.bookshelf(0.65, 0.2, -90, w=0.1, hgt=0.19); PR.bookshelf(0.65, 0.33, -90, w=0.08, hgt=0.19)
    PR.armchair(0.9, 0.12, -120)
    K._to(K.sphere('globe', 0.012, (0.93, 0.36, 0.075), mat=M['book3']))
    K._to(K.cylinder('globe_stand', 0.0015, 0.06, (0.93, 0.36, 0.03), mat=M['brass']))
    # --- garage (C middle): a workbench, a chest freezer, boxes along the wall (room for Mum's car)
    K.block('workbench', 1.0 - IN - 0.03, 1.0 - IN, 0.47, 0.6, 0.06, 0.065, M['wood'], bevel=0.0015)
    for yy in (0.475, 0.595): K.block('workbench_leg', 1.0 - IN - 0.028, 1.0 - IN - 0.024, yy - 0.002, yy + 0.002, 0, 0.06, M['wood'], bevel=0.0005)
    K.block('chest_freezer', 0.62, 0.68, 0.74, 0.79 - IN, 0.0, 0.05, M['washer'], bevel=0.003)
    K.block('freezer_lid', 0.618, 0.682, 0.738, 0.79 - IN, 0.05, 0.054, M['washer'], bevel=0.002)
    PR.boxes(0.615, 0.66, 0.47, 0.72, seed=3)
    # --- laundry (C back): washing machine, basket, washing drying on a line, the stairs down to the basement
    K.block('washing_machine', 0.62, 0.67, 1.2 - IN - 0.05, 1.2 - IN, 0.0, 0.07, M['washer'], bevel=0.004)
    K._to(K.cylinder('washer_window', 0.015, 0.002, (0.645, 1.2 - IN - 0.051, 0.04), rot=(math.pi / 2, 0, 0), mat=M['glass']))
    K._to(K.cylinder('laundry_basket', 0.016, 0.03, (0.7, 1.12, 0.015), mat=M['sack']))
    K.block('clothes_line', 0.64, 0.86, 0.98, 0.982, 0.2, 0.202, M['tape'], bevel=0.0003)
    for i, xx in enumerate((0.67, 0.73, 0.8)):
        sh = K.block('hanging_sheet', xx - 0.025, xx + 0.025, 0.978, 0.986, 0.06 + 0.01 * (i % 2), 0.2, M['bedsheet'], bevel=0.002)
        K.add_lumps(sh, 0.0015, size=0.012)
    K.stairs_down(BMS[0] + 0.003, BMS[2] - 0.003, BMS[1], 1, n=13, rise=PL.UP / 13, run=(BMS[3] - BMS[1]) / 13)
    K.banister(BMS[0] - 0.002, BMS[1] + 0.03, BMS[3])
    bb = K.point_light('laundry_bulb', (0.8, 1.0, 0.22), 0.0, radius=0.004, color=(1.0, 0.85, 0.6)); K._to(bb, 'Lights')


def room_fills(rooms, z_ceiling=K.H, k=3.2):
    """a faint cold light under each room's ceiling (moonlight bouncing round the room), so nothing goes pitch black"""
    for name, (x0, y0, x1, y1) in rooms.items():
        w, d = x1 - x0, y1 - y0
        l = K.area_light('fill_' + name, ((x0 + x1) / 2, (y0 + y1) / 2, z_ceiling - 0.015), ((x0 + x1) / 2, (y0 + y1) / 2, 0.0),
                         k * w * d, min(w, d) * 0.7, (0.55, 0.64, 0.92))
        K._to(l, 'Lights')


def build(house=False):
    extra_materials()
    was = K.HOUSE; K.HOUSE = True                                         # one connected floor: doors open onto rooms
    for name, r in PL.GROUND.items():
        x0, y0, x1, y1 = r
        holes = []
        if name == 'hall': holes = [(MS[0], MS[1], MS[2], MS[3])]
        if name == 'back_stairs': holes = [(BS[0], BS[1], BS[2], BS[3])]
        fh = [(BMS[0], BMS[1], BMS[2], BMS[3])] if name == 'laundry' else []
        K.floor((x0, y0, x1, y1), mat=FLOORS[name], holes=fh)
        K.ceiling((x0, y0, x1, y1), holes=holes)
    for a, b, inward, ops, kw in WALLS:
        w = K.wall(a, b, inward=inward, openings=ops)
        if kw.get('wild'): w['wild'] = True
    flight(MS[0], MS[1], MS[2], MS[3])
    flight(BS[0], BS[1], BS[2], BS[3])
    K.banister(MS[0] - 0.002, MS[1], MS[1] + 0.06)                      # the foot of the main stairs
    furnish()
    K.mood('night', moon_from=(-0.5, 0.2, 0.36), moon_to=(0.2, 0.2, 0.0), moon_energy=18)
    K.mood('night', moon_from=(0.17, 1.8, 0.4), moon_to=(0.17, 1.0, 0.0), moon_energy=14)
    room_fills(PL.GROUND)
    K.HOUSE = was
    if not house:
        K.mood('night', bounds=(0.005, 0.0, 0.0, 0.995, 1.195, K.H), haze_density=0.35)
        f = K.area_light('fill_front', (0.5, -0.9, 0.3), (0.5, 0.4, 0.1), 2.5, 0.8, (0.5, 0.6, 0.9)); K._to(f, 'Lights')
    K.mark('dollhouse_ground', (0.5, -1.05, 0.13), (0.5, 0.4, 0.1), lens=24)
    K.mark('living', (0.3, -0.12, 0.1), (0.12, 0.3, 0.05), lens=22)
    K.mark('dining', (0.36, 0.5, 0.1), (0.15, 0.68, 0.05), lens=22)
    K.mark('kitchen', (0.36, 0.86, 0.11), (0.15, 1.15, 0.07), lens=22)
    K.mark('hall', (0.45, 0.025, 0.1), (0.5, 0.6, 0.09), lens=20)
    K.mark('study', (0.75, -0.1, 0.1), (0.8, 0.35, 0.06), lens=22)
    K.mark('garage', (0.65, 0.5, 0.12), (0.85, 0.65, 0.04), lens=20)
    K.mark('laundry', (0.65, 0.84, 0.12), (0.85, 1.05, 0.08), lens=20)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def opt(name, n=1, default=None):
        if '--' + name not in argv: return default
        i = argv.index('--' + name); v = argv[i + 1:i + 1 + n]; return v if n > 1 else v[0]
    RES = tuple(int(v) for v in opt('res', 2, ('1080', '1920')))
    OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'ground')))
    K.begin('home_ground', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    if opt('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt('blend')))
    os.makedirs(OUT, exist_ok=True)
    for m in (opt('marks') or 'dollhouse_ground,living,dining,kitchen,hall,study,garage,laundry').split(','):
        K.shoot(m, OUT, fstop=float(opt('fstop', 1, '8')))
    print('DONE ground', OUT)
