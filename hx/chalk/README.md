# hx.chalk: the kit of film version 4, "the child's own drawing"

Chalk and crayon on dark paper, drawn by code (skia + numpy). This file is all a scene author needs.
Everything is importable from the package: `from hx.chalk import *`.

    PYTHONPATH=. .venv/bin/python -m hx.still --t 14.0 --scale 1.0 --out hx/_review/x.png     # one frame
    PYTHONPATH=. .venv/bin/python -m hx.still --sheet 0:36 --n 16 --out hx/_review/x.jpg      # contact sheet
    PYTHONPATH=. .venv/bin/python -m hx.render --out output/x.mp4 --t0 13 --t1 23 [--lyrics placeholder] [--audio]
    PYTHONPATH=. .venv/bin/python -m hx.motion output/x.mp4        # flicker numbers of a clip (or: hx.motion 13 23)
    PYTHONPATH=. .venv/bin/python -m hx.scenes                     # who draws what: taken spans and free gaps

Files: `core.py` (palette, paper, tooth, Frame, camera, strokes), `sketch.py` (named stroke sets:
draw on, un-draw, morph), `figure.py` (pose rig, the two characters), `gloom.py` (the scribble),
`weather.py` (rain, light), `props.py` (set pieces), `day.py` (colour world, the ring), `title.py`,
`demo.py` (four example scenes and the proof images; read it as worked examples).

## 1. A scene

A scene is a module in `hx/scenes/` with a time span on the song's clock and a draw function:

```python
# hx/scenes/v1a.py
import math                                # the star import brings the kit only: numpy and math are yours to import
import numpy as np
from hx.chalk import *

SPAN = (12.27, 24.27)                      # t0 <= t < t1, seconds of the recording (or SPANS = ((a, b), ...))

def draw(F):                               # F: the Frame of this picture, night paper already on it
    F.cam = Cam.ease(Cam(), Cam.at(946, 610, 1.4), F.seg(20.0, 24.0))     # camera first
    ground_line(F)
    sofa().draw(F)                         # the set piece alone; a whole room: doc/sets.md
    figure(F, 815, 618, 380, STOPPED, "child", seed=3)
    gloom(F, 730, 308, 440, 156, seed=4, loops=46)
```

The registry picks the module whose span holds the time. Spans of two real modules may not overlap
(error at load; nor may two `demo_*` modules). Modules named `demo_*` are stand-ins that a real scene
silently wins over: delete them when their time is covered. `python -m hx.scenes` lists the spans
that are taken and the gaps. A time nobody draws gets a placeholder (ground line, child
standing). A module whose name starts with `_` is a helper and is not registered. With `HX_STRICT=1`
(set by `hx.render`) an import error is fatal; otherwise the module is skipped with a message.

The Renderer (`hx/frame.py`) does, per frame: Frame on night paper, `draw(F)`, finish (bloom,
vignette, fade, grain), sharp overlays (`F.overlay`), resize, lyric line, debug strip.

The star import brings many short names: `A C H W CX CY FPS` (frame constants and the palette),
`line fill hand ring sky sun seg ramp mix fit under loop trim title day props sketch`. A module-level
name of your own shadows them in your module only, which is harmless until you need the kit's one.

A whole small scene, start to finish (`hx/scenes/demo_verify.py` is this scene with a far layer
and a camera that pushes in and pulls back):

```python
GY = 760.0
def shelter():                              # a set of your own: six named strokes
    col = C.CHALK_COOL
    return Sketch([Stroke(A((1010, GY), (1012, 392)), col, 4.6, 0.95, seed=31, name="post_l"),
                   line(1500, GY, 1497, 400, col, 4.6, 0.95, 32, "post_r"),      # the same, shorter
                   Stroke(A((950, 404), (1255, 330), (1560, 410)), col, 5.2, 0.95, seed=33, name="roof"),
                   line(1090, 640, 1420, 638, col, 4.6, 0.95, 34, "bench"),
                   line(1120, 640, 1118, GY, C.CHALK_DIM, 3.8, 0.9, 35, "leg_l"),
                   line(1392, 639, 1394, GY, C.CHALK_DIM, 3.8, 0.9, 36, "leg_r")], name="shelter")

def draw(F):
    chalk(F, A((-1400, GY), (3300, GY)), C.CHALK_COOL, 4.2, 0.9, seed=20, taper=1.0)   # ground: longer than any framing
    S = shelter()
    S.on_beats(F.tl, 100.0)                 # a stroke a beat from the first beat at or after 100.0 s
    S.off_beats(F.tl, 123.0)                # taken away again, a stroke a beat, each leaving its ghost
    S.draw(F)
    figure(F, 1255, GY, 290, STAND, "friend", -1, seed=5)
    W = walk_to(F.t, 250, 840, 300, start=100.0)             # the child walks in and stops, feet planted
    ground_shadow(F, W.x + 10, GY + 4, 110, 0.7)
    J = figure(F, W.x, GY, 300, W.pose, "child", W.face, seed=3)
    gloom(F, J["head"][0] - 40, J["head"][1] - 205, 300, 100, seed=4, loops=30)      # the weight follows the head
    with F.screen():
        rain(F, 0, 0, 1920, 1080, n=160, a=0.4, seed=7)
```

