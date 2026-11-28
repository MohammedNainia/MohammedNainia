"""Haru #8 "Sector B13 · File 01": finish the silent render into the final reel: hook, captions, voices, sound, card.
    python post.py                frames from renders/full (blender/scenes/sector_b13.py) -> sector_b13_1080x1920.mp4
    python post.py --mix          only the sound (mix.wav)
    python post.py --frames 0,30  check frames (PNG) in check/ instead of the video
Voices: voice/*.wav laid out by voice/layout.json (voice/build_layout.py). Sounds: sfx/*.mp3 (sfx/SOURCES.md), each
normalised before the volume plan in sfx_picks.md is applied; the claws on the nylon are made here. The voice leads,
the ambience ducks 4 dB under it, the mix is -18 LUFS with peaks under -3 dBTP.
Timeline: the reel is 44 s of picture (12 fps renders shown at 24 fps), then the black FILE 01 card to 46.5 s, then the
cut back to frame 0 (the torch clicks on: the loop)."""
import os, sys, json, wave, glob, subprocess, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import butter, sosfilt
from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, 'voice'); SX = os.path.join(HERE, 'sfx')
FRAMES = os.path.join(HERE, 'renders', 'full')
OUT, MIX = os.path.join(HERE, 'sector_b13_1080x1920.mp4'), os.path.join(HERE, 'mix.wav')
LAYL = json.load(open(os.path.join(VO, 'layout.json'))); LAY = {l['name']: l for l in LAYL}
WORDS = json.load(open(os.path.join(VO, 'words.json')))
W, H, FPS, PIC, DUR = 1080, 1920, 24, 44.0, 46.5
SR = 48000; N = int(DUR * SR)
args = sys.argv[1:]
rng = np.random.default_rng(813)

# ---------------------------------------------------------------- sound helpers
def db(x): return 10 ** (x / 20)
def lowp(x, f, o=2): return sosfilt(butter(o, f, 'lowpass', fs=SR, output='sos'), x)
def band(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def tt(sec): return np.arange(int(sec * SR)) / SR


def load(p, af=None):
    cmd = [FF, '-v', 'error', '-i', p] + (['-af', af] if af else []) + ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).astype(np.float64)


def rms_norm(x, ref=db(-20)):
    """level a clip by the loudness of its active part (so a quiet source can't vanish and a loud one can't jump out)"""
    a = np.abs(x); act = a[a > a.max() * 0.05] if a.max() > 0 else a
    r = np.sqrt(np.mean(act ** 2)) if len(act) else 1.0
    return x * ref / max(r, 1e-9)


def fade(x, fin=0.05, fout=0.2):
    x = x.copy(); a, b = int(fin * SR), int(fout * SR)
    if a: x[:a] *= np.linspace(0, 1, min(a, len(x)))[:len(x[:a])]
    if b: x[-b:] *= np.linspace(1, 0, min(b, len(x)))[-len(x[-b:]):]
    return x


def bed(name, a, b, af=None):
    """a looping bed from a clip, a..b seconds, with soft ends"""
    x = load(os.path.join(SX, name), af); L = int((b - a) * SR)
    y = np.resize(x, L) if len(x) < L else x[:L]
    return fade(rms_norm(y), 0.6, 0.8)


V = np.zeros(N); A = np.zeros(N); FX = np.zeros(N)                  # voice, ambience (ducks), effects (no duck)


def put(bus, sig, at, gain_db=0.0):
    i = int(at * SR); n = min(len(sig), N - i)
    if n > 0: bus[i:i + n] += sig[:n] * db(gain_db)


# ---------------------------------------------------------------- the voices
for l in LAYL:
    if l['name'] == 'END': continue
    w = wave.open(os.path.join(VO, l['audio'] + '.wav'))
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    x = rms_norm(x)
    if l['name'] == 'm1':                                            # Mika, outside the tent: through the nylon
        x = lowp(x, 4200); g = -1.5
    elif l['name'] == 'c1':                                          # the creature, in Mika's voice, from the treeline
        x = lowp(x, 3600); ir = rng.standard_normal(int(0.5 * SR)) * np.exp(-tt(0.5) * 9); ir /= np.abs(ir).sum() / 6
        x = x + 0.35 * np.convolve(x, ir)[:len(x)]; g = -3.0
    else:
        g = 0.0
    put(V, x, l['offset'], g)

# ---------------------------------------------------------------- ambience (ducks under the voice)
put(A, bed('crickets.mp3', 0.0, 35.6), 0.0, -26)                    # the night under everything until dawn
put(A, bed('wind.mp3', 0.0, PIC), 0.0, -27)                          # wind in the pines, all the way
put(A, bed('campfire.mp3', 4.0, 9.8), 4.0, -22)                      # the flashback: the fire leads
put(A, bed('campfire.mp3', 15.0, 18.5, 'lowpass=f=1800'), 15.0, -32)   # embers by the tents
put(A, bed('birds.mp3', 35.5, PIC), 35.5, -24)                       # dawn
put(A, bed('drone.mp3', PIC, DUR), PIC, -20)                         # under the FILE 01 card

