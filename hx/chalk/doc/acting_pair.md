# hx.chalk.acting_pair: the friend, and the two together

The performances of the relationship: the far friend of the first chorus, and everything from the
second chorus to the end (138.2 s on). `from hx.chalk import acting_pair as AP` (the package's star
import does not bring it). The module imports only the rig (`figure.py`), nothing that draws a
world: whatever a performance needs from the scene comes in as arguments.
Proofs, with the real kit round the figures, and the script that makes them:
`hx/_review/v4_kit/acting_pair/` (`proofs.py`, `numbers.txt`). A second set of scenes written from
this page alone, at the film's cameras, and the measurements: `hx/_review/v4_kit/acting_pair/review/`
(`review.py`: strips and every acted beat as consecutive frames at 100 percent; `measure.py`:
hand-offs, pops, hands, feet, heads, cost; `switches.py`, `checks.py`, `tools.py`). No lyric text anywhere.

## 1. What a performance is

A pure function of the song's time (absolute seconds). It returns a `Duet`:

| | |
|---|---|
| `D.child`, `D.friend` | an `Act` each (`friend` is `None` while it is not in the picture) |
| `D.pts` | named WORLD points `(x, y)` the scene stages things with (or `None` while they do not exist) |
| `D.num` | named numbers: cues, 0..1 ramps, counts |
| `D.order` | `"fc"`: draw the friend first, the child on top; `"cf"`: the child first |
| `D.show(F, child_kw=None, friend_kw=None)` | draws both in that order; returns `(child joints, friend joints)` |

`Act`: `pose x y face grab draw a h skin seed lift` (everything `figure()` takes; `lift` = world
units off the ground in a jump, for the shadow), `pts`, `num` (solo performances only).
`a.show(F, a=1.0, **figure_kw)` draws it and returns the joints; `a.joints()` gives them without
drawing (pinned hands applied; 0.15 ms). To put something between the two, draw them yourself:

```python
D = AP.s07(F.t)
first, second = (D.child, D.friend) if D.order == "cf" else (D.friend, D.child)
first.show(F); second.show(F, rim=(light_col(F), (0.3, -1.0), k))
```

- **Times** are cue dictionaries with the storyboard's values: `S07_T .. S11_T`. Override any cue by
  keyword: `AP.s08(t, join=195.2)`. `s06` and `s03_friend` take their cues as plain arguments.
  `beat(k)`, `beat_after(t)`: the beat grid (0.265 + 0.75 k).
- **Places** are arguments with `hx/story.py`'s values as defaults. Everything is WORLD.
- **Take `x`, `y`, `face` from the Act on every frame.** A face is never animated: where a figure
  turns round, the function changes the way it is written in the MIDDLE of the turn (`Act.face`
  flips, and with it which hand is `"f"`; on the sofa the ground point changes too). The picture on
  both sides of that frame is the same but for the slant of the garment's zigzag, which is why it
  happens inside fast motion and never on a hold.
- **Hands that meet** are pinned on both figures to one world point (`grab`); that point is in `pts`.
- **Holds are alive** (breath and shifts on the true time, chance blinks kept off the acted beats).
  Panting and the sleeper's slow breath run on a phase of their own that is continuous in time.
- **A figure is drawn at full height where it stands.** Walking away into the depth (`s06`) is the
  camera's pull-back and the falling pressure `Act.a`, as in `acting_child.s03`.
- Nothing keeps state; the plans are cached per set of arguments (first call of a section 1 to 3 ms).

## 2. The rest states of the hand-offs

