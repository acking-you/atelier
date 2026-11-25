# hx.kit: drawn weather and light

What `hx/scenes/film.py` lays over the pictures. Everything is drawn in hard pixels of `PX`
logical units (film.py scales the canvas so that they match the pictures' own pixels) and is a
pure function of its arguments; `t` is the stepped time (`ctx.t`).

- `look.py`: `rain(ctx, rect, amount, slant, seed, color, alpha, lit_side, lit_reach, splash,
  ground, canvas)` (one-pixel streaks at three depths, optional warm light from one side),
  `wind(canvas, rect, t, strength, ...)`, `fog_band` / `fog_bank` (mist strata), `graded(ctx, sat,
  cool)` (a block drawn with only `sat` of its colour and a cold cast), `reveal(ctx, draw_fn, cx,
  cy, radius, soft, sat, cool)` (the ring of colour: graded outside, true colour inside), the
  palette, and helpers the film does not use at present (`sky`, `cumulus`, `shaft`, `mirror`,
  `sun_disc`, `shadow`).
- `lights.py`: `pollen(ctx, rect, n, seed, color, alpha, glow)`, and unused at present: `motes`,
  `ribbon`, `moth`, `chirp_rings`, `glints`, `windows`.
- `_atm_px.py`, `_atm_puffs.py`, `pixel.py`: their pixel buffers and dither.

The figure rig, birds, cloud, family picture and memory objects of the drawn versions are in
`hx/_attic/kit_procedural/` with their README.
