"""Slim a generated .glb for the library: textures re-encoded as JPEG (base colour and normal map, at most MAX px), the metal/roughness
map dropped (our clay material ignores it), every unused buffer view removed. Geometry is left as it is.

    python glb_slim.py IN.glb OUT.glb [--max 2048]
"""
import sys, json, struct, io
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]; MAX = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 2048
b = open(src, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + L]); bin0 = 20 + L + 8
BL = struct.unpack('<I', b[20 + L:24 + L])[0]; BIN = b[bin0:bin0 + BL]
def bv_bytes(i): v = j['bufferViews'][i]; o = v.get('byteOffset', 0); return BIN[o:o + v['byteLength']]

# drop metal/roughness and occlusion references
for m in j.get('materials', []):
    pbr = m.get('pbrMetallicRoughness', {}); pbr.pop('metallicRoughnessTexture', None); pbr['metallicFactor'] = 0; pbr['roughnessFactor'] = .9
    m.pop('occlusionTexture', None)
used_tex = set()
for m in j.get('materials', []):
    t = m.get('pbrMetallicRoughness', {}).get('baseColorTexture');  t and used_tex.add(t['index'])
    t = m.get('normalTexture');  t and used_tex.add(t['index'])
used_img = {j['textures'][t]['source'] for t in used_tex}
# re-encode used images
new_img = {}
for i in used_img:
    im = Image.open(io.BytesIO(bv_bytes(j['images'][i]['bufferView']))).convert('RGB')
    if max(im.size) > MAX: im = im.resize((MAX, MAX * im.size[1] // im.size[0]), Image.LANCZOS)
    o = io.BytesIO(); im.save(o, 'JPEG', quality=88, optimize=True); new_img[i] = o.getvalue()
# rebuild the binary: keep accessor views, add the new images, drop everything else
keep = sorted({a['bufferView'] for a in j['accessors'] if 'bufferView' in a})
out = bytearray(); remap = {}
def put(data):
    while len(out) % 4: out.append(0)
    off = len(out); out.extend(data); return off
views = []
for old in keep:
    v = dict(j['bufferViews'][old]); data = bv_bytes(old); v['byteOffset'] = put(data); v['buffer'] = 0; remap[old] = len(views); views.append(v)
for a in j['accessors']:
    if 'bufferView' in a: a['bufferView'] = remap[a['bufferView']]
for i, data in new_img.items():
    views.append({'buffer': 0, 'byteOffset': put(data), 'byteLength': len(data)}); j['images'][i] = {'bufferView': len(views) - 1, 'mimeType': 'image/jpeg'}
# images and textures no longer used: point them at the first kept image (harmless), so indices stay valid
for i, im in enumerate(j['images']):
    if i not in new_img and new_img: j['images'][i] = j['images'][next(iter(new_img))]
j['bufferViews'] = views
while len(out) % 4: out.append(0)
j['buffers'] = [{'byteLength': len(out)}]
js = json.dumps(j, separators=(',', ':')).encode()
while len(js) % 4: js += b' '
glb = b'glTF' + struct.pack('<II', 2, 12 + 8 + len(js) + 8 + len(out)) + struct.pack('<I', len(js)) + b'JSON' + js + struct.pack('<I', len(out)) + b'BIN\0' + bytes(out)
open(dst, 'wb').write(glb); print(f'{src}: {len(b) // 1024} KB -> {dst}: {len(glb) // 1024} KB')
