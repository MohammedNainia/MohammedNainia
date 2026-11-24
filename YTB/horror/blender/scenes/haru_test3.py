"""Test 3: the clay puppet does the test-2 story on a tabletop (17 s, 204 frames at 12 fps, stop motion).
Asleep on the floor -> wakes -> sits up, looks around -> hugs her knees -> crouches -> stands -> walks, glances
back -> runs -> stops, turns to us -> camera zooms to her face -> 9 expressions -> pulls out -> jumps, arms up.

The story (poses, timing, speed, faces) comes from haru/test2_shot.py, scaled to the 12.6 cm puppet (x0.1).
Every frame is keyed (CONSTANT), with hand-placement boil on the root, chatter on the joints, a +-1.2% key-light
flicker, and every pose put exactly on the floor.
blender -b -P scenes/haru_test3.py -- [--still F] [--range A B] [--res 1080 1920] [--samples 64] [--out DIR]
"""
import bpy, sys, os, math, random, importlib.util
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
import haru_puppet as HP
from claylib import *
spec = importlib.util.spec_from_file_location('story', os.path.join(HERE, '..', 'haru', 'test2_shot.py'))
ST = importlib.util.module_from_spec(spec); spec.loader.exec_module(ST)

OPTS = cli('haru_test3')
FPS = 12; F = int(ST.END * FPS)                      # 204 frames
reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=F)
HP.fast_cycles(sc)
world((0.6, 0.6, 0.62), 0.2)
sc.view_settings.exposure = -0.6
S = HP.S

# ------------------------------------------------------------------ set: a tabletop seamless, wide enough to run across
import bmesh
bm = bmesh.new(); prof = [(-0.45, 0.0)]
for i in range(13):
    a = math.pi / 2 * i / 12; prof.append((0.12 + math.sin(a) * 0.15, 0.15 - math.cos(a) * 0.15))
prof.append((0.27, 0.6))
rows = [[bm.verts.new((x, y, z)) for y, z in prof] for x in (-0.9, 0.9)]
for i in range(len(prof) - 1): bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
me = bpy.data.meshes.new('sweep'); bm.to_mesh(me); bm.free()
bd = bpy.data.objects.new('sweep', me); bpy.context.collection.objects.link(bd); smooth(bd)
import clay_v3 as CV
assign(bd, CV.clay('sweep', '#cfccc6', rough=0.9, bump=0.25, prints=0.3, specks=0.6, film=0.05))
HP.colliders().objects.link(bd)

h = HP.Haru(loc=(ST.X0 * S, 0, 0), yaw=math.radians(90))
# key and fill sit in front of the action (toward the camera) so the floor near the lens is lit too
key_l = area_light('key', (-0.42, -0.5, 0.32), (0, 0, 0.05), 12, 0.2, (1.0, 0.94, 0.86))
lights = [key_l, area_light('fill', (0.45, -0.55, 0.2), (0, 0, 0.05), 1.4, 0.5, (0.8, 0.88, 1.0)),
          area_light('rim', (0.2, 0.4, 0.32), (0, 0, 0.09), 4.5, 0.2, (1.0, 0.97, 0.92))]
rig = empty('light_rig')                              # the lights travel with the camera so she stays lit
for l in lights: parent(l, rig)
cam = camera((0, -0.245, 0.08), (0, 0, 0.062), lens=32, fstop=4.0)
cam.data.clip_start = 0.005          # tabletop scale: the default 10 cm near clip cuts away the floor in front of the lens

# ------------------------------------------------------------------ animation
boil = Boil(5, amp=0.0002, rot=0.004)
chat = random.Random(7)
x = ST.X0; phase = 0.0; prev = 0.0; cx = None
for f in range(1, F + 1):
    t = (f - 1) / FPS; dt = t - prev; prev = t
    x += ST.speed(t) * dt
    phase += dt / (ST.RUN_T if t >= 7.15 else ST.WALK_T)
    body, lift, facing = ST.body(t, phase)
    body = ST.add(body, {(b, a): chat.uniform(-ST.CHATTER, ST.CHATTER) for b in ST.CHATTER_BONES for a in ('x', 'z')})
    h.place(loc=(x * S, 0, 0), yaw=math.radians(facing)); h.pose(body); h.ground(lift=lift * S)
    j, je = boil.v(), boil.e()
    h.root.location += j; h.root.rotation_euler = (je.x, je.y, h.yaw + je.z)
    (a, b, tb), bl = ST.face(t)
    h.expr(b if (b and tb >= 0.5) else a, blink=bl >= 0.9)
    h.key(f)

    # camera: tracks her across the table (low while she is on the floor), zooms to her face, pulls out to jump
    bpy.context.view_layer.update()
    head = h.P['head'].matrix_world.translation + Vector((0, 0, 0.008))
    lead = -0.12 * (1 - ST.seg(t, 1.3, 2.1)) + 0.22 * ST.speed(t)
    target_x = (x + lead) * S
    cx = target_x if cx is None else cx + (target_x - cx) * 0.45
    zoom = ST.seg(t, 10.1, 11.3) - ST.seg(t, 15.35, 15.75)
    low = 1 - ST.seg(t, 1.6, 4.4)
    wide_loc = Vector((cx, -0.245, 0.08 - 0.03 * low)); wide_tgt = Vector((cx, 0, 0.062 - 0.037 * low))
    close_loc = Vector((head.x, -0.19, head.z + 0.003)); close_tgt = Vector((head.x, 0, head.z + 0.001))
    loc = wide_loc.lerp(close_loc, zoom); tgt = wide_tgt.lerp(close_tgt, zoom)
    cam.location = loc; look_at(cam, tgt); key(cam, f, loc=tuple(cam.location), rot=tuple(cam.rotation_euler))
    cam.data.lens = 32 + (85 - 32) * zoom; cam.data.keyframe_insert('lens', frame=f)
    focus_pt = head if (zoom > 0.3 or t > 1.6) else Vector((x * S, 0, 0.02))
    cam.data.dof.focus_distance = (loc - focus_pt).length; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    cam.data.dof.aperture_fstop = 4.0 + 7.0 * zoom; cam.data.dof.keyframe_insert('aperture_fstop', frame=f)
    key(rig, f, loc=(cam.location.x if t < 10.1 else x * S, 0, 0))
    key_l.data.energy = 12 * (1 + boil.r.uniform(-0.012, 0.012)); key_l.data.keyframe_insert('energy', frame=f)

constant_interp()
run(sc, OPTS)
