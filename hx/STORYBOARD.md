# hx version 4: storyboard

"The child's own drawing." The film is one sheet of dark paper on which chalk draws a
nine-year-old's world, the way the child would draw it, come alive. Everything is drawn by code
(`hx/chalk/`). The song: 258.87 s, 80 BPM, beat k at 0.265 + 0.75 k s, bar = 3.0 s. Lyric lines are
named by 0-based LRC index and time only; what a line means is given as a loose paraphrase.
**Never write lyric text anywhere.**

## 1. What the film is about, in pictures

A child lives under a black scribble: the only black on the sheet. The scribble is made of what
the child cannot say: every word that does not come out goes up a thin dark strand from the child
into the scribble, and the scribble grows. One friend, drawn in amber crayon (the only warm colour
for most of the film), says from far away "I am still here", later comes through the storm and
sits beside the child, later holds the scribble apart with bare hands. The child lets go of the
strand. Light comes back in steps; colour comes last (at 217.84, as a ring opening from the two
joined hands). At the end the child is on the same sofa, curled the same way, the scribble
reduced to a small tangle on a string tied to the armrest, and the phone that nobody called rings.

No magic cure: relief is gradual and comes partly from someone else; at the end the scribble is
still there, small; two of the three chairs still stand apart; the family drawing is taped, the
tear still showing.

### Care (hard rules)

No self-harm, no heights, edges, water or trains as threat, no methods. "Leaving" is only ever the
child walking away into the mist while its chalk line loses pressure (it is being rubbed out); it
never goes further than that. Family and school are shown as objects and metaphors, never graphic:
no violence, no abuse, no humiliation played for effect; adults and pupils are faceless outlines
turned away, not villains; never one cause that explains everything.

## 2. The rules of the drawing

1. **The protagonist never cuts.** The child is on screen from 9.3 s to the last frame. There are
   no cuts in the film. A change of place is the set un-drawing and the next one drawing on around
   the child, a declared morph (window into window, ground line into ground line), or the camera
   travelling. The only abrupt events are musical: the band's entries at 58.60 and 201.25 and the
   three hits of each chorus.
2. **One ground line** (world y = 742) never leaves the frame: skirting board, classroom floor,
   kerb, horizon, hill contour. Sets grow out of it and sink back into it.
3. **Things draw themselves on in time with the music**: one stroke per beat, half beat or measured
   attack, the chalk tip leading. They are un-drawn from their ends and leave a rubbed ghost that
   fades. Nothing pops and nothing cross-fades.
4. **Only the scribble is black.** Cold chalks (white, blue-grey, dim, far) for everything else at
   night; amber belongs to the friend alone (the friend, the friend's window across the street,
   the amber ground line, the tape, the phone call). Before 217.84 nothing else has colour.
5. **Light is rubbed pastel**: pools, shafts and glows through the paper's tooth, one bloom.
   Depth comes from tone (far = dimmer, thinner), mist at the horizon, overlap and cropping by the
   frame. A frame must look like a picture, never like a diagram: sets are dressed (hatch, rubbed
   tone, light), big things are cropped and overlap.
6. **The line boils on twos and the paper does not move.** In the two true silences (56.00-58.60
   and 193.00-201.25) the boil is held and the rain hangs still in the air: the only times the
   picture is completely still.
7. **The camera** moves slowly and on eases; it pushes in for faces and pulls back for
   loneliness. Faces must be big enough to act when they act (head at least 90 px on screen for
   a close beat). The band y > 864 (0.80 H) belongs to the lyric line: ground, floor and light may
   be there, nothing that matters.
8. **Acting first.** Every lyric line has one clear action by the child (listed below). Poses are
   blended with different timing per body part (eyes lead, then head, spine, hands; hair arrives
   last), with anticipation and a small overshoot; holds are alive (breathing, a blink now and
   then). Walks are one step per beat (0.75 s), feet planted.
