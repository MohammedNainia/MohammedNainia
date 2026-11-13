# How the reference reels are made (from the creator's own guide, @hashhh.co, Notion "How I make my AI skits")

They are not 3D renders. They are AI still images, animated in code.

Pipeline: character sheet > empty set > 6 stills > script > voices > code animates and edits.

| Tool | Used for |
|---|---|
| ImagineArt (Nano Banana Pro) | characters, set, the 6 stills (any image tool that takes reference images works) |
| ElevenLabs v3 | voices, stability ~0.3, one file per line, emotion tag first: `[deadpan]`, `[softly, sincere]` |
| Claude Code + Remotion | cutouts, breathing, lip sync from loudness, blinks, push-ins, living backgrounds, captions |
| Whisper | word timings for captions and lip sync |
| FFmpeg | audio cleanup |

## Steps
1. Character sheet: 1 clear photo + 2 style screenshots as references, 16:9, turnaround prompt (front, three-quarter, profile, plain warm grey background, "low-poly faceted 3D animation style, matte clay-like materials with visible flat polygon facets, small black dot eyes, tiny short line mouth, warm soft studio lighting").
2. Fix with edits, one change at a time, always starting "Keep EVERYTHING the same".
3. Sidekick sheet using the finished sheet as style reference. No mouth (the mouth is animated in code).
4. Empty set, 9:16, no characters. "Warm light on the main area, cool shadows everywhere else, shallow depth of field."
5. Characters placed in the set (3 references: sheet, sidekick sheet, set) = the wide master shot.
6. Six stills from the master: wide; A medium close-up; B close-up; A reaction; B very tight low angle (emotional); from behind (room for cards). Template ends "mouth closed. Empty space in the top third."
7. Script: 40 to 50 s, a new line (and a cut) every 2 to 2.5 s, 1 to 8 words per line, hook with the other character's name, one sincere beat then undercut, callback ending, spoken CTA. Write with commas, not full stops.
8. Voices as above.
9. Code: trim and join lines, Whisper timings, cut per line, slow push-in per shot (strongest on the emotional line), cut characters out so they breathe, fill the background behind them, mouth from loudness, natural blinks, word-by-word captions (Montserrat, no box, never over faces), no grain or jitter.
10. Post 1080x1920 30 fps; caption repeats the joke, comment gate, end with a question, reply to everything in the first hour.
