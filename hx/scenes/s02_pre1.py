"""s02_pre1   36.27 - 58.60   p1a, p1b, hush1          B1  ->  B2

One travelling shot: the child trudges right from X1 to X2, a step a beat, and the world changes
round it: the room turns into the classroom by declared pairs, the classroom un-draws, a street
lamp passes and becomes the lamp over the home table, the home is taken back to the bare sheet.

CUE SHEET (song's clock; lines by 0-based LRC index and time, paraphrased; no lyric text)
  B1 36.27      the first frame is S.handoff(F, "B1"): the night room, eleven crows, the amber window, the child
                standing at X1 = 1040 head down, the cloud on its crown, the strand
  p1a 36.27 - 48.27
  36.27 idx 11  (never really present anywhere) the first step on the bar; the child trudges right, a step a beat,
                five steps to its place XS = 1386 (40.02). The crows fly up one after another (36.42 - 37.3). The room
                turns into the classroom round it (36.27 - 38.6, _s02.turn): the soft things let go first, the
                window stays a window (its pane goes from night to a grey day, no amber at school), the sofa travels
                into the desks of the rows it passes, the torn drawing into the board, the table into the desk that
                stands apart, the pulled-away chair into the chair of the last back it passes, lamp into door,
                cushion into clock, books into pinned drawings; a pupil about every quarter beat from 36.9, the rows
                it passes sit along its way (it walks between the back row and the front row: nobody turns); the
                hanging lamps one by one. Ahead, the far rows draw on, a pupil per half beat from 37.765.
                Camera: from B1 it eases after the child and past it (36.27 - 40.4) to the classroom framing: the
                child in the left third, its desk and the rows ahead, head 147 px
  40.02         it arrives at its place under the window, its desk just ahead
  40.34 idx 12  (a voice too thin to be heard) the face lifts (40.02 - 40.57), a hand half
                raised; three small tries at a word (40.4, 40.8, 41.16); the voice leaves its mouth as a thin wavering
                chalk line on the attack 40.37 and wanders out over the turned backs, falling short (to 41.45);
                nobody turns. 41.51 (attack) it droops, wilting from its far end among the backs; 41.75 - 42.15 it
                turns dark; 41.95 - 42.56 its mouth end lets go, goes up before the brow onto the crown and the
                whole line is wound up the strand into the scribble, which swallows it on the attack 42.56 (it grows,
                swells and sheds pale dust)
  42.66 idx 13  (it tells itself to try) hands on its desk (42.37); three shoves with the whole body on
                the attacks 42.70, 44.12, 44.86 (58, 76, 96 units), the desk slides back each time; after each shove
                the rows ahead are a step further away (110, 130, 150 units); the strand goes taut as it leans
                and tugs the cloud's belly; a tremble while the last is held
  46.2          (attack 46.225) the arms drop (46.2 - 46.66), the head goes down
  46.5 - 48.2   the classroom is taken back while it walks on: its own desk first (46.5), pins, board, clock, door,
                lamps, the backs (from 46.5), the window (47.1), the wall lines (47.4)
  46.765        it walks on (seven steps, arrives at X2 52.02); a street lamp draws on (46.765 post, 46.9 kerb),
                its lantern lights (47.5 - 47.8) and goes out as the heavy cloud comes over it
  46.6 - 52.3   camera: travels with it to the home framing (head 177 px)
  p1b 48.27 - 56.00
  48.27 idx 15  (home, as memory) on the bar the long table top draws on ahead of it; legs and cloth (48.7 - 50.2);
                the chair on the right (49.015), the window (49.4: the same window, curtains, the amber window across
                the street), the tall faceless one on the right chair (49.78 - 50.6), the child's own chair (50.21),
                the chair on the left once it has passed (50.515), the tall one on the left chair (50.99 - 51.7), two
                cups (51.0, 51.39); the street lamp's lantern travels up into the lamp over the table (49.2 - 50.6),
                which lights on the attack 50.99; the drawing, whole, stands on the table (51.27 - 51.95).
                The memory's light holds the cloud up (48.8 - 51.8)
  52.02         the child stands behind the table at its own place, three-quarter to us
  52.36 idx 16  (what broke cannot be mended) the two rise (52.36, 52.48), turn their backs on each other and
                walk away to opposite sides, a step a half beat, each stepping off on a tear (53.14, 53.505), to the
                frame's edges and rubbed out there (54.1 - 54.6, 54.45 - 54.95: the right one at the edge of the frame
                as the camera goes back); the two chairs slide apart (52.5 - 54.4); the child's eyes follow the left
                one; 53.14 the tear runs half down the drawing (its eyes drop, a hand to that half: the head goes
                down over 9 frames), 53.51 it runs through (the other hand); the lamplight dims a step with each; its
                eyes follow the right one (53.96). The cloud comes down and grows (53.2 - 55.7)
  54.64 idx 17  (each time it remembers) it lifts the halves (54.64) and holds them together (55.01); the grip
                loosens and they drift apart (55.27, 55.72); it takes them to its chest (55.62 - 55.95). Rain begins
                (54.6). Camera: back, slowly, to B2 (54.3 - 55.95), the halves keeping their place on screen
  55.0 - 55.93  every line of the home is taken back from its ends: lamp, cups, curtains, window, chairs, table
  hush1 56.00 - 58.60   true silence: the picture B2 (bare sheet, the child at X2 head down, hands at its chest, the
                cloud, the strand, the rain hanging still). Nothing moves but the breath and one slow blink (57.1)
  58.35         S.joined draws S.handoff(F, "B2") (the storyboard's breath-in at 58.56 lies inside that window:
                hold_B2's breath is falling there; it is the hand-off picture's to give)

STAGING   the child travels right and never turns: its desk stands AHEAD of it (push = +1) and the rows it is
          pushed toward sit beyond it; they recede a step after each shove (that is how they are a step further
          away). The rows it passes on its way stand along its first steps, the front row in front of it.
THE PERFORMANCE   AC.s02(x_stop=XS, push=+1) with five mends of this module (act): the arms let go of the desk
          over 14 frames (46.2), the upper body carried into the walk (46.745), the head going down at the first
          tear over 0.32 s with the eyes first (53.15), the feet that slide over the floor lifted (42.3 - 46.44,
          52.05 - 52.55), the halves drifting apart clearly on 55.27 (and a little on 55.72, into the tuck).
FILES     _s02.py: the turn of this staging, the street lamp, the voice line, the adults' walk, the scribble's
          two extra arguments.
"""
import functools
import math

