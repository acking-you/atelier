"""The film's look as pixel art: palette, the hope grade, banded skies with cumulus, mist, rain,
wind, light shafts, contact shadows, the wet-ground mirror and the colour ring.

Units: logical 1920x1080, seconds, colours (r, g, b) floats 0..1. Every helper is a pure function
of its arguments (time comes in as `t`, already stepped by the film); randomness from
prims.hash01. Drawing happens on the real pixel grid (hx/kit/_atm_px.py): hard edges, flat tones,
ordered stipple only where one tone meets another, whole-pixel motion. Light energy goes on
ctx.glow as before (soft is right there). See hx/kit/README.md for the API summary.
"""
from __future__ import annotations

import math
from contextlib import contextmanager
from functools import lru_cache

import numpy as np
import skia

from mv.engine import palette as P
from mv.engine import prims
from mv.engine.palette import hex_rgb, sk

from . import _atm_puffs as puffs
from ._atm_px import PX, Layer, line_px, null_canvas, quantize, rgb

# ---------------------------------------------------------------------------------------------
# palette
# ---------------------------------------------------------------------------------------------
INK, INDIGO, DUSK, SLATE = P.INK, P.INDIGO, P.DUSK, P.SLATE          # the gloom family
AMBER, PERSIMMON, ROSE, PAPER = P.AMBER, P.PERSIMMON, P.ROSE, P.PAPER  # the warm family
RAIN = P.RAIN

FOG_DEEP = hex_rgb("2A3140")      # fog in shadow, the plain at night
FOG = hex_rgb("5C6573")           # the body of the fog
FOG_PALE = hex_rgb("8D949C")      # lit fog tops, overcast sky
FOG_LIGHT = hex_rgb("B8BCBF")     # the brightest grey: a white-out, the sky through a hole

NIGHT_BLUE = hex_rgb("26304F")    # the cold night of the references (between INDIGO and DUSK)
COLD_LIGHT = hex_rgb("C9DAF2")    # a street lamp, a cold rim on a night cloud, a phone
WINDOW_WARM = hex_rgb("F4C77C")   # a lit window of another home
WINDOW_COLD = hex_rgb("8FA6CF")   # a window lit by a screen
SUN_GOLD = hex_rgb("FFE3A3")      # the lit rim of a cloud at sunset

MEADOW = hex_rgb("6FA35A")        # the late colours (after line 62)
MEADOW_DEEP = hex_rgb("3F7448")
MEADOW_LIGHT = hex_rgb("A9C96E")
SKY_BLUE = hex_rgb("7FB2DA")
SKY_DEEP = hex_rgb("4C83BD")
PEACH = hex_rgb("F6C7A0")
CREAM_CLOUD = hex_rgb("F5ECDD")
ROOF_RED = hex_rgb("C2553F")
ROOF_BLUE = hex_rgb("4F6FA0")
ROOF_OCHRE = hex_rgb("D49A45")
TEAL = hex_rgb("2F7F7C")          # the child's hoodie when colour floods in
FLOWER_RED = hex_rgb("E2584A")
FLOWER_YELLOW = hex_rgb("F4D25A")
FLOWER_WHITE = hex_rgb("F3EEE4")
FLOWER_VIOLET = hex_rgb("8F6BB8")
FLOWER_PINK = hex_rgb("EE9AB0")
FLOWERS = (FLOWER_RED, FLOWER_YELLOW, FLOWER_WHITE, FLOWER_VIOLET, FLOWER_PINK)

W, H = 1920, 1080
H01, HS = prims.hash01, prims.hash_sym


def _ss(a, b, x):
    u = min(1.0, max(0.0, (x - a) / (b - a)))
    return u * u * (3.0 - 2.0 * u)


def _snap(v):
    return round(v / PX) * PX


# ---------------------------------------------------------------------------------------------
# the grade
# ---------------------------------------------------------------------------------------------
COLD_HI = (0.68, 0.78, 1.0)       # where white goes at hope 0: a pale cold periwinkle
COLD_LIFT = 1.10                  # the cold world is lifted a little so its mids stay blue, not murky


def sat_for(hope: float) -> float:
    """Share of the true colour kept by the grade: 0.12 at hope 0, 1 at hope 1 (slow at first)."""
    return 0.12 + 0.88 * _ss(0.0, 1.0, float(hope)) ** 1.15


def cool_for(hope: float) -> float:
    """Strength 0..1 of the cold cast: 1 at hope 0, gone by hope 0.9."""
    return 1.0 - _ss(0.0, 0.9, float(hope))


_LUMA = np.array([0.2126, 0.7152, 0.0722])
_INK = np.array(INK)


def grade_filter(sat: float, cool: float) -> skia.ColorFilter | None:
    """Colour-matrix filter. The cold world: every colour goes to its luma placed on the line from
    INK to COLD_HI, lifted by COLD_LIFT (an indigo-and-slate monochrome that keeps its blue: mid
    grey lands on #63718F, white on #C5DDFF, amber on #A3B1D3), keeping `sat` of its own colour.
    `cool` blends between that and a plain luma drain to `sat` (so colours return as hope rises).
    INK maps to INK; (1, 0) is the identity."""
    if sat >= 0.999 and cool <= 0.001:
        return None
    one = np.ones(3)
    drain = sat * np.eye(3) + (1.0 - sat) * np.outer(one, _LUMA)
    y_ink = float(_LUMA @ _INK)
    span = COLD_LIFT * (np.array(COLD_HI) - _INK) / (1.0 - y_ink)
    tint_m = np.outer(span, _LUMA)                         # x -> INK + span * (Y(x) - Y(ink))
    tint_off = _INK - span * y_ink
    cold_m = sat * np.eye(3) + (1.0 - sat) * tint_m
    cold_off = (1.0 - sat) * tint_off
    m = (1.0 - cool) * drain + cool * cold_m
    off = cool * cold_off
    off = off + (_INK - (m @ _INK + off))                  # ink stays ink exactly
    rows = []
    for i in range(3):
        rows += [float(m[i, 0]), float(m[i, 1]), float(m[i, 2]), 0.0, float(off[i])]
    rows += [0.0, 0.0, 0.0, 1.0, 0.0]
    return skia.ColorFilters.Matrix(rows)


