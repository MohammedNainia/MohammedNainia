# Theme packs

Each theme: palette bases (feed to `ramp()`), signature shapes, motifs, and what to avoid. Mix freely
(e.g. "Moroccan + monster"). Always invent ORIGINAL characters and places in a theme; never recreate a specific
existing game's characters, logos or levels.

## Moroccan / Andalusian
- Bases: terracotta `#b5532e`, sand plaster `#d9b07a`, zellige blue `#1f5f8b`, zellige green `#2f7a4f`, brass `#c8962a`,
  cedar wood `#7a4a26`, indigo cloth `#2c3566`, saffron `#e0a020`, night sky `#141a33`.
- Shapes: horseshoe arches (`arch(kind='horseshoe')`), stepped merlons on wall tops, riad courtyards with a central fountain,
  carved cedar ceilings, brass lanterns with star cut-outs (light dots on the wall), keyhole doors with big studs.
- Motifs: 8-point star zellige (use `pattern()` with a star tiling), arabesque bands, tadelakt walls (smooth, low contrast),
  djellaba with pointed hood, babouche slippers, tea glass and pot, palm trees, kasbah towers.
- Light: hard warm sun, deep blue shadows in courtyards; at night warm lantern pools.

## Japanese (Edo / feudal / folklore)
- Bases: vermilion `#c23b22`, aged wood `#5a3a28`, paper shoji `#e8dcc0`, indigo `#24324f`, pine green `#2e4a32`,
  roof tile grey `#4a4e58`, gold leaf `#d4a640`, ink black `#16141a`, sakura `#e8a0b4`.
- Shapes: torii gates (two capsules + two flat beams with up-curved ends), curved tiled roofs (poly with tilt), engawa
  verandas, stone lanterns (stacked boxes/ellipsoids), paper lanterns (ellipsoids, flat=True when lit), bamboo.
- Characters: ronin, miko, yokai (kitsune, oni with horns via `cone()`, kappa), straw hats (wide flat cone).
- Light: soft overcast or lantern-lit night; mist bands (dithered) between layers.

## Ancient Greek
- Bases: marble `#e6e0d2`, aged marble `#bfb6a2`, terracotta `#b8643a`, black-figure black `#1c1612`, olive `#6b7a3a`,
  Aegean blue `#2a6fa8`, bronze `#a8702a`, purple dye `#5a2a5a`, gold `#d8b04a`.
- Shapes: Doric/Ionic columns (capsule + boxes for capital, `pattern()` vertical fluting), pediments (triangle poly),
  amphorae (stacked ellipsoids), meander (Greek key) bands, laurel wreaths.
- Characters: hoplites (crested helmet, round shield `ellipsoid` flattened, spear), philosophers in himation,
  monsters: Minotaur, Medusa (snakes = small capsules), harpies, cyclops.
- Light: bright Mediterranean sun, short hard shadows; marble needs hue-shifted ramps (warm light, blue shadow) or it looks grey.

## Gothic / dark religious
- Bases: crimson `#6e1a20`, tarnished gold `#a06a1c`, iron `#55555f`, bone `#d8ccb0`, candle wax `#e8dcc0`,
  stone `#3a3440`, purple shadow `#2a1838`, pale skin `#c8a890`.
- Shapes: pointed arches (`kind='pointed'`), rose windows, ribbed vaults, thorns (`cone()` rows), hoods and veils,
  ornate armour with filigree (`pattern()`), long greatswords and censers.
- Light: single strong source (candles, stained glass), deep shadows, rim light on the silhouette.

## Medieval / historical fiction
- Bases: wool brown `#6a4a30`, linen `#d8ccae`, chainmail `#6a6e78`, leather `#7a4a2a`, heraldic red `#a82a2a`,
  heraldic blue `#2a4a8a`, grass `#4a6a2a`, thatch `#a88a4a`.
- Shapes: timber-frame houses (boxes + dark beam lines), castles with crenellations, banners (poly with wave),
  carts, wells, market stalls.

## Monsters (any theme)
- Exaggerate one feature (mouth, horns, limbs); keep the silhouette readable in solid black first.
- Use a sickly or unnatural accent (`#8aa83a` bile green, `#6a2a8a` corrupt purple) against a neutral body ramp.
- Eyes and glows: `flat=True` materials so they never get shaded.

## Animals
- Build from ellipsoids (body, head) and tapered capsules (legs, neck, tail). Fur = ramp with low contrast + a few
  hand-placed highlight clusters, never per-pixel noise.
