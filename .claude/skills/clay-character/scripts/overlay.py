"""Side by side part maps of the sheet and our ID render, both scaled to the same figure height, plus a blend.
    python overlay.py REF_SHEET.png OUR_ID.png OUT.png [--view 0]"""
import sys
import numpy as np
from PIL import Image
import measure as M

def crop(mask_parts, fg, view, im_shape):
    core = mask_parts['hair'] | mask_parts['top'] | mask_parts['pants']
    x0, x1 = M.views(core)[view]
    m = {k: v[:, x0:x1] for k, v in mask_parts.items()}
    allp = np.zeros(m['hair'].shape, bool)
    for k in ('hair', 'top', 'pants', 'skin'): allp |= m[k]
    t0, t1 = M.band(m['top'], .3)
    sh = m['shoes'].copy(); sh[:t1] = False
    y0, _ = M.band(m['hair'], .05); _, y1 = M.band(sh | m['pants'], .2)
    pad = 60
    img = np.full((y1 - y0, x1 - x0 + 2 * pad, 3), 25, np.uint8)
    for k in M.PARTS:
        mk = m[k][y0:y1] if k != 'shoes' else sh[y0:y1]
        img[:, pad:pad + x1 - x0][mk] = M.ID[k]
    return Image.fromarray(img)

def main():
    ref, ours, out = sys.argv[1:4]
    view = int(sys.argv[sys.argv.index('--view') + 1]) if '--view' in sys.argv else 0
    a = np.array(Image.open(ref).convert('RGB')).astype(int); b = np.array(Image.open(ours).convert('RGB')).astype(int)
    ma, fa = M.classify_sheet(a); mb, fb = M.classify_ids(b)
    A = crop(ma, fa, view, a.shape); Bm = crop(mb, fb, view, b.shape)
    H = 900
    A = A.resize((int(A.width * H / A.height), H)); Bm = Bm.resize((int(Bm.width * H / Bm.height), H))
    W = max(A.width, Bm.width)
    ca = Image.new('RGB', (W, H), (25, 25, 25)); ca.paste(A, ((W - A.width) // 2, 0))
    cb = Image.new('RGB', (W, H), (25, 25, 25)); cb.paste(Bm, ((W - Bm.width) // 2, 0))
    blend = Image.blend(ca, cb, .5)
    c = Image.new('RGB', (A.width + Bm.width + W + 40, H), (0, 0, 0))
    c.paste(A, (0, 0)); c.paste(Bm, (A.width + 20, 0)); c.paste(blend, (A.width + Bm.width + 40, 0)); c.save(out)

if __name__ == '__main__':
    main()
