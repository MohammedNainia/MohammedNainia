"""The modular room kit for Haru's house (Coraline-style miniature sets, 1:10 scale, metres).

Rooms are built from a handful of calls, so every room shares the same look and joins the others on one floor plan:

    import kit as K
    K.begin()                                   # fresh scene, render settings, shared materials
    K.floor((x0, y0, x1, y1), holes=[...])      # floorboards (holes for stairwells)
    K.ceiling((x0, y0, x1, y1))
    K.wall((x0, y0), (x1, y1), openings=[K.door(u0, u1), K.window(u0, u1, z0, z1)])
    K.stairs_down(...); K.banister(...)
    K.picture(...); K.radiator(...); K.runner(...); K.sconce(...)
    K.mood('night', moon=..., ...)              # lighting presets
    K.mark('wide', loc, target, lens)           # named camera marks, saved with the room

Rules from library/STYLE.md: nothing perfectly straight (walls lean a fraction of a degree, frames and pictures are
crooked), worn materials (faded patterned wallpaper, gappy floorboards, scuffed paint), skirting and frames on every
wall. Every walkable or sittable surface goes into the Colliders collection for the contact solver.
"""
import bpy, math, os, sys, random
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
BL = os.path.normpath(os.path.join(HERE, '..', '..'))                 # YTB/horror/blender
sys.path.insert(0, os.path.join(BL, 'puppets'))
import haru_puppet as HP                                              # also puts claylib on the path
import burton_materials as BM
from claylib import *

WT = 0.01            # wall thickness
H = 0.25             # ceiling height (2.5 m)
DOOR_H = 0.2         # door opening height
RNG = random.Random(13)
HOUSE = False        # True while house.py assembles every room into one scene
M = {}               # shared materials, made in begin()


