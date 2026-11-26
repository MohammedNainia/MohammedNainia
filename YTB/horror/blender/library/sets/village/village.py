"""Haru's village (see village_plan.py): one quiet street at night. Ordinary houses on both sides (solid shells with windows,
doors, porches, chimneys; some windows lit), Haru's house in the middle of the north side (the big home's exact
footprint and roof, so ../home can be dropped in at village_plan.HOME_AT), raised sidewalks with curbs, the road, front
gardens with fences, hedges and paths, street lamps, a few trees, moonlight and a thin haze.

    import village; village.build()            after kit.begin(); returns the objects
    blender -b -P library/sets/village/village.py -- [--out DIR] [--res W H] [--samples N] [--marks a,b]
"""
import bpy, bmesh, os, sys, math, random
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', 'home'))
import kit as K
import props as PR
import ground as G
import village_plan as VP

RNG = random.Random(7)
U = VP.UP


# ------------------------------------------------------------------ materials
def materials():
    G.extra_materials(); M = K.M
    sc = lambda name, scan, size, col, **kw: K.scanned(name, scan, size, col, fallback=K.painted(name + '_plain', col), **kw)
    M['asphalt'] = sc('asphalt', 'concrete_floor', 0.5, (0.025, 0.025, 0.027), rough=0.75, bump=0.4, grime=0.5)
    M['pavement'] = sc('pavement', 'concrete_floor', 0.3, (0.16, 0.16, 0.15), bump=0.3, grime=0.5)
    M['curb'] = sc('curb', 'concrete_floor', 0.2, (0.22, 0.22, 0.2), bump=0.2, grime=0.4)
    M['lawn'] = M.get('garden') or K.painted('lawn', (0.03, 0.045, 0.025), rough=0.95)
    M['dirt'] = sc('dirt', 'dirt_rocks', 0.3, (0.06, 0.045, 0.03), rough=0.95, bump=0.5)
    M['brick_wall'] = sc('brick_wall', 'brick_reclaimed', 0.3, (0.17, 0.09, 0.07), bump=0.5, grime=0.35)
    for name, col in (('plaster_cream', (0.42, 0.38, 0.3)), ('plaster_blue', (0.24, 0.28, 0.31)), ('plaster_old', (0.36, 0.33, 0.27)), ('plaster_pale', (0.5, 0.5, 0.47)),
                      ('siding_grey', (0.3, 0.31, 0.3)), ('siding_cream', (0.45, 0.42, 0.34))):
        M[name] = sc(name, 'adobe_plaster', 0.28, col, rough=0.9, bump=0.35, grime=0.45)
    for name, col in (('door_green', (0.06, 0.14, 0.08)), ('door_red', (0.3, 0.05, 0.04)), ('door_blue', (0.05, 0.09, 0.18)),
                      ('door_black', (0.02, 0.02, 0.02)), ('door_white', (0.6, 0.6, 0.56))):
        M[name] = K.scan_overlay(K.painted(name, col, rough=0.4), 'plaster_white', 0.12, amount=0.5, bump=0.1, grime=0.3)
    M['glass_dark'] = K.painted('glass_dark', (0.012, 0.016, 0.02), rough=0.06)
    M['glass_lit'] = K.emissive('glass_lit', (1.0, 0.7, 0.4), 0.7)
    M['curtain_lit'] = K.emissive('curtain_lit', (0.85, 0.45, 0.2), 0.35)
    M['lamp_glow'] = K.emissive('lamp_glow', (1.0, 0.78, 0.5), 14.0)
    M['leaves'] = K.painted('leaves', (0.025, 0.045, 0.022), rough=0.9)
    M['hedge'] = K.painted('hedge', (0.02, 0.04, 0.02), rough=0.95)
    M['bark'] = K.painted('bark', (0.04, 0.03, 0.022), rough=0.9)
    M['picket'] = K.scan_overlay(K.painted('picket', (0.5, 0.49, 0.45), rough=0.6), 'plaster_white', 0.1, amount=0.6, grime=0.5)
    return M


# ------------------------------------------------------------------ mesh helpers
def mesh_obj(name, verts, faces, mat, parent=None, coll=False):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(mat); K._to(ob)
    if parent: K.attach(ob, parent)
    if coll: K.HP.colliders().objects.link(ob)
    return ob


def prism(name, tri, a0, a1, axis, mat, parent=None):
    """a triangular solid: triangle `tri` [(u, z) x3] extruded along `axis` ('x' or 'y') from a0 to a1"""
    def P(u, z, a): return (a, u, z) if axis == 'x' else (u, a, z)
    v = [P(u, z, a0) for u, z in tri] + [P(u, z, a1) for u, z in tri]
    f = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    return mesh_obj(name, v, f, mat, parent)


