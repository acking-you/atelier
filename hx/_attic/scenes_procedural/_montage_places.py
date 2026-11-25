"""The places of the montage: each is two baked cut-paper planes (a hazy far plane at half resolution
that scrolls slowly, and a near plane at full resolution) plus where its lamp hangs.

Near-plane coordinates run 0..NW; the screen shows near x = scroll .. scroll + 1920. The child's feet
stand on GY. Desks, windows and posts are placed by hash, never on a grid.
"""
from __future__ import annotations

import math

import skia

from hx.kit import look
from mv.engine import palette as P
from mv.engine import prims

from ._montage_paper import H01, HS, blob, cut_poly, cut_rect, flat, haze, hex_rgb, scribble, shape, smooth_closed

W, H = 1920, 1080
NW, FW = 2400, 2200          # near / far plane widths (logical px)
GY = 838                     # the ground line the child stands on
BASE = 200                   # default scroll (near x at the screen's left edge)
FAR_K = 0.35                 # far plane parallax


def _poly(pts):
    return cut_poly(pts, 0, 0.0)


# ------------------------------------------------------------------------------------------------
# props
# ------------------------------------------------------------------------------------------------
def desk(c, x, base, s, seed, top=hex_rgb("B89A72"), body=hex_rgb("8E7458"), chair=hex_rgb("66727E"),
         stack=False):
    w = (165 + 30 * HS(seed, 1)) * s
    tilt = 2.5 * HS(seed, 2) * s
    ty = base - 102 * s
    look.shadow(c, x, base + 2, w * 1.25, 0.32)
    # chair behind
    cx = x + (w * 0.18 + 10 * s) * (1 if H01(seed, 3) < 0.5 else -1)
    shape(c, cut_rect(cx - 34 * s, ty - 62 * s, cx + 34 * s, ty - 10 * s, seed + 5, 1.2, 3 * HS(seed, 4) * s),
          chair, 0.08, lift=2 * s)
    for lx in (cx - 28 * s, cx + 26 * s):
        shape(c, _poly([(lx - 3 * s, ty - 14 * s), (lx + 3 * s, ty - 14 * s), (lx + 2 * s, base - 8 * s),
                        (lx - 2 * s, base - 8 * s)]), P.shade(chair, -0.08), 0.0)
    # legs, box, top
    for lx in (x - w * 0.43, x + w * 0.41):
        shape(c, _poly([(lx - 5 * s, ty + 8), (lx + 5 * s, ty + 8), (lx + 3.5 * s, base), (lx - 3.5 * s, base)]),
              P.shade(body, -0.10), 0.03)
    shape(c, cut_rect(x - w * 0.46, ty + 10 * s, x + w * 0.46, ty + 46 * s, seed + 7, 1.0), body, 0.06, lift=3 * s)
    shape(c, cut_poly([(x - w / 2, ty - tilt), (x + w / 2, ty + tilt), (x + w / 2 - 3 * s, ty + 13 * s + tilt),
                       (x - w / 2 + 2 * s, ty + 13 * s - tilt)], seed + 9, 1.0), top, 0.10, lift=3 * s)
    if stack:
        sheets(c, x + w * (0.18 * HS(seed, 11)), ty - 2 * s, 46 * s, seed + 13, int(2 + 4 * H01(seed, 12)))


def sheets(c, x, y, w, seed, n=4, col=hex_rgb("E8E3D6")):
    """A small stack of exam sheets: blank, with ruled marks only."""
    for i in range(n):
        dx = 4 * HS(seed + i, 21) * w / 50
        yy = y - i * 2.2 * w / 50
        rot = 5 * HS(seed + i, 22)
        c.save()
        c.translate(x + dx, yy)
        c.rotate(rot)
        c.scale(1, 0.32)
        shape(c, cut_rect(-w / 2, -w * 0.7, w / 2, w * 0.7, seed + i, 0.6), P.shade(col, -0.03 * (n - i)), 0.03,
              lift=2)
        if i == n - 1:
            pr = prims.stroke(hex_rgb("8E96A3"), 1.4, 0.45)
            for k in range(5):
                yk = -w * 0.5 + k * w * 0.22
                c.drawLine(-w * 0.38, yk, w * (0.15 + 0.25 * H01(seed + k, 23)), yk, pr)
        c.restore()


