"""hx.chalk.day: the colour world. The warm paper, the ring that brings the colour, the sky.

Colour arrives as crayons arrive: ring(F, draw_fn, ...) renders the same scene function twice (night
skin, day skin; same time, same camera, each on its own paper) and shows the day render inside a
wobbling disc whose edge is eight pastel strokes running round and round. A scene function reads
F.skin (or F.day, F.pick(night, day)); the pieces here and in hills.py follow it by themselves.

The day skin is a pastel drawing at golden hour: sky(F, hour) rubs a gradient from dusty blue down to
peach, lays irregular strokes over it, soft cloud bands, and a low sun as a rubbed disc in its halo
(no rays). hour runs from afternoon gold (0) to evening (1). In the night skin the same sky is the
same clouds as dim smears and the same sun as a pale disc of chalk behind the haze.
"""
from __future__ import annotations

import math

import numpy as np
import skia

from .core import (A, C, H, W, Frame, Post, _CACHE, arc, blob, chalk, ease, htab, lowfreq, mix, path_of, ramp, rgb_image, rnd,
                   rsym, seg, smooth, smudge, tooth_tile, vn, wash, white)
from .hills import _mesh, _polys, _rgb, _rub, _rub_layer

__all__ = ["paper_day", "paper_tone", "ring", "sky", "sun", "cloud", "sun_at", "CRAYONS"]

# the eight pastels that draw the ring (golden hour, never primaries)
CRAYONS = (C.MUSTARD, C.SUN_HALO, C.CORAL, C.ROSE, C.LILAC, C.SKY_HI, C.SEA, C.HILL_LIT)


def paper_day(w=W, h=H):
    """Warm drawing paper: fibres, faint stains, tooth."""
    key = ("pd", w, h)
    if key not in _CACHE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
        u, v = xx / w, yy / h
        cloud = 0.6 * lowfreq(w, h, 380, 31) + 0.4 * lowfreq(w, h, 110, 32)
        fib = lowfreq(w, h, 5, 33, aniso=9.0) * 0.5 + lowfreq(w, h, 4, 34, aniso=0.12) * 0.5
        vig = np.clip(((u - 0.5) ** 2 + (v - 0.5) ** 2 * 1.2) * 1.7, 0, 1) ** 1.5
        T = tooth_tile(w, h)
        a = np.array(C.DAY)[None, None, :]
        sh = np.array(C.DAY_SHADE)[None, None, :]
        img = a + (sh - a) * (np.clip((cloud - 0.45) * 1.6, 0, 1) * 0.5 + vig * 0.75)[..., None]
        img = img * (1.0 + 0.055 * (T - 0.5) + 0.05 * (fib - 0.5))[..., None]
        img += (white((h, w), 35) - 0.5)[..., None] * 0.014
        _CACHE[key] = rgb_image(img)
    return _CACHE[key]


def paper_tone(F: Frame, hour: float = 1.0) -> None:
    """Tone the warm sheet toward evening (C.EVE_PAPER at hour = 1): the paper itself, so call it
    before anything is drawn on it (sky() does it by itself). Day skin only. The bare sheet of the
    coda's start is `paper_tone(F, 1.0)` and the ground line."""
    if not F.day or hour <= 0.0:
        return
    k = tuple(min(1.0, e / d) for e, d in zip(C.EVE_PAPER, C.DAY))
    F.c.drawPaint(F.paint(k, min(1.0, float(hour)), None, skia.BlendMode.kMultiply))


