"""Cover / thumbnail (1080x1920) from the reel's own scene: a clean frame + a big hook question.
Text sits in the upper-middle band, clear of the TikTok/Shorts UI (bottom ~25% and right edge)."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .config import FONT
W, H = 1080, 1920

def run(reel):
    th = reel.cfg['thumb']; sc = reel.scene()
    im = Image.fromarray(sc.frame(float(th['t']))).convert('RGB')
    # soft darkening behind the text band for legibility
    band = np.zeros((H, W), np.float32); y0, y1 = th.get('band', (250, 900))
    ys = np.arange(H)[:, None]; band[:] = np.clip(1 - np.abs(ys - (y0 + y1) / 2) / ((y1 - y0) / 2 + 200), 0, 1) ** 1.5
    arr = np.asarray(im, np.float32) * (1 - 0.45 * band[..., None]); im = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(im); lines = th['text']; size = th.get('size', 132)
    f = ImageFont.truetype(FONT, size); fs = ImageFont.truetype(FONT, 44)
    y = th.get('y', 380)
    for ln in lines:
        w = d.textlength(ln, font=f); x = (W - w) / 2
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x, y + 6), ln, font=f, fill=(5, 8, 25, 220), stroke_width=10, stroke_fill=(5, 8, 25, 220))
        im = Image.alpha_composite(im.convert('RGBA'), sh.filter(ImageFilter.GaussianBlur(10))).convert('RGB'); d = ImageDraw.Draw(im)
        d.text((x, y), ln, font=f, fill=(255, 238, 208), stroke_width=3, stroke_fill=(35, 28, 45)); y += int(size * 1.12)
    y += 18; d.line([(W / 2 - 70, y), (W / 2 + 70, y)], fill=(240, 196, 110), width=4); y += 30
    label = th.get('label', reel.cfg.get('series', '')).upper()
    if label:
        sp = ' '.join(label); w = d.textlength(sp, font=fs)
        d.text(((W - w) / 2, y), sp, font=fs, fill=(235, 220, 196), stroke_width=2, stroke_fill=(20, 18, 30))
    out = reel.path('thumbnail_1080x1920.jpg'); im.save(out, quality=93)
    im.resize((360, 640)).save(reel.path('thumbnail_small.jpg'), quality=88)
    print('  ' + os.path.basename(out))
