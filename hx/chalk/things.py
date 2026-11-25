"""hx.chalk.things: the small things that carry the story.

Each is something the child handles or looks at, on screen for a few seconds, and has to read at once:
the family drawing (whole, torn, held as two halves, taped), strips of amber tape, the hero with a
cape, the small speech balloon and the soap bubbles, the voice line, the bare bulb and its moth, the
phone, the crows and the birds, the chalk stub and the lines it goes over, the string of the tangle.

Two kinds, all in WORLD coordinates through F.cam:

  * builders return a Sketch of named strokes (family, wall_drawing, tape, hero, balloon): give them
    times, let them take part in a declared morph, then .draw(F). They take no Frame, so a builder
    that has two skins takes `day=` (pass F.day);
  * the others draw at once with F and return the points a scene needs (hands, tips, light).

Clocks: what ACTS takes a progress or a true time from the scene (a landing, a ring, the wings of a
moth); what is merely ALIVE (a crow shifting on the wire, a string swaying, the voice wavering) runs
on F.tb by default and stands still in the two silences. Nothing here keeps state.
The doc is hx/chalk/doc/things.md.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from .core import (A, C, FPS, PLUS, WIDE, Frame, arc, blob, chalk, disc, ease, ease_out, fill, hand, htab, mix, ramp, rnd, rsym,
                   seg, smooth, smudge, spline, vn)
from .sketch import Fill, Sketch, Stroke

__all__ = ["SHEET", "family", "wall_drawing", "family_held", "family_half", "tape", "sketch_tip", "hero", "BALLOON_FREE",
           "balloon", "bubble", "float_up", "voice_line", "hanging_lamp", "moth", "moth_path", "moth_trail", "PHONE_LEN",
           "RING_TIMES", "phone", "phone_held", "crow", "crow_land", "crow_fly", "crows_on_wire", "perches", "swing", "bird",
           "flock", "STUB_LEN", "stub_grip", "chalk_stub", "restroke", "string"]

FLOOR = 742.0


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def _xf(P, pos, ang: float = 0.0, s: float = 1.0, anchor=(0.0, 0.0)):
    """Local points -> world: turned by ang about `anchor`, scaled by s, the anchor put on `pos`."""
    P = np.asarray(P, dtype=np.float64) - anchor
    c, n = math.cos(ang), math.sin(ang)
    return np.stack([pos[0] + s * (P[:, 0] * c - P[:, 1] * n), pos[1] + s * (P[:, 0] * n + P[:, 1] * c)], axis=1)


def _pt(p, pos, ang: float = 0.0, s: float = 1.0, anchor=(0.0, 0.0)):
    q = _xf(np.asarray([p], dtype=np.float64), pos, ang, s, anchor)[0]
    return float(q[0]), float(q[1])


def _lines(F: Frame, lines, col, w: float, a: float = 1.0, grain: str | None = "dense", seed: int = 0, wob: float = 0.0,
           floor: float = 1.1, close: bool = False):
    """Several world polylines in ONE path with one pen (constant width): the cheap line for details
    too small to need a ribbon. wob > 0 gives each its hand and its boil."""
    ws, a = F.lw(w, a, floor)
    if a <= 0.003:
        return
    cam, z = F.cam, F.cam.zoom
    p = skia.Path()
    for i, P in enumerate(lines):
        if wob > 0.0:
            P = hand(P, seed + i * 7, F.k, wob, 4.0, 1.0, z)[0]
        S = cam.pts(P).tolist()
        p.moveTo(*S[0])
        for x, y in S[1:]:
            p.lineTo(x, y)
        if close:
            p.close()
    F.c.drawPath(p, F.pen(col, ws, a, grain))


_BEAM_IDX: dict = {}


def _beam(F: Frame, x0, y0, h0, x1, y1, h1, col, a0: float, a1: float, additive: bool = True, edge: float = 1.5):
    """A beam of rubbed light from world (x0, y0), half width h0, down to (x1, y1), half width h1:
    strength a0 at the top running to a1 at the bottom, strongest down its middle and dying away to
    nothing at both sides (edge: how soon), so that it has no outline. One mesh through the glow grain."""
    if max(a0, a1) <= 0.003:
        return
    nr, nc = 8, 11
    v = np.linspace(0.0, 1.0, nr + 1)
    u = np.linspace(-1.0, 1.0, nc)
    X = (x0 + (x1 - x0) * v)[:, None] + (h0 + (h1 - h0) * v)[:, None] * u[None, :]
    Y = np.repeat((y0 + (y1 - y0) * v)[:, None], nc, axis=1)
    S = F.cam.pts(np.stack([X.ravel(), Y.ravel()], axis=1))
    lo, hi = S.min(0), S.max(0)
    if hi[0] < 0.0 or lo[0] > F.surf.width() or hi[1] < 0.0 or lo[1] > F.surf.height():
        return
    al = (a0 + (a1 - a0) * v ** 0.8)[:, None] * ((1.0 - u * u) ** edge)[None, :]
    if (nr, nc) not in _BEAM_IDX:
        idx = []
        for i in range(nr):
            for j in range(nc - 1):
                p, q = i * nc + j, (i + 1) * nc + j
                idx += [p, q, p + 1, p + 1, q, q + 1]
        _BEAM_IDX[(nr, nc)] = idx
    pts = [skia.Point(x, y) for x, y in S.tolist()]
    cols = [(int(k) << 24) | 0xFFFFFF for k in np.clip(al.ravel() * 255.0 + 0.5, 0, 255).tolist()]
    F.c.drawVertices(skia.Vertices.MakeCopy(skia.Vertices.kTriangles_VertexMode, pts, None, cols, _BEAM_IDX[(nr, nc)]),
                     F.paint(col, 1.0, "glow" + WIDE, PLUS if additive else None), skia.BlendMode.kSrcIn)


def _dense(P, step: float = 2.0):
    """A polyline with points added along its segments (its corners kept)."""
    P = np.asarray(P, dtype=np.float64)
    out = [P[:1]]
    for a_, b_ in zip(P[:-1], P[1:]):
        n = max(1, int(math.ceil(math.hypot(*(b_ - a_)) / step)))
        out.append(a_ + (b_ - a_) * (np.arange(1, n + 1) / n)[:, None])
    return np.vstack(out)


# --------------------------------------------------------------------------
# tape
# --------------------------------------------------------------------------
def tape(x0, y0, x1, y1, w: float = 13.0, d: float = 1.0, seed: int = 560, a: float = 1.0, day: bool = False,
         name: str = "tape") -> Sketch:
    """A strip of amber tape laid from world (x0, y0) to (x1, y1), w wide, both short ends torn.
    d = 0..1: how much of it has been laid (it grows from the first point, its torn end leading).
    Parts: strip.fill (the tape), strip (its rim), shine (a pale sliver along it)."""
    d = min(1.0, max(0.0, float(d)))
    if d <= 0.0:
        return Sketch([], name)
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.atan2(y1 - y0, x1 - x0)
    ln = max(w * 0.35, L * d)
    n = 5

    def end(u0, sgn, sd):                                  # a torn end: a few teeth across the strip
        v = np.linspace(-0.5, 0.5, n) * w
        j = np.arange(n)
        return np.stack([u0 + sgn * w * 0.16 * ((j % 2) * 1.4 - 0.5 + 0.8 * (htab(j, 5, sd) - 0.5)), v], axis=1)

    e0, e1 = end(0.0, -1.0, seed * 7 + 1), end(ln, 1.0, seed * 7 + 3)
    k = max(2, int(ln / (w * 0.9)) + 1)
    uu = np.linspace(0.0, ln, k + 2)[1:-1]
    top = np.stack([uu, -0.5 * w + w * 0.05 * (2 * htab(np.arange(k), 3, seed) - 1)], axis=1)
    bot = np.stack([uu[::-1], 0.5 * w + w * 0.05 * (2 * htab(np.arange(k), 3, seed + 5) - 1)], axis=1)
    P = _xf(np.vstack([e0[::-1], top, e1, bot, e0[-1:]]), (x0, y0), ang)       # round the strip, from its first corner
    rim = C.AMBER_DEEP if day else C.AMBER
    body, lit = (C.MUSTARD, C.AMBER_PALE) if day else (mix(C.AMBER, C.AMBER_PALE, 0.45), C.AMBER_PALE)
    s1 = max(w * 0.4, ln - w * 0.3)                         # the shine: a pale sliver along the upper edge
    sh = _xf(A((w * 0.3, -w * 0.27), (s1, -w * 0.29), (s1, -w * 0.17), (w * 0.3, -w * 0.14)), (x0, y0), ang)
    grow = 0.55 + 0.45 * min(1.0, d * 3.0)
    return Sketch([
        Fill(P, lit, 0.0, 9.0, 3.0, 0.0, seed + 1, knock=body, base=0.55 * a, name="strip.fill"),
        Stroke(P, rim, max(1.3, w * 0.13), 0.9 * a * grow, seed + 2, "strip", wob=0.0, edge=0.0, step=4.0, taper=0.9),
        Fill(sh, C.CREAM, 0.0, 9.0, 3.0, 0.0, seed + 3, knock=C.CREAM, base=0.0, name="shine"),
    ], name)


# --------------------------------------------------------------------------
# the family drawing
# --------------------------------------------------------------------------
SHEET = (150.0, 112.0)            # the sheet in its own units (times s in the world)
_GRIP = (62.0, 30.0)              # where a hand holds a half: |u| from the middle, v below the middle
_PIN = (62.0, -45.0)              # where a half is pinned to the wall
_TAPES = ((-31.0, -0.24), (46.0, 0.16))     # the two strips: v on the tear, slant (above and below the small figure)


@lru_cache(maxsize=8)
def _tear(seed: int):
    """The tear, in sheet units: a ragged line down the middle, the same in every state. It is wild
    above and below the small figure and quieter where it runs through it, so that the two halves
    of that figure still read."""
    n = 15
    v = np.linspace(-SHEET[1] / 2, SHEET[1] / 2, n)
    j = np.arange(n)
    amp = np.where(v < -20.0, 6.0, np.where(v > 39.0, 4.2, 2.3)) * (0.55 + 0.75 * htab(j, 7, seed * 13 + 1))
    u = (-1.0) ** j * amp + 1.0 - 2.0 * j / (n - 1.0)
    u[0] *= 0.4
    u[-1] *= 0.5
    return np.stack([u, v], axis=1)


def _split(P, tr):
    """Cut a polyline (sheet units) along the tear: [(side, piece), ...], side -1 left / +1 right."""
    P = _dense(P, 1.5)
    dlt = P[:, 0] - np.interp(P[:, 1], tr[:, 1], tr[:, 0])
    sd = np.where(dlt < 0.0, -1, 1)
    out, i0 = [], 0
    for i in range(1, len(P) + 1):
        if i == len(P) or sd[i] != sd[i0]:
            piece = [P[i0:i]]
            if i0 > 0:                                   # start on the tear
                w_ = dlt[i0 - 1] / (dlt[i0 - 1] - dlt[i0])
                piece.insert(0, (P[i0 - 1] + (P[i0] - P[i0 - 1]) * w_)[None, :])
            if i < len(P):                               # end on the tear
                w_ = dlt[i - 1] / (dlt[i - 1] - dlt[i])
                piece.append((P[i - 1] + (P[i] - P[i - 1]) * w_)[None, :])
            Q = np.vstack(piece)
            if len(Q) >= 2 and np.hypot(np.diff(Q[:, 0]), np.diff(Q[:, 1])).sum() > 1.6:
                out.append((int(sd[i0]), Q))
            i0 = i
    return out


def _head(u, v, r, seed, a0=math.pi, turns=1.5):
    """A head as a child draws it: once round and a little further, ending at the neck."""
    q = np.linspace(a0, a0 + turns * math.pi, 15)
    rr = r * (1.0 + 0.06 * (2 * htab(np.arange(15), 3, seed) - 1))
    return np.stack([u + np.cos(q) * rr, v + np.sin(q) * rr * 0.96], axis=1)


@lru_cache(maxsize=8)
def _family_local(seed: int, detail: int):
    """The drawing in sheet units, already cut along the tear: {side: [(name, points, class)]}, the
    tear, the corners. Two tall figures and a small one between them, hand in hand; the tear runs
    through the small one, and each half keeps half of it."""
    tr = _tear(seed)
    w2, h2 = SHEET[0] / 2, SHEET[1] / 2
    tu = lambda v: float(np.interp(v, tr[:, 1], tr[:, 0]))          # noqa: E731
    vb = 37.0
    out = {-1: [], 1: []}
    if detail >= 1:
        raw = []
        # the corner sun (white chalk on the pale sheet) and the ground: what every such drawing has
        sx, sy, sun = -w2 + 21.0, -h2 + 19.0, []
        for j in range(9):                                   # round once, a ray out and back at every eighth
            q = j * math.pi / 4 + 0.3
            rr = 6.6 + 0.8 * rsym(seed + j, 41)
            sun += [(sx + rr * math.cos(q - 0.3), sy + rr * math.sin(q - 0.3)), (sx + rr * math.cos(q), sy + rr * math.sin(q))]
            if j < 8:
                r1 = 12.0 + 2.6 * rnd(seed + j, 42)
                sun += [(sx + r1 * math.cos(q + 0.05), sy + r1 * math.sin(q + 0.05)), (sx + rr * math.cos(q + 0.1), sy + rr * math.sin(q + 0.1))]
        raw.append(("sun", A(*sun), "sun"))
        gx = np.linspace(-w2 + 8.0, w2 - 9.0, 30)
        gi = np.arange(30)
        raw.append(("ground", np.stack([gx, vb + 4.5 + 2.6 * ((gi % 2) * 2 - 1) * (0.6 + 0.4 * htab(gi, 5, seed)) + 1.5 * np.sin(gx * 0.05)],
                                       axis=1), "c4"))
        # the tall one on the left: a triangle dress, waving
        u0, h0, r0 = -42.0, 63.0, 8.6
        hc0 = vb - h0 + r0
        n0 = (u0, hc0 + r0)
        hem, bw = vb - h0 * 0.20, h0 * 0.20
        j = np.arange(9)
        raw.append(("fig0.dress", np.stack([u0 + ((j % 2) * 2 - 1) * bw * (0.20 + 0.60 * j / 8.0), n0[1] + 3.5 + (hem - n0[1] - 6.0) * j / 8.0],
                                           axis=1), "c0"))
        raw.append(("fig0.body", np.vstack([_head(u0, hc0, r0, seed + 1),
                                            A(n0, (u0 - bw, hem), (u0 - bw * 0.40, hem), (u0 - bw * 0.42, vb), (u0 - bw * 0.40, hem),
                                              (u0 + bw * 0.40, hem + 0.4), (u0 + bw * 0.46, vb), (u0 + bw * 0.40, hem + 0.4), (u0 + bw, hem + 0.6),
                                              (u0 + 0.6, n0[1] + 1.0))]), "ink"))
        # the tall one on the right: a cap of hair, long legs
        u2, h2_, r2 = 42.0, 68.0, 9.0
        hc2 = vb - h2_ + r2
        n2 = (u2, hc2 + r2)
        hip2 = vb - h2_ * 0.36
        cap = A((u2 + r2 * 1.02, hc2 - r2 * 0.42), (u2 + r2 * 0.25, hc2 - r2 * 1.26), (u2 - r2 * 0.99, hc2 - r2 * 0.25))
        raw.append(("fig2.body", np.vstack([cap, _head(u2, hc2, r2, seed + 3), A(n2, (u2 + 0.5, hip2), (u2 - h2_ * 0.10, vb), (u2 + 0.5, hip2),
                                                                                (u2 + h2_ * 0.11, vb))]), "ink"))
        # the small one in the middle, drawn as its two halves (each wholly on its side of the tear)
        u1, h1, r1 = 0.3, 41.0, 7.8
        hc1 = vb + 0.5 - h1 + r1
        sh1, hip1 = hc1 + r1 + 2.2, vb + 0.5 - h1 * 0.30
        ring = [(sd_, Q) for sd_, Q in _split(_head(tu(hc1 - r1), hc1, r1, seed + 2, -math.pi / 2, 2.0), tr)]
        for side in (-1, 1):
            arcs = [Q for sd_, Q in ring if sd_ == side]
            hd = max(arcs, key=len)
            if hd[0, 1] > hd[-1, 1]:
                hd = hd[::-1]                                # from the crown down to the chin
            top = hd[0]
            tuft = A((top[0] + side * 6.4, top[1] - 2.2), (top[0] + side * 5.0, top[1] + 2.4), (top[0] + side * 3.2, top[1] - 4.6),
                     (top[0] + side * 1.6, top[1] + 0.6), (top[0] + side * 0.5, top[1] - 3.4))
            body = A((u1 + side * 5.6, sh1), (u1 + side * 5.3, hip1), (tu(hip1) + side * 1.0, hip1 + 0.3), (u1 + side * 3.6, hip1),
                     (u1 + side * 4.6, vb + 0.5))
            jz = np.arange(6)
            lo, hi = tu(sh1 + 6.0) + side * 1.1, u1 + side * 4.4
            jum = np.stack([np.where(jz % 2 == 0, lo, hi) + 0.0 * jz, sh1 + 1.6 + (hip1 - sh1 - 2.6) * jz / 5.0], axis=1)
            out[side].append(("fig1.jumper", jum, "c1"))
            out[side].append(("fig1.body", np.vstack([tuft, hd, body]), "ink"))
        # hand in hand: each link is one line from a tall shoulder to the small one's
        hl, hr = (-21.5, sh1 + 2.6), (22.0, sh1 + 1.8)
        s0, s2 = (u0, n0[1] + r0 * 0.55), (u2, n2[1] + r2 * 0.55)
        raw.append(("fig0.arms", A((s0[0] - 15.0, s0[1] - 13.0), (s0[0] - 9.0, s0[1] + 1.0), s0, hl, (u1 - 5.6, sh1 + 0.8)), "ink"))
        raw.append(("fig2.arms", A((u1 + 5.6, sh1 + 0.8), hr, s2, (s2[0] + 10.0, s2[1] + 9.0), (s2[0] + 14.0, s2[1] + 21.0)), "ink"))
        dots = []
        if detail >= 2:                                      # faces: two dots and a smile each (small filled shapes)
            cq = np.linspace(0.0, 2 * math.pi, 8)[:-1]
            for nm, (fu, fv, fr) in (("fig0", (u0, hc0, r0)), ("fig1", (tu(hc1), hc1, r1)), ("fig2", (u2, hc2, r2))):
                ev = fv - fr * 0.10
                for sg in (-1, 1):
                    eu = (tu(ev) + sg * max(fr * 0.40, 2.8)) if nm == "fig1" else fu + sg * fr * 0.40      # clear of the tear
                    dots.append((-1 if eu < tu(ev) else 1, f"{nm}.eye_{'l' if sg < 0 else 'r'}",
                                 np.stack([eu + 1.15 * np.cos(cq), ev + 1.35 * np.sin(cq)], axis=1)))
                raw.append((f"{nm}.smile", arc(fu, fv + fr * 0.20, fr * 0.50, fr * 0.36, 0.2, math.pi - 0.2, 7), "face"))
        seen = {}
        for nm, P, cls in raw:
            for side, Q in _split(P, tr):
                k = seen.get((side, nm), 0)
                seen[(side, nm)] = k + 1
                if cls == "face":                            # a line made into a thin sliver
                    d_ = np.gradient(Q, axis=0)
                    nr_ = np.stack([-d_[:, 1], d_[:, 0]], axis=1) / (np.hypot(d_[:, 0], d_[:, 1])[:, None] + 1e-9)
                    hw = (0.32 + 0.5 * np.sin(np.pi * np.linspace(0.0, 1.0, len(Q))))[:, None]
                    Q, cls = np.vstack([Q + nr_ * hw, (Q - nr_ * hw)[::-1]]), "dot"
                out[side].append((nm if k == 0 else f"{nm}{k}", Q, cls))
        for side, nm, P in dots:
            out[side].append((nm, P, "dot"))
        order = {"sun": 0, "c4": 0, "c0": 1, "c1": 1, "ink": 2, "dot": 3}
        for side in (-1, 1):
            out[side].sort(key=lambda it: order[it[2]])
    j = np.arange(4)
    cj = 1.6 * (2 * htab(j, 11, seed * 5 + 2) - 1)                    # the corners are not quite square
    corner = {(-1, -1): (-w2 + cj[0], -h2 + cj[1]), (1, -1): (w2 + cj[1], -h2 + cj[2]),
              (1, 1): (w2 + cj[2], h2 + cj[3]), (-1, 1): (-w2 + cj[3], h2 + cj[0])}
    return out, tr, corner


def _family_items(xf, s, tear, taped, pins, detail, day, seed, a=1.0, sides=(-1, 1), joined=True):
    """The sheet's items. xf[side] = (pos, ang, anchor): where that half is (see _xf)."""
    loc, tr, corner = _family_local(int(seed), int(detail))
    if day:
        paper, lit, rim, ink, knock = mix(C.CREAM, C.DAY_SHADE, 0.25), C.CREAM, mix(C.PENCIL, C.DAY, 0.42), C.PENCIL, C.DAY
        cols = dict(c0=C.CORAL, c1=C.JUMPER, c4=C.HILL_NEAR, sun=C.MUSTARD)
        shade, shade_a, rip, fibre = C.SHADOW, 0.30, mix(C.PENCIL, C.DAY_SHADE, 0.45), (1.0, 1.0, 1.0)
    else:
        paper, lit, rim, ink, knock = (0.52, 0.565, 0.70), (0.68, 0.72, 0.84), (0.82, 0.85, 0.92), (0.10, 0.12, 0.21), C.KNOCK
        cols = dict(c0=(0.30, 0.37, 0.60), c1=(0.20, 0.33, 0.72), c4=(0.33, 0.40, 0.57), sun=(0.93, 0.95, 1.0))
        shade, shade_a, rip, fibre = C.PAPER_DEEP, 0.60, (0.09, 0.105, 0.17), (0.92, 0.94, 0.98)
    live = detail >= 2                                     # close enough for the lines to wobble and boil
    wob = min(1.0, max(0.12, 0.42 * s))
    step = 4.0 if s < 1.5 else 6.0
    kw_ink = dict(wob=wob * 0.7 if live else 0.0, edge=0.0, step=step, taper=0.75)
    kw_col = dict(wob=0.0, edge=0.0, step=step, taper=0.8, grain="mid")
    torn = tear >= 1.0
    sk = []

    def T(P, side):
        pos, ang, anchor = xf[side]
        return _xf(P, pos, ang, s, anchor)

    def sheet_fill(P, side, nm, sd):
        # the shade the sheet throws: only the band that shows beside it (down its right-hand side and under it)
        o = np.array((2.6, 3.4))
        i0, i1 = int(np.argmin(P[:-1, 1] - P[:-1, 0])), int(np.argmax(P[:-1, 1] - P[:-1, 0]))      # top right, bottom left
        ring = np.vstack([P[:-1], P[:-1]])
        run = ring[i0:i0 + ((i1 - i0) % (len(P) - 1)) + 1]       # the outline from the top right corner round to the bottom left
        sk.append(Fill(T(np.vstack([run, (run + o)[::-1]]), side), shade, 0.5, 9, 4, 0.0, seed + sd, base=shade_a * a,
                       name=nm.replace("sheet.fill", "shade")))
        sk.append(Fill(T(P, side), lit, 0.42 + 0.1 * side, 7.0 * s, 3.6 * s, 0.0, seed + sd + 1, knock=paper, base=0.62 * a, name=nm))

    if not torn and len(sides) == 2:
        sheet_fill(A(corner[(-1, -1)], corner[(1, -1)], corner[(1, 1)], corner[(-1, 1)], corner[(-1, -1)]), -1, "sheet.fill", 0)
    for side in sides:
        h_ = "l" if side < 0 else "r"
        if torn or len(sides) == 1:
            sheet_fill(np.vstack([[corner[(side, -1)]], tr, [corner[(side, 1)]], [corner[(side, -1)]]]), side, f"{h_}.sheet.fill", side)
        out3 = np.vstack([tr[:1], [corner[(side, -1)]], [corner[(side, 1)]], tr[-1:]])
        sk.append(Stroke(T(out3, side), rim, 2.3 * s, 0.95 * a, seed + 4 + (side > 0), f"{h_}.sheet", wob=wob, edge=0.0, taper=1.0))
        items = loc[side]
        if items:                                        # every point of the half through the transform at once
            W = T(np.vstack([P for _, P, _ in items]), side)
        o = 0
        for i, (nm, P0, cls) in enumerate(items):
            sd = seed + 20 + i + (40 if side > 0 else 0)
            P, o = W[o:o + len(P0)], o + len(P0)
            if cls == "ink":
                sk.append(Stroke(P, ink, 2.0 * s, 0.95 * a, sd, f"{h_}.{nm}", **kw_ink))
            elif cls == "dot":
                sk.append(Fill(P, ink, 0.0, 9.0, 4.0, 0.0, sd, knock=ink, base=0.0, name=f"{h_}.{nm}"))
            else:
                sk.append(Stroke(P, cols[cls], (3.6 if cls in ("c0", "c1") else 2.4) * s, (0.95 if cls == "sun" else 0.85) * a,
                                 sd, f"{h_}.{nm}", **kw_col))
    if tear > 0.0:
        f1 = min(1.0, tear)
        touch = joined and len(sides) == 2
        if touch:                                        # the rip itself, where the halves still touch
            P = T(tr, -1)
            if not torn:                                 # it runs down from the top edge
                P = _dense(P, 2.0 * s)
                P = P[: max(2, int(len(P) * f1))]
            sk.append(Stroke(P, rip, 2.0 * s, 0.9 * a, seed + 8, "tear", wob=0.0, edge=0.0, step=5.0, taper=0.6))
        # the pale fibres of a torn edge: on each half when they are apart, down one side of the rip when they touch
        for side in (sides if not touch else (1,) if live else ()):
            h_ = "l" if side < 0 else "r"
            P = T(tr + (side * (1.5 if touch else 0.9), 0.0), side)
            if not torn:
                P = _dense(P, 2.0 * s)
                P = P[: max(2, int(len(P) * f1))]
            sk.append(Stroke(P, fibre, (1.1 if touch else 1.5) * s, (0.6 if touch else 0.85) * a, seed + 9 + (side > 0), f"{h_}.edge",
                             wob=0.0, edge=0.0, step=5.0, taper=0.6, floor=1.0))
    if taped > 0.0 and len(sides) == 2:
        for j, (v, sl) in enumerate(_TAPES):
            dj = min(1.0, max(0.0, taped - j))
            if dj <= 0.0:
                continue
            u = float(np.interp(v, tr[:, 1], tr[:, 0]))
            p0 = T(A((u - 19.0, v - 19.0 * sl)), -1)[0]
            p1 = T(A((u + 19.0, v + 19.0 * sl)), 1)[0]
            sk.append(tape(p0[0], p0[1], p1[0], p1[1], 12.5 * s, dj, seed + 60 + j * 5, a, day, f"tape{j}"))
    if pins:
        for side in sides:
            p = T(A((side * _PIN[0], _PIN[1])), side)[0]
            pc = C.CORAL if day else C.CHALK
            sk.append(Fill(blob(p[0], p[1], 3.6 * s, 3.6 * s, seed + 70 + side, 0.12, 9), pc, 0.0, 9.0, 4.0, 0.0, seed + 72 + side, knock=pc,
                           base=0.0, name="pin_l" if side < 0 else "pin_r"))
    return sk


