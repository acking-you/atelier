# 《好想爱这个世界啊》 music film

The song by 华晨宇 (studio recording, 4:18.87, 80 BPM, 4/4, bar 3.0 s), told
from the point of view of a child living with depression, from the gloom
toward light in steps. This page is the work's record: what exists, what was
tried, how to render it. The film's own rules are in [hx/DESIGN.md](../../hx/DESIGN.md).

## Material

| File | What |
| --- | --- |
| `reference/haoxiangaizhegeshijie/haoxiangaizhegeshijie.mp3` | the soundtrack, muxed untouched (48 kHz, 320 kbps) |
| `reference/haoxiangaizhegeshijie/haoxiangaizhegeshijie.lrc` | time-stamped lyrics of the same recording (66 lines, 50 sung) |
| `reference/haoxiangaizhegeshijie/meta.json` | source metadata (`netease-1407358755`) |
| `hx/data/timeline.json` | the measured clock: sections, cues, beats, bars, onsets, curves (`python -m hx.analyze` rebuilds it) |

## Versions

| Version | Where | Look | Outcome |
| --- | --- | --- | --- |
| 1-2 | `hx/_attic/kit_procedural`, `scenes_procedural` | code-drawn, semi-realistic paper-cut figures | rejected: looked wrong and dull |
| anime cut | `gx/` | 53 generated video shots cut to the clock (`gx/plan.py`, `gx/assemble.py`); clips not kept | rejected: no coherence or logic between shots |
| 3 | `hx/art/`, `hx/_attic/v3_pictures` | generated painted pictures composited with code-drawn weather | rejected: no continuity of animation |
| **4** | `hx/` | chalk and crayon on dark paper, stick figures on a pose rig, one continuous drawing | **delivered 2026-11-17** |

Version 4's soft spots are listed at the end of [hx/DESIGN.md](../../hx/DESIGN.md).

## Render

```bash
.venv/bin/python -m hx.render --out output/haoxiang-mv.mp4 --audio
.venv/bin/python -m hx.render --out output/haoxiang-mv-lyrics.mp4 --audio --lyrics reference/haoxiangaizhegeshijie/haoxiangaizhegeshijie.lrc
```

1920x1080, 30 fps, 7766 frames. The renders delivered so far live outside
git on the owner's machine (`play-forme/output/haoxiang-*.mp4`).

## Further reading

- [Storyboard](../../hx/STORYBOARD.md): the film beat by beat, the nine rules of the drawing
- [Chalk kit](../../hx/chalk/README.md) and its part docs in `hx/chalk/doc/`
- [Scene guide](../../hx/scenes/README.md): writing a scene on the scaffold, the joining rule
- `hx/story.py`: the binding numbers (journey, seeds, hand-off states)
