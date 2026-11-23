"""Flatten a generated character's face: the image-to-3D models often push the middle of the face forward (a muzzle: the forehead set back,
the cheeks and nose bulging out). This pulls the front of the face back onto a smooth rounded front, keeps a smaller nose, and writes the
model back in place (positions and normals only; texture, UVs and triangles untouched).

    python glb_face_flatten.py ../three/data/lib/chars/haru.glb [--front .216] [--nose .4] [--dry]

--front  how far forward (model units, z) the face front may come at its middle; default: the forehead's own depth
--nose   how much of the nose bump to keep (0..1, default .4)
--dry    only print the profile before and after
Face placement comes from <name>.rig.json ("face": x range, y range chin..brow)."""
import sys, json, struct
import numpy as np
from scipy.ndimage import gaussian_filter, distance_transform_edt

path = sys.argv[1]; arg = lambda k, d: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
rig = json.load(open(path.replace('.glb', '.rig.json'))); F = rig['face']
b = open(path, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + L]); bin0 = 20 + L + 8
BL = struct.unpack('<I', b[20 + L:24 + L])[0]; BIN = bytearray(b[bin0:bin0 + BL])
pr = j['meshes'][0]['primitives'][0]
def acc(i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]; comp = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a['componentType']]
    c = {'VEC3': 3, 'VEC2': 2, 'SCALAR': 1}[a['type']]; o = bv.get('byteOffset', 0) + a.get('byteOffset', 0); st = bv.get('byteStride', c * np.dtype(comp).itemsize) // np.dtype(comp).itemsize
    return np.frombuffer(bytes(BIN), comp, count=a['count'] * st, offset=o).reshape(a['count'], st)[:, :c].copy(), o, st
P, po, pst = acc(pr['attributes']['POSITION']); N, no, nst = acc(pr['attributes']['NORMAL']); I = acc(pr['indices'])[0].reshape(-1, 3).astype(np.int64)
x, y, z = P[:, 0].astype(float), P[:, 1].astype(float), P[:, 2].astype(float)
chin, brow = F['y'][0], F['y'][1]; hw = F['x'][1] * 1.45                       # the face's height range, and a half-width that takes in the cheeks
def profile(Z, label):
    out = []
    for yy in np.arange(brow, chin - .04, -(brow - chin) / 10):
        s = (np.abs(y - yy) < .006) & (np.abs(x) < .012); out.append(f'{yy:.3f}:{Z[s].max():.3f}' if s.any() else '')
    print(label, ' '.join(out))
profile(z, 'before')

