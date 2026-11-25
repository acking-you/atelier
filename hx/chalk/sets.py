"""hx.chalk.sets: the indoor sets of the film, as canonical named-stroke sets.

The room (night, evening, warm sunset), the classroom from the back, the home table, the corridor,
and the declared changes between them. Every scene that shows one of these places builds it here, so
that it is the same place every time (same anchors, same seeds, same hand).

A set is three things, drawn in this order:

    S = room("night")                  # a Place: named groups (Sketch) in paint order
    S.back(F)                          # the seated dressing: wall tone and hatch, floor (never the ground line)
    ...light (hx.chalk.weather) ...    # pools, halos: see hx/chalk/doc/sets.md for where and how big
    S.view(F)                          # what the window shows (roofs, the wire, the one amber window)
    ground_line(F)                     # the one ground line: always the scene's, never the set's
    S.draw(F)                          # every group, or S.draw(F, "wall", "window") / S["sofa"].draw(F)

World coordinates through F.cam; anchors from hx/story.py. Nothing here imports another artist's module.

Every builder and every change takes dx: the set stands at its own coordinates + dx (the evening room
at story.ROOM2_DX, the coda's at story.ROOM3_DX). S.dx is that offset; S.rect(PANE), S.pt(FAR_WINDOW)
shift an anchor of this file to where the set stands.
"""
from __future__ import annotations

import math

import numpy as np
import skia

from .. import story
from .core import A, C, H, W, Frame, arc, blob, chalk, ease, fill, hand, hatch, mix, ramp, rect_pts, rnd, rrect_pts, rsym, seg, smudge, spline, wash, zigzag
from .sketch import Fill, Sketch, Stroke, morph

__all__ = [
    # the Place, moods
    "Place", "Change", "Mood", "MOODS",
    # the room
    "room", "room_on", "room_on_coda", "ROOM_ON", "ROOM_CODA", "room_wall", "room_floor", "room_shade", "window_view", "wire_pts", "wire_y",
    "PANE", "FAR_WINDOW", "WIRE_ENDS", "WIRE_SAG", "LAMP_SHADE", "WALL_X", "WALL_LINE_X", "TOP_Y", "SKIRT_Y", "CORNICE_Y",
    "sofa", "cushion", "window", "rug", "lamp", "chair", "table3", "shelf",
    # the classroom
    "classroom", "class_back", "board", "door", "desk", "CLASS_BOARD", "CLASS_DOOR", "CLASS_DESK", "CLASS_DESK_S", "CLASS_DESK_TOP_Y",
    "CLASS_CHAIR", "CLASS_DESK_R", "CLASS_CHAIR_R", "CLASS_CLOCK", "CLASS_DADO_Y", "CLASS_ROWS", "CLASS_LAMPS",
    # the home table
    "home_table", "home_back", "home_anchors", "HOME_X", "HOME_TABLE", "HOME_LAMP", "HOME_CHAIR_S", "HOME_SLIDE",
    # the corridor
    "corridor", "corridor_back", "corridor_view", "COR_BASE_Y", "COR_EDGE_Y", "COR_X", "COR_LINE_X", "COR_CORNER_X", "COR_WINDOW", "COR_LOCKERS",
    "COR_HOOKS", "COR_LAMPS",
    # the changes
    "between", "room_to_class", "class_to_home", "home_to_bare", "plain_to_room", "room_to_corridor", "corridor_to_bare",
    "ROOM_TO_CLASS", "ROOM_TO_CLASS_R", "CLASS_TO_HOME", "PLAIN_TO_ROOM", "ROOM_TO_CORRIDOR",
    "SPAN_ROOM_TO_CLASS", "SPAN_CLASS_TO_HOME", "SPAN_HOME_TO_BARE", "SPAN_PLAIN_TO_ROOM", "SPAN_ROOM_TO_CORRIDOR", "SPAN_CORRIDOR_TO_BARE",
]

FLOOR = story.FLOOR
WINDOW = story.WINDOW

# ---------------------------------------------------------------------------------------------
# small builders
# ---------------------------------------------------------------------------------------------
def _ln(x0, y0, x1, y1, col, w, a, seed, name, **kw) -> Stroke:
    return Stroke(A((x0, y0), (x1, y1)), col, w, a, seed, name, **kw)


def _cl(P, col, w, a, seed, name, **kw) -> Stroke:
    """A closed outline that overshoots its start a little, as a child closes a shape."""
    P = np.asarray(P, dtype=np.float64)
    n = max(2, len(P) // 12)
    return Stroke(np.vstack([P, P[1:n + 1]]), col, w, a, seed, name, **kw)


def _poly(*pts):
    """Closed polygon through the points (first point repeated)."""
    P = np.asarray(pts, dtype=np.float64)
    return np.vstack([P, P[:1]])


def _marks(F: Frame, polys, col, w, a, grain="mid", floor=1.2, draw=1.0):
    """Seated dressing: many polylines (world points) in ONE path. They do not boil. draw = 0..1:
    how many of them exist yet (in list order); the one being ruled in exists up to its tip.
    Lines the camera does not see are left out."""
    if a <= 0.003 or draw <= 0.0 or not polys:
        return
    nf = len(polys) * min(1.0, float(draw))
    n = int(nf)
    ws, a = F.lw(w, a, floor)
    cam = F.cam
    box = _BOX.get(id(polys))
    if box is None:
        box = _BOX[id(polys)] = (polys, np.array([[P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max()] for P in polys]))
    vl, vt, vr, vb = cam.view(ws + 4.0)
    b = box[1]
    seen = (b[:, 2] >= vl) & (b[:, 0] <= vr) & (b[:, 3] >= vt) & (b[:, 1] <= vb)
    p = skia.Path()
    for i in np.flatnonzero(seen[:n]).tolist():
        S = cam.pts(polys[i]).tolist()
        p.moveTo(*S[0])
        for x, y in S[1:]:
            p.lineTo(x, y)
    if n < len(polys) and nf - n > 0.02 and seen[n]:
        P = polys[n]
        u = (nf - n) * (len(P) - 1)
        k = int(u)
        tip = P[k] + (P[min(k + 1, len(P) - 1)] - P[k]) * (u - k)
        S = cam.pts(np.vstack([P[:k + 1], tip[None, :]])).tolist()
        p.moveTo(*S[0])
        for x, y in S[1:]:
            p.lineTo(x, y)
    if not p.isEmpty():
        F.c.drawPath(p, F.pen(col, ws, a, grain))


_BOX: dict = {}                  # id(list of polylines) -> (the list, their world boxes); the lists live in _GEO
_ZIG: dict = {}                  # seated zigzags of the wide dressing, with their hand


def _seat_hatch(F: Frame, rect, col, ang, gap, w, a, seed, grain="sparse", wob=2.2):
    """A seated zigzag over a wide world rectangle (l, t, r, b), kept inside it: what
    hatch(clip=True, boil=False) draws, but the zigzag and its hand are built once and only the
    rows the camera sees are painted (the walls reach far past any framing)."""
    if a <= 0.003:
        return
    cam = F.cam
    z = cam.zoom
    l, t, r, b = rect
    sl, st = cam.to_screen(l, t)
    sr, sb = cam.to_screen(r, b)
    if sr < 0 or sl > W or sb < 0 or st > H:
        return
    # the hand of a seated line depends on the zoom only by octaves of sampling and, under 0.71, by its
    # wobble: there the hand is kept for exactly this zoom only, so that a frame never depends on another
    kz = (l, t, r, b, ang, gap, seed)
    key = kz + (wob, round(math.log2(1.0 / z)) if not 0.71 < z < 1.41 else 0, z if z < 0.71 else 0.71)
    Q = _ZIG.get(key)
    if Q is None:
        Z = _ZIG.get(kz)
        if Z is None:
            Z = zigzag(rect_pts(l, t, r, b), ang + 0.05 * rsym(seed, 9), gap, seed)
            if Z is None:
                return
        if len(_ZIG) > 64:
            _ZIG.clear()
        _ZIG[kz] = Z
        Q = _ZIG[key] = hand(Z, seed + 17, 0, wob, max(5.0, gap * 1.2), 0.0, z)[0]
    ws, a = F.lw(w, a, 1.0)
    S = cam.pts(Q)
    m = ws + 2.0
    x0, y0 = np.minimum(S[:-1, 0], S[1:, 0]), np.minimum(S[:-1, 1], S[1:, 1])
    x1, y1 = np.maximum(S[:-1, 0], S[1:, 0]), np.maximum(S[:-1, 1], S[1:, 1])
    seen = (x1 >= -m) & (x0 <= W + m) & (y1 >= -m) & (y0 <= H + m)
    if not seen.any():
        return
    idx = np.flatnonzero(seen)
    cut = np.flatnonzero(np.diff(idx) > 1)
    starts, ends = np.concatenate([[idx[0]], idx[cut + 1]]), np.concatenate([idx[cut], [idx[-1]]])
    pts = S.tolist()
    p = skia.Path()
    for i0, i1 in zip(starts.tolist(), ends.tolist()):
        p.moveTo(*pts[i0])
        for x, y in pts[i0 + 1:i1 + 2]:
            p.lineTo(x, y)
    c = F.c
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(float(sl), float(st), float(sr), float(sb)), skia.ClipOp.kIntersect, True)
    c.drawPath(p, F.pen(col, ws, a, grain))
    c.restore()


_GEO: dict = {}                  # seated geometry is a pure function of its arguments: built once


def _seated(P, seed, wob=1.0, step=9.0):
    """A polyline with the hand's static wobble baked in (no boil)."""
    return hand(np.asarray(P, dtype=np.float64), seed, 0, wob, step, 0.0, 1.0)[0]


# ---------------------------------------------------------------------------------------------
# moods: the colours of a set at one time of day
# ---------------------------------------------------------------------------------------------
class Mood:
    def __init__(self, name, **kw):
        self.name = name
        self.__dict__.update(kw)


def _grey(c, w, g=(0.34, 0.37, 0.45)):
    return mix(c, g, w)


_NIGHT = dict(day=False, near=C.CHALK_COOL, mid=C.CHALK_DIM, far=C.CHALK_FAR, knock=C.KNOCK, dark=C.PAPER_DEEP,
              sofa=(0.22, 0.28, 0.45), seat=(0.30, 0.37, 0.56), cushion=(0.36, 0.40, 0.58), throw=(0.44, 0.50, 0.66),
              rug=(0.30, 0.35, 0.52), rug2=(0.42, 0.48, 0.65), curtain=(0.24, 0.29, 0.45), shade=(0.30, 0.35, 0.50),
              wood=(0.20, 0.24, 0.37), cloth=(0.40, 0.45, 0.61), book=((0.30, 0.36, 0.54), (0.22, 0.27, 0.42), (0.40, 0.45, 0.60)),
              wall_a=(0.21, 0.26, 0.41), wall_b=(0.13, 0.16, 0.26), wall_ang=1.12, wall_k=1.0, corner=0.55,
              board_line=C.CHALK_FAR, board_a=0.24, lit=0.0)
MOODS = {
    "night": Mood("night", **_NIGHT),
    "eve": Mood("eve", **{**_NIGHT, **dict(
        sofa=_grey((0.22, 0.28, 0.45), 0.35), seat=_grey((0.30, 0.37, 0.56), 0.35), cushion=_grey((0.36, 0.40, 0.58), 0.3),
        throw=_grey((0.44, 0.50, 0.66), 0.3), rug=_grey((0.30, 0.35, 0.52), 0.35), rug2=_grey((0.42, 0.48, 0.65), 0.3),
        curtain=_grey((0.27, 0.32, 0.47), 0.35), shade=_grey((0.30, 0.35, 0.50), 0.3), wood=_grey((0.20, 0.24, 0.37), 0.3),
        cloth=_grey((0.40, 0.45, 0.61), 0.3), wall_a=(0.27, 0.31, 0.42), wall_b=(0.17, 0.20, 0.29), wall_ang=1.32,
        wall_k=0.9, corner=0.25)}),
    "day": Mood("day", **{**_NIGHT, **dict(
        wall_a=(0.30, 0.35, 0.48), wall_b=(0.19, 0.23, 0.34), wall_ang=1.40, wall_k=1.0, corner=0.2)}),
    "sunset": Mood("sunset", day=True, near=C.PENCIL, mid=mix(C.PENCIL, C.EVE_PAPER, 0.18), far=mix(C.PENCIL, C.EVE_PAPER, 0.45),
                   knock=C.DAY, dark=C.SHADOW,
                   sofa=C.SEA, seat=mix(C.SEA, C.CREAM, 0.35), cushion=C.MUSTARD, throw=C.CORAL,
                   rug=C.ROSE, rug2=C.EVE_LOW, curtain=mix(C.CREAM, C.ROSE, 0.35), shade=C.SUN_CORE,
                   wood=mix(C.MUSTARD, C.PENCIL, 0.38), cloth=C.CREAM, book=(C.CORAL, C.SEA, C.LILAC),
                   wall_a=C.EVE_MID, wall_b=C.ROSE, wall_ang=1.12, wall_k=1.0, corner=0.3,
                   board_line=mix(C.EVE_LOW, C.PENCIL, 0.45), board_a=0.34, lit=1.0),
}


MOODS["evening"] = MOODS["eve"]                       # the weather's name for the same time of day


def _mood(m) -> Mood:
    return m if isinstance(m, Mood) else MOODS[m]


# ---------------------------------------------------------------------------------------------
# the Place: named groups in paint order, with its seated dressing
# ---------------------------------------------------------------------------------------------
class Place(dict):
    """Named groups (each a Sketch) in paint order. S["sofa"] is a group; S.all() is everything as
    one Sketch; S.draw(F) paints all groups, S.draw(F, "wall", "window") only those. S.back(F) and
    S.view(F) paint what is not strokes (wall and floor dressing; the view through the window).
    S.cues holds (t0, t1) spans for the dressing when a draw-on schedule has been applied.
    S.dx: where the set stands (world x added to every coordinate of this file); S.rect / S.pt shift
    an anchor of this file by it."""

    def __init__(self, kind: str, mood, groups, back=None, view=None):
        super().__init__(groups)
        self.kind, self.mood, self.cues, self.dx = kind, _mood(mood), {}, 0.0
        self._back, self._view = back, view

    def at(self, dx: float) -> "Place":
        """Move the whole set dx world units to the right (strokes, dressing and view). Returns self."""
        dx = float(dx)
        if dx:
            for k in list(self.keys()):
                self[k] = self[k].place(dx, 0.0)
            self.dx += dx
        return self

    def rect(self, r):
        """An (l, t, r, b) anchor of this file (PANE, WINDOW, CLASS_BOARD ...) where this set stands."""
        return (r[0] + self.dx, r[1], r[2] + self.dx, r[3])

    def pt(self, p):
        """An anchor whose first number is a world x (a point, FAR_WINDOW, CLASS_CLOCK ...) where this set stands."""
        return (p[0] + self.dx,) + tuple(p[1:])

    def all(self, *names) -> Sketch:
        """The groups (all, or the named ones) as one Sketch in paint order (same objects)."""
        return Sketch([self[k] for k in (names or self.keys())])

    def draw(self, F: Frame, *names, **kw) -> None:
        for k in (names or self.keys()):
            self[k].draw(F, **kw)

    def cue(self, name: str, t: float, default: float = 1.0) -> float:
        """Progress 0..1 of a dressing cue at time t (1 when no schedule was applied)."""
        c = self.cues.get(name)
        return default if c is None else seg(t, *c)

    def back(self, F: Frame, a: float = 1.0) -> None:
        """The seated dressing behind everything: wall and floor (not the ground line)."""
        if self._back is not None:
            with F.place(self.dx, 0.0):
                self._back(F, self, a)

    def view(self, F: Frame, a: float = 1.0, wire=None, **kw) -> None:
        """What the window shows. Draw it after the light and before the strokes. wire: the wire's
        world polyline (wire_pts(dx=S.dx)) when it dips and swings."""
        if self._view is not None:
            if wire is not None and self.dx:
                wire = np.asarray(wire, dtype=np.float64) - (self.dx, 0.0)
            with F.place(self.dx, 0.0):
                self._view(F, self, a, wire=wire, **kw)


# ---------------------------------------------------------------------------------------------
# the window and what it shows
# ---------------------------------------------------------------------------------------------
PANE = (WINDOW[0] + 7.0, WINDOW[1] + 7.0, WINDOW[2] - 7.0, WINDOW[3] - 7.0)      # the glass: rain on the pane goes here
FAR_WINDOW = (WINDOW[0] + 271.0, WINDOW[3] - 112.0, 56.0, 70.0)                # the friend's window: centre x, centre y, w, h
WIRE_ENDS = ((WINDOW[0] - 14.0, WINDOW[1] + 90.0), (WINDOW[2] + 14.0, WINDOW[1] + 108.0))   # the wire's two fixings
WIRE_SAG = 20.0                                       # how deep the wire hangs in the middle
LAMP_SHADE = (story.LAMP_X, FLOOR - 459.0)            # middle of the standing lamp's shade (its glow in the coda)


