# The Haru library: everything an episode is built from

Goal: an episode is assembled, not built. A story's shot list picks a room, a lighting mood, characters (with their
hair and clothes), props, a monster and motion clips by name; only what is truly new gets made, and then it joins
the library for every later episode. The look follows [STYLE.md](STYLE.md) (Coraline-style stop motion).

## Folders

```
library/
  STYLE.md                 the rules every asset follows
  characters/
    haru/                  the lead: hand-built puppet (face rig, replacement mouths and brows, mechanical eyes)
    bodies/                rigged base bodies: child_f, child_m, teen, woman, man, elderly
    hair/                  hair pieces that snap onto any head (bob, long_straight, bun, pigtails, buzz, ...)
    clothes/               tops, bottoms, shoes, outerwear, accessories (glasses, hats, bags) fitted to the bodies
    cast/                  saved combinations with names (mum, dad, grandma, nurse, neighbour, ...)
  monsters/                one folder per creature: model, rig, materials, notes on how it moves
  sets/
    house/                 Haru's house, one .blend per room, all on one floor plan
    outside/               street, garden, school, woods, ... as stories need them
  props/                   furniture, toys, kitchen, bathroom, attic clutter, lights, ...
  materials/               the shared shader library: silicone, knit, weave, canvas, wood, plaster, glass eyes
  references/              Artlist style sheets and concept images each asset was made from
```

Motion lives in `../mocap/` (Mixamo clips baked to `clips.npz`), sound in a shared sound folder (to come).

## Haru's house (one floor plan, so rooms always connect the same way)

| Floor | Rooms |
|---|---|
| Attic | attic (boxes, old furniture under sheets, a round window, a hatch with a pull-down ladder) |
| Upstairs | Haru's bedroom (exists), hallway and landing, bathroom, Mum's bedroom, a narrow linen cupboard |
| Ground | entrance and front door, staircase, living room, kitchen, back door |
| Below | basement (boiler, shelves, one bare bulb) |
| Outside | front porch and street, back garden with a shed |

Build order (most-used first): bedroom (done), hallway and stairs, bathroom, kitchen, attic, living room, front
door and porch, basement, garden.

Rooms are made from a **modular kit**: wall panels (plain, window, door), floors, ceilings, skirting, door and window
frames, stairs, all on a 5 cm grid at 1:10 scale. Every room .blend also holds: named camera marks (wide, door,
low, high corner), lighting moods (day, evening, night, power cut), the support surfaces for the contact solver.

## Side characters: a kit, not one-off models

`bodies x hair x clothes x colours` gives hundreds of different people from a few dozen parts.

1. Base bodies share one rig (the same pivot/bone names as Haru), so every motion clip works on all of them.
2. Hair and clothes are separate pieces fitted to each body and parented to its bones.
3. Every piece takes its colour from a material slot, so one jumper can be mustard, plum or grey.
4. A cast member is a saved recipe: body + head + hair + outfit + colours + name.

## Monsters

Each creature gets: concept image, 3D model, a rig suited to how it moves (Mixamo auto-rig if it is human-shaped,
a simple custom chain otherwise, like the long arm in "Something Under the Bed"), its eye/glow material, and a note
on its rules (what it does, how it is shown). Existing: the tall black figure (Lights Off), the under-bed arm.

## How an Artlist asset joins the library

1. **Concept:** generate the image in Artlist with the style prompt block and the Haru reference attached
   (prompts in [ARTLIST_PROMPTS.md](ARTLIST_PROMPTS.md)). Save the pick in `references/`.
2. **3D:** Artlist image-to-3D -> textured GLB (also FBX/OBJ).
3. **Clean-up in Blender:** scale to 1:10, origin on the floor, facing -Y, tidy and lighten the mesh, replace the
   baked texture with our shared materials (so everything matches), add stop-motion boil where it moves.
4. **Rig** (characters, monsters): Mixamo free auto-rig, or our own rig; check with a walk, a sit and a crouch.
5. **Check:** a turntable render under the night lighting next to Haru for scale and style; fix or reject.
6. **File:** save in its folder, mark it as an asset with a thumbnail and tags, note its source in `references/`.

## Order of work

1. Style sheets in Artlist (Haru turnaround, expressions, materials, one room mood board), then rebuild Haru to them.
2. The house: hallway and stairs, bathroom, kitchen, attic (with their props).
3. The cast kit: two base bodies first (woman, man), five hairstyles, six outfits; then children and elderly.
4. Monsters as episodes need them, kept for reuse.

Artlist tokens: images are cheap, 3D models cost more. Spend in this order: style sheets, props, cast parts,
monsters. Check the cost of a 3D generation before the first one.