`hold_B6(t, x=X5, y=FLOOR, d=180)`, `hold_B7(t, x=X5, y=FLOOR, d=180)`, `hold_B8(t, x=X5, y=FLOOR, d=180)`,
`hold_B9(t, x=X9, y=FLOOR, d=180, ground=None)`, `hold_B10(t, x=X10, y=FLOOR, ground=None)` -> `Duet`
(`PAIR_HANDOFF["B6"]` ...). `x`: the child's ground x of that hand-off, `d`: the friend stands at
`x + d`. Both neighbouring scenes call the same function at the hand-off. Every section returns
exactly its opening rest state up to its first cue, and exactly its closing one from at least
0.25 s before the hand-off (measured at -0.26, -0.25, -0.02, 0 and +0.017 s: 0.000 world units at all
five on both sides, places and faces as `story.HANDOFF` has them; the pixels of `hold_B7` and of the
first frame of `s08` are identical).

| | state | pts |
|---|---|---|
| B5 (start of `s06`) | `alive(STOPPED, t, 3)` at `(X5, FLOOR)`, face 1: equal to `acting_child.hold_B5` (0.000) | |
| B6 158.86 | child sitting at x, head lifted, looking up; friend crouched at x + 180 (face -1), looking up; near hands joined | `hands`, `sky` |
| B7 182.30 | both standing; the friend's near hand on the child's upper arm (the shoulder itself is under the chin), both the child's hands closed over it; the child's eyes fully open; `order "cf"` | `shoulder` |
| B8 201.25 | back to back in the opening: child at x - 20 (face -1), friend at x + 200 (face +1, on tiptoe); each has both hands up on the bunch of strands of its own curtain and hangs back on it, its feet planted 15 and 50 units outward of its ground point; the arms go up BEHIND the heads, so both faces are free; the heads are 77 units apart; the grips shiver (true time) | `grip_l`, `grip_r`, `hands_l`, `hands_r` |
| B9 226.76 | hand in hand on the hill: child at x (face 1, small smile, tufts up), friend at x + 180 (face -1); the string in the child's far hand, held behind its hip | `hands` (= `ring`), `string` |
| B10 244.50 | the child alone at x (face -1), at ease; the string in its near hand | `string` |

B8's grips: `(x - 107.4, FLOOR - 319.2)` and `(x + 289.2, FLOOR - 325.9)`: give them to
`gloom.curtains(left=, right=)`; the opening is 397 wide about `x + 91` (287 left and 109 right of the
seam at `x + 180`: section 6).

## 3. The far friend (first chorus)

`s03_friend(t, x=FRIEND_FAR_1, y=FLOOR, h=293.0, t_on=70.9, t_seen=75.3, t_last=82.76, t_go=84.3) -> Act`

Built for 60 to 80 px on screen (`land.tower_layout(X2).friend`, `.friend_h`): at that size only
whole shapes read, so it turns three-quarter to us and waves with its outer arm held out at its
SIDE (an arm raised straight up hides behind the big head), a sweep a beat, and hops on every beat
(it lands on the beat); the other hand is at its mouth. It draws itself on from `t_on` (0.7 s). At
`t_seen` (the child has turned) it dips and jumps with both arms up, waves with both, later holds
an arm out and scoops it in once a beat (come). At `t_last` it waves once more; at `t_go` it turns
round and walks off right, a step a beat (`Act.face` becomes +1, `x` travels).
`num`: `call` (0..1, its mouth), `seen`, `hop` (world units off the ground; already in `y`),
`point` (0..1 from `t_go + 1.4` over 2 s: let it become a point of light; `Act.a` = 1 - 0.85 point).
`pts["feet"]`: where the amber line starts. Draw `amber_glow` at no more than a = 0.6 behind it: a
full glow washes its thin limbs out. Framing: the wide frame (the whole figure 60 px); its face is
two dots there. 0.02 ms.

## 4. s06: the storm (138.20 to 158.86)

`s06(t, x=X5, y=FLOOR, d=180, hits=HITS_2, t_turn=138.26, step=0.5, t_enter=147.265, t_run=150.265, t_offer=152.36, t_take=154.40, t_lift=154.84, t_up=157.01)`

