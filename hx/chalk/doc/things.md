# hx.chalk.things: the small things that carry the story

`from hx.chalk.things import *`, written AFTER `from hx.chalk import *` (the package does not
import this module yet). `wall_drawing`, `phone` and `crow` here then replace the prototype's in
`props.py`: same leading arguments, better drawing, with two differences. The wall drawing's part
names are `pic.l.sheet`, `pic.r.sheet`, `pic.l.fig0.body` ... (props had `pic.left`, `pic.right`,
`pic.fig0.*`), and the phone's `lit` is its SCREEN, cold by default: `warm=1` makes it amber (in
props `lit` was an amber glow).

Where things are in a figure: this module knows no figure. Take the mouth, an ear or a hand from the
joints `figure` returns (`J["head"]`, `J["R"]`, `J["ha_f"]`). The proofs put the mouth of a 380-unit
child in profile at `(head_x + face * 32, head_y + 23)` (about 0.55 R forward, 0.4 R down); the
acting artists' docs give exact points.

World coordinates through `F.cam`, y down, angles in radians, sizes in world units. Nothing keeps
state; every random number is a hash of a `seed`. Two kinds:

- **builders** return a `Sketch` of named parts (`family`, `wall_drawing`, `tape`, `hero`,
  `balloon`): give them times (`on_beats`, `spread`, `set_off`), let them take part in a `morph`,
  then `.draw(F)`. They take no Frame, so those with two skins take `day=` (pass `F.day`).
- **drawn at once** with `F`: everything else. They follow `F.skin` and return the points a scene
  needs (a hand, a tip, where light comes from).

Clocks: an argument that ACTS (`u`, `d`, `w`, `fall`, `tear`, `taped`, `lit`, `pop`, a flap count)
is yours to drive from `F.t`. What is merely ALIVE (a crow shifting, the string swaying, the voice
wavering, a bubble wobbling) runs on `F.tb` by default (`t=None`) and stands still in the two
silences. The moth's wings and the phone's rings run on true time.

Costs are ms per call at 1080p on one core (median of 10; `hx/_review/v4_kit/things/cost.txt`).
Proofs and the script that makes them: `hx/_review/v4_kit/things/` (`proofs.py`); a second set of
test scenes written from this doc alone, and the measurements: `hx/_review/v4_kit/things/review/`
(`scenes.py`, `measure.py`).

## 1. The family drawing

The child's drawing: two tall figures and a small one between them, hand in hand, a corner sun, a
scribbled ground, on a sheet of pale paper. `SHEET = (150, 112)`: its size in its own units, times
`s` in the world. The tear is one jagged line (a function of `seed`, default 300 everywhere): the
same in every state. It runs through the small figure; each half keeps half of it.

```python
family(x, y, s=1.0, tear=1.0, gap=0.0, askew=0.0, rot=0.0, taped=0.0, pins=False, detail=1,
       day=False, seed=300, a=1.0, name="pic") -> Sketch
```
- `(x, y)` centre; `rot` turns the sheet.
- `tear` 0 whole .. 1 torn through; in between the rip has run that far down from the top edge
  (53.14 and 53.51: `0.5 * F.ramp(53.14, 53.30) + 0.5 * F.ramp(53.51, 53.67)`).
- `gap`, `askew` (only when torn through): how far apart the halves hang, in sheet units, and how
  much each has dropped about its pin (rad).
- `taped` 0..2: strips of amber tape across the tear, each laid from left to right
  (`F.seg(165.63, 165.87) + F.seg(166.39, 166.63)`: one strip per attack, 7 frames each).
- `pins`: two pins (on a wall). `detail`: 0 the bare sheet (far away, under about 60 px), 1 the
  figures (the wall, 100 to 200 px), 2 their faces too and lines that boil (from about 200 px).
