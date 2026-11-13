"""The Paper Visitor - low-poly look (faceted flat-shaded 3D, dark navy room, warm lantern, cold moon). Everything is built in code.
    blender -b -P lowpoly_scene.py                    (1920x1080)
    blender -b -P lowpoly_scene.py -- --preview       (960x540, quick)
    blender -b -P lowpoly_scene.py -- --eevee         (EEVEE instead of Cycles: much faster on a GPU)
    blender -b -P lowpoly_scene.py -- --frames 31,181 (only those frames, as PNGs)
Beats: 0-4 asleep | 4-6 eyes open | 6.5 ONE footstep, breath stops, eyes slide to the door | 7.5-10 she lifts her head |
10.2-13 sits up (a held breath halfway) | 13-16 seen from the corner: hand to her chest | 16-20 the Visitor, its head slowly tilting.
True silence apart from the footstep and one paper rustle."""
import bpy, bmesh, os, sys, math, wave, struct, random
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREVIEW = '--preview' in ARGS
FPS, DUR = 30, 20.0; FRAMES = int(FPS * DUR)
def F(t): return 1 + round(t * FPS)

for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
scene = bpy.context.scene; scene.render.fps = FPS; scene.frame_start = 1; scene.frame_end = FRAMES; C = scene.collection

# ---------------------------------------------------------------- helpers
MATS = {}
def mat(name, rgb, rough=.8, emit=0.0, spec=.3):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
    if emit: b.inputs['Emission Color'].default_value = (*rgb, 1); b.inputs['Emission Strength'].default_value = emit
    MATS[name] = m; return m
def finish(ob, m, parent=None, jitter=0.0, seed=1):
    me = ob.data
    if jitter:                                                  # crumple: nudge every vertex a little (paper / faceted look)
        r = random.Random(seed)
        for v in me.vertices: v.co += Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1))) * jitter
    for p in me.polygons: p.use_smooth = False
    me.materials.append(m)
    if parent: ob.parent = parent
    return ob
def new_mesh(name, build):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); C.objects.link(ob); return ob
def ico(name, r, sub, loc, scale=(1, 1, 1), m=None, parent=None, jitter=0.0, seed=1):
    ob = new_mesh(name, lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r))
    ob.location = loc; ob.scale = scale; return finish(ob, m, parent, jitter, seed)
def cyl(name, r1, r2, h, segs, loc, rot=(0, 0, 0), scale=(1, 1, 1), m=None, parent=None, jitter=0.0, seed=1, base=False):
    def b(bm):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=h)
        if base: bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, h / 2))   # origin at the bottom
    ob = new_mesh(name, b); ob.location = loc; ob.rotation_euler = rot; ob.scale = scale; return finish(ob, m, parent, jitter, seed)
def box(name, size, loc, m, parent=None, rot=(0, 0, 0), jitter=0.0, seed=1, bevel=0.0):
    ob = new_mesh(name, lambda bm: bmesh.ops.create_cube(bm, size=1)); ob.scale = size; ob.location = loc; ob.rotation_euler = rot
    if bevel: md = ob.modifiers.new('b', 'BEVEL'); md.width = bevel; md.segments = 1
    return finish(ob, m, parent, jitter, seed)
def pivot(name, loc, parent=None, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); C.objects.link(e); e.empty_display_size = .05
    e.parent = parent; e.location = loc; e.rotation_euler = rot; return e
def keys(ob, path, idx, pairs, scale=1.0):
    for t, v in pairs:
        getattr(ob, path)[idx] = v * scale; ob.keyframe_insert(path, index=idx, frame=F(t))
R = math.radians

# ---------------------------------------------------------------- palette
NAVY, NAVY2 = mat('navy_wall', (.030, .045, .085)), mat('navy_trim', (.05, .065, .11))
FLOOR, WOOD, WOOD2 = mat('floor', (.10, .055, .035)), mat('wood', (.20, .10, .055)), mat('wood_dark', (.11, .055, .03))
SHEET, QUILT = mat('sheet', (.55, .52, .47)), mat('quilt', (.26, .05, .045))
SKIN, SKIN_D = mat('skin', (.62, .40, .30), rough=.6), mat('skin_dark', (.45, .26, .19))
HAIR = mat('hair', (.012, .010, .012), rough=.45, spec=.6)
KIMONO, COLLAR = mat('kimono', (.06, .07, .15)), mat('collar', (.70, .64, .55))
EYEW, PUPIL, SHINE = mat('eye_white', (.75, .74, .70), rough=.3), mat('pupil', (.005, .005, .006), rough=.15, spec=.8), mat('shine', (1, 1, 1), emit=4)
LIP, BROW = mat('lip', (.40, .16, .14)), mat('brow', (.02, .015, .015))
PAPER = mat('paper', (.66, .61, .50), rough=.95, spec=.15)
HOLE = mat('hole', (0, 0, 0), rough=1, spec=0)
VOID, NIGHT, MOON = mat('void', (0, 0, 0), rough=1, spec=0), mat('night', (.01, .02, .05)), mat('moon', (.85, .9, 1), emit=8)
LANTERN = mat('lantern_paper', (1.0, .55, .22), emit=6)

