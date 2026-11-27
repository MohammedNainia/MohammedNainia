"""Windows and doors with working parts, for every set (1:10 scale, metres). Most of our scares happen at these.

They plug into the room kit: give an opening rig=True and it is built from here instead of the plain static version,
and the built object comes back on the opening dict:

    import kit as K
    w = K.window(0.22, 0.38, 0.075, 0.2, rig=True, curtains='thin', outside='streetlamp')
    d = K.door(0.25, 0.33, rig=True, beyond='lit', color='white')
    K.wall((x0, y0), (x1, y1), openings=[w, d], inward=-1)
    W, D = w['obj'], d['obj']
    W.close(f, 0.0..1.0)      # curtains: 0 open, 1 closed (the edges meet just past the middle)
    W.blind(f, 0.0..1.0)      # roller blind: 0 up, 1 down
    W.open(f, 0.0..1.0)       # sash window: the lower sash slides up
    W.lamp(f, energy)         # the streetlamp outside (outside='streetlamp')
    D.swing(f, deg)           # 0 shut, + opens into the room
    D.turn(f, 0.0..1.0)       # the handle turns down
    D.light(f, energy)        # the light in the room behind it (beyond='lit')

Every setter keys the frame it is given (f=None just sets the pose). Coordinates are the wall's own frame:
x = u along the wall, y = across it (side = +1 or -1 is the room side), z up, the same as kit.wall().
Looks follow refs/props/window_curtains.jpg, door_ajar.jpg and moods/mood_streetlamp_window.jpg.
"""
import bpy, bmesh, math
from mathutils import Vector
import kit as K
import burton_materials as BM
from claylib import emissive, sphere, cylinder, empty, point_light

WT = K.WT


# ------------------------------------------------------------------ materials
def _mat(name):
    m = bpy.data.materials.get(name)
    if m: return m, None
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree


def glass():
    """window glass that light and shadows pass through (a streetlamp spot works through it), with a faint sheen"""
    m, nt = _mat('window_glass')
    if nt is None: return m
    N, L = nt.nodes, nt.links; N.remove(N['Principled BSDF'])
    tr = N.new('ShaderNodeBsdfTransparent'); gl = N.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.06
    lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.15
    mx = N.new('ShaderNodeMixShader')
    L.new(lw.outputs['Fresnel'], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], N['Material Output'].inputs['Surface'])
    return m


def thin_cloth(name='curtain_thin', color=(0.5, 0.4, 0.27), glow=(0.95, 0.8, 0.55), through=0.55):
    """thin cloth a light behind shines through (shadows outside show on it): The Garden's curtains"""
    m, nt = _mat(name)
    if nt is None: return m
    N, L = nt.nodes, nt.links; pb = N['Principled BSDF']
    pb.inputs['Base Color'].default_value = (*color, 1); pb.inputs['Roughness'].default_value = 0.95
    tr = N.new('ShaderNodeBsdfTranslucent'); tr.inputs['Color'].default_value = (*glow, 1)
    mx = N.new('ShaderNodeMixShader'); mx.inputs[0].default_value = through
    L.new(pb.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N['Material Output'].inputs['Surface'])
    return m


DOOR_COLORS = {'white': (0.62, 0.6, 0.55), 'dark': (0.32, 0.3, 0.25), 'green': (0.17, 0.25, 0.19), 'red': (0.36, 0.08, 0.06)}


def _door_paint(color):
    if color in (None, 'default'): return K.M['door']
    c = DOOR_COLORS.get(color, color)
    return K.painted(f'door_paint_{color}' if isinstance(color, str) else 'door_paint_custom', c)


def _key(ob, f, *paths):
    if f is None: return
    for p in paths: ob.keyframe_insert(p, frame=f)


def _part(par, name, x0, x1, y0, y1, z0, z1, mat, bevel=0.0008):
    return K.attach(K.block(name, x0, x1, y0, y1, z0, z1, mat, bevel=bevel), par)


