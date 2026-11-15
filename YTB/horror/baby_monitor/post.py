"""BABY MONITOR : finish the render (silent) into the final reel: hook, captions, narration, the voice on the monitor, sound.
    python post.py                  reads raw.mp4 -> baby_monitor_1080x1920.mp4
    python post.py --frames 0,900   check frames in check/"""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1080, 1920, 30, 71.4
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_I = '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'
if not os.path.exists(FONT_I): FONT_I = FONT
if not os.path.exists(FONT): FONT = FONT_I = 'C:/Windows/Fonts/arialbd.ttf'
WORDS = json.load(open(os.path.join(VO, 'words.json'))); LAY = {l['name']: l for l in json.load(open(os.path.join(VO, 'layout.json')))}
args = sys.argv[1:]
RAW = os.path.join(HERE, args[args.index('--raw') + 1] if '--raw' in args else 'raw.mp4')
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
GLITCH = [(1.4, 1.65), (25.95, 26.3), (27.2, 27.4), (66.0, 66.25), (67.5, 67.75)]     # same as the scene

CHUNKS, i = [], 0
while i < len(WORDS):
    n = min(3, len(WORDS) - i) if len(WORDS) - i != 4 else 2
    for k in range(n - 1):
        if WORDS[i + k][0][-1:] in ',.?!' or WORDS[i + k][3] != WORDS[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(WORDS[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 64); f_mon = ImageFont.truetype(FONT_I, 64); f_hook = ImageFont.truetype(FONT, 120)
END_CAP = 69.4
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < .12 else max(0, 1 - (t - .12) / .3) if t < .42 else ease((t - (DUR - .55)) / .2) if t > DUR - .55 else 0
    if ha > 0:
        for k, line in enumerate(['BABY', 'MONITOR']):
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
    # the house at night: low hum, a slow clock in the living room
    t = tt(DUR); add(0, (.5 * np.sin(2 * np.pi * 50 * t) * .3 + .4 * brown(DUR)).astype(np.float32), .025)
    tick = load(os.path.join(SFX, 'synth_tick.wav'))
    for k in np.arange(.5, DUR, 1.0):
        if not (4.4 < k < 9.6 or 33 < k < 54.8): add(k, tick, .04)
    # the monitor's hiss: always on, louder close to it, bursts on the glitches
    hiss = band(rng.standard_normal(n).astype(np.float32), 1500, 7000)
    hiss /= np.abs(hiss).max(); env = np.full(n, .012, np.float32)
    for a, b in [(0, 4.4), (14.15, 17.4), (25.77, 28.34), (59.3, 62.0), (64.3, DUR)]: env[int(a * SR):int(b * SR)] = .03
    for a, b in GLITCH: env[int(a * SR):int(b * SR)] = .16
    m[:n] += hiss * env
    # the star projector's music box, heard only in the nursery
    notes = [76, 79, 84, 83, 79, 76, 74, 76, 79, 77, 74, 72]
    box = np.zeros(int(8 * SR), np.float32)
    for j, nn in enumerate(notes):
        f0 = 440 * 2 ** ((nn - 69) / 12); tn = tt(1.4); tone = (np.sin(2 * np.pi * f0 * tn) + .3 * np.sin(2 * np.pi * f0 * 2.01 * tn)) * np.exp(-tn * 3.2)
        i0 = int(j * .62 * SR); box[i0:i0 + len(tone)] += tone[:len(box) - i0].astype(np.float32)
    for a, b in [(4.4, 9.6), (33.0, 37.5), (39.0, 47.9), (47.9, 54.8)]:
        k = a
        while k < b: seg = box[:int(min(8, b - k) * SR)].copy(); fade = np.minimum(1, (len(seg) - np.arange(len(seg))) / (.3 * SR)); add(k, seg * fade, .05); k += 8
    # Haru
    for name, l in LAY.items():
        if name[0] == 'n': add(l['offset'], load(os.path.join(VO, name + '.mp3')), 1.0)
    # the voice on the monitor: humming, the laugh, then very close
    add(LAY['m1']['offset'], radio(load(os.path.join(VO, 'm1.mp3'), 'asetrate=44100*0.96,aresample=44100')), .7)
    add(LAY['laugh']['offset'], radio(load(os.path.join(VO, 'laugh.mp3'), 'asetrate=44100*0.94,aresample=44100')), 1.1)
    add(LAY['m2']['offset'], radio(load(os.path.join(VO, 'm2.mp3'), 'asetrate=44100*0.95,aresample=44100'), .02), .6)
    # running up the stairs, the closet doors, the curtain rings, walking back, sitting down
    thud = load(os.path.join(SFX, 'synth_thud.wav'))
    for k in np.arange(37.5, 39.0, .17): add(k, thud, .28)
    t = tt(.9); f = 300 + 90 * np.sin(t * 5); cr = np.sin(2 * np.pi * np.cumsum(f) / SR) * (rng.random(len(t)) > .45) * np.sin(np.pi * t / t[-1])
    add(48.25, cr.astype(np.float32), .05)
    t = tt(.5); sw = band(rng.standard_normal(len(t)).astype(np.float32), 2000, 9000) * np.sin(np.pi * t / t[-1]); add(51.85, sw / np.abs(sw).max(), .12)
    t = tt(.04); ring = (np.sin(2 * np.pi * 3100 * tt(.25)) * np.exp(-tt(.25) * 30)).astype(np.float32)
    for k in np.arange(51.9, 52.3, .07): add(k, ring, .03)
    for k in np.arange(54.9, 57.3, .55): add(k, thud, .1)
    add(57.45, band(rng.standard_normal(int(.4 * SR)).astype(np.float32), 80, 600) * np.exp(-tt(.4) * 9), .15)
    # her heartbeat while it whispers, then a low swell under the last line
    hb = load(os.path.join(SFX, 'synth_heartbeat.wav')); k = 59.4
    while k < 64.2: add(k, hb, .3); k += .85
    t = tt(6.0); dr = (np.sin(2 * np.pi * 55 * t) + .5 * np.sin(2 * np.pi * 82.4 * t) + .3 * brown(6.0)) * np.minimum(1, t / 4) * np.minimum(1, (6 - t) / .4)
    add(64.3, dr.astype(np.float32), .07)
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
    out = os.path.join(HERE, 'baby_monitor_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