# ---------------------------------------------------------------- room
box('floor', (8, 6.2, .1), (0, .1, -.05), FLOOR)
for i in range(12): box(f'board_{i}', (8, .012, .004), (0, -3 + i * .5, .001), WOOD2)
for (x0, x1, z0, z1) in ((-4, -2.25, 0, 3.2), (-1.15, 1.55, 0, 3.2), (2.55, 4, 0, 3.2), (-2.25, -1.15, 0, 1.15), (-2.25, -1.15, 2.25, 3.2), (1.55, 2.55, 2.15, 3.2)):
    box(f'wall_{x0}_{z0}', (x1 - x0, .1, z1 - z0), ((x0 + x1) / 2, 2.55, (z0 + z1) / 2), NAVY)
box('wall_left', (.1, 6, 3.2), (-2.6, .5, 1.6), NAVY)
box('skirting', (6, .03, .1), (0, 2.49, .05), NAVY2)
box('sill', (1.25, .3, .06), (-1.7, 2.47, 1.13), WOOD, bevel=.01)
for nm, sz, lc in (('fl', (.07, .06, 1.1), (-2.22, 2.53, 1.7)), ('fr', (.07, .06, 1.1), (-1.18, 2.53, 1.7)), ('ft', (1.1, .06, .07), (-1.7, 2.53, 2.24)),
                   ('fm', (.05, .06, 1.1), (-1.7, 2.53, 1.7)), ('fh', (1.1, .06, .05), (-1.7, 2.53, 1.7))):
    box('frame_' + nm, sz, lc, WOOD)
box('night_sky', (4, .1, 4), (-1.5, 4.6, 2), NIGHT)
ico('moon', .17, 2, (-1.45, 4.5, 2.05), m=MOON)
box('hall', (1.3, 1.9, 2.3), (2.05, 3.55, 1.15), VOID)
hinge = pivot('door_hinge', (1.55, 2.55, 0)); door = box('door', (.98, .05, 2.12), (.49, 0, 1.06), WOOD, parent=hinge, bevel=.01)
box('door_knob', (.04, .06, .04), (.88, -.05, 1.0), WOOD2, parent=hinge)
keys(hinge, 'rotation_euler', 2, [(0, -12), (6.5, -12), (7.6, -21), (DUR, -21)], R(1))
box('nightstand', (.5, .5, .55), (-2.1, 2.15, .275), WOOD, bevel=.015)
lant = cyl('lantern', .1, .1, .26, 6, (-2.1, 2.15, .69), m=LANTERN, jitter=.004)
cyl('lantern_cap', .07, .04, .04, 6, (-2.1, 2.15, .84), m=WOOD2); cyl('lantern_base', .11, .11, .03, 6, (-2.1, 2.15, .565), m=WOOD2)
box('headboard', (.1, 1.05, 1.15), (-1.8, 1.825, .575), WOOD, bevel=.02)
box('footboard', (.1, 1.05, .6), (.95, 1.825, .3), WOOD, bevel=.02)
box('bedframe', (2.75, 1.05, .27), (-.43, 1.825, .285), WOOD, bevel=.015)
box('mattress', (2.65, .95, .16), (-.43, 1.825, .48), SHEET, bevel=.03)
box('pillow', (.5, .62, .1), (-1.42, 1.82, .61), SHEET, bevel=.035, jitter=.006)
quilt = box('quilt', (2.02, 1.0, .22), (-.06, 1.825, .66), QUILT, bevel=.06, jitter=.012, seed=4)
box('quilt_fold', (.16, 1.02, .06), (-1.0, 1.825, .78), SHEET, bevel=.02, jitter=.006)

