---
name: clay-character
description: Rebuild a character from an AI model sheet (turnaround) as a code-built, animatable clay stop-motion puppet in three.js, and prove the match with measurements. Use when the user wants a clay / plasticine / claymation character "like the sheet", wants our code character to match a reference image, or asks to turn a model sheet into a puppet for a video.
---

# Clay character from a model sheet

Goal: a three.js puppet that matches a model sheet part by part (heights and widths within 2% of the figure height),
made of real-looking clay (one continuous piece per garment, lumpy surface, fingerprints), with a skeleton so it animates.
Template: `scripts/character_template.js` (Haru v3). Test page: `scripts/sheet_page_template.html`.

## 1. The reference sheet
Ask the image model (Artlist Nano Banana 2, with a frame of the character as reference) for a **turnaround on a plain light grey
seamless background**: front, three-quarter front, side, three-quarter back, back, full body, same scale, feet on one line,
no text. Also an expression sheet (8 head-and-shoulder portraits). Keep both in the repo (e.g. `YTB/channel_art/`).

## 2. Measure the sheet
`python scripts/measure.py sheet SHEET.png --view 0 > ref_view0.json` (views 0..4 left to right; do 0 = front, 2 = side, 4 = back).
Parts are found by colour: hair (dark, unsaturated), skin, top (the garment colour), pants (mid grey), shoes (light, under the pants).
Landmarks are fractions of the figure height (0 = top of the hair, 1 = soles): hair_bottom, face_top, chin (where the skin meets
the collar), top_top, top_hem, hands_bottom, pants_hem, shoes_top; widths w_hair, w_face, w_top_shoulders (15% below the solid
top of the garment), w_top_mid, w_top_hem, w_pants_mid, w_shoes. Run with `--debug seg.png` and LOOK at the part map first:
if a garment colour is not hair/skin/ochre/grey/white, change the thresholds in `classify_sheet`.

## 3. Build the puppet (SDF clay)
Copy the template. Each garment is ONE signed distance field: soft shapes merged with `smin` (k 0.02 to 0.06), cut with `smax`,
turned into one mesh by `meshSDF` (three's MarchingCubes; resolution 100 to 140 per garment), roughened with `lumps()`.
Garments that bend (top, pants) are skinned with `skinIt` (inverse distance weights to the bone segments; vertices of the torso
are kept on hips/chest so the hem is not dragged by the arms). Rigid pieces (head, hair, hands, shoes) hang on their bones.
Face pieces (eyes, brows, mouths, tears, sweat) are small meshes on the head with `P.expr(name)` for the 8 sheet expressions.
Clay look: `clay3()` material = mottled colour map + fingerprint/tool-mark bump + matte sheen. Keep bump 1 to 2.

## 4. Measure ours the same way
The test page has an ID mode (`?id=1`): every part painted a flat colour (hair red, skin green, top blue, pants yellow,
shoes magenta), lights off, orthographic front camera, figures spaced so they do not touch.
`THREE_ROOT=<folder with scenes/ and node_modules/> IDM=1 node scripts/shot.js <page> 0 out.png 1` then
`python scripts/measure.py ids out_0.png --view 0 > ours_view0.json`,
`python scripts/compare.py ref_view0.json ours_view0.json` (marks every part off by > 2%) and
`python scripts/overlay.py SHEET.png out_0.png overlay.png` (both part maps at the same height + a 50% blend).

## 5. Fix in this order, re-measure after every change
1. **Heights first** (they move everything else): leg length (thigh/shin bones + one `DY` shift for everything above the hips),
   head scale, collar height, hem height, hand bone length, shoe height.
2. **Then widths**: torso scale, shoulder joints and arm rest angle, leg spacing and radius, hair/face radii, shoe scale.
3. **Then silhouette details from the overlay** (numbers miss these): a visible neck (collar dips at the front),
   sleeves hanging beside the body, two separate legs and shoes, sloping vs square shoulders, hair crown shape.
4. **Check the side and back views and the normal render**: pieces that look fine from the front can poke through the hair
   from behind (they did: hood side bulges, drawstrings). Measure views 2 and 4 too.
   `measure.py` also reports `poke_px`: garment pixels visible through the hair (garment with hair on both sides in a row).
   It must be 0 in the back views (`--view 3` and `--view 4`). In the front view the garment between the hair panels is normal,
   and in the side view the near arm can sit in front of the hair, so for those two look at a close-up instead of trusting the count.
Stop when the front has at most 2 parts off by > 2% and poke_px is 0 in every view.

## Lessons from Haru (Nov 2026)
- Heights matched within 1% after one round once the legs were lengthened; widths needed 4 rounds.
- A capsule torso ends in a rounded point: cut it flat with `smax(d, hemY - y, k)` and add a hem ring.
- Bind the skeleton in the rest pose you will show; deforming far from the bind pose drags the hem into a V.
- Building one Haru takes a few seconds at page load (8 copies for the expression sheet need `waitUntil: 'commit'`
  and long timeouts in the capture script); rendering frames is as fast as before.
- Expressions stay as separate small face pieces; they read better than sculpting them into the head.
