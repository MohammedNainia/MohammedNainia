# Mirror Rules: Haru's narration, made locally with VoiceStudio

For the agent on the user's PC. Same app and method as `../../night_count/voice/VOICESTUDIO.md`
(VoiceStudio, local API on `127.0.0.1:3900`, `POST /generate`, one generation per line), English, a clone of Haru's usual narrator.

## Voice
- Clone from: `YTB/horror/pattern/voice/h02.mp3` (Samara X, normal speed, about 9 s).
  Its exact text (ref text): `Inside, the guide made us walk his way. Five slow steps. Two fast. Over and over.`
- Language: English (`en`). Effect preset: `raw`. Other settings: VoiceStudio defaults (guidance 2.0, speed 1.0, denoise on, duration automatic).
- She is speaking straight to the viewer, quietly, like a warning between friends: calm and serious, a little scared, never shouting.
  The "..." are real pauses. Use one seed for all lines (e.g. 7); redo a line with another seed only if it is bad.

## Lines (write each to `YTB/horror/mirror_rules/voice/<name>.src.wav`, mono, 48 kHz, normal speed; do NOT speed them up)

| Name | Text |
|---|---|
| m01 | If your reflection blinks before you do... don't look away first. |
| m02 | Rule two. Don't smile at it. It's learning how. |
| m03 | Rule three. If it starts brushing its teeth before you've picked up the brush... turn off the light. Slowly. |
| m04 | In the dark, it can't see you. That's the rule. |
| m05 | I turned the light back on. |
| m06 | It's not in the mirror anymore. |
| m07 | So whatever you do... don't blink. |

## Check, then push
- Read every take back with VoiceStudio's ASR (`/v1/audio/transcriptions`) and compare it to the text; redo any line that reads back wrong or slurred.
- Write a short `VOICESTUDIO_LOG.md` next to them: seed and length of each line, and which were redone.
- `git add -f YTB/horror/mirror_rules/voice/*.src.wav YTB/horror/mirror_rules/voice/VOICESTUDIO_LOG.md`, commit "Mirror Rules narration (VoiceStudio)", push.
  Do not run anything else (no render, no post.py).
