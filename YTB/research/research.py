"""PaperLit Research - a free vidIQ-style toolkit (YouTube Data API v3 + YouTube autocomplete + Google Trends).

  python research.py suggest "would you rather"            keyword ideas from YouTube autocomplete (free, no key)
  python research.py keyword "free will"                   competition: top results, their views, age, avg views/day, common tags
  python research.py outliers @channel1 @channel2 ...       each channel's recent Shorts that beat its own median (viral finder)
  python research.py niche "philosophy shorts"             find channels in a niche + their outlier videos
  python research.py trending US                            what's trending now (region code)
  python research.py channel @paperlit                     stats + every video; appends a snapshot to history/ for tracking
  python research.py comments VIDEO_ID                     top comments (ideas, questions people ask)
  python research.py title "Would You Open It? 📩"           title score with tips (free, offline)
  python research.py trends "free will" "death" "time"       Google Trends (YouTube searches): rising or fading, + rising related searches

API key: in the cloud session the proxy adds it (network secret on www.googleapis.com, header X-Goog-Api-Key).
On your PC: set the environment variable YT_API_KEY. Quota is free: 10,000 units/day (search = 100, others = 1).
"""
import os, sys, re, json, math, statistics, datetime, urllib.parse, urllib.request
API = 'https://www.googleapis.com/youtube/v3/'
HERE = os.path.dirname(os.path.abspath(__file__))
KEY = os.environ.get('YT_API_KEY', '')

def get(path, **params):
    if KEY: params['key'] = KEY
    url = API + path + '?' + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'paperlit-research'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        msg = e.read().decode()[:300]
        sys.exit(f'YouTube API error {e.code}: {msg}\n(no/invalid API key? see the top of this file)')

def iso_dur(s):
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', s or '');  h, mi, se = (int(x or 0) for x in m.groups()) if m else (0, 0, 0)
    return h * 3600 + mi * 60 + se

def age_days(ts): return max(0.5, (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))).total_seconds() / 86400)

def videos(ids):
    out = []
    for i in range(0, len(ids), 50):
        out += get('videos', part='snippet,statistics,contentDetails', id=','.join(ids[i:i + 50])).get('items', [])
    for v in out:
        st = v.get('statistics', {}); v['views'] = int(st.get('viewCount', 0)); v['likes'] = int(st.get('likeCount', 0))
        v['comments'] = int(st.get('commentCount', 0)); v['secs'] = iso_dur(v['contentDetails'].get('duration'))
        v['age'] = age_days(v['snippet']['publishedAt']); v['vpd'] = v['views'] / v['age']
        v['short'] = v['secs'] <= 180
    return out

def channel_id(handle):
    if handle.startswith('UC'): return handle
    r = get('channels', part='id', forHandle=handle.lstrip('@'))
    if not r.get('items'): sys.exit(f'channel not found: {handle}')
    return r['items'][0]['id']

def channel_videos(cid, n=50):
    ch = get('channels', part='snippet,statistics,contentDetails', id=cid)['items'][0]
    up = ch['contentDetails']['relatedPlaylists']['uploads']; ids, tok = [], None
    while len(ids) < n:
        r = get('playlistItems', part='contentDetails', playlistId=up, maxResults=50, **({'pageToken': tok} if tok else {}))
        ids += [i['contentDetails']['videoId'] for i in r.get('items', [])]; tok = r.get('nextPageToken')
        if not tok: break
    return ch, videos(ids[:n])

def fmt(n): return f'{n/1e6:.1f}M' if n >= 1e6 else f'{n/1e3:.1f}K' if n >= 1e3 else str(int(n))