from hx import story
from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk import acting_child as AC

from . import _s02 as M
from . import _shared as S

SPAN = (36.27, 58.60)
START, END = "B1", "B2"

FLOOR, X1, X2 = story.FLOOR, story.X1, story.X2
C1, C2 = story.HANDOFF[START]["cloud"], story.HANDOFF[END]["cloud"]

# ---- the staging: where things stand (world x) ------------------------------------------------------
XS = 1386.0                                              # where the child stops: its place in the classroom (five trudging steps from X1)
DESK_DX = XS + 112.0 + 75.6 - 400.0                      # classroom(side=-1): its desk's left end 112 units ahead of it, where the hands go
ROWS_L = dict(far=((690.0, 930.0, 1170.0), 738.0, 1.16), near=((570.0, 810.0, 1050.0), 826.0, 1.40))   # the rows it passes on its first steps
ROWS_R = dict(far=((2050.0, 2290.0, 2530.0), 738.0, 1.16), near=((1930.0, 2170.0, 2410.0, 2650.0), 826.0, 1.40))   # the rows its desk is pushed toward
ROWS_R_ON = ("f0", "b0", "f1", "b1", "f2", "b2", "f3")   # they draw on left to right as the camera comes to them
STEPS = (110.0, 130.0, 150.0)                            # how much further away the rows are after each shove
LAMP_X = 1768.0                                          # the street lamp between school and home (its lantern hangs 92 further on)
HOME_DX = X2 - 1010.0                                    # the home table: the child stands behind its middle at X2
LAMP_UP = 40.0                                           # the lamp over the table hangs this much higher than the kit's (the cloud's belly is where the kit hangs it)
SHEET = 0.62                                             # the scale of the family drawing on the table

