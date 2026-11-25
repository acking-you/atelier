"""The room set, in world units (one virtual camera looks at it; see room.py).

bake() rasterises the static set once (wall, floor, rug, sofa, the lamp that is off, the low table
and cup, the jacket on its hook, the window frame) with the window opening punched out; the light
of the hour, the view through the window, the sashes and the curtains are drawn per frame.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from mv.engine import prims
from mv.engine.palette import mix, sk
from hx.kit import look

hx = look.hex_rgb
INK = look.INK
WW, WH = 2700, 1500
FLOOR = 968                       # wall meets floor
SEAT = 880                        # sofa seat surface (where the child sits)
SOFA = (700.0, 1120.0)            # the sofa as placed (drawn at 0.6 about its foot, see bake)
ARM_TOP = 829.0
WIN = (1480.0, 320.0, 1990.0, 770.0)          # outer frame
OPEN = (1502.0, 342.0, 1968.0, 748.0)         # the opening (sky side)
TRANSOM = (1502.0, 452.0, 1968.0, 466.0)
MEET = 1735.0                                 # where the two sashes meet
SILL = 748.0
BAKE_S = 1.25


def R(l, t, r, b):
    return skia.Rect.MakeLTRB(float(l), float(t), float(r), float(b))


def rr(l, t, r, b, rx, ry=None):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(R(l, t, r, b), rx, rx if ry is None else ry))
    return p


def vgrad(t, b, cols, pos=None, alpha=1.0, x=0.0):
    return prims.linear_paint((x, t), (x, b), cols, pos, alpha)


def hgrad(l, r, cols, pos=None, alpha=1.0, y=0.0):
    return prims.linear_paint((l, y), (r, y), cols, pos, alpha)


def soft(c, path, color, alpha, sigma, blend=None):
    p = prims.fill(color, alpha, blend=blend)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(0.5, sigma)))
    c.drawPath(path, p)


def blob(pts, close=True):
    """Smooth path through points (quadratic through the midpoints)."""
    pts = [(float(x), float(y)) for x, y in pts]
    n = len(pts)
    p = skia.Path()
    if close:
        m = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)  # noqa: E731
        p.moveTo(*m(pts[-1], pts[0]))
        for i in range(n):
            q = m(pts[i], pts[(i + 1) % n])
            p.quadTo(pts[i][0], pts[i][1], q[0], q[1])
        p.close()
    else:
        p.moveTo(*pts[0])
        for i in range(1, n - 1):
            q = ((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
            p.quadTo(pts[i][0], pts[i][1], q[0], q[1])
        p.lineTo(*pts[-1])
    return p


def wobbly(pts, amp, salt, sub=6):
    """Subdivide a polygon's edges and jitter them a little (nothing ruled)."""
    out = []
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        for k in range(sub):
            u = k / sub
            j = i * 31 + k
            out.append((x0 + (x1 - x0) * u + amp * float(prims.hash_sym(j, salt)),
                        y0 + (y1 - y0) * u + amp * float(prims.hash_sym(j, salt + 1))))
    return out


def poly(pts, close=True):
    p = skia.Path()
    p.addPoly([skia.Point(float(x), float(y)) for x, y in pts], close)
    return p


# ---------------------------------------------------------------------------------------------
# the static set
# ---------------------------------------------------------------------------------------------
def _wall(c):
    c.drawRect(R(0, 0, WW, FLOOR), vgrad(0, FLOOR, [hx("7A7B6B"), hx("A19F88"), hx("AAA891"), hx("97957D")],
                                         [0, .28, .72, 1]))
    look.mottle(c, (0, 0, WW, FLOOR), alpha=0.24, scale=1.5, seed=3)
    # where a picture once hung, and the nail left behind
    soft(c, rr(2296, 386, 2446, 566, 6), hx("C2C0A8"), 0.32, 5)
    c.drawCircle(2369, 378, 3.2, prims.fill(hx("3E392F"), 0.8))
    # a worn band where the sofa back rubs the wall
    soft(c, rr(610, 636, 1220, 690, 26), hx("6A6855"), 0.30, 22)
    # cornice and the shadow under it
    c.drawRect(R(0, 0, WW, 44), vgrad(0, 44, [hx("8C8878"), hx("C0BBA9")]))
    c.drawRect(R(0, 44, WW, 100), prims.linear_paint((0, 44), (0, 100), [INK, INK], alphas=[0.30, 0.0]))
    # skirting
    c.drawRect(R(0, 936, WW, FLOOR), vgrad(936, FLOOR, [hx("A3937C"), hx("7B6B58"), hx("5B4E40")], [0, .14, 1]))


