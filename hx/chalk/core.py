"""hx.chalk.core: the medium. Palette, hashes, paper, tooth, the Frame, the camera, the strokes.

Everything is drawn by code (skia + numpy); all randomness is hashed, so a frame is a pure function
of its time. The medium in six rules:

  * a stroke is a variable-width ribbon (pressure taper at both ends, pressure noise along it) filled
    through a paper-tooth mask, plus a wider, sparser pass for the dusty edge;
  * the tooth is FIXED in screen space (the paper never moves); a line that moves is chalk dragged
    over that paper. Only stroke GEOMETRY boils, on twos (Frame.k), by a fraction of a pixel;
  * a line is never straight: a slow hand wobble that belongs to the drawing (a function of the
    stroke's own arc length in world units, so it zooms rigidly) plus the small boil;
  * areas are coloured in the way a child does it: a zigzag that turns short of, or over, the outline
    (hatch), on a thin rubbed base; a zigzag larger than a prop is seated and does not boil;
  * every drawing function takes WORLD coordinates and sizes and maps them through F.cam itself; the
    canvas is never scaled. A line thinner than its floor keeps the floor width and loses pressure;
  * light is rubbed pastel (smudge, wash) and one additive bloom in the finish.
"""
from __future__ import annotations

import math
from contextlib import contextmanager

import numpy as np
import skia
from scipy.ndimage import gaussian_filter, zoom as _zoom

from mv.engine.palette import mix, sk
from mv.engine.prims import hash01

__all__ = ["W", "H", "FPS", "CX", "CY", "BOIL", "HOLDS", "boil_clock", "LINE_FLOOR", "GRAINS", "PLUS", "C", "hexc", "mix", "sk", "vn", "rnd", "rsym",
           "htab", "smooth", "ease", "ease_out", "seg", "ramp", "A", "resample", "fit", "spline", "arc", "blob", "rrect_pts",
           "rect_pts", "path_of", "hand", "trim", "ribbon", "zigzag", "Cam", "Post", "Frame", "chalk", "scrib", "fill", "disc",
           "loop", "hatch", "smudge", "wash", "specks", "dashes", "paper_night"]

W, H, FPS = 1920, 1080, 30
CX, CY = W / 2.0, H / 2.0
BOIL = 15.0                      # boil rate in 1/s: on twos at 30 fps
# The two true silences of the recording. In them the picture stands still: the line does not boil, the
# rain hangs in the air, the scribble does not churn; only what acts (poses, the camera) moves. Both
# lengths are whole boil steps (39 and 124), so the pairs of frames stay aligned afterwards.
HOLDS = ((56.0, 58.6), (193.0, 201.0 + 4.0 / 15.0))


def boil_clock(t: float) -> float:
    """Time with the two silences taken out: the clock of everything that is alive but not acting."""
    return t - sum(min(max(t - a, 0.0), b - a) for a, b in HOLDS)
TS = 512                         # tooth tile size
LINE_FLOOR = 1.6                 # px: a main line is never drawn thinner than this (it fades instead)
BOIL_AMP = 0.45                  # px of boil for a wob = 1 line at zoom 1
BOIL_ZMIN = 0.45                 # the boil does not shrink below this zoom (far lines stay alive)
BOIL_ZMAX = 1.6                  # ... nor grow above this one (close-ups do not shake)
SEAT_AREA = 200_000.0            # px^2 on screen: a hatch whose box is larger does not boil
LINEAR = skia.SamplingOptions(skia.FilterMode.kLinear)
NEAREST = skia.SamplingOptions()
REPEAT = skia.TileMode.kRepeat
PLUS = skia.BlendMode.kPlus


def hexc(h: str):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)


# --------------------------------------------------------------------------
# palette
# --------------------------------------------------------------------------
class C:
    # night paper and chalks (nothing here is fully saturated except the amber family)
    PAPER = hexc("1d2437")
    PAPER_DEEP = hexc("121724")
    PAPER_HAZE = hexc("2c3652")
    KNOCK = hexc("171c2b")          # what a figure rubs out behind itself
    CHALK = hexc("efeadc")
    CHALK_COOL = hexc("b9c7e0")
    CHALK_BLUE = hexc("8ea3cc")
    CHALK_DIM = hexc("66759a")
    CHALK_FAR = hexc("4a5676")
    MOON = hexc("a9bde0")
    GLOOM = hexc("05060a")
    GLOOM_MID = hexc("11131f")
    GLOOM_EDGE = hexc("464d6b")
    AMBER = hexc("f7b548")
    AMBER_DEEP = hexc("ea8a2c")
    AMBER_PALE = hexc("ffdf9e")
    AMBER_GLOW = hexc("ffc66a")
    # day paper and crayons (allowed only after the colour moment)
    DAY = hexc("f5ead2")
    DAY_SHADE = hexc("e6d5b4")
    PENCIL = hexc("3d2f2a")
    SKY = hexc("3d9be9")
    SKY_PALE = hexc("8cc8f5")
    SUN = hexc("ffc61a")
    ORANGE = hexc("ff8a1f")
    RED = hexc("ee3d3a")
    PINK = hexc("ff7fae")
    GREEN = hexc("44b556")
    GREEN_DEEP = hexc("23884a")
    LIME = hexc("a5d63f")
    PURPLE = hexc("8660d3")
    TEAL = hexc("18a9a5")
    BLUE = hexc("2b6fd8")
    SKIN = hexc("ffd9b6")
    # golden hour in rubbed pastel: the colour world of the film (day skin). Soft, warm, never primary.
    SKY_HI = hexc("9dbfd6")         # dusty blue, top of the sky
    SKY_MID = hexc("f3dcae")        # cream-apricot
    SKY_LOW = hexc("f2b488")        # peach at the horizon
    SUN_CORE = hexc("fff0b8")
    SUN_HALO = hexc("ffc97a")
    HILL_FAR = hexc("a9b6c9")       # hazy blue-violet: distance against the peach horizon
    HILL_MID = hexc("a3bd8c")       # sage
    HILL_NEAR = hexc("93ba64")      # warm green
    HILL_LIT = hexc("e8d679")       # the sunward side
    HILL_SHADE = hexc("568a72")     # the cool side
    SHADOW = hexc("7b6f92")         # long violet-grey shadows (low alpha)
    CORAL = hexc("ee7f6c")
    MUSTARD = hexc("efb740")
    LILAC = hexc("b49cd4")
    ROSE = hexc("f1a4b4")
    CREAM = hexc("fff7e8")
    SEA = hexc("6fb6ae")
    JUMPER = hexc("5e8fce")         # the child's jumper in colour
    COAT = hexc("f3a83c")           # the friend's coat in colour
    # evening: the same world an hour later (the outro's end and the coda)
    EVE_HI = hexc("c9b6c9")         # mauve
    EVE_MID = hexc("f4c08c")
    EVE_LOW = hexc("ef8f66")        # orange-rose at the horizon
    EVE_PAPER = hexc("f3dfc0")