# the front surface as a height map over the face (x, y): the furthest-forward clay in each cell
NX, NY = 96, 120; x0, x1, y0, y1 = -hw, hw, chin - .08, brow + .06
fr = (z > 0) & (x > x0) & (x < x1) & (y > y0) & (y < y1)
ix = np.clip(((x[fr] - x0) / (x1 - x0) * (NX - 1)).round().astype(int), 0, NX - 1); iy = np.clip(((y[fr] - y0) / (y1 - y0) * (NY - 1)).round().astype(int), 0, NY - 1)
H = np.full((NY, NX), -np.inf); np.maximum.at(H, (iy, ix), z[fr]); bad = ~np.isfinite(H)
H = H[tuple(distance_transform_edt(bad, return_distances=False, return_indices=True))]; H = gaussian_filter(H, 2.0)   # smooth: the per-cell max is noisy
gx = np.linspace(x0, x1, NX); gy = np.linspace(y0, y1, NY); GX, GY = np.meshgrid(gx, gy)
# the target front: a rounded dome as deep as the forehead (no muzzle), the cheeks curving back like a ball
fz = arg('--front', float(np.median(H[(np.abs(GY - (brow - .02)) < .02) & (np.abs(GX) < .03)])))
dome = fz * np.sqrt(np.clip(1 - (GX / (hw * 1.25)) ** 2, 0, 1)) - .012 * ((GY - (chin + brow) / 2) / ((brow - chin) / 2)) ** 2
nose = H - gaussian_filter(H, 4)                                                  # the nose: the small sharp bump on top of the broad shape
nmask = gaussian_filter(((np.abs(GX) < .05) & (GY > chin + .06) & (GY < (chin + brow) / 2 + .04)).astype(float), 2)
target = np.minimum(H, dome + np.maximum(nose, 0) * nmask * arg('--nose', .4))
D = gaussian_filter(target - H, 4.0)                                               # how far each cell moves (<= 0: back), smooth so the face stays smooth
# fade the move out at the edges of the face (hair, ears, under the chin) and through the head's depth (only the front skin moves)
ey = np.clip((GY - (chin - .06)) / .06, 0, 1) * np.clip(((brow + .05) - GY) / .05, 0, 1); ex = np.clip((hw - np.abs(GX)) / (hw * .3), 0, 1)
D *= ey * ex
from scipy.interpolate import RegularGridInterpolator
f = RegularGridInterpolator((gy, gx), D, bounds_error=False, fill_value=0)
sel = (z > -.02) & (x > x0) & (x < x1) & (y > y0) & (y < y1)
d = f(np.stack([y[sel], x[sel]], 1))
Hs = RegularGridInterpolator((gy, gx), H, bounds_error=False, fill_value=0)(np.stack([y[sel], x[sel]], 1))
depth = np.clip(1 - (Hs - z[sel]) / .09, 0, 1)                                     # skin at the front moves fully, 9 cm in it doesn't move
z2 = z.copy(); z2[sel] += d * depth
profile(z2, 'after ')
if '--dry' in sys.argv: sys.exit()

# relax: a few passes of neighbour-averaging on the vertices that moved (only their depth), so the new front is smooth clay
sel_idx = np.where(sel)[0]; movedv = np.zeros(len(z2), bool); movedv[sel_idx[np.abs(d * depth) > 1e-5]] = True
E = np.concatenate([I[:, [0, 1]], I[:, [1, 2]], I[:, [2, 0]]]); E = E[movedv[E[:, 0]] | movedv[E[:, 1]]]
for it in range(int(arg('--relax', 6))):
    acc = np.zeros(len(z2)); cnt = np.zeros(len(z2))
    np.add.at(acc, E[:, 0], z2[E[:, 1]]); np.add.at(cnt, E[:, 0], 1); np.add.at(acc, E[:, 1], z2[E[:, 0]]); np.add.at(cnt, E[:, 1], 1)
    m = movedv & (cnt > 0); z2[m] = .5 * z2[m] + .5 * acc[m] / cnt[m]
profile(z2, 'relaxed')
# normals again (area-weighted), then write positions and normals back in place
P2 = np.stack([x, y, z2], 1); tri = P2[I]; fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
N2 = np.zeros_like(P2); [np.add.at(N2, I[:, k], fn) for k in range(3)]; N2 /= np.maximum(np.linalg.norm(N2, axis=1, keepdims=True), 1e-12)
moved = movedv
grow = np.zeros(len(P2), bool); grow[I[moved[I].any(1)].reshape(-1)] = True      # only touch normals on and next to what moved
Nout = N.astype(np.float32).copy(); Nout[grow] = N2[grow]
def write(arr, o, st):
    A = np.frombuffer(BIN, np.float32, count=len(arr) * st, offset=o).reshape(len(arr), st); A[:, :3] = arr
write(P2.astype(np.float32), po, pst); write(Nout, no, nst)
a = j['accessors'][pr['attributes']['POSITION']]; a['min'] = P2.min(0).tolist(); a['max'] = P2.max(0).tolist()
js = json.dumps(j, separators=(',', ':')).encode()
while len(js) % 4: js += b' '
glb = b'glTF' + struct.pack('<II', 2, 12 + 8 + len(js) + 8 + len(BIN)) + struct.pack('<I', len(js)) + b'JSON' + js + struct.pack('<I', len(BIN)) + b'BIN\0' + bytes(BIN)
open(path, 'wb').write(glb); print('wrote', path, f'{moved.sum()} vertices moved, max {(-d * depth).max():.3f}')
