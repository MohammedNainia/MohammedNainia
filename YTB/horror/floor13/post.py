"""Floor 13: finish the GPU render (silent) into the final reel: hook, white word captions, narration and sound design.
    python post.py                         reads floor13_raw.mp4 -> floor13_1080x1920.mp4
    python post.py --raw other.mp4         a different silent render
    python post.py --frames 0,300          caption check frames in check/ (no audio)"""
import os, sys, json, math, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1080, 1920, 30, 52.5
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if not os.path.exists(FONT): FONT = 'C:/Windows/Fonts/arialbd.ttf'
HOOK = ['My building has', 'no 13th floor.']
WORDS = json.load(open(os.path.join(VO, 'words.json')))
args = sys.argv[1:]
RAW = os.path.join(HERE, args[args.index('--raw') + 1] if '--raw' in args else 'floor13_raw.mp4')

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

# ---------------------------------------------------------------- captions: up to 3 words, never across a sentence or comma
CHUNKS, i = [], 0
while i < len(WORDS):
    n = min(3, len(WORDS) - i) if len(WORDS) - i != 4 else 2
    for k in range(n - 1):
        if WORDS[i + k][0][-1:] in ',.?!': n = k + 1; break
    CHUNKS.append(WORDS[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 66); f_hook = ImageFont.truetype(FONT, 104)
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < .12 else max(0, 1 - (t - .12) / .3) if t < .42 else ease((t - 51.95) / .25) if t > 51.95 else 0
    if ha > 0:
        for k, s in enumerate(HOOK):
            d.text((W // 2, 360 + k * 125), s, font=f_hook, fill=(255, 255, 255, int(255 * ha)), stroke_width=8, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if .42 <= t < 51.3:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .3:
                d.text((W // 2, 1500), ' '.join(w for w, _, _ in ch), font=f_cap, fill=(255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound design
SR = 48000
def load(p): return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + SR, np.float32); rng = np.random.default_rng(13)
    def add(t, x, g): i = int(t * SR); m[i:i + len(x)] += x[:len(m) - i] * g
    def tt(sec): return np.arange(int(sec * SR)) / SR
    def env(x, a, r): L = len(x); e = np.ones(L); A, R = int(a * SR), int(r * SR); e[:A] = np.linspace(0, 1, A); e[L - R:] = np.linspace(1, 0, R); return x * e
    def brown(sec): x = np.cumsum(rng.standard_normal(int(sec * SR))).astype(np.float32); x -= np.convolve(x, np.ones(3000) / 3000, 'same'); return x / (np.abs(x).max() + 1e-6)
    # elevator hum: low mains tone + motor rumble, while we are in the cab
    for a, b in [(0, 13), (19.9, 24), (36.3, 51.25)]:
        t = tt(b - a); add(a, env(.5 * np.sin(2 * np.pi * 50 * t) + .25 * np.sin(2 * np.pi * 100 * t) + .6 * brown(b - a), .3, .2), .05)
    add(4.74, load(os.path.join(SFX, 'synth_thud.wav')), .6)                                  # the cab jolts to a stop
    t = tt(1.6); ding = (np.sin(2 * np.pi * 1318 * t) + .6 * np.sin(2 * np.pi * 1975 * t)) * np.exp(-t * 3)
    add(6.84, ding, .18)                                                                       # 13
    for a in (10.9, 36.5):                                                                     # doors slide
        t = tt(1.0 if a < 20 else .35); add(a, env(brown(len(t) / SR) * (1 + .3 * np.sin(2 * np.pi * 7 * t)), .05, .15), .25)
    add(36.82, load(os.path.join(SFX, 'synth_thud.wav')), .9)                                 # slam
    # hallway: buzzing tube while the doors are open
    t = tt(36.5 - 11.5); buzz = (np.sign(np.sin(2 * np.pi * 120 * t)) * .3 + np.sin(2 * np.pi * 240 * t) * .2)
    add(11.5, env(buzz, .5, .2), .018)
    rus = load(os.path.join(SFX, 'synth_paper_rustle.wav'))
    add(28.6, rus, .5); add(29.3, rus, .4)                                                     # its head turns
    for a, b in [(32.85, 33.15), (33.95, 34.25), (34.85, 35.12)]: add(b, rus, .7)             # each time it is closer
    hb = load(os.path.join(SFX, 'synth_heartbeat.wav')); t0 = 19.9
    while t0 < 26.3: add(t0, hb, .35); t0 += .62 - .2 * (t0 - 19.9) / 6.4                    # hammering the button
    # drone rising from the drop to the mirror, then the sting, then silence
    t = tt(51.25 - 40.6); f = 55 + 25 * (t / t[-1]) ** 2
    drone = np.sin(2 * np.pi * np.cumsum(f) / SR) + .5 * np.sin(2 * np.pi * np.cumsum(f * 1.06) / SR) + .3 * brown(len(t) / SR)
    add(40.6, drone * np.linspace(.2, 1, len(t)), .12)
    t = tt(2.2); sting = (np.sin(2 * np.pi * 220 * t) + np.sin(2 * np.pi * 233 * t) + np.sin(2 * np.pi * 311 * t) + 1.5 * brown(2.2)) * np.exp(-t * 1.6)
    add(49.35, sting, .22)
    add(0, load(os.path.join(VO, 'narration.mp3')), 1.0)
    m = m[:n]; m[int(51.25 * SR):] *= np.linspace(1, 0, n - int(51.25 * SR)) ** 8          # dead silence on the black
    m /= max(1.0, np.abs(m).max() / .95)
    with wave.open(path, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((m * 32767).astype('<i2').tobytes())

if __name__ == '__main__':
    cap = cv2.VideoCapture(RAW)
    if '--frames' in args:
        os.makedirs(os.path.join(HERE, 'check'), exist_ok=True)
        for i in [int(x) for x in args[args.index('--frames') + 1].split(',')]:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i); ok, fr = cap.read()
            if not ok: fr = np.zeros((H, W, 3), np.uint8)
            cv2.imwrite(os.path.join(HERE, 'check', f'c{i:04d}.png'), overlay(fr, i / FPS))
        sys.exit()
    wav = os.path.join(HERE, 'mix.wav'); mix(wav)
    meas = json.loads(subprocess.run(['ffmpeg', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                                     capture_output=True, text=True).stderr.split('[Parsed_loudnorm')[-1].split('\n', 1)[1])
    LN = ('loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s'
          % (meas['input_i'], meas['input_tp'], meas['input_lra'], meas['input_thresh'], meas['target_offset']))
    out = os.path.join(HERE, 'floor13_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    N = int(DUR * FPS)
    for i in range(N):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
