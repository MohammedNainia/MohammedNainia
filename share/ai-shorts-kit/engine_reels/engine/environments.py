"""Environment presets: pick the place that suits each reel's idea.

    from engine.environments import ENVS, draw_env
    ground = draw_env(img, L, cam, t, ENVS['dusk_sea'], reveal)   # draws sky, light, layers, props, weather
    # then draw characters standing on ground(x) and call finish()

An environment is plain data, so a new place = a new dict (copy the closest one and change colours/kinds).
Layer kinds: hills, dunes, mountains, sea, city, forest, flat, castle (crag + gothic castle at cx), stage (front mound/ledge where characters stand).
"""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import paper as P
from .paper import W, H, hexc, glow, paper_layer, mask_poly, GRAINS, ss

# ---------- shapes ----------
def _peaks(seed, by, amp, n=9, x0=-900, x1=2000):
    r = np.random.default_rng(seed); px = np.sort(r.uniform(x0, x1, n)); ph = r.uniform(.5, 1, n); pw = r.uniform(140, 320, n)
    return lambda x: by - amp * max(0.0, max(ph[i] * (1 - abs(x - px[i]) / pw[i]) for i in range(n)))

def shape(ly, t):
    k, by, a, s = ly['k'], ly['y'], ly.get('a', 60), ly.get('s', 1)
    ph = np.random.default_rng(s).random(3) * 6.28
    if k in ('hills', 'forest'): return lambda x: P.wave(x, by, a, s)
    if k == 'castle':     # rocky crag the castle sits on
        cx = ly.get('cx', 600); return lambda x: by - a * math.exp(-((x - cx) / 420) ** 2) - 18 * math.sin(x / 47 + ph[0]) * math.exp(-((x - cx) / 600) ** 2)
    if k == 'dunes': return lambda x: by - a * (.65 * math.sin(x / 330 + ph[0]) + .35 * math.sin(x / 170 + ph[1]))
    if k == 'mountains': return _peaks(s, by, a)
    if k == 'sea': return lambda x: by + 5 * math.sin(x / 38 + t * 1.6 + ph[0]) + 3 * math.sin(x / 17 - t * 2.1)
    if k in ('flat', 'city'): return lambda x: by + 3 * math.sin(x / 90 + ph[0])
    if k == 'stage':
        cx, w = ly.get('cx', 540), ly.get('w', 380); form = ly.get('form', 'mound')
        if form == 'ledge':   # cliff / rooftop edge: flat top, drops away on the right
            return lambda x: by + (0 if x < cx + w * .55 else min(900, (x - cx - w * .55) * 3)) + 2 * math.sin(x / 31)
        return lambda x: by + 330 * (1 - math.exp(-((x - cx) / w) ** 2)) - 240 + 6 * math.sin(x / 37)
    raise ValueError(k)

def props(ly, fn, T):
    """extra paper polygons cut from the same sheet as the layer (same colour)"""
    k, s = ly['k'], ly.get('s', 1); out = []; r = np.random.default_rng(s + 50)
    if k == 'forest':
        xs = np.arange(-700, 1800, ly.get('gap', 55)); xs = xs + r.uniform(-15, 15, len(xs))
        for x in xs:
            h = r.uniform(.7, 1.3) * ly.get('th', 90); y = fn(x) + 8
            if r.random() < ly.get('round', 0):   # round deciduous tree
                c = [T(x + h * .32 * math.cos(q), y - h * .9 + h * .32 * math.sin(q)) for q in np.linspace(0, 6.283, 14)]
                out += [c, [T(x - 3, y), T(x + 3, y), T(x + 3, y - h * .6), T(x - 3, y - h * .6)]]
            else:
                out.append([T(x - 2, y), T(x - h * .3, y - h * .25), T(x - h * .12, y - h * .3), T(x - h * .24, y - h * .6),
                            T(x, y - h), T(x + h * .24, y - h * .6), T(x + h * .12, y - h * .3), T(x + h * .3, y - h * .25), T(x + 2, y)])
    if k == 'castle':
        for tw in _castle(ly):
            x0, w, h, roof = tw; y = fn(x0 + w / 2) + 30
            out.append([T(x0, y), T(x0 + w, y), T(x0 + w, y - h), T(x0, y - h)])
            if roof: out.append([T(x0 - w * .12, y - h), T(x0 + w / 2, y - h - w * 1.5), T(x0 + w * 1.12, y - h)])
            else:
                for bx in np.arange(x0, x0 + w - 5, 16): out.append([T(bx, y - h), T(bx + 9, y - h), T(bx + 9, y - h - 12), T(bx, y - h - 12)])
    if k == 'city':
        for x, w, h, spire in _buildings(ly):
            y = fn(x) + 4; out.append([T(x, y), T(x + w, y), T(x + w, y - h), T(x, y - h)])
            if spire: out.append([T(x + w * .4, y - h), T(x + w * .5, y - h - 40), T(x + w * .6, y - h)])
    if ly.get('trees'):        # sparse trees on hills (reel 1 look)
        for x in ly['trees']:
            h = 34; y = fn(x) + 6
            out.append([T(x - 2, y), T(x - 2, y - h * .5), T(x - h * .32, y - h * .45), T(x, y - h * 1.6), T(x + h * .32, y - h * .45), T(x + 2, y - h * .5), T(x + 2, y)])
    return out

