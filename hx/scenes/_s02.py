"""hx.scenes._s02: what s02_pre1 builds for itself (a helper, not a scene: the registry skips it).

    turn(w, K, L)        the room turning into the classroom of this staging: the kit's between()
                         with this scene's own pairs and plan (the kit's room_to_class has the desk
                         that stands apart come out of the sofa, 950 units away across the child)
    street(x)            a street lamp and a kerb (the kit has none): a Sketch; street_light() its cone
    voice_pts(...)       the voice line as points; voice() draws it leaving the mouth, falling short,
                         drooping, going dark and being wound up the strand into the scribble
                         (the kit's things.voice_line lies down on the floor and is faded out)
    adults(...)          people.home_adults' seated pair with their own draw-on, a walk that takes them
                         out of a close frame (a step a half beat) and their own rub-out times
    scribble(...)        S.scribble's own three calls with two more arguments (where the strand ends
                         in the cloud, heads the loose loops keep off)

World coordinates through F.cam; a frame is a pure function of time; no lyric text anywhere.
"""
from __future__ import annotations

import math

import numpy as np

from hx import story
from hx.chalk import *                                   # noqa: F401,F403

from . import _shared as S

FLOOR = story.FLOOR
T0, BEAT = 36.265, 0.75                                  # the bar line the span starts on; a beat
PALE = (0.80, 0.84, 0.92)                                # cold lamp light (sets.md: never amber)

# ---------------------------------------------------------------------------------------------
# the room turning into the classroom (36.27 to 38.6)
# ---------------------------------------------------------------------------------------------
SPAN_TURN = (T0, 38.6)
FRAME = ("window.frame", "window.inner", "window.mullion", "window.transom", "window.sill", "window.ledge")
# only these travel, each between things that stand near each other:
TURN_PAIRS = (
    ("table.top", "lone.desk.top"), ("table.cloth", "lone.desk.box"),                                               # the table: the desk that stands apart
    ("table.chair_l.seat", "rowsL.b2.seat"),                                                                        # its pulled-away chair: the chair of the last back it passes
    ("sofa.arm_l", "rowsL.f0.desk.top"), ("sofa.seat", "rowsL.f1.desk.top"), ("sofa.arm_r", "rowsL.f2.desk.top"),  # the sofa: the desks of the rows it trudges past
    ("sofa.back", "rowsL.b1.desk.top"),
    ("pic.l.sheet", "board.frame"), ("pic.r.sheet", "board.ledge"),                                                 # the drawing on the wall: the board
    ("lamp.pole", "door.frame"), ("lamp.shade", "door.pane"), ("cushion.shape", "clock.rim"),                       # the kit's own
    ("shelf.book0", "pins.sheet0"), ("shelf.book1", "pins.sheet1"), ("shelf.book2", "pins.sheet2"),
)
# the order the turning picture is painted in: at w = 0 it is the room's own paint order
TURN_ORDER = ("-wall", "window", "-window", "-lamp", "-shelf", "-table", "-rug", "-pic", "<phone>", "-sofa", "-cushion",
              "wall", "board", "clock", "pins", "door", "lamps", "rowsL", "lone")


def _b(k: float, n: float = 1.0):
    """A window in w of the turn: k beats after its start, n beats long."""
    d = (SPAN_TURN[1] - SPAN_TURN[0]) / BEAT
    return (k / d, min(1.0, (k + n) / d))


