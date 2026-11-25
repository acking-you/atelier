
## figures / birds (`figures.py`, `birds.py`)

### `hx.kit.figures`: the child and the friend

Pixel-art sprites (refs `hx/_concept/00_*_px.jpg`, `01_*.jpg`). One rig, two costumes, built at
real-pixel resolution: every shape is a flat material rasterised without anti-aliasing into a small
buffer (one cell = one film pixel), then in whole pixels: the face is stamped, a one-pixel dark
outline goes round the silhouette and between overlapping parts (arms on the body, legs, pocket,
hood, chin), materials become colours (pre-snapped to the centre of the pixel stage's bands, so
flat stays flat), the rim light lands on the lit edge, and the buffer is drawn x5 with nearest
sampling at a pixel-aligned spot. Nothing is blurred or blended.
`who="child"`: big messy tufted black hair (lighter clusters, cowlick, fringe to the eyes), pale
face, tired blue-grey eyes, oversized dark navy hoodie (hood down, two pale drawstrings, kangaroo
pocket), loose grey-blue trousers, pale sneakers. `who="friend"`: brown bob with fringe and a rose
clip, amber raincoat (hood down, buttons, two patch pockets, flared hem, a white collar), dark
leggings, tall cream boots; upright (the rig damps `slump` to 18 %). Head with hair is about 40 %
of the height. Rig units: h = standing height, x = the way the figure faces, y up; limb angles are
absolute, measured from straight down, positive forward.

    anchors = draw(canvas, who, x, y_feet, h, pose=None, facing=1, tint=0.0, alpha=1.0,
                   dissolve=0.0, eye="half", smile=0.0, head_tilt=0.0, wind=0.0, t=0.0,
                   wind_dir=None, shadow=0.35, cushion=False, cushion_color=..., seed=0,
                   mood=None, light=(-0.6, -0.8), rim=None, blink=True,
                   view="three", phone=None, tray=False, backpack=False)

- Sizes: wide 140 to 180 (28 to 36 px: eyes are dark dots, no mouth unless smiling), standard
  240 (48 px, the reference sprites: 2x3 eyes with a highlight, strings, pocket, buttons), close
  550 to 650 (110 to 130 px: big eyes with lash, iris, pupil, two highlights, brows, nose, shaped
  mouth, blush; hands with thumb and finger slits). Detail switches by the head's size in pixels
  (`_fig_face.size_class`), never fades. Cost: about 0.9 / 1.2 / 2.0 ms at 160 / 240 / 600.
- Pixel discipline: `x, y_feet` are snapped to the 5-unit grid inside `draw` (in device space
  when the canvas is only translated); face features sit on whole pixels from the head centre.
  A still pose gives the same pixels every frame, except a blink (one or two frames about every
  4 s) and breathing (head and shoulders up one pixel for part of a 3.9 s cycle, only at h >= 200).
  Hair and hem follow-through move five times a second and only with wind or a walk swing.
- `view`: `"three"` (default: three-quarter, how far set by `Pose.turn`, 0 near profile .. 0.6
  full), `"side"` (profile), `"back"` (three-quarter from behind: hair, hood on the back, the edge
  of a cheek; every pose), `"front"` (straight on) and `"back_front"` (straight from behind).
  Front/back_front support standing, walking toward / away (legs alternate in depth), knees-up
  sitting (`sit_floor`, `phone_look`, `curled`), cross-legged (`sit_cross`) and arms out
  (`arms_open`, `push_up`, `wave`, via `Pose.spread_*`); joint heights come from the same Pose.
- `y_feet` is the ground, or the seat surface for seated poses (the lowest contact rests on it
  when `pose.plant` is 1). `head_tilt` > 0 looks up; `tint` 0..1 turns the child's hoodie teal.
- Face: `mood` -1 (heavy) .. 1 (glad; default from `set_default_mood`) sets lids, mouth, brows and
  blush; `eye` `"half" | "open" | "closed" | "up"` (the wary look up: lid high, white below the
  iris) and `smile` (< 0.35 the very small first smile, < 0.7 a smile, above that open) override.
  Heavy/empty (low mood: low lid, no highlight), closed, up, first smile and open smile are all
  distinct at 48 px and at 120 px; closed eyes with a big smile arch up.
- `wind` 0..1 lifts tufts, hood and hem toward `wind_dir` (screen sign, default `-facing`).
  `alpha` < 1 thins the sprite with a screen-fixed ordered stipple (no half colours). `dissolve`
  0..1 stipples it down to about 45 % and breaks the lee edge (downwind, else behind) into single
  pixels that drift away and up; `seed` varies them.
