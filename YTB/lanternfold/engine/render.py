"""Parallel, resumable master render (no captions/audio) -> build/master_clean.mp4"""
import os, sys, subprocess, numpy as np
from concurrent.futures import ProcessPoolExecutor
from .config import FFMPEG, FFPROBE, FPS
from .reel import Reel

def frames_in(path):
    r = subprocess.run([FFPROBE, '-v', 'error', '-count_packets', '-select_streams', 'v', '-show_entries',
                        'stream=nb_read_packets', '-of', 'csv=p=0', path], capture_output=True, text=True)
    try: return int(r.stdout.strip())
    except ValueError: return -1

_scene = {}
def work(args):
    d, i, a, b = args
    reel = Reel(d); path = os.path.join(reel.build, f'_seg{i:02}.mp4')
    if os.path.exists(path) and frames_in(path) == b - a: return path
    sc = _scene.get(d) or _scene.setdefault(d, reel.scene())
    p = subprocess.Popen([FFMPEG, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '12', '-pix_fmt', 'yuv420p', path],
                         stdin=subprocess.PIPE)
    for f in range(a, b): p.stdin.write(sc.frame(reel.story(f / FPS)).tobytes())
    p.stdin.close(); p.wait(); return path

def run(reel, workers=None):
    k = workers or max(1, (os.cpu_count() or 2) - 0)
    N = int(round(reel.timing['duration'] * FPS)); cuts = np.linspace(0, N, k * 3 + 1).astype(int)
    jobs = [(reel.dir, i, int(cuts[i]), int(cuts[i + 1])) for i in range(len(cuts) - 1)]
    with ProcessPoolExecutor(k) as ex: segs = list(ex.map(work, jobs))
    bad = [s for (_, _, a, b), s in zip(jobs, segs) if frames_in(s) != b - a]
    if bad: raise SystemExit(f'incomplete segments: {bad} (re-run to resume)')
    lst = os.path.join(reel.build, '_list.txt')
    with open(lst, 'w') as f: f.writelines(f"file '{s}'\n" for s in segs)
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                    os.path.join(reel.build, 'master_clean.mp4')], check=True)
    for s in segs: os.remove(s)
    os.remove(lst); print(f'  master_clean.mp4: {N} frames')
