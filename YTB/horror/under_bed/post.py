"""Haru #2 "Something Under the Bed": sound for the silent render, 1.5 s of black at the end, then the final video.
No words, no captions; the reel loops (the last breath in the dark runs into her happy steps at the start).
    python post.py                       frames from ../blender/renders/under_bed -> under_bed_1080x1920.mp4
    python post.py --audio-only          only writes mix.wav
Needs: numpy scipy imageio-ffmpeg. Beat times match blender/scenes/under_bed_tail.py."""
import os, sys, subprocess, json, re, glob
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__)); args = sys.argv[1:]
FRAMES = os.path.join(HERE, '..', 'blender', 'renders', 'under_bed')
RAW, OUT, MIX = os.path.join(HERE, 'raw.mp4'), os.path.join(HERE, 'under_bed_1080x1920.mp4'), os.path.join(HERE, 'mix.wav')
SR = 48000; RENDER = 15.5; DUR = 17.0
SHAPE, LOOK, SHRUG, DOOR, BED, LAMP, EYES, HAND, OPEN = 0.62, 1.5, 3.0, 4.0, 5.2, 6.5, 9.0, 10.0, 14.0
rng = np.random.default_rng(11); N = int(DUR * SR); L = np.zeros(N); R = np.zeros(N); t = np.arange(N) / SR


