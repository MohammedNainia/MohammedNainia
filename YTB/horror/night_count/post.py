"""THE NIGHT COUNT: finish the render (silent) into the final reel: hook, captions, voices, sound.
    python post.py                  reads raw.mp4 -> night_count_1080x1920.mp4
    python post.py --raw FILE       another silent render
    python post.py --frames 0,900   check frames in check/
    python post.py --mix            only the sound (mix.wav)
Voices are the 1.5x .wav files in voice/ (narration from VoiceStudio, dialogue from Artlist). The nurse's question is one take (n01) used three times."""
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
# ---------------------------------------------------------------- captions: short chunks, never across a sentence or a speaker
HOOK_END = next(w[2] for w in WORDS if w[0].lower().startswith('bed')) + .25   # the hook is the first line, spoken and shown at once
CAPW = [w for w in WORDS if w[1] >= HOOK_END - .2]
CHUNKS, i = [], 0
while i < len(CAPW):
    n = min(3, len(CAPW) - i) if len(CAPW) - i != 4 else 2
    for k in range(n - 1):
        if CAPW[i + k][0][-1:] in ',.?!:' or CAPW[i + k][3] != CAPW[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(CAPW[i:i + n]); i += n
f_cap = ImageFont.truetype(FONT, 66); f_oth = ImageFont.truetype(FONT_I, 70); f_hook = ImageFont.truetype(FONT, 54)
HOOK = ["I TOLD THE NIGHT NURSE", "THE TRUTH.", "NOW I'M IN THE EMPTY BED."]
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
                y = 1440
                d.text((W // 2, y), s, font=f_oth if oth else f_cap, fill=(255, 238, 226) if oth else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
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
    night0, black0, morning0 = S('h02') - .3, E('n02') + .2, S('h09') - .4
    # MORNING (the flash-forward): birds, a far trolley, the monitor steady
    seg(0, night0, band(noise(6), 2500, 6000) * (np.sin(tt(6) * 40) > .85), .012); seg(0, night0, band(brown(6), 40, 300), .05)
    # NIGHT: the room's hum, the heart monitor beeping, the wall clock ticking
    seg(night0, black0, band(brown(40), 40, 180), .07); seg(night0, black0, buzz(40, 50) * .1, .01)
    k = night0; bpm = 62
    while k < black0 - .2:
        if not (S('h07') - .2 < k < S('h07') + .9): add(k, beep(980), .045)              # it skips while she says "Three"
        k += 60 / bpm; bpm = 62 if k < S('n1b') else min(110, bpm + 4)
    for k in np.arange(night0, black0, 1.0): add(k, tick(), .035)
    # THE DOOR: each time the nurse comes, the handle, the hinge, the corridor's hum and light buzz spilling in
    for d0 in (S('n1a') - .8, S('n1b') - .9, S('n1c') - .9):
        add(d0, door(), .22); seg(d0 + .2, d0 + 2.6, band(brown(3), 100, 900), .05)
    # EVERY HOUR: the clock jumping, the door opening and closing quickly, four times
    for j in range(4): a = S('h03') - .3 + j * (S('h04') - S('h03')) / 4; add(a, tick(), .2); add(a + .05, door()[:int(.4 * SR)], .12)
    # GRANDMA asleep: snoring at three; the shape under the sheet breathing, slow, wet, and too close
    for k in np.arange(S('h05') - .4, S('n1b') - 1, 2.6): add(k, snore(), .08)
    for k in np.arange(S('h05') + .6, black0, 2.6): add(k, breath(), .1)
    # "THEN ONE OF YOU HAS TO LEAVE": the strip light buzzes up, dies; black; the bed creaks; the sheet slides
    a = E('n02') - .3; seg(a, black0 + .1, buzz(1.0, 120), .05); add(black0, hit(.5, 200, 2000, 20), .2)
    add(black0 + .6, norm(band(noise(1.2), 100, 900) * np.abs(np.sin(tt(1.2) * 9))), .15)     # a creak
    add(black0 + 1.5, norm(band(noise(1.0), 1500, 6000) * np.sin(np.pi * tt(1.0))), .08)     # cloth sliding
    # MORNING AGAIN: birds, a trolley, Grandma laughing in another room of sound; the monitor slow and calm
    seg(morning0, DUR, band(noise(20), 2500, 6000) * (np.sin(tt(20) * 40) > .85), .012); seg(morning0, DUR, band(brown(20), 40, 300), .05)
    k = morning0
    while k < E('d01') + .2: add(k, beep(980), .03); k += 1.0
    add(S('d01') + .5, hit(1.6, 20, 200, 2.5), .55)                                             # the last "Two."
    # voices
    for name, l in LAY.items():
        if name == 'END': continue
        p = os.path.join(VO, l.get('audio', name) + '.wav'); x = load(p)
        if name.startswith('n1') or name == 'n02': x = verb(x, .25, .4)                         # the nurse, in the doorway
        add(l['offset'], x, .85 if name == 'g01' else 1.0)                                      # Grandma's "Two" is a touch loud
    m = m[:n]
    k = int((E('d01') + .5) * SR); m[k:] *= np.exp(-np.arange(len(m) - k) / (.3 * SR))
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
    out = os.path.join(HERE, args[args.index('--out') + 1] if '--out' in args else 'night_count_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '20', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
