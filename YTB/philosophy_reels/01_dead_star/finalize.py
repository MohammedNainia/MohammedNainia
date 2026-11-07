"""Captions + audio mix + exports.
python finalize.py   (needs build/master_clean.mp4, build/voice.wav from timing.py, build/soundtrack.wav, music_score.mp3)"""
import os, re, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import FFMPEG, FPS, OUT, VOICE, FONT, HERE
import json
TM = json.load(open(os.path.join(HERE, "timing.json")))
W, H, DUR = 1080, 1920, TM["duration"]
KV, KS = zip(*TM["knots"])
def V(story): return float(np.interp(story, KS, KV))
CHUNKS = [["This star died", "four thousand years ago."],
          ["But she can", "still see it.", "Its light is", "still travelling…", "still arriving."],
          ["Everything you see", "in the sky", "is a goodbye", "that hasn't finished", "being said."],
          ["She didn't know it…", "but she was doing", "the same thing.", "Every kindness", "left her like light.", "Slowly.", "Quietly."],
          ["One night,", "her light went out."],
          ["But it didn't", "stop arriving.", "It's still reaching", "people she never met."],
          ["So maybe the question", "isn't how long", "you shine…", "but how far", "your light travels after."]]
LINES = [' '.join(c) for c in CHUNKS]
MAP = [(0.6, 3.6), (4.3, 9.6), (10.5, 17.2), (18.5, 27.6), (30.5, 33.5), (38.5, 48.5), (50.0, 54.6)]

def ff(*a, **k): return subprocess.run([FFMPEG, '-hide_banner', '-y', *a], capture_output=True, text=True, **k)

def check_audio(path):
    """refuse silent / near-silent files"""
    e = ff('-i', path, '-af', 'volumedetect', '-f', 'null', '-').stderr
    mean = float(re.search(r'mean_volume: ([-\d.]+)', e).group(1)); peak = float(re.search(r'max_volume: ([-\d.]+)', e).group(1))
    ok = mean > -60 and peak > -40
    print(f'{os.path.basename(path)}: mean {mean} dB, peak {peak} dB ->', 'OK' if ok else 'SILENT')
    if not ok: sys.exit(f'Aborting: {path} is silent')

def duration(path):
    e = ff('-i', path, '-f', 'null', '-').stderr
    h, m, s = re.findall(r'time=(\d+):(\d+):([\d.]+)', e)[-1]; return int(h) * 3600 + int(m) * 60 + float(s)

def speech_intervals(path, off):
    e = ff('-i', path, '-af', 'silencedetect=noise=-38dB:d=0.35', '-f', 'null', '-').stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', e)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', e)]
    d = duration(path); iv, cur = [], 0.0
    for a, b in zip(st, en + [d]):
        if a - cur > 0.15: iv.append((cur + off, a + off))
        cur = b
    if d - cur > 0.15: iv.append((cur + off, d + off))
    return iv

def chunks(line):
    w = line.split(); n = len(w); out, i = [], 0
    while i < n:
        k = 4 if n - i >= 7 or n - i == 4 else 3 if n - i >= 3 else n - i
        if n - i - k in (1, 2) and k == 4: k = 3 if n - i - 3 >= 3 else 4   # avoid 1-2 word leftovers
        out.append(' '.join(w[i:i + k])); i += k
    return out

def word_times(intervals):
    """spread all words over the speech time, weighted by length"""
    words = [w for l in LINES for w in l.split()]
    wt = np.array([len(w) + 2 for w in words], float); wt /= wt.sum()
    total = sum(b - a for a, b in intervals); edges = np.concatenate([[0], np.cumsum(wt)]) * total
    def at(x):
        for a, b in intervals:
            if x <= b - a + 1e-9: return a + x
            x -= b - a
        return intervals[-1][1]
    return [(at(edges[i]), at(edges[i + 1])) for i in range(len(words))]

def spread(words, intervals):
    """word (start,end) spread over the given speech spans, weighted by word length"""
    wt = np.array([len(w) + 2 for w in words], float); wt /= wt.sum()
    total = sum(b - a for a, b in intervals); edges = np.concatenate([[0], np.cumsum(wt)]) * total
    def at(x):
        for a, b in intervals:
            if x <= b - a + 1e-9: return a + x
            x -= b - a
        return intervals[-1][1]
    return [(at(edges[i]), at(edges[i + 1])) for i in range(len(words))]

