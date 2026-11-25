"""hx.chalk.hills: the hill world, in both skins.

From 175 s the land has hills. They are one long drawing (the near contour is the film's one ground
line, continued), deterministic from world x, in three layers of parallax (near, middle, far through
F.depth). Every function here draws the SAME geometry in the skin of the Frame it is given: chalk
contours and a little hatch on dark paper (night), rubbed pastel fields on warm paper at golden
hour (day). That is what the ring needs: its inside and its outside are one drawing in two skins.

The land sits where hx/story.py puts the film: flat left of HILL_X0 (4700), the first crest at
5690 under the two at hand-off B9 (X9 = 5600 and 5780), a low level shoulder at X10 = 9000.

    hills(F, rise=1.0)                 # far, middle, near, haze, grass and the ground line
    y = ground_y(x)                    # where a foot stands on the near contour (exact, cheap)
    flowers(F, 4700, 9300, 150, open_=1.0)
    tree(F, 6800)                      # stands on the land by itself
    cast_shadow(F, x, 380)             # the long shadow of something 380 tall (day skin)

The sun stands low on the RIGHT: slopes that fall away to the right are the sunward side
(C.HILL_LIT), slopes that rise to the right are the cool side (C.HILL_SHADE); shadows fall left.
"""
from __future__ import annotations

import math

import numpy as np
import skia

from .core import A, C, H, W, Frame, blob, chalk, disc, ease, fill, fit, htab, mix, path_of, rnd, rsym, seg, smooth, smudge, spline, vn
from .ground import GROUND_Y, ground_line
from ..story import HILL_X0

__all__ = ["NEAR", "MID", "FAR", "FLAT_TO", "HILL1_X", "HILL1_SPAN", "ground_y", "ground_slope", "land_curve", "layer_y",
           "layer_slope", "layer_x", "hills", "hills_back", "hills_front", "hill_rise", "hill_from_line", "tufts", "flowers",
           "flower", "bud", "ring_bloom", "tree", "home", "cast_shadow", "FLOWER_COLS"]

FLOOR = GROUND_Y                 # 742: where the land is flat
NEAR, MID, FAR = 1.0, 0.5, 0.22  # parallax factors of the three layers (F.depth)
FLAT_TO = HILL_X0                # 4700 (hx/story.py): the near land is the flat plain left of this world x
_RUNUP = 1060.0                  # the plain runs into the first hill over this stretch
_DX = 3749.5                     # where the waves sit in the film's world: the first crest is under the two at B9 (story.X9)
_DXM, _DXF = 1813.0, 797.7       # the same for the middle and the far layer (their own coordinates)
KMODULATE = skia.BlendMode.kModulate
_SEG = 1450.0                    # a far contour is drawn in stretches this long (layer units)


# --------------------------------------------------------------------------
# the land: three contours, pure functions of x (sums of sines: exact slope, no tables)
# --------------------------------------------------------------------------
def _waves(x, terms):
    """sum of a * sin((x - o) / l) and its derivative."""
    h = np.zeros_like(x)
    d = np.zeros_like(x)
    for a, l, o in terms:
        q = (x - o) / l
        h += a * np.sin(q)
        d += (a / l) * np.cos(q)
    return h, d


_NEAR = ((78.0, 410.0, 1356.0), (26.0, 197.0, 260.0), (7.0, 87.0, -108.0), (24.0, 937.0, -364.0))
_MID = ((56.0, 283.0, -620.0), (26.0, 127.0, -60.0), (9.0, 53.0, -212.0), (16.0, 811.0, 150.0))
_FAR = ((40.0, 231.0, -1180.0), (20.0, 101.0, -100.0), (7.0, 43.0, -86.0), (14.0, 677.0, 90.0))


def _near(x):
    """Height of the near land above the flat line and its derivative (both >= 0 / arrays)."""
    b, db = _waves(x - _DX, _NEAR)
    b = b + 108.0
    r = np.sqrt(b * b + 30.0 * 30.0)                   # a soft floor: valleys bottom out, never a kink
    hs, dhs = 0.5 * (b + r), 0.5 * (1.0 + b / r) * db
    u = np.clip((x - FLAT_TO) / _RUNUP, 0.0, 1.0)       # the plain runs into the first hill
    g, dg = u * u * (3.0 - 2.0 * u), 6.0 * u * (1.0 - u) / _RUNUP
    return g * hs, dg * hs + g * dhs


def _mid(x):
    h, d = _waves(x - _DXM, _MID)
    return h + 152.0, d


def _far(x):
    h, d = _waves(x - _DXF, _FAR)
    return h + 252.0, d


def ground_y(x, rise: float = 1.0):
    """World y of the near contour (the ground line) at world x: scalar in, float out; array in, array
    out. rise: 0 = the flat plain (742 everywhere), 1 = the hills. Exact: figures, shadows and flowers
    stand on it."""
    if np.ndim(x) == 0:
        return FLOOR - rise * float(_near(np.float64(x))[0])
    return FLOOR - rise * _near(np.asarray(x, dtype=np.float64))[0]


def ground_slope(x, rise: float = 1.0):
    """dy/dx of the near contour at world x (y is down: negative = the land rises to the right).
    The angle of the ground is atan(ground_slope(x))."""
    if np.ndim(x) == 0:
        return 0.0 - rise * float(_near(np.float64(x))[1])
    return 0.0 - rise * _near(np.asarray(x, dtype=np.float64))[1]


def land_curve(rise: float = 1.0):
    """The near contour as a function for ground_line(F, curve=land_curve(rise))."""
    return lambda xs: FLOOR - rise * _near(np.asarray(xs, dtype=np.float64))[0]


_LAYERFN = {NEAR: _near, MID: _mid, FAR: _far}


def layer_y(x, depth: float = MID):
    """World y (in the layer's own coordinates: use inside `with F.depth(depth):`) of the contour of
    the layer with parallax factor `depth` (NEAR, MID or FAR)."""
    fn = _LAYERFN[depth]
    if np.ndim(x) == 0:
        return FLOOR - float(fn(np.float64(x))[0])
    return FLOOR - fn(np.asarray(x, dtype=np.float64))[0]


def layer_slope(x, depth: float = MID):
    fn = _LAYERFN[depth]
    if np.ndim(x) == 0:
        return -float(fn(np.float64(x))[1])
    return -fn(np.asarray(x, dtype=np.float64))[1]


def layer_x(cam, sx: float, depth: float = MID) -> float:
    """The x, in the coordinates of the layer `depth`, that the camera `cam` shows at screen x = sx
    (to stand something on a far layer where the picture wants it)."""
    c = cam.depth(depth)
    return c.cx + (sx - W / 2.0) / c.zoom


def _first_crest():
    xs = np.arange(FLAT_TO, FLAT_TO + 2800.0, 2.0)
    h = _near(xs)[0]
    i = int(np.argmax(h[:700]))
    j = i + int(np.argmin(h[i:]))
    return float(xs[i]), float(xs[j])


HILL1_X, _HILL1_END = _first_crest()        # the crest of the first hill; the bottom of the valley behind it
HILL1_SPAN = (FLAT_TO - 60.0, _HILL1_END)   # the stretch of contour the first hill is laid down along


# --------------------------------------------------------------------------
# drawing helpers
# --------------------------------------------------------------------------
_IDX: dict = {}


def _grid_idx(nr: int, nc: int):
    key = (nr, nc)
    if key not in _IDX:
        idx = []
        for r in range(nr - 1):
            for c in range(nc - 1):
                a = r * nc + c
                idx += [a, a + nc, a + 1, a + 1, a + nc, a + nc + 1]
        _IDX[key] = idx
    return _IDX[key]


def _argb(rgb, al):
    c = np.clip(rgb * 255.0 + 0.5, 0, 255).astype(np.uint32)
    a = np.clip(al * 255.0 + 0.5, 0, 255).astype(np.uint32)
    return ((a << 24) | (c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]).ravel().tolist()


def _mesh(F: Frame, X, Y, rgb, al, grain="mid"):
    """A rubbed field: a grid of world points (nr, nc) with a colour and a pressure at every point,
    seen through the (screen-fixed) grain. One draw call."""
    S = F.cam.pts(np.stack([X.ravel(), Y.ravel()], axis=1))
    pts = [skia.Point(x, y) for x, y in S.tolist()]
    F.c.drawVertices(skia.Vertices.MakeCopy(skia.Vertices.kTriangles_VertexMode, pts, None, _argb(rgb, al),
                                            _grid_idx(*X.shape)), F.paint((1.0, 1.0, 1.0), 1.0, grain), KMODULATE)


def _polys(F: Frame, X, Y, mask=None) -> skia.Path:
    """One path of many open polylines: X, Y (n, m) world."""
    cam = F.cam
    SX = ((X - cam.cx) * cam.zoom + W / 2.0)
    SY = ((Y - cam.cy) * cam.zoom + H / 2.0)
    if mask is not None:
        SX, SY = SX[mask], SY[mask]
    p = skia.Path()
    for xs, ys in zip(SX.tolist(), SY.tolist()):
        p.moveTo(xs[0], ys[0])
        for x, y in zip(xs[1:], ys[1:]):
            p.lineTo(x, y)
    return p


def _rgb(c):
    return np.asarray(c, dtype=np.float64)


