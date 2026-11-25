"""s01_room   0.00 - 36.27   intro, v1a, v1b          (no start hand-off)  ->  B1

The night room draws itself with the piano; the child is drawn asleep on the sofa and the black
crayon scribbles its cloud over it; the wish (a caped hero on the wall) and its crossing-out; the
crows; the word that does not come and goes up into the scribble; the child stands beside the sofa.

CUE SHEET (lines by 0-based LRC index and time, paraphrased; no lyric text)
  intro 0.00 - 12.27    piano alone; bars at 0.27, 3.27, 6.27, 9.27
    0.00          the bare dark sheet
    0.27 - 1.00   the first note: the ground line, left to right, chalk dust sinking behind its tip
    0.4 - 3.1     the wall's hatch and the floorboards come up; skirting 1.23, cornice 1.58 (two soft notes)
    2.0 - 10.5    the title (screen space, cx 820: over the sofa, clear of the torn drawing and the curtain rail)
    3.27 - 6.2    the sofa, a stroke a beat: back 3.27, arms 4.02 / 4.39, seat 4.77, blanket 5.52, cushion 5.89; the rug
                  quietly under it (sets.room_on is the schedule); dust sinks from every fresh line (to 10.2)
    6.27 - 9.2    the window on the beats (frame 6.27, bars 6.64 / 7.02, sill 7.39, rail 7.77, curtains 7.95 / 8.33); the
                  pane and its light 7.0 - 8.4, rain behind the glass; quietly between the beats: the phone on the rug
                  7.0, the lamp, the two halves of the torn family drawing on two soft notes (7.22, 8.13), table, chairs, shelf
    8.52 - 9.04   the one window across the street is coloured in amber: the first and only warm thing
    9.27 - 11.3   the child is drawn, curled asleep on the sofa: back, limbs, jumper, head, hair, the face last
    11.0 - 11.95  the black crayon begins: a small tangle just over the sleeper, loop after loop (the very tangle
                  that is left on its string at the end of the film); from 11.5 the first loops of the mass round it
    camera        the whole room (zoom 0.95 creeping to 0.975); from 10.3 it eases in on the sofa (arrives 13.3)
  v1a 12.27 - 24.27
    12.27 idx 5   (it clings to the sofa, bleary, hair on end) the eyes open half (12.3 - 13.1; the head 140 to 150 px),
                  a look up at what hangs over it; the scribble gets more loops on the attack (12.27 - 13.1)
                  and piles up, the tangle is lifted into it; again on 13.29 (to 14.4), while the child clings to the armrest
    13.29, 14.52  two loose runs of the black crayon stray over its back and hip (rubbed out 16.3 - 18.0)
    14.87         the scribble sags (14.45 - 15.0) and lands: its belly on back and head; the head gives; the far hand
                  slides off the armrest and hangs
    16.47 idx 6   (it wishes it were as dashing as a film hero) the hand lifts beside its chin (16.04) and leads a thin
                  bright line on the wall above the armrest: the face of a small caped figure of itself (16.47), body
                  and fists (17.18), the cape (17.79), its fist toward the scribble; the scribble draws back from that
                  piece of wall (16.0 - 16.9) and lifts off the child's head; the wish gives a little pale light (on the
                  wall, a rim on the child's face); eyes, then the face go up to it: the first time the face lifts
    18.27 ..      the cape waves on the beats; 19.36 (strong attack) the mouth almost smiles, a light in the eyes
    20.79, 21.2, 21.6   three hard zigzags of the black crayon cross the hero out, the scribble lunging nearer with
                  each, each putting out a third of the light; a flinch at each; the eyes fall, it sinks back into the curl
    21.9 - 23.6   the hero and the zigzags are wiped: a rubbed ghost that fades
    22.0 - 24.2   it sits up slowly under the weight and hugs its knees; the scribble rises with it (22.0 - 24.4);
                  the camera eases back and to the right (21.9 - 24.3): the window, the table, the chairs pulled apart
  v1b 24.27 - 36.27
    24.27 idx 8   (crows lined up under the eaves, more and more) a crow lands on the wire on every beat (24.27 ..
                  28.02: six), the wire dips and swings; the child turns its head and watches, its eyes going to each
    28.6  idx 9   (feelings pressed down that it does not know how to say) a breath; 28.6 - 29.4 a speech balloon
                  draws itself out of its mouth (the loose loops of the scribble give way to it); three tries;
                  29.36, 29.70, 30.06 nothing comes into it but a knot of black scribble, a third on each attack;
                  30.3 - 30.6 the mouth shuts, the head drops; crows 29.5, 30.3
    31.58         the sleeve wipes the balloon away: the far hand goes up beside the face (31.2) and comes down through
                  the balloon (31.56 - 31.92); the knot stays, a thin dark strand runs out of the child's crown to it
                  (31.62 - 31.9), and it rises on the strand into the scribble (31.8 - 32.88), which swells (32.8 -
                  33.06): from here on the strand exists
    32.3 - 33.14  once more, smaller: the mouth opens, a small knot leaves it (32.42), goes round the head and up the
                  strand; the scribble swells again (33.12 - 33.4, B1's size); crows 32.3, 33.0, 33.8: eleven
    33.6 - 35.8   it slides off the seat and stands beside the sofa, head down; the scribble is dragged after it on
                  the taut strand (33.95 - 35.95) and settles on its crown; the camera goes back to the whole room
                  (33.6 - 36.0) and is still from 36.0
  B1 36.27        S.handoff(F, "B1") from 36.02: camera (960, 540, 1.0); the night room complete, rain on the pane,
                  eleven crows, the amber window; the child standing at X1 = 1040 (AC.hold_B1), the cloud
                  (1010, 236, 380 x 128) resting on its crown, the strand

NOT IN IT         the storyboard's "pulls the cushion closer" (12.34): the cushion lies at the other end of the sofa;
                  the performance clutches the armrest instead (AC.s01).
"""
import math

