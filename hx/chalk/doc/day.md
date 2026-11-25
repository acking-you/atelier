# day: the hill world in both skins, the sky, the ring

`hx/chalk/hills.py` (the land and what grows on it) and `hx/chalk/day.py` (paper, sky, sun, ring).
`from hx.chalk import *` does NOT bring these (it still gives the prototype's `tree`, `flower`, `bud`,
and only `sky sun cloud ring paper_day tear_light` of day.py). Import them after it:

    from hx.chalk import *
    from hx.chalk.hills import *          # hills hills_back hills_front ground_y ground_slope land_curve hill_from_line hill_rise
                                          # flowers flower bud ring_bloom tufts tree home cast_shadow layer_x layer_y layer_slope
                                          # NEAR MID FAR FLAT_TO HILL1_X HILL1_SPAN FLOWER_COLS
    from hx.chalk.day import *            # sky sun cloud sun_at paper_tone paper_day ring tear_light CRAYONS

Every function draws the SAME geometry in the skin of the Frame it is given (`F.skin`): chalk on dark
paper (night), rubbed pastel on warm paper at golden hour (day). So one scene function serves `ring`.
Proofs: `hx/_review/v4_kit/day/` (`proofs.py`), and the film's own cameras in `review/` (`review.py`).

**The picture.** The sun stands low on the RIGHT, in front of us. Slopes that fall away to the right
are the sunward side (`C.HILL_LIT`), slopes that rise to the right the cool side (`C.HILL_SHADE`);
lights, shades and shadows lean to the lower left. Figures travelling right walk into the light.
The sky is fixed to the sheet (screen px); the land travels under it in three layers of parallax.

## 1. The land (numbers)

World units, y down. The near contour IS the ground line: 742 where the land is flat. The land sits
where `hx/story.py` puts the film (nothing is re-centred):

| world x | the land | the film |
|---|---|---|
| up to 4700 (`FLAT_TO` = `story.HILL_X0`) | flat, 742 | everything before the hills; the two at `X5` = 4300 and 4480 from the bridge to the rip |
| 4700 to 5690 | the first hill rises (never steeper than 0.47) | they walk up it, 205.9 to 213 |
| 5690 (`HILL1_X`) | first crest, `ground_y` 530 (212 high) | hand-off B9: the two at 5600 and 5780 stand at 535 and 534.5; the ring opens here |
| 7300 | bottom of the long valley behind it (13 high) | the run |
| 8158 | second crest (186 high) | the run |
| 9013 to 9150 | a level shoulder (96 to 99 high) | the last stand: `X10` = 9000 is at `ground_y` 645.8, slope 0.01 |
| 9654, 10780, 11265, 12287 ... | valley (36), crest (215), crest (157), valley (15) ... | beyond the frame; the land never ends |

| | |
|---|---|
| `ground_y(x, rise=1.0)` | world y of the near contour at world x. Scalar in, float out (11 us); array in, array out. `rise` 0 = flat plain, 1 = hills. Exact (sums of sines): feet, shadows and flowers stand on it |
| `ground_slope(x, rise=1.0)` | dy/dx there (y down: negative = rising to the right); the ground's angle is `atan(ground_slope(x))` |
| `land_curve(rise=1.0)` | the contour as a function for `ground_line(F, curve=land_curve(r))` |
| `FLAT_TO`, `HILL1_X`, `HILL1_SPAN` | 4700; 5690; (4640, 7300): the stretch of contour the first hill is laid down along |
| `NEAR, MID, FAR = 1.0, 0.5, 0.22` | the layers' parallax factors (`with F.depth(MID): ...`) |
| `layer_y(x, depth=MID)`, `layer_slope(x, depth)` | contour of the middle / far layer in that layer's OWN coordinates (`depth` is `MID` or `FAR`) |
| `layer_x(cam, sx, depth=MID)` | the layer x that camera `cam` shows at screen x `sx` (to stand the house where the picture wants it) |

## 2. hills

`hills(F, rise=1.0, back=1.0, lit=1.0, hour=0.0, gone=0.0, grass=1.0, line=True, house=None, a=1.0) -> r`

Far layer, middle layer, the house, near field, grass, and the ground line (through `ground_line`:
do NOT draw it again; `line=False` to draw it yourself). Call it after `sky`, before shadows, flowers
and figures. Returns the rise actually drawn: use it in `ground_y(x, r)`.

