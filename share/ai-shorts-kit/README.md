# AI shorts kit

A Claude Code setup for making short videos: slow-burn horror shorts and character skits in a low-poly 3D look, and code-drawn philosophy reels with voice, word-timed captions and sound. Claude Code does the work; you approve each step.

## What's inside

| Path | What it is |
|---|---|
| `.claude/skills/ai-horror-shorts/` | The horror and skit workflow: character sheets, edits, empty set, master shot, shot stills, direction, motion and sound, with the exact prompt templates. |
| `.claude/skills/paper-reel/` | The reel workflow for the code-drawn engine (paper cut-out, watercolor, comic, manga, pixel, low-poly 3D and more). |
| `.claude/skills/cinematic-director/` | Directing skill: beat sheets, shot lists, blocking, sound plans, horror playbook. From [DirectorSKILL](https://github.com/wuwangzhang1216/DirectorSKILL), MIT. |
| `.claude/skills/virality`, `going-viral`, `humanizer`, `caption-and-hashtags`, `comment-mining`, `content-audit` | Hooks, post copy, comment mining and audits. Third-party skills; their license files are inside each folder. |
| `engine_reels/` | The Python video engine: `make.py` runs every step (frames, timing, render, captions, mix, cover, checks). |
| `engine_reels/reels/example_would_you_listen/` | One complete example reel definition (`reel.json`, `scene.py`, `narration.txt`) to copy. |
| `docs/SKITS_METHOD.md` | How the reference low-poly skits are made: AI stills animated in code (summary of @hashhh.co's public guide). |

## Setup

1. Install [Claude Code](https://code.claude.com) and open this folder with it. The skills in `.claude/skills/` load automatically.
2. Python 3.10+ and the engine's packages:
   ```
   pip install numpy pillow faster-whisper imageio-ffmpeg
   ```
   FFmpeg on your PATH works too, or point the `FFMPEG` environment variable at it.
3. For images, voices and music, connect your own accounts in Claude (for example the Artlist connector for Nano Banana Pro images and ElevenLabs voices). Any image tool that accepts reference images works for the horror workflow.
4. Optional: a free [Freesound](https://freesound.org) API key as the `FREESOUND_KEY` environment variable for real sound effects (without it, the built-in sounds are used).

Keys always go in environment variables or the connector settings, never in files in this repo. `.gitignore` already blocks `.env`, token and OAuth files.

## How to start

Ask Claude Code, in plain words:

- "Make a slow-burn horror short: a girl wakes up at 3 am and something is standing in her doorway." It follows `ai-horror-shorts`: character sheets first, then the room, the master shot and the stills, asking you to pick at each step.
- "Make a 45 second reel asking: would you want to know the day you die?" It follows `paper-reel`: concept, style frames for your approval, voice, render, captions, cover, check.
- "Plan the shots for this scene with the horror playbook." It uses `cinematic-director`.

## Rules baked into the skills

- Hook first: the first frame is the strongest one, already moving.
- Comments come from people taking sides, not from yes/no questions.
- Never the long dash character in anything you publish.
- Horror: true silence, single sounds, slow push-ins, the threat appears between cuts.
- Approve before spending credits; one change at a time when editing images.