# ---------------------------------------------------------------- HARU (built standing, origin at the hips, facing -Y)
haru = pivot('haru_root', (0, 0, 0))
for sx in (1, -1): cyl(f'leg_{sx}', .07, .055, .85, 6, (.08 * sx, 0, -.85), m=KIMONO, parent=haru, base=True)
waist = pivot('waist', (0, 0, 0), haru)
torso = cyl('torso', .15, .175, .5, 7, (0, 0, 0), scale=(1, .62, 1), m=KIMONO, parent=waist, base=True, jitter=.004)
for sx in (1, -1): box(f'collar_{sx}', (.025, .012, .26), (.045 * sx, -.108, .38), COLLAR, parent=waist, rot=(0, R(-24 * sx), 0))
box('obi', (.34, .23, .07), (0, 0, .14), mat('obi', (.22, .05, .05)), parent=waist)
neck = pivot('neck', (0, 0, .5), waist, rot=(R(14), 0, 0))
cyl('neck_mesh', .045, .042, .1, 6, (0, 0, -.02), m=SKIN, parent=neck, base=True)
head = pivot('head', (0, 0, .07), neck)
ico('head_mesh', .15, 3, (0, 0, .15), scale=(.95, .92, 1.12), m=SKIN, parent=head)
def hair_cap(bm):                                               # a skull cap with the face cut out
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=.163)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -.03 and v.co.z < .06], context='VERTS')
cap = new_mesh('hair_cap', hair_cap); cap.location = (0, .006, .158); cap.scale = (1.0, .97, 1.12); finish(cap, HAIR, head)
for k, (x, ln) in enumerate(((-.075, .09), (-.035, .12), (.0, .07), (.04, .11), (.08, .085))):     # a few uneven strands over the forehead
    cyl(f'fringe_{k}', .006, .02, ln, 5, (x, -.128 + abs(x) * .25, .292 - ln), rot=(R(-12), 0, 0), m=HAIR, parent=head, base=True, jitter=.002, seed=40 + k)
for sx in (1, -1): cyl(f'side_lock_{sx}', .018, .042, .44, 6, (.128 * sx, -.035, -.17), scale=(1, .6, 1), m=HAIR, parent=head, rot=(0, R(-5 * sx), 0), base=True, jitter=.005, seed=2 + sx)
cyl('back_hair', .16, .135, .66, 7, (0, .045, -.4), scale=(1, .5, 1), m=HAIR, parent=head, base=True, jitter=.01, seed=7)
EYES = []
for sx in (1, -1):
    box(f'lash_{sx}', (.058, .004, .006), (.052 * sx, -.118, .162), BROW, parent=head)   # hidden behind the open eye, shows when it closes
    eye = pivot(f'eye_{sx}', (.052 * sx, -.12, .165), head)
    cyl(f'sclera_{sx}', .03, .03, .012, 10, (0, 0, 0), rot=(R(90), 0, 0), scale=(1, .72, 1), m=EYEW, parent=eye)
    pup = pivot(f'pupil_{sx}', (0, -.007, 0), eye)
    cyl(f'iris_{sx}', .017, .017, .006, 8, (0, 0, 0), rot=(R(90), 0, 0), m=PUPIL, parent=pup)
    ico(f'shine_{sx}', .0045, 1, (.006, -.004, .006), m=SHINE, parent=pup)
    lid = eye                                                    # eyes close by squashing into a line, like the reference
    brow = box(f'brow_{sx}', (.05, .01, .009), (.055 * sx, -.135, .215), BROW, parent=head, rot=(0, R(-8 * sx), 0))
    EYES.append((pup, lid, brow, sx))
cyl('nose', .016, 0, .03, 3, (0, -.148, .125), rot=(R(-80), 0, 0), m=SKIN_D, parent=head)
mouth = box('mouth', (.034, .006, .007), (0, -.135, .068), LIP, parent=head)
for sx in (1, -1):
    sh = pivot(f'shoulder_{sx}', (.175 * sx, 0, .45), waist, rot=(0, R(-6 * sx), 0))
    cyl(f'upperarm_{sx}', .045, .04, .27, 6, (0, 0, -.27), m=KIMONO, parent=sh, base=True)
    el = pivot(f'elbow_{sx}', (0, 0, -.27), sh)
    cyl(f'forearm_{sx}', .04, .05, .24, 6, (0, 0, -.24), m=KIMONO, parent=el, base=True)
    ico(f'hand_{sx}', .038, 1, (0, -.005, -.275), scale=(.8, .55, 1.1), m=SKIN, parent=el)
    if sx == -1: ELBOW_R, SHOULDER_R = el, sh