def _buildings(ly):
    r = np.random.default_rng(ly.get('s', 1) + 50); out = []; x = -700
    while x < 1800:
        w = r.uniform(60, 140); h = r.uniform(80, ly.get('a', 260)); out.append((x, w, h, r.random() < .3)); x += w + r.uniform(4, 20)
    return out

def _castle(ly):
    """(x0, width, height, pointed_roof) for a gothic castle silhouette centred on cx"""
    cx, sc = ly.get('cx', 600), ly.get('scale', 1.0)
    parts = [(-230, 300, 120, False), (-210, 46, 230, True), (-120, 60, 330, True), (-30, 80, 420, True), (70, 56, 300, True), (150, 44, 210, True), (-170, 340, 170, False)]
    return [(cx + dx * sc, w * sc, h * sc, r) for dx, w, h, r in parts]

def castle_windows(L, ly, fn, T, z, t, b=1.0):
    """small warm arched windows that glow (some flicker)"""
    r = np.random.default_rng(ly.get('s', 1) + 91)
    for x0, w, h, roof in _castle(ly):
        y = fn(x0 + w / 2) + 30
        for wy in np.arange(y - h + 30, y - 25, 38):
            for wx in np.arange(x0 + 12, x0 + w - 10, 26):
                if r.random() < .22:
                    fl = .75 + .25 * math.sin(t * (2 + r.random() * 3) + wx)
                    sx, sy = T(wx, wy); glow(L, sx, sy, 3.2 * z, hexc('#ffc46b'), .9 * fl * b); glow(L, sx, sy, 14 * z, hexc('#ff9a4a'), .12 * fl * b)

def city_windows(img, ly, fn, T, z, t):
    r = np.random.default_rng(ly.get('s', 1) + 77); m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    for x, w, h, _ in _buildings(ly):
        y = fn(x) + 4
        for wy in np.arange(y - h + 14, y - 12, 22):
            for wx in np.arange(x + 10, x + w - 14, 20):
                if r.random() < .28 and math.sin(t * .3 + wx + wy) > -.8:
                    a, b = T(wx, wy); c_, e = T(wx + 8, wy + 11); d.rectangle([a, b, c_, e], fill=255)
    a = np.asarray(m, np.float32)[..., None] / 255
    img[:] = img * (1 - a) + a * hexc('#f2c46b') * P._REV

# ---------- weather / light ----------
def weather(L, kind, t, amt=1.0):
    if not kind or amt <= 0: return
    r = np.random.default_rng(9)
    if kind == 'rain':
        R = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(R)
        for _ in range(260):
            x0, sp = r.uniform(-50, 1130), r.uniform(1500, 2100); y0 = (r.uniform(0, H) + t * sp) % (H + 200) - 100
            dr.line([x0, y0, x0 - 10, y0 + 46], fill=int(150 * amt), width=2)
        L += np.asarray(R.filter(ImageFilter.GaussianBlur(.8)), np.float32)[..., None] / 255 * np.array([.55, .65, .8], np.float32) * .5
    else:
        n, col, sz, sp = {'snow': (160, (1, 1, 1), 3.0, 60), 'fireflies': (35, (1, .85, .45), 3.5, 0),
                          'leaves': (40, (1, .6, .3), 3.0, 90), 'dust': (60, (1, .9, .7), 2.0, 8)}[kind]
        for q in range(n):
            x0, y0, f = r.uniform(0, W), r.uniform(0, H), r.uniform(.6, 1.4)
            x = (x0 + 40 * math.sin(t * .7 * f + q)) % W; y = (y0 + t * sp * f) % H if sp else y0 + 30 * math.sin(t * .5 * f + q)
            tw = .6 + .4 * math.sin(t * 3 * f + q) if kind == 'fireflies' else 1
            glow(L, x, y, sz * f, np.array(col, np.float32), .7 * amt * tw)

