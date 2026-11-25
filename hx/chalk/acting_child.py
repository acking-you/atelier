"""hx.chalk.acting_child: the child's solo performances (sections s01 to s05, 0 to 138.2 s), the rest
states of the hand-offs B1 to B5, and the general acting tools. Read hx/chalk/doc/acting_child.md.

A performance is a pure function of the song's time that returns an Act: everything figure() needs
(pose, ground point, face, pinned hands, draw-on, pressure) plus the points and numbers the scene
needs to stage the things the child handles (a fingertip, two hand points, how far the desk has
been pushed). It draws nothing and imports no drawing module: places and things come in as arguments.

    a = s04(F.t)                                   # or perform(F.t)
    J = a.show(F)                                  # = figure(F, a.x, a.y, a.h, a.pose, "child", a.face, seed=3, a=a.a,
    phone_held(F, a.pts["phone"], -1.05, ...)      #          grab=a.grab, draw=a.draw)

How it is made: key poses (small changes to the rig's library), moved with overlapping action (the
eyes lead, then the head, the spine, the hands; the hair arrives last), anticipation and a small
overshoot; reactions (flinch, startle, stagger) are layers added on top with a fast attack and a
slow release; small steps keep the standing foot where it stands; every hold breathes and blinks
(the rig's alive). Hair follow-through is set from the head's speed without state. Times are the
song's (absolute seconds); every section takes its cue times as keyword arguments, with the
storyboard's values as defaults. Every section ends in the rest state of its hand-off (hold_B1 ..
hold_B5) and the next begins from it. No lyric text anywhere.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from .. import story as ST
from .figure import (BACK_STAND, CLING, CURL, LOOK_UP, R_HEAD, SIT_CURL, SIT_EDGE, SIT_FLOOR, SIT_HUG, STOPPED, TORSO,
                     WALK_BEAT, aim_foot, aim_hand, alive, curl_up_pose, figure, mixp, Pose, pose_joints, rebase,
                     sit_up_pose, slide_off_pose, solve, swap_sides, turn_round, walk_away, walk_to)

# (Act and beat_after are left out of the star import on purpose: acting_pair exports the same two names)
__all__ = ["perform", "s01", "s02", "s03", "s04", "s05",
           "hold_B1", "hold_B2", "hold_B3", "hold_B4", "hold_B5", "CHILD_HANDOFF",
           "move", "through", "chain", "react", "flinch", "startle", "stagger", "head_lift", "turn_to", "look_at", "reach_to",
           "carry", "sit_down", "stand_up", "sit_up", "curl_up", "small_step", "beat_at",
           "W_HEAD", "W_HAND", "W_BODY", "W_FLAT", "K_ACT", "K_BLINK", "K_SOFT", "K_SLOW", "K_HAND", "K_BODY", "K_LAND",
           "K_HIT", "K_EASE", "K_FALL", "S01_T", "S02_T", "S03_T", "S04_T", "S05_T", "HUSH", "PLANTED", "ON_RUG", "SIT_B",
           "HERO", "AIR", "BALLOON", "TABLE_TOP", "DESK_TOP", "SHOVE", "STUB_ANG", "FLOOR_SIT", "FLOOR_HUG", "EDGE_SIT"]

FLOOR, H0 = ST.FLOOR, ST.CHILD_H
BEAT0, BEAT = 0.265, 0.75
HALF_PI = math.pi / 2.0
_DT = 0.10                       # the look-back of the follow-through (seconds)


def beat_at(k: float) -> float:
    """The time of beat k of the song (beat 0 at 0.265 s, 0.75 s apart)."""
    return BEAT0 + BEAT * k


def beat_after(t: float) -> float:
    """The first beat at or after t."""
    return BEAT0 + BEAT * math.ceil((t - BEAT0) / BEAT - 1e-6)


# --------------------------------------------------------------------------
# what a performance returns
# --------------------------------------------------------------------------
class Act:
    """One moment of a performance. pose, x, y, face, grab, draw, a go into figure(); s scales the
    height (1 except where a scene asked for a shrink); J: the world joints of the pose (what figure()
    will return, before drawing and without the pinned hands: head neck crown mouth ha_f ha_b ...);
    h: the world height to draw it with (story.CHILD_H times s); pts: named world points of what the
    child handles; num: named numbers (cues for the scene: 0..1 ramps, world offsets)."""
    __slots__ = ("pose", "x", "y", "face", "grab", "draw", "a", "s", "h", "J", "pts", "num")

    def __init__(self, pose, x, y=FLOOR, face=1, grab=None, draw=1.0, a=1.0, s=1.0, J=None, pts=None, num=None, h=H0):
        self.pose, self.x, self.y, self.face, self.grab = pose, float(x), float(y), face, grab
        self.draw, self.a, self.s, self.h = draw, a, s, h * s
        self.J = pose_joints(pose, self.x, self.y, self.h, face) if J is None else J
        self.pts = {} if pts is None else pts
        self.num = {} if num is None else num

    def show(self, F, skin="child", seed: int = ST.CHILD_SEED, a: float = 1.0, **kw):
        """Draw it: figure(F, x, y, h, pose, skin, face, seed, a, grab, draw, **kw) -> world joints
        (with the pinned hands applied). kw: rim=..., t=... as figure() takes them."""
        if self.draw <= 0.0 or self.a * a <= 0.0:
            return self.J
        return figure(F, self.x, self.y, self.h, self.pose, skin, self.face, seed=seed, a=self.a * a, grab=self.grab,
                      draw=self.draw, **kw)


# --------------------------------------------------------------------------
# small maths
# --------------------------------------------------------------------------
def _c(u):
    return 0.0 if u <= 0.0 else (1.0 if u >= 1.0 else u)


def _sm(u):
    u = 0.0 if u <= 0.0 else (1.0 if u >= 1.0 else u)
    return u * u * (3.0 - 2.0 * u)


def _seg(t, a, b):
    return _c((t - a) / (b - a))


def _ramp(t, a, b):
    return _sm((t - a) / (b - a))


def _env(t, t0, up=0.10, hold=0.08, down=0.55):
    """A reaction's envelope: 0 before t0, up to 1 fast (slowing in), held, released slowly."""
    d = t - t0
    if d <= 0.0 or d >= up + hold + down:
        return 0.0
    if d < up:
        v = 1.0 - d / up
        return 1.0 - v * v * v
    if d < up + hold:
        return 1.0
    return 1.0 - _sm((d - up - hold) / down)


def _bell(t, t0, dur):
    """0..1..0 over dur from t0 (a blink, a glance)."""
    u = (t - t0) / dur
    return math.sin(math.pi * u) ** 2 if 0.0 < u < 1.0 else 0.0


def _blink(t, t0, dur=0.26):
    """An acted blink that closes at t0 + 0.4 dur."""
    u = (t - t0) / dur
    if u <= 0.0 or u >= 1.0:
        return 0.0
    return _sm(u / 0.32) if u < 0.32 else (1.0 if u < 0.48 else 1.0 - _sm((u - 0.48) / 0.52))


# --------------------------------------------------------------------------
# overlapping action: one move between two poses
# --------------------------------------------------------------------------
_GROUPS = dict(
    eyes=("look", "gaze", "eye", "lid", "blink", "brow", "lift", "spark"),
    head=("neck", "tilt", "hturn"),
    body=("lean", "bend", "roll", "pel", "pz", "chest", "press", "open"),
    feet=("ff", "fb", "ffz", "fbz", "kf", "kb", "af", "ab", "front", "turn", "rot"),
    hand=("hf", "hb", "hfz", "hbz", "ef", "eb", "over"),
    mouth=("mouth", "mopen", "joy", "blush"),
    hair=("hair", "sway", "bob"),
)
_DYN = dict(eyes=0, head=1, body=1, feet=0, hand=2, mouth=2, hair=3)      # 1: anticipation + overshoot, 2: overshoot, 3: hair
_PAIRK = frozenset(k for k, v in Pose().items() if isinstance(v, tuple))
_FLAGK = frozenset(("front", "over"))


def _compile(**win):
    out = []
    for g, keys in _GROUPS.items():
        t0, t1 = win[g]
        for k in keys:
            out.append((k, t0, 1.0 / (t1 - t0), _DYN[g], k in _PAIRK, k in _FLAGK))
    return tuple(out)


W_HEAD = _compile(eyes=(0.0, 0.50), head=(0.08, 0.66), body=(0.16, 0.82), feet=(0.16, 0.82), hand=(0.26, 0.94),
                  mouth=(0.34, 0.86), hair=(0.46, 1.0))          # a look, a lift: the eyes lead
W_HAND = _compile(eyes=(0.0, 0.42), head=(0.14, 0.74), body=(0.20, 0.90), feet=(0.20, 0.90), hand=(0.04, 0.72),
                  mouth=(0.30, 0.80), hair=(0.45, 1.0))          # a reach, a wipe: the hand leads after the eyes
W_BODY = _compile(eyes=(0.04, 0.60), head=(0.16, 0.92), body=(0.0, 0.78), feet=(0.0, 0.72), hand=(0.10, 0.94),
                  mouth=(0.30, 0.80), hair=(0.40, 1.0))          # a sit, a rise, a step: the weight leads
W_FLAT = _compile(eyes=(0.0, 1.0), head=(0.0, 1.0), body=(0.0, 1.0), feet=(0.0, 1.0), hand=(0.0, 1.0), mouth=(0.0, 1.0),
                  hair=(0.0, 1.0))


def move(a: Pose, b: Pose, u: float, win=W_HEAD, ant: float = 0.07, over: float = 0.07, blink: float = 0.0,
         warp: float = 0.0) -> Pose:
    """One acted move from pose a to pose b, u = 0..1 over the whole move. win: which part leads
    (W_HEAD the eyes and the head, W_HAND the hand, W_BODY the weight, W_FLAT everything together).
    ant: the small dip the other way before head and spine go; over: how far they overshoot before
    they settle; blink: a blink on the way (at 40 percent); warp: > 0 a fast start that slows in (a
    reaction), < 0 a slow start (a tired move). Every in-between is a drawing. 0.02 ms."""
    u = _c(u)
    if warp > 0.0:
        u = 1.0 - (1.0 - u) ** (1.0 + warp)
    elif warp < 0.0:
        u = u ** (1.0 - warp)
    out = Pose()
    for k, t0, inv, dyn, pair, flag in win:
        v = (u - t0) * inv
        v = 0.0 if v <= 0.0 else (1.0 if v >= 1.0 else v)
        w = v * v * (3.0 - 2.0 * v)
        if flag:
            out[k] = a[k] if w < 0.5 else b[k]
            continue
        if dyn:
            if over and v > 0.6:
                w += over * math.sin(math.pi * (v - 0.6) / 0.4) * (1.6 if dyn == 3 else 1.0)
            if ant and dyn == 1:
                e = (u - t0 + 0.14) / 0.22
                if 0.0 < e < 1.0:
                    s = math.sin(math.pi * e)
                    w -= ant * s * s
        if pair:
            p, q = a[k], b[k]
            out[k] = (p[0] + (q[0] - p[0]) * w, p[1] + (q[1] - p[1]) * w)
        else:
            out[k] = a[k] + (b[k] - a[k]) * w
    if blink:
        out["blink"] = max(out["blink"], blink * math.exp(-((u - 0.40) / 0.075) ** 2))
    return out


# kinds of a key: (window, anticipation, overshoot, blink, warp)
K_ACT = (W_HEAD, 0.07, 0.07, 0.0, 0.0)
K_BLINK = (W_HEAD, 0.07, 0.07, 1.0, 0.0)
K_SOFT = (W_HEAD, 0.0, 0.03, 0.0, 0.0)          # small and tired: no wind-up
K_SLOW = (W_HEAD, 0.0, 0.0, 0.0, -0.5)          # sinking: a slow start
K_HAND = (W_HAND, 0.05, 0.06, 0.0, 0.0)
K_BODY = (W_BODY, 0.06, 0.07, 0.0, 0.0)
K_LAND = (W_BODY, 0.0, 0.14, 0.0, 0.6)          # weight coming down: fast, lands and settles
K_HIT = (W_FLAT, 0.0, 0.10, 0.0, 1.4)           # a jolt
K_EASE = (W_FLAT, 0.0, 0.0, 0.0, 0.0)
K_FALL = (W_FLAT, 0.0, 0.08, 0.0, -0.7)         # a fall: it starts slowly and is fastest when it lands


def _table(fn, n=64):
    """A move of the rig that costs half a millisecond a call (sit_up_pose ...), sampled once at n + 1 places."""
    return tuple(fn(i / n) for i in range(n + 1))


def _look(tab, w):
    """The pose at w = 0..1 of a sampled move (straight between two neighbouring samples). 0.005 ms."""
    w = _c(w) * (len(tab) - 1)
    i = min(int(w), len(tab) - 2)
    return mixp(tab[i], tab[i + 1], w - i)


def _get(p):
    return p() if callable(p) else p


def through(poses, us, u: float, win=W_FLAT, warp: float = 0.0) -> Pose:
    """One move that passes THROUGH breakdown poses: poses[0] at us[0] = 0 .. poses[-1] at us[-1] = 1,
    a smooth curve through all of them (it starts and ends slowly, and does not stop on the way).
    win: which part leads, as in move(). 0.03 ms."""
    u = _c(u)
    if warp > 0.0:
        u = 1.0 - (1.0 - u) ** (1.0 + warp)
    elif warp < 0.0:
        u = u ** (1.0 - warp)
    n = len(poses) - 1
    out = Pose()
    for k, t0, inv, dyn, pair, flag in win:
        v = (u - t0) * inv
        v = 0.0 if v <= 0.0 else (1.0 if v >= 1.0 else v)
        i = 0
        while i < n - 1 and v > us[i + 1]:
            i += 1
        d = us[i + 1] - us[i]
        s = (v - us[i]) / d
        if flag:
            out[k] = poses[i][k] if s < 0.5 else poses[i + 1][k]
            continue
        s2 = s * s
        s3 = s2 * s
        h00, h10, h01, h11 = 2.0 * s3 - 3.0 * s2 + 1.0, s3 - 2.0 * s2 + s, -2.0 * s3 + 3.0 * s2, s3 - s2
        a, b = poses[i][k], poses[i + 1][k]
        if pair:
            val = []
            for j in (0, 1):
                m0 = (b[j] - poses[i - 1][k][j]) / (us[i + 1] - us[i - 1]) * d if i > 0 else 0.0
                m1 = (poses[i + 2][k][j] - a[j]) / (us[i + 2] - us[i]) * d if i < n - 1 else 0.0
                val.append(h00 * a[j] + h10 * m0 + h01 * b[j] + h11 * m1)
            out[k] = (val[0], val[1])
        else:
            m0 = (b - poses[i - 1][k]) / (us[i + 1] - us[i - 1]) * d if i > 0 else 0.0
            m1 = (poses[i + 2][k] - a) / (us[i + 2] - us[i]) * d if i < n - 1 else 0.0
            out[k] = h00 * a + h10 * m0 + h01 * b + h11 * m1
    return out


def _state(keys, i, t, P0):
    if i < 0:
        return _get(P0)
    key = keys[i]
    t0, dur, pose, kind = key[0], key[1], key[2], key[3]
    u = (t - t0) / dur
    if u >= 1.0:
        return _get(pose)
    if i == 0:
        a = _get(P0)
    else:
        p = keys[i - 1]
        a = _get(p[2]) if t0 >= p[0] + p[1] - 1e-9 else _state(keys, i - 1, t0, P0)
    win, ant, over, blink, warp = kind
    if len(key) > 4:                                       # breakdowns on the way: ((u, pose), ...)
        mids = key[4]
        return through([a] + [m[1] for m in mids] + [_get(pose)], [0.0] + [m[0] for m in mids] + [1.0], u, win, warp)
    return move(a, _get(pose), u, win, ant, over, blink, warp)


def chain(t: float, P0, keys) -> Pose:
    """A sequence of acted moves. keys: [(t0, dur, pose, kind), ...] sorted by t0: at t0 a move of dur
    seconds begins toward `pose` (a Pose, or a function without arguments giving one), from wherever
    the figure is then (the pose of the key before, or the middle of its move). kind: one of K_ACT,
    K_BLINK, K_SOFT, K_SLOW, K_HAND, K_BODY, K_LAND, K_HIT, K_EASE. A fifth entry ((u, pose), ...)
    gives breakdown poses the move passes through (see through()). Before the first key: P0."""
    i = len(keys) - 1
    while i >= 0 and t < keys[i][0]:
        i -= 1
    return _state(keys, i, t, P0)