# ---- the times (song's clock) -------------------------------------------------------------------------
SHOVES = AC.S02_T["shoves"]                              # 42.7, 44.12, 44.86
V_OUT, V_DROOP, V_DARK, V_WIND = (40.37, 41.45), (41.51, 42.05), (41.75, 42.15), (41.95, 42.56)
DROP = (46.2, 46.66)                                     # the arms drop off the desk
CLASS_OFF = (46.5, 48.2)
T_HUSH = 56.0
CAM_BACK = (54.3, 55.95)                                 # the camera goes back to B2 under the halves

# ---- the camera: three moves, each on an ease, and three holds ---------------------------------------
CAM_CLASS = Cam(XS + 420.0, 558.0, 1.25)                 # the child in the left third, the rows ahead; head 147 px; the ground line at 770
CAM_HOME = Cam(X2 + 10.0, 535.0, 1.5)                    # the table; head 177 px; the ground line at 850, clear of the lyric line


def _between(a: Cam, b: Cam, u: float) -> Cam:
    return Cam(a.cx + (b.cx - a.cx) * u, a.cy + (b.cy - a.cy) * u, a.zoom * (b.zoom / a.zoom) ** u)


def camera(t: float) -> Cam:
    if t < 43.0:
        return _between(S.CAM[START], CAM_CLASS, ease(seg(t, 36.27, 40.4)))     # travelling with the trudge, coming in for the face
    if t < 53.3:
        return _between(CAM_CLASS, CAM_HOME, ease(seg(t, 46.6, 52.3)))          # the way home
    return _between(CAM_HOME, S.CAM[END], ease(seg(t, *CAM_BACK)))              # back, slowly, as the two are gone: the bare sheet


# ---------------------------------------------------------------------------------------------
# the performance, staged
# ---------------------------------------------------------------------------------------------
_UPPER = ("bend", "neck", "lean", "look", "gaze", "eye", "lid", "brow", "mouth", "hair")
_HEAD = ("bend", "neck", "lean", "look", "hturn", "tilt", "hair")      # what turns the head (the eyes and the face react at once)
T_GO2 = AC.S02_T["on"] - 0.02                            # 46.745: where AC.s02 hands the give-up pose to the walk
T_TEAR1 = AC.S02_T["tear"][0] + 0.01                     # 53.15: AC.s02 drops the head onto the sheet in 0.16 s (a jolt)
SOFT_TEAR = 0.32                                         # ... here the head takes 0.32 s, eyes first


def _raw(t: float):
    return AC.s02(t, x_stop=XS, push=1, sheet=SHEET)


SHUFFLE = ((42.30, 46.44), (52.05, 52.55))              # AC.s02 moves its feet over the floor here (stance changes, the shoves' steps, the turn to us)
DRIFT = ((55.27, 55.52, 14.0), (55.716, 55.90, 10.0))   # the halves drift apart: (t0, t1, units each side) on the two attacks


def _with(a, P, grab=None, pts=None):
    """The Act a with pose P (grab, pts): joints and the points that hang on them recomputed."""
    J = pose_joints(P, a.x, a.y, a.h, a.face)
    return AC.Act(P, a.x, a.y, a.face, a.grab if grab is None else grab, a.draw, a.a, 1.0, J,
                  dict(a.pts if pts is None else pts, mouth=J["mouth"], crown=J["crown"]), a.num, a.h)


def _step_feet(P, t: float):
    """A foot that travels must leave the floor: in AC.s02's stance changes (into the ready pose,
    42.37; into the give-up pose, 46.04) both feet slide 15 to 20 units over the floor in a few
    frames. Each is lifted by its own speed (up to 9 units), so the shuffle reads as small steps."""
    pa, pb = _raw(t - 1.0 / 30).pose, _raw(t + 1.0 / 30).pose
    kw = {}
    for key in ("ff", "fb"):
        v = abs(pb[key][0] - pa[key][0]) * 15.0                              # body units a second
        if v > 0.02:
            kw[key] = (P[key][0], P[key][1] + 0.024 * min(1.0, v / 0.35))
    return P.but(**kw) if kw else P


