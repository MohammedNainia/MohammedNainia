"""The Paper Visitor - motion test (16:9, 20 s). Upgraded paper-puppet character + night bedroom + slow-burn timing.
  python motion_test.py [workers]  ->  motion_test.mp4 (1920x1080, 30 fps) + visitor_sheet.png
Timeline: 0-4 asleep, breathing (slow push-in) | 4-6 eyes open | 6.5 one footstep in the hallway, then silence |
7.5-10 slow head turn toward the door | 10-13 sits up | 13-16 freezes, hand grips the blanket | 16-20 camera drifts to the
corner: the Paper Visitor, full height, perfectly still. A small folded one has been on her pillow the whole time."""
import os, sys, math, subprocess, numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, SS, FPS, DUR = 1920, 1080, 2, 30, 20.0

def ss(a, b, t): x = min(1, max(0, (t - a) / (b - a))); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def rot(v, a): return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))
def add(p, q): return (p[0] + q[0], p[1] + q[1])

# ---------------- camera ----------------
def camera(t):
    keys = [(0, 3.0, (700, 585)), (6, 3.5, (690, 580)), (10, 3.2, (720, 575)), (13, 2.1, (860, 540)), (16, 2.1, (860, 540)), (19.5, 1.7, (1250, 520)), (DUR, 1.7, (1250, 520))]
    for (t0, z0, c0), (t1, z1, c1) in zip(keys, keys[1:]):
        if t <= t1:
            k = ss(t0, t1, t); return lerp(z0, z1, k), (lerp(c0[0], c1[0], k), lerp(c0[1], c1[1], k))
    return keys[-1][1], keys[-1][2]

class Pen:
    """draws world-space shapes through the camera onto a supersampled RGBA layer"""
    def __init__(s, t):
        s.z, s.c = camera(t); s.im = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im)
    def P(s, p): return ((p[0] - s.c[0]) * s.z * SS + W / 2 * SS, (p[1] - s.c[1]) * s.z * SS + H / 2 * SS)
    def poly(s, pts, col): s.d.polygon([s.P(p) for p in pts], fill=col)
    def line(s, pts, col, w): s.d.line([s.P(p) for p in pts], fill=col, width=max(1, int(w * s.z * SS)), joint='curve')
    def ell(s, c, rx, ry, col, a=0.0, n=28):
        s.poly([add(c, rot((rx * math.cos(q), ry * math.sin(q)), a)) for q in np.linspace(0, 2 * math.pi, n, endpoint=False)], col)
    def caps(s, p, q, r, col):                      # a limb: a thick line with round ends
        s.line([p, q], col, 2 * r); s.ell(p, r, r, col); s.ell(q, r, r, col)

# ---------------- set ----------------
WALL, FLOOR, WOOD, SHEET, BLANKET = (66, 76, 104), (44, 50, 70), (74, 58, 54), (200, 196, 190), (92, 104, 140)
def room(pen, t):
    pen.poly([(-400, -300), (2400, -300), (2400, 760), (-400, 760)], WALL + (255,))
    pen.poly([(-400, 760), (2400, 760), (2400, 1500), (-400, 1500)], FLOOR + (255,))
    pen.poly([(-400, 752), (2400, 752), (2400, 764), (-400, 764)], (54, 60, 82, 255))                      # skirting
    pen.poly([(170, 170), (430, 170), (430, 470), (170, 470)], (30, 34, 48, 255))                         # window frame
    pen.poly([(186, 186), (414, 186), (414, 454), (186, 454)], (150, 170, 205, 255))                     # night sky glass
    pen.line([(300, 186), (300, 454)], (30, 34, 48, 255), 10); pen.line([(186, 320), (414, 320)], (30, 34, 48, 255), 10)
    pen.ell((360, 250), 26, 26, (230, 232, 220, 255))                                                      # moon
    sway = 6 * math.sin(t * .4)
    pen.poly([(130, 150), (205 + sway, 150), (190 + sway, 500), (120, 510)], (58, 54, 80, 255))           # curtains
    pen.poly([(395 - sway, 150), (470, 150), (480, 510), (410 - sway, 500)], (58, 54, 80, 255))
    pen.poly([(1490, 250), (1730, 250), (1730, 760), (1490, 760)], (40, 44, 60, 255))                     # door frame
    gap = 34 + 20 * ss(6.3, 7.2, t)                                                                         # the door has been open a crack
    pen.poly([(1505, 265), (1715, 265), (1715, 760), (1505, 760)], (8, 9, 14, 255))                       # hallway dark
    pen.poly([(1505 + gap, 265), (1715, 265), (1715, 760), (1505 + gap, 760)], (80, 72, 70, 255))         # door slab
    pen.ell((1530 + gap, 520), 7, 7, (150, 140, 120, 255))
    pen.poly([(380, 610), (500, 610), (500, 760), (380, 760)], (62, 50, 48, 255))                         # nightstand
    pen.poly([(420, 520), (460, 520), (470, 600), (410, 600)], (190, 180, 160, 255)); pen.poly([(436, 600), (444, 600), (444, 612), (436, 612)], (90, 80, 70, 255))
    pen.poly([(500, 470), (545, 470), (545, 720), (500, 720)], WOOD + (255,))                             # headboard
    pen.poly([(520, 640), (1190, 640), (1190, 720), (520, 720)], WOOD + (255,))                           # bed frame
    pen.poly([(540, 600), (1180, 600), (1180, 660), (540, 660)], SHEET + (255,))                          # mattress
    pen.ell((640, 590), 85, 28, (225, 222, 215, 255))                                                      # pillow

