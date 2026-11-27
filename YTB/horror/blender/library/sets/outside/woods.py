"""The woods kit (1:10, metres): a forest clearing for night and dawn, dome tents with a zip that opens, a campfire,
a hand torch, and the Sector B13 fence with its gate and warning sign. Built for "Sector B13 · File 01" and kept for
every later woods story.

    import woods as W
    W.ground(); W.trees()                        # the clearing (radius about 6 m) ringed by pines
    fire = W.Campfire(0, 0)                      # fire.burn(f0, f1); fire.level(f, 0.25) = embers
    t = W.Tent('tent_haru', x, y, yaw, 'green')  # t.zip(f, 0..1) opens the door slit from the bottom; t.h = holder
    torch = W.Torch(x, y, z, yaw, pitch)         # a small hand torch; parent torch.h to a hand; torch.on()/off()
    fence = W.Fence(y=0.8)                       # chain link, posts, barbed top; fence.gate(f, deg); fence.sign_at
    W.mood('night') / W.mood('dawn')             # sky, moon or low dawn light, mist

The clearing is centred on the origin, the fire at (0, 0). North (+y) leads through the trees to the fence.
"""
import bpy, math, os, random
from mathutils import Vector, Matrix
import kit as K
import practicals as PL
import haru_puppet as HP
from claylib import sphere, cylinder, empty, point_light, area_light, emissive, world

HERE = os.path.dirname(os.path.abspath(__file__))
R = random.Random(8)
M = {}


def piece(name, s, mat, voxel=0.0012, smooth=3, lump=0.0):
    """an organic clay shape authored in metres (HP.piece works at puppet scale, so undo its x0.1)"""
    ob = HP.piece(name, s, mat, 'top', bpy.data.collections['Set'], voxel=voxel, smooth=smooth, lump=0)
    ob.data.transform(Matrix.Scale(1 / HP.S, 4))
    if lump: HP.CV.geometry(ob, dents=lump * 4, pits=lump * 0.7, lumps=lump * 0.7)   # thumb dents sized for this piece
    return ob


