"""Example: "the Bell-Bearer", an original dark-religious character (theme: gothic, subject: human, ~100 px tall).
A hunched penitent wearing a cracked bronze bell over head and shoulders, one red eye in the crack,
dragging an iron bell-clapper on a chain. Dark chapel, candles, a pointed window.
    python examples/bell_bearer.py out_dir"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import numpy as np
from pixkit import Sprite, ramp, qa, save_gif

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
W, H, N = 144, 160, 8

def frame(f):
    t = f / N * 2 * math.pi
    s = Sprite(W, H)
    for k, v in {'stone': ['#120e14', '#1a151c', '#221c25', '#2b232e', '#352b38'], 'floor': ramp('#3a3236', 4), 'glass': ['#3a5a8a', '#6a8ac0', '#a8c4e8'],
                 'bronze': ramp('#8a6428', 7), 'patina': ramp('#4a7a68', 4), 'sack': ramp('#6a5640', 6),
                 'rope': ramp('#8a6a3a', 4), 'skin': ramp('#8a7a72', 6), 'iron': ramp('#4a4a54', 6),
                 'wax': ramp('#d8ccb0', 4), 'flame': ['#ff9a3a', '#ffd070', '#fff0c0'],
                 'ember': ['#5a0a0a', '#e0301c', '#ff8a5a'] if f % 4 < 2 else ['#5a0a0a', '#c0281c', '#ff6a3a'],
                 'void': ['#0a080c', '#100c12', '#140f16'], 'sackd': ramp('#3e3226', 4), 'joint': ['#141014', '#1a1418', '#201a1e']}.items():
        s.material(k, v)
    # --- the chapel
    s.box('stone', 0, 0, W, 150, bevel=0, z0=-60)
    s.pattern('joint', lambda X, Y: (Y < 150) & ((((Y.astype(int)) % 10 == 0)) | (((X.astype(int) + (Y.astype(int) // 10) * 7) % 16) == 0)), on='stone')   # masonry joints
    s.arch('stone', 104, 96, 22, 60, kind='pointed', thick=4, bevel=2, z0=-55, hole_mat='glass')
    s.pattern('void', lambda X, Y: (np.abs(X - 104) < .6) & (Y > 40) & (Y < 96), on='glass')                                   # window mullion
    s.pattern('void', lambda X, Y: (np.abs(Y - 70) < .6) & (np.abs(X - 104) < 11), on='glass')
    s.box('floor', 0, 150, W, 10, bevel=1, z0=-40)
    for k, (cx, h) in enumerate([(22, 14), (30, 9), (124, 12)]):                                                               # candles
        s.capsule('wax', (cx, 150 - h), (cx, 150), 1.6, 2.0, z0=-20)
        fl = round(math.sin(t * 3 + k * 2) * .6)
        s.ellipsoid('flame', cx, 150 - h - 3 + fl, 1.3, 2.4, z0=-19, flat=True)
    # --- the Bell-Bearer (hunched, ~100 px tall)
    br = round(math.sin(t))                                     # breath: the bell rises and falls 1 px
    cx = 74
    # legs (bent, heavy) and bare feet
    s.capsule('sack', (68, 116), (63, 132), 6, 5, z0=0); s.capsule('skin', (63, 132), (61, 146), 3.4, 3.0, z0=0)
    s.capsule('sack', (82, 116), (88, 132), 6, 5, z0=-1); s.capsule('skin', (88, 132), (90, 146), 3.4, 3.0, z0=-1)
    s.ellipsoid('skin', 59, 148, 5, 2.4, z0=1); s.ellipsoid('skin', 92, 148, 5, 2.4, z0=-1)
    # sackcloth robe over a hunched torso, torn hem, rope wound round the waist
    s.capsule('sack', (cx - 2, 84 + br), (cx + 2, 112), 15, 13, z0=2)
    hem = [(50 + i * 2.4, 128 + (3 if i % 3 == 0 else 0) + (2 if i % 5 == 1 else 0)) for i in range(21)]
    s.poly('sack', [(58, 92 + br), (92, 92 + br), (99, 128)] + hem[::-1] + [(50, 128)], bevel=4, z0=3)
    s.pattern('sackd', lambda X, Y: (Y > 100) & (Y < 128) & ((np.abs(((X - cx) * 14 / (Y - 70)) % 5 - 2.5) < .4)), on='sack')     # long folds
    s.box('rope', 58, 108 + br, 36, 3, bevel=1, z0=5)
    s.capsule('rope', (62, 111 + br), (60, 124), 1, z0=5); s.capsule('rope', (65, 111 + br), (66, 121), 1, z0=5)
    # right arm hanging, wrapped in rope
    s.capsule('sack', (92, 90 + br), (98, 106), 6, 5, z0=1); s.capsule('skin', (98, 106), (97, 120), 3.2, 3, z0=1)
    s.ellipsoid('skin', 97, 123, 3, 3.4, z0=1.5)
    s.pattern('rope', lambda X, Y: (np.abs(X - 97.5) < 3.5) & (Y > 108) & (Y < 118) & ((Y.astype(int) % 3) == 0), on='skin')
    # the bell: worn over head and shoulders, flaring to a heavy lip; patina on the crown; inscription band; a glowing crack
    s.ellipsoid('bronze', cx, 54 + br, 12.5, 9.5, depth=11, z0=24)
    s.poly('bronze', [(cx - 12.5, 54 + br), (cx + 12.5, 54 + br), (cx + 16, 70 + br), (cx + 23, 88 + br), (cx - 23, 88 + br), (cx - 16, 70 + br)], bevel=7, z0=24)
    s.capsule('bronze', (cx - 24, 89 + br), (cx + 24, 89 + br), 3.4, z0=26)
    s.capsule('bronze', (cx - 3, 44 + br), (cx + 3, 44 + br), 2.4, z0=24)                  # the crown loop
    s.pattern('patina', lambda X, Y: (Y < 58 + br) & (np.sin(X * .9) + np.sin(Y * 1.3 + X * .4) > 1.1), on='bronze')
    s.pattern('patina', lambda X, Y: (Y > 82 + br) & (Y < 92 + br) & (np.sin(X * .7) > .55), on='bronze')
    s.pattern('rope', lambda X, Y: (np.abs(Y - (79 + br)) < 1) & ((X.astype(int) % 3) != 0), on='bronze')                    # inscription band
    crack = [(cx + 4, 56), (cx + 6, 61), (cx + 4, 65), (cx + 7, 70), (cx + 5, 75), (cx + 8, 82)]
    for (x0, y0), (x1, y1) in zip(crack, crack[1:]):
        s.capsule('void', (x0, y0 + br), (x1, y1 + br), .8, z0=40, flat=True)
    s.ellipsoid('ember', cx + 5.5, 67 + br, 1.8, 1.3, z0=41, flat=True)                   # the eye in the crack
    # left arm reaching down with the chain; the clapper drags on the floor
    s.capsule('sack', (cx - 19, 90 + br), (cx - 25, 106), 6, 5, z0=30); s.capsule('skin', (cx - 25, 106), (cx - 24, 118), 3.6, 3.2, z0=30)
    s.ellipsoid('skin', cx - 24, 121, 3.8, 3.6, z0=31)
    sw = math.sin(t) * 1.2
    chain = [(cx - 24, 123), (cx - 27 + sw, 130), (cx - 30 + sw, 136)]
    for k, ((x0, y0), (x1, y1)) in enumerate(zip(chain, chain[1:])):
        for j in range(4):
            q = j / 4; s.ellipsoid('iron', x0 + (x1 - x0) * q, y0 + (y1 - y0) * q, 1.4, 1.0, z0=10)
    s.capsule('iron', (cx - 30 + sw, 136), (cx - 33 + sw, 141), 2.2, z0=10)
    s.ellipsoid('iron', cx - 35 + sw, 145, 7, 5.5, depth=6, z0=10)                          # the clapper head
    # --- light: cold window light from upper right, warm candles low on the left, rim from behind
    fl = 1 + .1 * math.sin(t * 3)
    img = s.render(light=(.55, -.7, .45), key=.55, ambient=.1, rim=(-.8, -.3, -.3), rim_amt=.4,
                   point=(26, 132, 30), point_amt=.75 * fl, point_range=80)
    return img

frames = [frame(f) for f in range(N)]
frames[0].save(os.path.join(OUT, 'bell_bearer.png'), scale=5)
save_gif(frames, os.path.join(OUT, 'bell_bearer.gif'), scale=5, ms=130)
print(qa(frames[0].a))