def slab(name, e0, e1, r0, r1, thick, mat, parent=None):
    """a thick quad: eave edge e0-e1, ridge edge r0-r1 (local points), thickness along its outward normal"""
    e0, e1, r0, r1 = map(Vector, (e0, e1, r0, r1))
    n = (e1 - e0).cross(r0 - e0).normalized()
    if n.z < 0: n = -n
    v = [e0, e1, r1, r0] + [p + n * thick for p in (e0, e1, r1, r0)]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return mesh_obj(name, v, f, mat, parent)


# ------------------------------------------------------------------ facade pieces (built on a face holder: u along the face, outward -y)
def face_holder(h, name, origin, yaw):
    e = K.empty(name, (0, 0, 0)); K._to(e); K.attach(e, h); e.location = origin; e.rotation_euler = (0, 0, math.radians(yaw)); return e


def window(fh, u0, u1, z0, z1, lit):
    M = K.M; t = 0.006
    for (a, b, c, d) in ((u0 - t, u0, z0 - t, z1 + t), (u1, u1 + t, z0 - t, z1 + t), (u0, u1, z1, z1 + t), (u0, u1, z0 - t, z0)):
        PR.part(fh, 'win_frame', a, b, -0.006, 0.0, c, d, 'trim', bevel=0.0008)
    PR.part(fh, 'win_glass', u0, u1, -0.003, -0.001, z0, z1, 'glass_lit' if lit else 'glass_dark', bevel=0.0002)
    um, zm = (u0 + u1) / 2, (z0 + z1) / 2
    PR.part(fh, 'win_bar', um - 0.0015, um + 0.0015, -0.005, -0.002, z0, z1, 'trim', bevel=0.0004)
    PR.part(fh, 'win_bar', u0, u1, -0.005, -0.002, zm - 0.0015, zm + 0.0015, 'trim', bevel=0.0004)
    PR.part(fh, 'win_sill', u0 - 0.01, u1 + 0.01, -0.016, 0.0, z0 - 0.01, z0 - 0.005, 'trim', bevel=0.001)
    if lit:                                                            # half-drawn curtains glowing in the window
        w = (u1 - u0) * 0.28
        for a, b in ((u0, u0 + w), (u1 - w, u1)): PR.part(fh, 'win_curtain', a, b, -0.0012, -0.0008, z0, z1, 'curtain_lit', bevel=0.0002)


def front_door(fh, u, mat, porch_on, h=0.2, w=0.08):
    u0, u1 = u - w / 2, u + w / 2; t = 0.008
    for (a, b, c, d) in ((u0 - t, u0, 0, h + t), (u1, u1 + t, 0, h + t), (u0, u1, h, h + t)):
        PR.part(fh, 'door_frame', a, b, -0.008, 0.0, c, d, 'trim', bevel=0.001)
    PR.part(fh, 'front_door', u0, u1, -0.004, 0.0, 0.0, h, mat, bevel=0.001)
    for zz in (0.03, 0.115): PR.part(fh, 'door_panel', u0 + 0.01, u1 - 0.01, -0.0055, -0.004, zz, zz + 0.07, mat, bevel=0.0012)
    kn = K.sphere('door_knob', 0.0028, (0, 0, 0), mat=K.M['brass']); K._to(kn); K.attach(kn, fh); kn.location = (u1 - 0.012, -0.007, 0.095)
    PR.part(fh, 'door_step', u0 - 0.02, u1 + 0.02, -0.04, 0.0, 0.0, 0.014, 'curb', bevel=0.001, coll=True)
    PR.part(fh, 'porch_roof', u0 - 0.03, u1 + 0.03, -0.05, 0.0, h + 0.02, h + 0.028, 'trim', bevel=0.0015)
    lamp = K.sphere('porch_lamp', 0.006, (0, 0, 0), scale=(1, 1, 1.3), mat=K.M['lamp_glow' if porch_on else 'bulb_off']); K._to(lamp)
    K.attach(lamp, fh); lamp.location = (u1 + 0.025, -0.01, h - 0.02)
    if porch_on:
        lt = K.point_light('porch_light', (0, 0, 0), 0.35, radius=0.006, color=(1.0, 0.72, 0.42)); K._to(lt, 'Lights')
        K.attach(lt, fh); lt.location = (u1 + 0.025, -0.03, h - 0.03)


