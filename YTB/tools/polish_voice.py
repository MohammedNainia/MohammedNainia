"""Make a voice recording sound like a podcast: clean, close, warm and even.
  python polish_voice.py my_voice.wav                 -> my_voice_polished.wav
  python polish_voice.py my_voice.wav --strong        -> heavier noise and breath removal (noisy room / headset mic)
Steps (ffmpeg): rumble cut -> noise reduction -> breath/room gate -> de-ess -> warmth + presence EQ -> compressor -> -16 LUFS.
Use it on the reference clip BEFORE cloning (a cleaner clip gives a cleaner clone) and on generated lines if needed."""
import os, sys, shutil, subprocess

def ffmpeg():
    if os.name == 'nt':     # the user's PC: imageio's ffmpeg if ffmpeg isn't on PATH
        p = shutil.which('ffmpeg')
        if p: return p
        try:
            import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError: sys.exit('ffmpeg not found: run  py -m pip install imageio-ffmpeg')
    return shutil.which('ffmpeg') or 'ffmpeg'

def chain(strong=False):
    nr, gate = (18, -38) if strong else (10, -45)
    return ','.join([
        'highpass=f=80',                                   # cut rumble, desk thumps, mic handling
        'lowpass=f=15000',
        f'afftdn=nr={nr}:nf=-50:tn=1',                     # background hiss / fan noise
        f'agate=threshold={10 ** (gate / 20):.4f}:ratio=3:attack=5:release=180:range=0.25',   # tame breaths between words
        'deesser=i=0.4:f=0.5',                             # soften harsh "s"
        'equalizer=f=180:t=q:w=1:g=2',                     # warmth
        'equalizer=f=400:t=q:w=1.4:g=-2',                  # remove boxiness (headset sound)
        'equalizer=f=3500:t=q:w=1.2:g=3',                  # presence / clarity
        'equalizer=f=10000:t=h:w=2000:g=1.5',              # air
        'acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3',                # even, "close to the mic"
        'loudnorm=I=-16:TP=-1.5:LRA=7',                    # podcast loudness
        'aresample=48000'])

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    src = sys.argv[1]; strong = '--strong' in sys.argv
    base, _ = os.path.splitext(src); out = base + '_polished.wav'
    subprocess.run([ffmpeg(), '-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-af', chain(strong), '-ac', '1', out], check=True)
    print('saved', out)
