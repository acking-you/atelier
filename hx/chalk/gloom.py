"""hx.chalk.gloom: the weight. The only black on the sheet: a child's tired, angry scribbling.

One scribble in many forms (doc: hx/chalk/doc/gloom.md):

    gloom       the cloud over the child, with a belly that rests on a head     band_cloud
    shawl       the mass settled on a sitting child's shoulders and back        band_shawl
    ceiling     the lid across the top of a wide frame, with a thin pale place  band_ceiling, lid_for
    curtains    the lid let down to the ground; parted strand by strand (peel, or by the grips of a
                performance; curtain_gap), held by hands; ripped: loose curls that fall, pieces of lid
                that drift off, one piece that stays
    remnant     that piece; wind_up: it winds itself up into the small tangle on its string
    handoff_gloom   the scribble's state at each hand-off of hx/story.py, as one call
    mass        draws any Band. One form becomes the next without a pop through the band between
                them: spread_band (a cloud opens into a lid; ceiling / curtains take cloud=, spread=),
                morph_band (a mass draws in to another shape; shawl takes cloud=, settle=), mix_band
    strand      the thin dark line from the child into the mass (slack .. taut, trembling)
    cross_out   a quick angry zigzag drawn on in four frames; later a rubbed ghost
    unravel     a loose end pulled out into one long line that coils on the ground
    tangle      the small knot (in a speech balloon; what is left at the end)
    on_string   the small tangle on its string; float_at where it bobs; wane the cloud worn down to it
    gloom_dust  the pale dust that falls from it

How it is drawn. A large form is a Band: the stuff between an upper and a lower curve. The scribble
itself lies on an endless sheet anchored to the band (Band.ax): layers of RUNS, each one stroke of the
hand (a chain of flat loops with the lean of that hand, a hard zigzag, a tall fold, a loose end), each
with its own pressure (width, grain) that sets in, wavers and thins out. A run sits at a place along
the sheet and at a share of the band's depth, so the same strokes follow whatever shape the band
takes: sag a belly onto a head, spread into a lid, hang to the ground, part round two hands.
Dense strokes and rubbed dark make the core; single pale-edged loops, hanging arcs and loose ends
make the rim; pale dust is rubbed round it so that black reads on dark paper.
It churns by the hand moving on: every run is scribbled afresh once in a long while (its
predecessor fades under it, over more than six frames); at any moment only one or two are being
drawn, pale, with the chalk tip leading. All of that runs on the boil clock (F.tb), so the scribble
stands completely still in the two silences. Nothing is re-rolled: every number comes from a hash
of (seed, layer, place, generation). The generation is counted on that clock times the churn speed,
so every form must be called with the same seed, anchor, hand and churn (CHURN, the default) to be
the same strokes: what differs between forms (how pale the rim, how wide the line) travels in the
Band and is interpolated when one becomes the other.
"""
from __future__ import annotations

import math
import struct

import numpy as np
import skia

from .. import story as ST
from .core import (A, BOIL, C, H, TAB, W, Cam, Frame, boil_clock, chalk, disc, ease, ease_out, htab, ramp, rnd, rsym, seg, smooth,
                   smudge, specks, spline, vn)

__all__ = ["Band", "Tip", "Unravelled", "UNRAVEL_LINE", "band_cloud", "band_ceiling", "band_shawl", "mix_band", "mass",
           "gloom", "ceiling", "lid_for", "spread_band", "morph_band", "CHURN", "curtains", "curtain_gap", "peel", "STRAND_W", "shawl", "strand", "strand_pts", "cross_out", "unravel", "unravel_pts",
           "tangle", "tangle_pts", "on_string", "float_at", "wane", "wind_up", "remnant", "REMNANT_R", "gloom_dust", "scribble_pts",
           "handoff_gloom", "HANDOFF_GLOOM", "PART_HANG", "PART_STRANDS", "PART_GAP", "THIN_PLACE", "STRING"]

# =============================================================================================
# 1. fast paths: numpy arrays straight into skia (the scribble is thousands of points a frame)
# =============================================================================================
_HDR = struct.Struct("<4i")


def _mkpath(pts, verbs) -> skia.Path:
    """A skia path from float points (N, 2) and verb bytes (0 move, 1 line, 2 quad, 5 close), through
    skia's own serialised form: about fifty times faster than moveTo/lineTo from Python."""
    p = skia.Path()
    n = len(verbs)
    p.readFromMemory(_HDR.pack(5, len(pts), 0, n) + np.ascontiguousarray(pts, dtype="<f4").tobytes()
                     + verbs.tobytes() + b"\0" * (-n % 4))
    return p


def _mkpath_slow(pts, verbs) -> skia.Path:
    p, it, i = skia.Path(), np.asarray(pts, dtype=np.float64).tolist(), 0
    for v in verbs.tolist():
        if v == 0:
            p.moveTo(*it[i]); i += 1
        elif v == 1:
            p.lineTo(*it[i]); i += 1
        elif v == 2:
            p.quadTo(*it[i], *it[i + 1]); i += 2
        else:
            p.close()
    return p


def _selftest() -> bool:
    try:
        pts = np.array([[1.5, 2.5], [3.5, 4.5], [5.0, 6.0], [7.0, 8.0]])
        verbs = np.array([0, 1, 2, 5], np.uint8)
        return _mkpath(pts, verbs) == _mkpath_slow(pts, verbs)
    except Exception:
        return False


if not _selftest():            # another skia build: fall back to the slow, safe way
    _mkpath = _mkpath_slow

_RV: dict = {}


def _ribbon_verbs(m: int, r: int):
    v = _RV.get(m)
    if v is None:
        side = [1] + [2] * (m - 2) + [1]
        v = _RV[m] = np.array([0] + side + [1, 1] + side + [1, 5], np.uint8)
    return np.tile(v, r)


def _ribbons(S, wd) -> skia.Path:
    """One path of R closed ribbons. S: (R, M, 2) SCREEN points of R strokes, wd: (R, M) full widths
    in px. Each side is a chain of quadratic curves through the mid-points, so that a loop sampled
    at ten points is round; the ends are pointed (the width profile brings them there)."""
    r, m = S.shape[:2]
    d = np.gradient(S, axis=1)
    ln = np.hypot(d[..., 0], d[..., 1]) + 1e-9
    tx, ty = d[..., 0] / ln, d[..., 1] / ln
    hw = 0.5 * wd
    off = np.stack([-ty * hw, tx * hw], axis=-1)
    Lf, Rt = S + off, (S - off)[:, ::-1]
    out = np.empty((r, 4 * m, 2))
    for o, P in ((0, Lf), (2 * m, Rt)):
        mid = 0.5 * (P[:, :-1] + P[:, 1:])
        out[:, o] = P[:, 0]
        out[:, o + 1] = mid[:, 0]
        out[:, o + 2:o + 2 * m - 2:2] = P[:, 1:m - 1]
        out[:, o + 3:o + 2 * m - 2:2] = mid[:, 1:]
        out[:, o + 2 * m - 2] = P[:, m - 1]
    tip = np.stack([tx[:, -1] * hw[:, -1], ty[:, -1] * hw[:, -1]], axis=-1)
    tail = np.stack([tx[:, 0] * hw[:, 0], ty[:, 0] * hw[:, 0]], axis=-1)
    out[:, 2 * m - 1] = S[:, -1] + tip
    out[:, 4 * m - 1] = S[:, 0] - tail
    return _mkpath(out.reshape(-1, 2), _ribbon_verbs(m, r))


_GRID: dict = {}


def _grid_idx(rows: int, n: int):
    key = (rows, n)
    if key not in _GRID:
        idx = []
        for r in range(rows - 1):
            for i in range(n - 1):
                a0, b0 = r * n + i, (r + 1) * n + i
                idx += [a0, b0, a0 + 1, a0 + 1, b0, b0 + 1]
        _GRID[key] = idx
    return _GRID[key]


# =============================================================================================
# 2. the band: every large form of the scribble is the stuff between an upper and a lower curve
# =============================================================================================
class Band:
    """The shape of a mass of scribble: world x samples, its upper and lower edge there (world y),
    the anchor `ax` of its scribbling (the world x its loops are counted from: move it with the
    mass, or the loops swim through it) and the size of the hand `s` (1 = the cloud over the sofa:
    loops 100 to 350 world units wide, lines 4 to 12 wide). `dens` (0..1 per sample) thins it
    locally; `floor` is a world y nothing hangs below; `cut` a world x where its tone is parted;
    `reach` the world distance from the anchor that draw = 1 means for a wide mass.
    The look a form carries with it (factors on mass's arguments; a mix interpolates them, so a
    form turns into another without a step): `pale` the pale edges and fresh chalk, `core` the
    rubbed dark, `halo` the dust round it, `w` the line width. `rests` = [(x, y, r, k), ...]: world
    points the mass lies on: within r of x its loops are pressed flat against the height y (k 0..1:
    how firmly). `thin` (0..1 per sample): where it is worn thin: its dark strokes drop out one after
    another, the rubbed dark goes, and single pale loops are left with the paper between them."""
    __slots__ = ("x", "top", "bot", "ax", "s", "dens", "floor", "cut", "reach", "pale", "core", "halo", "w", "rests", "thin")

    def __init__(self, x, top, bot, ax, s=1.0, dens=None, floor=None, cut=None, reach=None, pale=1.0, core=1.0,
                 halo=1.0, w=1.0, rests=(), thin=None):
        self.x = np.asarray(x, dtype=np.float64)
        self.top = np.asarray(top, dtype=np.float64)
        self.bot = np.maximum(np.asarray(bot, dtype=np.float64), self.top)
        self.ax, self.s = float(ax), float(s)
        self.dens = None if dens is None else np.asarray(dens, dtype=np.float64)
        self.floor, self.cut, self.reach = floor, cut, reach
        self.pale, self.core, self.halo, self.w = float(pale), float(core), float(halo), float(w)
        self.rests = tuple(rests)
        self.thin = None if thin is None else np.asarray(thin, dtype=np.float64)

    @property
    def thick(self):
        return self.bot - self.top

    def under(self, x: float) -> float:
        """World y of the underside at world x."""
        return float(np.interp(x, self.x, self.bot))

    def over(self, x: float) -> float:
        """World y of the upper edge at world x."""
        return float(np.interp(x, self.x, self.top))

    def root(self, x: float, depth: float = 0.3):
        """A world point inside the mass above world x: where a strand from below ends (depth 0 = on
        the underside, 1 = on the upper edge)."""
        t, b = self.over(x), self.under(x)
        return (float(x), b - depth * (b - t))

    def moved(self, dx: float = 0.0, dy: float = 0.0) -> "Band":
        """The same mass somewhere else (its loops travel with it)."""
        return Band(self.x + dx, self.top + dy, self.bot + dy, self.ax + dx, self.s, self.dens,
                    None if self.floor is None else self.floor + dy, None if self.cut is None else self.cut + dx, self.reach,
                    self.pale, self.core, self.halo, self.w, [(x + dx, y + dy, r, k) for (x, y, r, k) in self.rests], self.thin)

    def _like(self, x, top, bot, **kw) -> "Band":
        d = dict(ax=self.ax, s=self.s, dens=self.dens, floor=self.floor, cut=self.cut, reach=self.reach, pale=self.pale,
                 core=self.core, halo=self.halo, w=self.w, rests=self.rests, thin=self.thin)
        d.update(kw)
        return Band(x, top, bot, **d)


def _look(a: Band, b: Band, k: float) -> dict:
    """Anchor, hand and look between two bands (k = the weight at the anchor)."""
    fl = b.floor if a.floor is None else a.floor if b.floor is None else a.floor + (b.floor - a.floor) * k
    rests = [(x, y, r, q * (1.0 - k)) for (x, y, r, q) in a.rests] + [(x, y, r, q * k) for (x, y, r, q) in b.rests]
    return dict(ax=a.ax + (b.ax - a.ax) * k, s=a.s * (b.s / a.s) ** k, floor=fl, cut=b.cut if k > 0.5 else a.cut,
                reach=b.reach if k > 0.5 else a.reach, pale=a.pale + (b.pale - a.pale) * k, core=a.core + (b.core - a.core) * k,
                halo=a.halo + (b.halo - a.halo) * k, w=a.w + (b.w - a.w) * k, rests=rests)


def mix_band(a: Band, b: Band, w, n: int = 0) -> Band:
    """The band between a and b at the same places: w = 0 gives a, 1 gives b. w may be an array over
    the n samples of the result (np.linspace from the leftmost to the rightmost x of both) for a
    change that runs along the mass. Where one of the two does not reach, it counts as a seam of no
    thickness at the level of its own middle. Anchor, hand and look are interpolated by the weight
    AT THE ANCHOR (the hand geometrically): give both bands the same anchor if the loops are to
    stay where they are. For a cloud that opens into a lid use spread_band, for a mass that draws
    in to another shape (the cloud settling as a shawl) morph_band."""
    xl, xr = min(a.x[0], b.x[0]), max(a.x[-1], b.x[-1])
    n = n or max(len(a.x), len(b.x))
    x = np.linspace(xl, xr, n)

    def ext(q: Band):
        mid = 0.5 * (q.top + q.bot)
        inside = (x >= q.x[0]) & (x <= q.x[-1])
        tp = np.where(inside, np.interp(x, q.x, q.top), np.interp(x, q.x, mid))
        bt = np.where(inside, np.interp(x, q.x, q.bot), np.interp(x, q.x, mid))
        dn = np.ones(n) if q.dens is None else np.interp(x, q.x, q.dens)
        tn = np.zeros(n) if q.thin is None else np.interp(x, q.x, q.thin, left=0.0, right=0.0)
        return tp, bt, dn, tn

    ta, ba, da, na = ext(a)
    tb, bb, db, nb = ext(b)
    w = np.clip(np.asarray(w, dtype=np.float64), 0.0, 1.0)
    k = float(w) if w.ndim == 0 else float(np.interp(a.ax, x, w))
    dens = None if a.dens is None and b.dens is None else da + (db - da) * w
    thin = None if a.thin is None and b.thin is None else na + (nb - na) * w
    return Band(x, ta + (tb - ta) * w, ba + (bb - ba) * w, dens=dens, thin=thin, **_look(a, b, k))


def spread_band(cloud: Band, lid: Band, w: float, front: float | None = None) -> Band:
    """A cloud opening out into a lid (w 0 -> 1), or a lid gathering into a cloud (w 1 -> 0).
    Where the cloud hangs it lifts and deepens into the lid; to either side the lid comes down
    out of its own upper edge (which is above the frame), further and further from the anchor: a
    blunt front that runs outward. w = 0 is exactly the cloud, w = 1 exactly the lid.
    front: how far from the anchor (world units) the lid has come at this moment; default: it runs
    with w and has passed the ends of `lid` at w = 1. The anchor is the cloud's: give the lid the
    same one (the child's place when it spread)."""
    w = min(1.0, max(0.0, float(w)))
    if w <= 0.0:
        return cloud
    c0, c1 = float(cloud.x[0]), float(cloud.x[-1])
    d_end = max(abs(lid.x[0] - cloud.ax), abs(lid.x[-1] - cloud.ax))
    fw = 460.0 * lid.s
    f = 1.04 * w * (d_end + fw) if front is None else float(front)
    if w >= 1.0 and f >= d_end + fw:
        return lid
    e0, e1 = max(float(lid.x[0]), min(c0, cloud.ax - f)), min(float(lid.x[-1]), max(c1, cloud.ax + f))
    x = np.unique(np.concatenate([lid.x[(lid.x > e0) & (lid.x < e1)], cloud.x[(cloud.x > e0) & (cloud.x < e1)], [e0, e1]]))
    lt, lb = np.interp(x, lid.x, lid.top), np.interp(x, lid.x, lid.bot)
    ct, cb = np.interp(x, cloud.x, cloud.top), np.interp(x, cloud.x, cloud.bot)
    out = np.maximum(np.maximum(c0 - x, x - c1), 0.0)             # beyond its ends the cloud is a web drawn up into the lid
    half = 0.5 * (c1 - c0)
    mid = 0.5 * (ct + cb)
    th = 0.5 * (cb - ct) * (1.0 - smooth(out / (0.22 * half + 1e-6)))
    mid = mid + (lt - mid) * smooth(out / (0.9 * half + 1e-6))
    ct, cb = mid - th, mid + th
    u = np.clip((f - np.abs(x - cloud.ax)) / fw, 0.0, 1.0)
    m = ease(seg(w, 0.0, 0.62)) * (1.0 - (1.0 - u) ** 2.4)
    k = float(np.interp(cloud.ax, x, m))
    dens = (1.0 if cloud.dens is None else np.interp(x, cloud.x, cloud.dens)) * (1.0 - m) + \
        (1.0 if lid.dens is None else np.interp(x, lid.x, lid.dens)) * m
    # beside the cloud the lid is only pressed lightly while it is still shallow: no thin dark sheets (horns) at its ends
    dens = dens * (1.0 - (1.0 - smooth((m - 0.06) / 0.5)) * smooth(out / (0.06 * half + 1e-6)))
    thin = None
    if cloud.thin is not None or lid.thin is not None:
        thin = (0.0 if cloud.thin is None else np.interp(x, cloud.x, cloud.thin, left=0.0, right=0.0)) * (1.0 - m) + \
            (0.0 if lid.thin is None else np.interp(x, lid.x, lid.thin)) * m
    return Band(x, ct + (lt - ct) * m, cb + (lb - cb) * m, dens=dens, thin=thin, **_look(cloud, lid, k))


