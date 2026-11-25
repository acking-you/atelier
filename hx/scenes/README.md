# hx/scenes: writing a scene module on the scaffold

The film is ONE continuous drawing with no cuts, written as eleven scene modules (`s01_room.py` ..
`s11_coda.py`), one time span each. Each module is a scaffold today: its header holds your cue
sheet, its `draw(F)` is a placeholder that shows the hand-off picture it starts from and, after a
plain cut in the middle of its span, the one it ends on. You replace the placeholder with the scene.
With the scaffolds the whole film already renders end to end and every hand-off already matches;
your job is to keep it that way while everything between the two pictures comes alive.

Read first: `hx/chalk/README.md` (the kit), `hx/STORYBOARD.md` section 5 for your span,
`hx/story.py` (binding numbers), the part docs your scene uses (`hx/chalk/doc/`), and
`hx/scenes/_shared.py` (short: every layer has a docstring). Python: `.venv/bin/python` with
`PYTHONPATH=.` from the project root. No process pools larger than 4.

## 1. The rules

1. **No cuts.** The child is on screen from 9.3 s to the last frame. A change of place is a set
   un-drawing and the next drawing on round the child, a declared morph, or the camera travelling.
   Nothing pops, nothing cross-fades: things draw on (`on`, `draw=`) with the music and are taken
   back from their ends. A fade needs at least 6 frames. The only abrupt events are musical (the
   band's entries at 58.60 and 201.25, the three hits of each chorus).
2. **The joining rule.** `draw(F)` begins with

   ```python
   if S.joined(F, START, END):
       return
   ```

   In the last 0.25 s before your end hand-off `joined` draws the hand-off picture
   (`S.handoff(F, END)`) and returns True: both neighbours draw that picture with the same code.
   So: your own drawing must have ARRIVED at the hand-off state by `S.T[END] - 0.25` (camera still,
   figures in their rest state, sets complete, nothing half drawn), and your own first frame must
   BE the picture `S.handoff(F, START)` (movement begins after it). You never call
   `handoff(F, START)` yourself: you build your first frame from the same layers with the hand-off's
   arguments, and move the arguments from there. A scene arrives at a hand-off by moving the layers'
   arguments to the hand-off's values.
3. **One world.** World coordinates through `F.cam`; never transform the canvas. The child travels
   to the right through one world (`hx/story.py`: `X1` .. `X10`, `ROOM2_DX`, `ROOM3_DX`); nothing is
   re-centred. Draw `ground_line(F)` in every frame (`S.bare`, `S.room_set`, `S.hill_ground` and
   `S.hill_world` draw it for you; `S.plain_base` does not).
4. **Three clocks.** `F.t`: everything that acts and everything timed against the song (cameras,
   poses, draw-on, the performances). `F.tb` (the kit's `t=None`): what is merely alive (rain, the
   scribble's churn, sways, dust); it stands still in the two true silences (56.00 to 58.60 and
   193.00 to 201.27), where the picture is still but for what acts. Never give the boil clock a time
   of the song. Inside a pair of frames nothing changes but what truly moves.
5. **Deterministic.** A frame is a pure function of time: no state, no random numbers but the kit's
   hashes with a fixed seed. Never change a seed with time. Seeds of the story: child 3, friend 5,
   the scribble 4, the ground line 20.
6. **The lyric band.** The lower 20 percent of the frame (screen y > 864) belongs to the lyric line:
   ground, floor and light may be there, nothing that matters.
7. **No lyric text**, anywhere: not in code, comments, names, pictures or reports. A line is its
   0-based LRC index and time (`F.since(19)`, `F.line_ramp(19)`), or a loose paraphrase. No letters
   or numerals inside the picture (the title overlay of s01 is the one exception).
8. **Colour.** Before 217.84 only cold chalks; amber is the friend's alone (the friend, its window,
   the amber line, the tape, the phone call). Only the scribble is black. Crayon colour after the ring.