# --------------------------------------------------------------------------
# hashes and easing (all randomness comes from hash01)
# --------------------------------------------------------------------------
TAB = hash01(np.arange(8192), 9001)


def vn(x, seed: int = 0):
    """1-D value noise in 0..1 (C1), array or scalar."""
    x = np.asarray(x, dtype=np.float64)
    i = np.floor(x).astype(np.int64)
    f = x - i
    f = f * f * (3.0 - 2.0 * f)
    o = int(seed) * 131
    a = TAB[(i + o) & 8191]
    b = TAB[(i + 1 + o) & 8191]
    return a + (b - a) * f


def rnd(seed: int, salt: int = 0) -> float:
    """Scalar hash in 0..1."""
    return float(TAB[((int(seed) * 2654435761 + int(salt) * 40503 + 12345) >> 5) & 8191])


def rsym(seed: int, salt: int = 0) -> float:
    return rnd(seed, salt) * 2.0 - 1.0


def htab(i, mul: int, add: int = 0):
    """Hashed 0..1 per index (array in, array out): TAB[(i * mul + add) mod 8192]."""
    return TAB[(np.asarray(i) * int(mul) + int(add)) & 8191]


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def ease(x: float) -> float:
    x = min(1.0, max(0.0, float(x)))
    return x * x * (3.0 - 2.0 * x)


def ease_out(x: float, p: float = 3.0) -> float:
    x = min(1.0, max(0.0, float(x)))
    return 1.0 - (1.0 - x) ** p


def seg(t: float, a: float, b: float) -> float:
    """0 before a, 1 after b, linear between."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return min(1.0, max(0.0, (t - a) / (b - a)))


def ramp(x: float, a: float, b: float) -> float:
    """Smooth 0..1 as x goes from a to b."""
    return ease(seg(x, a, b))


# --------------------------------------------------------------------------
# textures (baked once per process)
# --------------------------------------------------------------------------
_CACHE: dict = {}


def white(shape, salt):
    n = int(shape[0] * shape[1])
    return hash01(np.arange(n), salt).reshape(shape)


def _rank(a):
    """Rank-normalise to a uniform 0..1 field, so a threshold equals a coverage."""
    flat = a.ravel()
    order = np.argsort(flat, kind="stable")
    out = np.empty_like(flat)
    out[order] = np.linspace(0.0, 1.0, flat.size)
    return out.reshape(a.shape)


def _norm(a):
    return (a - a.mean()) / (a.std() + 1e-9)


def tooth_field():
    """The paper's tooth: uniform 0..1 tile; low = a pit the chalk skips first."""
    if "T" not in _CACHE:
        s = (TS, TS)
        f = (0.80 * _norm(gaussian_filter(white(s, 11), 0.62, mode="wrap"))
             + 0.50 * _norm(gaussian_filter(white(s, 12), 1.3, mode="wrap"))
             + 0.20 * _norm(gaussian_filter(white(s, 13), 3.4, mode="wrap"))
             + 0.07 * _norm(gaussian_filter(white(s, 14), 12.0, mode="wrap")))
        _CACHE["T"] = _rank(f)
    return _CACHE["T"]


def a8(alpha01):
    a = np.ascontiguousarray(np.clip(alpha01 * 255.0 + 0.5, 0, 255).astype(np.uint8))
    return skia.Image.frombytes(a.tobytes(), (a.shape[1], a.shape[0]), skia.kAlpha_8_ColorType)


def rgb_image(img01):
    h, w, _ = img01.shape
    a = np.empty((h, w, 4), dtype=np.uint8)
    a[..., :3] = np.clip(img01 * 255.0 + 0.5, 0, 255).astype(np.uint8)
    a[..., 3] = 255
    return skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType, copy=True)


# name: (coverage, softness of the threshold, floor = how much chalk reaches even the pits)
GRAINS = {"dense": (0.95, 0.14, 0.42), "mid": (0.80, 0.18, 0.12), "sparse": (0.58, 0.20, 0.0),
          "dust": (0.26, 0.16, 0.0), "soft": (0.66, 0.60, 0.10), "glow": (0.70, 0.80, 0.55)}


RUBBED = ("soft", "glow")          # the grains of rubbed tone: the tooth plus the marks of the rubbing hand
WIDE = "~"                         # suffix of their sideways-wiped variant (picked by smudge and wash themselves)


def rub_field(wide: bool = False):
    """Frame-sized uniform 0..1 field for rubbed pastel: the paper's tooth under the marks of the
    rubbing hand. Round patches (a glow, a halo, a sky) are dabbed: soft blotches. Wide flat ones
    (mist, a contact shadow, a pool or a shaft of light) are wiped sideways: smears."""
    key = "Rw" if wide else "R"
    if key not in _CACHE:
        if wide:
            mark = 0.75 * lowfreq(W, H, 2.6, 51, aniso=11.0) + 0.25 * lowfreq(W, H, 7, 52, aniso=4.0)
        else:
            mark = 0.5 * lowfreq(W, H, 6.0, 53) + 0.5 * lowfreq(W, H, 15.0, 54)
        _CACHE[key] = _rank(0.30 * _norm(tooth_tile()) + 1.0 * _norm(mark))
    return _CACHE[key]


def tooth_images():
    """A8 coverage masks: chalk pressed hard ('dense') ... barely touching ('dust'), as 512 px tiles;
    the rubbed grains (and their sideways variants, name + WIDE) are frame-sized. All are fixed to the screen."""
    if "tooth" not in _CACHE:
        out = {}
        for name, (cov, soft, floor) in GRAINS.items():
            for key, T in ((name, rub_field()), (name + WIDE, rub_field(True))) if name in RUBBED else ((name, tooth_field()),):
                m = floor + (1.0 - floor) * np.clip((T - (1.0 - cov)) / soft + 0.5, 0.0, 1.0)
                out[key] = a8(m.mean() + (m - m.mean()) * 0.6 if name in RUBBED else m)
        _CACHE["tooth"] = out
    return _CACHE["tooth"]


def lowfreq(w, h, cell, salt, aniso=1.0):
    """Smooth 0..1 noise at pixel size (h, w), features about `cell` px (x stretched by aniso)."""
    gw, gh = max(3, int(w / (cell * aniso)) + 3), max(3, int(h / cell) + 3)
    g = white((gh, gw), salt)
    z = _zoom(g, (h / (gh - 2.0), w / (gw - 2.0)), order=3)[:h, :w]
    if z.shape != (h, w):
        z = np.pad(z, ((0, h - z.shape[0]), (0, w - z.shape[1])), mode="edge")
    return np.clip(z, 0.0, 1.0)