def _turn_plan():
    b = _b
    return (
        # beat 0 (36.27): the room lets go, the soft things first; its wall lines hold it together a beat longer
        (*b(0.0, 0.9), "-window.curtain", "-window.rail"), (*b(0.1, 0.9), "-rug"),
        (*b(0.15, 0.9), "-sofa.throw", "-sofa.fringe", "-sofa.split", "-sofa.roll_l", "-sofa.roll_r", "-sofa.leg_l", "-sofa.leg_r"),
        (*b(0.2, 0.8), "-pic"), (*b(0.45, 1.0), "-table"), (*b(0.4, 0.9), "-cushion", "-lamp", "-shelf", "-sofa"), (*b(0.9, 1.0), "-wall"),
        # what travels: the sofa into the desks of the rows (from 36.6), the drawing into the board, the table into the desk that stands apart
        (*b(0.5, 1.0), "rowsL.f0.desk.top", "rowsL.f1.desk.top", "rowsL.f2.desk.top", "rowsL.b1.desk.top"),
        (*b(0.55, 1.0), "board.frame", "board.ledge"),
        (*b(0.7, 1.1), "lone.desk.top", "lone.desk.box", "rowsL.b2.seat"),
        (*b(0.6, 0.9), "clock.rim"), (*b(0.6, 0.9), "door.frame", "door.pane"), (*b(0.8, 1.0), "pins.sheet0", "pins.sheet1", "pins.sheet2"),
        # what draws on: a pupil about every quarter beat from just before beat 1, the dado, the lamps one by one, the board's writing
        (*b(0.9, 0.9), "+rowsL.b0"), (*b(1.1, 0.9), "+rowsL.f0"), (*b(1.3, 0.9), "+rowsL.b1"), (*b(1.5, 0.9), "+rowsL.f1"),
        (*b(1.75, 0.9), "+rowsL.b2"), (*b(2.0, 0.9), "+rowsL.f2"),
        (*b(1.45, 1.0), "+board"), (*b(1.0, 1.2), "+wall"), (*b(1.6, 0.9), "+lone"), (*b(1.3, 0.8), "+clock"), (*b(1.3, 0.8), "+door"),
        (*b(1.2, 0.5), "+lamps.lamp0"), (*b(1.7, 0.5), "+lamps.lamp1"), (*b(2.2, 0.5), "+lamps.lamp2"), (*b(1.8, 0.8), "+pins"),
    )


def turn(w: float, K, L):
    """The room (night, where it stands) turning into the classroom K with the rows L that the child
    trudges past: (the room, {group: Sketch}). Draw the groups in TURN_ORDER (the phone lies between
    "-pic" and "-sofa"); the room's and the classroom's dressing, light and views are the scene's.
    At w = 0 it is the room of hand-off B1 with the family drawing on its wall, stroke for stroke."""
    R = room("night")
    A_ = dict(R)
    A_["pic"] = wall_drawing(*story.WALL_DRAWING)
    B_ = dict(K)
    B_["rowsL"] = Sketch(L.items)
    return R, between(A_, B_, w, TURN_PAIRS, _turn_plan(), keep=FRAME)


# ---------------------------------------------------------------------------------------------
# the street between school and home: a lamp and a kerb
# ---------------------------------------------------------------------------------------------
LAMP_H = 448.0                                           # the post


def lantern_at(x: float):
    """Where the lantern hangs (the middle of its rim) for a post standing at world x."""
    return x + 92.0, FLOOR - LAMP_H + 24.0


