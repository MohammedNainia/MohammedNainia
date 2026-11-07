"""Render the clean master (no captions, no audio) in parallel chunks.
usage: python render.py [workers]"""
import os, sys, subprocess, numpy as np
from multiprocessing import Pool
import scene, json
TM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'timing.json')))
KV, KS = zip(*TM['knots'])
def story(v): return float(np.interp(v, KV, KS))
from config import FFMPEG, FPS, OUT

N = int(round(TM['duration'] * FPS))

def work(args):
    i, a, b = args
    path = f'{OUT}/_seg{i}.mp4'
    p = subprocess.Popen([FFMPEG, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{scene.W}x{scene.H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'slow', '-crf', '12', '-pix_fmt', 'yuv420p', path],
                         stdin=subprocess.PIPE)
    for f in range(a, b):
        p.stdin.write(scene.frame(story(f / FPS)).tobytes())
    p.stdin.close(); p.wait()
    return path

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    k = int(sys.argv[1]) if len(sys.argv) > 1 else os.cpu_count()
    cuts = np.linspace(0, N, k * 3 + 1).astype(int)
    jobs = [(i, cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]
    with Pool(k) as pool:
        segs = pool.map(work, jobs)
    with open(f'{OUT}/_list.txt', 'w') as f:
        f.writelines(f"file '{os.path.abspath(s)}'\n" for s in segs)
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/_list.txt',
                    '-c', 'copy', f'{OUT}/master_clean.mp4'], check=True)
    for s in segs: os.remove(s)
    os.remove(f'{OUT}/_list.txt')
    print('master_clean.mp4 done,', N, 'frames')