- `light`: screen direction toward the light; the shade tone falls on the far side, whole pixels.
  `rim=(colour, strength)` (or a bare strength: pale warm) lights the one-pixel edge on the lit
  side; a cool rim, e.g. `((0.62, 0.74, 0.95), 0.75)`, makes the dark child read on indigo.
- Props: `phone="cold" | "warm" | "dark"` a lit phone in the hands (between them when they are
  together, else the near hand; at the ear with `phone_ear`); `tray=True` a lunch tray with a bowl
  and a cup in both hands (pose `carry()`); `backpack=True` a small pack with straps (behind the
  back, or over it in the back views); `cushion=True` the hugged cushion (`curled`).
- `shadow` is the alpha of the contact shadow under grounded parts (0 to draw your own).
- Returned anchors (canvas units): `head eye top ear chest shoulder elbow_n hand_n hand_f hold`
  (between the hands) `foot_n foot_f hip seat`, plus `phone` / `tray` when drawn. `_n` = near.

Poses (`Pose` is a frozen dataclass of floats; `blend(a, b, w)` lerps every field; `pose(name, ...)`
calls a preset by name, `POSES` lists them). Hand state per hand: `hand_n/_f` 0 relaxed .. 1 open
palm, `fist_n/_f` 0..1 curled (holding, fist). `legs_front` 1 = near leg over the body, 2 = both.
`spread_n/_f` 0..1 swing an arm out to the side in the front/back views; `look` >= 0.5 turns the
head back over the shoulder.
`stand(slump=0.7)`, `curled()` (sofa corner: knees up in front of the chest, feet together, head
bowed; with `cushion=True` a big cushion on the knees covers the lower face and both arms wrap
round it; best with `view="front"`, as in v1a and the coda),
`sit_floor(slump, hold=1)` (back to the wall, knees high, hands on the knees), `phone_look(slump)`,
`sit_cross(slump)` (best `view="front"`; with `eye="closed"`), `walk(phase, slump=0.7, stride=0.40)`
(high slump = the slumped walk), `walk_light(phase, stride=0.56)` (lighter, longer stride),
`run(phase, stride=0.95)`, `lean_wind(phase, slump, stride=0.26, hug=1)` (bent into wind, an armful
at the chest), `reach_up()` (tiptoe, near arm up, face lifted), `arms_open()` (best front, with
`head_tilt`), `look_back(slump)`, `hand_out()`, `take_hand()`, `push_up(lift=0)` (both arms up on
tiptoe; `lift` > 0 jumps), `hold_string()` (kite string, anchor `hand_n`), `carry()` (tray),
`phone_ear(base=None, who="child")` (near hand at the ear on any base), `wave(t, slump, side="n")`
(`phone_ear(wave(t, side="f"), who="friend")` waves with a phone at the ear), `hero_stand()`.
`reach(base, target, side="n", elbow=-1, who="child")` solves one arm to a target (local x, y or
`("head", dx, dy)` in head radii). The close two-shot (`hand_out` / `reach(take_hand(), ...)` at
about 600 units, waist up) shows open hands with thumb and fingers.

Walk and run are phase-locked and stepped: the phase is quantised to 8 sprite frames per cycle
(`STEPS`); advance the figure's x by `stride * h` per cycle (phase 0..1 = two steps).

Helpers: `contact_shadow(canvas, x, y, width, alpha=0.35, color=INK, squash=0.20, stipple=False)`:
a flat hard-edged ellipse of whole pixels (translucent tone, or an ordered half-tone with
`stipple=True`). `hero_shadow(canvas, x, y_base, h, rise, t, color=INK, alpha=0.6, facing=1,
soft=1.0)`: the flat hard-edged wall shadow standing up in ten steps with `rise` 0..1 from the
curled lump into a caped hero (about 1.45 h tall, fists on hips); the cape moves five times a
second; `soft` is ignored. Private modules: `_fig_draw` (sprite raster, outline, rim, stipple,
dissolve), `_fig_face` (pixel faces), `_fig_front` (front and straight-back views), `_fig_geom`.

### `hx.kit.birds`: crows and small birds

