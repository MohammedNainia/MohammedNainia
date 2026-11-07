"""Code-made ambience: wind + star chimes (+ optional synth piano) -> build/soundtrack.wav, timed via timing.json."""
import numpy as np, wave, os
import json, sys
from config import OUT, HERE
TM = json.load(open(os.path.join(HERE, 'timing.json'))); KV, KS = zip(*TM['knots'])
def V(story): return float(np.interp(story, KS, KV))          # story time -> video time
WITH_PIANO = '--piano' in sys.argv
SR, DUR = 44100, TM['duration']
N = int(SR * DUR); t = np.arange(N) / SR
rng = np.random.default_rng(3)
L = np.zeros(N); R = np.zeros(N)

def midi(m): return 440 * 2 ** ((m - 69) / 12)

def piano(t0, m, vel=0.5, pan=0.0, length=5.0):
    f = midi(m); n = int(length * SR); tt = np.arange(n) / SR
    s = np.zeros(n)
    for k, a in enumerate([1, .45, .22, .12, .06, .03], 1):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)                    # slight inharmonicity
        s += a * np.sin(2 * np.pi * fk * tt + rng.random()) * np.exp(-tt * (0.9 + 0.55 * k))
    s *= np.minimum(1, tt / 0.012) * vel                             # soft felt attack
    s += 0.02 * vel * rng.standard_normal(n) * np.exp(-tt * 60)      # hammer felt thump
    s = np.convolve(s, np.ones(6) / 6, 'same')                       # soften highs
    i = int(t0 * SR); j = min(N, i + n)
    L[i:j] += s[:j - i] * (1 - pan) * .5; R[i:j] += s[:j - i] * (1 + pan) * .5

def chime(t0, f, vel=0.25, pan=0.0):
    n = int(4 * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for r, a, d in [(1, 1, 1.2), (2.76, .5, 2.2), (5.40, .25, 3.5), (8.93, .12, 5)]:
        s += a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * d)
    s *= np.minimum(1, tt / 0.003) * vel
    i = int(t0 * SR); j = min(N, i + n)
    L[i:j] += s[:j - i] * (1 - pan) * .5; R[i:j] += s[:j - i] * (1 + pan) * .5

# --- piano: slow progression in D major (Dmaj9 - Bm7 - Gmaj7 - Asus4), sparse arpeggios
prog = [[50, 57, 62, 64, 66, 69], [47, 54, 59, 62, 66, 69], [43, 50, 59, 62, 66, 71], [45, 52, 57, 62, 64, 69]]
bar = 4.8
for b in range(int(DUR / bar) + 1 if WITH_PIANO else 0):
    t0 = b * bar
    if t0 < 3.2 or 31.0 < t0 < 38.4 or t0 > 52: continue           # empty opening, stillness, quiet end
    ch = prog[b % 4]; v = 0.32 if t0 < 18 else 0.4 if t0 < 34 else 0.42
    piano(t0, ch[0] - 12, v * 0.8, -0.2, 6)
    for k, nidx in enumerate([1, 2, 3, 5, 4, 3]):
        piano(t0 + 0.6 + k * 0.62 + rng.uniform(-.03, .03), ch[nidx], v * (0.55 if k else 0.7), 0.3 * np.sin(k), 4)
# last gentle note under the final line, rings out into the loop
if WITH_PIANO: piano(V(50.2), 62, 0.35, 0, 6); piano(V(50.2), 69, 0.25, 0.2, 6); piano(V(52.0), 74, 0.2, -0.2, 3.5)

# --- chimes on story beats
D6 = midi(86)
for tt, f, v in [(1.0, D6, .22), (10.5, midi(81), .16), (12.0, D6, .12), (20.0, midi(88), .14), (23.4, midi(86), .14),
                 (26.8, midi(90), .14), (41.0, midi(81), .1), (42.6, midi(85), .1), (44.2, midi(88), .1), (45.4, midi(86), .1),
                 (46.8, midi(90), .1), (47.8, midi(93), .1), (51.0, D6, .2)]:
    chime(V(tt), f, v, rng.uniform(-.5, .5))

# --- reverb (stereo, decaying noise IR)
def reverb(x, seed):
    ir_n = int(2.8 * SR); it = np.arange(ir_n) / SR
    ir = np.random.default_rng(seed).standard_normal(ir_n) * np.exp(-it * 2.3); ir[0] = 0; ir /= np.abs(ir).sum() / 4
    m = 1 << int(np.ceil(np.log2(len(x) + ir_n)))
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[:len(x)]
L, R = L * .75 + reverb(L, 1) * .45, R * .75 + reverb(R, 2) * .45

# --- wind: filtered noise with slow gusts
def lowpass(x, a):            # one-pole low-pass applied in the frequency domain (numpy only)
    X = np.fft.rfft(x); w = np.linspace(0, np.pi, len(X))
    return np.fft.irfft(X * (1 - a) / (1 - a * np.exp(-1j * w)), len(x))
for ch, sd in ((0, 11), (1, 12)):
    w = np.random.default_rng(sd).standard_normal(N)
    w = lowpass(lowpass(w, 0.985), 0.97)
    w -= lowpass(w, 0.9995)                                           # remove rumble
    g = 0.55 + 0.45 * np.sin(2 * np.pi * t / 13 + sd) * np.sin(2 * np.pi * t / 7.3 + sd * 2)
    w *= g / (np.abs(w).max() + 1e-9) * 0.09
    w *= np.where((t > V(35.2)) & (t < V(38)), 1.6, 1.0)                    # wind alone in the stillness
    (L if ch == 0 else R)[:] += w

# --- loop-friendly edges + normalise
env = np.minimum(1, t / 1.0) * np.minimum(1, (DUR - t) / 1.2)
L *= env; R *= env
pk = max(np.abs(L).max(), np.abs(R).max()); L, R = L / pk * 0.6, R / pk * 0.6
os.makedirs(OUT, exist_ok=True)
with wave.open(os.path.join(OUT, 'soundtrack.wav'), 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((np.stack([L, R], 1) * 32767).astype('<i2').tobytes())
print('soundtrack.wav written')