# ------------------------------------------------------------------ one house
def house(name, x0, x1, side, depth, storeys, roof, facade, door_mat, lit, porch_on, y_front=None):
    M = K.M; w = x1 - x0; cx = (x0 + x1) / 2
    y_front = y_front if y_front is not None else (VP.FRONT_N if side == 'N' else VP.FRONT_S)
    h = PR.holder(name, cx, y_front, 0 if side == 'N' else 180)        # local: front at y 0 facing -y, house toward +y
    E = storeys * U
    PR.part(h, name + '_body', -w / 2, w / 2, 0.0, depth, 0.0, E, facade, bevel=0.002)
    PR.part(h, name + '_plinth', -w / 2 - 0.004, w / 2 + 0.004, -0.004, depth + 0.004, 0.0, 0.02, 'curb', bevel=0.001)
    ov = 0.035
    if roof == 'side':                                                 # ridge along the street, gables at the sides
        R = E + depth * 0.45
        prism(name + '_gable', [(0, E), (depth, E), (depth / 2, R)], -w / 2, w / 2, 'x', M[facade], h)
        for ya, yb in ((-ov, depth / 2), (depth + ov, depth / 2)):
            ze = E - ov * 0.9
            slab(name + '_roof', (-w / 2 - ov, ya, ze), (w / 2 + ov, ya, ze), (-w / 2 - ov, yb, R), (w / 2 + ov, yb, R), 0.012, M['shingle'], h)
        ch = (w / 2 - 0.1, depth * 0.7)
    else:                                                              # gable facing the street, ridge front to back
        R = E + w * 0.45
        prism(name + '_gable', [(-w / 2, E), (w / 2, E), (0, R)], 0.0, depth, 'y', M[facade], h)
        for xa in (-w / 2 - ov, w / 2 + ov):
            ze = E - ov * 0.9
            slab(name + '_roof', (xa, -ov, ze), (xa, depth + ov, ze), (0, -ov, R), (0, depth + ov, R), 0.012, M['shingle'], h)
        ch = (-w / 4, depth * 0.75)
        fh = face_holder(h, name + '_gable_face', (0, 0, 0), 0)
        window(fh, -0.035, 0.035, E + 0.04, E + 0.11, False)            # a small attic window in the front gable
    PR.part(h, name + '_chimney', ch[0] - 0.03, ch[0] + 0.03, ch[1] - 0.03, ch[1] + 0.03, E, R + 0.08, 'brick_wall', bevel=0.002)
    # the front: a door and windows on each storey; side walls get one or two dark windows
    fh = face_holder(h, name + '_front', (0, 0, 0), 0)
    names = [r[0] for r in VP.HOUSES]
    du = VP.door_x(names.index(name))[1] if name in names else 0.0
    front_door(fh, du, door_mat, porch_on)
    li = list(lit) + [0] * 8; k = 0
    for s in range(storeys):
        z0 = s * U + 0.085
        cols = [u for u in (-w * 0.3, 0.0, w * 0.3) if abs(u - du) > 0.09] if s == 0 else [-w * 0.3, w * 0.3]
        for u in cols:
            window(fh, u - 0.04, u + 0.04, z0, z0 + 0.1, bool(li[k])); k += 1
    for sx in (-1, 1):
        sh = face_holder(h, name + '_side', (sx * w / 2, depth / 2, 0), -90 * sx)
        window(sh, -0.04, 0.04, 0.085 + (storeys - 1) * U, 0.185 + (storeys - 1) * U, False)
    return h


# ------------------------------------------------------------------ Haru's house: the big home's outside
def haru_house():
    """the shell of ../home at village_plan.HOME_AT: 1.0 x 1.2, two storeys and the attic, gable to the street, ridge at x 0.5"""
    M = K.M; ox, oy = VP.HOME_AT
    h = PR.holder('haru_house', ox + 0.5, oy, 0)
    W, D, E = 1.0, 1.2, 2 * U + 0.035; R = 2 * U + 0.33
    PR.part(h, 'haru_house_body', -W / 2, W / 2, 0, D, 0, E, 'plaster_old', bevel=0.002)
    PR.part(h, 'haru_house_plinth', -W / 2 - 0.004, W / 2 + 0.004, -0.004, D + 0.004, 0, 0.02, 'curb', bevel=0.001)
    prism('haru_house_gable', [(-W / 2, E), (W / 2, E), (0, R)], 0, D, 'y', M['plaster_old'], h)
    ov = 0.04
    for xa in (-W / 2 - ov, W / 2 + ov):
        slab('haru_house_roof', (xa, -ov, E - ov * 0.9), (xa, D + ov, E - ov * 0.9), (0, -ov, R), (0, D + ov, R), 0.014, M['shingle'], h)
    PR.part(h, 'haru_house_chimney', 0.25, 0.32, 0.75, 0.82, E, R + 0.06, 'brick_wall', bevel=0.002)
    fh = face_holder(h, 'haru_house_front', (0, 0, 0), 0)
    front_door(fh, 0.0, M['door_green'], True)
    for u, lit0, lit1 in ((-0.3, False, True), (0.3, False, False)):    # living / study below; her room / Mum's above
        window(fh, u - 0.08, u + 0.08, 0.085, 0.19, lit0)
        window(fh, u - 0.08, u + 0.08, U + 0.085, U + 0.19, lit1)
    window(fh, -0.04, 0.04, U + 0.09, U + 0.19, False)                  # the landing window
    rw = K.cylinder('haru_attic_window', 0.04, 0.008, (0, 0, 0), rot=(math.pi / 2, 0, 0), mat=M['glass_dark'], verts=32)
    K._to(rw); K.attach(rw, fh); rw.location = (0, -0.002, 2 * U + 0.16)
    rf = K.cylinder('haru_attic_frame', 0.046, 0.006, (0, 0, 0), rot=(math.pi / 2, 0, 0), mat=M['trim'], verts=32)
    K._to(rf); K.attach(rf, fh); rf.location = (0, -0.0005, 2 * U + 0.16)
    for sx in (-1, 1):
        sh = face_holder(h, 'haru_house_side', (sx * W / 2, D / 2, 0), -90 * sx)
        for u in (-0.3, 0.3): window(sh, u - 0.06, u + 0.06, 0.085, 0.19, False); window(sh, u - 0.06, u + 0.06, U + 0.085, U + 0.19, False)
    return h


