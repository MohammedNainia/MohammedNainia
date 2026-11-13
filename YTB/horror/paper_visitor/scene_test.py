"""The Paper Visitor - 20 s scene test with the MPFB2 characters (needs characters.blend from build_characters.py).
    blender -b -P scene_test.py                 (1920x1080, full quality)
    blender -b -P scene_test.py -- --preview    (960x540, quick)
    blender -b -P scene_test.py -- --frames 31,181,361   (just those frames as PNGs, for checking)
Output: scene_frames[_preview]/ (resumable) and paper_visitor_scene[_preview].mp4 with sound.
Beats: 0-4 asleep, breathing | 4-6 eyes open | 6.5 ONE footstep, breathing stops | 7.5-10 head turns toward the door |
10.2-13 sits up (hand pushes, a held breath, then the rest) | 13-16 frozen | 16-20 the camera finds the Visitor. True silence otherwise."""
import bpy, os, sys, math, wave, struct, random
from mathutils import Vector, Matrix, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW = '--preview' in ARGS
FPS, DUR = 30, 20.0; FRAMES = int(FPS * DUR)
def F(t): return 1 + round(t * FPS)

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'characters.blend'))
scene = bpy.context.scene; scene.render.fps = FPS; scene.frame_start = 1; scene.frame_end = FRAMES
for ob in [o for o in bpy.data.objects if o.type in ('CAMERA', 'LIGHT') or o.name == 'floor']: bpy.data.objects.remove(ob, do_unlink=True)

# ---------------------------------------------------------------- materials + room (paper diorama, muted palette)
def mat(name, rgb, rough=.85, bumpstr=.2, emit=0.0):
    m = bpy.data.materials.new(name); n = m.node_tree.nodes; l = m.node_tree.links; b = n['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    if emit: b.inputs['Emission Color'].default_value = (*rgb, 1); b.inputs['Emission Strength'].default_value = emit
    tc = n.new('ShaderNodeTexCoord'); nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 90; nz.inputs['Detail'].default_value = 8
    l.new(tc.outputs['Object'], nz.inputs['Vector'])
    mix = n.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs['Fac'].default_value = .2; mix.inputs['Color1'].default_value = (*rgb, 1)
    l.new(nz.outputs['Color'], mix.inputs['Color2']); l.new(mix.outputs['Color'], b.inputs['Base Color'])
    bp = n.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bumpstr; bp.inputs['Distance'].default_value = .002
    l.new(nz.outputs['Fac'], bp.inputs['Height']); l.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m
def box(name, x0, x1, y0, y1, z0, z1, m, bevel=0.0, subdiv=0):
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    import bmesh; bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    ob.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); ob.scale = (x1 - x0, y1 - y0, z1 - z0); me.materials.append(m)
    if bevel: md = ob.modifiers.new('bevel', 'BEVEL'); md.width = bevel; md.segments = 4
    if subdiv: md = ob.modifiers.new('sub', 'SUBSURF'); md.levels = md.render_levels = subdiv
    return ob

WALL, WALL2, FLOOR, WOOD = mat('wall', (.20, .14, .11)), mat('plank', (.15, .10, .085)), mat('floor', (.11, .08, .07)), mat('wood', (.25, .13, .08))
SHEET, QUILT, LANTERN = mat('sheet', (.40, .36, .30)), mat('quilt', (.34, .07, .06), bumpstr=.5), mat('lantern', (.62, .50, .34))
VOID = mat('void_room', (0, 0, 0), rough=1); MOONM = mat('moon', (.9, .9, .82), emit=6)
box('floor', -4, 4, -3, 3.2, -.05, 0, FLOOR)
for (x0, x1, z0, z1) in ((-4, -2.25, 0, 3.2), (-1.15, 1.55, 0, 3.2), (2.55, 4, 0, 3.2), (-2.25, -1.15, 0, 1.15), (-2.25, -1.15, 2.25, 3.2), (1.55, 2.55, 2.15, 3.2)):
    box(f'wall_{x0}_{z0}', x0, x1, 2.5, 2.6, z0, z1, WALL)
for i, x in enumerate([-3.6 + .55 * k for k in range(14)]):
    if not (-2.3 < x < -1.1 or 1.5 < x < 2.6): box(f'plank_{i}', x, x + .02, 2.49, 2.5, 0, 3.2, WALL2)
