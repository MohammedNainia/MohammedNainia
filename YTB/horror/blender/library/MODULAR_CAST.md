# Modular cast kit: heads, bodies, hair, clothes

Every character is put together from parts, the way stop-motion studios do it:
character = head + expressions + hair + body + clothes (+ colours).

Standards (so any part fits any other):
- Children are Haru's size (1.26 m, head about 1/4.5 of the height). Women are about 1.65 m and men about 1.78 m, with
  heads about 1/7 of the height.
- Every head ends in a short neck peg, and every body has a short smooth neck where a head attaches.
- Hair is a wig shape that sits on the bald scalp of its head size (child or adult).
- Bodies wear a plain light grey base layer, so clothes and colours make the character.
- In code, `puppets/haru_clay.py` is the rig. Mika and Jun in `puppets/cast_camp.py` already work this way (a palette
  plus a hair shape).

## How to run (Artlist, Nano Banana)
- Attach `YTB/channel_art/haru_turnaround_sheet.png` as the reference image for every prompt.
- Use 16:9. Paste the prompt exactly as written. Generate 4 and keep the best in `YTB/channel_art/kit/`, with the
  generation id in the file name.
- Every prompt below is complete on its own, so there is nothing to fill in.

## Batch 1: heads

### Girl head
```
A character turnaround photo of a handmade stop-motion clay puppet head of a 10-year-old girl, shown four times in a row on a plain light grey background: front view, three-quarter view, side profile, and back of the head. The head is completely bald with no hair, a smooth round scalp and small ears. There is no body: the head ends under the chin in a short smooth neck peg. Round soft face, small chin, small dark dot eyes with a tiny white highlight, thin dark eyebrows, a small round nose, a small closed mouth, calm neutral expression. Warm tan matte plasticine skin with soft fingerprints and tool marks, nothing glossy. Exactly the same clay style, skin and face as the girl in the reference image. Soft even studio light, sharp focus, all four heads the same size, no text.
```

### Boy head
```
A character turnaround photo of a handmade stop-motion clay puppet head of a 10-year-old boy, shown four times in a row on a plain light grey background: front view, three-quarter view, side profile, and back of the head. The head is completely bald with no hair, a smooth round scalp and slightly big ears. There is no body: the head ends under the chin in a short smooth neck peg. Round face, a slightly wider nose than a girl's, small dark dot eyes with a tiny white highlight, thin dark eyebrows, a small closed mouth, calm neutral expression. Warm tan matte plasticine skin with soft fingerprints and tool marks, nothing glossy. Exactly the same clay style, skin and face as the girl in the reference image. Soft even studio light, sharp focus, all four heads the same size, no text.
```

### Woman head
```
A character turnaround photo of a handmade stop-motion clay puppet head of a woman about 35 years old, shown four times in a row on a plain light grey background: front view, three-quarter view, side profile, and back of the head. The head is completely bald with no hair, a smooth oval scalp and small ears. There is no body: the head ends under the chin in a short smooth neck peg. An oval adult face that is longer than a child's, a soft jaw, gentle cheekbones, small dark dot eyes with a tiny white highlight, thin dark eyebrows, a small nose, a small closed mouth, calm neutral expression. Warm tan matte plasticine skin with soft fingerprints and tool marks, nothing glossy. The same clay style and simple face style as the girl in the reference image, but an adult. Soft even studio light, sharp focus, all four heads the same size, no text.
```

### Man head
```
A character turnaround photo of a handmade stop-motion clay puppet head of a man about 40 years old, shown four times in a row on a plain light grey background: front view, three-quarter view, side profile, and back of the head. The head is completely bald with no hair, a smooth scalp and medium ears. There is no body: the head ends under the chin in a short smooth neck peg. A longer adult face with a square jaw, heavier dark eyebrows, a larger nose, small dark dot eyes with a tiny white highlight, a small closed mouth, calm neutral expression. Warm tan matte plasticine skin with soft fingerprints and tool marks, nothing glossy. The same clay style and simple face style as the girl in the reference image, but an adult man. Soft even studio light, sharp focus, all four heads the same size, no text.
```

## Batch 2: bodies

