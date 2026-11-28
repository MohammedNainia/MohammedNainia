"""Lay the Sector B13 lines on the timeline; write layout.json and words.json ([word, start, end, other_speaker]).
Lines are the trimmed .wav files in this folder: Haru (Samara X, Eleven v3, stability 0.5) at 1.5x, Mika (Candid, British)
at 1.25x, the creature (Mika's voice) at 1.0x. Word timings come from raw_words.json (faster-whisper, tools/trw.py); the
script's own words replace Whisper's spelling when the word counts match. The scene's shot map (scenes/sector_b13.py T)
follows these start times.
The .wav files are made from the Artlist .mp3s (silence trimmed, then sped up):
  ffmpeg -i n1.mp3 -af "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,
         silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse,atempo=1.5" -ar 48000 -ac 1 n1.wav
  (atempo 1.5 for n1-n7, 1.25 for m1, 1.0 for c1). voice_preview.mp3 is all lines on the timeline, voice only."""
import json, wave
TXT = dict(
    n1="Three of us went camping. I'm the only one still in the tent.",
    n2="It was the best night. Fire, stupid stories, Mika burning every marshmallow.",
    n3="On the walk in, we passed a fence. Sector B13. And the gate was open.",
    n4="At three, Jun screamed. Then Mika. Then nothing.",
    m1="Haru? It's okay. It's gone. You can come out now.",
    n5="I didn't answer. Mika was the second one who screamed.",
    n6="I didn't say a word. All night.",
    n7="At sunrise, two people in grey suits walked it back behind the fence. Like a dog.",
    c1="Bye, Haru.",
)
START = dict(n1=0.3, n2=4.3, n3=10.1, n4=15.3, m1=23.9, n5=28.4, n6=32.9, n7=35.9, c1=41.9)   # seconds into the reel
W = json.load(open('raw_words.json'))


def dur(n):
    w = wave.open(n + '.wav'); return w.getnframes() / w.getframerate()


lay, out = [], []
for n, t in sorted(START.items(), key=lambda kv: kv[1]):
    ws = W[n]; sw = TXT[n].split()
    fixed = []
    for w, a, b in ws:                                              # Whisper hears "a fence" as "offence"
        if w.lower().strip(',.') == 'offence': m = round((a + b) / 2, 2); fixed += [['a', a, m], ['fence.', m, b]]
        else: fixed.append([w, a, b])
    ws = fixed
    if len(sw) == len(ws): ws = [[sw[i], a, b] for i, (_, a, b) in enumerate(ws)]
    else: print('WORDS differ', n, len(sw), len(ws))
    lay.append(dict(name=n, start=t, end=round(t + dur(n), 2), offset=t, audio=n))
    for w, a, b in ws: out.append([w, round(a + t, 2), round(b + t, 2), n[0] != 'n'])
lay.append(dict(name='END', start=44.0, end=44.0, offset=44.0))
json.dump(lay, open('layout.json', 'w'), indent=1); json.dump(out, open('words.json', 'w'))
print(' '.join(f"{l['name']}:{l['start']}-{l['end']}" for l in lay))
