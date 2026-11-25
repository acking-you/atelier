"""hx.chalk.acting_pair: the friend, and the two together (the far friend of s03, and s06 to s11:
138.2 s to the end). Read hx/chalk/doc/acting_pair.md.

A performance is a pure function of the song's time. It returns a Duet: one Act for the child, one
for the friend (pose, ground point, face, grab, pressure: everything figure() needs) and the world
points the two share with each other and with the scene (the joined hands, the grips on the
curtains, the hand that holds the string ...).

    D = s06(F.t)
    Jc, Jf = D.show(F)                      # draws both in the right order; or D.child.show(F), D.friend.show(F)
    amber_rub(F, D.pts["hands"], D.num["warm"])          # what the scene stages with the returned points

How it is made: key poses built on the rig's library, moved with overlapping action (the eyes lead,
then the head, the spine, the hands; the hair arrives last; anticipation and a small overshoot); the
two never move as one: one acts, the other answers a few frames later; eye lines are aimed at the
other's head; hands that meet are pinned (grab) on BOTH figures to one shared world point. Journeys
(walks, the run with its jumps) are planned once per set of arguments and keep every stance foot
planted. Every hold breathes and blinks (the rig's alive). No state between frames, no randomness.
Times are the song's (absolute seconds), with the storyboard's values as defaults. No lyric text.

Every hand-off of these sections has its REST STATE as a function of time: hold_B6 ... hold_B10
(the figures in the named state, alive but not acting). A section begins in the rest state of the
hand-off before it and ends in the one after it at least 0.25 s before the hand-off time.
"""
from __future__ import annotations

import math
from bisect import bisect_right
from functools import lru_cache

import numpy as np

from .. import story as ST
from .figure import (BACK_STAND, F_CALL, F_CROUCH, F_OFFER, F_STAND, HOLD, JUMP, LOOK_UP, SIT_EDGE, SIT_HUG, SIT_LIFT, STAND,
                     STOPPED, TORSO, Pose, act, aim_foot, aim_hand, alive, figure, mixp, mixs, pose_joints, rebase, run, solve,
                     swap_sides, turn_round, walk, walk_away)
from .figure import _ankle_x, _step          # the rig's own planted step (walk_to is built on these two)
from .figure import curl_up_pose, roll_over_pose        # the lying specialist's moves between sitting, curled and on its back

__all__ = ["Act", "Duet", "beat", "beat_after",
           "s03_friend", "s06", "s07", "s08", "s09", "s10", "s11", "window_friend",
           "hold_B6", "hold_B7", "hold_B8", "hold_B9", "hold_B10", "PAIR_HANDOFF",
           "hold_hands", "eye_to_eye", "look_to", "side_by_side", "run_together", "stand_on",
           "S07_T", "S08_T", "S09_T", "S10_T", "S11_T"]

FLOOR = ST.FLOOR
HC, HF = ST.CHILD_H, ST.FRIEND_H
SC, SF = ST.CHILD_SEED, ST.FRIEND_SEED
BEAT0, BEAT = 0.265, 0.75
HALF_PI = math.pi / 2.0
_DT = 0.10                              # the look-back of the follow-through (seconds)


def beat(k: float) -> float:
    """The time of beat k of the song (beat 0 at 0.265 s, 0.75 s apart)."""
    return BEAT0 + BEAT * k


def beat_after(t: float) -> float:
    """The first beat at or after t."""
    return BEAT0 + BEAT * math.ceil((t - BEAT0) / BEAT - 1e-6)


_beat_after = beat_after


# --------------------------------------------------------------------------
# what a performance returns
# --------------------------------------------------------------------------
class Act:
    """One figure at one moment. pose, x, y, face, grab, draw, a go into figure(); h is the standing
    height, skin "child" / "friend", seed the hand; lift: world units the figure is in the air above
    the ground under it (a jump: for its shadow). pts / num: named world points and numbers (cues for
    the scene) of a solo performance (s03_friend, window_friend); a Duet carries its own."""
    __slots__ = ("pose", "x", "y", "face", "grab", "draw", "a", "h", "skin", "seed", "lift", "pts", "num")

    def __init__(self, pose, x, y=FLOOR, face=1, grab=None, h=HC, skin="child", seed=SC, a=1.0, draw=1.0, lift=0.0,
                 pts=None, num=None):
        self.pose, self.x, self.y, self.face, self.grab = pose, float(x), float(y), face, grab
        self.h, self.skin, self.seed, self.a, self.draw, self.lift = h, skin, seed, a, draw, lift
        self.pts = {} if pts is None else pts
        self.num = {} if num is None else num

    def show(self, F, a: float = 1.0, **kw):
        """Draw it: figure(F, x, y, h, pose, skin, face, seed, a, grab, draw, **kw) -> world joints."""
        if self.draw <= 0.0 or self.a * a <= 0.0:
            return self.joints()
        return figure(F, self.x, self.y, self.h, self.pose, self.skin, self.face, seed=self.seed, a=self.a * a,
                      grab=self.grab, draw=self.draw, **kw)

    def joints(self) -> dict:
        """The world joints without drawing (pose_joints, with the pinned hands applied)."""
        P = self.pose
        if self.grab:
            fh = (1 if self.face >= 0 else -1) * self.h
            c_, s_ = math.cos(P["rot"]), math.sin(P["rot"])
            for which, pt in self.grab.items():
                bx, by = (pt[0] - self.x) / fh, (self.y - pt[1]) / self.h
                P = aim_hand(P, which, (bx * c_ - by * s_, bx * s_ + by * c_))
        return pose_joints(P, self.x, self.y, self.h, self.face)


class Duet:
    """The two at one moment. child, friend: an Act each (friend is None while it is not in the
    picture). pts: named world points (x, y); num: named numbers (cues for the scene). order: who is
    drawn first ("fc": the friend, then the child on top; "cf": the child first)."""
    __slots__ = ("child", "friend", "pts", "num", "order")

    def __init__(self, child, friend=None, pts=None, num=None, order="fc"):
        self.child, self.friend, self.order = child, friend, order
        self.pts = {} if pts is None else pts
        self.num = {} if num is None else num

    def show(self, F, child_kw=None, friend_kw=None):
        """Draw both in `order`. Returns (child joints, friend joints or None)."""
        jc = jf = None
        for who in self.order:
            if who == "f" and self.friend is not None:
                jf = self.friend.show(F, **(friend_kw or {}))
            elif who == "c" and self.child is not None:
                jc = self.child.show(F, **(child_kw or {}))
        return jc, jf


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


def _out(u, p=3.0):
    """Fast start, slow arrival (a reaction, a landing)."""
    return 1.0 - (1.0 - _c(u)) ** p


def _bell(t, t0, dur):
    u = (t - t0) / dur
    return math.sin(math.pi * u) ** 2 if 0.0 < u < 1.0 else 0.0


def _env(t, t0, up=0.10, hold=0.08, down=0.55):
    """An effort's or a reaction's envelope: 0 before t0, up to 1 fast, held, released slowly."""
    d = t - t0
    if d <= 0.0 or d >= up + hold + down:
        return 0.0
    if d < up:
        return _out(d / up)
    if d < up + hold:
        return 1.0
    return 1.0 - _sm((d - up - hold) / down)


def _blinkat(t, t0, dur=0.26):
    """An acted blink that is closed at about t0 + 0.4 dur."""
    u = (t - t0) / dur
    if u <= 0.0 or u >= 1.0:
        return 0.0
    return _sm(u / 0.32) if u < 0.32 else (1.0 if u < 0.48 else 1.0 - _sm((u - 0.48) / 0.52))


def _lerp(p, q, w):
    return (p[0] + (q[0] - p[0]) * w, p[1] + (q[1] - p[1]) * w)


def _mirror(P):
    """The pose that draws exactly the same picture with `face` mirrored. The rig's swap_sides turns
    the body about its pelvis, which is the same picture only when the pelvis stands over the ground
    point; this also puts pelvis and feet back where they were (pel x -> -x, feet x - 2 pel x)."""
    Q = swap_sides(P)
    px, py = P["pel"]
    if not px:
        return Q
    return Q.but(pel=(-px, py), ff=(Q["ff"][0] - 2.0 * px, Q["ff"][1]), fb=(Q["fb"][0] - 2.0 * px, Q["fb"][1]))


def _add(p, dx, dy):
    return (p[0] + dx, p[1] + dy)


def _flip(A, dx=0.0, dy=0.0, x=None, y=None):
    """The Act that draws exactly the same figure written for the other `face` (pose mirrored, pinned hands
    renamed); with x, y also from another ground point (dx, dy: its offset in body units as seen). Only the
    slant of the garment's zigzag differs between the two ways of writing, so a performance changes over in the
    middle of a fast turn, never on a still frame."""
    P = _mirror(A.pose)
    if x is not None:
        P = rebase(P, dx, dy)
    g = None if not A.grab else {("b" if k == "f" else "f"): v for k, v in A.grab.items()}
    return Act(P, A.x if x is None else x, A.y if y is None else y, -A.face, g, A.h, A.skin, A.seed, a=A.a, draw=A.draw,
               lift=A.lift, pts=A.pts, num=A.num)


def _pt(p):
    return (float(p[0]), float(p[1]))


# --------------------------------------------------------------------------
# one acted move, with a choice of what leads
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


_W_HEAD = _compile(eyes=(0.0, 0.50), head=(0.08, 0.66), body=(0.16, 0.82), feet=(0.16, 0.82), hand=(0.26, 0.94),
                   mouth=(0.34, 0.86), hair=(0.46, 1.0))          # a look, a lift: the eyes lead
_W_HAND = _compile(eyes=(0.0, 0.42), head=(0.14, 0.74), body=(0.20, 0.90), feet=(0.20, 0.90), hand=(0.04, 0.72),
                   mouth=(0.30, 0.80), hair=(0.45, 1.0))          # a reach: the hand leads after the eyes
_W_BODY = _compile(eyes=(0.04, 0.60), head=(0.16, 0.92), body=(0.0, 0.78), feet=(0.0, 0.72), hand=(0.10, 0.94),
                   mouth=(0.30, 0.80), hair=(0.40, 1.0))          # a sit, a rise, a heave: the weight leads
_W_FLAT = _compile(eyes=(0.0, 1.0), head=(0.0, 1.0), body=(0.0, 1.0), feet=(0.0, 1.0), hand=(0.0, 1.0), mouth=(0.0, 1.0),
                   hair=(0.0, 1.0))


def _move(a, b, u, win=_W_HEAD, ant=0.07, over=0.07, blink=0.0, warp=0.0):
    """One acted move from pose a to pose b, u = 0..1 over the whole move. win: what leads. ant: the
    dip the other way before head and spine go; over: the overshoot; blink: a blink on the way; warp:
    > 0 a fast start that slows in (a reaction, a landing), < 0 a slow start."""
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


# mode of a key -> (window, anticipation, overshoot, blink, warp)
_KIND = {
    "body": (_W_BODY, 0.06, 0.07, 0.0, 0.0),       # the weight leads
    "hand": (_W_HAND, 0.05, 0.06, 0.0, 0.0),       # the hand leads
    "soft": (_W_HEAD, 0.0, 0.03, 0.0, 0.0),        # small: no wind-up
    "slow": (_W_HEAD, 0.0, 0.0, 0.0, -0.5),        # sinking: a slow start
    "land": (_W_BODY, 0.0, 0.14, 0.0, 0.6),        # weight coming down: fast, lands and settles
    "jolt": (_W_FLAT, 0.0, 0.10, 0.0, 1.4),        # a jerk
    "blink": (_W_HEAD, 0.07, 0.07, 1.0, 0.0),      # the eyes lead, a blink on the way
}


# --------------------------------------------------------------------------
# tracks of key poses
# --------------------------------------------------------------------------
class _Track:
    """Key poses in time. keys: (t0, dur, pose[, mode[, kw]]) in order; each move starts at t0 from the
    pose before it and must be over before the next begins. mode: "act" (the rig's overlapping
    action, the eyes lead; kw: ant, over, blink), "body" / "hand" / "soft" / "slow" / "land" / "jolt" /
    "blink" (see _KIND), "mix" (one smooth blend), "hit" (fast attack: a reaction), "turn"
    (turn_round), "s" (mixs: ankles travel straight)."""
    __slots__ = ("p0", "ts", "keys")

    def __init__(self, p0, *keys):
        self.p0 = p0
        self.keys = keys
        self.ts = [k[0] for k in keys]
        for a, b in zip(keys, keys[1:]):
            assert a[0] + a[1] <= b[0] + 1e-6, ("moves overlap", a[0], a[1], b[0])

    def at(self, t):
        i = bisect_right(self.ts, t) - 1
        if i < 0:
            return self.p0
        k = self.keys[i]
        u = (t - k[0]) / k[1]
        if u >= 1.0:
            return k[2]
        prev = self.keys[i - 1][2] if i else self.p0
        mode = k[3] if len(k) > 3 else "act"
        if mode == "act":
            return act(prev, k[2], u, **(k[4] if len(k) > 4 else {}))
        if mode == "mix":
            return mixp(prev, k[2], _sm(u))
        if mode == "hit":
            return mixp(prev, k[2], _out(u))
        if mode == "turn":
            return turn_round(prev, k[2], u, **(k[4] if len(k) > 4 else {}))
        if mode == "s":
            return mixs(prev, k[2], _sm(u))
        return _move(prev, k[2], u, *_KIND[mode])

    def end(self):
        return self.keys[-1][2] if self.keys else self.p0

    def busy(self, t):
        """True while a move runs (so that a chance blink does not fall into it)."""
        i = bisect_right(self.ts, t) - 1
        return i >= 0 and t < self.keys[i][0] + self.keys[i][1]


def _head_q(P):
    """About where the head is, in body units from the ground point (cheap; before rot)."""
    a = P["lean"] + 0.5 * P["bend"]
    b = P["lean"] + P["bend"] + P["neck"]
    px, py = P["pel"]
    c = math.cos(P["turn"] * HALF_PI)
    return px + (TORSO * math.sin(a) + 0.137 * math.sin(b)) * c, py + TORSO * math.cos(a) + 0.137 * math.cos(b)


def _follow(P1, P0, dxb=0.0, dyb=0.0, k=1.0):
    """Follow-through without state: sway and bob of hair, scarf and hem from how far the head has
    moved since the pose _DT seconds ago (dxb, dyb: the travel of the ground point, body units)."""
    (ax, ay), (bx, by) = _head_q(P1), _head_q(P0)
    vx = (ax - bx + dxb) / _DT
    vy = (ay - by + dyb) / _DT
    return P1.but(sway=max(-1.0, min(1.0, P1["sway"] + 0.9 * k * vx)), bob=max(-1.0, min(1.0, P1["bob"] - 0.9 * k * vy)))


def _quiet(t, spans):
    for a, b in spans:
        if a <= t <= b:
            return 0.0
    return 1.0


def _live(P, t, seed, quiet=(), breath=1.0, shift=1.0, phase=None):
    """The rig's alive(); no chance blink inside the spans `quiet` (beats that the eyes carry), nor
    while the eyes are shut or an acted blink runs. phase: the breath's own phase in breaths (_breaths:
    panting, a sleeper's slow breath); None = the rig's resting rate. (alive() multiplies its rate by the
    time, so a rate that CHANGES with time must never be given to it: the phase would jump on every frame.)"""
    bl = _quiet(t, quiet)
    if bl and (P["eye"] < 0.2 or P["blink"] > 0.02):
        bl = 0.0
    if phase is None:
        return alive(P, t, seed, breath=breath, blink=bl, shift=shift)
    return alive(alive(P, phase, seed, breath=breath, blink=0.0, shift=0.0, rate=1.0), t, seed, breath=0.0, blink=bl, shift=shift)


_REST_RATE = 0.27                        # alive()'s breaths a second


def _breaths(t, t0, t1, n, shape="s"):
    """The phase (in breaths) of a breath that runs at the resting rate outside t0..t1 and makes n more
    breaths between them ("s": most of them in the middle; "o": most at the start: a pant dying down).
    Continuous; with a whole n it is the resting phase again afterwards, so the hold that follows is the
    plain alive()."""
    u = _c((t - t0) / (t1 - t0))
    return _REST_RATE * t + n * (_sm(u) if shape == "s" else 1.0 - (1.0 - u) ** 2)


def _hand_b(P, which="f"):
    """A hand of a pose in body units from its ground point, as seen (after rot)."""
    J = solve(P)
    p = J["ha_" + which]
    c_, s_ = math.cos(P["rot"]), math.sin(P["rot"])
    return (float(p[0] * c_ + p[1] * s_), float(-p[0] * s_ + p[1] * c_))


def _joint_b(P, key):
    p = solve(P)[key]
    return (float(p[0]), float(p[1]))


def _w(pb, x, y, h, face):
    """Body units (forward, up) from a ground point -> world."""
    return (x + face * h * pb[0], y - h * pb[1])


def _b(pw, x, y, h, face):
    """World -> body units from a ground point."""
    return ((pw[0] - x) / (face * h), (y - pw[1]) / h)


def _aimed(P, x, y, h, face, f=None, b=None):
    """The pose with its near and / or far hand on WORLD points (a key pose that a pin will hold)."""
    if f is not None:
        P = aim_hand(P, "f", _b(f, x, y, h, face))
    if b is not None:
        P = aim_hand(P, "b", _b(b, x, y, h, face))
    return P


def _eyes(P, x, y, h, face, target, k=1.0, head=0.3):
    """Aim the eyes (and a little the head) of a profile pose at a world point: the eye line."""
    hx, hy = _head_q(P)
    dx = (target[0] - (x + face * h * hx)) * face
    dy = (y - h * hy) - target[1]
    d = math.hypot(dx, dy) + 1e-6
    ux, uy = dx / d, dy / d
    lx, ly = P["look"]
    tx = 0.36 + 0.22 * max(0.0, ux) - 0.55 * max(0.0, -ux)
    ty = max(-0.9, min(0.9, 1.05 * uy))
    gx, gy = P["gaze"]
    return P.but(look=(lx + (tx - lx) * k, ly + (ty - ly) * k), gaze=(gx + (0.6 * ux - gx) * k, gy + (0.6 * uy - gy) * k),
                 neck=P["neck"] - head * k * 0.45 * (uy - 0.15))


# --------------------------------------------------------------------------
# journeys: walks and runs with planted feet, planned once
# --------------------------------------------------------------------------
def _cyc(fn, ph, q, m):
    """A cycle pose with its step length scaled by q (the stance foot still does not slide)."""
    P, adv = fn(ph) if fn is run else fn(ph, m)
    return P.but(ff=(P["ff"][0] * q, P["ff"][1]), fb=(P["fb"][0] * q, P["fb"][1])), adv * q


def _lead(ph):
    """The foot that is in front and planted at a contact (ph a multiple of 0.5)."""
    return "ff" if int(round(ph * 2.0)) % 2 == 0 else "fb"


class _Gait:
    """A journey: phases (t_a, t_b, kind, data), each giving a pose and how far the body has advanced
    (body units) since the journey began. at(t) -> (pose, world x, air) with air = body units above
    the ground (jumps)."""
    __slots__ = ("x0", "x1", "face", "h", "ts", "ph", "base", "t0", "t1", "rest0", "rest", "q")

    def at(self, t):
        if t <= self.t0:
            return self.rest0, self.x0, 0.0
        if t >= self.t1:
            return self.rest, self.x1, 0.0
        i = bisect_right(self.ts, t) - 1
        ta, tb, kind, d = self.ph[i]
        u = (t - ta) / (tb - ta)
        air = 0.0
        if kind == 0:                                # a step between two poses, one foot planted
            w = u * u if d[4] == 0 else (1.0 - (1.0 - u) ** 2 if d[4] == 1 else u)
            P, dx = _step(d[0], d[1], w, d[2], d[3])
        elif kind == 1:                              # a stretch of a cycle
            P, adv = _cyc(d[0], d[2] + (d[3] - d[2]) * u, d[1], d[4])
            dx = adv - d[5]
        else:                                        # a jump: take-off pose, apex pose, landing pose
            w1, w2 = _sm(u / 0.36), _sm((u - 0.56) / 0.44)
            P = mixp(mixp(d[0], d[1], w1), d[2], w2)
            dx = d[3] * u
            air = d[4] * 4.0 * u * (1.0 - u)
        return P, self.x0 + self.face * self.h * (self.base[i] + dx), air

    def x_at(self, t):
        return self.at(t)[1]


def _plan(spec, h, face, t0, q, m_lift=0.05):
    """Lay a journey out for step-length factor q. spec items:
    ("out", rest0, dur, fn, m): a step out of a standing pose into the cycle's first contact;
    ("cyc", fn, m, dph, dur): a stretch of the cycle (from the phase it is in);
    ("fly", dur, height, apex pose, land phase): a jump out of the cycle, landing in a contact;
    ("sw", fn, m, dur): one step from this cycle's contact into another cycle's contact;
    ("in", rest, dur): the last step into a standing pose.
    Returns (phases, bases, total advance in body units, end time, first pose, last pose)."""
    t, ph, base = t0, 0.0, 0.0
    fn, m, speed = None, 0.0, 0.0
    out, bases = [], []
    first = last = None
    for it in spec:
        kind = it[0]
        if kind == "out":
            fn, m = it[3], it[4]
            b = _cyc(fn, 0.0, q, m)[0]
            D = _ankle_x(it[1], "fb") - _ankle_x(b, "fb")
            out.append((t, t + it[2], 0, (it[1], b, "fb", m_lift, 0)))
            first = it[1] if first is None else first
            ph, dur = 0.0, it[2]
            speed = 2.0 * D / dur
        elif kind == "cyc":
            fn, m = it[1], it[2]
            a0, a1 = _cyc(fn, ph, q, m)[1], _cyc(fn, ph + it[3], q, m)[1]
            out.append((t, t + it[4], 1, (fn, q, ph, ph + it[3], m, a0)))
            if first is None:
                first = _cyc(fn, ph, q, m)[0]
            D, dur = a1 - a0, it[4]
            ph += it[3]
            speed = D / dur
        elif kind == "fly":
            Pa, Pb = _cyc(fn, ph, q, m)[0], _cyc(fn, it[4], q, m)[0]
            D, dur = speed * it[1], it[1]
            out.append((t, t + dur, 2, (Pa, it[3], Pb, D, it[2])))
            ph = it[4]
        elif kind == "sw":
            a = _cyc(fn, ph, q, m)[0]
            lead = _lead(ph)
            fn, m = it[1], it[2]
            ph = 0.5 if lead == "ff" else 0.0
            b = _cyc(fn, ph, q, m)[0]
            D, dur = _ankle_x(a, lead) - _ankle_x(b, lead), it[3]
            out.append((t, t + dur, 0, (a, b, lead, m_lift, 2)))
            speed = D / dur
        else:                                        # "in"
            a = _cyc(fn, ph, q, m)[0]
            lead = _lead(ph)
            D, dur = _ankle_x(a, lead) - _ankle_x(it[1], lead), it[2]
            out.append((t, t + dur, 0, (a, it[1], lead, m_lift, 1)))
            last = it[1]
        bases.append(base)
        base += D
        t += dur
    if last is None:
        last = _cyc(fn, ph, q, m)[0]
    return out, bases, base, t, first, last


def _journey(spec, h, t0, x0=None, x1=None, face=None, q=None, m_lift=0.05) -> _Gait:
    """Plan a journey. Give x0 and x1 (the step length adapts: q is solved) or one end and q (the
    other end follows); face: +1 / -1 when only one end is given."""
    if x0 is not None and x1 is not None:
        face = 1 if x1 >= x0 else -1
        d1, d2 = _plan(spec, h, face, t0, 1.0, m_lift)[2], _plan(spec, h, face, t0, 2.0, m_lift)[2]
        q = 1.0 + (abs(x1 - x0) / h - d1) / (d2 - d1)
    ph, bases, total, t1, first, last = _plan(spec, h, face, t0, q, m_lift)
    G = _Gait()
    if x0 is None:
        x0 = x1 - face * h * total
    G.x0, G.x1 = x0, x0 + face * h * total
    G.face, G.h, G.ph, G.base, G.t0, G.t1, G.q = face, h, ph, bases, t0, t1, q
    G.ts = [p[0] for p in ph]
    G.rest0, G.rest = first, last
    return G


def stand_on(P: Pose, x: float, face: int, h: float, ground=None, y: float = FLOOR, air: float = 0.0):
    """Stand a pose on a ground function: returns (pose with each foot on the ground under it, world
    y of the ground point). ground(x) -> world y takes a float or an array (hills.ground_y; the
    curve given to ground_line); None = the flat line at y. air: body units the figure is in the air
    (a jump: the feet are left as they are). On a slope the downhill leg is longer, the uphill knee
    bends: both feet stay on the line."""
    if ground is None:
        return P, y - air * h
    fx, bx = P["ff"], P["fb"]
    xs = np.array([x, x + face * h * fx[0], x + face * h * bx[0]])
    ys = np.asarray(ground(xs), dtype=np.float64)
    if ys.shape != (3,):
        ys = np.array([float(ground(float(v))) for v in xs])
    y0 = float(ys[0])
    if air > 0.02:
        return P, y0 - air * h
    k = 1.0 - air / 0.02 if air > 0.0 else 1.0
    return P.but(ff=(fx[0], fx[1] + k * (y0 - ys[1]) / h), fb=(bx[0], bx[1] + k * (y0 - ys[2]) / h)), y0 - air * h


