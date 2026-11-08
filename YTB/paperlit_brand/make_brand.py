"""PaperLit brand: YouTube banner (2560x1440, text in the 1546x423 all-device safe area) + profile picture (800x800)."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
SERIF = next(f for f in [r'C:\Windows\Fonts\georgia.ttf', '/usr/share/fonts/truetype/freefont/FreeSerif.ttf'] if os.path.exists(f))
SERIF_I = next(f for f in [r'C:\Windows\Fonts\georgiai.ttf', '/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf'] if os.path.exists(f))
GOLD, CREAM, CORAL = (240, 196, 110), (255, 238, 210), (238, 132, 112)

def spaced(d, xy, text, font, fill, track):
    w = sum(d.textlength(c, font=font) for c in text) + track * (len(text) - 1); x, y = xy[0] - w / 2, xy[1]
    for c in text: d.text((x, y), c, font=font, fill=fill); x += d.textlength(c, font=font) + track

def banner(src='banner1.png', cx=1660, cy=700):
    im = Image.open(os.path.join(HERE, src)).convert('RGB'); W, H = 2560, 1440
    s = max(W / im.width, H / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
    title = ImageFont.truetype(SERIF, 170); tag = ImageFont.truetype(SERIF_I, 52)
    for col, off, blur, a in [((255, 190, 100), (0, 0), 26, .35), ((8, 12, 30), (5, 7), 6, .75)]:
        m = Image.new('L', (W, H), 0); spaced(ImageDraw.Draw(m), (cx + off[0], cy - 130 + off[1]), 'PaperLit', title, 255, 12)
        im = Image.composite(Image.new('RGB', (W, H), col), im, m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * a)))
    d = ImageDraw.Draw(im)
    spaced(d, (cx, cy - 130), 'PaperLit', title, CREAM, 12)
    d.line([(cx - 70, cy + 68), (cx + 70, cy + 68)], fill=GOLD, width=4)
    spaced(d, (cx, cy + 92), 'tiny paper stories, big quiet questions', tag, (230, 218, 200), 1)
    im.save(os.path.join(HERE, 'paperlit_banner_2560x1440.jpg'), quality=95)
    im.crop((0, (H - 423) // 2, W, (H + 423) // 2)).save(os.path.join(HERE, 'preview_banner_desktop.jpg'), quality=90)

def profile(n=2):
    Image.open(os.path.join(HERE, f'pfp{n}.png')).convert('RGB').resize((800, 800), Image.LANCZOS).save(os.path.join(HERE, 'paperlit_profile_800.png'))

if __name__ == '__main__':
    banner(); profile(2); print('done')
