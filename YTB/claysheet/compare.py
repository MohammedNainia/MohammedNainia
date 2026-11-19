"""python compare.py REF.json OURS.json  -> a table of every measurement (fractions of total height) and the gap"""
import json, sys
r, o = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
print(f"{'part':16}{'sheet':>8}{'ours':>8}{'diff':>8}")
bad = 0
for k in r:
    if k == 'height_px' or r[k] is None or o.get(k) is None: continue
    d = o[k] - r[k]; bad += abs(d) > .02
    print(f"{k:16}{r[k]:8.3f}{o[k]:8.3f}{d:+8.3f}{'  <<' if abs(d) > .02 else ''}")
print('parts off by more than 2%:', bad)