# lay her down on her back, head to the headboard: local Z -> world -X, local -Y (her front) -> world +Z
haru.matrix_world = Matrix.Translation((-.72, 1.82, .67)) @ Matrix(((0, 0, -1), (1, 0, 0), (0, -1, 0))).to_4x4()

# ---------------------------------------------------------------- THE VISITOR: tall, paper, never blinks
vis = pivot('visitor_root', (1.2, 2.12, 0), rot=(0, 0, R(-24)))
ROBE = mat('robe_paper', (.30, .28, .24), rough=.95, spec=.1)
cyl('v_robe', .4, .17, 1.62, 7, (0, 0, 0), scale=(1, .7, 1), m=ROBE, parent=vis, base=True, jitter=.025, seed=12)
cyl('v_chest', .17, .14, .2, 7, (0, 0, 1.6), scale=(1, .62, 1), m=ROBE, parent=vis, base=True, jitter=.01, seed=13)
vneck = pivot('v_neck', (0, -.01, 1.78), vis, rot=(R(12), 0, 0))
cyl('v_neck_mesh', .035, .03, .3, 6, (0, 0, 0), m=PAPER, parent=vneck, base=True, jitter=.005, seed=14)
vhead = pivot('v_head', (0, 0, .3), vneck, rot=(0, R(-6), 0))
ico('v_head_mesh', .13, 2, (0, 0, .14), scale=(.86, .82, 1.3), m=PAPER, parent=vhead, jitter=.006, seed=15)
ico('v_eye_L', .032, 2, (.044, -.092, .175), scale=(1, .45, 1.3), m=HOLE, parent=vhead)
ico('v_eye_R', .032, 2, (-.046, -.089, .158), scale=(1, .45, 1.35), m=HOLE, parent=vhead)     # a little lower: wrong, not obviously
box('v_mouth', (.115, .02, .012), (0, -.098, .055), HOLE, parent=vhead, rot=(0, R(3), 0))
def veil(bm):                                                    # long black hair: cap + curtain down to the chest, face left open
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=.146)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -.02 and v.co.z < .07], context='VERTS')
vh = new_mesh('v_hair_cap', veil); vh.location = (0, .01, .16); vh.scale = (.92, .9, 1.3); finish(vh, HAIR, vhead)
for sx in (1, -1): box(f'v_hair_side_{sx}', (.05, .1, .62), (.1 * sx, -.02, -.12), HAIR, parent=vhead, jitter=.012, seed=30 + sx)
box('v_hair_back', (.26, .08, .8), (0, .08, -.2), HAIR, parent=vhead, jitter=.015, seed=33)
for sx in (1, -1):
    vsh = pivot(f'v_shoulder_{sx}', (.2 * sx, 0, 1.72), vis, rot=(R(-3), R(-4 * sx), 0))
    cyl(f'v_sleeve_{sx}', .07, .05, .45, 6, (0, 0, -.45), m=ROBE, parent=vsh, base=True, jitter=.01, seed=20 + sx)
    cyl(f'v_arm_{sx}', .028, .022, .62, 5, (0, 0, -1.02), m=PAPER, parent=vsh, base=True, jitter=.004, seed=22 + sx)
    for k in range(4): box(f'v_finger_{sx}_{k}', (.008, .008, .19), ((-.018 + .012 * k) * sx, -.005, -1.11), PAPER, parent=vsh, rot=(R(-3 + k * 2), 0, 0))
keys(vhead, 'rotation_euler', 1, [(0, -6), (17.0, -6), (20.0, -20)], R(1))           # its only movement: a slow tilt at the end

# ---------------------------------------------------------------- Haru's animation
# breathing (torso thickness), stops dead at the footstep
br = [(i * 1.1, 1.0 + (.05 if i % 2 else 0)) for i in range(6)] + [(6.5, 1.0), (DUR, 1.0)]
keys(torso, 'scale', 1, [(t, .62 * v) for t, v in br])
for pup, lid, brow, sx in EYES:
    keys(lid, 'scale', 2, [(0, .04), (4.0, .04), (4.5, .45), (4.8, .15), (5.9, .92), (6.5, .92), (6.8, 1.12), (8.95, 1.12), (9.05, .04), (9.2, 1.12), (DUR, 1.12)])
    keys(pup, 'location', 0, [(0, 0), (6.6, 0), (6.9, -.006), (13.2, -.006), (13.6, 0), (DUR, 0)])     # eyes slide toward the door side
    keys(pup, 'location', 2, [(0, 0), (6.6, 0), (6.9, -.007), (10, -.004), (13.2, 0), (DUR, 0)])
    keys(brow, 'location', 2, [(0, .215), (6.6, .215), (6.9, .224), (DUR, .224)])
    keys(brow, 'rotation_euler', 1, [(0, -8 * sx), (6.6, -8 * sx), (6.9, 10 * sx), (DUR, 10 * sx)], R(1))   # inner ends up: fear