# ------------------------------------------------------------------ the hospital and the police station
def sign_text(parent, text, u, z, size, mat, depth=0.002):
    """raised letters on a face holder (outward -y), centred at u"""
    cu = bpy.data.curves.new('sign_' + text, 'FONT'); cu.body = text; cu.size = size; cu.extrude = depth
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    ob = bpy.data.objects.new('sign_' + text.lower(), cu); ob.data.materials.append(mat); K._to(ob); K.attach(ob, parent)
    ob.location = (u, -0.004 - depth, z); ob.rotation_euler = (math.pi / 2, 0, 0)
    return ob


def civic(name, x0, x1, side, depth, storeys, facade, door_off):
    """a flat-roofed public building: rows of windows, a glazed lit entrance under a canopy, its sign"""
    M = K.M; w = x1 - x0; cx = (x0 + x1) / 2
    h = PR.holder(name, cx, VP.door_y(side), 0 if side == 'N' else 180)
    E = storeys * U
    PR.part(h, name + '_body', -w / 2, w / 2, 0.0, depth, 0.0, E, facade, bevel=0.002)
    PR.part(h, name + '_plinth', -w / 2 - 0.005, w / 2 + 0.005, -0.005, depth + 0.005, 0.0, 0.025, 'curb', bevel=0.001)
    PR.part(h, name + '_parapet', -w / 2 - 0.006, w / 2 + 0.006, -0.006, depth + 0.006, E, E + 0.03, 'curb', bevel=0.002)
    PR.part(h, name + '_roof_plant', -0.1, 0.1, depth * 0.5, depth * 0.7, E, E + 0.07, 'metal_shelf', bevel=0.004)
    fh = face_holder(h, name + '_front', (0, 0, 0), 0)
    r = random.Random(hash(name) % 1000); du = door_off
    # the entrance: two glass doors with light behind, a flat canopy, steps
    ew = 0.16
    for (a, b, c, d) in ((du - ew / 2 - 0.008, du - ew / 2, 0, 0.21), (du + ew / 2, du + ew / 2 + 0.008, 0, 0.21), (du - ew / 2, du + ew / 2, 0.2, 0.21)):
        PR.part(fh, 'entrance_frame', a, b, -0.008, 0.0, c, d, 'metal_shelf', bevel=0.001)
    PR.part(fh, 'entrance_glass', du - ew / 2, du + ew / 2, -0.004, -0.002, 0.0, 0.2, 'glass_lit', bevel=0.0002)
    PR.part(fh, 'entrance_mullion', du - 0.002, du + 0.002, -0.006, -0.002, 0.0, 0.2, 'metal_shelf', bevel=0.0005)
    PR.part(fh, 'entrance_canopy', du - ew / 2 - 0.06, du + ew / 2 + 0.06, -0.12, 0.0, 0.235, 0.245, 'curb', bevel=0.002)
    for sx in (-1, 1):
        PR.part(fh, 'canopy_post', du + sx * (ew / 2 + 0.05) - 0.004, du + sx * (ew / 2 + 0.05) + 0.004, -0.115, -0.107, 0.0, 0.235, 'metal_shelf', bevel=0.001)
    PR.part(fh, 'entrance_step', du - ew / 2 - 0.04, du + ew / 2 + 0.04, -0.1, 0.0, 0.0, 0.012, 'curb', bevel=0.001, coll=True)
    lt = K.point_light(name + '_entrance_light', (0, 0, 0), 0.6, radius=0.02, color=(1.0, 0.9, 0.75)); K._to(lt, 'Lights')
    K.attach(lt, fh); lt.location = (du, -0.07, 0.22)
    # windows: a grid on every storey, the entrance bay left clear on the ground floor
    cols = [u for u in [-w / 2 + 0.1 + i * 0.16 for i in range(int((w - 0.2) / 0.16) + 1)] if u < w / 2 - 0.08]
    for s in range(storeys):
        z0 = s * U + 0.085
        for u in cols:
            if s == 0 and abs(u - du) < ew / 2 + 0.1: continue
            window(fh, u - 0.045, u + 0.045, z0, z0 + 0.11, r.random() < (0.45 if name == 'hospital' else 0.25))
    for sx in (-1, 1):
        sh = face_holder(h, name + '_side', (sx * w / 2, depth / 2, 0), -90 * sx)
        for s in range(storeys):
            for u in (-depth * 0.25, depth * 0.25): window(sh, u - 0.045, u + 0.045, s * U + 0.085, s * U + 0.195, r.random() < 0.3)
    if name == 'hospital':
        red = K.emissive('cross_red', (1.0, 0.06, 0.05), 6.0); white = K.emissive('sign_white', (1.0, 0.97, 0.92), 3.0)
        sign_text(fh, 'HOSPITAL', du, 0.275, 0.05, white)
        cz = E - 0.06                                                  # a glowing red cross high on the front
        PR.part(fh, 'red_cross', du - 0.012, du + 0.012, -0.006, 0.0, cz - 0.04, cz + 0.04, red, bevel=0.0005)
        PR.part(fh, 'red_cross', du - 0.04, du + 0.04, -0.006, 0.0, cz - 0.012, cz + 0.012, red, bevel=0.0005)
        cl = K.point_light('cross_glow', (0, 0, 0), 0.4, radius=0.03, color=(1.0, 0.1, 0.08)); K._to(cl, 'Lights')
        K.attach(cl, fh); cl.location = (du, -0.05, cz)
    else:
        blue = K.emissive('police_blue', (0.15, 0.35, 1.0), 5.0); board = K.painted('police_board', (0.02, 0.05, 0.2), rough=0.4)
        white = K.emissive('police_white', (0.95, 0.97, 1.0), 2.5)
        PR.part(fh, 'police_sign', du - 0.1, du + 0.1, -0.006, 0.0, 0.25, 0.3, board, bevel=0.001)
        sign_text(fh, 'POLICE', du, 0.275, 0.04, white)
        PR.part(fh, 'blue_lamp_arm', du + ew / 2 + 0.03, du + ew / 2 + 0.036, -0.04, 0.0, 0.2, 0.206, 'iron', bevel=0.0005)
        bl = K.cylinder('blue_lamp', 0.011, 0.022, (0, 0, 0), mat=blue, verts=16); K._to(bl); K.attach(bl, fh)
        bl.location = (du + ew / 2 + 0.033, -0.045, 0.22)
        bg = K.point_light('blue_lamp_glow', (0, 0, 0), 0.5, radius=0.012, color=(0.2, 0.4, 1.0)); K._to(bg, 'Lights')
        K.attach(bg, fh); bg.location = (du + ew / 2 + 0.033, -0.06, 0.22)
    return h


