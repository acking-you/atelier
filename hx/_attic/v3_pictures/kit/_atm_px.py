"""Private to look / cloud / lights: drawing straight on the real pixel grid.

A `Layer` is an RGBA float buffer covering a box of real pixels (device space / PX). A helper
computes its picture there with numpy (hard masks, flat tones, ordered stipple aligned to the
same 4x4 Bayer matrix as the pixel stage) and `blit`s it onto the canvas as an image enlarged PX
times with nearest sampling. Shapes are given in the canvas's local units; the canvas matrix
(camera pan or zoom) is honoured by mapping into device space, so whatever the transform the
result sits exactly on the film's 384x216 grid and nothing crawls.
"""
from __future__ import annotations

import math

import numpy as np
import skia

from . import pixel

PX = pixel.PX
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0  # 0..1
NEAREST = skia.SamplingOptions()


def rgb(c):
    return np.asarray(c[:3], np.float32)


class Layer:
    """Real-pixel buffer over the device box of local rect (l, t, r, b), clipped to the canvas.

    `ix0, iy0` its top-left pixel index on the device grid, `w, h` its size; `rgb` (h, w, 3) and
    `a` (h, w) are premultiplied float32. `s` = local units per real pixel are `PX / s`."""

    def __init__(self, canvas, rect=None, pad: float = 0.0, sparse: bool = False):
        m = canvas.getTotalMatrix()
        self.m = m
        self.s = math.sqrt(abs(m.getScaleX() * m.getScaleY() - m.getSkewX() * m.getSkewY())) or 1.0
        dc = canvas.getDeviceClipBounds()
        if rect is None:
            L, T, R, B = dc.left(), dc.top(), dc.right(), dc.bottom()
        else:
            l, t, r, b = rect
            box = m.mapRect(skia.Rect.MakeLTRB(l - pad, t - pad, r + pad, b + pad))
            L, T = max(box.left(), dc.left()), max(box.top(), dc.top())
            R, B = min(box.right(), dc.right()), min(box.bottom(), dc.bottom())
        self.ix0, self.iy0 = int(math.floor(L / PX)), int(math.floor(T / PX))
        self.w = max(0, int(math.ceil(R / PX)) - self.ix0)
        self.h = max(0, int(math.ceil(B / PX)) - self.iy0)
        self.empty = self.w <= 0 or self.h <= 0
        self.sparse = sparse
        if sparse:                       # only single pixels: kept as lists, drawn as points
            self._pts = []
        else:
            self.rgb = np.zeros((max(1, self.h), max(1, self.w), 3), np.float32)
            self.a = np.zeros((max(1, self.h), max(1, self.w)), np.float32)
        self._bayer = None
        self._inv = None

    @classmethod
    def raw(cls, ix0: int, iy0: int, rgb_premul, a):
        """A layer around ready-made premultiplied buffers at pixel (ix0, iy0) (for blitting)."""
        L = cls.__new__(cls)
        L.ix0, L.iy0 = ix0, iy0
        L.h, L.w = a.shape
        L.empty = L.w <= 0 or L.h <= 0
        L.sparse = False
        L.rgb, L.a = rgb_premul, a
        return L

    # coordinates ---------------------------------------------------------------------------
    def to_px(self, xs, ys):
        """Local points -> fractional layer pixel coordinates (pixel i has its centre at i)."""
        xs = np.asarray(xs, np.float64)
        ys = np.asarray(ys, np.float64)
        m = self.m
        dx = m.getScaleX() * xs + m.getSkewX() * ys + m.getTranslateX()
        dy = m.getSkewY() * xs + m.getScaleY() * ys + m.getTranslateY()
        return dx / PX - 0.5 - self.ix0, dy / PX - 0.5 - self.iy0

    def to_ipx(self, xs, ys):
        fx, fy = self.to_px(xs, ys)
        return np.round(fx).astype(np.int64), np.round(fy).astype(np.int64)

    def local_grid(self):
        """Local coordinates (X, Y) of every pixel centre, (h, w) each."""
        if self._inv is None:
            inv = skia.Matrix()
            self.m.invert(inv)
            ii = (np.arange(self.w) + self.ix0 + 0.5) * PX
            jj = (np.arange(self.h) + self.iy0 + 0.5) * PX
            DX, DY = np.meshgrid(ii, jj)
            X = inv.getScaleX() * DX + inv.getSkewX() * DY + inv.getTranslateX()
            Y = inv.getSkewY() * DX + inv.getScaleY() * DY + inv.getTranslateY()
            self._inv = (X, Y)
        return self._inv

    def px_len(self, v):
        """A local length in real pixels."""
        return v * self.s / PX

    @property
    def bayer(self):
        """(h, w) ordered thresholds 0..1, fixed to the screen (same matrix as the pixel stage)."""
        if self._bayer is None:
            yy = (np.arange(self.h) + self.iy0) % 4
            xx = (np.arange(self.w) + self.ix0) % 4
            self._bayer = BAYER[yy[:, None], xx[None, :]]
        return self._bayer

    # painting ------------------------------------------------------------------------------
    def fill(self, mask, color, alpha=1.0):
        """Source-over a flat colour where mask (bool or 0..1 per pixel) at alpha."""
        a = np.asarray(alpha, np.float32) * (mask.astype(np.float32) if mask.dtype == bool else mask)
        c = rgb(color)
        self.rgb *= (1.0 - a)[..., None]
        self.rgb += a[..., None] * c
        self.a *= 1.0 - a
        self.a += a

    def put(self, ix, iy, color, alpha=1.0):
        """Source-over single pixels (integer layer coords; out-of-box ones are dropped).
        `color` one colour or (n, 3); `alpha` scalar or (n,)."""
        ix = np.asarray(ix, np.int64).ravel()
        iy = np.asarray(iy, np.int64).ravel()
        al = np.broadcast_to(np.asarray(alpha, np.float32), ix.shape)
        col = np.asarray(color, np.float32)
        col = np.broadcast_to(col, (len(ix), 3)) if col.ndim == 1 else col
        ok = (ix >= 0) & (ix < self.w) & (iy >= 0) & (iy < self.h) & (al > 0.003)
        if not ok.any():
            return
        ix, iy, al, col = ix[ok], iy[ok], al[ok], col[ok]
        if self.sparse:
            self._pts.append((ix, iy, al, col))
            return
        # later points win where they overlap (painter's order inside one call is not kept)
        self.rgb[iy, ix] = self.rgb[iy, ix] * (1.0 - al)[:, None] + col * al[:, None]
        self.a[iy, ix] = self.a[iy, ix] * (1.0 - al) + al

    def blit(self, canvas, alpha: float = 1.0, blend=None, crop: bool = True):
        """Draw the buffer onto the canvas at its pixel box, cropped to what is painted unless
        `crop` is False (needed for blend modes that also act where the source is empty, such as
        kDstIn). A fully opaque buffer drawn plainly is enlarged in numpy and copied (about 1.5 ms
        full frame); otherwise skia blends it (about 4 ms per full frame of area)."""
        if self.empty or alpha <= 0.003:
            return
        if self.sparse:
            self._blit_points(canvas, alpha, blend)
            return
        a = self.a
        if crop:
            on = a > 0.002
            rows = np.flatnonzero(on.any(1))
            if not len(rows):
                return
            cols = np.flatnonzero(on.any(0))
            r0, r1, c0, c1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        else:
            r0, r1, c0, c1 = 0, self.h, 0, self.w
        a = np.clip(a[r0:r1, c0:c1], 0.0, 1.0)
        arr = np.empty((r1 - r0, c1 - c0, 4), np.uint8)
        arr[..., :3] = np.clip(self.rgb[r0:r1, c0:c1] * 255.0 + 0.5, 0, 255)
        arr[..., 3] = a * 255.0 + 0.5
        x0, y0 = (self.ix0 + c0) * PX, (self.iy0 + r0) * PX
        canvas.save()
        canvas.resetMatrix()
        if blend is None and alpha >= 0.999 and arr[..., 3].min() == 255:
            big = np.repeat(np.repeat(arr, PX, 0), PX, 1)
            img = skia.Image.fromarray(big, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kOpaque_AlphaType)
            canvas.drawImage(img, x0, y0, NEAREST, skia.Paint(BlendMode=skia.BlendMode.kSrc))
        else:
            img = skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
            p = skia.Paint()
            if alpha < 0.999:
                p.setAlphaf(float(alpha))
            if blend is not None:
                p.setBlendMode(blend)
            canvas.drawImageRect(img, skia.Rect.MakeXYWH(x0, y0, (c1 - c0) * PX, (r1 - r0) * PX), NEAREST, p)
        canvas.restore()


    def _blit_points(self, canvas, alpha, blend):
        if not self._pts:
            return
        ix = np.concatenate([p[0] for p in self._pts]) + self.ix0
        iy = np.concatenate([p[1] for p in self._pts]) + self.iy0
        al = np.concatenate([p[2] for p in self._pts]) * alpha
        col = np.concatenate([p[3] for p in self._pts])
        key = np.round(col * 255).astype(np.int64)
        key = (key[:, 0] << 16) | (key[:, 1] << 8) | key[:, 2]
        for k in np.unique(key):
            sel = key == k
            c = ((k >> 16) / 255.0, ((k >> 8) & 255) / 255.0, (k & 255) / 255.0)
            points(canvas, ix[sel], iy[sel], c, al[sel], levels=4, blend=blend)


