import json
W=json.load(open('cut_words.json'))
# (name, gap before). Other voices: m=Mum, k=Kenji, km=Kenji's mother, nb=neighbour
ORDER=[('n01',.3),('n02',1.0),('n03',.35),('n04',.4),('n05',.35),('n06',1.1),('m1',.25),
 ('n07',.9),('n09',.35),('n10',.45),('n11',.4),
 ('n12',.8),('k1',.3),('n13',.35),('n14',.7),('n15',.9),('n16',.4),('n18',.5),('km1',.35),('n19',.6),
 ('n20',.8),('n21',.4),
 ('n22',.8),('n23',.35),('n24',.8),('n25',.35),('m2',.4),('n26',.5),
 ('n27',1.2),('n28',.45),('n29',.45),('nb1',.3),('n30',.5),('n31',.5),('n32',.6),('n33',.35)]
t=0; lay=[]; words=[]
for name,gap in ORDER:
    t+=gap; ws=W[name]; st=ws[0][1]; en=ws[-1][2]
    off=round(t-st,2); lay.append(dict(name=name,start=round(t,2),end=round(t+en-st,2),offset=off))
    oth=name[0] in 'mk' or name.startswith('nb')
    for w,a,b in ws: words.append([w,round(a+off,2),round(b+off,2),oth])
    t+=en-st
END=round(t+7.5,1)        # after the scream: darkness, the shadow, doors closing, then the loop
json.dump(lay,open('layout.json','w'),indent=1); json.dump(words,open('words.json','w'))
print(', '.join(f"{l['name']}:{l['start']}-{l['end']}" for l in lay)); print('END',END)
