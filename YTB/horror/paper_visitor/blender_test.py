"""The Paper Visitor - 20 s sample, built and rendered in Blender (paper diorama, GPU).

Run on the PC with the RTX card (Blender 4.x / 5.x):
    blender -b -P blender_test.py
Optional:  blender -b -P blender_test.py -- --preview   (960x540, fewer samples, quick look)
Output (next to this file): frames/ (resumable: re-run to continue), paper_visitor_sample.mp4 (with sound)

Look: flat paper cut-outs with real thickness, paper grain and gentle crumple, standing in a small room like a paper
theater, lit by moonlight through the window (real shadows, a faint haze in the beam), shallow depth of field.
Sound: true silence, except ONE footstep in the hallway at 6.5 s and a very soft paper rustle at 16.2 s.
"""
import bpy, bmesh, math, os, sys, wave, struct, random
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__))
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW = '--preview' in ARGS
FPS, DUR = 30, 20.0
FRAMES = int(FPS * DUR)
def F(t): return 1 + round(t * FPS)          # seconds -> frame number

# ---------------------------------------------------------------- reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS; scene.frame_start = 1; scene.frame_end = FRAMES

# ---------------------------------------------------------------- materials
_mats = {}
def paper(name, rgb, rough=.85, crumple=.25, emit=0.0):
    key = (name, rgb)
    if key in _mats: return _mats[key]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; l = nt.links
    bsdf = n['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = rough
    try: bsdf.inputs['Subsurface Weight'].default_value = .04       # thin paper lets a little light through
    except KeyError: pass
    if emit:
        try: bsdf.inputs['Emission Color'].default_value = (*rgb, 1); bsdf.inputs['Emission Strength'].default_value = emit
        except KeyError: pass
    # paper grain (fine) + crumple (large): colour variation and bump
    tc = n.new('ShaderNodeTexCoord')
    fine = n.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value = 140; fine.inputs['Detail'].default_value = 8
    big = n.new('ShaderNodeTexVoronoi'); big.inputs['Scale'].default_value = 9
    mix = n.new('ShaderNodeMath'); mix.operation = 'ADD'
    l.new(tc.outputs['Object'], fine.inputs['Vector']); l.new(tc.outputs['Object'], big.inputs['Vector'])
    l.new(fine.outputs['Fac'], mix.inputs[0]); l.new(big.outputs['Distance'], mix.inputs[1])
    bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = crumple; bump.inputs['Distance'].default_value = .002
    l.new(mix.outputs['Value'], bump.inputs['Height']); l.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    tint = n.new('ShaderNodeMixRGB'); tint.blend_type = 'MULTIPLY'; tint.inputs['Fac'].default_value = .18
    tint.inputs['Color1'].default_value = (*rgb, 1)
    l.new(fine.outputs['Color'], tint.inputs['Color2']); l.new(tint.outputs['Color'], bsdf.inputs['Base Color'])
    _mats[key] = m; return m

def black(name='void'):
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0, 0, 0, 1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 1
    _mats[name] = m; return m

# ---------------------------------------------------------------- geometry helpers
def cut(name, pts, mat, thick=.004, loc=(0, 0, 0), parent=None, y=0.0, jag=0.0):
    """a paper cut-out: 2D outline pts [(x, z)] in metres, in the XZ plane, extruded to `thick` along -Y"""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    r = random.Random(hash(name) & 0xffff)
    vs = [bm.verts.new((x + r.uniform(-jag, jag), y, z + r.uniform(-jag, jag))) for x, z in pts]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in ext['geom'] if isinstance(e, bmesh.types.BMVert)]: v.co.y -= thick
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    ob.data.materials.append(mat); ob.location = loc
    if parent: ob.parent = parent
    return ob

def oval(name, cx, cz, rx, rz, mat, n=32, **kw):
    return cut(name, [(cx + rx * math.cos(a), cz + rz * math.sin(a)) for a in [i * 2 * math.pi / n for i in range(n)]], mat, **kw)

