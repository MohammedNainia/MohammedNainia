"""Headless: rebuild Haru (with strand hair), stage, set up test 2, render check stills, save the .blend.
blender -b -P make_test2.py -- [--stills] [--frames 13,103,187] [--no-save]
"""
import bpy, os, sys, math, json

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
B = {'__name__': 'haru_build', '__file__': os.path.join(HERE, 'build_haru.py')}
exec(compile(open(B['__file__']).read(), B['__file__'], 'exec'), B)
T = {'__name__': 'haru_t2'}
exec(compile(open(os.path.join(HERE, 'test2_shot.py')).read(), 'test2_shot.py', 'exec'), T)

info = B['build']()
B['stage'](64, width=8.0)
info['shot'] = T['setup'](B, os.path.join(HERE, 'renders', 'test2'))
sc = bpy.context.scene

if '--stills' in args:
    frames = [int(x) for x in args[args.index('--frames') + 1].split(',')] if '--frames' in args else [13, 103, 187]
    keep = (sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples)
    w, h = (int(v) for v in args[args.index('--res') + 1].split(',')) if '--res' in args else (540, 960)
    sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples = w, h, 48
    out = os.path.join(HERE, 'renders', 'hair_check')
    for f in frames:
        sc.frame_set(f); sc.render.filepath = os.path.join(out, f'f{f:03d}.png'); bpy.ops.render.render(write_still=True)
    sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples = keep

sc.frame_set(1)
sc.render.filepath = os.path.join(HERE, 'renders', 'test2', 'f_')
if '--no-save' not in args:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'haru_test2.blend'))
print('RESULT', json.dumps(info, default=str))