# ---------- commands ----------
def suggest(q):
    """YouTube autocomplete, plus a-z expansion (what people actually type)"""
    seen = []
    for suffix in [''] + [' ' + c for c in 'abcdefghijklmnopqrstuvwxyz'] + [' why', ' what if', ' would you']:
        url = 'https://suggestqueries.google.com/complete/search?' + urllib.parse.urlencode({'client': 'firefox', 'ds': 'yt', 'q': q + suffix})
        try:
            with urllib.request.urlopen(url, timeout=15) as r: data = json.loads(r.read().decode('utf-8', 'ignore'))
        except Exception: continue
        for s in data[1]:
            if s not in seen: seen.append(s)
    print(f'{len(seen)} keyword ideas for "{q}":'); [print('  -', s) for s in seen[:80]]

def keyword(q, shorts=True):
    r = get('search', part='id', q=q, type='video', maxResults=25, order='relevance', **({'videoDuration': 'short'} if shorts else {}))
    vs = videos([i['id']['videoId'] for i in r.get('items', [])])
    if not vs: return print('no results')
    views = [v['views'] for v in vs]; med = statistics.median(views); young = [v for v in vs if v['age'] < 90]
    big = sum(1 for v in vs if v['views'] > 1e6)
    comp = min(100, int(20 * math.log10(max(med, 1))))       # 0-100, higher = harder
    print(f'"{q}" ({"Shorts" if shorts else "all"}): median views {fmt(med)}, {big}/25 over 1M, {len(young)}/25 younger than 90 days')
    print(f'  competition score ~{comp}/100  ({"low" if comp < 50 else "medium" if comp < 75 else "high"});  fresh-video share {len(young) * 4}% (higher = room for new creators)')
    tags = {}
    for v in vs:
        for t in v['snippet'].get('tags', []) or []: tags[t.lower()] = tags.get(t.lower(), 0) + 1
    print('  common tags:', ', '.join(t for t, c in sorted(tags.items(), key=lambda x: -x[1])[:15]))
    print('  top results:')
    for v in sorted(vs, key=lambda v: -v['views'])[:10]:
        print(f"   {fmt(v['views']):>7} views  {fmt(v['vpd']):>6}/day  {int(v['age']):>4}d  {v['snippet']['channelTitle'][:22]:22}  {v['snippet']['title'][:70]}")

def outliers(handles, min_x=3.0):
    for h in handles:
        ch, vs = channel_videos(channel_id(h)); vs = [v for v in vs if v['short']] or vs
        med = statistics.median([v['views'] for v in vs]) or 1
        print(f"\n{ch['snippet']['title']} ({fmt(int(ch['statistics'].get('subscriberCount', 0)))} subs) - median {fmt(med)} views over {len(vs)} recent")
        for v in sorted(vs, key=lambda v: -v['views']):
            x = v['views'] / med
            if x >= min_x: print(f"   {x:5.1f}x  {fmt(v['views']):>7}  {int(v['age']):>4}d  {v['snippet']['title'][:80]}  https://youtu.be/{v['id']}")

def niche(q):
    r = get('search', part='snippet', q=q, type='channel', maxResults=8)
    hs = [i['id']['channelId'] for i in r.get('items', [])]
    print('channels found:', ', '.join(i['snippet']['title'] for i in r.get('items', [])))
    outliers(hs, 2.5)

def trending(region='US'):
    r = get('videos', part='snippet,statistics,contentDetails', chart='mostPopular', regionCode=region, maxResults=30)
    for v in r.get('items', []):
        print(f"  {fmt(int(v['statistics'].get('viewCount', 0))):>7}  {v['snippet']['channelTitle'][:22]:22}  {v['snippet']['title'][:80]}")

def channel(h):
    ch, vs = channel_videos(channel_id(h)); st = ch['statistics']
    print(f"{ch['snippet']['title']}: {st.get('subscriberCount')} subs, {st.get('viewCount')} views, {st.get('videoCount')} videos")
    for v in sorted(vs, key=lambda v: v['snippet']['publishedAt']):
        eng = (v['likes'] + v['comments']) / max(v['views'], 1) * 100
        print(f"  {v['snippet']['publishedAt'][:10]}  {fmt(v['views']):>6} views  {fmt(v['vpd']):>6}/day  eng {eng:4.1f}%  {v['snippet']['title'][:70]}")
    os.makedirs(os.path.join(HERE, 'history'), exist_ok=True)
    snap = {'date': datetime.date.today().isoformat(), 'subs': st.get('subscriberCount'), 'videos': {v['id']: v['views'] for v in vs}}
    with open(os.path.join(HERE, 'history', f"{ch['snippet']['title']}.jsonl"), 'a') as f: f.write(json.dumps(snap) + '\n')
    print('  (snapshot saved to history/ - run again later to track growth)')

