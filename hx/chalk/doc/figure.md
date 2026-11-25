# hx.chalk.figure: the two characters

Everything is in the package namespace (`from hx.chalk import *`). Proofs and the script that makes
them: `hx/_review/v4_kit/figure/` (`proofs.py`, `numbers.txt`); test scenes at the film's sizes, cameras
and times, written from this page alone: `review/review.py` there. No lyric text anywhere.

A figure is a `Pose` (a dict of numbers) drawn by `figure()`. The body is solved in three dimensions
and projected flat, so it can turn round, lie down and roll over; every blend of two poses is a
valid drawing. Use seed 3 for the child and 5 for the friend everywhere (`story.CHILD_SEED`,
`FRIEND_SEED`): the seed is their hand.

## 1. Units and the three rotations

Body units: 1.0 = standing height `h` (the child 380 world units, the friend 388). In the body's own
frame x = forward, y = up; the origin is the **ground point** (world `x, y` given to `figure`).

| key | what | values |
|---|---|---|
| `face` (argument) | which way "forward" points on screen | +1 right, -1 left. A mirror: never animate it (see `turn`) |
| `turn` | the body about its own vertical axis, in quarter turns | 0 profile (facing `face`), 0.5 three-quarter, 1 front (facing us), 2 profile the other way, -1 (= 3) back view |
| `hturn` | the head turned further than the body | same unit; about -0.6 .. 0.6 |
| `rot` | the whole flat figure about the ground point | radians; + lays the head toward `face` (lying: about 1.1) |
| `open` | a profile opened a little toward us (spreads shoulders, hips) | 0 .. 1; no effect at `turn` 1 or -1 |

`figure(.., P, face)` and `figure(.., swap_sides(P), -face)` are the same picture; so a turn from
profile right to profile left is `turn` 0 -> 2 with `face` unchanged, then (if a walk follows)
`swap_sides` and `face = -face` on a frame where nothing moves.

Near and far: keys ending in `f` are the limbs on our side in a profile (drawn on top), `b` the far
ones. At `turn` 1 the `f` side is on the `-face` side of the picture; at `turn` -1 on the `face` side.

Proportions (constants, body units): `R_HEAD` 0.155 head radius, `TORSO` 0.27 pelvis to neck,
`UPPER` = `FORE` 0.165 (arms; they were 0.135), `THIGH` = `SHIN` 0.205, `PEL0` 0.414 standing pelvis
height, `SHO` 0.086 and `HIP` 0.045 half widths of shoulders and hips. The top of a standing head is
at 0.975 h.

## 2. figure

```python
figure(F, x, y, h, P, skin="child", face=1, seed=0, a=1.0, grab=None, draw=1.0, t=None, rim=None) -> joints
```

- `x, y`: world ground point. `h`: world standing height. `P`: a Pose.
- `skin`: `"child"` / `"friend"` (night or day skin follows `F.skin`) or a `Skin`.
- `a`: pressure 0..1 (the line being rubbed out as the child walks into the mist: animate it on `F.t`).
- `grab={"f": (X, Y)}` / `{"b": ..}`: pins that hand to a WORLD point (holding hands, an armrest); the
  arm stretches at most 6 percent, then the hand stops short.
- `draw` 0..1: the figure draws itself on (limbs 0-0.45, garment 0.3-0.65, head 0.5-0.8, hair fades in
  0.65-0.8, face fades in 0.86-1). A lying figure is drawn in another order, the back first and the
  limbs one after the other: section 11, "Drawn on".
- `t`: clock of the idle sway of scarf, ponytail and glad tufts; default `F.tb` (stands still in the
  two silences). Leave it.
- `rim=(colour, side[, strength])`: light on one side: `side` +1 from the right, -1 from the left, or
  a direction `(dx, dy)` (y down). A chalk rim on head, garment and limbs and a soft tone inside the
  head. `rim=(C.AMBER, 1, k)` is the friend's light on the child; `rim=(light_col(F), (-0.5, -1), k)`
  a shaft from the upper left. Animate `strength` 0..1 on `F.t`. Costs about 1 ms more.
