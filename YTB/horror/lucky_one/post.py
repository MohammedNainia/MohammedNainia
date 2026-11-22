"""THE LUCKY ONE: finish the render (silent) into the final reel: hook, captions, voices, sound.
    python post.py                  reads raw.mp4 -> lucky_one_1080x1920.mp4
    python post.py --raw FILE       another silent render
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)
Voices are the 1.5x .wav files in voice/ (the woman is warmed here; the thing's line is made in voice/: t01.wav)."""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
LAYL = json.load(open(os.path.join(VO, 'layout.json'))); LAY = {l['name']: l for l in LAYL}
W, H, FPS, DUR = 1080, 1920, 30, LAY['END']['start']
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_I = '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'
if not os.path.exists(FONT_I): FONT_I = FONT
if not os.path.exists(FONT): FONT = FONT_I = 'C:/Windows/Fonts/arialbd.ttf'
WORDS = json.load(open(os.path.join(VO, 'words.json')))
S = lambda n: LAY[n]['start']; E = lambda n: LAY[n]['end']
args = sys.argv[1:]
RAW = os.path.join(HERE, args[args.index('--raw') + 1] if '--raw' in args else 'raw.mp4')

# ---------------------------------------------------------------- captions: short chunks, never across a sentence or a speaker
HOOK_END = next(w[2] for w in WORDS if w[0] == 'one.') + .25          # the hook is the first line, spoken and shown at once
CAPW = [w for w in WORDS if w[1] >= HOOK_END - .2]
CHUNKS, i = [], 0
while i < len(CAPW):
    n = min(3, len(CAPW) - i) if len(CAPW) - i != 4 else 2
    for k in range(n - 1):
        if CAPW[i + k][0][-1:] in ',.?!:' or CAPW[i + k][3] != CAPW[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(CAPW[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 66); f_oth = ImageFont.truetype(FONT_I, 66); f_hook = ImageFont.truetype(FONT, 64); f_small = ImageFont.truetype(FONT_I, 46)
HOOK = ["MY LUCK TOOK THREE", "OF MY CHILDREN.", "TONIGHT IT'S COMING", "FOR THE LAST ONE."]
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < HOOK_END else max(0, 1 - (t - HOOK_END) / .3)
    if ha > 0:
        for k, line in enumerate(HOOK):
            col = (255, 214, 90) if k >= 2 else (255, 255, 255)
            d.text((W // 2, 300 + k * 96), line, font=f_hook, fill=col + (int(255 * ha),), stroke_width=9, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if HOOK_END <= t < DUR - .2:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .25:
                oth = ch[0][3]; s = ' '.join(w for w, _, _, _ in ch)
                if S('t01') - .1 <= t <= E('t01') + .3:
                    d.text((W // 2, 1530), '(give it back.)', font=f_small, fill=(255, 205, 220, 220), stroke_width=5, stroke_fill=(0, 0, 0, 220), anchor='mm')
                d.text((W // 2, 1440), s, font=f_oth if oth else f_cap, fill=(255, 205, 220) if oth else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound
SR = 48000
def load(p, extra=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', p] + (['-af', extra] if extra else []) + ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).copy()
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + 4 * SR, np.float32); rng = np.random.default_rng(16)
    def add(t, x, g): i = int(t * SR); m[i:i + len(x)] += x[:max(0, len(m) - i)] * g
    def tt(sec): return np.arange(int(sec * SR)) / SR
    def band(x, lo, hi):
        X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x)).astype(np.float32)
    def noise(sec): return rng.standard_normal(int(sec * SR)).astype(np.float32)
    def norm(x): return (x / (np.abs(x).max() + 1e-6)).astype(np.float32)
    def brown(sec):
        x = np.cumsum(noise(sec)).astype(np.float32); x -= np.convolve(x, np.ones(3000) / 3000, 'same'); return norm(x)
    def verb(x, amt=.3, dec=.35):
        ir = noise(dec) * np.exp(-tt(dec) * 6 / dec); ir /= np.abs(ir).sum() / 8
        out = amt * np.convolve(x, ir); out[:len(x)] += x; return out.astype(np.float32)
    def seg(a, b, x, g):
        L = int((b - a) * SR); y = np.resize(x, L).astype(np.float32); fe = min(L // 3, int(.2 * SR)); y[:fe] *= np.linspace(0, 1, fe); y[-fe:] *= np.linspace(1, 0, fe); add(a, y, g)
    def hit(sec=.6, lo=30, hi=250, d=7): return norm(band(noise(sec), lo, hi) * np.exp(-tt(sec) * d))
    def snap(): return norm(band(noise(.12), 300, 3000) * np.exp(-tt(.12) * 25))
    def step(): return norm(band(noise(.09), 60, 900) * np.exp(-tt(.09) * 45))
    def glass(): return norm(sum(np.sin(2 * np.pi * f * tt(.6)) * np.exp(-tt(.6) * (8 + 6 * rng.random())) for f in rng.uniform(2500, 7000, 9)) + 2 * band(noise(.6), 3000, 9000) * np.exp(-tt(.6) * 12))
    def engine(sec, f0=38, rev=0):
        t = tt(sec); f = f0 * (1 + rev * t / sec); return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + .5 * np.sin(2 * np.pi * 7 * t)) + .4 * band(noise(sec), 60, 500))
    def whoosh(sec=1.2): return norm(band(noise(sec), 150, 4000) * np.sin(np.pi * tt(sec) / sec) ** 3)
    def screech(sec=1.0): t = tt(sec); return norm(np.sin(2 * np.pi * np.cumsum(1900 + 300 * np.sin(t * 30)) / SR) * np.sin(np.pi * t / sec) + .3 * band(noise(sec), 2000, 6000))
    def bell(f=440, sec=3.0): t = tt(sec); return norm(sum(np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, d in [(1, 1.2), (2.4, 2), (3.9, 3), (5.4, 4)]))
    rain = lambda sec: band(noise(sec), 800, 9000) * .6 + band(brown(sec), 60, 600) * .4
    h02 = S('h02') - .3; h03 = S('h03') - .3; w01 = S('w01') - .4; h04 = S('h04') - .3; h05 = S('h05') - .3; h06 = S('h06') - .3; h07 = S('h07') - .3
    h08 = S('h08') - .4; h09 = S('h09') - .6; h10 = S('h10') - .4; w02 = S('w02') - .4; h11 = S('h11') - .5; h12 = S('h12') - .4; h13 = S('h13') - .4; t01 = S('t01') - .2
    # HOOK: feet hammering down the stairs, the lamp dropping and bursting behind them
    for k in np.arange(0, h02, .2): add(k, step(), .3)
    add(2.4, glass(), .35); add(2.4, hit(.5, 60, 600, 10), .3); add(0, norm(band(noise(h02), 40, 300)), .06)
    # sixteen: rain, the bus pulling away, the slip, the car through the puddle
    seg(h02, h04, rain(12), .07)
    add(h02, engine(1.6, 45, .6) * np.linspace(1, 0, int(1.6 * SR)), .18)
    add(h02 + 1.5, hit(.4, 60, 500, 12), .4)
    add(h02 + 2.1, whoosh(1.0), .25); add(h02 + 2.45, norm(band(noise(.7), 300, 5000) * np.exp(-tt(.7) * 5)), .35)
    # the car runs the light: horn, tyres; she is yanked back
    L = 1.4; add(h03 + .4, norm(np.sin(2 * np.pi * 415 * tt(L)) + .6 * np.sin(2 * np.pi * 520 * tt(L))) * np.linspace(1, .6, int(L * SR)), .12)
    add(h03 + .6, screech(1.2), .12); add(h03 + 1.25, whoosh(.9), .3); add(h03 + 1.3, hit(.3, 200, 2000, 20), .2)
    # under her umbrella: the rain dulls; a whisper of frost at the handshake
    seg(w01, h04, band(rain(8), 200, 2500), .05)
    a = E('w01') - 1.1; add(a, norm(band(noise(1.4), 3000, 10000) * (tt(1.4) / 1.4) ** .5 * np.exp(-tt(1.4) * 1.2)), .15); add(a, bell(1320, 2.0), .03)
    # it worked: a warm room; a music-box rise; the vase caught
    seg(h04, h05, band(brown(4), 60, 300), .04)
    for j, f in enumerate([1046, 1318, 1568, 2093]): add(h04 + .1 + j * .3, bell(f, 1.2), .03)
    add(h04 + .8, hit(.2, 200, 1500, 25), .15)
    # KEN: an engine, a radio hum; wood groaning; the tree; then nothing
    seg(h05, S('h05') + 3.2, engine(5, 32), .06)
    L = 1.2; add(S('h05') + 1.9, norm(band(np.sin(2 * np.pi * (90 + 40 * np.sin(tt(L) * 6)) * tt(L)) + .4 * noise(L), 60, 900) * np.sin(np.pi * tt(L) / L)), .2)
    add(S('h05') + 3.15, hit(1.2, 20, 600, 4), .7); add(S('h05') + 3.15, glass(), .3)
    # YUI: quick feet up the stairs, a crack, the fall
    for k in np.arange(h06, h06 + 1.8, .17): add(k, step(), .22)
    add(h06 + 1.95, snap(), .45); add(h06 + 2.2, hit(.6, 40, 400, 6), .5); add(h06 + 2.4, hit(.5, 40, 400, 7), .4)
    # REN: birds, a whistle, the kick; a crack of thunder out of nothing
    seg(h07, h07 + 2.0, band(noise(3), 2500, 7000) * (.4 + .6 * (np.sin(tt(3) * 40) > .7)), .015)
    add(h07 + 1.45, hit(.15, 80, 1200, 30), .2)
    add(h07 + 1.9, norm(band(noise(2.2), 30, 4000) * np.exp(-tt(2.2) * 2) + .6 * hit(2.2, 20, 200, 1.5)), .8)
    # the graves: rain on everything; a low drone; the umbrella snapping shut
    seg(h08, h09, rain(8), .1); seg(h08, h09, band(brown(8), 40, 160), .05)
    add(S('h08') + 2.6, hit(.15, 300, 3000, 30), .2)
    # midnight: a clock strikes; she blows; every bulb pops; the cooker goes up
    for j in range(3): add(h09 + .1 + j * .45, bell(220, 2.5), .07)
    add(h09 + 1.0, band(noise(.6), 200, 3000) * np.sin(np.pi * tt(.6) / .6), .08)
    for j in range(3): add(h09 + 2.4 + j * .07, glass(), .3)
    add(h09 + 2.8, norm(band(noise(1.5), 40, 2000) * (1 - np.exp(-tt(1.5) * 20)) * np.exp(-tt(1.5) * 1.5)), .5)
    # the hall: running feet, frames smashing, the fan tearing down
    for k in np.arange(h10, w02, .16): add(k, step(), .3)
    for j in range(5): add(h10 + .5 + j * .55, glass(), .14); add(h10 + .5 + j * .55, hit(.2, 100, 1200, 20), .12)
    add(S('h10') + 2.8, hit(1.0, 30, 1500, 4), .55); add(S('h10') + 2.8, snap(), .3)
    # the woman in the door: everything drops out but a low swell
    L = w02 - h10; add(w02 - .2, norm(np.sin(2 * np.pi * 36 * tt(2.4)) * np.sin(np.pi * tt(2.4) / 2.4)), .25)
    # the garage door slamming down; the engine catching
    add(h11, norm(band(noise(1.0), 200, 3000) * (np.sin(tt(1.0) * 90) > 0)), .15); add(h11 + 1.0, hit(.6, 40, 800, 6), .5)
    add(h11 + 1.6, engine(.9, 20, 1.5) * (np.sin(tt(.9) * 25) > 0), .2); add(h11 + 2.3, engine(1.2, 30, 1.0), .25)
    # the road: the engine screaming; a truck horn; tyres; the crash; the line sparking
    seg(h12, h13 + .3, engine(10, 52), .12)
    add(h12 + .1 * (h13 - h12), bell(330, 1.0), .03)
    a = h12 + .3 * (h13 - h12); L = 1.8; add(a, norm(np.sin(2 * np.pi * 155 * tt(L)) + np.sin(2 * np.pi * 185 * tt(L))) * np.linspace(1, .4, int(L * SR)), .18)
    add(a + .6, screech(1.4), .14); add(h12 + .6 * (h13 - h12), hit(1.4, 20, 1500, 3), .6); add(h12 + .6 * (h13 - h12), glass(), .3)
    b = h12 + .78 * (h13 - h12)
    for j in range(10): add(b + j * .09, norm(band(noise(.06), 2000, 9000) * np.exp(-tt(.06) * 50)), .25)
    seg(b, h13, norm(np.sin(2 * np.pi * 100 * tt(3)) + .3 * np.sin(2 * np.pi * 200 * tt(3))), .06)
    # the bridge: brakes; silence; the face slides (wet); the reveal hits
    add(h13, screech(1.2), .2); add(h13 + 1.1, hit(.5, 30, 300, 8), .3)
    add(E('h13') + .3, norm(band(noise(1.0), 100, 1200) * np.abs(np.sin(tt(1.0) * 18))) * np.linspace(.3, 1, int(SR)), .12)
    add(E('h13') + 1.3, hit(2.5, 20, 400, 1.5), .85); add(E('h13') + 1.3, snap(), .3)
    # it crawls: joints cracking, its breath; a drone that rises to the end; a heartbeat that speeds up
    for j in range(7): add(t01 + .3 + j * .33, snap(), .14)
    L = DUR - t01; t = tt(L); add(t01, norm(np.sin(2 * np.pi * np.cumsum(30 + 25 * (t / L) ** 2) / SR) * (.4 + .6 * (t / L))), .22)
    k, bpm = S('h14'), 70
    while k < E('h15') + .6:
        for o, g in ((0, 1), (.16, .6)): add(k + o, hit(.12, 30, 120, 25), .35 * g)
        k += 60 / bpm; bpm = min(150, bpm + 6)
    add(E('h15') + .6, hit(1.0, 20, 300, 4), .6)                                               # the touch; cut
    # voices
    for name, l in LAY.items():
        if name == 'END': continue
        p = os.path.join(VO, name + '.wav'); g = 1.0
        if name[0] == 'w': x = verb(load(p), .2, .5); g = 1.0
        elif name == 't01': x = load(p); g = 1.15
        else: x = load(p)
        add(l['offset'], x, g)
    m = m[:n]
    k = int((E('h15') + .75) * SR); m[k:] *= np.exp(-np.arange(len(m) - k) / (.25 * SR))          # black, and nothing
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
    out = os.path.join(HERE, args[args.index('--out') + 1] if '--out' in args else 'lucky_one_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '19', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
