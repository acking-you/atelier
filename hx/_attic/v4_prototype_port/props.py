"""hx.chalk.props: the set pieces of the story (faithful port of the prototype's).

Two kinds, all in WORLD coordinates (x, y = the anchor on the floor unless said otherwise):

  * builders return a Sketch of named strokes and fills (sofa, cushion, window, wall_drawing, chair,
    table3, lamp, rug, house, back_figure, voice, desk, pupil, board, door): place it, give it times,
    morph it, then .draw(F). The `name` argument prefixes the item names ("sofa.back", ...);
  * the others draw at once with F (phone, crow, flower, bud, grass, floorboards, night_wall,
    window_night, window_day, plain_ground, footprints, hill, tree) and follow F.skin where it matters.

To put a piece somewhere else or at another size, wrap it: `with F.place(dx, dy, scale): ...`
"""
from __future__ import annotations

import math

import numpy as np
import skia

from .core import (A, C, Frame, arc, blob, chalk, dashes, disc, fill, hatch, htab, mix, rect_pts, rnd, rrect_pts, rsym,
                   scrib, smudge, spline, vn)
from .gloom import scribble_pts
from .sketch import Fill, Sketch, Stroke
from .weather import rain


__all__ = ["line", "closed", "sofa", "cushion", "window", "wall_drawing", "chair", "table3", "lamp", "rug", "phone", "crow",
           "floorboards", "night_wall", "window_night", "window_day", "desk", "pupil", "board", "door", "house", "back_figure",
           "voice", "plain_ground", "footprints", "under", "hill", "tree", "flower", "bud", "grass", "tear_outline"]

# --------------------------------------------------------------------------
# small builders
# --------------------------------------------------------------------------
def line(x0, y0, x1, y1, col=C.CHALK, w=4.0, a=1.0, seed=0, name="", **kw) -> Stroke:
    return Stroke(A((x0, y0), (x1, y1)), col, w, a, seed, name, **kw)


