"""PaperLit data study - every recommendation here is measured on real Shorts, and tested on videos the model never saw.

  python study.py collect [queries.txt]     gather niche Shorts + each channel's normal views (~6,000 of the 10,000 daily API units)
  python study.py report [--tz Europe/Paris] what actually beats a channel's normal: title patterns, tags, length, day/hour - with confidence
  python study.py score "Would You Open It? 📩"   title score learned from the data (+ how reliable the model is)
  python study.py scoreboard @paperlit       our videos: model prediction vs what really happened
  python study.py top "death"               best-performing Shorts on a topic (to study their hooks)

How "good" is judged: a video's lift = its views / its own channel's median Short views, so a tiny channel's 20K-view hit counts
as much as a giant's. Videos under 7 days old are left out (not settled yet). Effects are shown with 95% intervals; when an interval
crosses 1.00x the effect is not proven. The title model is trained on 80% of channels and graded on the other 20% it never saw.
"""
import os, sys, re, json, math, random, statistics, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from research import get, videos, channel_id, fmt
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, 'data'); DS = os.path.join(DATA, 'shorts.jsonl'); CH = os.path.join(DATA, 'channels.json')
QUERIES = ['philosophy', 'philosophy shorts', 'deep questions', 'would you rather', 'would you', 'what if', 'existential', 'meaning of life',
           'free will', 'death philosophy', 'simulation theory', 'stoicism', 'thought experiment', 'deep thoughts', 'mind blowing questions',
           'questions that break your brain', 'how small are we', 'universe perspective', 'consciousness', 'time philosophy', 'afterlife',
           'are we alone', 'paradox', 'moral dilemma', 'trolley problem', 'nihilism', 'reality is not real', 'animated story short', 'life lesson animation', 'existential crisis']

# ---------------- collect ----------------
def collect(qfile=None):
    qs = [l.strip() for l in open(qfile)] if qfile else QUERIES; os.makedirs(DATA, exist_ok=True)
    have = {json.loads(l)['id'] for l in open(DS)} if os.path.exists(DS) else set()
    after = (datetime.datetime.utcnow() - datetime.timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ'); ids = []
    for q in qs:
        r = get('search', part='id', q=q, type='video', videoDuration='short', maxResults=50, order='viewCount', publishedAfter=after)
        new = [i['id']['videoId'] for i in r.get('items', []) if i['id']['videoId'] not in have]; ids += new; have.update(new)
        print(f'  "{q}": {len(new)} new')
    vs = videos(list(dict.fromkeys(ids)))
    with open(DS, 'a') as f:
        for v in vs:
            if v['secs'] > 180: continue
            sn = v['snippet']; f.write(json.dumps({'id': v['id'], 'title': sn['title'], 'tags': sn.get('tags', []), 'ch': sn['channelId'],
                'chname': sn['channelTitle'], 'published': sn['publishedAt'], 'views': v['views'], 'likes': v['likes'], 'comments': v['comments'],
                'secs': v['secs'], 'desc': sn.get('description', '')[:300], 'got': datetime.date.today().isoformat()}) + '\n')
    baselines()

def baselines():
    """each channel's median views over its last 50 Shorts (older than 7 days)"""
    chs = json.load(open(CH)) if os.path.exists(CH) else {}; need = {json.loads(l)['ch'] for l in open(DS)} - set(chs)
    print(f'  channel baselines to fetch: {len(need)}')
    for i, c in enumerate(need):
        try:
            ch = get('channels', part='statistics,contentDetails', id=c)['items'][0]; up = ch['contentDetails']['relatedPlaylists']['uploads']
            r = get('playlistItems', part='contentDetails', playlistId=up, maxResults=50)
            vs = [v for v in videos([x['contentDetails']['videoId'] for x in r.get('items', [])]) if v['short'] and v['age'] > 7]
            chs[c] = {'subs': int(ch['statistics'].get('subscriberCount', 0)), 'median': statistics.median([v['views'] for v in vs]) if len(vs) >= 5 else None, 'n': len(vs)}
        except (Exception, SystemExit): chs[c] = {'median': None}
        if i % 50 == 0: json.dump(chs, open(CH, 'w'))
    json.dump(chs, open(CH, 'w')); print(f'  dataset: {sum(1 for _ in open(DS))} Shorts, {sum(1 for c in chs.values() if c.get("median"))} channels with a baseline')

# ---------------- features ----------------
EMOJI = re.compile(r'[\U0001F300-\U0001FAFF☀-➿]')
def feats(title, secs=None, published=None):
    t = re.sub(r'#\S+', '', title).strip(); low = t.lower(); f = {}
    f['question mark'] = '?' in t
    f['says "you/your"'] = bool(re.search(r'\b(you|your|you\'re)\b', low))
    f['starts with a question word'] = bool(re.match(r'(would|what|why|how|are|is|do|did|can|could|have|who|where|when)\b', low))
    f['"would you"'] = 'would you' in low
    f['"what if"'] = 'what if' in low
    f['"imagine"'] = 'imagine' in low
    f['"why"'] = bool(re.search(r'\bwhy\b', low))
    f['has a number'] = bool(re.search(r'\d', t))
    f['has an emoji'] = bool(EMOJI.search(title))
    f['2+ hashtags in title'] = title.count('#') >= 2
    f['textbook word (paradox/explained/in N sec)'] = bool(re.search(r'\b(paradox|explained|in \d+ seconds|theory)\b', low))
    f['"philosophy" in title'] = 'philosoph' in low
    f['ALL-CAPS word'] = bool(re.search(r'\b[A-Z]{3,}\b', t))
    f['ellipsis …'] = '...' in t or '…' in t
    f['exclamation !'] = '!' in t
    f['short title (<30 chars)'] = len(t) < 30
    f['long title (>60 chars)'] = len(t) > 60
    f['fear/dark word (terrifying/die/death/dark)'] = bool(re.search(r'\b(terrif\w*|scar\w*|die|dying|death|dead|dark)\b', low))
    f['"you" + question'] = f['says "you/your"'] and f['question mark']
    if secs is not None:
        f['under 30s'] = secs < 30; f['45-60s'] = 45 <= secs <= 60; f['over 60s'] = secs > 60
    return f

def load(min_age=7):
    chs = json.load(open(CH)); rows = []
    for l in open(DS):
        v = json.loads(l); b = chs.get(v['ch'], {}).get('median')
        age = (datetime.datetime.fromisoformat(v['got']) - datetime.datetime.fromisoformat(v['published'][:10])).days
        if not b or age < min_age: continue
        v['lift'] = math.log((v['views'] + 10) / (b + 10)); v['f'] = feats(v['title'], v['secs']); rows.append(v)
    return rows

def ci_diff(a, b, n=1000):
    """bootstrap 95% interval of mean(a) - mean(b) in log-lift -> multiplier"""
    a, b = np.array(a), np.array(b); rng = np.random.default_rng(0)
    d = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(n)]
    return math.exp(a.mean() - b.mean()), math.exp(np.percentile(d, 2.5)), math.exp(np.percentile(d, 97.5))

