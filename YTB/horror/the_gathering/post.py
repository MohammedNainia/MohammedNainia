"""Haru #5 "The Gathering": quiet, natural sound for the silent render, a short black tail, then the final video.
No words, no captions. Mixed low like the others: -18 LUFS, peaks under -3 dBTP.

Sound leads picture: a far hummed chant from the first frame, growing as she follows it, cut dead at 15.0 s (the
silence before the face). Steps on the pavement, then soft creeping steps on grass. The doors creak in the wind.
When every head turns: a dry rustle of necks and seeds, her gasp, and the whole ring hums one low note into the black.
    python post.py                       frames from ../blender/renders/the_gathering -> the_gathering_1080x1920.mp4
    python post.py --audio-only          only writes mix.wav
Needs: numpy scipy imageio-ffmpeg. Beat times match blender/scenes/the_gathering.py."""
import os, sys, subprocess, json, re, glob
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__)); args = sys.argv[1:]
FRAMES = os.path.join(HERE, '..', 'blender', 'renders', 'the_gathering')
RAW, OUT, MIX = os.path.join(HERE, 'raw.mp4'), os.path.join(HERE, 'the_gathering_1080x1920.mp4'), os.path.join(HERE, 'mix.wav')
SR = 48000; RENDER = 19.6; DUR = RENDER + 0.9
T_WALK, T4, T_PEEK, STOP, LIFT, WIDE, TURN = 3.3, 8.0, 11.4, 15.0, 15.5, 17.3, 18.3
rng = np.random.default_rng(55); N = int(DUR * SR); L = np.zeros(N); R = np.zeros(N); T = np.arange(N) / SR


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


# night air outside: soft wind in waves, always; it dips a little when the chant stops
wind = band(rng.standard_normal(N), 80, 900, 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * T + 1.0))
wind_g = 1 - 0.45 * ramp(T, STOP, STOP + 0.05)
L += wind * wind_g * db(-31); R += np.roll(wind, 7001) * wind_g * db(-31)


# the chant: nine voices humming one slow minor phrase, pulsing with the sway (a beat every 1.43 s)
def voice(f0, vowel, seed):
    r = np.random.default_rng(seed)
    vib = 1 + 0.006 * np.sin(2 * np.pi * r.uniform(4.5, 5.5) * T + r.uniform(0, 6)) + 0.003 * lowp(r.standard_normal(N), 3)
    phrase = np.where((T % 5.72) < 2.86, 1.0, 2 ** (-2 / 12))          # the phrase steps down a tone and back
    ph = 2 * np.pi * np.cumsum(f0 * vib * phrase) / SR
    src = sum(np.sin(k * ph) / k for k in range(1, 18))                 # a soft sawtooth: a throat
    fm = {'oo': ((300, 120), (870, 150)), 'mm': ((250, 100), (2200, 300)), 'ah': ((700, 140), (1150, 180))}[vowel]
    return sum(band(src, f - w, f + w) * g for (f, w), g in zip(fm, (1.0, 0.35)))
chant = np.zeros(N)
for i, (f0, vw) in enumerate(((98, 'mm'), (98.6, 'oo'), (116.5, 'mm'), (117.2, 'oo'), (146.8, 'mm'), (130.8, 'oo'),
                              (196, 'mm'), (73.4, 'oo'), (87.3, 'mm'))):
    chant += voice(f0, vw, i) * (0.7 + 0.6 * ((i * 37) % 10) / 10)
pulse = 0.65 + 0.35 * np.maximum(0, np.sin(2 * np.pi * T / 1.43 - 1.2)) ** 2
chant = norm(chant) * pulse
near = ramp(T, 0, T_PEEK) ** 1.6                                         # far and muffled at first, clear at the reveal
far_ch = lowp(chant, 500, 4); chant = far_ch * (1 - near) + chant * near
level = db(-40 + 20 * near) * (1 - ramp(T, STOP, STOP + 0.03))          # ... and cut dead
L += chant * level; R += np.roll(chant, 400) * level