- `day`: warm paper, pencil, pastel (the coda).
- Parts: `l.*` and `r.*`, the two halves: `sheet` (rim), `sheet.fill`, `shade`, `fig0.body`
  `fig0.dress` `fig0.arms` (left tall one), `fig1.body` `fig1.jumper` (its half of the small one),
  `fig2.body` `fig2.arms` (right tall one), `sun`, `ground`, with detail 2 `figN.eye_l` `figN.eye_r`
  `figN.smile`, and `edge` (pale fibres of the torn edge); `tear` (the rip where the halves touch);
  `tape0.*` `tape1.*`; `pin_l` `pin_r`. A whole sheet (`tear < 1`) has one `sheet.fill` and `shade`.
  For a morph pair the two rims: `("pic.l.sheet", ...)`, `("pic.r.sheet", ...)`.

```python
wall_drawing(x, y, s=1.0, gap=9.0, taped=False, seed=300, rot=-0.05, askew=0.07, day=False,
             detail=1, name="pic") -> Sketch
```
The drawing as it hangs on the wall: torn, the halves `gap` apart and askew, each on its pin; with
`taped=True` (or a number 0..2) mended, the tear still showing. At `story.WALL_DRAWING`, s = 1.

```python
family_held(F, hand_l, hand_r, s=0.8, taped=0.0, a=1.0, detail=2, seed=300, day=None, droop=1.0) -> dict
family_half(F, side, x, y, s=0.8, rot=0.0, a=1.0, detail=2, seed=300, day=None, grip=None) -> (x, y)
```
- `family_held`: the two halves in two hands (world points; `hand_l` holds the left half). Each
  half hangs from its hand by its outer lower part. Hands `124 * s` apart: the halves meet and the
  picture is whole but for the tear. Nearer: they stay together between the hands. Further: each
  follows its own hand and its torn edge drops (`droop` scales that). Animate the two hand points
  (pin the figure's hands to them with `grab`). Returns `{"c": middle of the tear, "gap": distance
  between the halves, "ang": angle of the sheet, "tape": [(p0, p1), (p0, p1)]}` (world ends of the
  two strips, for the hand that lays them).
- `family_half`: one half (`side` -1 left, +1 right) held at a world point, turned by `rot`.
  `grip=(u, v)` in sheet units says where it is held ((0, 0) = the middle of the whole sheet;
  default the outer lower part). Returns the middle of its torn edge. For falling out of the jumper
  and being gathered up (135.6 to 137.0).

Costs: wall (detail 1) 1.9, taped 2.3; held at film size (detail 2, zoom 1.9: a 230 px sheet) 2.6,
taped 3.1; a 345 px sheet with faces: whole 2.6, torn 3.0, taped 3.5; far (detail 0) 0.9; one half
1.4. The close taped states are over the 3 ms budget: nothing else of this module is on screen then.

```python
# 55.01: held together; 55.27 and 55.72: the grip loosens and they drift apart
apart = 26 * F.ramp(55.27, 55.6) + 34 * F.ramp(55.72, 56.2)
hl, hr = (cx - 50 - 0.55 * apart, cy + 24), (cx + 50 + 0.45 * apart, cy + 24 + 14 * F.ramp(55.72, 56.2))
J = figure(F, 900, 742, 380, pose, "child", seed=3, grab={"b": hl, "f": hr})
family_held(F, hl, hr)                                  # s = 0.8: the hands meet the sheet 99 apart

# 167.1 to 170.7: let go, it rises and shrinks and stays far off, pinned (choose detail by its size)
u = ease(F.seg(167.1, 170.7))
family(cx + 260 * u, cy - 430 * u, 0.8 * (1 - 0.72 * u), taped=2, rot=-0.1 * u, pins=u > 0.95,
       detail=2 if u < 0.3 else 1 if u < 0.8 else 0).draw(F)
