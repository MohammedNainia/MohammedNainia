"""Reel 6 - Would You Want to Know? Desert under the moon. Hook-first: frame 0 = the striking shot
(traveller holding a glowing envelope); the reel ends on the same shot. frame(t), t in story seconds 0-55."""
import os, sys, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.paper import *            # noqa: F401,F403
from engine import paper as P_
from engine.environments import ENVS, draw_env

DUR = 55.0
NIGHT = ENVS['desert_moon']
GOLDEN = {'sky': ('#e48f55', '#ffdca4'), 'sun': (330, 820, 55, '#ffbf6a'), 'layers': [
    {'c': '#d98f5f', 'k': 'dunes', 'y': 1200, 'a': 70, 's': 7, 'p': .5},
    {'c': '#e6a96e', 'k': 'dunes', 'y': 1320, 'a': 80, 's': 8, 'p': .7},
    {'c': '#c97b4f', 'k': 'stage', 'y': 1500, 'w': 460, 'p': 1}], 'weather': 'dust', 'weather_amt': .5}
X = 540.
HOOK = (2.0, (560., 1270.))

def camera(t):
    wide, mid = (540., 1010.), (540., 1190.)
    def mix(a, b, k): return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
    if t < 5: return lerp(2.0, 2.12, ss(0, 5, t)), mix(HOOK[1], (560., 1255.), ss(0, 5, t))      # moving from frame 1
    if t < 14: k = ss(5, 9.5, t); return lerp(2.12, 1.0, k), mix((560., 1255.), wide, k)
    if t < 46: k = ss(29, 31.5, t); return lerp(1.0, 1.4, k), mix(wide, mid, k)
    k = ss(46.5, 52.5, t); return lerp(1.4, HOOK[0], k), mix(mid, HOOK[1], k)

def envelope(d, L, T, z, x, y, a=1.0, s=1.0, reveal=1.0):
    """small cream envelope that glows faintly from inside"""
    def Q(px, py): sx, sy = T(x + px * s, y + py * s); return (sx * SS, sy * SS)
    w, h = 34, 23
    d.polygon([Q(-w, -h), Q(w, -h), Q(w, h), Q(-w, h)], fill=(250, 238, 210, int(255 * a)))
    d.line([Q(-w, -h), Q(0, 4), Q(w, -h)], fill=(196, 160, 112, int(255 * a)), width=max(2, int(2.5 * z * SS)))
    d.polygon([Q(-6, -2), Q(6, -2), Q(6, 9), Q(-6, 9)], fill=(214, 92, 72, int(255 * a)))     # wax seal
    sx, sy = T(x, y)
    glow(L, sx, sy, 16 * z * s, P_.GOLD, .55 * a * reveal); glow(L, sx, sy, 70 * z * s, P_.WARM, .14 * a * reveal)

def traveller(d, T, z, x, y, h, coat, scarf, seated=False, face=1, arm=(.3, .52)):
    Pf, hc = person(d, T, z, x, y, h, dress=coat, hair='#2a1a10', kind='adult', arm=arm, face=face, seated=seated)
    sx, sy = Pf(hc[0] - .02, hc[1] - .14); sx2, sy2 = Pf(hc[0] - .12 * face, hc[1] - .3)   # scarf
    d.line([sx - 40 * z, sy, sx + 40 * z, sy], fill=scarf, width=max(3, int(10 * z * SS * .5)))
    d.line([sx, sy, sx2, sy2], fill=scarf, width=max(3, int(8 * z * SS * .5)))
    return Pf, hc

def night_scene(t, cam, single=True):
    img = sky(); L = np.zeros((H, W, 3), np.float32)
    ground = draw_env(img, L, cam, t, NIGHT, 1.0)
    T, z = cam.f(1.0); gy = ground(X) + 3; fi, d = new_fig_layer()
    two = (1 - ss(45, 47.5, t)) * ss(29, 31, t)            # both versions together on one dune
    if two > 0.01:
        f2, d2 = new_fig_layer()
        traveller(d2, T, z, X - 110, ground(X - 110) + 3, 150, '#c9824f', '#f0c46b', seated=True, arm=(.25, .45))
        traveller(d2, T, z, X + 110, ground(X + 110) + 3, 150, '#4f6fa0', '#8fb3e0', seated=True, arm=(.25, .45), face=-1)
        composite_fig(img, fade_layer(f2, two), .4)
    if two < .99:
        Pf, hc = traveller(d, T, z, X, gy, 170, '#5d5a8a', '#ee8470')
        hx, hy = Pf(.3, .52); ex, ey = (hx / SS - 0, hy / SS)
        # envelope in hand (convert hand point back to world coords for the helper)
        wx, wy = X + .3 * 170 + 10, gy - .52 * 170
        composite_fig(img, fade_layer(fi, 1 - two))
        f3, d3 = new_fig_layer(); envelope(d3, L, T, z, wx, wy - 6, a=1 - two); composite_fig(img, f3, .3)
    still = math.exp(-((t - 44.88) / .9) ** 2)
    if still > .02:
        sx, sy = T(X, gy - 120); glow(L, sx, sy, 120 * z, P_.WARM, .08 * still)
    return img, L

