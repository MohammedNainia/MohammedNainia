"""Make a generated character ready for a drawn (2D) face: flatten its sculpted eyes, brows and lips, paint them over with skin in its
texture, and shift its skin toward a target colour. Writes a new .glb next to it (<name>_clean.glb).

    python glb_face_clean.py ../three/data/glb/haru_rodin.glb

Feature positions come from <name>.rig.json ("face": eyes [x, y, size], brows [x, y], mouth [x, y, width], skinTarget), in model units.
The nose is kept: the drawn face goes around it, like a clay puppet's sculpted nose."""
import sys, json, struct, io, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

path = sys.argv[1]; rig = json.load(open(path.replace('.glb', '.rig.json'))); F = rig['face']
b = open(path, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + L]); bin0 = 20 + L + 8
BL = struct.unpack('<I', b[20 + L:24 + L])[0]; BIN = bytearray(b[bin0:bin0 + BL])

def view(acc_i):
    a = j['accessors'][acc_i]; bv = j['bufferViews'][a['bufferView']]
    comp = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a['componentType']]; n = a['count']; c = {'VEC3': 3, 'VEC2': 2, 'SCALAR': 1}[a['type']]
    o = bv.get('byteOffset', 0) + a.get('byteOffset', 0); st = bv.get('byteStride', c * np.dtype(comp).itemsize) // np.dtype(comp).itemsize
    arr = np.frombuffer(BIN, comp, count=n * st, offset=o).reshape(n, st)[:, :c]
    return arr, o, st

pr = j['meshes'][0]['primitives'][0]
P, po, pst = view(pr['attributes']['POSITION']); P = P.astype(np.float64).copy()
N, no, nst = view(pr['attributes']['NORMAL'])
UV, _, _ = view(pr['attributes']['TEXCOORD_0']); UV = UV.copy()
I = view(pr['indices'])[0].reshape(-1).astype(np.int64).reshape(-1, 3)
x, y, z = P[:, 0], P[:, 1], P[:, 2]

# ---- the regions to clear: ellipses around each painted feature, on the front of the face
ex, ey, es = F['eyes']; bx, by = F['brows']; mx, my, mw = F['mouth']
def ell(cx, cy, rx, ry): return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
front = (z > .08) & (N[:, 2] > .1)
reg = np.minimum.reduce([ell(ex, ey, .046, .036), ell(-ex, ey, .046, .036), ell(bx, by, .062, .03), ell(-bx, by, .062, .03), ell(mx, my, mw * .78, .04)])
w = np.clip((1.35 - reg) / .55, 0, 1) * front          # 1 inside, fading to 0 just outside (the edge blends into the untouched clay)

# ---- the face plate: the model keeps its shape; a smooth shell is laid over the face like a tarp (the highest clay under each point, then
# softened), so it covers the sculpted brows and lips and meets the bare skin at its edges. Saved as a height map in the rig file.
NX = NY = 96; fx0, fx1 = F['x']; fy0, fy1 = F['y']   # (the face rect, widened in the rig to take in the brows)
fr = front & (np.abs(x) < fx1 + .03) & (y > fy0 - .03) & (y < fy1 + .03)
nose = ell(0, F.get('nose', [0, .603])[1], .034, .034) < 1; fr &= ~nose                     # the nose is left out: the real sculpted nose pokes through the plate
gx = np.linspace(fx0, fx1, NX); gy = np.linspace(fy0, fy1, NY); Z = np.full((NY, NX), np.nan); R0 = .013
ix = np.clip(((x[fr] - fx0) / (fx1 - fx0) * (NX - 1)).round().astype(int), 0, NX - 1); iy = np.clip(((y[fr] - fy0) / (fy1 - fy0) * (NY - 1)).round().astype(int), 0, NY - 1)
cell = np.full((NY, NX), -np.inf); np.maximum.at(cell, (iy, ix), z[fr])
from scipy.ndimage import gaussian_filter, distance_transform_edt, maximum_filter
Zs = np.where(np.isfinite(cell), cell, np.nan); bad = np.isnan(Zs); Zs = Zs[tuple(distance_transform_edt(bad, return_distances=False, return_indices=True))]
Zs = gaussian_filter(Zs, 1.0)                                                    # the face itself (lightly softened)
rr = int(np.ceil(R0 / ((fx1 - fx0) / (NX - 1)))); Zt = gaussian_filter(maximum_filter(Zs, size=2 * rr + 1), 2.6)   # a tarp over everything
GX, GY = np.meshgrid(gx, gy); fm = np.minimum.reduce([((GX - cx) / rx) ** 2 + ((GY - cy) / ry) ** 2 for cx, cy, rx, ry in
    [(ex, ey, .046, .036), (-ex, ey, .046, .036), (bx, by, .062, .03), (-bx, by, .062, .03), (mx, my, mw * .78, .04)]])
