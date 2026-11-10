"""Captions (3-4 words, top third) + mix (voice, music, ambience) + exports (1080x1920 master, 720p preview <30 MB)."""
import os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .config import FFMPEG, FPS, FONT
from .audio import check, speech_spans, load
from .config import SR
from . import words as WORDS
W, H = 1080, 1920

def spread(words, spans):
    wt = np.array([len(w) + 2 for w in words], float); wt /= wt.sum()
    total = sum(b - a for a, b in spans); edges = np.concatenate([[0], np.cumsum(wt)]) * total
    def at(x):
        for a, b in spans:
            if x <= b - a + 1e-9: return a + x
            x -= b - a
        return spans[-1][1]
    return [(at(edges[i]), at(edges[i + 1])) for i in range(len(words))]

def cues(reel, spans):
    """[start, end, chunk, [(word_start, word_end), ...]] - word times from whisper when available, else estimated"""
    out, dur = [], reel.timing['duration']
    allw = [w for ln in reel.cfg['lines'] for ch in ln['chunks'] for w in ch.split()]
    ws = WORDS.heard(reel); wt_all = WORDS.align(allw, ws) if ws else None; gi = 0
    for ln, (la, lb) in zip(reel.cfg['lines'], reel.timing['lines']):
        words = ' '.join(ln['chunks']).split()
        if wt_all: wt = wt_all[gi:gi + len(words)]
        else:
            iv = [(max(a, la), min(b, lb)) for a, b in spans if b > la and a < lb] or [(la, lb)]; wt = spread(words, iv)
        gi += len(words); i = 0
        for ch in ln['chunks']:
            n = len(ch.split()); out.append([wt[i][0], wt[i + n - 1][1], ch, wt[i:i + n]]); i += n
    for a, b in zip(out, out[1:]): a[1] = b[0] - 0.05 if b[0] - a[1] < 0.7 else a[1] + 0.35
    out[-1][1] = min(dur - 0.4, out[-1][1] + 0.6)
    print(f"  captions: {'whisper word timing' if wt_all else 'estimated timing'}, {len(out)} cues")
    return out

HI = (255, 200, 95, 255)        # karaoke highlight (PaperLit gold)

def cue_img(text, size=70, hi=-1):
    """caption strip; word number `hi` drawn in gold (karaoke) when >= 0"""
    f = ImageFont.truetype(FONT, size); im = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = (W - d.textlength(text, font=f)) / 2; y = 110
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((x, y + 3), text, font=f, fill=(5, 8, 25, 235), stroke_width=6, stroke_fill=(5, 8, 25, 235))
    im = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)), im); d = ImageDraw.Draw(im); sp = d.textlength(' ', font=f)
    for i, w in enumerate(text.split()):
        d.text((x, y), w, font=f, fill=HI if i == hi else (255, 244, 224, 255), stroke_width=2, stroke_fill=(30, 26, 40, 255))
        x += d.textlength(w, font=f) + sp
    return np.asarray(im)

def hook_img(lines, size=130):
    """big hook question shown on frame 1 (and again at the loop point)"""
    f = ImageFont.truetype(FONT, size); h = int(size * 1.15 * len(lines) + 80); im = Image.new('RGBA', (W, h), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); d0 = ImageDraw.Draw(sh); d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        x = (W - d.textlength(ln, font=f)) / 2; y = 30 + i * size * 1.15
        d0.text((x, y + 6), ln, font=f, fill=(5, 8, 25, 230), stroke_width=12, stroke_fill=(5, 8, 25, 230))
        d.text((x, y), ln, font=f, fill=(255, 238, 208, 255), stroke_width=3, stroke_fill=(35, 28, 45, 255))
    return np.asarray(Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), im))

def srt(cs, path):
    ts = lambda s: f'{int(s // 3600):02}:{int(s % 3600 // 60):02}:{int(s % 60):02},{int(s % 1 * 1000):03}'
    with open(path, 'w', encoding='utf-8') as f:
        for n, (a, b, c, *_) in enumerate(cs, 1): f.write(f'{n}\n{ts(a)} --> {ts(b)}\n{c}\n\n')