def _image_mat(name, path, rough=0.6, alpha=False, color=None, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; N, L = m.node_tree.nodes, m.node_tree.links
    pb = N['Principled BSDF']; tx = N.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(path, check_existing=True)
    pb.inputs['Roughness'].default_value = rough; pb.inputs['Metallic'].default_value = metal
    if color: pb.inputs['Base Color'].default_value = (*color, 1)
    else: L.new(tx.outputs['Color'], pb.inputs['Base Color'])
    if alpha:
        L.new(tx.outputs['Alpha'], pb.inputs['Alpha'])
        try: m.blend_method = 'HASHED'
        except Exception: pass
    return m, tx


def materials():
    sc = lambda name, scan, size, col, **kw: K.scanned(name, scan, size, col, fallback=K.painted(name + '_plain', col, rough=0.95), **kw)
    M['earth'] = sc('forest_earth', 'dirt_rocks', 0.35, (0.05, 0.04, 0.03), rough=0.95, bump=0.5)
    M['grass'] = sc('forest_grass', 'grass', 0.3, (0.035, 0.05, 0.025), rough=0.9, bump=0.4)
    M['tuft'] = HP.CV.clay('grass_tuft', '#3a4a26', rough=0.85, bump=0.4)
    M['bark'] = HP.CV.clay('bark', '#2e2219', rough=0.9, bump=1.0, prints=0.3)
    M['pine'] = HP.CV.clay('pine_needles', '#1d2a1c', rough=0.9, bump=0.8)
    M['rock'] = HP.CV.clay('rock', '#5b5852', rough=0.85, bump=0.8)
    M['log'] = HP.CV.clay('log', '#4a3423', rough=0.85, bump=0.9)
    M['log_end'] = HP.CV.clay('log_end', '#9a7a55', rough=0.8, bump=0.5)
    M['char'] = HP.CV.clay('charcoal', '#141110', rough=0.9, bump=0.6)
    M['leaf'] = HP.CV.clay('dead_leaf', '#5a3a1e', rough=0.85, bump=0.3)
    M['pole'] = K.painted('tent_pole', (0.08, 0.08, 0.085), rough=0.35)
    M['post'] = K.painted('fence_post', (0.16, 0.14, 0.12), rough=0.55)
    M['rust'] = K.painted('rust', (0.2, 0.08, 0.035), rough=0.8)
    M['wire'], _ = _image_mat('chainlink', os.path.join(HERE, 'chainlink.png'), rough=0.45, alpha=True, color=(0.32, 0.31, 0.29), metal=0.6)
    M['sign'], _ = _image_mat('sign_b13', os.path.join(HERE, 'sign_b13.png'), rough=0.55)
    return M


TENT_COLORS = {'green': ((0.12, 0.22, 0.12), (0.5, 0.75, 0.35)), 'red': ((0.38, 0.06, 0.05), (1.0, 0.35, 0.2)),
               'blue': ((0.06, 0.12, 0.3), (0.35, 0.55, 1.0)), 'orange': ((0.55, 0.2, 0.04), (1.0, 0.6, 0.25))}


def tent_cloth(name, color, glow, through=0.45):
    """nylon: a light inside makes the whole tent glow its colour and shapes outside show as silhouettes"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N, L = m.node_tree.nodes, m.node_tree.links
    pb = N['Principled BSDF']; pb.inputs['Base Color'].default_value = (*color, 1); pb.inputs['Roughness'].default_value = 0.55
    tr = N.new('ShaderNodeBsdfTranslucent'); tr.inputs['Color'].default_value = (*glow, 1)
    mx = N.new('ShaderNodeMixShader'); mx.inputs[0].default_value = through
    L.new(pb.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N['Material Output'].inputs['Surface'])
    return m


# ------------------------------------------------------------------ the clearing
def ground(radius=4.0, clearing=0.55, tufts=420, seed=4):
    """an earth disc with a trodden bare middle, grass tufts thickening toward the trees, dead leaves and twigs"""
    if not M: materials()
    bpy.ops.mesh.primitive_circle_add(vertices=96, radius=radius, fill_type='NGON'); g = bpy.context.object; g.name = 'forest_floor'
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=70); bpy.ops.object.mode_set(mode='OBJECT')
    r = random.Random(seed)
    for v in g.data.vertices:                                           # gentle rolls, a slight dip at the fire
        x, y = v.co.x, v.co.y; d = math.hypot(x, y)
        v.co.z = 0.004 * math.sin(x * 9 + 1.3) * math.sin(y * 7) + 0.003 * math.sin(x * 23 + y * 17) - 0.004 * math.exp(-(d / 0.08) ** 2)
        v.co.z *= min(1.0, d / 0.12)
    g.data.materials.append(M['earth']); g.data.materials.append(M['grass'])
    for p in g.data.polygons:
        c = p.center; d = math.hypot(c.x, c.y) + 0.06 * math.sin(c.x * 11) * math.cos(c.y * 9)
        p.material_index = 1 if d > clearing * 0.75 and r.random() < min(1.0, (d - clearing * 0.75) / 0.25) else 0
        p.use_smooth = True
    K._to(g); HP.colliders().objects.link(g)
    protos = []                                                         # a few tuft shapes, linked many times
    for k in range(4):
        s = HP.Shape()
        for i in range(9):
            a = r.uniform(0, 6.28); l = r.uniform(0.008, 0.018); lean = r.uniform(0.2, 0.6)
            tip = Vector((math.cos(a) * lean * l, math.sin(a) * lean * l, l))
            s.capsule((r.uniform(-0.002, 0.002), r.uniform(-0.002, 0.002), 0), tip, 0.0011, 0.0003, 8)
        protos.append(piece(f'tuft_{k}', s, M['tuft'], voxel=0.0005, smooth=1))
    for i in range(tufts):
        d = clearing * 0.6 + abs(r.gauss(0, 0.45)); a = r.uniform(0, 6.28)
        if d > 1.8 or (d < clearing * 0.9 and r.random() < 0.7): continue
        t = protos[i % 4].copy(); bpy.data.collections['Set'].objects.link(t)
        t.location = (math.cos(a) * d, math.sin(a) * d, -0.001); t.rotation_euler = (0, 0, r.uniform(0, 6.28))
        sc_ = r.uniform(0.7, 1.4); t.scale = (sc_, sc_, sc_ * r.uniform(0.8, 1.3))
    for p in protos: p.hide_render = p.hide_viewport = True
    lp = piece('leaf_proto', HP.Shape().ellipsoid((0, 0, 0.0004), (0.004, 0.0024, 0.0005)), M['leaf'], voxel=0.0004, smooth=1)
    for i in range(160):
        d = r.uniform(0.1, min(radius, 1.6)); a = r.uniform(0, 6.28)
        lf = lp.copy(); bpy.data.collections['Set'].objects.link(lf)
        lf.location = (math.cos(a) * d, math.sin(a) * d, 0.0); lf.rotation_euler = (r.uniform(-0.3, 0.3), r.uniform(-0.3, 0.3), r.uniform(0, 6.28))
        lf.scale = (r.uniform(0.7, 1.3),) * 3
    lp.hide_render = lp.hide_viewport = True
    return g


def trees(r_in=0.62, r_out=3.6, n=120, seed=9, path=(-0.09, 0.09)):
    """pines round the clearing: tall dark trunks (the canopy is above every shot), a few dead low branches.
    path: an x range kept clear north of the clearing, the trail to the fence"""
    if not M: materials()
    r = random.Random(seed); out = []
    protos = []
    for k in range(3):
        s = HP.Shape(); h = 1.0; z = 0.0; x = y = 0.0; rad = 0.02 + 0.006 * k
        for i in range(6):                                              # a slightly wandering trunk, wider at the foot
            nx, ny = x + r.uniform(-0.006, 0.006), y + r.uniform(-0.006, 0.006)
            s.capsule((x, y, z), (nx, ny, z + h / 6), rad * (1 - 0.12 * i) * (1.35 if i == 0 else 1), rad * (1 - 0.12 * (i + 1)), 14)
            x, y, z = nx, ny, z + h / 6
        for a in (0.0, 2.1, 4.2):                                       # root flare
            s.capsule((0, 0, 0.012), (math.cos(a + k) * rad * 2.2, math.sin(a + k) * rad * 2.2, -0.002), rad * 0.5, rad * 0.25, 10)
        for i in range(4):                                              # dead stubs of lower branches
            zz = r.uniform(0.18, 0.5); a = r.uniform(0, 6.28); L_ = r.uniform(0.03, 0.07)
            s.capsule((0, 0, zz), (math.cos(a) * L_, math.sin(a) * L_, zz - L_ * 0.3), 0.0025, 0.0008, 8)
        tr = piece(f'trunk_{k}', s, M['bark'], voxel=0.003, smooth=2, lump=0.0003)
        cn = _pine_tiers(f'canopy_{k}', r)
        protos.append((tr, cn))
    placed = []
    while len(placed) < n:
        d = math.sqrt(r_in ** 2 + (r_out ** 2 - r_in ** 2) * r.random()); a = r.uniform(0, 6.28); p = Vector((math.cos(a) * d, math.sin(a) * d, 0))
        if p.y > 0 and path[0] - 0.03 < p.x < path[1] + 0.03: continue
        if any((p - q).length < 0.11 for q in placed): continue
        placed.append(p)
    for i, p in enumerate(placed):
        tr0, cn0 = protos[i % 3]; sc_ = r.uniform(0.75, 1.25)
        hold = empty(f'tree_{i}', tuple(p)); K._to(hold); hold.rotation_euler = (r.uniform(-0.02, 0.02), r.uniform(-0.02, 0.02), r.uniform(0, 6.28))
        hold.scale = (sc_, sc_, r.uniform(0.9, 1.15))
        for o0 in (tr0, cn0):
            o = o0.copy(); bpy.data.collections['Set'].objects.link(o); K.attach(o, hold)
        out.append(hold)
    for tr, cn in protos: tr.hide_render = tr.hide_viewport = cn.hide_render = cn.hide_viewport = True
    return out


def _pine_tiers(name, r, z0=0.62, z1=1.4, n=7):
    """a pine's needle mass as drooping skirts, wide low and narrow at the top, joined into one lumpy clay mesh"""
    obs = []
    for i in range(n):
        t = i / (n - 1); z = z0 + (z1 - z0) * t; rad = 0.12 * (1 - t) ** 0.9 + 0.02
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=rad, radius2=rad * 0.12, depth=rad * 1.1,
                                        location=(r.uniform(-0.01, 0.01), r.uniform(-0.01, 0.01), z))
        c = bpy.context.object
        for v in c.data.vertices:                                       # ragged, drooping hem
            if v.co.z < 0: v.co.z -= rad * 0.25 * (0.5 + 0.5 * math.sin(math.atan2(v.co.y, v.co.x) * 7 + i))
        obs.append(c)
    bpy.ops.object.select_all(action='DESELECT')
    for c in obs: c.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.join()
    ob = bpy.context.object; ob.name = name; ob.data.materials.append(M['pine'])
    for p in ob.data.polygons: p.use_smooth = True
    K.add_lumps(ob, 0.008, size=0.03); K._to(ob)
    return ob


