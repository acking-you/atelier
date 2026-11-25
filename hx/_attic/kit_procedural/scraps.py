"""The family picture: a child's crayon drawing (three figures holding hands, two adults and a small
one in the middle, a house, a sun, grass) on cream paper, torn so that the main tear runs through
the small middle figure; its pieces, the picture on the room wall (torn, taped), and paper birds.

Pixel art: the drawing is a handful of bold shapes in picture units (100 x 72), painted straight at
the real-pixel size it is shown at (anti-aliasing off, strokes never under one pixel, faces and
rays and hatching dropped as it gets small), cut by a fixed label map of the tear, given a pale
torn rim and a dark outline, cached as a sprite per (piece, size, rotation step, flip step) and
blitted at snapped positions. `scale` keeps its old meaning: the whole picture is 720 * scale
logical units wide. API in hx/kit/README.md.
"""
from __future__ import annotations

import functools
import math

import numpy as np
import skia

from mv.engine import prims
from mv.engine.palette import hex_rgb, mix, shade

from hx.kit import _thg_px as X
from hx.kit import look
from hx.kit.pixel import PX

H01 = prims.hash01
HS = prims.hash_sym
UW, UH = 100.0, 72.0               # picture units
PWL, PHL = 720.0, 518.4            # logical size at scale 1
N_PIECES = 12
CREAM = hex_rgb("F1E6CC")
TORN = hex_rgb("FBF7EE")
BACK = hex_rgb("D9CCB0")
OUT = hex_rgb("3A2E2A")            # the chunky outline round a piece
TAPE = hex_rgb("E9DFB4")
WAX = dict(sky=hex_rgb("6FA6D8"), sun=hex_rgb("F6C534"), ray=hex_rgb("F08A2C"),
           grass=hex_rgb("58A84A"), wall=hex_rgb("E2683C"), roof=hex_rgb("A8402F"),
           door=hex_rgb("7A4A2C"), window=hex_rgb("4F86C6"), skin=hex_rgb("F2B48C"),
           hair=hex_rgb("3A2A22"), a=hex_rgb("3A78C0"), b=hex_rgb("D9506A"),
           c=hex_rgb("F1B53A"), flower=hex_rgb("D94A8C"))

# the main tear (top to bottom), through the small figure's right side
TEAR = [(52.0, -1.0), (50.0, 7.0), (53.5, 15.0), (49.5, 24.0), (52.5, 31.0), (49.0, 38.0), (51.5, 44.0),
        (48.5, 50.0), (51.0, 56.0), (48.0, 63.0), (50.5, 73.0)]
_SEEDS_L = [(12, 14), (34, 12), (10, 46), (28, 38), (22, 64), (44, 50)]
_SEEDS_R = [(66, 12), (88, 14), (62, 42), (90, 40), (70, 64), (92, 64)]
KEPT = 5                           # the piece holding the small middle figure (seed 44, 50)
_MR = 4                            # label-map resolution, cells per picture unit