def verdict(m, lo, hi): return 'PROVEN +' if lo > 1 else 'PROVEN -' if hi < 1 else 'not proven'

# ---------------- model ----------------
def fit(rows, lam=3.0):
    names = list(rows[0]['f']); X = np.array([[r['f'][k] for k in names] for r in rows], float); y = np.array([r['lift'] for r in rows])
    mu = X.mean(0); Xc = X - mu; w = np.linalg.solve(Xc.T @ Xc + lam * np.eye(len(names)), Xc.T @ (y - y.mean()))
    return {'names': names, 'w': w.tolist(), 'mu': mu.tolist(), 'b': float(y.mean())}

def predict(m, f): return m['b'] + sum(wi * (f.get(k, 0) - mi) for k, wi, mi in zip(m['names'], m['w'], m['mu']))

def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b)); return float(np.corrcoef(ra, rb)[0, 1])

def validate(rows, k=5):
    """split by CHANNEL (so the model can't memorise a channel), train on 4/5, test on 1/5"""
    chans = sorted({r['ch'] for r in rows}); random.Random(1).shuffle(chans); folds = [set(chans[i::k]) for i in range(k)]
    rhos, tops = [], []
    for fo in folds:
        tr = [r for r in rows if r['ch'] not in fo]; te = [r for r in rows if r['ch'] in fo]
        if len(te) < 30: continue
        m = fit(tr); p = [predict(m, r['f']) for r in te]; y = [r['lift'] for r in te]; rhos.append(spearman(p, y))
        order = np.argsort(p); q = len(te) // 4                                   # top-quarter predicted vs bottom-quarter predicted
        tops.append(math.exp(np.mean([y[i] for i in order[-q:]]) - np.mean([y[i] for i in order[:q]])))
    return float(np.mean(rhos)), float(np.mean(tops))

