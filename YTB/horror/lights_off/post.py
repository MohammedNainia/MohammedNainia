"""Haru #3 "Lights Off": quiet, natural sound for the silent render, 1.5 s of black at the end, then the final video.
No words, no captions; the reel loops. Mixed low on purpose (the user found the last one too loud): -18 LUFS, peaks
under -3 dBTP, every effect sits under or just above the room tone; the only swell is short and soft.
    python post.py                       frames from ../blender/renders/lights_off -> lights_off_1080x1920.mp4
    python post.py --audio-only          only writes mix.wav
Needs: numpy scipy imageio-ffmpeg. Beat times match blender/scenes/lights_off_tail.py (OFF_ON)."""
import os, sys, subprocess, json, re, glob
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__)); args = sys.argv[1:]
FRAMES = os.path.join(HERE, '..', 'blender', 'renders', 'lights_off')
RAW, OUT, MIX = os.path.join(HERE, 'raw.mp4'), os.path.join(HERE, 'lights_off_1080x1920.mp4'), os.path.join(HERE, 'mix.wav')
SR = 48000; RENDER = 11.5; DUR = 13.0
FLICKS = [0.85, 2.4, 3.9, 5.4, 6.9, 10.0, 11.4]
def lit(t): return sum(t >= x for x in FLICKS) % 2 == 0
rng = np.random.default_rng(23); N = int(DUR * SR); L = np.zeros(N); R = np.zeros(N); T = np.arange(N) / SR


def band(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def lowp(x, f, o=2): return sosfilt(butter(o, f, 'lowpass', fs=SR, output='sos'), x)
def db(x): return 10 ** (x / 20)
def put(sig, at, gain_db=0.0, pan=0.0):
    i = int(at * SR); n = min(len(sig), N - i)
    if n <= 0: return
    g = db(gain_db); L[i:i + n] += sig[:n] * g * (1 - max(0, pan)); R[i:i + n] += sig[:n] * g * (1 + min(0, pan))
def decay(n, tau, attack=0.0005):
    e = np.exp(-np.arange(n) / SR / tau); ia = max(1, int(attack * SR)); e[:ia] *= np.linspace(0, 1, ia); return e


# room tone: a soft, dark air (always) and the faint electrical hum of the ceiling light (only while it is on)
air = lowp(rng.standard_normal(N), 220, 4) * 0.35
on = np.array([lit(x) for x in T[::480]]).repeat(480)[:N].astype(float)
on = np.convolve(on, np.ones(240) / 240, 'same')                                  # no clicks at the edges
hum = (np.sin(2 * np.pi * 100 * T) * .6 + np.sin(2 * np.pi * 200 * T) * .25 + np.sin(2 * np.pi * 300 * T) * .1) * 0.04 * on
L += air * db(-30) + hum * db(-14); R += np.roll(air, 3301) * db(-30) + hum * db(-14)


def switch_click():
    """a wall rocker switch: a small plastic tick, then the clack of the rocker seating, and a tiny thump in the wall"""
    n = int(.08 * SR); s = np.zeros(n)
    tick = band(rng.standard_normal(n), 3500, 9000) * decay(n, .0015)
    clack = band(rng.standard_normal(n), 900, 3000, 3) * decay(n, .005); k = int(.009 * SR)
    thump = np.sin(2 * np.pi * 140 * np.arange(n) / SR) * decay(n, .012)
    s += tick * .6; s[k:] += clack[:n - k] * 1.0 + thump[:n - k] * .5
    return s / np.max(np.abs(s))
for x in FLICKS: put(switch_click(), x - 0.02, -14 if x != 10.0 else -12, pan=.25)


def carpet_step(heavy=1.0):
    """a soft shoe on carpet: a dull low thud and the brush of fibres, nothing sharp"""
    n = int(.16 * SR)
    thud = lowp(rng.standard_normal(n), 160, 4) * decay(n, .03, .004)
    brush = band(rng.standard_normal(n), 1200, 3800) * decay(n, .045, .01) * .12
    s = thud + brush; return s / np.max(np.abs(s)) * heavy
for x, g in ((2.55, -26), (2.85, -28), (5.6, -27), (8.6, -29)): put(carpet_step(), x, g, pan=.1)


def breath(d, inhale=True, shaky=0.0):
    n = int(d * SR); x = np.arange(n) / SR
    env = np.sin(np.pi * x / d) ** (1.5 if inhale else 2.2)
    if shaky: env *= 1 + shaky * np.sin(2 * np.pi * 9 * x)
    s = band(rng.standard_normal(n), 400 if inhale else 250, 2600 if inhale else 1800) * env; return s / np.max(np.abs(s))
put(breath(.5), 2.45, -30)                                    # a small breath as she looks round
for i, x in enumerate((7.05, 7.55, 8.0)): put(breath(.42, i % 2 == 0, .5), x, -27)   # shaky breaths in the dark
put(breath(.35, True, .6), 9.35, -27)                         # she draws a breath... and holds it
put(breath(.9, False, .7), RENDER + .45, -29)                 # in the black: a trembling breath out (runs into the loop)


def creak(d, f0, g=1.0):
    """slow wood creak: a stick-slip buzz through a narrow resonance"""
    n = int(d * SR); x = np.arange(n) / SR
    fr = f0 * (1 + .18 * np.sin(2 * np.pi * 1.3 * x)); ph = 2 * np.pi * np.cumsum(fr) / SR
    s = (np.sin(ph) > .7).astype(float) * rng.uniform(.6, 1, n)
    s = band(s, 250, 1400) * np.sin(np.pi * x / d) ** 2; return s / np.max(np.abs(s)) * g
put(creak(.9, 70), 4.35, -27, pan=-.3)                        # something shifts on the ceiling
put(creak(.6, 55), 5.75, -30, pan=-.3)                        # the bed, settling where it sat


def tone(d, freqs, rise=1.0):
    n = int(d * SR); x = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * x + p) for f, p in zip(freqs, (0, 1.3, 2.1))) * (x / d) ** rise * np.minimum(1, (d - x) / .15)
    return s / np.max(np.abs(s))