def _view(F: Frame, m: float = 60.0):
    """World x range and bottom of what the camera in force shows (grown by m screen px)."""
    l, t, r, b = F.cam.view(m)
    return l, r, t, b


def _band(xl: float, xr: float, seed: int = 0) -> skia.Path:
    """The screen between x = xl and x = xr as a path whose two edges are ragged like the strokes of
    a rubbing (or colouring) hand: scallops, never a ruled line."""
    ys = np.linspace(-40.0, H + 40.0, 56)
    zl = 52.0 * np.abs(np.sin(ys / 61.0 + 4.0 * vn(ys / 190.0, seed + 1))) + 80.0 * vn(ys / 150.0 + 3.0, seed + 2)
    zr = 52.0 * np.abs(np.sin(ys / 67.0 + 4.0 * vn(ys / 170.0, seed + 3))) + 80.0 * vn(ys / 130.0 + 9.0, seed + 4)
    L = np.stack([xl + zl, ys], axis=1)
    R = np.stack([xr - zr, ys], axis=1)[::-1]
    return path_of(np.vstack([L, R]), True)


def _rub(F: Frame, e: float, seed: int = 0, toward: float | None = None):
    """Rub out what has just been drawn into the layer opened with F.c.saveLayer(): from both ends of
    the frame toward screen x = toward, e 0..1, in the strokes of the rubbing hand (row by row, each
    as far as it happens to reach). The first pass leaves the smeared ghost of the drawing; a second
    one, a little behind it, takes the ghost away."""
    if e <= 0.0:
        return
    c = F.c
    cx = W / 2.0 if toward is None else toward
    rows = np.arange(-24.0, H + 64.0, 42.0)
    i = np.arange(len(rows))
    rows = rows + 16.0 * (htab(i, 17, seed + 6) - 0.5)
    tl = 16.0 * (htab(i, 13, seed + 5) - 0.5)
    m = 190.0

    def comb(e_, sd):
        jl = 170.0 * (vn(i * 0.31, sd + 1) - 0.5) + 90.0 * (htab(i, 7, sd + 2) - 0.5)
        jr = 170.0 * (vn(i * 0.29 + 5.0, sd + 3) - 0.5) + 90.0 * (htab(i, 11, sd + 4) - 0.5)
        xl, xr = -m + (cx + 150.0 + m) * e_, W + m - (W + m - cx + 150.0) * e_
        p = skia.Path()
        for y, a_, b_, t_ in zip(rows.tolist(), (xl + jl).tolist(), (xr - jr).tolist(), tl.tolist()):
            p.moveTo(-160.0, y - t_)
            p.lineTo(a_, y + t_)
            p.moveTo(W + 160.0, y + t_)
            p.lineTo(b_, y - t_)
        return p
    for e_, grain, sd in ((e, "soft~", seed), ((e - 0.10) / 0.90, None, seed + 40)):
        if e_ > 0.0:
            pen = F.pen((1.0, 1.0, 1.0), 72.0, 1.0, grain)
            pen.setBlendMode(skia.BlendMode.kDstOut)
            c.drawPath(comb(min(1.0, e_), sd), pen)
            pen.setBlendMode(skia.BlendMode.kSrcOver)


def _rub_layer(F: Frame, e: float) -> bool:
    """Open the sheet a layer is drawn on while it is being rubbed out (close it with _rub and
    F.c.restore()); the whole of it loses a little pressure on the way."""
    if e <= 0.0:
        F.c.save()
        return False
    lp = skia.Paint()
    lp.setAlphaf(1.0 - 0.25 * e)
    F.c.saveLayer(None, lp)
    return True


# --------------------------------------------------------------------------
# palettes: one geometry, two skins; the day skin from afternoon gold to evening
# --------------------------------------------------------------------------
def _pal(F: Frame, name: str, hour: float, lit: float):
    """Colours of one layer for the skin of F: knock (what it rubs out behind itself), base, lit,
    shade, haze (what its lower part dissolves into), line (its contour), gold and deep (accents)."""
    if F.day:
        k = float(hour)
        if name == "far":
            base = C.HILL_FAR
            li, sh = mix(base, C.SKY_LOW, 0.50), mix(mix(base, C.LILAC, 0.34), C.SHADOW, 0.16)
            haze, line = mix(C.SKY_LOW, C.CREAM, 0.50), mix(base, C.SHADOW, 0.60)
            gold, deep = mix(li, C.CREAM, 0.40), mix(sh, C.SHADOW, 0.30)
        elif name == "mid":
            base = C.HILL_MID
            li, sh = mix(base, C.HILL_LIT, 0.78), mix(base, C.HILL_SHADE, 0.70)
            haze, line = mix(C.SKY_MID, base, 0.40), mix(C.HILL_SHADE, C.PENCIL, 0.45)
            gold, deep = mix(C.HILL_LIT, C.MUSTARD, 0.28), mix(sh, C.SHADOW, 0.34)
        else:
            base, li, sh = C.HILL_NEAR, C.HILL_LIT, C.HILL_SHADE
            haze, line = mix(C.HILL_NEAR, C.HILL_SHADE, 0.50), C.PENCIL
            gold, deep = mix(C.HILL_LIT, C.MUSTARD, 0.40), mix(C.HILL_SHADE, C.SHADOW, 0.42)
        if k > 0.0:                                        # evening: the lights go to apricot, the shades to mauve
            base = mix(base, C.EVE_HI, 0.28 * k)
            li, gold = mix(li, C.EVE_MID, 0.50 * k), mix(gold, C.EVE_LOW, 0.44 * k)
            sh, deep = mix(sh, C.SHADOW, 0.44 * k), mix(deep, C.SHADOW, 0.46 * k)
            haze = mix(haze, C.EVE_LOW if name != "near" else C.SHADOW, (0.40 if name != "near" else 0.25) * k)
        return dict(knock=mix(C.DAY, base, 0.66), base=base, lit=li, shade=sh, haze=haze, line=line, gold=gold, deep=deep)
    if name == "far":
        knock = mix(C.PAPER, C.PAPER_HAZE, 0.42)
        line = C.CHALK_FAR
    elif name == "mid":
        knock = mix(C.PAPER, C.PAPER_HAZE, 0.16)
        line = C.CHALK_DIM
    else:
        knock = mix(C.PAPER, C.PAPER_DEEP, 0.34)
        line = C.CHALK_COOL
    li = mix(knock, C.MOON, 0.30 * lit)
    sh = mix(knock, C.PAPER_DEEP, 0.45)
    haze = mix(knock, C.PAPER_HAZE, 0.8) if name != "near" else mix(knock, C.PAPER_DEEP, 0.5)
    return dict(knock=knock, base=knock, lit=li, shade=sh, haze=haze, line=line, gold=mix(C.CHALK_DIM, C.MOON, 0.5 * lit),
                deep=C.CHALK_FAR)


# name: depth, height fn, mesh rows (depth below the contour), mesh column step, stroke cells
_SPEC = {
    "far": dict(depth=FAR, fn=_far, rows=(0.0, 26.0, 70.0, 150.0), cstep=70.0, cell=170.0, per=6, dmax=130.0, lens=(80.0, 190.0),
                w=11.0, seed=7100, lw=3.0, haze=0.62, lean=1.5),
    "mid": dict(depth=MID, fn=_mid, rows=(0.0, 34.0, 90.0, 190.0), cstep=70.0, cell=170.0, per=8, dmax=180.0, lens=(90.0, 230.0),
                w=15.0, seed=7200, lw=3.6, haze=0.50, lean=1.4),
    "near": dict(depth=NEAR, fn=_near, rows=(0.0, 40.0, 110.0, 240.0), cstep=80.0, cell=180.0, per=13, dmax=430.0, lens=(110.0, 300.0),
                 w=21.0, seed=7300, lw=4.2, haze=0.62, lean=1.25),
}


def _strokes(spec, yfn, sfn, x0, x1):
    """The marks of the hand that coloured a field in: short strokes that follow the slope, more of
    them near the crest, deterministic from their cell of world x. Returns X, Y (n, 6), the slope at
    each stroke, its depth below the contour, two hashes."""
    cell, per, seed = spec["cell"], spec["per"], spec["seed"]
    i0, i1 = int(math.floor(x0 / cell)) - 2, int(math.ceil(x1 / cell)) + 2
    key = (np.repeat(np.arange(i0, i1), per) * per + np.tile(np.arange(per), i1 - i0))
    u1, u2, u3, u4 = htab(key, 7, seed), htab(key, 13, seed + 71), htab(key, 29, seed + 113), htab(key, 31, seed + 17)
    xs = (np.repeat(np.arange(i0, i1), per) + u1) * cell
    d = 5.0 + spec["dmax"] * u2 ** 1.7
    L = (spec["lens"][0] + (spec["lens"][1] - spec["lens"][0]) * u3) * (1.0 + d / 500.0)
    t = np.linspace(-0.5, 0.5, 6)[None, :]
    X = xs[:, None] + L[:, None] * t
    yc = yfn(xs)
    f = 1.0 / (1.0 + d / 260.0)                           # deeper in the field the strokes lie flatter
    Y = (yc + d)[:, None] + f[:, None] * (yfn(X) - yc[:, None]) + ((u4 - 0.5) * 0.14)[:, None] * (X - xs[:, None]) \
        + (8.0 * (u3 - 0.5))[:, None] * (4.0 * t * t)
    return X, Y, sfn(xs), d, u4, htab(key, 37, seed + 29)


