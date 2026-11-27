"""Haru, our own clay style (the Artlist turnaround, YTB/channel_art/haru_turnaround_sheet.png), back from the Burton detour.

Matte plasticine everywhere: warm tan skin, small glossy black dot eyes, thin dark brows, a small round nose, a simple
mouth; a soft mustard hoodie with a thick rolled collar, long drawstrings and a kangaroo pocket; straight charcoal
trousers; white sneakers with light grey soles; long straight black hair as one solid clay mass (a rounded crown,
a fringe swept across the forehead, flat panels framing the face and a broad slab down the back).

Same rig and interface as the other puppets (pivots root, hips, spine, chest, neck, head, upper_arm/forearm/hand,
thigh/shin/foot .L/.R), so the mocap retargeter, the contact solver and the room scenes drive it unchanged:
    import haru_clay as HC; h = HC.HaruClay(loc=(0, 0, 0)); h.pose({...}); h.ground(); h.expr('scared'); h.key(f)
The hair is a single piece bent by a two-bone armature (crown on the head, ends on the chest), so it never splits.
"""
import bpy, math, os, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import haru_puppet as HP
from haru_puppet import Shape, piece, arc, soft_rest, S, CV
import claylib as C

# ---------------------------------------------------------------- proportions (1.26 m units, x0.1 when built)
HEAD_C, HEAD_R = Vector((0, 0, 1.06)), Vector((0.134, 0.115, 0.14))   # round, wide face like the sheet
SH = Vector((0.12, 0.01, 0.835)); A_REST = math.radians(11); L_UP, L_FORE = 0.175, 0.17
HEM = 0.50
EYE_X, EYE_Z = 0.048, 1.045

PAL = {'hoodie': '#d29a36', 'skin': '#e59c74', 'pants': '#55565b', 'hair': '#1c1d20', 'shoe': '#eceae6',
       'sole': '#c8c6c2', 'mouth': '#7a3a2c', 'mouth_in': '#3a1411', 'brow': '#2a2220', 'white': '#f4f2ec'}

EXPR = HP.EXPR          # eyes variant, brow tilt, brow lift, mouth variant
EYES, MOUTHS = HP.EYES, HP.MOUTHS


def on_face(x, z, lift=0.0):
    """point (1.26 m units) on the front of the head at (x, z), and the outward normal"""
    u, w = x / HEAD_R.x, (z - HEAD_C.z) / HEAD_R.z
    y = HEAD_C.y - HEAD_R.y * math.sqrt(max(0.0, 1 - u * u - w * w))
    p = Vector((x, y, z))
    n = Vector(((x - HEAD_C.x) / HEAD_R.x ** 2, (y - HEAD_C.y) / HEAD_R.y ** 2, (z - HEAD_C.z) / HEAD_R.z ** 2)).normalized()
    return p + n * lift, n


def hair_shape():
    """long straight hair as one clay mass, shaped after the turnaround's front, side and back views"""
    s = Shape()
    s.ellipsoid((0, 0.04, 1.09), (0.152, 0.132, 0.165))                     # crown over the skull, set back: face open
    s.ellipsoid((0, 0.03, 1.16), (0.145, 0.125, 0.1))                       # fuller top
    for sd in (1, -1):                                                      # flat panels framing the face to the collar
        s.ellipsoid((sd * 0.142, 0.04, 0.99), (0.036, 0.09, 0.16))
        s.ellipsoid((sd * 0.144, 0.045, 0.86), (0.036, 0.08, 0.07))         # rounded ends resting on the shoulders
    s.ellipsoid((0, 0.075, 0.96), (0.16, 0.07, 0.2))                      # broad slab down the back
    s.ellipsoid((0, 0.08, 0.81), (0.155, 0.05, 0.055))                        # its rounded lower edge
    s.ellipsoid((0.02, -0.075, 1.185), (0.12, 0.028, 0.04), rot=(math.radians(-30), math.radians(8), 0))   # fringe, high
    s.ellipsoid((0.095, -0.06, 1.145), (0.045, 0.028, 0.05), rot=(math.radians(-20), 0, 0))  # swept down at her left temple
    s.ellipsoid((-0.06, -0.07, 1.18), (0.06, 0.028, 0.032), rot=(math.radians(-34), 0, 0))   # parted high on her right
    return s


