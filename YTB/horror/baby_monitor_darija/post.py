"""BABY MONITOR (Darija) : the same GPU render as ../baby_monitor (raw.mp4), with the Darija voices from VoiceStudio.
The Darija lines are shorter, so some are cut into phrases and each phrase is placed on its shot (SEGS below).
    python post.py                  reads ../baby_monitor/raw.mp4 -> baby_monitor_darija_1080x1920.mp4
    python post.py --frames 0,900   check frames in check/"""
import os, sys, json, wave, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice')
SFX = os.path.join(HERE, '..', '..', 'lanternfold', 'sfx_library')
W, H, FPS, DUR = 1080, 1920, 30, 71.4
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if not os.path.exists(FONT): FONT = 'C:/Windows/Fonts/arialbd.ttf'
args = sys.argv[1:]
RAW = os.path.join(HERE, args[args.index('--raw') + 1] if '--raw' in args else os.path.join('..', 'baby_monitor', 'raw.mp4'))
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
GLITCH = [(1.4, 1.65), (25.95, 26.3), (27.2, 27.4), (66.0, 66.25), (67.5, 67.75)]     # same as the scene

# (file, clip from, clip to, placed at (s), [(caption, clip from, clip to), ...]); clip times are seconds inside the wav
SEGS = [
 ('n1', 0, 99, .05,  [('الجهاز ديال البيبي شد شي حد كيغني.', .2, 2.72), ('وأنا كنت بوحدي فالدار.', 3.3, 4.48)]),
 ('n2', 0, 99, 6.6,  [('كنت كنحضي واحد البيبي.', .18, 1.42), ('كان ناعس الفوق.', 1.72, 2.6), ('وأنا كنت فالكنبة،', 3.04, 4.05), ('نص ناعسة،', 4.33, 5.08), ('والجهاز حدايا.', 5.27, 6.24)]),
 ('m1', 0, 99, 14.15, [('نيني يا مومو...', .16, 1.41), ('نيني يا مومو...', 1.93, 3.42), ('حتى يطيب عشانا...', 3.42, 5.16)]),
 ('n3', 0, 99, 20.47, [('قلت غير شي راديو.', .21, 1.08), ('تشويش.', 1.44, 1.95), ('هاد الأجهزة كيديرو هكا.', 2.14, 3.52)]),
 ('laugh', 0, 99, 25.77, []),
 ('n4', 0, 99, 29.63, [('ولكن من بعد سكتات.', .2, 1.17), ('وضحكات. بشوية.', 1.62, 2.88), ('بحال شي حد مايل على السرير ديال البيبي.', 3.37, 5.28)]),
 ('n5', 0, 1.45, 37.48, [('طلعت جارية للفوق.', .22, 1.19)]),                           # the stairs
 ('n5', 1.45, 3.36, 38.95, [('الباب ديال البيت كان محلول.', 1.6, 3.18)]),               # the open door
 ('n5', 3.36, 4.54, 41.3, [('البيبي كان ناعس.', 3.54, 4.3)]),                          # the baby
 ('n5', 4.54, 5.7, 43.8, [('وما كان حتى حد.', 4.78, 5.57)]),                            # the empty room
 ('n5', 5.7, 99, 45.4, [('حتى حد.', 5.84, 6.2)]),
 ('n6', 0, 1.3, 47.9, [('قلبت فالماريو.', .17, 1.09)]),                                # closet
 ('n6', 1.3, 2.48, 49.36, [('تحت السرير.', 1.69, 2.48)]),                              # under the crib
 ('n6', 2.48, 2.97, 51.4, [('ورا الريدو.', 2.48, 2.97)]),                              # curtains
 ('n6', 2.97, 99, 53.6, [('والو.', 2.97, 3.43)]),                                      # nothing
 ('n7', 0, 99, 56.2, [('رجعت هبطت...', .2, .9), ('وجلست حدا الجهاز.', .9, 1.93)]),
 ('m2', 0, 99, 60.3, [('شششش... مشات.', .12, 1.58), ('دابا تقدر تحل عينيك.', 1.58, 2.84)]),
 ('n8', 0, 1.44, 64.24, [('ماكانش كيغني للبيبي.', .19, 1.34)]),
 ('n8', 1.44, 99, 67.85, [('كان كيتسناني نمشي.', 1.54, 2.7)]),                         # after the hand appears
]
CHUNKS = []                                                     # caption chunks: (text, start, end, monitor?)
for f, a, b, at, caps in SEGS:
    for txt, ca, cb in caps:
        ws = txt.split(); t0, t1 = at + ca - a, at + cb - a
        parts = [ws] if len(ws) <= 4 else [ws[:(len(ws) + 1) // 2], ws[(len(ws) + 1) // 2:]]
        tot = sum(len(' '.join(p)) for p in parts); t = t0
        for p in parts:
            d = (t1 - t0) * len(' '.join(p)) / tot; CHUNKS.append((' '.join(p), t, t + d, f[0] == 'm')); t += d
f_cap = ImageFont.truetype(FONT, 66); f_hook = ImageFont.truetype(FONT, 130)
END_CAP = 69.4
def txt(d, xy, s, font, **k):
    try: d.text(xy, s, font=font, anchor='mm', direction='rtl', language='ar', **k)
    except Exception: d.text(xy, s, font=font, anchor='mm', **k)          # Pillow without raqm: plain draw
def overlay(fr, t):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < .12 else max(0, 1 - (t - .12) / .3) if t < .42 else ease((t - (DUR - .55)) / .2) if t > DUR - .55 else 0
    if ha > 0: txt(d, (W // 2, 300), 'جهاز البيبي', f_hook, fill=(255, 255, 255, int(255 * ha)), stroke_width=9, stroke_fill=(0, 0, 0, int(230 * ha)))
    if .42 <= t < END_CAP:
        for s, a, b, mon in CHUNKS:
            if a - .05 <= t <= b + .25:
                txt(d, (W // 2, 1500), s, f_cap, fill=(255, 205, 220) if mon else (255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 235))
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
    # the voices: each segment cut from its wav (short fades at the cuts) and placed on its shot
    for f, a, b, at, caps in SEGS:
        x = load(os.path.join(VO, f + '.wav')); x = x[int(a * SR):int(min(b, len(x) / SR) * SR)].copy()
        fl = int(.012 * SR); x[:fl] *= np.linspace(0, 1, fl); x[-fl:] *= np.linspace(1, 0, fl)
        if f[0] == 'n': add(at, x, .9)                              # Haru speaks low (no whisper), a little under the room
        elif f == 'm2': add(at, radio(x, .02), .45)                 # the monitor: thin, crackly, very close at the end
        else: add(at, radio(x), .55 if f == 'm1' else .8)
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
    out = os.path.join(HERE, 'baby_monitor_darija_1080x1920.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-af', LN, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ok, fr = cap.read()
        if not ok: fr = np.zeros((H, W, 3), np.uint8)
        ff.stdin.write(overlay(fr, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('saved', out)