def golden_world(t):
    """opened it: walks with purpose, plants glowing seeds, an hourglass empties in the sky"""
    cam = Cam(1.45, (540 + 270 / 1.45, 1300), 6 * math.sin(t))
    img = sky(); L = np.zeros((H, W, 3), np.float32); g = draw_env(img, L, cam, t, GOLDEN, 1.0)
    T, z = cam.f(1.0); k = ss(14, 29, t); x = lerp(420, 640, k); fi, d = new_fig_layer()
    for i in range(7):                                    # seeds sprouting behind the walker
        sxw = 420 + i * 32
        if sxw < x - 20:
            age = min(1, (x - 20 - sxw) / 60); gy = g(sxw) + 2
            def Q(px, py): a, b = T(sxw + px, gy + py); return (a * SS, b * SS)
            d.polygon([Q(-6 * age, 0), Q(0, -26 * age), Q(6 * age, 0)], fill='#5f8a4a')
            a, b = T(sxw, gy - 28 * age); glow(L, a, b, 4 * z, P_.GOLD, .7)
    traveller(d, T, z, x, g(x) + 3, 165, '#c9824f', '#f0c46b', arm=(.35, .7))
    composite_fig(img, fi, .35)
    Th, zh = cam.f(.4); cx, cy = Th(560, 560); fh, dh = new_fig_layer()     # hourglass emptying
    def H_(px, py): return ((cx + px * zh) * SS, (cy + py * zh) * SS)
    sand = 1 - ss(14, 29, t)
    dh.polygon([H_(-40, -60), H_(40, -60), H_(5, 0), H_(40, 60), H_(-40, 60), H_(-5, 0)], fill=(255, 240, 215, 170))
    dh.polygon([H_(-30 * sand, -50 + 50 * (1 - sand)), H_(30 * sand, -50 + 50 * (1 - sand)), H_(0, -2)], fill=(214, 150, 80, 255))
    dh.polygon([H_(-35 * (1 - sand), 55), H_(35 * (1 - sand), 55), H_(0, 55 - 45 * (1 - sand))], fill=(214, 150, 80, 255))
    composite_fig(img, fh, .2)
    return img, L

def blue_world(t):
    """never knew: sits under the stars, no hourglass, shooting stars"""
    cam = Cam(1.45, (540 - 270 / 1.45, 1300), 6 * math.sin(t + 1))
    img = sky(); L = np.zeros((H, W, 3), np.float32); g = draw_env(img, L, cam, t, NIGHT, 1.0)
    T, z = cam.f(1.0); fi, d = new_fig_layer()
    traveller(d, T, z, X, g(X) + 3, 165, '#4f6fa0', '#8fb3e0', seated=True, arm=(.15, .75))
    composite_fig(img, fi, .35)
    for q in range(3):                                    # shooting stars
        ph = (t * .45 + q / 3) % 1
        if ph < .35:
            k = ph / .35; sx = 300 + q * 220 + k * 420; sy = 260 + q * 120 + k * 200
            for j in range(10): glow(L, sx - j * 14, sy - j * 6.5, 3 - j * .2, np.array([1, 1, 1], np.float32), .9 * (1 - j / 10) * (1 - k))
    return img, L

def split(t):
    gi, gl = golden_world(t); bi, bl = blue_world(t)
    xs = np.arange(W)[None, :]; ys = np.arange(H)[:, None]
    edge = 540 + 9 * np.sin(ys / 23.0) + 5 * np.sin(ys / 7.0)
    m = (xs < edge).astype(np.float32)[..., None]
    img = gi * m + bi * (1 - m); L = gl * m + bl * (1 - m)
    img = img * (1 - 0.45 * np.exp(-((xs - edge - 8) ** 2) / 60.0)[..., None]) + np.exp(-((xs - edge) ** 2) / 18.0)[..., None] * .25
    return img, L

def frame(t):
    set_reveal(1.0)
    z, c = camera(t); cam = Cam(z, c, 0)
    if 13.6 < t < 29.4:
        si, sl = split(t); a = min(ss(13.6, 14.6, t), 1 - ss(28.4, 29.4, t))
        if a < 1:
            ni, nl = night_scene(t, cam); si = si * a + ni * (1 - a); sl = sl * a + nl * (1 - a)
        img, L = si, sl
    else:
        img, L = night_scene(t, cam)
    return finish(img, L)