def morph_band(a: Band, b: Band, w: float, pin=None, n: int = 0) -> Band:
    """The band on its way from a to b when the mass DRAWS IN (or opens out) to the other shape:
    every part of a travels to the matching part of b (left end to left end, right end to right
    end), so a wide cloud gathers into a narrow heap instead of thinning to a seam. pin = (xa, xb):
    the world x of a that ends up at the world x of b (the middle of the cloud over the head ends
    on the nape). Anchor, hand and look are interpolated."""
    w = min(1.0, max(0.0, float(w)))
    if w <= 0.0 or w >= 1.0:
        return a if w <= 0.0 else b
    n = n or max(len(a.x), len(b.x))
    q = np.linspace(0.0, 1.0, n)

    def par(B: Band, px):
        u = (B.x - B.x[0]) / max(1e-9, B.x[-1] - B.x[0])
        if px is not None:                                     # the pinned place sits at q = 0.5
            up = min(0.95, max(0.05, (px - B.x[0]) / max(1e-9, B.x[-1] - B.x[0])))
            u = np.where(u <= up, 0.5 * u / up, 0.5 + 0.5 * (u - up) / (1.0 - up))
        dn = np.ones(n) if B.dens is None else np.interp(q, u, B.dens)
        tn = np.zeros(n) if B.thin is None else np.interp(q, u, B.thin)
        return np.interp(q, u, B.x), np.interp(q, u, B.top), np.interp(q, u, B.bot), dn, tn

    xa, ta, ba, da, na = par(a, None if pin is None else pin[0])
    xb, tb, bb, db, nb = par(b, None if pin is None else pin[1])
    dens = None if a.dens is None and b.dens is None else da + (db - da) * w
    thin = None if a.thin is None and b.thin is None else na + (nb - na) * w
    return Band(xa + (xb - xa) * w, ta + (tb - ta) * w, ba + (bb - ba) * w, dens=dens, thin=thin, **_look(a, b, w))


# =============================================================================================
# 3. the scribble itself: layers of runs of the hand, laid out on an endless sheet
# =============================================================================================
# A layer is a kind of stroke; its runs sit in cells along the sheet's X (sheet units = world units
# / hand size, counted from the band's anchor). A run is ONE stroke of the hand: a chain of flat
# loops that travels a little, or a hard zigzag. Across the band it sits at v (0 = upper edge, 1 =
# lower edge) plus E sheet units of its own, so the same run follows any shape the band takes.
#   cw cell width, k runs a cell, M points a run, n loops, RX loop half width (sheet units), RV loop
#   half height (share of the band's thickness), TX how far it travels, DV drift across the band,
#   EH / ER a hang and a half height in sheet units (not stretched by the band), vc where across the
#   band, w line width (sheet units), T seconds until a slot is scribbled afresh, slant the lean of
#   the hand, tilt the rise of the loops' long axis, drape: +1 only in a hanging curtain, -1 less there
_LAYERS = (
    dict(name="body", cw=120.0, k=2, M=44, zig=0, n=(2.6, 4.4), RX=(90, 175), RV=(0.06, 0.14), TX=(60, 260), DV=0.10,
         EH=(0, 0), ER=(0, 0), vc=(0.40, 0.62), w=11.0, col="dark", a=1.0, grain="dense", edge=0.0, T=60.0, slant=0.2,
         tilt=0.10, wander=0.14, drape=-1),
    dict(name="mid", cw=130.0, k=2, M=40, zig=0, n=(2.0, 3.4), RX=(60, 125), RV=(0.13, 0.24), TX=(60, 240), DV=0.2,
         EH=(0, 0), ER=(0, 0), vc=(0.2, 0.8), w=7.4, col="dark", a=0.95, grain="mid", edge=0.0, T=50.0, slant=0.3,
         tilt=0.16, drape=-1),
    dict(name="grey", cw=180.0, k=1, M=40, zig=0, n=(2.2, 3.6), RX=(80, 150), RV=(0.12, 0.22), TX=(80, 280), DV=0.16,
         EH=(0, 0), ER=(0, 0), vc=(0.3, 0.7), w=5.6, col="mid", a=0.95, grain="dense", edge=0.0, T=50.0, slant=0.3,
         tilt=0.16, drape=-1),
    dict(name="zig", cw=250.0, k=1, M=40, zig=1, n=(3.5, 6.0), RX=(0, 0), RV=(0.20, 0.36), TX=(90, 170), DV=0.10,
         EH=(0, 0), ER=(0, 0), vc=(0.40, 0.64), w=7.0, col="dark", a=0.96, grain="dense", edge=0.0, T=70.0, slant=0.70,
         tilt=0.0, drape=0),
    dict(name="fold", cw=104.0, k=1, M=44, zig=0, n=(2.2, 4.0), RX=(18, 46), RV=(0.26, 0.41), TX=(30, 150), DV=0.12,
         EH=(0, 0), ER=(0, 0), vc=(0.46, 0.60), w=9.5, col="dark", a=1.0, grain="dense", edge=0.0, T=60.0, slant=0.04,
         tilt=0.0, drape=1),
    dict(name="stroke", cw=160.0, k=1, M=40, zig=1, n=(3.0, 5.5), RX=(0, 0), RV=(0.36, 0.47), TX=(50, 150), DV=0.04,
         EH=(0, 0), ER=(0, 0), vc=(0.46, 0.54), w=7.5, col="dark", a=0.96, grain="mid", edge=0.0, T=70.0, slant=0.06,
         tilt=0.0, drape=1),
    dict(name="veil", cw=250.0, k=1, M=36, zig=0, n=(1.6, 2.8), RX=(22, 54), RV=(0.24, 0.42), TX=(30, 120), DV=0.1,
         EH=(0, 0), ER=(0, 0), vc=(0.40, 0.60), w=3.0, col="edge", a=0.5, grain="mid", edge=0.0, T=30.0, slant=0.04,
         tilt=0.0, drape=1),
    dict(name="rim", cw=100.0, k=1, M=30, zig=0, n=(1.05, 1.9), RX=(55, 130), RV=(0.10, 0.24), TX=(20, 150), DV=0.10,
         EH=(0, 0), ER=(10, 30), vc="rim", w=5.6, col="dark", a=0.96, grain="dense", edge=1.0, T=26.0, slant=0.3,
         tilt=0.2, drape=0),
    dict(name="sag", cw=290.0, k=1, M=20, zig=0, n=(0.5, 0.75), RX=(90, 170), RV=(0.03, 0.08), TX=(0, 40), DV=0.0,
         EH=(0, 0), ER=(12, 30), vc=(0.86, 0.98), w=5.8, col="dark", a=0.96, grain="dense", edge=1.0, T=44.0, slant=0.0,
         tilt=0.0, drape=0),
    dict(name="tail", cw=190.0, k=1, M=22, zig=0, n=(0.8, 1.5), RX=(9, 22), RV=(0.0, 0.0), TX=(-36, 36), DV=0.0,
         EH=(60, 150), ER=(5, 12), vc=(0.74, 0.92), w=4.2, col="dark", a=0.94, grain="dense", edge=1.0, T=36.0, slant=0.0,
         tilt=0.0, drape=0),
    dict(name="pale", cw=260.0, k=1, M=34, zig=0, n=(1.4, 2.4), RX=(90, 160), RV=(0.15, 0.27), TX=(60, 220), DV=0.2,
         EH=(0, 0), ER=(0, 0), vc=(0.2, 0.7), w=2.6, col="edge", a=0.6, grain="mid", edge=0.0, T=20.0, slant=0.3,
         tilt=0.16, drape=-1),
    # only where a band is worn thin (Band.thin): the single loops that are left, one layer deep
    dict(name="single", cw=128.0, k=1, M=34, zig=0, n=(1.15, 2.1), RX=(62, 128), RV=(0.13, 0.25), TX=(30, 170), DV=0.16,
         EH=(0, 0), ER=(0, 0), vc=(0.26, 0.84), w=5.0, col="dark", a=0.96, grain="dense", edge=1.0, T=34.0, slant=0.3,
         tilt=0.2, drape=0, only="thin"),
)
_T0 = 300.0          # the thickness (sheet units) the cloud's layers are made for
_HANG = 1.9          # from this many cloud thicknesses on a mass hangs (a curtain, a belly let down): tall loops take over
CHURN = 0.9          # the scribbling hand's speed, the same in every form: a form called with another value is OTHER strokes
_D_ON, _D_OFF, _D_FRESH = 0.8, 0.6, 3.2     # seconds: a run draws on / its predecessor fades / it stays pale
_HM = (7919, 104729, 1543, 15485863, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
       127, 131, 137, 139, 149, 151)


def _h(key, j: int):
    return TAB[(key * _HM[4 + j] + 977 * j + 13) & 8191]


def _lerp(lo_hi, h):
    return lo_hi[0] + (lo_hi[1] - lo_hi[0]) * h


def _cols(day: bool):
    if day:        # soft dark pencil-grey: the same thing on warm paper
        return dict(dark=(0.21, 0.20, 0.25), mid=(0.32, 0.31, 0.37), edge=(0.50, 0.48, 0.54), fresh=(0.12, 0.12, 0.16),
                    halo=(0.42, 0.38, 0.44), tip=(0.10, 0.10, 0.14), thin=(0.58, 0.56, 0.62), lit=(0.62, 0.60, 0.64))
    return dict(dark=C.GLOOM, mid=C.GLOOM_MID, edge=C.GLOOM_EDGE, fresh=(0.60, 0.65, 0.80), halo=(0.20, 0.24, 0.38),
                tip=(0.85, 0.88, 0.95), thin=(0.40, 0.45, 0.62), lit=(0.56, 0.63, 0.82))