def ink(name, pts, w, mat, parent=None, y=0.0):
    """an ink line: a thin flat strip along a polyline"""
    me = bpy.data.meshes.new(name); bm = bmesh.new(); left, right = [], []
    for i, (x, z) in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(len(pts) - 1, i + 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz) or 1; nx, nz = -dz / L * w / 2, dx / L * w / 2
        left.append(bm.verts.new((x + nx, y, z + nz))); right.append(bm.verts.new((x - nx, y, z - nz)))
    for i in range(len(pts) - 1): bm.faces.new([left[i], left[i + 1], right[i + 1], right[i]])
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); ob.data.materials.append(mat)
    if parent: ob.parent = parent
    return ob

def box(name, x0, x1, y0, y1, z0, z1, mat):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    ob.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); ob.scale = (x1 - x0, y1 - y0, z1 - z0)
    ob.data.materials.append(mat); return ob

def empty(name, loc, parent=None):
    e = bpy.data.objects.new(name, None); scene.collection.objects.link(e); e.empty_display_size = .05
    if parent: e.parent = parent
    e.location = loc; return e

def key(ob, path, t_vals, index=-1):
    """keyframe ob.<path> at (seconds, value) pairs; smooth Bezier easing between keys"""
    for t, v in t_vals:
        if index >= 0: getattr(ob, path)[index] = v
        else: setattr(ob, path, v)
        ob.keyframe_insert(data_path=path, index=index, frame=F(t))

# ---------------------------------------------------------------- palette (muted, paper theater)
WALL = paper('wall', (.20, .14, .11)); WALL2 = paper('wall_plank', (.15, .10, .085))
FLOOR = paper('floor', (.11, .08, .07)); WOOD = paper('wood', (.25, .13, .08))
SHEET = paper('sheet', (.40, .36, .30)); QUILT = paper('quilt', (.36, .07, .06)); QUILT2 = paper('quilt_dark', (.26, .05, .05))
SKIN = paper('skin', (.72, .58, .46), crumple=.12); SKIN_SH = paper('skin_shadow', (.48, .36, .29), crumple=.1)
HAIR = paper('hair', (.02, .015, .015), rough=.6); KIMONO = paper('kimono', (.09, .11, .17)); KIMONO2 = paper('kimono2', (.06, .075, .12))
RED = paper('red', (.40, .05, .04)); EYEW = paper('eye_white', (.80, .76, .70), crumple=.03)
INK = paper('ink', (.012, .008, .008), rough=.5, crumple=0); INK_SOFT = paper('ink_soft', (.20, .12, .10), crumple=0)
VPAPER = paper('visitor', (.50, .47, .40), crumple=.6); VPAPER2 = paper('visitor_shade', (.34, .31, .26), crumple=.6)
LANTERN = paper('lantern', (.62, .50, .34)); NIGHT = paper('night', (.02, .03, .06), emit=.0)
MOON = paper('moon', (.9, .9, .82), emit=6.0)

# ---------------------------------------------------------------- the room (a small paper theater)
box('floor', -4, 4, -3, 3.2, -.05, 0, FLOOR)
for (x0, x1, z0, z1) in ((-4, -2.25, 0, 3.2), (-1.15, 1.55, 0, 3.2), (2.55, 4, 0, 3.2), (-2.25, -1.15, 0, 1.15), (-2.25, -1.15, 2.25, 3.2), (1.55, 2.55, 2.15, 3.2)):
    box(f'wall_{x0}', x0, x1, 2.5, 2.6, z0, z1, WALL)                          # back wall with a window hole and a door hole
for i, x in enumerate([-3.6 + .55 * k for k in range(14)]):
    if not (-2.3 < x < -1.1 or 1.5 < x < 2.6): box(f'plank_{i}', x, x + .02, 2.49, 2.5, 0, 3.2, WALL2)
box('sill', -2.3, -1.1, 2.3, 2.62, 1.1, 1.15, WOOD)
for (x0, x1, z0, z1) in ((-2.3, -2.22, 1.15, 2.3), (-1.18, -1.1, 1.15, 2.3), (-2.3, -1.1, 2.22, 2.3), (-1.74, -1.66, 1.15, 2.22), (-2.22, -1.18, 1.68, 1.74)):
    box(f'frame_{x0}_{z0}', x0, x1, 2.52, 2.6, z0, z1, WOOD)
