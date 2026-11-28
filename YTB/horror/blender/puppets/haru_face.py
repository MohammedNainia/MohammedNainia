"""The new Haru's face (cast_kit.haru). Her eyes stay small glossy dots, always (her look). The feeling is carried by her
clay brows and her mouth, like the Artlist sheet YTB/channel_art/kit/haru_dot_expressions_01a221d3.png.

    face = HF.Face(c)                                    # c = cast_kit.haru(...), built while the rig is at rest
    face.set(f, 'sad', look=(0.2, -0.1), blink=0, tears=0.6, pale=0.5, t=seconds)

How it works (a stop-motion replacement kit)
- Her painted eyes, brows and mouth are painted out of her texture (filled with her own skin), so nothing is doubled.
- Eyes: one dot bead each that can look around, and a closed curve for blinks and sleep. Nothing else.
- Brows: a set of sculpted clay brows per side (thick in the middle, tapered at the ends), bent onto her forehead.
  Each expression swaps in its pair, like an animator swapping replacement parts.
- Mouth: sculpted into her own clay. Her face is refined around the mouth and each mouth is a shape key: a pressed
  groove with rolled lips (line, frown, wavy, pressed, smile) or a real hollow with raised lips, a dark inside, clay
  teeth and a tongue (o, cry, scream, laugh, grimace). The jaw shape key drops her chin with the open ones.
- Cheeks push up for a smile (shape key). Tears pool under the dots and run down. pale drains her skin.
Positions come from a flat front photo of her face (measured once): see MEASURED."""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, Matrix

# measured on the flat front render of haru_full at the kit size (12.6 cm), rig at rest: x, z in metres
MOUTH_AT = (0.0004, 0.1031, 0.0019)   # where the sculpted mouth sits: lower than her painted one, as on the sheet
MEASURED = dict(eye=(0.0050, 0.1100, 0.0012), brow=(0.0057, 0.1137, 0.0024, 0.0009), mouth=(0.0004, 0.1037, 0.0019),
                skin=(0.894, 0.673, 0.556))