def forecourt(x0, x1, side, door_x):
    """paving from the sidewalk to the building, low hedges either side of the entrance"""
    M = K.M
    if side == 'N': g0, g1 = VP.SIDEWALK_N[1], VP.FRONT_N
    else: g0, g1 = VP.FRONT_S, VP.SIDEWALK_S[0]
    K.block('forecourt', x0, x1, g0, g1, -0.006, 0.002, M['pavement'], bevel=0, coll=True)
    hy = (g0 + 0.02) if side == 'N' else (g1 - 0.02)
    for a, b in ((x0 + 0.03, door_x - 0.16), (door_x + 0.16, x1 - 0.03)):
        hb = K.block('hedge', a, b, hy - 0.012, hy + 0.012, 0.0, 0.05, M['hedge'], bevel=0.008); K.add_lumps(hb, 0.004, size=0.02)


# ------------------------------------------------------------------ street, gardens, lamps, trees
def tree(x, y, s=1.0, seed=0):
    r = random.Random(seed); M = K.M
    K._to(K.cylinder('tree_trunk', 0.012 * s, 0.4 * s, (x, y, 0.2 * s), mat=M['bark']))
    for i in range(6):
        a = r.uniform(0, 2 * math.pi); d = r.uniform(0.03, 0.09) * s
        c = K.sphere('tree_crown', r.uniform(0.09, 0.14) * s, (x + math.cos(a) * d, y + math.sin(a) * d, r.uniform(0.42, 0.62) * s),
                     scale=(1, 1, 0.85), mat=M['leaves']); K._to(c); K.add_lumps(c, 0.012 * s, size=0.05)


def street_lamp(x, side):
    M = K.M; y = VP.SIDEWALK_N[0] + 0.03 if side == 'N' else VP.SIDEWALK_S[1] - 0.03; d = -1 if side == 'N' else 1
    K._to(K.cylinder('lamp_post', 0.0045, 0.42, (x, y, 0.21), mat=M['iron']))
    K.block('lamp_arm', x - 0.003, x + 0.003, min(y, y + d * 0.07), max(y, y + d * 0.07), 0.415, 0.421, M['iron'], bevel=0.001)
    K.block('lamp_head', x - 0.014, x + 0.014, y + d * 0.07 - 0.02, y + d * 0.07 + 0.02, 0.405, 0.418, M['iron'], bevel=0.003)
    K.block('lamp_lens', x - 0.011, x + 0.011, y + d * 0.07 - 0.016, y + d * 0.07 + 0.016, 0.402, 0.405, M['lamp_glow'], bevel=0.001)
    lt = K.point_light('street_light', (x, y + d * 0.07, 0.395), 3.5, radius=0.012, color=(1.0, 0.76, 0.5)); K._to(lt, 'Lights')
    return lt