def family(x, y, s: float = 1.0, tear: float = 1.0, gap: float = 0.0, askew: float = 0.0, rot: float = 0.0,
           taped: float = 0.0, pins: bool = False, detail: int = 1, day: bool = False, seed: int = 300, a: float = 1.0,
           name: str = "pic") -> Sketch:
    """The child's drawing of three figures hand in hand on a sheet of paper, as a Sketch.

    (x, y): its centre; the sheet is SHEET (150 x 112) times s; rot turns it.
    tear: 0 whole .. 1 torn through (in between the rip has run that far down from the top edge).
    gap, askew (only when torn through): how far apart the halves hang, in sheet units, and by how
    much each has dropped about its pin (rad): on the wall at night gap 9, askew 0.07.
    taped: 0..2, the strips of amber tape across the tear (1.6 = the first laid, the second 60 percent).
    pins: the two pins that hold it on a wall. detail: 0 the bare sheet, 1 the figures (seated lines),
    2 their faces too and lines that boil (from about 200 px of sheet on screen).
    day: the warm-paper skin (pass F.day).
    Parts: l.* and r.*, the two halves (sheet, sheet.fill, shade, edge, sun, ground, fig0.body
    fig0.dress fig0.arms, fig1.body fig1.jumper, fig2.body fig2.arms, with detail 2 figN.eye_l
    figN.eye_r figN.smile), tear, tape0.* tape1.*, pin_l pin_r; a whole sheet has one sheet.fill and
    shade."""
    torn = tear >= 1.0
    g = gap if torn else 0.0
    k = askew if torn else 0.0
    xf = {}
    for side in (-1, 1):
        pin = (side * _PIN[0], _PIN[1])
        pos = _pt((pin[0] + side * g * 0.5, pin[1] + (g * 0.10 if side > 0 else 0.0)), (x, y), rot, s)
        xf[side] = (pos, rot - side * k, pin)
    return Sketch(_family_items(xf, s, tear, taped, pins, detail, day, seed, a, joined=g < 1.5), name)


