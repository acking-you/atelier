"""s05_pre2   115.77 - 138.20   p2a, p2b          B4  ->  B5

The two pre-choruses again, heavier. School: a ring of turned backs, a whisper that passes behind the
child, its voice that leaves it and circles a lamp like a moth, two backs that un-draw under its
hand. Home: the ring unrolls into one line, the line is the family's line, the two tall ones slide
away, the lines slip, the child is left with the two halves of its drawing under a cloud that swells.

CUE SHEET (song's clock; lines by 0-based LRC index, paraphrased; no lyric text)
  115.77        B4: the first frame is S.handoff(F, "B4"): bare sheet, the child planted at X4, the cloud
  p2a
  115.77 idx 33 (wherever it is, it is not there) six turned backs draw on round the child, one per half beat
                (115.77, 116.14, 116.52, 116.89, 117.27, 117.64), on either side in turn: in front of it, behind
                it, the last one near us on the left. The camera eases in (116.2 - 118.8) to the ring, head 133 px
  116.22        a look over its shoulder at the one that has appeared behind it
  116.9 - 118.1 a bare bulb is let down on its cord at the left, outside the ring (unlit)
  117.10        a small step closer to the two on its right; it leans to look in, a hand half raised (AC.s05)
  118.40 118.76 119.14  the whisper: a small knot of the black crayon hops from head to head: between the two
                on the right, BEHIND the child's head to the one behind it, on to the left. Its eyes go after it;
  118.98        it turns round after it (0.52 s, toward us): on its left too there are only backs. The whisper fades
  119.3 - 119.8 the bulb lights
  119.79 idx 34 (its voice, like the cry of a lost insect) a breath, the mouth, two small tries: its voice leaves its
                mouth as a thin line, flies over the heads on the left and is at the lamp on 121.00; it circles it
                like a moth. Its eyes and its head follow it; a hand goes out after it (121.3 - 121.8) and sinks
  122.08 idx 35 (it knows it should make an effort) it turns back to the two on its right (0.5 s); a step;
  123.26        its hand is on the nearer back: the back un-draws from under the hand; the hand stays in the air
  124.76        a longer step, the hand on the next one: gone too. The arm drops, the head goes down
  125.14 - 126.24  behind it the moth's circling runs down; it sinks to the floor in the lamp's pool and lies still
  126.265       it walks out through the gap, a step a beat, head down; the camera travels with it (to 130.4). The
                cloud is heavy: it stays where the ring was, the strand between them goes taut
  127.01 - 127.76  what is left of the ring unrolls behind it into one long line across the frame
  p2b
  127.78 idx 37 the line is the family's line (home, as memory): it breaks into four arms, two tall
                drawn figures draw on to either side of the walking child (complete 129.26), each holding a hand
                out. Pale light comes up where they stand. The child arrives between them (129.27), turns to us
  130.20        they take its hands; it lifts them (130.7), looks up at the one, then the other: three hand in hand,
                the cloud left behind on its strand (head 123 px)
  131.85 idx 38 (the past that cannot be mended) the line parts: the two tall ones slide away to the two edges of
                the frame (to 134.0), their arms
                stretch into two long lines that the child holds, sunk low with its whole weight, trembling.
                The cloud comes after the child and is over it again (131.9 - 134.5); the pale light thins
  134.51 134.77 idx 39  the left line slips, the right line slips: it sits down hard (135.19); the cloud's belly lets
                go of its head. The two tall ones are taken back from their ends at the frame's edges (135.0 - 136.0)
  135.07        the two halves of the torn drawing fall out of its jumper; the camera closes in (135.35 - 136.45,
                head 153 px). It gathers them (135.53), holds them together on its knees and looks (136.2 - 136.5),
                takes them to its chest (gone by 136.93). The cloud swells and comes down over it (135.1 - 137.6)
  136.93        it stands up under the cloud and lifts it; the camera eases back to the hand-off's
  137.88        the hold of B5 (AC.s05's last move ends two frames earlier than written: stand = 136.933)
  137.95        B5: S.joined draws S.handoff(F, "B5"): the child at X5, head down, the large cloud

THE PERFORMANCE   AC.s05 with backs = the two it touches, its cue table shifted (CUES), and three things of this
                  scene laid over it: the look over its shoulder, the two turns (AC.s05 is written facing right: for
                  the turn to the left it is played mirrored, swap_sides, with the moth mirrored about the child).
THE RING          six people.person_sketch at chosen places and depths (RING), not people.ring_of_backs.
THE SCRIBBLE      S.scribble's own calls (_scribble) with more heads the loops keep off, a strand that reaches
                  the cloud when the child has walked out from under it, and the belly's weight as a number.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from hx import story
from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk import acting_child as AC

from . import _shared as S

SPAN = (115.77, 138.20)
START, END = "B4", "B5"

X4, X5, FLOOR = story.X4, story.X5, story.FLOOR

# ---------------------------------------------------------------------------------------------
# the cues (song's clock)
# ---------------------------------------------------------------------------------------------
RING_T0, RING_EVERY, RING_DUR = 115.765, 0.375, 0.46     # a back per half beat from the bar
GLANCE = (116.22, 116.55, 116.85, 117.18)                # a look over its shoulder at the one behind it
LAMP_DOWN = (116.9, 118.1)
WH = (118.40, 118.76, 119.14)                            # the whisper's three hops (measured attacks)
TURN_L = (118.98, 119.50)                                # it turns round after the whisper (to the backs on its left)
LAMP_LIT = (119.3, 119.79)
T_SPEAK, T_MOTH = 119.79, 121.0                          # LRC 34; the voice is at the lamp on the strong attack
TURN_R = (122.08, 122.58)                                # it turns back to the backs on its right (LRC 35)
T_TOUCH = (123.26, 124.76)
T_FALL = (125.14, 126.24)                                # the moth gives up circling and sinks
T_UNROLL = (127.01, 127.76)
T_FAMILY = (127.78, 129.26)
T_JOIN = (130.20, 130.72)                                # the two tall ones take its hands
T_PART = (131.85, 134.0)
T_SLIP = (134.51, 134.77)
_2F = 2.0 / 30.0
# AC.S05_T shifted: the hand that went after the moth sinks as it turns back; the last two cues two frames
# early, so that the performance IS hold_B5 on this module's last own frame. sheet: the halves a little larger.
CUES = dict(touch=T_TOUCH, slip=T_SLIP, part=T_PART, effort=122.0, gather=135.6 - _2F, stand=137.0 - _2F, sheet=0.6)

# ---------------------------------------------------------------------------------------------
# places (world)
# ---------------------------------------------------------------------------------------------
# the ring: name, x from X4, depth (-1 far .. +1 near), face, seed, build (taller, shorter); in the order they draw
# on. An arc on the floor round the child: behind it the far ones (smaller, their feet higher, dimmer), on the left
# it comes forward to a near one; the two on the right are the two it will reach for; nobody stands in front of them.
RING = (("r1", 195.0, -0.70, 1, 1734, 0.97),
        ("l1", -218.0, -0.60, -1, 1768, 1.05),
        ("r2", 338.0, -0.05, 1, 1717, 1.02),
        ("l2", -345.0, 0.00, -1, 1785, 0.95),
        ("b", -96.0, -1.00, -1, 1751, 1.04),
        ("l3", -428.0, 0.70, -1, 1802, 1.00))
PAINT = ("b", "r1", "l1", "r2", "l2")                    # far to near, behind the child; l3 is drawn after it
TOUCHED = ("r1", "r2")
WHISPER = ("r2", "r1", "b", "l1")                        # the heads the whisper visits
HOPS = (0.36, 0.10, 0.34)                                # how high each hop arcs (the second passes behind the child's head)
W_DUR, W_LEAD, W_TAIL, W_SIZE = 0.30, 0.35, 0.60, 56.0
LAMP_X, LAMP_TOP, LAMP_DROP = X4 - 600.0, -220.0, 480.0  # the bulb hangs left of the ring, clear of the cloud
LINE_Y = 552.0                                           # the long line the ring unrolls into
WAIT = 112.6, FLOOR - 186.0                              # where the tall ones hold a hand out (people.family_line's own)
_HEADS = ("family.a.head", "family.a.hair0", "family.a.hair1", "family.a.hair2", "family.a.eye_l", "family.a.eye_r", "family.a.mouth",
          "family.b.head", "family.b.hair", "family.b.eye_l", "family.b.eye_r", "family.b.mouth")

C_RING = Cam(X4 - 145.0, 488.0, 1.13)                    # the lamp in the left third, the child right of the middle
C_FAM = Cam(X5, 500.0, 1.04)                             # the family: at the end the tall ones are cut by the frame's edges
C_FALL = Cam.at(X5 + 14.0, 600.0, 1.3, 960.0, 610.0)     # the halves


# ---------------------------------------------------------------------------------------------
# the ring of backs
# ---------------------------------------------------------------------------------------------
def _leans(t):
    """{name: (signed lean in x, amount)} while the whisper passes: who passes it on leans toward the next one,
    who gets it leans in to take it and straightens again (the timing of people.ring_of_backs)."""
    out = {}
    xs = {nm: dx for nm, dx, *_ in RING}
    for i, th in enumerate(WH):
        g, k = WHISPER[i], WHISPER[i + 1]
        give = ease(seg(t, th - 0.26, th - 0.02)) * (1.0 - ease(seg(t, th + 0.6 * W_DUR, th + W_DUR + 0.30)))
        take = 0.8 * ease(seg(t, th - 0.06, th + 0.8 * W_DUR)) * (1.0 - ease(seg(t, th + W_DUR + 0.16, th + W_DUR + 0.62)))
        for me, other, am in ((g, k, give), (k, g, take)):
            if am > 0.0:
                lx, la = out.get(me, (0.0, 0.0))
                out[me] = (lx + am * (1.0 if xs[other] >= xs[me] else -1.0), min(1.0, la + am))
    return out


def _ring(t=None, tb=None):
    """{name: People}: the six, each a people.person_sketch with its draw-on (and un-draw) times. t: the song's time
    (None: as they stand, without times); tb: the boil clock of their small shifts of weight."""
    leans = _leans(t) if t is not None else {}
    out = {}
    for k, (nm, dx, d, face, sd, build) in enumerate(RING):
        lx, la = leans.get(nm, (0.0, 0.0))
        view = max(-1.0, min(-0.30, math.asin(d) / (math.pi / 2.0) - 0.30))          # -1 from behind .. -0.3 a shoulder to us
        P = P_REST.but(neck=0.05 + 0.10 * rnd(sd, 3) + 0.10 * la, bend=0.04 + 0.10 * rnd(sd, 4) + 0.08 * la, lean=0.03 * rnd(sd, 5),
                       ff=(0.030 + 0.02 * rnd(sd, 6), 0.0), fb=(-0.034 - 0.02 * rnd(sd, 7), 0.0))
        tilt = 0.02 * (1.0 if dx > 0 else -1.0) * abs(view) + 0.02 * rsym(sd, 8) + 0.058 * lx * (0.45 + 0.55 * abs(view))
        head = 0.10 * rsym(sd, 10)
        if tb is not None:                               # alive: a slow shift of weight, a head that turns a little
            tilt += 0.010 * math.sin(tb * 0.83 + 6.28 * rnd(sd, 11))
            head += 0.05 * math.sin(tb * 0.51 + 6.28 * rnd(sd, 12))
        h = 342.0 * (1.0 + 0.135 * d) * build
        p = person_sketch(X4 + dx, FLOOR + 56.0 * d, h, P, "pupil", face, sd, 1.0, back=-view, head=head, tilt=tilt,
                          far=0.34 * (1.0 - d), name=nm)
        if t is not None:
            p.spread(RING_T0 + RING_EVERY * k, 0.0, RING_DUR, by=1)
        out[nm] = p
    if t is not None:
        for nm, th in zip(TOUCHED, T_TOUCH):             # the back goes from under the hand, outward
            undraw(out[nm], out[nm].who[0]["back"], th, 1.1)
    return out


@lru_cache(maxsize=1)
def _backs():
    """The two points the child's hand goes to (between the shoulders of the two on its right)."""
    R = _ring()
    return tuple((float(R[nm].who[0]["back"][0]), float(R[nm].who[0]["back"][1])) for nm in TOUCHED)


