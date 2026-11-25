# Artlist prompts for the library (Coraline-style stop motion)

Ready to run when the Artlist tokens are back. Rules:
- Start every prompt with the **style block**. For anything with Haru in it, attach Haru's reference image
  (`YTB/channel_art/haru_ref.png`; once we have the new turnaround, attach that instead).
- Generate 4 of each, keep the best in `references/` with the generation id in the file name.
- Images first (cheap). Only send the chosen image to **image-to-3D** (costs more; check the price first).
- For 3D, ask for **one object alone, front view, plain background, nothing touching it** (cleaner models).

## Style block (paste at the start of every prompt)

> Handmade stop-motion feature film style, like the miniature sets and puppets of Laika's Coraline: real miniature
> materials, matte silicone skin, knitted and woven fabric clothes with visible stitches, sculpted hair with fine
> grooves, real wood, faded wallpaper, slightly crooked handmade shapes, muted desaturated colours, moody practical
> lighting, shallow depth of field. Original design, not a character from any film.

## 1. Haru (the lead)

**Turnaround (16:9):**
> [style block] Character turnaround sheet of Haru, an original 10-year-old girl puppet. Big head on a thin neck,
> slim body, long thin arms and legs, long fingers, small feet. Pale matte silicone face, large dark eyes with whites
> and catchlights, thin dark brows, small nose, small mouth. Long straight jet-black sculpted hair past the shoulders
> with a side-swept fringe and a few stray sculpted locks. Oversized mustard-ochre knitted hoodie with a kangaroo
> pocket and two drawstrings, charcoal grey woven trousers, small white canvas sneakers with grey rubber soles.
> Five full-body views in one row, same scale, feet on one line: front, three-quarter front, side, three-quarter
> back, back. Neutral standing pose, arms slightly away from the body. Plain light grey studio background, even
> soft light, no text.

**Expressions (16:9):** attach the chosen turnaround.
> [style block] Expression sheet of the same puppet girl Haru, 8 head-and-shoulders portraits in a 4 by 2 grid,
> same angle: neutral, worried, scared with a small round mouth, terrified with eyes wide and mouth open screaming,
> sad and teary, small smile, suspicious with narrowed lids, blank wide stare with tiny pupils. Replacement-face
> stop-motion puppet. Plain light grey background, no text.

**Materials (1:1):**
> [style block] Macro close-ups, 2 by 2 grid: the silicone face skin and one glass-like eye; the mustard knitted
> hoodie fabric with stitches and fuzz; the sculpted black hair with grooves; the white canvas sneaker and grey
> rubber sole. Studio macro photography, no text.

## 2. The house (one mood board per room, 9:16)

> [style block] Miniature film set of [ROOM], inside an old two-storey family house, night, lit only by [LIGHT].
> Dense handmade set dressing: [PROPS]. Crooked walls, faded patterned wallpaper, worn wooden floor, dust. Empty of
> people. Vertical frame, wide shot from the doorway, shallow depth of field.

| ROOM | LIGHT | PROPS |
|---|---|---|
| a narrow upstairs hallway and landing with a staircase going down | a small warm wall lamp and blue moonlight from a window at the end | family photos in crooked frames, a runner rug, a radiator, a linen cupboard door, banister |
| a small old bathroom | a single flickering bulb over the mirror | claw-foot bathtub with a shower curtain, cracked tiles, a sink with a mirror cabinet, towels, a rubber duck, a dripping tap |
| an old kitchen | the cold light of an open fridge | worn table and chairs, hanging pots, a stove, a calendar, cereal boxes, a cat bowl, a window over the sink |
| a dusty attic under a sloped roof | moonlight through a small round window | boxes, furniture under white sheets, an old rocking chair, a dressmaker's dummy, a trunk, old toys, a pull-down ladder hatch |
| a small living room | the blue glow of an old CRT television | a sagging sofa with a knitted blanket, a standard lamp, a rug, a bookshelf, a clock, curtains |
| a basement | one bare hanging bulb | a boiler, metal shelves of jars, a washing machine, a workbench, pipes, a small high window |

## 3. Props (for image-to-3D; one object each, 1:1)

> [style block] A single handmade miniature [OBJECT] for a stop-motion film set, alone, three-quarter front view,
> centred, plain light grey background, nothing else in the picture, no text.

First batch: wooden single bed with headboard; wardrobe; bedside table with drawer; desk and chair; bookshelf with
books; claw-foot bathtub; pedestal sink with mirror; toilet; kitchen table; old fridge; stove; sofa; rocking chair;
old CRT television; standing lamp; cardboard box; old trunk; porcelain doll; teddy bear; music box.

## 4. The cast kit (images first, then 3D of the chosen ones)

**Base bodies (A-pose, plain clothes so the body shape reads):**
> [style block] Full-body front view of a neutral stop-motion puppet base body: [BODY]. Arms held slightly away from
> the body (A-pose), plain grey fitted clothes, bald head with a smooth face, no hair. Plain light grey background,
> no text.

BODY: a slim woman about 35; a tall thin man about 40; a boy about 10; a girl about 7; an elderly woman about 75;
an elderly man about 75.

**Hair pieces (one piece alone, to fit any head):**
> [style block] A single sculpted stop-motion puppet hairpiece, [STYLE], shown alone without a head, front
> three-quarter view, plain light grey background, no text.

STYLE: low bun; short bob; long wavy; two pigtails; short tidy boy's cut; balding with grey sides; curly afro;
long straight red hair; grey bun with hairpins.

**Clothes (one garment alone, on an invisible body):**
> [style block] A single stop-motion puppet garment, [GARMENT], shown alone as if worn by an invisible body, front
> view, plain light grey background, no text.

GARMENT: plum knitted jumper; light blue shirt; beige raincoat; lilac cardigan; grey pleated skirt; jeans; green
hoodie; pink sweater; brown corduroy trousers; long red coat; nurse's uniform; school uniform blazer; slippers;
wellington boots.

## 5. Monsters (concept first, one creature per prompt, 9:16)

> [style block] Concept art for a stop-motion horror creature puppet: [CREATURE]. Full body, front three-quarter
> view, standing in a dim miniature room, plain composition, no text.

CREATURE ideas: the tall thin black figure with pale eyes (Lights Off, to rebuild properly); the long-armed thing
under the bed; a pale woman with a too-wide smile who wears Mum's clothes; a doll that is a little too big; a
creature made of coats from the hallway coat rack.
