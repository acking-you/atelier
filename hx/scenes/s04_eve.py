"""s04_eve   91.77 - 115.77   v2a, v2b          B3  ->  B4

The quietest and loneliest stretch of the film: the evening room, the phone that brings nothing, the
scribble coming down like a shawl; then the room is taken away, the last edge of the window's light
runs out into ONE narrow line on a corridor floor, and the child, shouldered off that line three
times, plants its feet on it, is crossed out, and draws itself again.

CUE SHEET (lines by 0-based LRC index and time, paraphrased; no lyric text anywhere)
  91.77   B3      first frame = S.handoff(F, "B3"): the evening room at ROOM2_DX, the child standing on the
                  rug at X3, eyes on the phone, the cloud on its crown
  v2a 91.77 - 103.77   (one slow push in, 91.9 to 100.6: down with the child to the phone by 95.1 (head
                  126 px at the first stroke, 150 by 94.75), then a creep to 175 px under the shawl; the child
                  low on the left, the pale pool across the floor, the amber window small on the right, lit
                  the whole time; it never looks)
  91.80   idx 27  (sunset, leafing through the phone, nobody calls) it sits down on the rug, its back
                  against the sofa; the cloud's belly lets go of its crown and the strand pays out
  92.515          (beat) it has slumped forward as it landed and its hand is on the phone; it sits back with
                  it (to 92.95, a still moment before the first stroke); from 92.6 the screen lights its face
                  pale from below (a glow under the chin and on the hands, a soft rim from below)
  93.05, 93.26, 94.75, 95.98   (attacks) the thumb strokes; a column of empty lines slides by; the face
                  empties between them
  96.02           nothing has come: it lays the phone face down; the light on its face goes out
  96.18   idx 28  (perhaps that is what someone used to being alone deserves) the cloud sinks and
                  settles on its shoulders like a shawl (to 98.8); knees drawn up, forehead on them (99.0)
  99.0 - 101.6    the hold: breath under the shawl, one long sigh on the attack 100.40, dust
  101.52 - 102.3  the pale pool is drawn up to its edge under the window
  102.27          (attack) that edge runs out both ways along the floor: one long narrow line of light,
                  and the chalk line is inked along it, the tip leading (to 103.3)
  101.52 - 104.52 the room is taken off and its bones become the corridor (sets.room_to_corridor, a
                  part per beat; the amber window is the last thing of the room to go, 102.7 - 103.3)
  101.9 - 103.4   it gets up onto the line, heavy, the head last, the shawl hanging down its back like a
                  cloak; 102.45 - 104.35 the cloak gathers up over its head into the cloud again
  v2b 103.77 - 115.77
  103.02  idx 30  (the single-plank bridge: whom must one push off to win) the stream of faceless pupils
                  draws on, coming the other way along the line, two per bar
  104.07, 105.23, 106.57   (attacks) three tries at a step, three times shouldered: the child gives way,
                  steps off the line toward us and lets them by; it pushes nobody (a small jolt of the frame)
  108.25  idx 31  (when will its silent resistance win) the far foot is set down hard on the attack: feet
                  planted on the line; the stream parts round it (108.8 one behind, 109.0 a small one in front);
                  the camera closes in a little (108.3 - 110.5)
  109.6           the black crayon comes down out of the cloud and crosses out its near arm and shoulder:
                  the line under the crayon is rubbed to a ghost, the whole child pales a little; a wince;
                  it looks at the arm
  111.0 - 112.0   with a stub of chalk it goes over its own arm again: the stub's tip lays a bright new
                  stroke; behind it the ghost is gone and the black zigzag is rubbed away slice by slice as
                  the tip passes (ahead of it both are still there); the stroke stays fresh, settles by 113.3;
                  its pressure comes back
  113.5           crossed out more: down its whole side, harder; it pales more
  114.3 - 115.0   it draws its side again, quicker this time (the zigzag kept off its face; all of it rubbed
                  away and settled by 115.42)
  112.4 - 115.42  the camera eases back, slowly, to the hand-off frame; 113.5 - 115.3 the stream thins and
                  is rubbed out, the farthest first; 114.27 - 115.45 the corridor is taken back
                  (sets.corridor_to_bare), the line of light draws in to the child's feet and is gone
  115.52  B4      S.handoff(F, "B4"): bare sheet, the child planted at X4, braced, head level, the cloud

THE PERFORMANCE   AC.s04(F.t, **CUES): its own cue table (every cue is on a measured attack already) with the
                  pick moved onto the beat 92.515 (written 92.72: the sit-back then took the frames before
                  the first stroke in a rush). This
                  module's own: how far and how long the child is off the line after each bump (28 units,
                  until the one who shouldered it is by: _off_line), and the sigh at 100.40.
THE STREAM        people.walkers with every pass that matters staged (HITS, ROUND) and drawn by this
                  module (_stream_draw): on the line before the plant, round the child after it.
PROOFS            hx/_review/v4_scenes/s04/ (proofs.py makes the strips; proofs.py hits prints the gaps)
"""
import math