def _layer(F: Frame, L: dict, li: int, band: Band, seed: int, tq: float, churn: float, a: float, wk: float, cols: dict,
           draw, seq: bool, edge: float, lod: float, warp, avoid, day: bool, thmax: float, nrun: float, kept: float):
    """Draw one layer of the sheet inside the band. Returns the newest chalk tip (x, y, age) or None."""
    cam = F.cam
    z, s = cam.zoom, band.s
    vl, vt, vr, vb = cam.view(60.0)
    cw = L["cw"]
    reach = L["RX"][1] + 0.5 * max(abs(L["TX"][0]), abs(L["TX"][1])) + 30.0
    xa, xb = band.x[0], band.x[-1]
    if not seq and warp is None:
        xa, xb = max(xa, vl - reach * s), min(xb, vr + reach * s)
    if xb <= xa:
        return None
    c0, c1 = math.floor((xa - band.ax) / s / cw) - 1, math.floor((xb - band.ax) / s / cw) + 1
    k = L["k"]
    tiers = 2 if thmax > 0.95 and L["name"] in ("body", "mid") else 1       # a deeper mass holds more strokes
    kt = k * tiers
    cc = np.repeat(np.arange(c0, c1 + 1, dtype=np.int64), kt)
    jj = np.tile(np.arange(kt, dtype=np.int64), c1 - c0 + 1)
    slot = (cc * 8 + jj) * _HM[0] + li * _HM[1] + int(seed) * _HM[2]
    # churn: each slot is scribbled afresh every T seconds; its predecessor fades under it
    T = L["T"]
    if churn > 0.0:
        age = tq * churn / T + _h(slot, 0)
        g = np.floor(age).astype(np.int64)
        sec = (age - g) * T / churn                        # seconds since this generation began
    else:
        g, sec = np.zeros(len(slot), np.int64), np.full(len(slot), 99.0)
    old = sec < _D_OFF
    no = int(old.sum())
    key = np.concatenate([slot + g * _HM[3], (slot + (g - 1) * _HM[3])[old]])
    cc = np.concatenate([cc, cc[old]])
    jj = np.concatenate([jj, jj[old]])
    f1 = np.concatenate([np.clip(sec / _D_ON, 0.0, 1.0), np.ones(no)])
    al = np.concatenate([np.ones(len(slot)), 1.0 - sec[old] / _D_OFF])
    fresh = np.concatenate([1.0 - np.clip((sec - _D_ON) / _D_FRESH, 0.0, 1.0), np.zeros(no)])
    born = np.concatenate([sec, np.full(no, 99.0)])
    # the run's own numbers
    Xc = (cc + ((jj % k) + 0.15 + 0.7 * _h(key, 1)) / k) * cw
    xw = band.ax + s * Xc
    th = np.interp(xw, band.x, band.thick, left=0.0, right=0.0) / (s * _T0)       # the band's thickness there, in cloud thicknesses
    vc = L["vc"]
    if vc == "rim":
        hv = _h(key, 2)
        vcen = np.where(hv < 0.36, 0.02 + 0.14 * hv / 0.36, 0.80 + 0.22 * (hv - 0.36) / 0.64)
        vcen = np.where(vcen > 0.5, 1.0 - (1.0 - vcen) / np.maximum(1.0, th), vcen / np.maximum(1.0, th))
    else:
        vcen = _lerp(vc, _h(key, 2)) + L.get("wander", 0.0) * (2.0 * vn(Xc / 330.0 + seed * 7.3, seed + 3) - 1.0)
        if L["name"] in ("sag", "tail"):
            vcen = 1.0 - (1.0 - vcen) / np.maximum(1.0, th)
    nl = _lerp(L["n"], _h(key, 3))
    RX = _lerp(L["RX"], _h(key, 4))
    RV = _lerp(L["RV"], _h(key, 5))
    TX = _lerp(L["TX"], _h(key, 6)) * np.where(_h(key, 7) < 0.5, -1.0, 1.0)
    DV = L["DV"] * (2.0 * _h(key, 8) - 1.0)
    EH = _lerp(L["EH"], _h(key, 9))
    ER = _lerp(L["ER"], _h(key, 10))
    ph = 2.0 * math.pi * _h(key, 11) if L["name"] != "sag" else 0.25 * (_h(key, 11) - 0.5)
    wr = 0.72 + 0.5 * _h(key, 12)                         # the pressure of this run
    f0 = np.zeros(len(key))
    wipe = np.zeros(len(key), bool)
    # where the band is thin a run is only begun; where it is thinned (dens) it is pressed lightly
    pres = np.clip((th - 0.06) / 0.22, 0.0, 1.0)
    pres = pres * pres * (3.0 - 2.0 * pres)
    if tiers > 1:
        tier = jj // k
        pres = pres * np.where(tier > 0, np.clip((th - 0.95) / 0.6, 0.0, 1.0) * np.clip((2.3 - th) / 0.6, 0.0, 1.0), 1.0)
        vcen = np.where(tier > 0, 0.16 + 0.68 * _h(key, 17), vcen)
    # a mass that hangs long (a curtain) is drawn with tall loops; the flat loops of the cloud thin out there
    dr = L["drape"]
    if dr:
        hang = np.clip((th - _HANG) / 0.5, 0.0, 1.0)
        pres = pres * (hang if dr > 0 else 1.0 - hang)
        if dr < 0:
            st = np.maximum(1.0, th / 1.3)
            RX, RV = RX / st ** 0.6, np.minimum(0.44, RV * st ** 0.35)
    elif L["zig"]:
        RV = RV / np.maximum(1.0, th / 1.4) ** 0.7
    else:                                                  # rim strokes keep their own size however long the band hangs
        RV = RV / np.maximum(1.0, th)
    if L["name"] in ("body", "mid", "grey", "zig"):        # the core does not pile up against the ends of a mass
        pres = pres * (0.2 + 0.8 * smooth(np.minimum(xw - band.x[0], band.x[-1] - xw) / (170.0 * s)))
    f1 = f1 * (0.25 + 0.75 * pres) if dr <= 0 else f1 * pres
    al = al * np.minimum(1.0, pres * 3.0)
    # a run whose middle lies at the very end of the mass is not there: nothing pops when a band grows or its hand changes
    al = al * np.clip(np.minimum(xw - band.x[0], band.x[-1] - xw) / (46.0 * s), 0.0, 1.0)
    lodk = min(1.0, max(0.12, s * z / 0.62)) ** 1.15        # far away: fewer strokes (the tone stands in for them)
    if lodk < 1.0:
        al = al * np.clip((lodk * 1.2 - _h(key, 19)) / 0.2, 0.0, 1.0)
    if band.dens is not None:
        al = al * np.interp(xw, band.x, band.dens) ** (1.0 if L["name"] in ("rim", "tail", "sag", "veil") else 2.4)
    # a thin place: the dark strokes of the core drop out one after another (cut short on their way), about half of
    # the rim's loops stay, and the single loops under them come to light
    tau = None
    if band.thin is not None:
        tau = np.interp(xw, band.x, band.thin, left=0.0, right=0.0)
        hq = _h(key, 20)
        nm = L["name"]
        if nm == "single":
            al = al * smooth((tau - 0.20) / 0.30)
        elif nm in ("rim", "sag", "tail"):
            f1 = f1 * np.clip((1.25 - 0.60 * tau - hq) / 0.25, 0.0, 1.0)
        elif nm not in ("pale", "veil"):
            f1 = f1 * np.clip((1.22 - 1.60 * tau - hq) / 0.22, 0.0, 1.0)
    # keep: how much of it is left (strokes drop out all over it, cut short on their way: loose ends, no tips)
    if np.ndim(kept) > 0:                                  # (an array over the band's samples: each part its own share)
        f1 = f1 * np.clip((np.interp(xw, band.x, kept) * 1.05 - _h(key, 13)) / 0.05, 0.0, 1.0)
    elif kept < 1.0:
        f1 = f1 * np.clip((kept * 1.05 - _h(key, 13)) / 0.05, 0.0, 1.0)
    # draw: the order the mass was scribbled in
    d0, d1 = (0.0, float(draw)) if not isinstance(draw, tuple) else draw
    if d0 > 0.0 or d1 < 1.0:
        hr = _h(key, 13)
        if seq:        # one hand: a knot in the middle first, then a sweep to the left, then one to the right
            xn = np.clip((xw - band.x[0]) / max(1e-6, band.x[-1] - band.x[0]), 0.0, 1.0)
            first = (hr < 0.30) & (np.abs(2.0 * xn - 1.0) < 0.5)
            rank = np.where(first, 0.22 * (xn - 0.25) / 0.5, np.where(hr < 0.65, 0.25 + 0.34 * (1.0 - xn), 0.625 + 0.34 * xn))
            rank = rank + 0.035 * _h(key, 18)
            dl = 1.0 / max(8.0, nrun)                       # one stroke at a time
        else:          # a wide mass: scribbled from its anchor outward, both ways, the front ragged
            rch = band.reach if band.reach is not None else 0.5 * (band.x[-1] - band.x[0])
            rank = 0.86 * np.clip(np.abs(xw - band.ax) / max(1.0, rch), 0.0, 1.0) + 0.14 * _h(key, 18)
            dl = 0.04
        lo, hi = np.clip((d0 * (1.0 + dl) - rank) / dl, 0.0, 1.0), np.clip((d1 * (1.0 + dl) - rank) / dl, 0.0, 1.0)
        f0, f1 = np.maximum(f0, lo * f1), f1 * hi
        tipd = (hi > 0.0) & (hi < 1.0)                     # the strokes being made carry the tip and are pale
        if d1 < 1.0:
            born = np.where(tipd, 0.0, 99.0)
            last = np.clip(1.0 - (d1 * (1.0 + dl) - rank - dl) / (2.5 * dl), 0.0, 1.0) * (hi >= 1.0)
            fresh = np.where(tipd, 1.0, np.maximum(0.8 * last, fresh * min(1.0, max(0.0, (d1 - 0.9) / 0.1))))
        wipe = (lo > 0.0) & (lo < 1.0)
    keep = (f1 - f0 > 0.03) & (al > 0.04)
    if not keep.any():
        return None
    sel = np.nonzero(keep)[0]
    (key, Xc, xw, th, vcen, nl, RX, RV, TX, DV, EH, ER, ph, wr, f0, f1, al, fresh, born, wipe) = (
        v[sel] for v in (key, Xc, xw, th, vcen, nl, RX, RV, TX, DV, EH, ER, ph, wr, f0, f1, al, fresh, born, wipe))
    if tau is not None:
        tau = tau[sel]
    # geometry: (R, M) parameter along each run
    M = L["M"]
    uu = f0[:, None] + (f1 - f0)[:, None] * np.linspace(0.0, 1.0, M)[None, :]
    spin = np.where((_h(key, 14) < 0.3) & (L["name"] != "sag"), -1.0, 1.0)[:, None]
    th_ = 2.0 * math.pi * nl[:, None] * uu * spin + ph[:, None]
    osz = (_h(key, 15) * 97.0)[:, None]
    m = 1.0 + 0.16 * (2.0 * vn(uu * nl[:, None] * 0.7 + osz, 7) - 1.0)
    if L["zig"]:
        wave = np.arcsin(0.97 * np.sin(th_)) * (2.0 / math.pi)
        cx_ = np.zeros_like(th_)
    else:
        wave = np.sin(th_)
        cx_ = np.cos(th_)
    X = Xc[:, None] + TX[:, None] * (uu - 0.5) + RX[:, None] * m * cx_
    vline = vcen[:, None] + DV[:, None] * (uu - 0.5)
    x0 = band.ax + s * X
    pad = 70.0 * s                                         # nothing is scribbled past the ends of the band: it piles up there
    ov = x0 - (band.x[-1] - pad)
    x0 = np.where(ov > 0.0, band.x[-1] - pad + pad * np.tanh(ov / pad), x0)
    ov = (band.x[0] + pad) - x0
    x0 = np.where(ov > 0.0, band.x[0] + pad - pad * np.tanh(ov / pad), x0)
    flat = x0.ravel()
    tk = np.interp(flat, band.x, band.thick).reshape(x0.shape)
    x0 = xw[:, None] + (x0 - xw[:, None]) * (0.2 + 0.8 * np.clip(tk / (th[:, None] * (s * _T0) * 0.7 + 1e-6), 0.0, 1.0))
    flat = x0.ravel()
    tp = np.interp(flat, band.x, band.top).reshape(x0.shape)
    bt = np.interp(flat, band.x, band.bot).reshape(x0.shape)
    thick = bt - tp
    yc = tp + vline * thick + s * EH[:, None] * uu
    dy = RV[:, None] * m * wave * thick + s * ER[:, None] * m * wave
    tilt = L["tilt"] * (2.4 * _h(key, 16) - 0.9)[:, None]
    y = yc + dy - tilt * s * RX[:, None] * m * cx_
    x = x0 - L["slant"] * dy
    if L["name"] == "tail":
        x = x + s * 16.0 * (2.0 * vn(uu * 2.2 + osz, 9) - 1.0) * uu
    wseg = None
    if warp is not None:
        if hasattr(warp, "runs"):                          # a mass that comes apart: every stroke in pieces (see _Shatter)
            x, y, wseg = warp.runs(x, y, xw, key)
        else:
            x, y = warp(x, y, xw[:, None])
    if band.floor is not None:                             # nothing hangs through the floor: it settles on it, rounded
        mfl = 26.0 * s
        over = y - (band.floor - mfl)
        y = np.where(over > 0.0, band.floor - 3.0 * s - (mfl - 3.0 * s) * np.exp(-over / mfl), y)
    for (px, py, prad, pk) in band.rests:                  # what it lies on: there the loops are pressed flat, not hung through
        if pk > 0.0:
            wx = np.clip(1.3 - np.abs(x - px) / prad, 0.0, 1.0)
            over = np.maximum(y - py, 0.0)
            cm = 15.0 * s
            y = y - pk * wx * wx * (3.0 - 2.0 * wx) * (over - cm * np.tanh(over / cm))
    for (ox, oy, orad) in avoid:                           # a head it lies round: the loops are pushed off it
        ddx, ddy = x - ox, y - oy
        dd = np.hypot(ddx, ddy) + 1e-6
        push = 0.7 * np.maximum(0.0, orad * 1.16 - dd) / dd
        x, y = x + ddx * push, y + ddy * push
    S = np.stack([(x - cam.cx) * z + W / 2.0, (y - cam.cy) * z + H / 2.0], axis=-1)
    vis = (S[..., 0].max(1) > -40) & (S[..., 0].min(1) < W + 40) & (S[..., 1].max(1) > -40) & (S[..., 1].min(1) < H + 40)
    if not vis.any():
        return None
    # pressure along the stroke: it sets in, wavers, and thins out into a loose end
    pr = (0.66 + 0.34 * smooth(uu / 0.04)) * (0.40 + 0.60 * smooth((f1[:, None] - uu) / 0.10))
    pr = pr * (0.84 + 0.30 * vn(uu * nl[:, None] * 2.3 + osz * 1.7, 11))
    wpx = L["w"] * wk * s * z
    fl = 1.25
    a_l = L["a"] * a * lod
    if wpx < fl:
        a_l, wpx = a_l * wpx / fl, fl
    wd = wpx * wr[:, None] * pr
    if wseg is not None:
        wd = wd * wseg
        vis = vis & (wseg.max(axis=1) > 0.02)              # (a shard that has been rubbed away is not drawn at all)
        if not vis.any():
            return None
    col = cols[L["col"]]
    c = F.c
    tip = None
    e = L["edge"] * edge
    # buckets: the pressure of a run decides its grain; fading runs go through four steps of alpha
    hard = wr > 0.94
    lev = np.ceil(np.clip(al, 0.0, 1.0) * 4.0 - 1e-6) / 4.0
    soft = "mid" if L["grain"] == "dense" else L["grain"]
    # a thin place: a line that runs into it loses its black on the way and goes on as a pale line, pressed lightly
    wp = tq_ = None
    if tau is not None:
        taup = np.interp(x.ravel(), band.x, band.thin, left=0.0, right=0.0).reshape(x.shape)
        if L["col"] == "edge":
            wd = wd * (1.0 + 0.5 * taup)
        else:
            tq_ = taup.max(axis=1) > 0.04
            wp = wd * 0.60 * smooth(taup / 0.42)
            wd = wd * (1.0 - 0.84 * smooth(taup / 0.85))
    k_ = max(0.6, min(2.0, s * z))
    for gname, gm in ((L["grain"], hard), (soft, ~hard)):
        for lv in (1.0, 0.75, 0.5, 0.25):
            q = vis & gm & (lev == lv)
            if not q.any():
                continue
            P = _ribbons(S[q], wd[q])
            if e > 0.0 or tq_ is not None:
                c.save()
                c.translate(1.5 * k_ + 0.4, -1.3 * k_ - 0.4)
                if e > 0.0:
                    c.drawPath(P, F.paint(cols["edge"], (0.62 if not day else 0.4) * e * a_l * lv, "mid"))
                if tq_ is not None and (q & tq_).any():
                    c.drawPath(_ribbons(S[q & tq_], wp[q & tq_]), F.paint(cols["thin"], 0.9 * L["a"] * a * lv * min(1.0, lod * 1.5), "mid"))
                c.restore()
            c.drawPath(P, F.paint(col, a_l * lv, gname))
    # the newest runs are still pale chalk, and the one being drawn carries the tip
    if edge > 0.0 and L["col"] != "edge":
        fr = vis & (fresh > 0.02)
        for lo_, hi_, av in ((0.66, 1.01, 0.85), (0.33, 0.66, 0.5), (0.02, 0.33, 0.2)):
            q = fr & (fresh > lo_) & (fresh <= hi_)
            if q.any():
                c.drawPath(_ribbons(S[q], np.where(wd[q] > 0.0, np.maximum(1.2, wd[q] * 0.42), 0.0)),
                           F.paint(cols["fresh"], av * 0.7 * a_l * min(1.0, edge), "mid"))
    tips = vis & (born < _D_ON) & (f1 < 0.999) & (al >= 1.0)
    if tips.any():
        i = int(np.argmin(np.where(tips, born, 99.0)))
        for j in np.nonzero(tips)[0].tolist():
            c.drawCircle(float(S[j, -1, 0]), float(S[j, -1, 1]), max(1.3, (4.4 if seq and d1 < 1.0 else 2.4) * s * z * wk),
                         F.paint(cols["tip"], 0.85 * a * min(1.0, max(0.0, edge * 1.6 - 0.6)), None))
        tip = (float(x[i, -1]), float(y[i, -1]), float(born[i]))
    for j in np.nonzero(vis & wipe)[0].tolist():           # what wipes it away leads too
        c.drawCircle(float(S[j, 0, 0]), float(S[j, 0, 1]), max(1.2, 2.4 * s * z * wk), F.paint(cols["tip"], 0.8 * a, None))
    return tip


