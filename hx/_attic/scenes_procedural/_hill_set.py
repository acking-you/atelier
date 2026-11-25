"""The hill set: one gentle rounded grass hill above a sea of fog, far hills with a small town,
grass tufts, flowers, rain-green patches, paper cut-outs and the kite.

World units are logical px at camera zoom 1 (the wide shot). A layer of depth d (0 = the sky,
1 = the near hill where the children stand) is seen through the camera with zoom
1 + (z - 1) * d and pan scaled by d, so one camera move gives the whole set its parallax.
"""
from __future__ import annotations

import math
from contextlib import contextmanager

import numpy as np
import skia

from mv.engine import palette as P
from mv.engine import prims
from mv.engine.palette import sk

from hx.kit import look

W, H = 1920, 1080
H01, HS = prims.hash01, prims.hash_sym
CREST_Y = 770.0          # the summit under the children's feet (world y at x = 0)
LINEAR = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kNone)


# ---------------------------------------------------------------------------------------------
# camera
# ---------------------------------------------------------------------------------------------
class Cam:
    def __init__(self, cx: float = 0.0, cy: float = 540.0, z: float = 1.0):
        self.cx, self.cy, self.z = float(cx), float(cy), float(z)

    def zd(self, d: float) -> float:
        return 1.0 + (self.z - 1.0) * d

    def pt(self, x, y, d: float = 1.0):
        z = self.zd(d)
        return ((x - self.cx * d) * z + W / 2, (y - (540.0 + (self.cy - 540.0) * d)) * z + H / 2)

    def inv(self, sx, sy, d: float = 1.0):
        z = self.zd(d)
        return ((sx - W / 2) / z + self.cx * d, (sy - H / 2) / z + 540.0 + (self.cy - 540.0) * d)

    @contextmanager
    def layer(self, canvas, d: float):
        z = self.zd(d)
        canvas.save()
        canvas.translate(W / 2, H / 2)
        canvas.scale(z, z)
        canvas.translate(-self.cx * d, -(540.0 + (self.cy - 540.0) * d))
        try:
            yield
        finally:
            canvas.restore()

    def xrange(self, d: float = 1.0, pad: float = 200.0):
        x0, _ = self.inv(-pad, 0, d)
        x1, _ = self.inv(W + pad, 0, d)
        return x0, x1

    @staticmethod
    def lerp(a: "Cam", b: "Cam", w: float) -> "Cam":
        w = min(1.0, max(0.0, w))
        return Cam(a.cx + (b.cx - a.cx) * w, a.cy + (b.cy - a.cy) * w, a.z * (b.z / a.z) ** w)


# ---------------------------------------------------------------------------------------------
# the ground: a rounded summit at x = 0 that falls gently to the left and runs on to the right
# as a long, softly rolling ridge (the walk of c3a and the outro)
# ---------------------------------------------------------------------------------------------
def ground_y(x):
    x = np.asarray(x, dtype=np.float64)
    left = CREST_Y + 230.0 * (1.0 - np.exp(-(x / 1250.0) ** 2))
    right = (CREST_Y + 34.0 * (1.0 - np.exp(-(x / 650.0) ** 2)) + 20.0 * (1.0 - np.cos(x / 950.0))
             + 9.0 * (1.0 - np.cos(x / 410.0)))
    y = np.where(x < 0, left, right)
    return float(y) if y.ndim == 0 else y


def _swells():
    """Lower rolling planes in front of the main slope (x0, depth below the ground, curvature)."""
    out = []
    for k in range(-3, 9):
        x0 = -700.0 + k * 1080.0 + 260.0 * HS(k, 3)
        out.append((x0, 95.0 + 70.0 * H01(k, 4), 0.00026 + 0.00018 * H01(k, 5), k))
    return out


SWELLS = _swells()


