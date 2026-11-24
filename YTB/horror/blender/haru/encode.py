"""Frames rendered on twos (f_0001.png, f_0003.png, ...) -> 24 fps mp4 with light film grain, plus a phone-size copy.
uv run --no-project --with imageio-ffmpeg python encode.py FRAME_DIR OUT.mp4 [--step 2]"""
import glob, os, subprocess, sys
import imageio_ffmpeg

src, out = sys.argv[1], sys.argv[2]
step = int(sys.argv[sys.argv.index('--step') + 1]) if '--step' in sys.argv else 2
ff = imageio_ffmpeg.get_ffmpeg_exe()
frames = sorted(glob.glob(os.path.join(src, 'f_*.png')) or glob.glob(os.path.join(src, '[0-9][0-9][0-9][0-9].png')))
# (f_*.png: 24 fps timeline rendered on twos; 0001.png: the claymation skill's 12 fps frames. Both hold 1/12 s each.)
lst = os.path.join(src, 'list.txt')
with open(lst, 'w') as f:
    for p in frames: f.write(f"file '{os.path.basename(p)}'\nduration {step / 24}\n")
    f.write(f"file '{os.path.basename(frames[-1])}'\n")
subprocess.run([ff, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                '-vf', 'fps=24,vignette=angle=PI/5,noise=alls=5:allf=t,format=yuv420p', '-c:v', 'libx264', '-crf', '17', '-preset', 'slow',
                '-movflags', '+faststart', out], check=True)
small = out.replace('.mp4', '_small.mp4')
subprocess.run([ff, '-y', '-loglevel', 'error', '-i', out, '-c:v', 'libx264', '-crf', '24', '-preset', 'slow',
                '-movflags', '+faststart', small], check=True)
print(len(frames), 'poses ->', out, os.path.getsize(out) // 2**20, 'MB;', small, os.path.getsize(small) // 2**10, 'KB')