def _floor(c):
    c.drawRect(R(0, FLOOR, WW, WH), vgrad(FLOOR, WH, [hx("47382D"), hx("5F4A3A"), hx("6C5442")], [0, .3, 1]))
    look.mottle(c, (0, FLOOR, WW, WH), alpha=0.30, scale=2.2, seed=5)
    # a few long, faint board seams running into the room (uneven spacing, broken)
    vx, vy = 1300.0, 520.0
    for i in range(9):
        fx = -300 + 3300 * (i + 0.5 * prims.hash01(i, 41)) / 9.0
        u0, u1 = 0.18 + 0.1 * prims.hash01(i, 42), 0.62 + 0.35 * prims.hash01(i, 43)
        ys = FLOOR + (WH - FLOOR) * np.array([u0, u1])
        xs = vx + (fx - vx) * (ys - vy) / (WH - vy)
        c.drawLine(xs[0], ys[0], xs[1], ys[1], prims.stroke(INK, 1.4, 0.10 + 0.06 * prims.hash01(i, 44)))
    c.drawRect(R(0, FLOOR, WW, FLOOR + 46), prims.linear_paint((0, FLOOR), (0, FLOOR + 46), [INK, INK],
                                                               alphas=[0.45, 0.0]))


def _rug(c):
    back, front = 994.0, 1262.0
    outer = wobbly([(372, back), (1520, back), (1676, front), (226, front)], 2.2, 300)
    po = poly(outer)
    soft(c, po, INK, 0.35, 5)
    c.drawPath(po, vgrad(back, front, [hx("7A5240"), hx("8E5F48")]))

    def inset(d):
        return [(372 + d * 0.9, back + d * 0.55), (1520 - d * 0.9, back + d * 0.55),
                (1676 - d * 1.15, front - d * 0.7), (226 + d * 1.15, front - d * 0.7)]
    field = poly(wobbly(inset(64), 1.6, 310))
    c.drawPath(field, vgrad(back, front, [hx("62332F"), hx("85453E")]))
    band = poly(wobbly(inset(96), 1.4, 320))
    band.setFillType(skia.PathFillType.kEvenOdd)
    band.addPath(poly(wobbly(inset(118), 1.4, 330)))
    c.drawPath(band, vgrad(back, front, [hx("7E5E44"), hx("94704F")], alpha=0.28))
    c.save()
    c.clipPath(po, doAntiAlias=True)
    look.mottle(c, (200, back, 1700, front), alpha=0.45, scale=0.9, seed=7)
    # worn: a pale patch near the front right where feet go, threads gone thin
    c.drawOval(R(1180, 1150, 1600, 1290), prims.radial_paint((1400, 1215), 210, hx("B79C7C"), 0.45, 1.6))
    c.restore()
    # fringe along the front, missing toward the worn corner
    for i in range(150):
        x = 236 + i * 9.6 + 4 * float(prims.hash_sym(i, 340))
        if x > 1330 and prims.hash01(i, 341) < 0.55 + 0.4 * min(1.0, (x - 1330) / 250):
            continue
        ln = 7 + 9 * float(prims.hash01(i, 342))
        ang = 0.35 * float(prims.hash_sym(i, 343))
        c.drawLine(x, front - 1, x + ln * math.sin(ang), front - 1 + ln * math.cos(ang),
                   prims.stroke(hx("C8B592"), 1.6, 0.55))


