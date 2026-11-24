# Mirror Rules: VoiceStudio log

Made locally with **VoiceStudio** (engine OmniVoice, NVIDIA RTX 5090), local API `127.0.0.1:3900`, `POST /generate`, one generation per line.

- Voice: **clone** of `YTB/horror/pattern/voice/h02.mp3` (converted to 24 kHz mono WAV for the upload), with its exact text as `ref_text`.
- Language `English`, `effect_preset=raw`. Everything else at VoiceStudio defaults (guidance 2.0, speed 1.0, denoise on, duration automatic).
- Output: `<name>.src.wav`, mono, 16-bit, 48 kHz, normal speed (not sped up). Loudness not normalised: mean about -18.7 to -22.4 dB, peaks -2.4 dB or lower.

## Lines

| File | Seed | Length |
|---|---|---|
| m01.src.wav | 7 | 5.40 s |
| m02.src.wav | 7 | 4.98 s |
| m03.src.wav | 7 | 9.68 s |
| m04.src.wav | 7 | 4.62 s |
| m05.src.wav | 7 | 2.62 s |
| m06.src.wav | 7 | 2.74 s |
| m07.src.wav | 7 | 3.56 s |

Redone: none. All seven are the first take at seed 7.

## Check

Every take was read back with VoiceStudio's ASR (`/v1/audio/transcriptions`, language `en`) and compared word for word with the script.
All 7 read back correctly, apart from punctuation and "2"/"3" written as digits for "two"/"three".
Nobody has listened to them by ear yet.