# ---------------------------------------------------------------------------------------------
# the drawing
# ---------------------------------------------------------------------------------------------
def _paint_picture(c, k: float, paper=True, faces=True):
    """The crayon drawing on canvas c, whose transform maps picture units to real pixels (k px per
    unit). Detail steps with k: rays, faces, crayon hatching and flowers appear as it grows."""
    def fp(col):
        return skia.Paint(AntiAlias=False, Color=skia.Color4f(col[0], col[1], col[2], 1.0))

    def sp(col, units, min_px=1.0):
        p = fp(col)
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(max(min_px / k, units))
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
        return p

    def poly(pts):
        path = skia.Path()
        path.addPoly([skia.Point(float(a), float(b)) for a, b in pts], True)
        return path

    def hatch(path, col, gap, salt):
        if k < 1.6:
            return
        c.save()
        c.clipPath(path, skia.ClipOp.kIntersect, False)
        b = path.getBounds()
        p = sp(shade(col, -0.07), 0.6)
        x = b.left() - b.height()
        i = 0
        while x < b.right():
            c.drawLine(x, b.bottom(), x + b.height() * 0.8, b.top(), p)
            x += gap * (0.8 + 0.4 * H01(i, salt))
            i += 1
        c.restore()

    def shape(path, col, salt, outline=True):
        c.drawPath(path, fp(col))
        hatch(path, col, 2.6, salt)
        if outline and k >= 0.55:
            c.drawPath(path, sp(shade(col, -0.16), 0.7))

    if paper:
        c.drawRect(skia.Rect.MakeLTRB(-2, -2, UW + 2, UH + 2), fp(CREAM))
    # grass along the bottom
    g = [(-2, UH + 2)] + [(UW * i / 10, 61.0 + 1.6 * HS(i, 30)) for i in range(11)] + [(UW + 2, UH + 2)]
    shape(poly(g), WAX["grass"], 31, outline=False)
    if k >= 0.9:
        for i in range(14):
            x = 3 + 94 * H01(i, 32)
            c.drawLine(x, 63.0, x + 1.2 * HS(i, 33), 58.5 + 1.5 * H01(i, 34), sp(shade(WAX["grass"], -0.12), 0.5))
    # a crayon sky along the top edge
    sky = [(-2, -2), (UW + 2, -2)] + [(UW - UW * i / 12, 5.5 + 1.8 * HS(i, 35)) for i in range(13)]
    shape(poly(sky), WAX["sky"], 36, outline=False)
    # sun, top left, with rays once there is room for them
    sun = skia.Path()
    sun.addCircle(13.0, 12.0, 6.5)
    if k >= 0.45:
        for i in range(8):
            a = 2 * math.pi * (i + 0.5) / 8
            c.drawLine(13 + math.cos(a) * 8.0, 12 + math.sin(a) * 8.0, 13 + math.cos(a) * 12.0,
                       12 + math.sin(a) * 12.0, sp(WAX["ray"], 1.1))
    shape(sun, WAX["sun"], 20)
    if k >= 0.45:
        c.drawPath(sun, sp(WAX["ray"], 0.9))
    # a cloud stroke in the sky
    if k >= 0.7:
        cl = skia.Path()
        cl.moveTo(30, 10)
        cl.quadTo(34, 4, 38, 9)
        cl.quadTo(42, 4, 46, 10)
        c.drawPath(cl, sp(WAX["sky"], 1.0))
    # house, right
    wall = poly([(76, 42), (96, 42), (96, 62), (76, 62)])
    shape(wall, WAX["wall"], 40)
    shape(poly([(73, 43), (86, 29), (99, 43)]), WAX["roof"], 41)
    c.drawRect(skia.Rect.MakeLTRB(84, 51, 89, 62), fp(WAX["door"]))
    if k >= 0.35:
        c.drawRect(skia.Rect.MakeLTRB(78.5, 45, 82.5, 49), fp(WAX["window"]))
        c.drawRect(skia.Rect.MakeLTRB(90, 45, 94, 49), fp(WAX["window"]))
    # the three figures, holding hands: A (left, blue), the small one (amber), B (right, rose)
    figs = [(29.0, 62.0, 1.0, WAX["a"], "shirt"), (47.0, 62.0, 0.68, WAX["c"], "small"),
            (66.0, 62.0, 1.0, WAX["b"], "dress")]
    hands = []
    for j, (x, fy, s, col, kind) in enumerate(figs):
        hr = 5.4 * (1.0 if s == 1.0 else 0.84)
        hy = fy - 33 * s - hr * 0.2
        top = hy + hr                                      # shoulders
        leg = sp(WAX["hair"], 1.5)
        hip = fy - 12 * s
        c.drawLine(x - 2.4 * s, hip, x - 2.8 * s, fy, leg)
        c.drawLine(x + 2.4 * s, hip, x + 2.8 * s, fy, leg)
        if kind == "dress":
            body = poly([(x - 2.8, top + 1), (x + 2.8, top + 1), (x + 8.5, hip + 2), (x - 8.5, hip + 2)])
        else:
            w0, w1 = 4.6 * s, 5.4 * s
            body = poly([(x - w0, top + 1), (x + w0, top + 1), (x + w1, hip + 1), (x - w1, hip + 1)])
        shape(body, col, 60 + j)
        arm = sp(WAX["skin"] if k >= 0.6 else col, 1.3)
        hands.append((x, top + 3.5 * s, s, arm))
        head = skia.Path()
        head.addCircle(x, hy, hr)
        shape(head, WAX["skin"], 50 + j)
        hair = skia.Path()                                  # a crayon cap of hair
        if kind == "dress":
            hair.addPoly([skia.Point(x - hr - 1.2, hy + hr * 1.1), skia.Point(x - hr - 0.6, hy - hr * 0.6),
                          skia.Point(x, hy - hr - 0.8), skia.Point(x + hr + 0.6, hy - hr * 0.6),
                          skia.Point(x + hr + 1.2, hy + hr * 1.1), skia.Point(x + hr - 1.0, hy + hr * 1.1),
                          skia.Point(x + hr - 1.2, hy - hr * 0.25), skia.Point(x - hr + 1.2, hy - hr * 0.25),
                          skia.Point(x - hr + 1.0, hy + hr * 1.1)], True)
        else:
            hair.addPoly([skia.Point(x - hr - 0.4, hy - hr * 0.1), skia.Point(x - hr * 0.6, hy - hr - 0.9),
                          skia.Point(x, hy - hr - 1.6), skia.Point(x + hr * 0.6, hy - hr - 0.9),
                          skia.Point(x + hr + 0.4, hy - hr * 0.1), skia.Point(x, hy - hr * 0.45)], True)
        c.drawPath(hair, fp(WAX["hair"]))
        if faces and hr * k >= 3.2:                         # a child's face: two dots and a smile
            d = max(0.5 / k, 0.75)
            c.drawRect(skia.Rect.MakeXYWH(x - hr * 0.42 - d / 2, hy - d / 2 + 0.3, d, d), fp(WAX["hair"]))
            c.drawRect(skia.Rect.MakeXYWH(x + hr * 0.42 - d / 2, hy - d / 2 + 0.3, d, d), fp(WAX["hair"]))
            sm = skia.Path()
            sm.moveTo(x - hr * 0.42, hy + hr * 0.42)
            sm.quadTo(x, hy + hr * 0.85, x + hr * 0.42, hy + hr * 0.42)
            c.drawPath(sm, sp(WAX["roof"], 0.5))
    # joined hands: A -> small -> B, and the two outer arms hanging
    (xa, ya, sa, pa), (xc, yc, sc, pc), (xb, yb, sb, pb) = hands
    for (x0, y0, w0), (x1, y1, w1), p in (((xa + 4.4, ya, 1), (xc - 3.2, yc + 1.5, 1), pa),
                                         ((xc + 3.2, yc + 1.5, 1), (xb - 4.4, yb, 1), pb)):
        mx, my = (x0 + x1) / 2, max(y0, y1) + 4.0
        arm = skia.Path()
        arm.moveTo(x0, y0)
        arm.quadTo(mx, my, x1, y1)
        c.drawPath(arm, p)
    c.drawLine(xa - 4.4, ya, xa - 7.5, ya + 9, pa)
    c.drawLine(xb + 4.4, yb, xb + 7.5, yb + 9, pb)
    if k >= 0.9:                                             # flowers in the grass
        for i in range(6):
            fx, fy = 4 + 92 * H01(i, 70), 65 + 5 * H01(i, 71)
            if 18 < fx < 76:
                continue
            c.drawCircle(fx, fy, 1.3, fp(WAX["flower"]))