# ---------------------------------------------------------------------------------------------
# colours of the set by light level: `lit` 0 (a heavy dark afternoon) .. 1 (full daylight);
# the world is painted in true colours and the grade drains it
# ---------------------------------------------------------------------------------------------
def tones(lit: float, gold: float = 0.0):
    dk = 1.0 - lit
    g = {}
    g["crest"] = P.shade(P.mix(look.MEADOW, look.MEADOW_LIGHT, 0.25), -0.30 * dk)
    g["slope"] = P.shade(look.MEADOW, -0.34 * dk - 0.04)
    g["foot"] = P.shade(look.MEADOW_DEEP, -0.30 * dk - 0.02)
    g["swell"] = P.shade(P.mix(look.MEADOW, look.MEADOW_DEEP, 0.5), -0.30 * dk)
    g["swell_foot"] = P.shade(look.MEADOW_DEEP, -0.32 * dk - 0.07)
    haze = P.mix(look.FOG_PALE, look.SKY_BLUE, 0.35 * lit)
    g["mid"] = P.mix(P.shade(look.MEADOW_DEEP, -0.18 * dk), haze, 0.45)
    g["far1"] = P.mix(P.shade(look.MEADOW_DEEP, -0.12 * dk), haze, 0.72)
    g["far2"] = P.mix(P.shade(look.MEADOW_DEEP, -0.15 * dk), haze, 0.60)
    g["fog"] = P.shade(P.mix(look.FOG_PALE, look.CREAM_CLOUD, 0.6 * lit), -0.22 * dk)
    g["fog_far"] = P.shade(P.mix(look.FOG, look.FOG_LIGHT, 0.5 + 0.3 * lit), -0.18 * dk)
    if gold > 0:
        for k in g:
            g[k] = P.mix(g[k], P.mix(g[k], look.PERSIMMON, 0.55), 0.35 * gold)
    return g


# ---------------------------------------------------------------------------------------------
# far hills and the far town (depth 0.06), cached paths
# ---------------------------------------------------------------------------------------------
D_FAR, D_FOG, D_MID, D_LID = 0.18, 0.27, 0.50, 0.15
_PATHS: dict = {}


def _ridge(seed, y0, amp, x0=-4000.0, x1=6000.0, step=16.0):
    xs = np.arange(x0, x1 + step, step)
    y = (y0 - amp * (0.55 * np.maximum(0, np.sin(xs / 520.0 + seed)) ** 1.5
                     + 0.45 * prims.value_noise(xs / 300.0, seed) + 0.25 * prims.value_noise(xs / 90.0, seed + 5) * 0.4))
    return xs, y


def far_y(xs, which):
    xs = np.asarray(xs, dtype=np.float64)
    if which == 1:
        return np.interp(xs, *_ridge(11, 560.0, 120.0))
    return np.interp(xs, *_ridge(23, 590.0, 80.0))


def _path_under(xs, ys, bottom):
    p = skia.Path()
    pts = [skia.Point(float(x), float(y)) for x, y in zip(xs, ys)]
    pts += [skia.Point(float(xs[-1]), bottom), skia.Point(float(xs[0]), bottom)]
    p.addPoly(pts, True)
    return p


def _far_path(which):
    key = ("far", which)
    if key not in _PATHS:
        xs, ys = _ridge(11, 560.0, 120.0) if which == 1 else _ridge(23, 590.0, 80.0)
        _PATHS[key] = _path_under(xs, ys, 900.0)
    return _PATHS[key]


def _town():
    """Small houses clustered on the near far-ridge (x, w, h, roof h, roof colour index, wall shade)."""
    if "town" in _PATHS:
        return _PATHS["town"]
    out = []
    for i in range(22):
        c = 0 if H01(i, 1) < 0.62 else 1
        cx = (430.0 if c == 0 else 760.0) + 150.0 * HS(i, 2) * (0.5 + 0.5 * H01(i, 3))
        w = 7.0 + 9.0 * H01(i, 4) ** 1.4
        hgt = w * (0.55 + 0.5 * H01(i, 5))
        out.append((cx, w, hgt, w * (0.45 + 0.35 * H01(i, 6)), int(H01(i, 7) * 3), H01(i, 8)))
    out.sort(key=lambda r: float(far_y(r[0], 2)))
    _PATHS["town"] = out
    return out


def draw_far(canvas, cam: Cam, g: dict, roofs: float = 1.0):
    with cam.layer(canvas, D_FAR):
        for which, col in ((1, g["far1"]), (2, g["far2"])):
            top = 470.0 if which == 1 else 520.0
            p = prims.linear_paint((0, top), (0, 700), [P.shade(col, 0.03), col, P.mix(col, g["fog"], 0.6)])
            canvas.drawPath(_far_path(which), p)
            if which == 2:
                canvas.drawPicture(_town_picture(g["far2"], roofs))


