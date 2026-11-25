"""s10_out   226.76 - 244.50   out          B9  ->  B10

The outro, instrumental, full and joyful. The two run over the hills into the low sun, jump on the
accents, drop into the grass laughing; in the golden evening the friend points home, waves and goes;
the hills and the sky are rubbed out round the child, who is left on the bare warm sheet, at ease,
the small tangle on its string.

CUE SHEET (song's clock; no line is sung in this span: LRC 62 ends at 226.84, 64 begins at 244.64)
  226.76        B9: the first frame is the picture S.handoff(F, "B9") (the same layers, the same arguments)
  227.00        the hands part (onset 227.13); the friend turns and is off; the child stays glad
  227.0 - 227.7 the camera starts to travel, a quarter second ahead of the pair (AHEAD)
  227.515       they run (beat); the tangle leans back and lags behind the hand like a balloon (RUN_LEAN, _balloon)
  227.6 - 229.2 the low sun's light comes up on their right sides as they run into it (RIM)
  228.3 - 234.9 a flock of six birds flies past them, overtaking (FLOCK_RUN, depth 0.6)
  229.765       the friend jumps (accent 229.76); the child watches
  ~229.9        they pass the tree (x 6840)
  ~231.2        the flowers' skip moves from B9's place to the place of the sit (both out of the frame)
  232.765       the child jumps, lower, copying (accent 232.76); the friend looks back
  233.69        both jump (accent 233.69), the friend's near arm thrown up
  234.6 - 236.9 the camera slows and comes to rest; the two run on into the right of the frame
  235.015 - 236.95  the camera pushes in as they arrive (zoom 0.75 -> 1.2: heads 142 px)
  235.75        they drop into the grass (accent 235.75): the child at X10, the friend at X10 + 180
  236.1 - 237.4 they laugh, out of breath; 237.65 a second, smaller laugh; then they sit, calm: the held picture
  238.75        golden evening begins (hour 0 -> 1 by 242.0: the sun goes down on the far ridge); they stand
                (the friend first; accent 238.75)
  239.3 - 241.95 four small birds fly home toward the house and go down behind the far ridge (FLOCK_HOME)
  239.50        the friend points home with its whole outer arm: the house with the amber window, beside the
                setting sun, right of it in the frame; the child looks where it points; the window glows
  240.55        the friend waves (an extreme of the swing on 241.01)
  241.15 - 242.8 the child waves back, the arm coming down slowly
  241.765       the friend turns and walks off right (bar), looking back once (242.3 - 243.6); the camera begins
                to settle on the child alone: a slow pull-back to zoom 1.0 and to B10's place (SETTLE, to 244.2)
  242.0 - 244.2 the hills and the sky are rubbed out from the frame's ends (GONE); the contour flattens into the
                one ground line from 242.88; the camera carries the sink (the child's feet stay at screen y 742)
  242.87 - 244.07 the friend's line loses pressure as it walks (faded whole on a layer); gone from 244.07
  243.6         the child turns to face left (to 244.15); the tangle swings over behind its head (the string is
                drawn behind the child until the middle of the turn)
  244.2         everything has arrived: the ground under the child is still from here on
  244.25        S.joined draws B10: the bare warm sheet at evening, the child alone at X10 facing left, its long
                shadow, the tangle on its string

STAGING   AP.s10 with its own cue table (CUES = AP.S10_T: every beat above that is the performance's is on its
          time); the ground is hills.ground_y, from 242.0 the contour as the un-drawing flattens it.
LAND      S.hill_world's layers called here (_land), with the far layer drawn on a camera of its own: it travels
          FAR_P = 0.03 of the camera's travel instead of 0.22, so that S.HOUSE (which stands on it) is still
          beside the sun, right of the friend, at the end of the run (see the report: on the far layer's own
          parallax the house ends behind the two, left of the friend who points at it and walks off right).
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from hx import story
from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk import acting_pair as AP

from . import _shared as S

SPAN = (226.76, 244.50)
START, END = "B9", "B10"

X9, X10 = story.X9, story.X10
T0, T1 = S.T[START], S.T[END]

# ---------------------------------------------------------------------------------------------
# cues (song's clock)
# ---------------------------------------------------------------------------------------------
CUES = dict(AP.S10_T)
GONE = (242.0, 244.2)                                    # the land and the sky rubbed out
HOUR = (238.75, 242.0)                                   # afternoon gold -> evening
PUSH = (235.015, 236.95)                                 # the camera comes to rest on them as they drop, pushing in
SETTLE = (241.765, 244.2)                                # the camera settles on the child alone, carrying the sink
RUN_LEAN = (227.5, 228.2, 235.5, 236.3)                  # the tangle leans back while they run
RIM = (227.6, 229.2)                                     # the low sun's light on the runners' right sides

# ---------------------------------------------------------------------------------------------
# the far layer: its parallax during the travel (S.HOUSE stands on it)
# ---------------------------------------------------------------------------------------------
FAR_P = 0.03
CAM9 = S.CAM[START]
_FAR9 = CX + (CAM9.cx - CX) * FAR                       # the far layer's own camera x at B9


def _far_cam(cam: Cam) -> Cam:
    """A camera whose far layer (cam.depth(FAR)) travels FAR_P of the camera's travel since B9 instead of FAR."""
    fx = _FAR9 + FAR_P * (cam.cx - CAM9.cx)
    return Cam(CX + (fx - CX) / FAR, cam.cy, cam.zoom)


