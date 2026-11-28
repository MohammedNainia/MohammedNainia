"""The new Haru's face (cast_kit.haru): real eyes, clay eyelids, brows, a mouth with depth, a jaw and cheeks that move
the clay, tears and pallor. Built on her Tripo head, matched to the Artlist sheet
YTB/channel_art/kit/haru_new_expressions_01a220ad-358b.png.

    face = HF.Face(c)                                    # c = cast_kit.haru(...), built while the rig is at rest
    face.set(f, 'terrified', look=(0.2, -0.1), blink=0, tears=0.6, pale=0.5, t=seconds)

How it works
- Her painted eyes, brows and mouth are painted out of her texture (filled with her own skin), so nothing is doubled.
- Each eye is a small rig on the head bone: a glossy dot bead (her neutral look), a white eyeball that grows for fear with
  a pupil that looks around, an upper lid of her skin clay that closes over it, and closed-eye curves (laugh, squeeze,
  sleep) like the sheet.
- Brows are clay strokes that tilt and lift. The mouth is a set of sculpted shapes (line, frown, o, smile, scream) with
  a dark inside and teeth, and the jaw is a shape key on her head that drops her chin, so a scream stretches the clay.
- Cheeks push up for a smile (shape key). Tears are glossy drops that run down her cheeks. pale drains her skin.
Positions come from a flat front photo of her face (measured once): see MEASURED."""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, Matrix
import clay_v3 as CV

# measured on the flat front render of haru_full at the kit size (12.6 cm), rig at rest: x, z in metres
MEASURED = dict(eye=(0.0050, 0.1100, 0.0012), brow=(0.0057, 0.1137, 0.0024, 0.0009), mouth=(0.0004, 0.1037, 0.0019),
                skin=(0.894, 0.673, 0.556))

# expression table: eyes (dot | wide | happy | squeeze | sleep), white (eyeball size when wide), pupil (scale),
# lid (0 open .. 1 shut), brow (tilt deg, + = inner ends up; lift m), mouth, jaw (0..1), cheeks (0..1)
EXPR = {
    'neutral':   dict(eyes='dot', lid=0.0, brow=(0, 0.0), mouth='line', jaw=0.0, cheeks=0.0),
    'worried':   dict(eyes='dot', lid=0.2, brow=(30, 0.0003), mouth='frown', jaw=0.1, cheeks=0.0),
    'scared':    dict(eyes='wide', white=1.0, pupil=0.55, lid=0.0, brow=(14, 0.0006), mouth='o', jaw=0.35, cheeks=0.0),
    'terrified': dict(eyes='wide', white=1.2, pupil=0.4, lid=0.0, brow=(22, 0.0009), mouth='scream', jaw=1.0, cheeks=0.2),
    'crying':    dict(eyes='dot', lid=0.45, brow=(24, 0.0003), mouth='frown', jaw=0.15, cheeks=0.1),
    'laugh':     dict(eyes='happy', lid=0.0, brow=(0, 0.0004), mouth='smile', jaw=0.5, cheeks=1.0),
    'happy':     dict(eyes='dot', lid=0.05, brow=(0, 0.0002), mouth='smile', jaw=0.2, cheeks=0.6),
    'squeeze':   dict(eyes='squeeze', lid=0.0, brow=(-16, -0.0004), mouth='grimace', jaw=0.25, cheeks=0.6),
    'stare':     dict(eyes='wide', white=1.0, pupil=0.32, lid=0.0, brow=(0, 0.0003), mouth='line', jaw=0.0, cheeks=0.0),
    'sleep':     dict(eyes='sleep', lid=0.0, brow=(0, -0.0001), mouth='line', jaw=0.0, cheeks=0.0),
}
HIDE = 1e-4


def _mat(name, rgb, rough=0.4, gloss=False, glass=False, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    if gloss: b.inputs['Coat Weight'].default_value = 0.8; b.inputs['Coat Roughness'].default_value = 0.04
    if glass:
        b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['IOR'].default_value = 1.33
        b.inputs['Roughness'].default_value = 0.02
    return m


def _curve(name, pts, r, mat, coll):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    ob = bpy.data.objects.new(name, cu); coll.objects.link(ob); ob.data.materials.append(mat)
    return ob


def _ball(name, r, mat, coll, scale=(1, 1, 1), loc=(0, 0, 0), hemi=False):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)
    if hemi: bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-9], context='VERTS')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob); me.materials.append(mat)
    ob.scale = scale; ob.location = loc
    if hemi:
        s = ob.modifiers.new('shell', 'SOLIDIFY'); s.thickness = r * 0.25
    return ob