def _there(t, k):
    """0..1: how much of ring person k stands there (its shadow; the cloud's loops that keep off its head)."""
    nm = RING[k][0]
    t0 = RING_T0 + RING_EVERY * k
    th = T_TOUCH[TOUCHED.index(nm)] if nm in TOUCHED else T_UNROLL[0]           # the rest go as the ring unrolls
    return ramp(t, t0 + 0.1, t0 + 0.7) * (1.0 - ramp(t, th, th + 0.6))


def _whisper(F, R, t):
    """The whisper: people.whisper on this scene's perches: beside a head, on the side of the one it goes to next,
    low enough to be clear of the cloud. Drawn before the child: its second hop passes behind the child's head."""
    t0, t1 = WH[0] - W_LEAD, WH[-1] + W_DUR + W_TAIL
    if t < t0 or t > t1:
        return
    grow = seg(t, t0, t0 + 0.22) * (1.0 - seg(t, t1 - 0.3, t1))
    i = sum(1 for th in WH if t >= th + W_DUR)

    def perch(j):
        w = R[WHISPER[j]].who[0]
        sg = -1.0 if j + 1 >= len(WHISPER) else (1.0 if R[WHISPER[j + 1]].who[0]["head"][0] >= w["head"][0] else -1.0)
        return np.array([w["head"][0] + sg * 0.78 * w["R"], w["head"][1] - 0.50 * w["R"]])

    if i < len(WH) and t >= WH[i]:
        whisper(F, perch(i), perch(i + 1), (t - WH[i]) / W_DUR, 5 + i, W_SIZE, grow, hop=HOPS[i])
    else:
        whisper(F, perch(i), perch(i), 0.0, 5 + max(0, i - 1), W_SIZE, grow)