def ring(F: Frame, draw_fn, cx: float, cy: float, radius: float, turn: float | None = None, glow: float = 0.42,
         bloom: float = 0.30, seed: int = 1000) -> None:
    """The colour moment. Call it first in a scene (it starts the picture over):

    draw_fn(F2) draws the scene for the skin of the frame it is given. (cx, cy) is the WORLD point
    the ring opens from; `radius` is in SCREEN pixels. Outside the ring the night drawing, inside it
    the day drawing. radius <= 0: night only; a radius that covers the whole frame: day only (one
    render is paid for, on F itself). turn: seconds the crayons have been running round (default F.t).
    glow: the light the ring throws on the dark side; bloom: the night side's bloom once the ring is
    a few hundred px across (it starts from the night's own bloom, and the vignette ends on the day's).
    """
    sx, sy = F.cam.to_screen(cx, cy)
    far = max(math.hypot(sx - x, sy - y) for x in (0.0, W) for y in (0.0, H))
    if radius <= 0.0:
        if F.skin != "night":
            F.set_skin("night")
        draw_fn(F)
        return
    if radius * 0.95 - 60.0 > far:
        F.set_skin("day")
        draw_fn(F)
        return
    turn = F.t if turn is None else turn
    R = float(radius)
    FN = F.sub("night")
    draw_fn(FN)
    with FN.screen():
        smudge(FN, sx, sy, R * 1.35, R * 1.35, (0.96, 0.84, 0.60), glow, "glow", additive=True, power=1.8, inner=0.66)
    FN.apply_bloom(FN.post.bloom + (bloom - FN.post.bloom) * ramp(R, 20.0, 260.0))      # from the night's own bloom: no step when the ring is born
    FD = F.sub("day")
    draw_fn(FD)
    F.set_skin("night")
    F.post.bloom = 0.0                                  # the night side has had its bloom; crayons do not glow
    # the finish goes over to the day paper's as the disc takes the frame: no step when the day render takes over
    F.post.vignette += (Post("day").vignette - F.post.vignette) * ramp(R, 0.3 * far, (far + 60.0) / 0.95)
    c = F.c
    c.drawImage(FN.image(), 0, 0)
    # the disc wobbles slowly: its outline drifts from one hand-drawn round to the next (on twos)
    u = F.tb * 0.9
    i = math.floor(u)
    edge = blob(sx, sy, R, R, seed + i, 0.035, 72)
    edge = edge + (blob(sx, sy, R, R, seed + i + 1, 0.035, 72) - edge) * ease(u - i)
    c.save()
    c.clipPath(path_of(edge, True), skia.ClipOp.kIntersect, True)
    c.drawImage(FD.image(), 0, 0)
    c.restore()
    # the crayons that draw the ring: each colour runs part of the way round, over and over
    with F.screen():
        for j, col in enumerate(CRAYONS):
            a0 = j * 0.83 + turn * (1.6 + 0.2 * j)
            an = np.linspace(a0, a0 + 2.6 + 1.1 * rnd(j, 51), 60)
            rr = R + (j - 3.5) * 9 + 9 * np.sin(an * 5 + j) + 7 * (2 * vn(an * 2.0 + j * 9, 60 + j) - 1)
            chalk(F, np.stack([sx + rr * np.cos(an), sy + rr * np.sin(an)], axis=1), col, 11.0, 0.95, seed + 100 + j, wob=1.6,
                  taper=0.3, grain="mid", edge=0.35, var=0.35)


_SUN = (1440.0, 318.0, 486.0, 54.0)      # the sun in screen px: x, y in the afternoon, y at evening, radius in the afternoon
_SKY_H = 760                             # the sky is painted down to this screen y (the land covers the rest)


def sun_at(hour: float = 0.0):
    """(x, y, r) of the sun in SCREEN px (the sky is fixed to the sheet: the land travels under it):
    low in the afternoon (hour 0), down on the far hills by evening (hour 1), larger as it sinks."""
    h = min(1.0, max(0.0, float(hour)))
    return _SUN[0], _SUN[1] + (_SUN[2] - _SUN[1]) * h, _SUN[3] * (1.0 + 0.24 * h)


def _sky_cols(hour: float):
    h = min(1.0, max(0.0, float(hour)))
    return (mix(C.SKY_HI, C.EVE_HI, h), mix(C.SKY_MID, C.EVE_MID, h), mix(C.SKY_LOW, C.EVE_LOW, h),
            mix(C.SUN_HALO, C.EVE_LOW, 0.50 * h), mix(C.SUN_CORE, C.EVE_MID, 0.42 * h))