9. **Care.** The protagonist is a child with depression. Causes are shown through image and
   metaphor: never graphic violence, abuse or humiliation played for effect, never one explanation
   that makes the illness simple or blames a person; the other people are faceless outlines turned
   away, not villains. No self-harm; no heights, edges, water or trains as threat ("leaving" is only
   the child walking away while its line loses pressure). No magic cure: relief is gradual and
   partly relational; the end is warm and open, with the gloom still there, small.
10. **Acting first.** Every lyric line has one clear action by the child; the performances are
    written (`hx/chalk/acting_child.py`, `acting_pair.py`): take `x`, `y`, `face` from the Act on
    every frame and put the camera where the beat reads (the head 90 px or more on screen for a
    face; your header lists the beats that need it).
11. **Files.** You own your module. Frozen: `hx/story.py`, `hx/STORYBOARD.md`, `hx/chalk/` and its
    docs, `hx/frame.py`, `hx/scenes/__init__.py`, `hx/scenes/_shared.py`, `hx/handoff.py`,
    `hx/pops.py`. If a kit piece or a shared layer is wrong or missing, work round it in your module
    and report it precisely: do not edit it (ten other modules lean on it).

## 2. A module on the scaffold

```python
from hx import story
from hx.chalk import *
from hx.chalk import acting_child as AC                   # as modules, never star-imported (both define Act)
from . import _shared as S

SPAN = (115.77, 138.20)
START, END = "B4", "B5"                                   # the hand-offs you start from and end on

def draw(F):
    if S.joined(F, START, END):                           # the last 0.25 s: the hand-off picture B5
        return
    a = AC.s05(F.t)                                       # the performance (it IS the rest state at both ends)
    w = ease(F.seg(126.3, 130.0))                         # your own timing, on F.t
    F.cam = Cam.ease(S.CAM[START], S.CAM[END], w)         # camera first; still at both ends
    S.bare(F)                                             # the ground line
    ...                                                   # your sets and things behind the child
    J = S.child(F, a)                                     # seed, height, skin, contact shadow
    ...                                                   # things in its hands
    S.scribble(F, S.cloud_between(START, END, w, a.x), J) # the cloud resting on its crown, the strand, dust
```

