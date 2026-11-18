"""BLACK SKY : finish the render (silent) into the final reel: hook, captions, narration, the other voices, sound.
    python post.py                  reads raw.mp4 -> black_sky_1080x1920.mp4
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)"""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1080, 1920, 30, 177.7
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
HOOK = ['EVERYONE FORGOT', 'THE SUN.', 'I REMEMBERED.', 'BIG MISTAKE.']
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
    n = int(DUR * SR); m = np.zeros(n + 4 * SR, np.float32); rng = np.random.default_rng(29)
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
        e = np.ones(int(sec * SR), np.float32); ai, ri = int(a * SR), int(r * SR); e[:ai] = np.linspace(0, 1, ai); e[-ri:] = np.linspace(1, 0, ri); return e
    INSIDE = [(5.4, 12.4), (17.3, 29.2), (37.6, 43.2), (86.5, 91.8), (104.5, 126.7), (130.5, 140.7), (148.7, 159.0)]
    # the town: no birds, no wind, just a low electrical hum from the streetlamps and a room tone indoors
    t = tt(DUR); hum = (np.sin(2 * np.pi * 50 * t) * .4 + np.sin(2 * np.pi * 100 * t) * .2).astype(np.float32)
    he = np.full(n, .02, np.float32)
    for a, b in INSIDE: he[int(a * SR):int(b * SR)] = .006
    m[:n] += hum * he
    add(0, (brown(DUR) * .5).astype(np.float32), .025)
    # "it": a huge, slow groan above the roofs, like something heavy turning over
    def groan(sec, f0=38):
        t = tt(sec); f = f0 + 6 * np.sin(2 * np.pi * .3 * t); ph = 2 * np.pi * np.cumsum(f) / SR
        x = np.sin(ph) + .5 * np.sin(ph * 1.5 + .3) + .35 * band(rng.standard_normal(len(t)).astype(np.float32), 30, 300) * 3
        x *= np.sin(np.pi * t / sec) ** 1.5; return (x / np.abs(x).max()).astype(np.float32)
    for a, sec, g in [(62.0, 7.0, .22), (127.0, 4.2, .24), (164.4, 6.0, .2), (100.0, 5.0, .15), (175.0, 2.6, .2)]: add(a, groan(sec), g)
    # the cup breaks
    t = tt(.5); crash = band(rng.standard_normal(len(t)).astype(np.float32), 1500, 9000) * np.exp(-t * 14)
    for k in range(5): add(23.75 + k * .04, (np.sin(2 * np.pi * (2400 + k * 700) * t) * np.exp(-t * 20)).astype(np.float32), .08)
    add(23.75, crash, .35)
    # chalk on the wall
    for k in np.arange(55.8, 59.6, .45): x = band(rng.standard_normal(int(.35 * SR)).astype(np.float32), 2000, 7000) * np.sin(np.pi * tt(.35) / .35); add(k, x, .06)
    # knocking, a door
    knock = band(rng.standard_normal(int(.08 * SR)).astype(np.float32), 120, 900) * np.exp(-tt(.08) * 60)
    for k in [80.7, 81.0, 81.3]: add(k, knock, .4)
    t = tt(.9); f = 260 + 70 * np.sin(t * 6); cr = np.sin(2 * np.pi * np.cumsum(f) / SR) * (rng.random(len(t)) > .45) * np.sin(np.pi * t / t[-1])
    add(83.0, cr.astype(np.float32), .05); add(159.2, cr.astype(np.float32), .05)
    # footsteps in the street when people pass
    def step(g): return band(rng.standard_normal(int(.1 * SR)).astype(np.float32), 120, 1600) * np.exp(-tt(.1) * 40) * g
    for a, b, gap in [(12.4, 17.3, .27), (33.1, 37.6, .3), (43.2, 49.7, .3), (159.6, 163.8, .55), (174.5, 177.0, .5)]:
        k = a
        while k < b: add(k + rng.random() * .05, step(.12), 1.0); k += gap
    # doors and curtains when the street wakes to her scream
    for k in np.arange(166.0, 167.4, .23): add(k, cr[:int(.4 * SR)].astype(np.float32), .03)
    # the darkness coming down: a rushing, swallowing sound, then nothing
    t = tt(1.5); rush = band(rng.standard_normal(len(t)).astype(np.float32), 60, 2500) * (t / 1.5) ** 2
    add(168.8, rush / np.abs(rush).max(), .5)
    add(170.15, groan(.9, 28) * 1.0, .6)
    def drone(sec): t = tt(sec); return ((np.sin(2 * np.pi * 49 * t) + .5 * np.sin(2 * np.pi * 73.4 * t) + .3 * brown(sec)) * np.minimum(1, t / 3) * np.minimum(1, (sec - t) / .5)).astype(np.float32)
    add(69.0, drone(11), .05); add(130.5, drone(10), .06); add(171.0, drone(6.7), .06)
    # voices
    for name, l in LAY.items():
        x = load(os.path.join(VO, 'c', name + '.wav'))
        if name[0] != 'n': x = verb(x, .15, .3)
        if name == 'n33': x = verb(x, .5, 1.2); x[-int(.03 * SR):] *= np.linspace(1, 0, int(.03 * SR))   # the scream, cut off
        add(l['offset'], x, 1.0 if name[0] == 'n' else 1.3)
    m = m[:n]
    m[int(170.2 * SR):int(171.0 * SR)] *= .15                        # the beat of total black
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
    out = os.path.join(HERE, 'black_sky_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
