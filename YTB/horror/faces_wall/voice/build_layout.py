"""Lay the Faces on the Wall lines on the timeline (gap before each line); write layout.json and words.json ([word, start, end, other_speaker])."""
import json
W = json.load(open('raw_words.json'))
ORDER = [('h01', .3), ('h02', .5), ('h03', .4), ('k01', .4), ('h04', 1.0), ('h05', .5), ('h06', .5), ('h07', 1.2), ('h08', .3), ('h09', .9),
         ('h10', 1.4), ('h11', .5), ('h12', .9), ('x01', .6), ('h13', 1.0), ('h14', .4), ('h15', .9), ('x02', .3), ('h16', 1.0), ('h17', .7), ('h18', .6)]
t = 0; lay = []; words = []
for name, gap in ORDER:
    t += gap; ws = W[name]; en = ws[-1][2] + .12
    lay.append(dict(name=name, start=round(t, 2), end=round(t + en, 2), offset=round(t, 2)))
    for w, a, b in ws: words.append([w, round(a + t, 2), round(b + t, 2), name[0] != 'h'])
    t += en
END = round(t + 3.4, 1)
lay.append(dict(name='END', start=END, end=END, offset=END))
json.dump(lay, open('layout.json', 'w'), indent=1); json.dump(words, open('words.json', 'w'))
print(' '.join(f"{l['name']}:{l['start']}-{l['end']}" for l in lay))
