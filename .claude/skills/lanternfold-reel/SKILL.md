---
name: lanternfold-reel
description: Make a new Lanternfold reel (9:16 paper cut-out philosophy short, ≤60 s) with the shared engine in YTB/lanternfold. Use when the user asks for a new reel, a new Lanternfold episode, or to continue/render one.
---

# Lanternfold reel workflow

Everything reusable lives in `YTB/lanternfold/`. Never rebuild from scratch: a new reel = one folder with `reel.json` + `scene.py` (+ voice + music).

```
YTB/lanternfold/
  make.py                 # one command for every step
  engine/                 # shared: paper.py (drawing), timing, ambience, render, finalize, audio, config
  reels/NN_slug/          # reel.json, scene.py, narration.txt, voice/line1..N.mp3, music.mp3, style/, build/
  PLAYBOOK.md             # human version of this file
```

## Channel rules (always)
- **Never use the long dash "—"** anywhere (titles, descriptions, captions, comments, narration, covers). Viewers read it as AI-written. Use a period, comma or question mark instead.
- Deep, philosophical, NEUTRAL: plant a question, show ≥2 answers with equal beauty, never moralise. End on a question + ~2 s stillness.
- 9:16, 1080x1920, 30 fps, ≤60 s. Last frame == first frame (loop).
- Captions 3–4 words, centred, top third (engine does this).
- Check every audio file is not silent before use (engine `audio.check` does this, never bypass).
- Keep tokens low: reuse engine helpers, render style frames at 360x640 contact sheets to inspect.

## Hook-first (from channel analytics: 94% of views come from the Shorts feed, so the first 1-2 s decide everything)
- NO black/slow intro. Frame 0 = the most striking shot, already moving. Add `"hook": {"text": ["Would you", "open it?"], "hold": 2.2}` to reel.json: the big question shows on frame 1 and returns at the end (seamless loop on the same frame).
- Titles are personal questions ("Would you…", "Are you…"), not concept names. Bright warm/cool contrast in the first frame. Search terms/tags matter little for Shorts.
- Shorter is fine (40-50 s) if it keeps people watching.

## Steps
1. **Concept → reel.json + narration.txt.** Copy the latest reel folder as a template. Fill `lines` (`say` with ElevenLabs v3 tags, `chunks` for captions, `beat` = story second the line belongs to, `lead`, `hold_after` 2.2 on the line before the final question), `stillness`, `chimes`, `music_prompt`. Story time is 0–55 s; the engine maps it to the voice.
2. **Environment (every reel gets a place that fits its idea, not always the navy hill).** Run `python make.py envs` to see the presets in `engine/environments.py` (night_hills, dusk_sea, desert_moon, snow_peaks, city_roofs, autumn_forest, space_planet, firefly_meadow). Pick the one whose mood matches the question; vary across consecutive reels. If none fits, add a new preset dict (copy the closest, change sky/sun/moon/layers/weather; layer kinds: hills, dunes, mountains, sea, city, forest, flat, stage with form mound|ledge). Store the choice as `"env"` in reel.json. A reel may switch environments mid-story (e.g. split worlds).
2b. **Art type** (vary it per reel, like the environment; all CPU-only, free, no AI images):
   - Post-process styles via `"style"` in reel.json (engine/styles.py): `paper` (signature), `watercolor`, `ink`, `stained_glass`, `chalk`, `comic` (ink outlines, halftone, panel frame), `manga` (B&W screentone), `pixel` (16-colour dithered pixel art), `flat` (clean flat-vector: paper texture switched off). Preview: `python make.py styles reels/NN_slug <sec>`.
   - **Low-poly 3D** (engine/lowpoly3d.py): build the scene in scene.py with `Scene3D`, `icosphere`, `terrain`, `tree`, `figure`, `box`, `cone`, `look_cam`; `frame(t)` returns `(sc.render(cam)*255).astype(uint8)`. Animate by moving the camera / objects with t. ~0.3 s per frame.
   - **Explainer kit** (engine/explainer.py `Overlay`): callouts, arrows, counters (linear/log), timelines, scale bars, pulsing rings, titles, all revealed with a progress p. Use for science/fact reels on top of any style.
   - Pick the art type that fits the question; avoid repeating the same type twice in a row.
