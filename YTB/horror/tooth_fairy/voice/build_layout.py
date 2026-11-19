import json
W=json.load(open('raw_words.json'))
for ws in W['h09']:
    if ws[0].lower()=='whole': ws[0]='hall'
# (name, gap before). m = Mum, c = the creature. Gaps leave room for the picture beats.
ORDER=[('h01',.3),('h02',1.0),('m01',.45),('h03',1.1),('h04',.8),('h05',.35),
 ('h06',1.4),('h07',1.0),('h08',1.1),('h09',2.6),('h10',.9),('h11',1.2),('c01',2.2),('h12',8.2)]
t=0; lay=[]; words=[]
for name,gap in ORDER:
    t+=gap; ws=W[name]; st=ws[0][1]; en=ws[-1][2]
    off=round(t-st,2); lay.append(dict(name=name,start=round(t,2),end=round(t+en-st,2),offset=off))
    for w,a,b in ws: words.append([w,round(a+off,2),round(b+off,2),name[0] in 'mc'])
    t+=en-st
END=round(t+4.5,1)          # Mum sets a glass by Haru's bed, then the loop
json.dump(lay,open('layout.json','w'),indent=1); json.dump(words,open('words.json','w'))
print(', '.join(f"{l['name']}:{l['start']}-{l['end']}" for l in lay)); print('END',END)
