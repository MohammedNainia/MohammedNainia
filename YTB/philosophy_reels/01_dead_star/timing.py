"""Builds build/voice.wav from voice/line1-7.mp3 (long [pause] gaps trimmed to 0.75 s),
places each line on the timeline, and writes timing.json with:
  - lines: [start, end] of each line in video time
  - knots: piecewise-linear map video time -> story time (scene.py works in story time, 0-55)"""
import json, os, re, subprocess, wave, numpy as np
from config import FFMPEG, OUT, HERE
SR = 44100
MAXGAP = 0.75
# where each line starts relative to its story beat (story seconds the line belongs to)
STORY_BEAT = [0.0, 4.0, 10.0, 18.0, 28.0, 38.0, 50.0]
LEAD = [0.8, 0.5, 0.5, 0.6, 1.2, 0.5, 0.4]      # seconds of picture before each line starts
STILL_AFTER_5 = 2.2                               # stillness after "her light went out"
TAIL = 1.6                                        # end hold before the loop point

def load(path):
    raw = subprocess.run([FFMPEG, '-v', 'error', '-i', path, '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def squeeze_pauses(x):
    win = int(0.02 * SR); n = len(x) // win
    rms = np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1)); quiet = rms < 10 ** (-40 / 20)
    keep = np.ones(n, bool); i = 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]: j += 1
            if i > 0 and j < n and (j - i) * 0.02 > MAXGAP:      # interior gap only
                cut = (j - i) - int(MAXGAP / 0.02); a = i + int(MAXGAP / 0.02 / 2)
                keep[a:a + cut] = False
            i = j
        else: i += 1
    y = x[:n * win].reshape(n, win)[keep].ravel()
    # trim leading/trailing silence to 50 ms
    nz = np.where(np.abs(y) > 10 ** (-45 / 20))[0]
    return y[max(0, nz[0] - int(.05 * SR)): nz[-1] + int(.12 * SR)]

def main():
    clips = [squeeze_pauses(load(os.path.join(HERE, 'voice', f'line{i}.mp3'))) for i in range(1, 8)]
    t = 0.0; lines = []; knots = [(0.0, 0.0)]
    for k, c in enumerate(clips):
        if k == 0: start = LEAD[0]
        else:
            gap = LEAD[k] + (STILL_AFTER_5 if k == 5 else 0.35)
            start = lines[-1][1] + gap
            knots.append((start - LEAD[k], STORY_BEAT[k]))
        lines.append((start, start + len(c) / SR))
    dur = round(lines[-1][1] + TAIL, 2)
    knots.append((dur, 55.0))
    v = np.zeros(int(dur * SR) + SR, np.float32)
    for (a, _), c in zip(lines, clips):
        i = int(a * SR); v[i:i + len(c)] += c
    os.makedirs(OUT, exist_ok=True)
    with wave.open(os.path.join(OUT, 'voice.wav'), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(v[:int(dur * SR)], -1, 1) * 32767).astype('<i2').tobytes())
    json.dump({'duration': dur, 'lines': lines, 'knots': knots}, open(os.path.join(HERE, 'timing.json'), 'w'), indent=1)
    print('duration', dur); [print(f'line{i+1}: {a:6.2f} - {b:6.2f}') for i, (a, b) in enumerate(lines)]; print('knots', knots)

if __name__ == '__main__':
    main()
