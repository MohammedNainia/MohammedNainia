"""Sleep paralysis reel (9:16) from the AI stills + Samara voice lines.
    python reel.py             -> sleep_paralysis_1080x1920.mp4
    python reel.py --frames 0,90,300   -> check frames in check/
Question: is it better to know a truth that terrifies you, or to stay safe not knowing?"""
import os, sys, json, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.join(HERE, 'stills'); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS = 1080, 1920, 30
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
GOLD = (255, 200, 95)

# voice lines: (file, start second)
LINES = [(1, .45), (2, 5.95), (3, 11.4), (4, 15.9), (5, 21.0), (6, 24.7), (7, 30.0)]
DUR = 35.0; N = int(DUR * FPS)
WORDS = json.load(open(os.path.join(VO, 'words.json')))
HOOK = ['Know it,', 'or sleep?']

# shots: start, end, still, zoom from->to, centre from->to, effects
SHOTS = [
    (0.0, 5.7, 'h1_face_dots.png', (1.00, 1.10), ((.5, .48), (.5, .47)), {}),
    (5.7, 11.2, 'd1_hand.png', (1.00, 1.06), ((.5, .5), (.5, .52)), {'twitch': (.40, .40)}),
    (11.2, 15.95, 'pov_b.png', (1.00, 1.05), ((.5, .45), (.5, .40)), {}),
    (15.95, 16.7, 'pov_b.png', (1.05, 1.055), ((.5, .40), (.5, .40)), {'close': 1}),          # she closes her eyes
    (16.7, 20.9, 'e1_pov_empty.png', (1.055, 1.07), ((.5, .40), (.5, .40)), {'open': 1}),    # ...and it is gone
    (20.9, 24.6, 'pov_b.png', (1.07, 1.16), ((.5, .40), (.5, .30)), {}),                   # it was never gone
    (24.6, 29.9, 'f1_visitor_close.png', (1.00, 1.14), ((.5, .5), (.5, .55)), {'drool': (.53, .80)}),
    (29.9, 33.2, 'v7_master.png', (1.00, 1.04), ((.5, .5), (.45, .5)), {}),                # the twist: two of them
    (33.2, DUR, 'h1_face_dots.png', (1.03, 1.00), ((.5, .475), (.5, .48)), {}),             # settles back onto frame 0 (loop)             # loop back to frame 0
]

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
_c = {}
def img(n):
    if n not in _c: _c[n] = cv2.imread(os.path.join(ST, n)).astype(np.float32) / 255
    return _c[n]
def blob(a, cx, cy, sx, sy):
    h, w = a.shape[:2]; X, Y = np.meshgrid(np.arange(w) / w, np.arange(h) / h)
    return np.exp(-(((X - cx) / sx) ** 2 + ((Y - cy) / sy) ** 2)).astype(np.float32)
def warp(a, wt, dx, dy):
    h, w = a.shape[:2]; X, Y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    return cv2.remap(a, X - dx * wt, Y - dy * wt, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
def view(a, z, cx, cy):
    h, w = a.shape[:2]; s = W / (w / z)
    hw, hh = .5 / z, .5 * (H / W) * (w / h) / z
    cx = min(max(cx, hw), 1 - hw); cy = min(max(cy, hh), 1 - hh)
    M = np.float32([[s, 0, W / 2 - s * cx * w], [0, s, H / 2 - s * cy * h]])
    return cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
def warm_flicker(a, t, n):
    k = n + ':m'
    if k not in _c:
        b, g, r = a[..., 0], a[..., 1], a[..., 2]
        _c[k] = cv2.GaussianBlur(np.clip((r - b) * 3, 0, 1) * np.clip((r + g) * .8, 0, 1), (0, 0), 25)[..., None]
    return a * (1 + _c[k] * .05 * (math.sin(t * 7.3) * .5 + math.sin(t * 13.1 + 1) * .3 + math.sin(t * 2.9) * .2))

def picture(t):
    for t0, t1, n, z, c, fx in SHOTS:
        if t0 <= t < t1: break
    p = (t - t0) / (t1 - t0); e = ease(p); a = warm_flicker(img(n), t, n)
    if 'twitch' in fx:                                   # fingers strain: tiny pulls, never smooth
        k = n + ':tw'
        if k not in _c: _c[k] = blob(a, *fx['twitch'], .12, .1)
        tw = max(0, math.sin(t * 9)) ** 8 * 6 + max(0, math.sin(t * 5.3 + 1)) ** 10 * 4
        a = warp(a, _c[k], tw * .6, -tw)
    if 'drool' in fx:
        k = n + ':dr'
        if k not in _c: _c[k] = blob(a, *fx['drool'], .03, .09)
        a = warp(a, _c[k], 0, 30 * ease(p * 1.1))
    out = view(a, z[0] + (z[1] - z[0]) * e, c[0][0] + (c[1][0] - c[0][0]) * e, c[0][1] + (c[1][1] - c[0][1]) * e)
    if 'close' in fx: out *= 1 - ease(p / .8)            # eyelids: the frame goes dark
    if 'open' in fx: out *= ease(p / .35)                # ...and opens on an empty room
    return np.clip(out, 0, 1)

# ---------------------------------------------------------------- text: hook (frame 0 + loop end) and word captions
f_cap = ImageFont.truetype(FONT, 62); f_hook = ImageFont.truetype(FONT, 118)
def draw_text(d, xy, s, f, fill, stroke=6):
    d.text(xy, s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 230), anchor='mm')