def caption_track(intervals):
    cues = []
    for chunks, (la, lb) in zip(CHUNKS, TM['lines']):
        iv = [(max(a, la), min(b, lb)) for a, b in intervals if b > la and a < lb] or [(la, lb)]
        words = ' '.join(chunks).split(); wt = spread(words, iv); i = 0
        for c in chunks:
            n = len(c.split()); cues.append([wt[i][0], wt[i + n - 1][1], c]); i += n
    for a, b in zip(cues, cues[1:]):
        a[1] = b[0] - 0.05 if b[0] - a[1] < 0.7 else a[1] + 0.35
    cues[-1][1] = min(DUR - 0.4, cues[-1][1] + 0.6)
    return cues

FONT_SIZE = 70
def cue_image(text):
    f = ImageFont.truetype(FONT, FONT_SIZE) if FONT else ImageFont.load_default()
    im = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    tw = d.textlength(text, font=f); x, y = (W - tw) / 2, 110
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((x, y + 3), text, font=f, fill=(5, 8, 25, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    im = Image.alpha_composite(sh, im); ImageDraw.Draw(im).text((x, y), text, font=f, fill=(255, 244, 224, 255))
    return np.asarray(im)

def main():
    amb = os.path.join(OUT, 'soundtrack.wav'); master = os.path.join(OUT, 'master_clean.mp4')
    voice = os.path.join(OUT, 'voice.wav'); score = os.path.join(HERE, 'music_score.mp3')
    for f in (voice, score, amb): check_audio(f)
    iv = speech_intervals(voice, 0.0); print('speech spans', len(iv))
    cues = caption_track(iv)
    with open(os.path.join(HERE, 'captions.srt'), 'w', encoding='utf-8') as f:
        ts = lambda s: f'{int(s // 3600):02}:{int(s % 3600 // 60):02}:{int(s % 60):02},{int(s % 1 * 1000):03}'
        for n, (a, b, c) in enumerate(cues, 1): f.write(f'{n}\n{ts(a)} --> {ts(b)}\n{c}\n\n')
    imgs = {c: cue_image(c) for _, _, c in cues}
    final = os.path.join(HERE, 'dead_star_1080x1920.mp4')
    ins = ['-i', master, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', voice, '-i', score, '-i', amb]
    s0, s1 = V(35.4), V(38.0)       # 2 s stillness after the lantern goes out: score dips away
    env = (f"volume='0.5*(1-0.9*between(t,{s0:.2f},{s1:.2f}))*min(1,t/1.5)*min(1,({DUR}-t)/2.0)':eval=frame")
    af = (f'[2:a]aresample=44100,aformat=channel_layouts=stereo,apad,asplit[vk][vo];'
          f'[3:a]aresample=44100,{env}[sc];[4:a]volume=0.6[am];[sc][am]amix=inputs=2:normalize=0[bed];'
          f'[bed][vk]sidechaincompress=threshold=0.05:ratio=4:attack=40:release=600[md];'
          f'[md][vo]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]')
    cmd = [FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', *ins, '-filter_complex',
           f'[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];{af}', '-map', '[v]', '-map', '[a]',
           '-t', str(DUR), '-r', str(FPS), '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-profile:v', 'high',
           '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-movflags', '+faststart', final]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    blank = np.zeros((H, W, 4), np.uint8).tobytes(); top = 420   # caption band (top third)
    for fi in range(int(DUR * FPS)):
        t = fi / FPS; a = 0.0; cur = None
        for s, e, c in cues:
            if s - 0.15 <= t <= e + 0.15:
                a = min(1, (t - s + 0.15) / 0.3, (e + 0.15 - t) / 0.3); cur = c; break
        if cur is None or a <= 0: p.stdin.write(blank); continue
        fr = np.zeros((H, W, 4), np.uint8); im = imgs[cur].copy(); im[..., 3] = (im[..., 3] * a).astype(np.uint8)
        fr[top:top + 300] = im; p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    prev = final.replace('1080x1920', '720p_preview')
    subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', final, '-vf', 'scale=720:1280:flags=lanczos',
                    '-c:v', 'libx264', '-preset', 'slow', '-b:v', '2800k', '-maxrate', '3500k', '-bufsize', '6000k',
                    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', prev], check=True)
    for f in (final, prev): print(os.path.basename(f), round(os.path.getsize(f) / 1e6, 1), 'MB')
    check_audio(final)

if __name__ == '__main__':
    main()
