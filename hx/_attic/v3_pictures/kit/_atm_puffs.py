"""Private to look / cloud: lumpy cloud masses as pixel art.

A cloud is a set of puffs (squashed spheres) rasterised on the real pixel grid with a depth
buffer: each pixel knows which puff it shows and that puff's surface normal. Lighting is then a
few flat tones (ordered stipple only across a tone edge), a cast shadow where a nearer puff lies
between the pixel and the light (the dark band under every row of billows), a one-pixel lit rim
on the sun side of the silhouette and of every puff that stands in front of another, and an
optional darker flat base. Centres and radii are whole pixels, so a slowly drifting puff changes
the picture one pixel at a time and edges never crawl.
"""
from __future__ import annotations

import numpy as np

from ._atm_px import quantize, shift


_TPL: dict = {}


def _template(rr: int, ry: int):
    """Unit height (0..1 at the centre, -inf outside) of a squashed sphere, (2ry+1, 2rr+1)."""
    key = (rr, ry)
    tp = _TPL.get(key)
    if tp is None:
        dx = np.arange(-rr, rr + 1, dtype=np.float32) / rr
        dy = np.arange(-ry, ry + 1, dtype=np.float32) / ry
        d2 = dy[:, None] ** 2 + dx[None, :] ** 2
        tp = np.where(d2 < 1.0, np.sqrt(np.clip(1.0 - d2, 0.0, None)), -np.inf).astype(np.float32)
        if len(_TPL) > 4000:
            _TPL.clear()
        _TPL[key] = tp
    return tp


def raster(L, cx, cy, r, z, squash=0.82):
    """Depth-buffer the puffs into L's pixel box. cx, cy, r in layer pixels (rounded here), z an
    offset added to each puff's height (bigger = nearer). Returns (Z, NX, NY, NZ, ID)."""
    H, W = L.h, L.w
    Z = np.full((H, W), -1e9, np.float32)
    ID = np.full((H, W), -1, np.int32)
    cx = np.round(np.asarray(cx, np.float64)).astype(np.int64)
    cy = np.round(np.asarray(cy, np.float64)).astype(np.int64)
    r = np.round(np.asarray(r, np.float64)).astype(np.int64)
    z = np.broadcast_to(np.asarray(z, np.float64), cx.shape)
    sq = np.broadcast_to(np.asarray(squash, np.float64), cx.shape)
    ry = np.maximum(1, np.round(r * sq)).astype(np.int64)
    vis = (r >= 1) & (cx + r >= 0) & (cx - r < W) & (cy + ry >= 0) & (cy - ry < H)
    for k in np.nonzero(vis)[0].tolist():
        x, y, rr, yy = int(cx[k]), int(cy[k]), int(r[k]), int(ry[k])
        tp = _template(rr, yy)
        x0, x1 = max(0, x - rr), min(W, x + rr + 1)
        y0, y1 = max(0, y - yy), min(H, y + yy + 1)
        za = tp[y0 - y + yy:y1 - y + yy, x0 - x + rr:x1 - x + rr] * float(yy) + float(z[k])
        zs = Z[y0:y1, x0:x1]
        upd = za > zs
        np.copyto(zs, za, where=upd)
        np.copyto(ID[y0:y1, x0:x1], k, where=upd)
    # normals of the winning puff at every pixel
    m = ID >= 0
    k = np.where(m, ID, 0)
    xx = np.arange(W, dtype=np.float32)[None, :]
    yy = np.arange(H, dtype=np.float32)[:, None]
    NX = np.where(m, (xx - cx[k]) / np.maximum(1, r[k]), 0.0).astype(np.float32)
    NY = np.where(m, (yy - cy[k]) / ry[k], 0.0).astype(np.float32)
    NZ = np.sqrt(np.clip(1.0 - NX * NX - NY * NY, 0.0, 1.0)) * m
    return Z, NX, NY, NZ, ID


def _box(a, r: int):
    """Box blur (2r+1 square) via an integral image, edge-clamped."""
    if r <= 0:
        return a
    p = np.pad(a, r + 1, mode="edge").astype(np.float64)
    c = p.cumsum(0).cumsum(1)
    k = 2 * r + 1
    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    return (s / (k * k))[: a.shape[0], : a.shape[1]].astype(np.float32)