@functools.lru_cache(maxsize=1)
def _drop_ends():
    """The two hands on the desk as the arms let go, and where they hang once dropped."""
    a0, a1 = _raw(DROP[0] - 0.05), _raw(DROP[1] + 0.04)  # (46.70: still the give-up pose; the walk takes over at 46.745)
    return (a0.grab["f"], a0.grab["b"]), (a1.J["ha_f"], a1.J["ha_b"])


@functools.lru_cache(maxsize=8192)
def act(t: float):
    """AC.s02 stopping at XS, its desk ahead (push = +1: no turn), with three things of this staging:
    - 46.15 to 46.66 the arms drop: AC.s02 lets go of the desk in one frame (the pinned hands spring
      to the pose's own, 22 units) and drops them 95 units in four frames; here the hands are carried
      from the desk to where they hang over 14 frames, slow to leave, faster, settling;
    - 46.745 with push = +1 the kit goes from the give-up pose (head hanging) straight into the walk's
      first pose in one frame: the upper body is carried over for half a second;
    - 53.15 the first tear: the head goes down onto the sheet over 0.32 s instead of 0.16 (eyes, lids,
      brows and mouth react on the frame; the head follows);
    and two small mends: the feet that slide over the floor in the stance changes are lifted
    (SHUFFLE), and the halves drift apart visibly on the two attacks (DRIFT: AC.s02 moves them 9 to
    15 units on the first and not on the second)."""
    a = _raw(t)
    P, grab, pts = a.pose, None, None
    if DROP[0] - 0.05 <= t < DROP[1]:
        (pf, pb), (qf, qb) = _drop_ends()
        u = ease(seg(t, *DROP))
        grab = {"f": (pf[0] + (qf[0] - pf[0]) * u, pf[1] + (qf[1] - pf[1]) * u), "b": (pb[0] + (qb[0] - pb[0]) * u, pb[1] + (qb[1] - pb[1]) * u)}
    if T_GO2 <= t < T_GO2 + 0.55:
        P0 = _raw(T_GO2 - 0.005).pose
        Pm = mixp(P0, P, ease(seg(t, T_GO2, T_GO2 + 0.55)))
        P = P.but(pel=(P["pel"][0], Pm["pel"][1]), **{k: Pm[k] for k in _UPPER})
    if T_TEAR1 <= t < T_TEAR1 + SOFT_TEAR:
        P0 = _raw(T_TEAR1 - 0.005).pose
        Pm = mixp(P0, P, ease(seg(t, T_TEAR1, T_TEAR1 + SOFT_TEAR)))
        P = P.but(**{k: Pm[k] for k in _HEAD})
    if any(t0 <= t < t1 for t0, t1 in SHUFFLE):
        P = _step_feet(P, t)
    if a.grab is not None and t > DRIFT[0][0] and a.num["tuck"] < 1.0:
        tk = a.num["tuck"]
        d = DRIFT[0][2] * ease(seg(t, DRIFT[0][0], DRIFT[0][1])) + DRIFT[1][2] * ease(seg(t, DRIFT[1][0], DRIFT[1][1]))
        d *= 1.0 - tk ** 3                                                   # into the jumper they come in to the chest
        (lx, ly), (rx, ry) = a.pts["hand_l"], a.pts["hand_r"]
        pts = dict(a.pts, hand_l=(lx - d, ly), hand_r=(rx + d, ry))
        grab = {"f": (a.grab["f"][0] - d, a.grab["f"][1]), "b": (a.grab["b"][0] + d, a.grab["b"][1])}
    if P is a.pose and grab is None and pts is None:
        return a
    return _with(a, P, grab, pts)


_G = 0.1                                                  # the grid (s) the trailing averages sample the performance on


@functools.lru_cache(maxsize=1024)
def _xc(k: int):
    a = act(round(k * _G, 6))
    return a.x, a.pts["crown"][0]


def _mean(t: float, span: float, i: int) -> float:
    """The mean over [t - span, t] of _xc(.)[i] taken as a polyline through the grid points (exact)."""
    a, b = t - span, t
    k0, k1 = math.floor(a / _G), math.ceil(b / _G)
    s = 0.0
    for k in range(k0, k1):
        u0, u1 = max(a, k * _G), min(b, (k + 1) * _G)
        if u1 <= u0:
            continue
        p, q = _xc(k)[i], _xc(k + 1)[i]
        f = lambda u: p + (q - p) * (u - k * _G) / _G
        s += 0.5 * (f(u0) + f(u1)) * (u1 - u0)
    return s / span