def street(x: float, kerb=(-330.0, 110.0)) -> Sketch:
    """A street lamp as a child draws one (a foot, a tall post, a neck bent over toward home, a small
    lantern) standing on the ground line at world x, and the kerb under it from x + kerb[0] to
    x + kerb[1]: a second line a little in front of the ground line, and the joints of its stones.
    Parts: lamp.foot lamp.post lamp.neck lamp.hood (+ .fill) lamp.bulb, kerb.edge kerb.j0-5."""
    c, d = mix(C.CHALK_COOL, C.CHALK_DIM, 0.45), C.CHALK_DIM
    top = FLOOR - LAMP_H
    lx, ly = lantern_at(x)
    hood = A((lx - 27, ly), (lx - 15, ly - 24), (lx + 13, ly - 25), (lx + 27, ly - 1), (lx - 27, ly))
    it = [
        closed(A((x - 17, FLOOR), (x - 9, FLOOR - 30), (x + 9, FLOOR - 31), (x + 16, FLOOR), (x - 17, FLOOR)), d, 3.4, 0.9, 3101, "lamp.foot", wob=0.6),
        Stroke(A((x, FLOOR - 28), (x + 3, FLOOR - 170), (x - 2, FLOOR - 330), (x, top)), c, 5.4, 0.95, 3102, "lamp.post", taper=0.75),
        Stroke(spline(A((x, top), (x + 5, top - 34), (x + 42, top - 50), (x + 80, top - 34), (lx, ly - 24)), 14), c, 4.6, 0.95, 3103, "lamp.neck", taper=0.7),
        Fill(hood, (0.30, 0.35, 0.50), 0.3, 6.0, 4.0, 0.5, 3104, knock=C.KNOCK, base=0.5, name="lamp.hood.fill"),
        closed(hood, c, 3.8, 0.95, 3105, "lamp.hood", wob=0.6),
        Stroke(arc(lx, ly + 2, 12, 10, 0.15, math.pi - 0.15, 8), mix(c, C.CHALK, 0.4), 3.0, 0.9, 3106, "lamp.bulb", wob=0.3),
    ]
    x0, x1 = x + kerb[0], x + kerb[1]
    it.append(Stroke(A((x0, FLOOR + 17), ((x0 + x1) / 2, FLOOR + 19), (x1, FLOOR + 17)), c, 3.6, 0.85, 3110, "kerb.edge", taper=0.9, step=12.0))
    for j in range(6):
        xj = x0 + (x1 - x0) * (j + 0.6 + 0.25 * rsym(3120 + j, 1)) / 6.0
        it.append(line(xj, FLOOR + 3, xj - 6, FLOOR + 17, d, 3.0, 0.85, 3120 + j, f"kerb.j{j}"))
    return Sketch(it)


def street_light(F: Frame, x: float, lit: float) -> None:
    """The lamp's cold cone and its pool on the ground (before the ground line and the figures)."""
    if lit <= 0.003:
        return
    lx, ly = lantern_at(x)
    shaft(F, lx, 16, ly + 6, lx - 8, 170, FLOOR + 10, col=PALE, a=0.30 * lit, alphas=(1, 0.7, 0.5, 0.32), top=0.12)
    light_pool(F, lx - 8, FLOOR + 22, 210, 34, col=PALE, a=0.26 * lit)
    glow(F, lx, ly + 10, 70, 58, col=PALE, a=0.34 * lit)


# ---------------------------------------------------------------------------------------------
# the voice line (40.3 to 42.6)
# ---------------------------------------------------------------------------------------------
VOICE_SEED = 860                                         # the kit's (things.voice_line): the same hand


def voice_pts(tb: float, mouth, aim, w: float, droop: float = 0.0, reach: float = 0.72, amp: float = 1.0, seed: int = VOICE_SEED):
    """The voice as a world polyline, the mouth first: things.voice_line's own line (its wander, its
    fine shiver, the bursts that travel out along it and never arrive) toward `aim`, stopping at
    `reach` of the way. w: 0..1 how far it has come out. droop: 0..1 it gives up IN THE AIR: from the
    far end back it loses its waver and sinks, hanging in a belly (it does not lie down on the floor:
    in this staging the desks of the rows stand there). tb: the clock of its wavering (F.tb)."""
    x0, y0 = mouth
    dx, dy = aim[0] - x0, aim[1] - y0
    D = math.hypot(dx, dy) + 1e-9
    ex, ey = dx / D, dy / D
    L = D * reach * (0.5 * w + 0.5 * ease(w))
    n = max(12, int(L / 2.6))
    s = np.linspace(0.0, L, n)
    q = s / max(L, 1e-9)
    ph = rnd(seed, 3) * 40.0
    env = np.minimum(1.0, s / 70.0) * (1.0 - 0.55 * q ** 2)
    say = smooth((vn((s - 150.0 * tb) / 58.0 + ph, seed + 2) - 0.42) / 0.22) * np.minimum(1.0, s / 40.0) * (1.0 - q ** 3)
    wv = amp * (env * (15.0 * (2 * vn(s / 96.0 - tb * 0.55 + ph, seed) - 1) + 6.0 * (2 * vn(s / 31.0 - tb * 1.5 + ph, seed + 1) - 1))
                + say * 6.5 * np.sin(s / 3.3))
    sag = 0.08 * L * q ** 2
    if droop > 0.0:
        k = smooth((droop * 1.5 - (1.0 - q)) / 0.5)      # the far end first
        wv = wv * (1.0 - 0.55 * k)                       # the bursts die, a tired waver stays: still a voice, not a wire
        bend = np.clip((q - 0.30) / 0.70, 0.0, 1.0) ** 2.0          # it wilts like a stem: level by the mouth, bowed toward its end
        sag = sag + droop * L * (0.17 * bend + 0.035 * np.sin(math.pi * q) ** 2) + 0.03 * L * k * q
        s = s * (1.0 - 0.10 * droop * q ** 1.5)          # it hangs: its far end comes back a little
    return np.stack([x0 + ex * s - ey * wv, y0 + ey * s + ex * wv + sag], axis=1)