# ---------------------------------------------------------------------------------------------
# tables of the performance (pure functions of time, sampled once per process)
# ---------------------------------------------------------------------------------------------
_DT = 1.0 / 60.0
_TG = np.arange(T0 - 2.0, T1 + 1.0, _DT)


@lru_cache(maxsize=1)
def _tables():
    """The pair's middle, the ground under it, and the hand that holds the string (on the hills: rise 1)."""
    n = len(_TG)
    xm, hx_, hy_ = np.empty(n), np.empty(n), np.empty(n)
    for i, t in enumerate(_TG):
        D = AP.s10(float(t), ground=ground_y, **CUES)
        f = D.friend
        xm[i] = 0.5 * (D.child.x + (f.x if f is not None and t < CUES["drop"] + 0.5 else D.child.x + 180.0))
        hx_[i], hy_[i] = D.pts["string"]
    return xm, ground_y(xm), hx_, hy_


def _smooth_at(arr, t: float, sigma: float) -> float:
    k = np.arange(-3.0 * sigma, 3.0 * sigma + 1e-9, _DT)
    w = np.exp(-0.5 * (k / sigma) ** 2)
    return float((np.interp(t + k, _TG, arr) * w).sum() / w.sum())


# ---------------------------------------------------------------------------------------------
# the camera
# ---------------------------------------------------------------------------------------------
ZOOM_E = 1.2
CAM_E = Cam(8900.0, ground_y(X10) - 202.0 / ZOOM_E, ZOOM_E)   # the evening: the child's feet at screen y 742, heads 142 px
AHEAD = 0.25                                             # the camera runs this far ahead of the pair in time
STOP_D = 100.0                                           # how softly the travelling camera comes to rest at CAM_E.cx
ZOOM_RUN = 0.8                                           # a little closer than B9 as they set off: heads 94 px in the jumps


def _follow(t: float) -> Cam:
    """The travelling camera: on the pair's middle (smoothed), a quarter second ahead of it, coming softly to
    rest at CAM_E.cx as they slow down: the two run on into the right of the frame and drop there."""
    xm, gm, _, _ = _tables()
    x = _smooth_at(xm, t + AHEAD, 0.40)
    g = _smooth_at(gm, t + AHEAD, 0.55)
    x = CAM_E.cx - STOP_D * math.log1p(math.exp((CAM_E.cx - x) / STOP_D))
    w0 = ease(seg(t, 226.95, 227.7))
    cx = CAM9.cx + (x - CAM9.cx) * w0
    cy = CAM9.cy + 0.5 * (g - ground_y(CAM9.cx)) * w0
    return Cam(cx, cy, CAM9.zoom * (ZOOM_RUN / CAM9.zoom) ** ease(seg(t, 227.0, 228.6)))


def camera(t: float, r: float = 1.0) -> Cam:
    if t < PUSH[0]:
        return _follow(t)
    if t < SETTLE[0]:
        return Cam.ease(_follow(min(t, 237.5)), CAM_E, seg(t, *PUSH))
    # the settle: a slow pull-back to B10's zoom while the child slides to B10's place on the screen; its feet
    # stay at screen y 742 all the way, so that the ground under it sinks with the camera
    w = ease(seg(t, *SETTLE))
    B = S.CAM[END]
    z = CAM_E.zoom * (B.zoom / CAM_E.zoom) ** w
    sx0 = CAM_E.to_screen(X10, 0.0)[0]
    sx = sx0 + (B.to_screen(X10, 0.0)[0] - sx0) * w
    return Cam(X10 - (sx - CX) / z, ground_y(X10, r) - (742.0 - CY) / z, z)