import numpy as np


from hx import story
from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk import acting_child as AC

from . import _shared as S

SPAN = (91.77, 115.77)
START, END = "B3", "B4"

DX = story.ROOM2_DX
FLOOR = story.FLOOR
X3, X4 = story.X3, story.X4
CUES = dict(pick=92.515)          # the performance's cues this scene moves (AC.s04(t, **CUES)): the hand is on the
                                 # phone on the beat, so that the sit-back is over before the first stroke (93.05)
T = dict(AC.S04_T, **CUES)
_WL, _WT, _WR, _WB = (story.WINDOW[0] + DX, story.WINDOW[1], story.WINDOW[2] + DX, story.WINDOW[3])
_CWL, _CWT, _CWR, _CWB = (COR_WINDOW[0] + DX, COR_WINDOW[1], COR_WINDOW[2] + DX, COR_WINDOW[3])

# ---- times of this module (all on beats or measured attacks) ---------------------------------------
PUSH = (91.9, 100.6)             # the one slow push in of the first half
POOL_UP = (101.515, 102.3)       # the pool is drawn up to its edge (from the beat)
LINE_OUT = (102.265, 103.75)     # the edge runs out into the line (attack 102.255; past the frame's edge by the bar 103.765)
CHANGE = SPAN_ROOM_TO_CORRIDOR   # 101.515 .. 104.515: a part per beat
TRAVEL = (101.6, 104.0)          # the camera goes from the rug to the corridor
STREAM = (103.015, 115.4)        # the pupils: they draw on from the beat, a quarter beat apart
CLOSE = (108.3, 110.5)           # the camera closes in on the planted child
BACK = (112.4, 115.42)           # ... and eases back, slowly, to the hand-off frame
BARE = (114.265, 115.45)         # the corridor is taken back
C1, C2 = T["cross"]              # 109.6, 113.5
(D0, D1), (E0, E1) = T["redraw"]  # (111.0, 112.0), (114.3, 115.0)

# ---- cameras --------------------------------------------------------------------------------------
CAM_RUG = Cam.at(X3 - 50.0, 590.0, 1.48, 360.0, 560.0)       # head 175 px, low on the left; the amber window at x 1810
CAM_COR = Cam.at(X4, FLOOR, 1.10, 760.0, 806.0)              # head 130 px; door cropped left, window cropped right
CAM_PLANT = Cam.at(X4, FLOOR, 1.22, 773.0, 812.0)            # head 144 px
STEP_OFF = 28.0                                              # the step off the line toward us, as far as the light is deep (the acting's is 15)


