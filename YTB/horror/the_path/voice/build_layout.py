import json
W=json.load(open('cut_words.json'))
# fixes
W['n25']=[(('Forty-one' if w=='41' else w),a,b) for w,a,b in W['n25']]
W['n17']=[(w.replace('–','').strip() or None,a,b) for w,a,b in W['n17']]; W['n17']=[x for x in W['n17'] if x[0]]
W['n17']=[(('day,' if w=='day' else w),a,b) for w,a,b in W['n17']]
# order with the gap BEFORE each line (seconds)
ORDER=[('n01',.4),('n02',1.2),('n03',.6),('n04',.6),('n05',.8),('n06',1.8),('n07',.9),('n08',.7),
 ('n09',1.4),('s1',1.2),('n10',.8),('n11',.5),('n12',.7),('n13',1.2),('n14',1.3),('n15',.6),
 ('n17',.5),('n18',.6),('a1',.4),('n19',.5),('n20',.6),('n21',.6),
 ('n22',1.4),('n23',.5),('n24',.6),('s2',.8),
 ('n25',1.2),('n26',.6),('n27',.7),('n28',.6),('n29',1.2),('n30',1.2),('n32',.9),('n33',.9),('s3',.9),('n34',.4),
 ('n35',1.2),('n36',1.0),('n37',1.2),('n38',1.2),('n39',1.2),('s4',3.2)]
GS=0.55
t=0; lay=[]; words=[]
for name,gap in ORDER:
    t+=(gap if gap>=1.6 else gap*GS); ws=W[name]; st=ws[0][1]; en=ws[-1][2]
    off=round(t-st,2); lay.append(dict(name=name,start=round(t,2),end=round(t+en-st,2),offset=off))
    oth=name[0] in 'sa'
    for w,a,b in ws: words.append([w,round(a+off,2),round(b+off,2),oth])
    t+=en-st
END=round(t+1.2,1)
json.dump(lay,open('layout.json','w'),indent=1); json.dump(words,open('words.json','w'))
for l in lay: print(l['name'],l['start'],l['end'])
print('END',END)