def tree(c, x, base, s, seed, col=hex_rgb("5E7560"), trunk=hex_rgb("4C4440"), alpha=1.0):
    shape(c, _poly([(x - 9 * s, base), (x + 9 * s, base), (x + 4 * s, base - 170 * s), (x - 5 * s, base - 170 * s)]),
          trunk, 0.05, alpha)
    for k in range(5):
        a = HS(seed + k, 61)
        bx = x + a * 70 * s
        by = base - (200 + 60 * H01(seed + k, 62)) * s
        r = (70 + 30 * H01(seed + k, 63)) * s
        shape(c, blob(bx, by, r * 1.15, r * 0.9, seed + k, 0.14), P.shade(col, 0.04 * k - 0.06), 0.09, alpha,
              lift=4 * s)


def lamp_post(c, x, base, head_y, s, seed, col=hex_rgb("2A3044"), shade_col=hex_rgb("3B4257"), lit=0.4,
              light=hex_rgb("E9DDB8")):
    """Post, a curved arm reaching left, a hooded head. Returns the head's light point."""
    shape(c, _poly([(x - 11 * s, base), (x + 11 * s, base), (x + 6 * s, head_y + 10), (x - 5 * s, head_y + 10)]),
          col, 0.10, lift=4)
    shape(c, cut_rect(x - 18 * s, base - 46 * s, x + 18 * s, base, seed, 1.0), P.shade(col, 0.04), 0.06)
    hx = x - 70 * s
    arm = skia.Path()
    arm.moveTo(x - 5 * s, head_y + 12)
    arm.quadTo(x - 6 * s, head_y - 34 * s, hx, head_y - 22 * s)
    c.drawPath(arm, prims.stroke(col, 8 * s))
    lx, ly = hx, head_y - 6 * s
    if lit > 0:
        prims.glow(c, lx, ly + 10, 150 * s, light, 0.35 * lit, 2.0)
        prims.glow(c, lx, base, 240 * s, light, 0.12 * lit, 1.6)
    shape(c, smooth_closed([(lx - 30 * s, ly), (lx - 14 * s, ly - 24 * s), (lx + 14 * s, ly - 24 * s), (lx + 30 * s, ly),
                            (lx, ly + 6 * s)]), shade_col, 0.08, lift=2)
    c.drawOval(skia.Rect.MakeLTRB(lx - 16 * s, ly - 4 * s, lx + 16 * s, ly + 10 * s),
               prims.fill(P.mix(shade_col, light, 0.3 + 0.6 * lit)))
    return (lx, ly + 6 * s)


def building(c, l, r, top, bot, seed, col, win=None, win_alpha=0.6, lit=()):
    shape(c, cut_rect(l, top, r, bot, seed, 1.4), col, 0.06)
    if win is None:
        return
    y = top + 26 + 10 * H01(seed, 71)
    row = 0
    while y < bot - 50:
        x = l + 18 + 14 * H01(seed + row, 72)
        k = 0
        while x < r - 40:
            ww = 20 + 14 * H01(seed * 13 + row * 7 + k, 73)
            hh = 26 + 10 * H01(seed * 13 + row * 7 + k, 74)
            if H01(seed * 13 + row * 7 + k, 75) > 0.18:
                on = (seed * 13 + row * 7 + k) % 11 in lit
                colw = P.mix(win, hex_rgb("E8C988"), 0.75) if on else win
                flat(c, cut_rect(x, y, x + ww, y + hh, seed + row * 9 + k, 0.8), colw, win_alpha + (0.25 if on else 0))
            x += ww + 18 + 22 * H01(seed * 5 + row * 3 + k, 76)
            k += 1
        y += 58 + 22 * H01(seed + row, 77)
        row += 1


def floor(c, top, cols, seed, edge=None):
    l, r = -20, NW + 20
    shape(c, cut_poly([(l, top + 3 * HS(seed, 81)), (r, top + 3 * HS(seed, 82)), (r, H + 20), (l, H + 20)], seed, 2.0),
          cols[0], 0.0)
    c.drawRect(skia.Rect.MakeLTRB(l, top, r, H + 20),
               prims.linear_paint((0, top), (0, H), list(cols), None, 1.0, n=10))
    if edge is not None:
        flat(c, cut_rect(l, top - 6, r, top + 6, seed + 3, 1.2), edge, 0.9)


