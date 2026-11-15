# Horror narration voice (from Nov 15, 2026, every horror video)

The user tried "Unfiltered" (raw, stability 0) on Keeper Part 1 and found it robotic. Chosen instead: **Samara X**, the soft, slow
woman's voice from the philosophy reels (Lanternfold 07 to 10).

## Settings (Artlist, Eleven v3)
- Voice: Samara X (Artlist library voice id 224933), British.
- voice_stability: **0.5**, and **one generation per line/paragraph** (not one long take). This is what makes her soft and unhurried.
- Tags stay gentle: [whispering], [softly], [nervous], [scared], [thoughtful]. Avoid loud tags ([panicked], [crying]); fear comes from whispering.

## Building the narration
- Lay the lines out with the pauses the scene needs; then build a time map so the animation follows her pacing
  (see YTB/horror/keeper/part1: timemap.json, three/scenes/keeper_p1_map.js). Pin key words (counts, knocks, names) as anchors.
- Word timings with faster-whisper per line; fix misheard words by hand.
- Loudness: two-pass loudnorm to -14 LUFS in the post script.

Earlier test voices: YTB/horror/voice_tests/ (Unfiltered was #4).
