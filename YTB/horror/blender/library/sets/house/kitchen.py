"""Haru's house, ground floor: the kitchen (built with the room kit, library/sets/kit.py).

On the floor plan it is under the bathroom and the west half of the hallway: x -0.245..0.065, y 0.25..0.6, on the
ground floor (this file builds it at its own floor level z = 0; the ground floor sits 0.26 below the upstairs floor).
North wall: the counter run with the old gas stove, the sink under a window with the moon, wall cupboards, pots on a
rail. North-east corner: a rounded old fridge with its door ajar, cold light spilling out (the night light of this
room). East wall: the door to the hall. West wall: the back door. Middle: a worn table with three chairs.

    blender -b -P library/sets/house/kitchen.py -- [--blend OUT.blend] [--out DIR] [--res W H] [--samples N] [--marks a,b]
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
OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'kitchen')))
MARKS = (opt('marks') or 'wide,fridge,table,sink').split(',')

def build(house=False):
    """build the room at its own floor level 0 (house.py moves it to its level). house=True: walls shared with a
    neighbouring room are left to the room that owns them (see plan.py), walls that only the house needs are added"""
    M = K.M; B = K.block
    X0, X1, Y0, Y1 = -0.245, 0.065, 0.25, 0.6
    IN = K.WT / 2                                    # wall surface offset from the wall line
    K.floor((X0, Y0, X1, Y1), mat='lino')
    K.ceiling((X0, Y0, X1, Y1))
    K.wall((X0, Y1), (X1, Y1), inward=-1, openings=[K.window(0.1, 0.18, 0.1, 0.185, curtains=True, moon=True)])
    K.wall((X1, Y0), (X1, Y1), inward=1, openings=[K.door(0.05, 0.13, angle=-25, hinge='end')])           # to the hall
    K.wall((X0, Y0), (X0, Y1), inward=-1, openings=[K.door(0.1, 0.18, angle=0, hinge='start')])           # back door
    K.cladding((X0, Y1), (X1, Y1), -1, height=0.13, mat='tiles_kitchen')
    if house:                                       # the wall to the living room (open in the standalone preview)
        K.wall((X0, Y0), (X1, Y0), inward=1, openings=[K.door(0.2, 0.28, angle=30, hinge='start')])

    # counter run along the north wall: base cupboards, worktop, sink under the window, stove at the west end
    cy0, cy1, ch = Y1 - IN - 0.045, Y1 - IN, 0.068
    B('base_cupboards', X0 + IN + 0.052, 0.0, cy0 + 0.002, cy1, 0.004, ch - 0.004, M['cabinet'], bevel=0.0012)
    for xx in [X0 + IN + 0.06 + i * 0.033 for i in range(7)]:
        if xx + 0.03 > 0.0: break
        B('cupboard_door', xx, xx + 0.03, cy0 - 0.0005, cy0 + 0.002, 0.01, ch - 0.012, M['cabinet'], bevel=0.0015)
        K._to(K.sphere('cupboard_knob', 0.0018, (xx + 0.026, cy0 - 0.002, ch - 0.02), mat=M['brass']))
    top = B('worktop', X0 + IN + 0.05, 0.002, cy0 - 0.003, cy1, ch - 0.004, ch, M['counter'], bevel=0.001, coll=True)
    sx = -0.105
    basin = B('sink', sx - 0.022, sx + 0.022, cy0 + 0.004, cy1 - 0.004, ch - 0.02, ch + 0.002, M['enamel'], bevel=0.004)
    cut = B('sink_cut', sx - 0.018, sx + 0.018, cy0 + 0.008, cy1 - 0.008, ch - 0.016, ch + 0.01, M['enamel'], bevel=0.003)
    for m_ in list(basin.modifiers): bpy.context.view_layer.objects.active = basin; bpy.ops.object.modifier_apply(modifier=m_.name)
    K.hollow(basin, cut)
    K._to(K.cylinder('sink_tap', 0.002, 0.022, (sx, cy1 - 0.006, ch + 0.011), mat=M['chrome']))
    B('tap_spout', sx - 0.0018, sx + 0.0018, cy1 - 0.02, cy1 - 0.006, ch + 0.02, ch + 0.024, M['chrome'], bevel=0.0012)
    # the old gas stove
    gx0, gx1 = X0 + IN + 0.002, X0 + IN + 0.05
    B('stove', gx0, gx1, cy0 - 0.002, cy1, 0.004, ch + 0.002, M['fridge'], bevel=0.003)
    B('oven_door', gx0 + 0.005, gx1 - 0.005, cy0 - 0.004, cy0 - 0.001, 0.012, 0.05, M['fridge'], bevel=0.002)
    B('oven_window', gx0 + 0.012, gx1 - 0.012, cy0 - 0.0045, cy0 - 0.0035, 0.025, 0.042, M['iron'], bevel=0.001)
    for i, (bx_, by_) in enumerate([(gx0 + 0.013, cy0 + 0.012), (gx1 - 0.013, cy0 + 0.012), (gx0 + 0.013, cy1 - 0.012), (gx1 - 0.013, cy1 - 0.012)]):
        K._to(K.cylinder('burner', 0.007, 0.002, (bx_, by_, ch + 0.003), mat=M['iron']))
    for i in range(4): K._to(K.sphere('stove_knob', 0.002, (gx0 + 0.01 + i * 0.01, cy0 - 0.003, ch - 0.004), mat=M['iron']))
    K._to(K.sphere('kettle', 0.0085, (gx0 + 0.013, cy0 + 0.012, ch + 0.012), scale=(1, 1, 0.85), mat=M['red']))
    sp = K.rounded_box('kettle_spout', (0.002, 0.01, 0.002), (gx0 + 0.013, cy0 + 0.002, ch + 0.016), bevel=0.0008, mat=M['red'])
    sp.rotation_euler = (math.radians(-35), 0, 0); K._to(sp)
    # pots hanging on a rail over the stove
    B('pot_rail', gx0, gx1 + 0.03, cy1 - 0.006, cy1 - 0.003, 0.16, 0.163, M['chrome'], bevel=0.001)
    for i, r in enumerate((0.008, 0.01, 0.007)):
        x_ = gx0 + 0.008 + i * 0.022
        K._to(K.cylinder('hanging_pot', r, 0.012, (x_, cy1 - 0.012, 0.142 - i * 0.004), mat=M['iron']))
        B('pot_hook', x_ - 0.0005, x_ + 0.0005, cy1 - 0.006, cy1 - 0.005, 0.148 - i * 0.004, 0.161, M['chrome'], bevel=0.0002)
    # wall cupboards left of the window
    B('wall_cupboard', X0 + IN + 0.055, -0.15, cy1 - 0.03, cy1, 0.135, 0.2, M['cabinet'], bevel=0.0015)
    for xx in (X0 + IN + 0.058, X0 + IN + 0.081):
        B('wall_cupboard_door', xx, xx + 0.021, cy1 - 0.0315, cy1 - 0.029, 0.138, 0.197, M['cabinet'], bevel=0.0012)
    # things on the worktop: a cereal box, jars, a bread bin
    B('cereal_box', -0.06, -0.044, cy1 - 0.012, cy1 - 0.004, ch, ch + 0.024, M['red'], bevel=0.0006, tilt=0.03)
    for i in range(3): K._to(K.cylinder('jar', 0.0045, 0.012 - i * 0.002, (-0.04 + i * 0.011, cy1 - 0.008, ch + 0.006 - i * 0.001), mat=M['glass']))
    B('bread_bin', -0.15, -0.13, cy1 - 0.02, cy1 - 0.004, ch, ch + 0.016, M['cabinet'], bevel=0.003)

    # the fridge in the north-east corner, its door ajar, cold light spilling out
    fx0, fx1, fy0, fy1, fh = 0.006, X1 - IN - 0.002, Y1 - IN - 0.058, Y1 - IN - 0.002, 0.155
    body = B('fridge', fx0, fx1, fy0, fy1, 0.004, fh, M['fridge'], bevel=0.008)
    cut = B('fridge_cut', fx0 + 0.004, fx1 - 0.004, fy0 - 0.01, fy1 - 0.004, 0.012, fh - 0.01, M['fridge'], bevel=0.004)
    for m_ in list(body.modifiers): bpy.context.view_layer.objects.active = body; bpy.ops.object.modifier_apply(modifier=m_.name)
    K.hollow(body, cut)
    B('fridge_back_glow', fx0 + 0.005, fx1 - 0.005, fy1 - 0.0055, fy1 - 0.0045, 0.013, fh - 0.011, M['fridge_in'], bevel=0)
    for zz in (0.045, 0.085, 0.12):
        B('fridge_shelf', fx0 + 0.005, fx1 - 0.005, fy0 + 0.004, fy1 - 0.006, zz, zz + 0.0015, M['glass'], bevel=0.0003)
    K._to(K.cylinder('milk', 0.005, 0.02, (fx0 + 0.015, fy0 + 0.02, 0.0565), mat=M['enamel']))
    B('leftovers', fx0 + 0.026, fx1 - 0.008, fy0 + 0.012, fy0 + 0.032, 0.0865, 0.095, M['red'], bevel=0.0015)
    hinge = K.empty('fridge_hinge', (fx1, fy0, 0)); K._to(hinge)
    door = B('fridge_door', -(fx1 - fx0), 0.0, -0.006, 0.0, 0.006, fh - 0.002, M['fridge'], bevel=0.006); K.attach(door, hinge)
    hd = B('fridge_handle', -(fx1 - fx0) + 0.004, -(fx1 - fx0) + 0.007, -0.01, -0.006, 0.06, 0.11, M['chrome'], bevel=0.0012); K.attach(hd, hinge)
    hinge.rotation_euler = (0, 0, math.radians(-40))
    cold = K.point_light('fridge_light', ((fx0 + fx1) / 2, fy0 + 0.02, fh - 0.03), 0.3, radius=0.01, color=(0.82, 0.92, 1.0)); K._to(cold, 'Lights')
    spill = K.area_light('fridge_spill', ((fx0 + fx1) / 2, fy0 - 0.002, 0.08), ((fx0 + fx1) / 2 - 0.05, fy0 - 0.15, 0.0), 0.22, 0.05,
                         (0.8, 0.9, 1.0)); K._to(spill, 'Lights')
    K._to(K.cylinder('cat_bowl', 0.008, 0.004, (fx0 - 0.02, fy0 - 0.03, 0.002), mat=M['red']))

    # the table and chairs, a calendar and a clock, a lamp shade (off)
    tx, ty = -0.095, 0.415
    B('table_top', tx - 0.045, tx + 0.045, ty - 0.03, ty + 0.03, 0.056, 0.061, M['counter'], bevel=0.0015, coll=True, tilt=0.004)
    for sx_ in (-1, 1):
        for sy_ in (-1, 1): B('table_leg', tx + sx_ * 0.04 - 0.0025, tx + sx_ * 0.04 + 0.0025, ty + sy_ * 0.025 - 0.0025, ty + sy_ * 0.025 + 0.0025, 0, 0.056, M['counter'], bevel=0.0008)
    K.chair(tx - 0.02, ty + 0.045, facing=180); K.chair(tx + 0.03, ty + 0.047, facing=172); K.chair(tx - 0.06, ty - 0.005, facing=-90)
    K._to(K.cylinder('mug', 0.0035, 0.007, (tx + 0.012, ty - 0.008, 0.0645), mat=M['enamel']))
    cal = K.picture((X1 - IN - 0.001, 0.47, 0.13), (0.024, 0.034), normal=(-1, 0, 0), crooked=2, mat='paper')
    clock = K.cylinder('wall_clock', 0.013, 0.004, (-0.04, Y1 - IN - 0.002, 0.2), rot=(math.pi / 2, 0, 0), mat=M['paper']); K._to(clock)
    for a in (0.4, 2.1):
        hand = K.rounded_box('clock_hand', (0.0008, 0.0006, 0.009 if a < 1 else 0.006), (-0.04, Y1 - IN - 0.0045, 0.2), bevel=0.0002, mat=M['iron'])
        hand.rotation_euler = (0, a, 0); K._to(hand)
    K._to(K.cylinder('lamp_shade', 0.016, 0.012, (tx, ty, K.H - 0.03), mat=M['cabinet']))
    K._to(K.cylinder('lamp_cord', 0.0006, 0.024, (tx, ty, K.H - 0.012), mat=M['iron']))

    K.mood('night', moon_from=(-0.11, 1.0, 0.36), moon_to=(-0.1, 0.4, 0.0), bounds=(X0, Y0 - 0.1, 0.0, X1, Y1, K.H), moon_energy=18, haze_density=0.45)

    K.mark('wide', (-0.09, Y0 - 0.07, 0.105), (-0.09, Y1, 0.065), lens=20)           # the whole kitchen
    K.mark('fridge', (-0.07, 0.36, 0.055), (0.03, 0.55, 0.07), lens=26)              # low, the open fridge
    K.mark('table', (-0.02, 0.32, 0.09), (-0.1, 0.45, 0.055), lens=30)                # over the table
    K.mark('sink', (-0.09, 0.4, 0.105), (-0.105, 0.58, 0.085), lens=28)                 # at the sink, the window above



if __name__ == '__main__':
    K.begin('kitchen', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    if opt('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt('blend')))
    os.makedirs(OUT, exist_ok=True)
    for m in MARKS: K.shoot(m, OUT, fstop=float(opt('fstop', 1, '5.6')))
    print('DONE kitchen', OUT)