Proofs of a kit piece without a scene module (`hx/chalk/proof.py`): `still(draw, t, path, skin="night",
crop=None)`, `sheet(draw, times | n, path, cols=4, tile=(640, 360), t0=, t1=)`, `clip(draw, t0, t1, path)`,
`flicker(draw, t0, t1)`, where `draw(F)` is any draw function.

## 2. Conventions

- **Units.** World units are the screen pixels of the 1920x1080 frame at the identity camera `Cam()`
  (centre 960, 540, zoom 1). x right, y DOWN. Angles in radians. Colours are (r, g, b) in 0..1.
  Alphas ("pressure") 0..1. Times in seconds of the recording.
- **Every drawing function takes WORLD coordinates and world sizes** and maps them through `F.cam`
  itself. Never scale or translate the canvas: the tooth, the grain and the paper are screen-fixed.
- **Line widths** scale with zoom, with a floor in screen px (1.6 for main lines). Under the floor the
  line keeps the floor width and loses pressure: far things get fainter, never fatter.
- **Time.** Three clocks. `F.t` is the true time: cameras, poses, draw-on, everything that ACTS and
  everything timed against the song. `F.tb` is the boil clock, stepped on twos: rain, the scribble's
  churn, sways, drifting dust, anything that is merely ALIVE (the kit's `t=None` defaults use it).
  It stands still in the two true silences of the recording (`HOLDS`: 56.00-58.60 and 193.00-201.27),
  so there the line does not boil, the rain hangs in the air and the picture is completely still
  except for what acts; afterwards it runs behind the true time, so never compare it with a time of
  the song. `F.k` is the boil index (`floor(F.tb * 15)`): both frames of a pair share it. `F.tq` is
  the true time stepped on twos (for a song-timed thing that should hold inside a pair).
- **Deterministic.** A frame is a pure function of time. Randomness only from the hashes (`rnd`,
  `rsym`, `vn`, `htab`) with a `seed`. Give every stroke its own seed: the seed IS the line's hand
  (its wobble, its pressure). No state between frames. Do not keep a paint returned by `F.paint`.
- **Skins.** `F.skin` is `"night"` or `"day"`. `figure`, `crow`, `hill`, `tree`, `gloom`,
  `ground_shadow`, `on_string` follow it; for your own colours use `F.pick(night, day)`.
  Before 217.84 s only cold chalks plus the amber family (the friend's); crayon colours only after.
- **Names.** Sketch items are named `prop.part` (`"sofa.back"`, `"sofa.back.fill"`); a prefix names
  the group (`"sofa"`). Morph pairs and timing helpers work on these names.
- **Lyrics are never written anywhere** (code, comments, file names, images). Address a line by its
  0-based LRC index: `F.since(19)`, `F.line_ramp(19)`, `F.tl.cue(19).t`. No letters or numerals in
  the picture (the title overlay, `title.draw`, is the one exception). The lower 20 percent of the
  frame (y > 864) is where the lyric line sits (baseline 959).

### The ground line

`ground_line(F, curve=None, a=0.9, w=4.2, col=None, span=None)` (`hx/chalk/ground.py`) is the one ground
line of the film: skirting board, classroom floor, kerb, horizon, foot of the hills. It is always the
same stroke (fixed ends at world x -3000 and 15000, seed 20), so it never jumps when the set changes.
Every scene draws it; no set draws a floor line of its own. `curve`: a function of an array of world
x giving world y (a hill contour that is 742 where the land is flat). `span=(xa, xb)`: only that part
exists (to draw it on or rub it out). Shared numbers (heights, seeds, room anchors): `hx/story.py`.

## 3. The Frame

| | |
|---|---|
| `F.c`, `F.surf` | skia canvas and surface (1920x1080). Raw canvas calls are in SCREEN px: map with `F.cam` / `F.path` |
| `F.t`, `F.tb`, `F.k`, `F.tq` | true time; boil clock (held in the silences, on twos); boil index; true time on twos |
| `F.cam` | the camera every function maps through; assign a `Cam` at the top of draw |
| `F.skin`, `F.day`, `F.pick(night, day)` | the skin |
| `F.tl` | the Timeline (`hx/timeline.py`): `sections`, `cue(lrc)`, `beat_time(k)`, `beats_between(a, b)`, `bars_between`, `onsets_between(a, b, min_strength)`, `curve(name, t)` |
| `F.sec`, `F.u` | current Section (`id`, `t0`, `t1`, `kind`) and position 0..1 through it |
| `F.beat`, `F.beat_frac`, `F.bar`, `F.bar_beat`, `F.bar_frac` | grid position (beat k is at 0.265 + 0.75 k s; a bar is 3.0 s) |
| `F.loud`, `F.fast`, `F.hit`, `F.kick`, `F.curve("bright")` | measured curves of the recording at F.t, 0..1 |
| `F.cue`, `F.lrc` | the line being sung (or None), its LRC index |
| `F.since(lrc)` | seconds since that line began (negative before) |
| `F.seg(t0, t1)`, `F.ramp(t0, t1)` | linear / smooth 0..1 between two times |
| `F.line_ramp(lrc, lead=0, dur=1)` | smooth 0..1 from `lead` s before a line, over `dur` s |
| `F.pulse(tau=0.22, every=1)`, `F.bar_pulse(tau=0.5)` | 1 on the beat / bar, decaying with time constant tau |
| `F.post` | the finish: `bloom` (0.42 night, 0 day), `vignette` (0.12 / 0.08), `fade` 0..1 toward `fade_col` (exposure, fade to a colour), `grain` (1.0, seated), `shimmer` (0: grain that moves on twos; keep under 0.25) |
| `F.overlay(fn)` | `fn(canvas)` on the finished frame, screen px (sharp things; use sparingly) |
| `F.set_skin("day")` | start the picture over on that paper |
| `F.sub(skin=None)` | an offscreen Frame (same time, camera, timeline) on its own paper; `G.image()` is its picture |
| `F.lw(w, a, floor=1.6)` | world width -> (screen width, alpha) with the floor rule |
| `F.path(P, close=False)` | skia path through world points |
| `F.paint(col, a, grain, blend)`, `F.pen(col, w_px, a, grain)` | shared fill / stroke paints through a grain |

Camera contexts (they swap `F.cam` for the block):

```python
with F.depth(0.4):                 # a far layer: pan scaled by 0.4, zoom ** 0.4 (0 = fixed to the screen, > 1 = foreground)
    hill(F, FAR_CURVE)
with F.screen():                   # screen pixels: rain in front, light leaks, frame-wide washes
    rain(F, 0, 0, 1920, 1080, n=200)
with F.place(400, 0, 0.5):         # anything inside sits at local * 0.5 + (400, 0) in the world, half size
    tree(F, 250, 700)
with F.clip(rect=(1300, 170, 1670, 560)):     # or F.clip(poly), out=True for the outside
    rain(F, 1300, 170, 1670, 560)
```

Coordinates returned inside `F.place` (figure joints) are local to it.

### Cam

`Cam(cx=960, cy=540, zoom=1)`: world point -> screen `((wx - cx) * zoom + 960, (wy - cy) * zoom + 540)`.

- `Cam.at(x, y, zoom, sx=960, sy=540)`: the camera that shows world (x, y) at screen (sx, sy).
- `cam.to_screen(x, y)`, `cam.to_world(sx, sy)`, `cam.s(size)`, `cam.pts(P)` (arrays), `cam.view(margin=0)` (world rect on screen), `cam.depth(d)`.
- `Cam.lerp(a, b, w)`: zoom interpolated geometrically, the common fixed point held (a clean dolly;
  a pan when the zooms are equal). `Cam.ease(a, b, w)`: the same with a soft start and stop.

```python
close = Cam.at(child_x, feet_y, 1.0, 900, 790)          # child at screen (900, 790), 300 px tall
wide = Cam(3692, 2077, 0.26)
F.cam = Cam.ease(close, wide, F.seg(60.27, 62.27))      # the pull-back, one continuous move
```

## 4. Strokes and tones (core)

Grains (how hard the chalk is pressed through the tooth): `"dense"`, `"mid"`, `"sparse"`, `"dust"`
(lines and zigzags), `"soft"`, `"glow"` (rubbed tone and light), `None` (flat: rub-outs, features).
Rubbed tone shows the hand that rubbed it, fixed to the screen: a round patch (a glow, a halo, a
sky) is dabbed into soft blotches; a wide flat one (mist, a contact shadow: rx over about 2.3 ry)
and every `wash` is wiped sideways into smears. `smudge` and `wash` choose by themselves.

- `chalk(F, P, col, w, a=1, seed=0, wob=1, taper=0.5, draw=1, grain="dense", edge=0.34, under=None, step=6, var=0.2, boil=1, floor=1.6, lead=0, baked=False)`
  A hand-drawn stroke along world polyline P (N, 2), w wide. `wob` hand wobble (1 = about 1.7 world
  units; 0 = none), `taper` width at the ends (0..1), `draw` fraction or `(f0, f1)` of it that exists,
  `edge` alpha of the dusty pass (0 = clean crayon), `under` colour rubbed out behind it, `step` sample
  spacing in screen px, `var` pressure noise, `boil` 0 = seated, `floor` least screen width, `lead`
  world length behind the tip where pressure still builds. Returns the world point of the tip.
- `scrib(F, P, col, w, a=1, grain="mid", close=False, floor=1.2)`: constant width, no wobble, one path (dense scribbles).
- `loop(F, P, col, w, a, seed, wob, fill_col=None, fill_a=0.9, fill_grain=None, **chalk_kw)`: closed outline that overshoots its start; optional fill first.
- `fill(F, P, col, a=1, grain=None, blend=None)`: polygon (closed world outline). `disc(F, x, y, r, col, a=1, grain=None, floor=0)`: a dot.
- `hatch(F, poly, col, ang, gap, w, a=1, seed=0, grain="sparse", wob=0.6, draw=1, clip=False, over=0.5, boil=None, jit=0.35)`
  Colours a shape in with a zigzag: scan lines at `ang`, `gap` apart, lines `w` wide; `over` how far
  it runs over (or stops short of) the outline, `jit` unevenness of the rows, `clip` keeps it inside.
  `boil=None`: boils only if the shape's box on screen is under 200 000 px2; pass `False` to seat it.
  When the gap falls under 3 screen px (far away) it turns into rubbed tone of the same weight.
- `smudge(F, cx, cy, rx, ry, col, a=0.5, grain="soft", power=1.6, rot=0, additive=False, inner=0)`:
  rubbed pastel, a soft ellipse. `power` falloff, `inner` solid core 0..1, `additive=True` for light.
- `wash(F, poly, col, y0, y1, alphas, grain="soft", additive=False)`: polygon whose strength runs through the list `alphas` from world y0 to y1 (beams, pools of light).
- `specks(F, xs, ys, r, col, a=1, grain="dense")`: many dots. `dashes(F, x0, y0, x1, y1, w, col, a=1, grain="mid", floor=1.3)`: many short lines (arrays).

```python
P = blob(600, 400, 120, 80, seed=7)                       # a hand-drawn round outline
fill(F, P, C.KNOCK, 0.94)                                 # rub out what is behind
hatch(F, P, (0.3, 0.4, 0.6), 0.9, 12, 6, 0.6, seed=8)     # colour it in
chalk(F, np.vstack([P, P[1:4]]), C.CHALK_COOL, 4.5, 0.95, seed=9)   # outline, overshooting its start
smudge(F, 600, 380, 300, 200, C.MOON, 0.12, additive=True)          # a little light on it
```

Geometry helpers (plain arrays, no camera): `A((x, y), (x, y), ...)` (points to an array), `spline(ctrl, n)` (Catmull-Rom), `arc(cx, cy, rx,
ry, a0, a1, n, rot)`, `blob(cx, cy, rx, ry, seed, rough, n, rot)`, `rrect_pts(l, t, r, b, rad)`,
`rect_pts(l, t, r, b)`, `resample(P, step)`, `fit(P, n)`, `zigzag(poly, ang, gap, seed, ...)`,
`path_of(P)` (screen points). Hashes and easing: `rnd(seed, salt)` 0..1, `rsym` -1..1, `vn(x, seed)`
smooth noise 0..1, `htab(i, mul, add)` per-index hash, `ease(x)`, `ease_out(x, p)`, `seg(t, a, b)`,
`ramp(x, a, b)`, `smooth(array)`, `mix(col_a, col_b, w)`.

Palette `C`: night `PAPER PAPER_DEEP PAPER_HAZE KNOCK CHALK CHALK_COOL CHALK_BLUE CHALK_DIM CHALK_FAR
MOON GLOOM GLOOM_MID GLOOM_EDGE`, amber `AMBER AMBER_DEEP AMBER_PALE AMBER_GLOW`, day paper and line
`DAY DAY_SHADE PENCIL SKIN`, the colour world (golden hour in rubbed pastel) `SKY_HI SKY_MID SKY_LOW
SUN_CORE SUN_HALO HILL_FAR HILL_MID HILL_NEAR HILL_LIT HILL_SHADE SHADOW CORAL MUSTARD LILAC ROSE
CREAM SEA JUMPER COAT`, evening `EVE_HI EVE_MID EVE_LOW EVE_PAPER`. (The older crayon primaries `SKY
SKY_PALE SUN ORANGE RED PINK GREEN GREEN_DEEP LIME PURPLE TEAL BLUE` are the prototype's: do not use
them in new work.)
Depth by tone: near `CHALK` / `CHALK_COOL`, middle `CHALK_DIM`, far `CHALK_FAR`.

## 5. Sets: draw on, un-draw, morph (sketch)

`Stroke(P, col=C.CHALK, w=4, a=1, seed=0, name="", **chalk_kw)`, `Fill(P, col, ang, gap, w, a, seed,
knock=None, base=0, grain="mid", clip=False, name="")` (knock = rub-out colour under it, base = alpha
of a rubbed base tone, a = alpha of the zigzag), `Sketch(items, name="")` (ordered; `name` prefixes
the item names). Two shorthands that return a Stroke: `line(x0, y0, x1, y1, col, w, a, seed, name)`
and `closed(P, col, w, a, seed, name)` (an outline that overshoots its start, as a child closes a shape).

- `S + T`, `S["sofa.back"]` (item), `S["sofa"]` / `S.sub("a", "b")` (sub-set, same objects), `S.without(...)`, `S.names()`.
- `S.place(dx, dy, scale=1, origin=(0, 0))`: a copy moved / scaled in the world.
- `S.draw(F, d=None, a=1, thin=1, tint=None, tint_w=0)`: paint at F.t. `d` = progress 0..1 of the whole
  set in authoring order; `a` pressure; `thin`, `tint`, `tint_w` make a far set thinner and hazier.
- Times, in seconds: `item.on = (t0, t1)` draws it on (the tip leads, pressure builds), `item.off =
  (t0, t1)` takes it back from both ends and leaves a rubbed ghost that fades over the second half.
  `S.set_on(t0, t1)`, `S.set_off(t0, t1)` for all items at once.
- `S.on_beats(F.tl, t0, every=1, dur=1, by=None)`: one group per `every` beats (0.5 = half beats)
  from the first beat at or after t0, each taking `dur` beats; returns the end time. `off_beats`
  likewise, in the same order (the first drawn leaves first; `S[::-1].off_beats(...)` takes the last
  one first). `S.spread(t0, every_s, dur_s, by, attr)` is the same in seconds. A group is an outline
  with its `.fill` (by=None) or everything sharing the first `by` name parts (by=1: a whole prop).
  An item with both `on` and `off` simply lives between them; build the set afresh every frame.
- `morph(A, B, w, pairs, stagger=0.5, seed=0)`: the set between A and B. `pairs = (("sofa", "desk"),
  ("window.frame", "window.frame"), ...)`: a name is one stroke, or a prefix whose strokes pair in
  order. ONLY declared pairs travel (arc-length resampling, the change running along the line,
  pressed lightly on the way). Two open lines travel end to end; an outline flattens into a line,
  a line opens into an outline, an outline turns into an outline (each started where it lies
  closest to the other, so nothing is unrolled across the picture). Everything else of A is wiped
  off first (w 0..0.5), everything else of B draws on last (w 0.5..1), each sweeping left to right.
  Draw what stays (a window that is the same in both) outside the morph. Declare few pairs, between
  things that are near each other: seven strokes converging on one desk is the busiest it should get.

```python
S = sofa(230, 744) + window(1300, 170, 1670, 560)
S["sofa"].on_beats(F.tl, 1.0)                        # the sofa, a part per beat from the first beat after 1.0 s
S["window"].on_beats(F.tl, 4.0, every=0.5)           # the window, a line per half beat
S.sub("window.rail", "window.curtain").set_off(30.0, 31.5)
S.draw(F)
morph(room, school, F.seg(33.0, 36.0), (("sofa", "lone"), ("lamp", "door"))).draw(F)
```

## 6. The parts (read the part docs: they are the reference)

Everything below is exported by `from hx.chalk import *` (where a part doc still says the package
does not import it yet, or names a prototype function in `props.py`, that is out of date: `props.py`
and the demo scenes are gone). One doc per part, written and checked by its own artist and reviewer:

| doc | what it is |
|---|---|
| `doc/figure.md` | the two characters: `figure()`, the Pose and its keys (turn, lying, face), `alive`, `act`, `lag`, `turn_round`, `walk`, `walk_to`, `walk_away`, `run`, the pose library, skins, the rim of light |
| `doc/acting_child.md` | the child's solo performances, sections s01 to s05 (functions of song time giving pose, place and the points a scene needs) |
| `doc/acting_pair.md` | the friend, and the two together, s03 and s06 to s11 (duets: hands that meet, eye lines, the hand-off states) |
| `doc/people.md` | the other people: faceless outline pupils and adults, the classroom rows, the stream on the corridor line, the ring of backs and its whispers, the home adults, the family line |
| `doc/gloom.md` | the scribble in all its forms: birth, cloud, strand, crossings-out, knot, shawl, lid over the plain, curtains, unravelling, fragments, the small tangle on its string |
| `doc/weather.md` | light and weather: rain (hanging still in the silences), mist, window pools, lamp, shafts and dust, the friend's amber (glow, ground line with its pulse), the rip of the sheet, shadows |
| `doc/sets.md` | the indoor sets as Places: the room (night, evening, sunset) at `dx`, classroom, home table, corridor, and the declared changes between them |
| `doc/things.md` | the small things: family drawing (whole, torn, held, taped), the caped hero, speech balloon and bubbles, voice line, moth and lamp, phone, crows and birds, chalk stub, tape, string |
| `doc/land.md` | the plain of the choruses, footsteps, the three towering groups (voices, backs, the split house), `tower_layout` (the wide camera and where everything stands) |
| `doc/day.md` | the hill world in both skins (`hills.py`), the sky, sun and paper of the colour world, the ring (`day.py`) |

The two acting modules are used as modules, never star-imported (both define `Act`):
`from hx.chalk import acting_child as AC, acting_pair as AP`. A performance is a function of song
time: `a = AC.s01(F.t)` gives an Act (pose, x, y, face, grab, the points and cue numbers the scene
needs: `a.pts`, `a.num`), `a.show(F)` draws it; `AP.s08(F.t)` gives a Duet (`.child`, `.friend`,
`.pts`, `.num`, `.show(F)`). Take x, y and face from the Act every frame. The rest states at the
hand-offs are `AC.hold_B1` .. `hold_B5` and `AP.hold_B6` .. `hold_B10`.

Rulings where two parts overlap:
- **Rim of light on a figure**: use `figure(..., rim=...)` (it follows the outline), not `weather.rim`.
- **Classroom rows**: `people.class_rows()` with its own defaults (not `sets.CLASS_ROWS`); the desk
  that stands apart is the set's (`sets.classroom`, scale 1.35, top at `story.DESK_TOP_Y`).
- **The parting of the curtains**: the seam is where the performance opens it (`gloom.PART_GAP` =
  X5 + 180); `handoff_gloom(F, "B8", left=..., right=...)` with the grips of `AP.hold_B8` / `AP.s08`.
- **The phone** lies at `story.PHONE` (the rug's far edge) in the first two rooms; in the coda the scene
  lays it where `AP.s11`'s hand will reach (`pts["reach"]`).
- **The tear of the sheet**: `weather.tear` / `tear_shafts` / `scraps` (the prototype's `tear_light` is gone).
- **The wide frame of the choruses**: `story.WIDE_ZOOM` (0.205) through `land.tower_layout`.
- **Seeds**: child 3, friend 5, the scribble 4 (`story.py`); the scribble's anchor, hand and churn must
  agree across modules (see `doc/gloom.md`, "four numbers that must agree everywhere").

The colour ring: `ring(F, draw_fn, cx, cy, radius, turn=None, ...)` (`doc/day.md`): call it FIRST in the
scene (it starts the picture over); `draw_fn(F2)` draws the scene for the skin of the Frame it gets
and is rendered twice (night, day); (cx, cy) is the WORLD point it opens from, `radius` is SCREEN px.

## 11. Title

`title.draw(F, t0=2.0, t1=10.5, y=150, cx=960)`: the title and credit lines in chalk, upper middle,
in screen space, read from `hx/credits.py`. Call it last in the scene that covers 2.0-10.5 s.
Measured ink at the defaults: the title line x 651-1272, y 127-183 (622 px wide: it is centred on
`cx`), the credit lines x 792-1126, y 220-289. Keep x 630-1290, y 110-300 free, or move it with
`cx` / `y` (the demo room uses cx=900 to clear its curtain rail).

## 12. Flicker: what moves and what must not

Measured on 10 s clips with a static camera (room, plain): as rendered 0.75 to 0.8 levels mean luma
change and 2.2 to 2.4 percent of pixels over 8 levels on a boil step, under 0.01 inside a pair; as
encoded by `hx.render` 0.85 to 0.9 levels, 2.2 to 2.3 percent, 0.03 inside a pair, 8.7 MB. The day
field: 0.45 levels, 1.3 percent, 12 MB. (The prototype: 4.1 levels, 13 percent, 31 MB.) Targets:
under 1.2 levels and 6 percent on a boil step, about zero inside a pair, under 25 MB. To stay there:

- Do not animate large areas on every step: no re-seeded hatch, no smudge whose size or alpha
  jitters. Pass `boil=False` for any zigzag that is part of the background.
- Inside a pair nothing should change but what truly moves at 30 fps (camera, a pose). Drive
  secondary motion (sways, flaps, rain, dust) from `F.tb`, not `F.t`.
- Never change a seed with time (a new seed = a new hand = the whole line jumps).
- A thing that fades in or out: alpha over at least 6 frames, or `draw=` / `on` / `off`.
- Check with `python -m hx.motion t0 t1` before handing a scene over. It cannot tell flicker from
  motion: a walking figure or a camera move counts in both columns (a 300 px child trudging adds
  about 0.7 levels inside a pair). Judge the numbers on a stretch where nothing is meant to move.
- In an encoded file every 60th frame is a keyframe; the step onto it measures about 1.3 to 1.5
  levels instead of 0.9 (the encoder refreshing the whole picture, not the drawing).

## 13. Costs (1080p, one core)

Budget: a whole frame under 200 ms. Paper + finish costs 24 ms; the first frame of a process 1 to 2 s
more (textures are baked once). The ring pays for two renders. Every part doc lists the cost of its
pieces; typical: a figure 5 to 8 ms, the cloud 12 to 17 ms, the lid or the curtains 32 to 40 ms, the
room 53 to 58 ms, the rip of the curtains 55 to 61 ms for its first 1.8 s, the plain 15 ms, a towering group 15 ms, the day hills 27 ms, the sky 8 ms, rain 3 ms
a layer. Building a Sketch is cheap: rebuild sets every frame. Things wholly off screen are skipped.
A trap: skia-python serialises an image on every `setShader`, so never build a paint with an image
shader per call; use `F.paint` / `F.pen` (cached per grain).

## 14. Known limits

- The camera has no rotation. Sketch items have no per-item camera depth (wrap the draw in `F.depth`).
- `morph`: an outline that turns into a line is a flattened sliver on its way; keep such pairs few.
- `Sketch.draw(d=...)` brings a Fill (with its knock-out) on before the Stroke that outlines it: over
  a light background that shows as a blot ahead of the line; prefer `on` times to `d=` there.
- Rubbed tone carries the marks of the rubbing hand fixed to the screen; under a fast camera move
  large smudges slide under that texture (the same is true, and wanted, for lines).
- Each part doc ends with its own open points: read them before leaning on a piece.
