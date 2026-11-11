"""Reel 9 - Would You Follow the Red Thread? Point of view: YOUR hand, a red thread tied to your little finger.
At 0.8 s the thread snaps tight and races across a firefly meadow to a distant warm light (the one you're meant to meet).
Then it forks: the straight thread vs a winding path full of small lit moments (detours). Built to the virality rules:
big moving subject on frame 0, an event before 3 s, no slow pull-back, a turn at ~8 s. frame(t), story seconds 0-45."""
import os, sys, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.paper import *            # noqa: F401,F403
from engine import paper as P_
from engine.environments import ENVS, draw_env

DUR = 45.0
ENV = ENVS['firefly_meadow']
RED = np.array([1.0, .22, .25], np.float32)
TARGET_X = 820.
MOMENTS = [(300, 1210, 'friends'), (470, 1060, 'alone'), (620, 1180, 'dance'), (730, 1000, 'rain')]

def camera(t):
    hook, push, along = (1.35, (600., 1240.)), (1.6, (700., 1270.)), (1.7, (760., 1265.))
    wide, left, right = (1.25, (560., 1160.)), (1.5, (500., 1140.)), (1.5, (790., 1250.))
    keys = [(0, hook), (1.4, hook), (3.2, push), (8.8, along), (10.3, wide), (17.5, wide), (19, left), (24.5, left), (26, right),
            (32, right), (33.5, wide), (38.5, wide), (41.5, hook), (DUR, hook)]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            k = ss(t0, t1, t); return lerp(a[0], b[0], k), (lerp(a[1][0], b[1][0], k), lerp(a[1][1], b[1][1], k))
    return hook

def hand_slide(t):
    """POV hand: on screen at the hook and the end, slides out of frame as the camera rushes along the thread"""
    return 900 * ss(1.6, 3.0, t) * (1 - ss(39, 41.5, t))

def pov_hand(d, slide):
    """your hand, palm towards you, bottom-left of the frame (screen coords). Returns the little-finger ring point."""
    def S(x, y): return (x * SS, (y + slide) * SS)
    skin, shade = (231, 196, 160, 255), (205, 166, 132, 255)
    d.rounded_rectangle([*S(170, 1570), *S(480, 1960)], radius=70 * SS, fill=skin)
    for x0, top, w in ((185, 1300, 66), (258, 1255, 68), (332, 1290, 66), (404, 1370, 60)):
        d.rounded_rectangle([*S(x0, top), *S(x0 + w, 1640)], radius=int(w / 2 * SS), fill=skin)
        d.line([*S(x0 + 8, 1500 + (top - 1300) * .2), *S(x0 + w - 8, 1500 + (top - 1300) * .2)], fill=shade, width=3 * SS)
    d.polygon([S(170, 1700), S(90, 1560), S(110, 1520), S(200, 1600)], fill=skin)                # thumb
    rx, ry = 434, 1450
    d.ellipse([*S(rx - 36, ry - 12), *S(rx + 36, ry + 12)], outline=(214, 40, 52, 255), width=7 * SS)  # the knot
    return rx, ry + slide

def thread_pts(t, ring, T, ground, snap):
    """screen points of the main thread: slack loop before the snap, then a taut line to the target"""
    tx = T(TARGET_X, ground(TARGET_X) - 95)
    pts = []
    for i in range(40):
        k = i / 39
        x = lerp(ring[0], tx[0], k); y = lerp(ring[1], tx[1], k)
        sag = (1 - snap) * 420 * math.sin(k * math.pi) + snap * 40 * math.sin(k * math.pi)
        wob = (1 - snap) * 25 * math.sin(k * 9 + t * 3)
        pts.append((x + wob, y + sag))
    return pts

def winding_pts(T, ground, p):
    """the long way round: from the fork through every lit moment to the same light"""
    path = [(300, 1460), (250, 1330)] + [(x, y + 70) for x, y, _ in MOMENTS] + [(TARGET_X, ground(TARGET_X) - 95)]
    out = []
    for a, b in zip(path, path[1:]):
        for q in range(12): k = q / 12; out.append(T(lerp(a[0], b[0], k) + 30 * math.sin(k * 6.28), lerp(a[1], b[1], k)))
    return out[:max(2, int(len(out) * p))]

def draw_thread(d, L, pts, b, t, width=6):
    if b <= .01 or len(pts) < 2: return
    a = int(255 * min(1, b))
    d.line([(x * SS, y * SS) for x, y in pts], fill=(222, 45, 58, a), width=int(width * SS), joint='curve')
    for i, (x, y) in enumerate(pts[::2]):
        glow(L, x, y, 7, RED, .35 * b)
    k = (t * .5) % 1; x, y = pts[int(k * (len(pts) - 1))]; glow(L, x, y, 14, RED, .7 * b)            # a pulse travels along it