put(tone(1.4, (41, 43.5)), 1.0, -26)                          # dread under the eyes in the corner (barely there)
put(tone(1.5, (38, 39.6, 57)), 8.5, -24, )                    # the reach in the dark, rising
# the light snaps on beside it: a soft low swell and a thin, wrong high note, both short
n = int(1.3 * SR); x = np.arange(n) / SR
sw = (np.sin(2 * np.pi * (46 - 6 * x) * x) * np.exp(-x / .5) + lowp(rng.standard_normal(n), 180) * np.exp(-x / .3) * .5)
hi = np.sin(2 * np.pi * 1480 * x) * np.sin(2 * np.pi * 1523 * x) * np.exp(-x / .6) * np.minimum(1, x / .05)
put(sw / np.max(np.abs(sw)), 10.0, -14); put(hi, 10.02, -30)
gate = np.ones(N); a = int(RENDER * SR); gate[a:a + 2400] = np.linspace(1, .15, 2400); gate[a + 2400:] = .15
L *= gate; R *= gate                                          # the light goes off: near silence

mix = np.stack([L, R], 1); mix *= db(-3) / np.max(np.abs(mix))
wavfile.write(MIX, SR, (mix * 32767).astype(np.int16)); print('wrote', MIX)
if '--audio-only' in args: sys.exit()

frames = sorted(glob.glob(os.path.join(FRAMES, '[0-9][0-9][0-9][0-9].png')))
lst = os.path.join(FRAMES, 'list.txt')
with open(lst, 'w') as f:
    for p in frames: f.write(f"file '{os.path.basename(p)}'\nduration {1 / 12}\n")
    f.write(f"file '{os.path.basename(frames[-1])}'\n")
subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                '-vf', f'fps=24,vignette=angle=PI/5,noise=alls=5:allf=t,tpad=stop_mode=add:stop_duration={DUR - RENDER}:color=black,format=yuv420p',
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
