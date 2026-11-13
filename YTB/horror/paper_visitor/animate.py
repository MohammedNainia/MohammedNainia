"""The Paper Visitor: 20 s test made from the AI stills in stills/, animated in code.
    python animate.py              -> paper_visitor_ai_test.mp4 (1920x1080, 30 fps, with sound)
    python animate.py --preview    -> 960x540 quick version
    python animate.py --frames 60,200,400   -> those frames as PNGs in anim_check/
Motion: slow sub-pixel push-ins, lantern flicker, breathing that stops dead at the footstep,
blink and glance by cross-fading face stills, the drool slowly stretching. Silence except single sounds."""
import os, sys, math, wave, struct, subprocess, random
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.join(HERE, 'stills')
ARGS = sys.argv[1:]; PREVIEW = '--preview' in ARGS
W, H = (960, 540) if PREVIEW else (1920, 1080)
FPS, DUR = 30, 20.0; N = int(FPS * DUR)

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
_cache = {}
def img(name):
    if name not in _cache:
        a = cv2.imread(os.path.join(ST, name), cv2.IMREAD_COLOR).astype(np.float32) / 255.0
        _cache[name] = a
    return _cache[name]

def warm_mask(name):                                   # where the paper lantern light falls (warm and bright): flicker only there
    k = name + ':mask'
    if k not in _cache:
        a = img(name); b, g, r = a[..., 0], a[..., 1], a[..., 2]
        m = np.clip((r - b) * 3.0, 0, 1) * np.clip((r + g) * .8, 0, 1)
        _cache[k] = cv2.GaussianBlur(m, (0, 0), 25)[..., None]
    return _cache[k]

def flicker(t):                                        # smooth candle-like brightness wobble, +-5 %
    return .05 * (math.sin(t * 7.3) * .5 + math.sin(t * 13.1 + 1) * .3 + math.sin(t * 2.9 + 2) * .2)

def blob(shape, cx, cy, sx, sy):                       # gaussian weight in normalised image coords
    h, w = shape[:2]; X, Y = np.meshgrid(np.arange(w) / w, np.arange(h) / h)
    return np.exp(-(((X - cx) / sx) ** 2 + ((Y - cy) / sy) ** 2)).astype(np.float32)

