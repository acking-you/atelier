"""hx.chalk.people: the other people. Faceless outline figures in dim chalk: pupils with a satchel, two
adults, the rows of the classroom, the stream on the corridor line, the ring of backs with its
whispers, the two adults at the home table, and the three drawn figures of the family line.

They are never villains and never individuals: they are simply turned away. Nobody here has a face
until the last chorus, when they turn round and are just children with two dots and a small mouth.

A person is built from the joints of the figure rig (hx.chalk.figure.solve), so it stands, walks,
sits and turns with the same poses as the two characters, but it is drawn here, as an outline: a
garment shape with a little rubbed tone inside, a head with its hair scribbled in, single-line limbs.
The rig is a side view; a person also has a width, so the same joints can be seen in profile, from
behind and from the front, and every angle in between is a valid drawing (the turn is a parameter).

Everything is WORLD coordinates through F.cam; a frame is a pure function of time. Doc: doc/people.md.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from .core import A, C, Frame, blob, chalk, ease, mix, ramp, rnd, rrect_pts, rsym, scrib, seg, spline
from .figure import STAND, Pose, mixp, solve, walk, walk_to
from .sketch import Fill, Sketch, Stroke

__all__ = ["person", "person_sketch", "turned", "P_REST", "P_AWAY", "P_WAVE", "P_SIT", "STEP_RATE", "People",
           "pupil", "class_rows", "Walker", "walkers", "stream", "passes", "ring_of_backs", "whisper", "whispers", "undraw",
           "walk_off", "home_adults", "family_line", "long_line", "SITS", "HAIRS", "RISE"]

FLOOR = 742.0                    # the ground line (hx/story.py)
BEAT0, BEAT = 0.265, 0.75        # the song's grid: beat k at BEAT0 + BEAT * k
STEP_RATE = 1.0 / (2.0 * BEAT)   # walk cycles a second for one step per beat
TONE = (0.23, 0.28, 0.43)        # the rubbed tone inside a garment at night
TONE_HEAD = (0.30, 0.36, 0.53)
PASTELS = (C.CORAL, C.SEA, C.MUSTARD, C.LILAC, C.ROSE, C.JUMPER)      # their jumpers in the colour world
HAIRS_DAY = (C.PENCIL, (0.45, 0.30, 0.20), (0.62, 0.42, 0.20), (0.30, 0.22, 0.20))
# what "standing at ease" is in the rig (its STAND pose): the length of a hanging arm, the height of the hips.
# Everything here is measured against these two, so the people follow the rig if its build changes.
_HANG = math.hypot(*STAND["hf"])
_PEL = STAND["pel"][1]


# --------------------------------------------------------------------------
# kinds: proportions in body units (1 = standing height)
# --------------------------------------------------------------------------
class Kind:
    def __init__(self, **kw):
        self.__dict__.update(kw)


# R head radius; ub = how much longer than the rig's the upper body is (a tall body with a head no
# bigger than a child's); arm = length of a hanging arm (None: the rig's); stoop = how much of a
# pose's stoop it keeps; lw line width.
# body / skirt: stations of the garment from the hem up to the neck: (where, lateral half-width, half-depth)
#   where: ("low", d) = d below the pelvis; ("sp", i) = spine point i (0 pelvis .. 6 neck); ("up", d); ("top", d)
KINDS = {
    # a pupil: the child's own build, a jumper, a satchel on the back. Standing height 330..360
    "pupil": Kind(R=0.150, ub=1.0, arm=None, stoop=1.0, lw=0.0142, satchel=True, skirt=None, shade=False,
                  hair=("short", "bob", "tail", "bunches"),
                  body=((("low", 0.062), 0.124, 0.110), (("sp", 0), 0.113, 0.098), (("sp", 3), 0.100, 0.084),
                        (("sp", 5), 0.092, 0.070), (("top", 0.016), 0.040, 0.036)),
                  dress=((("low", 0.118), 0.150, 0.130), (("sp", 0), 0.120, 0.102), (("sp", 3), 0.099, 0.083),
                         (("sp", 5), 0.091, 0.069), (("top", 0.016), 0.040, 0.036))),
    # an adult in a long coat (trousers under it). Standing height 520..560
    "coat": Kind(R=0.097, ub=1.40, arm=0.350, stoop=0.55, lw=0.0094, satchel=False, skirt=None, shade=True, hair=("neat",), dress=None,
                 body=((("low", 0.245), 0.122, 0.104), (("low", 0.12), 0.113, 0.095), (("sp", 0), 0.105, 0.086),
                       (("sp", 3), 0.100, 0.079), (("sp", 5), 0.106, 0.070), (("top", 0.012), 0.034, 0.030))),
    # an adult in a cardigan and a skirt, the hair in a bun
    "skirt": Kind(R=0.095, ub=1.40, arm=0.345, stoop=0.55, lw=0.0094, satchel=False, shade=False, hair=("bun",), dress=None,
                  skirt=((("low", 0.215), 0.134, 0.108), (("low", 0.09), 0.110, 0.090), (("sp", 0), 0.088, 0.072),
                         (("up", 0.035), 0.078, 0.060)),
                  body=((("low", 0.030), 0.095, 0.076), (("sp", 0), 0.091, 0.072), (("sp", 3), 0.088, 0.067),
                        (("sp", 5), 0.098, 0.064), (("top", 0.012), 0.033, 0.028))),
}

# poses of their own (the rig's units; blend them with mixp like any pose). The view is never in the pose:
# it comes from back / dots (a pose's own `turn` is ignored here).
P_REST = Pose(pel=(0.0, _PEL + 0.015), lean=0.0, bend=0.05, neck=0.02, hf=(0.020, -0.998 * _HANG), hb=(-0.016, -0.998 * _HANG),
              ff=(0.032, 0.0), fb=(-0.034, 0.0), open=0.5)                     # standing, at ease
P_AWAY = P_REST.but(lean=0.02, bend=0.14, neck=0.16, hf=(0.028, -0.996 * _HANG), hb=(-0.008, -0.998 * _HANG))   # standing, head a little down
P_WAVE = P_REST.but(bend=-0.03, neck=-0.06)                                    # standing a little taller, to go with wave=1
P_SIT = Pose(pel=(-0.02, 0.215), lean=0.06, bend=0.20, neck=0.12, hf=(0.150, -0.235), hb=(0.120, -0.245),
             ff=(0.200, 0.0), fb=(0.165, 0.0), open=0.4)                       # on a seat 0.19 body units high, hands in the lap


def turned(w: float, lead: float = 0.18) -> dict:
    """The keywords of a turn from the back view (w = 0) through the profile (0.5) to the front with
    its dot face (1): person(F, ..., **turned(w)). The head leads the body by `lead` of the turn."""
    w = min(1.0, max(0.0, float(w)))
    v = 2.0 * w - 1.0
    hv = 2.0 * min(1.0, w * (1.0 + lead)) - 1.0
    return dict(back=max(0.0, -v), dots=max(0.0, v), head=hv - v)


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------
def _limb(a_, j_, b_, n=12):
    """A soft joint: an arm or a leg drawn in one go."""
    m0, m1 = a_ + (j_ - a_) * 0.72, j_ + (b_ - j_) * 0.28
    return spline(np.array([a_, m0, j_ * 0.5 + (m0 + m1) * 0.25, m1, b_]), n)


def _run(vis):
    """The longest run of True in a boolean array, as a slice (None if shorter than 3)."""
    best, i, n = (0, 0), 0, len(vis)
    while i < n:
        if vis[i]:
            j = i
            while j < n and vis[j]:
                j += 1
            if j - i > best[1] - best[0]:
                best = (i, j)
            i = j
        else:
            i += 1
    return slice(*best) if best[1] - best[0] >= 3 else None


# the hairline: how far forward the hair comes at each height of the head (unit radius; + = toward the face).
# Above 0.58 everything is hair (a cap with a fringe); below, only the back of the head.
_HL_U = np.array([-1.0, -0.60, -0.20, 0.10, 0.40, 0.58, 1.0])
_HL_F = np.array([-0.70, -0.55, -0.25, 0.0, 0.34, 1.01, 1.01])
_BETA = np.linspace(0.0, math.pi, 17)
# how far down the hair scribble goes (unit head radius) per style: in profile, and seen from behind
# (the back of a head is all hair, down to the nape: that is what makes a turned back a back)
_LOW = {"short": -0.26, "bob": -0.66, "tail": -0.06, "bunches": -0.04, "bun": -0.10, "neat": 0.04}
_LOW_BACK = {"short": -0.66, "bob": -0.90, "tail": -0.60, "bunches": -0.58, "bun": -0.52, "neat": -0.56}


def _edge(f, f0, j0, j1):
    """The angle between samples j0 (hair) and j1 (not hair) where the hairline lies."""
    t = (f0 - f[j0]) / (f[j1] - f[j0] + 1e-9)
    return _BETA[j0] + (_BETA[j1] - _BETA[j0]) * min(1.0, max(0.0, t))


def _hair_rows(style: str, seed: int, hth: float):
    return _hair_rows_q(style, seed, round(float(hth), 3))


@lru_cache(maxsize=4096)
def _hair_rows_q(style: str, seed: int, hth: float):
    """The scribble that colours the hair in, for a head turned by hth (-pi/2 = seen from behind, 0 =
    profile, +pi/2 = from the front): head-plane points (x toward the face side, y up; unit radius)
    of a zigzag over the part of the head that is hair and faces us, and the same for the far temple.
    It is a continuous function of hth, so the hair travels round the head as the head turns."""
    n_ = int((0.90 - _LOW_BACK[style]) / 0.150) + 1     # (the same rows at every angle: they only close up)
    low = _LOW[style] + (_LOW_BACK[style] - _LOW[style]) * ramp(-math.sin(hth), 0.15, 0.95)
    us = np.linspace(0.90, low, n_) + np.array([0.025 * rsym(seed, 80 + i) for i in range(n_)])
    r = np.sqrt(np.maximum(0.05, 1.0 - np.minimum(us, 0.0) ** 2 * 0.55 - np.maximum(us, 0.0) ** 2))   # the hair hangs below the equator
    f0 = np.interp(us, _HL_U, _HL_F)
    f = r[:, None] * np.cos(_BETA[None, :] - hth)        # forward component of what faces us along each row
    hair = f < f0[:, None]
    n = len(_BETA)
    main, far = [], []
    for i in range(len(us)):
        hrow = hair[i]
        if not hrow.any():
            continue
        j1 = n - 1                                       # the run of hair nearest the back of the head
        while not hrow[j1]:
            j1 -= 1
        j0 = j1
        while j0 > 0 and hrow[j0 - 1]:
            j0 -= 1
        b1 = math.pi if j1 == n - 1 else _edge(f[i], f0[i], j1, j1 + 1)
        b0 = 0.0 if j0 == 0 else _edge(f[i], f0[i], j0, j0 - 1)
        xa, xb = r[i] * math.cos(b0), r[i] * math.cos(b1)
        if xa - xb > 0.16:
            jit = 0.06 * rsym(seed, 90 + i)
            main.append((xa - 0.07 + jit, us[i]) if i % 2 == 0 else (xb + 0.07 + jit, us[i]))
        if j0 > 1 and hrow[0]:                           # and the hair beyond the face, at the far temple
            k = 0
            while hrow[k + 1]:
                k += 1
            xc = r[i] * math.cos(_edge(f[i], f0[i], k, k + 1))
            if r[i] - xc > 0.12:
                far.append((r[i] - 0.07, us[i]) if i % 2 == 0 else (xc + 0.06, us[i]))
    return (np.array(main) if len(main) >= 3 else None), (np.array(far) if len(far) >= 3 else None)


def _hair_extra(style: str, seed: int, back: float = 0.0):
    return _hair_extra_q(style, int(seed), round(min(1.0, max(0.0, float(back))), 2))


@lru_cache(maxsize=4096)
def _hair_extra_q(style: str, seed: int, back: float):
    """What hangs out of a head of hair, as head-local polylines (forward, up, lateral; unit radius).
    back: 0 seen from the side .. 1 from behind. A ponytail is tied at the back of the head; seen
    from behind it is drawn the way a child draws one: out to one side (it slides there as the head
    turns away), because down the middle of the head it would only be a crack."""
    j = lambda k, s=0.10: s * rsym(seed, 40 + k)
    if style == "tail":
        sg = 1.0 if rnd(seed, 47) < 0.5 else -1.0
        b = back ** 1.5
        side = A((-0.70, 0.62, 0.0), (-1.22, 0.60, 0.05), (-1.52, 0.16 + j(1), -0.07), (-1.46, -0.30, 0.06), (-1.36, -0.66, -0.02))
        away = A((-0.70, 0.60, sg * 0.56), (-1.22, 0.82, sg * 0.94), (-1.52, 0.38 + j(1), sg * 1.22), (-1.46, -0.26, sg * 1.16),
                 (-1.36, -0.84, sg * 1.03))
        return [spline(side + (away - side) * b, 11)]
    if style == "bob":                                   # cut straight: it hangs past the head on both sides, the hem under it
        return [spline(A((-0.30, -0.50, -0.88), (-0.38, -0.90, -0.95), (-0.46, -1.13, -0.80), (-0.52, -1.17 + j(2, 0.04), -0.26),
                         (-0.52, -1.16, 0.26), (-0.46, -1.13, 0.80), (-0.38, -0.90, 0.95), (-0.30, -0.50, 0.88)), 15)]
    if style == "bunches":
        return [spline(A((-0.50, 0.24, sg * 0.84), (-0.62, 0.04, sg * 1.13), (-0.67, -0.46 + j(3 + int(sg)), sg * 1.17),
                         (-0.60, -0.96, sg * 1.03)), 7) for sg in (-1.0, 1.0)]
    if style == "bun":
        a = np.linspace(0.0, 2.0 * math.pi + 0.6, 11)
        return [np.stack([-0.98 + 0.16 * np.cos(a), 0.52 + 0.30 * np.sin(a), 0.30 * np.cos(a)], axis=1)]
    return []


def _straight(hv):
    """A hanging hand moved out to arm's length (the same direction), so that the elbow does not stick out."""
    d = math.hypot(hv[0], hv[1])
    if hv[1] > -0.5 * _HANG or d >= _HANG or d < 1e-6:
        return hv
    k = 1.0 + (_HANG / d - 1.0) * min(1.0, (-hv[1] - 0.5 * _HANG) / (0.2 * _HANG))
    return (hv[0] * k, hv[1] * k)