def _groves(F: Frame, name: str, yfn, x0: float, x1: float, pal, fade: float, avoid=None):
    """Small trees standing here and there on a far contour, alone or two or three together: they give
    the far layers their scale and make the parallax read. Day: rubbed crowns, light on the sun's
    side; night: little chalk rounds. Deterministic from the layer's x."""
    cell, R0, seed = (540.0, 21.0, 7250) if name == "mid" else (400.0, 10.0, 7150)
    i = np.arange(int(math.floor(x0 / cell)) - 1, int(math.ceil(x1 / cell)) + 1)
    i = i[htab(i, 7, seed) < 0.66]
    if not len(i):
        return
    k = np.arange(3)[None, :]
    n3 = 1 + (htab(i, 11, seed + 1) * 3).astype(int)                       # one, two or three together
    x = ((i + 0.1 + 0.8 * htab(i, 13, seed + 2)) * cell)[:, None] + (k - 1) * R0 * (1.5 + htab(i[:, None] * 3 + k, 17, seed + 3))
    R = R0 * (0.72 + 0.6 * htab(i[:, None] * 3 + k, 19, seed + 4))
    ok = (k < n3[:, None])
    if avoid is not None:
        ok &= np.abs(x - avoid) > 150.0
    x, R = x[ok], R[ok]
    if not len(x):
        return
    cam, c = F.cam, F.c
    yb = yfn(x) + 2.0
    cx_, cy_ = x + 0.12 * R, yb - 1.95 * R
    an = np.linspace(0.0, 2.0 * math.pi, 11)[None, :-1]
    rr = R[:, None] * (1.0 + 0.16 * (htab((x[:, None] * 0.37).astype(int) + np.arange(10)[None, :], 23, seed + 5) - 0.5))
    PX, PY = cx_[:, None] + rr * np.cos(an), cy_[:, None] + rr * 0.92 * np.sin(an)

    def rounds(px, py):
        p = skia.Path()
        SX, SY = cam.to_screen(px, py)
        for xs_, ys_ in zip(SX.tolist(), SY.tolist()):
            p.moveTo(xs_[0], ys_[0])
            for a_, b_ in zip(xs_[1:], ys_[1:]):
                p.lineTo(a_, b_)
            p.close()
        return p
    trunks = _polys(F, np.stack([x, x + 0.06 * R], axis=1), np.stack([yb, yb - 1.25 * R], axis=1))
    ws, ka = F.lw(max(2.0, R0 * 0.16), fade, 1.2)
    crowns = rounds(PX, PY)
    if F.day:
        col = mix(pal["shade"], pal["base"], 0.30)
        c.drawPath(trunks, F.pen(mix(pal["line"], C.PENCIL, 0.4), ws, 0.85 * ka, "mid"))
        c.drawPath(crowns, F.paint(mix(C.DAY, col, 0.7), fade if fade < 0.999 else 1.0, None))
        c.drawPath(crowns, F.paint(col, 0.95 * fade, "glow"))
        c.drawPath(rounds(cx_[:, None] + 0.26 * R[:, None] + 0.58 * rr * np.cos(an), cy_[:, None] - 0.24 * R[:, None] + 0.52 * rr * np.sin(an)),
                   F.paint(pal["gold"], 0.62 * fade, "soft"))
        c.drawPath(rounds(cx_[:, None] - 0.30 * R[:, None] + 0.52 * rr * np.cos(an), cy_[:, None] + 0.34 * R[:, None] + 0.42 * rr * np.sin(an)),
                   F.paint(pal["deep"], 0.50 * fade, "soft"))
    else:
        c.drawPath(trunks, F.pen(pal["line"], ws, 0.8 * ka, "mid"))
        c.drawPath(crowns, F.paint(pal["knock"], fade if fade < 0.999 else 1.0, None))     # (never a dark disc: black is the scribble's)
        c.drawPath(crowns, F.paint(pal["line"], 0.16 * fade, "sparse"))
        c.drawPath(crowns, F.pen(pal["line"], ws, 0.85 * ka, "mid"))


def _layer(F: Frame, name: str, hour: float, lit: float, rise: float = 1.0, on: float = 1.0, e: float = 0.0,
           contour: bool = True, a: float = 1.0, bottom_s: float | None = None, avoid=None, more=None):
    """One layer in the camera in force: knock, rubbed field, the marks of the hand, contour.
    on: 0..1 drawn on across the view from the left (the contour's tip leads, the field follows);
    e: 0..1 rubbed out from both ends of the frame; bottom_s: the screen y below which a nearer
    layer hides it anyway; more: a function drawn on the same sheet, after the field (rubbed out with it)."""
    if on <= 0.0 or e >= 1.0 or a <= 0.003:
        return
    spec = _SPEC[name]
    fn = spec["fn"]
    cam, c = F.cam, F.c
    x0, x1, _, vb = _view(F, 70.0)
    pal = _pal(F, name, hour, lit)
    day = F.day

    def yfn(x):
        return FLOOR - rise * fn(x)[0]

    def sfn(x):
        return -rise * fn(x)[1]

    cs = spec["cstep"]
    xs = np.arange(math.floor(x0 / cs), math.ceil(x1 / cs) + 1) * cs
    ys = yfn(xs)
    sl = sfn(xs)
    bot = vb if bottom_s is None else min(vb, cam.to_world(0.0, bottom_s)[1])
    rub = _rub_layer(F, e)
    if bottom_s is not None and bottom_s < H:               # (a nearer layer hides everything below this: do not pay for it)
        c.clipRect(skia.Rect.MakeLTRB(0.0, 0.0, float(W), float(bottom_s)))
    if on < 1.0:
        tip = x0 + (x1 - x0) * on                         # the contour's tip in world x
        fx = cam.to_screen(tip - (x1 - x0) * 0.07, 0.0)[0]   # the colouring-in follows the tip, its edge the hand's
        c.save()
        c.clipPath(_band(-400.0, float(fx) + 60.0, spec["seed"] + 7), skia.ClipOp.kIntersect, True)
    fade = a
    # 1. rub out what is behind
    poly = np.vstack([np.stack([xs, ys], axis=1), [(xs[-1], bot + 4.0), (xs[0], bot + 4.0)]])
    fill(F, poly, pal["knock"], fade if fade < 0.999 else 1.0)
    # 2. the rubbed field: sunward warm, the other side cool, dissolving into haze below
    # (its rows lie at fixed depths under the contour, as many as the view needs: the tone at a place in the world
    # is the same whatever the camera does, so nothing swims when the frame travels up or down)
    rows = list(spec["rows"])
    need = float(bot + 4.0 - ys.min())
    while rows[-1] < need:
        rows.append(rows[-1] * 1.7 + 60.0)
    rows = np.asarray(rows)
    nr = len(rows)
    X = np.tile(xs, (nr, 1))
    Y = ys[None, :] + rows[:, None]
    # (the light comes low from the right and a little from behind the land: down the field the lights and the
    # shades lean to the lower left, as the long shadows do; sampled along that lean they follow the form of
    # the hills and never stand as upright bands under a crest)
    sl2 = sfn(X + spec["lean"] * rows[:, None])
    wl = smooth(sl2 / 0.20)
    ws = smooth(-sl2 / 0.20)
    dn = np.minimum(rows / spec["rows"][-1], 1.0)[:, None]          # 0 at the contour .. 1 deep
    base, li, sh, hz = _rgb(pal["base"]), _rgb(pal["lit"]), _rgb(pal["shade"]), _rgb(pal["haze"])
    mod = 1.0 - (0.72 if day else 0.90) * dn ** 0.8                  # the modelling is strongest near the crest
    rgb = base[None, None, :] + (wl * mod)[..., None] * (li - base) + (ws * mod * 0.9)[..., None] * (sh - base)
    rgb = rgb + (smooth(dn * 1.1) * spec["haze"])[..., None] * (hz - rgb)
    # (rubbed tone is fixed to the screen: the smoother grain for whatever travels far and slowly, so that it does not seem to slide)
    _mesh(F, X, Y, rgb, np.full((nr, len(xs)), (0.97 if day else 0.90) * fade), "glow" if day or name == "far" else "soft")
    # 3. the marks of the hand
    SX, SY, ss, dd, uu, u5 = _strokes(spec, yfn, sfn, x0, x1)
    vis = (SY.min(axis=1) < bot + 6.0) & ((dd < 170.0) | ((uu * 7.0) % 1.0 < 0.45))     # the deep field is calmer
    z = cam.zoom
    w = spec["w"]
    if day:
        Ln = ss / 0.11 + 1.15 * (uu - 0.5)
        lm, sm = (Ln > 0.30) & vis, (Ln < -0.30) & vis
        rim = lm & (dd < 24.0)
        groups = [(lm & (u5 < 0.60) & ~rim, pal["lit"], 0.56, 1.0), (sm & (u5 < 0.60), pal["shade"], 0.50, 1.0),
                  ((lm & (u5 >= 0.60)) | rim, pal["gold"], 0.62, 0.60), (sm & (u5 >= 0.60), pal["deep"], 0.44, 0.60),
                  (~lm & ~sm & vis, mix(pal["base"], C.CREAM, 0.30), 0.30, 0.80)]
        if name == "far":
            groups = [(lm, pal["lit"], 0.52, 1.0), (sm, pal["shade"], 0.50, 1.0), (~lm & ~sm & vis, pal["gold"], 0.30, 0.7)]
        for m, col, al_, wk in groups:
            for mm, kk in (((m & (dd < 170.0), 1.0), (m & (dd >= 170.0), 0.58)) if name == "near" else ((m, 1.0),)):
                if mm.any():                                           # down the field the marks are fainter: it is calm there
                    c.drawPath(_polys(F, SX, SY, mm), F.pen(col, max(2.0, w * wk * z), al_ * kk * fade, "sparse"))
    else:
        m = (uu < 0.17) & vis                                         # a little hatch: a few long thin lines
        ws_, al_ = F.lw(2.6, 0.50 * fade, 1.2)
        dark = m if lit <= 0.0 else m & (ss <= 0.035)
        if dark.any():
            c.drawPath(_polys(F, SX, SY, dark), F.pen(pal["deep"], ws_, al_, "mid"))
        if lit > 0.0:
            m2 = (ss > 0.035) & (uu > 0.60) & vis                     # pale under the light: the same thin lines, in pale chalk
            if m2.any():
                c.drawPath(_polys(F, SX, SY, m2), F.pen(pal["gold"], ws_, al_ * 0.9 * lit, "mid"))
    if name != "near":
        _groves(F, name, yfn, x0, x1, pal, fade, avoid)
    if on < 1.0:
        c.restore()
    # 4. the contour: long hand-drawn lines, each a fixed stretch of the world (so its hand never slides)
    if contour:
        tipx = x0 + (x1 - x0) * on
        for k in range(int(math.floor(x0 / _SEG)), int(math.floor(x1 / _SEG)) + 1):
            xa, xb = k * _SEG - 34.0, (k + 1) * _SEG + 34.0
            dr = 1.0 if on >= 1.0 else min(1.0, max(0.0, (tipx - xa) / (xb - xa)))
            cx = np.linspace(xa, xb, 52)
            chalk(F, np.stack([cx, yfn(cx)], axis=1), pal["line"], spec["lw"], (0.80 if day else 0.92) * fade,
                  seed=spec["seed"] + 13 * (k % 89), wob=1.2, taper=0.75, draw=dr, edge=0.25 if day else 0.34,
                  lead=120.0 if 0.0 < dr < 1.0 else 0.0)
    if more is not None:                                   # the caller's own, on the same sheet (rubbed out with it)
        more()
    if rub:
        _rub(F, e, spec["seed"])
    c.restore()


