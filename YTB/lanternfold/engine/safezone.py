"""Where each app's buttons and text cover a 1080x1920 reel. Boxes are (x0, y0, x1, y1), measured on current app layouts (approximate).
  python make.py reels/<reel> safe [video_sec ...]  -> safezones.png: the frame under YouTube Shorts / Instagram Reels / TikTok UI"""
import os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
from .config import FFMPEG, FONT
W, H = 1080, 1920
ZONES = {
    'YouTube Shorts': [(0, 0, 1080, 150, 'top bar'), (940, 880, 1080, 1700, 'like / comment / share'), (0, 1540, 940, 1920, 'title + channel')],
    'Instagram Reels': [(0, 0, 1080, 170, 'top bar'), (950, 1020, 1080, 1720, 'buttons'), (0, 1560, 950, 1920, 'caption + audio')],
    'TikTok': [(0, 0, 1080, 190, 'Following / For You'), (930, 760, 1080, 1620, 'buttons'), (0, 1500, 930, 1920, 'caption + sound')],
}
SAFE = (60, 190, 930, 1500)       # area clear on all three apps

def blocked(box):
    """which app UI elements a box (x0, y0, x1, y1) overlaps"""
    hits = []
    for app, zs in ZONES.items():
        for x0, y0, x1, y1, name in zs:
            if box[0] < x1 and box[2] > x0 and box[1] < y1 and box[3] > y0: hits.append(f'{app}: {name}')
    return hits

def grab(video, sec):
    raw = subprocess.run([FFMPEG, '-v', 'error', '-ss', str(sec), '-i', video, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{W}x{H}', '-'], capture_output=True, check=True).stdout
    return Image.frombytes('RGB', (W, H), raw)

def run(reel, secs=None):
    final = reel.path(f'{reel.slug}_1080x1920.mp4')
    if not os.path.exists(final): raise SystemExit('finalize the reel first (the preview uses the captioned video)')
    secs = [float(s) for s in secs] if secs else [0.1, reel.timing['duration'] * .4]
    f = ImageFont.truetype(FONT, 34); tiles = []
    for sec in secs:
        fr = grab(final, sec)
        for app, zs in ZONES.items():
            im = fr.copy().convert('RGBA'); ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
            for x0, y0, x1, y1, name in zs:
                d.rectangle([x0, y0, x1, y1], fill=(220, 40, 60, 95), outline=(255, 80, 90, 255), width=4)
                d.text((x0 + 14, y0 + 10), name, font=f, fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 255))
            d.rectangle(SAFE, outline=(90, 230, 140, 255), width=3)
            im = Image.alpha_composite(im, ov).convert('RGB'); d = ImageDraw.Draw(im)
            d.text((W / 2, 1880), f'{app}  @ {sec:.1f}s', font=ImageFont.truetype(FONT, 46), anchor='mm', fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
            tiles.append(im.resize((360, 640)))
    sheet = Image.new('RGB', (360 * 3, 640 * len(secs)))
    for i, t in enumerate(tiles): sheet.paste(t, (i % 3 * 360, i // 3 * 640))
    out = reel.path('safezones.png'); sheet.save(out); print('  ' + os.path.basename(out)); return out
