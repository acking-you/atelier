"""hx.kit.birds: pixel crows (perched, landing, flying, far flocks) and the same as ordinary small birds.

Every bird is a hand-placed pixel map (`_thg_birdmaps`, three size classes per shape), coloured,
cached by (shape, pose, size, tilt, colour) and blitted at a snapped position (no resampling;
nose up or down is a one-step column shear). A wingbeat is four
stepped poses (up, mid, down, mid); far birds (under about 6 px) are 3 or 5 pixel marks that still
flap; perched heads turn in three steps. `s` is the body length in logical units (beak to tail,
5 units = 1 px); `small` 0..1 morphs a crow into an ordinary small bird (lighter, rounder, 42 %
smaller, quicker wingbeat; the shape switches at 0.5, the colour steps along). Randomness from
prims.hash01 by seed.
"""
from __future__ import annotations

import math

import numpy as np

from mv.engine import prims
from mv.engine.palette import hex_rgb, mix, shade

from hx.kit import _thg_birdmaps as M
from hx.kit import _thg_px as X
from hx.kit.pixel import PX

CROW = hex_rgb("1C2030")          # just above INK: the child stays the darkest shape
SMALL = hex_rgb("8C8274")         # a warm grey-brown sparrow tone (pass color= to change)
PI = math.pi

# ---------------------------------------------------------------------------------------------
# sprites from the hand-placed maps in _thg_birdmaps (facing right)
# ---------------------------------------------------------------------------------------------
_ROLE = {"#": X.BASE, "b": X.BASE, "+": X.LIGHT, "-": X.SHADE}


def _colors(color, small):
    base = color if color is not None else mix(CROW, SMALL, round(float(small) * 4) / 4)
    if small >= 0.5:
        return {X.BASE: base, X.LIGHT: shade(base, 0.12), X.SHADE: shade(base, -0.10)}
    return {X.BASE: base, X.LIGHT: mix(base, (0.42, 0.47, 0.62), 0.22), X.SHADE: base}


def _pick(table: dict, L: int):
    keys = sorted(table)
    k = keys[0]
    for kk in keys:
        if L >= kk - 1:
            k = kk
    return table[k], (2 if L >= 2 * keys[-1] else 1)


def _build(entry, colors, facing: int, head: int = 1, tilt: int = 0, scale: int = 1) -> X.Sprite:
    rows, ox, oy = entry
    g = np.array([list(r) for r in rows])
    pad = 3
    g = np.pad(g, pad, constant_values=".")
    ox, oy = ox + pad, oy + pad
    if head != 1:
        for j in range(g.shape[0]):
            bs = np.nonzero(g[j] == "b")[0]
            if len(bs) == 0:
                continue
            g[j, bs] = "."
            if head == -1:
                filled = np.nonzero(g[j] != ".")[0]
                c0 = filled[0] if len(filled) else ox
                for k in range(len(bs)):
                    if c0 - 1 - k >= 0:
                        g[j, c0 - 1 - k] = "b"
    if tilt:
        tn = math.tan(math.radians(15.0 * tilt))
        out = np.full_like(g, ".")
        for i in range(g.shape[1]):
            dy = int(round(-tn * (i + 0.5 - ox)))
            col = g[:, i]
            if dy > 0:
                out[dy:, i] = col[:-dy]
            elif dy < 0:
                out[:dy, i] = col[-dy:]
            else:
                out[:, i] = col
        g = out
    roles = np.zeros(g.shape, np.uint8)
    for ch, r in _ROLE.items():
        roles[g == ch] = r
    if facing < 0:
        roles = roles[:, ::-1]
        ox = roles.shape[1] - ox
    if scale > 1:
        roles = np.repeat(np.repeat(roles, scale, 0), scale, 1)
        ox, oy = ox * scale, oy * scale
    return X.Sprite(X.colorize(roles, colors), ox, oy)


def _pose_of(phase: float) -> int:
    return int((phase % 1.0) * 4) % 4


def _flying_sprite(L: int, pose, tilt: int, facing: int, small: bool, ck, colors):
    key = ("bfly", L, pose, tilt, facing, small, ck)

    def make():
        lim3, lim5 = (4, 6) if small else (4, 7)
        if L < lim5:
            marks = M.MARKS[3 if L < lim3 else 5]
            return _build(marks[pose if pose in marks else 1], colors, 1)
        entry, sc = _pick(M.SMALL_FLY if small else M.CROW_FLY, L)
        return _build(entry[pose], colors, facing, tilt=tilt, scale=sc)
    return X.memo(key, make)


def _perched_sprite(L: int, head: int, facing: int, small: bool, ck, colors, fold=None):
    key = ("bsit", L, head, facing, small, ck, fold)

    def make():
        if fold is not None:
            if small:
                entry, sc = _pick(M.SMALL_FLY, L)
                return _build(entry[0 if fold == "flare" else 3], colors, facing, tilt=1, scale=sc)
            return _build(M.CROW_FLARE if fold == "flare" else M.CROW_HALF, colors, facing)
        entry, sc = _pick(M.SMALL_SIT if small else M.CROW_SIT, L)
        return _build(entry, colors, facing, head, scale=sc)
    return X.memo(key, make)