def _low_s(F: Frame, depth: float, rise: float = 1.0) -> float:
    """Screen y of the lowest point of a layer's contour in view (what lies below it is hidden by it)."""
    cam = F.cam.depth(depth)
    l, _, r, _ = cam.view(70.0)
    hmin = float(_LAYERFN[depth](np.linspace(l, r, 28))[0].min())
    return cam.to_screen(0.0, FLOOR - (rise if depth == NEAR else 1.0) * hmin)[1] + 16.0


def _house(house):
    """house argument -> (x, depth) or (None, None)."""
    if house is None:
        return None, None
    if np.ndim(house) == 0:
        return float(house), MID
    return float(house[0]), float(house[1])


def hills_back(F: Frame, back=1.0, lit: float = 1.0, hour: float = 0.0, gone: float = 0.0, house=None, a: float = 1.0,
               rise: float = 1.0):
    """The far and the middle layer (each in its own parallax), haze between them, and the house on
    one of them. rise: the near land's (it hides their lower parts). See hills()."""
    bf, bm = (back, back) if not isinstance(back, tuple) else back
    g = float(gone)
    r = float(rise) * (1.0 - ease(seg(g, 0.40, 1.0)))
    near_s = _low_s(F, NEAR, r) if a >= 0.999 else H + 10.0      # (a see-through land hides nothing)
    mid_s = min(near_s, _low_s(F, MID)) if bm >= 1.0 and g <= 0.0 else near_s
    hx_, hd = _house(house)
    for name, d, on, e, bs in (("far", FAR, float(bf), ease(seg(g, 0.0, 0.55)), mid_s),
                               ("mid", MID, float(bm), ease(seg(g, 0.12, 0.70)), near_s)):
        mine = hx_ is not None and hd == d
        with F.depth(d):
            _layer(F, name, hour, lit, on=on, e=e, a=a, bottom_s=bs, avoid=hx_ if mine else None)
        if mine and on > 0.5:                                   # it draws itself on behind the layer's tip, and is un-drawn first
            home(F, hx_, depth=d, w=132.0 if d == MID else 96.0, a=a, hour=hour, lit=1.0, haze=0.0 if d == MID else 0.5,
                 draw=seg(on, 0.5, 1.0) * (1.0 - seg(g, 0.02, 0.36)))


def hills_front(F: Frame, rise: float = 1.0, lit: float = 1.0, hour: float = 0.0, gone: float = 0.0, grass: float = 1.0,
                line: bool = True, a: float = 1.0):
    """The near land: the field under the ground line, its grass, and the ground line itself (drawn
    with ground_line: do not draw it again). Returns the rise actually drawn. See hills()."""
    g = float(gone)
    r = float(rise) * (1.0 - ease(seg(g, 0.40, 1.0)))
    e = ease(seg(g, 0.30, 0.96))
    gr = grass * (1.0 - 0.6 * seg(g, 0.25, 0.80))
    _layer(F, "near", hour, lit, rise=r, e=e, contour=False, a=a, more=(lambda: tufts(F, rise=r, grow=gr, a=a)) if gr > 0.0 else None)
    if line:
        ground_line(F, land_curve(r) if r > 0.0 else None)
    return r


def hills(F: Frame, rise: float = 1.0, back=1.0, lit: float = 1.0, hour: float = 0.0, gone: float = 0.0, grass: float = 1.0,
          line: bool = True, house=None, a: float = 1.0) -> float:
    """The hill world, far to near, in the skin of F. World coordinates; the near contour is the
    ground line (drawn here through ground_line unless line=False).

    rise: 0 = the flat plain .. 1 = the hills (the near land only: the ground itself lifts).
    back: 0..1, the far and the middle layer draw themselves on across the view, the contour's tip
        leading (a pair (far, mid) to stagger them). They do not exist before the first hill.
    lit: night skin, 0..1: the pale light on the sunward slopes (after the sheet has ripped).
    hour: day skin, 0 = afternoon gold .. 1 = evening.
    gone: 0..1, the un-drawing at the end of the outro: far, then middle, then near are rubbed out
        from both ends of the frame, the grass sinks, the near contour flattens into the flat line.
    grass: 0..1, how far the grass has grown (0 = none). house: x of the house with the amber
        window on the middle layer (that layer's own coordinates, see layer_x), or (x, FAR) to
        stand it small on the far layer; None = no house.
    Returns the rise actually drawn (rise taken down by gone): use it for ground_y(x, r)."""
    hills_back(F, back, lit, hour, gone, house, a, rise)
    return hills_front(F, rise, lit, hour, gone, grass, line, a)


# --------------------------------------------------------------------------
# the first hill is born from a line
# --------------------------------------------------------------------------
def hill_rise(w: float) -> float:
    """The rise of the near land while the first hill is being laid down (w 0..1): flat while the
    line is pulled straight and lifted into the hill's shape, then (w 0.42 to 0.86) the ground
    swells up under the line until it carries it."""
    return ease(seg(w, 0.42, 0.86))


def _line_rise(w: float) -> float:
    """The rise of the line itself: it leads the ground (lifts off it, a little too far, and settles)."""
    return ease(seg(w, 0.24, 0.58)) * (1.0 + 0.07 * math.sin(math.pi * seg(w, 0.44, 0.80)))


def hill_from_line(F: Frame, P, w: float, col0=C.GLOOM, w0: float = 5.0, a: float = 1.0, seed: int = 4, span=None) -> float:
    """A loose line becomes the first hill. P: world polyline (N, 2) of the line as it lies (the
    loose end unravelled from the scribble, in the colour col0, w0 wide); w: 0 = the line as given,
    1 = the stretch `span` (default HILL1_SPAN) of the near contour. w 0 to 0.3: it is pulled out
    straight along the ground line (its near end first, the far end cast out last); 0.24 to 0.58:
    it lifts off the ground into the shape of the hill and hangs there, dark, a little too high;
    0.42 to 0.86: the ground swells up under it (hill_rise(w)) and takes it, and the line pales
    from col0 into the contour's own colour; from 0.86 it melts into the ground line and at 1
    nothing is left to draw. Draw the land first with rise = hill_rise(w), then this. Returns
    hill_rise(w)."""
    w = min(1.0, max(0.0, float(w)))
    r = hill_rise(w)
    if w >= 1.0 or a <= 0.003:
        return r
    xa, xb = HILL1_SPAN if span is None else span
    n = 110
    Q0 = fit(np.asarray(P, dtype=np.float64), n)
    if Q0[0, 0] > Q0[-1, 0]:
        Q0 = Q0[::-1]                                       # so that it is laid down left to right
    q = np.linspace(0.0, 1.0, n)
    tx = xa + (xb - xa) * q
    T = np.stack([tx, ground_y(tx, max(r, _line_rise(w))) - 1.0], axis=1)
    e = smooth(seg(w, 0.0, 0.30) * 1.5 - 0.5 * q)           # the near end lands first, the far end is cast out last
    Q = Q0 + (T - Q0) * e[:, None]
    Q[:, 1] -= np.sin(np.pi * e) * (22.0 + 64.0 * np.sin(np.pi * q) ** 0.8)       # it leaves the ground on its way
    k = ease(seg(w, 0.52, 0.88))
    out = 1.0 - ease(seg(w, 0.86, 1.0))
    line = F.pick(C.CHALK_COOL, C.PENCIL)
    if not F.day and k < 1.0:                               # dark on dark paper: a little pale dust round it
        chalk(F, Q, C.GLOOM_EDGE, w0 * 2.3, a * 0.42 * (1.0 - k), seed=seed + 1, wob=1.2, taper=0.6, grain="sparse", edge=0.0, step=5.0)
    # (not a mix of the two colours: black on its way to pale chalk would pass through the paper's own tone and vanish;
    # the contour's chalk comes up under the dark line while the dark is rubbed off it)
    if k > 0.0:
        chalk(F, Q, line, 4.4 + 1.6 * (1.0 - k), a * out * 0.95 * k ** 0.7, seed=seed, wob=1.0 + 0.5 * (1.0 - k), taper=0.8,
              grain="dense", edge=0.34, step=5.0)
    if k < 1.0:
        chalk(F, Q, col0, w0 * (1.0 - 0.45 * k), a * out * 0.95 * (1.0 - k), seed=seed, wob=1.0 + 0.5 * (1.0 - k), taper=0.8,
              grain="dense", edge=0.0, step=5.0)
    return r


