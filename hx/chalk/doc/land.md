# hx.chalk.land: the plain of the choruses and what towers over it

When the band enters (58.60) the room is gone: a bare, endless plain under the scribble's ceiling,
the child tiny on the one ground line. On the three hits of each chorus three groups draw themselves
on over it: the voices, the turned backs, the house that came apart. In the last chorus they come
back knee-high and are answered.

    from hx.chalk.land import *        # every name below

Proofs and the script that makes them: `hx/_review/v4_kit/land/` (`proofs.py`, `00_overview.jpg`);
a second, independent set of test scenes written from this page alone: `hx/_review/v4_kit/land/review/`.

**Conventions.** World coordinates and sizes through `F.cam`; y runs down; the ground is world y 742
(`hx.story.FLOOR`). Nothing here draws a floor line: draw `ground_line(F)` yourself. Night skin and
cold chalks only (no amber: that is the friend's); the knee-high pieces also have a `day` look.
Nothing keeps state. Costs are ms at 1080p on one core (`10_cost.txt`).

**The story's numbers** (`hx/story.py`, binding). Chorus 1 happens at `X2` (2200), chorus 2 at `X5`
(4300). The wide zoom is `WIDE_ZOOM` (0.205: the child 78 px tall, 9366 world units across); the far
friend of chorus 1 stands at `FRIEND_FAR_1` (`X2 + 4900`). `tower_layout(X2)` gives exactly that
camera, zoom and friend. The hits: `HITS_1`, `HITS_2`, `HITS_3`.

**Clocks.** Everything here is still unless you move it. What you move runs on `F.t`: the hits
(`hit(t)`), the un-draw (`off(t)`), pressures (`a`, `thin`), `reach`, `split`, `full`, `born`. The
lines boil on twos by themselves. One thing is merely alive and runs on `F.tb`: the rings of rain
in the puddles (they stand still in the two silences, like the rain). In a silence the plain and the
groups do not change by one level in one pixel (measured).

**Order of drawing** (back to front): `plain` .. (weather's mist, back rain) .. `ground_line` ..
`footsteps` .. the groups (`T.draw(F)`, which ends with `dark_above`) .. the amber line, shadows,
glows .. figures .. the scribble's ceiling .. front rain.

**Flicker** (still wide frame, a boil step / inside a pair; `09_flicker.txt`): plain alone 0.02
levels, 0.10 % / 0.000; plain at zoom 1 with the rain rings 0.10, 0.37 % / 0.000; chorus 1 complete
(kit only) 0.20, 0.82 % / 0.000; chorus 2 0.33, 1.31 % / 0.000; chorus 1 with the stand-in ceiling
and rain 0.78, 2.41 % / 0.006. Targets 1.2 levels, 6 %, about zero.

---

## 1. The plain

### `plain(F, vx=2200, a=1.0, haze=1.0, wet=1.0, far=1.0, rain=1.0, seed=31, reach=None, end=None)`
The ground under the line, for whatever the camera shows (it has no edges; any x, any zoom): a rubbed
ground tone and a mist band along the horizon (both fixed to the horizon on screen, so they neither
swim nor thin out in the pull-back), a few far low shapes in the mist (a line of poles and their
wire going off, a broken fence, small roofs, an unlit street lamp: camera depth 0.3, about one per
frame, dim), furrows running to the vanishing point `(vx, 742)`, puddles with a pale far edge and
rings of rain, stones, tufts.

Every mark is fixed in the world and sized by its depth below the line (a mark twice as far down is
twice as large), so the picture is the same kind of picture at zoom 1.6, 1.0 and 0.205 and rigid in
between; marks that become too small or too close to their neighbours lose pressure and go (nothing
pops: the pressure is continuous in the zoom).

- `vx`: world x the furrows run to (default `story.X2`). Keep it FIXED for a whole scene (the x where
  the child stops in the chorus is the natural choice: every line of the ground then leads to the
  child; `story.X5` in chorus 2 and the bridge). Far from it (the child walking on along the amber
  line) the furrows lie flatter and thin out; that is right.
- `a`: pressure of everything; fade it over 6 frames or more (`plain(F, a=1 - w)` while the room
  comes back, or to change over to the hills' own ground).
- `haze` 0..1: the mist band (170 px above the line on screen at any zoom). Give 0 to 0.4 when you
  draw weather's `mist(F)`, which is the one a figure can walk into.
- `wet` 0..1: the puddles (0: a dry plain; fade it out after the rain has stopped, about 87 s).
  `rain` 0..1: the rings in them (follow the rain's amount).
- `far` 0..1: the far low shapes. They are a far layer: in a pull-back they shrink much less than the
  child, and a row of small roofs may come to stand beside it (give `far=0` if a framing dislikes that).
- `reach=(x0, radius)`: only what lies within `radius` world units of world x0 is there yet: the plain
  spreading out from the child as the ground line shoots out at 58.60. `None`: all of it.
- `end=x`: the marks on the ground stop at world x (soft, 260 units): the foot of the first hill
  (`hills.FLAT_TO`, 4700). Tone and mist go on. Only once the hill is drawn (from 175): chorus 2
  stands 400 units left of it and its wide frame shows flat land far beyond.
- Cost: 10 to 11 ms at zoom 1.6, 1.0, 0.5, 0.26 and 0.205 (budget 15).

```python
r = 4000 * ease_out(F.seg(58.60, 59.60), 2.2)                 # the horizon shoots out
plain(F, vx=story.X2, reach=(child_x, r))
ground_line(F, span=(child_x - 1.25 * r, child_x + 1.25 * r))
```

### `puddles(F, seed=31) -> array (n, 6)`
The puddles of `plain(F, seed=seed)` that are on screen: rows `x, y, rx, ry, a, key` in world units
(`a` 0..1: how visible; `key`: a number that is the puddle's own). For a light of your own lying in
them (an amber glint under the friend's line: `wet_reflection` at each). 0.3 ms.

### `footsteps(F, xs, born=None, y=None, s=1.3, a=0.9, life=16.0, face=None, col=(0.50, 0.58, 0.76), rest=0.25)`
The way already walked: one mark per step, left and right in turn, the toes turned out a little,
just under the ground line. Close by (the mark over about 14 px long on screen) it is a print pressed
into the wet ground: a dark sole and heel with a pale rim, like the puddles. Far away it is a pale
dash and the trail a dotted line.
- `xs`: world x of every step in the order walked. `born`: the time each mark appeared (same length;
  `None`: all old). A mark comes up in 0.25 s and loses pressure with its age: after `life` seconds
  about `rest` of it is left (it never quite goes: the trail stays). The fading runs on `F.t`: marks
  under about 30 s old still change in a silence (in the film none are that young there).
- `y`: world y of the trail (default `742 + 14 s`; in a wide frame the default trail keeps 7 px clear
  of the line on screen, so that it is not lost in it: give `y` yourself to switch that off).
  `s`: size (1 = the child's shoe, 36 units; in the wide frame the marks are dashes of 6 by 2.5 px,
  no smaller). `face`: +1 / -1, the way the toes point.
- Pressure changes in 32 steps, so no mark jumps as it fades.
- Animate: nothing; it follows `F.t` through `born`. 0.25 ms for 9 marks in the wide frame, 0.55 ms for
  9 fresh prints at zoom 0.9.

### `footfalls(x0, x1, t0, t1, every=0.75) -> (xs, born)`
The marks of a walk from world x0 (left at t0) to x1 (reached at t1), a step every `every` seconds:
feed it the `W.t0`, `W.t1` of a `walk_to`. The place where the walker stands at the end has no mark yet.

```python
W = walk_to(F.t, x0, x1, 380, start=58.76)
footsteps(F, *footfalls(x0, x1, W.t0, W.t1))
```

`footprints(F, x0, x1, y=None, n=12, a=0.6, col, s=1.3)` is the prototype's call, kept (n marks,
fading toward x0).

---

## 2. The wide frame

### `tower_layout(child_x=2200, level=1, zoom=None) -> TowerLayout`
The composition of the wide chorus frame for a child standing at world x `child_x`. Give it the
FIXED x where the child stops (`story.X2`, `story.X5`: the groups are cached by it).
`level` 1: the first chorus; 2: the second (bigger, nearer, more of them, pressed harder).
`zoom`: default `story.WIDE_ZOOM` (0.205). The layout is laid out in screen px, so another zoom gives
the same picture with a larger or smaller child (0.26: the child 99 px).

The wide camera `L.cam` shows 9366 world units: the child at screen (685, 748), 78 px tall; the far
friend at 88 percent of the width (screen x 1690), 60 px tall; the ground line at y 748; nothing but
ground under y 864 (the lyric band). The backs fill the left quarter (the nearest cropped by the left
edge, the far ones behind the horizon in its mist), the voices hang over the child with their tails
aimed at its head, the house stands between the child and the friend; one far balloon hangs at the
right edge, high above the friend, and the right quarter is clear below it down to the ground for
the amber point and its line.

| field | |
|---|---|
| `L.cam` | the wide camera: `F.cam = Cam.ease(close, L.cam, F.seg(60.27, 62.47))` |
| `L.child` | `(child_x, 742)` |
| `L.target` | where the tails aim: the child's head, `(child_x + 8, 742 - 327)`. You may set another point BEFORE building the groups (a sitting child); a new target is a new build (3 ms) |
| `L.friend`, `L.friend_h` | ground point and world height (293: 60 px) of the far friend: 4900 units right of the child at the default zoom (`story.FRIEND_FAR_1` for `child_x = story.X2`) |
| `L.lid_y` | world y where the underside of the scribble's ceiling should hang: screen y 235, which is where gloom's `lid_numbers(L.cam)` hangs it. The heads and shoulders of the near backs, the ridge of the roof and the top of the far balloon are lost in it; the rows of the big balloon begin at about screen y 390 |
| `L.free` | world rectangle (l, t, r, b) of the lyric band in the wide frame |
| `L.backs`, `L.voices`, `L.house` | the members as dicts (x, y, sizes, depth, kind, seed; a back also its `build`), in the subject's plane as `L.cam` sees them |
| `L.level`, `L.zoom` | |

The ceiling over it (gloom's; its doc has `lid_numbers` and the opening of the cloud into the lid):

```python
s = 1 / F.cam.zoom                                    # afterwards: the lid follows the camera
ceiling(F, ax=child_x, s=s, y=F.cam.view()[1] + 235 * s, depth=365 * s, sag=(child_x, 50 * s, 600 * s))
```

### `towers(L, press=None) -> Towers`
The three groups of the layout, built (cached: 0.15 ms a frame; the first build of a process 15 ms).
`press`: how hard they are drawn, default 1.0 at level 1 and 1.25 at level 2 (wider, brighter lines).

- `T.voices`, `T.backs`, `T.house`: the three `TowerGroup`s. `T.layout`.
- `T.hit(times, order=("voices", "backs", "house"), dur=0.45, lead=0.066)`: each group lands on its hit.
- `T.draw(F, a=1.0, thin=1.0, tint=None, tint_w=0.0, dark=1.0)`: paints all layers of the three
  far to near (house, backs, voices over them), then `dark_above(F, dark)`. `a`, `thin`: a number,
  or a dict by group name (`{"voices": 0.5}`; missing names are 1).
- `T.off(t0, dur=1.6) -> t_end`: all three are taken back, the voices first.
- Cost of the whole wide frame (plain, footsteps, three groups built, timed and drawn, dark_above):
  43 ms at level 1, 48 ms at level 2 (budget 60; measured on a shared machine).

```python
L = tower_layout(story.X2)                            # module level or per frame: cheap
def draw(F):
    F.cam = Cam.ease(Cam(story.X2, 520, 0.9), L.cam, F.seg(60.27, 62.47))     # from the camera of hand-off B2
    plain(F, vx=story.X2)
    ground_line(F)
    T = towers(L)                                     # build it afresh every frame
    T.house = tower_house(L, split=house_crack(F.t, story.HITS_1[2], L.house["split"]))   # it comes apart with its hit
    T.hit(story.HITS_1)
    k = F.ramp(75.5, 77.5)                            # they lose their pressure
    T.draw(F, a=1 - 0.55 * k, thin=1 - 0.4 * k)
    ...                                               # friend at L.friend, amber line, child, the ceiling, rain
```

### `tower_voices(L, press=None, depth=1.0)`, `tower_backs(L, ...)`, `tower_house(L, press=None, depth=1.0, split=None) -> TowerGroup`
One group alone. `depth` scales every member's camera depth (under 1: the whole group further away).
`tower_house(split=...)`: the lean of the halves in radians (default 0.085 at level 1, 0.12 at
level 2). It may be animated on `F.t`; every new value is a new build (2.9 ms; a value that stays
is cached).

### `house_crack(t, t_hit, split=0.085, dur=0.40) -> float`
The lean of the halves as a number of the song's time: 0 until just after the hit, open to `split`
within `dur` seconds, a small shudder as it stops. With it the house draws itself on whole and
comes apart WITH its hit (`03_hit_house_cracking_open_8.jpg`; recommended, see the example above).

Sizes in world units at the default zoom (multiply by 0.205 for screen px):

| group | level 1 | level 2 | draw, ms (1 / 2) | anchors |
|---|---|---|---|---|
| voices | 4 balloons (round 2260 wide, a spiky shout, a box at the right edge, a small far one), depths 1.0 to 0.56 | 5, bigger, and a second shout right at the child's head | 9.3 / 11.8 | `anchors[name]` = x, y, rx, ry, depth |
| backs | 5 backs 3260 to 1660 units tall, depths 1.0 to 0.42, each its own build: a long belted coat, a broad short jacket with a satchel, a slight flared coat with a scarf, two far ones | 5, three of them near giants: the nearest 4680 tall (cut off by the top and the left of the frame), one standing astride right over the child | 11.6 / 14.0 | `anchors[name]` = x, y, h, depth, head |
| house | 1640 wide, 2460 tall, split 0.085 | 1815 wide, 2720 tall, split 0.12 | 6.2 / 6.5 | x, y, w, h, split, depth, and the seam (see `house_seam`) |

### `TowerGroup`
Sketch layers at camera depths, painted far to near. A member of depth under 1 is drawn through
`F.depth` (it is composed so that it sits exactly as laid out when the camera is `L.cam`; under any
other camera it parallaxes: slower than the subject's plane, as a far thing should). Far backs
stand BEHIND the horizon: they are cut at the ground line and stand in a little mist.

- `G.hit(t0, dur=0.45, lead=0.066)`: it draws itself on with the hit at `t0`. The first stroke starts
  `lead` seconds before the hit, so that the big contour is half there on the hit frame and closed
  three to four frames later; the dressing follows to `t0 + dur`, the colouring-in trails to
  `t0 + 1.2 dur`. The nearest member leads; in each member the coat / balloon / roof and walls come
  first. On landing the lines are pressed 20 percent wider and relax in 0.2 s (`G.punch = 0.2`; 0 for none).
- `G.off(t0, dur=1.2) -> t_end`: taken back: colouring-in first, the big contour last, each line
  from both its ends, leaving a rubbed ghost that fades.
- `G.draw(F, d=None, a=1.0, thin=1.0, tint=None, tint_w=0.0, depths=None)`: paint at `F.t`.
  `a` pressure, `thin` line-width factor (lost pressure: `a=0.45, thin=0.6`). `d`: progress 0..1 of
  the whole draw-on instead of times. `depths=(lo, hi)`: only those layers (to interleave groups).
  Call it with `F.cam` = the scene's camera (not inside `F.place` / `F.depth`).
- `G.sub("back1", "voice0.row")`, `G["house.l.tear"]`, `G.names()`, `G.items()`: the named parts over
  all layers (the same objects: `G.sub("voice0.cross").set_off(t0, t1)` sticks).
- `G.anchors`: world points in the subject's plane as `L.cam` sees them. `G.members`: name prefixes,
  nearest first. `G.layers`: `[[Sketch, depth, mist], ...]`.
- `G.flat(cam=None) -> Sketch`: one Sketch in the subject's plane that looks like the group seen
  through `cam` (default `L.cam`), without the mist: for a morph. `sets.plain_to_room(w,
  house=T.house.flat(F.cam), backs=T.backs.flat(F.cam))` runs with it (it takes the longest strokes);
  draw the group itself until the change begins.
- `G.schedule(t0, dur) -> {id(item): (t_start, t_end)}`: the times `hit` gives, for your own use.

Part names: `voiceN.balloon` (+ `.fill`), `.row0..`, `.cross0..`; `backN.coat` (+ `.fill`, `.hatch`),
`.leg_l .leg_r` (+ `.fill`), `.arm_l .arm_r` (+ `.fill`), `.collar | .scarf`, `.head` (+ `.fill`),
`.hair`, `.vent .seam .crease_l .crease_r`, `.belt .button_l .button_r` | `.satchel .flap .strap_l
.strap_r` | `.scarf_tail`; `house.l.wall .l.roof .l.eave .l.tear .l.base` (+ `.wall.fill .roof.fill
.wall.hatch`), `.l.tile0-2 .l.attic .l.door` (+ `.fill`) `.l.knob .l.chimney`, the same for `r` with
`.r.window` (+ `.fill`) `.r.bars .r.sill` in place of door, knob and chimney.

### `dark_above(F, a=1.0, reach=500)`
The dark the towering things rise into: the top of the frame darkened, fading out `reach` px down
the screen. After the groups, before the ceiling (`Towers.draw` does it). 2.4 ms.

### A small camera jolt on a hit (the scene's business; the layers answer it with parallax)
```python
j = sum(math.exp(-(F.t - h) / 0.09) * math.cos((F.t - h) * 38) for h in HITS_1 if 0 <= F.t - h < 0.6)
c = F.cam
F.cam = Cam(c.cx, c.cy + 26 * j / c.zoom, c.zoom * (1 + 0.014 * j))
```

---

## 3. The single pieces (improved props; a Sketch each)

Giant or small: line width, wobble and colouring-in scale with the size. A piece larger than 520
units carries the slow wobble of a whole arm in its points (the kit's own wobble would be invisible
on a line 2000 units long); `S.place` and `Sketch.draw` work as for any prop.

### `back_figure(x, y, h, seed=700, col=C.CHALK_FAR, a=1.0, lw=None, fill=(0.16, 0.19, 0.30), lean=0.0, tilt=0.0, name="back", kit="belt", detail=2, sink=0.0, loom=0.0, knock=C.KNOCK, girth=1.0, hem=0.375, stance=0.0, flare=0.0)`
A turned back standing on (x, y), h tall: long coat, elbows out and hands gone into the pockets,
legs like pillars, the back of a head. No face.
`lw`: line width (default h / 125, at least 2.8). `lean`: dx per height. `tilt` -1..1: one shoulder
lower, its elbow further out, the head to one side. `kit`: `"belt"`, `"satchel"`, `"scarf"`,
`"plain"`. `detail` 2 / 1 / 0.
`sink`: the legs run on below the ground by sink * h, no shoes (a far figure behind the horizon).
`loom` 0..1: seen from far below, wide at the feet and narrowing to a small head (the giants use 0.5).
`fill`: tone of the coat; `knock`: what is rubbed out behind it (None: nothing).
The build, so that two backs are two people: `girth` 0.85 slight .. 1.2 broad (shoulders, coat,
legs); `hem` where the coat ends as a part of the height (0.30 a long coat .. 0.43 a short jacket);
`stance` -1..1: the weight on one leg, the other set out to that side; `flare` 0..0.2: the coat
widens toward its hem.

### `voice(x, y, rx, ry, tail, seed=800, col=C.CHALK_FAR, a=1.0, lw=None, lines=4, name="voice", style="round", cross="strike", fill=(0.17, 0.21, 0.34), full=1.0, knock=C.KNOCK)`
A speech balloon centred (x, y), radii rx, ry, full of rows of scribble that have been crossed out
(zigzag stands for writing: never letters), its tail a curved horn aimed at the world point `tail`.
`style`: `"round"`, `"box"`, `"spiky"` (a shout). `cross`: `"strike"` (a hard line through every row),
`"scribble"`, `"x"`, `"slash"`. `full` 1..0: the rows and the crossing-out are taken back (empty at 0).

### `house(x, y, w=300, seed=600, col=C.CHALK_DIM, split=0.0, a=1.0, lw=None, fill=None, roof=None, name="house", wall=0.88, pitch=0.62, detail=2, knock=C.KNOCK)`
The child's drawing of a house, x = its middle on the ground, `(wall + pitch) * w` tall, torn down the
middle. `split`: each half leans outward by that many radians about its outer bottom corner and
moves aside by `0.42 * split * w` (the inner corners lift off the ground); at 0 the halves stand
together, the tear still showing. `fill` / `roof`: tones of walls / roof (None: outline only).
The left half has the door and the chimney, the right one the window; a round attic window is torn
in two. It draws no floor line (the underside of a lifted half, `l.base` / `r.base`, fades to
nothing as split goes to 0).

### `house_seam(x, y, w=300, wall=0.88, pitch=0.62, split=0.0) -> dict`
Where the halves meet or gape: world points `"top"` (the ridge), `"roof"`, `"wall"` (half the wall's
height), `"foot"`, and `"gap"`: the width of the gape at each of them (0 when split is 0). The strips
of tape go across the seam at `"roof"` and `"wall"`.

---

## 4. Knee-high (the last chorus: 207.26, 208.76, 210.26)

Each returns a `TowerGroup` of one layer (so `.hit(t)`, `.off(t)`, `.draw(F, a=...)`, `.sub(...)`,
`.anchors` work as above). Pale (pressure 0.8). `day=F.day` gives the look on the warm paper (faded
pencil, a breath of pastel) for a `ring` draw function. Rebuild them every frame.

### `small_backs(xs, y=742, h=150, seed=760, a=0.8, day=False, name="sback")`
One back at every world x of `xs`, standing on `y`: a number, or the hill contour as a function of an
array of x (`hills.ground_y`, or what you give `ground_line`: `hills.land_curve()`). Heights differ a little (129 to 171), and so do their
builds (girth, coat length, stance: from the seed).
`anchors["sback0"]` = x, y, h, head: where a small person stands when it turns round (take the back
away with `G.sub("sback0").set_off(t0, t1)`, or cross-fade with `a`). 4 backs: 8.8 ms.

### `small_voices(centres, target, rx=88, ry=52, seed=860, a=0.8, full=1.0, day=False, name="svoice")`
One balloon at every world point of `centres`, tails toward `target`. They empty with
`G.sub("svoice0.row", "svoice0.cross").set_off(t0, t1)` (or `full` 1..0);
`anchors["svoice0"]` = x, y, rx, ry: where a bubble takes over. 3 balloons: 5.5 ms.

### `small_house(x, y=742, h=150, split=0.10, seed=600, a=0.8, day=False, name="shouse")`
The split house, h to the ridge (100 wide). Animate `split` to 0 on `F.t` as the two push the halves
together. `anchors["wall"]`, `anchors["roof"]`: where the strips of tape go; `anchors["gap"]`: how wide
the gape still is there. 3.7 ms.

```python
from hx.chalk.hills import ground_y                   # the hill contour: array of x in, array of y out
V = small_voices([(4960, ground_y(4960) - 300), (5080, ground_y(5080) - 380)], (px, ground_y(px) - 330)).hit(207.26)
V.sub("svoice0.row", "svoice0.cross", "svoice1.row", "svoice1.cross").set_off(208.0, 208.8)     # they empty
V.draw(F)
small_backs([5150, 5240, 5340, 5430], ground_y, day=F.day).hit(208.76).draw(F)
split = 0.10 * (1 - ease(F.seg(211.0, 211.8)))        # the two push the halves together
Hs = small_house(5560, ground_y, split=split, day=F.day).hit(210.26)
Hs.draw(F)
# when split has reached 0: a strip of tape (things') at Hs.anchors["wall"] and at Hs.anchors["roof"]
```

---

## 5. Limits

- The far backs' legs end in the horizon's mist (they have no feet): if the camera rises so far
  that the ground line leaves the frame, nothing hides that. Keep the ground line in frame (rule 2).
  That mist is a soft patch about the horizon under them; it is meant to lie on the plain's haze.
- The ceiling decides how much of the groups is seen. With gloom's lid at screen y 235 and a sag of
  50 px over the child its loose loops reach to about screen y 430 in places: the spiky shout and
  the top rows of the big balloon are crossed by them. That is wanted (things lost in the scribble),
  but a lid hung lower than that hides the voices' crossed-out rows.
- `TowerGroup.flat` is the same picture as the layered group only at the camera you give it, and
  without the mist; hand it to a morph at the frame the change begins. Its strokes keep the giants'
  line width.
- Depth layers parallax under a camera MOVE; at `L.cam` they sit as composed. If your wide camera is
  not `L.cam`, the far members shift a little against the near ones (nothing breaks).
- The furrows need `vx` within about 3000 units of the camera to read as a fan; further away (the
  right third of the wide frame) they are rows that bunch toward the horizon and mostly fade.
- The plain is a night set. The day skin has no plain (the hills take over).
- Level 2 backs cost about 14 ms, close to the 15 ms budget.
- The backs stand upright on the point you give: on a steep hillside (small_backs) their two feet
  are on one level.
- The storyboard's "two doors behind the house" are not in the house group: draw two `door` sets of
  your own in a `F.depth(0.6)` layer if the scene wants them.
- `import` it by name (`from hx.chalk.land import *`) until `hx/chalk/__init__.py` exports it; its
  `house`, `voice`, `back_figure` and `footprints` replace the prototype's of the same names.