box('sill', -2.3, -1.1, 2.3, 2.62, 1.1, 1.15, WOOD)
for (x0, x1, z0, z1) in ((-2.3, -2.22, 1.15, 2.3), (-1.18, -1.1, 1.15, 2.3), (-2.3, -1.1, 2.22, 2.3), (-1.74, -1.66, 1.15, 2.22), (-2.22, -1.18, 1.68, 1.74)):
    box(f'frame_{x0}_{z0}', x0, x1, 2.52, 2.6, z0, z1, WOOD)
box('night_sky', -3, 0, 4.5, 4.6, 0, 4, mat('night', (.02, .03, .06)))
bpy.ops.mesh.primitive_circle_add(vertices=40, radius=.16, fill_type='NGON', location=(-1.45, 4.4, 2.05), rotation=(math.radians(90), 0, 0))
bpy.context.active_object.data.materials.append(MOONM)
box('hall', 1.4, 2.7, 2.6, 4.5, 0, 2.3, VOID)
hinge = bpy.data.objects.new('door_hinge', None); scene.collection.objects.link(hinge); hinge.location = (1.55, 2.55, 0)
door = box('door', 0, .98, -.025, .025, 0, 2.12, WOOD); door.parent = hinge
for t, a in ((0, -12), (6.5, -12), (7.6, -21)): hinge.rotation_euler = (0, 0, math.radians(a)); hinge.keyframe_insert('rotation_euler', index=2, frame=F(t))
box('nightstand', -2.35, -1.85, 1.9, 2.4, 0, .55, WOOD)
box('lantern', -2.22, -1.98, 2.08, 2.32, .55, .83, LANTERN, bevel=.02)
box('headboard', -1.85, -1.75, 1.3, 2.35, 0, 1.15, WOOD)
box('bedframe', -1.8, .95, 1.3, 2.35, .15, .42, WOOD)
box('mattress', -1.75, .9, 1.35, 2.3, .42, .56, SHEET, bevel=.03)
box('pillow', -1.68, -1.08, 1.5, 2.15, .55, .68, SHEET, bevel=.05, subdiv=2)

# ---------------------------------------------------------------- Haru: lying on her back, head to the headboard
haru_rig = bpy.data.objects['Haru_rig']; vis_rig = bpy.data.objects['Visitor_rig']
haru_rig.rotation_mode = 'XYZ'
haru_rig.matrix_world = Matrix.Translation((0.0, 1.8, .66)) @ Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Rotation(math.radians(-90), 4, 'X')
quilt = box('quilt', -.95, .97, 1.36, 2.27, .5, .86, QUILT, bevel=.12, subdiv=3)               # over her from the chest down
qt = quilt.modifiers.new('folds', 'DISPLACE'); qt.strength = .03
qt.texture = bpy.data.textures.new('quiltnoise', 'CLOUDS'); qt.texture.noise_scale = .25

# ---------------------------------------------------------------- the Visitor: in the corner by the door, never moves
vis_rig.matrix_world = Matrix.Translation((1.18, 2.1, 0)) @ Matrix.Rotation(math.radians(-14), 4, 'Z')

# ---------------------------------------------------------------- animation on Haru's bones
def pb(name): return haru_rig.pose.bones.get(name)
def rot_key(bone, axis, pairs):
    b = pb(bone)
    if not b: print('  (no bone', bone, ')'); return
    b.rotation_mode = 'XYZ'
    for t, deg in pairs:
        e = list(b.rotation_euler); e['XYZ'.index(axis)] = math.radians(deg); b.rotation_euler = e
        b.keyframe_insert('rotation_euler', frame=F(t))
LID = float(os.environ.get('PV_LID', 1.0))       # sign of the eyelid axis (checked with --frames)
SIT = float(os.environ.get('PV_SIT', 1.0))       # sign of the spine bend axis
for side in ('L', 'R'):     # measured: upper lid closes at X -45, lower lid rises at X +; after the footstep the eyes go slightly wide
    rot_key(f'orbicularis03.{side}', 'X', [(0, -46 * LID), (4.0, -46 * LID), (4.6, -30 * LID), (5.0, -40 * LID), (5.9, 0), (6.5, 0), (6.9, 9 * LID), (8.93, 9 * LID), (9.03, -46 * LID), (9.2, 9 * LID), (DUR, 9 * LID)])
    rot_key(f'orbicularis04.{side}', 'X', [(0, 14 * LID), (4.0, 14 * LID), (5.9, 0), (6.5, 0), (6.9, -5 * LID), (DUR, -5 * LID)])
