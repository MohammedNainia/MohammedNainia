"""PaperLit YouTube publisher - free, official YouTube Data API (no vidIQ credits).

  python youtube_publish.py reel ..\\lanternfold\\reels\\06_would_you_know            upload + title/desc/tags/cover, scheduled next 04:00 Morocco
  python youtube_publish.py reel ..\\lanternfold\\reels\\07_x --when "2026-11-11 04:00"   pick the slot (Morocco time)
  python youtube_publish.py reel ..\\lanternfold\\reels\\07_x --now                     public right away
  python youtube_publish.py edit VIDEO_ID --title "..." [--desc-file d.txt] [--tags "a, b"] [--thumb cover.jpg] [--when "..." | --now]
  python youtube_publish.py list                                                     your latest videos (incl. private / scheduled)
  python youtube_publish.py comments                                                 comments you haven't answered yet (with their IDs)
  python youtube_publish.py reply COMMENT_ID "Thank you so much!"                    reply as PaperLit (no vidIQ credits)

Reads from the reel folder: <slug>_1080x1920.mp4, thumbnail_1080x1920.jpg and seo.md (**Title:**, **Tags:**, **Description:** ... **Pinned comment:**).
It posts the pinned-comment text as a comment (YouTube's API cannot pin; tap "Pin" on it in the app).
Every upload is "not made for kids", category Education, language English.
First run opens your browser once to sign in to the PaperLit channel; after that it remembers (token.json). See SETUP.md.
"""
import os, re, sys, glob, json, argparse, datetime
from zoneinfo import ZoneInfo
HERE = os.path.dirname(os.path.abspath(__file__))
TZ = ZoneInfo('Africa/Casablanca')
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.force-ssl']
CATEGORY = '27'          # Education (Film & Animation = '1')

def yt():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    tok, sec = os.path.join(HERE, 'token.json'), os.path.join(HERE, 'client_secret.json')
    creds = Credentials.from_authorized_user_file(tok, SCOPES) if os.path.exists(tok) else None
    if creds and creds.expired and creds.refresh_token:
        try: creds.refresh(Request())
        except Exception: creds = None
    if not creds or not creds.valid:
        if not os.path.exists(sec): sys.exit('client_secret.json missing - follow SETUP.md step 1-4 and put it next to this script')
        creds = InstalledAppFlow.from_client_secrets_file(sec, SCOPES).run_local_server(port=0)
        open(tok, 'w').write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)

def seo(path):
    s = open(path, encoding='utf-8').read()
    title = re.search(r'\*\*Title:\*\*\s*(.+)', s).group(1).strip()
    tags = [t.strip() for t in re.search(r'\*\*Tags:\*\*\s*(.+)', s).group(1).split(',')] if '**Tags:**' in s else []
    m = re.search(r'\*\*Description:\*\*\s*\n(.*?)\n\s*\*\*Pinned comment:\*\*[ \t]*([^\n]+)', s, re.S)
    desc, pin = (m.group(1).strip(), m.group(2).strip()) if m else (re.search(r'\*\*Description:\*\*\s*\n(.*?)(\n## |\Z)', s, re.S).group(1).strip(), None)
    return title, desc, tags, pin

def guard(title, desc, tags):
    """channel rules, checked before anything goes out"""
    for name, txt in (('title', title), ('description', desc), ('tags', ', '.join(tags))):
        if '—' in txt: sys.exit(f'STOP: long dash "—" in the {name}. Channel rule: never use it.')
    if len(title) > 100: sys.exit(f'STOP: title is {len(title)} characters (max 100)')
    if len(', '.join(tags)) > 480: sys.exit('STOP: tags over YouTube\'s 500-character limit')

def slot(when=None):
    """Morocco-time string -> UTC ISO. Default: the next 04:00 Morocco time at least 1 hour away."""
    if when: t = datetime.datetime.strptime(when, '%Y-%m-%d %H:%M').replace(tzinfo=TZ)
    else:
        now = datetime.datetime.now(TZ); t = now.replace(hour=4, minute=0, second=0, microsecond=0)
        if t < now + datetime.timedelta(minutes=10): t += datetime.timedelta(days=1)
    return t, t.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def set_thumb(y, vid, path):
    from googleapiclient.http import MediaFileUpload
    try:
        y.thumbnails().set(videoId=vid, media_body=MediaFileUpload(path, mimetype='image/jpeg')).execute(); print('  thumbnail set')
    except Exception as e:
        print(f'  thumbnail NOT set: {str(e)[:160]}\n  (custom thumbnails need a phone-verified channel: studio.youtube.com > Settings > Channel > Feature eligibility)')

