"""The Morning Train (9:16, ~69 s): problem of other minds, told as a horror moment.
    python reel.py                     -> morning_train_1080x1920.mp4
    python reel.py --frames 0,300,800  -> check frames in check/"""
import os, sys, json, math, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.join(HERE, 'stills'); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS = 1080, 1920, 30
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
CL = os.path.join(HERE, 'clips_kling')
XF = .4                                                  # soft dissolve between shots
HARD = {14.6, 16.4, 52.4}                                # cuts that stay hard: lights out, lights on, the flash
HOOK = ['Is anyone', 'really there?']

# voice: (name, start second). w1 lives inside the lip-sync clip (speech starts 0.7 s into it)
LINES = [('n1', .4), ('n2', 5.0), ('n3', 10.6), ('n4', 16.4), ('n5', 20.3), ('w1', 26.4 + .7), ('n6', 31.2), ('n7', 38.1),
         ('n8', 44.2), ('n9', 50.3), ('n10', 52.8), ('n11', 59.0), ('n12', 61.8)]
DUR = 69.0; N = int(DUR * FPS)
WORDS = json.load(open(os.path.join(VO, 'words.json')))

# (start, end, source, zoom from->to, centre from->to, effects). source: still png, 'clip:<mp4>' or 'black'
SHOTS = [
    (0.0, 4.9, 'mov:t1:0:120', (1.00, 1.04), ((.5, .5), (.51, .49)), {}),
    (4.9, 10.4, 'mov:t2:30:100', (1.00, 1.04), ((.5, .45), (.5, .43)), {}),
    (10.4, 14.6, 't3_tunnel_dark.png', (1.03, 1.06), ((.5, .5), (.5, .5)), {'lights_out': 13.6}),
    (14.6, 16.4, 'black', (1, 1), ((.5, .5), (.5, .5)), {}),
    (16.4, 21.0, 'mov:t4:0:120', (1.00, 1.05), ((.5, .5), (.5, .47)), {'flicker_on': 1}),
    (21.0, 26.4, 't5_woman_b.png', (1.00, 1.09), ((.5, .45), (.5, .40)), {'flicker': 1}),
    (26.4, 30.74, 'clip:w1_lipsync.mp4', (1.00, 1.04), ((.5, .45), (.5, .43)), {'flicker': 1}),
    (30.74, 37.9, 'mov:t7:0:120', (1.00, 1.06), ((.5, .5), (.48, .5)), {'flicker': 1}),      # the face peels further open
    (37.9, 44.0, 'mov:t8:0:120', (1.00, 1.05), ((.5, .5), (.52, .46)), {}),
    (44.0, 50.2, 'mov:t4:120:30', (1.05, 1.12), ((.5, .47), (.58, .5)), {'flicker': 1}),
    (50.2, 52.4, 'mov:t2:96:120', (1.06, 1.10), ((.5, .42), (.5, .40)), {'dim': .6}),       # she shakes
    (52.4, 58.6, 'mov:t1:0:120', (1.00, 1.04), ((.5, .5), (.5, .5)), {'flash_in': 1}),
    (58.6, 61.5, 'mov:t9:0:50', (1.00, 1.25), ((.5, .5), (.76, .42)), {}),     # push in on the tear in her cheek
    (61.5, 67.3, 'mov:t9:50:120', (1.25, 1.28), ((.76, .42), (.76, .42)), {}),
    (67.3, DUR, 'mov:t1:30:0', (1.03, 1.00), ((.51, .49), (.5, .5)), {}),     # plays back onto frame 0 (loop)
]

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
_c = {}
def img(n):
    if n not in _c: _c[n] = cv2.imread(os.path.join(ST, n)).astype(np.float32) / 255
    return _c[n]
def clip_frame(name, t):
    k = 'clip:' + name
    if k not in _c:
        cap = cv2.VideoCapture(os.path.join(ST, name)); fr = []
        while True:
            ok, f = cap.read()
            if not ok: break
            fr.append(f.astype(np.float32) / 255)
        _c[k] = (fr, cap.get(cv2.CAP_PROP_FPS) or 25)
    fr, fps = _c[k]; return fr[min(len(fr) - 1, int(t * fps))]