def comments(vid):
    r = get('commentThreads', part='snippet', videoId=vid, maxResults=50, order='relevance', textFormat='plainText')
    for c in r.get('items', []):
        s = c['snippet']['topLevelComment']['snippet']; print(f"  [{s['likeCount']:>4} likes] {s['authorDisplayName']}: {s['textDisplay'][:200]}")

def title(t):
    s, tips = title_score(t); print(f'title score {s}/100  ' + ('; '.join(tips) if tips else 'strong'))

def title_score(t):
    """offline title score, tuned for curiosity/question Shorts -> (score, tips)"""
    s, tips = 50, []
    n = len(t); s += 10 if 25 <= n <= 60 else -10; tips += [] if 25 <= n <= 60 else ['keep it 25-60 characters']
    if '?' in t: s += 12
    else: tips.append('ask a question')
    if re.search(r'\b(you|your)\b', t, re.I): s += 12
    else: tips.append('speak to the viewer ("you")')
    if re.search(r'^(would|what|why|how|are|is|do|did|can)\b', t, re.I): s += 8
    if re.search(r'\d', t): s += 4
    if re.search(r'[\U0001F300-\U0001FAFF]', t): s += 3
    if t.count('#') > 3: s -= 8; tips.append('max 2-3 hashtags in the title')
    if re.search(r'\b(paradox|explained|in \d+ seconds)\b', t, re.I): s -= 6; tips.append('avoid textbook words; make it personal')
    return max(0, min(100, s)), tips

def trends(terms, geo=''):
    """Google Trends for YouTube search, last 90 days: is each topic rising or fading right now?"""
    from pytrends.request import TrendReq
    pt = TrendReq(hl='en-US', tz=0, timeout=(10, 30))
    for i in range(0, len(terms), 5):
        grp = terms[i:i + 5]; pt.build_payload(grp, timeframe='today 3-m', geo=geo, gprop='youtube'); df = pt.interest_over_time()
        if df.empty: print('  no Trends data for', ', '.join(grp)); continue
        for t in grp:
            s = df[t].astype(float); last, prev = s.iloc[-14:].mean(), s.iloc[-42:-14].mean()
            ch = (last - prev) / max(prev, 1) * 100; arrow = 'RISING' if ch > 15 else 'fading' if ch < -15 else 'steady'
            spark = ''.join(' ▁▂▃▄▅▆▇█'[min(8, int(v / 12.5))] for v in s.iloc[::max(1, len(s) // 26)])
            print(f'  {t[:24]:24}  avg {s.mean():5.1f}  {arrow:6} {ch:+5.0f}%  {spark}')
        try:
            rel = pt.related_queries()
            for t in grp:
                r = (rel.get(t) or {}).get('rising')
                if r is not None and not r.empty: print(f'    rising searches for "{t}":', ', '.join(r['query'].head(8)))
        except Exception: pass

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    c, a = sys.argv[1], sys.argv[2:]
    {'suggest': lambda: suggest(' '.join(a)), 'keyword': lambda: keyword(' '.join(a)), 'outliers': lambda: outliers(a),
     'niche': lambda: niche(' '.join(a)), 'trending': lambda: trending(a[0] if a else 'US'), 'channel': lambda: channel(a[0]),
     'comments': lambda: comments(a[0]), 'trends': lambda: trends(a), 'title': lambda: title(' '.join(a))}.get(c, lambda: sys.exit(__doc__))()