# --------------------------------------------------------------------------
# where the head is (cheaply), follow-through, aliveness
# --------------------------------------------------------------------------
def _head_q(P):
    """The head's centre and its lean, as seen, in body units from the ground point (no solve: the
    spine's maths of the rig for a profile, flattened by the turn, turned by rot). About 2 us."""
    px, py = P["pel"]
    lean, bend = P["lean"], P["bend"]
    ux, uy = math.sin(lean), math.cos(lean)
    L = TORSO * (1.0 - 0.06 * abs(bend))
    nx, ny = px + ux * L, py + uy * L
    k = bend * TORSO * 0.42
    tx, ty = nx - (px + ux * TORSO * 0.5 - uy * k), ny - (py + uy * TORSO * 0.5 + ux * k)
    n = math.hypot(tx, ty) + 1e-9
    tx, ty = tx / n, ty / n
    nk = max(-0.8, min(0.8, P["neck"]))
    cn, sn = math.cos(nk), math.sin(nk)
    hdx, hdy = tx * cn + ty * sn, -tx * sn + ty * cn
    ct = math.cos(P["turn"] * HALF_PI)
    X, Y = px + (nx + hdx * R_HEAD * 0.88 - px) * ct, ny + hdy * R_HEAD * 0.88
    r = P["rot"]
    if r:
        c_, s_ = math.cos(r), math.sin(r)
        X, Y = X * c_ + Y * s_, -X * s_ + Y * c_
    return X, Y, math.atan2(hdx, hdy) * ct


def _follow(P1, P0, dxb=0.0, dyb=0.0, k=1.0):
    """sway / bob from how fast the head has moved over the last _DT seconds (dxb, dyb: how far the
    ground point itself has travelled, body units toward `face` and up)."""
    ax, ay, _ = _head_q(P1)
    bx, by, _ = _head_q(P0)
    vx, vy = (ax - bx + dxb) / _DT, (ay - by + dyb) / _DT
    return P1.but(sway=max(-1.0, min(1.0, P1["sway"] + 0.9 * k * vx)), bob=max(-1.0, min(1.0, P1["bob"] - 0.9 * k * vy)))


def _calm(t, spans, e=0.14):
    """1 outside the spans (a, b), 0 inside, eased over e seconds at their ends: how much of a chance
    blink may show (a span covers an acted beat that the eyes must carry)."""
    k = 1.0
    for a, b in spans:
        if a - e < t < b + e:
            k = min(k, 1.0 - _sm((t - a + e) / e) * (1.0 - _sm((t - b) / e)))
    return k


def _live(P, t, breath=1.0, blink=1.0, shift=1.0):
    """The rig's alive() for the child (seed 3); no chance blink while the eyes are shut or acting."""
    if blink:
        blink *= _c((P["eye"] - 0.12) / 0.10) * (1.0 - _c(P["blink"] / 0.25))
    return alive(P, t, ST.CHILD_SEED, breath=breath, blink=blink, shift=shift)


# --------------------------------------------------------------------------
# general tools (poses in, poses out)
# --------------------------------------------------------------------------
def _is_up(P):
    return P["pel"][1] > 0.30 and abs(P["rot"]) < 0.4


def flinch(P: Pose, k: float = 1.0) -> Pose:
    """P pulled in by a flinch of strength k (0..1.5; animate k with a fast attack and a slow
    release, see react()): the head ducks between the shoulders, the eyes shut, the hands jerk in,
    a standing figure's knees give. Works on standing, sitting and lying poses."""
    if k <= 0.0:
        return P
    up = 1.0 if _is_up(P) else 0.0
    lie = 1.0 if abs(P["rot"]) > 0.5 else 0.0
    px, py = P["pel"]
    lx, ly = P["look"]
    hf, hb = P["hf"], P["hb"]
    kh = k * (1.0 - 0.7 * lie)
    return P.but(pel=(px - 0.010 * k * up, py - 0.030 * k * up), bend=P["bend"] + 0.20 * k * (1.0 - 0.6 * lie),
                 lean=P["lean"] + 0.04 * k * up, neck=P["neck"] + 0.20 * k, look=(lx, max(-1.0, ly - 0.22 * k)),
                 blink=max(P["blink"], min(1.0, 1.4 * k)), brow=min(1.0, P["brow"] + 0.45 * k),
                 mouth=P["mouth"] - 0.25 * k, hf=(hf[0] + 0.012 * kh, hf[1] + 0.035 * kh),
                 hb=(hb[0] + 0.012 * kh, hb[1] + 0.035 * kh), hair=max(0.0, P["hair"] - 0.2 * k), bob=P["bob"] + 0.5 * k)


def startle(P: Pose, k: float = 1.0) -> Pose:
    """P with a start of strength k: the shoulders jump, the head comes up and back, the eyes wide,
    the hands lift a little off the body, the hair flies. (The half step back is the caller's.)"""
    if k <= 0.0:
        return P
    lx, ly = P["look"]
    hf, hb = P["hf"], P["hb"]
    px, py = P["pel"]
    return P.but(pel=(px - 0.012 * k, py + 0.012 * k), lean=P["lean"] - 0.10 * k, bend=P["bend"] - 0.16 * k,
                 neck=P["neck"] - 0.22 * k, look=(lx, min(1.0, ly + 0.45 * k)), eye=P["eye"] + (1.3 - P["eye"]) * min(1.0, k),
                 lid=P["lid"] * (1.0 - 0.6 * min(1.0, k)), lift=min(1.0, P["lift"] + 0.7 * k), mopen=max(P["mopen"], 0.3 * k),
                 hf=(hf[0] + 0.03 * k, hf[1] + 0.05 * k), hb=(hb[0] - 0.02 * k, hb[1] + 0.05 * k),
                 hair=min(1.0, P["hair"] + 0.6 * k), bob=P["bob"] + 0.6 * k)


def stagger(P: Pose, k: float = 1.0, side: int = 1) -> Pose:
    """P knocked by the shoulder of someone coming the other way, strength k: the upper body is
    thrown back and the knees give, the head is left behind, the arms fly out a little. side +1:
    the near shoulder is hit (the body twists open toward us), -1 the far one (it twists away, we
    see more of its back). Layer it with a fast attack; move the ground point for the step it
    forces (the sections do)."""
    if k <= 0.0:
        return P
    s = 1.0 if side >= 0 else -1.0
    hf, hb = P["hf"], P["hb"]
    px, py = P["pel"]
    return P.but(turn=P["turn"] + (0.30 if s > 0 else -0.24) * k, hturn=P["hturn"] - 0.22 * k * s, roll=P["roll"] + 0.14 * k * s,
                 lean=P["lean"] - (0.14 if s > 0 else 0.18) * k, pel=(px - 0.022 * k, py - 0.022 * k), tilt=P["tilt"] + 0.15 * k,
                 neck=P["neck"] + 0.06 * k, hf=(hf[0] - 0.05 * k * s, hf[1] + 0.05 * k), hb=(hb[0] + 0.06 * k * s, hb[1] + 0.04 * k),
                 hfz=P["hfz"] + 0.05 * k, hbz=P["hbz"] + 0.04 * k, blink=max(P["blink"], min(1.0, 1.2 * k)),
                 brow=min(1.0, P["brow"] + 0.3 * k), bob=P["bob"] + 0.3 * k)


def react(P: Pose, t: float, times, fn=flinch, k: float = 1.0, up: float = 0.09, hold: float = 0.08, down: float = 0.55,
          grow: float = 0.0, **kw) -> Pose:
    """A reaction layered on P at each of `times` (two frames after the cue): fn is flinch, startle
    or stagger; up / hold / down shape its envelope (seconds); grow: each one stronger than the last
    by this share. react(P, t, HITS_1, flinch, 1.0, grow=0.25)."""
    for i, t0 in enumerate(times):
        e = _env(t, t0 + 0.05, up, hold, down)
        if e > 0.0:
            P = fn(P, e * k * (1.0 + grow * i), **kw)
    return P


def head_lift(t: float, t0: float, a: Pose = STOPPED, b: Pose = LOOK_UP, dur: float = 1.2, spark_at: float | None = None) -> Pose:
    """The head lift as one choreography from t0: a small dip first, a slow rise that goes about 7
    percent too far and settles, a blink on the way (at 40 percent), the hair arriving last; the
    spark comes into the eyes at spark_at (default: with the end of the move). Before t0: a."""
    P = move(a, b, (t - t0) / dur, W_HEAD, 0.07, 0.07, 1.0)
    ts = t0 + dur * 0.92 if spark_at is None else spark_at
    return P.but(spark=max(P["spark"], _ramp(t, ts, ts + 0.3)))


def turn_to(a: Pose, b: Pose, u: float, hop: float = 1.0) -> Pose:
    """A turn on the spot from a to b (their `turn` keys differ), u = 0..1: the rig's turn_round (the
    head leads, the weight dips, the feet are picked up one after the other)."""
    return turn_round(a, b, u, 0.30, hop)


def look_at(P: Pose, x: float, y: float, target, h: float = H0, face: int = 1, k: float = 1.0, head: float = 0.5) -> Pose:
    """P with head and eyes turned to a WORLD point (x, y: the figure's ground point). k: how much
    (0..1: animate it; the eyes are there at k = 0.5, the head at k = 1, so the eyes lead); head: how
    much of the way the head goes (the eyes do the rest). Works standing, sitting, lying, at any turn."""
    if k <= 0.0:
        return P
    hx, hy, hang = _head_q(P)
    dx, dy = face * (target[0] - x) / h - hx, (y - target[1]) / h - hy          # body units: toward face, up
    n = math.hypot(dx, dy) + 1e-9
    dx, dy = dx / n, dy / n
    ha = max(-0.5, min(0.5, 0.7 * hang)) + P["tilt"] + P["rot"]
    c_, s_ = math.cos(ha), math.sin(ha)
    sx, sy = dx * c_ - dy * s_, dx * s_ + dy * c_                                 # in the head's frame
    ke, kh = _sm(min(1.0, k * 2.0)), _sm(max(0.0, k * 2.0 - 1.0) if head else 0.0) * head
    yaw0 = P["turn"] + P["hturn"]                                                # quarter turns: 0 toward face, 1 toward us
    want = 1.0 - sx                                                              # 0 .. 2
    dh = max(-0.5, min(0.5, (want - yaw0))) * kh
    yaw = (yaw0 + dh) * HALF_PI
    lx, ly = P["look"]
    cy = math.cos(yaw)
    look_x = lx + (0.25 + 0.40 * abs(sx) - lx) * kh              # the face slides toward what it looks at
    gx = max(-1.0, min(1.0, 1.25 * (sx - look_x * cy)))
    look_y = ly + (0.75 * sy - ly) * kh
    gy = max(-1.0, min(1.0, 1.3 * sy - 0.6 * look_y))
    g0 = P["gaze"]
    return P.but(hturn=P["hturn"] + dh, look=(look_x, look_y), neck=P["neck"] - 0.30 * sy * kh * abs(cy),
                 gaze=(g0[0] + (gx - g0[0]) * ke, g0[1] + (gy - g0[1]) * ke))


def reach_to(P: Pose, x: float, y: float, point, h: float = H0, face: int = 1, which: str = "f", k: float = 1.0,
             lean: float = 1.0, arc: float = 0.03) -> Pose:
    """P with one hand ('f' near, 'b' far) reaching to a WORLD point; k = 0..1 brings the hand there
    from where P has it (a little arc on the way), the spine leaning after it when the point is far
    (lean scales that). Beyond reach the arm stretches toward the point and stops short."""
    if k <= 0.0:
        return P
    bx, by = face * (point[0] - x) / h, (y - point[1]) / h
    r = P["rot"]
    if r:
        c_, s_ = math.cos(r), math.sin(r)
        bx, by = bx * c_ - by * s_, bx * s_ + by * c_
    hx, hy, _ = _head_q(P)
    far = _sm((math.hypot(bx - P["pel"][0], by - (P["pel"][1] + 0.24)) - 0.26) / 0.22) * lean
    sg = 1.0 if bx >= P["pel"][0] else -1.0
    Q = P
    if far > 0.0 and not r:
        ct = math.cos(P["turn"] * HALF_PI)
        Q = P.but(lean=P["lean"] + 0.22 * far * sg * ct, roll=P["roll"], pel=(P["pel"][0] + 0.022 * far * sg, P["pel"][1] - 0.008 * far))
    Q = aim_hand(Q, which, (bx, by))
    if k >= 1.0:
        return Q
    w = _sm(k)
    key = "h" + which
    out = mixp(P, Q, w)
    a_ = arc * math.sin(math.pi * w)
    out[key] = (out[key][0], out[key][1] + a_)
    return out


def carry(P: Pose, x: float, y: float, left, right, h: float = H0, face: int = 1, k: float = 1.0):
    """P with both hands on two WORLD points (left and right as seen on the paper): two halves of a
    drawing, a thing carried. Returns (pose, grab) for figure(..., grab=grab). k = 0..1 brings the
    hands there. Which hand is on which side follows the pose's turn."""
    tn = P["turn"] % 4.0
    if 0.5 <= tn <= 1.5:                             # facing us: the near side is on the -face side of the paper
        near_left = face > 0
    elif 2.5 <= tn <= 3.5:                           # the back view
        near_left = face < 0
    else:                                            # a profile: the near hand takes the point nearer the body
        near_left = abs(left[0] - x) <= abs(right[0] - x)
    pf, pb = (left, right) if near_left else (right, left)
    Q = reach_to(reach_to(P, x, y, pf, h, face, "f", 1.0, 0.0), x, y, pb, h, face, "b", 1.0, 0.0)
    if k >= 1.0:
        return Q, {"f": tuple(pf), "b": tuple(pb)}
    return mixp(P, Q, _sm(k)), None


def _hands(P, x, y, h, face, pf=None, pb=None, kf=1.0, kb=1.0, arc=0.02):
    """P with the near and / or the far hand brought to WORLD points (kf, kb = 0..1 on the way, on a small arc).
    No lean: what the sections use where reach_to would lean the spine after the hand."""
    Q = P
    for which, pt, k in (("f", pf, kf), ("b", pb, kb)):
        if pt is None or k <= 0.0:
            continue
        key = "h" + which
        A_ = aim_hand(Q, which, (face * (pt[0] - x) / h, (y - pt[1]) / h), True)
        if k >= 1.0:
            Q = A_
        else:
            w = _sm(k)
            a0, a1 = Q[key], A_[key]
            z0, z1 = Q[key + "z"], A_[key + "z"]
            Q = Q.but(**{key: (a0[0] + (a1[0] - a0[0]) * w, a0[1] + (a1[1] - a0[1]) * w + arc * math.sin(math.pi * w)),
                         key + "z": z0 + (z1 - z0) * w})
    return Q


def _edge(sheet):
    """How far outside a half's grip point (things.family_held: 13 sheet units inside its outer edge) the hand that
    holds it is put, so that the mitt shows beside the paper instead of under it (world units)."""
    return 13.0 * sheet + 5.0


def _tip(J, which="f", ext=0.036, h=H0):
    """The fingertip of a hand: the end of the mitt, along the forearm."""
    q, e = J["ha_" + which], J["el_" + which]
    d = q - e
    n = math.hypot(d[0], d[1]) + 1e-9
    return q + d * (ext * h / n)


def _seen(P, **kw):
    """P with hands (hf, hb) and ankles (ff, fb) put where they are to be SEEN (body units from the ground point)."""
    for k, pt in kw.items():
        P = (aim_hand if k[0] == "h" else aim_foot)(P, k[1], pt, True)
    return P


def _finish(t, raw, h, quiet=(), breath=1.0, shift=1.0, follow=1.0):
    """raw(t) -> (pose, x, y, face). The follow-through from raw(t - _DT), then the rig's aliveness."""
    P, x, y, face = raw(t)
    if follow:
        P0, x0, y0, _ = raw(t - _DT)
        P = _follow(P, P0, face * (x - x0) / h, (y0 - y) / h, follow)
    return _live(P, t, breath, _calm(t, quiet), shift), x, y, face


# ==========================================================================
# s01: the room (0 to 36.27)
# ==========================================================================
_SX, _SY = ST.CURL_X, ST.SOFA_SEAT_Y            # the ground point of everything that happens on the sofa


def _sw(px, py):
    """A world point as seen from the sofa's ground point, in body units (h = 380)."""
    return ((px - _SX) / H0, (_SY - py) / H0)


S01_T = dict(draw=(9.27, 11.3), wake=12.34, sag=(13.29, 14.87), hero=(16.5, 18.0), cross=(20.79, 21.2, 21.6),
             situp=(22.0, 24.2), crows=24.27, speak=(28.6, 30.6), wipe=31.58, again=(32.0, 33.6), off=(33.6, 36.0))

AIR = (_SX + 160.0, _SY - 62.0)                # where the hand draws in the air while the hero appears: lifted off the
                                                #   armrest's outer end, beside the chin, clear of the face (the FAR hand)
HERO = (965.0, 425.0, 150.0)                    # the hero on the wall: feet x, y, height (the things doc's place)
BALLOON = (_SX + 150.0, _SY - 262.0, 76.0)      # the speech balloon: centre x, y, radius (clear of the sitting child's head)

L_WAKE = CURL.but(eye=0.52, lid=0.9, brow=0.85, gaze=(-0.2, 0.1), hair=0.85, tilt=CURL["tilt"] - 0.07, neck=CURL["neck"] - 0.10,
                  mouth=-0.4)
L_CLING = CLING
L_PRESS = CLING.but(press=1.0, bend=CLING["bend"] + 0.16, neck=CLING["neck"] + 0.20, tilt=CLING["tilt"] + 0.10, eye=0.22,
                    brow=1.0, mouth=-0.6, hair=0.55, look=(0.2, -0.12))