# ---------------- commands ----------------
def report(tz=None):
    rows = load(); print(f'{len(rows)} Shorts from {len({r["ch"] for r in rows})} channels (each judged against its own channel median)\n')
    print('TITLE & LENGTH PATTERNS  (x = how many times more views vs the channel normal, compared with videos without it)')
    out = []
    for k in rows[0]['f']:
        a = [r['lift'] for r in rows if r['f'][k]]; b = [r['lift'] for r in rows if not r['f'][k]]
        if len(a) >= 25 and len(b) >= 25: out.append((k, len(a)) + ci_diff(a, b))
    for k, n, m, lo, hi in sorted(out, key=lambda x: -x[2]): print(f'  {m:5.2f}x  [{lo:4.2f}-{hi:4.2f}]  {verdict(m, lo, hi):10}  n={n:<5} {k}')
    print('\nTAGS  (used by 20+ videos)')
    cnt = {}
    for r in rows:
        for t in {t.lower() for t in r['tags']}: cnt.setdefault(t, []).append(r['lift'])
    allv = [r['lift'] for r in rows]; tg = []
    for t, a in cnt.items():
        if len(a) >= 20: tg.append((t, len(a)) + ci_diff(a, allv, 400))
    for t, n, m, lo, hi in sorted(tg, key=lambda x: -x[2])[:20]: print(f'  {m:5.2f}x  [{lo:4.2f}-{hi:4.2f}]  {verdict(m, lo, hi):10}  n={n:<4} {t}')
    print(f'  ({sum(1 for r in rows if not r["tags"])}/{len(rows)} winning-or-not videos use no tags at all; tags matter little for Shorts reach)')
    from zoneinfo import ZoneInfo
    z = ZoneInfo(tz) if tz else datetime.timezone.utc; zn = tz or 'UTC'
    def local(r): return datetime.datetime.fromisoformat(r['published'].replace('Z', '+00:00')).astimezone(z)
    print(f'\nPUBLISH DAY  ({zn})')
    for d, name in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
        a = [r['lift'] for r in rows if local(r).weekday() == d]; b = [r['lift'] for r in rows if local(r).weekday() != d]
        if len(a) >= 20: m, lo, hi = ci_diff(a, b, 400); print(f'  {name}  {m:5.2f}x  [{lo:4.2f}-{hi:4.2f}]  {verdict(m, lo, hi):10}  n={len(a)}')
    print(f'\nPUBLISH HOUR  ({zn}, 3-hour blocks)')
    for h in range(0, 24, 3):
        a = [r['lift'] for r in rows if h <= local(r).hour < h + 3]; b = [r['lift'] for r in rows if not h <= local(r).hour < h + 3]
        if len(a) >= 20: m, lo, hi = ci_diff(a, b, 400); print(f'  {h:02}:00-{h + 3:02}:00  {m:5.2f}x  [{lo:4.2f}-{hi:4.2f}]  {verdict(m, lo, hi):10}  n={len(a)}')
    rho, top = validate(rows)
    print(f'\nTITLE MODEL TEST (on channels it never saw): rank correlation {rho:+.2f}; titles it rates top-25% got {top:.2f}x the views of its bottom-25%.')
    print('  ' + ('useful signal' if rho > .1 and top > 1.3 else 'weak signal - treat title scores as a tie-breaker, not a rule'))
    m = fit(rows); json.dump(m | {'rho': rho, 'top': top, 'n': len(rows), 'pred': sorted(predict(m, r['f']) for r in rows)}, open(os.path.join(DATA, 'model.json'), 'w'))

def score(title, secs=None):
    m = json.load(open(os.path.join(DATA, 'model.json'))); f = feats(title, secs); p = predict(m, f)
    pct = 100 * np.searchsorted(m['pred'], p) / len(m['pred'])
    print(f'"{title}": better than {pct:.0f}% of {m["n"]} niche Shorts titles  (expected {math.exp(p):.2f}x channel normal)')
    contrib = sorted(((wi * (f.get(k, 0) - mi), k) for k, wi, mi in zip(m['names'], m['w'], m['mu'])), reverse=True)
    print('  helps: ' + ', '.join(f'{k} ({math.exp(c):.2f}x)' for c, k in contrib[:3] if c > .02))
    print('  hurts: ' + ', '.join(f'{k} ({math.exp(c):.2f}x)' for c, k in contrib[::-1][:3] if c < -.02))
    print(f'  model reliability: rank correlation {m["rho"]:+.2f} on unseen channels ({"useful" if m["rho"] > .1 else "weak - tie-breaker only"})')

def scoreboard(h):
    from research import channel_videos
    m = json.load(open(os.path.join(DATA, 'model.json'))); ch, vs = channel_videos(channel_id(h)); med = statistics.median([v['views'] for v in vs]) or 1
    print(f"{ch['snippet']['title']}: median {fmt(med)} views.  predicted = model's title rank, actual = views vs our median")
    rows = [(predict(m, feats(v['snippet']['title'], v['secs'])), v['views'] / med, v) for v in vs]
    for p, a, v in sorted(rows, key=lambda x: -x[1]):
        print(f"  pred {100 * np.searchsorted(m['pred'], p) / len(m['pred']):3.0f}%   actual {a:5.2f}x  {fmt(v['views']):>6}  {int(v['age'])}d  {v['snippet']['title'][:60]}")
    if len(rows) >= 5: print(f'  agreement so far: {spearman([r[0] for r in rows], [r[1] for r in rows]):+.2f} (needs ~15 videos to mean much)')

def top(q, n=15):
    rows = [r for r in load() if re.search(q, r['title'] + ' ' + ' '.join(r['tags']), re.I)]
    for r in sorted(rows, key=lambda r: -r['lift'])[:n]:
        print(f"  {math.exp(r['lift']):6.1f}x  {fmt(r['views']):>6}  {r['secs']:>3}s  {r['chname'][:18]:18}  {r['title'][:70]}  https://youtu.be/{r['id']}")

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    c, a = sys.argv[1], sys.argv[2:]
    tz = a[a.index('--tz') + 1] if '--tz' in a else None
    {'collect': lambda: collect(a[0] if a else None), 'baselines': baselines, 'report': lambda: report(tz), 'score': lambda: score(' '.join(a)),
     'scoreboard': lambda: scoreboard(a[0]), 'top': lambda: top(' '.join(a))}.get(c, lambda: sys.exit(__doc__))()