# ---------------------------------------------------------------------------------------------
# the tear: a fixed label map at _MR cells per unit
# ---------------------------------------------------------------------------------------------
class Piece:
    """img (unused, kept for old callers: None), home (centroid offset from the picture centre,
    logical units at scale 1), size (max radius, logical at scale 1), poly (8-point unit outline),
    _cx, _cy (centroid, picture units), color (its main crayon colour)."""


_LAB: dict = {}


def _noise2(h, w, cell, salt):
    """Smooth 2-D value noise 0..1 on an (h, w) grid with `cell` cells per lattice step."""
    gy, gx = h // cell + 2, w // cell + 2
    rnd = H01(np.arange(gy * gx), salt).reshape(gy, gx)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    fx, fy = xx / cell, yy / cell
    ix, iy = fx.astype(int), fy.astype(int)
    ux, uy = fx - ix, fy - iy
    ux, uy = ux * ux * (3 - 2 * ux), uy * uy * (3 - 2 * uy)
    a = rnd[iy, ix] * (1 - ux) + rnd[iy, ix + 1] * ux
    b = rnd[iy + 1, ix] * (1 - ux) + rnd[iy + 1, ix + 1] * ux
    return a * (1 - uy) + b * uy


def _tear_x(y):
    ys = np.array([p[1] for p in TEAR])
    xs = np.array([p[0] for p in TEAR])
    return np.interp(y, ys, xs)


def _labels():
    if "lab" in _LAB:
        return _LAB
    h, w = int(UH * _MR), int(UW * _MR)
    yy, xx = (np.mgrid[0:h, 0:w].astype(np.float64) + 0.5) / _MR
    # jagged warp of the secondary tears
    nx = (_noise2(h, w, 9 * _MR, 92) - 0.5) * 8 + (_noise2(h, w, 2 * _MR, 93) - 0.5) * 2.4
    ny = (_noise2(h, w, 9 * _MR, 95) - 0.5) * 8 + (_noise2(h, w, 2 * _MR, 96) - 0.5) * 2.4
    wx, wy = xx + nx, yy + ny
    tx = _tear_x(yy) + (prims.value_noise(yy * 2.1, 97) - 0.5) * 1.2
    left = xx < tx
    lab = np.zeros((h, w), np.int32)
    for side, seeds, off in ((True, _SEEDS_L, 0), (False, _SEEDS_R, 6)):
        d = np.stack([np.hypot(wx - sx, wy - sy) for sx, sy in seeds])
        li = np.argmin(d, 0) + off
        lab = np.where(left == side, li, lab)
    _LAB["lab"] = lab
    _LAB["half"] = np.where(left, 0, 1)
    return _LAB


def _mask_image(kind: str, i: int) -> skia.Image:
    key = ("scr_mask", kind, i)

    def make():
        L = _labels()
        m = (L["lab"] == i) if kind == "piece" else ((L["half"] == i) if kind == "half" else np.ones_like(L["lab"], bool))
        return prims.mask_image((m * 255).astype(np.uint8))
    return X.memo(key, make)


_PIECES: list = []


def _main_color(i):
    """The crayon colour a piece mostly carries (for its paper bird's wing)."""
    L = _labels()["lab"]
    ys, xs = np.nonzero(L == i)
    cx, cy = xs.mean() / _MR, ys.mean() / _MR
    best, bd = WAX["c"], 1e9
    for (px_, py_), col in (((29, 45), WAX["a"]), ((47, 50), WAX["c"]), ((66, 45), WAX["b"]),
                            ((13, 12), WAX["sun"]), ((86, 48), WAX["wall"]), ((50, 66), WAX["grass"]),
                            ((40, 20), WAX["sky"]), ((86, 34), WAX["roof"])):
        d = math.hypot(cx - px_, cy - py_)
        if d < bd:
            best, bd = col, d
    return best