# ---------------------------------------------------------------------------------------------
# the lamp and the moth
# ---------------------------------------------------------------------------------------------
BULB = (LAMP_X, LAMP_TOP + LAMP_DROP + 26.25)            # the bulb's middle when it hangs (things.hanging_lamp)


def _way():
    mx, my = _mouth0()
    return dict(come=(mx, my, T_SPEAK, T_MOTH), fall=T_FALL)


def _moth_xy(t):
    return BULB if t < T_SPEAK else moth_path(t, BULB[0], BULB[1], 80.0, **_way())[:2]


# ---------------------------------------------------------------------------------------------
# the child: AC.s05, the look over its shoulder, the two turns
# ---------------------------------------------------------------------------------------------
def _pose(t, moth=None):
    """(the Act of AC.s05, the pose to draw). While the child faces left the performance is played mirrored: its
    moth is mirrored about the child (it stands at xm from the step closer to the first touch) and the pose is
    swap_sides: the same picture as drawing it with face = -1."""
    b = _backs()
    xm = X4 + 0.5 * (b[0][0] - 120.0 - X4)
    if moth is None:
        moth = _moth_xy(t)
    a = AC.s05(t, backs=b, moth=(2.0 * xm - moth[0], moth[1]), **CUES)
    P = a.pose
    if GLANCE[0] < t < GLANCE[3]:                        # a look over its shoulder at the one behind it: eyes, then the head
        k = seg(t, GLANCE[0], GLANCE[1]) * (1.0 - seg(t, GLANCE[2], GLANCE[3]))
        P = AC.look_at(P, a.x, a.y, (X4 + RING[1][1], FLOOR - 300.0), a.h, 1, k, 1.0)
        P = P.but(brow=P["brow"] + 0.25 * k)
    if TURN_L[0] < t < TURN_R[1]:
        P0, PL = P, swap_sides(P)
        if t < TURN_L[1]:
            w = seg(t, *TURN_L)
            P = turn_round(P, PL, w)
        elif t <= TURN_R[0]:
            w = None
            P = PL
        else:
            w = seg(t, *TURN_R)
            P = turn_round(PL, P, w)
        P = _planted(P, P0, a, w)
    st = CUES["stand"]
    if st < t < STAND_FEET:                              # it stands up over its feet: they do not swing out and back
        P = _stand_feet(P, a, ease(seg(t, st, STAND_FEET)))
    return a, P