```
Tucking a half into the jumper: move a `family_half` to the chest while its `s` and `a` go down over
6 frames or more (there is no fold). The paper is rigid: the halves do not bend.

## 2. Tape

```python
tape(x0, y0, x1, y1, w=13.0, d=1.0, seed=560, a=1.0, day=False, name="tape") -> Sketch
```
A strip of amber tape from (x0, y0) to (x1, y1), `w` wide, both ends torn. `d` 0..1: how much has
been laid (it grows from the first point). Parts: `strip.fill`, `strip`, `shine`. Rebuild it every
frame with the current `d` (do not use `on` times: it is short). 0.2 ms. The house halves of the
last chorus get one: `tape(xa, ya, xb, yb, 30, F.seg(t, t + 0.25), day=F.day).draw(F)`.

## 3. The hero with a cape (16.5 to 18.0)

```python
hero(x, y, h=150.0, wave=0.0, face=1, seed=340, col=C.CHALK, a=1.0, name="hero") -> Sketch
sketch_tip(S, t) -> (x, y) | None
```
A small figure of the child itself (the same tufts), in one thin bright line: mask, grin, a fist
raised, a fist on the hip, a cape flying out behind. Feet on (x, y), `h` to the top of the hair;
it stands inside x - 0.68 h .. x + 0.36 h (mirrored by `face`), y - 1.14 h .. y.
`wave` -1..1 swings the free end of the cape: rebuild the set every frame with the new value.
Parts in drawing order: `head hair mask eye_b eye_f grin body leg_b leg_f arm_hip arm_up fist
cape.fill cape`. 2.7 ms.
`sketch_tip(S, t)`: the world point of the chalk tip of whatever stroke of a Sketch is being drawn
at time t (by its `on` times), else None: pin the drawing hand to it.

```python
# on the wall above the sofa's right arm; x 965 keeps it clear of the wall drawing (x 1065 to 1215)
S = hero(965, 425, 150, wave=math.sin((F.t - 18.0) * 2 * math.pi / 1.5) * F.ramp(18.0, 18.4))
S.spread(16.5, 1.32 / 13, 0.18)          # a stroke at a time, the tip leading; complete at 18.0
S.set_off(21.9, 23.2)                    # wiped (after the scribble's three zigzags have crossed it out)
S.draw(F)
tip = sketch_tip(S, F.t)
figure(F, 760, 742, 380, pose, "child", seed=3, grab={"f": tip} if tip else None)
```

## 4. The speech balloon and the soap bubbles

```python
balloon(x, y, rx=105.0, ry=74.0, mouth=None, seed=820, col=None, a=1.0, lw=3.4,
        on=None, off=None, name="balloon", day=False) -> Sketch
BALLOON_FREE = 0.62
```
An EMPTY balloon centred (x, y) with radii rx, ry. Its tail points at the world point `mouth` and
stops short of it; the line starts at the tail's tip, so it draws itself out of the mouth.
`on=(t0, t1)` draws it (the inside is rubbed clean as the line closes), `off=(t0, t1)` wipes it;
or set times on the parts `shape`, `shape.fill` yourself. The ellipse `BALLOON_FREE * (rx, ry)`
about (x, y) stays free: the knot of scribble goes there. To make it rise, move (x, y) and rebuild.
`col`: default cold chalk; `day=True` (pass `F.day`): pencil line, the inside rubbed back to the warm
paper (without it the inside is rubbed to the NIGHT paper, a dark patch on a warm sheet). 0.6 ms.

```python
bubble(F, x, y, r, t=None, seed=0, a=1.0, pop=0.0)
float_up(x0, y0, age, seed=0, rise=46.0, sway=16.0) -> (x, y)
```
`bubble`: a soap bubble, pale, with a sheen; wobbles slowly on `t` (default `F.tb`). `pop` 0..1: it
bursts (dashes flying out; give it 6 to 8 frames). Night: pale chalk; day: a breath of pastel.
`float_up`: where a bubble let go at (x0, y0) is `age` seconds later (rising, swaying). 0.16 ms.

```python
age = F.t - 207.4                         # a balloon of the last chorus has emptied: it floats off
if age >= 0:
    bubble(F, *float_up(bx, by, age, seed=2, rise=60), 50, seed=2, pop=F.seg(210.6, 210.85))
```

## 5. The voice line (40.3 to 42.6)

```python
voice_line(F, x0, y0, x1, y1, w=1.0, fall=0.0, floor=756.0, reach=0.72, t=None, seed=860,
           col=None, a=1.0, lw=3.0, dark=0.0, amp=1.0) -> (x, y)