# ---------------- the girl: a jointed paper puppet ----------------
SKIN, SKIN_SH, HAIR, PJ, PJ_SH = (226, 200, 178, 255), (196, 168, 148, 255), (38, 28, 26, 255), (110, 128, 168, 255), (88, 104, 140, 255)
def girl_pose(t):
    breath = math.sin(t * 2 * math.pi / 4.2) * (1 - .6 * ss(6.3, 6.8, t)) * (1 - ss(13, 13.5, t))       # breathing stops when she freezes
    eyes = ss(4, 6, t) - .9 * (math.exp(-((t - 9.0) / .06) ** 2))                                         # opens, one slow blink at 9 s
    turn = ss(7.5, 10, t)                                                                                 # 0 = face up, 1 = looking toward the door
    up = ss(10.2, 12.8, t)                                                                                # sitting up
    grip = ss(13, 14.2, t)
    return dict(breath=breath, eyes=max(0, eyes), turn=turn, up=up, grip=grip, brow=ss(6.6, 7.4, t))

def head(pen, c, a, p):
    """head at c, rotation a (local up = -y); turn = 0 front, 1 three-quarter toward the door; eyes 0 closed .. 1 open"""
    turn, eyes, brow = p['turn'], p['eyes'], p['brow']
    sq = 1 - .22 * turn                                                                   # head narrows as it turns
    def L(x, y): return add(c, rot((x * sq + 14 * turn, y), a))
    def Lf(x, y): return add(c, rot((x * sq * (1 - .25 * turn) + 16 * turn, y), a))       # face features slide toward the turn
    pen.poly([L(-46, -8), L(-40, -46), L(0, -58), L(40, -46), L(48, -6), L(50, 40), L(-50, 42)], HAIR)    # hair back
    pen.ell(L(0, 0), 36 * sq, 44, SKIN, a)                                                # face
    pen.ell(L(-30 + 24 * turn, 6), 8 * sq, 40, SKIN_SH, a)                                # shadow side
    for side in (-1, 1):
        if side == -1 and turn > .85: continue
        ex, ey = 14 * side, 2
        w = 8.5 * (1 - .35 * turn * (side == -1))
        if eyes > .08:
            h = 4.6 * eyes
            pen.poly([Lf(ex - w, ey), Lf(ex, ey - h), Lf(ex + w, ey), Lf(ex, ey + h * .7)], (236, 232, 226, 255))
            pen.ell(Lf(ex + 2.5 * turn, ey + .2), 3.4, 3.4 * min(1, eyes * 1.3), (24, 22, 26, 255), a)
        pen.line([Lf(ex - w, ey), Lf(ex - w * .3, ey - 1.6), Lf(ex + w, ey)], (60, 44, 40, 255), 1.6)    # lash line / closed lid
        by = -12 - 2.5 * brow
        pen.line([Lf(ex - 9, by + 2 * brow * side * -.5), Lf(ex + 9, by - 1.5 * brow * side)], (50, 36, 32, 255), 2.2)
    pen.line([Lf(1, 9), Lf(-1, 15), Lf(3, 16)], SKIN_SH, 1.6)                                # nose
    m = 2.5 + 3 * brow
    pen.poly([Lf(-7, 26), Lf(7, 26), Lf(0, 26 + m * .6)], (150, 96, 92, 255))               # mouth (parts slightly in fear)
    pen.poly([L(-40, -30), L(-10, -52), L(30, -48), L(44, -20), L(20, -34), L(-6, -38), L(-30, -14)], HAIR)        # fringe
    pen.poly([L(-44, -20), L(-50, 30), L(-38, 46), L(-36, 4)], HAIR); pen.poly([L(42, -10), L(46, 34), L(36, 44), L(34, 0)], HAIR)

