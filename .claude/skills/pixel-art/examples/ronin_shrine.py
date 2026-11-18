"""Example: an original masked ronin at a night shrine (theme: Japanese, subject: human, ~100 px tall).
Straw kasa hat, red oni half-mask, dark kimono, haori blown by the wind, hakama, hand on the sword hilt.
Vermilion torii, stone lantern, a hanging paper lantern (point light), drifting petals, mist.
    python examples/ronin_shrine.py out_dir"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import numpy as np
from pixkit import Sprite, ramp, qa, save_gif

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
W, H, N = 144, 160, 8

def frame(f):
    t = f / N * 2 * math.pi
    s = Sprite(W, H)
    for k, v in {'sky': ['#0c0f1c', '#121628', '#1a1f36'], 'moon': ['#e8e4d0', '#f4f0e0', '#fffbea'],
                 'verm': ramp('#c23b22', 6), 'blackw': ramp('#24202a', 4), 'stone': ramp('#5a5e66', 5), 'ground': ['#14161e', '#1c1f2a', '#242836', '#2c3142'],
                 'paper': ['#f2b04a', '#ffd27a', '#fff0c0'], 'straw': ramp('#a8884a', 6), 'kimono': ramp('#2e3456', 6),
                 'haori': ramp('#3a2a2e', 6), 'hakama': ramp('#25233a', 6), 'obi': ramp('#8a2a2a', 5), 'oni': ramp('#b82a1e', 6),
                 'tusk': ['#c8c0a8', '#e8e0c8', '#fff8e8'], 'skin': ramp('#b0805e', 5), 'lacq': ramp('#1c1a20', 5),
                 'wrap': ramp('#6a5a8a', 4), 'gold': ramp('#c8a040', 5), 'shade': ['#06060a', '#0a0a10', '#0e0e16'],
                 'petal': ['#e8a0b4', '#f4c0d0', '#ffe0ea'], 'crest': ['#c8c4b8', '#e0dcd0', '#f0ece0']}.items():
        s.material(k, v)
    # --- background: night sky, moon, torii, stone lantern, ground
    s.box('sky', 0, 0, W, 150, bevel=0, z0=-90, flat=True)
    s.ellipsoid('moon', 112, 26, 11, 11, z0=-85, flat=True)
    for x in (34, 110):
        s.capsule('verm', (x, 34), (x, 150), 4.2, 4.8, z0=-50)
    s.poly('blackw', [(14, 30), (130, 30), (136, 24), (128, 34), (16, 34), (8, 24)], bevel=1.5, z0=-48)        # kasagi with up-turned ends
    s.box('verm', 18, 34, 108, 4, bevel=1, z0=-49)
    s.box('verm', 24, 48, 96, 4, bevel=1, z0=-49)                                                            # nuki
    s.box('verm', 68, 38, 8, 10, bevel=1, z0=-49)                                                            # gakuzuka
    s.box('stone', 118, 136, 12, 14, bevel=1.5, z0=-30); s.box('stone', 115, 126, 18, 4, bevel=1.5, z0=-29)
    s.box('stone', 119, 116, 10, 10, bevel=1.5, z0=-30); s.poly('stone', [(113, 116), (135, 116), (124, 108)], bevel=1.5, z0=-29)
    s.box('ground', 0, 150, W, 10, bevel=0, z0=-40)
    # hanging paper lantern on the left (the warm point light)
    lsw = math.sin(t) * .8
    s.capsule('blackw', (24, 38), (24 + lsw, 60), .5, z0=-20)
    s.ellipsoid('paper', 24 + lsw, 68, 5.5, 8, z0=-19, flat=True)
    s.pattern('verm', lambda X, Y: (np.abs(X - 24 - lsw) < 5) & ((np.abs(Y - 62) < .6) | (np.abs(Y - 74) < .6)), on='paper')
    # --- the ronin
    br = round(math.sin(t))
    wind = math.sin(t) * 2.5
    cx = 74
    # hakama (wide pleated trousers) and straw sandals
    s.poly('hakama', [(cx - 10, 100 + br), (cx + 10, 100 + br), (cx + 20, 146), (cx - 19, 146)], bevel=4, z0=0)
    s.pattern('blackw', lambda X, Y: (Y > 104) & (Y < 146) & (np.abs(((X - cx) * 10 / (Y - 80)) % 4 - 2) < .3), on='hakama')     # pleats
    s.box('straw', cx - 15, 146, 9, 3, bevel=.6, z0=1); s.box('straw', cx + 6, 146, 9, 3, bevel=.6, z0=1)
    # haori blown back by the wind (behind the body), with a white crest
    s.poly('haori', [(cx - 13, 72 + br), (cx + 13, 72 + br), (cx + 26 + wind, 108), (cx + 18 + wind * .6, 118), (cx - 16, 110)], bevel=4, z0=-2)
    s.ellipsoid('crest', cx + 16 + wind * .5, 92, 2.2, 2.2, z0=-1, flat=True)
    # kimono torso, obi
    s.capsule('kimono', (cx, 74 + br), (cx, 98 + br), 11, 9.5, z0=2)
    s.poly('kimono', [(cx - 4, 72 + br), (cx + 4, 72 + br), (cx + 1, 92 + br), (cx - 1, 92 + br)], bevel=1, z0=4)                  # the crossed collar
    s.pattern('crest', lambda X, Y: (np.abs(X - cx - (Y - 72) * .12) < .7) & (Y > 72 + br) & (Y < 84 + br), on='kimono')
    s.box('obi', cx - 11, 97 + br, 22, 5, bevel=1, z0=5)
    # the sword at the left hip: lacquered scabbard angled back, wrapped hilt forward, gold tsuba
    s.capsule('lacq', (cx - 6, 100 + br), (cx + 30, 114), 1.6, 1.4, z0=6)
    s.capsule('wrap', (cx - 20, 92 + br), (cx - 7, 99 + br), 1.7, z0=7)
    s.pattern('lacq', lambda X, Y: (((X.astype(int) + Y.astype(int)) % 3) == 0), on='wrap')
    s.ellipsoid('gold', cx - 6, 99.5 + br, 1.6, 2.6, z0=8)
    # arms: right hand on the hilt, left arm hanging, wide sleeves
    s.capsule('kimono', (cx + 9, 76 + br), (cx + 4, 90 + br), 5.5, 6.5, z0=8)
    s.capsule('kimono', (cx + 4, 90 + br), (cx - 12, 94 + br), 5.5, 4, z0=9)
    s.ellipsoid('skin', cx - 15, 93 + br, 2.6, 2.4, z0=10)
    s.capsule('kimono', (cx - 9, 76 + br), (cx - 13, 96 + br), 5.5, 7, z0=3)
    s.ellipsoid('skin', cx - 14, 99 + br, 2.2, 2.6, z0=3.5)
    # head: face in the hat's shadow, red oni half-mask with tusks
    s.capsule('skin', (cx, 66 + br), (cx, 72 + br), 3, z0=5)
    s.ellipsoid('skin', cx, 62 + br, 6, 7, z0=6)
    s.ellipsoid('shade', cx, 58 + br, 6.2, 3.6, z0=7, flat=True)                                                                  # shadow under the brim
    s.ellipsoid('oni', cx, 66 + br, 6.2, 4.6, z0=8)
    s.pixels('shade', [(cx - 3, 65 + br), (cx - 2, 65 + br), (cx + 2, 65 + br), (cx + 3, 65 + br)])                                 # nostrils/teeth shadow
    s.cone('tusk', (cx - 3, 63 + br), (cx - 3, 68 + br), 1.2, z0=9); s.cone('tusk', (cx + 3, 63 + br), (cx + 3, 68 + br), 1.2, z0=9)
    s.pixels('moon', [(cx - 2, 59 + br), (cx + 2, 59 + br)])                                                                       # eyes catching the moon
    # the kasa: a wide, shallow straw cone
    s.poly('straw', [(cx - 27, 57 + br), (cx, 44 + br), (cx + 27, 57 + br), (cx + 25, 59 + br), (cx - 25, 59 + br)], bevel=5, z0=10)
    s.pattern('blackw', lambda X, Y: (Y < 59 + br) & (np.abs(((np.arctan2(Y - 44 - br, X - cx) * 18) % 3) - 1.5) < .25), on='straw')   # woven ribs
    s.capsule('blackw', (cx - 6, 62 + br), (cx - 4, 70 + br), .5, z0=10.5); s.capsule('blackw', (cx + 6, 62 + br), (cx + 4, 70 + br), .5, z0=10.5)
    # drifting petals
    rr = np.random.default_rng(5)
    pts = []
    for i in range(16):
        x0, y0, sp = rr.integers(0, W), rr.integers(0, H), rr.choice([1, 2])
        pts.append((int((x0 + f * 2 + wind) % W), int((y0 + f * sp) % H)))
    s.pixels('petal', pts)
    # --- light: cold moon from upper right, warm paper lantern on the left, rim from the moon side
    fl = 1 + .08 * math.sin(t * 3)
    img = s.render(light=(.6, -.7, .4), key=.5, ambient=.08, rim=(.85, -.3, -.2), rim_amt=.5,
                   point=(24, 68, 40), point_amt=.8 * fl, point_range=85)
    # low mist band over the ground (quantised, so it stays pixel art)
    a = img.a.astype(int); Y, X = np.mgrid[0:H, 0:W]
    m = np.clip(1 - np.abs(Y - 142 - np.sin(X * .08 + t) * 2) / 10, 0, 1); m = np.round(m * 3) / 3 * .35
    for c, v in enumerate((150, 160, 190)): a[..., c] = (a[..., c] * (1 - m) + v * m).astype(int)
    img.a = np.clip(a, 0, 255).astype(np.uint8)
    return img

frames = [frame(f) for f in range(N)]
frames[0].save(os.path.join(OUT, 'ronin_shrine.png'), scale=5)
save_gif(frames, os.path.join(OUT, 'ronin_shrine.gif'), scale=5, ms=130)
print(qa(frames[0].a))
