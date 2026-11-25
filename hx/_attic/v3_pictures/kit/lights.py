"""Small lights as pixel art: the amber firefly-mote (a one-pixel core, a twinkling plus-shaped
sparkle, a stippled halo), a ribbon of motes, the dull moth, one-pixel chirp rings, pollen and
glints as single pixels, and lit windows in far buildings.

Cores on ctx.canvas on the real pixel grid, energy on ctx.glow (soft there). Pure functions of
their arguments and t. API in hx/kit/README.md.
"""
from __future__ import annotations

import math

import numpy as np

from mv.engine import palette as P
from mv.engine import prims

from . import look
from ._atm_px import PX, Layer, canvas_scale, dev_px, points

H01 = prims.hash01
HS = prims.hash_sym
CORE = P.mix(look.AMBER, look.PAPER, 0.55)        # the hot cream centre of a mote
MOTH = look.hex_rgb("7D7F86")


def wander(seed, t, amp: float = 1.0):
    """Gentle irregular flight offset (dx, dy) for amplitude `amp` (about +-amp). Works on
    scalar or array seeds: a sum of three detuned sines plus value noise, never periodic-looking."""
    s = np.asarray(seed)
    fx = 0.23 + 0.17 * H01(s, 1)
    fy = 0.31 + 0.19 * H01(s, 2)
    p1, p2 = 6.283 * H01(s, 3), 6.283 * H01(s, 4)
    dx = (0.55 * np.sin(t * fx * 6.283 + p1) + 0.25 * np.sin(t * fx * 2.71 * 6.283 + p2)
          + 0.4 * (prims.value_noise(t * 0.9 + 37.0 * s, 11) - 0.5))
    dy = (0.5 * np.sin(t * fy * 6.283 + p2) + 0.2 * np.sin(t * fy * 3.13 * 6.283 + p1)
          + 0.5 * (prims.value_noise(t * 1.1 + 53.0 * s, 12) - 0.5))
    return dx * amp, dy * amp


def flicker(seed, t):
    """0.6..1 slow irregular breathing of a mote's brightness."""
    return 0.6 + 0.4 * prims.value_noise(t * 2.3 + 17.0 * np.asarray(seed), 13)


_HALO: dict = {}


def _halo_offsets(r: int):
    """Pixel offsets of a stippled halo ring (checkerboard) between radius 1.5 and r + 0.5."""
    if r not in _HALO:
        k = np.arange(-r - 1, r + 2)
        dx, dy = np.meshgrid(k, k)
        d = np.hypot(dx, dy)
        sel = (d > 1.5) & (d < r + 0.5) & ((dx + dy) % 2 == 0)
        _HALO[r] = (dx[sel], dy[sel], d[sel] / (r + 0.5))
    return _HALO[r]


