# Tim Burton style: what it is, and what we can use (research, 2026-11-24)

Goal: move Haru's horror reels from "clay toy" toward Tim Burton stop motion (Corpse Bride, The Nightmare Before
Christmas). This file collects how that look is built and every resource we can use, with licences.

## 1. The look

**Roots: German Expressionism** (The Cabinet of Dr. Caligari). Sharp angles, high contrast, distorted perspective,
long hard shadows (chiaroscuro) used for menace, bodies and objects bent out of true.
Sources: [StudioBinder style analysis](https://www.studiobinder.com/blog/tim-burton-style-analysis/),
[Far Out: Caligari and Burton](https://faroutmagazine.co.uk/the-cabinet-of-dr-caligari-shaped-tim-burton-aesthetic/),
[SlashFilm: Caligari and Nightmare](https://www.slashfilm.com/1444520/the-nightmare-before-christmas-cabinet-of-dr-caligari-german-expressionism).

**Shapes:** spindly fingers, thin limbs and necks, sunken eyes with dark rings, exaggerated silhouettes (a big head
on a thin body), curling lines and **spiral hills**, crooked houses, twisted trees, stripes.
Sources: [Backstage](https://www.backstage.com/magazine/article/tim-burtons-signature-style-explained-78275),
[Bold Entrance: Burtonesque](https://boldentrance.com/?p=1328).

**Colour (Corpse Bride, DP Pete Kozachik):** the living world is nearly black and white: grey, blue-grey, a
permanent overcast, faint colour only. The Land of the Dead is vivid (blue, purple, orange, yellow, green, red).
Kozachik shot the "real" world "staid and level and sensible", near black and white.
Sources: [AWN: Corpse Bride, stop motion goes digital](https://www.awn.com/vfxworld/corpse-bride-stop-motion-goes-digital),
[Hypercritic: Corpse Bride at 20](https://hypercritic.org/collection/corpse-bride-tim-burton-20th-anniversary),
[Variety review](https://variety.com/2005/film/reviews/tim-burton-s-corpse-bride-2-1200523455/).

**Our version:** a grey, blue-grey world, and Haru's mustard hoodie as the only warm colour in it.

## 2. The puppets are NOT clay

- Nightmare Before Christmas: sculpted in clay first, then cast as **foam latex skins** over custom metal armatures;
  faces were **replacement heads/mouths** (like ours).
  Sources: [Cartoon Research: animation production on Nightmare](https://cartoonresearch.com/index.php/capture-lightning-in-a-bottle-animation-production-on-the-nightmare-before-christmas/),
  [BYU Design Review](https://www.designreview.byu.edu/collections/the-nightmare-before-christmas-a-timeless-masterpiece-of-movie-design).
- Corpse Bride: **metal, silicone, foam and fabric**; skin of foam and silicone covered with **real cloth**; heads with
  **tiny gears** under the silicone to move the face (no replacement faces). Built by Mackinnon & Saunders.
  Sources: [Smithsonian puppet record](https://www.si.edu/object/nmah_1444987),
  [Mental Floss: 12 facts](https://www.mentalfloss.com/entertainment/movies/12-lively-facts-about-corpse-bride),
  [Mackinnon & Saunders](https://www.mackinnonandsaunders.com/portfolio/tim-burtons-corpse-bride).

So a Burton Haru means: a smooth, slightly translucent **silicone** face and hands (fine sculpted detail, no
fingerprints), a **real fabric** hoodie and trousers (weave, fuzz, seams), and sculpted or real **hair**. Clay
thumbprints are an Aardman signature, not a Burton one.

## 3. Free assets we can use (check the licence on each page before downloading)

| What | Where | Licence |
|---|---|---|
| Night and overcast HDRIs (moon light, grey sky) | [Poly Haven: Clarens Night 02](https://polyhaven.com/a/clarens_night_02), [Rogland Clear Night](https://polyhaven.com/a/rogland_clear_night), [Schadowplatz (overcast)](https://polyhaven.com/a/schadowplatz) | CC0 |
| Fabric, wood, plaster, stone PBR textures | [ambientCG](https://ambientcg.com) (1,300+ materials), [Poly Haven textures](https://polyhaven.com) | CC0 |
| Graveyard: tombstones, fences, crypts, trees | [Kenney Graveyard Kit](https://kenney.nl/assets/graveyard-kit) | CC0 |
| Halloween props (60+ models) | [KayKit Halloween Bits](https://kaylousberg.itch.io/halloween-bits) | CC0 |
| Spiral hills, curled shapes | Blender's own [Curve Spiral node](https://docs.blender.org/manual/uk/dev/modeling/geometry_nodes/curve/primitives/curve_spiral.html) (we can build these in code) | free |

Avoid: the Sketchfab "Ghost character" (CC BY-NC, no commercial use; the channel is monetised). No free,
commercially usable Burton-style puppet model turned up; we build our own anyway.

Paid, only if we need them: knit/wool shaders [Woolly](https://www.blendermarket.com/products/woolly),
[Weave It](https://superhivemarket.com/products/weaveit/docs); spiral setups
[The Curl](https://superhivemarket.com/products/the-curl---unified-unfolding-spiral-setup-in-geometry-nodes).
A procedural fabric shader is easy to write ourselves, like the clay one.

## 4. Claude skills for Blender (all MIT)

| Repo | What it adds | Notes |
|---|---|---|
| [el4cteo/blender-skills](https://github.com/el4cteo/blender-skills) | lighting and lookdev, **clothing**, **hair grooming**, **facial shape keys**, environment kits, geometry nodes, rigging, animation | Built for Blender 5.3 (our version), 2.8k stars, active. **Best fit.** |
| [RobLe3/cc-blender-skill](https://github.com/RobLe3/cc-blender-skill) | 10 skills incl. lighting (material-aware profiles) and cameras, with evals | 185 stars |
| [DisturbedMediaGroup/claude-animation-skill](https://github.com/DisturbedMediaGroup/claude-animation-skill) | cinematography reference, camera moves, lens maths, timing | small |
| [Evan1108-Coder/blender-cinematic-modeling-skill](https://github.com/Evan1108-Coder/blender-cinematic-modeling-skill) | cinematic materials and lighting brief | early stage |

Already installed: `.claude/skills/blender-claymation` (stop-motion workflow, 12 fps, boil), `camera-cinematography`,
`clay-character`.

## 5. Tutorials and making-of reading

- [AWN: Corpse Bride, stop motion goes digital](https://www.awn.com/vfxworld/corpse-bride-stop-motion-goes-digital) (Kozachik on lighting and the digital shoot)
- [Cartoon Research: Bossert behind-the-scenes series on Nightmare](https://cartoonresearch.com/index.php/tag/nightmare-before-christmas/)
- [AWN: The Advanced Art of Stop-Motion Animation, building puppets](https://www.awn.com/print/animationworld/advanced-art-stop-motion-animation-building-puppets-part-2)
- [Blender Studio: stylized character workflow](https://studio.blender.org/training/stylized-character-workflow/)
- [Studio Daily: stop-motion looks in CG](https://studiodaily.com/2005/12/stop-motion-looks-with-xsi-or-other-cgi-packages) (exaggerated proportions, replacement parts, the Jack Skellington puppet)

## 6. What this means for Haru (proposal)

1. **Design:** Burton proportions: bigger head, thinner neck, longer and thinner arms and legs, spindly fingers,
   bigger eyes with dark rings under them, paler skin. Keep the hoodie, the long black hair and her face simple.
2. **Materials:** silicone skin (smooth, soft translucency), fabric hoodie and trousers (weave, fuzz, soft folds),
   sculpted hair with fine strand grooves (or real strands).
3. **World:** near black-and-white blue-grey sets, crooked expressionist houses, spiral hill, bare twisted trees,
   graveyard props from the CC0 kits.
4. **Light:** cold moonlight key, strong rim lights, long hard shadows on the walls, warm practicals (a window, a
   lamp) as the only other warm notes; overcast flat grey for "daytime" scenes.
5. **Motion:** keep the stop-motion rules we already have (12 fps, held poses, boil, light flicker).
