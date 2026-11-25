# hx.chalk.weather: light and weather

Light in this film is rubbed pastel through the paper's tooth: pools, shafts and glows, and one soft
bloom from the finish. This module is the rain, the mist, the room's light, the shafts through the
scribble, the friend's amber, the rip of the sheet, the shadows.

    from hx.chalk.weather import *          # every name below (hx.chalk itself exports only the seven old ones)

Proofs and the scripts that make them: `hx/_review/v4_kit/weather/` (`proofs.py`, `numbers.txt`) and,
as the film frames them, `hx/_review/v4_kit/weather/review/` (`review.py`, `measure.py`).

**Conventions.** World coordinates and world sizes, mapped through `F.cam`; y runs down; the ground
line is world y 742 (`hx.story.FLOOR`, the default of every `ground` / `y` argument). Alphas 0..1.
Nothing here keeps state: a frame is a function of its time. Costs are ms at 1080p on one core.

**Clocks.** What is merely alive (rain, splashes, mist, the shimmer of a reflection, dust by default)
runs on the boil clock `F.tb`: it steps on twos and stands still in the two silences, where the rain
hangs in the air. Each such function has `t=None` (= `F.tb`); pass another clock only on purpose
(`t=F.t` for the dust in the long silence). What ACTS has no clock of its own: you pass a number that
you compute from `F.t` (`open_`, `since`, `head`, `pulse`, `narrow`, `a`).

**Colour rule.** Before 217.84 s only cold chalk and, for the friend, amber. `light_col(F)` gives the
colour of plain light for the moment: `PALE` (cold) before the sheet rips at 201.25 s, `WARM` (the
under sheet's pale warmth) after it, cream on the day paper; it is the default `col` of shafts, pools
and dust. Shadows at night are deep blue, never the scribble's black.

**Skins.** `amber_glow`, `tear`, `tear_shafts` and `scraps` draw nothing on the day paper, so a scene
function that the ring renders twice (night and day) may call them in both.

**Order of drawing** (back to front): `mist` .. `rainfall(part="back")` .. shafts, `tear_shafts`,
pools, window light .. `ground_line` .. `amber_line` .. shadows .. glows .. figures .. `rim` .. the
scribble .. `tear` .. `scraps` .. `rainfall(part="front")` .. `flash`.

---

## 1. Rain

### `rainfall(F, k=1.0, part="all", ground=742, slant=None, lean=None, seed=9, t=None, col=C.CHALK_BLUE, splash=1.0, lens=1.0)`
The rain of the plain with ONE intensity `k`: 0 dry, 0.55 the thin rain that hangs in the first
silence, 1 the first chorus, 1.5 the storm of the second. Drops are short chalk strokes, pressed
harder toward the head, with a bead on it. Above 1 the rain is driven, not only thicker: drop after
drop goes over to a third more speed (a faster drop is a longer stroke), the tracks slant hard, and
it comes in gusts (sheets of thicker rain crossing the frame). At 1.5: 1.4 times the drops, strokes
1.37 times as long.

- `part="back"`: two far layers (parallax 0.4 and 0.7 through `F.depth`), ending on the horizon. Draw
  BEFORE the figures. `part="front"`: the rain of the figures' own plane (it lands on and just below
  the ground line), its splashes, and big sparse drops close to the lens (fixed to the screen, thinning
  out over the ground and the lyric band). Draw AFTER the figures. `"all"`: both.
- The three world layers are anchored in the world: their tracks are fixed there, they pan and scale
  with the camera, each at its own parallax, and their detail goes by octaves of zoom, so a drop is
  always about the same size on screen (the pull-back does not turn the rain into dust).
- `slant`: dx per dy of the tracks; default 0.20 + 0.08 k up to k = 1 (0.28), then on to 0.46 at
  k = 1.5. `lean`: extra slant of the strokes alone, default `rain_lean(F)` (the music).
  `splash`, `lens`: 0..1 scale those two parts.
