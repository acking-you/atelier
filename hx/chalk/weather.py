"""hx.chalk.weather: weather and light.

Light in this film is rubbed pastel through the paper's tooth: pools, shafts and glows, with one soft
bloom from the finish. It turns line drawings into pictures and it carries the story: cold moonlight,
the friend's amber, the pale light through the parted scribble, and at last the warm sheet under the
dark one. Read hx/chalk/doc/weather.md.

  rain        rain, rainfall (depth layers, splashes, lens rain), splashes, rain_window, rain_amount, rain_lean
  mist        mist (the band at the horizon, in slabs), mist_keep
  the room    window_pool (night / evening / sunset), moon_pool, window_glow, lamp_light
  shafts      shaft, shafts, light_pool, dust, shaft_dust, gap_light
  amber       glow, amber_glow, amber_point, wet_reflection, amber_line, amber_run, amber_window, rim
  the tear    rip_outline, tear, tear_shafts, scraps, flash, decay
  shadows     ground_shadow, long_shadow

Everything takes WORLD coordinates and maps through F.cam. Everything is a pure function of the
frame: what is merely alive (rain, mist, shimmer) runs on the boil clock F.tb and stands still in the
two silences; what acts (the amber pulse, the tear, the scraps) is driven by arguments the scene
computes from F.t. No lyric text anywhere.
"""
from __future__ import annotations

import math

import numpy as np
import skia

from ..story import BAND_SLAM, FLOOR
from .core import (A, BOIL, C, H, HOLDS, RUBBED, TAB, W, WIDE, Frame, _off, _shade, chalk, dashes, disc, ease, ease_out, fill,
                   hatch, htab, mix, ramp, rnd, rsym, seg, smooth, smudge, specks, spline, vn)
from .core import _mesh as _disc          # the unit disc of a soft patch (power, inner) -> ux, uy, alphas, indices
from .ground import ground_line

__all__ = ["PALE", "WARM", "light_col",
           "rain", "rainfall", "splashes", "rain_window", "rain_amount", "rain_lean",
           "mist", "mist_keep",
           "window_pool", "moon_pool", "window_glow", "lamp_light",
           "shaft", "shafts", "light_pool", "dust", "shaft_dust", "gap_light",
           "glow", "amber_glow", "amber_point", "wet_reflection", "amber_line", "amber_run", "amber_window", "rim",
           "rip_outline", "tear", "tear_shafts", "scraps", "flash", "decay",
           "ground_shadow", "long_shadow"]

PALE = mix(C.CHALK, C.MOON, 0.30)        # the pale light through the parted scribble: cold, before the sheet rips
WARM = (0.93, 0.87, 0.71)                # the light of the warm sheet, from the rip on
SHADE_NIGHT = mix(C.PAPER_DEEP, C.GLOOM, 0.45)     # a rubbed night shadow: deep blue, never the scribble's black
HAZE = (0.33, 0.40, 0.60)                # mist: chalk dust rubbed into the dark paper with the side of the hand


def light_col(F: Frame):
    """The colour of plain light at this moment of the film: pale cold chalk before the sheet rips
    (201.25 s), the pale warm of the under sheet after it, cream on the day paper."""
    if F.day:
        return C.SUN_CORE
    return WARM if F.t >= BAND_SLAM else PALE


def decay(since: float, tau: float = 0.3) -> float:
    """0 before an event, 1 on it, then falling with time constant tau seconds (a flash, a ring)."""
    return math.exp(-since / tau) if since >= 0.0 else 0.0


def _h(i, mul: int, add):
    """Hash 0..1 per index with a per-element offset (htab takes only a scalar one)."""
    return TAB[(np.asarray(i, dtype=np.int64) * int(mul) + np.asarray(add, dtype=np.int64)) & 8191]


def _steps(t: float) -> float:
    """A clock stepped on twos (rain and splashes move with the boil, whatever clock they are given)."""
    return math.floor(t * BOIL + 1e-6) / BOIL


def _held_tq(F: Frame) -> float:
    """The song time the boil clock is at: F.tq, standing still in the two silences."""
    for a_, b_ in HOLDS:
        if a_ <= F.t < b_:
            return (math.floor(a_ * BOIL + 1e-6) - 0.5) / BOIL
    return F.tq


_IDX: dict = {}


def _grid_idx(n: int, m: int):
    """Triangle indices of an n x m vertex grid (row-major)."""
    key = (n, m)
    if key not in _IDX:
        idx = []
        for i in range(n - 1):
            for j in range(m - 1):
                a0 = i * m + j
                idx += [a0, a0 + m, a0 + 1, a0 + 1, a0 + m, a0 + m + 1]
        _IDX[key] = idx
    return _IDX[key]


_EDGE_U = np.array([0.0, 0.45, 1.0])               # across a soft edge: where ...
_EDGE_A = np.array([0.0, 0.26, 1.0])               # ... and how strong (a slow start: no hard rim)


def _strip(F: Frame, Lp, Rp, al, col, a: float, grain: str = "glow", additive: bool = True, edge=0.25, wide: bool = False):
    """A rubbed band between two world polylines Lp and Rp (n, 2), its strength `al` (n) along it,
    falling to nothing over the fraction `edge` (a number or (n,)) at both sides."""
    al = np.asarray(al, dtype=np.float64)
    if a <= 0.003 or al.max() <= 0.003:
        return
    Ls, Rs = F.cam.pts(Lp), F.cam.pts(Rp)
    if _off(np.vstack([Ls, Rs]), 0.0):
        return
    n = len(Ls)
    e = np.broadcast_to(np.asarray(edge, dtype=np.float64), (n,))[:, None]
    u = np.concatenate([e * _EDGE_U[None, :], 1.0 - e * _EDGE_U[None, ::-1]], axis=1)          # (n, 6)
    pa = np.concatenate([_EDGE_A, _EDGE_A[::-1]])
    X = Ls[:, :1] + (Rs[:, :1] - Ls[:, :1]) * u
    Y = Ls[:, 1:] + (Rs[:, 1:] - Ls[:, 1:]) * u
    g = grain + WIDE if (wide and grain in RUBBED) else grain
    _shade(F, X.ravel(), Y.ravel(), (al[:, None] * pa[None, :]).ravel(), _grid_idx(n, 6), col, a, g, additive)


def _mesh(F: Frame, X, Y, AL, col, a: float, grain: str = "glow", additive: bool = True, wide: bool = False):
    """A rubbed tone on a grid of WORLD vertices X, Y (n, m) with vertex strengths AL (n, m)."""
    if a <= 0.003 or AL.max() <= 0.003:
        return
    S = F.cam.pts(np.stack([X.ravel(), Y.ravel()], axis=1))
    if _off(S, 0.0):
        return
    g = grain + WIDE if (wide and grain in RUBBED) else grain
    _shade(F, S[:, 0], S[:, 1], AL.ravel(), _grid_idx(*X.shape), col, a, g, additive)


# --------------------------------------------------------------------------------------------------
# rain
# --------------------------------------------------------------------------------------------------
def _streaks(F: Frame, ax, ay, bx, by, w: float, col, a: float, bead=None):
    """Rain drops as chalk strokes, SCREEN px: a faint tail from (ax, ay), pressed harder toward the
    head (bx, by), and on the drops in the mask `bead` a round bead at the head. w: world width."""
    if len(ax) == 0:
        return
    ws, al = F.lw(w, a, 1.3)
    if al <= 0.004:
        return
    mx, my = ax + (bx - ax) * 0.42, ay + (by - ay) * 0.42
    p, q = skia.Path(), skia.Path()
    for x0, y0, xm, ym, x1, y1 in zip(ax.tolist(), ay.tolist(), mx.tolist(), my.tolist(), bx.tolist(), by.tolist()):
        p.moveTo(x0, y0)
        p.lineTo(xm, ym)
        q.moveTo(xm, ym)
        q.lineTo(x1, y1)
    c = F.c
    c.drawPath(p, F.pen(col, ws * 0.8, al * 0.42, "sparse"))
    c.drawPath(q, F.pen(col, ws, al, "mid"))
    if bead is not None and bead.any():
        d = skia.Path()
        rr = max(1.1, ws * 0.95)
        for x1, y1 in zip(bx[bead].tolist(), by[bead].tolist()):
            d.addCircle(x1, y1, rr)
        c.drawPath(d, F.paint(mix(col, C.CHALK, 0.4), min(1.0, al * 1.25), "dense"))


def rain(F: Frame, l, t_, r, b, n=140, slant=0.20, ln=30.0, col=C.CHALK_BLUE, a=0.5, w=2.0, speed=1100.0,
         seed=0, t=None, lean=0.0, bead=0.6):
    """Chalk rain inside the world rectangle (l, t_, r, b): n drops, each a short stroke about ln long
    and w wide with a bead at its head, falling `speed` units a second along tracks that slant by
    `slant` (dx per dy). lean: extra slant of the strokes alone (a gust; see rain_lean). bead: share of
    the drops that carry a bead. t: its clock (default F.tb: the rain hangs still in the two silences);
    whatever the clock, it steps on twos. Inside `with F.screen():` the rectangle is in screen px."""
    n = int(n)
    if n <= 0 or a <= 0.004:
        return
    tq = _steps(F.tb if t is None else t)
    i = np.arange(n)
    hh = b - t_
    sp = 0.75 + 0.5 * htab(i, 13, seed * 139 + 9)
    li = ln * sp
    u = htab(i, 11, seed * 137 + 5) + tq * speed * sp / hh
    cyc = np.floor(u)
    y = t_ + (u - cyc) * (hh + li)                                    # the head
    x = l - slant * hh + _h(i, 7, seed * 131 + cyc * 977) * (r - l + slant * hh) + slant * (y - t_)
    sl = slant + lean + 0.03 * (2.0 * htab(i, 17, seed * 151 + 1) - 1.0)
    cam = F.cam
    bx, by = cam.to_screen(x, y)
    ax, ay = cam.to_screen(x - sl * li, y - li)
    with F.clip(rect=(l, t_, r, b)):
        _streaks(F, ax, ay, bx, by, w, col, a, htab(i, 19, seed * 157 + 3) < bead if bead > 0 else None)


def _rain_world(F: Frame, n, ln, w, a, speed, slant, lean, seed, tq, col, land_sy, land_px, bead, gust=0.0, quick=0.0):
    """One layer of world rain in the current camera (call it inside F.depth): drops anchored in the
    world, so the layer pans and scales with its camera; its detail goes by octaves of zoom, so on
    screen a drop is always about ln px long. Drops end on the screen line land_sy (+ up to land_px).
    quick: the share of the drops that fall a third faster (the storm). A drop's speed is its own
    for good: a speed that changed with time would throw every drop to a new place on every step."""
    cam = F.cam
    z = cam.zoom
    Lz = math.log2(1.0 / max(z, 1e-6))
    o = math.floor(Lz)
    w1 = float(smooth(Lz - o))
    vl, vt = cam.view(8.0)[:2]
    for oc, wt in ((o, 1.0 - w1), (o + 1, w1)):
        if wt < 0.004:
            continue
        s = 2.0 ** oc
        pw, ph = 3840.0 * s, 2160.0 * s                              # the layer repeats beyond the frame, never inside it
        m = int(4 * n * math.sqrt(wt) / (1.0 - 0.5 * gust))
        if m <= 0:
            continue
        i = np.arange(m)
        sd = seed * 131 + oc * 517
        sp = (0.75 + 0.5 * _h(i, 13, sd + 9)) * np.where(_h(i, 31, sd + 11) < quick, 1.3, 1.0)
        li = ln * s * sp
        top = vt - ln * s * 1.4
        u = _h(i, 11, sd + 5) * ph + tq * speed * s * sp
        ky = np.floor((u - top) / ph)
        wy = u - ky * ph                                             # the head, in [top, top + ph)
        xt = _h(i, 7, sd + ky * 977) * pw + slant * wy               # a track fixed in the world
        wx = vl + np.mod(xt - vl, pw)
        sx, sy = cam.to_screen(wx, wy)
        keep = (sx < W + 40.0) & (sy - li * z < H) & (sy < land_sy + land_px * _h(i, 23, sd + 3 + ky * 31))
        if gust > 0.0:                                               # sheets of thicker rain, driven across
            keep &= _h(i, 29, sd + 7) < 1.0 - gust * (1.0 - _gust(sx - slant * sy, tq, seed))
        if not keep.any():
            continue
        sx, sy, li = sx[keep], sy[keep], li[keep] * z
        sl = slant + lean + 0.03 * (2.0 * _h(i[keep], 17, sd + 1) - 1.0)
        _streaks(F, sx - sl * li, sy - li, sx, sy, w * s, col, a * math.sqrt(wt),
                 _h(i[keep], 19, sd + 2) < bead if bead > 0 else None)