_on_ground = stand_on


def _gy(ground, x, y=FLOOR):
    return y if ground is None else float(ground(float(x)))


def _hand_of(a, which):
    """World point of a hand of an Act that is not pinned (one solve)."""
    return _pt(pose_joints(a.pose, a.x, a.y, a.h, a.face)["ha_" + which])


# --------------------------------------------------------------------------
# s03 (70.7 to about 87): the far friend at the right of the wide frame
# --------------------------------------------------------------------------
_ARM = 0.322                             # a nearly straight arm (shoulder to hand, body units)


def _swing(P, th, which="f", k=1.0, body=1.0):
    """P with one arm held out sideways and up, nearly straight, at the angle th from the vertical
    (the figure is turned toward us: a raised arm must show BESIDE the big head, never behind it),
    the whole body going with it a little (what makes a wave read from far away)."""
    if k <= 0.0:
        return P
    key = "h" + which
    hx, hy = P[key]
    hz = P[key + "z"]
    ty, tz = _ARM * math.cos(th), _ARM * math.sin(th)
    px, py = P["pel"]
    s = (th - 0.8) * body * k * (1.0 if which == "f" else -1.0)
    return P.but(**{key: (hx + (0.0 - hx) * k, hy + (ty - hy) * k), key + "z": hz + (tz - hz) * k, "e" + which: P["e" + which] * (1.0 - k) + 0.3 * k},
                 roll=P["roll"] - 0.16 * s, tilt=P["tilt"] - 0.10 * s, pz=P["pz"] - 0.012 * s, pel=(px, py + 0.008 * abs(s)),
                 sway=P["sway"] + 0.5 * s)


# three-quarter toward us, calling to the left: the outer arm waves, the inner hand is at the mouth
_F_WAVE = F_CALL.but(turn=0.72, open=1.0, lean=0.06, hf=(0.0, 0.22), hfz=0.23, ef=0.3, hb=(0.115, 0.085), look=(0.42, 0.20),
                     ff=(-0.03, 0.0), fb=(0.03, 0.0), ffz=0.02, fbz=0.02, sway=0.2)
_F_BOTH = _F_WAVE.but(turn=0.85, hb=(0.0, 0.25), hbz=0.20, eb=0.3, neck=-0.28, look=(0.30, 0.34), mouth=1.1, mopen=0.6, joy=0.5,
                      lift=0.6, blush=0.8, hair=1.0)                              # both arms up: it has been seen
_F_DIP = F_STAND.but(turn=0.8, open=1.0, pel=(0.0, 0.372), lean=0.10, bend=0.18, hf=(0.02, -0.20), hb=(0.02, -0.20), hfz=0.06,
                     hbz=0.06, ff=(-0.03, 0.0), fb=(0.03, 0.0), ffz=0.03, fbz=0.03, mouth=0.9, mopen=0.4, lift=0.5, eye=1.15,
                     look=(0.3, 0.1))                                             # the dip before the big hop
_F_BECK = F_STAND.but(turn=0.3, lean=0.10, neck=-0.12, look=(0.50, 0.12), mouth=0.9, mopen=0.3, joy=0.3, hf=(0.26, 0.02), ef=-1.0,
                      hb=(-0.03, -0.27), ff=(-0.06, 0.0), fb=(0.06, 0.0), blush=0.6, hair=0.9)     # "come": the arm held out
_F_REST = F_STAND.but(turn=0.3, neck=-0.08, look=(0.44, 0.08), mouth=0.75, blush=0.5)
_F_GO = Pose(lean=0.04, neck=-0.05, look=(0.40, 0.08), mouth=0.7, hair=0.8, blush=0.5, hf=(0.0, -0.30), hb=(0.04, -0.30),
             ff=(-0.012, 0.0), fb=(0.022, 0.0))                                   # facing right, about to walk off


@lru_cache(maxsize=8)
def _s03_plan(t_on, t_seen, t_last, t_go, h, x):
    tr = _Track(_F_WAVE,
                (t_seen, 0.26, _F_DIP, "body"), (t_seen + 0.28, 0.30, _F_BOTH, "body"),
                (t_seen + 3.1, 0.5, _F_BECK, "hand"), (t_last - 2.3, 0.6, _F_REST, "soft"),
                (t_last - 0.36, 0.34, _F_WAVE.but(mopen=0.3, hb=(0.03, -0.27)), "hand"),
                (t_last + 0.95, 0.4, _F_REST, "soft"), (t_go, 0.56, _mirror(_F_GO), "turn"))
    tw = beat_after(t_go + 0.56)
    G = _journey((("out", _F_GO, BEAT, walk, 0.85), ("cyc", walk, 0.85, 8.0, 16 * BEAT)), h, tw, x0=x, face=1, q=1.0)
    return tr, G, tw


def s03_friend(t: float, x: float = ST.FRIEND_FAR_1, y: float = FLOOR, h: float = 293.0, t_on: float = 70.9,
               t_seen: float = 75.3, t_last: float = 82.76, t_go: float = 84.3) -> Act:
    """The far friend of the first chorus, at the right of the wide frame (about 80 px tall at
    story.WIDE_ZOOM): it draws itself on from t_on (0.7 s), waving with its whole arm, a sweep a
    beat, the other hand at its mouth: calling. At t_seen (the child has turned round) it hops with
    both arms up, then waves with both; later it holds an arm out (come); at t_last it waves once
    more, at t_go it turns round and walks off to the right, a step a beat.
    x, y: its ground point; it faces left. Returns an Act (face -1; +1 once it walks away).
    num: call (0..1: its mouth as it calls), seen (0..1 from t_seen), point (0..1 from t_go + 1.4
    over 2 s: the scene's cue to let it become a point of light; Act.a is 1 - 0.85 * point), hop
    (world units off the ground). pts: feet (where the amber line starts)."""
    tr, G, tw = _s03_plan(t_on, t_seen, t_last, t_go, h, x)
    point = _ramp(t, t_go + 1.4, t_go + 3.4)
    num = dict(call=0.0, seen=_ramp(t, t_seen, t_seen + 0.5), point=point, hop=0.0)
    if t >= tw:
        P, fx, _ = G.at(t)
        P0, fx0, _ = G.at(t - _DT)
        P = _follow(P.but(mouth=0.7, blush=0.5), P0, (fx - fx0) / h, 0.0, 0.8)
        return Act(P, fx, y, 1, None, h, "friend", SF, a=1.0 - 0.85 * point, pts=dict(feet=(fx, y)), num=num)

    def raw(tt):
        P = tr.at(tt)
        s = math.sin(2.0 * math.pi * (tt - beat(0)) / (2.0 * BEAT) + HALF_PI)        # an extreme on every beat
        k1 = (1.0 - _ramp(tt, t_seen - 0.05, t_seen + 0.2)) + _ramp(tt, t_last - 0.3, t_last) * (1.0 - _ramp(tt, t_last + 0.85, t_last + 1.25))
        if k1 > 0.0:                                 # the whole-arm wave, out at its side
            P = _swing(P, 0.90 + 0.40 * s, "f", k1)
        k2 = _ramp(tt, t_seen + 0.5, t_seen + 0.8) * (1.0 - _ramp(tt, t_seen + 2.9, t_seen + 3.3))
        if k2 > 0.0:                                 # both arms, a little faster
            s2 = math.sin(2.0 * math.pi * (tt - beat(0)) / BEAT)
            P = _swing(_swing(P, 0.72 + 0.34 * s2, "f", k2, 0.5), 0.72 - 0.34 * s2, "b", k2, 0.5)
        k3 = _ramp(tt, t_seen + 3.5, t_seen + 3.8) * (1.0 - _ramp(tt, t_last - 2.4, t_last - 2.0))
        if k3 > 0.0:                                 # come: the held-out arm scoops toward itself, once a beat
            u = ((tt - beat(0)) / BEAT) % 1.0
            g = _sm(u / 0.45) * (1.0 - _sm((u - 0.55) / 0.45))
            P = P.but(hf=(P["hf"][0] - 0.13 * g * k3, P["hf"][1] + 0.05 * g * k3), lean=P["lean"] - 0.03 * g * k3)
        return P

    P = _follow(raw(t), raw(t - _DT), k=0.8)
    # calling: a breath, then the mouth wide, twice a bar, until it has been seen
    if t < t_seen:
        u = ((t - beat(0)) / (2.0 * BEAT)) % 1.0
        call = _sm(u / 0.18) * (1.0 - _sm((u - 0.55) / 0.3))
        num["call"] = call
        P = P.but(mopen=0.25 + 0.65 * call, lean=P["lean"] + 0.04 * call, neck=P["neck"] - 0.06 * call)
    # it jumps to be seen: a small hop on every beat while it waves (it lands on the beat), a big one when the child turns
    kh = (_ramp(t, t_on + 0.7, t_on + 1.0) * (1.0 - _ramp(t, t_seen - 0.35, t_seen - 0.05))
          + 0.8 * _ramp(t, t_seen + 0.9, t_seen + 1.2) * (1.0 - _ramp(t, t_seen + 2.6, t_seen + 3.0))
          + _ramp(t, t_last - 0.4, t_last - 0.1) * (1.0 - _ramp(t, t_last + 0.7, t_last + 0.95)))
    u = ((t - beat(0)) / BEAT) % 1.0
    v = (u - 0.24) / 0.76
    air = 0.085 * kh * (4.0 * v * (1.0 - v) if v > 0.0 else 0.0)
    sq = kh * (math.sin(math.pi * u / 0.24) if u < 0.24 else 0.0)                    # the landing: the knees give
    air += 0.15 * _bell(t, t_seen + 0.30, 0.50)
    if kh > 0.0:
        px, py = P["pel"]
        P = P.but(pel=(px, py - 0.022 * sq), bend=P["bend"] + 0.10 * sq, bob=max(-1.0, min(1.0, P["bob"] + 0.8 * kh * math.cos(2.0 * math.pi * v) * (1.0 if v > 0.0 else 0.0) - 0.6 * sq)),
                  af=P["af"] - 0.7 * min(1.0, air / 0.05), ab=P["ab"] - 0.7 * min(1.0, air / 0.05))
    num["hop"] = air * h
    busy = t < t_seen + 3.3 or t_last - 0.4 < t < t_last + 1.4 or t >= t_go
    P = _live(P, t, SF, ((t_seen - 0.2, t_seen + 1.0),), breath=0.6 if busy else 1.4, shift=0.0 if busy else 1.0)
    return Act(P, x, y - air * h, -1, None, h, "friend", SF, draw=_seg(t, t_on, t_on + 0.7), lift=air * h,
               pts=dict(feet=(x, y)), num=num)


# --------------------------------------------------------------------------
# s06 (138.20 to 158.86): the storm at its worst; the friend comes through it and sits down beside the child
# --------------------------------------------------------------------------
_DXS = 0.145        # a child sitting on the ground has its feet this far in front of its ground point (body units)

# the child: back view (drawn from the sitting ground point: its feet stay where they are when it sits down)
_C_BACK = rebase(BACK_STAND.but(pel=(0.0, 0.388), bend=0.36, neck=0.30, hair=0.04), -_DXS, 0.0)
_C_FL1 = rebase(BACK_STAND.but(pel=(0.0, 0.338), bend=0.68, neck=0.58, lean=0.12, hf=(0.02, -0.255), hb=(0.02, -0.255),
                               hfz=-0.012, hbz=-0.012, hair=0.0), -_DXS, 0.0)                  # hit 1: the knees give, the head ducks
_C_FL1S = rebase(BACK_STAND.but(pel=(0.0, 0.352), bend=0.60, neck=0.50, lean=0.10, hf=(0.02, -0.27), hb=(0.02, -0.27),
                                hfz=-0.008, hbz=-0.008, hair=0.0), -_DXS, 0.0)
_C_SQUAT0 = Pose(pel=(0.030, 0.170), lean=0.34, bend=0.84, neck=0.58, look=(0.26, -0.85), hf=(0.17, -0.10), hb=(0.12, -0.12),
                 ff=(0.165, 0.0), fb=(0.125, 0.0), open=0.35, front=1.0, eye=0.15, lid=1.0, brow=0.9, mouth=-0.5, hair=0.0)
_C_SQUAT = _C_SQUAT0.but(pel=(0.038, 0.198), lean=0.28, bend=0.74, neck=0.50, eye=0.3, brow=0.8)   # hit 2: down on its heels
# sitting, the forehead on the knees (the head stays over the knees: the space before the shins is free for a hand)
_SITB = dict(lean=0.10, bend=0.62, neck=0.58)
_C_PLOP = SIT_HUG.but(pel=(-0.066, 0.048), lean=0.13, bend=0.74, neck=0.66, look=(0.25, -0.9), eye=0.0, brow=0.9, hair=0.0,
                      mouth=-0.5)
_C_SITLOW = SIT_HUG.but(look=(0.26, -0.85), eye=0.25, brow=0.8, mouth=-0.45, hair=0.0, **_SITB)     # hit 3: sitting
_C_WARY = _C_SITLOW.but(bend=0.66, neck=0.62, tilt=-0.05, gaze=(0.6, 0.1), eye=0.42, brow=0.85)     # someone is there
_C_PEEK = SIT_HUG.but(lean=0.12, bend=0.55, neck=0.40, look=(0.36, -0.50), gaze=(0.5, -0.5), eye=0.62, brow=0.62, hair=0.05)
_C_REACH1 = _C_PEEK.but(hf=(0.262, -0.092), lean=0.17, neck=0.32, look=(0.38, -0.42), eye=0.7)   # the hand comes out half way
_C_BACKOFF = _C_REACH1.but(hf=(0.236, -0.088), lean=0.14, neck=0.30, gaze=(0.6, 0.45), brow=0.78, eye=0.75)   # and stops
_C_TAKE = SIT_HUG.but(lean=0.28, bend=0.50, neck=0.26, look=(0.38, -0.32), gaze=(0.4, -0.4), eye=0.78, brow=0.5,
                      hf=(0.29, -0.07), hair=0.15, mouth=-0.2)
_C_FACE = SIT_LIFT.but(look=(0.50, 0.12), gaze=(0.5, 0.2), neck=-0.12, mopen=0.12, eye=1.0, lift=0.4, lid=0.5, hair=0.5,
                       mouth=-0.05, hf=(0.29, -0.07))                                             # head lifted: at the friend
_C_UP = SIT_LIFT.but(look=(0.40, 0.84), gaze=(0.25, 1.0), neck=-0.46, hf=(0.29, -0.07), lid=0.22, eye=1.22, lift=0.8,
                     mopen=0.3, mouth=0.05, hair=0.62)                                            # looking up (hand-off B6)

# the friend
_F_FEET = dict(ff=(0.03, 0.0), fb=(0.085, 0.0))        # the crouch's feet: it stops on them, so it can go straight down
_F_BRAKE = F_STAND.but(pel=(0.035, 0.392), lean=-0.12, bend=0.06, neck=0.12, look=(0.42, -0.35), mouth=0.1, mopen=0.35,
                       lift=0.45, brow=0.3, hf=(0.11, -0.23), hb=(0.13, -0.19), sway=-0.8, **_F_FEET)
_F_SEE = F_STAND.but(pel=(0.045, 0.398), lean=0.15, bend=0.14, neck=0.26, look=(0.42, -0.5), gaze=(0.3, -0.6), mouth=0.15,
                     brow=0.4, hf=(0.03, -0.29), hb=(0.06, -0.28), **_F_FEET)
_F_CR = F_CROUCH.but(neck=0.04, look=(0.48, -0.25), gaze=(0.4, -0.4), mouth=0.3, brow=0.3)
_F_OFF = F_OFFER.but(lean=0.14, neck=-0.20, look=(0.50, -0.15), gaze=(0.4, -0.3), mouth=0.55, lift=0.3)
_F_WAIT = _F_OFF.but(tilt=0.08, neck=-0.10, mouth=0.62, gaze=(0.45, -0.2))
_F_GLAD = _F_OFF.but(look=(0.50, 0.0), gaze=(0.4, 0.0), mouth=1.0, joy=0.35, lift=0.4, blush=0.7, neck=-0.2)
_F_UP = _F_GLAD.but(look=(0.40, 0.82), gaze=(0.2, 1.0), neck=-0.50, joy=0.1, mouth=0.7, mopen=0.2, lean=0.16)   # B6
_CR_B = _hand_b(_F_CR, "f")                       # the friend's near hand on its knee
_BACKOFF_B = _hand_b(_C_BACKOFF, "f")
_GIVE = (104.0, -74.0)                           # the open hand, from the child's ground point: before its shins, clear of its head
_JOIN = (100.0, -78.0)                           # the joined hands


def _away(ph):
    """The child walking away in back view, lower than in the first chorus."""
    P, adv = walk_away(ph, 0.0)
    return P.but(pel=(P["pel"][0], P["pel"][1] - 0.012), bend=P["bend"] + 0.12, neck=P["neck"] + 0.08, hair=0.03), adv


@lru_cache(maxsize=8)
def _s06_plan(hits, t_turn, step, t_enter, t_run, t_offer, t_take, t_lift, t_up, xf, hf):
    h1, h2, h3 = hits
    tw = t_turn + 0.55
    turn = _Track(STOPPED, (t_turn, 0.55, _C_BACK, "turn"))
    pw = mixp(_C_BACK, rebase(_away((h1 - tw) / (2.0 * step))[0], -_DXS, 0.0), 1.0)
    n = max(1, int(round((t_run - t_enter) / BEAT)))
    G = _journey((("cyc", walk, 0.5, 0.5 * n, n * BEAT), ("sw", run, 0.0, 0.26), ("cyc", run, 0.0, 0.5, 0.24),
                  ("in", _F_BRAKE, 0.26)), hf, t_run - n * BEAT, x1=xf, face=-1, q=1.0)
    ta = G.t1
    child = _Track(pw, (h1, 0.15, _C_FL1, "hit"), (h1 + 0.2, 0.7, _C_FL1S, "mix"),
                   (h2, 0.34, _C_SQUAT0, "turn", dict(hop=0.5)), (h2 + 0.36, 0.5, _C_SQUAT, "mix"),
                   (h3, 0.22, _C_PLOP, "hit"), (h3 + 0.26, 0.8, _C_SITLOW, "mix"),
                   (ta + 0.25, 0.5, _C_WARY), (t_offer + 0.3, 0.5, _C_PEEK), (t_take - 1.2, 0.45, _C_REACH1),
                   (t_take - 0.72, 0.26, _C_BACKOFF, "mix"), (t_take - 0.42, 0.42, _C_TAKE, "mix"),
                   (t_lift, 1.25, _C_FACE, "act", dict(blink=1.0)), (t_up - 0.68, 0.7, _C_UP))
    friend = _Track(_F_BRAKE, (ta, 0.26, _F_SEE, "mix"), (ta + 0.3, 0.5, _F_CR), (t_offer - 0.45, 0.45, _F_OFF),
                    (t_offer + 0.9, 0.5, _F_WAIT, "mix"), (t_take + 0.12, 0.45, _F_GLAD), (t_up - 0.4, 0.65, _F_UP))
    return turn, tw, child, G, friend


def s06(t: float, x: float = ST.X5, y: float = FLOOR, d: float = 180.0, hits=ST.HITS_2, t_turn: float = 138.26,
        step: float = 0.5, t_enter: float = 147.265, t_run: float = 150.265, t_offer: float = 152.36,
        t_take: float = 154.40, t_lift: float = 154.84, t_up: float = 157.01, hc: float = HC, hf: float = HF) -> Duet:
    """The second chorus. The child turns its back and walks away (in place: the camera pulls back),
    a step every `step` seconds, lower and paler; stops on the first hit, shrinks under each of the
    three and ends sitting, its forehead on its knees. The friend walks in from the right from
    t_enter (a step a beat, leaning into the rain), runs the last steps from t_run, stops short,
    crouches, holds out an open hand (it is there at t_offer) and waits; the child's hand comes out,
    stops, and takes it (t_take); the friend's free hand brushes twice over the crown of the bowed head
    (the loops off it: num brush 0..2); the child lifts its head (t_lift) and looks at the friend; both
    look up (t_up).
    x, y: the child's ground point (it sits where it stood); d: the friend crouches at x + d.
    pts: hands (the friend's open hand from t_offer, then the joined hands; None before), sky (where
    they look up to). num: away (body units walked into the depth), cower (0..1: how far down the
    hits have pressed it), warm (0..1: amber rubbing off on the child's hand and arm), joined (0/1).
    The child's Act.a is its pressure (it pales as it walks away, comes back from the hand on); the
    friend's comes up over its first 0.6 s (it walks out of the rain; it does not pop in)."""
    hits = tuple(hits)
    if t >= t_up + 1.2:
        return hold_B6(t, x, y, d, hc, hf)
    xf = x + d
    turn, tw, ctrack, G, ftrack = _s06_plan(hits, t_turn, step, t_enter, t_run, t_offer, t_take, t_lift, t_up, xf, hf)
    h1 = hits[0]
    k = 0.5 * (d - 180.0)
    give = (x + _GIVE[0] + k, y + _GIVE[1])
    H = _lerp(give, (x + _JOIN[0] + k, y + _JOIN[1] + 4.0 * _bell(t, t_take - 0.03, 0.5)), _ramp(t, t_take, t_take + 0.5))
    sky = _b6_sky(x, y, d)

    # ---- the child
    away = 0.0
    if t < tw:
        Pc = P0 = turn.at(t)
    elif t < h1:
        Pw, away = _away((t - tw) / (2.0 * step))
        Pc = P0 = mixp(_C_BACK, rebase(Pw, -_DXS * _seg(t, tw, h1), 0.0), _ramp(t, tw, tw + 0.5 * step))
    else:
        Pc = ctrack.at(t)
        P0 = ctrack.at(t - _DT)
        away = _away((h1 - tw) / (2.0 * step))[1]
        Pc = _follow(Pc, P0, k=0.7)
    joined = 1.0 if t >= t_take else 0.0
    gc = None
    if t >= t_take - 0.42:
        gc = {"f": H if joined else _lerp(_w(_BACKOFF_B, x, y, hc, 1), H, _out((t - (t_take - 0.42)) / 0.42, 2.0))}

    # ---- the friend
    Pf, gf, fx = None, None, xf
    if t >= G.t1:
        Pf = _follow(ftrack.at(t), ftrack.at(t - _DT), k=0.8)
        if t >= t_offer - 0.45:
            gf = {"f": H if t >= t_offer else _lerp(_w(_CR_B, xf, y, hf, -1), give, _sm((t - (t_offer - 0.45)) / 0.45))}
        # eye lines: at the child's head; at its own open hand while it waits; up
        wf = _ramp(t, G.t1 + 0.3, G.t1 + 0.8) * (1.0 - _ramp(t, t_up - 0.45, t_up + 0.1))
        wf *= 1.0 - 0.6 * _ramp(t, t_offer - 0.4, t_offer) * (1.0 - _ramp(t, t_take - 1.0, t_take - 0.5))
        if wf > 0.0:
            Pf = _eyes(Pf, xf, y, hf, -1, _w(_head_q(Pc), x, y, hc, 1), wf, head=0.15)
        wu = _ramp(t, t_up - 0.4, t_up + 0.25)
        if wu > 0.0:
            Pf = _eyes(Pf, xf, y, hf, -1, sky, wu, head=0.0)
        wc = _ramp(t, t_lift + 0.35, t_lift + 0.9) * (1.0 - _ramp(t, t_up - 0.68, t_up - 0.2))
        if wc > 0.0:
            Pc = _eyes(Pc, x, y, hc, 1, _w(_head_q(Pf), xf, y, hf, -1), wc, head=0.0)
        # its free hand brushes over the crown of the bowed head, twice (the loops off it), while it holds the hand
        if t_take + 0.10 < t < t_take + 1.16:
            hq = _w(_joint_b(Pc, "head"), x, y, hc, 1)

            def brush(tt, hq=hq):
                v = _c((tt - (t_take + 0.30)) / 0.62) * 2.0
                v = v - 1.0 if v > 1.0 else v
                w = _sm(v / 0.6) * (1.0 - _sm((v - 0.6) / 0.4))
                a_ = 0.50 + 0.70 * w                                            # round the rim, from before the crown to over it
                r_ = 0.155 * hc * (1.13 + 0.16 * math.sin(math.pi * _c((v - 0.6) / 0.4)))    # lifted on the way back
                return (hq[0] + r_ * math.cos(a_), hq[1] - r_ * math.sin(a_))

            Pf, gb = _pin(Pf, t, xf, y, hf, -1, ((t_take + 0.10, t_take + 0.32, t_take + 0.94, t_take + 1.16, "b", brush),))
            if gb:
                gf = dict(gf or {}, **gb)
    elif t >= G.t0:
        Pf, fx, _ = G.at(t)
        lean = 1.0 - _ramp(t, t_run - 0.1, t_run + 0.3)                # leaning into the rain, an arm up before its face
        Pf = Pf.but(lean=Pf["lean"] + 0.20 * lean + 0.06, neck=Pf["neck"] + 0.16 * lean,
                    hb=_lerp(Pf["hb"], (0.17, 0.06), 0.9 * lean), eb=Pf["eb"] + 2.0 * lean, eye=1.0 - 0.45 * lean,
                    brow=0.5 * lean, mouth=0.1, mopen=0.25 * (1.0 - lean), sway=0.5 + 0.4 * lean, lift=0.4 * (1.0 - lean))
    quiet = ((t_turn, tw + 0.2), (h1 - 0.2, hits[2] + 1.2), (t_take - 1.3, t_take + 0.3), (t_lift - 0.1, t_lift + 1.4),
             (t_up - 0.7, t_up + 0.3))
    low = _ramp(t, tw, tw + 1.0) * (1.0 - _ramp(t, t_take, t_take + 1.5))          # shallow breath while it is far gone
    Pc = _live(Pc, t, SC, quiet, breath=1.0 - 0.45 * low,
               shift=1.0 - _ramp(t, t_turn, tw) + 0.4 * _ramp(t, h1, h1 + 0.5) + 0.6 * _ramp(t, t_take, t_take + 1.0))
    a = 1.0 - 0.62 * _seg(t, tw, h1) + 0.62 * _ramp(t, t_take, t_up)
    child = Act(Pc, x, y, 1, gc, hc, "child", SC, a=a)
    friend = None
    if Pf is not None:
        if t >= G.t1:
            Pf = _live(Pf, t, SF, quiet, breath=1.6 - 0.6 * _ramp(t, t_offer - 0.5, t_offer + 0.5), shift=0.5)
        friend = Act(Pf, fx, y, -1, gf, hf, "friend", SF, a=_ramp(t, G.t0, G.t0 + 0.6))
    pts = dict(hands=H if t >= t_offer else None, sky=sky)
    num = dict(away=away, warm=_ramp(t, t_take, t_take + 1.6), joined=joined,
               cower=0.3 * _ramp(t, h1, h1 + 0.2) + 0.3 * _ramp(t, hits[1], hits[1] + 0.3) + 0.4 * _ramp(t, hits[2], hits[2] + 0.3),
               brush=_ramp(t, t_take + 0.30, t_take + 0.49) + _ramp(t, t_take + 0.61, t_take + 0.80))
    return Duet(child, friend, pts, num, "fc")



