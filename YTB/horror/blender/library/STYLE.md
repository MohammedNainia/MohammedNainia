# Haru the Unfortunate: style guide (Coraline-style stop motion)

Every asset in the library (Haru, the cast, the house, props, monsters) must look like it came out of one stop-motion
studio. This page is the rule book. If a new asset breaks a rule here, it gets fixed before it goes into the library.

We take the **craft** of feature stop-motion films like Coraline (Laika, 2009): real miniature materials, handmade
imperfection, moody practical light. We do **not** copy their characters, designs, logos or names. Haru stays Haru.

---

## 1. The feel in one line

A real miniature world built by hand: knitted clothes with visible stitches, silicone skin, sculpted hair, crooked
furniture, dust, and light that comes from somewhere you can see. Cozy at first glance, wrong at second.

## 2. Scale (never changes)

- The world is built at **1:10**. Haru is **12.6 cm** tall (1.26 m in the story). One Blender unit is one metre.
- Doors 20 cm tall, ceilings 25 cm, a bed 20 x 11 cm, a mattress top at 4 cm. Props are scaled from real sizes / 10.
- Every asset's origin sits on the floor at its footprint centre, facing -Y (the camera side).

## 3. Characters

**Proportions (stop-motion film style):** big head (about 1/3.5 of the height for children, 1/5 for adults), thin
neck, narrow shoulders, slim body, long thin arms and legs, long fingers, small feet. Slight asymmetry is good.

**Faces:** smooth matte silicone, pale and slightly translucent, tiny pores, a few hand-painted freckles allowed.
Large expressive eyes with whites, coloured irises, black pupils and a catchlight; lids that close over them.
Thin painted brows, a small nose, a small mouth. Mouths and brows are **replacement parts** (swapped every pose),
like the 3D-printed replacement faces of feature stop motion; the eyes and lids move mechanically.

**Hair:** sculpted, never loose strands: a solid shape with fine grooves, slightly glossy, with a few stray
sculpted locks so it does not look like a helmet.

**Clothes:** real fabric scaled down: knitted jumpers with visible stitches and fuzz, woven trousers with a weave,
canvas shoes, felt, corduroy. Seams, pilling and small wrinkles. Clothes are separate parts so they can be swapped.

**Haru (the lead):** about 10 years old. Long straight jet-black hair past the shoulders with a side-swept fringe;
an oversized mustard-ochre knitted hoodie (kangaroo pocket, two drawstrings); charcoal grey trousers; small white
canvas sneakers with grey rubber soles. Big dark eyes. Always readable by her silhouette: hair, hoodie, thin legs.

## 3b. Materials: who gets what (decided)

- **Haru and every normal character:** the Coraline puppet look. Smooth matte silicone faces, real knitted and woven
  fabric clothes, sculpted hair. Never a clay or plaster texture on a normal person.
- **The house and sets:** aged, worn real materials: old plaster and clay walls, faded wallpaper, worn wood, stained
  tiles. Scanned textures (Poliigon free textures, downloaded by the user, kept out of git) replace the code-made ones.
- **Monsters:** aged, cracked clay. Something old and crumbling against Haru's soft clean look reads as wrong at once.

## 4. Sets

- Built like miniature film sets: real wood with grain and worn edges, wallpaper with a faded pattern and peeling
  corners, floorboards with gaps, plaster with cracks. Nothing perfectly straight: walls lean, frames are crooked.
- Dense set dressing: books, jars, toys, framed photos, rugs, cables, dust. Empty rooms look like a video game.
- Haru's house is one building with a floor plan (see the library README), so every room joins the others the same
  way in every episode.

## 5. Colour

- **The everyday world:** muted and slightly desaturated: greys, greens, browns, faded blues and dusty pinks.
- **Haru** is the warm accent (mustard hoodie), so she reads in every frame.
- **Night / dread:** cold blue moonlight against small warm practical lights (lamps, a hall light).
- **Something wrong:** an unnatural colour that does not belong (sickly green, a too-bright red), used sparingly.

## 6. Light

- Every light is motivated: a window, a lamp, a hall light, a torch, a TV. No flat front light.
- Night scenes: one cold key (moonlight) through a window with a thin haze so the beam shows, warm practicals,
  a cold rim so silhouettes cut out of the dark, deep blacks (AgX High Contrast).
- Shallow depth of field like a real miniature lens; slight film grain and vignette in post.

## 7. Motion

- Stop motion on twos: **12 poses a second**, held frames, a little "boil" (the hand of the animator).
- Body motion comes from the motion-capture library (Mixamo clips, retargeted), cut and timed for drama.
- Characters always touch what they stand, sit or lie on (the contact solver checks it every pose).

## 8. Sound

- Quiet and natural. Room tone always; real-sounding foley matched to the surface (carpet, wood, tile).
- Mix around **-18 LUFS**, peaks under -2 dBTP. One short, soft swell at the scare, never a blast.
