"""The Keeper's Rules, Part 1: finish the GPU render (silent) into the final 16:9 video: hook, captions, part card, narration, sound.
    python post.py                  reads raw.mp4 -> keeper_part1_1920x1080.mp4
    python post.py --frames 0,4300  check frames in check/"""
import os, sys, json, math, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1920, 1080, 30, 150.0
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if not os.path.exists(FONT): FONT = 'C:/Windows/Fonts/arialbd.ttf'
HOOK = ['The last keeper left me 3 rules.']
WORDS = json.load(open(os.path.join(VO, 'words.json')))
args = sys.argv[1:]
RAW = os.path.join(HERE, args[args.index('--raw') + 1] if '--raw' in args else 'raw.mp4')
OUT = 'keeper_part1_1920x1080.mp4'
CARD = [(142.2, 146.0), (147.0, 150.0)]                       # PART 2 card, around the 1 s flash of part 2

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

CHUNKS, i = [], 0
while i < len(WORDS):
    n = min(3, len(WORDS) - i) if len(WORDS) - i != 4 else 2
    for k in range(n - 1):
        if WORDS[i + k][0][-1:] in ',.?!': n = k + 1; break
    CHUNKS.append(WORDS[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 56); f_hook = ImageFont.truetype(FONT, 78); f_part = ImageFont.truetype(FONT, 150); f_sub = ImageFont.truetype(FONT, 52)
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < .12 else max(0, 1 - (t - .12) / .3) if t < .42 else 0
    if ha > 0: d.text((W // 2, 150), HOOK[0], font=f_hook, fill=(255, 255, 255, int(255 * ha)), stroke_width=7, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if .42 <= t < 141.3:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .3:
                d.text((W // 2, H - 140), ' '.join(w for w, _, _ in ch), font=f_cap, fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    for a, b in CARD:
        if a <= t < b:
            k = ease((t - a) / .6) * (1 - ease((t - (b - .4)) / .4)) if b < 149 else ease((t - a) / .4)
            d.text((W // 2, H // 2 - 50), 'PART 2', font=f_part, fill=(235, 230, 220, int(255 * k)), anchor='mm')
            d.text((W // 2, H // 2 + 80), 'THE LIGHT STOPPED', font=f_sub, fill=(200, 60, 50, int(255 * k)), anchor='mm')
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound design
SR = 48000
def load(p): return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + SR, np.float32); rng = np.random.default_rng(21)
    def add(t, x, g): i = int(t * SR); m[i:i + len(x)] += x[:len(m) - i] * g
    def tt(sec): return np.arange(int(sec * SR)) / SR
    def env(x, a, r): L = len(x); e = np.ones(L); A, R = int(a * SR), int(r * SR); e[:A] = np.linspace(0, 1, A); e[L - R:] = np.linspace(1, 0, R); return x * e
    def brown(sec): x = np.cumsum(rng.standard_normal(int(sec * SR))).astype(np.float32); x -= np.convolve(x, np.ones(3000) / 3000, 'same'); return x / (np.abs(x).max() + 1e-6)
    def white_lp(sec, k): x = rng.standard_normal(int(sec * SR)).astype(np.float32); return np.convolve(x, np.ones(k) / k, 'same')
    # the sea: slow swells of filtered noise, all the way to the black
    sec = 141.3; t = tt(sec); sw = .55 + .45 * np.sin(2 * np.pi * t / 7.3) * np.sin(2 * np.pi * t / 3.1 + 1)
    sea = white_lp(sec, 60); sea /= np.abs(sea).max(); add(0, env(sea * sw, 1.5, 1.0), .16)
    wind = brown(sec); add(0, env(wind * (.6 + .4 * np.sin(2 * np.pi * t / 11)), 2, 1), .05)
    # gulls at dusk
    for g0 in (8.4, 10.9, 13.6):
        tg = tt(.5); f = 1500 + 900 * np.sin(np.pi * tg / .5) ** 2; add(g0, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tg / .5) ** 2, .05)
    # the lamp turning: a low motor hum and a click per turn, until it stops
    t = tt(139.2 - 16.6); add(16.6, env(.5 * np.sin(2 * np.pi * 60 * t) + .3 * brown(len(t) / SR), .5, .05), .035)
    tick = load(os.path.join(SFX, 'synth_tick.wav'))
    for c in [55.9, 65.9, 71.8, 72.8, 80.0, 81.2, 82.5, 83.7]: add(c - .05, tick, .5)            # the beam lands on them
    hb = load(os.path.join(SFX, 'synth_heartbeat.wav')); t0 = 62.0
    while t0 < 89.5: add(t0, hb, .32); t0 += .95 - .45 * (t0 - 62) / 27.5
    thud = load(os.path.join(SFX, 'synth_thud.wav'))
    def sting(t0, g, base=220):
        t = tt(2.4); x = (np.sin(2 * np.pi * base * t) + np.sin(2 * np.pi * base * 1.06 * t) + np.sin(2 * np.pi * base * 1.41 * t) + 1.5 * brown(2.4)) * np.exp(-t * 1.5)
        add(t0, x, g)
    sting(85.1, .2)                                                                                 # the ninth, at the bottom of the stairs
    for k in (121.9, 122.35, 122.8, 126.1, 126.5): add(k, thud, .95)                                # the knocks
    sting(136.6, .24, 196)                                                                          # the face in the window
    add(139.2, thud, .7); t = tt(1.4); add(139.2, np.sin(2 * np.pi * np.cumsum(60 - 40 * t / t[-1]) / SR) * np.linspace(1, 0, len(t)), .08)   # the motor winds down
    t = tt(1.0); add(142.2, env(brown(1.0), .02, .8) * np.linspace(1, 0, len(t)), .2)              # card whoosh
    sting(146.0, .22, 247)                                                                          # part 2 flash
    add(0, load(os.path.join(VO, 'narration.mp3')), 1.0)
    m = m[:n]; m[int(141.3 * SR):int(142.2 * SR)] *= .0
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
    out = os.path.join(HERE, OUT)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    N = int(DUR * FPS)
    for i in range(N):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