def motes(ctx, xs, ys, size=1.0, alphas=1.0, color=look.AMBER, core=CORE, glow: float = 1.0, canvas=None):
    """Batch of firefly-motes: a one-pixel core (two by two above size 1.6), a plus-shaped
    sparkle whose arms show when a mote is bright (so they twinkle with its flicker), and a
    stippled halo ring of about 2 to 4 pixels; the energy on ctx.glow. size scales them;
    per-mote alphas allowed."""
    canvas = ctx.canvas if canvas is None else canvas
    xs = np.atleast_1d(np.asarray(xs, float))
    if not len(xs):
        return
    ys = np.atleast_1d(np.asarray(ys, float))
    n = len(xs)
    sz = np.broadcast_to(np.asarray(size, float), (n,)) * canvas_scale(canvas)
    al = np.clip(np.broadcast_to(np.asarray(alphas, float), (n,)), 0.0, 1.0)
    ix, iy = dev_px(canvas, xs, ys)
    # halo: one ring size per mote (2, 3 or 4 px), alpha falling outward in two steps
    for r in (2, 3, 4):
        sel = np.clip(np.round(1.0 + 1.3 * sz), 2, 4) == r
        if not sel.any():
            continue
        hx, hy, hd = _halo_offsets(r)
        px = (ix[sel][:, None] + hx[None, :]).ravel()
        py = (iy[sel][:, None] + hy[None, :]).ravel()
        ha = (al[sel][:, None] * np.where(hd[None, :] < 0.7, 0.45, 0.22)).ravel()
        points(canvas, px, py, color, ha, levels=3)
    # sparkle arms: one pixel at alpha > 0.55, two when big and bright
    arm = (al * np.minimum(1.0, sz)) > 0.55
    if arm.any():
        a1 = np.r_[1, -1, 0, 0], np.r_[0, 0, 1, -1]
        px = (ix[arm][:, None] + a1[0][None, :]).ravel()
        py = (iy[arm][:, None] + a1[1][None, :]).ravel()
        points(canvas, px, py, color, np.repeat(al[arm] * 0.9, 4), levels=2)
        far = arm & (sz > 1.4) & (al > 0.8)
        if far.any():
            px = (ix[far][:, None] + 2 * a1[0][None, :]).ravel()
            py = (iy[far][:, None] + 2 * a1[1][None, :]).ravel()
            points(canvas, px, py, color, np.repeat(al[far] * 0.55, 4), levels=2)
    points(canvas, ix, iy, core, al, levels=3)
    big = sz > 1.6
    if big.any():
        points(canvas, np.r_[ix[big] + 1, ix[big], ix[big] + 1], np.r_[iy[big], iy[big] + 1, iy[big] + 1], core,
               np.tile(al[big], 3), levels=3)
    g = getattr(ctx, "glow", None)
    if glow > 0 and g is not None:
        cx, cy = (ix + 0.5) * PX, (iy + 0.5) * PX                 # device; the glow canvas is in logical units
        m = canvas.getTotalMatrix()
        inv = __import__("skia").Matrix()
        m.invert(inv)
        gx = inv.getScaleX() * cx + inv.getSkewX() * cy + inv.getTranslateX()
        gy = inv.getSkewY() * cx + inv.getScaleY() * cy + inv.getTranslateY()
        prims.draw_sprites(g, prims.soft_disc(64, 0.0), gx, gy, 60.0 * np.broadcast_to(np.asarray(size, float), (n,)) / 64,
                           color, np.minimum(1, al * glow * 0.9), additive=True)


def mote(ctx, x, y, size=1.0, alpha=1.0, seed: int = 0, t=None, color=look.AMBER, glow=1.0):
    """One firefly-mote at (x, y) with its own flicker."""
    t = ctx.t if t is None else t
    motes(ctx, [x], [y], size, alpha * float(flicker(seed, t)), color, glow=glow)


def ribbon(ctx, path, n: int, head: float, t=None, seed: int = 0, size=1.0, alpha=1.0, trail: float = 0.6,
           spread: float = 14.0, color=look.AMBER):
    """N motes along a polyline `path` [(x, y)...] behind a travelling head at `head` (0..1 of the
    path length; it may run past 1 to let the tail through). The trail covers `trail` of the path,
    motes shrinking and fading behind the head, spaced irregularly and each wandering by `spread`."""
    t = ctx.t if t is None else t
    pts = np.asarray(path, float)
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    ids = np.arange(n) + seed * 1009
    lag = np.sort(H01(ids, 30) ** 1.4) * trail                # irregular spacing, denser near the head
    pos = head - lag
    ok = (pos >= 0) & (pos <= 1)
    if not ok.any():
        return
    s = pos[ok] * seg[-1]
    x = np.interp(s, seg, pts[:, 0])
    y = np.interp(s, seg, pts[:, 1])
    dx, dy = wander(ids[ok], t, spread)
    f = 1.0 - lag[ok] / max(trail, 1e-6)
    sz = size * (0.35 + 0.75 * f ** 1.5) * (0.7 + 0.5 * H01(ids[ok], 31))
    al = alpha * (0.25 + 0.75 * f) * flicker(ids[ok], t)
    motes(ctx, x + dx * (1.2 - f), y + dy * (1.2 - f), sz, al, color)