def hand(pen, wrist, a, grip):
    """small paper hand with four fingers and a thumb; grip 0 = relaxed, 1 = clutching"""
    pen.ell(add(wrist, rot((0, 11), a)), 10, 12, SKIN, a)
    for i, fx in enumerate((-7, -2.5, 2.5, 7)):
        base = add(wrist, rot((fx, 20), a)); tip = add(base, rot((0, 13 - 7 * grip), a + .25 * grip))
        pen.caps(base, tip, 2.6, SKIN)
    pen.caps(add(wrist, rot((-9, 8), a)), add(wrist, rot((-15 + 5 * grip, 18), a)), 3, SKIN)

def girl(pen, t):
    p = girl_pose(t)
    hip = (900, 628)
    th = lerp(math.pi, -math.pi / 2 - .12, p['up'])                 # torso direction: left (lying) -> up (sitting)
    d = (math.cos(th), math.sin(th)); n = (-d[1], d[0])
    torso_len = 175
    sh = add(hip, (d[0] * torso_len, d[1] * torso_len))
    b = 3 * p['breath']
    tw = 44 + b * .6
    pen.poly([add(hip, (n[0] * 46, n[1] * 46)), add(sh, (n[0] * tw, n[1] * tw)), add(sh, (-n[0] * tw, -n[1] * tw)), add(hip, (-n[0] * 46, -n[1] * 46))], PJ)
    pen.poly([add(hip, (n[0] * 46, n[1] * 46)), add(sh, (n[0] * tw, n[1] * tw)), add(sh, (n[0] * 26, n[1] * 26)), add(hip, (n[0] * 30, n[1] * 30))], PJ_SH)
    neck = add(sh, (d[0] * 22, d[1] * 22)); pen.caps(sh, neck, 12, SKIN)
    hc = add(neck, (d[0] * 48, d[1] * 48))
    ha = th + math.pi / 2 + .5 * p['turn'] * (1 - p['up']) - .15 * p['up'] + .35 * p['turn'] * p['up']
    if p['up'] < .5: hc = add(hc, (0, -10 * (1 - p['up'])))         # head rests on the pillow
    head(pen, hc, ha, p)
    # blanket: pulled up to the chest while lying, falls to the waist as she sits up
    edge = lerp(735, 905, p['up'])
    pen.poly([(edge, 600 - 8 * b / 3 - 30 * (1 - p['up'])), (1185, 585), (1200, 670), (edge - 20, 672)], BLANKET + (255,))
    pen.line([(edge + 10, 610 - 30 * (1 - p['up'])), (1180, 596)], (120, 132, 168, 255), 4)
    # near arm: lies on the blanket, then reaches down and grips it
    sa = add(sh, (n[0] * -30, n[1] * -30))
    up_a = th + lerp(-2.9, 1.2, p['up']) if False else lerp(-.15, 1.35, p['up']) + th + math.pi * (1 - p['up']) * 0
    elbow = add(sa, rot((80, 0), lerp(th + math.pi - .08, math.pi / 2 - .35, p['up'])))
    wrist = add(elbow, rot((74, 0), lerp(th + math.pi - .02, .25 - .2 * p['grip'], p['up'])))
    pen.caps(sa, elbow, 12, PJ); pen.caps(elbow, wrist, 10, PJ)
    hand(pen, wrist, math.atan2(wrist[1] - elbow[1], wrist[0] - elbow[0]) - math.pi / 2, p['grip'])

# ---------------- the Paper Visitor ----------------
PAPER, PAPER_SH, FOLD = (226, 220, 204, 255), (180, 172, 156, 255), (150, 142, 126, 255)
def visitor(pen, base, h, unfold=1.0, lean=0.0):
    """a tall paper figure with fold creases; unfold 0 = folded small, 1 = full height"""
    s = h / 430
    def V(x, y): return (base[0] + (x + lean * (430 + y)) * s, base[1] + y * s)
    body = [V(-36, 0), V(-30, -230), V(-58, -290), V(-40, -330), V(0, -345), V(40, -330), V(58, -290), V(30, -230), V(36, 0)]
    pen.poly(body, PAPER)
    pen.ell(V(0, -380), 30 * s, 40 * s, PAPER)
    pen.poly([V(-58, -290), V(-74, -120), V(-62, -112), V(-46, -270)], PAPER_SH); pen.poly([V(58, -290), V(74, -120), V(62, -112), V(46, -270)], PAPER_SH)
    pen.poly([V(0, -345), V(36, 0), V(14, 0), V(0, -230)], PAPER_SH)                       # one shaded facet
    for y in (-300, -230, -150, -70): pen.line([V(-34, y), V(34, y + 6)], FOLD, 1.6)      # horizontal folds
    pen.line([V(0, -345), V(0, 0)], FOLD, 1.4)
    pen.line([V(-12, -386), V(-4, -383)], (110, 104, 92, 255), 2.2); pen.line([V(4, -383), V(12, -386)], (110, 104, 92, 255), 2.2)   # two faint creases for eyes