def _sky_bake(F: Frame, k: int, seed: int = 601) -> skia.Image:
    """The gradient and the strokes of the sky at hour k (0 or 1), on a clear sheet, baked once per
    process: it is fixed to the screen like the paper, so it need not be drawn again every frame."""
    key = ("sky", k, seed)
    if key in _CACHE:
        return _CACHE[key]
    G = Frame(0.0, "day", tl=F.tl, surface=skia.Surface(W, _SKY_H))
    c = G.c
    c.clear(0x00000000)
    hi, mid, low, halo, core = _sky_cols(float(k))
    sx_, sy_, sr_ = sun_at(float(k))
    # 1. the rubbed gradient, warm round the sun
    xs = np.linspace(-20.0, W + 20.0, 17)
    ys = np.array([-20.0, 70.0, 180.0, 280.0, 370.0, 450.0, 520.0, 590.0, 670.0, 750.0])
    X, Y = np.meshgrid(xs, ys)
    u = np.clip((Y - 50.0) / 340.0, 0.0, 1.0)
    v = np.clip((Y - 390.0) / 180.0, 0.0, 1.0)
    rgb = _rgb(hi) + smooth(u)[..., None] * (_rgb(mid) - _rgb(hi))
    rgb = rgb + smooth(v)[..., None] * (_rgb(low) - rgb)
    d = np.hypot((X - sx_) / 1.45, Y - sy_)
    g = np.exp(-(d / 300.0) ** 2)
    rgb = rgb + (0.78 * g)[..., None] * (_rgb(mix(halo, core, 0.25)) - rgb)
    al = (0.92 - 0.10 * smooth(u) * (1.0 - v) + 0.06 * g) * (1.0 - smooth((Y - 610.0) / 140.0))
    _mesh(G, X, Y, rgb, al, "soft~")
    _mesh(G, X, Y, rgb * 0.5 + 0.5 * _rgb(C.CREAM), al * 0.22, "soft")       # dabbed over the wiping: the hand, not a ramp
    # 2. the strokes of the hand over it: long, irregular, a little off the level
    cell = 400.0
    ii, rr = np.meshgrid(np.arange(-2, 6), np.arange(23))
    ii, rr = ii.ravel(), rr.ravel()
    key_ = ii * 23 + rr * 7
    u1, u2, u3, u4 = htab(key_, 7, seed), htab(key_, 13, seed + 5), htab(key_, 29, seed + 9), htab(key_, 31, seed + 3)
    keep = u4 < 0.78
    xa = (ii + u1) * cell
    L = 240.0 + 560.0 * u2
    yy = -30.0 + rr * 31.0 + 22.0 * (u3 - 0.5)
    q = np.linspace(0.0, 1.0, 5)[None, :]
    SX = xa[:, None] + L[:, None] * q
    SY = yy[:, None] + (0.07 * (u1 - 0.5))[:, None] * L[:, None] * (q - 0.5) + (9.0 * (u2 - 0.5))[:, None] * np.sin(q * 3.1 + 6.0 * u3[:, None])
    band = yy + 80.0 * (u4 - 0.39)
    near_sun = np.hypot((xa + 0.5 * L - sx_) / 1.6, yy - sy_) < 300.0
    warm = mix(halo, core, 0.45)
    for m, col, w_, a_ in (((band < 180.0) & (u3 < 0.5), mix(hi, C.CREAM, 0.42), 26.0, 0.42),
                           ((band < 180.0) & (u3 >= 0.5), mix(hi, C.LILAC, 0.25), 21.0, 0.36),
                           ((band >= 180.0) & (band < 400.0) & (u3 < 0.5), mix(mid, C.CREAM, 0.55), 28.0, 0.44),
                           ((band >= 180.0) & (band < 400.0) & (u3 >= 0.5), mix(mid, hi, 0.34), 21.0, 0.30),
                           ((band >= 400.0) & (band < 640.0) & (u3 < 0.55), mix(low, C.CREAM, 0.28), 26.0, 0.42),
                           ((band >= 400.0) & (band < 640.0) & (u3 >= 0.55), mix(low, C.ROSE, 0.42), 20.0, 0.34),
                           (near_sun & (u3 > 0.3), warm, 24.0, 0.36)):
        m = m & keep
        if m.any():
            c.drawPath(_polys(G, SX, SY, m), G.pen(col, w_, a_, "sparse"))
    _CACHE[key] = G.surf.makeImageSnapshot()
    return _CACHE[key]


def _cloud_bands(t: float):
    """The cloud bands on the sheet: centre x, y, half length, thickness, a hash, a key (screen px).
    They drift left very slowly on the boil clock."""
    cell = 520.0
    drift = t * 2.2
    i0, i1 = int(math.floor((-300.0 + drift) / cell)) - 1, int(math.ceil((W + 300.0 + drift) / cell)) + 1
    out = []
    for i in range(i0, i1):
        for j in range(2):
            key = i * 2 + j
            if rnd(key, 71) < 0.24:
                continue
            x = (i + 0.15 + 0.7 * rnd(key, 72)) * cell - drift
            y = 64.0 + 320.0 * rnd(key, 73) ** 1.25
            half = 120.0 + 230.0 * rnd(key, 74)
            out.append((x, y, half, 14.0 + 15.0 * rnd(key, 75), rnd(key, 76), key))
    return out