def moment(d, T, x, y, kind, a, warm):
    """a small lit paper window on the winding path: one of the detours"""
    if a <= .01: return
    def Q(px, py): sx, sy = T(x + px, y + py); return (sx * SS, sy * SS)
    al = int(255 * a); w, h = 92, 118
    d.polygon([Q(-w / 2 - 7, -h / 2 - 7), Q(w / 2 + 7, -h / 2 - 7), Q(w / 2 + 7, h / 2 + 7), Q(-w / 2 - 7, h / 2 + 7)], fill=(30, 40, 52, al))
    c = (np.array([150, 160, 190]) * (1 - warm) + np.array([250, 214, 140]) * warm).astype(int)
    d.polygon([Q(-w / 2, -h / 2), Q(w / 2, -h / 2), Q(w / 2, h / 2), Q(-w / 2, h / 2)], fill=(*c, al))
    sil = (40, 34, 50, al)
    def fig(fx, hh):
        hr = hh * .13
        d.ellipse([*Q(fx - hr, h / 2 - hh), *Q(fx + hr, h / 2 - hh + 2 * hr)], fill=sil)
        d.polygon([Q(fx - hh * .2, h / 2 - hh + 2 * hr), Q(fx + hh * .2, h / 2 - hh + 2 * hr), Q(fx + hh * .26, h / 2), Q(fx - hh * .26, h / 2)], fill=sil)
    if kind == 'friends': fig(-22, 80); fig(0, 86); fig(22, 78)
    elif kind == 'alone': fig(10, 80); d.line([*Q(-34, -40), *Q(-24, -18)], fill=sil, width=max(2, int(3 * SS)))
    elif kind == 'dance': fig(-14, 84); fig(16, 78)
    elif kind == 'rain':
        fig(0, 82)
        for q in range(6): d.line([*Q(-40 + q * 15, -55), *Q(-44 + q * 15, -38)], fill=(90, 110, 150, al), width=max(1, int(2 * SS)))

def frame(t):
    set_reveal(1.0)
    z, c = camera(t); cam = Cam(z, c, 3 * math.sin(t * .5))
    img = sky(); L = np.zeros((H, W, 3), np.float32)
    ground = draw_env(img, L, cam, t, ENV, 1.0)
    T, z1 = cam.f(1.0)
    snap = ss(.8, 1.4, t) * (1 - ss(43.2, 44.8, t))
    fork = ss(9, 10.5, t) * (1 - ss(33.5, 38, t))
    straight_b = 1.0 * (1 - .55 * ss(18, 19.5, t) * (1 - ss(24.5, 26, t))) * (1 + .35 * ss(25, 26.5, t) * (1 - ss(32, 33.5, t)))
    wind_b = fork * (.6 + .6 * ss(18, 19.5, t) * (1 - ss(24.5, 26, t)) - .35 * ss(25, 26.5, t) * (1 - ss(32, 33.5, t)))
    fi, d = new_fig_layer()
    # the one you're meant to meet: a small figure with a warm light, far across the meadow
    them = ss(.9, 1.6, t) * (1 - ss(43, 44.5, t))
    if them > .01:
        gx = ground(TARGET_X) + 3; ff, dfg = new_fig_layer()
        person(dfg, T, z1, TARGET_X, gx, 150, dress='#c97a5a', hair='#3a2418', kind='adult', face=-1)
        composite_fig(img, fade_layer(ff, them), .3); sx, sy = T(TARGET_X, gx - 95); glow(L, sx, sy, 40 * z1, P_.WARM, .35 * them)
    for x, y, kind in MOMENTS:
        moment(d, T, x, y, kind, fork, ss(18, 19.5, t) * (1 - ss(24.5, 26, t)))
    if fork > .01: draw_thread(d, L, winding_pts(T, ground, fork), wind_b, t, 4)
    slide = hand_slide(t)
    ring = (434, 1450 + slide)
    if slide < 880 or True:
        pts = thread_pts(t, ring, T, ground, snap)
        draw_thread(d, L, pts, straight_b, t, 7)
    composite_fig(img, fi, .35)
    if slide < 900:
        fh, dh = new_fig_layer(); pov_hand(dh, slide); composite_fig(img, fh, .45)
    flash = math.exp(-((t - 1.05) / .18) ** 2)                      # the snap: a quick red flash along the thread
    if flash > .02: L += flash * .18 * RED
    still = math.exp(-((t - 33.6) / .9) ** 2)
    if still > .02: L *= (1 + .3 * still)
    return finish(img, L)