@contextmanager
def graded(ctx, sat: float | None = None, cool: float | None = None, bounds=None):
    """Everything drawn on ctx.canvas inside the block is graded as one layer. Defaults follow
    ctx.hope. bounds (l, t, r, b) limits the layer (cheaper). About 5 ms full frame, 0 at hope 1."""
    s = sat_for(ctx.hope) if sat is None else sat
    c = cool_for(ctx.hope) if cool is None else cool
    f = grade_filter(s, c)
    if f is None:
        yield
        return
    p = skia.Paint()
    p.setColorFilter(f)
    canvas = ctx.canvas
    n = canvas.getSaveCount()
    canvas.saveLayer(skia.Rect.MakeLTRB(*bounds) if bounds else None, p)
    try:
        yield
    finally:
        canvas.restoreToCount(n)


def reveal(ctx, draw_fn, cx: float, cy: float, radius: float, soft: float = 60.0, sat=None, cool=None):
    """The colour ring: draw_fn() paints the world on ctx.canvas twice, graded outside and true
    colour inside the disc of `radius` around (cx, cy). The ring's edge is an ordered stipple
    `soft` units wide on the pixel grid. Call draw_fn for the glow separately. Cost: two world
    draws + about 3 ms; once the disc covers the frame the world is drawn once."""
    corners = max(math.hypot(cx - x, cy - y) for x in (0, W) for y in (0, H))
    if radius - soft >= corners:
        draw_fn()
        return
    with graded(ctx, sat, cool):
        draw_fn()
    if radius <= 1.0:
        return
    canvas = ctx.canvas
    l, t, r, b = max(0.0, cx - radius), max(0.0, cy - radius), min(W, cx + radius), min(H, cy + radius)
    if r <= l or b <= t:
        return
    box = skia.Rect.MakeLTRB(l, t, r, b)
    n = canvas.getSaveCount()
    canvas.save()
    canvas.clipRect(box)
    canvas.saveLayer(box, None)
    draw_fn()
    L = Layer(canvas, (l, t, r, b))
    if not L.empty:
        X, Y = L.local_grid()
        d = np.hypot(X - cx, Y - cy)
        cov = np.clip((radius - d) / max(1.0, soft), 0.0, 1.0)
        L.a[:] = (cov > L.bayer).astype(np.float32)
        L.rgb[:] = L.a[..., None]
        L.blit(canvas, blend=skia.BlendMode.kDstIn, crop=False)
    canvas.restoreToCount(n)


# ---------------------------------------------------------------------------------------------
# skies
# ---------------------------------------------------------------------------------------------
SKY_POS = (0.0, 0.3, 0.6, 0.85, 1.0)
SKIES = {   # top .. horizon, five stops each
    "night":     [hex_rgb(h) for h in ("141B2E", "1B2440", "222D4E", "2B3759", "34406B")],
    "overcast":  [hex_rgb(h) for h in ("4A515E", "5A616D", "6B727C", "7C828A", "878C92")],
    "lid":       [hex_rgb(h) for h in ("1E2536", "2C3447", "424A5C", "6A6E78", "9A8F86")],
    "sunset":    [hex_rgb(h) for h in ("3D3F6E", "7A5378", "C7566B", "F0834D", "F7C873")],
    "day":       [hex_rgb(h) for h in ("4C83BD", "6E9FD0", "93BBDD", "C9D3D6", "F6C7A0")],
    "golden":    [hex_rgb(h) for h in ("6C82B0", "B0A2A8", "E9B88E", "F4C37E", "F7D9A0")],
    # added for the references
    "rain_night": [hex_rgb(h) for h in ("232B47", "2E3858", "3B4769", "4C5A7E", "5E6C92")],  # p1a_street, v1a
    "rain_dusk":  [hex_rgb(h) for h in ("232B47", "34406B", "53597E", "7A6E8A", "9C8794")],  # inter, a wet evening
    "storm":      [hex_rgb(h) for h in ("12172A", "1A2135", "262E44", "343C52", "474E62")],  # c2a under the lid
    "blue":       [hex_rgb(h) for h in ("2F63B0", "4C83C8", "78A8DC", "A9CCEA", "DCEAF2")],  # out, c3b: deep Shinkai blue
}


def sky_colors(mood):
    """mood: a name from SKIES, or {name: weight} / [(name, weight), ...] to blend (OKLab)."""
    if isinstance(mood, str):
        return SKIES[mood]
    items = list(mood.items()) if isinstance(mood, dict) else list(mood)
    tot = sum(max(0.0, w) for _, w in items) or 1.0
    lab = sum(P.to_oklab(np.array(SKIES[n])) * (max(0.0, w) / tot) for n, w in items)
    return [tuple(float(v) for v in row) for row in P.from_oklab(lab)]


def _sky_bands(cols, positions, nb):
    lab = P.to_oklab(np.array(cols, np.float64))
    u = (np.arange(nb) + 0.5) / nb
    out = np.stack([np.interp(u, positions, lab[:, i]) for i in range(3)], 1)
    return P.from_oklab(out).astype(np.float32)