def _clouds(F: Frame, bands, hi, low, a: float, light: float = 1.0):
    """Soft bands: a rubbed body, a warm underside toward the low sun, a cool top. No outline."""
    if not bands or a <= 0.003:
        return
    c, cam = F.c, F.cam
    z = cam.zoom
    body, under, top = [], [], []
    q = np.linspace(-1.0, 1.0, 7)
    for x, y, half, th, u, key in bands:
        for k in range(3):                                         # three overlapping strokes: a band, not a sausage
            hx = half * (1.0 - 0.24 * k) * (0.85 + 0.3 * rnd(key, 80 + k))
            ox = half * 0.40 * rsym(key, 83 + k)
            oy = th * 0.50 * (k - 1) * (1.0 if u > 0.5 else -1.0)
            body.append((x + ox + hx * q, y + oy + th * 0.22 * np.sin(q * 2.4 + 6.0 * u + k) - th * 0.30 * (1.0 - q * q)))
        xs = x + half * 0.70 * q
        under.append((xs + half * 0.10, y + th * 0.60 + th * 0.2 * np.sin(q * 2.0 + 5.0 * u)))
        top.append((xs - half * 0.12, y - th * 0.64 + th * 0.2 * np.sin(q * 2.2 + 3.0 * u)))

    def path(items):
        p = skia.Path()
        for xs, ys in items:
            S = cam.pts(np.stack([xs, ys], axis=1)).tolist()
            p.moveTo(*S[0])
            for i in range(1, len(S) - 1, 2):
                p.quadTo(S[i][0], S[i][1], S[i + 1][0], S[i + 1][1])
        return p
    th = float(np.mean([b[3] for b in bands])) * z
    if not F.day:
        c.drawPath(path(body), F.pen(C.PAPER_HAZE, th * 1.5, 0.34 * a * (0.4 + 0.6 * light), "soft~"))
        c.drawPath(path(under), F.pen(mix(C.PAPER_HAZE, C.MOON, 0.5), th * 0.5, 0.18 * a * light, "soft~"))
        return
    c.drawPath(path(body), F.pen(mix(C.CREAM, low, 0.16), th * 1.6, 0.66 * a, "soft~"))
    c.drawPath(path(top), F.pen(mix(hi, C.LILAC, 0.45), th * 0.62, 0.30 * a, "soft~"))
    c.drawPath(path(under), F.pen(mix(C.CREAM, C.SUN_HALO, 0.60), th * 0.66, 0.66 * a, "soft~"))
    c.drawPath(path(body[::3]), F.pen(C.CREAM, th * 0.5, 0.42 * a, "sparse"))


def sun(F: Frame, x: float | None = None, y: float | None = None, r: float | None = None, t=None, seed: int = 611,
        hour: float = 0.0, a: float = 1.0, light: float = 1.0):
    """The low sun: a rubbed disc in its halo, the marks of the rubbing hand going round it; no rays.
    (x, y), r: centre and radius in the coordinates of the camera in force (sky() draws it in screen
    px at sun_at(hour), the default here). hour 0 = afternoon gold .. 1 = evening (redder, softer).
    Night skin: a pale disc of chalk behind the haze, `light` strong (0 = not there)."""
    sx_, sy_, sr_ = sun_at(hour)
    x, y, r = sx_ if x is None else x, sy_ if y is None else y, sr_ if r is None else r
    if a <= 0.003:
        return
    if not F.day:
        if light <= 0.0:
            return
        # (a pale sun behind the haze, not a moon: smooth, wide in its light, no blotches on its face)
        smudge(F, x, y, r * 5.2, r * 3.8, C.MOON, 0.10 * a * light, "glow", additive=True, power=1.5)
        smudge(F, x, y, r * 1.9, r * 1.9, C.MOON, 0.10 * a * light, "glow", additive=True, power=1.8)
        smudge(F, x, y, r * 1.12, r * 1.12, mix(C.PAPER_HAZE, C.MOON, 0.55), 0.40 * a * light, "glow", power=1.7, inner=0.62)
        return
    _, _, _, halo, core = _sky_cols(hour)
    k = min(1.0, max(0.0, float(hour)))
    smudge(F, x, y, r * 2.7, r * 2.7, halo, (0.74 - 0.06 * k) * a, "glow", power=1.35)
    # the rubbing hand: a few arcs round the disc
    c, cam = F.c, F.cam
    for j, (rr, col, w_, al) in enumerate(((1.60, mix(core, C.CREAM, 0.4), 0.34, 0.55), (2.2, mix(halo, core, 0.3), 0.36, 0.40),
                                           (2.95, mix(halo, C.CREAM, 0.3), 0.40, 0.28))):
        p = skia.Path()
        for q in range(3):
            a0 = 2.1 * q + 1.3 * rnd(seed + j, q) + 0.4 * j
            S = cam.pts(arc(x, y, r * rr * (1.0 + 0.05 * rsym(seed + q, j)), r * rr * 0.96, a0, a0 + 1.2 + 0.7 * rnd(seed + j, 9 + q), 9)).tolist()
            p.moveTo(*S[0])
            for s_ in S[1:]:
                p.lineTo(*s_)
        c.drawPath(p, F.pen(col, r * w_ * cam.zoom, al * a, "sparse"))
    pale = mix(core, (1.0, 1.0, 1.0), 0.20 * (1.0 - k))             # a creamy yellow, never a white hole in the sky
    smudge(F, x, y, r * 1.16, r * 1.16, mix(C.CREAM, core, 0.5), 0.95 * a, None, power=2.0, inner=0.74)
    smudge(F, x, y, r * 1.14, r * 1.14, pale, 0.97 * a, "glow", power=1.9, inner=0.76)
    smudge(F, x - 0.22 * r, y - 0.26 * r, r * 0.62, r * 0.56, C.CREAM, 0.50 * a * (1.0 - 0.5 * k), "soft", power=1.6)     # where the pastel was pressed last


