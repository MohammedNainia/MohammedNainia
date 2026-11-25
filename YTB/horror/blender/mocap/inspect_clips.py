"""Print what each Mixamo clip holds: frames, fps, bones, how far the hips travel and how high they ride.
blender -b -P mocap/inspect_clips.py"""
import bpy, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))
for i, path in enumerate(sorted(glob.glob(os.path.join(HERE, 'mixamo', '*.fbx')))):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False)
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    act = arm.animation_data.action
    f0, f1 = act.frame_range
    sc = bpy.context.scene
    hips = arm.pose.bones[next(b.name for b in arm.pose.bones if b.name.endswith('Hips'))]
    pts = []
    for f in (int(f0), int((f0 + f1) / 2), int(f1)):
        sc.frame_set(f); pts.append((arm.matrix_world @ hips.head).to_tuple(3))
    if i == 0:
        print('BONES', [b.name for b in arm.data.bones])
        print('SCALE', arm.scale[:], 'fps', sc.render.fps)
    print('CLIP', os.path.basename(path), 'frames', f0, f1, 'hips start/mid/end', pts)
