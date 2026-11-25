"""Private: the sprite engine of hx.kit.figures.

A figure is built as a list of flat shapes in *sprite pixel space* (one unit = one real pixel of the
film, x to the right on screen, y down, the figure's root at the origin, on a pixel corner). Every
shape carries a material index and a part index instead of a colour. `render` rasterises the list
without anti-aliasing into a small buffer at real-pixel resolution, so every real pixel is exactly
one material; then, on that buffer and in whole pixels: the face features are stamped, a one-pixel
outline is put round the silhouette and between overlapping parts, the materials become colours,
the rim light lands on the lit edge, and translucency / dissolve become an ordered stipple. `blit`
draws the buffer enlarged x5 with nearest sampling at a pixel-aligned position, so the pixel stage
samples exactly these pixels back.
"""
from __future__ import annotations

import math

import numpy as np
import skia

from hx.kit._fig_geom import closed_path, poly_path
from hx.kit.pixel import PX

# --------------------------------------------------------------------------------------------
# materials: names -> index (0 = empty); the palette of each figure maps them to colours
# --------------------------------------------------------------------------------------------
MATS = ("line cloth cloth_sh cloth_lt cloth_dk acc acc_sh leg leg_sh leg_lt shoe shoe_sh sole "
        "skin skin_sh blush hair hair_sh hair_lt clip clip_sh collar "
        "lash iris iris_dk hl sclera mouth mouth_in tongue brow "
        "p_dark p_body p_screen p_screen_hi p_tray p_tray_sh p_bowl p_bowl_sh p_food "
        "p_pack p_pack_sh p_pack_lt p_strap p_cush p_cush_sh p_cush_lt flat").split()
M = {n: i + 1 for i, n in enumerate(MATS)}

_BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32)
_BAYER = (_BAYER + 0.5) / 16.0
_NEAREST = skia.SamplingOptions(skia.FilterMode.kNearest)


def qdir(v, lim=0.38):
    """A direction quantised to one of the 8 pixel neighbours."""
    x, y = float(v[0]), float(v[1])
    n = math.hypot(x, y) or 1.0
    x, y = x / n, y / n
    return (int(np.sign(x)) if abs(x) > lim else 0, int(np.sign(y)) if abs(y) > lim else 0)


class Sprite:
    """Collects the shapes of one figure in pixel space.

    s: real pixels per rig unit (h / PX); facing: +1 / -1 mirrors the rig's x; light: screen
    direction toward the light."""

    def __init__(self, s: float, facing: int, light=(-0.6, -0.8), flat: bool = False):
        self.s = float(s)
        self.f = 1 if facing >= 0 else -1
        self.flat = flat
        self.ops: list = []
        self.pid = 0
        self.cast = np.zeros(256, bool)      # part draws a line onto the parts behind it
        self.recv = np.ones(256, bool)       # part takes lines from the parts in front
        self.L = qdir(light)
        self.face = None                     # (callable(mat, part, ox, oy)) stamped after raster
        self.marks: dict = {}                # named pixel positions (anchors for props)

    # ---- coordinates ---------------------------------------------------------------------
    def P(self, pts) -> np.ndarray:
        a = np.asarray(pts, dtype=np.float64)
        out = np.empty_like(a)
        out[..., 0] = a[..., 0] * (self.f * self.s)
        out[..., 1] = a[..., 1] * -self.s
        return out

    def px(self, n: float) -> float:
        """n real pixels in rig units."""
        return n / self.s

    # ---- parts ---------------------------------------------------------------------------
    def part(self, cast: bool = True, recv: bool = True) -> int:
        self.pid = min(255, self.pid + 1)
        self.cast[self.pid] = cast and not self.flat
        self.recv[self.pid] = recv
        return self.pid

    def code(self, mat: str) -> int:
        return skia.Color(M["flat"] if self.flat else M[mat], self.pid, 0, 255)

    # ---- shapes (rig units in, pixel-space paths out) ------------------------------------
    def path(self, pts, smooth_: bool = True) -> skia.Path:
        if isinstance(pts, skia.Path):
            return pts
        q = self.P(pts)
        return closed_path(q) if smooth_ else poly_path(q)

    def fill(self, pts, mat: str, smooth_: bool = True, into=None):
        p = self.path(pts, smooth_)
        (self.ops if into is None else into).append(("f", p, self.code(mat)))
        return p

    def stroke(self, pts, mat: str, w_px: float = 1.0, into=None):
        q = self.P(pts)
        p = skia.Path()
        p.moveTo(float(q[0, 0]), float(q[0, 1]))
        for x, y in q[1:]:
            p.lineTo(float(x), float(y))
        (self.ops if into is None else into).append(("s", p, self.code(mat), max(1.0, float(w_px))))
        return p

    def rect_px(self, x0, y0, w, h, mat: str, into=None):
        """A rectangle given directly in pixel space (whole pixels)."""
        p = skia.Path()
        p.addRect(skia.Rect.MakeXYWH(float(x0), float(y0), float(w), float(h)))
        (self.ops if into is None else into).append(("f", p, self.code(mat)))
        return p

    def formed(self, pts, base: str, shade: str | None = None, lit: str | None = None, d: int = 1,
               dl: int = 1, details=None, smooth_: bool = True):
        """A flat shape with a shade crescent `d` pixels wide away from the light and a lit edge
        `dl` pixels wide toward it (whole-pixel offsets, so the bands keep their width)."""
        path = self.path(pts, smooth_)
        if self.flat:
            self.ops.append(("f", path, self.code(base)))
            return path
        lx, ly = self.L
        items = []
        if shade is not None and d > 0 and (lx or ly):
            items.append(("f", path, self.code(shade)))
            items.append(("t", path, self.code(base), lx * d, ly * d))
        else:
            items.append(("f", path, self.code(base)))
        if lit is not None and dl > 0 and (lx or ly):
            items.append(("x", path, -lx * dl, -ly * dl, [("f", path, self.code(lit))]))
        if details:
            items += details
        self.ops.append(("g", path, items))
        return path

    def clip_last(self, clip_path):
        """Keep the shape added last inside clip_path (a fringe inside its hair mass)."""
        if self.ops:
            self.ops.append(("g", clip_path, [self.ops.pop()]))

    def clip(self, clip_path, items):
        if items:
            self.ops.append(("g", clip_path, items))


