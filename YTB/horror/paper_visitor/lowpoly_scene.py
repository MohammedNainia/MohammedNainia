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
def ico(name, r, sub, loc, scale=(1, 1, 1), m=None, parent=None, jitter=0.0, seed=1, rot=(0, 0, 0)):
    ob = new_mesh(name, lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r))
    ob.location = loc; ob.scale = scale; ob.rotation_euler = rot; return finish(ob, m, parent, jitter, seed)
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
SKIN, SKIN_D = mat('skin', (.92, .5, .3), rough=.7, spec=.2), mat('skin_dark', (.74, .42, .3))
HAIR, VHAIR = mat('hair', (.05, .028, .02), rough=.55, spec=.35), mat('vhair', (.008, .008, .01), rough=.5, spec=.3)
KIMONO, KIMONO_D, COLLAR = mat('hoodie', (.85, .55, .08), rough=.85), mat('hoodie_dark', (.62, .36, .04), rough=.85), mat('collar', (.70, .64, .55))
EYEW, PUPIL, SHINE = mat('eye_white', (.6, .58, .54), rough=.45), mat('pupil', (.006, .005, .005), rough=.35, spec=.3), mat('shine', (1, 1, 1), emit=2)
LIP, BROW = mat('lip', (.10, .035, .03)), mat('brow', (.02, .015, .015))
PAPER = mat('paper', (.80, .76, .67), rough=.9, spec=.15)
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
box('night_sky', (30, .1, 16), (-1.5, 16, 6), NIGHT)
ico('moon', .55, 2, (-3.0, 15.5, 7.5), m=MOON)
rc = random.Random(9)
for b_ in range(9):                                                   # dark towers with lit windows far outside
    bx, by, bw, bh = -6.5 + b_ * 1.5 + rc.uniform(-.3, .3), 8 + rc.uniform(0, 5), rc.uniform(.8, 1.4), rc.uniform(3, 8)
    box(f'tower_{b_}', (bw, .4, bh), (bx, by, bh / 2), mat('tower', (.012, .016, .03)))
    for w_ in range(14):
        if rc.random() < .55:
            col = rc.choice([(1, .7, .35), (1, .8, .5), (.5, .8, 1), (1, .35, .25)])
            box(f'win_{b_}_{w_}', (.16, .02, .2), (bx + rc.uniform(-bw / 2 + .15, bw / 2 - .15), by - .22, rc.uniform(1, bh - .3)), mat(f'winlight_{col}', col, emit=rc.choice([3, 5, 8])))
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

# ---------------------------------------------------------------- a lived-in bedroom
CLOTH, CLOTH2 = mat('curtain', (.32, .28, .22), rough=.9), mat('rug', (.22, .07, .05), rough=.95)
RUGB, BOOKS = mat('rug_border', (.40, .30, .18), rough=.95), [mat(f'book{i}', c) for i, c in enumerate(((.25, .06, .05), (.07, .12, .2), (.32, .26, .12), (.1, .16, .1), (.35, .33, .3)))]
GLASS, PHOTO, PLUSH = mat('mirror', (.02, .025, .035), rough=.05, spec=1), mat('photo', (.42, .38, .32)), mat('plush', (.55, .45, .38), rough=.95)
# curtains, half drawn, a little crumpled
for nm, x in (('l', -2.36), ('r', -1.04)):
    for k in range(3): box(f'curtain_{nm}{k}', (.09, .04, 1.55), (x + (k - 1) * .075, 2.42 - (k % 2) * .03, 1.53), CLOTH, jitter=.012, seed=50 + k)
box('curtain_rod', (1.7, .03, .03), (-1.7, 2.42, 2.33), WOOD2)
# rug beside the bed, slippers on it
box('rug', (1.7, .95, .012), (-.35, .82, .006), RUGB, bevel=.004); box('rug_in', (1.5, .78, .014), (-.35, .82, .007), CLOTH2)
for k, dx in enumerate((-.06, .07)): box(f'slipper_{k}', (.24, .09, .05), (-.55 + dx * 2, 1.12 + dx * .3, .03), mat('slipper', (.45, .4, .33)), rot=(0, 0, R(8 + k * 14)), bevel=.02)
# shelf over the bed with books, a photo frame and a small plush
box('shelf', (1.2, .2, .03), (-.6, 2.4, 1.62), WOOD, bevel=.005)
x = -1.15
for i in range(9):
    w = .035 + (i * 7 % 5) * .006; h = .16 + (i * 3 % 4) * .025
    box(f'book_{i}', (w, .15, h), (x, 2.4, 1.635 + h / 2), BOOKS[i % 5], rot=(0, R(10) if i == 8 else 0, 0)); x += w + .006