def garden(x0, x1, side, path_u, hedge=False):
    """the front garden between the sidewalk and the house: lawn, a path to the door, a picket fence or a hedge"""
    M = K.M
    if side == 'N': g0, g1, fence_y = VP.SIDEWALK_N[1], VP.FRONT_N, VP.SIDEWALK_N[1] + 0.012
    else: g0, g1, fence_y = VP.FRONT_S, VP.SIDEWALK_S[0], VP.SIDEWALK_S[0] - 0.012
    K.block('path', path_u - 0.03, path_u + 0.03, g0, g1, 0.0, 0.003, M['pavement'], bevel=0.0008, coll=True)
    if hedge:
        for a, b in ((x0 + 0.01, path_u - 0.05), (path_u + 0.05, x1 - 0.01)):
            hb = K.block('hedge', a, b, fence_y - 0.012, fence_y + 0.012, 0.0, 0.07, M['hedge'], bevel=0.008); K.add_lumps(hb, 0.004, size=0.02)
        return
    for a, b in ((x0 + 0.01, path_u - 0.045), (path_u + 0.045, x1 - 0.01)):
        for zz in (0.02, 0.05): K.block('fence_rail', a, b, fence_y - 0.002, fence_y + 0.002, zz, zz + 0.005, M['picket'], bevel=0.0006)
        u = a
        while u < b - 0.004:
            K.block('picket', u, u + 0.007, fence_y - 0.0015, fence_y + 0.0015, 0.0, 0.065, M['picket'], bevel=0.0008, tilt=0.02); u += 0.014


def street():
    M = K.M; x0, y0, x1, y1 = VP.ROAD; X0, X1 = -6.0, 6.0
    K.block('road', X0, X1, y0, y1, VP.ROAD_Z - 0.02, VP.ROAD_Z, M['asphalt'], bevel=0, coll=True)
    for (a, b) in (VP.SIDEWALK_N, VP.SIDEWALK_S):
        K.block('sidewalk', X0, X1, a, b, VP.ROAD_Z - 0.02, 0.0, M['pavement'], bevel=0, coll=True)
    for yc in (y0, y1):                                                # the curbs
        K.block('curb', X0, X1, yc - 0.006, yc + 0.006, VP.ROAD_Z - 0.005, 0.002, M['curb'], bevel=0.001, coll=True)
    x = X0                                                             # sidewalk joints
    while x < X1:
        for (a, b) in (VP.SIDEWALK_N, VP.SIDEWALK_S): K.block('pave_joint', x, x + 0.002, a, b, -0.0005, 0.0003, M['iron'], bevel=0)
        x += 0.12
    K.block('lawn_n', X0, X1, VP.SIDEWALK_N[1], 6.0, -0.02, 0.0, M['lawn'], bevel=0, coll=True)
    K.block('lawn_s', X0, X1, -6.0, VP.SIDEWALK_S[0], -0.02, 0.0, M['lawn'], bevel=0, coll=True)
    K.block('centre_line', X0, X1, 0.297, 0.303, VP.ROAD_Z, VP.ROAD_Z + 0.0004, K.painted('road_paint', (0.32, 0.3, 0.22), rough=0.8), bevel=0)


# ------------------------------------------------------------------ street life
def car(x, y, yaw, colour, z=VP.ROAD_Z):
    """an ordinary small parked car: body, cabin with dark glass, four wheels, lights off"""
    M = K.M; h = PR.holder('parked_car', x, y, yaw, z=z)                  # wheels on the road, not the sidewalk level
    PR.part(h, 'car_body', -0.21, 0.21, -0.085, 0.085, 0.022, 0.07, colour, bevel=0.018)
    PR.part(h, 'car_cabin', -0.11, 0.08, -0.075, 0.075, 0.066, 0.122, colour, bevel=0.016)
    for sy in (-1, 1): PR.part(h, 'car_window', -0.1, 0.07, sy * 0.0755 - 0.0012, sy * 0.0755 + 0.0012, 0.078, 0.114, 'glass_dark', bevel=0.004)
    PR.part(h, 'car_windscreen', 0.074, 0.083, -0.068, 0.068, 0.074, 0.116, 'glass_dark', bevel=0.004)
    PR.part(h, 'car_rear_window', -0.115, -0.106, -0.068, 0.068, 0.076, 0.114, 'glass_dark', bevel=0.004)
    for wx in (-0.13, 0.13):
        for sy in (-1, 1):
            wh = K.cylinder('car_wheel', 0.03, 0.022, (0, 0, 0), rot=(math.pi / 2, 0, 0), mat=M['iron'], verts=24); K._to(wh); K.attach(wh, h)
            wh.location = (wx, sy * 0.078, 0.03); wh.rotation_euler = (math.pi / 2, 0, 0)
    for sy in (-1, 1):
        PR.part(h, 'car_headlight', 0.205, 0.212, sy * 0.06 - 0.012, sy * 0.06 + 0.012, 0.048, 0.06, 'bulb_off', bevel=0.003)
        PR.part(h, 'car_taillight', -0.212, -0.205, sy * 0.065 - 0.01, sy * 0.065 + 0.01, 0.05, 0.06, 'red', bevel=0.002)
    return h