# ------------------------------------------------------------------------------------------------
# places
# ------------------------------------------------------------------------------------------------
def classroom_far(c):
    prims.fill_rect_gradient(c, (0, 0, FW, H), [hex_rgb("7D877C"), hex_rgb("A9B2A2"), hex_rgb("9EA796")],
                             [0, 0.45, 1])
    flat(c, cut_rect(-10, 560, FW + 10, 720, 3, 1.5), hex_rgb("7F8B7C"), 1.0)
    xs = [70, 330, 620]
    for i, x in enumerate(xs):
        w = 190 + 40 * H01(i, 91)
        t = 150 + 30 * H01(i, 92)
        b = 540 + 20 * H01(i, 93)
        prims.glow(c, x + w / 2, (t + b) / 2, 360, hex_rgb("E6E8DF"), 0.35, 1.6)
        shape(c, cut_rect(x - 10, t - 10, x + w + 10, b + 14, i + 40, 1.0), hex_rgb("8B8E86"), 0.05, lift=4)
        c.drawRect(skia.Rect.MakeLTRB(x, t, x + w, b),
                   prims.linear_paint((0, t), (0, b), [hex_rgb("E4E7DE"), hex_rgb("C9CFC6")], n=6))
        flat(c, cut_rect(x + w * 0.48, t, x + w * 0.52, b, i + 50, 0.4), hex_rgb("8B8E86"))
        flat(c, cut_rect(x, t + (b - t) * 0.38, x + w, t + (b - t) * 0.38 + 7, i + 60, 0.4), hex_rgb("8B8E86"))
    # blackboard
    shape(c, cut_rect(930, 238, 1690, 528, 5, 1.6), hex_rgb("6A6157"), 0.06, lift=6)
    shape(c, cut_rect(946, 252, 1674, 512, 6, 1.4), hex_rgb("33463F"), 0.05)
    scribble(c, 990, 280, 420, 140, 7, hex_rgb("D8DCD2"), 0.22, 2.4, 3)
    scribble(c, 1300, 400, 330, 90, 19, hex_rgb("D8DCD2"), 0.16, 2.0, 2)
    flat(c, cut_rect(960, 518, 1660, 532, 9, 0.6), hex_rgb("7C7266"))
    shape(c, cut_rect(1790, 300, 1930, 470, 11, 1.4, 6), hex_rgb("C9C3B0"), 0.06, lift=4)
    for i, x in enumerate((460, 1240, 1980)):
        y = 92 + 30 * H01(i, 95)
        c.drawLine(x, 0, x, y, prims.stroke(hex_rgb("4A4E52"), 3))
        shape(c, smooth_closed([(x - 70, y + 44), (x - 40, y + 6), (x, y), (x + 40, y + 6), (x + 70, y + 44)]),
              hex_rgb("D5D2C4"), 0.08, lift=3)
    haze(c, (0, 0, FW, H), hex_rgb("B9C0B6"), 0.18)


def classroom_near(c):
    floor(c, 700, (hex_rgb("948068"), hex_rgb("7E6B57"), hex_rgb("5E5146")), 1, hex_rgb("6A6A60"))
    x = 120
    i = 0
    while x < NW - 80:                    # back row, small and hazy
        desk(c, x, 742 + 8 * HS(i, 101), 0.58 + 0.05 * HS(i, 102), 200 + i, stack=H01(i, 103) < 0.4)
        x += 270 + 120 * H01(i, 104)
        i += 1
    haze(c, (0, 600, NW, 760), hex_rgb("A9B2A2"), 0.22)
    x = 40
    i = 0
    while x < NW:                          # middle row
        desk(c, x, 798 + 10 * HS(i, 111), 0.82 + 0.07 * HS(i, 112), 300 + i, stack=H01(i, 113) < 0.35)
        x += 420 + 160 * H01(i, 114)
        i += 1
    desk(c, 2080, 1010, 1.45, 77)


def street_far(c):
    look.sky(c, (0, 0, FW, 720), "overcast")
    x, i = -40, 0
    while x < FW:
        w = 150 + 170 * H01(i, 121)
        building(c, x, x + w, 300 + 160 * H01(i, 122), 720, 500 + i, hex_rgb("9BA2AA"), hex_rgb("B4BAC0"), 0.5)
        x += w - 20 + 30 * H01(i, 123)
        i += 1
    haze(c, (0, 0, FW, 720), hex_rgb("B7BCC1"), 0.35)
    x, i = -60, 0
    while x < FW:
        w = 260 + 200 * H01(i, 131)
        building(c, x, x + w, 400 + 140 * H01(i, 132), 720, 600 + i, P.shade(hex_rgb("6F7886"), 0.05 * HS(i, 133)),
                 hex_rgb("8A93A0"), 0.7, lit=(3, 7))
        if H01(i, 134) < 0.5:              # an awning, a little colour the grade will mostly take
            aw = hex_rgb("8F5B4C") if H01(i, 135) < 0.5 else hex_rgb("4C6E78")
            shape(c, cut_poly([(x + 30, 610), (x + w - 40, 612), (x + w - 30, 650), (x + 20, 648)], i, 1.2), aw, 0.1,
                  lift=4)
        x += w + 10 + 40 * H01(i, 136)
        i += 1
    haze(c, (0, 0, FW, 720), hex_rgb("A7ADB3"), 0.14)