9. **Day skin** (after the ring): warm paper, pencil-brown line, soft pastel and crayon colour,
   a low sun, long shadows, haze. A talented child's pastel drawing at golden hour: no icon sun
   with ray spikes, no stamped clouds, no ruler-regular hatch, no saturated primaries.

## 3. Cast and recurring things

- **The child**: white chalk line, pale chalk face, cold blue hatched jumper, dark-blue hair cap
  with tufts (droop when low, stand up when glad), heavy lids with bags. World height 380.
- **The friend**: the same build in amber crayon, A-line coat, bob with a small ponytail, scarf
  with two lagging tails, a soft amber glow. Always to the child's right in two-shots (child at
  world x about 900, friend about 1080). World height 388.
- **Other people**: faceless outlines in dim chalk (pupils with a satchel, adults taller), turned
  away or passing. In the last chorus they turn round and are just children with dot faces.
- **The scribble (the weight)** and **the strand** from the child's crown or fist into it. Sizes:
  a cloud over the sofa; a shawl on the shoulders; a ceiling over the plain; two curtains hanging
  to the ground; at the end a small tangle on a string.
- **Home that came apart**: the table with three chairs (two pulled apart); the child's drawing of
  three figures hand in hand, torn through the middle (on the wall; later as two halves in the
  child's hands; later taped with amber tape and put away small in the distance; in the coda
  taped on the wall); in the choruses a child's drawing of a house split down the middle.
- **School that shut the child out**: the desk that stands apart from the rows of turned backs;
  the ring of backs with whispers (scribbles passing from head to head); the stream of pupils on
  the one narrow line of the corridor floor; in the choruses enormous turned backs (coats, hands
  in pockets) and speech balloons full of crossed-out zigzag (never writing), tails aimed at
  the child.
- **Crows** on the wire under the eaves outside the window: black rubbed bodies with a pale
  outline. After colour they are only birds.
- **The phone**: a small dark slab on the rug. Its screen is a pale cold rectangle in the second
  verse; it lights amber and rings in the coda.
- **The amber window** across the street, lit from the first seconds: the friend was always there.

## 4. Spans, authors and hand-offs

The film is written as eleven scene modules, one time span each. At a hand-off both modules must
draw EXACTLY the state given in `hx/story.py` for that time (camera, the child's place and named
pose, the friend, the scribble, the set and its state, rain, skin): the frame before and the
frame after a hand-off must be the same picture. At every hand-off the figures hold a named pose
(they are still, breathing); movement starts after it.

| module | span | sections | hand-off at its end |
|---|---|---|---|
| `s01_room` | 0.00-36.27 | intro, v1a, v1b | B1: night room complete, 11 crows, child standing beside the sofa, head down |
| `s02_pre1` | 36.27-58.60 | p1a, p1b, hush1 | B2: bare sheet, ground line, child standing, cloud, rain hanging still |
| `s03_plain1` | 58.60-91.77 | c1a, c1b, inter | B3: evening room complete, child standing on the rug by the sofa |
| `s04_eve` | 91.77-115.77 | v2a, v2b | B4: bare sheet, child standing planted, cloud |
| `s05_pre2` | 115.77-138.20 | p2a, p2b | B5: bare sheet, child standing head down, large cloud |
| `s06_storm` | 138.20-158.86 | c2a, c2b | B6: plain, thinned ceiling, child sitting and friend crouched, hands joined, both looking up |
| `s07_bridge` | 158.86-182.30 | br_a, br_b, br_c | B7: plain with the first hill, both standing, the friend's hand on the child's shoulder, high cloud |
| `s08_part` | 182.30-201.25 | bd, hush2 (to the slam) | B8: the scribble parted as two curtains, both holding it apart, the shaft |
| `s09_colour` | 201.25-226.76 | c3a, c3b | B9: day skin complete, hills, the two hand in hand, the small tangle on its string |
| `s10_out` | 226.76-244.50 | out | B10: bare warm sheet at evening, child alone standing, the tangle on its string |
| `s11_coda` | 244.50-258.87 | coda | (end: slow lift toward warm paper) |