def _trail(t: float):
    """(where the child's ground point was on the average over the last 1.7 s: the cloud is heavy and
    trails behind a walker; where its crown was over the last 1.2 s: the strand's upper end, which
    stays behind when the child leans into a shove). Sampled on a fixed grid of 0.1 s, so that
    consecutive frames share their samples."""
    return _mean(t, 1.7, 0), _mean(t, 1.2, 1)


def _dead(v: float, d: float) -> float:
    return math.copysign(max(0.0, abs(v) - d), v)


# ---------------------------------------------------------------------------------------------
# the classroom
# ---------------------------------------------------------------------------------------------
def _class(desk_dx: float):
    K = classroom(desk_dx=DESK_DX + desk_dx, side=-1)
    K["lone"] = K["lone"].without("lone.chair")                            # the desk stands apart by itself (the back it passes sits where a chair would)
    K["pins"] = K["pins"].without("pins.sheet3", "pins.mark3")              # the lowest sheet hangs where the voice goes by
    return K


def _rows_l(F):
    """The rows the child passes on its first steps (drawn on by the turn), taken back from 46.55."""
    L = class_rows(seed=1400, name="rowsL", t=F.tb, **ROWS_L)
    if F.t > CLASS_OFF[0]:
        for j, nm in enumerate(("f2", "b2", "f1", "b1", "f0", "b0")):      # the nearest first
            L.sub("rowsL." + nm).set_off(46.55 + 0.09 * j, 46.55 + 0.09 * j + 0.6)
    return L


def _split(Sk):
    """(the back row, the front row) of a set of the rows L's strokes: the child walks between them."""
    return (Sketch([it for it in Sk if it.name.startswith("rowsL.b")]),
            Sketch([it for it in Sk if it.name.startswith("rowsL.f")]))


def _rows_r(F, t: float):
    R = class_rows(seed=1470, name="rowsR", t=F.tb, **ROWS_R)
    for j, nm in enumerate(ROWS_R_ON):                                       # a pupil per half beat from beat 2 (37.765): there before it speaks
        R.sub("rowsR." + nm).spread(37.765 + 0.375 * j, 0.0, 0.62, by=2)
    if t > CLASS_OFF[0]:
        for j, nm in enumerate(ROWS_R_ON):
            R.sub("rowsR." + nm).set_off(CLASS_OFF[0] + 0.09 * j, CLASS_OFF[0] + 0.09 * j + 0.6)
    dx = sum(s_ * ease(seg(t, ts + 0.10, ts + 0.72)) for s_, ts in zip(STEPS, SHOVES))    # a step further away after every shove
    far = Sketch([it for it in R if it.name.startswith("rowsR.b")]).place(dx, 0.0)
    near = Sketch([it for it in R if it.name.startswith("rowsR.f")]).place(dx, 0.0)
    return far, near