def _gust(sx, tq: float, seed: int):
    """0..1 along the screen: where the sheets of the storm are at this step (they travel with the wind)."""
    return smooth(1.6 * vn((sx - 330.0 * tq) / 430.0 + seed * 3.7, seed + 40) - 0.3)


def rain_lean(F: Frame, k: float = 1.0) -> float:
    """How much further the rain strokes lean with the music's loudness, about -0.12 (quiet: they hang
    straighter) .. +0.08 (loud). Held on twos, and held in the two silences."""
    loud = F.tl.curve("loud", _held_tq(F))
    return k * min(0.08, max(-0.12, 0.9 * (loud - 0.80)))


def rain_amount(t: float) -> float:
    """The storyboard's rain on the plain as one number of the song's time, for rainfall(F, k): 0 dry,
    1 the first chorus, 1.5 the storm of the second. It begins thinly at 54.6, hangs in the silence,
    falls with the band's entry (58.60), thins when the child's head lifts (75.5) and stops in the
    interlude (87); comes back hard at 138.2, thins from 150 and is gone by 160."""
    k = 0.55 * ramp(t, 54.6, 55.9) + 0.45 * ramp(t, 58.6, 59.0) - 0.50 * ramp(t, 75.5, 79.5) - 0.50 * ramp(t, 80.5, 87.0)
    k += 1.5 * ramp(t, 138.2, 138.8) - 1.05 * ramp(t, 150.1, 152.5) - 0.45 * ramp(t, 155.0, 160.0)
    return max(0.0, k)


def rainfall(F: Frame, k: float = 1.0, part: str = "all", ground: float = FLOOR, slant=None, lean=None, seed: int = 9,
             t=None, col=C.CHALK_BLUE, splash: float = 1.0, lens: float = 1.0):
    """The rain of the plain, one intensity k (0 dry .. 1 the first chorus .. 1.5 the storm; see
    rain_amount). Above 1 it does not only thicken: the strokes lengthen, fall faster and slant
    harder, and it comes in gusts: sheets of thicker rain driven across the frame.

    part="back": two far layers (parallax 0.4 and 0.7 through F.depth) that end on the horizon, to be
    drawn BEFORE the figures; part="front": the rain of the figures' own
    plane, its splashes on the ground line, and the big sparse drops close to the lens (fixed to the
    screen), to be drawn AFTER them; "all": both at once. ground: world y of the ground line. slant:
    of the tracks (default 0.20 + 0.08 k up to k = 1, then steeply on to 0.46 at k = 1.5: a storm is
    driven); lean: of the strokes (default rain_lean(F): the music).
    splash, lens: 0..1 scale the splashes and the lens rain. t: the clock (default F.tb). Call it
    with F.cam = the scene's camera (not inside F.screen / F.depth)."""
    k = float(k)
    if k <= 0.012:
        return
    tq = _steps(F.tb if t is None else t)
    over = max(0.0, min(k, 2.0) - 1.0)                       # the storm
    slant = 0.20 + 0.08 * min(k, 1.0) + 0.36 * over if slant is None else slant      # a storm is driven: 0.46 at k = 1.5
    lean = rain_lean(F) if lean is None else lean
    al = min(1.0, 0.35 + 0.65 * k) * ramp(k, 0.0, 0.12)
    # The storm is driven, not only thicker: drop after drop goes over to a third more speed (and a faster
    # drop is a longer stroke), the tracks slant hard, and it comes in gusts. The ink on the sheet grows by
    # about 1.9 from k = 1 to k = 1.5 (count 1.4, length 1.37): more than that reads as noise, not as rain.
    kn = min(k, 1.0) + 0.8 * over
    lg, quick = 1.0 + 0.10 * over, min(1.0, over * 2.0)
    gust = 0.75 * min(1.0, over * 2.0)
    gsy = F.cam.to_screen(0.0, ground)[1]
    if part in ("all", "back"):
        with F.depth(0.4):
            _rain_world(F, 96 * kn, 27.0 * lg, 1.5, 0.32 * al, 520.0, slant, lean, seed + 1, tq, mix(col, C.CHALK_DIM, 0.5),
                        gsy - 3.0, 8.0, 0.0, gust, quick)
        with F.depth(0.7):
            _rain_world(F, 72 * kn, 40.0 * lg, 1.9, 0.42 * al, 760.0, slant, lean, seed + 2, tq, mix(col, C.CHALK_DIM, 0.2),
                        gsy, 14.0, 0.35, gust, quick)
    if part in ("all", "front"):
        _rain_world(F, 48 * kn, 54.0 * lg, 2.3, 0.52 * al, 1000.0, slant, lean, seed + 3, tq, col, gsy + 4.0, 46.0, 0.6, gust, quick)
        if splash > 0.0:
            splashes(F, y=ground, k=kn * splash, seed=seed + 4, t=tq, col=col)
        if lens > 0.0:
            m = int(24 * (min(k, 1.0) + 1.3 * over) * lens)
            i = np.arange(m)
            sp = (0.8 + 0.4 * htab(i, 13, seed * 139 + 60)) * np.where(htab(i, 31, seed * 149 + 64) < quick, 1.3, 1.0)
            li = 84.0 * sp * lg
            hh = H + 120.0 * 1.25                                    # a fixed period (it must not change with k)
            u = htab(i, 11, seed * 137 + 61) + tq * 1500.0 * sp / hh
            cyc = np.floor(u)
            y = (u - cyc) * hh
            x = -slant * hh + _h(i, 7, seed * 131 + 62 + cyc * 977) * (W + slant * hh) + slant * y
            sl = slant + lean
            # close to the lens the drops pass in front of everything; they thin out over the ground and the lyric band
            fade = 1.0 - smooth((y - (gsy + 20.0)) / 260.0)
            for lo, hi, ka in ((0.67, 1.01, 1.0), (0.34, 0.67, 0.6), (0.04, 0.34, 0.28)):
                mk = (fade >= lo) & (fade < hi)
                if mk.any():
                    with F.screen():
                        _streaks(F, x[mk] - sl * li[mk], y[mk] - li[mk], x[mk], y[mk], 3.0, col, 0.50 * al * ka,
                                 htab(i[mk], 19, seed + 63) < 0.75)


def splashes(F: Frame, x0=None, x1=None, y: float = FLOOR, k: float = 1.0, n: float = 40.0, size: float = 13.0,
             spread: float = 34.0, col=C.CHALK_BLUE, a: float = 0.8, seed: int = 0, t=None):
    """Drops landing on the ground line at world y: small crowns (two ticks flying apart, a flat ring
    opening on the wet ground) that live four boil steps. About n * k of them are born a second per
    frame width; they lie up to `spread` px below the line (nearer the viewer: larger). x0, x1: only
    between these world x (default: wherever the camera looks). size: of a crown in screen px (they
    keep their size on screen at any zoom, like the rain). t: the clock (default F.tb)."""
    k = float(k)
    if k <= 0.012 or a <= 0.004:
        return
    tq = _steps(F.tb if t is None else t)
    cam = F.cam
    z = cam.zoom
    Lz = math.log2(1.0 / max(z, 1e-6))
    o = math.floor(Lz)
    w1 = float(smooth(Lz - o))
    vl, _, vr, _ = cam.view(20.0)
    life = 4.0 / BOIL
    sy0 = cam.to_screen(0.0, y)[1]
    c = F.c
    for oc, wt in ((o, 1.0 - w1), (o + 1, w1)):
        if wt < 0.03:
            continue
        s = 2.0 ** oc
        pw = 3840.0 * s
        m = int(2.0 * n * min(k, 2.0) * 0.75 * math.sqrt(wt)) + 1    # over the period; each is alive life / T of the time
        i = np.arange(m)
        sd = seed * 131 + oc * 517
        T = 0.55 + 0.4 * _h(i, 13, sd + 1)
        u = _h(i, 11, sd + 2) + tq / T
        cyc = np.floor(u)
        age = (u - cyc) * T / life
        dep = _h(i, 29, sd + 4 + cyc * 61) ** 1.6
        wx = vl + np.mod(_h(i, 7, sd + 3 + cyc * 977) * pw - vl, pw)
        keep = (age < 1.0) & (wx < vr)
        if x0 is not None:
            keep &= wx >= x0
        if x1 is not None:
            keep &= wx <= x1
        if not keep.any():
            continue
        sx = cam.to_screen(wx[keep], 0.0)[0]
        ag, dp = age[keep], dep[keep]
        sy = sy0 + 2.0 + dp * spread
        sz = size * (0.6 + 0.8 * dp) * (2.0 ** (oc - Lz)) ** 0.5
        hk = _h(i[keep], 17, sd + 5)
        for q in range(4):                                           # one pressure per age: a crown fades as it opens
            mk = (ag >= q / 4.0) & (ag < (q + 1) / 4.0)
            if not mk.any():
                continue
            g = (q + 0.5) / 4.0
            p, rg = skia.Path(), skia.Path()
            for x_, y_, s_, h_ in zip(sx[mk].tolist(), sy[mk].tolist(), sz[mk].tolist(), hk[mk].tolist()):
                dx, up = s_ * (0.35 + 1.0 * g), s_ * (0.5 + 1.1 * g) * (1.0 - 0.55 * g)
                p.moveTo(x_ - dx * 0.35, y_ - up * 0.3)
                p.lineTo(x_ - dx * (0.9 + 0.3 * h_), y_ - up)
                p.moveTo(x_ + dx * 0.35, y_ - up * 0.3)
                p.lineTo(x_ + dx * (1.1 - 0.3 * h_), y_ - up * (0.8 + 0.3 * h_))
                rw = s_ * (0.5 + 1.5 * g)
                rg.addOval(skia.Rect.MakeLTRB(x_ - rw, y_ - rw * 0.22, x_ + rw, y_ + rw * 0.22))
            al = a * math.sqrt(wt) * min(1.0, 0.4 + 0.6 * k) * (1.0 - g) ** 0.7
            c.drawPath(p, F.pen(mix(col, C.CHALK, 0.35), 2.0, al, "mid"))
            c.drawPath(rg, F.pen(col, 1.5, al * 0.75, "mid"))


