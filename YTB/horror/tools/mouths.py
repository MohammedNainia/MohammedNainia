"""Mouth shapes for every voice line of a reel, with Rhubarb Lip Sync (github.com/DanielSWolf/rhubarb-lip-sync).

    python mouths.py VOICE_DIR [--rhubarb PATH]

Reads VOICE_DIR/layout.json (name, offset per line, made by the reel's build_layout.py) and the audio files
VOICE_DIR/<name>.mp3 or .wav. Uses the line's words from VOICE_DIR/raw_words.json as the dialog text when present
(more accurate). Writes VOICE_DIR/mouths.json: {line name: [{start, end, value}] on the reel's timeline}, and one
speaker letter per line (the name's first letter: h Haru, m Mum, g Grandma, p Grandpa...).
In the scene: P.talkCues(cues, t) for the character's lines.
Rhubarb: Windows/Linux/Mac builds on its GitHub releases page; set RHUBARB=path or pass --rhubarb."""
import json, os, subprocess, sys, tempfile

def main():
    vd = sys.argv[1]
    rb = sys.argv[sys.argv.index('--rhubarb') + 1] if '--rhubarb' in sys.argv else os.environ.get('RHUBARB', 'rhubarb')
    lay = json.load(open(os.path.join(vd, 'layout.json')))
    raw = json.load(open(os.path.join(vd, 'raw_words.json'))) if os.path.exists(os.path.join(vd, 'raw_words.json')) else {}
    out = {}
    with tempfile.TemporaryDirectory() as td:
        for L in lay:
            name = L['name']
            src = next((os.path.join(vd, name + e) for e in ('.wav', '.mp3') if os.path.exists(os.path.join(vd, name + e))), None)
            if not src: print('no audio for', name); continue
            wav = os.path.join(td, name + '.wav')
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-ar', '16000', '-ac', '1', wav], check=True)
            cmd = [rb, '-q', '-f', 'json', '-r', 'phonetic', wav]
            if raw.get(name):
                txt = os.path.join(td, name + '.txt'); open(txt, 'w').write(' '.join(w[0] for w in raw[name])); cmd[1:1] = ['--dialogFile', txt]
            cues = json.loads(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout)['mouthCues']
            off = L.get('offset', L['start'])
            out[name] = {'speaker': name[0], 'cues': [{'start': round(c['start'] + off, 3), 'end': round(c['end'] + off, 3), 'value': c['value']} for c in cues]}
            print(f"{name}: {len(cues)} mouth cues")
    json.dump(out, open(os.path.join(vd, 'mouths.json'), 'w'))
    print('wrote', os.path.join(vd, 'mouths.json'))

if __name__ == '__main__':
    main()