def _lamp(c):
    x = 438.0
    look.shadow(c, x + 8, 978, 120, 0.55, INK, 0.22)
    c.drawOval(R(x - 36, 963, x + 36, 981), vgrad(963, 981, [hx("4A433D"), hx("221E1C")]))
    c.drawPath(poly([(x - 6, 968), (x + 6, 968), (x + 16, 528), (x + 8, 528)]),
               hgrad(x - 4, x + 14, [hx("6A625A"), hx("2B2724")]))
    sx = x + 11
    shade = blob([(sx - 38, 452), (sx + 36, 450), (sx + 52, 524), (sx + 6, 532), (sx - 56, 526)])
    soft(c, shade, INK, 0.3, 14)
    c.drawPath(shade, hgrad(sx - 56, sx + 52, [hx("A89D86"), hx("D5CAB0"), hx("B8AD94"), hx("968B76")],
                            [0, .35, .7, 1]))
    c.drawOval(R(sx - 54, 518, sx + 52, 536), prims.fill(hx("3A342C"), 0.75))


def _sofa(c):
    L, Rr = 560.0, 1260.0
    teal, teal_d, teal_l = hx("56736F"), hx("374C49"), hx("6F8D87")
    soft(c, rr(L + 18, 652, Rr + 14, 962, 60), INK, 0.50, 24)
    look.shadow(c, (L + Rr) / 2 + 10, 972, Rr - L + 90, 0.75, INK, 0.09)
    c.drawPath(rr(L + 40, 668, Rr - 40, 862, 34), vgrad(668, 862, [teal_l, teal, teal_d]))
    for i, (l, r, top, rot) in enumerate(((628, 916, 684, -1.4), (898, 1186, 696, 1.9))):
        c.save()
        c.rotate(rot, (l + r) / 2, 840)
        p = blob([(l + 10, top + 30), (l + 70, top + 2), ((l + r) / 2, top - 4), (r - 60, top + 4),
                  (r - 6, top + 34), (r, 790), (r - 8, 846), (l + 6, 846), (l, 790)])
        soft(c, p, INK, 0.35, 10)
        c.drawPath(p, vgrad(top, 846, [teal_l, teal, teal_d], [0, .45, 1]))
        c.restore()
    for l, r, top in ((640, 918, 808), (904, 1180, 812)):
        c.drawPath(rr(l, top, r, 904, 24), vgrad(top, 904, [teal_l, teal, teal_d], [0, .3, 1]))
        c.drawPath(rr(l + 8, top + 2, r - 8, top + 22, 12), prims.fill(teal_l, 0.35))
    soft(c, rr(906, 812, 918, 902, 6), INK, 0.35, 4)
    c.drawPath(rr(L + 14, 892, Rr - 14, 960, 10), vgrad(892, 960, [teal_d, hx("26332F")]))
    for fx, fw in ((L + 44, 17.0), (Rr - 52, 15.0)):
        c.drawPath(poly([(fx - fw / 2, 958), (fx + fw / 2, 958), (fx + fw / 3, 976), (fx - fw / 3, 976)]),
                   prims.fill(hx("3A2C22")))
    for l, r in ((L, L + 104), (Rr - 104, Rr)):
        c.drawPath(rr(l, 744, r, 960, 42, 30), vgrad(744, 960, [teal_l, teal, teal_d], [0, .3, 1]))
        c.drawPath(rr(l - 5, 734, r + 5, 792, 30), vgrad(734, 792, [teal_l, teal]))
        inner = r if l < 800 else l
        soft(c, rr(inner - 10, 796, inner + 10, 950, 8), INK, 0.30, 8)
    # a knitted throw over the right arm
    tx = Rr - 104
    throw = blob([(tx - 8, 742), (tx + 50, 728), (Rr + 10, 744), (Rr + 14, 820), (Rr + 6, 902), (Rr - 22, 920),
                  (Rr - 48, 896), (tx + 20, 916), (tx - 6, 884), (tx - 12, 800)])
    soft(c, throw, INK, 0.35, 8)
    c.drawPath(throw, vgrad(728, 920, [hx("C49D61"), hx("A47E48"), hx("7E6037")], [0, .5, 1]))
    for k, fx in enumerate((tx + 18, tx + 56, tx + 86)):
        soft(c, blob([(fx, 760), (fx + 8, 840), (fx + 2, 905), (fx - 6, 840)]), hx("5E4628"), 0.35, 5)


