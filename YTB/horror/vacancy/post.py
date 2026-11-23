"""THE VACANCY: finish the render (silent) into the final reel: hook, captions, voices, sound.
    python post.py                  reads raw.mp4 -> vacancy_1080x1920.mp4
    python post.py --raw FILE       another silent render
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)
Voices are the 1.5x .wav files in voice/. The other Haru's line (d01) is made wrong here: her own voice, doubled a little low and a little high."""
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
X_MAN, X_WOM, X_BOY = S('h07') + .5, S('h08') + 2.7, S('h09') + .5          # when each guest steps into the light (as in the scene)
BLACK0, SIGN0 = E('h15') + 1.3, DUR - 1.6                                    # the cut to black; the sign again (NO clicks on at DUR - 1.1)

# ---------------------------------------------------------------- captions: short chunks, never across a sentence or a speaker
HOOK_END = next(w[2] for w in WORDS if w[0].lower().startswith('them')) + .25   # the hook is the first line, spoken and shown at once
CAPW = [w for w in WORDS if w[1] >= HOOK_END - .2]
CHUNKS, i = [], 0
while i < len(CAPW):
    n = min(3, len(CAPW) - i) if len(CAPW) - i != 4 else 2
    for k in range(n - 1):
        if CAPW[i + k][0][-1:] in ',.?!:' or CAPW[i + k][3] != CAPW[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(CAPW[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 66); f_oth = ImageFont.truetype(FONT_I, 70); f_hook = ImageFont.truetype(FONT, 66)
HOOK = ["THREE OF US CHECKED IN.", "THREE OF US LEFT.", "I WASN'T ONE OF THEM."]
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
                y = 960 if oth else 1440                                           # the other one's line sits in the middle of the black
                d.text((W // 2, y), s, font=f_oth if oth else f_cap, fill=(255, 238, 226) if oth else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound
SR = 48000
def load(p, extra=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', p] + (['-af', extra] if extra else []) + ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).copy()
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + 4 * SR, np.float32); rng = np.random.default_rng(21)
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
    def crack(): return norm(band(noise(.05), 800, 6000) * np.exp(-tt(.05) * 70))
    def step(lo=60, hi=900): return norm(band(noise(.09), lo, hi) * np.exp(-tt(.09) * 45))
    def clang(): t = tt(.5); return norm(sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in [(410, 9), (980, 12), (1730, 16)]) + band(noise(.5), 400, 4000) * np.exp(-t * 30))   # a foot on a metal step
    def engine(sec, f0=38, rev=0):
        t = tt(sec); f = f0 * (1 + rev * t / sec); return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + .5 * np.sin(2 * np.pi * 7 * t)) + .4 * band(noise(sec), 60, 500))
    def hum(sec, f=120): t = tt(sec); return norm(np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * 2 * f * t) + .3 * np.sin(2 * np.pi * 3 * f * t) + .15 * band(noise(sec), 2000, 6000))
    def crickets(sec): t = tt(sec); return norm(np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 28 * t) > .3) * (np.sin(2 * np.pi * .7 * t) > -.2)) * .6 + .4 * norm(band(noise(sec), 3500, 6000)) * .2
    def door(): return norm(band(noise(.35), 60, 900) * np.exp(-tt(.35) * 14) + .4 * band(noise(.35), 1500, 4000) * np.exp(-tt(.35) * 40))
    def bell(f=440, sec=3.0): t = tt(sec); return norm(sum(np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, d in [(1, 1.2), (2.4, 2), (3.9, 3), (5.4, 4)]))
    def jingle(): return norm(sum(np.sin(2 * np.pi * f * tt(.5)) * np.exp(-tt(.5) * (12 + 8 * rng.random())) * (tt(.5) > o) for f, o in zip(rng.uniform(3000, 6500, 7), rng.uniform(0, .15, 7))))
    def flick(): return norm(band(noise(.04), 1000, 8000) * np.exp(-tt(.04) * 80))
    # THE ROAD: the engine, tyres on tarmac, wind past the windows
    seg(0, S('h02') + 3.0, engine(14, 34), .1); seg(0, S('h02') + 3.0, band(brown(14), 50, 400), .12); seg(0, S('h02'), band(noise(6), 400, 3000), .025)
    # THE SIGN: neon buzzing on, clicking; the car slowing, turning in over gravel
    a = S('h02') - .3; seg(a, S('h03') - .5, hum(7, 120), .035)
    for k in np.arange(a, a + .6, 1 / 12):
        if int(k * 12) % 3 == 0: add(k, flick(), .25)
    add(S('h03') - 1.6, norm(band(noise(1.2), 600, 5000) * (np.abs(np.sin(tt(1.2) * 40)) ** 4)), .08)   # gravel
    # THE OFFICE: room tone, a clock; nobody; the keys lifted off the counter
    seg(S('h03') - .5, S('h04') - .5, band(brown(5), 60, 250), .04)
    for k in np.arange(S('h03') - .5, S('h04') - .5, 1.0): add(k, crack(), .05)
    add(S('h03') + 2.9, jingle(), .2)
    # THE ROOM: a fridge-hum of a room; the bed springs under her hand; Mom's voice too far to hear
    seg(S('h04') - .5, S('h05') - .4, hum(5, 60), .015); add(S('h04') + .4, norm(band(noise(.4), 300, 2000) * np.exp(-tt(.4) * 6) * np.sin(tt(.4) * 90)), .08)
    add(E('h04') - .1, hit(1.6, 30, 120, 2), .25)                                                    # "There was no heater."
    # OUTSIDE: a door; crickets; a highway very far off; the lamps buzzing
    add(S('h05') + .1, door(), .3)
    seg(S('h05'), BLACK0, crickets(8), .035); seg(S('h05'), BLACK0, band(brown(10), 40, 200), .05); seg(S('h05'), S('h13') - .5, hum(6, 100), .012)
    # THE MAN: joints clicking as it crawls, nails on tarmac; the lamp stutters as it steps in; a man's ordinary footsteps
    for k in np.arange(S('h06') - .4, X_MAN, .19): add(k + rng.uniform(-.03, .03), crack(), .12); add(k + .07, step(800, 4000), .05)
    for j in range(4): add(X_MAN - .18 + j * .09, flick(), .3)
    add(X_MAN - .1, norm(band(noise(.5), 30, 300) * np.exp(-tt(.5) * 6)), .2)
    for k in np.arange(X_MAN + .2, S('h08'), .55): add(k, step(), .12)
    # THE WOMAN: a slow drag; the neck snapping straight; then heels
    for k in np.arange(S('h08') - .5, X_WOM, .7): add(k, norm(band(noise(.4), 200, 1500) * np.sin(np.pi * tt(.4) / .4)), .04)
    for j in range(4): add(X_WOM - .18 + j * .09, flick(), .25)
    for j in range(3): add(X_WOM + .02 + j * .05, crack(), .5)
    add(X_WOM + .05, snap(), .35)
    for k in np.arange(X_WOM + .4, S('h09'), .5): add(k, step(900, 4000), .08)
    # THE BOY: a long creak as he shrinks back to size; small quick steps; a child's hum? no: just the wave, and silence
    for j in range(4): add(X_BOY - .18 + j * .09, flick(), .25)
    L = .5; add(X_BOY - .05, norm(band(np.sin(2 * np.pi * np.cumsum(300 - 220 * tt(L) / L) / SR) + .4 * noise(L), 100, 2000) * np.sin(np.pi * tt(L) / L)), .2)
    for k in np.arange(X_BOY + .3, S('h10'), .36): add(k, step(), .08)
    # THEY ALL HAD KEYS: three doors, one after another
    for j in range(3): add(S('h10') + .2 + j * .7, door(), .3)
    # THE RAIL: her grip, the paint crackling off; a heartbeat starts
    add(S('h11') + .3, norm(band(noise(1.6), 2000, 8000) * (rng.random(int(1.6 * SR)) > .995)), .3)
    k, bpm = S('h11'), 72
    while k < E('h15') + .4:
        for o, g in ((0, 1), (.16, .6)): add(k + o, hit(.12, 30, 120, 25), .3 * g)
        k += 60 / bpm; bpm = min(140, bpm + 3)
    # DOWN: metal stairs ringing under her feet, then grass
    for j in range(10): add(S('h12') + j * .18, clang(), .1)
    for k in np.arange(S('h12') + 1.9, S('h13') - .5, .42): add(k, step(80, 1200), .1)
    # THE HOLE: wet earth giving way, a breath that isn't hers; a drone that rises
    L = E('h13') + 1.0 - (S('h13') - .5); t = tt(L)
    add(S('h13') - .5, norm(band(brown(L), 40, 400) * (.5 + .5 * np.sin(t * 2.1))), .2)
    for j in range(5): add(S('h13') + .3 + j * .8, norm(band(noise(.9), 100, 900) * np.sin(np.pi * tt(.9) / .9) ** 2), .12)
    L = BLACK0 - (S('h13') - .5); t = tt(L); add(S('h13') - .5, norm(np.sin(2 * np.pi * np.cumsum(32 + 26 * (t / L) ** 2) / SR) * (.3 + .7 * (t / L))), .2)
    # RUN: her feet, her breath
    for k in np.arange(S('h14'), S('h15') + .1, .17): add(k, step(80, 1500), .22)
    for k in np.arange(S('h14'), S('h15'), .34): add(k, norm(band(noise(.25), 500, 3000) * np.sin(np.pi * tt(.25) / .25)), .05)
    # SHE WAS ALREADY THERE: everything stops dead; a low hit as the face is seen
    add(S('h15') + .45, hit(2.0, 20, 300, 2), .8); add(S('h15') + .45, snap(), .25)
    # voices
    for name, l in LAY.items():
        if name == 'END': continue
        p = os.path.join(VO, name + '.wav')
        if name == 'd01':                                                                            # her voice, wrong: doubled, one low, one high, close and dry
            lo = load(p, 'asetrate=44100*0.88,aresample=48000,atempo=1.136'); hi = load(p, 'asetrate=44100*1.1,aresample=48000,atempo=0.909'); L = max(len(lo), len(hi))
            x = np.zeros(L + 1200, np.float32); x[:len(lo)] += lo; x[600:600 + len(hi)] += hi * .55; x = verb(x, .12, .25); add(l['offset'], x, .9)
        else: add(l['offset'], load(p), 1.0)
    # THE SIGN AGAIN: the buzz; NO clicking on
    seg(SIGN0, DUR, hum(2, 120), .04); add(DUR - 1.1, flick(), .4); add(DUR - 1.1, hit(.3, 200, 2000, 20), .15)
    m = m[:n]
    a, b = int(BLACK0 * SR), int((S('d01') - .1) * SR); m[a:b] *= np.linspace(1, 0, b - a) ** 4 if b > a else 1     # the black: the world drains away before she speaks
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