box('night_sky', -3, 0, 4.5, 4.6, 0, 4, NIGHT)
oval('moon', -1.45, 2.05, .16, .16, MOON, y=4.4)
box('hall', 1.4, 2.7, 2.6, 4.5, 0, 2.3, black('hall'))                       # pure darkness behind the door
door_hinge = empty('door_hinge', (1.55, 2.55, 0))
box('door', 0, .98, -.025, .025, 0, 2.12, WOOD).parent = door_hinge
door_hinge.rotation_euler = (0, 0, math.radians(-12))
key(door_hinge, 'rotation_euler', [(0, math.radians(-12)), (6.5, math.radians(-12)), (7.6, math.radians(-21))], index=2)
box('nightstand', -2.35, -1.85, 1.9, 2.4, 0, .55, WOOD)
lan = cut('lantern', [(-.12, 0), (.12, 0), (.1, .28), (-.1, .28)], LANTERN, thick=.18, loc=(-2.1, 2.2, .55))
for k in range(4): ink(f'lantern_rib{k}', [(-.11, .05 + k * .065), (.11, .05 + k * .065)], .006, INK_SOFT, parent=lan, y=-.181)
box('headboard', -1.85, -1.75, 1.3, 2.35, 0, 1.15, WOOD)
box('bedframe', -1.8, .95, 1.3, 2.35, .15, .42, WOOD)
box('mattress', -1.75, .9, 1.35, 2.3, .42, .56, SHEET)
pil = oval('pillow', 0, 0, .3, .085, SHEET, thick=.4, loc=(-1.35, 2.3, .6))          # sits BEHIND her head (puppet plane is y=1.62)

