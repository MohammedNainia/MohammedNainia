"""Haru's house, top: the attic (built with the room kit, library/sets/kit.py).

On the floor plan it covers the whole upstairs (x -0.245..0.165, y 0..0.6) with its floor on top of the upstairs
ceiling (z = 0.258). A pitched roof along y with rafters and collar ties; at the far end a gable wall of planks with
a round window and the moon. The pull-down ladder hatch opens down into the hallway (a warm glow comes up through it).
Clutter: stacked cardboard boxes, furniture under dust sheets (one tall shape that looks like someone standing), a
rocking chair facing the window, a dressmaker's dummy, a trunk with a porcelain doll on it, a teddy bear, and a bare
bulb (off) hanging from the ridge on its cord. The near end is open for filming.

    blender -b -P library/sets/house/attic.py -- [--blend OUT.blend] [--out DIR] [--res W H] [--samples N] [--marks a,b]
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
OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'attic')))
MARKS = (opt('marks') or 'wide,chair,hatch,sheets').split(',')

def build(house=False):
    """build the room at its own floor level 0 (house.py moves it to its level). house=True: walls shared with a
    neighbouring room are left to the room that owns them (see plan.py), walls that only the house needs are added"""
    M = K.M; B = K.block
    X0, X1, Y0, Y1 = -0.245, 0.165, 0.0, 0.6
    AZ = K.H + 0.01                                    # attic floor = on top of the upstairs ceiling
    ZE, ZR = AZ + 0.035, AZ + 0.23                     # eaves, ridge
    HATCH = (-0.03, 0.2, 0.03, 0.28)                   # over the hallway

    K.floor((X0, Y0, X1, Y1), holes=[HATCH], z=AZ)
    rx = K.roof(X0, X1, Y0, Y1, ZE, ZR, ridge_x=-0.04)
    for xa in (X0, X1 - K.WT):                         # low knee walls under the eaves
        B('knee_wall', xa, xa + K.WT, Y0, Y1, AZ, ZE, M['planks'], bevel=0.0004)
    K.gable(X0, X1, Y1, AZ, ZE, ZR, rx, inward=-1, round_window=(rx, AZ + 0.12, 0.035))

    # the hatch and its pull-down ladder, down into the hallway; light from the hallway comes up through it
    hx0, hy0, hx1, hy1 = HATCH
    for (a, b, c, d) in ((hx0 - 0.005, hy0, hx0, hy1), (hx1, hy0, hx1 + 0.005, hy1), (hx0 - 0.005, hy0 - 0.005, hx1 + 0.005, hy0),
                         (hx0 - 0.005, hy1, hx1 + 0.005, hy1 + 0.005)):
        B('hatch_frame', a, c, b, d, AZ, AZ + 0.004, M['wood'], bevel=0.001)
    top, bot = Vector((0, hy0 + 0.004, AZ)), Vector((0, 0.36, 0.0))     # down through the hatch into the hallway
    d = bot - top; ln = d.length; ang = math.atan2(-d.z, -d.y)
    for sx in (-0.016, 0.016):
        r = K.rounded_box('ladder_rail', (0.004, ln, 0.006), (sx, (top.y + bot.y) / 2, (top.z + bot.z) / 2), bevel=0.001, mat=M['wood'])
        r.rotation_euler = (-ang, 0, 0); K._to(r)
    for i in range(1, 12):
        p = top + d * (i / 12)
        B('ladder_rung', -0.016, 0.016, p.y - 0.002, p.y + 0.002, p.z - 0.002, p.z + 0.002, M['wood'], bevel=0.0008)
    glow = K.point_light('hallway_glow', (0.0, 0.24, 0.17), 1.0, radius=0.03, color=(1.0, 0.68, 0.38)); K._to(glow, 'Lights')

    # clutter: cardboard boxes stacked under the left slope
    import random
    R = random.Random(5)
    y = 0.06
    while y < 0.5:
        w, dpt, h = R.uniform(0.035, 0.05), R.uniform(0.035, 0.05), R.uniform(0.025, 0.04)
        x0 = X0 + K.WT + 0.004 + R.uniform(0, 0.01)
        bx = B('box', x0, x0 + w, y, y + dpt, AZ, AZ + h, M['cardboard'], bevel=0.0015, tilt=0.03)
        B('box_tape', x0 + w / 2 - 0.003, x0 + w / 2 + 0.003, y, y + dpt, AZ + h - 0.0005, AZ + h + 0.0004, M['tape'], bevel=0.0003)
        if R.random() < 0.6:
            h2 = R.uniform(0.02, 0.03)
            B('box', x0 + 0.004, x0 + w - 0.002, y + 0.003, y + dpt - 0.004, AZ + h, AZ + h + h2, M['cardboard'], bevel=0.0015, tilt=0.06)
        y += dpt + R.uniform(0.004, 0.02)

    # furniture under dust sheets (right side), and one tall shape at the back that could be someone standing
    def sheet(x0, x1, y0, y1, h, lump=0.004):
        ob = K.draped('dust_sheet', x0, x1, y0, y1, h, lump=lump)
        ob.location.z += AZ; bpy.data.objects[ob['hem']].location.z = AZ + 0.002
        return ob
    sheet(0.06, 0.14, 0.1, 0.28, 0.05)                 # a sofa
    sheet(0.07, 0.14, 0.44, 0.55, 0.1, lump=0.005)     # a wardrobe
    tall = sheet(-0.125, -0.09, 0.53, 0.565, 0.165, lump=0.003)   # a standing mirror ... or someone

    # the rocking chair, facing the round window
    cx, cy = rx, 0.4
    B('chair_seat', cx - 0.02, cx + 0.02, cy - 0.018, cy + 0.018, AZ + 0.026, AZ + 0.03, M['wood'], bevel=0.0012)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B('chair_leg', cx + sx * 0.017 - 0.002, cx + sx * 0.017 + 0.002, cy + sy * 0.015 - 0.002, cy + sy * 0.015 + 0.002,
              AZ + 0.006, AZ + 0.027, M['wood'], bevel=0.0008)
        rk = K.rounded_box('chair_rocker', (0.004, 0.058, 0.004), (cx + sx * 0.017, cy, AZ + 0.005), bevel=0.0012, mat=M['wood']); K._to(rk)
        K.add_lumps(rk, 0.0004, size=0.01)
        B('chair_back_post', cx + sx * 0.018 - 0.002, cx + sx * 0.018 + 0.002, cy - 0.019, cy - 0.015, AZ + 0.03, AZ + 0.085, M['wood'], bevel=0.0008)
    for i in range(5):
        xx = cx - 0.012 + i * 0.006
        B('chair_spindle', xx - 0.001, xx + 0.001, cy - 0.018, cy - 0.016, AZ + 0.03, AZ + 0.08, M['wood'], bevel=0.0004)
    B('chair_top_rail', cx - 0.02, cx + 0.02, cy - 0.02, cy - 0.014, AZ + 0.08, AZ + 0.088, M['wood'], bevel=0.0015)

    # the dressmaker's dummy
    dx_, dy_ = 0.03, 0.5
    K._to(K.cylinder('dummy_pole', 0.0018, 0.06, (dx_, dy_, AZ + 0.03), mat=M['wood']))
    for a in range(3):
        t = a * 2 * math.pi / 3
        leg = K.rounded_box('dummy_foot', (0.024, 0.003, 0.003), (dx_ + 0.01 * math.cos(t), dy_ + 0.01 * math.sin(t), AZ + 0.002),
                            bevel=0.001, mat=M['wood']); leg.rotation_euler = (0, 0, t); K._to(leg)
    K._to(K.sphere('dummy_torso', 0.018, (dx_, dy_, AZ + 0.085), scale=(1.0, 0.7, 1.55), mat=M['dummy']))
    K._to(K.sphere('dummy_neck_cap', 0.006, (dx_, dy_, AZ + 0.115), scale=(1, 1, 0.6), mat=M['wood']))

    # the trunk with a porcelain doll sitting on it, a teddy bear on the floor
    tx, ty = -0.17, 0.53
    B('trunk', tx - 0.035, tx + 0.035, ty - 0.022, ty + 0.022, AZ, AZ + 0.035, M['leather'], bevel=0.003)
    for xx in (tx - 0.02, tx + 0.02):
        B('trunk_band', xx - 0.002, xx + 0.002, ty - 0.0232, ty + 0.0232, AZ - 0.0005, AZ + 0.0365, M['brass'], bevel=0.001)
    K._to(K.sphere('doll_head', 0.0075, (tx + 0.01, ty - 0.005, AZ + 0.06), mat=M['porcelain']))
    K._to(K.sphere('doll_body', 0.009, (tx + 0.01, ty - 0.003, AZ + 0.045), scale=(1, 0.8, 1.2), mat=M['sheet_cloth']))
    K._to(K.sphere('doll_hair', 0.0078, (tx + 0.01, ty - 0.003, AZ + 0.062), scale=(1.05, 1.0, 0.95), mat=M['leather']))
    for ex in (-0.0025, 0.0025):
        K._to(K.sphere('doll_eye', 0.0012, (tx + 0.01 + ex, ty - 0.0122, AZ + 0.061), mat=M['wood']))
    bx_, by_ = rx + 0.04, 0.33
    K._to(K.sphere('teddy_body', 0.01, (bx_, by_, AZ + 0.01), scale=(1, 0.85, 1.1), mat=M['plush']))
    K._to(K.sphere('teddy_head', 0.0075, (bx_, by_ - 0.002, AZ + 0.025), mat=M['plush']))
    for ex in (-0.006, 0.006): K._to(K.sphere('teddy_ear', 0.003, (bx_ + ex, by_, AZ + 0.031), mat=M['plush']))

    # the bare bulb on its cord from the ridge (off), with a pull string
    K._to(K.cylinder('bulb_cord', 0.0006, ZR - (AZ + 0.16), (rx, 0.3, (ZR + AZ + 0.16) / 2), mat=M['wood']))
    K._to(K.sphere('bulb_glass', 0.0055, (rx, 0.3, AZ + 0.152), scale=(1, 1, 1.3), mat=M['bulb_off']))
    K._to(K.cylinder('pull_string', 0.0003, 0.05, (rx + 0.004, 0.3, AZ + 0.13), mat=M['tape']))

    K.mood('night', moon_from=(rx + 0.01, 1.0, AZ + 0.32), moon_to=(rx, 0.3, AZ), bounds=(X0, Y0, AZ, X1, Y1, ZR), haze_density=1.6)   # dusty
    fill = K.area_light('attic_fill', (rx, -0.02, AZ + 0.17), (rx, 0.4, AZ + 0.03), 1.6, 0.35, (0.55, 0.64, 0.9)); K._to(fill, 'Lights')
    side = K.area_light('attic_side', (X1 - 0.03, 0.05, AZ + 0.1), (X0 + 0.05, 0.4, AZ + 0.02), 0.6, 0.2, (0.55, 0.64, 0.9)); K._to(side, 'Lights')

    K.mark('wide', (rx, 0.03, AZ + 0.1), (rx, 0.6, AZ + 0.1), lens=18)                    # the whole attic, to the window
    K.mark('chair', (rx + 0.05, 0.27, AZ + 0.045), (rx, 0.45, AZ + 0.06), lens=28)       # behind the rocking chair
    K.mark('hatch', (0.03, 0.13, AZ + 0.12), (0.0, 0.24, AZ), lens=24)                     # looking down the open hatch
    K.mark('sheets', (-0.1, 0.3, AZ + 0.05), (-0.105, 0.55, AZ + 0.08), lens=26)            # the tall sheet at the back



if __name__ == '__main__':
    K.begin('attic', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    if opt('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt('blend')))
    os.makedirs(OUT, exist_ok=True)
    for m in MARKS: K.shoot(m, OUT, fstop=float(opt('fstop', 1, '5.6')))
    print('DONE attic', OUT)
