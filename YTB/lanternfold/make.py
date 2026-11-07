"""Lanternfold reel pipeline.
  python make.py reels/<reel> frames 6 14 23   -> style frames at story seconds (before voice exists, story time = video time)
  python make.py reels/<reel> timing           -> place voice lines (voice/line1..N.mp3), build time map
  python make.py reels/<reel> ambience         -> wind + chimes bed
  python make.py reels/<reel> render [workers] -> parallel, resumable master render
  python make.py reels/<reel> finalize         -> captions + mix + 1080x1920 + 720p preview
  python make.py reels/<reel> all              -> timing, ambience, render, finalize"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.reel import Reel
from engine import timing, ambience, render, finalize

if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(__doc__)
    reel, step, args = Reel(sys.argv[1]), sys.argv[2], sys.argv[3:]
    if step == 'frames':
        from PIL import Image
        sc = reel.scene(); os.makedirs(reel.path('style'), exist_ok=True)
        for i, t in enumerate(args, 1):
            Image.fromarray(sc.frame(float(t))).save(reel.path('style', f'style_frame_{i}_{t}s.png')); print('  style frame', t)
    elif step == 'timing': timing.run(reel)
    elif step == 'ambience': ambience.run(reel)
    elif step == 'render': render.run(reel, int(args[0]) if args else None)
    elif step == 'finalize': finalize.run(reel)
    elif step == 'all':
        timing.run(reel); ambience.run(reel); render.run(reel, int(args[0]) if args else None); finalize.run(reel)
    else: sys.exit(__doc__)
