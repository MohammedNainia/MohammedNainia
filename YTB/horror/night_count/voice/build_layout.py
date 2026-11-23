"""Lay the Night Count lines on the timeline (gap before each line); write layout.json and words.json ([word, start, end, other_speaker]).
The nurse's question is one recording (n01) used three times (n1a, n1b, n1c). Lines without a recording yet get an estimated length
(narration at 1.5x speaks about 4.4 words a second) so the scene can be built before the voices exist; run again once they do."""
import json, os
TXT = {l.split(None, 2)[0]: l.split(None, 2)[2].split('  (')[0].strip() for l in open('../script.txt') if l[:1] in 'hngd' and l[1:3].isdigit()}
W = json.load(open('raw_words.json')) if os.path.exists('raw_words.json') else {}
W.update({k: v for k, v in json.load(open('raw_words_dialogue.json')).items() if k not in W})
FIX = {'2': 'Two.', '3': 'Three.', 'too.': 'Two.', 'to,': 'two,'}
def words(name):
    src = 'n01' if name.startswith('n1') else name
    if src in W:
        ws = [[FIX.get(w, w), a, b] for w, a, b in W[src]]; sw = TXT[src].split()
        return [[sw[i], a, b] for i, (w, a, b) in enumerate(ws)] if len(sw) == len(ws) else ws   # the script's own words when the count matches
    ws = TXT[src].split(); d = len(ws) / 4.4; return [[w, round(i * d / len(ws), 2), round((i + .85) * d / len(ws), 2)] for i, w in enumerate(ws)]
ORDER = [('h01', .3), ('h02', 1.2), ('n1a', .9), ('g01', .5), ('h03', 1.0), ('h04', 1.0), ('g02', .5), ('h05', 1.6), ('h06', 1.2), ('n1b', 1.2), ('h07', .9),
         ('n02', .9), ('h08', .6), ('h09', 2.0), ('h10', 1.2), ('h11', 1.2), ('n1c', 1.2), ('d01', .8)]
t = 0; lay = []; out = []
for name, gap in ORDER:
    t += gap; ws = words(name); en = ws[-1][2] + .12
    lay.append(dict(name=name, start=round(t, 2), end=round(t + en, 2), offset=round(t, 2), audio='n01' if name.startswith('n1') else name))
    for w, a, b in ws: out.append([w, round(a + t, 2), round(b + t, 2), name[0] != 'h'])
    t += en
END = round(t + 2.0, 1)
lay.append(dict(name='END', start=END, end=END, offset=END))
json.dump(lay, open('layout.json', 'w'), indent=1); json.dump(out, open('words.json', 'w'))
print(' '.join(f"{l['name']}:{l['start']}-{l['end']}" for l in lay))
