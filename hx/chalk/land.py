"""hx.chalk.land: the plain of the choruses and what towers over it.

  * plain(F, ...)            the bare, endless ground under the one ground line: furrows running to a
                             vanishing point on the horizon, puddles holding a pale reflection, tufts,
                             stones, a mist band, a few far low shapes. Self-similar in depth, so it is
                             the same kind of picture at zoom 1.6, 1.0 and 0.205 and rigid in between.
  * footsteps(F, xs, born)   the way already walked, one mark per step, fading with age.
  * back_figure, voice, house: one turned back / one speech balloon of crossed-out scribble / the
                             child's drawing of a house, torn down the middle (improved props).
  * tower_layout(child_x)    where the three groups stand in the wide frame, and the wide camera.
  * tower_backs, tower_voices, tower_house (or towers(L) for all three): the towering groups composed
                             for that frame: Sketch layers at camera depths (TowerGroup: .hit(t) draws
                             it on with a chorus hit, .draw(F)).
  * small_backs, small_voices, small_house: the same three, knee-high, for the last chorus.

Everything is in WORLD coordinates and goes through F.cam. Nothing here draws a floor line: the
ground line is ground_line(F). Night skin, cold chalks only (the amber is the friend's).
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from ..story import CHILD_H, FLOOR, FRIEND_FAR_1, WIDE_ZOOM, X2
from .core import (A, C, CX, CY, H, TAB, W, Cam, Frame, arc, blob, htab, mix, ramp, rnd, rsym, seg, sk, smooth, smudge,
                   spline, vn, wash, zigzag)
from .sketch import Fill, Sketch, Stroke

__all__ = ["ZOOM_WIDE", "plain", "puddles", "footsteps", "footfalls", "footprints", "back_figure", "voice", "house",
           "house_seam", "house_crack", "TowerGroup", "TowerLayout", "tower_layout", "tower_backs", "tower_voices", "tower_house", "Towers", "towers", "dark_above",
           "small_backs", "small_voices", "small_house"]

ZOOM_WIDE = WIDE_ZOOM             # the wide framing of the choruses (hx.story): the child 78 px tall, 9366 world units across


# ==========================================================================================
# a big hand: wobble baked into the points (the kit's own wobble is 1.7 world units, which is
# nothing on a line 2000 units long seen at the wide zoom)
# ==========================================================================================
def _dense(P, step: float):
    """Polyline with points added so that no segment is longer than `step` (the vertices are kept)."""
    P = np.asarray(P, dtype=np.float64)
    out = [P[:1]]
    for p, q in zip(P[:-1], P[1:]):
        n = max(1, int(math.ceil(math.hypot(q[0] - p[0], q[1] - p[1]) / step)))
        out.append(p + (q - p) * (np.arange(1, n + 1) / n)[:, None])
    return np.vstack(out)


def _hand(P, seed: int, amp: float, wave: float, step: float, ends: float = 0.4):
    """P with the slow wobble of a whole arm: amplitude amp, wavelength wave (world units), sampled
    every `step`. ends: how much of it the two ends keep (0 for an outline that must close)."""
    Q = _dense(P, step)
    if amp <= 0.0:
        return Q
    s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(Q[:, 0]), np.diff(Q[:, 1])))])
    L = s[-1] + 1e-9
    o = rnd(seed, 3) * 300.0
    u1, u2 = s / wave + o, s / (wave * 0.29) + o * 1.7
    dx = amp * ((2 * vn(u1, seed) - 1) + 0.38 * (2 * vn(u2, seed + 1) - 1))
    dy = amp * ((2 * vn(u1, seed + 2) - 1) + 0.38 * (2 * vn(u2, seed + 3) - 1))
    e = ends + (1.0 - ends) * smooth(np.minimum(s, L - s) / (0.12 * L + 1e-6))
    return Q + np.stack([dx * e, dy * e], axis=1)


class _Pen:
    """The hand that draws one prop of size `size` (world units): line width, colour, pressure, and
    a wobble that grows with the prop. Small props (under 520) keep the kit's own wobble."""

    def __init__(self, size: float, lw: float, col, a: float, seed: int, wob: float = 1.0, edge: float | None = None):
        self.size, self.lw, self.col, self.a, self.seed, self.n = float(size), float(lw), col, float(a), int(seed), 0
        self.edge = edge                                 # the dusty second pass of every line (None: the kit's own)
        self.big = size >= 520.0
        self.amp, self.wave, self.step = 0.0042 * size * wob, 0.21 * size, max(6.0, 0.0105 * size)
        self.wob = wob

    def _seed(self) -> int:
        self.n += 1
        return self.seed + self.n * 7

    def pts(self, P, amp: float = 1.0, ends: float = 0.4):
        """The wobbled points of a line (for an outline shared by a fill and a stroke)."""
        sd = self._seed()
        return (_hand(P, sd, self.amp * amp, self.wave, self.step, ends) if self.big else np.asarray(P, dtype=np.float64)), sd

    def stroke(self, P, name, w=1.0, a=1.0, col=None, amp=1.0, ends=0.4, done=None, **kw) -> Stroke:
        """A line. done = (points, seed) from pen.pts when the wobble is already in."""
        Q, sd = done if done is not None else self.pts(P, amp, ends)
        if self.edge is not None:
            kw.setdefault("edge", self.edge)
        if self.big:
            kw.setdefault("wob", 2.2)                    # the boil of a giant line: about 0.45 px on screen
            kw.setdefault("step", 12.0)                  # a line this long is sampled every 12 px: half the cost
            kw["baked"] = True
        else:
            kw.setdefault("wob", 0.85 * self.wob)
        return Stroke(Q, col or self.col, self.lw * w, min(1.0, self.a * a), sd, name, **kw)

    def closed(self, P, name, w=1.0, a=1.0, col=None, amp=1.0, **kw):
        """A closed outline that overshoots its start. Returns (the closed points, the Stroke)."""
        Q, sd = self.pts(P, amp, 0.0)
        n = max(2, len(Q) // 14)
        return Q, self.stroke(None, name, w, a, col, done=(np.vstack([Q, Q[1:n + 1]]), sd), **kw)

    def zig(self, poly, name, ang, gap, w=1.0, a=0.5, col=None, jit=0.5, over=0.35, grain="sparse", amp=0.7):
        """Colouring-in: a seated zigzag over a closed outline, as one stroke (or None if too small)."""
        sd = self._seed()
        Z = zigzag(poly, ang + 0.06 * rsym(sd, 9), gap, sd, jit=jit, over=over)
        if Z is None or len(Z) < 4:
            return None
        if self.big:
            Z = _hand(Z, sd, self.amp * amp, self.wave * 0.6, max(self.step, gap * 0.45))
        return Stroke(Z, col or self.col, self.lw * w, min(1.0, self.a * a), sd, name, baked=self.big, wob=0.6, boil=0.0,
                      edge=0.0, grain=grain, taper=0.55, var=0.38, step=12.0 if self.big else 6.0)


def _tone(P, name, col, base=0.55, knock=C.KNOCK, ang=0.8, gap=10.0, w=5.0, a=0.0, seed=0, grain="mid") -> Fill:
    """A rubbed base tone over a rub-out (and, with a > 0, the kit's own small hatch). The outline is
    thinned to at most about 90 points: its edge lies under a line anyway."""
    P = np.asarray(P, dtype=np.float64)
    n = max(1, len(P) // 90)
    if n > 1:
        P = np.vstack([P[::n], P[:1]])
    return Fill(P, col, ang, gap, w, a, seed, knock=knock, base=base, grain=grain, name=name)


def _deep(knock):
    """The darkest tone a prop may use, by the paper it is rubbed out of: deep night paper, or on
    the warm paper a soft pencil brown."""
    if knock is not None and sum(knock) > 1.5:
        return mix(C.PENCIL, C.DAY_SHADE, 0.55)
    return C.PAPER_DEEP


def _cover(P, name, col, base=0.9, knock=C.KNOCK) -> Fill:
    """A small part lying over another: one pass of dense tone (nothing, if nothing is rubbed out)."""
    return _tone(P, name, col, base if knock is not None else 0.0, None, grain="dense")


# which named parts are the big contour (drawn first), which are colouring-in (last); the rest is dressing
_CONTOUR = {"coat", "leg_l", "leg_r", "arm_l", "arm_r", "head", "balloon", "wall", "roof", "tear", "base"}
_HATCH = {"hatch", "hair"}
_FIRST = ("coat", "balloon", "roof", "wall", "tear", "leg_l", "leg_r", "arm_l", "arm_r", "base", "head")


def _stage(name: str) -> int:
    parts = name.split(".")
    if parts[-1] == "fill":
        parts = parts[:-1]
    if parts[-1] in _HATCH or (len(parts) > 1 and parts[-2] in _HATCH):
        return 2
    return 0 if parts[-1] in _CONTOUR else 1


# ==========================================================================================
# one turned back
# ==========================================================================================
def back_figure(x, y, h, seed=700, col=C.CHALK_FAR, a=1.0, lw=None, fill=(0.16, 0.19, 0.30), lean=0.0, tilt=0.0,
                name="back", kit="belt", detail=2, sink=0.0, loom=0.0, knock=C.KNOCK, girth=1.0, hem=0.375, stance=0.0,
                flare=0.0) -> Sketch:
    """A turned back, h tall, standing on the world point (x, y): a long coat, elbows out and hands
    gone into the pockets, legs like pillars, the back of a head. No face. Knee-high or enormous.

    lw: line width (default h / 125, at least 2.8). lean: the whole figure leans (dx per height).
    tilt: -1..1, one shoulder lower and the head to one side. kit: what it wears on its back:
    "belt" (half belt, two buttons), "satchel", "scarf" or "plain". detail: 2 all the dressing,
    1 coat, sleeves, collar, head and colouring-in, 0 the bare shape with a rubbed tone. sink: the legs run
    on below the ground by sink * h and have no shoes (a far figure whose feet are behind the horizon).
    loom: 0..1, seen from far below: wide at the feet, narrowing to a small head (the giants).
    fill: the tone of the coat; knock: what is rubbed out behind it (None: nothing).
    Its build (so that two backs are two people): girth: 0.85 slight .. 1.2 broad (shoulders, coat,
    legs). hem: where the coat ends, as a part of the height (0.30 a long coat .. 0.43 a short
    jacket). stance: -1..1, the weight on one leg, the other set out to that side. flare: 0..0.2,
    the coat widens toward its hem.
    Parts: coat (+ .fill .hatch) leg_l leg_r (+ .fill) arm_l arm_r (+ .fill) collar head (+ .fill)
    hair seam vent crease_l crease_r, and belt button_l button_r | satchel (+ .fill)
    flap strap_l strap_r | scarf (+ .fill) scarf_tail (+ .fill)."""
    lw = max(2.8, h / 125.0) if lw is None else lw
    pen = _Pen(h, lw, col, a, seed, edge=None if detail >= 2 else 0.0)
    dark = mix(fill, _deep(knock), 0.62)
    pale = mix(fill, col, 0.62)
    kk = C.KNOCK if knock is None else knock
    legk = None if knock is None else mix(knock, dark, 0.55)

    def PT(*uv, g=1.0):
        return np.array([(x + (u * g * (1.0 + loom * (0.30 - 0.62 * v)) + lean * v) * h, y - v * h) for u, v in uv])

    sh = 0.014 * tilt
    g = float(girth)
    hem_v = min(0.43, max(0.29, float(hem)))
    wf, wm = 0.172 * (1.0 + flare), 0.160 * (1.0 + 0.45 * flare)
    out = []
    # legs first in the paint order (the coat hangs over them): two pillars, the weight on one of them
    for side, nm in ((-1, "l"), (1, "r")):
        lg = 0.55 + 0.45 * g
        uo, ui = side * 0.128 * lg, side * 0.020
        so = side * 0.052 * abs(stance) if side * stance > 0.0 else 0.0       # this leg is set out to its side
        if sink > 0.0:
            leg = PT((uo, hem_v + 0.01), (uo * 0.97 + 0.6 * so, 0.12), (uo * 0.95 + so, -sink), (ui * 1.2 + so, -sink), (ui * 1.1 + 0.6 * so, 0.12),
                     (ui, hem_v + 0.01))
        else:
            leg = PT((uo, hem_v + 0.01), (uo * 0.965 + 0.5 * so, 0.20), (uo * 0.95 + so, 0.050), (uo * 1.10 + 1.25 * so, 0.036),
                     (uo * 1.13 + 1.3 * so, 0.004), (ui * 0.75 + so, 0.004), (ui * 0.85 + so, 0.036), (ui * 1.25 + so, 0.050),
                     (ui * 1.1 + 0.5 * so, 0.20), (ui, hem_v + 0.01))
        Q, sd = pen.pts(leg, 0.7)
        out.append(_tone(np.vstack([Q, Q[:1]]), f"leg_{nm}.fill", dark, 0.0, legk))
        out.append(pen.stroke(None, f"leg_{nm}", 1.0, 1.0, done=(Q, sd), taper=0.7, edge=0.0))
        if detail >= 2 and sink <= 0.0:
            out.append(pen.stroke(PT((uo * 0.93 + 0.5 * so, 0.215), (side * 0.078 * lg + 0.5 * so, 0.198 + 0.012 * (1 if so else 0)),
                                     (ui * 2.0 + 0.5 * so, 0.21)), f"crease_{nm}", 0.6, 0.65, edge=0.0))
    # the coat: one line from the hem up over the shoulders, down and back along the hem
    mid_v = max(0.52, hem_v + 0.11)
    body = spline(PT((-wf, hem_v), (-wm, mid_v), (-0.151, 0.66), (-0.155, 0.745 - sh), (-0.140, 0.786 - sh),
                     (-0.098, 0.809 - sh * 0.5), (-0.045, 0.820), (0.0, 0.822), (0.045, 0.820), (0.098, 0.809 + sh * 0.5),
                     (0.140, 0.786 + sh), (0.155, 0.745 + sh), (0.151, 0.66), (wm, mid_v), (wf, hem_v), g=g), 46)
    hem = spline(PT((wf, hem_v), (0.06, hem_v - 0.012 - 0.05 * flare), (-0.05, hem_v - 0.008 - 0.05 * flare), (-wf, hem_v), g=g), 8)
    coat, st = pen.closed(np.vstack([body, hem[1:]]), "coat", 1.1)
    out.append(_tone(coat, "coat.fill", fill, 0.66, knock) if detail >= 2 else _cover(coat, "coat.fill", mix(fill, kk, 0.3), 0.9, knock))
    if detail >= 1:
        z = pen.zig(coat, "coat.hatch", (1.02 if rnd(seed, 31) > 0.5 else 2.1) + 0.2 * rsym(seed, 32), 0.066 * h, 1.6, 0.72, pale, jit=0.6)
        if z is not None:
            out.append(z)
    out.append(st)
    if detail >= 2:
        out.append(pen.stroke(PT((-0.018, hem_v - 0.006), (0.0, min(0.50, hem_v + 0.087)), (0.020, hem_v - 0.008)), "vent", 0.6, 0.75, edge=0.0))
        if kit not in ("satchel", "belt"):
            out.append(pen.stroke(PT((0.004, 0.775), (-0.002, 0.50)), "seam", 0.55, 0.55, edge=0.0))
    # what it wears on its back
    if kit == "belt" and detail >= 2:
        out.append(pen.stroke(PT((-0.082, 0.588), (0.082, 0.593), (0.083, 0.558), (-0.081, 0.554), (-0.082, 0.588), (-0.02, 0.590), g=g),
                              "belt", 0.7, 0.85, edge=0.0))
        for sx, nm in ((-0.052, "l"), (0.052, "r")):
            cx_, cy_ = PT((sx, 0.573), g=g)[0]
            out.append(Fill(blob(cx_, cy_, 0.011 * h, 0.011 * h, seed + 60, 0.08, 12), mix(col, C.CHALK_COOL, 0.3), a=0.0, base=0.9 * a,
                            grain="dense", name=f"button_{nm}"))
    elif kit == "satchel" and detail >= 1:
        sat = np.vstack([arc(*PT((0.066, 0.740))[0], 0.030 * h, 0.030 * h, -math.pi / 2, 0, 5),
                         arc(*PT((0.070, 0.620))[0], 0.026 * h, 0.026 * h, 0, math.pi / 2, 5),
                         arc(*PT((-0.070, 0.620))[0], 0.026 * h, 0.026 * h, math.pi / 2, math.pi, 5),
                         arc(*PT((-0.066, 0.740))[0], 0.030 * h, 0.030 * h, math.pi, 1.5 * math.pi, 5)])
        Q, st = pen.closed(np.vstack([sat, sat[:1]]), "satchel", 0.9, amp=0.6)
        out.append(_cover(Q, "satchel.fill", mix(dark, kk, 0.3), 0.94, knock))
        out.append(st)
        if detail >= 2:
            out.append(pen.stroke(spline(PT((-0.096, 0.690), (-0.04, 0.674), (0.0, 0.662), (0.04, 0.674), (0.096, 0.690)), 10),
                                  "flap", 0.7, 0.85, edge=0.0))
            for sx, nm in ((-1, "l"), (1, "r")):
                out.append(pen.stroke(PT((sx * 0.070, 0.766), (sx * 0.082, 0.798), (sx * 0.088, 0.812)), f"strap_{nm}", 0.8, 0.8, edge=0.0))
    elif kit == "scarf" and detail >= 1:
        tail = PT((0.030, 0.806), (0.060, 0.71), (0.052, 0.600), (0.108, 0.594), (0.112, 0.71), (0.088, 0.806))
        Q, st = pen.closed(np.vstack([tail, tail[:1]]), "scarf_tail", 0.75, 0.9, amp=0.6)
        out.append(_tone(Q, "scarf_tail.fill", pale, 0.55, knock, ang=0.1, gap=max(5.0, 0.022 * h), w=max(2.5, 0.008 * h), a=0.55 * a, seed=seed + 73))
        out.append(st)
    # sleeves: elbows out, hands gone into the pockets
    for side, nm in ((-1, "l"), (1, "r")):
        s_ = sh * side
        eo = 1.0 + 0.09 * tilt * side                    # the elbow on the higher shoulder sticks out further
        outer = spline(PT((side * 0.149, 0.780 + s_), (side * 0.185 * eo, 0.69 + s_), (side * 0.210 * eo, 0.585 + s_ * 0.5),
                          (side * 0.184 * eo, 0.50), (side * 0.134, 0.462), g=g), 12)
        inner = spline(PT((side * 0.104, 0.478), (side * 0.143, 0.525), (side * 0.154 * eo, 0.585), (side * 0.132, 0.655),
                          (side * 0.123, 0.725 + s_), g=g), 10)
        Q, sd = pen.pts(np.vstack([outer, inner]), 0.7)
        if detail >= 1:
            out.append(_cover(np.vstack([Q, Q[:1]]), f"arm_{nm}.fill", mix(mix(fill, pale, 0.18), kk, 0.3), 0.92, knock))
        out.append(pen.stroke(None, f"arm_{nm}", 0.95, 0.95, done=(Q, sd), taper=0.6, edge=0.0))
    # collar (or the scarf round the neck) and the back of the head
    band = np.vstack([spline(PT((-0.080, 0.797), (-0.053, 0.846), (0.0, 0.856), (0.053, 0.846), (0.080, 0.797)), 10),
                      spline(PT((0.080, 0.797), (0.040, 0.785), (0.0, 0.775), (-0.040, 0.785), (-0.080, 0.797)), 8)[1:]])
    nm = "scarf" if kit == "scarf" else "collar"
    if detail >= 1:
        Q, st = pen.closed(band, nm, 0.8, 0.9, amp=0.5, edge=0.0)
        out.append(_cover(Q, nm + ".fill", mix(pale if kit == "scarf" else mix(fill, pale, 0.25), kk, 0.3), 0.92, knock))
        out.append(st)
    hx_, hy_ = PT((0.012 * tilt, 0.914))[0]
    r = 0.084 * h * (1.0 + loom * (0.30 - 0.62 * 0.914))
    Q, st = pen.closed(blob(hx_, hy_, r, r * 1.06, seed + 5, 0.035, 30), "head", 1.0, amp=0.5, edge=0.0)
    out.append(_cover(Q, "head.fill", mix(mix(fill, col, 0.25), kk, 0.3), 0.92, knock))
    if detail >= 1:
        z = pen.zig(Q, "hair", 0.55 + 0.3 * rsym(seed, 41), max(4.0, 0.020 * h), 0.9, 0.62, mix(fill, col, 0.7), jit=0.4, over=0.1, grain="mid")
        if z is not None:
            out.append(z)
    out.append(st)
    return Sketch(out, name)


# ==========================================================================================
# one voice
# ==========================================================================================
def _balloon_outline(x, y, rx, ry, tail, seed, style):
    """The closed outline of a balloon with its tail (drawn round the long way, the tail last), and
    the tip. style: "round", "box" or "spiky"."""
    if style == "spiky":
        ns = 13 + seed % 3
        j = np.arange(2 * ns)
        an = 2 * math.pi * (j + 0.20 * (2 * htab(j, 7, seed) - 1)) / (2 * ns)
        rad = np.where(j % 2 == 0, 1.10 + 0.13 * htab(j, 11, seed + 3), 0.86 + 0.05 * htab(j, 13, seed + 5))
        P = np.stack([x + rx * rad * np.cos(an), y + ry * rad * np.sin(an)], axis=1)
        m = 1
    else:
        n = 56
        an = np.linspace(0.0, 2 * math.pi, n, endpoint=False)
        p = 4.4 if style == "box" else 2.3
        c, s = np.cos(an), np.sin(an)
        rr = 1.0 + 0.035 * (2 * vn(an / (2 * math.pi) * 6.0 + seed, seed) - 1)
        P = np.stack([x + rx * rr * np.sign(c) * np.abs(c) ** (2 / p), y + ry * rr * np.sign(s) * np.abs(s) ** (2 / p)], axis=1)
        m = 3
    n = len(P)
    dx, dy = (tail[0] - x) / rx, (tail[1] - y) / ry
    i0 = int(np.argmax(((P[:, 0] - x) / rx) * dx + ((P[:, 1] - y) / ry) * dy))
    if style == "spiky" and i0 % 2 == 1:
        i0 = (i0 + 1) % n                              # the tail is one giant spike, from valley to valley
    ia, ib = (i0 - m) % n, (i0 + m) % n
    edge = 0.5 * (P[ia] + P[ib])
    v = np.asarray(tail, dtype=np.float64) - edge
    dist = float(np.hypot(*v)) + 1e-9
    ln = min(max(0.70 * dist, 0.6 * ry), 2.8 * ry, dist)
    tip = edge + v / dist * ln
    perp = np.array([-v[1], v[0]]) / dist
    bend = (0.10 + 0.08 * rnd(seed, 17)) * ln * (1 if rnd(seed, 18) > 0.5 else -1)
    q = np.linspace(0.0, 1.0, 9)[:, None]

    def side(p0):
        ctrl = 0.5 * (p0 + tip) + perp * bend
        return (1 - q) ** 2 * p0 + 2 * q * (1 - q) * ctrl + q ** 2 * tip

    idx = (ib + np.arange((ia - ib) % n + 1)) % n       # from one root of the tail round the long way to the other
    return np.vstack([P[idx], side(P[ia])[1:], side(P[ib])[::-1][1:]]), tip


def voice(x, y, rx, ry, tail, seed=800, col=C.CHALK_FAR, a=1.0, lw=None, lines=4, name="voice", style="round",
          cross="strike", fill=(0.17, 0.21, 0.34), full=1.0, knock=C.KNOCK) -> Sketch:
    """A voice: a speech balloon centred on the world point (x, y) with radii rx, ry, full of lines
    of scribble that have been crossed out (zigzag stands for writing: never letters), its tail
    aimed at the world point `tail`.

    style: "round", "box" or "spiky" (a shout). cross: how it was crossed out: "strike" (a hard line
    through every row), "scribble" (one tight back-and-forth over them), "x" or "slash". lines: rows
    of scribble. lw: line width (default from its size). full: 1 as said, 0 empty (the rows and the
    crossing-out are taken back). fill: the tone inside; knock: what is rubbed out behind it.
    Parts: balloon (+ .fill) row0.. cross0.."""
    size = 2.0 * max(rx, ry)
    lw = max(2.8, size / 150.0) if lw is None else lw
    pen = _Pen(size * 1.1, lw, col, a, seed, wob=0.8)
    P, _tip = _balloon_outline(x, y, rx, ry, tail, seed, style)
    Q, st = pen.closed(np.vstack([P, P[:1]]), "balloon", 1.1, amp=0.3 if style == "spiky" else 1.0, taper=0.6)
    out = [_tone(Q, "balloon.fill", fill, 0.62, knock), st]
    inner = 0.52 if style == "spiky" else 0.74
    span = (1.04 if style != "box" else 1.2) * ry * (0.60 if style == "spiky" else 1.0)
    pitch = span / max(1, lines - 1) if lines > 1 else ry * 0.5
    tp, am = pitch * 0.50, pitch * 0.27
    ends = []
    for j in range(lines):
        yy = y - 0.5 * span + j * pitch - 0.03 * ry
        hc = rx * inner * (1.0 if style == "box" else math.sqrt(max(0.10, 1.0 - ((yy - y) / (0.92 * ry)) ** 2)))
        x0 = x - hc * (0.96 - 0.10 * rnd(seed + j, 51))
        x1 = x - hc + 2 * hc * ((0.30 + 0.35 * rnd(seed + j, 52)) if j == lines - 1 else (0.72 + 0.28 * rnd(seed + j, 53)))
        k = max(6, int((x1 - x0) / (tp * 0.5)))
        i = np.arange(k)
        word = np.cumsum(htab(i, 17, seed * 7 + j * 29) < 0.12)       # a new word now and then
        gapm = np.concatenate([[False], np.diff(word) > 0])
        env = np.where(gapm | np.roll(gapm, 1), 0.10, 1.0)
        xs = x0 + (i + 0.5 * (2 * htab(i, 19, seed + j * 31) - 1) * 0.6) * (x1 - x0) / k
        ys = yy + (i % 2 * 2 - 1) * am * (0.55 + 0.75 * htab(i, 23, seed + j * 37)) * env + 0.25 * am * np.sin(i * 0.21 + j)
        out.append(Stroke(np.stack([xs, ys], axis=1), col, lw * 0.72, min(1.0, 0.85 * a), seed + 20 + j, f"row{j}", wob=0.5, step=3.5,
                          edge=0.0, grain="mid", taper=0.7, baked=pen.big))
        ends.append((x0, x1, yy))
    hard = mix(col, C.CHALK_COOL, 0.5)
    xa, xb = min(e[0] for e in ends), max(e[1] for e in ends)
    ya, yb = ends[0][2] - pitch * 0.5, ends[-1][2] + pitch * 0.5
    if cross == "x":
        c0 = spline(A((xa - 0.04 * rx, ya - 0.1 * pitch), (0.5 * (xa + xb) + 0.03 * rx, 0.5 * (ya + yb)), (xb + 0.05 * rx, yb + 0.2 * pitch)), 7)
        c1 = spline(A((xb + 0.02 * rx, ya - 0.2 * pitch), (0.5 * (xa + xb) - 0.04 * rx, 0.5 * (ya + yb)), (xa - 0.05 * rx, yb + 0.1 * pitch)), 7)
        out += [pen.stroke(c0, "cross0", 1.2, 1.0, hard, taper=0.35), pen.stroke(c1, "cross1", 1.2, 1.0, hard, taper=0.35)]
    elif cross == "strike":
        for j, (x0, x1, yy) in enumerate(ends):
            e0, e1 = pitch * 0.26 * rsym(seed + j, 57), pitch * 0.26 * rsym(seed + j, 58)
            pts = spline(A((x0 - (0.03 + 0.05 * rnd(seed + j, 60)) * rx, yy + e0),
                           (0.5 * (x0 + x1), yy + 0.5 * (e0 + e1) + pitch * 0.12 * rsym(seed + j, 59)),
                           (x1 + (0.03 + 0.07 * rnd(seed + j, 61)) * rx, yy + e1)), 9)
            out.append(pen.stroke(pts[::-1] if j % 2 else pts, f"cross{j}", 1.05, 1.0, hard, amp=1.8, taper=0.35, edge=0.12))
    else:
        if cross == "slash":
            Z = zigzag(A((xa, ya), (xb, ya), (xb, yb), (xa, yb), (xa, ya)), 1.12, (xb - xa) * 0.21, seed + 9, jit=0.45, over=1.2)
        else:
            mx, hwd = 0.5 * (xa + xb), 0.40 * (xb - xa)
            Z = zigzag(A((mx - hwd, ya), (mx + hwd, ya), (mx + hwd, yb), (mx - hwd, yb), (mx - hwd, ya)), 0.10 + 0.08 * rsym(seed, 55),
                       pitch * 0.47, seed + 9, jit=0.7, over=1.6)
        if Z is not None:
            Z = _hand(Z, seed + 11, pen.amp * 0.8, pen.wave * 0.5, pen.step) if pen.big else Z
            out.append(Stroke(Z, hard, lw * 1.0, min(1.0, a), seed + 12, "cross0", baked=pen.big, wob=1.2 if pen.big else 0.8,
                              taper=0.4, var=0.3, edge=0.25))
    if full < 1.0:
        for it in out[2:]:
            it.poff = min(1.0, max(0.0, 1.0 - full))
    return Sketch(out, name)


# ==========================================================================================
# the house that came apart
# ==========================================================================================
def _house_frame(x, y, w, wall, pitch, split, side):
    """The map of one half (side -1 left, +1 right): house coordinates (X right of the middle, Y up
    from the ground) -> world. The half leans outward about its outer bottom corner and moves aside."""
    th = split * side * -1.0                            # left half: its top goes left
    ca, sa = math.cos(th), math.sin(th)
    px = side * w * 0.5
    shift = side * split * w * 0.42

    def T(X, Y):
        lx, ly = X - px, Y
        return (x + px + shift + lx * ca - ly * sa, y - (lx * sa + ly * ca))

    return T


def _tear(w, top, seed, n=11):
    """The torn edge in house coordinates, from the ridge down to the ground (both halves share it)."""
    ys = np.linspace(top, 0.0, n)
    xs = np.array([(-1) ** j * w * 0.036 * (0.45 + rnd(seed + j, 3)) for j in range(n)])
    xs[0] *= 0.4
    xs[-1] *= 0.5
    return xs, ys


def house(x, y, w=300.0, seed=600, col=C.CHALK_DIM, split: float = 0.0, a=1.0, lw=None, fill=None, roof=None,
          name="house", wall=0.88, pitch=0.62, detail=2, knock=C.KNOCK) -> Sketch:
    """The child's drawing of a house, x = its middle on the ground, w wide, (wall + pitch) * w tall.
    split > 0: torn down the middle, each half leaning outward by `split` radians about its outer
    bottom corner (the inner corners lift off the ground); at 0 the halves stand together, the tear
    still showing. fill / roof: colours of the rubbed tone of the walls / the roof (None: no tone,
    nothing rubbed out behind it); knock: the rub-out colour under them. detail: 2 tiles, chimney, door, window, attic window, colouring-in;
    1 door, window and colouring-in; 0 the bare outline.
    Parts per half (l, r): l.wall l.roof l.eave l.tear l.base (+ l.wall.fill l.roof.fill l.wall.hatch),
    l.tile0-2 l.attic l.door l.knob l.chimney, r.window r.bars r.sill."""
    hw, hr = wall * w, pitch * w
    lw = max(2.8, (hw + hr) / 125.0) if lw is None else lw
    pen = _Pen(hw + hr, lw, col, a, seed)
    tx, ty = _tear(w, hw + hr, seed)
    xe = float(np.interp(hw, ty[::-1], tx[::-1]))       # where the tear crosses the eave line
    ov = 0.085 * w
    slope = hr / (0.5 * w)
    bright = mix(col, C.CHALK, 0.45)
    fills, lines = [], []
    for side, nm in ((-1, "l"), (1, "r")):
        T = _house_frame(x, y, w, wall, pitch, split, side)

        def PT(*XY, T=T):
            return np.array([T(X, Y) for X, Y in XY])

        tear = PT(*zip(tx, ty))
        up = ty >= hw
        wallp = np.vstack([PT((side * w * 0.5, 0.0), (side * w * 0.5, hw), (xe, hw)), tear[~up]])
        roofp = np.vstack([PT((side * (w * 0.5 + ov), hw - ov * slope)), tear[up], PT((xe, hw), (side * w * 0.5, hw))])
        if fill is not None:
            fills.append(_tone(np.vstack([wallp, wallp[:1]]), f"{nm}.wall.fill", fill, 0.5, knock))
        if roof is not None:
            fills.append(_tone(np.vstack([roofp, roofp[:1]]), f"{nm}.roof.fill", roof, 0.62, knock))
        if detail >= 1 and fill is not None:
            z = pen.zig(np.vstack([wallp, wallp[:1]]), f"{nm}.wall.hatch", 0.95 * side + 0.1 * rsym(seed, 61 + side), 0.050 * w, 0.95, 0.42,
                        mix(fill, col, 0.5), over=0.25)
            if z is not None:
                fills.append(z)
        lines.append(pen.stroke(PT((side * w * 0.5, 0.0), (side * w * 0.5, hw)), f"{nm}.wall", 1.0, 1.0))
        lines.append(pen.stroke(PT((side * (w * 0.5 + ov), hw - ov * slope), (tx[0], hw + hr)), f"{nm}.roof", 1.15, 1.0))
        lines.append(pen.stroke(PT((side * w * 0.5, hw), (xe, hw + 0.004 * w)), f"{nm}.eave", 0.8, 0.8, edge=0.0))
        lines.append(pen.stroke(tear, f"{nm}.tear", 0.85, 1.0, bright, amp=0.25, taper=0.7))
        if split > 0.004:
            lines.append(pen.stroke(PT((side * w * 0.5, 0.0), (tx[-1], 0.0)), f"{nm}.base", 0.8, min(1.0, split * 14.0), edge=0.0))
        if detail >= 2:
            for j in range(3):                           # roof tiles: rows of scallops
                f = (j + 0.9) / 4.2
                yy = hw + hr * f
                xo = side * (w * 0.5 + ov) * (1.0 - f) - side * 0.04 * w
                xi = float(np.interp(yy, ty[::-1], tx[::-1])) + side * 0.03 * w
                k = max(2, int(abs(xo - xi) / (0.085 * w)))
                q = np.linspace(0.0, 1.0, k * 6 + 1)
                row = np.stack([xo + (xi - xo) * q, yy - 0.030 * w * np.abs(np.sin(q * k * math.pi)) + 0.012 * w], axis=1)
                lines.append(pen.stroke(PT(*row), f"{nm}.tile{j}", 0.6, 0.62, amp=0.3, edge=0.0, step=4.0))
            ra = 0.085 * w                               # the round attic window, torn in two
            a0, a1 = (math.pi / 2, 1.5 * math.pi) if side < 0 else (-math.pi / 2, math.pi / 2)
            ya_ = hw + hr * 0.30
            xa_ = float(np.interp(ya_, ty[::-1], tx[::-1]))
            ring_ = [(xa_ + side * 0.012 * w + ra * math.cos(q_), ya_ + ra * math.sin(q_)) for q_ in np.linspace(a0, a1, 9)]
            lines.append(pen.stroke(PT(*ring_), f"{nm}.attic", 0.7, 0.85, amp=0.3, edge=0.0))
        if side < 0:
            if detail >= 1:
                dl, dr, dh = -0.37 * w, -0.17 * w, 0.50 * hw
                door = [(dl, 0.0), (dl, dh * 0.8), (dl + 0.03 * w, dh * 0.96), (0.5 * (dl + dr), dh), (dr - 0.03 * w, dh * 0.96),
                        (dr, dh * 0.8), (dr, 0.0)]
                Q, sd = pen.pts(PT(*door), 0.5)
                if fill is not None:
                    fills.append(_tone(np.vstack([Q, Q[:1]]), "l.door.fill", mix(fill, _deep(knock), 0.6), 0.8, knock=None))
                lines.append(pen.stroke(None, "l.door", 0.85, 0.95, done=(Q, sd)))
                kx, ky = T(dr - 0.045 * w, dh * 0.45)
                lines.append(Fill(blob(kx, ky, 0.013 * w, 0.013 * w, seed + 81, 0.08, 10), bright, a=0.0, base=0.9 * a, grain="dense",
                                  name="l.knob"))
            if detail >= 2:
                c0, c1 = -0.36 * w, -0.25 * w
                ch = [(c0, hw + (0.5 * w + c0) * slope), (c0, hw + hr * 0.78), (c0 - 0.012 * w, hw + hr * 0.80), (c1 + 0.012 * w, hw + hr * 0.80),
                      (c1, hw + hr * 0.78), (c1, hw + (0.5 * w + c1) * slope)]
                lines.append(pen.stroke(PT(*ch), "l.chimney", 0.8, 0.9, amp=0.4))
        elif detail >= 1:
            wl, wr, wb, wt = 0.13 * w, 0.37 * w, 0.40 * hw, 0.72 * hw
            Q, st = pen.closed(PT((wl, wb), (wl, wt), (wr, wt), (wr, wb), (wl, wb)), "r.window", 0.85, 0.95, amp=0.4)
            if fill is not None:
                fills.append(_tone(Q, "r.window.fill", mix(fill, _deep(knock), 0.6), 0.8, knock=None))
            lines.append(st)
            wm, hm = 0.5 * (wl + wr), 0.5 * (wb + wt)
            lines.append(pen.stroke(PT((wm, wt), (wm, wb), (wm, hm), (wl, hm), (wr, hm)), "r.bars", 0.55, 0.8, amp=0.3, edge=0.0))
            if detail >= 2:
                lines.append(pen.stroke(PT((wl - 0.025 * w, wb - 0.012 * w), (wr + 0.025 * w, wb - 0.010 * w)), "r.sill", 0.9, 0.9, edge=0.0))
    return Sketch(fills + lines, name)


def house_crack(t: float, t_hit: float, split: float = 0.085, dur: float = 0.40) -> float:
    """The lean of the halves as a number of the song's time, for a house that draws itself on whole
    and comes apart WITH its hit: 0 until just after t_hit, open to `split` within `dur` seconds, a
    small shudder as it stops. Pass it as the `split` of tower_house / house (on F.t)."""
    e = t - t_hit
    if e <= 0.05:
        return 0.0
    k = 1.0 - (1.0 - min(1.0, (e - 0.05) / (0.85 * dur))) ** 2.6
    q = e - 0.75 * dur
    if q > 0.0:
        k += 0.18 * math.exp(-q / 0.12) * math.sin(q * 24.0)
    return max(0.0, split * k)


def house_seam(x, y, w=300.0, wall=0.88, pitch=0.62, split: float = 0.0):
    """Where the two halves of house(x, y, w, ...) meet or gape: world points on the tear's middle line
    {"top": the ridge, "roof": at two thirds of the roof, "wall": at half the wall's height, "foot": on
    the ground} and "gap": the width of the gape at each of them in world units (0 when split is 0).
    A strip of tape goes across the seam at "roof" and at "wall"."""
    hw, hr = wall * w, pitch * w
    Tl, Tr = _house_frame(x, y, w, wall, pitch, split, -1), _house_frame(x, y, w, wall, pitch, split, 1)
    out, gap = {}, {}
    for nm, Y in (("top", hw + hr), ("roof", hw + hr * 0.62), ("wall", hw * 0.5), ("foot", 0.0)):
        pl, pr = np.array(Tl(0.0, Y)), np.array(Tr(0.0, Y))
        out[nm] = (float(0.5 * (pl[0] + pr[0])), float(0.5 * (pl[1] + pr[1])))
        gap[nm] = float(np.hypot(*(pr - pl)))
    out["gap"] = gap
    return out


# ==========================================================================================
# a towering group: Sketch layers at camera depths
# ==========================================================================================
def _to_layer(sk: Sketch, ref: Cam, d: float) -> Sketch:
    """A sketch composed in the subject's plane as the camera `ref` sees it, moved to the layer of
    depth d (it looks the same through ref; under any other camera it parallaxes)."""
    if abs(d - 1.0) < 1e-6:
        return sk
    k = ref.zoom ** (1.0 - d)
    return sk.place(CX + (ref.cx - CX) * d - ref.cx * k, CY + (ref.cy - CY) * d - ref.cy * k, k)


class TowerGroup:
    """One towering group: Sketches at camera depths, painted far to near.

    layers: [[Sketch, depth, mist], ...] (a layer of depth < 1 is drawn through F.depth and, if mist
    is not None, only above the ground line: it stands behind the horizon, in `mist` of haze).
    members: the name prefixes of its things in draw-on order (the nearest first).
    anchors: world points and sizes in the subject's plane, as the reference camera sees them."""

    def __init__(self, layers, members=(), ref: Cam | None = None, anchors=None, name: str = ""):
        self.layers, self.members, self.ref = layers, tuple(members), ref or Cam()
        self.anchors, self.name = anchors or {}, name
        self.t_hit, self.punch, self._frac = None, 0.2, None

    # ---- its parts -------------------------------------------------------------------------
    def items(self) -> list:
        return [it for sk, _d, _m in self.layers for it in sk.items]

    def names(self) -> list:
        return [it.name for it in self.items()]

    def sub(self, *prefixes) -> Sketch:
        """The items named `prefix` or `prefix.something`, over all layers (the same objects)."""
        return Sketch(self.items()).sub(*prefixes)

    def __getitem__(self, key):
        return Sketch(self.items())[key]

    def copy(self) -> "TowerGroup":
        g = TowerGroup([[Sketch([it.copy() for it in sk.items]), d, m] for sk, d, m in self.layers], self.members, self.ref,
                       self.anchors, self.name)
        g.t_hit, g.punch, g._frac = self.t_hit, self.punch, self._fractions()
        return g

    # ---- times -----------------------------------------------------------------------------
    def _fractions(self) -> list:
        """(start, end) of every item's draw-on as fractions of its duration, in items() order."""
        if self._frac is not None:
            return self._frac
        n = max(1, len(self.members))
        items = self.items()

        def member(it):
            return next((i for i, m in enumerate(self.members) if it.name == m or it.name.startswith(m + ".")), 0)

        def rank(it):
            leaf = it.name.split(".")[-1]
            return _FIRST.index(leaf) if leaf in _FIRST else len(_FIRST)

        lines = sorted((it for it in items if not it.name.endswith(".fill")), key=lambda it: (member(it), _stage(it.name), rank(it)))
        count, seen, start, out = {}, {}, {}, {}
        for it in lines:
            key = (member(it), _stage(it.name))
            count[key] = count.get(key, 0) + 1
        for it in lines:
            mi, st = member(it), _stage(it.name)
            mo = 0.16 * mi / max(1, n - 1) if n > 1 else 0.0
            j = seen.get((mi, st), 0)
            seen[(mi, st)] = j + 1
            J = count[(mi, st)]
            if st == 0:
                a0, ln = mo + 0.20 * j / J, 0.28
            elif st == 1:
                a0, ln = 0.30 + 0.7 * mo + 0.28 * j / J, 0.28
            else:
                a0, ln = 0.30 + mo + 0.08 * j / J, 0.72
            start[it.name] = a0
            out[id(it)] = (a0, a0 + ln)
        for it in items:
            if it.name.endswith(".fill"):
                a0 = start.get(it.name[:-5], 0.2) + 0.10
                out[id(it)] = (a0, a0 + 0.40)
        self._frac = [out[id(it)] for it in items]
        return self._frac

    def schedule(self, t0: float = 0.0, dur: float = 1.0) -> dict:
        """{id(item): (t_start, t_end)} of a draw-on that starts at t0: the big contour of every member
        in the first half of `dur` (the nearest member first; the coat, the balloon, the roof before
        the rest), its dressing in the second half, the colouring-in trailing to 1.2 dur."""
        return {id(it): (t0 + dur * a0, t0 + dur * a1) for it, (a0, a1) in zip(self.items(), self._fractions())}

    def hit(self, t0: float, dur: float = 0.45, lead: float = 0.066) -> "TowerGroup":
        """It draws itself on with the chorus hit at t0, in about `dur` seconds, the chalk tip leading.
        The first stroke starts `lead` seconds before the hit, so that the big contour is half there
        on the hit and closed four frames later (it slams in ON the beat, not after it)."""
        sch = self.schedule(t0 - lead, dur)
        for it in self.items():
            it.on = sch[id(it)]
        self.t_hit = t0
        return self

    def off(self, t0: float, dur: float = 1.2) -> float:
        """It is taken back from t0: the colouring-in first, then the dressing, the big contour last,
        each line from both its ends, leaving a rubbed ghost that fades. Returns the end time."""
        for it in self.items():
            st = _stage(it.name)
            a0, a1 = ((0.35, 1.0), (0.15, 0.65), (0.0, 0.45))[st]
            if it.name.endswith(".fill"):
                a0, a1 = a0 + 0.25 * (a1 - a0), a1
            it.off = (t0 + dur * a0, t0 + dur * a1)
        return t0 + dur

    # ---- painting ---------------------------------------------------------------------------
    def draw(self, F: Frame, d: float | None = None, a: float = 1.0, thin: float = 1.0, tint=None, tint_w: float = 0.0,
             depths=None) -> None:
        """Paint it at F.t. a: pressure, thin: line-width factor (a group that has lost its pressure:
        a=0.45, thin=0.6). d: optional progress 0..1 of the whole draw-on instead of times.
        depths = (lo, hi): only the layers with lo <= depth < hi (to paint several groups far to near)."""
        if a <= 0.003:
            return
        keep = None
        if d is not None and d < 1.0:
            sch = self.schedule(0.0, 1.0 / 1.25)
            keep = [(it, it.pon) for it in self.items()]
            for it in self.items():
                it.pon = seg(d, *sch[id(it)])
        if self.t_hit is not None and self.punch > 0.0 and 0.0 <= F.t - self.t_hit < 1.5:
            thin = thin * (1.0 + self.punch * math.exp(-(F.t - self.t_hit) / 0.2))      # pressed hard as it lands
        mx0, mx1, mw = 1e9, -1e9, 0.0
        for sk, depth, mist in self.layers:
            if depths is not None and not (depths[0] <= depth < depths[1]):
                continue
            if depth >= 0.999:
                sk.draw(F, None, a, thin, tint, tint_w)
            elif mist is None:
                with F.depth(depth):
                    sk.draw(F, None, a, thin, tint, tint_w)
            else:
                with F.clip(rect=(-1e6, -1e6, 1e6, FLOOR)), F.depth(depth) as cd:
                    sk.draw(F, None, a, thin, tint, tint_w)
                    if mist > 0.0 and sk.items:
                        vis = max((seg(F.t, *it.on) if it.on else 1.0) * (1.0 - (seg(F.t, *it.off) if it.off else 0.0)) for it in sk.items)
                        mx0 = min(mx0, cd.to_screen(min(float(it.P[:, 0].min()) for it in sk.items), 0.0)[0])
                        mx1 = max(mx1, cd.to_screen(max(float(it.P[:, 0].max()) for it in sk.items), 0.0)[0])
                        mw = max(mw, mist * vis)
        if mw > 0.0:                                    # the horizon's mist in front of the far ones' legs
            sy = F.cam.to_screen(0.0, FLOOR)[1]
            with F.screen():
                smudge(F, 0.5 * (mx0 + mx1), sy - 4.0, 0.5 * (mx1 - mx0) + 150.0, 84.0, (0.27, 0.33, 0.52), 0.5 * mw * min(1.0, a), "soft", power=1.3)
        if keep is not None:
            for it, p in keep:
                it.pon = p

    def flat(self, cam: Cam | None = None) -> Sketch:
        """One Sketch in the subject's plane that looks like the group seen through `cam` (default:
        the camera it was composed for), without the mist: for a morph into another set. What a far
        layer hides behind the horizon is folded onto the ground line."""
        cam = cam or self.ref
        out = []
        for sk_, d, mist in self.layers:
            if d >= 0.999:
                out.append(sk_)
                continue
            cd, k = cam.depth(d), cam.zoom ** (d - 1.0)
            pl = sk_.place(cam.cx - cd.cx * k, cam.cy - cd.cy * k, k)
            if mist is not None:
                for it in pl.items:
                    it.P[:, 1] = np.minimum(it.P[:, 1], FLOOR)
            out.append(pl)
        return Sketch(out)


class TowerLayout:
    """Where the three groups stand in the wide frame. World units; the subject's plane.

    cam: the wide camera. child: the child's ground point. target: where the tails aim (its head).
    friend, friend_h: the ground point and world height of the far friend (60 px tall on screen, at 88 percent of the width).
    backs, voices, house: the members of the three groups (see tower_layout). level: 1 or 2.
    free: the world rectangle (l, t, r, b) of the lyric band in the wide frame (ground only).
    lid_y: the world y where the underside of the scribble's ceiling should hang (screen y 235 in
    the wide frame, where gloom's lid_numbers puts it) so that the heads of the nearest backs are
    lost in it."""
    __slots__ = ("level", "zoom", "cam", "child", "target", "friend", "friend_h", "backs", "voices", "house", "free", "lid_y")

    def key(self):
        return (self.level, self.zoom, self.child[0], float(self.target[0]), float(self.target[1]))


# the wide frame, in screen px of the 1920x1080 picture at the wide zoom with the child at (685, 748):
# backs: name, x, height, depth, kit, detail, lean, tilt, seed, build (girth, hem, stance, flare)
_BACKS = {1: (("back0", -10, 668, 1.00, "belt", 2, 0.012, 0.5, 700, (1.00, 0.335, 0.7, 0.0)),        # tall, a long coat
              ("back1", 228, 598, 0.86, "satchel", 2, -0.010, -0.6, 720, (1.13, 0.425, -0.6, 0.0)),  # broad, a short jacket
              ("back2", 450, 505, 0.70, "scarf", 1, 0.008, 0.4, 740, (0.90, 0.36, 0.5, 0.14)),       # slight, a flared coat
              ("back3", 115, 418, 0.52, "plain", 1, 0.0, -0.3, 760, (1.06, 0.40, -0.4, 0.0)),
              ("back4", 345, 340, 0.42, "satchel", 0, 0.0, 0.2, 780, (0.92, 0.35, 0.3, 0.08))),
          2: (("back0", 0, 960, 1.00, "belt", 2, 0.012, 0.5, 700, (1.00, 0.335, 0.7, 0.0)),
              ("back1", 262, 652, 0.88, "satchel", 2, -0.010, -0.6, 720, (1.13, 0.425, -0.6, 0.0)),
              ("back5", 525, 690, 0.95, "plain", 2, -0.016, 0.7, 800, (0.97, 0.31, -0.8, 0.10)),     # right over the child
              ("back2", 398, 556, 0.72, "scarf", 1, 0.008, 0.4, 740, (0.90, 0.36, 0.5, 0.14)),
              ("back3", 135, 470, 0.55, "plain", 0, 0.0, -0.3, 760, (1.06, 0.40, -0.4, 0.0)))}     # (the far fifth of level 1 would be hidden here)
# voices: name, cx, cy, rx, ry, depth, style, cross, rows, seed
_VOICES = {1: (("voice0", 850, 462, 232, 122, 1.00, "round", "strike", 5, 830),
               ("voice1", 560, 400, 172, 94, 0.84, "spiky", "x", 4, 810),
               ("voice2", 1800, 420, 170, 96, 0.70, "box", "scribble", 4, 850),
               ("voice3", 712, 318, 112, 62, 0.56, "round", "slash", 3, 870)),
           2: (("voice0", 809, 458, 250, 142, 1.00, "round", "strike", 5, 830),
               ("voice1", 515, 392, 205, 112, 0.88, "spiky", "x", 4, 810),
               ("voice2", 1800, 420, 196, 110, 0.74, "box", "scribble", 4, 850),
               ("voice3", 700, 310, 136, 74, 0.60, "round", "slash", 3, 870),
               ("voice4", 880, 632, 106, 58, 1.00, "spiky", "scribble", 3, 890))}
# house: x, width, split, depth
_HOUSE = {1: (1205, 336, 0.085, 1.0), 2: (1201, 372, 0.12, 1.0)}
_FRIEND_DX = FRIEND_FAR_1 - X2           # the far friend stands this many world units right of the child (hx.story: 4900)
_FRIEND_PX = 0.88 * W                    # ... which the wide camera shows at 88 percent of the width
_CHILD_PX = (_FRIEND_PX - _FRIEND_DX * WIDE_ZOOM, 748.0)        # (685, 748)
_LID_PX = 235.0                          # the underside of the scribble's ceiling (gloom's lid_numbers hangs it there)


def tower_layout(child_x: float = X2, level: int = 1, zoom: float | None = None) -> TowerLayout:
    """The composition of the wide chorus frame for a child standing at world x = child_x.

    zoom: the wide zoom (default hx.story.WIDE_ZOOM, 0.205). The wide camera shows the child at screen
    (685, 748), 78 px tall, the far friend at 88 percent of the width (screen x 1690, 60 px tall; at
    the default zoom 4900 world units right of the child: story.FRIEND_FAR_1 for child_x = story.X2),
    the ground line at y 748 and nothing but ground below y 864 (the lyric band). The backs fill the
    left quarter (the nearest cropped by the frame), the voices hang over the child with their tails
    aimed at its head, the house stands between the child and the friend.
    level 1: the first chorus. level 2: the second (bigger, nearer, more of them)."""
    L = TowerLayout()
    zoom = WIDE_ZOOM if zoom is None else float(zoom)
    k = 1.0 / zoom
    L.level, L.zoom = int(level), zoom
    L.cam = Cam.at(child_x, FLOOR, zoom, *_CHILD_PX)
    L.child = (float(child_x), FLOOR)
    L.target = (float(child_x) + 8.0, FLOOR - 0.86 * CHILD_H)
    L.friend = (child_x + (_FRIEND_DX if zoom == WIDE_ZOOM else _FRIEND_DX * WIDE_ZOOM * k), FLOOR)
    L.friend_h = 60.0 * k

    def X(px):
        return child_x + (px - _CHILD_PX[0]) * k

    def Y(py):
        return FLOOR + (py - _CHILD_PX[1]) * k

    L.backs = tuple(dict(name=n, x=X(x), y=FLOOR, h=h * k, depth=d, kit=kit, detail=det, lean=ln, tilt=tl, seed=sd, build=bd)
                    for n, x, h, d, kit, det, ln, tl, sd, bd in _BACKS[L.level])
    L.voices = tuple(dict(name=n, x=X(x), y=Y(y), rx=rx * k, ry=ry * k, depth=d, style=st, cross=cr, rows=rw, seed=sd)
                     for n, x, y, rx, ry, d, st, cr, rw, sd in _VOICES[L.level])
    hx_, hw_, sp, hd = _HOUSE[L.level]
    L.house = dict(x=X(hx_), y=FLOOR, w=hw_ * k, split=sp, depth=hd)
    L.free = (X(0.0), Y(864.0), X(1920.0), Y(1080.0))
    L.lid_y = Y(_LID_PX)
    return L


def _chalk_of(depth: float, press: float):
    """Tone by distance: (line colour, fill colour, pressure, line width in px of the wide frame)."""
    t = min(1.0, max(0.0, (depth - 0.4) / 0.6))
    col = mix(C.CHALK_FAR, C.CHALK_DIM, 0.10 + 0.85 * t)
    if press > 1.0:
        col = mix(col, C.CHALK_COOL, min(0.6, 1.5 * (press - 1.0)))
    fillc = mix((0.19, 0.235, 0.375), C.PAPER_HAZE, 0.55 * (1.0 - t))
    return col, fillc, min(1.0, (0.60 + 0.38 * t) * press), (3.0 + 2.2 * t) * press ** 0.8


@lru_cache(maxsize=16)
def _backs(key, press, depth):
    L = tower_layout(key[2], key[0], key[1])
    L.target = (key[3], key[4])
    k = 1.0 / L.zoom
    layers, anchors = [], {}
    for m in sorted(L.backs, key=lambda m: m["depth"]):
        d = min(1.0, m["depth"] * depth)
        col, fillc, a, lwp = _chalk_of(d, press)
        far = d < 0.95
        gi, he, sta, fla = m["build"]
        sk = back_figure(m["x"], m["y"], m["h"], m["seed"], col, a, lwp * k, fillc, m["lean"], m["tilt"], m["name"], m["kit"],
                         m["detail"], sink=0.3 if far else 0.0, loom=0.5, girth=gi, hem=he, stance=sta, flare=fla)
        layers.append([_to_layer(sk, L.cam, d), d, (0.9 * (1.0 - d) / 0.6 + 0.25) if far else None])
        anchors[m["name"]] = dict(x=m["x"], y=m["y"], h=m["h"], depth=d, head=(m["x"] + m["lean"] * m["h"] * 0.91, m["y"] - 0.912 * m["h"]))
    return TowerGroup(layers, [m["name"] for m in sorted(L.backs, key=lambda m: -m["depth"])], L.cam, anchors, "backs")


def tower_backs(L: TowerLayout, press: float | None = None, depth: float = 1.0) -> TowerGroup:
    """School: the enormous turned backs of L (tower_layout), far to near, the far ones dimmer and
    thinner, standing behind the horizon in its mist. press: how hard they are drawn (1 the first
    chorus, 1.25 the second: wider, brighter; default by L.level). depth: scales every member's
    camera depth (under 1: the whole group further away). anchors[name] = x, y, h, depth, head."""
    return _backs(L.key(), (1.0 if L.level == 1 else 1.25) if press is None else float(press), float(depth)).copy()


@lru_cache(maxsize=16)
def _voices(key, press, depth):
    L = tower_layout(key[2], key[0], key[1])
    L.target = (key[3], key[4])
    k = 1.0 / L.zoom
    layers, anchors = [], {}
    for m in sorted(L.voices, key=lambda m: m["depth"]):
        d = min(1.0, m["depth"] * depth)
        col, fillc, a, lwp = _chalk_of(d, press)
        sk = voice(m["x"], m["y"], m["rx"], m["ry"], L.target, m["seed"], col, a, lwp * 0.9 * k, m["rows"], m["name"], m["style"],
                   m["cross"], mix(fillc, C.PAPER_DEEP, 0.12))
        layers.append([_to_layer(sk, L.cam, d), d, None])
        anchors[m["name"]] = dict(x=m["x"], y=m["y"], rx=m["rx"], ry=m["ry"], depth=d)
    return TowerGroup(layers, [m["name"] for m in sorted(L.voices, key=lambda m: -m["depth"])], L.cam, anchors, "voices")


def tower_voices(L: TowerLayout, press: float | None = None, depth: float = 1.0) -> TowerGroup:
    """The voices: speech balloons as big as houses, full of crossed-out scribble, overlapping, their
    tails aimed at L.target (an argument over the child's head). anchors[name] = x, y, rx, ry, depth."""
    return _voices(L.key(), (1.0 if L.level == 1 else 1.25) if press is None else float(press), float(depth)).copy()


@lru_cache(maxsize=16)
def _home(key, press, depth, split):
    L = tower_layout(key[2], key[0], key[1])
    L.target = (key[3], key[4])
    k = 1.0 / L.zoom
    m = L.house
    d = min(1.0, m["depth"] * depth)
    col, fillc, a, lwp = _chalk_of(d, press)
    sp = m["split"] if split is None else split
    sk = house(m["x"], m["y"], m["w"], 600, col, sp, a, lwp * k, fill=fillc, roof=mix(fillc, C.PAPER_DEEP, 0.5))
    anchors = house_seam(m["x"], m["y"], m["w"], split=sp)
    anchors.update(x=m["x"], y=m["y"], w=m["w"], h=1.5 * m["w"], split=sp, depth=d)
    return TowerGroup([[_to_layer(sk, L.cam, d), d, None]], ["house.l", "house.r"], L.cam, anchors, "house")


def tower_house(L: TowerLayout, press: float | None = None, depth: float = 1.0, split: float | None = None) -> TowerGroup:
    """Home: the child's drawing of a house, as tall as the backs, split down the middle, the halves
    leaning apart (split: their lean in radians, default from L). anchors: x, y, w, h, split and the
    seam (see house_seam)."""
    return _home(L.key(), (1.0 if L.level == 1 else 1.25) if press is None else float(press), float(depth),
                 None if split is None else float(split)).copy()


class Towers:
    """The three groups of one chorus: T.voices, T.backs, T.house (TowerGroup), T.layout.
    T.hit(times) gives them their hits; T.draw(F) paints them in depth order."""
    ORDER = ("voices", "backs", "house")

    def __init__(self, L: TowerLayout, press=None):
        self.layout = L
        self.voices, self.backs, self.house = tower_voices(L, press), tower_backs(L, press), tower_house(L, press)

    def hit(self, times, order=ORDER, dur: float = 0.45, lead: float = 0.066) -> "Towers":
        """times: the three hits; order: which group lands on which."""
        for t, nm in zip(times, order):
            getattr(self, nm).hit(t, dur, lead)
        return self

    def off(self, t0: float, dur: float = 1.6) -> float:
        return max(g.off(t0 + 0.15 * i * dur, dur * 0.7) for i, g in enumerate((self.voices, self.backs, self.house)))

    def draw(self, F: Frame, a=1.0, thin=1.0, tint=None, tint_w: float = 0.0, dark: float = 1.0) -> None:
        """Paint the house, the backs, then the voices over them, and let their tops sink into the dark
        above (dark: strength of dark_above). a, thin: a number, or a dict by group name."""
        for band in ((0.0, 0.78), (0.78, 9.0)):
            for nm in ("house", "backs", "voices"):
                g = getattr(self, nm)
                g.draw(F, None, a.get(nm, 1.0) if isinstance(a, dict) else a, thin.get(nm, 1.0) if isinstance(thin, dict) else thin,
                       tint, tint_w, band)
        if dark > 0.0:
            dark_above(F, dark)


def towers(L: TowerLayout, press: float | None = None) -> Towers:
    """The three groups of the layout L, ready for T.hit((64.77, 66.27, 67.77)) and T.draw(F)."""
    return Towers(L, press)


def dark_above(F: Frame, a: float = 1.0, reach: float = 500.0) -> None:
    """The dark the towering things rise into: the top of the frame darkened, fading out `reach`
    px down the screen. Draw it after the groups and before the scribble's ceiling."""
    if a > 0.003:
        cols = [sk(C.PAPER_DEEP, 0.85 * a), sk(C.PAPER_DEEP, 0.62 * a), sk(C.PAPER_DEEP, 0.28 * a), sk(C.PAPER_DEEP, 0.0)]
        p = skia.Paint(Shader=skia.GradientShader.MakeLinear([(0.0, 0.0), (0.0, float(reach))], cols, [0.0, 0.33, 0.67, 1.0]))
        F.c.drawRect(skia.Rect.MakeLTRB(0.0, 0.0, float(W), float(reach)), p)


# ==========================================================================================
# the same three, knee-high (the last chorus)
# ==========================================================================================
def _small_cols(day: bool):
    """(line, tone, rub-out) of the pale knee-high things: night chalk, or faded pencil and a breath
    of pastel on the warm paper."""
    if day:
        return mix(C.PENCIL, C.DAY_SHADE, 0.30), mix(C.DAY_SHADE, C.LILAC, 0.40), C.DAY
    return mix(C.CHALK_DIM, C.CHALK_COOL, 0.22), (0.18, 0.22, 0.35), C.KNOCK


def _ground_y(y, x):
    return float(y(np.array([x]))[0]) if callable(y) else float(y)


def small_backs(xs, y=FLOOR, h: float = 150.0, seed: int = 760, a: float = 0.8, day: bool = False, name: str = "sback") -> TowerGroup:
    """The turned backs again, pale and only knee-high: one at every world x of xs, standing on y
    (a number, or the hill contour as a function of an array of x). h: their height (each a little
    different). anchors[name + index] = x, y, h, head: where a small person can stand when it turns round."""
    col, tone, kn = _small_cols(day)
    kits = ("satchel", "plain", "scarf", "belt")
    items, anchors, members = [], {}, []
    for i, x in enumerate(xs):
        yy = _ground_y(y, x)
        hh = h * (0.86 + 0.28 * rnd(seed + i * 13, 1))
        nm = f"{name}{i}"
        items.append(back_figure(x, yy, hh, seed + i * 20, col, a, 3.0, tone, 0.02 * rsym(seed + i, 2), rsym(seed + i, 3), nm,
                                 kits[(i + seed) % 4], 1, knock=kn, girth=0.90 + 0.24 * rnd(seed + i * 13, 4),
                                 hem=0.33 + 0.09 * rnd(seed + i * 13, 5), stance=0.8 * rsym(seed + i * 13, 6),
                                 flare=0.14 * rnd(seed + i * 13, 7) ** 2))
        anchors[nm] = dict(x=float(x), y=yy, h=hh, head=(float(x), yy - 0.914 * hh))
        members.append(nm)
    return TowerGroup([[Sketch(items), 1.0, None]], members, None, anchors, "small_backs")


def small_voices(centres, target, rx: float = 88.0, ry: float = 52.0, seed: int = 860, a: float = 0.8, full: float = 1.0,
                 day: bool = False, name: str = "svoice") -> TowerGroup:
    """The voices again, pale and knee-high: one balloon at every world point of `centres`, its tail
    toward the world point `target`. full: 1 the crossed-out scribble is in them, 0 they are empty
    (or take the scribble back in time: G.sub("svoice0.row", "svoice0.cross").set_off(t0, t1)).
    anchors[name + index] = x, y, rx, ry: where a bubble can take over."""
    col, tone, kn = _small_cols(day)
    styles, crosses = ("round", "spiky", "box"), ("strike", "x", "scribble")
    items, anchors, members = [], {}, []
    for i, (x, y) in enumerate(centres):
        k = 0.85 + 0.3 * rnd(seed + i * 17, 1)
        nm = f"{name}{i}"
        items.append(voice(x, y, rx * k, ry * k, target, seed + i * 30, col, a, 2.8, 3, nm, styles[i % 3], crosses[i % 3],
                           mix(C.DAY, C.CREAM, 0.5) if day else tone, full, kn))
        anchors[nm] = dict(x=float(x), y=float(y), rx=rx * k, ry=ry * k)
        members.append(nm)
    return TowerGroup([[Sketch(items), 1.0, None]], members, None, anchors, "small_voices")


def small_house(x, y=FLOOR, h: float = 150.0, split: float = 0.10, seed: int = 600, a: float = 0.8, day: bool = False,
                name: str = "shouse") -> TowerGroup:
    """The split house again, pale and knee-high (h to the ridge), standing on (x, y). split: the lean
    of its halves in radians: animate it to 0 as the two push them together (the tear stays).
    anchors: x, y, w, h, split and the seam of house_seam: "wall" and "roof" are where the strips of
    tape go, anchors["gap"] how wide the gape still is there."""
    col, tone, kn = _small_cols(day)
    w = h / 1.5
    yy = _ground_y(y, x)
    wall_c, roof_c = (mix(C.DAY_SHADE, C.CREAM, 0.35), mix(C.DAY_SHADE, C.CORAL, 0.40)) if day else (tone, mix(tone, kn, 0.45))
    sk = house(x, yy, w, seed, col, split, a, 2.9, fill=wall_c, roof=roof_c, name=name, detail=1, knock=kn)
    anchors = house_seam(x, yy, w, split=split)
    anchors.update(x=float(x), y=yy, w=w, h=h, split=split)
    return TowerGroup([[sk, 1.0, None]], [name + ".l", name + ".r"], None, anchors, "small_house")


# ==========================================================================================
# the plain
# ==========================================================================================
_G = 0.40                         # furrows: the step of the tangent from one furrow to the next
_SP = (5.0, 14.0)                 # px between neighbours: under the first a furrow is not drawn, over the second fully
_GROUND = (0.19, 0.24, 0.39)
_HAZE = (0.30, 0.37, 0.56)
_HAZE_HI = (0.42, 0.50, 0.70)
_FAR_D = 0.30                     # camera depth of the far low shapes on the horizon
_LOGR = math.log(1.5)             # the scatter lives in bands of depth, each 1.5 times the last


class _Batch:
    """Many small strokes in a few paths: screen polylines bucketed by width and pressure."""

    def __init__(self, floor: float = 1.15):
        self.paths, self.floor = {}, floor

    def add(self, S, w, al, close: bool = False) -> None:
        """S: (m, n, 2) screen points; w: (m,) widths in px; al: (m,) alphas 0..1."""
        w, al = np.asarray(w, dtype=np.float64), np.asarray(al, dtype=np.float64)
        al = np.where(w < self.floor, al * w / self.floor, al)
        wq = np.round(np.log(np.maximum(w, self.floor)) * 6.0).astype(int)
        aq = np.minimum(9, (np.clip(al, 0.0, 1.0) * 10.0).astype(int))
        paths = self.paths
        for kw, ka, pts in zip(wq.tolist(), aq.tolist(), np.asarray(S).tolist()):
            if ka <= 0:
                continue
            p = paths.get((kw, ka))
            if p is None:
                p = paths[(kw, ka)] = skia.Path()
            p.moveTo(*pts[0])
            for q in pts[1:]:
                p.lineTo(*q)
            if close:
                p.close()

    def flush(self, F: Frame, col, a: float = 1.0, grain: str = "mid") -> None:
        for (kw, ka), p in self.paths.items():
            F.c.drawPath(p, F.pen(col, math.exp(kw / 6.0), a * (ka + 0.5) / 10.0, grain))
        self.paths = {}


def _h(i, j, mul: int, add: int):
    """Hash 0..1 of the integer cell (i, j)."""
    return TAB[(np.asarray(i) * mul + int(j) * 1013 + int(add)) & 8191]


def _reach(x, reach):
    """Pressure 0..1 of things at world x. reach = (x0, radius, end): the plain is still spreading
    from x0 (radius None: it is all there) and stops at world x = end (None: it has no end)."""
    x = np.asarray(x, dtype=np.float64)
    out = np.ones_like(x)
    if reach is None:
        return out
    if reach[1] is not None:
        out = smooth((reach[1] - np.abs(x - reach[0])) / (0.18 * reach[1] + 40.0))
    if reach[2] is not None:
        out = out * smooth((reach[2] - x) / 260.0)
    return out


def _furrows(F: Frame, vx: float, a: float, seed: int, reach) -> None:
    """Furrows: parallel lines on the ground running to the vanishing point (vx, FLOOR), each broken
    into strokes whose places are spaced evenly in the logarithm of the depth."""
    cam = F.cam
    z = cam.zoom
    l, _t, r, b = cam.view(24.0)
    db = b - FLOOR
    if db <= 1.0:
        return
    Xl, Xr = l - vx, r - vx
    kmax = int(math.sqrt(max(abs(Xl), abs(Xr), 1.0) * _G * z / _SP[0]) / _G) + 2
    k = np.arange(-kmax, kmax + 1)
    m = (k + 0.30 * (2 * _h(k, 0, 37, seed * 17) - 1)) * _G
    ms = np.where(np.abs(m) < 1e-6, 1e-6, m)
    da, dc = Xl / ms, Xr / ms
    qn = np.sqrt(1.0 + m * m)
    d_lo = np.maximum(np.maximum(np.minimum(da, dc), 0.0), _SP[0] * qn / (_G * z))
    d_hi = np.minimum(np.maximum(da, dc), db)
    ok = (_h(k, 1, 41, seed * 19) > 0.10) & (d_hi > d_lo * 1.02)
    if not ok.any():
        return
    k, m, qn, d_lo, d_hi = k[ok], m[ok], qn[ok], d_lo[ok], d_hi[ok]
    lam = 0.36
    ph = _h(k, 2, 43, seed * 23) * lam
    n0 = np.floor((np.log(d_lo) - ph) / lam).astype(int)
    cnt = np.floor((np.log(d_hi) - ph) / lam).astype(int) - n0 + 1
    ki = np.repeat(np.arange(len(k)), cnt)
    n = n0[ki] + (np.arange(len(ki)) - np.repeat(np.cumsum(cnt) - cnt, cnt))
    kk = k[ki]
    key = kk * 193 + n * 71
    keep = _h(key, 3, 1, seed * 29) > 0.30
    ki, n, kk, key = ki[keep], n[keep], kk[keep], key[keep]
    if not len(ki):
        return
    ua = ph[ki] + n * lam + lam * 0.3 * _h(key, 4, 1, seed * 31)
    ub = ua + lam * (0.35 + 0.75 * _h(key, 5, 1, seed * 37))
    u = ua[:, None] + (ub - ua)[:, None] * np.linspace(0.0, 1.0, 7)[None, :]
    d = np.exp(u)
    mm, qq = m[ki][:, None], qn[ki][:, None]
    # each stroke lies a little off its furrow and bends a little: hatching by hand, not a ruled fan
    off = 0.30 * (2 * _h(key, 8, 1, seed * 47) - 1)[:, None] + 0.16 * (2 * vn(u * 2.6 + kk[:, None] * 7.31, seed) - 1)
    wob = off * _G * d / qq
    wx = vx + mm * d + wob / qq
    wy = FLOOR + d - wob * mm / qq
    dm = d[:, 3]
    lod = smooth((_G * dm * z / qq[:, 0] - _SP[0]) / (_SP[1] - _SP[0]))
    al = lod * (0.35 + 0.65 * _h(key, 6, 1, seed * 41)) * _reach(wx[:, 3], reach)
    wpx = 0.0125 * dm * z * (0.6 + 0.8 * _h(key, 7, 1, seed * 43))
    S = np.stack([(wx - cam.cx) * z + CX, (wy - cam.cy) * z + CY], axis=2)
    B = _Batch()
    B.add(S, wpx * 2.1, al * 0.5)
    B.flush(F, C.CHALK_FAR, 0.50 * a, "sparse")
    B.add(S[:, 1:6], wpx, al)
    B.flush(F, mix(C.CHALK_FAR, C.CHALK_DIM, 0.35), 0.60 * a, "mid")


def _bands(cam: Cam, px_min: float, margin: float = 60.0):
    """The depth bands on screen (index j, depth d_j = 6 * 1.5 ** j) from px_min below the horizon down."""
    z = cam.zoom
    _l, _t, _r, b = cam.view(margin)
    db = b - FLOOR
    if db <= 6.0:
        return range(0)
    j0 = int(math.ceil(math.log(max(px_min / z, 6.0) / 6.0) / _LOGR)) - 1
    return range(j0, int(math.floor(math.log(db / 6.0) / _LOGR)) + 1)


def puddles(F: Frame, seed: int = 31):
    """The puddles of plain(F, seed=seed) on screen: arrays (x, y, rx, ry, a) in world units, a = how
    visible each is (0..1; the far ones are too small to draw). For a light of your own in them."""
    cam = F.cam
    z = cam.zoom
    l, _t, r, _b = cam.view(260.0)
    out = []
    for j in _bands(cam, 34.0, 120.0):
        dj = 6.0 * 1.5 ** j
        cw = 3.6 * dj
        i = np.arange(int(math.floor(l / cw)), int(math.floor(r / cw)) + 1)
        on = _h(i, j, 61, seed * 211) < 0.40
        i = i[on]
        if not len(i):
            continue
        rx = dj * (0.34 + 0.50 * _h(i, j, 67, seed * 223))
        x = (i + 0.28 + 0.44 * _h(i, j, 71, seed * 227)) * cw
        d = dj * 1.5 ** _h(i, j, 73, seed * 229)
        ry = rx * 0.150 * (0.8 + 0.5 * _h(i, j, 79, seed * 233))
        out.append(np.stack([x, FLOOR + d, rx, ry, smooth((rx * z - 8.0) / 14.0), i * 31.0 + j * 7.0], axis=1))
    if not out:
        return np.zeros((0, 6))
    P = np.vstack(out)
    return P[P[:, 4] > 0.02]


_RING = np.linspace(0.0, 2 * math.pi, 19)


def _scatter(F: Frame, a: float, wet: float, rain: float, seed: int, reach) -> None:
    """Puddles, stones and tufts, scattered in bands of depth and sized by their depth."""
    cam = F.cam
    z = cam.zoom
    l, _t, r, _b = cam.view(60.0)
    c = F.c
    # ---- puddles: a dark wet patch, a pale reflection in its far half, a rim, a glint, rings of rain
    if wet > 0.003:
        P = puddles(F, seed)
        if len(P):
            x, y, rx, ry, al, hk = P.T
            al = al * _reach(x, reach)
            hk = hk.astype(np.int64)
            rr = 1.0 + 0.13 * (2 * vn(_RING[None, :] * 0.9 + hk[:, None] * 0.37, seed + 5) - 1)
            rr[:, -1] = rr[:, 0]
            ox, oy = rx[:, None] * rr * np.cos(_RING)[None, :], ry[:, None] * rr * np.sin(_RING)[None, :]
            sx, sy = (x[:, None] + ox - cam.cx) * z + CX, (y[:, None] + oy - cam.cy) * z + CY
            rx_, ry_ = (x[:, None] + ox * 0.80 - cam.cx) * z + CX, (y[:, None] - 0.20 * ry[:, None] + oy * 0.62 - cam.cy) * z + CY
            dark, pale = {}, {}
            for q, X_, Y_, X2, Y2 in zip(np.minimum(4, (al * 5.0).astype(int)).tolist(), sx.tolist(), sy.tolist(), rx_.tolist(), ry_.tolist()):
                for store, xs_, ys_ in ((dark, X_, Y_), (pale, X2, Y2)):
                    p = store.get(q)
                    if p is None:
                        p = store[q] = skia.Path()
                    p.moveTo(xs_[0], ys_[0])
                    for u_, v_ in zip(xs_[1:], ys_[1:]):
                        p.lineTo(u_, v_)
                    p.close()
            for q, p in dark.items():
                c.drawPath(p, F.paint(C.PAPER_DEEP, 0.62 * wet * a * (q + 0.5) / 5.0, None))
            for q, p in pale.items():
                c.drawPath(p, F.paint((0.34, 0.42, 0.63), 0.42 * wet * a * (q + 0.5) / 5.0, "soft~"))
            B = _Batch()
            S = np.stack([sx, sy], axis=2)
            wpx = np.maximum(1.3, 0.016 * rx * z)
            B.add(S[:, 9:19], wpx, al * 0.75)                               # the far edge catches the light
            B.add(S[:, 1:8], wpx * 0.8, al * 0.30)
            gx = x + rx * (0.5 * _h(hk, 0, 83, seed) - 0.45)                 # a glint lying in it
            gl = rx * (0.22 + 0.25 * _h(hk, 0, 89, seed))
            gy = y + ry * 0.30
            G = np.stack([np.stack([(gx - cam.cx) * z + CX, (gy - cam.cy) * z + CY], axis=1),
                          np.stack([(gx + gl - cam.cx) * z + CX, (gy + 0.03 * ry - cam.cy) * z + CY], axis=1)], axis=1)
            B.add(G, wpx * 0.9, al * 0.55)
            B.flush(F, C.CHALK_DIM, wet * a, "mid")
            if rain > 0.003:
                big = rx * z > 24.0
                if big.any():
                    xb, yb, rxb, ryb, hb, ab = x[big], y[big], rx[big], ry[big], hk[big], al[big]
                    for ring_ in range(2):
                        ph = F.tb * (0.9 + 0.5 * _h(hb, ring_, 97, seed)) + _h(hb, ring_, 101, seed) * 7.0
                        cyc, p_ = np.floor(ph).astype(np.int64), ph - np.floor(ph)
                        cx_ = xb + rxb * 0.62 * (2 * _h(hb * 7 + cyc * 13, ring_, 103, seed) - 1)
                        cy_ = yb + ryb * 0.5 * (2 * _h(hb * 11 + cyc * 17, ring_, 107, seed) - 1)
                        rad = rxb * (0.05 + 0.24 * p_)
                        ex = (cx_[:, None] + rad[:, None] * np.cos(_RING)[None, ::2] - cam.cx) * z + CX
                        ey = (cy_[:, None] + rad[:, None] * (ryb / rxb)[:, None] * np.sin(_RING)[None, ::2] - cam.cy) * z + CY
                        B.add(np.stack([ex, ey], axis=2), np.full(len(xb), 1.4), ab * (1.0 - p_) ** 1.4 * 0.8)
                    B.flush(F, C.CHALK_COOL, rain * wet * a * 0.8, "mid")
    # ---- stones and tufts
    B, B2 = _Batch(), _Batch()
    for j in _bands(cam, 24.0):
        dj = 6.0 * 1.5 ** j
        cw = 1.30 * dj
        i = np.arange(int(math.floor(l / cw)), int(math.floor(r / cw)) + 1)
        hh = _h(i, j, 109, seed * 131)
        x = (i + 0.15 + 0.7 * _h(i, j, 113, seed * 137)) * cw
        d = dj * 1.5 ** _h(i, j, 127, seed * 139)
        rc = _reach(x, reach)
        tf = hh < 0.34
        if tf.any():
            xt, dt, it = x[tf], d[tf], i[tf]
            hg = 0.115 * dt * (0.6 + 0.8 * _h(it, j, 131, seed * 149))
            q = np.arange(4)[None, :] - 1.5 + 0.5 * (2 * _h(it[:, None] * 5 + np.arange(4)[None, :], j, 137, seed * 151) - 1)
            bx = xt[:, None] + q * 0.014 * dt[:, None]
            tx = xt[:, None] + q * 0.050 * dt[:, None] * (0.6 + 0.8 * _h(it, j, 139, seed * 157))[:, None] + 0.25 * hg[:, None]
            ty = (FLOOR + dt - hg)[:, None] + np.abs(q) * 0.22 * hg[:, None]
            by = np.broadcast_to((FLOOR + dt)[:, None], bx.shape)
            mx, my = 0.5 * (bx + tx) - 0.06 * hg[:, None] * np.sign(q), 0.5 * (by + ty) - 0.05 * hg[:, None]
            S = np.stack([np.stack([bx, by], axis=2), np.stack([mx, my], axis=2), np.stack([tx, ty], axis=2)], axis=2).reshape(-1, 3, 2)
            S = (S - (cam.cx, cam.cy)) * z + (CX, CY)
            al = np.repeat(smooth((hg * z - 3.5) / 5.0) * rc[tf] * (0.6 + 0.4 * _h(it, j, 149, seed * 163)), 4)
            B.add(S, np.repeat(0.0105 * dt * z, 4), al)
        stn = (hh > 0.34) & (hh < 0.44)
        if stn.any():
            xs_, ds_, is_ = x[stn], d[stn], i[stn]
            sr = 0.030 * ds_ * (0.6 + 0.9 * _h(is_, j, 151, seed * 167))
            an = _RING[::2]
            ox = sr[:, None] * np.cos(an)[None, :] * (1.0 + 0.2 * (2 * vn(an[None, :] + is_[:, None] * 1.7, seed + 9) - 1))
            oy = sr[:, None] * 0.55 * np.sin(an)[None, :]
            S = np.stack([(xs_[:, None] + ox - cam.cx) * z + CX, (FLOOR + ds_[:, None] - sr[:, None] * 0.5 + oy - cam.cy) * z + CY], axis=2)
            al = smooth((sr * z - 2.2) / 3.0) * rc[stn]
            B2.add(S, np.maximum(1.2, 0.008 * ds_ * z), al * 0.8)
            sh = np.stack([np.stack([(xs_ - sr * 0.9 - cam.cx) * z + CX, (FLOOR + ds_ + sr * 0.12 - cam.cy) * z + CY], axis=1),
                           np.stack([(xs_ + sr * 1.3 - cam.cx) * z + CX, (FLOOR + ds_ + sr * 0.16 - cam.cy) * z + CY], axis=1)], axis=1)
            B2.add(sh, np.maximum(1.2, 0.012 * ds_ * z), al * 0.45)
    B2.flush(F, C.CHALK_FAR, 0.9 * a, "mid")
    B.flush(F, mix(C.CHALK_FAR, C.CHALK_DIM, 0.5), 0.85 * a, "mid")


def _far_shapes(F: Frame, cam: Cam, sy: float, a: float, seed: int, reach) -> None:
    """A few low things far away on the horizon, in a layer of camera depth 0.3: a line of poles and
    their wire going off, a broken fence, the roofs of a place left behind. Dim; half lost in the mist.
    cam: the scene's camera (F itself is in screen space here)."""
    zf = cam.zoom ** _FAR_D
    fx = CX + (cam.cx - CX) * _FAR_D
    cw = 900.0
    i0, i1 = int(math.floor((fx - (CX + 300.0) / zf) / cw)), int(math.floor((fx + (CX + 300.0) / zf) / cw))
    B = _Batch(1.0)
    roofs = skia.Path()

    def scr(X, Y):                                      # far-layer units (Y up from the horizon) -> screen
        return (np.asarray(X, dtype=np.float64) - fx) * zf + CX, sy - np.asarray(Y, dtype=np.float64) * zf

    for i in range(i0, i1 + 1):
        h0 = rnd(seed * 7 + i, 201)
        x0 = (i + 0.2 + 0.6 * rnd(seed * 7 + i, 202)) * cw
        if reach is not None:
            wxn = cam.cx + ((x0 - fx) * zf) / cam.zoom       # the world x in the subject's plane that it stands behind
            ra = float(_reach(wxn, (reach[0], reach[1], None if reach[2] is None else reach[2] - 300.0)))
            if ra <= 0.01:
                continue
        else:
            ra = 1.0
        if h0 < 0.12:                                   # poles going away: each smaller and closer than the last
            dr = 1.0 if rnd(seed * 7 + i, 203) > 0.5 else -1.0
            n = 5 + int(rnd(seed * 7 + i, 204) * 3)
            hs = 66.0 * 0.76 ** np.arange(n)
            xs = x0 + dr * np.concatenate([[0.0], np.cumsum(112.0 * 0.76 ** np.arange(n - 1))])
            lean = 0.04 * (2 * htab(np.arange(n), 7, i * 13 + seed) - 1)
            px0, py0 = scr(xs, 0.0)
            px1, py1 = scr(xs + lean * hs, hs)
            B.add(np.stack([np.stack([px0, py0 + 0 * px0], axis=1), np.stack([px1, py1], axis=1)], axis=1), 3.4 * zf * hs / 66.0 + 0.6, np.full(n, 0.95 * ra))
            ax0, ay0 = scr(xs + lean * hs - 0.16 * hs, hs * 0.90)
            ax1, ay1 = scr(xs + lean * hs + 0.16 * hs, hs * 0.92)
            B.add(np.stack([np.stack([ax0, ay0], axis=1), np.stack([ax1, ay1], axis=1)], axis=1), 2.6 * zf * hs / 66.0 + 0.5, np.full(n, 0.9 * ra))
            q = np.linspace(0.0, 1.0, 7)[None, :]
            for off in (-0.16, 0.16):                   # the wires sag from pole to pole
                wx_ = (xs[:-1] + lean[:-1] * hs[:-1] + off * hs[:-1])[:, None] * (1 - q) + (xs[1:] + lean[1:] * hs[1:] + off * hs[1:])[:, None] * q
                wy_ = (hs[:-1] * 0.91)[:, None] * (1 - q) + (hs[1:] * 0.91)[:, None] * q - 0.10 * hs[:-1, None] * np.sin(math.pi * q)
                X_, Y_ = scr(wx_, wy_)
                B.add(np.stack([X_, Y_], axis=2), np.full(n - 1, 1.3), 0.7 * ra * (hs[:-1] / 66.0) ** 0.5)
        elif h0 < 0.24:                                 # a broken fence
            n = 6 + int(rnd(seed * 7 + i, 205) * 5)
            j = np.arange(n)
            there = htab(j, 11, i * 17 + seed) > 0.22
            xs = x0 + j * 30.0 + 7.0 * (2 * htab(j, 13, i * 19 + seed) - 1)
            hs = 21.0 + 10.0 * htab(j, 17, i * 23 + seed)
            lean = 0.22 * (2 * htab(j, 19, i * 29 + seed) - 1)
            px0, py0 = scr(xs, 0.0)
            px1, py1 = scr(xs + lean * hs, hs)
            S = np.stack([np.stack([px0, py0 + 0 * px0], axis=1), np.stack([px1, py1], axis=1)], axis=1)
            B.add(S[there], np.full(int(there.sum()), 2.8 * zf + 0.4), np.full(int(there.sum()), 0.9 * ra))
            rx_, ry_ = scr(xs + lean * hs * 0.7, hs * 0.68 + 1.5 * np.sin(j * 1.3))
            cut = n - 1 - int(rnd(seed * 7 + i, 206) * 3)
            B.add(np.stack([rx_[:cut], ry_[:cut]], axis=1)[None, :, :], [2.2 * zf + 0.4], [0.8 * ra])
        elif h0 < 0.32:                                 # roofs
            n = 2 + int(rnd(seed * 7 + i, 207) * 3)
            xx = x0
            for j in range(n):
                wd = 40.0 + 30.0 * rnd(seed * 7 + i * 5 + j, 208)
                ht = 18.0 + 13.0 * rnd(seed * 7 + i * 5 + j, 209)
                rf = 11.0 + 12.0 * rnd(seed * 7 + i * 5 + j, 210)
                X_, Y_ = scr([xx, xx, xx + wd * 0.5, xx + wd, xx + wd], [0.0, ht, ht + rf, ht, 0.0])
                roofs.moveTo(float(X_[0]), float(Y_[0]))
                for u_, v_ in zip(X_[1:].tolist(), Y_[1:].tolist()):
                    roofs.lineTo(u_, v_)
                roofs.close()
                B.add(np.stack([X_, Y_], axis=1)[None, :, :], [2.4 * zf + 0.4], [0.85 * ra])
                xx += wd * (0.8 + 0.5 * rnd(seed * 7 + i * 5 + j, 211))
        elif h0 < 0.38:                                 # a street lamp, unlit, and another further off
            dr = 1.0 if rnd(seed * 7 + i, 212) > 0.5 else -1.0
            for j, (dx, hs_) in enumerate(((0.0, 72.0), (140.0, 48.0))):
                q = np.linspace(0.0, 1.0, 8)
                lx = x0 + dr * dx + np.where(q < 0.72, 0.0, dr * hs_ * 0.30 * np.sin((q - 0.72) / 0.28 * math.pi / 2))
                ly = hs_ * np.where(q < 0.72, q / 0.72 * 0.92, 0.92 + 0.08 * np.sin((q - 0.72) / 0.28 * math.pi))
                X_, Y_ = scr(lx, ly)
                B.add(np.stack([X_, Y_], axis=1)[None, :, :], [3.0 * zf * hs_ / 72.0 + 0.5], [0.9 * ra])
    if not roofs.isEmpty():
        F.c.drawPath(roofs, F.paint(C.PAPER_DEEP, 0.42 * a, None))
    B.flush(F, mix(C.CHALK_FAR, C.CHALK_DIM, 0.35), 0.72 * a, "mid")


def plain(F: Frame, vx: float = X2, a: float = 1.0, haze: float = 1.0, wet: float = 1.0, far: float = 1.0,
          rain: float = 1.0, seed: int = 31, reach=None, end: float | None = None) -> None:
    """The bare, endless plain under the ground line (world y 742): rubbed ground tone, a mist band
    along the horizon, a few far low shapes in it, furrows running to the vanishing point (vx, 742),
    puddles, stones and tufts. It has no edges: it is made for whatever the camera shows, and every
    mark is fixed in the world (sized by its depth below the line, so the same kind of picture at
    zoom 1 and at the wide zoom; marks that get too small or too close lose pressure and go).

    vx: world x the furrows run to (keep it fixed for a whole scene: where the child is heading).
    a: pressure of everything (fade over 6 frames or more). haze: the mist band. wet: the puddles
    (0: a dry plain). rain: rings of rain in the puddles (they run on F.tb). far: the far low shapes.
    reach: None, or (x0, radius): only what lies within `radius` world units of world x0 is there yet
    (the plain spreading out from a point as the ground line shoots out).
    end: None, or the world x where the marks on the ground stop (the foot of the first hill); the
    tone and the mist go on.
    Draw it first; then ground_line(F), footsteps, the groups, the ceiling, the figures."""
    if a <= 0.003:
        return
    cam = F.cam
    sy = float(cam.to_screen(0.0, FLOOR)[1])
    kr = 1.0 if reach is None else ramp(reach[1] * cam.zoom, 0.0, 700.0)
    reach = None if reach is None and end is None else ((reach[0], reach[1], end) if reach is not None else (0.0, None, end))
    with F.screen():
        if sy < H + 4.0:
            wash(F, A((-4, sy), (W + 4, sy), (W + 4, H + 4), (-4, H + 4)), _GROUND, sy, sy + 420.0,
                 [0.44 * a * kr, 0.31 * a * kr, 0.21 * a * kr, 0.13 * a * kr, 0.07 * a * kr, 0.03 * a * kr, 0.0], "soft")
        if -40.0 < sy < H + 280.0:
            k = a * haze * kr
            if k > 0.003:
                wash(F, A((-4, sy - 260), (W + 4, sy - 260), (W + 4, sy + 16), (-4, sy + 16)), _HAZE, sy - 260.0, sy + 16.0,
                     [0.0, 0.015 * k, 0.045 * k, 0.09 * k, 0.16 * k, 0.26 * k, 0.38 * k, 0.48 * k, 0.32 * k], "soft")
            if far > 0.003:
                _far_shapes(F, cam, sy, a * far, seed, reach)
            if k > 0.003:
                wash(F, A((-4, sy - 44), (W + 4, sy - 44), (W + 4, sy + 30), (-4, sy + 30)), _HAZE_HI, sy - 44.0, sy + 30.0,
                     [0.0, 0.12 * k, 0.30 * k, 0.16 * k, 0.0], "soft")
    _furrows(F, vx, a, seed, reach)
    _scatter(F, a, wet, rain, seed, reach)


# ==========================================================================================
# the way already walked
# ==========================================================================================
def footfalls(x0: float, x1: float, t0: float, t1: float, every: float = 0.75):
    """The marks of a walk from world x0 (left at t0) to x1 (reached at t1), one step every `every`
    seconds: (xs, born), the world x of each mark and the time its foot lifts off it. The place
    where the walker stands at the end has no mark yet."""
    n = max(1, int(round((t1 - t0) / every)))
    i = np.arange(n)
    return x0 + (x1 - x0) * i / n, t0 + (t1 - t0) * (i + 1) / n


def footsteps(F: Frame, xs, born=None, y: float | None = None, s: float = 1.3, a: float = 0.9, life: float = 16.0,
              face: int | None = None, col=(0.50, 0.58, 0.76), rest: float = 0.25) -> None:
    """The way already walked: one mark per step just under the ground line, left and right in turn,
    the toes turned out a little. Close by a mark is a print pressed into the wet ground (a dark sole
    and heel with a pale rim, like the puddles); far away it is a pale dash, and the trail a dotted line.

    xs: world x of every step, in the order walked. born: the time each mark appeared (the same
    length; None: all of them old). A mark comes up in 0.25 s and loses pressure with its age: after
    `life` seconds it keeps only `rest` of it. y: world y of the trail (default 14 * s under the line;
    in a wide frame the default trail keeps 7 px clear of the line on screen, so that it is not
    lost in it). s: size (1 = the child's shoe, 36 units long).
    face: +1 / -1 the way the toes point (default: the way xs runs)."""
    xs = np.atleast_1d(np.asarray(xs, dtype=np.float64))
    n = len(xs)
    if n == 0 or a <= 0.003:
        return
    cam = F.cam
    z = cam.zoom
    lift = max(0.0, 7.0 - 14.0 * s * z) if y is None else 0.0
    y = FLOOR + 14.0 * s if y is None else y
    if face is None:
        face = 1 if n < 2 or xs[-1] >= xs[0] else -1
    if born is None:
        al = np.full(n, rest)
    else:
        age = F.t - np.asarray(born, dtype=np.float64)
        al = smooth(age / 0.25) * (rest + (1.0 - rest) * np.exp(-np.maximum(age, 0.0) / (0.45 * life)))
    i = np.arange(n)
    side = (i % 2) * 2 - 1
    ys = y + 4.5 * s * side + 1.5 * s * (2 * htab(i, 7, 55) - 1)
    lz = 17.0 * s * z
    ln, wd = max(lz, 3.2), max(4.4 * s * z, 1.25)        # on screen: never smaller than a dash of 6 by 2.5 px
    big = float(smooth((lz - 7.0) / 7.0))                # 0 a dash in a dotted trail .. 1 a print
    al = al * a * min(1.0, (lz / 2.4) ** 2)
    sx, sy_ = (xs - cam.cx) * z + CX, (ys - cam.cy) * z + CY + lift + np.maximum(0.0, 1.6 - 4.5 * s * z) * side
    vis = (al > 0.02) & (sx > -60) & (sx < W + 60) & (sy_ > -60) & (sy_ < H + 60)
    if not vis.any():
        return
    q = np.linspace(0.0, 2 * math.pi, 15)[:-1]
    cq, sq = np.cos(q), np.sin(q)
    paths = {}
    for b_, px, py, sd, k in zip(np.minimum(31, (al[vis] * 32.0).astype(int)).tolist(), sx[vis].tolist(), sy_[vis].tolist(),      # 32 steps of pressure: no mark jumps
                                 side[vis].tolist(), i[vis].tolist()):
        p = paths.get(b_)
        if p is None:
            p = paths[b_] = skia.Path()
        th = (0.16 + 0.10 * (2 * float(TAB[(k * 131 + 77) & 8191]) - 1)) * sd * big      # toes out, each a little differently
        ca, sa = math.cos(th), math.sin(th)
        for ox, rx_, ry_ in ((face * 0.275 * ln, 0.725 * ln, wd * (1.0 + 0.12 * big)), (-face * 0.80 * ln, 0.27 * ln, 0.85 * wd)):
            ex, ey = ox + rx_ * cq * (1.0 + 0.10 * big * face * cq), ry_ * sq
            p.addPoly([(px + u * ca - v * sa, py + u * sa + v * ca) for u, v in zip(ex.tolist(), ey.tolist())], True)
    grain = "mid" if lz > 9.0 else "dense"               # small marks are pressed harder: they stay a trail
    for b_, p in paths.items():
        k = (b_ + 0.5) / 32.0
        if big > 0.02:
            F.c.drawPath(p, F.paint(C.PAPER_DEEP, 0.62 * big * min(1.0, 1.6 * k), None))
            F.c.drawPath(p, F.pen(col, 1.25 + 0.035 * lz, 0.95 * big * k, "mid"))
        F.c.drawPath(p, F.paint(col, k * (1.0 - 0.78 * big), grain))


def footprints(F: Frame, x0, x1, y=None, n=12, a=0.6, col=(0.50, 0.58, 0.76), s=1.3) -> None:
    """The prototype's call, kept: n marks from world x0 to x1, fading toward the past (x0)."""
    xs = x0 + (x1 - x0) * (np.arange(n) + 0.5) / n
    footsteps(F, xs, F.t - 12.0 * (1.0 - (np.arange(n) + 0.5) / n), y, s, a, 16.0, None, col)
