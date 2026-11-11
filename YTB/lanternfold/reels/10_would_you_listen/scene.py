"""Reel 10 - Would You Listen? Autumn forest at golden hour, two people on a bench. Above the other person's head floats a
sealed paper thought-bubble. At ~1 s it cracks open: light pours out and small paper notes (their thoughts) drift out.
At ~8 s the turn: some notes turn grey. Warm notes pull the two closer, grey ones push them apart. Hook-first, loops:
the bubble closes again at the end. frame(t), story seconds 0-42."""
import os, sys, math, copy, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.paper import *            # noqa: F401,F403
from engine import paper as P_
from engine.environments import ENVS, draw_env

DUR = 42.0
ENV = copy.deepcopy(ENVS['autumn_forest']); ENV['sun'] = (170, 760, 60, '#ffbf6a')     # sun off to the side, not behind a face
YOU_X, THEM_X, HT = 430., 610., 230.
GOLDW = np.array([1.0, .85, .5], np.float32)

def camera(t):
    hook, wide, close, apart = (2.4, (600., 950.)), (1.45, (520., 1010.)), (1.75, (520., 1045.)), (1.6, (520., 1030.))
    keys = [(0, hook), (1.5, hook), (3.0, wide), (13.5, wide), (15, close), (20.5, close), (22, apart), (29, apart),
            (30.5, wide), (36, wide), (39.5, hook), (DUR, hook)]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            k = ss(t0, t1, t); return lerp(a[0], b[0], k), (lerp(a[1][0], b[1][0], k), lerp(a[1][1], b[1][1], k))
    return hook

def bubble(d, L, T, z, cx, cy, op, t):
    """paper thought-bubble: two halves of a folded cloud; op 0 = sealed, 1 = open (halves tilt apart, light pours out)"""
    for side in (-1, 1):
        dx, dy = side * 46 * op, -20 * op
        def Q(px, py): sx, sy = T(cx + px + dx, cy + py + dy); return (sx * SS, sy * SS)
        blobs = [(-40, 0, 38), (0, -14, 46), (40, 0, 38), (-20, 18, 32), (20, 18, 32)]
        for bx, by, r in blobs:
            if bx * side < -1: continue                                   # each half keeps its own side of the cloud
            d.ellipse([*Q(bx - r, by - r), *Q(bx + r, by + r)], fill=(246, 236, 214, 255))
        d.line([Q(0, -58), Q(0, 48)], fill=(205, 186, 150, 255), width=max(2, int(3 * z * SS)))      # the seam
    for i, (bx, by, r) in enumerate([(-6, 78, 12), (-14, 106, 7)]):                                   # little trailing dots
        a, b = T(cx + bx, cy + by); d.ellipse([(a - r * z) * SS, (b - r * z) * SS, (a + r * z) * SS, (b + r * z) * SS], fill=(246, 236, 214, 255))
    sx, sy = T(cx, cy)
    glow(L, sx, sy, 30 * z, GOLDW, .25 + .55 * op); glow(L, sx, sy, 140 * z, GOLDW, .12 * op)
    if op > .05:
        for q in range(9):                                               # light rays
            a = -math.pi / 2 + (q - 4) * .32
            for s in range(1, 8): glow(L, sx + math.cos(a) * s * 22 * z, sy + math.sin(a) * s * 22 * z, 6 * z, GOLDW, .25 * op * (1 - s / 8))

