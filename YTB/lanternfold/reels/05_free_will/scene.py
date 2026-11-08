"""Reel 5 - Did You Choose This? City rooftops at night. frame(t) with t in story seconds (0-55)."""
import os, sys, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.paper import *            # noqa: F401,F403
from engine import paper as P_
from engine.environments import ENVS, draw_env

DUR = 55.0
ENV = ENVS['city_roofs']
WIN = (700., 1010.); WP = .45          # the loop-anchor window, on the far skyline (parallax .45)
BOY_X = 430.
OPEN_Z = 3.3
OPEN_C = (540 + (WIN[0] - 540) / WP, 960 + (WIN[1] - 960) / WP)
WARM = np.array([1.0, .82, .5], np.float32)
PHONE = np.array([.55, .75, 1.0], np.float32)
# memory frames: (world x, world y, appear time, vignette)
MEM = [(170, 760, 15.6, 'parent'), (860, 700, 17.2, 'teacher'), (250, 520, 18.8, 'friends'), (790, 470, 20.4, 'alone'), (520, 360, 22.0, 'baby')]

def camera(t):
    wide, boy, mid = (540., 1060.), (480., 1290.), (540., 1110.)
    def mix(a, b, k): return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
    if t < 4: return OPEN_Z, OPEN_C
    if t < 10: k = ss(4, 10, t); return lerp(OPEN_Z, 1.0, k), mix(OPEN_C, wide, k)
    if t < 15: k = ss(10, 13, t); return lerp(1.0, 1.9, k), mix(wide, boy, k)
    if t < 31: k = ss(15, 17.5, t); return lerp(1.9, 1.0, k), mix(boy, mid, k)
    if t < 45: k = ss(31, 33.5, t); return lerp(1.0, 1.75, k), mix(mid, boy, k)
    k = ss(46, DUR, t); return lerp(1.75, OPEN_Z, k), mix(boy, OPEN_C, k)

def window_light(L, cam, b):
    T, z = cam.f(WP); sx, sy = T(*WIN)
    for dx in (-5, 5):
        for dy in (-7, 7): glow(L, sx + dx * z, sy + dy * z, 4 * z, WARM, .55 * b)
    glow(L, sx, sy, 30 * z, WARM, .22 * b); glow(L, sx, sy, 90 * z, WARM, .05 * b)
    return sx, sy

def thread(L, a, b, p, t, amp=60, col=P_.GOLD, a_=.5, r=2.0):
    """golden thread from a to b, revealed with p"""
    if p <= 0: return
    n = 46
    for i in range(int(n * p)):
        k = i / n; x = lerp(a[0], b[0], k) + amp * math.sin(k * math.pi) * math.sin(t * .7 + a[0]); y = lerp(a[1], b[1], k) - amp * .6 * math.sin(k * math.pi)
        glow(L, x, y, r, col, a_)
    k = (t * .35) % 1
    if k < p:
        x = lerp(a[0], b[0], k) + amp * math.sin(k * math.pi) * math.sin(t * .7 + a[0]); y = lerp(a[1], b[1], k) - amp * .6 * math.sin(k * math.pi)
        glow(L, x, y, 5, col, .8)

def memory(d, T, z, x, y, kind, a):
    """a small lit paper window showing a moment of his past"""
    if a <= 0: return
    w, h = 150, 190
    def Q(px, py): sx, sy = T(x + px, y + py); return (sx * SS, sy * SS)
    al = int(255 * a)
    d.polygon([Q(-w / 2 - 10, -h / 2 - 10), Q(w / 2 + 10, -h / 2 - 10), Q(w / 2 + 10, h / 2 + 10), Q(-w / 2 - 10, h / 2 + 10)], fill=(40, 34, 60, al))
    d.polygon([Q(-w / 2, -h / 2), Q(w / 2, -h / 2), Q(w / 2, h / 2), Q(-w / 2, h / 2)], fill=(250, 214, 140, al))
    sil = (45, 36, 52, al)
    def fig(fx, hh, child=False):
        hr = hh * (.16 if child else .12)
        d.ellipse([*Q(fx - hr, h / 2 - hh), *Q(fx + hr, h / 2 - hh + 2 * hr)], fill=sil)
        d.polygon([Q(fx - hh * .2, h / 2 - hh + 2 * hr), Q(fx + hh * .2, h / 2 - hh + 2 * hr), Q(fx + hh * .26, h / 2), Q(fx - hh * .26, h / 2)], fill=sil)
    if kind == 'parent': fig(-25, 150); fig(30, 85, True)
    elif kind == 'teacher':
        d.polygon([Q(-60, -70), Q(20, -70), Q(20, -10), Q(-60, -10)], fill=(70, 90, 80, al)); fig(45, 140)
    elif kind == 'friends': fig(-35, 130); fig(35, 125)
    elif kind == 'alone':
        fig(10, 120)
        d.line([*Q(-40, -50), *Q(-30, -30)], fill=sil, width=max(2, int(3 * z * SS)))   # a broken heart-ish crack in the glass
    elif kind == 'baby': fig(0, 80, True)