def _town_picture(far2, roofs):
    key = ("town_pic", tuple(round(v, 2) for v in far2), round(roofs, 2))
    pic = _PATHS.get(key)
    if pic is not None:
        return pic
    rec = skia.PictureRecorder()
    canvas = rec.beginRecording(skia.Rect.MakeLTRB(-4000, 0, 6000, 1000))
    roof_cols = (look.ROOF_RED, look.ROOF_BLUE, look.ROOF_OCHRE)
    wall = P.mix(look.PAPER, far2, 0.35)
    for (x, w, hgt, rh, rc, sh) in _town():
        y = float(far_y(x, 2)) + 3.0
        canvas.drawRect(skia.Rect.MakeLTRB(x - w / 2, y - hgt, x + w / 2, y + 4), prims.fill(P.shade(wall, -0.06 * sh)))
        roof = P.mix(roof_cols[rc], far2, 0.25 + 0.35 * (1 - roofs))
        canvas.drawPath(prims.poly_path([x - w * 0.62, x + 0.06 * w * HS(rc, 9), x + w * 0.62],
                                        [y - hgt, y - hgt - rh, y - hgt], close=True), prims.fill(roof))
    pic = rec.finishRecordingAsPicture()
    if sum(1 for k in _PATHS if k[0] == "town_pic") > 200:
        for k in [k for k in _PATHS if k[0] == "town_pic"]:
            del _PATHS[k]
    _PATHS[key] = pic
    return pic


def draw_fog_sea(canvas, cam: Cam, g: dict, t: float, density: float = 1.0, flow: float = 1.0):
    with cam.layer(canvas, D_FOG):
        look.fog_band(canvas, (-3000, 520, 6000, 700), t, density, g["fog_far"], speed=6 * flow, seed=3, alpha=0.75,
                      size=1.6)
        look.fog_band(canvas, (-3000, 585, 6000, 780), t, density, g["fog"], speed=11 * flow, seed=7, alpha=0.85,
                      size=1.2)


def _mid_path():
    if "mid" not in _PATHS:
        xs = np.arange(-4000.0, 6000.0, 16.0)
        hump = np.zeros_like(xs)
        for k, (c, w, hh) in enumerate(((-950, 520, 105), (-380, 300, 40), (720, 600, 95), (1450, 420, 70),
                                        (2350, 650, 110), (3300, 480, 80), (4300, 600, 100), (-2100, 600, 90))):
            hump = np.maximum(hump, hh * np.exp(-((xs - c) / w) ** 2))
        ys = 742.0 - hump - 6.0 * prims.value_noise(xs / 120.0, 41)
        _PATHS["mid"] = _path_under(xs, ys, 1400.0)
    return _PATHS["mid"]


def draw_mid(canvas, cam: Cam, g: dict, t: float, density: float = 1.0, flow: float = 1.0):
    with cam.layer(canvas, D_MID):
        canvas.drawPath(_mid_path(), prims.linear_paint((0, 630), (0, 790), [P.shade(g["mid"], 0.04), g["mid"],
                                                                               P.mix(g["mid"], g["fog"], 0.7)]))
        look.fog_band(canvas, (-3000, 705, 6000, 830), t, density, g["fog"], speed=16 * flow, seed=11, alpha=0.7, size=0.9)


# ---------------------------------------------------------------------------------------------
# the near hill: the main slope, lower swells in front, mottle
# ---------------------------------------------------------------------------------------------
def draw_near(canvas, cam: Cam, g: dict):
    x0, x1 = cam.xrange(1.0, 260.0)
    xs = np.arange(x0, x1 + 24.0, 24.0)
    ys = ground_y(xs)
    _, ybot = cam.inv(0, H + 40, 1.0)
    bottom = max(float(ybot), float(ys.max()) + 40)
    with cam.layer(canvas, 1.0):
        y_top = float(ys.min())
        canvas.drawPath(_path_under(xs, ys, bottom),
                        prims.linear_paint((0, y_top - 4), (0, y_top + 330), [g["crest"], g["slope"], g["foot"]],
                                           (0.0, 0.18, 1.0)))
        for (sx0, dep, k, sid) in SWELLS:
            if sx0 + 1500 < x0 or sx0 - 1500 > x1:
                continue
            top = float(ground_y(sx0)) + dep
            sxs = xs[(xs > sx0 - 1600) & (xs < sx0 + 1600)]
            if len(sxs) < 2:
                continue
            sys_ = top + k * (sxs - sx0) ** 2
            sys_ = np.minimum(sys_, bottom)
            p = prims.linear_paint((0, top - 10), (0, top + 260), [P.mix(g["swell"], g["crest"], 0.35), g["swell"],
                                                                   g["swell_foot"]], (0.0, 0.12, 1.0))
            canvas.drawPath(_path_under(sxs, sys_, bottom), p)
    return xs, ys