class People(Sketch):
    """A Sketch of people with what a scene needs to know about each: `who` is a list of dicts (name,
    x, y, h, head (world centre), R (head radius), back (a point between the shoulders), face, view, ...)
    in the order they stand in; `heads` the head centres in that order."""

    def __init__(self, items=(), name: str = "", who=()):
        super().__init__(items, name)
        self.who = list(who)

    @property
    def heads(self):
        return [w["head"] for w in self.who]


# --------------------------------------------------------------------------
# one person
# --------------------------------------------------------------------------
def _build(x, y, h, P, kind, face, seed, a, view, dots, head, tilt, col, tone, tone_head, knock, hair_col, dot_col,
           lod=1, variant=None, day=False, wave=0.0, wag=0.0):
    """The strokes and fills of one person in paint order, and its world joints."""
    K = KINDS[kind] if isinstance(kind, str) else kind
    if P.get("turn") or P.get("hturn"):                  # the view is ours (back / dots), not the pose's
        P = P.but(turn=0.0, hturn=0.0)
    if K.stoop != 1.0:                                   # a tall body keeps less of a pose's stoop, and its hanging arms are long and straight
        P = P.but(lean=P["lean"] * K.stoop, bend=P["bend"] * K.stoop, neck=P["neck"] * (0.5 + 0.5 * K.stoop),
                  hf=_straight(P["hf"]), hb=_straight(P["hb"]))
    J = solve(P)
    rot = P["rot"]
    view = max(-1.0, min(1.0, view))
    th = view * (math.pi / 2)
    c, s = math.cos(th), math.sin(th)
    hth = max(-1.0, min(1.0, view + head)) * (math.pi / 2)
    hc_, hs_ = math.cos(hth), math.sin(hth)
    pel = J["pel"]
    ub = K.ub
    cr, sr = math.cos(rot), math.sin(rot)
    sd = int(seed) * 97

    def W(p, l=0.0):
        """Body point(s) (forward, up) with a lateral offset l -> world."""
        p = np.asarray(p, dtype=np.float64)
        f, u = p[..., 0], p[..., 1]
        if rot:
            f, u = f * cr + u * sr, -f * sr + u * cr
        X = f * c - l * s
        return np.stack([x + h * (face * X + u * tilt), y - h * u], axis=-1)

    up = lambda p: pel + (p - pel) * ub
    sp = up(J["spine"])
    tan0, tan1 = J["tan0"], J["tan1"]
    neck = sp[6]
    hd = J["head"] - J["neck"]
    hd = hd / (math.hypot(hd[0], hd[1]) + 1e-9)
    R = K.R
    headc = neck + hd * R * 0.88
    knm = (J["kn_f"] + J["kn_b"]) * 0.5
    low = knm - pel
    low = low / (math.hypot(low[0], low[1]) + 1e-9)
    k_sit = ramp(abs(low[0]), 0.40, 0.75)                # a skirt hangs; on a seat it lies along the thighs
    low = np.array([low[0] * (0.12 + 0.88 * k_sit), low[1] * (0.12 + 0.88 * k_sit) - 0.88 * (1.0 - k_sit)])
    low = low / (math.hypot(low[0], low[1]) + 1e-9)
    stride = abs(J["kn_f"][0] - J["kn_b"][0])
    lw = K.lw * h
    bob = float(P.get("bob", 0.0))                       # the walk's follow-through: what is carried arrives late
    wob = min(1.0, max(0.25, h / 400.0)) * 0.8
    step = 5.0 if lod >= 1 else 3.5
    kw = dict(wob=wob, taper=0.7, step=step)                           # the outlines of garment and head
    kw_l = dict(wob=wob, taper=0.7, step=step, edge=0.0)               # limbs, satchel
    kw_s = dict(wob=wob * 0.6, taper=0.55, edge=0.0, step=3.5)         # small strokes: hair, straps
    it = []

    def shape(stations):
        cs, wl = [], []
        for (wh, v), al, af in stations:
            if wh == "low":
                p = pel + low * v * (1.0 - 0.42 * k_sit)  # (on a seat it ends on the lap)
                af = max(af, (0.5 * stride + 0.030) * (1.0 - k_sit))       # a hem opens with the stride
            elif wh == "sp":
                p = sp[v]
            elif wh == "up":
                p = pel + tan0 * v * ub
            else:
                p = neck + tan1 * v
            cs.append(p)
            wl.append(math.hypot(af * c, al * s))
        Cw = W(np.array(cs))
        d = np.gradient(Cw, axis=0)
        ln = np.hypot(d[:, 0], d[:, 1]) + 1e-9
        nrm = np.stack([-d[:, 1] / ln, d[:, 0] / ln], axis=1) * (np.array(wl) * h)[:, None]
        return Cw, nrm

    # ---- limbs ----------------------------------------------------------------------------
    al_sh = K.body[-2][1]

    ua = ub if K.arm is None else K.arm / _HANG          # arms: the rig's own, or a hanging length of our own
    ka = _HANG / 0.27

    def arm_pts(which, sgn):
        sh = up(J["sh_" + which])
        el, ha = sh + (J["el_" + which] - J["sh_" + which]) * ua, sh + (J["ha_" + which] - J["sh_" + which]) * ua
        l1, l2, l3 = sgn * (al_sh - 0.014), sgn * (al_sh + 0.012), sgn * (al_sh + 0.006)
        if wave > 0.0 and which == "f":                  # the near hand lifted out to the side: hello (it reads in every view)
            e = ease(wave)
            el = el + (sh + np.array([0.040, 0.012]) * ka * ua - el) * e
            ha = ha + (sh + np.array([0.080 + 0.03 * wag, 0.200]) * ka * ua - ha) * e
            l2, l3 = l2 + 0.085 * ka * ua * e, l3 + (0.110 + 0.050 * wag) * ka * ua * e
        return W(np.array([sh, el, ha]), np.array([l1, l2, l3]))

    def arm(which, sgn):
        return _limb(*arm_pts(which, sgn), 12)

    def leg(which, sgn):
        an = J["an_" + which]
        pitch = P["a" + which]
        ll = sgn * 0.040
        toe = an + np.array([0.086 * math.cos(pitch), 0.086 * math.sin(pitch) - 0.008])
        Q = W(np.array([J["hip_" + which], J["kn_" + which], an, toe]), np.array([ll, ll, ll, ll + sgn * 0.052]))
        return np.vstack([_limb(Q[0], Q[1], Q[2], 12), Q[3:]])

    arm_b_behind = c > 0.5                               # the far arm hangs behind the body until we see the back or the front
    dim = 0.80
    hb_ = up(J["sh_b"]) + (J["ha_b"] - J["sh_b"]) * ua
    if arm_b_behind and (abs(hb_[0] - pel[0]) * c > 0.080 or hb_[1] > sp[5][1] or hb_[1] < pel[1] - 0.05 or lod >= 2):      # (not when the body hides all of it)
        it.append(Stroke(arm("b", -1.0), col, lw, a * dim, sd + 1, "arm_b", **kw_l))
    it.append(Stroke(leg("b", -1.0), col, lw, a * dim, sd + 3, "leg_b", **kw_l))
    it.append(Stroke(leg("f", 1.0), col, lw, a, sd + 5, "leg_f", **kw_l))

    # ---- satchel: a box on the back (in front of the body when seen from behind) -----------
    bag = []
    has_bag = K.satchel and (variant is None or variant.get("satchel", True))
    if has_bag and s < 0.8:
        bf = np.array([tan0[1], -tan0[0]])               # forward perpendicular of the spine
        cen = sp[3] + (sp[4] - sp[3]) * 0.3 - bf * (0.066 + 0.046) + tan0 * (0.050 * bob) - bf * (0.012 * bob)   # it bounces on the back
        Cb = W(cen)
        ax_ = W(cen + tan0 * 0.1) - Cb
        ax_ = ax_ / (math.hypot(ax_[0], ax_[1]) + 1e-9)
        pr = np.array([-ax_[1], ax_[0]])
        hw_, hh_ = h * math.hypot(0.046 * c, 0.070 * s), h * 0.088
        Q = rrect_pts(-hw_, -hh_, hw_, hh_, min(hw_, hh_) * 0.42, 4)
        Bp = Cb + Q[:, :1] * pr + Q[:, 1:] * ax_
        bag.append(Fill(Bp, tone, 0.6, 9.0, 4.0, 0.0, sd + 20, knock=knock, base=0.50 * a, name="bag.fill"))
        q = np.array([-1.0, -0.4, 0.4, 0.98])            # the outline, and on in one go into the line of the flap
        fl = Cb + (q * hw_)[:, None] * pr + (hh_ * (0.26 + 0.10 * (1.0 - np.abs(q))))[:, None] * ax_
        i0 = int(np.argmin(((Bp - fl[0]) ** 2).sum(1)))
        bag.append(Stroke(np.vstack([Bp[i0:-1], Bp[:i0 + 1], fl[1:]]), col, lw * 0.95, a, sd + 21, "bag", **kw_l))
    bag_front = bool(bag) and s < -0.12
    if bag and not bag_front:
        it.extend(bag)

    # ---- skirt, body --------------------------------------------------------------------
    def garment(stations, nm, sd_, tone_a):
        Cw, nrm = shape(stations)
        out = spline(np.vstack([Cw - nrm, (Cw + nrm)[::-1]]), 34 if lod >= 1 else 24)
        poly = np.vstack([out, out[:1]])
        if day:                                          # crayon: a rubbed base and a loose zigzag over it
            it.append(Fill(poly, tone, 0.9 * face, max(5.0, 0.034 * h), max(2.5, 0.017 * h), 0.75 * a, sd_, knock=knock, base=0.45 * a,
                           name=nm + ".fill"))
        else:
            it.append(Fill(poly, tone, 0.6, 9.0, 4.0, 0.0, sd_, knock=knock, base=tone_a * a, name=nm + ".fill"))
        it.append(Stroke(np.vstack([poly, poly[1:3]]), col, lw, a, sd_ + 1, nm, **kw))
        return Cw, nrm

    if K.skirt is not None:
        garment(K.skirt, "skirt", sd + 30, 0.45)
    dress = K.dress is not None and (variant or {}).get("dress", rnd(seed, 33) < 0.40)
    Cw, nrm = garment(K.dress if dress else K.body, "body", sd + 34, 0.55)
    if lod >= 2 and K.shade and not day:
        # a child's quick shading down a long coat: a few slanted strokes of one loose zigzag
        k0, k1 = 1, len(Cw) - 2
        zz = []
        for i in range(6):
            q0 = 0.10 + 0.72 * i / 6
            for q, sg in ((q0, -1.0), (q0 + 0.16, 1.0)):
                zz.append(Cw[k0] + (Cw[k1] - Cw[k0]) * q + (nrm[k0] + (nrm[k1] - nrm[k0]) * q) * sg * (0.56 + 0.16 * rnd(seed, 60 + i)))
        it.append(Stroke(np.array(zz), mix(tone, col, 0.5), lw * 1.7, 0.36 * a, sd + 38, "body.shade", wob=wob, taper=0.3, edge=0.0,
                         grain="sparse", step=6.0))
    if bag_front:
        it.extend(bag)

    # straps of the satchel: lines over the shoulders, only what faces us
    if has_bag and s > -0.85:
        bf = np.array([tan0[1], -tan0[0]])
        pts = np.array([sp[4] - bf * 0.070, sp[5] - bf * 0.050 + tan1 * 0.030, sp[5] + tan1 * 0.052, sp[5] + bf * 0.052 + tan1 * 0.020,
                        sp[4] + bf * 0.072, sp[3] + bf * 0.060])
        rel = np.array([-0.070, -0.050, 0.0, 0.052, 0.072, 0.060])
        for sgn in (1.0, -1.0):
            ll = sgn * 0.050
            r_ = _run(rel * s + ll * c >= -0.012)
            if r_ is not None:
                it.append(Stroke(spline(W(pts[r_], ll), 9), col, lw * 0.8, a * 0.85, sd + 24 + int(sgn),
                                 "strap_f" if sgn > 0 else "strap_b", **kw_s))

    # ---- head, hair, the dot face ---------------------------------------------------------
    Hc = W(headc)
    Rw = R * h
    hang = J["hang"] + rot
    ha = face * max(-0.48, min(0.48, hang * 0.7)) * abs(c) + tilt * 0.5
    hp = blob(Hc[0], Hc[1], Rw * 1.03, Rw * 0.975, sd + 41, 0.022, 26 if lod >= 1 else 18, rot=ha)
    backness = max(0.0, -hs_)
    it.append(Fill(hp, tone_head, 0.6, 9.0, 4.0, 0.0, sd + 42, knock=knock, base=(0.9 if day else 0.46 + 0.10 * backness) * a,
                   name="head.fill"))
    it.append(Stroke(np.vstack([hp, hp[1:3]]), col, lw, a, sd + 43, "head", **kw))
    ex = np.array([math.cos(ha), math.sin(ha)])          # the head's own axes on screen (it nods with the neck)
    ey = np.array([-math.sin(ha), math.cos(ha)])

    def head_pts(Q):
        """Head-local (forward, up, lateral) unit points -> world, and their depth toward us."""
        X = Q[:, 0] * hc_ - Q[:, 2] * hs_
        Z = Q[:, 0] * hs_ + Q[:, 2] * hc_
        return Hc + (face * X * Rw)[:, None] * ex - (Q[:, 1] * Rw)[:, None] * ey, X, Z

    style = (variant or {}).get("hair") or K.hair[int(rnd(seed, 31) * len(K.hair)) % len(K.hair)]
    main, far_ = _hair_rows(style, int(seed), hth)
    for nm, Z_, sd_ in (("hair", main, 50), ("hair_far", far_, 51)):
        if Z_ is not None:
            Pw = Hc + (face * Z_[:, 0] * Rw)[:, None] * ex - (Z_[:, 1] * Rw)[:, None] * ey
            it.append(Stroke(Pw, hair_col, lw * (1.9 if lod >= 1 else 1.6), a * 0.80, sd + sd_, nm, wob=wob * 0.7, taper=0.5,
                             edge=0.0, grain="mid", step=4.0))
    for i, Q in enumerate(_hair_extra(style, int(seed), backness)):
        if bob and style in ("tail", "bunches"):         # what hangs swings behind the step
            kq = np.clip((0.62 - Q[:, 1]) / 1.5, 0.0, 1.0)
            Q = Q + np.stack([-0.30 * bob * kq, 0.12 * bob * kq, np.zeros(len(Q))], axis=1)
        Pw, X, Z = head_pts(Q)
        r_ = _run((Z > -0.10) | (X * X + Q[:, 1] ** 2 > 1.02))
        if r_ is not None:
            it.append(Stroke(Pw[r_], hair_col, lw * 1.5, a * 0.95, sd + 54 + i, f"hair{i}", **kw_s))
    if dots > 0.0:
        da = a * ramp(dots, 0.25, 0.75)
        er = 0.085 * Rw
        for nm, az in (("eye_l", -0.40), ("eye_r", 0.40)):
            Pw, X, Z = head_pts(np.array([[math.cos(az) * 0.96, 0.04, math.sin(az) * 0.96]]))
            k = da * ramp(float(Z[0]), 0.05, 0.35)
            if k > 0.003:
                it.append(Stroke(np.array([Pw[0] - (0.0, er * 0.25), Pw[0] + (0.0, er * 0.25)]), dot_col, er * 2.0, k, sd + 61, nm,
                                 wob=0.0, taper=1.0, edge=0.0, step=3.0, floor=1.9))
        az = np.linspace(-0.26, 0.26, 5)
        Pw, X, Z = head_pts(np.stack([np.cos(az) * 0.95, -0.40 - 0.07 * np.cos(az * 5.5), np.sin(az) * 0.95], axis=1))
        k = da * ramp(float(Z.min()), 0.05, 0.35)
        if k > 0.003:
            it.append(Stroke(Pw, dot_col, max(lw * 0.62, er * 0.75), k, sd + 64, "mouth", wob=0.0, taper=0.6, edge=0.0, step=3.0))

    # ---- the arms that lie in front --------------------------------------------------------
    if not arm_b_behind:
        it.append(Stroke(arm("b", -1.0), col, lw, a * (dim + (1.0 - dim) * abs(s)), sd + 1, "arm_b", **kw_l))
    it.append(Stroke(arm("f", 1.0), col, lw, a, sd + 7, "arm_f", **kw_l))

    Af, Ab = arm_pts("f", 1.0), arm_pts("b", -1.0)
    Q = W(np.array([neck, pel, sp[4], J["an_f"], J["an_b"]]), np.array([0.0, 0.0, 0.0, 0.04, -0.04]))
    out = dict(head=Hc, R=Rw, neck=Q[0], pel=Q[1], back=Q[2], ha_f=Af[2], ha_b=Ab[2], sh_f=Af[0], sh_b=Ab[0], an_f=Q[3], an_b=Q[4],
               top=np.array([Hc[0], Hc[1] - Rw]))
    return it, out


