# atelier docs

One page per work in `works/`; each work's design docs live beside its code.
Rules for people and agents are in [AGENTS.md](../AGENTS.md).

## Works

| Page | Covers |
| --- | --- |
| [《好想爱这个世界啊》](works/haoxiang.md) | material, versions tried, render commands |

## 《好想爱这个世界啊》 film (`hx/`)

| Page | Covers |
| --- | --- |
| [Design](../hx/DESIGN.md) | story, look, hard rules, how it is built, known soft spots |
| [Storyboard](../hx/STORYBOARD.md) | the film beat by beat with times, the rules of the drawing |
| [Chalk kit](../hx/chalk/README.md) | the drawing kit: frame, camera, strokes, sets, the colour ring |
| [Kit parts](../hx/chalk/doc/) | figure, acting (child, pair), people, gloom, weather, sets, things, land, day |
| [Scene guide](../hx/scenes/README.md) | scene modules, the joining rule, checks |
| [Version 3 notes](../hx/_attic/v3_pictures/README.md) · [Version 1-2 kit](../hx/_attic/kit_procedural/README.md) | archived earlier versions |

## Shared code (`mv/`)

| Module | Covers |
| --- | --- |
| `mv/engine/palette.py` | sRGB colours, OKLab mixes, `sk()` for skia |
| `mv/engine/prims.py` | hashing, noise, paints, cached sprites, text with asserted glyph coverage |
| `mv/encode.py` | x264 settings, GOP-aligned chunk planning, container checks |