def points(canvas, dx, dy, color, alphas=1.0, levels: int = 4, blend=None):
    """Single real pixels at device pixel indices (dx, dy), one colour, alpha bucketed into
    `levels` draw calls (cheap for sparse things: rain, dust, motes)."""
    dx = np.asarray(dx, np.float64).ravel()
    if not len(dx):
        return
    dy = np.asarray(dy, np.float64).ravel()
    al = np.clip(np.broadcast_to(np.asarray(alphas, np.float64), dx.shape), 0.0, 1.0)
    q = np.minimum((al * levels).astype(np.int64), levels - 1)
    p = skia.Paint(AntiAlias=False, StrokeWidth=PX, StrokeCap=skia.Paint.kSquare_Cap)
    if blend is not None:
        p.setBlendMode(blend)
    from mv.engine.palette import sk
    canvas.save()
    canvas.resetMatrix()
    for lv in range(levels):
        sel = (q == lv) & (al > 0.003)
        if not sel.any():
            continue
        p.setColor(sk(color, (lv + 0.5) / levels if levels > 1 else float(al[sel].max())))
        xs = (dx[sel] + 0.5) * PX
        ys = (dy[sel] + 0.5) * PX
        canvas.drawPoints(skia.Canvas.kPoints_PointMode, [skia.Point(x, y) for x, y in zip(xs.tolist(), ys.tolist())], p)
    canvas.restore()