def rain_window(F: Frame, l, t_, r, b, k: float = 1.0, seed: int = 3, t=None, col=C.CHALK_BLUE, a: float = 1.0):
    """Rain as the room's window shows it: thin slanting rain behind the glass, and on the glass a few
    beads that creep down in fits with a wet trail behind them, and small ones that only sit. Inside
    the world rectangle of the pane (l, t_, r, b). k: 0..1 how hard it rains. t: clock (default F.tb)."""
    k = float(k)
    if k <= 0.012 or a <= 0.004:
        return
    t = F.tb if t is None else t
    wd, hh = r - l, b - t_
    s = wd / 370.0
    with F.clip(rect=(l, t_, r, b)):
        rain(F, l, t_, r, b, n=64 * k, slant=0.24, ln=30 * s, col=col, a=0.50 * a * min(1.0, 0.4 + 0.6 * k), w=1.9 * s,
             speed=640.0 * s, seed=seed, t=t, bead=0.0)
        cam = F.cam
        # beads that sit on the glass
        j = np.arange(int(16 * min(1.0, k * 1.5)))
        if len(j):
            bx = l + 12 * s + htab(j, 7, seed * 31 + 4) * (wd - 24 * s)
            by = t_ + 12 * s + htab(j, 11, seed * 37 + 5) * (hh - 24 * s)
            specks(F, bx, by, (1.3 + 1.3 * htab(j, 13, seed + 6)) * s, C.CHALK_COOL, 0.5 * a, "dense")
        # beads that run: rest, slide, rest (stick and slip), each leaving a trail that wavers
        m = int(round(9 * min(1.0, k * 1.5)))
        i = np.arange(m)
        if m:
            T = 5.0 + 6.0 * htab(i, 23, seed * 41 + 7)
            u = htab(i, 19, seed * 43 + 5) * 3.0 + t / T
            cyc = np.floor(u)
            f = u - cyc
            go = np.floor(f * 3.0) + smooth((f * 3.0 - np.floor(f * 3.0) - 0.45) / 0.55)     # three slides a fall
            gx = l + 18 * s + _h(i, 17, seed * 47 + 3 + cyc * 131) * (wd - 36 * s)
            gy = t_ - 20 * s + go / 3.0 * (hh + 90 * s)
            tr = (40.0 + 80.0 * htab(i, 29, seed + 8)) * s
            q = np.linspace(0.0, 1.0, 7)
            p = skia.Path()
            for x_, y_, L_, j_ in zip(gx.tolist(), gy.tolist(), tr.tolist(), i.tolist()):
                yy = y_ - L_ * (1.0 - q)
                xs = x_ + 3.2 * s * np.sin(yy * 0.045 / s + j_ * 1.7) * (1.0 - q) ** 0.5
                S = cam.pts(np.stack([xs, yy], axis=1)).tolist()
                p.moveTo(*S[0])
                for pt in S[1:]:
                    p.lineTo(*pt)
            ws, al = F.lw(2.0 * s, 0.50 * a, 1.2)
            F.c.drawPath(p, F.pen(C.CHALK_COOL, ws, al, "mid"))
            specks(F, gx, gy, 3.0 * s, C.CHALK_COOL, 0.85 * a, "dense")


# --------------------------------------------------------------------------------------------------
# mist
# --------------------------------------------------------------------------------------------------
def mist(F: Frame, y: float = FLOOR, a: float = 1.0, h: float | None = None, col=None, seed: int = 0, t=None, x0=None, x1=None,
         low: float = 0.30, core: float = 1.0, slab=(0.0, 1.0)):
    """A band of rubbed haze lying on the horizon at world y: thickest on the line, thinning upward
    over about h and downward over low * h, in slow billows that drift sideways (t: its clock, default
    F.tb). It spans whatever the camera sees, or only world x0..x1 (soft ends). col: default cold haze
    at night, cream by day. core: 0..1 the paler seam along the line itself. h: world units; default
    170 / zoom ** 0.8, which keeps the band between 170 px (zoom 1) and about 125 px (zoom 0.2) on
    screen through a pull-back (a fixed world height would be a hairline in the wide frame).

    slab = (d0, d1): only the part of the mist between these depths (0 = its near face, 1 = its far
    side). A figure that has walked d = 0..1 of the way into it stands between two slabs:
    mist(F, slab=(d, 1)) BEFORE the figure, mist(F, slab=(0, d)) AFTER it, and the figure's own
    pressure is mist_keep(d). The two slabs together are exactly the whole band, whatever d is."""
    th = min(1.0, max(0.0, slab[1])) - min(1.0, max(0.0, slab[0]))
    if a <= 0.004 or th <= 0.004:
        return
    t = F.tb if t is None else t
    cam = F.cam
    z = cam.zoom
    h = 170.0 / max(z, 1e-6) ** 0.8 if h is None else h
    vl, _, vr, _ = cam.view(60.0)
    l = vl if x0 is None else max(vl, x0)
    r = vr if x1 is None else min(vr, x1)
    if r <= l:
        return
    dx = 64.0 * 2.0 ** math.floor(math.log2(1.0 / max(z, 1e-6)) + 0.5)       # columns anchored in the world, about 64 px apart
    xs = np.arange(math.floor(l / dx), math.ceil(r / dx) + 1) * dx
    den = np.clip(0.66 + 0.44 * (2.0 * vn(xs / 1100.0 + t * 0.010 + 7.3, seed) - 1.0)
                  + 0.30 * (2.0 * vn(xs / 3900.0 - t * 0.004 + 2.1, seed + 1) - 1.0), 0.18, 1.15)
    top = h * (0.62 + 0.76 * vn(xs / 760.0 + t * 0.008 + 4.4, seed + 2))
    if x0 is not None:
        den = den * smooth((xs - x0) / (h * 1.5))
    if x1 is not None:
        den = den * smooth((x1 - xs) / (h * 1.5))
    fr = np.array([1.0, 0.70, 0.42, 0.20, 0.06, 0.0])
    pa = np.array([0.0, 0.20, 0.52, 0.84, 1.0, 1.0])
    X = np.tile(xs, (len(fr) + 2, 1))
    Y = np.vstack([y - np.outer(fr, top), np.full((1, len(xs)), y + h * low * 0.4), np.full((1, len(xs)), y + h * low)])
    AL = np.vstack([np.outer(pa, den), 0.55 * den[None, :], 0.0 * den[None, :]])

    def part(al):                                                   # the share of a tone of strength al that lies in the slab
        return al if th >= 1.0 else 1.0 - (1.0 - np.minimum(al, 0.999)) ** th

    _mesh(F, X, Y, part(np.minimum(1.0, AL * 0.62 * a)), F.pick(HAZE, C.CREAM) if col is None else col, 1.0, "soft", additive=False,
          wide=True)
    if core > 0.0:
        k = len(fr) - 3
        _mesh(F, X[k:], Y[k:], part(np.minimum(1.0, AL[k:] * np.array([0.0, 0.7, 1.0, 0.5, 0.0])[:, None] * 0.42 * a * core)),
              F.pick(mix(HAZE, C.CHALK_BLUE, 0.55), C.CREAM) if col is None else col, 1.0, "soft", additive=False, wide=True)


def mist_keep(dist: float, reach: float = 1.0, floor: float = 0.0) -> float:
    """How much pressure the line of a figure keeps that has gone `dist` toward the mist, which
    swallows it at `reach` (same units; the default makes dist a 0..1 progress): 1 here, `floor`
    there. Slow at first, quickest in the middle: a figure is still itself for the first steps."""
    return floor + (1.0 - floor) * (1.0 - ease(dist / reach)) ** 1.25


# --------------------------------------------------------------------------------------------------
# the room: window pool, glow round the window, the lamp
# --------------------------------------------------------------------------------------------------
_MOODS = {  # light colour, strength from the window outward, hatch colour, shadow of the bars
    "night": (C.MOON, (0.44, 0.31, 0.19, 0.08, 0.0), C.MOON, C.PAPER_DEEP),
    "evening": (mix(C.CHALK, C.CHALK_COOL, 0.30), (0.34, 0.28, 0.21, 0.13, 0.05, 0.0), C.CHALK, C.PAPER_DEEP),
    "sunset": (C.EVE_LOW, (0.62, 0.66, 0.60, 0.44, 0.22, 0.0), C.CORAL, C.SHADOW),
}
GOLD = mix(C.SUN_HALO, C.MUSTARD, 0.45)      # lamplight and low sun as pastel on the warm paper


def _mood(F: Frame, mood):
    return mood or ("sunset" if F.day else "night")


def window_pool(F: Frame, l, r, y0, a: float = 1.0, lean: float = -0.55, depth: float = 300.0, mull: bool = True, col=None,
                mood: str | None = None, narrow: float = 0.0, shade: float = 1.0):
    """A window's light lying on the floor: a slanting pool from world y0 (the floor line) down
    `depth`, between world x l and r at the top, pushed sideways by `lean`, with the shadow of the
    window's cross in it (mull). mood: "night" cold blue (default on night paper), "evening" pale and
    colourless (the second verse: pass a longer depth and lean, e.g. 380 and -0.9), "sunset" gold
    going to orange-rose pastel on the warm paper (default on day paper; with `shade`, 0..1, a breath
    of violet dusk round it so that it reads as light). narrow: 0..1 draws the pool together into a
    sliver along its long far edge (the pool that becomes a line). Returns the four world corners
    (top-left, top-right, bottom-right, bottom-left): corners[0] to corners[3] is that long edge."""
    mood = _mood(F, mood)
    lc, prof, hc, bar = _MOODS[mood]
    lc = lc if col is None else col
    x0, x1 = l + lean * 60.0, r + lean * 60.0
    x2, x3 = r + lean * (60.0 + depth * 1.9), l + lean * (60.0 + depth * 2.4) - 60.0
    if narrow > 0.0:
        k = min(1.0, narrow) * 0.985
        x1, x2 = x1 + (x0 - x1) * k, x2 + (x3 - x2) * k
    Q = A((x0, y0), (x1, y0), (x2, y0 + depth), (x3, y0 + depth))
    if a <= 0.004:
        return Q
    n = 13
    v = np.linspace(0.0, 1.0, n)
    al = np.interp(v, np.linspace(0.0, 1.0, len(prof)), prof)
    Lp = np.stack([x0 + (x3 - x0) * v, y0 + depth * v], axis=1)
    Rp = np.stack([x1 + (x2 - x1) * v, y0 + depth * v], axis=1)
    wd = 1.0 - min(1.0, narrow)
    sun = mood == "sunset"
    edge = (0.03 + 0.09 * v) * wd + 0.3 * (1.0 - wd)
    if sun:
        if shade > 0.0:                                               # dusk on the floor on both sides of the light
            for sg, xa, xb in ((-1.0, x0, x3), (1.0, x1, x2)):
                off = sg * (60.0 + 0.55 * depth * v)
                E = np.stack([xa + (xb - xa) * v, y0 + depth * v], axis=1)
                O = E + np.stack([off, np.zeros(n)], axis=1)
                lo, hi = (O, E) if sg < 0 else (E, O)
                _strip(F, lo, hi, 0.9 - 0.5 * v, C.SHADOW, 0.20 * a * shade * wd, "soft", additive=False, edge=0.5, wide=True)
        _strip(F, Lp, Rp, al, lc, a, "soft", additive=False, edge=edge, wide=True)
        _strip(F, Lp[:9], Rp[:9], np.interp(v[:9], [0.0, 0.25, 0.66], [0.85, 0.60, 0.0]), GOLD, 0.85 * a, "soft", additive=False,
               edge=edge[:9] + 0.05, wide=True)
    else:
        _strip(F, Lp, Rp, al, lc, a, "glow", additive=True, edge=edge, wide=True)
    if wd > 0.25:                                                     # loose strokes of the light's chalk, laid the way the light falls
        m = 11
        j = np.arange(m)
        uu = np.clip((j + 0.5 + 0.7 * (htab(j, 7, 611) - 0.5)) / m, 0.03, 0.97)
        va = 0.02 + 0.30 * htab(j, 11, 612) ** 1.5
        vb = np.minimum(0.84, va + 0.30 + 0.42 * htab(j, 13, 613))    # they stop where the light gives out
        q = np.linspace(0.0, 1.0, 7)
        vv = va[:, None] + (vb - va)[:, None] * q[None, :]
        ub = uu[:, None] + 0.035 * (vn(q[None, :] * 2.2 + j[:, None] * 5.3, 614) - 0.5)
        xa, xb = x0 + (x1 - x0) * ub, x3 + (x2 - x3) * ub
        S = F.cam.pts(np.stack([(xa + (xb - xa) * vv).ravel(), (y0 + depth * vv).ravel()], axis=1)).reshape(m, len(q), 2)
        if not _off(S.reshape(-1, 2), 0.0):
            p = skia.Path()
            for row in S.tolist():
                p.moveTo(*row[0])
                for pt in row[1:]:
                    p.lineTo(*pt)
            ws, al = F.lw(5.5, (0.30 if sun else 0.085) * a * wd, 1.4)
            F.c.drawPath(p, F.pen(hc, ws, al, "sparse"))
    if mull and wd > 0.05:
        ba = (0.34 if sun else 0.78) * a * wd
        q = np.linspace(0.0, 1.0, 9)
        mx = (x0 + x1) / 2.0 + ((x2 + x3) / 2.0 - (x0 + x1) / 2.0) * q + 2.5 * (2.0 * vn(q * 3.0, 62) - 1.0)
        hw = (6.5 + 10.0 * q) * wd
        _strip(F, np.stack([mx - hw, y0 + depth * q], 1), np.stack([mx + hw, y0 + depth * q], 1), 1.0 - 0.7 * q ** 1.5, bar, ba,
               "soft", additive=False, edge=0.40, wide=True)
        f = 0.42
        ya = y0 + depth * f
        xa, xb = x0 + (x3 - x0) * f, x1 + (x2 - x1) * f
        xx = xa + (xb - xa) * q
        yy = ya + 2.0 * (2.0 * vn(q * 3.0, 63) - 1.0)
        hh = 8.0 * wd
        _strip(F, np.stack([xx, yy - hh], 1), np.stack([xx, yy + hh], 1), 0.85 * np.sin(np.pi * np.clip(0.04 + q * 0.92, 0, 1)) ** 0.25,
               bar, ba, "soft", additive=False, edge=0.40, wide=True)
    return Q