def warp_down(a, weight, px):                          # pull pixels down by px * weight (breathing, drool)
    h, w = a.shape[:2]; X, Y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    return cv2.remap(a, X, Y - px * weight, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def view(a, zoom, cx, cy):                             # sub-pixel crop + resize: smooth push-ins, no jitter
    h, w = a.shape[:2]; s = W / (w / zoom)
    hw, hh = .5 / zoom, .5 * (H / W) * (w / h) / zoom          # keep the crop inside the picture (no mirrored edges)
    cx = min(max(cx, hw), 1 - hw); cy = min(max(cy, hh), 1 - hh)
    M = np.float32([[s, 0, W / 2 - s * cx * w], [0, s, H / 2 - s * cy * h]])
    return cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

# ---------------------------------------------------------------- the shot list (seconds)
# each shot: start, end, stills [(name, from_t, fade)], zoom from -> to, centre from -> to, extra effects
SHOTS = [
    dict(t0=0.0, t1=4.0, stills=[('s1_wide_empty.png', 0, 0)], z=(1.0, 1.05), c=((.52, .55), (.55, .52))),
    dict(t0=4.0, t1=10.0, stills=[('s2_haru_asleep.png', 0, 0), ('s3_haru_eyes_open.png', 5.2, .45), ('s4_haru_glance.png', 7.45, .1)],
         z=(1.0, 1.16), c=((.52, .48), (.52, .42)), breathe=dict(c=(.5, .86), s=(.25, .12), px=7, hz=.42, stop=6.5)),
    dict(t0=10.0, t1=12.3, stills=[('s5_door_gap.png', 0, 0)], z=(1.0, 1.04), c=((.47, .5), (.47, .5))),
    dict(t0=12.3, t1=14.7, stills=[('master_b.png', 0, 0)], z=(1.02, 1.05), c=((.55, .5), (.6, .48))),
    dict(t0=14.7, t1=17.0, stills=[('s7_haru_sitting.png', 0, 0)], z=(1.05, 1.13), c=((.38, .55), (.38, .5)),
         breathe=dict(c=(.38, .78), s=(.12, .1), px=3, hz=1.6, stop=99)),
    dict(t0=17.0, t1=19.4, stills=[('s6_visitor_face.png', 0, 0)], z=(1.0, 1.18), c=((.5, .5), (.5, .55)),
         drool=dict(c=(.53, .78), s=(.025, .08), px=26)),
]

def frame(i):
    t = i / FPS
    shot = next((s for s in SHOTS if s['t0'] <= t < s['t1']), None)
    if shot is None: return np.zeros((H, W, 3), np.float32)
    p = (t - shot['t0']) / (shot['t1'] - shot['t0']); e = ease(p)
    a = None                                           # cross-fade the face stills (blink / glance)
    for name, ft, fade in shot['stills']:
        b = img(name) * (1 + warm_mask(name) * flicker(t))
        if a is None: a = b
        elif t >= ft: k = ease((t - ft) / fade) if fade else 1.0; a = a * (1 - k) + b * k
    if 'breathe' in shot:
        bp = shot['breathe']; amp = 0 if t >= bp['stop'] else (math.sin(2 * math.pi * bp['hz'] * (t - shot['t0'])) * .5 + .5)
        key = 'breath' + str(shot['t0'])
        if key not in _cache: _cache[key] = blob(a.shape, *bp['c'], *bp['s'])
        a = warp_down(a, _cache[key], -bp['px'] * amp)  # chest rises (pixels move up)
    if 'drool' in shot:
        dp = shot['drool']; key = 'drool' + str(shot['t0'])
        if key not in _cache: _cache[key] = blob(a.shape, *dp['c'], *dp['s'])
        a = warp_down(a, _cache[key], dp['px'] * ease(p * 1.1))
    z = shot['z'][0] + (shot['z'][1] - shot['z'][0]) * e
    cx = shot['c'][0][0] + (shot['c'][1][0] - shot['c'][0][0]) * e; cy = shot['c'][0][1] + (shot['c'][1][1] - shot['c'][0][1]) * e
    out = view(a, z, cx, cy)
    if t < .8: out *= ease(t / .8)                     # fade in from black at the very start
    if shot is SHOTS[-1] and p > .9: out *= 1 - ease((p - .9) / .1)
    return np.clip(out, 0, 1)

# ---------------------------------------------------------------- sound: silence, then single sounds
def sound(path):
    sr = 48000; n = int(DUR * sr); s = np.zeros(n, np.float32); rnd = np.random.default_rng(3)
    def add(t0, x): i = int(t0 * sr); s[i:i + len(x)] += x[:n - i]
    tt = np.arange(int(.5 * sr)) / sr                   # one heavy footstep on old wood (6.5 s)
    noise = np.convolve(rnd.uniform(-1, 1, len(tt)), np.ones(40) / 40, 'same')
    add(6.5, .5 * (np.sin(2 * np.pi * (60 + 30 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 13) + 2.2 * noise * np.exp(-((tt - .12) / .06) ** 2)))
    tt = np.arange(int(1.1 * sr)) / sr                  # a slow floorboard creak before the wide reveal (11.9 s)
    f = 180 + 60 * np.sin(tt * 3.0) + 25 * rnd.standard_normal(len(tt)).cumsum() / sr * 40
    ph = 2 * np.pi * np.cumsum(f) / sr
    cr = (np.sign(np.sin(ph)) * .4 + np.sin(ph * 2) * .3) * np.sin(np.pi * tt / tt[-1]) ** 2
    add(11.9, .06 * np.convolve(cr, np.ones(12) / 12, 'same'))
    tt = np.arange(int(1.0 * sr)) / sr                  # a soft dry paper rustle just before its face (16.8 s)
    rs = rnd.uniform(-1, 1, len(tt)) * (rnd.random(len(tt)) > .7) * np.sin(np.pi * tt / tt[-1])
    add(16.8, .05 * rs)
    pcm = (np.clip(s, -1, 1) * 30000).astype('<i2')
    with wave.open(path, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

if __name__ == '__main__':
    if '--frames' in ARGS:
        os.makedirs(os.path.join(HERE, 'anim_check'), exist_ok=True)
        for i in [int(x) for x in ARGS[ARGS.index('--frames') + 1].split(',')]:
            cv2.imwrite(os.path.join(HERE, 'anim_check', f'f{i:04d}.png'), (frame(i) * 255).astype(np.uint8))
        sys.exit()
    wav = os.path.join(HERE, 'paper_visitor_ai_test.wav'); sound(wav)
    out = os.path.join(HERE, 'paper_visitor_ai_test' + ('_preview' if PREVIEW else '') + '.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', wav, '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', out],
                          stdin=subprocess.PIPE)
    for i in range(N):
        ff.stdin.write((frame(i) * 255 + .5).astype(np.uint8).tobytes())
        if i % 60 == 0: print('  frame', i, '/', N, flush=True)
    ff.stdin.close(); ff.wait(); print('saved', out)