def cloud(F: Frame, x, y, s: float = 1.0, seed: int = 630, hour: float = 0.0, a: float = 1.0):
    """One soft cloud band, its middle at (x, y) in the coordinates of the camera in force; s scales
    it (1 = about 440 long). sky() lays its own; this is for a cloud of your own."""
    hi, _, low, _, _ = _sky_cols(hour)
    _clouds(F, [(x, y, 220.0 * s, 22.0 * s, rnd(seed, 1), seed)], hi, low, a)


def sky(F: Frame, hour: float = 0.0, gone: float = 0.0, light: float = 1.0, clouds: float = 1.0, sun_a: float = 1.0,
        t: float | None = None) -> None:
    """The sky, behind everything: call it first in the scene function.

    Day skin: the sheet is toned toward evening (paper_tone), then a rubbed gradient from C.SKY_HI at
    the top through C.SKY_MID down to C.SKY_LOW at the horizon, warm round the sun; irregular long
    strokes over it; soft cloud bands; the low sun. hour: 0 = afternoon gold (217.84 to 238) .. 1 =
    evening (the EVE colours; the sun down on the far hills). gone: 0..1, the sky is rubbed out from
    both ends of the frame (at 1 only the toned sheet is left). clouds, sun_a: their pressure.
    Night skin: the same clouds as dim smears and the same sun as a pale disc of chalk, both scaled
    by `light` (0 = a dark sky: nothing is drawn).
    The sky is fixed to the sheet (screen px), whatever the camera does: the land travels under it.
    Only the clouds move, drifting on the boil clock (t)."""
    t = F.tb if t is None else t
    day = F.day
    if day:
        paper_tone(F, hour)
    e = ease(seg(float(gone), 0.0, 0.62))
    if e >= 1.0 or (not day and light <= 0.0):
        return
    hi, mid, low, halo, core = _sky_cols(hour)
    h = min(1.0, max(0.0, float(hour)))
    c = F.c
    rub = _rub_layer(F, e)
    fade = 1.0
    bands = _cloud_bands(t) if clouds > 0.0 else []
    with F.screen():
        if day:
            p = skia.Paint()
            if h <= 0.0 or h >= 1.0:
                p.setAlphaf(fade)
                c.drawImage(_sky_bake(F, int(h)), 0, 0, skia.SamplingOptions(), p)
            else:                                      # between the two: the same strokes, their colours on the way
                p.setAlphaf(fade)
                c.saveLayer(skia.Rect.MakeWH(W, _SKY_H), p)
                q = skia.Paint()
                q.setBlendMode(skia.BlendMode.kPlus)
                q.setAlphaf(1.0 - h)
                c.drawImage(_sky_bake(F, 0), 0, 0, skia.SamplingOptions(), q)
                q.setAlphaf(h)
                c.drawImage(_sky_bake(F, 1), 0, 0, skia.SamplingOptions(), q)
                c.restore()
        _clouds(F, bands, hi, low, clouds * fade, light)
        sun(F, hour=hour, a=sun_a * fade, light=light)
    if rub:
        _rub(F, e, 601)
    c.restore()