def street_near(c):
    shape(c, cut_poly([(-20, 704), (NW + 20, 700), (NW + 20, 770), (-20, 770)], 4, 1.0), hex_rgb("55596A"), 0.06)
    floor(c, 770, (hex_rgb("A5A49E"), hex_rgb("8E8D88"), hex_rgb("6F6F6C")), 5, hex_rgb("6D6D6A"))
    tree(c, 330, 790, 1.15, 3)
    shape(c, _poly([(700, 800), (707, 800), (705, 520), (699, 520)]), hex_rgb("4D5260"), 0.05)
    shape(c, blob(703, 500, 34, 34, 5, 0.04), hex_rgb("C9C7BD"), 0.10, lift=4)
    shape(c, cut_rect(1980, 742, 2210, 760, 8, 1.0), hex_rgb("6B5B4D"), 0.08, lift=4)
    shape(c, cut_rect(1990, 700, 2200, 722, 9, 1.0, -3), hex_rgb("6B5B4D"), 0.08, lift=3)
    for lx in (2005, 2185):
        flat(c, _poly([(lx - 4, 720), (lx + 4, 720), (lx + 3, 805), (lx - 3, 805)]), hex_rgb("3E3E44"))
    look.shadow(c, 2095, 806, 300, 0.25)
    shape(c, smooth_closed([(1150, 812), (1146, 784), (1160, 772), (1174, 784), (1170, 812)]), hex_rgb("7A5A52"), 0.1,
          lift=3)


STREET_LAMP = (1500, 440)


def street_near_lamp(c):
    street_near(c)
    lamp_post(c, STREET_LAMP[0] + 70, 812, STREET_LAMP[1] + 6, 1.0, 9, lit=0.3)


def dusk_far(c):
    look.sky(c, (0, 0, FW, 700), {"sunset": 0.45, "lid": 0.55})
    prims.glow(c, 1500, 640, 700, hex_rgb("E19A74"), 0.25, 1.4)
    x, i = -30, 0
    while x < FW:
        w = 120 + 160 * H01(i, 141)
        top = 470 + 90 * H01(i, 142)
        peak = top - 40 - 40 * H01(i, 143)
        pts = [(x, 700), (x, top), (x + w * (0.3 + 0.4 * H01(i, 144)), peak), (x + w, top), (x + w, 700)]
        shape(c, cut_poly(pts, i, 1.4), P.mix(hex_rgb("3A4060"), hex_rgb("5C5F7A"), 0.4 * H01(i, 145)), 0.05)
        if H01(i, 146) < 0.45:
            wx = x + w * (0.2 + 0.5 * H01(i, 147))
            flat(c, cut_rect(wx, top + 50, wx + 24, top + 80, i, 0.6), hex_rgb("E8C384"), 0.75)
        if H01(i, 148) < 0.4:
            cx = x + w * 0.7
            flat(c, cut_rect(cx, peak + 8, cx + 18, peak + 50, i + 3, 0.6), hex_rgb("343A58"))
        x += w + 6 * H01(i, 149)
        i += 1
    for k in range(4):
        tx = 250 + 520 * k + 120 * HS(k, 151)
        shape(c, blob(tx, 540, 110, 90, k + 70, 0.16), hex_rgb("2C3350"), 0.04)
    haze(c, (0, 0, FW, 700), hex_rgb("6A6684"), 0.18)


DUSK_LAMP = (1330, 452)