def _aim_local(ob, target):
    d = Vector(target) - Vector(ob.location)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def _frame(holder, u0, u1, z0, z1, s, window):
    f = 0.007; y0, y1 = sorted((s * (WT / 2 - 0.012), s * (WT / 2 + 0.003)))
    parts = [(u0 - f, u0, z0, z1 + f), (u1, u1 + f, z0, z1 + f), (u0, u1, z1, z1 + f)]
    if window: parts.append((u0, u1, z0 - f, z0))
    for (p0, p1, q0, q1) in parts: _part(holder, 'frame', p0, p1, y0, y1, q0, q1, K.M['trim'], bevel=0.0009)


# ------------------------------------------------------------------ doors
class Door:
    """A panelled door on a hinge: four raised panels on both faces, a brass lever handle that turns, a keyhole plate,
    hinge knuckles, an optional peephole and letterbox (front doors). Behind it: darkness ('dark'), a lit room with a
    warm spill that falls across the floor when it opens ('lit'), or nothing (the next room is really there)."""

    def __init__(self, holder, u0, u1, h=K.DOOR_H, side=1, hinge='start', color='white', handle='lever',
                 peephole=False, letterbox=False, beyond='dark', spill=(0.6, (1.0, 0.62, 0.32)), frame=True,
                 undercut=0.001):
        s = self.s = side; self.hinge = hinge; self.sg = 1 if hinge == 'start' else -1
        self.holder = holder; self.u0, self.u1, self.h = u0, u1, h
        if frame: _frame(holder, u0, u1, 0.0, h, s, False)
        paint = _door_paint(color)
        hu = u0 if hinge == 'start' else u1
        hg = self.hg = empty('door_hinge', (0, 0, 0)); K._to(hg); K.attach(hg, holder); hg.location = (hu, 0, 0)
        w = (u1 - u0) - 0.003; T = 0.0022                                  # leaf width; half thickness (4.4 cm)
        x0, x1 = (0.0015, w) if hinge == 'start' else (-w, -0.0015)
        self.leaf = _part(hg, 'door_leaf', x0, x1, -T, T, undercut, h - 0.001, paint, bevel=0.0009)   # undercut: the gap light shows under
        st = 0.008; mid = (x0 + x1) / 2; k = h / 0.2                       # stiles and rails; panel rows scale with height
        rows = ((0.022 * k, 0.088 * k), (0.104 * k, 0.186 * k))
        for ss in (1, -1):                                                 # raised panels on both faces
            for (q0, q1) in rows:
                for (p0, p1) in ((x0 + st, mid - st / 2), (mid + st / 2, x1 - st)):
                    _part(hg, 'door_panel', p0 + 0.002, p1 - 0.002, *sorted((ss * T, ss * (T + 0.0012))), q0 + 0.002, q1 - 0.002, paint, bevel=0.0009)
        ex = x1 - 0.008 if hinge == 'start' else x0 + 0.008                # handle side edge
        hz = 0.092 * k; self.handles = []
        for ss in (1, -1):
            pv = empty('door_handle', (0, 0, 0)); K._to(pv); K.attach(pv, hg); pv.location = (ex, ss * (T + 0.0012), hz)
            rose = cylinder('handle_rose', 0.0034, 0.0016, (0, ss * 0.0008, 0), verts=24, mat=K.M['brass'], rot=(math.pi / 2, 0, 0))
            K._to(rose); K.attach(rose, pv)
            if handle == 'lever':
                d = -self.sg                                               # the lever points back toward the hinge
                _part(pv, 'handle_lever', min(0, d * 0.013), max(0, d * 0.013), *sorted((ss * 0.0016, ss * 0.0034)), -0.0011, 0.0011,
                      K.M['brass'], bevel=0.0007)
            else:
                kn = sphere('handle_knob', 0.0028, (0, ss * 0.004, 0), mat=K.M['brass']); K._to(kn); K.attach(kn, pv)
            _part(hg, 'keyhole_plate', ex - 0.0016, ex + 0.0016, *sorted((ss * (T + 0.0012), ss * (T + 0.0018))), hz - 0.012, hz - 0.006,
                  K.M['brass'], bevel=0.0004)
            self.handles.append((pv, ss))
        hx = 0.0 if hinge == 'start' else 0.0
        for zz in (0.03 * k, 0.165 * k):                                   # hinge knuckles on the hinge edge
            kn = cylinder('hinge_knuckle', 0.0015, 0.012, (hx, -s * 0.0024, zz), verts=12, mat=K.M['brass']); K._to(kn); K.attach(kn, hg)
        if peephole:
            pp = cylinder('peephole', 0.0012, 0.0062, (mid, 0, 0.152 * k), verts=16, mat=K.M['brass'], rot=(math.pi / 2, 0, 0))
            K._to(pp); K.attach(pp, hg)
        if letterbox:
            for ss in (1, -1):
                _part(hg, 'letterbox', mid - 0.013, mid + 0.013, *sorted((ss * (T + 0.0012), ss * (T + 0.0022))), 0.075 * k, 0.083 * k,
                      K.M['brass'], bevel=0.0005)
        self.spill = None
        if beyond in ('dark', 'lit'):
            mat = K.M['beyond'] if beyond == 'lit' else K.M['void']
            _part(holder, 'doorway_beyond', u0 - 0.05, u1 + 0.05, *sorted((-s * 0.06, -s * 0.07)), -0.01, h + 0.05, mat, bevel=0)
            for (p0, p1) in ((u0 - 0.05, u0 - 0.04), (u1 + 0.04, u1 + 0.05)):
                _part(holder, 'doorway_side', p0, p1, *sorted((0.0, -s * 0.07)), -0.01, h + 0.05, mat, bevel=0)
            if beyond == 'lit':                                            # the floor of that room, so its light has somewhere to land
                _part(holder, 'doorway_floor', u0 - 0.05, u1 + 0.05, *sorted((-s * WT / 2, -s * 0.07)), -0.01, 0.0, K.M['floor'], bevel=0)
                sp = self.spill = point_light('door_spill', (0, 0, 0), spill[0], radius=0.015, color=spill[1]); K._to(sp, 'Lights')
                K.attach(sp, holder); sp.location = ((u0 + u1) / 2, -s * 0.045, 0.16 * k)
        self.swing(None, 0.0)

    def swing(self, f, deg):
        self.hg.rotation_euler = (0, 0, math.radians(deg) * self.sg * self.s); _key(self.hg, f, 'rotation_euler')

    def turn(self, f, amount):
        """amount 0..1: the lever pushed down 40 degrees (on both sides of the door)"""
        for pv, ss in self.handles:
            pv.rotation_euler = (0, math.radians(40) * amount * self.sg * ss, 0); _key(pv, f, 'rotation_euler')

    def light(self, f, energy):
        if self.spill is None: return
        self.spill.data.energy = energy
        if f is not None: self.spill.data.keyframe_insert('energy', frame=f)


