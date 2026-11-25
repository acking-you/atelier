"""The looming shapes in the fog: hanging speech-bubble signs full of thread scribble, tall bending
adult figures whose heads are lost in the cloud, and a thicket of jagged shards along the path.
Each is a baked, pre-blurred A8 mask with a soft inner gradient (half resolution), tinted a
little darker than the fog it stands in. Logical 1920x1080 units."""
from __future__ import annotations

import math

import numpy as np
import skia

from mv.engine import palette as P, prims

from hx.kit import look

H01, HS = prims.hash01, prims.hash_sym
R = 0.5                                        # bake resolution of the soft masks

# --------------------------------------------------------------------------- bubbles
BW, BH, BP = 440.0, 330.0, 50.0                # body box and padding (logical)


def _bubble_outline(v):
    cx, cy = BP + BW / 2, BP + BH * 0.42
    a, b = BW * 0.47, BH * 0.38
    n = 90
    ph = np.linspace(0, 2 * np.pi, n, endpoint=False)
    wob = 1.0 + 0.07 * (prims.value_noise(ph * 1.3 + v * 5.0, 40 + v) - 0.5) * 2 + 0.03 * np.sin(ph * 3 + v)
    sq = np.abs(np.cos(ph)) ** 0.25 * np.sign(np.cos(ph)), np.abs(np.sin(ph)) ** 0.35 * np.sign(np.sin(ph))
    xs = cx + a * wob * (0.55 * np.cos(ph) + 0.45 * sq[0])
    ys = cy + b * wob * (0.55 * np.sin(ph) + 0.45 * sq[1])
    path = prims.poly_path(xs, ys, True)
    # the tail, curling down to one side
    d = -1 if v % 2 else 1
    tx0 = cx + d * a * (0.15 + 0.12 * H01(v, 41))
    tail = skia.Path()
    tail.moveTo(tx0 - 34, cy + b * 0.75)
    tail.quadTo(tx0 + d * 10, cy + b * 1.25, tx0 + d * 70, cy + b * 1.55 + 18 * H01(v, 42))
    tail.quadTo(tx0 + d * 20, cy + b * 1.12, tx0 + 40, cy + b * 0.70)
    tail.close()
    path.addPath(tail)
    path.setFillType(skia.PathFillType.kWinding)
    return path, (cx, cy, a, b)


def _bubble_mask(v):
    w, h = int((BW + 2 * BP) * R), int((BH + 2 * BP + 60) * R)

    def draw(c):
        c.scale(R, R)
        path, (cx, cy, a, b) = _bubble_outline(v)
        p = prims.linear_paint((0, cy - b), (0, cy + b * 1.4), [(1, 1, 1)] * 3, alphas=[0.55, 0.78, 0.95])
        c.drawPath(path, p)
        # a paler inner face, so the sign reads as a thing with a front, not a hole
        inner = prims.radial_paint((cx - a * 0.15, cy - b * 0.2), a * 0.9, (1, 1, 1), 0.35, power=1.4)
        inner.setBlendMode(skia.BlendMode.kDstOut)
        c.drawPath(path, inner)
    return prims.sprite(("fog_bubble", v), w, h, draw, blur=5.0, alpha_only=True)