- Returns WORLD points (arrays of 2): `head neck pel sh_f sh_b el_f el_b ha_f ha_b hip_f hip_b kn_f
  kn_b an_f an_b toe_f toe_b`, `R` (head radius, 0.155 h), `crown` (the top of the skull: where the
  strand leaves; on a standing head also where the scribble's belly rests), `top` (the highest point
  of the head as it is SEEN: the same as `crown` on an upright head, on a lying head the point above
  its centre) and `back` (the top of the back: the highest part of the garment; on a lying figure the
  hump of its back): the two rest points of a figure that lies (section 11), `up` (unit vector
  neck -> head, y down), `mouth` (where a balloon or the voice line starts).
  `pose_joints(P, x, y, h, face=1, kind="child")` gives the same without drawing (0.17 ms; it ignores
  `grab`; `kind="friend"` for the coat's `back`).

Detail follows the height on screen (`h * zoom`) and cross-fades: under 84 px a plain thin line, the
garment one rubbed tone, eyes as two dots under a head radius of 13 px (about 85 px tall); 96-124
px mitts, coloured limbs, the scarf band; 130-170 px the inner hatching; lids, bags, brows, the
spark from a head radius of 24-32 px (155-205 px tall). The 78 px child and the 60 px friend still
read (hair cap, jumper / coat, scarf, ponytail): `ladder_night.png`, `film_plain_far_2x.png`.

## 3. Pose

`Pose(**keys)`, `pose.but(**keys)` (a changed copy). All keys, defaults in brackets:

**Body.** `pel` (0, 0.414): pelvis in the picture, relative to the ground point. `pz` 0: pelvis
sideways (weight on one leg; seen from front or back). `lean` 0: spine angle, + forward. `bend` 0:
spine curl, + hunched (0.45 the trudge, 1.0 the curl). `roll` 0: spine tipped sideways. `neck` 0:
nod, + down (-0.8 .. 0.8). `tilt` 0: head tipped in the picture, + toward `face`. `turn`, `hturn`,
`rot`, `open` (0.7): section 1. `chest` 0: breath, -1 .. 1 (set by `alive`). `press` 0: 0..1, the
crown flattened by a weight resting on it (`crown` comes down by 0.17 R).

**Limbs.** `hf` (0.02, -0.322), `hb` (0.045, -0.318): hands relative to their shoulders (forward, up);
arm length 0.33 (`UPPER` + `FORE`), the mitt adds 0.03. `hfz`, `hbz` 0: hands out sideways (from the
front: arms away from the body). `ef`, `eb` -1: elbow side (-1 behind the arm's line, +1 before it;
blends pass through a straight arm). `ff` (-0.012, 0), `fb` (0.022, 0): feet relative to the ground
point; leg length 0.41. `ffz`, `fbz` 0: feet apart sideways. `kf`, `kb` +1: knee side. `af`, `ab` 0:
foot pitch, + toe up. `front` 0: > 0.5 draws the legs over the garment (knees up). `over` 0: > 0.5
draws both arms over the head (arms raised, hands at the face). These two are layers: they switch
at the half-way point of a blend; switch them while the limb is over the garment anyway.
`lgw` 0, `lgf` (0, 0), `lgb` (0, 0): a LYING figure only (they do nothing while `rot` is under 0.30):
with `lgw` = 1 the near / far leg is laid by the directions of its thigh and its shin as they are
seen (radians, 0 = toward `face`, + = up) instead of by its ankle; `lay_pose` notes the angles of the
pose it makes in `lgf` / `lgb`. It is how `roll_over_pose` swings the knees over at full length
(section 11); leave them alone otherwise.

**Face** (all blend). `look` (0.30, 0): where the face sits in the head, x forward, y up, -1..1 (head
down: y -0.7). `gaze` (0, 0): pupils in the eyes, -1..1. `eye` 1: 0 closed, 0.35 bleary, 0.55 the
child's rest, 1 open, 1.3 wide. `lid` 0: 0..1 heavy lids with bags (the child: 1). `blink` 0: 0..1
on top of `eye`. `joy` 0: lower lids push up, 0.3 soft, 0.6 arcs with a pupil, 1 closed smiling
arcs. `brow` 0: worried (inner ends up). `lift` 0: brows lifted. `mouth` 0: -1 turned down .. 0
flat .. 0.55 small smile .. 1 smile .. 1.5 the friend's wide smile. `mopen` 0: 0..1 (speaking: 0.6
with mouth about 0). `blush` 0: warm cheeks (night: pale amber on the child, so only where the
friend's warmth reaches it; day skins have a little at rest). `spark` 0: a point of light in the
eyes.

**Hair and follow-through.** `hair` 0.5: 0 drooping .. 1 standing up (the child's tufts; the friend's
small sprout of two hairs). `sway` 0: hair, scarf tails, ponytail and coat hem left behind: + = trailing away from
`face` (moving forward, wind in the face), - = thrown forward (a sudden stop); about -1 .. 1; set
by `lag` or by hand. `bob` 0: the same vertically (+ flying up while falling, - pressed down while
rising).

Recipes at head radius 120 px: `faces_child_night.png`, `faces_friend_day.png` (captions give the keys).

| face | keys |
|---|---|
| the child at rest | `eye=0.55, lid=1, brow=0.55, mouth=-0.35, hair=0.08` |
| asleep, clenched / at ease | `eye=0, lid=1, brow=0.75, mouth=-0.35` / `eye=0, lid=0.3, mouth=0.3` |
| bleary | `eye=0.35, lid=1, hair=0.9` |
| eyes fully open (181 s) | `eye=1, lid=0.2, lift=0.3` |
| the first small smile (217.33) | `eye=1, lid=0.3, joy=0.3, mouth=0.55, blush=0.6, spark=0.6, hair=0.9` |
| speaking | `mopen=0.6, mouth=-0.1` (pulse `mopen` 0.2..0.7 on `F.t`) |
| the friend's wide smile | `F_SMILE`: `joy=0.8, mouth=1.4, mopen=0.55, blush=1, lift=0.3` |

## 4. Blending and acting

- `mixp(a, b, w)`: plain blend, w 0..1. 0.004 ms.
- `mixg(a, b, weights, default)`: a weight per key, `default` for the rest.
- `act(a, b, u, ant=0.07, over=0.07, blink=0)`: one acted move, u = 0..1 over the WHOLE move: eyes
  0-0.5, head 0.08-0.66, spine and feet 0.16-0.82, hands 0.26-0.94, mouth 0.34-0.86, hair 0.46-1;
  head and spine dip the other way first (`ant`) and overshoot (`over`); `blink=1` blinks on the way
  (u 0.4). The head lift: `act(STOPPED, LOOK_UP, (F.t - 75.5) / 1.2, blink=1)`. When `rot` or `turn`
  differ (sitting up, lying down) the ankles travel straight, as in `mixs`. 0.02 ms (0.3 ms lying).
- `mixs(a, b, w, feet=True, hands=False)`: `mixp` with ankles (and hands) travelling in straight
  lines in the picture: for poses whose `rot` / `turn` differ much. 0.3 ms.
- `turn_round(a, b, w, lead=0.30, hop=1.0)`: a turn (the `turn` keys of a and b differ) as acting: eyes
  and head lead, the weight dips, the feet are picked up one after the other (`hop=0`: they pivot),
  the hair is left behind. 12 frames (0.4 s) for a half turn; 0.5 s reads calmer. The turn runs
  straight through the numbers, so the numbers choose the way round: `turn_round(STOPPED, BACK_STAND, w)`
  (0 to -1) turns away from us; `turn_round(BACK_STAND.but(turn=3.0), FRONT, w)` (3 to 1) comes round
  through the left profile to face us, and `turn_round(FRONT, STOPPED, w)` then goes on to the right
  (`review/turn_lift_24.png`). Turn -1 and turn 3 are the same picture.
- `swap_sides(P)`: the pose that draws the same picture with `face` mirrored (section 1).
- `rebase(P, dx, dy)`: the same drawing with its ground point moved by (dx, dy) body units as seen:
  `figure(F, x + face*h*dx, y - h*dy, h, rebase(P, dx, dy))` = `figure(F, x, y, h, P)`. To blend a pose
  on the seat with one on the floor, give them one ground point first.
- `aim_hand(P, "f" | "b", point, seen=False)`, `aim_foot(...)`: the pose with that hand / ankle at a
  point in body units from the ground point: before `rot` (as `solve` gives them), or with
  `seen=True` as the figure is seen (use this for lying figures). Works at any turn.
- `solve(P)`: joints in body units, flat, before `rot` and `face` (X toward `face`, Y up): `pel neck
  head sh_* el_* ha_* hip_* kn_* an_* heel_* toe_* tan0 tan1 spine (7, 2) hang hang_s ct st se near`.
  0.06 ms. Keys and names are stable (people.py builds on them); new ones are only ever added.

```python
u = F.seg(12.3, 13.5)                                       # the child wakes and clings (two lying poses: act is right)
P = alive(act(CURL, CLING, u), F.t, 3, blink=0)
figure(F, CURL_X, SOFA_SEAT_Y, CHILD_H, P, "child", 1, seed=3)      # the same ground point before, during and after
```

Between lying and upright, and between lying on the side and on the back, do not blend two poses:
use the moves of section 11 (`sit_up_pose`, `curl_up_pose`, `slide_off_pose`, `roll_over_pose`), which
pass through real breakdown poses.

Two poses that are blended must share a ground point, or the figure jumps where the blend begins:
`rebase` one of them first (as above), never change `x` on the frame the blend starts.

## 5. Alive and follow-through

- `alive(P, t, seed=0, breath=1, blink=1, shift=1, rate=0.27)`: a held pose, alive: breathing (`rate`
  breaths a second: chest, spine, hands; on the TRUE time, so it goes on in the silences), a blink
  about every 3 s (never more than 6 s apart; 0.24 s, sometimes double; deterministic from t and seed), slow weight shifts. Wrap
  every hold: `alive(STOPPED, F.t, 3)`. Pass `blink=0` while an acted blink runs, and through a beat
  that the eyes must carry (a chance blink would close them on it: seed 3 blinks at 217.5 s, a
  sixth of a second after the first smile). 0.007 ms.
  Blinks of seed 3 in the first minute fall near 15.4, 19.2, 23.5, 28.1 s.
- `lag(pose_at, t, x_at=None, h=1, face=1, k=1, dt=0.10)`: follow-through without state: evaluates
  `pose_at` (a function of time giving a Pose) at t and t - dt and sets `sway` / `bob` from the head's
  velocity (plus the travel `x_at(t)` in world units, if given). Hair, scarf tails, ponytail and the
  coat's hem arrive late. 0.16 ms around a walk.

```python
pa = lambda t: act(STOPPED, LOOK_UP, (t - 75.5) / 1.2, blink=1.0)
figure(F, x, FLOOR, 380, lag(pa, F.t), "child", 1, seed=3, rim=(C.AMBER, 1, F.seg(75.5, 76.7)))
```

## 6. Walks and runs

- `walk(ph, m=0) -> (pose, advance)`: ph counts cycles (two steps), m = mood 0 trudge (short dragging
  steps, head hanging, hands heavy) .. 1 light (heel strike, swinging arms). `advance`: body units
  travelled since ph = 0; draw at `x0 + face * h * advance` and the planted foot does not slide.
  Stride of a cycle: 0.48 (m 0) .. 0.72 (m 1) body units.
- `WALK_BEAT` = 1 / 1.5: cycles a second for one step per beat.
- `walk_to(t, x0, x1, h, *, start=None, arrive=None, m=0, rate=None, rest=None, rest0=None) -> Walk`:
  from world x0 to x1 and stop, feet planted all the way (measured: 0.0000 drift): a step out of
  `rest0`, whole steps (their length adapts so the last ends on x1), a step into `rest` (default
  STOPPED for m < 0.5, STAND otherwise). Give `start` or `arrive`; `rate=WALK_BEAT` for a step a beat
  (default 0.62 .. 0.92). `W.pose`, `W.x`, `W.face`, `W.t0`, `W.t1`. At a step a beat a 380-unit child
  covers 122 (m 0) .. 183 (m 1) units a second.
- `walk_away(ph, m=0, toward=False, depth=0.22) -> (pose, advance)`: the walk in back view (or from
  the front): no travel in x; `advance` = body units walked into the depth. Shrink it yourself. The
  cycle begins (ph = 0) with the feet apart: let its first half step grow out of the standing pose.

```python
T0 = 59.26                                                  # the first chorus: into the mist (after the turn-round)
P, adv = walk_away((F.t - T0) * WALK_BEAT, 0.0)
P = mixp(BACK_STAND, P, F.seg(T0, T0 + 0.375))              # out of the standing back view in half a step
s = 1.0 / (1.0 + 0.35 * adv)
figure(F, x, hz + (y0 - hz) * s, 330 * s, P, "child", 1, seed=3, a=0.35 + 0.65 * s)
```

- `run(ph) -> (pose, advance)`: a run with a flight phase (about 1.55 cycles a second; 1.17 body units
  a cycle). The knee no longer flips; the foot leaves the ground where the stance left it.

```python
wt = lambda t: walk_to(t, 250, 840, 380, start=36.27, m=0.0, rate=WALK_BEAT)
W = wt(F.t)
P = lag(lambda t: wt(t).pose, F.t, lambda t: wt(t).x, 380, W.face)
J = figure(F, W.x, FLOOR, 380, P, "child", W.face, seed=3)
```

A cycle pose is a profile; to walk at another `turn`, scale the travel by `cos(turn * pi / 2)`.

## 7. The pose library

Ground point: under the feet for standing poses; otherwise as stated. All are for the child unless
named `F_`; every pose can be drawn with either skin. `poses_child_night.png` shows all of them.

| pose | what | ground point |
|---|---|---|
| `STAND`, `FRONT`, `BACK_STAND` | neutral profile; facing us; back view, head a little down (no face: cap, tufts, hatch) | feet |
| `STOPPED` | standing, head down, heavy lids: the child's rest | feet |
| `LOOK_UP`, `REACH`, `HOLD`, `JUMP` | face lifted; reaching forward and up; hand in hand (the NEAR hand held forward: pin it with `grab={"f": point}`; the far hand is held a little behind the hip, free for the string); in the air | feet (JUMP: the ground under it) |
| `SIT_HUG`, `SIT_LIFT` | on the floor in profile, hugging the knees; the same with the face lifted | floor under the hips |
| `SIT_FLOOR` | on the floor, legs folded, hands in the lap (the phone goes at `ha_f`) | floor under the hips |
| `SIT_SOFA` | on the seat, three-quarter to us, hugging the knees | on the seat: `(x, SOFA_SEAT_Y)` |
| `SIT_EDGE` | on the front edge of the sofa, feet dangling | the FLOOR under the hips: `(x, FLOOR)`; the hips are 0.366 up (a seat 120 units high at h 380); blends straight into `STOPPED` (slides off and stands) |
| `CURL` = `ASLEEP`, `CURL_EASE`, `curl_pose(tense)` | curled on its side facing us, head on the armrest, the back rounded, the knees drawn up before the belly. `CURL` (tense 1, the opening): a tight ball, shoulders up, a fist under the chin, lids clenched; `CURL_EASE` (tense 0, the coda): the back longer and lower, the head lying back, the face soft, a hand hanging off the seat. `curl_pose` costs 0.6 ms: blend the two constants with `mixp` instead | `(CURL_X, SOFA_SEAT_Y)` with `face=1`: head on the right armrest, hips 0.08 h left of the point, the head's centre 0.26 to 0.29 h right of it |
| `CLING` | lying, awake, propped a little, head lifted, both hands clutching the top of the armrest under its chin, eyes half open, hair on end | the same |
| `LIE_UP` | on its back, knees up, feet on the seat, a hand on the belly, looking up at what hangs over it (the face at the top of the head, the pupils up) | the same |
| `LIE_PHONE` | on its back, turned toward us, a hand at the ear (`ha_b`: put the phone there), smiling; `roll_over_pose` (section 11) ends in it | the same |
| `SIT_CURL`, `EDGE_CURL` | `SIT_SOFA` and `SIT_EDGE` written from the curl's ground point (hips 40 / 15 world units left of it): where the moves of section 11 end and begin | the curl's: `(CURL_X, SOFA_SEAT_Y)` |
| `F_STAND`, `F_SMILE` | the friend at ease, hands resting on the coat; the wide smile | feet |
| `F_CALL` | waving with the whole arm (swing `hf` or `aim_hand`) | feet |
| `F_CROUCH` | crouched in front of the sitting child: sitting back on its heels, back upright, hands on the knees. Built for the two-shot of the second chorus (ground points 180 units apart, `face=-1`): its head stays clear of the bowed head of `SIT_HUG` | feet |
| `F_OFFER` | the same crouch, the NEAR hand held out low and open in front of the child's knees (`ha_f`): pin the child's near hand to it, `grab={"f": JF["ha_f"]}` | feet |
| `F_PART` | arms up and apart, looking up, feet wide (holding the curtains) | feet |

The sofa anchors are `hx/story.py`'s (`SOFA_SEAT_Y` = FLOOR - 120, `SOFA_ARM_R`, `CURL_X` = 815). To
blend seat and floor poses give them one ground point first: `rebase(SIT_EDGE, 0, (FLOOR -
SOFA_SEAT_Y) / CHILD_H)` has its ground point on the seat. How a lying figure is drawn, its rest
points, its breath, and sitting up, curling up, rolling over and sliding off the sofa: section 11.

Hand in hand (hand-offs B6 and B9: the child's right in the friend's left) is the NEAR hand of both
figures, the child facing right and the friend facing left: `grab={"f": point}` on both.

```python
JF = pose_joints(F_OFFER, X5 + 180, FLOOR, FRIEND_H, -1)            # 152.4: the friend's open hand
figure(F, X5, FLOOR, CHILD_H, SIT_LIFT, "child", 1, seed=3, grab={"f": JF["ha_f"]})   # 154.4: the child takes it
figure(F, X5 + 180, FLOOR, FRIEND_H, F_OFFER, "friend", -1, seed=5)
```

## 8. Skins

`CHILD_NIGHT`, `FRIEND_NIGHT`, `CHILD_DAY`, `FRIEND_DAY`; `SKINS[name] = (night, day)`. Night: the
child in white chalk, pale face, cold blue hatched jumper, dark-blue cap; the friend in amber
crayon, A-line coat, bob with a ponytail at the back of the head, scarf with two lagging tails.
Day (warm paper): the same two in soft pastel from the palette: pencil-slate line, `C.SKIN` face
and arms, `C.JUMPER` / `C.COAT`, slate trousers, `C.CORAL` scarf, `C.ROSE` cheeks; softer and
thinner outlines, no rub-out halo. `Skin(**fields)`: copy one and change fields for a variant
(`import copy; s = copy.copy(CHILD_NIGHT); s.garment = ...`): `kind line arm leg hand shoe garment
garment2 face face2 hair hair_line feature knock blush blush0 scarf edge grain halo soft`.

## 9. Cost (ms, one core; `numbers.txt`)

| | 380 px | 250 | 150 | 100 | 78 | 60 |
|---|---|---|---|---|---|---|
| child night / day | 5.7 / 6.6 | 5.2 / 6.0 | 4.2 / 5.0 | 3.2 / 4.0 | 1.9 / 2.0 | 1.8 / 1.9 |
| friend night / day | 6.1 / 6.5 | 5.4 / 5.9 | 4.9 / 5.4 | 4.0 / 4.4 | 2.1 / 2.2 | 2.1 / 2.2 |

Over the 7 ms budget at 380 px: a figure with a rim (7.4), the friend's wide smile `F_SMILE` (7.1; a
second measurement on a busy machine gave 7.2 night, 7.6 day), and every close-up: 760 px tall (head
radius 118 px) costs 7.7 (child) to 9.5 (friend, wide smile). Pose maths is negligible beside the
drawing: `solve` 0.06, `act` 0.02 (0.3 lying), `walk_to` 0.03, `lag` 0.18.

