"""Lay the Mirror Rules lines on the timeline (gap before each line); write layout.json and words.json ([word, start, end, other_speaker]).
Lines without a recording yet get an estimated length (narration at 1.5x speaks about 4.4 words a second), so the scene can be built
before the voices exist; run again once they do (after trw.py has written raw_words.json)."""
import json, os
TXT = {l.split(None, 2)[0]: l.split(None, 2)[2].strip() for l in open('../script.txt') if l[:1] == 'm' and l[1:3].isdigit()}
W = json.load(open('raw_words.json')) if os.path.exists('raw_words.json') else {}
def words(name):
    if name in W:
        ws = W[name]; sw = TXT[name].split()
        return [[sw[i], a, b] for i, (w, a, b) in enumerate(ws)] if len(sw) == len(ws) else ws   # the script's own words when the count matches
    ws = TXT[name].split(); d = len(ws) / 4.4; return [[w, round(i * d / len(ws), 2), round((i + .85) * d / len(ws), 2)] for i, w in enumerate(ws)]
# the gaps carry the picture: m05 follows the dark (only the brushing sound), m07 is followed by her blink and the cut back to the start
ORDER = [('m01', .3), ('m02', .9), ('m03', .9), ('m04', 1.0), ('m05', 2.2), ('m06', .9), ('m07', 1.1)]
t = 0; lay = []; out = []
for name, gap in ORDER:
    t += gap; ws = words(name); en = ws[-1][2] + .12
    lay.append(dict(name=name, start=round(t, 2), end=round(t + en, 2), offset=round(t, 2), audio=name))
    for w, a, b in ws: out.append([w, round(a + t, 2), round(b + t, 2), False])
    t += en
END = round(t + 1.3, 1)
lay.append(dict(name='END', start=END, end=END, offset=END))
json.dump(lay, open('layout.json', 'w'), indent=1); json.dump(out, open('words.json', 'w'))
print(' '.join(f"{l['name']}:{l['start']}-{l['end']}" for l in lay))