def sky(canvas, rect, mood, positions=SKY_POS, bands: int | None = None, zone: float = 2.5):
    """Opaque banded sky over rect (l, t, r, b), top to bottom: flat horizontal bands, each meeting
    the next across an ordered stipple about `zone` pixels tall. `bands` defaults to one per
    visible step of lightness (6 to 22). About 1.5 ms full frame."""
    L = Layer(canvas, rect)
    if L.empty:
        return
    cols = sky_colors(mood)
    l, t, r, b = rect
    if bands is None:
        lab = P.to_oklab(np.array(cols, np.float64))
        dist = float(np.sum(np.linalg.norm(np.diff(lab, axis=0), axis=1)))
        bands = int(np.clip(round(dist / 0.028), 6, 22))
    pal = _sky_bands(cols, positions, bands)
    band_px = max(1.0, L.px_len(b - t) / bands)
    m = L.m
    if abs(m.getSkewX()) < 1e-9 and abs(m.getSkewY()) < 1e-9:
        # axis-aligned (the usual case): the band index depends only on the row and x mod 4
        jj = (np.arange(L.h) + L.iy0 + 0.5) * PX
        ii = (np.arange(L.w) + L.ix0 + 0.5) * PX
        yrow = (jj - m.getTranslateY()) / m.getScaleY()
        xcol = (ii - m.getTranslateX()) / m.getScaleX()
        s = np.clip((yrow - t) / max(1e-6, b - t), 0.0, 0.9999)[:, None]
        bay = L.bayer[:, :4] if L.w >= 4 else L.bayer
        idx4 = quantize(np.broadcast_to(s, (L.h, bay.shape[1])), bands, bay, min(0.9, zone / band_px))
        reps = -(-L.w // bay.shape[1])
        idx = np.tile(idx4, (1, reps))[:, :L.w]
        inside = ((xcol >= l) & (xcol < r))[None, :] & ((yrow >= t) & (yrow < b))[:, None]
    else:
        X, Y = L.local_grid()
        s = np.clip((Y - t) / max(1e-6, b - t), 0.0, 0.9999)
        idx = quantize(s, bands, L.bayer, min(0.9, zone / band_px))
        inside = (X >= l) & (X < r) & (Y >= t) & (Y < b)
    L.a[:] = inside
    L.rgb[:] = pal[idx] * L.a[..., None]
    L.blit(canvas)


def sun_disc(ctx, x: float, y: float, r: float, color=PERSIMMON, halo: float = 2.2, alpha: float = 1.0,
             core=None, glow: float = 0.8, canvas=None):
    """A low sun: a hard disc of radius r, a hotter core, and two flat halo rings out to
    `halo` * r meeting across ordered stipple; its energy on ctx.glow."""
    canvas = ctx.canvas if canvas is None else canvas
    rr = r * halo
    L = Layer(canvas, (x - rr, y - rr, x + rr, y + rr))
    if not L.empty:
        X, Y = L.local_grid()
        d = np.hypot(X - x, Y - y) / max(1.0, r)
        core = P.mix(color, PAPER, 0.55) if core is None else core
        f = np.clip((halo - d) / max(0.01, halo - 1.0), 0.0, 1.0)          # 1 at the disc, 0 at the halo's edge
        ring = quantize(f, 3, L.bayer, 0.7)
        for k, a in ((1, 0.16), (2, 0.32)):
            L.fill((ring >= k) & (d >= 1.0), color, a * alpha)
        L.fill(d < 1.0, color, alpha)
        L.fill(d < 0.62, core, alpha)
        L.blit(canvas)
    if glow > 0 and getattr(ctx, "glow", None) is not None:
        prims.glow(ctx.glow, x, y, rr * 1.4, color, glow * alpha * 0.6)


# ---------------------------------------------------------------------------------------------
# cumulus: towering hard-edged clouds in flat tones
# ---------------------------------------------------------------------------------------------
CUMULUS = {   # dark (base, shadow) .. light (lit tops), then the rim
    "day":     ([hex_rgb(h) for h in ("8496BC", "AEBCDA", "DCE4F0", "F8F6F0")], hex_rgb("FFFFFF")),
    "blue":    ([hex_rgb(h) for h in ("7C93C6", "A9BEE2", "E0E9F4", "FFFFFF")], hex_rgb("FFFFFF")),
    "sunset":  ([hex_rgb(h) for h in ("5E4673", "9A5C7E", "E0806E", "F9BE86")], SUN_GOLD),
    "golden":  ([hex_rgb(h) for h in ("857CA0", "C39C9E", "EEBF90", "FDDFAA")], hex_rgb("FFF3D2")),
    "night":   ([hex_rgb(h) for h in ("232B48", "313C62", "44527E", "5D6C9A")], hex_rgb("B7CDF0")),
    "overcast": ([hex_rgb(h) for h in ("3C4458", "4B5468", "5E677B", "747D90")], hex_rgb("97A0B2")),
}


def cumulus_tones(mood):
    """(tones dark..light, rim) for a mood name or {name: weight} (OKLab blend)."""
    if isinstance(mood, str):
        return [tuple(c) for c in CUMULUS[mood][0]], tuple(CUMULUS[mood][1])
    items = list(mood.items()) if isinstance(mood, dict) else list(mood)
    tot = sum(max(0.0, w) for _, w in items) or 1.0
    lab = sum(P.to_oklab(np.array(CUMULUS[n][0] + [CUMULUS[n][1]])) * (max(0.0, w) / tot) for n, w in items)
    cols = [tuple(float(v) for v in row) for row in P.from_oklab(lab)]
    return cols[:4], cols[4]


@lru_cache(maxsize=4096)
def _profile_consts(seed):
    return tuple(float(H01(seed, k)) for k in range(1, 6))


def _cumulus_profile(u, seed, tower):
    """Height 0..1 of a cloud's top across u 0..1: a tower and two shoulders (max of bumps)."""
    h1, h2, h3, h4, h5 = _profile_consts(int(seed))
    c1 = 0.32 + 0.36 * h1
    s1 = 0.16 + 0.10 * (1.0 - tower)
    c2, c3 = c1 - 0.22 - 0.1 * h2, c1 + 0.22 + 0.1 * h3
    b1 = np.exp(-((u - c1) / s1) ** 2)
    b2 = (0.45 + 0.2 * h4) * np.exp(-((u - c2) / 0.2) ** 2)
    b3 = (0.40 + 0.25 * h5) * np.exp(-((u - c3) / 0.2) ** 2)
    edge = np.clip(np.minimum(u, 1 - u) / 0.12, 0, 1)
    return np.maximum(b1, np.maximum(b2, b3)) * (0.35 + 0.65 * edge)


def _cumulus_puffs(x, base, w, h, t, seed, tower, billow):
    """Puffs (local units) for one cloud: a ring of lumps along its top profile (bigger on the
    tower, smaller toward the ends, irregular in size and spacing), a row along the flat base,
    and big puffs filling the body behind them."""
    # lumps along the profile
    n = int(10 + 8 * tower + w / max(1.0, h) * 4)
    k = np.arange(n)
    key = seed * 977 + k
    u = np.clip((k + 0.5 + 0.7 * HS(key, 2)) / n, 0.02, 0.98)
    prof = _cumulus_profile(u, seed, tower)
    rr = h * (0.07 + 0.13 * prof) * (0.7 + 0.6 * H01(key, 3))
    xs = x - w / 2 + u * w
    ys = base - prof * h + rr * (0.85 + 0.25 * H01(key, 6))
    zs = rr * (0.3 + 0.4 * H01(key, 7)) + h * 0.3
    # the base row and the body
    m = max(3, int(w / (h * 0.30)))
    bk = seed * 977 + 300 + np.arange(m)
    bu = (np.arange(m) + 0.5 + 0.4 * HS(bk, 8)) / m
    bp = _cumulus_profile(bu, seed, tower)
    br = h * (0.10 + 0.14 * bp) * (0.8 + 0.4 * H01(bk, 9))
    bx = x - w / 2 + bu * w
    by = base - br * 0.55
    bz = br * 0.5 + h * 0.2
    q = max(3, int(w / (h * 0.35)))
    fk = seed * 977 + 600 + np.arange(2 * q)
    fu = (np.arange(2 * q) % q + 0.5 + 0.3 * HS(fk, 10)) / q
    fp = _cumulus_profile(fu, seed, tower)
    fr = h * (0.12 + 0.2 * fp)
    fx_ = x - w / 2 + fu * w
    fy = base - fp * h * np.where(np.arange(2 * q) < q, 0.35, 0.62) - fr * 0.1
    fz = np.zeros(2 * q)
    xs, ys, rr, zs = np.r_[xs, bx, fx_], np.r_[ys, by, fy], np.r_[rr, br, fr], np.r_[zs, bz, fz]
    ids = seed * 977 + 900 + np.arange(len(xs))
    ph = 6.283 * H01(ids, 4)
    per = 9.0 + 8.0 * H01(ids, 5)
    xs = xs + billow * rr * 0.08 * np.sin(6.283 * t / per + ph)
    ys = ys - billow * rr * 0.06 * (1 + np.sin(4.4 * t / per + ph))
    return xs, ys, rr, zs


def _cumulus_layer(canvas, box, clouds, t, sun, tones, rim, alpha, billow, rim_w=1):
    """Render clouds [(x, base, w, h, seed, tower, z)] into one pixel layer: one depth buffer,
    so nearer clouds (bigger z) stand in front with a lit rim along their edge."""
    L = Layer(canvas, box)
    if L.empty:
        return
    parts = [_cumulus_puffs(x, b, w, h, t, sd, tw, billow) for (x, b, w, h, sd, tw, z) in clouds]
    cid = np.concatenate([np.full(len(p[0]), i) for i, p in enumerate(parts)])
    xs, ys, rs, zs = (np.concatenate([p[k] for p in parts]) for k in range(4))
    zs = zs + np.array([c[6] for c in clouds])[cid]
    fx, fy = L.to_px(xs, ys)
    Z, NX, NY, NZ, ID = puffs.raster(L, fx, fy, L.px_len(rs), L.px_len(zs), 0.86)
    xb = np.array([c[0] for c in clouds])
    _, brow = L.to_px(xb, np.array([c[1] for c in clouds]))
    _, trow = L.to_px(xb, np.array([c[1] - c[3] for c in clouds]))
    brow = np.round(brow)
    cl = cid[np.maximum(ID, 0)]
    yy = np.arange(L.h, dtype=np.float32)[:, None]
    Z[(ID >= 0) & (yy >= brow[cl])] = -1e9                           # flat bases
    f = np.clip((yy - trow[cl]) / np.maximum(1.0, brow[cl] - trow[cl]), 0.0, 1.0)
    vadd = 0.12 - 0.34 * f - 0.22 * np.clip((yy - (brow[cl] - 4)) / 4.0, 0.0, 1.0)
    sm = int(np.clip(np.median(L.px_len(np.array([c[3] for c in clouds]))) * 0.12, 2, 10))
    mask, idx = puffs.shade(L, Z, NX, NY, NZ, len(tones), light=sun, lz=0.6, ambient=vadd, cast=0.4,
                            cast_len=3, smooth=sm, local=0.45, dither=0.3)
    rr = puffs.rims(Z, mask, sun, inner=4.0, width=rim_w)
    puffs.paint(L, mask, idx, tones, rr, rim, alpha)
    L.blit(canvas)


def cumulus(canvas, x: float, base: float, w: float, h: float, t: float = 0.0, seed: int = 0, mood="day",
            sun=(-0.6, -0.75), drift: float = 0.0, alpha: float = 1.0, tower: float = 0.5, tones=None,
            rim=None, billow: float = 1.0, cut=None, rim_width: int = 1):
    """One towering cumulus standing on the flat base line `base`, centred on x, w wide and h tall
    (local units). Four flat tones (`mood` from CUMULUS or `tones` dark..light), lit from `sun`
    (screen direction toward the light): the whole mass is lit as one form, its lumps cast
    scalloped shadows on one another, a one-pixel lit rim runs along the sun side of the
    silhouette and of each lump standing in front, the flat base is darker. `drift` units/s moves
    it sideways in whole pixels; lumps billow slowly (`billow` 0 = still). `cut` = (l, t, r, b)
    local box it is limited to; `rim_width` 2 for the bright night rims. 2 to 5 ms per cloud."""
    tn, rc = cumulus_tones(mood)
    dx = _snap(drift * t)
    box = (x + dx - w * 0.6, base - h * 1.05, x + dx + w * 0.6, base + PX)
    if cut is not None:
        box = (max(box[0], cut[0]), max(box[1], cut[1]), min(box[2], cut[2]), min(box[3], cut[3]))
        if box[2] <= box[0] or box[3] <= box[1]:
            return
    _cumulus_layer(canvas, box, [(x + dx, base, w, h, seed, tower, 0.0)], t, sun, tn if tones is None else tones,
                   rc if rim is None else rim, alpha, billow, rim_width)


def cumulus_bank(canvas, rect, t: float = 0.0, mood="day", seed: int = 0, n: int = 5, sun=(-0.6, -0.75),
                 drift: float = 6.0, alpha: float = 1.0, tower: float = 0.5, layers: int = 2, tones=None, rim=None,
                 rim_width: int = 1):
    """A row of cumulus standing on the bottom edge of rect (l, t, r, b), drawn as one layer:
    far ones smaller, lower and slower (parallax drift in whole pixels), near ones in front."""
    l, tp, r, b = rect
    clouds = []
    for li in range(layers):
        f = li / max(1, layers - 1) if layers > 1 else 1.0
        k = max(1, int(round(n * (1.3 - 0.5 * f))))
        hh = (b - tp) * (0.45 + 0.55 * f)
        for i in range(k):
            key = seed * 101 + li * 17 + i
            u = (i + 0.5 + 0.6 * HS(key, 11)) / k
            ww = (r - l) / k * (1.1 + 0.5 * H01(key, 12))
            hi = hh * (0.55 + 0.45 * H01(key, 13))
            span = (r - l) + ww
            xx = l - ww / 2 + ((u * (r - l) + ww / 2 + _snap(drift * (0.4 + 0.6 * f) * t)) % span)
            clouds.append((xx, b - (1 - f) * (b - tp) * 0.08, ww, hi, key, tower * (0.6 + 0.4 * f), 1000.0 * li))
    tn, rc = cumulus_tones(mood)
    clouds.sort(key=lambda c: c[6])
    _cumulus_layer(canvas, rect, clouds, t, sun, tn if tones is None else tones, rc if rim is None else rim,
                   alpha, 1.0, rim_width)


# ---------------------------------------------------------------------------------------------
# contact shadow
# ---------------------------------------------------------------------------------------------
def shadow(canvas, x: float, y: float, w: float, alpha: float = 0.55, color=INK, squash: float = 1.0,
           stipple: bool = True):
    """Flat contact shadow centred at (x, y), `w` wide: a hard ellipse at least one pixel tall
    and, if stipple, a ring a quarter wider at half strength in an ordered stipple."""
    rx = w * 0.5
    ry = max(PX * 0.75, w * 0.06 * max(0.3, squash))
    ro = 1.25 if stipple else 1.0
    L = Layer(canvas, (x - rx * ro, y - ry * ro - PX, x + rx * ro, y + ry * ro + PX))
    if L.empty:
        return
    X, Y = L.local_grid()
    d = np.hypot((X - x) / rx, (Y - y) / ry)
    if stipple:
        L.fill((d < ro) & (d >= 1.0) & (L.bayer < 0.5), color, alpha * 0.6)
    L.fill(d < 1.0, color, alpha)
    L.blit(canvas)


# ---------------------------------------------------------------------------------------------
# light shaft
# ---------------------------------------------------------------------------------------------
def shaft(ctx, x0: float, y0: float, x1: float, y1: float, w0: float, w1: float, color=AMBER,
          alpha: float = 0.35, dust: float = 1.0, t: float | None = None, seed: int = 0, glow: float = 0.6,
          core: float = 0.35, canvas=None):
    """A flat translucent wedge of light from (x0, y0) (top, width w0) to its foot (x1, y1)
    (width w1), screen-blended: hard edges, a brighter core band `core` of its width, an ordered
    stipple where it begins and ends; dust as single pixels drifting inside it; energy on glow."""
    t = ctx.t if t is None else t
    canvas = ctx.canvas if canvas is None else canvas
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    quad = [(x0 - nx * w0 / 2, y0 - ny * w0 / 2), (x0 + nx * w0 / 2, y0 + ny * w0 / 2),
            (x1 + nx * w1 / 2, y1 + ny * w1 / 2), (x1 - nx * w1 / 2, y1 - ny * w1 / 2)]
    qx, qy = [q[0] for q in quad], [q[1] for q in quad]
    L = Layer(canvas, (min(qx), min(qy), max(qx), max(qy)))
    if not L.empty and alpha > 0.004:
        X, Y = L.local_grid()
        v = ((X - x0) * dx + (Y - y0) * dy) / (ln * ln)
        half = 0.5 * (w0 + (w1 - w0) * np.clip(v, 0, 1))
        u = ((X - x0) * nx + (Y - y0) * ny) / np.maximum(1.0, half)
        au = np.abs(u)
        inside = (v >= 0) & (v <= 1) & (au <= 1.0)
        cov = np.clip(v / 0.18, 0, 1) * np.clip((1.0 - v) / 0.05, 0, 1)         # stippled ends
        on = inside & (cov > L.bayer)
        a = np.where(au < core, alpha * 1.7, alpha)
        L.fill(on, color, np.minimum(1.0, a))
        L.blit(canvas, blend=skia.BlendMode.kScreen)
    g = getattr(ctx, "glow", None)
    if glow > 0 and g is not None and alpha > 0.004:
        path = prims.poly_path(qx, qy, close=True)
        p = skia.Paint(AntiAlias=True, Color=sk(color, alpha * glow * 0.6), BlendMode=skia.BlendMode.kPlus)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(4.0, 0.15 * min(w0, w1))))
        g.drawPath(path, p)
    if dust > 0.0 and not L.empty:
        n = int(18 + ln * 0.03 * dust)
        ids = np.arange(n) + seed * 7919
        vv = (H01(ids, 1) + t * (0.010 + 0.02 * H01(ids, 2))) % 1.0
        uu = HS(ids, 3) * 0.8
        ww = w0 + (w1 - w0) * vv
        xs = x0 + dx * vv + nx * uu * ww / 2
        ys = y0 + dy * vv + ny * uu * ww / 2
        tw = 0.5 + 0.5 * np.sin(t * (1.1 + 2.0 * H01(ids, 5)) + 6.283 * H01(ids, 6))
        on = (tw > 0.35) & (vv > 0.1)
        D = Layer(canvas, (min(qx), min(qy), max(qx), max(qy)))
        ix, iy = D.to_ipx(xs[on], ys[on])
        D.put(ix, iy, P.mix(color, PAPER, 0.6), np.minimum(1.0, alpha * 2.2 * (0.4 + 0.6 * tw[on])) * dust)
        D.blit(canvas)