Flicker of held, breathing figures (static camera): 0.11 levels / 0.4 percent on a boil step for
one figure, 0.15 / 0.5 for both, 0.02 to 0.03 inside a pair (the breath); in the silences the boil
step is exactly 0 and only the breath and the blinks of `alive` move (0.014 levels inside a pair for
one figure, 0.06 on a blink); a figure that is not wrapped in `alive` is exactly still there. The same
frame rendered in two processes is identical.

## 10. Limits

- The projection is flat: no perspective. A foot or hand further from us is not drawn higher except
  in `walk_away` (its `depth`). Seen from the front, legs and arms that move forward only shorten.
- `front` and `over` are layer switches (a limb jumps over or under the garment at the half-way
  point of a blend); between `turn` 0.42 and 0.52 the arms cross-fade from behind the garment to
  over it (two or three frames of a turn; the copy that fades in rubs nothing out, so a hand never
  goes grey on the way).
- At `turn` near -0.4 (turning away) the face leaves over the edge of the head in about 0.2 turns;
  hold poses there only briefly.
- Lying poses are built for `face=1` on the sofa's right armrest; mirrored (`face=-1`) they work on
  a left armrest at `2 * centre - CURL_X`.
- Hands are mitts: no fingers, no grip. Things held are drawn by the scene at `ha_f` / `ha_b`.
- Lying: section 11 ends with its own limits.