# ---------------------------------------------------------------- effects
def clip(name, af=None, sec=None):
    x = load(os.path.join(SX, name), af)
    if sec: x = x[:int(sec * SR)]
    return fade(rms_norm(x), 0.005, 0.08)


put(FX, clip('torch.mp3', sec=0.4), 0.0, -13)                        # frame 0: the torch is on (the loop's click)
put(FX, fade(rms_norm(load(os.path.join(SX, 'breath.mp3'))[:int(4.0 * SR)]), 0.02, 0.6), 0.0, -12)   # held, shaky breathing
put(FX, clip('scream_jun.mp3', 'lowpass=f=1500,highpass=f=200', sec=0.9), 15.96, -16)     # Jun's tent, cut short
put(FX, clip('scream_mika.mp3', 'lowpass=f=1300,highpass=f=200', sec=1.6), 16.84, -17)    # then Mika's, further off
put(FX, clip('steps.mp3', 'lowpass=f=2500', sec=2.5), 20.3, -15)    # something tall walks round her tent


def claws(sec, strokes):
    """fingernails dragged slowly over taut nylon: scratchy bursts with a low skin rasp, made here (nothing fit)"""
    s = np.zeros(int(sec * SR))
    for a, d in strokes:
        n = int(d * SR); x = np.arange(n) / SR
        fr = 2400 + 900 * np.sin(2 * np.pi * 1.3 * x)
        grit = (rng.random(n) < (0.08 + 0.05 * np.sin(2 * np.pi * 17 * x))).astype(float) * rng.uniform(.4, 1, n)
        rasp = band(rng.standard_normal(n), 900, 5200) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(fr) / SR / 60))
        env = np.sin(np.pi * x / d) ** 0.8
        i = int(a * SR); s[i:i + n] += (band(grit, 1800, 7000) * 1.4 + rasp * 0.6) * env
    return fade(rms_norm(s), 0.02, 0.2)


put(FX, claws(3.0, [(0.0, 1.3), (1.5, 1.4)]), 20.6, -13)             # the fingers drag along the wall
put(FX, clip('zip.mp3', 'atempo=0.5,atempo=0.88'), 28.05, -12)       # the zip opens by itself, slow (about 4 s)
put(FX, clip('zip.mp3', 'areverse,atempo=0.6', sec=2.0), 32.6, -17)  # the fingers slide back out
put(FX, clip('chain.mp3', 'lowpass=f=2600', sec=3.0), 36.6, -17)     # its collar chain, across the clearing
put(FX, clip('steps.mp3', 'lowpass=f=2200', sec=3.0), 37.4, -19)     # the handlers' steps
put(FX, clip('gate.mp3', 'lowpass=f=3200'), 43.05, -12)              # the gate clangs at the treeline
put(FX, clip('lock.mp3', 'lowpass=f=3500', sec=1.2), 43.6, -13)      # the padlock

# ---------------------------------------------------------------- ducking and the final mix
env = uniform_filter1d(maximum_filter1d(np.abs(V), int(0.05 * SR)), int(0.25 * SR))
duck = db(-4) ** np.clip(env / (env.max() * 0.08 + 1e-9), 0, 1)     # -4 dB while she speaks
mix = V + A * duck + FX
mix *= db(-3) / np.max(np.abs(mix))
mix *= db(5)                                                         # gentle peak limiter (as in dont_open/post.py)
w = int(0.005 * SR)
g = np.minimum(1.0, db(-4) / np.maximum(maximum_filter1d(np.abs(mix), 2 * w), 1e-9))
g = uniform_filter1d(minimum_filter1d(g, 2 * w), w); mix *= g
st = np.stack([mix, mix], 1)
import scipy.io.wavfile as wf
wf.write(MIX, SR, (st * 32767).astype(np.int16)); print('wrote', MIX)
if '--mix' in args: sys.exit()