# ---------------------------------------------------------------- the girl: a jointed paper puppet (lies along -X, faces the camera plane)
PLANE_Y = 1.62
hip = empty('hip', (-.3, PLANE_Y, .63))
cut('torso', [(0, -.095), (-.5, -.1), (-.53, -.06), (-.53, .07), (-.5, .1), (0, .095)], KIMONO, thick=.03, parent=hip)
cut('torso_shade', [(0, .02), (-.5, .03), (-.5, .095), (0, .09)], KIMONO2, thick=.002, parent=hip, y=-.031)
cut('collar', [(-.36, .1), (-.53, .06), (-.53, .03), (-.38, .07)], RED, thick=.002, parent=hip, y=-.032)
breath = empty('breath', (0, 0, 0), parent=hip)
neck = empty('neck', (-.56, 0, .0), parent=hip)
cut('neck_piece', [(.03, -.035), (-.08, -.035), (-.08, .035), (.03, .035)], SKIN, thick=.02, parent=neck)
head = empty('head', (-.12, 0, .0), parent=neck)
# profile head: drawn so the face looks along +Z (the ceiling) while lying; S = scale from design units to metres
S = .0024
def P(x, y): return (y * S, x * S)            # design (x = facing, y = down) -> local (X, Z)
def Ppts(lst): return [P(x, y) for x, y in lst]
cut('hair_back', Ppts([(-46, -50), (10, -62), (32, -38), (-6, 70), (-54, 84), (-62, 10)]), HAIR, thick=.025, parent=head, y=.035)          # behind the face
cut('face', Ppts([(-30, -40), (14, -46), (34, -24), (36, -6), (44, 6), (36, 12), (38, 22), (30, 30), (32, 38), (18, 50), (-14, 48), (-32, 20)]), SKIN, thick=.012, parent=head)
cut('socket', Ppts([(6, -16), (30, -14), (31, 2), (8, 4)]), SKIN_SH, thick=.001, parent=head, y=-.0125)
cut('cheek', Ppts([(-6, 14), (20, 10), (26, 30), (4, 40)]), SKIN_SH, thick=.001, parent=head, y=-.0125)
eye = empty('eye', (P(20, -6)[0], -.0135, P(20, -6)[1]), parent=head)
cut('eye_white', [(x * S, z * S) for x, z in ((0, -9), (-7, 0), (0, 9), (5, 0))], EYEW, thick=.001, parent=eye)
pupil = empty('pupil', (0, -.0012, .002), parent=eye)
oval('pupil_disc', 0, 0, .0072, .0072, INK, thick=.001, parent=pupil)
ink('lid', Ppts([(10, -6), (20, -13), (30, -5)]), .0055, INK, parent=head, y=-.0145)
ink('lid_low', Ppts([(12, -1), (27, -3)]), .0025, INK_SOFT, parent=head, y=-.0145)
ink('eyebag', Ppts([(12, 3), (20, 6), (28, 4)]), .0025, INK_SOFT, parent=head, y=-.0145)
brow = empty('brow', (P(19, -19)[0], -.0146, P(19, -19)[1]), parent=head)
ink('brow_line', [((y + 19) * S, (x - 19) * S) for x, y in ((7, -17), (19, -21), (30, -15))], .0065, INK, parent=brow)
ink('crease', Ppts([(16, -25), (18, -19)]), .0025, INK, parent=head, y=-.0145)
ink('nostril', Ppts([(36, 14), (40, 20), (35, 22)]), .003, INK_SOFT, parent=head, y=-.0145)
ink('lips', Ppts([(26, 33), (33, 34)]), .004, paper('lip', (.30, .12, .11), crumple=0), parent=head, y=-.0145)
for k in range(4): ink(f'hatch{k}', Ppts([(-4 + k * 5, 18 + k * 3), (2 + k * 5, 30 + k * 3)]), .0018, INK_SOFT, parent=head, y=-.0145)
ink('jaw', Ppts([(-12, 46), (16, 50), (30, 40)]), .0028, INK_SOFT, parent=head, y=-.0145)
cut('fringe', Ppts([(-34, -44), (16, -56), (38, -30), (14, -36), (-8, -30), (-22, 0), (-36, 10)]), HAIR, thick=.004, parent=head, y=-.015)
cut('lock', Ppts([(-2, -34), (6, -32), (4, 6), (-4, 30), (-8, 28)]), HAIR, thick=.002, parent=head, y=-.016)

# arm: shoulder -> elbow -> wrist, lying along the body on top of the quilt
shoulder = empty('shoulder', (-.47, -.04, -.02), parent=hip)
cut('upper_arm', [(0, -.035), (.27, -.03), (.27, .03), (0, .035)], KIMONO2, thick=.025, parent=shoulder)
elbow = empty('elbow', (.27, 0, 0), parent=shoulder)
cut('forearm', [(0, -.03), (.25, -.027), (.25, .027), (0, .03)], KIMONO2, thick=.025, parent=elbow)
wrist = empty('wrist', (.25, -.003, 0), parent=elbow)
cut('hand', [(0, -.03), (.06, -.032), (.1, -.02), (.11, 0), (.1, .018), (.05, .028), (0, .025)], SKIN, thick=.012, parent=wrist)
for k, z in enumerate((-.018, -.006, .006, .017)): ink(f'finger{k}', [(.06, z), (.105, z * .8)], .002, SKIN_SH, parent=wrist, y=-.0125)

# quilt: the lower part stays; the upper flap covers her chest and slides off as she sits up
cut('quilt_low', [(-.35, .56), (.92, .53), (.95, .68), (-.38, .74)], QUILT, thick=.95, loc=(0, 2.3, 0))
flap = empty('flap', (-.35, PLANE_Y - .02, .62))
cut('quilt_flap', [(0, -.08), (-.42, -.08), (-.44, .1), (0, .12)], QUILT2, thick=.06, parent=flap)     # stops at her chest, face stays clear
for k in range(3): ink(f'stitch{k}', [(-.1 - k * .12, -.07), (-.06 - k * .12, .1)], .004, paper('stitch', (.2, .03, .03), crumple=0), parent=flap, y=-.061)