def closed(P, col=C.CHALK, w=4.0, a=1.0, seed=0, name="", **kw) -> Stroke:
    """A closed outline that overshoots its start a little, as a child closes a shape."""
    P = np.asarray(P, dtype=np.float64)
    n = max(2, len(P) // 12)
    return Stroke(np.vstack([P, P[1:n + 1]]), col, w, a, seed, name, **kw)


# --------------------------------------------------------------------------
# the room
# --------------------------------------------------------------------------
def sofa(x, y, w=760.0, seed=100, col=C.CHALK_COOL, fill=(0.22, 0.28, 0.45), k=C.KNOCK, name="sofa") -> Sketch:
    """x = its left end, y = the floor. Parts: back seat split arm_l arm_r leg_l leg_r (+ .fill)."""
    s = w / 760.0
    aw = 104 * s
    back = rrect_pts(x + aw * 0.45, y - 290 * s, x + w - aw * 0.45, y - 60 * s, 46 * s)
    seat = rrect_pts(x + aw * 0.6, y - 122 * s, x + w - aw * 0.6, y - 26 * s, 20 * s)
    arm_l = rrect_pts(x, y - 186 * s, x + aw, y - 18 * s, 36 * s)
    arm_r = rrect_pts(x + w - aw, y - 186 * s, x + w, y - 18 * s, 36 * s)
    return Sketch([
        Fill(back, fill, 0.9, 13 * s, 6.0 * s, 0.55, seed + 1, knock=k, base=0.28, name="back.fill"),
        closed(back, col, 4.6 * s, 0.95, seed + 2, "back"),
        Fill(seat, mix(fill, C.CHALK_BLUE, 0.25), -0.5, 12 * s, 6.0 * s, 0.6, seed + 3, knock=k, base=0.34, name="seat.fill"),
        closed(seat, col, 4.6 * s, 0.95, seed + 4, "seat"),
        line(x + w * 0.5, y - 120 * s, x + w * 0.5 + 4, y - 30 * s, col, 3.2 * s, 0.7, seed + 5, "split"),
        Fill(arm_l, fill, 1.1, 11 * s, 5.5 * s, 0.6, seed + 6, knock=k, base=0.36, name="arm_l.fill"),
        closed(arm_l, col, 4.8 * s, 1.0, seed + 7, "arm_l"),
        Fill(arm_r, fill, 1.1, 11 * s, 5.5 * s, 0.6, seed + 8, knock=k, base=0.36, name="arm_r.fill"),
        closed(arm_r, col, 4.8 * s, 1.0, seed + 9, "arm_r"),
        line(x + 30 * s, y - 18 * s, x + 26 * s, y + 4 * s, col, 5 * s, 0.9, seed + 10, "leg_l"),
        line(x + w - 30 * s, y - 18 * s, x + w - 26 * s, y + 4 * s, col, 5 * s, 0.9, seed + 11, "leg_r"),
    ], name)


def cushion(x, y, s=1.0, rot=0.0, seed=120, col=C.CHALK_COOL, fill=(0.36, 0.40, 0.58), name="cushion") -> Sketch:
    """x, y = its centre."""
    P = blob(x, y, 62 * s, 40 * s, seed, 0.07, 30, rot)
    return Sketch([Fill(P, fill, 0.3 + rot, 9 * s, 5 * s, 0.7, seed + 1, knock=C.KNOCK, base=0.4, name="shape.fill"),
                   closed(P, col, 4 * s, 0.95, seed + 2, "shape")], name)


def window(l, t, r, b, seed=200, col=C.CHALK_COOL, curtains=True, name="window") -> Sketch:
    """The frame only (what it shows: window_night / window_day). Parts: frame inner mullion transom
    sill, and with curtains: rail curtain.l0-3 curtain.r0-3."""
    sk = [
        closed(rect_pts(l, t, r, b), col, 5.5, 1.0, seed + 1, "frame"),
        closed(rect_pts(l + 14, t + 14, r - 14, b - 14), col, 3.0, 0.75, seed + 2, "inner"),
        line((l + r) / 2, t + 4, (l + r) / 2 + 2, b - 4, col, 4.4, 0.95, seed + 3, "mullion"),
        line(l + 4, (t + b) / 2 - 14, r - 4, (t + b) / 2 - 12, col, 4.4, 0.95, seed + 4, "transom"),
        line(l - 26, b + 12, r + 26, b + 14, col, 6.0, 1.0, seed + 5, "sill"),
    ]
    if curtains:
        sk.append(line(l - 70, t - 34, r + 70, t - 32, col, 4.0, 0.8, seed + 6, "rail"))
        for side, x0 in ((-1, l - 8), (1, r + 8)):
            for j in range(4):
                xx = x0 + side * j * 16
                yy = np.linspace(t - 30, b + 40 - j * 6, 9)
                xs = xx + side * (6 + j * 3) * np.sin(np.linspace(0, 2.6, 9) + j) + side * 10 * (yy - t) / (b - t)
                sk.append(Stroke(np.stack([xs, yy], axis=1), mix(col, C.CHALK_DIM, 0.45), 3.2, 0.72,
                                 seed + 10 + j + (side > 0) * 5, f"curtain.{'l' if side < 0 else 'r'}{j}"))
    return Sketch(sk, name)


def wall_drawing(x, y, s=1.0, gap=10.0, taped=False, seed=300, paper=(0.58, 0.62, 0.74), ink=(0.12, 0.14, 0.22),
                 rot=-0.06, name="pic") -> Sketch:
    """The child's drawing of three figures, torn through the middle (the halves `gap` apart); later
    taped. x, y = its centre. Parts: left right (+ .fill), fig0.* fig1.l.* fig1.r.* fig2.*, pin_l pin_r
    or tape0 tape1."""
    w, h = 150 * s, 112 * s
    cr, sr = math.cos(rot), math.sin(rot)

    def T(px, py, side=0):
        px = px + side * gap * 0.5
        py = py + side * gap * 0.22
        return (x + px * cr - py * sr, y + px * sr + py * cr)

    n = 9
    ty = np.linspace(-h / 2, h / 2, n)
    tx = np.array([(-1) ** j * 7 * s * (0.5 + rnd(seed + j, 1)) for j in range(n)])
    tx[0] *= 0.3
    left = [T(-w / 2, -h / 2, -1), *[T(tx[j], ty[j], -1) for j in range(n)], T(-w / 2, h / 2, -1)]
    right = [T(w / 2, -h / 2, 1), *[T(tx[j], ty[j], 1) for j in range(n)], T(w / 2, h / 2, 1)]
    sk = []
    for nm, poly, sd in (("left", left, 1), ("right", right, 2)):
        P = np.asarray(poly + [poly[0]])
        sk.append(Fill(P, paper, 0.4, 5 * s, 4 * s, 0.0, seed + sd, knock=C.KNOCK, base=0.92, grain="dense", name=nm + ".fill"))
        sk.append(Stroke(P, mix(paper, C.CHALK, 0.6), 2.6 * s, 0.95, seed + sd + 2, nm))
    # three stick figures: big, small, big; the small one is on the tear
    kw = dict(wob=0.3, edge=0.0)
    for j, (fx, fh, side) in enumerate(((-0.30, 0.56, -1), (0.0, 0.36, 0), (0.30, 0.60, 1))):
        px = fx * w
        base = h * 0.36
        top = base - fh * h
        hr = fh * h * 0.20
        if side == 0:
            # half of the small figure on each piece
            for sgn in (-1, 1):
                nm = f"fig{j}.{'l' if sgn < 0 else 'r'}"
                a0, a1 = (math.pi / 2, 3 * math.pi / 2) if sgn < 0 else (-math.pi / 2, math.pi / 2)
                hd = np.array([T(px + sgn * 0.5 + math.cos(q) * hr, top + hr + math.sin(q) * hr, sgn) for q in np.linspace(a0, a1, 9)])
                sk.append(Stroke(hd, ink, 2.2 * s, 0.95, seed + 20 + j + sgn, nm + ".head", **kw))
                sk.append(Stroke(A(T(px + sgn * 2, top + 2 * hr, sgn), T(px + sgn * 9 * s, base, sgn)), ink, 2.2 * s, 0.95,
                                 seed + 25 + sgn, nm + ".body", **kw))
                sk.append(Stroke(A(T(px + sgn * 2, top + 2.6 * hr, sgn), T(px + sgn * 14 * s, top + 3.4 * hr, sgn)), ink, 2.0 * s,
                                 0.95, seed + 28 + sgn, nm + ".arm", **kw))
            continue
        nm = f"fig{j}"
        hd = np.array([T(px + math.cos(q) * hr, top + hr + math.sin(q) * hr, side) for q in np.linspace(0, 2 * math.pi + 0.4, 14)])
        sk.append(Stroke(hd, ink, 2.3 * s, 0.95, seed + 30 + j, nm + ".head", **kw))
        hip = top + 2 * hr + (base - top - 2 * hr) * 0.55
        sk.append(Stroke(A(T(px, top + 2 * hr, side), T(px, hip, side)), ink, 2.3 * s, 0.95, seed + 33 + j, nm + ".body", **kw))
        sk.append(Stroke(A(T(px - 9 * s, base, side), T(px, hip, side), T(px + 9 * s, base, side)), ink, 2.3 * s, 0.95,
                         seed + 36 + j, nm + ".legs", **kw))
        sk.append(Stroke(A(T(px - 13 * s, top + 3.3 * hr, side), T(px, top + 2.5 * hr, side), T(px + 13 * s, top + 3.3 * hr, side)),
                         ink, 2.1 * s, 0.95, seed + 39 + j, nm + ".arms", **kw))
    if taped:
        for j, ty_ in enumerate((-h * 0.26, h * 0.2)):
            a0 = 0.25 * (1 if j else -1)
            P = [T(-16 * s, ty_ - 6 * s - a0 * 8, 0), T(16 * s, ty_ - 6 * s + a0 * 8, 0), T(16 * s, ty_ + 6 * s + a0 * 8, 0),
                 T(-16 * s, ty_ + 6 * s - a0 * 8, 0)]
            P = np.asarray(P + [P[0]])
            sk.append(Fill(P, C.AMBER_PALE, 0.2, 4, 3, 0.0, seed + 50 + j, knock=None, base=0.85, grain="mid", name=f"tape{j}.fill"))
            sk.append(Stroke(P, C.AMBER, 1.8 * s, 0.9, seed + 52 + j, f"tape{j}", wob=0.3))
    else:
        for nm, sx, sd in (("pin_l", -1, 60), ("pin_r", 1, 62)):
            sk.append(Stroke(blob(*T(sx * w * 0.36, -h * 0.40, sx), 4 * s, 4 * s, seed + sd, 0.1, 10), C.CHALK, 2.4 * s, 1.0,
                             seed + sd + 1, nm, wob=0.2))
    return Sketch(sk, name)


def chair(x, y, s=1.0, face=1, seed=400, col=C.CHALK_DIM, a=0.8, name="chair") -> Sketch:
    """A child's chair in side view. Parts: seat leg_b leg_f back rail."""
    f = face
    return Sketch([
        line(x - 30 * s * f, y - 62 * s, x + 30 * s * f, y - 62 * s, col, 4.2 * s, a, seed + 1, "seat"),
        line(x - 28 * s * f, y - 60 * s, x - 32 * s * f, y, col, 3.8 * s, a, seed + 2, "leg_b"),
        line(x + 28 * s * f, y - 60 * s, x + 31 * s * f, y, col, 3.8 * s, a, seed + 3, "leg_f"),
        line(x - 30 * s * f, y - 62 * s, x - 36 * s * f, y - 150 * s, col, 4.0 * s, a, seed + 4, "back"),
        line(x - 44 * s * f, y - 150 * s, x - 26 * s * f, y - 148 * s, col, 4.2 * s, a, seed + 5, "rail"),
    ], name)


def table3(x, y, s=1.0, seed=420, col=C.CHALK_DIM, a=0.8, apart=0.0, name="table") -> Sketch:
    """The table with three chairs; apart = 0..1 how far two of the chairs have been pulled away.
    Parts: top leg_l leg_r chair_l.* chair_r.* chair_m.*"""
    return Sketch([
        line(x - 120 * s, y - 108 * s, x + 120 * s, y - 106 * s, col, 5 * s, a, seed + 1, "top"),
        line(x - 100 * s, y - 104 * s, x - 108 * s, y, col, 4 * s, a, seed + 2, "leg_l"),
        line(x + 100 * s, y - 104 * s, x + 107 * s, y, col, 4 * s, a, seed + 3, "leg_r"),
        chair(x - (170 + 90 * apart) * s, y, s, 1, seed + 10, col, a, "chair_l"),
        chair(x + (170 + 110 * apart) * s, y, s, -1, seed + 20, col, a, "chair_r"),
        chair(x + 4 * s, y - 8 * s, s * 0.82, 1, seed + 30, col, a * 0.85, "chair_m"),
    ], name)


def lamp(x, y, h=420.0, seed=440, col=C.CHALK_DIM, a=0.85, name="lamp") -> Sketch:
    """A standing lamp. Parts: pole foot shade (+ .fill)."""
    s = h / 420.0
    shade = A((x - 48 * s, y - h + 96 * s), (x - 28 * s, y - h), (x + 28 * s, y - h), (x + 50 * s, y - h + 96 * s), (x - 48 * s, y - h + 96 * s))
    return Sketch([
        line(x, y - h + 96 * s, x + 2, y - 8, col, 4 * s, a, seed + 1, "pole"),
        Stroke(arc(x, y - 4, 44 * s, 10 * s, math.pi, 2 * math.pi, 12), col, 4 * s, a, seed + 2, "foot"),
        Fill(shade, mix(col, C.PAPER, 0.4), 1.2, 9 * s, 4 * s, 0.5, seed + 3, knock=C.KNOCK, base=0.2, name="shade.fill"),
        closed(shade, col, 4 * s, a, seed + 4, "shade"),
    ], name)


def rug(x, y, rx, ry, seed=460, col=(0.30, 0.35, 0.52), name="rug") -> Sketch:
    """x, y = its centre. Parts: outer (+ .fill) inner."""
    P = blob(x, y, rx, ry, seed, 0.03, 44)
    Q = blob(x, y, rx * 0.72, ry * 0.62, seed + 3, 0.03, 36)
    return Sketch([Fill(P, col, 0.12, 15, 5.5, 0.42, seed + 1, base=0.12, name="outer.fill"),
                   closed(P, mix(col, C.CHALK_DIM, 0.6), 3.4, 0.7, seed + 2, "outer"),
                   closed(Q, mix(col, C.CHALK_DIM, 0.5), 2.6, 0.5, seed + 4, "inner")], name)


def phone(F: Frame, x, y, s=1.0, lit: float = 0.0, seed=480, ring: float = 0.0, col=C.CHALK_COOL, draw: float = 1.0):
    """A phone lying on the floor (a little slanted slab). lit = 0..1 screen glow (amber when it
    rings), ring = 0..1 strength of the ring arcs, draw = 0..1 it is still being drawn."""
    if draw <= 0.0:
        return
    P = A((x - 26 * s, y - 9 * s), (x + 22 * s, y - 13 * s), (x + 30 * s, y + 8 * s), (x - 20 * s, y + 13 * s), (x - 26 * s, y - 9 * s))
    fill(F, P, C.GLOOM_MID, 0.95 * draw)
    if lit > 0:
        smudge(F, x, y - 4 * s, 120 * s, 70 * s, C.AMBER_GLOW, 0.5 * lit, "soft", additive=True)
        fill(F, P, C.AMBER_PALE, 0.9 * lit, "dense")
    chalk(F, np.vstack([P, P[1:2]]), mix(col, C.AMBER, lit), 3.0 * s, 0.95, seed, wob=0.4, taper=0.7, draw=draw)
    if ring > 0:
        for j in range(3):
            rr = (34 + j * 20) * s
            chalk(F, arc(x, y - 6 * s, rr, rr * 0.8, -2.5, -0.65, 12), C.AMBER, 2.6 * s, ring * (1 - j * 0.25), seed + 3 + j,
                  wob=0.5)


def crow(F: Frame, x, y, s=1.0, seed=500, face=1, a=1.0, hunch: float = 0.0, col=None, day: bool | None = None):
    """A crow perched on the world point (x, y): a dark body rubbed in, a pale outline, beak, tail, legs."""
    day = F.day if day is None else day
    col = col or (C.PENCIL if day else (0.36, 0.41, 0.58))
    f = face
    body = blob(x - 4 * s * f, y - 24 * s, 25 * s, 17 * s * (1 + 0.15 * hunch), seed, 0.06, 22, rot=-0.35 * f)
    hd = blob(x + 15 * s * f, y - (44 - 6 * hunch) * s, 11.5 * s, 10.5 * s, seed + 1, 0.05, 16)
    dark = (0.22, 0.22, 0.30) if day else C.GLOOM
    for P in (body, hd):
        fill(F, P, dark, 0.96 * a, "dense" if day else None)
    w = 2.6 * s
    kw = dict(step=4.0, floor=1.3)
    chalk(F, np.vstack([body, body[1:3]]), col, w, 0.9 * a, seed + 2, wob=0.4 * s, edge=0.2, **kw)
    chalk(F, np.vstack([hd, hd[1:3]]), col, w, 0.9 * a, seed + 3, wob=0.3 * s, edge=0.2, **kw)
    by = y - (46 - 6 * hunch) * s
    chalk(F, A((x + 24 * s * f, by), (x + 38 * s * f, by + 5 * s), (x + 24 * s * f, by + 7 * s)), col, w, a, seed + 4, wob=0.0,
          edge=0.0, **kw)
    chalk(F, A((x - 22 * s * f, y - 20 * s), (x - 44 * s * f, y - 6 * s)), col, w * 1.6, 0.9 * a, seed + 5, wob=0.3 * s, taper=0.3,
          edge=0.2, step=4.0, floor=2.1)
    for dx in (-3, 6):
        chalk(F, A((x + dx * s * f, y - 9 * s), (x + (dx + 1) * s * f, y + 1 * s)), col, w * 0.8, 0.9 * a, seed + 6 + dx, wob=0.0,
              edge=0.0, step=4.0, floor=1.05)
    disc(F, x + 18 * s * f, by, 1.9 * s, C.DAY if day else C.CHALK, 0.95 * a * (s * F.cam.zoom > 0.5), None, floor=1.0)


def floorboards(F: Frame, y, x0=-20.0, x1=1940.0, bottom=1090.0, a=0.22, col=C.CHALK_FAR, vx=960.0, draw: float = 1.0):
    """The floor: the skirting line at world y from x0 to x1 and a fan of boards toward the viewer
    (vx = the vanishing x; a = pressure of the boards; draw = 0..1 the skirting line is still being drawn)."""
    chalk(F, A((x0, y), (x1, y + 3)), C.CHALK_DIM, 4.2, 0.85, 11, wob=1.2, draw=draw)
    chalk(F, A((x0, y - 22), (x1, y - 19)), col, 2.6, 0.5, 12, wob=1.0, draw=min(1.0, max(0.0, draw * 1.3 - 0.3)))
    for j in range(13):
        xa = x0 - 240 + j * (x1 - x0 + 500) / 12.0 + 40 * rsym(j, 5)
        chalk(F, A((xa, y + 10), (vx + (xa - vx) * 2.3, bottom)), col, 2.4, a * (0.7 + 0.5 * rnd(j, 6)), 20 + j, wob=1.0, taper=0.3)


def night_wall(F: Frame, y1, x0=-40.0, x1=1960.0, y0=-40.0, a=1.0):
    """Night coloured into the wall by a tired hand: one long loose seated zigzag from y0 down to y1,
    darker in the corners."""
    poly = A((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))
    hatch(F, poly, (0.21, 0.26, 0.41), 1.12, 58, 15, 0.30 * a, 901, grain="sparse", wob=2.2, clip=True, boil=False)
    hatch(F, poly, (0.13, 0.16, 0.26), 1.02, 74, 20, 0.42 * a, 902, grain="sparse", wob=2.2, clip=True, boil=False)
    for j in range(22):
        xa = x0 - 60 + j * (x1 - x0) / 20.0 + 30 * rsym(j, 1)
        ln = 260 + 300 * rnd(j, 2)
        ya = y0 + 20 + 100 * rnd(j, 3)
        d = abs(j - 10.5) / 10.5
        chalk(F, A((xa, ya), (xa - ln * 0.45, ya + ln)), C.PAPER_DEEP, 18, a * (0.15 + 0.55 * d), 900 + j, wob=2.0,
              taper=0.3, grain="sparse", edge=0.0, boil=0.0)


def _roofline(l, r, b, chimney=True):
    ry = b - 110
    pts = [(l - 10, ry + 40), (l + 24, ry + 40), (l + 24, ry + 2), (l + 92, ry - 44), (l + 160, ry + 2), (l + 160, ry + 34),
           (l + 204, ry + 34), (l + 204, ry - 10)]
    if chimney:
        pts += [(l + 228, ry - 10), (l + 228, ry - 40), (l + 246, ry - 40), (l + 246, ry - 22)]
    return A(*pts, (l + 284, ry - 52), (l + 352, ry - 6), (l + 352, ry + 30), (r + 10, ry + 30)), ry


def _wire(l, t, r):
    return np.stack([np.linspace(l - 10, r + 10, 14), t + 150 + 16 * np.sin(np.linspace(0.2, 2.9, 14))], axis=1)


def window_night(F: Frame, l, t, r, b, t_now=None, crows=0, a=1.0, lit=1.0):
    """What the window shows at night: a darker night, roofs with a wire, rain, drops on the glass;
    in one far house a window is lit amber (lit = 0..1). crows: how many sit on the wire."""
    t_now = F.tb if t_now is None else t_now
    with F.clip(rect=(l, t, r, b)):
        fill(F, rect_pts(l, t, r, b), C.PAPER_DEEP, 0.92)
        smudge(F, (l + r) / 2 + 60, t + 70, 300, 210, (0.30, 0.38, 0.60), 0.55 * a, "soft", power=1.3)
        roof, ry = _roofline(l, r, b)
        fill(F, np.vstack([roof, [(r + 10, b + 5), (l - 10, b + 5)]]), C.GLOOM, 0.9)
        chalk(F, roof, C.CHALK_FAR, 3.0, 0.95, 71, wob=0.8)
        fill(F, rect_pts(l + 70, ry + 24, l + 92, ry + 50), (0.30, 0.34, 0.48), 0.6, "mid")
        if lit > 0:
            wx, wy = l + 268, ry + 16
            smudge(F, wx + 12, wy + 14, 100, 90, C.AMBER_GLOW, 0.40 * a * lit, "glow", additive=True)
            fill(F, rect_pts(wx, wy, wx + 24, wy + 28), C.AMBER, 0.95 * a * lit, "dense")
            chalk(F, A((wx + 12, wy), (wx + 12, wy + 28)), C.AMBER_DEEP, 2.0, 0.9 * lit, 73, wob=0.0, edge=0.0)
        wire = _wire(l, t, r)                              # the wire under the eaves
        chalk(F, wire, C.CHALK_DIM, 2.4, 0.85, 72, wob=0.6)
        for j in range(crows):
            xx = l + (r - l) * (0.2 + 0.6 * (j + 0.5) / max(1, crows) + 0.04 * rsym(j, 8))
            crow(F, xx, float(np.interp(xx, wire[:, 0], wire[:, 1])), 0.62, 510 + j, face=1 if rnd(j, 9) > 0.4 else -1, a=0.95,
                 day=False)
        rain(F, l, t, r, b, n=70, slant=0.22, ln=34, col=C.CHALK_BLUE, a=0.62, w=2.2, seed=3, t=t_now)
        # drops running down the glass
        i = np.arange(9)
        gx = l + 20 + htab(i, 17, 3) * (r - l - 40)
        gy = t + ((htab(i, 19, 5) + t_now * (0.05 + 0.05 * htab(i, 23, 7))) % 1.0) * (b - t)
        for x_, y_, j in zip(gx, gy, i):
            yy = np.linspace(y_ - 70, y_, 8)
            xs = x_ + 3 * np.sin(yy * 0.05 + j)
            chalk(F, np.stack([xs, yy], axis=1), C.CHALK_COOL, 2.2, 0.55, 80 + int(j), wob=0.3, taper=0.2, edge=0.0, boil=0.0)
            disc(F, xs[-1], y_, 3.0, C.CHALK_COOL, 0.8)


def window_day(F: Frame, l, t, r, b, a=1.0, crows=5):
    """The same window by day, before colour: a pale grey sky, the wire, the roofs (a = 0..1 fades it in)."""
    with F.clip(rect=(l, t, r, b)):
        fill(F, rect_pts(l, t, r, b), (0.30, 0.35, 0.48), 0.85 * a, "glow")
        hatch(F, rect_pts(l, t, r, b), (0.46, 0.52, 0.66), 0.2, 26, 10, 0.5 * a, 1700, grain="sparse", clip=True, boil=False)
        roof, _ = _roofline(l, r, b, chimney=False)
        fill(F, np.vstack([roof, [(r + 10, b + 5), (l - 10, b + 5)]]), (0.17, 0.20, 0.31), 0.9 * a)
        chalk(F, roof, C.CHALK_DIM, 3.0, 0.9 * a, 71, wob=0.8)
        wire = _wire(l, t, r)
        chalk(F, wire, C.CHALK_DIM, 2.4, 0.85 * a, 72, wob=0.6)
        for j in range(crows):
            xx = l + (r - l) * (0.14 + 0.18 * j)
            crow(F, xx, float(np.interp(xx, wire[:, 0], wire[:, 1])), 0.6, 510 + j, face=1 if j % 2 else -1, a=a, day=False)


# --------------------------------------------------------------------------
# school
# --------------------------------------------------------------------------
def desk(x, y, s=1.0, seed=900, col=C.CHALK_DIM, a=0.85, name="desk") -> Sketch:
    """A school desk seen from the side. Parts: top leg_l leg_r shelf."""
    return Sketch([
        line(x - 52 * s, y - 96 * s, x + 52 * s, y - 94 * s, col, 4.6 * s, a, seed + 1, "top"),
        line(x - 46 * s, y - 94 * s, x - 48 * s, y, col, 3.6 * s, a, seed + 2, "leg_l"),
        line(x + 46 * s, y - 92 * s, x + 47 * s, y, col, 3.6 * s, a, seed + 3, "leg_r"),
        line(x - 46 * s, y - 70 * s, x + 46 * s, y - 68 * s, col, 2.8 * s, a * 0.8, seed + 4, "shelf"),
    ], name)


def pupil(x, y, s=1.0, seed=1200, col=C.CHALK_DIM, a=0.85, name="pupil") -> Sketch:
    """A classmate at a desk, seen from behind. Parts: shoulders head (+ .fill) chair leg_l leg_r."""
    r = 26 * s
    head = blob(x, y - 150 * s, r, r * 1.05, seed, 0.03, 20)
    sh = spline(A((x - 44 * s, y - 62 * s), (x - 40 * s, y - 104 * s), (x, y - 122 * s), (x + 40 * s, y - 104 * s), (x + 44 * s, y - 62 * s)), 14)
    return Sketch([
        Fill(np.vstack([sh, sh[:1]]), (0.19, 0.23, 0.36), 1.0, 9 * s, 4.5 * s, 0.6, seed + 1, knock=C.KNOCK, base=0.5, name="shoulders.fill"),
        Stroke(sh, col, 4.0 * s, a, seed + 2, "shoulders"),
        Fill(head, (0.24, 0.29, 0.44), 0.5, 7 * s, 4 * s, 0.8, seed + 3, knock=C.KNOCK, base=0.7, name="head.fill"),
        closed(head, col, 3.8 * s, a, seed + 4, "head"),
        Stroke(rect_pts(x - 50 * s, y - 70 * s, x + 50 * s, y - 16 * s), col, 3.6 * s, a * 0.9, seed + 5, "chair"),
        line(x - 44 * s, y - 16 * s, x - 46 * s, y + 6 * s, col, 3.4 * s, a * 0.9, seed + 6, "leg_l"),
        line(x + 44 * s, y - 16 * s, x + 46 * s, y + 6 * s, col, 3.4 * s, a * 0.9, seed + 7, "leg_r"),
    ], name)


def board(l, t, r, b, seed=1320, col=C.CHALK_COOL, name="board") -> Sketch:
    """The blackboard: scribbled lines only, never writing. Parts: frame (+ .fill) ledge chalk text0-2."""
    def text(j, x1, n):
        return Stroke(np.stack([np.linspace(l + 50, x1, n), t + 66 + 60 * j + 12 * (np.arange(n) % 2)], axis=1), C.CHALK_DIM, 3.0,
                      0.75, seed + 4 + j, f"text{j}")
    return Sketch([Fill(rect_pts(l, t, r, b), (0.13, 0.20, 0.22), 0.3, 18, 9, 0.55, seed, knock=C.PAPER_DEEP, base=0.6, name="frame.fill"),
                   closed(rect_pts(l, t, r, b), col, 5.5, 0.95, seed + 1, "frame"),
                   line(l - 14, b + 14, r + 14, b + 16, col, 6.0, 0.95, seed + 2, "ledge"),
                   Stroke(rect_pts(r - 150, b - 2, r - 90, b + 12), C.CHALK, 3.0, 0.9, seed + 3, "chalk"),
                   text(0, l + 330, 28), text(1, l + 470, 40), text(2, l + 250, 20)], name)


def door(l, t, r, b, seed=1600, col=C.CHALK_DIM, name="door") -> Sketch:
    """Parts: frame knob."""
    return Sketch([closed(rect_pts(l, t, r, b), col, 4.6, 0.85, seed, "frame"),
                   Stroke(blob(r - 26, t + (b - t) * 0.56, 7, 7, seed + 1, 0.1, 10), col, 3.0, 0.9, seed + 2, "knob")], name)


# --------------------------------------------------------------------------
# the towering things of the choruses
# --------------------------------------------------------------------------
def house(x, y, w=300.0, seed=600, col=C.CHALK_DIM, split: float = 0.0, a=1.0, lw=4.0, fill=None, roof=None,
          name="house") -> Sketch:
    """A child's house, x = its middle on the ground. split > 0: torn down the middle, the halves
    leaning apart (split = lean in rad). fill / roof: colours to colour the walls / the roof in.
    Parts per half (l, r): l.wall l.roof l.eave l.tear l.wall.fill l.roof.fill, l.door, r.window r.bar."""
    h = w * 0.72
    rh = w * 0.5
    n = 8
    ty = np.linspace(-(h + rh), 0.0, n)
    tx = np.array([(-1) ** j * w * 0.035 * (0.5 + rnd(seed + j, 3)) for j in range(n)])
    fills, sk = [], []
    for side, nm in ((-1, "l"), (1, "r")):
        ang = side * split
        ca, sa = math.cos(ang), math.sin(ang)
        px = x + side * (w * 0.5 + (w * 0.10 if split > 0 else 0.0) * min(1.0, split * 6))

        def T(dx, dy, px=px, ca=ca, sa=sa, side=side):
            lx = dx - side * w * 0.5                   # rotate about the half's outer bottom corner
            return (px + lx * ca - dy * sa, y + lx * sa + dy * ca)

        tear = [T(tx[j] if split > 0 else 0.0, ty[j]) for j in range(n)]
        wall = [T(side * w * 0.5, 0.0), T(side * w * 0.5, -h)]
        sk.append(Stroke(np.asarray([tear[-1]] + wall), col, lw, a, seed + 10 + side, nm + ".wall"))
        sk.append(Stroke(np.asarray([T(side * w * 0.62, -h + 6), tear[0]]), col, lw * 1.1, a, seed + 14 + side, nm + ".roof"))
        sk.append(Stroke(np.asarray([T(side * w * 0.5, -h), T(tx[2] if split > 0 else 0.0, -h + 2)]), col, lw * 0.8, a * 0.8,
                         seed + 18 + side, nm + ".eave"))
        if split > 0:
            sk.append(Stroke(np.asarray(tear), mix(col, C.CHALK, 0.5), lw * 0.8, a, seed + 22 + side, nm + ".tear", wob=0.3))
        if fill is not None:
            fills.insert(0, Fill(np.asarray(wall + [T(0.0, -h), T(0.0, 0.0)]), fill, 0.9 * side, 12, 5, 0.5 * a, seed + 30 + side,
                                 base=0.12, name=nm + ".wall.fill"))
        if roof is not None:
            fills.insert(0, Fill(np.asarray([T(side * w * 0.62, -h + 6), tear[0], T(0.0, -h + 4)]), roof, -0.6 * side, 11, 5, 0.7 * a,
                                 seed + 34 + side, base=0.2, name=nm + ".roof.fill"))
        if side < 0:
            d = [T(-w * 0.30, 0.0), T(-w * 0.30, -h * 0.5), T(-w * 0.10, -h * 0.5), T(-w * 0.10, 0.0)]
            sk.append(Stroke(np.asarray(d), col, lw * 0.85, a, seed + 40, "l.door"))
        else:
            q = [T(w * 0.14, -h * 0.34), T(w * 0.14, -h * 0.68), T(w * 0.36, -h * 0.68), T(w * 0.36, -h * 0.34), T(w * 0.14, -h * 0.34)]
            sk.append(Stroke(np.asarray(q), col, lw * 0.85, a, seed + 41, "r.window"))
            sk.append(Stroke(np.asarray([T(w * 0.25, -h * 0.68), T(w * 0.25, -h * 0.34)]), col, lw * 0.6, a * 0.8, seed + 42, "r.bar"))
    return Sketch(fills + sk, name)


def back_figure(x, y, h, seed=700, col=C.CHALK_FAR, a=1.0, lw=4.0, fill=(0.16, 0.19, 0.30), lean=0.0, tilt=0.0,
                name="back") -> Sketch:
    """A turned back, h tall, standing on (x, y): the back of a head (hair scribbled in), shoulders, a
    long coat, hands in pockets, two legs. No face. Used small (classmates) and enormous.
    Parts: body (+ .fill) hem leg0-3 foot_l foot_r arm_l arm_r head (+ .fill)."""
    r = h * 0.095
    hx = x + lean * h
    hy = y - h + r
    head = blob(hx + tilt * r, hy, r, r * 1.05, seed, 0.03, 26)
    sh = hy + r * 1.02
    wS, wH = h * 0.135, h * 0.118
    hem = y - h * 0.26
    body = np.vstack([
        A((x - wH, hem)),
        spline(A((x - wH, hem), (hx - wS * 1.02, sh + h * 0.12), (hx - wS * 0.9, sh + h * 0.035), (hx - wS * 0.45, sh), (hx, sh - h * 0.006),
                 (hx + wS * 0.45, sh), (hx + wS * 0.9, sh + h * 0.035), (hx + wS * 1.02, sh + h * 0.12), (x + wH, hem)), 26),
        A((x + wH, hem)), A((x - wH, hem))])
    return Sketch([
        Fill(body, fill, 1.05, max(7.0, h * 0.026), max(3.0, h * 0.011), 0.6 * a, seed + 1, knock=C.KNOCK, base=0.55, name="body.fill"),
        Stroke(body[:-1], col, lw, a, seed + 2, "body"),
        Stroke(A((x - wH * 0.9, hem + 2), (x + wH * 0.9, hem + 4)), col, lw * 0.8, a * 0.8, seed + 3, "hem"),
        Stroke(A((x - wH * 0.62, hem + 3), (x - wH * 0.66, y)), col, lw, a, seed + 4, "leg0"),
        Stroke(A((x - wH * 0.08, hem + 3), (x - wH * 0.14, y)), col, lw * 0.9, a * 0.9, seed + 5, "leg1"),
        Stroke(A((x + wH * 0.10, hem + 3), (x + wH * 0.16, y)), col, lw * 0.9, a * 0.9, seed + 6, "leg2"),
        Stroke(A((x + wH * 0.64, hem + 3), (x + wH * 0.68, y)), col, lw, a, seed + 7, "leg3"),
        Stroke(A((x - wH * 0.9, y), (x - wH * 0.05, y + 1)), col, lw * 1.2, a, seed + 8, "foot_l"),
        Stroke(A((x + wH * 0.05, y), (x + wH * 0.9, y + 1)), col, lw * 1.2, a, seed + 9, "foot_r"),
        # arms: down the sides, hands gone into the pockets
        Stroke(spline(A((hx - wS * 0.72, sh + h * 0.07), (x - wH * 0.74, y - h * 0.50), (x - wH * 0.42, y - h * 0.40)), 10), col, lw * 0.8,
               a * 0.85, seed + 10, "arm_l"),
        Stroke(spline(A((hx + wS * 0.72, sh + h * 0.07), (x + wH * 0.74, y - h * 0.50), (x + wH * 0.42, y - h * 0.40)), 10), col, lw * 0.8,
               a * 0.85, seed + 11, "arm_r"),
        # the back of the head
        Fill(head, mix(fill, col, 0.35), 0.5, max(5.0, h * 0.016), max(3.0, h * 0.011), 0.85 * a, seed + 12, knock=C.KNOCK, base=0.7,
             name="head.fill"),
        closed(head, col, lw, a, seed + 13, "head"),
    ], name)


def voice(x, y, rx, ry, tail, seed=800, col=C.CHALK_FAR, a=1.0, lw=3.6, lines=4, name="voice") -> Sketch:
    """A voice: a speech balloon centred (x, y) full of scribbled-out lines (no writing), its tail
    aimed at the world point `tail`. Parts: balloon (+ .fill) line0.."""
    P = blob(x, y, rx, ry, seed, 0.05, 36)
    ang = math.atan2(tail[1] - y, tail[0] - x)
    i0 = int(round((ang % (2 * math.pi)) / (2 * math.pi) * 36)) % 36
    Q = np.vstack([P[:-1][i0 + 2:], P[:-1][:max(0, i0 - 1)]]) if i0 >= 1 else P[2:-2]
    tipv = np.array([x + math.cos(ang) * rx * 1.75, y + math.sin(ang) * ry * 1.9])
    Q = np.vstack([Q, tipv[None, :], Q[:1]])
    sk = [Fill(P, (0.13, 0.15, 0.24), 0.2, 12, 5, 0.0, seed + 1, knock=C.KNOCK, base=0.55, name="balloon.fill"),
          Stroke(Q, col, lw, a, seed + 2, "balloon")]
    for j in range(lines):
        yy = y - ry * 0.5 + j * ry * 1.0 / max(1, lines - 1)
        half = rx * 0.68 * math.sqrt(max(0.05, 1 - ((yy - y) / ry) ** 2)) * (0.75 + 0.25 * rnd(seed + j, 5))
        q = np.linspace(-half, half, 26)
        zz = (np.arange(26) % 2 * 2 - 1) * ry * 0.075 * (0.6 + 0.8 * htab(np.arange(26), 7, seed + j * 31))
        sk.append(Stroke(np.stack([x + q, yy + zz], axis=1), col, lw * 0.75, a * 0.85, seed + 10 + j, f"line{j}", wob=0.5, step=4.0))
    return Sketch(sk, name)


# --------------------------------------------------------------------------
# the plain, the hills
# --------------------------------------------------------------------------
def plain_ground(F: Frame, hy, x0=-40.0, x1=1960.0, bottom=1120.0, a=1.0, col=C.CHALK_DIM, haze=1.0, seed=31):
    """A vast empty ground below the horizon at world y = hy, from x0 to x1 down to `bottom`: mist
    along the horizon, the horizon line, a few contour lines, tufts and stones that grow toward the viewer."""
    wd, mx = x1 - x0, (x0 + x1) / 2
    k = wd / 2000.0
    gpoly = A((x0, hy + 8), (x1, hy + 8), (x1, bottom), (x0, bottom), (x0, hy + 8))
    hatch(F, gpoly, (0.20, 0.25, 0.40), 0.10, 44, 15, 0.30 * a, seed + 20, grain="sparse", wob=2.4, clip=True, boil=False, jit=0.8)
    hatch(F, gpoly, (0.11, 0.14, 0.23), -0.06, 70, 22, 0.40 * a, seed + 21, grain="sparse", wob=2.4, clip=True, boil=False, jit=0.8)
    smudge(F, mx, hy - 10, wd * 0.72, 150, (0.30, 0.37, 0.56), 0.50 * haze, "soft", power=1.5)
    smudge(F, mx, hy + 6, wd * 0.67, 46, (0.42, 0.50, 0.70), 0.32 * haze, "soft", power=1.2)
    xs = np.linspace(x0 + 10, x1 - 10, int(40 * k) + 2)
    ys = hy + 5 * np.sin(xs * 0.004 + 1.0) + 3 * np.sin(xs * 0.013)
    chalk(F, np.stack([xs, ys], axis=1), col, 4.6, 0.95 * a, seed, wob=1.3, taper=0.6)
    for j, (d, u0, u1) in enumerate(((34, 0.06, 0.40), (58, 0.54, 0.93), (104, 0.17, 0.77), (176, 0.0, 0.47), (250, 0.51, 1.0))):
        xx = np.linspace(x0 + wd * u0, x0 + wd * u1, 16)
        yy = hy + d + 5 * np.sin(xx * 0.006 + j * 2.0) + 0.012 * d * np.sin(xx * 0.02 + j)
        chalk(F, np.stack([xx, yy], axis=1), C.CHALK_FAR, 2.6 + 0.01 * d, a * 0.5, seed + 1 + j, wob=1.6, taper=0.2, edge=0.2)
    i = np.arange(int(70 * k))
    dep = htab(i, 7, seed * 131) ** 1.7
    gx = x0 + htab(i, 11, seed * 137) * wd
    gy = hy + 14 + dep * 330
    sz = 5 + 20 * dep
    for q in range(3):
        dx = (q - 1) * sz * 0.45
        dashes(F, gx + dx * 0.4, gy, gx + dx, gy - sz * (1.0 - 0.25 * abs(q - 1)), 2.0, C.CHALK_FAR, a * 0.7, "mid")
    j = np.arange(int(26 * k))
    dep = htab(j, 5, seed * 151) ** 1.5
    px = x0 + 40 + htab(j, 13, seed * 139) * (wd - 80)
    py = hy + 20 + dep * 320
    ws, al = F.lw(2.0, 0.55 * a, 1.2)
    p = skia.Path()
    for x_, y_, d_ in zip(px, py, dep):
        l_, t_ = F.cam.to_screen(x_, y_)
        p.addOval(skia.Rect.MakeXYWH(float(l_), float(t_), float(F.cam.s(8 + 16 * d_)), float(F.cam.s(4 + 6 * d_))))
    F.c.drawPath(p, F.pen(C.CHALK_FAR, ws, al, "mid"))


def footprints(F: Frame, x0, x1, y, n=12, a=0.6, col=C.CHALK_DIM, s=1.0):
    """The way already walked: small paired marks from x0 to x1 along world y, fading toward the past."""
    i = np.arange(n)
    xs = x0 + (x1 - x0) * (i + 0.5) / n
    ys = y + 3 * s * (i % 2 * 2 - 1) + 2 * np.sin(i * 1.3)
    for x_, y_, a_ in zip(xs, ys, np.linspace(0.25, 1.0, n)):
        fill(F, blob(x_ + 5.5 * s, y_ + 2.1 * s, 5.5 * s, 2.1 * s, 0, 0.0, 14), col, a * a_, "mid")


def under(curve, bottom):
    """The closed outline of everything under a curve, down to world y = bottom."""
    return np.vstack([curve, [(curve[-1, 0], bottom), (curve[0, 0], bottom), curve[0]]])


def hill(F: Frame, curve, bottom=1100.0, seed=641, ang=0.5, front=False, c1=C.GREEN, c2=C.GREEN_DEEP,
         night=(0.18, 0.23, 0.36)):
    """A hill: everything under the world curve (N, 2), coloured in. Night skin: a dark rubbed mass with
    a chalk contour; day skin: green crayon (c1 over c2). front: the nearest hill (brighter contour at
    night, an extra lime zigzag by day). The zigzags are seated."""
    poly = under(curve, bottom)
    if F.day:
        fill(F, poly, C.DAY, 0.96)
        fill(F, poly, c1, 0.55, "mid")
        hatch(F, poly, c1, ang, 24, 15, 0.85, seed, grain="mid", wob=3.0, clip=True, jit=0.9)
        hatch(F, poly, c2, ang + 0.9, 46, 10, 0.34, seed + 1, grain="sparse", wob=3.0, clip=True, jit=0.9)
        if front:
            hatch(F, poly, C.LIME, 0.25, 64, 18, 0.40, seed + 3, grain="sparse", wob=3.0, clip=True, jit=0.9)
        chalk(F, curve, C.GREEN_DEEP, 5.5, 0.95, seed + 2, wob=1.4, edge=0.2)
    else:
        fill(F, poly, C.KNOCK, 0.94)
        fill(F, poly, night, 0.5, "mid")
        hatch(F, poly, mix(night, C.CHALK_DIM, 0.35), ang, 30, 8, 0.38, seed, grain="sparse", wob=3.0, clip=True, jit=0.9)
        chalk(F, curve, C.CHALK_COOL if front else C.CHALK_DIM, 4.6, 0.95, seed + 2, wob=1.4)


def tree(F: Frame, x, y, t=None, seed=691):
    """A child's tree standing on (x, y): trunk, a round crown with a scribble in it; by day green
    with red apples. Its scribble sways a little (t: its clock, default the stepped time)."""
    t = F.tb if t is None else t
    day = F.day
    pen = C.PENCIL if day else C.CHALK_DIM
    trunk = A((x - 20, y), (x - 12, y - 190), (x + 14, y - 190), (x + 24, y), (x - 20, y))
    if day:
        fill(F, trunk, (0.62, 0.38, 0.18), 0.9, "mid")
        hatch(F, trunk, (0.42, 0.24, 0.10), 1.5, 9, 4, 0.7, seed, grain="mid", clip=True)
    else:
        fill(F, trunk, C.KNOCK, 0.95)
        hatch(F, trunk, C.CHALK_FAR, 1.5, 10, 4, 0.6, seed, grain="mid", clip=True)
    chalk(F, trunk[:2], pen, 4.4, 0.95, seed + 1, wob=1.0)
    chalk(F, trunk[2:4], pen, 4.4, 0.95, seed + 2, wob=1.0)
    cx, cy = x + 4, y - 300
    crown = blob(cx, cy, 170, 140, seed + 3, 0.10, 40)
    if day:
        fill(F, crown, C.DAY, 0.9)
        fill(F, crown, C.GREEN, 0.6, "mid")
    else:
        fill(F, crown, C.KNOCK, 0.6)
        hatch(F, crown, (0.20, 0.25, 0.39), 0.7, 22, 9, 0.5, seed + 4, grain="sparse", wob=2.0, clip=True)
    chalk(F, np.vstack([crown, crown[1:4]]), C.GREEN_DEEP if day else C.CHALK_DIM, 5.0, 0.9, seed + 5, wob=1.6, edge=0.2)
    u = np.arange(0, 2 * math.pi * 26, 0.3) + 50.0
    S_ = scribble_pts(u, 77)
    lp = np.stack([cx + S_[:, 0] * 118, cy + S_[:, 1] * 135 + 6 * np.sin(t * 1.1 + u * 0.05)], axis=1)
    scrib(F, lp, C.GREEN_DEEP if day else C.CHALK_FAR, 6.0, 0.85, "mid")
    scrib(F, lp[::-1][:300] + (6, -4), C.LIME if day else C.CHALK_DIM, 3.4, 0.7, "mid")
    if day:
        for j in range(7):
            ax, ay = cx + 120 * rsym(j, 41), cy + 100 * rsym(j, 42)
            disc(F, ax, ay, 11, C.RED, 0.95, "dense")
            scrib(F, blob(ax, ay, 11, 11, 0, 0.0, 16), C.PENCIL, 2.0, 0.6, "mid")


def flower(F: Frame, x, y, h, col, seed=0, a=1.0, sway=0.0, stem=C.GREEN_DEEP):
    """An open flower h tall growing from the world point (x, y) (day skin)."""
    top = np.array([x + sway * h * 0.25, y - h])
    chalk(F, spline(A((x, y), (x + sway * h * 0.05 + h * 0.06 * rsym(seed, 1), y - h * 0.5), top), 8), stem, h * 0.045, a,
          seed, wob=0.3, taper=0.6, edge=0.15, step=4.0)
    r = h * 0.16
    n = 5 + int(rnd(seed, 2) * 3)
    for j in range(n):
        an = j * 2 * math.pi / n + rnd(seed, 3) * 3
        c_ = top + r * 0.9 * np.array([math.cos(an), math.sin(an)])
        fill(F, blob(c_[0], c_[1], r * 0.62, r * 0.62, seed + j, 0.12, 10), col, 0.92 * a, "mid")
    disc(F, top[0], top[1], r * 0.45, C.SUN, a, "dense")


def bud(F: Frame, x, y, h, seed=0, a=0.9, sway=0.0):
    """A flower not yet open (night skin): a pale stem and a dot."""
    top = (x + sway * h * 0.25, y - h)
    chalk(F, spline(A((x, y), (x + sway * h * 0.05, y - h * 0.5), top), 8), C.CHALK_FAR, h * 0.04, a, seed, wob=0.3, taper=0.6,
          edge=0.15, step=4.0)
    disc(F, top[0], top[1], h * 0.09, C.CHALK_DIM, a, "dense", floor=1.0)


def grass(F: Frame, l, r, y, n, col, seed=0, hmin=8.0, hmax=26.0, w=2.2, a=0.9, yj=0.0, lean=0.0):
    """n blades between world x = l and r, rooted about y (scattered by +-yj), hmin..hmax tall."""
    i = np.arange(n)
    x = l + htab(i, 7, seed * 131) * (r - l)
    hh = hmin + (hmax - hmin) * htab(i, 11, seed * 137 + 3)
    yy = y + yj * (2 * htab(i, 5, seed * 151 + 1) - 1)
    dx = (lean + 0.5 * (2 * htab(i, 13, seed * 139 + 7) - 1)) * hh
    dashes(F, x, yy, x + dx, yy - hh, w, col, a, "mid")


def tear_outline(x0=1000.0, x1=1850.0, y0=120.0, y1=215.0, hw=92.0, seed=5, open_=1.0):
    """A rip in the sheet from (x0, y0) to (x1, y1): a wandering gash, widest in the middle (half width
    hw * open_), with a ragged fibrous edge. Returns the closed world outline (see day.tear_light)."""
    n = 54
    q = np.linspace(0.0, 1.0, n)
    xs = x0 + (x1 - x0) * q
    mid = y0 + (y1 - y0) * q + 34 * (2 * vn(q * 3.1, seed) - 1)
    prof = hw * open_ * np.sin(np.pi * q) ** 0.6
    rag = np.minimum(1.0, prof / 30.0)
    up = mid - prof * (0.7 + 0.6 * vn(q * 6.3, seed + 1)) - 13 * rag * (2 * vn(q * 31, seed + 2) - 1)
    dn = mid + prof * (0.7 + 0.6 * vn(q * 5.1, seed + 3)) + 13 * rag * (2 * vn(q * 37, seed + 4) - 1)
    xu = xs + 9 * rag * (2 * vn(q * 29, seed + 5) - 1)
    xd = xs + 9 * rag * (2 * vn(q * 33, seed + 6) - 1)
    return np.vstack([np.stack([xu, up], axis=1), np.stack([xd, dn], axis=1)[::-1]])