keys(mouth, 'scale', 2, [(0, .007), (6.5, .007), (6.8, .018), (DUR, .018)])                     # lips part
keys(neck, 'rotation_euler', 0, [(0, 14), (7.6, 14), (10.0, 38), (10.2, 38), (13.0, 2), (DUR, 2)], R(1))   # lifts her head to look at the door
keys(head, 'rotation_euler', 2, [(0, 0), (7.6, 0), (10.0, -10), (13.0, 0), (DUR, 0)], R(1))
keys(waist, 'rotation_euler', 0, [(0, 0), (10.2, 0), (11.0, 30), (11.6, 30), (13.0, 86), (DUR, 86)], R(1))   # sits up, a held breath halfway
keys(SHOULDER_R, 'rotation_euler', 0, [(0, 0), (13.6, 0), (14.6, 34), (DUR, 34)], R(1))   # right hand comes up to her chest
keys(ELBOW_R, 'rotation_euler', 0, [(0, 0), (13.6, 0), (14.6, 100), (DUR, 104)], R(1))
keys(ELBOW_R, 'rotation_euler', 1, [(0, 0), (13.6, 0), (14.6, -40), (DUR, -40)], R(1))

# ---------------------------------------------------------------- light
world = bpy.data.worlds.new('night'); scene.world = world
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.003, .005, .012, 1)
def light(name, kind, energy, color, loc, rot=(0, 0, 0), size=1.0, spot=None):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA': L.size = size
    if kind == 'POINT': L.shadow_soft_size = size
    if spot: L.spot_size = R(spot); L.spot_blend = .7
    o = bpy.data.objects.new(name, L); C.objects.link(o); o.location = loc; o.rotation_euler = [R(a) for a in rot]; return o
light('moonlight', 'AREA', 260, (.45, .6, 1.0), (-1.7, 3.4, 2.5), (-48, 0, 12), size=1.0)
lamp = light('lantern_glow', 'POINT', 38, (1.0, .52, .2), (-2.1, 2.1, .72), size=.12)          # the warm key, like a candle
fc = lamp.data.driver_add('energy'); fc.driver.expression = '38 + 3*noise.random()' if False else '38'
lamp.data.keyframe_insert('energy', frame=1)
for i in range(0, FRAMES, 4): lamp.data.energy = 38 * (1 + .06 * math.sin(i * .9) + .04 * math.sin(i * 2.3)); lamp.data.keyframe_insert('energy', frame=i + 1)
lamp.data.driver_remove('energy')
light('rim_warm', 'AREA', 30, (1.0, .5, .25), (-2.4, .8, 1.6), (0, -70, -40), size=1.2)        # warm edge on the left like the reference
light('fill', 'AREA', 6, (.35, .45, .8), (0, -2.5, 2.4), (65, 0, 0), size=3)
light('door_spill', 'AREA', 16, (.5, .6, .95), (.7, 1.75, 1.45), (0, 80, 0), size=.5)
light('visitor_rim', 'SPOT', 4, (.5, .6, .95), (1.0, 3.4, 2.6), (-35, 0, 160), spot=30)