# ---------------------------------------------------------------- the Paper Visitors
def visitor(name, base, height):
    root = empty(name, base)
    k = height / 470.0
    outline = [(-30, 0), (-26, 200), (-34, 250), (-70, 300), (-62, 330), (-30, 345), (-24, 380), (-30, 420), (-18, 452), (0, 460),
               (18, 452), (30, 420), (24, 380), (30, 345), (62, 330), (70, 300), (34, 250), (26, 200), (30, 0)]
    cut(name + '_body', [(x * k, z * k) for x, z in outline], VPAPER, thick=.006, parent=root, jag=.012 * height / 2)
    cut(name + '_armL', [(x * k, z * k) for x, z in ((-70, 300), (-84, 110), (-74, 96), (-60, 290))], VPAPER2, thick=.006, parent=root, y=-.007)
    cut(name + '_armR', [(x * k, z * k) for x, z in ((70, 300), (84, 110), (74, 96), (60, 290))], VPAPER2, thick=.006, parent=root, y=-.007)
    for i, z in enumerate((320, 250, 170, 90)): ink(f'{name}_fold{i}', [(-28 * k, z * k), (28 * k, (z - 5) * k)], .004, INK_SOFT, parent=root, y=-.0075)
    ink(name + '_spine', [(0, 0), (0, 460 * k)], .003, INK_SOFT, parent=root, y=-.0075)
    for ex, ez, rw, rh in ((-12, 414, 8, 4.5), (12, 410, 7, 5.5)):           # two uneven holes torn through the paper
        oval(f'{name}_hole{ex}', ex * k, ez * k, rw * k, rh * k, black(), thick=.001, parent=root, y=-.0072)
    ink(name + '_streak', [(-13 * k, 409 * k), (-14 * k, 392 * k), (-12 * k, 380 * k)], .003, INK_SOFT, parent=root, y=-.0075)
    return root

visitor('visitor', (1.2, 2.05, 0), 2.05)                                       # in the corner by the door: never moves
small = visitor('folded', (-1.6, 2.05, .66), .12)                              # folded on her pillow the whole time
small.rotation_euler = (0, math.radians(-8), 0)

# ---------------------------------------------------------------- animation (smooth Bezier keys)
# breathing: the chest rises and falls, stops at the footstep
br = [(t, 1 + .035 * (math.sin(t * 2 * math.pi / 4.4) * .5 + .5)) for t in [i * .55 for i in range(12)]] + [(6.5, 1.0), (DUR, 1.0)]
key(hip, 'scale', br, index=2)
# eyes: closed -> slow open -> widen in fear; one slow blink at 9 s
key(eye, 'scale', [(0, .08), (4.0, .08), (5.6, 1.0), (6.5, 1.0), (7.3, 1.3), (8.93, 1.3), (9.0, .08), (9.12, 1.3), (DUR, 1.3)], index=0)
key(pupil, 'scale', [(0, 1), (6.5, 1), (7.4, .6), (DUR, .6)], index=0)
key(pupil, 'scale', [(0, 1), (6.5, 1), (7.4, .6), (DUR, .6)], index=2)
key(brow, 'location', [(0, brow.location[0]), (6.5, brow.location[0]), (7.4, brow.location[0] - .012), (DUR, brow.location[0] - .012)], index=0)
key(brow, 'rotation_euler', [(0, 0), (6.5, 0), (7.4, math.radians(9)), (DUR, math.radians(9))], index=1)
# head turns toward the door
key(head, 'rotation_euler', [(0, 0), (7.6, 0), (10.0, math.radians(32)), (11.5, math.radians(30)), (13.0, math.radians(8)), (DUR, math.radians(6))], index=1)
# sitting up: a hand pushes, a held breath, then the rest
key(hip, 'rotation_euler', [(0, 0), (10.2, 0), (11.0, math.radians(15)), (11.5, math.radians(15)), (13.0, math.radians(78)), (DUR, math.radians(78))], index=1)
key(shoulder, 'rotation_euler', [(0, math.radians(4)), (10.2, math.radians(4)), (11.0, math.radians(-30)), (13.0, math.radians(-8)), (DUR, math.radians(-8))], index=1)
key(elbow, 'rotation_euler', [(0, 0), (10.2, 0), (11.0, math.radians(40)), (13.0, math.radians(-70)), (13.2, math.radians(-70)), (14.4, math.radians(-82)), (DUR, math.radians(-82))], index=1)
key(wrist, 'rotation_euler', [(0, 0), (13.2, 0), (14.4, math.radians(-25)), (DUR, math.radians(-25))], index=1)
# the quilt flap slides off her chest as she rises
key(flap, 'location', [(0, -.35), (11.5, -.35), (13.0, .12), (DUR, .12)], index=0)
key(flap, 'location', [(0, .62), (11.5, .62), (13.0, .66), (DUR, .66)], index=2)
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action:
        try:
            for fc in ob.animation_data.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.easing = 'AUTO'
        except AttributeError: pass        # Blender 5 layered actions: Bezier is already the default