# --------------------------------------------------------------------------
# grass
# --------------------------------------------------------------------------
def tufts(F: Frame, rise: float = 1.0, grow: float = 1.0, a: float = 1.0, t: float | None = None, seed: int = 31):
    """Grass in tufts along the near contour and, larger and fewer, down the field toward the viewer.
    Everywhere (deterministic from world x); only what the camera shows is built. grow: 0..1, the
    blades' length (they come out of the ground and sink back into it). They lean with a slow wind
    on the boil clock (t)."""
    if grow <= 0.0 or a <= 0.003:
        return
    t = F.tb if t is None else t
    x0, x1, _, vb = _view(F, 40.0)
    cell = 64.0
    i0, i1 = int(math.floor(x0 / cell)) - 1, int(math.ceil(x1 / cell)) + 1
    ii = np.arange(i0, i1)
    # two kinds: on the contour (every cell, some skipped), in the field (sparser, deeper, bigger)
    kx = np.concatenate([ii, ii + 5000, ii + 9000])
    xx = np.concatenate([(ii + htab(ii, 7, seed)) * cell, (ii + htab(ii, 11, seed + 3)) * cell, (ii + htab(ii, 5, seed + 9)) * cell])
    dep = np.concatenate([-3.0 + 9.0 * htab(ii, 13, seed + 1), 20.0 + 130.0 * htab(ii, 17, seed + 5) ** 1.3,
                          120.0 + 330.0 * htab(ii, 19, seed + 7)])
    keep = np.concatenate([htab(ii, 23, seed + 2) < 0.62, htab(ii, 29, seed + 6) < 0.55, htab(ii, 37, seed + 8) < 0.5])
    hh = (13.0 + 17.0 * htab(kx, 31, seed + 4)) * (1.0 + dep / 150.0) * grow
    yy = ground_y(xx, rise) + dep
    keep &= (yy - hh < vb + 10.0)
    xx, yy, hh, kx = xx[keep], yy[keep], hh[keep], kx[keep]
    if not len(xx):
        return
    nb = 5
    b = np.arange(nb)[None, :]
    fan = (b - (nb - 1) / 2.0) / (nb - 1)                          # -0.5 .. 0.5
    hb = htab(kx[:, None] * nb + b, 41, seed + 11)
    wind = 0.10 * np.sin(t * 1.25 + xx * 0.004)[:, None] + 0.05 * np.sin(t * 2.3 + xx * 0.011)[:, None]
    ang = fan * (1.25 + 0.5 * htab(kx, 43, seed + 12))[:, None] + 0.16 + wind       # from the vertical; the tufts lean a little right
    ln = hh[:, None] * (0.55 + 0.45 * hb) * (1.0 - 0.9 * np.abs(fan) ** 1.5)
    bx = xx[:, None] + fan * hh[:, None] * 0.34
    by = yy[:, None] + 0.0 * fan
    mx, my = bx + 0.5 * ln * np.sin(ang * 0.6), by - 0.5 * ln * np.cos(ang * 0.6)
    tx, ty = bx + ln * np.sin(ang), by - ln * np.cos(ang)
    X = np.stack([bx, mx, tx], axis=2).reshape(-1, 3)
    Y = np.stack([by, my, ty], axis=2).reshape(-1, 3)
    lightm = (hb > 0.62).ravel()
    if F.day:
        dark, light = mix(C.HILL_SHADE, C.PENCIL, 0.22), mix(C.HILL_LIT, C.HILL_NEAR, 0.25)
        al_d, al_l = 0.85, 0.9
    else:
        dark, light = C.CHALK_FAR, C.CHALK_DIM
        al_d, al_l = 0.75, 0.8
    ws, k = F.lw(2.7, a, 1.2)
    F.c.drawPath(_polys(F, X, Y, ~lightm), F.pen(dark, ws, al_d * k, "mid"))
    F.c.drawPath(_polys(F, X, Y, lightm), F.pen(light, ws, al_l * k, "mid"))


# --------------------------------------------------------------------------
# flowers
# --------------------------------------------------------------------------
FLOWER_COLS = (C.CORAL, C.MUSTARD, C.LILAC, C.CREAM)


