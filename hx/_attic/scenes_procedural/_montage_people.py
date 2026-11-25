"""Faceless cut-paper passers-by and pupils: tapered grey silhouettes, paler than the child, varied
in height, build and gait. They never look anywhere but ahead."""
from __future__ import annotations

import math

import skia

from hx.kit import look
from mv.engine import palette as P
from mv.engine import prims

from ._montage_paper import H01, HS, smooth_closed

PI2 = 2 * math.pi


def _taper(x0, y0, x1, y1, w0, w1):
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) + 1e-9
    nx, ny = -dy / ln, dx / ln
    p = skia.Path()
    p.moveTo(x0 + nx * w0, y0 + ny * w0)
    p.lineTo(x1 + nx * w1, y1 + ny * w1)
    p.quadTo(x1 + dx / ln * w1 * 1.2, y1 + dy / ln * w1 * 1.2, x1 - nx * w1, y1 - ny * w1)
    p.lineTo(x0 - nx * w0, y0 - ny * w0)
    p.close()
    return p


def build(seed: int, kid: bool | None = None):
    """Stable traits of figure `seed`."""
    kid = (H01(seed, 1) < 0.35) if kid is None else kid
    return dict(
        kid=kid,
        coat=H01(seed, 2) < 0.6,
        hat=(not kid) and H01(seed, 3) < 0.3,
        bag=kid and H01(seed, 4) < 0.85 or (not kid and H01(seed, 5) < 0.3),
        tail=kid and H01(seed, 6) < 0.4,
        wide=0.85 + 0.35 * H01(seed, 7),
        lean=0.04 + 0.08 * H01(seed, 8),
        swing=0.28 + 0.18 * H01(seed, 9),
        tone=HS(seed, 10),
    )


def draw(c, x, y, h, phase, seed, col, facing=1, alpha=1.0, tr=None, shadow=0.28, stand=0.0):
    """Figure with its feet at (x, y), height h px, gait phase (0..1 = two steps), colour col.
    stand 0..1 settles the legs together."""
    if alpha <= 0.01:
        return
    tr = tr or build(seed)
    kid = tr["kid"]
    hip, sh = (0.43, 0.72) if kid else (0.48, 0.81)
    hr = 0.088 if kid else 0.060
    hy = sh + hr * 1.15
    wd = tr["wide"]
    col = P.shade(col, 0.04 * tr["tone"])
    dark = P.shade(col, -0.07)
    if shadow > 0:
        look.shadow(c, x, y + 2, h * 0.36 * wd, shadow * alpha)
    layer = alpha < 0.99
    if layer:
        c.saveLayerAlpha(None, int(255 * alpha))
    c.save()
    c.translate(x, y)
    c.scale(h * facing, h)
    c.skew(-tr["lean"] * (1 - 0.6 * stand), 0)
    paint = prims.linear_paint((0, -1.0), (0, 0), [P.shade(col, 0.07), col, P.shade(col, -0.05)], [0, 0.4, 1], n=6)
    dpaint = prims.fill(dark)
    a = tr["swing"] * math.sin(PI2 * phase) * (1 - stand)
    lift = 0.025 * max(0.0, math.sin(PI2 * phase + 1.2)) * (1 - stand)
    legw0, legw1 = 0.045 * wd, 0.024
    for side, ang, lf, pnt in ((-1, -a, 0.025 * max(0.0, -math.sin(PI2 * phase + 1.2)) * (1 - stand), dpaint),
                               (1, a, lift, None)):
        fx = hip * math.sin(ang) + 0.012 * side
        fy = -lf
        if pnt is not None:
            c.drawPath(_taper(0.012 * side, -hip, fx, fy - 0.01, legw0, legw1), pnt)
            c.drawOval(skia.Rect.MakeLTRB(fx - 0.02, fy - 0.028, fx + 0.06, fy + 0.002), pnt)
            # far arm
            b = 0.55 * ang
            ex, ey = 0.30 * math.sin(-b) - 0.01, -sh + 0.01 + 0.30 * math.cos(b)
            c.drawPath(_taper(-0.01, -sh + 0.02, ex, ey, 0.03 * wd, 0.018), pnt)
    if tr["bag"]:
        bw = 0.10 if kid else 0.07
        c.drawPath(smooth_closed([(-0.06 * wd - bw, -sh + 0.02), (-0.04 * wd, -sh + 0.04), (-0.04 * wd, -hip - 0.03),
                                  (-0.06 * wd - bw * 0.9, -hip - 0.01)]), dpaint)
    hem = 0.36 if (tr["coat"] and not kid) else hip - 0.02
    flare = 0.11 if tr["coat"] else 0.075
    torso = smooth_closed([(-0.075 * wd, -sh + 0.01), (0.0, -sh - 0.015), (0.08 * wd, -sh + 0.01),
                           (0.07 * wd, -(sh + hem) / 2), (flare * wd, -hem), (0.0, -hem + 0.012),
                           (-flare * wd * 0.95, -hem), (-0.07 * wd, -(sh + hem) / 2)])
    # near leg
    fx = hip * math.sin(a) + 0.012
    c.drawPath(_taper(0.012, -hip, fx, -lift - 0.01, legw0, legw1), paint)
    c.drawOval(skia.Rect.MakeLTRB(fx - 0.02, -lift - 0.028, fx + 0.06, -lift + 0.002), paint)
    c.drawPath(torso, paint)
    c.drawPath(_taper(0.0, -sh, 0.008, -sh - hr * 0.6, 0.022, 0.02), paint)
    c.drawOval(skia.Rect.MakeLTRB(-hr + 0.012, -hy - hr * 1.12, hr + 0.012, -hy + hr * 1.05), paint)
    if tr["hat"]:
        c.drawPath(smooth_closed([(-hr * 1.6, -hy - hr * 0.35), (0.0, -hy - hr * 0.55), (hr * 1.7, -hy - hr * 0.3),
                                  (hr * 0.8, -hy - hr * 1.5), (-hr * 0.8, -hy - hr * 1.5)]), dpaint)
    if tr["tail"]:
        c.drawPath(smooth_closed([(-hr * 0.8, -hy - hr * 0.2), (-hr * 1.7, -hy + hr * 0.3), (-hr * 1.4, -hy + hr * 0.9),
                                  (-hr * 0.7, -hy + hr * 0.3)]), dpaint)
    # near arm
    b = -0.55 * a
    ex, ey = 0.30 * math.sin(b) + 0.01, -sh + 0.01 + 0.30 * math.cos(b)
    c.drawPath(_taper(0.01, -sh + 0.02, ex, ey, 0.032 * wd, 0.019), paint)
    c.restore()
    if layer:
        c.restore()


def eased_beats(tl, t, ease: float = 0.62):
    """Beats as a monotone clock that moves in one eased shove per beat."""
    k, f = tl.beat_at(t)
    g = min(1.0, f / ease)
    return k + g * g * (3 - 2 * g)