_HANG = (_SX + 72.0, _SY + 50.0)               # the far hand, slid off the armrest: it hangs before the sofa's front
L_BEAR = _seen(CLING.but(press=0.7, bend=CLING["bend"] + 0.08, neck=CLING["neck"] + 0.10, tilt=CLING["tilt"] + 0.05, eye=0.42,
                         brow=0.85, hair=0.7, gaze=(0.0, -0.3)), hb=_sw(*_HANG))                      # a hand has slid off and hangs
L_HAND = _seen(L_BEAR.but(eye=0.5, gaze=(-0.3, 0.5)), hb=_sw(AIR[0] - 30.0, AIR[1] + 34.0))             # it lifts
L_DRAW = _seen(CLING.but(press=0.35, neck=-0.42, tilt=-0.30, look=(0.16, 0.34), eye=0.85, lid=0.65, brow=0.25, lift=0.45,
                         mouth=-0.08, hair=0.75, gaze=(0.0, 0.5)), hb=_sw(AIR[0], AIR[1]))
L_ADMIRE = CLING.but(press=0.3, neck=-0.46, tilt=-0.32, look=(0.16, 0.40), eye=0.95, lid=0.45, brow=0.1, lift=0.5, mouth=0.22,
                     hair=0.85, gaze=(0.0, 0.6))
L_HURT = CLING.but(press=0.6, neck=-0.05, tilt=-0.05, look=(0.2, -0.1), eye=0.5, lid=0.9, brow=0.95, mouth=-0.55, hair=0.4,
                   gaze=(0.0, -0.6))
L_FALL = CURL.but(eye=0.42, lid=1.0, brow=0.9, mouth=-0.5, gaze=(0.0, -0.7), hair=0.15, press=0.5)
SIT_B = SIT_CURL                                 # sitting on the seat, hugging its knees (the rig's SIT_SOFA written from the
                                                 #   curl's ground point: hips 40 units left of it): where sit_up_pose ends
_TAB_UP = _table(sit_up_pose)                    # the rig's moves between lying and upright, sampled (space only: the
_TAB_CURL = _table(curl_up_pose)                 # timing is given here)
S_WATCH = SIT_B.but(hturn=-0.25, neck=0.0, look=(0.62, 0.12), eye=0.75, lid=0.8, brow=0.4, gaze=(0.5, 0.35), bend=0.44,
                    hair=0.12, mouth=-0.3)
S_BREATH = SIT_B.but(hturn=-0.05, neck=-0.02, look=(0.30, 0.02), eye=0.85, lid=0.6, brow=0.75, lift=0.2, bend=0.36, lean=0.16,
                     chest=0.9, mouth=-0.2, mopen=0.1, hair=0.2)
S_SPEAK = S_BREATH.but(mopen=0.85, mouth=-0.05, chest=0.3, bend=0.40, neck=-0.06, look=(0.32, 0.08), lift=0.35)
S_SPEAK_B = S_SPEAK.but(mopen=0.25, chest=0.0, neck=-0.02, brow=0.85, lift=0.2, gaze=(0.4, 0.5))
S_SPEAK_C = S_SPEAK.but(mopen=0.60, chest=0.1, brow=0.9, gaze=(0.45, 0.55), eye=0.8)
S_NOTHING = SIT_B.but(mopen=0.10, mouth=-0.5, brow=1.0, eye=0.7, lid=0.8, gaze=(0.45, 0.6), look=(0.3, -0.1), neck=0.1,
                      bend=0.5)
S_SHUT = SIT_B.but(mouth=-0.55, brow=0.95, eye=0.55, gaze=(0.45, 0.55), look=(0.3, -0.25), neck=0.16)
S_WIPE = SIT_B.but(mouth=-0.5, brow=0.9, eye=0.4, lid=1.0, look=(0.3, -0.2), neck=0.12, bend=0.5, hturn=-0.1)
S_AFTER = SIT_B.but(mouth=-0.5, brow=0.8, eye=0.5, look=(0.3, -0.4), gaze=(0.0, -0.3))
S_SMALL = S_AFTER.but(mopen=0.30, mouth=-0.2, look=(0.3, -0.12), neck=0.12, eye=0.62, brow=0.9, chest=0.5, gaze=(0.3, 0.3))
S_DOWN = SIT_B.but(neck=0.42, bend=0.68, look=(0.3, -0.8), eye=0.3, brow=0.9, mouth=-0.55, hair=0.0)
_OFF_DX, _OFF_DY = (_SX - ST.X1) / H0, (FLOOR - _SY) / H0
S_STOOD = rebase(STOPPED, _OFF_DX, _OFF_DY)      # STOPPED at (X1, FLOOR), written from the sofa's ground point
_TAB_OFF = _table(lambda w: rebase(slide_off_pose(w, -_OFF_DX, _OFF_DY)[0], _OFF_DX, _OFF_DY))    # off the sofa, likewise
_OFF_DUR = 2.18


def _air_path(u):
    """The little figure the hand draws in the air (u = 0..1), in units of the hero's height about its middle."""
    if u < 0.72:
        v = u / 0.72
        return 0.16 * math.sin(2.0 * math.pi * 4.0 * v) * (0.4 + 0.6 * math.sin(math.pi * v)), -0.5 + 0.95 * v
    v = _sm((u - 0.72) / 0.28)
    return -0.55 * math.sin(math.pi * v * 0.8), 0.45 - 0.55 * v


def _s01_raw(t, T, tip, hero, balloon, window):
    c0, c1, c2 = T["cross"]
    s0, s1 = T["situp"]
    k0, k1 = T["speak"]
    wp = T["wipe"]
    a0, a1 = T["again"]
    o0, o1 = T["off"]
    h0, h1 = T["hero"]
    g0, g1 = T["sag"]
    wk = T["wake"]
    su = (s1 - s0) * 0.94
    keys = (
        (wk - 0.06, 0.85, L_WAKE, K_SOFT),
        (g0 + 0.04, 1.15, L_CLING, K_ACT),
        (g1 + 0.02, 0.42, L_PRESS, K_LAND),
        (g1 + 0.62, 0.80, L_BEAR, K_SOFT),
        (h0 - 0.46, 0.50, L_HAND, K_HAND),
        (h0 + 0.22, 1.05, L_DRAW, K_ACT),
        (h1 + 0.30, 0.95, L_ADMIRE, K_SOFT),
        (c0 + 0.16, 0.36, L_HURT, K_SLOW),
        (c1 + 0.16, 0.60, L_FALL, K_SLOW),
        (s0, su, SIT_B, K_EASE),
        (T["crows"] + 0.25, 0.95, S_WATCH, K_ACT),
        (k0 - 0.46, 0.44, S_BREATH, K_ACT),
        (k0, 0.30, S_SPEAK, K_SOFT),
        (k0 + 0.55, 0.26, S_SPEAK_B, K_SOFT),
        (k0 + 0.90, 0.28, S_SPEAK_C, K_SOFT),
        (k0 + 1.40, 0.50, S_NOTHING, K_SLOW),
        (k1 - 0.45, 0.50, S_SHUT, K_SLOW),
        (wp - 0.36, 0.34, S_WIPE, K_HAND),
        (wp + 0.44, 0.50, S_AFTER, K_SOFT),
        (a0 + 0.30, 0.34, S_SMALL, K_SOFT),
        (a0 + 0.95, 0.55, S_DOWN, K_SLOW),
        (o0, _OFF_DUR, S_STOOD, K_EASE),
    )
    P = chain(t, CURL, keys)
    if s0 < t < s0 + su:                                  # sitting up: the rig's move, slow to start
        u = (t - s0) / su
        P = mixp(L_FALL, _look(_TAB_UP, _sm(u) ** 1.12), _sm(u / 0.2))
    elif o0 < t < o0 + _OFF_DUR:                          # sliding off the seat and standing beside the sofa
        u = (t - o0) / _OFF_DUR
        P = mixp(S_DOWN, _look(_TAB_OFF, _sm(u)), _sm(u / 0.25))
    x, y = _SX, _SY
    # the look up at the scribble on waking; the eyes on the crows, on the balloon
    k = _ramp(t, wk + 0.45, wk + 0.85) * (1.0 - _ramp(t, g0 + 0.05, g0 + 0.5))
    if k > 0.0:
        P = look_at(P, x, y, (x - 70.0, y - 250.0), H0, 1, 0.5 * k, 0.0)
    if s1 < t < k0:
        k = _ramp(t, T["crows"] + 0.3, T["crows"] + 1.1) * (1.0 - _ramp(t, k0 - 0.5, k0 - 0.15))
        if k > 0.0:                                   # a small move of the eyes at each landing (a crow a beat)
            b = (t - beat_after(T["crows"] - 0.01)) / BEAT
            n = math.floor(b)
            e = _sm(_c((b - n) / 0.22))
            px0 = window[0] + (window[2] - window[0]) * (0.30 + 0.5 * ((n * 0.618) % 1.0))
            px1 = window[0] + (window[2] - window[0]) * (0.30 + 0.5 * (((n + 1) * 0.618) % 1.0))
            P = look_at(P, x, y, (px0 + (px1 - px0) * e if n >= 0 else px1, window[1] + 100.0), H0, 1, 0.5 * k, 0.0)
    # the three crossings-out: a flinch each, a little stronger each time
    if c0 < t < c2 + 1.0:
        P = react(P, t, (c0, c1, c2), flinch, 0.75, 0.08, 0.06, 0.34, 0.2)
    return P, x, y, 1


def s01(t: float, tip=None, hero=HERO, balloon=None, window=ST.WINDOW, h: float = H0, **times) -> Act:
    """The room, 0 to 36.27: drawn on, curled on the sofa (draw); asleep; waking and clinging under
    the sagging scribble, the far hand sliding off the armrest; that hand lifts beside its chin and
    draws the hero in the air while the face lifts to the wall; a flinch at each crossing-out;
    sitting up; watching the crows; trying to speak; the sleeve going through the balloon's tail;
    trying again; off the sofa, standing beside it (hand-off B1: STOPPED at story.X1, facing right).

    tip: the world point of the hero's chalk tip (things.sketch_tip) or None: the hand then draws a
    little figure of its own. hero: (x, y, h) of the hero on the wall (scales the hand's movement).
    balloon: (x, y, r) of the speech balloon (only the side it hangs on is used: the balloon is out
    of an arm's reach, the sleeve comes down through its tail and the scene wipes the balloon with
    num["wipe"]). window: the room's window (l, t, r, b): where the crows land. times: any key of S01_T.
    Returns pts: tip (the fingertip of the drawing hand, the far one), hand (the same far hand: the
    one that wipes), mouth, crown; num: hero (0..1 the drawing), speak (how far the mouth is open),
    wipe (0..1 the sleeve's stroke), press (the weight on the crown)."""
    T = dict(S01_T, **times) if times else S01_T
    if t >= T["off"][0] + _OFF_DUR + 0.04:
        A = hold_B1(t, ST.X1, h)
        A.pts.update(tip=A.J["ha_b"], hand=A.J["ha_b"])
        A.num.update(hero=1.0, speak=0.0, wipe=1.0, press=0.0)
        return A
    if balloon is None:
        balloon = BALLOON
    raw = lambda tt: _s01_raw(tt, T, tip, hero, balloon, window)
    d0, d1 = T["draw"]
    wk, o0 = T["wake"], T["off"][0]
    quiet = ((wk - 1.0, T["sag"][1] + 1.2), (T["hero"][0] - 0.6, T["cross"][2] + 0.8), (T["speak"][0] - 0.6, T["speak"][1]),
             (T["wipe"] - 0.5, T["again"][0] + 1.6))
    P, x, y, face = _finish(t, raw, h, quiet, shift=0.0 if t < T["situp"][0] else 1.0)
    grab = None
    h0, h1 = T["hero"]
    wp = T["wipe"]
    # the hand that draws in the air
    kd = _ramp(t, h0 - 0.10, h0 + 0.05) * (1.0 - _ramp(t, h1 + 0.25, h1 + 0.9))
    if kd > 0.0:
        hx, hy, hh = hero
        if tip is not None:
            ox, oy = (tip[0] - (hx - 0.16 * hh)) / hh, (tip[1] - (hy - 0.57 * hh)) / hh
        else:
            ox, oy = _air_path(_seg(t, h0, h1))
        e = _sm(_seg(t, h0 - 0.1, h0 + 0.12))
        P = _hands(P, x, y, H0, 1, None, (AIR[0] + 0.16 * hh * ox * e, AIR[1] + 0.30 * hh * oy * e), 0.0, kd, 0.0)
    # the sleeve that wipes the balloon away: up beside it, then across and down through it
    kw_ = _ramp(t, wp - 0.34, wp - 0.06) * (1.0 - _ramp(t, wp + 0.34, wp + 0.72))
    if kw_ > 0.0:
        sg = 1.0 if balloon[0] >= x else -1.0                 # (the balloon itself hangs out of reach: the sleeve goes
        e = _seg(t, wp - 0.02, wp + 0.36)                     #  through its tail, beside the face, and the scene wipes it)
        e = 1.0 - (1.0 - e) ** 2.2
        sx, sy = _SX - 5.0, _SY - 105.0                       # the far shoulder as it sits
        P = _hands(P, x, y, H0, 1, None, (sx + sg * (80.0 + 30.0 * e + 16.0 * math.sin(math.pi * e)), sy - 44.0 + 100.0 * e),
                   0.0, kw_, 0.0)
    if t >= o0:                                           # the same drawing from the floor beside the sofa
        P = rebase(P, -_OFF_DX, -_OFF_DY)
        x, y = ST.X1, FLOOR
    J = pose_joints(P, x, y, h, face)
    pts = dict(tip=_tip(J, "b", 0.036, h), hand=J["ha_b"], mouth=J["mouth"], crown=J["crown"])
    num = dict(hero=_seg(t, T["hero"][0], T["hero"][1]), speak=P["mopen"], wipe=_seg(t, T["wipe"] - 0.02, T["wipe"] + 0.36),
               press=P["press"])
    return Act(P, x, y, face, grab, _seg(t, d0, d1), 1.0, 1.0, J, pts, num, h)


# ==========================================================================
# s02: school and the home table (36.27 to 58.60)
# ==========================================================================
S02_T = dict(go=36.27, speak=(40.3, 42.6), shoves=(42.7, 44.12, 44.86), drop=46.2, on=46.765, tear=(53.14, 53.51),
             hold=(54.64, 55.01), loose=55.27, tuck=(55.62, 55.95), hush=(56.0, 58.6))
DESK_TOP = FLOOR - 128.25                        # the classroom's lone desk (scale 1.35): world y of its top
TABLE_TOP = FLOOR - 162.0                        # the home table's top
SHOVE = (58.0, 76.0, 96.0)                       # how far each shove moves the desk (world units) before it slides back

_TIRED = dict(eye=0.55, lid=1.0, brow=0.55, mouth=-0.35, hair=0.08)
C_LIFT = STOPPED.but(pel=(0.0, 0.405), lean=0.04, bend=0.12, neck=-0.12, look=(0.52, 0.22), eye=0.9, lid=0.55, brow=0.65,
                     lift=0.3, mouth=-0.1, hair=0.28, gaze=(0.4, 0.2))
C_HAND = C_LIFT.but(hf=(0.205, -0.035), ef=-1.0, lean=0.08, mopen=0.15, look=(0.55, 0.25))
C_DROOP = STOPPED.but(look=(0.42, -0.38), eye=0.6, brow=0.9, gaze=(0.3, -0.5), mouth=-0.5, bend=0.4, neck=0.22)
D_STAND = STOPPED
D_READY = Pose(pel=(0.045, 0.398), lean=0.26, bend=0.30, neck=0.18, look=(0.36, -0.55), hf=(0.20, -0.22), hb=(0.23, -0.21),
               ef=-1.0, eb=-1.0, ff=(0.02, 0.0), fb=(-0.035, 0.0), open=0.45, **dict(_TIRED, brow=0.75, eye=0.65))
D_WIND = D_READY.but(pel=(-0.005, 0.372), lean=0.20, bend=0.42, neck=0.26, ff=(0.02, 0.0), fb=(-0.035, 0.0), eye=0.5, brow=0.9,
                     mouth=-0.5)
D_SHOVE1 = Pose(pel=(0.135, 0.372), lean=0.58, bend=0.16, neck=0.34, look=(0.34, -0.72), hf=(0.27, -0.16), hb=(0.30, -0.15),
                ef=-1.0, eb=-1.0, ff=(0.165, 0.0), fb=(-0.035, 0.012), ab=-0.5, open=0.4,
                **dict(_TIRED, eye=0.32, brow=1.0, mouth=-0.65, hair=0.2))
D_SHOVE2 = D_SHOVE1.but(pel=(0.165, 0.360), lean=0.68, ff=(0.205, 0.0), fb=(-0.05, 0.016), ab=-0.62, eye=0.22, mopen=0.2)
D_SHOVE3 = D_SHOVE1.but(pel=(0.195, 0.345), lean=0.80, bend=0.10, neck=0.42, ff=(0.245, 0.0), fb=(-0.105, 0.020), ab=-0.75,
                        eye=0.12, mopen=0.35, mouth=-0.75, hair=0.3)