# ---------------------------------------------------------------------------------------------
# grass tufts: one baked atlas of variants, drawn as one drawAtlas (sway = rotation about the base)
# ---------------------------------------------------------------------------------------------
TW, TH, NT = 96, 128, 7


def _tuft_atlas():
    def draw(c):
        for v in range(NT):
            ox = v * TW + TW / 2
            nb = 4 + int(H01(v, 60) * 6)
            for b in range(nb):
                k = v * 31 + b
                bx = ox + (H01(k, 61) - 0.5) * 30
                hgt = 42 + 78 * H01(k, 62) ** 0.8
                lean = (H01(k, 63) - 0.5) * 50 + (bx - ox) * 0.9
                wb = 2.6 + 3.4 * H01(k, 64)
                tipx, tipy = bx + lean, TH - 4 - hgt
                midx, midy = bx + lean * 0.35, TH - 4 - hgt * 0.55
                p = skia.Path()
                p.moveTo(bx - wb, TH - 2)
                p.quadTo(midx - wb * 0.6, midy, tipx, tipy)
                p.quadTo(midx + wb * 0.6, midy, bx + wb, TH - 2)
                p.close()
                shade = -0.10 + 0.16 * H01(k, 65)
                cols = [P.shade(look.MEADOW_DEEP, shade - 0.05), P.shade(look.MEADOW, shade),
                        P.shade(P.mix(look.MEADOW, look.MEADOW_LIGHT, 0.6), shade)]
                c.drawPath(p, prims.linear_paint((0, TH), (0, tipy), cols, (0.0, 0.5, 1.0)))
    return prims.sprite(("hill_tufts", 2), TW * NT, TH, draw)


def _tufts():
    """Tuft sites on the near hill: clustered along x, more near the crest line (x, depth, scale, variant, key)."""
    if "tufts" in _PATHS:
        return _PATHS["tufts"]
    xs, deps, scs, vs = [], [], [], []
    for c in range(620):
        cx = -2600.0 + 8200.0 * H01(c, 70)
        dep_c = 360.0 * H01(c, 71) ** 1.7
        n = 2 + int(H01(c, 72) * 5)
        for j in range(n):
            k = c * 11 + j
            xs.append(cx + 34.0 * HS(k, 73) * (1 + dep_c / 200))
            deps.append(max(0.0, dep_c + 14.0 * HS(k, 74)))
            scs.append((0.16 + 0.22 * H01(k, 75) ** 1.3))
            vs.append(int(H01(k, 76) * NT))
    xs, deps, scs, vs = map(np.array, (xs, deps, scs, vs))
    order = np.argsort(deps, kind="stable")
    ks = np.arange(len(xs))[order]
    res = (xs[order], deps[order], scs[order], vs[order], ks, 6.28 * H01(ks, 77), 0.80 + 0.28 * H01(ks, 78))
    _PATHS["tufts"] = res
    return res


def wave_rot(xs, t, waves):
    """Gust waves travelling through the grass: waves = [(t0, x0, speed, strength, dir)] in world x;
    dir 0 runs outward both ways from x0. Returns the extra lean (radians, + = toward +x)."""
    out = np.zeros_like(xs)
    for (t0, x0, sp, st, d) in waves:
        s = t - t0
        if s < 0 or s > 6.0:
            continue
        if d == 0:
            dist = np.abs(xs - x0) - sp * s
            sign = np.sign(xs - x0)
        else:
            dist = (xs - x0) * d - sp * s
            sign = d
        out += st * 0.42 * np.exp(-(dist / 140.0) ** 2) * np.exp(-s / 2.8) * sign * (dist < 260)
    return out


def bow_rot(sx, sy, bow):
    """Grass bowing outward as a ring's edge passes: bow = (cx, cy, radius, width, strength) on screen."""
    cx, cy, rad, wd, st = bow
    d = np.hypot(sx - cx, sy - cy)
    return st * 0.5 * np.exp(-((d - rad) / wd) ** 2) * np.sign(sx - cx)