def _arclen(P):
    return np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])


def _at(P, u, s):
    return np.array([np.interp(s, u, P[:, 0]), np.interp(s, u, P[:, 1])])


def _cut(P, u, a, b):
    """The part of polyline P between arc lengths a and b (u = its arc lengths), or None."""
    a, b = max(a, 0.0), min(b, u[-1])
    if b - a < 1.0:
        return None
    q = np.linspace(a, b, max(2, int((b - a) / 3.0) + 1))
    return np.stack([np.interp(q, u, P[:, 0]), np.interp(q, u, P[:, 1])], axis=1)


def _thread(F: Frame, P, dark: float, a: float = 1.0, lw: float = 3.0, seed: int = VOICE_SEED, tip: bool = False):
    """The voice's line: the child's white chalk; as `dark` goes to 1 the pale edge of the scribble with its black inside."""
    c = mix(C.CHALK, C.GLOOM_EDGE, min(1.0, dark))
    lw = lw * (1.0 + 0.35 * dark)
    chalk(F, P, c, lw, a * (1.0 - 0.15 * dark), seed, wob=0.0, taper=0.25, edge=0.3, step=2.5, grain="dense")
    k = ramp(dark, 0.45, 1.0)
    if k > 0.0:
        chalk(F, P, C.GLOOM, lw * 0.6, a * k, seed + 1, wob=0.0, taper=0.3, edge=0.0, step=2.5, grain="dense")
    if tip:
        disc(F, P[-1, 0], P[-1, 1], lw * 0.8, mix(c, C.CHALK, 0.6), 0.95 * a, None, floor=1.3)


class Voice:
    """The voice at one instant: .air the part of it that is in the air (a polyline, or None), .far
    its far end, .wound the part that is on the strand (or None), .gone 0..1 how much of it has gone
    into the cloud. draw_air(F) after the child; draw_wound(F) after the scribble."""

    def __init__(self, air, wound_, gone, dark, tip, lw):
        self.air, self.wound, self.gone, self.dark, self.tip, self.lw = air, wound_, gone, dark, tip, lw
        self.far = None if air is None else (float(air[-1, 0]), float(air[-1, 1]))

    def draw_air(self, F: Frame) -> None:
        if self.air is not None:
            _thread(F, self.air, self.dark, 1.0, self.lw, tip=self.tip)

    def draw_wound(self, F: Frame) -> None:
        if self.wound is not None:
            chalk(F, self.wound, C.GLOOM_EDGE, self.lw * 1.3, 0.85, VOICE_SEED + 2, wob=0.0, taper=0.3, edge=0.25, step=2.0, grain="dense")
            chalk(F, self.wound, C.GLOOM, self.lw * 0.8, 0.95, VOICE_SEED + 3, wob=0.0, taper=0.3, edge=0.0, step=2.0, grain="dense")