def _colours(day: bool, seed: int, col, far: float = 0.0):
    """(line, tone, head tone, knock, hair, dots) for the skin."""
    if day:
        line = C.PENCIL if col is None else col
        return (line, PASTELS[int(rnd(seed, 71) * len(PASTELS)) % len(PASTELS)], C.SKIN, C.DAY,
                HAIRS_DAY[int(rnd(seed, 72) * len(HAIRS_DAY)) % len(HAIRS_DAY)], C.PENCIL)
    line = mix(C.CHALK_DIM, C.CHALK_FAR, far) if col is None else col
    return line, mix(TONE, C.PAPER, 0.5 * far), mix(TONE_HEAD, C.PAPER, 0.5 * far), C.KNOCK, line, mix(line, C.CHALK, 0.5)


def _rub(items, off: float, x: float, face: int):
    """Rub a person out: every item is taken back, the trailing side first (off 0..1)."""
    if off <= 0.0:
        return
    key = [-face * (it.cx - x) for it in items]
    lo, hi = min(key), max(key)
    for it, k in zip(items, key):
        it.poff = seg(off * 1.6 - 0.6 * (1.0 - (k - lo) / (hi - lo + 1e-9)), 0.0, 1.0)


def _draw_on(items, d: float, overlap: float = 0.25):
    """A person draws itself on (d 0..1): the lines one after another in paint order, each fill
    rubbed in as its own outline closes. (Never before it: a rub-out that arrives ahead of its line
    is a dark blot, and against a lit window a black one.)"""
    lines = [it for it in items if isinstance(it, Stroke)]
    n = max(1, len(lines))
    end = (n - 1) / n * (1.0 - overlap) + overlap + 1.0 / n
    span = {}
    for k, it in enumerate(lines):
        s0 = k / n * (1.0 - overlap)
        span[it.name] = (s0 / end, (s0 + overlap + 1.0 / n) / end)
        it.pon = seg(d, *span[it.name])
    for it in items:
        if isinstance(it, Fill):
            s0, s1 = span.get(it.name[:-5] if it.name.endswith(".fill") else it.name, (0.0, 1.0))
            it.pon = seg(d, s0 + 0.55 * (s1 - s0), min(1.0, s1 + 0.25 * (s1 - s0)))


