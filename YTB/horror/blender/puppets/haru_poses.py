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
    if name in ('hug', 'mouth'):                       # on the floor, knees drawn up
        for sd in ('L', 'R'):
            T('thigh.' + sd, 'X', -120); T('shin.' + sd, 'X', 120)
        rg.pose.bones['root'].location = (0, 0, -hipz(c) + 0.012)
        T('spine', 'X', -12); T('chest', 'X', -8)
        if name == 'hug':
            for sd, g in (('L', 1), ('R', -1)):                # arms forward round the shins, hands meeting
                T('upper_arm.' + sd, 'X', -55); T('upper_arm.' + sd, 'Z', -g * 25); T('forearm.' + sd, 'X', -25)
        else:                                          # both hands up over her mouth
            for sd, g in (('L', 1), ('R', -1)):                # elbows out and down, forearms up, hands over her mouth
                T('upper_arm.' + sd, 'X', -88); T('upper_arm.' + sd, 'Z', -g * 20); T('upper_arm.' + sd, 'Y', g * -64)
                T('forearm.' + sd, 'X', -112); T('hand.' + sd, 'Z', -g * 80)   # solved: elbows out and low, hands over her mouth
            T('head', 'X', -6)
    elif name == 'sit':
        for sd in ('L', 'R'):
            T('thigh.' + sd, 'X', -85); T('shin.' + sd, 'X', 85)
            T('upper_arm.' + sd, 'X', -25); T('forearm.' + sd, 'X', -35)
        rg.pose.bones['root'].location = (0, 0, -(hipz(c) - seat))
    elif name == 'lie':
        rg.rotation_euler = (math.radians(-90), 0, rg.rotation_euler.z)
        rg.pose.bones['root'].location = (0, 0, 0)
    elif name == 'point':
        CK.relax(rg); T('upper_arm.R', 'X', -70); T('forearm.R', 'X', -10)
    if extra:
        for (b, ax), d in extra.items(): T(b, ax, d)
    if f is not None: key(rg, f)