def _arc(cx, w, h, n=9, z0=0.0):
    """points of a curve across x in [-w, w], bulging by h in z (negative h bows down), in a feature's local frame
    (y is depth: points sit just proud of the surface)"""
    return [(cx + w * (2 * i / (n - 1) - 1), -0.0002, z0 + h * (1 - (2 * i / (n - 1) - 1) ** 2)) for i in range(n)]


class Face:
    def __init__(self, c, name='haru'):
        self.c, self.rg, self.body, self.name = c, c['rig'], c['body'], name
        self.coll = bpy.data.collections.new(name + '_face'); bpy.context.scene.collection.children.link(self.coll)
        bpy.context.view_layer.update()
        self.dg = bpy.context.evaluated_depsgraph_get()
        self.skin_rgb = MEASURED['skin']
        self._paint_out()
        self.M = dict(dark=_mat('face_dark', (0.006, 0.005, 0.005), rough=0.3, gloss=True),
                      white=_mat('eye_white', (0.86, 0.85, 0.82), rough=0.25, gloss=True),
                      brow=_mat('brow_clay', (0.02, 0.018, 0.018), rough=0.8),
                      inside=_mat('mouth_inside', (0.03, 0.004, 0.004), rough=0.7),
                      teeth=_mat('teeth', (0.85, 0.83, 0.78), rough=0.35),
                      lip=_mat('lip_line', (0.32, 0.1, 0.07), rough=0.6),
                      tear=_mat('tear', (0.8, 0.88, 0.95), rough=0.05, gloss=True))
        lin = tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in self.skin_rgb)
        self.M['lid'] = CV.clay(name + '_lid_clay', lin, rough=0.8, sss=0.12, bump=0.5, prints=0.6)
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

    # ---------------------------------------------------------------- eyes
    def _eyes(self):
        ex, ez, er = MEASURED['eye']; self.eyes = []
        for sd, tag in ((-1, 'R'), (1, 'L')):                       # her right eye is on -x
            e = self.frame(f'{self.name}_eye.{tag}', sd * ex, ez)
            E = dict(root=e)
            E['dot'] = self._kid(_ball(f'eye_dot.{tag}', er * 1.1, self.M['dark'], self.coll, scale=(1, 0.6, 1)), e)
            Rw = er * 1.75
            E['white'] = self._kid(_ball(f'eye_white.{tag}', Rw, self.M['white'], self.coll, loc=(0, Rw - 0.0011, 0)), e)
            E['pupil'] = self._kid(_ball(f'eye_pupil.{tag}', er * 0.85, self.M['dark'], self.coll, scale=(1, 0.35, 1)), e)
            lid_r = Rw * 1.04
            E['lid'] = self._kid(_ball(f'eye_lid.{tag}', lid_r, self.M['lid'], self.coll, loc=(0, Rw - 0.0011, 0), hemi=True), e)
            E['lid'].rotation_mode = 'XYZ'
            E['happy'] = self._kid(_curve(f'eye_happy.{tag}', _arc(0, er * 1.25, er * 0.9, z0=-er * 0.3), er * 0.28, self.M['dark'], self.coll), e)
            E['sleep'] = self._kid(_curve(f'eye_sleep.{tag}', _arc(0, er * 1.2, -er * 0.55), er * 0.25, self.M['dark'], self.coll), e)
            sq = [(sd * -er * 1.2, -0.0002, er * 0.7), (sd * er * 0.9, -0.0002, 0.0), (sd * -er * 1.2, -0.0002, -er * 0.7)]
            E['squeeze'] = self._kid(_curve(f'eye_squeeze.{tag}', sq, er * 0.27, self.M['dark'], self.coll), e)
            E['Rw'] = Rw; E['sd'] = sd
            self.eyes.append(E)

    # ---------------------------------------------------------------- brows
    def _brows(self):
        bx, bz, bw, bh = MEASURED['brow']; self.brows = []
        for sd, tag in ((-1, 'R'), (1, 'L')):
            e = self.frame(f'{self.name}_brow.{tag}', sd * bx, bz)
            e.rotation_mode = 'XYZ'
            b = self._kid(_curve(f'brow.{tag}', _arc(0, bw * 0.85, bh * 0.5), bh * 0.55, self.M['brow'], self.coll), e)
            self.brows.append(dict(root=e, sd=sd, rest=e.location.copy(), rest_rot=e.rotation_euler.copy()))

    # ---------------------------------------------------------------- mouth
    def _mouth(self):
        mx, mz, mw = MEASURED['mouth']
        e = self.frame(f'{self.name}_mouth', mx, mz); self.mouth_root = e; M = self.M; co = self.coll
        P = dict()
        P['line'] = _curve('mouth_line', _arc(0, mw * 0.9, -mw * 0.04), mw * 0.13, M['lip'], co)
        P['frown'] = _curve('mouth_frown', _arc(0, mw * 0.8, mw * 0.28, z0=-mw * 0.15), mw * 0.14, M['lip'], co)
        P['grimace'] = _curve('mouth_grimace', _arc(0, mw * 1.05, mw * 0.18, z0=-mw * 0.1), mw * 0.2, M['inside'], co)
        # open mouths: a dark inside sunk into the clay (the face surface cuts it into an opening), teeth along the top
        P['o'] = _ball('mouth_o', mw * 0.75, M['inside'], co, scale=(0.8, 0.22, 1.0), loc=(0, 0.0, -mw * 0.2))
        P['smile'] = _ball('mouth_smile', mw * 1.0, M['inside'], co, scale=(1.0, 0.5, 0.45), loc=(0, 0.0005, -mw * 0.2))
        P['smile_teeth'] = _ball('mouth_smile_teeth', mw * 0.85, M['teeth'], co, scale=(1.0, 0.4, 0.14), loc=(0, 0.00012, mw * 0.08))
        P['scream'] = _ball('mouth_scream', mw * 1.9, M['inside'], co, scale=(0.85, 0.2, 1.35), loc=(0, 0.0001, -mw * 1.05))
        P['scream_teeth'] = _ball('mouth_scream_teeth', mw * 0.95, M['teeth'], co, scale=(1.0, 0.3, 0.17), loc=(0, -0.00012, mw * 0.3))
        for ob in P.values(): self._kid(ob, e)
        self.mouth = P
        self.mouth_sets = dict(line=('line',), frown=('frown',), grimace=('grimace',), o=('o',), smile=('smile', 'smile_teeth'),
                               scream=('scream', 'scream_teeth'))

    # ---------------------------------------------------------------- tears
    def _tears(self):
        ex, ez, er = MEASURED['eye']; self.tears = []
        for sd in (-1, 1):
            path = []
            for i in range(10):
                zz = ez - er * 1.1 - i * 0.0009; xx = sd * (ex + 0.0004 + 0.0002 * i)
                p, n = self.surf(xx, zz); path.append((p, n))
            root = self.eyes[0 if sd < 0 else 1]['root']                 # ride on the eye's frame (head bone)
            inv = root.matrix_world.inverted() @ self.rg.matrix_world
            path = [(inv @ p, (inv.to_3x3() @ n).normalized()) for p, n in path]
            drops = []
            for k in range(2):
                d = _ball(f'tear_{sd}_{k}', 0.0006, self.M['tear'], self.coll, scale=(1, 0.7, 1.5))
                self._kid(d, root); drops.append(d)
            self.tears.append(dict(path=path, drops=drops))

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
        nt = self.M['lid'].node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')   # the lids pale with her
        src = b.inputs['Base Color'].links[0].from_socket
        v = nt.nodes.new('ShaderNodeValue'); v.outputs[0].default_value = 0.0
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; nt.links.new(v.outputs[0], mx.inputs['Factor'])
        nt.links.new(src, mx.inputs[6]); mx.inputs[7].default_value = (0.5, 0.46, 0.47, 1); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
        self.pale_nodes.append(v)

    # ---------------------------------------------------------------- set an expression
    def set(self, f, name='neutral', look=(0.0, 0.0), blink=0.0, tears=0.0, pale=0.0, t=0.0):
        X = EXPR[name]; gx, gz = look
        lid = max(X.get('lid', 0.0), blink)
        for E in self.eyes:
            eyes = X['eyes']
            for k in ('dot', 'white', 'pupil', 'lid', 'happy', 'sleep', 'squeeze'):
                E[k].hide_render = False
            vis = dict(dot=eyes == 'dot', white=eyes == 'wide', pupil=eyes == 'wide', lid=eyes in ('dot', 'wide'),
                       happy=eyes == 'happy', sleep=eyes == 'sleep', squeeze=eyes == 'squeeze')
            if eyes in ('dot', 'wide') and lid > 0.97:                 # a full blink: the closed curve replaces the lid
                vis.update(sleep=True, lid=False, dot=False, white=False, pupil=False)
            for k, on in vis.items():
                ob = E[k]; base = Vector((1, 0.6, 1)) if k == 'dot' else Vector((1, 0.35, 1)) if k == 'pupil' else Vector((1, 1, 1))
                if k == 'white' and on: base = Vector((1, 1, 1)) * X.get('white', 1.0)
                if k == 'pupil' and on: base = Vector((1, 0.35, 1)) * X.get('pupil', 0.5)
                ob.scale = base if on else Vector((HIDE,) * 3)
                ob.keyframe_insert('scale', frame=f)
            Rw = E['Rw'] * X.get('white', 1.0)
            c0 = Vector((0, E['Rw'] - 0.0011, 0))
            if eyes == 'wide':                                         # the pupil sits on the white, looking
                d = Vector((gx * 0.55, -1.0, gz * 0.55)).normalized()
                E['pupil'].location = c0 + d * Rw * 1.01
                E['white'].scale = Vector((1, 1, 1)) * X.get('white', 1.0)
            else:
                E['pupil'].location = c0
            E['dot'].location = (gx * 0.0004, -0.0002, gz * 0.0004)
            E['pupil'].keyframe_insert('location', frame=f); E['dot'].keyframe_insert('location', frame=f)
            E['white'].keyframe_insert('scale', frame=f)
            # the lid: open = rolled back over the top into the head, shut = down over the front
            E['lid'].location = c0; E['lid'].scale = Vector((1, 1, 1)) * (X.get('white', 1.0) if eyes == 'wide' else 0.72)
            if not vis.get('lid'): E['lid'].scale = Vector((HIDE,) * 3)
            a0 = -75 if eyes == 'wide' else -35                        # wide eyes: the lid rolls right back out of sight
            E['lid'].rotation_euler = (math.radians(a0 + (125 - a0 - 35) * min(1.0, lid)), 0, 0)
            for a in ('location', 'scale', 'rotation_euler'): E['lid'].keyframe_insert(a, frame=f)
        tilt, lift = X['brow']
        for B in self.brows:
            # tilt about the brow's own depth axis (inner end, toward the nose, up for +tilt) and lift it
            b = B['root'].children[0]
            b.rotation_mode = 'XYZ'; b.rotation_euler = (0, math.radians(B['sd'] * tilt), 0)
            b.location = (0, 0, lift)
            b.keyframe_insert('rotation_euler', frame=f); b.keyframe_insert('location', frame=f)
        on = self.mouth_sets[X['mouth']]
        jaw = X.get('jaw', 0.0)
        for k, ob in self.mouth.items():
            vis = k in on
            s0 = {'o': (0.8, 0.6, 1.0), 'smile': (1.0, 0.5, 0.45), 'smile_teeth': (1.0, 0.4, 0.14),
                  'scream': (0.85, 0.2, 1.35), 'scream_teeth': (1.0, 0.3, 0.17), 'o': (0.8, 0.22, 1.0)}.get(k, (1, 1, 1))
            if k in ('o', 'scream', 'smile'): s0 = (s0[0], s0[1], s0[2] * (0.6 + 0.6 * jaw))
            ob.scale = s0 if vis else (HIDE,) * 3
            ob.keyframe_insert('scale', frame=f)
        if 'scream' in on:                                              # the top teeth ride the top edge of the opening
            sc_ = self.mouth['scream']; R = MEASURED['mouth'][2] * 1.9
            self.mouth['scream_teeth'].location = (0, -0.0003, sc_.location.z + R * sc_.scale.z * 0.74)
            self.mouth['scream_teeth'].keyframe_insert('location', frame=f)
        self.keys['jaw'].value = jaw; self.keys['cheeks'].value = X.get('cheeks', 0.0)
        self.keys['jaw'].keyframe_insert('value', frame=f); self.keys['cheeks'].keyframe_insert('value', frame=f)
        # tears run down in turn while tears > 0
        for T in self.tears:
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