def person_sketch(x: float, y: float, h: float, P: Pose = P_REST, kind: str = "pupil", face: int = 1, seed: int = 0,
                  a: float = 1.0, back: float = 0.0, dots: float = 0.0, head: float = 0.0, tilt: float = 0.0, col=None,
                  day: bool = False, far: float = 0.0, name: str = "person", variant: dict | None = None, wave: float = 0.0,
                  wag: float = 0.0) -> People:
    """One person as a Sketch of named strokes, for sets that draw on, are un-drawn and morph. Same
    arguments as person(); `day` picks the skin. Parts in paint order (present as the view needs them):
    arm_b leg_b leg_f bag skirt body body.shade strap_f strap_b head hair hair_far hair0 hair1 eye_l
    eye_r mouth arm_f, with bag.fill skirt.fill body.fill head.fill. `who[0]` holds its joints."""
    cols = _colours(day, seed, col, far)
    v = float(dots) - float(back)
    it, J = _build(x, y, h, P, kind, face, seed, a, v, dots, head, tilt, *cols, lod=1, variant=variant, day=day, wave=wave, wag=wag)
    return People(it, name, who=[dict(J, name=name, x=x, y=y, h=h, face=face, view=v)])


def person(F: Frame, x: float, y: float, h: float, P: Pose = P_REST, kind: str = "pupil", face: int = 1, seed: int = 0,
           a: float = 1.0, draw: float = 1.0, back: float = 0.0, dots: float = 0.0, head: float = 0.0, tilt: float = 0.0,
           col=None, far: float = 0.0, off: float = 0.0, variant: dict | None = None, wave: float = 0.0, wag: float = 0.0) -> dict:
    """Draw one of the other people standing on the world point (x, y), h tall, in pose P.

    kind: "pupil" (330..360 tall, a satchel), "coat" or "skirt" (the two adults, 520..560).
    face: +1 looks right / -1 left (in profile). back: 0 profile .. 1 seen from behind (the main view
    of the film). dots: 0 .. 1 seen from the front, with two dot eyes and a small mouth. The view is
    continuous: dots - back runs from -1 (back) through 0 (profile) to +1 (front); use turned(w).
    head: extra turn of the head in the same units (it leads a turn). tilt: sideways lean in radians.
    wave: 0..1 the near hand is lifted out to the side (hello; it reads in every view), wag: -1..1 swings it.
    draw: 0..1 the person is drawn on (limbs, garment, head, hair). off: 0..1 it is rubbed out again,
    the trailing side first, leaving a ghost. a: pressure. far: 0..1 dimmer (depth).
    col: line colour (default dim chalk at night; pencil in the day skin, where the jumper gets a pastel).
    variant: {"hair": "short" | "bob" | "tail" | "bunches" | "neat" | "bun", "satchel": False, "dress": True | False}
    (by default the seed decides hair and jumper or dress).
    Returns world points: head neck pel back ha_f ha_b sh_f sh_b an_f an_b top, and R (head radius).
    """
    z = F.cam.zoom
    hs = h * z
    sx, _ = F.cam.to_screen(x, y)
    seen = a > 0.003 and draw > 0.0 and off < 1.0 and -0.9 * hs <= sx <= F.w + 0.9 * hs
    lod = 2 if hs >= 420.0 else 1 if hs >= 150.0 else 0
    it, J = _build(x, y, h, P, kind, face, seed, a, float(dots) - float(back), dots if seen else 0.0, head, tilt,
                   *_colours(F.day, seed, col, far), lod=lod, variant=variant, day=F.day, wave=wave, wag=wag)
    if seen:
        _rub(it, off, x, face)
        if draw < 1.0:
            _draw_on(it, draw)
        Sketch(it).draw(F)
    return J


# --------------------------------------------------------------------------
# the classroom rows: pupils at their desks, seen from behind
# --------------------------------------------------------------------------
SITS = ("upright", "upright", "slumped", "propped")       # how a classmate sits (the seed picks one)
HAIRS = ("short", "tail", "bob", "bunches", "short")


def pupil(x: float, y: float, s: float = 1.0, seed: int = 1200, col=C.CHALK_DIM, a: float = 0.85, name: str = "pupil",
          far: float = 0.0, hair: str | None = None, desk: bool = True, sit: str | None = None, sway: float = 0.0) -> Sketch:
    """A classmate sitting at a desk, seen from behind: (x, y) = the floor under the chair, s = scale
    (1 = 192 world units from the floor to the top of the head, the desk 132 wide; 1.3 goes with the
    child's 380). The build of the standing pupils: a big round head of hair on a small jumper.
    Parts, in paint order: desk (+ .fill: the box under its top), desk.top, [desk.book], shin_l, shin_r, shoulders (+ .fill), [sleeve_l,
    sleeve_r: not in the far row], [arm], collar, head (+ .fill), hair, [hair0, hair1], seat, leg_l, leg_r (the chair's
    posts and legs), chair (+ .fill: the slat of its back), [bag (+ .fill), bag.handle].
    The seed is the pupil: how it sits, how it holds its head, its hair, its feet (side by side,
    crossed, one hooked round the chair leg), what lies on its desk, a satchel beside it.
    sit: "upright" | "slumped" (the head sunk between the shoulders) | "propped" (leaning on an elbow,
    the head in a hand), hair: "short" | "bob" | "tail" | "bunches": instead of the seed's choice.
    far: 0..1 dimmer tone (the far row). sway: -1..1 shifts its weight and tips its head a little (to
    keep a sitting child alive: drive it slowly, on the boil clock). The Sketch has .head (world
    centre) and .R (head radius)."""
    sd = int(seed) * 7
    sit = sit or SITS[int(rnd(seed, 21) * len(SITS)) % len(SITS)]
    prop, slumped = sit == "propped", sit == "slumped"
    side = 1.0 if rnd(seed, 22) < 0.5 else -1.0
    lean = 0.050 * rsym(seed, 1) + (0.095 * side if prop else 0.0) + 0.016 * sway       # everybody sits a little differently
    slump = 0.55 + 0.45 * rnd(seed, 2) if slumped else 0.22 * rnd(seed, 2)
    tilt = 0.12 * rsym(seed, 23) + (0.24 * side if prop else 0.0) + 0.075 * sway
    cl, sl = math.cos(lean), math.sin(lean)
    tone, tone_h = mix(TONE, C.PAPER, 0.5 * far), mix(TONE_HEAD, C.PAPER, 0.5 * far)
    wob = min(1.0, max(0.3, s)) * 0.8
    kw = dict(wob=wob, taper=0.7, step=5.0)
    kw_l = dict(wob=wob, taper=0.7, step=5.0, edge=0.0)
    kw_s = dict(wob=wob * 0.6, taper=0.55, edge=0.0, step=3.5)
    SEAT = 57.0

    def T(pts, body=False):
        q = np.asarray(pts, dtype=np.float64)
        dx, du = q[..., 0], q[..., 1]
        if body:                                         # the upper body leans about the seat
            du0 = du - SEAT
            dx, du = dx * cl + du0 * sl, SEAT - dx * sl + du0 * cl
        return np.stack([x + dx * s, y - du * s], axis=-1)

    it = []
    if desk:                                             # beyond the pupil: the box under the top (rubbed in), two legs, the top
        bx_ = T([(-58, 99), (-57, 77), (57, 78), (58, 99)])
        it.append(Fill(np.vstack([bx_, bx_[:1]]), tone, 0.6, 9.0, 4.0, 0.0, sd + 37, knock=C.KNOCK, base=0.40 * a, name="desk.fill"))
        it.append(Stroke(T([(-55, -2), (-57, 77), (57, 78), (56, -2)]), col, 3.2 * s, a * 0.66, sd + 1, "desk", **kw_l))
        it.append(Stroke(T([(-66, 100), (-20, 101), (30, 100), (66, 101)]), col, 3.6 * s, a * 0.88, sd + 30, "desk.top", **kw_l))
        if rnd(seed, 24) < 0.55:                         # something lies on it: a book or two, beside the elbow
            bx = -side * (46.0 + 6.0 * rnd(seed, 25))
            bw, bh = 11.0 + 5.0 * rnd(seed, 26), 7.0 + 6.0 * rnd(seed, 27)
            it.append(Stroke(T([(bx - bw, 101), (bx - bw + 1, 101 + bh), (bx + bw, 102 + bh), (bx + bw + 1, 101)]), col, 2.8 * s,
                             a * 0.75, sd + 31, "desk.book", **kw_s))
    # its own legs under the seat, between the chair's
    feet = int(rnd(seed, 28) * 3) % 3
    fs = 1.0 if rnd(seed, 29) < 0.5 else -1.0
    if feet == 1:                                        # ankles crossed
        shins = ([(-11, SEAT - 2), (-3, 30), (8, 5), (19, 3)], [(11, SEAT - 2), (3, 30), (-8, 5), (-19, 3)])
    elif feet == 2:                                      # one foot hooked round the chair leg
        shins = ([(-fs * 11, SEAT - 2), (-fs * 12, 28), (-fs * 12, 4), (-fs * 23, 2)],
                 [(fs * 11, SEAT - 2), (fs * 20, 36), (fs * 33, 19), (fs * 45, 15)])
    else:
        shins = ([(-11, SEAT - 2), (-13, 28), (-12, 4), (-23, 2)], [(11, SEAT - 2), (12, 28), (13, 4), (24, 2)])
    for nm, q, k in (("shin_l", shins[0], 16), ("shin_r", shins[1], 17)):
        it.append(Stroke(spline(T(q), 9), col, 3.2 * s, a * 0.78, sd + k, nm, **kw_l))
    # the jumper: small sloping shoulders, the sleeves out to the elbows that rest on the desk
    sw = 1.0 + 0.07 * rsym(seed, 3)
    sh_y = 112.0 - 3.0 * slump
    hunch = 5.0 * slump                                  # slumped: the shoulders come up round the head
    ell, elr = (8.0 * rnd(seed, 34) + (9.0 if prop and side < 0 else 0.0)), (8.0 * rnd(seed, 35) + (9.0 if prop and side > 0 else 0.0))
    bell = spline(T([(-34 * sw, SEAT - 1), (-37 * sw, 72), (-(38 + ell) * sw, 91), (-(31 + 0.4 * ell) * sw, sh_y - 7 + hunch),
                     (-15, sh_y + 2 + 0.6 * hunch), (0, sh_y + 4), (15, sh_y + 2 + 0.6 * hunch), ((31 + 0.4 * elr) * sw, sh_y - 7 + hunch),
                     ((38 + elr) * sw, 91), (37 * sw, 72), (34 * sw, SEAT - 1)], True), 32)
    it.append(Fill(np.vstack([bell, bell[:1]]), tone, 0.6, 9.0, 4.0, 0.0, sd + 2, knock=C.KNOCK, base=0.55 * a, name="shoulders.fill"))
    it.append(Stroke(bell, col, 4.0 * s, a, sd + 3, "shoulders", **kw))
    for nm, sg, k, el in (("sleeve_l", -1.0, 32, ell), ("sleeve_r", 1.0, 33, elr)) if far < 0.5 else ():     # where each arm lies against the body
        it.append(Stroke(spline(T([(sg * 22 * sw, sh_y - 8 + hunch), (sg * (26 + 0.5 * el) * sw, 93), (sg * 25 * sw, 78)], True), 7), col,
                         2.8 * s, a * 0.60, sd + k, nm, **kw_s))
    R = 37.0 * s
    hc = T([(4.0 * rsym(seed, 4) + (9.0 * side if prop else 0.0), sh_y + 39.0 - 10.0 * slump - (3.0 if prop else 0.0))], True)[0]
    if prop:                                             # the forearm, from the elbow on the desk up to the cheek
        el_ = T([(side * (45 + (ell if side < 0 else elr)) * sw, 97)], True)[0]
        hand = hc + np.array([side * 0.80 * R, 0.52 * R])
        it.append(Stroke(spline(np.array([el_, (el_ + hand) / 2 + (side * 5.0 * s, 0.0), hand]), 8), col, 3.8 * s, a * 0.95, sd + 36, "arm", **kw_l))
    it.append(Stroke(spline(T([(-13, sh_y + 2), (-7, sh_y - 4), (0, sh_y - 6), (7, sh_y - 4), (13, sh_y + 2)], True), 9), col, 2.8 * s,
                     a * 0.75, sd + 4, "collar", **kw_s))
    ha = -(lean + tilt)
    hp = blob(hc[0], hc[1], R * 1.03, R * 0.975, sd + 5, 0.022, 24, rot=ha)
    it.append(Fill(hp, tone_h, 0.6, 9.0, 4.0, 0.0, sd + 6, knock=C.KNOCK, base=0.58 * a, name="head.fill"))
    it.append(Stroke(np.vstack([hp, hp[1:3]]), col, 3.9 * s, a, sd + 7, "head", **kw))
    style = hair or HAIRS[int(rnd(seed, 31) * len(HAIRS)) % len(HAIRS)]
    ex, ey = np.array([math.cos(ha), math.sin(ha)]), np.array([-math.sin(ha), math.cos(ha)])
    main, _ = _hair_rows(style, int(seed), -math.pi / 2)
    if main is not None:
        it.append(Stroke(hc + (main[:, 0] * R)[:, None] * ex - (main[:, 1] * R)[:, None] * ey, col, 7.0 * s, a * 0.80, sd + 8, "hair",
                         wob=wob * 0.7, taper=0.5, edge=0.0, grain="mid", step=4.0))
    for i, Q in enumerate(_hair_extra(style, int(seed), 1.0)):
        it.append(Stroke(hc + (Q[:, 2] * R)[:, None] * ex - (Q[:, 1] * R)[:, None] * ey, col, 5.2 * s, a * 0.95, sd + 9 + i, f"hair{i}",
                         **kw_s))
    # the chair, nearest to us and lightly drawn: the seat, the two posts that are its back legs, the slat across the back
    ca = a * 0.82
    it.append(Stroke(T([(-42, SEAT), (-10, SEAT + 1), (42, SEAT + 1)]), col, 3.4 * s, ca, sd + 13, "seat", **kw_l))
    it.append(Stroke(T([(-24, 96), (-25, SEAT), (-33, -3)]), col, 3.0 * s, ca, sd + 14, "leg_l", **kw_l))
    it.append(Stroke(T([(24, 96), (25, SEAT), (33, -3)]), col, 3.0 * s, ca, sd + 15, "leg_r", **kw_l))
    fr = rrect_pts(-30, -96, 30, -85, 5, 4)
    bd = T(np.stack([fr[:, 0], -fr[:, 1]], axis=1))
    it.append(Fill(bd, mix(tone, col, 0.30), 0.6, 9.0, 4.0, 0.0, sd + 11, knock=tone, base=0.50 * a, name="chair.fill"))
    it.append(Stroke(np.vstack([bd, bd[1:3]]), col, 3.0 * s, ca, sd + 12, "chair", **kw_l))
    if rnd(seed, 6) < 0.45:                              # a satchel standing by the desk
        sgn = 1.0 if rnd(seed, 7) < 0.6 else -1.0
        q = rrect_pts(70, -31, 108, -1, 8, 3)
        bp = T(np.stack([sgn * q[:, 0], -q[:, 1]], axis=1))
        it.append(Fill(bp, tone, 0.6, 9.0, 4.0, 0.0, sd + 17, knock=C.KNOCK, base=0.5 * a, name="bag.fill"))
        fl = T([(sgn * 70, 20), (sgn * 89, 16), (sgn * 108, 20)])
        i0 = int(np.argmin(((bp - fl[0]) ** 2).sum(1)))
        it.append(Stroke(np.vstack([bp[i0:-1], bp[:i0 + 1], fl[1:]]), col, 3.2 * s, a * 0.85, sd + 18, "bag", **kw_l))
        it.append(Stroke(spline(T([(sgn * 80, 31), (sgn * 83, 41), (sgn * 95, 41), (sgn * 98, 31)]), 8), col, 2.8 * s, a * 0.8, sd + 19,
                         "bag.handle", **kw_s))
    P_ = Sketch(it, name)
    P_.head, P_.R = hc, R
    return P_


