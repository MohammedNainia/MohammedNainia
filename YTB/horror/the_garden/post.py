"""Haru #6 "The Sunflower in Our Garden": the white hook line on frame 0, quiet natural sound, the final video.
Wordless otherwise. Mixed low like the others: -18 LUFS, peaks under -3 dBTP. No black tail: the last frame cuts back
to frame 0 (the loop), so the first sound (the tap on the glass) is also what you hear on every replay.

The tap on the glass at once. Crickets outside. Bed springs, small steps on the boards, a breath. The curtains swish shut
and the crickets stop. A dry creak of the stem as the shadow tilts. A floorboard as she steps back. The far hummed chant
comes back, very faint, as the two shadows rise, and stops dead when all three tilt. A dry rustle, her gasp.
    python post.py                 frames from ../blender/renders/the_garden -> the_garden_1080x1920.mp4
    python post.py --audio-only    only writes mix.wav
Needs: numpy scipy pillow imageio-ffmpeg. Beat times match blender/scenes/the_garden_tail.py."""
import os, sys, subprocess, json, re, glob
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__)); args = sys.argv[1:]
FRAMES = os.path.join(HERE, '..', 'blender', 'renders', 'the_garden')
RAW, OUT, MIX = os.path.join(HERE, 'raw.mp4'), os.path.join(HERE, 'the_garden_1080x1920.mp4'), os.path.join(HERE, 'mix.wav')
HOOK = os.path.join(HERE, 'hook.png')
SR = 48000; DUR = 15.4
HOOK_LINES = ['The sunflower', 'in our garden', 'was facing', 'my window.']
T_TAP, T_EDGE, T_STAND, T_WALK, T_WIN = 0.2, 1.3, 2.3, 3.9, 5.9
T_YANK, T_YANK1, T_TILT, T_BACK, T_RISE, T_ALL, T_TURN = 6.9, 7.2, 8.3, 9.8, 10.6, 12.8, 13.4
rng = np.random.default_rng(66); N = int(DUR * SR); L = np.zeros(N); R = np.zeros(N); T = np.arange(N) / SR


