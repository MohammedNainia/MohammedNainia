"""pixkit: volumetric pixel art in code (numpy + Pillow only).

Build a sprite from solid primitives (each pixel gets a depth z and a surface normal), light it with one key light
plus a rim light, quantise the light into hand-made colour ramps (hue-shifted), then clean up like a pixel artist:
selective outlines, interior contour lines between overlapping parts, orphan-pixel removal. Then run qa() before
showing anything.

    from pixkit import *
    s = Sprite(64, 96)
    s.ellipsoid('skin', 32, 20, 7, 8)                    # head
    s.capsule('cloth', (32, 30), (32, 60), 10, 13)       # torso
    s.render(light=(-0.6, -0.7, 0.4)).save('out.png', scale=6)
    print(qa(s.img))
"""
import colorsys, math
import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------------------------------- colour ramps
def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def rgbhex(c): return '#%02x%02x%02x' % tuple(int(v) for v in c)

def ramp(base, n=6, hue_shift=22, light_range=(0.10, 0.80), sat_curve=(1.15, 0.85)):
    """Hue-shifted ramp from deep shadow to highlight around a base colour.
    Shadows drift toward blue/purple and get more saturated; highlights drift toward yellow and desaturate.
    This is what keeps pixel art from looking muddy (never just 'darker' and 'lighter' of one hue)."""
    r, g, b = [v / 255 for v in hexrgb(base)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    out = []
    for i in range(n):
        k = i / (n - 1)                                    # 0 shadow .. 1 highlight
        hh = h * 360
        # move toward 240 (blue) in shadow, toward 60 (yellow) in light, along the shorter way round the wheel
        def toward(a, target, amt):
            d = ((target - a + 540) % 360) - 180; return a + d * amt
        hh = toward(hh, 250, (1 - k) * hue_shift / 90) if k < .5 else toward(hh, 55, (k - .5) * 2 * hue_shift / 90)
        ll = light_range[0] + (light_range[1] - light_range[0]) * (k ** .9) * (0.55 + l * .9)
        ss = min(1, s * (sat_curve[0] + (sat_curve[1] - sat_curve[0]) * k))
        rr, gg, bb = colorsys.hls_to_rgb((hh % 360) / 360, min(.97, ll), ss)
        out.append((int(rr * 255), int(gg * 255), int(bb * 255)))
    return out

# ---------------------------------------------------------------------------------------------------- the sprite
class Sprite:
    def __init__(self, w, h, ramps=None):
        self.w, self.h = w, h
        self.mat = np.full((h, w), -1, np.int16)          # material id per pixel (-1 empty)
        self.z = np.full((h, w), -1e9)                     # depth (towards viewer is +)
        self.n = np.zeros((h, w, 3)); self.n[..., 2] = 1   # surface normal
        self.part = np.full((h, w), -1, np.int32)          # which primitive drew this pixel (for contour lines)
        self.flat = np.zeros((h, w), bool)                 # unlit pixels (emissive: eyes, flames, glass)
        self.names, self.ramps = [], []
        self._pid = 0
        for k, v in (ramps or {}).items(): self.material(k, v)
        Y, X = np.mgrid[0:h, 0:w]; self.X, self.Y = X + .5, Y + .5

    def material(self, name, ramp_or_base):
        r = ramp_or_base if isinstance(ramp_or_base, list) else ramp(ramp_or_base)
        r = [hexrgb(c) if isinstance(c, str) else tuple(c) for c in r]
        if name in self.names: self.ramps[self.names.index(name)] = r
        else: self.names.append(name); self.ramps.append(r)
        return self

    def _mid(self, name):
        if name not in self.names: raise KeyError(f'unknown material {name}; add it with material()')
        return self.names.index(name)

    def _put(self, name, mask, z, nx, ny, nz, flat=False, z0=0.0):
        z = z + z0
        m = mask & (z > self.z)
        mid = self._mid(name); self._pid += 1
        self.mat[m] = mid; self.z[m] = z[m]; self.part[m] = self._pid; self.flat[m] = flat
        nn = np.stack([nx, ny, nz], -1); nn /= np.linalg.norm(nn, axis=-1, keepdims=True) + 1e-9
        self.n[m] = nn[m]
        return self

    # ---- primitives (all take z0: how far toward the viewer the part sits; bigger draws in front)
    def ellipsoid(self, name, cx, cy, rx, ry, depth=None, z0=0, flat=False):
        depth = depth or min(rx, ry)
        u, v = (self.X - cx) / rx, (self.Y - cy) / ry; q = 1 - u * u - v * v; m = q > 0
        w = np.sqrt(np.clip(q, 0, 1))
        return self._put(name, m, w * depth, u / rx, v / ry, w / depth, flat, z0)

    def capsule(self, name, p0, p1, r0, r1=None, z0=0, flat=False):
        """A rounded limb / torso / column from p0 to p1, radius r0 -> r1 (tapers)."""
        r1 = r0 if r1 is None else r1
        (x0, y0), (x1, y1) = p0, p1; dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy + 1e-9
        t = np.clip(((self.X - x0) * dx + (self.Y - y0) * dy) / L2, 0, 1)
        px, py = x0 + t * dx, y0 + t * dy; r = r0 + (r1 - r0) * t
        ox, oy = self.X - px, self.Y - py; d2 = ox * ox + oy * oy; m = d2 < r * r
        w = np.sqrt(np.clip(1 - d2 / (r * r), 0, 1))
        return self._put(name, m, w * r, ox / r, oy / r, w, flat, z0)

    def poly(self, name, pts, bevel=2.0, z0=0, flat=False, tilt=(0, 0)):
        """A flat panel (cloth, wall, blade, roof) with a bevelled rim so its edges catch light like real form.
        tilt=(tx, ty) leans the whole panel (e.g. a roof plane facing up: tilt=(0,-.6))."""
        m = _poly_mask(self.w, self.h, pts)
        d = _dist_inside(m)                                 # distance to the edge, in pixels
        k = np.clip(d / max(bevel, .01), 0, 1)
        gx, gy = np.gradient(-d); g = np.hypot(gx, gy) + 1e-9
        edge = (1 - k)
        nx = gx / g * edge + tilt[0]; ny = gy / g * edge + tilt[1]; nz = np.ones_like(d) * (.6 + .4 * k)
        return self._put(name, m, k * bevel * .5, nx, ny, nz, flat, z0)

    def box(self, name, x, y, w, h, bevel=1.5, z0=0, flat=False):
        return self.poly(name, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], bevel, z0, flat)

    def cone(self, name, apex, base_c, base_r, z0=0):
        """Spikes, hats, horns, roof finials: a cone from apex down to a round base."""
        return self.capsule(name, apex, base_c, .4, base_r, z0)

    def arch(self, name, cx, y_bottom, w, h, kind='round', thick=3, bevel=1.5, z0=0, hole_mat=None):
        """Architecture: an arch frame. kind = 'round' | 'pointed' (gothic) | 'horseshoe' (Moroccan) | 'ogee' | 'flat'.
        Draws the frame; if hole_mat is given, also fills the opening with that (flat) material behind it."""
        outer = arch_path(cx, y_bottom, w + 2 * thick, h + thick, kind)
        inner = arch_path(cx, y_bottom, w, h, kind)
        mo, mi = _poly_mask(self.w, self.h, outer), _poly_mask(self.w, self.h, inner)
        if hole_mat: self._put(hole_mat, mi, np.full(mi.shape, -.5), *np.zeros((2,) + mi.shape), np.ones(mi.shape), True, z0)
        ring = mo & ~mi
        d = np.minimum(_dist_inside(mo), _dist_inside(~mi & np.ones_like(mo)))
        k = np.clip(d / bevel, 0, 1); gx, gy = np.gradient(-d); g = np.hypot(gx, gy) + 1e-9
        return self._put(name, ring, k * bevel * .5, gx / g * (1 - k), gy / g * (1 - k), .6 + .4 * k, False, z0 + .5)

    def pattern(self, name, mask_fn, z0=.2, flat=False, on=None):
        """Inlay / tiles / embroidery / folds: paint material where mask_fn(X, Y) is True, keeping the surface normals.
        on='material' restricts it to pixels that currently show that material (e.g. folds only on the robe)."""
        m = mask_fn(self.X, self.Y) & (self.mat >= 0)
        if on is not None: m &= self.mat == self._mid(on)
        mid = self._mid(name); self.mat[m] = mid; self.flat[m] = flat
        return self

    def pixels(self, name, pts, flat=True):
        """Hand-placed pixels (eyes, sparkles, stitches): [(x, y), ...]."""
        mid = self._mid(name)
        for x, y in pts:
            if 0 <= x < self.w and 0 <= y < self.h: self.mat[y, x] = mid; self.flat[y, x] = flat; self.z[y, x] = max(self.z[y, x], 50)
        return self

    # ---- light, quantise, clean up
    def render(self, light=(-.6, -.75, .5), ambient=.18, rim=(0.75, -.2, -.3), rim_amt=.35, contour=True, outline='selective', bg=None, ramp_bias=0.0,
               key=1.0, point=None, point_amt=1.0, point_range=40.0):
        """key: strength of the directional light (lower it for night). point=(x, y, z): a local light (lantern, candle, fire)
        whose direction and falloff are computed per pixel; point_range = distance where it fades out."""
        L = np.array(light, float); L /= np.linalg.norm(L)
        R = np.array(rim, float); R /= np.linalg.norm(R)
        n = self.n
        diff = np.clip((n * L).sum(-1), 0, 1) * key
        if point is not None:
            z = np.where(self.z > -1e8, self.z, 0)
            D = np.stack([point[0] - self.X, point[1] - self.Y, point[2] - z], -1); dist = np.linalg.norm(D, axis=-1) + 1e-6
            d2 = np.hypot(point[0] - self.X, point[1] - self.Y)          # falloff measured across the picture plane
            pdiff = np.clip((n * D).sum(-1) / dist, 0, 1) * np.clip(1 - d2 / point_range, 0, 1) ** 1.3 * point_amt
            diff = np.clip(diff + pdiff, 0, 1)
        rimv = np.clip((n * R).sum(-1), 0, 1) ** 3 * rim_amt * (n[..., 2] < .6)
        I = np.clip(ambient + (1 - ambient) * diff + rimv + ramp_bias, 0, 1)
        h, w = self.h, self.w
        img = np.zeros((h, w, 4), np.uint8)
        idx = np.zeros((h, w), int)
        for mid, r in enumerate(self.ramps):
            m = self.mat == mid
            if not m.any(): continue
            k = np.clip(np.round(I * (len(r) - 1)).astype(int), 0, len(r) - 1)
            idx[m] = k[m]
        # flat (emissive) materials use their own ramp by brightness = middle-high, never shaded
        for mid, r in enumerate(self.ramps):
            m = (self.mat == mid) & self.flat; idx[m] = len(r) - 2 if len(r) > 2 else len(r) - 1
        # interior contours: where a part sits clearly in front of another, darken the pixels behind by 2 steps
        if contour:
            for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                zz = np.roll(np.roll(self.z, dy, 0), dx, 1); pp = np.roll(np.roll(self.part, dy, 0), dx, 1)
                behind = (self.mat >= 0) & (pp != self.part) & (zz > self.z + 1.5) & (pp >= 0) & ~self.flat
                idx[behind] = np.maximum(0, idx[behind] - 2)
        for mid, r in enumerate(self.ramps):
            m = self.mat == mid
            if m.any():
                rr = np.array(r, np.uint8); img[m, :3] = rr[np.clip(idx[m], 0, len(r) - 1)]; img[m, 3] = 255
        img = _remove_orphans(img)
        if outline:
            img = _outline(img, self.mat, idx, self.ramps, L, mode=outline)
        if bg is not None:
            base = bg if isinstance(bg, np.ndarray) else np.full((h, w, 3), hexrgb(bg) if isinstance(bg, str) else bg, np.uint8)
            a = img[..., 3:4] > 0; out = np.where(a, img[..., :3], base[..., :3]); img = np.dstack([out, np.full((h, w), 255, np.uint8)])
        self.img = img
        return PixelImage(img)