### The journey (one continuous world; numbers in `hx/story.py`, which is binding)

The child travels to the right through one world; nothing is ever re-centred, because the ground
line is one stroke with one hand. The same room is drawn at three places.

| world x | what stands there | when |
|---|---|---|
| 0 to 1920 | the room at night (`dx = 0`); the child leaves it at `X1` = 1040 | 0 to 36.27 |
| 1040 to 2200 | the trudge: the classroom, then the home table, drawn round the walking child | 36.27 to 56 |
| `X2` = 2200 | the bare sheet (B2); chorus 1: the plain, the wide frame (`WIDE_ZOOM` 0.205), the towers; the far friend at `X2` + 4900 | 56 to 80.5 |
| 2200 to 3700 | the walk along the amber line | 80.5 to 91.77 |
| 3060 to 4980 | the evening room (`dx = ROOM2_DX`); the child on its rug at `X3` = 3700 (B3) | 85.75 to 103.7 |
| `X4` = 3760 | the corridor line; the bare sheet (B4) | 103.7 to 115.77 |
| 3760 to 4300 | the ring of backs, the walk out, the family line; the bare sheet at `X5` = 4300 (B5) | 115.77 to 138.2 |
| `X5` = 4300 | chorus 2, the bridge, the parting of the curtains (B6, B7, B8): the friend at `X5` + 180 | 138.2 to 201.25 |
| from `HILL_X0` = 4700 | the first hill rises; they walk over it to its top at `X9` = 5600 (B9) | 205.9 to 226.76 |
| 5600 to 9000 | the run over the hills; the hills are rubbed out round `X10` = 9000 (B10) | 226.76 to 244.5 |
| 7700 to 9620 | the warm room of the coda (`dx = ROOM3_DX`); the child walks left to its sofa | 244.5 to the end |

Hand-offs are made the same on both sides by construction: `hx/scenes/_shared.py` draws each
hand-off picture (`B1` ... `B10`: set, figures in their rest state, the scribble, light, rain,
camera) as a function of time; the earlier module draws nothing but that picture for the last
0.25 s before the hand-off, and the later module starts from it.

## 5. The film, section by section

Times are on the song's clock. "Beat" times come from the timeline (`F.tl`); strong measured
attacks are listed where an action should land on them.

### s01_room (0.00-36.27)

**intro 0.00-12.27** (piano alone; bars at 0.27, 3.27, 6.26, 9.27; title in the upper middle from
2.0 to 10.5, so keep x 560-1360, y 60-260 empty).
- 0.27: on the first note the ground line is drawn across the empty dark sheet, left to right.
- Bar 2 (3.27): the sofa draws on, a stroke per beat (back, arms, seat, cushion), then its hatch.
- Bar 3 (6.26): the window (frame, mullions, curtains); behind it the wire, the roofs, and at
  about 8.5 one window across the street is filled in amber: the first and only warm thing.
  Rain starts as dashes behind the glass. The lamp, the torn drawing on the wall, the table with
  its three chairs (two pulled apart), the rug and the phone on it come in quietly between beats.
- Bar 4 (9.27): the child is drawn, curled on the sofa: spine, limbs, jumper hatch, head, hair,
  and last the face with closed heavy lids (done by 11.3). From 11.0 a black crayon starts the
  scribble over the child: the first loops.
- Camera: the whole room (zoom about 0.95), barely drifting in.

