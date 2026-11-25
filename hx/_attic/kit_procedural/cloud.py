"""The gloom as pixel art: one dark lumpy mass in four flat tones with a heavier underside.

The mass is a field of puffs rasterised on the real pixel grid with a depth buffer
(hx/kit/_atm_puffs.py): rows of billows hang one below the other, the lowest row nearest, so
every row shows a pale lit lower edge over the dark band of the row behind it, as the cloud is
seen from below. A cloud in the open (`crown`) is built like a cumulus instead, lit from above
with a flat dark base. Openings (holes, the tear) are cut on the same grid: what is cut shows
whatever was drawn before (the sky), the cloud's own billows bulge into the gap, and the cloud's
edge round it catches the light in a bright rim. Puff centres and radii are whole pixels and move
slowly, so the mass changes a pixel at a time, never boils, and openings never pop.
Pure function of the arguments and t. API in hx/kit/README.md.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

from mv.engine import palette as P
from mv.engine import prims

from . import _atm_puffs as puffs
from . import look
from ._atm_px import PX, Layer, dilate, points, shift

H01 = prims.hash01
HS = prims.hash_sym

# tones: (crown, top, belly, underside)
GLOOM = (look.hex_rgb("4A5370"), look.hex_rgb("343C56"), look.hex_rgb("262D44"), look.hex_rgb("181D2F"))
STORM = (look.hex_rgb("3E4660"), look.hex_rgb("2C3349"), look.hex_rgb("20263A"), look.hex_rgb("131826"))
PALE = (look.hex_rgb("E4E7EC"), look.hex_rgb("C8CDD5"), look.hex_rgb("A9B0BC"), look.hex_rgb("8890A0"))

LIGHT_DIR = (-0.35, -0.94)          # where the sun behind the cloud sits (unit vector, screen space)


def _snap(v):
    return round(v / PX) * PX


def _noise_line(x, seed):
    """Smooth ragged line in -0.5..0.5 (three octaves); x in lobe units."""
    v = (prims.value_noise(x * 0.35, seed) - 0.5) + 0.45 * (prims.value_noise(x * 1.1, seed + 13) - 0.5) \
        + 0.2 * (prims.value_noise(x * 3.3, seed + 26) - 0.5)
    return v / 1.65


def _ends(taper):
    return taper if isinstance(taper, tuple) else (taper, taper)


def _envelope(u, taper):
    """Rounding of the ends: taper is a fraction of the width, or (left, right); 0 = no rounding."""
    tl, tr = _ends(taper)
    if tl <= 0 and tr <= 0:
        return np.ones_like(u)
    el = np.clip(u / tl, 0, 1) if tl > 0 else 1.0
    er = np.clip((1 - u) / tr, 0, 1) if tr > 0 else 1.0
    e = np.minimum(el, er) * np.ones_like(u)
    return np.sqrt(e * (2 - e))


# ---------------------------------------------------------------------------------------------
# the mass seen from below (room, lid)
# ---------------------------------------------------------------------------------------------
def _underside(rect, t, heavy, seed, churn, taper):
    """(us, ybot, ytop, rb): the underside line and the top envelope sampled across the rect
    (local units) and the size of the lowest billows."""
    l, tp, r, b = rect
    w, h = r - l, b - tp
    rb = float(np.clip(0.05 * h + 0.025 * w, 60.0, 130.0)) * (0.9 + 0.25 * heavy)
    room = max(_ends(taper)) > 0
    us = np.linspace(0.0, 1.0, max(24, int(w / rb * 4)))
    xu = us * w / rb
    tt = t * churn
    base = tp + h * 0.80
    ybot = base + rb * (0.30 + 0.25 * (1 - heavy)) * 2 * _noise_line(xu * 0.8 + 0.01 * tt, seed + 5)
    env = _envelope(us, taper)
    if room:                                             # the underside sags under its weight
        ybot = ybot + h * (0.08 + 0.08 * heavy) * (np.sin(np.pi * us) ** 1.5 - 0.6)
        ytop = tp + h * (0.18 + 0.25 * (_noise_line(xu * 0.6, seed) + 0.5))
        ytop = ybot - (ybot - ytop) * env
    else:
        ytop = np.full_like(us, -1e9)
    return us, ybot, ytop, rb


def _mass_puffs(rect, t, heavy, seed, churn, taper, density, vis_top):
    """Puffs (x, y, r, z) in local units: rows of billows from the underside up to the top
    envelope (or to the top of what can be seen), the lowest row nearest."""
    l, tp, r, b = rect
    w = r - l
    us, ybot, ytop, rb = _underside(rect, t, heavy, seed, churn, taper)
    tt = t * churn
    lo = max(float(np.min(ytop)), vis_top - 2.0 * rb)
    nrows = max(1, int(math.ceil((float(np.max(ybot)) - lo) / (0.62 * rb))) + 1)
    ns = int(math.ceil(w / (1.15 * rb))) + 3
    row = np.repeat(np.arange(nrows), ns)
    st = np.tile(np.arange(ns), nrows)
    ids = seed * 7919 + row * 1009 + st
    u = (st - 1 + 0.5 * (row % 2) + 0.7 * H01(ids, 1)) / (ns - 2)
    u = u + (6.0 / w) * tt                                  # the whole mass drifts slowly
    room = max(_ends(taper)) > 0
    if not room:
        u = u % 1.08 - 0.04
    env = _envelope(np.clip(u, 0, 1), taper)
    yb = np.interp(u, us, ybot)
    yt = np.interp(u, us, ytop)
    rr = rb * (1.0 + 0.14 * row) * (0.62 + 0.55 * H01(ids, 2)) * (0.45 + 0.55 * env)
    per = 9.0 + 9.0 * H01(ids, 3)
    ph = 6.283 * H01(ids, 4)
    x = l + u * w + rr * 0.12 * np.sin(6.283 * tt / per + ph)
    y = yb - rr * (0.50 + 0.12 * HS(ids, 5)) - row * 0.62 * rb + rr * 0.06 * np.cos(6.283 * tt / (per * 1.3) + ph)
    keep = (u > -0.02) & (u < 1.02) & (y + rr * 0.8 > yt) & (y + rr > lo) & (rr > 6.0)
    keep &= H01(ids, 6) < 0.55 + 0.45 * density + (row == 0)
    if room:
        keep &= env > 0.12
    z = row * rb * 0.6 + rb * 0.08 * H01(ids, 7)          # each row overlaps the one below it, like tiles
    return x[keep], y[keep], rr[keep], z[keep], (us, ybot, rb)


# ---------------------------------------------------------------------------------------------
# openings
# ---------------------------------------------------------------------------------------------
def _hole_shapes(L, holes, seed, tt):
    """Erase mask of the holes (ragged ellipses; near ones merge) and the billows round their
    rims (layer px): each billow is centred just outside the opening, so it bulges into the gap
    while staying part of the cloud; billows that would float inside another opening are dropped."""
    E = np.zeros((L.h, L.w), bool)
    bx, by, br = [], [], []
    X = np.arange(L.w, dtype=np.float32)[None, :]
    Y = np.arange(L.h, dtype=np.float32)[:, None]
    for i, x, y, rad, amt in holes:
        key = i + seed * 37
        amt = min(1.0, amt)
        (cx,), (cy,) = L.to_px([x], [y])
        ro = L.px_len(rad) * (0.18 + 0.82 * amt ** 0.9)
        if ro < 0.8:
            continue
        tilt = 0.8 * HS(key, 81)
        asp = 1.0 + 0.5 * H01(key, 82)
        ca, sa = math.cos(tilt), math.sin(tilt)
        rx, ry = ro * asp, ro * 0.8
        x0, x1 = max(0, int(cx - rx * 1.3) - 1), min(L.w, int(cx + rx * 1.3) + 2)
        y0, y1 = max(0, int(cy - rx * 1.3) - 1), min(L.h, int(cy + rx * 1.3) + 2)
        if x1 > x0 and y1 > y0:
            dx, dy = X[:, x0:x1] - cx, Y[y0:y1] - cy
            u, v = dx * ca + dy * sa, -dx * sa + dy * ca
            ang = np.arctan2(v / ry, u / rx)
            rag = 1.0 + 0.16 * (prims.value_noise((ang + 3.1416) * 1.6, key + 7) - 0.5) * 2
            E[y0:y1, x0:x1] |= (u / rx) ** 2 + (v / ry) ** 2 < rag ** 2
        nb = 9 + int(5 * H01(key, 86))
        for j in range(nb):
            a = 6.283 * (j + 0.6 * H01(key * 17 + j, 87)) / nb
            rr = ro * (0.20 + 0.28 * H01(key * 17 + j, 88) ** 1.5)
            d = 1.0 + 0.10 * H01(key * 17 + j, 89)
            u, v = math.cos(a) * rx * d, math.sin(a) * ry * d
            bx.append(cx + u * ca - v * sa)
            by.append(cy + u * sa + v * ca)
            br.append(rr)
    bx, by, br = np.array(bx), np.array(by), np.array(br)
    if len(bx):
        ix = np.clip(np.round(bx).astype(int), 0, L.w - 1)
        iy = np.clip(np.round(by).astype(int), 0, L.h - 1)
        inb = (bx >= 0) & (bx < L.w) & (by >= 0) & (by < L.h)
        keep = ~(inb & E[iy, ix])
        bx, by, br = bx[keep], by[keep], br[keep]
    return E, bx, by, br, None


def _seam_px(L, rect, holes, seam, seed, t):
    """The seam in layer pixels as a function of x: (xs, ys) sampled every pixel column."""
    l, tp, r, b = rect
    h = b - tp
    if seam is not None:
        pts = np.asarray(seam, np.float64)
    elif holes:
        hs = sorted(holes, key=lambda hh: hh[1])
        pts = np.array([(l - 0.1 * (r - l), hs[0][2])] + [(hh[1], hh[2]) for hh in hs] + [(r + 0.1 * (r - l), hs[-1][2])])
    else:
        pts = np.array([(l - 0.1 * (r - l), tp + 0.55 * h), (r + 0.1 * (r - l), tp + 0.45 * h)])
    pts = pts[np.argsort(pts[:, 0], kind="stable")]
    fx, fy = L.to_px(pts[:, 0], pts[:, 1])
    # low-pass the polyline (no straight segments survive)
    xs = np.linspace(fx[0], fx[-1], 96)
    ys = np.interp(xs, fx, fy)
    k = 9
    ker = np.hanning(k + 2)[1:-1]
    ys = np.convolve(np.r_[np.full(k, ys[0]), ys, np.full(k, ys[-1])], ker / ker.sum(), mode="same")[k:-k]
    u = (xs - xs[0]) / max(1e-6, xs[-1] - xs[0])
    hp = L.px_len(h)
    ys = ys + hp * (0.05 * (prims.value_noise(u * 3.0 + 0.02 * t, seed + 120) - 0.5)
                    + 0.025 * (prims.value_noise(u * 7.0, seed + 121) - 0.5))
    return xs, ys, u


def _tear_shapes(L, rect, holes, seam, seed, tear, tt):
    """Erase mask of the tear and the billows along its lips (layer px)."""
    l, tp, r, b = rect
    hp = L.px_len(b - tp)
    wp = L.px_len(r - l)
    xs, ys, u = _seam_px(L, rect, holes, seam, seed, tt)
    prof = np.sin(np.pi * np.clip(u, 0, 1)) ** 1.8
    ww = (hp * 0.42 * tear ** 1.4 + wp * 0.22 * tear ** 4) * prof \
        * (0.7 + 0.6 * prims.value_noise(u * 4.0 + 0.01 * tt, seed + 122))
    rag = 1.0 - min(1.0, tear / 0.35)
    reach = 0.10 + 0.90 * min(1.0, tear / 0.30) ** 0.8          # it runs out from the middle along the seam
    run = np.clip((reach * 0.5 - np.abs(u - 0.5)) / 0.07, 0.0, 1.0)
    ww = (ww * (1.0 - rag + rag * (0.25 + 1.5 * prims.value_noise(u * 11.0 + 0.02 * tt, seed + 123))) + 1.3) * run
    cols = np.arange(L.w, dtype=np.float64)
    sy = np.interp(cols, xs, ys)
    sw = np.interp(cols, xs, ww, left=0.0, right=0.0)
    Y = np.arange(L.h, dtype=np.float64)[:, None]
    E = (np.abs(Y - sy[None, :]) < sw[None, :]) & (sw[None, :] >= 1.0)
    # billows along both lips, sizes from small to large, bigger where the gap is wide
    m = 34
    bx, by, br = [], [], []
    for side in (1.0, -1.0):
        ids = np.arange(m) + (seed * 131 + (7 if side > 0 else 0)) * 1000
        uu = np.sort((np.arange(m) + 0.8 * H01(ids, 90)) / m)
        k = np.clip((uu * (len(u) - 1)).astype(int), 0, len(u) - 1)
        w_ = ww[k]
        rr = (0.4 + 0.6 * H01(ids, 91) ** 1.5) * (w_ * 0.7 + 2.5 + hp * 0.05 * tear)
        d = w_ + rr - np.minimum(0.55 * w_, rr * (0.45 + 0.25 * H01(ids, 92)))   # bulge in, never across
        ok = w_ > 1.0
        bx += xs[k][ok].tolist()
        by += (ys[k] + side * d)[ok].tolist()
        br += rr[ok].tolist()
    return E, np.array(bx), np.array(by), np.array(br), (xs, ys, ww)


# ---------------------------------------------------------------------------------------------
# the gloom
# ---------------------------------------------------------------------------------------------
def draw(ctx, rect, t=None, density: float = 1.0, heavy: float = 0.5, tone=None, holes=(), tear: float = 0.0,
         seed: int = 0, lit=None, churn: float = 1.0, taper: float | None = None, seam=None, canvas=None,
         rim: float = 0.18, crown: bool | None = None, light=None):
    """The gloom over rect (l, t, r, b) in local units. The underside sits at 80 % of the rect's
    height. Seen from below (room, lid): rows of billows, each with a pale lit lower edge over the
    dark band of the row behind; a room mass rounds off at its ends and its top meets the
    ceiling; a lid (rect wider than the frame) fills everything above its underside.

    density 0..1  pales and empties it (1 = solid).   heavy 0..1  darker, lower, bigger billows.
    tone          (crown, top, belly, underside); GLOOM default, STORM for the lid in c2, PALE.
    holes         [(x, y, r, amount)]: ragged openings about r across, amount 0..1 widens them,
                  near ones merge; the cloud's billows bulge into them and its edge round them
                  catches a bright rim (in `lit`'s colour), widest toward LIGHT_DIR.
    tear 0..1     a clean gap along `seam` (polyline [(x, y)...], low-passed; default through the
                  holes), running out from the middle and widening; its lips are towering lit
                  billows; at 1 only remnants at the ends remain.
    lit           the light's colour seen through the openings (default a pale cold white).
    churn         speed of the billows' slow drift (1 = periods of 9 to 18 s; 2.5 = storm).
    taper         fraction of the width over which the ends round off (default 0.14 at each end
                  that lies inside the frame, else 0 for a sky lid).
    rim           strength 0..1 of the pale lit rims.
    crown         a cloud in the open, seen from the side: lumpy lit crown, flat dark base (default:
                  when the rect's top lies well inside the frame).
    light         screen direction toward the light (default from below for a mass seen from
                  below, from above-left for a crown).
    Cost: whole-sky lid about 8 ms, with holes or a tear 10 to 14 ms; room mass about 6 ms."""
    t = ctx.t if t is None else t
    canvas = ctx.canvas if canvas is None else canvas
    tone = GLOOM if tone is None else tone
    l, tp, r, b = rect
    m = canvas.getTotalMatrix()
    dc = canvas.getDeviceClipBounds()
    if taper is None:
        x0, _ = m.mapXY(l, tp)
        x1, _ = m.mapXY(r, tp)
        pad = 40.0 * m.getScaleX()
        taper = (0.14 if min(x0, x1) > dc.left() - pad else 0.0, 0.14 if max(x0, x1) < dc.right() + pad else 0.0)
    if crown is None:
        crown = m.mapXY(l, tp).y() > dc.top() + 0.08 * dc.height() and (r - l) * m.getScaleX() < 0.7 * dc.width()
    if density < 1.0:
        pale = P.mix(tone[0], look.FOG_LIGHT, 0.4)
        tone = tuple(P.mix(c, pale, (1 - density) * 0.45) for c in tone)
    holes = [(i, *hh) for i, hh in enumerate(holes) if hh[3] > 0.01]
    tear = min(1.0, max(0.0, tear))
    if crown:
        _crowned(canvas, rect, t, tone, seed, churn, heavy, rim, lit, light, density)
        return
    L = Layer(canvas, rect)
    if L.empty:
        return
    tt = t * churn
    inv_top = L.local_grid()[1][0, 0] if L.h else tp
    xs, ys, rs, zs, (us, ybot, rb) = _mass_puffs(rect, t, heavy, seed, churn, taper, density, float(inv_top))
    n_mass = len(xs)
    fx, fy = L.to_px(xs, ys)
    Z, NX, NY, NZ, ID = puffs.raster(L, fx, fy, L.px_len(rs), L.px_len(zs), 0.78)
    # the body behind the billows: everything above the lowest row is cloud
    cols = np.arange(L.w, dtype=np.float64)
    bx_px, by_px = L.to_px(l + us * (r - l), ybot)
    yb_col = np.interp(cols, bx_px, by_px)
    yy = np.arange(L.h, dtype=np.float32)[:, None]
    rbp = max(1.0, L.px_len(rb))
    back = (yy < (yb_col - rbp * 0.9)[None, :]) & (ID < 0)
    if max(_ends(taper)) > 0:
        _, ty_px = L.to_px(l + us * (r - l), _underside(rect, t, heavy, seed, churn, taper)[2])
        yt_col = np.interp(cols, bx_px, ty_px)
        back &= yy > (yt_col + rbp * 0.6)[None, :]
    Z[back] = -1e6
    NZ[back] = 1.0
    # openings: cut, then the billows round them (only those rooted in the mass: none float)
    E = None
    bxs, bys, brs = [], [], []
    if holes:
        Eh, hx, hy, hr, _ = _hole_shapes(L, holes, seed, tt)
        E = Eh
        bxs.append(hx), bys.append(hy), brs.append(hr)
    if tear > 0.001:
        Et, tx, ty, tr, _ = _tear_shapes(L, rect, holes, seam, seed, tear, tt)
        E = Et if E is None else (E | Et)
        bxs.append(tx), bys.append(ty), brs.append(tr)
    if E is not None:
        gap = E.copy()
        bx_, by_, br_ = np.concatenate(bxs), np.concatenate(bys), np.concatenate(brs)
        if len(bx_):
            ix = np.clip(np.round(bx_).astype(int), 0, L.w - 1)
            iy = np.clip(np.round(by_).astype(int), 0, L.h - 1)
            zc = Z[iy, ix]
            ok = (zc > -1e8) & (bx_ > -br_) & (bx_ < L.w + br_)
            if ok.any():
                zm = float(Z[Z > -1e5].max()) if (Z > -1e5).any() else 0.0
                zb = np.where(zc[ok] > -1e5, zc[ok], zm) + 2.0          # just in front of the mass there
                Z2, NX2, NY2, NZ2, ID2 = puffs.raster(L, bx_[ok], by_[ok], br_[ok], zb, 0.78)
                win = ID2 >= 0
                Z[win], NX[win], NY[win], NZ[win] = Z2[win], NX2[win], NY2[win], NZ2[win]
                ID[win] = ID2[win] + n_mass
                gap &= ~win
        Z[gap] = -1e9
        # no slivers or threads of cloud left along a gap: open the mask near it
        solid = Z > -1e8
        thin = solid & ~dilate(~dilate(~solid, 1), 1) & dilate(gap, 3)
        Z[thin] = -1e9
        # and no islands cut off by the gap that are too small to be a lip
        lab, n = ndimage.label(Z > -1e8)
        if n > 1:
            size = np.bincount(lab.ravel())
            small = size < max(12.0, 1.5 * rbp * rbp)
            small[0] = False
            Z[small[lab]] = -1e9
    # the underside: a darker zone just above it (heavier with `heavy`)
    above = (yb_col[None, :] - yy) / rbp                          # 0 at the underside, 1 one billow up
    vadd = -0.20 - (0.10 + 0.15 * heavy) * np.clip(1.0 - above, 0.0, 1.0) + 0.04 * np.clip(above - 2.0, 0.0, 1.0)
    lt = light if light is not None else (0.18, 0.98)
    mask, idx = puffs.shade(L, Z, NX, NY, NZ, 4, light=lt, lz=0.3, ambient=vadd, cast=0.45, cast_len=2,
                            smooth=int(np.clip(rbp * 0.35, 2, 8)), local=0.55, dither=0.25)
    outer = puffs.rims(Z, mask, lt, inner=0.0)                   # the underside's edge: the pale rim
    inner = puffs.rims(Z, mask, lt, inner=2.0) & ~outer           # each row's lower edge: one tone up
    tones = [tone[3], tone[2], tone[1], tone[0]]
    rim_c = P.mix(tone[0], look.FOG_LIGHT, min(1.0, 0.25 + rim * 1.5))
    lit_c = P.mix(look.COLD_LIGHT, (1, 1, 1), 0.2) if lit is None else lit
    col = np.asarray(tones, np.float32)[idx]
    col[inner] = np.asarray(tones, np.float32)[np.minimum(idx[inner] + 1, 3)]
    col[outer] = np.asarray(rim_c, np.float32)
    if E is not None:
        # light through the openings: the cloud's edge round a gap catches a bright rim (two pixels
        # toward the light), the billows next to it a lighter tone
        hole = E & ~mask
        near1 = dilate(hole, 1) & mask
        dx, dy = int(round(-LIGHT_DIR[0] * 1.5)), int(round(-LIGHT_DIR[1] * 1.5))
        near2 = shift(hole, dx, dy, False) & mask
        near3 = dilate(hole, 3) & mask & ~near1
        lip = (ID >= n_mass) & mask                       # the billows round the openings face the light
        up = np.where(lip, 1, 0) + np.where(near3, 1, 0)
        col_up = np.asarray(tones, np.float32)[np.minimum(idx + up, 3)]
        sel = up > 0
        col[sel] = col_up[sel]
        top_lit = lip & (idx + up >= 3) & (L.bayer < 0.5) & near3
        col[top_lit] = np.asarray(P.mix(tone[0], lit_c, 0.35), np.float32)
        col[near1 | near2] = np.asarray(P.mix(rim_c, lit_c, 0.7), np.float32)
    a = mask.astype(np.float32)
    L.rgb[:] = col * a[..., None]
    L.a[:] = a
    L.blit(canvas, alpha=min(1.0, density ** 0.7))


# ---------------------------------------------------------------------------------------------
# a cloud in the open: lumpy crown lit from above, flat dark base
# ---------------------------------------------------------------------------------------------
def _crowned(canvas, rect, t, tone, seed, churn, heavy, rim, lit, light, density, tilt: float = 0.0,
             centre=None):
    l, tp, r, b = rect
    w, h = r - l, b - tp
    base = tp + h * 0.80
    x = (l + r) / 2
    xs, ys, rs, zs = look._cumulus_puffs(x, base, w * 0.95, base - tp, t * churn, seed, 0.15, 1.0)
    if tilt:
        cx, cy = centre if centre is not None else (x, (tp + base) / 2)
        ca, sa = math.cos(tilt), math.sin(tilt)
        xs, ys = cx + (xs - cx) * ca - (ys - cy) * sa, cy + (xs - cx) * sa + (ys - cy) * ca
    L = Layer(canvas, (l - w * 0.1, tp - h * 0.1, r + w * 0.1, b))
    if L.empty:
        return
    fx, fy = L.to_px(xs, ys)
    Z, NX, NY, NZ, ID = puffs.raster(L, fx, fy, L.px_len(rs), L.px_len(zs), 0.84)
    _, by = L.to_px([x], [base])
    brow = int(round(by[0]))
    Z[max(0, brow + 1):] = -1e9
    _, ty = L.to_px([x], [tp])
    yy = np.arange(L.h, dtype=np.float32)[:, None]
    f = np.clip((yy - ty[0]) / max(1.0, brow - ty[0]), 0.0, 1.0)
    vadd = 0.10 - (0.30 + 0.15 * heavy) * f - 0.25 * np.clip((yy - (brow - 3)) / 3.0, 0.0, 1.0)
    lt = light if light is not None else (-0.45, -0.9)
    sm = int(np.clip(L.px_len(h) * 0.12, 2, 8))
    mask, idx = puffs.shade(L, Z, NX, NY, NZ, 4, light=lt, lz=0.55, ambient=vadd, cast=0.4, cast_len=2,
                            smooth=sm, local=0.45, dither=0.35)
    rimm = puffs.rims(Z, mask, lt, inner=3.0)
    rim_c = P.mix(tone[0], look.FOG_LIGHT if lit is None else lit, min(1.0, 0.3 + rim * 1.5))
    puffs.paint(L, mask, idx, [tone[3], tone[2], tone[1], tone[0]], rimm, rim_c)
    L.blit(canvas, alpha=min(1.0, density ** 0.7))


# ---------------------------------------------------------------------------------------------
# the small pale cloud of the ending, and its string
# ---------------------------------------------------------------------------------------------
def bob(x: float, y: float, w: float, t: float, seed: int = 0):
    """Balloon-like float of the small cloud: (x, y, tilt_radians), positions on whole pixels."""
    ph = 6.283 * H01(seed, 90)
    dx = w * 0.05 * math.sin(t * 0.83 + ph) + w * 0.02 * math.sin(t * 2.1 + ph * 2)
    dy = w * 0.06 * math.sin(t * 1.17 + ph * 1.5)
    return _snap(x + dx), _snap(y + dy), 0.05 * math.sin(t * 0.9 + ph)


def small(ctx, x: float, y: float, w: float, t=None, tone=None, seed: int = 3, canvas=None):
    """The small pale-grey cloud, centre (x, y), width w, bobbing in whole pixels and tilting a
    little. Lumpy crown lit from above-left in four flat tones with a one-pixel lit rim, flat
    base. Returns the (x, y) of its belly, where the string attaches. About 1.5 ms."""
    t = ctx.t if t is None else t
    canvas = ctx.canvas if canvas is None else canvas
    bx, by, tilt = bob(x, y, w, t, seed)
    h = w * 0.62
    rect = (bx - w / 2, by - h / 2, bx + w / 2, by + h / 2)
    _crowned(canvas, rect, 0.0, PALE if tone is None else tone, seed, 0.0, 0.2, 0.3, None, None, 1.0,
             tilt=tilt, centre=(bx, by))
    ay = h * 0.28
    return _snap(bx - math.sin(tilt) * ay), _snap(by + math.cos(tilt) * ay)


def string(canvas, x0: float, y0: float, x1: float, y1: float, t: float, color=None, width: float = 1.6,
           sag: float = 0.08, alpha: float = 0.85, seed: int = 0):
    """The string from the cloud (x0, y0) to the hand (x1, y1): one pixel wide, a natural sag
    and a slow sway (width is kept for old callers; the string is always one pixel)."""
    color = look.hex_rgb("6A6F78") if color is None else color
    ln = math.hypot(x1 - x0, y1 - y0)
    sw = math.sin(t * 1.3 + 6.283 * H01(seed, 91)) * ln * 0.05
    mx, my = (x0 + x1) / 2 + sw + ln * sag * 0.3, (y0 + y1) / 2 + ln * sag
    s = np.linspace(0.0, 1.0, max(8, int(ln / PX * 2)))
    c1x, c1y = x0 + sw * 0.6, y0 + (my - y0) * 0.7
    bx = (1 - s) ** 3 * x0 + 3 * (1 - s) ** 2 * s * c1x + 3 * (1 - s) * s ** 2 * mx + s ** 3 * x1
    by = (1 - s) ** 3 * y0 + 3 * (1 - s) ** 2 * s * c1y + 3 * (1 - s) * s ** 2 * my + s ** 3 * y1
    L = Layer(canvas, None)
    ix, iy = L.to_ipx(bx, by)
    key = np.unique(np.stack([ix, iy], 1), axis=0)
    points(canvas, key[:, 0] + L.ix0, key[:, 1] + L.iy0, color, alpha, levels=1)