box('photo_frame', (.16, .02, .2), (-.35, 2.42, 1.74), WOOD2, rot=(R(-8), 0, 0)); box('photo', (.12, .022, .155), (-.35, 2.415, 1.74), PHOTO, rot=(R(-8), 0, 0))
ico('plush_body', .055, 1, (-.12, 2.38, 1.69), scale=(1, .9, 1.1), m=PLUSH); ico('plush_head', .045, 1, (-.12, 2.37, 1.78), m=PLUSH)
for sx in (1, -1): cyl(f'plush_ear_{sx}', .015, .008, .07, 5, (-.12 + .022 * sx, 2.37, 1.85), m=PLUSH, base=True)
# a framed picture and a calendar on the back wall
box('frame_big', (.5, .03, .38), (.35, 2.49, 1.55), WOOD2); box('picture', (.42, .032, .3), (.35, 2.485, 1.55), mat('picture', (.07, .09, .1)))
box('calendar', (.24, .01, .32), (1.2, 2.495, 1.55), mat('calendar', (.6, .57, .5)))
# desk and chair against the left wall, a school bag, a desk lamp that is off
box('desk_top', (.6, 1.1, .04), (-2.27, .35, .74), WOOD, bevel=.008)
for dx, dy in ((-.27, -.5), (-.27, .5), (.27, -.5), (.27, .5)): box(f'desk_leg_{dx}_{dy}', (.04, .04, .72), (-2.27 + dx, .35 + dy, .36), WOOD2)
box('desk_drawer', (.5, .5, .16), (-2.27, .6, .62), WOOD2, bevel=.005)
for k in range(3): box(f'desk_book_{k}', (.22, .3, .035), (-2.3, .1, .78 + k * .036), BOOKS[k], rot=(0, 0, R(k * 7)))
cyl('lamp_base', .07, .07, .02, 8, (-2.38, .7, .77), m=WOOD2, base=True); cyl('lamp_arm', .012, .012, .35, 6, (-2.38, .7, .78), rot=(0, R(-15), 0), m=WOOD2, base=True)
cyl('lamp_shade', .08, .03, .1, 8, (-2.29, .7, 1.1), rot=(0, R(-60), 0), m=mat('shade', (.35, .3, .25)))
chair = pivot('chair', (-1.85, .35, 0), rot=(0, 0, R(-100)))
box('chair_seat', (.42, .42, .04), (0, 0, .45), WOOD, parent=chair, bevel=.005)
box('chair_back', (.42, .04, .45), (0, .2, .7), WOOD, parent=chair, bevel=.005)
for dx, dy in ((-.18, -.18), (-.18, .18), (.18, -.18), (.18, .18)): box(f'chair_leg_{dx}_{dy}', (.035, .035, .45), (dx, dy, .225), WOOD2, parent=chair)
box('jacket', (.4, .07, .38), (0, .23, .6), mat('jacket', (.12, .13, .16)), parent=chair, jitter=.015, seed=61)
box('bag', (.3, .16, .34), (-1.6, -.05, .17), mat('bag', (.18, .1, .07)), rot=(0, 0, R(20)), bevel=.03, jitter=.01)
# wardrobe and a dark mirror on the far right, past the door
box('wardrobe', (.85, .6, 2.1), (3.05, 2.2, 1.05), WOOD, bevel=.01)
box('wardrobe_split', (.01, .62, 2.0), (3.05, 2.2, 1.05), WOOD2)
for sx in (1, -1): box(f'wardrobe_knob_{sx}', (.02, .03, .1), (3.05 + .04 * sx, 1.89, 1.05), WOOD2)
box('mirror_frame', (.5, .04, .9), (2.4, -.2, 1.45), WOOD2, rot=(0, 0, R(90))); box('mirror', (.42, .045, .82), (2.4, -.2, 1.45), GLASS, rot=(0, 0, R(90)))
box('wall_right', (.1, 6, 3.2), (2.6 + .05, .5, 1.6), NAVY) if False else None
# clothes on the floor in the dark corner
box('clothes_pile', (.4, .3, .1), (2.2, 1.0, .05), mat('clothes', (.2, .18, .22)), jitter=.03, seed=70)

