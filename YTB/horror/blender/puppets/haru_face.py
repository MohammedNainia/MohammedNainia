"""The new Haru's face (cast_kit.haru). Her eyes stay small glossy dots, always (her look). The feeling is carried by her
clay brows and her mouth, like the Artlist sheet YTB/channel_art/kit/haru_dot_expressions_01a221d3.png.

    face = HF.Face(c)                                    # c = cast_kit.haru(...), built while the rig is at rest
    face.set(f, 'sad', look=(0.2, -0.1), blink=0, tears=0.6, pale=0.5, t=seconds)

How it works (a stop-motion replacement kit)
- Her painted eyes, brows and mouth are painted out of her texture (filled with her own skin), so nothing is doubled.
- Eyes: one dot bead each that can look around, and a closed curve for blinks and sleep. Nothing else.
- Brows: a set of sculpted clay brows per side (thick in the middle, tapered at the ends), bent onto her forehead.
  Each expression swaps in its pair, like an animator swapping replacement parts.
- Mouth: a set of sculpted mouths bent onto her face: lip lines (line, frown, wavy, pressed, smile) and openings with a
  dark inside, a lip rim and teeth (o, cry, scream, laugh, grimace). The jaw shape key drops her chin with the open ones.
- Cheeks push up for a smile (shape key). Tears pool under the dots and run down. pale drains her skin.
Positions come from a flat front photo of her face (measured once): see MEASURED."""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, Matrix

# measured on the flat front render of haru_full at the kit size (12.6 cm), rig at rest: x, z in metres
MEASURED = dict(eye=(0.0050, 0.1100, 0.0012), brow=(0.0057, 0.1137, 0.0024, 0.0009), mouth=(0.0004, 0.1037, 0.0019),
                skin=(0.894, 0.673, 0.556))

# brows: (inner z, outer z, arch, pinch toward the nose, thickness) in metres, relative to the measured brow line.
# inner high + outer low = sad. A pair is (her right, her left); one entry = both sides the same.
BROWS = {
    'neutral':   [(0.0000, -0.0002, 0.0005, 0.0000, 1.0)],
    'sad':       [(0.0011, -0.0007, 0.0004, 0.0003, 1.0)],
    'uneasy':    [(0.0002, -0.0003, 0.0003, 0.0001, 1.0), (0.0009, -0.0003, 0.0005, 0.0002, 1.0)],
    'worried':   [(0.0010, -0.0004, 0.0001, 0.0006, 1.05)],
    'scared':    [(0.0012, -0.0002, 0.0006, 0.0003, 1.0)],
    'crying':    [(0.0014, -0.0008, 0.0006, 0.0004, 1.05)],
    'terrified': [(0.0015, -0.0001, 0.0007, 0.0004, 1.05)],
    'soft':      [(0.0003, 0.0000, 0.0004, 0.0000, 0.95)],
    'up':        [(0.0005, 0.0002, 0.0005, 0.0000, 1.0)],
    'tight':     [(-0.0004, 0.0001, 0.0002, 0.0004, 1.1)],
    'low':       [(-0.0001, -0.0003, 0.0004, 0.0000, 1.0)],
}

# mouths: kind 'line' (a lip stroke) or 'open' (an opening). jaw = how far the chin drops with it.
MOUTHS = {
    'line':    dict(kind='line', jaw=0.0),
    'frown':   dict(kind='line', jaw=0.05),
    'wavy':    dict(kind='line', jaw=0.0),
    'pressed': dict(kind='line', jaw=0.0),
    'smile':   dict(kind='line', jaw=0.0),
    'o':       dict(kind='open', jaw=0.15),
    'cry':     dict(kind='open', jaw=0.45, teeth='top'),
    'scream':  dict(kind='open', jaw=1.0, teeth='both'),
    'laugh':   dict(kind='open', jaw=0.35, teeth='top'),
    'grimace': dict(kind='open', jaw=0.15, teeth='both'),
}