def voice(tb: float, mouth, aim, w: float, droop: float = 0.0, dark: float = 0.0, wind: float = 0.0, crown=None, strand_=None,
          head=None, reach: float = 0.72, amp: float = 1.0, lw: float = 3.0) -> Voice:
    """The child's voice (things.voice_line's line) as a Voice.

    w: 0..1 it leaves the mouth toward `aim` and falls short. droop: 0..1 it gives up in the air.
    dark: 0..1 it turns dark. wind: 0..1 it is wound up: its mouth end lets go of the lips, goes up
    before the brow (head = (x, y, R): never across the face) to the crown and runs up the strand
    (strand_: the strand's polyline, crown first) into the scribble; the rest of it follows along
    its own way, its far end coming home last; at 1 the last of it is in the cloud. tb: F.tb."""
    if w <= 0.0 or wind >= 1.0:
        return Voice(None, None, 1.0 if wind >= 1.0 else 0.0, dark, False, lw)
    P = voice_pts(tb, mouth, aim, w, droop, reach, amp)
    if wind <= 0.0:
        return Voice(P, None, 0.0, dark, w < 1.0 and droop <= 0.0, lw)
    back = P[::-1]                                       # the way home: its far end first
    ub = _arclen(back)
    Lv = float(ub[-1])
    m, c, SP = back[-1], np.asarray(crown, dtype=np.float64), np.asarray(strand_, dtype=np.float64)
    r = min(0.5 * Lv, 90.0 * ramp(wind, 0.0, 0.2))       # the short cut it takes past the mouth once its end has let go
    pa, pre = _at(back, ub, Lv - r), _at(back, ub, max(0.0, Lv - r - 40.0))
    hx, hy, hr = head
    ang = math.atan2(c[1] - hy, c[0] - hx)               # where the crown is on the head (y down: about -0.9 on a head that hangs)
    rim = lambda q, d: (hx + (hr + d) * math.cos(q), hy + (hr + d) * math.sin(q))
    ctrl = np.array([pre, pa, rim(0.08, 20.0), rim(0.5 * ang + 0.04, 15.0), rim(0.82 * ang, 9.0), c])
    curve = spline(ctrl, 51)[10:]                        # from where it leaves its old way, up round the brow, onto the crown
    j = int(np.searchsorted(ub, Lv - r))
    way = np.vstack([back[:j], curve, SP[1:]])
    u = _arclen(way)
    Lw, Ls = float(u[-1]), float(_arclen(SP)[-1])
    head = (Lv - r) + wind * (Lw - (Lv - r) + Lv)        # where its leading end is along the way
    air = _cut(way, u, head - Lv, min(head, Lw - Ls))
    on = _cut(way, u, max(head - Lv, Lw - Ls), min(head, Lw))
    if on is not None:                                   # wound round the strand, turning as it runs up
        q = np.linspace(max(head - Lv, Lw - Ls), min(head, Lw), len(on))
        tx, ty = np.gradient(on[:, 0]), np.gradient(on[:, 1])
        nn = np.hypot(tx, ty) + 1e-9
        tw = 5.5 * np.sin((q - head) / 4.2) * np.minimum(1.0, (q - (Lw - Ls)) / 14.0)
        on = on + np.stack([-ty / nn * tw, tx / nn * tw], axis=1)
    return Voice(None if air is None else air[::-1], on, float(min(1.0, max(0.0, (head - Lw) / Lv))), dark, False, lw)


# ---------------------------------------------------------------------------------------------
# the two adults at the home table
# ---------------------------------------------------------------------------------------------
ADULT_GO = (53.14, 53.505)                              # each one's first step away: one on each tear
ADULT_RATE = 2.0 * STEP_RATE                             # a step a half beat: an adult's ordinary gait beside the child's trudge


def adult_walk(t: float, x1: float, face: int, h: float, go: float, m: float = 0.4):
    """One adult walking away from standing at world x1 (from `go`, a step a half beat): (pose, x, t0)."""
    W = walk_to(t, x1, x1 + face * 1100.0, h, start=go, m=m, rate=ADULT_RATE, rest=P_AWAY, rest0=P_AWAY)
    return W.pose, W.x, W.t0


