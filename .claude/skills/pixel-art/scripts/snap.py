#!/usr/bin/env python3
# usage: python scripts/snap.py concept.png out.png [colours=40]   (writes out.png scaled 6x and out_1x.png)
# AI concept -> true pixel art: detect the fake pixel size, sample one colour per cell, cut out the background,
# reduce to a fixed palette, clean orphans, add a selective outline, upscale with hard edges.
import sys, numpy as np
from PIL import Image
src, out, ncol = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 32
im = np.asarray(Image.open(src).convert('RGB')).astype(int)
H, W, _ = im.shape
bg = np.median(np.concatenate([im[:20].reshape(-1, 3), im[-20:].reshape(-1, 3)]), 0)
fg = np.abs(im - bg).sum(-1) > 40
ys, xs = np.nonzero(fg); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
# fake pixel size from colour-change spacing along rows/cols
d = (np.abs(np.diff(im[y0:y1, x0:x1], axis=1)).sum(-1) > 30)
runs = []
for row in d[::7]:
    idx = np.nonzero(row)[0]
    if len(idx) > 2: runs += list(np.diff(idx))
runs = np.array([r for r in runs if 2 <= r <= 40])
cell = int(np.bincount(runs).argmax()) if len(runs) else 8
# grid phase: try offsets and keep the one that best lines up with colour changes
best = (0, 0, -1)
colsum = d.sum(0)
for ox in range(cell):
    sc = colsum[ox::cell].sum()
    if sc > best[2]: best = (ox, 0, sc)
ox = best[0]
print('cell size', cell, 'offset', ox)
pad = cell * 2
X0, Y0 = max(0, x0 - pad + ((ox - (x0 - pad)) % cell)), max(0, y0 - pad)
gw, gh = (min(W, x1 + pad) - X0) // cell, (min(H, y1 + pad) - Y0) // cell
cells = im[Y0:Y0 + gh * cell, X0:X0 + gw * cell].reshape(gh, cell, gw, cell, 3)
core = cells[:, cell // 4: cell - cell // 4, :, cell // 4: cell - cell // 4]         # sample the centre of each cell
small = np.median(core.reshape(gh, -1, gw, (cell - 2 * (cell // 4)), 3).transpose(0, 2, 1, 3, 4).reshape(gh, gw, -1, 3), 2).astype(np.uint8)
mask = np.abs(small.astype(int) - bg).sum(-1) > 40
# palette: quantise the character only
P = Image.fromarray(small).quantize(colors=ncol, method=Image.Quantize.FASTOCTREE, kmeans=3, dither=Image.Dither.NONE)
q = np.asarray(P.convert('RGB')).copy()
# orphan cleanup: a lone pixel unlike its 4 matching neighbours takes their colour
for _ in range(2):
    c = (q.astype(np.int32) * [65536, 256, 1]).sum(-1)
    up, dn, lf, rt = np.roll(c, 1, 0), np.roll(c, -1, 0), np.roll(c, 1, 1), np.roll(c, -1, 1)
    orph = (c != up) & (up == dn) & (dn == lf) & (lf == rt) & mask
    q[orph] = np.roll(q, 1, 0)[orph]
# remove tiny specks of mask, then a dark selective outline around the silhouette
m2 = mask.copy()
nb = sum(np.roll(np.roll(mask, a, 0), b, 1).astype(int) for a, b in ((0, 1), (1, 0), (0, -1), (-1, 0)))
m2[mask & (nb == 0)] = False
ring = np.zeros_like(m2)
for a, b in ((0, 1), (1, 0), (0, -1), (-1, 0)): ring |= np.roll(np.roll(m2, a, 0), b, 1)
ring &= ~m2
rgba = np.zeros((gh, gw, 4), np.uint8); rgba[m2, :3] = q[m2]; rgba[m2, 3] = 255
rgba[ring] = (10, 7, 12, 255)
Image.fromarray(rgba).save(out.replace('.png', '_1x.png'))
Image.fromarray(rgba).resize((gw * 6, gh * 6), Image.NEAREST).save(out)
print('sprite', gw, 'x', gh, 'colours', len({tuple(c) for c in rgba[rgba[..., 3] > 0][:, :3]}))
