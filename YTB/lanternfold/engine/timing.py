"""voice/line1..N.mp3 -> build/voice.wav + timing.json (line placement + video->story time map)."""
import os, json, wave, numpy as np
from .config import SR
from .audio import load, check

def squeeze(x, maxgap):
    win = int(0.02 * SR); n = len(x) // win
    rms = np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1)); quiet = rms < 10 ** (-40 / 20)
    keep = np.ones(n, bool); i = 0; g = int(maxgap / 0.02)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]: j += 1
            if i > 0 and j < n and (j - i) > g: keep[i + g // 2: i + g // 2 + (j - i) - g] = False
            i = j
        else: i += 1
    y = x[:n * win].reshape(n, win)[keep].ravel()
    nz = np.where(np.abs(y) > 10 ** (-45 / 20))[0]
    return y[max(0, nz[0] - int(.05 * SR)): nz[-1] + int(.12 * SR)]

def run(reel):
    c = reel.cfg; lines = c['lines']; clips = []
    for i in range(len(lines)):
        p = reel.path('voice', f'line{i + 1}.mp3'); check(p); clips.append(squeeze(load(p), c.get('max_pause', 0.75)))
    placed, knots = [], [(0.0, 0.0)]
    for k, (ln, clip) in enumerate(zip(lines, clips)):
        lead = ln.get('lead', 0.5)
        if k == 0: start = lead
        else:
            start = placed[-1][1] + lines[k - 1].get('hold_after', 0.35) + lead
            knots.append((start - lead, ln['beat']))
        placed.append((start, start + len(clip) / SR))
    dur = round(placed[-1][1] + c.get('tail', 1.6), 2)
    if dur > 60: print(f'  WARNING: {dur}s is over 60 s; shorten hold_after/max_pause or lines')
    knots.append((dur, c['story_duration']))
    v = np.zeros(int(dur * SR) + SR, np.float32)
    for (a, _), clip in zip(placed, clips): i = int(a * SR); v[i:i + len(clip)] += clip
    with wave.open(os.path.join(reel.build, 'voice.wav'), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(v[:int(dur * SR)], -1, 1) * 32767).astype('<i2').tobytes())
    json.dump({'duration': dur, 'lines': placed, 'knots': knots}, open(reel.timing_path, 'w'), indent=1)
    print(f'  duration {dur}s'); [print(f'  line{i+1}: {a:6.2f} - {b:6.2f}') for i, (a, b) in enumerate(placed)]
