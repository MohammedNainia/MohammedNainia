"""Word-level timing: faster-whisper (CPU) listens to build/voice.wav, then our caption words are aligned to what it heard.
Cached in build/words.json. Returns None if faster-whisper or its model is unavailable (captions fall back to estimates)."""
import os, re, json, difflib

def _norm(w): return re.sub(r"[^a-z0-9']", '', w.lower().replace('’', "'"))

def heard(reel):
    cache = os.path.join(reel.build, 'words.json'); voice = os.path.join(reel.build, 'voice.wav')
    if os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(voice):
        return json.load(open(cache))
    try:
        from faster_whisper import WhisperModel
        m = WhisperModel('base.en', device='cpu', compute_type='int8')
        segs, _ = m.transcribe(voice, word_timestamps=True, initial_prompt=' '.join(' '.join(l['chunks']) for l in reel.cfg['lines']))
        ws = [[round(w.start, 3), round(w.end, 3), w.word.strip()] for s in segs for w in s.words]
    except Exception as e:
        print(f'  (word timing unavailable: {str(e)[:80]} - using estimated timing)'); return None
    json.dump(ws, open(cache, 'w')); print(f'  whisper heard {len(ws)} words')
    return ws

def align(words, ws):
    """words: our caption words in order. ws: [[start, end, word]] heard. -> [(start, end)] per caption word"""
    a = [_norm(w) for w in words]; b = [_norm(w[2]) for w in ws]; t = [None] * len(words)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size): t[blk.a + k] = (ws[blk.b + k][0], ws[blk.b + k][1])
    known = [i for i, x in enumerate(t) if x]
    if not known: return None
    for i in range(len(t)):            # words whisper missed: interpolate between matched neighbours
        if t[i]: continue
        p = max((k for k in known if k < i), default=None); n = min((k for k in known if k > i), default=None)
        if p is None: t[i] = (max(0, t[n][0] - .3 * (n - i)), max(0, t[n][0] - .3 * (n - i) + .28))
        elif n is None: t[i] = (t[p][1] + .3 * (i - p - 1), t[p][1] + .3 * (i - p))
        else:
            span = (t[n][0] - t[p][1]) / (n - p); s = t[p][1] + span * (i - p - 1); t[i] = (s, s + span)
    return t