# ---------------------------------------------------------------------------------------------
# wind streaks
# ---------------------------------------------------------------------------------------------
def wind(canvas, rect, t: float, strength: float = 1.0, angle: float = -8.0, seed: int = 0,
         color=FOG_LIGHT, n: int = 80, speed: float = 1500.0, alpha: float = 0.55):
    """One-pixel wind streaks over rect, 4 to 30 pixels long, travelling along `angle` degrees
    (0 = to the right, negative tilts up); strength 0..1 scales count, length and alpha (pulse it
    on beats). Two strengths of alpha only."""
    if strength <= 0.01:
        return
    L = Layer(canvas, rect, sparse=True)
    if L.empty:
        return
    l, tp, r, b = rect
    life = 0.9
    ids, age = prims.emitter(t, n / life, life, id0=seed * 100003, max_n=600)
    keep = H01(ids, 21) < 0.25 + 0.75 * strength
    ids, age = ids[keep], age[keep]
    if not len(ids):
        return
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    span = (r - l) + 600.0
    sp = speed * (0.6 + 0.8 * H01(ids, 22))
    sx = l - 300.0 + H01(ids, 23) * span - ca * 0.5 * speed * life
    sy = tp + H01(ids, 24) * (b - tp)
    hx = sx + ca * sp * age
    hy = sy + sa * sp * age + 12.0 * np.sin(age * 5.0 + ids)
    ln = (20.0 + 130.0 * H01(ids, 25) ** 2) * (0.5 + 0.5 * strength)
    env = np.sin(np.pi * np.clip(age / life, 0, 1))
    al = alpha * strength * (0.6 + 0.4 * H01(ids, 26))
    al = np.where(env > 0.55, al, al * 0.5)
    hix, hiy = L.to_ipx(hx, hy)
    npx = np.maximum(2, np.round(L.px_len(ln))).astype(np.int64)
    slope = -sa / max(0.2, ca)                  # rows per column, walking back from the head
    ix, iy, k, idx = line_px(hix, hiy, -1.0, slope, npx)
    tail = k > npx[idx] * 0.6
    L.put(ix, iy, color, np.where(tail, al[idx] * 0.55, al[idx]))
    L.blit(canvas)


