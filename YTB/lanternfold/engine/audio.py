"""Audio helpers: decode, silence check, speech spans."""
import re, subprocess, numpy as np
from .config import FFMPEG, SR

def load(path, ch=1, tempo=1.0):
    af = ['-af', f'atempo={tempo}'] if tempo != 1.0 else []
    raw = subprocess.run([FFMPEG, '-v', 'error', '-i', path, *af, '-f', 's16le', '-ac', str(ch), '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def check(path):
    """refuse silent / near-silent audio (rule: never use a silent file)"""
    e = subprocess.run([FFMPEG, '-hide_banner', '-i', path, '-af', 'volumedetect', '-f', 'null', '-'], capture_output=True, text=True).stderr
    mean = float(re.search(r'mean_volume: ([-\d.]+)', e).group(1)); peak = float(re.search(r'max_volume: ([-\d.]+)', e).group(1))
    ok = mean > -60 and peak > -40
    print(f'  audio check {path.split("/")[-1].split(chr(92))[-1]}: mean {mean} dB, peak {peak} dB ->', 'OK' if ok else 'SILENT')
    if not ok: raise SystemExit(f'Aborting: {path} is silent')

def speech_spans(path, noise=-38, d=0.35):
    e = subprocess.run([FFMPEG, '-hide_banner', '-i', path, '-af', f'silencedetect=noise={noise}dB:d={d}', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', e)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', e)]
    dur = len(load(path)) / SR; out, cur = [], 0.0
    for a, b in zip(st, en + [dur]):
        if a - cur > 0.15: out.append((cur, a))
        cur = b
    if dur - cur > 0.15: out.append((cur, dur))
    return out