def reel(folder, when=None, now=False):
    from googleapiclient.http import MediaFileUpload
    folder = os.path.abspath(folder); mp4 = next(iter(glob.glob(os.path.join(folder, '*_1080x1920.mp4'))), None)
    if not mp4: sys.exit('no *_1080x1920.mp4 in ' + folder)
    title, desc, tags, pin = seo(os.path.join(folder, 'seo.md')); guard(title, desc, tags)
    status = {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
    if not now:
        local, utc = slot(when); status = {'privacyStatus': 'private', 'publishAt': utc, 'selfDeclaredMadeForKids': False}
    body = {'snippet': {'title': title, 'description': desc, 'tags': tags, 'categoryId': CATEGORY, 'defaultLanguage': 'en', 'defaultAudioLanguage': 'en'},
            'status': status}
    print(f'Uploading {os.path.basename(mp4)}\n  title: {title}\n  ' + ('publishing now' if now else f'scheduled: {local:%A %d %b %H:%M} Morocco time'))
    y = yt(); req = y.videos().insert(part='snippet,status', body=body, media_body=MediaFileUpload(mp4, chunksize=4 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st: print(f'  {int(st.progress() * 100)}%')
    vid = resp['id']; print(f'  uploaded: https://youtu.be/{vid}')
    th = os.path.join(folder, 'thumbnail_1080x1920.jpg')
    if os.path.exists(th): set_thumb(y, vid, th)
    if pin and now:
        try:
            y.commentThreads().insert(part='snippet', body={'snippet': {'videoId': vid, 'topLevelComment': {'snippet': {'textOriginal': pin}}}}).execute()
            print('  comment posted (open the video in the YouTube app and tap ⋮ > Pin on it)')
        except Exception: print(f'  comment not posted yet. Once the video is live, comment and pin:  {pin}')
    elif pin: print(f'  YouTube allows comments only after it goes live. Then comment and pin:  {pin}')
    json.dump({'videoId': vid, 'title': title, 'publishAt': status.get('publishAt')}, open(os.path.join(folder, 'youtube.json'), 'w'))
    print('done.')

def edit(vid, title=None, desc_file=None, tags=None, thumb=None, when=None, now=False):
    y = yt(); v = y.videos().list(part='snippet,status', id=vid).execute()['items'][0]; sn = v['snippet']
    if title: sn['title'] = title
    if desc_file: sn['description'] = open(desc_file, encoding='utf-8').read().strip()
    if tags is not None: sn['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
    guard(sn['title'], sn.get('description', ''), sn.get('tags', []))
    body = {'id': vid, 'snippet': {k: sn[k] for k in ('title', 'description', 'tags', 'categoryId') if k in sn}}
    parts = 'snippet'
    if when:
        _, utc = slot(when); body['status'] = {'privacyStatus': 'private', 'publishAt': utc, 'selfDeclaredMadeForKids': False}; parts += ',status'
    if now:
        body['status'] = {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}; parts += ',status'
    y.videos().update(part=parts, body=body).execute(); print(f'  updated https://youtu.be/{vid}: {sn["title"]}')
    if thumb: set_thumb(y, vid, thumb)

def listing():
    y = yt(); ch = y.channels().list(part='contentDetails,snippet', mine=True).execute()['items'][0]
    up = ch['contentDetails']['relatedPlaylists']['uploads']; print(ch['snippet']['title'])
    ids = [i['contentDetails']['videoId'] for i in y.playlistItems().list(part='contentDetails', playlistId=up, maxResults=15).execute()['items']]
    for v in y.videos().list(part='snippet,status', id=','.join(ids)).execute()['items']:
        st = v['status']; s = st['privacyStatus'] + (f" until {st['publishAt']}" if st.get('publishAt') else '')
        print(f"  {v['id']}  {s:34}  {v['snippet']['title'][:70]}")

def comments():
    y = yt(); ch = y.channels().list(part='id', mine=True).execute()['items'][0]['id']
    r = y.commentThreads().list(part='snippet,replies', allThreadsRelatedToChannelId=ch, maxResults=50, textFormat='plainText', order='time').execute()
    for c in r.get('items', []):
        top = c['snippet']['topLevelComment']['snippet']; reps = c.get('replies', {}).get('comments', [])
        if any(x['snippet'].get('authorChannelId', {}).get('value') == ch for x in reps): continue
        print(f"\n{c['id']}  ({top['authorDisplayName']} on https://youtu.be/{c['snippet']['videoId']})\n  {top['textDisplay'][:300]}")

def reply(cid, text):
    if '—' in text: sys.exit('STOP: long dash "—" in the reply. Channel rule: never use it.')
    y = yt(); y.comments().insert(part='snippet', body={'snippet': {'parentId': cid, 'textOriginal': text}}).execute(); print('  replied')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sub = ap.add_subparsers(dest='cmd')
    r = sub.add_parser('reel'); r.add_argument('folder'); r.add_argument('--when'); r.add_argument('--now', action='store_true')
    e = sub.add_parser('edit'); e.add_argument('video'); e.add_argument('--title'); e.add_argument('--desc-file'); e.add_argument('--tags'); e.add_argument('--thumb'); e.add_argument('--when'); e.add_argument('--now', action='store_true')
    sub.add_parser('list'); sub.add_parser('comments'); rp = sub.add_parser('reply'); rp.add_argument('comment'); rp.add_argument('text'); a = ap.parse_args()
    if a.cmd == 'reel': reel(a.folder, a.when, a.now)
    elif a.cmd == 'edit': edit(a.video, a.title, a.desc_file, a.tags, a.thumb, a.when, a.now)
    elif a.cmd == 'list': listing()
    elif a.cmd == 'comments': comments()
    elif a.cmd == 'reply': reply(a.comment, a.text)
    else: ap.print_help()