def draw_tufts(canvas, cam: Cam, t: float, sway: float, light, gust: float = 0.0, wind_dir: float = 1.0,
               waves=(), bow=None):
    """light: (r, g, b) multiplier for the baked grass colours."""
    xs, deps, scs, vs, ks, phs, shs = _tufts()
    x0, x1 = cam.xrange(1.0, 120.0)
    sel = (xs > x0) & (xs < x1)
    if not sel.any():
        return
    xs, deps, scs, vs, ks, phs, shs = xs[sel], deps[sel], scs[sel], vs[sel], ks[sel], phs[sel], shs[sel]
    gy = ground_y(xs) + deps
    sx, sy = cam.pt(xs, gy, 1.0)
    z = cam.zd(1.0)
    on = (sy > -50) & (sy < H + 140)
    if not on.any():
        return
    sx, sy, deps, scs, vs, xs, phs, shs = sx[on], sy[on], deps[on], scs[on], vs[on], xs[on], phs[on], shs[on]
    scale = scs * (1.0 + deps / 260.0) * z
    rot = (sway * (0.10 * np.sin(t * 1.3 + xs * 0.011 + phs) + 0.05 * np.sin(t * 3.1 + xs * 0.031))
           + gust * wind_dir * (0.22 + 0.08 * np.sin(t * 5.0 + xs * 0.02)))
    if waves:
        rot = rot + wave_rot(xs, t, waves)
    if bow is not None:
        rot = rot + bow_rot(sx, sy, bow)
    cs, sn = np.cos(rot) * scale, np.sin(rot) * scale
    ax, ay = TW / 2, TH - 3
    tx = sx - (cs * ax - sn * ay)
    ty = sy - (sn * ax + cs * ay)
    xf = [skia.RSXform(float(a), float(b), float(c), float(d)) for a, b, c, d in zip(cs, sn, tx, ty)]
    tex = [skia.Rect.MakeXYWH(float(v * TW), 0, TW, TH) for v in vs]
    shade = shs + np.minimum(deps, 300) / 300 * -0.18
    r, g_, b = light
    q = (np.clip(np.stack([r * shade, g_ * shade, b * shade], 1), 0, 1) * 255 + 0.5).astype(np.uint32)
    cols = (0xFF000000 | (q[:, 0] << 16) | (q[:, 1] << 8) | q[:, 2]).tolist()
    canvas.drawAtlas(_tuft_atlas(), xf, tex, cols, skia.BlendMode.kModulate, LINEAR, None, skia.Paint(AntiAlias=True))


def draw_fringe(canvas, cam: Cam, t: float, light, sway: float = 0.5, waves=(), dim: float = 0.55):
    """Big foreground grass along the bottom edge (depth 1.35: it slides past faster than the hill)."""
    D = 1.35
    x0, x1 = cam.xrange(D, 200.0)
    k0, k1 = int(math.floor(x0 / 47.0)), int(math.ceil(x1 / 47.0))
    ks = np.arange(k0, k1 + 1)
    if not len(ks):
        return
    xs = ks * 47.0 + 30.0 * HS(ks, 120)
    sx, _ = cam.pt(xs, 0.0, D)
    sy = H + 22.0 + 26.0 * H01(ks, 121)
    scale = (0.75 + 0.75 * H01(ks, 122) ** 1.5) * min(1.6, cam.zd(1.0) ** 0.5)
    rot = sway * 0.08 * np.sin(t * 1.1 + xs * 0.007) + (wave_rot(xs, t, waves) if waves else 0.0)
    cs, sn = np.cos(rot) * scale, np.sin(rot) * scale
    ax, ay = TW / 2, TH - 3
    xf = [skia.RSXform(float(a), float(b), float(c), float(d)) for a, b, c, d in
          zip(cs, sn, sx - (cs * ax - sn * ay), sy - (sn * ax + cs * ay))]
    tex = [skia.Rect.MakeXYWH(float(int(v) * TW), 0, TW, TH) for v in (H01(ks, 123) * NT).astype(int)]
    shade = dim * (0.8 + 0.3 * H01(ks, 124))
    r, g_, b = light
    q = (np.clip(np.stack([r * shade, g_ * shade, b * shade], 1), 0, 1) * 255 + 0.5).astype(np.uint32)
    cols = (0xFF000000 | (q[:, 0] << 16) | (q[:, 1] << 8) | q[:, 2]).tolist()
    canvas.drawAtlas(_tuft_atlas(), xf, tex, cols, skia.BlendMode.kModulate, LINEAR, None, skia.Paint(AntiAlias=True))