def tooth_tile(w=W, h=H):
    return np.tile(tooth_field(), (h // TS + 1, w // TS + 1))[:h, :w]


def paper_night(w=W, h=H):
    """Dark sugar paper: cloudy rubbed-out chalk ghosts, wipe streaks, tooth, vignette."""
    key = ("pn", w, h)
    if key not in _CACHE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
        u, v = xx / w, yy / h
        cloud = 0.55 * lowfreq(w, h, 420, 21) + 0.30 * lowfreq(w, h, 150, 22) + 0.15 * lowfreq(w, h, 46, 23)
        streak = lowfreq(w, h, 26, 24, aniso=14.0) * 0.6 + lowfreq(w, h, 9, 25, aniso=30.0) * 0.4
        haze = np.clip((cloud - 0.42) * 1.9, 0, 1) * (0.55 + 0.45 * streak)
        vig = np.clip(((u - 0.5) ** 2 * 1.25 + (v - 0.46) ** 2 * 1.6) * 1.9, 0, 1) ** 1.3
        T = tooth_tile(w, h)
        a = np.array(C.PAPER)[None, None, :]
        hz = np.array(C.PAPER_HAZE)[None, None, :]
        dp = np.array(C.PAPER_DEEP)[None, None, :]
        img = a + (hz - a) * (haze * 0.55)[..., None]
        img = img + (dp - img) * (vig * 0.85)[..., None]
        img = img * (1.0 + 0.10 * (T - 0.5))[..., None] + 0.012 * (T - 0.5)[..., None]
        img += (white((h, w), 26) - 0.5)[..., None] * 0.012
        _CACHE[key] = rgb_image(img)
    return _CACHE[key]


def _grain_image():
    """Film grain as a translucent grey overlay tile."""
    if "grain" not in _CACHE:
        n = _norm(gaussian_filter(white((512, 512), 41), 0.6, mode="wrap"))
        a = np.zeros((512, 512, 4), dtype=np.uint8)
        v = np.clip(n * 0.5, -1, 1)
        a[..., 0:3] = np.where(v > 0, 255, 0)[..., None]
        a[..., 3] = np.clip(np.abs(v) * 30, 0, 255).astype(np.uint8)
        a[..., :3] = (a[..., :3].astype(np.float64) * a[..., 3:4] / 255.0).astype(np.uint8)   # premultiply
        _CACHE["grain"] = skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType, copy=True)
    return _CACHE["grain"]


def _vignette_image():
    if "vig" not in _CACHE:
        h, w = H // 4, W // 4
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
        f = np.clip((((xx + 0.5) / w - 0.5) ** 2 * 1.15 + ((yy + 0.5) / h - 0.5) ** 2 * 1.35) * 2.0, 0, 1) ** 1.6
        a = np.zeros((h, w, 4), dtype=np.uint8)
        a[..., 3] = np.clip(f * 255.0 + 0.5, 0, 255).astype(np.uint8)
        _CACHE["vig"] = skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType, copy=True)
    return _CACHE["vig"]


# --------------------------------------------------------------------------
# geometry helpers (plain arrays of points; no camera here)
# --------------------------------------------------------------------------
def A(*pts):
    return np.asarray(pts, dtype=np.float64)


def resample(P, step: float):
    """Polyline resampled at about `step`. Returns (points, arclength)."""
    P = np.asarray(P, dtype=np.float64)
    d = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
    s = np.concatenate([[0.0], np.cumsum(d)])
    L = float(s[-1])
    if L < 1e-6:
        return P[:1].repeat(3, axis=0), np.zeros(3)
    n = max(3, int(L / step) + 2)
    u = np.linspace(0.0, L, n)
    return np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], axis=1), u


def fit(P, n: int):
    """Polyline resampled to exactly n points, evenly along its arc length."""
    P = np.asarray(P, dtype=np.float64)
    d = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
    s = np.concatenate([[0.0], np.cumsum(d)])
    u = np.linspace(0.0, s[-1], n)
    return np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], axis=1)


def spline(Cp, n: int = 24):
    """Catmull-Rom curve through control points."""
    Cp = np.asarray(Cp, dtype=np.float64)
    k = len(Cp)
    if k < 3:
        return Cp
    P = np.vstack([2 * Cp[0] - Cp[1], Cp, 2 * Cp[-1] - Cp[-2]])
    t = np.linspace(0.0, k - 1.0, n)
    i = np.minimum(t.astype(int), k - 2)
    f = (t - i)[:, None]
    p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)


def arc(cx, cy, rx, ry, a0, a1, n=24, rot=0.0):
    """Ellipse arc, angles in radians (y down)."""
    a = np.linspace(a0, a1, n)
    x, y = np.cos(a) * rx, np.sin(a) * ry
    cr, sr = math.cos(rot), math.sin(rot)
    return np.stack([cx + x * cr - y * sr, cy + x * sr + y * cr], axis=1)


def blob(cx, cy, rx, ry, seed, rough=0.06, n=40, rot=0.0):
    """A hand-drawn closed round shape (closed polyline, first point repeated)."""
    a = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    r = 1.0 + rough * (2.0 * vn(a / (2 * math.pi) * 5.0, seed) - 1.0)
    r = r + (r[0] - (1.0 + rough * (2.0 * float(vn(5.0, seed)) - 1.0))) * (a / (2 * math.pi))   # close the loop
    x, y = np.cos(a) * rx * r, np.sin(a) * ry * r
    cr, sr = math.cos(rot), math.sin(rot)
    P = np.stack([cx + x * cr - y * sr, cy + x * sr + y * cr], axis=1)
    return np.vstack([P, P[:1]])


def rrect_pts(l, t, r, b, rad, n=6):
    """Rounded rectangle as a closed polyline."""
    rad = min(rad, (r - l) / 2, (b - t) / 2)
    out = []
    for cx, cy, a0 in ((r - rad, t + rad, -math.pi / 2), (r - rad, b - rad, 0.0),
                       (l + rad, b - rad, math.pi / 2), (l + rad, t + rad, math.pi)):
        out.append(arc(cx, cy, rad, rad, a0, a0 + math.pi / 2, n))
    P = np.vstack(out)
    return np.vstack([P, P[:1]])


def rect_pts(l, t, r, b):
    return A((l, t), (r, t), (r, b), (l, b), (l, t))


def path_of(P, close=False) -> skia.Path:
    """skia path through SCREEN points (no camera: use F.path for world points)."""
    it = np.asarray(P, dtype=np.float64).tolist()
    p = skia.Path()
    p.moveTo(*it[0])
    for x, y in it[1:]:
        p.lineTo(x, y)
    if close:
        p.close()
    return p


