# hx.chalk.people: the other people

Faceless outline people in dim chalk: pupils with a satchel, two adults, the rows of the classroom,
the stream on the corridor line, the ring of backs and its whispers, the two adults at the home
table, the three drawn figures of the family line. They are never villains and never individuals:
they are simply turned away. Only in the last chorus do they turn round, and then they are just
children with two dots and a small mouth.

    from hx.chalk.people import *        # (or from hx.chalk import * once the package imports it)

Everything is in WORLD units through `F.cam`; a frame is a pure function of time; no lyric text
anywhere. Proofs and the script that makes them: `hx/_review/v4_kit/people/` (`proofs.py`; a second
set of test scenes, written from this page alone, is in `review/review.py` there).
Costs: 1080p, one core, zoom 1 (`cost.txt` there).

What the child stands next to, and where (the examples below use these numbers):

| piece | film time | the child |
|---|---|---|
| rows | 36.27 to 48.27 | left of them, on the ground line (the rows fill x 780 to 1680) |
| home adults | 48.3 to 54.4 | behind the table, between them |
| stream | 103.5 to 115.8 | on the line at the x the stream was made for; draw it between the two lanes |
| ring | 115.8 to 126.3 | outside: about `cx - rx - 190`; or in the middle with `inward=False` |
| family line | 127.8 to 138.2 | in the small one's place (`small=False`) or beside the drawing |
| turning round | 208.76 to 210.2 | passing by; they are knee-high (about 128 units) |

## 1. One person

```python
person(F, x, y, h, P=P_REST, kind="pupil", face=1, seed=0, a=1.0, draw=1.0, back=0.0, dots=0.0,
       head=0.0, tilt=0.0, col=None, far=0.0, off=0.0, variant=None, wave=0.0, wag=0.0) -> joints
```

Draws one person standing on the world point (x, y), `h` world units tall, in the rig pose `P`
(any `Pose` of `hx.chalk.figure`: `walk()`, `walk_to()`, `mixp()` all work; the pose's own `turn`
is ignored, the view is given here).

