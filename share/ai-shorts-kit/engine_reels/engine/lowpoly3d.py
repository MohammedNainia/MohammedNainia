"""Stylised low-poly 3D on the CPU (no GPU): flat-shaded meshes, perspective camera, sun + ambient light,
depth fog, painter's-algorithm drawing with Pillow. Good for toy-like / clay-like / low-poly worlds.

    from engine.lowpoly3d import Scene3D, icosphere, terrain, tree, box, figure, look_cam
    sc = Scene3D(sky=('#0b1236', '#f2a27a'), sun=(-.4, -.8, -.4))
    sc.add(icosphere(2, r=300), color='#4a6fa5')
    img = sc.render(look_cam(eye=(0, -150, -900), target=(0, 0, 0)))      # HxWx3 float 0..1
"""
import math, numpy as np
from PIL import Image, ImageDraw
W, H, SS = 1080, 1920, 2

def hexc(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255

# ---------- meshes: (V Nx3, F Mx3, per-face colour Mx3) ----------
def icosphere(sub=2, r=1.0, center=(0, 0, 0), jitter=0.0, seed=1):
    t = (1 + 5 ** .5) / 2
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
         (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    V = [np.array(v, float) / np.linalg.norm(v) for v in V]
    for _ in range(sub):
        cache = {}; nf = []
        def mid(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache:
                m = V[a] + V[b]; V.append(m / np.linalg.norm(m)); cache[k] = len(V) - 1
            return cache[k]
        for a, b, c in F:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a); nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        F = nf
    V = np.array(V)
    if jitter: V *= (1 + np.random.default_rng(seed).uniform(-jitter, jitter, (len(V), 1)))
    return V * r + np.array(center, float), np.array(F)

def box(size=(1, 1, 1), center=(0, 0, 0)):
    sx, sy, sz = np.array(size) / 2
    V = np.array([(x, y, z) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]) + np.array(center, float)
    F = np.array([(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)])
    return V, F

def cone(r=1, h=2, n=7, base=(0, 0, 0)):
    """y is up-negative (screen-like): the tip is at base_y - h"""
    bx, by, bz = base; V = [(bx, by - h, bz)] + [(bx + r * math.cos(2 * math.pi * i / n), by, bz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    F = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)] + [(1, 1 + (i + 1) % n, 1 + i) for i in range(1, n - 1)]
    return np.array(V, float), np.array(F)

def terrain(size=2000, n=22, amp=120, seed=3, center=(0, 0, 0), flat_r=0):
    r = np.random.default_rng(seed); xs = np.linspace(-size / 2, size / 2, n)
    hgt = np.zeros((n, n))
    for oct_, a in ((3, 1), (6, .45), (12, .2)):
        g = r.uniform(-1, 1, (oct_ + 1, oct_ + 1))
        from PIL import Image as _I
        hgt += a * (np.asarray(_I.fromarray(((g + 1) * 127.5).astype(np.uint8)).resize((n, n), _I.BICUBIC), float) / 127.5 - 1)
    V = []; cx, cy, cz = center
    for i, z in enumerate(xs):
        for j, x in enumerate(xs):
            d = math.hypot(x, z); k = 1 if d > flat_r else (d / flat_r) ** 2 if flat_r else 1
            V.append((cx + x, cy - hgt[i, j] * amp * k, cz + z))
    F = []
    for i in range(n - 1):
        for j in range(n - 1):
            a, b, c, d = i * n + j, i * n + j + 1, (i + 1) * n + j, (i + 1) * n + j + 1
            F += [(a, c, b), (b, c, d)]
    return np.array(V, float), np.array(F)

def tree(base, h=120, kind='pine', seed=0):
    r = np.random.default_rng(seed); x, y, z = base; parts = []
    parts.append((box((h * .08, h * .3, h * .08), (x, y - h * .15, z)), '#6b4a33'))
    if kind == 'pine':
        for k, (rr, hh, off) in enumerate([(h * .35, h * .5, .25), (h * .27, h * .42, .45), (h * .18, h * .34, .62)]):
            parts.append((cone(rr, hh, 7, (x, y - h * off, z)), None))
    else:
        parts.append((icosphere(1, h * .32, (x, y - h * .62, z), .18, seed), None))
    return parts

def figure(base, h=60, coat='#c97b63', skin='#e7c4a0'):
    x, y, z = base
    return [(box((h * .32, h * .5, h * .22), (x, y - h * .38, z)), coat),
            (icosphere(1, h * .14, (x, y - h * .78, z)), skin),
            (box((h * .1, h * .18, h * .1), (x - h * .08, y - h * .06, z)), '#2a2a3a'),
            (box((h * .1, h * .18, h * .1), (x + h * .08, y - h * .06, z)), '#2a2a3a')]

# ---------- camera ----------
def look_cam(eye, target, fov=50, roll=0.0):
    eye = np.array(eye, float); f = np.array(target, float) - eye; f /= np.linalg.norm(f)
    down = np.array([math.sin(roll), math.cos(roll), 0.0])          # world y grows downwards (like the screen)
    rgt = np.cross(down, f); rgt /= np.linalg.norm(rgt); u = np.cross(f, rgt)
    return {'eye': eye, 'R': np.stack([rgt, u, f]), 'f': (H / 2) / math.tan(math.radians(fov) / 2)}

# ---------- scene ----------
class Scene3D:
    def __init__(self, sky=('#0b1236', '#3a3f74'), sun=(-.4, -.8, -.45), ambient=.38, fog=('#3a3f74', 2600, 6000), outline=None):
        self.sky, self.sun, self.amb, self.fog, self.outline = sky, np.array(sun, float) / np.linalg.norm(sun), ambient, fog, outline
        self.items = []
    def add(self, mesh, color='#888888', vary=.06, seed=0):
        V, F = mesh; r = np.random.default_rng(seed)
        cols = np.repeat(hexc(color)[None], len(F), 0) * (1 + r.uniform(-vary, vary, (len(F), 1)))
        self.items.append((V, F, np.clip(cols, 0, 1)))
    def add_parts(self, parts, default='#3f6b4a', seed=0):
        for k, (mesh, col) in enumerate(parts): self.add(mesh, col or default, seed=seed + k)
    def render(self, cam, extra_sky=None):
        top, low = hexc(self.sky[0]), hexc(self.sky[1]); yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        img = (top * (1 - yy) + low * yy) * np.ones((1, W, 3), np.float32)
        if extra_sky is not None: img = extra_sky(img)
        tris = []
        for V, F, C in self.items:
            P = (V - cam['eye']) @ cam['R'].T
            for (a, b, c), col in zip(F, C):
                pa, pb, pc = P[a], P[b], P[c]
                if min(pa[2], pb[2], pc[2]) < 5: continue
                n = np.cross(V[b] - V[a], V[c] - V[a]); nn = np.linalg.norm(n)
                if nn == 0: continue
                n /= nn
                cen = (V[a] + V[b] + V[c]) / 3
                if np.dot(n, cam['eye'] - cen) < 0: n = -n
                shade = self.amb + (1 - self.amb) * max(0.0, float(np.dot(n, -self.sun)))
                depth = (pa[2] + pb[2] + pc[2]) / 3
                pts = [(cam['f'] * p[0] / p[2] + W / 2, cam['f'] * p[1] / p[2] + H / 2) for p in (pa, pb, pc)]
                fc, f0, f1 = hexc(self.fog[0]), self.fog[1], self.fog[2]
                k = min(1, max(0, (depth - f0) / (f1 - f0)))
                rgb = col * shade * (1 - k) + fc * k
                tris.append((depth, pts, rgb))
        tris.sort(key=lambda x: -x[0])
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((W * SS, H * SS), Image.NEAREST)
        d = ImageDraw.Draw(im)
        for _, pts, rgb in tris:
            q = [(x * SS, y * SS) for x, y in pts]; c = tuple(int(v * 255) for v in np.clip(rgb, 0, 1))
            d.polygon(q, fill=c, outline=c if self.outline is None else self.outline)
        return np.asarray(im.resize((W, H), Image.BOX), np.float32) / 255
