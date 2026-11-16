# Baby Monitor Part 3 (Darija): voice lines

Generated locally with **VoiceStudio 0.5.7** (engine k2-fsa/OmniVoice, NVIDIA RTX 5090), using its local API on
`127.0.0.1:3900` (`POST /generate`), with the same method as `../../baby_monitor2_darija/voice/README.md`. Language
for every line: **Moroccan Arabic** (`ary`), Arabic-script text, no effects (`effect_preset=raw`). Full stops were
used between phrases, never `...`. One generation per line.

Output: one mono 16-bit WAV per line, resampled from the engine's 24 kHz to **48 kHz**.

## Voices (all clones, so every voice matches the earlier parts)

| Voice | Lines | Cloned from (ref audio and ref text) |
|---|---|---|
| **HARU** | n1 to n10, song | `baby_monitor_darija/voice/n1.wav` (Part 1) |
| **MUM** | m1, m2, m3 | `baby_monitor2_darija/voice/m1.wav` (Part 2) |
| **NORA** (the monitor voice) | v1 | `baby_monitor_darija/voice/m2.wav` (Part 1, the old whispering woman) |

Base seeds: HARU 7, MUM 11, NORA 23. A redo uses the base seed plus 100 per try. Other settings were VoiceStudio
defaults: guidance 2.0, speed 1.0, denoise on, and duration estimated automatically.

## Lines

| File | Voice | Seed | Length | ASR score | Notes |
|---|---|---|---|---|---|
| n1.wav | HARU | 7 | 4.75 s | 0.93 | |
| n2.wav | HARU | 7 | 4.16 s | 0.96 | |
| n3.wav | HARU | 7 | 4.05 s | 0.95 | |
| m1.wav | MUM | 11 | 5.25 s | 0.95 | |
| m2.wav | MUM | 11 | 6.87 s | 0.95 | |
| n4.wav | HARU | 7 | 1.06 s | 1.00 | |
| m3.wav | MUM | 11 | 6.52 s | 0.98 | A clone cannot be told to be "very quiet", so lower its gain in the mix. |
| n5.wav | HARU | 7 | 4.56 s | 0.92 | |
| n6.wav | HARU | 7 | 3.88 s | 0.95 | |
| n7.wav | HARU | 307 | 3.54 s | 0.99 | **Redone.** In the seed 7 take, the ASR heard `الريدو` in place of `اليد`. Seed 307 reads `اليد` clearly. |
| n8.wav | HARU | 7 | 4.28 s | 0.92 | |
| v1.wav | NORA | 323 | 1.33 s | 0.89 | **Redone** (4 tries). Seed 123 was unreadable and seeds 23 and 223 lost the `دابا`. It is a quiet whisper (mean -33 dB), so raise it in the mix. |
| n9.wav | HARU | 107 | 6.80 s | 0.94 | **Redone.** The seed 7 take skipped the start (`جابو بنت جديدة`). |
| n10.wav | HARU | 7 | 2.90 s | 0.97 | |
| song.wav | HARU | 7 | 3.65 s | 0.91 | Lullaby, spoken softly (OmniVoice does not truly sing). |

## Check

Every take was read back with VoiceStudio's own ASR (`/v1/audio/transcriptions`) and compared to the script (similarity
on normalised Arabic letters). A take was kept at a score of 0.85 or more, otherwise it was redone with a new seed.
Loudness has not been normalised; the post script should bring the mix to -14 LUFS.