def _tear():
    if _PIECES:
        return _PIECES
    L = _labels()["lab"]
    for i in range(N_PIECES):
        ys, xs = np.nonzero(L == i)
        cx, cy = (xs.mean() + 0.5) / _MR, (ys.mean() + 0.5) / _MR
        dx, dy = (xs + 0.5) / _MR - cx, (ys + 0.5) / _MR - cy
        rad = np.hypot(dx, dy)
        ang = np.arctan2(dy, dx)
        pc = Piece()
        pc.img = None
        pc._cx, pc._cy = cx, cy
        pc.size = float(rad.max()) * PWL / UW
        pc.home = ((cx - UW / 2) * PWL / UW, (cy - UH / 2) * PWL / UW)
        pc.bbox = ((xs.min()) / _MR, (ys.min()) / _MR, (xs.max() + 1) / _MR, (ys.max() + 1) / _MR)
        poly = []
        r0 = float(rad.max())
        for kk in range(8):
            a0 = -math.pi + 2 * math.pi * kk / 8
            m = np.abs(((ang - a0 + math.pi) % (2 * math.pi)) - math.pi) < math.pi / 8
            rr = rad[m].max() if m.any() else 1.0
            poly.append((math.cos(a0) * rr / r0, math.sin(a0) * rr / r0))
        pc.poly = np.array(poly)
        pc.color = _main_color(i)
        _PIECES.append(pc)
    return _PIECES


def piece(i: int):
    """Piece i (0..11): .home (centroid offset from the picture's centre, logical units at scale 1),
    .size (max radius, logical at scale 1), .poly (8-point unit outline), .color (main crayon
    colour). Piece KEPT holds the small middle figure."""
    return _tear()[i % N_PIECES]


# ---------------------------------------------------------------------------------------------
# rendering a region (a piece, a half, the whole sheet) at pixel size
# ---------------------------------------------------------------------------------------------
def _region_center(kind, i):
    if kind == "piece":
        pc = piece(i)
        return pc._cx, pc._cy, pc.bbox
    if kind == "half":
        L = _labels()["half"]
        ys, xs = np.nonzero(L == i)
        return (xs.mean() + 0.5) / _MR, (ys.mean() + 0.5) / _MR, (xs.min() / _MR, ys.min() / _MR,
                                                                  (xs.max() + 1) / _MR, (ys.max() + 1) / _MR)
    return UW / 2, UH / 2, (0.0, 0.0, UW, UH)


def _render(kind: str, i: int, k: float, rot_q: int, flip_q: int, mode: str = "front"):
    """RGBA float + origin of region (kind, i) at k px per unit, rotated rot_q * 6 degrees, squashed
    across by flip_q / 8 (negative: the blank back). mode 'front' | 'mask' (shadow) | 'drawing'
    (returns mask and drawing-ink mask too, for the loom manner)."""
    cx, cy, (x0, y0, x1, y1) = _region_center(kind, i)
    rad = math.hypot(max(cx - x0, x1 - cx), max(cy - y0, y1 - cy)) * k
    n = int(2 * rad) + 8
    ox = oy = n // 2
    fx = flip_q / 8.0

    def setup(c):
        c.translate(ox, oy)
        c.rotate(rot_q * 6.0)
        c.scale(k * max(0.125, abs(fx)), k)
        c.translate(-cx, -cy)

    arr = np.zeros((n, n, 4), np.uint8)
    surf = skia.Surface(arr)
    c = surf.getCanvas()
    c.save()
    setup(c)
    _paint_picture(c, k * max(0.4, abs(fx)), faces=(mode != "drawing"))
    c.restore()
    surf.flushAndSubmit()
    marr = np.zeros((n, n, 4), np.uint8)
    ms = skia.Surface(marr)
    mc = ms.getCanvas()
    setup(mc)
    mc.scale(1.0 / _MR, 1.0 / _MR)
    mc.drawImage(_mask_image(kind, i), 0, 0, X.NEAREST, skia.Paint(Color=skia.ColorWHITE))
    ms.flushAndSubmit()
    mask = marr[..., 3] > 127
    pic = arr[..., :3].astype(np.float32) / 255.0
    out = X.rgba(n, n)
    if mode == "mask":
        X.put(out, X.dilate(mask), (0, 0, 0))
        return out, ox, oy, None
    if fx < 0:
        X.put(out, mask, BACK)
    else:
        out[mask, :3] = pic[mask]
        out[mask, 3] = 1.0
    ink = None
    if mode == "drawing":
        cr = np.array(CREAM, np.float32)
        ink = mask & (np.abs(pic - cr).sum(-1) > 0.12)
    if k * UW >= 40 and kind != "whole":                    # the pale torn rim
        rim = mask & ~X.erode(mask)
        X.put(out, rim, TORN if fx >= 0 else shade(BACK, 0.06))
        if ink is not None:
            ink &= ~rim
    X.put(out, X.dilate(mask) & ~mask, OUT)
    if mode == "drawing":
        return out, ox, oy, (mask, ink)
    return out, ox, oy, None


def _q_rot(rot: float) -> int:
    return int(round(rot / 6.0)) % 60