def door_creak(d, f0):
    n = int(d * SR); x = np.arange(n) / SR
    fr = f0 * (1 + .25 * np.sin(2 * np.pi * .7 * x)); ph = 2 * np.pi * np.cumsum(fr) / SR
    s = (np.sin(ph) > .8).astype(float) * rng.uniform(.5, 1, n)
    return norm(band(s, 300, 2000) * np.sin(np.pi * x / d) ** 2)
for x, f0, p in ((0.4, 38, -.4), (5.0, 44, .5), (9.6, 33, -.6)): put(door_creak(1.1, f0), x, -33, pan=p)


def step(soft=False, heavy=1.0):
    """a small sneaker on pavement (a dull tap and grit), or creeping on grass (a hush of blades)"""
    n = int(.16 * SR)
    if soft:
        s = band(rng.standard_normal(n), 1500, 6000) * decay(n, .05, .02) + lowp(rng.standard_normal(n), 120, 4) * decay(n, .02, .005) * .5
    else:
        s = lowp(rng.standard_normal(n), 260, 4) * decay(n, .022, .002) + band(rng.standard_normal(n), 2500, 7000) * decay(n, .01, .002) * .3
    return norm(s) * heavy
x = T_WALK + 0.25; i = 0
while x < T4 - 0.1: put(step(), x, -27, pan=.12 * (-1) ** i); x += 0.47; i += 1
x = T4 + 0.2; i = 0
while x < T_PEEK - 0.1: put(step(True, .8), x, -32, pan=.1 * (-1) ** i); x += 0.62; i += 1


def breath(d, inhale=True, shaky=0.0):
    n = int(d * SR); x = np.arange(n) / SR
    env = np.sin(np.pi * x / d) ** (1.5 if inhale else 2.2)
    if shaky: env *= 1 + shaky * np.sin(2 * np.pi * 9 * x)
    return norm(band(rng.standard_normal(n), 400 if inhale else 250, 2600 if inhale else 1800) * env)
put(breath(.5), 2.7, -32)                                               # she hears it
put(breath(.35, True, .5), T_PEEK + 0.5, -27)                           # the reveal: a small caught breath
put(breath(.45, True, .6), TURN + 0.15, -22)                            # every head turns: the gasp


def tone(d, freqs, rise=1.0):
    n = int(d * SR); x = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * x + p) for f, p in zip(freqs, (0, 1.3, 2.1))) * (x / d) ** rise * np.minimum(1, (d - x) / .2)
    return norm(s)
put(tone(2.2, (41, 43.2)), LIFT, -27, 0)                                # under the lift, barely there


def crackle(d, dens):
    """dry seeds shifting / stiff necks turning: sparse clicks through a woody band"""
    n = int(d * SR); s = np.zeros(n)
    for k in rng.integers(0, n - 400, int(dens * d)): s[k:k + 300] += rng.standard_normal(300) * decay(300, .0015)
    return norm(band(s, 600, 4000) * np.sin(np.pi * np.arange(n) / n) ** .5)
put(crackle(.5, 60), WIDE - 0.05, -28)                                  # the grin opens
put(crackle(.35, 140), TURN, -21, pan=-.15)                             # nine necks turn at once

# then the whole ring hums one low note at her, into the black, and it fades with the black
n = int((DUR - TURN - 0.3) * SR); x = np.arange(n) / SR
hum = sum(np.sin(2 * np.pi * f * x + p) / k for k, (f, p) in enumerate(((65.4, 0), (65.9, 1), (98, 2), (130.8, 3)), 1))
hum = band(hum + 0.3 * sum(np.sin(2 * np.pi * 65.4 * m * x) / m for m in range(2, 9)), 50, 900)
env = np.minimum(1, x / 0.25) * np.clip((DUR - TURN - 0.3 - x) / 0.6, 0, 1)
put(norm(hum) * env, TURN + 0.3, -20)

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