# ---------------------------------------------------------------- picture: hook, captions, card
FONT = 'C:/Windows/Fonts/arialbd.ttf'; FONT_I = 'C:/Windows/Fonts/arialbi.ttf'
if not os.path.exists(FONT_I): FONT_I = FONT
f_hook = ImageFont.truetype(FONT, 76); f_cap = ImageFont.truetype(FONT, 66); f_oth = ImageFont.truetype(FONT_I, 68)
f_card = ImageFont.truetype('C:/Windows/Fonts/consolab.ttf' if os.path.exists('C:/Windows/Fonts/consolab.ttf') else FONT, 64)
HOOK = ["Three of us went camping.", "I'm the only one", "still in the tent."]
HOOK_END = LAY['n1']['end'] + 0.25                                   # the hook is the first line, spoken and shown at once
CAPW = [w for w in WORDS if w[1] >= HOOK_END - 0.2]
CHUNKS, i = [], 0
while i < len(CAPW):                                                 # short chunks, never across a sentence or a speaker
    n = min(3, len(CAPW) - i) if len(CAPW) - i != 4 else 2
    for k in range(n - 1):
        if CAPW[i + k][0][-1:] in ',.?!:' or CAPW[i + k][3] != CAPW[i + k + 1][3]: n = k + 1; break
    CHUNKS.append(CAPW[i:i + n]); i += n


def overlay(im, t):
    d = ImageDraw.Draw(im, 'RGBA')
    ha = 1.0 if t < HOOK_END else max(0.0, 1 - (t - HOOK_END) / 0.3)
    if ha > 0:
        for k, line in enumerate(HOOK):
            d.text((W // 2, 300 + k * 96), line, font=f_hook, fill=(255, 255, 255, int(255 * ha)), stroke_width=8,
                   stroke_fill=(0, 0, 0, int(235 * ha)), anchor='mm')
    if HOOK_END <= t < PIC:
        for ch in CHUNKS:
            if ch[0][1] - 0.05 <= t <= ch[-1][2] + 0.25:
                oth = ch[0][3]; s = ' '.join(w for w, _, _, _ in ch)
                d.text((W // 2, 1440), s, font=f_oth if oth else f_cap, fill=(255, 190, 215) if oth else (255, 255, 255),
                       stroke_width=7, stroke_fill=(0, 0, 0, 235), anchor='mm')
                break
    if t >= PIC:                                                     # the card: typed like the sign
        k = min(1.0, (t - PIC) / 0.4)
        d.text((W // 2, H // 2), 'SECTOR B13 · FILE 01', font=f_card, fill=(240, 240, 236, int(255 * k)), anchor='mm')
    return im


frames = sorted(glob.glob(os.path.join(FRAMES, '[0-9][0-9][0-9][0-9].png')))
print('frames', len(frames))
def frame_at(t):
    if t >= PIC or not frames: return Image.new('RGB', (W, H), (0, 0, 0))
    k = min(len(frames) - 1, int(t * 12)); return Image.open(frames[k]).convert('RGB')


if '--frames' in args:
    os.makedirs(os.path.join(HERE, 'check'), exist_ok=True)
    for s in args[args.index('--frames') + 1].split(','):
        t = float(s); overlay(frame_at(t), t).save(os.path.join(HERE, 'check', f'check_{t:05.1f}.png'))
    sys.exit()

# vignette and a little grain, as in the earlier Blender reels; then captions over the top
yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIG = (1 - 0.32 * np.clip(r - 0.45, 0, 1) ** 1.6)[..., None].astype(np.float32)
enc = subprocess.Popen([FF, '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', MIX, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '17', '-preset', 'slow',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT + '.tmp.mp4'],
                       stdin=subprocess.PIPE)
nf = int(DUR * FPS)
for f in range(nf):
    t = f / FPS
    a = np.asarray(frame_at(t), np.float32)
    if t < PIC: a = np.clip(a * VIG + rng.normal(0, 3.2, a.shape[:2])[..., None], 0, 255)
    im = overlay(Image.fromarray(a.astype(np.uint8)), t)
    enc.stdin.write(np.asarray(im, np.uint8).tobytes())
enc.stdin.close(); enc.wait()
# loudness: two-pass loudnorm to -18 LUFS, peaks under -3 dBTP
m = subprocess.run([FF, '-hide_banner', '-i', MIX, '-af', 'loudnorm=I=-18:TP=-3:LRA=15:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
j = json.loads(re.findall(r'\{[^{}]*\}', m)[-1]); print('measured', j['input_i'], 'LUFS, peak', j['input_tp'], 'dBTP')
ln = (f"loudnorm=I=-18:TP=-3:LRA=15:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
      f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run([FF, '-y', '-v', 'error', '-i', OUT + '.tmp.mp4', '-i', MIX, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', ln,
                '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], check=True)
os.remove(OUT + '.tmp.mp4')
small = OUT.replace('.mp4', '_small.mp4')
subprocess.run([FF, '-y', '-v', 'error', '-i', OUT, '-c:v', 'libx264', '-crf', '24', '-preset', 'slow', '-c:a', 'copy', '-movflags', '+faststart', small], check=True)
m = subprocess.run([FF, '-hide_banner', '-i', OUT, '-af', 'loudnorm=print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
j = json.loads(re.findall(r'\{[^{}]*\}', m)[-1]); print('final', j['input_i'], 'LUFS, peak', j['input_tp'], 'dBTP')
print('saved', OUT, small)