# ---------------------------------------------------------------------------------------------
# the moth
# ---------------------------------------------------------------------------------------------
def moth_pos(cx, cy, t, r: float = 46.0, seed: int = 0):
    """Mechanical circling around a lamp at (cx, cy): even angular speed on a tilted ellipse with a
    small hard jitter. Returns (x, y, heading_radians)."""
    w = 4.2 + 0.8 * H01(seed, 40)
    a = t * w + 6.283 * H01(seed, 41)
    jit = 0.08 * math.sin(t * 23.0 + seed) + 0.05 * math.sin(t * 37.0)
    x = cx + math.cos(a) * r * (1 + jit)
    y = cy + math.sin(a) * r * 0.45 + r * 0.1 * math.sin(a * 2)
    return x, y, a + math.pi / 2


_MOTH_FRAMES = (  # (dx, dy, part) per wing state; part 0 body, 1 wing
    ((0, 0, 0), (0, 1, 0), (-1, -1, 1), (1, -1, 1), (-1, 0, 1), (1, 0, 1)),            # wings up
    ((0, 0, 0), (0, 1, 0), (-1, 0, 1), (1, 0, 1), (-2, 0, 1), (2, 0, 1)),             # spread
    ((0, 0, 0), (0, 1, 0), (-1, 1, 1), (1, 1, 1), (-1, 0, 1), (1, 0, 1)),             # down
)


def moth(ctx, cx, cy, t=None, r: float = 46.0, size: float = 1.0, seed: int = 0, color=MOTH, alpha: float = 0.9):
    """A dull grey moth of a few pixels circling the lamp point (cx, cy), its wings switching
    between three states every step. size 2 doubles its pixels."""
    t = ctx.t if t is None else t
    x, y, _hd = moth_pos(cx, cy, t, r, seed)
    canvas = ctx.canvas
    ix, iy = dev_px(canvas, [x], [y])
    fr = _MOTH_FRAMES[int(math.floor(t * 15.0 + seed)) % 3]
    k = max(1, int(round(size)))
    body = [(dx, dy) for dx, dy, p in fr if p == 0]
    wing = [(dx, dy) for dx, dy, p in fr if p == 1]
    for sel, col, a in ((wing, P.shade(color, 0.05), alpha * 0.85), (body, P.shade(color, -0.12), alpha)):
        px = [ix[0] + dx * k + i for dx, dy in sel for i in range(k) for j in range(k)]
        py = [iy[0] + dy * k + j for dx, dy in sel for i in range(k) for j in range(k)]
        points(canvas, px, py, col, a, levels=1)


_RINGS: dict = {}


def _ring_offsets(r: int):
    if r not in _RINGS:
        k = np.arange(-r - 1, r + 2)
        dx, dy = np.meshgrid(k, k)
        sel = np.abs(np.hypot(dx, dy) - r) < 0.5
        _RINGS[r] = (dx[sel], dy[sel])
    return _RINGS[r]


def chirp_rings(ctx, x, y, t, times, life: float = 1.1, radius: float = 70.0, color=MOTH, alpha: float = 0.35):
    """The moth's dull 'chirp': one-pixel rings growing from (x, y) a pixel at a time for each
    start time in `times` (pass the off-beat times), fading in steps over `life` seconds."""
    tt = np.asarray(times, float)
    age = t - tt
    sel = (age >= 0) & (age < life)
    if not sel.any():
        return
    canvas = ctx.canvas
    ix, iy = dev_px(canvas, [x], [y])
    rmax = radius / PX * canvas_scale(canvas)
    for a_ in age[sel]:
        f = a_ / life
        r = int(round((0.25 + 0.75 * (1 - (1 - f) ** 2)) * rmax))
        if r < 1:
            continue
        dx, dy = _ring_offsets(r)
        al = alpha * (1.0 if f < 0.4 else (0.6 if f < 0.75 else 0.3))
        points(canvas, ix[0] + dx, iy[0] + dy, color, al, levels=1)


