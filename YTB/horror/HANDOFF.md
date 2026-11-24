# Handoff: PaperLit horror pipeline (read this first in a new session)

Channel: PaperLit (YouTube @paperlit, channel UCEPxEir-yy6bpwdue24CLlA). **YouTube only** for now (Instagram and TikTok dropped).
Branch: `claude/dead-star-philosophy-reel-2kq6ee`. Commit + push there; no PRs unless asked. Never use the long dash in any text.

## Style and rules
- POSTING TIME: the user's clock is GMT+00 (same as UTC). Post one Short a day around 22:00 GMT (best window 21:30 to 03:30 GMT, from channel stats Nov 13 to 18). Never 16:9 for horror.
- FORMAT FROM NOW ON (user, Nov 17 2026): every reel is ONE complete story like "The Path" (YTB/horror/the_path):
  9:16, 2:00 to 2:59 (stays a Short), Haru at the centre, a simple rule the world follows, Haru's own choice/flaw drives it,
  a twist that recontextualises everything, a clear ending that leaves one unspoken question (the loop goes back to the hook shot).
  Outcome-first hook spoken + on screen at frame 0. Script audited with writing-principles/storyteller before voicing.
  Close-ups on the key moments; sound motifs set up early and paid off (e.g. the bracelet, the breathing).
- ENGLISH ONLY until the user says otherwise (Darija / Facebook versions on hold).
- Every reel needs a clear, understandable ending (a closer line that makes the threat obvious, e.g. "I live alone.")
  and close-ups on the key reveal so it reads at a glance on a phone.
