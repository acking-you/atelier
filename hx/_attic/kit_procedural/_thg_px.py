"""Private pixel helpers shared by birds.py, scraps.py and memory.py.

Things are drawn at real-pixel resolution (1 unit = 1 real pixel) with anti-aliasing off into
small role maps (which part is base, shade, light ...), coloured by a manner, cached as skia
images and blitted five times enlarged with nearest sampling at snapped positions. So every edge
is a whole pixel, nothing is thinner than one pixel, and a size or pose is a new sprite, never a
resampled one.
"""
from __future__ import annotations

import math

import numpy as np
import skia

from hx.kit import pixel
from hx.kit.pixel import PX, snap

NEAREST = skia.SamplingOptions()

# roles
BASE, SHADE, LIGHT, DARK, ID, ACCENT, FACE, LINE = 1, 2, 3, 4, 5, 6, 7, 8
ROLE_NAMES = {"base": BASE, "shade": SHADE, "light": LIGHT, "dark": DARK, "id": ID,
              "accent": ACCENT, "face": FACE, "line": LINE}

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0

_CACHE: dict = {}


def memo(key, fn):
    v = _CACHE.get(key)
    if v is None:
        if len(_CACHE) > 8000:
            _CACHE.clear()
        v = fn()
        _CACHE[key] = v
    return v


def qc(c):
    """Colour as a hashable cache key (6 bits a channel)."""
    return tuple(int(round(float(v) * 63)) for v in c[:3])


def bayer(h: int, w: int, ox: int = 0, oy: int = 0) -> np.ndarray:
    yy = (np.arange(h) + oy) % 4
    xx = (np.arange(w) + ox) % 4
    return BAYER4[yy[:, None], xx[None, :]]


def flat(c):
    """A colour moved to the middle of its band on the pixel stage, so a flat area stays one flat
    tone (no stipple) when drawn ungraded."""
    lab = pixel._to_oklab(np.array([[c[:3]]], np.float32))
    lab[..., 0] = np.round(lab[..., 0] * pixel.LEVELS) / pixel.LEVELS
    lab[..., 1] = np.round(lab[..., 1] / pixel.CHROMA_STEP) * pixel.CHROMA_STEP
    lab[..., 2] = np.round(lab[..., 2] / pixel.CHROMA_STEP) * pixel.CHROMA_STEP
    return tuple(float(v) for v in pixel._to_srgb(lab)[0, 0])


