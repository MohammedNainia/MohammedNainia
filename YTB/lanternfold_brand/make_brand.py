"""Lanternfold brand assets from the Artlist images: YouTube banner (2560x1440, text inside the
1546x423 all-device safe area) and profile picture (800x800, also used for TikTok)."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
SERIF = next(f for f in [r'C:\Windows\Fonts\georgia.ttf', '/usr/share/fonts/truetype/freefont/FreeSerif.ttf'] if os.path.exists(f))
SERIF_I = next(f for f in [r'C:\Windows\Fonts\georgiai.ttf', '/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf'] if os.path.exists(f))

def spaced(d, xy, text, font, fill, track, anchor_center=True):
    w = sum(d.textlength(c, font=font) for c in text) + track * (len(text) - 1)
    x, y = xy; x = x - w / 2 if anchor_center else x
    for c in text:
        d.text((x, y), c, font=font, fill=fill); x += d.textlength(c, font=font) + track
    return w

def banner():
    im = Image.open(os.path.join(HERE, 'banner_bg_2.png')).convert('RGB')
    W, H = 2560, 1440; s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
    cx, cy = 1530, 690                                  # right of the child, inside the safe area (507-2053 x 508-931)
    title = ImageFont.truetype(SERIF, 150); tag = ImageFont.truetype(SERIF_I, 50)
    glow = Image.new('L', (W, H), 0); g = ImageDraw.Draw(glow)
    spaced(g, (cx, cy - 120), 'Lanternfold', title, 255, 10)
    glow = glow.filter(ImageFilter.GaussianBlur(22))
    im = Image.composite(Image.new('RGB', (W, H), (255, 190, 100)), im, glow.point(lambda v: int(v * 0.35)))
    shadow = Image.new('L', (W, H), 0); sd = ImageDraw.Draw(shadow)
    spaced(sd, (cx + 4, cy - 114), 'Lanternfold', title, 255, 10)
    im = Image.composite(Image.new('RGB', (W, H), (8, 12, 30)), im, shadow.filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * .7)))
    d = ImageDraw.Draw(im)
    spaced(d, (cx, cy - 120), 'Lanternfold', title, (255, 236, 205), 10)
    d.line([(cx - 60, cy + 60), (cx + 60, cy + 60)], fill=(240, 196, 110), width=3)
    spaced(d, (cx, cy + 82), 'tiny paper stories about the light we leave behind', tag, (225, 214, 196), 1)
    im.save(os.path.join(HERE, 'lanternfold_banner_2560x1440.jpg'), quality=95)
    # preview of what desktop shows
    im.crop((0, (H - 423) // 2, W, (H + 423) // 2)).save(os.path.join(HERE, 'preview_banner_desktop.jpg'), quality=90)

def profile(n=1):
    im = Image.open(os.path.join(HERE, f'profile_option_{n}.png')).convert('RGB').resize((800, 800), Image.LANCZOS)
    im.save(os.path.join(HERE, 'lanternfold_profile_800.png'))

if __name__ == '__main__':
    banner(); profile(1); print('done')
