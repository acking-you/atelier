"""The numbers every part of the film must agree on (version 4, "the child's own drawing").

The storyboard is hx/STORYBOARD.md. World units are screen pixels of the 1920x1080 frame at the
identity camera; y runs down. Nothing here is lyric text: lines are LRC indices and times.
"""
from __future__ import annotations

FLOOR = 742.0            # the one ground line: skirting board, classroom floor, kerb, horizon, hill foot
CHILD_H = 380.0          # the child's standing height
FRIEND_H = 388.0         # the friend's
CHILD_X, FRIEND_X = 900.0, 1080.0      # two-shot: the friend is always on the child's right

# seeds are a line's hand: the same thing has the same seed in every module, or it jumps at a hand-off
CHILD_SEED = 3
FRIEND_SEED = 5
GLOOM_SEED = 4
GROUND_SEED = 20

# the song
T_END = 258.87
BAND_IN = 58.60          # the band enters (first chorus)
BAND_SLAM = 201.25       # the band comes back after the long silence: the sheet rips
T_COLOUR = 217.84        # LRC 62: the ring opens
HITS_1 = (64.77, 66.27, 67.77)         # the three hits of chorus 1
HITS_2 = (144.27, 145.77, 147.27)      # chorus 2
HITS_3 = (207.26, 208.76, 210.26)      # chorus 3 (answered)

# ---------------------------------------------------------------------------------------------
# The room (the same room in the intro, the second verse and the coda). Anchors every module and
# every performance agrees on; the set builders draw to them. World units.
# ---------------------------------------------------------------------------------------------
SOFA_X, SOFA_W = 230.0, 760.0            # the sofa's left end and width (its feet on FLOOR)
SOFA_SEAT_Y = FLOOR - 120.0              # top of the seat cushion: where a sitting pelvis and a lying body rest
SOFA_SEAT_X = (292.0, 928.0)             # the seat between the armrests
SOFA_ARM_Y = FLOOR - 184.0               # top of the armrests
SOFA_ARM_R = (886.0, 990.0)              # the right armrest (the child's head end; the string is tied here in the coda)
SOFA_BACK_Y = FLOOR - 288.0              # top of the back
CURL_X = 815.0                           # ground-point x of the child curled on the sofa, head toward the right armrest
RUG = (640.0, FLOOR + 62.0, 500.0, 50.0)           # centre x, centre y, radii
PHONE = (690.0, FLOOR + 20.0)            # the phone on the rug, at its far edge by the sofa: within reach of a hand from the floor
WINDOW = (1300.0, 170.0, 1670.0, 560.0)  # l, t, r, b
WALL_DRAWING = (1150.0, 318.0)           # centre of the family drawing on the wall (clear of a standing child's head)
TABLE_X = 1790.0                         # the table with three chairs (cropped by the right edge)
LAMP_X = 132.0
# school
DESK_TOP_Y = FLOOR - 128.25              # the top of the classroom desk that stands apart (sets.classroom, scale 1.35)


# ---------------------------------------------------------------------------------------------
# The journey and the hand-offs. BINDING, and newer than any task brief: where a brief or the
# storyboard's prose gives another number or another pose for a hand-off, these win.
#
# The film is ONE continuous world and the child travels to the right through it; nothing is ever
# re-centred (the ground line is one stroke with one hand, so a shifted world would show as a jump).
# The room is drawn three times at three places: at its own coordinates (0..1920) in the first
# verse, shifted by ROOM2_DX in the second verse, by ROOM3_DX in the coda (every room anchor above
# shifts with it). The land is flat left of HILL_X0; the first hill begins there.
#
# The figures' rest states are the acting modules' hold functions (acting_child.hold_B1 .. hold_B5,
# acting_pair.hold_B6 .. hold_B10): take x, y and face from the Act they return (they agree with the
# numbers below). The scribble at a hand-off is gloom.handoff_gloom(F, name, ...).
#
# At a hand-off time both neighbouring modules draw exactly this state: the figures stand in the
# named rest state, alive (breath, blinks) but not acting; the camera is still; nothing is half
# drawn. Motion ends at least 0.25 s before a hand-off and begins after it.
# ---------------------------------------------------------------------------------------------
ROOM2_DX = 3060.0        # the evening room (inter, second verse): room x + 3060
ROOM3_DX = 7700.0        # the warm room of the coda: room x + 7700
HILL_X0 = 4700.0         # where the plain ends and the first hill begins to rise
WIDE_ZOOM = 0.205        # the wide frame of the choruses: the child is 78 px tall, the frame 9366 units wide