STAND_FEET = 137.6                                       # AC.s05's feet are at B5's places from 137.58


@lru_cache(maxsize=1)
def _stand_ends():
    """The ankles where it sits (at the stand cue) and where it stands at B5 (world x)."""
    out = []
    for tt in (CUES["stand"], STAND_FEET):
        a = AC.s05(tt, backs=_backs(), **CUES)
        out.append({k: float(a.J["an_" + k][0]) for k in "fb"})
    return tuple(out)


def _stand_feet(P, a, w):
    """AC.s05's stand slides both feet on the floor 32 units forward and back again; here they go straight (and
    hardly at all) from where they were sitting to where B5 has them."""
    s0, s1 = _stand_ends()
    J = pose_joints(P, a.x, a.y, a.h, 1)
    for k in "fb":
        P = aim_foot(P, k, ((s0[k] + (s1[k] - s0[k]) * w - a.x) / a.h, (a.y - J["an_" + k][1]) / a.h))
    return P


def _planted(P, P0, a, w):
    """The feet of the turn and of the mirrored stretch kept where AC.s05's own feet are (P0, facing right). turn_round
    moves the ankles in the picture over the whole turn, though each foot is up only in its half (near foot w 0..0.5,
    far foot 0.5..1), and swap_sides drawn with face = +1 moves both feet with the pelvis (by 2 pel x): either way a
    foot that is down slides. Each ankle goes to its own place in P0; while a foot is up it keeps the turn's arc."""
    J, J0 = pose_joints(P, a.x, a.y, a.h, 1), pose_joints(P0, a.x, a.y, a.h, 1)
    for k, (u0, u1) in (("f", (0.0, 0.5)), ("b", (0.5, 1.0))):
        X, Y = J["an_" + k]
        X0 = J0["an_" + k][0]
        air = 0.0 if w is None else math.sin(math.pi * seg(w, u0, u1)) if u0 < w < u1 else 0.0
        P = aim_foot(P, k, ((X0 + (X - X0) * air - a.x) / a.h, (a.y - Y) / a.h))
    return P


