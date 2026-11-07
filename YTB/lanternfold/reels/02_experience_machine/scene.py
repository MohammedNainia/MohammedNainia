"""Reel 2 - The Machine That Makes You Happy. frame(t) with t in story seconds (0-55)."""
import os, sys, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.paper import *          # noqa: F401,F403  (W, H, Cam, glow, person, paper_layer, ...)
from engine import paper as P_

DUR = 55.0
MAN = (540., 0.)
HERO = lambda x: 1520 + 330 * (1 - math.exp(-((x - 540) / 380) ** 2)) - 240 + 6 * math.sin(x / 37)
MY = HERO(540)
GOLD_DOOR = (360., 160., 300.)        # x centre, width, height (stands on the hill)
REAL_DOOR = (720., 160., 300.)
SLIT = (GOLD_DOOR[0] + 72, MY - 150)  # light leaking from the ajar golden door (loop anchor)
OPEN_Z = 3.4

NIGHT = [('#1a2246', lambda x: wave(x, 1150, 80, 1), .5), ('#26305a', lambda x: wave(x, 1270, 90, 2), .65),
         ('#2f4466', lambda x: wave(x, 1390, 70, 3), .8), ('#36416a', HERO, 1.0)]
GOLDW = [('#e7a56b', lambda x: wave(x, 1150, 80, 1), .5), ('#eab27a', lambda x: wave(x, 1270, 90, 2), .65),
         ('#f0c58c', lambda x: wave(x, 1390, 70, 3), .8), ('#d98d5c', HERO, 1.0)]
REALW = [('#3b4a63', lambda x: wave(x, 1150, 80, 1), .5), ('#465672', lambda x: wave(x, 1270, 90, 2), .65),
         ('#51627e', lambda x: wave(x, 1390, 70, 3), .8), ('#5b6b86', HERO, 1.0)]

def camera(t):
    full, door = (540., 1000.), SLIT
    if t < 4: return OPEN_Z, door
    if t < 10: k = ss(4, 10, t); return lerp(OPEN_Z, 1.0, k), (lerp(door[0], full[0], k), lerp(door[1], full[1], k))
    if t < 16: k = ss(10, 16, t); return lerp(1.0, 1.18, k), (lerp(540, 470, k), lerp(1000, 1080, k))
    if t < 48: k = ss(40, 42, t); return lerp(1.3, 1.25, k), (540., lerp(1250, 1180, k))
    k = ss(49, DUR, t); return lerp(1.25, OPEN_Z, k), (lerp(540, door[0], k), lerp(1180, door[1], k))

def hills(img, cam, layers, reveal):
    for i, (col, fn, p) in enumerate(layers):
        T, z = cam.f(p)
        paper_layer(img, mask_poly(hill_poly(T, fn)), hexc(col) * reveal, GRAINS[i])

def door(d, L, T, z, spec, kind, t, light=1.0):
    x, w, h = spec; y = MY + 4
    def Q(px, py): sx, sy = T(px, py); return (sx * SS, sy * SS)
    frame_c, body = ('#8a5a2b', '#d9a441') if kind == 'gold' else ('#2c3446', '#5d6d88')
    d.polygon([Q(x - w / 2 - 12, y), Q(x + w / 2 + 12, y), Q(x + w / 2 + 12, y - h - 14), Q(x - w / 2 - 12, y - h - 14)], fill=frame_c)
    if kind == 'gold':   # ajar: the door leaf is narrower, a bright slit of light on its right
        d.polygon([Q(x - w / 2, y), Q(x + w / 2 - 22, y + 6), Q(x + w / 2 - 22, y - h - 6), Q(x - w / 2, y - h)], fill=body)
        d.polygon([Q(x + w / 2 - 22, y), Q(x + w / 2, y), Q(x + w / 2, y - h), Q(x + w / 2 - 22, y - h)], fill='#fff2c8')
        for yy in np.linspace(y - h * .9, y - h * .1, 6):
            sx, sy = T(x + w / 2 - 10, yy); glow(L, sx, sy, 22 * z, P_.GOLD, 0.16 * light)
        sx, sy = T(x, y - h / 2); glow(L, sx, sy, 160 * z, P_.WARM, 0.10 * light)
    else:
        d.polygon([Q(x - w / 2, y), Q(x + w / 2, y), Q(x + w / 2, y - h), Q(x - w / 2, y - h)], fill=body)
        for py in (y - h * .92, y - h * .48):
            d.polygon([Q(x - w / 2 + 18, py + h * .4), Q(x + w / 2 - 18, py + h * .4), Q(x + w / 2 - 18, py), Q(x - w / 2 + 18, py)], fill='#53627c')
    kx, ky = Q(x + (w / 2 - 40 if kind == 'gold' else w / 2 - 26), y - h * .48); r = 7 * z * SS
    d.ellipse([kx - r, ky - r, kx + r, ky + r], fill='#f5d58a' if kind == 'gold' else '#c9ced8')

