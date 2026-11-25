"""Timeline of a few clips: hips height and torso tilt every 10 frames, to find where she is lying, sitting, standing.
blender -b -P mocap/phases.py"""
import bpy, os, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for name in ('lie_awake_lookaround', 'getup_from_back', 'standing_up', 'stand_to_sit', 'sit_to_stand', 'scared_out_of_seat',
             'jump_onto_platform', 'terrified', 'sit_look_side'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(HERE, 'mixamo', name + '.fbx'))
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    f0, f1 = map(int, arm.animation_data.action.frame_range); sc = bpy.context.scene
    P = lambda b: arm.matrix_world @ arm.pose.bones['mixamorig:' + b].head
    rows = []
    for f in range(f0, f1 + 1, 10):
        sc.frame_set(f); hp, hd = P('Hips'), P('Head')
        up = (hd - hp).normalized(); tilt = math.degrees(math.acos(max(-1, min(1, up.z))))
        rows.append(f'{f}:z{hp.z:.2f} t{tilt:.0f} h({hd.x - hp.x:+.2f},{hd.y - hp.y:+.2f})')
    print('PH', name, ' | '.join(rows))