def draw_env(img, L, cam, t, env, reveal=1.0):
    """draws everything behind the characters; returns ground(x) of the stage layer"""
    top, low = env['sky']; img[:] = P.sky(top, low) * reveal
    if env.get('stars'): img[:] = P.stars_layer(img, cam, t, reveal * env['stars'])
    for kind in ('sun', 'moon'):
        if env.get(kind):
            x, y, rad, col = env[kind]; T, z = cam.f(.4); sx, sy = T(x, y); c = hexc(col)
            if kind == 'moon':
                m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).ellipse([sx - rad * z, sy - rad * z, sx + rad * z, sy + rad * z], fill=255)
                a = np.asarray(m, np.float32)[..., None] / 255; img[:] = img * (1 - a) + a * c * GRAINS[4] * reveal
                glow(L, sx, sy, rad * 2.2 * z, c, .18 * reveal)
            else:
                glow(L, sx, sy, rad * z, np.array([1, .97, .85], np.float32), .9 * reveal); glow(L, sx, sy, rad * 3 * z, c, .3 * reveal)
    ground = None
    for i, ly in enumerate(env['layers']):
        T, z = cam.f(ly.get('p', 1.0)); fn = shape(ly, t)
        pts = [T(x, fn(x)) for x in np.linspace(-900, 2000, 150)] + [(W + 50, H + 50), (-50, H + 50)]
        paper_layer(img, mask_poly(pts, props(ly, fn, T)), hexc(ly['c']) * reveal, GRAINS[i % 6])
        if ly['k'] == 'city': city_windows(img, ly, fn, T, z, t)
        if ly['k'] == 'castle': castle_windows(L, ly, fn, T, z, t, reveal)
        if ly['k'] == 'sea':   # glints on the water
            for q in range(12):
                gx = 80 + q * 85 + 20 * math.sin(t + q); sx, sy = T(gx, fn(gx) + 6); glow(L, sx, sy, 3, hexc(env.get('glint', '#ffe6b0')), .5 * (0.5 + 0.5 * math.sin(t * 2 + q)) * reveal)
        if ly['k'] == 'stage': ground = fn
    weather(L, env.get('weather'), t, env.get('weather_amt', 1.0) * reveal)
    return ground