# ---------------------------------------------------------------- light: moonlight through the window, faint haze
world = bpy.data.worlds.new('night'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.004, .005, .009, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1
vol = world.node_tree.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = .012 if not PREVIEW else .0
world.node_tree.links.new(vol.outputs['Volume'], world.node_tree.nodes['World Output'].inputs['Volume'])
moon = bpy.data.lights.new('moonlight', 'AREA'); moon.energy = 520; moon.color = (.55, .66, 1.0); moon.size = 1.1; moon.shape = 'SQUARE'
mo = bpy.data.objects.new('moonlight', moon); scene.collection.objects.link(mo); mo.location = (-1.9, 3.6, 2.6)
mo.rotation_euler = (math.radians(-42), 0, math.radians(15))          # points down through the window toward the bed
fill = bpy.data.lights.new('fill', 'AREA'); fill.energy = 18; fill.color = (.45, .52, .8); fill.size = 3
fo = bpy.data.objects.new('fill', fill); scene.collection.objects.link(fo); fo.location = (0, -2.5, 2.4); fo.rotation_euler = (math.radians(65), 0, 0)
rim = bpy.data.lights.new('rim', 'SPOT'); rim.energy = 7; rim.color = (.5, .6, .9); rim.spot_size = math.radians(30)
ro = bpy.data.objects.new('rim', rim); scene.collection.objects.link(ro); ro.location = (1.3, .2, 2.9); ro.rotation_euler = (math.radians(28), 0, 0)   # barely touches the visitor

# ---------------------------------------------------------------- camera: slow push-in, then drifts to find the corner
target = empty('focus', (-1.2, PLANE_Y, .7))
cam_data = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam); scene.camera = cam
tt = cam.constraints.new('TRACK_TO'); tt.target = target; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cam_data.dof.use_dof = True; cam_data.dof.focus_object = target; cam_data.dof.aperture_fstop = 2.4
shots = [(0, (-1.0, .62, .86), (-1.02, PLANE_Y, .67), 55), (6, (-1.0, .82, .8), (-1.02, PLANE_Y, .67), 55), (10, (-.98, .8, .82), (-1.0, PLANE_Y, .7), 55),
         (13.2, (-.55, -.55, 1.15), (-.45, PLANE_Y, .95), 42), (16, (-.5, -.55, 1.15), (-.45, PLANE_Y, .95), 42),
         (19.3, (.35, -1.35, 1.25), (.85, 1.9, 1.05), 36), (DUR, (.37, -1.38, 1.25), (.86, 1.9, 1.05), 36)]
for t, cl, tl, lens in shots:
    cam.location = cl; cam.keyframe_insert('location', frame=F(t))
    target.location = tl; target.keyframe_insert('location', frame=F(t))
    cam_data.lens = lens; cam_data.keyframe_insert('lens', frame=F(t))