def logs_seat(x, y, yaw, length=0.09, r_=0.009, name='seat_log'):
    """a fallen log to sit on by the fire (in the colliders)"""
    s = HP.Shape().capsule((-length / 2, 0, r_), (length / 2, 0, r_ * 0.95), r_, r_ * 0.92, 16)
    lg = piece(name, s, M['log'], voxel=0.0009, smooth=2, lump=0.00025)
    hold = empty(name + '_h', (x, y, 0)); K._to(hold); hold.rotation_euler = (0, 0, yaw); K.attach(lg, hold)
    HP.colliders().objects.link(lg); return hold


# ------------------------------------------------------------------ the campfire
class Campfire(PL.Practical):
    """a stone ring, crossed logs, a few flames that never hold still, embers, and a warm flickering light.
    level 1 = a good fire, about 0.3 = burnt down to embers (flames shrink with it)"""
    def __init__(self, x, y, energy=6.0, color=(1.0, 0.52, 0.2)):
        PL.Practical.__init__(self, 'campfire', x, y, 0.0, 0.0)
        if not M: materials()
        r = random.Random(5)
        for i in range(11):
            a = i / 11 * 6.28 + r.uniform(-0.1, 0.1); rr = 0.028
            s = HP.Shape().ellipsoid((0, 0, 0.003), (r.uniform(0.006, 0.009), r.uniform(0.005, 0.007), r.uniform(0.004, 0.006)))
            st = piece(f'fire_stone_{i}', s, M['rock'], voxel=0.0006, smooth=2, lump=0.00012)
            self._put(st, (math.cos(a) * rr, math.sin(a) * rr, 0)); st.rotation_euler = (0, 0, a)
        s = HP.Shape().ellipsoid((0, 0, 0.0), (0.024, 0.024, 0.003))
        self._put(piece('fire_ash', s, M['char'], voxel=0.0008, smooth=2), (0, 0, 0))
        em_m, glow = PL._emit_mat('embers', (1.0, 0.32, 0.08), 6.0, base=(0.05, 0.03, 0.02)); self._glow(glow, 6.0)
        for i in range(4):                                              # logs leaning into a cone, glowing ends
            a = i / 4 * 6.28 + 0.4
            s = HP.Shape().capsule((math.cos(a) * 0.022, math.sin(a) * 0.022, 0.002), (math.cos(a) * 0.003, math.sin(a) * 0.003, 0.016), 0.0035, 0.0028, 12)
            self._put(piece(f'fire_log_{i}', s, M['log'], voxel=0.0006, smooth=2, lump=0.0001), (0, 0, 0))
            s = HP.Shape().ball((math.cos(a) * 0.004, math.sin(a) * 0.004, 0.015), 0.003)
            self._put(piece(f'fire_ember_{i}', s, em_m, voxel=0.0005, smooth=1), (0, 0, 0))
        fl_m, fg = PL._emit_mat('flame', (1.0, 0.55, 0.18), 22.0); self._glow(fg, 22.0)
        fl_core, cg = PL._emit_mat('flame_core', (1.0, 0.85, 0.5), 30.0); self._glow(cg, 30.0)
        self.flames = []
        for i, (dx, dy, hh, m) in enumerate(((0, 0, 1.0, fl_core), (0.004, 0.002, 0.8, fl_m), (-0.004, 0.003, 0.75, fl_m),
                                             (0.001, -0.004, 0.7, fl_m), (-0.002, -0.002, 0.55, fl_m))):
            f = sphere(f'flame_{i}', 0.0045 if m is fl_m else 0.0035, (0, 0, 0), scale=(1, 1, 2.6), mat=m)
            self._put(f, (dx, dy, 0.01 + 0.006 * hh)); f.visible_shadow = False
            self.flames.append((f, Vector((dx, dy, 0.01 + 0.006 * hh)), hh))
        lt = point_light('fire_light', (0, 0, 0), energy, radius=0.012, color=color); self._light(lt, energy)
        K.attach(lt, self.h); lt.location = (0, 0, 0.03)
        lo = point_light('fire_bounce', (0, 0, 0), energy * 0.15, radius=0.05, color=(1.0, 0.4, 0.15)); self._light(lo, energy * 0.15)
        K.attach(lo, self.h); lo.location = (0, 0, 0.006)

    def burn(self, f0, f1, seed=3, level=None):
        """the flames lick and stretch every frame and the light breathes with them. level(f) -> 0..1 (embers)"""
        r = random.Random(seed)
        for f in range(f0, f1 + 1):
            lv = level(f) if level else self.cur
            for fl, base, hh in self.flames:
                s = r.uniform(0.7, 1.25) * hh * max(0.05, (lv - 0.2) / 0.8)
                fl.scale = (0.8 + 0.4 * lv, 0.8 + 0.4 * lv, 2.6 * s)
                fl.location = base + Vector((r.uniform(-0.0012, 0.0012), r.uniform(-0.0012, 0.0012), 0.004 * s))
                fl.keyframe_insert('scale', frame=f); fl.keyframe_insert('location', frame=f)
            self.level(f, lv * r.uniform(0.82, 1.12))
            self.cur = lv