# ------------------------------------------------------------------------------------- the pen
class Pen:
    """A small role map drawn in real pixels, AA off. Local units: `u` pixels per unit, origin
    (ox, oy) in pixels (a pixel corner), y up, optional mirror (`flip` -1) and rotation `rot`
    (radians, counter-clockwise in the y-up frame, applied after the mirror)."""

    def __init__(self, w: int, h: int, ox: float, oy: float, u: float, flip: int = 1, rot: float = 0.0,
                 sy: float = 1.0):
        self.w, self.h = int(w), int(h)
        self.arr = np.zeros((self.h, self.w, 4), np.uint8)
        self.surf = skia.Surface(self.arr)
        self.c = self.surf.getCanvas()
        self.ox, self.oy, self.u, self.flip, self.sy = ox, oy, u, flip, sy
        self.cr, self.sr = math.cos(rot), math.sin(rot)
        self.rotated = abs(rot) > 1e-6
        self._paints = {}

    def paint(self, role, stroke=0.0):
        k = (role, stroke)
        p = self._paints.get(k)
        if p is None:
            if role == 0:
                p = skia.Paint(AntiAlias=False, BlendMode=skia.BlendMode.kClear)
            else:
                p = skia.Paint(AntiAlias=False, Color=skia.ColorSetARGB(255, role, 0, role))
            if stroke:
                p.setStyle(skia.Paint.kStroke_Style)
                p.setStrokeWidth(0.0 if stroke < 1.5 else stroke)
                p.setStrokeCap(skia.Paint.kButt_Cap if stroke < 1.5 else skia.Paint.kRound_Cap)
            self._paints[k] = p
        return p

    def P(self, x, y):
        x = x * self.flip
        y = y * self.sy
        if self.rotated:
            x, y = x * self.cr - y * self.sr, x * self.sr + y * self.cr
        return self.ox + x * self.u, self.oy - y * self.u

    def px(self, n):
        """n local units in pixels."""
        return n * self.u

    def rect(self, x0, y0, x1, y1, role, minw=1, minh=1):
        """Axis-aligned box, snapped to whole pixels and at least minw x minh pixels."""
        if self.rotated:
            self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], role)
            return
        ax, ay = self.P(x0, y0)
        bx, by = self.P(x1, y1)
        l, r = sorted((ax, bx))
        t, b = sorted((ay, by))
        L, R, T, B = round(l), round(r), round(t), round(b)
        if R - L < minw:
            c = (l + r) / 2
            L = math.floor(c - minw / 2 + 0.5)
            R = L + minw
        if B - T < minh:
            c = (t + b) / 2
            T = math.floor(c - minh / 2 + 0.5)
            B = T + minh
        self.c.drawRect(skia.Rect.MakeLTRB(L, T, R, B), self.paint(role))

    def poly(self, pts, role):
        path = skia.Path()
        q = [self.P(x, y) for x, y in pts]
        path.addPoly([skia.Point(float(a), float(b)) for a, b in q], True)
        self.c.drawPath(path, self.paint(role))

    def oval(self, cx, cy, rx, ry, role, minw=1, minh=1):
        if self.rotated:
            n = 12
            self.poly([(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n))
                       for k in range(n)], role)
            return
        ax, ay = self.P(cx - rx, cy - ry)
        bx, by = self.P(cx + rx, cy + ry)
        l, r = sorted((ax, bx))
        t, b = sorted((ay, by))
        L, R, T, B = round(l), round(r), round(t), round(b)
        if R - L < minw:
            L = math.floor((l + r) / 2 - minw / 2 + 0.5)
            R = L + minw
        if B - T < minh:
            T = math.floor((t + b) / 2 - minh / 2 + 0.5)
            B = T + minh
        rr = skia.Rect.MakeLTRB(L, T, R, B)
        if R - L <= 2 or B - T <= 2:
            self.c.drawRect(rr, self.paint(role))
        else:
            self.c.drawOval(rr, self.paint(role))

    def line(self, pts, role, width=0.0, minw=1.0):
        """Polyline of `width` local units (at least `minw` pixels; 1 pixel = a hairline)."""
        wpx = max(minw, width * self.u)
        path = skia.Path()
        q = [self.P(x, y) for x, y in pts]
        if wpx < 1.5:
            q = [(math.floor(a) + 0.5, math.floor(b) + 0.5) for a, b in q]
        path.addPoly([skia.Point(float(a), float(b)) for a, b in q], False)
        self.c.drawPath(path, self.paint(role, wpx))

    def dot(self, x, y, role, n=1):
        a, b = self.P(x, y)
        L, T = math.floor(a - n / 2 + 0.5), math.floor(b - n / 2 + 0.5)
        self.c.drawRect(skia.Rect.MakeLTRB(L, T, L + n, T + n), self.paint(role))

    def roles(self) -> np.ndarray:
        self.surf.flushAndSubmit()
        r = self.arr[..., 0].copy()
        r[self.arr[..., 3] == 0] = 0
        return r


# ------------------------------------------------------------------------------------- morphology
def dilate(m: np.ndarray, diag: bool = False) -> np.ndarray:
    o = m.copy()
    o[1:] |= m[:-1]
    o[:-1] |= m[1:]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    if diag:
        o[1:, 1:] |= m[:-1, :-1]
        o[1:, :-1] |= m[:-1, 1:]
        o[:-1, 1:] |= m[1:, :-1]
        o[:-1, :-1] |= m[1:, 1:]
    return o


def erode(m: np.ndarray) -> np.ndarray:
    return ~dilate(~m)


