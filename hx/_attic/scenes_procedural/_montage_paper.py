"""Cut-paper shape helpers for the montage sets: hand-cut edges, soft inner gradients, lifted shadows."""
from __future__ import annotations

import math

import skia

from mv.engine import palette as P
from mv.engine import prims
from mv.engine.palette import hex_rgb, sk

H01, HS = prims.hash01, prims.hash_sym

_BLUR: dict = {}


def blur_mask(sigma: float) -> skia.MaskFilter:
    m = _BLUR.get(sigma)
    if m is None:
        m = _BLUR[sigma] = skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma)
    return m


def cut_poly(pts, seed: int = 0, wob: float = 2.0, seg: float = 38.0, close: bool = True) -> skia.Path:
    """Polygon whose edges wander slightly, like scissors."""
    path = skia.Path()
    n = len(pts)
    k = 0
    first = True
    for i in range(n if close else n - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        ln = math.hypot(x1 - x0, y1 - y0)
        m = max(1, int(ln / seg))
        nx, ny = (-(y1 - y0) / (ln + 1e-9), (x1 - x0) / (ln + 1e-9))
        for j in range(m):
            f = j / m
            d = 0.0 if j == 0 else HS(seed * 977 + k, 31) * wob
            x, y = x0 + (x1 - x0) * f + nx * d, y0 + (y1 - y0) * f + ny * d
            k += 1
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)
    if close:
        path.close()
    else:
        path.lineTo(*pts[-1])
    return path


def cut_rect(l, t, r, b, seed: int = 0, wob: float = 1.6, skew: float = 0.0) -> skia.Path:
    """A slightly irregular quad (corners nudged by hash; `skew` px leans the top)."""
    j = lambda s: HS(seed, s) * wob * 1.5  # noqa: E731
    return cut_poly([(l + skew + j(1), t + j(2)), (r + skew + j(3), t + j(4)), (r + j(5), b + j(6)), (l + j(7), b + j(8))],
                    seed, wob)


def blob(cx, cy, rx, ry, seed: int = 0, lumps: float = 0.12, n: int = 14) -> skia.Path:
    """Soft lumpy closed shape (canopies, bushes, hair of distant heads)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = 1.0 + lumps * HS(seed * 31 + i, 41)
        pts.append((cx + math.cos(a) * rx * rr, cy + math.sin(a) * ry * rr))
    return smooth_closed(pts)


def smooth_closed(pts) -> skia.Path:
    path = skia.Path()
    n = len(pts)
    mids = [((pts[i][0] + pts[(i + 1) % n][0]) / 2, (pts[i][1] + pts[(i + 1) % n][1]) / 2) for i in range(n)]
    path.moveTo(*mids[-1])
    for i in range(n):
        path.quadTo(pts[i][0], pts[i][1], mids[i][0], mids[i][1])
    path.close()
    return path


def vpaint(col, top: float, bot: float, light: float = 0.07, alpha: float = 1.0, dark: float | None = None):
    """Vertical inner gradient: a lighter top edge falling to a slightly darker foot."""
    dark = light * 0.7 if dark is None else dark
    return prims.linear_paint((0, top), (0, bot), [P.shade(col, light), col, P.shade(col, -dark)],
                              [0.0, 0.35, 1.0], alpha, n=8)


def shape(c, path: skia.Path, col, light: float = 0.07, alpha: float = 1.0, lift: float = 0.0,
          lift_alpha: float = 0.22, dark: float | None = None):
    """Fill a cut shape with its inner gradient; `lift` px drops a soft paper shadow under it."""
    b = path.getBounds()
    if lift > 0:
        p = prims.fill(P.INK, lift_alpha * alpha)
        p.setMaskFilter(blur_mask(max(1.5, lift * 0.9)))
        c.save()
        c.translate(lift * 0.6, lift)
        c.drawPath(path, p)
        c.restore()
    c.drawPath(path, vpaint(col, b.top(), b.bottom(), light, alpha, dark))


def flat(c, path, col, alpha: float = 1.0):
    c.drawPath(path, prims.fill(col, alpha))


def haze(c, rect, col, alpha: float):
    """A translucent veil of air colour over the far planes."""
    l, t, r, b = rect
    c.drawRect(skia.Rect.MakeLTRB(l, t, r, b), prims.fill(col, alpha))


def scribble(c, x, y, w, h, seed: int, col, alpha: float = 0.35, width: float = 2.2, rows: int = 4):
    """Loose wandering chalk loops: no letters, no numbers."""
    p = prims.stroke(col, width, alpha)
    for r in range(rows):
        if H01(seed + r, 51) < 0.15:
            continue
        path = skia.Path()
        yy = y + (r + 0.5) * h / rows
        x0 = x + w * 0.06 * H01(seed + r, 52)
        x1 = x + w * (0.55 + 0.42 * H01(seed + r, 53))
        path.moveTo(x0, yy)
        n = int((x1 - x0) / 9)
        for i in range(1, n):
            xx = x0 + (x1 - x0) * i / n
            path.lineTo(xx + 3 * math.sin(i * 1.7 + seed), yy + (h / rows) * 0.22 * math.sin(i * 2.3 + r * 1.1 + seed))
        c.drawPath(path, p)


__all__ = ["cut_poly", "cut_rect", "blob", "smooth_closed", "vpaint", "shape", "flat", "haze", "scribble",
           "blur_mask", "hex_rgb", "sk", "H01", "HS"]