def band(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def lowp(x, f, o=2): return sosfilt(butter(o, f, 'lowpass', fs=SR, output='sos'), x)
def env(n, a=.005, d=.3):
    e = np.ones(n); ia = int(a * SR); e[:ia] = np.linspace(0, 1, ia) if ia else 1
    return e * np.exp(-np.arange(n) / SR / d)
def put(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR); n = min(len(sig), N - i)
    if n <= 0: return
    L[i:i + n] += sig[:n] * gain * (1 - max(0, pan)); R[i:i + n] += sig[:n] * gain * (1 + min(0, pan))


# room tone all through (quiet, a little warmer while the hall light is on)
tone = lowp(rng.standard_normal(N), 300) * .05
L += tone; R += np.roll(tone, 1601)

# a cheerful little music-box tune while she comes in... cut dead the instant the shape passes behind her
def bell(f, d=1.2, g=1.0):
    n = int(d * SR); x = np.arange(n) / SR
    return sum(a * np.sin(2 * np.pi * f * m * x) * np.exp(-x / (d * dd)) for m, a, dd in [(1, 1, .5), (2.76, .3, .18), (5.4, .12, .08)]) * env(n, .002, 10) * g * .16
NOTE = lambda m: 440 * 2 ** ((m - 69) / 12)
tune = np.zeros(int(1.5 * SR))
for at, m in [(0.0, 79), (0.15, 83), (0.3, 86), (0.45, 83), (0.6, 88), (0.75, 86), (0.9, 83)]:
    b = bell(NOTE(m)); i = int(at * SR); tune[i:i + len(b)] += b[:len(tune) - i]
cut = int(SHAPE * SR); tune[cut:] *= np.exp(-np.arange(len(tune) - cut) / SR / .02)
put(tune, 0.0, 1.0)

# her light, quick footsteps (happy), then calmer ones to the bed
def step(g=1.0):
    n = int(.07 * SR); return lowp(rng.standard_normal(n), 900) * env(n, .002, .02) * g
for at in np.arange(0.05, LOOK, .27): put(step(.9), at, 1.0, pan=rng.uniform(-.1, .1))
for at in np.arange(DOOR + .1, BED, .3): put(step(.7), at, 1.0, pan=.1)

# the shape: a fast whoosh across, left to right, behind her
n = int(.45 * SR); x = np.arange(n) / SR
wh = band(rng.standard_normal(n), 400, 3500) * np.sin(np.pi * np.clip(x / .45, 0, 1)) ** 2 * .9
pan = np.linspace(-.8, .8, n)
i = int((SHAPE - .1) * SR); L[i:i + n] += wh * (1 - np.maximum(0, pan)); R[i:i + n] += wh * (1 + np.minimum(0, pan))

# the look back: a held silence, then a small "hm" breath out and the shrug's rustle
n = int(.35 * SR); x = np.arange(n) / SR
put(band(rng.standard_normal(n), 250, 1200) * np.sin(np.pi * x / .35) * .35, SHRUG - .1, 1.0)
n = int(.5 * SR); put(band(rng.standard_normal(n), 1500, 7000) * env(n, .05, .15) * .25, SHRUG + .2, 1.0)

# the door clicks shut; the bed creaks twice; a blanket rustle; the lamp clicks off
def click(g=1.0, f=2500):
    n = int(.05 * SR); return band(rng.standard_normal(n), f, f * 2.5) * env(n, .0005, .006) * g
put(click(1.4, 1200) + np.pad(click(1.0, 700), (int(.04 * SR), 0))[:int(.05 * SR)], DOOR, 1.0, pan=.4)
def creak(d=.5, f0=380, g=1.0):
    n = int(d * SR); x = np.arange(n) / SR
    fr = f0 * (1 + .25 * np.sin(2 * np.pi * 3 * x)) ; ph = 2 * np.pi * np.cumsum(fr) / SR
    s = np.sign(np.sin(ph)) * (rng.random(n) < .5) ; return band(s, 300, 2500) * np.sin(np.pi * x / d) * g * .25
put(creak(.45, 340), BED + .15, 1.0); put(creak(.6, 300), BED + 1.0, .9)
n = int(.7 * SR); put(band(rng.standard_normal(n), 1200, 6000) * np.sin(np.pi * np.arange(n) / n) * .2, BED + .5, 1.0)
put(click(1.6, 1800), LAMP, 1.0, pan=-.3)

# night: her slow breathing and a clock ticking; the clock stops dead when the eyes open under the bed
for at in np.arange(LAMP + .6, OPEN, 2.2):
    n = int(1.6 * SR); x = np.arange(n) / SR
    put(band(rng.standard_normal(n), 200, 1500) * np.sin(np.pi * x / 1.6) ** 2 * .12, at, 1.0)
for at in np.arange(LAMP + .2, EYES, .5): put(click(.5, 3500), at, 1.0, pan=-.5 if int(at * 2) % 2 else -.4)

# the eyes, the hand: a low drone that swells, dry joint creaks, fingertips dragging on the sheet
i0, i1 = int(EYES * SR), int(OPEN * SR); n = i1 - i0; x = np.arange(n) / SR
drone = (np.sin(2 * np.pi * 41 * x) + .5 * np.sin(2 * np.pi * 61.7 * x) + .3 * band(rng.standard_normal(n), 60, 200)) * (x / x[-1]) ** 1.6 * .5
L[i0:i1] += drone; R[i0:i1] += drone
for at in (HAND + .2, HAND + 1.0, HAND + 1.9, HAND + 2.7, HAND + 3.4, HAND + 3.8):
    n = int(.12 * SR); y = np.arange(n) / SR
    put(band(rng.standard_normal(n) * (rng.random(n) < .15), 800, 5000) * env(n, .001, .03) * .9, at, 1.0, pan=-.2)
n = int(1.6 * SR); put(band(rng.standard_normal(n), 2500, 8000) * np.sin(np.pi * np.arange(n) / n) * .08, HAND + 1.6, 1.0)

# her eyes snap open: a sharp hit and a screech, then silence; in the black, one breath
n = int(1.2 * SR); x = np.arange(n) / SR
hit = (np.sin(2 * np.pi * (52 * x - 12 * x ** 2)) * np.exp(-x / .35) * 1.2 + lowp(rng.standard_normal(n), 250) * np.exp(-x / .15)
       + np.sin(2 * np.pi * (1800 + 600 * x) * x) * np.exp(-x / .25) * .12)
put(hit, OPEN + .02, 1.0)
gate = np.ones(N); a = int((OPEN + .9) * SR); gate[a:] = .25; L *= gate; R *= gate
n = int(1.0 * SR); x = np.arange(n) / SR
put(band(rng.standard_normal(n), 300, 2000) * np.sin(np.pi * x / 1.0) ** 2 * .4, RENDER + .35, 1.0)

mix = np.stack([L, R], 1); mix /= np.max(np.abs(mix)) * 1.15
wavfile.write(MIX, SR, (mix * 32767).astype(np.int16)); print('wrote', MIX)
if '--audio-only' in args: sys.exit()

# picture: the 12 fps frames on twos at 24 fps, grain and vignette, then 1.5 s of black
frames = sorted(glob.glob(os.path.join(FRAMES, '[0-9][0-9][0-9][0-9].png')))
lst = os.path.join(FRAMES, 'list.txt')
with open(lst, 'w') as f:
    for p in frames: f.write(f"file '{os.path.basename(p)}'\nduration {1 / 12}\n")
    f.write(f"file '{os.path.basename(frames[-1])}'\n")
subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                '-vf', f'fps=24,vignette=angle=PI/5,noise=alls=5:allf=t,tpad=stop_mode=add:stop_duration={DUR - RENDER}:color=black,format=yuv420p',
                '-t', str(DUR), '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-movflags', '+faststart', RAW], check=True)
m = subprocess.run([FF, '-hide_banner', '-i', MIX, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
j = json.loads(re.findall(r'\{[^{}]*\}', m)[-1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
      f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run([FF, '-y', '-v', 'error', '-i', RAW, '-i', MIX, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', ln, '-ar', '48000',
                '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], check=True)
small = OUT.replace('.mp4', '_small.mp4')
subprocess.run([FF, '-y', '-v', 'error', '-i', OUT, '-c:v', 'libx264', '-crf', '24', '-preset', 'slow', '-c:a', 'copy', '-movflags', '+faststart', small], check=True)
print('saved', OUT, small)