# ---------------------------------------------------------------------------------------------
# pollen, dust, glints
# ---------------------------------------------------------------------------------------------
def pollen(ctx, rect, t=None, n: int = 60, seed: int = 0, color=None, alpha: float = 0.6, drift=(6.0, -3.0),
           glow: float = 0.0):
    """Slowly drifting pollen or dust in still air over rect (l, t, r, b) as single pixels:
    wraps inside the rect, twinkles as specks turn into the light (two alpha steps), the
    brightest fifth a lighter colour; glow > 0 also puts those on ctx.glow."""
    t = ctx.t if t is None else t
    color = P.mix(look.AMBER, look.PAPER, 0.6) if color is None else color
    l, tp, r, b = rect
    ids = np.arange(n) + seed * 4099
    sp = 0.5 + H01(ids, 50)
    dx, dy = wander(ids, t * 0.6, 22.0)
    x = l + ((H01(ids, 51) * (r - l) + drift[0] * sp * t + dx) % (r - l))
    y = tp + ((H01(ids, 52) * (b - tp) + drift[1] * sp * t + dy) % (b - tp))
    tw = 0.5 + 0.5 * np.sin(t * (0.8 + 1.6 * H01(ids, 53)) + 6.283 * H01(ids, 54))
    al = alpha * np.where(tw > 0.6, 1.0, 0.45)
    big = H01(ids, 55) > 0.8
    ix, iy = dev_px(ctx.canvas, x, y)
    points(ctx.canvas, ix[~big], iy[~big], color, al[~big], levels=2)
    points(ctx.canvas, ix[big], iy[big], P.mix(color, (1, 1, 1), 0.4), al[big], levels=2)
    if glow > 0 and getattr(ctx, "glow", None) is not None:
        prims.draw_dots(ctx.glow, x[big], y[big], 4.0, color, al[big] * glow, levels=2)


def glints(ctx, xs, ys, t=None, size=1.0, alpha=1.0, seed: int = 0, color=None, rate: float = 0.6):
    """Small glints at points that each flash briefly about every 1/rate seconds at hashed
    phases: a single bright pixel, at the peak a plus of one-pixel arms (two at size > 1.4).
    Energy on the glow."""
    t = ctx.t if t is None else t
    color = P.mix(look.AMBER, look.PAPER, 0.7) if color is None else color
    xs = np.atleast_1d(np.asarray(xs, float))
    ys = np.atleast_1d(np.asarray(ys, float))
    ids = np.arange(len(xs)) + seed * 211
    ph = (t * rate * (0.7 + 0.6 * H01(ids, 60)) + H01(ids, 61)) % 1.0
    f = np.clip(1.0 - np.abs(ph - 0.5) / 0.12, 0, 1) ** 2
    sel = f > 0.05
    if not sel.any():
        return
    sz = np.broadcast_to(np.asarray(size, float), xs.shape)[sel]
    canvas = ctx.canvas
    ix, iy = dev_px(canvas, xs[sel], ys[sel])
    fa = f[sel]
    peak = fa > 0.5
    if peak.any():
        a1 = np.r_[1, -1, 0, 0], np.r_[0, 0, 1, -1]
        points(canvas, (ix[peak][:, None] + a1[0]).ravel(), (iy[peak][:, None] + a1[1]).ravel(), color,
               np.repeat(alpha * fa[peak] * 0.8, 4), levels=2)
        two = peak & (sz > 1.4)
        if two.any():
            points(canvas, (ix[two][:, None] + 2 * a1[0]).ravel(), (iy[two][:, None] + 2 * a1[1]).ravel(), color,
                   np.repeat(alpha * fa[two] * 0.45, 4), levels=2)
    points(canvas, ix, iy, P.mix(color, (1, 1, 1), 0.5), alpha * np.maximum(0.5, fa), levels=2)
    g = getattr(ctx, "glow", None)
    if g is not None:
        prims.draw_sprites(g, prims.soft_disc(64), xs[sel], ys[sel], 0.6 * sz, color, alpha * fa * 0.7, additive=True)