class PixelImage:
    def __init__(self, a): self.a = a
    def pil(self, scale=1):
        im = Image.fromarray(self.a, 'RGBA'); return im.resize((im.width * scale, im.height * scale), Image.NEAREST) if scale > 1 else im
    def save(self, path, scale=6): self.pil(scale).save(path); return self

# ---------------------------------------------------------------------------------------------------- shapes
def arch_path(cx, yb, w, h, kind='round', n=40):
    """Outline of an arch opening (bottom-left, up and over, bottom-right)."""
    hw = w / 2; pts = [(cx - hw, yb)]
    if kind == 'flat': return [(cx - hw, yb), (cx - hw, yb - h), (cx + hw, yb - h), (cx + hw, yb)]
    if kind == 'round':
        spring = yb - h + hw
        pts.append((cx - hw, spring))
        pts += [(cx - hw * math.cos(a), spring - hw * math.sin(a)) for a in np.linspace(0, math.pi, n)]
    elif kind == 'horseshoe':                              # the circle continues below its widest point, pinching in
        r = hw * 1.12; c_y = yb - h + r
        angs = np.linspace(math.pi + .45, -.45, n)
        circ = [(cx + r * math.cos(a), c_y - r * math.sin(a)) for a in angs]
        pts = [(circ[0][0], yb)] + circ + [(circ[-1][0], yb)]
        return pts
    elif kind == 'pointed':                                # gothic: two arcs meeting at a point
        r = w * .85; spring = yb - h * .45
        aT = math.acos((hw - r) / r); rise = r * math.sin(aT); sy = (yb - spring and (h - (yb - spring)) / rise)
        pts.append((cx - hw, spring))
        lc = cx - hw + r
        pts += [(lc + r * math.cos(a), spring - r * math.sin(a) * sy) for a in np.linspace(math.pi, aT, n // 2)]
        rc = cx + hw - r
        pts += [(rc + r * math.cos(a), spring - r * math.sin(a) * sy) for a in np.linspace(math.pi - aT, 0, n // 2)]
    elif kind == 'ogee':
        spring = yb - h * .55
        pts.append((cx - hw, spring))
        for t in np.linspace(0, 1, n):
            x = cx - hw + t * hw; y = spring - (h * .45) * (3 * t * t - 2 * t * t * t) - math.sin(t * math.pi) * 1.5
            pts.append((x, y))
        for t in np.linspace(0, 1, n)[1:]:
            x = cx + t * hw; y = spring - (h * .45) * (1 - (3 * t * t - 2 * t * t * t)) - math.sin(t * math.pi) * 1.5
            pts.append((x, y))
    pts.append((cx + hw, pts[-1][1])); pts.append((cx + hw, yb))
    return pts

def _poly_mask(w, h, pts):
    im = Image.new('L', (w, h), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(im).polygon([(float(x), float(y)) for x, y in pts], fill=1)
    return np.array(im, bool)

def _dist_inside(m, maxd=12):
    """Chamfer distance from each inside pixel to the edge (numpy only)."""
    d = np.where(m, maxd, 0).astype(float)
    for _ in range(maxd):
        nb = np.minimum.reduce([np.pad(d, 1, constant_values=0)[1:-1, :-2], np.pad(d, 1, constant_values=0)[1:-1, 2:],
                                np.pad(d, 1, constant_values=0)[:-2, 1:-1], np.pad(d, 1, constant_values=0)[2:, 1:-1]])
        nd = np.where(m, np.minimum(d, nb + 1), 0)
        if np.array_equal(nd, d): break
        d = nd
    return d

def _remove_orphans(img):
    """A pixel unlike all 4 neighbours, which all share one colour, is noise: take the neighbours' colour."""
    a = img.copy(); h, w = a.shape[:2]
    c = a.view(np.uint32).reshape(h, w) if a.flags['C_CONTIGUOUS'] else np.ascontiguousarray(a).view(np.uint32).reshape(h, w)
    up, dn, lf, rt = np.roll(c, 1, 0), np.roll(c, -1, 0), np.roll(c, 1, 1), np.roll(c, -1, 1)
    orphan = (c != up) & (up == dn) & (dn == lf) & (lf == rt) & ((c >> 24) > 0) & ((up >> 24) > 0)
    orphan[0, :] = orphan[-1, :] = orphan[:, 0] = orphan[:, -1] = False
    c2 = c.copy(); c2[orphan] = up[orphan]
    return c2.view(np.uint8).reshape(h, w, 4)

def _outline(img, mat, idx, ramps, L, mode='selective'):
    """Selective outline ("sel-out"): on the lit side the outline is the material's own dark shade; on the shadow side
    it goes near-black. mode='black' for a classic hard outline."""
    a = img[..., 3] > 0; h, w = a.shape
    out = img.copy()
    nb = np.zeros_like(a)
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)): nb |= np.roll(np.roll(a, dy, 0), dx, 1)
    ring = nb & ~a
    ys, xs = np.nonzero(ring)
    lx, ly = L[0], L[1]
    for y, x in zip(ys, xs):
        best = None
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and a[yy, xx] and mat[yy, xx] >= 0: best = (yy, xx, dx, dy); break
        if best is None: out[y, x] = (8, 6, 12, 255); continue
        yy, xx, dx, dy = best
        r = ramps[mat[yy, xx]]
        lit_side = (-dx * lx + -dy * ly) < 0                      # outline pixel sits on the side facing the light
        col = r[0] if (mode == 'black' or not lit_side) else r[max(0, min(1, len(r) - 1))]
        if mode == 'black' or not lit_side: col = tuple(int(v * .45) for v in r[0])
        out[y, x] = (*col, 255)
    return out

# ---------------------------------------------------------------------------------------------------- QA
def qa(img, max_colors=48):
    """Check a finished sprite (RGBA array) for the classic mistakes. Returns a dict and a list of problems."""
    a = img[..., 3] > 0; rgb = img[..., :3]
    cols = {tuple(c) for c in rgb[a]}
    c = (rgb.astype(np.int32) * [65536, 256, 1]).sum(-1); c[~a] = -1
    up, dn, lf, rt = np.roll(c, 1, 0), np.roll(c, -1, 0), np.roll(c, 1, 1), np.roll(c, -1, 1)
    orphans = int(((c >= 0) & (c != up) & (c != dn) & (c != lf) & (c != rt) & (up >= 0) & (dn >= 0) & (lf >= 0) & (rt >= 0)).sum())
    # pillow shading: brightness that only follows distance-to-edge (dark rim all round, bright centre, same on every side)
    lum = (rgb * [.3, .59, .11]).sum(-1); d = _dist_inside(a, 6)
    rim_l = lum[(d == 1)]; rim_r = None
    xs = np.nonzero(a)[1]; cx = xs.mean() if len(xs) else 0
    left_rim = lum[(d == 1) & (np.arange(a.shape[1])[None, :] < cx)]; right_rim = lum[(d == 1) & (np.arange(a.shape[1])[None, :] >= cx)]
    pillow = bool(len(left_rim) and len(right_rim) and abs(left_rim.mean() - right_rim.mean()) < 6)
    # banding: long runs where two shade steps sit side by side in parallel stair-steps (approximate: count 2-colour runs of exactly equal length)
    problems = []
    if len(cols) > max_colors: problems.append(f'{len(cols)} colours (keep under {max_colors}: merge ramps)')
    if orphans > a.sum() * .01: problems.append(f'{orphans} orphan pixels (noise): simplify clusters')
    if pillow: problems.append('possible pillow shading: both sides of the silhouette are equally dark; light must come from one side')
    return {'colors': len(cols), 'orphans': orphans, 'pixels': int(a.sum()), 'pillow_suspect': pillow}, problems

# ---------------------------------------------------------------------------------------------------- export
def save_gif(frames, path, scale=6, ms=100):
    ims = [f.pil(scale).convert('RGBA') if isinstance(f, PixelImage) else f for f in frames]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=ms, loop=0, disposal=2)

def sheet(frames, path, scale=1, cols=None):
    ims = [f.pil(scale) for f in frames]; cols = cols or len(ims); rows = (len(ims) + cols - 1) // cols
    W, H = ims[0].size; S = Image.new('RGBA', (W * cols, H * rows), (0, 0, 0, 0))
    for i, im in enumerate(ims): S.paste(im, ((i % cols) * W, (i // cols) * H))
    S.save(path)

def compose(bg_rgb, *layers):
    """Paste rendered sprites (PixelImage, x, y) onto a background array (h, w, 3) -> PixelImage."""
    out = bg_rgb.copy()
    for im, x, y in layers:
        a = im.a; h, w = a.shape[:2]
        sub = out[y:y + h, x:x + w]; m = a[:sub.shape[0], :sub.shape[1], 3] > 0
        sub[m] = a[:sub.shape[0], :sub.shape[1], :3][m]
    return PixelImage(np.dstack([out, np.full(out.shape[:2], 255, np.uint8)]))