def _q_flip(flip: float) -> int:
    f = max(-1.0, min(1.0, flip))
    q = int(round(f * 8))
    if q == 0:
        q = 1 if f >= 0 else -1
    return q


def _k_of(scale: float) -> float:
    """px per picture unit for a picture `scale` (720 * scale logical wide), stepped to whole px."""
    wpx = max(8, int(round(PWL * scale / PX)))
    return wpx / UW


def _sprite(kind, i, scale, rot=0.0, flip=1.0, mode="front"):
    k = _k_of(scale)
    rq, fq = _q_rot(rot), _q_flip(flip)
    key = ("scr", kind, i, round(k * UW), rq, fq, mode)

    def make():
        out, ox, oy, _ = _render(kind, i, k, rq, fq, mode)
        return X.Sprite(out, ox, oy)
    return X.memo(key, make)


# ---------------------------------------------------------------------------------------------
# public: pieces
# ---------------------------------------------------------------------------------------------
def draw_piece(canvas, i: int, x: float, y: float, scale: float = 1.0, rot: float = 0.0, alpha: float = 1.0,
               flip: float = 1.0, shadow: float = 0.3, lift: float = 8.0):
    """Piece i with its centroid at (x, y), rotated `rot` degrees (6-degree steps). flip -1..1
    squashes it across in eight steps (a tumble); below 0 its blank back shows. shadow is the alpha
    of a flat ink copy offset by lift (whole pixels)."""
    i = i % N_PIECES
    if shadow > 0 and lift > 0:
        X.blit(canvas, _sprite("piece", i, scale, rot, flip, "mask"), x + max(PX, lift * scale * 0.6),
               y + max(PX, lift * scale), shadow * alpha * 0.8)
    X.blit(canvas, _sprite("piece", i, scale, rot, flip), x, y, alpha)


def draw_kept(canvas, x: float, y: float, scale: float = 0.3, rot: float = 0.0, alpha: float = 1.0,
              flip: float = 1.0, shadow: float = 0.0, lift: float = 8.0):
    """The kept piece (KEPT: the one with the small middle figure) on its own."""
    draw_piece(canvas, KEPT, x, y, scale, rot, alpha, flip, shadow, lift)


def drifting(canvas, t: float, rect, n: int = 12, seed: int = 0, scale: float = 0.35, alpha: float = 1.0,
             speed: float = 30.0, tumble: float = 1.0):
    """n pieces drifting through rect (l, t, r, b): slow travel with the wind (speed units/s), a bob
    and a slow stepped tumble. Positions from seed and t; they wrap within the rect."""
    l, tp, r, b = rect
    ids = np.arange(n) + seed * 53
    for i in ids:
        sp = speed * (0.6 + 0.8 * H01(i, 110))
        x = l + (H01(i, 111) * (r - l) + sp * t) % (r - l)
        y = tp + (b - tp) * (0.15 + 0.7 * H01(i, 112)) + 30 * math.sin(t * (0.5 + 0.4 * H01(i, 113)) + 6.28 * H01(i, 114))
        rot = 30 * HS(i, 115) + 25 * math.sin(t * 0.4 * (0.5 + H01(i, 116)) + i)
        flip = math.cos(t * tumble * (0.5 + 0.7 * H01(i, 117)) + 6.28 * H01(i, 118))
        draw_piece(canvas, int(i) % N_PIECES, x, y, scale * (0.8 + 0.4 * H01(i, 119)), rot, alpha, flip, 0.18, 14)


def assembled(canvas, cx: float, cy: float, scale: float = 0.5, fit: float = 0.8, t: float = 0.0, seed: int = 0,
              alpha: float = 1.0, rot: float = 0.0):
    """The pieces laid out as the picture around (cx, cy). fit 0..1 brings them together but never
    closes it: at fit 1 every piece still stands at least a pixel off its place (the dark outlines
    and a line of ground show between them), two pieces stay farther out, and now and then one
    shifts by a pixel."""
    pcs = _tear()
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    k = _k_of(scale)
    s_l = k * UW * PX / PWL                                  # logical per logical-at-scale-1, stepped
    for i, pc in enumerate(pcs):
        hx, hy = pc.home
        ln = math.hypot(hx, hy) + 1e-6
        gap = 2.2 * PX / s_l + (1 - fit) * 0.45 * ln          # never under about two pixels
        ox = hx / ln * gap + HS(i, 120 + seed) * (1 - fit) * 60
        oy = hy / ln * gap + HS(i, 121 + seed) * (1 - fit) * 60
        if i in (3, 8):
            ox += hx / ln * 18
            oy += hy / ln * 18
        px_, py_ = hx + ox, hy + oy
        x = cx + (px_ * cr - py_ * sr) * s_l
        y = cy + (px_ * sr + py_ * cr) * s_l
        if H01(int(t * 1.5) * 13 + i, 124 + seed) > 0.92:     # an occasional one-pixel shift
            y += PX
        twist = HS(i, 122 + seed) * (1.5 + 25 * (1 - fit))
        draw_piece(canvas, i, x, y, scale, rot + twist, alpha, 1.0, 0.25, 6)