| argument | meaning |
|---|---|
| `kind` | `"pupil"` (330 to 360 tall: the child's build, a jumper or a dress, a satchel), `"coat"` (an adult in a long coat, 520 to 560), `"skirt"` (an adult in a cardigan and a skirt, hair in a bun, 520 to 560). An adult's head is no bigger than a child's; its body is longer, its stoop smaller |
| `face` | +1 looks right, -1 left (in profile) |
| `back` | 0 profile .. 1 seen from behind (the main view of the film): the whole back of the head is hair, down to the nape, and the satchel sits on the back |
| `dots` | 0 .. 1 seen from the front, with two dot eyes and a small smiling mouth. The view is continuous: `dots - back` runs from -1 (back) through 0 (profile) to +1 (front) |
| `head` | extra turn of the head, same units (it leads a turn; +-0.15 makes a ring of people look at each other) |
| `tilt` | sideways lean of the whole figure, radians (+ = toward world +x; +-0.04: weight on one leg) |
| `wave`, `wag` | `wave` 0..1 lifts the near hand out to the side (hello; reads in every view); `wag` -1..1 swings it |
| `draw` | 0..1 the person draws itself on: the lines one after another (limbs, garment, head, hair, the tip leading), each tone rubbed in as its outline closes |
| `off` | 0..1 the person is rubbed out again, the trailing side first, each line taken back from its ends, a ghost left behind |
| `a`, `far` | pressure; `far` 0..1 dimmer and toward the far chalk (depth) |
| `col` | line colour. Default: `C.CHALK_DIM` at night; in the day skin (`F.day`) pencil line, skin-toned head, a pastel jumper chosen by the seed (coral, sea, mustard, lilac, rose, blue) and brown hair |
| `seed` | the hand, and the person: hair (short, bob, ponytail, bunches), jumper or dress. Keep it fixed |
| `variant` | `{"hair": "short" / "bob" / "tail" / "bunches" / "neat" / "bun", "satchel": False, "dress": True}` to choose instead of the seed |

Returns world points `head neck pel back ha_f ha_b sh_f sh_b an_f an_b top` and `R` (head radius);
`back` is the point between the shoulders (where a hand would touch). Detail follows the height on
screen (under 150 px: fewer points; from 420 px a coat gets a few shading strokes). A person wholly
off screen costs only its joints.

What moves, and on which clock: `P`, `x`, `back`, `dots`, `head`, `wave`, `draw`, `off` act: drive
them from `F.t`. The line boils by itself. Nothing in a person runs on its own clock. When `P` comes
from the rig's `walk()` its `bob` is used: the satchel bounces on the back and a ponytail or
bunches swing a little behind each step.

- `turned(w, lead=0.18) -> dict`: the keywords of a turn from the back view (w = 0) through the
  profile (0.5) to the front with the dot face (1); the head leads. `person(F, ..., **turned(w))`.
  The profile it passes through looks toward `face`. 0.8 s is a good length.
- Poses: `P_REST` (standing at ease, legs straighter than the child's), `P_AWAY` (head a little
  down), `P_WAVE` (a little taller: goes with `wave=1`), `P_SIT` (on a seat 0.19 body units high;
  for another seat `P_SIT.but(pel=(-0.02, seat / h + 0.035))`). `STEP_RATE` = 1 / 1.5: walk cycles a
  second for one step per beat.
- `person_sketch(x, y, h, P=P_REST, kind="pupil", face=1, seed=0, a=1, back=0, dots=0, head=0,
  tilt=0, col=None, day=False, far=0, name="person", variant=None, wave=0, wag=0) -> People`: the
  same person as a Sketch of named strokes, for sets that draw on, are un-drawn and morph. Parts in
  paint order (as the view needs them): `arm_b leg_b leg_f bag skirt body body.shade strap_f strap_b
  head hair hair_far hair0 hair1 eye_l eye_r mouth arm_f` and `bag.fill skirt.fill body.fill head.fill`.
  `S.who[0]` holds the joints listed above.

Cost: pupil 2.5 ms (profile, back), 2.7 with the dot face, 2.3 at 130 px; coat 2.7; skirt 2.8.

```python
# the last chorus: knee-high and pale, they turn round one after another; the middle one lifts a hand
for i, x in enumerate((1010, 1090, 1180)):
    w = ease(F.seg(208.76 + 0.14 * i, 209.56 + 0.14 * i))
    up = ease(F.seg(209.56, 209.96)) if i == 1 else 0.0
    person(F, x, 742, 128 + 10 * (i % 2), mixp(P_REST, P_WAVE, up), "pupil", -1, seed=14 + i, col=C.CHALK_COOL,
           wave=up, wag=math.sin((F.t - 209.76) * 9.0) * up, **turned(w))
```

## 2. The classroom rows

- `pupil(x, y, s=1.0, seed=1200, col=C.CHALK_DIM, a=0.85, name="pupil", far=0.0, hair=None, desk=True, sit=None, sway=0.0) -> Sketch`
  A classmate at a desk, seen from behind, in the build of the standing pupils (a big round head
  of hair on a small jumper). (x, y) = the floor under the chair. `s` = 1: 192 units from the floor
  to the top of the head, the desk 132 wide, the head 37 in radius (1.3 to 1.4 goes with the child's
  380). Parts in paint order: `desk` (+ `.fill`: the box under its top), `desk.top`, [`desk.book`],
  `shin_l`, `shin_r` (its own legs), `shoulders` (+ `.fill`), [`sleeve_l`, `sleeve_r`: not when `far`
  >= 0.5], [`arm`: only when propped], `collar`, `head` (+ `.fill`), `hair`, [`hair0`, `hair1`], `seat`,
  `leg_l`, `leg_r` (the chair's posts and legs), `chair` (+ `.fill`: the slat of its back), and for
  some seeds `bag` (+ `.fill`), `bag.handle` (a satchel standing by the desk).
  The seed is the pupil. `sit`: `"upright"`, `"slumped"` (the head sunk between the shoulders) or
  `"propped"` (leaning on an elbow, the head in a hand); `hair`: `"short"`, `"bob"`, `"tail"`,
  `"bunches"`; None = the seed chooses (`SITS`, `HAIRS` list them). `far` 0..1 dims the tone. `sway`
  -1..1 shifts its weight and tips its head a little. The Sketch has `.head` (world centre) and `.R`.
  It replaces `props.pupil` (same call; the old part names `shoulders head chair leg_l leg_r` are
  all still there).
- `class_rows(far=((980, 1220, 1460), 738, 1.16), near=((860, 1100, 1340, 1580), 826, 1.40), seed=1400, a=0.95, name="rows", t=None) -> People`
  Two rows in depth, each `(xs, floor y, scale)`. The far row (`rows.b0` ..., drawn first,
  `C.CHALK_FAR`, dimmer tone, thinner) sits against the wall, on the ground line; the near row
  (`rows.f0` ..., `C.CHALK_DIM`) sits on the floor in front of it, lower in the picture and larger,
  and overlaps it: the far row shows between and over its heads. Hair and posture go round, so a
  row is mixed. The defaults fill world x 780 to 1680 (inside what the classroom set keeps free;
  a satchel may stand beside the last desk, out to 1740) and y 520 to 830, above the lyric band; the near pupils have the child's own size (the far ones are a
  little smaller than the desk that stands apart, which is at 1.35). `class_rows(**CLASS_ROWS)`
  gives the set's own seats (scale 0.80 / 1.08: pupils half the child's size).
  `t=F.tb`: the class is alive: now and then somebody shifts on a chair or tips a head, slowly, each
  in its own time (most hardly at all); held in the silences. `t=None`: nobody moves.
  Names: `rows.f2.shoulders`, `rows.b0.chair`, ... `R.who`: every pupil (`name x y s head R`), far
  row first. `R.far`, `R.near`: the two rows as Sketches (the same strokes), for a child that
  passes between them: `R.far.draw(F)`, the child, `R.near.draw(F)`. The desk that stands apart is
  the set's.