# brows: (inner z, outer z, arch, pinch toward the nose, thickness) in metres, relative to the measured brow line.
# inner high + outer low = sad. A pair is (her right, her left); one entry = both sides the same.
BROWS = {   # (inner z, outer z, arch, pinch, thickness, where the arch peaks 0 inner .. 1 outer)
    'neutral':   [(0.0002, -0.0003, 0.0006, 0.0000, 1.0, 0.45)],
    'sad':       [(0.0012, -0.0012, 0.0005, 0.0003, 1.05, 0.3)],
    'uneasy':    [(0.0010, -0.0010, 0.0005, 0.0002, 1.0, 0.3), (0.0003, -0.0002, 0.0005, 0.0000, 1.0, 0.45)],
    'worried':   [(0.0013, -0.0011, 0.0003, 0.0006, 1.05, 0.28)],
    'scared':    [(0.0014, 0.0003, 0.0008, 0.0002, 1.0, 0.4)],
    'crying':    [(0.0013, -0.0013, 0.0006, 0.0004, 1.1, 0.28)],
    'terrified': [(0.0016, 0.0002, 0.0009, 0.0004, 1.05, 0.35)],
    'soft':      [(0.0003, -0.0001, 0.0006, 0.0000, 0.95, 0.45)],
    'up':        [(0.0007, 0.0003, 0.0007, 0.0000, 1.0, 0.45)],
    'tight':     [(-0.0004, 0.0001, 0.0002, 0.0004, 1.1, 0.5)],
    'low':       [(-0.0001, -0.0004, 0.0004, 0.0000, 1.0, 0.5)],
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
        self._subdivide()
        self._paint_out()
        self.M = dict(dark=_mat('face_dark', (0.006, 0.005, 0.005), rough=0.3, gloss=True),
                      brow=_mat('brow_clay', (0.035, 0.03, 0.029), rough=0.6),
                      inside=_mat('mouth_inside', (0.025, 0.004, 0.005), rough=1.0),
                      tongue=_mat('mouth_tongue', (0.3, 0.07, 0.07), rough=0.55),
                      crease=_mat('mouth_crease', (0.035, 0.01, 0.009), rough=0.6),
                      teeth=_mat('teeth', (0.78, 0.76, 0.71), rough=0.6),
                      lip=_mat('lip_line', (0.09, 0.025, 0.022), rough=0.55),
                      rim=_mat('lip_rim', (0.3, 0.1, 0.08), rough=0.6),
                      tear=_mat('tear', (0.85, 0.9, 0.95), rough=0.05, gloss=True))
        self._shape_keys()
        self._eyes(); self._brows(); self._mouth(); self._tears(); self._pallor(); self._mouth_shader()

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
                   (bx, bz, bw * 1.15, bh * 1.15), (mx, mz, mw * 1.7, 0.0013)]
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
        R = 4                                                           # a wider ring: catches the paint's last dark texels
        ring = np.zeros_like(mask)
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                ring |= np.roll(np.roll(mask, dy, 0), dx, 1)
        ring &= ~mask
        rgb = px[..., :3].copy(); lum = rgb @ [0.2126, 0.7152, 0.0722]
        ref = np.median(lum[ring]) if ring.any() else 0.6
        bad = ring & ((lum < 0.42) | (lum < ref - 0.08) | (rgb[..., 0] - rgb[..., 1] > 0.3))   # dark or red paint left at the rim
        hole = mask | bad
        skin = rgb[ring & ~bad]
        col = np.median(skin, axis=0) if len(skin) > 20 else np.array(self.skin_rgb, np.float32)
        # fill each patch from its edges inward until it settles (a membrane fill), on a crop so it is quick:
        # the patch takes on the skin's own baked shading around it instead of a flat, lighter average
        def blobs(idx, gap=40):                                         # split the patches apart (two face islands)
            out = []
            ys, xs = idx
            order = np.argsort(xs); xs, ys = xs[order], ys[order]
            cuts = np.where(np.diff(xs) > gap)[0] + 1
            for gx, gy in zip(np.split(xs, cuts), np.split(ys, cuts)):
                o2 = np.argsort(gy); gx, gy = gx[o2], gy[o2]
                c2 = np.where(np.diff(gy) > gap)[0] + 1
                out += list(zip(np.split(gy, c2), np.split(gx, c2)))
            return out
        for ys, xs in blobs(np.where(hole)):
            y0, y1 = max(0, ys.min() - 3), min(h, ys.max() + 4); x0, x1 = max(0, xs.min() - 3), min(w, xs.max() + 4)
            sub = rgb[y0:y1, x0:x1]; hm = hole[y0:y1, x0:x1]
            sub[hm] = col
            for _ in range(3000):
                avg = (np.roll(sub, 1, 0) + np.roll(sub, -1, 0) + np.roll(sub, 1, 1) + np.roll(sub, -1, 1)) / 4
                sub[hm] = avg[hm]
            rgb[y0:y1, x0:x1] = sub
        noise = np.random.default_rng(3).normal(0, 0.004, (int(hole.sum()), 1)).astype(np.float32)
        px[hole, :3] = rgb[hole] + noise
        mask = hole
        img.pixels.foreach_set(px.ravel()); img.update(); img.pack()
        self.skin_rgb = tuple(float(v) for v in col)
        print(f'FACE paint-out: {int(mask.sum())} texels filled with skin {np.round(col, 3)}', flush=True)

    # ---------------------------------------------------------------- shape keys: jaw and cheeks
    def _shape_keys(self):
        ob = self.body; me = ob.data
        if not me.shape_keys: ob.shape_key_add(name='Basis', from_mix=False)
        mx, mz, mw = MOUTH_AT; ex, ez, er = MEASURED['eye']
        co = np.array([v.co[:] for v in me.vertices])
        x, y, z = co[:, 0], co[:, 1], co[:, 2]
        front = y < -0.003
        # jaw: everything below the mouth line drops and tucks back; full at the chin, nothing at the lips' corners
        import cast_kit as CK
        fc = CK._face_colours(ob); lum = fc @ [0.2126, 0.7152, 0.0722]
        skin_f = (lum > 0.42) & (fc[:, 0] > fc[:, 1]) & (fc[:, 0] - fc[:, 2] < 0.45)    # her skin, not the hoodie collar
        skinv = np.zeros(len(co)); fv = np.zeros(len(co))
        for p, ok in zip(me.polygons, skin_f):
            for vi in p.vertices: fv[vi] += 1; skinv[vi] += ok
        skinv = (skinv / np.maximum(fv, 1)) ** 2
        below = np.clip((mz - z) / 0.0035, 0, 1) * np.clip(1 - (np.abs(x - mx) / 0.009) ** 2, 0, 1) * front * np.clip((z - (mz - 0.0095)) / 0.0025, 0, 1) * skinv   # the chin moves, the neck stays
        k = ob.shape_key_add(name='jaw', from_mix=False); k.value = 0.0; d = np.zeros_like(co)   # new keys start at 1 in Blender 5
        d[:, 2] = -0.0026 * below; d[:, 1] = 0.0005 * below
        k.data.foreach_set('co', (co + d).ravel())
        # cheeks: round pads under the eyes push up and out
        k = ob.shape_key_add(name='cheeks', from_mix=False); k.value = 0.0; d = np.zeros_like(co)   # new keys start at 1 in Blender 5
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
    def _brow_pts(self, sd, zi, zo, arch, pinch, peak=0.45, n=25):
        """a rolled clay brow like the sheet's: a smooth arc, round at both ends, a little fuller toward the nose"""
        bw = MEASURED['brow'][2]; L = bw * 1.05; pts, rad = [], []
        for i in range(n):
            u = i / (n - 1)                                            # 0 = inner end (toward the nose), 1 = outer
            x = -sd * (L - 2 * L * u) - sd * pinch * (1 - 0.5 * u)
            z = zi + (zo - zi) * u + arch * math.sin(math.pi * u ** (math.log(0.5) / math.log(peak)))   # arch peaking at 'peak'
            pts.append((x, 0, z))
            end = min(u, 1 - u) / 0.12                                 # rounded ends
            rad.append((1.0 - 0.18 * u) * (0.45 + 0.55 * math.sqrt(min(1.0, end))))
        return pts, rad

    def _brows(self):
        bx, bz, bw, bh = MEASURED['brow']; self.brows = []
        for side, (sd, tag) in enumerate(((-1, 'R'), (1, 'L'))):
            e = self.frame(f'{self.name}_brow.{tag}', sd * (bx - 0.0004), bz - 0.0011)   # skin between brow and fringe, like the sheet
            S = {}
            for k, spec in BROWS.items():
                zi, zo, arch, pinch, th, peak = spec[side] if len(spec) > 1 else spec[0]
                r = bh * 0.56 * th
                pts, rad = self._brow_pts(sd, zi, zo, arch, pinch, peak)
                pts = self.bend(e, pts, 0.0)
                xs = np.array([p[0] for p in pts]); ys = np.array([p[1] for p in pts])
                ys = np.polyval(np.polyfit(xs, ys, 2), xs) - r * 0.55            # smooth depth (no clay wobble), mostly proud
                pts = [(p[0], float(y), p[2]) for p, y in zip(pts, ys)]
                ob = _curve(f'brow_{k}.{tag}', pts, r, self.M['brow'], self.coll, radii=rad)
                ob.data.bevel_resolution = 5; ob.data.resolution_u = 3
                S[k] = self._kid(ob, e)
            self.brows.append(dict(root=e, sd=sd, set=S))

    # ---------------------------------------------------------------- mouths: sculpted into her clay
    # Her face is refined around the mouth, then each mouth is a shape key that sculpts her own skin clay: a pressed
    # groove with rolled lips for the closed ones, a real hollow with raised lips for the open ones (its inside darkens
    # through a vertex mask), with clay teeth and a tongue inside. Like the sheet, crying and terrified also crease the
    # cheeks and bunch the chin.
    BOX = (0.0088, 0.0955, 0.1061)                                     # |x|, z min, z max of the refined patch

    def _subdivide(self, levels=4):
        me = self.body.data; bx, z0, z1 = self.BOX
        inbox = lambda co: abs(co.x) < bx and z0 < co.z < z1 and co.y < -0.002
        bm = bmesh.new(); bm.from_mesh(me); n0 = len(bm.verts)
        for _ in range(levels):
            faces = [f for f in bm.faces if all(inbox(v.co) for v in f.verts)]
            edges = list({e for f in faces for e in f.edges})
            bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True, smooth=0.0)   # smoothing here scratches her cheeks
        bm.verts.ensure_lookup_table()
        edge = {v for f in bm.faces if not all(inbox(x.co) for x in f.verts) for v in f.verts}   # the patch's rim stays put
        new = [v for v in bm.verts[n0:] if v not in edge]              # relax only the new points: her own stay put
        for _ in range(6): bmesh.ops.smooth_vert(bm, verts=new, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        # her model has a little mouth crease sculpted where the painted mouth was: smooth it away (the mouths are ours)
        omx, omz, omw = MEASURED['mouth']
        old = [v for v in bm.verts if v not in edge and v.co.y < -0.004 and ((v.co.x - omx) / (omw * 1.9)) ** 2 + ((v.co.z - omz) / 0.0011) ** 2 < 1]
        for _ in range(25): bmesh.ops.smooth_vert(bm, verts=old, factor=0.5, use_axis_x=False, use_axis_y=True, use_axis_z=False)
        bm.to_mesh(me); bm.free(); me.update()
        # the fine clay noise (pits, small lumps) would scratch the dense patch: fade it out there, keep the thumb dents
        co = np.array([v.co[:] for v in me.vertices])
        out = np.maximum.reduce([np.abs(co[:, 0]) - bx, z0 - co[:, 2], co[:, 2] - z1, co[:, 1] + 0.002])   # > 0 outside the patch
        w = np.clip(out / 0.0018, 0.0, 1.0)                         # none on the dense patch, back to full 1.8 mm out
        vg = self.body.vertex_groups.new(name='face_soft')
        for i, wi in enumerate(w): vg.add([i], float(wi), 'REPLACE')
        for md in self.body.modifiers:
            if md.type == 'DISPLACE' and ('pits' in md.name or 'fine' in md.name): md.vertex_group = 'face_soft'
        print(f'FACE refined: {len(me.vertices)} verts', flush=True)

    @staticmethod
    def _seg(P, poly, closed):
        """distance from points P (N,2) to a polyline; the arc-length fraction and side (+1 above / left) of the nearest"""
        A = poly if not closed else poly
        B = np.roll(poly, -1, 0) if closed else poly[1:]
        A = A if closed else poly[:-1]
        AB = B - A; L = np.maximum((AB ** 2).sum(1), 1e-18)
        t = np.clip(((P[:, None, :] - A[None]) * AB[None]).sum(2) / L[None], 0, 1)
        Q = A[None] + t[..., None] * AB[None]; d = np.sqrt(((P[:, None, :] - Q) ** 2).sum(2))
        j = d.argmin(1); i = np.arange(len(P))
        seg_len = np.sqrt(L); cum = np.concatenate([[0], np.cumsum(seg_len)])
        frac = (cum[j] + t[i, j] * seg_len[j]) / cum[-1]
        cr = AB[j, 0] * (P[:, 1] - A[j, 1]) - AB[j, 1] * (P[:, 0] - A[j, 0])
        return d[i, j], frac, np.sign(cr)

    @staticmethod
    def _inside(P, poly):
        x, z = P[:, 0], P[:, 1]; ins = np.zeros(len(P), bool)
        for a, b in zip(poly, np.roll(poly, -1, 0)):
            c = (a[1] > z) != (b[1] > z)
            xi = (b[0] - a[0]) * (z - a[1]) / np.where(b[1] == a[1], 1e-12, b[1] - a[1]) + a[0]
            ins ^= c & (x < xi)
        return ins

    def _mouth(self):
        mx, mz, mw = MOUTH_AT; ob = self.body; me = ob.data
        e = self.frame(f'{self.name}_mouth', mx, mz); self.mouth_root = e; M = self.M
        co = np.array([v.co[:] for v in me.vertices]); nr = np.array([v.normal[:] for v in me.vertices])
        bx, z0, z1 = self.BOX
        reg = np.where((np.abs(co[:, 0]) < bx + 0.001) & (co[:, 2] > z0 - 0.001) & (co[:, 2] < z1) & (co[:, 1] < -0.002))[0]
        P = np.stack([co[reg, 0] - mx, co[reg, 2] - mz], 1)
        mm = 0.001
        ss = lambda a, b, x: np.clip((x - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((x - a) / (b - a), 0, 1))
        g = lambda x, w: np.exp(-(x / w) ** 2)
        sq = lambda u: math.sqrt(max(0.0, 1 - u * u))
        U = [2 * i / 40 - 1 for i in range(41)]

        def creases(disp, reach, depth=0.12):                    # nose-to-mouth-corner folds (terrified, crying)
            for sd in (-1, 1):
                pl = np.array([(sd * (0.0024 + 0.0018 * s ** 1.3 * reach), 0.0020 - 0.0032 * s) for s in np.linspace(0, 1, 12)])
                d, fr, _ = self._seg(P, pl, False)
                disp -= depth * mm * g(d, 0.18 * mm) * np.sin(np.pi * np.clip(fr, 0, 1)) ** 0.6

        # sizes measured off the sheet (mw = 1.9 mm): closed mouths are one clean groove with soft lips either side
        LINES = dict(                                               # pts, groove mm, lower lip mm, upper lip mm
            line=([(u * mw * 0.75, -mw * 0.02 * (1 - u * u)) for u in U], 0.16, 0.1, 0.05),
            frown=([(u * mw * 1.2, -mw * 0.45 + mw * 0.8 * (1 - u * u) ** 0.8) for u in U], 0.22, 0.26, 0.08),
            wavy=([(u * mw * 1.85, mw * 0.14 * math.sin(math.pi * 1.4 * (u + 1)) - mw * 0.1 * u) for u in U], 0.22, 0.34, 0.3),
            pressed=([(u * mw * 2.1, mw * 0.08 * math.sin(math.pi * 2.4 * (u + 1)) + mw * 0.05 * (1 - u * u)) for u in U], 0.24, 0.34, 0.3),
            smile=([(u * mw * 1.35, mw * 0.18 - mw * 0.36 * (1 - u * u)) for u in U], 0.2, 0.14, 0.05))
        OPENS = dict(                                               # half width, top(u), bottom(u), depth mm, lip mm
            o=(mw * 0.82, lambda u: -mw * 0.05 + mw * 0.36 * sq(u), lambda u: -mw * 0.05 - mw * 0.5 * sq(u), 0.9, 0.3),
            cry=(mw * 1.75, lambda u: -mw * 0.8 + mw * 1.3 * (1 - u * u) ** 0.6, lambda u: -mw * 0.8 - mw * 0.32 * (1 - u * u), 1.3, 0.36),
            scream=(mw * 1.5, lambda u: -mw * 0.1 + mw * 0.85 * sq(u) ** 0.5, lambda u: -mw * 0.1 - mw * 1.15 * sq(u) ** 0.7, 1.8, 0.34),
            laugh=(mw * 1.4, lambda u: mw * 0.1 * (1 - u * u), lambda u: -mw * 0.7 * (1 - u * u) ** 0.8, 0.9, 0.22),
            grimace=(mw * 1.5, lambda u: mw * 0.22 * (1 - u ** 4), lambda u: -mw * 0.22 * (1 - u ** 4), 0.6, 0.2))
        if not me.shape_keys: ob.shape_key_add(name='Basis', from_mix=False)
        self.mouth = {}; self.mouth_parts = {}
        for k, (pts, G, Lh, Lu) in LINES.items():
            pts = [(x * 1.25, z * 1.15) for x, z in pts]               # the sheet's closed mouths are a quarter wider
            pl = np.array(pts); d, fr, side = self._seg(P, pl, False)
            taper = np.clip(np.sin(np.pi * fr), 0, 1) ** 0.35
            disp = -G * 0.5 * mm * g(d, 0.1 * mm) * taper                 # a soft seam where the lips meet
            disp += np.where(side < 0, Lh * 0.7 * g(d - 0.3 * mm, 0.38 * mm), Lu * 0.8 * g(d - 0.2 * mm, 0.3 * mm)) * mm * taper ** 0.6   # soft lips, no hard edge
            for end in (pl[0], pl[-1]):                             # dimples at the corners
                disp -= 0.08 * mm * g(np.sqrt(((P - end) ** 2).sum(1)), 0.16 * mm)
            if k == 'pressed':                                      # short worried creases off the corners
                for end, sd in ((pl[0], -1), (pl[-1], 1)):
                    c2 = np.array([end, end + [sd * 0.3 * mm, -0.5 * mm]]); d2, f2, _ = self._seg(P, c2, False)
                    disp -= 0.08 * mm * g(d2, 0.1 * mm)
            dark = 0.35 * g(d, 0.2 * mm) * taper                       # a soft shadow; the crisp line is a clay crease below
            self._mouth_key(k, reg, nr, disp, dark)
            self.keys = me.shape_keys.key_blocks
            kb = self.keys['m_' + k]; kb.value = 1.0
            lp = self.bend(e, [(x, 0, z) for x, z in pts], -0.02 * mm)  # pressed into the seam
            kb.value = 0.0
            xs = np.array([q[0] for q in lp]); ys = np.array([q[1] for q in lp])
            ys = np.convolve(np.pad(ys, 4, mode='edge'), np.ones(9) / 9, mode='valid') - 0.03 * mm   # smooth: no in-and-out specks
            lp = [(q[0], float(y), q[2]) for q, y in zip(lp, ys)]
            tp = [math.sin(math.pi * i / (len(lp) - 1)) ** 0.5 for i in range(len(lp))]
            cr = _curve(f'mouth_{k}_crease', lp, 0.23 * mm, M['crease'], self.coll, radii=[0.35 + 0.65 * t for t in tp])
            cr.data.bevel_resolution = 4; cr.data.twist_mode = 'Z_UP'
            sp = cr.data.splines[0]; sp.type = 'NURBS'; sp.order_u = 4; sp.use_endpoint_u = True   # one smooth stroke
            self.mouth_parts[k] = [self._kid(cr, e)]
        for k, (w, top, bot, D, Lh) in OPENS.items():
            ol = np.array(_outline(top, bot, w, n=28)); d, fr, _ = self._seg(P, ol, True)
            ins = self._inside(P, ol); sd_ = np.where(ins, d, -d)          # signed: inside +
            zc = (top(0.0) + bot(0.0)) / 2
            lower = 1.0 + (0.7 if k == 'cry' else 0.4) * ss(0.3 * mm, -0.5 * mm, P[:, 1] - zc)   # a fuller lower lip (smooth, no step)
            hollow = D * mm * ss(-0.04 * mm, 0.65 * mm, sd_)                   # the lips roll in, then straight back into her head
            disp = Lh * mm * lower * g(sd_ + 0.16 * mm, 0.4 * mm)          # broad soft lips that roll into the mouth
            if k in ('cry', 'scream'):
                creases(disp, 1.0 if k == 'scream' else 1.3)
                chin = np.sqrt((P[:, 0] / 1.3) ** 2 + (P[:, 1] - (bot(0.0) - 0.8 * mm)) ** 2)
                disp += (0.18 if k == 'cry' else 0.08) * mm * g(chin, 0.6 * mm)       # the chin bunches up
            dark = ss(0.12 * mm, 0.5 * mm, sd_)
            self._mouth_key(k, reg, nr, disp, dark, hollow)
            self._mouth_parts(k, e, w, top, bot)
        self.keys = me.shape_keys.key_blocks

    def _mouth_key(self, k, reg, nr, disp, dark, hollow=None):
        ob = self.body; me = ob.data
        co = np.empty(len(me.vertices) * 3); me.shape_keys.key_blocks['Basis'].data.foreach_get('co', co); co = co.reshape(-1, 3)
        key = ob.shape_key_add(name='m_' + k, from_mix=False); key.value = 0.0   # new keys start at 1 in Blender 5
        co[reg, 1] -= disp                                              # straight out of her face (her normals crumple here)
        if hollow is not None: co[reg, 1] += hollow
        key.data.foreach_set('co', co.ravel())
        a = me.attributes.get('mk_' + k) or me.attributes.new('mk_' + k, 'FLOAT', 'POINT')
        v = np.zeros(len(me.vertices)); v[reg] = np.clip(dark, 0, 1); a.data.foreach_set('value', v)
        self.mouth[k] = True

    def _jaw_shift(self, x, z, jaw):
        mx, mz, mw = MOUTH_AT
        below = min(1, max(0, (mz - z) / 0.0035)) * max(0, 1 - ((x - mx) / 0.009) ** 2) * min(1, max(0, (z - (mz - 0.0095)) / 0.0025))
        return Vector((0, 0.0005 * below * jaw, -0.0026 * below * jaw))

    def _keep(self, ob, e):
        ob.parent = e; ob.matrix_parent_inverse = e.matrix_world.inverted(); return ob

    def _mouth_parts(self, k, e, w, top, bot):
        """clay teeth (wide flat bands, like the sheet) and a tongue inside an open mouth"""
        mx, mz, mw = MOUTH_AT; M = self.M; parts = []; jaw = MOUTHS[k]['jaw']; mm = 0.001
        Bw = self.body.matrix_world
        def at(x, z, inward, lower):
            p, n = self.surf(mx + x, mz + z)
            q = p + Vector((0, inward, 0))                             # straight back, like the hollow
            if lower: q = q + self._jaw_shift(mx + x, mz + z, jaw)
            return Bw @ q
        def band(name, edge, th, down, ext, inward, lower=False):
            n = 17; us = [ext * (2 * i / (n - 1) - 1) for i in range(n)]
            bm = bmesh.new(); A, B = [], []
            for u in us:
                rnd = (1 - (u / ext) ** 6) ** 0.5                         # rounded ends
                z0 = edge(u); z1 = z0 + (-th if down else th) * (0.35 + 0.65 * rnd)
                A.append(bm.verts.new(at(u * w, z0, inward, lower))); B.append(bm.verts.new(at(u * w, z1, inward, lower)))
            for i in range(n - 1): bm.faces.new((A[i], A[i + 1], B[i + 1], B[i]))
            me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
            ob = bpy.data.objects.new(name, me); self.coll.objects.link(ob); me.materials.append(M['teeth'])
            for p in me.polygons: p.use_smooth = True
            so = ob.modifiers.new('thick', 'SOLIDIFY'); so.thickness = 0.14 * mm; so.offset = 0.0
            sb = ob.modifiers.new('round', 'SUBSURF'); sb.levels = 2; sb.render_levels = 2
            return self._keep(ob, e)
        teeth = MOUTHS[k].get('teeth')
        ext = {'scream': 0.55, 'cry': 0.5, 'laugh': 0.6, 'grimace': 0.75}.get(k, 0.6)
        th = (0.2 if k == 'grimace' else 0.3) * mw
        flat = lambda f: (lambda u: 0.35 * f(u) + 0.65 * f(0.0))       # teeth sit in a straighter row than the lips
        if teeth:
            tf = flat(top) if k in ('scream', 'cry') else top
            parts.append(band(f'teeth_{k}', lambda u: tf(u) - 0.1 * mw, th, True, ext, 0.3 * mm))
        if teeth == 'both':
            bf = flat(bot) if k == 'scream' else bot
            parts.append(band(f'teeth_b_{k}', lambda u: bf(u) + 0.12 * mw, th * 0.8, False, ext * 0.9, 0.3 * mm, lower=True))
        if k in ('cry', 'scream'):                                      # a tongue low in the opening
            z = bot(0.0) + mw * (0.35 if k == 'cry' else 0.55)
            tg = _ball(f'tongue_{k}', 1.0, M['tongue'], self.coll)
            tg.data.transform(Matrix.Diagonal((w * 0.45, 0.3 * mm, mw * 0.28, 1.0)))   # size in the mesh: set() keys the object scale
            tg.location = at(0.0, z, (0.8 if k == 'cry' else 1.1) * mm, True)
            parts.append(self._keep(tg, e))
        self.mouth_parts[k] = parts

    def _mouth_shader(self):
        """the dark inside of each mouth: its vertex mask times a keyed value, over her skin colour"""
        self.mouth_vals = {k: [] for k in self.mouth}
        for m in self.body.data.materials:
            nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            src = b.inputs['Base Color'].links[0].from_socket; acc = None
            for k in self.mouth:
                at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'mk_' + k
                v = nt.nodes.new('ShaderNodeValue'); v.outputs[0].default_value = 0.0; self.mouth_vals[k].append(v)
                mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
                nt.links.new(at.outputs['Fac'], mul.inputs[0]); nt.links.new(v.outputs[0], mul.inputs[1])
                if acc is None: acc = mul
                else:
                    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; ad.use_clamp = True
                    nt.links.new(acc.outputs[0], ad.inputs[0]); nt.links.new(mul.outputs[0], ad.inputs[1]); acc = ad
            mx_ = nt.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'
            nt.links.new(acc.outputs[0], mx_.inputs['Factor']); nt.links.new(src, mx_.inputs[6])
            mx_.inputs[7].default_value = (0.03, 0.006, 0.006, 1)
            nt.links.new(mx_.outputs[2], b.inputs['Base Color'])

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
        for k in self.mouth:                                           # swap in this expression's sculpted mouth
            on = 1.0 if k == X['mouth'] else 0.0
            kb = self.keys['m_' + k]; kb.value = on; kb.keyframe_insert('value', frame=f)
            for v in self.mouth_vals[k]: v.outputs[0].default_value = on; v.outputs[0].keyframe_insert('default_value', frame=f)
            for ob in self.mouth_parts.get(k, []):
                ob.scale = (1, 1, 1) if on else (HIDE,) * 3; ob.keyframe_insert('scale', frame=f)
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
