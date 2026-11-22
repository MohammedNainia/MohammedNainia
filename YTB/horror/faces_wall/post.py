"""THE FACES ON THE WALL: finish the render (silent) into the final reel: hook, captions, voices, sound.
    python post.py                  reads raw.mp4 -> faces_wall_1080x1920.mp4
    python post.py --raw FILE       another silent render
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)
Voices are the 1.5x .wav files in voice/ (the boy, the wall and the crowd are treated here)."""
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
HOOK_END = next(w[2] for w in WORDS if w[0] == 'wall.') + .25          # the hook is the first sentence, spoken and shown at once
CAPW = [w for w in WORDS if w[1] >= HOOK_END - .2]
CHUNKS, i = [], 0
while i < len(CAPW):
    n = min(3, len(CAPW) - i) if len(CAPW) - i != 4 else 2
    for k in range(n - 1):
        if CAPW[i + k][0][-1:] in ',.?!:' or CAPW[i + k][3] != CAPW[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(CAPW[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 66); f_oth = ImageFont.truetype(FONT_I, 66); f_hook = ImageFont.truetype(FONT, 60)
HOOK = ["THREE KIDS AT MY SCHOOL", "WERE FOUND WITH THEIR", "FACES PRESSED AGAINST", "A CLASSROOM WALL."]
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < HOOK_END else max(0, 1 - (t - HOOK_END) / .3)
    if ha > 0:
        for k, line in enumerate(HOOK):
            col = (255, 214, 90) if k >= 2 else (255, 255, 255)
            d.text((W // 2, 300 + k * 92), line, font=f_hook, fill=col + (int(255 * ha),), stroke_width=9, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if HOOK_END <= t < DUR - .2:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .25:
                oth = ch[0][3]; s = ' '.join(w for w, _, _, _ in ch)
                d.text((W // 2, 1440), s, font=f_oth if oth else f_cap, fill=(255, 205, 220) if oth else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound
SR = 48000
def load(p, extra=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', p] + (['-af', extra] if extra else []) + ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).copy()
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + 4 * SR, np.float32); rng = np.random.default_rng(28)
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
        out = amt * np.convolve(x, ir); out[:len(x)] += x; return out.astype(np.float32)          # keeps the tail
    def seg(a, b, x, g):
        L = int((b - a) * SR); y = np.resize(x, L).astype(np.float32); fe = min(L // 3, int(.3 * SR)); y[:fe] *= np.linspace(0, 1, fe); y[-fe:] *= np.linspace(1, 0, fe); add(a, y, g)
    def hit(sec=.6, lo=30, hi=250, d=7): return norm(band(noise(sec), lo, hi) * np.exp(-tt(sec) * d))
    def snap(): return norm(band(noise(.12), 300, 3000) * np.exp(-tt(.12) * 25))
    def step(): return norm(band(noise(.09), 60, 900) * np.exp(-tt(.09) * 45))
    def buzz(sec, flick=False):                                         # fluorescent tubes: mains hum and its harmonics, a little sizzle
        t = tt(sec); x = sum(np.sin(2 * np.pi * 100 * k * t) / k for k in (1, 2, 3, 5)) + .3 * band(noise(sec), 3000, 9000)
        if flick:
            env = np.ones(len(t), np.float32)
            for k in np.arange(.6, sec - .3, 1.7 + rng.random()):
                i0 = int(k * SR); env[i0:i0 + int(.08 * SR)] = .1; env[i0 + int(.14 * SR):i0 + int(.19 * SR)] = .2
            x = x * env
        return norm(x)
    # where we are
    CR = [(0, S('h08') - .2)]; CO = [(S('h08') - .2, S('h09') - .4), (S('h15') - .5, DUR)]; AB = (S('h09') - .4, S('h15') - .5)
    # the classroom: a room tone, the tubes, the building
    for a, b in CR: seg(a, b, band(brown(12), 40, 400), .05); seg(a, b, buzz(10), .012)
    # the hook: a long low swell under the first line, a hit on "wall."
    add(0, norm(band(noise(3.6), 40, 500) * (tt(3.6) / 3.6) ** 2), .18); add(HOOK_END - .2, hit(1.2, 25, 180, 4), .5)
    # they're pulled off the wall: the scream is in the words; nails in the paint, a scrape
    add(S('h02') + 2.4, norm(band(noise(.9), 1500, 7000) * np.sin(np.pi * tt(.9) / .9) ** 3), .12)
    # the window: a thin high tone each time the glass holds the extra one
    for a in (S('h04') + 2.0, S('h05') + 1.8, S('h06') - .2):
        L = 2.6; t = tt(L); add(a, norm(np.sin(2 * np.pi * 1760 * t + 3 * np.sin(2 * np.pi * 3 * t)) * np.sin(np.pi * t / L) ** 2), .025)
    add(S('h06') - .1, hit(1.6, 25, 160, 3), .45)                                            # no face
    # the corridor: buzzing, flickering tubes
    for a, b in CO: seg(a, b, buzz(12, True), .03); seg(a, b, band(brown(12), 30, 250), .05)
    # the abandoned room: wind through boards, a drone that never resolves
    t = tt(20); dr = norm(np.sin(2 * np.pi * 43 * t) + .5 * np.sin(2 * np.pi * 64.5 * t + np.sin(t * .3)) + .6 * brown(20))
    seg(*AB, dr, .1); seg(*AB, band(brown(15), 200, 1800), .04)
    add(S('h09') + .6, norm(band(noise(1.0), 80, 1500) * np.sin(np.pi * tt(1.0) / 1.0)), .18)   # the boarded door gives
    # breathing behind the plaster, slower and slower; then the press back
    a = S('h12') + 1.4
    for k in range(4):
        L = 1.2 + k * .2; br = band(noise(L), 150, 1100) * np.sin(np.pi * tt(L) / L) ** 2; add(a, norm(br), .09); a += L + .5
    add(S('h12') + 4.5, hit(.8, 30, 200, 6), .55)
    # the wall cracks open: a split, then plaster falling for seconds
    a0 = S('h13') + .1; add(a0, hit(1.5, 20, 400, 3), .6); add(a0, snap(), .35)
    for k in a0 + np.cumsum(rng.exponential(.09, 40)):
        if k < a0 + 3.5: add(k, norm(band(noise(.05), 400, 5000) * np.exp(-tt(.05) * 80)), .05 + .1 * rng.random())
    seg(S('h13') + 2.0, E('h13'), band(brown(8), 30, 120), .08)                               # something huge, breathing in the dark
    # its head begins to turn: the neck cracks
    for j in range(5): add(S('h14') + .1 + j * .26, snap(), .2)
    # she runs: footsteps all the way down the corridor
    for k in np.arange(S('h14') + 1.0, S('h15') + 4.0, .27): add(k, step(), .25)
    # in the glass, right behind her: the sting; she turns, nothing
    add(S('h16') + .2, hit(2.0, 25, 300, 2.5), .55); L = 2.2; t = tt(L)
    add(S('h16') + .2, norm((np.sin(2 * np.pi * 220 * t) + np.sin(2 * np.pi * 233 * t) + .6 * np.sin(2 * np.pi * 311 * t)) * np.exp(-t * 1.4)), .08)
    # the end: a sub rising under her eyes, cut to silence at black
    L = DUR - S('h17'); t = tt(L); add(S('h17'), norm(np.sin(2 * np.pi * np.cumsum(28 + 30 * (t / L) ** 2) / SR) * (t / L) ** 1.5), .25)
    add(E('h18') + .6, hit(2.0, 20, 200, 2), .5)                                             # the eyes go blank
    # voices
    for name, l in LAY.items():
        if name == 'END': continue
        p = os.path.join(VO, name + '.wav'); g = 1.0
        if name == 'k01': x = verb(load(p, 'highpass=f=180,lowpass=f=6000'), .35, .6); g = .9               # the boy, into the plaster
        elif name == 'x01': x = verb(load(p, 'asetrate=44100*0.86,aresample=44100,lowpass=f=3200'), .6, 1.6); g = .8   # the wall, from inside it
        elif name == 'x02':                                                                    # the crowd: every child at every wall
            srcs = [load(os.path.join(VO, v + '.wav')) for v in ('x02', 'x02b', 'x02c')]; x = np.zeros(int(3.5 * SR), np.float32)
            for j in range(14):
                r = .82 + .3 * rng.random(); s = srcs[j % 3]; y = np.interp(np.arange(0, len(s) - 1, r), np.arange(len(s)), s).astype(np.float32)
                o = int(rng.random() * .22 * SR); x[o:o + len(y)] += y[:len(x) - o] * (.5 + .5 * rng.random())
            x = verb(norm(x), .5, 1.2); g = .9
        else: x = load(p)
        add(l['offset'], x, g)
    m = m[:n]
    k = int((DUR - .35) * SR); m[k:] = 0                                                       # black, and nothing
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
    out = os.path.join(HERE, args[args.index('--out') + 1] if '--out' in args else 'faces_wall_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
