"""Light From a Dead Star - paper cut-out scene renderer (numpy + Pillow).
frame(t) -> HxWx3 uint8 image. Pure code, no external assets."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
SS = 2                      # supersampling for cut edges
DUR = 55.0
rng = np.random.default_rng(7)

# ---------- palette ----------
def hexc(h): return np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], np.float32) / 255
SKY_TOP, SKY_LOW = hexc('#070d22'), hexc('#1d2c57')
GOLD, WARM = hexc('#ffd27a'), hexc('#ff9f4a')
HILLS = [  # (color, base y, amplitude, seed, parallax)
    (hexc('#1a2246'), 1150, 80, 1, 0.50),
    (hexc('#26305a'), 1270, 90, 2, 0.65),
    (hexc('#2f4466'), 1390, 70, 3, 0.80),
    (hexc('#36416a'), 1520, 0, 4, 1.00),   # hero hill (shaped below)
    (hexc('#1c1f38'), 1830, 70, 5, 1.25),  # dark foreground lip
]

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
STAR = (540., 430.)          # hero star (world)
NEWSTAR = (300., 330.)       # new star at the end
GIRL = (560., 0.)            # x of girl; y set from hill
OPEN_Z = 3.2

def camera(t):
    """returns zoom, center(world), horizontal drift"""
    full = (540., 960.)
    drift = 22 * math.sin(t / DUR * 2 * math.pi)
    if t < 4:   return OPEN_Z, STAR, drift
    if t < 10:  k = ss(4, 10, t); return lerp(OPEN_Z, 1.0, k), (lerp(STAR[0], full[0], k), lerp(STAR[1], full[1], k)), drift
    if t < 18:  k = ss(10, 18, t); return lerp(1.0, 1.12, k), (540., lerp(960, 900, k)), drift
    if t < 28:  k = ss(18, 19.5, t); return lerp(1.12, 1.65, k), (lerp(540, 600, k), lerp(900, 1330, k)), drift
    if t < 38:  k = ss(28, 30, t); return lerp(1.65, 1.35, k), (lerp(600, 560, k), lerp(1330, 1250, k)), drift
    if t < 50:  k = ss(38, 43, t); return lerp(1.35, 1.0, k), (lerp(560, 540, k), lerp(1250, 980, k)), drift
    k = ss(51.5, DUR, t)
    return lerp(1.0, OPEN_Z, k), (lerp(540, NEWSTAR[0], k), lerp(980, NEWSTAR[1], k)), drift

class Cam:
    def __init__(s, t):
        s.z, s.c, s.d = camera(t)
    def f(s, p):           # parallax-aware transform factory
        z = s.z ** p; cx = lerp(540, s.c[0], p); cy = lerp(960, s.c[1], p); d = s.d * p
        return lambda x, y: ((x - cx) * z + 540 + d, (y - cy) * z + 960), z

# ---------- hills ----------
def hill_y(i, x):
    col, by, amp, sd, p = HILLS[i]
    if i == 3:   # hero mound peaking under the girl
        return by + 330 * (1 - math.exp(-((x - GIRL[0]) / 380) ** 2)) - 240 + 6 * math.sin(x / 37)
    r = np.random.default_rng(sd); ph = r.random(3) * 6.28
    return by - amp * (math.sin(x / 260 + ph[0]) * .6 + math.sin(x / 120 + ph[1]) * .3 + math.sin(x / 61 + ph[2]) * .1)

GY = hill_y(3, GIRL[0])

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
_kern = {}
_REV = 1.0
def glow(L, x, y, r, col, a):
    r = max(1, int(r)); k = _kern.get(r)
    if k is None:
        g = np.arange(-3 * r, 3 * r + 1, dtype=np.float32); d = g[None] ** 2 + g[:, None] ** 2
        k = _kern[r] = np.exp(-d / (2 * r * r))[..., None]
    x, y = int(x), int(y); n = 3 * r
    x0, x1, y0, y1 = max(0, x - n), min(W, x + n + 1), max(0, y - n), min(H, y + n + 1)
    if x0 >= x1 or y0 >= y1: return
    L[y0:y1, x0:x1] += k[y0 - y + n:y1 - y + n, x0 - x + n:x1 - x + n] * (col * a)

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

# ---------- story data ----------
KIND = [  # (time spark leaves, label)
    (20.0, 'bread'), (23.4, 'hand'), (26.8, 'read')]
STRANGERS = [  # world pos (x, hill index), arrival time
    (150, 1, 41.0), (900, 1, 42.6), (330, 0, 44.2), (760, 2, 45.4), (1010, 0, 46.8), (60, 2, 47.8)]

def spark_path(k, t):
    """spark k: leaves her at KIND time, rises, hovers, then drifts to stranger(s)"""
    t0 = KIND[k][0]
    if t < t0: return None
    start = (GIRL[0] + 30, GY - 130)
    hover = (380 + k * 180, 760 - k * 60)
    if t < 38:
        u = ss(t0, t0 + 6, t)
        x = lerp(start[0], hover[0], u) + 18 * math.sin(t * 1.3 + k)
        y = lerp(start[1], hover[1], u) + 10 * math.sin(t * 0.9 + k * 2)
        return x, y, 1.0
    # after: each spark splits toward two strangers -> return hover for parent
    return hover[0] + 18 * math.sin(t * 1.3 + k), hover[1] + 10 * math.sin(t * .9 + k * 2), ss(38, 41, t) * -1 + 1

def stranger_pos(j):
    x, hi, ta = STRANGERS[j]; return x, hill_y(hi, x)

TREES = {0: [(-150, 30), (90, 22), (980, 26), (1250, 30)], 1: [(520, 26), (1150, 34), (-80, 30)], 2: [(260, 34), (1020, 40)]}
def trees(i, T, z):
    out = []
    for x, h in TREES.get(i, []):
        y = hill_y(i, x) + 6
        out.append([T(x - 2, y), T(x - 2, y - h * .5), T(x - h * .32, y - h * .45), T(x, y - h * 1.6), T(x + h * .32, y - h * .45), T(x + 2, y - h * .5), T(x + 2, y)])
    return out

# ---------- main frame ----------
def frame(t):
    cam = Cam(t)
    reveal = ss(3.6, 8.5, t) * (1 - ss(52.5, DUR - 0.15, t))     # scene visibility (black at start/end)
    img = SKY.copy() * SKY_GRAIN
    L = np.zeros((H, W, 3), np.float32)
    global _REV; _REV = reveal
    LS = np.zeros((H, W, 3), np.float32)
    draw_stars(LS, cam, t, reveal)

    # hero star: blinks on, at the very end it is the new star in the same frame
    b0 = 0.35 + ss(1.0, 1.25, t) * 0.65
    hero_b = b0 * (1 - ss(48, 51, t))
    hero_star(LS, cam, STAR, hero_b, t)
    new_b = ss(50.5, 52, t) * (0.35 + 0.65 * (1 - ss(DUR - 0.5, DUR, t)) )
    hero_star(LS, cam, NEWSTAR, new_b, t)

    img = img * reveal
    img = 1 - (1 - np.clip(img, 0, 1)) * (1 - np.clip(LS, 0, 1))   # stars sit behind the hills
    # hills
    figs = {}
    for i, (col, by, amp, sd, p) in enumerate(HILLS):
        if i == 4: draw_story(img, L, cam, t)
        T, z = cam.f(p)
        xs = np.linspace(-900, 2000, 140)
        pts = [T(x, hill_y(i, x)) for x in xs] + [(W + 50, H + 50), (-50, H + 50)]
        paper_layer(img, mask_poly(pts, trees(i, T, z)), col * reveal, GRAINS[i])
        if i < 3: draw_strangers(img, L, t, i, T, z)

    # fade scene in/out (stars + hero star survive as the loop frame)
    img = img * VIGN
    out = 1 - (1 - np.clip(img, 0, 1)) * (1 - np.clip(L, 0, 1))
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)

def composite_fig(img, fig_im, shadow=0.5):
    a = np.asarray(fig_im.resize((W, H), Image.BOX), np.float32) / 255
    m = a[..., 3:4]; c = a[..., :3]
    sh = shift(blur(m, 8), 3, 6)
    img *= 1 - shadow * sh * (1 - m)
    img[:] = img * (1 - m) + c * GRAINS[5] * m * _REV

def draw_strangers(img, L, t, hi, T, z):
    js = [j for j, s in enumerate(STRANGERS) if s[1] == hi]
    if not js or t < 33: return
    fi = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(fi)
    vis = ss(33, 38, t)
    for j in js:
        x, _, ta = STRANGERS[j]; y = hill_y(hi, x) + 4
        h = 70 * (0.75 + 0.1 * hi)
        cols = ['#7d8fb0', '#8a7fa6', '#6f9a9a', '#a88a7a', '#8f9fb8', '#9a8f7a']
        P, hc = person(d, T, z, x, y, h, dress=cols[j], hair='#2b2233', kind='adult', face=1 if j % 2 else -1)
        g = ss(ta, ta + 1.5, t)
        if g > 0:
            sx, sy = T(x, y - h * .5)
            glow(L, sx, sy, 22 * z, GOLD, 0.35 * g * (1 + .1 * math.sin(t * 2 + j)))
            glow(L, sx, sy, 70 * z, WARM, 0.12 * g)
    composite_fig(img, fi, 0.4 * vis)
    # sparks travelling to these strangers
    for j in js:
        x, _, ta = STRANGERS[j]; y = hill_y(hi, x)
        k = j % 3
        hp = spark_path(k, 37.99)
        u = ss(ta - 3.2, ta, t)
        if 0 < u < 1:
            sx = lerp(hp[0], x, u) + 30 * math.sin(u * 3.14) ; sy = lerp(hp[1], y - 40, u) - 60 * math.sin(u * 3.14)
            Tf, zf = T, z
            px, py = Tf(sx, sy)
            glow(L, px, py, 4 * zf, GOLD, 0.9); glow(L, px, py, 14 * zf, GOLD, 0.25)

def draw_story(img, L, cam, t):
    T, z = cam.f(1.0)
    fi = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(fi)
    fx, fy = GIRL[0], GY + 3
    if t < 18 or t >= 50:
        newkid = t >= 50
        h = 150
        P, hc = person(d, T, z, fx, fy, h, dress='#5f86a8' if newkid else '#c4664f', kind='child',
                       arm=(.22, .45), face=1)
        lb = ss(4, 6, t) if not newkid else ss(50, 51.2, t)
        lantern(d, P, (.22, .45), L, T, z, h, lb, t, fx, fy)
        if not newkid and t >= 10:   # golden thread star -> eyes
            ex, ey = T(fx + (hc[0] + .05) * h, fy - (hc[1] + .02) * h)
            sx, sy = T(*STAR)
            u = ss(10.3, 13.5, t) * (1 - ss(17, 18.2, t) * 0.0)
            fade = 1 - ss(17.2, 18.4, t)
            n = 70
            for i in range(int(n * u)):
                k = i / n
                x = lerp(sx, ex, k) + 90 * math.sin(k * math.pi) * z
                y = lerp(sy, ey, k) - 20 * math.sin(k * math.pi)
                glow(L, x, y, 2.2, GOLD, 0.55 * fade)
                glow(L, x, y, 8, GOLD, 0.06 * fade)
            for q in range(5):     # light beads travelling down the thread
                k = ((t * .18 + q / 5) % 1)
                if k < u:
                    x = lerp(sx, ex, k) + 90 * math.sin(k * math.pi) * z; y = lerp(sy, ey, k) - 20 * math.sin(k * math.pi)
                    glow(L, x, y, 5, GOLD, 0.8 * fade)
    elif t < 28:
        # growing up: three kindness vignettes
        seg = 0 if t < 21.7 else 1 if t < 25.1 else 2
        h = 170
        if seg == 0:   # sharing bread
            P, hc = person(d, T, z, fx - 40, fy, h, dress='#c4664f', kind='adult', arm=(.28, .42))
            P2, _ = person(d, T, z, fx + 70, fy + 2, h * .95, dress='#7e8c6a', hair='#5a4a3a', kind='adult', arm=(.25, .42), face=-1)
            bx, by = P(.31, .43); r = .07 * h * z * SS
            d.ellipse([bx - r * 1.3, by - r * .8, bx + r * 1.3, by + r * .8], fill='#c99258')
            d.line([bx - r * .5, by - r * .6, bx - r * .2, by + r * .5], fill='#a8733e', width=max(1, int(r * .15)))
        elif seg == 1:   # holding a hand
            P, hc = person(d, T, z, fx - 30, fy, h * 1.02, dress='#b85f4e', kind='adult', arm=(.33, .3))
            P2, _ = person(d, T, z, fx + 45, fy + 2, h * .62, dress='#d8b45a', hair='#2a1a10', kind='child', arm=(.17, .5), face=-1)
        else:   # teaching a kid to read
            P, hc = person(d, T, z, fx - 25, fy, h * .95, dress='#a85a4c', hair='#5b4535', kind='adult', arm=(.3, .3), seated=True)
            P2, _ = person(d, T, z, fx + 55, fy + 2, h * .55, dress='#6a95a0', hair='#2a1a10', kind='child', arm=(.3, .4), face=-1, seated=True)
            bx, by = P(.34, .28); r = .1 * h * z * SS
            d.polygon([(bx - r, by - r * .5), (bx, by - r * .3), (bx, by + r * .4), (bx - r, by + r * .2)], fill='#f2ead8')
            d.polygon([(bx, by - r * .3), (bx + r, by - r * .5), (bx + r, by + r * .2), (bx, by + r * .4)], fill='#e4dac4')
        lantern(d, P, (.55, .05), L, T, z, h, 1.0, t, fx - 40, fy, hang=False)
        # vignette crossfade: dip figures
    else:
        # old woman, lantern dims and goes out
        h = 160
        P, hc = person(d, T, z, fx, fy, h, dress='#8a5a5a', hair=GREY, kind='old', arm=(.22, .42))
        lb = 1 - ss(31.5, 34.0, t) if t < 38 else 0
        # flicker before going out
        if 31.5 < t < 34: lb *= 0.75 + 0.25 * math.sin(t * 31) * math.sin(t * 7)
        lantern(d, P, (.22, .42), L, T, z, h, lb if t < 38 else 0, t, fx, fy)
        if t >= 38:   # she fades away gently, leaving the hill
            pass
    fade = 1.0
    if 38 <= t < 50: fade = 1 - ss(38.5, 41, t)
    if 50 <= t: fade = ss(49.8, 50.8, t)
    if 17.4 < t < 18.6: fade = abs(t - 18) / .6
    for tb in (21.7, 25.1, 28.0):
        if abs(t - tb) < .35: fade = min(fade, abs(t - tb) / .35)
    if fade < 1:
        a = np.asarray(fi, np.uint8).copy(); a[..., 3] = (a[..., 3] * fade).astype(np.uint8); fi = Image.fromarray(a)
    composite_fig(img, fi)
    # kindness sparks
    for k in range(3):
        s = spark_path(k, t)
        if s:
            x, y, a = s
            if a <= 0: continue
            px, py = T(x, y)
            glow(L, px, py, 4 * z, GOLD, 1.0 * a); glow(L, px, py, 16 * z, GOLD, 0.3 * a)
            for q in range(4):   # little trail
                tt = t - q * .12; s2 = spark_path(k, tt)
                if s2: qx, qy = T(s2[0], s2[1]); glow(L, qx, qy, 2.5 * z, GOLD, 0.25 * a * (1 - q / 4))

if __name__ == '__main__':
    import sys
    for ts in sys.argv[1:]:
        Image.fromarray(frame(float(ts))).save(f'style_{ts}.png')
