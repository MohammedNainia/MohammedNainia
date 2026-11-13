"""Comic drawing kit: real comic-book drawing, not a filter.
Inked characters with faces and expressions, cel shading, panel layouts with gutters, speech/thought bubbles,
halftone skies, ink hatching, motion lines. Everything drawn at 2x and downsampled for clean lines.

    from engine.kits.comic import Page
    pg = Page(); p = pg.panel(40, 40, 1000, 700)          # returns a Panel you draw into
    p.sky('#f6b26b', '#7b4a8a'); p.sea(520); p.character(540, 640, 300, expr='thinking')
    p.bubble('Is it still the same ship?', (540, 160), tail=(560, 380), thought=True)
    img = pg.render()                                       # uint8 1080x1920
"""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from ..config import FONT
W, H, S = 1080, 1920, 2
INK = (18, 14, 22)

def hx(h, a=255): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)
def shade(c, k): return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (c[3] if len(c) > 3 else 255,)

def _font(size, bold=True):
    for f in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', r'C:\Windows\Fonts\comicbd.ttf', FONT]:
        try: return ImageFont.truetype(f, int(size * S))
        except Exception: pass
    return ImageFont.load_default()

class Panel:
    def __init__(self, page, x, y, w, h):
        self.page, self.x, self.y, self.w, self.h = page, x, y, w, h
        self.im = Image.new('RGBA', (w * S, h * S), (255, 255, 255, 255)); self.d = ImageDraw.Draw(self.im)
    # --- helpers in panel coordinates ---
    def P(self, x, y): return (x * S, y * S)
    def poly(self, pts, fill, ink=6):
        q = [self.P(*p) for p in pts]; self.d.polygon(q, fill=fill)
        if ink: self.d.line(q + [q[0]], fill=INK, width=int(ink * S), joint='curve')
    def ell(self, cx, cy, rx, ry, fill, ink=6):
        b = [self.P(cx - rx, cy - ry), self.P(cx + rx, cy + ry)]; self.d.ellipse(b, fill=fill, outline=INK if ink else None, width=int(ink * S))
    def stroke(self, pts, w=6, col=INK):
        self.d.line([self.P(*p) for p in pts], fill=col, width=int(w * S), joint='curve')
    # --- backgrounds ---
    def sky(self, top, low, dots=True):
        t, l = hx(top), hx(low)
        for y in range(self.h):
            k = y / self.h; c = tuple(int(t[i] * (1 - k) + l[i] * k) for i in range(3))
            self.d.line([(0, y * S), (self.w * S, y * S)], fill=c, width=S)
        if dots:   # ben-day halftone dots, larger towards the top
            for y in range(0, self.h, 14):
                r = 3.2 * (1 - y / self.h) + .4
                for x in range((y // 14) % 2 * 7, self.w, 14):
                    self.d.ellipse([self.P(x - r, y - r), self.P(x + r, y + r)], fill=shade(t, .8))
    def sun(self, x, y, r, col='#fff1b8'):
        for k in range(12):   # inked sun rays
            a = k * math.pi / 6; self.stroke([(x + math.cos(a) * r * 1.3, y + math.sin(a) * r * 1.3), (x + math.cos(a) * r * 1.9, y + math.sin(a) * r * 1.9)], 5, hx('#f3b24a'))
        self.ell(x, y, r, r, hx(col), 5)
    def sea(self, y0, col='#3b6aa5'):
        self.poly([(0, y0), (self.w, y0), (self.w, self.h), (0, self.h)], hx(col), 0)
        self.stroke([(0, y0), (self.w, y0)], 6)
        r = np.random.default_rng(int(y0))
        for k in range(int(self.w * (self.h - y0) / 9000)):    # ink wave strokes
            x = r.uniform(0, self.w); y = r.uniform(y0 + 15, self.h - 10); L = r.uniform(18, 46)
            self.stroke([(x, y), (x + L * .5, y - 6), (x + L, y)], 3, shade(hx(col), .55))
    def cliff(self, pts, col='#4a3b5c'):
        self.poly(pts, hx(col), 7)
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        for k in range(14):    # hatching for shadow
            x = min(xs) + 10 + k * 14
            if x < max(xs) - 20: self.stroke([(x, max(ys) - 10), (x + 30, min(ys) + 60)], 2, shade(hx(col), .55))
    def boat(self, x, y, s=1.0, hull='#b5703f', sail='#fbf3e0'):
        self.poly([(x - 120 * s, y), (x + 120 * s, y), (x + 85 * s, y + 48 * s), (x - 85 * s, y + 48 * s)], hx(hull))
        for k in range(1, 4): self.stroke([(x - 112 * s + k * 4, y + k * 12 * s), (x + 112 * s - k * 4, y + k * 12 * s)], 3)
        self.stroke([(x, y), (x, y - 200 * s)], 8)
        self.poly([(x + 8, y - 192 * s), (x + 8, y - 16), (x + 120 * s, y - 16)], hx(sail))
        self.stroke([(x + 40 * s, y - 140 * s), (x + 40 * s, y - 40)], 3, (200, 190, 170, 255))
    # --- the character ---
    def character(self, x, y, h, coat='#e0784f', hair='#3a2418', skin='#f2c9a0', age='young', expr='calm', look=1, gesture=None):
        """inked comic character standing at (x, y feet), height h"""
        u = h / 10.0; sk, ha, co = hx(skin), hx(hair), hx(coat)
        # legs + shoes
        for dx in (-u * .55, u * .55):
            self.poly([(x + dx - u * .35, y - u * 3.2), (x + dx + u * .35, y - u * 3.2), (x + dx + u * .3, y - u * .3), (x + dx - u * .3, y - u * .3)], hx('#2d3550'), 5)
            self.poly([(x + dx - u * .45, y - u * .4), (x + dx + u * .6 * look, y - u * .4), (x + dx + u * .55 * look, y), (x + dx - u * .45, y)], hx('#2a1d18'), 5)
        # coat with cel shading and fold lines
        body = [(x - u * 1.5, y - u * 6.4), (x + u * 1.5, y - u * 6.4), (x + u * 2.0, y - u * 3.0), (x - u * 2.0, y - u * 3.0)]
        self.poly(body, co, 7)
        self.poly([(x + u * .4 * look, y - u * 6.3), (x + u * 1.5 * look, y - u * 6.3), (x + u * 2.0 * look, y - u * 3.05), (x + u * .7 * look, y - u * 3.05)], shade(co, .78), 0)
        self.stroke([(x, y - u * 6.3), (x, y - u * 3.1)], 4)
        for k in range(3): self.ell(x - u * .25, y - u * (5.6 - k * .8), u * .12, u * .12, hx('#2a1d18'), 2)
        # arms
        sx, sy = x + u * 1.4 * look, y - u * 6.0
        hand = gesture or (sx + u * .6 * look, y - u * 3.6)
        self.stroke([(sx, sy), hand], u * .9, INK); self.stroke([(sx, sy), hand], u * .65, co)
        self.ell(hand[0], hand[1], u * .38, u * .38, sk, 4)
        ox = x - u * 1.4 * look
        self.stroke([(ox, sy), (ox - u * .4 * look, y - u * 3.5)], u * .9, INK); self.stroke([(ox, sy), (ox - u * .4 * look, y - u * 3.5)], u * .65, shade(co, .85))
        # neck + head
        self.poly([(x - u * .45, y - u * 7.0), (x + u * .45, y - u * 7.0), (x + u * .45, y - u * 6.3), (x - u * .45, y - u * 6.3)], sk, 4)
        hx_, hy = x + u * .15 * look, y - u * 8.3; hr = u * 1.55
        # back hair
        if age == 'old': self.ell(hx_ - u * .9 * look, hy - u * .6, u * .75, u * .75, hx('#d9d4cc'), 5); ha = hx('#e6e1d8')
        else: self.poly([(hx_ - hr * 1.1, hy + hr * .9), (hx_ - hr * 1.15, hy - hr * .4), (hx_ + hr * 1.1, hy - hr * .4), (hx_ + hr * 1.05, hy + hr * .5)], ha, 6)
        self.ell(hx_, hy, hr, hr * 1.08, sk, 6)
        self.poly([(hx_ + hr * .35 * look, hy - hr * .9), (hx_ + hr * .95 * look, hy - hr * .2), (hx_ + hr * .95 * look, hy + hr * .6), (hx_ + hr * .55 * look, hy + hr * .9)], shade(sk, .86), 0)  # face shading
        # fringe / hair top
        if age == 'old':
            self.poly([(hx_ - hr, hy - hr * .2), (hx_ - hr * .6, hy - hr * 1.05), (hx_ + hr * .5, hy - hr * 1.1), (hx_ + hr, hy - hr * .35), (hx_ + hr * .2, hy - hr * .6)], ha, 5)
        else:
            self.poly([(hx_ - hr * 1.05, hy + hr * .1), (hx_ - hr * .8, hy - hr * .95), (hx_ + hr * .2, hy - hr * 1.2), (hx_ + hr * 1.05, hy - hr * .6),
                       (hx_ + hr * .7, hy - hr * .35), (hx_ + hr * .25, hy - hr * .55), (hx_ - hr * .3, hy - hr * .35)], ha, 5)
        # face: eyes, brows, nose, mouth by expression
        ey = hy + hr * .05; ex = [hx_ + hr * (.05 + .2 * look), hx_ + hr * (.55 + .2 * look)]
        for e in ex:
            if expr == 'closed': self.stroke([(e - hr * .14, ey), (e, ey + hr * .07), (e + hr * .14, ey)], 4); continue
            self.ell(e, ey, hr * .15, hr * .2, (255, 255, 255, 255), 3)
            self.ell(e + hr * .05 * look, ey + hr * .03, hr * .08, hr * .11, INK, 0)
            self.ell(e + hr * .07 * look, ey - hr * .02, hr * .025, hr * .025, (255, 255, 255, 255), 0)
        brow = {'calm': (0, 0), 'thinking': (-.12, .1), 'sad': (.12, -.06), 'surprised': (-.18, -.18), 'happy': (.06, .04)}.get(expr, (0, 0))
        for i, e in enumerate(ex):
            tilt = brow[0] * (1 if i == 0 else -1)
            self.stroke([(e - hr * .17, ey - hr * (.33 + brow[1]) + hr * tilt), (e + hr * .17, ey - hr * (.33 + brow[1]) - hr * tilt)], 5)
        nx = hx_ + hr * (.3 + .55 * look * .6); self.stroke([(nx, ey + hr * .1), (nx + hr * .12 * look, ey + hr * .32), (nx, ey + hr * .36)], 3)
        mx, my = hx_ + hr * (.3 + .2 * look), hy + hr * .62
        if expr in ('happy',): self.d.chord([self.P(mx - hr * .25, my - hr * .15), self.P(mx + hr * .25, my + hr * .2)], 0, 180, fill=hx('#7a2b2b'), outline=INK, width=4 * S)
        elif expr == 'surprised': self.ell(mx, my, hr * .1, hr * .14, hx('#7a2b2b'), 4)
        elif expr == 'sad': self.d.arc([self.P(mx - hr * .2, my), self.P(mx + hr * .2, my + hr * .25)], 200, 340, fill=INK, width=4 * S)
        elif expr == 'thinking': self.stroke([(mx - hr * .15, my), (mx + hr * .12, my - hr * .05)], 4)
        else: self.d.arc([self.P(mx - hr * .2, my - hr * .2), self.P(mx + hr * .2, my + hr * .1)], 30, 150, fill=INK, width=4 * S)
        if age == 'old':   # wrinkles + glasses
            for e in ex: self.d.arc([self.P(e - hr * .2, ey - hr * .25), self.P(e + hr * .2, ey + hr * .25)], 0, 360, fill=INK, width=3 * S)
            self.stroke([(ex[0] + hr * .2, ey), (ex[1] - hr * .2, ey)], 3)
            self.stroke([(mx - hr * .35, my - hr * .1), (mx - hr * .3, my + hr * .05)], 2)
    def bubble(self, text, xy, tail, thought=False, size=40, maxw=520):
        f = _font(size); words = text.split(); lines, cur = [], ''
        for wd in words:
            t = (cur + ' ' + wd).strip()
            if self.d.textlength(t, font=f) / S > maxw and cur: lines.append(cur); cur = wd
            else: cur = t
        lines.append(cur)
        tw = max(self.d.textlength(l, font=f) for l in lines) / S; th = len(lines) * size * 1.25
        cx, cy = xy; rx, ry = tw / 2 + 40, th / 2 + 34
        if thought:
            for k, r in enumerate((10, 16, 22)):
                px = tail[0] + (cx - tail[0]) * (k + 1) / 4.5; py = tail[1] + (cy + ry - tail[1]) * (k + 1) / 4.5
                self.ell(px, py, r, r, (255, 255, 255, 255), 4)
            for k in range(10):   # cloud bumps
                a = k / 10 * 2 * math.pi; self.ell(cx + math.cos(a) * rx * .82, cy + math.sin(a) * ry * .8, rx * .32, ry * .38, (255, 255, 255, 255), 5)
            self.ell(cx, cy, rx * .95, ry * .9, (255, 255, 255, 255), 0)
        else:
            self.poly([(cx - rx * .2, cy + ry * .7), tail, (cx + rx * .15, cy + ry * .75)], (255, 255, 255, 255), 5)
            self.ell(cx, cy, rx, ry, (255, 255, 255, 255), 5)
            self.poly([(cx - rx * .18, cy + ry * .6), tail, (cx + rx * .13, cy + ry * .65)], (255, 255, 255, 255), 0)
        for i, l in enumerate(lines):
            self.d.text(self.P(cx, cy - th / 2 + size * .62 + i * size * 1.25), l, font=f, fill=INK, anchor='mm')
    def caption(self, text, size=32):
        f = _font(size); tw = self.d.textlength(text, font=f) / S
        self.poly([(14, 14), (tw + 50, 14), (tw + 50, size + 44), (14, size + 44)], hx('#fbe7a1'), 4)
        self.d.text(self.P(32, 14 + (size + 30) / 2), text, font=f, fill=INK, anchor='lm')
    def motion_lines(self, cx, cy, n=24, r0=200, r1=600):
        for k in range(n):
            a = k / n * 2 * math.pi; self.stroke([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], 2, (30, 30, 40, 160))

class Page:
    def __init__(self, paper='#fbf8f0', gutter=26):
        self.paper, self.g = paper, gutter; self.panels = []
    def panel(self, x, y, w, h):
        p = Panel(self, int(x), int(y), int(w), int(h)); self.panels.append(p); return p
    def render(self, reveal=None):
        """reveal: optional list of per-panel opacities (0..1) to bring panels in one by one"""
        page = Image.new('RGB', (W * S, H * S), hx(self.paper)[:3]); d = ImageDraw.Draw(page)
        for i, p in enumerate(self.panels):
            a = 1.0 if reveal is None else reveal[i]
            if a <= 0: continue
            im = p.im if a >= 1 else Image.blend(Image.new('RGBA', p.im.size, hx(self.paper)), p.im, a)
            page.paste(im.convert('RGB'), (p.x * S, p.y * S))
            d.rectangle([p.x * S, p.y * S, (p.x + p.w) * S, (p.y + p.h) * S], outline=INK, width=8 * S)
        return np.asarray(page.resize((W, H), Image.LANCZOS))
