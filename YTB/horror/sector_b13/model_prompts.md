# Sector B13: model sheet prompts (Artlist, Nano Banana)

These sheets become the reference for every Sector B13 file. Each code puppet gets rebuilt to match its sheet, the way
Haru was.

How to run:
- Attach `YTB/channel_art/haru_turnaround_sheet.png` to every prompt so the clay style, scale and face style match Haru.
  You can also start from the blank-face Haru generation `01a20472-a03b-705e-beec-2791c8c5c082`.
- Generate 4 of each. Keep the best one in `YTB/channel_art/b13/`, with the generation id in the file name.
- Run the turnaround first. Attach the chosen turnaround to that character's other sheets.
- Images only for now. Image-to-3D comes later, and only for the creature if the code version still fails.

## Style block (paste at the start of every prompt)

> Handmade stop-motion claymation puppet, matte plasticine with soft fingerprints and tool marks, rounded edges,
> slightly uneven surfaces, never glossy. The same clay style, proportions and simple face as the attached Haru sheet:
> small dark dot eyes with a tiny white catchlight, thin dark brows, a small round nose, a small simple mouth. Original
> design, not from any film or franchise.

## 1. The B13 creature (most important)

**Turnaround (16:9):**
> [style block] Character turnaround sheet of a tall stop-motion horror creature puppet, made of grey clay. About 2.7
> times the height of the attached girl, extremely thin and starved, hunched forward with a curved spine and visible
> spine knobs. The arms are far too long, the hands hang below its knees, and the fingers are long and thin, with
> darker grey pointed nails. The elbows and knees are bony and bend a little the wrong way. Its skin is stretched
> grey-taupe clay with thin sinew lines, ribs showing under the skin, and a sunken stomach. The head is long and narrow,
> with no nose, two deep black empty eye pits, and a thin lipless mouth line that is closed. It wears a heavy rusted
> metal collar with a small tag stamped "B13". Four full-body views in one row, same scale, feet on one line: front,
> three-quarter front, side, back. The girl from the attached sheet stands beside it at the far left for scale. Plain
> light grey studio background, even soft light, no other text.

**Face sheet (16:9):** attach the chosen turnaround.
> [style block] Head close-ups of the same grey clay creature, 6 views in a 3 by 2 grid: front, three-quarter, profile,
> looking down over its shoulder, mouth slightly open as if speaking softly, and mouth opened far too wide with small
> uneven teeth. Black empty eye pits in every view. Plain light grey background, no text.

**Hand (1:1):** this is the prop that comes through the tent zip.
> [style block] Macro close-up of one long thin grey clay creature hand reaching in through a half-open zip of green
> tent nylon, three long fingers with darker pointed nails, knuckles showing, lit cold from below by a torch. Dark
> background, shallow depth of field, no text.

**Variant B (run it once to compare):** use the turnaround prompt with this face instead:
> ...a smooth blank face with no eyes and no nose, only a thin mouth line, and a faint human smile pressed into the
> clay, as if it is trying to look like a person...

## 2. Mika

**Turnaround (16:9):**
> [style block] Character turnaround sheet of Mika, a girl puppet the same age and height as the attached girl Haru, a
> friendly calm face. A teal knitted hoodie with a kangaroo pocket, dark jeans, worn white sneakers. Brown hair in a
> chin-length bob with two small buns on top and a blunt straight fringe. Light peachy skin. Five full-body views in one
> row, same scale, feet on one line: front, three-quarter front, side, three-quarter back, back. Neutral standing pose,
> arms slightly away from the body. Plain light grey studio background, no text.

**Expressions (16:9):** attach the chosen turnaround.
> [style block] Expression sheet of the same puppet girl Mika, 6 head-and-shoulders portraits in a 3 by 2 grid: neutral,
> laughing with her eyes shut, a warm reassuring smile, mischievous grin, scared, screaming. Plain light grey
> background, no text.

## 3. Jun

**Turnaround (16:9):**
> [style block] Character turnaround sheet of Jun, a boy puppet the same age as the attached girl Haru and a little
> taller. An olive green hoodie with the hood down, khaki cargo trousers, dark hiking boots. Short messy black hair in
> soft clumps with a short flicked fringe. Warm tan skin. Five full-body views in one row, same scale, feet on one line:
> front, three-quarter front, side, three-quarter back, back. Relaxed standing pose, hands half in his pockets. Plain
> light grey studio background, no text.

**Expressions (16:9):** attach the chosen turnaround.
> [style block] Expression sheet of the same puppet boy Jun, 6 head-and-shoulders portraits in a 3 by 2 grid: neutral,
> big laugh, telling a spooky story with a torch under his chin, smug, scared, screaming. Plain light grey background,
> no text.

## 4. The B13 handler

**Turnaround (16:9):**
> [style block] Character turnaround sheet of a Sector B13 handler, an adult puppet about 1.4 times the height of the
> attached girl. A baggy matte grey hazmat suit with soft clay folds and taped seams, a grey hood, a round black visor
> that hides the face completely, a small gas-mask filter on each side, thick black rubber gloves, black boots. A small
> faded "B13" patch on the chest. Holding a long metal catch pole with a loop at the end. Four full-body views in one
> row, same scale, feet on one line: front, three-quarter front, side, back. Plain light grey studio background, no
> other text.

## 5. The cast lineup (16:9, run last)

Attach all the chosen turnarounds.
> [style block] Cast lineup of a stop-motion horror short, everyone standing side by side on one line at the same scale,
> front view: the B13 handler, the girl Mika, the girl Haru in the middle, the boy Jun, the tall grey B13 creature, and
> a second handler. Plain light grey studio background, even soft light, no text.

## After the sheets
- Rebuild the creature in `puppets/cast_camp.py` to match its turnaround, then compare them side by side.
- Adjust Mika, Jun and the handler to their sheets (hair, colours, proportions).
- Then build the animated scene `scenes/sector_b13.py`.