def wall_drawing(x, y, s: float = 1.0, gap: float = 9.0, taped=False, seed: int = 300, rot: float = -0.05,
                 askew: float = 0.07, day: bool = False, detail: int = 1, name: str = "pic") -> Sketch:
    """The family drawing as it hangs on the wall (see family): torn, the halves `gap` apart and a
    little askew, each on its pin; or, taped=True, mended with two strips of tape, the tear showing."""
    if taped:
        return family(x, y, s, 1.0, 0.0, 0.0, rot, 2.0 if taped is True else float(taped), True, detail, day, seed, 1.0, name)
    return family(x, y, s, 1.0, gap, askew, rot, 0.0, True, detail, day, seed, 1.0, name)


def family_half(F: Frame, side: int, x, y, s: float = 0.8, rot: float = 0.0, a: float = 1.0, detail: int = 2,
                seed: int = 300, day: bool | None = None, grip=None):
    """One half of the torn drawing, drawn at once: side -1 the left half, +1 the right one, held at
    the world point (x, y) (a hand: the half is held by its outer lower part; grip = (u, v) in sheet
    units to hold it elsewhere, (0, 0) = the middle of the whole sheet), turned by rot.
    Returns the world point of the middle of its torn edge."""
    day = F.day if day is None else day
    anchor = (side * _GRIP[0], _GRIP[1]) if grip is None else grip
    xf = {side: ((x, y), rot, anchor)}
    Sketch(_family_items(xf, s, 1.0, 0.0, False, detail, day, seed, a, sides=(side,))).draw(F)
    return _pt((0.0, 0.0), (x, y), rot, s, anchor)


def family_held(F: Frame, hand_l, hand_r, s: float = 0.8, taped: float = 0.0, a: float = 1.0, detail: int = 2,
                seed: int = 300, day: bool | None = None, droop: float = 1.0) -> dict:
    """The drawing as two halves held in two hands (world points; hand_l holds the left half).

    Each half hangs from its hand by its outer lower part. With the hands 124 * s apart the halves
    meet and the picture is whole but for the tear; nearer than that they stay together between the
    hands; further apart each half follows its own hand and its torn edge drops (droop scales that).
    taped: 0..2 strips of tape (they span the gap if there is one).
    Returns {"c": middle of the tear, "gap": distance between the halves in world units,
    "ang": the angle of the sheet, "tape": [(p0, p1), (p0, p1)] the world ends of the two strips}."""
    day = F.day if day is None else day
    hl, hr = np.asarray(hand_l, dtype=np.float64), np.asarray(hand_r, dtype=np.float64)
    v = hr - hl
    dist = float(math.hypot(*v)) + 1e-9
    ang = math.atan2(v[1], v[0])
    d0 = 2.0 * _GRIP[0] * s
    extra = max(0.0, dist - d0)
    if dist <= d0:                                         # together: the hands slide on the paper
        mid, e = (hl + hr) / 2, v / dist
        hl, hr = mid - e * d0 / 2, mid + e * d0 / 2
    k = droop * 0.30 * ease_out(min(1.0, extra / (70.0 * s)), 2.0)
    xf = {-1: (tuple(hl), ang + k * (1.0 + 0.25 * rsym(seed, 31)), (-_GRIP[0], _GRIP[1])),
          1: (tuple(hr), ang - k * (1.0 + 0.25 * rsym(seed, 32)), (_GRIP[0], _GRIP[1]))}
    Sketch(_family_items(xf, s, 1.0, taped, False, detail, day, seed, a, joined=extra < 1.5 * s)).draw(F)
    tr = _tear(int(seed))
    tp = []
    for vv, sl in _TAPES:
        u = float(np.interp(vv, tr[:, 1], tr[:, 0]))
        tp.append((_pt((u - 19.0, vv - 19.0 * sl), *xf[-1][:2], s, xf[-1][2]), _pt((u + 19.0, vv + 19.0 * sl), *xf[1][:2], s, xf[1][2])))
    cl, cr = _pt((0.0, 0.0), *xf[-1][:2], s, xf[-1][2]), _pt((0.0, 0.0), *xf[1][:2], s, xf[1][2])
    return {"c": ((cl[0] + cr[0]) / 2, (cl[1] + cr[1]) / 2), "gap": extra, "ang": ang, "tape": tp}


# --------------------------------------------------------------------------
# a Sketch's chalk tip (for a hand that draws)
# --------------------------------------------------------------------------
def sketch_tip(S: Sketch, t: float):
    """The world point of the chalk tip of a Sketch at time t: the end of the stroke that is being
    drawn on at that moment (by its `on` times), else None. For the hand that does the drawing."""
    best = None
    for it in S:
        if isinstance(it, Stroke) and it.on and it.on[0] <= t < it.on[1]:
            p = seg(t, *it.on)
            f = 0.5 * p + 0.5 * ease(p)
            P = it.P
            u = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])
            best = (float(np.interp(f * u[-1], u, P[:, 0])), float(np.interp(f * u[-1], u, P[:, 1])))
    return best


# --------------------------------------------------------------------------
# the hero with a cape
# --------------------------------------------------------------------------
def hero(x, y, h: float = 150.0, wave: float = 0.0, face: int = 1, seed: int = 340, col=C.CHALK, a: float = 1.0,
         name: str = "hero") -> Sketch:
    """What the child wishes it were: a small figure of itself (the same tufts of hair), drawn in one
    thin bright line, feet apart on the world point (x, y), h tall to the top of its hair: a mask, a
    fist raised, a fist on the hip, a cape flying out behind. face +1: the raised fist on the right,
    the cape flying to the left.
    wave: -1..1 swings the free end of the cape (move it on the beats; rebuild the set every frame).
    Parts, in the order a hand draws them: head hair mask eye_b eye_f grin body leg_b leg_f arm_hip
    arm_up fist cape (+ cape.fill). It stands inside x - 0.68 h .. x + 0.36 h (mirrored by face),
    y - 1.14 h .. y (the raised fist is the top)."""
    k = h / 150.0
    f = float(face)
    w = 3.0 * k
    kw = dict(wob=0.55 * min(1.3, max(0.4, k)), edge=0.25, step=4.0)
    kd = dict(wob=0.0, edge=0.0, step=3.0)

    def L(*pts):
        return np.asarray([(x + f * px * k, y + py * k) for px, py in pts], dtype=np.float64)

    r = 23.0
    hy = -150.0 + r + 12.0
    q = np.linspace(0.6 * math.pi, 2.75 * math.pi, 22)
    head = L(*[(math.cos(v) * r * (1.0 + 0.04 * rsym(seed + i, 7)), hy + math.sin(v) * r * 0.97) for i, v in enumerate(q)])
    hp = []                                                # tufts standing on end, fanned round the crown
    for i, (b_, ln) in enumerate(((-2.75, 13.0), (-2.25, 19.0), (-1.78, 15.0), (-1.32, 21.0), (-0.86, 14.0), (-0.42, 17.0))):
        hp.append((math.cos(b_) * (r + 0.5), hy + math.sin(b_) * (r + 0.5)))
        if i < 5:
            m_ = b_ + 0.30
            hp.append((math.cos(m_) * (r + ln), hy + math.sin(m_) * (r + ln)))
    hair = L(*hp)
    mask = L((-r * 1.0, hy - 7.5), (-2.0, hy - 5.0), (r * 0.99, hy - 8.5), (r * 0.97, hy + 4.0), (2.0, hy + 2.5), (-r * 0.97, hy + 5.0), (-r * 1.0, hy - 7.5),
             (-8.0, hy - 6.0))
    sh_y, hip_y = hy + r + 5.0, -52.0
    body = L((-17, sh_y), (17, sh_y - 1), (7.5, hip_y), (-7, hip_y + 1), (-17, sh_y), (-9, sh_y - 1))
    leg_b = L((-6, hip_y), (-17, -5), (-29, -3))
    leg_f = L((6.5, hip_y), (16, -4), (29, -4))
    arm_hip = L((-17, sh_y + 2), (-37, sh_y + 19), (-9, hip_y - 6))
    fx, fy = 45.0, -163.0
    arm_up = L((17, sh_y + 1), (35, sh_y - 20), (fx - 2.0, fy + 9.0))
    fist = L(*[(fx + 2.6 * math.cos(v), fy + 2.4 * math.sin(v)) for v in np.linspace(0.4 * math.pi, 2.6 * math.pi, 9)])
    # the cape: a banner from the shoulders flying out behind, its far edge rippling; wave lifts and drops that edge
    sw = float(wave)
    t1 = (-96.0 + 4.0 * abs(sw), sh_y + 7.0 - 22.0 * sw)
    t2 = (-85.0 + 3.0 * abs(sw), -47.0 - 15.0 * sw)
    top = spline(A((-13.0, sh_y - 2.0), (-38.0, sh_y - 9.0 - 4.0 * sw), (-67.0, sh_y - 6.0 - 12.0 * sw), t1), 12)
    far = spline(A(t1, (t1[0] + 8.0, t1[1] * 0.7 + t2[1] * 0.3 + 2.0), (t2[0] - 9.0, t1[1] * 0.3 + t2[1] * 0.7), t2), 9)
    low = spline(A(t2, (-54.0, -61.0 - 6.0 * sw), (-25.0, -67.0 - 1.0 * sw), (-9.0, hip_y - 9.0)), 10)
    capeP = L(*np.vstack([top, far[1:], low[1:]]))
    hc = mix(col, C.CHALK_BLUE, 0.6)
    return Sketch([
        Stroke(head, col, w, 0.95 * a, seed + 1, "head", **kw),
        Stroke(hair, col, w, 0.95 * a, seed + 2, "hair", **kw),
        Stroke(mask, col, w * 0.9, 0.95 * a, seed + 14, "mask", wob=0.3, edge=0.2, step=4.0),
        Stroke(L((-10.0, hy - 3.5), (-9.4, hy + 1.2)), col, w * 1.2, a, seed + 11, "eye_b", **kd),
        Stroke(L((9.0, hy - 4.0), (9.6, hy + 0.8)), col, w * 1.2, a, seed + 12, "eye_f", **kd),
        Stroke(L(*[(math.cos(v) * 10.0, hy + 10.0 + math.sin(v) * 6.0) for v in np.linspace(0.2, math.pi - 0.35, 8)]), col, w * 0.9, 0.95 * a,
               seed + 13, "grin", **kd),
        Stroke(body, col, w, 0.95 * a, seed + 3, "body", **kw),
        Stroke(leg_b, col, w, 0.95 * a, seed + 4, "leg_b", **kw),
        Stroke(leg_f, col, w, 0.95 * a, seed + 5, "leg_f", **kw),
        Stroke(arm_hip, col, w, 0.95 * a, seed + 6, "arm_hip", **kw),
        Stroke(arm_up, col, w, 0.95 * a, seed + 7, "arm_up", **kw),
        Stroke(fist, col, w * 2.5, 0.95 * a, seed + 8, "fist", wob=0.0, edge=0.2, step=3.0, taper=1.0),
        Fill(np.vstack([capeP, capeP[:1]]), hc, 1.15 * f, 7.5 * k, 2.6 * k, 0.8 * a, seed + 10, grain="mid", name="cape.fill"),
        Stroke(capeP, col, w, 0.95 * a, seed + 9, "cape", **kw),
    ], name)