def _camera(F, bump):
    t = F.t
    if t < TRAVEL[0]:
        s = 0.62 * ease(seg(t, PUSH[0], 95.1)) + 0.38 * ease(seg(t, 94.4, PUSH[1]))      # down with the child to the phone (head 150 px), then a slow creep
        return Cam.lerp(S.CAM[START], CAM_RUG, s)
    if t < CLOSE[0]:
        c = Cam.ease(CAM_RUG, CAM_COR, seg(t, *TRAVEL))
        return Cam(c.cx - 5.0 * bump, c.cy + 1.5 * bump, c.zoom)
    if t < BACK[0]:
        return Cam.ease(CAM_COR, CAM_PLANT, seg(t, *CLOSE))
    return Cam.ease(CAM_PLANT, S.CAM[END], seg(t, *BACK))


# ---- the performance --------------------------------------------------------------------------------
def _env(t, t0, up, hold, down):
    """A reaction's envelope: 0 before t0, up fast (slowing in), held, released slowly (as the acting's)."""
    d = t - t0
    if d <= 0.0 or d >= up + hold + down:
        return 0.0
    if d < up:
        return 1.0 - (1.0 - d / up) ** 3
    if d < up + hold:
        return 1.0
    return 1.0 - ease((d - up - hold) / down)


BACK_ON = (T["bumps"][1] - 0.16, T["bumps"][2] - 0.16, T["plant"] - 0.30)     # when it is on the line again after each bump


def _off_line(t):
    """0..1: the child is off the line, toward us. It gives way on the bump (0.2 s), stays off while
    the one who shouldered it goes by on the line, and comes back onto the line with its next step."""
    o = 0.0
    for th, tb in zip(T["bumps"], BACK_ON):
        if th < t < tb:
            o = max(o, min(_env(t, th + 0.02, 0.18, 9.0, 0.1), 1.0 - ease(seg(t, tb - 0.32, tb))))
    return o


def _act(t):
    a = AC.s04(t, **CUES)
    P, y = a.pose, a.y
    if 99.9 < t < 101.7:                                          # the sigh: in on the attack 100.40, out long
        up = ease(seg(t, 100.05, 100.45)) * (1.0 - ease(seg(t, 100.5, 101.6)))
        P = P.but(chest=P["chest"] + 1.0 * up, lean=P["lean"] - 0.08 * up, neck=P["neck"] - 0.12 * up)     # the back fills, the head comes off the knees a little
    if T["bumps"][0] < t < T["plant"]:
        y = FLOOR + STEP_OFF * _off_line(t)
    if P is a.pose and y == a.y:
        return a
    return AC.Act(P, a.x, y, a.face, a.grab, a.draw, a.a, 1.0, None, a.pts, a.num, a.h)


# ---- the window's light: a pool, then one long narrow line --------------------------------------------
def _floor_light(F):
    """The long pale pool of the evening window (as room_light draws it), drawn up to its edge under
    the window (POOL_UP), the edge running out both ways along the floor into one narrow line of
    light on the ground line (LINE_OUT); at the end it draws in to the child's feet. One primitive
    all the way (weather.window_pool), so nothing cross-fades. Returns (xa, xb): how far the line
    reaches (None while it is still the pool)."""
    t = F.t
    sun = ease(seg(t, 92.5, POOL_UP[0]))                                    # the evening goes on: the pool swings a little
    l0, r0, lean0, a0 = _WL - 20.0, _WR + 10.0, -0.9 - 0.12 * sun, 1.0 - 0.12 * sun      # further and pales a little
    k1 = ease(seg(t, *POOL_UP))
    k2 = ease_out(seg(t, *LINE_OUT), 1.5)
    if k1 <= 0.0:
        window_pool(F, l0, r0, FLOOR + 14.0, a0, lean0, 380.0, mood="evening")
        return None
    k3 = ease(seg(t, BARE[0] + 0.25, BARE[1] - 0.03))                       # drawn in again at the end
    xa0, xb0 = l0 + lean0 * 60.0, r0 + lean0 * 60.0
    xa = xa0 + (X4 - 1250.0 - xa0) * k2                                     # its left tip passes under the child at 102.8
    xb = xb0 + (X4 + 1900.0 - xb0) * ease_out(seg(t, LINE_OUT[0], LINE_OUT[0] + 0.5), 1.5)
    if k3 > 0.0:
        xa, xb = xa + (X4 - xa) * k3, xb + (X4 - xb) * k3
    depth = 380.0 + (44.0 - 380.0) * k1 + (30.0 - 44.0) * k2
    y0 = FLOOR + 14.0 + (-16.0) * k2
    narrow = 0.5 * k1 + 0.5 * k2
    lean = lean0 * (1.0 - k2)
    l = xa - lean * 60.0
    r = l + max(1.0, xb - xa) / (1.0 - 0.985 * narrow)
    a = (a0 + (1.5 - a0) * k2) * (1.0 - ease(seg(t, BARE[1] - 0.5, BARE[1] - 0.05)))
    window_pool(F, l, r, y0, a, lean, depth, mood="evening", narrow=narrow)
    return (xa, xb) if k2 > 0.0 and xb - xa > 2.0 else None