# ---------------------------------------------------------------------------------------------
# flowers: clusters of varied size and kind; each cluster opens at its own time
# ---------------------------------------------------------------------------------------------
FW, NF = 64, 3


def _flower_atlas():
    def draw(c):
        for v in range(NF):
            cx, cy = v * FW + FW / 2, FW / 2
            n = (5, 7, 4)[v]
            pr = (13.0, 15.0, 12.0)[v]
            pw = (8.5, 5.0, 9.0)[v]
            for k in range(n):
                a = 6.283 * k / n + 0.3 * HS(v * 9 + k, 80)
                px, py = cx + math.cos(a) * pr * 0.55, cy + math.sin(a) * pr * 0.55
                c.save()
                c.translate(px, py)
                c.rotate(math.degrees(a))
                c.drawOval(skia.Rect.MakeLTRB(-pr * 0.6, -pw / 2, pr * 0.6, pw / 2),
                           prims.fill((0.97 - 0.06 * H01(k, 81),) * 3))
                c.restore()
            c.drawCircle(cx, cy, 4.2 if v != 1 else 5.5, prims.fill((0.95, 0.80, 0.42)))
    return prims.sprite(("hill_flowers", 1), FW * NF, FW, draw)


FOOT_X = None          # set by the late sections: where the two stop (clusters open there one per beat)
FOOT_IDS = (1000, 1001, 1002, 1003, 1004)


def _flowers():
    if "flowers" in _PATHS:
        return _PATHS["flowers"]
    cl = []
    if FOOT_X is not None:
        for c, (dx, dep, n) in zip(FOOT_IDS, ((-105, 8, 9), (62, 16, 11), (-30, 34, 8), (135, 26, 10), (-170, 40, 7))):
            col, col2 = int(H01(c, 93) * 5), int(H01(c, 94) * 5)
            for j in range(n):
                k = c * 17 + j
                cl.append((c, FOOT_X + dx + 30.0 * HS(k, 95), max(0.0, dep + 10.0 * HS(k, 96)),
                           0.30 + 0.30 * H01(k, 97) ** 1.5, int(H01(k, 98) * NF), col if H01(k, 99) < 0.7 else col2))
    for c in range(260):
        cx = -1400.0 + 6400.0 * H01(c, 90) ** 0.95
        dep = 300.0 * H01(c, 91) ** 1.5
        n = 3 + int(H01(c, 92) ** 1.6 * 9)
        col = int(H01(c, 93) * 5)
        col2 = int(H01(c, 94) * 5)
        for j in range(n):
            k = c * 17 + j
            cl.append((c, cx + 26.0 * HS(k, 95) * (1 + n / 6), max(0.0, dep + 12.0 * HS(k, 96)),
                       0.22 + 0.32 * H01(k, 97) ** 1.5, int(H01(k, 98) * NF), col if H01(k, 99) < 0.75 else col2))
    arr = np.array(cl, dtype=np.float64)
    arr = arr[np.argsort(arr[:, 2], kind="stable")]
    _PATHS["flowers"] = arr
    return arr


def draw_flowers(canvas, cam: Cam, t: float, open_fn, light=(1, 1, 1), sway: float = 0.3):
    """open_fn(cluster_ids array, xs, ys) -> 0..1 openness per flower."""
    arr = _flowers()
    x0, x1 = cam.xrange(1.0, 60.0)
    sel = (arr[:, 1] > x0) & (arr[:, 1] < x1)
    if not sel.any():
        return
    a = arr[sel]
    xs, deps = a[:, 1], a[:, 2]
    wy = ground_y(xs) + deps
    op = np.asarray(open_fn(a[:, 0].astype(int), xs, wy), dtype=np.float64)
    vis = op > 0.01
    if not vis.any():
        return
    a, xs, wy, op = a[vis], xs[vis], wy[vis], op[vis]
    sx, sy = cam.pt(xs, wy, 1.0)
    z = cam.zd(1.0)
    e = op                                   # callers pass eased openness (may overshoot 1)
    scale = a[:, 3] * (1 + a[:, 2] / 260.0) * z * (0.2 + 0.8 * e)
    lift = scale * 14.0 + 3.0 * z
    sy = sy - lift + sway * 2.0 * np.sin(t * 1.5 + xs * 0.02)
    rot = 6.283 * prims.hash01(np.arange(len(xs)) + 7, 100) + 0.08 * np.sin(t + xs)
    cs, sn = np.cos(rot) * scale, np.sin(rot) * scale * 0.7
    tx = sx - (cs * FW / 2 - sn * FW / 2)
    ty = sy - (sn * FW / 2 + cs * FW / 2 * 0.7)
    xf = [skia.RSXform(float(p), float(q), float(r), float(s)) for p, q, r, s in zip(cs, sn, tx, ty)]
    tex = [skia.Rect.MakeXYWH(float(int(v) * FW), 0, FW, FW) for v in a[:, 4]]
    lr, lg, lb = light
    cols = []
    for ci, o in zip(a[:, 5].astype(int), e):
        r, g, b = look.FLOWERS[ci]
        cols.append(sk((r * lr, g * lg, b * lb), float(min(1.0, max(0.0, o) * 1.4))))
    canvas.drawAtlas(_flower_atlas(), xf, tex, cols, skia.BlendMode.kModulate, LINEAR, None, skia.Paint(AntiAlias=True))