def hand(P, seed: int, k: int, wob: float = 1.0, step: float = 6.0, boil: float = 1.0, z: float = 1.0,
         baked: bool = False):
    """Resample a world polyline and give it a hand: the static wobble of the drawing (world units,
    so it zooms rigidly) plus the boil of step k (screen units, floored so far lines stay alive).

    wob scales both (1.0 = a mid-shot line); step is the sample spacing in screen px; baked = the
    static wobble is already in P (morphing strokes). Returns (world points, world arclength).
    """
    q = 1.0 if 0.71 < z < 1.41 else 2.0 ** round(math.log2(1.0 / z))      # sample spacing by octaves of zoom
    P, s = resample(P, step * q)
    if wob <= 0.0:
        return P, s
    o = rnd(seed, 3) * 400.0
    dx = dy = 0.0
    if not baked:
        a1 = 1.7 * wob * ramp(z, 0.10, 0.22)          # each wobble fades out before it would alias
        a2 = 0.75 * wob * ramp(z, 0.35, 0.70)
        dx = a1 * (2 * vn(s / 52.0 + o, seed) - 1) + a2 * (2 * vn(s / 17.0 + o, seed + 1) - 1)
        dy = a1 * (2 * vn(s / 52.0 + o, seed + 2) - 1) + a2 * (2 * vn(s / 17.0 + o, seed + 3) - 1)
    b = BOIL_AMP * wob * boil * min(BOIL_ZMAX, max(z, BOIL_ZMIN)) / z
    if b > 0.0:
        kk = int(seed) * 3 + int(k) * 7919
        u = s * z / 24.0 + o
        dx = dx + b * (2 * vn(u, kk) - 1)
        dy = dy + b * (2 * vn(u, kk + 1) - 1)
    # the ends wobble less, so strokes still meet where they were aimed
    L = s[-1] + 1e-9
    e = 0.45 + 0.55 * smooth(np.minimum(s, L - s) / (0.18 * L + 6.0))
    return P + np.stack([dx * e, dy * e], axis=1), s


def trim(P, s, f0: float, f1: float):
    """Part of a resampled polyline between arclength fractions f0..f1."""
    L = s[-1]
    a, b = f0 * L, f1 * L
    if b - a < 1e-6:
        return None, None
    m = (s > a) & (s < b)
    pa = np.array([np.interp(a, s, P[:, 0]), np.interp(a, s, P[:, 1])])
    pb = np.array([np.interp(b, s, P[:, 0]), np.interp(b, s, P[:, 1])])
    return np.vstack([pa, P[m], pb]), np.concatenate([[0.0], s[m] - a, [b - a]])


_CAP = np.array([[math.cos(q * math.pi / 2), math.sin(q * math.pi / 2)] for q in (0.5, 0.0, -0.5)])


def ribbon(P, s, w: float, seed: int, taper: float = 0.5, var: float = 0.2, sn=None, lead: float = 0.0) -> skia.Path:
    """Closed outline of a variable-width stroke along SCREEN points P with arclength s
    (pressure taper + pressure noise; sn = the arclength the noise is keyed to, default s;
    lead = px behind the far end over which the pressure is still building: a stroke being drawn)."""
    d = np.gradient(P, axis=0)
    ln = np.hypot(d[:, 0], d[:, 1]) + 1e-9
    nrm = np.stack([-d[:, 1] / ln, d[:, 0] / ln], axis=1)
    L = s[-1] + 1e-9
    tz = min(0.5 * L, 2.4 * w + 2.0)
    env = 1.0 - (1.0 - taper) * (1.0 - smooth(np.minimum(s, L - s) / tz))
    if lead > 0.0:
        env = env * (0.45 + 0.55 * smooth((L - s) / lead))
    sn = s if sn is None else sn
    prof = (0.5 * w * env * (1.0 + var * (2.0 * vn(sn / 31.0 + rnd(seed, 5) * 99.0, seed + 101) - 1.0)))[:, None]
    # round caps: three points round each end, between the two normals through the tangent
    t1, t0 = d[-1] / ln[-1], -d[0] / ln[0]
    cap1 = P[-1] + prof[-1] * (_CAP[:, :1] * t1 + _CAP[:, 1:] * nrm[-1])
    cap0 = P[0] + prof[0] * (_CAP[:, :1] * t0 - _CAP[:, 1:] * nrm[0])
    return path_of(np.vstack([P + nrm * prof, cap1, (P - nrm * prof)[::-1], cap0]), True)


def zigzag(poly, ang: float, gap: float, seed: int, jit: float = 0.35, over: float = 0.5, inset: float = 0.0):
    """The zigzag a child colours a shape with: turns short of, or over, the outline.

    poly: closed outline (N, 2). Scan lines at `ang` (radians), spaced `gap`.
    Returns a polyline (M, 2), or None if the shape is too small.
    """
    poly = np.asarray(poly, dtype=np.float64)
    ca, sa = math.cos(ang), math.sin(ang)
    x = poly[:, 0] * ca + poly[:, 1] * sa             # rotate so that scan lines are horizontal
    y = -poly[:, 0] * sa + poly[:, 1] * ca
    y0, y1 = y.min(), y.max()
    m = int((y1 - y0) / gap)
    if m < 1:
        return None
    j = np.arange(m)
    ys = y0 + (j + 0.5 + jit * (2 * TAB[(j * 13 + seed * 71) & 8191] - 1)) * gap
    xb, yb = np.roll(x, -1), np.roll(y, -1)
    out = []
    for i, yy in enumerate(ys):
        cr = ((y <= yy) & (yb > yy)) | ((yb <= yy) & (y > yy))
        if not cr.any():
            continue
        xs = x[cr] + (yy - y[cr]) / (yb[cr] - y[cr]) * (xb[cr] - x[cr])
        lo, hi = xs.min() + inset, xs.max() - inset
        if hi <= lo:
            continue
        lo += gap * over * (2 * TAB[(i * 29 + seed * 53 + 7) & 8191] - 1.25)
        hi -= gap * over * (2 * TAB[(i * 31 + seed * 59 + 11) & 8191] - 1.25)
        out.append((lo, yy) if i % 2 == 0 else (hi, yy))
        out.append((hi, yy) if i % 2 == 0 else (lo, yy))
    if len(out) < 2:
        return None
    Z = np.asarray(out)
    return np.stack([Z[:, 0] * ca - Z[:, 1] * sa, Z[:, 0] * sa + Z[:, 1] * ca], axis=1)


