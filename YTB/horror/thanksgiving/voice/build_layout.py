import json, subprocess
W = json.load(open('raw_words.json'))
for ws in W['h02']:
    if ws[0].lower().startswith('thanksgiving'): ws[0] = 'Thanksgiving,'
for ws in W['p01']: ws[0] = ws[0].replace('"', '')
for ws in W['h02b']: ws[0] = ws[0].replace('rule.', 'rule:')
for ws in W['g03']: ws[0] = ws[0].replace('ready', 'ready.')
dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', 't01_trim.wav']))
tw = ["Hhhrrr...", "khvetsk'a...", "t'qhul...", "mnaaah?"]
W['t01'] = [[w, round(i * dur / 4, 2), round((i + 1) * dur / 4 - .1, 2)] for i, w in enumerate(tw)]
W['x01'] = [];  W['g04'] = W['g01']
# (name, gap before). g = Grandma, p = Grandpa, t = the thing (dead language), x = muffled scream (no caption)
ORDER = [('h01', .3), ('h02', 1.0), ('h02b', .45), ('g01', .45), ('h03', .5), ('h03b', .8), ('h04', .5), ('p01', 1.3),
         ('h05', 1.1), ('h06', .9), ('g02', .5), ('h07', 1.1), ('h08', .5), ('h09', 1.1), ('t01', .6), ('g03', .35),
         ('x01', 1.0), ('h10', 4.2), ('g04', 2.2)]
t = 0; lay = []; words = []
for name, gap in ORDER:
    t += gap
    if name == 'x01': lay.append(dict(name=name, start=round(t, 2), end=round(t + 3, 2), offset=round(t, 2))); continue
    ws = W[name]; st = ws[0][1]; en = ws[-1][2]
    if name == 't01': en = dur
    off = round(t - st, 2); lay.append(dict(name=name, start=round(t, 2), end=round(t + en - st, 2), offset=off))
    for w, a, b in ws: words.append([w, round(a + off, 2), round(b + off, 2), name[0] in 'gpt'])
    t += en - st
END = round(t + 2.6, 1)
json.dump(lay, open('layout.json', 'w'), indent=1); json.dump(words, open('words.json', 'w'))
print(', '.join(f"{l['name']}:{l['start']}-{l['end']}" for l in lay)); print('END', END)