| argument | moves on | meaning |
|---|---|---|
| `rise` | `F.t` | 0 = the flat plain .. 1 = hills: the near ground itself lifts (175.0 to 178.2 via `hill_rise`) |
| `back` | `F.t` | 0..1: the far and middle layer draw themselves on across the VIEW from the left, the contour's tip leading, the colouring following with a hand-ragged edge. A pair `(far, mid)` staggers them. 0 = they are not there (before 201.25). Keep the camera still meanwhile |
| `lit` | `F.t` | night skin: 0..1 pale light rubbed on the sunward slopes and pale hatch lines (after the sheet has ripped). No effect by day |
| `hour` | `F.t` | day skin: 0 = afternoon gold .. 1 = evening (lights to apricot, shades to mauve). Same number as `sky(F, hour)` |
| `gone` | `F.t` | 0..1 the un-drawing (242.0 to 244.4): section 6 |
| `grass` | `F.t` | 0..1 length of the grass (it comes out of the ground) |
| `house` | - | the house with the amber window: `x` on the middle layer, or `(x, FAR)` on the far layer (x in that layer's own coordinates: `layer_x(cam, sx, depth)`); None = none. It draws itself on over the second half of its layer's `back`, and is the first thing un-drawn by `gone` |
| `a` | `F.t` | pressure of the whole land (fade over 6 frames or more) |

`hills_back(F, back, lit, hour, gone, house, a, rise)` and `hills_front(F, rise, lit, hour, gone, grass, line, a) -> r`
are its two halves, for things that stand between the far layers and the near land.

Night skin: each layer rubs out what is behind it (far paler and mistier, near deepest), a few long
thin hatch lines along the slope, chalk contours (far `CHALK_FAR`, middle `CHALK_DIM`, near the
ground line). Day skin: rubbed fields modelled warm/cool by the slope, haze at the foot of the far
layers, irregular marks that follow the slope (fainter down the field: the lyric band stays calm),
contours in soft colour, the ground line in pencil. Small round trees stand here and there on the
far and the middle contour, alone or in twos and threes (scale for the distance; they make the
parallax read); none within 150 units of the house.

**Where to stand the house.** The film sees it from the hill top (camera x about 5690) and again at
the end of the run (about 9000), when the friend points at it. On the far layer it drifts by only
0.22 of the camera's travel: `house=(layer_x(Cam(5690, 480, 0.75), 1770, FAR), FAR)` puts it at the
right edge on the hill top and right of centre, beside the setting sun, at the end. On the middle
layer (larger, nearer) it would pass the runners and end up behind them.

The states of the film:

```python
hills(F, rise=0.0, back=0.0, lit=0.0)                  # before 175: flat, bare, the ground line and tufts
hills(F, rise=hill_rise(w), back=0.0, lit=0.0)         # 175.0 .. 178.2 (section 3)
hills(F, back=0.0, lit=0.0)                            # 178.2 .. 201.25: the first hill alone (hand-offs B7, B8)
k = F.seg(201.25, 203.0)                               # the rip: light, and the land behind draws itself on
sky(F, light=k); hills(F, back=(k, F.seg(201.6, 203.4)), lit=k, house=HOUSE)

def land(F):                                           # from 217.84: one function, both skins (give it to ring())
    sky(F, hour)
    r = hills(F, hour=hour, house=HOUSE)
    tree(F, 6840.0, hour=hour)
    for x, h in ((cx, 380.0), (fx, 388.0)):
        cast_shadow(F, x, h, hour, lift=jump_height)
    flowers(F, 4700.0, 9300.0, 150, seed=2, skip=(cx - 70, fx + 70))
    figure(F, cx, ground_y(cx, r), 380.0, pose, "child", 1, seed=3)
```

## 3. The first hill is born from a line (175.0 to 178.2)

- `hill_rise(w) -> rise`: the ground's rise: flat until w = 0.42, up by 0.86, then 1.
- `hill_from_line(F, P, w, col0=C.GLOOM, w0=5.0, a=1.0, seed=4, span=None) -> rise`
  `P`: world polyline (N, 2) of the loose line as it lies; `col0`, `w0` its colour and width; `w` 0..1
  on `F.t`. w 0 to 0.3: the line is pulled out straight along the ground (near end first, the far
  end cast out last). 0.24 to 0.58: it lifts off the ground into the shape of the hill and hangs
  there, dark, a little too high. 0.42 to 0.86: the ground swells up under it and takes it, while
  the dark is rubbed off the line and the contour's chalk comes up under it. From 0.86 it melts into
  the ground line; at 1 it draws nothing. At w = 0 it draws exactly `P`.
  `span`: the stretch of contour it becomes (default `HILL1_SPAN`, 2660 long: its far end is beyond
  the frame, the line is cast out of the picture to the right).

```python
w = F.seg(175.0, 178.2)
r = hills(F, rise=hill_rise(w), back=0.0, lit=0.0)     # the land first
hill_from_line(F, loose_end_points, w)                   # then the line
figure(F, 4300.0, ground_y(4300.0, r), 380.0, ...)       # (the two are on the flat part: nothing lifts them)
```

## 4. What grows there

- `tufts(F, rise=1.0, grow=1.0, a=1.0, t=None, seed=31)`: grass in tufts along the near contour and,
  larger and fewer, down the field. `hills` calls it (its `grass`); call it yourself only with
  `hills(grass=0)`. Leans with a slow wind on `F.tb`.
- `flowers(F, x0, x1, n=40, seed=0, open_=1.0, grow=1.0, rise=1.0, depth=(4, 150), a=1.0, t=None, skip=None) -> (x, y)`
  n flowers in clusters rooted on the near land between world x0 and x1, from `depth[0]` to
  `depth[1]` below the contour (nearer = larger, 30 to 80 tall). Colours: `FLOWER_COLS` = coral,
  mustard, lilac, cream, mostly one per cluster. Night: pale stems and bud dots. Day: `open_` 0 =
  closed bud .. 1 = open (a small overshoot on the way). `open_` may be one number, an array (in
  the order of the returned arrays), or a function of the heads' world (x, y): see `ring_bloom`.
  `grow` 0..1 = stem height. `skip=(xa, xb)`: none rooted there near the contour (the figures'
  place). The same (x0, x1, n, seed) is always the same flowers, so give a whole scene ONE range
  and let the camera choose; only those in view are built. They nod on `F.tb`. Returns the heads.
- `ring_bloom(F, cx, cy, radius_at, t0, behind=46, every=0.375, dur=0.34, cam_at=None) -> fn`
  for `flowers(open_=fn)`: a flower opens on the first eighth note (0.265 + 0.375 j) at which the
  ring's edge has passed it by `behind` px, taking `dur` s. `(cx, cy)` world point of the ring,
  `radius_at(t)` its radius in screen px (the function you give `ring`), `t0` its start,
  `cam_at(t)` the camera at time t if it moves meanwhile. Use it until the ring has left the frame.
- `flower(F, x, y, h, col=None, seed=0, a=1, sway=0, open_=1)`, `bud(F, x, y, h, seed, a, sway)`: one of them, anywhere.
- `tree(F, x, y=None, t=None, seed=691, s=1.0, a=1.0, hour=0.0, shadow=True, rise=1.0) -> (cx, cy)`
  one tree about 520 * s tall standing on the near land at x (or on (x, y)). Day: rubbed clumps,
  golden toward the sun, with its long shadow; night: one scalloped chalk outline. Stirs on `F.tb`.
- `home(F, x, y=None, w=132, depth=MID, a=1.0, hour=0.0, lit=1.0, draw=1.0, seed=600, haze=0.0) -> anchors`
  the mended house that is the friend's: seam, a strip of amber tape, chimney smoke, the amber
  window lit in BOTH skins (night: dim outline, the window glowing). `hills(house=...)` draws it in
  the right order (132 wide on the middle layer; 96 wide and `haze=0.5` on the far one). Call
  `home(F, x, depth=d, w=..., a=0)` for its anchors only: `x y apex eave_l eave_r window chimney`, in
  the layer's coordinates (birds on the roof: `with F.depth(d):`). `draw` 0..1 draws it on (and back);
  `lit` the window; `haze` 0..1 paler into the distance. `depth` is `MID` or `FAR` unless you give `y`.
- `cast_shadow(F, x, h, hour=0.0, a=1.0, rise=1.0, w=None, lift=0.0, kind="figure", seed=0)`
  the long shadow of something h tall standing at world x: left and toward the viewer, 1.35 h long
  in the afternoon, 2.5 h at evening. `kind`: "figure" (a round head at its end), "tree", "plain".
  `lift` = height off the ground (a jump: the shadow lets go of the feet). It is one fixed
  silhouette: it does not follow the pose. Day skin only; draw it after `hills`, before flowers and
  figures. Night: use the kit's `ground_shadow`.

## 5. The sky

`sky(F, hour=0.0, gone=0.0, light=1.0, clouds=1.0, sun_a=1.0, t=None)`: first call of the scene function.

- Day: tones the sheet toward evening, then a rubbed gradient `C.SKY_HI` > `C.SKY_MID` > `C.SKY_LOW`
  (at hour 1: `C.EVE_HI` > `C.EVE_MID` > `C.EVE_LOW`), warm round the sun; irregular long strokes
  over it; soft cloud bands (no outlines); the sun as a rubbed creamy disc in a halo, no rays.
  `hour` 0 = afternoon gold (217.84 to 238) .. 1 = evening (238.75 to 244.5); move it on `F.t`
  (between 0 and 1 it costs 3 ms more).
- `gone` 0..1: rubbed out (section 6); at 1 only the toned sheet is left.
- Night: the same cloud bands as dim smears and the same sun as a pale hazy disc of chalk where the
  day's sun stands, scaled by `light` (0 = dark sky, nothing drawn: before 201.25; ramp it up with
  the light). `sun_a=0` leaves the disc out.