# ---------------------------------------------------------------------------------------------
# mist
# ---------------------------------------------------------------------------------------------
def _noise_px(u, seed):
    return (prims.value_noise(u, seed) - 0.5) + 0.5 * (prims.value_noise(u * 2.3, seed + 7) - 0.5) \
        + 0.25 * (prims.value_noise(u * 5.1, seed + 13) - 0.5)


def fog_band(canvas, rect, t: float, density: float = 1.0, color=FOG, speed: float = 20.0, seed: int = 0,
             alpha: float = 0.6, size: float = 1.0):
    """Mist as flat translucent strata filling rect (l, t, r, b): a gently lumpy top whose edge is
    two pixels of ordered stipple, a dense core, and a foot that steps down in two thinner strata
    (stippled between). Scrolls at `speed` units/s in whole pixels. density 0..1 thins it and
    lowers its top. size scales the lumps along x. About 1 ms for a full-width band."""
    if density <= 0.01 or alpha <= 0.004:
        return
    L = Layer(canvas, rect)
    if L.empty:
        return
    l, tp, r, b = rect
    _, ty = L.to_px(np.array([l]), np.array([tp]))
    _, byy = L.to_px(np.array([l]), np.array([b]))
    top0, bot = float(ty[0]), float(byy[0])
    hpx = max(2.0, bot - top0)
    off = int(math.floor(speed * t / PX * L.s))                       # whole pixels
    cols = np.arange(L.w) + L.ix0 + off
    lump = 38.0 * size
    edge = top0 + hpx * (0.08 + 0.22 * (1.0 - density) + 0.26 * (_noise_px(cols / lump + seed * 13.1, seed) + 0.5))
    edge = np.round(edge)
    yy = np.arange(L.h, dtype=np.float32)[:, None]
    d = (yy - edge[None, :]) / hpx                                    # 0 at the top edge
    # strata: 1 in the core, 0.6 then 0.3 toward the foot, 0 below
    f = np.where(d < 0.45, 1.0, np.where(d < 0.68, 0.62, np.where(d < 0.88, 0.32, 0.0)))
    # stipple: the top edge over two pixels, and between strata
    top = (yy - edge[None, :])
    cov_top = np.clip((top + 2.0) / 2.5, 0.0, 1.0)
    f = np.where(top < 0.5, np.where(cov_top > L.bayer, 0.55, 0.0), f)
    for d0, hi, lo in ((0.45, 1.0, 0.62), (0.68, 0.62, 0.32), (0.88, 0.32, 0.0)):
        z = np.abs(d - d0) * hpx < 1.5
        f = np.where(z, np.where(L.bayer < 0.5, hi, lo), f)
    f = np.where((yy < 0) | (yy >= bot), 0.0, f)
    L.fill(f > 0, color, (alpha * min(1.0, density ** 0.8)) * f)
    L.blit(canvas)


