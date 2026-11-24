"""Look-dev for the clay Haru puppet: turnaround, expression sheet, ID views for measuring against the Artlist sheet.
blender -b -P scenes/haru_sheet.py -- --mode turn|expr|id [--res W H] [--samples N] [--out DIR] [--blend PATH]
"""
import bpy, sys, os, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'puppets'))
argv = sys.argv
MODE = argv[argv.index('--mode') + 1] if '--mode' in argv else 'turn'
if '--mode' in argv: i = argv.index('--mode'); del argv[i:i + 2]
PUPPET = argv[argv.index('--puppet') + 1] if '--puppet' in argv else 'clay'
if '--puppet' in argv: i = argv.index('--puppet'); del argv[i:i + 2]
import haru_puppet as HP
from claylib import *
if PUPPET == 'burton':
    import haru_burton as HB
    Puppet, EYE_Z = HB.HaruBurton, HB.EYE_Z * HP.S
else:
    Puppet, EYE_Z = HP.Haru, 0.1045

OPTS = cli('haru_sheet')
reset()
sc = setup_render(res=OPTS['res'], samples=OPTS['samples'], frames=1)
world((0.6, 0.6, 0.62), 0.2)
sc.view_settings.exposure = -0.6


def sweep(name='sweep', color=(0.62, 0.61, 0.59)):
    """tabletop seamless: floor curving up into a wall 30 cm behind her"""
    import bmesh
    bm = bmesh.new(); prof = [(-0.7, 0.0)]
    for i in range(13):
        a = math.pi / 2 * i / 12; prof.append((0.15 + math.sin(a) * 0.15, 0.15 - math.cos(a) * 0.15))
    prof.append((0.3, 0.6))
    rows = [[bm.verts.new((x, y, z)) for y, z in prof] for x in (-0.8, 0.8)]
    for i in range(len(prof) - 1): bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); smooth(ob)
    assign(ob, clay(name, color, rough=0.9, sss=0.0, bump=0.15, thumb=0.1, scale=2.0))
    HP.colliders().objects.link(ob)
    return ob


bd = sweep()
h = Puppet()
# a smaller key from the side and a little low, so it rakes across the clay and shows dents, folds and prints;
# fill about a tenth of the key (the skill's look guide)
key_l = area_light('key', (-0.42, -0.3, 0.3), (0, 0, 0.07), 9, 0.18, (1.0, 0.94, 0.86))
fill = area_light('fill', (0.45, -0.3, 0.18), (0, 0, 0.06), 1.0, 0.5, (0.8, 0.88, 1.0))
rim = area_light('rim', (0.2, 0.4, 0.32), (0, 0, 0.09), 4.5, 0.2, (1.0, 0.97, 0.92))
out = OPTS['out']; os.makedirs(out, exist_ok=True)
if OPTS['blend']: bpy.ops.wm.save_as_mainfile(filepath=OPTS['blend'])


def shot(path):
    sc.render.filepath = path; bpy.ops.render.render(write_still=True); print('STILL', path, flush=True)


if MODE == 'turn':        # front, 3/4 front, side, 3/4 back, back (like the Artlist turnaround)
    cam = camera((0, -0.55, 0.075), (0, 0, 0.063), lens=70, fstop=4.0)
    for i, yaw in enumerate((0, 35, 90, 145, 180)):
        h.place(yaw=math.radians(yaw)); h.pose({}); h.ground()
        shot(os.path.join(out, f'turn_{i}.png'))

elif MODE == 'look':      # judge the clay: full body 3/4, chest up, face
    h.place(yaw=math.radians(25)); h.pose({}); h.ground(); h.expr('worried')
    eyes = Vector((0, -0.0105, EYE_Z))            # focus on the eyes; miniature close-ups need small apertures
    for nm, loc, tgt, lens, fs in (('full', (0.12, -0.5, 0.08), (0, 0, 0.063), 70, 5.6),
                                    ('chest', (0.05, -0.25, EYE_Z - 0.01), (0, 0, EYE_Z - 0.017), 85, 8.0),
                                    ('face', (0.03, -0.17, EYE_Z), (0, -0.01, EYE_Z - 0.0035), 100, 11.0)):
        foc = (Vector(loc) - eyes).length if nm != 'full' else None
        cam = camera(loc, tgt, lens=lens, fstop=fs, focus=foc); shot(os.path.join(out, f'look_{nm}.png'))
    for nm, loc, tgt, lens, fs, yaw in (('feet', (0.07, -0.2, 0.03), (0, -0.008, 0.007), 85, 8.0, 55),
                                         ('back', (0.0, -0.42, 0.09), (0, 0, 0.075), 70, 5.6, 180)):   # back: turn her round
        h.place(yaw=math.radians(yaw)); h.ground()
        cam = camera(loc, tgt, lens=lens, fstop=fs, focus=(Vector(loc) - Vector(tgt)).length); shot(os.path.join(out, f'look_{nm}.png'))

elif MODE == 'expr':      # head-and-shoulders close-ups, one per expression
    cam = camera((0, -0.24, EYE_Z), (0, 0, EYE_Z - 0.0035), lens=100, fstop=5.6, focus=0.229)   # focus on the face, not the head centre
    h.pose({}); h.ground()
    for name in ('neutral', 'worried', 'scared', 'terrified', 'surprised', 'sad', 'smile', 'happy', 'suspicious',
                 'angry', 'relieved', 'stare', 'sleep'):
        h.expr(name); shot(os.path.join(out, f'expr_{name}.png'))

elif MODE == 'id':        # flat part colours, orthographic, for .claude/skills/clay-character/scripts/measure.py
    sc.render.engine = 'BLENDER_WORKBENCH'
    s = sc.display.shading; s.light = 'FLAT'; s.color_type = 'OBJECT'
    s.show_shadows = s.show_cavity = s.show_object_outline = s.show_specular_highlight = False
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = 0
    sc.world.color = (0.012, 0.012, 0.012)
    for o in bpy.data.objects:
        if o.type in ('MESH', 'CURVE') and o.name not in h.coll.objects: o.hide_render = True
    sc.render.resolution_x, sc.render.resolution_y = 1000, 1300
    cd = bpy.data.cameras.new('cam_id'); cd.type = 'ORTHO'; cd.ortho_scale = 1.4 * HP.S
    cam = bpy.data.objects.new('cam_id', cd); bpy.context.collection.objects.link(cam); sc.camera = cam
    h.pose({}); h.ground()
    for v, (loc, rot) in {0: ((0, -0.5, 0.063), (90, 0, 0)), 2: ((-0.5, 0, 0.063), (90, 0, -90)),
                          4: ((0, 0.5, 0.063), (90, 0, 180))}.items():
        cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
        shot(os.path.join(out, f'id_view{v}.png'))
print('DONE', MODE, flush=True)