- The sky is in SCREEN px whatever the camera does (it does not zoom or pan). Only the clouds move
  (2 px/s, on `F.tb`).
- `sun_at(hour) -> (x, y, r)` screen px: (1440, 318, 54) at hour 0 .. (1440, 486, 67) at hour 1. The
  sun is fixed to the sheet and the far hills pass in front of it: how far it has set depends on
  where the far contour crosses screen x 1440. At the last stand (camera x 9000 to 9200, zoom 0.75
  to 0.85) that is screen y 490 to 510: half set. Along the run it varies from 435 (all but
  hidden) to 555 (sitting on the ridge). To place it yourself: `sky(F, hour, sun_a=0)`, then
  `with F.screen(): sun(F, 1440, y, hour=hour)`, then `hills`.
- `sun(F, x=None, y=None, r=None, t=None, seed=611, hour=0, a=1, light=1)`, `cloud(F, x, y, s=1, seed=630, hour=0, a=1)`:
  a sun / one cloud band of your own, in the coordinates of the camera in force.
- `paper_tone(F, hour=1.0)`: the warm sheet toned toward `C.EVE_PAPER` (a multiply over the bare
  paper: call it before drawing; `sky` does it itself). Day skin only.
- `paper_day()`: the warm paper image.

## 6. The un-drawing (242.0 to 244.4) and the bare sheet (244.5)

