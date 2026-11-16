# Baby Monitor Part 2 (Darija): voice lines

Generated locally with **VoiceStudio 0.5.7** (engine k2-fsa/OmniVoice, NVIDIA RTX 5090), using its local API on
`127.0.0.1:3900` (`POST /generate`), with the same method as `../../baby_monitor_darija/voice/README.md`. Language
for every line: **Moroccan Arabic** (`ary`), Arabic-script text, no effects (`effect_preset=raw`). Full stops were
used between phrases, never `...`.

Output: one mono 16-bit WAV per line, resampled from the engine's 24 kHz to **48 kHz**.

## Voices

| Voice | Lines | How it was made |
|---|---|---|
| **HARU** | n1 to n7 | **Clone** of Part 1 `baby_monitor_darija/voice/n1.wav` (ref audio and ref text). Same voice as Part 1. |
| **MONITOR** | m3 | **Clone** of Part 1 `baby_monitor_darija/voice/m2.wav`. Same old woman as Part 1. |
| **MUM** (new) | m1, m2 | Voice design `female, middle-aged, moderate pitch`, seed 211, for m1. m2 clones that m1 take. The brief asked for "adult, middle pitch", but OmniVoice only accepts the ages child/teenager/young adult/middle-aged/elderly and the pitches very low to very high, so `middle-aged` and `moderate pitch` are the closest valid tags. |

Other settings were VoiceStudio defaults: guidance 2.0, speed 1.0, denoise on, and duration estimated automatically.

## Lines

| File | Voice | Seed | Length | Notes |
|---|---|---|---|---|
| n1.wav | HARU | 7 | 5.82 s | |
| n2.wav | HARU | 7 | 3.51 s | |
| m1.wav | MUM | 211 | 3.96 s | **Redone.** The seed 11 take dropped the negation `ما عندناش` (ASR heard "نحن لدينا"). Seed 211 keeps it. |
| n3.wav | HARU | 7 | 3.22 s | |
| n4.wav | HARU | 7 | 2.16 s | |
| m2.wav | MUM | 11 | 5.09 s | **Redone**, after m1 changed, so that it clones the new m1 take. |
| n5.wav | HARU | 7 | 4.02 s | |
| n6.wav | HARU | 7 | 4.47 s | |
| m3.wav | MONITOR | 923 | 1.88 s | **Redone** (9 tries). The short whisper often came out unreadable (ASR heard noise or "انتهيتي"). Seed 923 reads "ها أنت جيتي". It is quiet (mean -29 dB), so raise it in the mix if needed. |
| n7.wav | HARU | 7 | 4.47 s | ASR writes `ما بقاتش` / `ولات` as MSA `لا تبقى`. That is a known bias of the ASR, but give it a listen. |

## Check

Every take was read back with VoiceStudio's own ASR (`/v1/audio/transcriptions`) and compared to the script (similarity
on normalised Arabic letters). Final scores were 0.89 to 0.99. Loudness has not been normalised; the post script
should bring the mix to -14 LUFS.
