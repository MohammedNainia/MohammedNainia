"""Reusable furniture for the house sets, built for horror action (Coraline-style miniature, 1:10, metres).

Every piece is built in its own frame (facing -y, origin on the floor at its front-centre) under a holder empty, then
placed with (x, y, yaw in degrees). Pieces people hide in or behind are sized for Haru (12.6 cm tall, about 3 cm
wide): beds stand high enough to slide under, wardrobes and cupboards are hollow with doors on hinges that animate
(their hinge empties are returned so a scene can open, close, creak or slam them).

    import props as PR
    bed = PR.bed(x, y, yaw)                 -> holder; bed['top'] is the mattress height
    w = PR.wardrobe(x, y, yaw)              -> holder; w['doors'] = [hinge names]; open with PR.swing(hinge, deg)
"""
import bpy, math, random
from mathutils import Vector
import kit as K

R = random.Random(21)


def holder(name, x, y, yaw=0.0, z=0.0):
    h = K.empty(name, (x, y, z)); K._to(h); h.rotation_euler = (0, 0, math.radians(yaw)); return h


def part(h, name, x0, x1, y0, y1, z0, z1, mat, bevel=0.0012, coll=False, lump=0.0, tilt=0.0):
    ob = K.block(name, x0, x1, y0, y1, z0, z1, K.M[mat] if isinstance(mat, str) else mat, bevel=bevel, coll=coll, tilt=tilt)
    if lump: K.add_lumps(ob, lump, size=0.012)
    return K.attach(ob, h)


def hinge(h, name, x, y, z=0.0):
    e = K.empty(name, (0, 0, 0)); K._to(e); K.attach(e, h); e.location = (x, y, z); return e


def swing(hinge_ob, deg):
    hinge_ob.rotation_euler = (0, 0, math.radians(deg))


# ------------------------------------------------------------------ bedroom
def bed(x, y, yaw=0.0, w=0.11, l=0.2, top=0.055, duvet='duvet', name='bed'):
    """a single bed standing high on its legs (3 cm clear underneath: room to hide), headboard at the back (+y)"""
    h = holder(name, x, y, yaw); h['top'] = top
    x0, x1, y0, y1 = -w / 2, w / 2, 0.0, l
    part(h, 'bed_frame', x0, x1, y0, y1, top - 0.024, top - 0.012, 'wood', bevel=0.002)
    for lx in (x0 + 0.004, x1 - 0.004):
        for ly in (y0 + 0.004, y1 - 0.004): part(h, 'bed_leg', lx - 0.004, lx + 0.004, ly - 0.004, ly + 0.004, 0, top - 0.02, 'wood', bevel=0.001)
    part(h, 'headboard', x0, x1, y1 - 0.008, y1, 0.0, top + 0.07, 'wood', bevel=0.003)
    part(h, 'footboard', x0, x1, y0, y0 + 0.006, 0.0, top + 0.02, 'wood', bevel=0.002)
    part(h, 'mattress', x0 + 0.002, x1 - 0.002, y0 + 0.006, y1 - 0.009, top - 0.012, top, 'bedsheet', bevel=0.005, coll=True, lump=0.0008)
    part(h, 'pillow', x0 + 0.014, x1 - 0.014, y1 - 0.05, y1 - 0.012, top - 0.002, top + 0.006, 'bedsheet', bevel=0.004, coll=True, lump=0.001)
    part(h, 'duvet', x0 - 0.002, x1 + 0.002, y0 + 0.006, y1 - 0.068, top - 0.002, top + 0.008, duvet, bevel=0.004, lump=0.0014)
    # the duvet hangs down the sides almost to the floor: what is under the bed stays in shadow
    for sx in (-1, 1):
        xa, xb = sorted(((x1 + 0.001) * sx, (x1 + 0.005) * sx))
        part(h, 'duvet_side', xa, xb, y0 + 0.01, y1 - 0.07, 0.014, top + 0.004, duvet, bevel=0.002, lump=0.001)
    return h


