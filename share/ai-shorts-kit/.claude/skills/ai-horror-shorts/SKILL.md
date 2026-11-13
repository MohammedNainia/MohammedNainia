---
name: ai-horror-shorts
description: Make a slow-burn horror short (or any character skit) in the low-poly faceted 3D look, from AI still images animated in code. Character sheets, empty set, master wide shot, shot stills, then breathing, blinks, push-ins and silence in code. Use when the user asks for a horror short, a creepy story episode, a character skit in this style, or to continue one.
---

# AI horror shorts: stills first, motion in code

The look (big round heads, dot eyes, matte faceted clay, warm key light against deep blue shadow) does NOT come from 3D software. It comes from an image model that takes reference images (Nano Banana Pro works best), and the motion is added in code afterwards. Full background in `docs/SKITS_METHOD.md`.

Do every step with the user: show each result, let them pick, then move on. One change at a time.

## 0. Before starting
- Image tool: any image generator that accepts several reference images. With the Artlist connector use "Nano Banana Pro I2I 2K" (about 160 credits per image, generate 2 per call to pick from). Ask the user before spending credits on a new step, and quote the cost first when unsure.
- Style references: 2 frames from a reel in the target style, CROPPED so no captions or UI show (otherwise the model copies text). Upload them once and reuse them for every step.
- Format: 16:9 for long YouTube episodes, 9:16 for Reels/TikTok/Shorts. Decide once, keep it for the whole episode.
- Save every image in `stills/` with a clear name (`haru_sheet_a.png`, `master_b.png`) and keep a contact sheet preview to show the user.

## 1. Character sheets (one per character)
Inputs: the style references (+ a real photo if the character is the user).
```
Character turnaround sheet of ONE character shown three times side by side on a plain warm grey studio background: front view, three-quarter view, side profile view. Full body from head to feet, standing, neutral relaxed pose.

The character is [name], [age, who they are], in the EXACT art style of the reference images: low-poly faceted 3D animation style, matte clay-like materials with visible flat polygon facets, soft simplified shapes, big round head, very simple face with small black dot eyes each with one tiny white highlight, a tiny short line mouth, a tiny nose, warm soft studio lighting.

Identity: [hair], [glasses or not], [skin tone], [build]. They wear [outfit].

Same proportions and style as the characters in the style references. No text, no labels, no logos, no watermark.
```
For the monster, keep the same style ("it must look like it belongs in the same world as cute characters, which is what makes it wrong") and describe it plainly: height, skin material, hair, face (eyes with NO highlight are the single strongest creepy cue), clothes, hands. Calm and still, no gore.

## 2. Fix with edits, never regenerate
Edit the chosen sheet (pass it as the reference) and change ONE thing per edit:
```
Edit the reference image (the character turnaround sheet). Keep EVERYTHING the same: same three views, same style, same body, same clothes, same hair, same background, same lighting.

Only change the [FACE / MOUTH / OUTFIT], in all three views:
1. [the one change]
2. [optional second detail of the same change]

Same simple faceted style, not realistic, no blood, no gore. No text, no labels, no logos, no watermark.
```
Scarier faces that worked: larger empty black eye hollows with no highlight, one eye a little lower, faint stains running down from the eyes, a thin too-wide mouth, then small sharp teeth and a thin string of drool. Small, quiet details beat big gore.

## 3. Empty set
References: the style frames + the main character sheet (for style only).
```
Empty set, NO people, NO characters, NO creatures. [16:9 / vertical 9:16] film still. Same low-poly faceted 3D animation style, matte clay-like materials with visible flat polygon facets, and soft cinematic rendering as the reference images.

[The place, object by object, where things are, and one dark opening for the threat: a door left open a hand's width with pure black behind it, a deep shadowed corner].

Very dark horror mood: [one warm practical light] lights only [the main area], cold moonlight from [where], everything else falls into deep blue-black shadow. Shallow depth of field. Camera at [eye level / angle], wide shot. No text, no logos, no watermark.
```

## 4. Master wide shot
References in this order: character sheet 1, character sheet 2, the empty set. Say which is which by position.
```
[Format] film still. Use the third reference image as the exact location: same room, same furniture, same camera angle, same lighting, same style.

Place two characters in it, keeping their designs exactly as in their character sheets:
1. The [person] from the first reference sheet ([short description]). [pose, where, expression].
2. The [creature] from the second reference sheet ([short description]). [where it stands, how still, how much light reaches it].

Wide shot, both characters visible. No text, no logos, no watermark.
```
Horror tip: generate it twice, once with the threat hidden in shadow (the viewer finds it themselves) and once with the doorway EMPTY, so the threat can appear between two cuts.

## 5. Shot stills (6 to 10 per scene)
Always pass the master + the matching character sheet. Template:
```
[Format] film still, same scene, same characters, same style, same lighting and colours as the first reference image (the wide shot). [Shot type] of the [character] from the second reference sheet ([short description]), [pose and where they look], [expression], mouth closed. Empty space in the top third. No text, no logos, no watermark.
```
Horror set that covers a first scene: empty wide / sleeping close-up / eyes open / eyes turned to the door / the door gap with a face barely visible / the monster close-up / the victim sitting up frozen / the wide with the monster. Expression changes (eyes closed, open, looking aside) are separate stills: cross-fading between them IS the blink and the glance.

## 6. Direction (use the cinematic-director skill)
Before animating, write the beat sheet and shot list with the `cinematic-director` skill (its horror playbook): long locked wides with empty space, slow push-ins, a hard light contrast, shots that suddenly get very short at the scare, and silence.

## 7. Motion in code (the stills come alive)
- Slow push-in on every shot (1 to 4 percent zoom over the shot), strongest on the scariest beat. No shake, no grain, no jitter: check frame by frame.
- Cut characters out of the background (background removal model or masks) so they can breathe: a 1 to 2 percent vertical scale on the chest, which STOPS dead at the first sound.
- Blinks and glances: cross-fade between the expression stills (60 to 100 ms).
- Living background: lantern flicker (brightness noise on the warm area only), drool slowly stretching, dust in the moonlight.
- The threat never moves on screen in the first scene. It appears between cuts, or tilts its head once at the very end.
- Captions only if there is narration: word by word (Whisper), no box, never over faces. Horror often works better with no words at all.

## 8. Sound
True silence most of the time. Then single sounds: one footstep, a floorboard, a door sliding a few centimetres, a paper rustle. Never music under a scare. Put each sound slightly BEFORE the image that answers it.

## Rules
- Never write the long dash character in any title, caption, description or comment (viewers read it as AI text). Use a period or comma.
- Never commit API keys, OAuth files or tokens. They live in environment variables or the connector settings.
- Keep every generated image and the prompt that made it, so a later episode can reuse the same characters.