## 11. Lying: the child on the sofa

Proofs: `hx/_review/v4_kit/lying/` (`proofs.py` makes them in the real room with the real light and
scribble; `numbers.txt`). Look at `framings_100.png`, `poses_night_close.png`, `poses_sunset_close.png`,
`before_after_open_pair.png`. The reviewer's scenes, written from this section alone (the film's
cameras and times, and the child as `acting_child.s01` plays it): `review/review.py` there, and
`review/look.py` (the same as strips at 100 percent: `look_open.png`, `look_poses.png`,
`look_drawon.png`, `look_situp.png` ...); `review/upright_check.py` compares every upright pose with
the sheets made before this construction existed (identical to the pixel), `review/pops.py` looks
for pops along the moves, `review/determinism.py` prints frame hashes (the same in two processes).

### How a lying figure is drawn

A figure laid down by `rot` is drawn with mass instead of sticks. Nothing to call: it follows `rot`
alone (it begins at |rot| 0.30 and is complete from 0.85), so upright poses draw exactly as before
and every blend between lying and upright passes through it smoothly. What changes:

- the garment becomes **one rounded shape that lies on the surface**: its upper side stands out as
  the back (or, on its back, the belly), its lower side is laid flat on the seat, the hem end is
  rounded off; the jumper's zigzag runs across it and follows the curve;
