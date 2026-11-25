"""The film's pictures, painted by the local codex CLI and shown by hx/scenes/film.py.

    python -m hx.concept                 # everything missing, 4 at a time
    python -m hx.concept --only v1a,coda_call [--force]
    python -m hx.concept --sheet         # contact sheets into hx/art/_sheets/

One headless codex process per picture (gpt-6-astra, xhigh, read-only sandbox, stdin closed): it
can do nothing but call its image tool. The PNG lands in ~/.codex/generated_images/<thread id>/
and is copied to hx/art/<id>.png. Prompts are our own descriptions of pictures: no lyric
text and nothing personal. Pictures are named by section id.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).parent / "art"
HOME_IMAGES = Path.home() / ".codex" / "generated_images"
MODEL = "gpt-6-astra"
EFFORT = "xhigh"

STYLE = ("Style: atmospheric Japanese pixel art, low resolution (about 384 by 216 pixels, shown enlarged with crisp "
         "square pixels), in the spirit of Makoto Shinkai's skies and light translated into pixel art: towering clouds "
         "with hard-edged lit rims, rain, mirror reflections on wet ground, shafts of sun, glowing windows. Limited "
         "palette, flat colour clusters, banded and dithered gradients, no anti-aliasing, no blur, no smooth "
         "gradients, no photographic detail. Characters are small simple sprites with big heads and a one-pixel dark "
         "outline, clearly readable against the background. Wide 16:9 film frame, the lower sixth of the picture kept "
         "calm and empty. No text, no letters, no numbers, no writing of any kind, no watermark, no border, no user "
         "interface.")

CHILD = ("a small nine-year-old child with a big round head, messy tufted black hair falling over the forehead, large "
         "tired dark blue-grey eyes, pale skin, an oversized dark navy hoodie with the hood down and two pale "
         "drawstrings, loose grey-blue trousers and pale worn sneakers")
FRIEND = ("a nine-year-old girl with a chin-length warm brown bob with a fringe and a small rose-red hair clip, bright "
          "warm brown eyes, a bright amber-yellow raincoat with the hood down, dark leggings and cream rain boots")

COLD = ("Palette: deep indigo, slate blue and blue-grey only, nearly monochrome, dim soft light, a heavy quiet mood; "
        "no warm colour anywhere")
COLD_AMBER = ("Palette: deep indigo, slate blue and blue-grey, nearly monochrome and dim; the single warm colour in the "
              "picture is the small amber light described")
DUSK = ("Palette: muted indigo and slate with one deep persimmon-orange sunset light and long shadows; warm light in a "
        "lonely room")
STORM = "Palette: dark indigo and steel blue, hard wind, churning cloud, strong contrast, almost no colour"
BREAK = ("Palette: still mostly dark blue-grey, with warm golden shafts of sunlight cutting down through the cloud and "
         "the amber raincoat as the only strong colours")
LIGHT = "Palette: brightening, pale gold sun through thinning cloud, the first soft greens and blues returning"
COLOUR = ("Palette: full vivid saturated colour, clear warm sunlight, a brilliant blue sky with towering white cumulus "
          "clouds, fresh greens, small flowers")
GOLD = "Palette: warm golden-hour light, rich colour, long soft shadows, a gentle glow"

ROOM = ("a small living room seen straight on like a stage set: a three-seat sofa against the back wall on the left, a "
        "tall window with long curtains on the right showing apartment blocks, between them on the wall a child's "
        "crayon drawing of a family of three holding hands that was torn in two and taped back with a gap, and in the "
        "far right corner a small dining table with three chairs")
PLAIN = ("an endless flat rain-wet plain whose puddles and thin sheen of water mirror the sky, short grass tufts, "
         "drifting mist hiding the horizon, under a sky completely covered by one enormous low dark cloud")
HILL = ("a rounded grassy hilltop above a sea of mist, with soft far hills and a tiny town on the horizon")
CLOUD = "a heavy dark-grey cloud, soft and real, the child's own gloom"

SHEET = ("A pixel art sprite sheet on a plain flat mid-grey background: low-resolution sprites shown enlarged with crisp "
         "square pixels, each standing sprite about 48 pixels tall with a big head, limited palette, flat colour "
         "clusters with one shadow tone and a one-pixel dark outline, no anti-aliasing, no blur, no gradients; simple "
         "shapes that are easy to redraw. Wide 16:9 sheet. No text, no letters, no numbers, no labels, no watermark.")

# id -> (reference ids, picture). References are attached to the codex prompt in this order.
PLAN: dict[str, tuple[tuple[str, ...], str]] = {
    "00_child_px": (("00_child_sheet",), f"{SHEET} Redraw the character of the attached anime model sheet as pixel art sprites, keeping the design exactly: {CHILD}. Top row: full-body turnaround of the same child standing "
                           "slightly slumped, seen from the front, three-quarter, side and back. Bottom row: six larger head "
                           "sprites with different expressions: heavy and empty, eyes closed, looking up warily, "
                           "surprised, a very small first smile, a quiet open smile."),
    "00_friend_px": (("00_friend_sheet",), f"{SHEET} Redraw the character of the attached anime model sheet as pixel art sprites, keeping the design exactly: {FRIEND}. Top row: full-body turnaround of the same girl standing "
                            "upright and calm, seen from the front, three-quarter, side and back. Bottom row: six larger head "
                            "sprites with different expressions: gentle attention, concern, determined effort with "
                            "pressed lips, a warm closed smile, a wide open smile, looking up."),
    "01_child_seated": (("00_child_px",),
                        f"{SHEET} The same child as in the attached sprite sheet, drawn full body in five clearly separated "
                        "seated poses in a row: curled up in the corner of a sofa hugging a cushion with knees to the "
                        "chest; sitting on the floor with the back against a wall and knees up, arms on the knees; "
                        "sitting on the floor looking down at a lit phone held in both hands; sitting curled on a sofa "
                        "holding a phone to the ear with a small smile; sitting cross-legged with eyes closed and "
                        "hands in the lap."),
    "01_child_walk": (("00_child_px",),
                      f"{SHEET} The same child as in the attached sprite sheet, full body, side view facing right: a walk "
                      "cycle of six evenly spaced phases in one row, head down and shoulders slumped, small tired steps, "
                      "hands hanging in the long sleeves. Below it a second row of four phases of the same child "
                      "walking with a longer, lighter stride, head up."),
    "01_child_actions": (("00_child_px",),
                         f"{SHEET} The same child as in the attached sprite sheet, full body, five clearly separated "
                         "standing poses in a row: stretching up on tiptoe with one arm raised high; leaning forward "
                         "into a strong wind while hugging an armful of torn paper pieces to the chest, hair and hoodie "
                         "blown back; standing with both arms opened wide and the face lifted; standing and turning "
                         "to look back over the shoulder; hesitantly holding one hand out."),
    "01_friend_actions": (("00_friend_px",),
                          f"{SHEET} The same girl as in the attached sprite sheet, full body, six clearly separated poses in "
                          "a row: standing upright with hands at her sides; holding one open hand out to someone; "
                          "on tiptoe pushing upward with both arms as if shoving a heavy ceiling; jumping with both arms "
                          "thrown up; waving with one arm while holding a phone to her ear; walking with an easy stride "
                          "holding a kite string."),
    "01_pair": (("00_child_px", "00_friend_px"),
                f"{SHEET} The two children from the attached sprite sheets together, full body, four clearly separated "
                "pairs in a row: standing shoulder to shoulder facing the same way; the girl's open hand held out "
                "and the child's hand just taking it; walking side by side to the right, the girl half a step ahead; "
                "both looking up at the sky, seen from slightly below."),

    # --- room world ---
    "intro": (("00_child_px",),
              f"A wide, quiet night shot of {ROOM}. Only one chair at the table has a bowl in front of it. {CLOUD}, hangs "
              f"under the ceiling and fills the upper third of the room. On the sofa a small dark shape: {CHILD}, curled "
              f"up and turned away. The only light is the dull grey window. {COLD}. {STYLE}"),
    "v1a": (("00_child_px",),
            f"A medium shot in a dark living room at night: {CHILD}, curled deep in the corner of a sofa hugging a "
            "cushion, eyes half closed. The underside of a heavy dark-grey cloud almost touches the child's hair. A cold "
            "flickering television light from off-screen throws the child's shadow on the wall behind, and that shadow "
            f"stands tall as a caped film hero with fists on the hips. {COLD}. {STYLE}"),
    "v1b_crows": (("00_child_px",),
                  f"Night, inside a dark living room looking toward a tall window: {CHILD}, seen from behind, small in "
                  "the foreground, standing at the window. Outside, under the edge of the roof eave, a dense uneven row "
                  f"of black crows sits on a wire, some landing with wings flared. {COLD}. {STYLE}"),
    "v1b_door": (("00_child_px",),
                 f"Night, a dark hallway corner of a home: {CHILD}, sits on the floor with the back against a closed "
                 "door, knees up. Under the door a thin strip of pale light, and in that strip the shadows of two adults' "
                 "feet standing far apart, turned away from each other. Above the child's chest a dark tangled scribble "
                 "of thread rises like a speech balloon that never closes, drifting up into a heavy grey cloud under "
                 f"the ceiling. Nobody else is visible. {COLD}. {STYLE}"),
    "inter": (("00_child_px",),
              f"Late afternoon in {ROOM}, the window light warming toward sunset. {CHILD}, sits on the floor under the "
              "window with the back to the wall and knees up. A single tiny amber firefly light rests on the window "
              "sill and glows steadily. A thinner grey cloud hangs higher under the ceiling. Three chairs at the table, "
              f"all empty. {COLD_AMBER}, with a faint rose warmth in the window. {STYLE}"),
    "v2a_phone": (("00_child_px",),
                  f"Sunset in a quiet living room: a huge persimmon sun fills the window and throws one long orange shaft "
                  f"across the floor. {CHILD}, sits on the floor in the shaft's edge looking down at a phone held in both "
                  "hands; the phone's cold light on the face; the screen shows only blank pale bars. The child's long "
                  f"shadow lies alone across the floor. A heavy grey cloud presses low under the ceiling. {DUSK}. {STYLE}"),
    "v2a_windows": (("00_child_px",),
                    f"Dusk, seen from inside a dark room over the shoulder of {CHILD}, who sits small in the lower left "
                    "foreground as a dark shape: through the big window the apartment block opposite, where warm windows "
                    "have lit up one by one, and in each lit window the tiny silhouettes of a family of three at a table. "
                    f"Inside this room, a table with three empty chairs. {DUSK}. {STYLE}"),
    "coda_sofa": (("00_child_px",),
                  f"The same living room as a warm sunset evening in full colour: {ROOM}; the window is open to a peach "
                  f"and gold sky. {CHILD}, lies curled in the sofa corner exactly as on a bad day, wearing a deep teal "
                  "hoodie. A single small pale-grey cloud, the size of a balloon, bobs above the sofa on a thin string "
                  "tied to the sofa arm. A folded paper bird sits on the window sill. On the wall, the torn family "
                  f"drawing is taped back together, the gaps still showing. {GOLD}. {STYLE}"),
    "coda_call": (("00_child_px", "00_friend_px"),
                  f"Warm sunset evening in a living room in full colour: {CHILD}, wearing a deep teal hoodie, sits curled "
                  "on the sofa holding a warmly glowing phone to the ear, with a small real smile. A small pale-grey "
                  "cloud floats above on a thin string like a balloon. Through the open window, far down the street, "
                  f"a tiny figure in an amber-yellow raincoat waves with a phone at her ear. {GOLD}. {STYLE}"),

    # --- places and memory ---
    "p1a_class": (("00_child_px",),
                  f"A grey classroom after rain, seen from the side: neat rows of desks with faceless grey pupils sitting "
                  "close together, and one single desk pushed far away from the rows, alone by the window, where "
                  f"{CHILD}, stands slumped beside it. A dark-grey cloud hangs over the child only. The blackboard holds "
                  f"only vague chalk smudges. {COLD}. {STYLE}"),
    "p1a_street": (("00_child_px",),
                   f"A wet evening street after rain with reflections on the pavement: {CHILD}, stands still and slumped "
                   "in the middle while faceless grey passers-by walk past without looking, among them a small child "
                   "holding both parents' hands. A dark-grey cloud hangs low over the child alone. "
                   f"{COLD}. {STYLE}"),
    "p1a_lamp": (("00_child_px",),
                 f"Dusk under a single street lamp on an empty wet street: {CHILD}, stands slumped in the lamp's cold "
                 "cone of light, a grey moth circling the lamp, the child's reflection in a puddle. A dark-grey cloud "
                 f"hangs just above the lamp. {COLD}. {STYLE}"),
    "p1b_table": (("00_child_px",),
                  f"A memory standing in empty fog: a dining table with three chairs floats in the mist, lit faintly warm "
                  "like an old photograph. Two faceless adult silhouettes are walking away from the table in opposite "
                  "directions, toward the left and right edges of the picture, and the table has split down the middle "
                  f"with the small third chair left alone at the gap. In the foreground {CHILD}, seen from behind, stands "
                  f"looking at it. {COLD}, except the faint faded warmth of the memory. {STYLE}"),
    "p1b_pieces": (("00_child_px",),
                   f"In empty grey fog, {CHILD}, reaches up with both hands toward drifting torn pieces of a child's "
                   "warm-coloured crayon drawing of a family of three holding hands; the tear runs right through the "
                   "small middle figure, and the pieces float apart and do not fit together. A dark-grey cloud overhead. "
                   f"{COLD}, with the crayon pieces as the only colour. {STYLE}"),
    "v2b_path": (("00_child_px",),
                 f"A grey school hall: a long row of desks set end to end makes a narrow knee-high path across the hall. "
                 "Faceless grey pupils with school bags hurry along it in a stream, shouldering past one another; one who "
                 f"was shouldered simply steps down to the floor. In the middle of the path {CHILD}, stands still, "
                 "gripping the bag straps, while the stream passes on both sides. Loose blank sheets of paper flutter. "
                 f"{COLD}. {STYLE}"),
    "v2b_ring": (("00_child_px",),
                 f"A grey school hall: {CHILD}, sits cross-legged on a row of desks with eyes closed, calm and still. "
                 "Around the child, faceless grey pupils stand in a ring with their backs turned; two of them lean "
                 "together mouth to ear, and a thin dark scribble of thread passes between them. On the blackboard "
                 "behind, a row of chalk scribbles, one of them scratched out with rough strokes. One paper plane "
                 f"drifts past the child. {COLD}. {STYLE}"),
    "p2a_lunch": (("00_child_px",),
                  f"A grey school canteen: one long lunch table completely filled with faceless grey pupils sitting "
                  f"shoulder to shoulder, seen from behind, no gap anywhere. {CHILD}, stands alone at the end holding a "
                  "tray, looking for a place. A dark-grey cloud hangs over the child; one tiny amber firefly light "
                  f"hovers near the shoulder. {COLD_AMBER}. {STYLE}"),
    "p2a_houses": (("00_child_px",),
                   f"A long empty wet street at dusk, seen from the side: at the far left end a small house with one lit "
                   "window, at the far right end another small house with one lit window, very far apart. In the middle, "
                   f"{CHILD}, walks between them with a small backpack. A dark-grey cloud follows overhead; one tiny "
                   f"amber firefly light follows behind. {COLD_AMBER}. {STYLE}"),
    "p2a_reach": (("00_child_px",),
                  f"An empty playground at dusk with a swing set: {CHILD}, stretches up on tiptoe and pushes one hand into "
                  "the soft underside of the dark-grey cloud that hangs just overhead; the cloud dents a little around "
                  "the hand and a thin paler grey leaks from the dent. One tiny amber firefly light hovers beside the "
                  f"hand. {COLD_AMBER}. {STYLE}"),
    "p2b_armful": (("00_child_px",),
                   f"Open ground in rising wind and fog: {CHILD}, stands holding an armful of torn pieces of a child's "
                   "crayon drawing to the chest, not fitting them together, only holding them; more pieces swirl around "
                   "in the wind; hair and hoodie blown sideways. Far behind in the fog, a faint table with three empty "
                   f"chairs. {STORM}, with the crayon pieces as faint colour. {STYLE}"),

    # --- the plain (choruses 1 and 2) ---
    "c1a_before": (("00_child_px",),
                   f"Near darkness: only the faint cold rim light on {CHILD}, standing with head bowed, seen close from "
                   "the side, while a heavy dark cloud settles down over the head and shoulders. Almost everything is "
                   f"deep ink blue. {COLD}. {STYLE}"),
    "c1a_wide": (("00_child_px",),
                 f"A very wide shot of {PLAIN}. In the lower middle, tiny, {CHILD}, walks slowly away from us into the "
                 "mist, already half faded and translucent, leaving a long faint reflection on the wet ground. Wind "
                 f"streaks cross the frame. Enormous scale, the child very small. {COLD}. {STYLE}"),
    "c1a_whispers": (("00_child_px",),
                     f"On {PLAIN}: {CHILD}, tiny and fading, walks away. Out of the mist loom giant shapes as tall as "
                     "buildings, made of fog and shadow: huge faceless heads leaning together mouth to ear with a dark "
                     "scribble of thread passing between them, hanging speech-balloon signs filled only with scribble, "
                     "and a giant blackboard with a row of chalk scribbles, one scratched out. Their reflections lie "
                     f"in the puddles. {COLD}. {STYLE}"),
    "c1a_backs": (("00_child_px",),
                  f"On {PLAIN}: {CHILD}, tiny, walks away between giant figures as tall as towers that stand in a ring "
                  "with their backs turned, faceless grey shapes of schoolchildren seen from behind, and a few giant "
                  "hands that point down out of the cloud. Crows wheel overhead. Reflections in the wet ground. "
                  f"{COLD}. {STYLE}"),
    "c1a_doors": (("00_child_px",),
                  f"On {PLAIN}: at the far left edge a giant closed front door standing alone in the mist, and at the far "
                  "right edge another giant closed front door, each with a faceless adult silhouette turned away beside "
                  "it; between them a long dining table broken in the middle, and tall jagged shards that are the torn "
                  f"halves of a child's crayon drawing standing in the ground. In the middle, tiny, {CHILD}, stands "
                  f"between the two doors. {COLD}, the crayon shards barely tinted. {STYLE}"),
    "c1b_ribbon": (("00_child_px", "00_friend_px"),
                   f"On {PLAIN}: {CHILD}, now solid and clear, has stopped and turns to look back over the shoulder. A "
                   "thin ribbon of small amber firefly lights crosses the mist from far behind and arrives at the "
                   "child's shoulder. Far back, very small, a third door stands open and lit warm, and beside it a tiny "
                   "figure in an amber-yellow raincoat waits without approaching. The door's light lies reflected on "
                   f"the wet ground. {COLD_AMBER}. {STYLE}"),
    "c1b_mote": (("00_child_px",),
                 f"A close shot in mist: {CHILD}, looks down at one small amber firefly light resting in the open palm; "
                 "its warm glow on the face and in the eyes, which are a little wider than before. Behind, soft dark "
                 f"shapes sink back into the fog. {COLD_AMBER}. {STYLE}"),
    "c2a_storm": (("00_child_px",),
                  f"A storm on {PLAIN}, the cloud lower and churning, hard wind streaks and rain: {CHILD}, leans forward "
                  "into the wind hugging torn paper pieces to the chest, hair and hoodie whipped back. Much closer and "
                  "bigger than before loom the giant shapes: faceless heads whispering mouth to ear, a ring of giant "
                  "turned backs, two giant closed doors far apart at the left and right edges. A flock of crows wheels. "
                  f"{STORM}. {STYLE}"),
    "c2b_beside": (("00_child_px", "00_friend_px"),
                   f"On the stormy wet plain: {FRIEND}, has stepped in and stands shoulder to shoulder beside {CHILD}, "
                   "both facing the same wind, not touching, not talking. Around the girl the mist clears into a small "
                   "warm pocket of light, reflected on the wet ground. Both look up: in the dark cloud ceiling above "
                   f"them, a first thin tear with paler sky behind it. {STORM}, except her amber coat and the warm "
                   f"pocket. {STYLE}"),

    # --- the hill ---
    "br_a_birds": (("00_child_px", "00_friend_px"),
                   f"On {HILL}, under a dark cloud ceiling close overhead, in strong wind: {CHILD}, stands with arms "
                   "opened, and the torn pieces of a child's crayon drawing lift from the hands one after another, "
                   "climb, and unfold into small paper birds that sail up toward a pale tear in the cloud. "
                   f"{FRIEND}, stands a few steps behind, watching. {BREAK}. {STYLE}"),
    "br_b_rain": (("00_child_px", "00_friend_px"),
                  f"On {HILL}: the dark cloud is raining, and low sun under the cloud's edge lights every raindrop "
                  f"amber-gold. Where the rain falls the grey grass turns green in patches. {CHILD}, lifts the face into "
                  f"the rain with eyes closed; {FRIEND}, holds out an open palm to catch drops. {LIGHT}. {STYLE}"),
    "br_c_hands": (("00_child_px", "00_friend_px"),
                   "A close two-shot from the waist up in light golden rain: the girl in the amber-yellow raincoat holds "
                   "out her open hand, and the child in the dark navy hoodie, hesitant, is just taking it; their faces "
                   f"in profile toward each other, hers gentle, the child's uncertain. {LIGHT}. {STYLE}"),
    "bd_push": (("00_child_px", "00_friend_px"),
                f"A wide, nearly monochrome shot of {HILL}: a heavy dark haze of cloud fills the whole top of the frame, "
                f"very low. {FRIEND}, small, on tiptoe, shoves upward at the cloud with both arms; where she pushed, "
                "ragged holes have opened and shafts of golden sun fall through them onto the grass. "
                f"{CHILD}, watches from a few steps away, one foot stepping into a shaft. {BREAK}. {STYLE}"),
    "hush2_shafts": (("00_child_px", "00_friend_px"),
                     f"A still, silent wide shot of {HILL}: the two children stand side by side in golden shafts of sun "
                     "that fall through several ragged holes in a dark cloud ceiling; pollen drifts in the light; "
                     f"the grass in the shafts is green, the rest grey. {BREAK}. {STYLE}"),
    "c3a_tear": (("00_child_px", "00_friend_px"),
                 f"The same hilltop a moment later: the dark cloud ceiling has torn wide open along the holes and a "
                 "flood of sunlight pours through the long ragged gap, towering bright cloud edges on both sides. A "
                 "flock of crows lifts off and scatters outward, turning into ordinary small birds. The two children "
                 f"walk forward together to the right, toward the light, the child's stride longer. {LIGHT}. {STYLE}"),
    "c3a_cutouts": (("00_child_px", "00_friend_px"),
                    f"A sunlit grassy path on a hill: the two children walk past small knee-high paper cut-outs standing "
                    "beside the path like stage props: two faceless heads whispering, a ring of little turned backs, "
                    "two small doors far apart. The cut-outs are tipping over flat onto the grass as the children "
                    f"pass. {LIGHT}. {STYLE}"),
    "c3b_smile": (("00_child_px", "00_friend_px"),
                  f"A medium close shot on a hill in soft light: {FRIEND}, turns toward the child with a warm open smile; "
                  f"{CHILD}, looks at her. Small flowers are opening in the grass at their feet. Colours still pale and "
                  f"partly grey. {LIGHT}. {STYLE}"),
    "c3b_colour": (("00_child_px", "00_friend_px"),
                   f"A wide shot of {HILL}: a ring of full colour is spreading outward from between the two children, who "
                   "stand together in the middle. Inside the ring: a brilliant blue-to-peach sky with towering white "
                   "cumulus, vivid green grass full of flowers, the child's hoodie deep teal, and the child smiling a "
                   "little for the first time. Outside the ring's soft edge the world is still grey-blue. "
                   f"{COLOUR} inside the ring. {STYLE}"),
    "out_ridge": (("00_child_px", "00_friend_px"),
                  f"A wide travelling shot along a flowering green ridge in full colour under a huge blue sky with "
                  f"towering white cumulus: {CHILD}, in a deep teal hoodie, walks holding a thin string, and at the end "
                  "of the string one small pale-grey cloud follows above like a balloon. Beside the child the girl in "
                  f"the amber-yellow raincoat flies a red kite. Small birds and paper birds overhead. {COLOUR}, turning "
                  f"golden toward the horizon. {STYLE}"),
    # --- second round: the same sets seen again (the last reference is the place to keep) ---
    "v1a": (("00_child_px", "intro"),
            f"A closer view inside the same living room as the attached wide picture, at night: the left part of the "
            f"room, the sofa against the wall under the torn family drawing. {CHILD}, curled deep in the sofa corner "
            "hugging a cushion, eyes half closed, large in the frame (about half the picture's height). The underside of "
            "the heavy dark cloud almost touches the hair. A cold flickering television light from off-screen at the "
            "right throws the child's shadow on the wall beside the sofa, and that shadow stands tall as a caped film "
            f"hero with fists on the hips. {COLD}. {STYLE}"),
    "v1b_crows": (("00_child_px", "intro"),
                  f"Inside the same living room as the attached wide picture, at night, a closer view of its tall window "
                  f"with the long curtains: {CHILD}, seen from behind, stands at the window, about a third of the "
                  "picture's height. Outside in the rain, on a wire under the edge of the roof eave, a dense uneven row "
                  f"of black crows, two of them landing with wings flared; apartment blocks behind. {COLD}. {STYLE}"),
    "inter_phone": (("00_child_px", "inter"),
                    "A closer view in the same room as the attached picture, late afternoon: the child sits on the floor "
                    "under the window with the back to the wall and knees up, looking down at a phone that has just lit "
                    "up in both hands, its cold light on the face; the tiny amber light glows on the window sill above. "
                    f"{COLD_AMBER}, with a rose warmth in the window. {STYLE}"),
    "v2a_phone": (("00_child_px", "inter"),
                  "The same room as in the attached picture, at sunset: a huge persimmon-orange sun fills its window and "
                  f"throws one long orange shaft of light across the floor. {CHILD}, sits on the floor at the edge of "
                  "the shaft looking down at a phone held in both hands, the phone's cold light on the face; the child's "
                  "long shadow lies alone across the floor. The grey cloud presses low under the ceiling. Three empty "
                  f"chairs at the table. {DUSK}. {STYLE}"),
    "v2a_windows": (("00_child_px", "inter"),
                    "Dusk in the same room as the attached picture, seen from behind the child, who sits on the floor in "
                    "the lower left as a small dark shape looking out through the same window: in the apartment block "
                    "opposite, warm windows have lit up one after another, and in each lit window the tiny silhouettes "
                    "of a family at a table. Inside this room, the table with its three empty chairs in shadow. "
                    f"{DUSK}. {STYLE}"),
    "coda_ring": (("00_child_px", "coda_sofa"),
                  "A closer view in the same warm sunset room as the attached picture: the child in the deep teal hoodie "
                  "lies curled in the sofa corner, and on the cushion beside the child a phone has lit up warm and is "
                  "ringing, small ripples of warm light around it; the child's head is lifting to look at it. The small "
                  f"pale-grey cloud bobs above on its thin string. {GOLD}. {STYLE}"),
    "p1b_sink": (("00_child_px", "p1b_pieces"),
                 "The same scene as the attached picture a moment later: the torn pieces of the crayon drawing have "
                 "slipped from the child's hands and are sinking down through the mist; the child's arms have dropped and "
                 f"the head is bowed; everything is darker, the light dimming toward deep ink blue. {COLD}, the pieces "
                 f"barely tinted. {STYLE}"),
    "c1a_mid": (("00_child_px", "c1a_wide"),
                f"The same rain-wet plain as in the attached picture, seen closer: {CHILD}, seen from behind, the whole "
                "figure about half the picture's height, stands on the wet ground in the mist under the enormous dark "
                f"cloud, about to walk away from us; a long reflection on the ground. {COLD}. {STYLE}"),
    "c1b_mote": (("00_child_px", "c1a_wide"),
                 f"A close shot in the mist of the plain in the attached picture: {CHILD}, looks down at one small amber "
                 "firefly light resting in the open palm; its warm glow on the face and in the eyes, which are a little "
                 "wider than before. Behind the child only mist, rain and the wet plain: no buildings, no gates, no "
                 f"trees. {COLD_AMBER}. {STYLE}"),
    "p2a_lamp": (("00_child_px", "p1a_lamp"),
                 "The same street lamp and wet street as in the attached picture: the child walks past under the lamp, "
                 "mid-step, slumped, seen from the side walking to the right; a grey moth circles the lamp and one tiny "
                 "amber firefly light circles with it; the child's reflection in the puddle; the small dark cloud "
                 f"follows above the child. {COLD_AMBER}. {STYLE}"),
    "p2b_swirl": (("00_child_px", "p2b_armful"),
                  "The same place as the attached picture a little earlier: many torn pieces of the crayon drawing swirl "
                  "in the wind around the child, who is gathering them out of the air with both hands, a few already "
                  "held against the chest. Far behind in the mist, the faint table with three empty chairs. "
                  f"{STORM}, with the crayon pieces as faint colour. {STYLE}"),
    "c2a_lean": (("00_child_px", "c1a_wide"),
                 "The same plain as in the attached picture, now in a storm, seen closer and from the side: the child "
                 "leans forward into hard wind and rain, hugging torn paper pieces to the chest, hair and hoodie whipped "
                 "back, about half the picture's height; the cloud is lower and churning; a flock of crows wheels. "
                 f"{STORM}. {STYLE}"),
    "c2b_up": (("00_child_px", "00_friend_px", "c2b_beside"),
               "The same two children in the same place as the attached picture, seen from behind and below as they both "
               "look up: the lower third of the picture shows their heads and shoulders from behind, side by side; the "
               "rest is the dark churning cloud ceiling, in which a first thin ragged tear shows paler sky. No sun yet. "
               f"{STORM}, except her amber coat. {STYLE}"),
    "br_a_sky": (("br_a_birds",),
                 "A view up into the sky of the attached picture, no people: small paper birds folded from the pieces of "
                 "a child's crayon drawing sail upward in a loose line toward a pale tear in the dark cloud ceiling, "
                 f"golden light along the tear's edges. {BREAK}. {STYLE}"),
    "br_a_keep": (("00_child_px", "00_friend_px", "br_a_birds"),
                  "The same hilltop as in the attached picture, closer: the child holds the last torn piece of the crayon "
                  "drawing, the piece with one small figure on it, in both hands against the chest and looks down at "
                  "it, about to tuck it into the hoodie pocket; the girl stands a step behind, watching gently; wind in "
                  f"their hair; paper birds far up in the sky. {BREAK}. {STYLE}"),
    "br_b_face": (("00_child_px", "br_b_rain"),
                  "A close shot in the golden rain of the attached picture: the child's face lifted into the rain, eyes "
                  "closed, calm, the raindrops lit amber-gold, a first hint of ease in the face; the sunset glow under "
                  f"the cloud's edge behind. {LIGHT}. {STYLE}"),
    "bd_haze": (("00_child_px", "00_friend_px", "bd_push"),
                "The same hilltop as in the attached picture a little earlier: the heavy dark haze of cloud is "
                "completely closed and very low, no holes, no shafts of light, everything dim blue-grey; the girl in the "
                "amber raincoat stands on tiptoe reaching both arms up toward the cloud; the child stands a few steps "
                f"away watching, head low. Only the raincoat has colour. {STYLE}"),
    "bd_push1": (("00_child_px", "00_friend_px", "bd_push"),
                 "The same hilltop as in the attached picture, earlier: only one small ragged hole has opened in the "
                 "dark cloud, right above the girl's hands, and a single shaft of golden sun falls through it; she is "
                 f"jumping with both arms thrown up at the cloud; the child watches from a few steps away. {BREAK}. {STYLE}"),
    "bd_step": (("00_child_px", "bd_push"),
                "A close view on the same hilltop as in the attached picture: the child steps into one golden shaft of "
                "sunlight, the light on the face and the hoodie, looking up into it with narrowed eyes; one sneaker in "
                f"lit green grass, the other still in grey grass. {BREAK}. {STYLE}"),
    "c3a_walk": (("00_child_px", "00_friend_px", "c3a_tear"),
                 "The same hill and torn-open sky as in the attached picture, a closer side view: the two children walk "
                 "together to the right through flooding sunlight, the girl half a step ahead, the child's stride "
                 f"longer and the head up; small birds overhead; wet grass glittering. {LIGHT}. {STYLE}"),
    "c3a_fallen": (("00_child_px", "00_friend_px", "c3a_cutouts"),
                   "The same path as in the attached picture a moment later: the two children have walked on and are "
                   "seen from behind near the right edge; behind them all the little paper cut-outs lie flat on the "
                   f"grass, tipped over. {LIGHT}. {STYLE}"),
    "c3b_full": (("00_child_px", "00_friend_px", "c3b_colour"),
                 "The same hilltop and the same two children as in the attached picture, but now the whole world is in "
                 "full colour from edge to edge, with no ring and no grey anywhere: a brilliant blue-to-peach sky with "
                 "towering white cumulus, vivid green grass full of flowers, far hills, the child's hoodie deep teal, "
                 f"and the child smiling a little. {COLOUR}. {STYLE}"),
    "c3b_sky": (("c3b_colour",),
                "A view up into a brilliant blue sky with towering white cumulus clouds and soft shafts of sun, in which "
                "many small paper birds and a few real birds fly together; the green flowering top of a hill just shows "
                f"along the bottom edge. No people. {COLOUR}. {STYLE}"),
    "out_kite": (("00_child_px", "00_friend_px", "out_ridge"),
                 "The same ridge as in the attached picture, closer: the girl flies a red kite, laughing and looking up; "
                 "beside her the child in the deep teal hoodie holds the thin string of the small pale-grey cloud like a "
                 f"balloon and looks at the kite with a small smile. {COLOUR}. {STYLE}"),
    "out_gold": (("00_child_px", "00_friend_px", "out_ridge"),
                 "The same ridge as in the attached picture at golden evening: the two children, seen from behind, walk "
                 "away along the ridge toward a low golden sun, long shadows behind them, the small pale cloud on its "
                 f"string following above the child, the kite high in the sky. {GOLD}. {STYLE}"),
    # --- third round: more shots ---
    "p1a_walk": (("00_child_px", "p1a_lamp"),
                 "The same wet street as in the attached picture, a little further along, a wider side view: the child "
                 "walks slowly to the right with small slumped steps, mid-stride, the street lamp now behind at the left "
                 "edge; the small dark cloud follows above the child; the child's reflection on the wet pavement; far "
                 f"apartment blocks with a few lit windows. {COLD}. {STYLE}"),
    "v2b_whisper": (("00_child_px", "v2b_ring"),
                    "A closer view of the scene in the attached picture: in the foreground two faceless grey pupils, seen "
                    "from behind, lean together, one with a hand cupped at the mouth beside the other's ear, and a thin "
                    "dark scribble of thread passes between them; beyond them, in the middle distance, the child sits "
                    "cross-legged on the row of desks with eyes closed, calm; a paper plane drifts past. "
                    f"{COLD}. {STYLE}"),
    "inter_sill": (("00_child_px", "inter"),
                   "A close view in the same room as the attached picture, late afternoon: the window sill with one tiny "
                   "amber firefly light resting on it, glowing steadily; below the sill, the top of the child's head and "
                   "messy hair as the child sits against the wall, the face tilted a little up toward the light; beyond "
                   f"the glass the rose-tinted sunset sky and apartment blocks. {COLD_AMBER}, with a rose warmth in the "
                   f"window. {STYLE}"),
    "c1b_calm": (("00_child_px", "c1a_wide"),
                 "The same plain as in the attached picture, calmer: the rain has thinned to a drizzle and the mist lies "
                 "low; the child stands small in the middle, solid and clear, head bowed toward a tiny amber light held "
                 "in both hands, its glow on the wet ground around; far behind, the towering shapes of two whispering "
                 "heads, a ring of turned backs and two doors have sunk low and faint into the mist, still there. "
                 f"{COLD_AMBER}. {STYLE}"),
    "out_cloud": (("00_child_px", "00_friend_px", "out_ridge"),
                  "The same ridge as in the attached picture, a closer low view: the child looks up at the small "
                  "pale-grey cloud that floats just above on its thin string, held in the child's hand like a balloon, "
                  "with a calm small smile; the girl beside the child looks up at it too; towering white cumulus and "
                  f"blue sky behind. The child's hoodie is dark navy. {COLOUR}. {STYLE}"),
    "c3b_full": (("00_child_px", "00_friend_px", "c3b_colour"),
                 "The same hilltop and the same two children as in the attached picture, but now the whole world is in "
                 "full colour from edge to edge, with no ring and no grey anywhere: a brilliant blue-to-peach sky with "
                 "towering white cumulus, vivid green grass full of flowers, far hills; the child still wears the same "
                 f"dark navy hoodie and is smiling a little. {COLOUR}. {STYLE}"),
}

# edits: (reference id, change): one existing picture repainted with one thing changed
PAIRS = {
    "x_colour_before": ("c3b_colour", "Repaint the attached picture exactly, same composition, same children, same "
                        "hill and clouds, but one moment earlier: no ring yet, the whole world still pale grey-blue "
                        "and nearly colourless; only the girl's amber-yellow raincoat has colour. No text."),
    "x_tear_before": ("c3a_tear", "Repaint the attached picture exactly, same composition and same hill, but one "
                      "moment earlier: the dark cloud ceiling is still closed except for a few ragged holes with "
                      "golden shafts of sun falling through them; the two children stand still side by side; the "
                      "crows still sit in a row. No text."),
    "v1a_plain": ("v1a", "Repaint the attached picture exactly, same composition, same room, same child on the sofa, "
                  "same colours, but the tall caped hero shadow on the wall is gone: on the wall there is only the "
                  "small soft shadow of the curled child. No text."),
    "c3a_walk_b": ("c3a_walk", "Repaint the attached picture exactly, pixel for pixel the same background, the same "
                   "sky, clouds, birds, hills, grass, puddles and light, nothing moved. The only change is the walking "
                   "pose of the two children: this is the passing moment of the same walk, between two strides. Each "
                   "child now stands tall on one straight leg directly under the body, with the other foot lifted "
                   "just off the ground beside it, knees close together, and both arms hanging close to the body. "
                   "Their heads, faces, hair and clothes stay exactly as they are, and each child stays in exactly "
                   "the same place in the picture. No text."),
    "c1b_mote_k": ("c1b_mote", "Repaint the attached picture exactly, pixel for pixel the same, nothing moved. The only "
                   "change: the child's eyes are closed, as in the middle of a blink (two soft dark curved lines where "
                   "the eyes were). No text."),
    "br_c_offer": ("br_c_hands", "Repaint the attached picture exactly, same composition, same two children, same "
                   "light, but one moment earlier: the girl's open hand is held out, and the child's hand is still "
                   "drawn back near the chest, hesitating; a clear gap between the two hands. No text."),
}


SAME = ("Repaint the attached picture exactly, pixel for pixel the same background, light and colours, nothing "
        "moved and nothing added. ")


def _passing(who: str) -> str:
    return (SAME + f"The only change is the walking pose of {who}: this is the passing moment of the same walk, between "
            "two strides: standing tall on one straight leg directly under the body with the other foot lifted just off "
            "the ground beside it, knees close together, arms close to the body. Heads, faces, hair, clothes and "
            "anything carried or held stay exactly as they are, each figure stays in exactly the same place in the "
            "picture, and any reflection on the ground changes to match. No text.")


def _blink(who: str) -> str:
    return (SAME + f"The only change: the eyes of {who} are closed, as in the middle of a blink (a soft dark curved "
            "line where each eye was). No text.")


PAIRS.update({
    # the passing pose of a walk (shown on the off-beat)
    "p1a_walk_b": ("p1a_walk", _passing("the child")),
    "p2a_houses_b": ("p2a_houses", _passing("the child")),
    "p2a_lamp_b": ("p2a_lamp", _passing("the child")),
    "c1a_mid_b": ("c1a_mid", _passing("the child, who is seen from behind")),
    "c2a_lean_b": ("c2a_lean", SAME + "The only change is in the child's legs: the back foot has come forward so that "
                   "both feet are close together under the body, in the middle of a step; the child still leans "
                   "forward into the wind hugging the paper pieces, in exactly the same place. No text."),
    "c2a_storm_b": ("c2a_storm", SAME + "The only change is in the child's legs: the back foot has come forward so "
                    "that both feet are close together under the body, in the middle of a step; the child still "
                    "leans forward into the wind, in exactly the same place. No text."),
    "c3a_tear_s_b": ("c3a_tear_s", _passing("the two children")),
    "c3a_cutouts_b": ("c3a_cutouts", _passing("the two children")),
    "c3a_fallen_b": ("c3a_fallen", _passing("the two children, who are seen from behind")),
    "out_ridge_b": ("out_ridge", _passing("the two children")),
    "out_kite_b": ("out_kite", _passing("the two children")),
    "out_gold_b": ("out_gold", _passing("the two children, who are seen from behind")),
    "v2b_path_b": ("v2b_path", SAME + "The only change: every hurrying pupil is caught at the passing moment of the "
                   "stride, legs together under the body, instead of the open stride. The child standing still in the "
                   "middle does not change at all. No text."),
    "p1a_street_b": ("p1a_street", SAME + "The only change: each walking passer-by is caught at the passing moment of "
                     "the stride, legs together under the body, instead of the open stride. The child standing in the "
                     "middle does not change at all. No text."),
    "p1b_table_b": ("p1b_table", SAME + "The only change: the two adult silhouettes walking away are each caught at "
                    "the passing moment of the stride, legs together under the body. The child and the table do not "
                    "change at all. No text."),
    # the other half of a wingbeat
    **{f"{k}_f": (k, SAME + "The only change: every bird in the picture, paper birds and real birds alike, is at "
                  "the opposite moment of its wingbeat: wings that were raised are now lowered and wings that were "
                  "lowered are now raised. Each bird stays in exactly the same place and keeps its size and colour. "
                  "No text.") for k in ("br_a_birds", "br_a_sky", "c3a_tear_s", "c3a_walk", "c3b_sky")},
    # blinks and looks
    "v1a_k": ("v1a", SAME + "The only change: the child's eyes are open a little wider and look up and to the right, "
              "toward the tall shadow on the wall. No text."),
    "p1a_street_k": ("p1a_street", _blink("the child")),
    "p1a_lamp_k": ("p1a_lamp", _blink("the child")),
    "inter_phone_k": ("inter_phone", _blink("the child")),
    "p2b_armful_k": ("p2b_armful", _blink("the child")),
    "br_a_keep_k": ("br_a_keep", _blink("the child")),
    "br_c_offer_k": ("br_c_offer", _blink("the child in the dark hoodie")),
    "br_c_hands_k": ("br_c_hands", _blink("the girl in the yellow raincoat")),
    "c3b_smile_k": ("c3b_smile", _blink("the child in the dark hoodie")),
    "out_cloud_k": ("out_cloud", _blink("the child")),
    "coda_call_k": ("coda_call", _blink("the child")),
    # the friend gathering herself between shoves
    "bd_push1_b": ("bd_push1", SAME + "The only change: the girl in the yellow raincoat has landed and crouches a "
                   "little with knees bent and both arms pulled down beside her, gathering herself to jump again. "
                   "No text."),
    "bd_push_b": ("bd_push", SAME + "The only change: the girl in the yellow raincoat has dropped back onto her heels "
                  "with knees bent and both arms pulled down beside her, gathering herself to push up again. No text."),
    # earlier states of a picture (the film dissolves from them to the picture)
    "c3a_tear_s": ("c3a_tear", SAME + "The only change: the two walking children have swapped places. The child in "
                   "the dark hoodie now walks on the left, behind, and the girl in the yellow raincoat now walks on "
                   "the right, half a step ahead of the child; both still walk toward the right. No text."),
    "v1b_crows_a": ("v1b_crows", SAME + "The only change: most of the crows are gone; only three crows sit on the wire, "
                    "far apart, and none is flying. No text."),
    "v1b_door_b": ("v1b_door", SAME + "The only change: in the strip of light under the door only one pair of feet is "
                   "left, the other pair has gone, and the strip of light is half as bright. No text."),
    "v2a_windows_a": ("v2a_windows", SAME + "The only change: in the apartment block opposite only two windows are "
                      "lit; all the other windows are dark. No text."),
})


def _role(ref: str) -> str:
    if ref.startswith("00_child"):
        return "the child's character sheet (keep the face, hair, clothes, colours and childlike big-headed proportions exactly)"
    if ref.startswith("00_friend"):
        return "the girl's character sheet (keep her face, bob, clip, raincoat and proportions exactly)"
    return ("an earlier picture of this same place (keep its layout, its objects, its light, its colours and its "
            "pixel style; the new picture shows the same place)")


def _prompt(key: str) -> tuple[list[str], str]:
    if key in PAIRS:
        ref, change = PAIRS[key]
        return [ref], ("Use your built-in image generation tool exactly once to create one 16:9 landscape image, then "
                       "reply with only the word done. Do not run shell commands and do not read or write files. "
                       + change)
    refs, picture = PLAN[key]
    lead = "".join(f"Attached image {i + 1} is {_role(r)}. " for i, r in enumerate(refs))
    return list(refs), ("Use your built-in image generation tool exactly once to create one 16:9 landscape image, then "
                        "reply with only the word done. Do not run shell commands and do not read or write files. "
                        + lead + "Image: " + picture)


def generate(key: str, force: bool = False) -> str:
    out = OUT / f"{key}.png"
    if out.exists() and not force:
        return f"{key}: kept"
    refs, prompt = _prompt(key)
    cmd = ["codex", "exec", "-m", MODEL, "-c", f"model_reasoning_effort={EFFORT}", "-s", "read-only",
           "--skip-git-repo-check", "--ephemeral", "--json"]
    for r in refs:
        p = OUT / f"{r}.png"
        if not p.exists():
            return f"{key}: missing reference {r}"
        cmd += ["-i", str(p)]
    cmd += ["--", prompt]
    with tempfile.TemporaryDirectory() as cwd:
        res = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=900)
    thread = None
    for line in res.stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "thread.started":
            thread = ev.get("thread_id")
    (OUT / "_log").mkdir(parents=True, exist_ok=True)
    (OUT / "_log" / f"{key}.jsonl").write_text(res.stdout[-20000:])
    files = sorted((HOME_IMAGES / thread).glob("*.png")) if thread else []
    if not files:
        return f"{key}: no image (exit {res.returncode}) {res.stderr[-300:]}"
    Image.open(files[-1]).convert("RGB").save(out)
    return f"{key}: ok"


def sheets(cols: int = 4, tile: int = 480) -> None:
    files = sorted(p for p in OUT.glob("*.png"))
    (OUT / "_sheets").mkdir(exist_ok=True)
    per = cols * 4
    for s in range(math.ceil(len(files) / per)):
        part = files[s * per:(s + 1) * per]
        th = tile * 9 // 16
        rows = math.ceil(len(part) / cols)
        sheet = Image.new("RGB", (cols * tile, rows * th), (0, 0, 0))
        d = ImageDraw.Draw(sheet)
        for i, p in enumerate(part):
            im = Image.open(p).resize((tile, th))
            x, y = (i % cols) * tile, (i // cols) * th
            sheet.paste(im, (x, y))
            d.rectangle((x, y, x + 8 * len(p.stem) + 8, y + 14), fill=(0, 0, 0))
            d.text((x + 4, y + 1), p.stem, fill=(255, 255, 255))
        sheet.save(OUT / "_sheets" / f"sheet_{s}.jpg", quality=85)
        print(OUT / "_sheets" / f"sheet_{s}.jpg", len(part))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    if a.sheet:
        sheets()
        return
    keys = [k for k in a.only.split(",") if k] or list(PLAN) + list(PAIRS)
    # references first: sheets, then pictures, then pairs
    waves = [[k for k in keys if k.startswith("00_")], [k for k in keys if k in PLAN and not k.startswith("00_")],
             [k for k in keys if k in PAIRS]]
    for wave in waves:
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda k: generate(k, a.force), wave):
                print(msg, flush=True)


if __name__ == "__main__":
    main()