def dusk_near(c):
    floor(c, 712, (hex_rgb("4B4F63"), hex_rgb("40435A"), hex_rgb("2F3346")), 6, hex_rgb("3A3D52"))
    # a low wall of irregular stones behind the pavement
    x, i = -20, 0
    shape(c, cut_rect(-20, 630, NW + 20, 716, 7, 2.0), hex_rgb("5A5D72"), 0.05, lift=5)
    while x < NW:
        w = 70 + 70 * H01(i, 161)
        row = i % 2
        y0 = 636 + row * 40 + 4 * HS(i, 162)
        flat(c, cut_rect(x + 3, y0, x + w - 3, y0 + 34 + 4 * HS(i, 163), i + 90, 1.4),
             P.shade(hex_rgb("5A5D72"), 0.05 * HS(i, 164)))
        x += w * (0.55 if row == 0 else 0.45)
        i += 1
    shape(c, blob(180, 640, 200, 70, 71, 0.18), hex_rgb("2E3A44"), 0.06, lift=4)
    shape(c, blob(2150, 650, 240, 64, 72, 0.18), hex_rgb("2E3A44"), 0.06, lift=4)
    prims.glow(c, DUSK_LAMP[0], 840, 380, hex_rgb("E8D7AE"), 0.22, 1.6)
    lamp_post(c, DUSK_LAMP[0] + 70, 830, DUSK_LAMP[1] + 6, 1.0, 11, lit=0.8)


def stair_far(c):
    prims.fill_rect_gradient(c, (0, 0, FW, H), [hex_rgb("6A7674"), hex_rgb("9AA49E"), hex_rgb("8C968F")], [0, 0.5, 1])
    flat(c, cut_rect(-10, 500, FW + 10, 720, 2, 1.2), hex_rgb("697571"))
    flat(c, cut_rect(-10, 494, FW + 10, 504, 3, 0.8), hex_rgb("5C6763"))
    # a tall narrow window high up, its light on the wall
    prims.glow(c, 470, 250, 460, hex_rgb("E3E6DE"), 0.4, 1.6)
    shape(c, cut_rect(408, 80, 532, 420, 3, 1.0), hex_rgb("7E8580"), 0.04, lift=4)
    c.drawRect(skia.Rect.MakeLTRB(420, 92, 520, 408),
               prims.linear_paint((0, 92), (0, 408), [hex_rgb("ECEFE8"), hex_rgb("C8CEC8")], n=6))
    flat(c, cut_rect(420, 240, 520, 247, 4, 0.3), hex_rgb("7E8580"))
    # a door with a small pane, and a board of pinned blank sheets
    shape(c, cut_rect(110, 380, 300, 722, 5, 1.0), hex_rgb("6F6A62"), 0.07, lift=5)
    flat(c, cut_rect(160, 420, 250, 500, 6, 0.6), hex_rgb("B9C0BC"))
    flat(c, blob(272, 560, 8, 8, 7, 0.05), hex_rgb("3F4448"))
    shape(c, cut_rect(640, 330, 880, 470, 8, 1.2, 4), hex_rgb("8C7A62"), 0.07, lift=4)
    for k in range(4):
        sx, sy = 670 + 56 * k + 10 * HS(k, 170), 350 + 16 * H01(k, 171)
        shape(c, cut_rect(sx, sy, sx + 44, sy + 60 + 10 * H01(k, 172), 20 + k, 0.8, 3 * HS(k, 173)),
              hex_rgb("DCD8CC"), 0.04, lift=2)
    # the flight rising up and to the left, seen from its side: a heavy stringer with lit treads
    x, y = 1960, 722
    steps = []
    for k in range(12):
        dx = 72 + 6 * HS(k, 174)
        steps.append((x - dx, y - 40, x))
        x -= dx
        y -= 40
    top_x, top_y = x, y
    pts = [(1960, 722)]
    for l, yy, r in steps:
        pts += [(r, yy), (l, yy)]
    pts += [(top_x - 260, top_y), (top_x - 260, top_y + 46), (top_x + 40, top_y + 60), (1960, 790)]
    shadow_pts = [(1960, 790), (top_x + 40, top_y + 60), (top_x + 340, top_y + 330), (1960, 760)]
    flat(c, cut_poly(shadow_pts, 9, 1.0), hex_rgb("7D8883"), 0.55)
    shape(c, cut_poly(pts, 8, 0.8), hex_rgb("6E7476"), 0.05, lift=8)
    for l, yy, r in steps:
        flat(c, cut_rect(l - 2, yy, r + 1, yy + 7, int(l), 0.5), hex_rgb("A4AAAA"))
    flat(c, cut_rect(top_x - 262, top_y - 2, top_x + 4, top_y + 8, 10, 0.6), hex_rgb("A4AAAA"))
    rx0, ry0, rx1, ry1 = 1990, 600, top_x - 20, top_y - 112
    shape(c, cut_poly([(rx0, ry0 - 5), (rx1, ry1 - 5), (rx1, ry1 + 6), (rx0, ry0 + 6)], 11, 0.5), hex_rgb("3F4654"), 0.1)
    for k in range(7):
        f = (k + 0.3 + 0.4 * H01(k, 175)) / 7
        bx, by = rx0 + (rx1 - rx0) * f, ry0 + (ry1 - ry0) * f
        c.drawLine(bx, by, bx, by + 104, prims.stroke(hex_rgb("4A5260"), 4, 0.8))
    haze(c, (0, 0, FW, H), hex_rgb("A2ACA6"), 0.12)