```
A thin wavering line from the mouth (x0, y0) toward (x1, y1), in the child's own white chalk
(`col`: default `C.CHALK`, pencil by day). `w` 0..1: how far it has come out; it stops at `reach`
of the way (it falls short: aim (x1, y1) at whoever does not answer). `fall` 0..1: it gives up:
from the far end backward it sinks, hanging in a belly, and lies on the floor in slack curls (world
y = `floor` +- 8: by default a little in front of the ground line; it is drawn together to 0.9 of
its length); at 1 it has let go of the mouth. Bursts of a fine shiver travel out along it while it
speaks (clock `t`, default `F.tb`); `amp` scales the waver. `dark` 0..1 turns it dark (on its way
to the scribble). Returns its far end. Aim it clear of other pale lines of the set (a board's
ledge, a rail): it is thin. 0.9 ms.

```python
voice_line(F, mx, my, 1560, 470, w=F.seg(40.34, 41.5), fall=F.seg(41.5, 42.6), dark=F.seg(42.2, 42.6))
```

## 6. The bare bulb and the moth (119.8 to about 126)

```python
hanging_lamp(F, x, top, drop, lit=1.0, floor=742.0, s=1.0, swing=0.0, spread=0.42, seed=880,
             a=1.0, t=None) -> {"bulb": (x, y), "r": radius, "pool": (x, floor), "half": half width}
moth_path(t, cx, cy, r=80.0, seed=0, come=None, fall=None, floor=742.0) -> (x, y, heading)
moth(F, x, y, heading=0.0, s=1.0, t=None, a=1.0, beat=1.0, seed=0, col=None)
moth_trail(F, t, cx, cy, r=80.0, seed=0, dur=0.9, a=0.6, lw=2.2, col=None, come=None, fall=None,
           floor=742.0) -> (x, y, heading)
```
- `hanging_lamp`: a cord from (x, top), `drop` long, a pear-shaped bulb with its filament (30 * s
  across), and under it a cone of pale rubbed light to world y = `floor` with a pool there. The
  cone has no outline: it is strongest down its middle and dies away at its sides (`spread`: its
  half width at the floor as a share of its height). `lit` 0..1 (fade it over 6 frames or more).
  `swing`: a slow pendulum in rad on `t` (default `F.tb`); leave it 0 or under 0.03, the cone is a
  large area. Pale only. 2.2 ms.
- `moth_path`: a deterministic unsteady orbit about (cx, cy), about `r` wide: it keeps clear of the
  light, darts in at it now and then and is off again; `t` any clock (the film: `F.t`).
  `come=(x0, y0, t0, t1)`: it sets out from the world point (x0, y0) at t0 (the mouth: the voice
  that leaves it) and has joined its orbit by t1. `fall=(t0, t1)`: between these times its circling
  runs down and it sinks, fluttering, to world y = `floor`, and lies there afterwards.
- `moth`: a speck of a body and two small wings that open and shut on TRUE time (`t`, default
  `F.t`): one beat in four frames, three shapes. 34 * s across. `beat` 0..1: 0 = settled, wings
  open and still; in between they only quiver.
- `moth_trail`: the thin line it has drawn in the last `dur` seconds, thinning and fading toward its
  old end (the voice that circles the lamp); takes the same `r`, `seed`, `come`, `fall`, `floor` and
  returns the moth's place, for `moth`. Both together 0.2 ms.

```python
L = hanging_lamp(F, lx, -40, 300, lit=F.ramp(119.0, 119.6))
if F.t >= 119.79:                         # the voice leaves the mouth, is at the lamp by 121.0, circles, drops
    way = dict(come=(mx, my, 119.79, 121.0), fall=(124.8, 125.9))
    x, y, hd = moth_trail(F, F.t, *L["bulb"], 80, **way)
    moth(F, x, y, hd, a=F.ramp(119.79, 120.0), beat=1 - 0.85 * F.ramp(125.6, 126.0))
    # the child's reaching hand: toward moth_path(F.t, *L["bulb"], 80, **way)[:2], or toward L["bulb"]