# ---------------------------------------------------------------------------------------------
# the frame
# ---------------------------------------------------------------------------------------------
def draw(F):
    if S.joined(F, START, END):                          # the last 0.25 s: the hand-off picture B2
        return
    t = F.t
    a = act(t)
    n = a.num
    F.cam = camera(t)
    if t >= T_HUSH:                                      # the silence IS the picture B2: nothing but the breath and one slow blink
        k = story.HANDOFF[END]["rain"]
        S.rain_back(F, k)
        S.bare(F)
        J = S.child(F, a)
        S.scribble(F, C2, J)
        S.rain_front(F, k)
        return

    w = seg(t, *M.SPAN_TURN)
    turning, in_class, in_home = w < 1.0, t < CLASS_OFF[1] + 0.1, t > 48.2
    in_street = 46.7 < t < 50.6
    off = ramp(t, CLASS_OFF[0] + 0.1, CLASS_OFF[1] - 0.1)
    if in_class:
        L = _rows_l(F)

    # ================= behind everything: dressing, light, what the windows show =================
    if turning:
        K = _class(0.0)
        R_, G = M.turn(w, K, L)
        R_.back(F, 1.0 - ramp(w, 0.05, 0.55))
        K.back(F, ramp(w, 0.4, 0.95))
        day = ramp(w, 0.3, 0.85)                         # the pane goes from night to a grey day (no amber window at school)
        S.room_light(F, "night", 0.0, 1.0 - day)
        S.room_light(F, "eve", 0.0, 0.8 * day)
        wire, xs = S.crow_wire(F, 0.0, S.CROW_TIMES)
        R_.view(F, 1.0 - ramp(w, 0.9, 1.0), wire=wire)
        K.view(F, day, wire=wire, lit=0.0)
        rain_window(F, *PANE, 0.6 - 0.15 * day)
        with F.clip(rect=story.WINDOW):                  # the crows fly up one after another, the first as the child takes its first step
            crows_on_wire(F, wire, S.CROW_TIMES, xs, leave=[36.42 + 0.085 * j for j in range(len(S.CROW_TIMES))])
    elif in_class:
        K = _class(n["desk_dx"])
        if t > CLASS_OFF[0]:                             # taken back: its own desk first (it walks on through where it stood)
            for names, t0, d in ((("lone.desk",), 46.5, 0.7), (("pins",), 46.6, 0.7), (("lamps",), 46.8, 0.7),
                                 (("board", "clock", "door"), 46.7, 0.9), (("window",), 47.1, 0.9), (("wall",), 47.4, 0.8)):
                K.all().sub(*names).set_off(t0, t0 + d)
        K.back(F, a=1.0 - off)
        S.room_light(F, "eve", 0.0, 0.8 * (1.0 - off))
        kv = 1.0 - ramp(t, 46.9, 47.7)
        K.view(F, a=kv, lit=0.0)
        rain_window(F, *PANE, 0.45 * kv)
    xs_, cs_ = _trail(t)
    if in_street:
        Sk = M.street(LAMP_X)
        Sk.sub("lamp").spread(46.765, 0.12, 0.45)        # the post on the beat, the lantern after it
        Sk.sub("kerb").spread(46.9, 0.14, 0.5)
        Sk.sub("lamp.foot", "lamp.post", "lamp.neck").set_off(49.2, 49.9)
        Sk.sub("kerb").set_off(49.0, 49.9)
    if in_home:
        apart = ease(seg(t, 52.5, 54.4))
        Hm = home_table(apart, dx=HOME_DX)
        an, a0 = home_anchors(apart, HOME_DX), home_anchors(0.0, HOME_DX)
        Hm["lamp"] = Hm["lamp"].place(0.0, -LAMP_UP)
        _home_times(Hm)
        kh = ramp(t, 48.5, 50.2) * (1.0 - ramp(t, 55.0, 55.75))
        kv = ramp(t, 49.9, 50.9) * (1.0 - ramp(t, 55.1, 55.6))
        lit = ramp(t, 50.99, 51.3) * (1.0 - 0.2 * ramp(t, 53.14, 53.34) - 0.2 * ramp(t, 53.51, 53.71)) * (1.0 - ramp(t, 54.75, 55.2))
        Hm.back(F, a=kh)
        lx, ly = an["lamp"][0], an["lamp"][1] - LAMP_UP
        shaft(F, lx, 80, ly + 6, lx, 400, an["top_y"] + 8, col=M.PALE, a=0.34 * lit, alphas=(1, 0.8, 0.6, 0.45))
        light_pool(F, lx, 772, 470, 44, col=M.PALE, a=0.20 * lit)
        glow(F, lx, ly + 16, 130, 100, col=M.PALE, a=0.24 * lit)
        window_glow(F, *Hm.rect(story.WINDOW), 0.5 * kv, "night")
        Hm.view(F, a=kv)
        rain_window(F, *Hm.rect(PANE), 0.5 * ramp(t, 52.4, 54.0) * kv)
    rk = S.rain_k(t)
    if rk > 0.0:
        S.rain_back(F, rk)
    if in_street:
        cov = ramp(xs_ - 30.0 + 0.9 * C1[2], M.lantern_at(LAMP_X)[0] - 70.0, M.lantern_at(LAMP_X)[0] + 60.0)   # the cloud comes over the lantern: its light goes out
        M.street_light(F, LAMP_X, ramp(t, 47.5, 47.8) * (1.0 - cov))
    S.bare(F)                                            # the one ground line

    # ================= the sets' strokes, behind the child =================
    if turning:
        for g in M.TURN_ORDER:
            if g == "<phone>":
                phone(F, *story.PHONE, lit=0.0, a=1.0 - ramp(t, 36.3, 36.75))
            elif g == "rowsL":
                if g in G:
                    lb, lf = _split(G[g])
                    lb.draw(F)
            elif g in G:
                G[g].draw(F)
    elif in_class:
        K.draw(F)
        lb, lf = L.far, L.near
        lb.draw(F)
    if in_class:
        far, near = _rows_r(F, t)
        far.draw(F)
    if in_street:
        Sk.sub("kerb").draw(F)
    if in_home:
        Hm.draw(F, "window", "chair_m")

    # ================= the child =================
    J = S.child(F, a)

    # ================= what is nearer to us than the child =================
    if in_class and (not turning or "rowsL" in G):
        lf.draw(F)                                       # the front row of the backs it passes
    lift = ease(seg(t, 48.8, 51.8)) * (1.0 - ease(seg(t, 54.75, 55.93)))    # the lamplight of the memory holds the cloud up; it comes down again
    g1, g2 = ramp(t, 42.35, 42.95), ramp(t, 53.2, 55.7)                     # it grows: with the word that went up the strand, with the tear
    gulp = ramp(t, 42.35, 42.72) * (1.0 - ramp(t, 42.72, 43.6))             # ... and swells as it swallows the word
    cloud = (xs_ - 30.0, C1[1] + 4.0 * g1 + (C2[1] - C1[1] - 4.0) * g2 - 180.0 * lift,
             C1[2] + 12.0 * g1 + 10.0 * gulp + (C2[2] - C1[2] - 12.0) * g2, C1[3] + 6.0 * g1 + 9.0 * gulp + (C2[3] - C1[3] - 6.0) * g2)
    lean = min(1.0, max(0.0, abs(n["desk_dx"]) / 96.0))                      # leaning into a shove: the strand goes taut and holds it back
    k_rest = (1.0 - ease(seg(lift, 0.0, 0.45))) * (1.0 - 0.8 * lean)
    slack = 0.8 - 0.62 * lean - 0.3 * lift
    crown = J["crown"]
    root_dx = 40.0 + _dead(cs_ - crown[0], 2.0) * (1.0 - ramp(t, 55.2, 55.8)) - 230.0 * lift     # (40 again by the silence: S.scribble's)
    tug = (crown[0], crown[1], 0.16 * lean) if lean > 0.0 else None
    V = None
    if in_class:
        if V_OUT[0] < t < V_WIND[1] + 0.1:
            band = band_cloud(*cloud, rest=(crown[0], crown[1] + 6.0, k_rest), tug=tug)
            SP = strand_pts(crown, band.root(crown[0] + root_dx, 0.4), slack)
            mx, my = a.pts["mouth"]
            V = M.voice(F.tb, (mx, my), (mx + 1290.0, my - 30.0), seg(t, *V_OUT), ease(seg(t, *V_DROOP)), seg(t, *V_DARK),
                        seg(t, *V_WIND) ** 1.6, crown, SP, head=(J["head"][0], J["head"][1], J["R"]), amp=1.25)
            V.draw_air(F)
        near.draw(F)
    jl = jr = None
    if in_home:
        Hm.draw(F, "chair_l", "chair_r")
        jl, jr = M.adults(F, a0["adult_l"][0], a0["adult_r"][0], a0["seat_y"], draw=(seg(t, *ADULT_ON[0]), seg(t, *ADULT_ON[1])),
                          off=ADULT_OFF)
        Hm.draw(F, "table", "cups")
        if not n["in_hands"]:
            dw = family(*a.pts["sheet"], n["sheet"], tear=n["tear"], detail=2)
            dw.set_on(51.27, 51.95)
            dw.draw(F)
        elif n["tuck"] < 1.0:
            family_held(F, a.pts["hand_l"], a.pts["hand_r"], s=n["sheet"], a=1.0 - n["tuck"])

    # ================= the scribble =================
    avoid = S.clear_of(jl, jr, k=min(1.0, 3.0 * lift)) if in_home and lift > 0.0 else ()
    Tp, _ = M.scribble(F, cloud, J, k=k_rest, slack=slack, root_dx=root_dx, avoid=avoid, tug=tug)
    if V is not None:
        V.draw_wound(F)
    if gulp > 0.0:                                       # more of its pale dust falls as it takes the word in
        gloom_dust(F, cloud[0] - 0.5 * cloud[2], cloud[0] + 0.8 * cloud[2], 0.0, n=26, a=0.8 * gulp, seed=83, band=Tp.band)
    # the lamps stand and hang nearer to us than the cloud: the street lamp, whose lantern goes on with the child and is the lamp over the table
    if in_street and t < 49.2:
        Sk.sub("lamp").draw(F)
    elif in_street:
        Sk.sub("lamp.foot", "lamp.post", "lamp.neck").draw(F)
        Hm["lamp"].sub("lamp.cord").draw(F)
        morph(Sk.sub("lamp.hood", "lamp.bulb"), Hm["lamp"].without("lamp.cord"), seg(t, 49.2, 50.6),
              (("lamp.hood", "lamp.shade"), ("lamp.bulb", "lamp.bulb")), stagger=0.0).draw(F)
    elif in_home:
        Hm.draw(F, "lamp")
    if rk > 0.0:
        S.rain_front(F, rk)