def _length_px(s: float, small: float) -> int:
    return max(2, int(round(s * (1 - 0.42 * small) / PX)))


# ---------------------------------------------------------------------------------------------
# public
# ---------------------------------------------------------------------------------------------
def head_turn(t: float, seed: int) -> float:
    """Irregular head turns of a perched bird: holds, then a quick turn (1 forward, -1 back)."""
    per = 1.2 + 1.6 * prims.hash01(seed, 3)
    u = t / per + prims.hash01(seed, 4) * 7.0
    k = math.floor(u)
    choices = (1.0, 1.0, 0.55, -1.0, 0.8, -0.6, 1.0, 0.35)
    a = choices[int(prims.hash01(k * 131 + seed, 5) * len(choices))]
    b = choices[int(prims.hash01((k + 1) * 131 + seed, 5) * len(choices))]
    f = (u - k - 0.82) / 0.18
    f = 0.0 if f < 0 else (1.0 if f > 1 else f * f * (3 - 2 * f))
    return a * (1 - f) + b * f


def _head_step(ht: float) -> int:
    return 1 if ht > 0.6 else (-1 if ht < -0.2 else 0)


def perched(canvas, x: float, y: float, s: float, t: float, seed: int = 0, facing: int = 1, color=None,
            small: float = 0.0, alpha: float = 1.0):
    """One perched bird standing at (x, y) (its feet), body length s logical units."""
    perched_row(canvas, [x], [y], [s], t, [seed], [facing], color, small, alpha)


def perched_row(canvas, xs, ys, ss, t: float, seeds, facings, color=None, small: float = 0.0,
                alpha: float = 1.0, t_land=None):
    """Many perched (or landing, when t_land[i] is given) birds."""
    cols = _colors(color, small)
    ck = (X.qc(cols[X.BASE]), small >= 0.5)
    for i in range(len(xs)):
        tl = None if t_land is None else t_land[i]
        _bird(canvas, float(xs[i]), float(ys[i]), float(ss[i]), t, int(seeds[i]), int(facings[i]), small,
              tl, cols, ck, alpha)


def _bird(canvas, x, y, s, t, seed, facing, small, t_land, cols, ck, alpha):
    sm = small >= 0.5
    L = _length_px(s, small)
    fc = 1 if facing >= 0 else -1
    if t_land is None or t >= t_land + 0.35:
        head = _head_step(head_turn(t, seed))
        dip = 0
        if t_land is not None and t < t_land + 0.6:
            dip = PX                                         # the settle: one pixel down, once
        sp = _perched_sprite(L, head, fc, sm, ck, cols)
        X.blit(canvas, sp, x, y + dip, alpha)
        return
    tau = t - t_land
    if tau < -0.3:                                           # glide in along an arc from behind, above
        u = min(1.0, (-tau - 0.3) / 1.4)
        ox, oy = -fc * 3.0 * s * u, -1.4 * s * u * (0.6 + 0.4 * u)
        rate = flap_rate(small)
        pose = _pose_of(t * rate + prims.hash01(seed, 7)) if u > 0.45 else "glide"
        sp = _flying_sprite(L, pose, 0 if u < 0.6 else -1, fc, sm, ck, cols)
        X.blit(canvas, sp, x + ox, y + oy - 0.35 * s, alpha)
    elif tau < 0.0:                                          # flare: wings up and forward, body tilts up
        f = (tau + 0.3) / 0.3
        ox = -fc * 0.3 * s * (1 - f)
        oy = -0.12 * s * (1 - f)
        sp = _perched_sprite(L, 1, fc, sm, ck, cols, "flare")
        X.blit(canvas, sp, x + ox, y + oy, alpha)
    else:                                                    # fold in two steps
        fold = "flare" if tau < 0.15 else "half"
        sp = _perched_sprite(L, 1, fc, sm, ck, cols, fold)
        X.blit(canvas, sp, x, y, alpha)


def landing(canvas, x: float, y: float, s: float, t: float, t_land: float, seed: int = 0, facing: int = 1,
            color=None, small: float = 0.0, alpha: float = 1.0):
    """A bird landing on (x, y) at t_land: glides in for 1.4 s (flapping, then gliding), flares its
    wings for the last 0.3 s, folds them in two steps over 0.35 s and sits (one-pixel settle, head
    turns). Nothing is drawn before t_land - 1.7."""
    if t < t_land - 1.7:
        return
    perched_row(canvas, [x], [y], [s], t, [seed], [facing], color, small, alpha, t_land=[t_land])


def flying(canvas, x: float, y: float, s: float, phase: float, heading: float = 0.0, bank: float = 0.0,
           color=None, small: float = 0.0, alpha: float = 1.0):
    """One bird in flight centred at (x, y); heading in radians in screen space (0 = toward +x,
    positive turns toward +y), phase through one wingbeat (only its fraction counts: four stepped
    poses), bank -1..1 (kept for callers; pixel birds do not bank)."""
    draw_flock(canvas, [x], [y], s, [phase], [heading], [bank], None, color, small, alpha)