def wire_pts(sag: float = WIRE_SAG, dips=(), n: int = 28, dx: float = 0.0):
    """The wire under the eaves outside the window, as a world polyline (n, 2).
    sag: how deep it hangs in the middle; dips: [(x, depth, reach=60), ...] local pulls downward
    (a crow landing at world x pushes it down by `depth`), to animate the swing. dx: where the room
    stands (the dips' x are world x too)."""
    (xa, ya), (xb, yb) = WIRE_ENDS
    u = np.linspace(0.0, 1.0, n)
    x = xa + dx + (xb - xa) * u
    y = ya + (yb - ya) * u + sag * 4.0 * u * (1.0 - u)
    for d in dips:
        reach = d[2] if len(d) > 2 else 60.0
        k = np.clip(1.0 - np.abs(x - d[0]) / reach, 0.0, 1.0)
        y = y + d[1] * k * k * (3.0 - 2.0 * k) * np.minimum(1.0, 6.0 * u * (1.0 - u))
    return np.stack([x, y], axis=1)


def wire_y(x, sag: float = WIRE_SAG, dips=(), dx: float = 0.0):
    """World y of the wire at world x (scalar or array)."""
    P = wire_pts(sag, dips, 60, dx)
    return np.interp(x, P[:, 0], P[:, 1])


def _roofs(l, t, r, b):
    """Silhouettes outside the window, in world points: far row, the two houses across the street."""
    ry = b - 150.0
    far = A((l - 12, ry + 6), (l + 6, ry + 6), (l + 6, ry - 20), (l + 22, ry - 20), (l + 22, ry - 2), (l + 60, ry - 30), (l + 100, ry + 2),
            (l + 128, ry + 2), (l + 128, ry - 34), (l + 142, ry - 34), (l + 142, ry - 16), (l + 176, ry - 40), (l + 214, ry - 12),
            (l + 236, ry - 12), (l + 250, ry - 30), (l + 300, ry - 30), (l + 318, ry - 4), (l + 352, ry - 26), (r + 12, ry - 2),
            (r + 12, b + 6), (l - 12, b + 6))
    left = A((l - 12, ry + 58), (l + 6, ry + 58), (l + 6, ry + 34), (l + 66, ry - 18), (l + 108, ry + 18), (l + 108, ry + 4), (l + 124, ry + 4),
             (l + 124, ry + 32), (l + 140, ry + 46), (l + 140, ry + 62), (l + 158, ry + 62), (l + 158, b + 6), (l - 12, b + 6))
    right = A((l + 186, b + 6), (l + 186, ry + 30), (l + 172, ry + 30), (l + 272, ry - 46), (l + 304, ry - 22), (l + 304, ry - 52), (l + 324, ry - 52),
              (l + 324, ry - 6), (r + 12, ry + 34), (r + 12, b + 6))
    return far, left, right


_SKY = {"night": ((0.12, 0.15, 0.25), (0.30, 0.38, 0.60), 0.55), "eve": ((0.40, 0.44, 0.54), (0.66, 0.68, 0.72), 0.55),
        "day": ((0.44, 0.50, 0.62), (0.72, 0.76, 0.82), 0.6)}
_HOUSE = {"night": ((0.075, 0.09, 0.15), (0.10, 0.125, 0.205), C.CHALK_FAR), "eve": ((0.13, 0.155, 0.24), (0.22, 0.25, 0.35), C.CHALK_DIM),
          "day": ((0.16, 0.19, 0.29), (0.27, 0.31, 0.42), C.CHALK_DIM),
          "sunset": (mix(C.SHADOW, C.PENCIL, 0.06), mix(C.SHADOW, C.EVE_MID, 0.50), C.PENCIL)}


def window_view(F: Frame, mood="night", a: float = 1.0, lit: float = 1.0, wire=None, rect=WINDOW, eave: float = 1.0):
    """What the window shows: sky, a far row of roofs, two houses across the street, in the right one
    the ONE lit amber window (FAR_WINDOW), our own eave at the top and the wire under it.

    mood: "night" (dark, a pale cloud), "eve" (flat pale grey), "day" (the classroom's grey day),
    "sunset" (the coda: pastel sky on warm paper). a: 0..1 fades the whole view in (the pane fills
    once its frame stands). lit: 0..1 the amber window being coloured in. wire: its world polyline
    (default wire_pts(): pass your own to make it dip and swing); rect: the window (l, t, r, b).
    Rain, drops on the glass, crows and the figure in the far window are not drawn here."""
    if a <= 0.003:
        return
    m = _mood(mood)
    l, t, r, b = rect
    dx, dy = l - WINDOW[0], t - WINDOW[1]
    c = F.c
    sl, st = F.cam.to_screen(l, t)
    sr, sb = F.cam.to_screen(r, b)
    if sr < 0 or sl > F.w or sb < 0 or st > F.h:
        return
    layer = a < 0.999
    if layer:
        c.saveLayerAlpha(skia.Rect.MakeLTRB(sl - 2, st - 2, sr + 2, sb + 2), int(255 * a))
    with F.clip(rect=(l, t, r, b)):
        ry = b - 150.0
        far, left, right = _roofs(l, t, r, b)
        cdark, cfar, cline = _HOUSE[m.name]
        if m.day:
            fill(F, rect_pts(l, t, r, b), C.CREAM, 0.55)
            wash(F, rect_pts(l, t, r, b), C.EVE_HI, t, ry + 20, [0.85, 0.55, 0.12, 0.0], "soft")
            wash(F, rect_pts(l, t, r, b), C.EVE_MID, t + 60, ry + 40, [0.0, 0.5, 0.8, 0.5], "soft")
            wash(F, rect_pts(l, t, r, b), C.EVE_LOW, ry - 110, ry + 60, [0.0, 0.35, 0.85], "soft")
            smudge(F, l + 160, ry + 4, 120, 80, C.SUN_CORE, 0.85, "glow", power=1.5)
            _marks(F, _geo_sky(l, t, r, b), C.ROSE, 9.0, 0.55, "sparse")
        else:
            sky, pale, k = _SKY[m.name]
            fill(F, rect_pts(l, t, r, b), C.PAPER_DEEP, 0.92)
            if m.name == "night":
                fill(F, rect_pts(l, t, r, b), sky, 0.75, "mid")
                smudge(F, (l + r) / 2 + 70, t + 110, 250, 150, pale, k, "soft", power=1.3)
                smudge(F, (l + r) / 2, ry - 6, 300, 64, (0.34, 0.42, 0.64), 0.55, "soft", power=1.2)
                _marks(F, _geo_sky(l, t, r, b), (0.36, 0.44, 0.66), 10.0, 0.22, "sparse")
            else:
                fill(F, rect_pts(l, t, r, b), sky, 0.95, "glow")
                wash(F, rect_pts(l, t, r, b), pale, t + 40, ry + 30, [0.0, 0.35, 0.75], "soft")
                _marks(F, _geo_sky(l, t, r, b), pale, 12.0, 0.30, "sparse")
        # the far row: lighter, further
        fill(F, far, cfar, 0.92, "dense")
        # the two houses across the street
        for P in (left, right):
            fill(F, P, cdark, 0.96, "dense")
        chalk(F, left[1:11], cline, 2.8, 0.9, 71, wob=0.6, boil=0.0)
        chalk(F, right[1:9], cline, 2.8, 0.95, 74, wob=0.6, boil=0.0)
        # a dark window in the left house
        fill(F, rect_pts(l + 44, ry + 44, l + 74, ry + 80), mix(cdark, cline, 0.38), 0.8, "mid")
        chalk(F, A((l + 59, ry + 44), (l + 59, ry + 80)), cdark, 2.0, 0.9, 75, wob=0.0, edge=0.0, boil=0.0)
        # the friend's window: the one warm thing
        fx, fy, fw, fh = FAR_WINDOW[0] + dx, FAR_WINDOW[1] + dy, FAR_WINDOW[2], FAR_WINDOW[3]
        wr = rect_pts(fx - fw / 2, fy - fh / 2, fx + fw / 2, fy + fh / 2)
        chalk(F, np.vstack([wr, wr[1:2]]), mix(cdark, cline, 0.5), 2.2, 0.8, 76, wob=0.4, edge=0.0, boil=0.0)
        if lit > 0.0:
            g = ease(seg(lit, 0.35, 1.0))
            if m.day:
                smudge(F, fx, fy, 105, 96, C.AMBER_GLOW, 0.50 * g, "glow", power=1.5)
            else:
                smudge(F, fx, fy, 112, 100, C.AMBER_GLOW, 0.42 * g, "glow", additive=True)
                smudge(F, fx, fy + 62, 60, 40, C.AMBER_DEEP, 0.16 * g, "glow", additive=True)
            hatch(F, wr, C.AMBER, 0.5, 6.0, 5.0, 0.95, 77, grain="dense", draw=min(1.0, lit * 1.6), clip=True, boil=False)
            fill(F, wr, C.AMBER, 0.95 * g, "dense")
            fill(F, rect_pts(fx - fw / 2 + 4, fy - fh / 2 + 4, fx + fw / 2 - 4, fy - 4), C.AMBER_PALE, 0.45 * g, "mid")
            chalk(F, A((fx, fy - fh / 2), (fx, fy + fh / 2)), C.AMBER_DEEP, 2.2, 0.9 * g, 73, wob=0.0, edge=0.0, boil=0.0)
            chalk(F, A((fx - fw / 2, fy - 3), (fx + fw / 2, fy - 2)), C.AMBER_DEEP, 2.0, 0.85 * g, 78, wob=0.0, edge=0.0, boil=0.0)
        # our own eave at the top (near, dark), its gutter, and the wire strung under it
        if eave > 0.0:
            ev = A((l - 12, t - 4), (r + 12, t - 4), (r + 12, t + 22), (l - 12, t + 50))
            fill(F, ev, mix(C.SHADOW, C.EVE_MID, 0.35) if m.day else mix(cdark, C.PAPER_DEEP, 0.6), (0.72 if m.day else 0.97) * eave, "dense")
            _marks(F, _geo_eave(l, t, r, b), cline, 2.2, 0.5 * eave, "mid")
            chalk(F, A((l - 12, t + 52), (r + 12, t + 24)), cline, 3.2, 0.85 * eave, 79, wob=0.6, boil=0.0)
        W_ = wire_pts() if wire is None else np.asarray(wire, dtype=np.float64)
        if dx or dy:
            W_ = W_ + (dx, dy)
        chalk(F, W_, C.PENCIL if m.day else mix(C.CHALK_DIM, C.CHALK_COOL, 0.35), 2.6, 0.95, 72, wob=0.5, taper=0.9)
    if layer:
        c.restore()


def _geo_eave(l, t, r, b):
    key = ("eave", l, t, r, b)
    if key not in _GEO:
        out = []
        for j in range(9):
            x = l + 14 + j * (r - l - 20) / 8.0 + 6 * rsym(j, 37)
            yb = t + 50 - 28 * (x - l + 12) / (r - l + 24)
            out.append(A((x + 5, t + 6), (x, yb - 5)))
        _GEO[key] = out
    return _GEO[key]


def _geo_sky(l, t, r, b):
    key = ("sky", l, t, r, b)
    if key not in _GEO:
        out = []
        for j in range(6):
            y = t + 62 + j * 26 + 10 * rsym(j, 31)
            x0 = l + (r - l) * (0.05 + 0.5 * rnd(j, 32))
            x1 = min(r + 10, x0 + (r - l) * (0.25 + 0.4 * rnd(j, 33)))
            out.append(_seated(A((x0, y), ((x0 + x1) / 2, y - 6 + 8 * rsym(j, 34)), (x1, y + 4 * rsym(j, 35))), 3100 + j, 1.4))
        _GEO[key] = out
    return _GEO[key]


def window(l=WINDOW[0], t=WINDOW[1], r=WINDOW[2], b=WINDOW[3], seed=200, col=None, curtains=True, mood="night",
           name="window") -> Sketch:
    """The window: frame, glazing bars, sill; with curtains: rail and two hanging curtains that overlap
    the frame. Parts: frame inner mullion transom sill ledge | rail curtain.l (+ .fill) curtain.l0-1
    curtain.r (+ .fill) curtain.r0-1. What it shows: window_view."""
    m = _mood(mood)
    col = m.near if col is None else col
    sk = [
        _cl(rect_pts(l, t, r, b), col, 5.5, 1.0, seed + 1, "frame"),
        _cl(rect_pts(l + 14, t + 14, r - 14, b - 14), col, 3.0, 0.72, seed + 2, "inner"),
        _ln((l + r) / 2, t + 4, (l + r) / 2 + 2, b - 4, col, 4.4, 0.95, seed + 3, "mullion"),
        _ln(l + 4, (t + b) / 2 - 14, r - 4, (t + b) / 2 - 12, col, 4.4, 0.95, seed + 4, "transom"),
        _ln(l - 28, b + 12, r + 28, b + 14, col, 6.0, 1.0, seed + 5, "sill"),
        Stroke(A((l - 20, b + 16), (l - 16, b + 30), (r + 16, b + 32), (r + 21, b + 17)), mix(col, m.mid, 0.6), 3.0, 0.75, seed + 6,
               "ledge"),
    ]
    if curtains:
        cc = mix(col, m.mid, 0.35)
        sk.append(_ln(l - 62, t - 36, r + 94, t - 33, col, 4.4, 0.9, seed + 7, "rail"))
        for side, tag, x0, wd, drop in ((-1, "l", l + 36, 82, b + 52), (1, "r", r - 14, 98, b + 44)):
            # the curtain hangs from the rail, gathered: inner edge (toward the glass) wavy, hem scalloped
            xi, xo = x0, x0 + side * wd                                  # inner and outer x at the rail
            top = t - 33
            inner = spline(A((xi, top), (xi + side * 4, top + 120), (xi - side * 10, top + 300), (xi + side * 2, drop - 60), (xi - side * 6, drop)), 14)
            hem_x = np.linspace(xi - side * 6, xo + side * 14, 9)
            hem = np.stack([hem_x, drop + 6 + 7 * np.cos(np.linspace(0, 4 * math.pi, 9))], axis=1)[1:]
            outer = spline(A((xo + side * 14, drop + 6), (xo + side * 8, top + 300), (xo + side * 2, top + 120), (xo, top)), 10)[1:]
            P = np.vstack([inner, hem, outer, inner[:1]])
            sk.append(Fill(P, m.curtain, 1.50 + side * 0.04, 15.0, 7.0, 0.55, seed + 20 + (side > 0) * 10, knock=m.knock, base=0.55,
                           name=f"curtain.{tag}.fill"))
            sk.append(_cl(P, cc, 3.8, 0.9, seed + 21 + (side > 0) * 10, f"curtain.{tag}"))
            for j, f in enumerate((0.36, 0.70)):
                xx = xi + (xo - xi) * f
                yy = np.linspace(top + 10, drop - 6 - 24 * (j == 0), 8)
                xs = xx + side * (5 + 2 * j) * np.sin(np.linspace(0.4, 3.0 + j * 0.5, 8)) + side * 8 * f * (yy - top) / (drop - top)
                sk.append(Stroke(np.stack([xs, yy], axis=1), mix(cc, m.mid, 0.5), 2.8, 0.62, seed + 23 + j + (side > 0) * 10,
                                 f"curtain.{tag}{j}"))
    return Sketch(sk, name)


