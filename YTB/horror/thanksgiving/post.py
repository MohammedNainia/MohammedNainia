"""THANKSGIVING : finish the render (silent) into the final reel: hook, captions, narration, the other voices, sound.
    python post.py                  reads raw.mp4 -> thanksgiving_1080x1920.mp4
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)"""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1080, 1920, 30, 93.4
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
f_small = ImageFont.truetype(FONT_I, 44); f_cap = ImageFont.truetype(FONT, 66); f_oth = ImageFont.truetype(FONT_I, 66); f_hook = ImageFont.truetype(FONT, 84)
HOOK = ['MY FAMILY FATTENED ME', 'FOR THE THING', 'UNDER THE TABLE.']
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
                if LAY['t01']['start'] - .1 <= t <= LAY['t01']['end'] + .3:
                    d.text((W // 2, 1530), '(is she ready?)', font=f_small, fill=(255, 205, 220, 220), stroke_width=5, stroke_fill=(0, 0, 0, 220), anchor='mm')
                d.text((W // 2, 1440), s, font=f_oth if oth else f_cap, fill=(255, 205, 220) if oth else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound (real recordings dropped into sfx/ replace the synthesized cues)
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
    n = int(DUR * SR); m = np.zeros(n + 4 * SR, np.float32); rng = np.random.default_rng(51)
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
    def clink(f0=2600):
        t = tt(.35); x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in [(f0, 14), (f0 * 1.52, 18), (f0 * 2.31, 24)]); return norm(x)
    # room: a warm house at night (low hum), a clock ticking under everything
    rt = real('room_tone'); rt = rt if rt is not None else norm(band(brown(10), 40, 700))
    seg(0, 77.6, rt, .05); seg(80.6, DUR, rt, .05)
    tick = band(noise(.02), 2000, 6000) * np.exp(-tt(.02) * 200)
    for k in np.arange(.5, 77.5, 1.0): add(k, tick, .03)
    for k in np.arange(80.8, DUR, 1.0): add(k, tick, .03)
    # Haru eating: fork on the plate, only hers (nobody else eats)
    for k in list(np.arange(1.0, 22.5, 2.42)): add(k + rng.random() * .2, clink(2400 + rng.random() * 600), .05)
    # the spoon scraping more food onto her plate
    for k in [1.2, 12.4, 13.6, 50.2, 51.0, 88.7, 89.5]: add(k, band(noise(.35), 1200, 6000) * np.sin(np.pi * tt(.35) / .35), .05)
    # under the table: slow wet breathing, the cloth stirring
    def breath(sec=1.6):
        t = tt(sec); return norm(band(noise(sec), 80, 900) * np.sin(np.pi * t / sec) ** 2)
    for k in np.arange(23.3, 28.3, 1.7): add(k, breath(), .12)
    for k in np.arange(0, 3.8, 1.9): add(k, breath(), .05)
    add(24.0, band(noise(3), 1500, 7000) * np.sin(np.pi * tt(3) / 3) * .5, .05)                   # fingers over her sock
    # the drone: under it all from the ankle on, swells at the tablecloth
    dr = real('drone')
    if dr is None: t = tt(55); dr = norm(np.sin(2 * np.pi * 38 * t) + .6 * np.sin(2 * np.pi * 57 * t + np.sin(t * .3)) + .4 * brown(55))
    L = int((76.4 - 23.0) * SR); y = np.resize(dr, L) * np.linspace(.1, 1, L) ** 1.7; add(23.0, y, .13)
    # Grandpa carving
    for k in np.arange(28.6, 31.6, .45): add(k, band(noise(.25), 300, 3000) * np.sin(np.pi * tt(.25) / .25), .06)
    # grace: everything hushes; a long breath from under the floor at "almost ripe"
    add(35.5, breath(2.4), .2)
    # the napkin; the food scraped back
    add(45.5, band(noise(.6), 2000, 8000) * np.sin(np.pi * tt(.6) / .6), .05)
    # she runs; the locked door rattles; chairs scrape as the family sits back down
    for k in np.arange(53.2, 55.3, .27): add(k, band(noise(.06), 200, 2500) * np.exp(-tt(.06) * 60), .25)
    for k in np.arange(55.4, 57.2, .18): add(k, band(noise(.05), 300, 3000) * np.exp(-tt(.05) * 60), .25)
    def scrape(sec=.7, f0=180):
        t = tt(sec); f = f0 + 60 * np.sin(t * 13); return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * (rng.random(len(t)) > .3) * np.sin(np.pi * t / sec))
    for k in [57.9, 58.6, 59.3]: add(k, band(scrape(), 100, 3000), .07)
    # the tablecloth rises: a low groan, plates sliding, a candle falling over
    t = tt(3); add(61.6, norm(band(noise(3), 25, 220) * (t / 3) ** 1.5), .45)
    for k in [62.4, 63.0, 63.5]: add(k, clink(1800 + rng.random() * 900), .08)
    # the thing speaks (dead language, processed take A); Grandma answers
    g = load(os.path.join(VO, 't01_trim.wav'))
    add(LAY['t01']['offset'], g, 1.15)
    # her chair dragged back on its own, nails on the floor; then black: scream, a dinner bell, knives on plates
    add(76.4, band(scrape(1.2, 140), 80, 3000), .3)
    for k in np.arange(76.6, 77.5, .12): add(k, band(noise(.06), 2500, 9000) * np.exp(-tt(.06) * 40), .1)
    sc = load(os.path.join(VO, 'x01_muffled.wav')); add(77.6, sc, .75)
    bell = real('dinner_bell')
    if bell is None: t = tt(2.5); bell = norm(sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in [(1320, 1.8), (1985, 2.4), (3110, 3.2)]))
    add(78.9, verb(bell, .3, .6), .3)
    for k in np.arange(79.4, 80.6, .23): add(k + rng.random() * .05, clink(2200 + rng.random() * 1400), .1)
    # the forks lift: a few clinks, then black. Next year: the same clock, the spoon for Mei.
    for k in [81.1, 81.4, 81.7]: add(k, clink(2800), .06)
    # voices
    for name, l in LAY.items():
        if name in ('t01', 'x01'): continue
        src = 'g01' if name == 'g04' else name
        extra = 'asetrate=44100*0.94,aresample=44100' if name[0] == 'g' else None             # Grandma, a little older
        x = load(os.path.join(VO, src + '.mp3'), extra)
        if name[0] in 'gp': x = verb(x, .1, .25)
        add(l['offset'], x, 1.0 if name[0] == 'h' else 1.1)
    m = m[:n]
    m[int(77.55 * SR):int(77.65 * SR)] *= np.linspace(1, .2, int(.1 * SR))[:len(m[int(77.55 * SR):int(77.65 * SR)])]
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
    out = os.path.join(HERE, 'thanksgiving_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
