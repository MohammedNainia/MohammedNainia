"""Haru's home, upstairs (see plan.py): built at its own floor level 0 (the house lifts it by plan.UP).

Rooms: Haru's bedroom (front left), the bathroom, the old nursery kept shut (back left, a small narrow door), Mum's
bedroom (front right), the box room, the sewing room, and the long landing down the middle with both stairwells,
banisters, a linen cupboard and a window at the far end.
Hiding places: under Haru's bed and Mum's double bed, inside both wardrobes, the toy chest, the linen cupboard,
behind the shower curtain, among the boxes and sheets in the box room, behind the dress forms in the sewing room.

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
ROOMS = {'haru_bedroom': PL.rect('A', 'front'), 'bathroom': PL.rect('A', 'middle'), 'nursery': PL.rect('A', 'back'),
         'landing': (0.40, 0.0, 0.60, 1.2), 'mum_bedroom': PL.rect('C', 'front'), 'box_room': PL.rect('C', 'middle'),
         'sewing_room': PL.rect('C', 'back')}
FLOORS = {'haru_bedroom': 'floor', 'bathroom': 'tiles_floor', 'nursery': 'floor', 'landing': 'floor', 'mum_bedroom': 'floor',
          'box_room': 'floor', 'sewing_room': 'floor'}
WALLS = [
    ((0.0, 0.0), (0.0, 1.2), -1, [WIN(0.14, 0.30, 0.085, 0.19, moon=True), WIN(0.58, 0.66, 0.13, 0.19, curtains=False),
                                  WIN(0.95, 1.07, 0.09, 0.19)], 'wall'),                              # west
    ((0.0, 1.2), (1.0, 1.2), -1, [WIN(0.12, 0.24, 0.09, 0.19), WIN(0.45, 0.55, 0.08, 0.2, moon=True), WIN(0.75, 0.88, 0.09, 0.19)], 'wall'),
    ((1.0, 0.0), (1.0, 1.2), 1, [WIN(0.15, 0.30, 0.085, 0.19, moon=True), WIN(0.6, 0.68, 0.11, 0.18), WIN(0.95, 1.07, 0.09, 0.19)], 'wall'),
    ((0.40, 0.0), (0.60, 0.0), 1, [WIN(0.06, 0.14, 0.09, 0.19, curtains=False, sky=False)], 'wild'),            # front of the landing
    ((0.40, 0.0), (0.40, 1.2), 1, [D(0.32, 0.40, angle=20), D(0.55, 0.63, angle=20),
                                   D(1.135, 1.19, h=0.17, angle=0, keep=True)], 'wall'),              # landing | Haru, bath, nursery
    ((0.60, 0.0), (0.60, 1.2), -1, [D(0.30, 0.38, angle=-20), D(0.50, 0.58, angle=-20), D(0.90, 0.98, angle=-20)], 'wall'),
    ((0.0, 0.45), (0.40, 0.45), 1, [], 'wall'), ((0.0, 0.80), (0.40, 0.80), 1, [], 'wall_bath'),
    ((0.60, 0.45), (1.0, 0.45), 1, [], 'wall'), ((0.60, 0.80), (1.0, 0.80), 1, [], 'wall'),
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
    # --- the old nursery (kept shut): a cot, a rocking horse, a music box, everything else under dust sheets
    K.block('cot_base', 0.08, 0.2, 1.08, 1.19 - IN, 0.035, 0.04, M['wood'], bevel=0.001)
    for xx in [0.082 + i * 0.0094 for i in range(13)]:
        for yy in (1.08, 1.19 - IN - 0.002): K.block('cot_bar', xx - 0.001, xx + 0.001, yy - 0.001, yy + 0.001, 0.0, 0.09, M['wood'], bevel=0.0004)
    K.block('cot_rail', 0.08, 0.2, 1.078, 1.082, 0.088, 0.093, M['wood'], bevel=0.001)
    rh = PR.holder('rocking_horse', 0.25, 0.95, 30)
    PR.part(rh, 'horse_body', -0.006, 0.006, -0.02, 0.02, 0.04, 0.055, 'cabinet', bevel=0.005)
    PR.part(rh, 'horse_head', -0.005, 0.005, -0.03, -0.018, 0.05, 0.075, 'cabinet', bevel=0.004)
    for ly in (-0.014, 0.014): PR.part(rh, 'horse_leg', -0.004, 0.004, ly - 0.002, ly + 0.002, 0.008, 0.042, 'wood', bevel=0.001)
    PR.part(rh, 'horse_rocker', -0.006, 0.006, -0.03, 0.03, 0.002, 0.008, 'wood', bevel=0.002)
    for (a, b, c, d, hh) in ((0.02, 0.1, 0.84, 0.93, 0.06), (0.28, 0.37, 1.08, 1.17, 0.12)):
        sh = K.draped('dust_sheet', a, b, c, d, hh, lump=0.005)
    K._to(K.cylinder('music_box', 0.008, 0.01, (0.34, 0.86, 0.005), mat=M['wood']))
    # --- landing: runner, banisters round both stairwells, linen cupboard, pictures, a little night-light
    K.runner(0.415, 0.485, 0.02, 0.83)
    K.banister(MS[0] - 0.002, MS[1], MS[3]); K.rail((MS[0], MS[1] - 0.002), (MS[2], MS[1] - 0.002))
    K.banister(BS[2] + 0.002, BS[1], BS[3]); K.rail((BS[0], BS[1] - 0.002), (BS[2], BS[1] - 0.002))
    PR.wardrobe(0.60 - IN - 0.04, 0.73, -90, w=0.09, d=0.035, hgt=0.2, name='linen_cupboard', mat='trim')
    for yy, zz in ((0.5, 0.13), (0.58, 0.15), (0.2, 0.14)): K.picture((0.40 + IN + 0.001, yy, zz), (0.024, 0.03), normal=(1, 0, 0))
    nl = K.point_light('night_light', (0.41, 0.48, 0.02), 0.08, radius=0.003, color=(1.0, 0.75, 0.45)); K._to(nl, 'Lights')
    K._to(K.sphere('night_light_glow', 0.003, (0.405, 0.48, 0.02), mat=M['shade']))
    # --- Mum's bedroom: double bed (room under it), big wardrobe, dressing table with a mirror, bedside lamp
    PR.bed(0.83, 0.12, 0, w=0.16, l=0.21, duvet='knit_blanket', name='mum_bed')
    PR.bedside(0.73, 0.29, 0, energy=0.0)
    PR.wardrobe(0.68, 0.45 - IN - 0.05, 0, w=0.1, d=0.05, hgt=0.2, name='mum_wardrobe')
    K.block('dressing_table', 0.97 - 0.03, 1.0 - IN, 0.33, 0.42, 0.0, 0.06, M['wood'], bevel=0.002)
    K.block('dressing_mirror', 1.0 - IN - 0.004, 1.0 - IN - 0.002, 0.345, 0.405, 0.065, 0.15, M['mirror'], bevel=0.0005)
    K.block('dressing_mirror_frame', 1.0 - IN - 0.003, 1.0 - IN, 0.34, 0.41, 0.06, 0.155, M['wood'], bevel=0.001)
    K._to(K.cylinder('stool', 0.012, 0.035, (0.93, 0.375, 0.0175), mat=M['sofa']))
    # --- box room: stacks of boxes, sheets over old furniture, a standing mirror, a dressmaker's dummy
    PR.boxes(0.62, 0.72, 0.47, 0.78, seed=11); PR.boxes(0.85, 0.98, 0.47, 0.78, seed=12)
    K.draped('dust_sheet', 0.74, 0.83, 0.62, 0.74, 0.08, lump=0.005)
    K.draped('dust_sheet', 0.76, 0.8, 0.48, 0.52, 0.17, lump=0.003)        # tall: a mirror... or someone
    # --- sewing room: a sewing table and machine, dress forms standing about, rolls of fabric
    K.block('sewing_table', 0.85, 0.97, 1.2 - IN - 0.05, 1.2 - IN, 0.055, 0.06, M['wood'], bevel=0.0015, coll=True)
    for xx in (0.855, 0.965): K.block('sewing_table_leg', xx - 0.003, xx + 0.003, 1.2 - IN - 0.045, 1.2 - IN - 0.005, 0, 0.055, M['iron'], bevel=0.001)
    K.block('sewing_machine', 0.89, 0.93, 1.2 - IN - 0.035, 1.2 - IN - 0.015, 0.06, 0.085, M['iron'], bevel=0.003)
    for (dx_, dy_) in ((0.7, 0.92), (0.76, 1.05), (0.68, 1.12)):        # dress forms, like people standing in the dark
        K._to(K.cylinder('dummy_pole', 0.0018, 0.07, (dx_, dy_, 0.035), mat=M['wood']))
        K._to(K.sphere('dummy_torso', 0.02, (dx_, dy_, 0.095), scale=(1.0, 0.7, 1.6), mat=M['dummy']))
        K._to(K.cylinder('dummy_base', 0.012, 0.003, (dx_, dy_, 0.0015), mat=M['wood']))
    for i in range(4): K._to(K.cylinder('fabric_roll', 0.006, 0.09, (0.98, 0.85 + i * 0.016, 0.045), mat=M[['curtain', 'red', 'duvet', 'knit_blanket'][i]]))
    K.chair(0.91, 1.1, facing=0)


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
    K.mark('nursery', (0.36, 0.84, 0.12), (0.15, 1.12, 0.05), lens=22)
    K.mark('landing', (0.45, 0.02, 0.1), (0.46, 0.9, 0.08), lens=20)
    K.mark('mum_bedroom', (0.7, -0.12, 0.1), (0.85, 0.3, 0.05), lens=22)
    K.mark('box_room', (0.65, 0.5, 0.12), (0.85, 0.7, 0.06), lens=20)
    K.mark('sewing_room', (0.65, 0.84, 0.12), (0.85, 1.1, 0.07), lens=20)


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
    for m in (opt('marks') or 'haru_bedroom,bathroom,nursery,landing,mum_bedroom,box_room,sewing_room,dollhouse_upstairs').split(','):
        K.shoot(m, OUT, fstop=float(opt('fstop', 1, '8')))
    print('DONE upstairs', OUT)