def form_normals(Z, mask, NX, NY, NZ, smooth: int, local: float):
    """Blend each puff's own normal with the normal of the whole mass (the gradient of its depth
    field blurred over `smooth` px), so a cloud reads as one lit form with lumps, not a heap of
    balls. local 0..1 is the share of the puff's own normal."""
    if smooth <= 0:
        return NX, NY, NZ
    zmin = float(Z[mask].min()) if mask.any() else 0.0
    hgt = np.where(mask, Z - zmin + smooth * 0.6, 0.0).astype(np.float32)
    b = _box(_box(hgt, smooth // 2 + 1), smooth // 2 + 1)
    gy, gx = np.gradient(b)
    gz = np.full_like(gx, 0.9)
    n = np.sqrt(gx * gx + gy * gy + gz * gz) + 1e-6
    gx, gy, gz = -gx / n, -gy / n, gz / n
    nx = local * NX + (1 - local) * gx
    ny = local * NY + (1 - local) * gy
    nz = local * NZ + (1 - local) * gz
    n = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    return nx / n, ny / n, nz / n


def shade(L, Z, NX, NY, NZ, n_tones: int, light=(-0.4, -0.8), lz: float = 0.45, ambient: float = 0.0,
          cast: float = 0.35, cast_len: int = 2, vgrad=None, dither: float = 0.55, base=None, base_dark: float = 0.0,
          smooth: int = 0, local: float = 0.4):
    """Tone index per pixel (0 darkest .. n_tones-1) and the mask.

    light (lx, ly) points from the cloud toward the light in screen space (y down), lz its height
    out of the screen. vgrad = (y_top, y_bottom, top_add, bottom_add) in layer pixels adds a
    vertical term. base = layer row of a flat base: pixels within 3 px above it get base_dark less."""
    mask = Z > -1e8
    NX, NY, NZ = form_normals(Z, mask, NX, NY, NZ, smooth, local)
    lx, ly = light
    ln = float(np.sqrt(lx * lx + ly * ly + lz * lz)) or 1.0
    lam = (NX * lx + NY * ly + NZ * lz) / ln
    v = 0.5 + 0.5 * lam + ambient
    if cast > 0:
        d2 = float(np.hypot(lx, ly)) or 1.0
        sx, sy = lx / d2, ly / d2
        sh = np.zeros_like(mask)
        for k in range(1, cast_len + 1):
            dx, dy = int(round(sx * k)), int(round(sy * k))
            zt = shift(Z, -dx, -dy, -1e9)              # the pixel k steps toward the light
            sh |= zt > Z + 1.5 * k
        v = v - cast * sh
    if vgrad is not None:
        y0, y1, a0, a1 = vgrad
        yy = np.arange(L.h, dtype=np.float32)[:, None]
        f = np.clip((yy - y0) / max(1.0, y1 - y0), 0.0, 1.0)
        v = v + a0 + (a1 - a0) * f
    if base is not None and base_dark > 0:
        yy = np.arange(L.h, dtype=np.float32)[:, None]
        v = v - base_dark * np.clip((yy - (base - 4)) / 4.0, 0.0, 1.0)
    idx = quantize(np.clip(v, 0.0, 0.999), n_tones, L.bayer, dither)
    return mask, idx


def rims(Z, mask, light=(-0.4, -0.8), inner: float = 3.0, width: int = 1):
    """One-pixel rims on the light side: of the silhouette (the neighbour toward the light is
    empty) and, if inner > 0, of each puff standing `inner` px in front of the one behind it."""
    d = float(np.hypot(*light)) or 1.0
    sx, sy = light[0] / d, light[1] / d
    out = np.zeros_like(mask)
    for k in range(1, width + 1):
        dx, dy = int(round(sx * k)), int(round(sy * k))
        nb = shift(mask, -dx, -dy, False)
        out |= mask & ~nb
        if inner > 0:
            zn = shift(Z, -dx, -dy, -1e9)
            out |= mask & nb & (zn < Z - inner)
    return out


def paint(L, mask, idx, tones, rim=None, rim_color=None, alpha=1.0):
    """Write the toned cloud into the layer (opaque inside the mask, times alpha)."""
    col = np.asarray(tones, np.float32)[idx]
    if rim is not None and rim_color is not None:
        col[rim] = np.asarray(rim_color, np.float32)
    a = mask.astype(np.float32) * alpha
    L.rgb *= (1.0 - a)[..., None]
    L.rgb += col * a[..., None]
    L.a *= 1.0 - a
    L.a += a