def _b6_sky(x, y, d):
    return (x + 0.5 * d + 20.0, y - 560.0)


def _b6_hands(x, y, d):
    return (x + _JOIN[0] + 0.5 * (d - 180.0), y + _JOIN[1])


def hold_B6(t: float, x: float = ST.X5, y: float = FLOOR, d: float = 180.0, hc: float = HC, hf: float = HF) -> Duet:
    """The rest state of hand-off B6 (158.86): the child sitting on the ground at (x, y), head lifted,
    looking up; the friend crouched at x + d facing it, looking up; the child's near hand in the
    friend's near hand (pts["hands"]). Alive, not acting. pts: hands, sky (where they look)."""
    xf = x + d
    H, sky = _b6_hands(x, y, d), _b6_sky(x, y, d)
    Pc = _live(_C_UP, t, SC)
    Pf = _live(_eyes(_F_UP, xf, y, hf, -1, sky, 1.0, 0.0), t, SF, shift=0.5)
    return Duet(Act(Pc, x, y, 1, {"f": H}, hc, "child", SC), Act(Pf, xf, y, -1, {"f": H}, hf, "friend", SF),
                dict(hands=H, sky=sky), dict(away=0.0, warm=1.0, joined=1.0, cower=1.0, brush=2.0), "fc")


# --------------------------------------------------------------------------
# points that move, pins, looks
# --------------------------------------------------------------------------
class _Path:
    """A world point in time. keys: (t, (x, y)[, mode]) in order; between two keys the point moves
    with the mode of the later one: "s" smooth, "o" fast start (a pull, a drop), "i" slow start,
    "a" smooth with a small arc upward (a hand carried over). Before / after: the first / last."""
    __slots__ = ("ts", "keys")

    def __init__(self, *keys):
        self.keys = keys
        self.ts = [k[0] for k in keys]

    def __call__(self, t):
        i = bisect_right(self.ts, t) - 1
        if i < 0:
            return self.keys[0][1]
        if i >= len(self.keys) - 1:
            return self.keys[-1][1]
        a, b = self.keys[i], self.keys[i + 1]
        u = (t - a[0]) / (b[0] - a[0])
        m = b[2] if len(b) > 2 else "s"
        w = _sm(u) if m in "sa" else (_out(u, 2.6) if m == "o" else u * u)
        p, q = a[1], b[1]
        y = p[1] + (q[1] - p[1]) * w
        if m == "a":
            y -= 0.16 * math.hypot(q[0] - p[0], q[1] - p[1]) * math.sin(math.pi * w)
        return (p[0] + (q[0] - p[0]) * w, y)


def _pin(P, t, x, y, h, face, segs):
    """Hands held on world points. segs: (a0, a1, b0, b1, which, point): the hand `which` goes to the
    point over a0..a1, is held there, and leaves it over b0..b1 (point: (x, y) or a function of t).
    Returns (pose, grab): while a hand is on the way the pose itself is aimed; while it is held the
    point goes into grab (the rig then pins it exactly)."""
    grab = None
    J = None
    for a0, a1, b0, b1, which, pt in segs:
        if t <= a0 or t >= b1:
            continue
        w = (_sm((t - a0) / (a1 - a0)) if t < a1 else 1.0) * (1.0 - _sm((t - b0) / (b1 - b0)) if t > b0 else 1.0)
        p = pt(t) if callable(pt) else pt
        if w >= 0.9999:
            if grab is None:
                grab = {}
            grab[which] = p
            continue
        if J is None:
            J = solve(P)
        own = J["ha_" + which]
        bx, by = _b(p, x, y, h, face)
        lift = 0.018 * math.sin(math.pi * w)
        P = aim_hand(P, which, (own[0] + (bx - own[0]) * w, own[1] + (by - own[1]) * w + lift))
        J = None
    return P, grab


def _sumpull(t, times, dur=0.5):
    """How many pulls have been made (each eased over dur): the scene's `out` for gloom.unravel."""
    return sum(_out(_seg(t, tp, tp + dur), 2.2) for tp in times)


def _busy(t, times):
    """0..1: a pull is being made (the line taut: slack = 1 - busy)."""
    return max(_seg(t, tp - 0.1, tp + 0.15) * (1.0 - _seg(t, tp + 0.5, tp + 0.9)) for tp in times)


# --------------------------------------------------------------------------
# s07 (158.86 to 182.30): the bridge. Unravelling together; the drawing mended and let go; the fist
# opens; the line laid down; they stand
# --------------------------------------------------------------------------
S07_T = dict(pulls=(160.0, 161.9, 164.9, 167.9), offer=162.5, halves=163.3, tape=(165.63, 166.39), release=167.1,
             fist=173.5, fist2=175.0, lay=175.96, rise=178.45, stand=179.51, clasp=181.0, open=181.52)

# the friend sitting on the ground (it has fallen back on its bottom with the first pull; its feet stay where it crouched)
_F_SIT = Pose(pel=(-0.150, 0.056), lean=0.10, bend=0.26, neck=-0.10, look=(0.48, 0.0), eye=1.0, mouth=0.5, hf=(0.20, -0.10),
              hb=(0.17, -0.13), ff=(0.03, 0.0), fb=(0.085, 0.0), hair=0.7, open=0.5, front=1.0, blush=0.4)
_C_SIT = SIT_LIFT.but(lean=0.16, bend=0.22, neck=-0.08, look=(0.48, 0.10), gaze=(0.3, 0.0), eye=1.0, lid=0.5, lift=0.2,
                      brow=0.2, mouth=-0.08, mopen=0.0, hf=(0.215, -0.085), hb=(0.13, -0.11), hair=0.5)


@lru_cache(maxsize=4)
def _s07_plan(x, y, d, hc, hf, root, tape, T, ss):
    T = dict(T)
    p1, p2, p3, p4 = T["pulls"]
    xf = x + d
    k = 0.5 * (d - 180.0)

    def W(dx, dy):                                   # a point between the two, from the child's ground point
        return (x + dx + k, y + dy)

    def CE(P, target, kk=1.0, head=0.3):             # the child's eye line (set once, in the key pose)
        return _eyes(P, x, y, hc, 1, target, kk, head)

    def FE(P, target, kk=1.0, head=0.3):
        return _eyes(P, xf, y, hf, -1, target, kk, head)

    def up(p, n):                                    # n units up the line from p, toward where it leaves the mass
        dx, dy = root[0] - p[0], root[1] - p[1]
        m = math.hypot(dx, dy) + 1e-9
        return (p[0] + dx * n / m, p[1] + dy * n / m)

    H = _b6_hands(x, y, d)
    sky = _b6_sky(x, y, d)
    # every hand that goes to the line goes FORWARD, not up: an arm raised more than about 20 degrees crosses the big head
    END = W(102.0, -128.0)                           # where the loose end hangs (its tip)
    G1, A1 = W(100.0, -160.0), W(166.0, -92.0)       # the friend's first grip; where the first pull ends (its lap)
    G2, A2 = W(104.0, -132.0), W(180.0, -84.0)
    O = W(106.0, -92.0)                             # the end held out to the child
    A3 = W(66.0, -78.0)                              # the child's own small pull
    KN = W(124.0, -16.0)                             # the line dropped on the ground between them
    TT = W(98.0, -112.0)                             # held ready for the child's hands
    A4 = W(94.0, -66.0)                              # the pull together
    K2 = W(58.0, -70.0)                              # the line in the child's lap
    GND = W(78.0, -6.0)
    chead = _w(_head_q(_C_SIT), x, y, hc, 1)
    fhead = _w(_head_q(_F_SIT), xf, y, hf, -1)
    drawing = (x + 300.0, y - 640.0)                 # where the mended drawing ends up in the sky
    hill = (x + 900.0, y - 260.0)

    # ---- the points that move
    LF = _Path((p1 - 0.05, G1), (p1 + 0.22, A1, "o"), (p1 + 0.62, A1), (p1 + 1.35, G2, "a"), (p2 - 0.36, G2),
               (p2 - 0.04, _add(G2, -5.0, -6.0)), (p2 + 0.24, A2, "o"), (p2 + 0.56, A2), (T["offer"] + 0.55, O, "a"),
               (T["halves"] + 0.25, O), (T["halves"] + 0.75, _add(O, 4.0, 12.0)), (p3 - 0.55, _add(O, 4.0, 12.0)), (p3 - 0.2, O),
               (p3 + 0.1, O), (p3 + 0.62, KN), (T["release"] + 0.15, KN), (T["release"] + 0.50, up(TT, 40.0), "a"))
    LC = _Path((p3 - 0.05, O), (p3 + 0.18, A3, "o"), (p3 + 0.28, A3), (p3 + 0.62, KN), (T["release"] + 0.15, KN), (p4 - 0.12, TT),
               (p4 + 0.24, A4, "o"), (p4 + 0.75, A4), (p4 + 1.7, K2), (T["fist2"], K2), (T["fist2"] + 0.26, GND, "i"))
    # the two halves (where the left and the right half are held): out of the jumper, apart, pressed to
    # the chest while one hand pulls, held out together to be taped, lifted, let go
    th = T["halves"]
    # the sheet is held LOW, on the child's knees, below both heads (between two big heads 180 apart there is no room for it)
    gx, gy = 62.0 * ss, 30.0 * ss                    # where a hand holds a half: from the middle of the sheet (things._GRIP)
    CH = W(30.0, -50.0)                              # out from under the jumper, at its lap (below the bowed head)
    S_KN = W(70.0, -24.0 - 56.0 * ss)                 # ... as the child first holds them
    S_OUT = W(92.0, -26.0 - 56.0 * ss)                # ... held out to the friend to be taped
    S_UP = W(74.0, -184.0)                           # lifted, about to be let go
    apart = 9.0
    HL = _Path((th + 0.30, _add(CH, -6.0, 0.0)), (th + 0.80, _add(S_KN, -gx - apart, gy)), (p3 + 0.24, _add(S_KN, -gx - apart, gy)),
               (p3 + 0.66, _add(S_OUT, -gx, gy)), (T["tape"][1] + 0.30, _add(S_OUT, -gx, gy)), (T["release"], _add(S_UP, -gx, gy)))
    HR = _Path((th + 0.30, _add(CH, 20.0, 2.0)), (th + 0.80, _add(S_KN, gx + apart, gy - 2.0)), (p3 + 0.24, _add(S_KN, gx + apart, gy - 2.0)),
               (p3 + 0.66, _add(S_OUT, gx, gy)), (T["tape"][1] + 0.30, _add(S_OUT, gx, gy)), (T["release"], _add(S_UP, gx, gy)))
    if tape is None:
        q = ss / 0.8
        tape = ((_add(S_OUT, -15.0 * q, -21.0 * q), _add(S_OUT, 15.0 * q, -28.0 * q)),
                (_add(S_OUT, -15.0 * q, 34.0 * q), _add(S_OUT, 15.0 * q, 39.0 * q)))
    (s0a, s0b), (s1a, s1b) = tape
    t0, t1 = T["tape"]
    TP = _Path((t0 - 0.02, s0a), (t0 + 0.24, s0b), (t0 + 0.34, _add(s0b, 6.0, -10.0)), (t1 - 0.06, _add(s1a, -2.0, -8.0), "a"), (t1, s1a),
               (t1 + 0.24, s1b), (t1 + 0.50, _add(s1b, 2.0, -3.0)))
    tf, tf2 = T["fist"], T["fist2"]
    FX = W(84.0, -132.0)                             # the fist held out before it, where it can look at it
    FIST = _Path((170.8, W(30.0, -100.0)), (171.5, FX, "a"), (tf - 0.26, FX), (tf - 0.04, _add(FX, -14.0, 8.0)),
                 (tf + 0.30, _add(FX, 22.0, -30.0), "o"), (tf + 0.75, _add(FX, 20.0, -22.0)), (tf + 1.45, W(62.0, -74.0)))
    LAYC = _Path((tf2 + 0.30, W(82.0, -14.0)), (T["lay"], W(126.0, -10.0)))
    LAYF = _Path((tf2 + 0.12, (xf + 62.0, y - 14.0)), (tf2 + 0.5, (xf + 70.0, y - 20.0)), (T["lay"], (xf + 128.0, y - 56.0), "o"))
    SH = (x + 0.105 * hc, y - 0.556 * hc)              # the child's far shoulder (standing, turned to the friend): the friend's hand rests here

    # ---- the friend
    F6 = FE(_F_UP, sky, 1.0, 0.0)
    f_see = FE(_F_UP.but(lean=0.20, mouth=0.5, joy=0.0, lift=0.5, neck=-0.20), _add(G1, 0.0, -60.0), 1.0, 0.2)
    f_reach = _aimed(FE(F_CROUCH.but(pel=(-0.060, 0.190), lean=0.32, bend=0.05, neck=-0.22, mouth=0.4, lift=0.4), _add(G1, 0.0, -40.0),
                        1.0, 0.2), xf, y, hf, -1, f=G1)
    f_pull1 = _aimed(FE(_F_SIT.but(lean=-0.34, bend=0.08, neck=0.10, mouth=0.2, mopen=0.5, brow=0.3, eye=0.8,
                                   hb=(-0.14, -0.24), eb=1.0, ff=(0.03, 0.03), fb=(0.085, 0.045), af=0.5, ab=0.5), A1, 1.0, 0.0),
                     xf, y, hf, -1, f=A1)
    f_sitf = _aimed(FE(_F_SIT.but(lean=0.32, bend=0.14, neck=-0.24, mouth=0.6, lift=0.3, hb=(0.16, -0.10)), _add(G2, 0.0, -50.0), 1.0, 0.2),
                    xf, y, hf, -1, f=G2)
    f_ant2 = _aimed(f_sitf.but(lean=0.40, pel=(-0.146, 0.062), mouth=0.4, mopen=0.3), xf, y, hf, -1, f=_add(G2, -5.0, -6.0),
                    b=up(G2, -20.0))
    f_pull2 = _aimed(FE(_F_SIT.but(lean=-0.56, bend=0.0, neck=0.22, mouth=0.1, mopen=0.7, brow=0.45, eye=0.5, joy=0.3,
                                   ff=(0.05, 0.075), fb=(0.105, 0.10), af=0.7, ab=0.7, eb=1.0, hair=0.9), A2, 1.0, 0.0),
                     xf, y, hf, -1, f=A2, b=up(A2, -20.0))
    f_offer = _aimed(FE(_F_SIT.but(lean=0.20, bend=0.14, neck=-0.10, tilt=0.06, mouth=0.7, lift=0.3, hb=(0.15, -0.12)), chead, 1.0, 0.1),
                     xf, y, hf, -1, f=O)
    f_wait = _aimed(FE(f_offer.but(mouth=0.35, lift=0.0, brow=0.45, tilt=0.0, neck=0.0), S_KN, 1.0, 0.25),
                    xf, y, hf, -1, f=_add(O, 4.0, 12.0))
    f_offer2 = _aimed(FE(f_offer.but(mouth=0.6, lift=0.35, brow=0.2, tilt=0.09), chead, 1.0, 0.1), xf, y, hf, -1, f=O)
    f_glad = FE(_F_SIT.but(lean=0.14, bend=0.16, neck=-0.16, mouth=1.0, joy=0.4, lift=0.4, blush=0.7, hf=(0.19, -0.105),
                           hb=(0.16, -0.125)), A3, 1.0, 0.1)
    crouch = _F_SIT.but(lean=0.26, bend=0.26, neck=0.12, mouth=0.45, lift=0.1, brow=0.2, hb=(0.15, -0.14))
    f_tape0 = _aimed(FE(crouch, s0b, 1.0, 0.3), xf, y, hf, -1, f=s0a)
    f_tape1 = _aimed(FE(crouch.but(lean=0.28, mouth=0.5), s1b, 1.0, 0.3), xf, y, hf, -1, f=s1a)
    f_look = FE(_F_SIT.but(lean=0.12, neck=-0.12, tilt=0.07, mouth=0.9, joy=0.3, blush=0.6, lift=0.2), chead, 1.0, 0.1)
    f_pick = _aimed(FE(_F_SIT.but(lean=0.40, bend=0.3, mouth=0.6), KN, 1.0, 0.3), xf, y, hf, -1, f=KN)
    f_holdup = _aimed(FE(_F_SIT.but(lean=0.14, bend=0.14, neck=-0.2, mouth=0.75, lift=0.4, hb=(0.16, -0.11)), chead, 1.0, 0.1),
                      xf, y, hf, -1, f=up(TT, 40.0))
    f_pull4 = _aimed(FE(_F_SIT.but(lean=-0.40, bend=0.04, neck=0.14, mouth=0.5, mopen=0.6, brow=0.2, eye=0.6, joy=0.4,
                                   ff=(0.04, 0.045), fb=(0.095, 0.06), af=0.6, ab=0.6, hb=(-0.13, -0.24), eb=1.0, hair=0.9), A4, 1.0, 0.0),
                     xf, y, hf, -1, f=up(A4, 40.0))
    f_watch = FE(_F_SIT.but(lean=-0.06, bend=0.12, neck=-0.30, mouth=0.75, mopen=0.2, lift=0.5, hf=(0.19, -0.105),
                            hb=(-0.12, -0.25), eb=1.0), drawing, 1.0, 0.0)
    f_seefist = FE(_F_SIT.but(lean=0.16, neck=-0.06, mouth=0.3, brow=0.4, hf=(0.19, -0.105), hb=(0.16, -0.125)),
                   W(84.0, -132.0), 1.0, 0.2)
    f_follow = FE(f_seefist.but(lean=0.06, neck=-0.3, mouth=0.6, mopen=0.25, lift=0.6, brow=0.0), W(140.0, -520.0), 1.0, 0.0)
    f_nod = FE(f_seefist.but(neck=0.06, mouth=0.9, joy=0.3, lift=0.2, brow=0.0, blush=0.6), chead, 1.0, 0.0)
    f_lay0 = _aimed(_F_SIT.but(turn=1.2, hturn=0.3, lean=0.10, bend=0.30, neck=0.22, look=(0.30, -0.5), mouth=0.6, open=1.0, ef=-1.0,
                               eb=-1.0), xf, y, hf, -1, f=LAYF(tf2 + 0.5), b=_add(LAYF(tf2 + 0.5), -16.0, 6.0))
    f_cast = _aimed(_F_SIT.but(turn=1.35, hturn=0.3, lean=0.0, bend=0.0, neck=-0.2, look=(0.3, 0.2), mouth=0.9, mopen=0.4, lift=0.4,
                               open=1.0, hfz=0.0, hbz=0.0, ef=-1.0, eb=-1.0, sway=-0.6), xf, y, hf, -1,
                    f=(xf + 128.0, y - 56.0), b=(xf + 104.0, y - 80.0))
    f_hill = _F_SIT.but(turn=1.25, hturn=0.35, lean=0.0, bend=0.1, neck=-0.22, look=(0.32, 0.30), mouth=0.8, mopen=0.3, lift=0.5,
                        open=1.0, hf=(0.03, -0.24), hb=(0.02, -0.25), hfz=0.05, hbz=0.03)
    f_cr2 = FE(F_CROUCH.but(lean=0.24, mouth=0.7), chead, 1.0, 0.1)
    f_up = FE(F_STAND.but(mouth=0.75, hf=(0.03, -0.27), hb=(0.05, -0.28)), _add(chead, 30.0, -130.0), 1.0, 0.2)
    f_sh = _aimed(FE(F_STAND.but(pel=(0.01, 0.410), lean=0.10, bend=0.04, neck=0.02, mouth=0.7, hb=(0.03, -0.29), ef=-0.6),
                     _add(SH, -30.0, -70.0), 1.0, 0.2), xf, y, hf, -1, f=SH)
    f_conc = _aimed(FE(f_sh.but(lean=0.13, pel=(0.01, 0.398), neck=0.14, tilt=-0.12, mouth=0.35, brow=0.4), _add(SH, 30.0, -40.0), 1.0, 0.3),
                    xf, y, hf, -1, f=SH)
    f_b7 = _b7_friend(x, y, d, hc, hf)
    friend = _Track(F6,
                    (159.15, 0.40, f_see), (159.55, 0.38, f_reach, "hand"), (p1, 0.22, f_pull1, "land"),
                    (p1 + 0.70, 0.70, f_sitf, "body"), (p2 - 0.35, 0.33, f_ant2, "soft"), (p2, 0.24, f_pull2, "land"),
                    (T["offer"], 0.60, f_offer, "hand"), (th + 0.25, 0.50, f_wait, "soft"), (p3 - 0.6, 0.40, f_offer2, "soft"),
                    (p3 + 0.05, 0.34, f_glad), (t0 - 0.31, 0.30, f_tape0, "hand"), (t0 + 0.28, 0.40, f_tape1, "soft"),
                    (t1 + 0.27, 0.28, f_look, "soft"), (T["release"] - 0.14, 0.36, f_pick, "hand"),
                    (T["release"] + 0.24, 0.28, f_holdup, "hand"), (p4, 0.24, f_pull4, "land"), (p4 + 0.55, 0.70, f_watch, "body"),
                    (170.8, 0.60, f_seefist, "soft"), (tf + 0.05, 0.50, f_follow, "act", dict(blink=1.0)),
                    (tf + 0.80, 0.50, f_nod, "soft"), (tf2 + 0.08, 0.40, f_lay0, "hand"), (tf2 + 0.50, 0.46, f_cast, "body"),
                    (T["lay"] + 0.14, 0.60, f_hill, "soft"), (T["rise"], 0.30, f_cr2, "body"), (T["rise"] + 0.33, 0.42, f_up, "body"),
                    (T["stand"] - 0.26, 0.30, f_sh, "hand"), (T["stand"] + 0.70, 0.50, f_conc, "soft"),
                    (T["open"] - 0.20, 0.50, f_b7))

    # ---- the child
    c_lookf = CE(_C_SIT, fhead, 1.0, 0.2)
    c_upend = CE(_C_SIT.but(neck=-0.2, lift=0.4), _add(G1, 0.0, -30.0), 1.0, 0.3)
    c_start = c_upend.but(bend=0.14, lean=0.10, eye=1.2, lift=0.7, mopen=0.2, hair=0.7)
    c_down = CE(_C_SIT.but(lean=0.14, bend=0.26, neck=0.08, lift=0.3, mopen=0.1), W(170.0, -14.0), 1.0, 0.3)
    c_down2 = CE(_C_SIT.but(lean=0.14, bend=0.24, neck=0.06, lift=0.4, mopen=0.15, eye=1.1), W(190.0, -12.0), 1.0, 0.3)
    c_seeoff = CE(_C_SIT.but(lean=0.14, neck=0.0, brow=0.4), O, 1.0, 0.3)
    c_chest = SIT_HUG.but(lean=0.14, bend=0.44, neck=0.36, look=(0.26, -0.72), gaze=(0.0, -0.5), eye=0.6, lid=0.8, brow=0.7,
                          mouth=-0.3, hf=(0.085, -0.045), hb=(0.065, -0.05), hair=0.3)
    c_halves = _aimed(CE(_C_SIT.but(lean=0.12, bend=0.34, neck=0.34, eye=0.7, lid=0.8, brow=0.85, mouth=-0.35, hair=0.25),
                         S_KN, 1.0, 0.2), x, y, hc, 1, f=HR(th + 0.8), b=HL(th + 0.8))
    c_reacho = _aimed(CE(_C_SIT.but(lean=0.16, bend=0.26, neck=-0.04, eye=0.9, lid=0.6, brow=0.5, lift=0.2, mouth=-0.15), O, 1.0, 0.2),
                      x, y, hc, 1, f=O, b=HL(th + 0.8))
    c_pull3 = _aimed(CE(_C_SIT.but(lean=0.04, bend=0.20, neck=-0.10, eye=1.05, lid=0.45, lift=0.4, brow=0.3, mopen=0.15, hair=0.58),
                        _add(G1, 10.0, -90.0), 1.0, 0.2), x, y, hc, 1, f=A3, b=HL(th + 0.8))
    c_holdout = _aimed(CE(_C_SIT.but(lean=0.20, bend=0.22, neck=0.14, eye=0.95, lid=0.5, brow=0.45, mouth=-0.12), S_OUT, 1.0, 0.3),
                       x, y, hc, 1, f=HR(t0), b=HL(t0))
    c_lift = _aimed(CE(_C_SIT.but(lean=-0.02, bend=0.10, neck=-0.18, eye=1.0, lid=0.45, brow=0.3, lift=0.3, mouth=0.0, hair=0.55),
                       S_UP, 1.0, 0.3), x, y, hc, 1, f=HR(T["release"]), b=HL(T["release"]))
    c_open = _aimed(CE(c_lift.but(neck=-0.24, mopen=0.15, lift=0.5), _add(S_UP, 20.0, -60.0), 1.0, 0.3), x, y, hc, 1,
                    f=_add(HR(T["release"]), 14.0, 6.0), b=_add(HL(T["release"]), -10.0, 8.0))
    c_take2 = _aimed(CE(_C_SIT.but(lean=0.16, bend=0.16, neck=-0.06, eye=1.0, lid=0.4, lift=0.3, mouth=0.0), TT, 1.0, 0.2),
                     x, y, hc, 1, f=TT, b=up(TT, -20.0))
    c_pull4 = _aimed(CE(_C_SIT.but(lean=-0.16, bend=0.10, neck=-0.02, eye=0.5, lid=0.6, joy=0.2, brow=0.3, mouth=0.1, mopen=0.4,
                                   hair=0.7, ff=(0.165, 0.02), fb=(0.125, 0.03)), A4, 1.0, 0.0), x, y, hc, 1, f=A4, b=up(A4, -20.0))
    c_watchup = _aimed(CE(_C_SIT.but(lean=0.04, bend=0.10, neck=-0.34, eye=1.1, lid=0.4, lift=0.6, brow=0.1, mouth=0.05, mopen=0.2,
                                     hair=0.62), drawing, 1.0, 0.0), x, y, hc, 1, f=K2, b=W(30.0, -100.0))
    c_fist = _aimed(CE(_C_SIT.but(lean=0.20, bend=0.30, neck=0.14, eye=0.85, lid=0.6, brow=0.6, mouth=-0.2, hair=0.4),
                       W(84.0, -132.0), 1.0, 0.3), x, y, hc, 1, f=K2, b=W(84.0, -132.0))
    c_upstr = _aimed(CE(c_fist.but(neck=-0.16, lift=0.3, bend=0.2), W(140.0, -460.0), 1.0, 0.2), x, y, hc, 1, f=K2, b=W(84.0, -132.0))
    c_tight = _aimed(c_fist.but(bend=0.38, neck=0.22, eye=0.12, brow=0.95, mouth=-0.4, lean=0.16), x, y, hc, 1, f=K2, b=W(70.0, -124.0))
    c_open1 = _aimed(CE(_C_SIT.but(lean=0.14, bend=0.10, neck=-0.20, eye=1.25, lid=0.3, lift=0.8, brow=0.1, mouth=0.0, mopen=0.35,
                                   hair=0.75), W(120.0, -260.0), 1.0, 0.2), x, y, hc, 1, f=K2, b=W(106.0, -162.0))
    c_follow = _aimed(CE(_C_SIT.but(lean=0.08, bend=0.06, neck=-0.36, eye=1.15, lid=0.35, lift=0.6, mouth=0.05, mopen=0.25,
                                    hair=0.7), W(150.0, -560.0), 1.0, 0.0), x, y, hc, 1, f=K2, b=W(104.0, -154.0))
    c_hand2 = _aimed(CE(_C_SIT.but(lean=0.20, bend=0.24, neck=0.10, eye=0.95, lid=0.45, brow=0.3, mouth=0.0, hair=0.6), K2, 1.0, 0.3),
                     x, y, hc, 1, f=K2, b=W(62.0, -74.0))
    c_open2 = _aimed(c_hand2.but(neck=0.02, lift=0.3, mopen=0.1), x, y, hc, 1, f=_add(K2, 10.0, -22.0), b=W(62.0, -74.0))
    c_lay = _aimed(CE(_C_SIT.but(lean=0.52, bend=0.34, neck=0.0, eye=1.0, lid=0.4, mouth=0.05, hair=0.6, pel=(-0.05, 0.055)),
                      LAYC(T["lay"]), 1.0, 0.3), x, y, hc, 1, f=LAYC(T["lay"]), b=W(64.0, -60.0))
    c_hillw = CE(_C_SIT.but(lean=0.10, bend=0.10, neck=-0.2, eye=1.2, lid=0.3, lift=0.7, mouth=0.1, mopen=0.3, hair=0.7), hill, 1.0, 0.2)
    c_tuck = SIT_HUG.but(pel=(-0.035, 0.080), lean=0.24, bend=0.34, neck=0.0, look=(0.46, 0.0), eye=1.0, lid=0.4, brow=0.2, mouth=0.0,
                         hf=(0.03, -0.26), hb=(-0.05, -0.25), ff=(0.075, 0.0), fb=(0.045, 0.0), hair=0.5)
    c_squat = c_tuck.but(pel=(0.0, 0.215), lean=0.22, bend=0.30, neck=-0.1, hf=(0.10, -0.20), hb=(0.02, -0.24), ff=(0.02, 0.0),
                         fb=(0.035, 0.0), look=(0.48, 0.1))
    c_b7 = _b7_child(x, y, d, hc, hf)
    c_stand = CE(c_b7.but(eye=0.9, lid=0.5, lift=0.1, brow=0.3, hf=(0.03, -0.31), hb=(0.06, -0.30), ef=-1.0, eb=-1.0, hair=0.4,
                          neck=-0.04), _add(fhead, 0.0, -150.0), 1.0, 0.2)
    c_doubt = c_stand.but(lean=0.02, bend=0.14, neck=0.30, look=(0.34, -0.5), gaze=(0.0, -0.5), eye=0.62, lid=0.9, brow=0.75,
                          mouth=-0.3, hair=0.2, pel=(0.0, 0.404))
    c_clasp = _aimed(c_doubt.but(neck=0.18, bend=0.16, brow=0.6, eye=0.7, ef=1.0, eb=1.0), x, y, hc, 1, f=_add(SH, -10.0, 4.0),
                     b=_add(SH, 8.0, 9.0))
    child = _Track(_C_UP,
                   (159.25, 0.45, c_lookf), (159.76, 0.26, c_upend, "soft"), (p1 + 0.05, 0.20, c_start, "jolt"),
                   (p1 + 0.35, 0.60, c_down, "act", dict(blink=1.0)), (p2 - 0.40, 0.35, c_upend, "soft"), (p2 + 0.05, 0.55, c_down2),
                   (T["offer"] + 0.22, 0.42, c_seeoff), (th, 0.42, c_chest, "hand"), (th + 0.45, 0.50, c_halves, "hand"),
                   (p3 - 0.50, 0.42, c_reacho), (p3, 0.20, c_pull3, "land"), (p3 + 0.24, 0.42, c_holdout, "hand"),
                   (T["release"] - 0.40, 0.40, c_lift, "hand"), (T["release"] + 0.02, 0.30, c_open, "soft"),
                   (T["release"] + 0.40, 0.30, c_take2, "hand"), (p4, 0.24, c_pull4, "land"),
                   (p4 + 0.50, 0.80, c_watchup, "act", dict(blink=1.0)), (170.8, 0.70, c_fist), (172.2, 0.45, c_upstr, "soft"),
                   (172.85, 0.38, c_fist, "soft"), (tf - 0.26, 0.22, c_tight, "soft"), (tf, 0.30, c_open1, "jolt"),
                   (tf + 0.45, 0.60, c_follow, "act", dict(blink=1.0)), (tf + 1.15, 0.30, c_hand2, "soft"), (tf2, 0.26, c_open2, "hand"),
                   (tf2 + 0.30, 0.50, c_lay, "body"), (T["lay"] + 0.04, 0.70, c_hillw), (T["rise"] + 0.30, 0.34, c_tuck, "body"),
                   (T["rise"] + 0.65, 0.20, c_squat, "body"), (T["rise"] + 0.86, 0.42, c_stand, "body"),
                   (T["stand"] + 0.44, 0.80, c_doubt, "slow"), (T["clasp"], 0.50, c_clasp, "hand"),
                   (T["open"], 0.26, c_b7, "blink"))

    def lf4(t):                                      # the friend's hand on the line above the child's, pulling together
        return up(LC(t), 40.0)

    cpins = ((-1e9, -1e9 + 1.0, 159.45, 159.62, "f", H),
             (th + 0.50, th + 0.80, p3 - 0.50, p3 - 0.32, "f", HR), (th + 0.50, th + 0.80, T["release"], T["release"] + 0.14, "b", HL),
             (p3 - 0.36, p3 - 0.10, p3 + 0.26, p3 + 0.40, "f", LC), (p3 + 0.42, p3 + 0.66, T["release"], T["release"] + 0.14, "f", HR),
             (p4 - 0.34, p4 - 0.12, tf2, tf2 + 0.12, "f", LC), (p4 - 0.30, p4 - 0.08, p4 + 0.9, p4 + 1.4, "b", lambda t: up(LC(t), -20.0)),
             (170.8, 171.0, tf + 1.45, tf + 1.6, "b", FIST), (tf2 + 0.34, tf2 + 0.6, T["lay"], T["lay"] + 0.2, "f", LAYC),
             (T["clasp"] + 0.34, T["clasp"] + 0.5, 1e9, 1e9 + 1.0, "f", _add(SH, -10.0, 4.0)),
             (T["clasp"] + 0.42, T["clasp"] + 0.58, 1e9, 1e9 + 1.0, "b", _add(SH, 8.0, 9.0)))
    fpins = ((-1e9, -1e9 + 1.0, 159.45, 159.62, "f", H),
             (159.72, 159.95, p3 - 0.08, p3 + 0.06, "f", LF),
             (p2 - 0.30, p2 - 0.06, p2 + 0.40, p2 + 0.60, "b", lambda t: up(LF(t), -20.0)),
             (t0 - 0.24, t0 - 0.02, t1 + 0.40, t1 + 0.62, "f", TP),
             (T["release"] + 0.02, T["release"] + 0.15, p4 - 0.14, p4 - 0.10, "f", LF),
             (p4 - 0.14, p4 - 0.10, p4 + 0.62, p4 + 0.95, "f", lf4),
             (tf2 + 0.26, tf2 + 0.5, T["lay"] + 0.02, T["lay"] + 0.2, "f", LAYF),
             (T["stand"] - 0.1, T["stand"], 1e9, 1e9 + 1.0, "f", SH))
    return dict(T=T, friend=friend, child=child, LF=LF, LC=LC, HL=HL, HR=HR, TP=TP, FIST=FIST, LAYC=LAYC, LAYF=LAYF, SH=SH, H=H,
                cpins=cpins, fpins=fpins, tape=tape, S_UP=S_UP, END=END, lf4=lf4)