# ---------------------------------------------------------------------------------------------
# the room's furniture
# ---------------------------------------------------------------------------------------------
def sofa(x=story.SOFA_X, y=FLOOR, w=story.SOFA_W, seed=100, col=None, fill=None, k=None, mood="night", throw=True,
         name="sofa") -> Sketch:
    """The sofa. x = its left end, y = the floor. Built to story.py: seat top y - 120, armrests top
    y - 184, back top y - 288 (at w = 760). Parts: back seat split arm_l arm_r roll_l roll_r leg_l leg_r
    (+ .fill), and throw (+ .fill) fringe: a blanket over the back."""
    m = _mood(mood)
    col = m.near if col is None else col
    fc = m.sofa if fill is None else fill
    k = m.knock if k is None else k
    s = w / 760.0
    aw = 104 * s
    xm = x + w * 0.5
    back = rrect_pts(x + aw * 0.45, y - 288 * s, x + w - aw * 0.45, y - 58 * s, 46 * s)
    st = spline(A((x + aw * 0.6, y - 108 * s), (x + aw * 0.6 + 26 * s, y - 120 * s), (xm - 60 * s, y - 123 * s), (xm, y - 117 * s),
                  (xm + 60 * s, y - 123 * s), (x + w - aw * 0.6 - 26 * s, y - 120 * s), (x + w - aw * 0.6, y - 108 * s)), 22)
    seat = np.vstack([st, A((x + w - aw * 0.6, y - 30 * s), (x + w - aw * 0.6 - 8 * s, y - 22 * s), (x + aw * 0.6 + 8 * s, y - 22 * s),
                               (x + aw * 0.6, y - 30 * s)), st[:1]])
    arm_l = rrect_pts(x, y - 184 * s, x + aw, y - 16 * s, 38 * s)
    arm_r = rrect_pts(x + w - aw, y - 184 * s, x + w, y - 16 * s, 38 * s)
    sk = [
        Fill(back, fc, 0.9, 15.5 * s, 6.6 * s, 0.56, seed + 1, knock=k, base=0.28, name="back.fill"),
        _cl(back, col, 4.6 * s, 0.95, seed + 2, "back"),
    ]
    if throw:
        # a blanket thrown over the back, left of the middle: a pale mass with a fringe
        tl_, tr_ = x + 150 * s, x + 330 * s
        tp = np.vstack([A((tl_, y - 292 * s), (tl_ + 60 * s, y - 297 * s), (tr_, y - 293 * s)),
                        spline(A((tr_ + 4 * s, y - 293 * s), (tr_ + 10 * s, y - 240 * s), (tr_ + 2 * s, y - 176 * s)), 6),
                        A((tr_ - 60 * s, y - 168 * s), (tl_ + 40 * s, y - 180 * s), (tl_ - 6 * s, y - 172 * s)),
                        spline(A((tl_ - 6 * s, y - 172 * s), (tl_ - 12 * s, y - 236 * s), (tl_, y - 292 * s)), 6)])
        sk += [Fill(tp, m.throw, -0.35, 12 * s, 5.5 * s, 0.6, seed + 30, knock=k, base=0.45, name="throw.fill"),
               _cl(tp, mix(col, m.mid, 0.25), 3.6 * s, 0.9, seed + 31, "throw")]
        fx = np.linspace(tl_ - 4 * s, tr_ + 2 * s, 37)
        fy = np.interp(fx, [tl_ - 6 * s, tl_ + 40 * s, tr_ - 60 * s, tr_ + 2 * s], [y - 172 * s, y - 180 * s, y - 168 * s, y - 176 * s])
        sk.append(Stroke(np.stack([fx, fy + 1 * s + (np.arange(37) % 2) * 9 * s], axis=1), mix(col, m.mid, 0.4), 2.0 * s, 0.7, seed + 32, "fringe",
                         wob=0.3, step=4.0))
    sk += [
        Fill(seat, m.seat if fill is None else mix(fc, C.CHALK_BLUE, 0.25), -0.5, 13.5 * s, 6.2 * s, 0.6, seed + 3, knock=k, base=0.34,
             name="seat.fill"),
        _cl(seat, col, 4.6 * s, 0.95, seed + 4, "seat"),
        _ln(xm, y - 116 * s, xm + 4 * s, y - 26 * s, col, 3.2 * s, 0.7, seed + 5, "split"),
        Fill(arm_l, fc, 1.1, 11 * s, 5.5 * s, 0.6, seed + 6, knock=k, base=0.36, name="arm_l.fill"),
        _cl(arm_l, col, 4.8 * s, 1.0, seed + 7, "arm_l"),
        Stroke(arc(x + aw * 0.5, y - 146 * s, 24 * s, 21 * s, 0.9, 6.6, 14), mix(col, m.mid, 0.35), 3.0 * s, 0.8, seed + 12, "roll_l"),
        Fill(arm_r, fc, 1.1, 11 * s, 5.5 * s, 0.6, seed + 8, knock=k, base=0.36, name="arm_r.fill"),
        _cl(arm_r, col, 4.8 * s, 1.0, seed + 9, "arm_r"),
        Stroke(arc(x + w - aw * 0.5, y - 146 * s, 24 * s, 21 * s, 2.2, -3.5, 14), mix(col, m.mid, 0.35), 3.0 * s, 0.8, seed + 13, "roll_r"),
        _ln(x + 30 * s, y - 16 * s, x + 26 * s, y + 2 * s, col, 5 * s, 0.9, seed + 10, "leg_l"),
        _ln(x + w - 30 * s, y - 16 * s, x + w - 26 * s, y + 2 * s, col, 5 * s, 0.9, seed + 11, "leg_r"),
    ]
    return Sketch(sk, name)


def cushion(x=story.SOFA_X + 185.0, y=FLOOR - 150.0, s=1.0, rot=-0.42, seed=120, col=None, fill=None, mood="night",
            name="cushion") -> Sketch:
    """A plump pillow with pinched corners. x, y = its centre. Parts: shape (+ .fill) button."""
    m = _mood(mood)
    col = m.near if col is None else col
    hw, hh = 64 * s, 45 * s
    ctrl = A((-hw, -hh), (0, -hh * 0.93), (hw, -hh), (hw * 0.94, 0), (hw, hh), (0, hh * 0.95), (-hw, hh), (-hw * 0.94, 0), (-hw, -hh))
    P = spline(ctrl, 40)
    cr, sr = math.cos(rot), math.sin(rot)
    P = np.stack([x + P[:, 0] * cr - P[:, 1] * sr, y + P[:, 0] * sr + P[:, 1] * cr], axis=1)
    Q = blob(x, y, 5.5 * s, 5.0 * s, seed + 4, 0.1, 10)
    return Sketch([Fill(P, m.cushion if fill is None else fill, 0.3 + rot, 9 * s, 5 * s, 0.7, seed + 1, knock=m.knock, base=0.4, name="shape.fill"),
                   _cl(P, col, 4 * s, 0.95, seed + 2, "shape"),
                   Stroke(Q, mix(col, m.mid, 0.5), 2.6 * s, 0.75, seed + 3, "button", wob=0.3)], name)


def rug(x=story.RUG[0], y=story.RUG[1], rx=story.RUG[2], ry=story.RUG[3], seed=460, col=None, mood="night", name="rug") -> Sketch:
    """An oval rug lying on the floor. x, y = its centre. Parts: outer (+ .fill) inner (+ .fill) fringe_l fringe_r."""
    m = _mood(mood)
    fc = m.rug if col is None else col
    lc = m.far if m.day else mix(fc, C.CHALK_DIM, 0.6)
    P = blob(x, y, rx, ry, seed, 0.03, 44)
    Q = blob(x + rx * 0.02, y, rx * 0.70, ry * 0.58, seed + 3, 0.03, 36)
    k = 1.45 if m.day else 1.0                          # pastel on warm paper needs more pressure than chalk on dark
    sk = [Fill(P, fc, 0.12, 18, 6.0, 0.42 * k, seed + 1, base=0.14 * k, name="outer.fill"),
          _cl(P, lc, 3.4, 0.72, seed + 2, "outer", step=9.0),
          Fill(Q, m.rug2, -0.2, 16, 5.4, 0.36 * k, seed + 5, base=0.10 * k, name="inner.fill"),
          _cl(Q, mix(lc, fc, 0.3), 2.6, 0.55, seed + 4, "inner", step=9.0)]
    for tag, a0 in (("l", math.pi), ("r", 0.0)):
        an = np.linspace(a0 - 0.30, a0 + 0.30, 15)
        rr = 1.012 + (np.arange(15) % 2) * 0.026
        sk.append(Stroke(np.stack([x + np.cos(an) * rx * rr, y + np.sin(an) * ry * (1.0 + (rr - 1.0) * 3.0)], axis=1), lc, 2.0, 0.55,
                         seed + 7 + (tag == "r"), f"fringe_{tag}", wob=0.3, step=4.0))
    return Sketch(sk, name)


def lamp(x=story.LAMP_X, y=FLOOR, h=520.0, seed=440, col=None, a=0.9, mood="night", name="lamp") -> Sketch:
    """The standing lamp. Parts: foot pole ring shade (+ .fill) cord. In the sunset mood its shade is lit
    (the light itself is the scene's: see the doc)."""
    m = _mood(mood)
    col = m.mid if col is None else col
    s = h / 520.0
    top = y - h
    shade = _poly((x - 62 * s, top + 122 * s), (x - 36 * s, top), (x + 34 * s, top + 2 * s), (x + 64 * s, top + 122 * s))
    foot = np.vstack([arc(x, y - 6 * s, 50 * s, 15 * s, math.pi, 2 * math.pi, 12), A((x + 50 * s, y), (x - 50 * s, y + 1), (x - 50 * s, y - 6 * s))])
    lit = m.lit > 0
    return Sketch([
        Fill(foot, m.wood, 0.3, 7 * s, 4 * s, 0.5, seed + 5, knock=m.knock, base=0.4, name="foot.fill"),
        Stroke(foot, col, 4 * s, a, seed + 2, "foot"),
        Stroke(A((x, top + 122 * s), (x + 3 * s, top + 300 * s), (x + 1 * s, y - 18 * s)), col, 4.4 * s, a, seed + 1, "pole"),
        _ln(x - 9 * s, top + 262 * s, x + 11 * s, top + 263 * s, col, 3.4 * s, a * 0.9, seed + 6, "ring"),
        Fill(shade, m.shade, 1.25, 9 * s, 4.5 * s, 0.75 if lit else 0.55, seed + 3, knock=m.knock, base=0.9 if lit else 0.30, name="shade.fill"),
        _cl(shade, col, 4 * s, a, seed + 4, "shade"),
        Stroke(A((x + 30 * s, top + 122 * s), (x + 32 * s, top + 168 * s), (x + 31 * s, top + 176 * s)), mix(col, m.far, 0.4), 2.2 * s, a * 0.8,
               seed + 7, "cord", wob=0.4),
    ], name)


def chair(x, y, s=1.0, face=1, seed=400, col=None, a=0.9, mood="night", fill=True, name="chair") -> Sketch:
    """A wooden chair, drawn the way a child shows that it is a chair: from the side and a little
    from the front, so that its far legs, its far back post and the board of its back show. x =
    middle of the seat's near edge on the floor; face = +1 the sitter looks right. The seat is 64 s
    above the floor, the back 170 s (183 s at its far end). Parts: back_f leg_ff seat (+ .fill) apron leg_f bar back
    rail (+ .fill) slat (back and back_f are each one line from the floor to the top of the back;
    rail is the board across the top of the back, coloured in)."""
    m = _mood(mood)
    col = mix(m.mid, m.near, 0.35) if col is None else col
    f = face
    far = mix(col, m.far, 0.55)
    ox, oy = 20 * s * f, -11 * s                       # the far side of the chair: over and up
    B, N = (x - 30 * s * f, y - 64 * s), (x + 30 * s * f, y - 65 * s)
    seat = _poly((B[0] - 4 * s * f, B[1]), (N[0] + 4 * s * f, N[1]), (N[0] + ox + 3 * s * f, N[1] + oy), (B[0] + ox - 2 * s * f, B[1] + oy))
    # the board across the top of the back, between the near post and the far one
    rail = _poly((B[0] - 9 * s * f, y - 170 * s), (B[0] + ox - 6 * s * f, y - 172 * s + oy), (B[0] + ox - 3 * s * f, y - 141 * s + oy),
                 (B[0] - 6 * s * f, y - 138 * s))
    sk = [
        Stroke(A((B[0] + ox - 1 * s * f, y + oy), (B[0] + ox, B[1] + oy), (B[0] + ox - 3 * s * f, y - 118 * s + oy), (B[0] + ox - 6 * s * f, y - 168 * s + oy)),
               far, 3.4 * s, a * 0.85, seed + 11, "back_f"),
        _ln(N[0] + ox, N[1] + oy, N[0] + ox + 1 * s * f, y + oy, far, 3.2 * s, a * 0.8, seed + 7, "leg_ff"),
    ]
    if fill:
        sk.append(Fill(seat, m.cloth, 0.25, 5 * s, 3.5 * s, 0.0, seed + 8, knock=m.knock, base=0.72, name="seat.fill"))
    sk += [
        _cl(seat, col, 3.8 * s, a, seed + 1, "seat", wob=0.7),
        _ln(B[0] - 2 * s * f, B[1] + 9 * s, N[0] + 3 * s * f, N[1] + 9 * s, mix(col, m.far, 0.3), 3.0 * s, a * 0.9, seed + 12, "apron", wob=0.6),
        _ln(N[0], N[1], N[0] + 2 * s * f, y, col, 4.6 * s, a, seed + 3, "leg_f"),
        _ln(B[0] - 1 * s * f, y - 26 * s, N[0] + 1 * s * f, y - 27 * s, far, 3.0 * s, a * 0.85, seed + 9, "bar"),
        Stroke(A((B[0] - 3 * s * f, y), B, (B[0] - 3 * s * f, y - 118 * s), (B[0] - 8 * s * f, y - 168 * s)), col, 4.8 * s, a, seed + 4, "back"),
    ]
    if fill:
        sk.append(Fill(rail, mix(m.wood, m.cloth, 0.45), 1.2, 5 * s, 3.5 * s, 0.0, seed + 13, knock=m.knock, base=0.8, name="rail.fill"))
    sk += [
        _cl(rail, col, 3.8 * s, a, seed + 5, "rail", wob=0.6),
        _ln(B[0] - 5 * s * f, y - 106 * s, B[0] + ox - 3 * s * f, y - 108 * s + oy, col, 4.0 * s, a * 0.9, seed + 10, "slat"),
    ]
    return Sketch(sk, name)


def table3(x=story.TABLE_X, y=FLOOR, s=1.1, seed=420, col=None, a=0.92, apart=0.0, mood="night", name="table", chair_s=None) -> Sketch:
    """The table with three chairs, from the side: the home table as it stands in the room (the same
    cloth with its scalloped hem), with a bowl of fruit. apart = 0..1: how far two of the chairs have
    been pulled away from the third (chair_m stays tucked under the table's left end; chair_l is
    pulled off to the left, chair_r to the right). The top is 134 s above the floor; chair_s = the
    chairs' scale (default 1.18 s: seat 83, back 221 to 238 at s = 1.1). Parts: chair_m.* chair_l.*
    chair_r.* leg_l leg_r cloth (+ .fill) top (+ .fill) fruit0-2 (+ .fill) bowl (+ .fill)."""
    m = _mood(mood)
    col = mix(m.mid, m.near, 0.35) if col is None else col
    cs = 1.18 * s if chair_s is None else chair_s
    hw = 118 * s
    top = _poly((x - hw - 10 * s, y - 134 * s), (x + hw + 10 * s, y - 136 * s), (x + hw + 8 * s, y - 117 * s), (x - hw - 8 * s, y - 115 * s))
    hem_x = np.linspace(x - hw + 26 * s, x + hw - 26 * s, 15)
    hem = np.stack([hem_x, y - 66 * s + 7 * s * np.abs(np.sin(np.linspace(0, 3.5 * math.pi, 15)))], axis=1)
    cloth = np.vstack([A((x - hw + 22 * s, y - 118 * s), (x - hw + 26 * s, y - 68 * s)), hem, A((x + hw - 26 * s, y - 68 * s), (x + hw - 22 * s, y - 119 * s),
                                                                                               (x - hw + 22 * s, y - 118 * s))])
    bx, by = x - 30 * s, y - 135 * s
    bowl = np.vstack([A((bx - 40 * s, by - 26 * s)), arc(bx, by - 26 * s, 38 * s, 25 * s, math.pi, 0.0, 12), A((bx + 40 * s, by - 26 * s), (bx - 40 * s, by - 25 * s))])
    xm = x - hw + 4 * s                                # the chair that stays: its seat goes under the table's end
    sk = [chair(xm, y, cs, 1, seed + 30, col, a, mood, name="chair_m"),
          chair(xm - (84 + 90 * apart) * cs, y, cs, 1, seed + 10, col, a, mood, name="chair_l"),
          chair(x + hw + (40 + 120 * apart) * cs, y, cs, -1, seed + 20, col, a, mood, name="chair_r"),
          Stroke(A((x - hw + 13 * s, y - 116 * s), (x - hw + 11 * s, y - 50 * s), (x - hw + 6 * s, y)), col, 5.6 * s, a, seed + 2, "leg_l"),
          Stroke(A((x + hw - 13 * s, y - 118 * s), (x + hw - 11 * s, y - 50 * s), (x + hw - 7 * s, y)), col, 5.6 * s, a, seed + 3, "leg_r"),
          Fill(cloth, m.cloth, 1.45, 13 * s, 6 * s, 0.5, seed + 6, knock=m.knock, base=0.5, name="cloth.fill"),
          Stroke(cloth[1:-2], mix(col, m.mid, 0.3), 3.2 * s, a * 0.95, seed + 7, "cloth", wob=0.6, step=5.0),
          Fill(top, m.wood, 0.1, 6 * s, 4 * s, 0.55, seed + 5, knock=m.knock, base=0.66, name="top.fill"),
          _cl(top, col, 4.8 * s, a, seed + 1, "top")]
    fcols = (C.CORAL, C.MUSTARD, C.HILL_NEAR) if m.day else (m.cloth, m.rug2, m.cushion)
    for j, (fx, fy, fr) in enumerate(((-17, -34, 14), (10, -38, 15), (28, -31, 12))):
        P = blob(bx + fx * s, by + fy * s, fr * s, fr * s, seed + 50 + j, 0.08, 14)
        sk.append(Fill(P, fcols[j], 0.6, 4 * s, 3 * s, 0.0, seed + 53 + j, knock=m.knock, base=0.85 if m.day else 0.55, name=f"fruit{j}.fill"))
        sk.append(_cl(P, col, 2.6 * s, a, seed + 56 + j, f"fruit{j}", wob=0.5))
    sk += [Fill(bowl, m.cloth, 0.15, 5 * s, 3.5 * s, 0.45, seed + 60, knock=m.knock, base=0.6, name="bowl.fill"),
           Stroke(bowl, col, 3.4 * s, a, seed + 61, "bowl", wob=0.6)]
    return Sketch(sk, name)


