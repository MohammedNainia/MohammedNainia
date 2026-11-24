"""Overlay the Burton sheet's part map and our ID render for one view, scaled to the same figure height:
[sheet parts | ours | blend]. uv run --no-project --with pillow --with numpy python -I burton_overlay.py SHEET ID.png VIEW OUT.png"""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '.claude', 'skills',
                                'clay-character', 'scripts'))
import burton_measure as BMs
import measure as M


def crop_parts(m, fg, view):
    x0, x1 = M.views(fg)[view]
    pm = np.full(fg.shape + (3,), 24, np.uint8)
    for k in M.PARTS: pm[m[k]] = M.ID[k]
    rows = np.where(fg[:, x0:x1].sum(1) > 3)[0]
    return pm[rows.min():rows.max() + 1, max(0, x0 - 20):x1 + 20]


sheet = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int)
ours = np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(int)
view = int(sys.argv[3])
a = crop_parts(*BMs.classify(sheet), view)
b = crop_parts(*M.classify_ids(ours), 0)
H = 900
A = Image.fromarray(a).resize((round(a.shape[1] * H / a.shape[0]), H), Image.NEAREST)
Bi = Image.fromarray(b).resize((round(b.shape[1] * H / b.shape[0]), H), Image.NEAREST)
W = max(A.width, Bi.width)
pad = lambda im: (lambda c: (c.paste(im, ((W - im.width) // 2, 0)), c)[1])(Image.new('RGB', (W, H), (24, 24, 24)))
A2, B2 = pad(A), pad(Bi)
out = Image.new('RGB', (3 * W + 20, H), (0, 0, 0))
out.paste(A2, (0, 0)); out.paste(B2, (W + 10, 0)); out.paste(Image.blend(A2, B2, 0.5), (2 * W + 20, 0))
out.save(sys.argv[4]); print(sys.argv[4])
