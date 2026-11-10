"""Reel 8 - Would You Undo Your Biggest Regret? A stone ledge by the sea at dusk. Someone holds out an old pocket watch.
One turn rewinds time: the sun climbs back up, the waves run backwards, and the person who walked away comes back.
Small warm lights around the hero = what the regret taught them; they dim while the regret is undone.
Hook-first: frame 0 = the watch held out; the reel ends on the same shot. frame(t), t in story seconds 0-55."""
import os, sys, math, copy, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.paper import *            # noqa: F401,F403
from engine import paper as P_
from engine.environments import ENVS, draw_env

DUR = 55.0
X, HT = 470., 215.
HOOK = (2.5, (500., 1200.))
GOLDW = np.array([1.0, .82, .45], np.float32)

def camera(t):
    wide, mid = (470., 1060.), (380., 1110.)
    def mix(a, b, k): return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
    if t < 5: k = ss(0, 5, t); return lerp(HOOK[0], 2.05, k), mix(HOOK[1], (490., 1220.), k)
    if t < 12: k = ss(5, 10.5, t); return lerp(2.05, 1.45, k), mix((490., 1220.), wide, k)
    if t < 30: k = ss(19, 22, t); return lerp(1.45, 1.7, k), mix(wide, mid, k)
    if t < 46: k = ss(30, 33, t); return lerp(1.7, 1.5, k), mix(mid, wide, k)
    k = ss(46.3, 52.5, t); return lerp(1.5, HOOK[0], k), mix(wide, HOOK[1], k)

def rewind(t):
    """0 -> 1 while time runs backwards (12-21), eases back to 0 as time resumes (28-33)"""
    return ss(12, 14, t) * (1 - ss(28, 33, t))

def env_time(t):
    """the sea's own clock: runs backwards during the rewind"""
    if t < 12: return t
    if t < 21: return 12 - (t - 12) * 1.6
    return 12 - 9 * 1.6 + (t - 21)

def env_at(t):
    e = copy.deepcopy(ENVS['dusk_sea']); r = ss(12, 20, t) * (1 - ss(28, 33, t))
    x, y, rad, col = e['sun']; e['sun'] = (820, y - 260 * r, rad, col)            # sun off to the side, away from the watch               # the sunset reverses: sun climbs back up
    if r > 0: e['sky'] = ('#3b2f5c', '#f2a27a') if r < .5 else ('#4f4a7a', '#f6c08e')
    return e

def watch(d, L, T, z, cx, cy, t, rw):
    def C(px, py): sx, sy = T(cx + px, cy + py); return (sx * SS, sy * SS)
    r = 24
    d.ellipse([*C(-r - 3, -r - 3), *C(r + 3, r + 3)], fill='#a57a35')
    d.ellipse([*C(-r, -r), *C(r, r)], fill='#f3e6c4')
    d.rectangle([*C(-3, -r - 9), *C(3, -r - 3)], fill='#a57a35')
    spin = -t * 6 * rw * 3 + t * .5 * (1 - rw)                                    # hands run backwards during the rewind
    for ln, sp in ((17, 1.0), (11, .08)):
        a = spin * sp; d.line([C(0, 0), C(ln * math.sin(a), -ln * math.cos(a))], fill='#3a2a1a', width=max(2, int(2.2 * z * SS)))
    sx, sy = T(cx, cy); pulse = 1 + .12 * math.sin(t * 2.6)
    glow(L, sx, sy, 34 * z, GOLDW, .12 * pulse * (1 + rw)); glow(L, sx, sy, 120 * z, GOLDW, .05 * (1 + 2 * rw))

def frame(t):
    set_reveal(1.0)
    z, c = camera(t); cam = Cam(z, c, 4 * math.sin(t * .4))
    img = sky(); L = np.zeros((H, W, 3), np.float32)
    ground = draw_env(img, L, cam, env_time(t), env_at(t), 1.0)
    T, z1 = cam.f(1.0); gy = ground(X) + 3; rw = rewind(t)
    # the one who walked away: far down the ledge at first; during the rewind they walk backwards to the hero
    back = ss(13, 20, t)
    other = ss(10.5, 12.5, t) * (1 - ss(29, 31, t)) + ss(36.5, 38.5, t) * (1 - ss(43.5, 45.5, t))
    if other > .01:
        ox = lerp(120, 365, back) if t < 33 else 365
        ff, df = new_fig_layer(); person(df, T, z1, ox, ground(ox) + 3, 200, dress='#b86f5a', hair='#3a2418', kind='adult', face=1)
        composite_fig(img, fade_layer(ff, other * (.55 + .45 * back)), .35)
    # what the regret taught: small warm lights around the hero; dim while the regret is undone
    lessons = ss(4, 6, t) * (1 - ss(45.5, 47.5, t)) * (1 - .85 * rw) * (1 - .5 * ss(36.5, 38.5, t) * (1 - ss(43.5, 45.5, t)))
    for q in range(6):
        a = q * 1.05 + t * .35; lx = X + 120 * math.cos(a); ly = gy - HT * .55 + 70 * math.sin(a * 1.3)
        sx, sy = T(lx, ly); glow(L, sx, sy, 5 * z1, P_.WARM, .8 * lessons); glow(L, sx, sy, 22 * z1, P_.WARM, .15 * lessons)
    fi, d = new_fig_layer()
    reach = 1 - ss(5, 7, t) * (1 - ss(45.5, 48, t))
    hand = (lerp(.24, .36, reach), lerp(.50, .56, reach))
    person(d, T, z1, X, gy, HT, dress='#3f5d7a', hair='#2a1a10', kind='adult', arm=hand, face=1)
    watch(d, L, T, z1, X + hand[0] * HT + 6, gy - hand[1] * HT - 4, t, rw)
    composite_fig(img, fi, .4)
    still = math.exp(-((t - 44.9) / .9) ** 2)
    if still > .02: L *= (1 + .3 * still)
    return finish(img, L)