@lru_cache(maxsize=8)
def _b7_child(x, y, d, hc, hf):
    """The child of hand-off B7: standing, turned toward the friend, eyes fully open, both hands on the
    friend's hand on its shoulder."""
    SH = (x + 0.105 * hc, y - 0.556 * hc)
    P = STAND.but(pel=(0.0, 0.410), lean=-0.02, bend=0.04, neck=-0.10, open=1.0, look=(0.47, 0.14), gaze=(0.35, 0.15), eye=1.0, lid=0.2,
                  lift=0.3, brow=0.12, mouth=-0.04, hair=0.45, ef=1.0, eb=1.0, ff=(-0.018, 0.0), fb=(0.026, 0.0))
    return _aimed(P, x, y, hc, 1, f=_add(SH, -10.0, 4.0), b=_add(SH, 8.0, 9.0))


@lru_cache(maxsize=8)
def _b7_friend(x, y, d, hc, hf):
    SH = (x + 0.105 * hc, y - 0.556 * hc)
    xf = x + d
    P = F_STAND.but(pel=(0.01, 0.410), lean=0.10, bend=0.04, neck=-0.02, look=(0.46, 0.0), gaze=(0.4, -0.05), mouth=0.85, joy=0.2,
                    lift=0.2, blush=0.6, hb=(0.03, -0.29), ef=-0.6)
    return _aimed(P, xf, y, hf, -1, f=SH)


def hold_B7(t: float, x: float = ST.X5, y: float = FLOOR, d: float = 180.0, hc: float = HC, hf: float = HF) -> Duet:
    """The rest state of hand-off B7 (182.30): both standing, the child at (x, y) turned toward the
    friend, its eyes fully open; the friend at x + d, its near hand on the child's shoulder
    (pts["shoulder"]), both of the child's hands closed over it. The child is drawn first."""
    xf = x + d
    SH = (x + 0.105 * hc, y - 0.556 * hc)
    Pc = _live(_b7_child(x, y, d, hc, hf), t, SC, shift=0.5)
    Pf = _live(_b7_friend(x, y, d, hc, hf), t, SF, shift=0.5)
    return Duet(Act(Pc, x, y, 1, {"f": _add(SH, -10.0, 4.0), "b": _add(SH, 8.0, 9.0)}, hc, "child", SC),
                Act(Pf, xf, y, -1, {"f": SH}, hf, "friend", SF),
                dict(shoulder=SH, hands=None, end=None, line=None, half_l=None, half_r=None, tape=None, fist=None, lay_c=None, lay_f=None),
                dict(pulls=4.0, busy=0.0, who=0, halves=1.0, taped=2.0, release=1.0, fist=0.0, fist2=0.0, lay=1.0, up=1.0), "cf")


def s07(t: float, x: float = ST.X5, y: float = FLOOR, d: float = 180.0, root=None, tape=None, sheet_s: float = 0.62,
        hc: float = HC, hf: float = HF, **times) -> Duet:
    """The bridge. From hold_B6 (sitting, hands joined, looking up) to hold_B7 (standing, the
    friend's hand on the child's shoulder). Cue times: S07_T (override any by keyword).

    The friend sees a loose end hanging between them, lets the hand go, reaches up and pulls
    (pulls[0]: it falls back on its bottom), pulls again (pulls[1], with both hands), then holds the
    end out to the child and waits. The child takes the two halves of its drawing out of its jumper
    first (halves) and looks at them; then it takes the end and gives one small pull of its own
    (pulls[2]), the halves pressed to its chest. It holds the halves out together; the friend lays a
    strip of tape on each attack (tape). The child lifts the mended drawing and lets it go (release:
    from then on the scene moves it); it takes the line under the friend's hand and they pull
    together (pulls[3]), then watch the drawing rise. The child finds its other hand clenched round
    the strand, looks at it, and opens it (fist); it opens the hand that holds the line (fist2);
    they lay the line down along the ground and the friend casts it out to the right (to `lay`);
    they watch it become the hill. The friend gets up (rise), the child gets up by itself; the
    friend's hand comes to rest on its shoulder (stand); the child's head sinks, then both its hands
    close over that hand (clasp) and it lifts its face, eyes fully open (open + 0.26).

    x, y: the child's ground point (it sits, then stands, on it); d: the friend at x + d.
    root: the world point where the loose end leaves the scribble (default (x + 125, y - 470)): the
    hands slide along the line toward it. tape: the two strips' world ends ((p0, p1), (p0, p1)) as
    things.family_held returns them (default: where they lie for s = 0.8).
    pts: hands (the joined hands until they part, then None); end (where the loose end hangs before
    it is taken); line (the hand point for gloom.unravel: the lowest hand on the line, or where it
    lies when nobody holds it); half_l, half_r (where the two halves are held: give them to
    things.family_held; None while they are in the jumper; frozen from `release`); tape (the taping
    hand, while it tapes); fist (the child's clenched far hand, from 170.8); lay_c, lay_f (the hands
    that lay the line down); shoulder (where the friend's hand rests, from `stand`).
    num: pulls (0..4, eased: unravel's out = 500 * pulls), busy (0..1: slack = 1 - busy), who (which
    pull is whose: 0 none, 1 the friend, 2 the child, 3 both), halves (0..1: out of the jumper),
    taped (0..2), release (0 / 1), fist, fist2 (1 clenched .. 0 open), lay (0..1), up (0..1: standing)."""
    T = dict(S07_T)
    T.update(times)
    if t <= 158.86:
        D = hold_B6(t, x, y, d, hc, hf)
        D.pts.update(end=(x + 102.0 + 0.5 * (d - 180.0), y - 128.0), line=None, half_l=None, half_r=None, tape=None, fist=None,
                     lay_c=None, lay_f=None, shoulder=None)
        D.num.update(pulls=0.0, busy=0.0, who=0, halves=0.0, taped=0.0, release=0.0, fist=1.0, fist2=1.0, lay=0.0, up=0.0)
        return D
    if t >= T["open"] + 0.53:
        return hold_B7(t, x, y, d, hc, hf)
    root = (x + 125.0 + 0.5 * (d - 180.0), y - 470.0) if root is None else (float(root[0]), float(root[1]))
    if tape is not None:
        tape = tuple((_pt(a), _pt(b)) for a, b in tape)
    Pn = _s07_plan(x, y, d, hc, hf, root, tape, tuple(sorted(T.items())), sheet_s)
    xf = x + d
    p1, p2, p3, p4 = T["pulls"]
    ct, ft = Pn["child"], Pn["friend"]
    Pc = _follow(ct.at(t), ct.at(t - _DT), k=0.7)
    Pf = _follow(ft.at(t), ft.at(t - _DT), k=0.8)
    # effort: a tremble while a pull is held; shoulders shaking as the friend laughs after the child's own pull
    for tp, wf, wc in ((p1, 1.0, 0.0), (p2, 1.0, 0.0), (p3, 0.0, 0.6), (p4, 1.0, 1.0)):
        e = _env(t, tp + 0.2, 0.05, 0.25, 0.2)
        if e > 0.0:
            s = math.sin(2.0 * math.pi * 11.0 * t)
            if wf:
                Pf = Pf.but(lean=Pf["lean"] + 0.012 * e * s * wf)
            if wc:
                Pc = Pc.but(lean=Pc["lean"] + 0.010 * e * s * wc)
    lg = _env(t, p3 + 0.3, 0.1, 0.5, 0.4)
    if lg > 0.0:
        Pf = Pf.but(pel=(Pf["pel"][0], Pf["pel"][1] + 0.004 * lg * math.sin(2.0 * math.pi * 5.0 * t)), mopen=Pf["mopen"] + 0.4 * lg)
    Pc, gc = _pin(Pc, t, x, y, hc, 1, Pn["cpins"])
    Pf, gf = _pin(Pf, t, xf, y, hf, -1, Pn["fpins"])
    busy_c = ct.busy(t)
    busy_f = ft.busy(t)
    quiet = ((159.1, 160.6), (p2 - 0.5, p2 + 0.7), (T["halves"] - 0.1, p3 + 1.0), (T["release"] - 0.5, p4 + 1.4),
             (170.7, 171.6), (T["fist"] - 0.9, T["fist"] + 1.2), (T["stand"] + 0.3, T["open"] + 0.5))
    sit = 1.0 - _ramp(t, T["rise"] + 0.3, T["rise"] + 1.3)
    Pc = _live(Pc, t, SC, quiet if not busy_c else ((t - 1.0, t + 1.0),), shift=1.0 - 0.5 * _ramp(t, T["rise"], T["rise"] + 1.0))
    Pf = _live(Pf, t, SF, quiet if not busy_f else ((t - 1.0, t + 1.0),), shift=0.5)
    order = "cf" if (T["tape"][0] - 0.33 <= t < T["release"] - 0.1 or t >= T["stand"] - 0.3) else "fc"
    child = Act(Pc, x, y, 1, gc, hc, "child", SC)
    friend = Act(Pf, xf, y, -1, gf, hf, "friend", SF)
    # ---- what the scene needs
    th, t0, t1, tr = T["halves"], T["tape"][0], T["tape"][1], T["release"]
    if t < p1 - 0.05:
        line = None
    elif t < p3 - 0.05:
        line = Pn["LF"](t)
    elif t < tr + 0.15:
        line = Pn["LC"](t)
    elif t < p4 - 0.2:
        line = Pn["LF"](t)
    else:
        line = _lerp(Pn["LF"](t), Pn["LC"](t), _ramp(t, p4 - 0.2, p4 - 0.02))
    held = th + 0.30 <= t
    pts = dict(hands=Pn["H"] if t < 159.45 else None, end=Pn["END"], line=line,
               half_l=Pn["HL"](min(t, tr)) if held else None, half_r=Pn["HR"](min(t, tr)) if held else None,
               tape=Pn["TP"](t) if t0 - 0.02 <= t <= t1 + 0.5 else None,
               fist=Pn["FIST"](t) if 170.8 <= t <= T["fist"] + 1.6 else None,
               lay_c=Pn["LAYC"](t) if T["fist2"] + 0.3 <= t <= T["lay"] + 0.2 else None,
               lay_f=Pn["LAYF"](t) if T["fist2"] + 0.12 <= t <= T["lay"] + 0.2 else None,
               shoulder=Pn["SH"] if t >= T["stand"] else None, sheet=_add(Pn["S_UP"], 0.0, 0.0), tapes=Pn["tape"])
    who = 0
    for i, tp in enumerate((p1, p2, p3, p4)):
        if tp - 0.4 <= t <= tp + 0.9:
            who = (1, 1, 2, 3)[i]
    num = dict(pulls=_sumpull(t, T["pulls"]), busy=_busy(t, T["pulls"]), who=who, halves=_ramp(t, th + 0.30, th + 0.62),
               taped=_seg(t, t0, t0 + 0.24) + _seg(t, t1, t1 + 0.24), release=1.0 if t >= tr else 0.0,
               fist=1.0 - _ramp(t, T["fist"], T["fist"] + 0.3), fist2=1.0 - _ramp(t, T["fist2"], T["fist2"] + 0.26),
               lay=_seg(t, T["fist2"], T["lay"]), up=1.0 - sit)
    return Duet(child, friend, pts, num, order)


# --------------------------------------------------------------------------
# turning on the spot while the ground point travels (a turning step): no sliding foot
# --------------------------------------------------------------------------
def _turn_step(a, b, w, x0, x1, h, face=1, hop=1.0):
    """turn_round(a, b, w) while the figure's ground point goes from world x0 to x1: the foot that
    stands is held where it is in the world (the rig's turn picks up the near foot in the first
    half, the far one in the second). Returns (pose, world x)."""
    w = _c(w)
    P = turn_round(a, b, w, 0.30, hop)
    xg = x0 + (x1 - x0) * _sm(w)
    if x1 == x0 or w <= 0.0 or w >= 1.0:
        return P, xg
    if w < 0.5:                                      # the far foot stands: where pose a had it
        key, wx = "b", x0 + face * h * _ankle_x(a, "fb")
    else:                                            # the near foot stands: where pose b will have it
        key, wx = "f", x1 + face * h * _ankle_x(b, "ff")
    return aim_foot(P, key, ((wx - xg) / (face * h), P["f" + key][1] + 0.014)), xg