# --------------------------------------------------------------------------
# the camera
# --------------------------------------------------------------------------
class Cam:
    """World -> screen: ((wx - cx) * zoom + 960, (wy - cy) * zoom + 540). No rotation.
    World units are the screen pixels of the 1920x1080 frame at Cam() (centre 960, 540, zoom 1)."""
    __slots__ = ("cx", "cy", "zoom")

    def __init__(self, cx: float = CX, cy: float = CY, zoom: float = 1.0):
        self.cx, self.cy, self.zoom = float(cx), float(cy), float(zoom)

    def __repr__(self):
        return f"Cam({self.cx:.1f}, {self.cy:.1f}, {self.zoom:.3f})"

    @classmethod
    def at(cls, x: float, y: float, zoom: float = 1.0, sx: float = CX, sy: float = CY) -> "Cam":
        """The camera that shows world point (x, y) at screen point (sx, sy)."""
        return cls(x - (sx - CX) / zoom, y - (sy - CY) / zoom, zoom)

    def to_screen(self, x, y):
        return (x - self.cx) * self.zoom + CX, (y - self.cy) * self.zoom + CY

    def to_world(self, sx, sy):
        return (sx - CX) / self.zoom + self.cx, (sy - CY) / self.zoom + self.cy

    def s(self, size):
        """A world size in screen pixels."""
        return size * self.zoom

    def pts(self, P):
        """(N, 2) world points -> screen points."""
        return (np.asarray(P, dtype=np.float64) - (self.cx, self.cy)) * self.zoom + (CX, CY)

    def view(self, margin: float = 0.0):
        """The world rectangle on screen (l, t, r, b), grown by `margin` screen px."""
        hw, hh = (CX + margin) / self.zoom, (CY + margin) / self.zoom
        return self.cx - hw, self.cy - hh, self.cx + hw, self.cy + hh

    def depth(self, d: float) -> "Cam":
        """The camera for a layer of parallax factor d: its pan is scaled by d and its zoom is
        zoom ** d (d = 1 the subject's plane, 0.5 far, 0 fixed to the screen, above 1 foreground)."""
        return Cam(CX + (self.cx - CX) * d, CY + (self.cy - CY) * d, self.zoom ** d)

    @staticmethod
    def lerp(a: "Cam", b: "Cam", w: float) -> "Cam":
        """The camera between a and b: the zoom is interpolated geometrically, and the world point
        that both views show at the same screen place stays there (a pure dolly; a pan if zooms are equal)."""
        w = min(1.0, max(0.0, float(w)))
        if abs(a.zoom - b.zoom) < 1e-9 * a.zoom:
            return Cam(a.cx + (b.cx - a.cx) * w, a.cy + (b.cy - a.cy) * w, a.zoom)
        z = a.zoom * (b.zoom / a.zoom) ** w
        fx = (a.cx * a.zoom - b.cx * b.zoom) / (a.zoom - b.zoom)
        fy = (a.cy * a.zoom - b.cy * b.zoom) / (a.zoom - b.zoom)
        return Cam(fx - (fx - a.cx) * a.zoom / z, fy - (fy - a.cy) * a.zoom / z, z)

    @staticmethod
    def ease(a: "Cam", b: "Cam", w: float) -> "Cam":
        """lerp with a soft start and a soft stop."""
        return Cam.lerp(a, b, ease(w))


# --------------------------------------------------------------------------
# the frame
# --------------------------------------------------------------------------
_PAINTS: dict = {}
_SPARE: list = []                 # offscreen surfaces for Frame.sub and the bloom, reused across frames


def _paint(grain, stroke: bool) -> skia.Paint:
    # skia-python clones a shader (serialising its image) on every setShader, so the textured paints
    # are made once per (grain, style) and only recoloured afterwards. One seating for the whole film.
    key = (grain, stroke)
    p = _PAINTS.get(key)
    if p is None:
        p = skia.Paint(AntiAlias=True)
        if grain:
            p.setShader(tooth_images()[grain].makeShader(REPEAT, REPEAT, NEAREST))
        if stroke:
            p.setStyle(skia.Paint.kStroke_Style)
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
        _PAINTS[key] = p
    return p


def _spare(i: int) -> skia.Surface:
    while len(_SPARE) <= i:
        _SPARE.append(skia.Surface(W, H))
    return _SPARE[i]


class Post:
    """The finish of a frame. Set from a scene as F.post.<name> = value."""
    __slots__ = ("bloom", "grain", "shimmer", "vignette", "fade", "fade_col")

    def __init__(self, skin: str = "night"):
        day = skin == "day"
        self.bloom = 0.0 if day else 0.42      # additive glow of what is brighter than the paper
        self.grain = 1.0                       # seated grain (does not move): part of the paper
        self.shimmer = 0.0                     # grain that moves on twos (keep it under about 0.25: subtle)
        self.vignette = 0.08 if day else 0.12  # darkening toward the corners
        self.fade = 0.0                        # 0..1 toward fade_col (exposure, fades)
        self.fade_col = C.PAPER_DEEP


