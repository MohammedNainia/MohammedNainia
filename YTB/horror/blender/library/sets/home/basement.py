"""Haru's home, basement (see plan.py): built at its own floor level 0 (the house puts it 0.26 below the ground floor).

An ordinary basement under the back of the house (x 0.40..1.0, y 0.45..1.2): concrete floor and walls, exposed joists
with pipes, the stairs coming down from the laundry, a boiler and a water heater, metal shelves of boxes and jars,
some old furniture kept down here, a workbench, two small high windows, bare bulbs (one left on).

    blender -b -P library/sets/home/basement.py -- [--out DIR] [--res W H] [--samples N] [--marks a,b] [--blend F]
"""
import bpy, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import kit as K
import props as PR
import plan as PL
import ground as G

X0, Y0, X1, Y1 = PL.BASEMENT
BMS = PL.BASEMENT_STAIRS
WIN = K.window


def build(house=False):
    G.extra_materials(); M = K.M; IN = K.WT / 2
    if 'concrete_wall' not in M: M['concrete_wall'] = K.painted('concrete_wall', (0.22, 0.22, 0.2), rough=0.95)
    was = K.HOUSE; K.HOUSE = True
    K.floor((X0, Y0, X1, Y1), mat='concrete')
    K.ceiling((X0, Y0, X1, Y1), holes=[(BMS[0], BMS[1], BMS[2], BMS[3])])
    for a, b, inward, ops, wild in (((X0, Y0), (X0, Y1), -1, [], False),
                                    ((X0, Y1), (X1, Y1), -1, [], False),
                                    ((X1, Y0), (X1, Y1), 1, [WIN(0.15, 0.25, 0.19, 0.235, curtains=False, moon=True),
                                                             WIN(0.45, 0.55, 0.19, 0.235, curtains=False)], False),
                                    ((X0, Y0), (X1, Y0), 1, [], True)):                   # the front wall: a shot can hide it
        w = K.wall(a, b, inward=inward, openings=ops, mat='concrete_wall', skirting=False)
        if wild: w['wild'] = True
    # exposed joists and pipes under the ground floor
    x = X0 + 0.04
    while x < X1:
        K.block('joist', x - 0.004, x + 0.004, Y0, Y1, K.H - 0.022, K.H - 0.008, M['wood'], bevel=0.0008); x += 0.06
    for yy, r in ((0.52, 0.004), (0.56, 0.003)):
        p = K.cylinder('pipe', r, X1 - X0, ((X0 + X1) / 2, yy, K.H - 0.03), rot=(0, math.pi / 2, 0), mat=M['metal_shelf']); K._to(p)
    # the boiler and water heater in the back corner, metal shelves along the west wall
    K.block('boiler', X0 + IN + 0.005, X0 + IN + 0.055, Y1 - IN - 0.045, Y1 - IN, 0.0, 0.11, M['washer'], bevel=0.004)
    K.block('boiler_door', X0 + IN + 0.015, X0 + IN + 0.045, Y1 - IN - 0.046, Y1 - IN - 0.044, 0.02, 0.05, M['iron'], bevel=0.002)
    K._to(K.cylinder('flue', 0.006, 0.14, (X0 + IN + 0.03, Y1 - IN - 0.02, 0.18), mat=M['metal_shelf']))
    K._to(K.cylinder('water_heater', 0.02, 0.13, (X0 + IN + 0.09, Y1 - IN - 0.022, 0.065), mat=M['washer']))
    for (y0, y1) in ((0.55, 0.72), (0.76, 0.93)):
        for zz in (0.002, 0.05, 0.1, 0.15):
            K.block('metal_shelf', X0 + IN + 0.002, X0 + IN + 0.03, y0, y1, zz, zz + 0.003, M['metal_shelf'], bevel=0.0005)
        for yy in (y0 + 0.002, y1 - 0.002):
            for xx in (X0 + IN + 0.004, X0 + IN + 0.028): K.block('shelf_post', xx - 0.0012, xx + 0.0012, yy - 0.0012, yy + 0.0012, 0, 0.17, M['metal_shelf'], bevel=0.0003)
        for zz in (0.005, 0.053, 0.103):
            yy = y0 + 0.005
            while yy < y1 - 0.03:
                K.block('box', X0 + IN + 0.004, X0 + IN + 0.028, yy, yy + 0.025, zz, zz + 0.03, M['cardboard'], bevel=0.0012, tilt=0.03)
                yy += 0.029
        for i in range(6): K._to(K.cylinder('jar', 0.004, 0.012, (X0 + IN + 0.016, y0 + 0.01 + i * 0.012, 0.159), mat=M['glass']))
    # old furniture kept down here, a workbench, paint tins, a bicycle against the wall
    PR.armchair(0.6, 0.6, 30)
    K.block('old_table', 0.64, 0.74, 0.7, 0.76, 0.055, 0.06, M['wood'], bevel=0.0015)
    for xx in (0.645, 0.735):
        for yy in (0.705, 0.755): K.block('old_table_leg', xx - 0.002, xx + 0.002, yy - 0.002, yy + 0.002, 0, 0.055, M['wood'], bevel=0.0005)
    K.block('workbench', X1 - IN - 0.03, X1 - IN, 0.5, 0.64, 0.06, 0.065, M['wood'], bevel=0.0015)
    for yy in (0.505, 0.635): K.block('workbench_leg', X1 - IN - 0.028, X1 - IN - 0.024, yy - 0.002, yy + 0.002, 0, 0.06, M['wood'], bevel=0.0005)
    for i in range(3): K._to(K.cylinder('paint_tin', 0.006, 0.01, (0.9 + i * 0.014, 0.7, 0.005), mat=M[['red', 'cabinet', 'washer'][i]]))
    bk = PR.holder('bicycle', 0.78, Y1 - IN - 0.01, 0)
    for xx in (-0.03, 0.03):
        wh = K.cylinder('bike_wheel', 0.022, 0.002, (0, 0, 0), rot=(0, math.pi / 2, 0), mat=M['iron'], verts=32); K._to(wh); K.attach(wh, bk)
        wh.rotation_euler = (math.pi / 2, 0, math.pi / 2); wh.location = (xx, 0, 0.022)
    PR.part(bk, 'bike_frame', -0.03, 0.03, -0.001, 0.001, 0.03, 0.034, 'red', bevel=0.0008)
    # bare bulbs: one left on over the middle, one off by the stairs
    for (bx, by, on) in ((0.7, 0.75, True), (0.9, 1.05, False)):
        K._to(K.cylinder('bulb_cord', 0.0004, 0.03, (bx, by, K.H - 0.024), mat=M['tape']))
        K._to(K.sphere('bulb', 0.004, (bx, by, K.H - 0.042), scale=(1, 1, 1.3), mat=M['bulb' if on else 'bulb_off']))
        if on:
            lt = K.point_light('basement_bulb', (bx, by, K.H - 0.045), 0.3, radius=0.004, color=(1.0, 0.82, 0.55)); K._to(lt, 'Lights')
    K.mood('night', moon_from=(1.4, 0.65, 0.4), moon_to=(0.8, 0.65, 0.0), moon_energy=10)
    G.room_fills({'basement': (X0, Y0, X1, Y1)}, k=1.6)
    K.HOUSE = was
    if not house: K.mood('night', bounds=(X0 + 0.005, Y0 + 0.005, 0.0, X1 - 0.005, Y1 - 0.005, K.H), haze_density=0.5)
    K.mark('basement', (0.5, 0.5, 0.12), (0.8, 1.0, 0.06), lens=20)
    K.mark('basement_stairs', (0.75, 1.1, 0.1), (0.93, 1.0, 0.12), lens=22)
    K.mark('basement_shelves', (0.62, 0.95, 0.09), (0.43, 0.7, 0.07), lens=22)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def opt(name, n=1, default=None):
        if '--' + name not in argv: return default
        i = argv.index('--' + name); v = argv[i + 1:i + 1 + n]; return v if n > 1 else v[0]
    RES = tuple(int(v) for v in opt('res', 2, ('1080', '1920')))
    OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'basement')))
    K.begin('home_basement', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    os.makedirs(OUT, exist_ok=True)
    for m in (opt('marks') or 'basement,basement_stairs,basement_shelves').split(','): K.shoot(m, OUT, fstop=float(opt('fstop', 1, '8')))
    print('DONE basement', OUT)