def _live2(P, t, seed, w, quiet=(), breath=1.0, shift=1.0):
    """alive() for a pose that is written for the mirrored `face` (swap_sides): w = 0 gives exactly
    the picture the other way of writing it would give, w = 1 the plain alive; between, a blend
    (so that a figure can change the way it is written without the smallest jump)."""
    if w >= 1.0:
        return _live(P, t, seed, quiet, breath, shift)
    A_ = _mirror(_live(_mirror(P), t, seed, quiet, breath, shift))
    if w <= 0.0:
        return A_
    return mixp(A_, _live(P, t, seed, quiet, breath, shift), w)


# --------------------------------------------------------------------------
# s08 (182.30 to 201.25): the scribble comes down as a curtain; the friend parts it; the child
# lifts its head into the light, stands, and takes one side; both hang on the strands
# --------------------------------------------------------------------------
S08_T = dict(attacks=(184.34, 185.14, 186.26, 186.65, 187.56, 188.14, 188.90), lift=189.6, stand=191.90, join=195.5,
             turn=197.2, breath=200.2, pull=200.62)

_BK = Pose(turn=3.0, pel=(0.0, 0.412), lean=0.0, bend=-0.05, neck=-0.12, look=(0.0, 0.2), hf=(0.0, -0.30), hb=(0.0, -0.30),
           hfz=0.03, hbz=0.03, ff=(0.0, 0.0), fb=(0.0, 0.0), ffz=0.030, fbz=0.030, hair=0.9, open=1.0, mouth=0.0, ef=0.4, eb=0.4)
_C_SITB = rebase(SIT_HUG, 0.147, 0.0)              # sitting down where it stood: the feet stay, the hips go down behind them
_SITB8 = dict(pel=_C_SITB["pel"], ff=_C_SITB["ff"], fb=_C_SITB["fb"])


def _tremble(t, k):
    """A small shiver of a held grip (world units; on the true time: it goes on in the silence)."""
    if k <= 0.0:
        return 0.0, 0.0
    return (k * (0.9 * math.sin(2.0 * math.pi * 9.3 * t) + 0.6 * math.sin(2.0 * math.pi * 12.7 * t + 1.3)),
            k * (0.7 * math.sin(2.0 * math.pi * 10.9 * t + 0.4) + 0.5 * math.sin(2.0 * math.pi * 7.9 * t + 2.1)))


_B8_GX, _B8_GY = 0.230, 0.840            # the grips of hand-off B8: body units outward from, and above, each ground point
_B8_FEET = ((0.145, 0.0), (0.025, 0.0))  # where the two feet stand while they hang back (planted from the end of the turn)


@lru_cache(maxsize=8)
def _b8_poses(x, y, d, hc, hf):
    """Hand-off B8: (child pose, child x, friend pose, friend x, left grip, right grip). Each hangs
    back on its own bunch of strands, its back to the other."""
    xc, xf = x - 20.0, x + d + 20.0
    gl, gr = (xc - _B8_GX * hc, y - _B8_GY * hc), (xf + _B8_GX * hf, y - _B8_GY * hf)
    # the feet stand 0.06 h further out than the ground point and the body hangs back from them (the two big heads
    # stay about 60 units apart); over = -1: BOTH arms go up behind the head, so that neither crosses the face
    base = Pose(pel=(0.022, 0.390), lean=-0.17, bend=-0.04, neck=0.12, look=(0.40, 0.20), gaze=(0.3, 0.3), eye=0.6, lid=0.3,
                brow=0.6, mouth=-0.15, mopen=0.4, ff=_B8_FEET[0], fb=_B8_FEET[1], af=0.0, ab=0.0, ef=1.0, eb=1.0, hair=0.8,
                open=0.5, sway=0.3, over=-1.0)
    Pc = _aimed(base, xc, y, hc, -1, f=gl, b=_add(gl, 3.0, -15.0))
    Pf = _aimed(base.but(pel=(0.022, 0.404), af=-0.55, ab=-0.55, mouth=0.1, brow=0.5, blush=0.6), xf, y, hf, 1, f=gr,
                b=_add(gr, -3.0, -15.0))
    return Pc, xc, Pf, xf, gl, gr


def hold_B8(t: float, x: float = ST.X5, y: float = FLOOR, d: float = 180.0, hc: float = HC, hf: float = HF) -> Duet:
    """The rest state of hand-off B8 (201.25): the child at x - 20 facing left, the friend at
    x + d + 20 facing right (on tiptoe), back to back in the opening, each with both hands up on the
    bunch of strands of its own curtain, hanging back on it with its whole weight; the arms tremble. The
    arms go up BEHIND the heads (the rig's over = -1), so both faces are free; the heads are 77 units apart.
    pts: grip_l, grip_r (what gloom.curtains takes as left= and right=), hands_l, hands_r (the two
    hands on each). num: open 1, strain 1."""
    Pc, xc, Pf, xf, gl, gr = _b8_poses(x, y, d, hc, hf)
    tl, tr = _tremble(t, 1.3), _tremble(t + 0.37, 1.3)
    gl, gr = _add(gl, *tl), _add(gr, *tr)
    Pc = _live(Pc, t, SC, breath=1.5, shift=0.3)
    Pf = _live(Pf, t, SF, breath=1.5, shift=0.3)
    cl2, fr2 = _add(gl, 3.0, -15.0), _add(gr, -3.0, -15.0)
    return Duet(Act(Pc, xc, y, -1, {"f": gl, "b": cl2}, hc, "child", SC), Act(Pf, xf, y, 1, {"f": gr, "b": fr2}, hf, "friend", SF),
                dict(grip_l=gl, grip_r=gr, hands_l=(gl, cl2), hands_r=(gr, fr2), shoulder=None),
                dict(open=1.0, strain=1.0, lit=1.0, tremble=1.3), "fc")


@lru_cache(maxsize=4)
def _s08_plan(x, y, d, hc, hf, gap, T):
    T = dict(T)
    a1, a2, a3, a4, a5, a6, a7 = T["attacks"]
    xf0 = x + d
    xs1 = xs2 = xf0                                  # the friend parts the curtain where it stood
    SH = (x + 0.105 * hc, y - 0.556 * hc)
    Pc8, xc8, Pf8, xf8, gl8, gr8 = _b8_poses(x, y, d, hc, hf)
    tj, tt, tb, tp = T["join"], T["turn"], T["breath"], T["pull"]

    def G(dx, dy):
        return (gap + dx, y + dy)

    # ---- the two grips (the hands on the curtains): world points in time. The friend stands with its back
    # to us where it stood (xs) and opens the curtain over its own head: a hand must show BESIDE or ABOVE the
    # big head, never behind it
    def S(dx, dy):
        return (xs1 + dx, y + dy)

    LG = _Path((a5, S(-6.0, -396.0)), (a6 - 0.02, S(-6.0, -396.0)), (a6 + 0.14, S(-58.0, -374.0), "o"), (a6 + 0.26, S(-58.0, -374.0)),
               (a6 + 0.46, S(-38.0, -384.0), "o"), (a7 - 0.02, S(-38.0, -384.0)), (a7 + 0.16, S(-88.0, -334.0), "o"),
               (T["lift"] + 1.3, S(-88.0, -334.0)), (T["lift"] + 1.75, S(-80.0, -340.0)), (T["stand"] - 0.02, S(-80.0, -340.0)),
               (T["stand"] + 0.16, S(-100.0, -304.0), "o"), (193.0, S(-100.0, -304.0)), (tj, S(-92.0, -310.0)), (tt, S(-92.0, -310.0)),
               (tt + 0.50, (x - 4.0, y - 394.0)), (tt + 1.00, (xc8 - 104.0, y - 352.0)),
               (tt + 1.70, _add(gl8, -4.0, -8.0)), (tb, _add(gl8, -4.0, -8.0)), (tb + 0.40, _add(gl8, -1.0, -17.0)),
               (tp, _add(gl8, -1.0, -17.0)), (tp + 0.26, gl8, "o"))
    RG = _Path((a5, S(6.0, -396.0)), (a6 - 0.02, S(6.0, -396.0)), (a6 + 0.14, S(58.0, -374.0), "o"), (a6 + 0.26, S(58.0, -374.0)),
               (a6 + 0.46, S(38.0, -384.0), "o"), (a7 - 0.02, S(38.0, -384.0)), (a7 + 0.16, S(90.0, -334.0), "o"),
               (T["stand"] - 0.02, S(90.0, -334.0)), (T["stand"] + 0.16, S(102.0, -304.0), "o"), (193.0, S(102.0, -304.0)),
               (tj, S(96.0, -308.0)), (tt, S(96.0, -308.0)), (tt + 1.05, (xf8 + 106.0, y - 358.0)), (tt + 1.70, _add(gr8, 4.0, -8.0)),
               (tb, _add(gr8, 4.0, -8.0)), (tb + 0.40, _add(gr8, 1.0, -17.0)), (tp, _add(gr8, 1.0, -17.0)), (tp + 0.26, gr8, "o"))

    # ---- the friend, written for face = +1 all through (profile left is turn 2)
    fb7 = _b7_friend(x, y, d, hc, hf)

    def FE(P, target, kk=1.0, head=0.3):             # its eye line while it still faces left
        return _eyes(P, xf0, y, hf, -1, target, kk, head)

    f_up0 = FE(fb7.but(neck=-0.26, mouth=0.35, joy=0.0, lift=0.5, lean=0.06), (x + 120.0, y - 760.0), 1.0, 0.0)
    f_conc = FE(fb7.but(mouth=0.15, joy=0.0, brow=0.5, lift=0.0, tilt=-0.08, neck=0.08), _add(SH, -30.0, -60.0), 1.0, 0.2)
    f_ant = f_conc.but(pel=(0.01, 0.392), bend=0.14, hb=(0.06, -0.22), mouth=-0.1, brow=0.6, look=(0.42, 0.5), neck=-0.1)
    f_push = f_ant.but(pel=(0.01, 0.428), lean=0.04, bend=-0.10, neck=-0.34, look=(0.40, 0.85), gaze=(0.0, 0.8), mouth=-0.2, mopen=0.5,
                       brow=0.7, eye=1.1, hb=(0.16, 0.30), eb=1.0, af=-0.6, ab=-0.6, hair=1.0)
    f_duck = f_ant.but(pel=(-0.035, 0.372), lean=0.04, bend=0.32, neck=0.24, look=(0.36, -0.2), eye=0.3, brow=0.9, mouth=-0.4,
                       hb=(0.10, 0.17), eb=1.0, hair=0.5)
    FR = _mirror
    track1 = _Track(FR(fb7), (182.50, 0.45, FR(f_up0)), (183.35, 0.50, FR(f_conc), "soft"), (a1 - 0.24, 0.22, FR(f_ant), "soft"),
                    (a1, 0.20, FR(f_push), "jolt"), (a2, 0.20, FR(f_duck), "jolt"))
    bk0 = _BK.but(pel=(0.0, 0.400), bend=0.1, hf=(0.0, -0.20), hb=(0.0, -0.20), hfz=0.06, hbz=0.06, neck=-0.2)

    def BK(xs, l=None, r=None, **kw):                # a back-view pose with its hands on world points
        return _aimed(_BK.but(**kw), xs, y, hf, 1, f=r, b=l)

    up_ = dict(pel=(0.0, 0.430), af=-0.6, ab=-0.6, neck=-0.3)
    dip = dict(pel=(0.0, 0.372), bend=0.12, neck=0.0, ffz=0.045, fbz=0.045)
    bk_a1 = BK(xs1, S(-62.0, -250.0), S(62.0, -250.0), **dip)
    bk_s1 = BK(xs1, S(-80.0, -332.0), S(80.0, -332.0), **up_)
    bk_a2 = BK(xs1, S(-66.0, -246.0), S(66.0, -246.0), **dip)
    bk_s2 = BK(xs1, S(-90.0, -348.0), S(86.0, -352.0), roll=0.05, **up_)
    bk_seam = BK(xs1, S(-16.0, -388.0), S(12.0, -392.0), pel=(0.0, 0.422), neck=-0.3, af=-0.4, ab=-0.4)
    bk_in = BK(xs1, LG(a5), RG(a5), pel=(0.0, 0.432), neck=-0.34, af=-0.7, ab=-0.7)
    bk_dip = BK(xs1, LG(a5), RG(a5), **dip)
    bk_v1 = BK(xs1, LG(a6 + 0.2), RG(a6 + 0.2), pel=(0.0, 0.424), ffz=0.06, fbz=0.06, af=-0.5, ab=-0.5, neck=-0.34, sway=0.5)
    bk_slip = BK(xs1, LG(a6 + 0.5), RG(a6 + 0.5), pel=(0.0, 0.330), pz=0.05, roll=0.18, bend=0.2, neck=0.1, ffz=0.03, fbz=0.19,
                 ab=0.4, hair=0.5)
    bk_dip2 = BK(xs2, LG(a7 - 0.05), RG(a7 - 0.05), pel=(0.0, 0.356), bend=0.14, neck=0.0, ffz=0.075, fbz=0.075)
    bk_v2 = BK(xs2, LG(a7 + 0.2), RG(a7 + 0.2), pel=(0.0, 0.424), ffz=0.085, fbz=0.085, af=-0.5, ab=-0.5, neck=-0.36, sway=-0.6)
    bk_hold = BK(xs2, LG(a7 + 0.2), RG(a7 + 0.2), pel=(0.0, 0.408), ffz=0.085, fbz=0.085, neck=-0.1, hturn=-0.45, roll=-0.04)
    bk_give = BK(xs2, LG(T["lift"] + 1.8), RG(T["lift"] + 1.8), pel=(0.0, 0.392), pz=0.02, ffz=0.085, fbz=0.085, neck=0.06,
                 roll=0.05, bend=0.1)
    bk_dip3 = BK(xs2, LG(T["stand"] - 0.05), RG(T["stand"] - 0.05), pel=(0.0, 0.360), bend=0.14, ffz=0.085, fbz=0.085, roll=0.04)
    bk_v3 = BK(xs2, LG(T["stand"] + 0.2), RG(T["stand"] + 0.2), pel=(0.0, 0.428), ffz=0.085, fbz=0.085, af=-0.6, ab=-0.6,
               neck=-0.38, sway=0.5)
    bk_strain = BK(xs2, LG(193.0), RG(193.0), pel=(0.0, 0.420), ffz=0.085, fbz=0.085, af=-0.5, ab=-0.5, neck=0.10, bend=0.06)
    bk_sag = BK(xs2, LG(tj), RG(tj), pel=(0.0, 0.384), ffz=0.090, fbz=0.090, af=-0.15, ab=-0.15, neck=0.26, bend=0.16, hair=0.6)
    bk_relief = BK(xs2, LG(tj), RG(tj), pel=(0.0, 0.404), ffz=0.085, fbz=0.085, neck=-0.1, hturn=-0.5, roll=-0.04)
    track2 = _Track(bk0, (a3 - 0.14, 0.12, bk_a1, "soft"), (a3, 0.14, bk_s1, "jolt"), (a4 - 0.15, 0.13, bk_a2, "soft"),
                    (a4, 0.14, bk_s2, "jolt"), (a4 + 0.30, 0.48, bk_seam, "hand"), (a5 - 0.08, 0.10, bk_in, "jolt"),
                    (a6 - 0.24, 0.22, bk_dip, "soft"), (a6, 0.16, bk_v1, "jolt"), (a6 + 0.26, 0.22, bk_slip, "jolt"),
                    (a6 + 0.50, 0.24, bk_dip2, "body"), (a7, 0.16, bk_v2, "jolt"), (a7 + 0.35, 0.50, bk_hold, "soft"),
                    (T["lift"] + 1.3, 0.45, bk_give, "slow"), (T["stand"] - 0.20, 0.18, bk_dip3, "soft"),
                    (T["stand"], 0.16, bk_v3, "jolt"), (T["stand"] + 0.40, 0.60, bk_strain, "soft"), (193.2, 2.2, bk_sag, "mix"),
                    (tj + 1.40, 0.40, bk_relief, "soft"))
    # (after its turn each stands upright OVER the feet of hand-off B8, then hangs back from them: no foot slides)
    fr0 = _aimed(Pf8.but(pel=(0.085, 0.412), lean=0.0, bend=0.0, neck=-0.2, af=0.0, ab=0.0),
                 xf8, y, hf, 1, f=RG(tt + 1.05), b=_add(RG(tt + 1.05), -3.0, -15.0))
    fr_lean = _aimed(Pf8.but(lean=-0.11, pel=(0.03, 0.404), neck=0.0, eye=0.9, look=(0.40, 0.3)), xf8, y, hf, 1, f=RG(tt + 1.7), b=_add(RG(tt + 1.7), -3.0, -15.0))
    fr_look = fr_lean.but(neck=-0.10, look=(0.14, 0.30), gaze=(-0.9, 0.0), mouth=0.5, brow=0.2, lift=0.3, eye=1.0)
    fr_in = _aimed(Pf8.but(lean=-0.04, bend=-0.14, pel=(0.045, 0.414), neck=-0.20, look=(0.40, 0.4), mopen=0.2, mouth=0.0, chest=1.0, eye=1.05),
                   xf8, y, hf, 1, f=RG(tb + 0.4), b=_add(RG(tb + 0.4), -3.0, -15.0))
    track3 = _Track(fr0, (tt + 1.06, 0.62, fr_lean, "body"), (tt + 1.90, 0.40, fr_look, "soft"), (tt + 2.58, 0.40, fr_lean, "soft"),
                    (tb, 0.40, fr_in, "soft"), (tp, 0.26, Pf8, "land"))

    # ---- the child (written for face = +1 until it has turned under the bunch; then for face = -1)
    cb7 = _b7_child(x, y, d, hc, hf)
    c_up = cb7.but(neck=-0.30, look=(0.42, 0.72), gaze=(0.0, 0.7), eye=1.1, lift=0.6, mopen=0.2, lean=-0.04)
    c_sink = STOPPED.but(pel=(0.0, 0.398), lean=0.10, bend=0.40, neck=0.34, look=(0.30, -0.75), eye=0.45, lid=1.0, brow=0.75,
                         mouth=-0.4, hair=0.05, ff=(-0.018, 0.0), fb=(0.026, 0.0))
    c_sq = Pose(pel=(-0.15, 0.205), lean=0.22, bend=0.62, neck=0.50, look=(0.28, -0.85), hf=(0.11, -0.19), hb=(0.09, -0.20),
                ff=(-0.018, 0.0), fb=(0.026, 0.0), open=0.35, front=1.0, eye=0.3, lid=1.0, brow=0.85, mouth=-0.45, hair=0.0)
    c_low = SIT_HUG.but(lean=0.10, bend=0.62, neck=0.58, look=(0.26, -0.85), eye=0.12, brow=0.8, mouth=-0.45, hair=0.0, **_SITB8)
    c_stir = c_low.but(neck=0.50, eye=0.45, brow=0.7, gaze=(0.4, 0.5))
    c_lift = SIT_LIFT.but(look=(0.46, 0.66), gaze=(0.3, 0.6), neck=-0.34, lid=0.4, eye=1.15, lift=0.6, mopen=0.3, mouth=0.05,
                          hair=0.62, spark=0.0, **_SITB8)
    c_seef = c_lift.but(look=(0.50, 0.42), gaze=(0.6, 0.5), neck=-0.2, hf=(0.20, -0.07), mopen=0.15, lift=0.4, brow=0.3, spark=0.5)
    c_stand = LOOK_UP.but(look=(0.44, 0.62), eye=1.1, lid=0.3, mouth=0.0, mopen=0.15, lift=0.5, brow=0.15, hair=0.62, spark=0.6,
                          ff=(-0.018, 0.0), fb=(0.026, 0.0), pel=(0.0, 0.412), neck=-0.26)
    c_watch = _eyes(c_stand.but(neck=-0.06, lean=0.0, bend=-0.05, mopen=0.0, brow=0.45, lift=0.2, eye=1.0), x, y, hc, 1,
                    (xs2, y - 330.0), 1.0, 0.2)
    c_hes = _aimed(_eyes(c_watch.but(lean=0.0, lift=0.3, over=-1.0), x, y, hc, 1, LG(tj), 1.0, 0.2), x, y, hc, 1,
                   f=_add(LG(tj), -30.0, 100.0))
    c_watch2 = _aimed(c_hes.but(brow=0.55, mouth=-0.1), x, y, hc, 1, f=_add(LG(tj), -40.0, 132.0))
    c_reach = _aimed(_eyes(c_watch.but(lean=-0.04, pel=(0.02, 0.414), neck=-0.24, lift=0.4, brow=0.35, mouth=0.0, ef=1.0, eb=1.0,
                                       over=-1.0),
                           x, y, hc, 1, LG(tj), 1.0, 0.0), x, y, hc, 1, f=LG(tj))
    c_both = _aimed(c_reach.but(pel=(0.02, 0.404), lean=-0.06, brow=0.5, mouth=-0.05, mopen=0.3, eye=0.9), x, y, hc, 1, f=LG(tj),
                    b=_add(LG(tj), -4.0, 15.0))
    cl0n = _aimed(Pc8.but(pel=(0.085, 0.410), lean=0.02, bend=0.0, neck=-0.22), xc8, y, hc, -1,
                  f=LG(tt + 1.0), b=_add(LG(tt + 1.0), 3.0, -15.0))                  # after the turn: facing left, hands up before it
    cl0 = _mirror(cl0n).but(turn=-2.0)                                 # the same, as the +1 track reaches it (turn -2 = 2)
    c_lean = _aimed(Pc8.but(lean=-0.11, pel=(0.03, 0.394), neck=0.0, eye=0.9, look=(0.40, 0.3)), xc8, y, hc, -1, f=LG(tt + 1.7), b=_add(LG(tt + 1.7), 3.0, -15.0))
    c_look = c_lean.but(neck=-0.10, look=(0.14, 0.30), gaze=(-0.9, 0.0), mouth=0.2, mopen=0.2, brow=0.2, lift=0.4, eye=1.0)
    c_in = _aimed(Pc8.but(lean=-0.04, bend=-0.14, pel=(0.045, 0.402), neck=-0.20, look=(0.40, 0.4), mopen=0.2, chest=1.0, eye=1.05), xc8, y, hc, -1,
                  f=LG(tb + 0.4), b=_add(LG(tb + 0.4), 3.0, -15.0))
    ts = T["stand"]
    ctrack1 = _Track(cb7, (182.75, 0.45, c_up), (183.30, 1.25, c_sink, "slow"), (184.90, 0.62, c_sq, "slow"),
                     (185.55, 0.60, _C_SITB.but(lean=0.30, bend=0.6, neck=0.4, look=(0.28, -0.8), eye=0.3, hair=0.0), "body"),
                     (186.30, 0.60, c_low, "soft"), (a7 + 0.3, 0.35, c_stir, "soft"), (T["lift"], 1.25, c_lift, "act", dict(blink=1.0)),
                     (T["lift"] + 1.35, 0.35, c_seef, "soft"), (ts - 0.58, 0.56, c_stand, "body"), (ts + 0.60, 0.50, c_watch, "soft"),
                     (tj - 1.10, 0.45, c_hes, "soft"), (tj - 0.55, 0.35, c_watch2, "soft"), (tj, 0.50, c_reach, "hand"),
                     (tj + 0.80, 0.50, c_both, "hand"))
    ctrack2 = _Track(cl0n, (tt + 1.05, 0.62, c_lean, "body"), (tt + 1.80, 0.40, c_look, "soft"), (tt + 2.50, 0.40, c_lean, "soft"),
                     (tb, 0.40, c_in, "soft"), (tp, 0.26, Pc8, "land"))
    XF = _Path((a6 + 0.50, (xs1, 0.0)), (a6 + 0.74, (xs2, 0.0)))
    del G
    return dict(T=T, LG=LG, RG=RG, track1=track1, track2=track2, track3=track3, ctrack1=ctrack1, ctrack2=ctrack2, bk0=bk0, fr0=fr0,
                c_both=c_both, cl0=cl0, xs1=xs1, xs2=xs2, XF=XF, SH=SH, f_duck=FR(f_duck), bk_relief=bk_relief, xc8=xc8, xf8=xf8)