def _lights(F, reach):
    """Everything the window does: its glow on the wall (the room's window, travelling with the frame
    to the corridor's end), the pool / the line, the corridor's long shaft along the floor."""
    t = F.t
    u = ease(seg(t, CHANGE[0] + 0.75 * 2.2, CHANGE[0] + 0.75 * 3.5))        # the frame travels (sets' plan row)
    rect = [p + (q - p) * u for p, q in zip((_WL, _WT, _WR, _WB), (_CWL, _CWT, _CWR, _CWB))]
    gone = ease(seg(t, BARE[0], BARE[1] - 0.25))
    ga = (1.0 - 0.6 * ramp(t, 102.7, 103.25) + 0.6 * ramp(t, 103.95, 104.45)) * (1.0 - gone)
    window_glow(F, *rect, ga, "evening")
    reach[0] = _floor_light(F)
    ca = ramp(t, 103.9, 104.5) * (1.0 - gone)
    if ca > 0.0:
        shaft(F, 1640.0 + DX, 110.0, 616.0, 900.0 + DX, 620.0, 788.0, col=PALE, a=0.16 * ca)


def _lit(R, F0, reach):
    """Hang this module's light on a Place: S.room_set (and the corridor) then draw it where light
    belongs, after the dressing and before the view."""
    back = R.back

    def lit_back(F, a=1.0):
        back(F, a)
        _lights(F, reach)
    R.back = lit_back
    return R


# ---- the stream ---------------------------------------------------------------------------------------
# people.walkers times a pass by the moment a pupil is AT x. The child leans into its step, so the two
# meet when the pupil is still 115 units before it: the three who shoulder the child pass X4 about
# three quarters of a second after each bump (solved for seed 6: proofs.py hits prints the gaps). The
# one who goes round in front is a small one (330 tall): the child's eyes stay to be seen over its head.
HITS = (104.840, 106.022, 107.625)                # ... are 115 units before the child on 104.07, 105.23, 106.57
ROUND = (108.80, 109.00, 112.70)                  # after the plant: one goes round behind it, one in front, one behind
FRONT = (ROUND[1],)


def _stream():
    Wk = walkers(STREAM[0], STREAM[1], X4, hits=HITS + ROUND, seed=6, back_every=0, front=0.0, fade=1.9)
    return tuple(w for w in Wk if w.hit or not 102.2 < w.T < 104.4)      # nobody draws on right behind the rising child