def stair_near(c):
    floor(c, 720, (hex_rgb("8E9090"), hex_rgb("7A7C7D"), hex_rgb("5C5F63")), 9, hex_rgb("5F6566"))
    for k in range(22):                     # terrazzo flecks
        fx, fy = 80 + 2300 * H01(k, 181), 740 + 320 * H01(k, 182) ** 1.3
        flat(c, blob(fx, fy, 4 + 6 * H01(k, 183), 2.5, k, 0.3), hex_rgb("A6A7A3"), 0.5)
    # the first steps of the next flight, at the right
    x0 = 1760
    look.shadow(c, x0 + 320, 846, 760, 0.35)
    x, y = x0, 842
    steps = []
    for k in range(7):
        dx = 88 + 8 * HS(k, 184)
        steps.append((x, y - 42, x + dx))
        x += dx
        y -= 42
    pts = [(x0, 842)]
    for l, yy, r in steps:
        pts += [(l, yy), (r, yy)]
    pts += [(NW + 20, y), (NW + 20, 842)]
    shape(c, cut_poly(pts, 11, 0.8), hex_rgb("7E8388"), 0.06, lift=6)
    for l, yy, r in steps:
        flat(c, cut_rect(l - 3, yy, r, yy + 8, int(l) + 3, 0.5), hex_rgb("A9AEB0"))
    shape(c, cut_poly([(x0 + 30, 668), (NW + 20, 668 - (NW - x0) * 0.47), (NW + 20, 680 - (NW - x0) * 0.47),
                       (x0 + 30, 682)], 13, 0.5), hex_rgb("39404E"), 0.12, lift=5)
    shape(c, cut_rect(x0 + 18, 650, x0 + 50, 842, 12, 0.8), hex_rgb("39404E"), 0.08, lift=4)
    shape(c, blob(x0 + 34, 646, 22, 13, 14, 0.05), hex_rgb("39404E"), 0.12)


def play_far(c):
    look.sky(c, (0, 0, FW, 700), "overcast")
    building(c, 1300, 1760, 420, 700, 31, hex_rgb("A1A7AC"), hex_rgb("B8BDC1"), 0.45)
    for k in range(11):
        tx = -40 + 210 * k + 70 * HS(k, 191)
        shape(c, blob(tx, 610 - 30 * H01(k, 192), 120 + 50 * H01(k, 193), 80, k + 30, 0.18),
              P.shade(hex_rgb("7D8C7B"), 0.04 * HS(k, 194)), 0.05)
    haze(c, (0, 0, FW, 720), hex_rgb("B4BAB8"), 0.3)


PLAY_SWING = 1350


