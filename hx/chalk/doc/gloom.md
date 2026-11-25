# hx.chalk.gloom: the scribble

> **Ruling of the director (after this doc was written).** The seam of the parting is where the
> performance opens the curtain: `PART_GAP` is now `X5 + 180` and `handoff_gloom(..., strands=None)` is
> the default (the count of strands follows the grips). Where a passage below still speaks of a seam
> at `X5 + 90` with eight strands a side as the default, read this instead; the middle of the held
> opening is still about `X5 + 90`. In scenes use the shared layers of `hx/scenes/_shared.py`
> (`scribble`, `lid`, `high_cloud`, `curtain`, `tangle_on_string`), which make these calls for you.

The weight of the illness: the only black on the sheet, a child's tired, angry scribbling. It hangs
over the child, rests on it, becomes the sky, hangs to the ground, is parted by four hands, and at
the end is still there, small, on a string. One scribble in many forms; one form becomes the next
without a pop.

    from hx.chalk import *              # every name below

Proofs and the scripts that make them: `hx/_review/v4_kit/gloom/` (`proofs.py`,
`overview_all_forms.jpg`, `cost.txt`, `flicker.txt`), `hx/_review/v4_kit/gloom/review/`
(`review.py`: every form at the cameras and places of `hx/story.py`; `handover.py`: the test that
one form hands over to the next as the same picture) and, for the three turning points (the thin
pale place, the parting, the rip and what stays) and the hand-offs, `hx/_review/v4_kit/gloom2/`
(`proofs.py`, `handover.py`, `overview_three_moments.jpg`, `handoff_states_B1-B10.jpg`,
`cost.txt`, `flicker.txt`, `handover.txt`) and, staged with the real performances of `acting_pair`
(`s06`, `s08`, the holds), `hx/_review/v4_kit/gloom2/review/` (`review.py`, `measure.py`,
`numbers.txt`). Their scenes are worked examples.

**Conventions.** World coordinates and sizes through `F.cam`; y down; the floor is world y 742.
Nothing keeps state. Colours: `C.GLOOM`, `C.GLOOM_MID`, pale edges `C.GLOOM_EDGE`: nothing else in
the film may use them. In the day skin (`F.skin == "day"`, or `day=True`) every form is a soft dark
pencil-grey. The string of the small tangle is ordinary chalk / pencil.

**One scribble: four numbers that must agree everywhere.** The strokes are a pure function of
`seed`, the anchor `ax`, the hand `s` and the churn speed. Cloud, lid, curtains and shawl ARE the
same strokes when these agree, and other strokes (a jump) when they do not:
- `seed`: `story.GLOOM_SEED` = 4, the default. Never pass another for the weight itself.
- anchor: the cloud's is its centre `cx`; give the lid and the curtains `ax` = that same x (the
  cloud's `cx` at the hand-off in `story.HANDOFF`, e.g. `X2 - 30`). The weight belongs to the child:
  when the child walks under a lid, move `ax` with the child.
- hand: the cloud's follows its area (`s=None`); the lid's and the curtains' come from the camera:
  `lid_for(F.cam)`. Two modules that meet at a hand-off both call `lid_for` with the hand-off camera.
- churn: leave it alone (`CHURN` = 0.9 in every form). It is not a look to animate: another value
  is another set of strokes.

