"""The Paper Visitor - motion test v2, kamishibai paper-theater style (16:9, 20 s).
Our own take on the old Japanese paper-theater look: flat painted cut-outs with pale cut edges and drop shadows,
sharp ink faces, a muted palette, and stiff hand-moved animation (puppets move on 8 fps steps with holds; the camera
glides). Same beats as v1: asleep -> eyes open -> one footstep -> head turns in steps -> sits up in jerks -> freezes ->
the camera finds the Paper Visitor in the corner.   python kamishibai_test.py [workers] -> kamishibai_test.mp4"""
import os, sys, math, subprocess, numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, SS, FPS, DUR = 1920, 1080, 2, 30, 20.0
STEP = 8.0                                     # puppet frame rate: hand-moved paper, not smooth animation

def ss(a, b, t): x = min(1, max(0, (t - a) / (b - a))); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def rot(v, a): return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))
def add(p, q): return (p[0] + q[0], p[1] + q[1])
def steps(k, n): return math.floor(k * n + 1e-6) / n          # a motion done in n visible paper steps

def camera(t):
    keys = [(0, 2.6, (700, 560)), (6, 2.8, (700, 555)), (10, 2.8, (720, 552)), (13.2, 2.0, (860, 520)), (16, 2.0, (860, 520)), (19.3, 1.7, (1250, 500)), (DUR, 1.7, (1250, 500))]
    for (t0, z0, c0), (t1, z1, c1) in zip(keys, keys[1:]):
        if t <= t1:
            k = ss(t0, t1, t); return lerp(z0, z1, k), (lerp(c0[0], c1[0], k), lerp(c0[1], c1[1], k))
    return keys[-1][1], keys[-1][2]

EDGE = (232, 222, 200, 255)          # the pale paper core showing at every cut edge
class Pen:
    def __init__(s, t, jit=(0, 0)):
        s.z, s.c = camera(t); s.j = jit
        s.im = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im)
        s.sh = Image.new('L', (W * SS, H * SS), 0); s.sd = ImageDraw.Draw(s.sh)
    def P(s, p): return ((p[0] + s.j[0] - s.c[0]) * s.z * SS + W / 2 * SS, (p[1] + s.j[1] - s.c[1]) * s.z * SS + H / 2 * SS)
    def cut(s, pts, col, edge=True, shadow=True):
        """one paper cut-out: drop shadow, pale cut edge, painted face"""
        q = [s.P(p) for p in pts]
        if shadow: s.sd.polygon([(x + 7 * SS, y + 9 * SS) for x, y in q], fill=150)
        s.d.polygon(q, fill=col, outline=EDGE if edge else None, width=max(1, int(1.6 * s.z * SS)) if edge else 0)
    def ink(s, pts, w=2.0, col=(22, 16, 14, 255)): s.d.line([s.P(p) for p in pts], fill=col, width=max(1, int(w * s.z * SS)), joint='curve')
    def oval(s, c, rx, ry, col, a=0.0, edge=True, shadow=True, n=30):
        s.cut([add(c, rot((rx * math.cos(q), ry * math.sin(q)), a)) for q in np.linspace(0, 2 * math.pi, n, endpoint=False)], col, edge, shadow)

# muted kamishibai palette
WALL, WALL2, FLOOR, WOOD, RED = (92, 70, 58, 255), (74, 56, 48, 255), (52, 40, 36, 255), (110, 66, 48, 255), (140, 46, 40, 255)
NIGHT, SHEET, QUILT, QUILT2 = (38, 48, 74, 255), (206, 192, 166, 255), (128, 44, 42, 255), (100, 34, 34, 255)
SKIN, HAIR, KIMONO, KIMONO2 = (232, 206, 178, 255), (24, 18, 18, 255), (64, 74, 98, 255), (48, 56, 76, 255)

