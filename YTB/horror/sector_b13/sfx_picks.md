# Sector B13: Artlist sound picks

Save each one as WAV into `YTB/horror/sector_b13/sfx/`, using the file name in the first column. post.py will look for these names.

| Save as | Use | Artlist clip |
|---|---|---|
| campfire.wav | the fire, from 4 to 15 s | [Extreme Climate - Campfire, Crickets, Night](https://artlist.io/sfx/track/extreme-climate---campfire-crickets-chirping-crackling-fire-night-time/71022) |
| crickets.wav | night bed under everything | [European Forest - Nocturnal Cricket](https://artlist.io/sfx/track/european-forest---nocturnal-cricket-chirping-night/56733) |
| wind.wav | wind in the pines, low | [Cold Ambiences - Wind In Pine Tree, Forest](https://artlist.io/sfx/track/cold-ambiences---weather-wind-in-pine-tree-forest/122160) |
| zip.wav | the tent zip opening by itself | [Zipper, zipping and unzipping a zip, slowly](https://artlist.io/sfx/track/zipper-zipping-and-unzipping-a-zip-slowly/19959) |
| scream_jun.wav | first scream, cut short | [Universal Emotes Female - Woman Frightened, Scream](https://artlist.io/sfx/track/universal-emotes-female---woman-frightened-scream/93441) |
| scream_mika.wav | second scream | [Real Voices - Female Long Screams](https://artlist.io/sfx/track/real-voices---female-long-screams-shouting-in-fear/86847) |
| breath.wav | frame 0 panic breathing | [Female Essentials - Scared Woman, Breathing Heavily](https://artlist.io/sfx/track/female-essentials---scared-woman-breathing-heavily/78840) |
| breath2.wav | spare breathing | [Horror Reactions - Woman Panting](https://artlist.io/sfx/track/horror-reactions---woman-running-panting-breathing-heavily/75057) |
| gate.wav | the gate closing at dawn | [Locked - Closing Metallic Garden Gate](https://artlist.io/sfx/track/locked---closing-metallic-garden-gate/64055) |
| lock.wav | the padlock | [Jail Door - Metal Chain, Rattle](https://artlist.io/sfx/track/jail-door---metal-chain-rattle/98625) |
| torch.wav | torch click (frame 0 and the end) | [Everyday Routine - Flashlight Button Clicking 02](https://artlist.io/sfx/track/everyday-routine---flashlight-button-clicking-02/111010) |
| birds.wav | dawn | [Ambience Central - Forest Birds](https://artlist.io/sfx/track/ambience-central---forest-birds/111313) |
| drone.wav | the File 01 card | [Dystopian Drones - Dark Secrets Atmosphere](https://artlist.io/sfx/track/dystopian-drones---dark-secrets-atmosphere-/81091) |
| steps.wav | footsteps outside the tent | [A Step Ahead - Footsteps on Grass, Leaves, Slow](https://artlist.io/sfx/track/a-step-ahead---footsteps-on-grass-leaves-slow-pace/59860) |
| chain.wav | the creature's collar chain | [Courthouse - Chain Dragged on the Floor](https://artlist.io/sfx/track/courthouse---defendant-chain-dragged-on-the-floor/57667) |

## Volume plan (the voice always leads)
Haru's voice is the loudest thing in the mix. Every sound sits under it, and post.py normalises each clip before setting
its level, so a loud source file can't jump out.

| Layer | Level vs. the voice | Notes |
|---|---|---|
| Voice (Haru, Mika) | 0 dB | the reference |
| Crickets, wind | -26 dB | barely there; felt more than heard |
| Campfire | -22 dB | warm bed in the flashback |
| Dawn birds | -24 dB | |
| Drone under the card | -20 dB | |
| Breathing (frame 0) | -8 dB | close and intimate, never louder than her voice |
| Torch click, zip, footsteps, claws | -12 to -14 dB | clear but small |
| Screams (other tents) | -14 dB, muffled | distant, through nylon, so they startle without blasting |
| Gate clang, padlock | -12 dB | distant at the treeline |

- Ambience ducks a further 4 dB while she speaks.
- The final mix uses the same gentle limiter and two-pass loudnorm as Haru #7. The target is -18 LUFS, with no peaks above -3 dBTP.

Made in code, because nothing on Artlist fit: claws dragging on the tent nylon.
Any clip that's missing falls back to the code version.