# breathing: chest rises and falls, then stops at the footstep
br = [(i * 1.1, (2.2 if i % 2 else 0)) for i in range(6)] + [(6.5, 0), (DUR, 0)]
rot_key('spine03', 'X', [(t, v * SIT) for t, v in br])
# head turns toward the door (her feet side) and lifts a little
rot_key('neck01', 'X', [(0, 0), (7.6, 0), (10.0, 18 * SIT), (13, 4 * SIT), (DUR, 4 * SIT)])
rot_key('head', 'Z', [(0, 0), (7.6, 0), (10.0, -28), (13, 0), (DUR, 0)])
# sitting up: bend at the spine in two stages, a held breath between
for bone, share in (('spine05', .25), ('spine04', .25), ('spine03', .2), ('spine02', .15), ('spine01', .15)):
    rot_key(bone, 'X', [(0, 0), (10.2, 0), (11.0, 18 * share * SIT), (11.5, 18 * share * SIT), (13.0, 88 * share * SIT), (DUR, 88 * share * SIT)])
# arms: the rig rests in an A pose, so lay both arms along her sides (they follow the torso when she sits up)
scene.frame_set(1)                                         # measure the arms in the lying pose, not the last keyed one
for side, sx in (('L', 1), ('R', -1)):
    goal = Vector((.1 * sx, -.12, -1)).normalized()
    for bn, nxt in (('upperarm01', 'lowerarm01'), ('lowerarm01', 'wrist')):   # whole upper arm, then forearm, along the body
        b = pb(f'{bn}.{side}'); bpy.context.view_layer.update()
        m3 = b.matrix.to_3x3().normalized(); d = (pb(f'{nxt}.{side}').head - b.head).normalized()
        b.rotation_mode = 'QUATERNION'
        b.rotation_quaternion = (b.rotation_quaternion.to_matrix() @ (m3.inverted() @ d.rotation_difference(goal).to_matrix() @ m3)).to_quaternion()
        b.keyframe_insert('rotation_quaternion', frame=1)
# the right hand closes on the quilt when she freezes
for f in ('finger2', 'finger3', 'finger4', 'finger5'):
    for k in ('1', '2', '3'):
        rot_key(f'{f}-{k}.R', 'X', [(0, 8), (13.6, 8), (14.6, 50 if k == '1' else 65), (DUR, 50 if k == '1' else 65)])

# ---------------------------------------------------------------- light, camera, render
world = bpy.data.worlds.new('night'); scene.world = world
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.004, .005, .009, 1)
vol = world.node_tree.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = 0 if PREVIEW else .01
world.node_tree.links.new(vol.outputs['Volume'], world.node_tree.nodes['World Output'].inputs['Volume'])
def light(name, kind, energy, color, loc, rot, size=1.0, spot=None):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA': L.size = size
    if spot: L.spot_size = math.radians(spot); L.spot_blend = .6
    o = bpy.data.objects.new(name, L); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]; return o
light('moonlight', 'AREA', 480, (.55, .66, 1.0), (-1.9, 3.6, 2.6), (-42, 0, 15), size=1.1)
light('fill', 'AREA', 14, (.45, .52, .8), (0, -2.5, 2.4), (65, 0, 0), size=3)
light('face', 'AREA', 6, (.55, .65, 1), (-1.0, .3, 1.6), (35, 0, 0), size=.5)          # a whisper of light so her face reads
light('door_spill', 'AREA', 30, (.5, .6, .95), (.6, 1.7, 1.45), (0, -78, 0), size=.6)     # cold spill from the open door onto her face
light('visitor_rim', 'SPOT', 9, (.5, .6, .9), (1.3, .4, 3.0), (25, 0, 0), spot=28)

target = bpy.data.objects.new('focus', None); scene.collection.objects.link(target)
cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); scene.collection.objects.link(cam); scene.camera = cam
tt = cam.constraints.new('TRACK_TO'); tt.target = target; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cd.dof.use_dof = True; cd.dof.focus_object = target; cd.dof.aperture_fstop = 2.2
shots = [(0, (-.95, 1.05, 1.3), (-1.45, 1.8, .82), 60), (6, (-1.0, 1.1, 1.25), (-1.45, 1.8, .82), 60), (10, (-1.0, 1.08, 1.22), (-1.42, 1.8, .84), 60),
         (13.2, (.95, 1.62, 1.42), (-.85, 1.8, 1.2), 50), (16, (.88, 1.63, 1.41), (-.85, 1.8, 1.2), 56),
         (19.3, (.35, -1.6, 1.35), (.8, 2.0, 1.2), 34), (DUR, (.37, -1.62, 1.35), (.8, 2.0, 1.2), 34)]