# --------------------------------------------------------------------------
# the small speech balloon, and soap bubbles
# --------------------------------------------------------------------------
BALLOON_FREE = 0.62               # the middle of a balloon, this share of its radii, stays empty


def balloon(x, y, rx: float = 105.0, ry: float = 74.0, mouth=None, seed: int = 820, col=None, a: float = 1.0,
            lw: float = 3.4, on=None, off=None, name: str = "balloon", day: bool = False) -> Sketch:
    """A speech balloon centred on the world point (x, y) with radii rx, ry, EMPTY: the words do not
    come. Its tail points at the world point `mouth` (and stops short of it); the line starts at the
    tip of the tail, so that it draws itself out of the mouth. The inside is rubbed clean; the ellipse
    BALLOON_FREE * (rx, ry) about (x, y) is free for whatever is put into it.
    on = (t0, t1): it draws itself between these times (the inside is rubbed clean as the line
    closes); off = (t0, t1): it is wiped. (Or give the parts their times yourself.)
    day: on the warm paper (pass F.day): pencil line, the inside rubbed back to the paper.
    Parts: shape.fill, shape."""
    if col is None:
        col = C.PENCIL if day else C.CHALK_COOL
    n = 40
    P = blob(x, y, rx, ry, seed, 0.045, n)[:-1]
    if mouth is None:
        mouth = (x - rx * 0.9, y + ry * 1.9)
    ang = math.atan2((mouth[1] - y) / ry, (mouth[0] - x) / rx)
    i0 = int(round((ang % (2 * math.pi)) / (2 * math.pi) * n)) % n
    ring = np.roll(P, -(i0 + 2), axis=0)[: n - 3]          # round the balloon, leaving the gap where the tail joins
    base = (ring[0] + ring[-1]) / 2
    m = np.asarray(mouth, dtype=np.float64)
    d = m - base
    ln = float(math.hypot(*d)) + 1e-9
    tip = m - d / ln * min(ln * 0.3, 0.16 * (rx + ry))
    nrm = np.array([-d[1], d[0]]) / ln
    bow = 0.10 * ln * (1.0 if rsym(seed, 5) > 0 else -1.0)
    s0 = spline(np.array([tip, (tip + ring[0]) / 2 + nrm * bow, ring[0]]), 7)
    s1 = spline(np.array([ring[-1], (tip + ring[-1]) / 2 + nrm * bow * 0.6, tip]), 7)
    Q = np.vstack([s0[:-1], ring, s1[1:]])
    S = Sketch([
        Fill(np.vstack([Q, Q[:1]]), C.DAY_SHADE if day else C.PAPER_DEEP, 0.3, 12.0, 5.0, 0.0, seed + 1, knock=C.DAY if day else C.PAPER,
             base=0.0, name="shape.fill"),
        Stroke(Q, col, lw, 0.95 * a, seed + 2, "shape", wob=0.9, taper=0.6),
    ], name)
    if on is not None:
        S.items[1].on = (on[0], on[1])
        S.items[0].on = (on[0] + 0.62 * (on[1] - on[0]), on[1] + 0.12)
    if off is not None:
        S.set_off(*off)
    return S


def float_up(x0, y0, age: float, seed: int = 0, rise: float = 46.0, sway: float = 16.0):
    """Where a bubble let go at the world point (x0, y0) is `age` seconds later: it rises (rise
    units a second, a little faster as it goes) and sways. Returns (x, y)."""
    age = max(0.0, float(age))
    ph = rnd(seed, 61) * 6.28
    return (x0 + sway * (math.sin(age * (1.1 + 0.5 * rnd(seed, 62)) + ph) - math.sin(ph)) * min(1.0, age * 1.2) + 9.0 * rsym(seed, 63) * age,
            y0 - rise * age * (1.0 + 0.10 * age) * (0.8 + 0.4 * rnd(seed, 64)))


def bubble(F: Frame, x, y, r, t: float | None = None, seed: int = 0, a: float = 1.0, pop: float = 0.0):
    """A soap bubble at the world point (x, y), radius r: pale, with a sheen; it wobbles slowly.
    t: the clock of its wobble (default F.tb). pop: 0..1 it bursts (a ring of short dashes flying out).
    Pale chalk at night; in the day skin a breath of pastel."""
    if a <= 0.003 or r <= 0.0:
        return
    t = F.tb if t is None else t
    ph = rnd(seed, 71) * 6.28
    day = F.day
    rim = mix(C.SKY_HI, C.PENCIL, 0.25) if day else C.CHALK_COOL
    hi = (1.0, 1.0, 1.0) if day else C.CHALK
    if pop > 0.0:
        if pop >= 1.0:
            return
        q = np.arange(9) * (2 * math.pi / 9) + ph
        r0, r1 = r * (1.0 + 0.5 * ease_out(pop, 2.0)), r * (1.12 + 0.9 * ease_out(pop, 2.0))
        _lines(F, [A((x + r0 * math.cos(v), y + r0 * math.sin(v)), (x + r1 * math.cos(v), y + r1 * math.sin(v))) for v in q], rim,
               max(1.6, r * 0.05), a * (1.0 - pop) ** 1.2, "mid")
        return
    q = np.linspace(0.0, 2 * math.pi, 41)
    rr = r * (1.0 + 0.035 * np.sin(2 * q + 1.3 * t + ph) + 0.022 * np.sin(3 * q - 0.9 * t + 2 * ph))
    P = np.stack([x + rr * np.cos(q), y + rr * np.sin(q) * (1.0 + 0.03 * math.sin(0.8 * t + ph))], axis=1)
    tint = (C.ROSE, C.SEA, C.LILAC, C.SKY_HI)[int(rnd(seed, 72) * 4) % 4] if day else C.MOON
    fill(F, P, tint, (0.16 if day else 0.07) * a, "glow")
    w = max(1.7, r * 0.045)
    _lines(F, [P], rim, w, 0.8 * a, "mid", seed, 0.0)
    # the sheen: a bright arc inside the rim up on one side, a dot beside it, and a faint answer below
    g0 = -2.35 + 0.12 * math.sin(0.7 * t + ph)
    _lines(F, [arc(x, y, r * 0.74, r * 0.74, g0 - 0.42, g0 + 0.34, 8)], hi, w * 1.5, 0.9 * a, "dense")
    _lines(F, [arc(x, y, r * 0.78, r * 0.78, g0 + 3.05, g0 + 3.5, 6)], hi, w, 0.4 * a, "mid")
    disc(F, x + r * 0.70 * math.cos(g0 + 0.62), y + r * 0.70 * math.sin(g0 + 0.62), max(1.2, r * 0.05), hi, 0.9 * a, None, floor=1.0)


# --------------------------------------------------------------------------
# the voice line
# --------------------------------------------------------------------------
def voice_line(F: Frame, x0, y0, x1, y1, w: float = 1.0, fall: float = 0.0, floor: float = FLOOR + 14.0, reach: float = 0.72,
               t: float | None = None, seed: int = 860, col=None, a: float = 1.0, lw: float = 3.0, dark: float = 0.0,
               amp: float = 1.0):
    """The child's voice: a thin wavering line that leaves the mouth (x0, y0) toward (x1, y1), does
    not get there, and drops.

    w: 0..1 how far it has come out (it stops at `reach` of the way: it falls short).
    fall: 0..1 it gives up: from its far end backward it sinks, and lies on the floor (world y =
    floor: by default a little in front of the ground line) as a limp line; at 1 it has let go of
    the mouth too.
    t: the clock of its wavering (default F.tb). dark: 0..1 the line turns dark (it is on its way to
    the scribble). amp: size of the waver. Returns the world point of its far end."""
    w = min(1.0, max(0.0, float(w)))
    if w <= 0.0 or a <= 0.003:
        return (x0, y0)
    t = F.tb if t is None else t
    fall = min(1.0, max(0.0, float(fall)))
    dx, dy = x1 - x0, y1 - y0
    D = math.hypot(dx, dy) + 1e-9
    ex, ey = dx / D, dy / D
    L = D * reach * (0.5 * w + 0.5 * ease(w))
    n = max(12, int(L / 2.6))
    s = np.linspace(0.0, L, n)
    q = s / max(L, 1e-9)
    ph = rnd(seed, 3) * 40.0
    # the waver: a slow wander and a fine tremble, both growing away from the mouth and dying at the far end
    env = np.minimum(1.0, s / 70.0) * (1.0 - 0.55 * q ** 2)
    # ... and what it is saying: bursts of a fine shiver that travel out along it and never arrive
    say = smooth((vn((s - 150.0 * t) / 58.0 + ph, seed + 2) - 0.42) / 0.22) * np.minimum(1.0, s / 40.0) * (1.0 - q ** 3)
    wv = amp * (env * (15.0 * (2 * vn(s / 96.0 - t * 0.55 + ph, seed) - 1) + 6.0 * (2 * vn(s / 31.0 - t * 1.5 + ph, seed + 1) - 1))
                + say * 6.5 * np.sin(s / 3.3))
    sag = 0.10 * L * q ** 2                                 # it never flew straight
    X = x0 + ex * s - ey * wv
    Y = y0 + ey * s + ex * wv + sag
    if fall > 0.0:
        k = smooth((fall * 1.45 - (1.0 - q)) / 0.45)        # the far end first, the mouth end last
        # on the floor it lies as a limp thread does: drawn together a little, in slack curls
        gx = x0 + ex * s * 0.90 + 16.0 * (2 * vn(s / 52.0 + ph, seed + 5) - 1)
        gy = floor + 1.0 + 8.0 * (2 * vn(s / 34.0 + ph, seed + 6) - 1) * np.minimum(1.0, q * 3.0)
        X = x0 + ex * s - ey * wv * (1.0 - k) + (gx - (x0 + ex * s)) * k          # what has fallen no longer speaks
        Y = y0 + ey * s + ex * wv * (1.0 - k) + sag
        Y = Y + (gy - Y) * k ** 1.7                         # it drops like something with a little weight
        Y = Y + 0.05 * L * np.sin(np.pi * k) ** 2 * (1.0 - fall)                  # ... and what is still in the air hangs in a belly
    c = F.pick(C.CHALK, C.PENCIL) if col is None else col
    if dark > 0.0:
        c = mix(c, C.GLOOM_EDGE, min(1.0, dark))
    P = np.stack([X, Y], axis=1)
    live = 1.0 - 0.35 * fall
    chalk(F, P, c, lw, a * live, seed, wob=0.0, taper=0.25, edge=0.3, step=2.5, grain="dense")
    if w < 1.0 and fall <= 0.0:
        disc(F, X[-1], Y[-1], lw * 0.8, mix(c, C.CHALK, 0.6), 0.95 * a, None, floor=1.3)
    return (float(X[-1]), float(Y[-1]))


