import json,sys,subprocess,numpy as np
def A(f): return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',f,'-ac','1','-ar','16000','-f','f32le','-'],capture_output=True).stdout,np.float32)
from faster_whisper import WhisperModel
m=WhisperModel('small.en',compute_type='int8')
out={}
for n in sys.argv[1:]:
    segs,_=m.transcribe(A(n+".wav"),word_timestamps=True,vad_filter=False)
    ws=[(w.word.strip(),round(w.start,2),round(w.end,2)) for s in segs for w in s.words]
    out[n]=ws; print(n, ws[0][1] if ws else None, ws[-1][2] if ws else None, ' '.join(w[0] for w in ws))
json.dump(out,open('raw_words.json','w'))