def _flower_sites(x0, x1, n, seed, rise, depth):
    """n flowers in clusters between world x0 and x1 on the near land: x, y (root), height, colour
    index, a hash each. Sorted far to near."""
    i = np.arange(n)
    nc = max(1, n // 5)
    cl = (htab(i, 7, seed * 13 + 1) * nc).astype(int)                 # its cluster
    cx = x0 + (x1 - x0) * (cl + 0.15 + 0.7 * htab(cl, 11, seed * 13 + 2)) / nc
    cd = htab(cl, 13, seed * 13 + 3) ** 1.2
    x = cx + 95.0 * (htab(i, 17, seed * 13 + 4) + htab(i, 19, seed * 13 + 5) - 1.0)
    d = np.clip(cd + 0.30 * (htab(i, 23, seed * 13 + 6) - 0.5), 0.0, 1.0)
    dep = depth[0] + (depth[1] - depth[0]) * d
    y = ground_y(x, rise) + dep
    h = (30.0 + 16.0 * htab(i, 29, seed * 13 + 7)) * (1.0 + dep / 190.0)
    col = np.where(htab(i, 31, seed * 13 + 8) < 0.78, cl % 4, (cl + 1 + (i % 2)) % 4)
    o = np.argsort(dep, kind="stable")
    return x[o], y[o], h[o], col[o], htab(i, 37, seed * 13 + 9)[o], i[o]


def flowers(F: Frame, x0: float, x1: float, n: int = 40, seed: int = 0, open_=1.0, grow: float = 1.0, rise: float = 1.0,
            depth=(4.0, 150.0), a: float = 1.0, t: float | None = None, skip=None):
    """n flowers in clusters on the near land between world x0 and x1 (roots from depth[0] to depth[1]
    below the contour: nearer the viewer they are larger). Night skin: pale buds on pale stems; day
    skin: stems, leaves, and heads in coral, mustard, lilac and cream that open from bud (open_ = 0)
    to flower (1). open_: one number, an array of n (in the order of the arrays returned: far to
    near), or a function of the heads' world (x, y) arrays giving 0..1 (see ring_bloom). grow: 0..1,
    the stems' height (they come out of the ground; 0 = not there). skip: (xa, xb): no flower rooted
    there near the contour (where the figures stand). They nod on the boil clock (t). The same
    (x0, x1, n, seed) is always the same flowers: call it with one range for a whole scene and let
    the camera choose. Returns the heads' world (x, y) arrays."""
    if n <= 0:
        return np.zeros(0), np.zeros(0)
    t = F.tb if t is None else t
    x, y, h, ci, u, ids = _flower_sites(x0, x1, int(n), seed, rise, depth)
    h = h * max(0.0, float(grow))
    sway = 0.10 * np.sin(t * 1.5 + x * 0.006 + 6.0 * u) + 0.04 * np.sin(t * 2.7 + 17.0 * u)
    hx_, hy_ = x + h * (sway + 0.10 * (u - 0.5)), y - h
    if grow <= 0.0 or a <= 0.003:
        return hx_, hy_
    if callable(open_):
        op = np.asarray(open_(hx_, hy_), dtype=np.float64)
    else:
        op = np.broadcast_to(np.asarray(open_, dtype=np.float64), (len(x),))
    l, tp, r, b = F.cam.view(40.0)
    keep = (x > l) & (x < r) & (hy_ < b) & (y > tp)
    if skip is not None:
        keep &= ~((x > skip[0]) & (x < skip[1]) & (y - ground_y(x, rise) < 0.45 * depth[1]))
    if not keep.any():
        return hx_, hy_
    cam, c = F.cam, F.c
    z = cam.zoom
    day = F.day
    K = np.nonzero(keep)[0]
    # stems: root, a bend, the head
    mxp = x + (hx_ - x) * 0.45 + h * 0.06 * (2.0 * u - 1.0)
    SX = np.stack([x, mxp, hx_], axis=1)[K]
    SY = np.stack([y, y - h * 0.52, hy_], axis=1)[K]
    ws, k = F.lw(2.4, a, 1.1)
    stem = mix(C.HILL_SHADE, C.PENCIL, 0.30) if day else C.CHALK_FAR
    c.drawPath(_polys(F, SX, SY), F.pen(stem, ws, (0.9 if day else 0.8) * k, "mid"))
    # a leaf on every other stem
    lf = K[u[K] > 0.45]
    if len(lf):
        sgn = np.where(u[lf] > 0.72, 1.0, -1.0)
        lx0, ly0 = x[lf] + (mxp[lf] - x[lf]) * 0.6, y[lf] - h[lf] * 0.30
        LX = np.stack([lx0, lx0 + sgn * h[lf] * 0.20], axis=1)
        LY = np.stack([ly0, ly0 - h[lf] * 0.13], axis=1)
        ws2, k2 = F.lw(4.6, a, 1.4)
        c.drawPath(_polys(F, LX, LY), F.pen(mix(C.HILL_SHADE, C.HILL_NEAR, 0.4) if day else C.CHALK_FAR, ws2, (0.85 if day else 0.6) * k2, "mid"))
    # heads
    R = h * 0.21
    if not day:
        p = skia.Path()
        for sx, sy, rr in zip(*cam.to_screen(hx_[K], hy_[K]), np.maximum(1.2, R[K] * 0.42 * z)):
            p.addCircle(float(sx), float(sy), float(rr))
        c.drawPath(p, F.paint(C.CHALK_DIM, 0.9 * a, "dense"))
        return hx_, hy_
    np_ = 6
    pj = np.arange(np_)[None, :]
    for q, col in enumerate(FLOWER_COLS):
        J = K[ci[K] == q]
        if not len(J):
            continue
        o = np.clip(op[J], 0.0, 1.0)[:, None]
        pop = o + 0.18 * np.sin(np.pi * o) * o                                # a small overshoot as it opens
        # petal j: closed, they stand together above the stem; open, they stand round the middle
        up = -math.pi / 2 + (pj - (np_ - 1) / 2.0) * 0.20
        rnd_ = 2.0 * math.pi * pj / np_ + (6.0 * u[J])[:, None]
        ang = up + (rnd_ - up) * pop
        r0 = R[J][:, None] * (0.10 + 0.22 * pop)
        r1 = R[J][:, None] * (0.62 + 0.42 * pop) * (0.88 + 0.24 * htab(ids[J][:, None] * np_ + pj, 43, seed + 3))
        cxp = hx_[J][:, None]
        cyp = (hy_[J] - R[J] * 0.25 * (1.0 - o[:, 0]))[:, None]
        PX = np.stack([cxp + r0 * np.cos(ang), cxp + r1 * np.cos(ang)], axis=2).reshape(-1, 2)
        PY = np.stack([cyp + r0 * np.sin(ang), cyp + r1 * np.sin(ang)], axis=2).reshape(-1, 2)
        wpet = max(1.6, float(np.median(R[J])) * (0.34 + 0.20 * float(np.mean(pop))) * z)
        c.drawPath(_polys(F, PX, PY), F.pen(col, wpet, 0.95 * a, "dense"))
    # the middles of the open ones
    op_k = np.clip(op[K], 0.0, 1.0)
    p = skia.Path()
    any_ = False
    for sx, sy, rr, o_ in zip(*cam.to_screen(hx_[K], hy_[K]), R[K] * 0.30 * z, op_k):
        if o_ > 0.35:
            p.addCircle(float(sx), float(sy), float(max(1.0, rr * min(1.0, (o_ - 0.35) / 0.4))))
            any_ = True
    if any_:
        c.drawPath(p, F.paint(mix(C.MUSTARD, C.PENCIL, 0.35), 0.9 * a, "dense"))
    return hx_, hy_


def flower(F: Frame, x, y, h, col=None, seed: int = 0, a: float = 1.0, sway: float = 0.0, open_: float = 1.0):
    """One flower h tall growing from the world point (x, y); col: one of FLOWER_COLS (default by seed).
    Night skin: a bud."""
    ci = FLOWER_COLS.index(col) if col in FLOWER_COLS else seed % 4
    top = (x + sway * h * 0.25, y - h)
    day = F.day
    ws, k = F.lw(2.4, a, 1.1)
    S = spline(A((x, y), (x + sway * h * 0.05 + h * 0.05 * rsym(seed, 1), y - h * 0.5), top), 6)
    F.c.drawPath(F.path(S), F.pen(mix(C.HILL_SHADE, C.PENCIL, 0.30) if day else C.CHALK_FAR, ws, (0.9 if day else 0.8) * k, "mid"))
    R = h * 0.21
    if not day:
        disc(F, top[0], top[1], R * 0.42, C.CHALK_DIM, 0.9 * a, "dense", floor=1.2)
        return
    o = min(1.0, max(0.0, float(open_)))
    pop = o + 0.18 * math.sin(math.pi * o) * o
    p = skia.Path()
    for j in range(6):
        up = -math.pi / 2 + (j - 2.5) * 0.20
        an = up + (2.0 * math.pi * j / 6 + 6.0 * rnd(seed, 2) - up) * pop
        r0, r1 = R * (0.10 + 0.22 * pop), R * (0.62 + 0.42 * pop) * (0.88 + 0.24 * rnd(seed + j, 3))
        cy_ = top[1] - R * 0.25 * (1.0 - o)
        p.moveTo(*F.cam.to_screen(top[0] + r0 * math.cos(an), cy_ + r0 * math.sin(an)))
        p.lineTo(*F.cam.to_screen(top[0] + r1 * math.cos(an), cy_ + r1 * math.sin(an)))
    F.c.drawPath(p, F.pen(FLOWER_COLS[ci], max(1.6, R * (0.34 + 0.20 * pop) * F.cam.zoom), 0.95 * a, "dense"))
    if o > 0.35:
        disc(F, top[0], top[1], R * 0.30 * min(1.0, (o - 0.35) / 0.4), mix(C.MUSTARD, C.PENCIL, 0.35), 0.9 * a, "dense", floor=1.0)


def bud(F: Frame, x, y, h, seed: int = 0, a: float = 0.9, sway: float = 0.0):
    """A flower not yet open (night: a pale stem and a dot; day: a closed head)."""
    flower(F, x, y, h, None, seed, a, sway, 0.0)


def ring_bloom(F: Frame, cx: float, cy: float, radius_at, t0: float, behind: float = 46.0, every: float = 0.375,
               dur: float = 0.34, cam_at=None):
    """The opening of the flowers behind the ring's edge, for flowers(open_=...). (cx, cy): the WORLD
    point the ring opens from; radius_at(t): its radius in screen px at time t (the same function
    the scene gives ring()); t0: when it starts. A flower opens on the first eighth note (grid:
    0.265 + every * j s) at which the edge has passed it by `behind` px, and takes `dur` s to open.
    cam_at(t): the camera at time t if it moves while the ring opens (default: the camera in force).
    Returns a function of the flowers' world (x, y) arrays."""
    t = F.t
    j0 = int(math.ceil((t0 - 0.265) / every - 1e-9))
    ticks = [0.265 + every * j for j in range(j0, int(math.floor((t - 0.265) / every + 1e-9)) + 1)]

    def fn(x, y):
        x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
        t_open = np.full(x.shape, np.inf)
        for tk in ticks:
            cam = cam_at(tk) if cam_at is not None else F.cam
            sx, sy = cam.to_screen(x, y)
            ox, oy = cam.to_screen(cx, cy)
            hit = (np.hypot(sx - ox, sy - oy) < radius_at(tk) - behind) & ~np.isfinite(t_open)
            t_open[hit] = tk
        return np.clip((t - t_open) / dur, 0.0, 1.0)
    return fn


# --------------------------------------------------------------------------
# the long shadows of golden hour
# --------------------------------------------------------------------------
_SHAPES = {"figure": ((0.0, 0.42), (0.10, 0.50), (0.42, 0.78), (0.62, 0.70), (0.72, 0.40), (0.80, 0.86), (0.90, 1.00), (0.97, 0.66), (1.0, 0.0)),
           "tree": ((0.0, 0.16), (0.30, 0.20), (0.42, 0.62), (0.60, 1.0), (0.82, 0.92), (0.95, 0.52), (1.0, 0.0)),
           "plain": ((0.0, 0.6), (0.3, 1.0), (0.8, 0.8), (1.0, 0.0))}


def cast_shadow(F: Frame, x: float, h: float, hour: float = 0.0, a: float = 1.0, rise: float = 1.0, w: float | None = None,
                lift: float = 0.0, kind: str = "figure", seed: int = 0):
    """The long shadow of something h tall standing at world x on the near land: it lies on the field
    to the LEFT and toward the viewer (the sun is low on the right, in front of us), longer and
    paler as the hour goes to evening. kind: "figure" (legs, body, a round head at the far end),
    "tree" (a trunk and a crown) or "plain" (a tapering patch). w: its greatest half width (default
    0.15 h). lift: how far the thing is off the ground (a jump: the shadow lets go of the feet).
    Day skin only (the night skin draws nothing: use ground_shadow)."""
    if not F.day or a <= 0.003:
        return
    L = h * (1.35 + 1.15 * hour)
    w = h * 0.15 if w is None else w
    prof = np.asarray(_SHAPES[kind])
    q = np.linspace(0.0, 1.0, 26)
    hw = w * np.interp(q, prof[:, 0], prof[:, 1])
    xs = x - 4.0 - lift * 1.2 - L * q
    y0 = ground_y(x, rise)
    ys = y0 + 0.55 * (ground_y(xs, rise) - y0) + 3.0 + (0.24 * L + 0.10 * lift) * q
    # the outline of the patch: the shadow is foreshortened (it lies on the ground), so its width is flat
    wob = 1.0 + 0.10 * (2.0 * vn(q * 7.0 + seed, 77 + seed) - 1.0)
    up = np.stack([xs + hw * 0.22, ys - hw * 0.42 * wob], axis=1)
    dn = np.stack([xs - hw * 0.22, ys + hw * 0.42 * wob], axis=1)[::-1]
    P = np.vstack([up, dn])
    col = mix(C.SHADOW, C.HILL_SHADE, 0.36)
    al = (0.58 - 0.16 * hour) * a
    fill(F, P, col, al, "soft")
    fill(F, P, mix(col, C.PENCIL, 0.2), al * 0.40, "sparse")


# --------------------------------------------------------------------------
# the tree, the house
# --------------------------------------------------------------------------
_CLUMPS = ((-112, 30, 96, 80), (96, 44, 92, 74), (-58, -62, 104, 86), (70, -52, 108, 90), (4, -118, 96, 76), (0, 12, 122, 92))


def tree(F: Frame, x: float, y: float | None = None, t: float | None = None, seed: int = 691, s: float = 1.0, a: float = 1.0,
         hour: float = 0.0, shadow: bool = True, rise: float = 1.0):
    """One tree standing at world x on the near land (or on (x, y) if y is given), about 520 * s tall:
    a forked trunk and a crown of rubbed clumps, golden on the sun's side, cool on the other. Night
    skin: the same crown as one scalloped chalk outline. Its clumps stir on the boil clock (t).
    shadow: its long shadow on the field (day skin). Returns the crown's centre (x, y)."""
    t = F.tb if t is None else t
    y = ground_y(x, rise) + 3.0 if y is None else y
    day = F.day
    c = F.c
    if day and shadow:
        cast_shadow(F, x, 430.0 * s, hour, a * 0.8, rise, w=128.0 * s, kind="tree", seed=seed)
    pen = C.PENCIL if day else C.CHALK_DIM
    top = y - 250.0 * s
    # trunk: two sides, leaning a little, and a fork
    lx = A((x - 22 * s, y), (x - 15 * s, y - 90 * s), (x - 12 * s, y - 180 * s), (x - 34 * s, top - 30 * s))
    rx = A((x + 24 * s, y), (x + 15 * s, y - 95 * s), (x + 16 * s, y - 175 * s), (x + 44 * s, top - 10 * s))
    Ls, Rs = spline(lx, 14), spline(rx, 14)
    body = np.vstack([Ls, Rs[::-1]])
    op = 1.0 if a >= 0.999 else a
    if day:
        bark = mix(C.PENCIL, C.MUSTARD, 0.34)
        fill(F, body, mix(C.DAY, bark, 0.6), op)
        fill(F, body, bark, 0.85 * a, "soft")
        fill(F, np.vstack([spline((lx + rx) / 2 + (7 * s, 0), 14), Rs[::-1]]), mix(bark, C.SUN_HALO, 0.62), 0.66 * a, "sparse")
    else:
        fill(F, body, C.KNOCK, 0.95 * a)
        fill(F, body, C.CHALK_FAR, 0.22 * a, "sparse")
    chalk(F, Ls, pen, 4.2 * s, 0.92 * a, seed + 1, wob=1.0, taper=0.7)
    chalk(F, Rs, pen, 4.2 * s, 0.92 * a, seed + 2, wob=1.0, taper=0.7)
    chalk(F, spline(A((x + 1 * s, y - 150 * s), (x + 0 * s, y - 205 * s), (x - 8 * s, top - 40 * s)), 8), pen, 3.2 * s, 0.75 * a,
          seed + 3, wob=0.8, taper=0.4)
    # crown: clumps, back to front; the sun is on the right
    cxc, cyc = x + 6 * s, y - 360.0 * s
    cl = []
    for j, (dx, dy, rx_, ry_) in enumerate(_CLUMPS):
        st = 2.2 * math.sin(t * 1.1 + j * 1.7) * s
        cl.append((cxc + dx * s + st, cyc + dy * s + 0.5 * st, rx_ * s, ry_ * s, smooth(0.5 + dx / 240.0 - dy / 300.0)))
    blobs = [blob(bx_, by_, rx_, ry_, seed + 10 + j, 0.11, 30) for j, (bx_, by_, rx_, ry_, _) in enumerate(cl)]
    green = mix(C.HILL_SHADE, C.HILL_NEAR, 0.55)
    lit_c, deep_c = mix(C.HILL_LIT, C.MUSTARD, 0.30), mix(C.HILL_SHADE, C.SHADOW, 0.30)
    if hour > 0.0 and day:
        green, lit_c, deep_c = mix(green, C.EVE_HI, 0.2 * hour), mix(lit_c, C.EVE_MID, 0.45 * hour), mix(deep_c, C.SHADOW, 0.3 * hour)
    if day:                                            # the light is rubbed in inside the crown only
        crown = skia.Path()
        for Pb in blobs:
            crown.addPath(F.path(Pb, True))
        c.save()
        c.clipPath(crown, skia.ClipOp.kIntersect, True)
    for j, ((bx_, by_, rx_, ry_, sun_), Pb) in enumerate(zip(cl, blobs)):
        if day:
            col = mix(green, C.HILL_LIT, 0.35 * sun_)
            fill(F, Pb, mix(C.DAY, col, 0.62), op)
            fill(F, Pb, col, 0.96 * a, "glow")
            # light from the upper right, shade pooled at the lower left
            fill(F, blob(bx_ + rx_ * 0.26, by_ - ry_ * 0.30, rx_ * 0.62, ry_ * 0.56, seed + 40 + j, 0.18, 18), lit_c,
                 (0.16 + 0.30 * sun_) * a, "soft")
            fill(F, blob(bx_ - rx_ * 0.36, by_ + ry_ * 0.42, rx_ * 0.62, ry_ * 0.50, seed + 50 + j, 0.16, 18), deep_c,
                 (0.50 - 0.30 * sun_) * a, "soft")
        else:
            fill(F, Pb, C.KNOCK, 0.96 * a)
            fill(F, Pb, (0.20, 0.25, 0.39), 0.30 * a, "soft")
    if day:                                            # one soft light over the whole crown, from the sun's side
        smudge(F, cxc + 70 * s, cyc - 96 * s, 215 * s, 180 * s, lit_c, 0.52 * a, "soft", power=1.5)
        c.restore()
    # the outline: only where a clump is not inside another (one scalloped crown, not six rings)
    for j, ((bx_, by_, rx_, ry_, sun_), Pb) in enumerate(zip(cl, blobs)):
        out = np.ones(len(Pb), dtype=bool)
        for i, (ox, oy, orx, ory, _) in enumerate(cl):
            if i != j:
                out &= ((Pb[:, 0] - ox) / (orx * 0.96)) ** 2 + ((Pb[:, 1] - oy) / (ory * 0.96)) ** 2 > 1.0
        if day:                                        # by day the light side is left open: the colour ends there
            out &= (Pb[:, 0] - bx_) * 0.8 - (Pb[:, 1] - by_) < 0.25 * rx_
        idx = np.nonzero(out)[0]
        if len(idx) < 3:
            continue
        for run in np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1):
            if len(run) >= 3:
                if day:
                    chalk(F, Pb[run], mix(C.HILL_SHADE, C.PENCIL, 0.55), 3.0 * s, 0.60 * a, seed + 30 + j, wob=1.4, taper=0.3, edge=0.2)
                else:
                    chalk(F, Pb[run], C.CHALK_DIM, 3.6 * s, 0.88 * a, seed + 30 + j, wob=1.4, taper=0.5)
    # leaves: short dabs of the pastel's end, turning round the crown; light on the sun's side
    i = np.arange(64)
    ax = cxc + 172.0 * s * (2 * htab(i, 7, seed) - 1)
    ay = cyc - 30 * s + 128.0 * s * (2 * htab(i, 11, seed + 1) - 1)
    inside = ((ax - cxc) / (188 * s)) ** 2 + ((ay - cyc + 30 * s) / (142 * s)) ** 2 < 0.80
    ax, ay, i = ax[inside], ay[inside], i[inside]
    st = 2.2 * np.sin(t * 1.1 + i * 0.9) * s
    an = np.arctan2(ay - cyc + 30 * s, ax - cxc) + math.pi / 2 + 0.9 * (htab(i, 13, seed + 2) - 0.5)       # round the crown
    ln = (15.0 + 13.0 * htab(i, 17, seed + 3)) * s
    q = np.linspace(-1.0, 1.0, 3)[None, :]
    LX = ax[:, None] + st[:, None] + q * (ln * np.cos(an))[:, None] - (1 - q * q) * (5 * s * np.sin(an))[:, None]
    LY = ay[:, None] + q * (ln * np.sin(an))[:, None] + (1 - q * q) * (5 * s * np.cos(an))[:, None]
    lm = (ax - cxc) * 0.8 - (ay - cyc) > -10 * s
    ws, k = F.lw(8.0 * s, a, 1.4)
    if day:
        c.drawPath(_polys(F, LX, LY, lm), F.pen(mix(lit_c, C.CREAM, 0.30), ws, 0.58 * k, "sparse"))
        c.drawPath(_polys(F, LX, LY, ~lm), F.pen(deep_c, ws, 0.50 * k, "sparse"))
    else:
        c.drawPath(_polys(F, LX, LY, i % 3 == 0), F.pen(C.CHALK_FAR, ws * 0.42, 0.75 * k, "mid"))
    return cxc, cyc


