# hx.chalk.acting_child: the child's solo performances (0 to 138.2 s)

The child of sections s01 to s05, as functions of the song's time. A performance returns an `Act`:
what `figure()` needs (pose, ground point, face, pinned hands, draw-on, pressure) and the points and
numbers the scene needs to stage what the child handles. It draws nothing and knows nothing of the
sets: every place and every thing it touches comes in as an argument, with the numbers of
`hx/story.py` as defaults. No state, no randomness: the same `t` gives the same `Act`.

    from hx.chalk.acting_child import *        # until hx/chalk/__init__.py exports it

The star import gives every name below except the class `Act` and `beat_after` (acting_pair exports
a class and a function of the same names; the two `Act` classes are used the same way).

Proofs, and the scripts that make them: `hx/_review/v4_kit/acting_child/` (`proofs.py`: every picture
is staged with the real kit, so its draw functions `s01_draw` .. `s05_draw` are worked examples of
everything below; `check.py`: pops, sliding feet, cost, hand-offs as numbers). A second set of scenes,
written from this page alone at the storyboard's cameras, with every beat cut at 100 percent:
`review/review.py` there (`s01_draw` .. `s05_draw` again, shorter); `review/measure.py`: the hand-offs
against `hx/story.py`, cost, determinism, extreme cameras, flicker. No lyric text anywhere.

## 1. A performance in a scene

```python
def draw(F):
    a = s03(F.t)                                   # or perform(F.t): s01 .. s05 by their spans
    F.cam = ...
    ground_line(F)
    J = a.show(F, rim=(C.AMBER, 1, a.num["rim"]))  # = figure(F, a.x, a.y, a.h, a.pose, "child", a.face, seed=3, a=a.a,
                                                   #          grab=a.grab, draw=a.draw, rim=...)
    strand(F, J["crown"], ...)                     # J: figure()'s joints (pinned hands applied)
```

| `Act` | |
|---|---|
| `pose`, `x`, `y`, `face` | the Pose (follow-through, breath and blinks already in it), the WORLD ground point, +1 / -1 |
| `h` | world height to draw it with (380) |
| `grab` | `{"f": (x, y)}` / `{"b": ..}` or None: hands pinned to world points (give it to `figure`) |
| `draw` | 0..1: the figure is being drawn (s01 only), else 1 |
| `a` | pressure of its line (s03: it pales as it walks away), else 1 |
| `J` | the world joints of the pose WITHOUT drawing (`pose_joints`: head neck crown mouth back top ha_f ...; pinned hands not applied): use it for what must be placed BEFORE the figure is drawn |
| `pts` | named world points `(x, y)` (or polylines `(n, 2)`), listed per performance; always `crown`, `mouth` |
| `num` | named numbers: cues 0..1, counts, world offsets, listed per performance |
| `show(F, skin="child", seed=3, a=1, **kw)` | draws it; `kw` goes to `figure` (`rim=`, `t=`); returns figure()'s joints |

Rules that hold for all five:
- **Times** are the song's, absolute. Every section has a table of cue times (`S01_T` .. `S05_T`);
  pass any of its keys as a keyword to shift a cue: `s04(F.t, plant=108.3)`. Changing a time changes
  nothing else; keep the order of the cues.
- **Places** are world x (`x0`, `x1` ...) with `story.X1 .. X5` as defaults; the child stands on
  `story.FLOOR` except where stated. s01 happens on the sofa at the story's anchors (room at dx = 0).
- **The scene draws the things**: the performance gives the hand, the scene puts the stub, the
  phone, the halves, the balloon there. Draw order: sets, `ground_line`, things behind, the child,
  things in its hands, the scribble (give `gloom(..., avoid=[(J["head"][0], J["head"][1], 1.12 * J["R"])])`
  or the loops hang over the face that is acting).
- **Clock**: everything here is acting: call it with `F.t` (never `F.tb`). Breath and blinks run on
  the true time too, so the child breathes through the two silences.
- **Framing**: what a beat needs to read is given as the height of the HEAD on screen (the head is
  0.31 of the figure: 118 px at zoom 1). Body acting (walks, shoves, the hits, the fall) reads from a
  head of 24 px (the wide frame); hands and things from 60 px; eyes, lids and mouth from 90 px.

## 2. The five performances

### s01(t, tip=None, hero=HERO, balloon=None, window=story.WINDOW, h=380, **times) -> Act   (0 to 36.27)

On the sofa, ground point `(story.CURL_X, story.SOFA_SEAT_Y)` until it slides off; then `(story.X1, FLOOR)`.