def _scribble_mask(v):
    w, h = int(BW + 2 * BP), int(BH + 2 * BP + 60)

    def draw(c):
        _p, (cx, cy, a, b) = _bubble_outline(v)
        rows = 3 + (v % 2)
        for r in range(rows):
            k = v * 31 + r
            fy = (r + 0.5) / rows * 2 - 1                       # -1..1
            half = a * 0.78 * math.sqrt(max(0.05, 1 - (fy * 0.85) ** 2)) * (0.75 + 0.25 * H01(k, 1))
            y0 = cy + fy * b * 0.66
            x0 = cx - half + a * 0.08 * HS(k, 2)
            n = 320
            u = np.linspace(0, 1, n)
            sp = 0.35 + 1.3 * prims.value_noise(u * 6 + k * 3.1, k + 11)          # uneven pace
            phase = np.cumsum(sp) / n * 2 * np.pi * (8 + 7 * H01(k, 3)) + k
            rr = (5.0 + 11.0 * prims.value_noise(u * 5 + k, k + 12)) * (0.8 + 0.4 * H01(k, 4))
            adv = np.cumsum(0.4 + prims.value_noise(u * 4 + k * 1.7, k + 13)) / n
            adv = adv / adv[-1]
            wob = (prims.value_noise(u * 3 + k, k + 7) - 0.5) * 22
            xs = x0 + 2 * half * adv + rr * 1.25 * np.cos(phase)
            ys = y0 + rr * np.sin(phase * (1.0 + 0.15 * np.sin(u * 7 + k))) + wob
            p = prims.stroke((1, 1, 1), 1.8 + 1.4 * H01(k, 5), alpha=0.85)
            c.drawPath(prims.poly_path(xs, ys), p)
            # a second thread crossing the first, fainter, as if written over
            if H01(k, 8) > 0.35:
                xs2 = x0 + 2 * half * (0.1 + 0.8 * adv) + rr * 0.9 * np.cos(phase * 0.7 + 2)
                ys2 = y0 + 6 + rr * 0.8 * np.sin(phase * 0.7 + 2) - wob * 0.6
                c.drawPath(prims.poly_path(xs2, ys2), prims.stroke((1, 1, 1), 1.4, alpha=0.5))
            # a knot of tangled thread at one end of some rows
            if H01(k, 6) > 0.45:
                kx = x0 + 2 * half * (0.85 + 0.1 * H01(k, 7))
                th = np.linspace(0, 2 * np.pi * 5, 120)
                kr = 10 + 8 * np.sin(th * 0.37 + k)
                c.drawPath(prims.poly_path(kx + kr * np.cos(th * 1.03), y0 + kr * 0.8 * np.sin(th)),
                           prims.stroke((1, 1, 1), 2.2, alpha=0.7))
    return prims.sprite(("fog_scribble", v), w, h, draw, blur=1.0, alpha_only=True)


# --------------------------------------------------------------------------- tall figures
FW, FH = 600.0, 1040.0                          # sprite box (logical); feet at (FX, FY)
FX, FY = 210.0, 990.0


def _capsule(path, x0, y0, x1, y1, r0, r1):
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    path.moveTo(x0 + nx * r0, y0 + ny * r0)
    path.lineTo(x1 + nx * r1, y1 + ny * r1)
    path.lineTo(x1 - nx * r1, y1 - ny * r1)
    path.lineTo(x0 - nx * r0, y0 - ny * r0)
    path.close()
    path.addCircle(x0, y0, r0)
    path.addCircle(x1, y1, r1)