class Frame:
    """One picture. A scene draws with F: F.c (canvas), F.t (true time), F.k (boil index, on twos),
    F.cam (the camera every drawing function maps through), F.skin ('night' | 'day'), F.tl (the
    Timeline) and its helpers, F.post (the finish)."""

    def __init__(self, t: float = 0.0, skin: str = "night", tl=None, cam: Cam | None = None, surface=None):
        if tl is None:
            from ..timeline import get_timeline
            tl = get_timeline()
        self.tl = tl
        self.t = float(t)
        self.tq = (math.floor(self.t * BOIL + 1e-6) + 0.5) / BOIL     # true time of the pair of frames (stepped on twos)
        self.k = self.boil_index(self.t)               # boil index: stands still in the two silences
        self.tb = (self.k + 0.5) / BOIL                 # the boil clock, stepped on twos: rain, churn, sways run on it
        self.w, self.h = W, H
        self.surf = surface if surface is not None else skia.Surface(W, H)
        self.c = self.surf.getCanvas()
        self.cam = cam or Cam()
        self.overlays: list = []
        self._subs = [0]
        self.set_skin(skin)

    @staticmethod
    def boil_index(t: float) -> int:
        """The boil index (F.k) of time t."""
        return int(math.floor(boil_clock(float(t)) * BOIL + 1e-6))

    # ---- skin, paper, offscreen frames -------------------------------------------
    def set_skin(self, skin: str) -> None:
        """Start the picture over on the paper of `skin` (night: dark sugar paper, day: warm paper)."""
        self.skin = skin
        self.post = Post(skin)
        c = self.c
        c.restoreToCount(1)
        c.resetMatrix()
        if skin == "day":
            from .day import paper_day
            c.drawImage(paper_day(), 0, 0)
        else:
            c.drawImage(paper_night(), 0, 0)

    @property
    def day(self) -> bool:
        return self.skin == "day"

    def pick(self, night, day):
        """`night` or `day`, whichever skin this frame has."""
        return day if self.skin == "day" else night

    def sub(self, skin: str | None = None) -> "Frame":
        """An offscreen Frame of the same time, camera and timeline on its own paper (for compositing)."""
        G = Frame.__new__(Frame)
        G.__dict__.update(self.__dict__)
        self._subs[0] += 1
        G.surf = _spare(self._subs[0] - 1)
        G.c = G.surf.getCanvas()
        G.cam = Cam(self.cam.cx, self.cam.cy, self.cam.zoom)
        G.set_skin(skin or self.skin)
        return G

    def image(self) -> skia.Image:
        return self.surf.makeImageSnapshot()

    # ---- camera ----------------------------------------------------------------
    @contextmanager
    def depth(self, d: float):
        """with F.depth(0.5): ... draws a far layer (see Cam.depth)."""
        old = self.cam
        self.cam = old.depth(d)
        try:
            yield self.cam
        finally:
            self.cam = old

    @contextmanager
    def screen(self):
        """with F.screen(): ... coordinates are screen pixels (rain in front, light leaks, frame-wide washes)."""
        old = self.cam
        self.cam = Cam()
        try:
            yield self.cam
        finally:
            self.cam = old

    @contextmanager
    def place(self, dx: float = 0.0, dy: float = 0.0, scale: float = 1.0):
        """with F.place(dx, dy, scale): ... what is drawn inside sits at local * scale + (dx, dy) in the
        world (any piece of the kit, at any size, anywhere; coordinates returned inside are local)."""
        old = self.cam
        self.cam = Cam((old.cx - dx) / scale, (old.cy - dy) / scale, old.zoom * scale)
        try:
            yield self.cam
        finally:
            self.cam = old

    def lw(self, w: float, a: float = 1.0, floor: float = LINE_FLOOR):
        """World line width -> (screen width, alpha): under the floor the width holds and the pressure drops."""
        ws = w * self.cam.zoom
        return (ws, a) if ws >= floor else (floor, a * ws / floor)

    def path(self, P, close: bool = False) -> skia.Path:
        """skia path through WORLD points."""
        return path_of(self.cam.pts(P), close)

    @contextmanager
    def clip(self, poly=None, rect=None, out: bool = False):
        """with F.clip(poly) / F.clip(rect=(l, t, r, b)): ... world shapes; out=True draws outside it."""
        c = self.c
        c.save()
        op = skia.ClipOp.kDifference if out else skia.ClipOp.kIntersect
        if rect is not None:
            l, t = self.cam.to_screen(rect[0], rect[1])
            r, b = self.cam.to_screen(rect[2], rect[3])
            c.clipRect(skia.Rect.MakeLTRB(l, t, r, b), op, True)
        else:
            c.clipPath(self.path(poly, True), op, True)
        try:
            yield
        finally:
            c.restore()

    # ---- paints (shared objects: use at once, do not keep) -------------------------
    def paint(self, col, a: float = 1.0, grain: str | None = "dense", blend=None) -> skia.Paint:
        p = _paint(grain, False)
        p.setColor(sk(col, a))
        p.setBlendMode(blend if blend is not None else skia.BlendMode.kSrcOver)
        return p

    def pen(self, col, w: float, a: float = 1.0, grain: str | None = "mid") -> skia.Paint:
        """A stroking paint; w is in SCREEN px (map with F.lw)."""
        p = _paint(grain, True)
        p.setColor(sk(col, a))
        p.setStrokeWidth(float(w))
        return p

    # ---- the song's clock ----------------------------------------------------------
    @property
    def sec(self):
        return self.tl.section_at(min(self.t, self.tl.duration))

    @property
    def beat(self) -> int:
        return self.tl.beat_at(self.t)[0]

    @property
    def beat_frac(self) -> float:
        return self.tl.beat_at(self.t)[1]

    @property
    def bar(self) -> int:
        return self.tl.bar_at(self.t)[0]

    @property
    def bar_beat(self) -> int:
        return self.tl.bar_at(self.t)[1]

    @property
    def bar_frac(self) -> float:
        return self.tl.bar_at(self.t)[2]

    @property
    def u(self) -> float:
        """Position through the current section, 0..1."""
        return self.sec.u(self.t)

    @property
    def cue(self):
        return self.tl.cue_at(self.t)

    @property
    def lrc(self):
        c = self.tl.cue_at(self.t)
        return c.lrc if c else None

    def curve(self, name: str) -> float:
        """A measured curve of the recording at F.t, 0..1: loud, fast, hit, kick, bright."""
        return self.tl.curve(name, self.t)

    loud = property(lambda self: self.tl.curve("loud", self.t))
    fast = property(lambda self: self.tl.curve("fast", self.t))
    hit = property(lambda self: self.tl.curve("hit", self.t))
    kick = property(lambda self: self.tl.curve("kick", self.t))
    hope = property(lambda self: self.tl.hope(self.t))

    def since(self, lrc: int) -> float:
        """Seconds since LRC line `lrc` began (negative before it)."""
        return self.t - self.tl.cue(lrc).t

    def ramp(self, t0: float, t1: float) -> float:
        """Smooth 0..1 between two times of the song."""
        return ramp(self.t, t0, t1)

    def seg(self, t0: float, t1: float) -> float:
        """Linear 0..1 between two times of the song."""
        return seg(self.t, t0, t1)

    def line_ramp(self, lrc: int, lead: float = 0.0, dur: float = 1.0) -> float:
        """Smooth 0..1 starting `lead` seconds before line `lrc` and lasting `dur`."""
        t0 = self.tl.cue(lrc).t - lead
        return ramp(self.t, t0, t0 + dur)

    def pulse(self, tau: float = 0.22, every: int = 1) -> float:
        """Beat pulse: 1 on the beat (every `every` beats), decaying with time constant tau seconds."""
        k, f = self.tl.beat_at(self.t)
        if k < 0:
            return 0.0
        return math.exp(-((k % every) + f) * self.tl.beat_s / tau)

    def bar_pulse(self, tau: float = 0.5) -> float:
        b0 = float(self.tl.bars[self.bar])
        return math.exp(-(self.t - b0) / tau) if self.t >= b0 else 0.0

    # ---- finishing ---------------------------------------------------------------
    def overlay(self, fn) -> None:
        """Ask for fn(canvas) on the finished frame (after bloom and grain), in screen px. Use sparingly."""
        self.overlays.append(fn)

    def apply_bloom(self, amount: float) -> None:
        """One quarter-size blurred additive pass of what is clearly brighter than the paper."""
        if amount <= 0.0:
            return
        sw, sh = W // 4, H // 4
        if "bloom" not in _CACHE:
            _CACHE["bloom"] = (skia.Surface(sw, sh), skia.Surface(sw, sh))
        small, small2 = _CACHE["bloom"]
        sc = small.getCanvas()
        sc.clear(0xFF000000)
        sc.drawImageRect(self.surf.makeImageSnapshot(), skia.Rect.MakeWH(sw, sh), LINEAR)
        p = skia.Paint()
        p.setImageFilter(skia.ImageFilters.Blur(5.5, 5.5))
        k, off = 1.3, -0.46
        p.setColorFilter(skia.ColorFilters.Matrix([k, 0, 0, 0, off, 0, k, 0, 0, off, 0, 0, k, 0, off, 0, 0, 0, 1, 0]))
        small2.getCanvas().clear(0xFF000000)
        small2.getCanvas().drawImage(small.makeImageSnapshot(), 0, 0, LINEAR, p)
        q = skia.Paint()
        q.setBlendMode(PLUS)
        q.setAlphaf(min(1.0, amount))
        self.c.drawImageRect(small2.makeImageSnapshot(), skia.Rect.MakeWH(W, H), LINEAR, q)

    def finish(self) -> np.ndarray:
        """Bloom, vignette, fade, grain; returns RGBA uint8 (H, W, 4)."""
        c, post = self.c, self.post
        c.restoreToCount(1)
        c.resetMatrix()
        self.apply_bloom(post.bloom)
        if post.vignette > 0.0:
            q = skia.Paint()
            q.setAlphaf(min(1.0, post.vignette))
            c.drawImageRect(_vignette_image(), skia.Rect.MakeWH(W, H), LINEAR, q)
        if post.fade > 0.0:
            c.drawColor(sk(post.fade_col, min(1.0, post.fade)))
        # grain: a seated layer (part of the paper) and a faint one that moves on twos. Tiled images,
        # not a shader: skia-python serialises the image on every setShader.
        img = _grain_image()
        for amount, seat in ((post.grain, 0), (post.shimmer, 1 + self.k % 61)):
            if amount > 0.0:
                q = skia.Paint()
                q.setAlphaf(min(1.0, amount))
                ox, oy = int(rnd(seat, 7) * 512), int(rnd(seat, 8) * 512)
                for y in range(-oy, H, 512):
                    for x in range(-ox, W, 512):
                        c.drawImage(img, x, y, NEAREST, q)
        return self.surf.toarray(colorType=skia.kRGBA_8888_ColorType)

    def save(self, path: str) -> np.ndarray:
        from PIL import Image
        arr = self.finish()
        Image.fromarray(arr[..., :3]).save(path)
        return arr