# ---------------------------------------------------------------- HARU (built standing, origin at the hips, facing -Y)
# style from the reference: big round head, tiny black dot eyes with one highlight (no whites), small mouth, big smooth hair, chunky clothes
haru = pivot('haru_root', (0, 0, 0))
for sx in (1, -1): cyl(f'leg_{sx}', .075, .06, .85, 10, (.085 * sx, 0, -.85), m=KIMONO, parent=haru, base=True)
waist = pivot('waist', (0, 0, 0), haru)
torso = cyl('torso', .17, .2, .5, 12, (0, 0, 0), scale=(1, .7, 1), m=KIMONO, parent=waist, base=True, jitter=.004)
box('shirt', (.075, .02, .3), (0, -.132, .32), mat('shirt', (.03, .03, .035)), parent=waist)                 # dark top under the open hoodie
for sx in (1, -1): box(f'zip_edge_{sx}', (.03, .03, .5), (.055 * sx, -.128, .24), KIMONO_D, parent=waist, rot=(0, R(-7 * sx), 0))
cyl('collar_ring', .115, .12, .07, 12, (0, 0, .46), scale=(1, .8, 1), m=KIMONO_D, parent=waist, base=True)
neck = pivot('neck', (0, 0, .5), waist, rot=(R(14), 0, 0))
cyl('neck_mesh', .05, .048, .08, 10, (0, 0, -.02), m=SKIN, parent=neck, base=True)
head = pivot('head', (0, 0, .06), neck)
ico('head_mesh', .17, 4, (0, 0, .16), scale=(1.05, .98, .97), m=SKIN, parent=head)
def hair_cap(bm):                                               # one smooth mass: round on top, falling long at the sides and back, open in front of the face
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=.186)
    for v in bm.verts:
        if v.co.z < 0: v.co.z *= 3.2; v.co.x *= 1.0 + .25 * min(1, -v.co.z / .5)          # longer and a little wider toward the ends
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -.035 and v.co.z < .06 - .3 * max(0, -v.co.x)], context='VERTS')   # side part: hair dips over one eye-brow
cap = new_mesh('hair_cap', hair_cap); cap.location = (0, .02, .17); cap.scale = (1.07, 1.0, 1.0); finish(cap, HAIR, head)
EYES = []
for sx in (1, -1):
    eye = pivot(f'eye_{sx}', (.066 * sx, -.151, .132), head, rot=(0, 0, R(20 * sx)))
    ico(f'eye_dot_{sx}', .014, 2, (0, 0, 0), scale=(.75, .45, 1.25), m=PUPIL, parent=eye)
    shine = ico(f'shine_{sx}', .0036, 1, (.0035, -.0068, .0075), m=SHINE, parent=eye)
    EYES.append((eye, sx, shine, eye.location.copy()))
cyl('nose', .008, 0, .014, 3, (0, -.166, .108), rot=(R(-80), 0, 0), m=SKIN_D, parent=head)
mouth = box('mouth', (.022, .006, .006), (0, -.158, .073), LIP, parent=head)
for sx in (1, -1):
    sh = pivot(f'shoulder_{sx}', (.2 * sx, 0, .44), waist, rot=(0, R(-6 * sx), 0))
    cyl(f'upperarm_{sx}', .065, .06, .27, 10, (0, 0, -.27), m=KIMONO, parent=sh, base=True)
    el = pivot(f'elbow_{sx}', (0, 0, -.27), sh)
    cyl(f'forearm_{sx}', .058, .065, .23, 10, (0, 0, -.23), m=KIMONO, parent=el, base=True)
    ico(f'hand_{sx}', .045, 2, (0, -.005, -.27), scale=(.85, .6, 1.05), m=SKIN, parent=el)
    if sx == -1: ELBOW_R, SHOULDER_R = el, sh
# lay her down on her back, head to the headboard: local Z -> world -X, local -Y (her front) -> world +Z
haru.matrix_world = Matrix.Translation((-.7, 1.82, .69)) @ Matrix(((0, 0, -1), (1, 0, 0), (0, -1, 0))).to_4x4()