@lru_cache(maxsize=1)
def _mouth0():
    """Where its mouth is when the voice leaves it (the moth's way starts here)."""
    a, P = _pose(T_SPEAK, moth=BULB)
    J = pose_joints(P, a.x, a.y, a.h, 1)
    return (float(J["mouth"][0]), float(J["mouth"][1]))


@lru_cache(maxsize=8)
def _act(t):
    a, P = _pose(t)
    if P is a.pose:
        return a
    return AC.Act(P, a.x, a.y, 1, a.grab, a.draw, a.a, 1.0, None, dict(a.pts), a.num, a.h)


# ---------------------------------------------------------------------------------------------
# camera, cloud
# ---------------------------------------------------------------------------------------------
def _cam(t):
    c = Cam.ease(S.CAM[START], C_RING, seg(t, 116.2, 118.8))           # in to the ring
    c = Cam.ease(c, C_FAM, seg(t, 126.27, 130.4))                      # with the walk out, to the family's line
    c = Cam.ease(c, C_FALL, seg(t, 135.35, 136.45))                    # in on the halves
    return Cam.ease(c, S.CAM[END], seg(t, CUES["stand"], 137.85))      # back as it stands: the hand-off's camera


def _cloud(t):
    """(cx, cy, rx, ry), how far its belly rests on the crown, the strand's slack, how taut the strand pulls."""
    c4, c5 = story.HANDOFF[START]["cloud"], story.HANDOFF[END]["cloud"]
    q1, st = T_SLIP[1], CUES["stand"]
    g = ramp(t, 134.8, 137.6)                            # it swells (the hand follows the area, as at the hand-offs)
    away = ramp(t, 127.0, 128.2) * (1.0 - ramp(t, 133.0, 134.4))       # the child has walked out from under it
    cx = c4[0] + 80.0 * ramp(t, 127.2, 130.2) + (c5[0] - c4[0] - 80.0) * ramp(t, 131.9, 134.5)     # heavy: it comes late
    low = ramp(t, q1 + 0.3, 136.5) * (1.0 - ramp(t, st + 0.02, st + 0.78))        # it comes down over the sitting child
    cy = c4[1] + (c5[1] - c4[1]) * g - 35.0 * away + 95.0 * low
    # its belly: on the crown; it lets go as the child falls from under it, comes to rest on it again, is lifted as it stands
    k = (1.0 - away) * (1.0 - ramp(t, q1 + 0.02, q1 + 0.30) * (1.0 - 0.8 * ramp(t, 135.9, 136.8)) * (1.0 - ramp(t, st, st + 0.25)))
    taut = ramp(t, 127.8, 129.2) * (1.0 - ramp(t, 132.6, 134.0))
    return (cx, cy, c4[2] + (c5[2] - c4[2]) * g, c4[3] + (c5[3] - c4[3]) * g), k, 0.8 - 0.6 * taut, taut