- the legs become **trouser legs**: two tapering shapes each (thigh over shin), a plain slate tone
  with a chalk outline at night (the friend's: its own amber, darker), the skin's `leg` colour by
  day; arms stay lines with mitts, a fifth wider than an upright figure's (in the day skins with
  more of the skin's colour in them), so that they hold their own beside the body;
- knees and elbows **fold in the picture** at full length (no foreshortened stubs); a knee never
  sinks into the surface (it turns toward us instead), and no toe or heel goes under the surface of
  any figure with `rot` != 0 (the foot shortens instead). While the body rolls through facing us
  (`turn` 0.8 to 1.2) the folds pass through the limb seen end on, so nothing flips;
- `rim=` lights the side of the body that is turned to the light as it is seen;
- the surface is the ground point's level: lay the pose so that the seat is at y = 0 from its ground
  point (all library poses are).

Lying poses are written as they are SEEN, in body units from the ground point (x toward `face`, y up,
the seat at y = 0). `lay_pose(P, pel, lf=None, lb=None, hf=, hb=, ff=, fb=) -> Pose` does it: the
pelvis at `pel`; `lf` / `lb` = (thigh, shin): the near / far leg folded by two angles in degrees
(0 = toward `face`, 90 = up; `CURL`: (-7, 190) and (4, 191)); `ff` / `fb` instead: the ankles at
seen points; `hf` / `hb`: the hands at seen points. Give `P` its `rot`, `turn`, `bend`, face and
foot pitch first (`af` = `rot` - 3.1 lays a foot flat along the seat, toes away from the head).
0.45 ms: build such poses once, at import. For a variant of a library pose `aim_hand(P, "f", point,
seen=True)` and `.but(...)` are enough (face keys, `neck`, `tilt`, `bend`, `press` all work as on an
upright figure). `mixp` / `act` between two poses that lie the same way are valid at every weight
(`blends_6.png`): tense to ease, curl to cling. From the side onto the back use `roll_over_pose`
(below): a plain blend of the two tumbles (the third row of `blends_6.png`).

```python
L_PROPPED = lay_pose(CURL.but(rot=0.92, bend=0.88, neck=0.26, eye=0.3), (-0.080, 0.080),
                     ff=(-0.094, 0.058), fb=(-0.056, 0.026), hf=(0.088, 0.014), hb=(0.185, 0.016))   # both hands on the seat
```

### Where the scribble rests

`J = figure(...)` (or `pose_joints`) gives two world points for the cloud's belly, moving with the
pose and with the breath: `J["back"]`, the top of the back's hump (CURL: (820, 492), 130 units above
the seat), and `J["top"]`, the highest point of the head as it lies (CURL: (913, 492)). `J["crown"]`
is the top of the skull, which on a lying head points sideways (CURL: (972, 559), beyond the
armrest's edge): the strand leaves there. `press` flattens the skull's top as before.

```python
J = figure(F, CURL_X, SOFA_SEAT_Y, CHILD_H, alive(CURL, F.t, 3), "child", 1, seed=3)
k = F.ramp(13.3, 15.2)                                     # the belly comes down onto the child
gloom(F, 730, 308, 440, 156, seed=4, loops=46,
      rest=[(J["back"][0], J["back"][1] + 4, k), (J["top"][0], J["top"][1] + 6, k)])
```

### Asleep and alive

`alive(P, F.t, 3)` works on every lying pose. On a lying figure the breath lifts the back and leaves
the head where it rests: with `alive(CURL, t, 3)` the top of the back rises and falls by 6.7 world
units (6.4 px at the whole-room framing: `breath_8_wide_2x.png`, `breath_difference_2x.png`), the
head moves 1.3; on the true time, so it goes on in the silences. Weight shifts are a third of an
upright figure's. A chance blink does nothing while `eye` is 0. `breath=1.5` for a deeper sleep (the
coda's slow breath), `rate=0.2` for a slower one.

### Drawn on

`figure(..., draw=d)` on a lying figure (9.27 to 11.3 s: `draw=F.seg(9.27, 11.3)`) draws it as a hand
would, one thing after the other, the tip leading:

| d | what |
|---|---|
| 0 to 0.22 | the back, as one line that closes into the body |
| 0.17 to 0.48 | the limbs, one by one: the far leg (0.17 to 0.275), the near leg (0.245 to 0.35), the far arm (0.33 to 0.41), the near arm (0.39 to 0.48). A leg is the thigh's outline, then the shin's, the foot last; the trousers' tone is rubbed in after the line. An arm is its line, then the mitt |
| 0.30 to 0.65 | the jumper's zigzag, row by row from the hem to the neck |
| 0.50 to 0.80 | the head's line; its tone comes in from 0.62 to 0.755; hair 0.65 to 0.80 |
| 0.86 to 1 | the face with its closed heavy lids |

At the storyboard's two seconds a limb takes five to six frames; give `draw` more time (or ease it)
for a calmer hand. Upright figures are drawn on as before (section 2). `draw_on_12_wide_100.png`,
`draw_on_12.png`; every frame of the limbs: `review/look_drawon_30.png`.

### The moves: sitting up, curling up, sliding off, rolling over

Each is a function of `w` = 0..1 giving a pose that is a valid drawing at every w and passes through
real breakdowns. They are SPACE only: the timing is yours (ease w, hold on a breakdown, run a part
faster; a little anticipation and overshoot on `neck` / `bend` on top; wrap the result in `alive`).
Call them with a continuous w (or sample them densely once, 30 places or more, and blend neighbours
with `mixp`); do not blend two samples that lie far apart. 0.25 to 0.4 ms each.

- `sit_up_pose(w) -> Pose`: from `CURL` (w 0) to `SIT_CURL` (w 1: `SIT_SOFA`, hugging its knees). Draw
  every w at the curl's ground point `(CURL_X, SOFA_SEAT_Y)`. Breakdowns at w 0.24 (the hands come
  down onto the seat and take the weight), 0.50 (the back comes up over the hips, the legs still
  lying folded, the head still hanging), 0.76 (the feet are gathered in, the knees come up, the
  hands go round them); the head comes up last. `move_sit_up_16.png`.
