"""The phone screens for "Don't Open Your Door": a dark messages app, a chat with Mum.
python screens.py -> msg1.png (first text), msg2.png (both texts). The Blender scene maps them onto the phone screen."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 700, 1540                                     # the screen's shape (0.62 x 1.36 cm at 1:10)
BG, BUB, TXT, GREY = (12, 12, 14), (44, 44, 48), (245, 245, 245), (150, 150, 156)
FB, FR = 'arialbd.ttf', 'arial.ttf'


def font(n, b=False): return ImageFont.truetype(FB if b else FR, n)


def bubble(d, y, text, f):
    lines = text.split('\n'); lh = f.size + 14
    tw = max(d.textlength(l, font=f) for l in lines); bw, bh = tw + 70, lh * len(lines) + 46
    d.rounded_rectangle((40, y, 40 + bw, y + bh), radius=46, fill=BUB)
    for i, l in enumerate(lines): d.text((75, y + 23 + i * lh), l, font=f, fill=TXT)
    return y + bh


def screen(texts, path):
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    d.text((60, 40), '2:04', font=font(44, True), fill=TXT)                      # status bar
    d.rounded_rectangle((560, 52, 640, 82), radius=8, outline=TXT, width=3); d.rectangle((566, 58, 590, 76), fill=TXT)
    d.line((0, 330, W, 330), fill=(40, 40, 44), width=3)                         # header: back arrow, avatar, Mum
    d.text((40, 170), '<', font=font(80, True), fill=(80, 150, 255))
    d.ellipse((290, 120, 410, 240), fill=(110, 110, 118)); d.text((350, 180), 'M', font=font(64, True), fill=TXT, anchor='mm')
    d.text((350, 285), 'Mum', font=font(46, True), fill=TXT, anchor='mm')
    d.text((350, 420), 'Today 2:04 AM', font=font(34), fill=GREY, anchor='mm')
    y = 500; f = font(64)
    for t in texts: y = bubble(d, y, t, f) + 34
    d.rounded_rectangle((40, H - 170, W - 40, H - 80), radius=45, outline=(60, 60, 66), width=3)   # reply box
    d.text((90, H - 125), 'Text Message', font=font(38), fill=(90, 90, 96), anchor='lm')
    im.save(path)


screen(["Don't open\nyour door."], os.path.join(HERE, 'msg1.png'))
screen(["Don't open\nyour door.", "I'm still\nat work."], os.path.join(HERE, 'msg2.png'))
print('ok')