**v1a 12.27-24.27**
- idx 5 (12.34; the child clings to the sofa, bleary, hair on end): the camera eases in on the
  sofa (child's head about 150 px). The child breathes, shifts, pulls the cushion closer, opens
  bleary eyes halfway. On the strong attacks (12.27, 13.29, 14.87) the scribble gets more loops,
  sags, and rests its belly on the child (the child's back gives under it); a few loose runs of
  the black crayon stray over the child's shoulder like a crossing-out.
- idx 6 (16.50; it wishes it were as dashing as a film hero): the child's hanging hand lifts and
  a thin bright chalk line sketches on the wall above the sofa a small upright figure of itself
  with a cape, fists on hips (16.5-18.0). The child's eyes go up to it, then the head (the first
  time the face lifts); the cape waves on the beats; the child's mouth almost smiles.
- 20.79, 21.2, 21.6: three hard zigzags of the black crayon cross the hero out. The child's eyes
  fall, the hand drops. The hero stays as a rubbed ghost and fades.
- 22.0-24.2: the child sits up slowly on the sofa and hugs its knees; the camera eases back and
  drifts right until the window is in the right half of the frame.

**v1b 24.27-36.27**
- idx 8 (24.19; crows lined up under the eaves, more and more): outside the window crows land on
  the wire, one per beat from 24.27 (six by 28.0), each landing makes the wire dip and swing;
  the child, sitting, turns its head to the window and watches.
- idx 9 (28.59; feelings pressed down that it does not know how to say): the child opens its
  mouth. A speech balloon draws itself from its mouth (28.6-29.4); nothing comes into it but a
  knot of black scribble (29.4-30.6). At 31.58 the child wipes the balloon away with its sleeve;
  the knot rises on a thin dark strand and joins the scribble, which swells: from here on the
  strand between the child and the scribble exists. 32.0-33.6: it tries once more, smaller: the
  mouth opens, only a small knot leaves and rises. With each failed try more crows land (eleven
  at the end).
- 33.6-36.2: the child slides off the sofa, stands beside it with its head down. Camera back to
  the whole room. Hand-off B1.

### s02_pre1 (36.27-58.60)

**p1a 36.27-48.27** (wherever it is, it is not there)
- 36.27-38.6: the room turns into the classroom around the child: declared pairs only (window to
  window, now a grey day; sofa to the desk that stands apart; table and chairs to the rows of
  desks with turned backs; the wall drawing to the board), the rest un-draws and draws on,
  staggered on the beats. The child starts to trudge right on 36.27, one step per beat, the camera
  travelling with it; the scribble and the strand follow it.
- idx 11 (36.27): it trudges past the rows; nobody turns.
- idx 12 (40.34; its voice is like the cry of an insect that has lost its soul): the child stops,
  lifts its face, and its voice leaves its mouth as a thin wavering chalk line that wanders past
  the turned backs; nobody takes it up; it droops, turns dark and winds up the strand into the
  scribble (40.3-42.6).
- idx 13 (42.66; but it knows it should make an effort now): it goes to its desk and pushes it one
  step toward the rows (42.7-43.4); the rows are one step further away (44.12). It pushes again
  (44.86); further again. Its arms drop (46.2). 46.5-48.2: the classroom un-draws while the
  child walks on; a street lamp and a kerb draw on and pass.

**p1b 48.27-56.00** (the past that cannot be mended)
- idx 15 (48.27): the walk brings the child home, as memory: a large table with three chairs
  draws on, and on two of the chairs two tall faceless outline adults; the third chair is the
  child's. The torn drawing is here whole, lying on the table.
- idx 16 (52.36): the two adults stand up and walk away to opposite sides, each un-drawing as it
  goes (52.4-54.4); the two chairs slide apart; a tear draws itself down the middle of the
  drawing (53.14, 53.51).
- idx 17 (54.64; every time it comes to mind): the child takes the two halves and holds them
  together with both hands (55.01); when it loosens its grip they drift apart (55.27, 55.72). It
  keeps one half in each hand and tucks them into its jumper.
- 55.2-56.0: every line of the set is taken back from its ends.

**hush1 56.00-58.60** (true silence): the bare sheet: the ground line, the child standing with its
head down, the cloud of scribble and the strand, chalk dust. The boil is held; the rain that had
started hangs still in the air. At 58.56 the picture breathes in. Hand-off B2.

### s03_plain1 (58.60-91.77)

**c1a 58.60-70.70** (the band enters)
- 58.60: on the entry the ground line shoots out to both edges and beyond: a horizon. Rain falls
  again. idx 19 (58.76; it has thought of leaving): the child turns its back to us and walks away
  toward the mist band at the horizon, its line losing pressure with every step.
- **60.27: the pull-back.** One eased move in about 2.2 s from the child at mid size (about
  330 px) to the child at about 78 px in a vast empty sheet. The scribble spreads out into a
  ceiling over the whole plain. idx 20 (60.73; existing like this).
- idx 21 (63.66; because of those voices, those postures, those hurts): on 64.77, 66.27 and 67.77
  three groups draw themselves on, each in about six frames with a small camera jolt, enormous,
  cropped by the frame, overlapping, toned for depth: (1) speech balloons full of crossed-out
  zigzag, tails aimed at the child; (2) turned backs as tall as the sky, hands in pockets; (3) the
  drawn house split down the middle, its halves leaning apart, and behind it the two doors.
  The child stops walking at 64.77 and flinches smaller at each hit.
- 68.4-70.6: it stands, nearly rubbed out, small under all of it.

**c1b 70.70-80.50**
- idx 23 (70.71; it does not want to leave): the child's line stops fading. Far right on the
  horizon one amber stroke appears, then a tiny amber figure, waving with its whole arm.
- idx 24 (72.46; when you say you are still there): an amber line runs from the friend's feet
  along the ground line, as a pulse per beat, all the way to the child's feet (arrives 74.6). An
  amber rim appears on the child's right side. The child turns round (toward us, then to the
  right).