def smile(d, Pf, hc, h, z):
    cx, cy = Pf(hc[0] + .05, hc[1] - .05); r = .045 * h * z * SS
    d.arc([cx - r, cy - r * .9, cx + r, cy + r * .5], 20, 160, fill='#5a2e22', width=max(2, int(r * .35)))

def man(d, T, z, x, y, h, dress='#7a5c8e', arm=(.25, .45), arm2=None, face=1, happy=False):
    Pf, hc = person(d, T, z, x, y, h, dress=dress, kind='adult', arm=arm, face=face)
    if arm2: d.line([Pf(hc[0], hc[1] - .17), Pf(*arm2)], fill=dress, width=max(2, int(.05 * h * z * SS)))
    if happy: smile(d, Pf, hc, h, z)
    return Pf, hc

# ---------- worlds ----------
def hill_world(t, reveal):
    z, c = camera(t); cam = Cam(z, c, 18 * math.sin(t / DUR * 6.283))
    img = sky() * reveal; img = stars_layer(img, cam, t, reveal)
    L = np.zeros((H, W, 3), np.float32); hills(img, cam, NIGHT, reveal)
    T, z = cam.f(1.0); fi, d = new_fig_layer()
    door(d, L, T, z, GOLD_DOOR, 'gold', t); door(d, L, T, z, REAL_DOOR, 'real', t)
    reach = ss(40.5, 43, t)
    man(d, T, z, 540, MY + 3, 175, arm=(lerp(.2, -.62, reach), lerp(.42, .5, reach)) if reach else (.22, .4),
        arm2=(lerp(.0, .62, reach), lerp(.42, .5, reach)) if reach else None, face=1)
    composite_fig(img, fi)
    return img, L, cam

def gold_world(t):
    """the perfect life: warm sunset, applause, nothing goes wrong"""
    cam = Cam(1.5, (540 + 270 / 1.5, 1190), 8 * math.sin(t))
    img = sky('#e39a5e', '#ffe1a6'); L = np.zeros((H, W, 3), np.float32)
    T, z = cam.f(.6); sx, sy = T(560, 900); glow(L, sx, sy, 90, np.array([1, .95, .8]), .9); glow(L, sx, sy, 260, P_.GOLD, .25)
    hills(img, cam, GOLDW, 1.0); T, z = cam.f(1.0); fi, d = new_fig_layer()
    crowd = ss(29.5, 31.5, t)
    for k in range(5):           # identical applauding crowd: every smile guaranteed
        if crowd <= 0: break
        cx = 230 + k * 70; cy = HERO(cx) + 4
        man(d, T, z, cx, cy, 120, dress='#c9824f', arm=(.2, .62 + .05 * math.sin(t * 12)), face=1, happy=True)
    man(d, T, z, 540, MY + 3, 175, dress='#7a5c8e', arm=(.3, 1.02), arm2=(-.3, 1.02), happy=True)
    composite_fig(img, fi, 0.35)
    rng = np.random.default_rng(5)
    for q in range(40):          # golden confetti
        x0, sp, ph = rng.uniform(250, 1000), rng.uniform(60, 140), rng.uniform(0, 30)
        yy = 300 + ((t + ph) * sp) % 1300; xx = x0 + 30 * math.sin(t * 2 + q)
        px, py = T(xx, yy); glow(L, px, py, 3.5, P_.GOLD, .9)
    return img, L