import numpy as np

from hx import story
from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk import acting_child as AC

from . import _shared as S

SPAN = (0.00, 36.27)
START, END = None, "B1"

FLOOR = story.FLOOR
B1C = story.HANDOFF["B1"]["cloud"]                       # (1010, 236, 380, 128)
HAND = math.sqrt(B1C[2] * B1C[3] / (430.0 * 150.0))      # the scribble's hand at B1 (gloom's own rule), kept all through
TITLE_CX = 820.0                                         # clear of the torn drawing (screen x 1069 on) and of the curtain rail

# ---- cameras ------------------------------------------------------------------------------------
CAM_W0 = Cam(960.0, 540.0, 0.95)                         # the whole room
CAM_W1 = Cam(954.0, 538.0, 0.975)                        # ... crept in a little by the end of the intro
CAM_SOFA = Cam(900.0, 468.0, 1.27)                       # the first verse: the head about 150 px
CAM_SIT = Cam(1265.0, 476.0, 1.10)                       # eased back and to the right: the window, the table, the far chair
T_IN = (10.3, 13.3)
T_BACK = (21.9, 24.3)
T_OUT = (33.6, 36.0)

# ---- the hero on the wall -------------------------------------------------------------------------
HERO = (976.0, 428.0, 118.0)                             # feet x, y, height; its fist toward the scribble (face -1)
T_HERO = (16.47, 17.18, 17.79)                           # face, body, cape: three measured attacks
T_CROSS = (20.79, 21.2, 21.6)

# ---- the balloon ----------------------------------------------------------------------------------
BAL = (945.0, 428.0, 84.0, 62.0)                         # centre, radii: its near half within the sitting child's reach
T_BAL = (28.6, 29.4)
T_KNOT = (29.36, 29.70, 30.06)                           # the knot comes in three bursts, on three attacks
T_WIPE = 31.58
T_RISE = (31.8, 32.88)                                   # the knot goes up into the scribble
T_AGAIN = (32.42, 33.14)                                 # the small one, round the head and up the strand

# ---- the scribble ---------------------------------------------------------------------------------
SEED_XY = (826.0, 398.0)                                 # where the black crayon begins: a small tangle just over the sleeper
C_0 = (815.0, 378.0, 150.0, 58.0)
C_KEYS = (
    (11.5, 12.2, (795.0, 352.0, 200.0, 84.0)),           # the first loops round the tangle
    (12.27, 13.1, (768.0, 308.0, 268.0, 106.0)),         # more: it piles up
    (13.29, 14.4, (735.0, 264.0, 335.0, 128.0)),         # the whole cloud, hanging over the child
    (14.45, 15.0, (735.0, 302.0, 335.0, 128.0)),         # it sags onto the child (it lands on 14.87)
    (16.0, 16.9, (660.0, 286.0, 262.0, 118.0)),          # it draws back from the wall where the hero appears
    (20.79, 20.95, (668.0, 288.0, 276.0, 120.0)),        # three lunges with the three crossings-out
    (21.2, 21.36, (678.0, 290.0, 292.0, 122.0)),
    (21.6, 21.76, (690.0, 292.0, 310.0, 124.0)),
    (22.0, 24.4, (712.0, 238.0, 328.0, 109.0)),          # it rises with the child that sits up under it
    (32.8, 33.06, (712.0, 236.0, 360.0, 121.0)),         # the knot has joined it: it swells
    (33.12, 33.4, (712.0, 236.0, B1C[2], B1C[3])),       # and again
    (33.95, 35.95, B1C),                                 # dragged after the child, it settles
)
T_ARRIVED = C_KEYS[-1][1]