# ---------------------------------------------------------------------------------------------
# the land: S.hill_world with the far layer drawn on its own camera
# ---------------------------------------------------------------------------------------------
def _rise(gone: float) -> float:
    return 1.0 - ease(seg(gone, 0.40, 1.0))


def _land(F, hour: float, gone: float, figures=(), skip=None, birds=None) -> float:
    sky(F, hour, gone=gone)
    cam = F.cam
    F.cam = _far_cam(cam)
    if birds is not None:
        birds(F)                                         # (behind the far ridge: they fly home and go down behind it)
    hills_back(F, back=(1.0, 0.0), hour=hour, gone=gone, house=S.HOUSE, rise=0.0)
    k = hour * (1.0 - seg(gone, 0.0, 0.12))
    if k > 0.0:                                          # at evening the window is lit: home
        wx, wy = home(F, S.HOUSE[0], depth=FAR, w=96.0, a=0.0)["window"]
        with F.depth(FAR):
            smudge(F, wx, wy, 46.0, 40.0, C.AMBER_GLOW, 0.55 * k, "glow", additive=True, power=2.2)
    F.cam = cam
    hills_back(F, back=(0.0, 1.0), hour=hour, gone=gone, house=None, rise=1.0)
    _run_flock(F)
    r = hills_front(F, rise=1.0, hour=hour, gone=gone)
    k = 1.0 - seg(gone, 0.0, 0.3)
    if k > 0.0:
        tree(F, 6840.0, hour=hour, a=k)
    for act in figures:
        if act is not None:
            S.sun_shadow(F, act, hour, a=act.a, rise=r)
    g = 1.0 - seg(gone, 0.1, 0.5)
    if g > 0.0:
        flowers(F, 4700.0, 9300.0, 150, seed=2, grow=g, rise=r, skip=skip)
    return r


# ---------------------------------------------------------------------------------------------
# birds
# ---------------------------------------------------------------------------------------------
FLOCK_RUN = dict(t=(228.3, 234.9), a=(-90.0, 205.0), b=(2260.0, 140.0), depth=0.6, n=6, s=0.55, seed=21)
FLOCK_HOME = dict(t=(239.3, 241.95), a=(1500.0, -70.0), b=(1860.0, 600.0), n=4, s=0.40, seed=33)


@lru_cache(maxsize=1)
def _flock_run_path():
    F_ = FLOCK_RUN
    t0, t1 = F_["t"]
    c0, c1 = camera(t0).depth(F_["depth"]), camera(t1).depth(F_["depth"])
    p0, p1 = np.array(c0.to_world(*F_["a"])), np.array(c1.to_world(*F_["b"]))
    return p0, (p1 - p0) / (t1 - t0)


def _run_flock(F):
    F_ = FLOCK_RUN
    if not (F_["t"][0] <= F.t <= F_["t"][1]):
        return
    p0, v = _flock_run_path()
    with F.depth(F_["depth"]):
        flock(F, p0[0], p0[1], F.t - F_["t"][0], F_["n"], F_["s"], vel=(float(v[0]), float(v[1])), seed=F_["seed"])


def _home_flock(F):
    """Four small birds fly home in the evening, down toward the house, and go behind the far ridge."""
    F_ = FLOCK_HOME
    if not (F_["t"][0] <= F.t <= F_["t"][1]):
        return
    c = F.cam.depth(FAR)
    p0, p1 = np.array(c.to_world(*F_["a"])), np.array(c.to_world(*F_["b"]))
    v = (p1 - p0) / (F_["t"][1] - F_["t"][0])
    with F.depth(FAR):
        flock(F, p0[0], p0[1], F.t - F_["t"][0], F_["n"], F_["s"], vel=(float(v[0]), float(v[1])), seed=F_["seed"])


# ---------------------------------------------------------------------------------------------
# the small tangle on its string: a balloon that lags behind the hand
# ---------------------------------------------------------------------------------------------
_BAL_W, _BAL_Z = 6.0, 0.55                               # its spring: angular frequency, damping
_BAL_S = np.arange(0.0, 1.6, _DT)
_BAL_H = np.exp(-_BAL_Z * _BAL_W * _BAL_S) * np.sin(_BAL_W * math.sqrt(1.0 - _BAL_Z ** 2) * _BAL_S)
_BAL_H = _BAL_H / _BAL_H.sum()
BAL_OFF = (240.2, 240.9)                                 # the lag lets go (the hand is still there)


def _run_k(t: float) -> float:
    a, b, c, d = RUN_LEAN
    return ease(seg(t, a, b)) * (1.0 - ease(seg(t, c, d)))