- Call it with `F.cam` = the scene's camera, not inside `F.screen()` / `F.depth()`.
- Animate: `k` (slowly; `rain_amount(F.t)` is the storyboard's curve). Keep `seed` fixed. A drop
  keeps its track and its speed while `k` moves (between 1 and 1.5 each drop changes speed once).
- Cost: back (two layers together) 1.1-1.4 (k=1), 1.6-1.8 (k=1.5), up to 3.2 in the storm at zoom 0.205;
  front (plane, splashes, lens) 1.1-1.5 (k=1), 1.5-1.9 (k=1.5).

### `rain_amount(t) -> k`
The storyboard's rain as a number of the song's time: begins thinly at 54.6, 0.55 through the first
silence, 1.0 from the band's entry (58.6-59.0), thins from 75.5, gone by 87; 1.5 from 138.2-138.8,
thins from 150.1 (0.45 by 152.5), gone by 160. Every module that draws `rainfall(F, rain_amount(F.t))`
with the default seed draws the same rain at a hand-off.

### `rain_lean(F, k=1.0) -> float`
How much further the strokes lean with the recording's loudness: about -0.12 (quiet: they hang
straight) .. +0.08 (loud). Stepped on twos; held in the silences.

### `rain(F, l, t_, r, b, n=140, slant=0.20, ln=30, col=C.CHALK_BLUE, a=0.5, w=2, speed=1100, seed=0, t=None, lean=0, bead=0.6)`
One flat sheet of rain inside a world rectangle (clipped to it): `n` drops about `ln` long and `w`
wide, falling `speed` units a second. `bead`: share of drops with a bead. Inside `with F.screen():`
the rectangle is in screen px. Not anchored (no parallax): for the plain use `rainfall`. Keep `speed`
and the rectangle fixed over time. 1.4 ms for 200 drops over the frame.

### `splashes(F, x0=None, x1=None, y=742, k=1.0, n=40, size=13, spread=34, col=C.CHALK_BLUE, a=0.8, seed=0, t=None)`
Drops landing on the ground line: small crowns (two ticks flying apart, a flat ring opening) that
live four boil steps; in a silence they stand frozen half open. About `n * k` a second per frame
width, between world `x0` and `x1` (default: wherever the camera looks), up to `spread` screen px below
the line (nearer = larger). `size` in screen px. `rainfall` draws them itself. 0.3-0.4 ms.

### `rain_window(F, l, t_, r, b, k=1.0, seed=3, t=None, col=C.CHALK_BLUE, a=1.0)`
The rain a room's window shows, inside the pane's world rectangle: thin slanting rain behind the
glass, beads sitting on the glass, a few running down in fits (rest, slide, rest) with a wavering wet
trail. Draw it after what is behind the glass and before the window's frame. 0.6 ms.

```python
def draw(F):
    F.cam = cam(F.t)
    k = rain_amount(F.t)
    mist(F)
    rainfall(F, k, "back")
    ground_line(F)
    figure(F, x, 742, 380, pose, "child", seed=3)
    rainfall(F, k, "front")
```

Flicker (rain over mist, ground line and child, static camera; a boil step): k=0.4 0.2 levels /
0.8 %, k=1 0.5-0.6 / 1.6-1.9 %, the storm (k=1.5) 0.8-1.0 / 2.6-3.1 % (wide .. close); zero inside a
pair. A film frame adds its own 0.7-0.8 levels, so the storm measures about 1.6-1.8, over the 1.2
target: that is rain moving, not boil. Every drop
keeps its track, and from step to step it moves about 1.3 times its own length, so the eye links the
marks. In the silences the frames are identical.

## 2. Mist

### `mist(F, y=742, a=1.0, h=None, col=None, seed=0, t=None, x0=None, x1=None, low=0.30, core=1.0, slab=(0, 1))`
A band of rubbed haze lying on the horizon at world `y`: thickest on the line, thinning upward over
about `h` world units (billowing between 0.6 h and 1.4 h) and downward over `low * h`; the billows
drift slowly (`t`). It spans whatever the camera sees, or only world `x0..x1` (soft ends). `core`:
the paler seam on the line. `col`: default cold haze at night, cream by day.
`h`: default `170 / zoom ** 0.8`, which follows the camera: 170 px on screen at zoom 1, about 125 px
at zoom 0.2, smoothly through a pull-back (a fixed world height would be a hairline in the wide
frame). Pass a number only for a special band.
Animate `a` (slowly). Cost 1.9-2.3 ms per call (so 4-5 while a figure stands between two slabs).

