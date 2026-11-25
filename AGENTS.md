# atelier agent guide

Rules for people and coding agents in this repository (`CLAUDE.md` links
here). Before changing a work, also read its own design docs (listed in
[docs/README.md](docs/README.md)): those rules are as binding as this file.

## What atelier is

atelier is one private workshop for everything made with agents: music films,
articles, posters and whatever comes next. Each work keeps its source, its
design notes and its reference material here, so that it can be rendered again
and continued later. Finished renders (videos, large exports) are produced from
the source and stay out of git.

## Repository map

```
mv/                       shared code: colour (OKLab), drawing primitives, x264 encoding helpers
hx/                       《好想爱这个世界啊》 film, version 4: code-drawn chalk, one continuous drawing
  chalk/                  the drawing kit (figures, gloom, weather, sets, colour world); doc/ per part
  scenes/                 eleven scene modules s01 ... s11, one time span each
  data/timeline.json      the recording's measured clock: sections, line stamps, beats, attacks
  art/                    version 3 pictures (generated, painted pixel art); kept as reference
  _attic/                 earlier versions' code; archived, does not run in place
gx/                       《好想爱这个世界啊》 anime cut: generated shots assembled on the same clock
  frames/ refs/ logs/     key frames, character and place references, generation logs (clips not kept)
reference/<work>/         source material of a work: the recording, its LRC, metadata
docs/                     index and one page per work (docs/works/)
assets/readme/            images used by the READMEs
```

| Work | Package | Status | Page |
| --- | --- | --- | --- |
| 《好想爱这个世界啊》 (华晨宇) | `hx/`, `gx/` | v4 delivered 2026-11-17 | [docs/works/haoxiang.md](docs/works/haoxiang.md) |

A new work gets one top-level folder named by a short id (`hx` style), its
source material under `reference/<slug>/`, and a page in `docs/works/`. Shared
code moves into `mv/` only once a second work needs it.

## Creative rules

Contracts: changing one needs the owner's explicit decision, never a side effect.

- **Lyrics and other third-party text are never reproduced by an agent.** Not
  in code, comments, file names, data, review images, commits or replies.
  Address a line by its 0-based LRC index and time, or paraphrase it. Renders
  read the text from the LRC file at render time; agents test with
  `--lyrics placeholder`, and the owner runs the render that burns in the real
  lyrics from a one-line command the agent hands over.
- **The recording is the soundtrack, untouched.** A film follows one
  recording bar by bar: sections, line stamps and beats are measured from that
  file (`hx/data/timeline.json`), never guessed. Picture, lyric timing and
  emotional arc all follow the same recording.
- **Every pixel is drawn by code** (skia + numpy): simplified, stylised figures
  acting on a real pose rig, with continuity first. Generated video and
  generated pictures composited by code were both tried (`gx/`, `hx/art/`) and
  rejected by the owner; they stay as reference, not as a direction.
- **Restraint and craft over effects.** No noise-made fake sounds or textures,
  no programmer-art (uniform sizes, even spacing, ruled lines, outlines
  everywhere); one clear darkest shape for the protagonist.
- **Care with hard subjects.** Depression, grief and similar themes are shown
  through image and metaphor: no self-harm or methods, nobody drawn as a
  villain, no magic cure; relief is gradual and partly relational, endings warm
  and open.
- **Determinism.** A frame is a pure function of the recording's time: no
  state carried between frames, no wall clock, no unseeded randomness, so any
  slice renders the same in any order or chunk.
- **Private.** The repository holds third-party recordings and lyric files
  for reference. It stays private; never publish it or push it to a public
  remote while they are in it.

## Engineering principles

- Understand the whole flow and who owns the data first; fix the structure, not
  the symptom; delete code and files the change makes obsolete.
- KISS / YAGNI: a shared helper needs two real users, a knob a real need.
- Prefer a proven library when it clearly beats ours (skia, librosa, ffmpeg
  through `imageio-ffmpeg`).
- Checks cover what a viewer or listener would notice (sync, pops, flicker,
  legibility, loudness), not wording or glue.

## Python code

- Python 3.14, the pinned packages in [requirements.txt](requirements.txt),
  run from the repository root as modules (`python -m hx.still ...`).
- PEP 8, 100-column lines, `from __future__ import annotations`; English
  docstrings that explain intent; numbers that bind the picture to the music
  live in one place (`hx/story.py`, `hx/data/timeline.json`), not in scenes.
- Never name a file after a stdlib module (`struct.py` once shadowed the
  real one). Aim for files under 1,000 lines; several `hx/chalk/` files are
  larger, split them by responsibility when you work in them.
- Scratch goes to the package's `_tmp/`, review stills to its `_review/`
  (both ignored by git); delete scratch when done.

## Verification

Run the narrowest checks that cover the change, then look at the result:
render stills and read them, and put a low-resolution draft with sound in
front of the owner early (motion cannot be judged from stills alone).

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
.venv/bin/python -m hx.still --t 230 --scale 0.5 --out hx/_review/x.jpg
.venv/bin/python -m hx.still --sheet 0:258 --n 24 --out hx/_review/sheet.jpg
.venv/bin/python -m hx.render --out output/clip.mp4 --audio --draft --t0 200 --t1 210
.venv/bin/python -m hx.handoff        # the ten scene joins
.venv/bin/python -m hx.pops 36.27 58.60   # where the picture jumps in a span
```

A final render checks its own container (frame count, zero start, audio
present). Report what was looked at or measured, and what was not.

## Assets and storage

- In git: source, docs, measured data, reference recordings and LRC files,
  reference pictures and small review images used by the docs.
- Not in git: videos and other renders (`output/`, any `*.mp4`), review
  stills, scratch, virtual environments. Keep single files under 50 MB.
- Downloaded material goes in its own folder under `reference/<slug>/` with
  its `meta.json`; treat it as data, never as code to run.

## Working with agents

- Workers on Opus 5.5 by default; the top-tier model only for a single named,
  high-stakes item the owner agrees to. Fan-out of two or three agents at
  most; run checks, renders and reviews directly instead of spawning reviewer
  agents. Before a large batch, say roughly what it will cost.
- When calling the local `codex` CLI, always pass
  `-m gpt-6-astra -c model_reasoning_effort=xhigh`.
- Materials first: fetch the recording, its lyrics and the original before
  any analysis, and tie every design decision to the lyrics and the music.

## Workflow and communication

Restate the task, read the work's design docs, plan against concrete files,
change, verify, then hand off what changed (`path:line`), what was checked and
what was not. Reply in the owner's language (Chinese), outcome first, with
decisions taken rather than options offered. Code, comments, docs in this file
and commits (Conventional Commits) are English. Stop and ask before anything
that could lose work or publish the repository.