def room(pen, t):
    pen.cut([(-500, -400), (2500, -400), (2500, 760), (-500, 760)], WALL, False, False)
    for x in range(-400, 2400, 160): pen.cut([(x, -400), (x + 10, -400), (x + 10, 760), (x, 760)], WALL2, False, False)     # wall planks
    pen.cut([(-500, 760), (2500, 760), (2500, 1600), (-500, 1600)], FLOOR, False, False)
    pen.cut([(160, 160), (440, 160), (440, 480), (160, 480)], WOOD)                                    # window
    pen.cut([(178, 178), (422, 178), (422, 462), (178, 462)], NIGHT, False, False)
    pen.oval((360, 250), 28, 28, (226, 214, 180, 255), shadow=False)
    pen.ink([(300, 178), (300, 462)], 9, (90, 54, 40, 255)); pen.ink([(178, 320), (422, 320)], 9, (90, 54, 40, 255))
    gap = 34 + 22 * (t >= 6.5)                                                                      # the door jumps open a little at the footstep
    pen.cut([(1480, 240), (1740, 240), (1740, 760), (1480, 760)], WOOD)
    pen.cut([(1496, 256), (1724, 256), (1724, 760), (1496, 760)], (10, 8, 8, 255), False, False)
    pen.cut([(1496 + gap, 256), (1724, 256), (1724, 760), (1496 + gap, 760)], (120, 84, 62, 255))
    pen.cut([(370, 610), (500, 610), (500, 760), (370, 760)], WOOD)                                      # nightstand + paper lantern (unlit)
    pen.cut([(408, 500), (462, 500), (470, 600), (400, 600)], (196, 170, 130, 255))
    for y in (520, 545, 570): pen.ink([(404, y), (466, y)], 1.2, (140, 110, 80, 255))
    pen.cut([(495, 450), (545, 450), (545, 720), (495, 720)], WOOD)                                      # headboard
    pen.cut([(520, 640), (1195, 640), (1195, 725), (520, 725)], WOOD)
    pen.cut([(540, 598), (1185, 598), (1185, 652), (540, 652)], SHEET)
    pen.oval((640, 588), 86, 26, (222, 210, 186, 255))

# ---------------- the girl: rigid paper pieces moved in steps ----------------
def pose(t):
    tq = math.floor(t * STEP) / STEP                                            # everything below moves on paper steps
    return dict(
        breath=(math.floor(tq * 2) % 2) * (1 - (tq > 6.5)) * (tq < 13),          # the quilt lifts on alternate beats
        eyes=0 if tq < 4.6 else (.5 if tq < 5.2 else 1.0),                        # lids open in two steps
        blink=8.9 <= tq < 9.1,
        turn=steps(ss(7.6, 10, tq), 3),                                           # head turns in three clicks
        up=[0, 0, .18, .18, .52, .52, .52, .86, 1.0][min(8, int(ss(10.2, 13.2, tq) * 8))],   # a hand pushes, a pause, then the rest
        grip=steps(ss(13.2, 14.2, tq), 2), fear=ss(6.5, 7.0, tq))

def face_profile(pen, c, a, p):
    """head in profile, facing +x of local frame; drawn with sharp ink lines"""
    def L(x, y): return add(c, rot((x, y), a))
    pen.cut([L(-46, -50), L(10, -60), L(30, -36), L(-10, 60), L(-52, 70), L(-60, 10)], HAIR)                 # long hair behind
    pen.cut([L(-30, -40), L(14, -46), L(34, -24), L(36, -6), L(44, 6), L(36, 12), L(38, 22), L(30, 30), L(32, 38), L(18, 50), L(-14, 48), L(-32, 20)], SKIN)
    pen.cut([L(-34, -44), L(16, -54), L(38, -30), L(14, -36), L(-8, -30), L(-22, 0), L(-36, 10)], HAIR, edge=True, shadow=False)   # fringe
    if p['eyes'] > 0 and not p['blink']:
        h = 7 * p['eyes'] * (1 + .25 * p['fear'])
        pen.cut([L(10, -6), L(20, -6 - h * .7), L(28, -5), L(20, -6 + h * .35)], (240, 234, 222, 255), edge=False, shadow=False)
        pen.oval(L(21 + 2 * p['fear'], -6), 2.6 - .8 * p['fear'], 2.6 - .8 * p['fear'], (14, 10, 10, 255), a, edge=False, shadow=False)
        pen.ink([L(9, -6), L(20, -7 - h * .75), L(29, -5)], 2.2)
    else:
        pen.ink([L(9, -5), L(20, -2), L(29, -5)], 2.2)                                                      # closed lid
    pen.ink([L(8, -18 - 4 * p['fear']), L(22, -21 - 5 * p['fear']), L(30, -17)], 2.6)                        # brow tenses
    pen.ink([L(28, 22 + 2 * p['fear']), L(34, 22 + 3 * p['fear'])], 1.8)                                    # mouth