b = gaussian_filter((fm < 1.5).astype(float), 3.0); b = np.clip(b * 1.6, 0, 1)   # where the old features are (soft-edged)
Z = gaussian_filter(Zt, 1.5) + .001                                              # a smooth tarp over the whole face (its edge is faded out in the drawing)
F['plate'] = {'nx': NX, 'ny': NY, 'z': [round(float(v), 5) for v in Z.reshape(-1)]}
rig['face'] = F; json.dump(rig, open(path.replace('.glb', '_clean.rig.json'), 'w'))
P2 = P; N2 = N
# ---- texture: paint every feature triangle over with the face's own skin, then shift all skin to the target
tex_i = j['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']; img_i = j['textures'][tex_i]['source']; ib = j['bufferViews'][j['images'][img_i]['bufferView']]
img = Image.open(io.BytesIO(bytes(BIN[ib.get('byteOffset', 0):ib.get('byteOffset', 0) + ib['byteLength']]))).convert('RGB'); W, H = img.size
a = np.asarray(img).astype(float)
skin_now = np.array([196, 127, 91.]); tgt = np.array([int(F['skinTarget'][k:k + 2], 16) for k in (1, 3, 5)], float)
mask = Image.new('L', (W, H), 0); dm = ImageDraw.Draw(mask)
tri = I[(w[I] > .25).all(1)]
for t in tri: dm.polygon([(UV[v, 0] % 1 * W, UV[v, 1] % 1 * H) for v in t], fill=255)
mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2)); mk = np.asarray(mask).astype(float)[..., None] / 255
a = a * (1 - mk) + skin_now * mk
r, g, bl = a[..., 0], a[..., 1], a[..., 2]; br = bl / np.maximum(r, 1)
def sm(lo, hi, v): t = np.clip((v - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t)
ws = ((r > g) & (g > bl) & (r > 70)) * sm(.33, .42, br) * (1 - sm(.6, .7, br))   # skin: warm, with more blue than the hoodie
a = a * (1 + (tgt / skin_now - 1) * ws[..., None])
out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); bio = io.BytesIO(); out.save(bio, 'PNG'); newimg = bio.getvalue()

# ---- write: positions and normals in place; the image as a new buffer view at the end (the old one is left unused)
BIN = bytearray(bytes(BIN))   # a fresh copy: the numpy views above still hold the old buffer
while len(BIN) % 4: BIN.append(0)
off = len(BIN); BIN += newimg
while len(BIN) % 4: BIN.append(0)
j['bufferViews'].append({'buffer': 0, 'byteOffset': off, 'byteLength': len(newimg)}); j['images'][img_i] = {'bufferView': len(j['bufferViews']) - 1, 'mimeType': 'image/png'}
j['buffers'][0]['byteLength'] = len(BIN)
js = json.dumps(j).encode();
while len(js) % 4: js += b' '
glb = b'glTF' + struct.pack('<II', 2, 12 + 8 + len(js) + 8 + len(BIN)) + struct.pack('<I', len(js)) + b'JSON' + js + struct.pack('<I', len(BIN)) + b'BIN\0' + bytes(BIN)
outp = path.replace('.glb', '_clean.glb'); open(outp, 'wb').write(glb); print('wrote', outp, len(glb) // 1024, 'KB')