def adults(F: Frame, xl: float, xr: float, seat_y: float, draw=(1.0, 1.0), leave: float = 52.36, off=((54.0, 54.6), (54.15, 54.75)),
           y: float = FLOOR, hl: float = 545.0, hr: float = 528.0, seed: int = 2100):
    """people.home_adults' own seated pair (the same poses, seeds, heights, the same rising and turning
    away through the back), with what the kit's call does not take: each one's own draw-on (draw =
    (left, right), 0..1), a walk long enough to take them out of the frame (the kit's walk_off covers
    about 210 units in two seconds and leaves them in the middle of a close frame: here a step a half
    beat from ADULT_GO, 1100 units long) and WHEN each is rubbed out (off = ((t0, t1), (t0, t1)): as
    it reaches the frame's edge). Returns the joints of both (left, right)."""
    t = F.t
    out = []
    for i, (x0, face, h, kind) in enumerate(((xl, -1, hl, "coat"), (xr, 1, hr, "skirt"))):
        t0 = leave + 0.12 * i
        br = 0.004 * math.sin(F.tb * 2 * math.pi / (4.6 + 0.7 * i) + i) * (1.0 - seg(t, t0 - 0.6, t0))      # alive: a slow breath (boil clock)
        Ps = P_SIT.but(pel=(-0.02, (y - seat_y) / h + 0.035 + br), ff=(0.125, 0.0), fb=(0.090, 0.0), bend=P_SIT["bend"] - 4.0 * br)
        u = ease(seg(t, t0, t0 + RISE))                  # standing up, the feet where they were
        w = ease(seg(t, t0 + 0.12, t0 + RISE + 0.20))    # turning away, through the back: the turn ends as it steps off
        Pst = mixp(Ps, P_AWAY, u)
        x1 = x0 - face * h * (Ps["ff"][0] - P_AWAY["ff"][0])
        Pw, wx, w0 = adult_walk(t, x1, face, h, ADULT_GO[i])
        P, px = (Pw, wx) if t > w0 else (Pst, x0 - face * h * (Ps["ff"][0] - Pst["ff"][0]))
        fc, back = (-face, 2.0 * w) if w < 0.5 else (face, 2.0 * (1.0 - w))
        out.append(person(F, px, y, h, P, kind, fc, seed + i, draw=draw[i], back=back, off=seg(t, *off[i])))
    return tuple(out)


# ---------------------------------------------------------------------------------------------
# the scribble with two more arguments
# ---------------------------------------------------------------------------------------------
def scribble(F: Frame, cloud, J: dict, k: float = 1.0, slack: float = 0.8, root_dx: float = 40.0, avoid=(), tug=None,
             tremble: float = 0.0):
    """S.scribble's own three calls (the cloud resting on the crown, the strand, the dust) with two
    more arguments: root_dx, where the strand ends in the cloud (world units right of the crown; 40
    is the shared layer's), and avoid, more heads its loose loops keep off (S.clear_of). With the
    defaults it IS S.scribble (and calls it). Returns (the cloud's Tip, the strand's polyline)."""
    crown = J["crown"]
    if abs(root_dx - 40.0) < 1e-6 and not avoid and tremble <= 0.0:
        Tp = S.scribble(F, cloud, J, k=k, slack=slack, tug=tug)
        return Tp, strand_pts(crown, Tp.band.root(crown[0] + 40.0, 0.4), slack)
    Tp = gloom(F, *cloud, rest=(crown[0], crown[1] + 6.0, k), avoid=[(J["head"][0], J["head"][1], J["R"])] + list(avoid), tug=tug)
    P = strand(F, crown, Tp.band.root(crown[0] + root_dx, 0.4), slack=slack, tremble=tremble)
    gloom_dust(F, cloud[0] - 0.8 * cloud[2], cloud[0] + 0.8 * cloud[2], 0.0, band=Tp.band, a=0.5)
    return Tp, P