### Child body
```
A character turnaround photo of a handmade stop-motion clay puppet body of a 10-year-old child with no head, shown four times in a row on a plain light grey background: front view, three-quarter view, side view, and back view. The body ends at the top in a short smooth neck where a head will be attached later, and nothing is above the neck. Slim child proportions, long thin arms held slightly away from the body, open hands with long thin fingers, thin legs, feet flat on the ground. It wears a plain light grey fitted long-sleeve top, plain light grey fitted trousers and plain grey shoes, with no logos or details, so the body shape is easy to see. Matte plasticine with soft fingerprints and tool marks. The same clay style and proportions as the girl's body in the reference image. Soft even studio light, sharp focus, all four bodies the same size, no text.
```

### Woman body
```
A character turnaround photo of a handmade stop-motion clay puppet body of an adult woman with no head, shown four times in a row on a plain light grey background: front view, three-quarter view, side view, and back view. The body ends at the top in a short smooth neck where a head will be attached later, and nothing is above the neck. Average adult woman proportions, taller and longer-legged than a child, arms held slightly away from the body, open hands with long thin fingers, feet flat on the ground. It wears a plain light grey fitted long-sleeve top, plain light grey fitted trousers and plain grey shoes, with no logos or details, so the body shape is easy to see. Matte plasticine with soft fingerprints and tool marks, in the same clay style as the reference image. Soft even studio light, sharp focus, all four bodies the same size, no text.
```

### Man body
```
A character turnaround photo of a handmade stop-motion clay puppet body of an adult man with no head, shown four times in a row on a plain light grey background: front view, three-quarter view, side view, and back view. The body ends at the top in a short smooth neck where a head will be attached later, and nothing is above the neck. Average adult man proportions, broader shoulders, taller than a woman, arms held slightly away from the body, open hands with long thick fingers, feet flat on the ground. It wears a plain light grey fitted long-sleeve top, plain light grey fitted trousers and plain grey shoes, with no logos or details, so the body shape is easy to see. Matte plasticine with soft fingerprints and tool marks, in the same clay style as the reference image. Soft even studio light, sharp focus, all four bodies the same size, no text.
```

## Batch 3: hair (each one on a blank wig stand)

### Long straight hair (Haru)
```
A turnaround photo of a handmade sculpted clay wig for a stop-motion puppet, sitting on a smooth light grey egg-shaped wig stand with no face, shown four times in a row on a plain light grey background: front, three-quarter, side and back. Long straight jet-black hair past the shoulders with a side-swept fringe, sculpted as one solid clay mass with soft grooves and a few stray locks. Matte plasticine, no shine. The same hair as the girl in the reference image. Soft even studio light, no text.
```

### Bob with two buns (Mika)
```
A turnaround photo of a handmade sculpted clay wig for a stop-motion puppet, sitting on a smooth light grey egg-shaped wig stand with no face, shown four times in a row on a plain light grey background: front, three-quarter, side and back. A chin-length dark brown bob with a blunt straight fringe and two small round buns on top of the head, sculpted as one solid clay mass with soft grooves. Matte plasticine, no shine, in the same clay style as the reference image. Soft even studio light, no text.
```

### Two pigtails
```
A turnaround photo of a handmade sculpted clay wig for a stop-motion puppet, sitting on a smooth light grey egg-shaped wig stand with no face, shown four times in a row on a plain light grey background: front, three-quarter, side and back. Light brown hair with a centre parting, a short fringe and two pigtails tied low behind the ears with small red hair ties, sculpted as one solid clay mass with soft grooves. Matte plasticine, no shine, in the same clay style as the reference image. Soft even studio light, no text.
```

### Low bun (woman)
```
A turnaround photo of a handmade sculpted clay wig for a stop-motion puppet, sitting on a smooth light grey egg-shaped wig stand with no face, shown four times in a row on a plain light grey background: front, three-quarter, side and back. Black hair pulled back neatly into a low round bun at the back of the neck, with a few loose strands at the temples, sculpted as one solid clay mass with soft grooves. Matte plasticine, no shine, in the same clay style as the reference image. Soft even studio light, no text.
```

### Short messy hair (Jun)
```
A turnaround photo of a handmade sculpted clay wig for a stop-motion puppet, sitting on a smooth light grey egg-shaped wig stand with no face, shown four times in a row on a plain light grey background: front, three-quarter, side and back. Short messy black boy's hair made of soft rounded clumps, with a short fringe flicked to one side, sculpted as one solid clay mass. Matte plasticine, no shine, in the same clay style as the reference image. Soft even studio light, no text.
```