def armful(canvas, x: float, y: float, scale: float = 0.22, t: float = 0.0, seed: int = 0, n: int = 12,
           spread: float = 1.0, alpha: float = 1.0):
    """The pieces held as an armful around (x, y): bunched, overlapping, tilted; they breathe by a
    pixel."""
    ids = list(range(n))
    ids.sort(key=lambda i: H01(i, 130 + seed))
    for i in ids:
        a = 6.283 * H01(i, 131 + seed)
        rr = (0.25 + 0.75 * H01(i, 132 + seed) ** 0.7) * 140 * scale * spread
        px_ = x + math.cos(a) * rr * 1.25
        py_ = y + math.sin(a) * rr * 0.7 + (PX if math.sin(t * 1.6 + i) > 0.6 else 0)
        draw_piece(canvas, i % N_PIECES, px_, py_, scale, 70 * HS(i, 133 + seed), alpha, 1.0, 0.3, 4)


def shard(canvas, i: int, x: float, y: float, h: float, manner: str = "loom", tones=None, alpha: float = 1.0,
          dissolve: float = 0.22, flip: float = 1.0, lean: float = 0.0, light=None):
    """Piece i standing upright on its base (x, y) as a shard about h logical units tall (the
    standing shards of the first two choruses). manner "loom": a flat silhouette in three mist
    tones (`tones` top to bottom; default mist), darker at the top, stippled into the mist at its
    base, the crayon drawing kept only as a lifted tone (its identity). "thing": the piece itself.
    lean: degrees."""
    pc = piece(i)
    x0, y0, x1, y1 = pc.bbox
    span = max(x1 - x0, y1 - y0)
    scale = h / (span * PWL / UW)
    rq, fq = _q_rot(lean + (90.0 if (x1 - x0) > (y1 - y0) * 1.15 else 0.0)), _q_flip(flip)
    k = _k_of(scale)
    tones = tones or loom_tones()
    key = ("shard", i, round(k * UW), rq, fq, manner, tuple(X.qc(c) for c in tones), round(dissolve, 2))

    def make():
        out, ox, oy, extra = _render("piece", i, k, rq, fq, "drawing" if manner == "loom" else "front")
        if manner == "loom":
            mask, ink = extra
            mask = out[..., 3] > 0
            out = X.loom_colorize(mask, tones, ink, dissolve=dissolve, light=light, id_lift=0.22)
        rows = np.nonzero(out[..., 3].any(1))[0]
        bot = (rows[-1] + 1) if len(rows) else oy
        return X.Sprite(out, ox, bot)
    sp = X.memo(key, make)
    X.blit(canvas, sp, x, y, alpha)


def loom_tones(depth: float = 0.6):
    """Default mist tones (top, middle, base) for a looming shape at depth 0 (far, pale) .. 1 (near)."""
    return _loom_tones(round(float(depth), 2))


@functools.lru_cache(maxsize=256)
def _loom_tones(depth: float):
    far = mix(look.FOG_PALE, look.FOG, 0.6)
    near = mix(look.FOG, look.FOG_DEEP, 0.7)
    base = mix(far, near, depth)
    return (shade(base, -0.07), base, mix(base, look.FOG_PALE, 0.30))


# ---------------------------------------------------------------------------------------------
# public: the picture whole, on the wall
# ---------------------------------------------------------------------------------------------
def whole(canvas, x: float, y: float, w: float, alpha: float = 1.0, rot: float = 0.0):
    """The picture untorn, centred on (x, y), w logical units wide."""
    X.blit(canvas, _sprite("whole", 0, w / PWL, rot, 1.0), x, y, alpha)


def on_wall(canvas, x: float, y: float, w: float, state: str = "torn", t: float = 0.0, alpha: float = 1.0,
            seed: int = 0):
    """The picture hanging on the room wall, centred on (x, y), w logical units wide (about 130 =
    26 px: three coloured figures and a sun still read). state "whole"; "torn": the two halves
    (the tear through the small figure) hang apart with a gap, each by a pin, one a little lower;
    "taped": put back together with strips of tape across the tear, the gap still showing."""
    scale = w / PWL
    k = _k_of(scale)
    wpx = k * UW
    if state == "whole":
        whole(canvas, x, y, w, alpha)
        return
    s_l = k * PX                                               # logical per picture unit
    for side in (0, 1):
        cxh, cyh, _b = _region_center("half", side)
        dx = (cxh - UW / 2) * s_l
        dy = (cyh - UH / 2) * s_l
        sgn = -1 if side == 0 else 1
        if state == "torn":
            gap = max(2, round(wpx * 0.06)) * PX
            sag = PX if side == 1 else 0
            rot = (-6.0 if side == 0 else 6.0) if wpx >= 60 else 0.0
            X.blit(canvas, _sprite("half", side, scale, rot), x + dx + sgn * gap, y + dy + sag, alpha)
        else:
            X.blit(canvas, _sprite("half", side, scale), x + dx + sgn * PX * (1 if side else 0), y + dy, alpha)
    top = y - UH / 2 * s_l
    if state == "torn":
        gap = max(2, round(wpx * 0.06)) * PX
        for side, xx in ((0, x - UW * 0.25 * s_l - gap), (1, x + UW * 0.25 * s_l + gap)):
            pin = skia.Rect.MakeXYWH(X.snap(xx), X.snap(top + PX * (1 + side)), PX, PX)
            canvas.drawRect(pin, prims.fill(look.ROSE if side else look.SLATE, alpha))
        return
    # taped: strips across the tear and at the corners
    tw = max(2, round(wpx * 0.09))
    th = max(1, round(wpx * 0.045))
    tear_x = lambda yy: x + (float(_tear_x(yy)) - UW / 2) * s_l
    for yy in (UH * 0.18, UH * 0.52, UH * 0.82):
        cxp = tear_x(yy) + PX * 0.5
        r = skia.Rect.MakeXYWH(X.snap(cxp - tw * PX / 2), X.snap(y + (yy - UH / 2) * s_l - th * PX / 2), tw * PX,
                               th * PX)
        canvas.drawRect(r, prims.fill(TAPE, 0.9 * alpha, aa=False))
    for sx_ in (-1, 1):
        xx = x + sx_ * (UW / 2 - 2) * s_l
        r = skia.Rect.MakeXYWH(X.snap(xx - tw * PX / 2), X.snap(top - th * PX / 2), tw * PX, th * PX)
        canvas.drawRect(r, prims.fill(TAPE, 0.9 * alpha, aa=False))