# --------------------------------------------------------------------------
# the bare bulb and its moth
# --------------------------------------------------------------------------
def hanging_lamp(F: Frame, x, top, drop, lit: float = 1.0, floor: float = FLOOR, s: float = 1.0, swing: float = 0.0,
                 spread: float = 0.42, seed: int = 880, a: float = 1.0, t: float | None = None) -> dict:
    """A bare bulb on a cord: the cord hangs from the world point (x, top) and is `drop` long; under
    the bulb a cone of pale rubbed light falls to the ground (world y = floor) and lies there as a
    pool. The cone has no outline: it is strongest down its middle and dies away at its sides.

    lit: 0..1 the light. s: size of the bulb (1 = 30 units across). spread: half width of the cone
    at the ground, as a share of its height. swing: rad, a slow pendulum on t (default F.tb); keep it
    under 0.03 or leave it 0: the cone is a large area.
    Returns {"bulb": (x, y) its middle, "r": its radius, "pool": (x, floor), "half": the pool's half width}."""
    t = F.tb if t is None else t
    ang = swing * math.sin(t * 1.9 + rnd(seed, 1) * 6.0) if swing else 0.0
    sx, sy = x + math.sin(ang) * drop, top + math.cos(ang) * drop
    r = 15.0 * s
    bx, by = sx + math.sin(ang) * r * 1.75, sy + math.cos(ang) * r * 1.75
    line = F.pick(C.CHALK_DIM, C.PENCIL)
    pale = F.pick(C.MOON, C.SUN_HALO)
    lit = min(1.0, max(0.0, float(lit)))
    half = max(1.0, floor - by) * spread
    if lit > 0.0:
        k = lit * a
        # the mesh is wider than the cone: its sides have died away where the cone's edge would be
        _beam(F, bx, by + r * 0.2, r * 1.7, bx, floor, half * 1.3, pale, 0.28 * k, 0.17 * k, edge=1.35)
        _beam(F, bx, by + r * 0.2, r * 1.0, bx, floor, half * 0.62, pale, 0.10 * k, 0.03 * k, edge=1.0)      # its brighter heart
        smudge(F, bx, floor + 4.0, half * 0.92, max(8.0, half * 0.13), pale, 0.20 * k, "glow", additive=True, power=1.3)
        smudge(F, bx, by, r * 5.2, r * 5.2, pale, 0.36 * k, "glow", additive=True, power=2.2)
    chalk(F, A((x, top), ((x + sx) / 2 + 1.5 * s, (top + sy) / 2), (sx, sy)), line, 2.6 * s, 0.9 * a, seed, wob=0.7, taper=0.9, edge=0.2)
    ca, sa = math.cos(ang), math.sin(ang)

    def R(px, py):                                         # the fitting's own frame: down the cord
        return (sx + px * ca + py * sa, sy - px * sa + py * ca)

    sock = A(R(-0.46 * r, -0.2 * r), R(0.46 * r, -0.2 * r), R(0.52 * r, 0.74 * r), R(-0.52 * r, 0.74 * r), R(-0.46 * r, -0.2 * r))
    knock = C.KNOCK if not F.day else C.DAY
    fill(F, sock, knock, 0.95 * a)
    fill(F, sock, line, 0.55 * a, "mid")
    q = np.linspace(0.0, 2 * math.pi, 23)                  # a pear: narrow where it is screwed in, round below
    P = np.array([R(r * 1.04 * math.sin(v) * abs(math.sin(v / 2)) ** 0.55 * (1.0 + 0.03 * rsym(seed + i % 22, 4)), 1.75 * r - 1.22 * r * math.cos(v))
                  for i, v in enumerate(q)])
    fill(F, P, knock, 0.9 * a)
    fill(F, P, mix(F.pick(C.PAPER_HAZE, C.DAY_SHADE), F.pick(C.CHALK, C.SUN_CORE), lit), (0.5 + 0.45 * lit) * a, "dense")
    # the filament, as a child draws it: two posts and a little loop between them
    fil = A(R(-0.22 * r, 0.74 * r), R(-0.30 * r, 1.62 * r), R(-0.10 * r, 2.02 * r), R(0.0, 1.66 * r), R(0.10 * r, 2.02 * r), R(0.30 * r, 1.62 * r),
            R(0.22 * r, 0.74 * r))
    _lines(F, [fil], mix(line, F.pick(C.PAPER_HAZE, C.AMBER_DEEP), 0.5 * lit), 1.7 * s, (0.75 - 0.2 * lit) * a, "dense", floor=0.9)
    _lines(F, [sock, P], mix(line, F.pick(C.CHALK, C.PENCIL), 0.5 + 0.5 * lit), 2.4 * s, 0.95 * a, "dense", seed + 3, 0.3)
    return {"bulb": (bx, by), "r": r, "pool": (bx, floor), "half": half}


def moth_path(t: float, cx, cy, r: float = 80.0, seed: int = 0, come=None, fall=None, floor: float = FLOOR):
    """Where a moth circling the world point (cx, cy) is at time t (seconds; any clock, the film
    uses F.t): an unsteady orbit about r wide that keeps clear of the light, darts in at it now and
    then and is off again.

    come = (x0, y0, t0, t1): it sets out from the world point (x0, y0) at t0 (a mouth: the voice
    that leaves it) and has joined its orbit by t1; before t0 it is at (x0, y0).
    fall = (t0, t1): between these times it gives up circling and sinks, fluttering, to the world
    height `floor`, and lies there afterwards.
    Returns (x, y, heading in rad)."""
    p1, p2 = rnd(seed, 81) * 6.28, rnd(seed, 82) * 6.28
    w1 = 3.1

    def orbit(tt):
        ang = w1 * tt + 0.8 * math.sin(0.61 * w1 * tt + p1) + p2
        dart = max(0.0, math.sin(0.47 * w1 * tt + p2)) ** 8        # now and then straight at the light
        rad = r * (0.80 + 0.20 * math.sin(1.37 * w1 * tt + p1)) * (1.0 - 0.66 * dart)
        return (cx + rad * math.cos(ang) + 0.05 * r * math.sin(6.3 * w1 * tt),
                cy + 0.80 * rad * math.sin(ang) + 0.07 * r * math.sin(5.1 * w1 * tt + p1))

    def at(tt):
        if fall is not None and tt > fall[0]:
            g = min(1.0, (tt - fall[0]) / max(1e-6, fall[1] - fall[0]))
            x, y = orbit(fall[0] + (fall[1] - fall[0]) * 0.30 * (1.0 - (1.0 - g) ** 2))      # its circling runs down
            x += 0.22 * r * math.sin(11.0 * g + p1) * math.sin(math.pi * g) ** 0.7              # it flutters as it sinks
            y += (floor - 5.0 - y) * g ** 1.7
        else:
            x, y = orbit(tt)
        if come is not None:
            k = min(1.0, max(0.0, (tt - come[2]) / max(1e-6, come[3] - come[2])))
            if k < 1.0:
                e = k * k * (3.0 - 2.0 * k)
                bow = math.sin(math.pi * k) * 0.10 * math.hypot(cx - come[0], cy - come[1])
                x, y = come[0] + (x - come[0]) * e, come[1] + (y - come[1]) * e - bow        # it rises a little on the way
        return x, y

    x, y = at(t)
    x2, y2 = at(t + 0.02)
    if abs(x2 - x) + abs(y2 - y) < 1e-6:
        x2, y2 = x + 1.0, y
    return x, y, math.atan2(y2 - y, x2 - x)


_MOTH_BEAT = (1.0, 0.42, 0.0, 0.42)                # wings open, half, shut, half: one beat in four frames


def moth(F: Frame, x, y, heading: float = 0.0, s: float = 1.0, t: float | None = None, a: float = 1.0, beat: float = 1.0,
         seed: int = 0, col=None):
    """A moth at the world point (x, y), as a child draws one: a speck of a body and two small pale
    wings that open and shut on TRUE time (t, default F.t): one beat in four frames, three shapes.
    heading: where it is flying (rad). s = 1: 34 units across. beat: 0 = wings held open and still
    (settled); in between they only quiver."""
    if a <= 0.003:
        return
    t = F.t if t is None else t
    col = F.pick(C.CHALK, C.PENCIL) if col is None else col
    op = 1.0 - beat * (1.0 - _MOTH_BEAT[(int(math.floor(t * FPS + 1e-6)) + seed) % 4])      # 1 open .. 0 shut
    ex, ey = math.cos(heading), math.sin(heading)
    nx, ny = -ey, ex

    def P(u, v):
        return (x + s * (u * ex + v * nx), y + s * (u * ey + v * ny))

    Wg = 17.0 * (0.15 + 0.85 * op)
    wings = [A(P(3.4, 0.0), P(9.0, sg * Wg), P(3.5, sg * Wg * 1.02), P(-1.5, sg * Wg * 0.78), P(-7.5, sg * Wg * 0.80), P(-4.4, 0.0))
             for sg in (-1.0, 1.0)]
    for Q in wings:
        fill(F, Q, col, 0.92 * a, "dense")
    dim = mix(col, C.CHALK_DIM, 0.55) if not F.day else col
    _lines(F, wings, dim, 1.3 * s, 0.7 * a, "mid", floor=0.8, close=True)
    _lines(F, [A(P(-6.5, 0.0), P(6.0, 0.0))], dim, 3.4 * s, a, "dense", floor=1.3)
    disc(F, *P(7.0, 0.0), 2.3 * s, dim, a, None, floor=0.9)


def moth_trail(F: Frame, t: float, cx, cy, r: float = 80.0, seed: int = 0, dur: float = 0.9, a: float = 0.6, lw: float = 2.2, col=None,
               come=None, fall=None, floor: float = FLOOR):
    """The thin line a moth (see moth_path; r, seed, come, fall, floor are its) has drawn in the last
    `dur` seconds, thinning and fading toward its old end: the voice that circles the lamp.
    Returns the moth's (x, y, heading) at t, for moth."""
    n = max(8, int(dur * 44))
    pts = np.array([moth_path(t - dur * (1.0 - i / (n - 1.0)), cx, cy, r, seed, come, fall, floor)[:2] for i in range(n)])
    col = F.pick(C.CHALK_COOL, C.PENCIL) if col is None else col
    if float(np.abs(np.diff(pts, axis=0)).sum()) > 1.0:    # nothing while it has not moved
        m = (n - 1) // 4
        for j, k in enumerate((0.16, 0.36, 0.62, 1.0)):       # four overlapping lengths, the newest pressed hardest
            _lines(F, [pts[j * m:(n if j == 3 else (j + 1) * m + 1)]], col, lw * (0.55 + 0.15 * j), a * k, "mid", floor=0.9)
    return moth_path(t, cx, cy, r, seed, come, fall, floor)


# --------------------------------------------------------------------------
# the phone
# --------------------------------------------------------------------------
PHONE_LEN = 44.0                  # the slab's length at s = 1 (world units)
RING_TIMES = (251.41, 251.83, 252.37, 252.61, 252.87)       # the rings of the coda, on the song's clock


_RING_LIFE = 0.62                 # seconds a ring's marks live
_L1 = PHONE_LEN ** 0.25           # so that a ring's reach grows a little slower than the phone (L ** 0.75 * _L1 = L at s = 1)


def _ring_marks(F: Frame, x, y, rr: float, s: float, col, w: float, a: float, seed: int, inner: bool = True):
    """The marks a child draws round something that rings: a pair of brackets on each side of it,
    a little above the level (nothing below: the floor and the lyric band are there), rr from (x, y)."""
    if a <= 0.003:
        return
    small = []
    for side in (-1.0, 1.0):
        ac = -0.42 if side > 0 else math.pi + 0.42
        chalk(F, arc(x, y, rr, rr * 0.78, ac - 0.62, ac + 0.62, 10), col, w, a, seed + int(side), wob=0.5, taper=0.4, edge=0.25)
        small.append(arc(x, y, rr * 0.74, rr * 0.58, ac - 0.46, ac + 0.46, 8))
    if inner:
        _lines(F, small, col, w * 0.72, 0.75 * a, "dense", seed + 2, 0.4, floor=1.4)