- idx 25 (75.49; suddenly, for no reason, it begins to look forward): the head lift, the first
  one that stays: anticipation dip, slow rise with a small overshoot, a blink on the way, hair
  arriving late, a spark in the eyes (76.67). The child's line regains its pressure. The towering
  drawings lose theirs (dimmer, thinner); the rain thins. The camera travels back in along the
  amber line to mid size.

**inter 80.50-91.77** (instrumental, calm)
- The child walks right along the amber line, one step per beat, head a little higher than
  before (walk mood 0.3). The tiny friend ahead never gets nearer: it waves once more (82.76),
  turns and goes on, and becomes a point of amber light.
- 85.75-90.5: the plain turns back into the room around the walking child, in evening light:
  horizon into skirting line, the house halves into the window frame, the turned backs into
  curtains, the ceiling gathers back into a cloud; the amber point is now the lit window across
  the street, seen through the room's window. The rain has stopped.
- 91.0: the phone on the rug shows its pale screen for a moment. Hand-off B3.

### s04_eve (91.77-115.77)

**v2a 91.77-103.77** (sunset, still without colour: a pale warm-grey window, a long pale pool of
light on the floor)
- idx 27 (91.84; sunset, leafing through the phone, nobody calls): the child sits down on the
  rug, back against the sofa, picks up the phone. Its thumb moves on the attacks (93.05, 93.26,
  94.75, 95.98); the screen lights its face pale; on the screen a column of empty lines slides
  by. Nothing comes. It turns the phone face down.
- idx 28 (96.18; perhaps that is what someone used to being alone deserves): the cloud of
  scribble sinks and settles on its shoulders like a shawl; the child draws up its knees and
  puts its forehead on them. Slow push in. The amber window across the street is lit the whole
  time; the child does not look.
- 101.6-103.7: the edge of the light pool on the floor stretches out into one long narrow line;
  the room un-draws; the child stands up onto the line.

**v2b 103.77-115.77**
- idx 30 (103.53; the single-plank bridge: whom must one push off to win): the one narrow chalk
  line on the corridor floor (a line drawn on the floor, not a height: floor on both sides,
  doors and lockers faint behind). A stream of faceless outline pupils comes the other way along
  the line, two per bar; each time the child is shouldered and it is the child who steps off the
  line to let them by (104.07, 105.23, 106.57): it pushes nobody.
- idx 31 (108.01; when will its silent resistance win): at 108.25 it stops stepping aside: feet
  planted on the line. The stream parts around it. The black crayon crosses out part of the
  child (an arm and a shoulder, 109.6); with a stub of chalk the child draws its own outline
  again (111.0-112.0); the crayon crosses out more (113.5); it draws itself again (114.3).
  The stream thins and un-draws. Hand-off B4: bare sheet, the child standing planted.

