"""Builds the two main characters of The Paper Visitor with MPFB2 (MakeHuman for Blender) and saves characters.blend.
Run on the PC (needs MPFB2 + the CC0 asset packs):   blender -b -P build_characters.py
Also renders character_sheet.png (both characters, front and three-quarter, under moonlight).

HARU (the girl): young Japanese woman, long straight black hair, plain kimono, real skin, eyebrows, lashes, rigged.
THE VISITOR: the same human base pushed just past normal: too tall, too thin, arms too long, neck too long, head a
little small, skin replaced by crumpled, creased, aged paper. No eyes in the sockets, no hair, no mouth movement.
"""
import bpy, os, sys, math, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []

import addon_utils
for _m in addon_utils.modules():                    # make sure MPFB is loaded (also when run from a plain bpy module)
    if _m.__name__.endswith('mpfb'): addon_utils.enable(_m.__name__, default_set=True)

def mpfb(mod, key):
    for name in list(sys.modules):
        if name.endswith(mod): return getattr(importlib.import_module(name), key)
    raise SystemExit('MPFB2 is not enabled: Edit > Preferences > Add-ons > tick MPFB')
HumanService = mpfb('mpfb.services.humanservice', 'HumanService')
AssetService = mpfb('mpfb.services.assetservice', 'AssetService')
TargetService = mpfb('mpfb.services.targetservice', 'TargetService')
Props = mpfb('mpfb.entities.objectproperties', 'HumanObjectProperties')

def asset(fname, subdir):
    p = AssetService.find_asset_absolute_path(fname, asset_subdir=subdir)
    if not p: print(f'  (missing {subdir}/{fname}: skipped)')
    return p

def add(basemesh, fname, subdir, kind):
    p = asset(fname, subdir)
    if p: return HumanService.add_mhclo_asset(p, basemesh, asset_type=kind, subdiv_levels=1)

def human(name, macro, race):
    bpy.ops.object.select_all(action='DESELECT')
    b = HumanService.create_human(macro_detail_dict=dict(macro, race=race))
    b.name = name; return b

# ---------------------------------------------------------------- reset
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)     # empty scene, but keep add-ons loaded

# ---------------------------------------------------------------- HARU
haru = human('Haru', dict(gender=1.0, age=0.42, muscle=0.3, weight=0.35, proportions=0.6, height=0.42, cupsize=0.45, firmness=0.5),
             dict(african=0.0, asian=1.0, caucasian=0.0))
skin = asset('young_asian_female.mhmat', 'skins')
if skin: HumanService.set_character_skin(skin, haru, skin_type='ENHANCED_SSS')
add(haru, 'high-poly.mhclo', 'eyes', 'Eyes'); add(haru, 'mindfront_eyebrows_03.mhclo', 'eyebrows', 'Eyebrows')
add(haru, 'eyelashes01.mhclo', 'eyelashes', 'Eyelashes'); add(haru, 'teeth_base.mhclo', 'teeth', 'Teeth')
add(haru, 'o4saken_long01.mhclo', 'hair', 'Hair') or add(haru, 'long01.mhclo', 'hair', 'Hair')
add(haru, 'mindfront_kimono.mhclo', 'clothes', 'Clothes')
def dye(obj_name_part, rgb, fac=.85):
    for ob in bpy.data.objects:
        if obj_name_part in ob.name.lower() and ob.type == 'MESH':
            for m in ob.data.materials:
                if not m or not m.node_tree: continue
                n = m.node_tree.nodes; l = m.node_tree.links
                b = next((x for x in n if x.type == 'BSDF_PRINCIPLED'), None)
                if not b or not b.inputs['Base Color'].links: continue
                src = b.inputs['Base Color'].links[0].from_socket
                mix = n.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs['Fac'].default_value = fac
                mix.inputs['Color2'].default_value = (*rgb, 1)
                l.new(src, mix.inputs['Color1']); l.new(mix.outputs['Color'], b.inputs['Base Color'])
dye('kimono', (.10, .12, .24), fac=1.0)                                   # pink -> dark indigo
haru_rig = HumanService.add_builtin_rig(haru, 'default'); haru_rig.name = 'Haru_rig'