# ---------------------------------------------------------------- THE Haru clay (one recipe for every Haru, built or imported)
# Every Haru on the channel gets her materials from here: the code puppet (HaruClay) and any imported model
# (an Artlist GLB, a sculpt) through apply_haru_clay(). Change her look here and only here.
LOOK = {'hoodie': dict(sss=0.06, bump=0.7),
        'pants': dict(sss=0.04, bump=0.7),
        'skin': dict(rough=0.8, sss=0.12, bump=0.85, prints=1.2),
        'hair': dict(rough=0.7, sss=0.03, bump=0.6, prints=0.4, grooves=0.3, specks=0, film=0.2),
        'shoe': dict(sss=0.08, bump=0.5, specks=1.2),
        'sole': dict(bump=0.5),
        'mouth': dict(bump=0.2, prints=0, specks=0),
        'mouth_in': dict(bump=0.2, prints=0, specks=0),
        'brow': dict(bump=0.25, prints=0, specks=0),
        'white': dict(rough=0.6, sss=0.05, bump=0.2, prints=0, specks=0)}
LUMPS = dict(dents=0.0009, pits=0.00016, lumps=0.00016)      # shape imperfections for a 12.6 cm Haru (haru_puppet.piece)


def haru_materials(name='haru'):
    """the full set of Haru clay materials, named '<name>_<part>'"""
    M = {k: CV.clay(f'{name}_{k}', PAL[k], **kw) for k, kw in LOOK.items()}
    M['eye'] = CV.clay(f'{name}_eye', (0.012, 0.01, 0.01), gloss=True)
    return M


# where each part can be on a standing Haru (fraction of her height from the soles): painted textures shade hair grey
# and trousers dark, so colour alone mixes them up
BAND = {'hair': (0.62, 1.0), 'skin': (0.3, 1.0), 'hoodie': (0.3, 0.86), 'pants': (0.03, 0.5),
        'shoe': (0.0, 0.12), 'sole': (0.0, 0.05)}


def _srgb(c):
    return tuple((v * 12.92) if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055 for v in c[:3])


def _nearest(rgb, keys):
    """palette part whose sRGB colour is closest to rgb (sRGB 0..1), weighted toward lightness so tan vs mustard holds"""
    def hx(h): h = h.lstrip('#'); return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    def d(a, b): return 2.0 * (a[0] - b[0]) ** 2 + 4.0 * (a[1] - b[1]) ** 2 + 1.5 * (a[2] - b[2]) ** 2
    return min(keys, key=lambda k: d(rgb, hx(PAL[k])))


def apply_haru_clay(objects, name='haru', mapping=None, keys=('hoodie', 'skin', 'pants', 'hair', 'shoe', 'sole'),
                    lumps=True, height=None):
    """Give an imported Haru (Artlist GLB etc.) exactly the channel clay. Every face is sorted into a part (skin, hoodie,
    hair...) by its painted colour: the texture sampled at the face's UVs, or the material's base colour when there is no
    texture. The painted textures are dropped and the part's HC clay material goes on instead, plus the same clay lumps
    as the code puppet. mapping={'<imported material name>': 'hair', ...} forces whole materials to a part (use 'eye'
    for the eye beads). height: her height in metres if not yet scaled (the lumps are sized for 12.6 cm).
    Returns {part: face count} so you can check the sort."""
    import bmesh
    M = haru_materials(name); mapping = mapping or {}; count = {}
    meshes = [o for o in objects if o.type == 'MESH']
    for ob in meshes:
        old = list(ob.data.materials)
        info = []                                                       # per old slot: forced part, image pixels, base colour
        for m in old:
            forced = mapping.get(m.name if m else '', None) or mapping.get((m.name if m else '').split('.')[0], None)
            img, base = None, (0.5, 0.5, 0.5)
            if m and m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type != 'BSDF_PRINCIPLED': continue
                    bc = n.inputs['Base Color']; base = _srgb(bc.default_value)
                    stack = [l.from_node for l in bc.links]             # the colour texture, not the normal map
                    while stack and img is None:
                        s = stack.pop()
                        if s.type == 'TEX_IMAGE' and s.image: img = s.image
                        else: stack += [l.from_node for i in s.inputs for l in i.links]
            px = None
            if img is not None and img.size[0] > 0:
                import numpy as np
                px = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32); img.pixels.foreach_get(px)
                px = (px.reshape(img.size[1], img.size[0], 4), img.colorspace_settings.name.lower().startswith('srgb'))
            info.append((forced, px, base))
        bm = bmesh.new(); bm.from_mesh(ob.data); uv = bm.loops.layers.uv.active
        z0 = min(v.co.z for v in bm.verts); zh = max(max(v.co.z for v in bm.verts) - z0, 1e-9)
        parts = []
        for f in bm.faces:
            zf = (f.calc_center_median().z - z0) / zh                   # 0 at her soles, 1 at the top of her hair
            allowed = [p for p in keys if BAND.get(p, (0, 1))[0] <= zf <= BAND.get(p, (0, 1))[1]] or list(keys)
            forced, px, base = info[f.material_index] if f.material_index < len(info) else (None, None, (0.5, 0.5, 0.5))
            if forced: parts.append(forced); continue
            rgb = base
            if px is not None and uv is not None:
                arr, is_srgb = px; h, w = arr.shape[:2]; acc = [0.0, 0.0, 0.0]
                for l in f.loops:                                       # average the face's corners and centre
                    u, v = l[uv].uv; c = arr[int((v % 1) * (h - 1)), int((u % 1) * (w - 1))]
                    for i in range(3): acc[i] += c[i]
                rgb = [a / len(f.loops) for a in acc]
                if not is_srgb: rgb = _srgb(rgb)
            parts.append(_nearest(rgb, allowed))
        bm.free()
        used = sorted(set(parts)); slot = {p: i for i, p in enumerate(used)}
        ob.data.materials.clear()                                       # (clearing resets the face indices: set them after)
        for p in used: ob.data.materials.append(M[p])
        ob.data.polygons.foreach_set('material_index', [slot[p] for p in parts]); ob.data.update()
        for p in parts: count[p] = count.get(p, 0) + 1
        if lumps:
            k = 1.0 if height is None else height / 0.126
            CV.geometry(ob, **{a: v * k for a, v in LUMPS.items()})
    return count


