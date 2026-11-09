"""Reel 7 - Would You Live Forever? A gothic castle balcony under the moon. An ageless count (original paper design:
pale, black high-collar cape with crimson lining) holds out a glowing cup. Hook-first: frame 0 = the cup held out to
the viewer; the reel ends on the same shot. frame(t), t in story seconds 0-55."""
import os, sys, math, copy, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.paper import *            # noqa: F401,F403
from engine import paper as P_
from engine.environments import ENVS, draw_env

DUR = 55.0
X, HT = 580., 225.                     # the count's feet x, height
HOOK = (2.5, (600., 1240.))           # close on the cup
CUP = np.array([1.0, .45, .32], np.float32); GOLDC = P_.GOLD
FRIENDS = [(190, 170, '#b8775a', '#6b3e22', 22.5), (275, 178, '#5f7fa8', '#2a1a10', 24.5), (360, 164, '#a86b8f', '#4a2c1c', 26.5), (445, 172, '#7d9a6a', '#3a2418', 28.5)]

def camera(t):
    wide, mid, far = (520., 1090.), (430., 1150.), (510., 1110.)
    def mix(a, b, k): return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
    if t < 5: k = ss(0, 5, t); return lerp(HOOK[0], 2.0, k), mix(HOOK[1], (600., 1300.), k)
    if t < 12: k = ss(5, 10.5, t); return lerp(2.0, 1.45, k), mix((600., 1300.), wide, k)
    if t < 30: k = ss(20, 22.5, t); return lerp(1.45, 1.75, k), mix(wide, mid, k)
    if t < 46: k = ss(30, 33, t); return lerp(1.75, 1.55, k), mix(mid, far, k)
    k = ss(46.3, 52.5, t); return lerp(1.55, HOOK[0], k), mix(far, HOOK[1], k)

def env_at(t):
    """time passing (12-30): the moon swings across the sky again and again, dawn washes pulse"""
    e = copy.deepcopy(ENVS['gothic_castle']); k = ss(12, 14, t) * (1 - ss(28, 30, t))
    if k > 0:
        a = (t - 12) * 1.9; x, y, r, c = e['moon']
        e['moon'] = (x + k * 300 * math.sin(a), y + k * 120 * (1 - math.cos(a)), r, c)
    return e

def count(d, L, T, z, x, gy, t, reach):
    """the immortal: cape + collar behind, person on top (pale skin), cup in the outstretched hand"""
    h = HT
    def Q(px, py): sx, sy = T(x + px * h, gy - py * h); return (sx * SS, sy * SS)
    sway = .015 * math.sin(t * .8)
    d.polygon([Q(-.05, .66), Q(.07, .66), Q(.30 + sway, .0), Q(-.30 + sway, .0)], fill='#0e0a14')           # cape
    d.polygon([Q(-.03, .64), Q(.05, .64), Q(.22 + sway, .02), Q(.02, .02)], fill='#7a1626')                 # crimson lining
    d.polygon([Q(-.13, .63), Q(-.02, .64), Q(-.18, .93)], fill='#0e0a14'); d.polygon([Q(.13, .63), Q(.02, .64), Q(.18, .93)], fill='#0e0a14')
    d.polygon([Q(-.10, .64), Q(-.03, .65), Q(-.14, .86)], fill='#7a1626'); d.polygon([Q(.10, .64), Q(.03, .65), Q(.14, .86)], fill='#7a1626')
    old = P_.SKIN; P_.SKIN = '#ece4e8'
    hand = (lerp(.24, .36, reach), lerp(.50, .56, reach))
    Pf, hc = person(d, T, z, x, gy, h, dress='#16111c', hair='#0b0910', kind='adult', arm=hand, face=1)
    P_.SKIN = old
    hx, hy = hand; cx, cy = x + hx * h, gy - hy * h                                                          # cup
    def C(px, py): sx, sy = T(cx + px, cy - py); return (sx * SS, sy * SS)
    d.polygon([C(-11, 4), C(11, 4), C(8, 18), C(-8, 18)], fill='#c79a4a')
    d.line([C(0, 4), C(0, -6)], fill='#c79a4a', width=max(2, int(3 * z * SS))); d.line([C(-6, -6), C(6, -6)], fill='#c79a4a', width=max(2, int(3 * z * SS)))
    sx, sy = T(cx, cy - 16); pulse = 1 + .1 * math.sin(t * 2.3)
    glow(L, sx, sy, 7 * z, GOLDC, .8 * pulse); glow(L, sx, sy, 30 * z, CUP, .35 * pulse); glow(L, sx, sy, 110 * z, CUP, .08 * pulse)

