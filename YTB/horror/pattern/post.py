"""THE PATTERN: finish the render (silent) into the final reel: hook, captions, voices, sound.
    python post.py                  reads raw.mp4 -> pattern_1080x1920.mp4
    python post.py --raw FILE       another silent render
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)
Voices are the 1.5x .wav files in voice/. Her gasp (x01) and the chant are made here."""
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
HOOK_END = next(w[2] for w in WORDS if w[0].lower().startswith('pyramid')) + .25   # the hook is the first line, spoken and shown at once
CAPW = [w for w in WORDS if w[1] >= HOOK_END - .2]
CHUNKS, i = [], 0
while i < len(CAPW):
    n = min(3, len(CAPW) - i) if len(CAPW) - i != 4 else 2
    for k in range(n - 1):
        if CAPW[i + k][0][-1:] in ',.?!:' or CAPW[i + k][3] != CAPW[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(CAPW[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 66); f_oth = ImageFont.truetype(FONT_I, 70); f_hook = ImageFont.truetype(FONT, 66)
HOOK = ["I CAME HOME FROM EGYPT.", "EVERYTHING LOOKED THE SAME.", "I NEVER LEFT THE PYRAMID."]
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < HOOK_END else max(0, 1 - (t - HOOK_END) / .3)
    if ha > 0:
        for k, line in enumerate(HOOK):
            col = (255, 214, 90) if k == 2 else (255, 255, 255)
            d.text((W // 2, 320 + k * 100), line, font=f_hook, fill=col + (int(255 * ha),), stroke_width=9, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if HOOK_END <= t < DUR - .2:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .25:
                oth = ch[0][3]; s = ' '.join(w for w, _, _, _ in ch)
                y = 1440
                d.text((W // 2, y), s, font=f_oth if oth else f_cap, fill=(255, 238, 226) if oth else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound
SR = 48000
def load(p, extra=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', p] + (['-af', extra] if extra else []) + ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).copy()
PAT = [.62, .62, .62, .62, .62, .24, .24]                              # the guide's pattern, as the scene walks it
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + 4 * SR, np.float32); rng = np.random.default_rng(33)
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
    def step(lo=80, hi=1400): return norm(band(noise(.11), lo, hi) * np.exp(-tt(.11) * 38))
    def crack(): return norm(band(noise(.05), 800, 6000) * np.exp(-tt(.05) * 70))
    def door(): return norm(band(noise(.4), 50, 800) * np.exp(-tt(.4) * 12) + .5 * band(noise(.4), 1500, 4000) * np.exp(-tt(.4) * 40))
    def chant(sec, f0=98, voices=7):                                    # many low voices on one dark chord, breathing in and out together
        t = tt(sec); out = np.zeros(len(t), np.float32)
        for v in range(voices):
            f = f0 * [1, 1, 1.5, 2, 1.19, 1, .5][v % 7] * (1 + .006 * rng.standard_normal()); vib = 1 + .004 * np.sin(2 * np.pi * (4.5 + rng.random()) * t + rng.random() * 6)
            ph = 2 * np.pi * np.cumsum(f * vib) / SR; saw = sum(np.sin(k * ph) / k for k in range(1, 9))
            out += band(saw.astype(np.float32), 120, 1400) * (.6 + .4 * np.sin(2 * np.pi * .22 * t + v))
        return norm(out * (.55 + .45 * np.abs(np.sin(np.pi * t / 2.6))))   # syllables: a slow pulse
    def gasp(): t = tt(.55); return norm(band(noise(.55), 600, 4500) * np.sin(np.pi * np.clip(t / .22, 0, 1)) * np.exp(-np.clip(t - .2, 0, None) * 9) + .4 * band(noise(.55), 200, 900) * np.exp(-t * 8))
    def static(sec): return norm(band(noise(sec), 1500, 12000))
    a0 = S('h02') - .3; brk = S('h03') + 1.2; dark = S('h04') + 1.9
    # DUSK OUTSIDE: wind over sand, a few voices of the class
    seg(0, a0, band(brown(6), 80, 900), .14); seg(0, a0, band(noise(6), 1500, 5000), .02)
    # THE CORRIDOR: a cold stone room tone; every foot of the class in the pattern, five slow, two fast; the torches hiss
    seg(a0, dark, band(brown(16), 40, 220), .07); seg(a0, dark, band(noise(16), 2000, 6000) * (.5 + .5 * np.abs(np.sin(tt(16) * 3))), .012)
    times = np.cumsum([0] + PAT * 8)[:-1]
    for lag, g in ((0, .3), (.03, .22), (.05, .2), (.09, .18), (.12, .16)):
        for k in times:
            tk = a0 + k + lag
            if tk < dark - .1: add(tk, step(), g)
    for k in times:                                                      # Haru: in step until she breaks it; then one slow step alone, late
        tk = a0 + k + .07
        if tk < brk: add(tk, step(), .34)
    add(brk + .62, step(), .45)
    # THE TORCHES GONE: everything stops; her breath, close
    for k in np.arange(dark, S('h05') + 1.0, .9): add(k, norm(band(noise(.6), 400, 3000) * np.sin(np.pi * tt(.6) / .6) ** 2), .08)
    seg(dark, S('h06') - .5, band(brown(8), 30, 120), .1)
    # THE CHANT: far off below her at first, louder as she goes down; full in the chamber; cut dead by her gasp
    gx = S('x01')
    a = S('h05') - .2; L = gx - a; c = chant(L + .3); env = np.clip((tt(len(c) / SR) - 0) / (S('h06') - .5 - a), .15, 1) ** 1.5; c = c * env.astype(np.float32)
    c[int((gx - a) * SR):] = 0; c[int((gx - a) * SR) - 600:int((gx - a) * SR)] *= np.linspace(1, 0, 600); add(a, verb(c, .35, .9), .3)
    add(gx, gasp(), .9)
    # THE TURN: silence; heads turning with a creak of cloth; the arms coming up; a low swell
    for j in range(10): add(S('h07') + .2 + j * .22, norm(band(noise(.3), 300, 2500) * np.sin(np.pi * tt(.3) / .3)), .05)
    L = S('g02') - S('h07'); add(S('h07'), norm(np.sin(2 * np.pi * np.cumsum(36 + 20 * (tt(L) / L) ** 2) / SR) * (tt(L) / L) ** .7), .25)
    k, bpm = S('h07'), 80
    while k < S('g02') - .3:
        for o, g in ((0, 1), (.15, .6)): add(k + o, hit(.12, 30, 120, 25), .32 * g)
        k += 60 / bpm; bpm = min(150, bpm + 6)
    # THE GUIDE: torches again; the fall as she faints; silence
    seg(S('g02') - .3, S('h09') - .4, band(brown(4), 40, 220), .07); add(S('h09') - .1, hit(.6, 30, 400, 6), .35)
    # HOME: morning birds; a quiet house; a clock; Mum's slow turn with a creak; the TV hissing with the chant under it
    seg(S('h09') + 1.2, S('h12') - .3, band(noise(14), 2500, 6000) * (np.sin(tt(14) * 40) > .8), .01)
    for k in np.arange(S('h10') - .3, S('h12') - .3, 1.0): add(k, crack(), .04)
    add(S('h11') + 1.0, norm(band(noise(1.4), 200, 1200) * np.sin(np.pi * tt(1.4) / 1.4)), .05)
    seg(S('h12') - .3, S('h13') - .3, static(4), .06); seg(S('h12') + .6, S('h13') - .3, chant(3, 92, 5), .06)
    # SHE RUNS: feet, the door slammed; just a dream
    for k in np.arange(S('h13') - .3, S('h13') + .9, .17): add(k, step(), .25)
    add(S('h13') + .95, door(), .5)
    # THE CIRCLE AGAIN: the chant, all around, close; it stops for Mum
    a = S('h14') - .3; L = S('m01') - .2 - a; add(a, verb(chant(L, 98, 9), .3, .7), .32)
    add(S('h14') + .4, hit(1.4, 20, 250, 2.5), .55)
    # voices
    for name, l in LAY.items():
        if name in ('END', 'x01'): continue
        p = os.path.join(VO, name + '.wav')
        if name[0] == 'g': add(l['offset'], verb(load(p), .25, .5), 1.0)         # the guide in the stone corridor
        elif name == 'm01': add(l['offset'], verb(load(p, 'asetrate=44100*0.94,aresample=48000,atempo=1.064'), .3, .6), 1.0)   # Mum, a little low, in the chamber
        else: add(l['offset'], load(p), 1.0)
    m = m[:n]
    k = int((E('m01') + .7) * SR); m[k:] *= np.exp(-np.arange(len(m) - k) / (.3 * SR))          # black, and nothing
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
    out = os.path.join(HERE, args[args.index('--out') + 1] if '--out' in args else 'vacancy_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '20', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