def moon_pool(F: Frame, l, r, y0, a: float = 1.0, lean: float = -0.55, depth: float = 300.0, mull: bool = True, col=C.MOON):
    """The night window's cold pool on the floor (window_pool in its night mood)."""
    return window_pool(F, l, r, y0, a, lean, depth, mull, col, "night")


def window_glow(F: Frame, l, t_, r, b, a: float = 1.0, mood: str | None = None, col=None, spread: float | None = None):
    """The light a window lays on the wall round itself (draw it before the window and what it
    shows): rubbed light that hugs the frame and thins outward over `spread` world units (default
    0.58 of the window's larger side). Nothing is rubbed behind the pane. mood as in window_pool."""
    if a <= 0.004:
        return
    mood = _mood(F, mood)
    lc = _MOODS[mood][0] if col is None else col
    cx, cy, hw, hh = (l + r) / 2.0, (t_ + b) / 2.0, (r - l) / 2.0, (b - t_) / 2.0
    sp = 1.16 * max(hw, hh) if spread is None else spread
    th = np.linspace(0.0, 2.0 * math.pi, 41) + 0.11
    dx, dy = np.cos(th), np.sin(th)
    tt = np.minimum(hw * 0.9 / np.maximum(np.abs(dx), 1e-6), hh * 0.9 / np.maximum(np.abs(dy), 1e-6))
    grow = sp * (0.85 + 0.3 * vn(th * 1.3, 207))                       # not a ruler's halo
    fr = np.array([0.0, 0.16, 0.38, 0.66, 1.0])[:, None]
    al = np.array([1.0, 0.70, 0.38, 0.14, 0.0])[:, None] * np.ones((1, len(th)))
    X = cx + dx[None, :] * (tt[None, :] + grow[None, :] * fr)
    Y = cy + dy[None, :] * (tt[None, :] + grow[None, :] * fr)
    if mood == "sunset":
        _mesh(F, X, Y, al, GOLD if col is None else col, 0.62 * a, "soft", additive=False)
    else:
        _mesh(F, X, Y, al, lc, (0.25 if mood == "night" else 0.22) * a, "soft", additive=True)


def lamp_light(F: Frame, x, y, h: float = 420.0, a: float = 1.0, col=None, floor: float | None = None):
    """The standing lamp lit (props.lamp(x, y, h): the same anchor): a warm cone falling from the
    shade to a pool on the floor, a smaller fan going up, the shade full of light. Unlit at night (do
    not call it before the coda: warmth before 217.84 s belongs to the friend alone); on the warm
    paper it is gold pastel. floor: world y where the pool lies (default y). Draw it right AFTER the
    lamp (its light lies over the pole and inside the shade's outline)."""
    if a <= 0.004:
        return
    s = h / 420.0
    fy = y if floor is None else floor
    ty, by = y - h, y - h + 96.0 * s                       # the shade's top and bottom rim
    day = F.day
    lc = (GOLD if day else C.AMBER_GLOW) if col is None else col
    core = C.SUN_CORE if day else C.AMBER_PALE
    g, add = ("soft", False) if day else ("glow", True)
    k = 1.0 if day else 0.55
    v = np.linspace(0.0, 1.0, 9)
    hw = 44.0 * s + (fy - by) * 0.50 * v
    yy = by + (fy + 16.0 * s - by) * v
    _strip(F, np.stack([x - hw, yy], 1), np.stack([x + hw, yy], 1), np.interp(v, [0, 0.3, 0.7, 1], [0.80, 0.55, 0.42, 0.32]), lc,
           0.95 * a * k, g, add, edge=0.42)
    # loose strokes of the lamp's own crayon, fanning down from under the shade (the light is drawn, not only rubbed)
    m = 9
    j = np.arange(m)
    uu = (j + 0.5 + 0.6 * (htab(j, 7, 451) - 0.5)) / m * 2.0 - 1.0     # -1..1 across the cone
    va = 0.03 + 0.10 * htab(j, 11, 452)
    vb = 0.46 + 0.40 * htab(j, 13, 453) * (1.0 - 0.45 * np.abs(uu))    # the outer ones give out sooner
    q = np.linspace(0.0, 1.0, 6)
    vv = va[:, None] + (vb - va)[:, None] * q[None, :]
    ub = 0.84 * uu[:, None] + 0.05 * (vn(q[None, :] * 2.0 + j[:, None] * 4.1, 454) - 0.5)
    S = F.cam.pts(np.stack([(x + ub * (44.0 * s + (fy - by) * 0.50 * vv)).ravel(), (by + (fy + 16.0 * s - by) * vv).ravel()],
                           axis=1)).reshape(m, len(q), 2)
    if not _off(S.reshape(-1, 2), 0.0):
        p = skia.Path()
        for row in S.tolist():
            p.moveTo(*row[0])
            for pt in row[1:]:
                p.lineTo(*pt)
        ws, al = F.lw(5.0 * s, (0.50 if day else 0.22) * a, 1.4)
        F.c.drawPath(p, F.pen(mix(lc, C.MUSTARD, 0.5) if day else lc, ws, al, "sparse"))
    rp = 44.0 * s + (fy - by) * 0.58
    smudge(F, x, fy + 22.0 * s, rp, 50.0 * s, lc, 0.70 * a * k, g, additive=add, power=1.3)
    smudge(F, x, fy + 20.0 * s, rp * 0.5, 24.0 * s, core, 0.55 * a * k, g, additive=add, power=1.5)
    u = np.linspace(0.0, 1.0, 5)
    hu = 26.0 * s + 150.0 * s * u
    yu = ty - 190.0 * s * u
    _strip(F, np.stack([x - hu, yu], 1), np.stack([x + hu, yu], 1), np.array([0.6, 0.36, 0.18, 0.06, 0.0]), lc, 0.7 * a * k, g, add,
           edge=0.45)
    smudge(F, x, (ty + by) / 2.0, 170.0 * s, 150.0 * s, lc, 0.45 * a * k, g, additive=add, power=1.6)
    sh = A((x - 43 * s, by - 3 * s), (x - 25 * s, ty + 4 * s), (x + 25 * s, ty + 4 * s), (x + 45 * s, by - 3 * s))
    fill(F, sh, C.DAY if day else C.KNOCK, 0.9 * a)
    fill(F, sh, core, 0.95 * a, "mid")
    hatch(F, np.vstack([sh, sh[:1]]), lc, 1.2, 9.0 * s, 4.0 * s, 0.7 * a, 447, grain="mid", clip=True, boil=False)


# --------------------------------------------------------------------------------------------------
# shafts, pools, dust
# --------------------------------------------------------------------------------------------------
def _along(alphas, per: int = 4, top: float = 0.0):
    """Rows along a shaft: positions v and strengths, with a short soft start and a soft end past the
    landing. top: the share of its length over which it comes out of nothing at its upper end."""
    m = (len(alphas) - 1) * per + 1
    v = np.linspace(0.0, 1.0, m)
    al = np.interp(v, np.linspace(0.0, 1.0, len(alphas)), np.asarray(alphas, dtype=np.float64))
    if top > 0.0:
        al = al * smooth(v / top) ** 1.5
    return np.concatenate([[-0.035], v, [1.05]]), np.concatenate([[0.0], al, [0.0]])


def shaft(F: Frame, x0, w0, y0, x1, w1, y1, col=None, a: float = 0.15, alphas=(1.0, 0.67, 0.47, 0.2), soft: float = 0.34,
          top: float = 0.0):
    """One shaft of light: from a slit centred world x0 (half width w0) at y0 down to a patch centred
    x1 (half width w1) at y1, soft at both sides (soft: the share of the half width that is penumbra)
    and at both ends. `alphas`: its strength from top to bottom. col: default light_col(F) (pale cold
    before the sheet rips, pale warm after). Additive on the night paper, cream pastel on the day paper.
    top: the share of its length over which it comes out of nothing at its upper end (0: it starts
    full, for a slit that the scribble or the frame hides; about 0.25 when its upper end is in view)."""
    v, al = _along(alphas, 4, top)
    cx, cy, hw = x0 + (x1 - x0) * v, y0 + (y1 - y0) * v, w0 + (w1 - w0) * v
    _strip(F, np.stack([cx - hw, cy], 1), np.stack([cx + hw, cy], 1), al, light_col(F) if col is None else col, a,
           "soft" if F.day else "glow", additive=not F.day, edge=soft)


def shafts(F: Frame, x0, half, y0, xa, xb, y1, n: int = 7, col=None, a: float = 0.15, seed: int = 0,
           alphas=(1.0, 0.67, 0.47, 0.2), top: float = 0.0):
    """A fan of n soft shafts through a gap centred world x0 (half width `half`) at y0, landing between
    xa and xb at y1: uneven in width and strength, overlapping, one rubbed tone (one draw call).
    a: the strength of a single shaft at its top. seed: its hand (another fan, another seed).
    top: as in shaft (give about 0.25 when nothing hides the fan's upper end)."""
    n = int(n)
    q0 = (np.arange(n) + 0.5 + 0.5 * np.array([rsym(j + seed, 74) for j in range(n)])) / n          # where each shaft sits in the fan
    dl = np.array([(0.55 + 0.75 * rnd(j + seed, 71)) / n for j in range(n)])                        # its half width, as a share of the fan
    kk = np.array([0.55 + 0.75 * rnd(j + seed, 73) for j in range(n)])
    u = np.unique(np.round(np.concatenate([q0 - dl, q0 - 0.5 * dl, q0, q0 + 0.5 * dl, q0 + dl]), 4))
    d = np.abs(u[None, :] - q0[:, None]) / dl[:, None]
    pa = (kk[:, None] * np.interp(d, [0.0, 0.5, 1.0], [1.0, 0.36, 0.0])).sum(0)                    # the profile across the fan
    v, al = _along(alphas, 3, top)
    xl = (x0 - half) + (xa - (x0 - half)) * v
    xr = (x0 + half) + (xb - (x0 + half)) * v
    X = xl[:, None] + (xr - xl)[:, None] * u[None, :]
    Y = np.repeat((y0 + (y1 - y0) * v)[:, None], len(u), axis=1)
    _mesh(F, X, Y, al[:, None] * pa[None, :], light_col(F) if col is None else col, a, "soft" if F.day else "glow", additive=not F.day)


def light_pool(F: Frame, x, y, rx, ry=None, col=None, a: float = 0.3, core: float = 0.5):
    """Where a shaft lands: light rubbed flat on the ground round the world point (x, y), rx wide
    (half), ry deep (default rx * 0.17: a floor seen from the side), a brighter heart in it (core 0..1)."""
    if a <= 0.004:
        return
    ry = rx * 0.17 if ry is None else ry
    col = light_col(F) if col is None else col
    g, add = ("soft", False) if F.day else ("glow", True)
    smudge(F, x, y, rx, ry, col, a, g, additive=add, power=1.25)
    if core > 0.0:
        smudge(F, x, y, rx * 0.55, ry * 0.55, col, a * core, g, additive=add, power=1.6)


