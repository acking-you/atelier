"""hx.scenes._s07: the line of the bridge (s07_bridge's helper; not a scene).

The kit's unravel() ties the line that lies on the ground to the pulling hand (its coils start 26 units
beside the hand, so every move of a hand drags the whole coil along the ground), its pale twin and its
stroke differ from hill_from_line's (a step where the hill takes the line over), and strand() only draws
the strand_pts of two points. Here the same drawing with three changes:

- line_pts: the line pulled out of the lid, the part on the ground laid from a FIXED pile point (where it
  first touched the ground), so what lies there stays where it lies; the upper end can let go of the mass
  and fall (`top`, a point of its own).
- draw_line: unravel's own two chalk strokes (the pale twin, the dark line), for any polyline.
- hill_line: hills.hill_from_line's geometry for the line as it lies, point for point (no resampling:
  at w = 0 it is exactly the line drawn by draw_line), its dark line in unravel's own stroke, so that the
  hand-over at 175.0 shows no step; the contour's chalk comes up under it as in the kit.
- strand_line: gloom.strand's ribbon for any polyline (the strand that runs from the crown down to the
  hidden fist, and out of it).
"""
from __future__ import annotations

import math

import numpy as np

from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk.gloom import _cols, _stroke                # the scribble's own colours and ribbon (read only)
from hx.chalk.hills import HILL1_SPAN, ground_y, hill_rise

GROUND = 742.0


def _arc(P):
    d = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])
    return d


def coils(pile, lie, face=1, seed=41, s=1.0, ground=GROUND):
    """The part of the line lying on the ground: lazy coils from the world point `pile`, `lie` world units
    long, running toward `face` (gloom.unravel_pts' own coils, anchored at the pile instead of the hand)."""
    fx = float(pile[0])
    step = 13.0 * s
    lie = max(0.0, float(lie))
    if lie <= 1.0:
        return np.array([[fx, ground - 8.0 * s]])
    m = np.arange(0.0, lie + step, step)
    m[-1] = lie
    o = rnd(seed, 81) * 20.0
    mm = np.arange(0.0, lie + 2 * step, step)
    rate = (0.12 + 2.5 * vn(mm / (430.0 * s) + o, seed + 3) ** 1.9) / (66.0 * s)
    ph = np.interp(m, mm, np.concatenate([[0.0], np.cumsum(rate[:-1]) * step]))
    R = s * (26.0 + 92.0 * vn(m / (230.0 * s) + o, seed + 2) ** 1.3)
    hk = 0.26 + 0.42 * vn(m / (310.0 * s) + 2.0 * o, seed + 5)
    lx = fx + face * (0.44 * m + R * np.sin(ph) + 0.22 * R * np.sin(0.37 * ph + o))
    ly = ground - 8.0 * s - hk * R * (1.0 - np.cos(ph)) - 4.0 * s * vn(m / (120.0 * s), seed + 4)
    ly = np.minimum(ly, ground - 4.0 * s)
    return np.stack([lx, ly], axis=1)


def hang(p, q, n=10, sag=0.0, seed=41):
    """A short hanging curve from p (a hand) down to q (where it touches the ground)."""
    p, q = np.asarray(p, dtype=np.float64), np.asarray(q, dtype=np.float64)
    u = np.linspace(0.0, 1.0, n)
    x = p[0] + (q[0] - p[0]) * u ** 1.6 + 4.0 * np.sin(u * 5.0 + seed) * np.sin(math.pi * u)
    y = p[1] + (q[1] - p[1]) * u + sag * np.sin(math.pi * u)
    return np.stack([x, y], axis=1)


def line_pts(top, hand, lie, pile, slack=0.0, tremble=0.0, t=0.0, seed=41, face=1, tail=None):
    """The whole line, mass to free end: (line, lying). top: where it leaves the mass (or where its upper end
    is, once it has let go); hand: the hand on it (None: nobody holds it, it runs from top straight to the
    pile); lie: world units lying on the ground from the pile; tail: an extra stretch from the free upper end
    (a polyline from top toward the hand) that replaces the strand between them (the fallen upper end)."""
    G = coils(pile, lie, face, seed)
    if tail is not None:
        A_ = np.asarray(tail, dtype=np.float64)
    elif hand is not None:
        A_ = strand_pts(hand, top, slack, seed + 1, tremble, t, 24)[::-1]
    else:
        A_ = strand_pts(pile, top, slack, seed + 1, tremble, t, 24)[::-1]
    if hand is not None:
        D = hang(hand, (pile[0], pile[1]), 10, 0.0, seed)
        P = np.vstack([A_, D[1:], G[1:]])
    else:
        P = np.vstack([A_, G[1:]])
    return P, G


