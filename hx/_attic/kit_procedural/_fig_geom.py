"""Private geometry helpers for hx.kit.figures and hx.kit.birds (smooth and straight outlines, tapered limbs)."""
from __future__ import annotations

import math

import numpy as np
import skia


def dirv(a: float) -> np.ndarray:
    """Unit vector at angle a measured from straight down, positive toward +x (local y is up)."""
    return np.array((math.sin(a), -math.cos(a)))


def rot(v, a: float) -> np.ndarray:
    """Rotate vectors (..., 2) by a (positive = clockwise in the y-up frame, i.e. tip forward)."""
    c, s = math.cos(a), math.sin(a)
    v = np.asarray(v, dtype=np.float64)
    return np.stack([v[..., 0] * c + v[..., 1] * s, -v[..., 0] * s + v[..., 1] * c], axis=-1)


def closed_path(P, path: skia.Path | None = None) -> skia.Path:
    """Closed Catmull-Rom curve through the points (N, 2) as cubic segments."""
    P = np.asarray(P, dtype=np.float64)
    Q = np.concatenate((P[-1:], P, P[:2]))          # prv | P | nxt, nx2 by slicing
    n = len(P)
    prv, nxt, nx2 = Q[:n], Q[2:n + 2], Q[3:n + 3]
    seg = np.concatenate((P + (nxt - prv) / 6.0, nxt - (nx2 - P) / 6.0, nxt), axis=1).tolist()
    path = path if path is not None else skia.Path()
    path.moveTo(float(P[0, 0]), float(P[0, 1]))
    cub = path.cubicTo
    for r in seg:
        cub(r[0], r[1], r[2], r[3], r[4], r[5])
    path.close()
    return path


def poly_path(P) -> skia.Path:
    """Closed polygon through the points (straight edges: hair spikes, hard corners)."""
    P = np.asarray(P, dtype=np.float64)
    path = skia.Path()
    path.addPoly([skia.Point(float(x), float(y)) for x, y in P], True)
    return path


def segment(a, b, ra: float, rb: float, bulge: float = 0.0, bulge_b: float | None = None) -> np.ndarray:
    """Outline points of a tapered capsule from a (radius ra) to b (radius rb).

    bulge widens the middle on the +normal side (a calf, a sleeve fold), bulge_b on the other.
    The outline always runs the same way round, so pieces union cleanly.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    d = b - a
    L = math.hypot(d[0], d[1]) or 1e-6
    t = d / L
    n = np.array((-t[1], t[0]))
    m = (a + b) * 0.5
    rm = (ra + rb) * 0.5
    bb = bulge if bulge_b is None else bulge_b
    return np.array([
        a - t * ra,
        a + n * ra * 0.72 - t * ra * 0.72,
        a + n * ra,
        m + n * (rm + bulge * L),
        b + n * rb,
        b + n * rb * 0.72 + t * rb * 0.72,
        b + t * rb,
        b - n * rb * 0.72 + t * rb * 0.72,
        b - n * rb,
        m - n * (rm + bb * L),
        a - n * ra,
        a - n * ra * 0.72 - t * ra * 0.72,
    ])


def frame_pts(origin, fx, fy, local, sx: float = 1.0, sy: float | None = None) -> np.ndarray:
    """Map local (x, y) points into a frame with axes fx, fy at origin, scaled."""
    L = np.asarray(local, dtype=np.float64)
    sy = sx if sy is None else sy
    return np.asarray(origin) + np.outer(L[:, 0] * sx, fx) + np.outer(L[:, 1] * sy, fy)


def lerp_pts(a, b, w: float) -> np.ndarray:
    return np.asarray(a, dtype=np.float64) * (1.0 - w) + np.asarray(b, dtype=np.float64) * w