# ---------------------------------------------------------------- THE VISITOR
vis = human('Visitor', dict(gender=0.55, age=0.62, muscle=0.0, weight=0.0, proportions=0.0, height=0.78, cupsize=0.5, firmness=0.5),
            dict(african=0.0, asian=0.5, caucasian=0.5))
vis_rig = HumanService.add_builtin_rig(vis, 'default'); vis_rig.name = 'Visitor_rig'
vis_rig.location.x = 1.4

# paper skin: crumpled, creased, aged; the empty eye sockets stay empty
def paper_skin():
    m = bpy.data.materials.new('visitor_paper'); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links; b = n['Principled BSDF']
    b.inputs['Roughness'].default_value = .9
    try: b.inputs['Subsurface Weight'].default_value = .12; b.inputs['Subsurface Radius'].default_value = (.02, .015, .01)
    except KeyError: pass
    tc = n.new('ShaderNodeTexCoord')
    crumple = n.new('ShaderNodeTexVoronoi'); crumple.inputs['Scale'].default_value = 22
    folds = n.new('ShaderNodeTexWave'); folds.inputs['Scale'].default_value = 3.5; folds.inputs['Distortion'].default_value = 2
    grain = n.new('ShaderNodeTexNoise'); grain.inputs['Scale'].default_value = 220; grain.inputs['Detail'].default_value = 10
    stain = n.new('ShaderNodeTexNoise'); stain.inputs['Scale'].default_value = 2.2; stain.inputs['Detail'].default_value = 4
    for t in (crumple, folds, grain, stain): l.new(tc.outputs['Object'], t.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')                                   # aged paper: cream with brown-grey stains
    ramp.color_ramp.elements[0].position = .4; ramp.color_ramp.elements[0].color = (.55, .48, .36, 1)
    ramp.color_ramp.elements[1].position = .7; ramp.color_ramp.elements[1].color = (.20, .17, .13, 1)
    l.new(stain.outputs['Fac'], ramp.inputs['Fac'])
    mul = n.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs['Fac'].default_value = .25
    l.new(ramp.outputs['Color'], mul.inputs['Color1']); l.new(grain.outputs['Color'], mul.inputs['Color2']); l.new(mul.outputs['Color'], b.inputs['Base Color'])
    creases = n.new('ShaderNodeValToRGB')                               # thin dark fold lines
    creases.color_ramp.elements[0].position = .0; creases.color_ramp.elements[0].color = (.12, .1, .08, 1)
    creases.color_ramp.elements[1].position = .1; creases.color_ramp.elements[1].color = (1, 1, 1, 1)
    l.new(crumple.outputs['Distance'], creases.inputs['Fac'])
    mul2 = n.new('ShaderNodeMixRGB'); mul2.blend_type = 'MULTIPLY'; mul2.inputs['Fac'].default_value = .85
    l.new(mul.outputs['Color'], mul2.inputs['Color1']); l.new(creases.outputs['Color'], mul2.inputs['Color2']); l.new(mul2.outputs['Color'], b.inputs['Base Color'])
    h = n.new('ShaderNodeMath'); h.operation = 'ADD'; l.new(crumple.outputs['Distance'], h.inputs[0]); l.new(folds.outputs['Fac'], h.inputs[1])
    bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 1.0; bump.inputs['Distance'].default_value = .03
    l.new(h.outputs['Value'], bump.inputs['Height']); l.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m
vis.data.materials.clear(); vis.data.materials.append(paper_skin())

# proportions pushed past human: longer arms and neck, smaller head, stooped shoulders (stored as the rest pose)
bpy.context.view_layer.objects.active = vis_rig; bpy.ops.object.mode_set(mode='EDIT')
for bn in ('upperarm02.L', 'upperarm02.R', 'lowerarm01.L', 'lowerarm01.R', 'lowerarm02.L', 'lowerarm02.R', 'wrist.L', 'wrist.R', 'neck02', 'neck03', 'head'):
    eb = vis_rig.data.edit_bones.get(bn)
    if eb: eb.inherit_scale = 'NONE'                      # each stretched segment stretches only itself
bpy.ops.object.mode_set(mode='POSE')
def scale(bone, s):
    pb = vis_rig.pose.bones.get(bone)
    if pb: pb.scale = s
for side in ('L', 'R'):
    for b in ('upperarm01', 'upperarm02'): scale(f'{b}.{side}', (1, 1.25, 1))
    for b in ('lowerarm01', 'lowerarm02'): scale(f'{b}.{side}', (1, 1.3, 1))
    
    pb = vis_rig.pose.bones.get(f'clavicle.{side}')
    if pb: pb.rotation_mode = 'XYZ'; pb.rotation_euler.x = math.radians(-8)
for b in ('neck01', 'neck02', 'neck03'): scale(b, (1, 1.35, 1))
scale('head', (.88, .88, .88))
from mathutils import Matrix
bpy.context.view_layer.update()
for side in ('L', 'R'):                                                  # arms hang straight down (rotate in armature space)
    pb = vis_rig.pose.bones.get(f'upperarm01.{side}')
    if not pb: continue
    d = (pb.tail - pb.head).normalized(); target = Matrix.Identity(3).col[2] * -1        # point straight down (-Z)
    q = d.rotation_difference(target); hd = pb.head.copy()
    pb.matrix = Matrix.Translation(hd) @ q.to_matrix().to_4x4() @ Matrix.Translation(-hd) @ pb.matrix
    bpy.context.view_layer.update()
pb = vis_rig.pose.bones.get('head')
if pb: pb.rotation_mode = 'XYZ'; pb.rotation_euler = (math.radians(6), 0, math.radians(14))     # the head sits a little wrong
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
void = bpy.data.materials.new('void'); void.use_nodes = True
void.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0, 0, 0, 1); void.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 1
for side in ('L', 'R'):                                                  # pure black holes where the eyes should be
    eb = vis_rig.pose.bones.get(f'eye.{side}')
    if not eb: continue
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.015, location=(vis_rig.matrix_world @ eb.head) + __import__('mathutils').Vector((0, -.004, 0)))   # sits inside the socket: reads as a hole
    hole = bpy.context.active_object; hole.name = f'Visitor_hole_{side}'; hole.data.materials.append(void)
    hole.parent = vis_rig; hole.parent_type = 'BONE'; hole.parent_bone = 'head'
    hole.matrix_world = bpy.data.objects[hole.name].matrix_world

