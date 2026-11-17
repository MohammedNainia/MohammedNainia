"""The Keeper's Rules, Part 2 "The Light Stopped": finish the GPU render (silent) into the final 16:9 video:
hook, captions (her double's line in pink italic), the PART 3 card, narration, sound.
    python post.py                   reads raw.mp4 (or raw_a.mp4 + raw_b.mp4) -> keeper_part2_1920x1080.mp4
    python post.py --frames 0,4300   check frames in check/"""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1920, 1080, 30, 151.0
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_I = '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'
if not os.path.exists(FONT_I): FONT_I = FONT
if not os.path.exists(FONT): FONT = FONT_I = 'C:/Windows/Fonts/arialbd.ttf'
WORDS = json.load(open(os.path.join(VO, 'words.json'))); LAY = {l['name']: l for l in json.load(open(os.path.join(VO, 'layout.json')))}
args = sys.argv[1:]
T = {'dark': 9.4, 'torch': 38.2, 'hatch': 41.3, 'coat': 57.0, 'them': 65.0, 'lever': 104.0, 'relit': 105.2, 'turn': 145.2, 'cut': 146.4}
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

CHUNKS, i = [], 0
while i < len(WORDS):
    n = min(3, len(WORDS) - i) if len(WORDS) - i != 4 else 2
    for k in range(n - 1):
        if WORDS[i + k][0][-1:] in ',.?!"' or WORDS[i + k][3] != WORDS[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(WORDS[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 56); f_capi = ImageFont.truetype(FONT_I, 56); f_hook = ImageFont.truetype(FONT, 70); f_part = ImageFont.truetype(FONT, 150); f_sub = ImageFont.truetype(FONT, 52)
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < .12 else max(0, 1 - (t - .12) / .3) if t < .42 else 0
    if ha > 0:
        d.text((W // 2, 120), "THE KEEPER'S RULES  ·  PART 2", font=f_hook, fill=(255, 255, 255, int(255 * ha)), stroke_width=7, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
        d.text((W // 2, 205), 'Someone was still turning the light.', font=f_sub, fill=(230, 200, 120, int(255 * ha)), stroke_width=6, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if .42 <= t < T['cut']:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .3:
                other = ch[0][3]
                d.text((W // 2, H - 140), ' '.join(w for w, *_ in ch), font=f_capi if other else f_cap, fill=(255, 205, 220) if other else (255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    if t >= T['cut'] + .4:
        k = ease((t - (T['cut'] + .4)) / .8)
        d.text((W // 2, H // 2 - 50), 'PART 3', font=f_part, fill=(235, 230, 220, int(255 * k)), anchor='mm')
        d.text((W // 2, H // 2 + 80), 'THE LAST KEEPER', font=f_sub, fill=(200, 60, 50, int(255 * k)), anchor='mm')
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound design
SR = 48000
def load(p, extra=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', p] + (['-af', extra] if extra else []) + ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).copy()
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + 2 * SR, np.float32); rng = np.random.default_rng(22)
    def add(t, x, g): i = int(t * SR); m[i:i + len(x)] += x[:len(m) - i] * g
    def tt(sec): return np.arange(int(sec * SR)) / SR
    def brown(sec): x = np.cumsum(rng.standard_normal(int(sec * SR))).astype(np.float32); x -= np.convolve(x, np.ones(3000) / 3000, 'same'); return x / (np.abs(x).max() + 1e-6)
    def band(x, lo, hi): X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x)).astype(np.float32)
    def verb(x, sec=1.6, wet=.4):                                    # the stone tower: a long, cold reverb
        ir = rng.standard_normal(int(sec * SR)).astype(np.float32) * np.exp(-np.arange(int(sec * SR)) / SR * 3.5); ir[0] = 1 / wet
        y = np.convolve(x, ir * wet)[:len(x) + int(sec * SR)]; return (y / (np.abs(y).max() + 1e-6) * np.abs(x).max()).astype(np.float32)
    # the sea all around: slow swells (louder outside, muffled inside the tower)
    sea = band(rng.standard_normal(n).astype(np.float32), 60, 900); sea /= np.abs(sea).max()
    sw = .55 + .45 * np.sin(2 * np.pi * np.arange(n) / SR / 7.0) ** 2
    inside = np.ones(n, np.float32) * .35
    for a, b in [(1.0, 4.6), (8.23, 13.4), (T['relit'], 110.66)]: inside[int(a * SR):int(b * SR)] = 1.0
    m[:n] += sea * sw * inside * .05
    t = tt(DUR); wind = band(rng.standard_normal(len(t)).astype(np.float32), 300, 1800); wind /= np.abs(wind).max(); add(0, wind * (.5 + .5 * np.sin(t * .4)) ** 2, .015)
    # the lamp's hum and motor: on, a click and silence at "dark", back with a clunk and a whir at "relit"
    hum = (np.sin(2 * np.pi * 100 * t) * .5 + np.sin(2 * np.pi * 150 * t) * .25).astype(np.float32)
    on = np.ones(n, np.float32); on[int(T['dark'] * SR):int(T['relit'] * SR)] = 0
    m[:n] += hum[:n] * on * .012
    tc = tt(.08); click = (rng.standard_normal(len(tc)) * np.exp(-tc * 70)).astype(np.float32)
    add(T['dark'], click, .5); add(T['dark'] + .05, band(rng.standard_normal(int(.6 * SR)).astype(np.float32), 40, 300) * np.exp(-tt(.6) * 5), .3)
    clunk = (band(rng.standard_normal(int(.4 * SR)).astype(np.float32), 50, 700) * np.exp(-tt(.4) * 9)).astype(np.float32)
    add(T['lever'] + .5, clunk / np.abs(clunk).max(), .6)
    tw = tt(5); whir = (np.sin(2 * np.pi * np.cumsum(40 + 80 * np.minimum(1, tw / 1.5)) / SR) * .6 + band(rng.standard_normal(len(tw)).astype(np.float32), 200, 1500) * .4) * np.minimum(1, tw / 1.0)
    add(T['lever'] + .6, (whir / np.abs(whir).max()).astype(np.float32), .05)
    # the torch clicking on, the hatch, footsteps on iron steps (down, between them; up, counting), the 65th step
    add(T['torch'], click, .3)
    t2 = tt(1.2); creak = (np.sin(2 * np.pi * np.cumsum(220 + 60 * np.sin(t2 * 5)) / SR) * (rng.random(len(t2)) > .5) * np.sin(np.pi * t2 / 1.2)).astype(np.float32); add(T['hatch'], creak, .05)
    ts = tt(.22); step = (band(rng.standard_normal(len(ts)).astype(np.float32), 120, 2500) * np.exp(-ts * 22)).astype(np.float32); step /= np.abs(step).max()
    ring = (np.sin(2 * np.pi * 740 * ts) * np.exp(-ts * 18)).astype(np.float32)
    def steps(a, b, dt, g):
        k = a
        while k < b: add(k, verb(step + ring * .3, .8, .3), g * (.8 + .4 * rng.random())); k += dt * (.9 + .2 * rng.random())
    steps(43.9, 56.6, .62, .09); steps(80.3, 95.0, .75, .07); steps(117.8, 125.2, .45, .09)
    add(125.6, verb(step + ring * .3, 1.6, .5), .2)                                                      # sixty-five
    # their heads turning: a soft creak of wool and old leather while she passes
    for k in np.arange(87.0, 94.0, 1.4): add(k, band(rng.standard_normal(int(.5 * SR)).astype(np.float32), 300, 1200) * np.sin(np.pi * tt(.5) / .5), .02)
    # heartbeat when she sees them, and at the end
    hb = load(os.path.join(SFX, 'synth_heartbeat.wav'))
    for a, b in [(64.4, 72.0), (128.5, 146.2)]:
        k = a
        while k < b: add(k, hb, .28); k += .85 - .3 * (k - a) / (b - a)
    # a low drone from the top of the stairs to the cut, then nothing; a low tone under the PART 3 card
    t3 = tt(18.0); dr = (np.sin(2 * np.pi * 49 * t3) + .5 * np.sin(2 * np.pi * 73.4 * t3) + .3 * brown(18.0)) * np.minimum(1, t3 / 6)
    add(128.4, dr.astype(np.float32), .07)
    t4 = tt(4.2); tone = (np.sin(2 * np.pi * 41.2 * t4) + .3 * np.sin(2 * np.pi * 82.4 * t4)) * np.minimum(1, t4 / .8) * np.minimum(1, (4.2 - t4) / 1.5); add(146.8, tone.astype(np.float32), .08)
    # voices: Haru; her double's line close and dry, a breath of the tower behind it
    for name, l in LAY.items():
        x = load(os.path.join(VO, name + '.mp3'))
        if name == 'l19': add(l['offset'], verb(x, .9, .22), 1.0)
        else: add(l['offset'], x, 1.0)
    m = m[:n]; m[int(T['cut'] * SR):int(146.8 * SR)] *= 0
    m /= max(1.0, np.abs(m).max() / .95)
    with wave.open(path, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((m * 32767).astype('<i2').tobytes())

def frames():
    srcs = [os.path.join(HERE, f) for f in (['raw.mp4'] if os.path.exists(os.path.join(HERE, 'raw.mp4')) else ['raw_a.mp4', 'raw_b.mp4'])]
    for s in srcs:
        cap = cv2.VideoCapture(s)
        while True:
            ok, fr = cap.read()
            if not ok: break
            yield fr

if __name__ == '__main__':
    if '--frames' in args:
        want = [int(x) for x in args[args.index('--frames') + 1].split(',')]; os.makedirs(os.path.join(HERE, 'check'), exist_ok=True)
        for i, fr in enumerate(frames()):
            if i in want: cv2.imwrite(os.path.join(HERE, 'check', f'c{i:04d}.png'), overlay(fr, i / FPS))
            if i > max(want): break
        sys.exit()
    wav = os.path.join(HERE, 'mix.wav'); mix(wav)
    if '--mix' in args: sys.exit()
    meas = json.loads(subprocess.run(['ffmpeg', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                                     capture_output=True, text=True).stderr.split('[Parsed_loudnorm')[-1].split('\n', 1)[1])
    LN = ('loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s'
          % (meas['input_i'], meas['input_tp'], meas['input_lra'], meas['input_thresh'], meas['target_offset']))
    out = os.path.join(HERE, 'keeper_part2_1920x1080.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '18', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    k = 0
    for fr in frames():
        if k >= int(DUR * FPS): break
        ff.stdin.write(overlay(fr, k / FPS).tobytes()); k += 1
    while k < int(DUR * FPS): ff.stdin.write(np.zeros((H, W, 3), np.uint8).tobytes()); k += 1
    ff.stdin.close(); ff.wait(); print('saved', out)