# ---------------------------------------------------------------- camera: close shots, hard cuts, slow pushes
target = pivot('focus', (0, 0, 0))
cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); C.objects.link(cam); scene.camera = cam
tt = cam.constraints.new('TRACK_TO'); tt.target = target; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cd.dof.use_dof = True; cd.dof.focus_object = target; cd.dof.aperture_fstop = 2.0; cd.sensor_width = 36
SHOTS = [  # start, end, camera from -> to, look from -> to, lens from -> to
    (0, 6.5, (-1.0, 1.84, 1.34), (-1.06, 1.84, 1.28), (-1.47, 1.82, .78), (-1.47, 1.82, .78), 42, 50),        # her face, asleep, then waking
    (6.5, 10.1, (-1.02, 1.8, 1.26), (-1.05, 1.8, 1.22), (-1.47, 1.82, .8), (-1.42, 1.82, .84), 62, 72),        # the footstep: tighter
    (10.1, 13.2, (-.45, -.55, 1.0), (-.48, -.5, 1.02), (-.75, 1.82, .95), (-.75, 1.82, 1.15), 32, 34),        # wide side: she sits up
    (13.2, 16.3, (.95, 1.62, 1.5), (.85, 1.64, 1.48), (-.74, 1.82, 1.36), (-.74, 1.82, 1.36), 50, 58),        # from the corner: we are where it stands
    (16.3, DUR, (.3, -1.5, 1.35), (.36, -1.25, 1.38), (.95, 2.05, 1.45), (.98, 2.07, 1.6), 30, 36),           # the reveal
]
for t0, t1, c0, c1, l0, l1, f0, f1 in SHOTS:
    for t, c, l, f in ((t0, c0, l0, f0), (t1 - 1 / FPS, c1, l1, f1)):
        cam.location = c; cam.keyframe_insert('location', frame=F(t)); target.location = l; target.keyframe_insert('location', frame=F(t))
        cd.lens = f; cd.keyframe_insert('lens', frame=F(t))
for ob in (cam, target, cd):                                     # straight lines inside a shot, hard cuts between shots
    ad = ob.animation_data
    if ad and ad.action:
        for fcu in getattr(ad.action, 'fcurves', []):
            for k in fcu.keyframe_points: k.interpolation = 'LINEAR'
        try:
            for layer in ad.action.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        for fcu in cb.fcurves:
                            for k in fcu.keyframe_points: k.interpolation = 'LINEAR'
        except AttributeError: pass

if '--cam' in ARGS:                                              # debug: fixed camera  x,y,z,tx,ty,tz,lens
    v = [float(x) for x in ARGS[ARGS.index('--cam') + 1].split(',')]
    for ob in (cam, target, cd): ob.animation_data_clear()
    cam.location = v[:3]; target.location = v[3:6]; cd.lens = v[6]; cd.dof.use_dof = False

# ---------------------------------------------------------------- render
if '--eevee' in ARGS:
    scene.render.engine = 'BLENDER_EEVEE'
    try: scene.eevee.taa_render_samples = 64; scene.eevee.use_shadows = True
    except Exception: pass
else:
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
    scene.cycles.samples = int(os.environ.get('PV_SAMPLES', 48 if PREVIEW else 128)); scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = (960, 540) if PREVIEW else (1920, 1080)
if os.environ.get('PV_SMALL'): scene.render.resolution_x, scene.render.resolution_y = 640, 360
scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = .3
try: scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
scene.view_settings.exposure = float(os.environ.get('PV_EXPOSURE', 0))
frames_dir = os.path.join(HERE, 'lowpoly_frames_preview' if PREVIEW else 'lowpoly_frames'); os.makedirs(frames_dir, exist_ok=True)
scene.render.filepath = os.path.join(frames_dir, 'f_'); scene.render.image_settings.file_format = 'PNG'
scene.render.use_overwrite = False; scene.render.use_placeholder = True

def write_sound(path):                                  # true silence; one footstep at 6.5 s; a soft paper rustle at 16.2 s
    sr = 48000; n = int(DUR * sr); s = [0.0] * n; rnd = random.Random(3); lp = 0.0
    for j in range(int(.5 * sr)):
        t = j / sr; lp += (rnd.uniform(-1, 1) - lp) * .05
        s[int(6.5 * sr) + j] += .45 * (math.sin(2 * math.pi * (62 + 28 * math.exp(-t * 25)) * t) * math.exp(-t * 13) + lp * math.exp(-((t - .14) / .07) ** 2) * 2.2)
    m = int(1.1 * sr)
    for j in range(m):
        if rnd.random() > .72: s[int(16.2 * sr) + j] += .035 * rnd.uniform(-1, 1) * math.sin(math.pi * j / m)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, v)) * 30000)) for v in s))

if '--frames' in ARGS:
    for fr in [int(x) for x in ARGS[ARGS.index('--frames') + 1].split(',')]:
        scene.frame_set(fr); scene.render.filepath = os.path.join(frames_dir, f'test_{fr:04d}.png'); bpy.ops.render.render(write_still=True)
    sys.exit(0)
wav = os.path.join(HERE, 'paper_visitor_lowpoly.wav'); write_sound(wav)
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
ed.render.filepath = os.path.join(HERE, 'paper_visitor_lowpoly' + ('_preview' if PREVIEW else '') + '.mp4')
with bpy.context.temp_override(scene=ed): bpy.ops.render.render(animation=True)
print('saved', ed.render.filepath)