# ------------------------------------------------------------------ the tent
class Tent:
    """a two-person dome tent (2.1 x 1.5 x 1.1 m): a thin nylon shell you can see out of from inside, two crossing
    poles, a groundsheet, and a door on the front (-y) whose zip opens from the bottom: tent.zip(f, 0..1)"""
    def __init__(self, name, x, y, yaw=0.0, color='green', w=0.21, d=0.15, h=0.11):
        if not M: materials()
        self.name, self.w, self.d, self.hgt = name, w, d, h
        self.h = empty(name, (x, y, 0)); K._to(self.h); self.h.rotation_euler = (0, 0, math.radians(yaw))
        col, glow = TENT_COLORS.get(color, color)
        self.cloth = tent_cloth(f'{name}_nylon', col, glow)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0)
        sh = bpy.context.object; sh.name = f'{name}_shell'
        me = sh.data
        import bmesh
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.02], context='VERTS')
        for v in bm.verts:                                              # a dome that sags between the poles
            z = max(0.0, v.co.z); sag = 1 - 0.05 * (math.sin(2 * math.atan2(v.co.y, v.co.x)) ** 2) * z
            v.co.x *= w / 2 * sag; v.co.y *= d / 2 * sag; v.co.z = z * h
        bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        sol = sh.modifiers.new('nylon', 'SOLIDIFY'); sol.thickness = 0.0008
        me.materials.append(self.cloth); K._to(sh); K.attach(sh, self.h); self.shell = sh
        # the door: a zip slit cut through the front of the shell, opening from the ground up
        self.cut = K.block(f'{name}_zipcut', -0.0025, 0.0025, -d / 2 - 0.02, -d / 2 + 0.03, 0.0, 1.0, K.M['void'], bevel=0)
        K.attach(self.cut, self.h); self.cut.location = (0, 0, 0.002); self.cut.scale = (1, 1, 1e-4)
        self.cut.hide_render = True; self.cut.display_type = 'WIRE'
        bo = sh.modifiers.new('zip', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = self.cut; bo.solver = 'FLOAT'
        self.door_h = h * 0.82
        s = HP.Shape()                                                  # the zip line itself: a dark track up the door
        for i in range(12):
            t = i / 11; z = 0.004 + t * self.door_h
            yy = -(d / 2) * math.sqrt(max(0.0, 1 - (z / h) ** 2)) - 0.0004
            s.ball((0, yy, z), 0.0007, 8)
        self.track = piece(f'{name}_zip', s, M['pole'], voxel=0.0004, smooth=1); K.attach(self.track, self.h)
        s = HP.Shape()                                                  # two poles crossing over the top
        for sgn in (1, -1):
            pts = []
            for i in range(17):
                t = i / 16 * math.pi; ca = math.cos(t)
                pts.append(Vector((ca * w / 2 * 1.01 * sgn * 0.71, ca * d / 2 * 1.01 * 0.71, math.sin(t) * h * 1.01)))
            for a, b in zip(pts, pts[1:]): s.capsule(a, b, 0.0009, 0.0009, 8)
        K.attach(piece(f'{name}_poles', s, M['pole'], voxel=0.0005, smooth=1), self.h)
        gs = K.block(f'{name}_floor', -w / 2 * 0.97, w / 2 * 0.97, -d / 2 * 0.97, d / 2 * 0.97, 0.0, 0.0012,
                     K.painted(f'{name}_groundsheet', (0.05, 0.05, 0.055), rough=0.6), bevel=0.0005)
        K.attach(gs, self.h); HP.colliders().objects.link(gs)
        self.zip(None, 0.0)

    def zip(self, f, u):
        """open the door slit from the bottom: u 0 closed, 1 fully open (0.9 m)"""
        self.cut.scale = (1 + 0.6 * u, 1, max(1e-4, u * self.door_h))
        if f is not None: self.cut.keyframe_insert('scale', frame=f)

    def door_point(self, z=0.03, out=0.0):
        """a point on the door line (world), out > 0 steps outside"""
        y = -(self.d / 2) * math.sqrt(max(0.0, 1 - (z / self.hgt) ** 2)) - out
        return self.h.matrix_world @ Vector((0, y, z))

    def inside(self, x=0.0, y=0.0, z=0.0):
        return self.h.matrix_world @ Vector((x, y, z))


# ------------------------------------------------------------------ the torch
class Torch(PL.Practical):
    """a small hand torch (16 cm): black body, a lens that glows, a cone of cold white light along its -y"""
    def __init__(self, x, y, z=0.0, yaw=0.0, pitch=0.0, energy=0.35, color=(0.92, 0.95, 1.0), cone=38):
        PL.Practical.__init__(self, 'torch', x, y, z, yaw)
        self.h.rotation_euler = (math.radians(pitch), 0, math.radians(yaw))
        body = cylinder('torch_body', 0.0022, 0.016, (0, 0, 0), verts=24, mat=K.painted('torch_black', (0.02, 0.02, 0.022), rough=0.35))
        self._put(body, (0, 0.008, 0)); body.rotation_euler = (math.pi / 2, 0, 0)
        head = cylinder('torch_head', 0.0029, 0.004, (0, 0, 0), verts=24, mat=K.M['chrome'])
        self._put(head, (0, -0.001, 0)); head.rotation_euler = (math.pi / 2, 0, 0)
        lm, glow = PL._emit_mat('torch_lens', color, 12.0, base=(0.2, 0.2, 0.2)); self._glow(glow, 12.0)
        lens = cylinder('torch_lens', 0.0025, 0.0004, (0, 0, 0), verts=24, mat=lm)
        self._put(lens, (0, -0.0032, 0)); lens.rotation_euler = (math.pi / 2, 0, 0)
        ld = bpy.data.lights.new('torch_beam', 'SPOT'); ld.energy = energy; ld.spot_size = math.radians(cone)
        ld.spot_blend = 0.5; ld.shadow_soft_size = 0.001; ld.color = color
        lt = bpy.data.objects.new('torch_beam', ld); bpy.context.scene.collection.objects.link(lt); self._light(lt, energy)
        K.attach(lt, self.h); lt.location = (0, -0.0036, 0); lt.rotation_euler = (math.pi / 2, 0, 0)   # spot looks down -z: turn to -y
        spill = point_light('torch_spill', (0, 0, 0), energy * 0.06, radius=0.003, color=color); self._light(spill, energy * 0.06)
        K.attach(spill, self.h); spill.location = (0, -0.006, 0)

    def src(self):
        return self.h.matrix_world @ Vector((0, -0.005, 0))


# ------------------------------------------------------------------ the fence
class Fence:
    """Sector B13: a 2.4 m chain-link fence on dark posts with a barbed strand on top, a gate in it (hinged on its
    left post), and the warning sign wired to the mesh right of the gate. Runs along x at y, facing the clearing (-y)."""
    def __init__(self, y=0.8, x0=-1.2, x1=1.2, gate=(-0.06, 0.06), height=0.24, sign=True, seed=2):
        if not M: materials()
        r = random.Random(seed); self.y = y; self.gate_x = gate; self.hgt = height
        self.h = empty('fence', (0, y, 0)); K._to(self.h)
        posts = [x0 + i * 0.12 for i in range(int((x1 - x0) / 0.12) + 1)]
        posts = [p for p in posts if not (gate[0] - 0.05 < p < gate[1] + 0.05)] + [gate[0], gate[1]]
        for i, px in enumerate(sorted(posts)):
            c = cylinder(f'fence_post_{i}', 0.0028, height + 0.01, (0, 0, 0), verts=16, mat=M['post'])
            K._to(c); K.attach(c, self.h); c.location = (px, 0, (height + 0.01) / 2)
            c.rotation_euler = (r.uniform(-0.02, 0.02), r.uniform(-0.02, 0.02), 0)
        for a, b in ((x0, gate[0]), (gate[1], x1)):                    # mesh panels and the top rail and barbed strand
            self._panel(f'fence_mesh_{a:.2f}', a, b, 0.003, height)
            rail = cylinder('fence_rail', 0.0012, b - a, (0, 0, 0), verts=12, mat=M['post'])
            K._to(rail); K.attach(rail, self.h); rail.location = ((a + b) / 2, 0, height); rail.rotation_euler = (0, math.pi / 2, 0)
            self._barbs(a, b, height + 0.012, r)
        self.hinge = empty('gate_hinge', (0, 0, 0)); K._to(self.hinge); K.attach(self.hinge, self.h); self.hinge.location = (gate[0], 0, 0)
        gw = gate[1] - gate[0] - 0.004
        g = self._panel('gate_mesh', 0.002, 0.002 + gw, 0.006, height - 0.01, par=self.hinge)
        for nm, (ax, az, bx, bz) in (('gate_top', (0, height - 0.01, gw, height - 0.01)), ('gate_bot', (0, 0.006, gw, 0.006)),
                                     ('gate_l', (0.002, 0.006, 0.002, height - 0.01)), ('gate_r', (gw, 0.006, gw, height - 0.01)),
                                     ('gate_brace', (0.002, 0.006, gw, height - 0.01))):
            a = Vector((ax, 0, az)); b = Vector((bx, 0, bz)); L_ = (b - a).length
            bar = cylinder(nm, 0.0011, L_, (0, 0, 0), verts=12, mat=M['post']); K._to(bar); K.attach(bar, self.hinge)
            bar.location = (a + b) / 2; bar.rotation_euler = (0, math.atan2(b.x - a.x, b.z - a.z), 0)
        chain = cylinder('gate_chain', 0.0009, 0.012, (0, 0, 0), verts=8, mat=M['rust']); K._to(chain); K.attach(chain, self.h)
        chain.location = (gate[1] - 0.003, -0.002, 0.12); self.lock_at = self.h.matrix_world @ Vector((gate[1], -0.004, 0.11))
        self.padlock = K.block('padlock', -0.0025, 0.0025, -0.0012, 0.0012, -0.004, 0.0, M['rust'], bevel=0.0006)
        K.attach(self.padlock, self.h); self.padlock.location = (gate[1] - 0.003, -0.004, 0.115)
        if sign:
            sg = K.block('b13_sign', -0.045, 0.045, -0.0008, 0.0008, -0.028, 0.028, M['sign'], bevel=0)
            K.attach(sg, self.h); sg.location = (gate[1] + 0.07, -0.004, 0.13); sg.rotation_euler = (0, math.radians(-2), 0)
            self._uv_front(sg)
            self.sign = sg; self.sign_at = self.h.matrix_world @ Vector((gate[1] + 0.07, -0.004, 0.13))

    def _panel(self, name, a, b, z0, z1, par=None):
        bpy.ops.mesh.primitive_plane_add(size=1); p = bpy.context.object; p.name = name
        p.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))
        p.scale = (b - a, 1, z1 - z0); p.location = ((a + b) / 2, 0, (z0 + z1) / 2)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        for lp in p.data.loops:                                         # the diamond is 5 cm across: tile by size
            co = p.data.vertices[lp.vertex_index].co
            p.data.uv_layers.active.data[lp.index].uv = ((co.x + (a + b) / 2) / 0.05, (co.z + (z0 + z1) / 2) / 0.05)
        p.data.materials.append(M['wire']); K._to(p); K.attach(p, par or self.h)
        return p

    def _barbs(self, a, b, z, r):
        s = HP.Shape(); x = a
        while x < b:
            nx = min(b, x + 0.01); s.capsule((x, 0, z + r.uniform(-0.0005, 0.0005)), (nx, 0, z + r.uniform(-0.0005, 0.0005)), 0.0004, 0.0004, 6)
            s.capsule((x, -0.002, z - 0.0015), (x, 0.002, z + 0.0015), 0.0003, 0.0003, 6); x = nx
        K.attach(piece('barbed_wire', s, M['rust'], voxel=0.0003, smooth=0), self.h)

    @staticmethod
    def _uv_front(ob):
        me = ob.data
        if not me.uv_layers: me.uv_layers.new()
        xs = [v.co.x for v in me.vertices]; zs = [v.co.z for v in me.vertices]
        for lp in me.loops:
            co = me.vertices[lp.vertex_index].co
            me.uv_layers.active.data[lp.index].uv = ((co.x - min(xs)) / (max(xs) - min(xs)), (co.z - min(zs)) / (max(zs) - min(zs)))

    def gate(self, f, deg):
        """swing the gate open toward the woods side (+y) by deg"""
        self.hinge.rotation_euler = (0, 0, math.radians(deg))
        if f is not None: self.hinge.keyframe_insert('rotation_euler', frame=f)