def wardrobe(x, y, yaw=0.0, w=0.07, d=0.045, hgt=0.19, name='wardrobe', mat='wood'):
    """a tall hollow wardrobe with two doors on hinges (Haru fits inside standing); returns the holder, its hinges in
    holder['doors'] (left, right)"""
    h = holder(name, x, y, yaw); t = 0.003
    part(h, 'wardrobe_back', -w / 2, w / 2, d - t, d, 0.0, hgt, mat)
    for sx in (-1, 1):
        xa, xb = sorted((sx * w / 2, sx * (w / 2 - t)))
        part(h, 'wardrobe_side', xa, xb, 0.0, d, 0.0, hgt, mat)
    part(h, 'wardrobe_top', -w / 2 - 0.002, w / 2 + 0.002, -0.002, d + 0.002, hgt, hgt + 0.006, mat, bevel=0.002)
    part(h, 'wardrobe_floor', -w / 2, w / 2, 0.0, d, 0.0, 0.008, mat, coll=True)
    part(h, 'wardrobe_rail', -w / 2 + t, w / 2 - t, d / 2 - 0.001, d / 2 + 0.001, hgt - 0.02, hgt - 0.018, 'chrome', bevel=0.0005)
    for i in range(3):                                                   # coats and dresses on the rail
        xx = -w / 2 + 0.012 + i * (w - 0.024) / 2
        c = K.sphere('wardrobe_coat', 0.008, (0, 0, 0), scale=(0.9, 1.4, 4.5), mat=K.M['coat']); K._to(c); K.attach(c, h)
        c.location = (xx, d / 2 + 0.004, hgt - 0.06); K.add_lumps(c, 0.0008, size=0.008)
    doors = []
    for sx, nm in ((-1, 'L'), (1, 'R')):
        hg = hinge(h, f'{name}_door_{nm}', sx * w / 2, 0.0)
        dw = w / 2 - 0.001
        xa, xb = sorted((0.0, -sx * dw))
        part(hg, 'wardrobe_door', xa, xb, -0.003, 0.0, 0.01, hgt - 0.004, mat, bevel=0.0012)
        kx = -sx * (dw - 0.005)
        kn = K.sphere('wardrobe_knob', 0.0016, (0, 0, 0), mat=K.M['brass']); K._to(kn); K.attach(kn, hg); kn.location = (kx, -0.004, hgt * 0.5)
        doors.append(hg.name)
    h['doors'] = doors
    return h


def bedside(x, y, yaw=0.0, lamp=True, energy=0.5):
    h = holder('bedside', x, y, yaw)
    part(h, 'bedside_table', -0.017, 0.017, 0.0, 0.034, 0.0, 0.045, 'wood', bevel=0.002)
    part(h, 'bedside_drawer', -0.014, 0.014, -0.001, 0.001, 0.025, 0.04, 'wood', bevel=0.001)
    if lamp:
        lb = K.cylinder('lamp_base', 0.005, 0.016, (0, 0, 0), mat=K.M['trim']); K._to(lb); K.attach(lb, h); lb.location = (0, 0.017, 0.053)
        ls = K.cylinder('lamp_shade', 0.01, 0.013, (0, 0, 0), mat=K.M['shade']); K._to(ls); K.attach(ls, h); ls.location = (0, 0.017, 0.067)
        lt = K.point_light('bedside_lamp', (0, 0, 0), energy, radius=0.006, color=(1.0, 0.66, 0.35)); K._to(lt, 'Lights'); K.attach(lt, h)
        lt.location = (0, 0.017, 0.067); h['light'] = lt.name
    return h


# ------------------------------------------------------------------ living / dining
def sofa(x, y, yaw=0.0, l=0.14, d=0.045, seat=0.026, name='sofa', blanket=True):
    """a sagging sofa, back to +y; there is a gap behind it to crouch in when it stands off the wall"""
    h = holder(name, x, y, yaw)
    part(h, 'sofa_base', -l / 2, l / 2, 0.0, d, 0.004, seat - 0.006, 'sofa', bevel=0.004)
    for k in range(3):
        a = -l / 2 + 0.008 + k * (l - 0.016) / 3
        c = part(h, 'sofa_cushion', a + 0.001, a + (l - 0.016) / 3 - 0.001, 0.0, d - 0.008, seat - 0.008, seat, 'sofa', bevel=0.005, coll=True, lump=0.0012)
        if k == 1: c.location.z -= 0.0015
    part(h, 'sofa_back', -l / 2, l / 2, d - 0.012, d, seat - 0.006, 0.058, 'sofa', bevel=0.005)
    for sx in (-1, 1):
        xa, xb = sorted((sx * l / 2, sx * (l / 2 - 0.01)))
        part(h, 'sofa_arm', xa, xb, 0.0, d, seat - 0.006, 0.04, 'sofa', bevel=0.005)
    if blanket: part(h, 'knit_blanket', l / 2 - 0.03, l / 2 + 0.002, -0.004, d - 0.004, 0.02, 0.042, 'knit_blanket', bevel=0.004, lump=0.002)
    return h


def armchair(x, y, yaw=0.0, seat=0.026):
    h = holder('armchair', x, y, yaw)
    for nm, a, b, c, d, e, f in (('seat', -0.02, 0.02, 0.0, 0.038, 0.008, seat), ('back', -0.02, 0.02, 0.03, 0.04, seat, 0.065),
                                  ('arm_l', -0.024, -0.016, 0.0, 0.04, 0.008, 0.042), ('arm_r', 0.016, 0.024, 0.0, 0.04, 0.008, 0.042)):
        part(h, 'armchair_' + nm, a, b, c, d, e, f, 'sofa', bevel=0.005, lump=0.0008, coll=(nm == 'seat'))
    return h