def class_rows(far=((980.0, 1220.0, 1460.0), FLOOR - 4.0, 1.16), near=((860.0, 1100.0, 1340.0, 1580.0), FLOOR + 84.0, 1.40),
               seed: int = 1400, a: float = 0.95, name: str = "rows", t: float | None = None) -> People:
    """The rows of the classroom from behind: two rows in depth, each (xs, floor y, scale). The far
    row (parts b0.., drawn first, dimmer and thinner) sits against the wall, on the ground line; the
    near row (f0..) sits on the floor in front of it (lower in the picture, larger) and overlaps it:
    between and over its heads the far row shows from the shoulders up. The defaults fill world x
    780 to 1680 (inside the place the classroom set keeps free; a satchel may stand beside the last
    desk) and y 520 to 830, above the lyric band; the near pupils have the child's own size. Any other seats: class_rows(far=(xs, y, s), near=(xs, y, s)).
    t: pass F.tb and the class is alive: now and then somebody shifts on a chair or tips a head, slowly,
    each in its own time (most hardly at all); it stands still in the silences. None: nobody moves.
    Names: rows.b2.shoulders, rows.f3.chair, ... (the parts of pupil()). `who` lists every pupil (name,
    x, y, s, head, R) far row first; `.far` and `.near` are the two rows as Sketches (the same strokes),
    for a child that passes between them. The desk that stands apart is not here: it belongs to the set."""
    it, who, rows = [], [], {"b": [], "f": []}
    for tag, (xs, y, s), col, far_, sd in (("b", far, C.CHALK_FAR, 0.6, seed), ("f", near, C.CHALK_DIM, 0.0, seed + 100)):
        for j, x_ in enumerate(xs):
            nm = f"{tag}{j}"
            xj, sj = x_ + 10.0 * s * rsym(sd + j, 11), s * (1.0 + 0.05 * rsym(sd + j, 12))     # nobody sits on a grid
            k = j * 2 + (1 if tag == "b" else 0) + seed % 5                   # hair and posture go round, so that a row is mixed
            sway = 0.0
            if t is not None:                            # a slow shift of the weight, held most of the time
                q = math.sin(2.0 * math.pi * (t / (7.0 + 5.0 * rnd(sd + j, 14)) + rnd(sd + j, 15)))
                q2 = math.sin(2.0 * math.pi * (t / (11.0 + 6.0 * rnd(sd + j, 16)) + rnd(sd + j, 17)))
                sway = (0.25 + 0.75 * rnd(sd + j, 18) ** 2) * math.tanh(2.6 * q) * (0.6 + 0.4 * q2)
            S = pupil(xj, y, sj, sd + j * 20, col, a, nm, far=far_, hair=HAIRS[(k * 3) % len(HAIRS)],
                      sit=SITS[(k + (2 if tag == "b" else 0)) % len(SITS)] if rnd(sd + j, 13) < 0.8 else None, sway=sway)
            it.append(S)
            rows[tag].append(S)
            who.append(dict(name=f"{name}.{nm}", x=xj, y=y, s=sj, head=S.head, R=S.R))
    R = People(it, name, who=who)
    R.far, R.near = Sketch(rows["b"]), Sketch(rows["f"])
    return R


# --------------------------------------------------------------------------
# the stream on the corridor line
# --------------------------------------------------------------------------
class Walker:
    """One pupil of the stream: seed, h (height), m (mood of the walk), q (stride factor), d (+1 walks
    right / -1 left), T (the time it passes world x `x`), lane (+1 passes in front of the child, -1
    behind), v (world units a second), on / off ((t0, t1) it draws on / is rubbed out, or None)."""
    __slots__ = ("k", "seed", "h", "m", "q", "d", "T", "x", "lane", "ph0", "v", "on", "off", "strap", "hit", "reach")

    def __repr__(self):
        return f"Walker({self.k}, d={self.d:+d}, T={self.T:.2f}, lane={self.lane:+d}, h={self.h:.0f}, v={self.v:.0f})"

    def ph(self, t: float) -> float:
        """Phase of its walk cycle at time t: a foot comes down on every beat."""
        return (t - BEAT0) * STEP_RATE + self.ph0

    def at(self, t: float) -> float:
        """Its world x at time t (constant speed; the planted foot does not slide)."""
        return self.x + self.d * self.h * self.q * (walk(self.ph(t), self.m)[1] - walk(self.ph(self.T), self.m)[1])

    def pose(self, t: float) -> Pose:
        P = walk(self.ph(t), self.m)[0]
        P = P.but(ff=(P["ff"][0] * self.q, P["ff"][1]), fb=(P["fb"][0] * self.q, P["fb"][1]),
                  pel=(P["pel"][0], P["pel"][1] + _lift(self.q)))
        if self.strap:                                   # a hand on the strap of the satchel
            P = P.but(hf=(0.075, -0.085), ef=-1.0)
        return P


def _lift(q: float = 1.0) -> float:
    """How much higher than the rig's trudge these people carry their hips when they walk: straighter
    legs, an easier gait (less when the stride is long, so that the feet stay planted)."""
    return max(0.0, 0.026 - 0.06 * max(0.0, q - 1.0))


def walkers(t0: float, t1: float, x: float, hits=(), seed: int = 31, every: float = 1.5, reach: float = 1500.0,
            h=(326.0, 362.0), back_every: int = 3, fade: float = 2.2, front: float = 0.5,
            front_from: float | None = None, hit_lane: int = -1, clear=()) -> tuple:
    """The stream of pupils on the corridor line between t0 and t1, as a tuple of Walker.

    Everyone walks one step per beat. x: the world x the passes are timed against (where the child
    stands). hits: times at which a pupil coming the other way (walking left) passes x exactly: the
    shoulder contacts (lane hit_lane: -1 = it passes behind the child, who stays readable).
    every: seconds between passes (1.5 = two per bar). front: the share that passes in front of the
    child, from the time front_from on (None = always; before it everybody passes behind).
    clear: ((t0, t1), ...) spans in which nobody may pass IN FRONT of x (whoever would, passes behind
    instead): the child's face is hidden for about 0.7 s by each pupil that passes in front of it, so
    name here the moments at which it acts.
    back_every: every n-th pupil overtakes from behind (walks right). reach: they exist only within
    x - reach .. x + reach. Those already inside at t0 draw themselves on in the first beats; in the
    last `fade` seconds nobody new comes and those still there are rubbed out one after another.
    Deterministic in its arguments (cached)."""
    return _walkers(float(t0), float(t1), float(x), tuple(float(v) for v in hits), int(seed), float(every), float(reach),
                    (float(h[0]), float(h[1])), int(back_every), float(fade), float(front),
                    None if front_from is None else float(front_from), int(hit_lane),
                    tuple((float(c0), float(c1)) for c0, c1 in clear))


COVER = 0.45                     # seconds before and after its pass during which a pupil in front hides the child's head


