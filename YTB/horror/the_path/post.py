"""THE PATH : finish the render (silent) into the final reel: hook, captions, narration, the other voices, sound.
    python post.py                  reads raw.mp4 -> the_path_1080x1920.mp4
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)"""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1080, 1920, 30, 178.1
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_I = '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'
if not os.path.exists(FONT_I): FONT_I = FONT
if not os.path.exists(FONT): FONT = FONT_I = 'C:/Windows/Fonts/arialbd.ttf'
WORDS = json.load(open(os.path.join(VO, 'words.json'))); LAY = {l['name']: l for l in json.load(open(os.path.join(VO, 'layout.json')))}
args = sys.argv[1:]
RAW = os.path.join(HERE, args[args.index('--raw') + 1] if '--raw' in args else 'raw.mp4')
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

# ---------------------------------------------------------------- captions: short chunks, never across a sentence or a speaker
CHUNKS, i = [], 0
while i < len(WORDS):
    n = min(3, len(WORDS) - i) if len(WORDS) - i != 4 else 2
    for k in range(n - 1):
        if WORDS[i + k][0][-1:] in ',.?!' or WORDS[i + k][3] != WORDS[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(WORDS[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 66); f_oth = ImageFont.truetype(FONT_I, 66); f_hook = ImageFont.truetype(FONT, 74)
HOOK = ['I WALKED MY WHOLE', 'VILLAGE TO THE', 'MOUNTAIN.', 'I GOT THERE ALONE.']
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < 4.9 else max(0, 1 - (t - 4.9) / .35) if t < 5.25 else ease((t - (DUR - .55)) / .2) if t > DUR - .55 else 0
    if ha > 0:
        for k, line in enumerate(HOOK):
            col = (255, 214, 90) if k == 3 else (255, 255, 255)
            d.text((W // 2, 220 + k * 92), line, font=f_hook, fill=col + (int(255 * ha),), stroke_width=9, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if 5.25 <= t < DUR - .6:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .3:
                oth = ch[0][3]; s = ' '.join(w for w, _, _, _ in ch)
                d.text((W // 2, 1480), s, font=f_oth if oth else f_cap, fill=(255, 205, 220) if oth else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound
SR = 48000
def load(p, extra=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', p] + (['-af', extra] if extra else []) + ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).copy()
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + 4 * SR, np.float32); rng = np.random.default_rng(23)
    def add(t, x, g): i = int(t * SR); m[i:i + len(x)] += x[:max(0, len(m) - i)] * g
    def tt(sec): return np.arange(int(sec * SR)) / SR
    def band(x, lo, hi):
        X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x)).astype(np.float32)
    def brown(sec):
        x = np.cumsum(rng.standard_normal(int(sec * SR))).astype(np.float32); x -= np.convolve(x, np.ones(3000) / 3000, 'same'); return x / (np.abs(x).max() + 1e-6)
    def verb(x, amt=.3, dec=.35):
        ir = rng.standard_normal(int(dec * SR)).astype(np.float32) * np.exp(-tt(dec) * 6 / dec); ir /= np.abs(ir).sum() / 8
        return (x + amt * np.convolve(x, ir)[:len(x)]).astype(np.float32)
    def env(sec, a, r):
        e = np.ones(int(sec * SR), np.float32); ai, ri = int(a * SR), int(r * SR)
        e[:ai] = np.linspace(0, 1, ai); e[-ri:] = np.linspace(1, 0, ri); return e
    # wind outside (everywhere outdoors), a quieter room tone inside
    wind = band(rng.standard_normal(n).astype(np.float32), 150, 900); wind /= np.abs(wind).max()
    w_env = .09 + .05 * np.sin(np.arange(n) / SR * .37) + .03 * np.sin(np.arange(n) / SR * 1.3)
    inside = [(26.0, 51.5)]
    for a, b in inside: w_env[int(a * SR):int(b * SR)] *= .25
    w_env[int(172.3 * SR):int(175.1 * SR)] *= 1.6                         # the silence before the tug: only the wind
    m[:n] += wind * w_env.astype(np.float32) * .5
    add(0, (brown(DUR) * .5).astype(np.float32), .03)
    # the monsters' breathing: slow, wet, low (a growl of filtered noise on an in-out envelope)
    def breath(sec, rate=.55, lo=70, hi=520, rough=1.0):
        x = band(rng.standard_normal(int(sec * SR)).astype(np.float32), lo, hi)
        t = tt(sec); e = np.maximum(0, np.sin(2 * np.pi * rate * t)) ** 1.5 + .45 * np.maximum(0, -np.sin(2 * np.pi * rate * t)) ** 2
        g = 1 + rough * .6 * np.sin(2 * np.pi * 31 * t) * (rng.random(len(t)) > .3)
        y = x * e * g; return (y / (np.abs(y).max() + 1e-6)).astype(np.float32)
    for a, b, g in [(10.0, 15.1, .10), (15.1, 19.85, .32), (23.5, 26.0, .08), (51.5, 53.3, .14), (53.3, 60.2, .42), (60.2, 62.6, .16),
                    (140.75, 145.7, .26), (145.7, 151.5, .16), (151.5, 158.1, .12), (160.8, 166.1, .18), (166.1, 172.3, .14), (175.1, 177.1, .06)]:
        add(a, breath(b - a) * env(b - a, .3, .4), g)
    # Mr. Hamid: his door, then a scream far away, cut short
    t = tt(.9); f = 260 + 70 * np.sin(t * 6); cr = np.sin(2 * np.pi * np.cumsum(f) / SR) * (rng.random(len(t)) > .45) * np.sin(np.pi * t / t[-1])
    add(20.2, cr.astype(np.float32), .05); add(52.15, cr.astype(np.float32), .07)
    t = tt(.95); f0 = 330 - 120 * t + 12 * np.sin(2 * np.pi * 6 * t); ph = 2 * np.pi * np.cumsum(f0) / SR
    saw = sum(np.sin(ph * k) / k for k in range(1, 18)).astype(np.float32) + .3 * rng.standard_normal(len(t)).astype(np.float32)
    voice = band(saw, 600, 1000) * 1.0 + band(saw, 1100, 1400) * .7 + band(saw, 2300, 2800) * .3
    voice *= np.minimum(1, t / .05) * np.where(t > .82, np.maximum(0, 1 - (t - .82) / .03), 1)
    add(22.45, verb(band(voice / np.abs(voice).max(), 200, 3500), .6, .8), .22)
    thud = load(os.path.join(SFX, 'synth_thud.wav')); add(23.3, thud, .25)
    # the bracelet: three little bells on a cord
    def bell(g=1.0):
        t = tt(.6); y = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) * a for f, d, a in [(3520, 9, 1), (5280, 14, .5), (7040, 20, .3), (4410, 11, .4)])
        return (y * g * (.7 + .6 * rng.random())).astype(np.float32)
    knock = band(rng.standard_normal(int(.08 * SR)).astype(np.float32), 120, 900) * np.exp(-tt(.08) * 60)
    for k in np.arange(39.4, 41.9, .55): add(k, knock, .25); add(k + .005, bell(), .05)            # tapping on the bed frame
    # Haru's footsteps on the path; the line's footsteps, thinning on the words
    def step(g=1.0, bright=1.0):
        x = band(rng.standard_normal(int(.12 * SR)).astype(np.float32), 120, 1800 * bright) * np.exp(-tt(.12) * 35); return x * g
    COUNT = [(0, 41), (151.78, 20), (152.84, 10), (153.56, 4), (155.33, 2), (159.73, 1), (166.1, 1), (172.3, 0)]
    def count(t): c = 41; [c := v for tt_, v in COUNT if t >= tt_]; return c
    for a, b in [(118.8, 124.55), (132.5, 172.3)]:
        k = a
        while k < b:
            c = count(k)
            if c > 0:
                add(k, step(.18), 1.0)                                                                  # Haru
                if c > 1:
                    for j in range(min(c - 1, 14)): add(k + .07 + rng.random() * .5, step(.12 * (1 if c < 6 else .7)), 1.0)
                    if t_in := (k < 159.73): add(k + .02, bell(.03), 1.0)                               # the bracelet with every step
            k += .58
    add(TUG := 174.1, bell(.09), 1.0)                                                                  # one clink, with the tug
    add(TUG - .02, band(rng.standard_normal(int(.15 * SR)).astype(np.float32), 200, 2000) * np.exp(-tt(.15) * 25), .12)
    # knocking before sunrise
    for k in [86.5, 86.8, 87.1, 88.4, 88.65]: add(k, knock, .35)
    # heartbeat while it smells her hair; a low swell under the reveal and the end
    hb = load(os.path.join(SFX, 'synth_heartbeat.wav')); k = 53.6
    while k < 60.2: add(k, hb, .35); k += .72
    def drone(sec): t = tt(sec); return ((np.sin(2 * np.pi * 49 * t) + .5 * np.sin(2 * np.pi * 73.4 * t) + .3 * brown(sec)) * np.minimum(1, t / 3) * np.minimum(1, (sec - t) / .5)).astype(np.float32)
    add(124.55, drone(7.9), .05); add(158.1, drone(14.2), .07); add(175.1, drone(2.0), .06)
    # voices
    for name, l in LAY.items():
        x = load(os.path.join(VO, 'c', name + '.wav'))
        if name[0] == 's': x = verb(x, .15, .3)
        if name == 's4': x = verb(band(x, 150, 7000), .35, .9)                                        # behind her, very close, not quite right
        if name == 'a1': x = verb(x, .2, .3)
        add(l['offset'], x, 1.0 if name[0] == 'n' else 1.35)
    m = m[:n]
    m[int(176.95 * SR):int(177.4 * SR)] *= np.linspace(1, 0, int(177.4 * SR) - int(176.95 * SR)) ** 2
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
    if '--mix' in args: sys.exit()
    meas = json.loads(subprocess.run(['ffmpeg', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                                     capture_output=True, text=True).stderr.split('[Parsed_loudnorm')[-1].split('\n', 1)[1])
    LN = ('loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s'
          % (meas['input_i'], meas['input_tp'], meas['input_lra'], meas['input_thresh'], meas['target_offset']))
    out = os.path.join(HERE, 'the_path_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