# expressions: eyes ('dot' | 'closed'), dot size, brows, mouth, cheeks. The sheet's eight plus the reel's extras.
EXPR = {
    'neutral':       dict(eyes='dot', brows='neutral', mouth='line', cheeks=0.0),
    'sad':           dict(eyes='dot', brows='sad', mouth='frown', cheeks=0.0),
    'uncomfortable': dict(eyes='dot', brows='uneasy', mouth='wavy', cheeks=0.0),
    'worried':       dict(eyes='dot', brows='worried', mouth='pressed', cheeks=0.0),
    'scared':        dict(eyes='dot', dot=0.9, brows='scared', mouth='o', cheeks=0.0),
    'crying':        dict(eyes='dot', brows='crying', mouth='cry', cheeks=0.2),
    'muffled':       dict(eyes='dot', brows='crying', mouth='pressed', cheeks=0.3),     # crying with her mouth clamped shut
    'terrified':     dict(eyes='dot', dot=0.85, brows='terrified', mouth='scream', cheeks=0.1),
    'relieved':      dict(eyes='dot', brows='soft', mouth='smile', cheeks=0.3),
    'happy':         dict(eyes='dot', brows='soft', mouth='smile', cheeks=0.6),
    'laugh':         dict(eyes='dot', brows='up', mouth='laugh', cheeks=1.0),
    'squeeze':       dict(eyes='closed', brows='tight', mouth='grimace', cheeks=0.6),
    'stare':         dict(eyes='dot', dot=0.85, brows='up', mouth='line', cheeks=0.0),
    'sleep':         dict(eyes='closed', brows='low', mouth='line', cheeks=0.0),
}
HIDE = 1e-4


def _mat(name, rgb, rough=0.4, gloss=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    if gloss: b.inputs['Coat Weight'].default_value = 0.8; b.inputs['Coat Roughness'].default_value = 0.04
    return m


def _curve(name, pts, r, mat, coll, radii=None, closed=False):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1); sp.use_cyclic_u = closed
    for i, (p, q) in enumerate(zip(sp.points, pts)):
        p.co = (*q, 1)
        if radii is not None: p.radius = radii[i]
    ob = bpy.data.objects.new(name, cu); coll.objects.link(ob); ob.data.materials.append(mat)
    return ob


def _ball(name, r, mat, coll, scale=(1, 1, 1), loc=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob); me.materials.append(mat)
    ob.scale = scale; ob.location = loc
    return ob


def _arc(cx, w, h, n=9, z0=0.0):
    """points across x in [-w, w], bulging by h in z (negative h bows down), in a feature's local x-z plane"""
    return [(cx + w * (2 * i / (n - 1) - 1), 0.0, z0 + h * (1 - (2 * i / (n - 1) - 1) ** 2)) for i in range(n)]


def _outline(top, bot, w, n=14):
    """a closed opening: top(u) and bot(u) give z for u in [-1, 1] (x = u * w); the corners are where they meet"""
    us = [math.cos(math.pi * (1 - i / (n - 1))) for i in range(n)]          # bunched at the corners
    return [(u * w, top(u)) for u in us] + [(u * w, bot(u)) for u in reversed(us[1:-1])]


