"""Haru's house, ground floor: the living room (built with the room kit, library/sets/kit.py; see plan.py).

x -0.245..0.065, y 0..0.25, front open. A sagging sofa with a knitted blanket under the window (the moon), a coffee
table, an old CRT television on a cabinet against the east wall (its blue glow is the room's night light), an
armchair facing it, a standard lamp (off), a bookshelf and a grandfather clock on the north wall, a big rug. Doors: to
the hall (east wall, y 0.08..0.16) and to the kitchen (north wall, x -0.045..0.035, built by the kitchen in the house).

    blender -b -P library/sets/house/living_room.py -- [--blend OUT.blend] [--out DIR] [--res W H] [--samples N] [--marks a,b]
"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import kit as K

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(name, n=1, default=None):
    if '--' + name not in argv: return default
    i = argv.index('--' + name); v = argv[i + 1:i + 1 + n]; return v if n > 1 else v[0]
RES = tuple(int(v) for v in opt('res', 2, ('1080', '1920')))
OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'living_room')))
MARKS = (opt('marks') or 'wide,sofa,tv,clock').split(',')

X0, X1, Y0, Y1 = -0.245, 0.065, 0.0, 0.25
SOFA_SEAT = 0.026


def build(house=False):
    """build the room at its own floor level 0 (house.py moves it to its level)"""
    M = K.M; B = K.block; IN = K.WT / 2
    K.floor((X0, Y0, X1, Y1))
    K.ceiling((X0, Y0, X1, Y1))
    K.wall((X0, Y0), (X0, Y1), inward=-1, openings=[K.window(0.07, 0.17, 0.085, 0.185, moon=True)])
    K.wall((X1, Y0), (X1, Y1), inward=1, openings=[K.door(0.08, 0.16, angle=-20, hinge='start')])     # to the hall
    if not house:                                                                      # the kitchen builds this one
        K.wall((X0, Y1), (X1, Y1), inward=-1, openings=[K.door(0.2, 0.28, angle=0, hinge='start')])

    # the sofa under the window, sagging, a knitted blanket over one arm
    sx0, sx1, sy0, sy1 = X0 + IN + 0.002, X0 + IN + 0.047, 0.05, 0.19
    B('sofa_base', sx0, sx1, sy0, sy1, 0.004, SOFA_SEAT - 0.006, M['sofa'], bevel=0.004)
    for k in range(3):
        y0 = sy0 + 0.008 + k * (sy1 - sy0 - 0.016) / 3
        cu = B('sofa_cushion', sx0 + 0.008, sx1, y0 + 0.001, y0 + (sy1 - sy0 - 0.016) / 3 - 0.001, SOFA_SEAT - 0.008, SOFA_SEAT, M['sofa'], bevel=0.005, coll=True)
        K.add_lumps(cu, 0.0012, size=0.012); cu.location.z -= 0.0015 * (k == 1)      # the middle one sags
    B('sofa_back', sx0, sx0 + 0.012, sy0, sy1, SOFA_SEAT - 0.006, 0.058, M['sofa'], bevel=0.005)
    for yy in (sy0, sy1 - 0.01):
        B('sofa_arm', sx0, sx1, yy, yy + 0.01, SOFA_SEAT - 0.006, 0.04, M['sofa'], bevel=0.005)
    bl = B('knit_blanket', sx0 + 0.002, sx1 + 0.004, sy1 - 0.03, sy1 + 0.002, 0.02, 0.042, M['knit_blanket'], bevel=0.004)
    K.add_lumps(bl, 0.002, size=0.01)

    # coffee table, mug, a magazine
    cx0, cx1, cy0, cy1 = -0.165, -0.12, 0.09, 0.15
    B('coffee_table', cx0, cx1, cy0, cy1, 0.022, 0.026, M['wood'], bevel=0.0012, coll=True)
    for xx in (cx0 + 0.003, cx1 - 0.003):
        for yy in (cy0 + 0.003, cy1 - 0.003): B('coffee_leg', xx - 0.0018, xx + 0.0018, yy - 0.0018, yy + 0.0018, 0, 0.022, M['wood'], bevel=0.0006)
    K._to(K.cylinder('mug', 0.0035, 0.007, (cx0 + 0.012, cy0 + 0.015, 0.0295), mat=M['red']))
    B('magazine', cx0 + 0.02, cx0 + 0.04, cy0 + 0.02, cy0 + 0.046, 0.026, 0.0266, M['paper'], bevel=0.0002, tilt=0.2)

    # the old television on its cabinet, screen glowing blue
    tx0, tx1, ty0, ty1 = X1 - IN - 0.036, X1 - IN - 0.002, 0.168, 0.232
    B('tv_cabinet', tx0, tx1, ty0, ty1, 0.0, 0.03, M['wood'], bevel=0.0015)
    B('tv_body', tx0 + 0.004, tx1, ty0 + 0.006, ty1 - 0.006, 0.03, 0.074, M['iron'], bevel=0.006)
    B('tv_screen', tx0 + 0.003, tx0 + 0.005, ty0 + 0.011, ty1 - 0.015, 0.037, 0.068, M['tv_screen'], bevel=0.003)
    for zz in (0.06, 0.05): K._to(K.sphere('tv_knob', 0.0018, (tx0 + 0.004, ty1 - 0.01, zz), mat=M['chrome']))
    for a in (-0.4, 0.5):
        ant = K.rounded_box('tv_antenna', (0.001, 0.001, 0.035), ((tx0 + tx1) / 2 + 0.004, (ty0 + ty1) / 2, 0.088), bevel=0.0003, mat=M['chrome'])
        ant.rotation_euler = (a, 0, 0); K._to(ant)
    glow = K.area_light('tv_glow', (tx0 - 0.001, (ty0 + ty1) / 2, 0.052), (X0, 0.12, 0.03), 0.35, 0.03, (0.55, 0.7, 1.0)); K._to(glow, 'Lights')

    # an armchair facing the television, a standard lamp (off) by the sofa
    ac = K.empty('armchair', (-0.04, 0.07, 0)); K._to(ac); ac.rotation_euler = (0, 0, math.radians(-150))
    for nm, a, b, c, d, e, f in (('seat', -0.02, 0.02, -0.018, 0.02, 0.008, SOFA_SEAT), ('back', -0.02, 0.02, 0.012, 0.022, SOFA_SEAT, 0.065),
                                  ('arm_l', -0.024, -0.016, -0.018, 0.022, 0.008, 0.042), ('arm_r', 0.016, 0.024, -0.018, 0.022, 0.008, 0.042)):
        ob = B('armchair_' + nm, a, b, c, d, e, f, M['sofa'], bevel=0.005); K.attach(ob, ac); K.add_lumps(ob, 0.0008, size=0.012)
    K._to(K.cylinder('standard_lamp_pole', 0.0015, 0.14, (X0 + IN + 0.02, 0.215, 0.07), mat=M['brass']))
    K._to(K.cylinder('standard_lamp_base', 0.008, 0.003, (X0 + IN + 0.02, 0.215, 0.0015), mat=M['brass']))
    K._to(K.cylinder('standard_lamp_shade', 0.014, 0.022, (X0 + IN + 0.02, 0.215, 0.148), mat=M['cabinet']))

    # bookshelf and a grandfather clock on the north wall
    bx0, bx1 = X0 + IN + 0.045, X0 + IN + 0.11
    B('bookshelf', bx0, bx1, Y1 - IN - 0.02, Y1 - IN - 0.001, 0.0, 0.15, M['wood'], bevel=0.0015)
    import random
    R = random.Random(3)
    for shelf in (0.012, 0.048, 0.084, 0.12):
        B('shelf', bx0 + 0.002, bx1 - 0.002, Y1 - IN - 0.021, Y1 - IN - 0.019, shelf - 0.002, shelf, M['wood'], bevel=0.0004)
        x = bx0 + 0.004
        while x < bx1 - 0.008:
            w = R.uniform(0.003, 0.0055); h = R.uniform(0.018, 0.03)
            B('book', x, x + w, Y1 - IN - 0.018, Y1 - IN - 0.004, shelf, shelf + h, M[R.choice(['book1', 'book2', 'book3', 'book4'])], bevel=0.0004)
            x += w + 0.0005
    gx = -0.105
    B('clock_case', gx - 0.012, gx + 0.012, Y1 - IN - 0.016, Y1 - IN - 0.001, 0.0, 0.17, M['wood'], bevel=0.002)
    B('clock_hood', gx - 0.014, gx + 0.014, Y1 - IN - 0.018, Y1 - IN - 0.001, 0.15, 0.19, M['wood'], bevel=0.003)
    face = K.cylinder('clock_face', 0.009, 0.002, (gx, Y1 - IN - 0.019, 0.17), rot=(math.pi / 2, 0, 0), mat=M['paper']); K._to(face)
    B('clock_window', gx - 0.006, gx + 0.006, Y1 - IN - 0.0172, Y1 - IN - 0.016, 0.04, 0.12, M['glass'], bevel=0.001)
    K._to(K.cylinder('pendulum', 0.004, 0.001, (gx, Y1 - IN - 0.015, 0.06), rot=(math.pi / 2, 0, 0), mat=M['brass']))
    rug = K.block('rug', -0.185, -0.005, 0.035, 0.205, 0.0, 0.0012, M['runner'], bevel=0.0006, coll=True); K.add_lumps(rug, 0.0005, size=0.02)
    K.picture((X1 - IN - 0.001, 0.04, 0.13), (0.026, 0.034), normal=(-1, 0, 0))
    K.picture((X1 - IN - 0.001, 0.2, 0.135), (0.03, 0.022), normal=(-1, 0, 0))

    K.mood('night', moon_from=(-0.6, 0.12, 0.36), moon_to=(-0.15, 0.12, 0.0), bounds=(X0, Y0 - 0.1, 0.0, X1, Y1, K.H), moon_energy=16)

    K.mark('wide', (-0.09, -0.12, 0.1), (-0.09, Y1, 0.05), lens=20)                    # the whole room from the open front
    K.mark('sofa', (-0.06, 0.1, 0.05), (-0.22, 0.13, 0.035), lens=26)                  # the sofa under the window
    K.mark('tv', (-0.15, 0.12, 0.05), (0.04, 0.2, 0.05), lens=28)                      # from the sofa: the glowing TV
    K.mark('clock', (-0.09, 0.08, 0.06), (-0.105, Y1, 0.11), lens=30)                  # the grandfather clock


if __name__ == '__main__':
    K.begin('living_room', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    if opt('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt('blend')))
    os.makedirs(OUT, exist_ok=True)
    for m in MARKS: K.shoot(m, OUT, fstop=float(opt('fstop', 1, '5.6')))
    print('DONE living_room', OUT)