def _stream_draw(F, Wk, lane, cx):
    """people.stream with this scene's staging: before the plant everybody keeps to the line (the
    child is the one who steps off); from the plant on they go round the child, behind it or in front
    (those of FRONT: nearer, larger, brighter as they come by). A pupil that shoulders the child is
    checked for a moment and walks on."""
    t = F.t
    part = ramp(t, T["plant"] - 0.35, T["plant"] + 0.25)
    l, _, r, _ = F.cam.view(95.0)
    for w in sorted(Wk, key=lambda w: rnd(w.seed, 9)):
        near = any(abs(w.T - tf) < 0.01 for tf in FRONT)
        if near != (lane > 0):
            continue
        on = 1.0 if w.on is None else seg(t, *w.on)
        off = 0.0 if w.off is None else seg(t, *w.off)
        if on <= 0.0 or off >= 1.0:
            continue
        wx = w.at(t)
        if wx < l or wx > r or abs(wx - w.x) > w.reach:
            continue
        g = math.exp(-((wx - cx) / 190.0) ** 2) * part
        tilt = 0.0
        if w.hit and not near:
            for th in T["bumps"]:
                tilt += 0.07 * _env(t, th, 0.07, 0.05, 0.38)
        if near:
            person(F, wx, FLOOR - 4.0 + 52.0 * g, w.h * (0.97 + 0.07 * g), w.pose(t), "pupil", w.d, w.seed, draw=on, off=off,
                   far=0.30 * (1.0 - g))
        else:
            person(F, wx, FLOOR - 4.0 - 22.0 * g, w.h * (0.97 - 0.02 * g), w.pose(t), "pupil", w.d, w.seed, draw=on, off=off,
                   far=0.14 if w.T in HITS else 0.30, tilt=tilt)


# ---- the scribble ---------------------------------------------------------------------------------------
S0, S1 = T["shawl"]              # 96.18, 98.8
UP = (102.45, 104.35)            # the shawl gathers up into the cloud again (the child is half up by then): linear in
                                 # settle, whose two stages (off the shoulders, up off the head) are eased by the kit


def _cloud_after(x):
    """The cloud over the standing child (hand-off B4's numbers, 30 units behind the child)."""
    c = story.HANDOFF[END]["cloud"]
    return (x - 30.0,) + tuple(c[1:])


def _scribble(F, a, J):
    t = F.t
    head = (J["head"][0], J["head"][1], J["R"])
    crown = J["crown"]
    c3 = story.HANDOFF[START]["cloud"]
    if t < S0:                                                    # the cloud of B3; its belly lets the sitting child go
        k = 1.0 - ease(seg(t, 91.82, 92.22))
        slack = 0.8 - 0.4 * math.sin(math.pi * seg(t, 91.85, 93.9)) ** 2
        return S.scribble(F, c3, J, k=k, slack=slack)
    if t < UP[0]:
        Bc = band_cloud(*c3, rest=(crown[0], crown[1] + 6.0, 0.0))
        k = seg(t, S0, S1)
    else:
        xs = X3 + (X4 - X3) * ease(seg(t, 104.3, 108.4))          # the cloud comes after the child, late
        k = 1.0 - seg(t, *UP)
        over = math.sin(math.pi * seg(t, UP[0], 104.5)) ** 2      # ... and rides on its head while it gets up
        cl = _cloud_after(xs + (J["head"][0] - 25.0 - xs) * over)
        if k <= 0.0:
            tug = reach = None
            for tc, key in ((C1, "arm"), (C2, "side")):           # it is the scribble that crosses the child out: its
                e = ease(seg(t, tc - 0.3, tc)) * (1.0 - ease(seg(t, tc + 0.2, tc + 0.9)))     # belly reaches down as the crayon strikes
                if e > 0.0 and key in a.pts:
                    p = _cross_axis(a, key)[:2]
                    tug = (p[0] + 20.0, p[1], 0.24 * e)
                    reach = (p, seg(t, tc - 0.24, tc) ** 2, ease(seg(t, tc + 0.14, tc + 0.75)))
            Tp = S.scribble(F, cl, J, tug=tug)
            if reach is not None:                                 # the crayon's line comes down out of the cloud, and goes back
                p, d, back = reach
                if d > 0.0 and back < 1.0:
                    strand(F, Tp.band.root(p[0] + 30.0, 0.25), p, slack=0.35, seed=14, draw=(0.0, d * (1.0 - back)))
            return Tp
        Bc = band_cloud(*cl, rest=(crown[0], crown[1] + 6.0, 1.0))
    Tp = shawl(F, J["neck"], J["pel"], FLOOR, 1, a.h, head=head, cloud=Bc, settle=k)
    sa = 1.0 - ramp(k, 0.12, 0.42)
    if sa > 0.0:
        strand(F, crown, Tp.band.root(crown[0] + 40.0, 0.4), slack=0.8, a=sa)
    bx = Tp.band.x
    gloom_dust(F, float(bx[0]) + 0.1 * float(bx[-1] - bx[0]), float(bx[-1]) - 0.1 * float(bx[-1] - bx[0]), 0.0, band=Tp.band, a=0.5)
    return Tp


