"""Bake the Mixamo clips into one small file the scenes can read fast: for every frame and every bone Haru uses, the bone's
rotation away from its rest pose (world space), plus the hips position; and each bone's rest direction.
blender -b -P mocap/bake_clips.py   ->  mocap/clips.npz
"""
import bpy, os, glob
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BONES = ['Hips', 'Spine1', 'Spine2', 'Neck', 'Head',
         'LeftArm', 'LeftForeArm', 'LeftHand', 'RightArm', 'RightForeArm', 'RightHand',
         'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'RightUpLeg', 'RightLeg', 'RightFoot']
out = {}
for path in sorted(glob.glob(os.path.join(HERE, 'mixamo', '*.fbx'))):
    name = os.path.splitext(os.path.basename(path))[0]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    f0, f1 = map(int, arm.animation_data.action.frame_range)
    Mw = arm.matrix_world.copy(); sc = bpy.context.scene
    rest = {}
    for b in BONES:
        bone = arm.data.bones['mixamorig:' + b]
        rest[b] = (Mw @ bone.matrix_local).to_3x3().normalized()
        if name not in ('_',) and 'rest_dir/' + b not in out:
            out['rest_dir/' + b] = np.array((Mw @ bone.tail_local - Mw @ bone.head_local).normalized())
    if 'rest_hips' not in out: out['rest_hips'] = np.array(Mw @ arm.data.bones['mixamorig:Hips'].head_local)
    Q = np.zeros((f1 - f0 + 1, len(BONES), 4)); H = np.zeros((f1 - f0 + 1, 3))
    for i, f in enumerate(range(f0, f1 + 1)):
        sc.frame_set(f)
        for j, b in enumerate(BONES):
            pb = arm.pose.bones['mixamorig:' + b]
            D = (Mw @ pb.matrix).to_3x3().normalized() @ rest[b].inverted()
            Q[i, j] = D.to_quaternion()
        H[i] = Mw @ arm.pose.bones['mixamorig:Hips'].head
    for j in range(1, len(Q)):                   # keep quaternions on one hemisphere so they blend smoothly
        flip = (Q[j] * Q[j - 1]).sum(-1) < 0; Q[j][flip] *= -1
    out[name + '/q'] = Q; out[name + '/hips'] = H
    print('BAKED', name, Q.shape, flush=True)
out['bones'] = np.array(BONES)
np.savez_compressed(os.path.join(HERE, 'clips.npz'), **out)
print('SAVED', len(out))