def _motes(F: Frame, xs, ys, rr, tw, col, a: float):
    """Dust: dots of radius rr, each with its own glint tw (0..1), in four pressures; the brightest
    carry a breath of light round them."""
    for q in range(4):
        m = (tw >= q / 4.0) & (tw < (q + 1) / 4.0 + (q == 3))
        if m.any():
            k = (q + 0.5) / 4.0
            if q == 3:
                specks(F, xs[m], ys[m], rr[m] * 2.6, col, a * 0.16, "sparse")
            specks(F, xs[m], ys[m], rr[m] * (0.75 + 0.5 * k), col, a * (0.22 + 0.78 * k ** 1.4), "dense")


def _dust_col(F: Frame):
    """Dust is the light's colour on the dark paper; on the warm paper it is pastel dust, rose-brown."""
    return mix(C.EVE_LOW, C.PENCIL, 0.35) if F.day else light_col(F)


def _wander(i, t, seed):
    """Slow turning of dust motes: (dx, dy) in -1..1 and a glint 0..1 per mote."""
    f1, f2 = 0.07 + 0.10 * htab(i, 31, seed + 1), 0.05 + 0.09 * htab(i, 37, seed + 2)
    p1, p2 = 6.283 * htab(i, 41, seed + 3), 6.283 * htab(i, 43, seed + 4)
    dx = np.sin(6.283 * f1 * t + p1) * 0.7 + np.sin(6.283 * f2 * 2.3 * t + p2) * 0.3
    dy = np.cos(6.283 * f2 * t + p2) * 0.7 + np.sin(6.283 * f1 * 1.7 * t + p1) * 0.3
    tw = 0.5 + 0.5 * np.sin(6.283 * (0.16 + 0.22 * htab(i, 47, seed + 5)) * t + 6.283 * htab(i, 53, seed + 6))
    return dx, dy, tw ** 1.4


def dust(F: Frame, l, t_, r, b, n: int = 34, col=None, a: float = 0.5, seed: int = 77, t=None, drift: float = 0.03,
         size: float = 1.0):
    """Chalk dust turning in the light inside the world rectangle (l, t_, r, b): n motes that wander,
    glint as they turn and sink slowly (drift: share of the box height per second; negative rises).
    t: the clock (default F.tb, on twos and still in the silences; pass F.t where the dust is the only
    thing that moves, as in the long silence: it then moves on every frame). size: scale of the motes.
    col: default the light's colour (light_col) on the night paper, rose-brown pastel dust by day."""
    n = int(n)
    if n <= 0 or a <= 0.004:
        return
    t = F.tb if t is None else t
    i = np.arange(n)
    dx, dy, tw = _wander(i, t, seed)
    amp = 0.035 * min(r - l, b - t_)
    xs = l + htab(i, 7, seed) * (r - l) + amp * dx
    v = (htab(i, 11, seed + 2) + t * drift * (0.5 + htab(i, 13, 5))) % 1.0
    ys = t_ + v * (b - t_) + amp * dy
    edge = np.minimum(1.0, np.minimum(v, 1.0 - v) / 0.08)             # born and lost softly at the box's top and bottom
    _motes(F, xs, ys, (1.5 + 1.7 * htab(i, 17, 3)) * size, tw * edge, _dust_col(F) if col is None else col, a)


def shaft_dust(F: Frame, x0, w0, y0, x1, w1, y1, n: int = 40, col=None, a: float = 0.7, seed: int = 78, t=None,
               drift: float = 0.02, size: float = 1.0):
    """Dust turning slowly inside a shaft (the shaft's own arguments): motes wander across it, sink
    along it, glint and go out near its edges. t: the clock (default F.tb; pass F.t in the long
    silence, where it is the only thing moving besides the two figures)."""
    n = int(n)
    if n <= 0 or a <= 0.004:
        return
    t = F.tb if t is None else t
    i = np.arange(n)
    dx, dy, tw = _wander(i, t, seed)
    v = (htab(i, 11, seed + 2) + t * drift * (0.5 + htab(i, 13, 5)) + 0.03 * dy) % 1.0
    u = np.clip((2.0 * htab(i, 7, seed) - 1.0) * 0.8 + 0.22 * dx, -1.0, 1.0)
    xs = x0 + (x1 - x0) * v + (w0 + (w1 - w0) * v) * u
    ys = y0 + (y1 - y0) * v
    edge = np.minimum(1.0, np.minimum(v, 1.0 - v) / 0.10) * np.minimum(1.0, (1.0 - np.abs(u)) / 0.25)
    _motes(F, xs, ys, (1.5 + 1.9 * htab(i, 17, 3)) * size, tw * edge, _dust_col(F) if col is None else col, a)


def gap_light(F: Frame, x0, w0, y0, x1, w1, y1, a: float = 1.0, open_: float = 1.0, col=None, dust_n: int = 40, t=None,
              pool: float = 1.0, seed: int = 0):
    """The light through a gap in the scribble, whole: a soft shaft from the gap (centre x0, half width
    w0, at y0) to the ground (centre x1, half width w1, at y1), finer rays inside it, the pool where it
    lands and dust turning in it. open_: 0..1 how far the gap stands open (the shaft's width and
    strength grow with it); a: strength (0.4: a guess of light; 1: the shaft that lands on the child).
    t: the dust's clock (default F.tb; F.t in the long silence). pool: 0..1. Draw it BEFORE the
    figures and the scribble; for light ON a figure add glow(F, x, y, r, col=light_col(F)) after it."""
    op = min(1.0, max(0.0, float(open_)))
    if op <= 0.004 or a <= 0.004:
        return
    col = light_col(F) if col is None else col
    k = 0.25 + 0.75 * op
    ww0, ww1 = w0 * op + 3.0, w1 * (0.35 + 0.65 * op)
    shaft(F, x0, ww0 * 1.3, y0, x1, ww1 * 1.3, y1, col, 0.22 * a * k, (1.0, 0.84, 0.68, 0.5), soft=0.45)
    shafts(F, x0, ww0 * 0.9, y0, x1 - ww1 * 0.9, x1 + ww1 * 0.9, y1, 5, col, 0.17 * a * k, seed + 5, (1.0, 0.8, 0.6, 0.42))
    if pool > 0.0:
        light_pool(F, x1, y1 + ww1 * 0.06, ww1 * 1.5, None, col, 0.36 * a * k * pool)
    if dust_n > 0:
        shaft_dust(F, x0, ww0, y0, x1, ww1, y1, int(dust_n * (0.4 + 0.6 * op)), col, 0.8 * min(1.0, a) * op, seed + 78, t)


# --------------------------------------------------------------------------------------------------
# the friend's amber
# --------------------------------------------------------------------------------------------------
def glow(F: Frame, x, y, rx, ry=None, col=C.AMBER_GLOW, a: float = 0.2, power: float = 1.6):
    """Rubbed light round a world point (the friend, a lit window, the phone): additive on the night
    paper, soft pastel on the day paper."""
    if F.day:
        smudge(F, x, y, rx, rx if ry is None else ry, col, a, "soft", power=power)
    else:
        smudge(F, x, y, rx, rx if ry is None else ry, col, a, "glow", additive=True, power=power)


def amber_glow(F: Frame, x, y, h, a: float = 1.0, wet: float = 0.0, t=None):
    """The friend's glow. (x, y) = the friend's ground point, h = the height of the figure as it
    stands NOW (world: 388 standing, about 0.62 of that crouched or sitting; the glow sits on the
    middle of that height). Near, it is amber pastel rubbed round the figure with a lit heart at its
    chest and light on the ground at its feet (never larger than about 340 px, however close). Far
    away the whole of it is light, and it never shrinks under 200 px radius on screen, so that a
    60 px friend is still a warm point in a wide cold frame. wet: 0..1 adds its reflection on wet
    ground (wet_reflection). Draw it BEFORE the friend. Night skin only: on the day paper it draws
    nothing (by day the friend needs no glow)."""
    if a <= 0.004 or F.day:
        return
    z = F.cam.zoom
    hs = h * z
    r1 = max(min(0.70 * hs, 340.0), 200.0) / z
    r2 = max(min(0.42 * hs, 210.0), 64.0) / z
    far = 1.0 - ramp(hs, 90.0, 260.0)                    # a far friend is a light more than a figure: its heart burns brighter
    near = 1.0 - far
    cy = y - h * 0.50
    # Near, light added to the blue paper at a halo's strength turns grey-brown: there the halo is amber
    # pastel rubbed round the figure (it takes the blue out), and only the heart is light. Far away the
    # whole of it is light.
    if near > 0.02:
        smudge(F, x, cy, r1, r1 * 0.98, C.AMBER_DEEP, 0.31 * near * a, "glow", power=1.25)
    if far > 0.02:
        smudge(F, x, cy, r1, r1 * 0.90, C.AMBER_GLOW, 0.29 * far * a, "glow", additive=True, power=1.6)
    smudge(F, x, cy, r2, r2 * (1.05 + 0.25 * near), C.AMBER_GLOW, (0.26 + 0.27 * far) * a, "glow", additive=True, power=1.5,
           inner=0.12 + 0.2 * far)
    smudge(F, x, y + 0.03 * h, r2 * 1.55, max(r2 * 0.15, 5.0 / z), C.AMBER, 0.22 * a, "glow", additive=True, power=1.3)
    if wet > 0.0:
        wet_reflection(F, x, y, max(0.17 * h, 13.0 / z), a * wet, t=t, ln=max(0.42 * h, 56.0 / z))


def amber_point(F: Frame, x, y, a: float = 1.0, r: float = 1.0):
    """A point of amber light at the world point (x, y): what the friend becomes far away, and the
    window across the street seen small. Sized in SCREEN px (r scales it): it does not shrink with
    the camera."""
    if a <= 0.004:
        return
    z = F.cam.zoom
    glow(F, x, y, 120.0 * r / z, 104.0 * r / z, C.AMBER_GLOW, 0.20 * a, 1.8)
    glow(F, x, y, 34.0 * r / z, 34.0 * r / z, C.AMBER_GLOW, 0.42 * a, 1.5)
    glow(F, x, y, 11.0 * r / z, 11.0 * r / z, C.AMBER_PALE, 0.70 * a, 1.2)
    disc(F, x, y, 2.6 * r / z, C.AMBER_PALE, a, "dense")


def wet_reflection(F: Frame, x, y, w, a: float = 1.0, col=C.AMBER, ln=None, seed: int = 0, t=None, rows: int = 8):
    """A light's reflection on wet ground, the way a child draws one: under the world point (x, y)
    ONE scribbled zigzag, wide and close under the light, narrower, looser and fainter downward over
    the length ln (default 4 w), breaking into a dash or two at its end, on a faint rubbed smear.
    w: half width of its first stroke. rows: how many strokes the zigzag has. It shimmers slowly: the
    turns slide sideways (t: its clock, default F.tb)."""
    if a <= 0.004:
        return
    t = F.tb if t is None else t
    ln = 4.0 * w if ln is None else ln
    z = F.cam.zoom
    smudge(F, x, y + ln * 0.36, w * 1.4, ln * 0.5, col, 0.20 * a, "glow", additive=True, power=1.4)
    rows = max(3, int(rows))
    j = np.arange(rows + 3)                                             # the turns of the zigzag (the last three: loose dashes)
    v = np.minimum(1.0, j / (rows + 1.0))
    side = np.where(j % 2 == 0, -1.0, 1.0)
    hw = w * (1.0 - 0.62 * v) * (0.66 + 0.68 * htab(j, 7, seed * 31 + 2))
    xx = x + side * hw + w * 0.15 * (2.0 * htab(j, 11, seed * 37 + 3) - 1.0) + w * 0.17 * np.sin(t * 1.9 + j * 2.3)
    yy = y + 3.0 / z + ln * (j / (rows + 2.0)) ** 1.5 + ln * 0.02 * (2.0 * htab(j, 13, seed * 41 + 5) - 1.0)
    cam = F.cam
    ww = max(2.4, w * 0.11)
    P = spline(np.stack([xx[:rows], yy[:rows]], axis=1), rows * 6)      # one stroke, its turns rounded by the hand
    S = cam.pts(P)
    m = len(S)
    for k in range(3):                                                  # pressed lighter as it goes down
        lo, hi = k * m // 3, min(m, (k + 1) * m // 3 + 1)
        p = skia.Path()
        p.moveTo(*S[lo].tolist())
        for pt in S[lo + 1:hi].tolist():
            p.lineTo(*pt)
        ws, al = F.lw(ww * (1.0 - 0.12 * k), a * (0.88 - 0.26 * k), 1.3)
        F.c.drawPath(p, F.pen(col, ws, al, "mid"))
    d = np.arange(rows, rows + 2)                                       # where it breaks up
    dashes(F, xx[d] - side[d] * hw[d] * 0.2, yy[d + 1], xx[d] - side[d] * hw[d] * 1.5, yy[d + 1] + ln * 0.012, ww * 0.8, col,
           0.30 * a, "mid")