# ---- the phone ------------------------------------------------------------------------------------------
PK, DN = T["pick"], T["down"]


def _phone(F, a, J):
    """The phone from the moment the hand is on it: off the rug into the hand, held up with its pale
    screen, turned face down, laid beside the child; taken off with the room."""
    t = F.t
    n = a.num
    up = ease(seg(t, PK - 0.10, PK + 0.22))                       # off the rug, upright in the hand
    dn = ease(seg(t, DN, DN + 0.45))                              # turned over and laid down
    lie = 1.0 - up * (1.0 - dn)
    rot = -0.07 + (-1.05 + 0.07) * up * (1.0 - dn) + (-0.2) * dn
    s = 1.0 + 0.25 * up * (1.0 - dn)                              # held up a little larger (more would cover the mouth)
    lit = (0.85 + 0.15 * up) * (1.0 - ramp(t, DN, DN + 0.22))
    L = PHONE_LEN * s
    px, py = a.pts["phone"]
    if t > S0 + 0.5:
        py += 6.0
    k = 0.20 * (1.0 - lie)
    off = 1.0 - seg(t, 101.9, 102.6)
    if off <= 0.0:
        return None
    return phone(F, px + k * L * math.cos(rot), py + k * L * math.sin(rot), s, lit, rot=rot, lie=lie, scroll=2.4 * n["stroke"],
                 down=dn > 0.5, draw=off)


# ---- crossed out, and drawn again --------------------------------------------------------------------
STUB_S = 1.6                     # the stub of chalk, large enough to be seen in its fist


def _pressure(t):
    """The child's own pressure: it pales when the crayon crosses it out and comes back as it draws itself."""
    return 1.0 - 0.12 * ramp(t, C1 + 0.05, C1 + 0.4) * (1.0 - ramp(t, D0 + 0.2, D1 + 0.2)) \
               - 0.18 * ramp(t, C2 + 0.05, C2 + 0.4) * (1.0 - ramp(t, E0 + 0.15, E1 + 0.1))


def _stub_at(P, d):
    """The world points at the shares d (an array) of the length of the polyline P (helper of _passes)."""
    P = np.asarray(P, dtype=np.float64)
    u = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    q = d * u[-1]
    return np.stack([np.interp(q, u, P[:, 0]), np.interp(q, u, P[:, 1])], axis=-1)


def _passes(P, axis, r0, r1, cuts):
    """When the stub (its tip at the share smoothstep(seg(t, r0, r1)) of P, as AC.s04 moves it) passes
    each of `cuts` (shares of the crossing-out's axis, measured along it)."""
    x0, y0, x1, y1 = axis
    ax = np.array([x1 - x0, y1 - y0])
    L = float(np.hypot(*ax)) + 1e-9
    ds = np.linspace(0.0, 1.0, 41)
    proj = np.maximum.accumulate(((_stub_at(P, ds) - (x0, y0)) @ (ax / L)) / L)
    d = np.interp(cuts, proj, ds)
    u = 0.5 - np.sin(np.arcsin(np.clip(1.0 - 2.0 * d, -1.0, 1.0)) / 3.0)          # smoothstep's inverse
    return r0 + (r1 - r0) * u