D_BACK = D_READY.but(pel=(0.02, 0.402), lean=0.10, bend=0.36, neck=0.20, look=(0.38, -0.4), eye=0.7, brow=0.9, lift=0.2)
D_GIVEUP = STOPPED.but(bend=0.56, neck=0.40, look=(0.30, -0.85), eye=0.35, brow=0.9, mouth=-0.55, hair=0.0, pel=(0.0, 0.388))
T_STAND = Pose(turn=0.80, pel=(0.0, 0.404), lean=0.05, bend=0.30, neck=0.22, look=(0.12, -0.55), hf=(0.0, -0.318), hb=(0.0, -0.318),
               hfz=0.03, hbz=0.03, ef=1.0, eb=-1.0, ff=(0.0, 0.0), fb=(0.0, 0.0), ffz=0.012, fbz=0.012, open=0.5, **_TIRED)
T_WATCH_L = T_STAND.but(hturn=0.42, look=(0.55, -0.02), neck=0.02, bend=0.2, eye=0.85, lid=0.6, brow=0.85, lift=0.2,
                        gaze=(-0.7, 0.05), mouth=-0.3, mopen=0.12)
T_WATCH_R = T_STAND.but(hturn=-0.42, look=(0.55, -0.02), neck=0.02, bend=0.2, eye=0.85, lid=0.6, brow=0.9, lift=0.2,
                        gaze=(0.7, 0.05), mouth=-0.4)
T_TEAR1 = T_STAND.but(lean=0.14, bend=0.40, neck=0.30, look=(0.10, -0.72), eye=1.15, lid=0.3, brow=0.9, lift=0.5, mouth=-0.3,
                      mopen=0.3, gaze=(0.0, -0.6), hair=0.3)
T_TEAR2 = T_TEAR1.but(lean=0.20, bend=0.46, eye=0.95, lid=0.5, brow=1.0, lift=0.2, mopen=0.15, mouth=-0.5, hair=0.15)
T_HOLD = T_STAND.but(lean=0.08, bend=0.40, neck=0.34, look=(0.08, -0.80), eye=0.6, lid=0.9, brow=1.0, mouth=-0.55,
                     gaze=(0.0, -0.7), hair=0.02)
T_LOOSE = T_HOLD.but(bend=0.46, neck=0.38, eye=0.45, look=(0.08, -0.85))
HUSH = _seen(T_STAND.but(lean=0.07, bend=0.50, neck=0.42, look=(0.08, -0.88), eye=0.3, lid=1.0, brow=0.9, mouth=-0.5,
                         gaze=(0.0, -0.8), hair=0.0, over=0.0),
             hf=(-0.040, 0.520), hb=(0.044, 0.516))          # hand-off B2: both hands at the chest, on what it tucked away


def _tired(P, k=1.0):
    """A walk pose with the child's tired upper body and face put back (k = 0..1): where the way is long for the
    beats it has, the walk needs a longer stride than the trudge's; this keeps it a trudge (hanging head, heavy
    arms, the weight forward) all the same."""
    if k <= 0.0:
        return P
    lx, ly = P["look"]
    hf, hb = P["hf"], P["hb"]
    return P.but(bend=P["bend"] + (max(P["bend"], 0.42) - P["bend"]) * k, neck=P["neck"] + (max(P["neck"], 0.32) - P["neck"]) * k,
                 lean=P["lean"] + (max(P["lean"], 0.18) - P["lean"]) * k,
                 look=(lx, ly + (-0.68 - ly) * k), eye=P["eye"] + (0.55 - P["eye"]) * k, lid=P["lid"] + (1.0 - P["lid"]) * k,
                 brow=P["brow"] + (0.55 - P["brow"]) * k, mouth=P["mouth"] + (-0.35 - P["mouth"]) * k,
                 hf=(hf[0] + (0.035 + 0.5 * (hf[0] - 0.035) - hf[0]) * k, hf[1] + (min(hf[1], -0.315) - hf[1]) * k),
                 hb=(hb[0] + (0.035 + 0.5 * (hb[0] - 0.035) - hb[0]) * k, hb[1] + (min(hb[1], -0.315) - hb[1]) * k),
                 hair=P["hair"] + (0.08 - P["hair"]) * k, blush=P["blush"] * (1.0 - k), sway=P["sway"] * (1.0 - k))


def _walk_mood(dist, steps, m0=0.0, fb0=0.015, ff1=-0.02):
    """The lowest mood (from m0) at which the rig's walk_to covers dist (body units) in `steps` steps or fewer
    (fb0, ff1: the far foot of the pose it starts from, the near foot of the pose it ends in: walk_to's own count)."""
    m = m0
    while m < 0.9:
        S, D = 0.31 + 0.11 * m, 0.64 - 0.06 * m
        v = S / D                                             # the stride of a cycle; a step is half of it
        if max(1, round((dist - fb0 + ff1 - S + 0.5 * v) / (0.5 * v))) + 2 <= steps:
            break
        m += 0.01
    return m


def _walk(t, xa, xb, h, start, steps, m0=0.0, rest=None, rest0=None):
    """walk_to on the beat: from xa to xb in at most `steps` steps of one beat from the beat at or after `start`."""
    rest = STOPPED if rest is None else rest
    m = _walk_mood(abs(xb - xa) / h, steps, m0, (rest if rest0 is None else rest0)["fb"][0], rest["ff"][0])
    return walk_to(t, xa, xb, h, start=beat_after(start - 0.02), m=m, rate=WALK_BEAT, rest=rest, rest0=rest0), m


def _out(u, p=2.2):
    u = _c(u)
    return 1.0 - (1.0 - u) ** p


def _desk_dx(t, T):
    """How far the desk has been pushed (world units, along the push), and the count of shoves so far."""
    s1, s2, s3 = T["shoves"]
    d = SHOVE[0] * (_out((t - s1) / 0.42) - _sm((t - s1 - 0.80) / 0.50)) \
        + SHOVE[1] * (_out((t - s2) / 0.36) - _sm((t - s2 - 0.40) / 0.26)) \
        + SHOVE[2] * (_out((t - s3) / 0.42) - _sm((t - s3 - 0.74) / 0.50))
    return d, _out((t - s1) / 0.42) + _out((t - s2) / 0.36) + _out((t - s3) / 0.42)


def _s02_raw(t, T, x0, xs, x1, push, h):
    k0, k1 = T["speak"]
    s1, s2, s3 = T["shoves"]
    dr = T["drop"]
    go2 = T["on"]
    t_turn = s1 - 0.75                                        # the turn toward the desk
    W, m1 = _walk(t, x0, xs, h, T["go"], 5)
    if t < W.t1:
        return _tired(W.pose, _ramp(t, W.t0, W.t0 + 0.5) * (1.0 - _ramp(t, W.t1 - 0.5, W.t1))), W.x, FLOOR, 1
    if t < t_turn or (push > 0 and t < s1 - 0.34):
        keys = ((k0 - 0.28, 0.55, C_LIFT, K_ACT), (k0 + 0.05, 0.45, C_HAND, K_HAND),
                (k0 + (1.05 if push < 0 else 1.22), 0.52 if push < 0 else 0.60, C_DROOP, K_SLOW))
        P = chain(t, STOPPED, keys)
        m = 0.0                                               # three small tries at a word
        for a_, b_, k_ in ((k0 + 0.10, 0.34, 0.65), (k0 + 0.50, 0.30, 0.5), (k0 + 0.86, 0.36, 0.7)):
            m = max(m, k_ * _bell(t, a_, b_))
        if m > 0.0:
            P = P.but(mopen=max(P["mopen"], m), chest=P["chest"] + 0.4 * m)
        return P, xs, FLOOR, 1
    if push < 0 and t < t_turn + 0.42:
        return turn_round(C_DROOP, swap_sides(D_STAND), (t - t_turn) / 0.42), xs, FLOOR, 1
    t_back = dr + 0.19                                        # the turn back to the way it was going
    if t < t_back or (push > 0 and t < go2 - 0.02):
        K1 = (W_BODY, 0.0, 0.09, 0.0, 0.7)
        keys = (
            (s1 - 0.33, 0.20, D_READY, K_HAND),
            (s1 - 0.15, 0.15, D_WIND, K_EASE),
            (s1, 0.42, D_SHOVE1, K1),
            (s1 + 0.80, 0.50, D_BACK, K_EASE),
            (s2 - 0.15, 0.15, D_WIND, K_EASE),
            (s2, 0.36, D_SHOVE2, K1),
            (s2 + 0.40, 0.26, D_BACK, K_EASE),
            (s3 - 0.10, 0.10, D_WIND, K_EASE),
            (s3, 0.42, D_SHOVE3, K1),
            (s3 + 0.74, 0.42, D_BACK, K_EASE),
            (dr - 0.16, 0.34, D_GIVEUP, K_SLOW),
        )
        P = chain(t, D_STAND, keys)
        lf = 0.0                                              # the front foot is lifted as it steps in and steps back
        for s_, d_ in ((s1, 0.80), (s2, 0.40), (s3, 0.74)):
            lf += _bell(t, s_, 0.26) + 0.8 * _bell(t, s_ + d_ + 0.04, 0.36)
        if lf > 0.0:
            P = P.but(ff=(P["ff"][0], P["ff"][1] + 0.026 * lf), af=P["af"] - 0.25 * lf)
        e = _env(t, s3 + 0.36, 0.08, 0.26, 0.1)               # straining: a tremble while the last shove is held
        if e > 0.0:
            q = 0.5 * math.sin((t - s3) * 2.0 * math.pi * 7.5) * e
            P = P.but(lean=P["lean"] + 0.012 * q, pel=(P["pel"][0], P["pel"][1] + 0.003 * q))
        return P, xs, FLOOR, push
    if push < 0 and t < t_back + 0.36:
        return turn_round(D_GIVEUP, swap_sides(STOPPED), (t - t_back) / 0.36), xs, FLOOR, -1
    W2, m2 = _walk(t, xs, x1, h, max(go2, t_back + 0.36 if push < 0 else go2), 7)
    if t < W2.t1:
        return _tired(W2.pose, _ramp(t, W2.t0, W2.t0 + 0.5) * (1.0 - _ramp(t, W2.t1 - 0.5, W2.t1))), W2.x, FLOOR, 1
    e0, e1 = T["tear"]
    h0, h1 = T["hold"]
    u0, u1 = T["tuck"]
    ta = W2.t1 + 0.04
    keys = (
        (ta, 0.44, T_STAND, K_BODY),
        (ta + 0.50, 0.40, T_WATCH_L, K_ACT),
        (e0 + 0.02, 0.16, T_TEAR1, K_HIT),
        (e1 + 0.02, 0.26, T_TEAR2, K_HAND),
        (e1 + 0.45, 0.36, T_WATCH_R, K_ACT),
        (h0 - 0.22, 0.30, T_TEAR2, K_SOFT),
        (h0 + 0.02, h1 - h0, T_HOLD, K_BODY),
        (T["loose"], 0.22, T_LOOSE, K_SLOW),
        (u0, u1 - u0, HUSH, K_SLOW),
    )
    return chain(t, STOPPED, keys), x1, FLOOR, 1


def s02(t: float, x0: float = ST.X1, x_stop: float | None = None, x1: float = ST.X2, push: int = -1, desk: float | None = None,
        desk_top: float = DESK_TOP, table_top: float = TABLE_TOP, drawing_x: float | None = None, sheet: float = 0.62,
        h: float = H0, **times) -> Act:
    """School and the home table, 36.27 to 58.60: the trudge past the rows (a step a beat from x0 to
    x_stop, five steps); the face lifts, a hand half raised, it speaks (three small tries), the hand
    sinks; it turns to its desk and shoves it three times, the whole body leaning (the desk slides
    back each time and pushes the child upright); the arms drop; it walks on to x1 (seven steps);
    at the home table (it stands BEHIND it, turned three-quarter to us) its eyes follow the one who
    leaves, drop to the drawing as it tears, a hand goes to each half; it lifts them and holds them
    together, its grip loosens, it takes them to its chest; the silence: still but for the breath
    and one slow blink (hand-off B2: the pose HUSH at story.X2).

    push: -1 the desk stands behind the child, which turns round (toward us) to push it to the left;
    +1 it stands ahead. desk: world x of the desk's end the hands go on (default 112 units from the
    child); desk_top / table_top: world y. drawing_x: world x of the tear (default x1). sheet: the scale s
    the scene gives things.family_held (the hands hold the halves 124 s apart when they are together).
    Returns pts: hand_l, hand_r (as seen: on the desk while num["on_desk"] is 1; from the first tear
    on the two points things.family_held takes: where the halves are gripped; the mitts are put
    beside the paper's outer edges), sheet (the middle of the whole sheet standing on the table:
    things.family(*sheet, num["sheet"], tear=num["tear"]) until num["in_hands"]), mouth, crown;
    num: desk_dx (signed world units the desk has moved), shove (0..3, the shoves so far, for
    moving the rows away instead), on_desk, speak, tear (0..1: how far the rip has run), in_hands
    (0 / 1: torn through, the halves are in its hands), halves (0 on the table, 1 held up), tuck
    (0..1: the halves go into the jumper), sheet (the scale to draw the paper with: it shrinks as
    it is tucked away)."""
    T = dict(S02_T, **times) if times else S02_T
    xs = x0 + 440.0 if x_stop is None else x_stop
    push = 1 if push > 0 else -1
    hu0, hu1 = T["hush"]
    if t <= T["go"] or t >= hu0:
        A = hold_B1(t, x0, h) if t <= T["go"] else hold_B2(t, x1, h)
        a_, b_ = A.J["ha_f"], A.J["ha_b"]
        A.pts["hand_l"], A.pts["hand_r"] = (a_, b_) if a_[0] < b_[0] else (b_, a_)
        z = 0.0 if t <= T["go"] else 1.0
        A.pts["sheet"] = ((x1 if drawing_x is None else drawing_x), table_top - 3.0 - 30.0 * sheet)
        A.num.update(desk_dx=0.0, shove=3.0 * z, on_desk=0.0, speak=0.0, halves=z, tuck=z, sheet=sheet * (1.0 - 0.6 * z), tear=z,
                     in_hands=z)
        return A
    raw = lambda tt: _s02_raw(tt, T, x0, xs, x1, push, h)
    quiet = ((T["speak"][0] - 0.5, T["drop"] + 0.6), (T["tear"][0] - 0.8, hu1 + 0.1))
    P, x, y, face = _finish(t, raw, h, quiet, shift=1.0 - _ramp(t, T["tear"][0] - 1.4, T["tear"][0] - 0.6))
    grab, pts, num = None, {}, {}
    s1, s2, s3 = T["shoves"]
    dx, n = _desk_dx(t, T)
    num["desk_dx"], num["shove"] = push * dx, n
    kd = _ramp(t, s1 - 0.33, s1 - 0.14) * (1.0 - _ramp(t, T["drop"] - 0.04, T["drop"] + 0.22))
    num["on_desk"] = 1.0 if kd >= 1.0 else 0.0
    if kd > 0.0:
        dk = (xs + push * 112.0 if desk is None else desk) + push * dx
        pa, pb = (dk + push * 6.0, desk_top - 4.0), (dk + push * 26.0, desk_top - 5.0)
        P = _hands(P, x, y, h, face, pa, pb, kd, kd, 0.02)
        if kd >= 1.0:
            grab = {"f": pa, "b": pb}
        pts["hand_l"], pts["hand_r"] = (pb, pa) if push < 0 else (pa, pb)
    e0, e1 = T["tear"]
    num["halves"] = num["tuck"] = 0.0
    num["sheet"] = sheet
    cx = x1 if drawing_x is None else drawing_x
    pts["sheet"] = (cx, table_top - 3.0 - 30.0 * sheet)       # the whole sheet on the table (things.family: its middle)
    num["tear"] = 0.5 * _ramp(t, e0, e0 + 0.16) + 0.5 * _ramp(t, e1, e1 + 0.16)
    num["in_hands"] = 1.0 if t >= e1 + 0.16 else 0.0          # torn through: from here on the two halves are in its hands
    if t > e0:
        h0, h1 = T["hold"]
        u0, u1 = T["tuck"]
        lift, loose, tuck = _ramp(t, h0, h1), _ramp(t, T["loose"], T["loose"] + 0.22), _ramp(t, u0, u1)
        num["halves"], num["tuck"], num["sheet"] = lift, tuck, sheet * (1.0 - 0.6 * tuck)
        yt, yh, yc = table_top - 3.0, table_top - 14.0, y - 0.518 * h
        half = 62.0 * sheet                                   # things.family_held: the halves meet when the hands are 124 s apart
        sep = 6.5 * _ramp(t, e1 + 0.16, e1 + 0.46) * (1.0 - lift)     # torn through, the halves come a little apart
        lx = cx - half - sep - 15.0 * loose
        rx = cx + half + sep + 9.0 * loose
        ly = yt + (yh - yt) * lift + 11.0 * loose
        ry = yt + (yh - yt) * lift + 5.0 * loose
        L = (lx + (cx - 0.040 * h - lx) * tuck, ly + (yc - ly) * tuck)
        R = (rx + (cx + 0.044 * h - rx) * tuck, ry + (yc + 1.5 - ry) * tuck)
        kl = _ramp(t, e0 + 0.06, e0 + 0.34)
        kr = _ramp(t, e1 + 0.05, e1 + 0.33)
        if tuck < 1.0:
            o = _edge(sheet) * (1.0 - tuck)                   # the mitts show beside the paper's outer edges
            Lm, Rm = (L[0] - o, L[1] + 0.3 * o), (R[0] + o, R[1] + 0.3 * o)
            P = _hands(P, x, y, h, face, Lm, Rm, kl, kr, 0.03)
            if kl >= 1.0 and kr >= 1.0:
                grab = {"f": Lm, "b": Rm}
        pts["hand_l"], pts["hand_r"] = L, R
    J = pose_joints(P, x, y, h, face)
    if "hand_l" not in pts:
        pts["hand_l"], pts["hand_r"] = (J["ha_f"], J["ha_b"]) if J["ha_f"][0] < J["ha_b"][0] else (J["ha_b"], J["ha_f"])
    pts["mouth"], pts["crown"] = J["mouth"], J["crown"]
    num["speak"] = P["mopen"]
    return Act(P, x, y, face, grab, 1.0, 1.0, 1.0, J, pts, num, h)