# --------------------------------------------------------------------------------------------
# raster
# --------------------------------------------------------------------------------------------
_PAINTS: dict = {}


def _paint(code: int, stroke: float = 0.0) -> skia.Paint:
    k = (code, stroke)
    p = _PAINTS.get(k)
    if p is None:
        p = skia.Paint(AntiAlias=False, Color=code)
        if stroke:
            p.setStyle(skia.Paint.kStroke_Style)
            p.setStrokeWidth(stroke)
            p.setStrokeCap(skia.Paint.kSquare_Cap)
            p.setStrokeJoin(skia.Paint.kMiter_Join)
        if len(_PAINTS) > 4000:
            _PAINTS.clear()
        _PAINTS[k] = p
    return p


def _run(canvas, ops):
    for op in ops:
        k = op[0]
        if k == "f":
            canvas.drawPath(op[1], _paint(op[2]))
        elif k == "s":
            canvas.drawPath(op[1], _paint(op[2], op[3]))
        elif k == "t":
            canvas.save()
            canvas.translate(op[3], op[4])
            canvas.drawPath(op[1], _paint(op[2]))
            canvas.restore()
        elif k == "g":
            canvas.save()
            canvas.clipPath(op[1], skia.ClipOp.kIntersect, False)
            _run(canvas, op[2])
            canvas.restore()
        elif k == "x":
            canvas.save()
            canvas.translate(op[2], op[3])
            canvas.clipPath(op[1], skia.ClipOp.kDifference, False)
            canvas.translate(-op[2], -op[3])
            _run(canvas, op[4])
            canvas.restore()


def _bounds(ops):
    x0 = y0 = 1e9
    x1 = y1 = -1e9
    for op in ops:
        b = op[1].getBounds()
        w = op[3] if op[0] == "s" else 0.0
        x0, y0 = min(x0, b.left() - w), min(y0, b.top() - w)
        x1, y1 = max(x1, b.right() + w), max(y1, b.bottom() + w)
    return x0, y0, x1, y1