It is a Sketch: `R.on_beats(F.tl, 36.27, every=0.5, by=2)` draws one pupil per half beat (far row
first); `R["rows.f3"]` is one pupil; `R.place(dx, 0)` moves the rows a step away; in a `morph`
declare few pairs, onto open lines (`("table.top", "rows.f3.seat")`, `("table.leg_l", "rows.f3.leg_l")`).
Cost: 3.2 ms a pupil at scale 1.4; the default 7 pupils 22 ms (build 2.3), the same with `t`;
10 pupils at the set's smaller seats 28 ms (over the 25 ms line: keep to 7 or 8).

```python
K = classroom(); K.back(F); K.view(F); ground_line(F); K.draw(F)
R = class_rows(t=F.tb)
R.on_beats(F.tl, 36.27, every=0.5, dur=1.0, by=2)
R.draw(F)                                   # then the child (left of x 780), the scribble
```

## 3. The stream on the corridor line

- `walkers(t0, t1, x, hits=(), seed=31, every=1.5, reach=1500, h=(326, 362), back_every=3, fade=2.2, front=0.5, front_from=None, hit_lane=-1, clear=()) -> tuple of Walker`
  The whole stream between t0 and t1, deterministic in its arguments (cached: call it every frame).
  Everyone walks one step per beat (a foot comes down on every beat); speed comes from height, mood
  and stride (about 135 to 205 world units a second). `x`: the world x the passes are timed against
  (the child's place). `hits`: times at which a pupil coming the other way (walking left) passes x
  exactly: the shoulder contacts. `hit_lane` -1: those pass BEHIND the child, who stays readable
  (it steps toward us, off the line); +1: in front. `every`: seconds between passes (1.5 = two per
  bar). `back_every`: every n-th walks right (overtakes from behind, a little brisker). `front`: the
  share that passes in front of the child from `front_from` on (before it everybody passes behind;
  None = from the start): 108.25 for the moment the child stops stepping aside and the stream parts
  round it. `clear`: `((t0, t1), ...)` spans in which nobody may pass in front of x (whoever would,
  passes behind): a pupil in front hides the child's head for about 0.45 s either side of its pass,
  so name the moments at which the child acts. `reach`: they exist only within x - reach .. x +
  reach. Those inside at t0 draw themselves on while they walk, one per quarter beat, nearest the
  child first (the first contact can be less than a second after t0); in the last `fade` seconds
  nobody new comes and those still there are rubbed out one after another, the farthest first.
- `Walker`: `seed h m q d (+1 right / -1 left) T (when it passes x) x lane (+1 front / -1 behind) v
  (units a second) on off hit`; `w.at(t)` = its world x at t; `w.pose(t)` = its pose (some hold a
  strap); `w.ph(t)` = its walk phase.
- `passes(W, x=None, lane=None) -> [(time, walker), ...]`: when each walker passes world x (default:
  the x they were made for), in order of time; `lane=+1` only those in front. Use it to time the
  child's reactions, or to find who is where: `[t for t, w in passes(W) if w.hit]`.
- `stream(F, W, y=742, t=None, lane=None, a=1.0, col=None) -> [(walker, joints), ...]`: draws the
  walkers at time `t` (default `F.t`: they act). `lane=-1` / `+1` draws only one lane: call it
  twice, round the child. The front lane stands 5 units lower and 3 percent larger, the back lane
  4 higher, 3 percent smaller and dimmer. Walkers off screen cost nothing.

Cost: 2.6 ms a walker on screen: 8 walkers 21 to 22 ms (zoom 1.3, the framing of the proofs' close
shot); at zoom 1 the default stream has 10 to 11 on screen: 26 to 29 ms (`every=2.0` thins it).

```python
W = walkers(103.5, 115.8, 900.0, hits=(104.07, 105.23, 106.57), seed=31, front_from=108.25,
            clear=((109.3, 110.0), (110.9, 112.1), (113.3, 114.5)))    # the child is crossed out and redraws itself
K.draw(F); ground_line(F)
stream(F, W, lane=-1)                       # those who pass behind
figure(F, cx, 742, 380, pose, "child", seed=3)
stream(F, W, lane=1)                        # those who pass in front (none before 108.25)
```

## 4. The ring of backs, the whispers

- `ring_of_backs(cx, y=742, n=7, rx=None, ry=None, h=345, seed=1700, a=1.0, inward=True, close=None, col=None, name="ring", t=None, times=(), start=0, step=1, dur=0.30) -> People`
  n pupils standing in a loose ring round the world point (cx, y): `ring.p0` .. `ring.p6` in the
  order they stand round it (the order a whisper travels), painted far to near. `rx`, `ry`: radii
  on the ground (the near ones stand `ry` below the line and 5 percent larger, the far ones above,
  smaller and dimmer).
  `inward=True` (rx 215, ry 40): a huddle; everybody faces the middle, so from outside there are
  only backs: the child stands outside, at about `cx - rx - 190` (the ring is about 2 rx + 120 wide).
  `inward=False` (rx 300, ry 62): everybody has turned its back on a child standing in the middle
  at cx: backs behind it, shoulders at its sides; the ring is open toward us (`close` 0.72 of the
  circle). Draw the far ones (`w["y"] <= y`), the child, then the rest.
  Nobody ever faces us: whoever would is seen in profile. Parts of each: those of `person_sketch`
  (`ring.p3.body`, `ring.p3.head`, ...). `R.who[j]`: `name x y h head R back face view` and the
  joints; `R.heads`: the head centres in ring order.
  `t`, `times`, `start`, `step`, `dur`: the arguments of `whispers()` (`t=F.t`). Given them the ring
  is alive while the whisper passes: whoever passes it on leans toward the next one, whoever gets
  it leans in to take it and straightens again. Without them it stands still (only the line boils).
- `undraw(S, pt, t0, dur=0.8) -> end time`: takes a set back from a world point outward (a back
  un-drawing under the child's hand): every item gets its `off` time by its distance from `pt`.
  `undraw(R["ring.p2"], R.who[2]["back"], 123.26)`.
- `whisper(F, p0, p1, w, seed=0, size=46, a=1.0, hop=0.42, t=None) -> point`: a whisper: a small knot
  of the black crayon with its pale dust, hopping from world point p0 to p1 (w 0..1) in an arc `hop`
  times their distance high, a thin tail behind it while it flies. Never writing, never a face. It
  churns on the boil clock (`t`, default `F.tb`); the hop is the caller's `w`, on `F.t`.
- `whispers(F, heads, times, dur=0.30, start=0, step=1, seed=0, size=46, a=1.0, lead=0.35, tail=0.6, r=52, t=None) -> point or None`
  A whisper passing from head to head: at each of `times` it hops to the next head. `heads`: the
  People of `ring_of_backs` (heads and radii in ring order) or a list of head centres with `r`.
  `start`: the head it begins at; `step` +1 / -1 the way round. It perches on the upper edge of a
  head, on the side of the next one (never on a face), appears `lead` s before the first hop (over
  0.22 s) and is gone `tail` s after the last has landed. Returns where it is (to send something
  after it), or None.
- `long_line(x0, x1, y=552, n=6, seed=2290, col=C.CHALK_COOL, a=1.0, lw=5.4, sag=14, name="line") -> Sketch`:
  one long hand-drawn line as n strokes laid end to end (`line.s0` .. left to right): what the ring
  unrolls into (127.01 to 127.76) and what the family's arms come out of. See the second example.

Draw-on with the beats, in ring order: `R[w["name"]].spread(t0 + 0.375 * k, 0.0, 0.5, by=2)`.
Cost: ring of 7: 18 ms either way round (build 3.7); a whisper 0.5 ms. Flicker of the standing
ring: 0.13 levels, 0.5 percent on a boil step, 0 inside a pair, 0 in the silences.

```python
WH = (118.40, 118.76, 119.14)
R = ring_of_backs(1240, 742, n=7, seed=1700, t=F.t, times=WH, start=2)
for k, w in enumerate(sorted(R.who, key=lambda w: w["x"])):          # one back per half beat from 115.77
    R[w["name"]].spread(115.765 + 0.375 * k, 0.0, 0.5, by=2)
near = sorted(R.who, key=lambda w: w["x"])[:2]                        # the two the child reaches for
for w, th in zip(near, (123.26, 124.76)):
    undraw(R[w["name"]], w["back"], th, 0.9)
R.draw(F)
figure(F, 1240 - 215 - 190, 742, 380, pose, "child", seed=3)
whispers(F, R, WH, start=2, seed=5)
```

```python
# 127.01: what is left of the ring unrolls into one long line; 127.78: the line is the family's
S = family_line(cx, 742, small=False, hands=(J["ha_b"], J["ha_f"]))      # J: the child's joints
L = long_line(cx - 1100, cx + 1100, 552, n=len(S.chain))
order = sorted(R.who, key=lambda w: w["x"])
rest = R.without(order[0]["name"], order[1]["name"])                     # the two that un-drew are gone
left = order[2:2 + len(S.chain)]
if F.t < 127.77:
    morph(rest, L, F.seg(127.01, 127.76), [(w["name"] + ".body", f"line.s{k}") for k, w in enumerate(left)]).draw(F)
else:
    morph(L, S, F.seg(127.78, 129.3), [(f"line.s{k}", nm) for k, nm in enumerate(S.chain)], stagger=0.3).draw(F)
```

## 5. The two adults at the home table

- `home_adults(F, xl, xr, y=742, t=None, leave=52.4, gone=54.4, seat_y=None, hl=545, hr=528, kinds=("coat", "skirt"), seed=2100, a=1.0, draw=1.0, m=0.62) -> (joints left, joints right)`
  `seat_y=None`: they stand at world x `xl` and `xr`, turned from each other (the left one faces
  left, the right one right, each a little turned away from us too), breathing. `seat_y` = world y
  of the chair seats: they sit on the two end chairs facing the table; at `leave` they stand up
  (feet where they were, `RISE` = 0.56 s) and turn their backs on each other, the turn ending in the
  first step. Either way they then walk away to opposite sides, one step per beat, and are rubbed
  out as they go: by `gone` only a fading ghost is left (nothing 0.25 s later). In those two seconds
  they get about 210 world units from the chair (340 when they stood): they do not reach the edge
  of a full frame. No gesture and no scene: two people who no longer face each other. `draw` 0..1
  draws them on.
  `xl`, `xr` are where they sit or stand BEFORE they leave: with the set, the anchors at apart = 0
  (`home_anchors(0.0)`), also while the chairs slide away (the function moves the adults itself).
- `walk_off(t, x, face, h, start, steps=6, m=0.62, rest=P_AWAY) -> (pose, x, face, t0, t1)`: a person
  leaving from standing: one step per beat from `start`, with an easier gait than the rig's trudge
  (the first step is slow: about 50 units in the first beat, then 230 a second for an adult).
  `person(F, W[1], y, h, W[0], kind, W[2])`. (The rig's own `walk_away` is something else: the child
  seen from behind.)

Cost: 5.6 ms standing, 9.5 ms while they are rubbed out.

```python
apart = ease(F.seg(52.4, 54.4))
Hm, an, a0 = home_table(apart), home_anchors(apart), home_anchors(0.0)
Hm.back(F); Hm.view(F); ground_line(F)
Hm.draw(F, "window", "lamp", "chair_m")
figure(F, *an["child"], 380, pose, "child", seed=3)
Hm.draw(F, "chair_l", "chair_r")
home_adults(F, a0["adult_l"][0], a0["adult_r"][0], seat_y=a0["seat_y"], draw=F.seg(48.3, 50.2))
Hm.draw(F, "table", "cups")
```

## 6. The family line

- `family_line(x, y=742, hs=318, ht=(520, 548), spread=268, part=0.0, slip=(0.0, 0.0), travel=640, hands=None, small=True, faces=1.0, seed=2300, col=C.CHALK_COOL, a=1.0, lw=5.4, name="family") -> People`
  Three drawn stick figures hand in hand, as the child draws them, come to stand on the ground
  line: two tall ones (`a` left, `b` right, heights `ht`, `spread` to either side) and a small one
  (`c`, height `hs`) at world x. Round heads that do not quite close, one line for the body, an
  upside-down V for the legs, dot eyes and a smile.
  - `part` 0..1: the line parts. The tall ones slide `travel` world units toward the two sides
    (640 brings them to the edges of a 1920 frame centred on x) and their inner arms stretch into
    long sagging lines that still end in the small one's hands. Animate 131.85 to 134.0, eased.
  - `slip=(left, right)`, 0..1 each: that line slips out of the small hand, the slack runs out of
    it in a wave and it falls back to its figure as an arm; the small one's arm sinks and its smile
    goes. Animate over about 0.6 s from 134.51 and 134.77.
  - `hands=(left point, right point)`: end the lines somewhere else: the real child's own hands
    (`J["ha_b"]`, `J["ha_f"]` of the figure), with `small=False`, which leaves the small figure out
    so that the child stands in its place.
  - `faces`: pressure of eyes and mouths (0: none).
  Parts: `a.head a.body a.legs a.arm_out a.arm_in a.hair0-2 a.eye_l a.eye_r a.mouth`, `b.*` likewise
  (`b.hair`: long hair in one stroke), `c.head c.body c.legs c.arm_l c.arm_r c.hair0-2 c.eye_l
  c.eye_r c.mouth`.
  `S.who`: a, c, b (`name x y h head R shoulder`); `S.hands` = {"l", "r"}: where the two lines end;
  `S.ends` = {"l", "r"}: where their free ends are now (they leave the hands as they slip);
  `S.chain`: the full names of the arm strokes, hand to hand, left to right (`family.a.arm_out`,
  `family.a.arm_in`, `family.c.arm_l`, `family.c.arm_r`, `family.b.arm_in`, `family.b.arm_out`; four
  with `small=False`): they are drawn left to right, so they can come out of `long_line()` in a
  `morph` (the example in section 4).
  Un-draw the tall ones with `S["family.a"].set_off(t0, t1)`.

Cost: 6.4 ms. Flicker standing: 0.22 levels, 0.7 percent.

```python
S = family_line(960, 742, part=ease(F.seg(131.85, 134.0)),
                slip=(F.seg(134.51, 135.1), F.seg(134.77, 135.36)))
S.spread(127.78, 0.075, 0.5)                # the whole line in about two seconds, left to right
S["family.a"].set_off(135.3, 136.4)
S["family.b"].set_off(135.5, 136.6)
S.draw(F)
```

## 7. Notes

- `People` is a `Sketch` with `who` (and `heads`); `S[...]`, `S.sub()`, `S.place()` return plain
  Sketches (the items are the same objects, so times set on them stick).
- Colours before 217.84: only cold chalk (`C.CHALK_DIM`, `C.CHALK_FAR`, a dim blue rubbed tone) and,
  for the whisper, the scribble's black with its pale dust. Nothing here is amber. In front of a
  lit window a person is a dark shape with a chalk outline (its tone is rubbed over a knock-out).
- Flicker, static camera, the piece and the ground line: rows 0.15 levels and 0.6 percent on a boil
  step (the same with `t=F.tb`), ring 0.13 / 0.5, adults standing 0.11 / 0.4, family 0.22 / 0.7;
  inside a pair 0; in the silence 56.0 to 58.6 exactly 0 for all of them.
- The people are built on `figure.solve()` (profile joints) and measured against `figure.STAND`
  (arm length, hip height): if the rig's build changes they follow. From a pose they read the
  rig's keys and, when present, `bob`.
- Not there: standing people do not breathe (only the home adults do); the rows and the ring move
  only as described; a walker has no contact pose for the shoulder brush; the sitting adults' coat
  is boxy on the lap; walking seen from behind or from the front is untried.
- The enormous turned backs of the choruses are not here (`land.py`).