# ---------------------------------------------------------------------------------------------
# lit windows in far buildings
# ---------------------------------------------------------------------------------------------
def windows(ctx, rect, t=None, seed: int = 0, size=(1, 1), gap=(2, 3), lit: float = 0.35, warm: float = 0.7,
            warm_color=None, cold_color=None, dark=None, people: float = 0.0, flicker: float = 0.0,
            alpha: float = 1.0, glow: float = 0.4, canvas=None):
    """Rows of small windows on a facade rect (l, t, r, b): each window `size` = (w, h) real
    pixels with `gap` = (x, y) pixels between them. A share `lit` of them is lit, always in the
    same hashed order (raise `lit` to light them one by one); `warm` of the lit ones are warm
    (other homes), the rest cold (screens). `dark` paints unlit panes (None = leave the wall).
    `people` 0..1: in lit windows at least 3x3 pixels, that share shows tiny dark silhouettes
    (one-pixel heads and shoulders at a table). `flicker` > 0: that share of cold windows changes
    brightness every few steps (a TV). Lit panes' energy on ctx.glow. Returns (xs, ys, on) of the
    window centres (local units) for reflections. About 1 ms for a few hundred windows."""
    t = getattr(ctx, "t", 0.0) if t is None else t
    canvas = ctx.canvas if canvas is None else canvas
    warm_color = look.WINDOW_WARM if warm_color is None else warm_color
    cold_color = look.WINDOW_COLD if cold_color is None else cold_color
    sw, sh = (size, size) if np.isscalar(size) else size
    gx, gy = (gap, gap) if np.isscalar(gap) else gap
    L = Layer(canvas, rect)
    if L.empty:
        return np.zeros(0), np.zeros(0), np.zeros(0, bool)
    l, tp, r, b = rect
    (x0,), (y0,) = L.to_ipx([l], [tp])
    (x1,), (y1,) = L.to_ipx([r], [b])
    nx = max(0, (x1 - x0 + gx) // (sw + gx))
    ny = max(0, (y1 - y0) // (sh + gy))
    if nx <= 0 or ny <= 0:
        return np.zeros(0), np.zeros(0), np.zeros(0, bool)
    ox = x0 + (x1 - x0 - (nx * (sw + gx) - gx)) // 2
    oy = y0 + gy // 2
    col, row = np.meshgrid(np.arange(nx), np.arange(ny))
    col, row = col.ravel(), row.ravel()
    ids = seed * 104729 + row * 997 + col
    on = H01(ids, 1) < lit
    is_warm = H01(ids, 2) < warm
    wx = ox + col * (sw + gx)
    wy = oy + row * (sh + gy)
    step = math.floor(t * 15.0 / 4.0)
    for i in range(len(ids)):
        sl = (slice(max(0, wy[i]), max(0, wy[i] + sh)), slice(max(0, wx[i]), max(0, wx[i] + sw)))
        if on[i]:
            c = warm_color if is_warm[i] else cold_color
            a = alpha
            if flicker > 0 and not is_warm[i] and H01(ids[i], 3) < flicker:
                a = alpha * (0.55 + 0.45 * H01(ids[i] * 31 + step, 4))
            L.rgb[sl] = np.asarray(c, np.float32) * a
            L.a[sl] = a
            if people > 0 and sw >= 3 and sh >= 3 and H01(ids[i], 5) < people:
                k = 1 + int(H01(ids[i], 6) * min(3, sw - 1))
                for j in range(k):
                    px_ = wx[i] + 1 + int((sw - 2) * (j + 0.5) / k)
                    for yy, xx in ((wy[i] + sh - 2, px_), (wy[i] + sh - 1, px_)):
                        if 0 <= yy < L.h and 0 <= xx < L.w:
                            L.rgb[yy, xx] = np.asarray(look.INK, np.float32) * alpha
                            L.a[yy, xx] = alpha
        elif dark is not None:
            L.rgb[sl] = np.asarray(dark, np.float32) * alpha
            L.a[sl] = alpha
    L.blit(canvas)
    cxs = (wx + L.ix0 + sw / 2) * PX
    cys = (wy + L.iy0 + sh / 2) * PX
    m = canvas.getTotalMatrix()
    import skia
    inv = skia.Matrix()
    m.invert(inv)
    lx = inv.getScaleX() * cxs + inv.getSkewX() * cys + inv.getTranslateX()
    ly = inv.getSkewY() * cxs + inv.getScaleY() * cys + inv.getTranslateY()
    g = getattr(ctx, "glow", None)
    if glow > 0 and g is not None and on.any():
        prims.draw_dots(g, lx[on & is_warm], ly[on & is_warm], PX * max(sw, sh) * 1.2, warm_color, alpha=glow * alpha,
                        additive=True)
    return lx, ly, on