def draw_line(F, P, a=1.0, w=1.0, draw=1.0, tip=True):
    """The line in gloom.unravel's own two strokes (its pale twin offset up and right at night, then the dark
    line). draw: 0..1 or (d0, d1) of it exists (from its first point)."""
    if a <= 0.003 or len(P) < 2:
        return
    day = F.day
    cols = _cols(day)
    kw = dict(UNRAVEL_LINE)
    wl = kw.pop("w") * w
    sd = kw.pop("seed")
    if not day:
        z = F.cam.zoom
        k = max(0.6, min(2.0, z)) / z
        chalk(F, P + (1.5 * k, -1.3 * k), cols["edge"], wl, 0.5 * a, sd, draw=draw, **kw)
    chalk(F, P, cols["dark"], wl, a, sd, draw=draw, **kw)
    if tip:
        disc(F, P[-1, 0], P[-1, 1], 2.6 * w, cols["tip"], 0.7 * a, None, floor=1.1)


def _line_rise(w):
    return ease(seg(w, 0.24, 0.58)) * (1.0 + 0.07 * math.sin(math.pi * seg(w, 0.44, 0.80)))


def hill_line(F, P, w, a=1.0, seed=4, span=None, lead=None):
    """hills.hill_from_line for the line P as it lies, point for point: w 0 .. 0.30 it is pulled out straight
    along the ground (its near end first, the far end cast out last), 0.24 .. 0.58 it lifts into the shape of
    the hill, 0.42 .. 0.86 the ground swells up under it (hill_rise) and the contour's chalk comes up while the
    dark is rubbed off, from 0.86 it melts into the ground line. The dark line keeps unravel's stroke. lead:
    a world point the near end is carried by (the casting hand) while w < 0.30. Returns hill_rise(w)."""
    w = min(1.0, max(0.0, float(w)))
    r = hill_rise(w)
    if w >= 1.0 or a <= 0.003:
        return r
    xa, xb = HILL1_SPAN if span is None else span
    Q0 = np.asarray(P, dtype=np.float64)
    d = _arc(Q0)
    q = d / max(1e-6, d[-1])
    tx = xa + (xb - xa) * q
    T = np.stack([tx, ground_y(tx, max(r, _line_rise(w))) - 1.0], axis=1)
    e = smooth(seg(w, 0.0, 0.30) * 1.5 - 0.5 * q)
    Q = Q0 + (T - Q0) * e[:, None]
    Q[:, 1] -= np.sin(np.pi * e) * (22.0 + 64.0 * np.sin(np.pi * q) ** 0.8)
    if lead is not None:                                  # the near stretch rides in the casting hand
        g = math.sin(math.pi * seg(w, 0.0, 0.32)) * np.clip(1.0 - q / 0.08, 0.0, 1.0) ** 1.5
        Q = Q + (np.asarray(lead, dtype=np.float64) - Q[0]) * g[:, None]
    k = ease(seg(w, 0.52, 0.88))
    out = 1.0 - ease(seg(w, 0.86, 1.0))
    if k > 0.0:
        chalk(F, Q, F.pick(C.CHALK_COOL, C.PENCIL), 4.4 + 1.6 * (1.0 - k), a * out * 0.95 * k ** 0.7, seed=seed,
              wob=1.0 + 0.5 * (1.0 - k), taper=0.8, grain="dense", edge=0.34, step=5.0)
    if k < 1.0:
        draw_line(F, Q, a * out * (1.0 - k), w=1.0 - 0.45 * k, tip=False)
    return r


def strand_line(F, P, v=None, a=1.0, w=1.0, seed=12, draw=1.0, n=40):
    """gloom.strand's ribbon along any world polyline P (its first point below, at the child): the same
    pressure profile, colour and pale tip. v: the coordinate of each point of P that the pressure profile
    and `draw` are measured in (increasing from P[0]; default the index fraction 0..1, as strand() does:
    with P = strand_pts(p0, p1, ...) this is exactly strand()). A strand made longer at its lower end keeps
    the profile of its upper part when v of the added stretch runs below 0. draw: 0..1 or (d0, d1) in v."""
    P = np.asarray(P, dtype=np.float64)
    v = np.linspace(0.0, 1.0, len(P)) if v is None else np.asarray(v, dtype=np.float64)
    d0, d1 = (float(v[0]), float(draw)) if not isinstance(draw, tuple) else draw
    d0, d1 = max(d0, float(v[0])), min(d1, float(v[-1]))
    if d1 - d0 <= 0.01 or a <= 0.003:
        return
    uu = np.linspace(d0, d1, n)
    Q = np.stack([np.interp(uu, v, P[:, 0]), np.interp(uu, v, P[:, 1])], axis=1)
    wpx, aa = F.lw(4.0 * w, a, 1.4)
    prof = (0.75 + 0.35 * vn(uu * 7.0 + seed, seed + 3)) * (0.5 + 0.5 * smooth((d1 - uu) / 0.08)) * (0.6 + 0.4 * smooth((uu - d0) / 0.05))
    cols = _cols(F.day)
    _stroke(F, Q, wpx * prof, cols["dark"], aa, "dense", 1.25, F.day)
    if d1 < 0.999:
        disc(F, Q[-1, 0], Q[-1, 1], 2.4 * w, cols["tip"], 0.8 * a, None, floor=1.1)


def resample(P, n):
    """P resampled to n points evenly along its length."""
    P = np.asarray(P, dtype=np.float64)
    d = _arc(P)
    u = np.linspace(0.0, d[-1], n)
    return np.stack([np.interp(u, d, P[:, 0]), np.interp(u, d, P[:, 1])], axis=1)