def wheelie_bin(x, y, mat):
    K.block('bin', x - 0.022, x + 0.022, y - 0.024, y + 0.024, 0.0, 0.07, K.M[mat], bevel=0.003)
    K.block('bin_lid', x - 0.024, x + 0.024, y - 0.026, y + 0.026, 0.07, 0.076, K.M[mat], bevel=0.002)


def mailbox(x, y):
    K._to(K.cylinder('mailbox_post', 0.003, 0.07, (x, y, 0.035), mat=K.M['wood']))
    K.block('mailbox', x - 0.012, x + 0.012, y - 0.02, y + 0.02, 0.07, 0.092, K.M['iron'], bevel=0.004)


def bushes(x0, x1, y, door_x, seed):
    r = random.Random(seed); x = x0 + 0.04
    while x < x1 - 0.04:
        if abs(x - door_x) > 0.08:
            b = K.sphere('bush', r.uniform(0.022, 0.034), (x, y, 0.018), scale=(1.2, 1, 0.9), mat=K.M['hedge']); K._to(b)
            K.add_lumps(b, 0.004, size=0.015)
            if r.random() < 0.4:                                       # a few pale flowers
                for _ in range(4):
                    f = K.sphere('flower', 0.0035, (x + r.uniform(-0.02, 0.02), y + r.uniform(-0.015, 0.015), 0.038 + r.uniform(0, 0.008)),
                                 mat=K.M[r.choice(('flower_pink', 'flower_white'))]); K._to(f)
        x += r.uniform(0.06, 0.1)


def wire(name, a, b, sag=0.03, n=12):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0007; cu.bevel_resolution = 1
    sp = cu.splines.new('POLY'); sp.points.add(n)
    for i in range(n + 1):
        u = i / n; p = Vector(a).lerp(Vector(b), u); p.z -= sag * 4 * u * (1 - u)
        sp.points[i].co = (p.x, p.y, p.z, 1)
    ob = bpy.data.objects.new(name, cu); ob.data.materials.append(K.M['iron']); K._to(ob); return ob


def power_poles(xs, y):
    M = K.M; tops = []
    for x in xs:
        K._to(K.cylinder('power_pole', 0.006, 0.54, (x, y, 0.27), mat=M['bark']))
        K.block('pole_crossarm', x - 0.003, x + 0.003, y - 0.045, y + 0.045, 0.5, 0.507, M['bark'], bevel=0.001)
        for dy in (-0.04, 0.0, 0.04): K._to(K.cylinder('insulator', 0.0018, 0.008, (x, y + dy, 0.511), mat=M['porcelain']))
        tops.append(x)
    for a, b in zip(tops, tops[1:]):
        for dy in (-0.04, 0.0, 0.04): wire('power_wire', (a, y + dy, 0.515), (b, y + dy, 0.515), sag=0.035)
    for x in tops[1::2]:                                               # service wires across the lane to the north houses
        wire('service_wire', (x, y + 0.04, 0.515), (x + 0.15, VP.FRONT_N + 0.05, 0.47), sag=0.05)


def back_row(side, y_front, seed):
    """a second row of houses behind the street (seen between the front houses and over their roofs)"""
    r = random.Random(seed); x = -4.9
    facades = ('brick_wall', 'plaster_cream', 'siding_grey', 'plaster_blue', 'siding_cream')
    i = 0
    while x < 4.6:
        w = r.uniform(0.6, 0.8)
        house(f'back_{side}_{i}', x, x + w, side, r.uniform(0.7, 0.8), r.choice((1, 2, 2)), r.choice(('side', 'front')),
              r.choice(facades), 'door_black', tuple(int(r.random() < 0.15) for _ in range(5)), False, y_front=y_front)
        x += w + r.uniform(0.06, 0.14); i += 1


