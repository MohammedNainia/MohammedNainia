---
name: pixel-art
description: Make pixel art in code (characters, monsters, animals, buildings, full scenes, animated loops, sprite sheets) in any theme: Moroccan, Japanese, ancient Greek, gothic, medieval/historical, fantasy, horror. Use whenever the user asks for pixel art, a sprite, a 16-bit / retro game look, a tileset, a pixel character or scene, or an animated pixel GIF, even if they only name a style or a game they like ("something like Blasphemous", "like Stardew", "like Celeste").
---

# Pixel art in code

Python (numpy + Pillow) library `scripts/pixkit.py`: build sprites from **solid primitives** so every pixel has depth and a
surface normal, light them (one key light, a rim light, optional point lights like lanterns and candles), quantise into
**hue-shifted colour ramps**, then clean up like a pixel artist (selective outlines, contour lines between overlapping parts,
orphan removal). `qa()` checks the result for the classic mistakes.

Read before drawing:
- `references/craft.md`: the rules (order of work, colour, what never to do, sizes, animation).
- `references/themes.md`: theme packs (palette bases, signature shapes, motifs, lighting) for Moroccan, Japanese, Greek, gothic,
  medieval, monsters, animals. Mix them.
- `references/subjects.md`: proportions and build recipes for humans, animals, monsters, architecture.
- `examples/moroccan_night.py`: a full worked scene (riad doorway, zellige, hooded traveller, lantern light, 8-frame loop).

## Originality
"Like game X" means its *level of craft and mood*, never its characters, logos, levels or exact designs. Always invent an
original subject in that spirit and say so.

## Workflow
1. Decide size (craft.md "Sizes"), theme (themes.md) and subject recipe (subjects.md). Write the palette first:
   `s.material('cloth', ramp('#6e1a20', 6))` for each material (4 to 7 shades, about 16 to 40 colours total).
2. Silhouette: block the big forms with `ellipsoid`, `capsule` (limbs, torso, columns, tapering), `poly` (cloth panels, walls,
   blades; bevelled edges), `box`, `cone` (spikes, horns, hats), `arch(kind='round'|'pointed'|'horseshoe'|'ogee'|'flat')`.
   Use `z0` to put parts in front of others (body < clothes < arms in front < held objects).
   Render once and look at it at 1x: the pose must read as a silhouette.
3. Light: `render(light=..., key=..., ambient=..., rim=..., point=(x, y, z), point_amt=, point_range=)`. One key direction.
   Night = low `key` and `ambient` plus a `point` light from the lantern/fire/candle.
4. Details: `pattern(mat, fn, on='material')` for tiles, inlay, embroidery, cloth folds, fluting; `pixels(mat, [(x,y),..])`
   for eyes, sparkles, stitches. Emissive things (flames, glowing eyes, lit windows) use `flat=True`.
5. QA: `stats, problems = qa(img.a)`. Fix every problem it lists, then look at the 1x and scaled images yourself against
   craft.md "Never". Iterate before showing the user.
6. Animate: build the scene as a function of frame `f` (breathing 1 px, cloth lagging the body, flicker on point lights),
   `save_gif(frames, path, scale, ms)`, `sheet(frames, path)` for sprite sheets. Always upscale with NEAREST (scale 4 to 8).

## Path B (best quality for detailed characters): AI concept, then code cleanup
Primitives alone look stiff for detailed, organic characters. When the user wants a high-detail character (the level of
big hand-painted pixel games), do this instead and tell them it's an AI-generated base:
1. Generate the concept with Artlist `generate_image` (2 variations): "detailed pixel art sprite of an original <character>,
   full body, <pose and view>, <palette with one accent colour>, high-detail hand-painted 16-bit pixel art, crisp pixels,
   clean dark outline, strong light from the upper left with a rim light, plain solid background, no text".
   Describe an ORIGINAL design; never name or describe an existing game's character.
2. `python scripts/snap.py concept.png sprite.png 40`: finds the fake pixel size, samples one colour per cell, cuts out the
   background, reduces to a fixed palette (keeps small accents like a glowing eye), removes orphans, adds the outline.
   Check the 1x result; if an accent colour is lost, raise the colour count.
3. Animate or place it with pixkit (backgrounds, light, export), e.g. `compose(bg, (sprite, x, y))`.

## Limits (be honest with the user)
Built from primitives, faces and hands stay simple at small sizes; this is a strong base for clean game-quality sprites,
not hand-painted masterpieces. For more organic detail: render bigger (96 to 128 px characters) and hand-place detail with
`pixels()`, or block the pose in a 3D tool and use this for lighting, palette and cleanup.