def _track(t, v, keys):
    """Eased from value to value: keys = ((t0, t1, value), ...) in order."""
    for t0, t1, v1 in keys:
        if t <= t0:
            break
        w = ease(seg(t, t0, t1))
        v = v1 if w >= 1.0 else tuple(p + (q - p) * w for p, q in zip(v, v1))
    return v


def _cam(t):
    u = seg(t, 0.0, T_IN[0] + 1.0)
    c = Cam.lerp(CAM_W0, CAM_W1, u * (2.0 - u))
    if t > T_IN[0]:
        c = Cam.ease(c, CAM_SOFA, seg(t, *T_IN))
    if t > T_BACK[0]:
        c = Cam.ease(c, CAM_SIT, seg(t, *T_BACK))
    if t > T_OUT[0]:
        c = Cam.ease(c, S.CAM[END], seg(t, *T_OUT))
    return c


def _hero(t):
    """The caped hero (a Sketch with its times): face, body, cape on three attacks; the cape waves on the beats."""
    wave = math.cos(math.pi * (t - 18.265) / 0.75) * ramp(t, 18.0, 18.4)
    Hr = hero(HERO[0], HERO[1], HERO[2], wave=wave, face=-1)
    groups = (("head", "hair", "mask", "eye_b", "eye_f", "grin"), ("body", "leg_b", "leg_f", "arm_hip", "arm_up", "fist"), ("cape",))
    for names, t0, dur, lead in zip(groups, T_HERO, (0.62, 0.56, 0.34), (0.0, 0.0, 0.08)):
        t0 -= lead                                       # the cape's first stretch runs along the shoulder, unseen: its tip shows on the attack
        n = len(names)
        for j, nm in enumerate(names):
            a0 = t0 + dur * j / n
            for it in Hr.sub("hero." + nm):
                it.on = (a0, a0 + dur / n * 1.15) if isinstance(it, Stroke) else (a0 + 0.2, a0 + 0.6)
    Hr.set_off(21.9, 23.2)
    return Hr


def _lead(Hr, t):
    """Where the bright line is being drawn, as a hand leads it: carried across the gaps between
    the strokes and smoothed over six frames (things.sketch_tip jumps from stroke to stroke)."""
    L = sorted((it for it in Hr if isinstance(it, Stroke) and it.on), key=lambda it: it.on[0])
    x = y = 0.0
    for k in range(6):
        tt = t - k / 30.0
        cur = L[0]
        for it in L:
            if it.on[0] <= tt:
                cur = it
        p = seg(tt, *cur.on)
        P = cur.P
        u = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])
        f = (0.5 * p + 0.5 * ease(p)) * u[-1]
        x, y = x + float(np.interp(f, u, P[:, 0])) / 6.0, y + float(np.interp(f, u, P[:, 1])) / 6.0
    return (x, y)


DUST_LIFE = 0.9


def _fall(F, pts, a=0.75):
    """Chalk dust let go at pts = [(x, y, age, j), ...]: it sinks, drifts and goes out over DUST_LIFE seconds."""
    for lo, hi in ((0.0, 0.3), (0.3, 0.6), (0.6, 0.9)):
        q = [(x + 9.0 * rsym(j, 5) * g, y + 4.0 + 30.0 * g + 60.0 * g * g) for x, y, g, j in pts if lo <= g < hi]
        if q:
            xs, ys = zip(*q)
            specks(F, xs, ys, 1.9, C.CHALK, a * (1.0 - (lo + 0.15) / DUST_LIFE) ** 1.3, "mid")


