"""Code-made bed: soft wind + glassy chimes on story beats -> build/ambience.wav"""
import os, wave, numpy as np
from .config import SR

def midi(m): return 440 * 2 ** ((m - 69) / 12)

def lowpass(x, a):
    X = np.fft.rfft(x); w = np.linspace(0, np.pi, len(X))
    return np.fft.irfft(X * (1 - a) / (1 - a * np.exp(-1j * w)), len(x))

def reverb(x, seed, sec=2.8):
    n = int(sec * SR); it = np.arange(n) / SR
    ir = np.random.default_rng(seed).standard_normal(n) * np.exp(-it * 2.3); ir[0] = 0; ir /= np.abs(ir).sum() / 4
    m = 1 << int(np.ceil(np.log2(len(x) + n)))
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[:len(x)]

def run(reel):
    c = reel.cfg; dur = reel.timing['duration']; N = int(dur * SR); t = np.arange(N) / SR
    L = np.zeros(N); R = np.zeros(N); rng = np.random.default_rng(3)
    for st, note, vel in c.get('chimes', []):
        t0 = reel.video(st); n = int(4 * SR); tt = np.arange(n) / SR; s = np.zeros(n); f = midi(note)
        for r, a, d in [(1, 1, 1.2), (2.76, .5, 2.2), (5.40, .25, 3.5), (8.93, .12, 5)]:
            s += a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * d)
        s *= np.minimum(1, tt / 0.003) * vel; pan = rng.uniform(-.5, .5)
        i = int(t0 * SR); j = min(N, i + n); L[i:j] += s[:j - i] * (1 - pan) * .5; R[i:j] += s[:j - i] * (1 + pan) * .5
    L, R = L * .75 + reverb(L, 1) * .45, R * .75 + reverb(R, 2) * .45
    still = [(reel.video(a), reel.video(b)) for a, b in c.get('stillness', [])]
    for ch, sd in ((0, 11), (1, 12)):
        w = np.random.default_rng(sd).standard_normal(N)
        w = lowpass(lowpass(w, 0.985), 0.97); w -= lowpass(w, 0.9995)
        g = 0.55 + 0.45 * np.sin(2 * np.pi * t / 13 + sd) * np.sin(2 * np.pi * t / 7.3 + sd * 2)
        w *= g / (np.abs(w).max() + 1e-9) * c.get('wind', 0.09)
        for a, b in still: w *= np.where((t > a) & (t < b), 1.6, 1.0)
        (L if ch == 0 else R)[:] += w
    env = np.minimum(1, t / 1.0) * np.minimum(1, (dur - t) / 1.2); L *= env; R *= env
    pk = max(np.abs(L).max(), np.abs(R).max(), 1e-9); L, R = L / pk * 0.6, R / pk * 0.6
    with wave.open(os.path.join(reel.build, 'ambience.wav'), 'wb') as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.stack([L, R], 1) * 32767).astype('<i2').tobytes())
    print('  ambience.wav written')