`gone` 0..1 on `F.t`, the same number for `sky` and `hills`. The far layer, the sky, the middle layer
and then the near field are rubbed out from both ends of the FRAME toward its middle, in the strokes
of a rubbing hand; each stroke leaves the smeared ghost of the drawing, which a second pass takes
away a moment later. Meanwhile the house un-draws itself (g 0.02 to 0.36), the grass goes with its
field, and from g 0.4 the near contour flattens into the flat ground line (the returned r goes to
0: stand the child on `ground_y(x, r)`). At 1 only the toned sheet and the flat ground line are left.
Yours to take away in the same time: flowers (`grow=1 - seg(g, 0.1, 0.5)`), trees and shadows
(`a=1 - seg(g, 0.0, 0.3)`).

```python
g = F.seg(242.0, 244.4)
sky(F, 1.0, gone=g)
r = hills(F, hour=1.0, gone=g, house=HOUSE)
# from 244.5 on (the coda, on the day skin):
paper_tone(F, 1.0)
ground_line(F)
```
(Measured: the last frame of the un-drawing and the bare sheet differ by 0.08 to 0.10 levels, a boil
step of the ground line.) For the coda's slow lift at the very end fade with `F.post.fade`,
`F.post.fade_col = C.EVE_PAPER`.

## 7. The ring

`ring(F, draw_fn, cx, cy, radius, turn=None, glow=0.42, bloom=0.30, seed=1000)`: as in README
section 10; its eight edge strokes use the pastels `CRAYONS` (mustard, sun-halo, coral, rose, lilac,
sky, sea, hill-lit). `tear_light` is as it was (it is being replaced).