def build():
    materials()
    M = K.M
    for name, col in (('car_red', (0.22, 0.04, 0.035)), ('car_grey', (0.18, 0.2, 0.22)), ('car_cream', (0.5, 0.46, 0.36)),
                      ('car_green', (0.05, 0.12, 0.08)), ('car_blue', (0.06, 0.1, 0.2)), ('bin_green', (0.04, 0.1, 0.05)),
                      ('bin_black', (0.02, 0.02, 0.022)), ('flower_pink', (0.5, 0.25, 0.3)), ('flower_white', (0.6, 0.6, 0.55))):
        M[name] = K.painted(name, col, rough=0.35 if name.startswith('car') else 0.7)
    before = set(bpy.data.objects)
    street()
    for i, args in enumerate(VP.HOUSES):
        house(*args)
        name, x0, x1, side = args[:4]
        dx = VP.door_x(i)[0]
        garden(x0 - 0.04, x1 + 0.04, side, dx, hedge=name in VP.HEDGED)
        fy = VP.door_y(side) + (-0.035 if side == 'N' else 0.035)
        bushes(x0, x1, fy, dx, seed=i)
        sw = VP.SIDEWALK_N[1] - 0.026 if side == 'N' else VP.SIDEWALK_S[0] + 0.026
        if i % 3 != 2:
            wheelie_bin(dx + (0.075 if i % 2 else -0.075), sw, 'bin_green' if i % 2 else 'bin_black')
        gy = VP.SIDEWALK_N[1] + 0.03 if side == 'N' else VP.SIDEWALK_S[0] - 0.03
        mailbox(dx + 0.055, gy)
    haru_house(); hx = VP.HOME_AT[0] + VP.HOME_DOOR_X
    garden(-0.04, 1.04, 'N', hx); bushes(0.0, 1.0, VP.FRONT_N - 0.035, hx, seed=99); mailbox(hx + 0.055, VP.SIDEWALK_N[1] + 0.03)
    wheelie_bin(hx - 0.09, VP.SIDEWALK_N[1] - 0.026, 'bin_green')
    for c in VP.CIVIC:                                                 # the hospital and the police station
        civic(*c); forecourt(c[1] - 0.03, c[2] + 0.03, c[3], VP.civic_door_x(c[0]))
    for x in VP.LAMPS_N: street_lamp(x, 'N')
    for x in VP.LAMPS_S: street_lamp(x, 'S')
    for x, side, col in VP.CARS:                                       # parked along the curbs
        car(x, VP.ROAD[3] - 0.1 if side == 'N' else VP.ROAD[1] + 0.1, 0 if side == 'N' else 180, col)
    power_poles(VP.POLES_S, VP.SIDEWALK_S[0] + 0.012)
    back_row('N', 2.15, 11); back_row('S', -1.45, 12)
    for i, (tx, ty, s) in enumerate(((4.7, -0.55, 1.0), (5.05, -0.95, 1.2), (4.55, 1.1, 1.0), (-4.95, 1.2, 1.1), (-4.85, -0.75, 1.05),
                                     (1.05, 1.95, 0.9), (-1.3, 1.75, 1.0), (2.9, 1.8, 1.1), (-2.5, -1.3, 0.95), (0.55, -1.3, 1.0))):
        tree(tx, ty, s, seed=i)
    # night: a cold moon (sun lamp), dark blue sky, a thin haze down the lane
    K.world((0.012, 0.022, 0.06), 0.3)
    sun = bpy.data.lights.new('moon_sun', 'SUN'); sun.energy = 1.0; sun.color = (0.5, 0.62, 1.0); sun.angle = math.radians(1.5)
    so = bpy.data.objects.new('moon_sun', sun); K._to(so, 'Lights'); so.rotation_euler = (math.radians(62), 0, math.radians(-35))
    hz = bpy.data.materials.new('street_haze'); hz.use_nodes = True; hn = hz.node_tree.nodes
    hn.remove(hn['Principled BSDF']); pv = hn.new('ShaderNodeVolumePrincipled')
    pv.inputs['Density'].default_value = 0.08; pv.inputs['Anisotropy'].default_value = 0.5; pv.inputs['Color'].default_value = (0.75, 0.82, 1.0, 1)
    hz.node_tree.links.new(pv.outputs[0], hn['Material Output'].inputs['Volume'])
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.0, 0.2, 0.6)); b = bpy.context.object; b.name = 'haze'
    b.scale = (11.0, 4.5, 1.25); b.data.materials.append(hz); K._to(b)
    bpy.context.scene.cycles.volume_bounces = 0; bpy.context.scene.cycles.volume_step_rate = 4.0
    # camera marks
    K.mark('street_overview', (-4.6, 0.2, 0.42), (0.5, 0.35, 0.14), lens=26)
    K.mark('street_level', (-3.3, 0.06, 0.075), (1.0, 0.4, 0.13), lens=24)
    K.mark('haru_house', (0.62, -0.07, 0.11), (0.5, 0.72, 0.3), lens=20)
    K.mark('sidewalk', (1.5, 0.49, 0.09), (-1.5, 0.5, 0.09), lens=24)
    K.mark('hospital', (-3.6, -0.05, 0.11), (-3.9, 0.72, 0.28), lens=22)
    K.mark('police', (3.25, 0.4, 0.1), (3.02, -0.3, 0.24), lens=22)
    return [o for o in bpy.data.objects if o not in before]


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def opt(name, n=1, default=None):
        if '--' + name not in argv: return default
        i = argv.index('--' + name); v = argv[i + 1:i + 1 + n]; return v if n > 1 else v[0]
    RES = tuple(int(v) for v in opt('res', 2, ('1080', '1920')))
    OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews')))
    K.begin('village', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    bpy.context.scene.camera = None
    os.makedirs(OUT, exist_ok=True)
    for m in (opt('marks') or 'street_overview,street_level,haru_house,sidewalk').split(','): K.shoot(m, OUT, fstop=float(opt('fstop', 1, '11')))
    print('DONE village', OUT)