# ---------------------------------------------------------------- render settings: Cycles on the GPU (OptiX)
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
scene.cycles.samples = int(os.environ.get('PV_SAMPLES', 48 if PREVIEW else 160))
scene.cycles.use_denoising = True
try: scene.cycles.denoiser = 'OPTIX' if scene.cycles.device == 'GPU' else 'OPENIMAGEDENOISE'
except Exception: pass
scene.cycles.max_bounces = 6; scene.cycles.volume_bounces = 1
scene.render.resolution_x, scene.render.resolution_y = (960, 540) if PREVIEW else (1920, 1080)
if os.environ.get('PV_SMALL'): scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.resolution_percentage = 100
scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = .35
scene.render.film_transparent = False
try:
    scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    try: scene.view_settings.view_transform = 'Filmic'; scene.view_settings.look = 'Medium High Contrast'
    except Exception: pass
scene.view_settings.exposure = -.6
frames_dir = os.path.join(HERE, 'frames_preview' if PREVIEW else 'frames')
os.makedirs(frames_dir, exist_ok=True)
scene.render.filepath = os.path.join(frames_dir, 'f_')
scene.render.image_settings.file_format = 'PNG'
scene.render.use_overwrite = False; scene.render.use_placeholder = True            # re-run to resume after a crash

# ---------------------------------------------------------------- sound: true silence, one footstep, one soft paper rustle
def write_sound(path):
    sr = 48000; n = int(DUR * sr); s = [0.0] * n; rnd = random.Random(3)
    def step(at, amp):
        i0 = int(at * sr); m = int(.5 * sr); lp = 0.0
        for j in range(m):
            tt_ = j / sr
            thud = math.sin(2 * math.pi * (62 + 28 * math.exp(-tt_ * 25)) * tt_) * math.exp(-tt_ * 13)
            lp += (rnd.uniform(-1, 1) - lp) * .05
            creak = lp * math.exp(-((tt_ - .14) / .07) ** 2) * 2.2
            s[i0 + j] += amp * (thud + creak)
    step(6.5, .45)
    i0 = int(16.2 * sr); m = int(1.1 * sr)
    for j in range(m):
        if rnd.random() > .72: s[i0 + j] += .035 * rnd.uniform(-1, 1) * math.sin(math.pi * j / m)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, v)) * 30000)) for v in s))

if __name__ == '__main__':
    wav = os.path.join(HERE, 'paper_visitor_sample.wav'); write_sound(wav)
    if '--frames' in ARGS:                                                     # render only some frames: --frames 1,150,300
        for fr in [int(x) for x in ARGS[ARGS.index('--frames') + 1].split(',')]:
            scene.frame_set(fr); scene.render.filepath = os.path.join(frames_dir, f'test_{fr:04d}.png'); bpy.ops.render.render(write_still=True)
        sys.exit(0)
    bpy.ops.render.render(animation=True)
    # put frames + sound together into an mp4 with Blender's own video editor (no ffmpeg install needed)
    ed = bpy.data.scenes.new('edit'); ed.render.fps = FPS; ed.frame_start = 1; ed.frame_end = FRAMES
    ed.render.resolution_x, ed.render.resolution_y = scene.render.resolution_x, scene.render.resolution_y
    seq = ed.sequence_editor_create()
    files = sorted(f for f in os.listdir(frames_dir) if f.startswith('f_') and f.endswith('.png'))
    strips = getattr(seq, 'strips', None) or seq.sequences
    img = strips.new_image('frames', os.path.join(frames_dir, files[0]), 1, 1)
    for f in files[1:]: img.elements.append(f)
    strips.new_sound('sound', wav, 2, 1)
    ed.render.image_settings.file_format = 'FFMPEG'
    ed.render.ffmpeg.format = 'MPEG4'; ed.render.ffmpeg.codec = 'H264'; ed.render.ffmpeg.constant_rate_factor = 'HIGH'
    ed.render.ffmpeg.audio_codec = 'AAC'; ed.render.ffmpeg.audio_bitrate = 192
    ed.render.filepath = os.path.join(HERE, 'paper_visitor_sample' + ('_preview' if PREVIEW else '') + '.mp4')
    with bpy.context.temp_override(scene=ed): bpy.ops.render.render(animation=True)
    print('saved', ed.render.filepath)
