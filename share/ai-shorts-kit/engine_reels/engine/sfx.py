"""Sound effects from Freesound (free API; the cloud proxy adds the key, on a PC set FREESOUND_KEY).
reel.json:  "sfx": [[story_sec, "paper rustle", volume], ...]   (volume optional, default 0.5)
  python make.py reels/<reel> sfx            -> download what's missing to sfx_library/, build build/sfx.wav
  python make.py sfx "paper whoosh"          -> browse: top results with duration and license
If Freesound is unreachable (blocked network), a built-in paper-style sound is made instead; "synth:whoosh" forces it.
Only Creative Commons 0 sounds are used by default (no credit needed); set "sfx_license": "any" to allow CC-BY (credits in sfx_library/CREDITS.txt)."""
import os, re, json, urllib.parse, urllib.request, numpy as np
from .config import SR
from .audio import load
LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sfx_library')
API = 'https://freesound.org/apiv2/'

def _get(url):
    h = {'User-Agent': 'ai-shorts-kit'}
    if os.environ.get('FREESOUND_KEY'): h['Authorization'] = 'Token ' + os.environ['FREESOUND_KEY']
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60)

def search(q, n=8, cc0=True, max_len=6):
    flt = f'duration:[0.2 TO {max_len}]' + (' license:"Creative Commons 0"' if cc0 else '')
    url = API + 'search/text/?' + urllib.parse.urlencode({'query': q, 'filter': flt, 'sort': 'score', 'page_size': n,
                                                          'fields': 'id,name,duration,license,username,previews,avg_rating,num_downloads'})
    with _get(url) as r: return json.load(r).get('results', [])

def fetch(q, cc0=True):
    """best match for q -> local mp3 path (cached by query)"""
    os.makedirs(LIB, exist_ok=True); idx_p = os.path.join(LIB, 'index.json')
    idx = json.load(open(idx_p)) if os.path.exists(idx_p) else {}
    if q in idx and os.path.exists(os.path.join(LIB, idx[q])): return os.path.join(LIB, idx[q])
    res = search(q, 5, cc0) or (search(q, 5, False) if not cc0 else [])
    if not res: raise SystemExit(f'no Freesound result for "{q}" - try other words (python make.py sfx "{q}")')
    s = max(res, key=lambda r: (r.get('avg_rating') or 0) * 0.5 + np.log1p(r.get('num_downloads') or 0))
    fn = re.sub(r'[^a-z0-9]+', '_', q.lower()).strip('_') + f"_{s['id']}.mp3"
    with _get(s['previews']['preview-hq-mp3']) as r, open(os.path.join(LIB, fn), 'wb') as f: f.write(r.read())
    idx[q] = fn; json.dump(idx, open(idx_p, 'w'), indent=1)
    with open(os.path.join(LIB, 'CREDITS.txt'), 'a', encoding='utf-8') as f:
        f.write(f"{fn}: \"{s['name']}\" by {s['username']} - {s['license']} - https://freesound.org/s/{s['id']}/\n")
    print(f"  sfx \"{q}\" -> {s['name']} ({s['duration']:.1f}s, {s['license'].split('/')[-3] if '/' in s['license'] else s['license']})")
    return os.path.join(LIB, fn)

def run(reel):
    """place every reel.json sfx cue (story time -> video time) into build/sfx.wav"""
    cues = reel.cfg.get('sfx', [])
    if not cues: print('  no "sfx" in reel.json'); return None
    cc0 = reel.cfg.get('sfx_license', 'cc0') == 'cc0'; dur = reel.timing['duration']
    out = np.zeros((int(dur * SR) + SR, 2), np.float32)
    for c in cues:
        t, q, vol = c[0], c[1], (c[2] if len(c) > 2 else 0.5)
        if q.startswith('synth:'): src = synth_file(q[6:])
        else:
            try: src = fetch(q, cc0)
            except Exception as e: print(f'  Freesound unavailable for "{q}" ({str(e)[:50]}) -> built-in sound'); src = synth_file(q)
        x = load(src, ch=2).reshape(-1, 2); x = x / max(1e-4, np.abs(x).max()) * vol
        x[-int(.05 * SR):] *= np.linspace(1, 0, int(.05 * SR))[:, None][:len(x[-int(.05 * SR):])]
        i = int(reel.video(t) * SR); n = min(len(x), len(out) - i)
        if n > 0: out[i:i + n] += x[:n]
    import wave
    p = os.path.join(reel.build, 'sfx.wav')
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(out[:int(dur * SR)], -1, 1) * 32767).astype(np.int16).tobytes())
    print(f'  build/sfx.wav: {len(cues)} cues'); return p