def _stroke_dust(F, sk, t, least=70.0):
    """Dust falling from the lines of a Sketch while (and just after) they are drawn on: where the tip has
    been. least: the shortest line (world units) that sheds any."""
    pts = []
    for it in sk:
        if not isinstance(it, Stroke) or not it.on or not (it.on[0] <= t < it.on[1] + DUST_LIFE):
            continue
        P = it.P
        u = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])
        if u[-1] < least:
            continue
        m = min(16, int(u[-1] / 45.0) + 2)
        for j in range(m):
            p = (j + 0.5 + 0.4 * rsym(it.seed * 31 + j, 3)) / m          # when, through the stroke's drawing
            g = t - (it.on[0] + p * (it.on[1] - it.on[0]))
            if 0.0 <= g < DUST_LIFE:
                f = (0.5 * p + 0.5 * ease(p)) * u[-1]
                pts.append((float(np.interp(f, u, P[:, 0])), float(np.interp(f, u, P[:, 1])), g, it.seed * 31 + j))
    if pts:
        _fall(F, pts)


def _out_of_head(m, hc, R, to, inset=6.0):
    """The point where the way from the mouth m toward `to` leaves the head (centre hc, radius R), `inset` inside it."""
    vx, vy = to[0] - m[0], to[1] - m[1]
    ln = math.hypot(vx, vy) + 1e-9
    vx, vy = vx / ln, vy / ln
    dx, dy = m[0] - hc[0], m[1] - hc[1]
    b = dx * vx + dy * vy
    s = -b + math.sqrt(max(0.0, b * b - (dx * dx + dy * dy - R * R)))
    return (m[0] + (s - inset) * vx, m[1] + (s - inset) * vy)


def _wipe(a, t):
    """The sleeve truly wipes the balloon: the far hand goes up beside the face (31.2), comes down
    through the balloon's near half on an arc about its shoulder (31.56 to 31.92), and goes back."""
    k = ramp(t, T_WIPE - 0.38, T_WIPE - 0.12) * (1.0 - ramp(t, T_WIPE + 0.5, T_WIPE + 1.05))
    if k <= 0.0:
        return
    sh = a.J["sh_b"]
    e = 1.0 - (1.0 - seg(t, T_WIPE - 0.02, T_WIPE + 0.34)) ** 2.2
    th = math.radians(-62.5 + 73.5 * e)
    pt = (sh[0] + 134.0 * math.cos(th), sh[1] + 134.0 * math.sin(th))
    a.pose = AC.reach_to(a.pose, a.x, a.y, pt, a.h, a.face, "b", k, lean=0.0)
    a.J = pose_joints(a.pose, a.x, a.y, a.h, a.face)


def _ground_on(F, t, line=True):
    """The first note: the ground line runs across the bare sheet, left to right, dust sinking behind its tip."""
    v = F.cam.view(40)
    if line:
        ground_line(F, span=(v[0], v[0] + (v[2] - v[0]) * seg(t, 0.265, 1.0)))
    pts = []
    for j in range(22):
        p = (j + 0.5 + 0.4 * rsym(j, 3)) / 22.0
        g = t - (0.265 + 0.735 * p)
        if 0.0 <= g < DUST_LIFE:
            pts.append((v[0] + (v[2] - v[0]) * p, FLOOR, g, 700 + j))
    if pts:
        _fall(F, pts)


