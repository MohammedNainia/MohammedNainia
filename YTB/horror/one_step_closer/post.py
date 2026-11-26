"""Haru #4 "One Step Closer": quiet, natural sound for the silent render, 1 s of black at the end, then the final video.
No words, no captions. Mixed low like Lights Off: -18 LUFS, peaks under -3 dBTP, effects sit just over the room tone,
one short soft swell at the reveal.
    python post.py                       frames from ../blender/renders/one_step_closer -> one_step_closer_1080x1920.mp4
    python post.py --audio-only          only writes mix.wav
Needs: numpy scipy imageio-ffmpeg. Beat times match blender/scenes/one_step_closer.py (FLICKS, RUN0, A)."""
import os, sys, subprocess, json, re, glob
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__)); args = sys.argv[1:]
FRAMES = os.path.join(HERE, '..', 'blender', 'renders', 'one_step_closer')
RAW, OUT, MIX = os.path.join(HERE, 'raw.mp4'), os.path.join(HERE, 'one_step_closer_1080x1920.mp4'), os.path.join(HERE, 'mix.wav')
SR = 48000; RENDER = 19.85; DUR = RENDER + 1.0
A = 13.05; RUN0 = 11.0                                          # she is in her room at A (from the scene's RUN line)
FLICKS = [2.5, 6.3, 7.5, 8.0, 8.5, 8.8, 9.1, 9.4, 10.0]         # dark at the start, every flick toggles the stair light
def lit(t): return sum(t >= x for x in FLICKS) % 2 == 1 and t < A + 0.5
MOVED = [6.3, 8.0, 8.8, 9.4]                                    # the light goes off and it is closer
rng = np.random.default_rng(41); N = int(DUR * SR); L = np.zeros(N); R = np.zeros(N); T = np.arange(N) / SR


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


# room tone: dark air in a big old house, always; the faint hum of the stair bulb while it is on
air = lowp(rng.standard_normal(N), 200, 4) * 0.35
on = np.array([lit(x) for x in T[::480]]).repeat(480)[:N].astype(float)
on = np.convolve(on, np.ones(240) / 240, 'same')
hum = (np.sin(2 * np.pi * 100 * T) * .6 + np.sin(2 * np.pi * 200 * T) * .25) * 0.04 * on
L += air * db(-30) + hum * db(-16); R += np.roll(air, 3301) * db(-30) + hum * db(-16)


def switch_click():
    n = int(.08 * SR); s = np.zeros(n)
    tick = band(rng.standard_normal(n), 3500, 9000) * decay(n, .0015)
    clack = band(rng.standard_normal(n), 900, 3000, 3) * decay(n, .005); k = int(.009 * SR)
    thump = np.sin(2 * np.pi * 140 * np.arange(n) / SR) * decay(n, .012)
    s += tick * .6; s[k:] += clack[:n - k] * 1.0 + thump[:n - k] * .5
    return norm(s)
for x in FLICKS: put(switch_click(), x - 0.02, -14, pan=.25)


def creak(d, f0, g=1.0):
    """a stair tread taking weight: a slow stick-slip creak through a narrow wooden resonance"""
    n = int(d * SR); x = np.arange(n) / SR
    fr = f0 * (1 + .18 * np.sin(2 * np.pi * 1.3 * x)); ph = 2 * np.pi * np.cumsum(fr) / SR
    s = (np.sin(ph) > .7).astype(float) * rng.uniform(.6, 1, n)
    return norm(band(s, 250, 1400) * np.sin(np.pi * x / d) ** 2) * g
for i, x in enumerate(MOVED): put(creak(.5 - .05 * i, 62 + 6 * i), x + 0.06, -29 + 1.5 * i, pan=-.1)   # each time, a little nearer


def breath(d, inhale=True, shaky=0.0):
    n = int(d * SR); x = np.arange(n) / SR
    env = np.sin(np.pi * x / d) ** (1.5 if inhale else 2.2)
    if shaky: env *= 1 + shaky * np.sin(2 * np.pi * 9 * x)
    return norm(band(rng.standard_normal(n), 400 if inhale else 250, 2600 if inhale else 1800) * env)
put(breath(.6), 3.4, -31)                                      # an ordinary breath: nothing there
put(breath(.7, False), 5.6, -31)                               # a tired sigh after rubbing her eyes
for i, x in enumerate((6.7, 7.2, 7.75, 8.25, 8.65, 9.0)): put(breath(.3, i % 2 == 0, .5), x, -28)    # faster and faster
put(breath(.35, True, .6), 9.5, -26)                           # she draws a breath... and holds it
put(breath(.45, True, .4), 10.05, -24)                         # the gasp as the light comes on
for i in range(6): put(breath(.18, i % 2 == 0, .3), RUN0 + .25 + i * .33, -29)   # panting as she runs
put(breath(1.3, False, .25), A + 1.4, -27)                     # leaning on the door: the long breath out
put(breath(.4, True, .6), A + 4.5, -29)                        # a small breath in as she turns her head


def step(wood=True, heavy=1.0):
    """a running sneaker: on the runner a dull thud and fibre brush; on bare boards a firmer knock, still soft"""
    n = int(.14 * SR)
    thud = lowp(rng.standard_normal(n), 220 if wood else 150, 4) * decay(n, .025 if wood else .03, .003)
    top = band(rng.standard_normal(n), 900, 3000) * decay(n, .012 if wood else .04, .004) * (.25 if wood else .1)
    return norm(thud + top) * heavy
x = RUN0 + 0.12; i = 0
while x < A - 0.05:                                            # the landing runner, then the boards of her room
    put(step(wood=x > A - 0.45), x, -24 if x > A - 0.45 else -26, pan=.15 * (-1) ** i); x += 0.19; i += 1
put(step(True, .8), A + 1.0, -28); put(step(True, .7), A + 1.2, -29)   # she steps back to the door


def door_shut():
    """a light interior door closing: a soft wooden bump and the latch catching, not a slam"""
    n = int(.25 * SR); x = np.arange(n) / SR
    bump = lowp(rng.standard_normal(n), 180, 4) * decay(n, .04, .003)
    latch = band(rng.standard_normal(n), 2000, 6000) * decay(n, .004); k = int(.03 * SR)
    s = bump.copy(); s[k:] += latch[:n - k] * .5
    return norm(s)
put(door_shut(), A + 0.82, -17, pan=.2)


def tone(d, freqs, rise=1.0):
    n = int(d * SR); x = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * x + p) for f, p in zip(freqs, (0, 1.3, 2.1))) * (x / d) ** rise * np.minimum(1, (d - x) / .15)
    return norm(s)
put(tone(1.8, (41, 43.5)), 0.2, -27)                           # dread under the first shot, barely there
put(tone(1.4, (38, 39.6, 57)), 8.6, -25)                       # rising under the fast flicks
# the reveal: a soft low swell and a thin wrong high note, both short, then the black
n = int(1.6 * SR); x = np.arange(n) / SR
sw = np.sin(2 * np.pi * (44 - 5 * x) * x) * np.exp(-x / .7) * np.minimum(1, x / .25) + lowp(rng.standard_normal(n), 160) * np.exp(-x / .4) * .4
hi = np.sin(2 * np.pi * 1480 * x) * np.sin(2 * np.pi * 1523 * x) * np.exp(-x / .8) * np.minimum(1, x / .08)
put(norm(sw), A + 4.65, -15); put(hi, A + 4.7, -31)
gate = np.ones(N); a = int(RENDER * SR); gate[a:a + 4800] = np.linspace(1, .12, 4800); gate[a + 4800:] = .12
L *= gate; R *= gate                                           # black: near silence

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
