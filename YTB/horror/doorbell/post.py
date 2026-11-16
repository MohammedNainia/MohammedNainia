"""DOORBELL CAMERA (English): finish the render (silent): hook, captions, narration, sound.
    python post.py                  reads raw.mp4 -> doorbell_1080x1920.mp4  (the Darija version: ../doorbell_darija/post.py)
    python post.py --frames 0,900   check frames in check/"""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1080, 1920, 30, 50.0
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_I = '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'
if not os.path.exists(FONT_I): FONT_I = FONT
if not os.path.exists(FONT): FONT = FONT_I = 'C:/Windows/Fonts/arialbd.ttf'
WORDS = json.load(open(os.path.join(VO, 'words.json'))); LAY = {l['name']: l for l in json.load(open(os.path.join(VO, 'layout.json')))}
args = sys.argv[1:]
RAW = os.path.join(HERE, args[args.index('--raw') + 1] if '--raw' in args else 'raw.mp4')
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
GLITCH = [(1.2, 1.45), (40.7, 40.95), (44.2, 44.35)]     # same as the scene

CHUNKS, i = [], 0
while i < len(WORDS):
    n = min(3, len(WORDS) - i) if len(WORDS) - i != 4 else 2
    for k in range(n - 1):
        if WORDS[i + k][0][-1:] in ',.?!' or WORDS[i + k][3] != WORDS[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(WORDS[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 64); f_mon = ImageFont.truetype(FONT_I, 64); f_hook = ImageFont.truetype(FONT, 120)
END_CAP = 46.6
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < .12 else max(0, 1 - (t - .12) / .3) if t < .42 else ease((t - (DUR - .55)) / .2) if t > DUR - .55 else 0
    if ha > 0:
        for k, line in enumerate(['DOORBELL', 'CAMERA']):
            d.text((W // 2, 250 + k * 135), line, font=f_hook, fill=(255, 255, 255, int(255 * ha)), stroke_width=9, stroke_fill=(0, 0, 0, int(230 * ha)), anchor='mm')
    if .42 <= t < END_CAP:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .3:
                mon = ch[0][3]; s = ' '.join(w for w, _, _, _ in ch)
                d.text((W // 2, 1500), s, font=f_mon if mon else f_cap, fill=(255, 205, 220) if mon else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

SR = 48000
def load(p, extra=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', p] + (['-af', extra] if extra else []) + ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).copy()
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + 2 * SR, np.float32); rng = np.random.default_rng(17)
    def add(t, x, g): i = int(t * SR); m[i:i + len(x)] += x[:len(m) - i] * g
    def tt(sec): return np.arange(int(sec * SR)) / SR
    def brown(sec): x = np.cumsum(rng.standard_normal(int(sec * SR))).astype(np.float32); x -= np.convolve(x, np.ones(3000) / 3000, 'same'); return x / (np.abs(x).max() + 1e-6)
    def band(x, lo, hi):                                            # FFT band-pass
        X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x)).astype(np.float32)
    def radio(x, crush=.04):                                        # the monitor speaker: thin, a little crushed, crackling
        y = band(x, 320, 3300); y = np.tanh(y * 3) / np.tanh(3); y = np.round(y / crush) * crush * .5 + y * .5
        cr = (rng.random(len(y)) > .9993) * rng.standard_normal(len(y)) * .5
        return (y + band(cr.astype(np.float32), 800, 6000)).astype(np.float32)
    # night outside: a distant hum, a dog far away; the room is quiet
    t = tt(DUR); add(0, (.4 * brown(DUR) + .3 * np.sin(2 * np.pi * 50 * t) * .2).astype(np.float32), .03)
    for k in [9.3, 9.9, 31.5]:
        tt_ = tt(.35); bark = (band(rng.standard_normal(len(tt_)).astype(np.float32), 300, 1400) * np.exp(-tt_ * 9)).astype(np.float32); add(k, bark / np.abs(bark).max(), .02)
    # the phone: buzz + ding for every motion alert
    t = tt(.32); bz = (np.sign(np.sin(2 * np.pi * 170 * t)) * .5 * np.sin(np.pi * t / .32)).astype(np.float32)
    t2 = tt(.5); ding = ((np.sin(2 * np.pi * 1320 * t2) + .5 * np.sin(2 * np.pi * 1980 * t2)) * np.exp(-t2 * 8)).astype(np.float32)
    for k in [1.9, 16.1, 17.4, 18.6, 19.8, 20.9]: add(k, bz, .22); add(k + .05, ding, .09)
    # the live view's hiss while it is on screen, glitch bursts
    hiss = band(rng.standard_normal(n).astype(np.float32), 1500, 7000); hiss /= np.abs(hiss).max(); env = np.zeros(n, np.float32)
    for a, b in [(0, 1.5), (7.6, 11.5), (15.0, 18.5), (20.0, 25.6), (29.2, 44.4), (47.2, DUR)]: env[int(a * SR):int(b * SR)] = .02
    for a, b in GLITCH: env[int(a * SR):int(b * SR)] = .16
    m[:n] += hiss * env
    # the camera's little motor: whirring while it turns (22.6 to 33.6), louder on the close-up
    t = tt(11.0); f = 900 + 120 * np.sin(t * 3); wh = (np.sin(2 * np.pi * np.cumsum(f) / SR) * .4 + band(rng.standard_normal(len(t)).astype(np.float32), 600, 3000) * .6)
    wh *= np.minimum(1, t / .4) * np.minimum(1, (11 - t) / .4) * (1 + 1.5 * ((t > 3.0) & (t < 6.6)))
    add(22.6, wh.astype(np.float32), .025)
    # narration
    for name, l in LAY.items(): add(l['offset'], load(os.path.join(VO, name + '.mp3')), 1.0)
    # her heartbeat from the window on, a low swell under "someone standing", silence on the last line
    hb = load(os.path.join(SFX, 'synth_heartbeat.wav')); k = 33.6
    while k < 44.2: add(k, hb, .3); k += .85 - .25 * (k - 33.6) / 10.6
    t = tt(3.6); dr = (np.sin(2 * np.pi * 55 * t) + .5 * np.sin(2 * np.pi * 82.4 * t) + .3 * brown(3.6)) * np.minimum(1, t / 1.5) * np.minimum(1, (3.6 - t) / .2)
    add(40.8, dr.astype(np.float32), .08)
    m = m[:n]
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
    out = os.path.join(HERE, 'doorbell_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