# ---------------------------------------------------------------- save + a quick moonlit character sheet
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'characters.blend'))
scene = bpy.context.scene
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.01, .012, .02, 1)
key = bpy.data.lights.new('moon', 'AREA'); key.energy = 400; key.color = (.6, .7, 1); key.size = 1.5
ko = bpy.data.objects.new('moon', key); scene.collection.objects.link(ko); ko.location = (-2, -2.5, 3); ko.rotation_euler = (math.radians(50), 0, math.radians(-38))
rim = bpy.data.lights.new('rim', 'AREA'); rim.energy = 150; rim.color = (.5, .6, 1); rim.size = 1
ro = bpy.data.objects.new('rim', rim); scene.collection.objects.link(ro); ro.location = (2.5, 2.5, 2.5); ro.rotation_euler = (math.radians(-60), 0, math.radians(135))
floor = bpy.data.meshes.new('floor'); floor.from_pydata([(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)], [], [(0, 1, 2, 3)])
fo = bpy.data.objects.new('floor', floor); scene.collection.objects.link(fo)
cam_d = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_d); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (.7, -5.6, 1.15); cam.rotation_euler = (math.radians(88), 0, 0); cam_d.lens = 38
scene.render.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
    if any(d.type == 'OPTIX' for d in prefs.devices):
        for d in prefs.devices: d.use = d.type == 'OPTIX'
        scene.cycles.device = 'GPU'
except Exception: pass
scene.cycles.samples = int(os.environ.get('PV_SAMPLES', 128)); scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = (1920, 1080) if not os.environ.get('PV_SMALL') else (960, 540)
try: scene.view_settings.view_transform = 'AgX'
except Exception: pass
scene.render.filepath = os.path.join(HERE, 'character_sheet.png')
bpy.ops.render.render(write_still=True)
print('saved characters.blend and character_sheet.png')