class Face:
    def __init__(self, c, name='haru'):
        self.c, self.rg, self.body, self.name = c, c['rig'], c['body'], name
        self.coll = bpy.data.collections.new(name + '_face'); bpy.context.scene.collection.children.link(self.coll)
        bpy.context.view_layer.update()
        self.skin_rgb = MEASURED['skin']
        self._paint_out()
        self.M = dict(dark=_mat('face_dark', (0.006, 0.005, 0.005), rough=0.3, gloss=True),
                      brow=_mat('brow_clay', (0.03, 0.026, 0.025), rough=0.75),
                      inside=_mat('mouth_inside', (0.025, 0.004, 0.005), rough=1.0),
                      tongue=_mat('mouth_tongue', (0.16, 0.03, 0.03), rough=0.6),
                      teeth=_mat('teeth', (0.78, 0.76, 0.71), rough=0.6),
                      lip=_mat('lip_line', (0.09, 0.025, 0.022), rough=0.55),
                      rim=_mat('lip_rim', (0.3, 0.1, 0.08), rough=0.6),
                      tear=_mat('tear', (0.85, 0.9, 0.95), rough=0.05, gloss=True))
        self._shape_keys()
        self._eyes(); self._brows(); self._mouth(); self._tears(); self._pallor()

    # ---------------------------------------------------------------- surface
    def surf(self, x, z):
        """point and outward normal on her face (rig rest space) straight in front of (x, z)"""
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()   # fresh: shape keys change the mesh
        ev = self.body.evaluated_get(dg)
        ok, p, n, _ = ev.ray_cast(Vector((x, -0.1, z)), Vector((0, 1, 0)), depsgraph=dg)
        if not ok: return Vector((x, -0.012, z)), Vector((0, -1, 0))
        return p, n.normalized()

    def frame(self, name, x, z, inset=0.0):
        """an empty on the head bone at (x, z) on her face: local -y points out of the face, x right, z up"""
        p, n = self.surf(x, z)
        Y = -n; X = Vector((1, 0, 0)) - Y * Y.x; X.normalize(); Z = X.cross(Y)
        e = bpy.data.objects.new(name, None); self.coll.objects.link(e); e.empty_display_size = 0.002
        M = Matrix((X, Y, Z)).transposed().to_4x4(); M.translation = p + Y * inset
        e.matrix_world = self.rg.matrix_world @ M
        e.parent = self.rg; e.parent_type = 'BONE'; e.parent_bone = 'head'
        e.matrix_world = self.rg.matrix_world @ M
        return e

    def _kid(self, ob, par):
        ob.parent = par; ob.matrix_parent_inverse.identity(); return ob

    # ---------------------------------------------------------------- paint out the painted face
    def _paint_out(self):
        me = self.body.data; img = None
        for m in me.materials:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image and n.image.size[0] > 0: img = n.image; break
            if img: break
        self.img = img
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(px); px = px.reshape(h, w, 4)
        ex, ez, er = MEASURED['eye']; bx, bz, bw, bh = MEASURED['brow']; mx, mz, mw = MEASURED['mouth']
        regions = [(-ex, ez, er * 1.45, er * 1.45), (ex, ez, er * 1.45, er * 1.45), (-bx, bz, bw * 1.15, bh * 1.15),
                   (bx, bz, bw * 1.15, bh * 1.15), (mx, mz, mw * 1.3, 0.0008)]
        uv = me.uv_layers.active.data
        mask = np.zeros((h, w), bool)
        for p in me.polygons:
            c = p.center
            if c.y > -0.004: continue
            if not any(((c.x - rx) / rw) ** 2 + ((c.z - rz) / rh) ** 2 < 1 for rx, rz, rw, rh in regions): continue
            tri = np.array([uv[li].uv[:] for li in p.loop_indices]) * [w - 1, h - 1]
            x0, y0 = np.floor(tri.min(0)).astype(int); x1, y1 = np.ceil(tri.max(0)).astype(int)
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            P = np.stack([xs.ravel(), ys.ravel()], 1).astype(float)
            a, b, cc = tri[0], tri[1], tri[2 if len(tri) > 2 else 1]
            v0, v1 = b - a, cc - a; d = v0[0] * v1[1] - v1[0] * v0[1]
            if abs(d) < 1e-9: continue
            q = P - a; s = (q[:, 0] * v1[1] - v1[0] * q[:, 1]) / d; t = (v0[0] * q[:, 1] - q[:, 0] * v0[1]) / d
            pad = 0.05
            inside = (s >= -pad) & (t >= -pad) & (s + t <= 1 + pad)
            xi, yi = P[inside, 0].astype(int) % w, P[inside, 1].astype(int) % h
            mask[yi, xi] = True
        # fill the holes from their edges inward (a membrane / Laplace fill), so the patch takes on the skin's own
        # shading around it; dark texels at the rim (the last of a painted line) are ignored as sources
        ring = np.zeros_like(mask)
        for dy in (-2, -1, 0, 1, 2):
            for dx in (-2, -1, 0, 1, 2):
                ring |= np.roll(np.roll(mask, dy, 0), dx, 1)
        ring &= ~mask
        rgb = px[..., :3].copy(); lum = rgb @ [0.2126, 0.7152, 0.0722]
        bad = ring & (lum < 0.42)                                       # rim texels still dark: fill them too
        hole = mask | bad
        skin = rgb[ring & ~bad]
        col = np.median(skin, axis=0) if len(skin) > 20 else np.array(self.skin_rgb, np.float32)
        rgb[hole] = col
        for _ in range(400):
            avg = (np.roll(rgb, 1, 0) + np.roll(rgb, -1, 0) + np.roll(rgb, 1, 1) + np.roll(rgb, -1, 1)) / 4
            rgb[hole] = avg[hole]
        noise = np.random.default_rng(3).normal(0, 0.006, (int(hole.sum()), 1)).astype(np.float32)
        px[hole, :3] = rgb[hole] + noise
        mask = hole
        img.pixels.foreach_set(px.ravel()); img.update(); img.pack()
        self.skin_rgb = tuple(float(v) for v in col)
        print(f'FACE paint-out: {int(mask.sum())} texels filled with skin {np.round(col, 3)}', flush=True)

    # ---------------------------------------------------------------- shape keys: jaw and cheeks
    def _shape_keys(self):
        ob = self.body; me = ob.data
        if not me.shape_keys: ob.shape_key_add(name='Basis', from_mix=False)
        mx, mz, mw = MEASURED['mouth']; ex, ez, er = MEASURED['eye']
        co = np.array([v.co[:] for v in me.vertices])
        x, y, z = co[:, 0], co[:, 1], co[:, 2]
        front = y < -0.003
        # jaw: everything below the mouth line drops and tucks back; full at the chin, nothing at the lips' corners
        below = np.clip((mz - z) / 0.0035, 0, 1) * np.clip(1 - (np.abs(x - mx) / 0.009) ** 2, 0, 1) * front * (z > mz - 0.012)
        k = ob.shape_key_add(name='jaw', from_mix=False); d = np.zeros_like(co)
        d[:, 2] = -0.0026 * below; d[:, 1] = 0.0005 * below
        k.data.foreach_set('co', (co + d).ravel())
        # cheeks: round pads under the eyes push up and out
        k = ob.shape_key_add(name='cheeks', from_mix=False); d = np.zeros_like(co)
        for sx in (-1, 1):
            r = np.sqrt((x - sx * 0.0062) ** 2 + (z - 0.1062) ** 2)
            w = np.clip(1 - r / 0.0038, 0, 1) ** 2 * front
            d[:, 2] += 0.00045 * w; d[:, 1] -= 0.0003 * w
        k.data.foreach_set('co', (co + d).ravel())
        self.keys = me.shape_keys.key_blocks

    # ---------------------------------------------------------------- bend a part onto her face
    def bend(self, e, pts, off):
        """pts in the frame's local x-z plane -> the same points laid on her face (local y = the surface), off proud"""
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        ev = self.body.evaluated_get(dg); Bw = self.body.matrix_world; Bi = Bw.inverted()
        Mw = e.matrix_world; Mi = Mw.inverted()
        Y = (Mw.to_3x3() @ Vector((0, 1, 0))).normalized(); d = (Bi.to_3x3() @ Y).normalized()
        out = []
        for q in pts:
            x, z = q[0], q[-1]
            ok, p, n, _ = ev.ray_cast(Bi @ (Mw @ Vector((x, -0.01, z))), d, depsgraph=dg)
            y = (Mi @ (Bw @ p)).y if ok else 0.0
            out.append((x, y - off, z))
        return out

    def _mesh(self, name, e, outline, off, mat):
        """a flat part (an opening, teeth) with this outline, bent onto her face"""
        pts = self.bend(e, [(x, 0, z) for x, z in outline], off)
        bm = bmesh.new(); vs = [bm.verts.new(p) for p in pts]; f = bm.faces.new(vs)
        bmesh.ops.triangulate(bm, faces=[f], quad_method='BEAUTY', ngon_method='EAR_CLIP')
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name, me); self.coll.objects.link(ob); me.materials.append(mat)
        return self._kid(ob, e)

    # ---------------------------------------------------------------- eyes: dots, always
    def _eyes(self):
        ex, ez, er = MEASURED['eye']; self.eyes = []
        for sd, tag in ((-1, 'R'), (1, 'L')):                       # her right eye is on -x
            e = self.frame(f'{self.name}_eye.{tag}', sd * ex, ez)
            E = dict(root=e, sd=sd)
            E['dot'] = self._kid(_ball(f'eye_dot.{tag}', er * 1.1, self.M['dark'], self.coll, scale=(1, 0.6, 1)), e)
            arc = [(x, -0.0002, z) for x, _, z in _arc(0, er * 1.2, -er * 0.55)]
            E['closed'] = self._kid(_curve(f'eye_closed.{tag}', arc, er * 0.25, self.M['dark'], self.coll), e)
            self.eyes.append(E)

    # ---------------------------------------------------------------- brows: replacement pairs
    def _brow_pts(self, sd, zi, zo, arch, pinch, n=13):
        bw = MEASURED['brow'][2]; L = bw * 0.95; pts, rad = [], []
        for i in range(n):
            u = i / (n - 1)                                            # 0 = inner end (toward the nose), 1 = outer
            x = -sd * (L - 2 * L * u) - sd * pinch * (1 - 0.5 * u)
            z = zi + (zo - zi) * u + arch * 4 * u * (1 - u)
            pts.append((x, 0, z))
            rad.append((0.35 + 0.8 * math.sin(math.pi * (0.08 + 0.84 * u)) ** 0.7) * (1.1 - 0.35 * u))   # fat inner-middle, thin tail
        return pts, rad

    def _brows(self):
        bx, bz, bw, bh = MEASURED['brow']; self.brows = []
        for side, (sd, tag) in enumerate(((-1, 'R'), (1, 'L'))):
            e = self.frame(f'{self.name}_brow.{tag}', sd * (bx - 0.0004), bz - 0.0007)   # lower and in: clear of her fringe
            S = {}
            for k, spec in BROWS.items():
                zi, zo, arch, pinch, th = spec[side] if len(spec) > 1 else spec[0]
                r = bh * 0.68 * th
                pts, rad = self._brow_pts(sd, zi, zo, arch, pinch)
                pts = self.bend(e, pts, r * 0.3)
                S[k] = self._kid(_curve(f'brow_{k}.{tag}', pts, r, self.M['brow'], self.coll, radii=rad), e)
            self.brows.append(dict(root=e, sd=sd, set=S))

    # ---------------------------------------------------------------- mouths: replacement shapes
    def _mouth(self):
        mx, mz, mw = MEASURED['mouth']
        e = self.frame(f'{self.name}_mouth', mx, mz); self.mouth_root = e; M = self.M
        P = {}
        taper = lambda n: [0.5 + 0.5 * math.sin(math.pi * i / (n - 1)) for i in range(n)]
        n = 15; U = [2 * i / (n - 1) - 1 for i in range(n)]
        lines = dict(
            line=([(u * mw * 0.8, 0, -mw * 0.03 * (1 - u * u)) for u in U], 0.12),
            frown=([(u * mw * 0.85, 0, -mw * 0.3 + mw * 0.45 * (1 - u * u)) for u in U], 0.15),
            wavy=([(u * mw * 0.95, 0, mw * 0.11 * math.sin(math.pi * 1.5 * (u + 1)) - mw * 0.09 * u) for u in U], 0.12),
            pressed=([(u * mw * 1.0, 0, mw * 0.07 * math.sin(math.pi * 2.5 * (u + 1)) + mw * 0.06 * (1 - u * u)) for u in U], 0.16),
            smile=([(u * mw * 0.85, 0, mw * 0.1 - mw * 0.3 * (1 - u * u)) for u in U], 0.12))
        for k, (pts, r) in lines.items():
            r *= mw * 1.15
            P[k] = [self._kid(_curve(f'mouth_{k}', self.bend(e, pts, r * 0.35), r, M['lip'], self.coll, radii=taper(n)), e)]
        sq = lambda u: math.sqrt(max(0.0, 1 - u * u))
        opens = dict(
            o=(mw * 0.5, lambda u: -mw * 0.08 + mw * 0.32 * sq(u), lambda u: -mw * 0.08 - mw * 0.4 * sq(u)),
            cry=(mw * 1.25, lambda u: -mw * 0.35 + mw * 0.55 * (1 - u * u), lambda u: -mw * 0.35 - mw * 0.6 * (1 - u * u) ** 0.7),
            scream=(mw * 0.9, lambda u: -mw * 0.05 + mw * 0.6 * sq(u), lambda u: -mw * 0.05 - mw * 1.65 * sq(u)),
            laugh=(mw * 1.0, lambda u: mw * 0.12 * (1 - u * u), lambda u: -mw * 0.75 * (1 - u * u) ** 0.8),
            grimace=(mw * 1.2, lambda u: mw * 0.24 * (1 - u ** 4), lambda u: -mw * 0.24 * (1 - u ** 4)))
        for k, (w, top, bot) in opens.items():
            self.keys['jaw'].value = MOUTHS[k]['jaw']                 # lay it on the face as it is with that jaw
            ol = _outline(top, bot, w, n=16)
            parts = [self._mesh(f'mouth_{k}', e, ol, 0.00006, M['inside'])]
            rim = self.bend(e, [(x, 0, z) for x, z in ol], mw * 0.02)
            parts.append(self._kid(_curve(f'mouth_{k}_rim', rim, mw * 0.045, M['rim'], self.coll, closed=True), e))
            teeth = MOUTHS[k].get('teeth')
            th = mw * (0.17 if k == 'grimace' else 0.2)
            if teeth:
                ext = 0.5 if k in ('scream', 'o') else 0.72               # an oval's sides fall away fast
                us = [ext * (2 * i / 10 - 1) for i in range(11)]
                tt = [(u * w, top(u) - mw * 0.03) for u in us]
                tt += [(u * w, top(u) - mw * 0.03 - th * (1 - u ** 6 * 0.6)) for u in reversed(us)]
                parts.append(self._mesh(f'mouth_{k}_teeth', e, tt, 0.00011, M['teeth']))
            if teeth == 'both':
                bt = [(u * w, bot(u) + mw * 0.03) for u in us]
                bt += [(u * w, bot(u) + mw * 0.03 + th * 0.8 * (1 - u ** 6 * 0.6)) for u in reversed(us)]
                parts.append(self._mesh(f'mouth_{k}_teeth_b', e, bt, 0.00011, M['teeth']))
            if k in ('cry', 'scream'):                                   # a tongue low in the opening
                tw, tz = w * 0.38, bot(0.0) + mw * 0.22
                tg = [(math.cos(a) * tw, tz + math.sin(a) * mw * (0.2 if math.sin(a) > 0 else 0.12))
                      for a in [2 * math.pi * i / 16 for i in range(16)]]
                parts.append(self._mesh(f'mouth_{k}_tongue', e, tg, 0.00009, M['tongue']))
            P[k] = parts
        self.keys['jaw'].value = 0.0
        self.mouth = P

    # ---------------------------------------------------------------- tears
    def _tears(self):
        ex, ez, er = MEASURED['eye']; self.tears = []
        for sd in (-1, 1):
            E = self.eyes[0 if sd < 0 else 1]; root = E['root']
            pool = self._kid(_ball(f'tear_pool_{sd}', 0.0007, self.M['tear'], self.coll, scale=(1.5, 0.45, 0.6)), root)
            pool.location = (sd * er * 0.15, -0.00015, -er * 1.7)
            path = []
            for i in range(10):
                zz = ez - er * 1.9 - i * 0.0009; xx = sd * (ex + 0.0004 + 0.0002 * i)
                p, n = self.surf(xx, zz); path.append((p, n))
            inv = root.matrix_world.inverted() @ self.rg.matrix_world
            path = [(inv @ p, (inv.to_3x3() @ n).normalized()) for p, n in path]
            drops = []
            for k in range(2):
                d = _ball(f'tear_{sd}_{k}', 0.0006, self.M['tear'], self.coll, scale=(1, 0.7, 1.5))
                self._kid(d, root); drops.append(d)
            self.tears.append(dict(path=path, drops=drops, pool=pool))

    def _tear_at(self, path, u):
        u = min(0.999, max(0.0, u)) * (len(path) - 1); i = int(u); f = u - i
        p = path[i][0].lerp(path[i + 1][0], f); n = path[i][1].lerp(path[i + 1][1], f).normalized()
        return p + n * 0.0003

    # ---------------------------------------------------------------- pallor
    def _pallor(self):
        me = self.body.data
        co = np.array([v.co[:] for v in me.vertices])
        # skin = the face and neck in front of the hair line, and the hands
        a = me.attributes.get('skin_mask') or me.attributes.new('skin_mask', 'FLOAT', 'POINT')
        import cast_kit as CK
        fc = CK._face_colours(self.body); lum = fc @ [0.2126, 0.7152, 0.0722]
        skin_f = (lum > 0.42) & (fc[:, 0] > fc[:, 1]) & (fc[:, 0] - fc[:, 2] < 0.45)      # warm skin, not hair or hoodie
        mask = np.zeros(len(co))
        for p, ok in zip(me.polygons, skin_f):
            c = p.center
            if ok and c.z > 0.093 and c.y < -0.004:
                for vi in p.vertices: mask[vi] = 1.0
        a.data.foreach_set('value', mask)
        self.pale_nodes = []
        for m in me.materials:
            nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            src = b.inputs['Base Color'].links[0].from_socket
            at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'skin_mask'
            v = nt.nodes.new('ShaderNodeValue'); v.name = v.label = 'pale'; v.outputs[0].default_value = 0.0
            mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
            nt.links.new(at.outputs['Fac'], mul.inputs[0]); nt.links.new(v.outputs[0], mul.inputs[1])
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
            nt.links.new(mul.outputs[0], mx.inputs['Factor']); nt.links.new(src, mx.inputs[6])
            mx.inputs[7].default_value = (0.5, 0.46, 0.47, 1)                  # drained, a little grey-blue
            nt.links.new(mx.outputs[2], b.inputs['Base Color'])
            self.pale_nodes.append(v)

    # ---------------------------------------------------------------- set an expression
    def set(self, f, name='neutral', look=(0.0, 0.0), blink=0.0, tears=0.0, pale=0.0, t=0.0):
        X = EXPR[name]; gx, gz = look
        closed = X['eyes'] == 'closed' or blink > 0.5
        for E in self.eyes:
            E['dot'].scale = Vector((1, 0.6, 1)) * X.get('dot', 1.0) if not closed else Vector((HIDE,) * 3)
            E['closed'].scale = Vector((1, 1, 1)) if closed else Vector((HIDE,) * 3)
            E['dot'].location = (gx * 0.0004, -0.0002, gz * 0.0004)
            E['dot'].keyframe_insert('scale', frame=f); E['closed'].keyframe_insert('scale', frame=f)
            E['dot'].keyframe_insert('location', frame=f)
        for B in self.brows:
            for k, ob in B['set'].items():
                ob.scale = (1, 1, 1) if k == X['brows'] else (HIDE,) * 3
                ob.keyframe_insert('scale', frame=f)
        for k, parts in self.mouth.items():
            for ob in parts:
                ob.scale = (1, 1, 1) if k == X['mouth'] else (HIDE,) * 3
                ob.keyframe_insert('scale', frame=f)
        self.keys['jaw'].value = MOUTHS[X['mouth']]['jaw']; self.keys['cheeks'].value = X.get('cheeks', 0.0)
        self.keys['jaw'].keyframe_insert('value', frame=f); self.keys['cheeks'].keyframe_insert('value', frame=f)
        # tears pool under the dots and run down in turn while tears > 0
        for T in self.tears:
            T['pool'].scale = Vector((1.5, 0.45, 0.6)) * min(1.0, tears * 1.5) if tears > 0.01 else Vector((HIDE,) * 3)
            T['pool'].keyframe_insert('scale', frame=f)
            for k, d in enumerate(T['drops']):
                if tears > 0.01:
                    u = ((t * 0.45 + k * 0.5 + (0.25 if T is self.tears[1] else 0)) % 1.0)
                    d.location = self._tear_at(T['path'], u)
                    d.scale = Vector((1, 0.7, 1.5)) * tears
                else:
                    d.scale = (HIDE,) * 3
                d.keyframe_insert('location', frame=f); d.keyframe_insert('scale', frame=f)
        for v in self.pale_nodes:
            v.outputs[0].default_value = pale; v.outputs[0].keyframe_insert('default_value', frame=f)