def _table(c):
    look.shadow(c, 1374, 1052, 230, 0.6, INK, 0.12)
    wood, wood_l, wood_d = hx("6A4C36"), hx("8C6A4A"), hx("402D21")
    for x0 in (1310, 1424):
        c.drawRect(R(x0, 996, x0 + 9, 1042), prims.fill(wood_d))
    for x0 in (1291, 1441):
        c.drawPath(poly([(x0, 998), (x0 + 13, 998), (x0 + 10, 1054), (x0 + 3, 1054)]), prims.fill(wood))
    c.drawPath(rr(1280, 982, 1464, 1001, 4), vgrad(982, 1001, [wood_l, wood, wood_d], [0, .5, 1]))
    # the cup, half drunk and cold
    cx = 1338.0
    look.shadow(c, cx + 3, 984, 34, 0.45, INK, 0.25)
    c.drawPath(poly([(cx - 13, 958), (cx + 13, 958), (cx + 11, 983), (cx - 11, 983)]),
               hgrad(cx - 13, cx + 13, [hx("D8D0C1"), hx("C2B9A8"), hx("8F877A")], [0, .45, 1]))
    c.drawOval(R(cx - 13, 954, cx + 13, 962), prims.fill(hx("5D5247")))
    c.drawOval(R(cx + 9, 962, cx + 22, 978), prims.stroke(hx("A79E8F"), 3.6))
    # a paper folded on the corner
    c.drawPath(poly([(1398, 981), (1452, 976), (1458, 983), (1402, 986)]), prims.fill(hx("CFC6B3"), 0.9))


def _jacket(c):
    x = 2212.0
    pts = [(x - 12, 514), (x + 14, 514), (x + 46, 548), (x + 78, 586), (x + 88, 700), (x + 82, 812),
           (x + 66, 820), (x + 58, 702), (x + 62, 868), (x + 18, 884), (x - 34, 876), (x - 66, 868),
           (x - 62, 700), (x - 76, 600), (x - 50, 552)]
    p = blob(pts)
    soft(c, _moved(p, 12, 10), INK, 0.4, 14)
    c.drawPath(p, vgrad(514, 884, [hx("4D5B79"), hx("3D4A66"), hx("2E3850")], [0, .4, 1]))
    soft(c, blob([(x - 30, 560), (x + 26, 556), (x + 34, 600), (x - 4, 616), (x - 38, 600)]), hx("5D6B8A"), 0.7, 4)
    for fx in (x - 20, x + 30):
        soft(c, blob([(fx, 640), (fx + 7, 760), (fx + 2, 870), (fx - 5, 760)]), INK, 0.35, 6)
    c.drawOval(R(x - 7, 506, x + 7, 518), prims.fill(hx("8C7A5E")))


def _window_frame(c):
    l, t, r, b = WIN
    frame, frame_l, frame_d = hx("C9C1AD"), hx("DED6C3"), hx("958D79")
    soft(c, rr(l - 8, t - 6, r + 12, b + 18, 6), INK, 0.32, 14)
    ring = skia.Path()
    ring.setFillType(skia.PathFillType.kEvenOdd)
    ring.addRect(R(l, t, r, b))
    ring.addRect(R(*OPEN))
    c.drawPath(ring, vgrad(t, b, [frame_l, frame, frame_d]))
    c.drawRect(R(*TRANSOM), vgrad(TRANSOM[1], TRANSOM[3], [frame_l, frame_d]))
    # sill and its shadow on the wall
    soft(c, rr(1470, 774, 2000, 806, 8), INK, 0.45, 9)
    c.drawPath(rr(1460, 744, 2010, 778, 4), vgrad(744, 778, [hx("E2DAC7"), hx("C3BBA7"), hx("8F8774")],
                                                  [0, .3, 1]))
    # curtain rod
    c.drawPath(rr(1414, 297, 2056, 306, 4), vgrad(297, 306, [hx("6A625A"), hx("2E2A27")]))
    for x in (1412, 2058):
        c.drawCircle(x, 301.5, 8, prims.fill(hx("3A3530")))