def _flat(y):
    return lambda xs: np.full_like(np.asarray(xs, dtype=np.float64), y)


def amber_line(F: Frame, x0, x1, y: float = FLOOR, head: float = 1.0, pulse=None, a: float = 1.0, w: float = 5.0, curve=None,
               reach: float = 150.0):
    """The amber ground line: the ground line itself gone over in amber chalk from world x0 (the
    friend's feet) toward x1 (the child's), with brightness travelling along it.

    head: 0..1 how far it has been drawn from x0 (its tip is a bright bead while it runs). pulse: where
    a pulse of brightness is, 0 at x0 .. 1 at x1: a number, a list of numbers, a list of (position,
    strength) pairs, or None; only the drawn part can carry one. a: pressure of the line; w: its width (the ground line's is 4.2). y: the ground line's
    world y (it has the ground line's own hand, so it lies exactly on it); curve: the same contour
    function you give ground_line on the hills. reach: half length of a pulse in SCREEN px. Draw it
    right after ground_line(F). Returns the world point of the tip. For the storyboard's timing (a
    surge per beat) see amber_run."""
    head = min(1.0, max(0.0, float(head)))
    if a <= 0.004 or head <= 0.0:
        return None
    cv = curve if curve is not None else (None if abs(y - FLOOR) < 1e-6 else _flat(y))
    yof = (lambda xx: y) if curve is None else (lambda xx: float(curve(np.array([xx], dtype=np.float64))[0]))
    z = F.cam.zoom
    w = max(w, 2.3 / z)                                                 # far away it stays a line of light, not a hair
    xh = x0 + (x1 - x0) * head
    lo, hi = min(x0, xh), max(x0, xh)
    # the warmth it lays on the ground (only the part on screen is rubbed)
    vl, _, vr, _ = F.cam.view(40.0)
    gl, gr = max(lo, vl), min(hi, vr)
    if gr > gl:
        smudge(F, (gl + gr) / 2.0, yof((gl + gr) / 2.0), (gr - gl) / 2.0 + 30.0 / z, 15.0 / z, C.AMBER_GLOW, 0.20 * a, "glow",
               additive=True, power=0.8, inner=0.7)
    ground_line(F, cv, a=0.95 * a, w=w, col=C.AMBER, span=(lo, hi))
    tip = (xh, yof(xh))
    if head < 1.0:                                                      # the chalk's tip, leading
        glow(F, tip[0], tip[1], 42.0 / z, 30.0 / z, C.AMBER_GLOW, 0.5 * a, 1.5)
        disc(F, tip[0], tip[1], max(w * 0.8, 3.2 / z), C.AMBER_PALE, a, "dense")
    if pulse is not None:
        rw = reach / z
        items = [pulse] if np.isscalar(pulse) else list(pulse)
        for it in items:
            p, st = (float(it), 1.0) if np.isscalar(it) else (float(it[0]), float(it[1]))
            if not (0.0 <= p <= 1.0) or p > head + 1e-6 or st <= 0.004:
                continue
            xp = x0 + (x1 - x0) * p
            if xp + rw < vl or xp - rw > vr:
                continue
            k = st * min(1.0, 4.0 * p + 0.25)                           # it swells out of the friend's feet
            yp = yof(xp)
            glow(F, xp, yp, rw * 1.15, 34.0 / z, C.AMBER_GLOW, 0.34 * a * k, 1.3)
            glow(F, xp, yp, rw * 0.42, 15.0 / z, C.AMBER_PALE, 0.34 * a * k, 1.3)
            ground_line(F, cv, a=0.75 * a * k, w=w * 1.5, col=C.AMBER_GLOW, span=(max(lo, xp - rw), min(hi, xp + rw)))
            ground_line(F, cv, a=0.95 * a * k, w=w * 1.15, col=C.AMBER_PALE, span=(max(lo, xp - rw * 0.4), min(hi, xp + rw * 0.4)))
    return tip


def amber_run(F: Frame, t0: float, t1: float, travel: float = 0.55, after: float = 0.0, linger: float = 0.6):
    """The storyboard's timing for amber_line: the line runs from the friend to the child between t0
    and t1 (72.46 and 74.6), surging on every beat and easing between; on every beat a pulse of
    brightness leaves the friend's feet and catches the tip up in `travel` seconds; the last one
    reaches the child's feet exactly at t1 and dies away there over `linger` seconds. after: if > 0,
    later on a pulse every `after` beats runs the whole line (in two beats). Returns (head, pulses)
    for amber_line(F, x0, x1, y, head, pulses); a pulse is a (position, strength) pair."""
    t, tl = F.t, F.tl
    if t < t0:
        return 0.0, ()
    bs, b0 = tl.beat_s, tl.beat0

    def g(tt):                                                          # advance with a surge on each beat
        ph = (tt - b0) / bs
        return (tt - t0) + 0.80 * bs / (2.0 * math.pi) * (math.sin(2.0 * math.pi * ph) - math.sin(2.0 * math.pi * (t0 - b0) / bs))

    head = min(1.0, g(min(t, t1)) / g(t1))
    pulses = []
    starts = [t0] + [float(b) for b in tl.beats_between(t0 + 0.2, t1 - 0.3)]
    for j, s0 in enumerate(starts):
        last = j == len(starts) - 1
        end = max(t1 if last else s0 + travel, s0 + 0.2)
        if t < s0:
            continue
        u = (t - s0) / (end - s0)
        if last:
            if t < end + linger:
                pulses.append((min(head, ease_out(min(1.0, u), 1.6)), 1.0 if t <= end else 1.0 - ease((t - end) / linger)))
        elif u < 1.0:
            tgt = min(1.0, g(min(end, t1)) / g(t1))
            pulses.append((min(head, tgt * ease_out(u, 1.6)), 1.0 - 0.7 * ease((u - 0.7) / 0.3)))     # it melts into the tip
    if after > 0.0 and t > t1:
        k0 = math.ceil((t1 + linger - b0) / bs)
        k = math.floor((t - b0) / bs)
        while k >= k0 and (t - (b0 + k * bs)) < 2.0 * bs:
            if (k - k0) % max(1, int(round(after))) == 0:
                u = (t - (b0 + k * bs)) / (2.0 * bs)
                pulses.append((ease(u), 1.0 - ease((u - 0.8) / 0.2)))
            k -= 1
    return head, tuple(pulses)


def amber_window(F: Frame, l, t_, r, b, a: float = 1.0, pane: bool = True, halo: float = 1.0):
    """The lit window across the street, world rectangle (l, t_, r, b): the pane filled in amber with
    a paler heart and its cross-bar (pane=False: only the light, round a pane drawn elsewhere), and
    its glow, which never shrinks under about 70 px on screen. The friend was always there."""
    if a <= 0.004:
        return
    z = F.cam.zoom
    cx, cy, wd, hh = (l + r) / 2.0, (t_ + b) / 2.0, r - l, b - t_
    if halo > 0.0:
        r1 = max(3.6 * max(wd, hh), 70.0 / z)
        glow(F, cx, cy + hh * 0.1, r1, r1 * 0.9, C.AMBER_GLOW, 0.36 * a * halo, 1.7)
        glow(F, cx, cy, max(1.3 * wd, 22.0 / z), max(1.3 * hh, 22.0 / z), C.AMBER_GLOW, 0.30 * a * halo, 1.4)
    if pane:
        P = A((l, t_), (r, t_ + 0.02 * hh), (r - 0.02 * wd, b), (l + 0.02 * wd, b - 0.02 * hh))
        fill(F, P, C.AMBER, 0.96 * a, "dense")
        smudge(F, cx, cy, wd * 0.5, hh * 0.5, C.AMBER_PALE, 0.7 * a, "mid", power=1.2)
        chalk(F, A((cx, t_), (cx + 0.02 * wd, b)), C.AMBER_DEEP, max(1.6, wd * 0.08), 0.9 * a, 73, wob=0.0, edge=0.0, floor=1.0)
        chalk(F, A((l, cy), (r, cy + 0.02 * hh)), C.AMBER_DEEP, max(1.4, wd * 0.07), 0.8 * a, 74, wob=0.0, edge=0.0, floor=1.0)


def rim(F: Frame, J: dict, side: int = 1, col=C.AMBER, a: float = 1.0, w: float = 4.0, seed: int = 90):
    """An amber rim on a figure's side: the light of the friend (or of the amber line) reaching the
    child. J: the joints figure() returned (head, R, neck, pel, sh_f, sh_b, ha_f, ha_b, kn_f, kn_b,
    an_f, an_b: world points). side: +1 the light comes from the right, -1 from the left. Short
    strokes of amber chalk just outside the head, the lit arm and the lit leg. Draw it right after
    the figure."""
    if a <= 0.004:
        return
    hd, R = np.asarray(J["head"], dtype=np.float64), float(J["R"])
    off = R * 0.10
    an = np.linspace(-1.15, 1.0, 14)
    P = np.stack([hd[0] + side * (R + off) * np.cos(an), hd[1] + (R + off) * np.sin(an)], axis=1)
    chalk(F, P, col, w, 0.95 * a, seed, wob=0.5, taper=0.25, edge=0.25)
    smudge(F, hd[0] + side * R * 0.9, hd[1], R * 1.0, R * 1.4, C.AMBER_GLOW, 0.26 * a, "glow", additive=True, power=1.5)

    def lit(*names):                                                    # of two limbs, the one toward the light
        best = max(names, key=lambda nm: side * float(J[nm][0]))
        return best[-1]

    q = lit("sh_f", "sh_b")
    sh, ha = np.asarray(J["sh_" + q], dtype=np.float64), np.asarray(J["ha_" + q], dtype=np.float64)
    chalk(F, np.stack([sh + (side * off * 1.6, 0.0), (sh + ha) / 2 + (side * off * 2.2, 0.0), ha + (side * off * 1.6, 0.0)]), col, w,
          0.85 * a, seed + 1, wob=0.5, taper=0.2, edge=0.25)
    q = lit("an_f", "an_b")
    pel, kn, ank = (np.asarray(J[nm], dtype=np.float64) for nm in ("pel", "kn_" + q, "an_" + q))
    chalk(F, np.stack([(pel + kn) / 2 + (side * off * 1.8, 0.0), kn + (side * off * 1.8, 0.0), ank + (side * off * 1.8, 0.0)]), col, w,
          0.8 * a, seed + 2, wob=0.5, taper=0.2, edge=0.25)