### s05_pre2 (115.77-138.20) (the two pre-choruses again, heavier: lines pressed harder)

**p2a 115.77-127.77**
- idx 33 (115.83): turned backs draw on around the child, one per half beat, until they stand in
  a ring; whispers pass as small dark scribbles from head to head round the ring (118.4,
  118.76, 119.14). The child turns on the spot; whichever way it faces there is a back.
- idx 34 (119.79; the lost insect's cry again): its voice leaves as a thin line, circles a hanging
  lamp like a moth (121.00) and drops.
- idx 35 (122.19; it knows it should make an effort): the child reaches a hand out to one back
  (123.26); that back un-draws under its hand. It tries the next (124.76); gone too. At 126.26 it
  walks out through the gap. The ring unrolls behind it into one long line across the frame
  (127.01-127.76).

**p2b 127.77-138.20**
- idx 37 (127.78): that line is the family's line: three drawn figures hand in hand as in the
  child's drawing, now as tall as the child: two tall ones and the child between them, holding a
  hand on each side.
- idx 38 (131.69; the past that cannot be mended): the line parts: the two tall figures slide
  away toward the two edges of the frame (131.85-134.0), their arms stretching into long lines
  that the child holds, one in each hand, leaning back with its whole weight to keep them.
- idx 39 (134.18): the lines slip through its hands (134.51, 134.77); the child sits down hard.
  The two figures un-draw at the edges. The two halves of the torn drawing fall out of its
  jumper; it gathers them up and holds them to its chest (135.6-137.0). The scribble swells.
  137.0-138.1: it stands. Hand-off B5.

### s06_storm (138.20-158.86)

**c2a 138.20-150.10** (the storm at its worst)
- 138.26 (idx 41): the horizon shoots out, heavy rain slants in, and the pull-back comes again,
  faster (1.4 s). The child walks away into the mist, losing pressure, as in the first chorus but
  further gone; the ceiling comes lower than before.
- idx 43 (142.96): on 144.27, 145.77, 147.27 the three groups land again, bigger, nearer,
  overlapping more. The child sits down and hugs its knees; the ceiling lets loops down over it
  until only the outline of its head shows (148.5).
- From 147.3, far right: the amber figure, not waving this time but walking in along the ground
  line, leaning into the rain, one step per beat, growing.

**c2b 150.10-158.86**
- idx 45 (150.16; it does not want to leave): the friend runs the last steps (150.26), stops,
  crouches down in front of the child. The camera closes in to a two-shot.
- idx 46 (151.81; perhaps, having tried being loved): the friend holds out an open hand (152.36).
  The child's hand comes out of the scribble, hesitates, and takes it (154.40): where they touch,
  amber rubs off onto the child's white hand and travels a little way up its arm. The friend
  brushes the loops off the child's shoulders with its other hand.
- idx 47 (154.84; one begins to look up toward the future): the child lifts its head (same
  choreography as at 75.49, shorter); both look up: the ceiling has one thin pale place above
  them (157.01). The rain thins. The towering drawings have lost their pressure and un-draw.
  Hand-off B6.

### s07_bridge (158.86-182.30)

**br_a 158.86-170.76** (idx 48; the scars: leave them to memory)
- The two sit side by side. The friend finds a loose end of the scribble hanging down and pulls
  (160.0): a long dark line unravels and coils on the ground, a pull per bar (161.9, 164.9,
  167.9); the ceiling thins.
- 162.3-166.5: the child takes the two halves of the torn drawing out of its jumper. The friend
  holds out two strips of amber tape; together they tape the halves (165.63, 166.39). The tear
  still shows.
- 167.1-170.7: the child holds the mended drawing up and lets it go: it rises, shrinking, and
  stays far off and small in the sky, pinned there (put away, kept). Far away the split house
  redraws small with its halves together.

**br_b 170.76-178.26** (idx 49; letting go is how something better comes)
- The child looks at its own fist: it has been clutching the dark strand all along. It opens
  the fist (173.5): the strand slips out and floats up; the scribble rises by a head and gathers
  into a high cloud. It opens the other hand too (175.0).
- 175.0-178.2: the long unravelled line on the ground straightens, lifts and settles as the
  contour of a hill behind them: the first hill. The camera eases back a little to show it.

**br_c 178.26-182.30** (idx 50; do not be afraid, said twice)
- 179.51: both stand up; the friend's hand on the child's shoulder. 181.00-181.76: the friend
  takes both the child's hands for a moment, then the hand goes back to the shoulder; the
  child's eyes open fully for the first time in the film. Close two-shot. Hand-off B7.

### s08_part (182.30-201.25)

**bd 182.30-193.00** (quiet; sparse attacks at 184.34, 185.14, 186.26, 186.65, 187.56, 188.14,
188.90, and the strong one at 191.90)
- idx 52 (183.12; it has thought of leaving): the high cloud comes down again and closes over
  the two: the pale light goes (idx 53, 184.81; when the sunlight lost to the haze). The
  scribble hangs to the ground like a curtain all round them. The child's line pales; its head
  sinks; it sits down.
- idx 54 (187.84; it never expected the friend would fight so hard to part it): the friend
  pushes its hands into the curtain and pulls it apart, with its whole body, leaning back; on
  each attack one more strand comes aside (the friend slips, plants its feet again, pulls
  again); a shaft of pale light opens in the gap and lands on the child (188.9).
- 189.6: the child lifts its head into the shaft (the full head-lift choreography). 191.90: it
  stands up.

**hush2 193.00-201.25** (true silence; the boil held, dust turning slowly in the shaft)
- The friend holds the two curtains apart, arms trembling. The child steps beside it and puts its
  own hands up (195.5-197.0); both lean back with their whole weight on the taut strands.
- 200.4-201.2: a breath in: they pull once more. Hand-off B8 at 201.25.

### s09_colour (201.25-226.76)

**c3a 201.25-213.10**
- **201.25: the sheet rips.** Along the gap the dark sheet itself tears open (0 to full in eight
  frames, a flash of pale light, scraps of dark paper falling); under it is pale warm paper; the
  curtains fall aside and drift off as ceiling fragments. Broad pale shafts fall on the land,
  which now has hills. Light, not yet colour. The two are thrown back a step, then stand, catch
  their breath, look at each other (idx 56, 200.84; idx 57, 203.27: yet it held on until now).
- idx 58 (205.92; it got through those voices, those postures, those hurts): the two walk right
  over the first hill, camera travelling. On 207.26, 208.76, 210.26 the three groups draw on
  once more, pale and only knee-high, and each is answered as the two pass: the balloons empty
  and float off like soap bubbles; the turned backs turn round and are just children with dot
  faces, one of whom lifts a hand; the house halves are pushed together by the two and get a
  strip of amber tape.
- 211.7-213.0: they reach the top of the hill.

**c3b 213.10-226.76**
- idx 60 (213.14; it does not want to leave): the child stops and turns to the friend.
- idx 61 (214.87; when your smile opens): the camera pushes in close on the two faces. The
  friend's face opens into its smile (216.07-216.98); the child answers with a small one, its
  first (217.33): its tufts stand up.
- **idx 62 (217.84; the world is suddenly filled with colour): the ring.** It opens from the
  joined hands and reaches the frame edges in about five seconds while the camera eases back
  to wide; inside it the same drawing is on warm paper in pastel and crayon; flowers open on
  the eighth notes just behind the ring's edge; the last crows on the roof fly up as birds.
- By 224.5 the ring is past the frame. Hand in hand on the hill, the small tangle of scribble
  bobbing on a string in the child's free hand. Hand-off B9.

### s10_out (226.76-244.50) (instrumental, full, joyful; accents at 229.76, 232.76, 233.69, 235.75, 238.75, 241.01)

- 226.8-238.7: the two run over the hills to the right, the camera travelling, three layers of
  hills in parallax, a low sun, long shadows. They jump on the accents (the friend first, the
  child copying, then together); the tangle bobs behind like a balloon; birds; flowers.
- 235.75-238.75: they roll or sit down in the grass, out of breath, laughing.
- 238.75-242.0: golden evening. They stand; the friend points home (the house with the amber
  window, far off), waves, and walks off right; the child waves back.
- 242.0-244.4: the hills and the sky are rubbed out from their ends; the hill contour flattens
  into the one ground line. Hand-off B10: the child alone on the bare warm sheet.

### s11_coda (244.50-258.87) (piano alone, as at the start)

- idx 64 (244.64; the first line of the first verse again): the child walks left; the room draws
  itself on around it with the piano attacks (244.77, 244.97, 245.57, 245.86, 247.49), the same
  room as in the intro, on warm paper at sunset: the sofa, the lamp (lit), the window with a
  sunset sky and an orange pool of light on the floor, the table (two chairs still apart), the
  drawing on the wall, taped. The child ties the string of the small tangle to the armrest,
  climbs onto the sofa and curls up exactly as in the intro, but at ease: a slow breath, eyes
  closing.
- idx 65 (250.74; sunset, the phone connects: it is you): the phone on the rug lights amber and
  rings (rings pulse at 251.41, 251.83, 252.37, 252.61, 252.87). The child's eyes open; it
  reaches down, picks it up, holds it to its ear (253.6), and smiles. Through the window: the
  house across the street, its amber window, and a small amber figure in it, waving (255.0).
- 255.5-258.6: the camera lifts slowly away; the picture holds, a little chalk dust falls, and
  the sheet fades toward plain warm paper.

## 6. What the kit must provide (inventory)

Figure rig: the child and the friend with the poses and cycles named in section 5 (curled asleep
on the sofa, clinging, lying and looking up, sitting hugging knees, sitting up, speaking, wiping
with a sleeve, standing head down, trudge and walk (mood 0 to 1), back view walking away, turning
round, pushing a desk, holding two paper halves together, sitting on the floor with a phone,
shouldered aside, planted, drawing on its own arm with a chalk stub, reaching out, leaning back
and pulling, looking up, the head lift with its timing, holding hands, smiling, running, jumping,
waving, lying with a phone at its ear; the friend waving far away, walking leaning into rain,
crouching and offering a hand, brushing loops away, pulling a loose end, taping, a hand on a
shoulder, holding the curtain apart on tiptoe and slipping, the big smile, running, jumping,
pointing), plus faceless outline people (pupils with satchels, taller adults, giant turned backs)
and the three drawn figures of the family line.

Scribble: cloud (with a belly that rests on a point), strand, stray crossing-out, shawl, ceiling
(with a thin pale place), curtains hanging to the ground and parted, a loose end being pulled out
into a long line, a small knot (in a balloon, rising), the small tangle on a string.

Light and weather: rain (with a clock that can stand still), mist band, window pools (night cold,
evening pale, sunset orange), lamp glow, shafts, dust in a shaft, amber glow, the amber ground
line with a travelling pulse, an amber rim on a figure, the tear of the sheet with scraps, flash.

Sets (canonical, named strokes, so that every module draws the same room): the room (night,
evening, warm sunset; window with wire, crows, roofs, the amber window, rain or sky), the
classroom, the street piece, the home table with two outline adults, the corridor line with its
stream, the ring of backs, the plain with mist and footprints, the three towering groups (giant
and knee-high), the hills (night chalk and day pastel, three parallax layers, the mended house,
tree, grass, flowers), the day sky and sun (day to golden evening), birds.

Small things: speech balloon (empty, with a knot), the voice line, the moth and hanging lamp, the
hero with a cape, the family drawing (whole, torn, taped, as two halves), tape strips, the chalk
stub, the kite-string, the phone (dark, pale screen with sliding empty lines, amber and ringing).