@lru_cache(maxsize=1)
def bake() -> skia.Image:
    w, h = int(WW * BAKE_S), int(WH * BAKE_S)
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.scale(BAKE_S, BAKE_S)
    _wall(c)
    _floor(c)
    _rug(c)
    # the furniture is drawn at its own size and set into the room at the child's scale
    for fn, (ax, ay), (bx, by), k in ((_lamp, (438, 978), (615, 978), 0.62), (_sofa, (910, 972), (910, 972), 0.6),
                                       (_table, (1372, 1052), (1236, 1000), 0.6),
                                       (_jacket, (2212, 510), (2200, 640), 0.6)):
        c.save()
        c.translate(bx, by)
        c.scale(k, k)
        c.translate(-ax, -ay)
        fn(c)
        c.restore()
    _window_frame(c)
    clear = skia.Paint(BlendMode=skia.BlendMode.kClear)
    c.drawRect(R(OPEN[0], OPEN[1], OPEN[2], TRANSOM[1]), clear)
    c.drawRect(R(OPEN[0], TRANSOM[3], OPEN[2], OPEN[3]), clear)
    img = surf.makeImageSnapshot()
    return img.withDefaultMipmaps() or img


def draw_bake(c):
    c.save()
    c.scale(1.0 / BAKE_S, 1.0 / BAKE_S)
    c.drawImage(bake(), 0, 0, prims.MIP, skia.Paint(AntiAlias=False))
    c.restore()


# ---------------------------------------------------------------------------------------------
# per frame: light, the outside, sashes, curtains
# ---------------------------------------------------------------------------------------------
def modulate(c, view, far, near, top=1.0):
    """Darken the room by the light of the hour: `far` at the TV side, `near` by the window."""
    l, t, r, b = view
    p = prims.linear_paint((200, 0), (1900, 0), [far, mix(far, near, 0.55), near], [0, .55, 1])
    p.setBlendMode(skia.BlendMode.kModulate)
    c.drawRect(R(l, t, r, b), p)
    if top < 0.999:
        g = (top, top, top)
        p2 = prims.linear_paint((0, 0), (0, 520), [g, (1.0, 1.0, 1.0)])
        p2.setBlendMode(skia.BlendMode.kModulate)
        c.drawRect(R(l, t, r, min(b, 520)), p2)


def spill(c, color, alpha, floor_alpha=None, reach=1.0):
    """Window light on the wall around the window and a soft patch on the floor below it."""
    if alpha <= 0.003:
        return
    p = prims.radial_paint((1735, 560), 620, color, alpha, 1.7)
    p.setBlendMode(skia.BlendMode.kScreen)
    c.drawCircle(1735, 560, 620, p)
    fa = alpha * 0.8 if floor_alpha is None else floor_alpha
    d = 260 * reach
    quad = poly([(1470, 992), (1990, 992), (1990 - d * 0.9, 1100 + d * 0.4), (1470 - d * 1.6, 1100 + d * 0.4)])
    soft(c, quad, color, fa, 26, blend=skia.BlendMode.kScreen)