for t, cl, tl, lens in shots:
    cam.location = cl; cam.keyframe_insert('location', frame=F(t)); target.location = tl; target.keyframe_insert('location', frame=F(t))
    cd.lens = lens; cd.keyframe_insert('lens', frame=F(t))

if '--cam' in ARGS:                                      # debug: fixed camera  x,y,z,tx,ty,tz,lens
    v = [float(x) for x in ARGS[ARGS.index('--cam') + 1].split(',')]
    cam.animation_data_clear(); target.animation_data_clear(); cd.animation_data_clear()
    cam.location = v[:3]; target.location = v[3:6]; cd.lens = v[6]; cd.dof.use_dof = False
scene.render.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = kind; prefs.get_devices()
            if any(d.type == kind for d in prefs.devices):
                for d in prefs.devices: d.use = d.type == kind
                scene.cycles.device = 'GPU'; print('rendering on', kind); break
        except TypeError: continue
except Exception as e: print('GPU setup failed, using CPU:', e)
scene.cycles.samples = int(os.environ.get('PV_SAMPLES', 48 if PREVIEW else 192)); scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = (960, 540) if PREVIEW else (1920, 1080)
if os.environ.get('PV_SMALL'): scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = .35
try: scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
scene.view_settings.exposure = -.5
frames_dir = os.path.join(HERE, 'scene_frames_preview' if PREVIEW else 'scene_frames'); os.makedirs(frames_dir, exist_ok=True)
scene.render.filepath = os.path.join(frames_dir, 'f_'); scene.render.image_settings.file_format = 'PNG'
scene.render.use_overwrite = False; scene.render.use_placeholder = True

def write_sound(path):                                  # true silence; one footstep at 6.5 s; a soft paper rustle at 16.2 s
    sr = 48000; n = int(DUR * sr); s = [0.0] * n; rnd = random.Random(3); lp = 0.0
    for j in range(int(.5 * sr)):
        tt_ = j / sr; lp += (rnd.uniform(-1, 1) - lp) * .05
        s[int(6.5 * sr) + j] += .45 * (math.sin(2 * math.pi * (62 + 28 * math.exp(-tt_ * 25)) * tt_) * math.exp(-tt_ * 13) + lp * math.exp(-((tt_ - .14) / .07) ** 2) * 2.2)
    m = int(1.1 * sr)
    for j in range(m):
        if rnd.random() > .72: s[int(16.2 * sr) + j] += .035 * rnd.uniform(-1, 1) * math.sin(math.pi * j / m)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, v)) * 30000)) for v in s))

wav = os.path.join(HERE, 'paper_visitor_scene.wav'); write_sound(wav)
if '--frames' in ARGS:
    for fr in [int(x) for x in ARGS[ARGS.index('--frames') + 1].split(',')]:
        scene.frame_set(fr); scene.render.filepath = os.path.join(frames_dir, f'test_{fr:04d}.png'); bpy.ops.render.render(write_still=True)
    sys.exit(0)
bpy.ops.render.render(animation=True)
ed = bpy.data.scenes.new('edit'); ed.render.fps = FPS; ed.frame_start = 1; ed.frame_end = FRAMES
ed.render.resolution_x, ed.render.resolution_y = scene.render.resolution_x, scene.render.resolution_y
seq = ed.sequence_editor_create(); strips = seq.strips if hasattr(seq, 'strips') else seq.sequences
files = sorted(f for f in os.listdir(frames_dir) if f.startswith('f_') and f.endswith('.png'))
img = strips.new_image('frames', os.path.join(frames_dir, files[0]), 1, 1)
for f in files[1:]: img.elements.append(f)
strips.new_sound('sound', wav, 2, 1)
if hasattr(ed.render.image_settings, 'media_type'): ed.render.image_settings.media_type = 'VIDEO'
ed.render.image_settings.file_format = 'FFMPEG'; ed.render.ffmpeg.format = 'MPEG4'; ed.render.ffmpeg.codec = 'H264'
ed.render.ffmpeg.constant_rate_factor = 'HIGH'; ed.render.ffmpeg.audio_codec = 'AAC'; ed.render.ffmpeg.audio_bitrate = 192
ed.render.filepath = os.path.join(HERE, 'paper_visitor_scene' + ('_preview' if PREVIEW else '') + '.mp4')
with bpy.context.temp_override(scene=ed): bpy.ops.render.render(animation=True)
print('saved', ed.render.filepath)
