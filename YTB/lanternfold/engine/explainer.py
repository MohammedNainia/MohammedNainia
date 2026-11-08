"""Explainer overlay kit: labels with leader lines, arrows, counters, timelines, highlight rings, scale bars.
Everything animates in with a progress value p (0..1), so a scene can reveal facts in time with the voice.

    from engine.explainer import Overlay
    ov = Overlay()
    ov.callout((790, 470), (620, 330), 'Earth', p=ss(2, 3, t))
    ov.counter((540, 300), lambda v: f'{v:,.0f} km', 0, 6_000_000_000, p=ss(3, 6, t))
    frame = ov.apply(frame)          # uint8 HxWx3 in, uint8 out
"""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .config import FONT
W, H, SS = 1080, 1920, 2
INK = (255, 244, 224, 255); ACCENT = (240, 196, 110, 255); SHADOW = (8, 10, 24, 200)

def _ease(p): p = max(0.0, min(1.0, p)); return p * p * (3 - 2 * p)

class Overlay:
    def __init__(self, color=INK, accent=ACCENT):
        self.im = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
        self.col, self.acc = color, accent
    def _f(self, size): return ImageFont.truetype(FONT, int(size * SS))
    def _line(self, pts, width, col, p):
        """draw a polyline progressively (p of its total length)"""
        seg = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]; L = sum(math.dist(a, b) for a, b in seg); left = L * _ease(p)
        for a, b in seg:
            d = math.dist(a, b)
            if left <= 0: break
            k = min(1, left / d) if d else 1
            e = (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
            self.d.line([a[0] * SS, a[1] * SS, e[0] * SS, e[1] * SS], fill=col, width=int(width * SS)); left -= d
    def _text(self, xy, text, size, col, anchor='mm', alpha=1.0):
        if alpha <= 0: return
        f = self._f(size); c = col[:3] + (int(col[3] * alpha),); s = SHADOW[:3] + (int(SHADOW[3] * alpha),)
        x, y = xy[0] * SS, xy[1] * SS
        self.d.text((x, y + 3 * SS), text, font=f, fill=s, anchor=anchor, stroke_width=int(4 * SS), stroke_fill=s)
        self.d.text((x, y), text, font=f, fill=c, anchor=anchor, stroke_width=int(1 * SS), stroke_fill=(30, 26, 40, int(255 * alpha)))
    def callout(self, target, label_xy, text, p=1.0, size=46):
        """dot on target, leader line, then label"""
        if p <= 0: return
        tx, ty = target; r = 9 * _ease(min(1, p * 3))
        self.d.ellipse([(tx - r) * SS, (ty - r) * SS, (tx + r) * SS, (ty + r) * SS], outline=self.acc, width=int(3 * SS))
        mid = (label_xy[0], ty + (label_xy[1] - ty) * .0) if False else label_xy
        self._line([target, mid], 3, self.acc, min(1, max(0, p * 1.6 - .2)))
        self._text((label_xy[0], label_xy[1] - 34), text, size, self.col, alpha=min(1, max(0, p * 2 - 1)))
    def arrow(self, a, b, p=1.0, width=6, head=26):
        if p <= 0: return
        self._line([a, b], width, self.acc, p)
        if p >= .95:
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            pts = [b, (b[0] - head * math.cos(ang - .45), b[1] - head * math.sin(ang - .45)), (b[0] - head * math.cos(ang + .45), b[1] - head * math.sin(ang + .45))]
            self.d.polygon([(x * SS, y * SS) for x, y in pts], fill=self.acc)
    def counter(self, xy, fmt, v0, v1, p=1.0, size=72, log=False):
        if p <= 0: return
        k = _ease(p); v = math.exp(math.log(v0 + 1) + (math.log(v1 + 1) - math.log(v0 + 1)) * k) - 1 if log else v0 + (v1 - v0) * k
        self._text(xy, fmt(v), size, self.col, alpha=min(1, p * 4))
    def ring(self, xy, radius, t, p=1.0):
        """pulsing highlight ring"""
        if p <= 0: return
        x, y = xy; r = radius * (1 + .08 * math.sin(t * 4)) * _ease(p); a = int(230 * _ease(p))
        self.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], outline=self.acc[:3] + (a,), width=int(4 * SS))
    def timeline(self, x0, x1, y, labels, p=1.0, size=34):
        """horizontal line with ticks; labels = [(fraction, text)] revealed as the line passes them"""
        if p <= 0: return
        self._line([(x0, y), (x1, y)], 4, self.col, p); k = _ease(p)
        for frac, text in labels:
            if frac <= k + 1e-6:
                x = x0 + (x1 - x0) * frac; a = min(1, (k - frac) * 8 + .2)
                self.d.line([x * SS, (y - 14) * SS, x * SS, (y + 14) * SS], fill=self.acc, width=int(4 * SS))
                self._text((x, y + 44), text, size, self.col, alpha=a)
    def scalebar(self, x, y, length, text, p=1.0):
        if p <= 0: return
        self._line([(x, y), (x + length, y)], 5, self.col, p)
        for xx in (x, x + length * _ease(p)): self.d.line([xx * SS, (y - 12) * SS, xx * SS, (y + 12) * SS], fill=self.col, width=int(4 * SS))
        self._text((x + length / 2, y - 34), text, 38, self.col, alpha=min(1, p * 2))
    def title(self, xy, text, p=1.0, size=64):
        self._text(xy, text, size, self.col, alpha=_ease(p))
    def apply(self, frame):
        ov = self.im.resize((W, H), Image.LANCZOS); base = Image.fromarray(frame).convert('RGBA')
        return np.asarray(Image.alpha_composite(base, ov).convert('RGB'))