@lru_cache(maxsize=16)
def _walkers(t0, t1, x, hits, seed, every, reach, h, back_every, fade, front, front_from, hit_lane, clear=()):
    out = []
    plan = []                                            # (pass time, direction, lane, is a hit)
    k, nf, T = 0, 0, t0 - 6.0
    while T < t1 + 6.0:
        d = 1 if back_every and k % back_every == back_every - 1 else -1
        Tj = T + every * 0.28 * rsym(seed * 131 + k, 1)
        if all(abs(Tj - th) > 0.62 * every for th in hits) or d > 0:
            lane = -1
            if front_from is None or Tj >= front_from:   # evenly: every 1 / front-th passes in front
                nf += 1
                lane = 1 if int(nf * front + 1e-9) > int((nf - 1) * front + 1e-9) else -1
                if lane > 0 and any(c0 - COVER <= Tj <= c1 + COVER for c0, c1 in clear):
                    lane = -1                            # not now: the child is acting
            plan.append((Tj, d, lane, False))
        T += every
        k += 1
    plan += [(float(th), -1, hit_lane, True) for th in hits]
    plan.sort(key=lambda p: p[0])
    for k, (T, d, lane, hit) in enumerate(plan):
        w = Walker()
        sd = seed * 131 + int(round(T * 7)) % 997 + k * 13
        w.k, w.seed, w.d, w.T, w.x, w.lane, w.hit = k, sd, d, T, float(x), lane, hit
        w.h = h[0] + (h[1] - h[0]) * rnd(sd, 3)
        w.m = 0.50 + 0.42 * rnd(sd, 4) + (0.12 if d > 0 else 0.0)        # who overtakes walks more briskly
        w.q = 0.92 + 0.20 * rnd(sd, 5) + (0.10 if d > 0 else 0.0)
        w.ph0 = 0.5 * int(rnd(sd, 6) * 2)
        w.strap = rnd(sd, 7) < 0.34
        w.v = w.h * w.q * (walk(1.0, w.m)[1] - walk(0.0, w.m)[1]) * STEP_RATE
        w.on = w.off = None
        w.reach = float(reach)
        t_in = T - reach / w.v                           # when it comes into reach, and leaves it
        t_out = T + reach / w.v
        if t_out < t0 or t_in > t1 - fade - 0.5:
            continue
        if t_in < t0:
            w.on = (t0, t0 + 0.55)                       # staggered below
        out.append(w)
    # those on the line when it begins draw on one per quarter beat, nearest the child first
    first = sorted((w for w in out if w.on), key=lambda w: abs(w.at(t0) - x))
    for i, w in enumerate(first):
        ta = t0 + 0.25 * BEAT * min(i, 5)
        w.on = (ta, ta + 0.5)
    # at the end they are rubbed out one after another, the farthest first
    last = sorted(out, key=lambda w: -abs(w.at(t1 - fade) - x))
    for i, w in enumerate(last):
        ta = t1 - fade + (fade - 1.0) * i / max(1, len(last) - 1)
        w.off = (ta, ta + 0.9)
    return tuple(out)


def passes(W, x: float | None = None, lane: int | None = None) -> list:
    """When the walkers pass world x (default: the x they were made for): [(time, walker), ...] in
    order of time. lane=+1: only those passing in front (the ones that can brush a shoulder)."""
    out = []
    for w in W:
        if lane is not None and w.lane != lane:
            continue
        t = w.T if x is None else w.T + (x - w.x) / (w.d * w.v)
        if x is not None:
            for _ in range(3):                           # exact for any gait: a few Newton steps on its true place
                t -= (w.at(t) - x) / (w.d * w.v)
        out.append((t, w))
    out.sort(key=lambda p: p[0])
    return out


def stream(F: Frame, W, y: float = FLOOR, t: float | None = None, lane: int | None = None, a: float = 1.0, col=None) -> list:
    """Draw the walkers W (from walkers()) at time t (default F.t) on the floor line y.

    lane: None draws everybody; -1 only those who pass behind the child, +1 only those who pass in
    front: call it twice, around the child. Returns [(walker, joints), ...] of those on screen."""
    t = F.t if t is None else t
    done = []
    l, _, r, _ = F.cam.view(95.0)
    for w in sorted(W, key=lambda w: (w.lane, rnd(w.seed, 9))):
        if lane is not None and w.lane != lane:
            continue
        on = 1.0 if w.on is None else seg(t, *w.on)
        off = 0.0 if w.off is None else seg(t, *w.off)
        if on <= 0.0 or off >= 1.0:
            continue
        wx = w.at(t)
        if wx < l or wx > r or abs(wx - w.x) > w.reach:
            continue
        near = w.lane > 0
        J = person(F, wx, y + (5.0 if near else -4.0), w.h * (1.03 if near else 0.97), w.pose(t), "pupil", w.d, w.seed, a=a,
                   draw=on, off=off, far=0.0 if near else 0.30, col=col)
        done.append((w, J))
    return done


# --------------------------------------------------------------------------
# the ring of backs, and the whispers
# --------------------------------------------------------------------------
def _lean_in(n: int, t: float, times, start: int, step: int, dur: float) -> dict:
    """Who leans to whom as a whisper passes: {j: [(partner, amount 0..1), ...]} at time t. Whoever
    passes it on leans toward the next one a moment before it leaves; whoever gets it leans in to
    take it, and straightens again."""
    out = {}
    for i, th in enumerate(times):
        j0, j1 = (start + step * i) % n, (start + step * (i + 1)) % n
        give = ease(seg(t, th - 0.26, th - 0.02)) * (1.0 - ease(seg(t, th + 0.6 * dur, th + dur + 0.30)))
        take = ease(seg(t, th - 0.06, th + 0.8 * dur)) * (1.0 - ease(seg(t, th + dur + 0.16, th + dur + 0.62)))
        if give > 0.0:
            out.setdefault(j0, []).append((j1, give))
        if take > 0.0:
            out.setdefault(j1, []).append((j0, 0.8 * take))
    return out


def ring_of_backs(cx: float, y: float = FLOOR, n: int = 7, rx: float | None = None, ry: float | None = None, h: float = 345.0,
                  seed: int = 1700, a: float = 1.0, inward: bool = True, close: float | None = None, col=None,
                  name: str = "ring", t: float | None = None, times=(), start: int = 0, step: int = 1, dur: float = 0.30) -> People:
    """Pupils standing in a loose ring round the world point (cx, y), as a Sketch: p0 .. p(n-1) in the
    order they stand round the ring (the order a whisper travels), painted far to near.

    rx, ry: radii of the ring on the ground (ry = how far the near ones stand below, the far ones
    above, the line; defaults 215, 40 for the huddle and 300, 62 round a child). inward=True: a
    huddle, everybody faces the middle, so from outside there are only backs (the child stands
    outside, at about cx - rx - 190). inward=False: everybody has turned its back on a child standing
    in the middle: backs behind it, shoulders at its sides. Nobody ever faces us: who would is seen
    in profile. close: how much of the circle they fill (default 1 = all round for the huddle; 0.72
    for the outward ring, which is left open on our side so that the child in it is seen: draw the
    child after those with y <= the line's).
    `who[j]`: name ("ring.p3"), x, y, h, head, R, back (between the shoulders: where a hand would touch),
    face, view. Parts of each: those of person_sketch (ring.p3.body, ring.p3.head, ...).
    t, times, start, step, dur: the arguments of whispers() (t = F.t). Given them, the ring is alive
    while the whisper passes: whoever passes it on leans toward the next one, whoever gets it leans
    in to take it and straightens again. Without them the ring stands still (only the line boils)."""
    people = []
    close = (1.0 if inward else 0.72) if close is None else close
    rx = (215.0 if inward else 300.0) if rx is None else rx
    ry = (40.0 if inward else 62.0) if ry is None else ry
    psis = [(j - (n - 1) / 2.0) * (2.0 * math.pi / n) * close + 0.16 * rsym(seed + j, 1) * (2.0 * math.pi / n) + (0.0 if inward else math.pi)
            for j in range(n)]                           # (the outward ring is gathered on the far side)
    pxs = [cx + rx * math.sin(psis[j]) * (1.0 + 0.06 * rsym(seed + j, 2)) * (1.0 if inward else 1.0 + 0.5 * max(0.0, math.cos(psis[j])))
           for j in range(n)]                            # (round a child, those nearest to us stand further out: they do not hide the others)
    leans = _lean_in(n, float(t), tuple(times), start, step, dur) if t is not None and len(times) else {}
    for j in range(n):
        psi = psis[j]
        d = math.cos(psi)                                # +1 nearest to us, -1 farthest
        px = pxs[j]
        py = y + ry * d
        lx = sum(am * (1.0 if pxs[k] >= px else -1.0) for k, am in leans.get(j, ()))      # leaning toward a neighbour, signed in x
        la = min(1.0, sum(am for _, am in leans.get(j, ())))
        sv = -d if inward else d                         # sine of the angle it is seen at (-1 = from behind)
        fx = -math.sin(psi) if inward else math.sin(psi)
        face = 1 if fx >= 0 else -1
        view = math.asin(max(-1.0, min(1.0, sv))) / (math.pi / 2)
        view = max(-1.0, min(0.0, view) if inward else min(-0.30, view - 0.30))   # (round a child, those at the sides show us a shoulder)
        sd = seed + j * 17
        P = P_REST.but(neck=0.05 + 0.10 * rnd(sd, 3) + 0.10 * la, bend=0.04 + 0.10 * rnd(sd, 4) + 0.08 * la, lean=0.03 * rnd(sd, 5),
                       ff=(0.030 + 0.02 * rnd(sd, 6), 0.0), fb=(-0.034 - 0.02 * rnd(sd, 7), 0.0))
        tilt = (-0.045 * math.sin(psi) if inward else 0.02 * math.sin(psi)) * abs(view) + 0.02 * rsym(sd, 8)
        tilt += 0.058 * lx * (0.45 + 0.55 * abs(view))   # (seen in profile, leaning sideways is mostly leaning into the picture)
        S = person_sketch(px, py, h * (1.0 + 0.055 * d) * (0.97 + 0.06 * rnd(sd, 9)), P, "pupil", face, sd, a, back=-view,
                          head=0.10 * rsym(sd, 10), tilt=tilt, col=col, far=0.30 * (1.0 - d), name=f"p{j}")
        people.append((d, j, S))
    items, who = [], [None] * n
    for d, j, S in sorted(people, key=lambda p: p[0]):
        items.append(S)
        w = S.who[0]
        w["name"] = f"{name}.p{j}"
        who[j] = w
    return People(items, name, who=who)


def undraw(S: Sketch, pt, t0: float, dur: float = 0.8) -> float:
    """Take a set back from a world point outward (a back un-drawing under the child's hand): every
    item gets its off time by its distance from `pt`, the nearest first; the whole takes `dur`
    seconds from t0. Returns the end time."""
    items = list(S)
    if not items:
        return t0
    px, py = float(pt[0]), float(pt[1])
    d = [math.hypot(float(it.P[:, 0].mean()) - px, float(it.P[:, 1].mean()) - py) for it in items]
    dm = max(d) + 1e-9
    for it, di in zip(items, d):
        ta = t0 + 0.55 * dur * di / dm
        it.off = (ta, ta + 0.45 * dur)
    return t0 + dur