def _figure_mask(v):
    """v = 0 crossed arms, 1 one pointing arm, 2 crossed arms, more hunched."""
    w, h = int(FW * R), int(FH * R)
    hunch = 0.0 if v < 2 else 1.0

    def draw(c):
        c.scale(R, R)
        path = skia.Path()
        path.setFillType(skia.PathFillType.kWinding)
        # legs
        _capsule(path, 192, 760, 182, FY - 6, 26, 15)
        _capsule(path, 246, 772, 266, FY - 6, 25, 14)
        path.addOval(skia.Rect.MakeLTRB(160, FY - 18, 214, FY + 2))
        path.addOval(skia.Rect.MakeLTRB(250, FY - 16, 302, FY + 4))
        # the long coat, bending forward from the hips
        sx, sy = 372 + 30 * hunch, 300 + 30 * hunch          # front shoulder
        coat = skia.Path()
        coat.moveTo(140, 800)
        coat.cubicTo(150, 690, 168, 600, 186, 540)            # back of the hip
        coat.cubicTo(205, 440, 250, 330, sx - 70, sy - 52)    # rounded back
        coat.quadTo(sx - 10, sy - 70, sx + 18, sy - 18)       # over the shoulder
        coat.cubicTo(sx + 10, sy + 70, 300, 470, 268, 560)    # chest to belly
        coat.cubicTo(262, 640, 280, 730, 292, 810)            # coat front to hem
        coat.quadTo(220, 826, 140, 800)
        coat.close()
        path.addPath(coat)
        # neck and head, pushed forward and down
        hx, hy = sx + 52 + 10 * hunch, sy - 70 + 20 * hunch
        _capsule(path, sx - 8, sy - 40, hx - 10, hy + 8, 26, 22)
        path.addOval(skia.Rect.MakeLTRB(hx - 44, hy - 50, hx + 44, hy + 46))
        if v in (0, 2):                                       # crossed arms: a bar with elbows
            _capsule(path, sx - 56, sy + 98, sx + 44, sy + 62, 30, 27)
            _capsule(path, sx - 40, sy + 70, sx + 36, sy + 104, 24, 22)
        else:                                                 # one arm pointing down and forward
            ex, ey = sx + 70, sy + 150
            hx2, hy2 = sx + 150, sy + 280
            _capsule(path, sx + 2, sy + 10, ex, ey, 26, 20)
            _capsule(path, ex, ey, hx2, hy2, 20, 15)
            _capsule(path, hx2, hy2, hx2 + 46, hy2 + 62, 9, 5)          # the finger
            path.addOval(skia.Rect.MakeLTRB(hx2 - 20, hy2 - 18, hx2 + 20, hy2 + 22))
            _capsule(path, sx - 60, sy + 60, sx - 20, sy + 220, 22, 16)  # the far arm hangs
        p = prims.linear_paint((0, 150), (0, FY), [(1, 1, 1)] * 6, positions=[0, 0.10, 0.2, 0.45, 0.8, 1.0],
                               alphas=[0.0, 0.35, 0.85, 0.95, 0.9, 0.65])
        c.drawPath(path, p)
        # the inner face: lighter toward the front edge so the mass is not a flat cut-out
        lite = prims.linear_paint((180, 0), (sx + 60, 0), [(1, 1, 1)] * 2, alphas=[0.0, 0.30])
        lite.setBlendMode(skia.BlendMode.kDstOut)
        c.drawPath(path, lite)
    return prims.sprite(("fog_figure", v, 2), w, h, draw, blur=4.0, alpha_only=True)


# --------------------------------------------------------------------------- shard thicket
SW, SH = 820.0, 640.0
SBY = 590.0                                     # base line of the thicket inside its box


def _shard_mask(v):
    w, h = int(SW * R), int(SH * R)

    def draw(c):
        c.scale(R, R)
        n = 10
        ids = np.arange(n) + v * 101
        order = np.argsort(H01(ids, 9))
        for j in order:
            k = int(ids[j])
            u = (j + 0.5) / n + 0.05 * HS(k, 1)
            bx = 70 + (SW - 140) * u
            tall = (0.35 + 0.65 * math.sin(math.pi * u) ** 0.8) * (0.45 + 0.55 * H01(k, 2))
            hh = 120 + 440 * tall
            lean = 0.50 * HS(k, 3) + 0.25 * (u - 0.5)
            wb = 46 + 90 * H01(k, 4)
            by = SBY + 18 * HS(k, 5)
            tx, ty = bx + math.sin(lean) * hh, by - math.cos(lean) * hh
            km = 0.45 + 0.25 * H01(k, 6)
            kx = bx + (tx - bx) * km + wb * 0.5 * HS(k, 7)
            ky = by + (ty - by) * km
            sh = skia.Path()
            sh.moveTo(bx - wb * 0.5, by + 10)
            sh.lineTo(kx - wb * 0.28, ky)
            sh.lineTo(kx - wb * 0.05, ky - wb * 0.35 * H01(k, 8))      # a notch
            sh.lineTo(tx, ty)
            sh.lineTo(kx + wb * 0.30, ky + wb * 0.2)
            sh.lineTo(bx + wb * 0.5, by + 10)
            sh.close()
            p = prims.linear_paint((0, ty), (0, by), [(1, 1, 1)] * 3, alphas=[0.55, 0.80, 0.95])
            c.drawPath(sh, p)
            # the lit facet: one side lighter
            fac = skia.Path()
            fac.moveTo(bx + wb * 0.05, by + 10)
            fac.lineTo(kx - wb * 0.05, ky - wb * 0.35 * H01(k, 8))
            fac.lineTo(tx, ty)
            fac.lineTo(kx + wb * 0.30, ky + wb * 0.2)
            fac.lineTo(bx + wb * 0.5, by + 10)
            fac.close()
            fp = prims.fill((0, 0, 0), 0.32, blend=skia.BlendMode.kDstOut)
            c.drawPath(fac, fp)
        # broken bits on the ground
        for m in range(9):
            k = v * 211 + m
            x = 40 + (SW - 80) * H01(k, 11)
            s = 10 + 22 * H01(k, 12)
            y = SBY + 6 + 14 * H01(k, 13)
            a = 6.283 * H01(k, 14)
            pts = [(x + s * math.cos(a), y + 0.4 * s * math.sin(a)),
                   (x + s * math.cos(a + 2.3), y + 0.4 * s * math.sin(a + 2.3) - s * 0.5),
                   (x + s * 0.7 * math.cos(a + 4.1), y + 0.4 * s * math.sin(a + 4.1))]
            c.drawPath(prims.poly_path([q[0] for q in pts], [q[1] for q in pts], True), prims.fill((1, 1, 1), 0.8))
    return prims.sprite(("fog_shards", v), w, h, draw, blur=1.6, alpha_only=True)