def sh(a: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """out[y, x] = a[y - dy, x - dx] (zero outside)."""
    H, W = a.shape[:2]
    out = np.zeros_like(a)
    if abs(dx) >= W or abs(dy) >= H:
        return out
    out[max(dy, 0):H + min(dy, 0), max(dx, 0):W + min(dx, 0)] = a[max(-dy, 0):H + min(-dy, 0),
                                                                  max(-dx, 0):W + min(-dx, 0)]
    return out


_N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def raster(sp: Sprite):
    """-> (mat, part, ox, oy): uint8 buffers and the pixel position of their top-left corner."""
    if not sp.ops:
        return None
    x0, y0, x1, y1 = _bounds(sp.ops)
    ox, oy = int(math.floor(x0)) - 2, int(math.floor(y0)) - 2
    W, H = int(math.ceil(x1)) - ox + 2, int(math.ceil(y1)) - oy + 2
    W, H = max(4, min(W, 1200)), max(4, min(H, 1200))
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    surf = skia.Surface(arr)
    c = surf.getCanvas()
    c.translate(-ox, -oy)
    _run(c, sp.ops)
    surf.flushAndSubmit()
    mat = arr[..., 0].copy()
    part = arr[..., 1].copy()
    if sp.face is not None:
        sp.face(mat, part, ox, oy)
    return mat, part, ox, oy


def finish(sp: Sprite, mat, part, pal: np.ndarray, *, outline: bool = True, rim=None, inner: bool = True):
    """Materials -> RGBA with the outline, inner lines and the rim light."""
    inside = mat > 0
    out = mat.copy()
    if outline:
        grow = np.zeros_like(inside)
        for dx, dy in _N4:
            grow |= sh(inside, dx, dy)
        edge = grow & ~inside
        if inner:
            line = np.zeros_like(inside)
            rc = sp.recv[part] & inside
            for dx, dy in _N4:
                nb = sh(part, dx, dy)
                line |= rc & (nb > part) & sp.cast[nb] & sh(inside, dx, dy)
            out[line] = M["line"]
        out[edge] = M["line"]
        solid = inside | edge
    else:
        solid = inside
    rgb = pal[out]
    if rim is not None and rim[1] > 0.01:
        lx, ly = sp.L
        if lx or ly:
            body = inside & (out != M["line"])
            open_ = np.zeros_like(inside)
            for dx, dy in {(lx, 0), (0, ly)}:
                if dx or dy:
                    open_ |= ~sh(inside, -dx, -dy)          # the neighbour toward the light is outside
            r = body & open_
            rgb[r] = _mix(rgb[r], rim[0], rim[1])
    a = np.where(solid, 255, 0).astype(np.uint8)
    return rgb, a


def _mix(c, col, w):
    col = np.asarray(col, dtype=np.float32) * 255.0
    return (c.astype(np.float32) * (1 - w) + col * w + 0.5).astype(np.uint8)


def stipple(a: np.ndarray, keep: float, gx0: int, gy0: int) -> np.ndarray:
    """Ordered thinning on the screen grid: keep about `keep` of the pixels, no blended colours."""
    if keep >= 0.999:
        return a
    H, W = a.shape
    ys = (np.arange(H) + gy0) % 4
    xs = (np.arange(W) + gx0) % 4
    th = _BAYER[ys[:, None], xs[None, :]]
    return np.where(th < keep, a, 0).astype(np.uint8)


def hash2(i, j, salt):
    v = np.sin(i * 12.9898 + j * 78.233 + salt * 37.719) * 43758.5453
    return v - np.floor(v)


def dissolve(rgb, a, d: float, lee: int, t: float, seed: int, gx0: int, gy0: int):
    """Thin the figure to about 45 % with the ordered stipple and break its lee edge into single
    pixels; returns the new alpha and the drifting flecks [(gx, gy, rgb)]."""
    if d <= 0.0:
        return a, []
    H, W = a.shape
    solid = a > 0
    a = stipple(a, 1.0 - 0.55 * d, gx0, gy0)
    # distance (in pixels, up to 4) to the outside on the lee side
    run = np.zeros((H, W), np.int8)
    cur = solid.copy()
    for k in range(1, 5):
        cur = cur & sh(solid, -lee * k, 0)
        run += cur
    reach = 1 + 3 * d
    gen = math.floor(t / 0.4)
    yy, xx = np.mgrid[0:H, 0:W]
    gi, gj = xx + gx0, yy + gy0
    n = hash2(gi, gj, gen * 3.1 + seed)
    gone = solid & (run < reach) & (n < 0.35 + 0.5 * d)
    a = np.where(gone, 0, a).astype(np.uint8)
    # flecks: lee-edge pixels that leave and drift downwind and up, one pixel each
    ey, ex = np.nonzero(solid & (run == 0))
    flecks = []
    if len(ex):
        m = int(4 + 22 * d)
        life = 2.4
        for k in range(m):
            ph = (t / life + hash2(k, seed, 5.0)) % 1.0
            g = math.floor(t / life + hash2(k, seed, 5.0))
            idx = int(hash2(k, g + seed * 7, 6.0) * len(ex)) % len(ex)
            sx, sy = int(ex[idx]), int(ey[idx])
            dx = lee * int(1 + ph * (8 + 10 * hash2(k, g, 7.0)))
            dy = -int(ph * (2 + 4 * hash2(k, g, 8.0)))
            if ph > 0.85 * d + 0.1:
                continue
            flecks.append((sx + gx0 + dx, sy + gy0 + dy, rgb[sy, sx]))
    return a, flecks


def blit(canvas, rgb, a, X0: float, Y0: float, ox: int, oy: int, alpha_layer: float = 1.0):
    """Draw the buffer with its top-left pixel at root + (ox, oy) pixels, enlarged x PX, nearest."""
    H, W = a.shape
    rgba = np.empty((H, W, 4), dtype=np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = a
    rgba[a == 0] = 0
    img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)
    dst = skia.Rect.MakeXYWH(X0 + ox * PX, Y0 + oy * PX, W * PX, H * PX)
    paint = None
    if alpha_layer < 0.999:
        paint = skia.Paint(Alphaf=float(alpha_layer))
    canvas.drawImageRect(img, skia.Rect.MakeWH(W, H), dst, _NEAREST, paint, skia.Canvas.kStrict_SrcRectConstraint)


def device_snap(canvas, x: float, y: float):
    """Snap the root to the device pixel grid when the canvas is only translated; returns the
    snapped local position and the global pixel index of the root (for screen-fixed patterns)."""
    m = canvas.getTotalMatrix()
    if m.isTranslate():
        tx, ty = m.getTranslateX(), m.getTranslateY()
        X = round((x + tx) / PX) * PX - tx
        Y = round((y + ty) / PX) * PX - ty
        return X, Y, int(round((X + tx) / PX)), int(round((Y + ty) / PX))
    return x, y, int(round(x / PX)), int(round(y / PX))
