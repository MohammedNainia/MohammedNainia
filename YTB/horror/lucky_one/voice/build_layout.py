"""Lay the Lucky One lines on the timeline (gap before each line); write layout.json and words.json ([word, start, end, other_speaker])."""
import json, subprocess
W = json.load(open('raw_words.json'))
dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', 't01.wav']))
W['t01'] = [[w, round(i * dur / 4, 2), round((i + 1) * dur / 4 - .1, 2)] for i, w in enumerate(["Hhhrrr...", "vaak'thu...", "nnhesk...", "drrah."])]
ORDER = [('h01', .3), ('h02', 1.0), ('h03', .6), ('w01', .7), ('h04', .6), ('h05', 1.0), ('h06', .9), ('h07', .9), ('h08', 1.2), ('h09', 1.2),
         ('h10', 1.4), ('w02', .8), ('h11', 1.0), ('h12', 1.4), ('h13', 1.6), ('t01', 1.6), ('h14', .8), ('h15', 1.0)]
t = 0; lay = []; words = []
for name, gap in ORDER:
    t += gap; ws = W[name]; en = dur if name == 't01' else ws[-1][2] + .12
    lay.append(dict(name=name, start=round(t, 2), end=round(t + en, 2), offset=round(t, 2)))
    for w, a, b in ws: words.append([w, round(a + t, 2), round(b + t, 2), name[0] != 'h'])
    t += en
END = round(t + 3.4, 1)
lay.append(dict(name='END', start=END, end=END, offset=END))
json.dump(lay, open('layout.json', 'w'), indent=1); json.dump(words, open('words.json', 'w'))
print(' '.join(f"{l['name']}:{l['start']}-{l['end']}" for l in lay))