def draw_flock(canvas, xs, ys, s: float, phases, headings, banks=None, scales=None, color=None,
               small: float = 0.0, alpha: float = 1.0):
    """Many flying birds (cached sprites: 40 birds about 0.5 ms)."""
    cols = _colors(color, small)
    sm = small >= 0.5
    ck = (X.qc(cols[X.BASE]), sm)
    for i in range(len(xs)):
        hd = float(headings[i])
        cx, sx = math.cos(hd), math.sin(hd)
        fc = 1 if cx >= 0 else -1
        ang = math.atan2(-sx, abs(cx))                       # nose up positive
        aq = int(round(ang / math.radians(15.0)))
        sc = 1.0 if scales is None else float(scales[i])
        L = _length_px(s * sc, small)
        sp = _flying_sprite(L, _pose_of(float(phases[i])), max(-1, min(1, aq)), fc, sm, ck, cols)
        X.blit(canvas, sp, float(xs[i]), float(ys[i]), alpha)


def flap_rate(small: float = 0.0) -> float:
    """Wingbeats per second (crow about 3, small bird about 7)."""
    return 3.0 + 4.0 * float(small)


def flock_wheel(n: int, t: float, center, radius: float, seed: int = 0, speed: float = 1.0,
                squash: float = 0.42, small: float = 0.0) -> dict:
    """Deterministic positions of n birds wheeling round center (an ellipse seen in perspective).

    Returns arrays x, y, heading, phase, scale, bank (feed them to draw_flock)."""
    ids = np.arange(n) + seed * 977
    h1, h2, h3, h4, h5 = (prims.hash01(ids, k) for k in (31, 32, 33, 34, 35))
    r = radius * (0.68 + 0.32 * h1)
    w = speed * (0.30 + 0.12 * h2) * (1.2 - 0.4 * h1)
    th = h3 * 2 * PI + w * t
    wob = 0.10 * radius * np.sin(t * (0.7 + 0.5 * h4) + h5 * 6.0)
    cx, cy = center
    x = cx + r * np.cos(th) + 0.08 * radius * np.sin(t * 0.43 + h2 * 5)
    y = cy + squash * r * np.sin(th) + wob
    dx = -r * np.sin(th) * w
    dy = squash * r * np.cos(th) * w + 0.1 * radius * (0.7 + 0.5 * h4) * np.cos(t * (0.7 + 0.5 * h4) + h5 * 6.0)
    heading = np.arctan2(dy * 0.55, dx)
    rate = flap_rate(small) * (0.85 + 0.3 * h4)
    glide = (np.sin(t * 0.9 + h5 * 9) > 0.55)
    phase = np.where(glide, 0.30, (t * rate + h5) % 1.0)              # gliding = wings level
    scale = (0.80 + 0.35 * h2) * (1.0 + 0.18 * np.sin(th))
    bank = np.clip(np.cos(th) * 0.8, -1, 1)
    return dict(x=x, y=y, heading=heading, phase=phase, scale=scale, bank=bank)


def flock_scatter(n: int, t: float, t0: float, origin, seed: int = 0, spread: float = 1.2, speed: float = 260.0,
                  start=None, small: float = 0.0, up: float = -PI / 2) -> dict:
    """n birds bursting outward from origin at t0 (a fan around direction `up`, default straight
    up the screen), accelerating away. start=(xs, ys) gives positions before t0 (else a loose
    cluster). speed in logical units/s. Same return format as flock_wheel."""
    ids = np.arange(n) + seed * 613
    h1, h2, h3, h4 = (prims.hash01(ids, k) for k in (41, 42, 43, 44))
    ox, oy = origin
    if start is None:
        sx = ox + (h1 - 0.5) * 120.0
        sy = oy + (h2 - 0.5) * 50.0
    else:
        sx, sy = np.asarray(start[0], float), np.asarray(start[1], float)
    ang = up + (h3 - 0.5) * 2 * spread
    delay = h4 * 0.45
    tau = np.maximum(0.0, t - t0 - delay)
    v = speed * (0.7 + 0.6 * h1)
    dist = v * tau + 0.5 * v * 0.8 * tau * tau
    curl = (h2 - 0.5) * 0.6 * np.minimum(tau, 3.0)
    a2 = ang + curl
    x = sx + np.cos(a2) * dist
    y = sy + np.sin(a2) * dist
    heading = np.where(tau > 0, a2, np.where(h1 > 0.5, 0.0, PI))
    rate = flap_rate(small) * (1.5 - 0.4 * np.minimum(tau, 1.0))
    phase = (t * rate + h3) % 1.0
    scale = 0.85 + 0.3 * h2
    bank = np.clip(curl, -1, 1)
    return dict(x=x, y=y, heading=heading, phase=phase, scale=scale, bank=bank)