def band(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def lowp(x, f, o=2): return sosfilt(butter(o, f, 'lowpass', fs=SR, output='sos'), x)
def db(x): return 10 ** (x / 20)
def put(sig, at, gain_db=0.0, pan=0.0):
    i = int(at * SR); n = min(len(sig), N - i)
    if n <= 0: return
    g = db(gain_db); L[i:i + n] += sig[:n] * g * (1 - max(0, pan)); R[i:i + n] += sig[:n] * g * (1 + min(0, pan))
def decay(n, tau, attack=0.0005):
    e = np.exp(-np.arange(n) / SR / tau); ia = max(1, int(attack * SR)); e[:ia] *= np.linspace(0, 1, ia); return e
def norm(s): return s / np.max(np.abs(s))
def ramp(t, a, b): return np.clip((t - a) / (b - a), 0, 1)


# room tone: a faint low hush, always
L += lowp(rng.standard_normal(N), 180, 2) * db(-46); R += lowp(rng.standard_normal(N), 180, 2) * db(-46)

# crickets outside, through the glass; they stop when the curtains close
cr = np.zeros(N)
for f0, rate, ph in ((4300, 2.9, 0.0), (4700, 3.4, 1.1), (3900, 2.2, 2.3)):
    chirp = (np.sin(2 * np.pi * rate * T + ph) > 0.55).astype(float) * (np.sin(2 * np.pi * 38 * T) > 0)
    cr += lowp(chirp, 60, 2) * np.sin(2 * np.pi * f0 * T)
cr = norm(lowp(cr, 6000)) * (1 - ramp(T, T_YANK1 - 0.05, T_YANK1 + 0.15))
L += cr * db(-39); R += np.roll(cr, 300) * db(-41)


def tap():
    """one knock of something soft but heavy on a window pane: a dull thud and the glass ringing a moment"""
    n = int(0.35 * SR); x = np.arange(n) / SR
    thud = lowp(rng.standard_normal(n), 220, 4) * decay(n, 0.012, 0.001)
    ring = sum(np.sin(2 * np.pi * f * x + p) * a for f, p, a in ((1850, 0, 1), (2730, 1, .6), (4100, 2, .3))) * decay(n, 0.03)
    return norm(thud * 1.4 + ring * 0.35)
put(tap(), T_TAP, -26, pan=0.2)


def creak(d, f0, lo=300, hi=2000, wob=0.25):
    n = int(d * SR); x = np.arange(n) / SR
    fr = f0 * (1 + wob * np.sin(2 * np.pi * .7 * x)); ph = 2 * np.pi * np.cumsum(fr) / SR
    s = (np.sin(ph) > .8).astype(float) * rng.uniform(.5, 1, n)
    return norm(band(s, lo, hi) * np.sin(np.pi * x / d) ** 2)
put(creak(0.7, 55, 200, 1500), T_EDGE + 0.1, -32, pan=-0.3)            # bed springs as she swings round
put(creak(0.5, 70, 200, 1500), T_STAND + 0.6, -33, pan=-0.3)           # and as she stands


def step():
    n = int(.14 * SR)
    s = lowp(rng.standard_normal(n), 300, 4) * decay(n, .02, .002) + band(rng.standard_normal(n), 2000, 6000) * decay(n, .008, .002) * .2
    return norm(s)
x = T_WALK + 0.2; i = 0
while x < T_WIN - 0.1: put(step(), x, -30, pan=.1 * (-1) ** i); x += 0.5; i += 1


def breath(d, inhale=True, shaky=0.0):
    n = int(d * SR); x = np.arange(n) / SR
    env = np.sin(np.pi * x / d) ** (1.5 if inhale else 2.2)
    if shaky: env *= 1 + shaky * np.sin(2 * np.pi * 9 * x)
    return norm(band(rng.standard_normal(n), 400 if inhale else 250, 2600 if inhale else 1800) * env)
put(breath(.45), 6.25, -31)                                            # before she grabs the curtains
put(breath(.3, True, .4), T_TILT + 0.6, -30)                            # the shadow tilts
put(breath(.45, True, .6), T_TURN + 0.1, -25)                           # the gasp


def swish(d):
    """curtains yanked along the rod: cloth hiss sweeping up, and the rings clattering"""
    n = int(d * SR); x = np.arange(n) / SR
    hiss = band(rng.standard_normal(n), 900, 7000) * np.sin(np.pi * x / d) ** 0.7
    rings = np.zeros(n)
    for k in rng.integers(0, n - 2000, 7): rings[k:k + 1800] += np.sin(2 * np.pi * rng.uniform(2500, 3600) * np.arange(1800) / SR) * decay(1800, .006)
    return norm(hiss + rings * 0.5)
put(swish(T_YANK1 - T_YANK + 0.12), T_YANK - 0.02, -28)

put(creak(1.1, 23, 120, 900, wob=0.15), T_TILT, -30, pan=0.1)          # the stem bends: low and dry
put(creak(0.45, 48, 250, 1600), T_BACK + 0.15, -31)                    # a floorboard as she steps back


# the chant from The Gathering, far and faint behind the glass, as the two rise; cut dead when all three tilt
def voice(f0, vowel, seed):
    r = np.random.default_rng(seed)
    vib = 1 + 0.006 * np.sin(2 * np.pi * r.uniform(4.5, 5.5) * T + r.uniform(0, 6)) + 0.003 * lowp(r.standard_normal(N), 3)
    ph = 2 * np.pi * np.cumsum(f0 * vib) / SR
    src = sum(np.sin(k * ph) / k for k in range(1, 18))
    fm = {'oo': ((300, 120), (870, 150)), 'mm': ((250, 100), (2200, 300))}[vowel]
    return sum(band(src, f - w, f + w) * g for (f, w), g in zip(fm, (1.0, 0.35)))
chant = sum(voice(f0, vw, i) for i, (f0, vw) in enumerate(((98, 'mm'), (116.5, 'oo'), (146.8, 'mm'), (73.4, 'oo'))))
chant = lowp(norm(chant), 600, 4) * (0.65 + 0.35 * np.maximum(0, np.sin(2 * np.pi * T / 1.43 - 1.2)) ** 2)
lvl = db(-44 + 8 * ramp(T, T_RISE, T_ALL)) * ramp(T, T_RISE - 0.3, T_RISE + 0.8) * (1 - ramp(T, T_ALL, T_ALL + 0.03))
L += chant * lvl; R += np.roll(chant, 400) * lvl


def crackle(d, dens):
    n = int(d * SR); s = np.zeros(n)
    for k in rng.integers(0, n - 400, int(dens * d)): s[k:k + 300] += rng.standard_normal(300) * decay(300, .0015)
    return norm(band(s, 600, 4000) * np.sin(np.pi * np.arange(n) / n) ** .5)
put(crackle(0.35, 120), T_ALL, -26)                                    # three heads tilt at once

mix = np.stack([L, R], 1); mix *= db(-3) / np.max(np.abs(mix))
# a gentle peak limiter: the steps, creaks and the tap are short spikes over a very quiet bed, so they would stop the
# loudness pass from reaching -18 LUFS cleanly; pull just the spikes down 5 dB with a smooth gain envelope (5 ms attack)
mix *= db(5)
from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
w = int(0.005 * SR)
g = np.minimum(1.0, db(-4) / np.maximum(maximum_filter1d(np.max(np.abs(mix), 1), 2 * w), 1e-9))
g = uniform_filter1d(minimum_filter1d(g, 2 * w), w)               # smooth, and never above the gain a peak needs
mix *= g[:, None]
wavfile.write(MIX, SR, (mix * 32767).astype(np.int16)); print('wrote', MIX)
if '--audio-only' in args: sys.exit()

# the hook line: white, black outline, upper third (clear of the top 12%), on screen from frame 0
img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 96)
for k, line in enumerate(HOOK_LINES):
    d.text((540, 330 + k * 118), line, font=font, fill=(255, 255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0, 235), anchor='mm')