class HaruClay(HP.Haru):
    def _materials(self):
        return haru_materials(self.name)

    # ---- body
    def _build(self):
        M, co = self.M, self.coll
        s = Shape()                                                         # hoodie body: soft, roomy, rounded
        s.ellipsoid((0, 0.012, 0.75), (0.14, 0.088, 0.14)); s.ellipsoid((0, 0, 0.63), (0.16, 0.097, 0.14))
        s.ellipsoid((0, 0, HEM + 0.06), (0.162, 0.097, 0.065)); s.ring((0, 0, HEM + 0.027), 0.153, 0.088, 0.024, 44)
        s.ring((0, 0.012, 0.915), 0.088, 0.078, 0.05, 26, tilt=0.6)       # thick rolled collar, low at the front
        s.ellipsoid((0, 0.08, 0.86), (0.1, 0.034, 0.08))                    # hood folded on the back
        s.ellipsoid((0, -0.09, 0.6), (0.1, 0.022, 0.058))                   # kangaroo pocket
        for side in (1, -1): s.ball((side * 0.108, 0.01, 0.795), 0.064)     # shoulders
        self._attach(piece('hoodie', s, M['hoodie'], 'top', co, cuts=[(HEM, 'above')], smooth=8), 'spine')
        s = Shape()
        for side in (1, -1):                                                # long drawstrings with knotted ends
            s.capsule((side * 0.024, -0.075, 0.875), (side * 0.03, -0.1, 0.76), 0.0068); s.ball((side * 0.03, -0.1, 0.752), 0.011)
        self._attach(piece('drawstrings', s, M['hoodie'], 'top', co, voxel=0.0016, smooth=3, lump=0.00006), 'chest', False)
        s = Shape().ellipsoid((0, 0, 0.58), (0.138, 0.097, 0.08))
        self._attach(piece('pelvis', s, M['pants'], 'pants', co, cuts=[(HEM + 0.045, 'below')]), 'hips')
        self._attach(piece('neck', Shape().capsule((0, 0.012, 0.84), (0, 0.012, 0.97), 0.042), M['skin'], 'skin', co,
                           voxel=0.003, smooth=4, lump=0.0001), 'neck')
        s = Shape().ellipsoid(HEAD_C, HEAD_R, seg=48)
        for sd in (1, -1): s.ellipsoid((sd * 0.133, 0.01, 1.04), (0.012, 0.02, 0.028))   # ears, hidden under the hair
        self._attach(piece('head', s, M['skin'], 'skin', co, voxel=0.003, lump=0.00012), 'head')
        for side, tag in ((1, 'L'), (-1, 'R')):
            d = Vector((side * math.sin(A_REST), 0, -math.cos(A_REST)))
            sh = Vector((side * SH.x, SH.y, SH.z)); el = sh + d * L_UP; wr = el + d * L_FORE
            s = Shape().capsule(sh, el, 0.064, 0.061).fold(sh, el, 0.62, 0.062, 0.012, 0.008, seed=1 + side)
            self._attach(piece('sleeve_up.' + tag, s, M['hoodie'], 'top', co), 'upper_arm.' + tag)
            s = Shape().capsule(el, wr - d * 0.012, 0.061, 0.06).ball(wr - d * 0.03, 0.063)
            for k, t in enumerate((0.12, 0.45, 0.72)):                      # the sleeve bunches toward the cuff
                s.fold(el, wr, t, 0.06, 0.012 + 0.002 * k, 0.008, seed=10 * k + side)
            self._attach(piece('sleeve_lo.' + tag, s, M['hoodie'], 'top', co), 'forearm.' + tag)
            out = Vector((math.cos(A_REST), 0, math.sin(A_REST))) if side > 0 else Vector((-math.cos(A_REST), 0, math.sin(A_REST)))
            Mx = Matrix((out, Vector((0, -1, 0)), -d)).transposed()
            P = lambda u, v, w: wr + Mx @ Vector((u, v, w))
            s = Shape().capsule(P(0, 0, 0.02), P(0, 0, -0.012), 0.022, 0.021).ellipsoid(P(0, 0, -0.038), (0.02, 0.035, 0.037), rot=Mx)
            for vy in (-0.022, -0.0073, 0.0073, 0.022):
                ln = 0.032 if abs(vy) < 0.01 else 0.026
                s.capsule(P(0.001, vy, -0.062), P(-0.008, vy * 1.05, -0.062 - ln), 0.009, 0.0082, 16)
            s.capsule(P(-0.007, -0.029, -0.028), P(-0.018, -0.04, -0.058), 0.0097, 0.009, 16)
            self._attach(piece('hand.' + tag, s, M['skin'], 'skin', co, voxel=0.0015, smooth=5, lump=0.00006), 'hand.' + tag)
            hip, knee, ank = Vector((side * 0.062, 0, 0.55)), Vector((side * 0.063, 0, 0.30)), Vector((side * 0.064, 0.005, 0.075))
            s = Shape().capsule(hip, knee, 0.06, 0.056).fold(hip, knee, 0.9, 0.056, 0.017, 0.01, seed=20 + side)
            self._attach(piece('thigh.' + tag, s, M['pants'], 'pants', co), 'thigh.' + tag)
            s = Shape().capsule(knee, ank, 0.056, 0.055)
            for k, t in enumerate((0.7, 0.88)):                             # the trousers bunch over the shoe
                s.fold(knee, ank, t, 0.055, 0.016 + 0.003 * k, 0.012, seed=30 + k + side)
            self._attach(piece('shin.' + tag, s, M['pants'], 'pants', co, cuts=[(0.062, 'above')]), 'shin.' + tag)
            x = side * 0.072                                                # low white sneakers, rounded toes
            s = Shape().ellipsoid((x, -0.028, 0.044), (0.054, 0.094, 0.042)).ellipsoid((x, -0.077, 0.033), (0.052, 0.05, 0.03))
            s.capsule((side * 0.068, 0.005, 0.058), (side * 0.068, 0.005, 0.082), 0.046)
            self._attach(piece('shoe.' + tag, s, M['shoe'], 'shoes', co, voxel=0.003, smooth=5, cuts=[(0.018, 'above')]), 'foot.' + tag)
            self._attach(piece('sole.' + tag, Shape().ellipsoid((x, -0.03, 0.016), (0.059, 0.103, 0.019)), M['sole'], 'shoes', co,
                               voxel=0.003, smooth=4, lump=0.00008, cuts=[(0.0, 'above')]), 'foot.' + tag)
        hair = piece('hair', hair_shape(), M['hair'], 'hair', co, voxel=0.0035, smooth=8, lump=0.00016)
        def w_head(z):                                                      # crown on the head, ends on the chest
            t = min(1.0, max(0.0, (z / S - 0.9) / 0.1)); return t * t * (3 - 2 * t)
        self._skin(hair, w_head)
        soft_rest(hair); self.soft.append(hair)

    def _skin(self, ob, w_head):
        """bend a piece between the head and chest pivots with a two-bone armature whose bones follow the pivots"""
        bpy.context.view_layer.update()
        ad = bpy.data.armatures.new(f'{self.name}_rig'); rig = bpy.data.objects.new(f'{self.name}_rig', ad)
        self.coll.objects.link(rig); rig.hide_render = True
        bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
        for pv in ('head', 'chest'):
            b = ad.edit_bones.new(pv); b.head = self.rest[pv]; b.tail = self.rest[pv] + Vector((0, 0, 0.01))
        bpy.ops.object.mode_set(mode='OBJECT')
        for pv in ('head', 'chest'):
            c = rig.pose.bones[pv].constraints.new('CHILD_OF'); c.target = self.P[pv]
            c.inverse_matrix = self.P[pv].matrix_world.inverted(); c.set_inverse_pending = False
        gh, gc = ob.vertex_groups.new(name='head'), ob.vertex_groups.new(name='chest')
        for v in ob.data.vertices:
            w = w_head(v.co.z)
            if w > 0: gh.add([v.index], w, 'REPLACE')
            if w < 1: gc.add([v.index], 1 - w, 'REPLACE')
        md = ob.modifiers.new('rig', 'ARMATURE'); md.object = rig; md.use_vertex_groups = True   # after the clay marks, so they stay put
        self.rig = rig

    # ---- face: dot eyes and replacement parts swapped by scale (the sheet's simple face)
    def _face(self):
        M, co = self.M, self.coll
        self.eyes = {v: [] for v in EYES}; self.mouths = {}; self.brows = []; self.eye_holders = []
        def holder(name, at):
            e = bpy.data.objects.new(f'{self.name}_{name}', None); co.objects.link(e)
            e.location = Vector(at) * S; e.empty_display_size = 0.002
            self._attach(e, 'head', False)
            return e
        def put(ob, h):
            bpy.context.view_layer.update(); ob.parent = h; ob.matrix_parent_inverse = h.matrix_world.inverted(); return ob
        for side, tag in ((1, 'L'), (-1, 'R')):
            ex = side * EYE_X; p, n = on_face(ex, EYE_Z)
            R = n.to_track_quat('-Y', 'Z').to_matrix()
            def bead(nm, r, at=None, mat=None):
                return piece(nm, Shape().ellipsoid(at or p - n * 0.002, r, rot=R), mat or M['eye'], 'skin', co, voxel=0.0008, smooth=3, lump=0)
            h = holder(f'eye_open.{tag}', p); put(bead(f'eye_bead.{tag}', (0.0118, 0.0062, 0.0128)), h); self.eyes['open'].append(h)
            h = holder(f'eye_half.{tag}', p); put(bead(f'eye_halfbead.{tag}', (0.0118, 0.005, 0.0058), at=p - n * 0.002 - Vector((0, 0, 0.003))), h)
            put(arc(f'eye_halflid.{tag}', [on_face(ex + k * 0.013, EYE_Z + 0.003 + 0.0015 * (1 - k * k), 0.002)[0] for k in (-1, -0.5, 0, 0.5, 1)],
                    0.0028, M['skin'], co), h); self.eyes['half'].append(h)
            h = holder(f'eye_closed.{tag}', p)
            put(arc(f'eye_lid.{tag}', [on_face(ex + k * 0.013, EYE_Z - 0.002 - 0.004 * (1 - k * k), 0.0015)[0] for k in (-1, -0.5, 0, 0.5, 1)],
                    0.0024, M['brow'], co), h); self.eyes['closed'].append(h)
            h = holder(f'eye_happy.{tag}', p)
            put(arc(f'eye_up.{tag}', [on_face(ex + k * 0.013, EYE_Z - 0.004 + 0.005 * (1 - k * k), 0.0015)[0] for k in (-1, -0.5, 0, 0.5, 1)],
                    0.0024, M['brow'], co), h); self.eyes['happy'].append(h)
            h = holder(f'eye_wide.{tag}', p)
            put(piece(f'eye_white.{tag}', Shape().ellipsoid(p - n * 0.0006, (0.0205, 0.0028, 0.022), rot=R), M['white'], 'skin', co,
                      voxel=0.0008, smooth=3, lump=0), h)
            put(bead(f'eye_pupil.{tag}', (0.0068, 0.004, 0.0072), at=p + n * 0.0014), h); self.eyes['wide'].append(h)
            bc = on_face(side * 0.05, 1.095, 0.0005)[0]
            h = holder(f'brow.{tag}', bc); h.rotation_mode = 'YXZ'
            put(arc(f'brow_arc.{tag}', [on_face(side * x_, 1.095 + 0.002 * (1 - ((x_ - 0.05) / 0.02) ** 2), 0.0005)[0]
                                         for x_ in (0.03, 0.04, 0.05, 0.06, 0.07)], 0.0034, M['brow'], co), h)
            self.brows.append((h, side, bc))
        p, n = on_face(0, 0.995, 0.004)
        self._attach(piece('nose', Shape().ellipsoid(p, (0.011, 0.0095, 0.0102), seg=24), M['skin'], 'skin', co,
                           voxel=0.0008, smooth=3, lump=0), 'head', False)
        MZ = 0.955
        mc, mn = on_face(0, MZ, 0.0005)
        R = mn.to_track_quat('-Y', 'Z').to_matrix()
        def mline(nm, curve):
            return arc(nm, [on_face(x_, MZ + curve * (x_ / 0.014) ** 2, 0.0005)[0] for x_ in (-0.014, -0.007, 0, 0.007, 0.014)],
                       0.0024, M['mouth'], co)
        for v, ob in (('line', mline('mouth_line', 0.0)), ('smile', mline('mouth_smile', 0.0045)), ('frown', mline('mouth_frown', -0.0038))):
            h = holder(f'mouth_{v}', mc); put(ob, h); self.mouths[v] = h
        for v, r, dz in (('o', (0.0065, 0.004, 0.0085), 0.0), ('scream', (0.021, 0.005, 0.026), -0.012)):
            h = holder(f'mouth_{v}', mc)
            put(piece(f'mouth_{v}_in', Shape().ellipsoid(mc + Vector((0, 0, dz)) - mn * 0.001, r, rot=R), M['mouth_in'], 'skin', co,
                      voxel=0.0008, smooth=3, lump=0), h)
            self.mouths[v] = h

    def expr(self, name, blink=False, gaze=None):
        """swap eyes, mouth and brows; gaze (yaw, pitch deg) slides the dot eyes a little across the face"""
        HP.Haru.expr(self, name, blink=blink)
        gx, gz = gaze or (0, 0)
        for hs in self.eyes.values():
            for h in hs: h.delta_location = (gx * 0.00009 * S, 0, -gz * 0.00007 * S)   # + yaw looks to her left, + pitch down

    def key(self, f):
        HP.Haru.key(self, f)
        for hs in self.eyes.values():
            for h in hs: h.keyframe_insert('delta_location', frame=f)