**Walking into it.** `slab=(d0, d1)` draws only the part of the mist between two depths (0 its near
face, 1 its far side). A figure that is `d` (0..1) of the way in stands between two slabs, which
together are exactly the whole band whatever `d` is:

```python
d = F.seg(58.76, 64.77)                       # how far the child has walked into it
mist(F, slab=(d, 1.0))                        # the mist behind the child
figure(F, x, 742, 380, pose, "child", seed=3, a=mist_keep(d, floor=0.12))
mist(F, slab=(0.0, d))                        # the mist in front of the child
```

In the close framing the band reaches only to the child's waist; in the wide frame (where most of
that walk happens) it is taller than the child and swallows it whole.

### `mist_keep(dist, reach=1.0, floor=0.0) -> 0..1`
The pressure a figure's line keeps after going `dist` toward a mist that swallows it at `reach` (same
units): 1 here, `floor` there, slow at first. (The child never goes all the way: keep a floor.)

## 3. The room: window light, lamp

### `window_pool(F, l, r, y0, a=1.0, lean=-0.55, depth=300, mull=True, col=None, mood=None, narrow=0.0, shade=1.0) -> corners`
The window's light on the floor: a slanting pool from world `y0` (the floor line; the room uses
`FLOOR + 14`) down `depth`, between world x `l` and `r` at the top, pushed sideways by `lean`, soft
at its edges (softer further from the window), a dozen loose strokes of the light's chalk laid the way
the light falls, and the shadow of the window's cross (`mull`).

| mood | when | look |
|---|---|---|
| `"night"` (default on night paper) | intro, first verse | cold blue, additive |
| `"evening"` | second verse | pale and colourless; pass a long pool: `lean=-0.9, depth=380` |
| `"sunset"` (default on day paper) | coda | gold going to orange-rose pastel, coral strokes, violet-grey bars, and with `shade` (0..1) a breath of violet dusk on the floor beside it so that it reads as light |

`narrow` 0..1 draws the pool together into a sliver along its long far edge (101.6-103.7: the pool
that becomes the corridor's line). Returns the four world corners (top-left, top-right, bottom-right,
bottom-left); `corners[0] -> corners[3]` is that edge: draw the chalk line along it.
Animate `a`, `narrow`. Cost 1.2 (night), 1.4 (evening, long), 2.0-2.2 (sunset).

### `moon_pool(F, l, r, y0, a=1, lean=-0.55, depth=300, mull=True, col=C.MOON)`
`window_pool` in its night mood (the old name).

### `window_glow(F, l, t_, r, b, a=1.0, mood=None, col=None, spread=None)`
The light the window lays on the wall round itself: rubbed light hugging the frame, thinning outward
over `spread` world units (default 0.58 of the larger side). Nothing is rubbed behind the pane. Draw
it before the window and what the window shows. It is quiet on purpose (at `a=1` a breath of light
on the wall hatch; up to about 1.8 for a moonlit wall). 1.8-2.0 ms.