def mov(name):                                           # Artlist clip (480x864): every frame matched to frame 0's colour level
    k = 'mov:' + name
    if k not in _c:
        cap = cv2.VideoCapture(os.path.join(CL, name + '.mp4')); fr = []
        while True:
            ok, f = cap.read()
            if not ok: break
            fr.append(f.astype(np.float32) / 255)
        ref = fr[0].reshape(-1, 3).mean(0); g = np.array([ref / (f.reshape(-1, 3).mean(0) + 1e-4) for f in fr])
        g = cv2.GaussianBlur(g.astype(np.float32)[:, None, :], (1, 0), sigmaX=1, sigmaY=4)[:, 0]   # smooth the correction over time
        _c[k] = [(np.clip(f * gi, 0, 1) * 255 + .5).astype(np.uint8) for f, gi in zip(fr, g)]   # uint8 keeps memory low
    return _c[k]
def mov_frame(spec, p):                                  # 'name:a:b' -> frames a..b stretched over the shot, blended between frames
    name, a, b = spec.split(':'); a, b = int(a), int(b); fr = mov(name)
    x = a + (b - a) * min(1, max(0, p)); i = int(math.floor(x)); f = x - i
    i = min(max(i, 0), len(fr) - 1); j = min(i + 1, len(fr) - 1)
    a = fr[i].astype(np.float32) / 255
    return a if f < 1e-3 else a * (1 - f) + fr[j].astype(np.float32) / 255 * f
def sharpen(a): return a + .45 * (a - cv2.GaussianBlur(a, (0, 0), 1.4))
def view(a, z, cx, cy):
    h, w = a.shape[:2]; s = max(W / (w / z), H / (h / z))                 # cover the frame
    hw, hh = W / (2 * s * w), H / (2 * s * h)
    cx = min(max(cx, hw), 1 - hw); cy = min(max(cy, hh), 1 - hh)
    M = np.float32([[s, 0, W / 2 - s * cx * w], [0, s, H / 2 - s * cy * h]])
    return cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
def flick(t):                                            # broken fluorescent tube: mostly on, sometimes dips
    v = 1 - .10 * (math.sin(t * 31) > .93) - .25 * (math.sin(t * 7.7 + 2) > .985) - .05 * math.sin(t * 50)
    return max(.55, v)

def picture(t):
    i = next(k for k, s in enumerate(SHOTS) if s[0] <= t < s[1]) if t < DUR else len(SHOTS) - 1
    out = shot(i, t); t0 = SHOTS[i][0]
    if i > 0 and t0 not in HARD and t - t0 < XF:        # dissolve from the previous shot (it keeps moving under the fade)
        k = ease((t - t0) / XF); out = shot(i - 1, t) * (1 - k) + out * k
    return out

def shot(i, t):
    t0, t1, src, z, c, fx = SHOTS[i]
    if src == 'black': return np.zeros((H, W, 3), np.float32)
    p = (t - t0) / (t1 - t0); e = ease(min(p, 1.0))
    a = clip_frame(src[5:], t - t0) if src.startswith('clip:') else mov_frame(src[4:], p) if src.startswith('mov:') else img(src)
    out = view(a, z[0] + (z[1] - z[0]) * e, c[0][0] + (c[1][0] - c[0][0]) * e, c[0][1] + (c[1][1] - c[0][1]) * e)
    if src.startswith('mov:'): out = sharpen(out)
    if 'flicker' in fx: out = out * flick(t)
    if 'flicker_on' in fx:                               # lights stutter back on
        k = t - t0; out = out * (0 if k < .25 else .8 if k < .4 else .1 if k < .55 else 1 if k < .7 else .3 if k < .8 else flick(t))
    if 'lights_out' in fx and t >= fx['lights_out']:
        k = t - fx['lights_out']; out = out * (.15 if k < .12 else .9 if k < .2 else .05 if k < .5 else 0)
    if 'dim' in fx: out = out * fx['dim']
    if 'flash_in' in fx and t - t0 < .5: out = np.clip(out + (1 - (t - t0) / .5) * .6, 0, 1)
    return np.clip(out, 0, 1)

