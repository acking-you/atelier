# hx.chalk.sets: the indoor sets

The room (night, evening, sunset), the classroom from the back, the home table, the corridor, and the
declared changes between them. Build a set here and nowhere else: then it is the same place in every
scene (same anchors, same seeds, same hand). `from hx.chalk.sets import *` (or from `hx.chalk` once
the package imports it). World units, y down, everything through `F.cam`. Proofs:
`hx/_review/v4_kit/sets/` (`proofs.py` makes them; `review/review.py` places every set as the film does).

## 1. A Place, where it stands, and the order to draw it in

Every builder (`room`, `classroom`, `home_table`, `corridor`, and every change) returns a **Place**:
a dict of named groups, each a `Sketch`, in paint order, plus the dressing that is not strokes.
Build it afresh every frame (1 to 1.6 ms).

```python
R = room("night")
R.back(F)                 # seated dressing: wall hatch and tone, floor, contact shade. Never the ground line.
...light...               # the weather artist's pools and halos (section 3 says where and how big)
R.view(F)                 # what the window shows: after the light (it is opaque), before the strokes
ground_line(F)            # always the scene's
R.draw(F, "wall", "window", "lamp", "shelf", "table", "rug")     # groups by name, or R.draw(F) for all
R["sofa"].draw(F)
figure(F, story.CURL_X, story.SOFA_SEAT_Y, 380, ASLEEP, "child", seed=3)     # the child lies ON the sofa
R["cushion"].draw(F)      # the cushion is its own group so that it can go over or under the child
```

**Where a set stands.** The film is one continuous world (`hx/story.py`): the room is drawn three
times at three places. Every builder and every change takes `dx`, the world x added to all of its
coordinates: strokes, dressing and view move together, and so must everything you put into it.

| set | when | dx |
|---|---|---|
| night room, room into classroom, classroom | 0 to 48 s | 0 |
| home table | 48.27 to 56 | yours: the child stands at `home_anchors(apart, dx)["child"]`, so `dx = child_x - 1010` |
| evening room, plain into room, room into corridor, corridor | 85.75 to 115.77 | `story.ROOM2_DX` (3060) |
| sunset room | 244.5 to the end | `story.ROOM3_DX` (7700) |

```python
R = room("eve", dx=story.ROOM2_DX)
window_glow(F, *R.rect(WINDOW), 1.0, "evening")          # an (l, t, r, b) anchor of this file, where R stands
figure(F, story.CURL_X + R.dx, story.SOFA_SEAT_Y, 380, pose, "child", seed=3)
```

Every anchor in section 2 is given at dx = 0. `R.rect(PANE)` shifts an (l, t, r, b), `R.pt(FAR_WINDOW)`
anything whose first number is a world x; `wire_pts(dx=R.dx)` and `home_anchors(apart, dx)` take it
themselves. Wall, floor and their tone reach from x -3000 to 5000 round the set and the long wall
lines from -1400 to 3300, so no framing of the film shows where a room ends.

| | |
|---|---|
| `R[name]` | a group (Sketch): give it times, `on_beats`, `set_off`, `sub(...)` as any Sketch |
| `R.all(*names)` | the groups (default all) as one Sketch in paint order, same objects |
| `R.draw(F, *names, **kw)` | paint groups (default all); `kw` goes to `Sketch.draw` (`a`, `thin`, `tint`...). An unknown name is a KeyError (a Change skips a group that has nothing to show) |
| `R.back(F, a=1)` | the dressing; `a` = pressure 0..1 (fade it over at least 6 frames) |
| `R.view(F, a=1, lit=None, wire=None)` | the view through the window: `lit` 0..1 the amber window, `wire` your own WORLD polyline for the wire |
| `R.dx`, `R.rect(r)`, `R.pt(p)`, `R.at(dx)` | where it stands; an anchor shifted there; move the whole Place (returns it) |
| `R.mood` | the `Mood` (colours): `.near .mid .far` line colours, `.day` True only for `"sunset"` |
| `R.cues` | `{name: (t0, t1)}` set by `room_on` / `room_on_coda`: `back` and `view` then follow the schedule by themselves |

Moods: `"night"`, `"eve"` (flat grey evening; `"evening"` is accepted too), `"day"` (the classroom's grey day: still cold chalk on
the night skin), `"sunset"` (the coda: `C.PENCIL` line and golden-hour pastel; draw it on the day
skin). `MOODS` is the dict of them by name; a builder's `mood=` takes a name or a `Mood`.
Before 217.84 a set uses only the cold chalks; the only amber is the friend's window.

