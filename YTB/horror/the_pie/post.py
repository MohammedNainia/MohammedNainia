"""THE PIE : finish the render (silent) into the final reel: hook, captions, narration, the other voices, sound.
    python post.py                  reads raw.mp4 -> the_pie_1080x1920.mp4
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)"""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1080, 1920, 30, 84.5
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
HOOK = ['I SHOULD\'VE', 'NEVER GONE', 'TO HER HOUSE.']
PHONE = [(27.0, 31.5, 'selfie'), (34.0, 37.4, 'photo'), (60.5, 67.0, 'selfie')]
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
    def brown(sec):
        x = np.cumsum(rng.standard_normal(int(sec * SR))).astype(np.float32); x -= np.convolve(x, np.ones(3000) / 3000, 'same'); return x / (np.abs(x).max() + 1e-6)
    def verb(x, amt=.3, dec=.35):
        ir = rng.standard_normal(int(dec * SR)).astype(np.float32) * np.exp(-tt(dec) * 6 / dec); ir /= np.abs(ir).sum() / 8
        return (x + amt * np.convolve(x, ir)[:len(x)]).astype(np.float32)
    def seg(a, b, x, g):
        L = int((b - a) * SR); y = np.resize(x, L).astype(np.float32); fe = min(L // 3, int(.3 * SR)); y[:fe] *= np.linspace(0, 1, fe); y[-fe:] *= np.linspace(1, 0, fe); add(a, y, g)
    # rooms: night street (crickets), warm house (oven hum, fridge), the night house (a clock, almost nothing), morning (birds)
    t = tt(8); cr = (np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 18 * t) > .3) * (np.sin(2 * np.pi * .7 * t) > 0)).astype(np.float32)
    seg(0, 3.4, cr, .012); seg(83.6, DUR, cr, .012)
    hum = (np.sin(2 * np.pi * 60 * tt(30)) * .5 + brown(30) * .5).astype(np.float32)
    seg(3.4, 37.4, hum, .02)
    tick = band(rng.standard_normal(int(.02 * SR)).astype(np.float32), 2000, 6000) * np.exp(-tt(.02) * 200)
    for k in np.arange(37.6, 73.6, 1.0): add(k, tick, .05)
    for k in np.arange(75.2, 83.6, .37):
        f0 = 2600 + rng.random() * 1800; tb = tt(.12); add(k + rng.random() * .2, (np.sin(2 * np.pi * (f0 + 900 * tb) * tb) * np.sin(np.pi * tb / .12)).astype(np.float32), .03)
    # heavy, slow footsteps with creaking boards
    def step(g=1.0):
        x = band(rng.standard_normal(int(.18 * SR)).astype(np.float32), 50, 500) * np.exp(-tt(.18) * 22)
        cr = np.sin(2 * np.pi * np.cumsum(220 + 60 * np.sin(tt(.35) * 9)) / SR) * np.exp(-tt(.35) * 6) * .35
        y = np.zeros(int(.35 * SR), np.float32); y[:len(x)] += x; y += cr.astype(np.float32); return y * g
    for k in [16.8, 17.9, 19.0, 20.1]: add(k, step(), .5)                     # across the hallway, behind the sofa
    for k in [58.0, 58.9]: add(k, step(), .55)                                 # behind Haru in the hallway
    for k in [61.6, 63.8, 65.6]: add(k, step(), .45 + .1 * (k > 64))
    for k in np.arange(48.6, 58.0, .62): add(k, band(rng.standard_normal(int(.07 * SR)).astype(np.float32), 300, 2500) * np.exp(-tt(.07) * 50), .08)   # Haru's bare feet
    # the spoon in the bowl, the oven tick, the TV murmur
    for k in np.arange(11.6, 15.2, .45 * 1.1): add(k, band(rng.standard_normal(int(.05 * SR)).astype(np.float32), 1500, 6000) * np.exp(-tt(.05) * 60), .06)
    seg(16, 27, band(rng.standard_normal(int(11 * SR)).astype(np.float32), 300, 3000) * (.5 + .5 * np.sin(2 * np.pi * 3 * tt(11))), .008)
    # the selfie: shutter; the thing crossing: a fast whoosh
    sh = band(rng.standard_normal(int(.06 * SR)).astype(np.float32), 1000, 8000) * np.exp(-tt(.06) * 70); add(29.6, sh, .3); add(29.68, sh, .2)
    wt = tt(.5); wh = band(rng.standard_normal(len(wt)).astype(np.float32), 200, 3000) * np.sin(np.pi * wt / .5); add(29.8, wh / np.abs(wh).max(), .25)
    # bedroom door creak, heartbeat in the hallway, the breath, the rush, then nothing
    t = tt(1.0); f = 240 + 80 * np.sin(t * 5); creak = (np.sin(2 * np.pi * np.cumsum(f) / SR) * (rng.random(len(t)) > .45) * np.sin(np.pi * t / t[-1])).astype(np.float32)
    add(48.6, creak, .05); add(31.4, creak * .6, .03)
    hb = load(os.path.join(SFX, 'synth_heartbeat.wav')); k = 60.5
    while k < 72.6: add(k, hb, .25 + (k - 60) * .02); k += .85 - (k - 60) * .03
    g = verb(load(os.path.join(VO, 'g01.mp3'), 'asetrate=44100*0.82,aresample=44100'), .4, .5)
    add(66.6, band(g, 80, 4000), .9)
    t = tt(1.0); roar = band(rng.standard_normal(len(t)).astype(np.float32), 40, 6000) * (t ** 2); add(72.6, roar / np.abs(roar).max(), .8)
    def drone(sec): t = tt(sec); return ((np.sin(2 * np.pi * 49 * t) + .5 * np.sin(2 * np.pi * 73.4 * t) + .3 * brown(sec)) * np.minimum(1, t / 3) * np.minimum(1, (sec - t) / .5)).astype(np.float32)
    add(51, drone(22), .05)
    # voices
    for name, l in LAY.items():
        x = load(os.path.join(VO, name + '.mp3'))
        if name[0] == 's': x = verb(x, .12, .25)
        add(l['offset'], x, 1.0 if name[0] == 'h' else 1.15)
    m = m[:n]
    m[int(73.6 * SR):int(75.0 * SR)] *= .05
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
    out = os.path.join(HERE, 'the_pie_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
