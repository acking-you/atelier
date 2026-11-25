"""The fog plain: a low horizon, three receding ground planes baked once, a faint worn path,
dead grass tufts, leaning posts, and the far lit doorway. Logical 1920x1080 units."""
from __future__ import annotations

import math

import numpy as np
import skia

from mv.engine import palette as P, prims
from mv.engine.palette import sk

from hx.kit import look

W, H = 1920, 1080
HZ = 648.0                                    # horizon
H01, HS = prims.hash01, prims.hash_sym

# the worn path: front-left to the right distance (cubic Bezier), sampled with arc length
_B = np.array([(150.0, 1140.0), (640.0, 850.0), (1000.0, 708.0), (1580.0, 652.0)])
_u = np.linspace(0.0, 1.0, 600)[:, None]
PATH = ((1 - _u) ** 3 * _B[0] + 3 * (1 - _u) ** 2 * _u * _B[1] + 3 * (1 - _u) * _u ** 2 * _B[2] + _u ** 3 * _B[3])
_seg = np.hypot(*np.diff(PATH, axis=0).T)
ARC = np.concatenate([[0.0], np.cumsum(_seg)])


def path_at(arc: float):
    """(x, y) on the path centre at arc length `arc` px from the front end."""
    return float(np.interp(arc, ARC, PATH[:, 0])), float(np.interp(arc, ARC, PATH[:, 1]))


def arc_at_x(x: float) -> float:
    return float(np.interp(x, PATH[:, 0], ARC))


def path_width(y):
    return np.maximum(2.0, 0.60 * (np.asarray(y, float) - HZ + 2.0))


def depth_scale(y: float) -> float:
    """Perspective scale of something standing at ground y (1 at y = 735)."""
    return max(0.05, (y - HZ + 8.0) / (735.0 - HZ + 8.0))


# --------------------------------------------------------------------------- planes
GROUND_FAR = P.mix(look.FOG_PALE, look.FOG, 0.30)
_PLANES = (
    # top y, undulation amp, noise freq, colour at top, colour at bottom, seed
    (HZ - 1.0, 3.0, 2.0, P.mix(look.FOG_PALE, look.FOG, 0.18), P.mix(look.FOG, look.FOG_DEEP, 0.15), 1),
    (684.0, 16.0, 3.1, P.mix(look.FOG_PALE, look.FOG, 0.55), P.mix(look.FOG, look.FOG_DEEP, 0.35), 2),
    (846.0, 26.0, 2.3, P.mix(look.FOG, look.FOG_DEEP, 0.25), P.mix(look.FOG, look.FOG_DEEP, 0.62), 3),
)
POSTS = (  # x, base y, height, lean (rad, + right), seed
    (402.0, 838.0, 118.0, 0.10, 1), (742.0, 772.0, 64.0, -0.13, 2), (1228.0, 694.0, 30.0, 0.06, 3),
    (1318.0, 680.0, 20.0, -0.16, 4), (1712.0, 705.0, 46.0, 0.19, 5), (176.0, 742.0, 74.0, -0.07, 6),
)


def plane_top(i: int, xs):
    y0, amp, fq, _c0, _c1, sd = _PLANES[i]
    xs = np.asarray(xs, float)
    n = prims.value_noise(xs / W * fq * 4.0, sd * 13) - 0.5
    n2 = prims.value_noise(xs / W * fq * 11.0, sd * 13 + 5) - 0.5
    y = y0 + amp * (1.6 * n + 0.5 * n2)
    if i == 2:                                     # the near rise lifts toward the left
        y = y - 40.0 * np.clip(1.0 - xs / 900.0, 0, 1) ** 2
    return y


def _tuft(c, x, y, s, seed, color, alpha):
    n = 3 + int(H01(seed, 1) * 5)
    for k in range(n):
        kk = seed * 11 + k
        lean = 0.55 * HS(kk, 2) + 0.25
        ln = s * (0.45 + 0.75 * H01(kk, 3))
        bx = x + s * 0.25 * HS(kk, 4)
        wd = max(0.7, s * 0.06 * (0.7 + 0.6 * H01(kk, 5)))
        tx = bx + math.sin(lean) * ln
        ty = y - math.cos(lean) * ln
        mx = bx + math.sin(lean * 0.4) * ln * 0.55
        my = y - ln * 0.6
        path = skia.Path()
        path.moveTo(bx - wd, y)
        path.quadTo(mx - wd * 0.5, my, tx, ty)
        path.quadTo(mx + wd * 0.5, my, bx + wd, y)
        path.close()
        c.drawPath(path, prims.fill(P.shade(color, -0.04 + 0.06 * H01(kk, 6)), alpha * (0.6 + 0.4 * H01(kk, 7))))