class ClayRake:
    """The clay key: one small warm light that skims across Haru's face from the side, so the dents, thumbprints and
    hair grooves throw tiny shadows and she reads as plasticine (soft head-on light makes her look like a smooth ball).
    Use it on close-ups and mediums only; wide and "something is wrong" shots stay dark. It is always motivated: it comes
    from the side where a real source is (a lamp, a candle, a window, a phone), never from nowhere.
        rake = HC.ClayRake()                       # once, after the set is built
        rake.aim(f, head, cam.location, src, on)   # every frame: head = her head point, src = the motivating source
    energy 0.22 W at 6 cm, 1.8 cm above her head point, is the channel default: texture shows, her hair stays black
    and her face keeps a dark side (0.5 W already greys the hair and washes the hoodie)."""

    def __init__(self, energy=0.22, color=(1.0, 0.7, 0.42), size=0.012, dist=0.06, lift=0.018):
        self.energy, self.dist, self.lift = energy, dist, lift
        self.ob = C.area_light('clay_rake', (0, 0, 0), (0, 0, -1), 0.0, size, color)

    def aim(self, f, head, cam_loc, src, on=True):
        head, cam_loc, src = Vector(head), Vector(cam_loc), Vector(src)
        view = (head - cam_loc).normalized()
        side = src - head; side -= view * side.dot(view)              # only the sideways part: it must rake, not face her
        if side.length < 1e-6: side = view.cross(Vector((0, 0, 1)))
        side.normalize()
        L = self.ob; L.location = head + side * self.dist + Vector((0, 0, self.lift)) - view * 0.012
        C.look_at(L, head)
        L.data.energy = self.energy if on else 0.0
        L.keyframe_insert('location', frame=f); L.keyframe_insert('rotation_euler', frame=f)
        L.data.keyframe_insert('energy', frame=f)
