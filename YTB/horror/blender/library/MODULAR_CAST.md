# Modular cast kit: heads, bodies, hair, clothes

Every character in the channel is put together from parts, the way real stop-motion studios do it:

  character = head + face + hair + body + clothes (+ colours)

All parts are made to one standard so any part fits any other:
- Child scale is Haru: 1.26 m, head about 1/4.5 of the height. Adults are about 1.65 m (women) and 1.78 m (men), with a
  head about 1/7 of the height.
- Every head ends in the same flat neck cut, and every body starts with the same neck stump. They snap together there.
- Every hairpiece is a cap that sits on the bald scalp of its head size (child or adult), so any hair fits any head of
  the same size.
- Bodies wear a plain light grey fitted base layer, so a clothes layer or a colour change makes a new character.
- In code: `puppets/haru_clay.py` is the rig. A new character is a palette plus a hair shape, as Mika and Jun already
  are in `puppets/cast_camp.py`. The kit adds head shapes and body types as swappable options.

## How to run on Artlist (Nano Banana)
- Attach `YTB/channel_art/haru_turnaround_sheet.png` to every prompt, or start from the blank-face Haru generation
  `01a20472-a03b-705e-beec-2791c8c5c082`. This keeps every part in Haru's clay style.
- Use 16:9 for every sheet, with the same layout: front, three-quarter, side, back in one row, at the same scale, on a
  plain light grey background.
- Generate 4 of each, keep the best in `YTB/channel_art/kit/<part>/`, and put the generation id in the file name.

## Style block (start of every prompt)
> Handmade stop-motion claymation puppet part, matte plasticine with soft fingerprints and tool marks, rounded edges,
> slightly uneven surfaces, never glossy. Exactly the same clay style and simple face as the attached Haru sheet: small
> dark dot eyes with a tiny white catchlight, thin dark brows, a small round nose, a small simple mouth. Original
> design. Plain light grey studio background, even soft light, no text.

## 1. Heads (bald, no hair, no body)
> [style block] Turnaround sheet of a single bald puppet head with no hair and no body, [HEAD]. The neck is cut flat
> just under the jaw. Four views in one row, same scale: front, three-quarter, side, back. Neutral expression, ears
> showing, smooth bald scalp so a hairpiece can sit on top.

HEAD (one prompt each):
- Girl: a girl about 10, round soft face, small chin, the same head as the attached Haru.
- Teen girl: a girl about 16, slightly longer face, defined cheekbones.
- Woman: a woman about 35, oval face, soft jaw.
- Old woman: a woman about 75, soft sagging cheeks, wrinkles pressed into the clay, thin lips.
- Boy: a boy about 10, round face, a slightly wider nose than the girl, bigger ears.
- Teen boy: a boy about 16, longer face, a stronger jaw starting.
- Man: a man about 40, square jaw, heavier brows, a larger nose.
- Old man: a man about 75, a long face, deep wrinkles, big ears and nose, a slightly hollow cheek.

## 2. Faces (replacement parts for any head)
> [style block] Sheet of stop-motion replacement face parts for the attached bald head, laid out in a neat grid:
> 8 pairs of eyes (neutral, wide, closed, half-closed sleepy, narrowed, looking left, looking right, tiny pinprick
> pupils), 8 brow pairs (neutral, worried, angry, raised, sad, one raised, flat, knitted), 10 mouths (closed, small
> smile, big smile, open "o", screaming, sad, flat line, teeth showing, talking "ah", talking "ee"), and 4 noses
> (button, small round, long, wide). Each part alone, front view.

## 3. Bodies (no head, neck stump, A-pose)
> [style block] Turnaround sheet of a headless puppet body, [BODY], ending in a short neck stump where a head attaches.
> Arms slightly away from the body (A-pose), hands open with long fingers, feet flat. It wears a plain light grey fitted
> base layer and plain grey shoes so the body shape reads. Four views in one row, same scale: front, three-quarter,
> side, back.

BODY:
- Girl and boy (child, Haru's height): slim (Haru's own body); average; sturdy and round.
- Women (adult): slim and tall; average; heavy and pear-shaped.
- Men (adult): thin and tall; average; heavy, broad shoulders and a belly.
- Elderly (use the adult bodies): slightly hunched, with a rounder back and shorter steps.

## 4. Hair (one piece alone, no head)
> [style block] Turnaround sheet of a single sculpted clay hairpiece, [HAIR], shown alone with no head inside, as a
> hollow cap that fits a [child / adult] bald head. Soft sculpted grooves, one solid clay mass. Four views in one row:
> front, three-quarter, side, back.

HAIR for girls and women: long straight with a side fringe (Haru); a chin-length bob with a blunt fringe; a bob with
two small buns (Mika); two pigtails; a high ponytail; a low bun; long wavy; curly afro; short pixie cut; a grey bun
with hairpins (old woman).

HAIR for boys and men: short messy clumps (Jun); a short tidy side parting; a buzz cut; curly top with short sides;
a long fringe over the eyes; slicked back; balding on top with grey sides (old man); a beard and moustache piece (for
the man's head, sits on the jaw).

## 5. Clothes (one garment alone, on an invisible body)
> [style block] Turnaround sheet of a single clay puppet garment, [GARMENT], made for the [child / woman / man]
> [slim / average / heavy] body, shown alone as if worn by an invisible body, with soft thick clay folds and seams. Four
> views in one row: front, three-quarter, side, back.

GARMENT: a hoodie with a kangaroo pocket; a knitted jumper; a buttoned shirt; a school blazer; a raincoat; a long
coat; a cardigan; a dress; a pleated skirt; jeans; trousers; shorts; pyjamas; a nightgown; a hazmat suit; a nurse's
uniform; sneakers; boots; slippers.

## Order to make them
1. Heads: girl, boy, woman, man (four prompts). Then the elderly and teen heads.
2. Bodies: the child average body, the woman average body, the man average body. Then the other types.
3. Hair: ten pieces to start, the ones current characters need first.
4. Faces: one sheet for the child head and one for the adult head.
5. Clothes as stories need them.

After each batch: rebuild the parts in code to the standard sizes, then make a test lineup that mixes them (for
example the woman's head on the slim body with the bun) and check that the seams and sizes fit.
