# ALLO FLOUSSI: finishing guide (60s film)

Everything is in the `allo-floussi/` folder. It is also in Artlist → Default Project → **"ALLO FLOUSSI – Phase 1"**, where the storyboard frames can be animated directly.

| What | File |
|---|---|
| **Animatic** (the full 60s film as timed stills with music and narrator). It is a fallback cut and your edit template. | `ALLO-FLOUSSI-animatic-60s.mp4` |
| Start frames for every video shot | `storyboard/s01.jpg … s17.jpg` |
| Character sheets + locations (use as extra references if a face drifts) | `phase1/` |
| App UI animation (shot 11), ready to drop in | `motion/shot11-app-ui-1080p.mp4` |
| Logo reveal + slogan (shot 19), ready to drop in | `motion/shot19-logo-reveal-1080p.mp4` |
| Music: take 1 (58s, follows the cue sheet) / take 2 (longer, more epic) | `audio/music-take1-58s.mp3`, `audio/music-take2-148s.mp3` |
| Narrator lines (Darija) | `audio/vo-1-mashakil-sghar.mp3`, `audio/vo-2-allo-floussi-endline.mp3` |
| Subtitles FR / EN | `subtitles/allo-floussi-FR.srt`, `subtitles/allo-floussi-EN.srt` |
| Editable motion-graphic sources (HTML) | `motion/app.html`, `motion/logo.html` |

---

## 1. Generate the video shots (image-to-video)

**Settings for every shot:**
- Image-to-video, 16:9, 1080p, 24 or 30 fps
- **Audio OFF**: music and voices come from the files above
- 5s clips; you'll trim them in the edit
- Good models: **Kling 3 / 4.0 Pro**, **Veo 3.1**, **Seedance 2.5**. Kling and Seedance hold faces best from a start frame.
- Upload the storyboard frame as the **start frame** and paste the prompt.

**Add this line to the end of every prompt:**
> `Cinematic 35mm film look, anamorphic, shallow depth of field, natural skin texture, subtle film grain, realistic understated performance, no text, no logos, keep the face, hair and clothing exactly as in the image.`

| Shot | Start frame | Use (s) | Video prompt (motion only) |
|---|---|---|---|
| 1 | `s01.jpg` | 3 | Slow, steady aerial push-in over the Casablanca rooftops toward the single glowing apartment window; the sunset sky darkens slightly; birds cross the frame in the distance. Ignore and remove the thin blue streak across the skyline. |
| 2 | `s02.jpg` | 2 | Handheld medium close-up. The mother tastes from the wooden spoon, pauses, frowns slightly, then turns her head toward the hallway as if calling someone. Steam drifts across the foreground. |
| 3 | `s03.jpg` | 2 | Close insert. The boy's hand slowly slides the folded banknote across the counter toward the cashier; the digital display glows; slight camera push-in. |
| 4 | `s04.jpg` | 2 | The cashier holds up the banknote and gives a gentle apologetic shrug, shaking his head slightly; the boy's face falls a little. Very slow push-in. |
| 5 | `s05.jpg` | 3 | Four friends laughing naturally around the tea table; the man in the linen shirt raises his hand playfully as if saying "this one's on me"; the others react with laughs; string lights sway slightly. Slow crane down. |
| 6 | `s06.jpg` | 3 | The waiter holds the saucer with the bill and banknote, apologetic; the seated man's smile fades into an awkward half-laugh as he looks up at him. Slow push-in. |
| 7 | `s07.jpg` | 3 | Steadicam drifting backwards. The man holds a red rose, glances down at his glowing phone and smiles nervously; leaves move in the backlight. |
| 8 | `s08.jpg` | 3 | Over-the-shoulder. The florist holds the bouquet and the banknote and gently shakes her head; the man's shoulder shifts slightly in the foreground. Rack focus from banknote to her face. |
| 9 | `s09.jpg` | 3 | Long-lens shot across the street. The young woman smiles and waves; cars pass blurred in the foreground; warm backlight. |
| 10a | `s10a.jpg` | 1 | Locked-off close-up. The boy lifts the phone to his ear and looks up with quiet hope. Almost still. |
| 10b | `s10b.jpg` | 1 | Locked-off close-up. Same action and timing: the phone to his ear, a hopeful look up. |
| 10c | `s10c.jpg` | 1 | Locked-off close-up. Same action and timing: the phone to his ear, a hopeful look up. |
| 11 | **use `motion/shot11-app-ui-1080p.mp4`** | 5 | Not AI. Optionally composite it onto a hand-held phone. |
| 12 | `s12.jpg` | 4 | The rider glances at his phone, smiles, zips the pouch of counted banknotes, picks up the helmet from the scooter seat and starts putting it on. Wet street reflections shimmer. |
| 13 | `s13.jpg` | 4 | Low tracking shot. The rider accelerates along the wet boulevard; the tram streaks past with motion blur; city lights stream; the camera races alongside at wheel height. |
| 14 | `s14.jpg` | 2 | The rider hands the boy the small stack of banknotes; the boy takes it, smiles with relief, and they exchange a natural nod. |
| 15 | `s15.jpg` | 4 | **Slow motion.** The mother touches her son's cheek tenderly; he leans in and kisses her forehead; she closes her eyes and smiles. Steam drifts. |
| 16 | `s16.jpg` | 3 | **Slow motion.** The friends burst into laughter; one throws an arm around the other's shoulders; one claps; string lights glow. |
| 17 | `s17.jpg` | 5 | **Slow motion.** The young woman holds the roses and rests her head on his shoulder, eyes closed, smiling; he looks down at her; sun flare through the trees; slow orbit. |
| 18 | `s15`/`s16`/`s17` (or new) | 1 | Quick montage. Optional extras: a family dinner table, friends at night, the couple walking away, the cashier smiling at a customer. |
| 19 | **use `motion/shot19-logo-reveal-1080p.mp4`** | 5 | Not AI. |