# ---------------------------------------------------------------------------------------------
# paper birds and the paper plane
# ---------------------------------------------------------------------------------------------
def bird_poly(phase: float):
    """8-point unit outline of a paper bird heading +x (side-on, wings by flap phase radians; y
    down, as on screen)."""
    f = math.sin(phase)                                      # +1 wings up, -1 down
    return np.array([(1.0, -0.02), (0.30, -0.10), (-0.05 - 0.15 * f, -0.15 - 0.85 * f), (-0.30, -0.06),
                     (-0.95, -0.24), (-0.80, 0.12), (-0.10 + 0.1 * f, 0.12 + 0.35 * max(0.0, -f)), (0.40, 0.10)])


_FLAPS = (math.pi / 2, 0.0, -math.pi / 2, 0.0)              # up, mid, down, mid


def _flap_step(phase: float) -> int:
    return int(((phase / (2 * math.pi)) % 1.0) * 4) % 4


def _bird_sprite(L: int, step: int, head_q: int, paper, wing, morph_q: int = 4, tex: int | None = None):
    """A paper bird `L` px long (half-length L / 2), flap step, heading head_q * 15 degrees.
    morph_q 0..4: 4 = the bird, lower = still partly the torn piece `tex` (its drawing showing)."""
    key = ("pbird", L, step, head_q, X.qc(paper), X.qc(wing), morph_q, tex)

    def make():
        u = L / 2.0
        n = int(L * 1.6) + 6
        ox = oy = n // 2
        e = morph_q / 4.0
        pts = bird_poly(_FLAPS[step])
        if tex is not None and e < 1.0:
            pts = (piece(tex).poly * (1 - e) + pts * e) * (1.0 + 0.35 * (1 - e))   # keeps the piece's size
        ca, sa = math.cos(math.radians(head_q * 15.0)), math.sin(math.radians(head_q * 15.0))
        q = [(ox + (a * ca - b * sa) * u, oy + (a * sa + b * ca) * u) for a, b in pts]

        def path(idx):
            p = skia.Path()
            p.addPoly([skia.Point(float(q[j][0]), float(q[j][1])) for j in idx], True)
            return p
        arr = np.zeros((n, n, 4), np.uint8)
        s = skia.Surface(arr)
        c = s.getCanvas()
        pid = lambda r: skia.Paint(AntiAlias=False, Color=skia.ColorSetARGB(255, r, 0, r))
        c.drawPath(path(range(8)), pid(X.BASE))
        if e >= 0.5:
            c.drawPath(path([1, 2, 3]), pid(X.ACCENT))           # the near wing, crayon coloured
            if L >= 9:
                c.drawPath(path([7, 6, 5, 3]), pid(X.SHADE))      # the belly fold
        s.flushAndSubmit()
        roles = arr[..., 0].copy()
        roles[arr[..., 3] == 0] = 0
        cols = {X.BASE: paper, X.SHADE: shade(paper, -0.10), X.ACCENT: wing}
        out = X.colorize(roles, cols, outline=shade(paper, -0.45) if L >= 7 else None)
        if tex is not None and e < 1.0:                          # the drawing still shows on the folding piece
            k = u * (1.0 + 0.35 * (1 - e)) / (piece(tex).size * UW / PWL)
            parr = np.zeros((n, n, 4), np.uint8)
            ps = skia.Surface(parr)
            pc_ = ps.getCanvas()
            pc_.translate(ox, oy)
            pc_.rotate(head_q * 15.0)
            pc_.scale(k, k)
            pc_.translate(-piece(tex)._cx, -piece(tex)._cy)
            _paint_picture(pc_, k)
            ps.flushAndSubmit()
            m = (roles == X.BASE)
            w = 1.0 - e
            out[m, :3] = out[m, :3] * (1 - w) + parr[m, :3].astype(np.float32) / 255.0 * w
        return X.Sprite(out, ox, oy)
    return X.memo(key, make)


