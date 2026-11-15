"""MUM? : finish the GPU render (silent) into the final reel: hook, captions, narration, Mum's voice from downstairs, sound.
    python post.py                  reads raw.mp4 -> mum_1080x1920.mp4
    python post.py --frames 0,900   check frames in check/"""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1080, 1920, 30, 58.5
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_I = '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'
if not os.path.exists(FONT_I): FONT_I = FONT
if not os.path.exists(FONT): FONT = FONT_I = 'C:/Windows/Fonts/arialbd.ttf'
WORDS = json.load(open(os.path.join(VO, 'words.json'))); LAY = {l['name']: l for l in json.load(open(os.path.join(VO, 'layout.json')))}
args = sys.argv[1:]
RAW = os.path.join(HERE, args[args.index('--raw') + 1] if '--raw' in args else 'raw.mp4')
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

CHUNKS, i = [], 0
while i < len(WORDS):
    n = min(3, len(WORDS) - i) if len(WORDS) - i != 4 else 2
    for k in range(n - 1):
        if WORDS[i + k][0][-1:] in ',.?!' or WORDS[i + k][3] != WORDS[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(WORDS[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 64); f_mum = ImageFont.truetype(FONT_I, 64); f_hook = ImageFont.truetype(FONT, 150)
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < .12 else max(0, 1 - (t - .12) / .3) if t < .42 else ease((t - 57.95) / .2) if t > 57.95 else 0
    if ha > 0: d.text((W // 2, 420), 'Mum?', font=f_hook, fill=(255, 255, 255, int(255 * ha)), stroke_width=9, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if .42 <= t < 57.3:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .3:
                mum = ch[0][3]; s = ' '.join(w for w, _, _, _ in ch)
                d.text((W // 2, 1480), s, font=f_mum if mum else f_cap, fill=(255, 205, 220) if mum else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

SR = 48000
def load(p, extra=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', p] + (['-af', extra] if extra else []) + ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32)
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + SR, np.float32); rng = np.random.default_rng(31)
    def add(t, x, g): i = int(t * SR); m[i:i + len(x)] += x[:len(m) - i] * g
    def tt(sec): return np.arange(int(sec * SR)) / SR
    def brown(sec): x = np.cumsum(rng.standard_normal(int(sec * SR))).astype(np.float32); x -= np.convolve(x, np.ones(3000) / 3000, 'same'); return x / (np.abs(x).max() + 1e-6)
    def verb(x, sec=1.4, wet=.45):                                   # a hallway: decaying noise reverb
        ir = rng.standard_normal(int(sec * SR)).astype(np.float32) * np.exp(-np.arange(int(sec * SR)) / SR * 4.5); ir[0] = 1 / wet
        y = np.convolve(x, ir * wet)[:len(x) + int(sec * SR)]; return y / (np.abs(y).max() + 1e-6) * np.abs(x).max()
    # the house at night: low fridge hum and a slow clock
    t = tt(57.3); add(0, .5 * np.sin(2 * np.pi * 50 * t) * .3 + .4 * brown(57.3), .03)
    tick = load(os.path.join(SFX, 'synth_tick.wav'))
    for k in np.arange(.5, 57.3, 1.0): add(k, tick, .05)
    # narration
    for name, l in LAY.items():
        if name[0] == 'n': add(l['offset'], load(os.path.join(VO, name + '.mp3')), 1.0)
    # Mum, from downstairs: muffled and roomy; the second time a little too low, a little too slow
    m1 = load(os.path.join(VO, 'm1.mp3'), 'highpass=f=250,lowpass=f=2600'); add(LAY['m1']['offset'], verb(m1), .62)
    m2 = load(os.path.join(VO, 'm2.mp3'), 'asetrate=44100*0.94,aresample=44100,atempo=1.0,highpass=f=220,lowpass=f=3000'); add(LAY['m2']['offset'], verb(m2, 1.8, .5), .72)
    # the phone buzzes, the texts arrive
    t = tt(.32); bz = np.sign(np.sin(2 * np.pi * 170 * t)) * .5 * np.sin(np.pi * t / .32)
    add(22.3, bz, .25); add(22.75, bz, .25)
    t = tt(.5); ping = (np.sin(2 * np.pi * 1760 * t) + .5 * np.sin(2 * np.pi * 2640 * t)) * np.exp(-t * 9)
    add(24.15, ping, .12); add(48.45, ping * .7, .1); add(53.6, ping, .14)
    # footsteps down, heartbeat while she stares, running back up, the slam and the lock
    thud = load(os.path.join(SFX, 'synth_thud.wav'))
    for k in np.arange(17.0, 21.6, .62): add(k, thud, .16)
    hb = load(os.path.join(SFX, 'synth_heartbeat.wav')); k = 31.9
    while k < 42.2: add(k, hb, .32); k += .82 - .3 * (k - 31.9) / 10.3
    for k in np.arange(42.35, 44.0, .22): add(k, thud, .3)
    add(44.0, thud, 1.0)
    t = tt(.08); click = rng.standard_normal(len(t)) * np.exp(-t * 90); add(44.7, click, .5); add(44.82, click, .4)
    for k in np.arange(46.8, 48.3, .09): add(k + rng.random() * .03, click * .5, .25)                     # typing
    # the handle: a slow metal creak, then dead silence on the black
    t = tt(1.1); f = 380 + 120 * np.sin(t * 6); cr = np.sin(2 * np.pi * np.cumsum(f) / SR) * (rng.random(len(t)) > .4) * np.sin(np.pi * t / t[-1])
    add(56.6, cr, .06)
    m = m[:n]; m[int(57.3 * SR):int(57.9 * SR)] *= 0
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
    meas = json.loads(subprocess.run(['ffmpeg', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                                     capture_output=True, text=True).stderr.split('[Parsed_loudnorm')[-1].split('\n', 1)[1])
    LN = ('loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s'
          % (meas['input_i'], meas['input_tp'], meas['input_lra'], meas['input_thresh'], meas['target_offset']))
    out = os.path.join(HERE, 'mum_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
