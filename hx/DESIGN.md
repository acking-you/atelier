# hx: story, look and how the film is made (version 4, "the child's own drawing")

A music film for one studio recording (4:18.87, 80 BPM, 4/4, bar = 3.0 s), 1920x1080, 30 fps,
7766 frames; video time 0 = audio time 0. Every frame is a pure function of the recording's time.
Sections, line stamps, beats and measured attacks come from `hx/data/timeline.json`
(`hx/timeline.py`), never from guesses.

Version 4 is drawn entirely by code (skia + numpy), with no generated pictures: chalk and crayon on
dark paper, as if the child had drawn its own story. The user's verdict on the earlier versions
decided it: version 2 (code-drawn, semi-realistic figures) looked wrong and dull; version 3
(generated pictures composited by code) had no continuity of animation. So: simplified stick
figures on a real pose rig that act, and ONE continuous drawing with no cuts. Version 3's code is
in `hx/_attic/v3_pictures/` (its pictures stay in `hx/art/`); the prototype port of version 4 is
in `hx/_attic/v4_prototype_port/`.

## Hard rules

1. **No lyric text anywhere**: not in code, comments, file names, data, review images or reports.
   Lines are addressed by 0-based LRC index and time, or paraphrased. Render tests use
   `--lyrics placeholder` or no lyrics; the render with the real lyric file is run by the user.
   No letters or numerals inside the picture (scribbled zigzag stands for writing; the title
   overlay is the one exception).
2. **Care with the subject** (a child living with depression): causes (a family coming apart,
   exclusion at school) shown through image and metaphor, never graphic, never one cause that
   explains everything, nobody drawn as a villain (other people are faceless outlines turned
   away). No self-harm; no heights, edges, water or trains as threat ("leaving" is walking into
   mist and fading). No magic cure: relief is gradual and partly relational; the end is warm and
   open with the gloom still there, small, on a string.
3. **Continuity**: the child never cuts (on screen from 9.3 s to the end); one ground line (world
   y 742, one stroke with one hand) never leaves the frame; places change by un-drawing and
   drawing on round the child, by declared morphs, or by the camera travelling; nothing pops,
   nothing cross-fades. The two true silences (56.0-58.6, 193.0-201.27) are completely still
   except for what acts.

## The story in one paragraph

A small chalk child, white line and cold blue jumper, lies curled on a sofa under a black
scribble that a tired hand keeps drawing over it (the only black on the sheet). Its hero sketch
is crossed out; its words come out as a knot. The room turns into a classroom of turned backs
and into a home table that two adults leave; the family drawing tears. In the choruses the room
is gone: a bare plain under a lid of scribble, the child tiny, three enormous groups slamming
down on the hits (crossed-out voices, turned backs, a house split down the middle). Far away an
amber figure, the friend, waves; an amber line runs to the child's feet; its head lifts. The
second verse is the phone that nobody calls and the scribble as a shawl, the corridor where it
steps aside and then stands and redraws its own crossed-out outline. In the second chorus the
friend walks in through the storm, crouches, offers a hand; the child takes it; a thin pale place
opens above. They unravel the scribble together, tape the drawing, the child lets go of the dark
strand, the line becomes the first hill. The scribble comes down as curtains; the friend parts
them and the light lands on the child; in the long silence they hold the dark apart together. On
the band's return the sheet itself rips: warm paper under the dark. At the first small smile
(217.84) colour opens as a ring from their joined hands: golden-hour pastel hills. They run, jump,
lie in the grass, and part at evening. In the coda the room draws itself again on warm paper; the
child ties the small tangle to the armrest, curls up at ease, and the phone rings amber: the
friend, waving from the window across the street.

## How it is built

- `hx/chalk/`: the drawing kit. `README.md` first, then the part docs in `hx/chalk/doc/`
  (figure, acting_child, acting_pair, people, gloom, weather, sets, things, land, day). Core:
  camera-mapped Frame, screen-fixed paper tooth, line boil on twos, three clocks (`F.t` acts,
  `F.tb` is merely alive and stands still in the silences), named stroke sets that draw on,
  un-draw and morph by declared pairs, the colour ring (`day.ring`: the same scene in night and
  day skin).
- `hx/story.py`: the binding numbers: the journey through one continuous world (X1 ... X10, the
  room drawn at three places), seeds, the ten hand-off states B1 ... B10.
- `hx/STORYBOARD.md`: the film beat by beat with times, the nine rules of the drawing, the journey.
- `hx/scenes/`: eleven scene modules (`s01_room` ... `s11_coda`), one time span each, on
  `_shared.py` (the ten hand-off pictures and the shared layers; the joining rule: the last
  0.25 s of a module is the next hand-off picture). `README.md` there is the animator's guide.
- Tools: `python -m hx.still` (stills, sheets), `hx.render` (film or slice), `hx.handoff` (the ten
  joins), `hx.pops` (where the picture jumps), `hx.motion` (flicker), `hx.scenes` (spans),
  `hx/chalk/proof.py` (proofs of a piece without a scene).

## Known soft spots (version 4 as delivered)

- Motion was judged on strips of consecutive frames, pop scans and numbers; nobody watched the
  film at speed with sound before delivery.
- Per scene (from the animators' own lists): the scribble's birth at 11-12.6 s is not yet one
  gesture; the scribble drawn back during the hero (16-21.8) reads as a ball beside the child;
  the wipe at 31.3 is snappy; the plain-to-room change at 86 s has about ten frames of tangled
  line; the shawl gathers back fast at 102.8; the wide frame of chorus 2 (140-144) is flat; the
  line laid down as the first hill (175) does not read as cast; the shoves into the curtain
  (186) do not bulge it; the phone in the coda is small.