**Clocks.** The scribble CHURNS on the boil clock (`t=None` means `F.tb`): the hand goes on
scribbling, one stroke after another is made afresh (pale, the chalk tip leading) while its
predecessor fades under it; everything else stands exactly where it was (its lines do not boil).
In the two silences it does not change at all. Dust and the bobbing of the small tangle run on the
same clock. What ACTS has no clock of its own: you pass numbers computed from `F.t` (`draw`, `rest`,
`tug`, `spread`, `settle`, `drop`, the thin place's `k`, `strands`, the grips, `rip`, `amount`,
`out`, `slack`, `wind_up`'s `k`); `tremble` and `cross_out` read `F.t` themselves. A fade (`a`)
needs at least 6 frames; prefer `draw`.

**Order of drawing.** Lid, curtains: after the far sets and the light that comes through them
(weather's `gap_light` / `shaft`, `tear_shafts`), BEFORE the figures (they stand in front of it);
weather's `tear` and `scraps` after the ripped curtains. Cloud, strand: after the figure. Shawl,
crossings-out over the child, the piece that stays, the tangle on its string: after the figures.
The ground line is never mine.

**Every large form returns a `Tip`**: a tuple `(x, y)`, the world point of the chalk tip that is
scribbling now, with `.band` (the `Band` drawn): `T.band.under(x)` is the world y of the underside
at world x, `T.band.root(x, depth=0.3)` a point inside the mass above x (where a strand ends).

| form (storyboard) | call | animate |
|---|---|---|
| birth 11.0-13 | `gloom(..., draw=d)` | `draw` 0..1; radii may grow with it (`s=1.0`) |
| cloud, belly resting on the head | `gloom(..., rest=(x, y, k))` | cx, cy follow the head (ease them: it is heavy); `k` 0..1 |
| strand, slack / taut / pulled | `strand(F, p0, p1, slack, tremble=)`, `gloom(tug=)` | `slack`, `tremble`, tug `k` |
| crossings-out 20.79, 21.2, 21.6; 109.6, 113.5 | `cross_out(F, x0, y0, x1, y1, t0, off=)` | nothing: give the times |
| knot in the balloon 29.4-30.6, wiped, rising | `tangle(F, x, y, rx, ry, loops=12, draw=)` | `draw`, then x, y, radii |
| shawl 96.18 | `shawl(F, neck, pel, 742, head=, cloud=Bc, settle=k)` | `settle` 0..1 |
| cloud into lid 60.27, 138.26; lid into cloud 85.75, 173.5 | `ceiling(F, cloud=Bc, spread=w, ax=, **lid_for(F.cam))` | `spread` 0..1 or 1..0 |
| lid; belly let down 148.5 | `ceiling(F, ax=, rest=, **lid_for(F.cam))` | `rest` k, `sag`, `amount` |
| thin pale place 155.6-157.0 (to 173.5) | `ceiling(..., thin=(x, r, k))` + weather's `gap_light` | thin `k` 0 .. 0.9 |
| curtains 182.3-201.25 | `curtains(F, drop=, gap=, ...)` | `spread`, `drop` |
| parted, a strand at a time | `curtains(..., gap=, left=, right=, strands=None)` (the count follows the performance's grips) or `strands=peel(F.t, attacks)` (a strand on each attack) + `curtain_gap` for the light | the grips; `strands` |
| held by four hands 193-201.25 | the same, `tremble=` 1.3 to 2.6 | the grips, `tremble` |
| ripped 201.25: loose curls, pieces of lid | `curtains(..., rip=F.t - 201.25, stays=(x, y))` | `rip`, the point `stays` |
| the piece that stays, 211.7 to 219.8 | `remnant(F, x, y)` | x, y (it follows the child, lagging) |
| it winds itself up 219.8-223.8 | `wind_up(F, x, y, k, hand)` | `k`, x, y, the hand |
| unravelling 160.0 ... 178.2 | `unravel(F, root, hand, out)`, `ceiling(amount=)` | `out`, `slack`, the hand |
| small tangle 223.8 to the end | `on_string(F, *float_at(F, hand), hand)` | the hand; `lean` when running |
| dust | `gloom_dust(F, x0, x1, 0, band=T.band)` | `a` |
| at a hand-off of `hx/story.py` | `handoff_gloom(F, "B6", crown=...)` (last section) | nothing |

---

## 1. The engine: `Band`, `mass`, and the bands between two forms

A large form is a **Band**: the stuff between an upper and a lower curve. The strokes lie on an
endless sheet anchored to the band: each stroke has a place along the sheet and a share of the
band's depth, so the SAME strokes follow whatever shape the band takes (sag onto a head, open into a
lid, hang to the ground). You rarely need this section: `gloom`, `ceiling`, `curtains` and `shawl`
take the transitions as arguments.

### `Band(x, top, bot, ax, s=1.0, dens=None, floor=None, cut=None, reach=None, pale=1.0, core=1.0, halo=1.0, w=1.0, rests=(), thin=None)`
`x`: world x samples (ascending); `top`, `bot`: world y of the upper and lower edge there.
`ax`: the anchor, the world x its strokes are counted from. `s`: the size of the hand: 1 = the cloud
over the sofa (loops 100 to 350 world units wide, lines 4 to 12). `dens`: 0..1 per sample, thins it.
`floor`: a world y nothing hangs through. `reach`: the world distance from the anchor that
`draw = 1` means for a mass with `seq=False` (default: half its width).
The look a form carries (factors on `mass`'s `edge`, `core`, `halo`, `w`; interpolated when one form
becomes another, so nothing steps): `pale` (the lid: 0.6), `core`, `halo`, `w` (the shawl: 0.82,
0.8, 1.6). `rests = [(x, y, r, k)]`: world points it lies on: within about `r` of x its loops are
pressed flat against the height y instead of hanging through (set by `rest=`). `thin`: 0..1 per
sample: where the mass is worn thin (set by `thin=`): there its dark strokes drop out one after
another (cut short on their way), the rubbed dark goes first, every line that runs into the place
loses its black on the way and goes on as a pale line pressed lightly, and single loops of a layer
that only a thin place has are left, with the paper between them. (`dens` only presses everything
more lightly; it is what the curtains use beside their opening.)
Methods: `.thick`, `.under(x)`, `.over(x)`, `.root(x, depth=0.3)`, `.moved(dx, dy)` (the same mass
elsewhere). Attributes may be set.

### `mass(F, band, seed=4, a=1, draw=1, churn=CHURN, w=1, halo=1, edge=1, core=1, day=None, t=None, seq=False, warp=None, avoid=(), layers=None, keep=1)`
Draws the scribble that fills a band. All forms below are this call.
- `a`: pressure 0..1. `w`, `core`, `halo`, `edge`: factors on the band's own look (line width, the
  rubbed dark under the strokes, the pale dust round it that makes black read on dark paper, the
  pale fresh chalk and pale edges).
- `draw`: how much of it is scribbled yet: 0..1, or a pair `(d0, d1)`: its strokes exist from d0 to
  d1 of the order they were made in (raise d0 to wipe it away from its first stroke); the strokes at
  either limit are cut short and carry the pale tip. `seq=True`: ONE hand makes it, a stroke at a
  time (first a knot in the middle, then a sweep to the left and one to the right): for a mass that
  is wholly on screen (the birth). `seq=False`: it is scribbled from its anchor outward, both ways,
  out to `band.reach` world units at draw = 1, a ragged front with several tips (a lid drawn on).
- `keep`: 0..1, how much of it is left: strokes drop out all over it, cut short into loose ends, no
  tips (unravelling, drifting off). An array over the band's samples gives each part its own share.
- `churn`: the scribbling hand's speed; one value for the whole film (see the top). 0 = none.
- `avoid=[(x, y, r), ...]`: world discs it lies round (a head): nothing is drawn inside.
- `warp(x, y, xc) -> (x, y)`: your own displacement of its points (arrays; `xc` = world x of each
  stroke's middle, `None` for the tone). `layers`: names of the layers to draw (debugging).
- Returns the chalk tip `(x, y)` or `None`.
- Far away (`s * zoom` under 0.62) fewer strokes are drawn and the rubbed tone stands in for them;
  loops under about 3 px are not drawn at all. A band more than 1.9 cloud depths deep (in units of
  `300 s`) hangs: tall loops and long strokes take over from the flat ones (curtains, a belly let down).

### The band between two forms
- `spread_band(cloud, lid, w, front=None) -> Band`: a cloud opening out into a lid (w 0 -> 1) or a
  lid gathering into a cloud (1 -> 0). The cloud lifts and deepens where it hangs; to either side
  the lid comes down out of its own upper edge, further and further from the anchor (`front`: how
  far, in world units; default: it runs with w). w = 0 is exactly the cloud, 1 exactly the lid.
  `ceiling` and `curtains` call it for you (`cloud=`, `spread=`, `front=`).
- `morph_band(a, b, w, pin=None, n=0) -> Band`: the mass DRAWS IN (or opens out) to the other
  shape: every part of `a` travels to the matching part of `b`, so a wide cloud gathers into a
  narrow heap. `pin=(xa, xb)`: the world x of `a` that ends at the world x of `b`. `shawl` calls it.
- `mix_band(a, b, w, n=0) -> Band`: the plain mix at the same places; `w` may be an array over the
  `n` samples of the result. Where one band does not reach, it counts as a seam of no thickness at
  the level of its own middle (thin flat wings: prefer the two above).
In all three the anchor, the hand and the look are interpolated (by the weight at the anchor).

---

## 2. The cloud

### `gloom(F, cx, cy, rx, ry, seed=4, a=1, loops=None, w=1, churn=CHURN, strands=(), day=None, halo=1, grow=1, t=None, edge=1, rest=None, tug=None, draw=None, s=None, avoid=(), lump=1) -> Tip`
The cloud about the world centre `(cx, cy)` with world RADII `rx`, `ry`: 430 x 150 over the sofa
(it is 860 wide), 380 to 420 x 128 to 150 over a standing child (`story.HANDOFF[...]["cloud"]`).
Its rim loops hang up to about 100 world units below `cy + ry`.
- `draw` (or the old `grow`): the birth, 0..1, one hand (see `mass`, `seq=True`).
- `rest=(x, y)` or `(x, y, k)` or `(x, y, k, r)` or a list: the underside sags (or gives) until it
  touches that world point (the top of the head, a shoulder), and within `r` (default 90) of it the
  loops are pressed flat on the point instead of hanging over the face. `k` 0..1 is how far it has
  come down: ease it over a second. Keep the point within about 120 world units below the cloud's
  own underside, or the belly turns into a funnel. To keep a face wholly clear also pass
  `avoid=[(J["head"][0], J["head"][1], J["R"])]`.
- `tug=(x, y, k)`: a taut strand pulls a point of the underside `k` of the way toward `(x, y)`;
  0.1 to 0.2 is a firm pull.
- `s`: the hand; default by area (1 for 430 x 150; `loops`, the prototype's argument, still works).
  Pass `s=1.0` while you animate the radii, so that the loops do not change size.
- `lump`: unevenness of its outline. `strands=[(x0, y0, x1, y1, seed)]`: the prototype's loose
  crossings-out lying still over what is below (use `cross_out` for ones that act).

### `band_cloud(cx, cy, rx, ry, seed=4, rest=None, tug=None, s=None, lump=1, n=72) -> Band`
Its band (anchor = cx): what `ceiling`, `curtains` and `shawl` take as `cloud=`.

```python
J = figure(F, CURL_X, SOFA_SEAT_Y, 380, CURL, "child", 1, seed=3)
top = (J["head"][0], J["head"][1] - J["R"])             # the highest point of the head as it lies
d = F.seg(11.0, 13.0)                                   # the birth: it swells as it is made
g = ease_out(d, 2.0)
T = gloom(F, 700, 292, 250 + 180 * g, 100 + 50 * g, s=1.0, draw=d,
          rest=(top[0], top[1] + 6, F.ramp(13.3, 15.2)))            # then the belly comes to rest
strand(F, top, T.band.root(top[0] + 40, 0.4), slack=0.8)            # after 31.58: the strand
gloom_dust(F, 330, 1080, 0, band=T.band)
```

---

## 3. Thin things

### `strand(F, p0, p1, slack=0.5, a=1, w=1, tremble=0, seed=12, draw=1, day=None, t=None) -> polyline`
The thin dark line from the child (`p0`: the crown, a fist) up into the mass (`p1`: `T.band.root(x)`).
`slack`: 1 = it hangs in a lazy wave, 0 = taut and straight; ease it over 4 to 8 frames when it is
pulled, over half a second when it is let go. `tremble`: world units of shiver on the TRUE time (2
to 5: a strand under load; it does not stop in the silences, which is wanted at 193-201). `draw`:
0..1 or `(d0, d1)`, from `p0`, with the tip. `w`: 1 = 4 world units wide. Returns its world polyline
(40 points, `p0` first): put a rising knot on it with `P[int(u * 39)]`.
`strand_pts(p0, p1, slack, seed, tremble, t, n=40)`: the polyline alone.

```python
k = F.ramp(170.4, 170.9) * (1 - F.ramp(173.5, 173.9))               # pulled taut, held, let go
T = gloom(F, cx, 190, 430, 140, tug=(fist[0] + 60, fist[1] - 60, 0.16 * k))
strand(F, fist, (fist[0] + 60, T.band.under(fist[0] + 60) - 14), slack=1 - k, tremble=3.5 * k)
```

### `cross_out(F, x0, y0, x1, y1, t0, amp=40, n=8, seed=0, a=1, w=1, dur=4/30, off=None, day=None, t=None)`
One quick angry zigzag of the black crayon along the world axis `(x0, y0) -> (x1, y1)`, about `amp`
world units to either side, `n` strokes back and forth (keep n at 7 or more: fewer can look like a
letter). It draws itself on from the true time `t0` in `dur` seconds (4 frames), the pale tip
leading, with crumbs where the hand turned, and stays. `off=(ta, tb)`: it is rubbed out: the line
goes in the first half, a smeared ghost of it stays and fades over the whole span (give it a second
or more). `w`: 1 = 9 world units. Returns the tip while it is being drawn, else `None`.
Give each one its own seed and a different axis; cross the thing out, do not underline it.

```python
for j, (t0, x0, y0, x1, y1) in enumerate(((20.79, 1120, 300, 1240, 350), (21.2, 1236, 372, 1118, 420),
                                          (21.6, 1124, 440, 1240, 470))):          # over the hero on the wall
    cross_out(F, x0, y0, x1, y1, t0, amp=34, n=9, seed=30 + j, w=0.8, off=(22.4, 23.6))
sh, ha = J["sh_f"], J["ha_f"]                                       # 109.6: over an arm and a shoulder of the child
cross_out(F, sh[0] - 50, sh[1] - 30, ha[0] + 30, ha[1] - 10, 109.6, amp=42, n=9, seed=51, off=(110.9, 112.2))
```

### `unravel(F, root, hand, out, ground=742, face=-1, seed=41, a=1, w=1, slack=0, s=1, tremble=0, day=None, t=None) -> Unravelled`
A loose end pulled out of the mass into one long line. `root`: where it leaves the mass
(`T.band.root(x, 0.15)`); `hand`: the world point of the pulling hand; `out`: world units of line
pulled out past the hand so far (ease it up on every pull: about 500 a pull). From the hand the line
falls to `ground`, piles up a little where it lands and runs off along the ground toward `face`
(-1 left, +1 right: toward the hill) in lazy coils, a little under half a unit of ground per unit
of line; what already lies there never moves: new length is added at its free end, which carries
the tip. `slack` (0 while pulling .. 1 between pulls) and `tremble` belong to the stretch between
mass and hand. `s`: size of the coils (1: 70 to 220 wide).
Returns `Unravelled(line, lying)`: `U.line` the whole line as a world polyline (mass, hand, free
end), `U.lying` the part on the ground (from under the hand to the free end).
`unravel_pts(root, hand, out, ground, face, seed, slack, s, t, tremble)`: the polylines alone.
**Hand-over to the hill (175.0):** the line is drawn as
`chalk(F, U.line, C.GLOOM, UNRAVEL_LINE["w"] * w, a, UNRAVEL_LINE["seed"], wob=0.5, taper=0.5, grain="dense", edge=0.0)`
(8.5 world units wide; plus a pale twin offset by (1.5, -1.3) px at night). `hills.hill_from_line(F,
U.lying, w, w0=UNRAVEL_LINE["w"])` takes the lying part on from there: stop calling `unravel` when
it starts (the stretch from the mass to the hand should be gone by then: let the hand drop it).
Make the mass smaller with each pull: `ceiling(..., amount=1 - 0.17 * pulls)`.

```python
pulls = sum(ease_out(seg(F.t, tp, tp + 0.5), 2.2) for tp in (160.0, 161.9, 164.9, 167.9))
T = ceiling(F, ax=X5, amount=1 - 0.17 * pulls, **lid_for(F.cam))
busy = max(seg(F.t, tp - 0.1, tp + 0.15) * (1 - seg(F.t, tp + 0.5, tp + 0.9)) for tp in (160.0, 161.9, 164.9, 167.9))
U = unravel(F, T.band.root(hand[0] + 40, 0.15), hand, 500 * pulls, slack=1 - busy, face=1)
```

---

## 4. The small tangle

### `tangle(F, x, y, rx, ry=None, loops=6, seed=11, a=1, w=1, draw=1, churn=0.35, day=None, t=None, halo=1, end=None, rot=0)`
A few loops of the scribble about the world point `(x, y)`, world radii `rx`, `ry` (default 0.8 rx).
`loops`: 5 to 7 on a string, 10 to 14 for the knot that fills a balloon (radii about 0.7 of the
balloon's). `draw`: 0..1 or `(d0, d1)`: it scribbles itself on / is wiped from its first loop, the
tip leading. `end=(x, y)`: its first loop runs out to that world point (the mouth it came from).
`rot`: the whole knot turned by that angle (radians) about its middle.
`churn` here is its own: loops a second scribbled on at one end and lost at the other. Reads from
about 40 px across (at 24 px it is a dark blob). Returns its newest end.

### `on_string(F, x, y, hand, t=None, s=1, a=1, tie=False, seed=11, day=None, loops=6)`
The small tangle (112 world units wide at `s=1`) at `(x, y)` on a string held at the world point
`hand`; `tie=True` ends the string in a small bow round `hand` (the armrest, `story.SOFA_ARM_R`).
Returns where the string meets the tangle.

### `float_at(F, hand, rise=150, lean=-60, seed=11, t=None, bob=1) -> (x, y)`
Where it floats: `rise` above the hand, `lean` to the side (negative = left; when the child runs,
lean it away from the way it runs, 100 to 200), bobbing on `F.tb`. For a hand at the hip use
`rise` about 330 so that it clears the head, and a `lean` that keeps the string off the face
(`STRING` = `dict(rise=330, lean=110)`: the hand-offs use `lean = -face * 110`).

### `remnant(F, x, y, r=REMNANT_R, a=1, seed=4, t=None, day=None, draw=1, keep=1, churn=CHURN) -> Tip`
The one piece of the scribble that is left when the lid has drifted away: a small ragged scrap of
cloud about the world point `(x, y)`, `r` its half width (`REMNANT_R` = 118: a little over twice
the tangle it will become; it is about half as deep as wide). It rides where you put it: behind and
above the child, lagging (ease its place over a second: it is light now, and slow).
`curtains(rip=, stays=(x, y))` draws this very piece while the lid breaks up round it (it comes up
over 2.5 s among the lid's pieces), so go over to `remnant(F, x, y)` at any moment after
`rip = 10.4` and nothing changes. `keep`: 0..1, the share of its strokes that is left. 4.3 ms.

### `wind_up(F, x, y, k, hand=None, r=REMNANT_R, s=1, a=1, seed=4, t=None, day=None, tangle_seed=11, loops=6)`
The piece winds itself up into the small tangle: `k` 0..1 on `F.t`, over 3 to 4 seconds
(219.8 to 223.8). `k = 0` is exactly `remnant(F, x, y, r)`; `k = 1` is exactly
`on_string(F, x, y, hand, s=s)`. Between: a loose end of the piece comes down to the world point
`hand` (k 0 .. 0.24: the child takes it); then stroke after stroke of the piece is pulled out of
it, in the order they were made, a pale tip running along each as it goes, and is wound, turn upon
turn, into the knot in the piece's middle, which turns as it winds and comes to rest; the dark of
the loose end is drawn up the line into the knot too, and what it leaves is the string.
Move `(x, y)` yourself meanwhile: from where the piece rode to `float_at(F, hand, ...)` (it comes
down its own line), and keep bobbing afterwards with `on_string`. `hand=None`: the knot alone, no
strand and no string. Returns where the string meets the tangle. 4.3 ms.

### `wane(F, x, y, rx, ry, k, seed=4, a=1, r=56, t=None, day=None, tangle_seed=11, hand=None)`
The first version's call, kept: a last CLOUD of radii `rx`, `ry` (`gloom` with those numbers) worn
down to the small tangle of radius `r`, in one place: `k` 0 .. 0.45 the cloud draws in to the piece
that stays, then that piece winds itself up (`wind_up`, with `hand=` onto its string). The film's
own chain does not need it: `curtains(rip=, stays=)` .. `remnant` .. `wind_up` .. `on_string`.

```python
hand = J["ha_b"]                                                    # the child's free hand
fl = float_at(F, hand, rise=330, lean=-110)
ride = (hand[0] - 150, hand[1] - 560)                               # where the piece rides: behind, above
m = ease(seg(F.t, 220.4, 223.6))                                    # it comes down its own line
x, y = ride[0] + (fl[0] - ride[0]) * m, ride[1] + (fl[1] - ride[1]) * m
if F.t < 219.8:
    remnant(F, x, y)                                                # (before 211.7: curtains(..., stays=(x, y)))
else:
    wind_up(F, x, y, seg(F.t, 219.8, 223.8), hand)                  # at k = 1 it is on_string(F, x, y, hand)
on_string(F, *float_at(F, tie, rise=170, lean=70, bob=0.6), tie, tie=True)      # the coda: tied to the armrest
```

### `gloom_dust(F, x0, x1, y, fall=240, n=22, a=0.5, seed=77, t=None, band=None, day=None)`
The pale dust that falls from the scribble: `n` specks between world x0 and x1 that leave the
height `y` (or the underside of `band`), sink `fall` world units and fade, on `F.tb`.

---

## 5. The shawl (96.18)

### `shawl(F, neck, pel, ground, face=1, h=380, head=None, a=1, seed=4, s=None, spread=1, draw=1, churn=CHURN, w=1, t=None, day=None, halo=1, edge=1, cloud=None, settle=1) -> Tip`
The scribble lying on a SITTING child: heaped on the nape behind the head, down the back to the
ground, trailing behind (`spread`: 1 = about half of h); in front it only comes over the shoulder
and the upper arm: the face, the arms, the knees and the feet stay to be seen, so the pose still
acts. `neck`, `pel`: the figure's world joints `J["neck"]`, `J["pel"]`; `face`, `h`: as given to
`figure`; `head=(J["head"][0], J["head"][1], J["R"])` stays free. Draw it after the figure.
- `cloud`, `settle`: the cloud (its `band_cloud`, where it hung) sinks until it lies on the head,
  then slides off it and gathers on the shoulders: `settle` 0 = that cloud exactly (the same picture
  as `gloom` with those numbers), 1 = the shawl. Give it 2.5 s or more.
- `s`: the hand (default 0.46 for h = 380: small loops, pressed hard).
`band_shawl(neck, pel, ground, face=1, h=380, seed=4, s=None, spread=1, n=56) -> Band`: its band.

```python
J = figure(F, x, 742, 380, SIT_HUG, "child", 1, seed=3)
head = (J["head"][0], J["head"][1], J["R"])
Bc = band_cloud(x - 30, 240, 380, 135)                              # the cloud as it hung (hand-off B3)
shawl(F, J["neck"], J["pel"], 742, 1, 380, head=head, cloud=Bc, settle=F.seg(96.18, 98.8))
```

---

## 6. The lid (the choruses)

### `lid_for(cam, hang=235, above=130, s=None) -> dict`
The lid that suits a framing: `dict(s, y, depth)` for `ceiling`, `curtains`, `band_ceiling`. The
hand is `1 / zoom` (its loops are as large on screen as the cloud's were at zoom 1: that is what
makes the child small under it), the underside hangs `hang` screen px below the frame top, the
upper edge is `above` px above it. Call it with `F.cam` every frame: the lid then follows a
pull-back or a push-in by itself. `hang` may be animated (the lid comes lower: 138.26).

### `ceiling(F, x0=None, x1=None, y=260, a=1, seed=4, t=None, depth=340, s=1, ax=900, sag=None, rest=None, thin=None, amount=1, draw=1, churn=CHURN, w=1, halo=1, edge=1, day=None, glow=1, avoid=(), reach=4200, cloud=None, spread=1, front=None) -> Tip`
The scribble as a lid across the top of the frame. Its underside hangs about world `y` (with
bellies and scallops of its own, up to 200 `s` lower); its upper edge is the straight line
`y - depth`: keep that above the frame top, so that the frame shows its dark core and its rim.
- `x0`, `x1`: world extent; default: the frame and a margin, whatever the camera.
- `s`, `y`, `depth`: from `lid_for(F.cam)`. `ax`: the anchor (see the top).
- `cloud`, `spread`, `front`: the lid opens out of that cloud (`band_cloud(...)`): `spread` 0 = the
  cloud exactly (the same picture as `gloom` with those numbers), 1 = the lid. Between, the cloud
  lifts off the head and swells while the lid comes down out of the top of the frame to either
  side, a front that runs outward and has passed the frame at about `spread` 0.6 (`front`: its
  distance from the anchor in world units, if you want to time it yourself). Run `spread` down to
  gather the lid into a cloud. Give it 1.5 s or more.
- `sag=(x, d, width)`: it hangs `d` lower about world x (over the child).
- `rest=(x, y, k)`: one belly is let down to that world point: a heavy round sack about as wide as
  it is deep (148.5: onto the sitting child, with `avoid=[head]`; `k` over 2 s or more).
- `thin=(x, r, k)`: the thin pale place: about world x, out to the radius r, the lid is worn thin
  by `k` 0..1 (see `Band.thin`): from its edge inward the dark core gives way, first the rubbed
  dark, then stroke after stroke, and the lines that are left turn pale and are pressed lightly;
  in the middle third single pale loops with the paper between them, and a guess of light behind
  (`glow` 0..1: the lid's own breath of it). `k` moves on `F.t`: 155.6 to 157.0 up to 0.9 (above
  0.76 no dark stroke is left in the middle); it stays until the lid gathers into the high cloud.
  `r`: world units; `None` = 190 hands; never under 150 hands (`150 * s`), or no loop would fit.
  The film's: `THIN_PLACE` = `(X5 + 90, 250, 0.9)` (at zoom 1.2 to 1.6, where the film shows it, a
  place 600 to 800 px wide, its pale middle a third of that). The radius is in WORLD units while
  the loops grow with `1 / zoom`: in a wider frame give `r=None` (190 hands), or the place shrinks
  to a narrow column of pale loops (zoom 0.72: still a thin place; 0.36: a pale knot under the
  light). Costs 3 ms more than the plain lid.
  The light itself is weather's, drawn BEFORE the lid so that it shows between the loops and goes
  on down to the ground as a faint shaft (example below).
- `amount`: 0..1, how much of it is left: it gets shallower and loses strokes (the unravelling).
- `draw`: 0..1: it scribbles itself on from the anchor outward, out to `draw * reach` world units
  either way, the ragged front carrying the tips (a lid that is drawn on rather than opened out of
  a cloud; `(d0, d1)` wipes it from the middle).

### `band_ceiling(x0, x1, y=260, depth=340, seed=4, s=1, ax=900, sag=None, rest=None, thin=None, amount=1, n=None) -> Band`
Its band (give x0, x1 yourself: wide enough for every framing of the move).

```python
CLOUD = story.HANDOFF["B2"]["cloud"]                    # (X2 - 30, 250, 420, 150)
F.cam = Cam.ease(CLOSE, WIDE, F.seg(60.27, 62.47))      # the pull-back
w = seg(F.t, 60.27, 61.9)
Bc = band_cloud(*CLOUD, rest=(top[0], top[1] + 4, 1 - ease(seg(w, 0, 0.3))))    # it lifts off the head first
L = lid_for(F.cam)
ceiling(F, ax=CLOUD[0], sag=(x, 50 * L["s"], 600 * L["s"]), cloud=Bc, spread=w, **L)
# the same call for the rest of the chorus (spread stays 1); 85.75-90.5: spread runs down again
# toward band_cloud(...) at the child's new place, with ax = that cloud's cx

k = F.ramp(155.6, 157.0)                                # the thin pale place (s06; hand-off B6 keeps it)
x, r, thin = THIN_PLACE
gap_light(F, x, 60, F.cam.view()[1] - 40, x, 170, 742, a=0.45, open_=k)     # weather: before the lid
ground_line(F)
ceiling(F, ax=story.HANDOFF["B5"]["cloud"][0], thin=(x, r, thin * k), **lid_for(F.cam))
```

---

## 7. The curtains (182.3-201.25), the parting, the rip

### `curtains(F, y=260, ground=742, drop=1, gap=None, left=None, right=None, apex=None, depth=340, a=1, seed=4, s=1, ax=900, x0=None, x1=None, taut=1, rip=None, t=None, draw=1, churn=CHURN, w=1, halo=1, edge=1, day=None, sag=None, thin=None, tremble=0, cloud=None, spread=1, front=None, strands=None, strand_w=None, lit=1, stays=None) -> Tip`
The lid let down to the ground: a heavy curtain of tall loops and long strokes, pooling on the
floor. `y`, `depth`, `s` (from `lid_for`), `seed`, `ax`, `sag`, `thin`, `cloud`, `spread`, `front`:
the lid it hangs from, exactly as in `ceiling`; with the same numbers `curtains(drop=0)` is pixel
for pixel that `ceiling`, so use it for the whole of 182.3 on (the high cloud of hand-off B7 is
its `cloud=`). The lid of s08 and s09 is `lid_for(cam, hang=PART_HANG)` (215).
- `drop`: 0..1, how far it has come down (unevenly, in tongues; 3 s is a heavy fall).
- `gap`: the world x of the seam, where it parts (`PART_GAP` = `X5 + 180`: the performance's seam; formerly `X5 + 90`:
  "Where the seam is", below). Give it from the start: the few strands that hang at the gap are
  then there as soon as the curtain is down.

**The parting.** The curtain's edge at the gap is made of STRANDS, each `strand_w` wide (default
`STRAND_W * s` = 20 hands; 23.5 world units at the camera of B8), hanging from the lid to the
ground. The next three on either side always show as lines of their own: the fringe.
- `strands`: how many have been taken aside so far: a number for both sides, or `(left, right)`.
  The opening is exactly that many strands wide on each side, so it widens by a strand's width with
  every strand, and the light with it. The FRACTION of the number is the strand that is on its way:
  hooked at the height of the hand it gives a little toward the opening (it bows into the light),
  then it is pulled over into the grip and goes taut, and its lower end whips in and is drawn up
  into the bunch. A taken strand runs taut from where it hangs in the lid into the grip; most end
  in the bunch, every third hangs on below the hand. The bunch (a knot under the fist) grows with
  every strand.
- `strands=None`: THE COUNT FOLLOWS THE GRIPS: as many strands as fit between the gap and each
  grip, so the two edges of the opening are always in the two hands: a heave of the hands takes
  two strands in five frames, a hand that slips lets one go again, a hand that walks outward
  takes strand after strand. This is the way to drive it from a performance (`acting_pair.s08`
  gives the grips). A resting hand may hold a strand half taken, so in this mode the bow and the
  whip of the strand on its way are only hinted at (a strand cannot hang still in mid-whip), and
  a grip that shivers moves the edge it holds with it. A grip on the wrong side of the seam holds
  nothing (that side stays shut): if an opening will not follow the hands, the seam is elsewhere.
- `peel(t, attacks, dur=0.34, n0=0) -> float`: the number for `strands`: one strand for every time in
  `attacks` (seconds of the song), each taking `dur` seconds. Call it with `t - 0.07` for the other
  side (that hand is two frames late), so that the two hands are not a machine.
- `left`, `right`: the GRIPS: the world points of the hand that holds the left / the right bunch.
  A side without a grip stays shut. With a timed count (`peel`) the hands may be anywhere: best in
  the curtain a little beyond the opening's edge (a strand then visibly travels from the edge to
  the hand); with `strands=None` they ARE the edges.
- **Where the seam is.** `gap` is one world x for the whole of s08 and s09 (the strands are counted
  from it: move it and every strand slides). `acting_pair.s08` parts the curtain where the friend
  stood, over its own head: `gap = X5 + 180`, both hands plunging in there (attacks[4], 187.56),
  heaving apart to 90 units either side; from 197.2 the child walks the left bunch out to the
  place of hand-off B8 (`hold_B8`: the grips 287 units left and 109 right of that seam: the opening
  is then "parted about X5 + 90", as `story.HANDOFF["B8"]` says, but its seam, where it draws
  together at the top, is over the friend). With that performance use `gap=X5 + 180, strands=None`
  from the first frame of s08 to the last of the rip. `PART_GAP` (`X5 + 90`) and `PART_STRANDS`
  (8 a side) are the symmetric staging of the first proofs (a strand a side on each of the seven
  attacks, hands 188 units either side of the seam at B8); it does not fit `s08` as it is written.
- `taut`: 1 = the taken strands are straight lines under load, 0 = they belly. `tremble`: world
  units of shiver of the held strands on the TRUE time, coming and going strand by strand (2 to 3
  in the long silence when the grips themselves are still; `D.num["tremble"]`, 1.3, when they
  shiver already, as `s08`'s do: measured numbers in section 8). `lit`: 0..1, the light of the opening on
  the side of each strand that faces it. `apex`: the world y toward which the opening draws
  together at the top (default the top of the lid, above the frame: light falls in from above).
- `curtain_gap(cam, gap, strands=None, left=None, right=None, s=1, ground=742, strand_w=None) -> (x0, w0, y0, x1, w1, y1)`:
  the opening as the six numbers weather's `gap_light` / `shaft` take (a slit above the frame top,
  the patch on the ground between the two hanging edges): the light widens with the strands. Draw
  it BEFORE the curtains.
- Returns a Tip; `T.edges = (left_edge, right_edge)`, each a function of world y (array) giving the
  world x of that edge of the opening; `T.grips`: the grip of each side that holds a bunch (or None).
- It is paid by the screen it covers: do not make the hand smaller than `1.1 / zoom`.

**The rip.** `rip`: seconds since the sheet ripped (`F.t - 201.25`; `None` before; 0 is still the
held picture, to the pixel). Keep every other argument as it was at the rip: the last grips and
strands, `drop=1`, the lid's numbers of that camera (`lid_for(B8_CAM, hang=PART_HANG)`, not of
`F.cam` once the camera travels).
- The two curtains: every stroke breaks into pieces of line (the strands and the bunches too).
  Let go, each piece curls up as a taut thing does when it is cut (a hook, a C, now and then
  nearly a ring: it stays scribble), turns about itself and is rubbed away in its own time, from
  half a second on. The pieces that lay together fly as one loosening tangle: thrown outward from
  the gap as the tear passes (0 to 0.5 s), then falling as paper falls, sailing off, thinning.
  What reaches the ground lies on it until it is rubbed away. The rubbed dark of the curtain goes
  in the first 0.3 s (under weather's flash). Loose curls at 1.5 s, the last gone by 4.4 s.
- The lid shows behind them from 0.2 s on, cut into a few ragged pieces (about 430 hands wide, none
  over the opening): each sags a little, draws in to a lump whose ends lift off the lid's
  underside (a scrap of cloud, rubbed lightly), then drifts up and outward and tilts, losing its
  strokes: wisps in the upper corners by 6 s, nothing by 10.4 s. The pieces are fixed in
  the world: a travelling camera leaves them behind.
- `stays=(x, y)` or `(x, y, r)`: the piece that stays (`remnant`), coming up among the lid's pieces
  from 0.8 to 2.5 s. Start it in the lid over the child (at the camera of B8: about 60 units left
  of the child, world y 150, just under the lid's edge) and let it follow the child from there,
  lagging about a second, sinking to where it will ride (150 behind the free hand, 560 above it).
  After `rip = 10.4` the call draws nothing else: go over to `remnant` when you like.

```python
HIGH = story.HANDOFF["B7"]["cloud"]                                 # (X5 + 90, 110, 600, 150)
B7_CAM, B8_CAM = Cam(*story.HANDOFF["B7"]["cam"]), Cam(*story.HANDOFF["B8"]["cam"])
SEAM = X5 + 180                                                     # where acting_pair.s08 parts it (see above)
F.cam = Cam.ease(B7_CAM, B8_CAM, F.seg(182.4, 184.2))
L = lid_for(F.cam, hang=PART_HANG)
D = s08(F.t)                                                        # acting_pair: the two, and their grips
gl, gr = D.pts["grip_l"], D.pts["grip_r"]                           # None until the friend's hands are in (187.56)
if gl is not None:                                                  # the light through the opening: BEFORE the curtains
    G = curtain_gap(F.cam, SEAM, None, gl, gr, s=L["s"])
    gap_light(F, *G, a=0.45 + 0.55 * D.num["lit"], open_=min(1, G[4] / 40), t=F.t if F.t >= 193.0 else None)
T = curtains(F, ax=HIGH[0], cloud=band_cloud(*HIGH), spread=seg(F.t, 182.4, 183.6), drop=seg(F.t, 182.7, 184.25),
             gap=SEAM, left=gl, right=gr, strands=None, tremble=D.num["tremble"], **L)
D.show(F)                                                           # then the figures, their hands on the grips

ATTACKS = (184.34, 185.14, 186.26, 186.65, 187.56, 188.14, 188.90)  # or, timed: a strand a side on each attack
n = peel(F.t, ATTACKS) + ease(seg(F.t, 200.40, 200.95))             # (the last pull: PART_STRANDS, 8, at B8)
n = (n, peel(F.t - 0.07, ATTACKS) + ease(seg(F.t, 200.47, 201.0)))  # the right hand a moment later
gap_light(F, *curtain_gap(F.cam, PART_GAP, n, gl, gr, s=L["s"]), a=min(1, 0.35 + 0.1 * n[0]), open_=min(1, n[0]))
T = curtains(F, ..., gap=PART_GAP, left=gl, right=gr, strands=n, tremble=2.6 * seg(F.t, 193.0, 193.4), **L)

since = F.t - 201.25                                                # s09: the same call with the numbers of B8, and rip
D8 = hold_B8(201.25)                                                # the grips as they were at the rip
L8 = lid_for(B8_CAM, hang=PART_HANG)                                # (not of F.cam: the camera travels from 205.9)
RIP = (X5 + 60, 300, X5 + 250, -340)                                # weather's tear: up between the curtains, out of the frame
op = F.seg(201.25, 201.25 + 8 / 30)
tear_shafts(F, *RIP, X5 - 700, X5 + 1100, 782, 120, op)             # weather, before
k = ease(seg(F.t, 203.25, 208.25))                                  # the piece that stays: out of the lid, after the child
cx1, hy = child_x(F.t - 0.9), free_hand_y                           # (yours: where the child was 0.9 s ago; its free hand's height)
piece = (cx1 - 60 - 70 * k, 150 + (hy - 560 - 150) * k)
curtains(F, ax=HIGH[0], drop=1.0, gap=SEAM, left=D8.pts["grip_l"], right=D8.pts["grip_r"], strands=None,
         tremble=D8.num["tremble"], rip=since, stays=piece, **L8)   # (the shiver dies in the first 0.2 s)
tear(F, *RIP, 120, op, since)                                       # weather, after; then the figures and scraps
```

---

## 8. Numbers

Costs, 1080p, one core, 10 calls after a warm-up (`gloom/cost.txt`; the lid, the curtains and what
follows them measured again in `gloom2/cost.txt`, on a machine shared with other work):

| | ms | | ms |
|---|---|---|---|
| `gloom` 430 x 150, zoom 1.0 / 1.27 / 1.6 | 12 / 14 / 17 | `shawl` | 7 |
| `gloom` 300 x 100; 520 x 180 at zoom 0.9 | 9; 11.5 | `tangle` 6 loops / `on_string` | 0.9 / 0.8 |
| `ceiling`, zoom 1.0, 0.5, 0.26, 0.205 (`lid_for`) | 32 to 35 | knot, 12 loops | 1.3 |
| `ceiling` with the thin place (zoom 1.2) | 37 to 38 | `strand` / `cross_out` | 0.2 / 0.3 |
| `ceiling`, zoom 0.26, `s = 1` | 22 | `unravel` 2000 out / `gloom_dust` | 1.0 / 0.1 |
| `curtains`, zoom 0.85: closed / a strand peeling / 7 a side / held, 8 a side | 33 to 35 / 36 to 39 / 38 / 36 to 38 | `remnant` / `wind_up` | 4.3 / 4.3 |
| `curtains(rip=)`: 0.05 / 0.25 / 0.55 / 1.0 / 1.75 / 2.5 / 3.25 / 4.75 / 6.75 / 9.75 / 10.75 s | 40 / 60 / 56 / 59 / 42 / 27 / 19 / 10 / 8 / 7 / 5 (a tenth more with other jobs running) | `curtain_gap`, `peel` | 0.0 |

Budgets (cloud 12, lid 35, curtains 40, small tangle 2): the cloud is over its budget in close
framings (it is paid by the screen it covers); the lid in a close two-shot touches its budget and
is 2 to 3 over with the thin place; the curtains keep theirs while they hang, part and are held,
and are OVER it for the first 1.8 seconds of the rip (55 to 61 ms for a second, 66 at most with
other jobs running; 42 to 47 at 1.75 s, under 40 from 1.9 s on): the flying pieces and the lid's
pieces are two masses in one frame there. The whole film frame of that second (paper, plain,
hills, tear and its shafts, two figures, scraps, finish; no sky) measured 139 to 154 ms, so the
frame budget of 200 holds. A cloud opening into a
lid costs 12 rising to 32. The same at the extreme cameras (zoom 0.205, 0.26, 1.6): lid with thin
place 37 to 41, curtains held 35 to 38, the rip 57 to 63; wholly off screen the curtains cost 3,
the rip 8, the piece 1.5 (`gloom2/review/numbers.txt`).

Flicker (`gloom/flicker.txt`, `gloom2/flicker.txt`; static camera; mean luma change in levels and
percent of pixels over 8 levels on a boil step): cloud in the room 0.31 / 0.9 (the scribble alone on
a bare sheet 0.08 / 0.3); lid, wide 0.03 / 0.15; the lid with its thin place, held 0.10 / 0.34
(with plain, light and the two figures 0.19 / 0.68); curtains closed 0.15 / 0.5; parted, 7 strands
a side 0.08 / 0.28 (full scene 0.14 / 0.51); the piece that stays 0.06 / 0.20; the tangle on its
string with the two and the hills 0.17 / 0.65; inside a pair 0.000 in all of these. In both
silences exactly 0 on every step (cloud, lid with its thin place, the piece and the tangle
56.2-58.4; lid 197-198; curtains with `tremble=0` and grips that stand still). What moves in the
long silence is what is told to (levels a frame, the largest in brackets): `tremble=2.6` on still
grips 0.36 to 0.43 (0.52); the grips of `acting_pair.s08`, which shiver by themselves (1.3 units),
with `strands=None` and `tremble=0` 0.48 (0.93), with `tremble=2.6` on top 0.69 (0.98); that whole
scene with figures, light and dust 0.8 (1.2): as lively as the boil elsewhere, at 30 a second,
all of it in and round the held strands. For a stiller silence give `tremble=D.num["tremble"]`
or less. Targets: under 1.2 levels and 6 percent.

Hand-overs (`review/handover.py`): `gloom` against `ceiling(cloud=, spread=0)`, `ceiling` against
`ceiling(spread=1)` and against `curtains(drop=0)`: identical pictures (0 on every pixel); `gloom`
against `shawl(settle=0)`: 0 when both are given the head (`avoid=[head]` / `head=`). For scale: the
same cloud called with another churn differs by 116 levels at most, 3.3 percent of the frame. The
hand-offs of the story: the last section. The same frame rendered in two processes is identical
(cloud, lid, thin place, curtains parting and held, the rip at 0.4, 1.5 and 5 s, the piece, the
winding up, the tangle: ten film frames, md5 of the finished frame).

## 9. What changed

From the prototype:
- `gloom`: same positional arguments. `loops` now only sets the hand; new `rest`, `tug`, `draw`, `s`,
  `avoid`, `lump`; it returns a `Tip` (still a tuple `(x, y)`).
- `ceiling(F, x0, x1, y, ...)`: `y` is now the level of the UNDERSIDE (it was the middle of three
  masses), `depth` is world units (a value up to 8 is still read as the old factor), and without
  x0, x1 it covers the frame.
- `on_string(F, x, y, hand, t, s)`: unchanged call; the tangle is rounder (112 x 84 at s = 1).
- `scribble_pts(u, seed)`: unchanged (the tree's leaves use it).

From the first version of this module (if you wrote against the earlier doc):
- New: `lid_for`, `spread_band`, `morph_band`, `CHURN`; `ceiling` and `curtains` take `cloud=`,
  `spread=`, `front=`; `shawl` takes `cloud=`, `settle=`. Use these for cloud to lid and cloud to
  shawl instead of `mass(F, mix_band(...))`, which stepped at both ends (other churn, other edge).
- Every form now churns at `CHURN`; the lid's paler rim is in its band (`pale` 0.6), so `edge`
  defaults to 1 everywhere (`edge=0.6` on a lid would now be 0.36).
- `shawl` no longer covers the child's body; its hand is smaller (`s` default 0.46, was 0.7).
- `curtains`: a strand's width is `20 * s` (was "about 26 world units"); the edges are fans of
  strands with a knot in the grip.
- `mix_band` interpolates anchor and hand by the weight at the anchor (was: the mean weight).
- `rest=` also presses the loops flat on the point; a let-down belly of the lid is a round sack.
- `UNRAVEL_LINE["w"]` is 8.5 (was 7); the lying line coils more.

From the reviewed version (three turning points reworked; every old call still works):
- The thin place of the lid is a field of its own (`Band.thin`), no longer a lighter pressure all
  over (`dens`): strokes drop out, lines turn pale as they run into it, single loops are left. Its
  falloff is `(1 - u ** 1.6) ** 1.6` out to the radius (it was a bell that reached further).
- `curtains` parts by strands: new `strands`, `strand_w`, `lit`, `stays`; new `peel`, `curtain_gap`,
  `STRAND_W`. The opening is a slot as many strands wide as were taken (it was a tent from the
  apex to the grips); the stuff beside it bunches against its edge. With `strands=None` and grips
  that move apart (the first version's recipe) the picture is close to the old one.
- `curtains(rip=)` is new through and through (shards, pieces of lid, `stays`); it lasts 10.4 s
  (was 8.5). New `remnant`, `wind_up`, `REMNANT_R`; `wane` is kept and ends in `wind_up`; `tangle`
  has `rot`.
- New `handoff_gloom` and its numbers `HANDOFF_GLOOM`, `PART_HANG`, `PART_GAP`, `PART_STRANDS`,
  `THIN_PLACE`, `STRING`. `mass(keep=)` may be an array. The package now exports every name.

From the second review (no call changed its meaning; two got arguments):
- The rip: the pieces of the curtains curl up as they fly, turn and are rubbed away one by one
  (they were sheaves of straight sticks that died shard by shard). The lid's pieces are lumps that
  taper to their own middle, rubbed more lightly (they were dark wedges on the lid's underside).
- `curtains(strands=None)` is the way to drive the parting from a performance: the strand on its
  way is shown without its whip there. The bunch hangs under the fist (it was behind the hand).
- `handoff_gloom(..., gap=None, strands=PART_STRANDS)`: the seam and the count of hand-off B8 may
  be the performance's own (see "Where the seam is" and the last section).

## 10. Limits

- The lid and the curtains cost by the screen they cover; two large forms in one frame need care
  (the first two seconds of the rip are that case: section 8).
- A cloud's belly asked to reach far below it (more than about 0.8 of its depth) becomes a funnel.
- The thin place is one place per lid, as wide as a few loops at least; in a very wide frame (zoom
  0.36) it reads as a pale patch of the lid more than as single loops.
- The parting has one gap; each side has one grip (two hands on one curtain: give the grip between
  them). The strand on its way bows into the opening where a figure may stand in front of it: at
  the height of the hands and above it shows, below it the figure hides it. The bunches are small
  (a knot of 26 units radius for eight strands, hanging under the fist).
- With `strands=None` a grip that shivers shakes its edge of the opening and, a little, the loops
  of the curtain beside it (out to about 450 units): section 8 has the numbers.
- A strand is taken in the order it hangs; the count cannot go down by letting one go again
  without the same motion run backward (it does run backward, and reads as a strand slipping back).
- The pieces of the ripped curtains are its own strokes, which are long: for the first third of a
  second they are still sheaves of nearly straight line (under weather's flash), then tangles of
  large curls (a piece is 200 to 400 units long), loose curls from about 1.3 s. It is a storm of
  line for a second and a half, not torn cloth; most pieces are rubbed away in the air. The lid's
  pieces come up under the flash (0.2 to 0.6 s after the rip) rather than being the same strokes
  as the curtain's upper part, and for their first second or so the flank each turns to the
  opening is still a straight slope; they are fixed in the world, so which corner keeps its wisps
  longest depends on the lid's own bellies and on where the camera goes (in the proofs the left
  is faint after 205.5, the right keeps wisps to about 208.5). The piece that stays comes up by pressure (a fade of
  1.7 s behind the flying pieces), not by being drawn.
- The piece that stays is a scrap of cloud in a small hand (loops 30 to 100 units): at zoom 0.75 it
  is 180 px wide and reads as a dark scrap with loops, not loop by loop.
- While a cloud spreads into a lid its ends turn up toward the frame top for three or four frames.
- The unravelling does not eat the mass where the line leaves it: the lid gets shallower all over
  (and so the thin place's surroundings move with every pull).
- The shawl is made for sitting poses seen from the side (`SIT_HUG`, `SIT_FLOOR`, `SIT_LIFT`); for
  a standing child use a cloud with `rest`.
- The scribble's lines do not boil; only the stroke being made changes. If it looks too still
  beside the boiling chalk, that is the brief ("only the newest loops change"), not a setting.

## 11. HAND-OFF RECIPES

At a hand-off of `hx/story.py` both neighbouring modules draw the scribble with ONE call:

### `handoff_gloom(F, name, crown=None, head=None, left=None, right=None, hand=None, a=1, tremble=2.6, gap=None, strands=PART_STRANDS)`
`name`: `"B1"` .. `"B10"`. Everything comes from `story.HANDOFF[name]` and the hand-off's own camera
(not `F.cam`); you give the world points of the figures as they stand there (from the performance's
rest state: `hold_B6(t).child.joints()["crown"]`, `hold_B8(t).pts["grip_l"]` ...). `gap`, `strands`,
`tremble`: B8 only (below). Returns what the form returns. The earlier module
calls it in its last frames (its own moving numbers must have arrived at these values at least
0.25 s before), the later one in its first; the forms that follow start from the same call, which
is why the table gives it. `HANDOFF_GLOOM[name]` = (what it is, the points it wants).

| | t | what both draw (this is what `handoff_gloom` calls) | points | order |
|---|---|---|---|---|
| B1 | 36.27 | `T = gloom(F, 1010, 236, 380, 128, rest=(crown[0], crown[1] + 6, 1.0), avoid=[head])`; `strand(F, crown, T.band.root(crown[0] + 40, 0.4), slack=0.8)` | `crown`, `head` | after the child |
| B2 | 58.60 | the same with `gloom(F, 2170, 250, 420, 150, ...)` | `crown`, `head` | after the child |
| B3 | 91.77 | the same with `gloom(F, 3670, 240, 380, 135, ...)` | `crown`, `head` | after the child |
| B4 | 115.77 | the same with `gloom(F, 3730, 250, 420, 150, ...)` | `crown`, `head` | after the child |
| B5 | 138.20 | the same with `gloom(F, 4270, 240, 520, 180, ...)` | `crown`, `head` | after the child |
| B6 | 158.86 | `T = ceiling(F, ax=4270, thin=(4390, 250, 0.9), **lid_for(Cam(4390, 590, 1.2)))` (= `s 0.8333, y 335.8, depth 304.2`); `strand(F, crown, T.band.root(crown[0] + 40, 0.3), slack=0.8)` | `crown` (or the fist that holds the strand) | before the figures |
| B7 | 182.30 | `gloom(F, 4390, 110, 600, 150)` | none | after the figures |
| B8 | 201.25 | `curtains(F, ax=4390, drop=1.0, gap=gap, left=left, right=right, strands=strands, tremble=tremble, **lid_for(Cam(4390, 470, 0.85), hang=215))` (= `s 1.1765, y 87.6, depth 405.9`); defaults `gap=PART_GAP` (4480), `strands=None` (the count follows the grips), `tremble=2.6` | `left`, `right`: the two grips | before the figures |
| B9 | 226.76 | `on_string(F, *float_at(F, hand, rise=330, lean=-110), hand)` | `hand` | after the figures |
| B10 | 244.50 | `on_string(F, *float_at(F, hand, rise=330, lean=110), hand)` (the child faces left) | `hand` | after the child |

The numbers are `story.HANDOFF[name]["cloud"]`, `THIN_PLACE`, `PART_GAP`, `PART_STRANDS`, `PART_HANG`,
`STRING`, and the lid's anchor: the `cx` of the cloud it opened out of (B5's for B6, B7's for B8).
`head = (J["head"][0], J["head"][1], J["R"])` keeps the face clear of the cloud (optional, but both
sides must agree; give it: the large cloud of B5 would hide the face). The weather's light belongs
to the same instant: at B6 `gap_light(F, 4390, 60, F.cam.view()[1] - 40, 4390, 170, 742, a=0.45)`,
at B8 `gap_light(F, *curtain_gap(cam, gap, strands, left, right, s=1.1765), a=1.0, t=F.t)`.

**B8 with the performance as it is written.** `acting_pair.s08` parts the curtain at `X5 + 180` and
its `hold_B8` has the grips 287 units left and 109 right of that seam (section 7, "Where the seam
is"); the defaults above (seam `X5 + 90`, eight strands a side) then put the left bunch's strands
and the opening's top where no hand took them. With that performance both modules call

    D = hold_B8(F.t)                                    # s08 returns exactly this from 201.0 on
    handoff_gloom(F, "B8", left=D.pts["grip_l"], right=D.pts["grip_r"], gap=X5 + 180, strands=None, tremble=D.num["tremble"])

and s08 and s09 give `curtains` the same `gap`, `strands=None` and `tremble` (the example of
section 7). Which of the two stagings the film uses is one decision for both modules; this one
is what `gloom2/review/` shows and tests.

**The form on either side** (what the hand-off's call turns into, with the number that moves):

| | before it | after it |
|---|---|---|
| B1 | s01: `gloom` (it followed the head) | s02: `gloom`, `cx` and `rest` follow the walking child |
| B2 | s02: `gloom` | s03: `ceiling(F, ax=cloud[0], cloud=band_cloud(*cloud, rest=...), spread=w, avoid=[head], **lid_for(F.cam))`, `w` from 0 |
| B3 | s03: that `ceiling`, `spread` back at 0 over `band_cloud(*B3 cloud, rest=...)`, `ax` = its cx | s04: `gloom`; from 96.18 `shawl(..., cloud=band_cloud(*cloud, rest=...), settle=k)` |
| B4 | s04: `gloom` | s05: `gloom` |
| B5 | s05: `gloom` | s06: `ceiling(cloud=band_cloud(*cloud, rest=...), spread=w)`, `ax = cloud[0]` to the end of s06 |
| B6 | s06: `ceiling(ax=4270, thin=(4390, 250, 0.9 * F.ramp(155.6, 157.0)))`, no belly, no sag left | s07: the same with `amount=1 - 0.17 * pulls`; `unravel` only from 160.0 on |
| B7 | s07: `ceiling(F, ax=4390, cloud=band_cloud(*HIGH), spread=0, ...)` (the lid gathered: any lid numbers) | s08: `curtains(F, ax=4390, cloud=band_cloud(*HIGH), spread=w, drop=d, gap=PART_GAP, **lid_for(F.cam, hang=PART_HANG))`, `w`, `d` from 0 |
| B8 | s08: `curtains(..., gap=, strands=)` as it was called all through s08, the grips at rest from 201.0 (`strands=None`), or `n` = 8 on both sides from 201.0 (`peel`) | s09: the same call with the grips of 201.25, `rip=F.t - 201.25, stays=...` |
| B9 | s09: `wind_up(F, x, y, 1.0, hand)` (it IS `on_string`) | s10: `on_string`, the hand moving |
| B10 | s10: `on_string` | s11: `on_string`; tied to the armrest later (`tie=True`) |

Proof (`gloom2/handover.py test`, `gloom2/handover.txt`): for each hand-off the form before and
the form after, called at the hand-off's instant as above, against `handoff_gloom`: 0 levels on
every pixel for all ten, on both sides. One frame's worth further into the move that follows, the
largest steps are the rip's first frame (1.1 levels mean, 2.5 percent of pixels over 8: the slam)
and the lid as the unravelling begins to make it shallower (1.3 levels: the whole lid gives); all
others are under 0.2 levels (0.01 for a cloud beginning to spread). `gloom2/handoff_states_B1-B10.jpg` shows the ten states
with stand-in figures; `gloom2/review/handoff_states.jpg` with the performances' rest states.
The same on the film's own frames (`gloom2/review/measure.py hand`, in `numbers.txt`): the form
before at the last frame before each hand-off and the form after at the first frame after it,
each against `handoff_gloom` at that frame: 0 on every pixel for all ten, and for B8 with
`hold_B8`'s grips, `gap=X5 + 180, strands=None` (s08's own call; s09's with `rip=0`). The step
between those two frames of `handoff_gloom` itself is the boil of that moment: 0 to 0.15 levels
(0.4 at B8: the held strands shiver).
