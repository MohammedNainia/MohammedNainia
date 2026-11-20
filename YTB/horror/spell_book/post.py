"""THE SPELL BOOK: finish the render (silent) into the final reel: hook, captions, voices, sound.
    python post.py                  reads raw.mp4 -> spell_book_1080x1920.mp4
    python post.py --raw FILE       another silent render
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)
Voices are the 1.5x .wav files in voice/ (Gran 1.2x and aged here, Mum's line already reversed)."""
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
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

# ---------------------------------------------------------------- captions: short chunks, never across a sentence or a speaker
CHUNKS, i = [], 0
while i < len(WORDS):
    n = min(3, len(WORDS) - i) if len(WORDS) - i != 4 else 2
    for k in range(n - 1):
        if WORDS[i + k][0][-1:] in ',.?!' or WORDS[i + k][3] != WORDS[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(WORDS[i:i + n]); i += n
REV = [w for w in WORDS if w[1] >= S('m01') - .01 and w[2] <= E('m01') + .01]     # Mum's backwards line: shown whole, mirrored words
f_cap = ImageFont.truetype(FONT, 66); f_oth = ImageFont.truetype(FONT_I, 66); f_hook = ImageFont.truetype(FONT, 70)
HOOK = ["I READ ONE SPELL FROM", "MY DEAD GRAN'S BOOK.", "I'VE BEEN TRYING TO", "GET HOME EVER SINCE."]
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < 2.4 else max(0, 1 - (t - 2.4) / .35) if t < 2.75 else 0
    if ha > 0:
        for k, line in enumerate(HOOK):
            col = (255, 214, 90) if k >= 2 else (255, 255, 255)
            d.text((W // 2, 300 + k * 104), line, font=f_hook, fill=col + (int(255 * ha),), stroke_width=9, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if 2.75 <= t < DUR - .2:
        if REV and REV[0][1] - .1 <= t <= REV[-1][2] + 1.2:
            d.text((W // 2, 1440), 'uraH ,gninrom dooG', font=f_oth, fill=(255, 205, 220), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
        else:
            for ch in CHUNKS:
                if ch[0][1] - .05 <= t <= ch[-1][2] + .25 and ch[0] not in REV:
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
    n = int(DUR * SR); m = np.zeros(n + 4 * SR, np.float32); rng = np.random.default_rng(31)
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
    def click(): return band(noise(.03), 1500, 8000) * np.exp(-tt(.03) * 160)
    def birds(sec):
        b = np.zeros(int(sec * SR), np.float32)
        for k in np.arange(.2, sec - .4, .8 + rng.random()):
            tw = tt(.18); s = np.sin(2 * np.pi * np.cumsum(3200 + 900 * np.sin(tw * 70)) / SR) * np.sin(np.pi * tw / .18); i0 = int(k * SR); b[i0:i0 + len(s)] += s[:len(b) - i0] * .5
        return band(b, 1500, 7000)
    def engine(sec, f0=38):
        t = tt(sec); return norm(np.sin(2 * np.pi * f0 * t) * (1 + .5 * np.sin(2 * np.pi * 7 * t)) + .4 * band(noise(sec), 60, 500))
    # where we are
    back_parts = [(0, S('h02') - .3), (S('h06') + 2.6, E('h15') + .15)]                 # the backwards world
    attic_night = (S('h02') - .3, S('h06') + 2.6); attic_morning = [(S('h16') - .3, S('h17') - .2), (S('h18') - .2, S('h19') - .1)]
    street_morning = (S('h17') - .2, S('h18') - .2); kitchen = (S('h19') - .1, DUR)
    # the backwards world: wind that swells and is cut off (reversed gusts), a low drone, a far clock ticking the wrong way
    t = tt(20); dr = norm(np.sin(2 * np.pi * 47 * t) + .5 * np.sin(2 * np.pi * 70.5 * t + np.sin(t * .3)) + .6 * brown(20))
    for a, b in back_parts:
        seg(a, b, dr, .12)
        for k in np.arange(a + .5, b - 2, 3.3 + rng.random()):
            L = 1.8 + rng.random(); g = band(noise(L), 200, 2400) * (tt(L) / L) ** 3; add(k, norm(g), .08)
        for k in np.arange(a + .2, b, 1.0): add(k, click()[::-1].copy(), .035)
    # the attic at night: the house creaking, wind on the roof
    seg(*attic_night, band(brown(15), 40, 500), .07)
    for k in (attic_night[0] + 1.2, S('h04') + .5, S('h05') - .4): add(k, band(np.sin(2 * np.pi * (160 + 60 * np.sin(tt(.6) * 7)) * tt(.6)) * np.sin(np.pi * tt(.6) / .6), 80, 1200), .05)
    add(S('h02') + .8, band(noise(.4), 80, 1200) * np.exp(-tt(.4) * 10), .25)                       # the trunk lid
    # the spell: a rising hum from the page, then everything cut
    a0 = S('h05') + .4; L = E('h05') + .3 - a0; t = tt(L)
    add(a0, norm(np.sin(2 * np.pi * np.cumsum(110 + 500 * (t / L) ** 2) / SR) * (t / L) ** 1.5 + .5 * band(noise(L), 300, 5000) * (t / L) ** 3), .3)
    # the light comes back: a long low breath in
    add(S('h06') - .3, norm(band(noise(1.4), 60, 600) * np.sin(np.pi * tt(1.4) / 1.4)), .2)
    # green: the cars idle; red: one tears through
    seg(S('h07') - .2, S('h07') + 1.1, engine(4), .07)
    add(S('h07') + 1.0, norm(band(noise(1.2), 80, 3000) * np.sin(np.pi * tt(1.2) / 1.2) ** 2 + engine(1.2, 70) * np.sin(np.pi * tt(1.2) / 1.2)), .35)
    # the car backs off her; every bone clicks back into place
    add(S('h08') + .4, engine(1.4, 32) * np.linspace(1, 0, int(1.4 * SR)), .12)
    for j in range(6):
        k = S('h08') + 2.0 + j * .4
        for r in range(3): add(k + r * .03, click(), .22)
    # the funeral: cutlery on plates, chewing
    for k in np.arange(S('h09') - .2, S('h10') + .5, .37): add(k + rng.random() * .2, clink(3000 + rng.random() * 900, 22), .03)
    for k in np.arange(S('h09') + .5, S('h10') - .3, 1.1): add(k, band(noise(.25), 200, 1500) * np.sin(np.pi * tt(.25) / .25), .03)
    # every head turns: four snaps, then nothing at all
    for j in range(4): add(S('h10') + .6 + j * .3, norm(band(noise(.12), 300, 3000) * np.exp(-tt(.12) * 25)), .2)
    # she reads it backwards: chairs scrape, the table stands; cut to black with a thud
    for j in range(3): add(S('h15') + 1.0 + j * .33, norm(band(noise(.5), 100, 1800) * np.sin(np.pi * tt(.5) / .5)), .2)
    add(E('h15') + .1, norm(band(noise(.6), 30, 250) * np.exp(-tt(.6) * 7)), .7)
    # morning: birds, a calm attic, the ordinary street, a car pulling away
    for a, b in attic_morning: seg(a, b, birds(8), .04)
    seg(*street_morning, birds(8), .05); add(S('h17') + 2.4, engine(2.0, 45) * np.linspace(.4, 1, int(2 * SR)) * np.linspace(1, 0, int(2 * SR)) ** .5, .12)
    # the kitchen: the pan sizzling, the radio low; her footsteps
    seg(*kitchen, band(noise(10), 2000, 9000) * (.7 + .3 * np.sin(tt(10) * 9)), .02)
    for k in np.arange(S('h19') - .1, S('h19') + 1.5, .22): add(k, band(noise(.05), 100, 1500) * np.exp(-tt(.05) * 60), .12)
    # after "Good morning" backwards: a reversed swell, then the room goes silent under her face
    L = 1.6; add(E('m01') + .2, norm(verb(band(noise(L), 100, 3000), .6, 1.2)[::-1] * (tt(L) / L) ** 2), .25)
    # voices
    for name, l in LAY.items():
        if name == 'END': continue
        p = os.path.join(VO, name + '.wav')
        if name[0] == 'g': x = verb(load(p, 'asetrate=44100*0.92,aresample=44100,tremolo=f=5:d=0.25'), .3, .6)      # Gran: older, a tremor, from somewhere else
        elif name[0] == 'm': x = verb(load(p), .25, .5)
        else: x = load(p)
        add(l['offset'], x, 1.0 if name[0] == 'h' else 1.1)
    m = m[:n]
    k = int((E('m01') + .3) * SR); m[k:] *= np.linspace(1, .35, len(m) - k)                                           # the sound drains away at the end
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
    out = os.path.join(HERE, args[args.index('--out') + 1] if '--out' in args else 'spell_book_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