# ------------------------------------------------------------------ materials
def _nodes(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes['Principled BSDF']


def wallpaper(name, base, ink, scale=60.0, fade=0.5):
    """faded patterned wallpaper: a small repeating motif (voronoi dots on stripes), water stains, darker near the
    floor and ceiling; object coordinates so the pattern keeps its size on every panel"""
    m, nt, b = _nodes(name); N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord').outputs['Object']
    st = N.new('ShaderNodeTexWave'); st.bands_direction = 'X'; st.inputs['Scale'].default_value = scale * 0.5
    L.new(tc, st.inputs['Vector'])
    vo = N.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = scale * 1.6; L.new(tc, vo.inputs['Vector'])
    dots = N.new('ShaderNodeMath'); dots.operation = 'LESS_THAN'; L.new(vo.outputs['Distance'], dots.inputs[0]); dots.inputs[1].default_value = 0.18
    pat = N.new('ShaderNodeMath'); pat.operation = 'MAXIMUM'
    sp = N.new('ShaderNodeMath'); sp.operation = 'POWER'; L.new(st.outputs['Fac'], sp.inputs[0]); sp.inputs[1].default_value = 6.0
    L.new(sp.outputs[0], pat.inputs[0]); L.new(dots.outputs[0], pat.inputs[1])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; L.new(pat.outputs[0], mx.inputs[0])
    mx.inputs[6].default_value = (*base, 1); mx.inputs[7].default_value = (*ink, 1)
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9.0; nz.inputs['Detail'].default_value = 6; L.new(tc, nz.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB'); L.new(nz.outputs['Fac'], ramp.inputs[0])
    ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[0].color = (0.55, 0.5, 0.4, 1)    # stains
    ramp.color_ramp.elements[1].position = 0.62; ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    st2 = N.new('ShaderNodeMix'); st2.data_type = 'RGBA'; st2.blend_type = 'MULTIPLY'; st2.inputs[0].default_value = fade
    L.new(mx.outputs[2], st2.inputs[6]); L.new(ramp.outputs[0], st2.inputs[7])
    L.new(st2.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.85
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.08; bump.inputs['Distance'].default_value = 0.0003
    L.new(nz.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def boards(name, c1, c2, scale=38.0):
    """worn floorboards along Y with dark gaps, grain and scuffs"""
    m, nt, b = _nodes(name); N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord').outputs['Object']
    w = N.new('ShaderNodeTexWave'); w.bands_direction = 'X'; w.wave_profile = 'SAW'; w.inputs['Scale'].default_value = scale
    L.new(tc, w.inputs['Vector'])
    gap = N.new('ShaderNodeMath'); gap.operation = 'GREATER_THAN'; L.new(w.outputs['Fac'], gap.inputs[0]); gap.inputs[1].default_value = 0.96
    gr = N.new('ShaderNodeTexWave'); gr.bands_direction = 'Y'; gr.inputs['Scale'].default_value = scale * 6
    gr.inputs['Distortion'].default_value = 6.0; gr.inputs['Detail'].default_value = 4; L.new(tc, gr.inputs['Vector'])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; L.new(gr.outputs['Fac'], mx.inputs[0])
    mx.inputs[6].default_value = (*c1, 1); mx.inputs[7].default_value = (*c2, 1)
    dk = N.new('ShaderNodeMix'); dk.data_type = 'RGBA'; L.new(gap.outputs[0], dk.inputs[0])
    L.new(mx.outputs[2], dk.inputs[6]); dk.inputs[7].default_value = (0.01, 0.006, 0.004, 1)
    L.new(dk.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.55
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25; bump.inputs['Distance'].default_value = 0.0004
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(gap.outputs[0], inv.inputs[1])
    L.new(inv.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def painted(name, c, rough=0.55):
    return clay(name, c, rough=rough, sss=0.0, bump=0.15, thumb=0.08, scale=2.0)


def tiles(name, c, grout, scale=90.0, ratio=0.5, rough=0.25):
    """glazed tiles with grout lines and a little uneven colour (Brick texture in object space); ratio < 1 gives
    subway tiles, 1 gives square ones"""
    m, nt, b = _nodes(name); N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord').outputs['Object']
    mp = N.new('ShaderNodeMapping'); L.new(tc, mp.inputs['Vector']); mp.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    br = N.new('ShaderNodeTexBrick'); L.new(mp.outputs['Vector'], br.inputs['Vector'])
    br.inputs['Scale'].default_value = scale; br.inputs['Mortar Size'].default_value = 0.012
    br.inputs['Brick Width'].default_value = 0.5; br.inputs['Row Height'].default_value = 0.5 * ratio
    br.inputs['Color1'].default_value = (*c, 1); br.inputs['Color2'].default_value = tuple(v * 0.9 for v in c) + (1,)
    br.inputs['Mortar'].default_value = (*grout, 1)
    L.new(br.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.3; bump.inputs['Distance'].default_value = 0.0004
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(br.outputs['Fac'], inv.inputs[1])
    L.new(inv.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def checker(name, c1, c2, scale=60.0):
    """a floor of square tiles in two colours, slightly worn"""
    m, nt, b = _nodes(name); N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord').outputs['Object']
    ck = N.new('ShaderNodeTexChecker'); L.new(tc, ck.inputs['Vector']); ck.inputs['Scale'].default_value = scale
    ck.inputs['Color1'].default_value = (*c1, 1); ck.inputs['Color2'].default_value = (*c2, 1)
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 25; L.new(tc, nz.inputs['Vector'])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 0.35
    L.new(ck.outputs['Color'], mx.inputs[6]); L.new(nz.outputs['Color'], mx.inputs[7])
    L.new(mx.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.35
    return m


def mirror_mat(name='mirror'):
    m, nt, b = _nodes(name); b.inputs['Metallic'].default_value = 1.0; b.inputs['Roughness'].default_value = 0.04
    b.inputs['Base Color'].default_value = (0.8, 0.82, 0.8, 1); return m


def materials():
    M.update({
        'wall': wallpaper('wallpaper_hall', (0.36, 0.38, 0.3), (0.24, 0.27, 0.2)),
        'wall_bath': wallpaper('wallpaper_bath', (0.42, 0.46, 0.44), (0.32, 0.38, 0.38), scale=80),
        'floor': boards('floorboards', (0.16, 0.09, 0.05), (0.09, 0.05, 0.028)),
        'ceiling': painted('ceiling_plaster', (0.42, 0.41, 0.38), rough=0.9),
        'trim': painted('trim_paint', (0.5, 0.48, 0.42)),
        'wood': painted('dark_wood', (0.07, 0.04, 0.025), rough=0.45),
        'door': painted('door_paint', (0.32, 0.3, 0.25)),
        'brass': painted('brass', (0.45, 0.33, 0.12), rough=0.3),
        'metal': painted('radiator_paint', (0.46, 0.45, 0.42), rough=0.4),
        'runner': BM.fabric('runner_rug', '#5b2f2c', 'knit', fuzz=0.3),
        'curtain': BM.fabric('curtain_hall', '#4a3b2a', 'weave', fuzz=0.6, scale=900, dark=0.7),
        'void': emissive('void', (0, 0, 0), 0.0),
        'sky': emissive('night_sky', (0.08, 0.13, 0.3), 0.6),
        'moon': emissive('moon', (0.9, 0.93, 1.0), 6.0),
        'photo': painted('photo_dark', (0.12, 0.11, 0.1), rough=0.3),
        'shade': emissive('sconce_shade', (1.0, 0.65, 0.33), 2.5),
        'beyond': painted('room_beyond', (0.3, 0.24, 0.18), rough=0.9),
        'tiles_wall': tiles('tiles_wall', (0.62, 0.64, 0.58), (0.25, 0.25, 0.22)),
        'tiles_floor': checker('tiles_floor', (0.55, 0.54, 0.5), (0.08, 0.09, 0.09)),
        'enamel': painted('enamel', (0.72, 0.7, 0.62), rough=0.22),
        'chrome': painted('chrome', (0.6, 0.6, 0.62), rough=0.12),
        'mirror': mirror_mat(),
        'towel': BM.fabric('towel', '#7d8f86', 'knit', fuzz=1.0),
        'bathmat': BM.fabric('bathmat', '#8a6f78', 'knit', fuzz=1.0),
        'shower_curtain': painted('shower_curtain', (0.55, 0.6, 0.55), rough=0.5),
        'duck': painted('duck', (0.75, 0.55, 0.08), rough=0.35),
        'bulb': emissive('bare_bulb', (1.0, 0.85, 0.6), 8.0),
        'bulb_off': painted('bulb_off', (0.55, 0.52, 0.45), rough=0.15),
        'planks': boards('roof_planks', (0.12, 0.075, 0.045), (0.07, 0.042, 0.025), scale=30.0),
        'sheet_cloth': BM.fabric('dust_sheet', '#b9b3a6', 'weave', fuzz=0.9, scale=600, dark=0.6),
        'cardboard': painted('cardboard', (0.36, 0.25, 0.14), rough=0.9),
        'tape': painted('tape', (0.5, 0.42, 0.25), rough=0.4),
        'leather': painted('trunk_leather', (0.2, 0.08, 0.05), rough=0.5),
        'dummy': BM.fabric('dummy_linen', '#a99c86', 'weave', fuzz=0.5, scale=500, dark=0.7),
        'porcelain': painted('porcelain', (0.78, 0.68, 0.6), rough=0.25),
        'plush': BM.fabric('teddy_plush', '#6b4a2c', 'knit', fuzz=1.0),
        'lino': checker('linoleum', (0.42, 0.4, 0.33), (0.25, 0.3, 0.27), scale=45.0),
        'cabinet': painted('cabinet_green', (0.24, 0.3, 0.24), rough=0.5),
        'counter': painted('counter_top', (0.38, 0.33, 0.26), rough=0.4),
        'fridge': painted('fridge_cream', (0.7, 0.67, 0.56), rough=0.25),
        'fridge_in': emissive('fridge_inside', (0.85, 0.92, 1.0), 0.45),
        'iron': painted('cast_iron', (0.05, 0.05, 0.055), rough=0.5),
        'paper': painted('paper', (0.7, 0.66, 0.56), rough=0.9),
        'tiles_kitchen': tiles('tiles_kitchen', (0.6, 0.6, 0.52), (0.3, 0.29, 0.25), scale=110, ratio=1.0),
        'red': painted('faded_red', (0.45, 0.1, 0.08), rough=0.5),
        'glass': painted('jar_glass', (0.45, 0.5, 0.45), rough=0.1),
        'bedsheet': BM.fabric('bedsheet', '#b9b4ad', 'weave', fuzz=0.6, scale=1500, dark=0.85),
        'duvet': BM.fabric('duvet', '#4b3a52', 'knit', fuzz=0.9),
        'sofa': BM.fabric('sofa_velvet', '#4a3a30', 'weave', fuzz=1.0, scale=500, dark=0.6),
        'knit_blanket': BM.fabric('knit_blanket', '#7a4a3a', 'knit', fuzz=0.8),
        'tv_screen': emissive('tv_screen', (0.55, 0.7, 1.0), 0.7),
        'book1': painted('book_red', (0.32, 0.08, 0.06)), 'book2': painted('book_green', (0.1, 0.2, 0.12)),
        'book3': painted('book_blue', (0.08, 0.12, 0.25)), 'book4': painted('book_ochre', (0.45, 0.32, 0.1)),
        'coat': BM.fabric('coat_wool', '#3b3530', 'weave', fuzz=0.8, scale=600, dark=0.6),
    })
    return M


# ------------------------------------------------------------------ scene
def begin(name, res=(1080, 1920), samples=64, frames=1):
    reset()
    sc = setup_render(res=res, samples=samples, frames=frames)
    HP.fast_cycles(sc)
    world((0.02, 0.025, 0.045), 0.1)
    sc.view_settings.exposure = -0.25
    try: sc.view_settings.look = 'AgX - High Contrast'
    except TypeError: pass
    materials()
    for cname in ('Set', 'Lights', 'Marks'):
        if cname not in bpy.data.collections:
            c = bpy.data.collections.new(cname); sc.collection.children.link(c)
    return sc


def _to(ob, cname='Set'):
    for c in list(ob.users_collection): c.objects.unlink(ob)
    bpy.data.collections[cname].objects.link(ob); return ob


def attach(child, par):
    """parent in the parent's local frame (pieces are built in wall/holder coordinates)"""
    child.parent = par; child.matrix_parent_inverse = Matrix.Identity(4); return child


def block(name, x0, x1, y0, y1, z0, z1, mat, bevel=0.0008, coll=False, tilt=0.0):
    ob = rounded_box(name, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), bevel=bevel, mat=mat)
    if tilt: ob.rotation_euler = (RNG.uniform(-tilt, tilt), RNG.uniform(-tilt, tilt), RNG.uniform(-tilt, tilt))
    _to(ob)
    if coll: HP.colliders().objects.link(ob)
    return ob


# ------------------------------------------------------------------ floor, ceiling, walls
def floor(rect, holes=(), z=0.0, mat='floor'):
    """floor slab over rect (x0, y0, x1, y1), minus rectangular holes (stairwells)"""
    for (a0, b0, a1, b1) in _cut(rect, holes):
        block('floor', a0, a1, b0, b1, z - 0.01, z, M[mat], bevel=0.0003, coll=True)


def ceiling(rect, holes=(), z=H):
    for (a0, b0, a1, b1) in _cut(rect, holes):
        block('ceiling', a0, a1, b0, b1, z - 0.008, z, M['ceiling'], bevel=0.0003)     # under the next floor, not into it


def _cut(rect, holes):
    """split rect into boxes that avoid the holes (grid decomposition)"""
    x0, y0, x1, y1 = rect
    xs = sorted({x0, x1, *[h[0] for h in holes], *[h[2] for h in holes]}); xs = [x for x in xs if x0 <= x <= x1]
    ys = sorted({y0, y1, *[h[1] for h in holes], *[h[3] for h in holes]}); ys = [y for y in ys if y0 <= y <= y1]
    out = []
    for i in range(len(xs) - 1):
        col = []
        for j in range(len(ys) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            inside = any(h[0] <= cx <= h[2] and h[1] <= cy <= h[3] for h in holes)
            if not inside:
                if col and col[-1][3] == ys[j]: col[-1] = (col[-1][0], col[-1][1], col[-1][2], ys[j + 1])
                else: col.append((xs[i], ys[j], xs[i + 1], ys[j + 1]))
        out += col
    return out


def door(u0, u1, h=DOOR_H, kind='door', angle=0.0, leaf=True, hinge='start', spill=None, keep=False):
    """keep=True: an outside door or a cupboard; in the house the other doors swing wide open so she can walk through"""
    return dict(kind=kind, u0=u0, u1=u1, z0=0.0, z1=h, angle=angle, leaf=leaf, hinge=hinge, spill=spill, keep=keep)


def window(u0, u1, z0, z1, curtains=True, moon=False, sky=True):
    return dict(kind='window', u0=u0, u1=u1, z0=z0, z1=z1, curtains=curtains, moon=moon, sky=sky)


def wall(a, b, openings=(), h=H, mat='wall', skirting=True, inward=None):
    """A straight wall from a to b (xy), WT thick, centred on the line. `inward` is the room side (+1 = left of a->b).
    Openings are measured along the wall from a (u, metres). Doors get a frame, a leaf on a hinge (angle in degrees,
    0 = shut) and darkness or light behind; windows get a frame, cross bars, a sill, curtains, and sky (and a moon)."""
    a, b = Vector((*a, 0)), Vector((*b, 0)); d = (b - a); L_ = d.length; t = d.normalized()
    n = Vector((-t.y, t.x, 0)) * (inward or 1)
    rot = math.atan2(t.y, t.x)
    pieces = _cut((0, 0, L_, h), [(o['u0'], o['z0'], o['u1'], o['z1']) for o in openings])
    lean = RNG.uniform(-0.004, 0.004)                                  # walls are never quite plumb
    holder = empty('wall', tuple(a)); _to(holder); holder.rotation_euler = (lean * (inward or 1), 0, rot)
    for (u0, z0, u1, z1) in pieces:
        ob = block('wall_panel', u0, u1, -WT / 2, WT / 2, z0, z1, M[mat], bevel=0.0004); attach(ob, holder)
    side = (inward or 1)
    def P(u, off, z): return a + t * u + n * off + Vector((0, 0, z))
    if skirting:
        edges = [0.0] + sum([[o['u0'], o['u1']] for o in openings if o['kind'] != 'window'], []) + [L_]
        for i in range(0, len(edges), 2):
            if edges[i + 1] - edges[i] > 0.002:
                sk = block('skirting', edges[i], edges[i + 1], side * (WT / 2), side * (WT / 2 + 0.004), 0, 0.012, M['trim'], bevel=0.001)
                attach(sk, holder)
    for o in openings:
        _frame(holder, o, side, a, t, n)
    return holder


def _frame(holder, o, side, a, t, n):
    u0, u1, z0, z1 = o['u0'], o['u1'], o['z0'], o['z1']; f = 0.007; s = side
    y0, y1 = s * (WT / 2 - 0.012), s * (WT / 2 + 0.003)
    yy = (min(y0, y1), max(y0, y1))
    parts = [(u0 - f, u0, z0, z1 + f), (u1, u1 + f, z0, z1 + f), (u0, u1, z1, z1 + f)]
    if o['kind'] == 'window': parts.append((u0, u1, z0 - f, z0))
    for (p0, p1, q0, q1) in parts:
        fr = block('frame', p0, p1, yy[0], yy[1], q0, q1, M['trim'], bevel=0.0009); attach(fr, holder)
    if o['kind'] == 'window':
        sl = block('sill', u0 - 0.012, u1 + 0.012, s * (WT / 2) if s > 0 else -WT / 2 - 0.014, s * (WT / 2 + 0.014) if s > 0 else -WT / 2,
                   z0 - 0.009, z0 - 0.005, M['trim'], bevel=0.001); attach(sl, holder)
        um, zm = (u0 + u1) / 2, (z0 + z1) / 2
        for (p0, p1, q0, q1) in ((um - 0.002, um + 0.002, z0, z1), (u0, u1, zm - 0.002, zm + 0.002)):
            bar = block('window_bar', p0, p1, -0.002, 0.002, q0, q1, M['trim'], bevel=0.0005); attach(bar, holder)
        if o.get('sky', True):
            sky = block('sky', u0 - 0.07, u1 + 0.07, -s * 0.2, -s * 0.19, z0 - 0.07, z1 + 0.07, M['sky'], bevel=0); attach(sky, holder)
            sky.visible_shadow = False
        if o.get('moon'):
            mn = sphere('moon', 0.02, (0, 0, 0), mat=M['moon']); _to(mn); attach(mn, holder)
            mn.location = (um - 0.02, -s * 0.18, zm + 0.02); mn.visible_shadow = False
        if o.get('curtains'):
            for cu in (u0 - 0.012, u1 + 0.012):
                c = block('curtain', cu - 0.014, cu + 0.014, s * (WT / 2 + 0.004), s * (WT / 2 + 0.012), z0 - 0.04, z1 + 0.012,
                          M['curtain'], bevel=0.004)
                add_lumps(c, 0.0015, size=0.01); attach(c, holder)
    else:
        beyond = M['beyond'] if o.get('spill') else M['void']             # a lit room behind shows its walls
        if HOUSE: beyond = None                                             # in the house the next room is behind it
        if beyond is not None:
            dark = block('doorway_dark', u0 - 0.05, u1 + 0.05, -s * 0.06, -s * 0.07, -0.01, z1 + 0.05, beyond, bevel=0); attach(dark, holder)
            for (p0, p1, sgn) in ((u0 - 0.05, u0 - 0.04, 1), (u1 + 0.04, u1 + 0.05, 1)):
                side_w = block('doorway_side', p0, p1, -s * 0.0, -s * 0.07, -0.01, z1 + 0.05, beyond, bevel=0); attach(side_w, holder)
        if o.get('leaf'):
            hu = u0 if o['hinge'] == 'start' else u1
            hg = empty('door_hinge', (0, 0, 0)); _to(hg); attach(hg, holder); hg.location = (hu, -s * 0.0, 0)
            w_ = (u1 - u0) - 0.003
            x0, x1 = (0.0015, w_) if o['hinge'] == 'start' else (-w_, -0.0015)
            lf = block('door_leaf', x0, x1, -0.003, 0.003, 0.001, z1 - 0.001, M['door'], bevel=0.001); attach(lf, hg)
            for zz in (0.025, 0.11):
                pn = block('door_panel', x0 + 0.008, x1 - 0.008, s * 0.003, s * 0.0045, zz, zz + 0.06, M['door'], bevel=0.0012); attach(pn, hg)
            kx = x1 - 0.009 if o['hinge'] == 'start' else x0 + 0.009
            kn = sphere('door_knob', 0.0028, (0, 0, 0), mat=M['brass']); _to(kn); attach(kn, hg); kn.location = (kx, s * 0.006, 0.092)
            ang = o['angle']
            if HOUSE and not o.get('keep'): ang = math.copysign(165.0, ang or 1.0)      # swung right round, nearly flat to the wall
            hg.rotation_euler = (0, 0, math.radians(ang) * (1 if o['hinge'] == 'start' else -1) * s)
        if o.get('spill') and not HOUSE:                                    # light from the room behind the door
            sp = point_light('door_spill', (0, 0, 0), o['spill'][0], radius=0.02, color=o['spill'][1]); _to(sp, 'Lights')
            attach(sp, holder); sp.location = ((u0 + u1) / 2, -s * 0.05, 0.1)


def cladding(a, b, inward, height=0.12, mat='tiles_wall', skip=()):
    """tiles (or panelling) on the room side of a wall from the floor up to `height`, skipping door spans (u0, u1)"""
    a, b = Vector((*a, 0)), Vector((*b, 0)); t = (b - a).normalized(); L_ = (b - a).length
    holder = empty('cladding', tuple(a)); _to(holder); holder.rotation_euler = (0, 0, math.atan2(t.y, t.x))
    edges = [0.0] + sum([[u0, u1] for (u0, u1) in skip], []) + [L_]
    s_ = inward
    for i in range(0, len(edges), 2):
        if edges[i + 1] - edges[i] > 0.002:
            y0, y1 = sorted((s_ * WT / 2, s_ * (WT / 2 + 0.002)))
            ob = block('cladding', edges[i], edges[i + 1], y0, y1, 0.0, height, M[mat], bevel=0.0003); attach(ob, holder)
            y0, y1 = sorted((s_ * WT / 2, s_ * (WT / 2 + 0.004)))
            cap = block('cladding_cap', edges[i], edges[i + 1], y0, y1, height, height + 0.004, M[mat], bevel=0.0012); attach(cap, holder)
    return holder


def hollow(ob, inner):
    """cut inner out of ob (a basin, a tub) with a boolean, then drop the cutter"""
    md = ob.modifiers.new('hollow', 'BOOLEAN'); md.object = inner; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        if m.name == 'hollow': break
    bpy.ops.object.modifier_move_to_index(modifier='hollow', index=0)
    bpy.ops.object.modifier_apply(modifier='hollow')
    bpy.data.objects.remove(inner, do_unlink=True); return ob


def chair(x, y, facing=0.0, seat=0.032, mat='wood'):
    """a plain kitchen chair (spindle back), facing the given yaw in degrees (0 = facing -y)"""
    h = empty('chair', (x, y, 0)); _to(h); h.rotation_euler = (0, 0, math.radians(facing))
    parts = [('seat', -0.016, 0.016, -0.015, 0.017, seat - 0.004, seat)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(('leg', sx * 0.013 - 0.0018, sx * 0.013 + 0.0018, sy * 0.012 - 0.0018, sy * 0.012 + 0.0018, 0, seat - 0.003))
        parts.append(('back_post', sx * 0.014 - 0.0018, sx * 0.014 + 0.0018, 0.013, 0.017, seat, seat + 0.045))
    parts.append(('back_rail', -0.016, 0.016, 0.0125, 0.0175, seat + 0.038, seat + 0.046))
    for i in range(3): parts.append(('back_spindle', -0.006 + i * 0.006 - 0.0008, -0.006 + i * 0.006 + 0.0008, 0.014, 0.016, seat, seat + 0.04))
    for nm, a, b, c, d, e, f in parts:
        ob = block('chair_' + nm, a, b, c, d, e, f, M[mat], bevel=0.0007); attach(ob, h)
    h.rotation_euler.z += math.radians(RNG.uniform(-6, 6))
    return h


# ------------------------------------------------------------------ attic: roof, gables
def roof(x0, x1, y0, y1, z_eave, z_ridge, ridge_x=None, spacing=0.06):
    """a pitched roof along y: two planked slopes from the eaves (x0, x1) to the ridge, rafters every `spacing`,
    a ridge beam and a few collar ties; returns the ridge x"""
    rx = (x0 + x1) / 2 if ridge_x is None else ridge_x
    for xa in (x0, x1):
        dx, dz = rx - xa, z_ridge - z_eave; ln = math.hypot(dx, dz); ang = math.atan2(dz, dx)
        cx, cz = (xa + rx) / 2, (z_eave + z_ridge) / 2
        n = Vector((-math.sin(ang), 0, math.cos(ang))) * (1 if xa < rx else -1)   # outward normal of the slope
        sl = rounded_box('roof_slope', (ln + 0.01, y1 - y0 + 0.02, 0.006), (cx, (y0 + y1) / 2, cz), bevel=0.0005, mat=M['planks'])
        sl.rotation_euler = (0, -ang, 0); sl.location = Vector((cx, (y0 + y1) / 2, cz)) + n * 0.012; _to(sl)
        k = int((y1 - y0) / spacing)
        for i in range(k + 1):
            yy = y0 + (y1 - y0) * i / k
            r = rounded_box('rafter', (ln, 0.006, 0.012), (cx, yy, cz), bevel=0.001, mat=M['wood'])
            r.rotation_euler = (0, -ang, RNG.uniform(-0.01, 0.01)); r.location = Vector((cx, yy, cz)) + n * 0.003; _to(r)
    block('ridge_beam', rx - 0.005, rx + 0.005, y0, y1, z_ridge - 0.012, z_ridge + 0.004, M['wood'], bevel=0.001)
    zc = z_eave + (z_ridge - z_eave) * 0.62
    xc = (rx - x0) * 0.38
    for yy in (y0 + (y1 - y0) * 0.25, y0 + (y1 - y0) * 0.75):
        block('collar_tie', rx - xc, rx + xc, yy - 0.003, yy + 0.003, zc - 0.005, zc + 0.005, M['wood'], bevel=0.001, tilt=0.01)
    return rx


def gable(x0, x1, y, z0, z_eave, z_ridge, rx, inward=-1, round_window=None, moon=True):
    """the end wall under the roof (a pentagon of planks) with an optional round window (cx, cz, r)"""
    import bmesh
    bm = bmesh.new()
    pts = [(x0, z0), (x1, z0), (x1, z_eave), (rx, z_ridge), (x0, z_eave)]
    vs = [bm.verts.new((px, y, pz)) for px, pz in pts]; bm.faces.new(vs)
    me = bpy.data.meshes.new('gable'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('gable', me); bpy.context.collection.objects.link(ob); _to(ob)
    so = ob.modifiers.new('thick', 'SOLIDIFY'); so.thickness = WT; so.offset = 0
    ob.data.materials.append(M['planks'])
    if round_window:
        cx, cz, r = round_window
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.05, location=(cx, y, cz), rotation=(math.pi / 2, 0, 0), vertices=48)
        cut = bpy.context.object
        bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier='thick')
        hollow(ob, cut)
        bpy.ops.mesh.primitive_torus_add(major_radius=r + 0.003, minor_radius=0.004, location=(cx, y + inward * 0.004, cz),
                                         rotation=(math.pi / 2, 0, 0), major_segments=48, minor_segments=12)
        fr = bpy.context.object; fr.name = 'round_window_frame'; fr.data.materials.append(M['wood']); _to(fr)
        for rot in (0, math.pi / 2):
            bar = rounded_box('round_window_bar', (2 * r, 0.003, 0.003), (cx, y, cz), bevel=0.0008, mat=M['wood']); bar.rotation_euler = (0, rot, 0); _to(bar)
        sky = block('sky', cx - 0.12, cx + 0.12, y - inward * 0.3, y - inward * 0.29, cz - 0.12, cz + 0.12, M['sky'], bevel=0); sky.visible_shadow = False
        if moon:
            mn = sphere('moon', 0.02, (cx + 0.03, y - inward * 0.28, cz + 0.02), mat=M['moon']); _to(mn); mn.visible_shadow = False
    return ob


def draped(name, x0, x1, y0, y1, h, mat='sheet_cloth', lump=0.004, spread=0.012):
    """furniture hidden under a dust sheet: a soft lumpy shape whose hem spreads on the floor"""
    body = rounded_box(name, (x1 - x0, y1 - y0, h), ((x0 + x1) / 2, (y0 + y1) / 2, h / 2), bevel=min(0.01, h / 3), mat=M[mat]); _to(body)
    add_lumps(body, lump, size=0.02)
    hem = rounded_box(name + '_hem', (x1 - x0 + spread * 2, y1 - y0 + spread * 2, 0.004), ((x0 + x1) / 2, (y0 + y1) / 2, 0.002),
                      bevel=0.002, mat=M[mat]); _to(hem); add_lumps(hem, 0.0015, size=0.01)
    body['hem'] = hem.name
    return body


# ------------------------------------------------------------------ stairs
def stairs_down(x0, x1, y_top, y_dir, n=12, rise=0.018, run=0.025, mat='floor'):
    """a straight flight going down from floor level at y_top, stepping in y_dir (+1/-1); treads and risers, a
    stringer each side, carpet-runner strip down the middle"""
    for i in range(n):
        z = -rise * (i + 1)
        ya, yb = y_top + y_dir * run * i, y_top + y_dir * run * (i + 1)
        block('tread', x0, x1, min(ya, yb), max(ya, yb), z - 0.004, z, M[mat], bevel=0.0008, coll=True)
        block('riser', x0, x1, min(ya, ya + y_dir * 0.002), max(ya, ya + y_dir * 0.002), z, z + rise, M['trim'], bevel=0.0004)
        block('stair_runner', (x0 + x1) / 2 - 0.022, (x0 + x1) / 2 + 0.022, min(ya, yb) + 0.001, max(ya, yb) - 0.001, z, z + 0.0012,
              M['runner'], bevel=0.0004)
    yb = y_top + y_dir * run * n
    dy, dz = y_dir * run * n, -rise * n; ln = math.hypot(dy, dz); ang = math.atan2(dz, dy)
    for xx in (x0 - 0.002, x1 + 0.002):                                 # sloped side boards that follow the flight
        sg = rounded_box('stringer', (0.004, ln + 0.02, 0.03), (xx, y_top + dy / 2, dz / 2 - 0.012), bevel=0.001, mat=M['wood'])
        sg.rotation_euler = (ang, 0, 0); _to(sg)                           # its long side along the slope


def banister(x, y0, y1, h=0.09, n=12):
    """a banister along y at x (see rail)"""
    return rail((x, y0), (x, y1), h, n)


def rail(p0, p1, h=0.09, n=None):
    """a banister from p0 to p1 (xy): newel posts at both ends, spindles between, a handrail (a little out of true)"""
    a, b = Vector((*p0, 0)), Vector((*p1, 0)); d = b - a; L_ = d.length; n = n or max(3, int(L_ / 0.025))
    holder = empty('rail', tuple(a)); _to(holder); holder.rotation_euler = (0, 0, math.atan2(d.y, d.x))
    for u in (0.0, L_):
        attach(block('newel_post', u - 0.005, u + 0.005, -0.005, 0.005, 0, h + 0.012, M['wood'], bevel=0.0015), holder)
        cap = sphere('newel_cap', 0.006, (u, 0, h + 0.016), mat=M['wood']); _to(cap); attach(cap, holder)
    for i in range(1, n):
        u = L_ * i / n
        attach(block('spindle', u - 0.0015, u + 0.0015, -0.0015, 0.0015, 0, h, M['wood'], bevel=0.0006, tilt=0.03), holder)
    attach(block('handrail', 0, L_, -0.004, 0.004, h, h + 0.006, M['wood'], bevel=0.002, tilt=0.004), holder)
    return holder


# ------------------------------------------------------------------ dressing
def picture(loc, size=(0.03, 0.04), normal=(1, 0, 0), crooked=4.0, mat='photo'):
    """a framed photo hung on a wall: loc is the centre on the wall surface, normal points into the room"""
    nrm = Vector(normal).normalized(); w, hh = size
    holder = empty('picture', loc); _to(holder)
    holder.rotation_euler = (0, 0, math.atan2(nrm.y, nrm.x) - math.pi / 2)
    fr = block('picture_frame', -w / 2, w / 2, 0.0, 0.003, -hh / 2, hh / 2, M['wood'], bevel=0.001); attach(fr, holder)
    ph = block('picture_photo', -w / 2 + 0.004, w / 2 - 0.004, 0.003, 0.0034, -hh / 2 + 0.004, hh / 2 - 0.004, M[mat], bevel=0.0002)
    attach(ph, holder)
    holder.rotation_euler.y = math.radians(RNG.uniform(-crooked, crooked))
    return holder


def radiator(loc, width=0.06, normal=(0, -1, 0)):
    nrm = Vector(normal).normalized(); holder = empty('radiator', loc); _to(holder)
    holder.rotation_euler = (0, 0, math.atan2(nrm.y, nrm.x) - math.pi / 2)
    k = int(width / 0.006)
    for i in range(k):
        x = -width / 2 + (i + 0.5) * width / k
        f = block('radiator_fin', x - 0.0022, x + 0.0022, 0.004, 0.012, 0.012, 0.055, M['metal'], bevel=0.0015); attach(f, holder)
    for zz in (0.014, 0.052):
        p = block('radiator_pipe', -width / 2, width / 2, 0.006, 0.01, zz - 0.002, zz + 0.002, M['metal'], bevel=0.001); attach(p, holder)
    return holder


def runner(x0, x1, y0, y1, z=0.0):
    r = block('runner_rug', x0, x1, y0, y1, z, z + 0.0015, M['runner'], bevel=0.0006, coll=True)
    add_lumps(r, 0.0006, size=0.02); return r


def sconce(loc, normal=(1, 0, 0), energy=0.5):
    """a small wall lamp with a warm fabric shade and a real light"""
    nrm = Vector(normal).normalized(); p = Vector(loc)
    block('sconce_back', p.x - 0.004, p.x + 0.004, p.y - 0.004, p.y + 0.004, p.z - 0.008, p.z + 0.004, M['brass'], bevel=0.001)
    sh = cylinder('sconce_shade', 0.009, 0.012, tuple(p + nrm * 0.012 + Vector((0, 0, 0.004))), mat=M['shade']); _to(sh)
    lt = point_light('sconce_light', tuple(p + nrm * 0.014), energy, radius=0.006, color=(1.0, 0.66, 0.36)); _to(lt, 'Lights')
    return lt, sh


# ------------------------------------------------------------------ lighting and camera marks
def mood(kind, moon_from=None, moon_to=None, haze=True, bounds=None, moon_energy=26, haze_density=0.9):
    """lighting presets. night: one cold moon key through a window (+ thin haze), cold rim, faint cold fill; the
    practicals (sconces, door spills) stay as built"""
    sc = bpy.context.scene
    if kind == 'night':
        if moon_from:
            m = area_light('moonlight', moon_from, moon_to, moon_energy, 0.05, (0.55, 0.68, 1.0)); _to(m, 'Lights')
        if HOUSE: return sc                                                 # the house sets one fill and one haze
        f = area_light('fill_cold', (0, -0.4, 0.15), (0, 0.2, 0.08), 0.25, 0.4, (0.5, 0.6, 0.9)); _to(f, 'Lights')
        if haze and bounds:
            hz = bpy.data.materials.new('haze'); hz.use_nodes = True; hn = hz.node_tree.nodes
            hn.remove(hn['Principled BSDF']); pv = hn.new('ShaderNodeVolumePrincipled')
            pv.inputs['Density'].default_value = haze_density; pv.inputs['Anisotropy'].default_value = 0.55
            hz.node_tree.links.new(pv.outputs[0], hn['Material Output'].inputs['Volume'])
            x0, y0, z0, x1, y1, z1 = bounds
            bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
            ob = bpy.context.object; ob.name = 'haze'; ob.scale = (x1 - x0, y1 - y0, z1 - z0); ob.data.materials.append(hz); _to(ob)
            sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4.0
    elif kind == 'day':
        world((0.6, 0.62, 0.65), 0.6)
    return sc


def mark(name, loc, target, lens=28):
    """a named camera mark saved with the room (an empty that looks at the target, lens stored as a property)"""
    e = empty('cam_' + name, loc); _to(e, 'Marks')
    look_at(e, target); e['lens'] = lens; e['target'] = list(target)
    return e


def shoot(name, out, fstop=5.6):
    """render one still from a camera mark"""
    e = bpy.data.objects['cam_' + name]; sc = bpy.context.scene
    cam = sc.camera or camera((0, 0, 0), (0, 1, 0))
    cam.location = e.location; cam.rotation_euler = e.rotation_euler; cam.data.lens = e['lens']
    cam.data.clip_start = 0.002
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop
    cam.data.dof.focus_distance = (Vector(e['target']) - e.location).length
    sc.camera = cam; sc.render.filepath = os.path.join(out, name + '.png'); bpy.ops.render.render(write_still=True)