# --------------------------------------------------------------------------
# strokes and tones (WORLD coordinates and sizes; mapped through F.cam)
# --------------------------------------------------------------------------
def _off(S, m: float) -> bool:
    """Are these screen points wholly outside the frame (by more than m px)?"""
    lo, hi = S.min(0), S.max(0)
    return hi[0] < -m or lo[0] > W + m or hi[1] < -m or lo[1] > H + m


def chalk(F: Frame, P, col, w: float, a: float = 1.0, seed: int = 0, wob: float = 1.0, taper: float = 0.5,
          draw=1.0, grain: str = "dense", edge: float = 0.34, under=None, step: float = 6.0, var: float = 0.2,
          boil: float = 1.0, floor: float = LINE_FLOOR, lead: float = 0.0, baked: bool = False):
    """A hand-drawn chalk/crayon stroke along the world polyline P, w world units wide.

    draw: fraction (or (f0, f1) pair) of the stroke that exists yet (things draw themselves on).
    under: a colour rubbed out behind the stroke first (keeps a figure readable over a busy set).
    edge: alpha of the wider dusty pass (0 = a clean crayon line). wob: hand wobble (0 = none).
    boil: 0 = seated (does not boil). floor: the least screen width; thinner lines fade instead.
    lead: world length behind the far end where the pressure is still building (a stroke being drawn).
    Returns the world point where the drawn part ends (the chalk tip), or None if nothing was drawn.
    """
    f0, f1 = (0.0, float(draw)) if not isinstance(draw, tuple) else draw
    if f1 - f0 <= 0.002 or a <= 0.003:
        return None
    cam = F.cam
    z = cam.zoom
    Q, s = hand(P, seed, F.k, wob, step, boil, z, baked)
    if f0 > 0.0 or f1 < 1.0:
        Q, s = trim(Q, s, f0, f1)
        if Q is None:
            return None
    S = cam.pts(Q)
    ws = w * z
    if _off(S, ws * 2.0 + 8.0):
        return Q[-1]
    k = 1.0
    if ws < floor:
        k = ws / floor
        a, ws = a * k, floor
    thin = min(1.0, max(0.0, 2.6 - ws))                # a hairline keeps an even width
    if thin > 0.0:
        taper, var = taper + (max(taper, 0.9) - taper) * thin, var * (1.0 - 0.7 * thin)
    ss, c = s * z, F.c
    if under is not None:
        c.drawPath(ribbon(S, ss, ws * 2.0 + 2.5 * k, seed + 5, 0.8, 0.0, s), F.paint(under, 0.85 * (0.4 + 0.6 * k), None))
    if edge > 0.0:
        c.drawPath(ribbon(S, ss, ws * 1.75 + 0.8, seed + 7, taper, var * 1.5, s, lead * z), F.paint(col, a * edge, "sparse"))
    c.drawPath(ribbon(S, ss, ws, seed, taper, var, s, lead * z), F.paint(col, a, grain))
    return Q[-1]


def scrib(F: Frame, P, col, w: float, a: float = 1.0, grain: str = "mid", close: bool = False, floor: float = 1.2):
    """A constant-width pass for dense scribbles and zigzags (many world points, one path; no wobble)."""
    if a <= 0.003 or len(P) < 2:
        return
    S = F.cam.pts(P)
    ws, a = F.lw(w, a, floor)
    if not _off(S, ws):
        F.c.drawPath(path_of(S, close), F.pen(col, ws, a, grain))


def fill(F: Frame, P, col, a: float = 1.0, grain: str | None = None, blend=None):
    """A flat (or toothed) polygon: rub-outs, bases, small solid shapes. P is a closed world outline."""
    if a > 0.003:
        F.c.drawPath(F.path(P, True), F.paint(col, a, grain, blend))


def disc(F: Frame, x, y, r, col, a: float = 1.0, grain: str | None = None, floor: float = 0.0):
    """A dot of world radius r (floor: least screen radius; smaller dots fade instead)."""
    sx, sy = F.cam.to_screen(x, y)
    rs = r * F.cam.zoom
    if 0.0 < rs < floor:
        a, rs = a * (rs / floor) ** 2, floor
    if a > 0.003:
        F.c.drawCircle(float(sx), float(sy), float(rs), F.paint(col, a, grain))


