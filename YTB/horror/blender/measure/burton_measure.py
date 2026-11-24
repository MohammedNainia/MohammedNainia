"""Measure the Burton Haru turnaround (YTB/channel_art/burton_turnaround.png) with the clay-character skill's measure().
Her skin is pale grey-white like the sneakers and close to the background, so the parts are found differently from
classify_sheet(): background by difference from the top rows, hair = very dark, hoodie = olive/mustard, trousers =
mid grey, and light foreground pixels are skin above the trouser hems and shoes below them.
uv run --no-project --with pillow --with numpy python -I burton_measure.py SHEET.png --view N [--debug seg.png]
"""
import sys, os, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '.claude', 'skills',
                                'clay-character', 'scripts'))
import measure as M


def classify(im):
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    lum = .299 * r + .587 * g + .114 * b; sat = im.max(-1) - im.min(-1)
    H = im.shape[0]; yy = np.arange(H)[:, None]
    # background: bluish and brightening toward the floor -> estimate it per row from the left and right edges
    bg = np.median(np.concatenate([im[:, :15], im[:, -15:]], 1), 1)[:, None, :]
    fg = np.abs(im - bg).sum(-1) > 35
    top = fg & (sat > 28) & (r > b + 25) & (lum > 40) & (lum < 200)
    rows = np.where(top.sum(1) > 150)[0]                     # the hoodie is far wider than a hand
    hem = int(rows.max()) if len(rows) else H // 2           # lowest solid hoodie row
    warm_light = fg & (lum > 105) & (r >= b + 4) & (sat < 70) & ~top
    neutral_light = fg & (lum > 150) & (sat < 35) & ~top
    dark = fg & (lum < 120) & (sat < 32) & ~top
    leg_rows = np.where((dark & (yy > hem)).sum(1) > 60)[0]  # rows with trouser legs (5 figures x 2 legs)
    shoe_top = int(leg_rows.max()) + 1 if len(leg_rows) else H
    m = {'top': top}
    m['hair'] = dark & (yy < hem - 10)                        # black hair and its grey highlights, above the hem
    m['pants'] = dark & (yy > hem - 10) & (yy < shoe_top + 6)
    m['shoes'] = (neutral_light | warm_light) & (yy >= shoe_top) & (yy < shoe_top + 70)
    m['skin'] = warm_light & (yy < shoe_top) & ~m['hair']
    fg = m['hair'] | m['top'] | m['pants'] | m['shoes'] | m['skin']
    return m, fg


if __name__ == '__main__':
    im = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int)
    view = int(sys.argv[sys.argv.index('--view') + 1]) if '--view' in sys.argv else 0
    m, fg = classify(im)
    if '--debug' in sys.argv:
        dbg = np.full(im.shape, 30, np.uint8)
        for k in M.PARTS: dbg[m[k]] = M.ID[k]
        Image.fromarray(dbg).save(sys.argv[sys.argv.index('--debug') + 1])
    print(json.dumps(M.measure(m, fg, view), indent=1))