def s08(t: float, x: float = ST.X5, y: float = FLOOR, d: float = 180.0, gap: float | None = None, hc: float = HC,
        hf: float = HF, **times) -> Duet:
    """The breakdown and the long silence. From hold_B7 to hold_B8. Cue times: S08_T.

    The scribble comes down; both look up; the child's eyes go dull, its hands slip from the
    friend's hand, its head sinks, its knees give and it sits down where it stood, forehead on its
    knees (its line pales: Act.a). The friend fights from the first attack: an arm up against the
    dark (attacks[0]), pressed down (attacks[1]); it turns its back to us and goes to the curtain,
    shoves at it twice (attacks[2], [3]), finds the seam and plunges both hands in (attacks[4]: the
    grips exist from here); a heave apart (attacks[5]), it slips, plants its feet again, and a great
    heave (attacks[6]: the opening is over the child, the shaft lands on it). The child stirs, lifts
    its head into the light (lift: 1.25 s, the full choreography), looks at the friend's back, and
    stands on the strong attack (stand) while the friend heaves once more. In the silence the friend
    holds, on tiptoe, arms shaking, slowly sagging; the child lifts a hand, lets it sink, then puts
    both hands up on the left bunch (join .. join + 1.3). The friend lets that side go, turns to the
    right one with both hands; the child turns under its bunch to face left (turn); each walks its
    bunch outward and hangs back on it; a look over the shoulders; a breath in (breath), one more
    pull (pull), held to the hand-off.

    x, y: the child's ground point at B7; d: the friend at x + d; gap: world x of the seam (default
    x + d / 2). The friend is written as hold_B7 writes it (face -1) until the middle of its first turn
    (attacks[1] + 0.57), then for face +1; the child for face +1 until it has turned under its bunch (turn + 1):
    take face from the Acts.
    pts: grip_l, grip_r (None until attacks[4]; give them to gloom.curtains as left=, right=),
    hands_l, hands_r (the hands on each grip), shoulder (the friend's hand on the child, at first).
    num: open (0..1: how far the curtains are apart), lit (0..1: the shaft on the child, from
    attacks[6]), strain (0..1), tremble (world units of the grips' shiver: use it for curtains'
    tremble too), a (the child's pressure, also in child.a)."""
    T = dict(S08_T)
    T.update(times)
    if t <= 182.30:
        D = hold_B7(t, x, y, d, hc, hf)
        D.pts.update(grip_l=None, grip_r=None, hands_l=(), hands_r=())
        D.num.update(open=0.0, lit=0.0, strain=0.0, tremble=0.0, a=1.0)
        return D
    if t >= T["pull"] + 0.38:
        return hold_B8(t, x, y, d, hc, hf)
    gap = x + 0.5 * d if gap is None else float(gap)
    Pn = _s08_plan(x, y, d, hc, hf, gap, tuple(sorted(T.items())))
    a1, a2, a3, a4, a5, a6, a7 = T["attacks"]
    tj, tt, tb, tp = T["join"], T["turn"], T["breath"], T["pull"]
    xf0 = x + d
    SH = Pn["SH"]
    # ---- the grips
    hold = _ramp(t, a7 + 0.4, a7 + 1.0)
    ktr = 0.5 * hold + 0.8 * _ramp(t, 193.0, 193.6)
    gl = gr = None
    if t >= a5:
        gl, gr = _add(Pn["LG"](t), *_tremble(t, ktr)), _add(Pn["RG"](t), *_tremble(t + 0.37, ktr))
    # ---- the friend
    gf = {}
    if t < a2 + 0.26:
        Pf, xf = Pn["track1"].at(t), xf0
        P0 = Pn["track1"].at(t - _DT)
        if t < a2 + 0.16:
            w = 1.0 - _ramp(t, a2 - 0.10, a2 + 0.14)
            if w >= 1.0:
                gf["b"] = SH
            elif w > 0.0:
                Pf, _ = _pin(Pf, t, xf, y, hf, 1, ((-1e9, -1e9 + 1.0, a2 - 0.10, a2 + 0.14, "b", SH),))
    elif t < a2 + 0.26 + 0.62:
        w = (t - (a2 + 0.26)) / 0.62
        Pf, xf = _turn_step(Pn["f_duck"], Pn["bk0"], w, xf0, Pn["xs1"], hf)
        P0 = Pf
    elif t < tt + 0.05:
        Pf, xf = Pn["track2"].at(t), Pn["XF"](t)[0]
        P0 = Pn["track2"].at(t - _DT)
        if t >= a5:
            gf["f"] = gr
            if t < tt - 0.12:
                gf["b"] = gl
            else:
                Pf = aim_hand(Pf, "b", _b(_lerp(gl, _add(gr, -3.0, -15.0), _ramp(t, tt - 0.12, tt + 0.05)), xf, y, hf, 1))
    elif t < tt + 1.05:
        w = (t - (tt + 0.05)) / 1.00
        Pf, xf = _turn_step(Pn["bk_relief"], Pn["fr0"].but(turn=4.0), w, Pn["xs2"], Pn["xf8"], hf)
        P0 = Pf
        gf["f"] = gr
        gf["b"] = _add(gr, -3.0, -15.0)
    else:
        Pf, xf = Pn["track3"].at(t), Pn["xf8"]
        P0 = Pn["track3"].at(t - _DT)
        gf["f"] = gr
        gf["b"] = _add(gr, -3.0, -15.0)
    Pf = _follow(Pf, P0, k=0.8)
    strain = max(hold, _ramp(t, a1 - 0.2, a1)) * (1.0 - 0.0)
    Pf = _live2(Pf, t, SF, _ramp(t, 186.0, 187.4), ((182.4, 183.2),), breath=1.0 + 0.5 * hold, shift=0.5 - 0.2 * hold)
    # ---- the child
    gc = {}
    if t < tt:
        Pc, xc, facec = Pn["ctrack1"].at(t), x, 1
        P0 = Pn["ctrack1"].at(t - _DT)
        segs = ((-1e9, -1e9 + 1.0, 183.5, 183.8, "f", _add(SH, -10.0, 4.0)), (-1e9, -1e9 + 1.0, 183.25, 183.5, "b", _add(SH, 8.0, 9.0)))
        if t < 183.8:
            Pc, g = _pin(Pc, t, x, y, hc, 1, segs)
            gc = g or {}
        if t >= tj + 0.42:
            gc["f"] = gl
        if t >= tj + 1.26:
            gc["b"] = _add(gl, -4.0, 15.0)
        Pc = _follow(Pc, P0, k=0.7)
    elif t < tt + 1.00:
        w = (t - tt) / 1.00
        Pc, xc = _turn_step(Pn["c_both"], Pn["cl0"], w, x, Pn["xc8"], hc)
        facec = 1
        k = _sm(w)                                   # the hands change places on the bunch as it passes over the head
        gc["f"] = _add(gl, 3.0 * k, -15.0 * k)
        gc["b"] = _add(gl, -4.0 * (1.0 - k), 15.0 * (1.0 - k))
    else:
        Pc, xc, facec = Pn["ctrack2"].at(t), Pn["xc8"], -1
        Pc = _follow(Pc, Pn["ctrack2"].at(t - _DT), k=0.7)
        gc["f"] = gl
        gc["b"] = _add(gl, 3.0, -15.0)
    pale = 0.38 * _ramp(t, 183.6, 186.4) * (1.0 - _ramp(t, T["lift"] + 0.1, T["lift"] + 1.3))
    low = _ramp(t, 183.4, 185.0) * (1.0 - _ramp(t, T["lift"], T["lift"] + 1.0))
    quiet = ((182.6, 183.4), (T["lift"] - 0.5, T["lift"] + 1.6), (T["stand"] - 0.6, T["stand"] + 0.6), (tj - 0.2, tj + 1.5),
             (tt - 0.2, tt + 2.2), (tb - 0.2, tp + 0.05))
    hard = _ramp(t, tj + 1.2, tj + 1.5)
    if facec > 0:
        Pc = _live(Pc, t, SC, quiet, breath=1.0 - 0.45 * low + 0.5 * hard, shift=0.5 * (1.0 - hard) + 0.3 * hard)
    else:
        Pc = _live2(Pc, t, SC, _ramp(t, tt + 1.1, tt + 2.1), quiet, breath=1.5, shift=0.3)
    child = Act(Pc, xc, y, facec, gc or None, hc, "child", SC, a=1.0 - pale)
    friend = Act(Pf, xf, y, 1, gf or None, hf, "friend", SF)
    if t < a2 + 0.26 + 0.31:                         # (hand-off B7 is then the same picture to the pixel)
        friend = _flip(friend)
    hl = [] if gl is None else ([gl] if t < tj + 0.42 else ([gl, gc.get("f", gl)] if t < tt - 0.12 else [gc.get("f", gl), gc.get("b", gl)]))
    hr = [] if gr is None else ([gr] if t < tt + 0.05 else [gr, _add(gr, -3.0, -15.0)])
    pts = dict(grip_l=gl, grip_r=gr, hands_l=tuple(hl), hands_r=tuple(hr), shoulder=SH if t < a2 else None)
    opn = 0.0 if gl is None else min(1.0, (gr[0] - gl[0]) / (_B8_GX * (hc + hf) + d + 40.0))
    num = dict(open=opn, lit=_ramp(t, a7, a7 + 0.3), strain=hold, tremble=ktr, a=1.0 - pale)
    return Duet(child, friend, pts, num, "cf" if t < a2 + 0.2 else "fc")


# --------------------------------------------------------------------------
# general duet tools
# --------------------------------------------------------------------------
def look_to(P: Pose, x: float, y: float, h: float, face: int, target, k: float = 1.0, head: float = 0.3) -> Pose:
    """P (a profile pose standing or sitting at the world ground point x, y) with its eyes, and a
    little its head, on a WORLD point: the eye line. k 0..1 brings them there (animate it: the eyes
    lead when you ramp k before you move anything else); head: how much the head nods after them."""
    return _eyes(P, x, y, h, face, target, k, head)


def eye_to_eye(Pc: Pose, Pf: Pose, xc: float, yc: float, xf: float, yf: float, k: float = 1.0, kf: float | None = None,
               hc: float = HC, hf: float = HF, head: float = 0.2):
    """The two looking at each other: each one's eyes on the other's head. The child faces right
    (toward the friend), the friend left. k, kf: how much (the child's, the friend's; let one lead
    by a few frames). Returns (child pose, friend pose)."""
    kf = k if kf is None else kf
    tc = _w(_head_q(Pf), xf, yf, hf, -1)
    tf = _w(_head_q(Pc), xc, yc, hc, 1)
    return _eyes(Pc, xc, yc, hc, 1, tc, k, head), _eyes(Pf, xf, yf, hf, -1, tf, kf, head)


def hold_hands(xc: float, yc: float, xf: float, yf: float, hc: float = HC, hf: float = HF, lift: float = 0.455):
    """Hand in hand: the shared WORLD point of the joined hands for a child standing at (xc, yc) and
    the friend at (xf, yf) to its right, and the two grabs. Returns (point, child grab, friend grab):
    figure(..., HOLD-like pose, face=1, grab=child grab) and figure(..., face=-1, grab=friend grab)
    pin the NEAR hand of each to the point (the child's right in the friend's left)."""
    p = (0.5 * (xc + xf), 0.5 * (yc + yf) - lift * 0.5 * (hc + hf))
    return p, {"f": p}, {"f": p}


@lru_cache(maxsize=16)
def _walk_plan(x0, x1, start, steps, h, m, key0, key1):
    rest0, rest = _RESTS[key0], _RESTS[key1]
    if steps <= 2:
        spec = (("out", rest0, BEAT, walk, m), ("in", rest, BEAT))
    else:
        spec = (("out", rest0, BEAT, walk, m), ("cyc", walk, m, 0.5 * (steps - 2), (steps - 2) * BEAT), ("in", rest, BEAT))
    return _journey(spec, h, start, x0=x0, x1=x1)


def side_by_side(t: float, x0: float, x1: float, start: float, steps: int, ground=None, y: float = FLOOR, gap: float = 170.0,
                 lead: float = 0.5, m: float = 0.8, hc: float = HC, hf: float = HF, x1f: float | None = None) -> Duet:
    """The two walking to the right (or left) side by side, a step a beat, every stance foot
    planted: the child from world x0 to x1 in `steps` steps (the first begins at `start`: give a
    beat), the friend `gap` ahead of it and `lead` beats ahead in time (its feet fall between the
    child's). ground(x) -> y: the line they walk on (hills.ground_y); None: flat at y. x1f: where
    the friend stops (default x1 + gap). Before / after: both stand (STAND, F_STAND).
    num: going (0 / 1)."""
    s = 1.0 if x1 >= x0 else -1.0
    x1f = x1 + s * gap if x1f is None else x1f
    Gc = _walk_plan(x0, x1, start, steps, hc, m, "c", "c")
    Gf = _walk_plan(x0 + s * gap, x1f, start - lead * BEAT, steps, hf, m, "f", "f")
    acts = []
    for G, h, seed, skin in ((Gc, hc, SC, "child"), (Gf, hf, SF, "friend")):
        P, xx, _ = G.at(t)
        P0, xx0, _ = G.at(t - _DT)
        P = _follow(P, P0, G.face * (xx - xx0) / h, 0.0, 0.8)
        if not (G.t0 < t < G.t1):
            P = _live(P, t, seed, shift=0.5)
        P, yy = stand_on(P, xx, G.face, h, ground, y)
        acts.append(Act(P, xx, yy, G.face, None, h, skin, seed))
    return Duet(acts[0], acts[1], {}, dict(going=1.0 if Gc.t0 < t < Gc.t1 or Gf.t0 < t < Gf.t1 else 0.0), "fc")


_RUNCYC = BEAT                           # a run cycle a beat: a footfall on every eighth note
_JUMP_C = JUMP.but(pel=(0.0, 0.50), hf=(0.22, 0.0), hb=(0.16, 0.10), ef=-1.0, eb=1.0, joy=0.6, mouth=0.8, mopen=0.5, ff=(-0.12, 0.22),
                   fb=(0.10, 0.26), hair=1.0, look=(0.40, 0.3))                      # the child's first try: half as bold
_JUMP_F = JUMP.but(mouth=1.3, look=(0.40, 0.35))        # (the rig's: the near arm up and back, the far one up behind the head)


def _run_spec(t0, t1, jumps, rest0, rest, out_dur=0.375, in_dur=0.34):
    """A run from t0 to t1 with jumps: jumps = ((take-off time, air time, height in body units, apex pose), ...)."""
    spec = [("out", rest0, out_dur, run, 0.0)]
    t = t0 + out_dur
    for tj, dur, hgt, pose in jumps:
        if tj > t + 1e-6:
            spec.append(("cyc", run, 0.0, (tj - t) / _RUNCYC, tj - t))
        spec.append(("fly", dur, hgt, pose, None))
        t = tj + dur
    te = t1 - in_dur
    if te > t + 1e-6:
        spec.append(("cyc", run, 0.0, (te - t) / _RUNCYC, te - t))
    spec.append(("in", rest, in_dur))
    return tuple(spec)


def _plan_run(spec, h, face, t0, q, m_lift=0.05):
    """_plan for a run whose jumps land in the nearest contact of the cycle (the land phase None is
    resolved here) and whose last step may start anywhere in the cycle."""
    out, ph = [], 0.0
    for it in spec:
        if it[0] == "cyc":
            ph += it[3]
            out.append(it)
        elif it[0] == "fly":
            land = math.ceil(ph * 2.0 + 0.35) / 2.0           # the next contact but one: the flight spans a step
            out.append(("fly", it[1], it[2], it[3], land))
            ph = land
        elif it[0] == "in":
            near = round(ph * 2.0) / 2.0                      # finish the step that is under way, then stop
            if abs(near - ph) > 1e-6:
                # stretch the last stretch of cycle a little so that it ends on a contact
                k = out[-1]
                out[-1] = ("cyc", k[1], k[2], k[3] + (near - ph), k[4])
                ph = near
            out.append(it)
        else:
            out.append(it)
    return _plan(tuple(out), h, face, t0, q, m_lift)


def _run_journey(spec, h, t0, x0, x1):
    face = 1 if x1 >= x0 else -1
    d1, d2 = _plan_run(spec, h, face, t0, 1.0)[2], _plan_run(spec, h, face, t0, 2.0)[2]
    q = 1.0 + (abs(x1 - x0) / h - d1) / (d2 - d1)
    ph, bases, total, t1, first, last = _plan_run(spec, h, face, t0, q)
    G = _Gait()
    G.x0, G.x1 = x0, x0 + face * h * total
    G.face, G.h, G.ph, G.base, G.t0, G.t1, G.q = face, h, ph, bases, t0, t1, q
    G.ts = [p[0] for p in ph]
    G.rest0, G.rest = first, last
    return G


@lru_cache(maxsize=16)
def _run_plan(x0, x1, t0, t1, jumps, h, who):
    poses = {"c": _JUMP_C, "f": _JUMP_F, "j": JUMP}
    js = tuple((tj, dur, hgt, poses[k]) for tj, dur, hgt, k in jumps)
    return _run_journey(_run_spec(t0, t1, js, _RESTS[who], _RESTS[who]), h, t0, x0, x1)


def run_together(t: float, x0: float, x1: float, t0: float, t1: float, ground=None, y: float = FLOOR, gap: float = 170.0,
                 lead: float = 0.2, jumps_c=(), jumps_f=(), hc: float = HC, hf: float = HF, x1f: float | None = None) -> Duet:
    """The two running side by side from t0 to t1 (a run cycle a beat: a footfall on every eighth
    note), the child from world x0 to x1, the friend `gap` ahead and setting off `lead` seconds
    earlier; the step length adapts to the distance. jumps_c, jumps_f: ((take-off time, air time,
    height in body units, "c" | "f" | "j"), ...) with "c" the child's half-bold jump, "f" the
    friend's, "j" the rig's JUMP. ground(x) -> y as in side_by_side. Act.lift: world units off the
    ground (for the shadow). num: air_c, air_f (the same), speed (world units a second)."""
    s = 1.0 if x1 >= x0 else -1.0
    x1f = x1 + s * gap if x1f is None else x1f
    Gc = _run_plan(x0, x1, t0, t1, tuple(jumps_c), hc, "c")
    Gf = _run_plan(x0 + s * gap, x1f, t0 - lead, t1 - lead, tuple(jumps_f), hf, "f")
    acts, airs = [], []
    for G, h, seed, skin in ((Gc, hc, SC, "child"), (Gf, hf, SF, "friend")):
        P, xx, air = G.at(t)
        P0, xx0, air0 = G.at(t - _DT)
        P = _follow(P, P0, 0.25 * G.face * (xx - xx0) / h, air - air0, 0.8)
        if not (G.t0 < t < G.t1):
            P = _live(P, t, seed, shift=0.5)
        P, yy = stand_on(P, xx, G.face, h, ground, y, air)
        acts.append(Act(P, xx, yy, G.face, None, h, skin, seed, lift=air * h))
        airs.append(air * h)
    return Duet(acts[0], acts[1], {}, dict(air_c=airs[0], air_f=airs[1], speed=abs(x1 - x0) / max(1e-6, t1 - t0)), "fc")


_REST_C = STAND.but(look=(0.44, 0.10), eye=1.0, lid=0.25, mouth=0.1, hair=0.6)
_REST_F = F_STAND.but(mouth=0.8, blush=0.5)
_RESTS = {"c": _REST_C, "f": _REST_F}


# --------------------------------------------------------------------------
# s09 (201.25 to 226.76): the sheet rips; over the first hill; the smile; the ring; hand in hand
# --------------------------------------------------------------------------
S09_T = dict(rip=201.25, look=203.30, go=205.015, hits=ST.HITS_3, house=210.265, push=210.78, on=211.765, back=213.35,
             turn=214.60, smile_f=216.07, smile_c=217.33, join=217.72, ring=ST.T_COLOUR, string=223.5)

# (the arms are left reaching out to where the strands were, past the head and BEHIND it, over = -1 as in B8: the startled faces are seen)
_THROWN = Pose(pel=(-0.045, 0.384), lean=-0.10, bend=-0.08, neck=0.04, look=(0.40, 0.45), eye=1.3, lift=0.9, mouth=-0.1, mopen=0.7,
               hf=(0.285, 0.12), hb=(0.25, 0.20), ef=1.0, eb=1.0, ff=(0.07, 0.05), fb=(-0.15, 0.0), af=0.5, hair=1.0, sway=-0.8, open=0.6,
               over=-1.0)
_CATCH = Pose(pel=(-0.03, 0.360), lean=0.16, bend=0.20, neck=-0.16, look=(0.42, 0.2), eye=1.15, lift=0.5, mouth=0.0, mopen=0.5,
              hf=(0.20, -0.12), hb=(0.10, -0.22), ff=(0.04, 0.0), fb=(-0.10, 0.0), hair=0.8, open=0.7)
_PANT = Pose(pel=(-0.03, 0.384), lean=0.36, bend=0.28, neck=-0.30, look=(0.46, 0.22), eye=1.05, lid=0.3, lift=0.3, mouth=0.05,
             mopen=0.5, hf=(0.10, -0.235), hb=(0.12, -0.23), ff=(0.03, 0.0), fb=(-0.06, 0.0), hair=0.7, open=0.6)
_C_FACE9 = _REST_C.but(neck=-0.08, look=(0.46, 0.12), gaze=(0.35, 0.1), mouth=0.0, mopen=0.2, lift=0.2, open=0.9)
_F_WAITL = F_STAND.but(neck=-0.06, look=(0.46, 0.02), gaze=(0.35, -0.05), mouth=0.7, tilt=0.06, blush=0.5)
_C_SMILE = _C_FACE9.but(eye=1.0, lid=0.3, joy=0.3, mouth=0.55, mopen=0.0, blush=0.6, spark=0.6, lift=0.2, neck=-0.12)
_C_B9 = HOLD.but(look=(0.46, 0.12), gaze=(0.3, 0.05), eye=1.0, lid=0.3, joy=0.3, mouth=0.55, blush=0.6, spark=0.6, hair=0.9, neck=-0.1)
_F_B9 = HOLD.but(look=(0.46, 0.06), gaze=(0.3, 0.0), joy=0.6, mouth=1.15, mopen=0.3, blush=0.9, lift=0.2)
_STOOP = Pose(pel=(-0.07, 0.300), lean=0.50, bend=0.30, neck=-0.46, look=(0.44, -0.2), eye=1.0, lid=0.2, mouth=0.2, hf=(0.12, -0.26),
              hb=(0.10, -0.28), ff=(0.03, 0.0), fb=(-0.04, 0.0), hair=0.7, open=0.6)


def _b9_places(x, d, ground, y):
    xf = x + d
    return x, _gy(ground, x, y), xf, _gy(ground, xf, y)


def hold_B9(t: float, x: float = ST.X9, y: float = FLOOR, d: float = 180.0, ground=None, hc: float = HC, hf: float = HF) -> Duet:
    """The rest state of hand-off B9 (226.76): the two standing hand in hand on the hill, the child at
    x (facing the friend, a small smile, its tufts up), the friend at x + d (smiling); the child's
    far hand holds the string. ground(x) -> y: the hill's contour (hills.ground_y); None: flat at y.
    pts: hands (the joined hands), string (the child's hand that holds the string)."""
    xc, yc, xf, yf = _b9_places(x, d, ground, y)
    H, gc, gf = hold_hands(xc, yc, xf, yf, hc, hf)
    Pc, yc = stand_on(_live(_C_B9, t, SC, shift=0.5), xc, 1, hc, ground, y)
    Pf, yf = stand_on(_live(_F_B9, t, SF, shift=0.5), xf, -1, hf, ground, y)
    child = Act(Pc, xc, yc, 1, gc, hc, "child", SC)
    return Duet(child, Act(Pf, xf, yf, -1, gf, hf, "friend", SF), dict(hands=H, ring=H, string=_hand_of(child, "b")),
                dict(joined=1.0, smile_c=1.0, smile_f=1.0, string=1.0, push=1.0, thrown=0.0), "fc")


