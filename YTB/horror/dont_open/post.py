"""Haru #7 "Don't Open Your Door": the white hook line on frame 0, quiet natural sound, the final video.
No narration: the only words are the hook line and the two texts on the phone (rendered in the scene). -18 LUFS,
peaks under -3 dBTP. The last half second goes black; the phone buzzes in the dark and the cut back to frame 0 (the
first text, the same buzz) is the loop.

The phone buzzes twice on the duvet at once. A low room hush. Outside the door a floorboard creaks, then a soft settle
of weight as the feet arrive. Her held breath. The latch clicks as the handle reaches the bottom. The phone buzzes: the
second text. A long low creak as the door opens. A shaky breath as her phone dies. Black, and the buzz.
    python post.py                 frames from ../blender/renders/dont_open -> dont_open_1080x1920.mp4
    python post.py --audio-only    only writes mix.wav
Beat times match blender/scenes/dont_open_tail.py."""
import os, sys, subprocess, json, re, glob
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__)); args = sys.argv[1:]
FRAMES = os.path.join(HERE, '..', 'blender', 'renders', 'dont_open')
RAW, OUT, MIX = os.path.join(HERE, 'raw.mp4'), os.path.join(HERE, 'dont_open_1080x1920.mp4'), os.path.join(HERE, 'mix.wav')
HOOK = os.path.join(HERE, 'hook.png')
SR = 48000; DUR = 18.0
HOOK_LINES = ['Mum texted me', 'this at 2am.']
T_BUZZ1, T_CREAK, T_FEET, T_HOLD, T_LATCH, T_BUZZ2, T_OPEN, T_DARK, T_BLACK = 0.1, 5.6, 6.95, 9.0, 11.35, 12.0, 14.0, 16.5, 17.5
rng = np.random.default_rng(77); N = int(DUR * SR); L = np.zeros(N); R = np.zeros(N); T = np.arange(N) / SR


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


# room tone: a faint low hush, always
L += lowp(rng.standard_normal(N), 180, 2) * db(-46); R += lowp(rng.standard_normal(N), 180, 2) * db(-46)


def buzz():
    """a phone vibrating on a duvet: two muffled motor pulses"""
    n = int(0.9 * SR); x = np.arange(n) / SR; s = np.zeros(n)
    for a in (0.0, 0.5):
        i0, i1 = int(a * SR), int((a + 0.32) * SR); xx = x[i0:i1] - a
        motor = np.sign(np.sin(2 * np.pi * 172 * xx)) * (1 + 0.3 * np.sin(2 * np.pi * 23 * xx))
        env = np.minimum(1, xx / 0.015) * np.minimum(1, (0.32 - xx) / 0.03)
        s[i0:i1] += motor * env
    return norm(lowp(band(s, 90, 1400), 700))


for at in (T_BUZZ1, T_BUZZ2, T_BLACK + 0.05): put(buzz(), at, -24)


def creak(d, f0, lo=300, hi=2000, wob=0.25):
    n = int(d * SR); x = np.arange(n) / SR
    fr = f0 * (1 + wob * np.sin(2 * np.pi * .7 * x)); ph = 2 * np.pi * np.cumsum(fr) / SR
    s = (np.sin(ph) > .8).astype(float) * rng.uniform(.5, 1, n)
    return norm(band(s, lo, hi) * np.sin(np.pi * x / d) ** 2)


put(lowp(creak(0.6, 45, 200, 1400), 900), T_CREAK, -31, pan=0.35)        # a floorboard, outside the door (muffled)
n = int(0.25 * SR)
put(norm(lowp(rng.standard_normal(n), 160, 4) * decay(n, 0.04, 0.004)), T_FEET, -30, pan=0.35)   # weight settles outside


def breath(d, inhale=True, shaky=0.0):
    n = int(d * SR); x = np.arange(n) / SR
    env = np.sin(np.pi * x / d) ** (1.5 if inhale else 2.2)
    if shaky: env *= 1 + shaky * np.sin(2 * np.pi * 9 * x)
    return norm(band(rng.standard_normal(n), 400 if inhale else 250, 2600 if inhale else 1800) * env)


put(breath(0.35), 2.8, -33)                                              # she looks up from the phone
put(breath(0.4, True, 0.3), T_HOLD, -29)                                 # the breath she holds
put(breath(0.6, False, 0.6), T_DARK + 0.05, -29)                          # it shakes out as the phone dies


def latch():
    """a door latch released: a dry metal click with a short ring"""
    n = int(0.12 * SR); x = np.arange(n) / SR
    click = band(rng.standard_normal(n), 1500, 7000) * decay(n, 0.004, 0.0003)
    ring = (np.sin(2 * np.pi * 3100 * x) + 0.5 * np.sin(2 * np.pi * 4700 * x)) * decay(n, 0.02)
    return norm(click + 0.25 * ring)


put(latch(), 10.4, -36, pan=0.3)                                         # the handle starts to move
put(latch(), T_LATCH, -27, pan=0.3)                                      # and clicks at the bottom
put(creak(1.5, 21, 120, 1100, wob=0.12), T_OPEN, -27, pan=0.3)           # the long low creak of the door opening

mix = np.stack([L, R], 1); mix *= db(-3) / np.max(np.abs(mix))
mix *= db(5)                                                             # gentle peak limiter (as in the_garden/post.py)
from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
w = int(0.005 * SR)
g = np.minimum(1.0, db(-4) / np.maximum(maximum_filter1d(np.max(np.abs(mix), 1), 2 * w), 1e-9))
g = uniform_filter1d(minimum_filter1d(g, 2 * w), w)
mix *= g[:, None]
wavfile.write(MIX, SR, (mix * 32767).astype(np.int16)); print('wrote', MIX)
if '--audio-only' in args: sys.exit()

# the hook line: white, black outline, upper part of the frame, above the phone, on screen from frame 0
img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 96)
for k, line in enumerate(HOOK_LINES):
    d.text((540, 300 + k * 118), line, font=font, fill=(255, 255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0, 235), anchor='mm')
img.save(HOOK)

frames = sorted(glob.glob(os.path.join(FRAMES, '[0-9][0-9][0-9][0-9].png')))
lst = os.path.join(FRAMES, 'list.txt')
with open(lst, 'w') as f:
    for p in frames: f.write(f"file '{os.path.basename(p)}'\nduration {1 / 12}\n")
    f.write(f"file '{os.path.basename(frames[-1])}'\n")
subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-loop', '1', '-i', HOOK,
                '-filter_complex', '[0]fps=24,vignette=angle=PI/5,noise=alls=5:allf=t,'
                                   f'fade=t=out:st={T_BLACK}:d=0.08[v];'
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
