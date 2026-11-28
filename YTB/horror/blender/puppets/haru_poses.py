"""Story poses for the kit-rigged characters (cast_kit.character / cast_kit.haru). apply(c, name, f, ...) resets the
rig to rest, then sets the pose (and keys it on frame f when f is given). Names: rest, stand, hug (on the floor, knees
up, arms round the shins), sit (on a seat of height `seat`), mouth (hugging her knees, both hands over her mouth),
lie (on her back), point (standing, right arm out holding a torch)."""
import math
import cast_kit as CK

BONES = ('hips', 'spine', 'chest', 'neck', 'head', 'thigh.L', 'thigh.R', 'shin.L', 'shin.R', 'foot.L', 'foot.R',
         'upper_arm.L', 'upper_arm.R', 'forearm.L', 'forearm.R', 'hand.L', 'hand.R')


def reset(rg):
    for n in BONES:
        pb = rg.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0)
    rg.pose.bones['root'].location = (0, 0, 0)
    rg.rotation_euler = (0, 0, rg.rotation_euler.z)


def key(rg, f):
    for n in BONES: rg.pose.bones[n].keyframe_insert('rotation_quaternion', frame=f)
    rg.pose.bones['root'].keyframe_insert('location', frame=f)
    rg.keyframe_insert('rotation_euler', frame=f); rg.keyframe_insert('location', frame=f)


def hipz(c):
    return CK.JOINTS['hip'] * (c.get('neck_h') or max(v.co.z for v in c['body'].data.vertices))


def apply(c, name, f=None, seat=0.034, extra=None):
    rg = c['rig']; reset(rg); T = lambda b, ax, d: CK.turn(rg, b, ax, d)
    if name != 'point': CK.relax(rg)
    if name in ('hug', 'mouth'):                       # on the floor, knees drawn up, curled forward over them
        for sd in ('L', 'R'):
            T('thigh.' + sd, 'X', -120); T('shin.' + sd, 'X', 120)
        rg.pose.bones['root'].location = (0, 0, -hipz(c) + 0.012)
        # sitting up over her hips (+ about X leans forward, a negative turn tips her back; in the 7 cm tent her head
        # must stay over her hips for the close-ups). Arms solved against her knees / her mouth for this posture:
        # (upper_arm X, Z, Y, forearm X, hand Z) per side
        if name == 'hug':                              # clutching her knees (her arms are too short to wrap the shins)
            T('spine', 'X', 3); T('chest', 'X', 2); T('head', 'X', -2)
            arms = (('L', 1, (0, 39, 0, -70, 62)), ('R', -1, (0, 39, 0, -70, 62)))
        else:                                          # right palm flat on her mouth, left hand pressed over it (layered)
            T('spine', 'X', 2); T('chest', 'X', 2); T('head', 'X', 4)
            arms = (('R', -1, (-84, 12, -90, -118, 58)), ('L', 1, (-84, 21, -90, -127, 0)))
        for sd, g, (ux, uz, uy, fx, hz) in arms:
            T('upper_arm.' + sd, 'X', ux); T('upper_arm.' + sd, 'Z', -g * uz); T('upper_arm.' + sd, 'Y', g * uy)
            T('forearm.' + sd, 'X', fx); T('hand.' + sd, 'Z', -g * hz)
    elif name == 'sit':
        for sd in ('L', 'R'):
            T('thigh.' + sd, 'X', -85); T('shin.' + sd, 'X', 85)
        for sd, g in (('L', 1), ('R', -1)):                # solved: palms resting on her thighs, just behind the knees
            T('upper_arm.' + sd, 'X', -10); T('upper_arm.' + sd, 'Z', -g * 33); T('forearm.' + sd, 'X', -15)
        rg.pose.bones['root'].location = (0, 0, -(hipz(c) - seat))
    elif name == 'lie':
        rg.rotation_euler = (math.radians(-90), 0, rg.rotation_euler.z)
        rg.pose.bones['root'].location = (0, 0, 0)
    elif name == 'point':
        CK.relax(rg); T('upper_arm.R', 'X', -70); T('forearm.R', 'X', -10)
    if extra:
        for (b, ax), d in extra.items(): T(b, ax, d)
    if f is not None: key(rg, f)