@lru_cache(maxsize=4)
def _s09_plan(x, d, hc, hf, x9, hx, T):
    T = dict(T)
    rip, look, go = T["rip"], T["look"], T["go"]
    h1, h2, h3 = T["hits"]
    th, tp, on = T["house"], T["push"], T["on"]
    Pc8, xc8, Pf8, xf8, gl8, gr8 = _b8_poses(x, 0.0, d, hc, hf)
    xa_c, xa_f = xc8 + 6.0, xf8 - 6.0
    # ---- thrown back, catching the balance, the look
    c_up = _PANT.but(lean=0.14, bend=0.12, neck=-0.34, look=(0.44, 0.55), mopen=0.35, lift=0.5, hf=(0.05, -0.30), hb=(0.07, -0.30))
    cA = _Track(Pc8, (rip + 0.02, 0.16, _THROWN, "jolt"), (rip + 0.24, 0.30, _CATCH, "land"), (rip + 0.75, 0.55, _PANT, "body"),
                (rip + 1.55, 0.45, c_up, "soft"))
    c_r = _C_FACE9.but(mopen=0.3, lift=0.4, eye=1.1)
    cA2 = _Track(c_r, (look + 0.80, 0.36, _C_FACE9, "soft"), (go - 0.46, 0.40, _REST_C, "soft"))
    f_hips = F_STAND.but(neck=-0.32, look=(0.42, 0.6), mouth=0.8, mopen=0.4, lift=0.4, hf=(-0.03, -0.24), hb=(0.03, -0.24), ef=-1.0,
                         ff=(0.03, 0.0), fb=(-0.04, 0.0))
    f_half = F_STAND.but(turn=0.9, hturn=0.5, open=1.0, look=(0.25, 0.05), mouth=1.0, mopen=0.4, joy=0.3, blush=0.7, hfz=0.03, hbz=0.03,
                         hf=(0.0, -0.30), hb=(0.0, -0.30), ff=(0.0, 0.0), fb=(0.0, 0.0), ffz=0.02, fbz=0.02)
    fA = _Track(Pf8, (rip + 0.06, 0.16, _THROWN.but(mouth=0.2), "jolt"), (rip + 0.30, 0.30, _CATCH.but(mouth=0.4), "land"),
                (rip + 0.85, 0.60, f_hips, "body"), (look + 0.16, 0.50, f_half, "body"), (go - 0.375 - 0.52, 0.48, _REST_F, "body"))
    XC = _Path((rip + 0.02, (xc8, 0.0)), (rip + 0.50, (xa_c, 0.0), "o"))
    XF = _Path((rip + 0.06, (xf8, 0.0)), (rip + 0.56, (xa_f, 0.0), "o"))
    # ---- the walk over the hill, the house, on to the top
    Gc1 = _walk_plan(xa_c, hx - 120.0, go, 7, hc, 0.8, "c", "c")
    Gf1 = _walk_plan(xa_f, hx + 120.0, go - 0.375, 7, hf, 0.8, "f", "f")
    Gc2 = _walk_plan(hx - 120.0, x9, on, 2, hc, 0.85, "c", "c")
    Gf2 = _walk_plan(hx + 120.0, x9 + d, on, 2, hf, 0.85, "f", "f")
    c_see = _REST_C.but(neck=0.22, look=(0.44, -0.45), lift=0.3, mopen=0.15, bend=0.08)
    cH = _Track(_REST_C, (th + 0.05, 0.22, c_see, "soft"), (th + 0.28, 0.24, _STOOP, "body"),
                (tp + 0.46, 0.34, _REST_C.but(mouth=0.2, look=(0.46, 0.12)), "body"))
    f_stoop = _STOOP.but(mouth=0.8, blush=0.5)
    fH = _Track(_F_WAITL, (th + 0.10, 0.18, _F_WAITL.but(neck=0.2, look=(0.44, -0.45)), "soft"), (th + 0.30, 0.22, f_stoop, "body"))
    # ---- on the top
    c_backS = _mirror(_REST_C.but(neck=0.06, look=(0.42, -0.18), gaze=(0.3, -0.2), brow=0.25, mouth=-0.05, hair=0.5, bend=0.06))
    ts, tj, tr, tg = T["smile_c"], T["join"], T["ring"], T["string"]
    c_trem = _C_FACE9.but(mouth=0.2, mopen=0.0, lift=0.3, eye=1.05, lid=0.28, brow=0.1, blush=0.3)
    c_join = _C_SMILE.but(hf=HOLD["hf"], hb=HOLD["hb"], ef=HOLD["ef"], eb=HOLD["eb"], hair=0.9, open=1.0)
    c_look1 = _C_B9.but(turn=0.25, hturn=0.25, look=(0.30, -0.25), gaze=(0.0, -0.4), lift=0.4, mopen=0.2, eye=1.1)
    c_look2 = _C_B9.but(turn=0.2, hturn=0.1, neck=-0.3, look=(0.40, 0.6), gaze=(0.2, 0.6), lift=0.5, mopen=0.25, eye=1.1)
    c_str = _C_B9.but(turn=0.3, hturn=0.25, neck=-0.22, look=(0.08, 0.5), gaze=(-0.8, 0.5), hb=(-0.16, 0.02), eb=1.0, lift=0.3)
    cT = _Track(_C_FACE9, (ts - 0.78, 0.45, c_trem, "soft"), (ts - 0.22, 0.24, _C_SMILE, "soft"), (tj - 0.36, 0.34, c_join, "hand"),
                (tr + 0.30, 0.60, c_look1), (tr + 2.20, 0.60, _C_B9, "soft"), (tr + 3.60, 0.60, c_look2), (tg - 0.80, 0.50, _C_B9, "soft"),
                (tg - 0.10, 0.50, c_str, "hand"), (tg + 0.70, 0.60, _C_B9, "soft"))
    f_peek = _REST_F.but(turn=0.3, hturn=0.5, look=(0.2, 0.0), mouth=0.6)
    f_smile = _F_WAITL.but(look=(0.46, 0.06), neck=-0.12, joy=0.8, mouth=1.4, mopen=0.55, blush=1.0, lift=0.3, tilt=0.03, pel=(0.0, 0.420),
                           af=-0.3, ab=-0.3)
    f_off = _F_B9.but(joy=0.7, mouth=1.3, mopen=0.45, blush=1.0)
    f_look1 = _F_B9.but(turn=0.25, hturn=0.25, look=(0.30, -0.2), gaze=(0.0, -0.4), mopen=0.5, lift=0.5)
    f_look2 = _F_B9.but(turn=0.2, neck=-0.3, look=(0.40, 0.6), gaze=(0.2, 0.6), mopen=0.5, lift=0.5)
    fT = _Track(_F_WAITL, (T["smile_f"], 0.90, f_smile), (tj - 0.72, 0.36, f_off, "hand"), (tr + 0.20, 0.60, f_look1),
                (tr + 2.00, 0.60, _F_B9, "soft"), (tr + 3.40, 0.60, f_look2), (tg - 0.60, 0.50, _F_B9, "soft"))
    return dict(T=T, cA=cA, cA2=cA2, fA=fA, XC=XC, XF=XF, Gc1=Gc1, Gf1=Gf1, Gc2=Gc2, Gf2=Gf2, cH=cH, fH=fH, cT=cT, fT=fT, c_up=c_up,
                c_r=c_r, c_backS=c_backS, f_peek=f_peek, f_stoop=f_stoop, xa_c=xa_c, xa_f=xa_f, xc8=xc8, xf8=xf8)


def _layer_walk(P, t, T, who):
    """What the two do in passing while they walk: a look up at the emptied balloons, a look down
    and a wave back to the small children (the friend first, the child a few frames later)."""
    h1, h2, h3 = T["hits"]
    lag_ = 0.0 if who == "f" else 0.12
    k = _ramp(t, h1 + 0.05 + lag_, h1 + 0.40 + lag_) * (1.0 - _ramp(t, h1 + 1.0 + lag_, h1 + 1.4 + lag_))
    if k > 0.0:
        P = P.but(look=_lerp(P["look"], (0.40, 0.62), k), gaze=_lerp(P["gaze"], (0.1, 0.6), k), neck=P["neck"] - 0.22 * k,
                  lift=P["lift"] + 0.4 * k, mopen=P["mopen"] + 0.2 * k)
    if who == "f":
        k = _ramp(t, h2 + 0.12, h2 + 0.42) * (1.0 - _ramp(t, h2 + 0.78, h2 + 1.08))
        if k > 0.0:
            s = math.sin(2.0 * math.pi * 2.6 * (t - h2))
            P = P.but(hf=_lerp(P["hf"], (0.25 + 0.035 * s, -0.01), k), ef=P["ef"] + (1.0 - P["ef"]) * k, look=_lerp(P["look"], (0.50, -0.30), k),
                      gaze=_lerp(P["gaze"], (0.3, -0.5), k), mouth=P["mouth"] + 0.4 * k, joy=P["joy"] + 0.3 * k)
    else:
        k = _ramp(t, h2 + 0.50, h2 + 0.80) * (1.0 - _ramp(t, h2 + 1.12, h2 + 1.42))
        if k > 0.0:
            s = math.sin(2.0 * math.pi * 2.6 * (t - h2))
            P = P.but(hf=_lerp(P["hf"], (0.21 + 0.025 * s, -0.04), k), ef=P["ef"] + (1.0 - P["ef"]) * k, look=_lerp(P["look"], (0.50, -0.30), k),
                      gaze=_lerp(P["gaze"], (0.3, -0.5), k), mouth=P["mouth"] + 0.15 * k, lift=P["lift"] + 0.2 * k)
    return P


def s09(t: float, x: float = ST.X5, y: float = FLOOR, d: float = 180.0, x9: float = ST.X9, house_x: float | None = None,
        ground=None, hc: float = HC, hf: float = HF, **times) -> Duet:
    """The last chorus. From hold_B8 to hold_B9. Cue times: S09_T.

    At `rip` the strands go slack: both are thrown back a step (toward each other), catch their
    balance, stand panting; at `look` the child turns round toward the friend (through facing us),
    the friend half turns and grins; it nods toward the hill. From `go` they walk right, a step a
    beat, the friend 170 ahead and half a beat ahead in time, seven steps to the small house at
    house_x; on the way they look up after the emptied balloons (hits[0]) and wave back to the small
    children (hits[1]: the friend first, the child a small wave after it). At the house (it draws
    on at `house`) they stop either side of it, the friend turns round, both stoop and push the
    halves together with four hands (push .. push + 0.4); from `on` two steps to the top (x9 and
    x9 + d). The child turns to look back (back), then turns to the friend (turn); the friend's
    smile opens (smile_f, 0.9 s); the child's first small smile (smile_c), its tufts stand up; the
    friend holds out a hand, the child takes it (join); the ring opens from the joined hands (ring).
    They look about them, hand in hand; the child takes the string in its free hand (string).

    x, y, d: as hold_B8 (the place of the curtain); x9: where the child stands at the end; house_x:
    world x of the small house (default x9 - 120); ground(x) -> y: the hill's contour
    (hills.ground_y); None: flat at y. Both are written for whichever way they face (Act.face).
    pts: hands (the friend's offered hand, then the joined hands), ring (the same from `join`: the
    ring's centre), house_l, house_r (the two hands of each on the house's walls, while they push),
    string (the child's far hand, from `string`). num: thrown (0..1..0), push (0..1: the halves
    together), smile_f, smile_c (0..1), joined, string (0..1: it has it), tufts (the child's hair)."""
    T = dict(S09_T)
    T.update(times)
    if t < T["rip"] + 0.02:
        D = hold_B8(t, x, y, d, hc, hf)
        D.pts.update(hands=None, ring=None, house_l=None, house_r=None, string=None)
        D.num.update(thrown=0.0, push=0.0, smile_f=0.0, smile_c=0.0, joined=0.0, string=0.0)
        return D
    if t >= T["string"] + 1.45:
        return hold_B9(t, x9, y, d, ground, hc, hf)
    hx = x9 - 120.0 if house_x is None else float(house_x)
    Pn = _s09_plan(x, d, hc, hf, x9, hx, tuple(sorted(T.items())))
    rip, look, go, th, tp, on = T["rip"], T["look"], T["go"], T["house"], T["push"], T["on"]
    tb, tt, tj, tr, tg = T["back"], T["turn"], T["join"], T["ring"], T["string"]
    gc = gf = None
    pts = dict(hands=None, ring=None, house_l=None, house_r=None, string=None)
    push = _ramp(t, tp, tp + 0.40)
    mv_c = mv_f = True
    # ---------------- the child
    if t < look:
        Pc, xc, fc = Pn["cA"].at(t), Pn["XC"](t)[0], -1
        Pc = _follow(Pc, Pn["cA"].at(t - _DT), k=0.8)
    elif t < look + 0.65:
        Pc, xc, fc = turn_round(Pn["c_up"], _mirror(Pn["c_r"]), (t - look) / 0.65), Pn["xa_c"], -1
    elif t < go:
        Pc, xc, fc = Pn["cA2"].at(t), Pn["xa_c"], 1
        mv_c = Pn["cA2"].busy(t)
    elif t < th:
        G = Pn["Gc1"]
        Pc, xc, _ = G.at(t)
        P0, x0_, _ = G.at(t - _DT)
        Pc, fc = _follow(_layer_walk(Pc, t, T, "c"), P0, (xc - x0_) / hc, 0.0, 0.8), 1
    elif t < on:
        Pc, xc, fc = Pn["cH"].at(t), hx - 120.0, 1
        Pc = _follow(Pc, Pn["cH"].at(t - _DT), k=0.7)
    elif t < tb:
        G = Pn["Gc2"]
        Pc, xc, _ = G.at(t)
        P0, x0_, _ = G.at(t - _DT)
        Pc, fc = _follow(Pc, P0, (xc - x0_) / hc, 0.0, 0.8), 1
    elif t < tb + 0.6:
        Pc, xc, fc = turn_round(_REST_C, Pn["c_backS"], (t - tb) / 0.6), x9, 1
    elif t < tt:
        Pc, xc, fc = Pn["c_backS"], x9, 1
        mv_c = False
    elif t < tt + 0.65:
        Pc, xc, fc = turn_round(Pn["c_backS"], _C_FACE9, (t - tt) / 0.65), x9, 1
    else:
        Pc, xc, fc = Pn["cT"].at(t), x9, 1
        Pc = _follow(Pc, Pn["cT"].at(t - _DT), k=0.7)
        Pc = Pc.but(hair=max(Pc["hair"], 0.6 + 0.3 * _ramp(t, T["smile_c"], T["smile_c"] + 0.42)))
        mv_c = Pn["cT"].busy(t)
    # ---------------- the friend
    tf1 = go - 0.375
    if t < tf1:
        Pf, xf, ff = Pn["fA"].at(t), Pn["XF"](t)[0], 1
        Pf = _follow(Pf, Pn["fA"].at(t - _DT), k=0.8)
        mv_f = Pn["fA"].busy(t)
    elif t < th - 0.375:
        G = Pn["Gf1"]
        Pf, xf, _ = G.at(t)
        P0, x0_, _ = G.at(t - _DT)
        Pf, ff = _follow(_layer_walk(Pf, t, T, "f"), P0, (xf - x0_) / hf, 0.0, 0.8), 1
    elif t < th + 0.10:
        Pf, xf, ff = turn_round(_REST_F, _mirror(_F_WAITL), (t - (th - 0.375)) / 0.475), hx + 120.0, 1
    elif t < tp + 0.46:
        Pf, xf, ff = Pn["fH"].at(t), hx + 120.0, -1
        Pf = _follow(Pf, Pn["fH"].at(t - _DT), k=0.7)
    elif t < on:
        Pf, xf, ff = turn_round(Pn["f_stoop"], _mirror(_REST_F), (t - (tp + 0.46)) / (on - tp - 0.46)), hx + 120.0, -1
    elif t < tb + 0.35:
        G = Pn["Gf2"]
        Pf, xf, _ = G.at(t)
        P0, x0_, _ = G.at(t - _DT)
        Pf, ff = _follow(Pf, P0, (xf - x0_) / hf, 0.0, 0.8), 1
        if t >= tb + 0.10:
            Pf = mixp(Pf, Pn["f_peek"], _ramp(t, tb + 0.10, tb + 0.35))
    elif t < tb + 0.65:
        Pf, xf, ff = Pn["f_peek"], x9 + d, 1
    elif t < tb + 1.20:
        Pf, xf, ff = turn_round(Pn["f_peek"], _mirror(_F_WAITL), (t - (tb + 0.65)) / 0.55), x9 + d, 1
    else:
        Pf, xf, ff = Pn["fT"].at(t), x9 + d, -1
        Pf = _follow(Pf, Pn["fT"].at(t - _DT), k=0.8)
        mv_f = Pn["fT"].busy(t)
    # ---------------- the ground under them, the shared points
    yc, yf = _gy(ground, xc, y), _gy(ground, xf, y)
    if th + 0.28 < t < tp + 0.70:                    # four hands on the house
        yh = _gy(ground, hx, y)
        tr_ = 12.0 * push
        hl = ((hx - 50.0 + tr_, yh - 70.0), (hx - 50.0 + tr_, yh - 48.0))
        hr = ((hx + 50.0 - tr_, yh - 72.0), (hx + 50.0 - tr_, yh - 46.0))
        if th + 0.5 <= t <= tp + 0.46:
            pts["house_l"], pts["house_r"] = hl, hr
        Pc, gc = _pin(Pc, t, xc, yc, hc, fc, ((th + 0.28, th + 0.50, tp + 0.46, tp + 0.66, "f", hl[0]),
                                              (th + 0.30, th + 0.52, tp + 0.46, tp + 0.68, "b", hl[1])))
        if ff < 0:
            Pf, gf = _pin(Pf, t, xf, yf, hf, ff, ((th + 0.30, th + 0.52, tp + 0.46, tp + 0.47, "f", hr[0]),
                                                  (th + 0.32, th + 0.54, tp + 0.46, tp + 0.47, "b", hr[1])))
    H, g1, g2 = hold_hands(x9, _gy(ground, x9, y), x9 + d, _gy(ground, x9 + d, y), hc, hf)
    if t >= tj - 0.72:
        if ff < 0:
            Pf, gf = _pin(Pf, t, xf, yf, hf, ff, ((tj - 0.72, tj - 0.40, 1e9, 1e9 + 1.0, "f", H),))
        if t >= tj - 0.40:
            pts["hands"] = H
        Pc, gc = _pin(Pc, t, xc, yc, hc, fc, ((tj - 0.36, tj, 1e9, 1e9 + 1.0, "f", H),))
        if t >= tj:
            pts["ring"] = H
    # ---------------- alive, on the ground
    late = _ramp(t, tr + 1.0, tr + 2.5)
    quiet = ((rip + 0.02, look + 1.2), (tt - 0.2, T["join"] + 0.6), (tr - 0.1, tr + 1.2))
    pant = 1.0 - _ramp(t, rip + 1.2, go)
    sh0 = 0.3 * (1.0 - _ramp(t, rip, rip + 0.4))         # (hold_B8 breathes 1.5 deep and shifts 0.3: leave it without a step)
    ph = _breaths(t, rip + 0.3, go, 2.0, "o")            # panting: two breaths more than at rest, most of them at once
    Pc = _live(Pc, t, SC, quiet if not mv_c else ((t - 1.0, t + 1.0),), breath=1.0 + 0.5 * pant + 1.1 * pant * _ramp(t, rip + 0.6, rip + 1.0),
               shift=sh0 + 0.5 * late, phase=ph)
    Pf = _live(Pf, t, SF, quiet if not mv_f else ((t - 1.0, t + 1.0),), breath=1.0 + 0.5 * pant + 0.9 * pant * _ramp(t, rip + 0.6, rip + 1.0),
               shift=sh0 + 0.5 * late, phase=ph)
    Pc, yc = stand_on(Pc, xc, fc, hc, ground, y)
    Pf, yf = stand_on(Pf, xf, ff, hf, ground, y)
    child = Act(Pc, xc, yc, fc, gc, hc, "child", SC)
    friend = Act(Pf, xf, yf, ff, gf, hf, "friend", SF)
    if t >= tg - 0.1:
        pts["string"] = _hand_of(child, "b")
    num = dict(thrown=_bell(t, rip, 0.7), push=push, smile_f=_ramp(t, T["smile_f"], T["smile_f"] + 0.9),
               smile_c=_ramp(t, T["smile_c"] - 0.2, T["smile_c"] + 0.15), joined=1.0 if t >= tj else 0.0,
               string=_ramp(t, tg + 0.3, tg + 0.6), tufts=Pc["hair"])
    return Duet(child, friend, pts, num, "fc")


# --------------------------------------------------------------------------
# s10 (226.76 to 244.50): running over the hills, the jumps, in the grass; the friend goes home
# --------------------------------------------------------------------------
S10_T = dict(part=227.0, run=227.515, jumps=(229.765, 232.765, 233.69), drop=235.75, up=238.75, point=239.5, wave=240.55,
             leave=241.765, alone=243.6)

_B10 = STAND.but(look=(0.42, 0.04), eye=1.0, lid=0.3, mouth=0.4, blush=0.4, hair=0.8, hf=(0.06, -0.275), hb=(0.03, -0.31), neck=-0.04,
                 open=0.8)                                                           # alone, at ease, facing left: the string in its near hand
_RESTS["b10"] = _B10
# the hand that holds the string (the child's far hand while it faces right) stays low BEHIND its hip all through
# s10, as in HOLD: the string then rises behind its head (from a hand before the body it would cross the face)
_STR = dict(hb=HOLD["hb"], eb=HOLD["eb"])
_RESTS["cs"] = _REST_C.but(**_STR)
_FLOP = Pose(pel=(-0.207, 0.052), lean=-0.30, bend=0.12, neck=-0.26, look=(0.40, 0.4), eye=0.9, joy=1.0, mouth=1.0, mopen=0.8, blush=0.9,
             hf=(-0.10, -0.235), hb=(-0.15, -0.225), ef=1.0, eb=1.0, ff=(0.13, 0.0), fb=(0.17, 0.0), af=0.5, ab=0.5, hair=1.0, open=0.6,
             front=1.0)                                                              # dropped in the grass: legs out, leaning back on its hands
_SITG = _FLOP.but(lean=0.10, bend=0.26, neck=-0.10, look=(0.46, 0.06), joy=0.6, mouth=0.9, mopen=0.4, hf=(0.20, -0.09), hb=(0.16, -0.11),
                  ef=-1.0, eb=-1.0, ff=(0.10, 0.0), fb=(0.14, 0.0), af=0.0, ab=0.0)


def hold_B10(t: float, x: float = ST.X10, y: float = FLOOR, ground=None, hc: float = HC) -> Duet:
    """The rest state of hand-off B10 (244.50): the child alone at x, facing left, standing at ease,
    the string in its near hand (pts["string"]). friend is None."""
    P, yy = stand_on(_live(_B10, t, SC, shift=0.5), x, -1, hc, ground, y)
    child = Act(P, x, yy, -1, None, hc, "child", SC)
    return Duet(child, None, dict(string=_hand_of(child, "f")), dict(air_c=0.0, air_f=0.0, gone=1.0), "fc")


@lru_cache(maxsize=4)
def _s10_plan(x9, x10, d, hc, hf, T):
    T = dict(T)
    j1, j2, j3 = T["jumps"]
    tr, td, tu, tp, tw, tl, ta = T["run"], T["drop"], T["up"], T["point"], T["wave"], T["leave"], T["alone"]
    lead = 0.125
    Gc = _run_plan(x9, x10, tr, td - 0.08, ((j2 - 0.14, 0.50, 0.20, "c"), (j3 - 0.14, 0.54, 0.27, "j")), hc, "cs")
    Gf = _run_plan(x9 + d, x10 + d, tr - lead, td - 0.08 - lead, ((j1 - 0.14, 0.52, 0.27, "f"), (j3 - 0.14, 0.56, 0.29, "f")), hf, "f")
    rc = _RESTS["cs"]
    c0 = _Track(_C_B9, (T["part"] - 0.06, 0.30, rc.but(mouth=0.7, joy=0.4, lift=0.4, hair=0.9, blush=0.6), "soft"),
                (T["part"] + 0.26, 0.22, rc, "soft"))
    f_bounce = _F_B9.but(pel=(0.0, 0.392), bend=0.1, mouth=1.3, mopen=0.6, joy=0.7, lift=0.4)
    f0 = _Track(_F_B9, (226.80, 0.17, f_bounce, "soft"))
    # the child waves back as the friend waved: turned toward us, the whole outer arm out at its side (an arm
    # raised in a profile lies across the big face, or hides behind the head)
    c_wave = _swing(_C_FACE9.but(turn=0.62, hturn=-0.30, open=1.0, mouth=0.7, joy=0.3, blush=0.6, hair=0.9, mopen=0.2, neck=-0.10,
                                 look=(0.40, 0.14), ffz=0.02, fbz=0.02, **_STR), 0.95, "f", 1.0, 0.6)
    sit_ = dict(hb=(-0.10, -0.245), eb=1.0)          # sitting: the string hand rests on the grass behind it (the arm a little bent)
    c_laugh = _SITG.but(joy=1.0, mopen=0.7, neck=-0.2, look=(0.46, 0.2), **sit_)
    c_calm = _SITG.but(joy=0.4, mouth=0.7, mopen=0.15, eye=1.0, **sit_)
    cS = _Track(rc, (td, 0.30, _FLOP, "land"), (td + 1.0, 0.50, c_laugh, "body"), (td + 2.1, 0.50, c_calm, "soft"),
                (tu + 0.25, 0.55, rc.but(mouth=0.6, blush=0.5, hair=0.9), "body"),
                (tp + 0.45, 0.40, rc.but(neck=-0.22, look=(0.44, 0.5), lift=0.4, mouth=0.4, hair=0.9), "act"),
                (tp + 1.05, 0.28, _C_FACE9.but(mouth=0.5, joy=0.2, blush=0.5, hair=0.9, mopen=0.0, **_STR), "soft"),
                (tw + 0.35, 0.35, c_wave, "hand"),
                (tl + 0.75, 1.05, rc.but(mouth=0.4, blush=0.4, hair=0.85, look=(0.46, 0.06)), "slow"))
    f_flop = _FLOP.but(mouth=1.4)
    f_laugh = _SITG.but(joy=1.0, mouth=1.4, mopen=0.8, neck=-0.2)
    f_point = _swing(F_STAND.but(turn=0.8, hturn=-0.45, open=1.0, look=(0.36, 0.06), mouth=1.0, mopen=0.3, joy=0.3, hb=(0.0, -0.30),
                                 hbz=0.02, ff=(-0.02, 0.0), fb=(0.02, 0.0), ffz=0.02, fbz=0.02), 1.30, "f", 1.0, 0.4)
    f_wave = _F_WAVE.but(hb=(0.0, -0.29), hbz=0.03, mopen=0.4, mouth=1.2, joy=0.5, look=(0.36, 0.12), hturn=-0.3)
    fS = _Track(f_flop, (td + 0.9, 0.50, f_laugh, "body"), (td + 2.0, 0.50, _SITG.but(mouth=1.1, joy=0.5, mopen=0.2), "soft"),
                (tu, 0.50, _F_WAITL, "body"), (tp, 0.40, f_point, "hand"), (tw - 0.30, 0.30, f_wave, "hand"))
    Gl = _walk_plan(x10 + d, x10 + d + 760.0, tl, 7, hf, 0.85, "f", "f")
    return dict(T=T, Gc=Gc, Gf=Gf, c0=c0, f0=f0, cS=cS, fS=fS, f_flop=f_flop, f_wave=f_wave, Gl=Gl, lead=lead)


