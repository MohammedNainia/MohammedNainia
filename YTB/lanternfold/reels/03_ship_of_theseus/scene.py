"""Reel 3 - Is It Still You? (Ship of Theseus). Dusk sea cliff. frame(t) with t in story seconds (0-55)."""
import os, sys, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.paper import *            # noqa: F401,F403
from engine import paper as P_
from engine.environments import ENVS, draw_env, shape

DUR = 55.0
ENV = dict(ENVS['dusk_sea'], sun=(250., 1170., 38, '#ffb070'))   # sun moved to the far left horizon
SUN = ENV['sun'][:2]                  # loop anchor: the low sun on the horizon (parallax .4)
SEA = ENV['layers'][2]                # front sea layer: boats float on it
SHIP_NEW, SHIP_OLD = 960., 745.       # x of the repaired ship and the rebuilt original
GIRL_X = 430.
OPEN_Z = 3.0
OPEN_C = (540 + (SUN[0] - 540) / .4, 960 + (SUN[1] - 960) / .4)   # centres the sun (parallax .4) on screen
OLD = {'plank': '#6e4a31', 'sail': '#e3d5b5', 'mast': '#4e3524'}
NEW = {'plank': '#c8925c', 'sail': '#fbf6ea', 'mast': '#93613a'}
PARTS = [5.5 + i * 1.25 for i in range(6)]     # story time each part gets replaced: 4 planks, sail, mast

def camera(t):
    sea, girl, wide = (850., 1150.), (560., 1190.), (540., 1040.)
    def mix(a, b, k): return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
    if t < 4: return OPEN_Z, OPEN_C
    if t < 10: k = ss(4, 10, t); return lerp(OPEN_Z, 1.6, k), mix(OPEN_C, sea, k)
    if t < 21.5: return 1.6, (lerp(850, 830, ss(14, 18, t)), 1150.)
    if t < 46: k = ss(21.5, 23.5, t); return lerp(1.6, 1.85, k), mix((830., 1150.), girl, k)
    if t < 51: k = ss(46, 50.5, t); return lerp(1.85, 1.0, k), mix(girl, wide, k)
    k = ss(51, DUR, t); return lerp(1.0, OPEN_Z, k), mix(wide, OPEN_C, k)

def boat(d, L, T, z, x, t, cols, scale=1.0, appear=1.0):
    """paper sailing boat; cols = list of 6 colours (4 hull planks, sail, mast)"""
    if appear <= 0: return
    y = shape(SEA, t)(x) + 4; bob = 3 * math.sin(t * 1.3 + x)
    def Q(px, py): sx, sy = T(x + px * scale, y + py * scale + bob); return (sx * SS, sy * SS)
    hw, hb, hh = 110, 78, 48
    for i in range(4):               # hull planks, top to bottom
        y0, y1 = -hh + i * hh / 4, -hh + (i + 1) * hh / 4
        w0 = hw - (hw - hb) * (i / 4); w1 = hw - (hw - hb) * ((i + 1) / 4)
        if appear > (i + 1) / 6: d.polygon([Q(-w0, y0), Q(w0, y0), Q(w1, y1), Q(-w1, y1)], fill=cols[i])
    if appear > 5 / 6: d.line([Q(0, -hh), Q(0, -hh - 170)], fill=cols[5], width=max(2, int(5 * z * scale * SS)))
    if appear >= 1: d.polygon([Q(6, -hh - 160), Q(6, -hh - 14), Q(92, -hh - 14)], fill=cols[4])

def ship_new_cols(t):
    return [NEW[k] if t >= PARTS[i] else OLD[k] for i, k in enumerate(['plank'] * 4 + ['sail', 'mast'])]

def girl(d, T, z, t, x, y, stage, alpha_fade=None):
    spec = [('child', 105, '#d8b45a', HAIR), ('adult', 135, '#6a95a0', '#3a2418'),
            ('adult', 158, '#a85a4c', '#4a3020'), ('old', 148, '#8a5a6a', GREY)][stage]
    kind, h, coat, hair = spec
    return person(d, T, z, x, y, h, dress=coat, hair=hair, kind=kind, arm=(.18, .38), face=1)

def frame(t):
    reveal = ss(3.6, 8.5, t) * (1 - ss(52.5, DUR - 0.15, t)); set_reveal(reveal)
    z, c = camera(t); cam = Cam(z, c, 10 * math.sin(t / DUR * 6.283))
    img = sky(); L = np.zeros((H, W, 3), np.float32)
    ground = draw_env(img, L, cam, t, ENV, reveal)
    Tb, zb = cam.f(SEA.get('p', .75) + .1)
    fb, db = new_fig_layer()
    boat(db, L, Tb, zb, SHIP_NEW, t, ship_new_cols(t))
    for i, pt in enumerate(PARTS):    # a small spark each time a part is swapped
        if 0 < t - pt < .8:
            k = t - pt; sx, sy = Tb(SHIP_NEW + (-60 + i * 25 if i < 4 else 40), shape(SEA, t)(SHIP_NEW) - (20 if i < 4 else 120))
            glow(L, sx, sy, 10 * zb, P_.GOLD, .7 * (1 - k / .8) * reveal)
    rebuild = ss(15, 19.5, t)          # the old planks come back together
    if rebuild > 0:
        boat(db, L, Tb, zb, SHIP_OLD, t, [OLD[k] for k in ['plank'] * 4 + ['sail', 'mast']], appear=rebuild)
    composite_fig(img, fb, 0.35)
    # the girl on the cliff, ageing in place
    T, z1 = cam.f(1.0); gy = ground(GIRL_X) + 3
    if 21 < t < 51.5:
        edges = [26.5, 30.5, 34.5]
        stage = sum(t >= e for e in edges)
        fi, d = new_fig_layer(); girl(d, T, z1, t, GIRL_X, gy, stage)
        a = min(1, ss(21, 22.5, t), 1 - ss(50.5, 51.5, t))
        for e in edges:
            if abs(t - e) < .3: a = min(a, abs(t - e) / .3)
        composite_fig(img, fade_layer(fi, a))
        ghost = ss(38.5, 41, t) * (1 - ss(50.5, 51.5, t))   # her younger self beside her, equal in light
        if ghost > 0:
            fg, dg = new_fig_layer(); girl(dg, T, z1, t, GIRL_X - 95, ground(GIRL_X - 95) + 3, 0)
            composite_fig(img, fade_layer(fg, .55 * ghost), 0.2)
            sx, sy = T(GIRL_X - 95, gy - 60); glow(L, sx, sy, 60 * z1, P_.GOLD, .08 * ghost * reveal)
    out = finish(img, L, reveal=reveal).astype(np.float32) / 255
    # loop anchor: the sun survives the fade (same position at t=0 and t=DUR)
    Ts, zs = cam.f(.4); sx, sy = Ts(*SUN); Ls = np.zeros((H, W, 3), np.float32)
    b = 0.35 + 0.65 * ss(1.0, 1.4, t) if t < 10 else 1.0
    if t > DUR - 0.6: b = 0.35 + 0.65 * (1 - ss(DUR - 0.6, DUR, t))
    glow(Ls, sx, sy, 9 * zs ** .5, np.array([1, .95, .85], np.float32), .9 * b)
    glow(Ls, sx, sy, 45 * zs ** .5, hexc('#ffb070'), .3 * b)
    Ls *= (1 - reveal)
    out = 1 - (1 - out) * (1 - np.clip(Ls, 0, 1))
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)
