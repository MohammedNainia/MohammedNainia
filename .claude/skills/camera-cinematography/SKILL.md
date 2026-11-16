---
name: camera-cinematography
description: Cinematic camera work in Blender including framing, lenses, composition, camera animation, and shot language beyond basic rendering setup via MCP.
license: MIT
metadata:
  author: https://github.com/arjun988
  version: "1.0.0"
  domain: blender
  role: specialist
  triggers: camera, cinematography, lens, framing, composition, shot, dolly, orbit, focal length, depth of field, camera animation
  related-skills: rendering, lighting, animation, compositing, lookdev
---

# Camera Cinematography

Intentional framing. Lens language. Motivated camera moves. Shot-ready cameras.

## When to Use

- Cinematic stills and turntables with purpose
- Animated camera moves (dolly, crane, orbit, handheld)
- Matching reference camera / lens feel
- Shot layout for lookdev and portfolio

## Workflow

```
Shot intent → Camera + target empty → Lens/FOV → Composition
  → Focus/DoF → Move (if animated) → Viewport check → Render/comp
```

## Naming

- `CAM_[Shot]_[Angle]`
- `EMPTY_CamTarget_[Shot]`
- Collection: `COL_Cameras`

## Lens Guide

| Feel | Focal (FF equiv) | Notes |
|------|------------------|-------|
| Wide establishing | 18–28mm | Distortion; watch edges |
| Story / product | 35–50mm | Natural |
| Portrait / hero | 85–135mm | Compression |
| Tele drama | 150mm+ | Flat space |

Sensor fit and resolution affect FOV — set camera sensor intentionally.

## Composition Checklist

- [ ] Subject readable in silhouette
- [ ] Headroom / lead room intentional
- [ ] Horizon level (unless motivated)
- [ ] Foreground / mid / background depth
- [ ] Avoid tangent mergers on edges

## Camera Animation

| Move | Use |
|------|-----|
| Orbit | Product / character showcase |
| Dolly in | Reveal / tension |
| Crane | Scale / establishing |
| Handheld noise | Documentary / horror unease |
| Locked off | Archviz / product purity |

Animate camera + target empties; prefer slow ease-in/out.

## DoF

- Focus on primary subject empty
- F-stop for style: shallow for hero, deeper for environments
- Preview in Eevee; final in Cycles if needed

## Constraints

### MUST DO
- Name cameras and targets
- Match aspect ratio to delivery
- Check framing at start, mid, end of moves

### MUST NOT DO
- Default 50mm for every shot without intent
- Animate FOV wildly unless motivated
- Crop critical silhouette out of frame

## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|----------|
| Lens And Composition | `references/lens-and-composition.md` | When needed |
| Camera Move Library | `references/camera-move-library.md` | When needed |
| Dof Guide | `references/dof-guide.md` | When needed |

## Using it in our three.js pipeline (YTB/horror/three)

Source: https://github.com/arjun988/blender-skills (MIT). Our scenes are three.js, not Blender: apply the same shot language,
with these translations.

- Our `cam.fov` is the VERTICAL field of view. For the 9:16 Shorts (1080x1920) the long side is vertical, so a full-frame
  lens maps as vfov = 2*atan(18 / focal): 24mm ~ 74°, 35mm ~ 54°, 50mm ~ 40°, 85mm ~ 24°, 135mm ~ 15°.
  For 16:9 (`--landscape`): vfov = 2*atan(12 / focal): 24mm ~ 53°, 35mm ~ 38°, 50mm ~ 27°, 85mm ~ 16°.
- A vertical frame is narrow: a head scaled 1.45 (person()) fills the width fast. Close-ups need distance + a longer lens
  (about 1.8-2.4 m at 30-34°), not a camera pushed into the face.
- Camera moves are the `shot(t)` functions: dolly in = lerp the position with ease(); handheld = the small sin() shake;
  locked off = a fixed [pos, look]. Check framing at the start, middle and end of every move with
  `node render.js --cpu --scene <name> --frames a,b,c`.
- No real depth of field in the pipeline: separate subject from background with light (key/rim), fog and vignette.
- Horror grammar we use: slow dolly-ins on faces and screens, POV shots for searches, locked-off wides for "nobody there",
  hard cuts to black + silence before a reveal, and the loop (last frame = first frame).
