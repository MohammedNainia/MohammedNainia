"""Haru's house, upstairs: Haru's bedroom (built with the room kit, library/sets/kit.py; see plan.py).

x -0.245..-0.065, y 0..0.32, front open. Her bed along the west wall under the window (the moon), head against the
bathroom wall; a bedside table with her lamp (on, warm); a wardrobe; a small desk and chair by the front; a rug;
drawings pinned on the wall; a teddy on the bed. Her door opens to the upstairs hallway (east wall, y 0.06..0.14).

    blender -b -P library/sets/house/bedroom.py -- [--blend OUT.blend] [--out DIR] [--res W H] [--samples N] [--marks a,b]
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
OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'bedroom')))
MARKS = (opt('marks') or 'wide,bed,door,desk').split(',')

X0, X1, Y0, Y1 = -0.245, -0.065, 0.0, 0.32
MATT = 0.04                                         # mattress top (the contact solver's bed height)
BED = (X0 + K.WT / 2 + 0.002, X0 + K.WT / 2 + 0.112, Y1 - K.WT / 2 - 0.212, Y1 - K.WT / 2 - 0.002)   # x0 x1 y0 y1


def build(house=False):
    """build the room at its own floor level 0 (house.py moves it to its level)"""
    M = K.M; B = K.block; IN = K.WT / 2
    K.floor((X0, Y0, X1, Y1))
    K.ceiling((X0, Y0, X1, Y1))
    K.wall((X0, Y0), (X0, Y1), inward=-1, openings=[K.window(0.14, 0.24, 0.085, 0.185, moon=True)])
    K.wall((X0, Y1), (X1, Y1), inward=-1)                                              # the bathroom wall
    if not house:                                                                      # the hallway builds this one
        K.wall((X1, Y0), (X1, Y1), inward=1, openings=[K.door(0.06, 0.14, angle=-28, hinge='start')])

    # the bed: frame, headboard, mattress, pillow, duvet half turned back
    bx0, bx1, by0, by1 = BED
    B('bed_frame', bx0, bx1, by0, by1, 0.008, MATT - 0.012, M['wood'], bevel=0.002)
    for lx in (bx0 + 0.004, bx1 - 0.004):
        for ly in (by0 + 0.004, by1 - 0.004): B('bed_leg', lx - 0.004, lx + 0.004, ly - 0.004, ly + 0.004, 0, 0.01, M['wood'], bevel=0.001)
    B('headboard', bx0, bx1, by1 - 0.008, by1, 0.0, 0.1, M['wood'], bevel=0.003)
    for i in range(5):
        xx = bx0 + (i + 0.5) * (bx1 - bx0) / 5
        B('headboard_spindle', xx - 0.002, xx + 0.002, by1 - 0.006, by1 - 0.002, 0.1, 0.13, M['wood'], bevel=0.001)
    B('headboard_top', bx0 - 0.002, bx1 + 0.002, by1 - 0.009, by1 + 0.001, 0.128, 0.134, M['wood'], bevel=0.002)
    m = B('mattress', bx0 + 0.002, bx1 - 0.002, by0 + 0.002, by1 - 0.009, MATT - 0.012, MATT, M['bedsheet'], bevel=0.005, coll=True)
    K.add_lumps(m, 0.0008, size=0.02)
    pw = B('pillow', bx0 + 0.016, bx1 - 0.016, by1 - 0.052, by1 - 0.012, MATT - 0.002, MATT + 0.006, M['bedsheet'], bevel=0.004, coll=True)
    K.add_lumps(pw, 0.001, size=0.012)
    dv = B('duvet', bx0 - 0.001, bx1 + 0.001, by0 + 0.002, by1 - 0.07, MATT - 0.002, MATT + 0.008, M['duvet'], bevel=0.004)
    K.add_lumps(dv, 0.0014, size=0.012)
    fold = B('duvet_fold', bx0 - 0.001, bx1 + 0.001, by1 - 0.085, by1 - 0.068, MATT + 0.006, MATT + 0.013, M['duvet'], bevel=0.005)
    K.add_lumps(fold, 0.0012, size=0.01)
    K._to(K.sphere('bed_teddy', 0.009, (bx1 - 0.03, by1 - 0.06, MATT + 0.016), scale=(1, 0.85, 1.1), mat=M['plush']))
    K._to(K.sphere('bed_teddy_head', 0.007, (bx1 - 0.03, by1 - 0.062, MATT + 0.03), mat=M['plush']))

    # bedside table and her lamp (on), by the head of the bed
    nx0, nx1, ny0, ny1 = bx1 + 0.006, bx1 + 0.04, Y1 - IN - 0.036, Y1 - IN - 0.002
    B('bedside_table', nx0, nx1, ny0, ny1, 0.0, 0.045, M['wood'], bevel=0.002)
    B('bedside_drawer', nx0 + 0.003, nx1 - 0.003, ny0 - 0.001, ny0 + 0.001, 0.025, 0.04, M['wood'], bevel=0.001)
    lx, ly = (nx0 + nx1) / 2, (ny0 + ny1) / 2
    K._to(K.cylinder('lamp_base', 0.006, 0.018, (lx, ly, 0.054), mat=M['trim']))
    K._to(K.cylinder('lamp_shade', 0.011, 0.014, (lx, ly, 0.069), mat=M['shade']))
    lamp = K.point_light('bedside_lamp', (lx, ly, 0.069), 0.5, radius=0.006, color=(1.0, 0.66, 0.35)); K._to(lamp, 'Lights')

    # wardrobe against the east wall (north of the door), desk and chair by the front, a rug
    B('wardrobe', X1 - IN - 0.04, X1 - IN - 0.002, 0.17, 0.25, 0.0, 0.16, M['wood'], bevel=0.003)
    B('wardrobe_door_gap', X1 - IN - 0.041, X1 - IN - 0.039, 0.2095, 0.2105, 0.01, 0.155, M['void'], bevel=0)
    for yy in (0.205, 0.215): K._to(K.sphere('wardrobe_knob', 0.0018, (X1 - IN - 0.0425, yy, 0.09), mat=M['brass']))
    dx0, dx1, dy0, dy1 = X0 + IN + 0.002, X0 + IN + 0.06, 0.02, 0.055
    B('desk_top', dx0, dx1, dy0, dy1, 0.052, 0.056, M['wood'], bevel=0.001, coll=True)
    for xx in (dx0 + 0.003, dx1 - 0.003):
        for yy in (dy0 + 0.003, dy1 - 0.003): B('desk_leg', xx - 0.002, xx + 0.002, yy - 0.002, yy + 0.002, 0, 0.052, M['wood'], bevel=0.0006)
    for i, c in enumerate(('book1', 'book3', 'book4')):
        B('desk_book', dx0 + 0.006 + i * 0.006, dx0 + 0.011 + i * 0.006, dy1 - 0.02, dy1 - 0.004, 0.056, 0.074 - i * 0.002, M[c], bevel=0.0005)
    B('drawing_paper', dx0 + 0.025, dx0 + 0.045, dy0 + 0.006, dy0 + 0.024, 0.056, 0.0565, M['paper'], bevel=0.0002, tilt=0.15)
    K.chair(dx0 + 0.03, dy1 + 0.018, facing=180)
    rug = K.cylinder('rug', 0.055, 0.0012, (-0.15, 0.12, 0.0006), mat=M['runner'], verts=64); K._to(rug); K.HP.colliders().objects.link(rug)
    for i, (yy, zz) in enumerate(((0.06, 0.15), (0.09, 0.16), (0.075, 0.12))):         # her drawings, pinned crooked
        K.picture((X0 + IN + 0.001, yy, zz), (0.02, 0.016), normal=(1, 0, 0), crooked=10, mat='paper')

    K.mood('night', moon_from=(-0.6, 0.2, 0.36), moon_to=(-0.15, 0.2, 0.0), bounds=(X0, Y0 - 0.1, 0.0, X1, Y1, K.H))

    K.mark('wide', (-0.14, -0.11, 0.105), (-0.16, Y1, 0.06), lens=20)                 # the whole room from the open front
    K.mark('bed', (-0.09, 0.13, 0.06), (-0.2, 0.26, 0.045), lens=26)                   # low, the bed and the window
    K.mark('door', (-0.2, 0.16, 0.1), (X1, 0.1, 0.09), lens=26)                        # from the bed side to her door
    K.mark('desk', (-0.13, 0.1, 0.09), (-0.215, 0.035, 0.06), lens=30)                 # her desk


if __name__ == '__main__':
    K.begin('bedroom', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    if opt('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt('blend')))
    os.makedirs(OUT, exist_ok=True)
    for m in MARKS: K.shoot(m, OUT, fstop=float(opt('fstop', 1, '5.6')))
    print('DONE bedroom', OUT)