def _rubbed_zig(F, axis, P, t_cross, redraw, seed, done, n=7, **zig):
    """The crossing-out, rubbed away BEHIND the stub: the zigzag in n slices across its axis, each
    rubbed out (cross_out's off) from the moment the stub passes it; all of it gone by `done`."""
    x0, y0, x1, y1 = axis
    ax = np.array([x1 - x0, y1 - y0])
    L = float(np.hypot(*ax)) + 1e-9
    tx, ty = ax / L
    nx, ny = -ty, tx
    edges = np.linspace(-0.1, 1.1, n + 1)
    mids = 0.5 * (edges[1:] + edges[:-1])
    tp = _passes(P, axis, redraw[0], redraw[1], mids)
    edges[0], edges[-1] = -3.0, 4.0
    for i in range(n):
        end = min(tp[i] + 0.7, done)
        if F.t >= end:
            continue
        a_, b_ = edges[i] * L, edges[i + 1] * L
        quad = np.array([(x0 + tx * a_ + nx * s_, y0 + ty * a_ + ny * s_) for s_ in (-400.0, 400.0)] +
                        [(x0 + tx * b_ + nx * s_, y0 + ty * b_ + ny * s_) for s_ in (400.0, -400.0)])
        with F.clip(quad):
            cross_out(F, x0, y0, x1, y1, t_cross, seed=seed, off=(tp[i] - 0.04, end), **zig)


def _mend(F, P, t_cross, redraw, t_new, wide, seed, axis, **zig):
    """One stretch of the child's own outline (the world polyline P): crossed out at t_cross by the
    black crayon (cross_out along `axis`); the line under the crayon is rubbed to a ghost, so that it
    is truly gone. Gone over again with the stub during `redraw`: the tip (where AC.s04 puts it) lays a
    bright new stroke; BEHIND it the ghost is gone (the child's own line is there again under the new
    stroke) and the zigzag is rubbed away, slice by slice, as the tip passes; ahead of it both are
    still there. The new stroke stays fresh a moment and by t_new has settled into the child's line."""
    t = F.t
    r0, r1 = redraw
    d = ease(seg(t, r0, r1))                                      # (= AC's smoothstep: the stub's own progress)
    new = ramp(t, t_new - 0.5, t_new)
    gone = ramp(t, t_cross + 0.03, t_cross + 0.30)
    if gone > 0.0 and d < 0.995:
        chalk(F, P, C.KNOCK, wide, 0.9 * gone, seed=seed, wob=0.4, taper=0.85, edge=0.0, grain=None, boil=0,
              draw=(d, 1.0) if d > 0.0 else 1.0)
    _rubbed_zig(F, axis, P, t_cross, redraw, seed - 10, t_new, **zig)
    if t > r0 and new < 1.0:
        fresh = (1.0 - new) * (1.0 - 0.45 * ramp(t, r1, r1 + 0.6))
        chalk(F, P, PALE, 22.0, 0.26 * fresh, seed=seed + 1, wob=0.3, taper=0.9, edge=0.0, grain="glow", draw=d, boil=0)
        x, y, _ = restroke(F, P, d, w=10.5, seed=seed + 880, a=1.0 - new)
        press = ramp(t, r0, r0 + 0.2) * (1.0 - ramp(t, r1 - 0.05, r1 + 0.2))
        if press > 0.0:
            glow(F, x, y, 36.0, 36.0, PALE, 0.38 * press)                        # the chalk pressing


def _cross_axis(a, key):
    """The axis of a crossing-out (x0, y0, x1, y1) over a stretch of the child's outline: across it, not along it."""
    p0, p1 = a.pts[key][0], a.pts[key][-1]
    if key == "arm":                                              # the near arm and the shoulder
        return (float(p0[0]) - 44.0, float(p0[1]) - 40.0, float(p1[0]) + 20.0, float(p1[1]) + 8.0)
    return (float(p0[0]) - 46.0, float(p0[1]) + 44.0, float(p1[0]) + 36.0, float(p1[1]) + 34.0)    # its side: kept off the face