# ------------------------------------------------------------------ light
def mood(kind, bounds=(-3.5, -3.5, 0.0, 3.5, 3.5, 0.5), haze=0.14):
    """night: a cold moon high behind the trees, faint sky, thin mist. dawn: blue-grey sky, a low cold light from the
    east through the trunks, thicker mist lying on the ground"""
    sc = bpy.context.scene
    if kind == 'night':
        world((0.015, 0.02, 0.04), 0.25)
        m = area_light('moon', (-0.9, 1.1, 1.4), (0.1, 0, 0), 70.0, 0.15, (0.55, 0.68, 1.0)); K._to(m, 'Lights')
        f = area_light('sky_fill', (0, -0.8, 0.6), (0, 0.2, 0.0), 0.6, 1.0, (0.45, 0.55, 0.9)); K._to(f, 'Lights')
        dens = haze
    else:
        world((0.32, 0.38, 0.5), 0.9)
        s = area_light('dawn_low', (1.6, 0.4, 0.18), (0, 0.2, 0.05), 220.0, 0.6, (0.75, 0.82, 1.0)); K._to(s, 'Lights')
        f = area_light('dawn_sky', (0, 0, 1.5), (0, 0, 0), 40.0, 2.0, (0.6, 0.7, 0.95)); K._to(f, 'Lights')
        dens = haze * 3.0
    if haze:
        hz = bpy.data.materials.new('mist'); hz.use_nodes = True; hn = hz.node_tree.nodes
        hn.remove(hn['Principled BSDF']); pv = hn.new('ShaderNodeVolumePrincipled')
        pv.inputs['Density'].default_value = dens; pv.inputs['Anisotropy'].default_value = 0.5
        pv.inputs['Color'].default_value = (0.75, 0.8, 0.9, 1)
        # thicker near the ground: density fades with height
        gr = hn.new('ShaderNodeTexCoord'); sep = hn.new('ShaderNodeSeparateXYZ'); mp = hn.new('ShaderNodeMapRange')
        x0, y0, z0, x1, y1, z1 = bounds
        mp.inputs['From Min'].default_value = 0.0; mp.inputs['From Max'].default_value = 1.0
        mp.inputs['To Min'].default_value = dens; mp.inputs['To Max'].default_value = dens * 0.15
        hz.node_tree.links.new(gr.outputs['Generated'], sep.inputs[0]); hz.node_tree.links.new(sep.outputs['Z'], mp.inputs['Value'])
        hz.node_tree.links.new(mp.outputs['Result'], pv.inputs['Density'])
        hz.node_tree.links.new(pv.outputs[0], hn['Material Output'].inputs['Volume'])
        bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        ob = bpy.context.object; ob.name = 'mist'; ob.scale = (x1 - x0, y1 - y0, z1 - z0); ob.data.materials.append(hz); K._to(ob)
        sc.cycles.volume_bounces = 0; sc.cycles.volume_step_rate = 4.0
    return sc