# --------------------------------------------------------------------------- placements
# kind 0 bubbles: (pivot x, hang length below PIVOT_Y, scale, tilt deg, variant, depth)
PIVOT_Y = -160.0
# kind 1 figures: (feet x, feet y, height px, facing, variant, depth)
# kind 2 shards:  (base x, base y, scale, flip, variant, depth)
LAYOUT = {
    "c1": {
        0: [(110, 430, 1.40, -9, 0, 0.55), (690, 335, 1.05, 7, 1, 0.35), (1580, 390, 1.25, 11, 2, 0.5),
            (1880, 560, 0.95, -6, 3, 0.7), (1010, 290, 0.78, -13, 1, 0.25)],
        1: [(250, 800, 640, 1, 0, 0.62), (1310, 742, 600, -1, 1, 0.55), (1750, 690, 470, -1, 2, 0.25)],
        2: [(300, 848, 0.85, 1, 0, 0.72), (860, 722, 0.36, -1, 3, 0.32), (1330, 738, 0.55, -1, 1, 0.45)],
    },
    "c2": {
        0: [(110, 480, 1.75, -11, 0, 0.7), (680, 400, 1.30, 9, 1, 0.5), (1640, 450, 1.55, 13, 2, 0.65),
            (1950, 660, 1.25, -8, 3, 0.8), (1060, 330, 1.00, -15, 1, 0.35)],
        1: [(360, 872, 700, 1, 0, 0.8), (1350, 836, 680, -1, 1, 0.75), (1810, 712, 520, -1, 2, 0.35)],
        2: [(380, 862, 1.15, 1, 0, 0.85), (600, 760, 0.50, -1, 3, 0.45), (1440, 780, 0.80, -1, 1, 0.55)],
    },
}


def tone(depth: float):
    """A little darker than the fog at that depth."""
    far = P.mix(look.FOG_PALE, look.FOG, 0.75)
    near = P.mix(look.FOG, look.FOG_DEEP, 0.66)
    return P.mix(far, near, depth)


VP = (960.0, 600.0)                             # where the shapes advance from


def back_out(u: float, s: float = 1.2) -> float:
    """Ease-out with a little overshoot (0 -> 1, peaking a few percent above 1)."""
    u = min(1.0, max(0.0, u)) - 1.0
    return 1.0 + (s + 1.0) * u ** 3 + s * u ** 2


def entry_times(layout: str, kind: int, t_on: float, stagger: float):
    return [t_on + stagger * j for j in range(len(LAYOUT[layout][kind]))]


