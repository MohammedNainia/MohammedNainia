# The Night Count: VoiceStudio log

Made locally with **VoiceStudio 0.5.7** (engine OmniVoice, NVIDIA RTX 5090), local API `127.0.0.1:3900`, `POST /generate`, one generation per line.

- Voice: **clone** of `YTB/horror/pattern/voice/h02.mp3` (Samara X, 8.75 s, converted to 24 kHz mono WAV for the upload), with its exact text as `ref_text`.
- Language `English`, `effect_preset=raw`. Everything else at VoiceStudio defaults (guidance 2.0, speed 1.0, denoise on, duration automatic).
- Output: `<name>.src.wav`, mono, 16-bit, 48 kHz, normal speed (not sped up). Loudness not normalised: mean about -19 to -22.5 dB, peaks below -0.5 dB.

## Lines

| File | Seed | Length | Notes |
|---|---|---|---|
| h01.src.wav | 107 | 7.13 s | Redone. Seed 7 slurred "I told the night" (ASR: "I tutelst, nurse") |
| h02.src.wav | 7 | 9.56 s | |
| h03.src.wav | 107 | 8.46 s | Redone. Seed 7 slurred "the same question" (ASR: "this in question"). ASR writes "two" as "too", same sound |
| h04.src.wav | 7 | 4.66 s | |
| h05.src.wav | 107 | 7.84 s | Redone. Seed 7 added a stray "as in" after "At three" |
| h06.src.wav | 7 | 6.23 s | |
| h08.src.wav | 7 | 2.05 s | |
| h09.src.wav | 7 | 6.89 s | |
| h10.src.wav | 7 | 7.39 s | |
| h11.src.wav | 7 | 4.02 s | |

h07 ("Three.") was not touched; it stays the Artlist recording.

## Check

Every take was read back with VoiceStudio's ASR (`/v1/audio/transcriptions`, language `en`) and compared word for word with the script.
All 10 kept takes read back correctly (apart from punctuation, "4" for "four", and "too" for "two"). For the three redone lines, seeds 107, 207 and 307 were tried; the first good one (107) was kept.
Nobody has listened to them by ear yet.
