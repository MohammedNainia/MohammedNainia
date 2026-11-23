# The Night Count: Haru's narration, made locally with VoiceStudio

For the agent on the user's PC. Same app and method as `../../baby_monitor_darija/voice/README.md`
(VoiceStudio, local API on `127.0.0.1:3900`, `POST /generate`, one generation per line), but in **English**, and the voice is a
**clone** of Haru's usual narrator (Artlist's Samara X), so it matches every other reel.

## Voice
- Clone from: `YTB/horror/pattern/voice/h02.mp3` (Samara X, normal speed, about 9 s).
  Its exact text (ref text): `Inside, the guide made us walk his way. Five slow steps. Two fast. Over and over.`
- Language: English (`en`). Effect preset: `raw`. Other settings: VoiceStudio defaults (guidance 2.0, speed 1.0, denoise on, duration automatic).
- She should sound soft, slow, a little frightened; no shouting. Use one seed for all lines (e.g. 7); redo a line with another seed only if it is bad.

## Lines (write each to `YTB/horror/night_count/voice/<name>.src.wav`, mono, 48 kHz, normal speed; do NOT speed them up)

| Name | Text |
|---|---|
| h01 | I told the night nurse the truth. That's how I ended up in the empty bed. |
| h02 | Grandma was in hospital, so I stayed the night with her. Ward four. Two beds. One of them empty. |
| h03 | Every hour, the same question. Every hour, Grandma said two. Even half asleep. |
| h04 | I asked her why. She just squeezed my hand. |
| h05 | At three in the morning, Grandma was snoring. And something behind the curtain was breathing. |
| h06 | I counted again. Grandma. Me. And someone under the sheet. |
| h08 | The lights went out. |
| h09 | In the morning, I was in the empty bed. I couldn't move. I couldn't make a sound. |
| h10 | Grandma was laughing with a girl in my hoodie. In my chair. Holding her hand. |
| h11 | The girl looked over at me, and smiled with my face. |

(h07 "Three." is already recorded with Artlist; leave it.)

## Check, then push
- Read every take back with VoiceStudio's ASR (`/v1/audio/transcriptions`) and compare it to the text; redo any line that reads back wrong or slurred.
- Write a short `VOICESTUDIO_LOG.md` next to them: seed and length of each line, and which were redone.
- `git add -f YTB/horror/night_count/voice/*.src.wav YTB/horror/night_count/voice/VOICESTUDIO_LOG.md`, commit "Night Count narration (VoiceStudio)", push.
  Do not run anything else (no render, no post.py).