# ---------------------------------------------------------------- captions + hook
f_cap = ImageFont.truetype(FONT, 62); f_hook = ImageFont.truetype(FONT, 112)
CHUNKS = []
for name, start in LINES:
    ws = [(w, start + s, start + e, name == 'w1') for w, s, e in WORDS[name]]
    i = 0
    while i < len(ws):
        n = min(3, len(ws) - i) if len(ws) - i != 4 else 2
        while n > 1 and ws[i + n - 2][0][-1:] in ',.?': n -= 1
        CHUNKS.append(ws[i:i + n]); i += n
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor((fr * 255).astype(np.uint8), cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < .1 else max(0, 1 - (t - .1) / .3) if t < .4 else ease((t - (DUR - 1.4)) / .4) if t > DUR - 1.4 else 0
    if ha > 0:
        for k, s in enumerate(HOOK):
            d.text((W // 2, 380 + k * 130), s, font=f_hook, fill=(255, 255, 255, int(255 * ha)), stroke_width=8, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    for ch in CHUNKS:
        if ch[0][1] - .05 <= t <= ch[-1][2] + .35:
            sizes = [d.textlength(w + ' ', font=f_cap) for w, *_ in ch]; x = W / 2 - sum(sizes) / 2
            for k, ((w, s, e, whisper), sz) in enumerate(zip(ch, sizes)):
                nxt = ch[k + 1][1] if k + 1 < len(ch) else e + .25
                col = (255, 255, 255)                    # plain white captions
                d.text((x, 1520), w, font=f_cap, fill=col, stroke_width=6, stroke_fill=(0, 0, 0, 230), anchor='lm'); x += sz
            break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound: train rumble, then silence in the tunnel, a buzzing tube, one peel
def mix(path):
    sr = 48000; n = int(DUR * sr); m = np.zeros(n + sr, np.float32); rng = np.random.default_rng(5)
    def load(p): return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
    def add(t, x, g): i = int(t * sr); m[i:i + len(x)] += x[:len(m) - i] * g
    def rumble(t0, t1, g, fade_out=.0):                  # low brown noise + wheel clacks every 0.9 s
        k = int((t1 - t0) * sr); x = np.cumsum(rng.standard_normal(k)).astype(np.float32); x -= np.convolve(x, np.ones(4000) / 4000, 'same'); x /= np.abs(x).max() + 1e-6
        tt = np.arange(k) / sr
        for c in np.arange(.3, t1 - t0, .9):
            i = int(c * sr); L = int(.08 * sr); x[i:i + L] += (rng.standard_normal(min(L, k - i)) * np.exp(-np.arange(min(L, k - i)) / sr * 60)) * .8
        env = np.minimum(1, tt / .5) * (np.minimum(1, (t1 - t0 - tt) / fade_out) if fade_out else 1)
        add(t0, x * env, g)
    rumble(0, 13.7, .13, fade_out=1.2)                   # the train brakes to a stop, then nothing
    k = int(4.6 * sr); tt = np.arange(k) / sr            # buzzing fluorescent tube when the lights stutter back
    buzz = (np.sign(np.sin(2 * np.pi * 100 * tt)) * .3 + np.sin(2 * np.pi * 200 * tt) * .2) * (.5 + .5 * (tt > .7))
    add(16.4, buzz * np.minimum(1, (4.6 - tt) / 1.5), .03)
    add(30.6, load(os.path.join(SFX, 'synth_paper_rustle.wav')), .35)
    rumble(52.4, DUR, .11)                               # the train moves again
    for name, start in LINES:
        if name != 'w1': add(start, load(os.path.join(VO, f'{name}.mp3')), 1.0)
    add(26.4, load(os.path.join(VO, 'w1_padded.mp3')), 1.15)
    m = m[:n]; m /= max(1.0, np.abs(m).max() / .95)
    with wave.open(path, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((m * 32767).astype('<i2').tobytes())

def frame(i): t = i / FPS; return overlay(picture(t), t)

if __name__ == '__main__':
    args = sys.argv[1:]
    if '--frames' in args:
        os.makedirs(os.path.join(HERE, 'check'), exist_ok=True)
        for i in [int(x) for x in args[args.index('--frames') + 1].split(',')]: cv2.imwrite(os.path.join(HERE, 'check', f'f{i:04d}.png'), frame(i))
        sys.exit()
    wav = os.path.join(HERE, 'mix.wav'); mix(wav); out = os.path.join(HERE, 'morning_train_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(N):
        ff.stdin.write(frame(i).tobytes())
        if i % 300 == 0: print('  frame', i, '/', N, flush=True)
    ff.stdin.close(); ff.wait(); print('saved', out)
