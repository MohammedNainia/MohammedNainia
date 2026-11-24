"""Render-speed benchmark: clay Haru walks across the tabletop for 2 s (24 frames at 12 fps), 9:16.
blender -b -P scenes/haru_bench.py -- --res 1080 1920 --samples 64 --out renders/bench [--fast]
--fast: the tuned settings (adaptive threshold 0.03, 4 bounces, no caustics, light tree, OIDN on GPU).
Each frame's time is printed by Blender ("Time: ..."); the script also prints AVG per frame at the end.
"""
import bpy, sys, os, math, time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
FAST = '--fast' in sys.argv
if FAST: sys.argv.remove('--fast')
import haru_puppet as HP
from claylib import *

OPTS = cli('bench')
reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=24)
world((0.6, 0.6, 0.62), 0.2)
sc.view_settings.exposure = -0.6
if FAST:
    c = sc.cycles
    c.adaptive_threshold = 0.03; c.adaptive_min_samples = 16
    c.max_bounces = 4; c.diffuse_bounces = 2; c.glossy_bounces = 2; c.transmission_bounces = 2
    c.transparent_max_bounces = 4; c.volume_bounces = 0
    c.use_light_tree = True; c.sample_clamp_indirect = 4.0
    try: c.denoising_use_gpu = True
    except AttributeError: pass

import bmesh
bm = bmesh.new(); prof = [(-0.7, 0.0)]
for i in range(13):
    a = math.pi / 2 * i / 12; prof.append((0.15 + math.sin(a) * 0.15, 0.15 - math.cos(a) * 0.15))
prof.append((0.3, 0.6))
rows = [[bm.verts.new((x, y, z)) for y, z in prof] for x in (-0.8, 0.8)]
for i in range(len(prof) - 1): bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
me = bpy.data.meshes.new('sweep'); bm.to_mesh(me); bm.free()
bd = bpy.data.objects.new('sweep', me); bpy.context.collection.objects.link(bd); smooth(bd)
assign(bd, clay('sweep', (0.62, 0.61, 0.59), rough=0.9, sss=0.0, bump=0.15, thumb=0.1, scale=2.0))
HP.colliders().objects.link(bd)

h = HP.Haru(loc=(-0.05, 0, 0), yaw=math.radians(90))
key_l = area_light('key', (-0.35, -0.42, 0.45), (0, 0, 0.06), 14, 0.35, (1.0, 0.95, 0.88))
area_light('fill', (0.45, -0.3, 0.18), (0, 0, 0.06), 2.0, 0.5, (0.8, 0.88, 1.0))
area_light('rim', (0.15, 0.4, 0.35), (0, 0, 0.09), 4.0, 0.3, (1.0, 0.97, 0.92))
camera((0.0, -0.42, 0.085), (0.0, 0, 0.062), lens=50, fstop=4.0)


def walk(p):
    s, c = math.sin(2 * math.pi * p), math.cos(2 * math.pi * p)
    kl = 6 + 34 * max(0.0, c) ** 1.5; kr = 6 + 34 * max(0.0, -c) ** 1.5
    return {('thigh.L', 'x'): -22 * s, ('thigh.R', 'x'): 22 * s, ('shin.L', 'x'): kl, ('shin.R', 'x'): kr,
            ('foot.L', 'x'): -0.45 * (-22 * s + kl), ('foot.R', 'x'): -0.45 * (22 * s + kr),
            ('upper_arm.L', 'x'): 16 * s, ('upper_arm.R', 'x'): -16 * s, ('forearm.L', 'x'): -12, ('forearm.R', 'x'): -12,
            ('hips', 'z'): 5 * s, ('chest', 'z'): -6 * s, ('hips', 'x'): 3, ('head', 'x'): -2}


boil = Boil(5, amp=0.0002, rot=0.004)
for f in range(1, 25):
    t = (f - 1) / 12
    h.place(loc=(-0.05 + 0.072 * t, 0, 0)); h.pose(walk(t / 1.0)); h.ground()
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, h.yaw + je.z)
    h.expr('worried', blink=f in (15, 16)); h.key(f)
    key_l.data.energy = 14 * (1 + boil.r.uniform(-0.012, 0.012)); key_l.data.keyframe_insert('energy', frame=f)
constant_interp()

t0 = time.time()
run(sc, OPTS)
n = 24 if OPTS['still'] is None else 1
print(f'AVG {(time.time() - t0) / n:.2f} s/frame over {n} frames (fast={FAST})', flush=True)
