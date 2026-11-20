"""Lay the voice lines out on the reel timeline (gap before each line), write layout.json and words.json.
words.json: [word, start, end, other_speaker]; other = not Haru's narration (seller s, girl g, mum m, walls x)."""
import json
W = json.load(open('raw_words.json'))
# (line, gap before it). The suction after h04 and the fall inside need room: 2.2 s before h05.
ORDER = [('h01', .3), ('h02', .9), ('s01', .35), ('h02b', .8), ('h03', .7), ('h04', .5), ('h05', 2.4), ('h06', .7), ('h06b', .25),
         ('h07', .8), ('h08', .8), ('h09', .8), ('x01', .2), ('h10', .9), ('h11', .5), ('g01', .7), ('h12', 1.4), ('m01', .4),
         ('h13', 1.0), ('g02', .45)]
DUR = {'x01': 4.9}
t = 0; lay = []; words = []
for name, gap in ORDER:
    t += gap; ws = W[name]; en = DUR.get(name, ws[-1][2] + .15)
    lay.append(dict(name=name, start=round(t, 2), end=round(t + en, 2), offset=round(t, 2)))
    for w, a, b in ws: words.append([w, round(a + t, 2), round(b + t, 2), name[0] != 'h'])
    t += en
END = round(t + 1.6, 1)
json.dump(lay, open('layout.json', 'w'), indent=1); json.dump(words, open('words.json', 'w'))
print(' '.join(f"{l['name']}:{l['start']}-{l['end']}" for l in lay)); print('END', END)