def _post(c, x, y, h, lean, seed, color, alpha):
    w = max(2.0, h * 0.085)
    ca, sa = math.cos(lean), math.sin(lean)
    tx, ty = x + sa * h, y - ca * h
    bend = h * 0.04 * HS(seed, 9)
    # broken top: jagged
    j1 = h * 0.06 * (0.4 + H01(seed, 10))
    path = skia.Path()
    path.moveTo(x - w * 0.55, y + 1)
    path.quadTo((x + tx) / 2 - w * 0.5 + bend, (y + ty) / 2, tx - w * 0.42, ty + j1)
    path.lineTo(tx - w * 0.05, ty)
    path.lineTo(tx + w * 0.15, ty + j1 * 0.6)
    path.lineTo(tx + w * 0.42, ty + j1 * 1.3)
    path.quadTo((x + tx) / 2 + w * 0.5 + bend, (y + ty) / 2, x + w * 0.6, y + 1)
    path.close()
    look.shadow(c, x + w * 0.8, y + 1, w * 5.0, alpha=0.35 * alpha, color=look.FOG_DEEP, squash=0.22)
    c.drawPath(path, prims.linear_paint((tx, ty), (x, y), [P.shade(color, 0.05), color, P.shade(color, -0.06)],
                                        alpha=alpha))
    # a stub of a crossbar on the tall ones
    if h > 60:
        yy = y - h * (0.62 + 0.1 * H01(seed, 11))
        xx = x + sa * (y - yy)
        d = 1 if H01(seed, 12) > 0.5 else -1
        bar = skia.Path()
        bar.moveTo(xx, yy - w * 0.3)
        bar.lineTo(xx + d * h * 0.22, yy + h * 0.05 - w * 0.2)
        bar.lineTo(xx + d * h * 0.21, yy + h * 0.05 + w * 0.25)
        bar.lineTo(xx, yy + w * 0.45)
        bar.close()
        c.drawPath(bar, prims.fill(color, alpha * 0.9))