def real_world(t):
    """the true life: rain, a scraped day, a friend who comes back"""
    cam = Cam(1.5, (540 - 270 / 1.5, 1190), 8 * math.sin(t + 1))
    clear = ss(33, 37, t)
    img = sky('#232c44', '#56657f') * (1 + 0.15 * clear); L = np.zeros((H, W, 3), np.float32)
    if clear: T, z = cam.f(.6); sx, sy = T(640, 760); glow(L, sx, sy, 26, np.array([.9, .95, 1]), .8 * clear); glow(L, sx, sy, 110, np.array([.6, .7, .9]), .2 * clear)
    hills(img, cam, REALW, 1.0); T, z = cam.f(1.0); fi, d = new_fig_layer()
    Pf, hc = man(d, T, z, 540, MY + 3, 175, dress='#7a5c8e', arm=(.18, .78), happy=t > 31)
    ux, uy = Pf(.18, 1.12); r = .62 * 175 * z * SS        # umbrella
    d.pieslice([ux - r, uy - r * .55, ux + r, uy + r * .55], 180, 360, fill='#a5473d')
    d.line([Pf(.18, 1.12), Pf(.18, .78)], fill='#3a2a22', width=max(2, int(4 * z * SS)))
    friend = ss(26.5, 29, t)
    if friend:                    # a friend walks back in and shares the umbrella
        fx = lerp(980, 640, friend)
        man(d, T, z, fx, HERO(fx) + 3, 160, dress='#4f8a83', arm=(.3, .55), face=-1, happy=t > 31)
    composite_fig(img, fi, 0.45)
    rain = 1 - clear
    if rain > 0:
        rng = np.random.default_rng(9); R = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(R)
        for q in range(260):
            x0, sp = rng.uniform(-50, 1130), rng.uniform(1500, 2100); y0 = (rng.uniform(0, H) + t * sp) % (H + 200) - 100
            dr.line([x0, y0, x0 - 10, y0 + 46], fill=int(150 * rain), width=2)
        a = np.asarray(R.filter(ImageFilter.GaussianBlur(.8)), np.float32)[..., None] / 255
        L += a * np.array([.55, .65, .8], np.float32) * .5
    return img, L

def split(t):
    gi, gl = gold_world(t); ri, rl = real_world(t)
    xs = np.arange(W)[None, :]; ys = np.arange(H)[:, None]
    edge = 540 + 9 * np.sin(ys / 23.0) + 5 * np.sin(ys / 7.0)                 # torn paper seam
    m = (xs < edge).astype(np.float32)[..., None]
    img = gi * m + ri * (1 - m); L = gl * m + rl * (1 - m)
    seam = np.exp(-((xs - edge) ** 2) / 18.0)[..., None]                       # torn edge highlight + shadow
    img = img * (1 - 0.45 * np.exp(-((xs - edge - 8) ** 2) / 60.0)[..., None]) + seam * 0.25
    return img, L

def frame(t):
    reveal = ss(3.6, 8.5, t) * (1 - ss(52.5, DUR - 0.15, t))
    set_reveal(reveal)
    if 15.6 < t < 40.6:
        si, sl = split(t)
        a = min(ss(15.6, 16.8, t), 1 - ss(39.4, 40.6, t))
        if a < 1:
            hi, hl, _ = hill_world(t, reveal); si = si * a + hi * (1 - a); sl = sl * a + hl * (1 - a)
        img, L = si, sl
    else:
        img, L, _ = hill_world(t, reveal)
    out = finish(img, L, reveal=reveal).astype(np.float32) / 255
    # the golden slit survives the fade: it is the first and last frame of the loop
    z, c = camera(t); T, zz = Cam(z, c, 18 * math.sin(t / DUR * 6.283)).f(1.0); sx, sy = T(*SLIT)
    b = 0.35 + 0.65 * ss(1.0, 1.4, t) if t < 10 else 1.0
    if t > DUR - 0.6: b = 0.35 + 0.65 * (1 - ss(DUR - 0.6, DUR, t))
    Ls = np.zeros((H, W, 3), np.float32)
    for yy in np.linspace(-140, 140, 57):
        glow(Ls, sx, sy + yy * zz, 3 * zz ** .5, np.array([1, .95, .8]), .22 * b * (1 - (yy / 150) ** 4))
    glow(Ls, sx, sy, 40 * zz ** .5, P_.GOLD, .25 * b)
    Ls *= (1 - reveal)
    out = 1 - (1 - out) * (1 - np.clip(Ls, 0, 1))
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)
