"""Reel 4 - How Small Are We? Alien planet. frame(t) with t in story seconds (0-55)."""
import os, sys, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.paper import *            # noqa: F401,F403
from engine import paper as P_
from engine.environments import ENVS, draw_env

DUR = 55.0
ENV = dict(ENVS['space_planet'], moon=(230., 760., 150, '#b98ad6'))   # big planet moved left
EARTH = (790., 470.)                 # the pale blue dot (parallax .3) = loop anchor
EP = .3
SIT_X = 540.
OPEN_Z = 3.2
OPEN_C = (540 + (EARTH[0] - 540) / EP, 960 + (EARTH[1] - 960) / EP)
BLUE = np.array([.55, .78, 1.0], np.float32)

def camera(t):
    wide, her, close, mid = (540., 1100.), (560., 1240.), (580., 1270.), (560., 1170.)
    def mix(a, b, k): return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
    if t < 4: return OPEN_Z, OPEN_C
    if t < 11: k = ss(4, 11, t); return lerp(OPEN_Z, 1.0, k), mix(OPEN_C, wide, k)
    if t < 24: k = ss(12, 15, t); return lerp(1.0, 1.75, k), mix(wide, her, k)
    if t < 37: k = ss(29.5, 31.5, t); return lerp(1.75, 2.15, k), mix(her, close, k)
    if t < 47: k = ss(37, 39.5, t); return lerp(2.15, 1.35, k), mix(close, mid, k)
    k = ss(47.5, DUR, t); return lerp(1.35, OPEN_Z, k), mix(mid, OPEN_C, k)

def earth_dot(L, cam, b):
    T, z = cam.f(EP); sx, sy = T(*EARTH)
    glow(L, sx, sy, 4.2 * z ** .5, np.array([.9, .97, 1], np.float32), 1.0 * b)
    glow(L, sx, sy, 16 * z ** .5, BLUE, .45 * b); glow(L, sx, sy, 50 * z ** .5, BLUE, .08 * b)
    return sx, sy

def storm(d, L, T, z, x, y, a, t):
    """a small worry cloud with rain above her head"""
    if a <= 0: return
    def Q(px, py): sx, sy = T(x + px, y + py); return (sx * SS, sy * SS)
    col = (70, 72, 98, int(255 * a))
    for cx, cy, r in [(-34, 0, 26), (0, -12, 34), (34, 0, 26), (0, 8, 28)]:
        (ax, ay), (bx, by) = Q(cx - r, cy - r), Q(cx + r, cy + r); d.ellipse([ax, ay, bx, by], fill=col)
    for q in range(9):
        rx = -40 + q * 10; ry = 24 + ((t * 160 + q * 37) % 70)
        (ax, ay), (bx, by) = Q(rx, ry), Q(rx - 3, ry + 14); d.line([ax, ay, bx, by], fill=(150, 170, 210, int(200 * a)), width=max(1, int(2 * z)))

def surface(t, reveal):
    z, c = camera(t); cam = Cam(z, c, 8 * math.sin(t / DUR * 6.283))
    img = sky(); L = np.zeros((H, W, 3), np.float32)
    ground = draw_env(img, L, cam, t, ENV, reveal)
    earth_dot(L, cam, reveal)
    T, z1 = cam.f(1.0); gy = ground(SIT_X) + 3
    fi, d = new_fig_layer()
    Pf, hc = person(d, T, z1, SIT_X, gy, 150, dress='#c97b63', hair=HAIR, kind='adult', arm=(.25, .5), face=1, seated=True)
    worry = ss(14, 16, t) * (1 - ss(31.5, 33.5, t))
    storm(d, L, T, z1, SIT_X + 5, gy - 175, worry, t)
    friend = ss(29.8, 31.6, t)
    if friend > 0:               # someone sits down beside her and offers a small warm light
        fx = lerp(820, 650, friend)
        person(d, T, z1, fx, ground(fx) + 3, 150, dress='#5f86a8', hair='#2a1a10', kind='adult', arm=(.32, .45), face=-1, seated=friend >= 1)
    composite_fig(img, fi)
    if friend >= 1:
        warm = ss(31.6, 33, t); sx, sy = T(SIT_X + 62, gy - 70)
        glow(L, sx, sy, 6 * z1, P_.GOLD, .9 * warm * reveal); glow(L, sx, sy, 40 * z1, P_.WARM, .25 * warm * reveal)
        glow(L, sx, sy, 160 * z1, P_.WARM, .08 * warm * reveal)
    return img, L, cam

def tiny_planet(t, reveal):
    """far away: her whole world is a speck, the worry cloud is invisible"""
    k = ss(24.5, 28.5, t)
    cam = Cam(1.0, (540., 960.), 0); img = sky(); L = np.zeros((H, W, 3), np.float32)
    img = stars_layer(img, cam, t, reveal * 1.3)
    R = lerp(900, 55, k); cx, cy = 540, 1050 + R * .55
    m = Image.new('L', (W * SS, H * SS), 0)
    ImageDraw.Draw(m).ellipse([(cx - R) * SS, (cy - R) * SS, (cx + R) * SS, (cy + R) * SS], fill=255)
    m = np.asarray(m.resize((W, H), Image.BOX), np.float32)[..., None] / 255
    paper_layer(img, m, hexc('#3a2f63') * reveal, GRAINS[3], shadow=.4)
    glow(L, cx - R * .4, cy - R * .4, R * .9, np.array([.6, .5, .9], np.float32), .08 * reveal)
    s = R / 900
    if s > .08:
        T = lambda x, y: (cx + (x - 540) * s, cy - R + (y - 0) * s); fi, d = new_fig_layer()
        person(d, T, s, 540, 0, 150, dress='#c97b63', kind='adult', arm=(.25, .5), seated=True); composite_fig(img, fi)
    glow(L, 790, 470, 4.2, np.array([.9, .97, 1], np.float32), reveal); glow(L, 790, 470, 16, BLUE, .45 * reveal)
    return img, L

def frame(t):
    reveal = ss(3.6, 8.5, t) * (1 - ss(52.5, DUR - 0.15, t)); set_reveal(reveal)
    if 23.6 < t < 30.4:
        a = min(ss(23.6, 24.6, t), 1 - ss(29.4, 30.4, t))
        ti, tl = tiny_planet(t, reveal)
        if a < 1:
            si, sl, _ = surface(t, reveal); ti = ti * a + si * (1 - a); tl = tl * a + sl * (1 - a)
        img, L = ti, tl
    else:
        img, L, _ = surface(t, reveal)
    out = finish(img, L, reveal=reveal).astype(np.float32) / 255
    # loop anchor: the pale blue dot survives the fade
    z, c = camera(t); cam = Cam(z, c, 8 * math.sin(t / DUR * 6.283)); Ls = np.zeros((H, W, 3), np.float32)
    b = 0.35 + 0.65 * ss(1.0, 1.4, t) if t < 7 else 1.0
    if t > DUR - 0.6: b = 0.35 + 0.65 * (1 - ss(DUR - 0.6, DUR, t))
    earth_dot(Ls, cam, b); Ls *= (1 - reveal)
    out = 1 - (1 - out) * (1 - np.clip(Ls, 0, 1))
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)