3. **scene.py**: `frame(t)` in story seconds using `engine.environments.draw_env(img, L, cam, t, ENVS[cfg['env']], reveal)` for the place (returns `ground(x)` for where characters stand) plus `engine.paper` (Cam, sky, stars_layer, hill_poly, paper_layer, person, lantern, glow, composite_fig, finish, set_reveal). Keep a loop anchor (a light that survives the fade) identical at t=0 and t=DUR.
4. **Style frames**: `python make.py reels/NN_slug frames 8 22 34` → send 2–3 frames + narration.txt and **WAIT for approval**.
5. **Voice (Artlist, after approval)**: generate_voiceover per line with Eleven v3, voice "Charmed" (British), stability 0.5, same Artlist folder. Download each to `voice/lineN.mp3` (curl the assetUrl; needs the session environment that allows cms-toolkit-artifacts.artlist.io).
6. **Music (Artlist)**: generate_music with Lyria 3 Pro – T2M – Instrumental, duration 60, prompt from reel.json → save as `music.mp3`. Do NOT use catalog tracks/SFX: the plan has no catalog licence (watermarked / blocked).
7. **Build**: `python make.py reels/NN_slug all 4` (timing → ambience → render → finalize). Render is resumable; if a worker dies just re-run.
8. **Check**: contact sheet of 6–8 frames of the final MP4 + first/last frame diff; then send the 1080x1920 file, 720p preview and captions.srt.
9. **SEO**: title (hook + question), description, tags, pinned comment for YouTube/TikTok/Instagram.
10. **Cover**: add `"thumb": {"t": <story sec of the most telling frame>, "text": ["short", "question?"], "size": 150, "y": 300}` to reel.json and run `python make.py reels/NN_slug thumb` → thumbnail_1080x1920.jpg (title in upper-middle band, clear of the platform UI). Send it with the reel.
11. Commit + push the reel folder (MP4s are git-ignored).

11. **Pre-upload check (always)**: `python make.py reels/NN_slug check` (also runs at the end of `all`). Fix every FAIL; read the WARNs (still first second, fast narration, captions under app buttons, weak title...). Then `python make.py reels/NN_slug safe` → safezones.png shows the reel under YouTube / Instagram / TikTok buttons.
12. **Topic timing**: before picking a topic, `python ../research/research.py trends "topic a" "topic b"` (YouTube searches, last 90 days: RISING / steady / fading + rising related searches). Prefer rising topics; use rising searches as tags.

### Word-timed captions + sound effects
- Captions are timed to each spoken word by Whisper (faster-whisper base.en, CPU, cached in build/words.json) and the word being said turns gold (karaoke). `"captions": "plain"` in reel.json turns the highlight off. Falls back to estimated timing if Whisper is unavailable.
- Sound effects: `"sfx": [[story_sec, "paper rustle", 0.4], [14, "whoosh", 0.5], ...]` in reel.json; finalize mixes them in (after the music ducking, before loudness). Freesound (CC0 only by default) when reachable - the cloud server is blocked by Freesound, so there it uses built-in paper sounds: whoosh, paper/rustle/page, thud/drop/heartbeat, tick/click/clock, chime/bell, twinkle/sparkle. `"synth:whoosh"` forces the built-in one. Put one on each big cut/reveal, volume 0.3-0.5; never under a spoken word. Browse: `python make.py sfx "paper whoosh"`.

## Gotchas
- Lyria often rejects long/descriptive music prompts as a false content-safety violation (no credits charged). Keep prompts short and plain, e.g. "Calm solo piano, slow and gentle, soft celesta, warm reverb, light ambient pad, quiet intro and a soft ending. Instrumental." and retry once if blocked.
- Music sits quietly under the voice: default music_volume 0.32 (the user asked for a soft piano). Don't raise it unless asked.
- Default art type is `paper` (the channel's look); use other styles/kits only when the user asks.
- Credits: voice ≈ 100, music 300 (Lyria 3 Pro 60 s). Quote with get_generation_cost if unsure.
- If the voice runs long, timing prints a WARNING > 60 s: cut `hold_after`/`max_pause` or a phrase, regenerate that line only.
- `glow()` must stay uncached (an earlier cached version leaked 10 GB and got OOM-killed).
- Windows: config.py points at the user's imageio ffmpeg; fonts fall back to Georgia.
