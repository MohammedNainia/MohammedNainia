"""Code-only sample 3: Haru as pixel art (side view walk, 8 frames, ~64 px tall), built with the pixel-art skill's pixkit.
    python sample_haru_pixel.py out_dir"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '.claude', 'skills', 'pixel-art', 'scripts'))
from pixkit import Sprite, ramp, save_gif

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
W, H, N = 64, 80, 8

def frame(f):
    p = f / N * 2 * math.pi; sw = math.sin(p)
    s = Sprite(W, H)
    for k, v in {'bg': ['#e6dccb', '#ece4d6', '#f2ebdf'], 'floor': ramp('#c8b89c', 4), 'skin': ['#d8a486', '#e8bc9e', '#f2d0b4', '#f8e0cc'],
                 'hood': ramp('#d8a03a', 6), 'hoodd': ramp('#b8852a', 5), 'pants': ramp('#5a5962', 5), 'pantsd': ramp('#45444c', 5),
                 'shoe': ['#9a968e', '#cfcac2', '#f4f1ea'], 'hair': ['#0e0d12', '#18171d', '#222029', '#302e38'], 'eye': ['#101010', '#101010', '#101010'],
                 'blush': ['#e89a90', '#f0a8a0', '#f4b8b0'], 'shad': ['#b8a88c', '#b8a88c', '#b8a88c']}.items():
        s.material(k, v)
    s.box('bg', 0, 0, W, 70, bevel=0, z0=-50, flat=True)
    s.box('floor', 0, 70, W, 10, bevel=0, z0=-40)
    hx = 31
    hy = 41 + 22 * (1 - math.cos(.5 * sw))           # hips drop at full stride so the feet stay on the floor
    s.ellipsoid('shad', hx + 1, 70.5, 10, 1.4, z0=-30, flat=True)

    def leg(a, knee, mat, z):
        kx, ky = hx + math.sin(a) * 13, hy + math.cos(a) * 13
        b = a - knee
        fx, fy = kx + math.sin(b) * 13, ky + math.cos(b) * 13
        s.capsule(mat, (hx, hy), (kx, ky), 3.2, 2.8, z0=z)
        s.capsule(mat, (kx, ky), (fx, fy), 2.8, 2.4, z0=z)
        s.box('shoe', fx - 3, fy - 1, 8, 4, bevel=.8, z0=z + .5)

    def arm(a, mat, z):
        sx, sy = hx + 1, hy - 18
        ex, ey = sx + math.sin(a) * 8, sy + math.cos(a) * 8
        b = a + .35
        wx, wy = ex + math.sin(b) * 7, ey + math.cos(b) * 7
        s.capsule(mat, (sx, sy), (ex, ey), 2.8, 2.6, z0=z)
        s.capsule(mat, (ex, ey), (wx, wy), 2.6, 2.4, z0=z)
        s.ellipsoid('skin', wx + .5, wy + 1.5, 1.6, 1.6, z0=z + .5)

    kneeB = max(0, math.sin(p + math.pi - .6)) * .9
    kneeF = max(0, math.sin(p - .6)) * .9
    arm(sw * .5, 'hoodd', -6)                           # back limbs first
    leg(-.5 * sw, kneeB, 'pantsd', -5)
    s.poly('hair', [(hx - 3, hy - 29), (hx - 9, hy - 27), (hx - 10 + math.cos(2 * p) * .6, hy - 8), (hx - 4, hy - 9)], bevel=1.5, z0=-4)   # long hair down the back
    s.poly('hood', [(hx - 7, hy - 21), (hx + 6, hy - 21), (hx + 8, hy + 2), (hx - 8, hy + 2)], bevel=3, z0=0)                             # oversized hoodie
    s.ellipsoid('hoodd', hx - 6, hy - 20, 4, 2.4, z0=1)                                                                                    # hood at the neck
    s.box('hoodd', hx + 1, hy - 7, 6, 4, bevel=1, z0=1)                                                                                    # pocket
    leg(.5 * sw, kneeF, 'pants', 2)
    cy = round(hy - 29 + abs(math.cos(p)) * .5)
    s.ellipsoid('skin', hx + 2, cy, 6.5, 6.5, z0=4)                                                                                       # head
    s.poly('hair', [(hx - 6, cy + 3), (hx - 6, cy - 5), (hx, cy - 8), (hx + 7, cy - 6), (hx + 9, cy - 2), (hx + 4, cy - 3), (hx, cy), (hx - 2, cy + 5)], bevel=1.5, z0=14)
    s.pixels('eye', [(hx + 5, cy), (hx + 5, cy + 1)])
    s.pixels('blush', [(hx + 4, cy + 3)])
    arm(-sw * .5, 'hood', 8)
    return s.render(light=(.6, -.75, .4), ambient=.45, rim_amt=.15)

frames = [frame(f) for f in range(N)]
frames[0].save(os.path.join(OUT, 'haru_pixel.png'), scale=5)
save_gif(frames, os.path.join(OUT, '3_pixel_haru.gif'), scale=5, ms=110)
