# Horror narration voice (from Nov 14, 2026, every horror reel)

Chosen by the user after a 4-voice test (YTB/horror/voice_tests/): **number 4, "Unfiltered"** (young adult, Australian, raw).

## Settings (Artlist, Eleven v3)
- Voice: Unfiltered (Artlist library voice id 31). Accent: Australian (its default).
- voice_stability: **0** (most expressive). The old setting (0.3 with Samara X) sounded flat.
- One generation for the whole narration keeps the voice consistent; split only if a line needs a retake.

## Writing the script for her
- First person, present tense where possible ("The doors are opening"), so the fear is happening now.
- Emotion tag before each beat: [whispering], [nervous], [breathing heavily], [panicked], [crying], [shaky voice], [gasps].
- Short broken sentences and repeats under stress: "No, no, no... close. Close!"
- Calm start (whisper), rising to panic at the climax, then a quiet last line before the twist.
- Never use the long dash in the text; use "..." for pauses.

## After generating
- Word timings with faster-whisper (base.en), then fix any missed or misheard words by hand (it dropped the first line on Floor 13 and heard "past" as "passed").
- Loudness: two-pass loudnorm to -14 LUFS in the post script.