img.save(HOOK)

frames = sorted(glob.glob(os.path.join(FRAMES, '[0-9][0-9][0-9][0-9].png')))
lst = os.path.join(FRAMES, 'list.txt')
with open(lst, 'w') as f:
    for p in frames: f.write(f"file '{os.path.basename(p)}'\nduration {1 / 12}\n")
    f.write(f"file '{os.path.basename(frames[-1])}'\n")
subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-loop', '1', '-i', HOOK,
                '-filter_complex', '[0]fps=24,vignette=angle=PI/5,noise=alls=5:allf=t[v];'
                                   '[1]format=rgba,fade=t=out:st=2.2:d=0.3:alpha=1[h];'
                                   "[v][h]overlay=enable='lt(t,2.6)',format=yuv420p",
                '-t', str(DUR), '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-movflags', '+faststart', RAW], check=True)
m = subprocess.run([FF, '-hide_banner', '-i', MIX, '-af', 'loudnorm=I=-18:TP=-3:LRA=15:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
j = json.loads(re.findall(r'\{[^{}]*\}', m)[-1])
print('measured', j['input_i'], 'LUFS, peak', j['input_tp'], 'dBTP')
ln = (f"loudnorm=I=-18:TP=-3:LRA=15:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
      f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run([FF, '-y', '-v', 'error', '-i', RAW, '-i', MIX, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', ln, '-ar', '48000',
                '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], check=True)
small = OUT.replace('.mp4', '_small.mp4')
subprocess.run([FF, '-y', '-v', 'error', '-i', OUT, '-c:v', 'libx264', '-crf', '24', '-preset', 'slow', '-c:a', 'copy', '-movflags', '+faststart', small], check=True)
m = subprocess.run([FF, '-hide_banner', '-i', OUT, '-af', 'loudnorm=print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
j = json.loads(re.findall(r'\{[^{}]*\}', m)[-1]); print('final', j['input_i'], 'LUFS, peak', j['input_tp'], 'dBTP')
print('saved', OUT, small)