def shelf(x=1836.0, y=372.0, seed=480, col=None, a=0.85, mood="night", name="shelf") -> Sketch:
    """A shelf on the wall with three books and a plant, cropped by the right edge of the room.
    x, y = middle of the plank. Parts: plank bracket_l bracket_r book0-2 (+ .fill) pot (+ .fill) leaf0-2."""
    m = _mood(mood)
    col = m.far if col is None else col
    line = mix(col, m.mid, 0.5)
    sk = [_ln(x - 118, y, x + 122, y + 2, line, 4.6, a, seed + 1, "plank"),
          Stroke(A((x - 84, y + 3), (x - 84, y + 34), (x - 62, y + 4)), col, 3.0, a * 0.9, seed + 2, "bracket_l"),
          Stroke(A((x + 78, y + 4), (x + 78, y + 35), (x + 100, y + 5)), col, 3.0, a * 0.9, seed + 3, "bracket_r")]
    for j, (bx, bw, bh, tilt) in enumerate(((-96, 22, 74, 0.0), (-72, 18, 62, 0.0), (-40, 24, 70, 0.20))):
        P = _poly((x + bx, y - 2), (x + bx + tilt * bh, y - 2 - bh), (x + bx + bw + tilt * bh, y - 2 - bh + tilt * 8), (x + bx + bw, y - 2))
        sk.append(Fill(P, m.book[j], 1.5, 5, 3.5, 0.0, seed + 10 + j, knock=m.knock, base=0.8, name=f"book{j}.fill"))
        sk.append(_cl(P, line, 2.8, a, seed + 14 + j, f"book{j}", wob=0.6))
    px = x + 48
    pot = A((px - 20, y - 34), (px - 15, y - 2), (px + 15, y - 2), (px + 21, y - 34), (px - 20, y - 34))
    sk.append(Fill(pot, m.wood, 0.2, 5, 3.5, 0.0, seed + 20, knock=m.knock, base=0.75, name="pot.fill"))
    sk.append(Stroke(pot, line, 3.0, a, seed + 21, "pot", wob=0.6))
    lc = C.HILL_SHADE if m.day else line
    for j, (ex, ey) in enumerate(((-34, -78), (4, -98), (40, -74))):
        sk.append(Stroke(spline(A((px, y - 34), (px + ex * 0.4, y - 34 + ey * 0.75), (px + ex, y - 34 + ey), (px + ex * 0.72, y - 34 + ey * 0.45),
                                  (px + 2, y - 36)), 12), lc, 2.8, a, seed + 24 + j, f"leaf{j}", wob=0.5))
    return Sketch(sk, name)


# ---------------------------------------------------------------------------------------------
# the room: wall, floor, shade (seated dressing) and the Place
# ---------------------------------------------------------------------------------------------
WALL_X = (-3000.0, 5000.0)       # how far the room's (and the classroom's) wall and floor dressing reach: past any framing of the film
WALL_LINE_X = (-1400.0, 3300.0)  # ... and its long lines (skirting, cornice, dado)
TOP_Y = -420.0                   # ... and how far up (above any framing of these sets)
SKIRT_Y = FLOOR - 27.0           # top of the skirting board
CORNICE_Y = 52.0


def room_wall(F: Frame, mood="night", a: float = 1.0, x0=WALL_X[0], x1=WALL_X[1], y0=TOP_Y, y1=SKIRT_Y):
    """The wall, coloured in by a tired hand: two long loose seated zigzags from y0 down to the
    skirting board, a darker band above the cornice, the skirting board as a band of tone.
    a = 0..1 pressure (fade it over at least 6 frames)."""
    if a <= 0.003:
        return
    m = _mood(mood)
    rect = (x0, y0, x1, y1)
    k = a * m.wall_k
    if m.day:
        _seat_hatch(F, rect, m.wall_a, m.wall_ang, 62, 19, 0.44 * k, 901)
        _seat_hatch(F, rect, m.wall_b, m.wall_ang - 0.16, 112, 15, 0.26 * k, 902)
        wash(F, rect_pts(x0, y0, x1, CORNICE_Y + 4), C.SHADOW, y0, CORNICE_Y + 4, [0.16 * a, 0.12 * a], "soft")
    else:
        _seat_hatch(F, rect, m.wall_a, m.wall_ang, 60, 15, 0.30 * k, 901)
        _seat_hatch(F, rect, m.wall_b, m.wall_ang - 0.10, 92, 21, 0.42 * k, 902)
        wash(F, rect_pts(x0, y0, x1, CORNICE_Y + 4), C.PAPER_DEEP, y0, CORNICE_Y + 4, [0.6 * a, 0.5 * a], "soft")
    # the skirting board: a band of tone between its top line and the ground line
    fill(F, rect_pts(x0, y1, x1, FLOOR), m.wall_b if not m.day else m.wall_a, (0.34 if not m.day else 0.30) * a, "mid")