def home(F: Frame, x: float, y: float | None = None, w: float = 132.0, depth: float = MID, a: float = 1.0, hour: float = 0.0,
         lit: float = 1.0, draw: float = 1.0, seed: int = 600, haze: float = 0.0):
    """The house with the amber window, far off: the mended house (a seam down its middle, a strip of
    amber tape across it) and the friend's house (the window is lit in both skins). It stands at x on
    the layer `depth` (that layer's own coordinates; see layer_x), w wide. Night skin: a dim chalk
    outline, the window amber with a little glow. draw: 0..1 draws it on (and, going back, un-draws
    it). haze: 0..1, paler into the distance (for one on the far layer). Returns its anchors in the
    layer's coordinates: {"x", "y", "apex", "eave_l", "eave_r", "window", "chimney"}."""
    out = {}
    with F.depth(depth):
        y = layer_y(x, depth) + 5.0 if y is None else y
        day = F.day
        h, rh = w * 0.62, w * 0.46
        l, r = x - w / 2, x + w / 2
        apex = (x + w * 0.02, y - h - rh)
        el, er = (l - w * 0.10, y - h + 4), (r + w * 0.10, y - h + 2)
        win = (x + w * 0.24, y - h * 0.56)
        out.update(x=x, y=y, apex=apex, eave_l=el, eave_r=er, window=win, chimney=(x - w * 0.24, y - h - rh * 0.78))
        if a <= 0.003 or draw <= 0.0:
            return out
        d = float(draw)
        pen = mix(C.PENCIL, C.HILL_SHADE, 0.15) if day else C.CHALK_DIM
        hz = min(1.0, max(0.0, float(haze)))                 # far off: paler, into the distance's own tone
        far_tone = mix(C.HILL_FAR, C.SKY_LOW, 0.4)
        if hz > 0.0:
            pen = mix(pen, mix(C.HILL_FAR, C.SHADOW, 0.6) if day else C.CHALK_FAR, hz)
        wall = A((l, y), (l, y - h), (r, y - h), (r, y))
        roof = A(el, apex, er)
        fa = a * seg(d, 0.35, 1.0)
        if fa > 0:
            if day:
                wc = mix(mix(C.CREAM, C.SKY_MID, 0.45 + 0.35 * hour), far_tone, 0.45 * hz)
                rc = mix(mix(C.CORAL, C.PENCIL, 0.14 + 0.1 * hour), far_tone, 0.40 * hz)
                fill(F, np.vstack([wall, wall[:1]]), mix(C.DAY, wc, 0.7), 1.0 if fa >= 0.999 else fa)
                fill(F, np.vstack([wall, wall[:1]]), wc, 0.95 * fa, "soft")
                fill(F, A((l, y), (l, y - h), (x - w * 0.04, y - h), (x - w * 0.08, y)), mix(C.ROSE, C.SHADOW, 0.45), 0.40 * fa, "soft")
                fill(F, np.vstack([roof, roof[:1]]), mix(C.DAY, rc, 0.7), 1.0 if fa >= 0.999 else fa)
                fill(F, np.vstack([roof, roof[:1]]), rc, 0.95 * fa, "soft")
                fill(F, A(apex, er, (x + w * 0.10, y - h + 3)), mix(C.CORAL, C.SUN_HALO, 0.6), 0.55 * fa, "sparse")
            else:
                fill(F, np.vstack([wall, wall[:1]]), C.KNOCK, 0.95 * fa)
                fill(F, np.vstack([roof, roof[:1]]), C.KNOCK, 0.95 * fa)
                fill(F, np.vstack([roof, roof[:1]]), C.CHALK_FAR, 0.30 * fa, "sparse")
        lw = max(2.6, w * 0.026)
        chalk(F, A((l, y), (l, y - h)), pen, lw, 0.9 * a, seed + 1, draw=seg(d, 0.0, 0.2), wob=0.6)
        chalk(F, A((r, y - h), (r, y)), pen, lw, 0.9 * a, seed + 2, draw=seg(d, 0.1, 0.3), wob=0.6)
        chalk(F, roof, pen, lw * 1.1, 0.95 * a, seed + 3, draw=seg(d, 0.2, 0.5), wob=0.7)
        chalk(F, A((l + 2, y - h + 1), (r - 2, y - h)), pen, lw * 0.8, 0.7 * a, seed + 4, draw=seg(d, 0.3, 0.5), wob=0.6)
        # chimney, and a little smoke going up (someone is home)
        ch = out["chimney"]
        chalk(F, A((ch[0] - w * 0.05, ch[1] + rh * 0.34), (ch[0] - w * 0.05, ch[1] - 6), (ch[0] + w * 0.05, ch[1] - 6),
                   (ch[0] + w * 0.05, ch[1] + rh * 0.16)), pen, lw * 0.8, 0.85 * a, seed + 5, draw=seg(d, 0.45, 0.6), wob=0.4)
        if d >= 1.0:
            q = np.linspace(0, 1, 16)
            tt = F.tb
            sx_ = ch[0] + w * (0.05 * np.sin(q * 5.0 - tt * 0.9) * (0.3 + q) + 0.16 * q * q)
            sy_ = ch[1] - 10 - w * 0.62 * q
            chalk(F, np.stack([sx_, sy_], axis=1), mix(C.CREAM, C.LILAC, 0.35) if day else C.CHALK_FAR, lw * 1.3, 0.5 * a, seed + 6,
                  wob=0.5, taper=0.2, edge=0.5, grain="sparse", boil=0.0)
        # door
        dr = A((x - w * 0.34, y), (x - w * 0.34, y - h * 0.50), (x - w * 0.16, y - h * 0.50), (x - w * 0.16, y))
        if day and fa > 0:
            fill(F, np.vstack([dr, dr[:1]]), mix(C.SEA, C.PENCIL, 0.25), 0.8 * fa, "mid")
        chalk(F, dr, pen, lw * 0.8, 0.85 * a, seed + 7, draw=seg(d, 0.5, 0.7), wob=0.4)
        # the seam where it was mended, and the tape across it
        sm = np.stack([x + w * 0.02 * np.array([0.0, 1.0, -0.8, 0.9, -0.5, 0.6, 0.0]), np.linspace(y - h - rh + 4, y, 7)], axis=1)
        chalk(F, sm, pen, lw * 0.55, 0.55 * a, seed + 8, draw=seg(d, 0.6, 0.8), wob=0.3, edge=0.1)
        ta = a * seg(d, 0.8, 1.0)
        if ta > 0:
            tp = A((x - w * 0.085, y - h * 0.270), (x + w * 0.095, y - h * 0.345), (x + w * 0.110, y - h * 0.255), (x - w * 0.070, y - h * 0.180))
            fill(F, np.vstack([tp, tp[:1]]), C.AMBER if not day else mix(C.AMBER, C.AMBER_PALE, 0.35), 0.92 * ta, "dense")
            chalk(F, np.vstack([tp, tp[:1]]), C.AMBER_DEEP, lw * 0.5, 0.8 * ta, seed + 9, wob=0.3, edge=0.0)
        # the window: lit
        ww, wh = w * 0.13, h * 0.19
        wq = A((win[0] - ww, win[1] - wh), (win[0] + ww, win[1] - wh), (win[0] + ww, win[1] + wh), (win[0] - ww, win[1] + wh),
               (win[0] - ww, win[1] - wh))
        la = a * lit * seg(d, 0.7, 0.9)
        if la > 0:
            if not day:
                smudge(F, win[0], win[1], w * 0.62, w * 0.56, C.AMBER_GLOW, 0.30 * la, "glow", additive=True, power=1.7)
            fill(F, wq, C.DAY if day else C.KNOCK, 1.0 if la >= 0.999 else la)
            fill(F, wq, C.AMBER, 0.96 * la, "dense")
            fill(F, A((win[0] - ww, win[1] - wh), (win[0] + ww, win[1] - wh), (win[0] + ww, win[1]), (win[0] - ww, win[1] + wh * 0.3)),
                 C.AMBER_PALE, 0.55 * la, "mid")
        chalk(F, wq, pen if day else C.AMBER_DEEP, lw * 0.7, 0.9 * a, seed + 10, draw=seg(d, 0.7, 0.9), wob=0.3, edge=0.15)
        chalk(F, A((win[0], win[1] - wh), (win[0], win[1] + wh)), pen if day else C.AMBER_DEEP, lw * 0.5, 0.7 * a, seed + 11,
              draw=seg(d, 0.8, 0.95), wob=0.2, edge=0.0)
    return out
