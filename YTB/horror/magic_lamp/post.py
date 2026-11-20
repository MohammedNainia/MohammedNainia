"""THE MAGIC LAMP: finish the render (silent) into the final reel: hook, captions, the lamp's-eye view, voices, sound.
    python post.py                  reads raw.mp4 -> magic_lamp_1080x1920.mp4
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)"""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
W, H, FPS, DUR = 1080, 1920, 30, 89.5
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_I = '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'
if not os.path.exists(FONT_I): FONT_I = FONT
if not os.path.exists(FONT): FONT = FONT_I = 'C:/Windows/Fonts/arialbd.ttf'
WORDS = json.load(open(os.path.join(VO, 'words.json'))); LAY = {l['name']: l for l in json.load(open(os.path.join(VO, 'layout.json')))}
S = lambda n: LAY[n]['start']; E = lambda n: LAY[n]['end']
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
f_cap = ImageFont.truetype(FONT, 66); f_oth = ImageFont.truetype(FONT_I, 66); f_hook = ImageFont.truetype(FONT, 72)
HOOK = ['I RUBBED A MAGIC LAMP.', 'SOMETHING CAME OUT.', 'I WENT IN.']
# the shots seen from inside the lamp, out through the spout: a round view with a brass rim
LAMP_EYE = [(S('h12') - .8, E('m01') + .4)]
def lamp_eye(im, d, t):
    k = min(1, (t - LAMP_EYE[0][0]) / .4)
    r = int(lerp(1400, 470, ease(k))); cx, cy = W // 2, H // 2 - 60
    mask = Image.new('L', (W, H), 255); md = ImageDraw.Draw(mask); md.ellipse((cx - r, cy - r, cx + r, cy + r), fill=0)
    im.paste((6, 4, 2), (0, 0, W, H), mask)
    for w, col in [(26, (92, 66, 26)), (12, (150, 112, 48)), (4, (200, 160, 80))]:
        d.ellipse((cx - r - w, cy - r - w, cx + r + w, cy + r + w), outline=col + (255,), width=w)
