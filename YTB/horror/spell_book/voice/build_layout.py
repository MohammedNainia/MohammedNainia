"""Lay the Spell Book voice lines on the reel timeline (gap before each line); write layout.json and words.json.
words.json: [word, start, end, other_speaker]. Voices are the 1.5x .wav files (Gran 1.2x, Mum reversed at 1x)."""
import json
W = json.load(open('raw_words.json'))
ORDER = [('h01', .3), ('h02', .6), ('h03', .3), ('h04', .5), ('h05', .4), ('h06', 1.6), ('h07', .4), ('h08', .4), ('h09', .5),
         ('h10', .4), ('h11', .4), ('g01', .5), ('h12', .2), ('h13', .4), ('g02', .3), ('h14', .3), ('h14b', .4), ('h15', .4),
         ('h16', 1.6), ('h17', .4), ('h18', .3), ('h19', .5), ('m01', .7)]
t = 0; lay = []; words = []
for name, gap in ORDER:
    t += gap; ws = W[name]; en = ws[-1][2] + .12
    lay.append(dict(name=name, start=round(t, 2), end=round(t + en, 2), offset=round(t, 2)))
    for w, a, b in ws: words.append([w, round(a + t, 2), round(b + t, 2), name[0] != 'h'])
    t += en
END = round(t + 3.2, 1)          # the slow push-in on Haru's face, hands over her mouth
lay.append(dict(name='END', start=END, end=END, offset=END))
json.dump(lay, open('layout.json', 'w'), indent=1); json.dump(words, open('words.json', 'w'))
print(' '.join(f"{l['name']}:{l['start']}-{l['end']}" for l in lay)); print('END', END)