def notes(d, L, T, z, cx, cy, t, amount, grey):
    """their thoughts: small paper notes drifting out between the two of them; `grey` = how many turned hard"""
    if amount <= .01: return
    for q in range(14):
        ph = (t * .11 + q / 14) % 1; k = min(1, amount * 1.4 - q / 20)
        if k <= 0: continue
        x = cx + (q % 2 * 2 - 1) * 40 + 170 * math.sin(q * 1.9 + t * .3) * ph - 60 * ph
        y = cy - 30 - ph * 300 + 20 * math.sin(t + q)
        is_grey = (q % 3 == 0) and grey > .3 or (q % 3 == 1 and grey > .7)
        col = (150, 150, 160) if is_grey else (252, 222, 150)
        a = int(255 * k * math.sin(ph * math.pi) ** .5)
        def Q(px, py): sx, sy = T(x + px, y + py); return (sx * SS, sy * SS)
        ang = math.sin(t * 1.3 + q) * .5; cs, sn = math.cos(ang), math.sin(ang)
        pts = [Q(px * cs - py * sn, px * sn + py * cs) for px, py in ((-16, -10), (16, -10), (16, 10), (-16, 10))]
        d.polygon(pts, fill=(*col, a))
        d.line([Q(-10, -3), Q(10, -3)], fill=(120, 100, 80, a), width=max(1, int(1.5 * z * SS)))
        d.line([Q(-10, 3), Q(6, 3)], fill=(120, 100, 80, a), width=max(1, int(1.5 * z * SS)))
        sx, sy = T(x, y)
        if not is_grey: glow(L, sx, sy, 9 * z, GOLDW, .25 * k)

def bench(d, T, z, x0, x1, gy):
    def Q(px, py): sx, sy = T(px, gy - py); return (sx * SS, sy * SS)
    d.polygon([Q(x0, 80), Q(x1, 80), Q(x1, 92), Q(x0, 92)], fill='#6b3f2a')
    d.polygon([Q(x0 + 10, 120), Q(x1 - 10, 120), Q(x1 - 10, 132), Q(x0 + 10, 132)], fill='#6b3f2a')
    for lx in (x0 + 18, x1 - 30): d.polygon([Q(lx, 0), Q(lx + 12, 0), Q(lx + 12, 82), Q(lx, 82)], fill='#5a3423')

def frame(t):
    set_reveal(1.0)
    z, c = camera(t); cam = Cam(z, c, 3 * math.sin(t * .45))
    img = sky(); L = np.zeros((H, W, 3), np.float32)
    ground = draw_env(img, L, cam, t, ENV, 1.0)
    T, z1 = cam.f(1.0); gy = ground(520) + 3
    op = ss(.8, 1.5, t) * (1 - ss(38.5, 41, t))
    grey = ss(8, 9.5, t) * (1 - ss(13.5, 15, t)) + ss(21, 22.5, t) * (1 - ss(28.5, 30, t))
    lean = 28 * ss(14, 16, t) * (1 - ss(20.5, 22, t)) - 34 * ss(21.5, 23, t) * (1 - ss(29, 31, t))    # closer / apart
    warm_dim = .25 * ss(21, 22.5, t) * (1 - ss(28.5, 30, t))
    fi, d = new_fig_layer()
    bench(d, T, z1, 330, 720, gy)
    person(d, T, z1, YOU_X + lean, gy, HT, dress='#4f6f9a', hair='#2a1a10', kind='adult', face=1, seated=True, arm=(.22, .42))
    Pf, hc = person(d, T, z1, THEM_X - lean, gy, HT, dress='#b8604a', hair='#5a3420', kind='adult', face=-1, seated=True, arm=(.22, .42))
    composite_fig(img, fi, .4)
    fb, db = new_fig_layer()
    bx, by = THEM_X - lean - 10, gy - HT * .52 - 150
    notes(db, L, T, z1, bx, by, t, ss(1.3, 3, t) * (1 - ss(37, 39.5, t)), grey)
    bubble(db, L, T, z1, bx, by, op, t)
    composite_fig(img, fb, .25)
    if warm_dim > 0: img *= (1 - warm_dim * np.array([.0, .15, .3], np.float32))                    # the light cools when it hurts
    still = math.exp(-((t - 29.3) / .9) ** 2)
    if still > .02: L *= (1 + .3 * still)
    return finish(img, L)
