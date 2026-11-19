"""THE TOOTH FAIRY : finish the render (silent) into the final reel: hook, captions, narration, the other voices, sound.
    python post.py                  reads raw.mp4 -> tooth_fairy_1080x1920.mp4
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)"""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1080, 1920, 30, 88.6
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
f_cap = ImageFont.truetype(FONT, 66); f_oth = ImageFont.truetype(FONT_I, 66); f_hook = ImageFont.truetype(FONT, 84)
HOOK = ['THE TOOTH FAIRY', 'TOOK ALL', 'MY TEETH.']
PHONE = []
f_ui = ImageFont.truetype(FONT, 34)
def phone_frame(im, d, kind, t):
    """The phone in Haru's hand: a black bezel round the picture, a notch, the camera UI (or the gallery for the photo)."""
    m = 70; r = 70
    mask = Image.new('L', (W, H), 255); md = ImageDraw.Draw(mask); md.rounded_rectangle((m, m + 80, W - m, H - m - 80), r, fill=0)
    im.paste((8, 8, 10), (0, 0, W, H), mask)
    d.rounded_rectangle((m, m + 80, W - m, H - m - 80), r, outline=(40, 40, 46), width=6)
    d.rounded_rectangle((W // 2 - 70, m + 100, W // 2 + 70, m + 130), 15, fill=(8, 8, 10))
    if kind == 'selfie':
        d.ellipse((W // 2 - 56, H - m - 260, W // 2 + 56, H - m - 148), outline=(255, 255, 255), width=8)
        if abs(t - 29.6) < .08: d.rectangle((m, m + 80, W - m, H - m - 80), fill=(255, 255, 255, 140))     # the shutter flash
        d.text((W // 2, m + 180), 'SELFIE', font=f_ui, fill=(255, 210, 60), anchor='mm')
    else:
        d.text((m + 60, m + 175), '< Photos', font=f_ui, fill=(255, 255, 255), anchor='lm')
        d.text((W - m - 60, m + 175), '11:52 PM', font=f_ui, fill=(200, 200, 200), anchor='rm')
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    for a, b, kind in PHONE:
        if a <= t < b: phone_frame(im, d, kind, t)
    ha = 1.0 if t < 3.0 else max(0, 1 - (t - 3.0) / .35) if t < 3.35 else ease((t - (DUR - .55)) / .2) if t > DUR - .55 else 0
    if ha > 0:
        for k, line in enumerate(HOOK):
            col = (255, 214, 90) if k == 2 else (255, 255, 255)
            d.text((W // 2, 300 + k * 112), line, font=f_hook, fill=col + (int(255 * ha),), stroke_width=9, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if 3.35 <= t < DUR - .6:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .3:
                oth = ch[0][3]; s = ' '.join(w for w, _, _, _ in ch)
                d.text((W // 2, 1440), s, font=f_oth if oth else f_cap, fill=(255, 205, 220) if oth else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound
# Real recordings go in sfx/ (from Freesound once the key works): any file there named like a cue below replaces the synthesized one.
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
    n = int(DUR * SR); m = np.zeros(n + 4 * SR, np.float32); rng = np.random.default_rng(41)
    def add(t, x, g): i = int(t * SR); m[i:i + len(x)] += x[:max(0, len(m) - i)] * g
    def tt(sec): return np.arange(int(sec * SR)) / SR
    def band(x, lo, hi):
        X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x)).astype(np.float32)
    def noise(sec): return rng.standard_normal(int(sec * SR)).astype(np.float32)
    def brown(sec):
        x = np.cumsum(noise(sec)).astype(np.float32); x -= np.convolve(x, np.ones(3000) / 3000, 'same'); return x / (np.abs(x).max() + 1e-6)
    def verb(x, amt=.3, dec=.35):
        ir = noise(dec) * np.exp(-tt(dec) * 6 / dec); ir /= np.abs(ir).sum() / 8
        return (x + amt * np.convolve(x, ir)[:len(x)]).astype(np.float32)
    def seg(a, b, x, g):
        L = int((b - a) * SR); y = np.resize(x, L).astype(np.float32); fe = min(L // 3, int(.3 * SR)); y[:fe] *= np.linspace(0, 1, fe); y[-fe:] *= np.linspace(1, 0, fe); add(a, y, g)
    def norm(x): return (x / (np.abs(x).max() + 1e-6)).astype(np.float32)
    # ---- rooms: the night house (room tone), the dinner lamp hum, dawn, the bathroom bulb hum
    rt = real('room_tone'); rt = rt if rt is not None else norm(band(brown(10), 40, 900))
    seg(0, 68.95, rt, .05); seg(80.9, DUR, rt, .04)
    seg(3.4, 11.2, norm(np.sin(2 * np.pi * 60 * tt(8)) * .5 + band(noise(8), 100, 400) * .3), .015)
    hum = real('bulb_buzz'); hum = hum if hum is not None else norm(np.sin(2 * np.pi * 120 * tt(6)) + .3 * np.sin(2 * np.pi * 240 * tt(6)) + .1 * band(noise(6), 2000, 6000))
    seg(57.0, 68.95, hum, .03)
    # ---- the drone: creeps in at night, swells to "Open wide"
    dr = real('drone')
    if dr is None: t = tt(40); dr = norm(np.sin(2 * np.pi * 41 * t) + .6 * np.sin(2 * np.pi * 61.5 * t + np.sin(t * .3)) + .4 * brown(40))
    L = int((72.8 - 35.0) * SR); y = np.resize(dr, L) * np.linspace(.1, 1, L) ** 1.6; add(35.0, y, .12)
    # ---- teeth clicking, like teeth shaken in a jar
    cl = real('teeth_rattle')
    def click(): x = band(noise(.025), 2500, 9000) * np.exp(-tt(.025) * 180); return x.astype(np.float32)
    for k in np.arange(36.0, 41.4, .09):
        if rng.random() < .55: add(k + rng.random() * .05, click(), .12 * (.5 + .5 * ((k - 36) / 5.4)))
    if cl is not None: add(37.6, verb(cl, .2), .25)
    # ---- the door creaks open; slow, heavy steps
    def creak(sec=1.2, f0=230):
        t = tt(sec); f = f0 + 70 * np.sin(t * 4.3) + 30 * np.sin(t * 11)
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * (rng.random(len(t)) > .4) * np.sin(np.pi * t / t[-1])).astype(np.float32)
    dc = real('door_creak'); add(37.0, dc if dc is not None else band(creak(1.6), 150, 3000), .12)
    st = real('creature_steps')
    def step(): x = band(noise(.16), 50, 600) * np.exp(-tt(.16) * 26); y = np.zeros(int(.4 * SR), np.float32); y[:len(x)] += x; y += band(creak(.4, 300), 200, 2000) * .25; return y
    for k in [38.4, 39.5, 40.5]: add(k, step(), .35)
    if st is not None: add(38.3, st, .35)
    # ---- fingers sliding under the pillow (cloth)
    for k in np.arange(42.0, 45.6, .5): add(k, band(noise(.45), 1500, 7000) * np.sin(np.pi * tt(.45) / .45), .03)
    # ---- heartbeat from the fingers to the eyes
    def beat():
        t = tt(.35); x = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 18) + .6 * np.sin(2 * np.pi * 45 * t) * np.exp(-np.maximum(0, t - .16) * 18) * (t > .16)
        return x.astype(np.float32)
    k = 43.0
    while k < 50.4: add(k, beat(), .35); k += .78 - (k - 43) * .03
    # ---- the reveal sting (eyes open), low and close
    t = tt(2.2); add(47.6, norm(band(noise(2.2), 30, 400) * np.exp(-t * 1.2) + np.sin(2 * np.pi * 38 * t) * np.exp(-t * .9)), .45)
    # ---- she runs (bare feet), the sizzle at the light's edge
    rn = real('barefoot_run')
    if rn is not None: add(50.7, rn[:int(2.6 * SR)], .35)
    else:
        for k in np.arange(50.75, 53.2, .27): add(k, band(noise(.06), 200, 2500) * np.exp(-tt(.06) * 60), .25)
    t = tt(1.4); sz = band(noise(1.4), 3000, 12000) * (rng.random(len(t)) > .2) * np.exp(-t * 1.5); add(55.1, sz.astype(np.float32), .18)
    t = tt(.8); add(55.1, norm(band(noise(.8), 80, 1200) * np.exp(-t * 3)), .2)                  # a hiss of pain from it
    # ---- the bathroom lock; the taps all night
    lk = real('lock'); lck = lk if lk is not None else band(noise(.05), 800, 6000) * np.exp(-tt(.05) * 90)
    add(58.2, lck, .3); add(58.3, lck, .2)
    tp = real('door_taps')
    def tap(): x = band(noise(.06), 150, 3500) * np.exp(-tt(.06) * 70); return verb(x, .15, .2)
    for k in [63.4, 64.3, 64.9, 66.0, 66.4, 67.2]: add(k, tap(), .5)
    if tp is not None: add(63.35, verb(tp, .15), .3)
    # ---- the flicker buzz, then every light goes out: a thunk and dead silence
    for k in np.arange(67.4, 68.9, .25): add(k + rng.random() * .1, band(noise(.08), 100, 4000) * np.exp(-tt(.08) * 30), .1)
    po = real('power_off'); add(68.9, po if po is not None else norm(band(noise(.4), 30, 300) * np.exp(-tt(.4) * 9)), .5)
    # ---- in the dark: the lock turns by itself; the door creaks; the creature's voice
    add(70.2, lck, .35); add(70.35, lck, .25)
    add(70.8, band(creak(1.0, 180), 120, 2500), .14)
    g = verb(load(os.path.join(VO, 'c01.mp3'), 'asetrate=44100*0.78,aresample=44100'), .45, .6)
    add(LAY['c01']['offset'] - .1, band(g, 70, 5000), 1.25)
    # ---- the flicker on top of her: three electric zaps
    for k in [73.2, 73.62, 73.85]: add(k, band(noise(.12), 60, 6000) * np.exp(-tt(.12) * 25), .35)
    # ---- one by one: a wet pull, then a coin on the tile. Faster. Her muffled scream through it.
    cn = real('coin_tile')
    def coin():
        t = tt(.5); x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in [(3150, 9), (4720, 12), (6900, 16), (8350, 20)])
        hit = band(noise(.01), 2000, 9000) * np.exp(-tt(.01) * 400); x[:len(hit)] += hit * 2; return norm(x)
    pull = real('tooth_pull')
    def wet(): x = band(noise(.14), 200, 2500) * np.sin(np.pi * tt(.14) / .14) * (1 + .6 * np.sin(2 * np.pi * 37 * tt(.14))); return norm(x)
    sc = load(os.path.join(VO, 'x01_muffled.wav'))
    add(74.55, sc, .7); add(77.4, sc[int(1.2 * SR):], .5)
    k, gap = 74.9, .8
    while k < 80.3:
        add(k, pull if pull is not None else wet(), .14); add(k + .22, cn if cn is not None else coin(), .22 * (.8 + .4 * rng.random()))
        k += gap; gap = max(.16, gap * .82)
    # ---- morning: the coins shift; a bird far away. Night again: crickets as Mum sets the glass down.
    add(81.0, norm(sum(coin()[:int(.3 * SR)] * (rng.random() * .5 + .5) for _ in range(1))), .08)
    for k in [81.4, 83.0]: t = tt(.3); add(k, (np.sin(2 * np.pi * (3200 + 900 * np.sin(t * 40)) * t) * np.sin(np.pi * t / .3)).astype(np.float32), .015)
    t = tt(4); cr = (np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 18 * t) > .3) * (np.sin(2 * np.pi * .7 * t) > 0)).astype(np.float32); seg(85.2, DUR, cr, .008)
    add(86.1, band(noise(.05), 1500, 6000) * np.exp(-tt(.05) * 50), .15)                       # the glass on the wood
    # ---- voices (Mum in the room, the creature handled above)
    for name, l in LAY.items():
        if name == 'c01': continue
        x = load(os.path.join(VO, name + '.mp3'))
        if name == 'm01': x = verb(x, .1, .25)
        add(l['offset'], x, 1.0 if name[0] == 'h' else 1.1)
    m = m[:n]
    m[int(68.95 * SR):int(70.1 * SR)] *= .02                                                     # true silence after the lights die
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
    out = os.path.join(HERE, 'tooth_fairy_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
