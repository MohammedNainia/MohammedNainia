"""Lay the Pattern lines on the timeline (gap before each line); write layout.json and words.json ([word, start, end, other_speaker]).
x01 (her gasp) has no voice file: post.py makes it; it holds .7 s on the timeline."""
import json
W = json.load(open('raw_words.json'))
W['x01'] = [['(gasp)', 0, .6]]
ORDER = [('h01', .3), ('h02', 1.2), ('g01', .4), ('h03', .6), ('h04', 1.0), ('h05', 1.8), ('h06', 1.6), ('x01', 1.0), ('h07', 1.2), ('h08', 1.2),
         ('g02', 1.4), ('h09', 1.0), ('h10', 1.2), ('h11', 1.0), ('h12', 1.2), ('h13', 1.2), ('h14', 1.4), ('m01', 1.4)]
t = 0; lay = []; words = []
for name, gap in ORDER:
    t += gap; ws = W[name]; en = ws[-1][2] + .12
    lay.append(dict(name=name, start=round(t, 2), end=round(t + en, 2), offset=round(t, 2)))
    if name != 'x01':
        for w, a, b in ws: words.append([w, round(a + t, 2), round(b + t, 2), name[0] != 'h'])
    t += en
END = round(t + 2.2, 1)
lay.append(dict(name='END', start=END, end=END, offset=END))
json.dump(lay, open('layout.json', 'w'), indent=1); json.dump(words, open('words.json', 'w'))
print(' '.join(f"{l['name']}:{l['start']}-{l['end']}" for l in lay))