# ==========================================================================
# small planted steps; sitting down and standing up (general tools)
# ==========================================================================
def small_step(P: Pose, u: float, d: float, lead: str = "f", lift: float = 0.026):
    """One small step on the spot: over u = 0..1 the ground point travels d body units toward `face`
    (d < 0: backward); the foot `lead` ('f' near, 'b' far) is picked up and set down first, the other
    follows, and a foot that is not stepping stays where it stands. Returns (pose, travelled): draw
    the figure at x + face * h * travelled. For poses near a profile (the feet cannot step sideways
    in the picture when the figure faces us). Chain several by adding up what they return."""
    if u <= 0.0:
        return P, 0.0
    if u >= 1.0:
        return P, d
    dx = d * _sm(u)
    v1, v2 = _c(u / 0.56), _c((u - 0.44) / 0.56)
    ct = math.cos(P["turn"] * HALF_PI)
    ct = ct if abs(ct) > 0.4 else (0.4 if ct >= 0.0 else -0.4)
    k1, k2 = ("ff", "fb") if lead == "f" else ("fb", "ff")
    a1, a2 = P[k1], P[k2]
    s1, s2 = math.sin(math.pi * v1), math.sin(math.pi * v2)
    px, py = P["pel"]
    return P.but(**{k1: (a1[0] + (d * _sm(v1) - dx) / ct, a1[1] + lift * s1), k2: (a2[0] + (d * _sm(v2) - dx) / ct, a2[1] + lift * s2),
                    "a" + k1[1]: P["a" + k1[1]] - 0.3 * s1, "a" + k2[1]: P["a" + k2[1]] - 0.3 * s2,
                    "pel": (px, py - 0.006 * math.sin(math.pi * u))}), dx


def _steps(P, t, steps):
    """Several small steps: steps = [(t0, dur, d, lead[, lift]), ...] in order. Returns (pose, travelled)."""
    tot = 0.0
    for s in steps:
        if t <= s[0]:
            break
        P, d = small_step(P, (t - s[0]) / s[1], s[2], s[3], s[4] if len(s) > 4 else 0.026)
        tot += d
    return P, tot


_FT = 0.21                                      # sitting on the floor: the hips are this far behind where the feet stand
FLOOR_SIT = rebase(SIT_FLOOR, _FT, 0.0)         # sitting on the floor, legs folded; ground point under the FEET
FLOOR_HUG = rebase(SIT_HUG, 0.15, 0.0)          # hugging its knees, the same hips, the same feet
_SD1 = Pose(pel=(-0.070, 0.315), lean=0.44, bend=0.42, neck=0.14, look=(0.34, -0.62), hf=(0.13, -0.26), hb=(0.03, -0.30),
            ff=(-0.012, 0.0), fb=(0.030, 0.0), turn=0.10, open=0.5, **dict(_TIRED, brow=0.7))
_SD2 = Pose(pel=(-0.165, 0.150), lean=0.52, bend=0.58, neck=0.22, look=(0.32, -0.62), hf=(0.16, -0.20), hb=(-0.05, -0.27),
            ff=(-0.010, 0.0), fb=(0.030, 0.0), turn=0.20, open=0.5, front=1.0, **dict(_TIRED, brow=0.8, eye=0.4))
_SU1 = FLOOR_HUG.but(pel=(-0.185, 0.085), lean=0.66, bend=0.55, neck=0.34, hf=(0.10, -0.29), hb=(0.02, -0.30), eye=0.4,
                     brow=0.8, look=(0.3, -0.7))
_SU2 = Pose(pel=(-0.050, 0.215), lean=0.66, bend=0.52, neck=0.26, look=(0.30, -0.75), hf=(0.115, -0.185), hb=(0.135, -0.18),
            ff=(0.015, 0.0), fb=(-0.025, 0.0), turn=0.10, open=0.45, front=1.0, **dict(_TIRED, eye=0.35, brow=0.85))
_SU3 = STOPPED.but(pel=(-0.012, 0.335), lean=0.40, bend=0.56, neck=0.20, hf=(0.085, -0.27), hb=(0.075, -0.27), look=(0.3, -0.8),
                   ff=(0.015, 0.0), fb=(-0.025, 0.0), hair=0.0, eye=0.45)
_EDGE_DX = 0.363                                # sofa edge: the child stands this far in front of where its hips sat
EDGE_SIT = rebase(SIT_EDGE.but(hair=0.02, look=(0.3, -0.6), neck=0.3), _EDGE_DX, 0.0)      # ground point: where it will stand
_EDGE_UP = STOPPED.but(pel=(-0.215, 0.335), lean=0.50, bend=0.55, neck=0.10, hf=(0.10, -0.24), hb=(0.12, -0.23),
                       look=(0.3, -0.8), hair=0.0, turn=0.25)


def sit_down(u: float, kind: str = "floor", a: Pose | None = None, b: Pose | None = None) -> Pose:
    """Sitting down as one move, u = 0..1 (about 1.0 s on the floor, 0.9 s on the sofa's edge): the
    pelvis drops back before anything else, a hand goes down to find the floor, the body lands and
    settles (a small give of the spine), the head comes last.
    kind "floor": from standing (a, default STOPPED) to sitting on the floor with the legs folded
    (b, default the rig's SIT_FLOOR); the GROUND POINT STAYS UNDER THE FEET (the hips end 0.21 h
    behind it). kind "edge": onto the front edge of the sofa (b: the rig's SIT_EDGE): the ground point
    is where the child stood, the seat's edge 0.36 h behind it (story.SOFA_SEAT_Y high)."""
    u = _c(u)
    if kind == "edge":
        P = through([STOPPED if a is None else a, _EDGE_UP, EDGE_SIT if b is None else b], [0.0, 0.55, 1.0], u, W_BODY)
    else:
        P = through([STOPPED if a is None else a, _SD1, _SD2, FLOOR_SIT if b is None else b], [0.0, 0.34, 0.70, 1.0], u, W_BODY)
    g = _bell(u, 0.74, 0.26)                                         # the landing: the spine gives, the hair flies up
    return P.but(bend=P["bend"] + 0.10 * g, neck=P["neck"] + 0.08 * g, bob=P["bob"] + 0.5 * g) if g else P


def stand_up(u: float, kind: str = "floor", a: Pose | None = None, b: Pose | None = None) -> Pose:
    """Getting up as one move, u = 0..1 (1.4 s or more: it is heavy): the weight is rocked forward
    over the feet, the hands push off (floor, then knees), the pelvis rises, the back straightens,
    the head comes up last. kind "floor": from sitting on the floor (a, default hugging its knees:
    FLOOR_HUG) to standing (b, default STOPPED), ground point under the feet. kind "edge": sliding
    off the sofa's edge (a: EDGE_SIT) and standing 0.36 h in front of where it sat."""
    u = _c(u)
    if kind == "edge":
        return through([EDGE_SIT if a is None else a, _EDGE_UP, STOPPED if b is None else b], [0.0, 0.46, 1.0], u, W_BODY)
    return through([FLOOR_HUG if a is None else a, _SU1, _SU2, _SU3, STOPPED if b is None else b], [0.0, 0.22, 0.50, 0.76, 1.0], u,
                   W_BODY)


def sit_up(u: float) -> Pose:
    """Sitting up from the curl on the sofa, u = 0..1 (about 2 s): the weight goes onto a hand and a
    forearm, the back comes up while the legs still lie, the feet are gathered in, the knees come up
    and the arms go round them; the head comes up last. From the rig's CURL to SIT_B (its SIT_SOFA
    seen from the curl's ground point): the rig's sit_up_pose with a tired child's timing (slow to
    start). Ground point (story.CURL_X, SOFA_SEAT_Y) all the way. 0.005 ms."""
    return _look(_TAB_UP, _sm(u) ** 1.12)


def curl_up(u: float) -> Pose:
    """Curling up on the sofa (the coda), u = 0..1 (about 2.5 s): from the front edge of the seat (the
    rig's EDGE_CURL) it draws its legs up, lets itself down onto a forearm, the head goes down last:
    the rig's curl_up_pose, eased. Ends in CURL_EASE. Ground point (story.CURL_X, SOFA_SEAT_Y)."""
    return _look(_TAB_CURL, _sm(u))


# ==========================================================================
# s03: the plain (58.60 to 91.77)
# ==========================================================================
S03_T = dict(entry=58.60, turn=58.86, walk=59.515, hits=ST.HITS_1, arrive=74.6, lift=75.49, spark=76.67, go=79.015,
             phone=91.0)

B_BACK = BACK_STAND.but(hair=0.06)
N_FEET = STOPPED.but(turn=0.42, pel=(0.0, 0.394), bend=0.42, neck=0.30, look=(0.34, -0.80), gaze=(0.25, -0.6), eye=0.72,
                     lid=0.85, brow=0.7, hair=0.12, open=0.5)             # the amber line at its feet
N_SEE = Pose(turn=0.20, pel=(0.0, 0.410), lean=0.01, bend=0.02, neck=-0.12, look=(0.50, 0.20), gaze=(0.5, 0.1), eye=0.98,
             lid=0.5, brow=0.35, lift=0.45, mouth=-0.08, mopen=0.2, hf=(0.03, -0.318), hb=(0.05, -0.31), ff=(-0.02, 0.0),
             fb=(0.02, 0.0), hair=0.62, open=0.6)                         # the head lifted: someone is there
N_SPARK = N_SEE.but(spark=1.0, eye=1.1, lid=0.4, lift=0.65, lean=0.05, neck=-0.16, mouth=0.05, mopen=0.3, hair=0.75,
                    pel=(0.008, 0.412))
N_READY = N_SEE.but(turn=0.08, lean=0.05, bend=0.10, neck=-0.02, look=(0.46, 0.06), eye=0.9, lid=0.55, lift=0.25, mopen=0.0,
                    mouth=-0.1, spark=0.5, hair=0.5)                       # it will go
ON_RUG = STOPPED.but(lean=0.09, bend=0.34, neck=0.20, look=(0.35, -0.52), gaze=(0.3, -0.6), eye=0.6, hair=0.12)   # hand-off B3
_N_ARRIVE = ON_RUG.but(neck=0.14, look=(0.36, -0.36), gaze=(0.2, 0.0), eye=0.66)


def _away(ph):
    P, adv = walk_away(ph, 0.0)
    return P.but(hair=0.05), adv


def _low(S, k):
    """A standing back view S pressed down by k (0 .. about 1.2): the knees give, the back rounds,
    the head goes down between the shoulders, the hands come up a little."""
    px, py = S["pel"]
    hf, hb = S["hf"], S["hb"]
    return S.but(pel=(px, py - 0.135 * k), bend=S["bend"] + 0.24 * k, neck=S["neck"] + 0.20 * min(k, 1.1),   # (further, the crown tips over)
                 lean=S["lean"] + 0.03 * k, hf=(hf[0], hf[1] + 0.055 * k), hb=(hb[0], hb[1] + 0.055 * k), hair=0.0,
                 bob=S["bob"])


_LOW = ((0.70, 0.40), (1.00, 0.72), (1.20, 0.94))      # the three hits: how low each presses it at once, and where it stays


@lru_cache(maxsize=8)
def _s03_span(x0, x1, h, go):
    W = _walk(go, x0, x1, h, go, 15, 0.30, rest=_N_ARRIVE, rest0=N_READY)[0]
    return W.t0, W.t1


def _s03_raw(t, T, x0, x1, h):
    en, tu, wk = T["entry"], T["turn"], T["walk"]
    h1, h2, h3 = T["hits"]
    ar, li, sp, go = T["arrive"], T["lift"], T["spark"], T["go"]
    if t < wk:
        P = HUSH if t < tu else turn_round(HUSH, B_BACK, (t - tu) / (wk - tu - 0.06))
        e = _env(t, en + 0.03, 0.09, 0.10, 0.42)                 # the band comes in: a start
        if e > 0.0:
            P = startle(P, 0.85 * e)
            P = P.but(ff=(P["ff"][0], P["ff"][1] + 0.022 * _bell(t, en + 0.04, 0.26)))
        return P, x0, FLOOR, 1
    if t < h1:
        Pw, _ = _away((t - wk) * WALK_BEAT)
        return mixp(B_BACK, Pw, _seg(t, wk, wk + 0.375)), x0, FLOOR, 1
    tt = ar + 0.34                                               # the turn round
    Sp = _away((h1 - wk) * WALK_BEAT)[0]                         # the stride it stopped in
    if t < tt + 0.52:
        notice = _low(Sp, _LOW[2][1] - 0.2).but(hturn=0.62, tilt=0.10, roll=-0.05, hair=0.05)
        if t < tt:
            keys = []
            for th, (pk, st_), d_ in zip((h1, h2, h3), _LOW, (0.80, 0.80, 1.30)):
                keys += [(th, 0.13, _low(Sp, pk), K_HIT), (th + 0.22, d_, _low(Sp, st_), K_EASE)]
            keys.append((ar - 0.06, 0.40, notice, K_SOFT))
            P = chain(t, Sp, keys)
            for i, th in enumerate((h1, h2, h3)):                # the jolt of each hit: the arms jerk out and are pulled in,
                e = _env(t, th + 0.02, 0.07, 0.04, 0.30)         # the body rocks, the hair flies
                if e > 0.0:
                    sg = 1.0 if i % 2 else -1.0
                    P = P.but(hfz=P["hfz"] + 0.055 * e, hbz=P["hbz"] + 0.055 * e, bob=P["bob"] + 0.7 * e,
                              roll=P["roll"] + 0.07 * sg * e, pz=P["pz"] + 0.012 * sg * e)
            return P, x0, FLOOR, 1
        return turn_round(notice, N_FEET, (t - tt) / 0.52), x0, FLOOR, 1
    if t <= go:
        keys = ((li, 1.2, N_SEE, K_BLINK), (sp - 0.10, 0.36, N_SPARK, K_SOFT), (sp + 1.05, 0.80, N_READY, K_SOFT))
        return chain(t, N_FEET, keys), x0, FLOOR, 1
    W, m = _walk(t, x0, x1, h, go, 15, 0.30, rest=_N_ARRIVE, rest0=N_READY)
    if t < W.t1:
        P = W.pose
        k = _ramp(t, W.t0, W.t0 + 0.7) * (1.0 - _ramp(t, W.t0 + 3.5, W.t0 + 7.5))      # its eyes on the far friend at first
        if k > 0.0:
            lx, ly = P["look"]
            P = P.but(look=(lx + 0.06 * k, ly + 0.26 * k), neck=P["neck"] - 0.08 * k, gaze=(0.45 * k, 0.2 * k),
                      eye=P["eye"] + 0.16 * k, lid=P["lid"] - 0.2 * k, spark=0.5 * k, hair=P["hair"] + 0.2 * k)
        k2 = _ramp(t, W.t1 - 3.4, W.t1 - 1.2) * (1.0 - _ramp(t, W.t1 - 0.7, W.t1))    # the room comes back: the head sinks
        if k2 > 0.0:
            lx, ly = P["look"]
            P = P.but(look=(lx, ly - 0.10 * k2), neck=P["neck"] + 0.05 * k2, bend=P["bend"] + 0.05 * k2)
        return P, W.x, FLOOR, 1
    ph = max(T["phone"] + 0.04, W.t1 + 0.05)
    return chain(t, _N_ARRIVE, ((ph, 0.42, ON_RUG, K_SOFT),)), x1, FLOOR, 1