# ---------------------------------------------------------------------------------------------
# the home table: drawn on round the walking child, ahead of it first; taken back from 55.0
# ---------------------------------------------------------------------------------------------
ADULT_ON = ((50.99, 51.7), (49.78, 50.6))               # (left, right): the right one ahead of the child, the left one once it has passed
ADULT_OFF = ((54.1, 54.6), (54.45, 54.95))              # each rubbed out as it reaches the frame's edge


def _home_times(Hm) -> None:
    """The home table draws itself on with the beats from 48.27: the table first, then what stands
    ahead of the walking child (the right chair, the window), its own chair, and the left chair only
    once the child has passed it (it walks behind it); every line is taken back from its ends from 55.0."""
    T = Hm["table"]
    for nm, t0, t1 in (("table.top", 48.27, 48.85), ("table.top.fill", 48.7, 49.3), ("table.leg_l", 48.75, 49.1), ("table.leg_r", 48.85, 49.2),
                       ("table.leg_fl", 49.0, 49.3), ("table.leg_fr", 49.05, 49.35), ("table.cloth", 49.015, 49.7), ("table.cloth.fill", 49.5, 50.2)):
        T[nm].on = (t0, t1)
    Hm["chair_r"].spread(49.015, 0.0, 0.75, by=1)
    Hm["chair_m"].spread(50.207, 0.0, 0.6, by=1)
    Hm["chair_l"].spread(50.515, 0.0, 0.7, by=1)
    W = Hm["window"]
    W.sub(*M.FRAME).spread(49.4, 0.12, 0.5)
    W.without(*M.FRAME).spread(50.0, 0.1, 0.6)
    Hm["lamp"].sub("lamp.cord").set_on(50.0, 50.5)       # (its shade and bulb come from the street lamp)
    Hm["cups"].sub("cups.cup_l").spread(51.0, 0.0, 0.4, by=2)
    Hm["cups"].sub("cups.cup_r").spread(51.39, 0.0, 0.4, by=2)
    for names, t0, d in ((("lamp",), 54.85, 0.45), (("cups",), 55.0, 0.3), (("window.curtain", "window.rail"), 55.1, 0.45),
                         (("window",), 55.2, 0.5), (("chair_l", "chair_r"), 55.15, 0.5), (("chair_m",), 55.3, 0.45),
                         (("table.cloth", "table.leg_fl", "table.leg_fr"), 55.35, 0.45), (("table.leg_l", "table.leg_r"), 55.45, 0.42),
                         (("table.top",), 55.5, 0.43)):
        for it in Hm.all().sub(*names):
            if it.off is None:
                it.off = (t0, t0 + d)