### Short side parting (man)
```
A turnaround photo of a handmade sculpted clay wig for a stop-motion puppet, sitting on a smooth light grey egg-shaped wig stand with no face, shown four times in a row on a plain light grey background: front, three-quarter, side and back. Short tidy dark brown men's hair with a neat side parting and short sides, sculpted as one solid clay mass with fine grooves. Matte plasticine, no shine, in the same clay style as the reference image. Soft even studio light, no text.
```

## Batch 4: expressions (attach the chosen head as the reference)

### Child expressions
```
Eight copies of the same bald stop-motion clay puppet head from the reference image, arranged in a grid of 4 across and 2 down on a plain light grey background, all facing the camera at the same angle and size. Each head has a different expression: calm neutral; worried with raised inner eyebrows; scared with a small round open mouth; terrified with wide eyes and the mouth open screaming; sad and crying; a small happy smile; suspicious with narrowed eyelids; a blank wide stare with tiny pupils. Small dark dot eyes, thin eyebrows and a simple mouth, exactly like the reference. Matte plasticine with fingerprints, soft even studio light, no text.
```

### Adult expressions
```
Eight copies of the same bald adult stop-motion clay puppet head from the reference image, arranged in a grid of 4 across and 2 down on a plain light grey background, all facing the camera at the same angle and size. Each head has a different expression: calm neutral; worried; angry with lowered eyebrows; laughing with the eyes shut; sad; surprised with raised eyebrows and an open mouth; screaming; a cold flat stare. Small dark dot eyes, thin eyebrows and a simple mouth, exactly like the reference. Matte plasticine with fingerprints, soft even studio light, no text.
```

## Batch 5: clothes (attach the chosen body as the reference)

### Example: knitted jumper and jeans on the woman body
```
A turnaround photo of the same headless stop-motion clay puppet body from the reference image, shown four times in a row on a plain light grey background: front, three-quarter, side and back. It now wears a chunky plum-coloured knitted jumper with visible stitches and soft folds at the elbows, blue jeans with seams and a slight crease at the knees, and white sneakers. The body shape, size and pose are exactly the same as the reference. Matte plasticine and clay fabric, soft even studio light, no text.
```
Change the garment and colour words for any outfit, and keep everything else the same.

## Next
- The elderly and teen heads, the other body types (slim and heavy), and the rest of the hair list will be written the
  same way.
- After each batch: rebuild the parts in code to the standard sizes, then make a test lineup that mixes them.

## Built so far (batch 1, 28 Nov)
Models in `library/kit/` (Tripo H3.1 image-to-3D, medium), source images in `YTB/channel_art/kit/` (Nano Banana 2,
Haru's turnaround attached). Test scene: `scenes/kit_lineup.py`, result `docs/kit_lineup_v1.jpg`.

| Part | File | Image generation | 3D generation |
|---|---|---|---|
| Girl head | head_girl.glb | 01a2202c-b9c1 | 01a2202e-43e5 |
| Boy head | head_boy.glb | 01a2202c-be8b | 01a2202e-4823 |
| Woman head | head_woman.glb | 01a2202c-c3fe | 01a2202e-4cb9 |
| Man head | head_man.glb | 01a2202c-d0ef | 01a2202e-5112 |
| Child body | body_child.glb | 01a2202c-d600 | 01a2202e-557c |
| Woman body | body_woman.glb | 01a2202c-dbd7 | 01a2202e-5b3d |
| Man body | body_man.glb | 01a2202c-e06c | 01a2202e-5f8c |
| Haru (full) | haru_full.glb | (user's image) | 01a22025-5348 |

Rules learned:
- Always image-to-3D from one object in one front view. Text-to-3D of a turnaround made three heads in one 1.5M-tri mesh.
- Tripo GLBs import facing +x: turn them -90 degrees (kit_lineup.py and haru_clay_match.py --yaw -90).
- Use `HC.apply_textured_clay` (keeps the model's colours under our clay). The palette sort (`apply_haru_clay`) breaks
  on Tripo textures because their baked shadows flip skin to hoodie.
- Heads get `skin='#f3bf9f'` so every head matches Haru's face.
- Kit sizes: head model = 27% of the height for children, 19% for adults; 35% of the head's height overlaps the neck.
  Neck widths fit within 0.95 to 1.27 (the man's head peg is a little wide, hidden by the collar).
