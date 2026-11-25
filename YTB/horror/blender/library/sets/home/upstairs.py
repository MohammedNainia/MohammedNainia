"""Haru's home, upstairs (see plan.py): built at its own floor level 0 (the house lifts it by plan.UP).

An ordinary family upstairs: Haru's bedroom (front left), the bathroom (middle left), the guest bedroom (back left),
Mum's bedroom (the whole right side, front and middle), a second bathroom (back right), and the long landing down the
middle with both stairwells, banisters, a linen cupboard and a window at the far end.
Places to hide: under the beds, inside the wardrobes and the linen cupboard, behind the shower curtains.

    blender -b -P library/sets/home/upstairs.py -- [--out DIR] [--res W H] [--samples N] [--marks a,b] [--blend F]
"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import kit as K
import props as PR
import plan as PL
import ground as G

D = K.door; WIN = K.window
MS, BS = PL.MAIN_STAIRS, PL.BACK_STAIRS
ROOMS = {'haru_bedroom': PL.rect('A', 'front'), 'bathroom': PL.rect('A', 'middle'), 'guest_bedroom': PL.rect('A', 'back'),
         'landing': (0.40, 0.0, 0.60, 1.2), 'mum_bedroom': (0.60, 0.0, 1.0, 0.80), 'bathroom2': PL.rect('C', 'back')}
FLOORS = {'haru_bedroom': 'floor', 'bathroom': 'tiles_floor', 'guest_bedroom': 'floor', 'landing': 'floor', 'mum_bedroom': 'floor',
          'bathroom2': 'tiles_floor'}
WALLS = [
    ((0.0, 0.0), (0.0, 1.2), -1, [WIN(0.14, 0.30, 0.085, 0.19, moon=True), WIN(0.58, 0.66, 0.13, 0.19, curtains=False),
                                  WIN(0.95, 1.07, 0.09, 0.19)], 'wall'),                              # west
    ((0.0, 1.2), (1.0, 1.2), -1, [WIN(0.12, 0.24, 0.09, 0.19), WIN(0.45, 0.55, 0.08, 0.2, moon=True), WIN(0.75, 0.88, 0.09, 0.19)], 'wall'),
    ((1.0, 0.0), (1.0, 1.2), 1, [WIN(0.15, 0.30, 0.085, 0.19, moon=True), WIN(0.6, 0.68, 0.11, 0.18), WIN(0.95, 1.07, 0.09, 0.19)], 'wall'),
    ((0.40, 0.0), (0.60, 0.0), 1, [WIN(0.06, 0.14, 0.09, 0.19, curtains=False, sky=False)], 'wild'),            # front of the landing
    ((0.40, 0.0), (0.40, 1.2), 1, [D(0.32, 0.40, angle=20), D(0.55, 0.63, angle=20),
                                   D(1.135, 1.195, angle=20)], 'wall'),                               # landing | Haru, bath, guest
    ((0.60, 0.0), (0.60, 1.2), -1, [D(0.30, 0.38, angle=-20), D(0.90, 0.98, angle=-20)], 'wall'),   # landing | Mum, bathroom 2
    ((0.0, 0.45), (0.40, 0.45), 1, [], 'wall'), ((0.0, 0.80), (0.40, 0.80), 1, [], 'wall_bath'),
    ((0.60, 0.80), (1.0, 0.80), 1, [], 'wall_bath'),
]


def furnish():
    M = K.M; IN = K.WT / 2
    # --- Haru's bedroom: her bed under the window, wardrobe, bedside lamp, desk, toy chest, rug, drawings
    PR.bed(0.07, 0.12, 0, duvet='duvet')
    PR.bedside(0.145, 0.29, 0, energy=0.45)
    w = PR.wardrobe(0.3, 0.45 - IN - 0.046, 0)
    PR.swing(bpy.data.objects[w['doors'][1]], 25)                        # one door left ajar
    K.block('desk_top', 0.30, 0.38, 0.02, 0.06, 0.052, 0.056, M['wood'], bevel=0.001, coll=True)
    for xx in (0.303, 0.377):
        for yy in (0.023, 0.057): K.block('desk_leg', xx - 0.002, xx + 0.002, yy - 0.002, yy + 0.002, 0, 0.052, M['wood'], bevel=0.0006)
    K.chair(0.34, 0.08, facing=180)
    K.block('toy_chest', 0.04, 0.1, 0.07, 0.105, 0.0, 0.03, M['red'], bevel=0.003)
    K.block('toy_chest_lid', 0.038, 0.102, 0.068, 0.107, 0.03, 0.034, M['red'], bevel=0.003)
    K._to(K.sphere('teddy', 0.009, (0.1, 0.27, 0.07), scale=(1, 0.85, 1.1), mat=M['plush']))
    K._to(K.sphere('teddy_head', 0.007, (0.1, 0.268, 0.085), mat=M['plush']))
    r = K.cylinder('rug', 0.06, 0.0012, (0.22, 0.2, 0.0006), mat=M['runner'], verts=64); K._to(r); K.HP.colliders().objects.link(r)
    for yy, zz in ((0.36, 0.15), (0.4, 0.13), (0.38, 0.17)): K.picture((IN + 0.001, yy, zz), (0.02, 0.016), normal=(1, 0, 0), crooked=10, mat='paper')
    # --- bathroom: claw-foot bath with a shower curtain along the west wall, sink and mirror, toilet, one bare bulb
    tx0, tx1, ty0, ty1 = IN + 0.004, IN + 0.074, 0.5, 0.66
    tub = K.block('bathtub', tx0, tx1, ty0, ty1, 0.012, 0.062, M['enamel'], bevel=0.012)
    cut = K.block('tub_cut', tx0 + 0.006, tx1 - 0.006, ty0 + 0.007, ty1 - 0.007, 0.02, 0.08, M['enamel'], bevel=0.01)
    for m_ in list(tub.modifiers): bpy.context.view_layer.objects.active = tub; bpy.ops.object.modifier_apply(modifier=m_.name)
    K.hollow(tub, cut); K.HP.colliders().objects.link(tub)
    for (fx, fy) in ((tx0 + 0.008, ty0 + 0.012), (tx1 - 0.008, ty0 + 0.012), (tx0 + 0.008, ty1 - 0.012), (tx1 - 0.008, ty1 - 0.012)):
        K._to(K.sphere('claw_foot', 0.0055, (fx, fy, 0.006), scale=(1, 1.3, 1.2), mat=M['brass']))
    K.block('curtain_rail', tx1 - 0.001, tx1 + 0.002, ty0, ty1, 0.21, 0.213, M['chrome'], bevel=0.001)
    for i in range(14):                                                  # the shower curtain drawn all the way round
        yy = ty0 + 0.006 + i * 0.0108
        c = K.block('shower_curtain', tx1 - 0.0025, tx1 + 0.0015, yy - 0.0058, yy + 0.0058, 0.03, 0.21, M['shower_curtain'], bevel=0.002)
        c.rotation_euler = (0, 0, math.radians(16 * (-1) ** i)); K.add_lumps(c, 0.0008, size=0.012)
    sx, sy = 0.2, 0.80 - IN
    K.block('basin', sx - 0.024, sx + 0.024, sy - 0.038, sy, 0.072, 0.09, M['enamel'], bevel=0.008)
    K._to(K.cylinder('sink_pedestal', 0.009, 0.075, (sx, sy - 0.018, 0.0375), mat=M['enamel']))
    K.block('cabinet', sx - 0.022, sx + 0.022, sy - 0.012, sy, 0.112, 0.165, M['wood'], bevel=0.0015)
    K.block('mirror', sx - 0.019, sx + 0.019, sy - 0.0125, sy - 0.0115, 0.115, 0.162, M['mirror'], bevel=0.0003)
    K._to(K.sphere('bare_bulb', 0.0045, (sx, sy - 0.012, 0.178), scale=(1, 1, 1.3), mat=M['bulb']))
    bl = K.point_light('bath_bulb', (sx, sy - 0.016, 0.176), 0.25, radius=0.004, color=(1.0, 0.84, 0.6)); K._to(bl, 'Lights')
    K.block('toilet_tank', 0.32, 0.35, 0.80 - IN - 0.012, 0.80 - IN, 0.045, 0.078, M['enamel'], bevel=0.003)
    K._to(K.sphere('toilet_bowl', 0.017, (0.335, 0.80 - IN - 0.032, 0.035), scale=(1.0, 1.25, 0.55), mat=M['enamel']))
    K.block('bath_mat', tx1 + 0.004, tx1 + 0.03, ty0 + 0.04, ty0 + 0.11, 0.0, 0.0016, M['bathmat'], bevel=0.0008, coll=True)
    # --- guest bedroom: a plain single bed, wardrobe, chest of drawers, chair, bedside lamp (off)
    PR.bed(0.07, 0.95, 0, duvet='bedsheet', name='guest_bed')
    PR.bedside(0.145, 1.12, 0, energy=0.0)
    PR.wardrobe(0.3, 1.2 - IN - 0.046, 0, name='guest_wardrobe')
    K.block('chest_of_drawers', 0.40 - IN - 0.03, 0.40 - IN, 0.82, 0.9, 0.0, 0.07, M['wood'], bevel=0.002)
    for zz in (0.012, 0.032, 0.052): K.block('drawer_front', 0.40 - IN - 0.0312, 0.40 - IN - 0.03, 0.825, 0.895, zz, zz + 0.016, M['wood'], bevel=0.001)
    K.chair(0.25, 0.86, facing=0)
    # --- landing: runner, banisters round both stairwells, linen cupboard, pictures, a little night-light
    K.runner(0.415, 0.485, 0.02, 0.83)
    K.banister(MS[0] - 0.002, MS[1], MS[3]); K.rail((MS[0], MS[1] - 0.002), (MS[2], MS[1] - 0.002))
    K.banister(BS[2] + 0.002, BS[1], BS[3]); K.rail((BS[0], BS[1] - 0.002), (BS[2], BS[1] - 0.002))
    PR.wardrobe(0.60 - IN - 0.04, 0.73, -90, w=0.09, d=0.035, hgt=0.2, name='linen_cupboard', mat='trim')
    for yy, zz in ((0.5, 0.13), (0.58, 0.15), (0.2, 0.14)): K.picture((0.40 + IN + 0.001, yy, zz), (0.024, 0.03), normal=(1, 0, 0))
    nl = K.point_light('night_light', (0.41, 0.48, 0.02), 0.08, radius=0.003, color=(1.0, 0.75, 0.45)); K._to(nl, 'Lights')
    K._to(K.sphere('night_light_glow', 0.003, (0.405, 0.48, 0.02), mat=M['shade']))
    # --- Mum's bedroom (the whole right side, front and middle): double bed, wardrobe, dressing table, armchair
    PR.bed(0.83, 0.2, 0, w=0.16, l=0.21, duvet='knit_blanket', name='mum_bed')
    PR.bedside(0.73, 0.38, 0, energy=0.0); PR.bedside(0.93, 0.38, 0, energy=0.0)
    PR.wardrobe(0.66, 0.80 - IN - 0.05, 0, w=0.1, d=0.05, hgt=0.2, name='mum_wardrobe')
    K.block('dressing_table', 1.0 - IN - 0.03, 1.0 - IN, 0.55, 0.64, 0.0, 0.06, M['wood'], bevel=0.002)
    K.block('dressing_mirror', 1.0 - IN - 0.004, 1.0 - IN - 0.002, 0.565, 0.625, 0.065, 0.15, M['mirror'], bevel=0.0005)
    K.block('dressing_mirror_frame', 1.0 - IN - 0.003, 1.0 - IN, 0.56, 0.63, 0.06, 0.155, M['wood'], bevel=0.001)
    K._to(K.cylinder('stool', 0.012, 0.035, (0.93, 0.595, 0.0175), mat=M['sofa']))
    PR.armchair(0.68, 0.08, -150)
    r = K.cylinder('rug', 0.07, 0.0012, (0.8, 0.12, 0.0006), mat=M['runner'], verts=64); K._to(r); K.HP.colliders().objects.link(r)
    # --- second bathroom (back right): a shower with a curtain, sink and mirror, toilet
    K.block('shower_tray', 1.0 - IN - 0.07, 1.0 - IN, 1.2 - IN - 0.07, 1.2 - IN, 0.0, 0.006, M['enamel'], bevel=0.002, coll=True)
    K.block('shower_rail', 1.0 - IN - 0.07, 1.0 - IN, 1.2 - IN - 0.072, 1.2 - IN - 0.069, 0.21, 0.213, M['chrome'], bevel=0.001)
    for i in range(7):
        xx = 1.0 - IN - 0.066 + i * 0.0095
        c = K.block('shower_curtain', xx - 0.005, xx + 0.005, 1.2 - IN - 0.073, 1.2 - IN - 0.069, 0.03, 0.21, M['shower_curtain'], bevel=0.002)
        c.rotation_euler = (0, 0, math.radians(14 * (-1) ** i))
    K.block('basin2', 0.7, 0.745, 1.2 - IN - 0.035, 1.2 - IN, 0.072, 0.088, M['enamel'], bevel=0.007)
    K._to(K.cylinder('sink_pedestal2', 0.008, 0.074, (0.7225, 1.2 - IN - 0.018, 0.037), mat=M['enamel']))
    K.block('mirror2', 0.705, 0.74, 1.2 - IN - 0.002, 1.2 - IN - 0.001, 0.11, 0.155, M['mirror'], bevel=0.0003)
    K.block('toilet_tank2', 0.60 + IN, 0.60 + IN + 0.012, 1.0, 1.035, 0.045, 0.078, M['enamel'], bevel=0.003)
    K._to(K.sphere('toilet_bowl2', 0.017, (0.60 + IN + 0.03, 1.0175, 0.035), scale=(1.25, 1.0, 0.55), mat=M['enamel']))


def build(house=False):
    G.extra_materials()
    was = K.HOUSE; K.HOUSE = True
    for name, (x0, y0, x1, y1) in ROOMS.items():
        holes = [(MS[0], MS[1], MS[2], MS[3]), (BS[0], BS[1], BS[2], BS[3])] if name == 'landing' else []
        if name == 'landing':
            K.floor((x0, y0, x1, y1), holes=holes, mat=FLOORS[name])
        else:
            K.floor((x0, y0, x1, y1), mat=FLOORS[name])
        K.ceiling((x0, y0, x1, y1))
    for a, b, inward, ops, kind in WALLS:
        w = K.wall(a, b, inward=inward, openings=ops, mat='wall_bath' if kind == 'wall_bath' else 'wall')
        if kind == 'wild': w['wild'] = True
    K.cladding((0.0, 0.45), (0.0, 0.80), -1, height=0.12)
    K.cladding((1.0, 0.80), (1.0, 1.2), 1, height=0.12)
    furnish()
    K.mood('night', moon_from=(-0.5, 0.22, 0.36), moon_to=(0.15, 0.22, 0.0), moon_energy=18)
    K.mood('night', moon_from=(0.5, 1.9, 0.42), moon_to=(0.5, 0.9, 0.0), moon_energy=16)
    K.mood('night', moon_from=(1.5, 0.22, 0.36), moon_to=(0.85, 0.22, 0.0), moon_energy=14)
    G.room_fills(ROOMS)
    K.HOUSE = was
    if not house:
        K.mood('night', bounds=(0.005, 0.0, 0.0, 0.995, 1.195, K.H), haze_density=0.35)
        # stand-in for the ground floor ceiling below the stairwells, so the holes do not look into the void
        K.block('below', 0.4, 0.6, 0.1, 1.15, -0.27, -0.26, K.M['floor'], bevel=0)
    K.mark('dollhouse_upstairs', (0.5, -1.05, 0.13), (0.5, 0.4, 0.1), lens=24)
    K.mark('haru_bedroom', (0.3, -0.12, 0.1), (0.12, 0.3, 0.05), lens=22)
    K.mark('bathroom', (0.36, 0.5, 0.12), (0.06, 0.62, 0.07), lens=22)
    K.mark('guest_bedroom', (0.36, 0.84, 0.12), (0.12, 1.08, 0.05), lens=22)
    K.mark('landing', (0.45, 0.02, 0.1), (0.46, 0.9, 0.08), lens=20)
    K.mark('mum_bedroom', (0.7, -0.12, 0.11), (0.82, 0.45, 0.05), lens=22)
    K.mark('bathroom2', (0.65, 0.84, 0.12), (0.88, 1.12, 0.07), lens=20)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def opt(name, n=1, default=None):
        if '--' + name not in argv: return default
        i = argv.index('--' + name); v = argv[i + 1:i + 1 + n]; return v if n > 1 else v[0]
    RES = tuple(int(v) for v in opt('res', 2, ('1080', '1920')))
    OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'upstairs')))
    K.begin('home_upstairs', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    if opt('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt('blend')))
    os.makedirs(OUT, exist_ok=True)
    for m in (opt('marks') or 'haru_bedroom,bathroom,guest_bedroom,landing,mum_bedroom,bathroom2,dollhouse_upstairs').split(','):
        K.shoot(m, OUT, fstop=float(opt('fstop', 1, '8')))
    print('DONE upstairs', OUT)