# ---------------------------------------------------------------- THE VISITOR: tall, paper, never blinks
vis = pivot('visitor_root', (1.2, 2.12, 0), rot=(0, 0, R(-24)))
ROBE = mat('robe_paper', (.30, .28, .24), rough=.95, spec=.1)
cyl('v_robe', .4, .17, 1.62, 7, (0, 0, 0), scale=(1, .7, 1), m=ROBE, parent=vis, base=True, jitter=.025, seed=12)
cyl('v_chest', .17, .14, .2, 7, (0, 0, 1.6), scale=(1, .62, 1), m=ROBE, parent=vis, base=True, jitter=.01, seed=13)
vneck = pivot('v_neck', (0, -.01, 1.78), vis, rot=(R(12), 0, 0))
cyl('v_neck_mesh', .035, .03, .3, 6, (0, 0, 0), m=PAPER, parent=vneck, base=True, jitter=.005, seed=14)
vhead = pivot('v_head', (0, 0, .3), vneck, rot=(0, R(-6), 0))
ico('v_head_mesh', .15, 4, (0, 0, .16), scale=(.9, .9, 1.22), m=PAPER, parent=vhead)
ico('v_eye_L', .02, 2, (.07, -.122, .14), scale=(.8, .45, 1.45), rot=(0, 0, R(22)), m=HOLE, parent=vhead)     # the same dot eyes, but no light in them
ico('v_eye_R', .02, 2, (-.072, -.12, .128), scale=(.8, .45, 1.5), rot=(0, 0, R(-22)), m=HOLE, parent=vhead)  # a little lower: wrong, not obviously
box('v_mouth', (.06, .006, .004), (0, -.133, .06), HOLE, parent=vhead)
def veil(bm):                                                    # long straight black hair, face left open
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=.162)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -.03 and v.co.z < .09], context='VERTS')
vh = new_mesh('v_hair_cap', veil); vh.location = (0, .012, .17); vh.scale = (.93, .93, 1.22); finish(vh, VHAIR, vhead)
for sx in (1, -1): cyl(f'v_hair_side_{sx}', .03, .06, .78, 8, (.13 * sx, -.03, -.55), scale=(1, .7, 1), m=VHAIR, parent=vhead, base=True)
cyl('v_hair_back', .17, .16, .95, 12, (0, .06, -.72), scale=(1, .4, 1), m=VHAIR, parent=vhead, base=True)
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
for eye, sx, shine, base in EYES:
    EYE_K = [(0, .12), (4.0, .12), (4.5, .5), (4.8, .2), (5.9, .95), (6.5, .95), (6.8, 1.0), (8.95, 1.0), (9.05, .12), (9.2, 1.0), (DUR, 1.0)]
    keys(eye, 'scale', 2, EYE_K)                                          # shut = a short dark line, like the reference blink
    for ax in range(3): keys(shine, 'scale', ax, [(t, 1.0 if v > .3 else 0.0) for t, v in EYE_K])   # no glint on a closed eye
    keys(eye, 'location', 0, [(0, base.x), (6.6, base.x), (6.9, base.x - .005), (13.2, base.x - .005), (13.6, base.x), (DUR, base.x)])   # both dots slide toward the door
    keys(eye, 'location', 2, [(0, base.z), (6.6, base.z), (6.9, base.z - .004), (10, base.z - .003), (13.2, base.z), (DUR, base.z)])
    for ax in (0, 1): keys(eye, 'scale', ax, [(0, 1), (6.6, 1), (6.9, .82), (DUR, .82)])                # fear: the dots shrink
keys(mouth, 'scale', 2, [(0, .006), (6.5, .006), (6.8, .014), (DUR, .014)])                     # lips part
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
lamp = light('lantern_glow', 'POINT', 70, (1.0, .52, .2), (-2.1, 2.1, .72), size=.12)          # the warm key, like a candle
fc = lamp.data.driver_add('energy'); fc.driver.expression = '38 + 3*noise.random()' if False else '38'
lamp.data.keyframe_insert('energy', frame=1)
for i in range(0, FRAMES, 4): lamp.data.energy = 70 * (1 + .06 * math.sin(i * .9) + .04 * math.sin(i * 2.3)); lamp.data.keyframe_insert('energy', frame=i + 1)
lamp.data.driver_remove('energy')
light('rim_warm', 'AREA', 45, (1.0, .5, .22), (-2.4, .8, 1.6), (0, -70, -40), size=1.2)
fk = light('face_key', 'AREA', 26, (1.0, .6, .36), (-.25, 1.35, 1.65), size=.5)   # warm key that follows her face (the reference's screen glow)
tk = fk.constraints.new('TRACK_TO'); tk.target = bpy.data.objects['head']; tk.track_axis = 'TRACK_NEGATIVE_Z'; tk.up_axis = 'UP_Y'        # warm edge on the left like the reference
light('fill', 'AREA', 10, (.35, .45, .8), (0, -2.5, 2.4), (65, 0, 0), size=3)
light('door_spill', 'AREA', 16, (.5, .6, .95), (.7, 1.75, 1.45), (0, 80, 0), size=.5)
light('visitor_rim', 'SPOT', 4, (.5, .6, .95), (1.0, 3.4, 2.6), (-35, 0, 160), spot=30)

# ---------------------------------------------------------------- camera: close shots, hard cuts, slow pushes
target = pivot('focus', (0, 0, 0))
cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); C.objects.link(cam); scene.camera = cam
tt = cam.constraints.new('TRACK_TO'); tt.target = target; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cd.dof.use_dof = True; cd.dof.focus_object = target; cd.dof.aperture_fstop = 1.4; cd.sensor_width = 36
SHOTS = [  # start, end, camera from -> to, look from -> to, lens from -> to
    (0, 6.5, (-1.0, 1.84, 1.34), (-1.06, 1.84, 1.28), (-1.47, 1.82, .8), (-1.47, 1.82, .8), 34, 40),        # her face, asleep, then waking
    (6.5, 10.1, (-1.02, 1.8, 1.26), (-1.05, 1.8, 1.22), (-1.47, 1.82, .82), (-1.42, 1.82, .85), 44, 52),        # the footstep: tighter
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