```

## 7. The phone

```python
PHONE_LEN = 44.0;  RING_TIMES = (251.41, 251.83, 252.37, 252.61, 252.87)
phone(F, x, y, s=1.0, lit=0.0, seed=480, ring=0.0, col=None, draw=1.0, warm=0.0, rot=-0.07,
      lie=1.0, scroll=0.0, bars=1.0, down=False, rings=(), halo=1.0, a=1.0) -> dict
phone_held(F, hand, ang=-1.25, s=1.0, lit=0.0, warm=0.0, back=False, scroll=0.0, **kw) -> dict
```
A small dark slab centred (x, y), `PHONE_LEN * s` long (s = 1 on the rug at `story.PHONE`: 42 px
in the wide room; s = 4 to 5 for 150 to 250 px).
- `lie` 1 = lying on the floor, seen at a slant; 0 = held up, face to us. `rot`: angle of its long
  axis (-1.57 = upright). `down=True`: face down, or seen from the back.
- `lit` 0..1: the screen (fade over 6 frames). `warm` 0 = pale and cold (second verse), 1 = amber
  (the call).
- `bars`, `scroll`: rows of empty scribbled lines on a lit screen (never letters or icons);
  `scroll` moves them, in rows, any number: add 2 to 3 rows per flick of the thumb, eased out.
- `rings`: times of the song at which a ring leaves it (pass `RING_TIMES`): each is a pair of
  brackets on either side of the phone, as a child draws ringing, that widen and fade over 0.62 s
  (nothing is drawn below the phone: the lyric band is there), and the slab hops and rattles (the
  rattle alternates every frame on purpose). `ring` 0..1: steady ring marks instead.
- `draw` 0..1: it is still being drawn. `halo`: the small glow of the screen itself (0 for none):
  additive light at night; on warm paper a rubbed patch of pale pastel (a warm screen gets a pale
  heart, so that it shows on the coral rug too).
- Returns `{"light": (x, y), "a": 0..1, "col": colour, "c": (x, y), "rot": angle}`: where its
  light comes from and how strong. The glow on a face is the scene's to add.
- `phone_held`: the same in a hand: held at world point `hand` by its lower third, long axis at
  `ang`; `back=True` (or `down=True`) seen from behind: at the ear, or turned face down in the hand.
  It takes phone's other keywords (`bars`, `rings`, `halo`, `a`...) except `lie` and `rot`.

Costs: dark 0.55, lit with bars 0.95, amber with two rings alive 2.1 (2.2 by day), held 0.85.

At the ear the slab (44 x 23 units at s = 1) lies across whatever is under it: give `hand` a point at
the far side of the head (behind the ear, over the hair), not on the face.

```python
scroll = sum(2.4 * ease_out(seg(F.t, a, a + 0.35), 2.5) for a in (93.05, 93.26, 94.75, 95.98))
R = phone_held(F, J["ha_f"], -1.05, lit=F.ramp(92.2, 92.5) * (1 - F.ramp(96.0, 96.2)), scroll=scroll)
glow(F, J["head"][0] + 12, J["head"][1] + 14, 95, 80, R["col"], 0.22 * R["a"])   # its light on the face
phone(F, *story.PHONE, lit=F.ramp(251.2, 251.41), warm=1.0, rings=RING_TIMES)     # the coda
phone_held(F, ear, -1.95, lit=1.0, warm=1.0, back=True)                           # at the ear (253.6)
```

## 8. Crows, and after colour just birds

One bird model. Night skin: an almost black body with a pale outline (not the scribble's black).
Day skin: a small pastel bird (colour by seed, or `col`). s = 1 is about 70 units beak to tail; on
the wire the film uses 0.5 to 0.62 (about 35 px at zoom 0.95, 80 px at zoom 2).

```python
crow(F, x, y, s=1.0, seed=500, face=1, a=1.0, hunch=0.0, col=None, day=None, look=None, t=None, idle=1.0) -> head
crow_land(F, x, y, s=1.0, seed=500, face=1, u=1.0, a=1.0, hunch=0.0, col=None, day=None, come=(-64, -46)) -> feet
crow_fly(F, x, y, s=1.0, seed=500, face=1, u=0.0, a=1.0, to=(150, -210), col=None, day=None, beats=5.0, hunch=0.5) -> (x, y)
crows_on_wire(F, wire, times, xs=None, s=0.55, seed=510, hunch=0.75, a=1.0, land=0.26, leave=None,
              to=(150, -230), fly=1.1, t=None, col=None, day=None, approach=0.5) -> [(x, y, age), ...]
