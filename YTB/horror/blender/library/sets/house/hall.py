"""Haru's house, ground floor: the hall (built with the room kit, library/sets/kit.py; see plan.py).

x 0.065..0.165, y 0..0.6, front open. The front door (east wall, y 0.03..0.11), a coat rack with coats hanging on it,
an umbrella stand, a little table with a telephone and a lamp (on, dim), a runner. The stairs come down into it from
the upstairs hallway (the hallway module builds the flight); the space under the stairs stays dark. The kitchen and
living room build the west wall (x 0.065) with their doors.

    blender -b -P library/sets/house/hall.py -- [--blend OUT.blend] [--out DIR] [--res W H] [--samples N] [--marks a,b]
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
OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'hall')))
MARKS = (opt('marks') or 'front,door,phone').split(',')

X0, X1, Y0, Y1 = 0.065, 0.165, 0.0, 0.6
STAIRWELL = (0.065, 0.15, 0.165, 0.45)


def build(house=False):
    """build the room at its own floor level 0 (house.py moves it to its level)"""
    M = K.M; B = K.block; IN = K.WT / 2
    K.floor((X0, Y0, X1, Y1))
    K.ceiling((X0, Y0, X1, Y1), holes=[STAIRWELL])
    K.wall((X1, Y0), (X1, Y1), inward=1, openings=[K.door(0.03, 0.11, angle=0, hinge='end')])            # the front door
    K.wall((X0, Y1), (X1, Y1), inward=-1)
    K.runner(X0 + 0.02, X1 - 0.02, 0.01, 0.14)
    K.runner(X0 + 0.02, X1 - 0.02, 0.46, 0.59)

    # coat rack by the front door, three coats hanging like people
    rx, ry = X1 - IN - 0.012, 0.16
    K._to(K.cylinder('coat_rack_pole', 0.002, 0.17, (rx, ry, 0.085), mat=M['wood']))
    for a in range(3):
        t = a * 2 * math.pi / 3
        f = K.rounded_box('coat_rack_foot', (0.022, 0.003, 0.003), (rx + 0.009 * math.cos(t), ry + 0.009 * math.sin(t), 0.002), bevel=0.001, mat=M['wood'])
        f.rotation_euler = (0, 0, t); K._to(f)
    for i, (dx, dy, h) in enumerate(((-0.008, -0.004, 0.11), (0.004, 0.009, 0.1), (0.006, -0.009, 0.09))):
        c = K.sphere('coat', 0.012, (rx + dx, ry + dy, 0.165 - h / 2), scale=(0.9, 0.7, h / 0.024), mat=M['coat']); K._to(c)
        K.add_lumps(c, 0.0012, size=0.01)
    K._to(K.cylinder('umbrella_stand', 0.007, 0.03, (X1 - IN - 0.012, 0.125, 0.015), mat=M['brass']))
    for dx in (-0.002, 0.003): K._to(K.cylinder('umbrella', 0.0018, 0.06, (X1 - IN - 0.012 + dx, 0.125, 0.045), mat=M['iron']))

    # the telephone table at the back with a lamp left on (dim)
    tx0, tx1, ty0, ty1 = X0 + 0.02, X0 + 0.06, Y1 - IN - 0.03, Y1 - IN - 0.002
    B('phone_table', tx0, tx1, ty0, ty1, 0.05, 0.054, M['wood'], bevel=0.001)
    for xx in (tx0 + 0.003, tx1 - 0.003):
        for yy in (ty0 + 0.003, ty1 - 0.003): B('phone_table_leg', xx - 0.0016, xx + 0.0016, yy - 0.0016, yy + 0.0016, 0, 0.05, M['wood'], bevel=0.0005)
    B('telephone', tx0 + 0.006, tx0 + 0.02, ty0 + 0.006, ty0 + 0.018, 0.054, 0.062, M['red'], bevel=0.002)
    B('receiver', tx0 + 0.005, tx0 + 0.021, ty0 + 0.009, ty0 + 0.015, 0.062, 0.066, M['red'], bevel=0.0015)
    K._to(K.cylinder('hall_lamp_base', 0.005, 0.014, (tx1 - 0.01, ty0 + 0.014, 0.061), mat=M['brass']))
    K._to(K.cylinder('hall_lamp_shade', 0.009, 0.012, (tx1 - 0.01, ty0 + 0.014, 0.074), mat=M['shade']))
    lt = K.point_light('hall_lamp', (tx1 - 0.01, ty0 + 0.014, 0.074), 0.25, radius=0.006, color=(1.0, 0.66, 0.35)); K._to(lt, 'Lights')
    K.picture((X1 - IN - 0.001, 0.3, 0.13), (0.03, 0.04), normal=(-1, 0, 0))
    K.picture((X1 - IN - 0.001, 0.52, 0.14), (0.022, 0.03), normal=(-1, 0, 0))

    K.mood('night', bounds=(X0, Y0 - 0.1, 0.0, X1, Y1, K.H))

    K.mark('front', (0.115, -0.08, 0.09), (0.115, 0.5, 0.06), lens=22)                 # from the open front, down the hall
    K.mark('door', (0.09, 0.2, 0.08), (X1, 0.07, 0.09), lens=24)                       # the front door and the coats
    K.mark('phone', (0.13, 0.46, 0.08), (0.09, Y1, 0.06), lens=28)                     # the telephone table


if __name__ == '__main__':
    K.begin('hall', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    if opt('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt('blend')))
    os.makedirs(OUT, exist_ok=True)
    for m in MARKS: K.shoot(m, OUT, fstop=float(opt('fstop', 1, '5.6')))
    print('DONE hall', OUT)