def _knot(n: int, seed: int, ph: float):
    """A small tangle of loops, about one unit across (n points)."""
    u = np.linspace(0.0, 1.0, n)
    p1, p2, p3 = rnd(seed, 1) * 6.28, rnd(seed, 2) * 6.28, rnd(seed, 3) * 6.28
    th = u * 2.0 * math.pi * 4.6 + p1
    r = 0.30 + 0.20 * np.sin(u * 2.0 * math.pi * 1.7 + p2 + ph) + 0.10 * np.sin(u * 2.0 * math.pi * 3.1 + p3)
    cx = 0.20 * np.sin(u * 2.0 * math.pi * 1.3 + p3 + 0.7 * ph)
    cy = 0.14 * np.cos(u * 2.0 * math.pi * 0.9 + p1 - 0.5 * ph)
    return np.stack([cx + r * np.cos(th) * 1.15, cy + r * np.sin(th) * 0.85], axis=1)


def whisper(F: Frame, p0, p1, w: float, seed: int = 0, size: float = 46.0, a: float = 1.0, hop: float = 0.42, t: float | None = None):
    """A whisper: a small dark scribble hopping from world point p0 to p1 (w = 0 at p0 .. 1 at p1) in
    an arc `hop` times their distance high, a thin tail behind it. Never writing, never a face: only
    a knot of the same black crayon as the weight, with its pale dust. It churns on the boil clock
    (t: that clock, default F.tb); the hop itself is the caller's w (on F.t). Returns its world point."""
    if a <= 0.003:
        return None
    t = F.tb if t is None else t
    p0, p1 = np.asarray(p0, dtype=np.float64), np.asarray(p1, dtype=np.float64)
    w = min(1.0, max(0.0, float(w)))
    L = float(np.hypot(*(p1 - p0)))

    def at(q):
        q = np.asarray(q, dtype=np.float64)
        e = q * q * (3.0 - 2.0 * q)
        return np.stack([p0[0] + (p1[0] - p0[0]) * e, p0[1] + (p1[1] - p0[1]) * e - hop * L * np.sin(math.pi * q) ** 1.2], axis=-1)

    c = at(w)
    mov = math.sin(math.pi * w)                          # stretched along its way while it flies
    if mov > 0.02 and L > 1.0:
        tail = at(np.linspace(max(0.0, w - 0.34), w, 9))
        wig = size * 0.10 * np.sin(np.linspace(0.0, 9.0, 9) + seed) * np.linspace(0.0, 1.0, 9)
        tail[:, 1] += wig
        chalk(F, tail, C.GLOOM_EDGE, size * 0.085, 0.75 * a * mov, seed * 7 + 1, wob=0.3, taper=0.15, edge=0.0, step=3.5, floor=1.3)
        chalk(F, tail, C.GLOOM, size * 0.060, 0.90 * a * mov, seed * 7 + 2, wob=0.3, taper=0.15, edge=0.0, step=3.5, floor=1.1)
    K = _knot(46, seed, t * 2.6)
    d = at(min(1.0, w + 0.02)) - at(max(0.0, w - 0.02))
    ang = math.atan2(d[1], d[0]) if mov > 0.02 else 0.0
    ca, sa = math.cos(ang), math.sin(ang)
    K = K * (1.0 + 0.30 * mov, 1.0 - 0.18 * mov)
    K = np.stack([K[:, 0] * ca - K[:, 1] * sa, K[:, 0] * sa + K[:, 1] * ca], axis=1) * size + c
    pale = mix(C.GLOOM_EDGE, C.CHALK_DIM, 0.55)
    scrib(F, K + (K - c) * 0.34, pale, size * 0.10, 0.70 * a, "sparse", floor=1.5)                   # its pale dust
    scrib(F, K, C.GLOOM, size * 0.12, 0.97 * a, "dense", floor=1.7)
    scrib(F, K[3:20] + (K[3:20] - c) * 0.16, pale, size * 0.045, 0.85 * a, "mid", floor=1.2)         # fresh pale loops over the black
    return c


def whispers(F: Frame, heads, times, dur: float = 0.30, start: int = 0, step: int = 1, seed: int = 0, size: float = 46.0,
             a: float = 1.0, lead: float = 0.35, tail: float = 0.6, r: float = 52.0, t: float | None = None):
    """A whisper passing from head to head: at each of `times` it hops from one head to the next.

    heads: a People (ring_of_backs(...): its heads and their radii, in ring order) or a list of world
    head centres with r = their radius. start: the head it begins at; step: +1 / -1 the way round.
    It sits at the upper edge of a head, on the side of the next one (never on a face), appears
    `lead` seconds before the first hop and is gone `tail` seconds after the last has landed.
    t: the acting time (default F.t). Returns its world point, or None when there is none."""
    t = F.t if t is None else t
    if isinstance(heads, People):
        pts, rr = heads.heads, [w["R"] for w in heads.who]
    else:
        pts, rr = list(heads), [r] * len(heads)
    n = len(pts)
    if not times or t < times[0] - lead or t > times[-1] + dur + tail:
        return None
    grow = seg(t, times[0] - lead, times[0] - lead + 0.22) * (1.0 - seg(t, times[-1] + dur + tail - 0.3, times[-1] + dur + tail))
    i = sum(1 for th in times if t >= th + dur)          # hops finished
    j0 = start + step * i

    def perch(j):                                        # the upper edge of head j, toward the head it goes to next
        hx, hy = pts[j % n]
        sg = 1.0 if pts[(j + step) % n][0] >= hx else -1.0
        return np.array([hx + sg * 0.74 * rr[j % n], hy - 0.92 * rr[j % n] - 0.30 * size])

    if i < len(times) and t >= times[i]:
        return whisper(F, perch(j0), perch(j0 + step), (t - times[i]) / dur, seed + i, size, a * grow)
    return whisper(F, perch(j0), perch(j0), 0.0, seed + max(0, i - 1), size, a * grow)


# --------------------------------------------------------------------------
# the two adults at the home table
# --------------------------------------------------------------------------
def walk_off(t: float, x: float, face: int, h: float, start: float, steps: int = 6, m: float = 0.62, rest: Pose = P_AWAY):
    """A person leaving: from standing at world x it walks off the way `face` points, one step per
    beat from `start`, `steps` steps (then it stands again). Returns (pose, x, face, t0, t1) like the
    rig's walk_to: person(F, W[1], y, h, W[0], kind, W[2]). m: mood of the walk (0 trudge .. 1 light)."""
    dist = h * (walk(1.0, m)[1] - walk(0.0, m)[1]) * 0.5 * (steps + 0.9)
    W = walk_to(t, x, x + face * dist, h, start=start, m=m, rate=STEP_RATE, rest=rest, rest0=rest)
    k = seg(t, W.t0, W.t0 + BEAT) * (1.0 - seg(t, W.t1 - BEAT, W.t1))      # an easier gait than the rig's trudge
    P = W.pose.but(pel=(W.pose["pel"][0], W.pose["pel"][1] + _lift() * k)) if k > 0.0 else W.pose
    return P, W.x, W.face, W.t0, W.t1


RISE = 0.56                      # seconds a seated adult takes to stand up before its first step


def home_adults(F: Frame, xl: float, xr: float, y: float = FLOOR, t: float | None = None, leave: float = 52.4, gone: float = 54.4,
                seat_y: float | None = None, hl: float = 545.0, hr: float = 528.0, kinds=("coat", "skirt"), seed: int = 2100,
                a: float = 1.0, draw: float = 1.0, m: float = 0.62) -> tuple:
    """The two adults at either end of the home table (floor points xl, xr on y).

    seat_y=None: they stand, turned from each other (the left one faces left, the right one right;
    each a little turned away from us too). seat_y = world y of the chair seats: they sit on the two
    end chairs, facing the table; at `leave` they stand up and turn their backs to each other.
    Either way they then walk away to opposite sides, one step per beat, and are rubbed out as they
    go: by `gone` nothing is left but a fading ghost. No gesture, no scene: two people who no longer
    face each other. draw: 0..1 they are drawn on. Returns the joints of both (left, right)."""
    t = F.t if t is None else t
    out = []
    for i, (x0, face, h, kind) in enumerate(((xl, -1, hl, kinds[0]), (xr, 1, hr, kinds[1]))):
        t0 = leave + 0.12 * i
        br = 0.004 * math.sin(F.tb * 2 * math.pi / (4.6 + 0.7 * i) + i) * (1.0 - seg(t, t0 - 0.6, t0))  # alive: a slow breath (boil clock)
        if seat_y is None:
            Pw, wx, _, w0, _ = walk_off(t, x0, face, h, t0, m=m)
            go = ease(seg(t, t0 - 0.15, t0 + 0.55))      # the turn into the walk
            P = Pw if t > w0 else P_AWAY.but(pel=(0.0, P_AWAY["pel"][1] + br), bend=P_AWAY["bend"] - 4.0 * br)
            px, fc, back = wx, face, (0.30 - 0.08 * i) * (1.0 - go)
        else:
            Ps = P_SIT.but(pel=(-0.02, (y - seat_y) / h + 0.035 + br), ff=(0.125, 0.0), fb=(0.090, 0.0),
                           bend=P_SIT["bend"] - 4.0 * br)
            u = ease(seg(t, t0, t0 + RISE))              # standing up, the feet where they were
            w = ease(seg(t, t0 + 0.12, t0 + RISE + 0.20))   # turning away, through the back: the turn ends in the first step
            Pst = mixp(Ps, P_AWAY, u)
            x1 = x0 - face * h * (Ps["ff"][0] - P_AWAY["ff"][0])
            Pw, wx, _, w0, _ = walk_off(t, x1, face, h, t0 + RISE, m=m)
            P, px = (Pw, wx) if t > w0 else (Pst, x0 - face * h * (Ps["ff"][0] - Pst["ff"][0]))
            fc, back = (-face, 2.0 * w) if w < 0.5 else (face, 2.0 * (1.0 - w))
            t0 += RISE
        out.append(person(F, px, y, h, P, kind, fc, seed + i, a=a, draw=draw, back=back, off=seg(t, t0 + 0.75, gone + 0.25)))
    return tuple(out)


# --------------------------------------------------------------------------
# the family line: the child's drawing of three, hand in hand, come to stand on the ground line
# --------------------------------------------------------------------------
def long_line(x0: float, x1: float, y: float = FLOOR - 190.0, n: int = 6, seed: int = 2290, col=C.CHALK_COOL, a: float = 1.0,
              lw: float = 5.4, sag: float = 14.0, name: str = "line") -> Sketch:
    """One long hand-drawn line from world x0 to x1 at height y, as n strokes laid end to end (parts
    line.s0 .. line.s(n-1), left to right): what the ring of backs unrolls into, and what the family
    line's chain of arms comes out of. Declare the pairs of a morph on its pieces:
        morph(R, L, w, [(w["name"] + ".body", f"line.s{k}") for k, w in enumerate(backs left to right)])
        morph(L, S, w, [(f"line.s{k}", nm) for k, nm in enumerate(S.chain)])       # S = family_line(...), n = len(S.chain)
    sag: how much it hangs and wavers (world units)."""
    q = np.linspace(0.0, 1.0, 8 * n + 1)
    xs = x0 + (x1 - x0) * q
    ys = y + sag * np.sin(math.pi * q) * 0.6 + sag * 0.5 * np.sin(q * 9.0 + 6.28 * rnd(seed, 1)) + sag * 0.3 * np.sin(q * 21.0 + 6.28 * rnd(seed, 2))
    P = np.stack([xs, ys], axis=1)
    return Sketch([Stroke(P[8 * k:8 * k + 9], col, lw, a, seed + 1 + k, f"s{k}", wob=1.15, taper=0.85, step=5.0) for k in range(n)], name)