| cue (`S01_T`) | default | what the child does |
|---|---|---|
| `draw` | (9.27, 11.3) | it is drawn, curled up asleep: `Act.draw` runs 0..1 |
| `wake` | 12.34 | the eyes open half, a look up at what hangs over it |
| `sag` | (13.29, 14.87) | it clings to the armrest (first time); the belly comes down on it (second): the crown gives (`press`), it bears it; its far hand slides off the armrest and hangs before the sofa's front |
| `hero` | (16.5, 18.0) | the hanging hand lifts (from 16.04) to beside its chin, over the armrest's outer end, and draws in the air; its eyes go up to the wall, then the head: the first time the face lifts, the mouth almost smiles; the hand goes back onto the armrest (18.3 to 19.2) |
| `cross` | (20.79, 21.2, 21.6) | a flinch at each crossing-out, each a little stronger; the eyes fall, it sinks back into the curl |
| `situp` | (22.0, 24.2) | sits up (the rig's `sit_up_pose`, slow to start), hugging its knees |
| `crows` | 24.27 | turns its head to the window; a small move of the eyes at each landing, a beat apart |
| `speak` | (28.6, 30.6) | a breath, the mouth opens, three small tries, nothing comes; the mouth shuts |
| `wipe` | 31.58 | the far hand goes up beside its face (from 31.24) and comes down and out through the balloon's tail (0.38 s), then back to its knees |
| `again` | (32.0, 33.6) | once more, smaller; the head goes down |
| `off` | (33.6, 36.0) | slides off the seat (the rig's `slide_off_pose`) and stands at `story.X1`: hand-off B1 from 35.82 |

- `tip`: world point of the hero's chalk tip (`things.sketch_tip(S, F.t)`) or None; the drawing hand
  (the FAR hand, `ha_b`) repeats its movement small (0.16 of it sideways, 0.30 up and down), about
  `AIR` (975, 560: beside the chin, over the outer end of the sofa's right arm, where it does not
  cross the face). `hero = (x, y, h)`: the hero's feet and height (only scales that movement).
- `balloon = (x, y, r)`: centre and radius of the speech balloon (default `BALLOON` = (965, 360, 76):
  `balloon(965, 360, 95, 76, mouth=a.pts["mouth"], ...)`). Its middle hangs out of an arm's reach
  (the sitting child's hand gets to about (925, 470)): only the side it hangs on is used. The sleeve
  comes down through the balloon's TAIL, from (890, 473) to (918, 573); the scene wipes the balloon
  itself with `num["wipe"]` (`off=(31.58, 31.96)`). `window`: where the crows land (l, t, r, b).
- `pts`: `tip` (the fingertip of the drawing hand), `hand` (the wiping hand: the same far hand),
  `mouth`, `crown`. `num`: `hero` (0..1 through the drawing), `speak` (how far the mouth is open:
  the balloon's line can follow it), `wipe` (0..1 the sleeve's stroke: wipe the balloon with it),
  `press` (the weight on the crown, 0..1).
- Framing: the storyboard's push-in (head about 150 px) for wake, hero and crossing-out (the waking
  is in the lids and the hand's drawing is a wrist's movement: neither reads in the wide room); the
  try to speak needs a head of 90 px or more (the mouth is all there is); the rest reads in the
  wide room.
- The cloud must rest on `J["back"]` / `J["top"]` of the lying child (`a.J` has them before drawing).

### s02(t, x0=X1, x_stop=None, x1=X2, push=-1, desk=None, desk_top=DESK_TOP, table_top=TABLE_TOP, drawing_x=None, sheet=0.62, h=380, **times) -> Act   (36.27 to 58.60)

| cue (`S02_T`) | default | |
|---|---|---|
| `go` | 36.27 | trudges from `x0` to `x_stop` (default `x0 + 440`), a step a beat, five steps (arrives 40.02) |
| `speak` | (40.3, 42.6) | lifts its face, a hand half raised, three small tries at a word, the hand sinks, the head droops |
| `shoves` | (42.7, 44.12, 44.86) | hands on its desk; three shoves, each with the whole body, each further (`SHOVE` = 58, 76, 96 units); the desk comes back each time and stands the child up; a tremble on the last |
| `drop` | 46.2 | the arms drop, the head goes down |
| `on` | 46.765 | walks on to `x1`, seven steps (arrives 52.02) |
| `tear` | (53.14, 53.51) | behind the table, three-quarter to us: its eyes follow the one who leaves (left), drop to the sheet at the first tear (a hand goes to that half), the second (the other hand); torn through (53.67), the halves come a little apart in its hands; its eyes follow the other one (right) |
| `hold` | (54.64, 55.01) | lifts the two halves and holds them together, looking down at them |
| `loose` | 55.27 | its grip loosens: the halves drift apart |
| `tuck` | (55.62, 55.95) | takes them to its chest |
| `hush` | (56.0, 58.6) | the rest state of B2 (see 3): still but for the breath, one slow blink at 57.1 |

- `push`: which way the desk is shoved. `-1` (default): the child has passed its desk; it turns
  round toward us (41.95, 0.42 s) and pushes it to the left, then turns back (46.39). `+1`: the desk
  stands ahead and is pushed on to the right; no turns. `desk`: world x of the desk's end the hands go
  on (default 112 units from the child on that side); `desk_top`: world y of its top (613.75:
  `sets.CLASS_DESK_TOP_Y`). With the kit's classroom and the child travelling right, the proof uses
  `classroom(side=1, desk_dx=(x_stop - 112 - 1976) + a.num["desk_dx"], chair_dx=-440)` and rows that
  end left of x 1200: the desk stands under the window, the rows to its left, and the child shoves
  it back toward them.
- `table_top`: world y of the table's top (580); `drawing_x`: world x of the tear (default `x1`); the
  child stands BEHIND the table at `x1` (`home_anchors(apart, x1 - 1010)["child"]`): draw it before
  the table. `sheet`: the scale of the drawing (at 0.62 it stays below the chin).
- The drawing: it stands on the table (as a child draws a thing on a table), its middle at
  `pts["sheet"]`, and tears there; from `num["in_hands"]` on it is two halves in two hands. The two
  calls give the same picture on the frame they change over (measured: 0 levels):

  ```python
  n = a.num                                                   # after the table's groups, 50.0 to 56.0
  if n["in_hands"]:
      family_held(F, a.pts["hand_l"], a.pts["hand_r"], s=n["sheet"], a=1 - n["tuck"])
  else:
      family(*a.pts["sheet"], n["sheet"], tear=n["tear"], detail=2).draw(F)
  ```
- `grab` pins both hands on the desk (while `num["on_desk"]` is 1) and beside the halves.
- `pts`: `hand_l`, `hand_r` (as seen: on the desk; from the first tear on the two points
  `family_held` takes: where the halves are gripped, 124 * sheet apart when they are together; the
  mitts themselves are put `13 * sheet + 5` units outside them, beside the paper's outer edges, so
  that they show), `sheet`, `mouth` (the voice line starts here), `crown`. `num`: `desk_dx` (signed
  world units the desk has moved: add it to the set's `desk_dx`), `shove` (0..3, eased: move the
  rows away by it), `on_desk`, `speak`, `tear` (0..1: the rip, half of it at each of `tear`, 0.16 s
  each), `in_hands` (0 / 1, from 53.67), `halves` (0 on the table .. 1 held up), `tuck` (0..1: into
  the jumper), `sheet` (the scale to draw the paper with: `sheet`, down to 0.4 of it as it is
  tucked away).
- The two walks are longer than a trudge covers in their beats (X1 to X2 is 1160 units in twelve
  steps): the stride is the walk's at mood 0.5 to 0.7, the body is kept a trudge (head, back, arms).
- Framing: zoom 1 (head 118 px) carries all of it; the speak and the table want no less than 90 px.

### s03(t, x0=X2, x1=X3, h=380, **times) -> Act   (58.60 to 91.77)

| cue (`S03_T`) | default | |
|---|---|---|
| `entry` | 58.60 | a start as the band comes in: shoulders, eyes, hair, the hands fly off its chest, a foot is picked up and set down (no travel) |
| `turn` | 58.86 | turns its back on us (0.6 s) |
| `walk` | 59.515 | trudges away IN PLACE, a step a beat, in back view: the pull-back and the falling pressure make the distance. Draw it at `(x0, FLOOR)` at full height |
| `hits` | `story.HITS_1` | stops in its stride on the first; each hit presses it lower than the last (knees, back, head between the shoulders; the arms jerk out, the body rocks, the hair flies), and it comes only part of the way up again: the top of its head is 51, 75, 92 units lower at the three hits (of 380) and stays 30, 58, 69 lower after them; then it stands bowed |
| `arrive` | 74.6 | the amber line is at its feet: the head turns to it, the child turns round to the right, opened toward us (74.94, 0.52 s), and looks down at the line |
| `lift` | 75.49 | the head lift, 1.2 s: a small dip, a slow rise that goes about 7 percent too far and settles, a blink at 40 percent, the hair last |
| `spark` | 76.67 | a spark of attention: eyes, brows, a breath of a lean toward the friend; then it settles, ready to go |
| `go` | 79.015 | walks right along the line to `x1`, 15 steps of a beat at mood 0.38 (arrives 90.27), its eyes on the far friend for the first steps, the head sinking a little as the room comes back |
| `phone` | 91.0 | on the rug: the eyes go down to the phone as its screen shows. Hand-off B3 from 91.48 |

- `Act.a` is the pressure of its line: 1, minus 0.08 with every step away and 0.035 at each hit
  (0.32 at the lowest), held, back to 1 over the head lift.
- `pts`: `crown`, `mouth`, `feet` (`(x, FLOOR)`: where the amber line arrives), `eye` (a point 600
  units to its right at head height: where it looks along the line). `num`: `away` (body units walked
  into the depth, 0..1.7), `low` (0..1.2: how far down the hits have pressed it), `rim` (0..1 from
  `arrive`: `rim=(C.AMBER, 1, num["rim"])`), `lift` (0..1 through the head lift), `spark`, `walk`
  (0..1 along the walk home).
- Framing: the start, the turn and the first steps at mid size (head 100 px); the hits and the
  noticing are written to read in the wide frame (head 24 px: the 78 px figure drops by 10, 15 and
  19 px and ends 14 px shorter); the head lift reads there as a silhouette (bowed to upright, the
  tufts standing up) and wants a head of 90 px to show the blink and the spark: the camera should
  be on its way in by 75.5.

### s04(t, x0=X3, x1=X4, phone=None, sides=(-1, 1, -1), h=380, **times) -> Act   (91.77 to 115.77)

| cue (`S04_T`) | default | |
|---|---|---|
| `sit` | 91.80 | sits down on the floor where it stands (0.72 s): the feet stay at `x0`, its hips end 80 units to the left (against the sofa) |
| `pick` | 92.72 | bends right over, the near hand goes down to the phone and has it; sits back, legs out, the phone held up before its face, the other hand on it |
| `thumb` | (93.05, 93.26, 94.75, 95.98) | the far hand strokes the screen: a quick stroke, a slow return, the eyes going down with the rows; between them the face empties and the head sinks |
| `down` | 96.02 | nothing has come: it looks a moment longer, lays the phone face down beside it |
| `shawl` | (96.18, 98.8) | the scribble comes down on it: the crown gives (`press`), the spine curls; it draws up its knees and puts its forehead on them (done 99.0) |
| `rise` | (101.9, 103.4) | gets up, heavy: weight forward over the feet, hands to the floor, then the knees, the head last |
| `bumps` | (104.07, 105.23, 106.57) | on the corridor line: before each it tries a step forward (60 units); it is shouldered: thrown back, a stagger (`sides`: -1 the far shoulder is hit and it twists away from us, +1 the near one and it twists open), a step back (40 units) and off the line toward us (`y` + 15), and back on |
| `plant` | 108.25 | gathers itself; the near foot goes back, the far foot is set down hard on the beat: feet apart, braced, head level, at `x1` |
| `cross` | (109.6, 113.5) | crossed out: a wince, the feet stay |
| `redraw` | ((111.0, 112.0), (114.3, 115.0)) | turns to us, looks at its near arm, takes the stub in the far hand and goes over the arm from below the shoulder to the wrist; the second time down its near side, the arm held away. Hand-off B4 from 115.5 |

- `phone`: world point where the phone lies (default `story.PHONE` in the evening room, (3750, 800)).
  It lies 58 units in front of the ground line: out of the reach of anyone on that line. The child
  bends down as far as it can; `pts["phone"]` travels the last 30 to 40 units from the rug into the
  hand over 0.15 s (the pick-up).
- `grab` pins the far hand to the stub while it draws.
- `pts`: `phone` (where the phone is: on the rug, then the hand that holds it: `phone_held(F,
  pts["phone"], -1.05, lit=num["lit"], scroll=2.4 * num["stroke"])` while `num["held"]` is 1, then where
  it was laid), `thumb` (the stroking hand), `neck`, `pel`, `crown` (for `gloom.shawl`: or take
  them from figure()'s return), `arm` and `side` (polylines `(5, 2)` / `(7, 2)` of the two stretches of
  its outline, from `plant` on: aim `cross_out` at them and give them to `things.restroke(F, arm,
  num["redraw1"])`), `tip` (the stub's drawing end, while `num["stub"]` > 0: `chalk_stub(F, pts["tip"],
  num["ang"], a=num["stub"])`).
- `num`: `held` (0 / 1), `lit` (0..1: the screen's light), `stroke` (0..4, eased: the strokes so
  far), `down` (0..1: laid face down), `press`, `hug` (0..1 knees drawn up), `off` (0..1 off the
  line), `bump` (0..1 at each shouldering: a camera or a walker can answer it), `stub` (0..1: it has
  the stub), `redraw1`, `redraw2` (0..1), `ang` (the stub's angle: `STUB_ANG`, -0.75).
- Travel: `x1 - x0` is covered by the three tries (each forward step is `(x1 - x0) / 3 + 40` units).
- Framing: the phone and the shawl in the storyboard's push-in (head 150 to 180 px: the face's light
  and the emptying eyes are the beat); the corridor at zoom 1.1 (head 130 px); the stub wants 110 px
  or more (the tip on the arm is small).

### s05(t, x0=X4, x1=X5, backs=None, moth=None, hands=None, sheet=0.5, h=380, **times) -> Act   (115.77 to 138.20)

| cue (`S05_T`) | default | |
|---|---|---|
| `ring` | 115.77 | planted, it watches the backs come (the stance softens) |
| `closer` | 117.1 | a small step closer; leans to look in, on its toes, a hand half raised |
| `whispers` | (118.40, 118.76, 119.14) | its eyes go after each; the hand sinks, it gives up |
| `speak` | 119.79 | a breath, the mouth, two small tries |
| `moth` | 121.0 | its eyes and then its head follow `moth`; the near hand goes out after it (121.3 to 122.5), forward and a little up: never in front of its own face |
| `effort` | 122.19 | the hand sinks; it looks at the ring again |
| `touch` | (123.26, 124.76) | a small step and its hand is on the nearest back ON the time; the back goes, the hand stays in the air; a longer step to the next: gone too; the arm drops, the head goes down |
| `out` | 126.265 | walks on to `x1`, five steps (arrives 130.02), turns to face us (0.55 s), gives a hand to each side (up and out: 130.7 to 131.4), looks up at the one, then the other |
| `part` | (131.85, 134.0) | its arms are pulled straight, its feet go apart, it hangs between the two lines with all its weight, trembling |
| `slip` | (134.51, 134.77) | the left line slips: that arm falls in, the body is pulled over to the right; the right one slips: it sits down hard (a fall of 0.4 s), eyes shut, the arms left out after them, low; the eyes open and go after the one, then the other (135.25 to 135.5); the arms sink |
| `gather` | 135.6 | the two halves have fallen out of its jumper (135.07) and lie before its feet: a hand goes down for each (135.56 to 135.96), it lifts them, holds them together on its knees and looks (136.3 to 136.6), takes them to its chest: they are gone into the jumper by 137.0 |
| `stand` | 137.0 | gets up, a hand still on its chest; the hand sinks. Hand-off B5 from 137.95 |

- `backs`: `((x, y), (x, y))`, the world points on the two backs it touches (`R.who[j]["back"]` of the
  two nearest of `people.ring_of_backs`; default those of a ring at `x0 + 405`: (x0 + 175, 526) and
  (x0 + 257, 555)). It stands 120 units short of each. `moth`: `(x, y)`, where the moth is now
  (`things.moth_path(F.t, ...)[:2]`; default the lamp at (x0 + 405, 260)). `hands`: `((xl, yl), (xr,
  yr))` to pin its hands to given points while it holds the two; leave it None and end the family's
  lines in its hands instead (`family_line(x1, hands=(pts["hand_l"], pts["hand_r"]), small=False)`).
  `sheet`: the scale of the two halves (0.5: together they are 75 units wide, as wide as its knees).
- `pts`: `hand` (the near hand: the one that reaches), `hand_l`, `hand_r` (its two hands as seen),
  `half_l`, `half_r` (while `num["halves"]` > 0: the two points `things.family_held` takes, falling,
  lying, lifted, together on its knees, at its chest; the mitts are beside the paper's outer edges:
  `if n["halves"] > 0 and n["tuck"] < 1: family_held(F, pts["half_l"], pts["half_r"], s=n["sheet"],
  a=n["halves"] * (1 - n["tuck"]))`, after the child), `mouth`, `crown`.
- `num`: `speak`, `touch1`, `touch2` (0..1: the hand is on that back), `hold` (0..1: it has given
  its hands), `strain` (0..1), `slip_l`, `slip_r` (0..1 after each), `sit` (0..1), `halves` (0 in
  the jumper; 0..1 over 0.2 s as they fall out; 1 out), `tuck` (0..1: 136.64 to 137.0), `sheet` (the
  scale to draw them with: smaller as they come out and as they go back in).
- Framing: the ring at zoom 0.95 (head 110 px: the eyes on the moth and the hand on the back carry
  it); the family line reads in a full frame (head 100 px); the fall and the halves want the head
  at 110 px or more.

### perform(t, **kw) -> Act

`s01` .. `s05` by their spans (0, 36.27, 58.60, 91.77, 115.77 .. 138.20); `kw` goes to the section
that holds `t`. What `proofs.py` and `check.py` run.

## 3. The rest states of the hand-offs

`hold_B1(t, x=X1, h=380)` .. `hold_B5(t, x=X5, h=380)` -> Act: the child standing in the state of
`story.HANDOFF`, alive, not acting. Both neighbouring scene modules get exactly this from the
sections themselves: every section returns `hold_Bn(t)` from its last move's end to its span's end
and until its first cue (checked: 0.0000 units apart at -0.26, -0.02 and 0 s; movement begins after).

| | time | pose | performance ends | begins |
|---|---|---|---|---|
| `hold_B1` | 36.27 | `STOPPED` at X1, facing right | 35.82 | 36.27 (the first step, on the beat) |
| `hold_B2` | 58.60 | `HUSH` at X2: standing, head down, three-quarter to us, both hands at its chest on what it tucked away. Breath only (no weight shift, no chance blink), one slow blink at 57.1: this is the whole silence from 56.0 | 56.00 | 58.63 |
| `hold_B3` | 91.77 | `ON_RUG` at X3: standing, head a little down, eyes on the phone | 91.48 | 91.80 |
| `hold_B4` | 115.77 | `PLANTED` at X4: feet apart (103 units), braced, head level | 115.50 | 116.07 (a look first; the first step 117.1) |
| `hold_B5` | 138.20 | `STOPPED` at X5, the halves tucked away | 137.95 | (acting_pair's s06) |

`CHILD_HANDOFF = {"B1": (36.27, hold_B1), ...}`. All face right (`face=1`), `y = FLOOR`, pressure 1.
B1, B3, B4, B5 are `alive(pose, t, 3)` with the rig's defaults: a module that takes over (s06 at B5)
must draw exactly that until its first move (`acting_pair.s06(138.20).child` is: 0.0000 apart).
Checked against `story.HANDOFF` (`review/measure.py handoff`): time, x, `face` and the state named
there, for all five. B2: the story's words are "standing, head down"; `HUSH` is that, turned
three-quarter to us with the hands at the chest. B3: standing (the story's B3, which is newer than
the storyboard's prose): it sits down after the hand-off, in s04.

## 4. The tools

Poses in, poses out; body units are the rig's (1 = the figure's height); world points are world.

**Moves.**
- `move(a, b, u, win=W_HEAD, ant=0.07, over=0.07, blink=0, warp=0) -> Pose`: one acted move, u = 0..1
  over the whole of it. `win` says which part leads: `W_HEAD` (eyes 0-0.5, head 0.08-0.66, spine and
  feet 0.16-0.82, hands 0.26-0.94, mouth 0.34-0.86, hair 0.46-1), `W_HAND` (the hand goes right after
  the eyes), `W_BODY` (the weight leads, the head is last), `W_FLAT` (everything together). `ant`: the
  dip the other way before head and spine go; `over`: how far they overshoot; `blink=1`: a blink at
  40 percent; `warp` > 0 a fast start that slows in (a reaction), < 0 a slow start (a tired move, a
  fall). 0.01 ms. (The rig's `act` is `move` with `W_HEAD`.)
- `through(poses, us, u, win=W_FLAT, warp=0) -> Pose`: one move THROUGH breakdown poses (`poses[i]`
  at `us[i]`, `us` from 0 to 1) on a smooth curve that does not stop on the way. 0.03 ms.
- `chain(t, P0, keys) -> Pose`: a sequence on the song's clock. `keys = [(t0, dur, pose, kind), ...]`
  sorted by `t0`: at `t0` a move of `dur` seconds begins toward `pose` from wherever the figure is
  then (also from the middle of the move before). `kind` = `(win, ant, over, blink, warp)`:
  `K_ACT`, `K_BLINK` (with the blink), `K_SOFT` (small, no wind-up), `K_SLOW` (sinking), `K_HAND`,
  `K_BODY`, `K_LAND` (weight coming down: fast, overshoots, settles), `K_HIT` (a jolt), `K_FALL`
  (starts slowly, fastest at the end), `K_EASE`. A fifth entry `((u, pose), ...)` gives breakdowns.
  Before the first key: `P0`. 0.01 ms.
- `head_lift(t, t0, a=STOPPED, b=LOOK_UP, dur=1.2, spark_at=None) -> Pose`: the head lift as one
  choreography from `t0` (dip, slow rise, overshoot, blink, hair last); the spark comes at
  `spark_at` (default: as it settles). For 154.84 and 189.6 give your own `a` and `b`.
- `turn_to(a, b, u, hop=1) -> Pose`: a turn on the spot (the rig's `turn_round`): 0.4 to 0.55 s.
- `small_step(P, u, d, lead="f", lift=0.026) -> (pose, travelled)`: one small planted step: the
  ground point travels `d` body units toward `face` (negative: back); the foot `lead` goes first,
  the other follows; draw at `x + face * h * travelled`. For poses near a profile.

**Reactions** (layers on a pose; `k` = strength, animate it with a fast attack and a slow release):
- `flinch(P, k=1)`: the head ducks between the shoulders, the eyes shut, the hands jerk in, a
  standing figure's knees give. Standing, sitting, lying.
- `startle(P, k=1)`: shoulders up, head up and back, eyes wide, hands off the body, hair flying.
- `stagger(P, k=1, side=1)`: knocked by the shoulder of someone coming the other way: the upper
  body is thrown back, the knees give, the head is left behind, the arms fly out a little. +1 the
  near shoulder (the body twists open toward us), -1 the far one (it twists away: more of its back).
  Move the ground point for the step it forces (`small_step`).
- `react(P, t, times, fn=flinch, k=1, up=0.09, hold=0.08, down=0.55, grow=0, **kw)`: `fn` at each of
  `times` with that envelope (seconds), two frames after the cue; `grow`: each stronger than the
  last by this share. `react(P, F.t, story.HITS_2, flinch, 1.0, grow=0.25)`.

**Eyes and hands on world points** (`x, y`: the figure's ground point; `h`, `face` as given to `figure`):
- `look_at(P, x, y, target, h=380, face=1, k=1, head=0.5) -> Pose`: head and eyes turned to a world
  point. `k` 0..1: the eyes are there at 0.5, the head at 1 (so animating k makes the eyes lead);
  `head`: how much of the way the head goes (0: eyes only). A moving `target` is followed. 0.003 ms.
- `reach_to(P, x, y, point, h=380, face=1, which="f", k=1, lean=1, arc=0.03) -> Pose`: one hand
  ('f' near, 'b' far) to a world point; `k` 0..1 brings it there on a small arc, the spine leaning
  after it when the point is far (`lean` scales that). Beyond reach the arm stretches toward the
  point and stops short: pin with `grab={which: point}` only when it is within reach. 0.07 ms.
- `carry(P, x, y, left, right, h=380, face=1, k=1) -> (pose, grab)`: both hands on two world points
  (left and right as seen); which hand takes which follows the pose's turn. `grab` is for `figure`
  (None while k < 1). 0.13 ms.

**Down and up** (u = 0..1; the timing is yours: ease u, about the seconds given):
- `sit_down(u, kind="floor", a=None, b=None)`: from standing (`a`, default `STOPPED`) onto the
  floor, legs folded (`b`, default `FLOOR_SIT`), about 0.75 to 1 s; the pelvis drops back first, the
  body lands and settles. THE GROUND POINT STAYS UNDER THE FEET (the hips end 0.21 h behind it).
  `kind="edge"`: onto the front edge of the sofa (`EDGE_SIT`): the ground point is where the child
  stood, the seat's edge 0.36 h behind it.
- `stand_up(u, kind="floor", a=None, b=None)`: from the floor (`a`, default `FLOOR_HUG`: hugging its
  knees) to standing (`b`, default `STOPPED`), 1.4 s or more; `kind="edge"`: off the sofa's edge.
- `sit_up(u)`, `curl_up(u)`: on the sofa, ground point `(story.CURL_X, story.SOFA_SEAT_Y)`: the
  rig's `sit_up_pose` (CURL to `SIT_B`, about 2 s, slow to start) and `curl_up_pose` (from the seat's
  edge to `CURL_EASE`, about 2.5 s), sampled once (0.004 ms a call instead of 0.5).
- Poses: `FLOOR_SIT`, `FLOOR_HUG` (the rig's `SIT_FLOOR`, `SIT_HUG` with the ground point under the
  feet), `EDGE_SIT`, `SIT_B` (= the rig's `SIT_CURL`), `HUSH`, `ON_RUG`, `PLANTED`.

`beat_at(k)`: the time of beat k (0.265 + 0.75 k). (`acting_child.beat_after(t)`: the first beat at or after t.)

```python
# a scene's own small performance with the tools: the child hears something behind it (say 30.0 s)
keys = ((30.0, 0.5, STOPPED.but(hturn=-0.3, eye=0.9, lid=0.6), K_ACT), (31.2, 0.8, STOPPED, K_SLOW))
P = react(chain(F.t, STOPPED, keys), F.t, (30.0,), startle, 0.5)
P = look_at(P, x, FLOOR, (x - 400, 500), k=F.ramp(30.1, 30.5) * (1 - F.ramp(31.2, 31.8)), head=0.3)
figure(F, x, FLOOR, 380, alive(P, F.t, 3, blink=0), "child", seed=3)
```

## 5. Numbers

Cost of one evaluation (ms, one core, the machine shared; `review/measure.py cost`, every 0.05 s of each span):

| | mean | 95 percent under | worst |
|---|---|---|---|
| s01 | 0.21 | 0.31 | 0.34 |
| s02 | 0.27 | 0.39 | 0.42 |
| s03 | 0.22 | 0.26 | 0.30 |
| s04 | 0.22 | 0.34 | 0.38 |
| s05 | 0.23 | 0.33 | 0.37 |

The budget is 0.3: the means are under it, the moments with a pinned or reaching hand are over it
(the halves at the table are the dearest: two hands on world points). Of this the rig's
`pose_joints` (for `Act.J` and the points) is 0.15; a hand brought to a world point costs one more
`solve` (0.06 to 0.09). A rest state: 0.14. The tools: `move` 0.008, `through` 0.02, `chain` 0.01,
`head_lift` 0.009, `turn_to` 0.012, `small_step`, `flinch`, `startle`, `stagger`, `react`, `look_at`
0.002 to 0.003, `reach_to` 0.07, `carry` 0.13, `sit_down` / `stand_up` 0.023, `sit_up` / `curl_up` 0.004.

`check.py pops`: no frame-to-frame step of a joint more than 2.2 times its neighbours except the
ones that are meant: the jolt of each of the three hits (64.8, 66.3, 67.8: 26 to 35 units in a
frame), the thumb strokes (94.75, 95.98), one frame of the lying flinch at 21.28 (13 units: the
crown of a turning head) and the frame at 46.75 where the near and far legs change names after the
turn back (the same picture). `check.py feet`: the rig's planted walks; the stepping feet of the
shoves, the staggers and the stance; feet that slide on purpose: the legs stretched out with the
phone (92.8 to 93.05) and drawn up under the shawl (97.7 to 98.5).

Flicker of the held child (the child and the ground line, static camera; `proofs.py flick`,
`flicker.txt`; the same from `review/measure.py flicker`): the rest states 0.10 to 0.11 levels and
0.35 to 0.37 percent on a boil step, 0.007 to 0.012 inside a pair (the breath); the silence 56.2 to
58.5: 0.000 on every boil step, 0.012 inside a pair (the breath, which acts on true time), 0.028 at
the slow blink; the pose `HUSH` drawn without `alive`: exactly 0 in both; hugging its knees on the
floor (99 to 101): 0.10 / 0.34 percent, 0.007 inside a pair.

Determinism: six frames of the five sections, staged with the real kit, hashed in two separate
processes: identical (`review/measure.py hash`). Extreme cameras (`review/extreme_cameras.jpg`):
every section at zoom 0.26 and 1.6, the child cut by the left and the right edge, standing in the
lyric band, and wholly off screen: no error, nothing odd; at zoom 0.26 (a 99 px figure) the body
acting still reads, faces and hands do not (see the framing lines).

## 6. Open points

- **The phone is out of reach.** `story.PHONE` lies 58 units in front of the ground line; a hand of a
  child on that line gets about 20 below it. s04 bends the child right over and lets the phone come
  the last 30 to 40 units to the hand. The coda has the same problem from the sofa. A phone at about
  `FLOOR + 20` would be picked up for real.
- **The balloon is out of reach too** (s01, 31.58): at the default place its middle is 220 units
  from the sitting child's far shoulder (810, 517) and an arm is 130 long: the hand would only touch
  its lower edge. So the sleeve goes down through its tail and the scene wipes the balloon. A balloon
  whose middle is within 130 units of that shoulder could be wiped for real.
- **The hand that draws the hero** is the far hand lifted beside the chin: a small movement (20 to
  45 units), at the storyboard's push-in a clear gesture, in the wide room nearly nothing. Lying
  on its side with its head on the armrest the child has no hand that can point at the wall.
- **The first walks of s02 are not a trudge's stride** (see s02): the journey is binding, so the
  steps are long; shorter ways (`x_stop`, a nearer `x1`) give a truer trudge.
- **The classroom**: no staging of the kit's classroom lets a child that travels right push its desk
  toward the rows without turning round; `push=-1` turns it round (two quick turns, 0.42 and 0.36 s).
  The shoves themselves do not care. In the shoves the feet slide a little (5 to 25 units a frame,
  lifted only slightly).
- **s03 in back view** shows no face for 15 s (59.5 to 75): the hits are carried by the height of
  the figure and its arms alone. The noticing of the line (74.6) is small from behind; the amber
  rim does the telling.
- **The staggers** are a crumple, a step back off the line and a step back on: a walker has no
  contact pose, so nothing answers them; `num["bump"]` is there for a camera jolt or a walker's own
  reaction. Whether the child reads as shouldered depends on a walker passing at that frame
  (`people.walkers(hits=S04_T["bumps"])`).
- **Arms over the face**: with `over` (arms drawn on top) a far hand that crosses the body can pass
  before the chin: the hug under the shawl, the stub at the shoulder, and for about eight frames
  (137.05 to 137.3) the hands at the chest as it gets up, while its head is still down over its
  knees. Kept where it reads as hiding the face; the stub's stroke starts below the shoulder to
  stay clear of it.
- **The halves in s05** are small (75 units for the pair, the size of its knees): the drawing on
  them reads from a head of 110 px. They are rigid sheets: going into the jumper they shrink and
  fade over 0.36 s; there is no fold.
- **The hero and the cloud**: at the storyboard's sizes the cloud hangs where `things` puts the
  hero (x 863 to 1019, y 254 to 425); the proofs draw the hero over the cloud. A scene must settle it.
- The sofa moves are the rig's (`sit_up_pose`, `slide_off_pose`, `curl_up_pose`), sampled at import:
  a change of the rig's lying poses changes them with it; the lying poses of s01 (waking, clinging,
  the hanging and the drawing hand, the lifted face) are small changes to the rig's `CURL` and
  `CLING`, written as they are seen (`aim_hand(..., seen=True)`), and should be looked at again
  whenever those change. Going from the clinging pose back into the tight curl (21.4 to 22.0) is
  a plain blend of two lying poses, the head sliding back along the armrest.
- Nobody has watched the clips as video: motion was judged on strips of consecutive frames at 100
  percent, on the pop and foot numbers, and on the sheets.