def play_near(c):
    floor(c, 690, (hex_rgb("A49882"), hex_rgb("8F846F"), hex_rgb("6E6656")), 13, None)
    for k in range(16):                     # fence posts, leaning a little each
        px = -10 + 160 * k + 40 * HS(k, 201)
        lean = 6 * HS(k, 202)
        shape(c, _poly([(px - 6, 700), (px + 6, 700), (px + 5 + lean, 590 + 10 * H01(k, 203)),
                        (px - 5 + lean, 592 + 10 * H01(k, 203))]), hex_rgb("7A8486"), 0.06)
    c.drawLine(-20, 612, NW + 20, 618, prims.stroke(hex_rgb("7A8486"), 6))
    tree(c, 420, 760, 1.25, 8, hex_rgb("6A7D60"))
    # swing frame
    sx = PLAY_SWING
    col = hex_rgb("B4573F")
    for dx in (-210, 210):
        for lg in (-48, 48):
            shape(c, _poly([(sx + dx + lg - 6, 800), (sx + dx + lg + 6, 800), (sx + dx + 5, 412), (sx + dx - 5, 412)]),
                  col, 0.08)
    shape(c, cut_rect(sx - 240, 404, sx + 240, 420, 14, 0.8), P.shade(col, -0.05), 0.08, lift=4)
    for k, dx in enumerate((-95, 85)):
        sw = 4 * HS(k, 205)
        c.drawLine(sx + dx - 24, 420, sx + dx - 24 + sw, 690, prims.stroke(hex_rgb("3A3F4A"), 2.2))
        c.drawLine(sx + dx + 24, 420, sx + dx + 24 + sw, 690, prims.stroke(hex_rgb("3A3F4A"), 2.2))
        shape(c, cut_rect(sx + dx - 34 + sw, 688, sx + dx + 34 + sw, 700, 15 + k, 0.6), hex_rgb("3A3F4A"), 0.08, lift=5)
    look.shadow(c, sx, 804, 560, 0.3)
    # slide
    gx = 1980
    shape(c, cut_poly([(gx, 800), (gx + 14, 800), (gx + 40, 470), (gx + 26, 470)], 17, 0.6), hex_rgb("6F7C88"), 0.06)
    shape(c, cut_poly([(gx + 30, 470), (gx + 120, 470), (gx + 120, 490), (gx + 36, 494)], 18, 0.6), hex_rgb("6F7C88"))
    shape(c, cut_poly([(gx + 110, 468), (gx + 150, 466), (gx + 360, 760), (gx + 380, 800), (gx + 330, 800),
                       (gx + 320, 772)], 19, 1.0), hex_rgb("D2A24A"), 0.12, lift=6)
    look.shadow(c, gx + 200, 806, 420, 0.28)
    shape(c, blob(1660, 826, 22, 20, 21, 0.03), hex_rgb("9A5F5A"), 0.15, lift=3)


def hall_far(c):
    prims.fill_rect_gradient(c, (0, 0, FW, H), [hex_rgb("757B7C"), hex_rgb("A3A8A3"), hex_rgb("979C97")], [0, 0.5, 1])
    x, i = 60, 0
    while x < FW:
        w = 130 + 90 * H01(i, 211)
        t = 110 + 50 * H01(i, 212)
        b = 560 + 30 * H01(i, 213)
        prims.glow(c, x + w / 2, (t + b) / 2, 330, hex_rgb("E2E5DE"), 0.3, 1.6)
        c.drawRect(skia.Rect.MakeLTRB(x, t, x + w, b),
                   prims.linear_paint((0, t), (0, b), [hex_rgb("E2E5DE"), hex_rgb("C2C8C2")], n=6))
        flat(c, cut_rect(x + w * 0.47, t, x + w * 0.53, b, i, 0.3), hex_rgb("8F948F"))
        x += w + 150 + 120 * H01(i, 214)
        if H01(i, 215) < 0.55:              # a pillar between some
            shape(c, cut_rect(x - 120, 0, x - 60, 700, i + 40, 1.0), hex_rgb("8A8F8B"), 0.08, lift=8)
        i += 1
    for k in range(5):
        lx = 200 + 400 * k + 90 * HS(k, 216)
        ly = 70 + 40 * H01(k, 217)
        c.drawLine(lx, 0, lx, ly, prims.stroke(hex_rgb("575C60"), 2.5))
        shape(c, smooth_closed([(lx - 50, ly + 30), (lx - 26, ly + 4), (lx + 26, ly + 4), (lx + 50, ly + 30)]),
              hex_rgb("C8C6BA"), 0.08)
    flat(c, cut_rect(-10, 600, FW + 10, 700, 5, 1.2), hex_rgb("7C827E"))
    haze(c, (0, 0, FW, H), hex_rgb("ADB2AD"), 0.2)


PATH_TOP = 762       # the desk-path's top surface (back edge)
PATH_FEET = 776      # where feet stand on it
FLOOR_Y = 862        # the hall floor