def sashes(c, open_w=0.0, tint=(0.75, 0.8, 0.88), glass_alpha=0.10):
    """The two casement sashes in the lower opening: closed (open_w 0) or swung into the room."""
    l, t, r, b = OPEN[0], TRANSOM[3], OPEN[2], OPEN[3]
    fr, frd = hx("C9C1AD"), hx("8E8672")
    if open_w <= 0.01:
        for a, z in ((l, MEET), (MEET, r)):
            ring = skia.Path()
            ring.setFillType(skia.PathFillType.kEvenOdd)
            ring.addRect(R(a, t, z, b))
            ring.addRect(R(a + 13, t + 12, z - 13, b - 12))
            c.drawPath(ring, vgrad(t, b, [fr, frd]))
        # faint reflection on the glass
        c.drawRect(R(l, OPEN[1], r, b), prims.linear_paint((l, OPEN[1]), (r, b), [tint, tint, tint],
                                                             [0, .5, 1], alphas=[glass_alpha, 0.0, glass_alpha * 0.6]))
        return
    w = open_w
    for hinge, sgn in ((l, -1), (r, 1)):
        x2 = hinge + sgn * (MEET - l) * (1 - w) * 0.98 + sgn * 70 * w
        q = [(hinge, t), (x2, t - 26 * w), (x2, b + 40 * w), (hinge, b)]
        p = poly(q)
        c.drawPath(p, hgrad(hinge, x2, [fr, frd]))
        inner = poly([(hinge + sgn * 9, t + 12), (x2 - sgn * 9, t - 26 * w + 14), (x2 - sgn * 9, b + 40 * w - 14),
                      (hinge + sgn * 9, b - 12)])
        c.drawPath(inner, hgrad(hinge, x2, [mix(tint, (1, 1, 1), .2), tint], alpha=0.85))


def curtains(c, t, sway=0.0, col=hx("A98A6A")):
    """Gathered curtains at both sides of the window, folds by hashed stops; a breeze when open."""
    out = []
    for side, (x0, x1, b0) in enumerate(((1404.0, 1522.0, 942.0), (1950.0, 2036.0, 940.0))):
        sw = sway * (14 + 6 * side) * math.sin(t * (0.9 + 0.2 * side) + side)
        sw2 = sway * 6 * math.sin(t * 1.7 + 2 * side)
        pts = [(x0, 306), (x1, 306), (x1 + 6 + sw * 0.6, 520), (x1 + 14 + sw + sw2, b0 - 20),
               (x1 + 8 + sw, b0), (x0 - 10 + sw * 0.8, b0 + 4), (x0 - 14 + sw * 0.6 - sw2, b0 - 30), (x0 - 4, 520)]
        p = blob(pts)
        soft(c, _moved(p, 10, 6), INK, 0.35, 14)
        n = 9
        stops = np.sort(np.concatenate([[0, 1], prims.hash01(np.arange(n) + 13 * side, 360) * 0.96 + 0.02]))
        cols = [mix(col, INK, 0.35 + 0.25 * prims.hash01(i, 361 + side)) if i % 2 else
                mix(col, (1, 1, 1), 0.08 * prims.hash01(i, 363)) for i in range(len(stops))]
        c.drawPath(p, prims.linear_paint((x0 - 14, 0), (x1 + 14, 0), cols, list(stops)))
        c.drawPath(p, prims.linear_paint((0, 306), (0, b0), [INK, INK, INK], [0, .2, 1], alphas=[0.3, 0.0, 0.15]))
        out.append(p)
    return out


# ---------------------------------------------------------------------------------------------
# the view through the window
# ---------------------------------------------------------------------------------------------
def _opp_windows():
    """The opposite building's windows: three uneven columns, sizes and sills varied by hash."""
    out = []
    for i in range(9):
        col, row = i % 3, i // 3
        w = 40 + 22 * float(prims.hash01(i, 382))
        h = 46 + 24 * float(prims.hash01(i, 383))
        x = (1754, 1836, 1922)[col] + 10 * float(prims.hash_sym(i, 380)) + (3 if row == 1 else 0) * col
        y = (510, 606, 700)[row] + 12 * float(prims.hash_sym(i, 381)) + 4 * col
        out.append((x, y, w, h))
    return out


OPP_WINDOWS = _opp_windows()
OPP_KIND = [("curtain" if prims.hash01(i, 384) < 0.3 else "dark" if prims.hash01(i, 384) < 0.5 else "glass")
            for i in range(9)]


def wire_y(which, x):
    l, r = OPEN[0] - 20, OPEN[2] + 20
    u = (x - l) / (r - l)
    if which == 0:
        return 402 + 14 * u + 16 * 4 * u * (1 - u)
    return 512 - 12 * u + 22 * 4 * u * (1 - u)


