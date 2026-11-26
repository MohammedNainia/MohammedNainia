---
name: dolly-rotate
description: Camera moves forward while rotating around the product. More dynamic than a straight zoom.
---

## Dolly + Rotate Camera Animation

Camera dollies forward while simultaneously rotating around the product, creating a dynamic sweeping reveal that's more engaging than a straight zoom or static orbit.

## When to Use

- User wants a "dynamic" or "sweeping" shot
- User says "dolly", "move and rotate", "sweeping reveal"
- More cinematic than a simple turntable

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | `5` | Video length in seconds |
| `fps` | `24` | Frames per second |
| `rotation_degrees` | `90` | How far to rotate during the dolly |
| `start_distance` | `4.0` | Starting distance |
| `end_distance` | `2.5` | Ending distance |
| `start_height` | `2.0` | Starting height |
| `end_height` | `1.5` | Ending height |

## Flow

### Step 1: Set Up Camera Rig

```python
import bpy, math

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0.05))
tgt = bpy.context.active_object
tgt.name = 'DollyTarget'

bpy.ops.object.camera_add(location=(2.5, -START_DISTANCE, START_HEIGHT))
cam = bpy.context.active_object
cam.name = 'DollyCam'
cam.data.lens = 40

trk = cam.constraints.new(type='TRACK_TO')
trk.target = tgt
trk.track_axis = 'TRACK_NEGATIVE_Z'
trk.up_axis = 'UP_Y'

# Parent camera to target for orbital rotation
bpy.ops.object.select_all(action='DESELECT')
cam.select_set(True)
tgt.select_set(True)
bpy.context.view_layer.objects.active = tgt
bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

bpy.context.scene.camera = cam
```

### Step 2: Animate Dolly + Rotation

```python
TOTAL_FRAMES = DURATION * FPS

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES
scene.render.fps = FPS

# Frame 1: start position
tgt.rotation_euler = (0, 0, 0)
tgt.keyframe_insert(data_path='rotation_euler', frame=1)
cam.location = (2.5, -START_DISTANCE, START_HEIGHT)
cam.keyframe_insert(data_path='location', frame=1)
cam.data.lens = 40
cam.data.keyframe_insert(data_path='lens', frame=1)

# End: rotated + closer
tgt.rotation_euler = (0, 0, math.radians(ROTATION_DEGREES))
tgt.keyframe_insert(data_path='rotation_euler', frame=TOTAL_FRAMES)
cam.location = (1.5, -END_DISTANCE, END_HEIGHT)
cam.keyframe_insert(data_path='location', frame=TOTAL_FRAMES)
cam.data.lens = 50
cam.data.keyframe_insert(data_path='lens', frame=TOTAL_FRAMES)

# Default BEZIER interpolation for smooth cinematic feel
```

### Step 3: Render + Encode

Same as turntable — PNG sequence with Cycles, encode to ProRes 4444.

```bash
ffmpeg -y -framerate 24 \
  -i "~/Desktop/Blender Videos/dolly_rotate_frames/%04d.png" \
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le \
  "~/Desktop/Blender Videos/dolly_rotate.mov"
```

## Using it in our horror house (YTB/horror/blender)

Source: https://github.com/kevinbadi/blender-skills (no licence file; used for our own channel). The moves are written for
product showcases (metres, a product at the origin, ProRes to the Desktop); in our pipeline:
- Scenes are headless Python (`blender -b -P scenes/<name>.py`), rendered as 12 fps PNGs and encoded with haru/encode.py,
  not via the Blender MCP socket.
- The world is 1:10: Haru is 12.6 cm tall, so distances here are a tenth of the skill's (a 2 m push-in is 0.2 here).
- Room cameras live in library/sets/home/shots.py: `MOVES` gives each room's camera 'push' (this slow-zoom), 'crane'
  or 'locked', and `moved()` eases it over 5 s, capped at 30% of the way and never nearer than 9 cm to her.
- Horror pacing: slower and smaller than a product reveal; keep the lens fixed (no dolly-zoom) unless a scare motivates it.