def draw_kind(canvas, kind: int, layout: str, t: float, t_on: float, dur: float = 0.5, stagger: float = 0.0,
              sink: float = 0.0, sway: float = 1.0, grow: float = 0.09, bend: float = 0.0, reach: float = 0.18,
              sway_t: float | None = None, fade: float = 1.0):
    """All instances of one kind. Instance j enters at t_on + j * stagger: it rises out of the fog
    over `dur` (ease-out with overshoot), from `reach` farther toward the vanishing point, then keeps
    slowly advancing and growing by `grow`; tall figures bend lower by `bend` degrees over their life.
    sink 0..1 = sunk back into the fog. sway_t is the clock of the swaying (wind-driven)."""
    st = t if sway_t is None else sway_t
    if fade <= 0.01:
        return
    for i, it in enumerate(LAYOUT[layout][kind]):
        life = t - (t_on + stagger * i)
        if life <= 0.0:
            continue
        seed = kind * 17 + i * 5 + (0 if layout == "c1" else 300)
        u = life / dur
        ei = min(1.0, u) ** 0.7
        m = back_out(u)
        adv = (1.0 - reach * (1.0 - m)) * (1.0 + grow * (1.0 - math.exp(-life / 6.0)))
        depth = it[-1]
        col = tone(depth)
        al = (0.70 + 0.28 * depth) * ei * (1.0 - 0.42 * sink) * fade
        if al <= 0.01:
            continue

        def place(x, y):
            return VP[0] + (x - VP[0]) * adv, VP[1] + (y - VP[1]) * adv
        if kind == 0:
            px, L, sc, tilt, v, _d = it
            th = math.radians(sway * (3.0 * math.sin(0.55 * st + seed) + 1.6 * math.sin(1.13 * st + 2 * seed)))
            L2 = L - (1 - min(1.0, m)) * 120 - sink * 70
            bx, by = px + L2 * math.sin(th), PIVOT_Y + L2 * math.cos(th)
            ppx, ppy = place(px, PIVOT_Y)
            bx, by = place(bx, by)
            canvas.drawLine(ppx, ppy, bx, by, prims.stroke(col, 1.6, alpha=al * 0.5))
            rot = tilt + math.degrees(th) * 1.6 + sway * 2.0 * math.sin(0.8 * st + seed * 3)
            m_, s_ = _bubble_mask(v), _scribble_mask(v)
            ax = (BP + BW / 2) / (BW + 2 * BP)
            ay = (BP + 0.04 * BH) / (BH + 2 * BP + 60)
            canvas.save()
            canvas.translate(bx, by)
            canvas.rotate(rot)
            canvas.scale(sc * adv, sc * adv)
            prims.draw_image(canvas, m_, 0, 0, scale=1 / R, alpha=al, anchor=(ax, ay), color=col)
            prims.draw_image(canvas, s_, 0, 0, scale=1.0, alpha=al * 0.55, anchor=(ax, ay),
                             color=P.mix(col, look.INK, 0.35))
            canvas.restore()
        elif kind == 1:
            x, y, hgt, facing, v, _d = it
            sc = hgt / (FY - 120) * adv
            lean = bend * (1.0 - math.exp(-life / 5.0)) + 6.0 * (1.0 - min(1.0, m))
            rot = (sway * (1.4 * math.sin(0.31 * st + seed) + 0.6 * math.sin(0.71 * st + seed * 2)) + lean) * facing
            x, y = place(x, y)
            canvas.save()
            canvas.translate(x, y + sink * 50)
            canvas.rotate(rot)
            canvas.scale(sc * facing, sc * (0.82 + 0.18 * m))
            look.shadow(canvas, 40, 0, 220, alpha=0.22 * al, color=look.FOG_DEEP, squash=0.15)
            prims.draw_image(canvas, _figure_mask(v), 0, 0, scale=1 / R, alpha=al,
                             anchor=(FX / FW, FY / FH), color=col)
            canvas.restore()
        else:
            x, y, sc, flip, v, _d = it
            rot = sway * 0.8 * math.sin(0.4 * st + seed)
            x, y = place(x, y)
            canvas.save()
            canvas.translate(x, y + sink * 35)
            canvas.rotate(rot)
            canvas.scale(sc * adv * flip, sc * adv * max(0.05, m) * (1.0 - 0.12 * sink))
            prims.draw_image(canvas, _shard_mask(v), 0, 0, scale=1 / R, alpha=al,
                             anchor=(0.5, SBY / SH), color=col)
            canvas.restore()