# --------------------------------------------------------------------------------------------------
# the tear: the dark sheet rips, the warm sheet shows
# --------------------------------------------------------------------------------------------------
def _rip(x0, y0, x1, y1, hw, seed, open_, n=54):
    """The two sides of a rip from (x0, y0) toward (x1, y1): arrays up, dn (n, 2), the unit normal
    (pointing from up to dn), the local half width (n) and the length torn so far."""
    op = min(1.0, max(0.0, float(open_)))
    L = math.hypot(x1 - x0, y1 - y0) + 1e-9
    tx, ty = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -ty, tx
    run = ease_out(min(1.0, op * 1.7), 1.6)                 # the rip runs ahead: it has reached the far end at open_ 0.6
    wid = 0.25 * op + 0.75 * op ** 1.6                      # and goes on widening behind its tip
    q = np.linspace(0.0, 1.0, n)
    qq = q * run                                            # the ragged detail belongs to the place, not to the tip
    k = hw / 92.0
    mid = 0.045 * L * (2.0 * vn(qq * 3.1, seed) - 1.0) * np.sin(np.pi * qq) ** 0.5
    prof = hw * wid * np.sin(np.pi * q) ** 0.6
    rag = np.minimum(1.0, prof / (30.0 * k))
    u = mid - prof * (0.7 + 0.6 * vn(qq * 6.3, seed + 1)) - 13.0 * k * rag * (2.0 * vn(qq * 31.0, seed + 2) - 1.0)
    d = mid + prof * (0.7 + 0.6 * vn(qq * 5.1, seed + 3)) + 13.0 * k * rag * (2.0 * vn(qq * 37.0, seed + 4) - 1.0)
    su = qq * L + 9.0 * k * rag * (2.0 * vn(qq * 29.0, seed + 5) - 1.0)
    sd_ = qq * L + 9.0 * k * rag * (2.0 * vn(qq * 33.0, seed + 6) - 1.0)
    up = np.stack([x0 + tx * su + nx * u, y0 + ty * su + ny * u], axis=1)
    dn = np.stack([x0 + tx * sd_ + nx * d, y0 + ty * sd_ + ny * d], axis=1)
    return up, dn, (nx, ny), prof, run * L


def rip_outline(x0, y0, x1, y1, hw: float = 92.0, seed: int = 5, open_: float = 1.0):
    """The closed world outline of a rip in the sheet that starts at (x0, y0) and runs to (x1, y1):
    a wandering gash, widest in the middle (half width about hw), with a ragged edge. open_: 0..1; the
    rip runs from its start to its far end over the first six tenths and widens all the way."""
    up, dn, _n, _p, _l = _rip(x0, y0, x1, y1, hw, seed, open_)
    return np.vstack([up, dn[::-1]])


_PAPER: list = []


def _warm_sheet(F: Frame) -> skia.Image:
    """The warm paper itself (the day skin's sheet, fixed to the screen), baked once."""
    if not _PAPER:
        G = F.sub("day")
        _PAPER.append(skia.Image.fromarray(G.surf.toarray(colorType=skia.kRGBA_8888_ColorType),
                                           colorType=skia.kRGBA_8888_ColorType, copy=True))
    return _PAPER[0]


RIM_COL = (0.47, 0.53, 0.70)             # the torn edge of dark sugar paper: its paler fibrous core


def tear(F: Frame, x0, y0, x1, y1, hw: float = 92.0, open_: float = 1.0, since: float | None = None, a: float = 1.0,
         seed: int = 5, light: float = 1.0, flash_a: float = 1.0):
    """The dark sheet rips open from the world point (x0, y0) to (x1, y1) and the warm sheet under it
    shows: the paper of the day skin itself, the shade of the upper sheet lying along its upper edge,
    torn edges with a pale fibrous rim, light spilling onto the dark sheet round it.

    open_: 0..1 (the storyboard: 0 to 1 in eight frames from 201.25: F.seg(201.25, 201.25 + 8 / 30)).
    since: seconds since the rip began (F.t - 201.25): drives the flash of pale light, which is
    strongest about three frames in and gone after a second (None: no flash). hw: half width of the
    gash at its middle. light: 0..1 the steady light round the opening; flash_a: scale of the flash.
    Night skin (on the day paper it draws nothing and returns the outline). The scraps are
    scraps(F, ...) with the same geometry; the shafts falling out of it are tear_shafts(F, ...).
    Returns the closed world outline (None while it is still shut)."""
    op = min(1.0, max(0.0, float(open_)))
    if op <= 0.004 or a <= 0.004:
        return None
    if F.day:
        return rip_outline(x0, y0, x1, y1, hw, seed, op)
    up, dn, (nx, ny), prof, Lr = _rip(x0, y0, x1, y1, hw, seed, op)
    P = np.vstack([up, dn[::-1]])
    L = math.hypot(x1 - x0, y1 - y0)
    k = hw / 92.0
    cam = F.cam
    cx, cy = float(P[:, 0].mean()), float(P[:, 1].mean())
    rot = math.atan2(y1 - y0, x1 - x0)
    fl = 0.0 if since is None else decay(since, 0.30) * min(1.0, op * 4.0) * flash_a
    c = F.c
    # light on the dark sheet round the opening, and the flash
    if light > 0.0:
        smudge(F, cx, cy, Lr * 0.62 + hw, hw * (1.6 + 1.6 * op), WARM, 0.24 * a * light * op, "glow", additive=True, power=1.5, rot=rot)
    if fl > 0.004:
        flash(F, 0.36 * fl * a, WARM, cx, cy, min(L * 1.25, 520.0 / cam.zoom))
    # the opening: the warm sheet, and on it the shade of the upper sheet's edge
    c.save()
    c.clipPath(F.path(P, True), skia.ClipOp.kIntersect, True)
    c.drawImage(_warm_sheet(F), 0, 0)
    c.drawPaint(F.paint((0.80, 0.70, 0.52), 0.36 * (1.0 - min(1.0, fl * 1.6)), None))
    ws = max(2.0, 15.0 * k * cam.zoom * (0.3 + 0.7 * op))
    c.drawPath(F.path(np.vstack([P, P[:1]]) + (2.5 * k, 6.0 * k)), F.pen((0.47, 0.38, 0.29), ws, 0.45, "soft"))
    if fl > 0.004:
        c.drawPaint(F.paint((1.0, 0.98, 0.92), min(1.0, 0.8 * fl), None))
    c.restore()
    # the torn edge of the dark sheet: a pale fibrous band on the dark side, hairs standing into the opening
    tx, ty = -ny, nx
    for sd_, S, sg in ((0, up, -1.0), (1, dn, 1.0)):
        q = np.linspace(0.0, 1.0, len(S))
        rw = (4.0 + 12.0 * vn(q * 9.0, seed + 20 + sd_) ** 1.4) * (0.6 + 0.8 * vn(q * 41.0, seed + 22 + sd_)) * k \
            * np.minimum(1.0, prof / (14.0 * k))
        out = S + np.stack([nx * sg * rw, ny * sg * rw], axis=1)
        band = np.vstack([S, out[::-1]])
        fill(F, band, RIM_COL, 0.55 * a, "mid")
        fill(F, band, mix(RIM_COL, C.CHALK_COOL, 0.4), 0.55 * a, "sparse")
        m = 90
        j = np.arange(m)
        u = htab(j, 7, seed * 31 + sd_ * 97)
        px, py = np.interp(u, q, S[:, 0]), np.interp(u, q, S[:, 1])
        pw = np.interp(u, q, prof)
        ang = (2.0 * htab(j, 11, seed * 37 + sd_ * 89) - 1.0) * 1.0
        ln = (3.0 + 11.0 * htab(j, 13, seed * 41 + sd_ * 83) ** 2) * k * np.minimum(1.0, pw / (12.0 * k))
        dx = (-sg * nx) * np.cos(ang) + tx * np.sin(ang)
        dy = (-sg * ny) * np.cos(ang) + ty * np.sin(ang)
        ax, ay = cam.to_screen(px - dx * ln * 0.3, py - dy * ln * 0.3)
        bx, by = cam.to_screen(px + dx * ln, py + dy * ln)
        p = skia.Path()
        for a_, b_, c_, d_ in zip(ax.tolist(), ay.tolist(), bx.tolist(), by.tolist()):
            p.moveTo(a_, b_)
            p.lineTo(c_, d_)
        wsf, alf = F.lw(1.6 * k, 0.8 * a, 1.0)
        c.drawPath(p, F.pen(mix(RIM_COL, C.CHALK_COOL, 0.25), wsf, alf, "mid"))
        chalk(F, S, mix(C.CHALK, WARM, 0.3), 2.8 * k, 0.9 * a, seed + 790 + sd_, wob=0.0, taper=0.3, edge=0.3, var=0.45, step=4.0,
              boil=0.0)
    return P


def tear_shafts(F: Frame, x0, y0, x1, y1, xa, xb, land: float = FLOOR + 40.0, hw: float = 92.0, open_: float = 1.0,
                a: float = 1.0, n: int = 8, seed: int = 0, pool: float = 1.0, col=None):
    """The broad pale shafts that fall out of the rip onto the land (201.25 on), and the light where
    they land: a fan from the middle of the opening (tear's x0, y0, x1, y1, hw, open_) down to the
    ground between world xa and xb at world y `land`. Its upper end always lies inside the opening,
    whichever way the rip runs, so that tear(), drawn AFTER it, hides where it begins. a: strength;
    pool: 0..1 the light on the ground. Draw it before the ground line and the figures. Night skin
    (nothing on the day paper)."""
    op = min(1.0, max(0.0, float(open_)))
    if op <= 0.004 or a <= 0.004 or F.day:
        return
    L = math.hypot(x1 - x0, y1 - y0) + 1e-9
    tx, ty = (x1 - x0) / L, (y1 - y0) / L
    run = ease_out(min(1.0, op * 1.7), 1.6)                 # as in _rip: how far it has run, how wide it stands
    wid = 0.25 * op + 0.75 * op ** 1.6
    cx, cy = x0 + tx * 0.5 * run * L, y0 + ty * 0.5 * run * L
    half = 0.5 * hw * wid * abs(ty) + 0.36 * run * L * abs(tx) + 2.0
    shafts(F, cx, half, cy, xa, xb, land, n, col, 0.19 * a * op, seed)
    if pool > 0.0:
        rx = 0.5 * abs(xb - xa)
        light_pool(F, 0.5 * (xa + xb), land - 10.0, rx, max(40.0, 0.08 * rx), col, 0.18 * a * op * pool)


def _scrap(seed: int, i: int, sz: float):
    """A torn scrap (local points, about sz from its middle to its edge): three or four corners in the
    large, a ragged torn edge in the small, longer one way than the other."""
    m = 13
    j = np.arange(m)
    sd = seed * 31 + i
    an = (j + 0.7 * (htab(j, 7, sd * 13 + 1) - 0.5)) * (2.0 * math.pi / m)
    big = 0.22 * np.cos(2.0 * an + 6.283 * rnd(sd, 301)) + 0.15 * np.cos(3.0 * an + 6.283 * rnd(sd, 304))
    rr = sz * (0.80 + big + 0.26 * (htab(j, 11, sd * 17 + 2) - 0.5))
    return np.stack([rr * np.cos(an), rr * np.sin(an) * (0.58 + 0.32 * rnd(sd, 302))], axis=1)


SCRAP_FACE = (0.19, 0.235, 0.36)         # a scrap's dark face (a little paler than the sheet, or it would not be seen)
SCRAP_BACK = (0.40, 0.46, 0.61)          # and its back, where no chalk dust ever came


