"""Haru's home, attic (see plan.py): built at its own floor level 0 (the house puts it on top of the upstairs ceiling).

An ordinary attic over the whole house: a pitched roof along y with rafters, a round window in each gable end (the
front gable is a wall a shot can hide), boarded floor with the hatch from the landing, low knee walls under the
eaves, and the things people keep up there: boxes, suitcases, an old chair and lamp, a rolled-up rug, the water tank,
a bare bulb on the ridge.

    blender -b -P library/sets/home/attic.py -- [--out DIR] [--res W H] [--samples N] [--marks a,b] [--blend F]
"""
import bpy, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import kit as K
import props as PR
import plan as PL
import ground as G

X0, Y0, X1, Y1 = PL.FOOTPRINT
ZE, ZR, RX = 0.035, 0.33, 0.5


def build(house=False):
    G.extra_materials(); M = K.M
    was = K.HOUSE; K.HOUSE = True
    K.floor((X0, Y0, X1, Y1), holes=[PL.ATTIC_HATCH], mat='planks')
    K.roof(X0, X1, Y0, Y1, ZE, ZR, ridge_x=RX, spacing=0.08)
    for xa in (X0, X1 - K.WT): K.block('knee_wall', xa, xa + K.WT, Y0, Y1, 0, ZE, M['planks'], bevel=0.0004)
    K.gable(X0, X1, Y1, 0.0, ZE, ZR, RX, inward=-1, round_window=(RX, 0.16, 0.04))
    fg = K.gable(X0, X1, Y0, 0.0, ZE, ZR, RX, inward=1, round_window=(RX, 0.16, 0.04), moon=False, sky=False); fg['wild'] = True
    hx0, hy0, hx1, hy1 = PL.ATTIC_HATCH                                    # the hatch frame round the opening
    for (a, b, c, d) in ((hx0 - 0.005, hy0 - 0.005, hx1 + 0.005, hy0), (hx0 - 0.005, hy1, hx1 + 0.005, hy1 + 0.005),
                         (hx0 - 0.005, hy0, hx0, hy1), (hx1, hy0, hx1 + 0.005, hy1)):
        K.block('hatch_frame', a, c, b, d, 0.0, 0.004, M['wood'], bevel=0.001)
    # what is kept up here: boxes under the eaves on both sides, suitcases, an old chair and lamp, a rolled rug, the tank
    PR.boxes(0.03, 0.13, 0.08, 1.12, seed=31); PR.boxes(0.87, 0.97, 0.08, 1.12, seed=32)
    for i, (sx, sy) in enumerate(((0.3, 0.2), (0.33, 0.24), (0.68, 0.95))):
        K.block('suitcase', sx - 0.025, sx + 0.025, sy - 0.01, sy + 0.01, 0.0 + 0.0 * i, 0.035, M[['leather', 'coat', 'red'][i]], bevel=0.003)
        K.block('suitcase_handle', sx - 0.006, sx + 0.006, sy - 0.002, sy + 0.002, 0.035, 0.039, M['leather'], bevel=0.001)
    K.chair(0.62, 0.3, facing=20)
    K._to(K.cylinder('old_lamp_pole', 0.0015, 0.13, (0.66, 0.36, 0.065), mat=M['brass']))
    K._to(K.cylinder('old_lamp_shade', 0.013, 0.02, (0.66, 0.36, 0.135), mat=M['cabinet']))
    rr = K.cylinder('rolled_rug', 0.01, 0.16, (0.4, 0.75, 0.01), rot=(math.pi / 2, 0, 0), mat=M['runner']); K._to(rr)
    K.block('water_tank', 0.42, 0.58, 1.02, 1.14, 0.0, 0.09, M['metal_shelf'], bevel=0.004)
    K.block('tank_lid', 0.415, 0.585, 1.015, 1.145, 0.09, 0.094, M['wood'], bevel=0.002)
    K._to(K.cylinder('bulb_cord', 0.0005, 0.08, (RX, 0.55, ZR - 0.05), mat=M['tape']))
    K._to(K.sphere('bulb', 0.0055, (RX, 0.55, ZR - 0.094), scale=(1, 1, 1.3), mat=M['bulb_off']))
    K.mood('night', moon_from=(RX + 0.02, 1.9, 0.4), moon_to=(RX, 0.6, 0.0), moon_energy=22)
    G.room_fills({'attic': (0.15, 0.05, 0.85, 1.15)}, z_ceiling=0.2, k=3.0)
    K.HOUSE = was
    if not house: K.mood('night', bounds=(X0 + 0.01, Y0, 0.0, X1 - 0.01, Y1 - 0.01, ZR), haze_density=0.5)
    K.mark('attic', (RX, 0.06, 0.12), (RX, 1.1, 0.1), lens=18)
    K.mark('attic_hatch', (0.52, 0.45, 0.14), (0.5, 0.64, 0.0), lens=24)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def opt(name, n=1, default=None):
        if '--' + name not in argv: return default
        i = argv.index('--' + name); v = argv[i + 1:i + 1 + n]; return v if n > 1 else v[0]
    RES = tuple(int(v) for v in opt('res', 2, ('1080', '1920')))
    OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'attic')))
    K.begin('home_attic', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    os.makedirs(OUT, exist_ok=True)
    for m in (opt('marks') or 'attic,attic_hatch').split(','): K.shoot(m, OUT, fstop=float(opt('fstop', 1, '8')))
    print('DONE attic', OUT)
