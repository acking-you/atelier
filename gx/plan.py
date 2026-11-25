"""The anime dream film (look: Makoto Shinkai's Weathering with You): references and shots, addressed on the recording's clock.

The story is hx/DESIGN.md's, told as the inner dream world of one boy, drawn as a Japanese
animated feature: strange, luminous, phantasmagoric. His gloom is a colossal dark cloud in the
shape of a whale that lies over the whole city; his room stands in ankle-deep still water; the
crows are giant with white lamp eyes; the remarks, postures and hurts are giant eyes, floating
mouths and pointing hands in the sky. A girl in an amber raincoat comes through a door that
stands alone on the water and stays. Light returns in steps, colour last, and the gloom is still
there at the end, small: a tiny cloud-whale on a string.
Shot boundaries sit on the recording's bar lines and line stamps (hx/data/timeline.json).
Prompts are our own descriptions of pictures; no lyric text appears here.

Clips come back at 24 fps and are played at 30 fps (1.25x, no frame is dropped or doubled), so a
slot of d seconds uses 1.25 d seconds of generated footage.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

SPEED = 1.25

BOY = ("a nine-year-old boy with messy black hair falling over his forehead, large tired dark eyes with faint shadows "
       "under them, pale skin, wearing an oversized charcoal-black hoodie, dark trousers and worn white sneakers")
GIRL = ("a nine-year-old girl with a chin-length dark brown bob and a small red hair clip, bright warm eyes, wearing a "
        "bright amber-yellow raincoat with the hood down, dark leggings and cream rain boots")

BASE = ("Japanese anime feature film in the visual style of Makoto Shinkai's Weathering with You: breathtaking, "
        "hyper-detailed luminous painted backgrounds, dramatic skies with towering cumulonimbus clouds, glittering rain "
        "and wet reflective surfaces, shafts of sunlight and soft lens flares, rich saturated blues with warm highlights, "
        "clean modern anime character designs with fine line art and soft cel shading, cinematic depth of field, a "
        "surreal dreamlike atmosphere. 2D anime, not photorealistic live action, not 3D. No text, no captions, no watermark.")
TONES = {
    "grey": "Muted cold blue-grey and indigo palette, drifting mist, dim soft light, a heavy quiet mood.",
    "dusk": "Muted palette with a deep orange sunset glow through haze, long shadows, a lonely stillness.",
    "storm": "Dark indigo and steel-blue palette, violent wind, churning cloud, hard dramatic contrast.",
    "break": "Still mostly dark blue-grey, with a few warm golden shafts of sunlight cutting down through the cloud.",
    "light": "Brightening light, soft colour beginning to return, pale gold sun through thinning cloud.",
    "colour": "Full vivid saturated colour, clear warm sunlight, a brilliant blue sky with towering white clouds.",
    "gold": "Warm golden-hour light, rich colour, long soft shadows, gentle glow.",
}
REF_ROLE = {
    "boy": "the boy's character sheet (keep his face, hair, hoodie and proportions exactly as in it: a small "
           "nine-year-old child with a round childlike face, never a teenager)",
    "girl": "the girl's character sheet (keep her face, bob, red clip and amber raincoat exactly as in it)",
    "room": "the dream room (keep its layout, the sofa, the window and the still water on the floor)",
    "sea": "the mirror sea under the cloud-whale (keep its endless shallow water, the mist and the whale-shaped cloud)",
    "hill": "the grass hill island above the sea of clouds (keep its soft rounded slope and the cloud-whale overhead)",
    "school": "the dream school of floating desks (keep the row of desks low over the sea of paper)",
}

REF_CLEAR = {
    "sea": "the mirror sea (keep its endless shallow water; the dark whale-shaped cloud is gone now and the sky above "
           "it is open and bright)",
    "hill": "the grass hill island above the sea of clouds (keep its soft rounded slope; the dark whale-shaped cloud "
            "is gone now and the sky above it is open and bright)",
}
PREV = "the previous shot of this same scene (keep the same place, the same light and the same things in it)"

WHALE = "a colossal dark storm cloud in the unmistakable shape of a whale"
REFS = {
    "boy": {"prompt": f"Anime character model sheet on a plain pale-grey background: {BOY}, drawn full body four times side by "
                      "side in the same neutral standing pose: front view, three-quarter view, side profile, back view. "
                      "Slightly slumped shoulders, quiet withdrawn expression. Clean line art, flat cel shading, consistent "
                      "face and clothes in every view. Modern Japanese anime feature-film character design in the style of Makoto Shinkai's films: fine "
                      "clean line art, soft cel shading, natural proportions, expressive eyes. No text."},
    "girl": {"prompt": f"Anime character model sheet on a plain pale-grey background: {GIRL}, drawn full body four times side "
                       "by side in the same relaxed standing pose: front view, three-quarter view, side profile, back view. "
                       "Warm, calm, kind expression. Clean line art, flat cel shading, consistent face and clothes in every "
                       "view. Modern Japanese anime feature-film character design in the style of Makoto Shinkai's films: fine "
                      "clean line art, soft cel shading, natural proportions, expressive eyes. No text."},
    "room": {"prompt": "Wide view of a small living room at night in a dream: the floor is covered by ankle-deep, perfectly "
                       "still dark water that mirrors everything; a worn dark-green sofa with one cushion stands in it like "
                       "an island against the left wall; a low table, a floor lamp that is off, a jacket on a hook; on the "
                       "right a large window with a curtain, and outside it a night city of leaning towers under " + WHALE +
                       "; a low dark cloud hangs under the room's own ceiling. Empty of people. " + BASE + " " + TONES["grey"]},
    "sea": {"prompt": "Extreme wide dreamscape: an endless mirror-flat shallow sea only ankle deep, stretching to a misty "
                      "horizon, a few crooked lamp posts and a lone dead tree standing in the water, and filling the whole "
                      "sky above it " + WHALE + ", its vast belly hanging low, slowly swimming. Empty of people. "
                      + BASE + " " + TONES["grey"]},
    "hill": {"prompt": "A gentle rounded grass hill rising like an island out of a sea of clouds, seen from its slope: dry "
                       "grey-green grass bending in wind, far below the tops of crooked dream-city towers poking through "
                       "the cloud sea, and close overhead the huge dark belly of " + WHALE + ". No cliff, no edge: soft "
                       "slopes all around. Empty of people. " + BASE + " " + TONES["grey"]},
    "school": {"prompt": "A dream school: a long single row of wooden school desks set end to end, floating knee-high above a "
                         "calm sea made of loose white exam papers that stretches into mist; pale windows hang in the air "
                         "with no walls, paper lamps float overhead. Empty of people. " + BASE + " " + TONES["grey"]},
}


@dataclass(frozen=True)
class Shot:
    id: str
    t0: float
    t1: float
    tone: str
    refs: tuple          # reference images used to stage the first frame, in order
    frame: str           # the staged first frame ("" = no picture: black)
    motion: str          # what happens in the clip
    fade_in: float = 0.0       # from black
    fade_out: float = 0.0      # to black (or to `fade_to`)
    fade_to: str = "black"
    dissolve: float = 0.0      # seconds of dissolve INTO this shot from the previous one
    tail: float = 0.0          # seconds this shot keeps running under the next shot's dissolve

    @property
    def clear(self) -> bool:      # after the cloud breaks the references' dark whale is gone
        return self.t0 >= 204.0 and self.t1 <= 244.6

    @property
    def dur(self) -> float:
        return self.t1 - self.t0

    @property
    def use_seconds(self) -> float:
        return self.dur * SPEED

    @property
    def gen_seconds(self) -> int:
        return max(2, min(15, math.ceil((self.dur + self.tail) * SPEED + 0.2)))


def look(shot: Shot) -> str:
    def role(r):
        if r.startswith("@"):
            return PREV
        return REF_CLEAR[r] if shot.clear and r in REF_CLEAR else REF_ROLE[r]
    roles = "; ".join(f"reference image {i + 1} is {role(r)}" for i, r in enumerate(shot.refs))
    return (f"({roles}.) " if roles else "") + BASE + " " + TONES[shot.tone]


B, G = "the boy", "the girl"
S = Shot
SHOTS = [
    # ---- intro (solo piano) ----------------------------------------------------------------
    S("S01", 0.0, 6.265, "grey", (),
      "A night dream-city of crooked, leaning towers with thousands of dim windows, and lying over all of it " + WHALE +
      ", vast, its belly brushing the rooftops; thin silver threads of rain rise upward from the streets into the whale's belly "
      "instead of falling; one small window glows in a tower at the centre of the frame.",
      "The cloud-whale drifts slowly over the city, its fins trailing mist; the rain streams upward; the camera glides toward the one lit window.",
      fade_in=2.0),
    S("S02", 6.265, 12.265, "grey", ("room", "boy"),
      "Wide shot of the dream room at night: the boy is a small curled-up shape on the sofa-island, hugging a "
      "cushion; the still water on the floor mirrors him; a small dark cloud hangs under the ceiling and a "
      "slow, fine rain falls from it only inside the room; a framed family photograph of two parents and a "
      "small child hangs slightly crooked on the wall above the sofa, its glass cracked straight down the "
      "middle between the two parents.",
      "Very slow push-in toward the sofa; slow ripples cross the water; the cloud under the ceiling drifts; the "
      "boy breathes and does not move."),
    # ---- verse 1 -----------------------------------------------------------------------------
    S("S03", 12.265, 16.265, "grey", ("room", "boy"),
      f"Medium close shot of {B} curled on the sofa hugging a cushion, hair a mess, bleary half-closed eyes, cold "
      "flickering screen light on his face, the dark water glinting below; raindrops hang motionless in the air around "
      "him like glass beads, each one catching the cold light.",
      "He blinks slowly and pulls the cushion closer; cold screen light flickers on his face; the hanging drops tremble "
      "in the air; ripples slide past."),
    S("S04", 16.265, 24.265, "grey", ("room", "boy"),
      f"The dream room: {B} lies small and curled on the sofa in the foreground, while on the wall behind him his own "
      "shadow has stood up on its own, three times his size, as a proud caped film hero with a billowing cape.",
      "The giant shadow hero on the wall strikes a bold pose and its cape streams as if in wind; the boy only lifts his "
      "eyes toward it; then the shadow sags, shrinks and slides back down into a small curled shape."),
    S("S05", 24.265, 28.265, "grey", (),
      "Seen through a rain-streaked window at night: under the edge of a roof, a dense row of giant black crows with round "
      "glowing white eyes perched shoulder to shoulder on sagging wires, mist and the cloud-whale's belly behind them.",
      "More giant crows land one after another along the wires, crowding the row; white eyes blink out of time; wings "
      "flare and fold."),
    S("S06", 28.265, 36.265, "grey", ("room", "boy"),
      "The boy stands at the large window in profile; from his slightly open mouth a tangle of black ink-thread "
      "is drifting out instead of words, knotting in the air above him; the white-eyed crows watch from "
      "outside; in the wall behind him a frosted-glass door glows, and on it fall the tall shadows of two "
      "grown-ups facing each other, with a small thundercloud and tiny lightning hanging between them.",
      "The black thread keeps spilling from his mouth, tangling into a knot that floats up and dissolves into "
      "the dark cloud under the ceiling; behind the frosted door the two tall shadows gesture at each other and "
      "the little thundercloud flickers; he closes his mouth and lowers his head."),
    # ---- pre-chorus 1 ------------------------------------------------------------------------
    S("S07", 36.265, 39.265, "grey", ("school", "boy"),
      "A dream classroom on the sea of paper: the floating desks are all pushed together in one tight cluster "
      "on the left, where schoolchildren with blank white paper masks for faces lean toward each other, "
      "whispering behind their hands; far apart from them, alone at the centre of the frame, stands one single "
      "desk covered in black scribble, and beside it the boy, head down, backpack on; crumpled paper balls hang "
      "in the air around him. The boy is the only one without a mask: his own face, with eyes, nose and mouth, "
      "is clearly visible.",
      "The masked children whisper and turn their blank faces toward him; crumpled paper balls drift through "
      "the air and bounce softly off his shoulder and his desk; the boy stays perfectly still with his head "
      "down."),
    S("S08", 39.265, 42.265, "grey", ("boy",),
      "The boy stands in exactly the same pose, head down, centre frame, now in a dream street at night where "
      "faceless grown-ups under umbrellas walk past upside down along the sky; above him hangs a lamp like a "
      "small moon with one grey mechanical moth circling it.",
      "The umbrella people drift slowly past overhead; the moon-lamp flickers; the moth circles it with a dull, "
      "clockwork motion; the boy does not move, and his hoodie stays charcoal black."),
    S("S09", 42.265, 48.265, "grey", ("boy",),
      f"Close on {B} under the flickering moon-lamp, lifting his head a little, hands closing on his backpack straps, "
      "shallow water around his shoes, raindrops lifting off the water and rising slowly upward around him.",
      "He takes a breath, tightens his grip on the straps and starts to walk forward slowly through the shallow water, "
      "shoulders still heavy; the camera tracks backward with him."),
    S("S10", 48.265, 52.265, "grey", ("sea", "boy"),
      "The boy walks alone across the mirror sea in mist, small in the frame, seen from the side; around him in "
      "the air drift glowing shards of a broken mirror, some holding warm golden pictures of a happy family of "
      "three (a picnic in the sun, a small hand held by two big hands), others holding cold blue pictures of "
      "the same family (the two parents sitting with their backs to each other, an empty chair at a table).",
      "He walks slowly; the memory shards drift past him from behind, turning slowly in the air so that warm "
      "golden faces flip over to cold blue ones; mist slides across the water."),
    S("S11", 52.265, 56.0, "grey", ("boy",),
      "Close on the small hands of the boy, his face soft and out of focus above them, trying to fit together "
      "two glowing shards of mirror: one warm and golden, showing a mother, a father and a small child laughing "
      "at a sunny picnic, the other cold and blue, showing the same two parents sitting with their backs to "
      "each other; the jagged edges do not fit and a dark gap stays between them.",
      "He presses the warm shard and the cold shard together; they will not join; they crumble into drifting "
      "sand between his fingers and the light goes out.", fade_out=0.6),
    S("H1", 56.0, 58.6, "grey", (), "", ""),
    # ---- chorus 1 ----------------------------------------------------------------------------
    S("S12", 58.6, 60.265, "grey", ("sea", "boy"),
      f"Close behind {B}'s head and shoulders as he faces the endless mirror sea and the whale-cloud filling the sky; "
      "raindrops rise upward past him from the water into the cloud.",
      "Wind tugs his hair and hood; he takes one step forward into the water."),
    S("S13", 60.265, 63.265, "grey", ("sea", "boy"),
      f"Extreme wide shot: {B}, tiny, walking away from us across the endless mirror sea toward the mist, the colossal "
      "cloud-whale hanging over him; the water under his feet mirrors a clear sky full of stars that is not there above.",
      "He walks away into the mist and his figure grows faint and translucent; the whale-cloud sinks lower; sheets of "
      "mist sweep across; the camera rises."),
    S("S14", 63.265, 66.265, "grey", ("sea",),
      "Over the mirror sea the mist fills with dozens of enormous megaphones and loudspeakers hanging in the air on long "
      "tangled cables, all aimed downward and pouring out jagged speech bubbles full of black scribble (no letters); a "
      "tiny child figure far below on the water.",
      "The giant megaphones swing round one after another and bubbles of black scribble pour out, multiplying and drifting down "
      "toward the tiny figure."),
    S("S15", 66.265, 70.7, "grey", ("sea",),
      "Low angle from the water: gigantic eyes open in the dark belly of the cloud-whale and enormous pale hands reach "
      "down out of the clouds, fingers pointing at a tiny child figure walking below; black thorn vines rise out of the "
      "water along his path.",
      "The giant eyes turn to follow him and the pointing hands descend; thorn vines climb out of the water; the tiny "
      "figure keeps walking and fades into the mist."),
    S("S16", 70.7, 75.265, "grey", ("sea", "boy", "girl"),
      f"{B.capitalize()} has stopped on the mirror sea, seen from the front in a medium shot, head half turned back; far "
      f"behind him a single wooden door stands alone on the water, open, warm light inside it, and in the doorway {G}, "
      "small, holds up an amber lantern.",
      "From the lantern a ribbon of small glowing amber fish swims through the mist toward the boy; he slowly turns to "
      "look back; the wind dies down."),
    S("S17", 75.265, 80.5, "grey", ("boy",),
      f"Close-up of {B}'s face in the mist with a warm amber glow on one cheek, eyes lifting; his open hand is raised in "
      "the foreground with one tiny glowing amber fish hovering just above the palm.",
      "The tiny amber fish circles once and settles on his palm, pulsing softly; his tired eyes widen a little; the mist "
      "behind him thins.", tail=1.0),
    # ---- interlude ---------------------------------------------------------------------------
    S("S18", 80.5, 86.0, "dusk", ("room", "boy"),
      f"Late afternoon in the dream room: {B} sits in the shallow water under the window with his back against the wall "
      "and his knees up; the tiny amber fish swims slowly in the air near him; orange light ripples on the walls.",
      "The amber fish swims a slow circle around the boy and comes to rest on the windowsill; light ripples drift over "
      "the walls; very slow push-in.", dissolve=1.0),
    S("S19", 86.0, 91.765, "dusk", (),
      "Through the window: the dream-city of leaning towers at sunset, the haze turning deep orange, the cloud-whale a "
      "dark shape swimming slowly across the low sun, giant crows on the wires in silhouette.",
      "The whale-cloud passes slowly across the sun and the orange light slides over the towers; lights come on in "
      "distant windows."),
    # ---- verse 2 -----------------------------------------------------------------------------
    S("S20", 91.765, 96.265, "dusk", ("room", "boy"),
      f"Close on {B} sitting under the window in orange sunset light, holding a tin-can telephone to his ear; its string "
      "runs out of the window into the sky and hangs slack, tied to nothing.",
      "He listens; nothing comes; the slack string sways in the air outside; he slowly lowers the tin can to his knees."),
    S("S21", 96.265, 103.765, "dusk", ("room", "boy"),
      "Wide shot from behind: the boy small by the window, his long shadow lying alone across the water in the "
      "orange light; outside, the windows of the tower opposite float like warm lanterns; a framed family "
      "photograph of two parents and a small child hangs slightly crooked on the wall above the sofa, its glass "
      "cracked straight down the middle between the two parents.",
      "The windows opposite light up one by one, each a warm little box with silhouettes of families moving "
      "inside; the boy watches without moving; the room slowly darkens."),
    S("S22", 103.765, 109.765, "grey", ("school", "boy"),
      "The long row of floating desks crowded with schoolchildren in uniform with blank white paper masks for "
      "faces, hurrying along it in one direction, shouldering past each other and jostling the boy, exam papers "
      "flying; the boy stands still in the middle of the stream, in the foreground, facing us, gripping his "
      "backpack straps. The boy is the only one without a mask: his own face, with tired dark eyes, nose and "
      "mouth, is clearly drawn and visible.",
      "The masked children push past him along the desks, bumping his shoulders; whoever is shouldered aside "
      "steps down and dissolves into loose sheets of paper; papers swirl; he does not move."),
    S("S23", 109.765, 115.765, "grey", ("school", "boy"),
      f"{B.capitalize()} sits cross-legged on one of the floating desks facing us with his eyes closed and his backpack in "
      "his lap, while the stream of paper-masked children parts around him as blurred shapes.",
      "The stream flows around him in a blur; he breathes slowly with his eyes closed; one loose sheet folds itself into a "
      "paper plane and glides past him."),
    # ---- pre-chorus 2 ------------------------------------------------------------------------
    S("S24", 115.765, 118.765, "grey", ("boy",),
      f"{B.capitalize()} walks, seen from the side, through a dream market street where the stalls sell glowing jellyfish "
      "lanterns and stairs climb in impossible directions; the tiny amber fish swims at his shoulder.",
      "He walks steadily; lantern jellyfish bob past; the amber fish follows at his shoulder."),
    S("S25", 118.765, 121.765, "grey", ("boy",),
      f"{B.capitalize()} passes under the moon-lamp where the grey clockwork moth circles; the tiny amber fish has swum "
      "up beside the moth.",
      "The moth and the amber fish circle the moon-lamp together; the boy glances up at them as he passes."),
    S("S26", 121.765, 127.765, "grey", ("boy",),
      f"{B.capitalize()} stands on tiptoe reaching up with one arm, his fingertips touching the low dark belly of the "
      "cloud-whale, which dents and ripples like water where he touches it.",
      "He stretches and pushes his hand into the cloud; rings ripple out across its belly and a thin beam of paler light "
      "leaks through onto his face; he squints up at it."),
    S("S27", 127.765, 133.765, "grey", ("boy",),
      "A dream playground of old swings standing in shallow water; glowing shards of mirror, warm golden ones "
      "holding happy family pictures and cold blue ones holding lonely ones, swirl in the air around the boy, "
      "who is reaching out to catch them.",
      "The wind rises and the glowing shards whirl around him; he gathers them one by one, the warm and the "
      "cold alike, without trying to fit them together, and holds them to his chest with both arms."),
    S("S28", 133.765, 138.2, "storm", ("boy",),
      f"{B.capitalize()} stands on the mirror sea holding the glowing shards to his chest, hair and hood whipping in a "
      "rising wind, mist racing past, rain streaking sideways and upward.",
      "The wind strengthens; mist pours across the frame until the picture whites out.",
      fade_out=0.5, fade_to="fog"),
    # ---- chorus 2 ----------------------------------------------------------------------------
    S("S29", 138.2, 139.765, "storm", ("boy",),
      "Close-up of the round, soft face of the boy, a small nine-year-old child, in a storm: eyes narrowed "
      "against the wind, mouth closed, hair lashing, glowing shards held to his chest.",
      "Wind whips his hair and rain streaks past; he keeps his eyes narrowed and his mouth closed, a quiet "
      "tired child leaning slightly forward into the wind; his face stays the same.", dissolve=0.4),
    S("S30", 139.765, 142.765, "storm", ("sea", "boy"),
      f"Extreme wide: the mirror sea in a storm, waves of mist, the cloud-whale thrashing low overhead; {B}, tiny, leans "
      "into the wind.",
      "He fights forward step by step; the whale-cloud rolls and its tail sweeps down curtains of mist; the camera "
      "shakes slightly."),
    S("S31", 142.765, 145.765, "storm", ("sea",),
      "The storm sky crowded with enormous floating mouths and megaphones blasting speech bubbles of black "
      "scribble, bigger and closer than before; a tiny child figure below.",
      "The megaphones swing and shake as they blast; the bubbles of black scribble swell and multiply across "
      "the sky; slow push-in toward the tiny figure. The painted anime look stays the same throughout and the "
      "water stays flat and calm."),
    S("S32", 145.765, 150.1, "storm", ("sea", "boy"),
      "Low angle: out of the dark belly of the cloud-whale lean two towering grown-up figures made of storm "
      "cloud, one from each side of the sky, turned on each other and each pointing an enormous finger at the "
      "other, small lightning crackling between them; directly beneath them the boy, small, hunches around the "
      "glowing shards in his arms; giant crows wheel in a tight flock.",
      "The two cloud giants lean closer and jab their fingers at each other, lightning flickering between them; "
      "below them the boy hunches lower but keeps his feet; spray streaks past."),
    S("S33", 150.1, 154.765, "storm", ("sea", "boy", "girl"),
      f"{G.capitalize()} walks across the mirror sea from the left holding her amber lantern and stops beside {B}, shoulder "
      "to shoulder, both facing into the wind; warm lantern light on both of them, small amber fish around the lantern.",
      "She steps in beside him and simply stands there; around the two the wind eases and the mist clears into a small "
      "warm dome of calm air; he glances sideways at her."),
    S("S34", 154.765, 158.86, "storm", ("boy", "girl"),
      f"Low angle two-shot of {B} and {G} side by side looking up; above them in the dark belly of the cloud-whale a thin "
      "ragged crack shows pale light.",
      "Both tilt their heads back; the camera tilts up with them to the thin crack in the cloud, which widens slightly; "
      "pale light touches their faces."),
    # ---- bridge ------------------------------------------------------------------------------
    S("S35", 158.86, 164.765, "grey", ("hill", "boy", "girl"),
      "On the windy grass hill above the sea of clouds: the boy in the foreground opening his arms, the glowing "
      "mirror shards, warm golden ones and cold blue ones together, lifting off his open hands into the wind; "
      "the girl stands a few steps behind him.",
      "He opens his arms wide and the shards, golden and blue alike, lift away one by one on the wind; his hair "
      "and hoodie whip; he watches them go.", dissolve=0.4),
    S("S36", 164.765, 170.765, "grey", ("hill",),
      "Looking up from the hill: the glowing shards unfold in mid-air into a flock of white paper cranes that "
      "shine faintly as they climb toward the pale crack in the cloud-whale's belly.",
      "The shards, golden and blue alike, unfold into white paper cranes that flap and spiral upward toward the "
      "crack of light; the camera tilts up following them; light from the crack flickers across their wings."),
    S("S37", 170.765, 178.265, "light", ("hill", "boy", "girl"),
      f"Luminous rain begins to fall on the hill, every drop glowing amber in low sun under the cloud's edge; {B} lifts "
      f"his face into it with his eyes closed; beside him {G} holds out an open palm to catch the drops.",
      "Glowing rain falls and brightens; the boy keeps his face lifted, drops running down his cheeks; the dry grass "
      "around their feet turns green; the cloud-whale overhead grows thinner and paler."),
    S("S38", 178.265, 182.3, "light", ("boy", "girl"),
      "Extreme close-up of the small, soft hands of two nine-year-old children in soft glowing rain against a blurred grassy background: the girl's open "
      "palm in an amber raincoat sleeve held out, the boy's hand in a charcoal hoodie sleeve hovering just above it.",
      "The boy's hand hesitates, draws back a little, then lowers and takes the girl's hand; her fingers close gently "
      "around his; a soft warm glow spreads from their joined hands."),
    # ---- breakdown and the long silence ------------------------------------------------------------
    S("S39", 182.3, 187.765, "grey", ("hill", "girl"),
      "Wide, nearly monochrome: the dark belly of the cloud-whale has sunk low over the hill and swallowed the "
      "sun, only a dim smear of light left inside it; the boy sits small in the grass with his head down; "
      "beside him the girl stands on tiptoe with both arms stretched up, her fingers just reaching the "
      "underside of the cloud.",
      "The last dim light sinks into the cloud; the girl, on tiptoe with her boots staying on the grass, gets "
      "both fists into the heavy cloud like the hem of a curtain and hauls downward at it with her whole body, "
      "again and again; the cloud stretches; the boy lifts his head to look."),
    S("S40", 187.765, 193.0, "break", ("hill", "boy", "girl"),
      f"{G.capitalize()} tears holes in the dark cloud above the hill with her bare hands, and through each hole a golden "
      f"shaft of sun drops onto the grass; {B} watches from a few steps away.",
      "She rips open one hole after another and a new shaft of sunlight drops each time; the boy takes three slow steps "
      "and stands inside one of the shafts, lifting his face."),
    S("S41", 193.0, 201.25, "break", ("hill", "boy", "girl"),
      f"Quiet wide shot: {B} and {G} stand side by side on the hill inside golden shafts of sunlight falling through "
      "ragged holes in the dark cloud, glowing pollen drifting in the light.",
      "Almost still: pollen drifts through the shafts, grass sways slowly, the holes in the cloud widen very slowly; the "
      "two children stand and breathe."),
    # ---- final chorus --------------------------------------------------------------------------
    S("S42", 201.25, 204.265, "light", (),
      "Vast view over the dream-city as the colossal cloud-whale above it bursts apart into thousands of white birds, and "
      "a flood of sunlight and fanning rays pours down across the leaning towers. No people in the picture.",
      "The whale-cloud breaks from the middle outward into streaming flocks of white birds and sunlight sweeps across the "
      "city; the camera pulls back and rises fast."),
    S("S43", 204.265, 207.265, "light", ("hill", "boy", "girl"),
      f"{B.capitalize()} and {G} run side by side down the grassy slope in new sunlight, white birds streaming overhead, "
      "each footstep leaving a ring of golden light that spreads through the wet grass.",
      "They run together through the wind-blown grass, the girl a half step ahead looking back at him; the camera tracks "
      "alongside."),
    S("S44", 207.265, 210.265, "light", ("sea",),
      "Over the mirror sea in clearing light: the giant eyes close and turn into flowers, the huge pointing hands crumble "
      "into drifting petals, the floating megaphones shrink into small paper lanterns. No people in the picture.",
      "One after another the giant eyes close into blossoms, the hands fall apart into petals and the megaphones shrink into "
      "little lanterns that float away."),
    S("S45", 210.265, 213.1, "light", ("sea", "boy", "girl"),
      f"{B.capitalize()} and {G} walk toward us across the bright mirror sea past a tiny paper lantern no taller than "
      "their ankles, petals drifting around them; the water now mirrors a bright blue sky with towering white clouds, so "
      "that they seem to walk on the sky.",
      "They walk forward together, the boy's stride steadier; he passes the tiny lantern without looking at it."),
    S("S46", 213.1, 217.84, "light", ("hill", "girl"),
      f"Close-up of {G} on the hill turning toward us, sunlight on her face, beginning to smile; a sun shower "
      "hangs around her, glittering raindrops suspended in the light, each holding a tiny rainbow.",
      "She turns and her smile opens fully, warm and unguarded; wind lifts her hair; small flowers open in the grass "
      "behind her."),
    S("S47", 217.84, 223.765, "colour", ("hill",),
      "The hill and the whole dream world burst into colour: wildflowers of every colour blooming across the slope, the "
      "leaning towers bright and overgrown with gardens, gentle luminous sky-whales made of white cloud swimming in a "
      "brilliant blue sky.",
      "A wave of colour sweeps outward across the slope, wildflowers springing open in its wake; white cloud-whales glide "
      "overhead; the camera cranes up and back to reveal the whole landscape."),
    S("S48", 223.765, 226.765, "colour", ("boy",),
      f"Close-up of {B} in clear sunlight among wildflowers, colour in his cheeks, wind in his hair, looking at the world "
      "around him, the wide blue sky and its towering white clouds reflected in his eyes.",
      "He looks around, breathes in, and a small real smile appears for the first time; petals drift past."),
    # ---- outro and coda ----------------------------------------------------------------------------
    S("S49", 226.765, 232.765, "colour", ("hill", "boy", "girl"),
      f"Wide tracking shot: {B} and {G} run along a ridge of wildflowers, white birds and small glowing fish in the air "
      "around them, white cloud-whales in the blue sky.",
      "They run along the ridge through the flowers, laughing; birds sweep past the camera; the camera tracks with them."),
    S("S50", 232.765, 238.765, "colour", ("hill", "boy", "girl"),
      f"{G.capitalize()} flies a paper kite on the flowering hill; next to her {B} holds a string in his raised hand, and "
      "tied to the string, floating just above his head like a balloon, is one tiny pale-grey cloud in the shape of a "
      "baby whale.",
      "The kite tugs in the wind; the tiny cloud-whale bobs gently on its string above the boy as he walks; he looks up "
      "at it calmly."),
    S("S51", 238.765, 244.5, "gold", ("hill", "boy", "girl"),
      f"Golden hour: {B} and {G} walk away from us down the flowered slope, the boy holding a string in his hand, and on it, "
      "floating just above his head like a balloon, one tiny pale-grey cloud shaped like a baby whale; the sun low and huge.",
      "They walk on into the golden light; the tiny cloud-whale bobs along behind; the sun sinks lower.", tail=1.2),
    S("S52", 244.5, 250.5, "gold", ("room", "boy"),
      "The same room at sunset, warm and colourful now, the window open and the water on the floor gone, "
      "flowers in a jar: the boy curled on the sofa hugging the cushion exactly as before; the tiny pale-grey "
      "cloud-whale floats above the sofa arm, tied to it by a string; a paper crane sits on the windowsill; on "
      "the wall above the sofa the framed family photograph still hangs with its glass cracked down the middle, "
      "and beside it is pinned a new child's crayon drawing of two children on a green hill.",
      "Warm light moves slowly across the room; the tiny cloud-whale bobs on its string; the boy lies curled "
      "and still, eyes open, calm.", dissolve=1.2),
    S("S53", 250.5, 258.867, "gold", ("@S52", "boy"),
      "Close shot in the same warm, dry, colourful room at sunset, the camera near the sofa cushion: the head "
      "and shoulders of the boy, lying curled on the sofa with his cheek on the cushion and his eyes open, fill "
      "the right half of the frame; on the cushion right in front of his face lies a tin-can telephone, glowing "
      "warm amber, its string pulled taut out through the bright open window behind; the tiny pale-grey cloud "
      "floats on its string in the background.",
      "The tin can glows and trembles on its taut string; he looks at it, picks it up and holds it to his ear; "
      "after a moment a small smile spreads across his face and he turns his head toward the bright window.", fade_out=3.0, fade_to="paper"),
]


def shot_at(t: float) -> Shot:
    for s in SHOTS:
        if s.t0 <= t < s.t1:
            return s
    return SHOTS[-1]


def check() -> None:
    assert SHOTS[0].t0 == 0.0
    for a, b in zip(SHOTS, SHOTS[1:]):
        assert abs(a.t1 - b.t0) < 1e-6, (a.id, b.id)
    for s in SHOTS:
        assert s.use_seconds <= 15.0, (s.id, s.use_seconds)
        assert all(r in REFS or r.startswith("@") for r in s.refs), s.id


check()