def browse(q):
    for r in search(q, 10, cc0=False):
        lic = 'CC0' if 'zero' in r['license'] or '/publicdomain/' in r['license'] else 'CC-BY' if '/by/' in r['license'] else 'CC-other'
        print(f"  {r['duration']:5.1f}s  {lic:6}  ★{(r.get('avg_rating') or 0):.1f}  {r['name'][:60]}  https://freesound.org/s/{r['id']}/")

# ---------- built-in paper-style sounds (no network): used when Freesound is unreachable, or with "synth:<name>" ----------
def _env(n, a, d): t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-3)) * np.exp(-t / d)

def synth(name, seed=0):
    rng = np.random.default_rng(seed); name = name.lower()
    def noise(sec): return rng.standard_normal(int(sec * SR)).astype(np.float32)
    def lp(x, k): return np.convolve(x, np.ones(k) / k, 'same')
    if 'whoosh' in name or 'swoosh' in name:
        n = int(.8 * SR); x = noise(.8); t = np.arange(n) / n; out = np.zeros(n, np.float32)
        for i in range(0, n, 512):        # sweeping band: low -> high -> low
            k = int(40 - 34 * np.sin(np.pi * t[i])); seg = x[i:i + 512]; out[i:i + 512] = seg - lp(seg, k)
        return out * np.sin(np.pi * t) ** 2
    if 'paper' in name or 'rustle' in name or 'page' in name:
        n = int(.6 * SR); x = noise(.6); x = x - lp(x, 6); bursts = np.zeros(n)
        for _ in range(14): c = rng.integers(0, n - 2000); bursts[c:c + 2000] += np.hanning(2000) * rng.uniform(.3, 1)
        return (x * bursts * np.hanning(n)).astype(np.float32)
    if 'thud' in name or 'drop' in name or 'heartbeat' in name:
        n = int(.5 * SR); t = np.arange(n) / SR; x = np.sin(2 * np.pi * (60 + 40 * np.exp(-t * 30)) * t) * _env(n, .004, .12)
        if 'heartbeat' in name: x = x + np.roll(x, int(.28 * SR)) * .7
        return x.astype(np.float32)
    if 'tick' in name or 'click' in name or 'clock' in name:
        n = int(.06 * SR); return (noise(.06) * _env(n, .0005, .006) + np.sin(2 * np.pi * 2400 * np.arange(n) / SR) * _env(n, .0005, .01)).astype(np.float32)
    # chime / twinkle / sparkle / bell (default): soft bell partials
    n = int(2.2 * SR); t = np.arange(n) / SR; f0 = 880 if 'twinkle' in name or 'sparkle' in name else 660; x = np.zeros(n)
    for k, (m, a) in enumerate([(1, 1), (2.76, .5), (5.4, .25), (8.9, .12)]):
        x += a * np.sin(2 * np.pi * f0 * m * t) * _env(n, .002, .9 / (1 + k))
    return x.astype(np.float32)

def synth_file(name):
    import wave
    os.makedirs(LIB, exist_ok=True); p = os.path.join(LIB, 'synth_' + re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_') + '.wav')
    if not os.path.exists(p):
        x = synth(name); x = x / max(1e-4, np.abs(x).max()) * .9
        with wave.open(p, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
    return p
