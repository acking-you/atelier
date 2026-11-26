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

1920x1080, 30 fps, 7766 frames.

## Watch

The renders are archived in Google Drive under `atelier/haoxiang/` (rclone
remote `gdrive:`), outside git. Every link below is public: anyone with it can
watch and download without signing in. Drive shows a "can't scan for viruses"
notice before downloading large files, and limits a file for a while after
heavy traffic.

| Version | Without lyrics | With lyrics |
| --- | --- | --- |
| **4, the delivered film** (chalk, one continuous drawing) | [haoxiang-mv-v4.mp4](https://drive.google.com/file/d/1KiGRqpPndYERahEo076S2xb1uUQV0fIN/view) | [haoxiang-mv-v4-lyrics.mp4](https://drive.google.com/file/d/1x_qGl71DFQeqi1uZL4X_y15K2rs3EAfG/view) |
| 3 (generated pictures) | [haoxiang-mv-v3.mp4](https://drive.google.com/file/d/1-PxAmQcDrkgYclGh4tFL_GiyWEIk2zIK/view) | |
| 1-2 (code-drawn paper-cut figures) | [haoxiang-mv.mp4](https://drive.google.com/file/d/1UW2TSr4pQGr42YEEQmBVzP-MlebOB8M8/view) | [haoxiang-mv-lyrics.mp4](https://drive.google.com/file/d/1A4zTKYJwn6qnUnAPBIUf-x_L5OtSRqDs/view) |
| anime cut (generated video) | [haoxiang-anime.mp4](https://drive.google.com/file/d/1QHuf3Xm1sR5cfw4ISTQS8YajHa3emPI_/view) | |

Drafts (960x540): [version 3](https://drive.google.com/file/d/1wLfQySsLKLO09MDk5doRNLNM689HbtzM/view) ·
[version 1-2](https://drive.google.com/file/d/1nEU4Qa3OFNz_7GN1KorxOgHBmqZVXAw_/view) ·
[anime cut](https://drive.google.com/file/d/14lvUQy8pRwzVTbKuSx40JlRJ6PjDNKKf/view).

## Further reading

- [Storyboard](../../hx/STORYBOARD.md): the film beat by beat, the nine rules of the drawing
- [Chalk kit](../../hx/chalk/README.md) and its part docs in `hx/chalk/doc/`
- [Scene guide](../../hx/scenes/README.md): writing a scene on the scaffold, the joining rule
- `hx/story.py`: the binding numbers (journey, seeds, hand-off states)