def hall_near(c):
    floor(c, 700, (hex_rgb("8D8B82"), hex_rgb("78766E"), hex_rgb("5C5B57")), 21, hex_rgb("6B6E6A"))
    # a far row of stacked chairs and a second, lower path, hazy
    for k in range(9):
        x = 60 + 270 * k + 80 * HS(k, 221)
        desk(c, x, 712, 0.42, 400 + k, stack=H01(k, 222) < 0.5)
    haze(c, (0, 600, NW, 720), hex_rgb("A3A8A3"), 0.3)
    # the desk-path: desks end to end, knee-high
    x, i = -40, 0
    top, body = hex_rgb("B89A72"), hex_rgb("8E7458")
    desks = []
    while x < NW + 40:
        w = 168 + 36 * H01(i, 223)
        desks.append((x, w, 2.0 * HS(i, 224), i))
        x += w - 2 + 3 * HS(i, 225)
        i += 1
    look.shadow(c, NW / 2, FLOOR_Y + 2, NW * 1.2, 0.35, squash=0.6)
    for x, w, dy, i in desks:
        for lx in (x + 10, x + w - 14):
            shape(c, _poly([(lx - 5, PATH_TOP + 30), (lx + 5, PATH_TOP + 30), (lx + 4, FLOOR_Y), (lx - 4, FLOOR_Y)]),
                  P.shade(body, -0.12), 0.03)
        shape(c, cut_rect(x + 6, PATH_TOP + 28 + dy, x + w - 6, PATH_TOP + 56 + dy, i + 500, 0.8), body, 0.05)
    for x, w, dy, i in desks:
        shape(c, cut_rect(x, PATH_TOP + dy, x + w, PATH_TOP + 30 + dy, i + 600, 0.8),
              P.shade(top, 0.03 * HS(i, 226)), 0.12, lift=3)
        flat(c, cut_rect(x + 2, PATH_TOP + 22 + dy, x + w - 2, PATH_TOP + 31 + dy, i + 700, 0.6), P.shade(top, -0.12))
        if H01(i, 227) < 0.45:
            sheets(c, x + w * (0.3 + 0.4 * H01(i, 228)), PATH_TOP + 6 + dy, 40, i + 800, int(2 + 5 * H01(i, 229)))


def open_far(c):
    prims.fill_rect_gradient(c, (0, 0, FW, H), [look.FOG, look.FOG_PALE, look.FOG_LIGHT, look.FOG_PALE],
                             [0, 0.45, 0.66, 1])
    for k in range(4):
        x = -200 + 700 * k + 200 * HS(k, 231)
        shape(c, blob(x, 720, 520, 60 + 30 * H01(k, 232), k + 80, 0.1), P.mix(look.FOG_PALE, look.FOG, 0.35), 0.03)
    haze(c, (0, 0, FW, H), look.FOG_PALE, 0.25)


def open_near(c):
    floor(c, 730, (hex_rgb("858A86"), hex_rgb("6E7470"), hex_rgb("555A58")), 25, None)
    for k in range(40):
        tx, ty = 2400 * H01(k, 241), 750 + 300 * H01(k, 242) ** 1.5
        s = 0.5 + (ty - 740) / 300
        shape(c, cut_poly([(tx - 8 * s, ty), (tx - 2 * s, ty - 18 * s), (tx + 1 * s, ty - 6 * s), (tx + 5 * s, ty - 22 * s),
                           (tx + 9 * s, ty)], k, 0.5), hex_rgb("5F665F"), 0.06)


# ------------------------------------------------------------------------------------------------
PLACES = {
    "classroom": (classroom_far, classroom_near, None),
    "street": (street_far, street_near_lamp, STREET_LAMP),
    "dusk": (dusk_far, dusk_near, DUSK_LAMP),
    "stair": (stair_far, stair_near, None),
    "play": (play_far, play_near, None),
    "hall": (hall_far, hall_near, None),
    "open": (open_far, open_near, None),
}


def _far_img(name):
    fn = PLACES[name][0]

    def draw(c):
        c.scale(0.5, 0.5)
        fn(c)
        look.mottle(c, (0, 0, FW, H), 0.22, 1.0, sum(map(ord, name)) % 97)
    return prims.sprite(("montage_far", name), FW // 2, H // 2, draw)


def _near_img(name):
    fn = PLACES[name][1]

    def draw(c):
        fn(c)
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(0, 640, NW, H))
        look.mottle(c, (0, 640, NW, H), 0.18, 1.0, 7)
        c.restore()
    return prims.sprite(("montage_near", name), NW, H, draw)


def draw(canvas, name: str, scroll: float = BASE, alpha: float = 1.0):
    """Draw place `name` with near-plane x = scroll at the screen's left edge. Returns the lamp's
    screen position (or None)."""
    far, near = _far_img(name), _near_img(name)
    fs = min(max(0.0, BASE * FAR_K * 0.5 + (scroll - BASE) * FAR_K), FW - W)
    prims.draw_image(canvas, far, -fs, 0, 2.0, alpha, anchor=(0, 0))
    prims.draw_image(canvas, near, -scroll, 0, 1.0, alpha, anchor=(0, 0))
    lamp = PLACES[name][2]
    return None if lamp is None else (lamp[0] - scroll, lamp[1])


def warm(names=None):
    for n in names or PLACES:
        _far_img(n)
        _near_img(n)