def phone(F: Frame, x, y, s: float = 1.0, lit: float = 0.0, seed: int = 480, ring: float = 0.0, col=None, draw: float = 1.0,
          warm: float = 0.0, rot: float = -0.07, lie: float = 1.0, scroll: float = 0.0, bars: float = 1.0, down: bool = False,
          rings=(), halo: float = 1.0, a: float = 1.0) -> dict:
    """The phone: a small dark slab, centred on the world point (x, y), PHONE_LEN * s long.

    lie: 1 = lying on the floor, seen at a slant (the default); 0 = held up, its face to us.
    rot: the angle of its long axis (rad; -1.57 = upright). down: face down (or seen from the back).
    lit: 0..1 the screen. warm: 0 = a pale cold screen, 1 = amber (the call).
    bars, scroll: on a lit screen, rows of empty scribbled lines (bars = their pressure); scroll moves
    them along the phone, in rows (drive it with the thumb's flicks; it may be any number).
    ring: 0..1 steady ring marks about it. rings: times of the song at which a ring leaves it (pass
    RING_TIMES): each is an arc that widens and fades over 0.6 s, and the slab rattles.
    draw: 0..1 it is still being drawn. halo: the small glow of the screen itself (0 for none).
    Returns {"light": the world point the light comes from, "a": its strength 0..1, "col": its
    colour, "c": the slab's middle, "rot": its angle}: the glow on a face is the scene's to add."""
    if draw <= 0.0 or a <= 0.003:
        return {"light": (x, y), "a": 0.0, "col": C.MOON, "c": (x, y), "rot": rot}
    night = not F.day
    line = (F.pick(C.CHALK_COOL, C.PENCIL) if col is None else col)
    lit = min(1.0, max(0.0, float(lit)))
    warm = min(1.0, max(0.0, float(warm)))
    glowc = mix(C.MOON, C.AMBER_GLOW, warm)
    scr = mix(mix(C.MOON, C.CHALK, 0.55), C.AMBER_PALE if night else mix(C.AMBER_PALE, C.AMBER, 0.5), warm)
    # the ring: arcs leaving it, and the rattle
    live = [(j, F.t - tr) for j, tr in enumerate(rings) if 0.0 <= F.t - tr < _RING_LIFE]
    if live:
        k = max(math.exp(-ag / 0.16) for _, ag in live)
        tick = 1.0 if int(F.t * FPS + 1e-6) % 2 else -1.0
        hop = max(math.sin(math.pi * min(1.0, ag / 0.2)) for _, ag in live)    # each ring makes it jump
        rot = rot + 0.08 * k * tick
        x, y = x + 1.4 * s * k * tick, y - (1.0 * k + 3.2 * hop * lie) * s
    L, B = PHONE_LEN * s, 23.0 * s
    sq, sh = 1.0 - 0.50 * lie, 0.40 * lie
    cr, sr = math.cos(rot), math.sin(rot)

    def T(P):
        P = np.asarray(P, dtype=np.float64)
        u, v = P[:, 0] + P[:, 1] * sh, P[:, 1] * sq
        return np.stack([x + u * cr - v * sr, y + u * sr + v * cr], axis=1)

    rad = 4.6 * s
    q = np.linspace(0.0, math.pi / 2, 4)
    body = np.vstack([np.stack([cx_ + rad * np.cos(q + a0), cy_ + rad * np.sin(q + a0)], axis=1)
                      for cx_, cy_, a0 in ((L / 2 - rad, -B / 2 + rad, -math.pi / 2), (L / 2 - rad, B / 2 - rad, 0.0),
                                           (-L / 2 + rad, B / 2 - rad, math.pi / 2), (-L / 2 + rad, -B / 2 + rad, math.pi))])
    body = T(np.vstack([body, body[:1]]))
    face = T(A((-L / 2 + 3.4 * s, -B / 2 + 3.0 * s), (L / 2 - 5.2 * s, -B / 2 + 3.0 * s), (L / 2 - 5.2 * s, B / 2 - 3.0 * s),
               (-L / 2 + 3.4 * s, B / 2 - 3.0 * s), (-L / 2 + 3.4 * s, -B / 2 + 3.0 * s)))
    lx, ly = float(face[:4, 0].mean()), float(face[:4, 1].mean())
    k_on = 0.0 if down else lit
    if k_on > 0.0 and halo > 0.0:
        if night:
            smudge(F, lx, ly - 2.0 * s * lie, L * 2.1, L * (2.1 - 0.9 * lie), glowc, 0.42 * k_on * halo * a, "glow", additive=True, power=2.0)
        else:                                              # on warm paper light is pigment: a rubbed patch of its colour
            smudge(F, lx, ly - 2.0 * s * lie, L * 2.3, L * (2.3 - 0.9 * lie), mix(C.CREAM, C.SUN_HALO, warm), (0.35 + 0.25 * warm) * k_on * halo * a,
                   "soft", power=1.5)
            if warm > 0.0:                                 # a pale heart: lighter than whatever it lies on
                smudge(F, lx, ly - 2.0 * s * lie, L * 1.5, L * (1.5 - 0.62 * lie), C.SUN_CORE, 0.8 * warm * k_on * halo * a, "glow", power=1.2)
    if lie > 0.5 and night:
        smudge(F, x + 2.0 * s, y + B * 0.30, L * 0.62, B * 0.22, C.PAPER_DEEP, 0.7 * a * draw, "soft")      # it lies on something
    dark = (0.075, 0.085, 0.14) if night else (0.26, 0.24, 0.30)
    fill(F, body, dark, 0.96 * a * draw)
    if not down:
        if k_on < 1.0:                                     # the dark glass, and the bit of the room's light it catches
            fill(F, face, mix(dark, C.CHALK_FAR, 0.5) if night else (0.36, 0.34, 0.42), 0.55 * a * draw * (1.0 - k_on), "mid")
            _lines(F, [T(A((L * 0.10, -B * 0.30), (L * 0.30, B * 0.24))), T(A((L * 0.22, -B * 0.30), (L * 0.34, B * 0.02)))],
                   C.CHALK_BLUE if night else C.CREAM, 2.2 * s ** 0.7, 0.6 * a * draw * (1.0 - k_on), "mid", floor=1.0)
        if k_on > 0.0:
            fill(F, face, scr, 0.94 * k_on * a, "dense")
            if bars > 0.0:
                pitch = 5.4 * s
                u0, u1 = -L / 2 + 3.4 * s, L / 2 - 5.2 * s
                nrow = int((u1 - u0) / pitch) + 2
                base = math.floor(scroll)
                rows = []
                for j in range(-1, nrow):
                    idx = j - base
                    u = u1 - (j + (scroll - base)) * pitch - pitch * 0.5        # rows run from the top end down
                    ln = (0.36 + 0.5 * rnd(idx, 91)) * (B - 9.0 * s)
                    v0 = -B / 2 + 4.6 * s
                    rows.append(T(A((u, v0), (u + 0.5 * s * rsym(idx, 92), v0 + ln * 0.5), (u, v0 + ln))))
                with F.clip(face):
                    _lines(F, rows, mix(scr, C.CHALK_DIM if warm < 0.5 else C.AMBER_DEEP, 0.72), 2.0 * s, 0.8 * k_on * bars * a, "mid",
                           floor=0.9)
    else:
        cam = T(A((L / 2 - 8.0 * s, -B / 2 + 6.0 * s)))[0]
        disc(F, cam[0], cam[1], 2.0 * s * (0.6 + 0.4 * sq), mix(dark, line, 0.6), 0.9 * a * draw, None, floor=0.8)
    rim = mix(line, C.AMBER, warm * lit) if night else mix(line, C.AMBER_DEEP, 0.55 * warm * lit)
    chalk(F, np.vstack([body, body[1:3]]), rim, 2.6 * s ** 0.6, 0.95 * a, seed, wob=0.35 * min(1.5, max(0.4, s)), taper=0.7, draw=draw,
          step=4.0)
    # ring marks: steady (ring) and the pulses (rings)
    rc, rw = (C.AMBER, 3.6 * s ** 0.8) if night else (C.AMBER_DEEP, 4.6 * s ** 0.8)
    if ring > 0.0:
        _ring_marks(F, x, y - 3.0 * s, L * 1.25, s, rc, rw * 0.9, ring * a, seed + 3)
        _ring_marks(F, x, y - 3.0 * s, L * 1.95, s, rc, rw * 0.8, 0.6 * ring * a, seed + 5, inner=False)
    for j, ag in live:                                     # each ring: brackets that widen and fade
        u = ag / _RING_LIFE
        al = (1.0 - u) ** 0.8 * min(1.0, ag * FPS / 2.0)
        _ring_marks(F, x, y - 3.0 * s, 0.72 * L + 2.2 * L ** 0.75 * _L1 * ease_out(u, 2.2), s, rc, rw * (1.0 - 0.3 * u), al * a, seed + 7 + 4 * (j % 8))
    return {"light": (lx, ly), "a": k_on, "col": glowc, "c": (x, y), "rot": rot}


def phone_held(F: Frame, hand, ang: float = -1.25, s: float = 1.0, lit: float = 0.0, warm: float = 0.0, back: bool = False,
               scroll: float = 0.0, **kw) -> dict:
    """The phone in a hand: held at the world point `hand` by its lower third, its long axis at
    `ang` (rad; -1.57 = upright, its top up). back=True: seen from behind (at the ear). The other
    arguments and the return value are phone's."""
    L = PHONE_LEN * s
    back = bool(kw.pop("down", False)) or back
    kw.pop("lie", None)
    kw.pop("rot", None)
    return phone(F, hand[0] + 0.20 * L * math.cos(ang), hand[1] + 0.20 * L * math.sin(ang), s, lit, warm=warm, rot=ang, lie=0.0,
                 scroll=scroll, down=back, **kw)


# --------------------------------------------------------------------------
# crows (before colour) and birds (after it)
# --------------------------------------------------------------------------
_CROW_DARK = (0.075, 0.085, 0.14)                 # almost black, but not the scribble's black
_CROW_LINE = (0.47, 0.54, 0.73)
_PASTELS = ("CORAL", "MUSTARD", "LILAC", "SEA", "ROSE", "SKY_HI")
def _wing_shape():
    """A wing as a child draws one, unit length along x from the shoulder (0, 0), the trailing edge
    toward +y: a rounded blade whose trailing edge ends in three soft feather tips."""
    lead = [(0.0, 0.0), (0.20, -0.10), (0.48, -0.15), (0.78, -0.10), (0.96, -0.02), (1.0, 0.05)]
    trail = []
    for u0, u1, dep in ((0.98, 0.76, 0.15), (0.76, 0.54, 0.25), (0.54, 0.30, 0.31)):       # three scallops, tip to root
        for k in (0.25, 0.6, 0.9):
            u = u0 + (u1 - u0) * k
            trail.append((u, dep * (0.62 + 0.38 * math.sin(math.pi * k)) + 0.02))
        trail.append((u1 + 0.015, dep * 0.60))
    return np.array(lead + trail + [(0.16, 0.25), (0.0, 0.20)])


_WING = _wing_shape()


def swing(age: float, freq: float = 2.4, tau: float = 0.45) -> float:
    """A damped swing for whatever a bird lands on: 0 before, -1 at the moment of landing (age = 0),
    then swinging out. Multiply by the dip in world units and add it to the wire."""
    if age < 0.0:
        return 0.0
    return -math.cos(2 * math.pi * freq * age) * math.exp(-age / tau)


def _bird_cols(F: Frame, seed: int, col, day):
    day = F.day if day is None else day
    if day:
        body = getattr(C, _PASTELS[int(rnd(seed, 95) * len(_PASTELS)) % len(_PASTELS)]) if col is None else col
        return body, mix(C.PENCIL, body, 0.25), C.MUSTARD, C.PENCIL, C.DAY, True
    return _CROW_DARK, (_CROW_LINE if col is None else col), (0.50, 0.56, 0.72), C.CHALK, C.KNOCK, False