def small_visitor(pen, c):
    pen.poly([(c[0] - 14, c[1] + 8), (c[0] + 14, c[1] + 8), (c[0] + 10, c[1] - 10), (c[0] - 10, c[1] - 10)], PAPER)
    pen.ell((c[0], c[1] - 16), 7, 8, PAPER)
    pen.line([(c[0] - 12, c[1]), (c[0] + 12, c[1] + 2)], FOLD, 1.2)

# ---------------- light + finish ----------------
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIGN = np.clip(1 - .75 * (((XX - W / 2) / (W * .62)) ** 2 + ((YY - H / 2) / (H * .62)) ** 2), 0, 1)[..., None] ** 1.3

def light_mask(t):
    z, c = camera(t); m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    def P(p): return ((p[0] - c[0]) * z + W / 2, (p[1] - c[1]) * z + H / 2)
    d.polygon([P((186, 186)), P((414, 186)), P((414, 454)), P((186, 454))], 255)                 # the window itself
    d.polygon([P((200, 470)), P((420, 470)), P((1180, 820)), P((640, 900))], 150)                 # moon shaft across floor and bed
    d.polygon([P((540, 560)), P((1000, 560)), P((1100, 700)), P((560, 700))], 120)                # her face and the bed catch it
    r = int(60 * z); return np.asarray(m.filter(ImageFilter.GaussianBlur(r)), np.float32)[..., None] / 255

def render(fi):
    t = fi / FPS
    pen = Pen(t); room(pen, t)
    small_visitor(pen, (588, 570))                                     # on her pillow, the whole time
    girl(pen, t)
    visitor(pen, (1390, 760), 520, lean=-.02)                           # in the corner: never moves
    img = np.asarray(pen.im.resize((W, H), Image.LANCZOS).convert('RGB'), np.float32) / 255
    moon = np.array([.62, .72, .95], np.float32)
    L = light_mask(t)
    flick = 1 + .02 * math.sin(t * 13) * math.sin(t * 7.3)
    out = img * (.2 + 1.15 * L * moon) * flick
    rng = np.random.default_rng(fi); out += rng.normal(0, .028, (H, W, 1)).astype(np.float32)   # film grain
    out *= VIGN
    out *= 1 - ss(DUR - .7, DUR, t)                                     # fade to black
    out *= ss(0, .4, t) * .7 + .3 if t < .4 else 1
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)

# ---------------- sound: room tone, one footstep, a paper rustle ----------------
def sound(path):
    sr = 44100; n = int(DUR * sr); rng = np.random.default_rng(3); t = np.arange(n) / sr
    tone = np.convolve(rng.standard_normal(n), np.ones(400) / 400, 'same') * .9 + .004 * np.sin(2 * np.pi * 55 * t)   # low room tone
    def step(at, amp):
        i = int(at * sr); m = int(.45 * sr); tt = np.arange(m) / sr
        thud = np.sin(2 * np.pi * (70 + 30 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 14)
        creak = np.convolve(rng.standard_normal(m), np.ones(30) / 30, 'same') * np.exp(-((tt - .12) / .08) ** 2) * .35
        tone[i:i + m] += amp * (thud + creak)
    step(6.5, .55)                                                      # one footstep in the hallway. Then nothing.
    i = int(16.2 * sr); m = int(1.2 * sr); x = rng.standard_normal(m); x -= np.convolve(x, np.ones(6) / 6, 'same')
    tone[i:i + m] += .05 * x * np.hanning(m) * (rng.random(m) > .7)        # paper, very soft
    tone *= np.minimum(1, (DUR - t) / .7)
    y = (np.clip(tone / np.abs(tone).max() * .5, -1, 1) * 32767).astype(np.int16)
    import wave
    with wave.open(path, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())

def sheet():
    """the Paper Visitor in three states, for approval"""
    pen = Pen(0); pen.z, pen.c = 1.0, (960, 540)
    pen.poly([(-100, -100), (2100, -100), (2100, 1200), (-100, 1200)], (34, 38, 52, 255))
    small_visitor(pen, (420, 700)); visitor(pen, (960, 760), 260); visitor(pen, (1500, 860), 640)
    pen.im.resize((W, H), Image.LANCZOS).convert('RGB').save(os.path.join(HERE, 'visitor_sheet.png'))

if __name__ == '__main__':
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    out = os.path.join(HERE, 'motion_test.mp4'); wav = os.path.join(HERE, 'motion_test.wav')
    sheet(); sound(wav)
    p = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', out], stdin=subprocess.PIPE)
    with Pool(workers) as pool:
        for fr in pool.imap(render, range(int(DUR * FPS)), chunksize=4): p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait(); print('saved', out)
