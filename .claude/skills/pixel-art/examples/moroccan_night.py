"""Example: a Moroccan riad doorway at night, a hooded traveller holding a brass lantern (theme: Moroccan, subject: human).
    python examples/moroccan_night.py out_dir"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import numpy as np
from pixkit import Sprite, ramp, qa, save_gif

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
W, H = 144, 176

def scene(f, n=8):
    t = f / n * 2 * math.pi
    s = Sprite(W, H)
    s.material('plaster', ramp('#c89a68', 6)).material('cedar', ramp('#6a3e20', 6)).material('brass', ramp('#c8962a', 6))
    s.material('zb', ramp('#1f5f8b', 5)).material('zg', ramp('#2f7a4f', 5)).material('zw', ramp('#e8dcc0', 4))
    s.material('indigo', ramp('#2c3566', 7)).material('skin', ramp('#a8704e', 6)).material('stone', ramp('#6a5a52', 5))
    s.material('glow', ['#ffcf6a', '#ffe7a8', '#fff4d0']).material('void', ['#0c0a12', '#120e18', '#18121e'])
    s.material('eye', ['#e8c070', '#fff0b0', '#fff8e0'])
    # the wall and the doorway (behind everything)
    s.box('plaster', 0, 0, W, 150, bevel=0, z0=-40)
    s.pattern('plaster', lambda X, Y: (Y < 150) & (((X.astype(int) * 7 + Y.astype(int) * 13) % 97) == 0))   # faint tadelakt texture
    s.arch('plaster', 72, 150, 54, 92, kind='horseshoe', thick=8, bevel=3, z0=-36, hole_mat='void')
    s.arch('cedar', 72, 150, 46, 86, kind='horseshoe', thick=2, bevel=1, z0=-35)
    # the cedar door, half open, with brass studs
    s.box('cedar', 49, 66, 22, 84, bevel=1.5, z0=-37)
    s.pattern('brass', lambda X, Y: ((X.astype(int) - 52) % 6 == 0) & ((Y.astype(int) - 70) % 8 == 0) & (X > 50) & (X < 70) & (Y > 68) & (Y < 148), flat=False)
    # zellige wainscot: an 8-point star tiling in blue, green and white
    def star(X, Y):
        u, v = (X % 8) - 4, (Y % 8) - 4
        return (np.abs(u) + np.abs(v) < 3.2) | ((np.abs(u) < 1.2) & (np.abs(v) < 3.6)) | ((np.abs(v) < 1.2) & (np.abs(u) < 3.6))
    s.box('zw', 0, 128, 44, 22, bevel=0, z0=-39); s.box('zw', 100, 128, 44, 22, bevel=0, z0=-39)
    s.pattern('zb', on='zw', mask_fn=lambda X, Y: (Y > 128) & (Y < 150) & ((X < 44) | (X > 100)) & star(X, Y) & (((X // 8 + Y // 8) % 2) == 0))
    s.pattern('zg', on='zw', mask_fn=lambda X, Y: (Y > 128) & (Y < 150) & ((X < 44) | (X > 100)) & star(X, Y) & (((X // 8 + Y // 8) % 2) == 1))
    s.box('stone', 0, 150, W, 26, bevel=1, z0=-30)
    # the traveller in a djellaba (about 7 heads tall), built body-first, then clothes on top
    br = round(math.sin(t))
    cx, top = 84, 50 + br                                       # top of the hood
    hh = 13                                                     # head height
    hx, hy = cx, top + 11                                       # head centre
    # body under the robe: shoulders, chest, waist
    s.ellipsoid('indigo', cx, top + 24, 12, 5, depth=6, z0=4)                      # shoulders
    s.capsule('indigo', (cx, top + 26), (cx, top + 46), 10, 8, z0=4)              # chest to waist
    # the robe falls from the shoulders and widens to the hem, with long folds
    s.poly('indigo', [(cx - 11, top + 30), (cx + 11, top + 30), (cx + 16, top + 96), (cx - 15, top + 96)], bevel=4, z0=5)
    s.pattern('indigo', lambda X, Y: (Y > top + 50) & (Y < top + 96) & (np.abs(((X - cx) * 12 / (Y - top + 1)) % 5 - 2.5) < .4), on='indigo')   # fold lines
    s.box('indigo', cx - 12, top + 46, 24, 2, bevel=.5, z0=7)                      # cord belt
    s.pattern('brass', lambda X, Y: (Y >= top + 46) & (Y < top + 48) & (np.abs(X - cx) < 12) & ((X.astype(int) % 4) == 0))
    # left arm reaching out with the lantern: wide djellaba sleeve
    s.capsule('indigo', (cx - 10, top + 25), (cx - 18, top + 38), 4.2, 4.6, z0=8)
    s.capsule('indigo', (cx - 18, top + 38), (cx - 25, top + 42), 4.6, 5.2, z0=9)
    s.ellipsoid('skin', cx - 28, top + 43, 2.3, 2.1, z0=10)
    # right arm hanging, hand peeking from the sleeve
    s.capsule('indigo', (cx + 10, top + 25), (cx + 12, top + 50), 4.2, 5.4, z0=6)
    s.ellipsoid('skin', cx + 12, top + 54, 2.1, 2.4, z0=6.5)
    # head inside the hood; the hood has a crown, a point that falls back, and a deep shadowed opening
    s.ellipsoid('indigo', hx, hy, 7.5, 9, z0=7)
    s.capsule('indigo', (hx + 2, hy - 7), (hx + 7, hy - 14), 4.5, 1.2, z0=6.5)     # the pointed tip, falling back
    s.ellipsoid('void', hx - 1.5, hy + 1, 4.2, 5.4, z0=10, flat=True)
    s.ellipsoid('skin', hx - 2, hy + 3, 3.2, 3.6, z0=10.5)                         # the lower face catches the lantern
    s.pixels('void', [(hx - 4, hy + 1), (hx - 1, hy + 1), (hx - 4, hy + 2), (hx - 1, hy + 2)])       # eyes in shadow
    # the lantern on a short chain
    lx, ly = cx - 28, top + 56 + round(math.sin(t * 2) * .6)
    s.capsule('brass', (cx - 28, top + 44), (lx, ly - 8), .6, z0=11)
    s.cone('brass', (lx, ly - 10), (lx, ly - 6), 4.2, z0=11)
    s.box('glow', lx - 3, ly - 6, 7, 9, bevel=0, z0=11, flat=True)
    s.pattern('brass', lambda X, Y: (X >= lx - 3) & (X < lx + 4) & (Y >= ly - 6) & (Y < ly + 3) & ((X.astype(int) - lx) % 3 == 0))
    s.box('brass', lx - 4, ly + 3, 9, 2, bevel=.5, z0=11)
    fl = 1 + .08 * math.sin(t * 3)
    img = s.render(light=(.4, -.8, .4), key=.18, ambient=.06, rim=(.8, -.3, -.2), rim_amt=.25, point=(lx, ly - 2, 22), point_amt=1.15 * fl, point_range=95)
    return img, s

frames = []
for f in range(8):
    img, s = scene(f); frames.append(img)
frames[0].save(os.path.join(OUT, 'moroccan_night.png'), scale=5)
save_gif(frames, os.path.join(OUT, 'moroccan_night.gif'), scale=5, ms=140)
print(qa(frames[0].a))