def s10(t: float, x9: float = ST.X9, x10: float = ST.X10, d: float = 180.0, ground=None, y: float = FLOOR, hc: float = HC,
        hf: float = HF, **times) -> Duet:
    """The outro. From hold_B9 to hold_B10. Cue times: S10_T.

    The hands part (part), the friend turns and is off; they run right over the hills from `run`
    (a run cycle a beat, the friend a little ahead), about 3400 world units; the friend jumps on
    jumps[0], the child tries it on jumps[1], both jump on jumps[2]. At `drop` they drop into the
    grass where they stop (the child at x10, the friend at x10 + d, turning to face it), out of
    breath, laughing. At `up` they stand (the friend first); the friend points home with a whole
    arm (point), waves (wave: an extreme of its swing falls on 241.01), turns and walks off to the
    right from `leave`, looking back once over its shoulder, its line losing pressure (friend.a;
    friend is None once it is gone). The child looks where it points, waves back (turned toward us,
    the whole outer arm out at its side), lets its arm come down slowly, and at `alone` turns to face
    left (Act.face becomes -1 in the middle of that turn).
    ground(x) -> y: the hills' contour (hills.ground_y); None: flat at y.
    pts: hands (the joined hands until `part`), string (the hand that holds the string: the child's
    far hand; its near hand once it faces left). num: air_c, air_f (world units off the ground),
    sit (0..1), laugh (0..1), gone (0..1: the friend leaving), speed (world units a second), left
    (0..1 through the child's turn to the left: swing the tangle's lean over with it)."""
    T = dict(S10_T)
    T.update(times)
    if t <= 226.76:
        D = hold_B9(t, x9, y, d, ground, hc, hf)
        D.num.update(air_c=0.0, air_f=0.0, sit=0.0, laugh=0.0, gone=0.0, speed=0.0, left=0.0)
        return D
    if t >= T["alone"] + 0.62:
        D = hold_B10(t, x10, y, ground, hc)
        D.num.update(sit=0.0, laugh=0.0, speed=0.0, left=1.0)
        D.pts["hands"] = None
        return D
    Pn = _s10_plan(x9, x10, d, hc, hf, tuple(sorted(T.items())))
    tr, td, tu, tp, tw, tl, ta = T["run"], T["drop"], T["up"], T["point"], T["wave"], T["leave"], T["alone"]
    j1, j2, j3 = T["jumps"]
    lead = Pn["lead"]
    gc = gf = None
    air_c = air_f = 0.0
    pts = dict(hands=None, string=None)
    H, g1, g2 = hold_hands(x9, _gy(ground, x9, y), x9 + d, _gy(ground, x9 + d, y), hc, hf)
    # ---------------- the child
    string_hand = "b"
    if t < tr:
        Pc, xc, fc = Pn["c0"].at(t), x9, 1
        if t < T["part"] + 0.14:
            Pc, gc = _pin(Pc, t, xc, _gy(ground, xc, y), hc, 1, ((-1e9, -1e9 + 1.0, T["part"], T["part"] + 0.14, "f", H),))
            pts["hands"] = H if t < T["part"] else None
    elif t < td:
        G = Pn["Gc"]
        Pc, xc, air_c = G.at(t)
        P0, x0_, a0_ = G.at(t - _DT)
        k = _ramp(t, j1 - 0.05, j1 + 0.2) * (1.0 - _ramp(t, j1 + 0.7, j1 + 1.1))             # it watches the friend's jump
        if k > 0.0:
            Pc = Pc.but(look=_lerp(Pc["look"], (0.50, 0.5), k), lift=Pc["lift"] + 0.6 * k, eye=Pc["eye"] + 0.2 * k, joy=Pc["joy"] * (1.0 - 0.6 * k))
        # (the far hand holds the string: low and behind it, also in the jumps, or the string would cross its face)
        Pc, fc = _follow(Pc.but(hb=_lerp(Pc["hb"], _STR["hb"], 0.9), eb=_STR["eb"]), P0, 0.25 * (xc - x0_) / hc, air_c - a0_, 0.8), 1
    elif t < ta:
        Pc, xc, fc = Pn["cS"].at(t), x10, 1
        Pc = _follow(Pc, Pn["cS"].at(t - _DT), k=0.7)
        kw = _ramp(t, tw + 0.6, tw + 0.8) * (1.0 - _ramp(t, tl + 0.75, tl + 1.05))            # waving back
        if kw > 0.0:
            s = math.sin(2.0 * math.pi * (t - beat(0)) / BEAT)
            Pc = _swing(Pc, 0.92 + 0.34 * s, "f", kw, 0.6)
    else:
        Pc, xc, fc = turn_round(Pn["cS"].end(), _mirror(_B10), (t - ta) / 0.55), x10, 1
    # ---------------- the friend
    friend = None
    xf, ff, fa = x10 + d, -1, 1.0
    if t < T["part"]:
        Pf, xf, ff = Pn["f0"].at(t), x9 + d, -1
        gf = g2
    elif t < T["part"] + 0.36:
        Pf, xf, ff = turn_round(Pn["f0"].end(), _mirror(_REST_F), (t - T["part"]) / 0.36), x9 + d, -1
        Pf, gf = _pin(Pf, t, xf, _gy(ground, xf, y), hf, -1, ((-1e9, -1e9 + 1.0, T["part"], T["part"] + 0.12, "f", H),))
    elif t < td - lead:
        G = Pn["Gf"]
        Pf, xf, air_f = G.at(t)
        P0, x0_, a0_ = G.at(t - _DT)
        k = _ramp(t, j2 + 0.25, j2 + 0.45) * (1.0 - _ramp(t, j2 + 0.75, j2 + 0.95))           # it looks back at the child's jump
        if k > 0.0:
            Pf = Pf.but(hturn=Pf["hturn"] + 0.5 * k, turn=Pf["turn"] + 0.25 * k, mopen=Pf["mopen"] + 0.3 * k)
        Pf, ff = _follow(Pf, P0, 0.25 * (xf - x0_) / hf, air_f - a0_, 0.8), 1
    elif t < td + 0.30:
        Pf, xf, ff = turn_round(_REST_F, _mirror(Pn["f_flop"]), (t - (td - lead)) / (0.30 + lead), hop=0.6), x10 + d, 1
    elif t < tl - 0.42:
        Pf, xf, ff = Pn["fS"].at(t), x10 + d, -1
        Pf = _follow(Pf, Pn["fS"].at(t - _DT), k=0.8)
        kw = _ramp(t, tw - 0.05, tw + 0.1) * (1.0 - _ramp(t, tl - 0.62, tl - 0.44))
        if kw > 0.0:
            s = math.sin(2.0 * math.pi * (t - 241.01) / BEAT + HALF_PI)
            Pf = _swing(Pf, 0.90 + 0.40 * s, "f", kw)
    elif t < tl:
        Pf, xf, ff = turn_round(Pn["f_wave"], _mirror(_REST_F), (t - (tl - 0.42)) / 0.42), x10 + d, -1
    else:
        G = Pn["Gl"]
        Pf, xf, _ = G.at(t)
        P0, x0_, _ = G.at(t - _DT)
        Pf, ff = _follow(Pf, P0, (xf - x0_) / hf, 0.0, 0.8), 1
        k = _ramp(t, tl + 0.55, tl + 0.85) * (1.0 - _ramp(t, tl + 1.45, tl + 1.8))        # a look back over its shoulder as it goes
        if k > 0.0:
            Pf = Pf.but(hturn=Pf["hturn"] + 0.5 * k, turn=Pf["turn"] + 0.22 * k, mouth=Pf["mouth"] + 0.3 * k, joy=Pf["joy"] + 0.3 * k)
        fa = 1.0 - _ramp(t, tl + 1.1, tl + 2.3)
    # ---------------- laughing, panting, alive, on the ground
    sit = _ramp(t, td, td + 0.3) * (1.0 - _ramp(t, tu, tu + 0.8))
    laugh = _env(t, td + 0.35, 0.2, 1.0, 0.8) + 0.7 * _env(t, td + 1.9, 0.15, 0.4, 0.5)
    if laugh > 0.0:
        s = math.sin(2.0 * math.pi * 5.5 * t)
        Pc = Pc.but(pel=(Pc["pel"][0], Pc["pel"][1] + 0.004 * laugh * s), mopen=min(1.0, Pc["mopen"] + 0.25 * laugh * (0.5 + 0.5 * s)))
        if ff < 0:
            s2 = math.sin(2.0 * math.pi * 5.9 * t + 1.0)
            Pf = Pf.but(pel=(Pf["pel"][0], Pf["pel"][1] + 0.004 * laugh * s2), mopen=min(1.0, Pf["mopen"] + 0.25 * laugh * (0.5 + 0.5 * s2)))
    puff = _ramp(t, td, td + 0.4) * (1.0 - _ramp(t, td + 1.5, tu))
    still_c = t < tr or (td + 0.4 < t < ta and not Pn["cS"].busy(t))
    if t < ta:
        Pc = _live(Pc, t, SC, () if still_c else ((t - 1.0, t + 1.0),), breath=1.0 + 2.0 * puff, shift=0.5 * (1.0 - _ramp(t, 226.76, 227.2)),
                   phase=_breaths(t, td, tu, 2.0))
    else:                                            # written for face +1 still, alive as hold_B10 (face -1) will be
        Pc = _live2(Pc, t, SC, 0.0, ((t - 1.0, t + 1.0),), shift=0.5 * _ramp(t, ta, ta + 0.5))
    Pc, yc = stand_on(Pc, xc, fc, hc, ground, y, air_c)
    child = Act(Pc, xc, yc, fc, gc, hc, "child", SC, lift=air_c * hc)
    if t >= ta + 0.275:
        child = _flip(child)
        string_hand = "f"
    if fa > 0.0:
        Pf = _live(Pf, t, SF, ((t - 1.0, t + 1.0),) if (tr - lead <= t < td + 0.4 or t >= tl - 0.5) else (), breath=1.0 + 2.0 * puff,
                   shift=0.5 * (1.0 - _ramp(t, 226.76, 227.0)), phase=_breaths(t, td, tu, 2.0))
        Pf, yf = stand_on(Pf, xf, ff, hf, ground, y, air_f)
        friend = Act(Pf, xf, yf, ff, gf, hf, "friend", SF, a=fa, lift=air_f * hf)
    pts["string"] = _hand_of(child, string_hand)
    num = dict(air_c=air_c * hc, air_f=air_f * hf, sit=sit, laugh=min(1.0, laugh), gone=1.0 - fa,
               speed=abs(x10 - x9) / (td - tr) if tr < t < td else 0.0, left=_ramp(t, ta, ta + 0.55))
    return Duet(child, friend, pts, num, "fc")


# --------------------------------------------------------------------------
# s11 (244.50 to the end): home. The string tied to the armrest, curled up at ease, the phone rings
# --------------------------------------------------------------------------
S11_T = dict(walk=244.765, tie=246.32, tight=247.49, walk2=247.765, sit=249.30, lie=249.92, ring=251.41, look=251.83, reach=252.2,
             grab=252.87, ear=253.6, smile=253.9, wave=255.2)


_EDGE_F = dict(eye=0.9, lid=0.4, brow=0.1, mouth=0.3, hair=0.7, look=(0.30, -0.2))        # at ease as it sits down on the edge
_EDGE_DX = 0.0395                        # the rig's EDGE_CURL sits this far (body units) left of the curl's ground point


@lru_cache(maxsize=4)
def _s11_plan(x0, dx, hc, T):
    T = dict(T)
    xa = ST.SOFA_ARM_R[1] + 72.0 + dx
    xb = ST.CURL_X + dx
    xe = xb - _EDGE_DX * hc                          # where it stands before it sits up on the edge
    TP = (ST.SOFA_ARM_R[1] - 10.0 + dx, ST.SOFA_ARM_Y + 14.0)
    ys = ST.SOFA_SEAT_Y
    G1 = _walk_plan(x0, xa, T["walk"], 2, hc, 0.7, "b10", "b10")
    G2 = _walk_plan(xa, xe, T["walk2"], 2, hc, 0.7, "b10", "b10")
    tt, tg = T["tie"], T["tight"]
    c_bend = _aimed(_eyes(_B10.but(pel=(-0.02, 0.398), lean=0.30, bend=0.22, neck=0.16, mouth=0.3, ef=-0.2, eb=-0.2), xa, FLOOR, hc, -1,
                          TP, 1.0, 0.3), xa, FLOOR, hc, -1, f=_add(TP, 6.0, 0.0), b=_add(TP, -6.0, 2.0))
    cTie = _Track(_B10, (tt, 0.40, c_bend, "body"), (tg + 0.10, 0.17, _B10.but(mouth=0.5), "soft"))
    w = 2.0 * math.pi * 2.0 / max(0.2, tg - 0.14 - (tt + 0.42))

    def loop(t, sgn):                                # the two hands go round each other, twice; then pull the knot tight
        a = w * (t - (tt + 0.42))
        r = 7.0 * _ramp(t, tt + 0.42, tt + 0.6) * (1.0 - _ramp(t, tg - 0.2, tg - 0.1))
        pull = _env(t, tg - 0.03, 0.06, 0.06, 0.12)
        return (TP[0] + sgn * (6.0 + r * math.cos(a) + 13.0 * pull), TP[1] + sgn * (r * math.sin(a) + 4.0 * pull) + (0.0 if sgn > 0 else 2.0))

    pins = ((tt + 0.10, tt + 0.40, tg + 0.08, tg + 0.20, "f", lambda t: loop(t, 1.0)),
            (tt + 0.14, tt + 0.42, tg + 0.08, tg + 0.22, "b", lambda t: loop(t, -1.0)))
    # the rig's roll onto its back, timed: awake, a look, the legs out, the hand down at `grab`, up to the ear at `ear`
    RW = _Path((T["ring"] + 0.10, (0.0, 0.0)), (T["ring"] + 0.34, (0.12, 0.0), "o"), (T["look"], (0.14, 0.0)), (T["look"] + 0.34, (0.30, 0.0)),
               (T["reach"] + 0.22, (0.45, 0.0)), (T["grab"], (0.64, 0.0)), (T["grab"] + 0.40, (0.83, 0.0)), (T["ear"], (1.0, 0.0)))
    reach = pose_joints(roll_over_pose(0.64), xb, ys, hc, 1)["ha_b"]
    return dict(T=T, xa=xa, xb=xb, xe=xe, TP=TP, G1=G1, G2=G2, cTie=cTie, pins=pins, RW=RW, reach=_pt(reach))


def s11(t: float, dx: float = ST.ROOM3_DX, x0: float | None = None, y: float = FLOOR, hc: float = HC, **times) -> Duet:
    """The coda, the child alone (friend is None; the far friend in the window: window_friend).
    From hold_B10. Cue times: S11_T. dx: where the room stands (story.ROOM3_DX).

    It walks left, two steps (a step a beat) to the right end of the sofa, bends and ties the string
    to the armrest with both hands (tie; the knot is pulled tight on `tight`); two more steps to the
    front of the sofa (walk2), turns toward us and sits up on the edge (sit), then curls down as in
    the intro, at ease (lie, 1.1 s: the rig's curl_up_pose; the eyes close as its head comes down).
    At `ring` its eyes open; it looks (look), stretches out and rolls onto its back while the arm
    that lay under it reaches down in front of the sofa (the rig's roll_over_pose: the hand is at its
    lowest at `grab`, the last ring), brings the phone up to its ear (ear) and smiles (smile); a
    small wave of its free hand (wave).
    From the middle of its turn to sit (sit + 0.30) the ground point is (CURL_X + dx, SOFA_SEAT_Y) with
    face +1 (Act.x, y, face): the same picture on both sides of that frame.
    pts: string (the hand that holds the string; the tie point once it is tied), tie (the point on
    the armrest), reach (where the hand is at `grab`: about 17 above the floor line at the foot of the
    sofa, as far down as the rig's reach goes; the phone must be there then), phone (the hand that holds the phone, from `grab`: put
    things.phone_held there). num: tied (0..1), lying (0..1), asleep (0..1: eyes closed), grab
    (0 / 1), at_ear (0..1), smile (0..1)."""
    T = dict(S11_T)
    T.update(times)
    x0 = ST.X10 if x0 is None else float(x0)
    Pn = _s11_plan(x0, dx, hc, tuple(sorted(T.items())))
    xa, xb, xe, TP, ys = Pn["xa"], Pn["xb"], Pn["xe"], Pn["TP"], ST.SOFA_SEAT_Y
    tw, tt, tg, tw2, tsit, tlie = T["walk"], T["tie"], T["tight"], T["walk2"], T["sit"], T["lie"]
    grab = None
    yy, face = y, -1
    num = dict(tied=_ramp(t, tg - 0.05, tg + 0.12), lying=0.0, asleep=0.0, grab=0.0, at_ear=0.0, smile=0.0)
    pts = dict(string=None, tie=TP, reach=Pn["reach"], phone=None)
    moving = True
    if t <= 244.50:
        D = hold_B10(t, x0, y, None, hc)
        D.pts.update(tie=TP, reach=Pn["reach"], phone=None)
        D.num.update(num)
        return D
    if t < tt:
        G = Pn["G1"]
        P, xx, _ = G.at(t)
        P0, x0_, _ = G.at(t - _DT)
        P = _follow(P, P0, -(xx - x0_) / hc, 0.0, 0.8)
        moving = G.t0 < t < G.t1
    elif t < tw2:
        P, xx = Pn["cTie"].at(t), xa
        P = _follow(P, Pn["cTie"].at(t - _DT), k=0.7)
        P, grab = _pin(P, t, xx, y, hc, -1, Pn["pins"])
        moving = Pn["cTie"].busy(t)
    elif t < tsit:
        G = Pn["G2"]
        P, xx, _ = G.at(t)
        P0, x0_, _ = G.at(t - _DT)
        P = _follow(P, P0, -(xx - x0_) / hc, 0.0, 0.8)
        moving = G.t0 < t < G.t1
    elif t < tsit + 0.60:
        P, xx = turn_round(_B10, _mirror(SIT_EDGE.but(**_EDGE_F)), (t - tsit) / 0.60), xe
    elif t < T["ring"] + 0.10:
        u = _c((t - tlie) / 1.1)
        P = curl_up_pose(_sm(u))
        k = _ramp(u, 0.68, 1.0)                      # it stays at ease all the way down; the eyes close last
        P = P.but(eye=0.9 * (1.0 - k), lid=0.4 - 0.1 * k, brow=0.1 * (1.0 - k), mouth=0.3, hair=0.7 - 0.45 * _ramp(u, 0.4, 1.0),
                  blush=0.3 * _ramp(u, 0.3, 1.0), look=_lerp(_EDGE_F["look"], P["look"], _ramp(u, 0.0, 0.3)))
        xx, yy, face = xb, ys, 1
        num["lying"], num["asleep"] = _ramp(u, 0.2, 0.85), k
        moving = 0.0 < u < 1.0
    else:
        wr = Pn["RW"](t)[0]
        P, xx, yy, face = roll_over_pose(wr), xb, ys, 1
        num["lying"] = 1.0
        num["grab"] = 1.0 if t >= T["grab"] else 0.0
        num["at_ear"] = _ramp(t, T["grab"] + 0.1, T["ear"])
        sm = _ramp(t, T["smile"], T["smile"] + 0.6)
        num["smile"] = sm
        P = P.but(mouth=min(P["mouth"], 0.32) + 0.58 * sm, joy=min(P["joy"], 0.1) + 0.5 * sm, eye=max(P["eye"], 1.05 * _ramp(t, T["ring"] + 0.12, T["ring"] + 0.3)),
                  lift=max(P["lift"], 0.5 * _bell(t, T["ring"] + 0.1, 0.9)))
        kw = _ramp(t, T["wave"], T["wave"] + 0.3) * (1.0 - _ramp(t, T["wave"] + 1.2, T["wave"] + 1.5))
        if kw > 0.0:
            s = math.sin(2.0 * math.pi * 2.4 * (t - T["wave"]))
            P = P.but(hf=(P["hf"][0] + 0.03 * s * kw, P["hf"][1] + 0.07 * kw))
        moving = t < T["ear"] + 0.05 or kw > 0.0
    lie = 1.0 if yy != y else 0.0
    # asleep it breathes a quarter slower and deeper (the phase is the integral of the rate: nothing jumps as it changes)
    ta_, tb_, tc_ = tlie + 0.748, tlie + 1.1, T["ring"] + 0.10
    v = _c((t - ta_) / (tb_ - ta_))
    slept = (tb_ - ta_) * (v ** 3 - 0.5 * v ** 4) + max(0.0, min(t, tc_) - tb_)
    deep = 0.5 * (num["asleep"] if t < tc_ else 1.0 - _ramp(t, tc_, tc_ + 0.5))
    P = _live(P, t, SC, ((T["ring"] - 0.3, T["smile"] + 0.8),) if not moving else ((t - 1.0, t + 1.0),), breath=1.0 + deep,
              shift=0.5 * (1.0 - lie) * (1.0 - _ramp(t, tsit, tsit + 0.3)), phase=_REST_RATE * t - 0.07 * slept)
    child = Act(P, xx, yy, face, grab, hc, "child", SC)
    if tsit + 0.30 <= t < tsit + 0.60:               # from the middle of the turn: written as the sofa poses are (face +1, from the seat)
        child = _flip(child, _EDGE_DX, (y - ys) / hc, x=xb, y=ys)
    if t < tg:
        pts["string"] = _hand_of(child, "f") if grab is None else _pt(grab["f"])
    else:
        pts["string"] = TP
    if t >= T["grab"]:
        pts["phone"] = _hand_of(child, "b")
    return Duet(child, None, pts, num, "fc")


def window_friend(t: float, dx: float = ST.ROOM3_DX, t_on: float = 254.45, t_wave: float = 255.0,
                  window=(1571.0, 448.0, 56.0, 70.0), h: float = 76.0) -> Act:
    """The tiny amber figure in the lit window across the street (sets.FAR_WINDOW: centre x, centre
    y, width, height at dx = 0), waving: about 30 px of it show at zoom 1.3. It rises into the
    window from t_on (Act.a ramps over 0.3 s) and waves from t_wave with its whole arm at its side,
    a sweep every half beat, leaning with it: the one shape that reads at that size. Draw it inside
    the window's rectangle (clip to it: its legs are below the sill). Returns an Act (face -1).
    num: wave (0..1)."""
    cx, cy, ww, wh = window
    cx += dx
    up = _out((t - t_on) / 0.45, 2.0)
    P = _F_WAVE.but(hb=(0.0, -0.28), hbz=0.02, mopen=0.3, mouth=1.1, joy=0.4, turn=0.85, look=(0.20, 0.05))
    kw = _ramp(t, t_wave - 0.25, t_wave)
    s = math.sin(2.0 * math.pi * (t - t_wave) / BEAT + HALF_PI)
    P = _swing(P, 0.95 + 0.42 * s * kw, "f", 1.0, 1.4)
    yb = cy + 0.5 * wh + 0.40 * h + (1.0 - up) * 0.5 * h          # its hips at the sill
    return Act(alive(P, t, SF, blink=0.0, shift=0.0), cx - 0.08 * h, yb, -1, None, h, "friend", SF, a=_seg(t, t_on, t_on + 0.3),
               num=dict(wave=kw))


PAIR_HANDOFF = {"B6": hold_B6, "B7": hold_B7, "B8": hold_B8, "B9": hold_B9, "B10": hold_B10}