def unfold(canvas, i: int, x: float, y: float, w: float, size: float = 60.0, phase: float = 0.0,
           heading: float = 0.0, alpha: float = 1.0):
    """Piece i folding itself into a paper bird: w 0..1 in five steps (the piece, three folds
    where its torn outline turns into the bird with the drawing fading into paper, the bird); then
    it flaps in four stepped poses from `phase` (radians; drive it by t). The bird wears the
    piece's crayon colour on its wing. size is the bird's half-length (logical), heading degrees."""
    if w <= 0.1:
        pc = piece(i)
        draw_piece(canvas, i, x, y, size / pc.size, heading, alpha, 1.0, 0.0, 0.0)
        return
    pc = piece(i)
    mq = min(4, max(1, int(w * 4 + 0.5)))
    L = max(4, int(round(2 * size / PX)))
    step = _flap_step(phase) if mq == 4 else 1
    hq = int(round(heading / 15.0))
    X.blit(canvas, _bird_sprite(L, step, hq, TORN, pc.color, mq, i), x, y, alpha)


def paper_bird(canvas, x: float, y: float, size: float = 40.0, phase: float = 0.0, heading: float = 0.0,
               color=None, alpha: float = 1.0, tex: int | None = None):
    """A flying paper bird (half-length `size` logical, heading degrees in 15-degree steps, flap in
    four stepped poses from phase radians). With tex = a piece index it wears that piece's crayon
    colour on its wing; otherwise plain paper in `color`."""
    paper = look.PAPER if color is None else color
    wing = piece(tex).color if tex is not None else shade(paper, -0.06)
    L = max(4, int(round(2 * size / PX)))
    X.blit(canvas, _bird_sprite(L, _flap_step(phase), int(round(heading / 15.0)), paper, wing), x, y, alpha)


def paper_bird_sitting(canvas, x: float, y: float, size: float = 24.0, color=None, tex: int | None = None,
                       facing: int = 1, alpha: float = 1.0):
    """A folded paper bird sitting on a sill: base at (x, y), half-length `size` logical. With tex it
    is folded from that piece (its crayon colour on the wing); coda: tex=KEPT."""
    paper = TORN if color is None else color
    wing = piece(tex).color if tex is not None else shade(paper, -0.08)
    L = max(5, int(round(2 * size / PX)))
    key = ("psit", L, X.qc(paper), X.qc(wing), facing)

    def make():
        u = L / 2.0
        g = X.Pen(int(L * 1.4) + 6, int(L * 1.2) + 5, int(L * 0.7) + 3, int(L * 1.2) + 3, u, facing)
        g.poly([(-0.62, 0.0), (0.62, 0.0), (0.34, 0.32), (-0.34, 0.32)], X.BASE)          # the boat
        g.poly([(0.22, 0.24), (0.80, 0.95), (0.96, 0.86), (0.42, 0.16)], X.BASE)          # neck
        g.poly([(0.80, 0.95), (1.06, 0.84), (0.90, 0.80)], X.BASE)                        # head
        g.poly([(-0.20, 0.24), (-0.82, 0.78), (-0.70, 0.84), (-0.38, 0.16)], X.SHADE)    # tail
        g.poly([(-0.34, 0.30), (0.02, 0.86), (0.36, 0.30)], X.ACCENT)                     # folded wing
        if L >= 10:
            g.line([(-0.30, 0.10), (0.30, 0.10)], X.SHADE)
        cols = {X.BASE: paper, X.SHADE: shade(paper, -0.12), X.ACCENT: wing}
        return X.Sprite(X.colorize(g.roles(), cols, outline=shade(paper, -0.45)), g.ox, g.oy)
    X.blit(canvas, X.memo(key, make), x, y, alpha)


def paper_plane(canvas, x: float, y: float, size: float = 30.0, heading: float = 0.0, t: float = 0.0,
                color=None, alpha: float = 1.0, seed: int = 0):
    """A folded paper plane drifting (centre at (x, y), half-length `size` logical, heading degrees
    in 10-degree steps). It rocks by one step now and then (from t and seed)."""
    paper = hex_rgb("E6E2D6") if color is None else color
    L = max(5, int(round(2 * size / PX)))
    rock = 1 if math.sin(t * 2.1 + seed) > 0.7 else 0
    hq = int(round(heading / 10.0)) + rock
    key = ("plane", L, hq, X.qc(paper))

    def make():
        u = L / 2.0
        n = int(L * 1.3) + 6
        g = X.Pen(n, n, n // 2, n // 2, u, 1, -math.radians(hq * 10.0))
        g.poly([(1.0, 0.0), (-1.0, 0.26), (-0.72, 0.02)], X.BASE)          # the top wing
        g.poly([(1.0, 0.0), (-0.72, 0.02), (-0.95, -0.20)], X.SHADE)       # the keel fold
        g.poly([(0.6, -0.02), (-0.70, -0.02), (-0.80, -0.30)], X.SHADE)
        cols = {X.BASE: paper, X.SHADE: shade(paper, -0.14)}
        return X.Sprite(X.colorize(g.roles(), cols, outline=shade(paper, -0.45) if L >= 8 else None), g.ox, g.oy)
    X.blit(canvas, X.memo(key, make), x, y, alpha)