# ---------------------------------------------------------------------------------------------
# soft ground light: rain-green patches and sunlit pools (squashed soft discs, outside the grade)
# ---------------------------------------------------------------------------------------------
def soft_patches(canvas, cam: Cam, xs, deps, rs, color, alphas, squash: float = 0.32, additive: bool = False):
    xs, deps, rs, alphas = (np.asarray(v, dtype=np.float64) for v in (xs, deps, rs, alphas))
    if not len(xs):
        return
    sx, sy = cam.pt(xs, ground_y(xs) + deps, 1.0)
    z = cam.zd(1.0)
    canvas.save()
    canvas.scale(1.0, squash)
    prims.draw_sprites(canvas, prims.soft_disc(64), sx, sy / squash, rs * z / 32.0, color, alphas, additive=additive)
    canvas.restore()


# ---------------------------------------------------------------------------------------------
# the three paper cut-outs (knee-high, flat, on little stands): sign, figure, shards
# ---------------------------------------------------------------------------------------------
def _cutout_paths(kind):
    key = ("cut", kind)
    if key in _PATHS:
        return _PATHS[key]
    body = skia.Path()
    marks = skia.Path()
    if kind == 0:      # a speech-bubble sign full of scribble, on a post
        n = 26
        a = np.linspace(0, 2 * np.pi, n, endpoint=False)
        rr = 1 + 0.06 * HS(np.arange(n), 110)
        bx, by = 0.62 * rr * np.cos(a), 0.68 + 0.30 * rr * np.sin(a)
        body.addPoly([skia.Point(float(x), float(-y)) for x, y in zip(bx, by)], True)
        body.addPoly([skia.Point(-0.18, -0.42), skia.Point(-0.34, -0.22), skia.Point(-0.02, -0.40)], True)
        body.addRect(skia.Rect.MakeLTRB(-0.035, -0.40, 0.035, 0.0))
        pts = []
        for k in range(15):
            u = k / 14
            pts.append(skia.Point(-0.42 + 0.84 * u, -(0.68 + (0.13 if k % 2 else -0.11) + 0.04 * HS(k, 111))))
        marks.addPoly(pts, False)
        pts = [skia.Point(-0.30 + 0.55 * k / 8, -(0.60 + (0.07 if k % 2 else -0.06))) for k in range(9)]
        marks.addPoly(pts, False)
    elif kind == 1:    # a tall figure bending over, pointing
        xy = [(-0.16, 0.0), (-0.12, 0.38), (-0.20, 0.62), (-0.10, 0.80), (0.05, 0.95), (0.20, 0.98),
              (0.30, 0.90), (0.30, 0.86), (0.58, 0.66), (0.62, 0.62), (0.56, 0.60), (0.26, 0.76),
              (0.10, 0.70), (0.06, 0.40), (0.10, 0.0), (0.0, 0.0), (-0.03, 0.36), (-0.06, 0.36), (-0.07, 0.0)]
        body.addPoly([skia.Point(x, -y) for x, y in xy], True)
        body.addCircle(0.30, -1.02, 0.10)
    else:              # a clump of shards
        for k, (x, w, h) in enumerate(((-0.30, 0.20, 0.62), (-0.10, 0.24, 0.98), (0.12, 0.18, 0.74),
                                       (0.30, 0.16, 0.50), (0.0, 0.14, 0.40))):
            tip = x + 0.10 * HS(k, 112)
            body.addPoly([skia.Point(x - w / 2, 0.0), skia.Point(tip, -h), skia.Point(x + w / 2, 0.0),
                          skia.Point(x + w * 0.1, -h * 0.35)], True)
    stand = skia.Path()
    stand.addPoly([skia.Point(-0.12, 0.0), skia.Point(0.12, 0.0), skia.Point(0.02, -0.16)], True)
    _PATHS[key] = (body, marks, stand)
    return _PATHS[key]