def quantize(v, n: int, bayer, width: float = 0.5):
    """0..1 value -> tone index 0..n-1 with an ordered stipple of `width` (share of a band)
    across each band edge."""
    return np.clip(np.floor(v * n + (bayer - 0.5) * width), 0, n - 1).astype(np.int64)


def shift(a, dx: int, dy: int, fill=False):
    """a moved by (dx, dy) whole pixels (out-of-range filled with `fill`)."""
    out = np.full_like(a, fill)
    h, w = a.shape[:2]
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    if xs1 > xs0 and ys1 > ys0:
        out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = a[ys0:ys1, xs0:xs1]
    return out


def dilate(m, r: int = 1):
    """Square dilation of a bool mask by r pixels (4-neighbour steps r times)."""
    out = m.copy()
    for _ in range(r):
        o = out.copy()
        o[1:] |= out[:-1]
        o[:-1] |= out[1:]
        o[:, 1:] |= out[:, :-1]
        o[:, :-1] |= out[:, 1:]
        out = o
    return out


def line_px(x0, y0, dx, dy, n):
    """Pixel runs: for each start (x0, y0) (ints) a run of n[i] pixels stepping by (dx, dy) per
    pixel (floats, rounded). Returns (ix, iy, k, idx) flattened, k = step, idx = run index."""
    n = np.asarray(n, np.int64)
    if not len(n):
        z = np.zeros(0, np.int64)
        return z, z, z, z
    idx = np.repeat(np.arange(len(n)), n)
    start = np.cumsum(n) - n
    k = np.arange(int(n.sum())) - np.repeat(start, n)
    dx = np.broadcast_to(np.asarray(dx, np.float64), n.shape)[idx]
    dy = np.broadcast_to(np.asarray(dy, np.float64), n.shape)[idx]
    ix = np.asarray(x0)[idx] + np.round(dx * k).astype(np.int64)
    iy = np.asarray(y0)[idx] + np.round(dy * k).astype(np.int64)
    return ix, iy, k, idx


def null_canvas():
    """A canvas that swallows everything (stands in for ctx.glow while a picture is redrawn)."""
    return skia.MakeNullCanvas()


def dev_px(canvas, xs, ys):
    """Local points -> integer device pixel indices (the real pixel each falls in)."""
    m = canvas.getTotalMatrix()
    xs = np.asarray(xs, np.float64)
    ys = np.asarray(ys, np.float64)
    dx = m.getScaleX() * xs + m.getSkewX() * ys + m.getTranslateX()
    dy = m.getSkewY() * xs + m.getScaleY() * ys + m.getTranslateY()
    return np.floor(dx / PX).astype(np.int64), np.floor(dy / PX).astype(np.int64)


def canvas_scale(canvas) -> float:
    m = canvas.getTotalMatrix()
    return math.sqrt(abs(m.getScaleX() * m.getScaleY() - m.getSkewX() * m.getSkewY())) or 1.0