### `lamp_light(F, x, y, h=420, a=1.0, col=None, floor=None)`
The standing lamp lit, same anchor as `lamp(x, y, h)`: a cone from the shade to a pool on the floor
(`floor`: its world y, default `y`) with loose strokes of the lamp's own crayon fanning down in it, a
small fan going up, the shade full of light. Gold pastel on the warm paper. Draw it right AFTER the
lamp (the light lies over the pole, inside the shade's outline). **Unlit at night: do not call it
before the coda** (warmth before 217.84 s is the friend's). Animate `a` (at least 6 frames). 3.1 ms.

```python
l, t_, r, b = WINDOW
window_glow(F, l, t_, r, b, 1.0, "evening")
Q = window_pool(F, l - 20, r + 10, FLOOR + 14, 1.0, -0.9, 380, mood="evening", narrow=F.ramp(101.6, 103.2))
ground_line(F)
chalk(F, np.stack([Q[0], Q[3]]), C.CHALK, 4.2, 0.9, seed=41, draw=F.seg(102.2, 103.7))    # the line it leaves
```

## 4. Shafts, pools, dust

### `shaft(F, x0, w0, y0, x1, w1, y1, col=None, a=0.15, alphas=(1, 0.67, 0.47, 0.2), soft=0.34, top=0.0)`
One shaft: from a slit centred world `x0` (half width `w0`) at `y0` down to a patch centred `x1`
(half width `w1`) at `y1`. Soft at both sides (`soft`: share of the half width that is penumbra).
`alphas`: strength from top to bottom. Additive at night. `top`: the share of its length over which
it comes out of nothing at its upper end: 0 when the scribble, the rip or the frame hides the slit,
about 0.25 when its upper end is in view (or it starts as a ruled edge). 0.8 ms.

### `shafts(F, x0, half, y0, xa, xb, y1, n=7, col=None, a=0.15, seed=0, alphas=(1, 0.67, 0.47, 0.2), top=0.0)`
A fan of `n` shafts through a gap centred `x0` (half width `half`) at `y0`, landing between `xa` and
`xb` at `y1`: uneven widths and strengths, overlapping, one rubbed tone. `a`: strength of one shaft at
its top. `top` as in `shaft`. 2.6-4.3 ms for a broad fan over most of the frame (it is fill: cost grows
with its area on screen). For the fan out of the rip use `tear_shafts`.

### `light_pool(F, x, y, rx, ry=None, col=None, a=0.3, core=0.5)`
Where a shaft lands: light rubbed flat on the ground round (x, y), half width `rx`, half depth `ry`
(default 0.17 rx), a brighter heart (`core`). 0.6 ms (rx 250) .. 1.2 (rx 900).

### `dust(F, l, t_, r, b, n=34, col=None, a=0.5, seed=77, t=None, drift=0.03, size=1.0)`
Chalk dust in a world rectangle: motes that wander, glint as they turn and sink (`drift`: share of the
box height per second; negative rises). `t=None`: on twos, still in the silences. `t=F.t`: every
frame (the coda's falling dust; anywhere the dust is the only thing moving). `col`: default the
light's colour on the night paper, rose-brown pastel dust on the warm paper. 0.2 ms.

### `shaft_dust(F, x0, w0, y0, x1, w1, y1, n=40, col=None, a=0.7, seed=78, t=None, drift=0.02, size=1.0)`
The same inside a shaft (the shaft's own arguments): motes go out near its edges and ends. 0.2 ms.

### `gap_light(F, x0, w0, y0, x1, w1, y1, a=1.0, open_=1.0, col=None, dust_n=40, t=None, pool=1.0, seed=0)`
The light through a gap in the scribble, whole: a soft shaft, finer rays in it, the pool where it
lands, dust turning in it. `open_` 0..1: how far the gap stands open (width and strength grow from
a hair). `a`: 0.4-0.5 a guess of light (157.01), 1 the shaft that lands on the child (188.9).
`t`: the dust's clock. Put `y0` above the frame or behind the scribble (its upper end is not
softened). Draw it before the figures and the scribble; for light ON a figure add
`glow(F, hx, hy, 150, col=light_col(F), a=0.1)` after the figure. 3.1-3.3 ms.

```python
gap_light(F, 1010, 70, -40, 905, 170, 742, a=1.0, open_=F.ramp(188.3, 189.6),
          t=F.t if F.t >= 193.0 else None)          # in the long silence the dust passes true time
```

## 5. The friend's amber

### `glow(F, x, y, rx, ry=None, col=C.AMBER_GLOW, a=0.2, power=1.6)`
Rubbed light round a world point: additive on the night paper, soft pastel on the day paper.
1.3-1.5 ms at r 300 (fill: about 4.3 ns a pixel; keep big glows few). Additive amber on the blue paper
goes grey-brown when it is large and weak: for the friend use `amber_glow`.

### `amber_glow(F, x, y, h, a=1.0, wet=0.0, t=None)`
The friend's glow: (x, y) the friend's ground point, `h` the height of the figure AS IT STANDS NOW
(388 standing, about 0.62 of that crouched or sitting: the glow sits on the middle of that height).

- Near (figure over about 260 px on screen): amber pastel rubbed round the figure, which takes the
  blue out of the paper, a lit heart at the chest, light on the ground at the feet. Never larger than
  about 340 px, however close the camera.
- Far (under about 90 px): all of it is light, the halo keeps a radius of 200 px and the heart burns
  brighter: a 60 px friend at zoom 0.26 is a warm point in the cold frame. Between: a blend.
- `wet` 0..1 adds `wet_reflection`. Draw before the friend. Nothing on the day paper.
- Animate `a` with the friend's own `a`, `h` with the pose. Cost 1.3 ms (friend 60 px), 2.1 (350 px),
  3.0-3.1 in the two-shot at zoom 1.2 (over the 2 ms a glow should cost: it is capped there, and that
  frame has little else in it); `wet` adds 0.6.

### `amber_point(F, x, y, a=1.0, r=1.0)`
A point of amber light, sized in SCREEN px (`r` scales it): the friend gone far (82.76 on), the lit
window seen small. 0.9 ms.

### `wet_reflection(F, x, y, w, a=1.0, col=C.AMBER, ln=None, seed=0, t=None, rows=8)`
A light's reflection on wet ground as a child draws it: under (x, y) ONE scribbled zigzag of `rows`
strokes, wide and close under the light (first half width `w`), narrower, looser and fainter downward
over `ln` (default 4 w), breaking into a dash or two at its end, on a faint smear. Its turns slide
sideways slowly on `t`. 0.6 ms.

### `amber_line(F, x0, x1, y=742, head=1.0, pulse=None, a=1.0, w=5.0, curve=None, reach=150) -> tip`
The amber ground line: the ground line itself gone over in amber from world `x0` (the friend's feet)
toward `x1` (the child's). It is drawn with `ground_line`'s own stroke, so it lies exactly on it and
boils with it; pass the same `curve` you give `ground_line` on the hills. Draw right after
`ground_line(F)`.

- `head` 0..1: how far it has been drawn from `x0`; while it runs its tip is a bright bead.
- `pulse`: where a pulse of brightness is, 0 at `x0` .. 1 at `x1`: a number, a list of numbers, a
  list of `(position, strength)` pairs, or None. Only the drawn part carries one. `reach`: its half
  length in SCREEN px.
- Far away the line never gets thinner than 2.3 px. A faint warmth lies on the ground along it.
- Returns the world point of the tip (None while `head` is 0). Cost 0.8 ms, plus 1.2 per pulse on screen.

### `amber_run(F, t0, t1, travel=0.55, after=0, linger=0.6) -> (head, pulses)`
The storyboard's timing for `amber_line`: the line runs between `t0` and `t1`, surging on every beat
and easing between; on every beat a pulse leaves the friend's feet, catches the tip up in `travel`
seconds and melts into it; the last one reaches the far end exactly at `t1` and dies away there over
`linger` seconds. `after=n`: later on, a pulse every n beats runs the whole line in two beats.
`pulses` is a tuple of `(position, strength)` pairs.

```python
head, pulses = amber_run(F, 72.46, 74.6, after=4)
ground_line(F)
amber_line(F, friend_x, child_x + 40, 742, head, pulses)
amber_glow(F, friend_x, 742, friend_h, a=F.ramp(70.7, 71.4), wet=1.0)
figure(F, friend_x, 742, friend_h, F_CALL, "friend", -1, seed=5, a=F.ramp(70.7, 71.4))
J = figure(F, child_x, 742, 380, pose, "child", seed=3)
rim(F, J, +1, a=F.ramp(74.4, 74.9))
```

### `amber_window(F, l, t_, r, b, a=1.0, pane=True, halo=1.0)`
The lit window across the street (world rectangle): the pane in amber with a paler heart and its
cross-bar, and its glow, which keeps at least 70 px radius on screen. `pane=False`: only the light,
round a pane drawn elsewhere (the room's `window_view` draws its own pane). 1.0-1.2 ms.

### `rim(F, J, side=1, col=C.AMBER, a=1.0, w=4.0, seed=90)`
An amber rim on a figure: short amber strokes just outside the head, the lit arm and the lit leg, a
breath of glow on that cheek. `J`: the joints `figure()` returned (`head R sh_f sh_b ha_f ha_b pel
kn_f kn_b an_f an_b`, world points). `side`: +1 the light comes from the right. Draw right after
the figure. It is built from the joints, not from the outline: on a hunched or sitting pose the arm
and leg strokes can sit a little off the contour. `figure(..., rim=(C.AMBER, +1, strength))` is the
figure's own rim along its outline; use one of the two, not both. 1.0 ms.

## 6. The tear (201.25)

### `tear(F, x0, y0, x1, y1, hw=92, open_=1.0, since=None, a=1.0, seed=5, light=1.0, flash_a=1.0) -> outline`
The dark sheet rips from the world point (x0, y0) to (x1, y1), any direction (either end may lie
outside the frame): the warm sheet shows (the day skin's own paper, fixed to the screen like all
paper), with the shade of the upper sheet along its edge; the torn edge of the dark sheet has a pale
fibrous rim with hairs standing into the opening; light spills onto the dark sheet round it.

- `open_` 0..1: the rip runs from its start to its far end over the first six tenths and goes on
  widening to the end. The storyboard: `F.seg(201.25, 201.25 + 8 / 30)`.
- `since`: seconds since the rip (`F.t - 201.25`): the flash of pale light, strongest about three
  frames in, decayed after a second. `None`: no flash. `flash_a` scales it.
- `hw`: half width of the gash at its middle. `light` 0..1: the steady light round the opening.
- Draw it after `tear_shafts` and after the scribble (it is the sheet: what was drawn there goes
  with it); a figure that stands in front of the opening may be drawn after it.
- Returns the closed world outline (None while `open_` is 0). Nothing on the day paper.
- Cost 5.3-5.6 ms open; 8.5-10 during the flash.

### `tear_shafts(F, x0, y0, x1, y1, xa, xb, land=782, hw=92, open_=1.0, a=1.0, n=8, seed=0, pool=1.0, col=None)`
The broad pale shafts that fall out of the rip onto the land, and the light where they land: a fan
from the middle of the opening (the tear's own `x0, y0, x1, y1, hw, open_`) down to the ground
between world `xa` and `xb` at world y `land`. Its upper end always lies inside the opening,
whichever way the rip runs, so `tear`, drawn after it, hides where it begins. `a`: strength; `pool`
0..1: the light on the ground. Draw before the ground line and the figures. 4-5 ms (a fan over most
of the frame; 4.1 measured with its dust). Nothing on the day paper.

### `scraps(F, x0, y0, x1, y1, since, n=16, hw=92, seed=5, ground=742, a=1.0, size=1.0, avoid=())`
Scraps of the dark sheet (tear's geometry): torn pieces with ragged edges, many small and a few
large, thrown clear as the rip passes their place (0.02-0.24 s), then falling as paper falls, swaying
and turning over (dark face, paler back, a pale torn edge all round), until they lie on the ground
line (and up to 40 below it) and are rubbed away 1 to 2.6 s later. All gone about 7 s after the rip.
`avoid`: world circles `(x, y, r)` that the scraps slide round instead of crossing: pass the two
heads, so that no scrap hides a face at the film's turning point. Closed form of `since`: nothing to
keep between frames. 1.1 ms. Nothing on the day paper.

### `rip_outline(x0, y0, x1, y1, hw=92, seed=5, open_=1.0) -> (108, 2)`
The closed world outline `tear` uses (to clip something to the opening, or to draw into it).

### `flash(F, a, col=None, x=None, y=None, r=None)`
Light for a hit: the whole sheet lit (`a` 0.25 a clear flash, 0.6 a blinding one); with a world point
and radius it comes from there. Shape it in time yourself. 0.8 ms; from a point 3-9 ms (fill).

### `decay(since, tau=0.3) -> 0..1`
0 before an event, 1 on it, then `exp(-since / tau)`.

```python
T = 201.25
op, since = F.seg(T, T + 8 / 30), F.t - T
RIP = (hands_x, hands_y - 40, hands_x + 190, -340)       # up between the curtains and out of the frame
tear_shafts(F, *RIP, land_x0, land_x1, 742 + 40, 120, op)
ground_line(F, curve)
Jc = figure(F, cx, 742, 380, pose_c, "child", seed=3)
Jf = figure(F, fx, 742, 388, pose_f, "friend", -1, seed=5)
curtains(F, ..., rip=since)
tear(F, *RIP, 120, op, since)
scraps(F, *RIP, since, hw=120, avoid=[(*Jc["head"], Jc["R"] * 1.1), (*Jf["head"], Jf["R"] * 1.1)])

flash(F, 0.3 * decay(F.t - 64.77, 0.22))                 # a hit of the first chorus
```

## 7. Shadows

### `ground_shadow(F, x, y, w, a=0.5, day=None)`
The rubbed contact shadow under a figure: world centre (x, y) on the ground, half width `w` (about
0.3 of the figure's height). Night: deep blue with a tighter heart. Day: violet-grey multiplied onto
what is there (grass stays green under it). 0.5 ms.

### `long_shadow(F, x, y, h, sun_x, a=1.0, length=2.0, fall=0.20, lift=0.0, curve=None, col=None, seed=0, width=1.0)`
The long shadow of a low sun: from the figure's ground point (x, y), away from the sun at world x
`sun_x`, `length` times its height `h` long, dropping `fall` per unit of length (it lies on the ground
toward the viewer). A figure laid flat and drawn out (legs, a garment widest at its hem, the round
head at its end), with a few loose strokes. By day it is `C.SHADOW` multiplied onto what it lies on:
a darker, cooler green on the grass, violet-grey on bare paper. On the night paper deep blue (under
the shaft: `length=1.0`).

- It follows the figure: pass its x, y, h every frame. `lift`: how high the feet are above the ground
  in world units (a jump: the shadow lets go of the feet, slides away, pales).
- `curve`: the ground contour function you give `ground_line`: the shadow follows the land loosely
  (0.6 of the contour's rise and fall: it lies on the slope in front of the contour line).
- `width`: thickness scale. `seed`: its strokes (use the figure's). `a`: pressure. 1.0 ms.
- It is a generic figure, not the pose. `hills.cast_shadow` is the hills artist's shadow for things
  that stand on the near land (trees, the house); for the two figures use this one.

```python
for x, y, h, lift, sd in ((cx, cy, 380, cjump, 3), (fx, fy, 388, fjump, 5)):
    long_shadow(F, x, y, h, sun_x, lift=lift, curve=HILL, seed=sd)
    ground_shadow(F, x, y + 3, 0.28 * h, 0.7 / (1 + lift / 60))
```

## 8. Constants

`PALE` (cold pale light), `WARM` (the under sheet's light), `light_col(F)` (see above).

## 9. Things to know

- Rubbed light costs by its area on screen (about 4.3 ns a pixel): a glow of radius 300 px is 1.3 ms,
  one of 800 px is 8 ms. Keep big ones few.
- `mist`, `rainfall` and `splashes` span the camera's view by themselves; never transform the canvas.
- `tear` shows the warm paper through `F.sub("day")` once per process (baked like the other textures).
- Night bloom makes the warm opening of the tear glare; that is wanted for the first second. If the
  paper's tooth should show more afterwards, lower `F.post.bloom` toward 0.3 from 202.5 on.
- A figure fading into the mist still rubs out the paper behind itself (`figure(..., a < 1)` keeps its
  rub-out), so at low pressure it is a dim silhouette, not a pale line.
- Shafts are cream on cream on the day paper: nearly invisible. By day, light is the sky's and the
  hills' own (`day`, `hills`); use `glow` and `long_shadow` here.
- Measured on a still stretch (a boil step; all zero inside a pair, and exactly zero in the two
  silences for everything on the boil clock): room at night with pool, glow and window rain 0.55-0.65
  levels / 1.9 %; shaft with dust 0.16-0.18 / 0.5-0.6 %; tear open 0.12-0.14 / 0.5 %; day shadows
  0.10-0.13 / 0.4-0.5 %; the far friend with the line drawn and no pulse 0.02 / 0.1 %.
