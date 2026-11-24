"""Don't Turn Around: sound for the silent render, then the final video (no words, no captions; the reel loops).
    python post.py                 reads raw.mp4 -> snowman_1080x1920.mp4
    python post.py --raw FILE      another silent render
    python post.py --audio-only    only writes mix.wav (to check the sound)
Beat times come from snowman.html (window.BEATS): looks back at 4.18 / 6.18 / 8.18 s, the reveal at 10.63 s, the end at 12.08 s."""
import os, sys, subprocess, json, re
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__)); args = sys.argv[1:]
RAW = os.path.join(HERE, args[args.index('--raw') + 1] if '--raw' in args else 'raw.mp4')
OUT = os.path.join(HERE, 'snowman_1080x1920.mp4'); MIX = os.path.join(HERE, 'mix.wav')
SR = 48000; DUR = 12.08
LOOKS = [(4.18, 5.68), (6.18, 7.68), (8.18, 9.88)]; REVEAL = 10.63; EYES = 11.55
rng = np.random.default_rng(7); N = int(DUR * SR); L = np.zeros(N); Rr = np.zeros(N)
t = np.arange(N) / SR
def band(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def lowp(x, f, o=2): return sosfilt(butter(o, f, 'lowpass', fs=SR, output='sos'), x)
def put(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR); n = min(len(sig), N - i)
    if n <= 0: return
    L[i:i + n] += sig[:n] * gain * (1 - max(0, pan)); Rr[i:i + n] += sig[:n] * gain * (1 + min(0, pan))
def env(n, a=.005, d=.3):
    e = np.ones(n); ia = int(a * SR); e[:ia] = np.linspace(0, 1, ia) if ia else 1
    return e * np.exp(-np.arange(n) / SR / d)

# wind: soft filtered noise breathing slowly; the tail is folded onto the head so the loop has no seam
w = band(rng.standard_normal(N + SR), 180, 1400) * .25
wl = w[:N] * (.55 + .45 * np.sin(2 * np.pi * t / 6.04) ** 2); fold = SR // 2
wl[:fold] = wl[:fold] * np.linspace(0, 1, fold) + w[N:N + fold] * np.linspace(1, 0, fold) * (.55 + .45 * np.sin(2 * np.pi * (t[:fold] + DUR) / 6.04) ** 2)
duck = np.ones(N); a, b = int((LOOKS[2][1] + .05) * SR), int(REVEAL * SR)     # the silent beat before the reveal
duck[a:b] = np.linspace(1, .04, b - a); duck[b:] = .6
L += wl * duck; Rr += np.roll(wl, 977) * duck

# music box: a little tune of my own while she builds it, then one wrong note at each look back (lower and flatter every time)
def bell(f, d=1.6, g=1.0):
    n = int(d * SR); x = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * m * x) * np.exp(-x / (d * dd)) for m, a, dd in [(1, 1, .5), (2.76, .35, .18), (5.4, .15, .08), (8.9, .06, .04)])
    return s * env(n, .002, 10) * g * .18
NOTE = lambda m: 440 * 2 ** ((m - 69) / 12)
for i, (at, m) in enumerate([(.05, 76), (.4, 79), (.75, 81), (1.1, 79), (1.45, 76), (1.8, 74), (2.15, 76), (2.85, 72), (3.2, 74), (3.55, 71)]):
    put(bell(NOTE(m)), at, .9, pan=.2 * ((i % 3) - 1))
for k, (a0, _) in enumerate(LOOKS): put(bell(NOTE([70, 66.6, 61.3][k]), 2.2, 1.2), a0 - .02, 1.0)

# snow: her footsteps going off (crunch = short bright noise bursts), pats on the snowman, and its heavier crunch just before each look
def crunch(g=1.0, d=.09, lo=900, hi=6000):
    n = int(d * SR); x = rng.standard_normal(n) * (rng.random(n) < .35)
    return band(x, lo, hi) * env(n, .003, d / 3) * g
for at in np.arange(2.35, 3.85, .29): put(crunch(.9), at + rng.uniform(-.02, .02), 1.0, pan=rng.uniform(-.2, .2))
for at in [.87, 1.2, 1.45]: put(lowp(rng.standard_normal(int(.08 * SR)), 500) * env(int(.08 * SR), .002, .03), at, 1.2)
for k, (a0, _) in enumerate(LOOKS): put(crunch(1.8 + k * .4, .22, 200, 2500), a0 - .45, 1.0, pan=-.3)     # it moved (off screen)

# the reveal: a low hit, an icy scrape and a breath out of it; then her heartbeat as her eyes go wide
n = int(1.4 * SR); x = np.arange(n) / SR
hit = np.sin(2 * np.pi * (48 * x - 10 * x ** 2)) * np.exp(-x / .5) * 1.1 + lowp(rng.standard_normal(n), 220) * np.exp(-x / .25) * .8
scrape = band(rng.standard_normal(n), 3000, 9000) * np.exp(-x / .6) * .35 + np.sin(2 * np.pi * (2400 - 900 * x) * x) * np.exp(-x / .5) * .05
breath = band(rng.standard_normal(n), 300, 1800) * np.sin(np.pi * np.clip(x / 1.1, 0, 1)) * .25
put(hit + scrape + breath, REVEAL, 1.0)
for at in [EYES, EYES + .42]: m = int(.18 * SR); y = np.arange(m) / SR; put(np.sin(2 * np.pi * 55 * y) * np.exp(-y / .06), at, .9)

mix = np.stack([L, Rr], 1); mix /= np.max(np.abs(mix)) * 1.15
wavfile.write(MIX, SR, (mix * 32767).astype(np.int16)); print('wrote', MIX)
if '--audio-only' in args: sys.exit()

# the video: silent render + the mix, loudness to -14 LUFS (two passes)
m = subprocess.run(['ffmpeg', '-hide_banner', '-i', MIX, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
j = json.loads(re.findall(r'\{[^{}]*\}', m)[-1])
ln = f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', RAW, '-i', MIX, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', ln, '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], check=True)
print('saved', OUT)