def _crossings(F, a):
    t = F.t
    if t <= C1 or "arm" not in a.pts:
        return
    n = a.num
    if t < D1 + 1.4:                                              # 1: the near arm and the shoulder
        _mend(F, a.pts["arm"], C1, (D0, D1), D1 + 1.3, 15.0, 61, _cross_axis(a, "arm"), amp=40, n=9)
    if t > C2:                                                    # 2: more: down its whole side, harder
        _mend(F, a.pts["side"], C2, (E0, E1), E1 + 0.42, 22.0, 62, _cross_axis(a, "side"), amp=54, n=9, w=1.15)
    if "tip" in a.pts:
        sa = max(ramp(t, D0 - 0.30, D0 - 0.06) * (1.0 - ramp(t, D1 + 0.10, D1 + 0.38)),      # (the acting gives the tip
                 ramp(t, E0 - 0.30, E0 - 0.06) * (1.0 - ramp(t, E1 + 0.08, E1 + 0.34)))      # from 0.30 before to 0.36 after)
        if sa > 0.0:
            chalk_stub(F, a.pts["tip"], n["ang"], STUB_S, a=sa, dust=1.0)


# ---- the frame ----------------------------------------------------------------------------------------------
def draw(F):
    if S.joined(F, START, END):                          # the last 0.25 s: the hand-off picture B4
        return
    t = F.t
    a = _act(t)
    n = a.num
    F.cam = _camera(F, n["bump"])
    reach = [None]
    w = seg(t, *CHANGE)
    wb = seg(t, *BARE)

    # the place: the evening room, the change, the corridor, the corridor taken back
    if w < 1.0:
        R = room("eve", dx=DX) if w <= 0.0 else room_to_corridor(w, dx=DX)
        S.room_set(F, "eve", DX, R=_lit(R, F, reach), light=0.0, drawing=0.0, empty=1.0, phone_lit=0.85,
                   phone_a=1.0 if t < PK - 0.10 else 0.0, wall_off=(101.6, 102.6))
    else:
        K = corridor(dx=DX) if wb <= 0.0 else corridor_to_bare(wb, dx=DX)
        _lit(K, F, reach).back(F)
        K.view(F)
        ground_line(F)
        K.draw(F)
    if reach[0] is not None:                             # the one narrow line, inked along the light
        ground_line(F, a=1.0, w=5.4, col=C.CHALK, span=reach[0])

    # the stream, the child between its two lanes
    Wk = _stream() if t >= STREAM[0] else ()
    if Wk:
        _stream_draw(F, Wk, -1, a.x)
    lit = n["lit"]
    win = 0.45 * ramp(t, 103.9, 104.6) * (1.0 - ramp(t, BARE[0], BARE[1] - 0.25))     # the end window's light on its right side
    rim = (PALE, (0.45, 1.0), 0.40 * lit) if lit > 0.0 else (PALE, 1, win) if win > 0.0 else None
    J = S.child(F, a, rim=rim, a=_pressure(t))
    if t >= PK - 0.10:
        Ph = _phone(F, a, J)
        if lit > 0.0 and Ph is not None:                 # the screen's light on its face, from below: chin, cheeks, the
            hx_, hy_ = J["head"]                         # underside of the brow; the hands round the phone
            glow(F, hx_ + 12.0, hy_ + 36.0, 78.0, 58.0, Ph["col"], 0.26 * lit)
            lx, ly = Ph["light"]
            glow(F, lx, ly, 46.0, 40.0, Ph["col"], 0.18 * lit)
    _crossings(F, a)
    _scribble(F, a, J)
    if Wk:
        _stream_draw(F, Wk, 1, a.x)
