# compress long pauses inside each line (keeps her pace, removes dead air) -> c/<name>.wav + cut_words.json
import json, subprocess, numpy as np, wave, os
SR=48000; CAP=.34; os.makedirs('c',exist_ok=True)
W=json.load(open('raw_words.json')); out={}
def load(p): return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout,np.float32)
for n,ws in W.items():
    x=load(n+'.mp3'); keep=[]; shift=[0.0]*len(ws); cut=0.0; segs=[]; pos=0.0
    for i in range(1,len(ws)):
        a,b=ws[i-1][2],ws[i][1]; g=b-a
        if g>CAP:
            c0=a+(g-CAP)*.35+.08; c1=c0+(g-CAP)       # remove a chunk from inside the pause
            segs.append((pos,c0)); pos=c1; cut+=g-CAP
        shift[i]=cut
    segs.append((pos,ws[-1][2]+(0 if n=='n33' else .35)))
    y=np.concatenate([x[int(s*SR):int(e*SR)] for s,e in segs])
    with wave.open(f'c/{n}.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y,-1,1)*32767).astype('<i2').tobytes())
    out[n]=[(w_,round(a-shift[i],2),round(b-shift[i],2)) for i,(w_,a,b) in enumerate(ws)]
json.dump(out,open('cut_words.json','w'))