# ------------------------------------------------------------------ windows
def _curtain_mesh(name, width, z0, z1, sign, depth, period):
    """a hanging panel of soft vertical folds along x (grows by sign), origin at its fixed outer edge"""
    bm = bmesh.new(); nx, nz = 56, 10; rows = []
    for i in range(nx + 1):
        u = i / nx; xx = sign * u * width; yy = depth * math.sin(u * width * 2 * math.pi / period)
        rows.append([bm.verts.new((xx, yy, z0 + (z1 - z0) * k / nz - 0.0015 * math.sin(u * 9.0) * (k == 0))) for k in range(nz + 1)])
    for i in range(nx):
        for k in range(nz):
            q = (rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1]); bm.faces.new(q if sign > 0 else q[::-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); K._to(ob)
    sol = ob.modifiers.new('cloth', 'SOLIDIFY'); sol.thickness = 0.0007
    return ob


class Window:
    """A window: frame, sill, glazing bars and real glass; optional lower sash that slides up; curtains on a rod
    ('thin' cream cloth a streetlamp shines through, so shadows outside land on it, or 'heavy' patterned fabric that
    blocks it); an optional roller blind; and the night outside ('streetlamp', 'moon', 'dark' or None)."""

    def __init__(self, holder, u0, u1, z0, z1, side=1, bars=(1, 1), sash=False, curtains='thin', curtain_color='#2f3a5a',
                 blind=False, outside='streetlamp', lamp_energy=200.0, frame=True):
        s = self.s = side; self.holder = holder; self.u0, self.u1, self.z0, self.z1 = u0, u1, z0, z1
        um, zm = (u0 + u1) / 2, (z0 + z1) / 2; self.um, self.zm = um, zm
        if frame:
            _frame(holder, u0, u1, z0, z1, s, True)
            _part(holder, 'sill', u0 - 0.012, u1 + 0.012, *sorted((s * WT / 2, s * (WT / 2 + 0.014))), z0 - 0.009, z0 - 0.005,
                  K.M['trim'], bevel=0.001)
        G = glass(); trim = K.M['trim']
        def glazing(par, q0, q1, y, nv, nh):
            _part(par, 'glass', u0, u1, y - 0.0003, y + 0.0003, q0, q1, G, bevel=0)
            for i in range(1, nv + 1):
                x = u0 + (u1 - u0) * i / (nv + 1); _part(par, 'glazing_bar', x - 0.0017, x + 0.0017, y - 0.0016, y + 0.0016, q0, q1, trim, bevel=0.0005)
            for i in range(1, nh + 1):
                z = q0 + (q1 - q0) * i / (nh + 1); _part(par, 'glazing_bar', u0, u1, y - 0.0016, y + 0.0016, z - 0.0017, z + 0.0017, trim, bevel=0.0005)
        self.sash = None
        if sash:                                                           # upper sash fixed outside, lower one slides up inside it
            glazing(holder, zm, z1, -s * 0.0018, bars[0], 0)
            sh = self.sash = empty('sash', (0, 0, 0)); K._to(sh); K.attach(sh, holder)
            glazing(sh, z0, zm, s * 0.0018, bars[0], 0)
            _part(sh, 'meeting_rail', u0, u1, *sorted((s * 0.0002, s * 0.0034)), zm - 0.0035, zm + 0.0005, trim, bevel=0.0005)
            for p0, p1 in ((u0, u0 + 0.003), (u1 - 0.003, u1)):
                _part(sh, 'sash_stile', p0, p1, *sorted((s * 0.0002, s * 0.0034)), z0, zm, trim, bevel=0.0004)
            _part(sh, 'sash_lift', um - 0.004, um + 0.004, *sorted((s * 0.0034, s * 0.0055)), z0 + 0.003, z0 + 0.0045, K.M['brass'], bevel=0.0004)
        else:
            glazing(holder, z0, z1, 0.0, *bars)
        self.cur = []
        if curtains:
            ry = s * (WT / 2 + 0.014)
            _part(holder, 'curtain_rod', u0 - 0.032, u1 + 0.032, *sorted((ry - s * 0.0018, ry + s * 0.0018)), z1 + 0.015, z1 + 0.0186,
                  K.M['wood'], bevel=0.0012)
            for ux in (u0 - 0.034, u1 + 0.034):
                fin = sphere('rod_finial', 0.0032, (ux, ry, z1 + 0.0168), mat=K.M['wood']); K._to(fin); K.attach(fin, holder)
            heavy = curtains == 'heavy'
            mat = (BM.fabric(f'curtain_heavy_{curtain_color}', curtain_color, 'weave', fuzz=0.6, scale=900, dark=0.7)
                   if heavy else thin_cloth())
            self.CW = (u1 - u0) / 2 + 0.018
            cz0 = z0 - (0.045 if heavy else 0.012); cz1 = z1 + 0.014
            self.anc = (u0 - 0.016, u1 + 0.016); self.open_edge = (u0 + 0.01, u1 - 0.01)
            for k, sign in ((0, 1), (1, -1)):
                c = _curtain_mesh(f'curtain_{"ab"[k]}', self.CW, cz0, cz1, sign, 0.003 if heavy else 0.0022, 0.013 if heavy else 0.011)
                c.data.materials.append(mat); K.attach(c, holder); c.location = (self.anc[k], s * (WT / 2 + 0.009), 0)
                self.cur.append(c)
            self.close(None, 0.0)
        self.bl = None
        if blind:
            by = s * (WT / 2 - 0.0015)
            tube = cylinder('blind_roller', 0.0028, (u1 - u0) + 0.004, (um, by, z1 - 0.003), verts=16, mat=trim, rot=(0, math.pi / 2, 0))
            K._to(tube); K.attach(tube, holder)
            bl = self.bl = empty('blind', (0, 0, 0)); K._to(bl); K.attach(bl, holder); bl.location = (0, 0, z1 - 0.004)
            sheet = thin_cloth('blind_cloth', (0.55, 0.52, 0.45), (0.9, 0.85, 0.7), 0.4)
            _part(bl, 'blind_sheet', u0 + 0.001, u1 - 0.001, by - 0.0003, by + 0.0003, -(z1 - z0) + 0.004, 0, sheet, bevel=0)
            _part(bl, 'blind_bar', u0 + 0.001, u1 - 0.001, by - 0.0009, by + 0.0009, -(z1 - z0) + 0.003, -(z1 - z0) + 0.0052, trim, bevel=0.0004)
            self.blind(None, 0.0)
        self.lamp_ob = None
        if outside == 'streetlamp':
            bd = _part(holder, 'night_backdrop', u0 - 0.9, u1 + 0.9, *sorted((-s * 0.85, -s * 0.86)), z0 - 0.6, z1 + 0.6,
                       emissive('night_far', (0.04, 0.06, 0.16), 0.15), bevel=0); bd.visible_shadow = False
            ld = bpy.data.lights.new('streetlamp', 'SPOT'); ld.energy = lamp_energy; ld.spot_size = math.radians(34)
            ld.spot_blend = 0.25; ld.shadow_soft_size = 0.002; ld.color = (0.72, 0.82, 1.0)
            lo = self.lamp_ob = bpy.data.objects.new('streetlamp', ld); bpy.context.collection.objects.link(lo); K._to(lo, 'Lights')
            K.attach(lo, holder); lo.location = (um, -s * 0.7, zm - 0.005); _aim_local(lo, (um, 0, zm))
            bu = sphere('street_bulb', 0.008, (um + 0.012, -s * 0.71, zm - 0.005), mat=emissive('street_bulb', (0.8, 0.88, 1.0), 25.0))
            K._to(bu); K.attach(bu, holder); bu.visible_shadow = False
        elif outside == 'moon':
            sk = _part(holder, 'sky', u0 - 0.05, u1 + 0.05, *sorted((-s * 0.045, -s * 0.04)), z0 - 0.05, z1 + 0.05, K.M['sky'], bevel=0)
            sk.visible_shadow = False
            mn = sphere('moon', 0.006, (um - 0.008, -s * 0.038, zm + 0.01), mat=K.M['moon']); K._to(mn); K.attach(mn, holder); mn.visible_shadow = False
        elif outside == 'dark':
            _part(holder, 'outside_dark', u0 - 0.05, u1 + 0.05, *sorted((-s * 0.045, -s * 0.04)), z0 - 0.05, z1 + 0.05, K.M['void'], bevel=0)

    def close(self, f, amount):
        """curtains: 0 open (bunched at the sides), 1 closed (the edges overlap just past the middle)"""
        if not self.cur: return
        a, b = self.anc; oa, ob = self.open_edge
        ea = oa + (self.um + 0.003 - oa) * amount; eb = ob + (self.um - 0.003 - ob) * amount
        for c, span in ((self.cur[0], ea - a), (self.cur[1], b - eb)):
            k = span / self.CW
            c.scale = (k, min(2.4, 1 / math.sqrt(max(k, 0.05))), 1)        # bunched cloth folds deeper
            _key(c, f, 'scale')

    def blind(self, f, down):
        if self.bl is None: return
        self.bl.scale = (1, 1, max(0.03, down)); _key(self.bl, f, 'scale')

    def open(self, f, amount):
        if self.sash is None: return
        self.sash.location = (0, 0, amount * (self.zm - self.z0) * 0.92); _key(self.sash, f, 'location')

    def lamp(self, f, energy):
        if self.lamp_ob is None: return
        self.lamp_ob.data.energy = energy
        if f is not None: self.lamp_ob.data.keyframe_insert('energy', frame=f)