def run(reel):
    voice, amb, master = (os.path.join(reel.build, x) for x in ('voice.wav', 'ambience.wav', 'master_clean.mp4'))
    music = next((reel.path(f) for f in os.listdir(reel.dir) if f.startswith('music.')), None)
    if not music: raise SystemExit('put the score in the reel folder as music.mp3/.wav')
    for p in (voice, music, amb): check(p)
    dur = reel.timing['duration']; cs = cues(reel, speech_spans(voice)); srt(cs, reel.path('captions.srt'))
    karaoke = reel.cfg.get('captions', 'karaoke') == 'karaoke'; imgs = {}
    def img(c, k):
        if (c, k) not in imgs: imgs[(c, k)] = cue_img(c, hi=k if karaoke else -1)
        return imgs[(c, k)]
    dips = ''.join(f'*(1-0.9*between(t,{reel.video(a):.2f},{reel.video(b):.2f}))' for a, b in reel.cfg.get('stillness', []))
    mv = reel.cfg.get('music_volume', 0.32)
    env = f"volume='{mv}{dips}*min(1,t/1.5)*min(1,({dur}-t)/2.0)':eval=frame"
    from .sfx import run as sfx_run; sfx = sfx_run(reel) if reel.cfg.get('sfx') else None
    af = (f'[2:a]aresample=44100,aformat=channel_layouts=stereo,apad,asplit[vk][vo];'
          f'[3:a]aresample=44100,{env}[sc];[4:a]volume=0.6[am];[sc][am]amix=inputs=2:normalize=0[bed];'
          f'[bed][vk]sidechaincompress=threshold=0.05:ratio=4:attack=40:release=600[md];'
          + (f'[5:a]aresample=44100,aformat=channel_layouts=stereo[fx];[md][fx]amix=inputs=2:normalize=0[mf];' if sfx else '[md]anull[mf];')
          + f'[mf][vo]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]')
    final = reel.path(f'{reel.slug}_1080x1920.mp4')
    p = subprocess.Popen([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', master, '-f', 'rawvideo', '-pix_fmt', 'rgba',
                          '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', voice, '-i', music, '-i', amb, *(['-i', sfx] if sfx else []), '-filter_complex',
                          f'[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];{af}', '-map', '[v]', '-map', '[a]', '-t', str(dur),
                          '-r', str(FPS), '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-profile:v', 'high', '-c:a', 'aac',
                          '-b:a', '192k', '-ar', '44100', '-movflags', '+faststart', final], stdin=subprocess.PIPE)
    blank = bytes(H * W * 4); top = 420
    hk = reel.cfg.get('hook'); himg = hook_img(hk['text']) if hk else None
    for fi in range(int(dur * FPS)):
        t = fi / FPS; a, cur, wi = 0.0, None, -1; top = 420
        for s, e, c, wt in cs:
            if s - 0.15 <= t <= e + 0.15:
                a = min(1, (t - s + 0.15) / 0.3, (e + 0.15 - t) / 0.3); cur = c
                wi = max([k for k, (ws_, _) in enumerate(wt) if ws_ - 0.05 <= t] or [0]); break
        ha = 0.0
        if hk:   # hook: full at frame 1, fades out after `hold`, fades back in over the last `end` s (seamless loop)
            ha = max(1 - max(0, t - hk.get('hold', 2.2)) / hk.get('fade', .6), (t - (dur - hk.get('end', 1.2))) / hk.get('end', 1.2), 0)
            ha = min(1, ha)
            if t < dur / 2: top = int(420 + 150 * ha)   # opening: captions stay visible, just below the hook, then slide up
            else: a = a * (1 - ha)                      # loop point: the closing question is the hook itself
        if (cur is None or a <= 0) and ha <= 0: p.stdin.write(blank); continue
        fr = np.zeros((H, W, 4), np.uint8)
        if cur is not None and a > 0:
            im = img(cur, wi).copy(); im[..., 3] = (im[..., 3] * a).astype(np.uint8); fr[top:top + 300] = im
        if ha > 0:
            hi = himg.copy(); hi[..., 3] = (hi[..., 3] * ha).astype(np.uint8); y0 = 230; hh = hi.shape[0]
            base = fr[y0:y0 + hh].astype(np.float32); al = hi[..., 3:4].astype(np.float32) / 255
            fr[y0:y0 + hh] = (hi.astype(np.float32) * al + base * (1 - al)).clip(0, 255).astype(np.uint8)
            fr[y0:y0 + hh, :, 3] = np.maximum(fr[y0:y0 + hh, :, 3], hi[..., 3])
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    prev = final.replace('1080x1920', '720p_preview')
    subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', final, '-vf', 'scale=720:1280:flags=lanczos',
                    '-c:v', 'libx264', '-preset', 'slow', '-b:v', '2800k', '-maxrate', '3500k', '-bufsize', '6000k',
                    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', prev], check=True)
    for f in (final, prev): print(f'  {os.path.basename(f)}: {os.path.getsize(f) / 1e6:.1f} MB')
    check(final)