def draw(F):
    if S.joined(F, START, END):                          # the last 0.25 s: the hand-off picture B1
        return
    t = F.t
    F.cam = _cam(t)

    # ---- the room ---------------------------------------------------------------------------------
    R = room("night")
    room_on(R, F.tl)
    if t < 1.02:                                         # the bare sheet, the ground line on the first note
        R.back(F)
        _ground_on(F, t)
        return
    lit = F.ramp(7.0, 8.4)                               # the light comes with the pane
    ph = F.seg(7.0, 7.3)
    S.room_set(F, "night", 0.0, R=R, light=lit, pane_rain=0.6 * lit, crow_times=S.CROW_TIMES, cushion=False,
               drawing=1.0 if t >= 9.3 else 0.0, phone_a=1.0 if ph >= 1.0 else 0.0)
    if 0.0 < ph < 1.0:
        phone(F, *story.PHONE, draw=ph)
    if t < 9.3:                                          # the torn drawing: a half on each of two soft notes
        Wd = wall_drawing(*story.WALL_DRAWING)
        Wd.sub("pic.l", "pic.pin_l").spread(7.22, 0.0, 0.5, by=2)
        Wd.sub("pic.r", "pic.pin_r", "pic.tear").spread(8.13, 0.0, 0.5, by=2)
        Wd.draw(F)
    if t < 10.2:                                         # chalk dust sinks from the fresh lines
        if t < 1.0 + DUST_LIFE:
            _ground_on(F, t, line=False)
        _stroke_dust(F, R.all(), t)

    # ---- the wish on the wall, crossed out ---------------------------------------------------------
    tip = None
    wish = 0.0
    if 16.3 < t < 23.7:
        # the wish gives a little pale light of its own; each crossing-out puts a third of it out
        wish = ramp(t, T_HERO[0], T_HERO[2] + 0.3) * (1.0 - sum(ramp(t, tc, tc + 0.2) for tc in T_CROSS) / 3.0)
        if wish > 0.0:
            glow(F, HERO[0] + 10.0, HERO[1] - 0.55 * HERO[2], 150.0, 125.0, PALE, 0.13 * wish)
        Hr = _hero(t)
        Hr.draw(F)
        if t < T_HERO[2] + 1.6:
            _stroke_dust(F, Hr, t, 40.0)
        tip = _lead(Hr, t)
        hx, hy, hh = HERO
        for j, (t0, x0, y0, x1, y1) in enumerate(((T_CROSS[0], hx - 50.0, hy - 128.0, hx + 77.0, hy - 84.0),
                                                  (T_CROSS[1], hx + 81.0, hy - 76.0, hx - 47.0, hy - 36.0),
                                                  (T_CROSS[2], hx - 49.0, hy - 24.0, hx + 79.0, hy + 4.0))):
            cross_out(F, x0, y0, x1, y1, t0, amp=30.0, n=9, seed=30 + j, w=0.8, off=(22.4, 23.6))

    # ---- the child ----------------------------------------------------------------------------------
    a = AC.s01(t, tip=tip, hero=(HERO[0] + 0.32 * HERO[2], HERO[1], HERO[2]), balloon=(BAL[0], BAL[1], BAL[2]))
    _wipe(a, t)
    glad = ramp(t, 19.36, 19.8) * (1.0 - ramp(t, T_CROSS[0], T_CROSS[0] + 0.12))
    if glad > 0.0:                                       # on the strong attack the wish gets to its face: a light in the eyes
        a.pose = a.pose.but(mouth=a.pose["mouth"] + 0.16 * glad, spark=max(a.pose["spark"], 0.7 * glad))
    if T_BAL[0] - 0.1 < t < T_WIPE + 0.5:                # the balloon, behind the child: the sleeve goes over it
        balloon(BAL[0], BAL[1], BAL[2], BAL[3], mouth=_out_of_head(a.pts["mouth"], a.J["head"], a.J["R"], BAL), on=(T_BAL[0] - 0.1, T_BAL[1]),
                off=(T_WIPE + 0.02, T_WIPE + 0.4)).draw(F)
    on_sofa = t < AC.S01_T["off"][0]
    J = S.child(F, a, rim=(PALE, (0.55, -0.85), 0.75 * wish) if wish > 0.0 else None, shadow=0.0 if on_sofa else ramp(t, 34.6, 35.6))
    R["cushion"].draw(F)
    if t < 11.0:
        title.draw(F, 2.0, 10.5, cx=TITLE_CX)
        return
    for t0, x0, y0, x1, y1, sd in ((13.29, 752.0, 552.0, 848.0, 510.0, 41), (14.52, 764.0, 594.0, 842.0, 566.0, 42)):
        if t0 <= t < 18.2:                               # loose runs of the black crayon over its back and shoulder
            cross_out(F, x0, y0, x1, y1, t0, amp=21.0, n=8, seed=sd, w=0.6, off=(16.3 + 0.2 * (sd - 41), 17.8 + 0.2 * (sd - 41)))

    # ---- the scribble -------------------------------------------------------------------------------
    if t >= T_ARRIVED:
        S.scribble(F, B1C, J)
        return
    top, crown, back, head = J["top"], J["crown"], J["back"], J["head"]
    if t < 13.3:                                         # the black crayon begins: the small tangle (the one that is left at the end)
        up0 = ramp(t, 11.9, 12.9)                         # it is lifted into the mass that grows round it
        tangle(F, SEED_XY[0] - 24.0 * up0, SEED_XY[1] - 84.0 * up0, 56.0, 42.0, loops=6, draw=seg(t, 11.0, 11.95),
               a=1.0 - ramp(t, 12.6, 13.3))
    cloud = _track(t, C_0, C_KEYS)
    d = 0.20 * seg(t, 11.5, 12.2) + 0.40 * ramp(t, 12.27, 13.1) + 0.40 * ramp(t, 13.29, 14.4)
    sag = ramp(t, 14.45, 15.0)
    give = ramp(t, 16.0, 16.8) * (1.0 - ramp(t, 21.6, 22.4))
    up = ramp(t, 23.0, 24.2)
    kb = sag * (1.0 - ramp(t, 22.3, 23.3))
    hp = (top[0] + (crown[0] - top[0]) * up, top[1] + (crown[1] - top[1]) * up + 6.0)
    rest = [(hp[0], hp[1], sag * (1.0 - 0.9 * give))]
    if kb > 0.0:
        rest.append((back[0], back[1] + 4.0, kb))
    avoid = [(head[0], head[1], J["R"])]
    kbal = ramp(t, T_BAL[0], T_BAL[1]) * (1.0 - ramp(t, T_WIPE + 0.05, T_WIPE + 0.5))
    if kbal > 0.0:                                       # the balloon pushes the loose loops aside
        avoid += [(BAL[0], BAL[1], (BAL[3] + 6.0) * kbal), (BAL[0] - 34.0, BAL[1], (BAL[3] - 2.0) * kbal),
                  (BAL[0] + 34.0, BAL[1], (BAL[3] - 2.0) * kbal)]
    drag = ramp(t, 33.9, 34.5) * (1.0 - ramp(t, 35.3, T_ARRIVED))
    if d > 0.0:
        Tp = gloom(F, *cloud, s=HAND, draw=d if d < 1.0 else None, rest=rest, avoid=avoid,
                   tug=(crown[0], crown[1], 0.14 * drag) if drag > 0.0 else None)
        gloom_dust(F, cloud[0] - 0.8 * cloud[2], cloud[0] + 0.8 * cloud[2], 0.0, band=Tp.band, a=0.5 * ramp(t, 13.3, 15.0))
    if t < T_BAL[0] - 0.1:
        return

    # ---- the word that does not come ------------------------------------------------------------------
    root = Tp.band.root(crown[0] + 40.0, 0.4)
    u = ease(seg(t, *T_RISE))
    nudge = 16.0 * ease_out(seg(t, T_WIPE + 0.06, T_WIPE + 0.3), 2.0)
    kx, ky = BAL[0] + nudge + (root[0] - BAL[0] - nudge) * u ** 1.5, BAL[1] + (root[1] - BAL[1]) * u
    if t >= T_WIPE + 0.04:                               # the strand: out of the crown to the knot, and up with it
        strand(F, crown, (kx, ky) if u < 1.0 else root, slack=0.35 + 0.45 * u - 0.55 * drag, draw=seg(t, T_WIPE + 0.04, T_WIPE + 0.32))
    if T_KNOT[0] <= t < T_RISE[1] + 0.2:
        dk = sum(ease_out(seg(t, tk, tk + 0.26), 2.0) for tk in T_KNOT) / 3.0
        sz = 0.62 * (1.0 - 0.35 * u)
        tangle(F, kx, ky, sz * BAL[2], sz * BAL[3], loops=12, draw=dk, a=1.0 - ramp(t, T_RISE[1] - 0.1, T_RISE[1] + 0.15))
    if T_AGAIN[0] <= t < T_AGAIN[1] + 0.2:               # once more, smaller: round the head and up the strand
        m0 = _out_of_head(a.pts["mouth"], head, J["R"], BAL, -12.0)
        P = spline(A(m0, (head[0] + J["R"] + 16.0, head[1] - 28.0), (crown[0] + 12.0, crown[1] - 14.0),
                     (0.5 * (crown[0] + root[0]) + 8.0, 0.5 * (crown[1] + root[1])), root), 12)
        v = ease(seg(t, T_AGAIN[0] + 0.16, T_AGAIN[1])) * (len(P) - 1)
        i = min(len(P) - 2, int(v))
        q = P[i] + (P[i + 1] - P[i]) * (v - i)
        tangle(F, q[0], q[1], 24.0, 18.0, loops=7, seed=13, draw=seg(t, T_AGAIN[0], T_AGAIN[0] + 0.2),
               a=1.0 - ramp(t, T_AGAIN[1] - 0.08, T_AGAIN[1] + 0.15))
