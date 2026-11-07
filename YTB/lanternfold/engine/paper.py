"""Lanternfold paper engine: shared drawing library for every reel.
Coordinates are 'world' pixels on a 1080x1920 canvas; Cam maps world -> screen with zoom + parallax.
A reel's scene.py imports this and defines frame(t) -> HxWx3 uint8."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
SS = 2                      # supersampling for clean paper edges
rng = np.random.default_rng(7)
# ---------- palette ----------
def hexc(h): return np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], np.float32) / 255
SKY_TOP, SKY_LOW = hexc('#070d22'), hexc('#1d2c57')   # default night palette (reels may override)
GOLD, WARM = hexc('#ffd27a'), hexc('#ff9f4a')
# ---------- easing / helpers ----------
def cl(x, a=0., b=1.): return max(a, min(b, x))
def ss(a, b, t): x = cl((t - a) / (b - a)); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k

def grain_tex(seed, strength=0.13):
    r = np.random.default_rng(seed)
    fine = Image.fromarray((r.random((H, W)) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    mot = Image.fromarray((r.random((H // 16, W // 16)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(12))
    g = (np.asarray(fine, np.float32) / 255 - .5) * 0.8 + (np.asarray(mot, np.float32) / 255 - .5) * 1.4
    # paper fibres
    fib = Image.new('L', (W, H), 0); d = ImageDraw.Draw(fib)
    for _ in range(2500):
        x, y = r.random() * W, r.random() * H; a = r.random() * math.pi; l = 4 + r.random() * 14
        d.line([x, y, x + math.cos(a) * l, y + math.sin(a) * l], fill=int(40 + r.random() * 60), width=1)
    g += np.asarray(fib, np.float32) / 255 * 0.5
    return (1 + strength * g)[..., None]

GRAINS = [grain_tex(s) for s in range(10, 16)]
SKY_GRAIN = grain_tex(99, 0.035)
yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
SKY = SKY_TOP * (1 - yy ** 1.6) + SKY_LOW * yy ** 1.6
_vx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]; _vy = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
VIGN = (1 - 0.35 * np.clip((_vx ** 2 * 0.8 + _vy ** 2 * 0.6), 0, 1) ** 1.2)[..., None]

# ---------- camera ----------
class Cam:
    """z: zoom, c: world point at screen centre, d: horizontal drift. f(p) gives a transform for parallax depth p (0 far .. 1 near)."""
    def __init__(s, z=1.0, c=(540., 960.), d=0.0):
        s.z, s.c, s.d = z, c, d
    def f(s, p):
        z = s.z ** p; cx = lerp(540, s.c[0], p); cy = lerp(960, s.c[1], p); d = s.d * p
        return lambda x, y: ((x - cx) * z + 540 + d, (y - cy) * z + 960), z

def mask_poly(pts, extra=()):
    m = Image.new('L', (W * SS, H * SS), 0); dm = ImageDraw.Draw(m)
    for q in (pts, *extra): dm.polygon([(x * SS, y * SS) for x, y in q], fill=255)
    return np.asarray(m.resize((W, H), Image.BOX), np.float32)[..., None] / 255

def blur(a, r):          # fast blur of a HxWx1 mask at quarter res
    im = Image.fromarray((a[..., 0] * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    im = im.filter(ImageFilter.GaussianBlur(r / 4)).resize((W, H), Image.BILINEAR)
    return np.asarray(im, np.float32)[..., None] / 255

def shift(a, dx, dy):
    return np.roll(np.roll(a, dy, 0), dx, 1)

def paper_layer(img, m, col, grain, shadow=0.75, lit=None):
    sh = shift(blur(m, 30), 8, 20)
    img *= 1 - shadow * sh * (1 - m)
    edge = np.clip(m - shift(m, 0, 4), 0, 1)                      # top cut edge catching light
    c = col[None, None, :] * grain
    c = c + edge * 0.10 * _REV
    img[:] = img * (1 - m) + c * m

# ---------- light buffer ----------
_REV = 1.0
def glow(L, x, y, r, col, a):
    """additive gaussian light; separable and clipped to the screen, so no cache and no memory growth"""
    r = max(1.0, float(r)); n = 3 * r
    x0, x1, y0, y1 = max(0, int(x - n)), min(W, int(x + n) + 1), max(0, int(y - n)), min(H, int(y + n) + 1)
    if x0 >= x1 or y0 >= y1: return
    gx = np.exp(-((np.arange(x0, x1, dtype=np.float32) - x) ** 2) / (2 * r * r))
    gy = np.exp(-((np.arange(y0, y1, dtype=np.float32) - y) ** 2) / (2 * r * r))
    L[y0:y1, x0:x1] += (gy[:, None] * gx[None, :])[..., None] * (np.asarray(col, np.float32) * a)

# ---------- stars ----------
NS = 230
SX = rng.uniform(-300, 1380, NS); SY = rng.uniform(-200, 1250, NS) ** 1.0
SR = rng.choice([1, 1, 1, 2, 2, 3], NS); SPH = rng.uniform(0, 6.28, NS); SF = rng.uniform(.6, 2.2, NS)

def draw_stars(L, cam, t, vis):
    T, z = cam.f(0.5)
    for i in range(NS):
        x, y = T(SX[i], SY[i])
        if -10 < x < W + 10 and -10 < y < H + 10:
            tw = 0.55 + 0.45 * math.sin(t * SF[i] + SPH[i])
            glow(L, x, y, SR[i] * 1.3, np.array([.85, .9, 1.]), vis * tw * 0.9)

def hero_star(L, cam, pos, b, t):
    if b <= 0: return
    T, z = cam.f(1.0); x, y = T(*pos)
    fl = 1 + 0.06 * math.sin(t * 3.1)
    glow(L, x, y, 3 * z ** .5, np.array([1, 1, .95]), 1.6 * b)
    glow(L, x, y, 11 * z ** .5, GOLD, 0.55 * b * fl)
    glow(L, x, y, 45 * z ** .5, GOLD, 0.16 * b * fl)
    for dx, dy in ((1, 0), (0, 1)):   # soft cross flare
        for s in range(-6, 7):
            glow(L, x + dx * s * 6 * z ** .5, y + dy * s * 6 * z ** .5, 2 * z ** .5, GOLD, 0.25 * b * (1 - abs(s) / 7))

# ---------- figures (paper cut-outs) ----------
SKIN, HAIR, GREY = '#e7c4a0', '#3a2418', '#c9c3bb'
def person(d, T, z, fx, fy, h, dress='#c4664f', hair=HAIR, kind='child', arm=None, face=1, seated=False):
    """d: ImageDraw at SS scale. T world->screen. fx,fy feet (world). h height (world px)."""
    def P(x, y): sx, sy = T(fx + x * h * face, fy - y * h); return (sx * SS, sy * SS)
    old = kind == 'old'; lean = 0.06 if old else 0
    if seated:
        d.polygon([P(-.12, .0), P(.30, .0), P(.30, .06), P(-.12, .06)], fill='#2a2a3a')  # legs forward
        d.polygon([P(-.16, .05), P(.10, .05), P(.06, .42), P(-.10, .42)], fill=dress)
        hc = (-.02, .52)
    else:
        for lx in (-.05, .04):
            d.polygon([P(lx - .025, 0), P(lx + .025, 0), P(lx + .025, .3), P(lx - .025, .3)], fill='#2a2a3a')
        bw = .34 if kind == 'child' else .30
        d.polygon([P(-bw / 2, .26), P(bw / 2, .26), P(.08 + lean, .66), P(-.08 + lean, .66)], fill=dress)
        hc = (.0 + lean * 1.6, .78 - lean * .4)
    hr = .12 if kind == 'child' else .1
    cx, cy = P(*hc); rr = hr * h * z * SS
    hx, hy = P(hc[0] - .03, hc[1] + .01)
    if old:
        d.ellipse([hx - rr * 1.05, hy - rr * 1.05, hx + rr * 1.05, hy + rr * 1.05], fill=hair)
        bx, by = P(hc[0] - .1, hc[1] + .08); d.ellipse([bx - rr * .5, by - rr * .5, bx + rr * .5, by + rr * .5], fill=hair)
    else:
        d.ellipse([hx - rr * 1.12, hy - rr * 1.1, hx + rr * 1.12, hy + rr * 1.1], fill=hair)
        if kind == 'child':
            bx, by = P(hc[0] - .13, hc[1] - .02); d.ellipse([bx - rr * .45, by - rr * .45, bx + rr * .45, by + rr * .45], fill=hair)
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=SKIN)
    ex, ey = P(hc[0] + .06, hc[1] + .0); er = max(1.5, rr * .12)
    d.ellipse([ex - er, ey - er, ex + er, ey + er], fill='#2b1d18')
    if not old or True:   # fringe
        fx0, fy0 = P(hc[0] - .02, hc[1] + .02)
        d.pieslice([fx0 - rr * 1.05, fy0 - rr * 1.1, fx0 + rr * 1.05, fy0 + rr * .9], 180, 300 if face > 0 else 360, fill=hair) if face > 0 else \
        d.pieslice([fx0 - rr * 1.05, fy0 - rr * 1.1, fx0 + rr * 1.05, fy0 + rr * .9], 240, 360, fill=hair)
    sh = (hc[0], hc[1] - .17)
    hand = arm if arm else (sh[0] + .2, sh[1] - .12)
    d.line([P(*sh), P(*hand)], fill=dress, width=max(2, int(.05 * h * z * SS)))
    if old:  # cane
        d.line([P(.2, 0), P(.18, .4)], fill='#6b4a33', width=max(2, int(.022 * h * z * SS)))
    return P, hc

def lantern(d, P, hand, L, T, z, h, b, t, fx, fy, face=1, hang=True):
    """small paper lantern hanging from the hand; adds light to L"""
    if hang:
        top = (hand[0] + .02, hand[1] - .02); lx, ly = hand[0] + .02, hand[1] - .16
        d.line([P(*hand), P(*top), P(lx, ly + .06)], fill='#5a3d2a', width=max(1, int(.012 * h * z * SS)))
    else:
        lx, ly = hand
    pts = [P(lx - .045, ly + .06), P(lx + .045, ly + .06), P(lx + .055, ly - .05), P(lx - .055, ly - .05)]
    d.polygon(pts, fill='#3d2a1d')
    inner = [P(lx - .03, ly + .045), P(lx + .03, ly + .045), P(lx + .038, ly - .035), P(lx - .038, ly - .035)]
    c = (np.array([60, 40, 25]) * (1 - b) + np.array([255, 205, 120]) * b).astype(int)
    d.polygon(inner, fill=tuple(c))
    sx, sy = T(fx + lx * h * face, fy - ly * h)
    if b > 0:
        fl = 1 + 0.08 * math.sin(t * 9) + 0.05 * math.sin(t * 23)
        glow(L, sx, sy, 6 * z, GOLD, 0.9 * b * fl)
        glow(L, sx, sy, 28 * z, WARM, 0.35 * b * fl)
        glow(L, sx, sy, 110 * z, WARM, 0.16 * b * fl); glow(L, sx, sy+40*z, 260 * z, WARM, 0.07 * b * fl)
    return sx, sy

def composite_fig(img, fig_im, shadow=0.5):
    a = np.asarray(fig_im.resize((W, H), Image.BOX), np.float32) / 255
    m = a[..., 3:4]; c = a[..., :3]
    sh = shift(blur(m, 8), 3, 6)
    img *= 1 - shadow * sh * (1 - m)
    img[:] = img * (1 - m) + c * GRAINS[5] * m * _REV


# ---------- scene helpers ----------
def set_reveal(v):
    """global fade (0 black .. 1 full) applied to paper layers, figures and edges"""
    global _REV; _REV = v

def sky(top=None, low=None):
    if top is None: return (SKY * SKY_GRAIN).copy()
    s = hexc(top) * (1 - yy ** 1.6) + hexc(low) * yy ** 1.6
    return s * SKY_GRAIN

def hill_poly(T, fn, x0=-900, x1=2000, n=140):
    return [T(x, fn(x)) for x in np.linspace(x0, x1, n)] + [(W + 50, H + 50), (-50, H + 50)]

def wave(x, by, amp, seed):
    ph = np.random.default_rng(seed).random(3) * 6.28
    return by - amp * (math.sin(x / 260 + ph[0]) * .6 + math.sin(x / 120 + ph[1]) * .3 + math.sin(x / 61 + ph[2]) * .1)

def new_fig_layer():
    fi = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); return fi, ImageDraw.Draw(fi)

def fade_layer(fi, a):
    if a >= 1: return fi
    arr = np.asarray(fi, np.uint8).copy(); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8); return Image.fromarray(arr)

def finish(img, L, LS=None, reveal=1.0):
    """screen-blend light over paper, vignette, return uint8"""
    img = img * VIGN
    L = L * reveal
    out = 1 - (1 - np.clip(img, 0, 1)) * (1 - np.clip(L, 0, 1))
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)

def stars_layer(img, cam, t, vis, hero=None, hero_b=0.0):
    """twinkling stars (+ optional hero star) that sit behind the hills"""
    LS = np.zeros((H, W, 3), np.float32)
    draw_stars(LS, cam, t, vis)
    if hero is not None: hero_star(LS, cam, hero, hero_b, t)
    return 1 - (1 - np.clip(img, 0, 1)) * (1 - np.clip(LS, 0, 1))