- `curl_up_pose(w) -> Pose`: the coda, from `EDGE_CURL` (w 0: `SIT_EDGE` on the front edge of the
  seat, feet dangling) to `CURL_EASE` (w 1). Same ground point. Breakdowns at w 0.30 (the legs are
  drawn up onto the seat, a hand reaches for the seat beside the armrest), 0.56 (it lets itself down
  sideways onto that hand, the legs folding in), 0.80 (lying, the head still up: it goes down last;
  then the near hand slips off the seat). `move_curl_up_16.png`.
- `slide_off_pose(w, dx=225 / 380, seat=120 / 380) -> (pose, dx, dy)`: from `SIT_CURL` on the seat to
  `STOPPED` on the floor, `dx` body units further toward `face` than the curl's ground point (the
  default lands on `story.X1` = 1040) and `seat` below it. Draw every w at `(x + face * h * dx,
  y - h * dy)` where (x, y) is the curl's ground point: that is the floor point where it will stand,
  from the first frame on (at w 0 it is exactly the drawing of `SIT_CURL` at the curl's point).
  Breakdowns at w 0.34 (on the front edge, feet dangling), 0.66 (feet down, bent forward, a hand
  pushing off the armrest). `move_slide_off_16.png`.
- `roll_over_pose(w) -> Pose`: the coda's last action, from `CURL_EASE` (w 0) onto its back and to
  `LIE_PHONE` (w 1). Same ground point. Breakdowns at w 0.12 (awake: the eyes open, the head lifts a
  little), 0.30 (the folded legs come off the seat: the knees begin to swing up), 0.45 (rolled to
  face us, the knees up over the belly, the mouth open), 0.64 (THE REACH: on its back, knees up,
  leaning over, the head dipped, the arm that lay under it hanging straight down in front of the
  sofa: the hand `ha_b` is then at (CURL_X + 46, SOFA_SEAT_Y + 103): 17 world units above the floor
  line, as low as this child's arm gets), 0.83 (the hand on its way up, the smile beginning). The
  legs are laid by the directions of thigh and shin all the way (the pose keys `lgw`, `lgf`, `lgb`),
  so the knees swing over at full length: nothing flips and nothing shortens. `move_roll_over_16.png`.
  The reach does NOT get to the phone where it lies on the rug (`story.PHONE` is 171 units to the
  left of that hand and 75 lower): the scene must have the ringing phone under the hand (the rug's
  far edge is at y 759 there), or bring it to the hand. From w 0.64 on the phone is in the hand:
  `phone_held(F, J["ha_b"], ...)`.

In all four the ankles and the hands travel on smooth paths as they are seen (a hand planted in two
neighbouring breakdowns stays planted while the body turns over it). No knee, ankle or toe goes
under the seat line while the child is on the seat: rolling over they stay 4 world units above it;
sitting up a toe dips 2.8 under it near w 0.95 (less than the line is wide); curling up the feet
dangle from the edge by design until w 0.28 and are on the seat from there on. Largest step of any
joint (elbows included) for dw = 0.005, in world units: 1.6 sitting up, 2.7 curling up, 4.9 rolling
over (the reaching hand on its way up), 6.3 sliding off (an elbow in the last hundredth, where the
arm straightens into `STOPPED`; everything else there under 2.5) (`numbers.txt`). No pops: played
in 2.2 to 2.6 s with the boil held, the picture's change from one film frame to the next is never
more than 1.1 times its neighbours' (`review/pops.py`; the layer flags switch where the limbs lie
over the garment anyway). `clip_sit_up_4s.mp4`, `clip_curl_up_4s.mp4`, `clip_slide_off_4s.mp4`,
`clip_roll_over_4s.mp4` play them with a plain ease.

```python
u = F.seg(22.0, 24.2)                                      # the child sits up (retime u as you like)
P = alive(sit_up_pose(ease(u)), F.t, 3)
figure(F, CURL_X, SOFA_SEAT_Y, CHILD_H, P, "child", 1, seed=3)

P, dx, dy = slide_off_pose(ease(F.seg(33.6, 36.0)))        # off the sofa, standing at X1 (hand-off B1)
figure(F, CURL_X + CHILD_H * dx, SOFA_SEAT_Y - CHILD_H * dy, CHILD_H, alive(P, F.t, 3), "child", 1, seed=3)

P = alive(curl_up_pose(ease(F.seg(247.6, 250.2))), F.t, 3, breath=1.5)       # the coda (the room at ROOM3_DX)
figure(F, CURL_X + ROOM3_DX, SOFA_SEAT_Y, CHILD_H, P, "child", 1, seed=3)

w = ease(F.seg(251.4, 253.6))                              # the phone rings: it rolls over, reaches down, answers
J = figure(F, CURL_X + ROOM3_DX, SOFA_SEAT_Y, CHILD_H, alive(roll_over_pose(w), F.t, 3, blink=0), "child", 1, seed=3)
if w >= 0.64:                                              # (before that the phone lies under where the hand comes down)
    phone_held(F, J["ha_b"], -1.95, lit=1.0, warm=1.0, back=True)
```

To change the face on the way (the coda's child is at ease, not tired): `P.but(mouth=..., brow=...)`
on the result, or `mixg` it toward a face of your own.

### Cost and flicker (`numbers.txt`)

A lying figure, ms (night / sunset skin, 10 calls after a warm-up, machine load about 3; with more
renders running the same calls measured up to 1 ms more): at the whole-room framing (zoom 0.95)
`CURL` 6.1 / 6.7, `CURL_EASE` 6.3 / 6.6, `CLING` 6.1 / 6.8, `LIE_UP` 6.0 / 6.7, `LIE_PHONE` 6.7 / 7.0; at
the push-in (zoom 1.27) 6.4 to 7.4 / 7.0 to 7.5 (`LIE_PHONE` and `CLING`, with both arms over the
head, are the dearest). Closer than the film goes (zoom 2.2): 8.7 to 9.9. A standing figure at zoom
0.95 is 5.5. `solve` of a lying pose 0.08 (standing 0.06), `pose_joints` 0.17, half-drawn
(`draw=0.5`) 3.3. The moves: `sit_up_pose` 0.38, `curl_up_pose` 0.37, `roll_over_pose` 0.39,
`slide_off_pose` 0.25, `curl_pose` 0.6, `lay_pose` 0.45.

The sleeping child, static camera: alone on bare paper 0.04 levels / 0.14 percent on a boil step,
0.007 inside a pair (the breath); in the silences exactly 0 on a boil step. The whole night room
with the child: 0.51 levels / 1.8 percent; the push-in 0.67 / 2.2.

### Limits

- A roll between lying on the side (`turn` 0.6) and on the back (`turn` 1.6 to 2: `LIE_PHONE`,
  `LIE_UP`) is a real turn of the body. `roll_over_pose` is the one built move (`CURL_EASE` to
  `LIE_PHONE`); any other (`act(CLING, LIE_UP, u)`) is a plain blend and tumbles for about a third
  of the way (legs swinging over, an arm across the face): run it in under half a second, cover it
  with the cloud, or build its breakdowns as `roll_over_pose` does (figure.py, `_RO_A` .. `_RO_F`).
- In `roll_over_pose` the picture changes most between w 0.45 and 0.60 (the roll onto its back, the
  arm dropping off the seat) and between 0.70 and 0.80 (the hand coming up), three times as fast as
  at its ends: time w with that in mind.
- `swap_sides` is for upright poses: it leaves `rot` and the laid legs (`lgf`, `lgb`) as they are.
  To lie the other way round draw the same pose with `face=-1` (section 10).
- The trouser legs exist only while the figure lies; between |rot| 0.85 and 0.30 they thin into the
  upright figure's line legs (white chalk at night), and the jumper's two zigzags cross-fade
  (the body is a little paler for those frames). In `sit_up_pose` that is about a quarter of the
  move (22.8 to 23.35 s as `acting_child.s01` plays it; the legs change during about ten of those
  frames: `review/look_film_legs.png`); it reads as the legs coming out from under the body, but it
  is a change of drawing. Coming on, the trousers' tone leads their rub-out, so nothing pale shows.
- Arms are lines with mitts, also on a lying figure (a fifth wider there). The near arm's shoulder
  is the upper one, 105 world units above the seat: its hand gets no further than 35 units under
  the seat line. A hand that must hang or reach lower is the FAR hand (`hb`; its shoulder is 50 to
  60 above the seat: it reaches 75 under the seat line lying on the side, 103 in the lean of
  `roll_over_pose`). A hand aimed out of reach stops short on a stiff straight arm.
- The head of `CURL` covers the armrest's top from x 854 to 972, of `CURL_EASE` from 865 to 983
  (the armrest is `story.SOFA_ARM_R` = 886 to 990): something tied to the armrest (the string of
  the coda) shows only at its outer edge, or must be drawn after the child.
- `a` below 1 (a paling line) is not tuned for a lying figure (the film never pales it there): the
  rubbed halo of the limbs stays dark.
- The far hand of `CURL` is tucked under the chin, of `CURL_EASE` under the cheek (hidden by the
  head). Pinning it with `grab={"b": ...}` far from there shows the whole far arm over the garment.
- `sit_up_pose` and `slide_off_pose` carry the tired face of `SIT_SOFA` / `STOPPED`, `curl_up_pose`
  begins with the tired face of `SIT_EDGE`: set the coda's face yourself.
- The surface is assumed flat at the ground point's level; the armrest is not known to the figure
  (hands and head are placed on it by the pose numbers, for a sofa built to `story.py`).

## Two notes added after the acting was written

- Pose key `over`: 0 = the near arm in front of the body, 1 = raised in front of the head, **-1 = the
  near arm drawn behind the head** (as the far arm is): for two figures holding something up behind
  their heads so that both faces stay seen (the curtains at 198 to 201 s).
- `alive(P, t, seed, rate=...)`: `rate` multiplies the time, so it must be a constant for a stretch of
  holding. Never pass a rate that changes with time (the breath would jump); change the phase instead
  (acting_pair's `_breaths` shows how).
