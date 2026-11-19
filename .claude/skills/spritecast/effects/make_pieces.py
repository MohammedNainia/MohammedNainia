"""The small pictures an effect lets go along a swing (drop, flame, spark, leaf, petal, snow, star): drawn here from shapes, so they
are free and the same every time. Run once: `python make_pieces.py` writes <name>.png beside this file, each a strip of 64-px cells
(the cells are variants; a piece is drawn pointing UP). A user's own strip of square cells can be given instead ("image" in "trail")."""
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S, SS = 64, 6          # a cell, and how many times bigger it is drawn before being made smaller (smooth edges)
HERE = Path(__file__).resolve().parent


def cell(): return Image.new('RGBA', (S * SS, S * SS), (0, 0, 0, 0))
def P(pts): return [(x * S * SS, y * S * SS) for x, y in pts]
def done(im): return soft(im, 0).resize((S, S), Image.LANCZOS)


def soft(im, r):
    """blurred by r (0: only made ready to resize) WITHOUT dark edges: the colour is spread with its weight (premultiplied) and divided back.
    Blurred as it was, the clear pixels round a piece (black, at no weight) were mixed into its colour: a white puff of mist came out
    ringed in grey on a light floor."""
    a = np.asarray(im.convert('RGBA')).astype(np.float32) / 255; pm = np.dstack([a[..., :3] * a[..., 3:], a[..., 3:]])
    if r: pm = np.dstack([np.asarray(Image.fromarray((pm[..., k] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255 for k in range(4)])
    al = pm[..., 3:]; rgb = np.where(al > 1e-3, pm[..., :3] / np.maximum(al, 1e-3), 1.0)
    return Image.fromarray((np.dstack([np.clip(rgb, 0, 1), al]) * 255).round().astype(np.uint8))
def strip(name, cells):
    st = Image.new('RGBA', (S * len(cells), S), (0, 0, 0, 0))
    for i, c in enumerate(cells): st.paste(done(c), (i * S, 0))
    st.save(HERE / f'{name}.png', optimize=True); print(name, len(cells))


def drop(w, tail, col, rim):          # round at the top (the end that leads), a point trailing below
    im = cell(); d = ImageDraw.Draw(im); pts = []
    for i in range(41):
        a = 2 * math.pi * i / 40; c = math.cos(a)
        pts.append((0.5 + w * math.sin(a) * (0.5 - 0.5 * c) ** tail, 0.62 + 0.3 * c * (1 if c < 0 else 1.5)))
    pts = [(x, 1.24 - y) for x, y in pts]
    d.polygon(P(pts), fill=rim); d.polygon(P([(0.5 + (x - 0.5) * 0.72, 0.66 + (y - 0.66) * 0.74) for x, y in pts]), fill=col)
    d.ellipse(P([(0.40, 0.66), (0.47, 0.76)]), fill=(255, 255, 255, 235))
    return im.transpose(Image.FLIP_TOP_BOTTOM)


def flame(lean, col_out, col_mid, col_in):          # a tongue: round below, a point at the top leaning a little
    im = cell(); d = ImageDraw.Draw(im)
    for k, c in ((1.0, col_out), (0.68, col_mid), (0.38, col_in)):
        pts = []
        for i in range(61):
            a = 2 * math.pi * i / 60; ca = math.cos(a)
            y = 0.52 - 0.42 * k * ca * (1.35 if ca > 0 else 0.8) + 0.21 + 0.25 * (1 - k)          # (a point at the top once drawn: y runs down)
            pts.append((0.5 + 0.30 * k * (0.5 - 0.5 * ca) ** 0.75 * math.sin(a) + lean * k * (0.5 + 0.5 * ca) ** 2 * 0.5, y))
        d.polygon(P([(x, y - 0.25) for x, y in pts]), fill=c)
    return im


def glow(col, core, r=0.2):
    im = cell(); d = ImageDraw.Draw(im)
    d.ellipse(P([(0.5 - r, 0.5 - r), (0.5 + r, 0.5 + r)]), fill=col); d.ellipse(P([(0.5 - r * 0.5, 0.5 - r * 0.5), (0.5 + r * 0.5, 0.5 + r * 0.5)]), fill=core)
    return soft(im, SS * 1.2)


def leaf(col, vein, bend, kind=0):
    im = cell(); d = ImageDraw.Draw(im); pts = []
    for i in range(61):
        t = i / 60; a = 2 * math.pi * t
        w = 0.21 if kind == 0 else 0.26
        r = w * abs(math.sin(a)) ** (0.8 if kind == 0 else 0.6)
        if kind == 1: r *= 1 + 0.16 * math.cos(7 * a)          # a lobed, maple-like edge
        y = 0.5 - 0.38 * math.cos(a); x = 0.5 + r * (1 if math.sin(a) >= 0 else -1) + bend * math.sin(math.pi * (y - 0.12) / 0.76)
        pts.append((x, y))
    d.polygon(P(pts), fill=col)
    mid = [(0.5 + bend * math.sin(math.pi * (y - 0.12) / 0.76), y) for y in np.linspace(0.14, 0.97, 30)]
    d.line(P(mid), fill=vein, width=SS * 2)
    for y in (0.34, 0.5, 0.66):
        x0 = 0.5 + bend * math.sin(math.pi * (y - 0.12) / 0.76)
        for sx in (-1, 1): d.line(P([(x0, y), (x0 + sx * 0.12, y - 0.09)]), fill=vein, width=SS)
    return im


def petal(col, tip_, base):
    im = cell(); d = ImageDraw.Draw(im); pts = []
    for i in range(61):
        t = i / 60; a = 2 * math.pi * t
        r = 0.24 * abs(math.sin(a)) ** 0.55 * (0.75 + 0.25 * (0.5 - 0.5 * math.cos(a)))
        y = 0.52 - 0.33 * math.cos(a)
        if y < 0.24: y += 0.07 * max(0, 1 - abs(math.sin(a)) * 6)          # the notch at the top
        pts.append((0.5 + r * (1 if math.sin(a) >= 0 else -1), y))
    d.polygon(P(pts), fill=col)
    d.ellipse(P([(0.42, 0.66), (0.58, 0.86)]), fill=base)
    g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse(P([(0.36, 0.2), (0.64, 0.5)]), fill=tip_)
    g = g.filter(ImageFilter.GaussianBlur(SS * 3)); g.putalpha(Image.fromarray((np.asarray(g.getchannel('A')) * (np.asarray(im.getchannel('A')) > 0)).astype('uint8')))
    im.alpha_composite(g)
    return im


def flake(arms=True):
    im = cell(); d = ImageDraw.Draw(im); w = (255, 255, 255, 255)
    if not arms:
        d.ellipse(P([(0.3, 0.3), (0.7, 0.7)]), fill=w); return soft(im, SS * 1.5)
    for k in range(6):
        a = math.pi / 3 * k; c, s_ = math.cos(a), math.sin(a)
        d.line(P([(0.5, 0.5), (0.5 + 0.38 * c, 0.5 + 0.38 * s_)]), fill=w, width=SS * 3)
        for f in (0.5, 0.75):
            bx, by = 0.5 + 0.38 * f * c, 0.5 + 0.38 * f * s_
            for sg in (-1, 1):
                a2 = a + sg * math.pi / 3; d.line(P([(bx, by), (bx + 0.1 * math.cos(a2), by + 0.1 * math.sin(a2))]), fill=w, width=SS * 2)
    return im


def star(col, core, long_=0.44, short=0.2):
    im = cell(); d = ImageDraw.Draw(im); pts = []
    for k in range(8):
        a = math.pi / 4 * k - math.pi / 2; r = (long_ if k % 4 == 0 else short if k % 2 == 0 else 0.06)
        pts.append((0.5 + r * math.cos(a), 0.5 + r * math.sin(a)))
    d.polygon(P(pts), fill=col); d.ellipse(P([(0.44, 0.44), (0.56, 0.56)]), fill=core)
    return im


def puff(seed):          # a soft white cloud of a few round lumps (mist, steam)
    rng = np.random.default_rng(seed); im = cell(); d = ImageDraw.Draw(im)
    for _ in range(6):
        x, y, r = 0.5 + rng.uniform(-0.16, 0.16), 0.5 + rng.uniform(-0.14, 0.14), rng.uniform(0.12, 0.2)
        d.ellipse(P([(x - r, y - r), (x + r, y + r)]), fill=(255, 255, 255, 255))
    return soft(im, SS * 4)


def ash(seed, ember):          # a small ragged flake, dark grey; `ember`: one edge still glowing
    rng = np.random.default_rng(seed); im = cell(); d = ImageDraw.Draw(im); n = 9
    pts = [(0.5 + rng.uniform(0.12, 0.26) * math.cos(2 * math.pi * i / n), 0.5 + rng.uniform(0.08, 0.2) * math.sin(2 * math.pi * i / n)) for i in range(n)]
    d.polygon(P(pts), fill=(96, 92, 90, 255)); d.polygon(P([(0.5 + (x - 0.5) * 0.55, 0.5 + (y - 0.5) * 0.55) for x, y in pts]), fill=(150, 144, 140, 255))
    if ember: d.polygon(P(pts[:4] + [(0.5, 0.5)]), fill=(255, 138, 40, 255))
    return im


if __name__ == '__main__':
    strip('drop', [drop(0.20, 1.1, (73, 166, 238, 235), (214, 243, 255, 255)), drop(0.24, 0.5, (58, 146, 228, 235), (200, 236, 255, 255)), drop(0.16, 1.6, (96, 184, 244, 235), (226, 247, 255, 255))])
    strip('flame', [flame(l, (255, 70, 20, 235), (255, 160, 30, 255), (255, 236, 130, 255)) for l in (-0.25, 0.0, 0.3)])
    strip('spark', [glow((255, 150, 30, 255), (255, 240, 170, 255)), glow((255, 200, 60, 255), (255, 255, 220, 255), 0.15)])
    strip('leaf', [leaf((214, 96, 28, 255), (150, 60, 16, 255), 0.05), leaf((196, 44, 30, 255), (128, 26, 20, 255), -0.06, 1), leaf((228, 168, 38, 255), (166, 112, 20, 255), 0.03, 1), leaf((150, 98, 44, 255), (100, 62, 26, 255), -0.04)])
    strip('greenleaf', [leaf((86, 160, 62, 255), (48, 108, 40, 255), 0.05), leaf((124, 186, 70, 255), (70, 128, 44, 255), -0.05), leaf((58, 132, 66, 255), (34, 92, 46, 255), 0.03)])
    strip('petal', [petal((255, 196, 214, 255), (255, 240, 246, 200), (246, 150, 180, 230)), petal((255, 214, 226, 255), (255, 255, 255, 200), (250, 170, 196, 230)), petal((250, 178, 202, 255), (255, 230, 240, 200), (236, 128, 164, 230))])
    strip('snow', [flake(True), flake(False), flake(True).rotate(30, resample=Image.BICUBIC)])
    strip('star', [star((255, 236, 140, 255), (255, 255, 255, 255)), star((255, 255, 255, 255), (255, 250, 200, 255), 0.36, 0.14), star((180, 226, 255, 255), (255, 255, 255, 255), 0.4, 0.12)])
    strip('mist', [puff(1), puff(2), puff(3)])
    strip('ash', [ash(1, False), ash(2, False), ash(3, True), ash(4, False)])