def _bird(F: Frame, bx, by, s, face, seed, a, cols, pitch=0.35, hunch=0.0, look=1.0, wing=None, feet=None, tail=1.0, boil=True):
    """The one bird of the film. (bx, by): the middle of its body. pitch: how far the body is reared
    up (rad: 0 flying level, 0.4 perched, more when it brakes). look: +1 beak forward .. -1 turned
    back. wing: None folded, or (angle of the near wing, angle of the far one, spread 0..1); an
    angle is measured up from the body's backward axis (1.57 = straight up, negative = down).
    feet: world point the legs reach down to (perched), or None. Returns the head's world point."""
    body_c, line, beak_c, eye_c, knock, day = cols
    f = float(face)
    px = s * F.cam.zoom                                    # screen px per unit of bird
    cp, sp = math.cos(pitch), math.sin(pitch)

    def Bd(u, v):                                          # body frame (u toward the head, v down) -> world
        return (bx + f * s * (u * cp + v * sp), by + s * (-u * sp + v * cp))

    fat = 1.0 + 0.20 * hunch
    q = np.linspace(0.0, 2 * math.pi, 25)[:-1]
    rr = 1.0 + 0.045 * (2 * vn(np.arange(24) * 0.45, seed * 7) - 1)
    body = np.array([Bd(27.0 * math.cos(v) * r_ - 2.0, 15.5 * fat * math.sin(v) * r_ * (1.0 + 0.16 * math.cos(v))) for v, r_ in zip(q, rr)])
    # the head rides in front of and above the body, and sinks into it when the bird hunches
    hx_, hy_ = Bd(21.0 - 6.0 * hunch, -5.0)
    hy_ -= s * (10.5 - 7.0 * hunch) * (0.55 + 0.45 * cp)
    hx_ -= f * s * 2.5 * (1.0 - look) * 0.5
    hr = 10.6 * s
    head = np.stack([hx_ + hr * np.cos(q[::2]) * 1.05 * rr[::2], hy_ + hr * np.sin(q[::2]) * 0.94], axis=1)
    tailP = A(Bd(-20.0, -6.0), Bd(-27.0 - 25.0 * tail, -1.0 + 2.0 * tail), Bd(-26.0 - 22.0 * tail, 7.0 + 3.0 * tail), Bd(-19.0, 7.5))
    wn = wf = None
    if wing is not None and wing[2] > 0.24:               # a wing shorter than that is behind the body
        an, af, spr = wing
        Lw = 54.0 * (0.34 + 0.66 * spr)
        for ang_, k_, sh in ((af, 0.84, (5.0, -8.0)), (an, 1.0, (8.0, -3.0))):
            ax, ay = -math.cos(ang_), -math.sin(ang_)       # along the wing, in the body frame
            cx_, cy_ = -math.sin(ang_), math.cos(ang_)      # across it, toward the trailing edge
            W = _WING * (Lw * k_, Lw * k_ * (0.62 + 0.38 * spr))
            P = np.array([Bd(sh[0] + w0 * ax + w1 * cx_, sh[1] + w0 * ay + w1 * cy_) for w0, w1 in W])
            if k_ < 1.0:
                wf = P
            else:
                wn = P
    lw = 2.5 * s
    wob = 0.3 * min(1.4, max(0.3, s)) if (boil and px * 70.0 > 26.0) else 0.0

    def mass(polys, c_, sd):
        # the pale line first, twice as wide; the dark shape then covers its inner half and every
        # line inside the bird, so that only the outline of the whole bird is left
        _lines(F, polys, line, lw * 2.0, 0.92 * a, "dense", sd, wob, floor=2.7, close=True)
        for P in polys:
            if day:
                fill(F, P, knock, 0.95 * a)
            fill(F, P, c_, 0.97 * a if not day else 0.9 * a, None if not day else "dense")

    mass(([wf] if wf is not None else []) + [tailP, body, head], body_c, seed)
    if wn is not None:
        mass([wn], body_c if not day else mix(body_c, C.PENCIL, 0.16), seed + 5)
    elif wing is None and px > 0.45:
        # the folded wing: one curved line along the flank
        _lines(F, [A(Bd(11.0, -7.0), Bd(-3.0, 4.0 * fat), Bd(-21.0, 1.5))], line, lw * 0.8, 0.6 * a, "dense", seed + 6, 0.0, floor=1.0)
    # beak: heavy; it shortens as the head turns toward us and points the other way when turned back
    lk = max(-1.0, min(1.0, look))
    bl = 17.0 * s * (0.22 + 0.78 * abs(lk)) * (0.62 if day else 1.0)
    bd = f * (1.0 if lk >= 0 else -1.0)
    bxs = hx_ + bd * hr * (0.78 if abs(lk) > 0.3 else 0.25)
    dp = (0.62 if day else 1.0) * s
    bk = A((bxs, hy_ - 4.0 * dp), (bxs + bd * bl * 0.55, hy_ - 2.2 * dp), (bxs + bd * bl, hy_ + 2.6 * dp), (bxs, hy_ + 4.4 * dp))
    fill(F, bk, beak_c, 0.96 * a, "dense")
    _lines(F, [bk[:3], bk[2:]], line if not day else C.PENCIL, lw * 0.7, 0.9 * a, "dense", floor=1.0)
    if px > 0.40:
        disc(F, hx_ + bd * hr * 0.30 * abs(lk), hy_ - 1.8 * s, 1.7 * s, eye_c, 0.95 * a, None, floor=1.0)
    if feet is not None:
        lg = []
        for dx in (-3.5, 5.5):
            p0 = Bd(dx - 4.0, 13.5 * fat)
            p1 = (feet[0] + f * dx * s, feet[1] + 0.5 * s)
            lg += [A(p0, p1), A((p1[0] - f * 2.5 * s, p1[1]), (p1[0] + f * 3.5 * s, p1[1] + 0.6 * s))]
        _lines(F, lg, line, lw * 0.75, 0.9 * a, "dense", floor=1.0)
    return hx_, hy_


def _crow_idle(seed: int, t: float):
    """What a perched crow is doing at boil-clock time t: (look, bob, sidle, ruffle). Now and then it
    turns its head and holds it there, shifts its feet, or shakes the rain off."""
    per = 3.4 + 2.6 * rnd(seed, 101)
    u = t / per + rnd(seed, 102)
    n = math.floor(u)
    u -= n
    kind = int(rnd(seed * 31 + n, 103) * 5)                # 0, 1: turn the head; 2: shift; 3: ruffle; 4: nothing
    look, bob, sidle, ruf = 1.0, 0.0, 0.0, 0.0
    if kind in (0, 1):
        hold = 0.25 + 0.3 * rnd(seed * 31 + n, 104)
        look = 1.0 - 2.0 * (ramp(u, 0.10, 0.10 + 0.14 / per) - ramp(u, 0.10 + hold, 0.10 + hold + 0.14 / per))
    elif kind == 2:
        w_ = seg(u, 0.3, 0.3 + 0.5 / per)
        bob = math.sin(math.pi * w_) * abs(math.sin(2 * math.pi * w_))
        sidle = (1.0 if rnd(seed * 31 + n, 105) > 0.5 else -1.0) * math.sin(math.pi * w_)
    elif kind == 3:
        w_ = seg(u, 0.4, 0.4 + 0.6 / per)
        ruf = math.sin(math.pi * w_)
    return look, bob, sidle, ruf


def crow(F: Frame, x, y, s: float = 1.0, seed: int = 500, face: int = 1, a: float = 1.0, hunch: float = 0.0, col=None,
         day: bool | None = None, look: float | None = None, t: float | None = None, idle: float = 1.0):
    """A crow perched on the world point (x, y) (its feet): an almost black rubbed body with a pale
    outline, beak, tail, legs. s = 1: about 70 units from beak to tail (on the wire the film uses
    0.5 to 0.62). hunch: 0 upright .. 1 sunk into its shoulders. look: +1 beak forward .. -1 head
    turned back; None = it lives by itself on t (default F.tb): now and then it turns its head,
    shifts its feet or shakes itself (idle scales how much; 0 = stock-still).
    In the day skin (day, default F.skin) it is simply a bird: a small pastel one (col, default by seed).
    Returns the world point of its head."""
    if a <= 0.003:
        return (x, y)
    t = F.tb if t is None else t
    lk, bob, sidle, ruf = _crow_idle(seed, t) if idle > 0.0 else (1.0, 0.0, 0.0, 0.0)
    if look is not None:
        lk = look
    cols = _bird_cols(F, seed, col, day)
    hn = hunch + 0.35 * ruf * idle - 0.25 * bob * idle
    if cols[5]:
        hn = hn * 0.4
    px = x + 2.2 * s * sidle * idle
    return _bird(F, px - 4.0 * s * face, y - (24.0 - 2.0 * hn + 2.6 * bob * idle) * s, s, face, seed, a, cols, pitch=0.42 - 0.14 * hn,
                 hunch=hn, look=lk, feet=(px, y), tail=1.0 if not cols[5] else 0.6)


def crow_land(F: Frame, x, y, s: float = 1.0, seed: int = 500, face: int = 1, u: float = 1.0, a: float = 1.0, hunch: float = 0.0,
              col=None, day: bool | None = None, come=(-64.0, -46.0)):
    """A crow landing on the world point (x, y). u: 0..1 the landing (give it 6 to 8 frames: a short
    glide in from `come` (units of s, mirrored by face: it arrives from behind and above), wings
    spread and braking; from 0.55 its feet are on, the wings fold in two beats and the body dips and
    settles). u <= 0: nothing is drawn; u >= 1: the perched crow (crow, with hunch).
    Returns the world point of its feet (they reach the perch at u = 0.55)."""
    if u <= 0.0 or a <= 0.003:
        return (x + come[0] * s * face, y + come[1] * s)
    if u >= 1.0:
        crow(F, x, y, s, seed, face, a, hunch, col, day)
        return (x, y)
    cols = _bird_cols(F, seed, col, day)
    g = ease_out(min(1.0, u / 0.55), 2.2)                  # the glide: fast, then braking
    fx, fy = x + come[0] * s * face * (1.0 - g), y + come[1] * s * (1.0 - g) ** 1.5
    w_ = seg(u, 0.55, 1.0)                                 # the settling
    dip = 4.0 * s * math.sin(math.pi * min(1.0, w_ * 1.25)) * (1.0 - 0.5 * w_)
    pitch = 0.42 + 0.45 * (1.0 - w_) * (0.4 + 0.6 * g)       # reared back to brake
    spread = 1.0 - ease(seg(w_, 0.05, 0.9))
    flap = math.cos(2 * math.pi * (u * 2.2))                # two beats over the landing
    near, far = 1.25 + 0.40 * flap * (0.4 + 0.6 * spread) - 0.9 * (1.0 - spread), 1.50 + 0.32 * flap - 0.9 * (1.0 - spread)
    _bird(F, fx - 4.0 * s * face, fy - 24.0 * s + dip, s, face, seed, a, cols, pitch=pitch, hunch=0.0, look=1.0,
          wing=(near, far, spread), feet=(fx, fy + (0.0 if u >= 0.55 else 3.0 * s)), tail=1.0 + 0.3 * spread, boil=False)
    return (fx, fy)


def bird(F: Frame, x, y, s: float = 1.0, flap: float = 0.0, face: int = 1, seed: int = 0, col=None, a: float = 1.0,
         climb: float = 0.0, day: bool | None = None, glide: float = 0.0):
    """A bird flying, its body's middle on the world point (x, y). s = 1: about 70 units long, wings
    50. flap: its wing beat in cycles (drive it with true time: 3.5 * F.t for a small bird); glide:
    0..1 holds the wings out instead. climb: rad, how steeply it is climbing (+) or sinking (-).
    Night skin: a crow, dark with a pale outline; day skin: a small pastel bird (col, default by
    seed). Under about 16 px of wing on screen it is drawn as a child draws a far bird: two strokes."""
    if a <= 0.003:
        return
    cols = _bird_cols(F, seed, col, day)
    ph = 2 * math.pi * flap
    beat = math.cos(ph) * (1.0 - glide) + 0.25 * glide       # +1 wings up .. -1 down
    px = 50.0 * s * F.cam.zoom
    yb = y + 3.0 * s * math.sin(ph) * (1.0 - glide)          # the body rides up on the down stroke
    if px < 16.0:
        k = 26.0 * s
        up = 0.15 + 0.5 * (beat + 1.0)
        wl = A((x - face * k * 0.1 - k * 0.95, yb - k * up * 0.9), (x - k * 0.45, yb - k * up * 0.75 - k * 0.12), (x, yb))
        wr = A((x, yb), (x + k * 0.45, yb - k * up * 0.75 - k * 0.12), (x - face * k * 0.1 + k * 0.95, yb - k * up * 0.9))
        _lines(F, [np.vstack([wl, wr[1:]])], cols[1] if not cols[5] else mix(cols[0], C.PENCIL, 0.55), 3.0 * s, a, "dense", floor=1.3)
        return
    # from the side a wing is a blade that stands up, shortens to a stub as it passes the body, and hangs down
    near, far = math.atan2(beat, 0.40), math.atan2(beat + 0.18, 0.34)
    _bird(F, x, yb, s, face, seed, a, cols, pitch=0.10 + climb, hunch=0.0, look=1.0, wing=(near, far, 0.32 + 0.68 * abs(beat) ** 0.8),
          feet=None, tail=1.1 if not cols[5] else 0.8, boil=False)


def crow_fly(F: Frame, x, y, s: float = 1.0, seed: int = 500, face: int = 1, u: float = 0.0, a: float = 1.0, to=(150.0, -210.0),
             col=None, day: bool | None = None, beats: float = 5.0, hunch: float = 0.5):
    """A crow leaving its perch at the world point (x, y). u: 0..1 the flight: it crouches (to 0.12),
    throws its wings open and is off along a rising curve to (x, y) + to (world units; mirrored by
    face), beating its wings `beats` times on the way. u <= 0: perched (with `hunch`, as it sat);
    u >= 1: nothing (it is gone: let `to` end outside the frame, or fade it with a).
    Returns its world position."""
    if u <= 0.0:
        crow(F, x, y, s, seed, face, a, hunch, col, day)
        return (x, y)
    if u >= 1.0 or a <= 0.003:
        return (x + to[0] * face, y + to[1])
    if u < 0.12:
        cols = _bird_cols(F, seed, col, day)
        k = u / 0.12
        hn = (hunch if not cols[5] else 0.4 * hunch) + 0.3 * k
        _bird(F, x - 4.0 * s * face, y - (24.0 - 2.0 * hn + 3.0 * k) * s, s, face, seed, a, cols, pitch=0.42 - 0.14 * hn - 0.1 * k, hunch=hn,
              feet=(x, y), wing=(0.5, 0.7, 0.3 * k), tail=1.0 if not cols[5] else 0.6, boil=False)
        return (x, y)
    g = (u - 0.12) / 0.88
    e = g * g * (0.6 + 0.4 * g)                             # it gathers speed
    px, py = x + to[0] * face * e, y - 24.0 * s + (to[1] + 24.0 * s) * (1.0 - (1.0 - g) ** 1.8)
    bird(F, px, py, s, 0.5 + beats * g ** 0.8, face, seed, col, a, climb=0.55 * (1.0 - g) + 0.1, day=day)
    return (px, py)


