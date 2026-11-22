"""Measure a generated character (standing, arms down, facing +z) and write its rig file: the joint positions glb_person.js builds the
skeleton from, and where the drawn 2D face goes. Everything is in the model's own units.

    python glb_autorig.py ../three/data/lib/chars/mum.glb            -> mum.rig.json next to it
    python glb_autorig.py X.glb --rot 90                               a model that came out facing sideways (degrees about y; written into the rig)

How: the floor and head top are the lowest and highest points; the crotch is the top of the gap between the legs; the hands are the
outer clusters that hang below the crotch; the nose is the front-most point of the head; the chin is where the face's front profile falls
away under the nose. The shoulders, elbows, knees and face features follow from those by proportions measured on Haru (checked by eye)."""
import sys, json, struct, math
import numpy as np

path = sys.argv[1]; rot = float(sys.argv[sys.argv.index('--rot') + 1]) if '--rot' in sys.argv else 0.0
b = open(path, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + L]); bin0 = 20 + L + 8
a = j['accessors'][j['meshes'][0]['primitives'][0]['attributes']['POSITION']]; bv = j['bufferViews'][a['bufferView']]
st = bv.get('byteStride', 12) // 4; o = bin0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
P = np.frombuffer(b, np.float32, count=a['count'] * st, offset=o).reshape(-1, st)[:, :3].astype(float)
if rot: c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot)); P = P @ np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])
P -= [(P[:, 0].min() + P[:, 0].max()) / 2, 0, (P[:, 2].min() + P[:, 2].max()) / 2]
x, y, z = P.T; floor, top = y.min(), y.max(); H = top - floor

def intervals(sel, gap=.008 * H):
    xs = np.sort(x[sel])
    if len(xs) == 0: return []
    cut = np.where(np.diff(xs) > gap)[0]; return list(zip([xs[0]] + list(xs[cut + 1]), list(xs[cut]) + [xs[-1]]))

# crotch: going up from the knees, the first band where something crosses the middle
crotch = None
for yy in np.arange(floor + .2 * H, floor + .7 * H, .004 * H):
    iv = intervals((y >= yy) & (y < yy + .006 * H) & (np.abs(x) < .25 * H), gap=.004 * H)
    if any(lo < -.01 * H and hi > .01 * H for lo, hi in iv): crotch = yy; break   # one piece of clay across the middle
skirt = crotch is None or crotch < floor + .30 * H                             # a long coat, skirt or dress hides where the legs part
if skirt: crotch = floor + (.35 if '--child' in sys.argv else .37) * H
legs = (y > crotch - .1 * H) & (y < crotch - .02 * H); hipx = np.median(np.abs(x[legs & (np.abs(x) < .12 * H)])) if legs.any() else .06 * H
hip = crotch + .015 * H
# hands: the outer clusters between the crotch and mid-thigh
handsel = (y < crotch + .05 * H) & (y > crotch - .2 * H) & (np.abs(x) > hipx + .05 * H)
tip = y[handsel].min() if handsel.any() else crotch - .1 * H
hx = np.median(np.abs(x[handsel])) if handsel.any() else .17 * H
wrist = tip + .07 * H
# nose: the front-most point in the upper body; chin: under the nose, where the front profile has dropped back by a third of the head depth
up = y > floor + .6 * H; ni = np.argmax(np.where(up & (np.abs(x) < .05 * H), z, -9)); nose = P[ni]
prof = []
for yy in np.arange(nose[1], floor + .5 * H, -.004 * H):
    s = (y >= yy - .003 * H) & (y < yy + .003 * H) & (np.abs(x) < .015 * H)
    if s.any(): prof.append((yy, z[s].max()))
headDepth = z[up & (y > nose[1])].max() - z[up & (y > nose[1])].min()
chin = next((yy for yy, zz in prof if zz < nose[2] - .36 * headDepth), nose[1] - .1 * H)
hh = top - chin                                                    # head height, chin to crown
shoulder = chin - .095 * H; sx = max(hx * .86, hipx + .07 * H)
R = {'note': 'measured by tools/glb_autorig.py', 'rot': rot, 'skirt': bool(skirt), 'front': [0, 0, 1], 'floor': round(floor, 4),
     'hip': [round(hipx, 4), round(hip, 4), 0], 'pelvis': [0, round(hip, 4), 0], 'chestBase': [0, round(hip + .026 * H, 4), 0],
     'neckBase': [0, round(chin - .065 * H, 4), 0], 'headBase': [0, round(chin - .01 * H, 4), .01 * H], 'headTop': [0, round(top, 4), 0],
     'shoulder': [round(sx, 4), round(shoulder, 4), 0], 'elbow': [round((sx + hx) / 2 * 1.08, 4), round((shoulder + wrist) / 2, 4), 0],
     'wrist': [round(hx, 4), round(wrist, 4), .015 * H], 'fingerTip': [round(hx, 4), round(tip, 4), .02 * H],
     'knee': [round(hipx, 4), round((hip + floor + .045 * H) / 2, 4), .015 * H], 'ankle': [round(hipx, 4), round(floor + .045 * H, 4), 0],
     'toe': [round(hipx, 4), round(floor + .01 * H, 4), .1 * H],
     'face': {'note': 'drawn 2D face, placed around the sculpted nose', 'x': [round(-.31 * hh, 4), round(.31 * hh, 4)], 'y': [round(chin, 4), round(nose[1] + .39 * hh, 4)],
              'eyes': [round(.157 * hh, 4), round(nose[1] + .13 * hh, 4), round(.063 * hh, 4)], 'brows': [round(.157 * hh, 4), round(nose[1] + .245 * hh, 4)],
              'mouth': [0, round(nose[1] - .115 * hh, 4), round(.176 * hh, 4)], 'skinTarget': '#e2a07e'},
     'clean': True, 'skinDone': True}
out = path.replace('.glb', '.rig.json'); json.dump(R, open(out, 'w'), indent=1)
print(f'{out}: H {H:.3f} crotch {crotch:.3f} hands {tip:.3f} nose {nose.round(3).tolist()} chin {chin:.3f}')