def draw_cutout(canvas, kind: int, x: float, y: float, hc: float, stand: float, paper, ink):
    """x, y: screen base; hc: height px; stand: 1 upright (a little over 1 = stretched by a bounce),
    toward 0 lying flat backward."""
    if stand <= 0.0:
        return
    sy = max(0.06, stand)
    look.shadow(canvas, x + hc * 0.15 * (1 - sy), y + 2, hc * (1.0 + 0.5 * (1 - sy)), 0.30 + 0.15 * (1 - sy), look.INK, 0.25)
    body, marks, stand = _cutout_paths(kind)
    canvas.save()
    canvas.translate(x, y)
    canvas.skew(-0.25 * (1 - sy), 0)
    canvas.scale(hc, hc * sy)
    canvas.drawPath(body, prims.linear_paint((0, -1.0), (0, 0.0), [P.shade(paper, 0.03), paper, P.shade(paper, -0.08)]))
    if not marks.isEmpty():
        sp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=0.022, Color=sk(ink, 0.55))
        sp.setStrokeJoin(skia.Paint.kRound_Join)
        canvas.drawPath(marks, sp)
    canvas.drawPath(stand, prims.fill(P.shade(paper, -0.18)))
    canvas.restore()


# ---------------------------------------------------------------------------------------------
# the kite: a paper diamond with a bowed tail, on a sagging line
# ---------------------------------------------------------------------------------------------
def draw_kite(canvas, hx: float, hy: float, kx: float, ky: float, s: float, t: float, color, alpha: float = 1.0):
    sway = 0.10 * math.sin(t * 1.4) + 0.05 * math.sin(t * 3.3)
    # the line: a soft catenary-ish curve from the hand up to the kite
    mx, my = (hx + kx) / 2, (hy + ky) / 2 + 0.10 * math.hypot(kx - hx, ky - hy)
    line = skia.Path()
    line.moveTo(hx, hy)
    line.quadTo(mx, my, kx, ky + s * 0.45)
    canvas.drawPath(line, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.3,
                                     Color=sk(look.hex_rgb("5B5560"), 0.75 * alpha)))
    # the tail: small bows on a wavy string trailing downwind
    tail = skia.Path()
    tx0, ty0 = kx, ky + s * 0.95
    tail.moveTo(tx0, ty0)
    pts = []
    for k in range(1, 9):
        u = k / 8
        px = tx0 + s * 1.6 * u + s * 0.25 * math.sin(t * 4.0 - u * 6)
        py = ty0 + s * 1.1 * u
        tail.lineTo(px, py)
        pts.append((px, py))
    canvas.drawPath(tail, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.1,
                                     Color=sk(look.hex_rgb("5B5560"), 0.6 * alpha)))
    for k, (px, py) in enumerate(pts[1::2]):
        bc = look.FLOWERS[(k * 2 + 1) % 5]
        canvas.drawPath(prims.poly_path([px - 5, px + 5, px + 5, px - 5], [py - 4, py + 4, py - 4, py + 4], close=True),
                        prims.fill(bc, 0.9 * alpha))
    canvas.save()
    canvas.translate(kx, ky)
    canvas.rotate(math.degrees(sway) - 12)
    dia = prims.poly_path([0, s * 0.62, 0, -s * 0.62], [-s * 0.95, -s * 0.15, s * 0.95, -s * 0.15], close=True)
    canvas.drawPath(dia, prims.linear_paint((-s, -s), (s, s), [P.shade(color, 0.06), color, P.shade(color, -0.10)],
                                            alpha=alpha))
    half = prims.poly_path([0, s * 0.62, 0], [-s * 0.95, -s * 0.15, s * 0.95], close=True)
    canvas.drawPath(half, prims.fill(look.INK, 0.10 * alpha))
    canvas.restore()