Pixel birds: hand-placed pixel maps (`_thg_birdmaps.py`, facing right), three size classes per
shape, coloured and cached as sprites, blitted 5x at snapped positions (no resampling, no
rotation: nose up or down is a one-step column shear). `s` is the body length in logical units
(5 = one pixel): perched crows read at 6 to 13 px (40 to 65 units); flying crows use 9 and 13 px
maps, and under about 6 px become 3- or 5-pixel marks that still flap; above twice the largest
map the map is doubled. A wingbeat is four stepped poses (up, mid, down, mid; only `phase % 1`
counts); perched heads turn in three steps (forward, frontal, back). `small` 0..1 morphs a crow into an ordinary small bird (lighter `SMALL` grey-brown, 42 %
smaller, rounder, belly and wing tones, quicker wingbeat): the shape switches at 0.5, the colour
steps in quarters. `color` overrides. Crows are `CROW` (#1C2030, just above INK).

- `perched(canvas, x, y, s, t, seed=0, facing=1, color=None, small=0.0, alpha=1.0)`: standing at
  its feet (x, y) on a wire, tail hanging past it, head turns per seed (`head_turn(t, seed)`).
- `perched_row(canvas, xs, ys, ss, t, seeds, facings, color=None, small=0.0, alpha=1.0, t_land=None)`:
  a whole row; `t_land[i]` (or None) makes bird i land at that time. 12 birds 0.7 ms.
- `landing(canvas, x, y, s, t, t_land, seed=0, facing=1, ...)`: comes in from behind and above
  for 1.4 s (flapping, then a level glide), flares the wings up for the last 0.3 s, folds them in
  two steps over 0.35 s, settles one pixel down for a beat, then sits.
- `flying(canvas, x, y, s, phase, heading=0.0, bank=0.0, color=None, small=0.0, alpha=1.0)`:
  centred on the body; heading in screen radians (0 = toward +x, + turns toward +y). `bank` is
  accepted and ignored.
- `draw_flock(canvas, xs, ys, s, phases, headings, banks=None, scales=None, color=None, small=0.0,
  alpha=1.0)`: 40 birds about 1.1 ms.
- `flock_wheel(n, t, center, radius, seed=0, speed=1.0, squash=0.42, small=0.0)` and
  `flock_scatter(n, t, t0, origin, seed=0, spread=1.2, speed=260, start=None, small=0.0, up=-pi/2)`
  return dicts of arrays `x y heading phase scale bank` for `draw_flock`. For the scatter into small
  birds, pass the wheel's positions at t0 as `start` and ramp `small` over time.
  `flap_rate(small)` gives wingbeats per second.

## look / cloud / lights / scraps (`look.py`, `cloud.py`, `lights.py`, `scraps.py`)

Units: logical 1920x1080 px, seconds, colours `(r, g, b)` floats. Every helper is a pure function
of its arguments (`t` defaults to `ctx.t` where a `ctx` is taken); randomness from `prims.hash01`.
Costs measured at 1920x1080 on this machine (halve or quarter them at scale 0.5).

### `hx.kit.look`

Everything here draws straight on the real pixel grid (private `_atm_px.py`: a numpy buffer over
the device pixels a shape covers, ordered stipple on the same 4x4 Bayer matrix as the pixel
stage, enlarged x5 with nearest sampling). Shapes are given in local units and the canvas matrix
is honoured (camera pans and zooms land on whole pixels). No mask blur draws a form; soft energy
goes on `ctx.glow` only.

- Palette: `INK INDIGO DUSK SLATE AMBER PERSIMMON ROSE PAPER RAIN` (from `mv.engine.palette`),
  fog greys `FOG_DEEP FOG FOG_PALE FOG_LIGHT`, night `NIGHT_BLUE COLD_LIGHT` (a lamp, a phone, a
  cold rim), `WINDOW_WARM WINDOW_COLD`, `SUN_GOLD` (a cloud's lit rim at sunset), late colours
  `MEADOW MEADOW_DEEP MEADOW_LIGHT SKY_BLUE SKY_DEEP PEACH CREAM_CLOUD ROOF_RED ROOF_BLUE ROOF_OCHRE
  TEAL` (the hoodie), `FLOWERS` (5 colours).
- `with graded(ctx, sat=None, cool=None, bounds=None):` everything drawn on `ctx.canvas` inside is
  graded as one layer (colour matrix). At hope 0 every colour goes to its luma on the line INK ->
  `COLD_HI`, lifted by `COLD_LIFT`: a cold indigo-and-slate monochrome that keeps its blue (mid grey
  -> #63718F, white -> #C5DDFF, amber -> #A3B1D3), keeping `sat_for(hope)` (0.12 at 0) of its own
  colour; `cool_for(hope)` (1 at 0, gone by 0.9) blends toward a plain drain, so colours return
  with hope; identity at 1. INK stays INK. Paint warm accents after the block. 5 ms full frame.
  `grade_filter(sat, cool)` gives the bare filter.
- `reveal(ctx, draw_fn, cx, cy, radius, soft=60, sat=None, cool=None)`: the colour ring.
  `draw_fn()` paints the world on `ctx.canvas`, twice (graded, then true colour inside the disc);
  the ring's edge is an ordered stipple `soft` units wide on the pixel grid; once the disc covers
  the frame the world is drawn once. Cost = two world draws + about 3 ms. Draw glow separately.
- `sky(canvas, rect, mood, positions=SKY_POS, bands=None, zone=2.5)`: opaque banded sky, flat
  horizontal bands meeting across a stipple `zone` pixels tall (`bands` default: one per visible
  lightness step, 6 to 22). `mood` is a name or `{name: weight}` (OKLab): `night overcast lid sunset
  day golden` and `rain_night` (p1a_street, v1a), `rain_dusk`, `storm` (under the lid), `blue` (the
  deep late sky). `SKIES`, `sky_colors(mood)`. 3 ms full frame.
- `sun_disc(ctx, x, y, r, color=PERSIMMON, halo=2.2, alpha=1, core=None, glow=0.8, canvas=None)`:
  hard disc, hotter core, two flat stippled halo rings, energy on glow. 1 ms.
- `cumulus(canvas, x, base, w, h, t=0, seed=0, mood="day", sun=(-0.6, -0.75), drift=0, alpha=1,
  tower=0.5, tones=None, rim=None, billow=1, cut=None, rim_width=1)`: one towering hard-edged cumulus
  standing on the flat line `base`: lumps along a tower-and-shoulders profile (`tower` 0..1), lit
  as one form from `sun` (screen direction to the light) in four flat tones, lumps casting
  scalloped shadows on one another, a one-pixel lit rim on the sun side of the silhouette and of
  every lump in front of another (`rim_width=2` for the bright night rims of p1a_street), a darker
  flat base. Moods (`CUMULUS`, `cumulus_tones(mood)`; blends allowed): `day blue sunset golden
  night overcast`. `drift` units/s moves it in whole pixels; lumps billow slowly (a few pixels a
  second change). 4 ms for a 900x640 cloud.
  `cumulus_bank(canvas, rect, t=0, mood="day", seed=0, n=5, sun=..., drift=6, alpha=1, tower=0.5,
  layers=2, tones=None, rim=None, rim_width=1)`: a row standing on rect's bottom edge, far layer
  smaller and slower, one depth buffer (near clouds overlap far ones with a rim). 9 ms full width.
- `shadow(canvas, x, y, w, alpha=0.55, color=INK, squash=1, stipple=True)`: flat contact ellipse at
  least a pixel tall, with a half-strength stippled ring a quarter wider. <0.1 ms.
- `shaft(ctx, x0, y0, x1, y1, w0, w1, color=AMBER, alpha=0.35, dust=1, t=None, seed=0, glow=0.6,
  core=0.35, canvas=None)`: a flat translucent wedge (screen), hard sides, a brighter core band
  `core` of its width, stippled where it begins; dust as single drifting pixels; energy on glow. 2 ms.
- `wind(canvas, rect, t, strength=1, angle=-8, seed=0, color=FOG_LIGHT, n=80, speed=1500,
  alpha=0.55)`: one-pixel streaks 4 to 30 px long along `angle`; pulse `strength` on beats. 0.6 ms.
- `fog_band(canvas, rect, t, density=1, color=FOG, speed=20, seed=0, alpha=0.6, size=1)`: mist as
  flat translucent strata: a gently lumpy top with a two-pixel stippled edge, a dense core, a foot
  stepping down in two thinner strata; scrolls at `speed` units/s in whole pixels. 2 ms full width.
  `fog_bank(canvas, rect, t, density, colors=(FOG_DEEP, FOG, FOG_PALE), speeds=(8, 16, 30), seed,
  alpha, layers=3)`: far-to-near parallax strata. 6 ms for three.
- `mottle(canvas, rect, alpha=0.3, scale=1, seed=0, density=0.012)`: now a sparse pixel texture:
  single pixels a little lighter or darker, fixed to the surface. 0.6 ms full frame.
- `rain(ctx, rect, amount=0.6, slant=-0.18, seed=0, color=RAIN, alpha=0.8, lit_side=None,
  lit_color=AMBER, lit_reach=0.45, t=None, splash=0.6, ground=None, canvas=None)`: one-pixel streaks
  at three depths (2, 4, 7 px; far ones fainter and landing higher), about 700 * amount in the air;
  each drop lands in `ground` = (y0, y1) (default the lower 45 % of rect) with a tiny splash for one
  step; `lit_side="left"|"right"` lights them warm in three steps toward that side, energy on
  glow (br_b). 1 ms.
- `mirror(ctx, draw_fn, y0, depth=None, alpha=0.7, tint=None, ripple=1, squash=0.7, dark=0.25,
  x0=None, x1=None, t=None, streak=0.25, seed=0)`: the wet ground. `draw_fn()` paints on
  `ctx.canvas` what is reflected (sky, cloud, far shapes, windows); while it runs `ctx.canvas` is a
  scratch surface with the same matrix and `ctx.glow` swallows everything (nothing doubles). Laid
  below `y0` (to `y0 + depth`, between x0 and x1): flipped, squashed, darkened toward `tint`
  (INK), broken into one-pixel rows shifted sideways by whole pixels in a slow ripple (`ripple` px
  near the horizon, growing toward the viewer; it moves four times a second) and dimmed in a
  sparse pattern of streaks. Works inside `graded` and in a dissolve. Cost: the reflected drawing
  again + about 2 ms.
- `reflect(canvas, y, draw_fn, alpha=0.35, squash=1, tint=None, dark=0.3, gaps=True, x0, x1, depth)`:
  a figure's own reflection: `draw_fn()` (on `canvas`) flipped about `y`, darkened, every third
  pixel row cut out. Pass x0, x1, depth (the figure's box): 0.1 ms; unbounded about 4 ms.

### `hx.kit.cloud` (the gloom)

A field of puffs (squashed spheres) rasterised on the real pixel grid with a depth buffer
(private `_atm_puffs.py`, shared with `look.cumulus`): flat tones from lighting, cast shadows
and one-pixel rims; whole-pixel centres and radii that drift slowly, so the mass changes a few
pixels per step (measured 0.3 % of the frame per step for a lid, 0.7 % for a storm lid) and
never boils.

- `draw(ctx, rect, t=None, density=1, heavy=0.5, tone=None, holes=(), tear=0, seed=0, lit=None,
  churn=1, taper=None, seam=None, canvas=None, rim=0.18, crown=None, light=None)`. `rect` = (l, t, r,
  b), the underside at 80 % of its height. Seen from below (room mass: a wide rect inside the
  frame, ends taper; sky lid: a rect wider than the frame, top off-screen): rows of billows
  overlapping like tiles, each row's lower edge one tone lighter, the body dark and heavier toward
  the underside, a pale one-pixel rim along the underside's edge (`rim` 0..1), stipple only where
  tones meet (ref `intro`, `v1a`). `crown=True` (default: when the rect's top lies well inside the
  frame) draws a cloud in the open instead: lumpy crown lit from above-left, flat dark base (ref
  `p1a_street`, `p1a_class`); pass it for the private cloud that follows the child outdoors.
  `light` overrides the screen direction of the light. `tone` = (crown, top, belly, underside):
  `GLOOM` (default), `STORM` (darker; `churn=2.5, heavy=1`), `PALE`.
  `holes` = [(x, y, r, amount)]: ragged elliptical openings (tilted by seed and index; near ones
  merge) that grow pixel by pixel from a small gap (amount 0) to about r (1); the cloud's own
  billows bulge into them (only billows rooted in the mass: none float), what is cut shows what was
  drawn before (draw the lit sky first), and the edge round them catches a bright rim in `lit`'s
  colour, two pixels toward `LIGHT_DIR`, the billows next to it one tone lighter.
  `tear` 0..1: from its first frame a clean gap at least three pixels wide along `seam` (polyline,
  low-passed; default through the holes, else across the middle) that runs out from the middle and
  widens; billows bulge from both lips (never across), lit one tone up with a bright rim; slivers
  and small islands are removed; at 1 only remnants at the ends remain. Put `cumulus` behind it for
  the towering lit edges of `c3a_tear`. `density` < 1 pales it and makes it translucent (one
  alpha). `churn` scales the billows' drift (periods 9 to 18 s).
  Cost: whole-sky lid 5.4 ms, with three holes 10 ms, half torn 11.7 ms; room mass 6.6 ms; crown
  1.7 ms.
- `small(ctx, x, y, w, t=None, tone=None, seed=3, canvas=None) -> (bx, by)`: the small pale cloud
  (width w): a little cumulus in `PALE` tones lit from above-left with a rim, bobbing in whole
  pixels and tilting slightly (`bob(x, y, w, t, seed) -> (x, y, tilt)`); returns its belly.
  `string(canvas, x0, y0, x1, y1, t, color=None, width=1.6, sag=0.08, alpha=0.85, seed=0)`: one pixel
  wide whatever `width`, with sag and sway. Both 1 ms.

### `hx.kit.lights`

- `wander(seed, t, amp=1) -> (dx, dy)`: irregular gentle flight offset (scalar or array seeds).
  `flicker(seed, t)` 0.6..1.
All on the real pixel grid (single pixels drawn as one batch per colour and alpha step).

- `motes(ctx, xs, ys, size=1, alphas=1, color=AMBER, core=CORE, glow=1, canvas=None)`: firefly-motes:
  a one-pixel cream core (2x2 above size 1.6), a plus-shaped sparkle whose arms show only while the
  mote is bright (so it twinkles with its flicker; two-pixel arms when big), a checkerboard-
  stippled halo ring of 2 to 4 px, energy on glow. `mote(ctx, x, y, size, alpha, seed, t, color,
  glow)` adds its own flicker. 0.3 ms for 20.
- `ribbon(ctx, path, n, head, t=None, seed=0, size=1, alpha=1, trail=0.6, spread=14, color=AMBER)`:
  n motes along polyline `path` behind a head at `head` (0..1 of its length, may run past 1). <1 ms.
- `moth(ctx, cx, cy, t=None, r=46, size=1, seed=0, color=MOTH, alpha=0.9)`: a few pixels (body two,
  wings switching between three states each step) circling a lamp mechanically
  (`moth_pos(cx, cy, t, r, seed) -> (x, y, heading)`); `size` 2 doubles its pixels.
  `chirp_rings(ctx, x, y, t, times, life=1.1, radius=70, color=MOTH, alpha=0.35)`: one-pixel rings
  growing a pixel at a time from each start time in `times`, fading in three steps.
- `pollen(ctx, rect, t=None, n=60, seed=0, color=None, alpha=0.6, drift=(6, -3), glow=0)`: single
  pixels drifting and wrapping inside rect, twinkling in two steps. `glints(ctx, xs, ys, t=None,
  size=1, alpha=1, seed=0, color=None, rate=0.6)`: a bright pixel flashing at hashed phases, a plus
  of one-pixel arms at its peak.
- `windows(ctx, rect, t=None, seed=0, size=(1, 1), gap=(2, 3), lit=0.35, warm=0.7, warm_color=None,
  cold_color=None, dark=None, people=0, flicker=0, alpha=1, glow=0.4, canvas=None) -> (xs, ys, on)`:
  rows of windows `size` real pixels on a facade rect, `gap` pixels apart. A share `lit` is lit, in
  a fixed hashed order (raise it to light them one by one on beats, v2a); `warm` of those are
  `WINDOW_WARM`, the rest `WINDOW_COLD`; `dark` paints the unlit panes; `people` puts one-pixel
  family silhouettes in lit windows of at least 3x3 px; `flicker` makes that share of cold ones
  change like a TV. Warm energy on glow. Returns the window centres (for a reflection). 0.6 ms for
  a 400x300 facade.

### `hx.kit.scraps`

The family picture: a child's crayon drawing on cream paper (a blue sky strip, a sun with rays,
three figures holding hands: an adult in blue, the small one in amber in the middle, an adult in
a rose dress; a house; grass and flowers). Pixel art: the drawing is a few bold shapes in
picture units (100 x 72) painted straight at the real-pixel size it is shown at (AA off, strokes
never under a pixel; rays, faces, outlines, crayon hatching and flowers come in only as it gets
bigger, so 26 px wide still shows three coloured figures, a sun and the house). The main tear
(`TEAR`) runs down through the small middle figure; a fixed label map cuts `N_PIECES = 12` pieces
(six each side of it). Each piece, half or sheet gets a pale torn rim (from 40 px wide) and a
dark one-pixel outline (`OUT`); sprites are cached per (piece, width px, 6-degree rotation step,
eighth of a flip). `scale` keeps its meaning: the picture is 720 * scale logical wide.

- `piece(i)`: `.home` (centroid offset from the picture centre, logical at scale 1), `.size`
  (radius, logical at scale 1), `.poly` (8-point unit outline), `.color` (its main crayon colour).
  `KEPT` = the piece holding the small middle figure (the one kept in the pocket, folded into the
  sill bird in the coda).
- `draw_piece(canvas, i, x, y, scale=1, rot=0, alpha=1, flip=1, shadow=0.3, lift=8)`: centroid at
  (x, y), `rot` degrees; `flip` -1..1 tumbles it in eighths (below 0 its blank back shows);
  `shadow` = alpha of a flat ink copy offset by `lift`. `draw_kept(canvas, x, y, scale=0.3, rot=0,
  alpha=1, flip=1, shadow=0, lift=8)`.
- `drifting(canvas, t, rect, n=12, seed=0, scale=0.35, alpha=1, speed=30, tumble=1)`: 9 pieces
  about 1 to 3 ms (new tumble steps get baked as they come).
- `assembled(canvas, cx, cy, scale=0.5, fit=0.8, t=0, seed=0, alpha=1, rot=0)`: laid out as the
  picture; at `fit` 1 every piece still stands about two pixels off its place (outline and a line
  of ground between), two pieces stay farther out, now and then one shifts by a pixel. 1.7 ms.
- `armful(canvas, x, y, scale=0.22, t=0, seed=0, n=12, spread=1, alpha=1)`: bunched, breathing by
  a pixel. 1.3 ms.
- `whole(canvas, x, y, w, alpha=1, rot=0)`: the untorn picture, centred, w logical wide.
- `on_wall(canvas, x, y, w, state="torn", t=0, alpha=1, seed=0)`: the picture on the room wall,
  centred on (x, y), w logical wide (130 = 26 px). `"whole"`; `"torn"`: the two halves hang apart
  (gap 2 px or more), each on a pin, the right one a pixel lower (tilted when 60 px or wider);
  `"taped"`: back together with a one-pixel gap still showing, three tape strips across the tear
  and two at the top corners. 0.9 ms.
- `shard(canvas, i, x, y, h, manner="loom", tones=None, alpha=1, dissolve=0.22, flip=1, lean=0,
  light=None)`: piece i standing upright on (x, y), about h tall. `"loom"`: flat mist
  silhouette (three tones, darker at the top, stippled into the mist at the base), the crayon
  lines only as a lifted tone (no faces); `"thing"`: the piece itself. `loom_tones(depth=0.6)`
  gives the default mist tones (top, middle, base) for 0 = far and pale .. 1 = near.
- `unfold(canvas, i, x, y, w, size=60, phase=0, heading=0, alpha=1)`: piece i folds into a paper
  bird in five steps of `w` (the piece; three folds where the torn outline becomes the bird and
  the drawing fades to paper; the bird), then flaps in four stepped poses from `phase` radians.
  The bird wears the piece's crayon colour on its near wing. `size` = half-length, heading
  degrees (15-degree steps).
- `paper_bird(canvas, x, y, size=40, phase=0, heading=0, color=None, alpha=1, tex=None)`: plain
  paper bird, or `tex=i` for a piece's colour. `bird_poly(phase)` gives its 8-point outline.
- `paper_bird_sitting(canvas, x, y, size=24, color=None, tex=None, facing=1, alpha=1)`: a folded
  paper crane sitting on a sill, base at (x, y); coda: `tex=KEPT`.
- `paper_plane(canvas, x, y, size=30, heading=0, t=0, color=None, alpha=1, seed=0)`: a folded paper
  plane, centred, heading degrees in 10-degree steps; it rocks a step now and then.

### `hx.kit.memory`: what weighs on the child

The home objects and the school objects as pixel things (`memory.py`, helpers in `_thg_px.py`).
Every object takes its base point (x, y) (the middle of its foot line unless noted), a size (`h`
height, or `w` width where named), and `manner`, `t`, `seed`, `facing`, `alpha`, plus
`colors` (override `{"base", "shade", "light", "dark", "id", "accent", "face", "bag", "line"}`),
`tones` and `depth` (loom), `tip` (cutout), `dissolve` (loom base fade share). Three manners:

- `"thing"`: an object in a place in that place's colours (furniture with a dark one-pixel outline,
  people flat grey-blue without one). Draw it inside `look.graded` like the rest of the set.
- `"loom"`: a towering flat silhouette in three mist tones (`tones` top..base, default
  `loom_tones(depth)`; 0 = far and pale, 1 = near and dark), darker toward the top, stippled away
  into the mist over the last `dissolve` of its height (the hand: at the top, into the cloud);
  any size, taller than the frame if asked. Only the identifying detail stays, as a lifted tone
  (the door's knob and frame line, the board's chalk, the folded fingers); thread is a notch
  darker. A lit door's light stays warm.
- `"cutout"`: a knee-high paper prop: the object printed flat and muted on pale paper inside a
  paper margin, an ink contour (from 16 px tall), a darker back edge, a little strut behind;
  `tip` 0..1 lays it over flat away from us (eased fall, one small bounce near 0.8, a one-pixel
  strip at 1).

Objects (sizes are logical units; everything stepped is cached per step):

- `table(canvas, x, y, h, manner="thing", t=0, seed=0, chairs=3, split=0, bowl=0, ...)`: the small
  dining table with two side-on chairs at the ends and the small chair front-on in the middle
  behind it; h = chair-back height (table 1.25 h wide). `chairs` 3..0 drops right, left, small.
  `split` 0..1 (eight steps): the halves part with their chairs, their broken ends sag, the small
  chair stays alone at the gap. `bowl=1`: one bowl at the left place.
- `door(canvas, x, y, h, manner="thing", t=0, seed=0, open=0, lit=0, glow=None, spill=1, ...)`: a
  front door in its frame standing alone (0.6 h wide, a step at the foot). `open` 0..1 (six steps)
  swings the leaf in; `lit` fills the doorway warm (closed: a strip under the door) and lays three
  stepped bands of light on the ground; with `glow` the energy goes there too.
- `feet_light(canvas, x, y, w, t=0, seed=0, apart=0, gone=0, color=AMBER, glow=None, alpha=1,
  floor=None)`: the strip of light under a closed door, centred on the floor line: 1 px (2 px from
  300 wide) with a stepped spill, broken by two pairs of feet with short shadows. `apart` moves the
  pairs to the ends; `gone` walks the right pair out and dims the strip by half.
- `adult(canvas, x, y, h, manner, t, seed, pose="turned", phase=0, facing=1, ...)`: faceless
  silhouette; `pose` "stand" (from behind), "turned" (side-on, turned away), "walk_away" (side-on,
  four stepped poses from `phase`, 0..1 = two steps), "front" (a plain pale oval, no features).
  Coat or skirt, bob or short hair, build from seed. No gesture, no expression.
- `pupil(canvas, x, y, h, manner, t, seed, view="back", phase=None, bag=True, facing=1, ...)`: a
  schoolchild (big head); `view` "back" | "front" | "side" (walks with a `phase`); backpack.
  `passerby(canvas, x, y, h, manner, t, seed, phase=None, facing=1, kid=None, ...)`: a street
  passer-by (an adult, or a third of the time a child with a bag at 0.62 h).
  `family_trio(canvas, x, y, h, manner, t, seed, phase=0, facing=1, ...)`: a small one walking
  between two adults, holding both their hands (x = the child; adults at +-0.4 h).
- `desk(canvas, x, y, h, manner, t, seed, chair=True, ...)`: a school desk from the front, the chair
  back above it (h = chair-back height). `desk_row(canvas, x, y, h, n=8, ...)`: desks end to end,
  side-on, as a narrow knee-high path (h = top height, 1.15 h a desk).
  `lunch_table(canvas, x, y, h, n=12, ...)`: one long table seen from behind, n seated backs
  shoulder to shoulder with no gap (alternate tones), h = head height.
- `ring_of_backs(canvas, x, y, r, n=9, manner, t, seed, h=200, turned=1.0, squash=0.34,
  who="pupil", rot=0, near=0.15, ...)`: figures standing in a ring round (x, y), radius r, near
  side `near` larger; `turned` (one value or a list): 0 facing the centre, 1 back to the centre,
  turning through side-on; the far side then shows backs, the near side plain fronts.
- `whisper(canvas, x, y, h, manner, t, seed, flow=0, facing=1, ...)`: two heads and shoulders,
  one tipped in to the other's ear (1.3 h wide); a dark thread passes over from mouth to ear with a
  scribble knot at its head, `flow` 0..1 in twelve steps.
- `scribble(canvas, x, y, size, seed=0, grow=1, manner="thing", t=0, color=None, alpha=1, ...)`:
  the tangle of dark thread, centred, `size` across: a ball of loose loops (fewer when small),
  one-pixel thread (two from 60 px), `grow` 0..1 in sixteen steps.
- `balloon(canvas, x, y, w, seed=0, closed=0, grow=1, manner="thing", t=0, fill=None, hang=0,
  tail=1, ...)`: a speech balloon whose outline never closes (a gap at the upper right, 16 to 96
  degrees), its tail tip at (x, y), scribble inside (`grow`), never characters; `fill` (default on
  for loom and cutout: the hanging signs); `hang` = a one-pixel thread that long up from its top;
  `tail=-1` puts the tail on the other side.
- `board(canvas, x, y, w, manner="thing", t=0, seed=0, n=5, scratched=None, scratch=0,
  ladder=False, stand=None, ...)`: a blackboard w wide (0.44 w tall) with a row (or three-row
  ladder) of n chalk scribbles; scribble `scratched` is scratched out with rough strokes over
  `scratch` (six steps). `stand` (default outside "thing") puts it on an easel; base = feet.
- `pointing_hand(canvas, x, y, h, manner="loom", t=0, seed=0, facing=1, ...)`: a big plain hand
  coming down out of the cloud, the fingertip at (x, y), the sleeve h above; fades up into the
  cloud.
- `shards(canvas, x, y, h, manner="loom", t=0, seed=0, n=3, spread=0.9, alpha=1, tones=None,
  depth=0.6, dissolve=0.22)`: the standing shards of the torn picture (the middle one is `KEPT`).

Costs (cached; the first call of a new size or step bakes it, 0.5 to 5 ms, a big shard 40 ms
once): a person 0.2 to 0.4 ms, the table, door, desk row, balloon 0.3 to 0.5 ms, lunch table
0.5 ms, a ring of 9 pupils 0.8 ms, the board 1 ms, a 900-tall loom door 2 ms, a whisper 600 tall
in loom 1.8 ms, a ring of 7 giant loom backs 6 ms (cost is the blit area).