CHUNKS = []                                              # 2-4 word chunks with per-word timing
for li, start in LINES:
    ws = [(w, start + s, start + e) for w, s, e in WORDS[str(li)]]
    i = 0
    while i < len(ws):
        n = 3 if len(ws) - i > 4 else len(ws) - i if len(ws) - i <= 4 else 3
        chunk = ws[i:i + n]
        while n > 2 and chunk[-2][0][-1:] in ',.?' : n -= 1; chunk = ws[i:i + n]
        CHUNKS.append(chunk); i += n
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor((fr * 255).astype(np.uint8), cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    hook_a = 1.0 if t < .1 else max(0, 1 - (t - .1) / .3) if t < .4 else ease((t - (DUR - 1.6)) / .4) if t > DUR - 1.6 else 0
    if hook_a > 0:
        for k, s in enumerate(HOOK): draw_text(d, (W // 2, 360 + k * 135), s, f_hook, (255, 255, 255, int(255 * hook_a)), 8)
    cap_y = 1500
    for ch in CHUNKS:
        if ch[0][1] - .05 <= t <= ch[-1][2] + .35:
            words = [w for w, _, _ in ch]; sizes = [d.textlength(w + ' ', font=f_cap) for w in words]
            x = W / 2 - sum(sizes) / 2
            for k, ((w, s, e), sz) in enumerate(zip(ch, sizes)):
                nxt = ch[k + 1][1] if k + 1 < len(ch) else e + .25          # one gold word at a time
                col = GOLD if s - .03 <= t < nxt - .03 else (255, 255, 255)
                d.text((x, cap_y), w, font=f_cap, fill=col, stroke_width=6, stroke_fill=(0, 0, 0, 230), anchor='lm'); x += sz
            break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound: voice + slow heartbeat (stops when she closes her eyes) + one rustle
def mix(path):
    sr = 48000; mixb = np.zeros(int(DUR * sr) + sr, np.float32)
    def load(p):
        return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
    def add(t, x, g): i = int(t * sr); mixb[i:i + len(x)] += x[:len(mixb) - i] * g
    for li, start in LINES: add(start, load(os.path.join(VO, f'line{li}.mp3')), 1.0)
    hb = load(os.path.join(SFX, 'synth_heartbeat.wav'))
    t = 5.8
    while t < 15.9: add(t, hb, .22 + .12 * (t - 5.8) / 10); t += 1.05 - .25 * (t - 5.8) / 10   # it speeds up
    add(21.0, hb, .35); add(21.75, hb, .38)                                                    # one more beat when it is back
    add(24.4, load(os.path.join(SFX, 'synth_paper_rustle.wav')), .25)
    mixb = mixb[:int(DUR * sr)]; mixb /= max(1.0, np.abs(mixb).max() / .95)
    pcm = (mixb * 32767).astype('<i2')
    import wave
    with wave.open(path, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

def frame(i):
    t = i / FPS; return overlay(picture(t), t)

if __name__ == '__main__':
    args = sys.argv[1:]
    if '--frames' in args:
        os.makedirs(os.path.join(HERE, 'check'), exist_ok=True)
        for i in [int(x) for x in args[args.index('--frames') + 1].split(',')]: cv2.imwrite(os.path.join(HERE, 'check', f'f{i:04d}.png'), frame(i))
        sys.exit()
    wav = os.path.join(HERE, 'mix.wav'); mix(wav); out = os.path.join(HERE, 'sleep_paralysis_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(N):
        ff.stdin.write(frame(i).tobytes())
        if i % 150 == 0: print('  frame', i, '/', N, flush=True)
    ff.stdin.close(); ff.wait(); print('saved', out)
