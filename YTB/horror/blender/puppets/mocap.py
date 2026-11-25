"""Drive the rigid-piece Haru puppet with Mixamo motion capture (baked by mocap/bake_clips.py into mocap/clips.npz).

Each Mixamo bone's rotation away from its rest pose (world space) is applied to Haru's matching pivot. Where the two rest
poses differ (Mixamo stands in a T-pose, Haru's arms hang in an A-pose) the limb is first turned so its rest direction
matches Mixamo's, so a raised arm points where the actor's arm pointed. The hips travel is scaled by the ratio of hip
heights, so her steps cover the ground her shorter legs would (no sliding).

    lib = Library(path, puppet)
    W, hips = lib.sample('sneak_walk', t_clip, mirror=False, loop=True)     # world rotations per pivot, hips position (m)
    apply(puppet, rotate(W, yaw))                                           # sets every pivot's local rotation
"""
import math
import numpy as np
from mathutils import Quaternion, Vector

FPS = 30
MAP = {'hips': 'Hips', 'spine': 'Spine1', 'chest': 'Spine2', 'neck': 'Neck', 'head': 'Head'}
for t, s in (('L', 'Left'), ('R', 'Right')):
    MAP.update({f'upper_arm.{t}': f'{s}Arm', f'forearm.{t}': f'{s}ForeArm', f'hand.{t}': f'{s}Hand',
                f'thigh.{t}': f'{s}UpLeg', f'shin.{t}': f'{s}Leg', f'foot.{t}': f'{s}Foot'})
LIMB = {'upper_arm': ('upper_arm', 'forearm'), 'forearm': ('forearm', 'hand'), 'hand': ('forearm', 'hand'),
        'thigh': ('thigh', 'shin'), 'shin': ('shin', 'foot')}
swap = lambda b: b.replace('Left', '#').replace('Right', 'Left').replace('#', 'Right')


class Library:
    def __init__(self, path, puppet):
        d = np.load(path)
        self.idx = {str(b): i for i, b in enumerate(d['bones'])}
        self.clips = {k[:-2]: (d[k], d[k[:-2] + '/hips']) for k in d.files if k.endswith('/q')}
        self.k = puppet.rest['hips'].z / float(d['rest_hips'][2])          # Mixamo metres -> puppet metres
        self.A = {}
        for pv, bone in MAP.items():
            base = pv.split('.')[0]
            if base in LIMB:
                tag = '.' + pv.split('.')[1]; a, b = LIMB[base]
                dh = (puppet.rest[b + tag] - puppet.rest[a + tag]).normalized()
                dm = Vector(d['rest_dir/' + bone])
                self.A[pv] = dh.rotation_difference(dm)
            else:
                self.A[pv] = Quaternion()

    def length(self, clip):
        return (len(self.clips[clip][0]) - 1) / FPS

    def hips(self, clip, c, mirror=False, loop=False):
        Q, H = self.clips[clip]; n = len(H); T = (n - 1) / FPS; cyc = 0
        if loop: cyc = math.floor(c / T); c -= cyc * T
        x = min(max(c, 0.0), T) * FPS; i = min(int(x), n - 2); u = x - i
        p = Vector(H[i] * (1 - u) + H[i + 1] * u) + cyc * (Vector(H[-1]) - Vector(H[0]))
        if mirror: p.x = -p.x
        return p

    def sample(self, clip, c, mirror=False, loop=False):
        """world rotation of every pivot (facing -y, before the scene's yaw) and the hips position, at clip time c (s)"""
        Q, H = self.clips[clip]; n = len(Q); T = (n - 1) / FPS
        cc = c - math.floor(c / T) * T if loop else c
        x = min(max(cc, 0.0), T) * FPS; i = min(int(x), n - 2); u = x - i
        W = {}
        for pv, bone in MAP.items():
            j = self.idx[swap(bone) if mirror else bone]
            q = Quaternion(Q[i, j]).slerp(Quaternion(Q[i + 1, j]), u)
            if mirror: q = Quaternion((q.w, q.x, -q.y, -q.z))
            W[pv] = q @ self.A[pv]
        return W, self.hips(clip, c, mirror, loop)


def rotate(W, yaw):
    R = Quaternion((0, 0, 1), yaw)
    return {k: R @ q for k, q in W.items()}


def blend(Wa, Wb, k):
    out = {}
    for pv in Wa:
        a, b = Wa[pv], Wb[pv]
        if a.dot(b) < 0: b = -b
        out[pv] = a.slerp(b, k)
    return out


def apply(puppet, W, yaw):
    """set each pivot's local rotation from world rotations W (the root carries only the yaw)"""
    R = Quaternion((0, 0, 1), yaw)
    for pv, e in puppet.P.items():
        if pv == 'root' or pv not in W: continue
        par = e.parent.name[len(puppet.name) + 1:]
        pw = R if par == 'root' else W[par]
        e.rotation_euler = (pw.inverted() @ W[pv]).to_euler('YXZ')