def s03(t: float, x0: float = ST.X2, x1: float = ST.X3, h: float = H0, **times) -> Act:
    """The first chorus and the walk home, 58.60 to 91.77. From hand-off B2: a start as the band comes
    in; it turns its back on us and trudges away IN PLACE, a step a beat (the camera's pull-back and
    the falling pressure make the distance: draw it at x0, FLOOR, full height); it stops on the first
    hit and each of the three hits presses it lower; it stands bowed, nearly rubbed out; the amber
    line arrives at its feet (arrive): the head turns to it, the child turns round (through the
    right-hand profile, opened toward us) and looks down at the line; the head lift (lift: 1.2 s, a
    dip, a slow rise with a small overshoot, a blink on the way, the hair last); a spark of attention
    (spark); it walks right along the line from x0 to x1, a step a beat (15 steps from go, mood about
    0.3, its eyes on the far friend at first), stops on the rug and looks down at the phone as its
    screen shows (phone). Ends in hand-off B3 (ON_RUG at x1).
    times: any key of S03_T.
    Act.a is the line's pressure: it falls with every step away and under the hits (to about 0.3),
    stays, and comes back with the head lift. pts: crown, mouth, feet (x, FLOOR: where the amber line
    arrives), eye (where it looks along the line: a point 600 units to the right at head height).
    num: away (body units walked into the depth: 0 .. about 1.7), low (0..1.2: how far the hits have
    pressed it down), rim (0..1: the amber rim on its right side, from arrive), lift (0..1 through
    the head lift), spark, walk (0 before go, 0..1 along the walk home, 1 after)."""
    T = dict(S03_T, **times) if times else S03_T
    if t <= T["entry"]:
        A = hold_B2(t, x0, h)
        A.pts.update(feet=(x0, FLOOR), eye=(x0 + 600.0, float(A.J["head"][1])))
        A.num.update(away=0.0, low=0.0, rim=0.0, lift=0.0, spark=0.0, walk=0.0)
        return A
    wk, (h1, h2, h3), ar, li, sp, go = T["walk"], T["hits"], T["arrive"], T["lift"], T["spark"], T["go"]
    wt0, wt1 = _s03_span(x0, x1, h, go)
    ph = max(T["phone"] + 0.04, wt1 + 0.05)
    if t >= ph + 0.44:
        A = hold_B3(t, x1, h)
        A.pts.update(feet=(x1, FLOOR), eye=(x1 + 600.0, float(A.J["head"][1])))
        A.num.update(away=0.0, low=0.0, rim=1.0, lift=1.0, spark=0.0, walk=1.0)
        return A
    raw = lambda tt: _s03_raw(tt, T, x0, x1, h)
    quiet = ((T["entry"] - 0.3, wk), (ar - 0.3, sp + 1.2), (ph - 0.2, ph + 0.6))
    back = _ramp(t, T["turn"], wk) * (1.0 - _ramp(t, ar + 0.3, ar + 0.9))
    P, x, y, face = _finish(t, raw, h, quiet, shift=(1.0 - back) * _ramp(t, li, li + 1.5))
    # the line's pressure
    a = 1.0
    n = int((h1 - wk) / BEAT + 0.5)
    for k in range(n):
        a -= 0.082 * _ramp(t, wk + k * BEAT + 0.1, wk + k * BEAT + 0.5)
    for th in (h1, h2, h3):
        a -= 0.035 * _ramp(t, th, th + 0.3)
    a += (1.0 - a) * _ramp(t, li - 0.1, li + 1.7)
    away = _away((min(t, h1) - wk) * WALK_BEAT)[1] * _seg(t, wk, wk + 0.375) if t > wk else 0.0
    low = 0.0
    for th, (pk, st) in zip((h1, h2, h3), _LOW):
        if t >= th:
            low = st + (pk - st) * (1.0 - _ramp(t, th + 0.2, th + 1.0))
    low *= 1.0 - _ramp(t, ar + 0.3, ar + 0.9)
    J = pose_joints(P, x, y, h, face)
    pts = dict(crown=J["crown"], mouth=J["mouth"], feet=(x, FLOOR), eye=(x + 600.0, float(J["head"][1])))
    num = dict(away=away, low=low, rim=_ramp(t, ar - 0.2, ar + 0.3), lift=_seg(t, li, li + 1.2), spark=P["spark"],
               walk=_seg(t, wt0, wt1))
    return Act(P, x, y, face, None, 1.0, a, 1.0, J, pts, num, h)


# ==========================================================================
# s04: the evening room and the corridor line (91.77 to 115.77)
# ==========================================================================
S04_T = dict(sit=91.80, pick=92.72, thumb=(93.05, 93.26, 94.75, 95.98), down=96.02, shawl=(96.18, 98.8), rise=(101.9, 103.4),
             bumps=(104.07, 105.23, 106.57), plant=108.25, cross=(109.6, 113.5), redraw=((111.0, 112.0), (114.3, 115.0)))
STUB_ANG = -0.75                                 # the angle of the chalk stub's body (things.chalk_stub(F, tip, ang))
_STUB_GRIP = 15.6                                # the hand holds it this far up from its tip (things.stub_grip)

E_REACH = FLOOR_SIT.but(lean=0.98, bend=0.62, neck=0.02, look=(0.42, -0.72), gaze=(0.2, -0.6), eye=0.6, brow=0.6,
                        hb=(0.10, -0.28), over=1.0)
E_PHONE = FLOOR_SIT.but(lean=-0.06, bend=0.40, neck=0.34, look=(0.40, -0.58), gaze=(0.25, -0.5), eye=0.66, lid=0.9,
                        brow=0.6, mouth=-0.3, hf=(0.215, -0.050), hb=(0.185, -0.060), ff=(0.12, 0.0), fb=(0.16, 0.0),
                        hair=0.12, over=1.0)
E_EMPTY = E_PHONE.but(bend=0.52, neck=0.44, look=(0.39, -0.68), eye=0.42, lid=1.0, brow=0.3, mouth=-0.45, hair=0.02,
                      lean=-0.02, hf=(0.205, -0.085), hb=(0.175, -0.095))
E_DOWN = E_EMPTY.but(hf=(0.225, -0.275), hb=(0.215, -0.175), look=(0.34, -0.80), gaze=(0.0, -0.6), eye=0.36, neck=0.48)
E_WEIGHT = E_DOWN.but(bend=0.76, neck=0.56, lean=0.20, press=0.9, look=(0.30, -0.88), eye=0.2, brow=0.9, mouth=-0.55,
                      hair=0.0, pel=(-_FT, 0.052))
E_HUG = FLOOR_HUG.but(bend=0.80, neck=0.62, look=(0.25, -0.92), eye=0.1, brow=0.85, mouth=-0.5, hair=0.0, press=0.2,
                      over=1.0)
_E_UP1 = _SU1.but(over=1.0)
_E_UP2 = _SU2.but(over=1.0)
C_STAND = STOPPED.but(bend=0.52, neck=0.36, look=(0.30, -0.78), hair=0.03, pel=(0.0, 0.388), ff=(0.015, 0.0),
                      fb=(-0.025, 0.0))                                   # up, under the weight
C_TRY = C_STAND.but(bend=0.38, neck=0.18, lean=0.16, look=(0.40, -0.34), gaze=(0.5, 0.3), eye=0.7, brow=0.7)   # it tries a step
C_SHRUNK = C_STAND.but(bend=0.58, neck=0.42, pel=(-0.006, 0.380), eye=0.4, brow=0.85, hf=(0.05, -0.31), hb=(0.04, -0.31))
C_SET = C_STAND.but(pel=(0.0, 0.372), bend=0.44, neck=0.16, lean=0.14, look=(0.40, -0.30), gaze=(0.5, 0.2), eye=0.75,
                    brow=0.5, mouth=-0.45)                                # it gathers itself
PLANTED = Pose(pel=(0.0, 0.374), lean=0.07, bend=0.12, neck=0.0, turn=0.22, look=(0.42, -0.04), gaze=(0.4, 0.0), eye=0.85,
               lid=0.8, brow=0.38, mouth=-0.32, hf=(0.035, -0.305), hb=(0.0, -0.305), hfz=0.025, hbz=0.025, ff=(-0.135, 0.0),
               fb=(0.135, 0.0), open=0.6, hair=0.32)                     # hand-off B4: feet apart, braced, head level
_PJ = solve(PLANTED)                              # its feet stay where they stand when the body turns to us
P_ARM = _seen(PLANTED.but(turn=0.56, hturn=0.10, neck=0.26, tilt=-0.08, look=(0.10, -0.66), gaze=(-0.2, -0.6), eye=0.7,
                          brow=0.7, hf=(0.150, -0.215), hfz=0.03, mouth=-0.4, hair=0.2, bend=0.2),
              ff=tuple(_PJ["an_f"]), fb=tuple(_PJ["an_b"]))              # it looks at its arm
P_DRAW = P_ARM.but(over=1.0, eye=0.62, brow=0.55, mouth=-0.15, neck=0.30, bend=0.24, eb=1.0)
P_SIDE = P_DRAW.but(hf=(0.0, -0.20), hfz=0.20, look=(0.04, -0.70), tilt=-0.12)        # the arm held away from its side


def _along(Q, d):
    """The point at the share d of the length of a polyline Q (n, 2), and the direction there."""
    seg_ = np.hypot(*(Q[1:] - Q[:-1]).T)
    L = float(seg_.sum())
    s = _c(d) * L
    for i, l in enumerate(seg_):
        if s <= l or i == len(seg_) - 1:
            u = s / max(l, 1e-9)
            p = Q[i] + (Q[i + 1] - Q[i]) * min(1.0, u)
            v = Q[i + 1] - Q[i]
            return p, math.atan2(v[1], v[0])
        s -= l
    return Q[-1], 0.0


def _own_lines(P, x, y, h, face):
    """Two stretches of the child's own outline in the world: its near arm (shoulder, elbow, wrist,
    the corner rounded) and its near side (from under the arm down the garment to its hem)."""
    Jb = solve(P)
    fh = face * h
    W_ = lambda p: np.array([x + fh * p[0], y - h * p[1]])
    sh, el, ha = Jb["sh_f"], Jb["el_f"], Jb["ha_f"]
    arm = np.array([W_(sh + (el - sh) * 0.22), W_(sh + (el - sh) * 0.66), W_(el * 0.5 + (sh + ha) * 0.25), W_(el + (ha - el) * 0.38),
                    W_(el + (ha - el) * 0.96)])
    sp = Jb["spine"]
    sg = -1.0 if Jb["sh_f"][0] <= Jb["sh_b"][0] else 1.0             # the near side of the garment in the picture
    wide = 0.086 + 0.02 * min(1.0, abs(Jb["se"]))
    side = np.array([W_(sp[i] + np.array([sg * wide * (1.06 - 0.10 * i / 5.0), 0.0])) for i in (5, 4, 3, 2, 1, 0)])
    side = np.vstack([side, W_(sp[0] + np.array([sg * wide * 1.06, -0.035]))])
    return arm, side


@lru_cache(maxsize=8)
def _laid_phone(x0, h):
    """Where the hand lays the phone face down (world)."""
    q = pose_joints(E_DOWN, x0, FLOOR, h, 1)["ha_f"]
    return (float(q[0]), float(q[1]))


def _s04_raw(t, T, x0, x1, h, sides, phone):
    si, pk = T["sit"], T["pick"]
    th_ = T["thumb"]
    dn = T["down"]
    s0, s1 = T["shawl"]
    r0, r1 = T["rise"]
    if t < r0:                                                    # on the rug
        keys = ((si, 0.72, FLOOR_SIT, K_BODY, ((0.36, _SD1), (0.72, _SD2))),
                (pk - 0.30, 0.30, E_REACH, K_HAND),
                (pk + 0.04, 0.40, E_PHONE, K_BODY),
                (th_[1] + 0.5, th_[-1] - th_[1] - 0.6, E_EMPTY, K_EASE),
                (dn, 0.40, E_DOWN, K_SLOW),
                (s0 + 0.55, 0.85, E_WEIGHT, K_SLOW),
                (s0 + 1.30, 1.50, E_HUG, K_BODY))
        P = chain(t, ON_RUG, keys)
        g = _bell(t, si + 0.52, 0.30)                             # the landing
        if g > 0.0:
            P = P.but(bend=P["bend"] + 0.08 * g, bob=P["bob"] + 0.5 * g)
        kr = _ramp(t, pk - 0.26, pk - 0.02) * (1.0 - _ramp(t, pk + 0.04, pk + 0.30))
        if kr > 0.0:                                              # the hand goes down to the phone
            P = _hands(P, x0, FLOOR, h, 1, phone, None, kr, 0.0, 0.0)
        for a_ in th_:                                            # the thumb: a quick stroke, a slow return; the eyes go with the rows
            e = _env(t, a_ - 0.03, 0.07, 0.03, 0.30)
            if e > 0.0:
                hb, g_ = P["hb"], P["gaze"]
                P = P.but(hb=(hb[0] - 0.006 * e, hb[1] - 0.030 * e), gaze=(g_[0], g_[1] - 0.25 * e))
        e = _bell(t, th_[-1] + 0.25, 0.9)                         # nothing comes: it looks a moment longer
        if e > 0.0:
            P = P.but(gaze=(P["gaze"][0], P["gaze"][1] + 0.2 * e), brow=P["brow"] + 0.3 * e)
        return P, x0, FLOOR, 1
    if t < r1:
        u = (t - r0) / (r1 - r0)
        return through([E_HUG, _E_UP1, _E_UP2, _SU3, C_STAND], [0.0, 0.22, 0.50, 0.76, 1.0], u, W_BODY), x0, FLOOR, 1
    b1, b2, b3 = T["bumps"]
    pl = T["plant"]
    c0, c1 = T["cross"]
    (d0, d1), (e0, e1) = T["redraw"]
    back = 0.105
    fwd = (x1 - x0) / h / 3.0 + back
    if t < pl + 0.1:
        keys, steps = [], []
        for th in (b1, b2, b3):
            keys += [(th - 0.72, 0.50, C_TRY, K_SOFT), (th + 0.16, 0.55, C_SHRUNK, K_SLOW)]
            steps += [(th - 0.66, 0.52, fwd, "f", 0.03), (th + 0.03, 0.36, -back, "b", 0.02)]
        keys += [(pl - 0.92, 0.40, C_SET, K_BODY), (pl - 0.40, 0.44, PLANTED, K_LAND)]
        P = chain(t, C_STAND, keys)
        P, dxb = _steps(P, t, steps)
        for i, th in enumerate((b1, b2, b3)):
            e = _env(t, th, 0.08, 0.12, 0.50)
            if e > 0.0:
                P = stagger(P, 1.1 * e, sides[i % len(sides)])
        if t > pl - 0.92:                                         # the stance: the near foot goes back, then the far foot
            v1, v2 = _c((t - (pl - 0.64)) / 0.28), _c((t - (pl - 0.30)) / 0.30)       # is set down hard on the beat
            P = P.but(ff=(C_STAND["ff"][0] + (PLANTED["ff"][0] - C_STAND["ff"][0]) * _sm(v1), 0.030 * math.sin(math.pi * v1)),
                      fb=(C_STAND["fb"][0] + (PLANTED["fb"][0] - C_STAND["fb"][0]) * _sm(v2),
                          0.045 * math.sin(math.pi * v2) ** 0.8))
        off = 0.0
        for th in (b1, b2, b3):
            off = max(off, _env(t, th + 0.02, 0.18, 0.28, 0.42))
        return P, x0 + h * dxb, FLOOR + 15.0 * off, 1
    keys = ((c0 + 0.50, 0.55, P_ARM, K_ACT), (d0 - 0.36, 0.34, P_DRAW, K_HAND), (d1 + 0.30, 0.45, P_ARM, K_SOFT),
            (d1 + 0.85, 0.50, PLANTED, K_BODY), (c1 + 0.42, 0.34, P_SIDE, K_HAND), (e1 + 0.04, 0.44, PLANTED, K_BODY))
    P = chain(t, PLANTED, keys)
    for th, k in ((c0, 0.55), (c1, 0.75)):                        # crossed out: a wince, the feet stay
        e = _env(t, th + 0.04, 0.08, 0.10, 0.45)
        if e > 0.0:
            P = flinch(P, k * e).but(roll=P["roll"] + 0.06 * e, tilt=P["tilt"] - 0.08 * e)
    return P, x1, FLOOR, 1