def lerp(a, b, k): return a + (b - a) * k
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    for a, b in LAMP_EYE:
        if a <= t < b: lamp_eye(im, d, t)
    # the suction: the picture goes white-hot then black as she is pulled in
    a0, a1 = E('h04') + .1, S('h05') - .9
    if a0 <= t < a1 + .25:
        k = (t - a0) / (a1 - a0)
        if k > .75: d.rectangle((0, 0, W, H), fill=(0, 0, 0, int(255 * min(1, (k - .75) / .25))))
    ha = 1.0 if t < 2.4 else max(0, 1 - (t - 2.4) / .35) if t < 2.75 else ease((t - (DUR - .55)) / .2) if t > DUR - .55 else 0
    if ha > 0:
        for k, line in enumerate(HOOK):
            col = (255, 214, 90) if k == 2 else (255, 255, 255)
            d.text((W // 2, 300 + k * 112), line, font=f_hook, fill=col + (int(255 * ha),), stroke_width=9, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if 2.75 <= t < DUR - .6:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .3:
                oth = ch[0][3]; s = ' '.join(w for w, _, _, _ in ch)
                d.text((W // 2, 1440), s, font=f_oth if oth else f_cap, fill=(255, 205, 220) if oth else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound
SR = 48000
SFXD = os.path.join(HERE, 'sfx')
def load(p, extra=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', p] + (['-af', extra] if extra else []) + ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).copy()
def real(name):
    for ext in ('.wav', '.mp3', '.flac', '.ogg', '.m4a'):
        p = os.path.join(SFXD, name + ext)
        if os.path.exists(p): x = load(p); return x / (np.abs(x).max() + 1e-6)
    return None
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + 4 * SR, np.float32); rng = np.random.default_rng(23)
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
        return (x + amt * np.convolve(x, ir)[:len(x)]).astype(np.float32)
    def seg(a, b, x, g):
        L = int((b - a) * SR); y = np.resize(x, L).astype(np.float32); fe = min(L // 3, int(.3 * SR)); y[:fe] *= np.linspace(0, 1, fe); y[-fe:] *= np.linspace(1, 0, fe); add(a, y, g)
    def clink(f0=2600, d=14):
        t = tt(.4); return norm(sum(np.sin(2 * np.pi * f * t) * np.exp(-t * dd) for f, dd in [(f0, d), (f0 * 1.52, d * 1.3), (f0 * 2.31, d * 1.7)]))
    def breath(sec=2.0):
        t = tt(sec); return norm(band(noise(sec), 80, 900) * np.sin(np.pi * t / sec) ** 2)
    # where we are, second by second
    lamp_parts = [(0, S('h02') - .3), (S('h05') - .9, S('h12') - .8), (88.0, DUR)]
    market_parts = [(S('h02') - .3, S('h02b') - .4), (S('h13') - .6, 88.0)]
    kitchen = (S('h02b') - .4, S('h03') - .35); bedroom = (S('h03') - .35, S('h05') - .9); morning = (S('h12') - .8, S('h13') - .6)
    # inside the lamp: a low metal drone, slow wet breathing in the walls, oil dripping
    dr = real('lamp_drone')
    if dr is None: t = tt(30); dr = norm(np.sin(2 * np.pi * 41 * t) + .5 * np.sin(2 * np.pi * 61.5 * t + np.sin(t * .4)) + .5 * brown(30) + .2 * np.sin(2 * np.pi * 123 * t) * np.sin(t * .7))
    for a, b in lamp_parts:
        seg(a, b, verb(dr, .4, .8), .14)
        for k in np.arange(a + .8, b - 1, 3.1): add(k, breath(2.4), .09)
        for k in np.arange(a + .3, b, 1.7 + rng.random()): add(k + rng.random() * .6, verb(clink(1700 + rng.random() * 500, 30) * .4, .6, .9), .05)   # drips
    # the market: a murmur of people, a far bell, a cart
    mk = real('market')
    if mk is None: mk = norm(band(noise(20), 200, 2500) * (.6 + .4 * np.sin(tt(20) * 2.1)) + .4 * band(brown(20), 60, 400))
    for a, b in market_parts: seg(a, b, mk, .06)
    # the kitchen at night: fridge hum, the clock; Mum's steps and the front door
    t = tt(10); hum = norm(np.sin(2 * np.pi * 50 * t) + .4 * np.sin(2 * np.pi * 100 * t) + .2 * band(noise(10), 60, 300))
    seg(*kitchen, hum, .05)
    tick = band(noise(.02), 2000, 6000) * np.exp(-tt(.02) * 200)
    for k in np.arange(kitchen[0] + .3, kitchen[1], 1.0): add(k, tick, .05)
    for k in np.arange(S('h02b') + 1.5, S('h02b') + 4.5, .55): add(k, band(noise(.06), 150, 2000) * np.exp(-tt(.06) * 50), .12)
    add(kitchen[1] - .6, band(noise(.3), 60, 600) * np.exp(-tt(.3) * 14), .4)     # the door shuts
    # the bedroom at night: wind, the house settling; the brass squeaks under her thumb; the suction
    seg(*bedroom, band(brown(15), 50, 600), .05)
    for k in np.arange(S('h04') + .2, E('h04') + .1, .33): add(k, band(np.sin(2 * np.pi * (900 + 300 * np.sin(tt(.25) * 30)) * tt(.25)) * np.sin(np.pi * tt(.25) / .25), 400, 3000), .05)
    a0, a1 = E('h04') + .1, S('h05') - .9; L = a1 - a0; t = tt(L)
    whoosh = norm(band(noise(L), 80, 4000) * (t / L) ** 2 + .6 * np.sin(2 * np.pi * np.cumsum(60 + 400 * (t / L) ** 2) / SR) * (t / L))
    add(a0, whoosh, .5)
    add(a1 + .1, norm(band(noise(.5), 30, 300) * np.exp(-tt(.5) * 9)), .7)     # she hits the floor of the lamp
    # the coin man: a cough and a coin every 1.6 s while we see him
    for k in np.arange(S('h07') - .4, S('h08') - .4, 1.6):
        add(k + .05, band(noise(.25), 150, 1800) * np.exp(-tt(.25) * 12), .12)
        for j in range(3): add(k + .45 + j * .12, clink(3200 + rng.random() * 600, 10), .06 / (j + 1))
    # the mother rocking: a slow creak
    for k in np.arange(S('h08') - .3, S('h09') - .4, 1.45): add(k, band(np.sin(2 * np.pi * (220 + 80 * np.sin(tt(.5) * 9)) * tt(.5)) * np.sin(np.pi * tt(.5) / .5), 100, 1500), .04)
    # the girl tearing out of the wall: brass cracking
    for k in np.arange(S('h10') - .3, S('h10') + 1.6, .21): add(k + rng.random() * .08, band(noise(.08), 1200, 7000) * np.exp(-tt(.08) * 40), .09)
    # morning: birds outside, a calm room (everything is fine, that is the horror)
    mrn = real('morning')
    if mrn is None:
        mrn = np.zeros(int(9 * SR), np.float32)
        for k in np.arange(.2, 8.5, .9 + rng.random()):
            tw = tt(.18); s = np.sin(2 * np.pi * np.cumsum(3200 + 900 * np.sin(tw * 70)) / SR) * np.sin(np.pi * tw / .18); i0 = int(k * SR); mrn[i0:i0 + len(s)] += s[:len(mrn) - i0] * .5
    seg(*morning, band(mrn, 1500, 7000), .03)
    # the very end: a little brass ring as the boy's hand reaches, then the lamp's breath again (loop)
    add(E('g02') - .6, verb(clink(2200, 3), .5, 1.2), .12)
    add(DUR - 1.6, breath(1.6), .12)
    # voices
    for name, l in LAY.items():
        p = os.path.join(VO, name + '.mp3')
        if name[0] == 'g': x = verb(load(p, 'asetrate=44100*0.93,aresample=44100'), .35, .6)       # the girl: Haru's voice, slower, hollow
        elif name == 'x01':                                                                          # the walls: the whisper, three times over
            x0 = load(p); L0 = len(x0)
            def lay(x, d): y = np.zeros(L0, np.float32); seg_ = np.concatenate([np.zeros(int(d * SR), np.float32), x])[:L0]; y[:len(seg_)] = seg_; return y
            x = norm(x0 + .7 * lay(load(p, 'asetrate=44100*0.88,aresample=44100'), .13) + .5 * lay(load(p, 'asetrate=44100*1.1,aresample=44100'), .29))
            x = verb(x, .5, .9) * .8
        elif name[0] == 's': x = verb(load(p), .08, .2)
        else: x = load(p)
        if name[0] == 'h' and (S('h05') - .9 <= l['start'] < S('h12') - .8): x = verb(x, .25, .7)         # inside the lamp, her voice echoes
        add(l['offset'], x, 1.0 if name[0] == 'h' else 1.05)
    m = m[:n]; m /= max(1.0, np.abs(m).max() / .95)
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
    out = os.path.join(HERE, args[args.index('--out') + 1] if '--out' in args else 'magic_lamp_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