def fog_bank(canvas, rect, t: float, density: float = 1.0, colors=(FOG_DEEP, FOG, FOG_PALE),
             speeds=(8.0, 16.0, 30.0), seed: int = 0, alpha: float = 0.6, layers: int = 3):
    """Layered mist strata over rect: far layers high, small and slow; near ones low, big, fast."""
    l, tp, r, b = rect
    h = b - tp
    for i in range(layers):
        f = i / max(1, layers - 1)
        y0 = tp + h * 0.45 * f
        band = (l, y0, r, y0 + h * (0.45 + 0.25 * f))
        col = colors[min(i, len(colors) - 1)]
        fog_band(canvas, band, t, density, col, speeds[min(i, len(speeds) - 1)], seed + 17 * i,
                 alpha * (0.7 + 0.3 * f), size=0.8 + 0.6 * f)


# ---------------------------------------------------------------------------------------------
# a sparse pixel texture (was the paper mottle)
# ---------------------------------------------------------------------------------------------
def mottle(canvas, rect, alpha: float = 0.3, scale: float = 1.0, seed: int = 0, density: float = 0.012):
    """Sparse single pixels a little lighter or darker than what lies under them, fixed to the
    surface (they move with the canvas). Takes the plastic flatness off a big flat area; alpha
    0.2..0.4 is subtle. Under 1 ms full frame."""
    if alpha <= 0.004:
        return
    l, tp, r, b = rect
    cell = PX * max(1.0, scale)
    c0, r0 = math.floor(l / cell), math.floor(tp / cell)
    nc, nr = max(1, math.ceil(r / cell) - c0), max(1, math.ceil(b / cell) - r0)
    n = int(nc * nr * density)
    if n <= 0:
        return
    ids = np.arange(n) + seed * 7717
    # cells hashed from the surface's own cell grid, so the pattern does not depend on the rect
    cx = c0 + (H01(ids, 961) * nc).astype(np.int64)
    cy = r0 + (H01(ids, 962) * nr).astype(np.int64)
    key = cx * 73856093 ^ cy * 19349663
    keep = np.ones(n, bool)
    lite = H01(key, 964 + seed) < 0.5
    L = Layer(canvas, rect, sparse=True)
    if L.empty:
        return
    ix, iy = L.to_ipx((cx + 0.5) * cell, (cy + 0.5) * cell)
    L.put(ix[keep & lite], iy[keep & lite], (1.0, 0.98, 0.94), alpha * 0.5)
    L.put(ix[keep & ~lite], iy[keep & ~lite], INK, alpha * 0.7)
    L.blit(canvas)