def _bake_plane(i: int):
    y0, amp, _fq, c0, c1, sd = _PLANES[i]
    top = int(y0 - amp * 2.0 - 60.0) if i < 2 else int(y0 - amp * 2.0 - 110.0)
    hh = H - top + 4

    def draw(c):
        c.translate(0, -top)
        xs = np.linspace(-20, W + 20, 160)
        ys = plane_top(i, xs)
        shape = skia.Path()
        shape.moveTo(-20, H + 10)
        for x, y in zip(xs.tolist(), ys.tolist()):
            shape.lineTo(x, y)
        shape.lineTo(W + 20, H + 10)
        shape.close()
        p = prims.linear_paint((0, y0 - amp), (0, H), [c0, P.mix(c0, c1, 0.6), c1])
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.0 + 3.0 * (2 - i)))
        c.drawPath(shape, p)
        c.save()
        c.clipPath(shape, skia.ClipOp.kIntersect, True)
        # a lighter fog-lit lip along the plane's top edge
        lip = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=18.0 + 10 * i,
                         Color=sk(look.FOG_PALE, 0.22 - 0.05 * i))
        lip.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9.0))
        lipath = skia.Path()
        lipath.addPoly([skia.Point(x, y + 6) for x, y in zip(xs.tolist(), ys.tolist())], False)
        c.drawPath(lipath, lip)
        look.mottle(c, (-20, top, W + 20, H), alpha=0.16, scale=1.0 + 0.4 * i, seed=sd)
        # the worn path: a chain of soft pale patches, wider near, broken here and there
        pl = P.mix(c0, look.FOG_LIGHT, 0.35)
        ids = np.arange(900) + 1000 * i
        a = ARC[-1] * np.sort(H01(ids, 21))
        px = np.interp(a, ARC, PATH[:, 0])
        py = np.interp(a, ARC, PATH[:, 1])
        wd = path_width(py)
        keep = py > top
        img = prims.soft_disc(64, 0.35)
        for x, y, w_, k, a_ in zip(px[keep], py[keep], wd[keep], ids[keep], a[keep]):
            al = (0.10 + 0.25 * H01(k, 22) ** 1.5) * min(1.0, 10.0 / w_) * (0.15 if prims.value_noise(a_ / 90.0, 77) < 0.42 else 1.0)
            prims.draw_image(c, img, x + w_ * 0.22 * HS(k, 24), y + w_ * 0.04 * HS(k, 25),
                             scale=w_ * (0.7 + 0.5 * H01(k, 26)) / 64.0, scale_y=w_ * 0.2 / 64.0,
                             alpha=al, color=pl)
        # two faint ruts
        for side in (-1, 1):
            rx = px + side * wd * 0.22
            rut = prims.poly_path(rx[keep], py[keep] + 1.0)
            rp = prims.stroke(P.shade(c0, -0.05), 1.0, alpha=0.10)
            c.drawPath(rut, rp)
        c.restore()
        # dead grass tufts, sparse, off the path, sized by depth
        n = (60, 90, 50)[i]
        tid = np.arange(n) + 5000 * (i + 1)
        tx = -40 + (W + 80) * H01(tid, 31)
        yt = plane_top(i, tx)
        yb = (plane_top(i + 1, tx) if i < 2 else np.full(n, H + 40.0))
        ty = yt + 8 + (yb - yt) * H01(tid, 32) ** 1.4
        for x, y, k in zip(tx.tolist(), ty.tolist(), tid.tolist()):
            if abs(x - float(np.interp(y, PATH[::-1, 1], PATH[::-1, 0]))) < float(path_width(y)) * 0.9:
                continue
            if i == 2 and y > 900 and H01(k, 33) < 0.6:      # keep the lyric band calm
                continue
            s = 26.0 * depth_scale(y) * (0.6 + 0.8 * H01(k, 34))
            _tuft(c, x, y, s, k, P.shade(P.mix(c0, c1, (y - y0) / (H - y0)), -0.09), 0.55 if y < 900 else 0.35)
        for (x, y, h, lean, s) in POSTS:
            if (i == 1 and 684 <= y < 846) or (i == 0 and y < 684 and y >= HZ):
                fogk = 1.0 - min(1.0, (y - HZ) / 200.0)
                col = P.mix(P.mix(look.FOG_DEEP, look.INDIGO, 0.3), c0, 0.55 * fogk)
                _post(c, x, y, h, lean, s, col, 0.9 - 0.3 * fogk)

    img = prims.sprite(("fog_plane", i, 6), W, hh, draw)
    return img, top


def draw_planes(canvas, which, dy: float = 0.0):
    for i in which:
        img, top = _bake_plane(i)
        canvas.drawImage(img, 0, top + dy, prims.LINEAR, None)


def sky(canvas, dy: float, top_extra: float = 0.0, pale: float = 0.0, lid=None):
    """The fog behind the cloud lid, brightest at the horizon. pale lifts it toward a white-out.
    lid = (underside y, colour): above the underside the backdrop takes the lid's own colour, so no
    seam of the lid can ever show light through."""
    cols = [P.mix(look.FOG_DEEP, look.FOG, 0.4), look.FOG, P.mix(look.FOG, look.FOG_PALE, 0.7),
            P.mix(look.FOG_PALE, look.FOG_LIGHT, 0.45)]
    if pale > 0:
        cols = [P.mix(c, look.FOG_LIGHT, pale) for c in cols]
    prims.fill_rect_gradient(canvas, (-10, -top_extra + dy, W + 10, HZ + 30 + dy), cols, [0.0, 0.45, 0.8, 1.0])
    if lid is not None:
        y, col = lid
        prims.fill_rect_gradient(canvas, (-10, -top_extra + dy, W + 10, y + dy), [col, col, col],
                                 [0.0, 0.9, 1.0], alpha=1.0)


# --------------------------------------------------------------------------- the far doorway
DOOR = (640.0, HZ + 3.0)                     # foot of the doorway, far back-left