def shift(m: np.ndarray, dx: int, dy: int) -> np.ndarray:
    o = np.zeros_like(m)
    h, w = m.shape[:2]
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    o[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = m[ys0:ys1, xs0:xs1]
    return o


# ------------------------------------------------------------------------------------- colouring
def rgba(h: int, w: int) -> np.ndarray:
    return np.zeros((h, w, 4), np.float32)


def put(out: np.ndarray, mask: np.ndarray, color) -> None:
    out[mask, 0] = color[0]
    out[mask, 1] = color[1]
    out[mask, 2] = color[2]
    out[mask, 3] = 1.0


def colorize(roles: np.ndarray, colors: dict, outline=None) -> np.ndarray:
    """Role map -> RGBA float; `colors` maps role ids to colours (missing roles fall back to
    BASE); `outline` colour draws a one-pixel ring outside the shape."""
    out = rgba(*roles.shape)
    base = colors.get(BASE, (0.5, 0.5, 0.5))
    for r in np.unique(roles):
        if r == 0:
            continue
        put(out, roles == r, colors.get(int(r), base))
    if outline is not None:
        m = roles > 0
        put(out, dilate(m) & ~m, outline)
    return out


def loom_colorize(mask: np.ndarray, tones, idmask=None, accent=None, accent_color=None, dissolve: float = 0.2,
                  side: str = "bottom", id_lift: float = 0.38, light=None, darkmask=None) -> np.ndarray:
    """A flat towering silhouette in three mist tones (tones[0] at the top, darkest), bands with a
    stippled seam, dissolving into the mist over the last `dissolve` of its height at `side`
    ("bottom" or "top"). idmask pixels (the identifying detail) are lifted toward `light`,
    darkmask pixels (thread, lines) sink a notch below the local tone."""
    h, w = mask.shape
    out = rgba(h, w)
    body = mask if darkmask is None else (mask & ~darkmask)
    rows = np.nonzero(body.any(1))[0]
    if len(rows) == 0:
        rows = np.nonzero(mask.any(1))[0]
    if len(rows) == 0:
        return out
    top, bot = rows[0], rows[-1] + 1
    f = (np.arange(h, dtype=np.float32) - top) / max(1, bot - top)          # 0 top .. 1 bottom
    th = bayer(h, w)
    k = np.clip(f[:, None] * 3.0 + (th - 0.5) * 0.5, 0, 2.999).astype(int)
    T = np.array([t[:3] for t in tones], np.float32)
    col = T[k]
    if idmask is not None:
        lt = np.array((light or (0.80, 0.82, 0.84))[:3], np.float32)
        col = np.where(idmask[..., None], col * (1 - id_lift) + lt * id_lift, col)
    if darkmask is not None:
        col = np.where(darkmask[..., None], col * 0.72, col)
    keep = mask.copy()
    if dissolve > 0:
        g = (1.0 - f) if side == "top" else f
        z = (g - (1.0 - dissolve)) / dissolve                                   # 0..1 inside the zone
        keep &= ~((z[:, None] > 0) & (th < np.maximum(z, 0.0)[:, None] ** 0.8))
    out[..., :3] = col
    out[..., 3] = keep
    if accent is not None and accent_color is not None:
        put(out, accent & keep, accent_color)
    out[~keep] = 0
    return out


def tip_rows(img: np.ndarray, frac: float) -> np.ndarray:
    """Squash a picture vertically toward its bottom row (a prop falling flat away from us)."""
    h = img.shape[0]
    rows = np.nonzero(img[..., 3].any(1))[0]
    if len(rows) == 0 or frac >= 0.999:
        return img
    top, bot = rows[0], rows[-1] + 1
    hh = bot - top
    nh = max(1, int(round(hh * frac)))
    out = np.zeros_like(img)
    src = bot - 1 - np.minimum(hh - 1, (np.arange(nh) * hh / nh).astype(int))
    out[bot - 1 - np.arange(nh)] = img[src]
    return out


# ------------------------------------------------------------------------------------- images, blit
class Sprite:
    __slots__ = ("img", "w", "h", "ox", "oy")

    def __init__(self, arr: np.ndarray, ox: float, oy: float):
        a = np.clip(arr * 255 + 0.5, 0, 255).astype(np.uint8)
        a[a[..., 3] == 0] = 0
        self.img = skia.Image.fromarray(np.ascontiguousarray(a), colorType=skia.kRGBA_8888_ColorType)
        self.h, self.w = a.shape[:2]
        self.ox, self.oy = ox, oy


_PAINTS: dict = {}


def blit(canvas, sp: Sprite | None, x: float, y: float, alpha: float = 1.0, snapped: bool = True):
    """Draw a sprite with its origin pixel corner at (x, y) (snapped to the grid), 5x, nearest."""
    if sp is None or alpha <= 0.004:
        return
    if snapped:
        x, y = snap(x), snap(y)
    a = round(min(1.0, alpha), 3)
    p = _PAINTS.get(a)
    if p is None:
        p = skia.Paint()
        p.setAlphaf(a)
        _PAINTS[a] = p
    canvas.drawImageRect(sp.img, skia.Rect.MakeXYWH(x - sp.ox * PX, y - sp.oy * PX, sp.w * PX, sp.h * PX),
                         NEAREST, p)