# ---------------------------------------------------------------------------------------------
# rain, optionally lit warm from one side
# ---------------------------------------------------------------------------------------------
_DEPTHS = ((2, 0.30, 0.55), (4, 0.50, 0.80), (7, 0.80, 1.0))   # length px, alpha, speed share


def rain(ctx, rect, amount: float = 0.6, slant: float = -0.18, seed: int = 0, color=RAIN, alpha: float = 0.8,
         lit_side: str | None = None, lit_color=AMBER, lit_reach: float = 0.45, t: float | None = None,
         splash: float = 0.6, ground=None, canvas=None):
    """Rain as one-pixel streaks at three depths (far 2 px faint, mid 4 px, near 7 px bright)
    over rect (l, t, r, b), about 700 * amount in the air, slanting `slant` pixels sideways per
    pixel down. Each drop lands somewhere in `ground` = (y_top, y_bottom) (default the lower 45 %
    of rect; far drops land higher) and leaves a tiny splash for one step if splash > 0.
    lit_side 'left' / 'right' lights the streaks warm toward that side (over lit_reach of the
    width), their energy on ctx.glow. About 1.5 ms."""
    if amount <= 0.01:
        return
    t = ctx.t if t is None else t
    canvas = ctx.canvas if canvas is None else canvas
    L = Layer(canvas, rect, sparse=True)
    if L.empty:
        return
    l, tp, r, b = rect
    g0, g1 = ground if ground is not None else (tp + (b - tp) * 0.55, b)
    n = 700.0 * amount
    life = 0.9
    ids, age = prims.emitter(t, n / 0.55, life, id0=seed * 1000003, max_n=3000)
    dk = np.minimum(2, (H01(ids, 12) * 3).astype(np.int64))
    dep = np.array(_DEPTHS)
    lnp = dep[dk, 0].astype(np.int64)
    al = dep[dk, 1] * alpha
    speed = 1500.0 + 1300.0 * dep[dk, 2]
    land = g0 + (g1 - g0) * (0.15 + 0.85 * (dk / 2.0) ** 0.8) * (0.6 + 0.4 * H01(ids, 14))
    ystart = tp - 60.0 - H01(ids, 13) * 240.0
    py = ystart + speed * age
    span = (r - l) + 400.0
    pxs = l - 200.0 + H01(ids, 11) * span + slant * (py - ystart)
    falling = py < land
    hix, hiy = L.to_ipx(pxs, np.minimum(py, land))
    if lit_side:
        f = (pxs - l) / max(1.0, r - l)
        f = 1.0 - f if lit_side == "right" else f
        lit = np.clip(1.0 - f / lit_reach, 0.0, 1.0) ** 1.3
    else:
        lit = np.zeros_like(pxs)
    lit_q = np.round(lit * 2) / 2                                     # three steps: none, half, full
    sel = falling
    ix, iy, k, idx = line_px(hix[sel], hiy[sel], -slant, -1.0, lnp[sel])
    a_run = al[sel][idx] * np.where(k == 0, 1.0, np.where(k < lnp[sel][idx] - 1, 0.85, 0.5))
    lq = lit_q[sel][idx]
    warm = P.mix(lit_color, PAPER, 0.25)
    cols = np.where((lq > 0.75)[:, None], rgb(warm), np.where((lq > 0.25)[:, None], rgb(P.mix(color, warm, 0.5)), rgb(color)))
    L.put(ix, iy, cols, np.minimum(1.0, a_run * (1.0 + 0.8 * lq)))
    if splash > 0:
        sp = (~falling) & (age - (land - ystart) / speed < 1.0 / 15.0 + 1e-6) & (dk > 0)
        if sp.any():
            sx, sy = hix[sp], hiy[sp]
            a_s = al[sp] * splash
            L.put(np.r_[sx, sx - 1, sx + 1], np.r_[sy, sy - 1, sy - 1], color, np.r_[a_s, a_s * 0.7, a_s * 0.7])
    L.blit(canvas)
    g = getattr(ctx, "glow", None)
    if lit_side and g is not None:
        ws = falling & (lit > 0.25)
        if ws.any():
            x1, y1 = pxs[ws], np.minimum(py, land)[ws]
            x0, y0 = x1 - slant * lnp[ws] * PX, y1 - lnp[ws] * PX
            prims.draw_streaks(g, x0, y0, x1, y1, 4.0, lit_color, al[ws] * lit[ws] * 0.7, levels=2, additive=True)


# ---------------------------------------------------------------------------------------------
# the wet-ground mirror
# ---------------------------------------------------------------------------------------------
_SCRATCH: dict = {}


def _scratch(w: int, h: int):
    key = (w, h)
    if key not in _SCRATCH:
        arr = np.zeros((h, w, 4), np.uint8)
        _SCRATCH[key] = (arr, skia.Surface(arr))
    return _SCRATCH[key]