def outside(c, mood, facade, glass, roofs, warm=0.0, street=None):
    """Sky, far roofs, the far street, the opposite building with its windows, our eave and wires.
    Drawn clipped to the opening; colours come from the hour."""
    l, t, r, b = OPEN
    c.save()
    c.clipRect(R(l, t, r, b))
    look.sky(c, (l, t, r, b + 2), mood)
    # far roofs
    pts = [(l - 10, b + 5), (l - 10, 640)]
    x, i = l - 10, 0
    while x < 1760:
        w = 34 + 58 * float(prims.hash01(i, 390))
        y = 612 + 64 * float(prims.hash01(i, 391))
        if prims.hash01(i, 392) < 0.4:
            pts += [(x, y + 14), (x + w * 0.5, y - 10), (x + w, y + 14)]
        else:
            pts += [(x, y), (x + w, y)]
        x += w
        i += 1
    pts += [(x, b + 5)]
    c.drawPath(poly(pts), vgrad(600, b, [roofs, mix(roofs, INK, 0.25)]))
    if street is not None:
        c.drawRect(R(l, 712, 1760, b + 4), vgrad(712, b, [street, mix(street, INK, 0.3)]))
        c.drawRect(R(l, 710, 1760, 716), prims.fill(mix(street, (1, 1, 1), 0.25), 0.6))
    # the opposite building
    bl = 1732.0
    c.drawPath(poly([(bl, b + 5), (bl, 484), (1812, 484), (1812, 476), (1900, 476), (1900, 480), (r + 10, 480),
                     (r + 10, b + 5)]), hgrad(bl, r, [mix(facade, (1, 1, 1), 0.06), facade, mix(facade, INK, 0.2)]))
    c.drawRect(R(1838, 456, 1872, 478), prims.fill(mix(facade, INK, 0.35)))   # a water tank on the roof
    for i, (wx, wy, ww, wh) in enumerate(OPP_WINDOWS):
        g = mix(glass, INK, 0.45) if OPP_KIND[i] == "dark" else glass
        c.drawRect(R(wx, wy, wx + ww, wy + wh), vgrad(wy, wy + wh, [g, mix(g, INK, 0.3)]))
        if OPP_KIND[i] == "curtain":
            cw = ww * (0.35 + 0.4 * float(prims.hash01(i, 385)))
            x0 = wx if prims.hash01(i, 386) < 0.5 else wx + ww - cw
            c.drawRect(R(x0, wy, x0 + cw, wy + wh), hgrad(x0, x0 + cw, [mix(facade, (1, 1, 1), 0.25),
                                                                        mix(facade, (1, 1, 1), 0.1)]))
        so = 3 + 4 * float(prims.hash01(i, 387))
        c.drawRect(R(wx - so, wy + wh, wx + ww + so, wy + wh + 3 + so * 0.6), prims.fill(mix(facade, (1, 1, 1), 0.18)))
    # our eave, across the top, and the gutter's lip
    c.drawPath(poly([(l - 10, t - 10), (r + 10, t - 10), (r + 10, 384), (l - 10, 374)]),
               vgrad(t, 384, [hx("1A1E2A"), hx("2B3142")]))
    c.drawPath(poly([(l - 10, 368), (r + 10, 377), (r + 10, 387), (l - 10, 379)]), prims.fill(hx("12151F")))
    for k in (0, 1):
        xs = np.linspace(l - 20, r + 20, 24)
        c.drawPath(prims.poly_path(xs, [wire_y(k, x) for x in xs]), prims.stroke(hx("15181F"), 2.0, 0.9))
    c.restore()


def _moved(p, dx, dy):
    q = skia.Path(p)
    q.offset(dx, dy)
    return q


PANES = ((1502.0, 342.0, 1968.0, 452.0), (1515.0, 478.0, 1722.0, 736.0), (1748.0, 478.0, 1955.0, 736.0))


def panes_path():
    """The glass of the closed window (top light and the two sashes' panes)."""
    p = skia.Path()
    for q in PANES:
        p.addRect(R(*q))
    return p