def s04(t: float, x0: float = ST.X3, x1: float = ST.X4, phone=None, sides=(-1, 1, -1), h: float = H0, **times) -> Act:
    """The evening room and the corridor line, 91.77 to 115.77. From hand-off B3 (standing on the rug
    at x0): it sits down on the floor where it stands (the feet stay: its hips end 80 units to the
    left, against the sofa), bends right over to the phone and picks it up (pick), sits with it
    before its knees; the other hand strokes the screen on each of `thumb` (a quick stroke, a slow
    return, the eyes going with the rows) while the face empties and the head sinks; nothing comes:
    it lays the phone face down (down). The scribble comes down on it (shawl = (start, settled)):
    the crown gives, the spine curls, it draws up its knees and puts its forehead on them. It gets
    up (rise), heavy, the head last. On the corridor line: three times it tries a step forward, is
    shouldered (bumps) and it is the child that gives way: thrown back, a stagger to alternating
    sides (sides: -1 the far shoulder is hit, +1 the near one), a step back (40 units) and off the
    line toward us (y + 15), and back on; it gathers itself and plants its feet apart on the beat (plant) at x1. Crossed out
    (cross): a wince each time, the feet stay; it looks at its arm, takes the chalk stub in its far
    hand and goes over its near arm from the shoulder to the wrist (redraw[0]); the second time down
    its near side (redraw[1]). Ends in hand-off B4 (PLANTED at x1).
    phone: the world point where the phone lies (default story.PHONE in the evening room).
    times: any key of S04_T.
    grab pins the far hand to the stub while it draws. pts: phone (where the phone is: on the rug,
    then in the near hand: the point to give things.phone_held), thumb (the stroking hand), crown,
    neck, pel (for the shawl), arm, side (polylines (n, 2) of the two stretches of its outline that
    are crossed out and redrawn: give them to things.restroke), tip (the stub's drawing end while
    num["stub"] > 0). num: held (0 the phone lies, 1 it is in the hand), lit (0..1: how much of the
    screen's light is on the face: 1 while it holds it up), stroke (the count of thumb strokes so
    far, eased: for the scroll), down (0..1: the phone is laid face down), press (the weight on the
    crown), hug (0..1: knees drawn up), off (0..1: off the line), bump (0..1 at each shouldering),
    stub (0..1: the stub is in its hand), redraw1, redraw2 (0..1: how far each stretch is gone over),
    ang (the stub's angle for things.chalk_stub)."""
    T = dict(S04_T, **times) if times else S04_T
    if phone is None:
        phone = (ST.PHONE[0] + ST.ROOM2_DX, ST.PHONE[1])
    (d0, d1), (e0, e1) = T["redraw"]
    if t <= T["sit"] or t >= e1 + 0.5:
        first = t <= T["sit"]
        A = hold_B3(t, x0, h) if first else hold_B4(t, x1, h)
        A.pts.update(thumb=A.J["ha_b"], neck=A.J["neck"], pel=A.J["pel"])
        if first:
            A.pts["phone"] = phone
        else:
            A.pts["phone"] = _laid_phone(x0, h)
            A.pts["arm"], A.pts["side"] = _own_lines(A.pose, x1, FLOOR, h, 1)
        z = 0.0 if first else 1.0
        A.num.update(held=0.0, lit=0.0, stroke=4.0 * z, down=z, press=0.0, hug=0.0, off=0.0, bump=0.0, stub=0.0, redraw1=z,
                     redraw2=z, ang=STUB_ANG)
        return A
    raw = lambda tt: _s04_raw(tt, T, x0, x1, h, sides, phone)
    pk, dn, th_ = T["pick"], T["down"], T["thumb"]
    s0, s1 = T["shawl"]
    r0, r1 = T["rise"]
    pl = T["plant"]
    c0, c1 = T["cross"]
    quiet = ((T["sit"] - 0.2, th_[1] + 0.4), (th_[2] - 0.3, th_[2] + 0.5), (th_[3] - 0.3, r1 + 0.2), (pl - 1.0, pl + 0.4),
             (c0 - 0.2, d1 + 1.4), (c1 - 0.2, e1 + 0.5))
    floor_ = 1.0 - _ramp(t, r0, r1)
    P, x, y, face = _finish(t, raw, h, quiet, breath=1.0 - 0.35 * _ramp(t, s0, s1) * floor_, shift=1.0 - floor_ * _ramp(t, T["sit"], T["sit"] + 0.6))
    grab, pts, num = None, {}, {}
    # the stub: its tip travels along the arm, then down the side; the far hand holds it
    k1 = _ramp(t, d0 - 0.30, d0 - 0.04) * (1.0 - _ramp(t, d1 + 0.06, d1 + 0.40))
    k2 = _ramp(t, e0 - 0.30, e0 - 0.04) * (1.0 - _ramp(t, e1 + 0.04, e1 + 0.36))
    num["stub"] = max(_ramp(t, d0 - 0.42, d0 - 0.30) * (1.0 - _ramp(t, d1 + 0.40, d1 + 0.52)),
                      _ramp(t, e0 - 0.42, e0 - 0.30) * (1.0 - _ramp(t, e1 + 0.36, e1 + 0.48)))
    num["redraw1"], num["redraw2"], num["ang"] = _seg(t, d0, d1), _seg(t, e0, e1), STUB_ANG
    if t > pl:
        arm, side = _own_lines(P, x, y, h, face)
        pts["arm"], pts["side"] = arm, side
        if k1 > 0.0 or k2 > 0.0:
            tip, _ = _along(arm, _sm(_seg(t, d0, d1))) if k1 > 0.0 else _along(side, _sm(_seg(t, e0, e1)))
            k = max(k1, k2)
            grip = (tip[0] + _STUB_GRIP * math.cos(STUB_ANG), tip[1] + _STUB_GRIP * math.sin(STUB_ANG))
            P = _hands(P, x, y, h, face, None, grip, 0.0, k, 0.03)
            pts["tip"] = (float(tip[0]), float(tip[1]))
            if k >= 1.0:
                grab = {"b": grip}
            P = look_at(P, x, y, tip, h, face, 0.5 * k, 0.0)
    J = pose_joints(P, x, y, h, face)
    hand = J["ha_f"]
    if t <= s0 + 0.5:
        w = _ramp(t, pk - 0.10, pk + 0.05)
        pts["phone"] = (phone[0] + (hand[0] - phone[0]) * w, phone[1] + (hand[1] - phone[1]) * w)
    else:                                                         # it stays where the hand laid it, face down
        pts["phone"] = _laid_phone(x0, h)
    pts.update(thumb=J["ha_b"], crown=J["crown"], neck=J["neck"], pel=J["pel"], mouth=J["mouth"])
    stroke = 0.0
    for a_ in th_:
        stroke += _out((t - a_ + 0.03) / 0.32, 2.5)
    off = bump = 0.0
    for th in T["bumps"]:
        off = max(off, _env(t, th + 0.02, 0.18, 0.28, 0.42))
        bump = max(bump, _env(t, th, 0.08, 0.12, 0.50))
    num.update(held=1.0 if pk <= t <= s0 + 0.5 else 0.0, lit=_ramp(t, pk + 0.1, pk + 0.4) * (1.0 - _ramp(t, dn, dn + 0.3)), stroke=stroke,
               down=_ramp(t, dn, dn + 0.36), press=P["press"], hug=_ramp(t, s0 + 1.30, s0 + 2.80) * floor_, off=off, bump=bump)
    return Act(P, x, y, face, grab, 1.0, 1.0, 1.0, J, pts, num, h)


# ==========================================================================
# s05: the ring of backs and the family line (115.77 to 138.20)
# ==========================================================================
S05_T = dict(ring=115.77, closer=117.1, whispers=(118.40, 118.76, 119.14), speak=119.79, moth=121.0, effort=122.19,
             touch=(123.26, 124.76), out=126.265, part=(131.85, 134.0), slip=(134.51, 134.77), gather=135.6, stand=137.0)
_REACH = 120.0                                   # it stands this far from what it touches (world units at h = 380)

R_WATCH = PLANTED.but(turn=0.15, lean=0.05, bend=0.20, neck=0.0, look=(0.46, -0.02), gaze=(0.5, 0.1), eye=0.8, brow=0.6,
                      hair=0.25, hf=(0.03, -0.315), hb=(0.01, -0.315), hfz=0.0, hbz=0.0, mouth=-0.3)
R_PEEK = R_WATCH.but(pel=(0.035, 0.394), lean=0.22, bend=0.10, neck=-0.16, tilt=0.10, look=(0.55, 0.12), gaze=(0.6, 0.2),
                     eye=0.95, lid=0.6, lift=0.3, brow=0.5, hair=0.36, ab=-0.4)
R_HAND = R_PEEK.but(hf=(0.175, -0.07), mopen=0.15, lift=0.42, lean=0.20)
R_GIVE = R_WATCH.but(lean=0.08, bend=0.36, neck=0.20, look=(0.40, -0.40), gaze=(0.3, -0.4), eye=0.6, brow=0.85, mouth=-0.45,
                     hair=0.1)
R_BREATH = R_GIVE.but(bend=0.20, neck=0.0, look=(0.44, -0.02), gaze=(0.5, 0.2), chest=0.9, eye=0.8, lift=0.2, mouth=-0.2,
                      mopen=0.1)
R_SPEAK = R_BREATH.but(mopen=0.8, chest=0.3, neck=-0.06, look=(0.46, 0.08), lift=0.35, mouth=-0.05)
R_AFTER = R_BREATH.but(mopen=0.10, chest=0.0, eye=0.9, lid=0.6, brow=0.7, lift=0.3, hair=0.3)
R_RESOLVE = R_WATCH.but(lean=0.10, bend=0.16, look=(0.46, -0.06), eye=0.8, brow=0.45, mouth=-0.3)
R_GONE = R_RESOLVE.but(eye=1.05, lid=0.5, lift=0.45, brow=0.8, mopen=0.15, lean=0.12)
R_LOST = PLANTED.but(turn=0.10, pel=(0.0, 0.390), lean=0.12, bend=0.46, neck=0.32, look=(0.30, -0.74), gaze=(0.0, -0.3),
                     eye=0.5, lid=1.0, brow=0.7, mouth=-0.45, hair=0.05, hf=(0.035, -0.325), hb=(0.02, -0.325), hfz=0.0,
                     hbz=0.0)
L_FRONT = Pose(turn=1.0, pel=(0.0, 0.402), bend=0.26, neck=0.18, look=(0.0, -0.42), hf=(0.0, -0.31), hb=(0.0, -0.31),
               hfz=0.035, hbz=0.035, ff=(0.0, 0.0), fb=(0.0, 0.0), ffz=0.012, fbz=0.012, **_TIRED)
L_HOLD = L_FRONT.but(pel=(0.0, 0.408), bend=0.08, neck=-0.04, look=(0.0, 0.10), eye=0.85, lid=0.6, brow=0.35, lift=0.2,
                     mouth=-0.08, hair=0.42, hf=(0.0, 0.07), hfz=0.215, hb=(0.0, 0.07), hbz=0.215)
L_TAUT = L_HOLD.but(pel=(0.0, 0.398), bend=0.14, neck=0.0, look=(0.0, 0.0), eye=1.0, lid=0.45, brow=0.8, lift=0.35,
                    mouth=-0.3, mopen=0.15, hf=(0.0, 0.12), hfz=0.30, hb=(0.0, 0.12), hbz=0.30, hair=0.35)
L_PULL = L_FRONT.but(pel=(0.0, 0.318), bend=0.42, neck=0.40, look=(0.0, -0.66), eye=0.2, lid=1.0, brow=1.0, mouth=-0.65,
                     mopen=0.25, hf=(0.0, 0.155), hfz=0.31, hb=(0.0, 0.155), hbz=0.31, ffz=0.095, fbz=0.095, hair=0.12)
L_SLIP1 = L_PULL.but(pel=(0.0, 0.34), hf=(0.0, -0.06), hfz=0.20, roll=-0.24, pz=-0.035, look=(0.0, -0.3), hturn=-0.2, eye=0.95,
                     lid=0.5, lift=0.5, mopen=0.4, hair=0.4)
_L_SIT = SIT_FLOOR.but(turn=0.60, open=0.5, over=1.0)
G_PLOP = rebase(_L_SIT.but(lean=-0.05, bend=0.52, neck=0.30, look=(0.30, -0.42), eye=0.0, lid=1.0, brow=1.0, mouth=-0.6,
                           hf=(0.05, -0.10), hfz=0.27, hb=(0.05, -0.085), hbz=0.27, hair=0.5,
                           ff=(0.25, 0.0), fb=(0.28, 0.0)), 0.12, 0.0)          # it has sat down hard: the arms still out after them
G_SIT = rebase(_L_SIT.but(lean=0.10, bend=0.56, neck=0.30, look=(0.30, -0.50), eye=0.6, lid=0.9, brow=0.9, mouth=-0.5,
                          hf=(0.10, -0.27), hb=(0.12, -0.26), hair=0.05), 0.12, 0.0)
G_REACH = G_SIT.but(lean=0.52, bend=0.60, neck=0.16, look=(0.36, -0.72), gaze=(0.3, -0.5), eye=0.7)
_KNEE_SIT = ((-0.100, 0.105), (0.063, 0.110))    # the two halves held together on its knees (grip points, body units as seen,
_CHEST_SIT = ((-0.090, 0.172), (-0.032, 0.178))  #   at sheet = 0.5), and where they go into the jumper, under the chin
G_KNEE = G_SIT.but(lean=0.14, bend=0.62, neck=0.40, look=(0.30, -0.84), gaze=(0.0, -0.6), eye=0.5, brow=1.0, mouth=-0.5)
G_CHEST = _seen(G_SIT.but(lean=0.12, bend=0.64, neck=0.44, look=(0.28, -0.86), gaze=(0.0, -0.6), eye=0.34, brow=0.9,
                          mouth=-0.5), hf=_CHEST_SIT[0], hb=_CHEST_SIT[1])
_G_UP1 = _seen(G_CHEST.but(pel=(-0.10, 0.10), lean=0.60, bend=0.55, turn=0.45, neck=0.34), hf=(-0.037, 0.184), hb=(0.021, 0.19))
_G_UP2 = _seen(_SU2.but(turn=0.25, ff=G_SIT["ff"], fb=G_SIT["fb"]), hf=(0.058, 0.295), hb=(0.116, 0.29))     # (the arms go under
_G_UP3 = _seen(_SU3.but(turn=0.10, ff=STOPPED["ff"], fb=STOPPED["fb"]), hf=(0.06, 0.43), hb=(0.105, 0.43))    #  the head again)


@lru_cache(maxsize=16)
def _s05_route(closer, t1, t2, out, x0, x1, h, b1x, b2x):
    d1 = (b1x - _REACH - x0) / h                 # travelled by the first touch, in two small steps
    d2 = (b2x - b1x) / h                         # one more step to the next back
    steps = ((closer, 0.55, 0.5 * d1, "b", 0.028), (t1 - 0.74, 0.40, 0.5 * d1, "b", 0.026), (t2 - 0.80, 0.46, d2, "b", 0.036))
    xa = x0 + h * (d1 + d2)
    W = _walk(out, xa, x1, h, out, 5, 0.0, rest=STOPPED, rest0=R_LOST)[0]
    return steps, xa, W.t1


def _s05_plan(T, x0, x1, h, backs):
    """The small steps toward the two backs, where the walk out begins, and when it has arrived."""
    return _s05_route(T["closer"], T["touch"][0], T["touch"][1], T["out"], x0, x1, h, float(backs[0][0]), float(backs[1][0]))