def family_line(x: float, y: float = FLOOR, hs: float = 318.0, ht: tuple = (520.0, 548.0), spread: float = 268.0,
                part: float = 0.0, slip: tuple = (0.0, 0.0), travel: float = 640.0, hands=None, small: bool = True,
                faces: float = 1.0, seed: int = 2300, col=C.CHALK_COOL, a: float = 1.0, lw: float = 5.4,
                name: str = "family") -> People:
    """Three drawn stick figures hand in hand, as the child draws them: two tall ones (a left, b right,
    heights ht) and a small one (c, height hs) between them at world x, all standing on y.

    part: 0..1 the line parts: the tall ones slide `travel` world units toward the two sides and
    their inner arms stretch into long lines that still end in the small one's hands.
    slip: (left, right) 0..1 each: that line slips out of the small hand and falls back to its figure.
    hands: (left point, right point) to end the lines somewhere else (the real child's own hands, with
    small=False: then the small figure is not drawn and the child stands in its place).
    faces: pressure of the dot eyes and the smiles (0 = none).
    Parts: a.head a.body a.legs a.arm_out a.arm_in a.hair0-2 a.eye_l a.eye_r a.mouth, b.* likewise
    (b.hair), c.head c.body c.legs c.arm_l c.arm_r c.hair0-2 c.eye_l c.eye_r c.mouth. The whole chain of arms from
    a.arm_out to b.arm_out is drawn hand to hand, so it can come out of one long line (morph).
    Besides `who` (a, c, b: name, x, y, h, head, R, shoulder) the Sketch has `hands` = {"l", "r"}: where
    the two lines end, `ends` = {"l", "r"}: where the free ends of the lines are now (they leave
    the hands as they slip), and `chain`: the names of the arm strokes, hand to hand, left to right
    (six, or four with small=False): the pairs of a morph out of long_line()."""
    e_part = ease(min(1.0, max(0.0, part)))
    sl, sr = (min(1.0, max(0.0, float(v))) for v in slip)
    kw = dict(wob=1.15, taper=0.72, step=5.0)
    it, who = [], []

    def stick(nm, px, h, sd, R, tufts):
        """A stick figure: returns (shoulder point, head centre)."""
        top = y - h
        hc = np.array([px + 0.03 * h * rsym(sd, 1), top + R])
        hp = blob(hc[0], hc[1], R * (1.0 + 0.05 * rsym(sd, 2)), R * (0.96 + 0.05 * rsym(sd, 3)), sd, 0.05, 26, rot=0.3 * rsym(sd, 4))
        k0 = 6 + int(rnd(sd, 5) * 8)                     # the circle starts somewhere near the top and overshoots its start
        ring_ = np.vstack([hp[k0:-1], hp[:k0 + 4]])
        it.append(Stroke(ring_, col, lw, a, sd + 1, nm + ".head", **kw))
        nk = np.array([hc[0] + 0.01 * h * rsym(sd, 6), top + 2.0 * R - 2.0])
        hip = np.array([px + 0.012 * h * rsym(sd, 7), y - h * 0.36])
        it.append(Stroke(np.array([nk, (nk + hip) / 2 + (0.012 * h * rsym(sd, 8), 0.0), hip]), col, lw, a, sd + 2, nm + ".body", **kw))
        fl, fr = np.array([px - 0.125 * h, y - 1.0]), np.array([px + 0.135 * h * (0.9 + 0.2 * rnd(sd, 9)), y - 2.0 - 0.01 * h * rnd(sd, 10)])
        it.append(Stroke(np.array([fl - (0.055 * h, -1.0), fl, hip, fr, fr + (0.06 * h, 1.0)]), col, lw, a, sd + 3, nm + ".legs", **kw))
        sh = nk + (hip - nk) * 0.16
        who.append(dict(name=f"{name}.{nm}", x=px, y=y, h=h, head=hc, R=R, shoulder=sh))
        return sh, hc

    def face_of(nm, hc, R, sd, smile=1.0):
        if faces <= 0.003:
            return
        er = 0.085 * R
        for tag, ox in (("eye_l", -0.34), ("eye_r", 0.36)):
            q = hc + (ox * R, -0.08 * R + 0.04 * R * rsym(sd, 20 + int(ox * 10)))
            it.append(Stroke(np.array([q - (0.0, er * 0.3), q + (0.0, er * 0.3)]), col, er * 2.1, a * faces, sd + 11 + (ox > 0), nm + "." + tag,
                             wob=0.0, taper=1.0, edge=0.0, step=3.0, floor=1.9))
        mx = np.linspace(-0.30, 0.30, 6)
        mp = hc + np.stack([mx * R, (0.27 + 0.13 * smile * np.cos(mx * 5.0)) * R], axis=1)
        it.append(Stroke(mp, col, lw * 0.62, a * faces, sd + 13, nm + ".mouth", wob=0.3, taper=0.6, edge=0.0, step=3.0))

    def tufts_of(nm, hc, R, sd, kind):
        if kind == 1:                                    # long hair down both sides, drawn in one go over the top
            pts = [hc + (-1.16 * R, 0.86 * R), hc + (-1.12 * R, -0.10 * R), hc + (-0.74 * R, -0.86 * R), hc + (0.0, -1.14 * R),
                   hc + (0.76 * R, -0.84 * R), hc + (1.12 * R, -0.08 * R), hc + (1.18 * R, 0.90 * R)]
            it.append(Stroke(spline(np.array(pts), 16), col, lw * 0.9, a * 0.95, sd + 15, nm + ".hair", wob=0.6, taper=0.6, edge=0.2, step=4.0))
            return
        # short ticks standing on the head (the small one's are the child's own tufts)
        offs, ln = ((-0.46, -0.06, 0.40), 0.46) if kind == 2 else ((-0.30, 0.05, 0.36), 0.24)
        for i, ox in enumerate(offs):
            an = ox * 1.15 + 0.25 * rsym(sd, 30 + i)
            b0 = hc + np.array([math.sin(ox * 1.05), -math.cos(ox * 1.05)]) * R * 0.96
            tip = b0 + np.array([math.sin(an), -math.cos(an)]) * R * ln * (0.8 + 0.4 * rnd(sd, 34 + i))
            it.append(Stroke(np.array([b0, (b0 + tip) / 2 + (0.03 * R * rsym(sd, 38 + i), 0.0), tip]), col, lw * 0.9, a * 0.95, sd + 15 + i,
                             f"{nm}.hair{i}", wob=0.4, taper=0.5, edge=0.2, step=3.5))

    xa = x - spread - travel * e_part
    xb = x + spread + travel * e_part
    # where the small one's hands are: out to the sides, a little higher and wider as it holds on
    hl0 = np.array([x - 0.42 * spread - 26.0 * e_part, y - hs * (0.585 + 0.07 * e_part)])
    hr0 = np.array([x + 0.42 * spread + 26.0 * e_part, y - hs * (0.585 + 0.07 * e_part)])
    Hl, Hr = (np.asarray(hands[0], dtype=np.float64), np.asarray(hands[1], dtype=np.float64)) if hands is not None else (hl0, hr0)

    def tall(nm, px, h, sd, side, H, s_, kind):
        R = 0.118 * h
        sh, hc = stick(nm, px, h, sd, R, kind)
        # the free arm: out and down
        out_ = sh + (side * -0.20 * h, 0.17 * h)
        arm_out = np.array([out_, (out_ + sh) / 2 + (0.0, 0.012 * h), sh])
        # the arm toward the middle: to the hand it holds; as the line parts it stretches, taut with a little sag
        n = 14
        q = np.linspace(0.0, 1.0, n)[:, None]
        L = float(np.hypot(*(H - sh)))
        sag = (0.045 * L * (1.0 - 0.6 * e_part) + 6.0) * np.sin(np.pi * q[:, 0])
        held = sh + (H - sh) * q + np.stack([np.zeros(n), sag], axis=1)
        rest = sh + (np.array([side * 0.19 * h, 0.20 * h])) * q + np.stack([np.zeros(n), 0.012 * h * np.sin(np.pi * q[:, 0])], axis=1)
        e = ease(s_)
        cur = held + (rest - held) * e
        # the slack runs out of the line as it falls back: a wave that dies away
        wave = math.sin(math.pi * s_) * 0.055 * L * np.sin(q[:, 0] * math.pi * 3.0 + 5.0 * s_) * q[:, 0]
        cur[:, 1] += wave + math.sin(math.pi * s_) * 0.10 * L * q[:, 0] ** 2
        arm_in = cur if side > 0 else cur[::-1]          # always drawn left to right, so the chain of arms is one line
        return sh, hc, R, arm_out if side > 0 else arm_out[::-1], arm_in, cur[-1]

    sha, hca, Ra, a_out, a_in, end_l = tall("a", xa, ht[0], seed + 100, 1, Hl, sl, 0)
    it.append(Stroke(a_out, col, lw, a, seed + 105, "a.arm_out", **kw))
    it.append(Stroke(a_in, col, lw, a, seed + 106, "a.arm_in", **kw))
    tufts_of("a", hca, Ra, seed + 100, 0)
    face_of("a", hca, Ra, seed + 100)
    if small:
        Rc = 0.170 * hs
        shc, hcc = stick("c", x, hs, seed + 200, Rc, 2)
        # its arms: up and out to the hands it holds; when a line has slipped the arm sinks
        for tag, H, s_, sgn, sd in (("arm_l", hl0, sl, -1.0, 205), ("arm_r", hr0, sr, 1.0, 206)):
            e = ease(seg(s_, 0.15, 0.9))
            hand = H + (np.array([x + sgn * 0.16 * hs, y - hs * 0.40]) - H) * e
            mid = (shc + hand) / 2 + (0.0, 0.02 * hs)
            P_ = np.array([hand, mid, shc]) if sgn < 0 else np.array([shc, mid, hand])
            it.append(Stroke(P_, col, lw, a, seed + sd, "c." + tag, **kw))
        tufts_of("c", hcc, Rc, seed + 200, 2)
        face_of("c", hcc, Rc, seed + 200, smile=1.0 - 1.7 * max(sl, sr) * 0.6 - 0.9 * e_part * 0.5)
    else:
        who.append(dict(name=f"{name}.c", x=x, y=y, h=hs, head=np.array([x, y - hs * 0.83]), R=0.17 * hs, shoulder=np.array([x, y - hs * 0.62])))
    shb, hcb, Rb, b_out, b_in, end_r = tall("b", xb, ht[1], seed + 300, -1, Hr, sr, 1)
    it.append(Stroke(b_in, col, lw, a, seed + 306, "b.arm_in", **kw))
    it.append(Stroke(b_out, col, lw, a, seed + 305, "b.arm_out", **kw))
    tufts_of("b", hcb, Rb, seed + 300, 1)
    face_of("b", hcb, Rb, seed + 300)
    S = People(it, name, who=sorted(who, key=lambda w: w["x"]))
    S.hands = {"l": Hl, "r": Hr}
    S.ends = {"l": end_l, "r": end_r}
    S.chain = [f"{name}.{nm}" for nm in (("a.arm_out", "a.arm_in", "c.arm_l", "c.arm_r", "b.arm_in", "b.arm_out") if small else
                                         ("a.arm_out", "a.arm_in", "b.arm_in", "b.arm_out"))]
    return S
