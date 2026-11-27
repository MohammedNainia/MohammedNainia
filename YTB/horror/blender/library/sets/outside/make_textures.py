"""Images the woods kit maps onto geometry (run with the system Python, which has PIL):
    py make_textures.py  ->  sign_b13.png (the Sector B13 warning sign), chainlink.png (the fence mesh, alpha = wire)"""
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
FB = 'C:/Windows/Fonts/arialbd.ttf'

# the sign: a pale enamel plate, red band, black stencil-like text, rust bleeding from the bolts and edges
W, H = 1600, 1000
im = Image.new('RGB', (W, H), (214, 208, 190)); d = ImageDraw.Draw(im)
d.rectangle((0, 0, W, 250), fill=(150, 28, 22))
f1 = ImageFont.truetype(FB, 150); f2 = ImageFont.truetype(FB, 110); f3 = ImageFont.truetype(FB, 64)
d.text((W / 2, 128), 'SECTOR B13', font=f1, fill=(240, 234, 220), anchor='mm')
d.text((W / 2, 380), 'DO NOT ENTER', font=f2, fill=(20, 18, 16), anchor='mm')
d.line((120, 480, W - 120, 480), fill=(20, 18, 16), width=6)
d.text((W / 2, 600), 'IF IT CALLS YOUR NAME,', font=f3, fill=(20, 18, 16), anchor='mm')
d.text((W / 2, 690), 'DO NOT ANSWER.', font=f3, fill=(150, 28, 22), anchor='mm')
d.text((W / 2, 880), 'CONTAINMENT AREA  ·  AUTHORISED PERSONNEL ONLY', font=ImageFont.truetype(FB, 40), fill=(60, 56, 50), anchor='mm')
r = random.Random(13); rust = Image.new('L', (W, H), 0); rd = ImageDraw.Draw(rust)
for bx, by in ((60, 60), (W - 60, 60), (60, H - 60), (W - 60, H - 60)):
    rd.ellipse((bx - 40, by - 40, bx + 40, by + 40), fill=255)
    for k in range(40):                                     # streaks running down from each bolt
        x = bx + r.uniform(-35, 35); rd.line((x, by, x + r.uniform(-8, 8), by + r.uniform(60, 330)), fill=r.randint(60, 200), width=r.randint(3, 12))
for k in range(900):                                        # pitted edges and spots
    x, y = r.choice(((r.uniform(0, W), r.uniform(0, 50)), (r.uniform(0, W), r.uniform(H - 50, H)), (r.uniform(0, 50), r.uniform(0, H)),
                     (r.uniform(W - 50, W), r.uniform(0, H)), (r.uniform(0, W), r.uniform(0, H))))
    s = r.uniform(2, 16) if y < 60 or y > H - 60 or x < 60 or x > W - 60 else r.uniform(1, 5)
    rd.ellipse((x - s, y - s, x + s, y + s), fill=r.randint(90, 230))
rust = rust.filter(ImageFilter.GaussianBlur(5))
im = Image.composite(Image.new('RGB', (W, H), (92, 46, 22)), im, rust)
d = ImageDraw.Draw(im)
for bx, by in ((60, 60), (W - 60, 60), (60, H - 60), (W - 60, H - 60)): d.ellipse((bx - 16, by - 16, bx + 16, by + 16), fill=(55, 45, 38))
im.save(os.path.join(HERE, 'sign_b13.png'))

# chain link: diamond wire on transparent, tiles seamlessly
N = 512; c = Image.new('RGBA', (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(c); s = N // 4; w = 7
for i in range(-4, 9):
    d.line((i * s, 0, i * s + N, N), fill=(255, 255, 255, 255), width=w)
    d.line((i * s, N, i * s + N, 0), fill=(255, 255, 255, 255), width=w)
c.save(os.path.join(HERE, 'chainlink.png'))
print('ok')
