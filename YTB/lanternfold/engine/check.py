"""Pre-upload check: everything we've had to fix by hand, tested automatically.
  python make.py reels/<reel> check   -> PASS / WARN / FAIL list (exit code 1 on any FAIL)"""
import os, re, sys, json, subprocess, numpy as np
from PIL import ImageFont, ImageDraw, Image
from .config import FFMPEG, FFPROBE, FONT, FPS
from . import safezone
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'research'))

class R:
    def __init__(s): s.rows = []
    def ok(s, m): s.rows.append(('PASS', m))
    def warn(s, m): s.rows.append(('WARN', m))
    def fail(s, m): s.rows.append(('FAIL', m))
    def test(s, cond, good, bad, level='warn'): (s.ok(good) if cond else getattr(s, level)(bad))

def probe(p):
    out = subprocess.run([FFPROBE, '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate:format=duration', '-of', 'json', p],
                         capture_output=True, text=True).stdout
    return json.loads(out)

def frame_at(p, sec, w=270, h=480):
    raw = subprocess.run([FFMPEG, '-v', 'error', '-ss', str(sec), '-i', p, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{w}x{h}', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w).astype(np.float32)

def loudness(p):
    e = subprocess.run([FFMPEG, '-hide_banner', '-i', p, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = re.findall(r'I:\s+([-\d.]+) LUFS', e); pk = re.findall(r'Peak:\s+([-\d.]+) dBFS', e)
    return (float(I[-1]) if I else None), (float(pk[-1]) if pk else None)

def seo_title(reel):
    p = reel.path('seo.md')
    if not os.path.exists(p): return None
    m = re.search(r'\*\*Title:\*\*\s*(.+)', open(p, encoding='utf-8').read()); return m.group(1).strip() if m else None

def run(reel):
    r = R(); cfg = reel.cfg; final = reel.path(f'{reel.slug}_1080x1920.mp4'); prev = final.replace('1080x1920', '720p_preview')
    if not os.path.exists(final): r.fail('no final video - run finalize'); return report(r)
    info = probe(final); v = next(s for s in info['streams'] if s['codec_type'] == 'video'); dur = float(info['format']['duration'])
    r.test((v['width'], v['height']) == (1080, 1920), '1080x1920', f"size is {v['width']}x{v['height']}", 'fail')
    r.test(abs(eval(v['r_frame_rate']) - FPS) < .01, f'{FPS} fps', f"frame rate {v['r_frame_rate']}", 'fail')
    r.test(dur <= 60, f'{dur:.1f}s (Shorts limit 60s)', f'{dur:.1f}s is over 60s - not a Short', 'fail')
    r.test(any(s['codec_type'] == 'audio' for s in info['streams']), 'has audio', 'no audio track', 'fail')
    if os.path.exists(prev): r.test(os.path.getsize(prev) < 30e6, f'preview {os.path.getsize(prev) / 1e6:.1f} MB', 'preview over 30 MB')
    # hook: frame 0 must be a real picture, and something must move in the first second
    f0, f5, f10 = (frame_at(final, s) for s in (0.0, 0.5, 1.0))
    r.test(f0.mean() > 22, f'frame 0 is a real shot (brightness {f0.mean():.0f})', f'frame 0 is nearly black ({f0.mean():.0f}) - no black intros', 'fail')
    motion = max(np.abs(f5 - f0).mean(), np.abs(f10 - f0).mean())
    r.test(motion > 1.0, f'movement in first second ({motion:.1f})', f'first second is almost still ({motion:.1f}) - viewers swipe; move the camera from frame 1')
    r.test(bool(cfg.get('hook')), 'hook question on frame 1', 'no "hook" in reel.json - put the big question on screen at frame 1')
    # loop: the last frame should resemble the first
    fe = frame_at(final, max(0, dur - 0.1)); sim = np.abs(fe - f0).mean()
    r.test(sim < 25, f'ending matches opening (loop diff {sim:.0f})', f'last frame differs from first ({sim:.0f}) - weaker loop')
    # audio
    I, pk = loudness(final)
    if I is not None: r.test(-15.5 <= I <= -12.5, f'loudness {I:.1f} LUFS', f'loudness {I:.1f} LUFS (aim -14)')
    if pk is not None: r.test(pk <= -0.5, f'true peak {pk:.1f} dBFS', f'true peak {pk:.1f} dBFS - may clip')
    voice = os.path.join(reel.build, 'voice.wav')
    if os.path.exists(voice):
        from .audio import speech_spans
        words = sum(len(' '.join(l['chunks']).split()) for l in cfg['lines']); talk = sum(b - a for a, b in speech_spans(voice))
        wps = words / max(talk, 1e-3)
        r.test(wps <= 3.0, f'narration pace {wps:.1f} words/s', f'narration is fast ({wps:.1f} words/s) - viewers need time to think; slow it or cut words')
    r.test(cfg.get('music_volume', .32) <= .35, f"music volume {cfg.get('music_volume', .32)}", 'music volume over 0.35 - piano will cover the voice')
    # captions: width and placement against every app's buttons
    f = ImageFont.truetype(FONT, 70); d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    chunks = [c for l in cfg['lines'] for c in l['chunks']]; widest = max(chunks, key=lambda c: d.textlength(c, font=f)); w = d.textlength(widest, font=f)
    r.test(w <= 860, f'captions fit ({int(w)}px widest)', f'caption "{widest}" is {int(w)}px wide - split it (max ~860)')
    r.test(all(len(c.split()) <= 4 for c in chunks), 'captions 4 words or fewer', 'some captions over 4 words: ' + ', '.join(f'"{c}"' for c in chunks if len(c.split()) > 4)[:120])
    cap_box = ((1080 - w) / 2, 420 + 110, (1080 + w) / 2, 420 + 110 + 80)
    hits = safezone.blocked(cap_box); r.test(not hits, 'captions clear of app buttons', 'captions under ' + '; '.join(hits))
    if cfg.get('hook'):
        f2 = ImageFont.truetype(FONT, 130); hw = max(d.textlength(t, font=f2) for t in cfg['hook']['text'])
        hb = ((1080 - hw) / 2, 260, (1080 + hw) / 2, 260 + 150 * len(cfg['hook']['text']))
        hits = safezone.blocked(hb); r.test(not hits, 'hook text clear of app UI', 'hook text under ' + '; '.join(hits))
    # long dash: reads as AI-written (channel rule) - check every text we publish
    texts = [reel.path(f) for f in ('seo.md', 'narration.txt', 'captions.srt') if os.path.exists(reel.path(f))]
    bad = [os.path.basename(f) for f in texts if '—' in open(f, encoding='utf-8').read()]
    bad += ['reel.json captions/hook'] if '—' in json.dumps(cfg, ensure_ascii=False) else []
    r.test(not bad, 'no long dash "—" anywhere', 'long dash "—" found in: ' + ', '.join(bad) + ' (channel rule: never use it)', 'fail')
    # cover + title
    r.test(os.path.exists(reel.path('thumbnail_1080x1920.jpg')), 'cover image ready', 'no cover - run: python make.py <reel> thumb')
    t = seo_title(reel)
    if not t: r.warn('no seo.md title found')
    else:
        try:      # data-trained model (research/study.py report) - percentile vs 1,200+ niche Shorts
            from study import score_pct; pct, rho = score_pct(t)
            r.test(pct >= 60, f'title beats {pct:.0f}% of niche Shorts (data model)', f'title only beats {pct:.0f}% of niche Shorts - run: python ../research/study.py score "<title>" for what helps/hurts')
        except Exception: pass
        r.test(len(t) <= 100, f'title {len(t)} chars', f'title is {len(t)} chars - YouTube cuts at 100', 'fail')
        r.test(t.count('#') <= 3, 'hashtags in title ≤ 3', 'more than 3 hashtags in the title')
        r.test(not re.search(r'\b(paradox|explained|in \d+ seconds|theory)\b', t, re.I), 'no textbook words', 'textbook words in title (paradox / explained / in N seconds / theory) - proven 0.46x in the niche data')
    return report(r)

def report(r):
    for lvl, m in r.rows: print(f"  {'✔' if lvl == 'PASS' else '!' if lvl == 'WARN' else '✘'} {lvl}  {m}")
    n = {k: sum(1 for l, _ in r.rows if l == k) for k in ('PASS', 'WARN', 'FAIL')}
    print(f"  -> {n['PASS']} pass, {n['WARN']} warn, {n['FAIL']} fail" + ('  READY TO UPLOAD' if not n['FAIL'] else '  FIX BEFORE UPLOAD'))
    return not n['FAIL']