The child turns its back and walks away IN PLACE, lower and paler than in chorus 1 (`child.a` falls
to 0.38): draw it at `(x, y)` at full height, the pull-back makes the distance (`num["away"]`, body
units walked into the depth, is for the scene's footsteps and mist only). It stops on the first hit
and goes down under each: knees give, squat, sitting with its forehead on its knees (`num["cower"]`
0..1: let the lid sag by it). The friend walks in from the right from `t_enter` (from `x + 1085`; a
step a beat, leaning into the rain, an arm before its face; its line comes up over the first 0.6 s:
`friend.a`), runs the last steps from `t_run`, brakes (151.02), crouches without touching, holds out
an open hand low before the child's knees (there at `t_offer`) and waits. The child's hand comes out,
stops, takes it (`t_take`); still holding it, the friend brushes its free hand twice over the crown
of the bowed head (`t_take` + 0.3 to + 0.9: the loops off it); the child lifts its head (`t_lift`,
1.25 s, a blink on the way) and looks at the friend; both look up (`t_up`).
`pts`: `hands` (the open hand from `t_offer`, then the joined hands: `(x + 100, y - 78)`), `sky`
(where they look: `(x + 110, y - 560)`).
`num`: `away`, `cower`, `warm` (0..1 from `t_take`: amber rubbing off on the child's hand), `joined`,
`brush` (0..2: the strokes of the brushing hand done so far: let the scribble's loops come off the
child with them, half with each).
Framing: the hits are three changes of height and read in the wide frame (the child 78 px); the hand
and the brushing need the two-shot (zoom 1.2: heads 140 px). 0.05 ms (0.29 while it brushes).

## 5. s07: the bridge (158.86 to 182.30)

`s07(t, x=X5, y=FLOOR, d=180, root=None, tape=None, sheet_s=0.62, **S07_T)`

`S07_T = dict(pulls=(160.0, 161.9, 164.9, 167.9), offer=162.5, halves=163.3, tape=(165.63, 166.39), release=167.1, fist=173.5, fist2=175.0, lay=175.96, rise=178.45, stand=179.51, clasp=181.0, open=181.52)`

1. The friend sees the loose end hanging between them (`pts["end"]`), lets the hand go, reaches
   FORWARD for it and pulls: `pulls[0]` (it falls back on its bottom and stays sitting), `pulls[1]`
   (both hands, leaning far back). It holds the end out, low, and waits.
2. The child takes the two halves out from under its jumper instead (`halves`: they come up at its
   lap, below its bowed head) and holds them on its knees, apart; then it looks up, takes the end
   with its near hand and gives ONE small pull of its own (`pulls[2]`); the friend is glad.
3. The child pushes the halves together and holds them out; the friend lays a strip of tape on each
   attack (`tape`), its hand running along the strip.
4. The child lifts the mended drawing and opens its hands (`release`: from there the scene moves
   it); it takes the line under the friend's hand and they pull together (`pulls[3]`), then watch
   the drawing rise.
5. The child finds its far hand clenched (the fist is held out before it from 170.8: run the strand
   to `pts["fist"]`), looks along the strand, squeezes, and opens it (`fist`); it opens the hand
   that holds the line (`fist2`); it smooths the line along the ground while the friend takes it up
   on its own right and casts it out toward the hill (to `lay`); both watch.
6. The friend gets up (`rise`), the child gets up by itself; the friend's hand comes to rest on its
   upper arm (`stand`); the child's head sinks; both its hands close over the hand (`clasp`) and it
   lifts its face, eyes fully open (`open`, 0.26 s).

- `root`: world point where the loose end leaves the mass (default `(x + 125, y - 470)`): the
  friend's hand in the pull together is 40 units up the line from the child's.
- `sheet_s`: the scale you give `things.family_held` (0.62: between two big heads 180 apart there is
  no room for a larger sheet, and it is held LOW, on the child's knees). `tape`: the strips' ends as
  `family_held` returns them, if you want the taping hand exactly on them (default: computed for
  `sheet_s`; `pts["tapes"]` gives what it used).
- `pts`: `hands` (until they part at 159.45), `end`, `line` (the `hand` of `gloom.unravel`: the
  lowest hand on the line, or where the line lies when nobody holds it; `None` before `pulls[0]`),
  `half_l`, `half_r` (give them to `family_held`; frozen from `release`), `sheet` (the middle of the
  sheet at `release`: where the scene's rising drawing starts), `tape` (the taping hand), `tapes`,
  `fist`, `lay_c`, `lay_f`, `shoulder` (`(x + 39.9, y - 211.3)`).
- `num`: `pulls` (0..4, each eased over 0.5 s: `out = 500 * pulls`), `busy` (`slack = 1 - busy`),
  `who` (0 nobody, 1 the friend, 2 the child, 3 both), `halves` (0..1: their pressure as they come
  out), `taped` (0..2), `release`, `fist`, `fist2` (1 clenched .. 0), `lay` (0..1), `up` (0..1).
- While the friend tapes (`D.order == "cf"`) draw the sheet between the two figures, so that the
  taping hand lies on it; otherwise after both.

```python
D = AP.s07(F.t)
T = ceiling(F, ax=X5, amount=1 - 0.17 * D.num["pulls"], **lid)
hand = D.pts["line"] or D.pts["end"]
unravel(F, T.band.root(X5 + 125, 0.15), hand, 500 * D.num["pulls"], slack=1 - D.num["busy"], face=1)   # until 175.0
first, second = (D.child, D.friend) if D.order == "cf" else (D.friend, D.child)
first.show(F)
held = D.pts["half_l"] and F.t < AP.S07_T["release"]
if held and D.order == "cf":
    family_held(F, D.pts["half_l"], D.pts["half_r"], 0.62, taped=D.num["taped"], a=D.num["halves"])
second.show(F)
if held and D.order != "cf":
    family_held(F, D.pts["half_l"], D.pts["half_r"], 0.62, taped=D.num["taped"], a=D.num["halves"])
```
Framing: the two-shot of B6 (zoom 1.2: heads 140 px). The sheet is 93 world units wide; the fist beat
and the eyes of B7 want heads of 140 px or more. 0.09 ms (0.45 on the few frames a hand changes its hold).

## 6. s08: the curtain (182.30 to 201.25)

`s08(t, x=X5, y=FLOOR, d=180, gap=None, **S08_T)`

`S08_T = dict(attacks=(184.34, 185.14, 186.26, 186.65, 187.56, 188.14, 188.90), lift=189.6, stand=191.90, join=195.5, turn=197.2, breath=200.2, pull=200.62)`

Both look up; the child's eyes go dull, its hands slip off, its head sinks (1.25 s), its knees give
and it sits down WHERE IT STOOD (the feet stay; its hips are 56 units left of x), forehead on its
knees; its line pales to 0.62 (`child.a`, `num["a"]`) and comes back with the head lift.
The friend fights from the first attack: `attacks[0]` an arm up against the dark, `[1]` pressed down
(its hand leaves the child); it turns its back to us where it stands; `[2]`, `[3]` two shoves with
both arms; it finds the seam over its head and on `[4]` plunges both hands in (the grips exist from
here); `[5]` a heave apart; it slips (a foot shoots out, the opening half closes), plants its feet
again; `[6]` the great heave. It holds, looking round at the child; the left side gives a little.
The child stirs, lifts its head into the light (`lift`, the rig's choreography, 1.25 s), looks at the
friend's back, stands on `stand` while the friend heaves once more. In the silence the friend holds,
on tiptoe, sagging slowly; the child half lifts a hand and lets it sink, then puts first one hand,
then both, up on the left bunch (`join` .. `join + 1.3`). The friend lets that side go and turns to
the right one; the child turns UNDER its bunch to face left (`turn`, 1 s); each walks its bunch
outward and hangs back on it, feet planted; a look over the shoulders; a breath in (`breath`), one
more pull (`pull`), held from 200.88.

- The friend parts the curtain over its OWN head, at x + d (a hand must show beside or above the
  big head): until the child joins, the opening is at most 200 wide (x + 80 to x + 281) and lies
  right of the child. Slant the shaft to the left so that it lands on the child. `gap`: the seam's
  world x for `num["open"]` only; give `gloom.curtains` the seam `x + d` and `strands=None` (the
  count follows the grips), from the first frame of s08 to the last of the rip.
- `pts`: `grip_l`, `grip_r` (`None` until `attacks[4]`): `curtains(left=, right=)`; `hands_l`,
  `hands_r`: the hands on each (one or two points); `shoulder` (until `attacks[1]`).
- `num`: `open` (0..1), `lit` (0..1 from `attacks[6]`: the shaft on the child), `strain`,
  `tremble` (world units the grips shiver, 0.5 from the great heave, 1.3 in the silence: the grips
  already move by it; `curtains(tremble=D.num["tremble"])`), `a`.
- Faces: the friend is written as `hold_B7` writes it (face -1) until the middle of its first turn
  (`attacks[1]` + 0.57), then face +1 to the end; the child is face +1 until it has turned under its
  bunch (`turn` + 1.0), then -1. From the hesitation before `join` the child's arms go up behind its
  head (the rig's `over = -1`), as in B8.

Framing: B8's camera (zoom 0.85, figures 325 px): the fight is all body; the friend is seen from
behind from 185.7 to 197.7 (no face). 0.07 ms.

## 7. s09: colour (201.25 to 226.76)

`s09(t, x=X5, y=FLOOR, d=180, x9=X9, house_x=None, ground=None, **S09_T)`

`S09_T = dict(rip=201.25, look=203.30, go=205.015, hits=HITS_3, house=210.265, push=210.78, on=211.765, back=213.35, turn=214.60, smile_f=216.07, smile_c=217.33, join=217.72, ring=217.84, string=223.5)`

At `rip` the strands go slack: both are thrown back toward each other, their arms left reaching out
to where the strands were (a foot shoots back; they end 208 apart, at x - 14 and x + 194), catch
themselves, pant (two breaths more than at rest, dying down
by `go`). At `look` the child turns round toward the friend (through facing us); the friend half
turns, grinning. From `go` they walk right, a step a beat, the friend 208 to 240 ahead and half a
beat ahead in time (its feet fall between the child's): seven steps to the small house. On the way:
both look up after the emptied balloons (`hits[0]`); the friend waves back to the small children
(`hits[1]` + 0.1), the child a small wave of its own 0.4 s later (both low, before the chest). The
house draws on at `house` between them (the child stops 120 left of `house_x`, the friend 120 right
and turns round); both stoop, four hands on its walls, and push (`push`, 0.4 s: `num["push"]`). From
`on` two steps to the top (`x9`, `x9 + d`). The child turns to look back the way they came (`back`),
then turns to the friend (`turn`), who has turned to wait. The friend's smile opens (`smile_f`,
0.9 s); the child's mouth trembles, then its first small smile (`smile_c`), tufts up; the friend
holds a hand out, the child takes it (`join`); the ring opens from there (`ring`). They look about
(down, up), hand in hand; the child reaches back for the string (`string`).

- `ground(x) -> y`: `hills.ground_y` (float or array). `None`: flat at `y`. Both stand on it with
  each foot on the line. `house_x`: default `x9 - 120` (5480): `small_house(house_x, ground_y, split=0.10 * (1 - D.num["push"]))`.
- `pts`: `hands` (the offered hand from `join - 0.4`, then the joined hands), `ring` (from `join`:
  the centre for `day.ring`), `house_l`, `house_r` (two hands each), `string` (the child's far hand,
  from `string - 0.1`).
- `num`: `thrown`, `push`, `smile_f`, `smile_c`, `joined`, `string` (0..1 from `string + 0.3`: it has
  it), `tufts`.

Framing: the walk at zoom 0.75; the first small smile is carried by mouth, lower lids, spark and
tufts and needs the push-in (zoom 1.5: heads 175 px; under 110 px it is lost). 0.16 ms with `ground_y`
(0.68 on the frames the four hands go to the house).

## 8. s10, s11, the window

`s10(t, x9=X9, x10=X10, d=180, ground=None, y=FLOOR, **S10_T)`

`S10_T = dict(part=227.0, run=227.515, jumps=(229.765, 232.765, 233.69), drop=235.75, up=238.75, point=239.5, wave=240.55, leave=241.765, alone=243.6)`

The hands part, the friend turns and is off; they run from `run` to `drop` (a run cycle a beat: a
footfall on every eighth note; 3400 units in 8.2 s, so the steps are three quarters of the rig's):
the friend jumps on `jumps[0]` (the child watches), the child tries it on `jumps[1]` (lower, an arm
out before it; the friend looks back), both on `jumps[2]` (the near arm thrown up and back, over the
hair). At `drop` they drop into the grass where they stop (child at `x10`, friend at `x10 + d`,
turning to face it), legs out, laughing, out of breath (two breaths more than at rest by `up`). At
`up` they stand (the friend first); it points home with its whole outer arm (`point`), waves
(`wave`; an extreme of the swing is on 241.01), turns and walks off right from `leave`, looking back
once over its shoulder, its line fading (`friend.a`; `friend` is `None` from 244.07). The child looks
where it points, waves back as the friend waved (turned toward us, the whole outer arm out at its
side), lets the arm come down slowly (1.05 s), and at `alone` turns to face left (`Act.face` is -1
from `alone` + 0.275; `num["left"]` runs 0..1 through the turn).
- The string is in the child's far hand, low behind its hip (on the grass behind it while it sits),
  all through, so that with the hand-offs' `lean = -110` the string rises behind its head and never
  crosses its face. Swing the lean over to +110 with `num["left"]`; lean it 150 further back while
  `num["speed"]` > 0.
- `ground`: from 242.0 pass the contour as the un-drawing flattens it, `lambda x: ground_y(x, r)` with
  the `r` that `hills()` returns: B10 stands on the flat line (the ground still sinks 2.9 units under
  the standing child between 244.25 and 244.4: that is the un-drawing's own schedule).
- `pts`: `hands` (until `part`), `string` (the hand with the string). `num`: `air_c`, `air_f` (world
  units off the ground: also `Act.lift`), `sit`, `laugh`, `gone` (the friend leaving), `speed`, `left`.

Framing: zoom 0.75 (figures 285 px, heads 88 px). 0.26 ms with `ground_y`.

`s11(t, dx=ROOM3_DX, x0=None, y=FLOOR, **S11_T)` (friend `None`)

`S11_T = dict(walk=244.765, tie=246.32, tight=247.49, walk2=247.765, sit=249.30, lie=249.92, ring=251.41, look=251.83, reach=252.2, grab=252.87, ear=253.6, smile=253.9, wave=255.2)`

Two steps left to the sofa's right end (it stands at `dx + 1062`); it bends and ties the string with
both hands going round each other (`tie`), the knot pulled tight on `tight`; two more steps to the
front of the sofa (`walk2`, to `dx + 800`); it turns toward us and gets up onto the edge of the seat
(`sit`, 0.6 s), then curls down at ease (`lie`, 1.1 s: the rig's `curl_up_pose`, ending in
`CURL_EASE`; the eyes close as the head comes down; asleep it breathes a quarter slower and half as
deep again). At `ring` its eyes open; it looks (`look`), stretches out and rolls onto its back while
the arm that lay under it reaches down in front of the sofa (the rig's `roll_over_pose`, timed here:
the hand is at its lowest at `grab`, the last ring), brings the phone to its ear (`ear`: `LIE_PHONE`),
smiles (`smile`), a small wave of the free hand (`wave`).
- From `sit + 0.30` (the middle of the turn) the ground point is `(CURL_X + dx, SOFA_SEAT_Y)` and the
  face +1: take `x, y, face` from the Act (the picture does not jump: 0.08 world units).
- The phone: an arm is 148 long, so `story.PHONE` (178 below the seat, 125 to the left) cannot be
  reached from the sofa. The hand comes down to `pts["reach"]` (the rig's lowest reach: now
  `(CURL_X + 45.6 + dx, FLOOR - 16.6)`), at the foot of the sofa. Let the phone lie under it in the
  coda (the proofs: at `(reach x, FLOOR + 14)`, the rug's far edge) and let its last ring's hop
  carry it up into the hand over 252.66 to 252.87.
- `pts`: `string` (the hand with the string; the tie point `pts["tie"]` = `(dx + 980, 572)` once
  tied), `reach`, `phone` (the hand that holds the phone, from `grab`:
  `phone_held(F, D.pts["phone"], -1.95, lit=1, warm=1, back=True)`).
- `num`: `tied`, `lying`, `asleep`, `grab`, `at_ear`, `smile`.
- Draw the sofa, then the child, then the cushion, then the string (the child's head covers the
  armrest's top).

Framing: the whole room for the walk and the knot; the push-in on the sofa (zoom 1.3: head 150 px)
for the eyes and the smile. 0.21 ms on average; 0.6 while the rig's moves run (they cost 0.4 a call).

`window_friend(t, dx=ROOM3_DX, t_on=254.45, t_wave=255.0, window=(1571, 448, 56, 70), h=76) -> Act`:
the tiny amber figure in `sets.FAR_WINDOW`: it rises into the window and waves with its whole arm
at its side, a sweep every half beat. Clip it to the window's rectangle, after `R.view(F)`:

```python
W = AP.window_friend(F.t)
with F.clip(rect=(cx - 28, cy - 35, cx + 28, cy + 35)):      # FAR_WINDOW at R.dx
    W.show(F)
```
56 px of it show at zoom 1.3 (head 30 px); the wave is the arm and the lean. 0.005 ms.

## 9. Duet tools, numbers, limits

- `hold_hands(xc, yc, xf, yf, hc=380, hf=388, lift=0.455) -> (point, child grab, friend grab)`: the
  joined hands of two figures standing at those ground points; `figure(..., HOLD-like pose, grab=...)`.
- `eye_to_eye(Pc, Pf, xc, yc, xf, yf, k=1, kf=None) -> (Pc, Pf)`: each one's eyes on the other's head
  (child facing right, friend left); ramp `k` and `kf` a few frames apart.
- `look_to(P, x, y, h, face, target, k=1, head=0.3)`: a profile pose's eyes (and a little its head) on
  a world point.
- `side_by_side(t, x0, x1, start, steps, ground=None, y=FLOOR, gap=170, lead=0.5, m=0.8, x1f=None) -> Duet`:
  the two walking, a step a beat, the friend `gap` ahead and `lead` beats ahead in time. 0.07 ms.
- `run_together(t, x0, x1, t0, t1, ground=None, y=FLOOR, gap=170, lead=0.2, jumps_c=(), jumps_f=()) -> Duet`:
  running, with jumps `((take-off, air time, height in body units, "c" | "f" | "j"), ...)`. 0.07 ms.
- `stand_on(P, x, face, h, ground, y=FLOOR, air=0) -> (pose, y)`: a pose with each foot on a ground
  function.
(`review/tools_*.jpg` show them on their own.)

Measured (`numbers.txt`, `review/measure.py`, `review/checks.py`):
- Hand-offs: section 2. Joined hands, the hand on the shoulder and the grips: 0.000 apart.
- No pops: with the two figures alone on bare paper and the camera locked to them, no frame of s06
  to s11 changes more than 1.8 times its neighbours (the one exception is acted: the knot pulled
  tight, 247.48).
- Feet: one foot is always planted in the walks (the foot that moves least moves under 1 unit a
  frame but for the three or four frames of each change of feet, while the landing foot comes down
  from its heel: up to 4.4 a frame on the hill, 6.7 in the coda); nothing slides while they hang on
  the curtains (198.3 to 201.25: 0).
- Heads: the two head circles never overlap from s06 to s10 (least: 3.2 units at 184.3, 4.2 at 181.05).
- Cost, ms a call, mean / worst frame: `s06` 0.05 / 0.29, `s07` 0.09 / 0.45, `s08` 0.07 / 0.22, `s09`
  0.16 / 0.68, `s10` 0.26 / 0.56, `s11` 0.21 / 0.62; holds 0.02 (B9 0.23, B10 0.14 with `ground_y`).
  Frames over the 0.3 ms budget: 47 of 703, 17 of 765, 4 of 532 and 92 of 431 in `s07`, `s09`, `s10`, `s11`.
- Flicker of the rest states with a bare kit (levels / percent on a boil step; inside a pair): B6
  0.18 / 0.6; 0.03. B7 0.22 / 0.7; 0.05. B9 0.10 / 0.4; 0.02. B10 0.11 / 0.4; 0.02. B8 in the long
  silence: 0 on a boil step, 0.07 inside a pair (breath and the grips' shiver). With the real
  curtains and their light following the shivering grips: 0 and 0.40 (the edges of the opening move
  with the hands; give `curtains` a smaller `tremble` or hold the grips yourself if that is too much).
- The same frame in two processes: identical (ten whole frames of the review scenes, six poses).
- Extreme cameras (zoom 0.26, 1.6), figures cut by the frame, in the lyric band or off screen: no
  error (`review/extremes.jpg`).

Limits:
- A raised arm crosses the big head between about 20 and 40 degrees from the horizontal and hides
  behind it when it is straight up. Every reach here goes low and forward, or out to the side of a
  figure turned toward us, or up BEHIND the head: the pose key `over = -1` (added to `figure.py` for
  this: the near arm is drawn behind the head as the far one is; 0 and 1 are as before).
- Never give the rig's `alive()` a `rate` that changes with time (it multiplies the rate by the
  time: the breath would jump on every frame). This module keeps a phase of its own for that.
- Two heads 180 apart nearly touch. From the friend's crouch in `s06` to B7 the two heads never
  overlap (3.2 world units apart at the least).
- `swap_sides` of the rig is the same picture only for a pelvis over the ground point; this module
  mirrors with its own `_mirror`.
- `s06`: the friend brushes over the child's crown, not its shoulders (they are under its bowed
  head). The hand follows the head only as far as the arm reaches (it reaches the bowed head, not the
  lifted one): keep `t_lift` at `t_take` + 0.4 or later, or the second stroke falls short.
- `s08`: while the child turns under its bunch (197.5 to 198.0) only a hand of it shows above its
  head; the friend's back is to us for twelve seconds.
- `s09`: what the two do in passing (the look up, the waves) is timed to the hits, not aimed at
  where a scene puts the groups. The look back at the top (`back`) is this module's addition.
- `s10`: the child's own jump is low by design; the run's steps are three quarters of the rig's.
- `s11`: the knot is 1.2 s of two hands going round each other; the child is curled by 251.0 and
  the first ring is at 251.41. Between |rot| 0.85 and 0.30 the rig changes the lying figure's legs
  from masses to lines (figure.md, section 11).
- The clips in the proofs folder were rendered but motion was judged on consecutive-frame sheets
  and measurements only.