def _s05_raw(t, T, x0, x1, h, backs, moth):
    steps, xa, ta = _s05_plan(T, x0, x1, h, backs)
    w1, w2, w3 = T["whispers"]
    sk, mo, ef = T["speak"], T["moth"], T["effort"]
    t1, t2 = T["touch"]
    out = T["out"]
    if t <= out:
        keys = ((T["ring"] + 0.3, 0.9, R_WATCH, K_ACT), (T["closer"] + 0.05, 0.75, R_PEEK, K_ACT), (w1 - 0.42, 0.40, R_HAND, K_HAND),
                (w3 + 0.22, 0.65, R_GIVE, K_SLOW), (sk - 0.44, 0.42, R_BREATH, K_ACT), (sk, 0.26, R_SPEAK, K_SOFT),
                (sk + 0.80, 0.50, R_AFTER, K_SOFT), (ef + 0.25, 0.55, R_RESOLVE, K_ACT), (t1 + 0.10, 0.34, R_GONE, K_SOFT),
                (t1 + 0.80, 0.50, R_RESOLVE, K_SOFT), (t2 + 0.10, 0.34, R_GONE, K_SOFT), (t2 + 0.62, 0.66, R_LOST, K_SLOW))
        P = chain(t, PLANTED, keys)
        P, dxb = _steps(P, t, steps)
        x = x0 + h * dxb
        for i, tw in enumerate((w1, w2, w3)):                    # the whispers go round: the eyes go after them
            e = _env(t, tw, 0.08, 0.14, 0.22)
            if e > 0.0:
                g_ = P["gaze"]
                P = P.but(gaze=(g_[0] + (0.3 - 0.25 * i) * e, g_[1] + 0.2 * e), tilt=P["tilt"] + 0.03 * e)
        m_ = 0.0                                                  # the voice: two small tries
        for a_, b_, k_ in ((sk + 0.02, 0.36, 0.3), (sk + 0.40, 0.34, 0.6)):
            m_ = max(m_, k_ * _bell(t, a_, b_))
        if m_ > 0.0:
            P = P.but(mopen=min(1.0, P["mopen"] + 0.3 * m_), chest=P["chest"] + 0.3 * m_)
        km = _ramp(t, sk + 0.25, mo - 0.15) * (1.0 - _ramp(t, ef - 0.05, ef + 0.55))      # the eyes follow the moth
        if km > 0.0:
            P = look_at(P, x, FLOOR, moth, h, 1, km, 0.6)
            kr = _ramp(t, mo + 0.25, mo + 0.80) * (1.0 - _ramp(t, ef - 0.25, ef + 0.50))  # a hand goes up after it, half way
            if kr > 0.0:
                sx, sy = x + 0.02 * h, FLOOR - 0.63 * h                                   # about its shoulder
                el = max(-0.3, min(0.20, math.atan2(sy - moth[1], abs(moth[0] - sx) + 1e-9)))    # (higher, the hand would
                r = 0.30 * h                                                              #  be in front of its own face)
                sg = 1.0 if moth[0] >= sx else -1.0
                P = reach_to(P, x, FLOOR, (sx + sg * r * math.cos(el), sy - r * math.sin(el)), h, 1, "f", kr, 0.3, 0.03)
        # the hand on a back; the back goes; the hand stays in the air, sinks
        k1 = _ramp(t, t1 - 0.40, t1) * (1.0 - 0.55 * _ramp(t, t1 + 0.75, t1 + 1.10))
        k2 = _ramp(t, t2 - 0.42, t2)
        kk = k1 if t < t2 - 0.42 else max(k1 * (1.0 - k2), k2) * (1.0 - _ramp(t, t2 + 0.60, t2 + 1.15))
        if kk > 0.0:
            w = _ramp(t, t2 - 0.46, t2 - 0.04)
            pt = (backs[0][0] + (backs[1][0] - backs[0][0]) * w, backs[0][1] + (backs[1][1] - backs[0][1]) * w)
            P = reach_to(P, x, FLOOR, pt, h, 1, "f", kk, 0.8, 0.02)
        return P, x, FLOOR, 1
    W, m = _walk(t, xa, x1, h, out, 5, 0.0, rest=STOPPED, rest0=R_LOST)
    if t < W.t1:
        k = _ramp(t, W.t0, W.t0 + 0.6) * (1.0 - _ramp(t, W.t1 - 0.6, W.t1))
        return _tired(W.pose, k), W.x, FLOOR, 1
    p0, p1 = T["part"]
    q0, q1 = T["slip"]
    g0, st = T["gather"], T["stand"]
    tf = ta + 0.08                                                # it turns to face us
    if t < tf + 0.55:
        return turn_round(STOPPED, L_FRONT, (t - tf) / 0.55), x1, FLOOR, 1
    if t < q1 + 0.02:
        keys = ((tf + 0.60, 0.70, L_HOLD, K_HAND), (p0, p1 - p0, L_PULL, K_EASE, ((0.30, L_TAUT),)), (q0, 0.13, L_SLIP1, K_HIT))
        P = chain(t, L_FRONT, keys)
        th_ = tf + 1.30                                           # it looks at the one, then at the other
        gl = _bell(t, th_ + 0.05, 0.9) - _bell(t, th_ + 0.85, 0.9)
        if gl:
            P = P.but(hturn=P["hturn"] + 0.22 * gl, gaze=(0.0, 0.5 * abs(gl)), look=(P["look"][0], P["look"][1] + 0.15 * abs(gl)))
        if t > p0:                                                # feet apart, one after the other; then the strain
            v1, v2 = _c((t - p0 - 0.25) / 0.26), _c((t - p0 - 0.60) / 0.26)
            P = P.but(ffz=L_FRONT["ffz"] + (L_PULL["ffz"] - L_FRONT["ffz"]) * _sm(v1), fbz=L_FRONT["fbz"] + (L_PULL["fbz"] - L_FRONT["fbz"]) * _sm(v2),
                      ff=(0.0, 0.03 * math.sin(math.pi * v1)), fb=(0.0, 0.03 * math.sin(math.pi * v2)))
            e = _ramp(t, p0 + 0.9, p1) * (1.0 - _ramp(t, q0, q0 + 0.05))
            if e > 0.0:
                q = math.sin((t - p0) * 2.0 * math.pi * 7.0) * e
                P = P.but(hf=(P["hf"][0], P["hf"][1] + 0.005 * q), hb=(P["hb"][0], P["hb"][1] - 0.005 * q), roll=P["roll"] + 0.008 * q)
        return P, x1, FLOOR, 1
    keys = ((q1 + 0.02, 0.40, G_PLOP, K_FALL), (q1 + 0.62, 0.50, G_SIT, K_SLOW), (g0 - 0.12, 0.36, G_REACH, K_HAND),
            (g0 + 0.34, 0.46, G_KNEE, K_SOFT), (g0 + 1.03, 0.36, G_CHEST, K_SLOW))
    if t < st:
        P = chain(t, L_SLIP1, keys)
        e = _bell(t, q1 + 0.30, 0.34)                             # it lands: the spine gives, the hair flies up
        if e > 0.0:
            P = P.but(bend=P["bend"] + 0.14 * e, neck=P["neck"] + 0.10 * e, bob=P["bob"] + 0.7 * e)
        e = _bell(t, q1 + 0.04, 0.40)                             # its feet go from under it
        if e > 0.0:
            P = P.but(ff=(P["ff"][0], P["ff"][1] + 0.05 * e), fb=(P["fb"][0], P["fb"][1] + 0.035 * e))
        e = _ramp(t, q1 + 0.46, q1 + 0.62) * (1.0 - _ramp(t, g0 - 0.16, g0))      # the eyes open: it looks after them, the one
        if e > 0.0:                                               # side, then the other (the head hardly turns)
            sw = math.sin((t - q1 - 0.46) * 2.0 * math.pi / 0.72)
            P = P.but(eye=max(P["eye"], 0.72 * e), hturn=P["hturn"] + 0.16 * sw * e, gaze=(0.75 * sw * e, 0.1 * e),
                      look=(P["look"][0], P["look"][1] + 0.30 * e), neck=P["neck"] - 0.14 * e)
        return P, x1, FLOOR, 1
    return through([G_CHEST, _G_UP1, _G_UP2, _G_UP3, STOPPED], [0.0, 0.22, 0.50, 0.76, 1.0], (t - st) / 0.92, W_BODY), x1, FLOOR, 1


def s05(t: float, x0: float = ST.X4, x1: float = ST.X5, backs=None, moth=None, hands=None, sheet: float = 0.5, h: float = H0,
        **times) -> Act:
    """The ring of backs and the family line, 115.77 to 138.20. From hand-off B4 (planted at x0, the
    ring drawing itself on to its right): it watches them come, goes a small step closer and leans to
    look in, a hand half raised; its eyes go after the whispers; the hand sinks. It speaks (speak): a
    breath, the mouth, two small tries; its eyes follow what leaves its mouth to the lamp and round
    it (moth: a world point, the moth's place now), a hand goes up after it half way and sinks
    (effort). It steps up to the nearest back and its hand arrives on it on touch[0]: the back goes
    from under the hand, the hand stays in the air; a step to the next (touch[1]): gone too; the arm
    drops, the head goes down. It walks on through the gap to x1 (out; a step a beat, 5 steps),
    turns to face us and gives a hand to each side (arms up and out: the tall figures take them); it
    looks up at the one, then the other. They slide away (part): its arms are pulled straight, the
    feet go apart, it hangs between the two lines with all its weight, trembling; the left line
    slips (slip[0]): that arm falls in, the body is pulled over to the right; the right one slips
    (slip[1]): it sits down hard, eyes shut, the arms left out after them, low; the eyes open and
    go after the one, then the other; the arms sink. The two halves have fallen out of its jumper:
    a hand goes down for each (gather), it holds them together on its knees and looks, takes them
    to its chest and they are gone into the jumper; it gets up (stand), a hand still on its chest.
    Ends in hand-off B5 (STOPPED at x1).
    backs: ((x, y), (x, y)) the world points on the two backs it touches (people: R.who[j]["back"];
    default: those of ring_of_backs(x0 + 405)). moth: (x, y) or None (then the lamp is assumed at
    (x0 + 405, 260)). hands: ((xl, yl), (xr, yr)) to pin its hands to the tall figures' hands
    instead of letting the lines end where its own hands are. sheet: the scale of the two halves
    (things.family_held's s; 0.5: the pair is 75 units wide). times: any key of S05_T.
    pts: hand (the reaching hand), hand_l, hand_r (its two hands as seen: where the family's lines
    end: family_line(hands=(hand_l, hand_r), small=False)), half_l, half_r (while num["halves"] > 0:
    the two points things.family_held takes: family_held(F, half_l, half_r, s=num["sheet"],
    a=num["halves"] * (1 - num["tuck"])); the mitts are beside the paper's outer edges), mouth,
    crown. num: speak (the mouth), touch1, touch2 (0..1: the hand is on that back), hold (0..1: it
    has given its hands), strain (0..1), slip_l, slip_r (0..1 after each line has slipped), halves
    (0 in the jumper, 0..1 as they fall out, 1 out: lying, held), tuck (0..1 going back into the
    jumper), sheet (the scale to draw them with), sit (0..1: it sits on the ground)."""
    T = dict(S05_T, **times) if times else S05_T
    st = T["stand"]
    if t <= T["ring"] or t >= st + 0.95:
        first = t <= T["ring"]
        A = hold_B4(t, x0, h) if first else hold_B5(t, x1, h)
        a_, b_ = A.J["ha_f"], A.J["ha_b"]
        A.pts.update(hand=a_, hand_l=a_ if a_[0] <= b_[0] else b_, hand_r=b_ if a_[0] <= b_[0] else a_)
        z = 0.0 if first else 1.0
        A.num.update(speak=0.0, touch1=0.0, touch2=0.0, hold=0.0, strain=0.0, slip_l=z, slip_r=z, halves=0.0, tuck=z, sit=0.0,
                     sheet=sheet)
        return A
    if backs is None:
        backs = ((x0 + 175.0, FLOOR - 216.0), (x0 + 257.0, FLOOR - 187.0))
    if moth is None:
        moth = (x0 + 405.0, 260.0)
    raw = lambda tt: _s05_raw(tt, T, x0, x1, h, backs, moth)
    steps, xa, ta = _s05_plan(T, x0, x1, h, backs)
    t1, t2 = T["touch"]
    p0, p1 = T["part"]
    q0, q1 = T["slip"]
    g0 = T["gather"]
    sk, ef = T["speak"], T["effort"]
    quiet = ((T["closer"], T["whispers"][2] + 0.9), (sk - 0.5, ef + 0.8), (t1 - 0.5, t1 + 1.3), (t2 - 0.5, t2 + 1.3), (ta, ta + 2.8),
             (p0, st + 1.0))
    P, x, y, face = _finish(t, raw, h, quiet, shift=1.0 - _ramp(t, ta, ta + 0.5) * (1.0 - _ramp(t, st + 0.5, st + 0.9)))
    grab, pts, num = None, {}, {}
    tf = ta + 0.08
    hold = _ramp(t, tf + 0.86, tf + 1.30) if t > ta else 0.0
    if hands is not None and hold > 0.0 and t < q1:
        kl = hold * (1.0 - _ramp(t, q0, q0 + 0.06))
        kr = hold * (1.0 - _ramp(t, q1, q1 + 0.06))
        P = _hands(P, x, y, h, face, hands[0], hands[1], kl, kr, 0.0)
        grab = {k: v for k, v, kk in (("f", tuple(hands[0]), kl), ("b", tuple(hands[1]), kr)) if kk >= 1.0} or None
    # the two halves: they fall out of its jumper as it lands and lie there; a hand goes down for each; it holds them
    # together on its knees and looks; it takes them to its chest and they are gone into the jumper (before it gets up)
    tfall = q1 + 0.30
    num["halves"], num["tuck"], num["sheet"] = 0.0, (1.0 if t >= g0 + 1.40 else 0.0), sheet
    if tfall < t < g0 + 1.40:
        k_ = sheet / 0.5
        W_ = lambda p: (x1 + h * p[0], FLOOR - h * p[1])
        FL, FR = (x1 + 18.0 * k_, FLOOR - 13.0 * sheet - 5.0), (x1 + 18.0 * k_ + 156.0 * sheet, FLOOR - 13.0 * sheet - 3.0)
        KL, CL, CR = W_(_KNEE_SIT[0]), W_(_CHEST_SIT[0]), W_(_CHEST_SIT[1])
        KR = (KL[0] + 124.0 * sheet, W_(_KNEE_SIT[1])[1])         # together: the hands 124 sheet apart (things.family_held)
        fall = _c((t - tfall) / 0.34)
        c0 = (x1 - 0.105 * h, FLOOR - 0.19 * h)                   # where they leave the jumper
        wl, wr = _ramp(t, g0 + 0.30, g0 + 0.70), _ramp(t, g0 + 0.38, g0 + 0.76)
        tk = _ramp(t, g0 + 1.04, g0 + 1.40)
        TL = (c0[0] + (FL[0] - c0[0]) * _out(fall, 1.6), c0[1] + (FL[1] - c0[1]) * fall * fall)
        TR = (c0[0] + (FR[0] - c0[0]) * _out(fall, 1.4), c0[1] + (FR[1] - c0[1]) * fall ** 1.7)
        TL = (TL[0] + (KL[0] - TL[0]) * wl, TL[1] + (KL[1] - TL[1]) * wl - 16.0 * math.sin(math.pi * wl))
        TR = (TR[0] + (KR[0] - TR[0]) * wr, TR[1] + (KR[1] - TR[1]) * wr - 20.0 * math.sin(math.pi * wr))
        TL = (TL[0] + (CL[0] - TL[0]) * tk, TL[1] + (CL[1] - TL[1]) * tk)
        TR = (TR[0] + (CR[0] - TR[0]) * tk, TR[1] + (CR[1] - TR[1]) * tk)
        kl, kr = _ramp(t, g0 - 0.04, g0 + 0.26), _ramp(t, g0 + 0.08, g0 + 0.36)
        if kl > 0.0 or kr > 0.0:                                  # the mitts go beside the paper's outer edges, not under it
            o = _edge(sheet) * (1.0 - tk)
            P = _hands(P, x, y, h, face, (TL[0] - o, TL[1] + 0.3 * o), (TR[0] + o, TR[1] + 0.3 * o), kl, kr, 0.02)
        pts["half_l"], pts["half_r"] = TL, TR
        num["halves"], num["tuck"] = _ramp(t, tfall, tfall + 0.2), tk
        num["sheet"] = sheet * (0.55 + 0.45 * _ramp(t, tfall, tfall + 0.24)) * (1.0 - 0.6 * tk)
    J = pose_joints(P, x, y, h, face)
    a_, b_ = J["ha_f"], J["ha_b"]
    pts.update(hand=a_, mouth=J["mouth"], crown=J["crown"])
    pts["hand_l"], pts["hand_r"] = (a_, b_) if a_[0] <= b_[0] else (b_, a_)
    num.update(speak=P["mopen"], touch1=_ramp(t, t1 - 0.04, t1) * (1.0 - _ramp(t, t1 + 0.75, t1 + 1.10)),
               touch2=_ramp(t, t2 - 0.04, t2) * (1.0 - _ramp(t, t2 + 0.60, t2 + 1.15)), hold=hold * (1.0 if t < q1 else 0.0),
               strain=_ramp(t, p0, p1) * (1.0 - _ramp(t, q1, q1 + 0.1)), slip_l=_ramp(t, q0, q0 + 0.5), slip_r=_ramp(t, q1, q1 + 0.5),
               sit=_ramp(t, q1, q1 + 0.36) * (1.0 - _ramp(t, st, st + 0.6)))
    return Act(P, x, y, face, grab, 1.0, 1.0, 1.0, J, pts, num, h)


# ==========================================================================
# the rest states of the hand-offs, and the whole of it
# ==========================================================================
def _hold(t, P, x, h, blink=1.0, shift=1.0):
    Q = alive(P, t, ST.CHILD_SEED, blink=blink, shift=shift)
    J = pose_joints(Q, x, FLOOR, h, 1)
    return Act(Q, x, FLOOR, 1, None, 1.0, 1.0, 1.0, J, dict(crown=J["crown"], mouth=J["mouth"]), {}, h)


def hold_B1(t: float, x: float = ST.X1, h: float = H0) -> Act:
    """Hand-off B1 (36.27): standing beside the sofa, head down (STOPPED), facing right; alive."""
    return _hold(t, STOPPED, x, h)


def hold_B2(t: float, x: float = ST.X2, h: float = H0) -> Act:
    """Hand-off B2 (58.60), and the whole silence before it (from 56.0): standing, head down, turned
    three-quarter to us, both hands at its chest on what it tucked away (HUSH). Still but for the
    breath: no shift of weight, no chance blink, one slow blink at 57.1."""
    return _hold(t, HUSH.but(blink=_blink(t, 57.09, 0.80)), x, h, 0.0, 0.0)


def hold_B3(t: float, x: float = ST.X3, h: float = H0) -> Act:
    """Hand-off B3 (91.77): standing on the rug of the evening room, head a little down, its eyes on
    the phone (ON_RUG), facing right; alive."""
    return _hold(t, ON_RUG, x, h)


def hold_B4(t: float, x: float = ST.X4, h: float = H0) -> Act:
    """Hand-off B4 (115.77): planted: feet apart, braced, head level (PLANTED), facing right; alive."""
    return _hold(t, PLANTED, x, h)


def hold_B5(t: float, x: float = ST.X5, h: float = H0) -> Act:
    """Hand-off B5 (138.20): standing, head down (STOPPED), the two halves tucked away; alive."""
    return _hold(t, STOPPED, x, h)


CHILD_HANDOFF = {"B1": (36.27, hold_B1), "B2": (58.60, hold_B2), "B3": (91.77, hold_B3), "B4": (115.77, hold_B4),
                 "B5": (138.20, hold_B5)}


def perform(t: float, **kw) -> Act:
    """The child's whole solo performance, 0 to 138.2 s: s01 .. s05 by their spans (kw goes to the
    section that holds t: only pass what that section takes)."""
    if t < 36.27:
        return s01(t, **kw)
    if t < 58.60:
        return s02(t, **kw)
    if t < 91.77:
        return s03(t, **kw)
    if t < 115.77:
        return s04(t, **kw)
    return s05(t, **kw)