def _geo_boards(x0, x1, vx, bottom):
    key = ("boards", x0, x1, vx, bottom)
    if key not in _GEO:
        lines, joints = [], []
        pitch = 314.0
        n = int((x1 - x0) / pitch) + 2
        xs = [x0 + j * pitch + 40 * rsym(j, 5) for j in range(n)]
        for j, xa in enumerate(xs):
            lines.append(_seated(A((xa, FLOOR + 9), (vx + (xa - vx) * 2.3, bottom)), 20 + j, 1.2, 14.0))
        for j in range(n - 1):
            for q in range(2):
                d = 0.10 + 0.8 * rnd(j * 7 + q, 61)                  # depth 0..1 down the floor
                yy = FLOOR + 9 + d * (bottom - FLOOR - 9)
                k = 1.0 + 1.3 * d
                xa, xb = vx + (xs[j] - vx) * k, vx + (xs[j + 1] - vx) * k
                joints.append(_seated(A((xa + 2, yy), (xb - 2, yy + 2 * rsym(j + q, 62))), 60 + j * 2 + q, 0.8, 14.0))
        # ruled in from the middle of the room outward (draw = 0..1 shows the first so many)
        order = sorted(range(n), key=lambda j: abs(xs[j] - vx))
        jorder = sorted(range(len(joints)), key=lambda i: abs(xs[i // 2] - vx))
        _GEO[key] = ([lines[j] for j in order], [joints[i] for i in jorder])
    return _GEO[key]


def room_floor(F: Frame, mood="night", a: float = 1.0, draw: float = 1.0, x0=WALL_X[0], x1=WALL_X[1], bottom=1130.0, vx=960.0):
    """The floor in front of the ground line: boards running toward the viewer (vanishing x = vx)
    and their butt joints. NOT the ground line. a = pressure, draw = 0..1 the boards being ruled in,
    one after the other."""
    if a <= 0.003:
        return
    m = _mood(mood)
    lines, joints = _geo_boards(x0, x1, vx, bottom)
    if m.day:
        fill(F, rect_pts(x0, FLOOR + 4, x1, bottom), C.EVE_LOW, 0.20 * a, "mid")
    _marks(F, lines, m.board_line, 2.6, m.board_a * a, "mid", draw=draw)
    _marks(F, joints, m.board_line, 2.2, m.board_a * 0.8 * a, "mid", draw=min(1.0, max(0.0, draw * 1.5 - 0.5)))


def room_shade(F: Frame, mood="night", a: float = 1.0, sofa=1.0, table=1.0, lamp=1.0):
    """Rubbed contact shade where the furniture stands on the floor (sofa, table and chairs, lamp):
    draw it after back() and the light, before the furniture. Each argument 0..1 fades one of them."""
    m = _mood(mood)
    col, k = (C.SHADOW, 0.34) if m.day else (C.PAPER_DEEP, 0.85)
    if sofa > 0:
        smudge(F, story.SOFA_X + story.SOFA_W / 2, FLOOR + 13, story.SOFA_W * 0.57, 26, col, k * a * sofa, "soft")
    if table > 0:
        smudge(F, story.TABLE_X - 60, FLOOR + 12, 300, 22, col, 0.8 * k * a * table, "soft")
    if lamp > 0:
        smudge(F, story.LAMP_X, FLOOR + 9, 86, 15, col, 0.8 * k * a * lamp, "soft")


def _room_back(F, S, a):
    t = F.t
    room_wall(F, S.mood, a * ramp(S.cue("wall", t), 0.0, 1.0))
    room_floor(F, S.mood, a * ramp(S.cue("floor", t), 0.0, 0.5), draw=S.cue("floor", t))
    room_shade(F, S.mood, a, sofa=ease(S.cue("shade.sofa", t)), table=ease(S.cue("shade.table", t)), lamp=ease(S.cue("shade.lamp", t)))


def _room_view(F, S, a, lit=None, wire=None):
    t = F.t
    lit = S.cue("amber", t) if lit is None else lit
    window_view(F, S.mood, a * ease(S.cue("view", t)), lit, wire)


def room(mood: str = "night", apart: float = 1.0, throw: bool = True, dx: float = 0.0) -> Place:
    """The room, the same room three times: mood "night" (0 to 36 s), "eve" (85.75 to about 104 s,
    at dx = story.ROOM2_DX) or "sunset" (the coda, on warm paper in the day skin, at dx =
    story.ROOM3_DX). apart: the table's two chairs pulled away. dx: where the room stands (world x
    added to every anchor).

    Groups in paint order: wall (skirt cornice), window, lamp, shelf, table, rug, sofa, cushion.
    The family drawing hangs at story.WALL_DRAWING (not drawn here); the child lies at story.CURL_X."""
    m = _mood(mood)
    xa, xb = WALL_LINE_X
    wall = Sketch([_ln(xa, SKIRT_Y, xb, SKIRT_Y + 2, m.far, 2.8, 0.62, 12, "skirt", wob=1.0, step=16.0),
                   _ln(xa, CORNICE_Y, xb, CORNICE_Y + 3, m.far, 3.2, 0.6, 13, "cornice", wob=1.2, step=16.0)], "wall")
    return Place("room", m, dict(
        wall=wall,
        window=window(mood=m),
        lamp=lamp(mood=m),
        shelf=shelf(mood=m),
        table=table3(apart=apart, mood=m),
        rug=rug(mood=m),
        sofa=sofa(mood=m, throw=throw),
        cushion=cushion(mood=m)), back=_room_back, view=_room_view).at(dx)


# ---------------------------------------------------------------------------------------------
# draw-on schedules with the music
# ---------------------------------------------------------------------------------------------
def _schedule(S: Place, tl, k0: float, rows, cues=()) -> float:
    """rows: (prefix, beat, every, dur) in beats after beat k0: the outlines under `prefix` start one
    per `every` beats from `beat`, each taking `dur` beats, its fill following it. cues: (name, beat0,
    beat1) for the dressing. Returns the time everything is complete."""
    b = lambda k: tl.beat_time(k0 + k)
    bs = tl.beat_s
    allk = S.all()
    for it in allk:
        it.on = None
    end = b(0.0)
    for prefix, k, every, dur in rows:
        sub = allk.sub(prefix)
        if len(sub):
            end = max(end, sub.spread(b(k), every * bs, dur * bs))
    for it in allk:                                       # nothing is forgotten: what no row names comes last
        if it.on is None:
            it.on = (end - 0.4, end)
    for name, ka, kb in cues:
        S.cues[name] = (b(ka), b(kb))
        end = max(end, b(kb))
    S.cues["end"] = (end, end)
    return end


ROOM_ON = (                     # the intro: beat 0 is the first note (0.265 s); a bar is four beats
    # bar 1: the two long lines of the wall (the ground line is the scene's)
    ("wall.skirt", 1.28, 0, 1.7), ("wall.cornice", 1.75, 0, 1.7),
    # bar 2: the sofa, a stroke a beat, then the smaller ones; the rug quietly under it
    ("sofa.back", 4.0, 0, 1.0), ("sofa.arm_l", 5.0, 0, 0.5), ("sofa.roll_l", 5.3, 0, 0.3), ("sofa.arm_r", 5.5, 0, 0.5),
    ("sofa.roll_r", 5.8, 0, 0.3), ("sofa.seat", 6.0, 0, 0.8), ("sofa.split", 6.6, 0, 0.3), ("sofa.leg_l", 6.8, 0, 0.25),
    ("sofa.leg_r", 6.9, 0, 0.25), ("sofa.throw", 7.0, 0, 0.6), ("sofa.fringe", 7.4, 0, 0.5), ("cushion", 7.5, 0.3, 0.5),
    ("rug.outer", 7.25, 0, 1.0), ("rug.inner", 7.75, 0, 0.8), ("rug.fringe_l", 8.3, 0, 0.4), ("rug.fringe_r", 8.6, 0, 0.4),
    # bar 3: the window on the beats; lamp, table, chairs and shelf quietly between them
    ("window.frame", 8.0, 0, 0.9), ("window.mullion", 8.5, 0, 0.45), ("window.transom", 9.0, 0, 0.45), ("window.inner", 9.25, 0, 0.7),
    ("window.sill", 9.5, 0, 0.4), ("window.ledge", 9.7, 0, 0.4), ("window.rail", 10.0, 0, 0.45),
    ("window.curtain.l", 10.25, 0, 0.6), ("window.curtain.l0", 10.7, 0, 0.4), ("window.curtain.l1", 10.85, 0, 0.4),
    ("window.curtain.r", 10.75, 0, 0.6), ("window.curtain.r0", 11.2, 0, 0.4), ("window.curtain.r1", 11.35, 0, 0.4),
    ("lamp", 8.7, 0.22, 0.7),
    ("table.top", 10.0, 0, 0.5), ("table.leg_l", 10.3, 0, 0.3), ("table.leg_r", 10.4, 0, 0.3), ("table.cloth", 10.45, 0, 0.5),
    ("table.chair_m", 10.5, 0.06, 0.3), ("table.chair_l", 10.9, 0.06, 0.3), ("table.bowl", 11.1, 0, 0.3), ("table.fruit0", 11.2, 0, 0.25),
    ("table.fruit1", 11.3, 0, 0.25), ("table.fruit2", 11.4, 0, 0.25), ("table.chair_r", 11.0, 0.05, 0.25), ("shelf", 10.6, 0.07, 0.3))
ROOM_ON_CUES = (("wall", 0.2, 3.0), ("floor", 1.0, 3.8), ("shade.sofa", 4.6, 7.0), ("view", 9.0, 10.6), ("shade.lamp", 9.0, 10.4),
                ("amber", 11.0, 11.7), ("shade.table", 10.6, 11.9))


def room_on(S: Place, tl, bar: int = 0) -> float:
    """The room draws itself on with the piano of the intro (default: from the first note, 0.265 s;
    bar = the bar it starts in). Bar 1: skirting and cornice (1.23, 1.58), the wall's hatch and the
    floorboards coming up. Bar 2: the sofa, the first thing in the room, a stroke a beat (back 3.27,
    arms, seat, blanket, cushion; its hatch following); the rug quietly. Bar 3: the window on the
    beats (frame 6.27, bars, sill, rail, curtains), the pane filling from 7.0 and the one amber
    window coloured in at 8.5; lamp, table, chairs and shelf quietly between the beats. Sets every
    item's `on` and the dressing cues read by S.back / S.view. Everything is complete at 9.2 s
    (returned), before the child is drawn (9.27). The ground line (0.27) and the child are the scene's."""
    return _schedule(S, tl, 4.0 * bar, ROOM_ON, ROOM_ON_CUES)


# the coda: attacks of the piano at 244.77, 244.97, 245.57, 245.86, 247.49 (beats 0, 0.27, 1.08, 1.47, 3.63 of the bar at 244.765)
ROOM_CODA = (
    ("sofa.back", 0.0, 0, 0.7), ("sofa.arm_l", 0.1, 0, 0.5), ("sofa.arm_r", 0.2, 0, 0.5), ("sofa.seat", 0.5, 0, 0.6), ("sofa.split", 0.9, 0, 0.3),
    ("sofa.roll_l", 0.9, 0, 0.3), ("sofa.roll_r", 1.0, 0, 0.3), ("sofa.leg_l", 1.0, 0, 0.25), ("sofa.leg_r", 1.1, 0, 0.25),
    ("window.frame", 0.27, 0, 0.8), ("window.mullion", 0.7, 0, 0.4), ("window.transom", 0.85, 0, 0.4), ("window.inner", 1.0, 0, 0.6),
    ("window.sill", 1.08, 0, 0.4), ("window.ledge", 1.2, 0, 0.4),
    ("wall.skirt", 1.08, 0, 1.2), ("wall.cornice", 1.2, 0, 1.2),
    ("window.rail", 1.47, 0, 0.4), ("window.curtain.l", 1.6, 0, 0.6), ("window.curtain.l0", 2.05, 0, 0.4), ("window.curtain.l1", 2.2, 0, 0.4),
    ("window.curtain.r", 1.9, 0, 0.6), ("window.curtain.r0", 2.35, 0, 0.4), ("window.curtain.r1", 2.5, 0, 0.4),
    ("lamp", 1.47, 0.2, 0.6), ("rug.outer", 2.0, 0, 0.9), ("rug.inner", 2.4, 0, 0.7), ("rug.fringe_l", 2.9, 0, 0.4), ("rug.fringe_r", 3.1, 0, 0.4),
    ("table.top", 2.68, 0, 0.5), ("table.leg_l", 2.9, 0, 0.3), ("table.leg_r", 3.0, 0, 0.3), ("table.cloth", 3.05, 0, 0.5),
    ("table.chair_m", 3.2, 0.05, 0.3), ("table.chair_l", 3.63, 0.05, 0.3), ("table.chair_r", 3.9, 0.05, 0.25),
    ("table.bowl", 4.0, 0, 0.3), ("table.fruit0", 4.1, 0, 0.25), ("table.fruit1", 4.2, 0, 0.25), ("table.fruit2", 4.3, 0, 0.25),
    ("sofa.throw", 3.63, 0, 0.6), ("sofa.fringe", 4.0, 0, 0.4), ("cushion", 4.0, 0.3, 0.5), ("shelf", 3.9, 0.07, 0.3))
ROOM_CODA_CUES = (("wall", 0.3, 3.0), ("floor", 0.6, 3.0), ("shade.sofa", 0.6, 2.4), ("view", 1.0, 2.6), ("amber", 0.0, 0.01),
                  ("shade.lamp", 1.8, 3.0), ("shade.table", 3.0, 4.6))


def room_on_coda(S: Place, tl, t0: float = 244.765) -> float:
    """The room draws itself on around the child in the coda, with the piano's attacks: the sofa on
    244.77, the window on 244.97, sill and wall lines on 245.57, rail, curtains and lamp from 245.86,
    rug and table through the bar, the blanket and the pulled-away chair on 247.49; complete at about
    248.4 s (returned). t0: the downbeat it starts on."""
    return _schedule(S, tl, (t0 - tl.beat0) / tl.beat_s, ROOM_CODA, ROOM_CODA_CUES)


# ---------------------------------------------------------------------------------------------
# the classroom from the back (36.27 to 48.27)
# ---------------------------------------------------------------------------------------------
CLASS_BOARD = (620.0, 176.0, 1230.0, 446.0)          # l, t, r, b
CLASS_DOOR = (40.0, 236.0, 196.0, FLOOR)
CLASS_DESK = (400.0, FLOOR)                           # the desk that stands apart: middle of its near edge on the floor (desk_dx = 0)
CLASS_DESK_S = 1.35                                   # its scale: the top is 95 * scale above the floor
CLASS_DESK_TOP_Y = FLOOR - 95.0 * CLASS_DESK_S        # world y of its top: where pushing hands rest
CLASS_CHAIR = (268.0, FLOOR)                          # its chair
CLASS_DESK_R = (1900.0, FLOOR)                        # the same pair standing apart on the other side of the rows (side = +1):
CLASS_CHAIR_R = (2032.0, FLOOR)                       # past the window, the chair turned to face the rows
CLASS_CLOCK = (432.0, 268.0, 46.0)                    # centre, radius
CLASS_DADO_Y = 542.0
# where the rows of pupils sit (another artist draws them): x of each seat, floor y, scale; keep x 740..1700 free
CLASS_ROWS = {"far": ((800.0, 985.0, 1170.0, 1355.0, 1540.0), FLOOR - 4.0, 0.80),
              "near": ((760.0, 990.0, 1220.0, 1450.0, 1680.0), FLOOR + 96.0, 1.08)}
CLASS_LAMPS = ((330.0, 118.0, 1.0), (925.0, 104.0, 0.9), (1500.0, 112.0, 0.95))     # pendant lamps: x, y of the shade's rim, scale


def _scribble(x0, x1, y, amp, seed, step=7.0):
    """One line of 'writing': a zigzag in words with flat gaps between them. Never letters."""
    pts, x, j, word = [], x0, 0, 0
    left = 4 + int(rnd(seed, 1) * 7)
    while x < x1:
        if left > 0:
            pts.append((x, y + amp * (1 if j % 2 else -1) * (0.45 + 0.55 * rnd(seed + j, 2))))
            left -= 1
        else:
            pts.append((x, y + amp * 0.2))
            pts.append((x + step * 1.6, y + amp * 0.2))
            x += step * 1.6
            word += 1
            left = 3 + int(rnd(seed + word, 3) * 9)
        x += step * (0.8 + 0.4 * rnd(seed + j, 4))
        j += 1
    return np.asarray(pts, dtype=np.float64)


def board(l=CLASS_BOARD[0], t=CLASS_BOARD[1], r=CLASS_BOARD[2], b=CLASS_BOARD[3], seed=1320, col=None, mood="day", name="board") -> Sketch:
    """The blackboard: a dark slab, wiped in places, three scribbled lines for writing (never
    letters), a triangle and a circle, the ledge with a chalk and the sponge.
    Parts: frame (+ .fill) wipe0 wipe1 (fills) text0-2 shape0 shape1 ledge (+ .fill) chalk sponge."""
    m = _mood(mood)
    col = m.near if col is None else col
    w, h = r - l, b - t
    slate = (0.105, 0.145, 0.20)
    sk = [Fill(rect_pts(l, t, r, b), slate, 0.3, 18, 9, 0.40, seed, knock=C.PAPER_DEEP, base=0.72, name="frame.fill"),
          Fill(blob(l + w * 0.70, t + h * 0.36, w * 0.20, h * 0.26, seed + 20, 0.12, 18), (0.46, 0.53, 0.66), 0.25, 17, 15, 0.15, seed + 21,
               base=0.05, grain="sparse", name="wipe0.fill"),
          Fill(blob(l + w * 0.30, t + h * 0.72, w * 0.16, h * 0.16, seed + 22, 0.12, 16), (0.46, 0.53, 0.66), -0.15, 15, 13, 0.12, seed + 23,
               base=0.04, grain="sparse", name="wipe1.fill"),
          _cl(rect_pts(l, t, r, b), col, 5.5, 0.95, seed + 1, "frame")]
    for j, (x1, yy) in enumerate(((l + w * 0.54, t + 64), (l + w * 0.76, t + 122), (l + w * 0.42, t + 180))):
        sk.append(Stroke(_scribble(l + 46, x1, yy, 8.0, seed + 40 + j * 13), C.CHALK_DIM if not m.day else m.mid, 3.0, 0.78, seed + 4 + j, f"text{j}",
                         wob=0.4, step=4.0))
    tx, ty = l + w * 0.80, t + h * 0.72
    sk += [_cl(_poly((tx - 46, ty + 30), (tx + 4, ty - 44), (tx + 50, ty + 30)), C.CHALK_DIM, 2.8, 0.7, seed + 8, "shape0", wob=0.8),
           _cl(blob(l + w * 0.62, t + h * 0.74, 30, 30, seed + 9, 0.05, 20), C.CHALK_DIM, 2.8, 0.7, seed + 10, "shape1", wob=0.8),
           Fill(rect_pts(l - 14, b + 10, r + 14, b + 24), m.wood, 0.1, 6, 4, 0.5, seed + 11, knock=m.knock, base=0.6, name="ledge.fill"),
           _cl(rect_pts(l - 14, b + 10, r + 14, b + 24), col, 3.8, 0.95, seed + 2, "ledge"),
           _ln(r - 168, b + 6, r - 128, b + 8, C.CHALK, 5.0, 0.95, seed + 3, "chalk", wob=0.3),
           _cl(rect_pts(l + 60, b - 6, l + 106, b + 10), m.mid, 3.0, 0.9, seed + 12, "sponge", wob=0.6)]
    return Sketch(sk, name)


def door(l=CLASS_DOOR[0], t=CLASS_DOOR[1], r=CLASS_DOOR[2], b=CLASS_DOOR[3], seed=1600, col=None, mood="day", pane=True, side=1,
         name="door") -> Sketch:
    """A door standing on world y = b: the frame (three sides, open at the floor), the leaf with a
    small pane and a knob (side = +1: knob on the right). Parts: frame leaf (+ .fill) pane (+ .fill) knob."""
    m = _mood(mood)
    col = m.mid if col is None else col
    leaf = A((l + 11, b - 2), (l + 12, t + 12), (r - 11, t + 11), (r - 10, b - 2))
    sk = [Fill(np.vstack([leaf, leaf[:1]]), m.wood, 1.45, 15, 6, 0.42, seed + 3, knock=m.knock, base=0.42, name="leaf.fill"),
          Stroke(A((l, b), (l, t), (r, t + 1), (r + 1, b)), col, 4.8, 0.9, seed, "frame"),
          Stroke(leaf, mix(col, m.far, 0.4), 3.0, 0.8, seed + 4, "leaf")]
    if pane:
        pl, pr = (l + r) / 2 - (r - l) * 0.22, (l + r) / 2 + (r - l) * 0.22
        P = rect_pts(pl, t + 44, pr, t + 44 + (pr - pl) * 1.5)
        sk += [Fill(P, (0.36, 0.42, 0.56) if not m.day else C.SKY_MID, 0.4, 8, 5, 0.5, seed + 5, knock=m.knock, base=0.5, name="pane.fill"),
               _cl(P, col, 3.0, 0.9, seed + 6, "pane", wob=0.6)]
    kx = r - 28 if side > 0 else l + 28
    sk.append(_cl(blob(kx, t + (b - t) * 0.56, 7, 7, seed + 1, 0.1, 10), col, 3.0, 0.9, seed + 2, "knob", wob=0.4))
    return Sketch(sk, name)


def desk(x=CLASS_DESK[0], y=CLASS_DESK[1], s=1.0, seed=900, col=None, a=0.95, mood="day", name="desk") -> Sketch:
    """A school desk from the side, its far legs showing behind. x = middle of its near edge on the
    floor; the top is 95 s above the floor (story.DESK_TOP_Y at s = 1) and 112 s wide.
    Parts: leg_fl leg_fr top (+ .fill) box (+ .fill) leg_l leg_r bar."""
    m = _mood(mood)
    col = m.near if col is None else col
    far = mix(col, m.far, 0.6)
    ox, oy = 15 * s, -9 * s
    top = _poly((x - 56 * s, y - 95 * s), (x + 56 * s, y - 96 * s), (x + 56 * s + ox, y - 96 * s + oy), (x - 56 * s + ox, y - 95 * s + oy))
    box = _poly((x - 47 * s, y - 91 * s), (x + 47 * s, y - 92 * s), (x + 46 * s, y - 64 * s), (x - 46 * s, y - 63 * s))
    return Sketch([
        _ln(x - 45 * s + ox, y - 80 * s + oy, x - 46 * s + ox, y + oy, far, 3.0 * s, a * 0.8, seed + 6, "leg_fl"),
        _ln(x + 45 * s + ox, y - 80 * s + oy, x + 46 * s + ox, y + oy, far, 3.0 * s, a * 0.8, seed + 7, "leg_fr"),
        Fill(box, m.wood, 0.2, 6 * s, 4 * s, 0.5, seed + 8, knock=m.knock, base=0.55, name="box.fill"),
        _cl(box, mix(col, m.mid, 0.4), 3.4 * s, a * 0.9, seed + 4, "box", wob=0.7),
        Fill(top, m.cloth, 0.3, 5 * s, 3.5 * s, 0.4, seed + 9, knock=m.knock, base=0.6, name="top.fill"),
        _cl(top, col, 4.4 * s, a, seed + 1, "top", wob=0.7),
        _ln(x - 45 * s, y - 63 * s, x - 47 * s, y, col, 4.2 * s, a, seed + 2, "leg_l"),
        _ln(x + 45 * s, y - 64 * s, x + 46 * s, y, col, 4.2 * s, a, seed + 3, "leg_r"),
        _ln(x - 46 * s, y - 20 * s, x + 45 * s, y - 21 * s, far, 2.8 * s, a * 0.85, seed + 5, "bar"),
    ], name)


def _pendant(x, y, s, seed, col, m, name) -> Sketch:
    """A lamp hanging from above the frame: cord, shade (+ .fill), bulb. (x, y) = middle of the shade's rim."""
    sh = _poly((x - 50 * s, y), (x - 14 * s, y - 36 * s), (x + 13 * s, y - 37 * s), (x + 51 * s, y - 1 * s))
    return Sketch([_ln(x + 1, -150.0, x, y - 36 * s, mix(col, m.far, 0.5), 2.6, 0.75, seed, "cord", wob=0.5, step=10.0),
                   Fill(sh, m.shade, 0.2, 7 * s, 4 * s, 0.5, seed + 1, knock=m.knock, base=0.5, name="shade.fill"),
                   _cl(sh, col, 3.6 * s, 0.85, seed + 2, "shade", wob=0.7),
                   Stroke(arc(x, y + 1 * s, 12 * s, 9 * s, 0.1, math.pi - 0.1, 7), mix(col, C.CHALK, 0.3), 2.6 * s, 0.8, seed + 3, "bulb", wob=0.3)], name)


def _clock(cx, cy, r, seed, col, m, name="clock") -> Sketch:
    """A wall clock without numerals: rim (+ .fill), four ticks, the two hands."""
    P = blob(cx, cy, r, r, seed, 0.03, 26)
    sk = [Fill(P, m.cloth, 0.5, 8, 4, 0.0, seed + 1, knock=m.knock, base=0.30, name="rim.fill"),
          _cl(P, col, 3.8, 0.9, seed + 2, "rim", wob=0.7)]
    for j in range(4):
        an = j * math.pi / 2
        sk.append(_ln(cx + math.cos(an) * r * 0.70, cy + math.sin(an) * r * 0.70, cx + math.cos(an) * r * 0.88, cy + math.sin(an) * r * 0.88,
                      col, 2.6, 0.8, seed + 3 + j, f"tick{j}", wob=0.2))
    sk.append(Stroke(A((cx - r * 0.10, cy - r * 0.62), (cx, cy), (cx + r * 0.42, cy + r * 0.20)), col, 3.2, 0.95, seed + 8, "hands", wob=0.3))
    return Sketch(sk, name)


def _pins(seed, m, name="pins") -> Sketch:
    """Children's drawings pinned to the wall right of the window (scribbles; the last is cropped by the frame)."""
    sk = []
    line = mix(m.far, m.mid, 0.5)
    for j, (x, y, rot) in enumerate(((1768.0, 292.0, -0.05), (1852.0, 322.0, 0.06), (1774.0, 404.0, 0.04), (1862.0, 432.0, -0.07))):
        cr, sr = math.cos(rot), math.sin(rot)
        T = lambda px, py: (x + px * cr - py * sr, y + px * sr + py * cr)
        P = _poly(T(-32, -40), T(32, -40), T(32, 40), T(-32, 40))
        sk.append(Fill(P, m.cloth, 0.4, 6, 4, 0.0, seed + j * 5, knock=m.knock, base=0.42, name=f"sheet{j}.fill"))
        sk.append(_cl(P, line, 2.6, 0.85, seed + j * 5 + 1, f"sheet{j}", wob=0.6))
        if j == 0:
            Q = [T(-20, 18), T(-8, -12), T(2, 10), T(12, -20), T(22, 16)]
        elif j == 1:
            an = np.linspace(0, 4.5 * math.pi, 22)
            Q = [T(math.cos(q) * (3 + q * 1.3), math.sin(q) * (3 + q * 1.3)) for q in an]
        elif j == 2:
            Q = [T(-22, 14), T(-22, -6), T(-6, -22), T(10, -6), T(10, 14), T(-22, 14)]
        else:
            Q = [T(-20 + 4 * i, 8 * math.sin(i * 1.4)) for i in range(11)]
        sk.append(Stroke(np.asarray(Q), C.KNOCK if not m.day else m.near, 2.0, 0.85, seed + j * 5 + 2, f"mark{j}", wob=0.3, edge=0.0, step=4.0))
    return Sketch(sk, name)


def _geo_tiles(x0, x1, vx, bottom, y_top):
    key = ("tiles", x0, x1, vx, bottom, y_top)
    if key not in _GEO:
        out = []
        pitch = 250.0
        for j in range(int((x1 - x0) / pitch) + 2):
            xa = x0 + j * pitch
            out.append(_seated(A((xa, y_top), (vx + (xa - vx) * 2.1, bottom)), 2200 + j, 0.9, 16.0))
        for j, d in enumerate((30.0, 74.0, 132.0, 212.0, 318.0)):
            out.append(_seated(A((x0, y_top + d), (x1, y_top + d + 2)), 2230 + j, 1.0, 22.0))
        _GEO[key] = out
    return _GEO[key]


def class_back(F: Frame, a: float = 1.0, mood="day", x0=WALL_X[0], x1=WALL_X[1]):
    """The classroom's seated dressing: the wall of a grey day (lighter, more upright zigzag), the
    darker dado below CLASS_DADO_Y, the tiled floor in front of the ground line."""
    if a <= 0.003:
        return
    m = _mood(mood)
    rect = (x0, TOP_Y, x1, CLASS_DADO_Y)
    _seat_hatch(F, rect, m.wall_a, m.wall_ang, 64, 16, 0.24 * a, 911)
    _seat_hatch(F, rect, m.wall_b, m.wall_ang - 0.12, 110, 18, 0.16 * a, 912)
    fill(F, rect_pts(x0, CLASS_DADO_Y, x1, FLOOR), m.wall_b, 0.50 * a, "mid")
    _seat_hatch(F, (x0, CLASS_DADO_Y, x1, FLOOR), m.wall_a, 0.06, 34, 12, 0.20 * a, 913, wob=1.6)
    _marks(F, _geo_tiles(x0, x1, 960.0, 1130.0, FLOOR + 9.0), m.far, 2.4, 0.22 * a, "mid")


def _class_back(F, S, a):
    class_back(F, a * ease(S.cue("wall", F.t)), S.mood)


def _class_view(F, S, a, lit=None, wire=None):
    window_view(F, S.mood, a * ease(S.cue("view", F.t)), 1.0 if lit is None else lit, wire)


def classroom(desk_dx: float = 0.0, mood: str = "day", chair_dx: float = 0.0, desk_s: float = CLASS_DESK_S, dx: float = 0.0,
              side: int = -1) -> Place:
    """The classroom from the back. desk_dx: how far the desk that stands apart has been pushed (world
    units, + = right); chair_dx likewise for its chair; desk_s: the desk's scale (its top is
    95 * desk_s above the floor: CLASS_DESK_TOP_Y at the default); dx: where the classroom stands.
    side: where the pair stands apart. -1: left of the rows (CLASS_DESK, CLASS_CHAIR; + desk_dx is
    toward the rows). +1: right of the rows, past the window (CLASS_DESK_R, CLASS_CHAIR_R, the chair
    turned to face the rows; - desk_dx is toward the rows): where a child that has trudged to the
    right past the rows comes to it.

    Groups in paint order: wall (dado_l dado_r), window (the room's window, no curtains), board,
    clock, pins, door, lamps (lamp0-2), lone (desk.* chair.*). The rows of pupils are not drawn:
    their seats are CLASS_ROWS (x 740 to 1700 is left free)."""
    m = _mood(mood)
    l, t, r, b = WINDOW
    wall = Sketch([_ln(WALL_LINE_X[0], CLASS_DADO_Y, l - 34, CLASS_DADO_Y + 2, m.far, 3.0, 0.62, 1701, "dado_l", wob=1.0, step=16.0),
                   _ln(r + 34, CLASS_DADO_Y + 1, WALL_LINE_X[1], CLASS_DADO_Y + 3, m.far, 3.0, 0.62, 1702, "dado_r", wob=1.0, step=16.0)], "wall")
    cx, dkx = (CLASS_CHAIR[0], CLASS_DESK[0]) if side < 0 else (CLASS_CHAIR_R[0], CLASS_DESK_R[0])
    lone = Sketch([chair(cx + chair_dx, FLOOR, 0.85 * desk_s, 1 if side < 0 else -1, 1310, m.near, 0.95, m, name="chair"),
                   desk(dkx + desk_dx, FLOOR, desk_s, 1300, m.near, 0.95, m, name="desk")], "lone")
    lamps = Sketch([_pendant(x, y, s, 1720 + 10 * j, m.mid, m, f"lamp{j}") for j, (x, y, s) in enumerate(CLASS_LAMPS)], "lamps")
    return Place("classroom", m, dict(
        wall=wall,
        window=window(curtains=False, mood=m),
        board=board(mood=m),
        clock=_clock(*CLASS_CLOCK, 1750, m.mid, m),
        pins=_pins(1770, m),
        door=door(mood=m),
        lamps=lamps,
        lone=lone), back=_class_back, view=_class_view).at(dx)


# ---------------------------------------------------------------------------------------------
# the home table (48.27 to 56.0): a memory, drawn with love, coming apart
# ---------------------------------------------------------------------------------------------
HOME_X = 1010.0                                       # middle of the table
HOME_TABLE = (HOME_X - 300.0, FLOOR - 162.0, HOME_X + 300.0, FLOOR - 142.0)      # the top slab: l, t, r, b
HOME_LAMP = (HOME_X + 6.0, 318.0)                     # middle of the hanging lamp's rim (its light falls from here)
HOME_CHAIR_S = 1.5                                    # the three chairs: seat 96 above the floor, back 252
HOME_SLIDE = (170.0, 316.0)                           # how far the left and the right end chair slide away at apart = 1 (the right one ends before the curtain)


def home_anchors(apart: float = 0.0, dx: float = 0.0) -> dict:
    """Where things are at the home table (world points): child (floor point behind the table, at the
    middle chair), adult_l / adult_r (floor points of the two end chairs), seat_y, drawing (where the
    family drawing lies on the table), cup_l / cup_r, lamp (rim of the hanging lamp), top_y."""
    l, t, r, b = HOME_TABLE
    l, r, hx = l + dx, r + dx, HOME_X + dx
    return {"child": (hx, FLOOR), "adult_l": (l - 36.0 - HOME_SLIDE[0] * apart, FLOOR), "adult_r": (r + 36.0 + HOME_SLIDE[1] * apart, FLOOR),
            "seat_y": FLOOR - 64.0 * HOME_CHAIR_S, "top_y": t, "drawing": (hx, t - 2.0), "cup_l": (l + 110.0, t), "cup_r": (r - 96.0, t),
            "lamp": (HOME_LAMP[0] + dx, HOME_LAMP[1])}


def _cup(x, y, s, face, seed, col, m, name) -> Sketch:
    """A cup as the simplest marks: the bowl (+ .fill), the ear, a thread of steam. (x, y) = middle of its foot."""
    P = np.vstack([A((x - 17 * s, y - 30 * s)), spline(A((x - 17 * s, y - 30 * s), (x - 15 * s, y - 10 * s), (x - 9 * s, y - 1 * s), (x + 9 * s, y - 1 * s),
                                                           (x + 15 * s, y - 10 * s), (x + 17 * s, y - 31 * s)), 12), A((x - 17 * s, y - 30 * s))])
    return Sketch([Fill(P, m.cloth, 0.3, 4 * s, 3 * s, 0.0, seed, knock=m.knock, base=0.65, name="bowl.fill"),
                   Stroke(P, col, 3.2 * s, 0.95, seed + 1, "bowl", wob=0.5),
                   Stroke(arc(x + 17 * s * face, y - 18 * s, 9 * s, 8 * s, -math.pi / 2 * face, math.pi / 2 * face, 8), col, 2.8 * s, 0.9, seed + 2, "ear", wob=0.3),
                   Stroke(spline(A((x - 2 * s, y - 40 * s), (x + 5 * s, y - 54 * s), (x - 4 * s, y - 68 * s), (x + 3 * s, y - 84 * s)), 10), m.far, 2.2 * s, 0.6,
                          seed + 3, "steam", wob=0.4)], name)


def home_table(apart: float = 0.0, mood: str = "night", win: bool = True, dx: float = 0.0) -> Place:
    """The home table from the side: the table with its cloth, three chairs (the child's in the
    middle behind the table; the two end chairs slide away by `apart` = 0..1), the hanging lamp,
    two cups, and behind it the room's window (win=False leaves it out).

    Groups in paint order: window, lamp, chair_m, chair_l, chair_r, table, cups. Draw the child after
    chair_m, the two adults after chair_l / chair_r, the family drawing after the table (home_anchors)."""
    m = _mood(mood)
    col = m.near
    l, t, r, b = HOME_TABLE
    s = HOME_CHAIR_S
    an = home_anchors(apart)
    # the child's chair, seen from the front behind the table: two posts, top rail, two slats, the seat's edge
    cx, sy = HOME_X, FLOOR - 64 * s
    cm = Sketch([
        Stroke(A((cx - 44, sy), (cx - 46, sy - 96), (cx - 42, sy - 150)), mix(col, m.mid, 0.5), 4.4, 0.9, 2001, "post_l"),
        Stroke(A((cx + 44, sy), (cx + 46, sy - 96), (cx + 43, sy - 151)), mix(col, m.mid, 0.5), 4.4, 0.9, 2002, "post_r"),
        Fill(_poly((cx - 48, sy - 152), (cx + 49, sy - 154), (cx + 48, sy - 132), (cx - 47, sy - 130)), m.wood, 0.1, 6, 4, 0.5, 2003, knock=m.knock, base=0.55,
             name="rail.fill"),
        _cl(_poly((cx - 48, sy - 152), (cx + 49, sy - 154), (cx + 48, sy - 132), (cx - 47, sy - 130)), mix(col, m.mid, 0.5), 3.8, 0.9, 2004, "rail", wob=0.7),
        _ln(cx - 44, sy - 92, cx + 45, sy - 94, mix(col, m.mid, 0.5), 3.8, 0.85, 2005, "slat"),
        _ln(cx - 50, sy - 2, cx + 50, sy - 3, mix(col, m.mid, 0.5), 4.2, 0.9, 2006, "seat"),
    ], "chair_m")
    # the table: far legs, near legs, the cloth hanging over the long side with a scalloped hem, the top
    hem_x = np.linspace(l + 46, r - 46, 25)
    hem = np.stack([hem_x, b + 62 + 9 * np.abs(np.sin(np.linspace(0, 6 * math.pi, 25)))], axis=1)
    cloth = np.vstack([A((l + 40, b - 2)), A((l + 46, b + 60)), hem, A((r - 46, b + 60)), A((r - 40, b - 2)), A((l + 40, b - 2))])
    top = _poly((l - 8, t), (r + 8, t - 2), (r + 6, b), (l - 6, b + 2))
    table = Sketch([
        _ln(l + 58, b + 30, l + 60, FLOOR - 10, mix(col, m.far, 0.7), 3.4, 0.75, 2011, "leg_fl"),
        _ln(r - 58, b + 30, r - 60, FLOOR - 10, mix(col, m.far, 0.7), 3.4, 0.75, 2012, "leg_fr"),
        Stroke(A((l + 22, b), (l + 20, b + 80), (l + 14, FLOOR)), col, 6.0, 0.95, 2013, "leg_l"),
        Stroke(A((r - 22, b), (r - 20, b + 80), (r - 14, FLOOR)), col, 6.0, 0.95, 2014, "leg_r"),
        Fill(cloth, m.cloth, 1.45, 15, 7, 0.5, 2015, knock=m.knock, base=0.5, name="cloth.fill"),
        Stroke(cloth[1:-2], mix(col, m.mid, 0.3), 3.4, 0.9, 2016, "cloth", wob=0.6, step=5.0),
        Fill(top, m.wood, 0.08, 7, 4.5, 0.5, 2017, knock=m.knock, base=0.62, name="top.fill"),
        _cl(top, col, 5.0, 1.0, 2018, "top"),
    ], "table")
    # the lamp hanging over the table: cord from above the frame, a wide shade with a scalloped rim
    lx, ly = HOME_LAMP
    rim_x = np.linspace(lx - 92, lx + 92, 13)
    rim = np.stack([rim_x, ly + 7 * np.abs(np.sin(np.linspace(0, 6 * math.pi, 13)))], axis=1)
    shade = np.vstack([A((lx - 92, ly)), spline(A((lx - 92, ly), (lx - 70, ly - 44), (lx - 22, ly - 70), (lx + 22, ly - 70), (lx + 70, ly - 44), (lx + 92, ly)), 16),
                       rim[::-1]])
    lampk = Sketch([
        _ln(lx + 2, -150.0, lx, ly - 70, mix(col, m.far, 0.5), 2.8, 0.8, 2021, "cord", wob=0.5, step=10.0),
        Fill(shade, m.shade, 1.3, 9, 4.5, 0.6, 2022, knock=m.knock, base=0.5, name="shade.fill"),
        _cl(shade, mix(col, m.mid, 0.3), 4.0, 0.95, 2023, "shade", wob=0.7),
        Stroke(arc(lx, ly + 4, 15, 13, 0.15, math.pi - 0.15, 8), mix(col, C.CHALK, 0.4), 3.0, 0.9, 2024, "bulb", wob=0.3),
    ], "lamp")
    cups = Sketch([_cup(an["cup_l"][0], an["cup_l"][1], 1.0, -1, 2031, col, m, "cup_l"), _cup(an["cup_r"][0], an["cup_r"][1], 1.0, 1, 2041, col, m, "cup_r")],
                  "cups")
    groups = {}
    if win:
        groups["window"] = window(mood=m)
    groups.update(lamp=lampk, chair_m=cm,
                  chair_l=chair(an["adult_l"][0], FLOOR, s, 1, 2050, mix(col, m.mid, 0.25), 0.95, m, name="chair_l"),
                  chair_r=chair(an["adult_r"][0], FLOOR, s, -1, 2070, mix(col, m.mid, 0.25), 0.95, m, name="chair_r"),
                  table=table, cups=cups)
    P = Place("home", m, groups, back=_home_back, view=_home_view)
    P.apart = apart
    return P.at(dx)


def _geo_island(cx, y0, rx, depth):
    key = ("island", cx, y0, rx, depth)
    if key not in _GEO:
        near, far = [], []
        for j in range(13):
            u = (j + 0.5) / 13.0 * 2.0 - 1.0 + 0.05 * rsym(j, 81)
            xa = cx + u * rx
            ln = depth * math.sqrt(max(0.04, 1.0 - u * u)) * (0.75 + 0.25 * rnd(j, 82))
            P = _seated(A((xa, y0), (cx + (xa - cx) * (1.0 + 1.3 * ln / 388.0), y0 + ln)), 2090 + j, 1.0, 14.0)
            (near if abs(u) < 0.55 else far).append(P)
        _GEO[key] = (near, far)
    return _GEO[key]


def home_back(F: Frame, a: float = 1.0, mood="night", apart: float = 0.0):
    """The home table's dressing (a memory has no walls): an island of floorboards under the table
    that thins out toward its edges, and rubbed shade where the table and the chairs stand. a = pressure."""
    if a <= 0.003:
        return
    m = _mood(mood)
    an = home_anchors(apart)
    near, far = _geo_island(HOME_X, FLOOR + 9.0, 620.0, 250.0)
    _marks(F, near, m.far, 2.6, 0.32 * a, "mid")
    _marks(F, far, m.far, 2.4, 0.17 * a, "mid")
    smudge(F, HOME_X, FLOOR + 12, 360, 24, C.PAPER_DEEP, 0.8 * a, "soft")
    smudge(F, an["adult_l"][0], FLOOR + 10, 80, 15, C.PAPER_DEEP, 0.7 * a, "soft")
    smudge(F, an["adult_r"][0], FLOOR + 10, 80, 15, C.PAPER_DEEP, 0.7 * a, "soft")


def _home_back(F, S, a):
    home_back(F, a * ease(S.cue("shade", F.t)), S.mood, getattr(S, "apart", 0.0))


def _home_view(F, S, a, lit=None, wire=None):
    if "window" in S:
        window_view(F, S.mood, a * ease(S.cue("view", F.t)), 1.0 if lit is None else lit, wire)


# ---------------------------------------------------------------------------------------------
# the corridor (103.5 to 115.8): a place to be passed in
# ---------------------------------------------------------------------------------------------
COR_BASE_Y = FLOOR - 44.0                             # where the corridor's wall meets its floor
COR_EDGE_Y = FLOOR + 66.0                             # the near side of the lit floor band (the ground line runs along its middle; the floor goes on in front of it)
COR_X = (-3000.0, 5000.0)                             # how far the corridor's dressing reaches: past any framing of the film
COR_LINE_X = (-1400.0, 3300.0)                        # ... and the two long lines of its floor band
COR_CORNER_X = 1450.0                                 # the end of the long wall; right of it the end wall with its window
COR_WINDOW = (1520.0, 150.0, 1760.0, 596.0)           # the window at the end: l, t, r, b
COR_LOCKERS = (640.0, 300.0, 1180.0, 6)               # l, t, r, how many (they stand on COR_BASE_Y)
COR_HOOKS = (190.0, 392.0, 570.0)                     # the rail of coat hooks: l, y, r
COR_LAMPS = ((380.0, 96.0, 0.9), (1010.0, 88.0, 0.85), (1640.0, 80.0, 0.8))


def _lockers(l, t, r, n, seed, m, name) -> Sketch:
    """A block of n lockers standing on COR_BASE_Y: frame (+ .fill), dividers d1.., a vent and a lock on each."""
    b = COR_BASE_Y
    line = mix(m.far, m.mid, 0.6)
    w = (r - l) / n
    sk = [Fill(rect_pts(l, t, r, b), m.wood, 1.5, 19, 7, 0.36, seed, knock=m.knock, base=0.36, name="frame.fill"),
          Stroke(A((l, b), (l, t), (r, t + 2), (r + 1, b)), line, 4.0, 0.9, seed + 1, "frame")]
    for j in range(1, n):
        sk.append(_ln(l + j * w, t + 3, l + j * w + 1, b, mix(line, m.far, 0.4), 3.0, 0.8, seed + 1 + j, f"d{j}"))
    for j in range(n):
        x = l + (j + 0.5) * w
        sk.append(Stroke(A((x - 20, t + 34), (x + 20, t + 34), (x - 20, t + 46), (x + 20, t + 46), (x - 20, t + 58), (x + 20, t + 58)), m.far, 2.4, 0.75,
                         seed + 20 + j, f"vent{j}", wob=0.3))
        sk.append(_ln(x + w * 0.30, t + 170, x + w * 0.30, t + 196, line, 3.4, 0.85, seed + 40 + j, f"lock{j}", wob=0.2))
    return Sketch(sk, name)


def _coat(x, y, s, seed, m, bag=False, name="coat") -> Sketch:
    """A coat (or a satchel) hanging from a hook at (x, y): a soft dark mass with an outline."""
    line = mix(m.far, m.mid, 0.6)
    if bag:
        P = spline(A((x - 26 * s, y + 44 * s), (x - 30 * s, y + 96 * s), (x, y + 108 * s), (x + 30 * s, y + 96 * s), (x + 26 * s, y + 44 * s),
                     (x, y + 38 * s), (x - 26 * s, y + 44 * s)), 22)
        return Sketch([Stroke(A((x - 16 * s, y + 44 * s), (x, y + 2), (x + 16 * s, y + 44 * s)), m.far, 2.6, 0.8, seed + 2, "strap", wob=0.4),
                       Fill(P, m.sofa, 0.5, 8, 4.5, 0.5, seed, knock=m.knock, base=0.5, name="body.fill"),
                       Stroke(P, line, 3.2, 0.85, seed + 1, "body", wob=0.7),
                       _ln(x - 24 * s, y + 62 * s, x + 24 * s, y + 61 * s, m.far, 2.4, 0.7, seed + 3, "flap", wob=0.4)], name)
    # a jacket on its loop: collar, shoulders, two sleeves hanging, a straight hem
    P = spline(A((x, y + 4), (x - 16 * s, y + 12 * s), (x - 44 * s, y + 30 * s), (x - 56 * s, y + 118 * s), (x - 40 * s, y + 122 * s), (x - 36 * s, y + 70 * s),
                 (x - 34 * s, y + 150 * s), (x, y + 154 * s), (x + 34 * s, y + 150 * s), (x + 36 * s, y + 70 * s), (x + 40 * s, y + 122 * s),
                 (x + 56 * s, y + 118 * s), (x + 44 * s, y + 30 * s), (x + 16 * s, y + 12 * s), (x, y + 4)), 44)
    return Sketch([Fill(P, m.curtain, 1.4, 11, 5.5, 0.5, seed, knock=m.knock, base=0.5, name="body.fill"),
                   Stroke(P, line, 3.2, 0.85, seed + 1, "body", wob=0.7),
                   Stroke(A((x, y + 18 * s), (x + 2 * s, y + 80 * s), (x, y + 150 * s)), m.far, 2.4, 0.7, seed + 2, "zip", wob=0.4)], name)


def _geo_cor(x0, x1, vx=960.0, bottom=1140.0):
    """The corridor floor's joints: those of the lit band along the wall, their continuations toward
    the viewer (the same floor, in shadow), and the cross joints of the near floor."""
    key = ("cor", x0, x1, vx, bottom)
    if key not in _GEO:
        band, near = [], []
        j = 0
        x = x0
        while x < x1:
            k = (COR_EDGE_Y - COR_BASE_Y) / 760.0
            xe = vx + (x - vx) * (1.0 + k)                              # where this joint meets the band's near edge
            xb = vx + (x - vx) * (1.0 + (bottom - COR_BASE_Y) / 760.0)
            band.append(_seated(A((x, COR_BASE_Y + 5), (xe, COR_EDGE_Y - 3)), 2600 + j, 0.7, 16.0))
            near.append(_seated(A((xe, COR_EDGE_Y + 5), (xb, bottom)), 2700 + j, 0.9, 16.0))
            x += 150.0 + 26.0 * rsym(j, 71)
            j += 1
        for q, d in enumerate((74.0, 176.0)):
            near.append(_seated(A((x0, COR_EDGE_Y + d), (x1, COR_EDGE_Y + d + 2)), 2690 + q, 1.0, 22.0))
        _GEO[key] = (band, near)
    return _GEO[key]


def corridor_back(F: Frame, a: float = 1.0, mood="night", x0=COR_X[0], x1=COR_X[1]):
    """The corridor's seated dressing: the long wall (darker below the dado), the paler end wall right
    of the corner, the floor: one narrow lit band along the wall (the ground line runs along its
    middle) and, in front of it, the same tiled floor going on toward us in shadow. It is a floor on
    both sides of the line, never an edge to fall from."""
    if a <= 0.003:
        return
    m = _mood(mood)
    _seat_hatch(F, (x0, TOP_Y, COR_CORNER_X, COR_BASE_Y), m.wall_a, 1.42, 60, 15, 0.26 * a, 931)
    _seat_hatch(F, (COR_CORNER_X, TOP_Y, x1, COR_BASE_Y), mix(m.wall_a, C.CHALK_DIM, 0.3), 1.2, 44, 16, 0.30 * a, 932)
    fill(F, rect_pts(x0, 548.0, COR_CORNER_X, COR_BASE_Y), m.wall_b, 0.42 * a, "mid")
    floor = (0.24, 0.29, 0.43)
    fill(F, rect_pts(x0, COR_BASE_Y, x1, COR_EDGE_Y), floor, 0.36 * a, "mid")
    wash(F, rect_pts(x0, COR_EDGE_Y, x1, 1140.0), floor, COR_EDGE_Y, COR_EDGE_Y + 300, [0.24 * a, 0.15 * a, 0.07 * a, 0.0], "mid")
    band, near = _geo_cor(x0, x1)
    _marks(F, band, m.far, 2.4, 0.30 * a, "mid")
    _marks(F, near, m.far, 2.4, 0.17 * a, "mid")


def _cor_back(F, S, a):
    corridor_back(F, a * ease(S.cue("wall", F.t)), S.mood)


def _cor_view(F, S, a, lit=None, wire=None):
    corridor_view(F, a * ease(S.cue("view", F.t)), S.mood)


def corridor_view(F: Frame, a: float = 1.0, mood="night"):
    """The pane of the window at the corridor's end: a flat pale evening, nothing in it."""
    if a <= 0.003:
        return
    l, t, r, b = COR_WINDOW
    with F.clip(rect=(l, t, r, b)):
        fill(F, rect_pts(l, t, r, b), C.PAPER_DEEP, 0.9 * a)
        fill(F, rect_pts(l, t, r, b), (0.46, 0.51, 0.62), 0.95 * a, "glow")
        wash(F, rect_pts(l, t, r, b), (0.74, 0.77, 0.82), t + 60, b, [0.0, 0.4 * a, 0.75 * a], "soft")
        _marks(F, _geo_sky(l, t + 60, r, b), (0.74, 0.77, 0.82), 12.0, 0.28 * a, "sparse")


def corridor(mood: str = "night", dx: float = 0.0) -> Place:
    """The corridor, seen from the side: one narrow floor band (the ground line runs along its
    middle), a long wall with a door, coats on hooks over a bench, lockers, a notice board; a corner,
    and the end wall with its tall pale window; lamps hanging from above the frame.

    Groups in paint order: floor (base edge corner), far (lockers_b door_b), window, door, hooks
    (rail coat0-2 bag bench.*), lockers, notice, lamps (lamp0-2)."""
    m = _mood(mood)
    line = mix(m.far, m.mid, 0.6)
    x0, x1 = COR_LINE_X
    floor = Sketch([_ln(x0, COR_BASE_Y, x1, COR_BASE_Y + 2, m.far, 3.0, 0.75, 2601, "base", wob=1.0, step=16.0),
                    _ln(x0, COR_EDGE_Y, x1, COR_EDGE_Y + 3, m.far, 3.0, 0.42, 2602, "edge", wob=1.2, step=16.0),
                    _ln(COR_CORNER_X, -150.0, COR_CORNER_X + 3, COR_BASE_Y, line, 3.4, 0.8, 2603, "corner", wob=0.9, step=10.0)], "floor")
    far = Sketch([_lockers(-660.0, 300.0, -120.0, 6, 2700, m, "lockers_b"),
                  door(1850.0, 226.0, 2020.0, COR_BASE_Y, 2760, line, m, side=-1, name="door_b")], "far")
    l, t, r, b = COR_WINDOW
    cw = Sketch([_cl(rect_pts(l, t, r, b), m.near, 5.0, 0.95, 2611, "frame"),
                 _cl(rect_pts(l + 13, t + 13, r - 13, b - 13), m.near, 2.8, 0.65, 2612, "inner"),
                 _ln((l + r) / 2, t + 4, (l + r) / 2 + 2, b - 4, m.near, 4.0, 0.9, 2613, "mullion"),
                 _ln(l + 4, t + (b - t) * 0.36, r - 4, t + (b - t) * 0.36 + 2, m.near, 4.0, 0.9, 2614, "transom"),
                 _ln(l - 24, b + 12, r + 24, b + 14, m.near, 5.6, 0.95, 2615, "sill")], "window")
    hl, hy, hr = COR_HOOKS
    hooks = Sketch([_ln(hl, hy, hr, hy + 2, line, 4.2, 0.85, 2621, "rail"),
                    _coat(hl + 50, hy + 4, 1.0, 2630, m, name="coat0"), _coat(hl + 150, hy + 4, 0.92, 2640, m, name="coat1"),
                    _coat(hl + 250, hy + 4, 1.0, 2650, m, bag=True, name="bag"), _coat(hl + 338, hy + 4, 1.04, 2660, m, name="coat2"),
                    Fill(rect_pts(hl - 12, 622, hr + 12, 638), m.wood, 0.1, 6, 4, 0.5, 2671, knock=m.knock, base=0.55, name="bench.seat.fill"),
                    _cl(rect_pts(hl - 12, 622, hr + 12, 638), line, 3.8, 0.9, 2672, "bench.seat"),
                    _ln(hl + 10, 638, hl + 8, COR_BASE_Y, line, 4.0, 0.85, 2673, "bench.leg_l"),
                    _ln(hr - 10, 638, hr - 8, COR_BASE_Y, line, 4.0, 0.85, 2674, "bench.leg_r")], "hooks")
    nl, nt, nr, nb = 1215.0, 326.0, 1378.0, 478.0
    notice = Sketch([Fill(rect_pts(nl, nt, nr, nb), m.cloth, 0.3, 10, 5, 0.0, 2681, knock=m.knock, base=0.26, name="frame.fill"),
                     _cl(rect_pts(nl, nt, nr, nb), line, 3.6, 0.85, 2682, "frame", wob=0.8),
                     Stroke(_scribble(nl + 18, nr - 20, nt + 40, 5.0, 2684), m.far, 2.4, 0.8, 2685, "line0", wob=0.3, step=4.0),
                     Stroke(_scribble(nl + 18, nr - 46, nt + 74, 5.0, 2686), m.far, 2.4, 0.8, 2687, "line1", wob=0.3, step=4.0),
                     _cl(rect_pts(nl + 22, nt + 96, nl + 76, nb - 14), m.far, 2.4, 0.8, 2688, "sheet", wob=0.6)], "notice")
    lamps = Sketch([_pendant(x, y, s, 2740 + 10 * j, m.mid, m, f"lamp{j}") for j, (x, y, s) in enumerate(COR_LAMPS)], "lamps")
    return Place("corridor", m, dict(
        floor=floor, far=far, window=cw,
        door=door(-70.0, 226.0, 120.0, COR_BASE_Y, 2690, line, m, name="door"),
        hooks=hooks,
        lockers=_lockers(*COR_LOCKERS, 2710, m, "lockers"),
        notice=notice, lamps=lamps), back=_cor_back, view=_cor_view).at(dx)


# ---------------------------------------------------------------------------------------------
# one set turning into another: the declared changes
# ---------------------------------------------------------------------------------------------
def _under(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(prefix + ".")


def _travel(sa: Stroke, sb: Stroke, wi: float, seed: int) -> Stroke:
    """Stroke sa on its way to sb at wi = 0..1 (the kit's morph for one pair, spanning the whole of wi)."""
    if wi <= 0.0:
        return sa
    if wi >= 1.0:
        return sb
    out = morph(Sketch([sa.copy(name="a")]), Sketch([sb.copy(name="b")]), 0.2 + 0.6 * wi, (("a", "b"),), stagger=0.0, seed=seed).items[0]
    out.name = sb.name
    return out


def between(A, B, w: float, pairs=(), plan=(), keep=(), off=(0.0, 0.5), move=(0.2, 0.8), on=(0.5, 1.0), stagger: float = 0.5,
            lag: float = 0.4, seed: int = 7) -> dict:
    """The groups between two Places at w = 0..1. A or B may be None (the bare sheet).

    pairs: ((name_in_A, name_in_B), ...): a name is one stroke, or a prefix whose strokes pair in
    order. Only these travel. keep: prefixes that are the same in both and simply stay (drawn from B).
    plan: ((w0, w1, prefix, ...), ...): when the items under those prefixes change (un-draw if they
    are A's, travel if paired, draw on if they are B's); "-prefix" names A's items only, "+prefix"
    B's only. Several items under one row follow each other (lag = how much of the row their starts
    are spread over). Everything no row names uses the defaults: A's items un-draw inside `off`, pairs
    travel inside `move`, B's draw on inside `on`, each sweeping the picture left to right (stagger).
    Returns {group: Sketch}: A's leaving groups under "-name" first, then B's groups under their names."""
    w = min(1.0, max(0.0, float(w)))
    ga = [(g, it) for g, sk in (A or {}).items() for it in sk]
    gb = [(g, it) for g, sk in (B or {}).items() for it in sk]
    kept = lambda it: any(_under(it.name, p) for p in keep)
    if B is not None:
        ga = [(g, it) for g, it in ga if not kept(it)]
    sa = [it for _g, it in ga if isinstance(it, Stroke)]
    sb = [it for _g, it in gb if isinstance(it, Stroke) and not kept(it)]
    pair, used = {}, set()
    for na, nb in pairs:
        la = [s for s in sa if _under(s.name, na) and id(s) not in used]
        lb = [s for s in sb if _under(s.name, nb) and id(s) not in pair]
        if not la or not lb:
            raise KeyError(f"change pair {na!r} -> {nb!r}: no free stroke of that name in the {'first' if not la else 'second'} set")
        for x, y in zip(la, lb):
            pair[id(y)] = x
            used.add(id(x))
    back = {id(a): b for b in sb if id(b) in pair for a in [pair[id(b)]]}           # A stroke -> its B stroke
    xs = [it.cx for _g, it in ga] + [it.cx for _g, it in gb] or [0.0]
    x0, span = min(xs), max(1.0, max(xs) - min(xs))
    # explicit windows: each plan row spreads its items' starts over `lag` of the row
    rows = {}
    for row in plan:
        w0, w1, prefixes = row[0], row[1], row[2:]
        for side, items in (("-", [it for _g, it in ga]), ("+", [it for _g, it in gb])):
            hit = [it for it in items if id(it) not in rows and not (side == "+" and kept(it)) and any(
                _under(it.name, p.lstrip("+-")) for p in prefixes if not p.startswith("+" if side == "-" else "-"))]
            n = max(1, sum(1 for it in hit if isinstance(it, Stroke)))
            d = (w1 - w0) * (1.0 - lag * (n > 1))
            j = 0
            for it in hit:                               # a fill comes before its outline and shares its turn
                s0 = w0 + (w1 - w0) * lag * min(j, n - 1) / n
                rows[id(it)] = (s0, s0 + d)
                j += isinstance(it, Stroke)

    def win(it, phase):
        if id(it) in rows:
            return rows[id(it)]
        d = phase[1] - phase[0]
        s0 = phase[0] + d * stagger * min(1.0, max(0.0, (it.cx - x0) / span))
        return s0, s0 + d * (1.0 - stagger)

    def move_win(a, b):
        return rows.get(id(b)) or rows.get(id(a)) or win(b, move)

    out: dict = {}
    for g, it in ga:
        dst = out.setdefault("-" + g, [])
        if id(it) in back:                               # a stroke that travels: it waits in its place until it leaves
            if w <= move_win(it, back[id(it)])[0]:
                dst.append(it)
            continue
        if isinstance(it, Fill) and it.name.endswith(".fill"):
            stem = next((s for s in sa if s.name == it.name[:-5] and id(s) in back), None)
            if stem is not None:                         # its outline travels: the colour is rubbed out just before
                m0 = move_win(stem, back[id(stem)])[0]
                p = seg(w, max(0.0, m0 - 0.14), m0 + 0.02)
                if p < 1.0:
                    dst.append(it.copy(poff=p) if p > 0.0 else it)
                continue
        w0, w1 = win(it, off)
        p = seg(w, w0, w1)
        if isinstance(it, Fill):
            p = min(1.0, p * 1.6)
        if p < 1.0:
            dst.append(it.copy(poff=max(p, it.poff or 0.0)) if p > 0.0 else it)
    for g, it in gb:
        dst = out.setdefault(g, [])
        if kept(it):
            dst.append(it)
        elif isinstance(it, Stroke):
            if id(it) in pair:
                a = pair[id(it)]
                w0, w1 = move_win(a, it)
                if w > w0:
                    dst.append(_travel(a, it, seg(w, w0, w1), seed))
            else:
                p = seg(w, *win(it, on))
                if p > 0.0:
                    dst.append(it.copy(pon=p) if p < 1.0 else it)
        else:
            stem = next((s for s in sb if s.name == it.name[:-5]), None) if it.name.endswith(".fill") else None
            if stem is not None and id(stem) in pair:    # its outline travels: colour it in once that has arrived
                w1 = move_win(pair[id(stem)], stem)[1]
                p = seg(w, w1 - 0.04, min(1.0, w1 + 0.14))
            else:
                w0, w1 = win(stem if stem is not None else it, on)
                p = seg(w, w0 + 0.45 * (w1 - w0), min(1.0, w1 + 0.25 * (w1 - w0)))
            if p > 0.0:
                dst.append(it.copy(pon=p) if p < 1.0 else it)
    return {g: Sketch(items) for g, items in out.items() if items}


class Change(Place):
    """A Place on its way from one set to another (see the *_to_* functions). Use it like a Place:
    S.back(F), light, S.view(F), ground_line(F), S.draw(F). Groups: the leaving set's under "-name",
    then the arriving set's under their own names."""

    def __init__(self, kind, A, B, w, groups, fade_a=(0.05, 0.55), fade_b=(0.4, 0.95), view_a=(0.0, 0.3), view_b=(0.5, 0.9)):
        super().__init__(kind, (B or A).mood, groups)
        self.A, self.B, self.w = A, B, float(w)
        self.dx = (B if B is not None else A).dx
        self.fade_a, self.fade_b, self.view_a, self.view_b = fade_a, fade_b, view_a, view_b

    def draw(self, F, *names, **kw):
        """As Place.draw; a group that has nothing to show at this w is simply skipped."""
        for k in (names or self.keys()):
            if k in self:
                self[k].draw(F, **kw)

    def back(self, F, a=1.0):
        if self.A is not None:
            self.A.back(F, a * (1.0 - ramp(self.w, *self.fade_a)))
        if self.B is not None:
            self.B.back(F, a * ramp(self.w, *self.fade_b))

    def view(self, F, a=1.0, **kw):
        if self.A is not None:
            self.A.view(F, a * (1.0 - ramp(self.w, *self.view_a)), **kw)
        if self.B is not None:
            self.B.view(F, a * ramp(self.w, *self.view_b), **kw)


def _bw(span):
    """(beats after the span's start, length in beats) -> the window in w, for a plan row."""
    d = (span[1] - span[0]) / 0.75
    return lambda k, n: (k / d, min(1.0, (k + n) / d))


_FRAME = ("window.frame", "window.inner", "window.mullion", "window.transom", "window.sill", "window.ledge")

# ---- the room into the classroom (36.27 to 38.6) ----
SPAN_ROOM_TO_CLASS = (36.265, 38.6)
ROOM_TO_CLASS = (("sofa.back", "lone.desk.top"), ("sofa.seat", "lone.desk.box"), ("sofa.arm_l", "lone.chair.seat"),
                 ("lamp.pole", "door.frame"), ("lamp.shade", "door.pane"), ("cushion.shape", "clock.rim"),
                 ("shelf.book0", "pins.sheet0"), ("shelf.book1", "pins.sheet1"), ("shelf.book2", "pins.sheet2"), ("shelf.pot", "pins.sheet3"))


# with the pair on the right (side = +1) the room's table and its right-hand chair, which stand there, become the desk and its chair
ROOM_TO_CLASS_R = (("table.top", "lone.desk.top"), ("table.cloth", "lone.desk.box"), ("table.chair_r.seat", "lone.chair.seat"),
                   ("lamp.pole", "door.frame"), ("lamp.shade", "door.pane"), ("cushion.shape", "clock.rim"),
                   ("shelf.book0", "pins.sheet0"), ("shelf.book1", "pins.sheet1"), ("shelf.book2", "pins.sheet2"), ("shelf.pot", "pins.sheet3"))


def _plan_room_to_class():
    b = _bw(SPAN_ROOM_TO_CLASS)
    return ((*b(0.0, 0.8), "-window.curtain", "-window.rail"), (*b(0.1, 0.8), "-rug"), (*b(0.2, 0.9), "-sofa.throw", "-sofa.fringe"),
            (*b(0.3, 1.0), "-table"), (*b(0.5, 1.0), "-wall"), (*b(0.4, 0.9), "-sofa", "-cushion", "-lamp", "-shelf"),
            (*b(0.6, 1.4), "lone.desk.top", "lone.desk.box", "lone.chair.seat"),
            (*b(0.9, 1.2), "clock.rim"), (*b(1.0, 1.3), "door.frame", "door.pane"), (*b(1.2, 1.3), "pins.sheet0", "pins.sheet1", "pins.sheet2", "pins.sheet3"),
            (*b(1.4, 0.9), "+board.frame"), (*b(1.9, 0.6), "+board.ledge"), (*b(2.0, 1.0), "+board"),
            (*b(1.6, 1.2), "+wall"), (*b(2.0, 0.9), "+lone"), (*b(2.0, 0.8), "+clock"), (*b(2.2, 0.8), "+door"),
            (*b(2.0, 0.5), "+lamps.lamp0"), (*b(2.3, 0.5), "+lamps.lamp1"), (*b(2.6, 0.5), "+lamps.lamp2"), (*b(2.4, 0.7), "+pins"))


def room_to_class(w: float, desk_dx: float = 0.0, mood: str = "night", apart: float = 1.0, dx: float = 0.0, side: int = -1) -> Change:
    """The room turning into the classroom around the child: w = 0 the room (mood), 1 the classroom.
    The window's frame never leaves; its curtains are taken off, the sofa folds into the desk that
    stands apart (side = +1: the table and its right-hand chair do, where they stand, and the sofa is
    simply taken off), the lamp into the door, the cushion into the clock, the shelf's books into the
    pinned drawings; the board, the dado and the hanging lamps draw on. Default span SPAN_ROOM_TO_CLASS."""
    A_, B_ = room(mood, apart, dx=dx), classroom(desk_dx, dx=dx, side=side)
    g = between(A_, B_, w, ROOM_TO_CLASS if side < 0 else ROOM_TO_CLASS_R, _plan_room_to_class(), keep=_FRAME)
    return Change("room_to_class", A_, B_, w, g, view_a=(0.9, 1.0), view_b=(0.3, 0.85))


# ---- the classroom into the home table (48.27 to about 50) ----
SPAN_CLASS_TO_HOME = (48.265, 50.14)
CLASS_TO_HOME = (("lamps.lamp1.cord", "lamp.cord"), ("lamps.lamp1.shade", "lamp.shade"), ("lamps.lamp1.bulb", "lamp.bulb"),
                 ("board.frame", "table.top"), ("board.ledge", "table.cloth"))


def _plan_class_to_home():
    b = _bw(SPAN_CLASS_TO_HOME)
    return ((*b(0.0, 0.6), "-board"), (*b(0.1, 0.7), "-clock", "-pins"), (*b(0.2, 0.8), "-door", "-lamps"), (*b(0.3, 0.9), "-lone"),
            (*b(0.4, 0.9), "-wall"),
            (*b(0.5, 1.2), "lamp.cord", "lamp.shade", "lamp.bulb"), (*b(0.7, 1.3), "table.top", "table.cloth"),
            (*b(1.2, 0.5), "+window.rail"), (*b(1.3, 0.7), "+window.curtain.l"), (*b(1.5, 0.7), "+window.curtain.r"), (*b(1.8, 0.6), "+window.curtain"),
            (*b(1.5, 0.6), "+chair_m"), (*b(1.8, 0.5), "+table"), (*b(1.8, 0.6), "+chair_l"), (*b(1.9, 0.6), "+chair_r"), (*b(2.1, 0.4), "+cups"))


def class_to_home(w: float, desk_dx: float = 0.0, apart: float = 0.0, dx: float = 0.0, side: int = -1) -> Change:
    """The classroom turning into the home table: w = 0 the classroom, 1 the table. The window stays
    and gets its curtains back; the hanging lamp over the middle rows comes down and becomes the lamp
    over the table; the board sinks and flattens into the table top, its ledge into the cloth; the
    chairs and the cups draw on. Default span SPAN_CLASS_TO_HOME."""
    A_, B_ = classroom(desk_dx, dx=dx, side=side), home_table(apart, dx=dx)
    g = between(A_, B_, w, CLASS_TO_HOME, _plan_class_to_home(), keep=_FRAME)
    return Change("class_to_home", A_, B_, w, g, fade_a=(0.05, 0.6), fade_b=(0.6, 1.0), view_a=(0.9, 1.0), view_b=(0.3, 0.8))


# ---- the home table taken back to the bare sheet (55 to 56) ----
SPAN_HOME_TO_BARE = (55.0, 56.0)


def home_to_bare(w: float, apart: float = 1.0, dx: float = 0.0, win: bool = True) -> Change:
    """Every line of the home table is taken back from its ends: w = 0 the table, 1 the bare sheet
    (ghosts gone too). Cups first, then lamp and curtains, the window, the chairs, the table last.
    Groups keep their names with a "-" in front ("-table", "-chair_m" ...). Default span SPAN_HOME_TO_BARE."""
    A_ = home_table(apart, win=win, dx=dx)
    plan = ((0.0, 0.45, "cups"), (0.04, 0.55, "lamp"), (0.08, 0.6, "window.curtain", "window.rail"), (0.2, 0.75, "window"),
            (0.15, 0.7, "chair_l", "chair_r"), (0.3, 0.8, "chair_m"), (0.4, 1.0, "table"))
    g = between(A_, None, w, (), plan, lag=0.3)
    return Change("home_to_bare", A_, None, w, g, fade_a=(0.3, 0.8), view_a=(0.1, 0.45))


# ---- the plain into the evening room (85.75 to 90.5) ----
SPAN_PLAIN_TO_ROOM = (85.765, 90.5)
# the strokes of the scene's own sketches are ranked by length: the five longest of `house` and the two longest of `backs` travel
PLAIN_TO_ROOM = (("house.0", "window.frame"), ("house.1", "window.inner"), ("house.2", "window.sill"), ("house.3", "window.mullion"),
                 ("house.4", "window.transom"), ("backs.0", "window.curtain.l"), ("backs.1", "window.curtain.r"))


def _plan_plain_to_room():
    b = _bw(SPAN_PLAIN_TO_ROOM)
    return ((*b(0.0, 1.2), "-house", "-backs"),
            (*b(0.0, 1.5), "window.frame", "window.inner", "window.sill", "window.mullion", "window.transom"),
            (*b(1.0, 1.4), "window.curtain.l", "window.curtain.r"),
            (*b(1.5, 0.5), "+window.ledge"), (*b(2.0, 0.5), "+window.rail"), (*b(2.4, 0.8), "+window.curtain"),
            (*b(1.0, 1.5), "+wall"),
            (*b(2.0, 1.0), "+sofa.back"), (*b(3.0, 0.6), "+sofa.arm_l", "+sofa.roll_l"), (*b(3.3, 0.6), "+sofa.arm_r", "+sofa.roll_r"),
            (*b(3.6, 0.8), "+sofa.seat"), (*b(4.2, 0.6), "+sofa.split", "+sofa.leg_l", "+sofa.leg_r"), (*b(4.4, 0.8), "+sofa.throw", "+sofa.fringe"),
            (*b(4.6, 0.7), "+cushion"), (*b(4.0, 0.9), "+lamp"), (*b(4.4, 1.2), "+rug"),
            (*b(5.0, 0.7), "+table.leg_l", "+table.leg_r", "+table.cloth", "+table.top"), (*b(5.2, 0.8), "+table.chair_m"),
            (*b(5.4, 0.8), "+table.chair_l", "+table.chair_r"), (*b(5.6, 0.6), "+table"), (*b(5.4, 0.9), "+shelf"))


def _ranked(sk, n: int, name: str):
    """The n longest strokes of a foreign sketch, longest first, as copies named name.0, name.1 ...;
    the rest as copies named name.rest.j (they are simply taken off)."""
    st = [it for it in Sketch([sk]) if isinstance(it, Stroke)]
    ln = [float(np.hypot(np.diff(s.P[:, 0]), np.diff(s.P[:, 1])).sum()) for s in st]
    order = sorted(range(len(st)), key=lambda i: -ln[i])
    out = [st[i].copy(name=f"{name}.{j}" if j < n else f"{name}.rest.{j}") for j, i in enumerate(order)]
    return out


def plain_to_room(w: float, house=None, backs=None, mood: str = "eve", apart: float = 1.0, dx: float = 0.0) -> Change:
    """The evening room drawing itself on around the walking child: w = 0 nothing of it, 1 the room.
    house, backs: optional Sketches of the plain's towering drawings, ALREADY placed where they stand
    in the room's coordinates: the five longest strokes of `house` travel into the window's frame and
    bars, the two longest of `backs` into the two curtains; their other strokes are taken off. Without
    them the window simply draws on first. Then, a part per beat: wall lines, sofa, lamp, rug, table,
    shelf; the wall's hatch and the view through the window come up meanwhile. Default span SPAN_PLAIN_TO_ROOM."""
    B_ = room(mood, apart, dx=dx)
    old = {}
    if house is not None:
        old["house"] = Sketch(_ranked(house, 5, "house"))
    if backs is not None:
        old["backs"] = Sketch(_ranked(backs, 2, "backs"))
    have = {it.name for sk in old.values() for it in sk}
    pairs = [p for p in PLAIN_TO_ROOM if p[0] in have]
    A_ = Place("plain", mood, old) if old else None
    g = between(A_, B_, w, pairs, _plan_plain_to_room())
    b = _bw(SPAN_PLAIN_TO_ROOM)
    return Change("plain_to_room", None, B_, w, g, fade_b=(b(0.5, 3.0)), view_b=b(1.6, 1.4))


# ---- the evening room into the corridor (101.5 to 104.5: the room is taken off, its bones become the corridor) ----
SPAN_ROOM_TO_CORRIDOR = (101.515, 104.515)
ROOM_TO_CORRIDOR = (("window.frame", "window.frame"), ("window.inner", "window.inner"), ("window.mullion", "window.mullion"),
                    ("window.transom", "window.transom"), ("window.sill", "window.sill"),
                    ("sofa.back", "lockers.frame"), ("sofa.seat", "hooks.bench.seat"), ("lamp.pole", "door.frame"),
                    ("rug.outer", "floor.edge"), ("wall.skirt", "floor.base"), ("window.curtain.l", "notice.frame"))


def _plan_room_to_corridor():
    b = _bw(SPAN_ROOM_TO_CORRIDOR)
    return ((*b(0.0, 1.2), "-table", "-shelf"), (*b(0.3, 1.1), "-window.curtain", "-window.rail", "-window.ledge"),
            (*b(0.6, 1.2), "-cushion", "-sofa"), (*b(0.9, 1.1), "-rug", "-lamp"), (*b(1.2, 1.0), "-wall"),
            (*b(1.7, 1.3), "floor.base", "floor.edge"),
            (*b(2.2, 1.3), "window.frame", "window.inner", "window.mullion", "window.transom", "window.sill"),
            (*b(2.5, 1.1), "lockers.frame", "hooks.bench.seat"), (*b(2.7, 1.0), "door.frame", "notice.frame"),
            (*b(3.0, 0.5), "+floor.corner"), (*b(3.2, 0.7), "+lockers"), (*b(3.3, 0.65), "+hooks"), (*b(3.4, 0.55), "+door", "+notice"),
            (*b(3.5, 0.5), "+lamps", "+far"))


def room_to_corridor(w: float, mood: str = "eve", apart: float = 1.0, dx: float = 0.0) -> Change:
    """The evening room turning into the corridor: w = 0 the room, 1 the corridor. First the room is
    taken off down to its bones (window, the sofa's two outlines, the lamp's pole, the rug's rim, the
    skirting line, one curtain); then the bones travel: the skirting line becomes the foot of the
    corridor's wall and the rug's rim the near side of the lit floor band, the window goes to the
    corridor's end and grows tall, the sofa's back opens into the lockers, its seat into the bench,
    the lamp into the door, the curtain into the notice board; the rest of the corridor draws on last.
    Default span SPAN_ROOM_TO_CORRIDOR (four beats)."""
    A_, B_ = room(mood, apart, dx=dx), corridor(dx=dx)
    g = between(A_, B_, w, ROOM_TO_CORRIDOR, _plan_room_to_corridor(), lag=0.5)
    return Change("room_to_corridor", A_, B_, w, g, fade_a=(0.12, 0.6), fade_b=(0.55, 0.95), view_a=(0.4, 0.58), view_b=(0.84, 0.99))


# ---- the corridor taken back to the bare sheet (114.27 to 115.77) ----
SPAN_CORRIDOR_TO_BARE = (114.265, 115.765)


def corridor_to_bare(w: float, dx: float = 0.0) -> Change:
    """The corridor is taken back from its ends: w = 0 the corridor, 1 the bare sheet. Lamps and the
    far things first, then notice board, lockers, coats and bench, the doors, the window; the two long
    lines of the floor band go last. Groups keep their names with a "-" in front. Default span SPAN_CORRIDOR_TO_BARE."""
    A_ = corridor(dx=dx)
    plan = ((0.0, 0.4, "lamps", "far"), (0.08, 0.5, "notice"), (0.14, 0.62, "lockers"), (0.22, 0.7, "hooks"), (0.3, 0.75, "door"),
            (0.36, 0.84, "window"), (0.5, 0.9, "floor.corner"), (0.58, 1.0, "floor.base", "floor.edge"))
    g = between(A_, None, w, (), plan, lag=0.3)
    return Change("corridor_to_bare", A_, None, w, g, fade_a=(0.2, 0.8), view_a=(0.3, 0.6))