def balcony(d, T, z, gy):
    def Q(px, py): sx, sy = T(px, gy - py); return (sx * SS, sy * SS)
    d.polygon([Q(-200, 62), Q(760, 62), Q(760, 76), Q(-200, 76)], fill='#3a2840')
    for bx in np.arange(-180, 760, 44):
        d.polygon([Q(bx, 0), Q(bx + 14, 0), Q(bx + 17, 30), Q(bx + 14, 62), Q(bx, 62), Q(bx - 3, 30)], fill='#33233a')

def bats(d, T, z, t):
    for q in range(4):
        ph = (t * .07 + q * .27) % 1; bx = -100 + ph * 1300; by = 640 + 90 * q + 30 * math.sin(t * 2 + q)
        fl = 10 * math.sin(t * 14 + q)
        def Q(px, py): sx, sy = T(bx + px, by + py); return (sx * SS, sy * SS)
        d.polygon([Q(-16, -fl), Q(-5, 0), Q(0, -4), Q(5, 0), Q(16, -fl), Q(0, 5)], fill='#0a0712')

def pages(L, T, z, t):
    """every book: glowing pages drifting up around him (12-21)"""
    k = ss(12, 13.5, t) * (1 - ss(20, 22, t))
    if k <= 0: return
    for q in range(14):
        ph = (t * .12 + q / 14) % 1; px = X + 230 * math.sin(q * 2.4 + t * .3); py = 1420 - ph * 620
        sx, sy = T(px, py); glow(L, sx, sy, 5 * z, np.array([1, .93, .75], np.float32), .55 * k * math.sin(ph * math.pi))

def dawn(L, t):
    """every sunrise: warm washes across the horizon"""
    k = ss(12.5, 14, t) * (1 - ss(19.5, 21, t))
    if k <= 0: return
    w = max(0, math.sin((t - 12.5) * 2.2)) ** 2
    glow(L, 540, 1300, 700, np.array([1, .55, .35], np.float32), .22 * k * w)

def frame(t):
    set_reveal(1.0)
    z, c = camera(t); cam = Cam(z, c, 4 * math.sin(t * .4))
    img = sky(); L = np.zeros((H, W, 3), np.float32)
    ground = draw_env(img, L, cam, t, env_at(t), 1.0)
    dawn(L, t)
    T, z1 = cam.f(1.0); gy = ground(X) + 3
    fb, db = new_fig_layer(); bats(db, *cam.f(.6), t); composite_fig(img, fb, .1)
    pages(L, T, z1, t)
    for fx, fh, dress, hair, out in FRIENDS:                       # the people he loved: they age, then their light goes out
        a = ss(21, 22.5, t) * (1 - ss(out, out + 1.2, t))
        if a <= .01: continue
        ff, dfr = new_fig_layer(); age = ss(out - 2.2, out - .3, t)
        hc_ = tuple(int(lerp(int(hair[i:i + 2], 16), 200, age)) for i in (1, 3, 5))
        person(dfr, T, z1, fx, ground(fx) + 3, fh * (1 - .05 * age), dress=dress, hair='#%02x%02x%02x' % hc_, kind='old' if age > .5 else 'adult', face=1)
        composite_fig(img, fade_layer(ff, a), .35)
        sx, sy = T(fx, ground(fx) - fh * .5); glow(L, sx, sy, 8 * z1, P_.WARM, .5 * a * (1 - age * .5))
    new = ss(36.5, 38.5, t) * (1 - ss(43.5, 45.5, t))                # ...or more time to love again
    if new > .01:
        ff, dfr = new_fig_layer(); person(dfr, T, z1, 440, ground(440) + 3, 172, dress='#c98a5a', hair='#5a3420', kind='adult', face=1)
        composite_fig(img, fade_layer(ff, new), .35); sx, sy = T(440, ground(440) - 86); glow(L, sx, sy, 10 * z1, P_.WARM, .6 * new)
    fi, d = new_fig_layer()
    reach = 1 - ss(5, 7, t) * (1 - ss(45.5, 48, t))                 # cup held out to the viewer at the hook and the end
    count(d, L, T, z1, X, gy, t, reach); balcony(d, T, z1, gy)
    composite_fig(img, fi, .4)
    still = math.exp(-((t - 44.9) / .9) ** 2)
    if still > .02: L *= (1 + .3 * still)
    return finish(img, L)