# ---------- presets ----------
ENVS = {
 'night_hills': {'sky': ('#070d22', '#1d2c57'), 'stars': 1, 'layers': [
    {'c': '#1a2246', 'k': 'hills', 'y': 1150, 'a': 80, 's': 1, 'p': .5, 'trees': [-150, 90, 980, 1250]},
    {'c': '#26305a', 'k': 'hills', 'y': 1270, 'a': 90, 's': 2, 'p': .65, 'trees': [520, 1150]},
    {'c': '#2f4466', 'k': 'hills', 'y': 1390, 'a': 70, 's': 3, 'p': .8},
    {'c': '#36416a', 'k': 'stage', 'y': 1520, 'p': 1}]},
 'dusk_sea': {'sky': ('#3b2f5c', '#f2a27a'), 'sun': (560, 1180, 70, '#ffb070'), 'glint': '#ffd9a0', 'layers': [
    {'c': '#7d5a7a', 'k': 'mountains', 'y': 1200, 'a': 160, 's': 4, 'p': .35},
    {'c': '#4f4f7d', 'k': 'sea', 'y': 1230, 's': 5, 'p': .55},
    {'c': '#3d4370', 'k': 'sea', 'y': 1330, 's': 6, 'p': .75},
    {'c': '#2a2a45', 'k': 'stage', 'form': 'ledge', 'y': 1420, 'cx': 420, 'w': 420, 'p': 1}], 'weather': 'dust', 'weather_amt': .5},
 'desert_moon': {'sky': ('#0b1236', '#3a3f74'), 'stars': 1, 'moon': (760, 520, 70, '#f3ead2'), 'layers': [
    {'c': '#5a4a6e', 'k': 'dunes', 'y': 1200, 'a': 70, 's': 7, 'p': .5},
    {'c': '#7a5f6e', 'k': 'dunes', 'y': 1320, 'a': 80, 's': 8, 'p': .7},
    {'c': '#9a7666', 'k': 'stage', 'y': 1500, 'w': 460, 'p': 1}]},
 'snow_peaks': {'sky': ('#6f86b8', '#f2c7c4'), 'sun': (300, 1050, 50, '#ffd0b0'), 'layers': [
    {'c': '#b9c4e0', 'k': 'mountains', 'y': 1180, 'a': 420, 's': 9, 'p': .4},
    {'c': '#8f9fca', 'k': 'mountains', 'y': 1300, 'a': 260, 's': 10, 'p': .6},
    {'c': '#5f7099', 'k': 'forest', 'y': 1420, 'a': 40, 's': 11, 'p': .8, 'th': 80, 'gap': 38},
    {'c': '#e9eef7', 'k': 'stage', 'y': 1520, 'p': 1}], 'weather': 'snow'},
 'city_roofs': {'sky': ('#0d1230', '#3b3466'), 'stars': .5, 'moon': (820, 430, 45, '#f6efd9'), 'layers': [
    {'c': '#1f2346', 'k': 'city', 'y': 1250, 'a': 380, 's': 12, 'p': .45},
    {'c': '#2a2d55', 'k': 'city', 'y': 1360, 'a': 260, 's': 13, 'p': .7},
    {'c': '#1a1b33', 'k': 'stage', 'form': 'ledge', 'y': 1430, 'cx': 420, 'w': 520, 'p': 1}]},
 'autumn_forest': {'sky': ('#f0b46c', '#fde3b5'), 'sun': (700, 1000, 80, '#ffbf6a'), 'layers': [
    {'c': '#d9925e', 'k': 'forest', 'y': 1200, 'a': 50, 's': 14, 'p': .45, 'th': 120, 'gap': 46, 'round': .6},
    {'c': '#b86a45', 'k': 'forest', 'y': 1330, 'a': 50, 's': 15, 'p': .7, 'th': 150, 'gap': 70, 'round': .7},
    {'c': '#8a4b36', 'k': 'stage', 'y': 1520, 'p': 1}], 'weather': 'leaves'},
 'space_planet': {'sky': ('#04030f', '#1b1240'), 'stars': 1.4, 'moon': (720, 620, 230, '#b98ad6'), 'layers': [
    {'c': '#2b2350', 'k': 'mountains', 'y': 1350, 'a': 140, 's': 16, 'p': .6},
    {'c': '#3a2f63', 'k': 'stage', 'y': 1520, 'w': 520, 'p': 1}], 'weather': 'dust', 'weather_amt': .4},
 'gothic_castle': {'sky': ('#07041a', '#3b1636'), 'stars': .8, 'moon': (700, 470, 95, '#f1e3cf'), 'layers': [
    {'c': '#1d1233', 'k': 'mountains', 'y': 1260, 'a': 230, 's': 19, 'p': .35},
    {'c': '#130b24', 'k': 'castle', 'y': 1290, 'a': 120, 's': 20, 'p': .5, 'cx': 640},
    {'c': '#1b1029', 'k': 'forest', 'y': 1420, 'a': 30, 's': 21, 'p': .75, 'th': 95, 'gap': 36},
    {'c': '#2b1d33', 'k': 'stage', 'form': 'ledge', 'y': 1470, 'cx': 380, 'w': 640, 'p': 1}], 'weather': 'dust', 'weather_amt': .25},
 'firefly_meadow': {'sky': ('#0d1b2a', '#28465a'), 'stars': .8, 'layers': [
    {'c': '#16303d', 'k': 'forest', 'y': 1180, 'a': 40, 's': 17, 'p': .5, 'th': 140, 'gap': 34},
    {'c': '#1d3f45', 'k': 'hills', 'y': 1330, 'a': 60, 's': 18, 'p': .75},
    {'c': '#2a5550', 'k': 'stage', 'y': 1520, 'p': 1}], 'weather': 'fireflies'},
}
