"""Lanternfold reel pipeline.
  python make.py reels/<reel> frames 6 14 23   -> style frames at story seconds (before voice exists, story time = video time)
  python make.py reels/<reel> timing           -> place voice lines (voice/line1..N.mp3), build time map
  python make.py reels/<reel> ambience         -> wind + chimes bed
  python make.py reels/<reel> render [workers] -> parallel, resumable master render
  python make.py reels/<reel> finalize         -> captions + mix + 1080x1920 + 720p preview
  python make.py reels/<reel> all              -> timing, ambience, render, finalize
  python make.py reels/<reel> thumb            -> cover image from reel.json 'thumb' {t, text, size, y}
  python make.py styles reels/<reel> <sec>     -> that frame in every art style
  python make.py envs                          -> preview every environment preset"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.reel import Reel
from engine import timing, ambience, render, finalize, thumbnail

def style_preview(reel_dir, t):
    """python make.py styles reels/<reel> <story sec> -> styles_preview.png (that frame in every art style)"""
    from PIL import Image, ImageDraw, ImageFont; from engine.styles import stylize, STYLES; from engine.config import FONT
    fr = Reel(reel_dir).scene().frame(float(t)); f = ImageFont.truetype(FONT, 30); sheet = Image.new('RGB', (300 * len(STYLES), 533))
    for i, s in enumerate(STYLES):
        im = Image.fromarray(stylize(fr, s, float(t))).resize((300, 533)); d = ImageDraw.Draw(im)
        d.rectangle([0, 490, 300, 533], fill=(0, 0, 0)); d.text((10, 494), s.replace('_', ' '), font=f, fill=(255, 255, 255)); sheet.paste(im, (i * 300, 0))
    sheet.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'styles_preview.png')); print('  styles_preview.png')

def env_preview():
    """python make.py envs -> environments_preview.png (every preset with a stand-in figure)"""
    import numpy as np; from PIL import Image
    from engine import paper as P; from engine.environments import ENVS, draw_env
    tiles = []
    for name, env in ENVS.items():
        cam = P.Cam(1.0, (540., 1000.)); img = P.sky(); L = np.zeros((P.H, P.W, 3), np.float32); P.set_reveal(1.0)
        g = draw_env(img, L, cam, 3.0, env); T, z = cam.f(1.0); fi, d = P.new_fig_layer()
        P.person(d, T, z, 540, g(540) + 3, 150, kind='adult', arm=(.22, .4)); P.composite_fig(img, fi)
        im = Image.fromarray(P.finish(img, L)).resize((270, 480)); tiles.append(im); print('  env', name)
    sheet = Image.new('RGB', (270 * 4, 480 * ((len(tiles) + 3) // 4)))
    for i, im in enumerate(tiles): sheet.paste(im, (i % 4 * 270, i // 4 * 480))
    sheet.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'environments_preview.png'))

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'envs': env_preview(); sys.exit()
    if len(sys.argv) == 4 and sys.argv[1] == 'styles': style_preview(sys.argv[2], sys.argv[3]); sys.exit()
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
    elif step == 'thumb': thumbnail.run(reel)
    elif step == 'all':
        timing.run(reel); ambience.run(reel); render.run(reel, int(args[0]) if args else None); finalize.run(reel)
    else: sys.exit(__doc__)
