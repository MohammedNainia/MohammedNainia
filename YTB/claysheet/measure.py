"""Measure a character's parts on a turnaround sheet (or on our flat-colour ID render) so the two can be compared.

    python measure.py sheet REF.png  [--view 0]     a model sheet: parts found by colour
    python measure.py ids   RENDER.png [--view 0]   our ID render: hair/skin/top/pants/shoes painted in flat colours

Prints JSON: every landmark as a fraction of the figure's height (0 = top of the hair, 1 = sole of the shoes),
and every width as a fraction of the same height. Views are found left to right (0 = front)."""
import sys, json
import numpy as np
from PIL import Image

PARTS = ['hair', 'skin', 'top', 'pants', 'shoes']
ID = {'hair': (255, 0, 0), 'skin': (0, 255, 0), 'top': (0, 0, 255), 'pants': (255, 255, 0), 'shoes': (255, 0, 255)}

def classify_sheet(im):
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    lum = .299 * r + .587 * g + .114 * b; sat = im.max(-1) - im.min(-1)
    bg = np.median(im[:40].reshape(-1, 3), 0)                                  # the seamless background
    diff = np.abs(im - bg).sum(-1)
    m = {}
    m['hair'] = (lum < 66) & (sat < 30)
    m['pants'] = (lum >= 60) & (lum < 125) & (sat < 22)
    m['skin'] = (r > 140) & (r - g > 35) & (g - b > 12) & (g - b < 70) & (b > 60)
    m['top'] = (r > 110) & (r - b > 70) & (g > 70) & ~m['skin']
    fg = diff > 28
    m['shoes'] = fg & (lum > 150) & (sat < 30) & ~m['hair']
    return m, fg

def classify_ids(im):
    m = {k: (np.abs(im - np.array(c)).sum(-1) < 60) for k, c in ID.items()}
    fg = np.zeros(im.shape[:2], bool)
    for v in m.values(): fg |= v
    return m, fg

def views(fg):
    cols = fg.sum(0) > 20; spans = []; x = 0
    while x < len(cols):
        if cols[x]:
            s = x
            while x < len(cols) and cols[x]: x += 1
            if x - s > 40: spans.append((s, x))
        x += 1
    return spans

def band(mask, frac=.12, mn=6):
    """first and last rows where the part is solid (ignores specks and rims)"""
    c = mask.sum(1); thr = max(mn, frac * c.max()) if c.max() else 1e9
    ys = np.where(c >= thr)[0]; return (int(ys.min()), int(ys.max())) if len(ys) else (None, None)

def width_at(mask, y, win=3):
    best = 0
    for yy in range(max(0, y - win), min(mask.shape[0], y + win + 1)):
        xs = np.where(mask[yy])[0]
        if len(xs) > 4: best = max(best, int(np.percentile(xs, 98) - np.percentile(xs, 2)))
    return best

def measure(m, fg, view):
    core = m['hair'] | m['top'] | m['pants']
    x0, x1 = views(core)[view]; pad = 30; x0 = max(0, x0 - pad); x1 = min(fg.shape[1], x1 + pad)
    m = {k: v[:, x0:x1].copy() for k, v in m.items()}
    t0, t1 = band(m['top'], .3)                                   # the hoodie body (solid rows)
    # tidy: hair can only be above the hoodie hem; trousers only below the hoodie top; skin rims on the hoodie are not skin
    m['hair'][t1:] = False; m['pants'][:t0 + int(.5 * (t1 - t0))] = False
    m['hair'] |= (m['pants'] & False)
    p0, p1 = band(m['pants'], .25)
    pc, sc = m['pants'].sum(1), m['shoes'].sum(1)
    for y in range(p0 + 50, p1 + 1):                                  # the hem: where the shoes take over from the trousers
        if sc[y] > pc[y]: p1 = y - 1; break
    cols = np.where(m['pants'][p0:p1].any(0))[0]; cx0, cx1 = cols.min() - 15, cols.max() + 15
    sh = m['shoes'].copy(); sh[:p1 - 5] = False; sh[:, :cx0] = False; sh[:, cx1:] = False; m['shoes'] = sh
    s0, s1 = band(sh, .2)
    if s0 is not None and s0 < p1: s0 = p1
    top, h1 = band(m['hair'], .05)
    bot = s1 if s1 is not None else p1
    Hh = bot - top
    f = lambda y: round((y - top) / Hh, 4) if y is not None else None
    w = lambda px: round(px / Hh, 4)
    face = m['skin'].copy(); face[t0:] = False; f0, f1 = band(face, .2)
    hands = m['skin'].copy(); hands[:t0 + int(.6 * (t1 - t0))] = False; hands[p1:] = False; hd0, hd1 = band(hands, .05, 3)
    tops = m['top'].copy(); tt0, _ = band(tops, .08)
    # poke check: garment pixels showing THROUGH the hair (garment with hair on both sides in the same row, above the hair's end)
    poke = 0
    for y in range(top, h1 + 1):
        hx = np.where(m['hair'][y])[0]
        if len(hx) < 2: continue
        row = m['top'][y, hx.min():hx.max() + 1]
        if row.any():
            inside = row.copy(); hrow = m['hair'][y, hx.min():hx.max() + 1]
            left = np.maximum.accumulate(hrow); right = np.maximum.accumulate(hrow[::-1])[::-1]
            poke += int((inside & left & right).sum())
    return {
        'height_px': int(Hh), 'poke_px': poke,
        'hair_bottom': f(h1), 'face_top': f(f0), 'chin': f(f1),
        'top_top': f(tt0), 'top_hem': f(t1), 'hands_bottom': f(hd1),
        'pants_hem': f(p1), 'shoes_top': f(s0),
        'w_hair': w(max(width_at(m['hair'], y) for y in range(top, h1 + 1, 4))),
        'w_face': w(width_at(face, (f0 + f1) // 2)) if f0 is not None else None,
        'w_top_shoulders': w(width_at(m['top'], t0 + int(.15 * (t1 - t0)))),
        'w_top_mid': w(width_at(m['top'], (t0 + t1) // 2)),
        'w_top_hem': w(width_at(m['top'], t1 - 3)),
        'w_pants_mid': w(width_at(m['pants'], (p0 + p1) // 2)),
        'w_shoes': w(width_at(sh, s0 + int(.35 * (s1 - s0)))) if s0 is not None else None,
    }

if __name__ == '__main__':
    kind, path = sys.argv[1], sys.argv[2]
    view = int(sys.argv[sys.argv.index('--view') + 1]) if '--view' in sys.argv else 0
    im = np.array(Image.open(path).convert('RGB')).astype(int)
    m, fg = (classify_sheet if kind == 'sheet' else classify_ids)(im)
    if '--debug' in sys.argv:
        dbg = np.full(im.shape, 30, np.uint8)
        for k in PARTS: dbg[m[k]] = ID[k]
        Image.fromarray(dbg).save(sys.argv[sys.argv.index('--debug') + 1])
    print(json.dumps(measure(m, fg, view), indent=1))