**If a face drifts:** regenerate it as reference-to-video. Give the model the start frame plus that character's sheet from `phase1/`, e.g. `07-karim.jpg`.

**Rider's jacket logo:** if you show the back of the jacket, add your real logo in the edit with motion tracking. Don't let AI draw it.

---

## 2. Edit timeline (open the animatic next to your timeline and match it)

| Time | Picture | Sound |
|---|---|---|
| 0:00–0:03 | 1 | Music take 1 starts (piano) |
| 0:03–0:05 | 2 | Kitchen sizzle. Mama: **"ولدي، جيب ليا غير شي حاجة من الحانوت."** · Son (off-screen): **"واخا ا ماما."** |
| 0:05–0:07 | 3 | Store beep, fridge hum |
| 0:07–0:09 | 4 | **Music down to ~0%.** Cashier: **"آ ولدي، ما عنديش الصرف."** |
| 0:09–0:12 | 5 | Music back. Amine: **"اليوم عليا أنا!"** Laughter, tea glasses |
| 0:12–0:15 | 6 | **Music down at 0:13.** Waiter: **"سمح ليا خويا، ما عنديش الصرف."** |
| 0:15–0:18 | 7 | Music back. Tram bell, a phone message ping |
| 0:18–0:21 | 8 | **Music down at 0:19.** Florist: **"ما عنديش الصرف، خويا."** |
| 0:21–0:24 | 9 | One low piano note |
| 0:24–0:27 | 10a/b/c | Each character says **"ألو؟"**, three voices overlapping. Then the phone ring |
| 0:27–0:32 | 11 (app) | UI ticks; strings rise |
| 0:32–0:36 | 12 | **VO 1** at 0:32.5 (music ducked to ~45%) |
| 0:36–0:40 | 13 | Scooter engine whoosh |
| 0:40–0:42 | 14 | |
| 0:42–0:46 | 15 | Mama: **"الله يرضي عليك ولدي."** Orchestral crescendo |
| 0:46–0:49 | 16 | Laughter |
| 0:49–0:54 | 17 | Peak resolves |
| 0:54–0:55 | 18 | Montage |
| 0:55–1:00 | 19 (logo) | **VO 2** at 0:55.6; music fades out at 0:58.5 |

**Character dialogue:** the AI Arabic voices read Darija with a standard-Arabic accent. **For real Moroccan authenticity, record the 7 short lines on a phone with friends or family** in a quiet room. It takes 10 minutes and sounds far better. The same goes for the narrator, if you have a warm Moroccan voice available; my two narrator files are a usable placeholder.

**Sound effects:** search Artlist SFX or Freesound for: kitchen sizzle, convenience-store door chime, barcode beep, fridge hum, tea glass clink, tram bell, scooter pass-by, phone ring, message ping.

**Grade:**
- Warm amber for the family scenes, apricot and sunset for the friends and the couple.
- Cool and desaturate slightly on the three "no change" lines.
- Bring the warmth back stronger after the rider arrives.
- Keep green and blue only on the rider, the app and the logo.

**Exports:**
- 16:9 1080p master
- 9:16 version: reframe, keeping faces centred; the animatic frames were composed with safe centres

---

## 3. Fast fallback (if you run short of time)

`ALLO-FLOUSSI-animatic-60s.mp4` is already a complete, presentable 60s piece: slow Ken Burns moves, the score with its silences, the app UI, the narrator and the logo.

Generate only the **hero shots** as video: 5, 13, 15, 16 and 17 (the laughter, the ride and the payoffs). Cut them over the animatic and the film feels alive for about 5 generations.