def mass(F: Frame, band: Band, seed: int = 4, a: float = 1.0, draw=1.0, churn: float = CHURN, w: float = 1.0,
         halo: float = 1.0, edge: float = 1.0, core: float = 1.0, day: bool | None = None, t: float | None = None,
         seq: bool = False, warp=None, avoid=(), layers=None, keep: float = 1.0):
    """Draw the scribble that fills a Band (every large form is this call with another band).

    a: pressure 0..1 (a fade: at least 6 frames). draw: how much of it is scribbled yet, 0..1, or a
    pair (d0, d1): its strokes exist from d0 to d1 of the order they were made in; the strokes at
    either limit are cut short and carry the pale tip. seq=True: ONE hand makes it, stroke after
    stroke (a knot in the middle, a sweep left, a sweep right): for a mass that is wholly on screen
    (the birth). seq=False: it is scribbled from its anchor outward, both ways (band.reach world
    units at draw = 1; default half the band): a lid spreading. keep: 0..1, how much of it is left:
    strokes drop out all over it (unravelling, drifting off), without tips (it may be an array
    over the band's samples: each part of it its own share). churn: how fast the hand
    goes on scribbling (CHURN = 0.9: one or two new strokes a second in a cloud; 0 = none), on the
    clock t (default F.tb: it stands still in the two silences). It is a constant of the scribble:
    the same value in every form and never animated, or all strokes are re-rolled.
    w: line width factor. halo: the pale dust round it. edge: pale fresh chalk and pale edges.
    core: the rubbed dark under the strokes (these four multiply the band's own look).
    day: pencil-grey skin (default F.skin).
    warp(x, y, xc) -> (x, y): a displacement of its world points (arrays; xc = the world x of each
    stroke's middle, or None for the tone). avoid = [(x, y, r), ...]: world discs it lies round
    (a head): nothing is drawn inside, the loops are pushed off. layers: names of the layers to draw.
    Returns the world point of the chalk tip that is drawing now, or None."""
    if a <= 0.003:
        return None
    t = F.tb if t is None else t
    tq = math.floor(t * BOIL + 1e-6) / BOIL
    day = F.day if day is None else day
    cols = _cols(day)
    cam = F.cam
    z, s = cam.zoom, band.s
    w, halo, edge, core = w * band.w, halo * band.halo, edge * band.pale, core * band.core
    d0, d1 = (0.0, float(draw)) if not isinstance(draw, tuple) else draw
    dd = max(0.0, d1 - d0)
    if dd <= 0.0:
        return None
    c = F.c
    if avoid:
        c.save()
        for (ox, oy, orad) in avoid:
            sx, sy = cam.to_screen(ox, oy)
            pth = skia.Path()
            pth.addCircle(float(sx), float(sy), float(orad * z))
            c.clipPath(pth, skia.ClipOp.kDifference, True)
    thmax = float(band.thick.max()) / (s * _T0)
    # tone: the pale dust round it, and the rubbed dark of its core
    vl, vt, vr, vb = cam.view(80.0)
    m = (band.x >= vl - 200 * s) & (band.x <= vr + 200 * s) if warp is None else np.ones(len(band.x), bool)
    if m.sum() >= 2 and (halo > 0.0 or core > 0.0):
        xs, tp, bt = band.x[m], band.top[m], band.bot[m]
        dn = np.ones_like(xs) if band.dens is None else band.dens[m]
        ends = np.minimum(band.x - band.x[0], band.x[-1] - band.x)[m]
        if band.cut is not None and xs[0] < band.cut < xs[-1]:          # the tone is parted there (the two curtains)
            i = int(np.searchsorted(xs, band.cut))
            ct, cb = np.interp(band.cut, xs, tp), np.interp(band.cut, xs, bt)
            xs = np.concatenate([xs[:i], [band.cut - 0.5, band.cut + 0.5], xs[i:]])
            tp, bt = np.concatenate([tp[:i], [ct, ct], tp[i:]]), np.concatenate([bt[:i], [cb, cb], bt[i:]])
            dn, ends = np.concatenate([dn[:i], [0.0, 0.0], dn[i:]]), np.concatenate([ends[:i], [1e6, 1e6], ends[i:]])
        th = bt - tp
        thn = th / (s * _T0)
        k = np.clip(thn * 2.0, 0.0, 1.0) * dn * smooth(ends / (110.0 * s))
        if band.thin is not None:                              # where it is worn thin the rubbed dark is gone first
            k = k * np.clip(1.0 - np.interp(xs, band.x, band.thin, left=0.0, right=0.0) / 0.70, 0.0, 1.0) ** 1.3
        if seq and dd < 1.0:
            xn2 = np.abs(2.0 * (xs - band.x[0]) / max(1e-6, band.x[-1] - band.x[0]) - 1.0)
            k = k * np.clip((0.2 + 1.0 * smooth((dd - 0.25) / 0.7) - xn2) / 0.3, 0.0, 1.0)
        elif dd < 1.0:                                         # the tone follows the front of a spreading lid
            rr = 0.86 * np.abs(xs - band.ax) / max(1.0, band.reach if band.reach is not None else 0.5 * (band.x[-1] - band.x[0]))
            k = k * np.clip((d1 - rr - 0.04) / 0.10, 0.0, 1.0) * np.clip((rr + 0.18 - d0) / 0.10, 0.0, 1.0)
        g = 34.0 * s
        lodk = min(1.0, max(0.12, s * z / 0.62)) ** 1.15       # far away fewer strokes are drawn: the tone stands in for them
        grow = float(smooth((dd - 0.08) / 0.6)) if seq else 1.0
        ah = 0.0 if day else 0.70 * a * halo * grow
        ac = min(1.0, (0.88 if not day else 0.40) + 0.10 * (1.0 - lodk)) * a * core * grow
        kh = k * (1.0 - np.clip((thn - 1.6) / 0.6, 0.0, 1.0)) * ah
        kc = k * ac
        wv = 0.14 * (2.0 * vn((xs - band.ax) / s / 330.0 + seed * 7.3, seed + 3) - 1.0) / np.maximum(1.0, thn)
        deep = np.clip((thn - 1.0) / 0.8, 0.0, 1.0)            # a deep mass is dark all the way up and far down
        # a belly let down (no floor under it) is dark almost to its underside; a curtain thins toward the floor it pools on
        lowk = 0.30 if band.floor is not None else 0.30 - 0.19 * np.clip((thn - 1.7) / 0.9, 0.0, 1.0)
        v3 = np.maximum(0.70 + wv, 1.0 - lowk / np.maximum(1.0, thn))
        # one mesh, top to bottom: (y, alpha, 0 = dust colour .. 1 = dark)
        rows = [(tp - 2.0 * g, 0.0, 0.0), (tp - 0.3 * g * (1.0 - deep), 0.7 * kh * (1.0 - deep) + deep * kc, deep),
                (tp + (0.30 + wv) * th, (0.45 + 0.55 * deep) * kc, 1.0), (tp + (0.52 + wv) * th, kc, 1.0),
                (tp + v3 * th, (0.8 + 0.2 * deep) * kc, 1.0), (bt + 0.4 * g, 0.8 * kh, 0.0), (bt + 2.8 * g, 0.0, 0.0)]
        n = len(xs)
        A2 = np.stack([np.broadcast_to(np.asarray(v_, dtype=np.float64), (n,)) for _, v_, _ in rows])
        if A2.max() > 0.004:
            X2 = np.tile(xs, (len(rows), 1))
            Y2 = np.stack([np.asarray(y_, dtype=np.float64) for y_, _, _ in rows])
            M2 = np.stack([np.broadcast_to(np.asarray(m_, dtype=np.float64), (n,)) for _, _, m_ in rows])
            if warp is not None:
                X2, Y2 = warp(X2, Y2, None)
            if band.floor is not None:
                Y2 = np.minimum(Y2, band.floor)
            SX, SY = (X2 - cam.cx) * z + W / 2.0, (Y2 - cam.cy) * z + H / 2.0
            if not (SY.max() < -4 or SY.min() > H + 4 or SX.max() < -4 or SX.min() > W + 4):
                ch, cd = np.asarray(cols["halo"]) * 255.0, np.asarray(cols["dark"]) * 255.0
                rgb = (ch[None, None, :] + (cd - ch)[None, None, :] * M2[..., None] + 0.5).astype(np.int64)
                argb = (np.clip(A2 * 255.0 + 0.5, 0, 255).astype(np.int64) << 24) | (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
                pts = [skia.Point(x_, y_) for x_, y_ in zip(SX.ravel().tolist(), SY.ravel().tolist())]
                vt_ = skia.Vertices.MakeCopy(skia.Vertices.kTriangles_VertexMode, pts, None, argb.ravel().tolist(), _grid_idx(len(rows), n))
                hard = 1.0 if day else min(1.0, max(0.0, (thmax - 1.7) / 0.5))      # a deep hanging mass is pressed harder
                for gr, ga in (("soft~", 1.0 - hard), ("mid", hard)):
                    if ga > 0.004:
                        c.drawVertices(vt_, F.paint((1.0, 1.0, 1.0), ga, gr), skia.BlendMode.kDstIn)
    tip = None
    nrun = sum(L["k"] * (band.x[-1] - band.x[0]) / (s * L["cw"]) for L in _LAYERS
               if (L["drape"] <= 0 or thmax >= _HANG) and "only" not in L)
    for li, L in enumerate(_LAYERS):
        if (layers is not None and L["name"] not in layers) or (L["drape"] > 0 and thmax < _HANG):
            continue
        if "only" in L and band.thin is None:
            continue
        # far away, loops that would be only a few px turn into the tone they add up to
        lp = min(L["RX"][0] if L["RX"][0] > 0 else 60.0, 0.5 * (L["RV"][0] + L["RV"][1]) * _T0 + L["ER"][0] + 12.0) * s * z
        lod = float(ramp(lp, 2.0, 4.5))
        if lod <= 0.0:
            continue
        r = _layer(F, L, li, band, seed, tq, churn, a, w, cols, (d0, d1), seq, edge, lod, warp, avoid, day, thmax, nrun, keep)
        if r is not None and (tip is None or r[2] < tip[2]):
            tip = r
    if avoid:
        c.restore()
    return None if tip is None else (tip[0], tip[1])


# =============================================================================================
# 4. the forms
# =============================================================================================
class Tip(tuple):
    """What a form returns: (x, y), the world point of the chalk tip that is scribbling (or, when
    no stroke is being drawn at this moment, a point inside the mass), with `.band`, the Band that
    was drawn (ask it .under(x), .root(x) to hang a strand or to rest something against it)."""
    band: Band | None

    def __new__(cls, xy, band=None):
        self = super().__new__(cls, (float(xy[0]), float(xy[1])))
        self.band = band
        return self


def _hand_of(rx, ry, loops=None):
    """The hand size that suits a cloud of these radii (loops: the old way of saying how big it is)."""
    return math.sqrt(max(1e-6, rx * ry) / (430.0 * 150.0 if loops is None else max(1.0, loops) * 1402.0))


def band_cloud(cx, cy, rx, ry, seed: int = 4, rest=None, tug=None, s: float | None = None, lump: float = 1.0,
               n: int = 72) -> Band:
    """The cloud: a heavy lump about the world centre (cx, cy) with world RADII rx, ry (430 x 150
    over the sofa). Flattish on top, bellied underneath, blunt at its ends.
    rest = (x, y) or (x, y, k) or a list of them: the underside sags (or gives) until it touches
    that world point (the crown of a head, a shoulder); k = 0..1 is how far it has come. tug = (x, y, k): something pulls a point of the underside k
    (0..1) of the way toward the world point (x, y): the end of a taut strand.
    s: the hand (default: by its area, 1 for 430 x 150). lump: how uneven its outline is."""
    s = _hand_of(rx, ry) if s is None else s
    q = np.linspace(-1.0, 1.0, n)
    x = cx + q * rx
    base = (1.0 - 0.90 * np.abs(q) ** 2.8) ** 0.62
    o = rnd(seed, 31) * 50.0
    lt = 1.0 + 0.20 * lump * (2 * vn(q * 1.9 + o, seed + 11) - 1) + 0.10 * lump * (2 * vn(q * 4.3 + o, seed + 12) - 1)
    lb = 1.0 + 0.26 * lump * (2 * vn(q * 1.6 + o + 9, seed + 13) - 1) + 0.12 * lump * (2 * vn(q * 3.7 + o, seed + 14) - 1)
    lean = 0.10 * rsym(seed, 32) * q
    top = cy - ry * 0.86 * base * (lt + lean)
    bot = cy + ry * 1.0 * base * (lb - lean)
    for j in range(3):                                     # two or three bellies of its own
        bx = -0.60 + 0.60 * j + 0.22 * rsym(seed + j, 33)
        bot = bot + ry * lump * (0.16 + 0.22 * rnd(seed + j, 34)) * np.exp(-((q - bx) / (0.15 + 0.07 * rnd(seed + j, 35))) ** 2) * base
    rests = []
    if rest is not None:
        for pt in ([rest] if np.ndim(rest) == 1 else rest):
            px, py = pt[0], pt[1]
            k = pt[2] if len(pt) > 2 else 1.0
            dip = (py - float(np.interp(px, x, bot))) * k
            wd = max(0.24 * rx, 80.0 * s, 0.85 * abs(dip))
            bot = bot + dip * np.exp(-(np.abs(x - px) / wd) ** 2.6)
            rests.append((px, py, pt[3] if len(pt) > 3 else 90.0, min(1.0, max(0.0, 3.0 * k - 2.0))))
    if tug is not None:
        px, py, k = tug
        wd = max(0.10 * rx, 34.0 * s)
        bot = bot + k * (py - float(np.interp(px, x, bot))) * np.exp(-(np.abs(x - px) / wd) ** 1.5)
    return Band(x, top, bot, cx, s, rests=rests)


def gloom(F: Frame, cx, cy, rx, ry, seed: int = 4, a: float = 1.0, loops: float | None = None, w: float = 1.0,
          churn: float = CHURN, strands=(), day: bool | None = None, halo: float = 1.0, grow: float = 1.0,
          t: float | None = None, edge: float = 1.0, rest=None, tug=None, draw=None, s: float | None = None,
          avoid=(), lump: float = 1.0) -> Tip:
    """The cloud of scribble about the world centre (cx, cy) with world RADII rx, ry.

    a: pressure. grow / draw: 0..1, how much of it is scribbled yet (the birth: one hand, loop after
    loop, the pale tip leading); draw may be a pair (d0, d1) to wipe it away from its first stroke.
    rest, tug: see band_cloud (the belly that rests on a head; the point a strand pulls at).
    s: the size of the hand (default by area: 1 for 430 x 150; `loops` is the old way to say it).
    w, churn, halo, edge, day, t, avoid: see mass. strands = [(x0, y0, x1, y1, seed), ...]: loose
    crossings-out lying over what is below it (see cross_out for ones that act).
    Returns a Tip: (x, y) of the scribbling chalk, and .band."""
    s = _hand_of(rx, ry, loops) if s is None else s
    B = band_cloud(cx, cy, rx, ry, seed, rest, tug, s, lump)
    d = grow if draw is None else draw
    tip = mass(F, B, seed, a, d, churn, w, halo, edge, 1.0, day, t, seq=True, avoid=avoid)
    for (x0, y0, x1, y1, sd) in strands:
        cross_out(F, x0, (y0 + y1) / 2.0, x1, (y0 + y1) / 2.0, -1e9, amp=abs(y1 - y0) / 2.0, n=9, seed=sd, a=a, w=0.8 * w * s, day=day)
    return Tip(tip if tip is not None else B.root(cx), B)


def _thin_r(r, s: float) -> float:
    """The radius of a thin place: never under a loop and a half of the hand, or it could not be seen."""
    return max(190.0 * s if r is None else float(r), 150.0 * s)


def _thin_profile(x, x0: float, r, s: float):
    """1 in the middle of the thin place .. 0 at its radius: a plateau a third of the radius wide, long shoulders."""
    u = np.clip(np.abs(np.asarray(x, dtype=np.float64) - x0) / _thin_r(r, s), 0.0, 1.0)
    return (1.0 - u ** 1.6) ** 1.6


def _belly(d, dip: float, s: float):
    """Profile (1 at the middle .. 0) of a belly of the lid let down by `dip` world units: a heavy sack, wide at
    its mouth and round below, never a funnel."""
    wd = max(260.0 * s, 0.50 * dip)
    q = d / wd
    return 0.80 * np.clip(1.0 - q ** 3.2, 0.0, 1.0) ** (1.0 / 3.2) + 0.20 * np.exp(-(q / 1.35) ** 2)


def band_ceiling(x0: float, x1: float, y: float = 260.0, depth: float = 340.0, seed: int = 4, s: float = 1.0,
                 ax: float = 900.0, sag=None, rest=None, thin=None, amount: float = 1.0, n: int | None = None) -> Band:
    """The lid: scribble from world x0 to x1 whose underside hangs about world y and whose upper
    edge is the straight line y - depth (put that above the frame). Bellies and scallops of its own,
    fixed to its anchor `ax` and scaled by the hand `s`.
    sag = (x, d, width): it hangs d lower about world x (over the child: heavier in the middle).
    rest = (x, y) or (x, y, k): one belly is let down to touch that world point (k: how far yet). thin = (x, r, k): about world x,
    over the radius r, it is thinned by k (0..1): one layer deep, the place where light is guessed.
    amount: 0..1, how much of it is left (unravelling): it gets shallower."""
    n = n or int(np.clip((x1 - x0) / (60.0 * s), 24, 220))
    x = np.linspace(x0, x1, n)
    X = (x - ax) / s
    o = rnd(seed, 41) * 60.0
    bel = 46.0 * (2 * vn(X / 460.0 + o, seed + 1) - 1) + 30.0 * (2 * vn(X / 190.0 + o * 1.7, seed + 2) - 1)
    bel = bel + 130.0 * np.clip((vn(X / 520.0 + o * 0.6, seed + 4) - 0.52) / 0.48, 0.0, 1.0) ** 1.4
    bot = y + s * bel
    if sag is not None:
        bot = bot + sag[1] * np.exp(-((x - sag[0]) / sag[2]) ** 2)
    rests = []
    top = np.full(n, y - depth)
    bot = top + np.maximum(bot - top, 0.0) * (0.30 + 0.70 * amount)
    if rest is not None:
        for pt in ([rest] if np.ndim(rest) == 1 else rest):
            px, py = pt[0], pt[1]
            k = pt[2] if len(pt) > 2 else 1.0
            dip = (py - float(np.interp(px, x, bot))) * k
            bot = bot + dip * _belly(np.abs(x - px), abs(dip), s)
            rests.append((px, py, pt[3] if len(pt) > 3 else 90.0, min(1.0, max(0.0, 3.0 * k - 2.0))))
    tn = None
    if thin is not None and thin[2] > 0.0:
        tn = thin[2] * _thin_profile(x, thin[0], thin[1], s)
    return Band(x, top, bot, ax, s, None, pale=0.6, rests=rests, thin=tn)


def _span(F: Frame, x0, x1, s: float, q: float = 48.0):
    """World x range and sample count of a lid that covers the frame: snapped to a fixed grid, so
    its samples do not slide when the camera moves."""
    vl, _, vr, _ = F.cam.view(0.0)
    g = q * s
    a = math.floor((vl - 330.0 * s) / g) * g if x0 is None else x0
    b = math.ceil((vr + 330.0 * s) / g) * g if x1 is None else x1
    return a, b, (int(round((b - a) / g)) + 1 if x0 is None and x1 is None else None)


def lid_for(cam, hang: float = 235.0, above: float = 130.0, s: float | None = None) -> dict:
    """The lid that suits a framing, as keyword arguments for ceiling / curtains / band_ceiling:
    the hand s = 1 / zoom (its loops as large on screen as the cloud's were at zoom 1), the
    underside `hang` screen px below the frame top, the upper edge `above` px above it. Every
    module that draws the lid at a hand-off must get its numbers from the same camera this way."""
    s = 1.0 / cam.zoom if s is None else s
    k = 1.0 / cam.zoom
    return dict(s=s, y=cam.view()[1] + hang * k, depth=(hang + above) * k)


def ceiling(F: Frame, x0=None, x1=None, y: float = 260.0, a: float = 1.0, seed: int = 4, t: float | None = None,
            depth: float = 340.0, s: float = 1.0, ax: float = 900.0, sag=None, rest=None, thin=None, amount: float = 1.0,
            draw=1.0, churn: float = CHURN, w: float = 1.0, halo: float = 1.0, edge: float = 1.0, day: bool | None = None,
            glow: float = 1.0, avoid=(), reach: float = 4200.0, cloud: Band | None = None, spread: float = 1.0,
            front: float | None = None) -> Tip:
    """The scribble as a lid across the top of the frame: its underside hangs about world y, its
    upper edge is y - depth (keep that above the frame top; lid_for(cam) gives y, depth and s for
    a framing). x0, x1: its world extent (default: the frame and a margin, whatever the camera).
    s: the hand (for a wide framing 1 / zoom, so that its loops are as large on screen as the
    cloud's were). ax: its anchor (the world x of the child when it spread out).
    sag, rest, thin, amount: see band_ceiling. glow: the pale light guessed behind a thin place.
    cloud, spread, front: the lid opens out of that cloud band (spread 0 = the cloud itself .. 1 =
    the lid; see spread_band), or gathers back into it.
    draw: 0..1, it is scribbled from the anchor outward, out to draw * reach world units either
    way, the ragged front carrying the tips (or a pair (d0, d1) to wipe it from the middle).
    Returns a Tip with .band."""
    if depth <= 8.0:                                       # the old call gave a factor
        depth = depth * 340.0 * s
    xa, xb, n = _span(F, x0, x1, s)
    B = band_ceiling(xa, xb, y, depth, seed, s, ax, sag, rest, thin, amount, n)
    if cloud is not None and spread < 1.0:
        B = spread_band(cloud, B, spread, front)
    kl = 1.0 if B.pale <= 0.6 else max(0.0, (1.0 - B.pale) / 0.4)          # how much of a lid it is yet
    if thin is not None and glow > 0.0 and kl > 0.0 and not (F.day if day is None else day):
        smudge(F, thin[0], y - 0.30 * depth, _thin_r(thin[1], s) * 0.85, depth * 0.62, C.MOON, 0.26 * thin[2] * glow * a * kl, "glow",
               additive=True)
    B = B._like(B.x, B.top, B.bot, reach=reach)
    tip = mass(F, B, seed, a, draw, churn, w, halo, edge, 1.0, day, t, avoid=avoid, keep=0.3 + 0.7 * amount)
    return Tip(tip if tip is not None else B.root(ax), B)


STRAND_W = 20.0      # the width of one strand of the curtain's edge, in units of the hand (world units: STRAND_W * s)


def peel(t: float, attacks, dur: float = 0.34, n0: float = 0.0) -> float:
    """How many strands have come aside by the time t: one for every time in `attacks` (seconds of
    the song), each taking `dur` seconds to peel off and be gathered (the fraction is the strand on
    its way). Give the result to curtains(strands=...). n0: strands taken before the first attack."""
    return n0 + sum(ease(seg(t, tp, tp + dur)) for tp in attacks)


def _counts(strands, gap, left, right, sw):
    """Strands taken on the left and on the right: given, or (the first version's way) as many as fit
    between the gap and the grip."""
    if strands is None:                # (a grip on the wrong side of the gap holds nothing: that side stays shut)
        cl = 0.0 if left is None else (gap - left[0]) / sw
        cr = 0.0 if right is None else (right[0] - gap) / sw
    elif np.ndim(strands) == 0:
        cl = cr = float(strands)
    else:
        cl, cr = float(strands[0]), float(strands[1])
    return (max(0.0, cl) if left is not None else 0.0), (max(0.0, cr) if right is not None else 0.0)


def _slot(yy, gap, sgn, c, sw, apex, gy, seed):
    """World x of one edge of the opening at the heights yy: c strands' widths from the gap, a little
    uneven (a strand does not hang like a ruler), drawing together toward the apex above."""
    if c <= 0.0:
        return np.full(np.shape(yy), float(gap))
    yy = np.asarray(yy, dtype=np.float64)
    sh = smooth((yy - apex) / max(1.0, 0.42 * (gy - apex)))
    wob = 0.22 * sw * min(1.0, c) * (2.0 * vn(yy / (9.0 * sw) + 3.1 * sgn, seed + 71) - 1.0)
    return gap + sgn * (c * sw * (0.30 + 0.70 * sh) + wob * sh)


def curtain_gap(cam, gap: float, strands=None, left=None, right=None, s: float = 1.0, ground: float = 742.0,
                strand_w: float | None = None):
    """The opening of the parted curtains as the six numbers weather's shaft / gap_light take:
    (x0, w0, y0, x1, w1, y1): a slit above the frame top, the patch of light on the ground between
    the two hanging edges. Arguments as in curtains. Draw the light BEFORE the curtains."""
    sw = STRAND_W * s if strand_w is None else float(strand_w)
    cl, cr = _counts(strands, gap, left, right, sw)
    y0 = cam.view()[1] - 60.0 / cam.zoom
    wl, wr = cl * sw, cr * sw
    return (gap + 0.15 * (wr - wl), 0.20 * (wl + wr) + 0.1 * sw, y0, gap + 0.5 * (wr - wl), 0.5 * (wl + wr), ground)


def _strand_side(F: Frame, gap, sgn, c, grip, sw, s, apex, ground, taut, tremble, seed, nfree, wfree, act: float = 1.0):
    """The strands of one edge of the opening, as world polylines (R, 39, 2) and width factors (R, 39).
    Strand j hangs from the lid at about gap + sgn * (j + 0.5) * sw. j < c: it has been taken: it runs
    taut from its root into the grip and its end hangs below the hand. The strand c is on its way (the
    fraction of c): caught at the height of the hand, pulled over, its lower end whipping in toward
    the opening and then drawn up. The next few still hang at the edge, the fringe of the curtain.
    act: how much of the bow into the light and of the whip is shown: 1 when the count is timed (peel: every
    strand passes through its move), small when the count follows the grip (a hand at rest may hold a strand
    half taken, and a strand cannot hang still in mid-whip)."""
    M1, M2 = 14, 26
    n_take = int(math.ceil(c - 1e-9)) if grip is not None else 0
    R = n_take + nfree
    if R <= 0:
        return None
    j = np.arange(R)
    hj = htab(j, 7, seed * 13 + (95 if sgn > 0 else 59))
    h2 = htab(j, 11, seed * 17 + (31 if sgn > 0 else 77))
    xr = gap + sgn * (j + 0.5 + 0.30 * (hj - 0.5)) * sw                    # where each hangs from
    p = np.clip(c - j, 0.0, 1.0) if grip is not None else np.zeros(R)      # how far each has been taken
    gy0 = grip[1] if grip is not None else apex + 0.62 * (ground - apex)
    gy0 = max(gy0, apex + 1.0)
    yend = ground - s * (4.0 + 16.0 * h2)
    # the point of each strand that the hand takes: hooked, it first gives a little toward the opening, then it
    # goes over to the grip
    pg = 1.0 - (1.0 - np.clip((p - 0.20) / 0.42, 0.0, 1.0)) ** 2.4
    ant = np.sin(math.pi * np.clip(p / 0.44, 0.0, 1.0)) ** 1.4
    if grip is not None:
        ang = 2.0 * math.pi * hj
        gxj = grip[0] + s * 3.0 * np.cos(ang) * np.minimum(j, 5) / 5.0
        gyj = gy0 + s * 3.0 * np.sin(ang)
    else:
        gxj, gyj = xr, np.full(R, gy0)
    hx = xr + (gxj - xr) * pg
    hy = gy0 + (gyj - gy0) * pg
    # above the hand: from the root to that point; hanging it sways a little, taken it is a straight line under load
    v = np.linspace(0.0, 1.0, M1)[None, :]
    ux = xr[:, None] + (hx - xr)[:, None] * v
    uy = apex + (hy - apex)[:, None] * v
    sway = s * (5.0 * np.sin(uy / (95.0 * s) + 6.0 * hj[:, None]) + 3.5 * (2.0 * vn(uy / (60.0 * s) + 9.0 * j[:, None], seed + 5) - 1.0))
    ux = ux + sway * (1.0 - pg)[:, None] * np.sin(math.pi * np.minimum(1.0, 1.15 * v)) ** 0.5
    bell = np.sin(math.pi * v)
    amp = np.minimum(1.5 * sw + 0.10 * (gy0 - apex), (0.8 * (j + 0.5) + 0.3) * sw)                           # (never across the middle)
    ux = ux - sgn * (act * amp * ant)[:, None] * np.sin(math.pi * v ** 1.7) ** 1.2                            # the bow into the light
    ln = np.hypot(hx - xr, hy - apex)[:, None]
    ux = ux + sgn * (1.0 - taut) * 0.10 * ln * bell * pg[:, None] * (0.6 + 0.8 * hj[:, None])
    uy = uy + (1.0 - taut) * 0.05 * ln * bell * pg[:, None]
    if tremble > 0.0:                                      # (it comes and goes, strand by strand: arms that tremble, not a motor)
        env = (0.55 + 0.45 * np.sin(2.0 * math.pi * 0.8 * F.t + 6.28 * hj))[:, None]
        ux = ux + tremble * env * bell * pg[:, None] * np.sin(2.0 * math.pi * 8.5 * F.t + 2.3 * j[:, None] + 7.0 * v)
    # below the hand: hanging to the ground; when taken, most of it is in the bunch and only an end hangs on
    long_ = (h2 < 0.34) | (j == 0)
    tail = np.where(long_, 0.50 + 0.50 * hj, 0.07 + 0.20 * hj) * (ground - gy0)
    pt = smooth((p - 0.22) / 0.78)
    ell = (yend - gy0) * (1.0 - pt) + np.minimum(tail, yend - gy0) * pt
    u = np.linspace(0.0, 1.0, M2)[None, :]
    swing = np.sin(math.pi * np.clip((p - 0.12) / 0.84, 0.0, 1.0)) ** 1.3 * (1.0 - 0.25 * p)       # the whip: in toward the opening, and back
    th = -sgn * (0.95 * act * swing)[:, None] * u ** 1.25
    th = th + (0.10 + 0.10 * pg[:, None]) * np.sin(u * (3.0 + 4.0 * hj[:, None]) + 6.0 * h2[:, None]) * u ** 0.5
    if tremble > 0.0:
        th = th + 0.010 * tremble * pg[:, None] * u * np.sin(2.0 * math.pi * 5.0 * F.t + 1.7 * j[:, None])
    dx_, dy_ = np.sin(th) * ell[:, None] / (M2 - 1), np.cos(th) * ell[:, None] / (M2 - 1)
    lx = hx[:, None] + np.concatenate([np.zeros((R, 1)), np.cumsum(dx_[:, 1:], axis=1)], axis=1)
    ly = hy[:, None] + np.concatenate([np.zeros((R, 1)), np.cumsum(dy_[:, 1:], axis=1)], axis=1)
    lx = lx + sgn * s * (2.0 + 1.6 * np.minimum(j, 6))[:, None] * pt[:, None] * u ** 0.6       # the ends in the bunch spread a little
    over = ly - (ground - 3.0 * s)
    lx = np.where(over > 0.0, lx + sgn * (2.0 * h2[:, None] - 1.0) * 1.5 * over, lx)           # what reaches the ground lies along it
    ly = np.minimum(ly, ground - 3.0 * s - 2.0 * s * np.sin(np.maximum(over, 0.0) / (9.0 * s)) ** 2)
    P = np.stack([np.concatenate([ux, lx[:, 1:]], axis=1), np.concatenate([uy, ly[:, 1:]], axis=1)], axis=-1)
    # pressure: each its own; the fringe thinner the further it is from the opening; ends thin out
    prm = np.concatenate([np.broadcast_to(0.25 + 0.75 * smooth(v / 0.12), (R, M1)),                 # (it comes out of the lid, not out of a ruled line)
                          1.0 - 0.40 * np.broadcast_to(u[:, 1:], (R, M2 - 1)) ** 1.5], axis=1)
    wv = 0.80 + 0.34 * vn(np.arange(M1 + M2 - 1)[None, :] / 5.0 + 7.0 * j[:, None], seed + 9)
    free_k = np.clip((c + wfree - j) / max(1.0, wfree - 0.4), 0.0, 1.0)                        # 1 for taken strands; 0 as one first shows
    wj = (0.78 + 0.44 * hj) * (0.55 + 0.45 * np.maximum(pg, free_k * 0.8)) * np.where(p > 0.0, 1.0, free_k ** 0.8)
    wj = wj * (1.0 + 0.40 * np.sin(math.pi * p) ** 0.7)                                         # the one on its way is pressed hard
    return P, prm * wv * wj[:, None]


_SHARDS_GONE = 4.4     # seconds after the rip by which the last shard of the curtains has been rubbed away
_LID_GONE = 10.4       # ... and the last wisp of the lid
REMNANT_R = 118.0      # half width of the one piece that stays


class _Shatter:
    """The curtains coming apart (rip seconds ago). Every stroke breaks into pieces of line, six points
    long; each piece curls up as it is let go, turns about itself and is rubbed away in its own time;
    pieces that lie in the same cell of a ragged grid fly together, a loosening tangle: thrown outward
    from the gap as the tear passes, falling as paper falls, turning, sailing off, gone within about
    three seconds. A closed form of `rip`: nothing is kept between frames.
    runs(x, y, xw, key) -> x, y, width factors, for arrays (R, M) of world points; __call__ serves the
    tone (which only keeps the opening's own displacement and fades by itself)."""
    LS, CW, CH = 6, 250.0, 240.0

    def __init__(self, base, gap, ax, s, seed, rip, top, ground, hand_y):
        self.base, self.gap, self.ax, self.s, self.seed, self.rip = base, float(gap), float(ax), float(s), int(seed), float(rip)
        self.top, self.ground, self.hand_y = float(top), float(ground), float(hand_y)
        self.kbreak = seg(rip, 0.0, 0.10)

    def __call__(self, x, y, xc):
        return (x, y) if self.base is None else self.base(x, y, xc)

    def _move(self, cx, cy, late=0.0):
        """For shard centres (arrays): pivot x, y, shift x, y, cos, sin, width factor."""
        s, sd = self.s, self.seed
        U, V = (cx - self.ax) / s, (cy - self.top) / s
        ci = np.floor(U / self.CW + 0.34 * (2.0 * vn(V / 310.0 + 7.0, sd + 1) - 1.0)).astype(np.int64)
        cj = np.floor(V / self.CH + 0.34 * (2.0 * vn(U / 270.0 + 3.0, sd + 2) - 1.0)).astype(np.int64)
        idn = ci * 7919 + cj * 104729 + sd * 1543
        h = [TAB[(idn * m_ + 17 * i_ + 5) & 8191] for i_, m_ in enumerate((31, 37, 41, 43, 47, 53, 59))]
        px, py = self.ax + s * (ci + 0.5) * self.CW, self.top + s * (cj + 0.5) * self.CH
        sg = np.where(px >= self.gap, 1.0, -1.0)
        hi = np.clip((self.hand_y - py) / (900.0 * s), 0.0, 1.0)                 # how far above the hands (the tear runs upward)
        lo = np.clip((py - self.hand_y) / max(1.0, self.ground - self.hand_y), 0.0, 1.0)
        dly = 0.40 * np.clip(np.abs(px - self.gap) / (1500.0 * s), 0.0, 1.0) ** 0.8 + 0.10 * h[0] + 0.10 * hi + late
        tau = np.maximum(self.rip - dly, 0.0)
        e1 = 1.0 - np.exp(-tau / 0.42)
        # thrown outward, then sailing on; the upper ones are lifted first, all of them fall as paper falls
        dx = sg * s * ((330.0 + 620.0 * h[1]) * 0.42 * e1 + (50.0 + 170.0 * h[2]) * tau)
        vt = s * (250.0 + 330.0 * h[4]) * (1.0 - 0.45 * hi)
        dy = -s * (90.0 + 420.0 * h[3] * (0.4 + 0.6 * hi)) * 0.34 * (1.0 - np.exp(-tau / 0.34)) + vt * (tau - 0.6 * (1.0 - np.exp(-tau / 0.6)))
        fl = 1.0 - np.exp(-tau / 0.8)
        dx = dx + s * 26.0 * fl * np.sin(2.0 * math.pi * (0.55 + 0.5 * h[5]) * tau + 6.28 * h[6])
        rot = np.where(h[6] < 0.5, -1.0, 1.0) * ((1.0 + 3.4 * h[5]) * 0.5 * (1.0 - np.exp(-tau / 0.5)) + (0.25 + 0.75 * h[0]) * tau)
        rot = rot + 0.35 * fl * np.sin(2.0 * math.pi * (0.5 + 0.4 * h[2]) * tau + 6.28 * h[1])
        life = 1.0 + 1.5 * h[2] + 0.5 * lo
        wm = (1.0 - 0.40 * np.clip(tau / life, 0.0, 1.0)) * (1.0 - smooth((tau - life) / 0.7))
        return px, py, dx, dy, np.cos(rot), np.sin(rot), wm, tau

    def runs(self, x, y, xw, key, slot=True):
        if slot and self.base is not None:
            x, y = self.base(x, y, None if xw is None else xw[:, None])
        R, M = x.shape
        LS = self.LS
        off = (key % LS).astype(np.int64)
        K = (M + LS - 1) // LS + 1
        # the points of each run laid out so that its pieces are the columns of a (R, K, LS) block
        col = np.arange(M)[None, :] + off[:, None]
        row = np.arange(R)[:, None]
        xp, yp = np.full((R, K * LS), np.nan), np.full((R, K * LS), np.nan)
        xp[row, col], yp[row, col] = x, y
        xp, yp = xp.reshape(R, K, LS), yp.reshape(R, K, LS)
        ok = ~np.isnan(xp)
        cnt = np.maximum(ok.sum(axis=2), 1)
        cx, cy = np.where(ok, xp, 0.0).sum(axis=2) / cnt, np.where(ok, yp, 0.0).sum(axis=2) / cnt
        px, py, dx, dy, cs, sn, wk, tau = self._move(cx, cy)
        kk = key[:, None] * 61 + np.arange(K)[None, :] * 977
        h1, h2, h3, h4 = (TAB[(kk * m_ + a_) & 8191] for m_, a_ in ((1, 11), (3, 7), (5, 29), (7, 43)))
        g = 1.0 - np.exp(-tau / 0.30)
        # let go, every piece of line curls up, as a taut thing does when it is cut: a hook, a C, now and then
        # nearly a ring. So the pieces stay scribble (a sheaf of straight sticks is hay). Each segment of the piece
        # is turned a little further than the one before it; the piece keeps its length and its middle
        curl = np.where(h3 < 0.5, -1.0, 1.0) * (0.5 + 4.6 * h1 ** 1.4) * (g + 0.08 * tau)
        okd = ok[..., 1:] & ok[..., :-1]
        sx, sy = np.where(okd, np.diff(xp, axis=2), 0.0), np.where(okd, np.diff(yp, axis=2), 0.0)
        nseg = np.maximum(okd.sum(axis=2), 1)[..., None]
        al = curl[..., None] * ((np.cumsum(okd, axis=2) - 0.5) / nseg - 0.5)
        ca, sa = np.cos(al), np.sin(al)
        z1 = np.zeros((R, K, 1))
        qx = np.concatenate([z1, np.cumsum(sx * ca - sy * sa, axis=2)], axis=2)
        qy = np.concatenate([z1, np.cumsum(sx * sa + sy * ca, axis=2)], axis=2)
        qx = qx - (np.where(ok, qx, 0.0).sum(axis=2) / cnt)[..., None]
        qy = qy - (np.where(ok, qy, 0.0).sum(axis=2) / cnt)[..., None]
        # ... turns about itself, and drifts a little from its neighbours: a shard loosens as it flies
        own = (2.0 * h2 - 1.0) * (0.9 * g + 0.5 * tau)
        co, so = np.cos(own)[..., None], np.sin(own)[..., None]
        ex, ey = cx + self.s * 52.0 * (2.0 * h4 - 1.0) * tau, cy + self.s * 36.0 * (2.0 * h1 - 1.0) * tau
        rx, ry = ex[..., None] + qx * co - qy * so - px[..., None], ey[..., None] + qx * so + qy * co - py[..., None]
        # ... and is rubbed away in its own time (the shard thins from half a second on; its last pieces sail longest)
        wk = wk * (1.0 - smooth((tau - (0.45 + 2.6 * h4 * h4 + 0.5 * h2)) / 0.6))
        cs, sn = cs[..., None], sn[..., None]
        xo = (px[..., None] + dx[..., None] + rx * cs - ry * sn).reshape(R, K * LS)[row, col]
        yo = (py[..., None] + dy[..., None] + rx * sn + ry * cs).reshape(R, K * LS)[row, col]
        wm = np.broadcast_to(wk[..., None], (R, K, LS)).reshape(R, K * LS)[row, col]
        sidx = col // LS
        cut = sidx[:, 1:] != sidx[:, :-1]                      # the line is broken there: both ends come to a point
        brk = np.zeros((R, M), bool)
        brk[:, 1:] |= cut
        brk[:, :-1] |= cut
        return xo, yo, np.where(brk, wm * (1.0 - self.kbreak), wm)

    def point(self, x, y, late=0.0):
        """Where a small thing at the world point (x, y) has got to (it flies with its shard), its pressure, its turn."""
        px, py, dx, dy, cs, sn, wk, _ = (float(v[0]) for v in self._move(np.array([float(x)]), np.array([float(y)]), late))
        rx, ry = x - px, y - py
        return px + dx + rx * cs - ry * sn, py + dy + rx * sn + ry * cs, wk, math.atan2(sn, cs)


def _lid_pieces(F: Frame, lid: Band, rip, gap, hwl, hwr, seed, a, churn, w, halo, edge, day, t):
    """The lid after the rip: cut into a few ragged pieces (about 430 hands wide) that drift up and
    outward, tilt, draw in and lose their strokes; wisps by six seconds, nothing by ten."""
    s, ax = lid.s, lid.ax
    a_in = seg(rip, 0.20, 0.62)
    a_out = 1.0 - seg(rip, 7.6, _LID_GONE)
    if a_in * a_out * a <= 0.003:
        return

    def cell(xx):
        X = (np.asarray(xx, dtype=np.float64) - ax) / s
        q = X / 430.0 + 0.9 * vn(X / 1300.0, seed + 9)
        ci = np.floor(q)
        return ci.astype(np.int64), q - ci

    def moves(ci, xx):
        h1, h2, h3, h4 = (TAB[(ci * m_ + seed * 17 + 5 * i_) & 8191] for i_, m_ in enumerate((131, 137, 139, 149)))
        tau = np.maximum(rip - 0.5 * h3, 0.0)
        f = 1.0 - np.exp(-tau / 2.6)
        away = np.where(xx >= gap, 1.0, -1.0)
        near = np.exp(-(np.abs(xx - gap) / (330.0 * s)) ** 2)               # the pieces over the opening go up and out of sight
        dx = away * s * ((40.0 + 200.0 * h1) * f + 26.0 * tau)
        # let go, a piece sags a little first; then it rises, slowly, and those over the opening fast
        dy = s * ((36.0 + 50.0 * h4) * (1.0 - near) * (1.0 - np.exp(-tau / 0.45))
                  - (10.0 + 30.0 * h2 + 300.0 * near) * f - (14.0 + 12.0 * h2 + 40.0 * near) * tau)
        rot = away * (0.30 * h4 - 0.08) * f
        return dx, dy, rot, tau

    ci, fr = cell(lid.x)
    k1 = float(smooth(rip / 0.9))
    endp = np.clip(1.0 - np.abs(2.0 * fr - 1.0) ** 2.8, 0.0, 1.0) ** 0.62                     # blunt ends, like a cloud's
    off = np.where(lid.x >= gap, lid.x - gap - hwr, gap - hwl - lid.x)                        # nothing where the opening went up
    endp = endp * smooth(off / (150.0 * s))
    hq = TAB[(ci * 151 + seed * 23) & 8191]
    # each piece draws in to a ragged lump (its upper edge comes down into the picture) and goes on shrinking
    th0 = (lid.bot - lid.top) * (1.0 - k1 * (1.0 - endp))
    th1 = np.minimum(lid.bot - lid.top, s * (190.0 + 130.0 * hq)) * endp
    th = (th0 + (th1 - th0) * float(smooth(seg(rip, 0.15, 2.6)))) * (1.0 - 0.40 * seg(rip, 2.6, 7.5))
    _, _, _, tau_s = moves(ci, lid.x)
    kp = (1.0 - 0.88 * np.clip((tau_s - 0.5) / 5.4, 0.0, 1.0) ** 0.75) * (0.40 + 0.60 * seg(rip, 0.3, 1.1))
    mid = lid.bot - 0.5 * (lid.bot - lid.top)
    # ... and its ends lift off the lid's underside as it does: a lump tapers to its own middle, a scrap of cloud,
    # not a wedge lying on a ruled line
    lift = float(smooth(seg(rip, 0.15, 2.0))) * 0.44 * np.minimum(lid.bot - lid.top, s * (190.0 + 130.0 * hq)) * (1.0 - endp) ** 1.3
    bot = lid.bot - lift

    def warp(x, yy, xc):
        src = x if xc is None else np.broadcast_to(xc, np.shape(x))
        cc, ff = cell(src)
        dx, dy, rot, _ = moves(cc, src)
        # the piece's own middle (where its cell is half way): it tilts about that point
        px = src + (0.5 - ff) * 430.0 * s
        py = np.interp(px, lid.x, mid)
        cs, sn = np.cos(rot), np.sin(rot)
        rx, ry = x - px, yy - py
        return px + dx + rx * cs - ry * sn, py + dy + rx * sn + ry * cs

    B = Band(lid.x, bot - th, bot, ax, s, lid.dens, pale=0.6 + 0.4 * seg(rip, 1.0, 5.0), core=0.62 - 0.46 * seg(rip, 0.8, 4.5),
             halo=1.0 - 0.5 * seg(rip, 1.0, 5.0), thin=lid.thin)
    B.reach = 4200.0
    mass(F, B, seed, a * a_in * a_out, 1.0, churn, w, halo, edge, 1.0, day, t, warp=warp, keep=kp)


def _band_remnant(x, y, r, seed, k: float = 0.0, r1: float = 56.0) -> Band:
    """The band of the piece that stays (k = 0), drawn in toward the size of the small tangle (k = 1, radius r1)."""
    rx, ry = r * (1.25 * r1 / r) ** k, 0.50 * r * (1.1 * r1 / (0.50 * r)) ** k
    B = band_cloud(x, y, rx, ry, seed, s=0.56 * r / REMNANT_R * (rx / r) ** 0.5, lump=1.5)
    B.core = 0.62
    return B


def remnant(F: Frame, x, y, r: float = REMNANT_R, a: float = 1.0, seed: int = 4, t: float | None = None,
            day: bool | None = None, draw=1.0, keep: float = 1.0, churn: float = CHURN) -> Tip:
    """The one piece of the scribble that is left when the lid has drifted away (201.25 + 10 s to
    about 220 s): a small ragged scrap of cloud about the world point (x, y), `r` its half width
    (REMNANT_R = 118: a little over twice the small tangle it will wind itself up into). It rides
    where you put it: behind and above the child, lagging. curtains(rip=, stays=(x, y)) draws the same
    piece while the lid breaks up round it. Returns a Tip with .band."""
    B = _band_remnant(x, y, r, seed)
    tip = mass(F, B, seed, a, draw, churn, 1.2, 1.0, 1.0, 1.0, day, t, seq=True, keep=keep)
    return Tip(tip if tip is not None else (x, y), B)


def curtains(F: Frame, y: float = 260.0, ground: float = 742.0, drop: float = 1.0, gap: float | None = None, left=None,
             right=None, apex: float | None = None, depth: float = 340.0, a: float = 1.0, seed: int = 4, s: float = 1.0,
             ax: float = 900.0, x0=None, x1=None, taut: float = 1.0, rip: float | None = None, t: float | None = None,
             draw=1.0, churn: float = CHURN, w: float = 1.0, halo: float = 1.0, edge: float = 1.0, day: bool | None = None,
             sag=None, thin=None, tremble: float = 0.0, cloud: Band | None = None, spread: float = 1.0,
             front: float | None = None, strands=None, strand_w: float | None = None, lit: float = 1.0, stays=None) -> Tip:
    """The lid let down to the ground: a heavy curtain of tall loops, and its parting.

    y, depth, seed, s, ax, sag, thin: the lid it hangs from (the same numbers as the ceiling it was:
    curtains(drop=0) IS that ceiling). drop: 0..1, how far it has come down to `ground` (it comes
    down unevenly, in tongues). gap: the world x where it parts.
    The parting. The curtain's edge at the gap is made of strands, each strand_w wide (default
    STRAND_W * s), hanging from the lid to the ground. strands: how many of them have been taken
    aside so far, a number for both sides or (left, right); its fraction is the strand that is on
    its way: it is caught at the height of the hand, pulled over into the grip, and its lower end
    whips in and is drawn up into the bunch. The opening is as many strands wide as have been taken;
    taken strands run taut from the lid into the grip. left / right: the world point of the hand
    that holds the left / the right bunch (the grip). strands=None: as many as fit between the gap
    and each grip: the count follows the hands of a performance, the opening's two edges are in the
    two grips (the strand on its way is then shown without its whip: a resting hand may hold one
    half taken). A side with no grip stays shut. Use peel(F.t, attacks) for a strand on every attack.
    apex: the world y toward which the opening draws together at the top (default: the top of
    the lid, above the frame, so that light can fall in from above). taut: 1 = the taken strands
    are straight lines under load, 0 = they belly. tremble: world units of shiver of the held
    strands, on the TRUE time. lit: 0..1, the light of the opening on the strands beside it.
    rip: seconds since the sheet ripped (None: not yet; 0 is still the held picture). Every stroke
    of the two curtains, the strands and the bunches with them, breaks into pieces of line that
    curl up and fly: thrown outward from the gap, falling, turning, sailing off, rubbed away one by
    one within about 3.5 s. Behind them the lid shows broken into a few ragged pieces that sag, then drift up and
    outward and lose their strokes: wisps by 6 s, nothing by 10.4 s. Keep every other argument as
    it was at the rip (the last grips and strands, drop = 1, the lid's numbers of that moment).
    stays = (x, y) or (x, y, r): the world point where the one piece that stays rides (remnant):
    it comes up among the lid's pieces over 2.5 s and is all that is left from 10.4 s on.
    Returns a Tip with .band; .edges = (left edge, right edge), each a function of world y giving
    the world x of that edge of the opening; .grips = the two knots (or None)."""
    xa, xb, n = _span(F, x0, x1, s)
    B = band_ceiling(xa, xb, y, depth, seed, s, ax, sag, None, thin, 1.0, n)
    if cloud is not None and spread < 1.0:
        B = spread_band(cloud, B, spread, front)
    X = (B.x - ax) / s
    hem = ground - s * (22.0 + 44.0 * vn(X / 120.0 + 3.0, seed + 7))
    dl = np.clip(drop * 1.5 - 0.5 * vn(X / 350.0 + 5.0, seed + 8), 0.0, 1.0)
    dl = dl * dl * (3.0 - 2.0 * dl)
    top = float(B.top[0])
    apex = top if apex is None else apex
    if gap is None:
        gap = 0.5 * (left[0] + right[0]) if left is not None and right is not None else ax
    sw = STRAND_W * s if strand_w is None else float(strand_w)
    cl, cr = _counts(strands, gap, left, right, sw)
    gyl = max(left[1], apex + 1.0) if left is not None else apex + 0.62 * (ground - apex)
    gyr = max(right[1], apex + 1.0) if right is not None else apex + 0.62 * (ground - apex)
    lid_top, lid_bot, lid_dens = B.top.copy(), B.bot.copy(), (None if B.dens is None else B.dens.copy())
    bot = B.bot + (np.maximum(hem, B.bot) - B.bot) * dl
    opened = cl > 0.0 or cr > 0.0 or bool(rip)
    B = B._like(B.x, B.top, bot, floor=ground, cut=gap if opened else None)

    def e_l(yy):
        return _slot(yy, gap, -1.0, cl, sw, apex, gyl, seed)

    def e_r(yy):
        return _slot(yy, gap, 1.0, cr, sw, apex, gyr, seed)

    def warp(x, yy, xc):
        # the stuff that hung where the opening is now is pushed aside and bunches against its edge
        side = (x >= gap) if xc is None else (xc >= gap)
        hr = np.maximum(e_r(yy) - gap, 0.0)
        hl = np.maximum(gap - e_l(yy), 0.0)
        h = np.where(side, hr, hl)
        sg = np.where(side, 1.0, -1.0)
        d = np.maximum(sg * (x - gap), 0.0)                # (what a loop has on the far side of the gap comes to lie on its own edge)
        zone = h * 1.5 + 1.8 * sw
        xo = gap + sg * (d + h * np.clip(1.0 - d / zone, 0.0, 1.0) ** 1.4)
        xo = np.where(h > 0.0, xo, x)
        return xo, yy

    aa = a
    ripped = rip is not None and rip > 0.0
    # beside the opening the stuff is drawn out into strands: it is thinner there, so that it does not clot
    for c_, sgn in ((cl, -1.0), (cr, 1.0)):
        if c_ <= 0.0:
            continue
        hw = c_ * sw
        ko = float(smooth(hw / (46.0 * s)))
        d = sgn * (B.x - gap)
        fr = np.where(d >= 0.0, 1.0 - 0.62 * ko * (1.0 - smooth(d / (hw * 1.5 + 1.8 * sw))), 1.0)
        B.dens = fr if B.dens is None else B.dens * fr
    B.reach = 4200.0
    dayf = F.day if day is None else day
    sh = None
    if ripped:
        # the sheet has ripped. Behind: the lid, broken into a few ragged pieces that drift up and away; the piece that
        # stays; in front: the two curtains, every stroke of them in pieces that fall, turn and sail off
        if rip < _LID_GONE:
            lid = Band(B.x, lid_top, lid_bot, ax, s, lid_dens, pale=0.6, thin=B.thin)
            _lid_pieces(F, lid, rip, gap, cl * sw, cr * sw, seed, a, churn, w, halo, edge, dayf, t)
        if stays is not None:
            remnant(F, stays[0], stays[1], stays[2] if len(stays) > 2 else REMNANT_R, a * float(smooth((rip - 0.8) / 1.7)), seed, t=t, day=dayf)
        if rip >= _SHARDS_GONE:
            out = Tip(B.root(ax), B)
            out.edges, out.grips = (e_l, e_r), (None, None)
            return out
        sh = _Shatter(warp if opened else None, gap, ax, s, seed, rip, top, ground, min(gyl, gyr))
        tb0 = t - rip if t is not None else (math.floor(boil_clock(F.t - rip) * BOIL + 1e-6) + 0.5) / BOIL      # no stroke is made afresh in flight
        kt = 1.0 - seg(rip, 0.0, 0.3)
        tip = mass(F, B, seed, aa, draw, churn, w, halo * kt, edge, kt, day, tb0, warp=sh)
    else:
        tip = mass(F, B, seed, aa, draw, churn, w, halo, edge, 1.0, day, t, warp=warp if opened else None)
    # the edge of the opening: strands. The taken ones run taut from the lid into the grips and bunch there
    ka = aa
    down = float(smooth((drop - 0.80) / 0.20))
    knots = [None, None]
    if ka > 0.003 and down > 0.0 and gap is not None and (opened or left is not None or right is not None or strands is not None):
        cols = _cols(dayf)
        wpx, a_ = F.lw(6.4 * s * w, ka * down, 1.3)
        k_ = max(0.6, min(2.0, F.cam.zoom * s))
        for i, (grip, c_, sgn, gy_) in enumerate(((left, cl, -1.0, gyl), (right, cr, 1.0, gyr))):
            r_ = _strand_side(F, gap, sgn, c_, grip, sw, s, apex, ground, taut, tremble * (1.0 - seg(rip, 0.0, 0.2) if ripped else 1.0),
                              seed, 3, 3.0, 1.0 if strands is not None else 0.22)
            if r_ is None:
                continue
            P, Wd = r_[0], r_[1]
            if grip is not None and c_ > 0.0:
                knots[i] = (grip[0], gy_, c_, sgn)
            if sh is not None:                             # the strands snap and fall with the rest
                px_, py_, wm_ = sh.runs(P[..., 0], P[..., 1], None, np.arange(len(P), dtype=np.int64) * 7 + (3 if sgn > 0 else 0), slot=False)
                py_ = np.minimum(py_, ground - 2.0 * s)
                P, Wd = np.stack([px_, py_], axis=-1), Wd * wm_
            S = np.stack([(P[..., 0] - F.cam.cx) * F.cam.zoom + W / 2.0, (P[..., 1] - F.cam.cy) * F.cam.zoom + H / 2.0], axis=-1)
            path = _ribbons(S, wpx * Wd)
            lk = lit * float(smooth(c_ / 1.2)) * (1.0 - seg(rip, 0.0, 0.4) if ripped else 1.0)   # the light of the opening on each strand
            F.c.save()
            F.c.translate(1.4 * k_ + 0.3, -1.2 * k_ - 0.3)
            F.c.drawPath(path, F.paint(cols["edge"], (0.66 if not dayf else 0.4) * a_ * (1.0 - 0.6 * lk), "mid"))
            F.c.restore()
            if lk > 0.0 and not dayf:
                F.c.save()
                F.c.translate(-sgn * (1.9 * k_ + 0.4), -0.5 * k_)
                F.c.drawPath(path, F.paint(cols["lit"], 0.62 * lk * a_, "mid"))
                F.c.restore()
            F.c.drawPath(path, F.paint(cols["dark"], a_, "dense"))
        for kn in knots:                                   # the bunch in the hand: a tight knot, larger the more is held
            if kn is None:
                continue
            gx, gy_, c_, sgn = kn
            rk = s * (7.0 + 1.9 * min(c_, 12.0))
            kx, ky, kw_, krot = gx + sgn * 0.20 * rk, gy_ + 0.80 * rk, 1.0, 0.0       # (under the fist: a hand drawn over the grip does not hide it)
            if sh is not None:                             # the bunch drops out of the hand
                kx, ky, kw_, krot = sh.point(kx, ky, late=0.06)
                ky = min(ky, ground - rk)
            tangle(F, kx, ky, rk * 0.8, rk * 1.25, loops=1.6 + 0.5 * min(c_, 12.0), seed=seed + 60 + int(sgn),
                   a=ka * down * min(1.0, c_ / 0.6) * kw_, w=1.5, churn=0.0, day=dayf, halo=0.0, rot=krot)
    out = Tip(tip if tip is not None else B.root(ax), B)
    out.edges = (e_l, e_r)
    out.grips = tuple(None if k is None else (k[0], k[1]) for k in knots)
    return out


def band_shawl(neck, pel, ground: float, face: int = 1, h: float = 380.0, seed: int = 4, s: float | None = None,
               spread: float = 1.0, n: int = 56) -> Band:
    """The mass lowered onto a sitting child's shoulders: heaped on the nape behind the head, lying
    down the back to the ground and trailing a little way behind; in front it only comes over the
    shoulder and the upper arm, so that the arms, the knees and the feet stay to be seen.
    neck, pel: the figure's world joints; face +1 if it looks right; h its standing height;
    ground: world y of the floor under it. spread: how far it trails behind (1 = about half of h).
    s: the hand (default 0.46 for h = 380: small loops, pressed hard)."""
    f = 1.0 if face >= 0 else -1.0
    s = 0.46 * h / 380.0 if s is None else s
    nx, ny = float(neck[0]), float(neck[1])
    px, py = float(pel[0]), float(pel[1])
    # in a frame where the child looks to the right: X = f * (x - nx)
    PX = min(f * (px - nx), -0.02 * h)
    gy = ground - 0.004 * h
    xb = PX - (0.16 + 0.34 * spread) * h                            # the end of the trail on the ground behind
    xf = 0.10 * h                                                   # the front end, over the upper arm
    o = rnd(seed, 51) * 40.0
    ctl = A((xb, gy - 0.012 * h), (PX - (0.14 + 0.20 * spread) * h, gy - 0.075 * h), (PX - 0.185 * h, py - 0.13 * h),
            (-0.185 * h, ny - 0.01 * h), (-0.095 * h, ny - 0.165 * h), (0.02 * h, ny - 0.135 * h), (xf, ny + 0.0 * h))
    q = np.linspace(0.0, 1.0, n)
    X = xb + (xf - xb) * q
    cs = spline(ctl, 64)
    top = np.interp(X, np.maximum.accumulate(cs[:, 0]), cs[:, 1])
    top = top - 0.012 * h * (2 * vn(q * 7.0 + o, seed + 21) - 1) * np.sin(math.pi * q) ** 0.5
    # the front edge: up the back along the spine (a little behind it), then level across the upper arm
    sl = (py - ny) / max(0.02 * h, abs(-PX))                        # the spine's fall per unit forward
    edge_y = py + 0.03 * h - (X - (PX - 0.035 * h)) * sl
    bot = np.minimum(gy, np.maximum(edge_y, ny + 0.125 * h))
    bot = np.maximum(bot, top + 0.015 * h)
    x = nx + f * X
    if f < 0:
        x, top, bot = x[::-1], top[::-1], bot[::-1]
    return Band(x, top, bot, nx, s, None, ground, core=0.82, halo=0.8, w=1.6)


def shawl(F: Frame, neck, pel, ground: float, face: int = 1, h: float = 380.0, head=None, a: float = 1.0,
          seed: int = 4, s: float | None = None, spread: float = 1.0, draw=1.0, churn: float = CHURN, w: float = 1.0,
          t: float | None = None, day: bool | None = None, halo: float = 1.0, edge: float = 1.0,
          cloud: Band | None = None, settle: float = 1.0) -> Tip:
    """The scribble lying on a sitting child like a shawl (see band_shawl). Draw it AFTER the
    figure. head = (x, y, r): the head's world centre and radius (the figure's J["head"], J["R"]):
    it stays free.
    cloud, settle: the cloud (its Band, from band_cloud, where it hung) sinks until it lies on the
    head, then slides off it and gathers on the shoulders: settle 0 = that cloud exactly, 1 = the
    shawl (2 to 3 seconds; it is heavy). Returns a Tip with .band."""
    B = band_shawl(neck, pel, ground, face, h, seed, s, spread)
    if cloud is not None and settle < 1.0:
        k = max(0.0, float(settle))
        tx, ty = (head[0], head[1] - head[2]) if head is not None else (neck[0], neck[1] - 0.3 * h)
        f = 1.0 if face >= 0 else -1.0
        sink = ease(seg(k, 0.0, 0.5))
        C_ = cloud.moved(0.0, (ty + 4.0 - cloud.under(tx)) * sink)
        C_.rests = tuple(cloud.rests) + ((tx, ty + 4.0, 0.2 * h, seg(k, 0.25, 0.5)),)
        B = morph_band(C_, B, ease(seg(k, 0.34, 1.0)), pin=(tx, neck[0] - f * 0.05 * h))
    tip = mass(F, B, seed, a, draw, churn, w, halo, edge, 1.0, day, t, seq=True, avoid=[head] if head is not None else ())
    return Tip(tip if tip is not None else B.root(neck[0]), B)


# ---- thin things: strand, crossing-out, the unravelled line -------------------------------------
def _stroke(F: Frame, P, wd, col, a, grain="dense", edge=0.0, day=False, edge_col=None):
    """One ribbon along the world polyline P ((M, 2)) with screen widths wd ((M,)), pale-edged."""
    cam = F.cam
    S = cam.pts(P)[None, :, :]
    if S[0, :, 0].max() < -30 or S[0, :, 0].min() > W + 30 or S[0, :, 1].max() < -30 or S[0, :, 1].min() > H + 30:
        return
    path = _ribbons(S, np.asarray(wd, dtype=np.float64)[None, :])
    if edge > 0.0:
        k = max(0.6, min(2.0, cam.zoom))
        F.c.save()
        F.c.translate(1.4 * k + 0.3, -1.2 * k - 0.3)
        F.c.drawPath(path, F.paint(edge_col or _cols(day)["edge"], (0.62 if not day else 0.4) * edge * a, "mid"))
        F.c.restore()
    F.c.drawPath(path, F.paint(col, a, grain))


def strand_pts(p0, p1, slack: float = 0.5, seed: int = 12, tremble: float = 0.0, t: float = 0.0, n: int = 40):
    """World polyline ((n, 2)) of a strand from p0 (below: the crown, a fist) to p1 (in the mass).
    slack 0 = a straight taut line; 1 = it hangs in a lazy wave about a tenth longer than the way.
    tremble: world units of shiver at time t (a taut strand under load)."""
    p0, p1 = np.asarray(p0, dtype=np.float64), np.asarray(p1, dtype=np.float64)
    d = p1 - p0
    ln = float(np.hypot(d[0], d[1])) + 1e-9
    nx, ny = -d[1] / ln, d[0] / ln
    if ny < 0 or (abs(ny) < 0.2 and rnd(seed, 61) < 0.5):   # bow to the side that gravity (or its hand) chooses
        nx, ny = -nx, -ny
    u = np.linspace(0.0, 1.0, n)
    bell = np.sin(math.pi * u)
    o = rnd(seed, 62) * 30.0
    off = slack * ln * (0.13 * bell * (0.6 + 0.4 * np.sin(math.pi * u * 0.9 + 0.4)) + 0.045 * np.sin(2 * math.pi * 1.6 * u + o) * bell ** 0.7
                        + 0.03 * (2 * vn(u * 5.0 + o, seed) - 1) * bell)
    if tremble > 0.0:
        off = off + tremble * bell * (0.65 * np.sin(2 * math.pi * 11.0 * t + 9.0 * u + o) + 0.35 * np.sin(2 * math.pi * 6.3 * t - 5.0 * u))
    sag = slack * ln * 0.06 * bell
    return np.stack([p0[0] + d[0] * u + nx * off, p0[1] + d[1] * u + ny * off + sag], axis=1)


def strand(F: Frame, p0, p1, slack: float = 0.5, a: float = 1.0, w: float = 1.0, tremble: float = 0.0, seed: int = 12,
           draw=1.0, day: bool | None = None, t: float | None = None):
    """The thin dark strand from the child (p0: the crown, a fist) up into the mass (p1: use
    Tip.band.root(x)). slack: 1 hangs in a lazy wave .. 0 taut and straight (ease it over a few
    frames when it is pulled; ease it back when it is let go). tremble: world units of shiver, on
    the TRUE time (it acts): 2 to 5 for a strand under load. draw: 0..1 or (d0, d1), from p0.
    w: width factor (1 = 4 world units). Returns its world polyline (40 points, p0 first)."""
    day = F.day if day is None else day
    P = strand_pts(p0, p1, slack, seed, tremble, F.t if t is None else t)
    d0, d1 = (0.0, float(draw)) if not isinstance(draw, tuple) else draw
    if d1 - d0 <= 0.01 or a <= 0.003:
        return P
    n = len(P)
    uu = np.linspace(d0, d1, n)
    Q = np.stack([np.interp(uu, np.linspace(0, 1, n), P[:, 0]), np.interp(uu, np.linspace(0, 1, n), P[:, 1])], axis=1)
    z = F.cam.zoom
    wpx, aa = F.lw(4.0 * w, a, 1.4)
    prof = (0.75 + 0.35 * vn(uu * 7.0 + seed, seed + 3)) * (0.5 + 0.5 * smooth((d1 - uu) / 0.08)) * (0.6 + 0.4 * smooth((uu - d0) / 0.05))
    cols = _cols(day)
    _stroke(F, Q, wpx * prof, cols["dark"], aa, "dense", 1.25, day)
    if d1 < 0.999:
        disc(F, Q[-1, 0], Q[-1, 1], 2.4 * w, cols["tip"], 0.8 * a, None, floor=1.1)
    return P


def cross_out(F: Frame, x0, y0, x1, y1, t0: float, amp: float = 40.0, n: int = 8, seed: int = 0, a: float = 1.0,
              w: float = 1.0, dur: float = 4.0 / 30.0, off=None, day: bool | None = None, t: float | None = None):
    """A stray crossing-out: one quick angry zigzag of the black crayon along the world axis
    (x0, y0) -> (x1, y1), about `amp` world units to either side, n strokes back and forth (keep it
    at 7 or more: fewer can look like a letter).
    It is drawn on from the true time t0 in `dur` seconds (4 frames), the pale tip leading, and
    stays. off = (ta, tb): from ta to tb it is rubbed out: the line goes in the first half, a
    smeared ghost of it stays and fades over the whole span. a: pressure; w: width factor (1 = 9
    world units). Returns the world point of the tip while it is being drawn, else None."""
    t = F.t if t is None else t
    day = F.day if day is None else day
    f = 1.0 if dur <= 0 else min(1.0, max(0.0, (t - t0) / dur))
    if f <= 0.0 or a <= 0.003:
        return None
    gone = ghost = 0.0
    if off is not None:
        gone = seg(t, off[0], off[0] + 0.5 * (off[1] - off[0]))
        ghost = seg(t, off[0], off[1])
        if ghost >= 1.0:
            return None
    cols = _cols(day)
    n = max(2, int(n))
    ax_, ay_ = x1 - x0, y1 - y0
    ln = math.hypot(ax_, ay_) + 1e-9
    tx, ty = ax_ / ln, ay_ / ln
    k = np.arange(n + 1)
    side = np.where(k % 2 == 0, -1.0, 1.0) * (1.0 if rnd(seed, 70) < 0.5 else -1.0)
    al = (k + 0.55 * (htab(k, 7, seed * 31 + 3) - 0.5)) / n * 1.1 - 0.05           # no two strokes alike
    pe = side * amp * (0.62 + 0.62 * htab(k, 11, seed * 37 + 5))
    pe[0], pe[-1] = pe[0] * 0.6, pe[-1] * 0.8
    vx = x0 + ax_ * al - ty * pe + tx * 0.42 * pe
    vy = y0 + ay_ * al + tx * pe + ty * 0.42 * pe
    q = np.array([0.0, 0.07, 0.16, 0.5, 0.84, 0.93])                                # the corners are only just rounded
    P = np.stack([(vx[:-1, None] + (vx[1:, None] - vx[:-1, None]) * q[None, :]).ravel(),
                  (vy[:-1, None] + (vy[1:, None] - vy[:-1, None]) * q[None, :]).ravel()], axis=1)
    P = np.vstack([P, [[vx[-1], vy[-1]]]])
    P = P + 2.2 * w * np.stack([2 * vn(np.arange(len(P)) * 0.37, seed + 5) - 1, 2 * vn(np.arange(len(P)) * 0.37, seed + 6) - 1], axis=1)
    d = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])
    L = d[-1] * f
    m = d <= L
    if m.sum() < len(P):
        i = int(m.sum())
        r = (L - d[i - 1]) / max(1e-6, d[i] - d[i - 1])
        P = np.vstack([P[:i], P[i - 1] + (P[i] - P[i - 1]) * r])
        d = np.concatenate([d[:i], [L]])
    if len(P) < 3:
        return (float(P[-1, 0]), float(P[-1, 1]))
    wpx, aa = F.lw(9.0 * w, a, 1.5)
    u = d / max(1e-6, d[-1])
    pr = (1.15 - 0.3 * smooth(u / 0.05)) * (0.35 + 0.65 * smooth((1.0 - u) / (0.05 if f < 1.0 else 0.12)))
    pr = pr * (0.86 + 0.28 * vn(d / (30.0 * w) + seed, seed + 6))
    if ghost > 0.0:        # rubbed: a smear of pale dust, and the line dragged wide and thin
        cx_, cy_ = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
        bell = math.sin(math.pi * min(1.0, ghost * 1.1)) ** 0.7 * (1.0 - ghost) ** 0.4
        smudge(F, cx_, cy_, 0.60 * ln + amp * 0.4, amp * 1.25 + 8.0, cols["halo"] if not day else cols["mid"],
               (0.85 if not day else 0.3) * a * bell, "soft", power=1.2, rot=math.atan2(ay_, ax_))
        _stroke(F, P, wpx * pr * (1.0 + 1.3 * ghost), cols["dark"], 0.75 * aa * (1.0 - ghost) ** 0.8 * min(1.0, ghost * 4.0), "sparse", 0.0, day)
    kk = 1.0 - gone
    if kk > 0.0:
        _stroke(F, P, wpx * pr, cols["dark"], aa * kk, "dense" if kk > 0.6 else "mid", 1.0 * kk, day)
        # crumbs of crayon where the hand turned
        nv = int(np.searchsorted(d, d[-1]) // len(q))
        if nv > 0:
            j = np.arange(1, nv + 1)
            sx = vx[j] + (htab(j, 7, seed * 13) - 0.5) * 20.0 * w - ty * np.sign(pe[j]) * 8.0 * w
            sy = vy[j] + (htab(j, 11, seed * 17) - 0.5) * 20.0 * w + tx * np.sign(pe[j]) * 8.0 * w
            specks(F, sx, sy, (1.0 + 1.5 * htab(j, 13, seed)) * w, cols["dark"], 0.9 * a * kk, "dense")
    if f < 1.0:
        disc(F, P[-1, 0], P[-1, 1], 3.2 * w, cols["tip"], 0.9 * a, None, floor=1.2)
        return (float(P[-1, 0]), float(P[-1, 1]))
    return None


class Unravelled(tuple):
    """What unravel returns: (line, lying): `line` is the whole pulled-out line as a world polyline
    (from the mass, through the hand, to its free end), `lying` the part of it on the ground (from
    under the hand to the free end)."""
    line = property(lambda self: self[0])
    lying = property(lambda self: self[1])


def unravel_pts(root, hand, out: float, ground: float = 742.0, face: int = -1, seed: int = 41, slack: float = 0.0,
                s: float = 1.0, t: float = 0.0, tremble: float = 0.0):
    """Geometry of the pulled-out line (see unravel). Returns an Unravelled of world polylines."""
    hx, hy = hand
    A_ = strand_pts(hand, root, slack, seed + 1, tremble, t, 24)[::-1]             # mass -> hand
    drop = max(0.0, ground - 6.0 * s - hy)
    lie = max(0.0, out - drop)
    if out <= 1.0:
        return Unravelled((A_, A_[-1:]))
    # hand -> ground: it falls in a lazy curve to a point a little to the side
    fx = hx + face * 26.0 * s
    nd = max(4, int(min(out, drop) / (14.0 * s)) + 3)
    ud = np.linspace(0.0, min(1.0, out / max(1.0, drop)), nd)
    D = np.stack([hx + (fx - hx) * ud ** 1.6 + 5.0 * s * np.sin(ud * 5.0 + seed), hy + drop * ud], axis=1)
    if lie <= 1.0:
        return Unravelled((np.vstack([A_, D[1:]]), D[-1:]))
    # on the ground: it runs off in lazy coils (flat loops, as a line lies) from under the hand; its
    # shape is fixed in the world from that point, so more length only adds at the free end
    step = 13.0 * s
    m = np.arange(0.0, lie + step, step)
    m[-1] = lie
    o = rnd(seed, 81) * 20.0
    mm = np.arange(0.0, lie + 2 * step, step)
    rate = (0.12 + 2.5 * vn(mm / (430.0 * s) + o, seed + 3) ** 1.9) / (66.0 * s)        # here it runs straight, there it coils
    ph = np.interp(m, mm, np.concatenate([[0.0], np.cumsum(rate[:-1]) * step]))
    R = s * (26.0 + 92.0 * vn(m / (230.0 * s) + o, seed + 2) ** 1.3)
    hk = 0.26 + 0.42 * vn(m / (310.0 * s) + 2.0 * o, seed + 5)                          # some loops lie flat, some stand
    lx = fx + face * (0.44 * m + R * np.sin(ph) + 0.22 * R * np.sin(0.37 * ph + o))
    ly = ground - 8.0 * s - hk * R * (1.0 - np.cos(ph)) - 4.0 * s * vn(m / (120.0 * s), seed + 4)
    ly = np.minimum(ly, ground - 4.0 * s)
    G = np.stack([lx, ly], axis=1)
    return Unravelled((np.vstack([A_, D[1:], G[1:]]), G))


UNRAVEL_LINE = dict(w=8.5, seed=41, grain="dense", edge=0.0, wob=0.5, taper=0.5)      # how its line is drawn with chalk()


def unravel(F: Frame, root, hand, out: float, ground: float = 742.0, face: int = -1, seed: int = 41, a: float = 1.0,
            w: float = 1.0, slack: float = 0.0, s: float = 1.0, tremble: float = 0.0, day: bool | None = None,
            t: float | None = None) -> Unravelled:
    """A loose end pulled out of the mass into one long line.

    root: where it leaves the mass (Tip.band.root(x)); hand: the world point of the pulling hand;
    out: world units of line pulled out past the hand so far (ease it up on every pull: 0 before
    160.0 s, then about 500 more per pull). From the hand it falls to `ground` and runs off along
    it in lazy coils toward `face` (-1 left, +1 right; a little under half a unit of ground per unit
    of line); what already lies there never moves: new length is added at its free end, which
    carries the tip. slack: of the stretch between mass and hand (0 while pulling, up to 1 between
    pulls); tremble: its shiver on the true time. s: size of the coils (1: 70 to 220 wide).
    The line is drawn with chalk(F, P, C.GLOOM, UNRAVEL_LINE["w"] * w, a, **the rest of UNRAVEL_LINE),
    so whoever takes it over (it becomes the contour of the first hill) can go on with the very
    same stroke. Returns Unravelled(line, lying): world polylines."""
    day = F.day if day is None else day
    U = unravel_pts(root, hand, out, ground, face, seed, slack, s, F.t if t is None else t, tremble)
    if a <= 0.003:
        return U
    cols = _cols(day)
    kw = dict(UNRAVEL_LINE)
    wl = kw.pop("w") * w
    sd = kw.pop("seed")
    if not day:
        z = F.cam.zoom
        k = max(0.6, min(2.0, z)) / z
        chalk(F, U.line + (1.5 * k, -1.3 * k), cols["edge"], wl, 0.5 * a, sd, **kw)
    chalk(F, U.line, cols["dark"], wl, a, sd, **kw)
    if out > 1.0:
        disc(F, U.line[-1, 0], U.line[-1, 1], 2.6 * w, cols["tip"], 0.7 * a, None, floor=1.1)
    return U


# ---- the small tangle: the knot in a balloon, what is left at the end -----------------------------
def tangle_pts(u, seed: int):
    """Unit-space tangle: loops that keep turning their axis, about a centre that wanders a little
    (all within a radius of about 1)."""
    cx = 0.30 * (2 * vn(u * 0.21, seed) - 1)
    cy = 0.26 * (2 * vn(u * 0.19, seed + 1) - 1)
    aa = 0.42 + 0.30 * vn(u * 0.23, seed + 3)
    bb = 0.24 + 0.34 * vn(u * 0.17, seed + 4)
    rot = 2.4 * (2 * vn(u * 0.085, seed + 5) - 1)
    ex, ey = aa * np.cos(u), bb * np.sin(u)
    cr, sr = np.cos(rot), np.sin(rot)
    return np.stack([cx + ex * cr - ey * sr, cy + ex * sr + ey * cr], axis=1)


_DU = 2.0 * math.pi / 13.0


def tangle(F: Frame, x, y, rx, ry=None, loops: float = 6.0, seed: int = 11, a: float = 1.0, w: float = 1.0, draw=1.0,
           churn: float = 0.35, day: bool | None = None, t: float | None = None, halo: float = 1.0, end=None, rot: float = 0.0):
    """The small tangle: a few loops of the scribble about the world point (x, y), world radii rx,
    ry (ry default 0.8 rx). loops: 5 to 7 on a string, 10 to 14 the knot that fills a balloon.
    draw: 0..1 or (d0, d1): it scribbles itself on / is wiped away, the tip leading.
    churn: loops a second scribbled on at one end and lost at the other (on t, default F.tb).
    end = (x, y): its loose end runs out to this world point (the hand it came from, a strand).
    w: line width factor (1 = 0.085 rx). rot: the whole knot turned by this angle (radians) about
    its middle. Day skin: soft dark pencil-grey. Reads down to 30 px.
    Returns the world point of its newest end."""
    ry = 0.8 * rx if ry is None else ry
    t = F.tb if t is None else t
    day = F.day if day is None else day
    d0, d1 = (0.0, float(draw)) if not isinstance(draw, tuple) else draw
    if a <= 0.003 or d1 - d0 <= 0.01:
        return (x, y)
    cols = _cols(day)
    cam = F.cam
    z = cam.zoom
    tq = math.floor(t * BOIL + 1e-6) / BOIL
    n = max(10, int(loops * 13))
    i0 = math.floor(tq * churn * 13.0)
    i = i0 + d0 * n + (d1 - d0) * np.arange(n + 1)
    U = tangle_pts(i * _DU + seed * 37.0, seed * 17)
    if rot:
        cr_, sr_ = math.cos(rot), math.sin(rot)
        U = np.stack([U[:, 0] * cr_ - U[:, 1] * sr_, U[:, 0] * sr_ + U[:, 1] * cr_], axis=1)
    P = np.stack([x + U[:, 0] * rx, y + U[:, 1] * ry], axis=1)
    if end is not None:                                    # the first of it runs out to where it came from
        k = (1.0 - smooth(np.arange(n + 1) / (0.18 * n))) [:, None]
        P = P * (1.0 - k) + np.asarray(end, dtype=np.float64)[None, :] * k
    if not day:
        smudge(F, x, y, rx * 1.9, ry * 1.9, cols["halo"], 0.55 * a * halo * (d1 - d0), "soft", power=1.5)
    smudge(F, x, y + 0.06 * ry, rx * 0.86, ry * 0.86, cols["dark"], (0.72 if not day else 0.34) * a * (d1 - d0), "soft" if not day else "mid", power=0.9)
    wpx = max(0.085 * rx * w, 2.2 / max(z, 1e-6) * min(1.0, rx * z / 14.0)) * z
    aa = a
    if wpx < 1.3:
        aa, wpx = a * wpx / 1.3, 1.3
    uu = np.arange(n + 1) / n
    pr = (0.6 + 0.4 * smooth(uu / 0.05)) * (0.45 + 0.55 * smooth((1.0 - uu) / 0.08)) * (0.82 + 0.34 * vn(i * 0.23, seed + 9))
    S = cam.pts(P)[None, :, :]
    wd = (wpx * pr)[None, :]
    path = _ribbons(S, wd)
    c = F.c
    k_ = max(0.5, min(2.0, z * rx / 60.0))
    c.save()
    c.translate(1.2 * k_ + 0.5, -1.0 * k_ - 0.5)
    c.drawPath(path, F.paint(cols["edge"], (0.75 if not day else 0.4) * aa, "mid"))
    c.restore()
    c.drawPath(path, F.paint(cols["dark"], aa, "dense"))
    m = max(6, int(1.3 * 13))                              # its newest loop is still pale
    c.drawPath(_ribbons(S[:, -m:], np.maximum(1.1, wd[:, -m:] * 0.4)), F.paint(cols["fresh"], 0.6 * aa, "mid"))
    tipp = (float(P[-1, 0]), float(P[-1, 1]))
    if d1 < 0.999 or d0 > 0.001:
        disc(F, tipp[0], tipp[1], max(0.03 * rx, 2.2), cols["tip"], 0.85 * a, None, floor=1.1)
    return tipp


def float_at(F: Frame, hand, rise: float = 150.0, lean: float = -60.0, seed: int = 11, t: float | None = None,
             bob: float = 1.0):
    """Where the small tangle floats above the world point `hand` that holds its string: `rise`
    world units up, `lean` to the side (negative = left; when the child runs give the lean away from
    the way it runs), bobbing a little on the clock t (default F.tb: still in the silences)."""
    t = F.tb if t is None else t
    o = rnd(seed, 91) * 6.0
    dx = bob * (9.0 * math.sin(t * 0.83 + o) + 4.0 * math.sin(t * 1.9 + 2.0 * o))
    dy = bob * (7.0 * math.sin(t * 1.21 + 1.3 * o) + 3.0 * math.sin(t * 2.3 + o))
    return (hand[0] + lean + dx, hand[1] - rise + dy)


def _string_pts(x, y, hand, s: float = 1.0):
    """The string from the hand to the foot of the small tangle at (x, y): world polyline (16, 2) and the foot."""
    foot = (x + 6.0 * s, y + 36.0 * s)
    st = spline(A(hand, (hand[0] + (foot[0] - hand[0]) * 0.42 + 16 * s, hand[1] + (foot[1] - hand[1]) * 0.5 + 16 * s), foot), 16)
    return st, foot


def on_string(F: Frame, x, y, hand, t: float | None = None, s: float = 1.0, a: float = 1.0, tie: bool = False,
              seed: int = 11, day: bool | None = None, loops: float = 6.0):
    """What is left of the weight: the small tangle at the world point (x, y) on a string held at the
    world point `hand` (give (x, y) = float_at(F, hand) for the bobbing). s: size (1 = a tangle 112
    wide). tie=True: the string ends in a small bow round `hand` (tied to the armrest in the coda).
    The string is thin chalk (pencil in the day skin); the tangle is the scribble. Returns the
    world point where the string meets the tangle."""
    day = F.day if day is None else day
    col = C.PENCIL if day else C.CHALK_DIM
    st, foot = _string_pts(x, y, hand, s)
    chalk(F, st, col, 2.6 * s, 0.9 * a, 771, wob=0.8 * s, taper=0.8, edge=0.15)
    if tie:
        hx, hy = hand
        bow = spline(A((hx, hy), (hx - 13 * s, hy - 9 * s), (hx - 17 * s, hy + 3 * s), (hx, hy), (hx + 15 * s, hy - 7 * s),
                       (hx + 16 * s, hy + 5 * s), (hx, hy), (hx + 5 * s, hy + 15 * s)), 26)
        chalk(F, bow, col, 2.4 * s, 0.9 * a, 772, wob=0.5 * s, taper=0.8, edge=0.15)
    tangle(F, x, y, 56.0 * s, 42.0 * s, loops=loops, seed=seed, a=a, t=t, day=day, w=1.0)
    return foot


def wind_up(F: Frame, x, y, k: float, hand=None, r: float = REMNANT_R, s: float = 1.0, a: float = 1.0, seed: int = 4,
            t: float | None = None, day: bool | None = None, tangle_seed: int = 11, loops: float = 6.0):
    """The piece that stayed winds itself up into the small tangle (k 0..1; 3 to 4 seconds).

    k = 0 is exactly remnant(F, x, y, r); k = 1 is exactly on_string(F, x, y, hand, s=s). Between:
    a loose end of the piece comes down to the world point `hand` (k 0 .. 0.24: the child takes it);
    then stroke after stroke of the piece is pulled out of it, from its first to its last, the pale
    tip running along each as it goes, and is wound, turn upon turn, into the knot in its middle,
    which turns as it winds and comes to rest; the dark of the loose end is drawn up into the knot
    too, and what is left of it is the string. Move (x, y) yourself meanwhile, from where the piece
    rode to float_at(F, hand, ...); hand=None: no strand and no string (the knot alone).
    s: size of the tangle (1 = 112 wide). Returns where the string meets the tangle."""
    k = min(1.0, max(0.0, float(k)))
    day = F.day if day is None else day
    if k >= 1.0:
        if hand is None:
            tangle(F, x, y, 56.0 * s, 42.0 * s, loops=loops, seed=tangle_seed, a=a, t=t, day=day)
            return (x + 6.0 * s, y + 36.0 * s)
        return on_string(F, x, y, hand, t, s, a, seed=tangle_seed, day=day, loops=loops)
    kd = seg(k, 0.0, 0.24)                                 # the loose end comes down
    kw = seg(k, 0.20, 1.0)                                 # the winding
    wipe = ease(seg(kw, 0.0, 0.82))
    B = _band_remnant(x, y, r, seed, ease(seg(kw, 0.1, 0.9)), 56.0 * s)
    if wipe < 1.0:
        mass(F, B, seed, a, (wipe, 1.0), CHURN, 1.2, 1.0 - 0.6 * wipe, 1.0, 1.0, day, t, seq=True)
    wound = ease(seg(kw, 0.06, 0.96))
    foot = (x + 6.0 * s, y + 36.0 * s)
    if hand is not None:
        st, foot = _string_pts(x, y, hand, s)
        col = C.PENCIL if day else C.CHALK_DIM
        ks = seg(kw, 0.25, 0.95)                           # the dark goes up the line into the knot; the string is what it leaves
        if ks > 0.0:
            chalk(F, st, col, 2.6 * s, 0.9 * a, 771, wob=0.8 * s, taper=0.8, edge=0.15, draw=(0.0, max(0.02, ease(ks))))
        if ks < 1.0 and kd > 0.0:
            # the loose end: slack while it comes down, then along the string's own way
            u = np.linspace(0.0, 1.0, 40)
            Ps = np.stack([np.interp(u, np.linspace(0, 1, len(st)), st[:, 0]), np.interp(u, np.linspace(0, 1, len(st)), st[:, 1])], axis=1)
            slack = 1.0 - 0.8 * ease(seg(kw, 0.0, 0.5))
            Pl = strand_pts(hand, foot, slack, 12, 0.0, 0.0, 40)
            P = Ps + (Pl - Ps) * np.sin(math.pi * u)[:, None] ** 0.5 * min(1.0, slack + 0.2)
            d0, d1 = ease(ks), 1.0
            d0 = max(d0, 1.0 - ease_out(kd, 1.6))          # (it grows down from the piece toward the hand)
            if d1 - d0 > 0.02:
                uu = np.linspace(d0, d1, 40)
                Q = np.stack([np.interp(uu, u, P[:, 0]), np.interp(uu, u, P[:, 1])], axis=1)
                cols = _cols(day)
                wpx, aa = F.lw(4.0, a, 1.4)
                prof = (0.75 + 0.35 * vn(uu * 7.0 + 12, 15)) * (0.45 + 0.55 * smooth((uu - d0) / 0.06))
                _stroke(F, Q, wpx * prof, cols["dark"], aa, "dense", 1.25, day)
                if kd < 1.0 or ks > 0.0:
                    disc(F, Q[0, 0], Q[0, 1], 2.4, cols["tip"], 0.8 * a, None, floor=1.1)
    if wound > 0.0:
        spin = -2.6 * (1.0 - wound) ** 1.6                 # it turns as it winds, and comes to rest
        grow = 1.0 + 0.22 * math.sin(math.pi * wound) * (1.0 - wound)
        tangle(F, x, y, 56.0 * s * grow, 42.0 * s * grow, loops=loops, seed=tangle_seed, a=a, t=t, day=day, draw=wound,
               rot=spin, halo=wound)
    return foot


def wane(F: Frame, x, y, rx, ry, k: float, seed: int = 4, a: float = 1.0, r: float = 56.0, t: float | None = None,
         day: bool | None = None, tangle_seed: int = 11, hand=None):
    """A last cloud of radii rx, ry about (x, y) worn down to the small tangle of radius r, in one
    place: k = 0 the cloud (gloom with those numbers), k = 1 the tangle (with hand=: the tangle on
    its string, exactly on_string). First (k 0 .. 0.45) the cloud draws in to the one piece that
    stays; then that piece winds itself up (wind_up). For the film's own chain
    (curtains(rip=, stays=) -> remnant -> wind_up -> on_string) call wind_up directly."""
    k = min(1.0, max(0.0, float(k)))
    kA = seg(k, 0.0, 0.45)
    if kA >= 1.0:
        return wind_up(F, x, y, seg(k, 0.45, 1.0), hand, REMNANT_R * r / 56.0, r / 56.0, a, seed, t, day, tangle_seed)
    q = ease(kA)
    R1 = REMNANT_R * r / 56.0
    B0 = band_cloud(x, y, rx, ry, seed)
    B1 = _band_remnant(x, y, R1, seed)
    crx, cry = rx * (R1 / rx) ** q, ry * (0.5 * R1 / ry) ** q
    B = band_cloud(x, y, crx, cry, seed, s=B0.s * (B1.s / B0.s) ** q, lump=1.0 + 0.5 * q)
    B.core = 1.0 + (B1.core - 1.0) * q
    mass(F, B, seed, a, 1.0, CHURN, 1.0 + 0.2 * q, 1.0, 1.0, 1.0, day, t, seq=True)
    return (x, y)


def gloom_dust(F: Frame, x0, x1, y, fall: float = 240.0, n: int = 22, a: float = 0.5, seed: int = 77, t: float | None = None,
               band: Band | None = None, day: bool | None = None):
    """The pale dust that falls from the scribble: n specks between world x0 and x1 that leave the
    height y (or the underside of `band`), sink `fall` world units and fade, each in about four
    seconds, on the clock t (default F.tb: they hang still in the silences)."""
    t = F.tb if t is None else t
    day = F.day if day is None else day
    i = np.arange(n)
    ph = (htab(i, 11, seed + 2) + t * (0.18 + 0.14 * htab(i, 13, seed + 5))) % 1.0
    xs = x0 + htab(i, 7, seed) * (x1 - x0) + 14.0 * np.sin(ph * 5.0 + i)
    y0 = np.interp(xs, band.x, band.bot) - 12.0 if band is not None else np.full(n, float(y))
    ys = y0 + fall * ph ** 1.3
    col = (0.30, 0.28, 0.32) if day else (0.62, 0.68, 0.84)
    for lo, hi, k in ((0.0, 0.4, 1.0), (0.4, 0.75, 0.6), (0.75, 1.0, 0.25)):
        m = (ph >= lo) & (ph < hi)
        if m.any():
            specks(F, xs[m], ys[m], 1.3 + 1.5 * htab(i[m], 17, 3), col, a * k, "dense")


# =============================================================================================
# 5. the hand-offs: the scribble's state at each of hx/story.py's hand-offs, as one call
# =============================================================================================
PART_HANG = 215.0                                  # lid_for(cam, hang=PART_HANG): the lid the curtains hang from (s08, s09)
PART_GAP = ST.X5 + 180.0                           # the world x of the seam: where acting_pair.s08 opens the curtain (the opening's middle is X5 + 90)
PART_STRANDS = 8.0                                 # strands taken on either side by hand-off B8 (seven attacks, and the last pull)
THIN_PLACE = (ST.X5 + 90.0, 250.0, 0.9)            # the thin pale place of the lid at hand-off B6: (x, radius, how thin)
STRING = dict(rise=330.0, lean=110.0)              # float_at(F, hand, rise, -face * lean): the tangle over a hand at the hip
HANDOFF_GLOOM = {                                  # what handoff_gloom draws, and the world points it wants
    "B1": ("cloud", ("crown",)), "B2": ("cloud", ("crown",)), "B3": ("cloud", ("crown",)), "B4": ("cloud", ("crown",)),
    "B5": ("cloud", ("crown",)), "B6": ("lid", ("crown",)), "B7": ("high cloud", ()), "B8": ("curtains", ("left", "right")),
    "B9": ("tangle", ("hand",)), "B10": ("tangle", ("hand",)),
}


def handoff_gloom(F: Frame, name: str, crown=None, head=None, left=None, right=None, hand=None, a: float = 1.0,
                  tremble: float = 2.6, gap: float | None = None, strands=None):
    """The scribble exactly as it stands at the hand-off `name` of hx/story.py ("B1" .. "B10"): the
    call both neighbouring scene modules make at that instant (the earlier one in its last frames,
    the later one in its first), so that the frame before and the frame after are the same strokes.
    Everything comes from story.HANDOFF[name] and the hand-off's own camera (not F.cam); you give
    the points of the figures as they stand there:

    B1 .. B5  the cloud resting on the child's head, and the strand. crown = J["crown"] (world);
              head = (x, y, r) keeps the face clear (optional). gloom(*cloud, rest=crown) + strand.
    B6        the lid with its thin pale place, and the strand from the child up into it.
              crown = where the strand leaves the child (J["crown"], or the fist that holds it).
    B7        the high cloud. No points.
    B8        the two curtains parted, PART_STRANDS a side in each grip. left, right = the grips
              (world points of the hands that hold the left and the right bunch).
              tremble: the shiver of the held strands (the same value on both sides of the hand-off).
              gap, strands: only if the performance parts the curtain elsewhere than at PART_GAP:
              the world x of the seam, and the strands taken as in curtains (None: as many as fit
              between the seam and each grip, so the opening's edges are in the two hands). Both
              modules must give the same two values (the doc's last section has the recipe).
    B9, B10   the small tangle on its string. hand = the world point of the hand that holds it.

    Draw it where the form belongs in the frame: B1 .. B5 after the child; B6 and B8 before the
    figures (the strand of B6 is drawn here too: it lies behind the child); B7, B9, B10 after them.
    Returns what the form returns (a Tip with .band for B1 .. B8; the string's foot for B9, B10)."""
    st = ST.HANDOFF[name]
    cam = Cam(*st["cam"])
    kind = HANDOFF_GLOOM[name][0]
    if kind == "cloud":
        T = gloom(F, *st["cloud"], a=a, rest=(crown[0], crown[1] + 6.0, 1.0), avoid=[head] if head is not None else ())
        strand(F, crown, T.band.root(crown[0] + 40.0, 0.4), slack=0.8, a=a)
        return T
    if kind == "lid":
        T = ceiling(F, ax=ST.HANDOFF["B5"]["cloud"][0], thin=THIN_PLACE, a=a, **lid_for(cam))
        if crown is not None:
            strand(F, crown, T.band.root(crown[0] + 40.0, 0.3), slack=0.8, a=a)
        return T
    if kind == "high cloud":
        return gloom(F, *st["cloud"], a=a)
    if kind == "curtains":
        return curtains(F, ax=ST.HANDOFF["B7"]["cloud"][0], drop=1.0, gap=PART_GAP if gap is None else gap, left=left, right=right,
                        strands=strands, tremble=tremble, a=a, **lid_for(cam, hang=PART_HANG))
    face = st["child"]["face"]
    return on_string(F, *float_at(F, hand, rise=STRING["rise"], lean=-face * STRING["lean"]), hand, a=a)


# ---- kept from the prototype (the tree's leaves are scribbled with it) ----------------------------
def scribble_pts(u, seed: int):
    """Unit-space scribble: flat loops whose centre wanders inside a cloud-shaped envelope."""
    cx = 0.74 * (2 * vn(u * 0.043, seed) - 1) + 0.16 * (2 * vn(u * 0.19, seed + 9) - 1)
    cy = 0.58 * (2 * vn(u * 0.051, seed + 1) - 1) * np.sqrt(np.clip(1.0 - (0.85 * cx) ** 2, 0.05, 1.0))
    aa = 0.30 + 0.22 * vn(u * 0.13, seed + 3)
    bb = 0.07 + 0.17 * vn(u * 0.11, seed + 4)
    rot = 0.75 * (2 * vn(u * 0.027, seed + 5) - 1)
    ex, ey = aa * np.cos(u), bb * np.sin(u)
    cr, sr = np.cos(rot), np.sin(rot)
    return np.stack([cx + ex * cr - ey * sr, cy + ex * sr + ey * cr], axis=1)