def loop(F: Frame, P, col, w, a=1.0, seed=0, wob=1.0, fill_col=None, fill_a=0.9, fill_grain=None, **kw):
    """A closed hand-drawn outline; optionally rubbed out / filled inside first.
    The stroke overshoots its start a little, as a child closes a shape."""
    P = np.asarray(P, dtype=np.float64)
    if fill_col is not None:
        fill(F, P, fill_col, fill_a, fill_grain)
    n = max(2, len(P) // 14)
    return chalk(F, np.vstack([P, P[1:n + 1]]), col, w, a, seed, wob, **kw)


def hatch(F: Frame, poly, col, ang: float, gap: float, w: float, a: float = 1.0, seed: int = 0,
          grain: str = "sparse", wob: float = 0.6, draw=1.0, clip: bool = False, over: float = 0.5,
          boil=None, jit: float = 0.35):
    """Colour a world shape in with a zigzag (scan lines at `ang`, `gap` apart, `w` wide).

    draw < 1 (or a pair): the colouring is still under way. clip: keep it inside the outline.
    boil: None = only if the shape is smaller than a prop on screen (SEAT_AREA); False = seated.
    When the zigzag would close up on screen (far away) it turns into rubbed tone of the same weight.
    """
    if a <= 0.003:
        return
    f0, f1 = (0.0, float(draw)) if not isinstance(draw, tuple) else draw
    if f1 - f0 <= 0.0:
        return
    cam = F.cam
    z = cam.zoom
    poly = np.asarray(poly, dtype=np.float64)
    tone = 1.0 - ramp(gap * z, 1.6, 3.0)
    if tone > 0.0:
        fill(F, poly, col, a * min(1.0, w / gap) * tone * (f1 - f0), grain)
        if tone >= 1.0:
            return
    Z = zigzag(poly, ang + 0.05 * rsym(seed, 9), gap, seed, jit=jit, over=over)
    if Z is None:
        return
    if boil is None:
        ext = (poly.max(0) - poly.min(0)) * z
        boil = ext[0] * ext[1] < SEAT_AREA
    Q, s = hand(Z, seed + 17, F.k, wob, max(5.0, gap * 1.2), 0.6 if boil else 0.0, z)
    if f0 > 0.0 or f1 < 1.0:
        Q, s = trim(Q, s, f0, f1)
        if Q is None:
            return
    S = cam.pts(Q)
    ws, a = F.lw(w, a * (1.0 - tone), 1.0)
    if _off(S, ws):
        return
    c = F.c
    if clip:
        c.save()
        c.clipPath(F.path(poly, True), skia.ClipOp.kIntersect, True)
    c.drawPath(path_of(S), F.pen(col, ws, a, grain))
    if clip:
        c.restore()


_RINGS, _SEGS = 9, 36
_MESH: dict = {}


def _mesh(power: float, inner: float):
    """Unit disc mesh for a soft patch: ring radii, ring alphas, unit directions, triangle indices."""
    key = (round(power, 2), round(inner, 2))
    if key not in _MESH:
        rr = np.linspace(0.0, 1.0, _RINGS + 1) ** 0.85
        al = np.where(rr > inner, (1.0 - np.clip((rr - inner) / max(1e-6, 1.0 - inner), 0, 1)) ** power, 1.0)
        an = np.linspace(0.0, 2.0 * math.pi, _SEGS, endpoint=False)
        idx = []
        for i in range(_RINGS):
            for j in range(_SEGS):
                a0, a1 = i * _SEGS + j, i * _SEGS + (j + 1) % _SEGS
                idx += [a0, a0 + _SEGS, a1, a1, a0 + _SEGS, a1 + _SEGS]
        _MESH[key] = (np.outer(rr, np.cos(an)).ravel(), np.outer(rr, np.sin(an)).ravel(), np.repeat(al, _SEGS), idx)
    return _MESH[key]


def _shade(F: Frame, X, Y, al, idx, col, a, grain, additive):
    """Triangles whose vertex alphas shape a tone of colour col seen through the (screen-fixed) grain."""
    pts = [skia.Point(x, y) for x, y in zip(X.tolist(), Y.tolist())]
    if grain:
        cols = [(int(v) << 24) | 0xFFFFFF for v in np.clip(al * 255.0 + 0.5, 0, 255).tolist()]
        p = F.paint(col, a, grain, PLUS if additive else None)
    else:
        rgb = sk(col, 0.0)
        cols = [(int(v) << 24) | rgb for v in np.clip(al * (a * 255.0) + 0.5, 0, 255).tolist()]
        p = F.paint((1.0, 1.0, 1.0), 1.0, None, PLUS if additive else None)
    F.c.drawVertices(skia.Vertices.MakeCopy(skia.Vertices.kTriangles_VertexMode, pts, None, cols, idx), p, skia.BlendMode.kSrcIn)


def smudge(F: Frame, cx, cy, rx, ry, col, a: float = 0.5, grain: str | None = "soft", power: float = 1.6,
           rot: float = 0.0, additive: bool = False, inner: float = 0.0):
    """Rubbed pastel: an elliptical soft patch through the tooth (world centre and radii).
    power: falloff (higher = tighter core); inner: 0..1 solid core; additive: light, not pigment."""
    z = F.cam.zoom
    sx, sy = F.cam.to_screen(cx, cy)
    rx, ry = rx * z, ry * z
    m = max(rx, ry)
    if a <= 0.003 or rx <= 0.5 or ry <= 0.5 or sx < -m or sx > W + m or sy < -m or sy > H + m:
        return
    ux, uy, al, idx = _mesh(power, inner)
    X, Y = ux * rx, uy * ry
    if rot:
        cr, sr = math.cos(rot), math.sin(rot)
        X, Y = X * cr - Y * sr, X * sr + Y * cr
    # a round patch is dabbed (blotches), a wide flat one is wiped sideways (smears); in between, both
    k = ramp(rx / ry, 2.0, 2.6) if grain in RUBBED and not rot else 0.0
    if k < 1.0:
        _shade(F, sx + X, sy + Y, al, idx, col, a * (1.0 - k), grain, additive)
    if k > 0.0:
        _shade(F, sx + X, sy + Y, al, idx, col, a * k, grain + WIDE, additive)


def wash(F: Frame, poly, col, y0: float, y1: float, alphas, grain: str | None = "soft", additive: bool = False):
    """A world polygon of rubbed pastel whose strength runs through `alphas` from world y0 down to y1
    (a light beam, a pool of light on the floor)."""
    n = (len(alphas) - 1) * 4 + 1
    al = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(alphas)), np.asarray(alphas, dtype=np.float64))
    if al.max() <= 0.003:
        return
    S = F.cam.pts(poly)
    if _off(S, 0.0):
        return
    ys = np.linspace(F.cam.to_screen(0.0, y0)[1], F.cam.to_screen(0.0, y1)[1], n)
    xl, xr = float(S[:, 0].min()) - 2.0, float(S[:, 0].max()) + 2.0
    idx = []
    for i in range(n - 1):
        idx += [2 * i, 2 * i + 2, 2 * i + 1, 2 * i + 1, 2 * i + 2, 2 * i + 3]
    c = F.c
    c.save()
    c.clipPath(path_of(S, True), skia.ClipOp.kIntersect, True)
    _shade(F, np.tile([xl, xr], n), np.repeat(ys, 2), np.repeat(al, 2), idx, col, 1.0,
           grain + WIDE if grain in RUBBED else grain, additive)
    c.restore()


def specks(F: Frame, xs, ys, r, col, a=1.0, grain="dense"):
    """Chalk dust: many small dots in one path (world positions, world radii)."""
    z = F.cam.zoom
    S = F.cam.pts(np.stack([np.asarray(xs, dtype=np.float64), np.asarray(ys, dtype=np.float64)], axis=1))
    rr = np.broadcast_to(np.asarray(r, dtype=np.float64) * z, (len(S),))
    a = a * min(1.0, float(rr.mean()) / 0.8) ** 2
    if a <= 0.003:
        return
    p = skia.Path()
    for (x, y), q in zip(S.tolist(), np.maximum(rr, 0.8).tolist()):
        p.addCircle(x, y, q)
    F.c.drawPath(p, F.paint(col, a, grain))


def dashes(F: Frame, x0, y0, x1, y1, w, col, a=1.0, grain="mid", floor: float = 1.3):
    """Many short straight strokes in one path (rain, grass ticks, rays): world end points."""
    cam = F.cam
    ws, a = F.lw(w, a, floor)
    if a <= 0.003:
        return
    ax, ay = cam.to_screen(np.asarray(x0, dtype=np.float64), np.asarray(y0, dtype=np.float64))
    bx, by = cam.to_screen(np.asarray(x1, dtype=np.float64), np.asarray(y1, dtype=np.float64))
    p = skia.Path()
    for a_, b_, c_, d_ in zip(ax.tolist(), ay.tolist(), bx.tolist(), by.tolist()):
        p.moveTo(a_, b_)
        p.lineTo(c_, d_)
    F.c.drawPath(p, F.pen(col, ws, a, grain))