X1 = 1040.0              # B1  36.27  the child beside the sofa's right end
X2 = 2200.0              # B2  58.60  after the trudge through school and home; chorus 1 happens here
X3 = 640.0 + ROOM2_DX    # B3  91.77  on the rug of the evening room (= 3700)
X4 = 3760.0              # B4 115.77  planted on the corridor line
X5 = 4300.0              # B5 138.20  after the family line; chorus 2 and the bridge happen here
X9 = 5600.0              # B9 226.76  on top of the first hill
X10 = 1300.0 + ROOM3_DX  # B10 244.50 alone on the bare warm sheet (= 9000); the coda's room draws on round it
FRIEND_FAR_1 = X2 + 4900.0     # the far friend of chorus 1 (wide frame: at 88 percent of the width)

# cam = (cx, cy, zoom); cloud = (cx, cy, rx, ry) of the scribble; x, face, state of the figures.
# "state" names the rest state in words; the acting modules give the pose for it.
HANDOFF = {
    "B1": dict(t=36.27, skin="night", cam=(960.0, 540.0, 1.0),
               set="the night room, complete; 11 crows on the wire; the amber window lit; rain on the pane",
               child=dict(x=X1, face=1, state="standing, head down"),
               cloud=(X1 - 30.0, 236.0, 380.0, 128.0), strand=True, rain=0.0),
    "B2": dict(t=58.60, skin="night", cam=(X2, 520.0, 0.9),
               set="bare sheet: the ground line only",
               child=dict(x=X2, face=1, state="standing three-quarter to us, head down, both hands at the chest over the tucked halves (acting_child.hold_B2)"),
               cloud=(X2 - 30.0, 250.0, 420.0, 150.0), strand=True, rain=0.6),          # the rain hangs still
    "B3": dict(t=91.77, skin="night", cam=(960.0 + ROOM2_DX, 540.0, 1.0),
               set="the evening room at ROOM2_DX, complete; no crows; the amber window lit; the phone's screen pale",
               child=dict(x=X3, face=1, state="standing on the rug, head a little down (it sits down after the hand-off)"),
               cloud=(X3 - 30.0, 240.0, 380.0, 135.0), strand=True, rain=0.0),
    "B4": dict(t=115.77, skin="night", cam=(X4, 520.0, 0.9),
               set="bare sheet: the ground line only",
               child=dict(x=X4, face=1, state="standing planted: feet apart, braced, head level"),
               cloud=(X4 - 30.0, 250.0, 420.0, 150.0), strand=True, rain=0.0),
    "B5": dict(t=138.20, skin="night", cam=(X5, 520.0, 0.9),
               set="bare sheet: the ground line only",
               child=dict(x=X5, face=1, state="standing, head down, the two halves of the drawing tucked away"),
               cloud=(X5 - 30.0, 240.0, 520.0, 180.0), strand=True, rain=0.0),
    "B6": dict(t=158.86, skin="night", cam=(X5 + 90.0, 590.0, 1.2),
               set="the plain; the ceiling thinned, one thin pale place above the two; the towers gone",
               child=dict(x=X5, face=1, state="sitting on the ground, head lifted, looking up"),
               friend=dict(x=X5 + 180.0, face=-1, state="crouched facing the child, looking up"),
               hands="joined: the child's right in the friend's left", cloud=None, strand=True, rain=0.25),
    "B7": dict(t=182.30, skin="night", cam=(X5 + 90.0, 500.0, 1.3),
               set="the plain with the first hill's contour drawn (rising right of HILL_X0)",
               child=dict(x=X5, face=1, state="standing, eyes fully open, facing the friend"),
               friend=dict(x=X5 + 180.0, face=-1, state="standing, its hand on the child's shoulder"),
               cloud=(X5 + 90.0, 110.0, 600.0, 150.0), strand=False, rain=0.0),
    "B8": dict(t=201.25, skin="night", cam=(X5 + 90.0, 470.0, 0.85),
               set="the scribble hanging as two curtains; the seam where it was opened is X5 + 180, the opening held by the four hands is about X5 - 107 .. X5 + 289 (its middle X5 + 90); the shaft through it",
               child=dict(x=X5 - 20.0, face=-1, state="arms up, holding the left curtain aside, leaning back on it"),
               friend=dict(x=X5 + 200.0, face=1, state="on tiptoe, arms up, holding the right curtain aside, leaning back on it"),
               cloud=None, strand=False, rain=0.0),
    "B9": dict(t=226.76, skin="day", cam=(X9 + 90.0, 480.0, 0.75),
               set="the hill world in colour, afternoon gold; the ring is past the frame",
               child=dict(x=X9, face=1, state="standing hand in hand, a small smile, the string in its free (left) hand"),
               friend=dict(x=X9 + 180.0, face=-1, state="standing hand in hand, smiling"),
               tangle="the small tangle on its string above the child's free hand", cloud=None, strand=False, rain=0.0),
    "B10": dict(t=244.50, skin="day", cam=(960.0 + ROOM3_DX, 540.0, 1.0),
                set="bare warm sheet at evening: the ground line only",
                child=dict(x=X10, face=-1, state="standing alone, at ease, the string in its hand"),
                tangle="the small tangle on its string", cloud=None, strand=False, rain=0.0),
}
