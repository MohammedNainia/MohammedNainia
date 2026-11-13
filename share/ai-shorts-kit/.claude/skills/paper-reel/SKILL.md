---
name: paper-reel
description: Make a 9:16 short (up to 60 s) with the code-drawn engine in engine_reels/: paper cut-out, watercolor, ink, comic, manga, pixel, flat or low-poly 3D art, voice lines, word-timed karaoke captions, sound effects, music, cover image and a pre-upload check. Use when the user asks for a new reel, a philosophy or question short, or to continue or render one.
---

# Paper reel workflow

Everything reusable lives in `engine_reels/`. Never rebuild from scratch: a new reel = one folder with `reel.json` + `scene.py` (+ voice + music). Copy `engine_reels/reels/example_would_you_listen/` as the template.

```
engine_reels/
  make.py                 # one command for every step
  engine/                 # paper.py (drawing), environments, styles, lowpoly3d, explainer, timing, ambience, render, finalize, audio, sfx, check
  sfx_library/            # built-in sounds (whoosh, rustle, thud, tick, chime, twinkle, heartbeat)
  reels/NN_slug/          # reel.json, scene.py, narration.txt, voice/line1..N.mp3, music.mp3, build/
```

Setup once: `pip install numpy pillow faster-whisper imageio-ffmpeg` (FFmpeg on PATH also works; or set the `FFMPEG` environment variable).

## Rules that made reels perform
- Hook first: frame 0 is the most striking shot, already moving. No slow intro. `"hook": {"text": ["Would you", "open it?"], "hold": 0.1, "fade": 0.3}` shows the big question on frame 1 only (it becomes the profile-grid cover) and again at the end for a seamless loop. Keep frame 0's subject between y 240 and 1680 (Instagram's 3:4 grid crop).
- Titles are personal questions ("Would you...", "Are you..."), not concept names.
- Comments come from taking sides, not yes/no: name two camps, pin a comment that takes a soft stand people can push against, end on an identity choice ("Which one are you?").
- Neutral and deep: plant a question, show 2 answers with equal beauty, never moralise, end on the question + about 2 s of stillness.
- 1080x1920, 30 fps, 40 to 60 s. Last frame == first frame (loop). Plan a visual turn or a "but..." line at 8 to 10 s, where viewers usually leave.
- Never use the long dash character anywhere (titles, captions, narration, comments).
- Check every audio file is not silent before use (`audio.check`, never bypass).
- Inspect with small contact sheets (360x640) to keep tokens low.

## Content skills (use on every reel)
- **virality**: 8-point hook checklist on frame 0 + line 1 before writing narration.
- **going-viral**: pick the goal (shares, saves, follows) and the emotion that drives it.
- **humanizer**: run on narration, captions, descriptions and replies before publishing.
- **caption-and-hashtags**, **comment-mining**, **content-audit**: post copy, next topics from comments, weekly audit.

## Steps
1. **Concept: reel.json + narration.txt.** Fill `lines` (`say` with ElevenLabs v3 emotion tags like `[softly]`, `chunks` for captions, `beat` = story second, `lead`, `hold_after`), `stillness`, `chimes`, `music_prompt`. Story time 0 to 55 s; the engine maps it to the voice.
2. **Environment**: `python make.py envs` previews the presets (night_hills, dusk_sea, desert_moon, snow_peaks, city_roofs, autumn_forest, space_planet, firefly_meadow, gothic_castle). Pick the one that fits the idea, vary across reels; add a new preset dict if none fits. Store it as `"env"`.
3. **Art type** via `"style"`: paper, watercolor, ink, stained_glass, chalk, comic, manga, pixel, flat. Preview: `python make.py styles reels/NN_slug <sec>`. Low-poly 3D: build the scene with `engine/lowpoly3d.py`. Explainer overlays: `engine/explainer.py`.
4. **scene.py**: `frame(t)` in story seconds using `draw_env(...)` plus the `engine.paper` helpers (Cam, sky, person, lantern, glow, finish). Keep one loop anchor identical at t=0 and the end.
5. **Style frames**: `python make.py reels/NN_slug frames 8 22 34`, show them with narration.txt and WAIT for approval.
6. **Voice** (any TTS with emotion control; ElevenLabs v3 works well, stability about 0.3 to 0.5): one file per line, `voice/line1.mp3` ... Write with commas, not full stops, so it sounds human.
7. **Music**: a short, plain instrumental prompt (long descriptive prompts often get falsely blocked). Keep it quiet under the voice (music_volume about 0.32). Save as `music.mp3`.
8. **Build**: `python make.py reels/NN_slug all 4` (timing, ambience, render, finalize, check). Render is resumable.
9. **Check**: `python make.py reels/NN_slug check` (fix every FAIL) and `python make.py reels/NN_slug safe` (the reel under YouTube, Instagram and TikTok buttons).
10. **Cover**: `"thumb": {"t": <sec>, "text": ["short", "question?"], "size": 150, "y": 300}` then `python make.py reels/NN_slug thumb`.
11. **Post copy**: title (hook + question), description, tags, pinned comment for each platform.

## Captions and sound effects
- Captions are timed per word by Whisper (faster-whisper base.en, CPU) and the spoken word turns gold. `"captions": "plain"` turns the highlight off.
- `"sfx": [[story_sec, "paper rustle", 0.4], [14, "whoosh", 0.5]]` in reel.json. Uses Freesound (CC0) when `FREESOUND_KEY` is set, otherwise the built-in sounds. One per big cut, volume 0.3 to 0.5, never under a spoken word.

## Gotchas
- If the voice runs past 60 s, timing prints a WARNING: trim `hold_after`/`max_pause` or a phrase and regenerate that line only.
- `glow()` must stay uncached (a cached version once used 10 GB of memory).