def doorway_house(canvas, dy: float, alpha: float):
    """A small dim cottage shape (inside the grade, veiled by fog)."""
    if alpha <= 0.01:
        return
    x, y = DOOR[0], DOOR[1] + dy
    col = P.mix(look.FOG, look.FOG_PALE, 0.25)
    path = skia.Path()
    path.moveTo(x - 46, y)
    path.lineTo(x - 44, y - 40)
    path.lineTo(x - 18, y - 64)
    path.lineTo(x + 12, y - 41)
    path.lineTo(x + 24, y - 42)
    path.lineTo(x + 25, y)
    path.close()
    p = prims.fill(col, alpha * 0.85)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.6))
    canvas.drawPath(path, p)


def doorway_light(ctx, dy: float, alpha: float):
    """The lit door itself, warm, outside the grade, with its spill on the ground and on glow."""
    if alpha <= 0.01:
        return
    x, y = DOOR[0] - 6, DOOR[1] + dy
    c = ctx.canvas
    warm = P.mix(look.AMBER, look.PAPER, 0.25)
    c.save()
    c.translate(x, y + 2)
    c.scale(1.0, 0.22)
    prims.glow(c, 0, 0, 70, look.AMBER, alpha * 0.30)
    c.restore()
    prims.glow(c, x, y - 12, 40, look.AMBER, alpha * 0.22)
    door = skia.Path()
    door.moveTo(x - 6, y)
    door.lineTo(x - 6, y - 19)
    door.quadTo(x, y - 23, x + 6, y - 19)
    door.lineTo(x + 6, y)
    door.close()
    p = prims.fill(warm, alpha)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 0.8))
    c.drawPath(door, p)
    prims.glow(ctx.glow, x, y - 10, 34, look.AMBER, alpha * 0.55)


# --------------------------------------------------------------------------- streaming fog sheets
SHEET_W, SHEET_H = 2048, 256
_SHEET_PAINTS: dict = {}


def _sheet_paint(k: int):
    """A seamless (in x) A8 texture of long torn fog wisps, as a repeating shader paint (baked once)."""
    p = _SHEET_PAINTS.get(k)
    if p is not None:
        return p

    def draw(c):
        n = 150
        ids = np.arange(n) + 7000 * (k + 1)
        for x, y, rx, ry, a in zip((SHEET_W * H01(ids, 1)).tolist(), (40 + 176 * H01(ids, 2) ** 1.2).tolist(),
                                   (40 + 130 * H01(ids, 3) ** 1.5).tolist(), (12 + 34 * H01(ids, 4) ** 1.5).tolist(),
                                   (0.25 + 0.6 * H01(ids, 5)).tolist()):
            for dx in (-SHEET_W, 0, SHEET_W):
                c.drawOval(skia.Rect.MakeLTRB(x + dx - rx, y - ry, x + dx + rx, y + ry), prims.fill((1, 1, 1), a))
    rgba = np.zeros((SHEET_H, SHEET_W, 4), np.uint8)
    surf = skia.Surface(rgba)
    c = surf.getCanvas()
    lp = skia.Paint()
    lp.setImageFilter(skia.ImageFilters.Blur(7.0, 5.0, skia.TileMode.kRepeat))
    c.saveLayer(None, lp)
    draw(c)
    c.restore()
    surf.flushAndSubmit()
    arr = rgba[..., 3].astype(np.float64)
    yy = np.arange(SHEET_H)[:, None] / (SHEET_H - 1)
    env = np.sin(np.pi * yy) ** 1.2                     # soft top and bottom
    img = prims.mask_image((arr * env).astype(np.uint8))
    p = skia.Paint(AntiAlias=True)
    p.setShader(img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kDecal, prims.LINEAR))
    _SHEET_PAINTS[k] = p
    return p


def sheet(canvas, rect, clock: float, speed: float, color, alpha: float, seed: int = 0, stretch: float = 1.0):
    """A sheet of fog wisps filling rect, streaming leftward at `speed` px per unit of `clock`."""
    if alpha <= 0.004:
        return
    l, tp, r, b = rect
    p = _sheet_paint(seed % 3)
    p.setColor(sk(color, alpha))
    sy = (b - tp) / SHEET_H
    sx = sy * 1.1 * stretch
    off = (-speed * clock + H01(seed, 9) * SHEET_W * sx) % (SHEET_W * sx)
    canvas.save()
    canvas.translate(off, tp)
    canvas.scale(sx, sy)
    canvas.drawRect(skia.Rect.MakeLTRB((l - off) / sx, 0, (r - off) / sx, SHEET_H), p)
    canvas.restore()