- Pure horror (no philosophy question). Real, everyday situations that turn wrong; horror carried by sound and ambiguity.
  Avoid the "it gets closer every time" mechanic and "wish" stories (user says they are overused / didn't like).
- Look: low-poly faceted 3D built in three.js (YTB/horror/three). From Nov 19 the user also likes DARK CLAY stop-motion (scenes/clay.js, human-anatomy Haru); Artlist plan has NO sound-effects downloads; Freesound key needs the value `Token <key>`. Haru = main character (yellow hoodie or pyjamas, long black hair, dot eyes).
- Voice: Samara X (Artlist voice id 224933), Eleven v3, voice_stability 0.5, **one generation per line**, gentle tags
  ([whispering], [softly], [nervous], [scared]). See YTB/horror/VOICE.md. Second voices: "Assistance" (id 44) was Mum.
- Captions: white, sentence-safe chunks; other speakers in pink italic. Hook text on frame 0; reels loop (last frame = first).
- Loudness -14 LUFS (two-pass loudnorm in each post.py).

## Skills
- writing-principles + storyteller (.claude/skills): use them to write and audit every script (causality, a flaw/choice for Haru, setups that pay off, no explaining feelings).
- Hooks: state the outcome in the first line ("I walked my whole village to the mountain. I got there alone."), spoken AND on screen at frame 0.
- Shorts can be up to 3:00: keep 9:16 one-video stories under 2:59 (compress in-line pauses, see the_path/voice/cut.py).
- camera-cinematography (.claude/skills/camera-cinematography): use it when planning shots, lenses and camera moves for any scene.
- bang-motion: HTML + GSAP motion graphics (openers, title cards, kinetic type, explainers; 9:16 or 16:9, renders to MP4). Use for intros/outros, series title cards, thumbnail-style text animation.
- claude-drawing: code-painted images in 83 styles (ink wash, ukiyo-e, VHS, cave painting, pencil...), numpy + Pillow only, draw-on GIFs. Use for 2D story art, posters, the "photo"/drawing inserts.
- huashu-art-motion: animated paintings / art-style explainer clips (35+ styles, mostly Chinese docs; README.en.md in English). Needs uv + Playwright.
- vox-director: Vox-style paper-collage explainers. Needs a paid Atlas Cloud API key (ATLASCLOUD_API_KEY), not set up yet.
  (All four from the "4 repos" list: bangtutorial/bang-motion, cloveric/claude-drawing-skill, alchaincyf/huashu-art-motion,
  Alisa0808/vox-director; MIT; installed without their demo media.)

## Pipeline (see YTB/horror/mum as the latest complete example)
1. Script -> generate voice lines (Artlist) -> faster-whisper word timings -> layout.json (line starts) + words.json.
2. Scene: YTB/horror/three/scenes/<name>.html using scenes/lib.js (person(), flat(), mesh(), canvasTex(), post FX).
   Check frames here: `node render.js --cpu --scene <name> --frames 0,300,...` (add `--landscape` for 16:9).
3. Final render on the user's PC GPU (RTX 5090) via their local agent:
   `node render.js --gpu --scene <name> --dur <sec> --out ..\<name>\raw.mp4` then `git add -f raw.mp4` and push.
   Long 16:9 videos: split with `--start/--dur` and `--maxrate 9M` so each file is < 95 MB.
4. `python post.py` in the project folder: captions, hook, narration, sound design -> final mp4.
5. Post with vidIQ: vidiq_video_upload (localFile + run the given curl command) -> vidiq_social_post_draft_create
   (YouTube, public, category 24) -> show the user -> vidiq_social_post_publish only after they say go.
   Thumbnails: upload via a raw.githubusercontent.com URL (mcp.vidiq.com upload URL is blocked here).

## Done so far
- Floor 13 (Short), The Keeper's Rules Part 1 (16:9, 2:43, https://www.youtube.com/watch?v=KngNLKLPzas), Part 2 "The Light Stopped" (16:9, 2:31, https://www.youtube.com/watch?v=X2a-0pQ_ov0, thumbnail "THEY WERE ON THE STAIRS / PART 2"), Part 3 "The Last Keeper" (final, 16:9, 2:01, https://www.youtube.com/watch?v=iHF9rADSaGI), Mum? (Short), Baby Monitor (Short, 71 s, https://www.youtube.com/watch?v=VBFJkhn1cy0), Baby Monitor Part 2 (Short, 57 s, https://www.youtube.com/watch?v=HEXrLwstn0g), Baby Monitor Part 3 / final (101 s, https://www.youtube.com/watch?v=Og5Wlfrve7c), Doorbell Camera (62 s, https://www.youtube.com/watch?v=3j97KUMR9LI), The Path (9:16, 2:58, https://www.youtube.com/watch?v=K-eyH8zZ_T0, one complete story; see YTB/horror/the_path, scene three/scenes/the_path.html; rendered in 3 parts raw_a/b/c, joined into raw.mp4 before post.py), Black Sky (9:16, 2:58, https://www.youtube.com/watch?v=rPJ6qMx5am4, user's premise; see YTB/horror/black_sky, scene three/scenes/black_sky.html), The Pie (9:16, 84.5 s, https://www.youtube.com/watch?v=xhH4ch-fZwU, user's premise, visual-first; phone-screen overlay in post.py), The Tooth Fairy (9:16, 88.6 s, https://www.youtube.com/watch?v=QXfLo8ff_qE, user's premise, FIRST DARK CLAY STOP-MOTION video: scenes/clay.js kit (clay materials, boil, makePerson/makeFairy) + scenes/tooth_fairy.html; sound in tooth_fairy/post.py, real recordings dropped into tooth_fairy/sfx/ replace the synthesized cues), Thanksgiving (9:16, 93.4 s, https://www.youtube.com/watch?v=NVEPSruoTzg, dark clay; the thing under the table speaks an invented dead language, caption '(is she ready?)'; scene three/scenes/thanksgiving.html, post in thanksgiving/post.py), The Vacancy (9:16, 74.2 s, https://www.youtube.com/watch?v=GBh0-loW6i0, user's premise; FIRST REEL BUILT FROM THE CLAY LIBRARY (data/lib, lib_sets.js, moves.js): scene three/scenes/vacancy.html, post in vacancy/post.py), The Pattern (9:16, 75.2 s, https://www.youtube.com/watch?v=ERJEaHH1R-I, Egypt school trip, user's premise; cult, goat and pyramid built in code because Artlist credits ran out; scene three/scenes/pattern.html, post in pattern/post.py), The Night Count (9:16, 69.6 s, https://www.youtube.com/watch?v=x6DN3S5Le7I, hospital night nurse; Haru's narration from the user's local VoiceStudio; FIRST REEL WITH CONTACT FITTING (scenes/contact.js: sitOn/lieOn/drape, check with `node check_contact.js --scene night_count` before rendering); scene three/scenes/night_count.html, post in night_count/post.py), Don't Turn Around (9:16, 12 s, WORDLESS LOOP, first test of the format the competitor study points to (YTB/horror/research/COMPETITORS.md): Haru and a snowman that moves when she looks away; scene three/scenes/snowman.html, sound synthesized in snowman/post.py; https://www.youtube.com/watch?v=FTBoaqQGOtc): all posted. The Baby Monitor story is finished.
- Darija versions on the Facebook Page قصص هارو المرعبة (YTB/horror/facebook): Part 1 https://www.facebook.com/reel/1300685672216645 , Part 2 https://www.facebook.com/reel/3061539507571879 , Part 3 https://www.facebook.com/reel/4490946704487451 .
  Darija voices come from the user's VoiceStudio (OmniVoice) via their local agent; one render serves both languages (fixed line slots, see baby_monitor2).
- The Keeper's Rules is finished (3 parts).

## DONE: "Baby Monitor" (posted; see YTB/horror/baby_monitor, scene three/scenes/baby_monitor.html)
Monitor voice used: Artlist "Hushed" (id 28), pitched down and band-limited in post.py. The final render was done on the user's GPU (38 s).
Original plan:
Haru (Samara) + the voice on the monitor (a soft older woman; crackly, close-miked, band-limited in the mix).
1. Haru [whispering]: The baby monitor picked up someone singing. I was the only one home.
2. Haru [softly]: I was babysitting. The baby was asleep upstairs. I was on the couch, half asleep, with the monitor next to me.
3. Monitor (humming a lullaby): Hush now... hush now, little one...
4. Haru [nervous]: I thought it was a radio. Interference. Monitors do that.
5. Haru [whispering]: But then it stopped humming... and it laughed. Softly. Like someone leaning over the crib.
6. Haru [scared]: I ran upstairs. The nursery door was open. The baby was asleep. And there was nobody there. Nobody.
7. Haru [softly]: I checked the closet. Under the crib. Behind the curtains. Nothing.
8. Haru [whispering]: So I went back downstairs... and sat down next to the monitor.
9. Monitor (very close, whisper): Shh... she's gone. You can open your eyes now.
10. Haru [whispering]: It wasn't singing to the baby. It was waiting for me to leave.
Visuals: dark living room, monitor sound-LEDs jumping; nursery with a rotating star nightlight projector; the search (closet,
crib, curtains); final shot on the monitor's night-vision screen (render-to-texture): the baby's eyes open and a pale hand rests on
the crib rail, inside the room she just checked. Reuse the house from scenes/mum.html.