perches(x0, x1, n=11, seed=510) -> array of x
swing(age, freq=2.4, tau=0.45) -> -1..1
```
- `crow`: perched, feet on (x, y). `hunch` 0 upright .. 1 sunk into its shoulders. `look` +1 beak
  forward .. -1 head turned back; `None` = it lives by itself on `t` (default `F.tb`): now and
  then it turns its head and holds it, shifts its feet, shakes itself (`idle` scales it, 0 = still).
- `crow_land`: `u` 0..1 the landing: a short glide in from `come` (units of s, from behind and
  above), wings spread and braking; its feet are on at u = 0.55; then the wings fold and the body
  dips and settles. Give it 6 to 8 frames. u <= 0 draws nothing, u >= 1 the perched crow.
- `crow_fly`: `u` 0..1: it crouches (from `hunch`, as it sat), throws its wings open and flies
  along a rising curve to (x, y) + `to` (mirrored by face). Let `to` end outside the frame or the
  window. About 1.1 s reads well.
- `crows_on_wire`: the whole gathering. `wire`: its world polyline in this frame; `times[j]`: when
  crow j touches down (song's clock; its feet arrive ON that time); for `approach` seconds before,
  it is seen flying in. `xs`: the places in landing order (default `perches` along the wire: each
  newcomer takes a gap). After landing each sinks into its shoulders over two seconds and idles.
  `leave`: times at which they fly up again. Returns the crows on the wire with their age since
  touchdown. Clip it to the pane (`with F.clip(rect=WINDOW): ...`) and draw it after the view and
  before the window's own strokes, so that the bars are in front of the birds.
- `swing(age)`: a damped swing, -1 at the moment of landing, for the wire's dip.

```python
bird(F, x, y, s=1.0, flap=0.0, face=1, seed=0, col=None, a=1.0, climb=0.0, day=None, glide=0.0)
flock(F, x, y, t, n=7, s=0.5, vel=(95, -8), seed=0, cols=None, a=1.0, rate=3.4, day=None) -> leader (x, y)
```
- `bird`: flying, body's middle on (x, y). `flap`: wing beat in cycles (drive with true time,
  about `3.4 * F.t`: the wing stands up, folds to a stub along the back, hangs down); `glide` 0..1
  holds the wings out; `climb` rad. Under about 16 px of wing on screen it becomes two strokes, as
  a child draws a far bird.
- `flock`: 5 to 9 birds in a loose skein that breathes, travelling `vel` units a second from
  (x, y) at t = 0 (pass seconds since it set out, on `F.t`); every bird has its own beat and glides
  now and then. `cols`: their colours by day. Put it behind the land with `F.depth(...)`.

Costs: a crow 0.36, a landing 0.26, a take-off 0.24, eleven on the wire 4.0 (they are eleven
things), a bird 0.27 (0.36 by day), a flock of 7 at s 0.5: 2.3, of 9: 2.9, far (two strokes each) 0.42.

```python
T_LAND = [24.27 + 0.75 * j for j in range(6)] + [29.5, 30.3, 32.3, 33.0, 33.8]      # eleven in the end
xs = perches(WINDOW[0] + 26, WINDOW[2] - 26, 11)
dips = [(xs[j], 5 * (1 + swing(F.t - T_LAND[j])), 70) for j in range(11) if F.t >= T_LAND[j]]
wire = sets.wire_pts(dips=dips)                 # each landing dips the wire and sets it swinging
S.view(F, wire=wire)
with F.clip(rect=WINDOW):
    crows_on_wire(F, wire, T_LAND, xs)          # then ground_line(F); S.draw(F): the bars in front