def table(x, y, yaw=0.0, w=0.09, d=0.06, hgt=0.06, mat='counter', cloth=False):
    """a table; with cloth=True a long tablecloth hangs to the floor (a place to hide under)"""
    h = holder('table', x, y, yaw)
    part(h, 'table_top', -w / 2, w / 2, -d / 2, d / 2, hgt - 0.005, hgt, mat, bevel=0.0015, coll=True)
    for sx in (-1, 1):
        for sy in (-1, 1): part(h, 'table_leg', sx * (w / 2 - 0.005) - 0.0025, sx * (w / 2 - 0.005) + 0.0025, sy * (d / 2 - 0.005) - 0.0025,
                                sy * (d / 2 - 0.005) + 0.0025, 0, hgt - 0.005, mat, bevel=0.0008)
    if cloth:
        part(h, 'tablecloth', -w / 2 - 0.003, w / 2 + 0.003, -d / 2 - 0.003, d / 2 + 0.003, hgt, hgt + 0.0012, 'bedsheet', bevel=0.0006)
        for (a, b, c, dd) in ((-w / 2 - 0.003, w / 2 + 0.003, -d / 2 - 0.004, -d / 2 - 0.002), (-w / 2 - 0.003, w / 2 + 0.003, d / 2 + 0.002, d / 2 + 0.004),
                              (-w / 2 - 0.004, -w / 2 - 0.002, -d / 2 - 0.003, d / 2 + 0.003), (w / 2 + 0.002, w / 2 + 0.004, -d / 2 - 0.003, d / 2 + 0.003)):
            part(h, 'tablecloth_drop', a, b, c, dd, 0.004, hgt + 0.001, 'bedsheet', bevel=0.0008, lump=0.0006)
    return h


def bookshelf(x, y, yaw=0.0, w=0.065, d=0.02, hgt=0.15):
    h = holder('bookshelf', x, y, yaw)
    part(h, 'bookshelf', -w / 2, w / 2, 0.0, d, 0.0, hgt, 'wood', bevel=0.0015)
    for shelf in [0.012 + i * 0.036 for i in range(int(hgt / 0.036))]:
        part(h, 'shelf', -w / 2 + 0.002, w / 2 - 0.002, -0.0015, 0.0005, shelf - 0.002, shelf, 'wood', bevel=0.0004)
        xx = -w / 2 + 0.004
        while xx < w / 2 - 0.008:
            bw = R.uniform(0.003, 0.0055); bh = R.uniform(0.018, 0.03)
            part(h, 'book', xx, xx + bw, -0.001, 0.014, shelf, shelf + bh, R.choice(['book1', 'book2', 'book3', 'book4']), bevel=0.0004)
            xx += bw + 0.0005
    return h


def tv(x, y, yaw=0.0, energy=0.35):
    """an old CRT television on a low cabinet; its glow is a light"""
    h = holder('tv', x, y, yaw)
    part(h, 'tv_cabinet', -0.032, 0.032, 0.0, 0.034, 0.0, 0.03, 'wood', bevel=0.0015)
    part(h, 'tv_body', -0.026, 0.026, 0.004, 0.034, 0.03, 0.074, 'iron', bevel=0.006)
    part(h, 'tv_screen', -0.02, 0.016, 0.003, 0.005, 0.037, 0.068, 'tv_screen', bevel=0.003)
    gl = K.area_light('tv_glow', (0, 0, 0), (0, -1, 0), energy, 0.03, (0.55, 0.7, 1.0)); K._to(gl, 'Lights')
    K.attach(gl, h); gl.location = (0, -0.002, 0.052); gl.rotation_euler = (math.radians(90), 0, 0)
    return h


def grandfather_clock(x, y, yaw=0.0):
    h = holder('clock', x, y, yaw)
    part(h, 'clock_case', -0.012, 0.012, 0.0, 0.015, 0.0, 0.17, 'wood', bevel=0.002)
    part(h, 'clock_hood', -0.014, 0.014, -0.002, 0.017, 0.15, 0.19, 'wood', bevel=0.003)
    part(h, 'clock_window', -0.006, 0.006, -0.0012, 0.0, 0.04, 0.12, 'glass', bevel=0.001)
    f = K.cylinder('clock_face', 0.009, 0.002, (0, 0, 0), rot=(math.pi / 2, 0, 0), mat=K.M['paper']); K._to(f); K.attach(f, h); f.location = (0, -0.003, 0.17)
    return h


