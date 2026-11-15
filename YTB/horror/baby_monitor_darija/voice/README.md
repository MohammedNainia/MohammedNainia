# Baby Monitor (Darija): voice lines

Generated locally with **VoiceStudio 0.5.7** (desktop app, engine k2-fsa/OmniVoice, NVIDIA RTX 5090), using its local
API on `127.0.0.1:3900` (`POST /generate`). One generation per line. Language for every line: **Moroccan Arabic**
(`ary`), Arabic-script text. No effects (`effect_preset=raw`).

Output: one mono 16-bit WAV per line, resampled from the engine's 24 kHz to **48 kHz**.

## Voices

| Voice | Lines | How it was made |
|---|---|---|
| **HARU** (narrator) | n1 to n8 | Voice design `female, young adult, low pitch`, seed 7, for n1. n2 to n8 **clone** that n1 take (ref audio and ref text), so it is the same voice on every line. |
| **MONITOR** | m1, m2, laugh | Voice design `female, elderly, low pitch, whisper`, seed 23, for m2. m1 and laugh clone that m2 take. |

Other settings were VoiceStudio defaults: guidance 2.0, speed 1.0, denoise on, and duration estimated automatically (laugh fixed at 2.0 s).

## Lines

| File | Voice | Seed | Length | Notes |
|---|---|---|---|---|
| n1.wav | HARU | 7 | 4.81 s | |
| n2.wav | HARU | 7 | 6.44 s | |
| m1.wav | MONITOR | 23 | 5.40 s | Lullaby, spoken and hummed (OmniVoice does not truly sing) |
| n3.wav | HARU | 7 | 3.67 s | |
| laugh.wav | MONITOR | 23 | 2.20 s | Text `[laughter]` (OmniVoice nonverbal tag) |
| n4.wav | HARU | 7 | 5.52 s | Redone. Punctuation changed to `سكتات. وضحكات.` (the `...` made the model skip `وضحكات`) |
| n5.wav | HARU | 7 | 6.53 s | |
| n6.wav | HARU | 7 | 3.60 s | |
| n7.wav | HARU | 107 | 2.27 s | Redone (seed 7 slurred `وجلست حدا`) |
| m2.wav | MONITOR | 23 | 3.00 s | |
| n8.wav | HARU | 207 | 2.95 s | Redone (seed 7 slurred the end). Listen to check that `ماكانش` is Darija; the ASR keeps writing it as MSA `لم يكن` |

## Check

Every take was read back with VoiceStudio's own ASR (`/v1/audio/transcriptions`) and compared to the script. Takes that
read back badly were redone. None used the Arabizi text in the end: every Arabizi attempt came out worse than the
Arabic script. Loudness has not been normalised; the post script should bring the mix to -14 LUFS.

Lesson: the `whisper` voice-design tag on the young HARU voice gave unreadable audio (empty ASR on every line), so
HARU uses no whisper tag. For a quieter feel, lower the gain in post.