def _scribble(F, cloud, J, k=1.0, slack=0.8, avoid=(), taut=0.0):
    """S.scribble's calls with what this scene adds: more heads the loops keep off, the belly's weight k, and a
    strand that ends in the cloud's near end when the child has walked out from under it (S.scribble ends it 40
    units right of the crown, wherever the cloud is), pulling at it. With k = 1, slack = 0.8, no avoid and
    taut = 0 these are exactly S.scribble(F, cloud, J)'s calls."""
    crown = J["crown"]
    xr = min(crown[0] + 40.0, cloud[0] + cloud[2] - 90.0)
    tug = (xr, crown[1] + 40.0, 0.16 * taut) if taut > 0.0 else None
    Tp = gloom(F, *cloud, a=1.0, rest=(crown[0], crown[1] + 6.0, k), avoid=[(J["head"][0], J["head"][1], J["R"])] + list(avoid), tug=tug)
    strand(F, crown, Tp.band.root(xr, 0.4), slack=slack, a=1.0, draw=1.0)
    gloom_dust(F, cloud[0] - 0.8 * cloud[2], cloud[0] + 0.8 * cloud[2], 0.0, band=Tp.band, a=0.5)
    return Tp


def child_on_screen(t):
    """Where the child's hips are on screen (for the strips of the proofs)."""
    a = _act(t)
    return _cam(t).to_screen(a.x, a.y - 0.42 * a.h)