# ------------------------------------------------------------------ kitchen
def counter_run(x0, x1, y_back, yaw=0.0, d=0.045, hgt=0.068, sink_at=None, stove_at=None):
    """base cupboards with doors you can hide behind, a worktop, an optional sink and an old gas stove; built along x
    against a wall at y_back (in the holder frame), the cupboards' fronts facing -y"""
    h = holder('counter', 0, 0, yaw)
    y0 = y_back - d
    part(h, 'base_cupboards', x0, x1, y0 + 0.003, y_back, 0.004, hgt - 0.004, 'cabinet', bevel=0.0012)
    xx = x0 + 0.002
    while xx + 0.03 <= x1:
        part(h, 'cupboard_door', xx, xx + 0.03, y0 - 0.0005, y0 + 0.003, 0.01, hgt - 0.012, 'cabinet', bevel=0.0015)
        kn = K.sphere('cupboard_knob', 0.0016, (0, 0, 0), mat=K.M['brass']); K._to(kn); K.attach(kn, h); kn.location = (xx + 0.026, y0 - 0.002, hgt - 0.02)
        xx += 0.033
    part(h, 'worktop', x0 - 0.002, x1 + 0.002, y0 - 0.003, y_back, hgt - 0.004, hgt, 'counter', bevel=0.001, coll=True)
    if sink_at is not None:
        sx = sink_at
        part(h, 'sink', sx - 0.02, sx + 0.02, y0 + 0.006, y_back - 0.006, hgt - 0.001, hgt + 0.0015, 'enamel', bevel=0.003)
        part(h, 'sink_hole', sx - 0.016, sx + 0.016, y0 + 0.01, y_back - 0.01, hgt + 0.0015, hgt + 0.0018, 'iron', bevel=0.002)
        t = K.cylinder('sink_tap', 0.002, 0.022, (0, 0, 0), mat=K.M['chrome']); K._to(t); K.attach(t, h); t.location = (sx, y_back - 0.006, hgt + 0.011)
    if stove_at is not None:
        gx = stove_at
        part(h, 'stove', gx - 0.024, gx + 0.024, y0 - 0.002, y_back, 0.004, hgt + 0.002, 'fridge', bevel=0.003)
        part(h, 'oven_door', gx - 0.019, gx + 0.019, y0 - 0.004, y0 - 0.001, 0.012, 0.05, 'fridge', bevel=0.002)
        for bx_, by_ in ((gx - 0.011, y0 + 0.012), (gx + 0.011, y0 + 0.012), (gx - 0.011, y_back - 0.012), (gx + 0.011, y_back - 0.012)):
            b = K.cylinder('burner', 0.0065, 0.002, (0, 0, 0), mat=K.M['iron']); K._to(b); K.attach(b, h); b.location = (bx_, by_, hgt + 0.003)
    return h


def fridge(x, y, yaw=0.0, open_deg=0.0, light=0.3):
    """an old rounded fridge, its door on a hinge (open_deg > 0: ajar, cold light spilling out)"""
    h = holder('fridge', x, y, yaw); w, d, hh = 0.05, 0.055, 0.155
    part(h, 'fridge_body', -w / 2, w / 2, 0.004, d, 0.004, hh, 'fridge', bevel=0.008)
    part(h, 'fridge_inside', -w / 2 + 0.004, w / 2 - 0.004, 0.0035, 0.0045, 0.012, hh - 0.01, 'fridge_in', bevel=0)
    hg = hinge(h, 'fridge_door_hinge', w / 2, 0.0)
    part(hg, 'fridge_door', -w, 0.0, -0.006, 0.0, 0.006, hh - 0.002, 'fridge', bevel=0.006)
    part(hg, 'fridge_handle', -w + 0.004, -w + 0.007, -0.01, -0.006, 0.06, 0.11, 'chrome', bevel=0.0012)
    swing(hg, -open_deg)
    if open_deg > 0:
        lt = K.point_light('fridge_light', (0, 0, 0), light, radius=0.01, color=(0.82, 0.92, 1.0)); K._to(lt, 'Lights'); K.attach(lt, h)
        lt.location = (0, -0.01, hh - 0.04)
    h['door'] = hg.name
    return h


def boxes(x0, x1, y0, y1, seed=1):
    """a jumble of stacked cardboard boxes along a strip (good cover)"""
    r = random.Random(seed); y = y0
    while y < y1 - 0.03:
        w, dd, hh = r.uniform(0.03, 0.045), r.uniform(0.03, 0.045), r.uniform(0.025, 0.04)
        xa = x0 + r.uniform(0, max(0.0, (x1 - x0) - w))
        K.block('box', xa, xa + w, y, y + dd, 0, hh, K.M['cardboard'], bevel=0.0015, tilt=0.03)
        if r.random() < 0.6:
            K.block('box', xa + 0.003, xa + w - 0.002, y + 0.003, y + dd - 0.003, hh, hh + r.uniform(0.02, 0.03), K.M['cardboard'], bevel=0.0015, tilt=0.06)
        y += dd + r.uniform(0.004, 0.015)