def scraps(F: Frame, x0, y0, x1, y1, since: float, n: int = 16, hw: float = 92.0, seed: int = 5, ground: float = FLOOR,
           a: float = 1.0, size: float = 1.0, avoid=()):
    """Scraps of the dark sheet torn loose by the rip from (x0, y0) to (x1, y1) (tear's geometry):
    thrown clear as the rip passes, then falling the way paper falls, swaying, turning over and over
    (the dark face, the paler back, a pale torn edge all round), until they lie on the ground (world y
    `ground` and a little below it) and are rubbed away. since: seconds since the rip (F.t - 201.25;
    nothing before 0, all gone after about 7 s). n: how many; size: scale (most are small, a few as
    large as hw * 0.4 from middle to edge). avoid: world circles (x, y, r) the scraps slide round
    instead of crossing (the two faces: a scrap must not hide an eye at the film's turning point).
    Night skin (nothing on the day paper)."""
    if since <= 0.0 or a <= 0.004 or F.day:
        return
    L = math.hypot(x1 - x0, y1 - y0) + 1e-9
    tx, ty = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -ty, tx
    k = hw / 92.0
    tau = 0.34
    c = F.c
    edge_col = mix(RIM_COL, C.CHALK, 0.5)
    for i in range(int(n)):
        r_ = [rnd(seed * 17 + i, 200 + j) for j in range(14)]
        born = 0.02 + 0.22 * r_[0]                                    # they leave as the rip passes their place
        tt = since - born
        if tt <= 0.0:
            continue
        q = 0.08 + 0.84 * (0.6 * (born - 0.02) / 0.22 + 0.4 * r_[1])
        sg = 1.0 if r_[2] > 0.5 else -1.0
        px, py = x0 + tx * L * q + nx * sg * hw * 0.5, y0 + ty * L * q + ny * sg * hw * 0.5
        sp = (260.0 + 420.0 * r_[3]) * k
        vx = nx * sg * sp + tx * sp * 0.5 * (2.0 * r_[4] - 1.0)
        vy = ny * sg * sp + ty * sp * 0.5 * (2.0 * r_[4] - 1.0) - 150.0 * k * r_[5]
        vt = (150.0 + 130.0 * r_[6]) * k                              # the speed paper settles to
        gy = ground + 40.0 * k * r_[7] ** 2
        tl_ = max(0.4, (gy - py - (vy - vt) * tau) / vt)             # when it reaches the ground
        tf = min(tt, tl_)
        ef = 1.0 - math.exp(-tf / tau)
        fsw = 0.45 + 0.5 * r_[8]
        sway = (38.0 + 54.0 * r_[9]) * k
        x = px + vx * tau * ef + sway * (math.sin(6.283 * fsw * tf + 6.283 * r_[10]) - math.sin(6.283 * r_[10])) * min(1.0, tf / 0.5)
        y = py + vy * tau * ef + vt * (tf - tau * ef)
        if tt > tl_:
            y = gy
        rest = max(0.0, tt - tl_)
        fade = 1.0 - seg(rest, 1.0, 2.6)
        if fade <= 0.0:
            continue
        spin = 6.283 * (0.35 + 0.5 * r_[11]) * (1.0 if r_[12] > 0.5 else -1.0)
        rot = 6.283 * r_[12] + spin * tf + 0.6 * math.sin(6.283 * fsw * tf + 1.0)
        flip = math.cos(6.283 * (0.5 + 0.7 * r_[13]) * tf + 6.283 * r_[1])
        lie = ease(min(1.0, rest / 0.25))
        if lie > 0.0:                                                 # landed: it lies flat on the ground
            rot = rot * (1.0 - lie) + round(rot / math.pi) * math.pi * lie
            flip = flip + (math.copysign(1.0, flip) * 0.32 - flip) * lie
        sz = (10.0 + 30.0 * (r_[3] * r_[9]) ** 0.8 + 7.0 * r_[6]) * k * size     # many small, a few large
        for ax_, ay_, ar_ in avoid:                                     # slide round a face instead of crossing it
            reach = ar_ + sz * 0.9
            ddx, ddy = x - ax_, y - ay_
            d = math.hypot(ddx, ddy)
            if d < reach:                                               # carried out to the rim of the circle (continuous in time)
                if d < 1e-6:
                    ddx, ddy, d = sg, 0.0, 1.0
                q = reach * (0.86 + 0.14 * d / reach) / d
                x, y = ax_ + ddx * q, ay_ + ddy * q
        B = _scrap(seed, i, sz) * (1.0, max(0.16, abs(flip)))
        cr, sr = math.cos(rot), math.sin(rot)
        Pp = np.stack([x + B[:, 0] * cr - B[:, 1] * sr, y + B[:, 0] * sr + B[:, 1] * cr], axis=1)
        face = flip > 0.0
        al = a * fade * min(1.0, tt / 0.07)
        path = F.path(Pp, True)
        c.drawPath(path, F.paint(SCRAP_FACE if face else SCRAP_BACK, al, None))
        c.drawPath(path, F.paint(C.PAPER_DEEP if face else C.CHALK_COOL, (0.55 if face else 0.42) * al, "sparse"))   # its tooth
        ws, a2 = F.lw((2.6 if face else 1.8) * k * size, 0.9 * al, 1.2)
        c.drawPath(path, F.pen(edge_col if face else C.CHALK, ws, a2 * (0.85 if face else 0.6), "mid"))   # the torn edge, pale and fibrous


def flash(F: Frame, a: float, col=None, x=None, y=None, r: float | None = None):
    """Light for a hit: the whole sheet lit for an instant (a = 0..1; 0.25 is a clear flash, 0.6 a
    blinding one). With a world point (x, y) and a world radius r it comes from there (brightest
    there, still reaching the corners). The scene shapes it in time: flash(F, 0.3 * decay(F.t - T, 0.25))."""
    a = float(a)
    if a <= 0.004:
        return
    col = light_col(F) if col is None else col
    if F.day:
        F.c.drawPaint(F.paint(C.CREAM, min(1.0, a), None))
        return
    F.c.drawPaint(F.paint(col, min(1.0, 0.5 * a), None, skia.BlendMode.kPlus))
    if x is not None:
        r = 600.0 / F.cam.zoom if r is None else r
        smudge(F, x, y, r, r * 0.8, col, min(1.0, 0.8 * a), "glow", additive=True, power=1.4, inner=0.15)


# --------------------------------------------------------------------------------------------------
# shadows
# --------------------------------------------------------------------------------------------------
def ground_shadow(F: Frame, x, y, w, a: float = 0.5, day: bool | None = None):
    """A rubbed contact shadow under a figure: world centre (x, y) on the ground, half width w. Night:
    deep blue (never the scribble's black), a tighter heart under the feet. Day: violet-grey that
    darkens what it lies on (grass stays green under it, bare paper turns violet-grey)."""
    if a <= 0.004:
        return
    if F.day if day is None else day:
        _rub_shade(F, x, y + w * 0.05, w, w * 0.16, a * 0.62, 1.4)
        _rub_shade(F, x, y + w * 0.03, w * 0.5, w * 0.07, a * 0.50, 1.4)
    else:
        smudge(F, x, y + w * 0.05, w, w * 0.16, SHADE_NIGHT, a * 0.95, "soft", power=1.4)
        smudge(F, x, y + w * 0.03, w * 0.52, w * 0.075, SHADE_NIGHT, a * 0.6, "soft", power=1.5)


MULT = skia.BlendMode.kMultiply


def _tone(F: Frame, X, Y, al, idx, col, a: float, grain: str, blend):
    """core._shade with any blend mode (screen points X, Y; vertex strengths al)."""
    pts = [skia.Point(x_, y_) for x_, y_ in zip(X.tolist(), Y.tolist())]
    cols = [(int(v) << 24) | 0xFFFFFF for v in np.clip(al * 255.0 + 0.5, 0, 255).tolist()]
    F.c.drawVertices(skia.Vertices.MakeCopy(skia.Vertices.kTriangles_VertexMode, pts, None, cols, idx), F.paint(col, a, grain, blend),
                     skia.BlendMode.kSrcIn)


def _rub_shade(F: Frame, cx, cy, rx, ry, a: float, power: float = 1.4, col=C.SHADOW):
    """A day shadow rubbed on whatever is there: violet-grey pastel that darkens the ground under it
    (multiplied, so on grass it is a darker, cooler green and on bare paper a violet-grey)."""
    z = F.cam.zoom
    sx, sy = F.cam.to_screen(cx, cy)
    rx, ry = rx * z, ry * z
    if rx <= 0.5 or ry <= 0.5 or sx < -rx or sx > W + rx or sy < -ry or sy > H + ry:
        return
    ux, uy, al, idx = _disc(power, 0.0)
    _tone(F, sx + ux * rx, sy + uy * ry, al, idx, col, min(1.0, a), "soft" + WIDE, MULT)


def long_shadow(F: Frame, x, y, h, sun_x, a: float = 1.0, length: float = 2.0, fall: float = 0.20, lift: float = 0.0,
                curve=None, col=None, seed: int = 0, width: float = 1.0):
    """The long shadow a low sun lays behind a figure: from its ground point (x, y), away from the
    sun at world x = sun_x, `length` times its height h long, lying on the ground toward the viewer
    (fall: how much it drops per unit of length). A figure laid flat and drawn out: legs, a garment
    widest at its hem, the round of the head at its far end; softer and fainter toward its end, with
    a few loose strokes of the same crayon. By day it is C.SHADOW multiplied onto what it lies on (a
    darker, cooler green on the grass, violet-grey on the bare paper); on the night paper deep blue.

    It follows the figure: pass the figure's x, y, h every frame. lift: how high the feet are above
    the ground, in world units (a jump: the shadow lets go of the feet, slides away and pales).
    curve: the ground contour (function of world x arrays giving world y, as for ground_line): the
    shadow then follows the land loosely (0.6 of the contour's rise and fall: it lies on the slope in
    front of the contour line). width: scale of its thickness (a coat is wider than a jumper).
    col: another crayon (by day it is still multiplied)."""
    if a <= 0.004 or h <= 0.0:
        return
    sg = -1.0 if sun_x > x else 1.0
    Ls = h * length
    n = 25
    q = np.linspace(0.0, 1.0, n)
    start = lift * length
    sx = x + sg * (start + Ls * q)
    if curve is not None:                                             # it lies on the land in front of the contour, and follows it loosely
        base = y + 0.6 * (np.asarray(curve(sx), dtype=np.float64) - float(np.asarray(curve(np.array([float(x)])))[0]))
    else:
        base = np.full(n, float(y))
    sy = base + fall * (start + Ls * q) + 2.0
    # half thickness: the legs, the garment (widest at its hem), the neck, the round head (a figure laid flat and drawn out)
    body = np.interp(q, [0.0, 0.03, 0.34, 0.40, 0.62, 0.69], [0.012, 0.022, 0.025, 0.052, 0.036, 0.020])
    head = 0.066 * np.sqrt(np.clip(1.0 - ((q - 0.845) / 0.155) ** 2, 0.0, 1.0))
    wob = 1.0 + 0.12 * (2.0 * vn(q * 6.0 + seed, 77 + seed) - 1.0)
    prof = np.maximum(np.where(q <= 0.69, body, 0.0), head) * h * width * (1.15 + 0.45 * q) * wob
    al = 1.0 - 0.42 * q
    k = 1.0 / (1.0 + lift / (0.25 * h))
    day = F.day
    col = (C.SHADOW if day else SHADE_NIGHT) if col is None else col
    up = np.stack([sx, sy - prof], axis=1)
    dn = np.stack([sx, sy + prof], axis=1)
    Su, Sd = F.cam.pts(up), F.cam.pts(dn)
    if _off(np.vstack([Su, Sd]), 0.0):
        return
    e = (0.22 + 0.26 * q)[:, None]                                    # softer toward its end
    u = np.concatenate([e * _EDGE_U[None, :], 1.0 - e * _EDGE_U[None, ::-1]], axis=1)
    pa = np.concatenate([_EDGE_A, _EDGE_A[::-1]])
    X = Su[:, :1] + (Sd[:, :1] - Su[:, :1]) * u
    Y = Su[:, 1:] + (Sd[:, 1:] - Su[:, 1:]) * u
    # by day it darkens what it lies on (grass, bare paper); at night it is deep blue rubbed on the dark sheet
    _tone(F, X.ravel(), Y.ravel(), (al[:, None] * pa[None, :]).ravel(), _grid_idx(n, 6), col, min(1.0, (0.64 if day else 0.62) * a * k),
          "soft" + WIDE, MULT if day else None)
    poly = np.vstack([up, dn[::-1], up[:1]])
    hatch(F, poly, mix(col, C.PENCIL, 0.30) if day else col, math.atan2(fall * sg, 1.0) + 0.04, max(6.0, 0.024 * h), max(2.4, 0.010 * h),
          (0.14 if day else 0.30) * a * k, 900 + seed, grain="sparse", wob=0.5, clip=True, boil=False, jit=0.5, over=0.0)
