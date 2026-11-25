"""Haru's house, upstairs: the bathroom (built with the room kit, library/sets/kit.py).

On the floor plan it is behind the hallway's bathroom door: x -0.245..-0.065, y 0.32..0.54 (1.8 x 2.2 m at 1:10).
The near (south) side is open for filming. East wall: the door to the hallway and the toilet. North wall: the
pedestal sink with a mirror cabinet and one bare bulb over it, a small high window with the moon. West wall: the
claw-foot bath with a shower curtain half drawn. Tiles to waist height, faded wallpaper above, a checkered floor.

    blender -b -P library/sets/house/bathroom.py -- [--blend OUT.blend] [--out DIR] [--res W H] [--samples N] [--marks a,b]
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
OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'bathroom')))
MARKS = (opt('marks') or 'wide,mirror,tub,door').split(',')

def build(house=False):
    """build the room at its own floor level 0 (house.py moves it to its level). house=True: walls shared with a
    neighbouring room are left to the room that owns them (see plan.py), walls that only the house needs are added"""
    M = K.M
    X0, X1, Y0, Y1 = -0.245, -0.065, 0.32, 0.6
    K.floor((X0, Y0, X1, Y1), mat='tiles_floor')
    K.ceiling((X0, Y0, X1, Y1))
    if not house:                                   # in the house the hallway builds this wall (and its door)
        K.wall((X1, Y0), (X1, Y1), inward=1, mat='wall_bath', openings=[K.door(0.06, 0.14, angle=-18, hinge='end')])
    K.wall((X0, Y1), (X1, Y1), inward=-1, mat='wall_bath', openings=[K.window(0.03, 0.075, 0.15, 0.205, curtains=False, moon=True)])
    K.wall((X0, Y0), (X0, Y1), inward=-1, mat='wall_bath')
    K.cladding((X1, Y0), (X1, Y1), 1, skip=[(0.053, 0.147)])
    K.cladding((X0, Y1), (X1, Y1), -1)
    K.cladding((X0, Y0), (X0, Y1), -1)
    FL = K.WT / 2 + 0.002                                     # wall surface + cladding

    # the claw-foot bath along the west wall
    tx0, tx1, ty0, ty1, th = X0 + FL + 0.004, X0 + FL + 0.074, Y0 + 0.035, Y0 + 0.19, 0.062
    tub = K.block('bathtub', tx0, tx1, ty0, ty1, 0.012, th, M['enamel'], bevel=0.012)
    cut = K.block('tub_cut', tx0 + 0.006, tx1 - 0.006, ty0 + 0.007, ty1 - 0.007, 0.02, th + 0.02, M['enamel'], bevel=0.01)
    for m_ in list(tub.modifiers): bpy.context.view_layer.objects.active = tub; bpy.ops.object.modifier_apply(modifier=m_.name)
    K.hollow(tub, cut); K.HP.colliders().objects.link(tub)
    K.block('tub_rim', tx0 - 0.001, tx1 + 0.001, ty0 - 0.001, ty1 + 0.001, th - 0.003, th + 0.001, M['enamel'], bevel=0.0018)
    K.block('tub_rim_cut', 0, 0, 0, 0, 0, 0, M['enamel'])                  # placeholder kept simple: the rim reads as a roll
    bpy.data.objects.remove(bpy.data.objects['tub_rim_cut'], do_unlink=True)
    for (fx, fy) in ((tx0 + 0.008, ty0 + 0.012), (tx1 - 0.008, ty0 + 0.012), (tx0 + 0.008, ty1 - 0.012), (tx1 - 0.008, ty1 - 0.012)):
        K._to(K.sphere('claw_foot', 0.0055, (fx, fy, 0.006), scale=(1, 1.3, 1.2), mat=M['brass']))
    K._to(K.cylinder('tub_tap', 0.0022, 0.02, ((tx0 + tx1) / 2, ty1 - 0.004, th + 0.01), mat=M['chrome']))
    K.block('tub_spout', (tx0 + tx1) / 2 - 0.002, (tx0 + tx1) / 2 + 0.002, ty1 - 0.016, ty1 - 0.004, th + 0.018, th + 0.022, M['chrome'], bevel=0.0015)
    K._to(K.sphere('rubber_duck', 0.006, (tx1 - 0.006, ty0 + 0.03, th + 0.006), scale=(1.2, 1, 0.9), mat=M['duck']))
    K._to(K.sphere('rubber_duck_head', 0.004, (tx1 - 0.006, ty0 + 0.024, th + 0.013), mat=M['duck']))
    # shower curtain on a rail, half drawn along the open side of the bath
    rz = 0.21
    K.block('curtain_rail', tx1 - 0.001, tx1 + 0.002, ty0, ty1, rz, rz + 0.003, M['chrome'], bevel=0.001)
    for yy in (ty0, ty1): K.block('rail_bracket', X0 + FL, tx1 + 0.002, yy - 0.0015, yy + 0.0015, rz, rz + 0.003, M['chrome'], bevel=0.001)
    for i in range(9):                                                      # folds of the curtain, gathered toward the wall end
        yy = ty1 - 0.006 - i * 0.0085
        c = K.block('shower_curtain', tx1 - 0.0025, tx1 + 0.0015, yy - 0.0055, yy + 0.0055, th - 0.01, rz, M['shower_curtain'], bevel=0.002)
        c.rotation_euler = (0, 0, math.radians(18 * (-1) ** i)); K.add_lumps(c, 0.0008, size=0.012)

    # the sink and mirror cabinet on the north wall, one bare bulb above
    sx, sy = -0.13, Y1 - FL
    basin = K.block('basin', sx - 0.024, sx + 0.024, sy - 0.038, sy, 0.072, 0.09, M['enamel'], bevel=0.008)
    cut = K.block('basin_cut', sx - 0.019, sx + 0.019, sy - 0.033, sy - 0.006, 0.08, 0.1, M['enamel'], bevel=0.007)
    for m_ in list(basin.modifiers): bpy.context.view_layer.objects.active = basin; bpy.ops.object.modifier_apply(modifier=m_.name)
    K.hollow(basin, cut)
    K._to(K.cylinder('sink_pedestal', 0.009, 0.075, (sx, sy - 0.018, 0.0375), mat=M['enamel']))
    for dx in (-0.01, 0.01): K._to(K.cylinder('sink_tap', 0.0018, 0.012, (sx + dx, sy - 0.004, 0.096), mat=M['chrome']))
    K.block('cabinet', sx - 0.022, sx + 0.022, sy - 0.012, sy, 0.112, 0.165, M['wood'], bevel=0.0015)
    K.block('mirror', sx - 0.019, sx + 0.019, sy - 0.0125, sy - 0.0115, 0.115, 0.162, M['mirror'], bevel=0.0003)
    K._to(K.sphere('bare_bulb', 0.0045, (sx, sy - 0.012, 0.178), scale=(1, 1, 1.3), mat=M['bulb']))
    K.block('bulb_socket', sx - 0.003, sx + 0.003, sy - 0.014, sy, 0.181, 0.188, M['brass'], bevel=0.001)
    bulb = K.point_light('bulb_light', (sx, sy - 0.016, 0.176), 0.35, radius=0.004, color=(1.0, 0.84, 0.6)); K._to(bulb, 'Lights')
    K._to(K.cylinder('toothbrush_cup', 0.0035, 0.009, (sx + 0.016, sy - 0.006, 0.0945), mat=M['enamel']))

    # the toilet against the east wall, south of the door
    wx, wy = X1 - FL, Y0 + 0.03
    K.block('toilet_tank', wx - 0.012, wx, wy - 0.018, wy + 0.018, 0.045, 0.078, M['enamel'], bevel=0.003)
    K._to(K.cylinder('toilet_base', 0.012, 0.03, (wx - 0.026, wy, 0.015), mat=M['enamel']))
    bowl = K.sphere('toilet_bowl', 0.017, (wx - 0.03, wy, 0.035), scale=(1.25, 1.0, 0.55), mat=M['enamel']); K._to(bowl)
    K.block('toilet_seat', wx - 0.05, wx - 0.012, wy - 0.016, wy + 0.016, 0.043, 0.046, M['wood'], bevel=0.003)

    # a towel over a rail by the door, a bath mat
    K.block('towel_rail', X1 - FL - 0.004, X1 - FL - 0.002, Y1 - 0.06, Y1 - 0.02, 0.12, 0.123, M['chrome'], bevel=0.001)
    t_ = K.block('towel', X1 - FL - 0.007, X1 - FL - 0.001, Y1 - 0.058, Y1 - 0.022, 0.075, 0.124, M['towel'], bevel=0.002)
    K.add_lumps(t_, 0.0008, size=0.01)
    K.block('bath_mat', tx1 + 0.004, tx1 + 0.03, ty0 + 0.04, ty0 + 0.11, 0.0, 0.0016, M['bathmat'], bevel=0.0008, coll=True)

    K.mood('night', moon_from=(-0.19, 0.95, 0.42), moon_to=(-0.17, 0.4, 0.0), bounds=(X0, Y0 - 0.1, 0.0, X1, Y1, K.H))

    K.mark('wide', (-0.15, Y0 - 0.1, 0.11), (-0.155, Y1, 0.075), lens=22)            # the whole room from the open side
    K.mark('mirror', (sx + 0.02, sy - 0.11, 0.135), (sx, sy, 0.135), lens=35)         # Haru's eye level at the mirror
    K.mark('tub', (tx1 + 0.065, Y0 - 0.01, 0.085), ((tx0 + tx1) / 2, ty1 - 0.04, 0.05), lens=24)   # over the bath, from its foot
    K.mark('door', (X0 + 0.1, Y1 - 0.04, 0.1), (X1, 0.42, 0.09), lens=26)             # from inside, at the door ajar



if __name__ == '__main__':
    K.begin('bathroom', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    if opt('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt('blend')))
    os.makedirs(OUT, exist_ok=True)
    for m in MARKS: K.shoot(m, OUT, fstop=float(opt('fstop', 1, '5.6')))
    print('DONE bathroom', OUT)