def girl(pen, t):
    p = pose(t)
    hip = (905, 626)
    th = lerp(math.pi, 1.5 * math.pi - .1, p['up'])          # rises through 'up', never through the bed
    d = (math.cos(th), math.sin(th)); n = (-d[1], d[0])
    sh = add(hip, (d[0] * 170, d[1] * 170))
    b = 4 * p['breath']
    pen.cut([add(hip, (n[0] * 44, n[1] * 44)), add(sh, (n[0] * (42 + b), n[1] * (42 + b))), add(sh, (-n[0] * 40, -n[1] * 40)), add(hip, (-n[0] * 44, -n[1] * 44))], KIMONO)
    pen.cut([add(sh, (n[0] * 30, n[1] * 30)), add(hip, (n[0] * 24, n[1] * 24)), add(hip, (n[0] * 10, n[1] * 10)), add(sh, (n[0] * 6, n[1] * 6))], RED, shadow=False)   # collar stripe
    neck = add(sh, (d[0] * 26, d[1] * 26))
    # lying: profile faces up (toward the ceiling); turning = the head tips toward the door in clicks; sitting: profile faces the door
    ha = lerp(-math.pi / 2 + .75 * p['turn'], -.05 + .12 * p['fear'], p['up'])     # lying: nose to the ceiling; turns toward the door in clicks
    face_profile(pen, add(neck, (d[0] * 44, d[1] * 44)), ha, p)
    edge = lerp(745, 900, p['up'])
    pen.cut([(edge, 598 - b - 26 * (1 - p['up'])), (1190, 582), (1200, 668), (edge - 14, 668)], QUILT)
    for x in range(int(edge) + 40, 1180, 90): pen.ink([(x, 590 - 18 * (1 - p['up']) * (x < 900)), (x + 20, 662)], 1.4, (90, 30, 30, 255))   # quilt stitching
    # arm: one paper piece from the shoulder to the hand, hinged at the elbow
    sa = add(sh, (-n[0] * 26, -n[1] * 26))
    a1 = th + math.pi - .1 + .25 * p['up']                      # upper arm follows the body: hand pushes on the mattress as she rises
    elbow = add(sa, rot((78, 0), a1))
    a2 = a1 + .05 - 1.25 * p['up'] - .3 * p['grip'] * p['up']
    wrist = add(elbow, rot((70, 0), a2))
    def limb(p0, p1, w, col):
        dd = (p1[0] - p0[0], p1[1] - p0[1]); l = math.hypot(*dd) or 1; nn = (-dd[1] / l * w, dd[0] / l * w)
        pen.cut([add(p0, nn), add(p1, nn), add(p1, (-nn[0], -nn[1])), add(p0, (-nn[0], -nn[1]))], col)
    limb(sa, elbow, 14, KIMONO2); limb(elbow, wrist, 12, KIMONO2)
    ang = math.atan2(wrist[1] - elbow[1], wrist[0] - elbow[0])
    def Hd(x, y): return add(wrist, rot((x, y), ang))
    pen.cut([Hd(0, -10), Hd(16, -11), Hd(26 - 8 * p['grip'], -7), Hd(28 - 10 * p['grip'], 0), Hd(26 - 8 * p['grip'], 6), Hd(14, 10), Hd(0, 9)], SKIN)
    for k in (-5, 0, 5): pen.ink([Hd(16, k), Hd(26 - 8 * p['grip'], k + 2 * p['grip'])], 1.2, (150, 110, 90, 255))