```python
TOP = (5690.0, ground_y(5690.0) - 150.0)        # the joined hands
def radius_at(t): return 1250.0 * ease_out(seg(t, 217.84, 222.84), 1.6) + 20.0 if t >= 217.84 else 0.0

def both(G):                                    # drawn twice: night, day
    sky(G)                                       # night: dim clouds, pale disc; day: golden hour
    r = hills(G, house=HOUSE)
    flowers(G, 4700.0, 9300.0, 150, seed=2, skip=(5530, 5850),
            open_=ring_bloom(G, TOP[0], TOP[1], radius_at, 217.84, cam_at=cam_at))
    ...figures...

ring(F, both, TOP[0], TOP[1], radius_at(F.t), turn=F.t - 217.84)
```

## 8. Costs and flicker (1080p, one core, M3 Pro, other jobs running; zoom 0.75 / 1.0 / 1.3)

| piece | day ms | night ms |
|---|---|---|
| `hills` (three layers, far trees, grass, ground line) | 24.7 / 24.9 / 23.6 | 18.3 / 18.3 / 17.5 |
| of which: far + middle 11.3 to 12.0 (night 8.0 to 8.5), near field with grass 7.8 to 9.3 (night 5.1 to 6.3), `ground_line` 3.4 | | |
| `hills` with the house | 27.0 / 27.2 / 26.2 | 21.0 / 20.8 / 20.0 |
| `hills` while `gone` runs | up to 41 | |
| `sky` | 4.1 to 4.4 (7.1 while 0 < hour < 1; up to 12 while `gone` runs) | 3.0 |
| `flowers`, 40 in view | 1.3 to 1.6 | 0.5 to 0.6 |
| `tree` (with its shadow) | 6.0 to 7.6 | 3.6 to 4.3 |
| `home` | 2.4 | 2.4 |
| `cast_shadow` | 0.2 to 0.35 | 0 |
| `hill_from_line` | 0.6 | 0.6 |
| `ground_y` scalar / array of 600 | 0.011 / 0.038 | |

Whole frames with two stand-in figures and 150 flowers: the hill top by day 72 to 91 ms, by night 72
to 92 ms, the run 78 ms, the ring (both skins, 217.84 to about 223) 142 to 181 ms: close to the 200
ms limit, so what a scene adds inside the ring's function (birds, the tangle, more figures) should
be weighed; leaving the tree out of the ring's five seconds saves 12 ms.
The sky's gradient and strokes are baked once per process (two images, 15 ms each).

Still stretch, static camera (`proof.flicker`, 230.0 to 232.0): day 0.17 levels and 0.67 percent on a
boil step, night 0.18 and 0.70; evening 0.17 and 0.66; 0.00 inside a pair in all; exactly 0.00 on
every step inside the two silences (56.0 to 58.6 and 193.0 to 201.25). Alive on `F.tb`: grass,
flowers, the tree's clumps, the smoke, the clouds; everything else is seated (only the contours
boil). Under a pan each layer travels rigidly by exactly its parallax (`proofs.py rigid`: near 250 of
250 px, middle 125 of 125, far 55 of 55); the tone of a field is a function of the place in the
world, so nothing swims under a tilt either; a frame is the same picture whatever was rendered
before it (hashes equal across processes and orders).

## 9. Good to know

- Tooth and rubbed tone are fixed to the screen (the paper does not move): under the fast run the
  fields' fine grain stays put while their modelling, marks, contours, grass, trees and flowers
  travel rigidly. The fields use the smoothest rubbed grain so that this does not read as sliding.
- `back` (drawing on) and `gone` (rubbing out) are measured across the frame, not the world: a
  camera that pans meanwhile carries the tip and the rubbed edges with it.
- `hills(rise=0, back=0)` is the bare plain in this kit's dressing (hatch lines, tufts); it is not
  the plain of the choruses (that set has its own mist and stones). Change over with `a`.
- Colours before 217.84: this module uses only cold chalks, and amber for the house's window and
  tape (the friend's). The palette names `SKY_* SUN_* HILL_* EVE_*` are tuned here: `HILL_FAR` is a
  hazy blue-violet (a9b6c9), `HILL_NEAR` 93ba64, `HILL_LIT` e8d679, `HILL_SHADE` 568a72.
- The ground line (`ground.GROUND_X`) runs from x = -3000 to 15000; the land is defined everywhere.
- Superseded prototype pieces (still in props.py for the old demo): `hill`, `grass`, and the old
  `tree` / `flower` / `bud` (the new ones here keep those three names and their first arguments).
  `sky` here has a new signature (`sky(F, hour, ...)`, not the prototype's rectangle).
