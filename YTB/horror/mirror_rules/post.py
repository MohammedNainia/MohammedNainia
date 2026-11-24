"""MIRROR RULES: finish the render (silent) into the final reel: captions, Haru's voice, sound. No hook card: the first spoken line is the hook.
    python post.py                  reads raw.mp4 -> mirror_rules_1080x1920.mp4
    python post.py --raw FILE       another silent render
    python post.py --frames 0,300   check frames in check/
    python post.py --mix            only the sound (mix.wav)
Haru's narration is the 1.5x .wav files in voice/ (made from VoiceStudio's .src.wav). Lines without a recording are left silent."""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
LAYL = json.load(open(os.path.join(VO, 'layout.json'))); LAY = {l['name']: l for l in LAYL}
W, H, FPS, DUR = 1080, 1920, 30, LAY['END']['start']
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if not os.path.exists(FONT): FONT = 'C:/Windows/Fonts/arialbd.ttf'
WORDS = json.load(open(os.path.join(VO, 'words.json')))
S = lambda n: LAY[n]['start']; E = lambda n: LAY[n]['end']
args = sys.argv[1:]
RAW = os.path.join(HERE, args[args.index('--raw') + 1] if '--raw' in args else 'raw.mp4')
# ---------------------------------------------------------------- captions: short chunks, never across a sentence; the first line (the hook) bigger
CHUNKS, i = [], 0
while i < len(WORDS):
    n = min(3, len(WORDS) - i) if len(WORDS) - i != 4 else 2
    for k in range(n - 1):
        if WORDS[i + k][0][-1:] in ',.?!:' or WORDS[i + k][0].endswith('...'): n = k + 1; break
    CHUNKS.append(WORDS[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 66); f_hook = ImageFont.truetype(FONT, 78)
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    if t < DUR - .2:
        for ch in CHUNKS:
            if ch[0][1] - .05 <= t <= ch[-1][2] + .25:
                hook = ch[0][1] < E('m01'); s = ' '.join(w for w, _, _, _ in ch)
                d.text((W // 2, 1440), s, font=f_hook if hook else f_cap, fill=(255, 226, 120) if hook else (255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)

# ---------------------------------------------------------------- sound
SR = 48000
def load(p, extra=None):
    cmd = ['ffmpeg', '-v', 'error', '-i', p] + (['-af', extra] if extra else []) + ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).copy()
def mix(path):
    n = int(DUR * SR); m = np.zeros(n + 4 * SR, np.float32); rng = np.random.default_rng(44)
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
    def tick(): return norm(band(noise(.03), 1500, 7000) * np.exp(-tt(.03) * 120))
    def beep(f=1000, sec=.12): t = tt(sec); return norm(np.sin(2 * np.pi * f * t) * np.minimum(1, t / .005) * np.minimum(1, (sec - t) / .02))
    def door(): t = tt(1.0); return norm(band(noise(1.0), 300, 3000) * np.exp(-t * 4) * (.5 + .5 * np.sin(2 * np.pi * (3 + 20 * t) * t)) + .6 * band(noise(1.0), 60, 400) * np.exp(-t * 3))
    def buzz(sec, f=100): t = tt(sec); return norm(np.sign(np.sin(2 * np.pi * f * t)) * .5 + .5 * np.sin(2 * np.pi * 2 * f * t) + .2 * band(noise(sec), 2000, 6000))
    def breath(sec=2.6): t = tt(sec); return norm(band(noise(sec), 300, 2500) * np.sin(np.pi * t / sec) ** 2)
    def snore(sec=2.6): t = tt(sec); return norm(band(noise(sec), 60, 600) * np.sin(np.pi * np.clip(t / (sec * .45), 0, 1)) ** 2 * (1 + .6 * np.sin(2 * np.pi * 32 * t)))
    off, on = E('m03') + .15, S('m05') + .45                                        # the light: off after "Slowly", back on in "I turned the light back on"
    # THE BATHROOM: the light's hum, a slow drip from the tap, a low room tone
    seg(0, off, buzz(off, 100) * .25 + band(brown(off + 1), 40, 200)[:int(off * SR)], .035)
    seg(on, DUR, buzz(DUR - on + .5, 100) * .25 + band(brown(DUR - on + 1), 40, 200)[:int((DUR - on + .5) * SR)], .035)
    for k in np.arange(.9, DUR, 2.3): add(k, norm(np.sin(2 * np.pi * (1400 - 2600 * tt(.08)) * tt(.08)) * np.exp(-tt(.08) * 60)), .05)   # plink
    # the reflection's toothbrush: a soft scrub while it brushes; in the dark it's louder, faster, and stops dead before the light comes back
    scrub = lambda sec, rate: norm(band(noise(sec), 2500, 8000) * np.abs(np.sin(np.pi * rate * tt(sec))) ** 3)
    seg(S('m03') + .2, off, scrub(off - S('m03'), 4), .05)
    seg(off + .25, on - .5, scrub(on - off, 5.5), .13)
    # the switch: click off, click on; a buzz as the tube catches
    for c in (off, on): add(c, norm(band(noise(.04), 1000, 6000) * np.exp(-tt(.04) * 90)), .3)
    add(on + .03, buzz(.35, 120) * np.exp(-tt(.35) * 6), .05)
    # its smile (rule two) and the white eyes: a low swell, then a hit with a thin whine
    t0 = S('m02') + .9; x = band(noise(2.0), 60, 400) * np.sin(np.pi * tt(2.0) / 2.0) ** 2; add(t0, norm(x), .08)
    w0 = S('m06') + .5; add(w0, hit(1.4, 25, 220, 2.6), .45); add(w0, norm(np.sin(2 * np.pi * (2400 + 300 * tt(1.6)) * tt(1.6)) * np.exp(-tt(1.6) * 2.5)), .03)
    # "don't blink": the blink is a dry click, then the cut back to the start
    add(E('m07') + .5, norm(band(noise(.05), 300, 3000) * np.exp(-tt(.05) * 80)), .2)
    # Haru's voice: small bathroom reverb; silent where there's no recording yet
    for name, l in LAY.items():
        if name == 'END': continue
        p = os.path.join(VO, l.get('audio', name) + '.wav')
        if os.path.exists(p): add(l['offset'], verb(load(p), .18, .3), 1.0)
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
    out = os.path.join(HERE, args[args.index('--out') + 1] if '--out' in args else 'mirror_rules_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '20', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