def frame(t):
    reveal = ss(3.6, 8.5, t) * (1 - ss(52.5, DUR - 0.15, t)); set_reveal(reveal)
    z, c = camera(t); cam = Cam(z, c, 10 * math.sin(t / DUR * 6.283))
    img = sky(); L = np.zeros((H, W, 3), np.float32)
    ground = draw_env(img, L, cam, t, ENV, reveal)
    window_light(L, cam, reveal)
    T, z1 = cam.f(1.0); gy = ground(BOY_X) + 3
    fi, d = new_fig_layer()
    standing = ss(31, 33, t)
    if standing < 1:          # sitting on the ledge, phone in hand
        Pf, hc = person(d, T, z1, BOY_X, gy, 150, dress='#4f6fa0', hair='#2a1a10', kind='adult', arm=(.3, .45), face=1, seated=True)
        phone = T(BOY_X + .3 * 150, gy - .47 * 150)
    else:                     # standing at the edge, choosing a direction
        look = 1 if (t % 4) < 2 or t > 41 else -1
        Pf, hc = person(d, T, z1, BOY_X + 60, gy, 165, dress='#4f6fa0', hair='#2a1a10', kind='adult', arm=(.15, .35), face=look)
        phone = None
    mems = []
    for mx, my, ta, kind in MEM:
        a = ss(ta, ta + 1.0, t) * (1 - ss(29.5, 31, t))
        Tm, zm = cam.f(.75); memory(d, Tm, zm, mx, my, kind, a); mems.append((Tm(mx, my), a))
    composite_fig(img, fade_layer(fi, 1 - .0 * standing))
    if phone is not None:
        glow(L, phone[0], phone[1], 5 * z1, PHONE, .9 * reveal * (1 - standing)); glow(L, phone[0], phone[1], 40 * z1, PHONE, .15 * reveal * (1 - standing))
        # threads from the phone to what caused this moment (beats 5-15), then to his memories (15-30)
        cues = [(T(BOY_X + 260, gy - 520), 6.0), (T(BOY_X - 200, gy - 420), 8.0), (T(BOY_X + 140, gy - 700), 10.0)]
        for (pt, ta) in cues:
            p = ss(ta, ta + 1.5, t) * (1 - ss(15, 16.5, t)); thread(L, phone, pt, p, t)
            if p > .9: glow(L, pt[0], pt[1], 10, P_.GOLD, .6 * reveal)
        for (pt, a) in mems: thread(L, phone, pt, a, t, 40)
    # two glowing paths across the city: left and right (beats 32-45)
    paths = ss(33, 35, t) * (1 - ss(46, 48, t))
    if paths > 0:
        start = T(BOY_X + 60, gy - 10)
        thread(L, start, T(-200, gy - 260), paths, t, 120, P_.GOLD, .7, 4.0)
        thread(L, start, T(1300, gy - 300), paths, t, 120, np.array([.6, .8, 1.0], np.float32), .7, 4.0)
    # stillness: every light pulses once together
    pulse = math.exp(-((t - 43.79) / .5) ** 2)
    if pulse > .01: L *= (1 + .6 * pulse)
    out = finish(img, L, reveal=reveal).astype(np.float32) / 255
    Ls = np.zeros((H, W, 3), np.float32)       # loop anchor: one lit window survives the fade
    b = 0.35 + 0.65 * ss(1.0, 1.4, t) if t < 7 else 1.0
    if t > DUR - 0.6: b = 0.35 + 0.65 * (1 - ss(DUR - 0.6, DUR, t))
    window_light(Ls, cam, b); Ls *= (1 - reveal)
    out = 1 - (1 - out) * (1 - np.clip(Ls, 0, 1))
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)
