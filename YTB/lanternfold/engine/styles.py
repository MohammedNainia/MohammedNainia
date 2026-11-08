"""Art-style packs: restyle any rendered frame (numpy uint8 HxWx3) so the same scene can look
paper-cut, watercolour, ink wash, stained glass, chalkboard or linocut.

    from engine.styles import stylize
    frame = stylize(scene_frame, 'watercolor', t)

Set "style" in reel.json; render.py applies it to every frame. Pure numpy + Pillow (no extra installs).
"""
import numpy as np
from PIL import Image, ImageFilter

STYLES = ['paper', 'watercolor', 'ink', 'stained_glass', 'chalk', 'comic', 'manga', 'pixel', 'flat']   # 'linocut' is experimental (night skies band)
_cache = {}

def _noise(shape, scale, seed):
    """smooth value noise in [-1, 1] (upscaled random grid)"""
    key = (shape, scale, seed)
    if key not in _cache:
        h, w = shape; r = np.random.default_rng(seed)
        small = r.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
        im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        _cache[key] = np.asarray(im, np.float32) / 127.5 - 1
    return _cache[key]

def _blur(a, r):
    if a.ndim == 2: return np.asarray(Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255
    return np.asarray(Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255

def _lum(a): return a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114

def _edges(l):
    gx = np.abs(np.roll(l, -1, 1) - np.roll(l, 1, 1)); gy = np.abs(np.roll(l, -1, 0) - np.roll(l, 1, 0))
    return np.clip((gx + gy) * 2.5, 0, 1)

def _paper(shape, tone, seed=3, amt=.06):
    h, w = shape
    tex = 1 + amt * (_noise(shape, 3, seed) * .5 + _noise(shape, 40, seed + 1) * .8)
    return np.array(tone, np.float32)[None, None] * tex[..., None]

def _displace(a, amp, scale, seed):
    h, w = a.shape[:2]; dx = (_noise((h, w), scale, seed) * amp).astype(np.int32); dy = (_noise((h, w), scale, seed + 7) * amp).astype(np.int32)
    yy, xx = np.mgrid[0:h, 0:w]; return a[np.clip(yy + dy, 0, h - 1), np.clip(xx + dx, 0, w - 1)]

def watercolor(a, t):
    h, w = a.shape[:2]
    a = _displace(a, 6, 60, 11)                                   # pigment bleeding into wet paper
    soft = _blur(a, 4); soft = soft * .75 + _blur(a, 12) * .25
    l = _lum(_blur(a, 2)); e = _edges(_blur(l, 3))[..., None]
    g = soft.mean(2, keepdims=True); soft = np.clip(g + (soft - g) * 1.35, 0, 1)
    wash = 1 - (1 - soft) * .9                                     # transparent, lighter washes
    wash = wash * (1 - .5 * e)                                     # darker pigment pooled at edges
    gran = 1 + .05 * _noise((h, w), 2, 5)[..., None] + .04 * _noise((h, w), 90, 6)[..., None]
    return np.clip(wash * gran * _paper((h, w), (1.0, .98, .94), 21, .05), 0, 1)

def ink(a, t):
    h, w = a.shape[:2]; l = _lum(_blur(a, 1.5))
    dark = np.clip((0.62 - l) / 0.5, 0, 1) ** 0.9                   # how much ink
    dark = _displace(dark[..., None], 4, 30, 13)[..., 0]
    wash = _blur(dark, 6) * .55 + dark * .45
    dry = np.clip(_noise((h, w), 2, 17) * .5 + .75, 0, 1)            # dry-brush breakup
    e = np.clip(_edges(_blur(l, 2)) * 1.8, 0, 1) * dry
    inkc = np.array([.10, .10, .12], np.float32)
    paper = _paper((h, w), (.94, .90, .82), 31, .06)
    out = paper * (1 - (wash * .85 + e * .9)[..., None].clip(0, 1)) + inkc * (wash * .85 + e * .9)[..., None].clip(0, 1)
    warm = np.clip(_lum(a) - .82, 0, 1)[..., None] * 3              # keep the light sources as a faint gold
    out = out * (1 - warm * .4) + np.array([.92, .72, .35]) * warm * .4
    s = int(w * .07); x0, y0 = w - s - 48, h - s - 300               # red seal stamp
    out[y0:y0 + s, x0:x0 + s] = out[y0:y0 + s, x0:x0 + s] * .2 + np.array([.72, .13, .1]) * .8
    return np.clip(out, 0, 1)

def _voronoi(h, w, n, seed):
    key = ('vor', h, w, n, seed)
    if key not in _cache:
        r = np.random.default_rng(seed); sh, sw = h // 4, w // 4
        pts = np.stack([r.uniform(0, sh, n), r.uniform(0, sw, n)], 1).astype(np.float32)
        yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32); best = np.full((sh, sw), 1e9, np.float32); idx = np.zeros((sh, sw), np.int32)
        for i, (py, px) in enumerate(pts):
            d = (yy - py) ** 2 + (xx - px) ** 2; m = d < best; best[m] = d[m]; idx[m] = i
        idx = np.asarray(Image.fromarray(idx.astype(np.int32)).resize((w, h), Image.NEAREST))
        lead = (idx != np.roll(idx, 1, 0)) | (idx != np.roll(idx, 1, 1))
        lead = np.asarray(Image.fromarray((lead * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), np.float32) / 255
        _cache[key] = (idx, lead)
    return _cache[key]

def stained_glass(a, t):
    h, w = a.shape[:2]; idx, lead = _voronoi(h, w, 1400, 41); n = idx.max() + 1
    flat = idx.ravel(); cnt = np.bincount(flat, minlength=n).clip(1)
    col = np.stack([np.bincount(flat, a[..., c].ravel(), n) / cnt for c in range(3)], 1)
    g = col.mean(1, keepdims=True); col = np.clip(g + (col - g) * 1.6, 0, 1) ** .85     # richer glass colours
    out = col[idx]
    out = out * (1 + .12 * _noise((h, w), 6, 43)[..., None])                           # glass texture
    bloom = _blur(np.clip(out - .55, 0, 1), 18); out = 1 - (1 - out) * (1 - bloom * .8)
    out = out * (1 - lead[..., None] * .85) + np.array([.04, .04, .05]) * lead[..., None]
    det = _blur(np.clip(_edges(_lum(a)) * 3, 0, 1), 3)[..., None].clip(0, 1) ** .7   # keep people/boats readable
    return np.clip(out * (1 - det * .75) + a * det * .75, 0, 1)

def chalk(a, t):
    h, w = a.shape[:2]
    board = np.array([.16, .25, .21], np.float32)[None, None] * (1 + .08 * _noise((h, w), 140, 51)[..., None] + .06 * _noise((h, w), 2, 52)[..., None])
    l = _lum(_blur(a, 1)); e = _edges(_blur(l, 1.5))
    grain = np.clip(_noise((h, w), 1, 53) * .8 + .55, 0, 1)
    lines = np.clip(e * 3.0, 0, 1) * grain
    fillc = 1 - (1 - a) * .45; fill = np.clip(_lum(a) * 1.1, 0, 1)[..., None] * grain[..., None] * .8
    yy, xx = np.mgrid[0:h, 0:w]; hatch = (np.sin((xx + yy) * .35) > .6).astype(np.float32)[..., None]
    out = board * (1 - fill * hatch) + fillc * fill * hatch
    return np.clip(out * (1 - lines[..., None]) + np.array([.95, .95, .9]) * lines[..., None], 0, 1)

def linocut(a, t):
    h, w = a.shape[:2]; b = _blur(a, 1.5); l = _lum(b)
    ink_c = np.array([.09, .09, .14], np.float32); paper_c = np.array([.95, .91, .82], np.float32)
    q = np.round(np.clip(b * 1.15, 0, 1) * 3) / 3                       # few flat colour blocks, hues kept
    g = q.mean(2, keepdims=True); q = np.clip(g + (q - g) * 1.2, 0, 1) * .9
    yy, xx = np.mgrid[0:h, 0:w]
    carve = (np.sin((yy + 18 * _noise((h, w), 120, 62)) * .28) > .2).astype(np.float32)[..., None]
    out = q.copy()
    dark = (l < .16)[..., None]; shade = ((l >= .16) & (l < .26))[..., None]
    out = np.where(dark, ink_c, out); out = np.where(shade, ink_c * carve + q * (1 - carve), out)
    e = _edges(_blur(l, 1.2)) > .22; out[e] = ink_c
    out = np.where((l > .8)[..., None], paper_c, out)
    return np.clip(out * _paper((h, w), (1, 1, 1), 63, .06), 0, 1)


# ---------- comic / manga / pixel / flat ----------
def _posterize(a, levels):
    return np.round(a * (levels - 1)) / (levels - 1)

def _outline(l, thr, grow=3):
    e = (_edges(_blur(l, 1.2)) > thr).astype(np.uint8) * 255
    return np.asarray(Image.fromarray(e).filter(ImageFilter.MaxFilter(grow)), np.float32) / 255

def comic(a, t):
    """bold ink outlines, flat punchy colours, halftone dots in the shadows, panel border"""
    h, w = a.shape[:2]; b = _blur(a, 2.0); l = _lum(b)
    g = b.mean(2, keepdims=True); flat = np.clip(g + (b - g) * 1.6, 0, 1)
    flat = _posterize(np.clip(flat * 1.15 + .04, 0, 1), 6) * .55 + np.clip(flat * 1.1, 0, 1) * .45   # punchy but no rings
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); cell = 9.0
    cx = (xx % cell) - cell / 2; cy = (yy % cell) - cell / 2; r = np.sqrt(cx * cx + cy * cy)
    rad = np.clip((0.55 - l) / 0.55, 0, 1) * cell * .62               # bigger dots where darker
    dots = (r < rad).astype(np.float32)[..., None]
    out = flat * (1 - dots * .55)
    ol = _outline(l, .16, 3)[..., None]
    out = out * (1 - ol) + np.array([.06, .05, .08]) * ol
    m = 26; out[:m] = out[-m:] = 1; out[:, :m] = out[:, -m:] = 1        # white gutter + black panel frame
    out[m:m + 6, m:-m] = out[-m - 6:-m, m:-m] = 0; out[m:-m, m:m + 6] = out[m:-m, -m - 6:-m] = 0
    return np.clip(out, 0, 1)

def manga(a, t):
    """black and white: screentone shading, crisp ink lines, paper white highlights"""
    h, w = a.shape[:2]; l = _lum(_blur(a, 1.5))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (xx + yy) / np.sqrt(2); v = (xx - yy) / np.sqrt(2); cell = 7.0
    r = np.sqrt(((u % cell) - cell / 2) ** 2 + ((v % cell) - cell / 2) ** 2)
    tone_rad = np.clip((0.62 - l) / 0.45, 0, 1) * cell * .7
    tone = (r < tone_rad).astype(np.float32)
    solid = (l < .12).astype(np.float32)
    hatch = ((np.sin((xx - yy) * .9) > .55) & (l < .3)).astype(np.float32)
    ink = np.clip(tone + solid + hatch * .8, 0, 1)
    ol = _outline(l, .14, 3)
    ink = np.clip(ink + ol, 0, 1)
    glow = np.clip((_lum(a) - .8) * 5, 0, 1)                            # lights become paper-white
    ink = ink * (1 - glow)
    paper = np.array([.97, .96, .93], np.float32); inkc = np.array([.05, .05, .06], np.float32)
    out = paper * (1 - ink[..., None]) + inkc * ink[..., None]
    return np.clip(out * _paper((h, w), (1, 1, 1), 71, .03), 0, 1)

PIX_PAL = np.array([[13, 10, 30], [32, 28, 70], [58, 54, 120], [96, 88, 170], [52, 90, 140], [90, 140, 190], [160, 200, 230],
                    [246, 240, 220], [255, 214, 120], [240, 150, 70], [200, 90, 80], [130, 60, 90], [70, 120, 80], [120, 180, 110],
                    [200, 170, 140], [150, 110, 90]], np.float32) / 255
_BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - .5

def pixel(a, t, px=6):
    """retro pixel art: low resolution, 16-colour palette, ordered dithering, crisp upscale"""
    h, w = a.shape[:2]; sh, sw = h // px, w // px
    small = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((sw, sh), Image.BOX), np.float32) / 255
    g = small.mean(2, keepdims=True); small = np.clip(g + (small - g) * 1.3, 0, 1)
    d = np.tile(_BAYER, (sh // 4 + 1, sw // 4 + 1))[:sh, :sw][..., None] * .09
    q = np.clip(small + d, 0, 1)
    dist = ((q[:, :, None, :] - PIX_PAL[None, None]) ** 2).sum(-1); idx = dist.argmin(-1)
    out = PIX_PAL[idx]
    return np.asarray(Image.fromarray((out * 255).astype(np.uint8)).resize((w, h), Image.NEAREST), np.float32) / 255

def flat(a, t):
    """clean flat-vector cartoon. The scene is rendered with paper texture off (see paper.set_flat);
    here we only add a crisp, soft outline."""
    l = _lum(a); ol = _outline(l, .2, 3)[..., None] * .45
    g = a.mean(2, keepdims=True); a = np.clip(g + (a - g) * 1.2, 0, 1)
    return np.clip(a * (1 - ol) + np.array([.12, .1, .18]) * ol, 0, 1)

FN = {'watercolor': watercolor, 'ink': ink, 'stained_glass': stained_glass, 'chalk': chalk, 'linocut': linocut,
      'comic': comic, 'manga': manga, 'pixel': pixel, 'flat': flat}

def stylize(frame, style, t=0.0):
    if not style or style == 'paper': return frame
    out = FN[style](frame.astype(np.float32) / 255, t)
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)
