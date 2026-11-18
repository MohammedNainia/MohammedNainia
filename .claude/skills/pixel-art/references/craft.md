# Pixel-art craft rules (apply every time)

## Order of work
1. Silhouette first: fill every part with one dark colour and check it reads at 1x. If the pose isn't clear as a
   black shape, no shading will fix it.
2. Pick ONE key light direction (default upper-left, `light=(-.6,-.75,.5)`) and a rim light from behind the other side.
3. Block forms with volumetric primitives (ellipsoid/capsule/poly with bevel) so shading follows real form.
4. Details last: patterns, eyes, buckles, hand-placed highlights (`pixels()`), small dark crevices.
5. Run `qa()`; look at 1x and scaled; fix; repeat.

## Colour
- 4 to 7 shades per material ramp, hue-shifted (shadows toward blue/purple, highlights toward yellow).
- Whole sprite: about 16 to 40 colours. Reuse ramps between materials where possible.
- Background lower contrast and cooler than the character, so the character pops.

## Never
- Pillow shading (dark rim all round, bright centre). Light comes from one side.
- Banding (two shades running parallel to the outline in equal stair-steps).
- Orphan pixels and noise. Dither only on purpose: large gradients (sky, fog) or texture.
- Jaggies: lines should step in regular runs (1-1-1, 2-2-2, 1-2-1-2), not irregular 1-3-1-2.
- Pure black outlines everywhere. Use selective outline (default): coloured on the lit side, dark on the shadow side.

## Sizes (pick for the use)
- Tiny/readable: 16 to 24 px tall (icons, crowds). Game sprite: 32 to 64 px. Detailed hero / Blasphemous-like level of
  detail: 96 to 128 px tall. Scenes: 160x90, 256x144, 320x180 (16:9) or 144x256 (9:16); always upscale with NEAREST.

## Animation
- Idle: 4 to 8 frames, 1 px breathing on the torso, cloth/hair 1 frame behind the body (overlap).
- Walk: 6 to 8 frames; contact, down, pass, up.
- Attacks: anticipation (2 to 3 frames), a smear frame, impact, recovery.
- Sub-pixel motion: move a highlight or shade by one step instead of moving the shape.