At `F.t = S.T[START]` this is `S.handoff(F, "B4")` (camera `S.CAM["B4"]`, `AC.hold_B4`, B4's cloud);
from `S.T[END] - 0.25` on `joined` takes over with `S.handoff(F, "B5")`, and because `w` has been 1
since 130.0 nothing changes on that frame.

## 3. The shared layers (`from . import _shared as S`)

Use them wherever the thing appears: the same thing is then drawn by the same code in every module,
and a hand-off is only a set of argument values. Each takes explicit arguments; none sets the camera.

| layer | what it draws | where |
|---|---|---|
| `S.child(F, act, rim=None, a=1, shadow=1)` | the child from an Act (`AC.s01(F.t)` .., a Duet's `.child`): contact shadow, figure. `rim=S.amber_rim(k)` the friend's light on it, `S.shaft_rim(F, k, from_)` pale light from above. `shadow=0` on the sofa and in the day world. Returns the joints | all |
| `S.friend(F, act, rim=None, a=1, glow=1, wet=0)` | the friend: its amber glow (sized by how it stands), the figure | s06 to s10 |
| `S.pair(F, D, child_rim, friend_rim, a, glow, wet, shadow, warm)` | both figures of a Duet in its order. `warm` 0..1: the friend's warmth on the child once they touch (an amber rim on the child, a small glow where the hands meet; 1 at B6 and B7). Returns `(jc, jf)` | s06 to s10 |
| `S.far_friend(F, act, wet=1, glow=0.6)` | the far friend of chorus 1 (`AP.s03_friend`): glow, reflection, figure, the point of light it becomes | s03 |
| `S.scribble(F, cloud, J, k=1, slack=0.8, a=1, strand_=1, dust=0.5)` | the cloud resting on the child's crown, the strand, falling dust. `cloud = (cx, cy, rx, ry)`; at a hand-off `story.HANDOFF[name]["cloud"]`; between two: `S.cloud_between(a, b, w, child_x)`. After the child | s01 to s06 |
| `S.lid(F, ax, crown=None, thin=0, slack=0.8, hang=235, cam=None, **ceiling_kw)` | the scribble as a lid for the camera in force, its thin pale place, the strand up into it. Before the figures | s03, s06, s07 |
| `S.high_cloud(F, heads=(jc, jf), clear=1)` | the high cloud of B7 with its loose loops kept off the two heads (a loop ending on a head reads as a strand). After the figures. `clear` eased to 0 hands it to `S.curtain` (s08) | s07, s08 |
| `S.clear_of(*joints, k=1)` | the `avoid=` discs that keep the scribble's loose loops off these heads (for `S.lid`, `gloom`); B6's lid keeps them off the friend | s06, s07 |
| `S.tangle_on_string(F, hand, face)` | the small tangle on its string over the hand at the hip (`D.pts["string"]`); `face` +1 at B9, -1 at B10 | s09 to s11 |
| `S.room_set(F, mood, dx, R=None, light, pane_rain, crow_times, crow_leave, drawing, empty, phone_lit, phone_a, lamp_lit, cushion, wall_off)` | the room complete in paint order up to the sofa and cushion: dressing, window light, view, pane rain, crows, GROUND LINE, strokes, the family drawing, the phone. `R`: your scheduled Place (`room_on`, `room_on_coda`) or a declared change (`room_to_class(w)`, `plain_to_room(w)`, `room_to_corridor(w)`: drawn whole, the drawing and the phone laid over it). `drawing`: the family drawing on the wall (night room; taped in the coda); `empty`: the empty place where it hung (two pins, a ghost of the sheet): the evening room, while the halves are in the child's jumper (B3: `drawing=0, empty=1`). `wall_off=(t0, t1)` takes either off with the room. `cushion=False` when the child lies on the sofa (draw `R["cushion"]` after it). Returns the Place | s01 to s04, s11 |
| `S.room_light(F, mood, dx, a)` | the window's glow and pool alone (the same light round a declared change) | s02, s03, s04 |
| `S.crow_wire(F, dx, times)` | the wire as the crows have left it, and their places; the canon of their landings is `S.CROW_TIMES` | s01, s02 |
| `S.bare(F, hour=1)` | the bare sheet: the ground line (on the day skin the sheet toned to evening first) | s02 to s06, s10, s11 |
| `S.plain_base(F, vx, k=None, a=1, wet=None, hill=False, reach=None, far=1)` | the plain behind everything: ground, mist, far rain. Not the ground line. `a=0`: the far rain only (a bare sheet: only from B2 and B5 into the choruses); once the plain is there `a` stays 1 (B6, B7 and B8 draw it so, with `hill=True` from 175 on, where only horizon and haze remain) | s03, s06, s07, s08, s09 |
| `S.sky_gap(F, k)` | the guess of light under the lid's thin pale place | s06, s07 |
| `S.hill_ground(F, rise=1, a=1)` | the night land before the rip: the hills' own near ground and the first hill alone, with the ground line | s07, s08 |
| `S.curtain(F, left, right, tremble, light, spread, drop, rip, stays, cam, dust_t)` | the parted curtains at the seam `S.SEAM` with the light through the opening; with `rip=` the rip | s08, s09 |
| `S.calm_grips(D, t)` | the grips of `AP.s08` / `hold_B8` with their shiver taken out (the long silence) | s08, s09 |
| `S.hill_world(F, hour, gone, back, lit, light, figures, bloom, grow, skip, tree_a)` | the hill world in the skin of F: sky, three layers of hills, the friend's house (`S.HOUSE`), tree, the figures' shadows, flowers, ground line. Give `day.ring` a function that calls it. Returns the rise | s09, s10 |
| `S.sun_shadow(F, act, hour, a, rise)` | a figure's long shadow and contact shadow in the day skin (`hill_world` draws it for `figures`; B10 draws it on the bare sheet) | s09 to s11 |
| `S.rain_k(t)`, `S.rain_back(F, k=None)`, `S.rain_front(F, k=None)` | the story's rain as one number (0.6 hanging at B2, 0.25 at B6), the far rain before the figures, the near rain after the scribble | s02, s03, s06, s07 |
| `S.hold(name, t)` | the figures' rest state at a hand-off: an Act (B1 to B5) or a Duet (B6 to B10) | |
| `S.handoff(F, name)`, `S.joined(F, start, end)` | the hand-off picture; the joining rule | |

Constants: `S.T[name]` (hand-off times), `S.CAM[name]` (hand-off cameras), `S.JOIN` (0.25), `S.HIGH`
(B7's cloud), `S.SEAM` (X5 + 180), `S.HOUSE`, `S.CROW_TIMES`, `S.B8_TREMBLE`, `S.EMPTY_GHOST`, `S.HEAD_CLEAR`.

Paint order of a frame (back to front): set dressing .. window light .. view .. `plain_base` (ground,
mist, far rain) .. light through the scribble (`sky_gap`) .. ground line .. sets' strokes .. lid or
curtains .. shadows, glows .. figures and what they hold .. the cloud, the strand, the tangle ..
near rain .. flash. `S.handoff`'s ten private functions (`_b_room`, `_b_bare`, `_b6` .. `_b10` in
`_shared.py`) are the worked examples: each is a dozen lines of layers in the right order.

## 4. The ten hand-off pictures

`S.handoff(F, name)`: the complete picture at `F.t`, a function of time (breath, blinks, churn, rain
on the boil clock, crows shifting). Proofs: `hx/_review/v4_scenes/_shared/` (`ten_pictures.jpg`,
`B1.png` .. `B10.png`, `B<n>_six.jpg`, `costs.txt`, `flicker.txt`, `handoff.txt`).

| | time | camera | picture | ms |
|---|---|---|---|---|
| B1 | 36.27 | (960, 540, 1.0) | the night room complete, rain on the pane, eleven crows, the amber window; the child standing at X1, head down; the cloud on its crown, the strand | 116 |
| B2 | 58.60 | (2200, 520, 0.9) | bare sheet; the child at X2, three-quarter to us, hands at its chest; the cloud; rain 0.6 hanging still (the whole silence from 56.0 is this picture) | 56 |
| B3 | 91.77 | (4020, 540, 1.0) | the evening room at ROOM2_DX, the long pale pool, no crows, the phone's screen pale; the child standing on the rug, eyes on the phone; the cloud; on the wall only the empty place where the drawing hung (its halves are in the child's jumper) | 113 |
| B4 | 115.77 | (3760, 520, 0.9) | bare sheet; the child planted at X4, braced, head level; the cloud | 55 |
| B5 | 138.20 | (4300, 520, 0.9) | bare sheet; the child at X5, head down; the large cloud | 56 |
| B6 | 158.86 | (4390, 590, 1.2) | the plain; the lid with its thin pale place and the guess of light, its loops kept off the friend's head; the child sitting, the friend crouched, hands joined, both looking up; rain 0.25 | 110 |
| B7 | 182.30 | (4390, 500, 1.3) | the plain with the first hill; both standing, the friend's hand on the child's upper arm; the high cloud, its loops kept off both heads | 84 |
| B8 | 201.25 | (4390, 470, 0.85) | the curtains parted at X5 + 180 and held by four hands, the shaft, dust on the true time | 108 |
| B9 | 226.76 | (5690, 480, 0.75) | day skin: the hill world at afternoon gold; the two hand in hand on the hill top; the small tangle on its string | 80 |
| B10 | 244.50 | (8660, 540, 1.0) | day skin: the bare sheet toned to evening; the child alone at X10 facing left, its long shadow; the tangle on its string | 38 |

## 5. Tools (exact commands, from the project root)

```sh
PYTHONPATH=. .venv/bin/python -m hx.scenes                                   # the eleven spans: no gaps, no overlaps
PYTHONPATH=. .venv/bin/python -m hx.still --t 124.76 --scale 1.0 --out hx/_review/v4_scenes/s05/t124.76.png   # one frame at 100 percent
PYTHONPATH=. .venv/bin/python -m hx.still --sheet 115.77:138.2 --n 24 --cols 6 --out hx/_review/v4_scenes/s05/sheet.jpg
PYTHONPATH=. .venv/bin/python -m hx.render --out output/s05.mp4 --t0 115 --t1 139 --audio --lyrics placeholder --workers 4
PYTHONPATH=. .venv/bin/python -m hx.pops 115.77 138.20 --workers 4 --out hx/_review/v4_scenes/s05/pops   # where the picture jumps
PYTHONPATH=. .venv/bin/python -m hx.handoff B4 B5 --out hx/_review/v4_scenes/s05/handoff                 # your two hand-offs: must print ok
PYTHONPATH=. .venv/bin/python -m hx.scenes._shared ends s05_pre2             # your two ends against the hand-off pictures, same instant
PYTHONPATH=. .venv/bin/python -m hx.motion 120.0 122.0                       # flicker on a stretch where nothing is meant to move
PYTHONPATH=. .venv/bin/python -m hx.motion output/s05.mp4                    # the same on the encoded clip
```

- `hx.still`: `--scale 1.0` to judge the chalk; look at stills with crops at 100 percent, and at
  consecutive frames for anything that moves. `--lyrics placeholder` shows where the lyric line sits.
- `hx.render`: a slice with the recording under it; `--draft` for a quick 960x540 at 15 fps. It
  stops on an import error of any scene module.
- `hx.pops`: lists the steps that stand out from their neighbourhood and writes before | after |
  difference for the worst. A hit of the band, a fast gesture or a camera jolt are meant; the scan
  only says where to look. A scaffold shows exactly one: its placeholder cut.
- `hx.handoff`: the frame before and the frame after each hand-off against the frame steps round
  them: "ok" or "POP". Run it for both of yours whenever you touched either end.
- `ends`: your own drawing against `S.handoff` at the same instant (no boil step between the two):
  at your first frame it should be a fraction of a level (a first move that has just begun), at
  your last own frame before the `joined` window about 0 (the last ease of a move may still show as
  a fraction of a level).
- The proof harness for a piece of your scene without the module (`hx/chalk/proof.py`):
  `still(draw, t, path, crop=)`, `sheet(draw, times, path)`, `clip(draw, t0, t1, path)`,
  `flicker(draw, t0, t1)` with any `draw(F)`; `skin="day"` starts on the warm paper.

Targets: a whole frame under 200 ms on one core (the hand-off pictures cost 38 to 117); on a still
stretch under 1.2 levels and 6 percent of pixels on a boil step, about zero inside a pair; in the two
silences exactly 0 on a boil step.

## 6. Before you hand a scene over

- [ ] `python -m hx.scenes`: eleven spans, 0 to the end, no gaps (you did not change `SPAN`).
- [ ] `python -m hx.handoff <start> <end>`: both "ok". `ends <module>`: start a fraction of a level,
      end about 0.
- [ ] `python -m hx.pops <t0> <t1>`: every listed step is one you meant (name them in your report).
      No placeholder cut is left.
- [ ] No frame over 200 ms (say what your dearest frames cost).
- [ ] Flicker on two still stretches of your span inside the targets; if a silence is yours
      (s02: 56.00 to 58.60; s08: 193.00 to 201.25) nothing changes on a boil step, and inside a pair
      only what is told to move (breath, a blink, dust on the true time, the calmed grips).
- [ ] The child is on screen in every frame and never jumps: take `x`, `y`, `face` from the Act.
- [ ] Every beat of your cue sheet is there and lands on its time; faces are big enough when they act.
- [ ] Nothing that matters below screen y 864; render a sheet with `--lyrics placeholder` and look.
- [ ] You looked: a 24-frame sheet of the span, every acted beat as consecutive frames at 100
      percent, and the rendered slice with the recording. A frame must look like a picture, never
      like a diagram: dressed sets, light, depth by tone and overlap, big things cropped by the frame.
- [ ] No lyric text anywhere; no letters or numerals in the picture; only cold chalks and the
      friend's amber before 217.84; the care rules hold.
- [ ] Your report says what is not good yet, and what you needed from the kit or the shared layers.