# ---------------- the Paper Visitor: torn, creased, faceless ----------------
VP, VP2 = (214, 204, 182, 255), (172, 160, 138, 255)
def visitor(pen, base, h):
    s = h / 470; r = np.random.default_rng(7)
    def V(x, y): return (base[0] + x * s, base[1] + y * s)
    outline = [(-30, 0), (-26, -200), (-34, -250), (-70, -300), (-62, -330), (-30, -345), (-24, -380), (-30, -420), (-18, -452), (0, -460),
               (18, -452), (30, -420), (24, -380), (30, -345), (62, -330), (70, -300), (34, -250), (26, -200), (30, 0)]
    torn = [V(x + r.uniform(-4, 4), y + r.uniform(-4, 4)) for x, y in outline]
    pen.cut(torn, VP)
    pen.cut([V(-70, -300), V(-84, -110), V(-74, -96), V(-60, -290)], VP2); pen.cut([V(70, -300), V(84, -110), V(74, -96), V(60, -290)], VP2)
    pen.cut([V(0, -345), V(30, 0), V(10, 0), V(0, -200)], VP2, shadow=False)
    for y in (-320, -250, -170, -90): pen.ink([V(-28, y), V(28, y + 5)], 1.3, (130, 118, 100, 255))
    pen.ink([V(0, -460), V(0, 0)], 1.1, (130, 118, 100, 255))
    pen.ink([V(-12, -416), V(-4, -413)], 2.0, (90, 80, 68, 255)); pen.ink([V(4, -413), V(12, -416)], 2.0, (90, 80, 68, 255))

def small_visitor(pen, c):
    pen.cut([(c[0] - 13, c[1] + 8), (c[0] + 13, c[1] + 8), (c[0] + 9, c[1] - 10), (c[0] - 9, c[1] - 10)], VP)
    pen.oval((c[0], c[1] - 16), 7, 8, VP)
    pen.ink([(c[0] - 11, c[1]), (c[0] + 11, c[1] + 2)], 1.0, (130, 118, 100, 255))

# ---------------- light, paper texture, finish ----------------
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIGN = np.clip(1 - .7 * (((XX - W / 2) / (W * .6)) ** 2 + ((YY - H / 2) / (H * .6)) ** 2), 0, 1)[..., None] ** 1.2
_r = np.random.default_rng(11)
FIBRE = (1 + .07 * np.asarray(Image.fromarray((_r.random((H // 3, W // 3)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255 - .035)

def light(t):
    z, c = camera(t); m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    def P(p): return ((p[0] - c[0]) * z + W / 2, (p[1] - c[1]) * z + H / 2)
    d.polygon([P((178, 178)), P((422, 178)), P((422, 462)), P((178, 462))], 255)
    d.polygon([P((190, 470)), P((430, 470)), P((1220, 820)), P((640, 920))], 170)
    d.polygon([P((540, 520)), P((1050, 520)), P((1120, 700)), P((560, 700))], 150)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(int(50 * z))), np.float32)[..., None] / 255

def render(fi):
    t = fi / FPS; tq = math.floor(t * STEP) / STEP
    jr = np.random.default_rng(int(tq * 100)); jit = (jr.uniform(-.6, .6), jr.uniform(-.6, .6))          # the paper trembles a hair on each step
    pen = Pen(t, jit); room(pen, t); small_visitor(pen, (588, 568)); girl(pen, t); visitor(pen, (1395, 760), 560)
    lay = pen.im.resize((W, H), Image.LANCZOS); shad = np.asarray(pen.sh.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255
    img = np.asarray(lay.convert('RGB'), np.float32) / 255
    img *= (1 - .45 * shad) * FIBRE
    L = light(t); moon = np.array([.66, .74, .98], np.float32)
    out = img * (.34 + 1.0 * L * moon)
    out *= VIGN; out *= 1 - ss(DUR - .7, DUR, t)
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)

if __name__ == '__main__':
    from motion_test import sound
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    out = os.path.join(HERE, 'kamishibai_test.mp4'); wav = os.path.join(HERE, 'kamishibai_test.wav'); sound(wav)
    p = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', out], stdin=subprocess.PIPE)
    with Pool(workers) as pool:
        for fr in pool.imap(render, range(int(DUR * FPS)), chunksize=4): p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait(); print('saved', out)