def mirror(ctx, draw_fn, y0: float, depth: float | None = None, alpha: float = 0.7, tint=None,
           ripple: float = 1.0, squash: float = 0.7, dark: float = 0.25, x0: float | None = None,
           x1: float | None = None, t: float | None = None, streak: float = 0.25, seed: int = 0):
    """Wet ground mirroring what stands above the line y0 (local units on ctx.canvas).

    draw_fn() paints on ctx.canvas whatever is reflected (sky, cloud, far shapes, lights); while
    it runs ctx.canvas is a scratch surface with the same matrix and ctx.glow swallows everything,
    so nothing is painted twice. The reflection is laid below y0 down to y0 + depth (default: the
    frame's bottom) between x0 and x1: flipped, squashed by `squash` (0.7 = what stood 100 units
    above shows 70 below), darkened by `dark`, mixed toward `tint` (default INK) and broken into
    one-pixel rows, each shifted sideways by whole pixels in a slow ripple (`ripple` = amplitude
    in pixels near the horizon, growing toward the viewer) and dimmed in a sparse pattern of
    streaks (`streak` 0..1). Works inside `graded` and inside a dissolve (it draws on ctx.canvas
    like anything else). Cost: the reflected drawing again, plus about 2 ms."""
    t = ctx.t if t is None else t
    canvas = ctx.canvas
    m = canvas.getTotalMatrix()
    isz = canvas.getBaseLayerSize()
    dw, dh = isz.width(), isz.height()
    yline = m.mapXY(0.0, y0).y()
    ybot = dh if depth is None else m.mapXY(0.0, y0 + depth).y()
    xa = 0.0 if x0 is None else m.mapXY(x0, y0).x()
    xb = float(dw) if x1 is None else m.mapXY(x1, y0).x()
    xa, xb = max(0.0, min(xa, xb)), min(float(dw), max(xa, xb))
    row0 = int(math.floor(yline / PX + 0.5))                          # first pixel row of the reflection
    rows = int(min(dh / PX, math.ceil(ybot / PX))) - row0
    c0, c1 = int(math.floor(xa / PX)), int(math.ceil(xb / PX))
    if rows <= 0 or c1 <= c0:
        return
    span = int(math.ceil(rows / max(0.1, squash))) + 2                # rows of source above the line
    src_top = max(0, row0 - span)
    amp = max(0.0, ripple)
    pad = int(math.ceil(amp * 2.5)) + 1
    sc0, sc1 = max(0, c0 - pad), min(dw // PX, c1 + pad)
    arr, surf = _scratch(dw, dh)
    sc = surf.getCanvas()
    sc.restoreToCount(1)
    sc.resetMatrix()
    clip = skia.Rect.MakeLTRB(sc0 * PX, src_top * PX, sc1 * PX, row0 * PX)
    sc.clipRect(clip)
    sc.clear(0)
    sc.setMatrix(m)
    old_c, old_g = ctx.canvas, getattr(ctx, "glow", None)
    ctx.canvas, ctx.glow = sc, null_canvas()
    try:
        draw_fn()
    finally:
        ctx.canvas, ctx.glow = old_c, old_g
        sc.restoreToCount(1)
        sc.resetMatrix()
    surf.flushAndSubmit()
    src = arr[src_top * PX + PX // 2: row0 * PX: PX, sc0 * PX + PX // 2: sc1 * PX: PX].astype(np.float32) / 255.0
    if not len(src):
        return
    j = np.arange(rows)
    srow = (row0 - 1 - np.floor(j / max(0.1, squash)).astype(np.int64)) - src_top
    valid = (srow >= 0) & (srow < len(src))
    srow = np.clip(srow, 0, len(src) - 1)
    near = j / max(1.0, rows - 1)
    step = math.floor(t * 4.0)                                         # the ripple moves four times a second
    ph = 6.283 * H01(seed, 70)
    wob = np.sin(j * 0.9 + t * 2.1 + ph) + 0.6 * np.sin(j * 0.37 - t * 1.3 + 2 * ph)
    sh = np.round(amp * (0.5 + 1.5 * near) * wob * 0.6).astype(np.int64)
    cols = np.arange(c0, c1) - sc0
    cc = np.clip(cols[None, :] - sh[:, None], 0, src.shape[1] - 1)
    out = src[srow[:, None], cc]                                       # (rows, ncols, 4) premultiplied
    tint = INK if tint is None else tint
    a = out[..., 3:4]
    col = out[..., :3] * (1.0 - dark) + np.asarray(tint, np.float32) * dark * a
    hv = H01(j + 1000 * (seed + 1) + 7 * step, 71)
    rowf = np.where(hv < streak * 0.35, 0.5, np.where(hv < streak, 0.8, 1.0))
    fade = 1.0 - 0.25 * near
    k = (alpha * rowf * fade * valid)[:, None, None]
    Layer.raw(c0, row0, (col * k).astype(np.float32), (a * k)[..., 0].astype(np.float32)).blit(canvas)


def reflect(canvas, y: float, draw_fn, alpha: float = 0.35, squash: float = 1.0, tint=None, dark: float = 0.3,
            gaps: bool = True, x0: float = -1e5, x1: float = 1e5, depth: float = 1e5):
    """A figure's own reflection under its feet: draw_fn() (drawing on `canvas`) flipped about the
    line y, squashed by `squash`, darkened toward `tint` and, if gaps, with every third pixel row
    cut out (wet ground); x0, x1, depth limit it (cheaper: about 1 ms for a figure's box, 4 ms
    unbounded). Draw it before the figure. Its glow is not repeated."""
    n = canvas.getSaveCount()
    box = skia.Rect.MakeLTRB(x0, y, x1, y + depth)
    canvas.save()
    canvas.clipRect(box)
    canvas.saveLayerAlpha(box, int(round(255 * max(0.0, min(1.0, alpha)))))
    canvas.save()
    canvas.translate(0.0, y)
    canvas.scale(1.0, -squash)
    canvas.translate(0.0, -y)
    draw_fn()
    canvas.restoreToCount(n + 2)                     # back in the layer, matrix restored
    tint = INK if tint is None else tint
    canvas.drawPaint(skia.Paint(Color=sk(tint, dark), BlendMode=skia.BlendMode.kSrcATop))
    if gaps:
        dc = canvas.getDeviceClipBounds()
        y_dev = canvas.getTotalMatrix().mapXY(0.0, y).y()
        row0 = int(math.floor(y_dev / PX + 0.5))
        path = skia.Path()
        for k in range(row0 + 2, int(math.ceil(dc.bottom() / PX)), 3):
            path.addRect(skia.Rect.MakeLTRB(dc.left(), k * PX, dc.right(), (k + 1) * PX))
        canvas.save()
        canvas.resetMatrix()
        canvas.drawPath(path, skia.Paint(BlendMode=skia.BlendMode.kDstOut))
        canvas.restore()
    canvas.restoreToCount(n)