# ---------------------------------------------------------------------------------------------
def draw(F):
    if S.joined(F, START, END):                          # the last 0.25 s: the hand-off picture B5
        return
    t = F.t
    a = _act(t)
    n = a.num
    F.cam = _cam(t)
    q0, q1 = T_SLIP

    # ---- light, before the ground line --------------------------------------------------------
    if LAMP_DOWN[0] < t < 131.0:                         # the bare bulb (out of the frame from 129.2)
        lit = ramp(t, *LAMP_LIT) * (1.0 - ramp(t, 127.4, 128.6))
        L = hanging_lamp(F, LAMP_X, LAMP_TOP, LAMP_DROP * ease_out(seg(t, *LAMP_DOWN), 2.2), lit=lit,
                         swing=0.045 * (1.0 - ramp(t, 117.6, 119.3)))          # it sways as it is let down, and comes to rest
        if lit > 0.0:
            shaft_dust(F, LAMP_X, 16.0, BULB[1] + 20.0, LAMP_X, L["half"], FLOOR, n=22, a=0.5 * lit)
    # the light of the family's line: a breath of pale light where the three stand; it thins as they part and
    # goes out with the lines
    fk = ramp(t, 128.3, 129.7) * (1.0 - 0.45 * ramp(t, 132.2, 134.2)) * (1.0 - ramp(t, q0, q1 + 0.7))
    if fk > 0.0:
        glow(F, X5, FLOOR - 250.0, 470.0, 330.0, col=light_col(F), a=0.16 * fk)
        light_pool(F, X5, FLOOR + 8.0, 430.0, a=0.34 * fk)
    S.rain_back(F)                                       # (no rain in this span: S.rain_k is 0)
    S.bare(F)

    # ---- the sets behind the child: the ring, the long line, the family's line -----------------
    near, front, avoid = None, None, []
    if t < T_FAMILY[0]:                                  # their shadows, and the loops kept off their heads: these go
        R = _ring(t, F.tb)                               # with the unroll (_there), not in one frame at its start
        for k, (nm, *_r) in enumerate(RING):
            kk = _there(t, k)
            if kk > 0.0:
                w = R[nm].who[0]
                ground_shadow(F, w["x"], w["y"] + 4.0, 0.25 * w["h"], 0.5 * kk)
                avoid.append((w["head"][0], w["head"][1], kk * S.HEAD_CLEAR * w["R"]))
    if t < T_UNROLL[0]:
        for nm in PAINT:
            R[nm].draw(F)
        _whisper(F, R, t)
        near = R["l3"]
    elif t < T_FAMILY[0]:                                # what is left of it unrolls into one long line
        Lg = long_line(X5 - 1100.0, X5 + 1100.0, LINE_Y, n=4)
        rest = Sketch([R[nm] for nm in ("b", "l1", "l2", "l3")])
        morph(rest, Lg, seg(t, *T_UNROLL), [(f"{nm}.body", f"line.s{k}") for k, nm in enumerate(("l3", "l2", "l1", "b"))]).draw(F)
    else:
        # the two hold a hand out; when the child stands between them they take its hands (T_JOIN); a line that
        # has slipped falls back from where the hand was when it slipped
        kj = ramp(t, *T_JOIN)
        hl, hr = _act(min(t, q0)).J["ha_f"], _act(min(t, q1)).J["ha_b"]
        ends = ((X5 - WAIT[0] + (hl[0] - X5 + WAIT[0]) * kj, WAIT[1] + (hl[1] - WAIT[1]) * kj),
                (X5 + WAIT[0] + (hr[0] - X5 - WAIT[0]) * kj, WAIT[1] + (hr[1] - WAIT[1]) * kj))
        Sf = family_line(X5, FLOOR, part=ease(seg(t, *T_PART)), slip=(seg(t, q0, q0 + 0.6), seg(t, q1, q1 + 0.6)),
                         hands=ends, small=False)
        if t < T_FAMILY[1]:                              # the line breaks into their arms; the rest of them draws on
            Lg = long_line(X5 - 1100.0, X5 + 1100.0, LINE_Y, n=len(Sf.chain))
            M = morph(Lg, Sf, seg(t, *T_FAMILY), [(f"line.s{k}", nm) for k, nm in enumerate(Sf.chain)], stagger=0.3)
        else:
            Sf["family.a"].set_off(q0 + 0.50, q0 + 1.45)                # taken back from their ends at the frame's edges
            Sf["family.b"].set_off(q1 + 0.45, q1 + 1.35)
            M = Sf
        M.without(*_HEADS).draw(F)
        front = M.sub(*_HEADS)                           # their heads are drawn over the cloud's end (after it)

    # ---- the child, what it holds, the scribble ------------------------------------------------
    J = S.child(F, a)
    if near is not None:
        near.draw(F)
    if n["halves"] > 0.0 and n["tuck"] < 1.0:
        family_held(F, a.pts["half_l"], a.pts["half_r"], s=n["sheet"], a=n["halves"] * (1.0 - n["tuck"]))
    cloud, k, slack, taut = _cloud(t)
    _scribble(F, cloud, J, k, slack, avoid, taut)
    if front is not None:
        front.draw(F)

    # ---- its voice: the thin line and the moth (in front of everything) ------------------------
    if T_SPEAK <= t < 131.0:
        x, y, hd = moth_trail(F, t, BULB[0], BULB[1], 80.0, dur=1.0, a=0.75, lw=2.7, **_way())
        moth(F, x, y, hd, s=1.25, a=ramp(t, T_SPEAK, T_SPEAK + 0.2), beat=1.0 - 0.85 * ramp(t, T_FALL[1] - 0.3, T_FALL[1] + 0.1))
    S.rain_front(F)