Part names are `group.part` (`"sofa.back"`, `"sofa.back.fill"`, `"table.chair_l.seat"`,
`"window.curtain.l"`). A prefix names everything under it.

## 2. Anchors (world, at dx = 0)

From `hx/story.py` (the builders draw to them): `FLOOR 742`, `SOFA_X 230`, `SOFA_W 760`,
`SOFA_SEAT_Y 622`, `SOFA_ARM_Y 558`, `SOFA_ARM_R (886, 990)`, `SOFA_BACK_Y 454`, `CURL_X 815`,
`RUG (640, 804, 500, 50)`, `PHONE (690, 800)`, `WINDOW (1300, 170, 1670, 560)`,
`WALL_DRAWING (1150, 318)` (the family drawing is NOT drawn here: put it there, after `window`; at
s = 1 it is 150 wide and its right edge stays about 20 units clear of the left curtain), `TABLE_X 1790`,
`LAMP_X 132`.

Defined here:

| name | value | what |
|---|---|---|
| `PANE` | (1307, 177, 1663, 553) | the glass: rain and drops on the pane go in this rectangle |
| `FAR_WINDOW` | (1571, 448, 56, 70) | the friend's lit window across the street: centre x, centre y, width, height. The small waving figure of 255.0 goes inside it (clip to the rectangle); it is 73 x 91 px at zoom 1.3 |
| `WIRE_ENDS`, `WIRE_SAG` | ((1286, 260), (1684, 278)), 20 | the wire under the eaves; use `wire_pts` / `wire_y` |
| `LAMP_SHADE` | (132, 283) | middle of the standing lamp's shade |
| `WALL_X`, `WALL_LINE_X`, `TOP_Y` | (-3000, 5000), (-1400, 3300), -420 | how far the room's and the classroom's wall and floor dressing reach, how far their long lines (skirting, cornice, dado), and how far up |
| `SKIRT_Y`, `CORNICE_Y` | 715, 52 | the two wall lines of the room |
| `CLASS_BOARD` | (620, 176, 1230, 446) | the board, l t r b |
| `CLASS_DOOR` | (40, 236, 196, 742) | the classroom door |
| `CLASS_DESK`, `CLASS_DESK_S`, `CLASS_DESK_TOP_Y` | (400, 742), 1.35, 613.75 | the desk that stands apart: middle of its near edge on the floor, its scale, world y of its top (pushing hands rest there; its near end is at x = 400 + 76 + desk_dx) |
| `CLASS_CHAIR` | (268, 742) | its chair |
| `CLASS_DESK_R`, `CLASS_CHAIR_R` | (1900, 742), (2032, 742) | the same pair with `side=+1`: apart on the right of the rows, past the window, the chair turned to face them (the desk's near end, toward the rows, is at x = 1900 - 76 + desk_dx) |
| `CLASS_CLOCK` | (432, 268, 46) | centre and radius |
| `CLASS_DADO_Y` | 542 | below it the wall is darker |
| `CLASS_ROWS` | `{"far": (xs, 738, 0.80), "near": (xs, 838, 1.08)}` | where the rows of pupils sit: x of each seat, floor y, scale. far xs 800 985 1170 1355 1540; near xs 760 990 1220 1450 1680. World x 740 to 1700 below the dado is left free for them |
| `CLASS_LAMPS` | ((330, 118, 1.0), (925, 104, 0.9), (1500, 112, 0.95)) | hanging lamps: x, y of the shade's rim, scale |
| `HOME_X`, `HOME_TABLE`, `HOME_LAMP`, `HOME_CHAIR_S`, `HOME_SLIDE` | 1010, (710, 580, 1310, 600), (1016, 318), 1.5, (170, 316) | table middle; its top slab l t r b; rim of the hanging lamp; chair scale (seat 96, back 255 to 275 above the floor); how far the left and the right end chair slide at apart = 1 |
| `COR_BASE_Y`, `COR_EDGE_Y` | 698, 808 | the corridor's lit floor band: where the wall meets the floor, and the band's near side (the floor goes on in front of it). The ground line (742) runs along its middle |
| `COR_X`, `COR_LINE_X`, `COR_CORNER_X` | (-3000, 5000), (-1400, 3300), 1450 | how far the corridor's dressing and its two long floor lines reach; the end of the long wall |
| `COR_WINDOW` | (1520, 150, 1760, 596) | the window at the end, l t r b |
| `COR_LOCKERS`, `COR_HOOKS`, `COR_LAMPS` | (640, 300, 1180, 6), (190, 392, 570), ((380, 96, .9), (1010, 88, .85), (1640, 80, .8)) | lockers l t r count; coat rail l y r; hanging lamps |

`home_anchors(apart=0, dx=0) -> dict`: `child` (1010, 742: floor point behind the table at the middle
chair), `adult_l`, `adult_r` (floor points of the two end chairs: (674, 742) and (1346, 742) at apart 0,
(504, 742) and (1662, 742) at apart 1: the right chair ends in front of the curtain, clear of the amber
window), `seat_y` 646, `top_y` 580, `drawing` (1010, 578: where the family drawing lies), `cup_l`
(820, 580), `cup_r` (1214, 580), `lamp` (1016, 318). All x shifted by `dx`.

## 3. The room

`room(mood="night", apart=1.0, throw=True, dx=0.0) -> Place`. `apart` 0..1: how far two of the table's
chairs are pulled away from the third (1 in the film). Groups in paint order:

| group | parts |
|---|---|
| `wall` | skirt cornice |
| `window` | frame inner mullion transom sill ledge rail curtain.l (+.fill) curtain.l0-1 curtain.r (+.fill) curtain.r0-1 |
| `lamp` | foot (+.fill) pole ring shade (+.fill) cord |
| `shelf` | plank bracket_l bracket_r book0-2 (+.fill) pot (+.fill) leaf0-2 (cropped by the right edge) |
| `table` | chair_m.* chair_l.* chair_r.* leg_l leg_r cloth (+.fill) top (+.fill) fruit0-2 (+.fill) bowl (+.fill); a chair is back_f leg_ff seat (+.fill) apron leg_f bar back rail (+.fill) slat |
| `rug` | outer (+.fill) inner (+.fill) fringe_l fringe_r |
| `sofa` | back (+.fill) throw (+.fill) fringe seat (+.fill) split arm_l (+.fill) roll_l arm_r (+.fill) roll_r leg_l leg_r |
| `cushion` | shape (+.fill) button |

The table is the home table as it stands in the room: the same cloth with its scalloped hem, a bowl
of fruit, chairs a child could sit on (seat 83, back 221 to 238 above the floor). `chair_m` stays
tucked under the table's left end (x 1665); `chair_l` is pulled off to the left and stands alone
under the window's left pane (x 1439 at apart 1: the amber window shows between the two); `chair_r`
is pulled off to the right (x 2128: beyond the frame in the wide shot, there when the camera looks
right). Their backs reach y 504, into the lower panes; the nearest (chair_m's) stays 15 units right
of and 21 below the amber window. The left curtain's outer edge is
at x 1254 (its hem 1240) and its rail starts at x 1238: with the title at `cx=960` its last 34 px would
meet the rail (from 7.8 s), so use `title.draw(F, cx=900)` as the demo does (26 px clear).

Dressing (what `R.back(F)` calls; use them directly only for something special; they draw at dx = 0,
so wrap them in `with F.place(dx, 0):` for a room that stands elsewhere):

- `room_wall(F, mood="night", a=1, x0=-3000, x1=5000, y0=TOP_Y, y1=SKIRT_Y)`: two long loose seated
  zigzags, a darker band above the cornice, the skirting board as a band of tone. 8 ms.
- `room_floor(F, mood="night", a=1, draw=1, x0, x1, bottom=1130, vx=960)`: boards running toward the
  viewer and their butt joints; `draw` 0..1 rules them in one after the other from the middle of the
  room outward, each up to its tip. Not the ground line. 0.8 ms (2.4 at sunset, with its floor tone).
- `room_shade(F, mood="night", a=1, sofa=1, table=1, lamp=1)`: rubbed contact shade under the
  furniture; each argument fades one. 0.9 ms.
- `window_view(F, mood="night", a=1, lit=1, wire=None, rect=WINDOW, eave=1)` (what `R.view(F)`
  calls): sky, a far row of roofs, two houses across the street, in the right one the ONE amber
  window, our own eave at the top with the wire under it. `a` fades the pane in; `lit` 0..1 colours
  the amber window in (zigzag first, then solid); `wire` = your own polyline for the wire (here in
  the room's own coordinates; `R.view` takes world points).
  Not drawn here: rain, drops on the glass, crows, the figure in the far window. 5 to 6 ms.
- `wire_pts(sag=20, dips=(), n=28, dx=0) -> (n, 2)` and `wire_y(x, sag=20, dips=(), dx=0)`: the
  wire's world curve. `dips = [(x, depth, reach=60), ...]` (world x) pulls it down locally: for a crow
  landing at x, animate `depth` (a dip of 6 to 10 and a decaying swing on `F.t`), pass the same dips
  to `wire_y` for the crow's feet and `wire=wire_pts(dips=..., dx=R.dx)` to `R.view`. At rest the wire
  runs from (1286, 260) to (1684, 278) and hangs to y 289 in the middle; a crow of scale 0.5 sitting
  on it clears the transom (y 351) below and the eave (its edge runs from y 222 at the left to y 194
  at the right) above. Eleven crows fit from x 1320 to 1650; the mullion (x 1485) hides whatever sits
  right behind it.

Light is the weather artist's (`hx/chalk/doc/weather.md`); this is what goes with the room and where
(the proofs call exactly this; add `R.dx` to every x, or use `R.rect`):

| mood | before `R.view(F)` | after |
|---|---|---|
| night | `window_glow(F, *WINDOW, a, "night")`, `window_pool(F, 1280, 1680, 756, a, mood="night")` | `rain_window(F, *PANE, k)` after `R.view(F)` and before `R.draw(F)` |
| eve | `window_glow(F, *WINDOW, a, "evening")`; no pool in the flat grey evening. For the second verse's long pale pool: `window_pool(F, 1280, 1680, 756, a, -0.9, 380, mood="evening")` | |
| sunset | `window_glow(F, *WINDOW, a, "sunset")`, `window_pool(F, 1280, 1680, 756, a, mood="sunset")` | `lamp_light(F, 132, 742, 520, a)` right after `R.draw(F, "wall", "window", "lamp")`, then the other groups. The shade itself is already drawn lit in this mood |

The window's light is centred on (1485, 365); the pool starts at the floor line + 14 between x 1280
and 1680. The amber window and its glow are part of `R.view` (no `amber_window` needed).

### Drawing on with the music

- `room_on(R, tl, bar=0) -> end time (9.19)`: the intro. Sets every item's `on` and the cues that
  `R.back` / `R.view` read. Bar 1: skirting 1.23, cornice 1.58, the wall's hatch coming up 0.4 to 2.5,
  the floorboards ruled in 1.0 to 3.1. Bar 2: the sofa, the first thing in the room (back 3.27, arms
  4.02 and 4.39, seat 4.77, blanket 5.52, cushion 5.89, each hatch following its outline); the rug
  quietly from 5.7. Bar 3: the window on the beats (frame 6.27, mullion 6.64, transom 7.02, sill
  7.39, rail 7.77, curtains 7.95 and 8.33), the pane filling 7.0 to 8.2, the amber window coloured in
  8.5 to 9.0; quietly between the beats the lamp (from 6.8), the table, its cloth and chairs (from
  7.8), the shelf (from 8.2). Everything is complete at 9.19, before the child is drawn (9.27). The
  ground line (0.27) and the child are the scene's. The schedule itself is the table `ROOM_ON`
  (prefix, beat, every, dur).
- `room_on_coda(R, tl, t0=244.765) -> end time (248.39)`: the coda, on the piano's attacks: sofa
  244.77, window 244.97, sill and wall lines 245.57, rail, curtains and lamp from 245.86, rug 246.3,
  table 246.8, the pulled-away chair and the blanket 247.49. The amber window is lit from the start.
  Table: `ROOM_CODA`.

```python
def draw(F):                                   # the intro
    R = room("night")
    room_on(R, F.tl)
    R.back(F)
    lit = F.ramp(7.0, 8.4)                     # the light comes with the pane
    window_glow(F, *story.WINDOW, lit, "night")
    window_pool(F, 1280, 1680, 756, lit, mood="night")
    R.view(F)
    rain_window(F, *PANE, 0.6 * lit)
    v = F.cam.view(40)
    ground_line(F, span=(v[0], v[0] + (v[2] - v[0]) * F.seg(0.265, 1.0)))
    R.draw(F)

def draw(F):                                   # the coda: the same room, 7700 further on
    R = room("sunset", dx=story.ROOM3_DX)
    room_on_coda(R, F.tl)
    lit = F.ramp(245.3, 247.0)
    R.back(F)
    window_glow(F, *R.rect(WINDOW), lit, "sunset")
    window_pool(F, 1280 + R.dx, 1680 + R.dx, 756, lit, mood="sunset")
    R.view(F)
    ground_line(F)
    R.draw(F, "wall", "window", "lamp")
    lamp_light(F, 132 + R.dx, 742, 520, F.ramp(246.2, 247.4))
    R.draw(F, "shelf", "table", "rug", "sofa", "cushion")
```

To change one thing of a schedule, set that item's time afterwards: `R["lamp"].set_on(8.0, 8.6)`.
To take the room away again use the Sketch methods on `R.all()` (`off_beats`, `set_off`), or a change.

### The single builders

All return a Sketch at the coordinates you give; `mood` picks the colours; `seed`, `col`, `name` as in
the old props (these replace the props of the same name: same leading arguments).

- `sofa(x=230, y=742, w=760, seed=100, col=None, fill=None, k=None, mood="night", throw=True)`: x = left end, y = floor.
- `cushion(x=415, y=592, s=1, rot=-0.42, seed=120, ...)`: centre.
- `window(l, t, r, b, seed=200, col=None, curtains=True, mood="night")`: default `story.WINDOW`. The
  classroom and the home table use this same window (same seeds): its frame never jumps.
- `rug(x=640, y=804, rx=500, ry=50, seed=460, col=None, mood)`, `lamp(x=132, y=742, h=520, seed=440, ...)`,
  `shelf(x=1836, y=372, seed=480, ...)`.
- `chair(x, y, s=1, face=1, seed=400, col=None, a=0.9, mood, fill=True)`: x = middle of the seat's near
  edge on the floor; seat 64 s and back 170 s (its far end 183 s) above the floor; face +1 = the sitter looks right. Seen
  from the side and a little from the front: far legs, far post, the board of its back coloured in.
- `table3(x=1790, y=742, s=1.1, seed=420, col=None, a=0.92, apart=0, mood, name, chair_s=None)`: top
  134 s above the floor; `chair_s` = the chairs' scale (default 1.18 s).
- `desk(x=400, y=742, s=1, seed=900, ...)`: top 95 s above the floor, 112 s wide. `board(l, t, r, b, seed=1320, ...)`,
  `door(l, t, r, b, seed=1600, col=None, mood="day", pane=True, side=1)`.

## 4. The classroom (36.27 to 48.27)

`classroom(desk_dx=0, mood="day", chair_dx=0, desk_s=1.35, dx=0, side=-1) -> Place`. Seen from the back.
`side` says where the desk that stands apart is: -1 left of the rows by the door (x 400), +1 right
of them past the window (x 1900). The child of this film travels to the right (it stands at
`story.X1` = 1040 when the room turns into the classroom and trudges on past the rows), so with
`side=+1` it comes to its desk after the rows and pushes it back toward them, to the left; with
`side=-1` the desk is behind it. `desk_dx` moves the desk (world units, + = right: toward the rows
for side -1, away from them for side +1): animate it on `F.t` for the pushes at 42.7, 44.12, 44.86
and let it slide back. `desk_s` is its scale: its top is 95 * desk_s
above the floor (613.75 at the default; `desk_s=1` gives `story.DESK_TOP_Y` exactly, but that desk
is knee-high beside a 380 child). Groups: `wall` (dado_l dado_r), `window` (frame inner mullion
transom sill ledge: the room's window without curtains), `board` (frame (+.fill) wipe0-1 (fills)
text0-2 shape0-1 ledge (+.fill) chalk sponge), `clock` (rim (+.fill) tick0-3 hands), `pins`
(sheet0-3 (+.fill) mark0-3: children's drawings pinned up, the last cropped by the frame), `door`
(leaf (+.fill) frame pane (+.fill) knob), `lamps` (lamp0-2: cord shade (+.fill) bulb), `lone`
(chair.* desk.*: desk is leg_fl leg_fr box (+.fill) top (+.fill) leg_l leg_r bar).

`K.back(F)` = `class_back(F, a=1, mood="day")`: a calmer, more upright wall zigzag, the darker dado
below y 542, a tiled floor (10 ms). `K.view(F)` = `window_view(F, "day")`. The rows of pupils are not
drawn: put them at `CLASS_ROWS` after `K.draw(F)` (far row first), the child after or between them.

Light: `window_glow(F, *WINDOW, a, "evening")`, `window_pool(F, 1280, 1680, 756, 0.7 * a,
mood="evening")`; if wanted a faint cold glow under each of `CLASS_LAMPS`: `glow(F, x, y + 30, 210 * s,
150 * s, col=(0.80, 0.84, 0.92), a=0.10)`.

## 5. The home table (48.27 to 56.0)

`home_table(apart=0, mood="night", win=True, dx=0) -> Place`. `apart` 0..1 slides the two end chairs
away from the table (animate 52.4 to 54.4): the left one 170 units, the right one 316, to where it
stands in front of the curtain. Groups: `window` (the room's window with curtains; `win=False`
leaves it out), `lamp` (cord shade (+.fill) bulb: it hangs from above the frame), `chair_m` (the
child's chair behind the table, seen from the front: post_l post_r rail (+.fill) slat seat),
`chair_l`, `chair_r` (side chairs, scale 1.5), `table` (leg_fl leg_fr leg_l leg_r cloth (+.fill) top
(+.fill)), `cups` (cup_l.* cup_r.*: bowl (+.fill) ear steam).

Paint order with the people (the table's cloth hides legs behind it):

```python
Hm = home_table(apart, dx=dx)
an = home_anchors(apart, dx)
Hm.back(F)
lx, ly = an["lamp"]                                          # the lamp's light: cold, never amber
pale = (0.80, 0.84, 0.92)
shaft(F, lx, 80, ly + 6, lx, 360, an["top_y"] + 8, col=pale, a=0.34, alphas=(1, 0.8, 0.6, 0.45))
light_pool(F, lx, 772, 470, 44, col=pale, a=0.20)
glow(F, lx, ly + 16, 130, 100, col=pale, a=0.24)
window_glow(F, *Hm.rect(WINDOW), 0.5, "night")
Hm.view(F); ground_line(F)
Hm.draw(F, "window", "lamp", "chair_m")
figure(F, *an["child"], 380, pose, "child", seed=3)          # behind the table: visible from the chest up
Hm.draw(F, "chair_l", "chair_r")
# the two outline adults on the end chairs: floor points an["adult_l"], an["adult_r"], seat at an["seat_y"]
Hm.draw(F, "table", "cups")
# the family drawing lying on the table: an["drawing"]
```

`Hm.back(F)` = `home_back(F, a, mood, apart)`: an island of floorboards that thins out, and contact
shade (2 ms): a memory has no walls. The cone onto the table and the pool on the floor make the table
an island of light in the dark sheet; without them the set is flat.

## 6. The corridor (103.5 to 115.8)

`corridor(mood="night", dx=0) -> Place`. Seen from the side: a long wall, a corner at x 1450 and the
paler end wall with its tall window; the floor is tiled, with ONE narrow lit band along the wall
(y 698 to 808) and the ground line along its middle: the line the child keeps to. In front of the
band the same floor goes on toward us in shadow (its joints run on to the bottom of the frame): a
line on a floor, with floor on both sides, never an edge. Groups: `floor` (base edge corner), `far`
(lockers_b.* at x -660 to -120 and door_b at 1850 to 2020, for when the camera travels), `window`
(frame inner mullion transom sill), `door` (x -70 to 120, cropped by the left edge), `hooks` (rail
coat0-2.* bag.* bench.seat (+.fill) bench.leg_l bench.leg_r), `lockers` (frame (+.fill) d1-5
vent0-5 lock0-5), `notice` (frame (+.fill) line0-1 sheet), `lamps` (lamp0-2). Everything on the wall
stands on y 698, behind the line: draw the stream of pupils and the child after `K.draw(F)`. In the
film it stands at `story.ROOM2_DX`: the child (X4 = 3760) is then at corridor x 700, before the lockers.

`K.back(F)` = `corridor_back(F, a, mood)` (10 ms); `K.view(F)` = `corridor_view(F, a)`: the end
window's flat pale pane. Light: `window_glow(F, *K.rect(COR_WINDOW), a, "evening")`, and one long shaft
from under the window along the floor band: `shaft(F, 1640 + K.dx, 110, 616, 900 + K.dx, 620, 788,
col=(0.80, 0.84, 0.92), a=0.16)`.

## 7. The changes

Each change is a function of `w` in 0..1 returning a `Change`, which is used exactly like a Place
(`back`, light, `view`, `ground_line`, `draw`): it cross-fades the two dressings and views by itself.
Its groups: the leaving set's under `"-name"` first, then the arriving set's under their own names
(a group with nothing to show at this w is skipped by `draw`). `w = F.seg(*SPAN_...)`: the default
spans start on a beat and the parts inside are staggered on the beats; at the default span every
part changes in under 1.2 s, and a longer span stretches everything. Every change takes `dx` (both
sets stand there).

| function | default span | what travels (the pair list) | the rest |
|---|---|---|---|
| `room_to_class(w, desk_dx=0, mood="night", apart=1, dx=0, side=-1)` | `SPAN_ROOM_TO_CLASS` (36.265, 38.6) | `ROOM_TO_CLASS`: sofa back, seat, left arm into the desk's top, its box, the chair's seat (with `side=+1`, `ROOM_TO_CLASS_R`: the table's top and cloth and its right-hand chair's seat, which stand there, and the sofa is simply taken off); lamp pole and shade into the door's frame and pane; cushion into the clock; the shelf's three books and pot into the four pinned drawings | the window's frame stays; curtains, rug, table, blanket are taken off first (36.27 to 37.2); board 37.3, dado, desk and chair, door, hanging lamps one by one to 38.6 |
| `class_to_home(w, desk_dx=0, apart=0, dx=0, side=-1)` | `SPAN_CLASS_TO_HOME` (48.265, 50.14) | `CLASS_TO_HOME`: the middle hanging lamp comes down into the lamp over the table (cord, shade, bulb); the board sinks into the table top, its ledge into the cloth | the window's frame stays and gets its curtains back; everything else of the classroom is taken off first, chairs and cups draw on last |
| `home_to_bare(w, apart=1, dx=0, win=True)` | `SPAN_HOME_TO_BARE` (55.0, 56.0) | nothing | every line taken back from its ends: cups, lamp, curtains, window, chairs, table; the sheet is bare, ghosts gone, at w = 1 |
| `plain_to_room(w, house=None, backs=None, mood="eve", apart=1, dx=0)` | `SPAN_PLAIN_TO_ROOM` (85.765, 90.5) | `PLAIN_TO_ROOM`: the five longest strokes of `house` into the window's frame, inner frame, sill, mullion, transom; the two longest strokes of `backs` into the two curtains | then a part per beat: wall lines, sofa (87.3), lamp, rug, table, shelf; wall hatch and view come up meanwhile |
| `room_to_corridor(w, mood="eve", apart=1, dx=0)` | `SPAN_ROOM_TO_CORRIDOR` (101.515, 104.515) | `ROOM_TO_CORRIDOR`: skirting line into the foot of the corridor wall and rug rim into the near side of the floor band (102.8 to 103.8); window into the end window (five strokes, 103.2 to 104.1); sofa back into the lockers' frame, seat into the bench; lamp pole into the door frame; left curtain into the notice board | first the room is taken off down to those bones (101.5 to 103.2: table, shelf, curtains, cushion and the sofa's parts, rug, lamp, cornice); the rest of the corridor draws on last (103.8 to 104.5) |
| `corridor_to_bare(w, dx=0)` | `SPAN_CORRIDOR_TO_BARE` (114.265, 115.765) | nothing | lamps and far things, notice board, lockers, coats and bench, door, window; the two long floor lines last |

`plain_to_room`: `house` and `backs` are the scene's own Sketches of the towering drawings (any
part names), in WORLD coordinates where they stand at 85.77 (`Sketch.place`); best near the room's
window (x 1200 to 1800 + dx). Their other strokes are taken off in the first beat. Without them the
window simply draws on first. The ground line, the scribble and the child are the scene's as always.

`room_to_corridor` follows the storyboard's 101.6 to 103.7 (the room un-draws while the pool's edge
becomes the line and the child stands up) and has the corridor standing by 104.5; the window's view
with the amber window goes at 102.7 to 103.3. For the pool that narrows into the line see
`window_pool(..., narrow=)` in the weather doc.

```python
def draw(F):                                              # 36.27: the room turns into the classroom
    K = room_to_class(F.seg(*SPAN_ROOM_TO_CLASS))
    K.back(F)
    K.view(F)
    ground_line(F)
    K.draw(F)                                             # then the rows fading in, the child, the scribble
```

At the home table, groups interleave with the people as in section 5; during `class_to_home` draw
`K.draw(F, *[g for g in K if g.startswith("-")], "window", "lamp", "chair_m")`, the child,
`K.draw(F, "chair_l", "chair_r")`, the adults, `K.draw(F, "table", "cups")`; during `home_to_bare`
the same names with `"-"` in front.

For a change of your own: `between(A, B, w, pairs=(), plan=(), keep=(), off=(0, .5), move=(.2, .8),
on=(.5, 1), stagger=0.5, lag=0.4, seed=7) -> {group: Sketch}`. A, B: Places (or None = the bare
sheet), each where it stands (they may have different `dx`: pairs travel in world coordinates).
`pairs`: only these travel (a name, or a prefix whose strokes pair in order). `keep`: prefixes
that are the same in both and stay. `plan`: rows `(w0, w1, prefix, ...)` saying when the items under
those prefixes change (`"-prefix"` only the leaving set's, `"+prefix"` only the arriving set's);
the items of a row follow each other over `lag` of it. What no row names: A's items un-draw inside
`off`, pairs travel inside `move`, B's draw on inside `on`, each sweeping left to right. Wrap the
result: `Change("mine", A, B, w, groups, fade_a=(.05, .55), fade_b=(.4, .95), view_a=(0, .3),
view_b=(.5, .9))` (when the dressings and the views cross over, in w). A set drawing on from the bare
sheet (the home table after the street, say): `Hm = home_table(dx=dx); K = Change("on", None, Hm, w,
between(None, Hm, w, on=(0, 1)), fade_b=(0, .6), view_b=(.3, .8))`, or simply times on `Hm.all()`.

## 8. Costs and flicker

One core, 1080p, median of 10 frames after a warm-up, wide camera (zoom 0.95), dressing + view +
every stroke, without light and figures (`proofs.py cost`, `cost.txt`):

| set | ms | of which back / view |
|---|---|---|
| room night / eve / sunset | 53.5 / 53.1 / 54.3 | 11.4 to 12.7 / 5.7 to 6.5 |
| classroom | 39.1 | 9.5 / 5.1 |
| home table | 27.5 | 2.2 / 6.0 |
| corridor | 41.0 | 10.2 / 1.7 |

Groups of the room: wall 2.9, window 9.1, lamp 3.4, shelf 3.7, table 9.1, rug 4.6, sofa 11.7, cushion 2.4.
Worst frame of a change (set only): room_to_class 59, class_to_home 48, home_to_bare 36, plain_to_room 56,
room_to_corridor 62, corridor_to_bare 48 ms (budget 90). The machine was shared while measuring:
the room came out between 53 and 58 ms over five runs, the others moved by up to 4 ms. Building a Place: 0.7 to 1.3 ms (0.4 more with `dx`, 1 more with a
schedule); building a Change: 1 to 7 ms, included above.

Flicker of each finished set with a static camera, boil step in levels / percent of pixels over 8
(`flicker.txt`): room night 0.45 / 1.6, eve 0.43 / 1.5, sunset 0.53 / 2.0, classroom 0.36 / 1.3, home
table 0.34 / 1.2, corridor 0.26 / 0.9; inside a pair 0.000 everywhere, and 0.000 on every step inside the
silence 56.0 to 58.6. Everything large is seated: wall and floor dressing, the view's masses; only
the named strokes and the small hatches boil. Nothing here reads `F.tb` or `F.t` by itself except
the cues of a schedule. The same frame rendered in two processes is bit-identical.

## 9. Limits

- The room uses 53 to 58 of its 60 ms; do not add to it without taking something away.
- `story.DESK_TOP_Y` (95 above the floor) gives a knee-high desk beside the 380 child; the classroom's
  default desk is scale 1.35 (`CLASS_DESK_TOP_Y`). A pushing pose should take its hand height from
  `CLASS_DESK_TOP_Y`, or the scene passes `desk_s=1`.
- The corridor is a flat side view: it recedes by tone (the end wall is paler) and by the corner line,
  not by perspective, so that figures on the ground line keep their size.
- A travelling outline that flattens (sofa back into desk top, board into table top) is a sliver for
  a few frames; the strips show the worst of it.
- A set taken off quickly (`home_to_bare`, `corridor_to_bare`: many closed outlines within a second)
  reads as rubbing out rather than as lines retreating: each outline shrinks toward its middle and
  leaves its ghost. For a slower, visibly stroke-by-stroke leave use `S.all().off_beats(...)`.
- In the wide framing of the room only two of the table's three chairs are in the picture (the third
  stands right of the frame); the three are seen together at the home table.
- Only the room has a day-skin mood; classroom, home table and corridor are cold chalk only.