flock(F, -200, 330, F.t - 228.0, 7, 0.5, vel=(190, -14), seed=2)        # the colour world
```

## 9. The chalk stub, the lines it goes over, the string

```python
STUB_LEN = 26.0
chalk_stub(F, tip, ang=-0.9, s=1.0, a=1.0, dust=0.0, seed=930, t=None) -> grip (x, y)
stub_grip(tip, ang, s=1.0) -> (x, y)
restroke(F, P, d=1.0, w=5.0, col=None, seed=940, a=1.0, piece=30.0) -> (x, y, ang)
string(F, hand, end, slack=0.25, t=None, col=None, w=2.4, a=0.9, seed=771, knot=0.0, sway=1.0) -> points
```
- `chalk_stub`: a stub of white chalk, its drawing end on `tip`, its body pointing away along
  `ang`; `STUB_LEN * s` long. `dust` 0..1: crumbs falling from the tip (on `F.tb`). The hand goes
  to the returned grip point (`stub_grip` gives it without drawing). 0.15 ms.
- `restroke`: going over a line again (111.0 to 112.0, 114.3: the child redraws its own outline
  where it was crossed out). The world polyline `P` is redrawn as short strokes that overlap and
  lie a little across each other, one after another as `d` goes 0..1. Brighter and rougher than
  the line it mends: give it about 1.5 times that line's width. Returns the chalk's tip and its
  direction. 1.1 to 1.7 ms for 190 units.
- `string`: the string of the small tangle from `hand` (or what it is tied to) to `end` (where the
  tangle hangs). `slack` 0 taut .. 1 loose and bellying; a slow wave on `t` (default `F.tb`,
  `sway` scales it). `knot` 0..1 draws a bow at the hand end (tied to the armrest in the coda).
  Returns its points, hand first. The tangle itself is the gloom artist's. 0.6 ms.

```python
arm = spline(A(J["sh_b"], elbow, J["ha_b"]), 10)            # the stretch that was crossed out
d = F.seg(111.0, 112.0)
x, y, ang = restroke(F, arm, d, w=7.5)
if 0 < d < 1:
    grip = chalk_stub(F, (x, y), -0.75, dust=1.0)            # pin the other hand to `grip`
string(F, (story.SOFA_ARM_R[1] - 10, story.SOFA_ARM_Y + 14), tangle_xy, 0.2, knot=1.0)   # the armrest's outer end: clear of the head
```

## 10. Flicker, and what to keep in mind

Measured with a static camera (`flicker.txt`; `review/flicker_review.txt`): the wall drawing, the
phone and five crows at rest on a bare sheet: 0.078 levels and 0.27 percent on a boil step, against
0.068 and 0.23 for the ground line alone; 0.000 inside a pair. Every piece of this module at rest
on one sheet (23 things): 0.23 levels, 0.74 percent, 0.000 inside a pair. The same in the room (set
and child as stand-ins): 0.48 levels, 1.7 percent. In both silences (56.0 to 58.6, 193.2 to 194.4)
every frame of that sheet is identical to the one before it (largest pixel difference 0).
The same frames rendered in two separate processes are identical.
- Lines of the family drawing boil only with `detail=2`; at wall size they are seated.
- Flying and landing birds do not boil (they move); perched ones do, faintly.
- On true time by themselves, whatever the boil clock does: the moth's wings, a ringing phone's
  hop and rattle. Do not have them on stage in a silence unless they are meant to move there
  (`moth(beat=0)` holds the wings).
- `hanging_lamp(swing=...)` moves a large pale area: keep it 0 unless the lamp has been touched.
- Everything that fades takes an alpha from you (`a`, `lit`): ramp it over 6 frames or more.
- Colour: before 217.84 only cold chalk here, except the tape and the warm phone (the friend's
  amber). In the day skin: pencil and the golden-hour pastels. The crows' bodies are a very dark
  blue, not the scribble's black.
- Far cameras: at zoom 0.26 and under, the things keep their place and fade as the kit's lines do; a
  44-unit phone or a crow of scale 0.55 is then a speck. Nothing here is meant to be read there.
- Nothing is drawn below a lying phone or a ringing one's marks; the voice line lies at y 748 to
  764 by default: both above the lyric band (y > 864) at the room's cameras.