def flock(F: Frame, x, y, t: float, n: int = 7, s: float = 0.5, vel=(95.0, -8.0), seed: int = 0, cols=None, a: float = 1.0,
          rate: float = 3.4, day: bool | None = None):
    """A small flock (5 to 9) crossing the sky. (x, y): where its leader is at t = 0; it travels
    vel world units a second, in a loose skein that breathes; every bird beats its own wings (on t:
    pass true time since it set out) and rests them in a short glide now and then.
    s: size of a bird (bird). cols: their colours in the day skin (default: pastels by seed).
    Returns the leader's world position."""
    face = 1 if vel[0] >= 0 else -1
    lx = x + vel[0] * t
    ly = y + vel[1] * t + 14.0 * s * math.sin(0.45 * t + rnd(seed, 111) * 6.0)
    climb = -math.atan2(vel[1], abs(vel[0])) * 0.6
    for i in range(int(n) - 1, -1, -1):
        row = (i + 1) // 2
        side = 1.0 if i % 2 else -1.0
        ox = -face * row * 104.0 * s * (1.0 + 0.25 * rsym(seed + i, 112)) + 12.0 * s * math.sin(0.7 * t + i * 1.9)
        oy = side * row * 50.0 * s * (1.0 + 0.3 * rsym(seed + i, 113)) + 9.0 * s * math.sin(0.9 * t + i * 2.3)
        r_i = rate * (0.9 + 0.2 * rnd(seed + i, 114))
        cyc = t * 0.42 + rnd(seed + i, 115)                    # now and then a glide
        gl = ramp(cyc % 1.0, 0.70, 0.76) - ramp(cyc % 1.0, 0.92, 0.98)
        c_ = cols[i % len(cols)] if cols else None
        bird(F, lx + ox, ly + oy, s * (0.9 + 0.2 * rnd(seed + i, 116)), t * r_i + rnd(seed + i, 117), face, seed * 13 + i, c_, a,
             climb=climb, day=day, glide=gl)
    return (lx, ly)


# --------------------------------------------------------------------------
# the chalk stub, the lines it goes over again, the string
# --------------------------------------------------------------------------
STUB_LEN = 26.0


def stub_grip(tip, ang: float, s: float = 1.0):
    """Where the fingers hold a chalk stub whose drawing end is on the world point `tip` and whose
    body points away along `ang` (rad): the world point for the hand."""
    return (tip[0] + math.cos(ang) * STUB_LEN * 0.6 * s, tip[1] + math.sin(ang) * STUB_LEN * 0.6 * s)


def chalk_stub(F: Frame, tip, ang: float = -0.9, s: float = 1.0, a: float = 1.0, dust: float = 0.0, seed: int = 930, t: float | None = None):
    """A stub of white chalk: its drawing end on the world point `tip`, its body pointing away from
    there along `ang` (rad; the hand is at stub_grip(tip, ang, s)). s = 1: 26 units long.
    dust: 0..1 crumbs of chalk falling from the tip while it presses (on t, default F.tb).
    Returns the grip point."""
    t = F.tb if t is None else t
    ca, sa = math.cos(ang), math.sin(ang)
    L, B = STUB_LEN * s, 9.5 * s

    def P(u, v):
        return (tip[0] + u * ca - v * sa, tip[1] + u * sa + v * ca)

    body = A(P(0.0, -B * 0.18), P(L * 0.16, -B * 0.5), P(L * 0.96, -B * 0.46), P(L, -B * 0.2), P(L * 0.99, B * 0.42), P(L * 0.9, B * 0.5),
             P(L * 0.10, B * 0.5), P(0.0, B * 0.22), P(0.0, -B * 0.18))
    col = F.pick(C.CHALK, C.CREAM)
    fill(F, body, F.pick(C.KNOCK, C.DAY), 0.9 * a)
    fill(F, body, col, 0.95 * a, "dense")
    _lines(F, [body], F.pick(C.CHALK_COOL, C.PENCIL), 1.8 * s, 0.8 * a, "dense", seed, 0.2, floor=1.0)
    _lines(F, [A(P(L * 0.3, B * 0.16), P(L * 0.85, B * 0.2))], F.pick(C.CHALK_BLUE, C.DAY_SHADE), 1.6 * s, 0.55 * a, "mid", floor=0.9)
    if dust > 0.0:
        i = np.arange(7)
        age = (htab(i, 7, seed) + t * (0.9 + 0.6 * htab(i, 11, seed + 1))) % 1.0
        xs = tip[0] + (htab(i, 13, seed + 2) - 0.5) * 16.0 * s + 5.0 * s * age
        ys = tip[1] + 4.0 * s + 44.0 * s * age ** 1.5
        for x_, y_, g_ in zip(xs, ys, age):
            disc(F, x_, y_, 1.5 * s, col, 0.8 * a * dust * (1.0 - g_), "dense", floor=0.9)
    return stub_grip(tip, ang, s)


def restroke(F: Frame, P, d: float = 1.0, w: float = 5.0, col=None, seed: int = 940, a: float = 1.0, piece: float = 30.0):
    """Going over a line again with the chalk: the world polyline P is redrawn as short strokes that
    overlap (each about `piece` long, none quite on top of the last), one after another as d goes
    0..1, the newest one being drawn. Brighter and rougher than the line it mends.
    Returns (x, y, ang): the chalk's tip and the direction it is moving in (for chalk_stub and the hand)."""
    P = np.asarray(P, dtype=np.float64)
    u = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])
    L = float(u[-1])
    col = F.pick(C.CHALK, C.PENCIL) if col is None else col

    def at(q):
        return np.array([np.interp(q, u, P[:, 0]), np.interp(q, u, P[:, 1])])

    n = max(1, int(round(L / (piece * 0.72))))
    d = min(1.0, max(0.0, float(d)))
    tip, ang = at(0.0), math.atan2(P[1, 1] - P[0, 1], P[1, 0] - P[0, 0])
    for i in range(n):
        p = min(1.0, max(0.0, d * n - i))
        if p <= 0.0:
            break
        q0 = max(0.0, L * i / n - piece * 0.14)
        q1 = min(L, L * (i + 1) / n + piece * 0.14)
        m = max(3, int((q1 - q0) / 8.0) + 2)
        Q = np.array([at(q) for q in np.linspace(q0, q1, m)])
        tn = Q[-1] - Q[0]
        tl = float(math.hypot(*tn)) + 1e-9
        nr = np.array([-tn[1], tn[0]]) / tl
        sg = 1.0 if i % 2 else -1.0                         # each stroke lies a little across the last one
        off = np.linspace(0.45 * rsym(seed + i, 1) - 0.42 * sg, 0.45 * rsym(seed + i, 2) + 0.42 * sg, m)[:, None] * w
        Q = Q + nr * off
        tp = chalk(F, Q, col, w * (0.9 + 0.3 * rnd(seed + i, 3)), a * (0.82 + 0.18 * p), seed + i * 3, wob=0.5, taper=0.35, edge=0.4,
                   draw=p, step=4.0, lead=0.0 if p >= 1.0 else 10.0 * w)
        if tp is not None:
            tip, ang = np.asarray(tp), math.atan2(tn[1], tn[0])
    return (float(tip[0]), float(tip[1]), ang)


def string(F: Frame, hand, end, slack: float = 0.25, t: float | None = None, col=None, w: float = 2.4, a: float = 0.9,
           seed: int = 771, knot: float = 0.0, sway: float = 1.0):
    """The string of the small tangle, from the world point `hand` (or whatever it is tied to) to
    the world point `end` (where the tangle hangs on it).

    slack: 0 = taut, a straight line; 1 = very loose: it bellies downward and its waves are larger.
    t: the clock of its slow wave (default F.tb); sway scales the wave. knot: 0..1 a small bow drawn
    at the hand end (tied to the armrest). Returns its world points (N, 2), hand first."""
    t = F.tb if t is None else t
    p0, p1 = np.asarray(hand, dtype=np.float64), np.asarray(end, dtype=np.float64)
    v = p1 - p0
    L = float(math.hypot(*v)) + 1e-9
    e = v / L
    nr = np.array([-e[1], e[0]])
    if nr[1] < 0:
        nr = -nr                                           # the side that looks down
    n = 18
    q = np.linspace(0.0, 1.0, n)
    belly = np.sin(np.pi * q) ** 0.9 * (1.0 + 0.35 * np.sin(2 * np.pi * q))        # deepest a little past the middle
    drop = slack * L * 0.20
    wave = sway * (1.5 + 7.0 * slack) * np.sin(np.pi * q) * np.sin(2 * np.pi * (1.6 * q - 0.33 * t) + rnd(seed, 2) * 6.0)
    pts = p0 + np.outer(q, v) + np.outer(belly * drop * 0.6 + wave, nr) + np.outer(belly * drop * 0.4, (0.0, 1.0))
    col = F.pick(C.CHALK_DIM, C.PENCIL) if col is None else col
    chalk(F, pts, col, w, a, seed, wob=0.5, taper=0.8, edge=0.15, step=5.0)
    if knot > 0.0:                                         # a bow: two loops and two loose ends
        k = min(1.0, knot)
        r = 7.0 * w / 2.4
        g = np.linspace(0.0, 2 * math.pi * k, 11)
        loops = [np.stack([p0[0] + sg * r * 0.85 * (1.0 - np.cos(g)), p0[1] - r * 0.6 * np.sin(g) - r * 0.18 * (1.0 - np.cos(g))], axis=1)
                 for sg in (-1.0, 1.0)]
        ends = [A(p0, (p0[0] - r * 0.5, p0[1] + r * 1.5 * k)), A(p0, (p0[0] + r * 0.7, p0[1] + r * 1.3 * k))]
        _lines(F, loops + ends, col, w * 0.9, a, "dense", seed + 3, 0.2)
    return pts


def perches(x0, x1, n: int = 11, seed: int = 510):
    """n places along a wire between world x0 and x1, in the ORDER the crows take them (not left to
    right: each newcomer picks a gap). Returns an array of world x."""
    n = int(n)
    g = [(0.37 + rnd(seed, 121) + j * 0.6180339887) % 1.0 for j in range(n)]      # each newcomer lands in the widest gap
    rank = np.argsort(np.argsort(g))
    return np.array([x0 + (x1 - x0) * (rank[j] + 0.5 + 0.2 * rsym(seed + j, 122)) / n for j in range(n)])


def crows_on_wire(F: Frame, wire, times, xs=None, s: float = 0.55, seed: int = 510, hunch: float = 0.75, a: float = 1.0,
                  land: float = 0.26, leave=None, to=(150.0, -230.0), fly: float = 1.1, t: float | None = None, col=None,
                  day: bool | None = None, approach: float = 0.5):
    """The crows gathering on the wire: crow j touches down at times[j] (song's clock, read against
    F.t), a landing of `land` seconds whose feet arrive ON that time, then sits, sinking into its
    shoulders over the next two seconds, and lives (crow, on t = F.tb). For `approach` seconds
    before its landing it is seen flying in from above and behind (clip to the window pane).

    wire: its world polyline (N, 2), as it is in this frame (dipped and swinging if the scene does
    that: see swing). xs: world x of each crow's place, in landing order (default perches() along the
    middle 84 percent of the wire). leave: None, or the times at which they fly up again (crow_fly
    toward `to`, taking `fly` seconds). Day skin: the same, as small birds.
    Returns [(x, y, age), ...] for the crows on the wire: age = seconds since touchdown."""
    wire = np.asarray(wire, dtype=np.float64)
    n = len(times)
    if xs is None:
        xa, xb = wire[0, 0], wire[-1, 0]
        xs = perches(xa + 0.08 * (xb - xa), xa + 0.92 * (xb - xa), n, seed)
    out = []
    for j in range(n):
        x = float(xs[j])
        y = float(np.interp(x, wire[:, 0], wire[:, 1]))
        age = F.t - times[j]
        u = age / land + 0.55
        sd = seed + j
        fc = 1 if rnd(sd, 123) > 0.42 else -1
        sj = s * (0.92 + 0.16 * rnd(sd, 124))
        come = (-64.0 - 30.0 * rnd(sd, 125), -46.0 - 20.0 * rnd(sd, 128))
        if u <= 0.0:
            v = 1.0 + (age + 0.55 * land) / max(1e-6, approach)      # 0..1 through the approach
            if approach > 0.0 and v > 0.0:
                far = (come[0] - 250.0 - 120.0 * rnd(sd, 130), come[1] - 190.0 - 80.0 * rnd(sd, 131))
                e = v * (2.0 - v)                               # it slows as it comes
                bird(F, x + fc * sj * (far[0] + (come[0] - far[0]) * e) - 4.0 * sj * fc, y + sj * (far[1] + (come[1] - far[1]) * e ** 1.4) - 24.0 * sj,
                     sj, 3.2 * v * approach / 0.5 + rnd(sd, 132), fc, sd, col, a * min(1.0, v * 5.0), climb=-0.25 * (1.0 - v), day=day)
            continue
        hj = hunch * (0.75 + 0.25 * rnd(sd, 129))
        if leave is not None and F.t >= leave[j]:
            crow_fly(F, x, y, sj, sd, fc, (F.t - leave[j]) / fly, a, (to[0] * (0.7 + 0.6 * rnd(sd, 126)), to[1] * (0.8 + 0.4 * rnd(sd, 127))), col, day,
                     hunch=hj * ramp(leave[j] - times[j], land * 0.45, 2.2))
            continue
        if u < 1.0:
            crow_land(F, x, y, sj, sd, fc, u, a, 0.0, col, day, come=come)
        else:
            crow(F, x, y, sj, sd, fc, a, hj * ramp(age, land * 0.45, 2.2), col, day, t=t)
        if age >= 0.0:
            out.append((x, y, age))
    return out