def _lean_run(t):
    return -STRING["lean"] - 150.0 * _run_k(t)


def _balloon(t: float):
    """Where the tangle floats (before its bob): above the hand, leaning back, lagging like a balloon."""
    _, _, hx_, hy_ = _tables()
    ts = t - _BAL_S
    lx = np.array([_lean_run(float(u)) for u in ts[::6]])
    lx = np.interp(ts, ts[::6][::-1], lx[::-1])
    bx = np.interp(ts, _TG, hx_) + lx
    by = np.interp(ts, _TG, hy_) - STRING["rise"]
    return float((bx * _BAL_H).sum()), float((by * _BAL_H).sum())


def _tangle(F, D) -> None:
    t = F.t
    hand = D.pts["string"]
    left = D.num["left"]
    lean = -STRING["lean"] * (1.0 - 2.0 * ease(left)) - 150.0 * _run_k(t)
    tx, ty = hand[0] + lean, hand[1] - STRING["rise"]
    w = 1.0 - ease(seg(t, *BAL_OFF))
    if w > 0.0:
        px, py = _balloon(t)
        tx, ty = tx + (px - tx) * w, ty + (py - ty) * w
    bx, by = float_at(F, (0.0, 0.0), rise=0.0, lean=0.0)
    on_string(F, tx + bx, ty + by, hand)


# ---------------------------------------------------------------------------------------------
# the child stays glad between the rest poses the performance passes through (setting off, arriving)
# ---------------------------------------------------------------------------------------------
GLAD = ((227.05, 227.25, 227.85, 228.05), (235.20, 235.35, 235.95, 236.05))


def _keep_glad(act, t: float) -> None:
    k = max(ease(seg(t, a, b)) * (1.0 - ease(seg(t, c, d))) for a, b, c, d in GLAD)
    if k <= 0.0:
        return
    P = act.pose
    act.pose = P.but(mouth=max(P["mouth"], 0.65 * k), joy=max(P["joy"], 0.35 * k), hair=max(P["hair"], 0.9 * k),
                     lid=min(P["lid"], 0.25 + 0.75 * (1.0 - k)))


# ---------------------------------------------------------------------------------------------
# the two figures; the friend fading as it walks off is faded whole, on a layer of its own
# ---------------------------------------------------------------------------------------------
def _pair(F, D, rim) -> None:
    """S.pair(F, D, rim, rim, shadow=0), except that a friend whose line is losing pressure (Act.a < 1, from
    242.87) is drawn at full pressure on a layer laid down at that alpha: figure() leaves the pale edge of the
    scarf tails at full strength while the rest fades, and it would vanish in one frame when the friend goes."""
    f = D.friend
    if f is None or f.a >= 1.0:
        S.pair(F, D, child_rim=rim, friend_rim=rim, shadow=0.0)
        return
    if f.a > 0.0:
        p = skia.Paint()
        p.setAlphaf(f.a)
        F.c.saveLayer(None, p)
        f.a = 1.0
        S.friend(F, f, rim, shadow=0.0)
        F.c.restore()
    S.child(F, D.child, rim, shadow=0.0)


# ---------------------------------------------------------------------------------------------
def draw(F):
    if S.joined(F, START, END):                          # the last 0.25 s: the hand-off picture B10
        return
    t = F.t
    F.set_skin("day")
    gone = seg(t, *GONE)
    r = _rise(gone)
    hour = ease(seg(t, *HOUR))
    D = AP.s10(t, ground=(lambda x: ground_y(x, r)) if r < 1.0 else ground_y, **CUES)
    _keep_glad(D.child, t)
    F.cam = camera(t, r)
    c, f = D.child, D.friend
    skip = (X9 - 70.0, X9 + 250.0) if F.cam.cx < 7390.0 else (X10 - 70.0, X10 + 250.0)
    _land(F, hour, gone, (c, f), skip, _home_flock)
    k = ease(seg(t, *RIM)) * (1.0 - seg(gone, 0.15, 0.55))
    rim = (mix(C.SUN_HALO, C.CORAL, 0.35 * hour), (1.0, -0.35), 0.55 * k) if k > 0.0 else None
    # while the child turns to the left the string is still in its far hand, behind it, and the tangle swings over
    # its head to the other side: the string passes BEHIND the head (drawn before the figures) until the middle of
    # the turn, where the hand becomes the near one (AP.s10 flips the figure at alone + 0.275)
    behind = CUES["alone"] <= t < CUES["alone"] + 0.275
    if behind:
        _tangle(F, D)
    _pair(F, D, rim)
    if not behind:
        _tangle(F, D)
