"""The spec palette and OKLab helpers.

Colours are plain (r, g, b) float tuples in sRGB 0..1. Convert with `sk()` only
at the moment of painting. All blends go through OKLab so that gradients keep
their chroma and never pass through grey mud.
"""
from __future__ import annotations

import numpy as np

RGB = tuple[float, float, float]


def hex_rgb(h: str) -> RGB:
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)


# ---- spec palette (creative_spec.mv.palette) ------------------------------
INK = hex_rgb("0E1320")          # ink-night: walker, nearest foreground; the black floor
INDIGO = hex_rgb("1B2440")
DUSK = hex_rgb("34406B")
HEATHER = hex_rgb("6B5B8E")
ROSE = hex_rgb("C7566B")
PERSIMMON = hex_rgb("F0834D")
AMBER = hex_rgb("F7C873")
PAPER = hex_rgb("E9D9BC")
SAND_LIT = hex_rgb("B9A27E")
SAND_SHADOW = hex_rgb("7C6650")
SLATE = hex_rgb("4F6D7A")
RAIN = hex_rgb("8FB3B8")
MINT = hex_rgb("7FD1C7")
SCARF = hex_rgb("D9503F")
SIENNA = hex_rgb("A8673F")
COLLAR = hex_rgb("23262B")

BLACK_FLOOR = (0x0E, 0x13, 0x20)  # per-channel 8-bit floor applied by post

NAMES = {
    "ink": INK, "indigo": INDIGO, "dusk": DUSK, "heather": HEATHER, "rose": ROSE,
    "persimmon": PERSIMMON, "amber": AMBER, "paper": PAPER, "sand_lit": SAND_LIT,
    "sand_shadow": SAND_SHADOW, "slate": SLATE, "rain": RAIN, "mint": MINT,
    "scarf": SCARF, "sienna": SIENNA, "collar": COLLAR,
}


# ---- OKLab -----------------------------------------------------------------
_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])
_M1I = np.linalg.inv(_M1)
_M2I = np.linalg.inv(_M2)


def srgb_to_linear(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, dtype=np.float64), 0.0, None)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def to_oklab(rgb):
    """sRGB (..., 3) -> OKLab (..., 3)."""
    lms = srgb_to_linear(rgb) @ _M1.T
    return np.cbrt(lms) @ _M2.T


def from_oklab(lab):
    """OKLab (..., 3) -> sRGB (..., 3), clipped to gamut."""
    lms = (np.asarray(lab, dtype=np.float64) @ _M2I.T) ** 3
    return np.clip(linear_to_srgb(lms @ _M1I.T), 0.0, 1.0)


def mix(a: RGB, b: RGB, w: float) -> RGB:
    """OKLab interpolation a -> b by w in 0..1."""
    w = float(min(1.0, max(0.0, w)))
    if w <= 0.0:
        return tuple(a)
    if w >= 1.0:
        return tuple(b)
    lab = to_oklab(a) * (1.0 - w) + to_oklab(b) * w
    return tuple(float(x) for x in from_oklab(lab))


def mix_many(cols_a, cols_b, w: float):
    """OKLab blend of two equal-length colour lists."""
    return [mix(a, b, w) for a, b in zip(cols_a, cols_b)]


def shade(c: RGB, dl: float = 0.0, chroma: float = 1.0) -> RGB:
    """Shift OKLab lightness by dl and scale chroma (atmospheric perspective knob)."""
    lab = to_oklab(c).copy()
    lab[0] = lab[0] + dl
    lab[1:] *= chroma
    return tuple(float(x) for x in from_oklab(lab))


def ramp(colors, positions=None, n: int = 24):
    """Resample colour stops through OKLab into n evenly spaced sRGB stops.

    Returns (list[RGB], list[float]) ready for a skia gradient, so that the
    gradient is perceptually interpolated even though skia lerps in sRGB.
    """
    colors = [tuple(c) for c in colors]
    k = len(colors)
    if positions is None:
        positions = np.linspace(0.0, 1.0, k)
    positions = np.asarray(positions, dtype=np.float64)
    lab = to_oklab(np.array(colors))
    xs = np.linspace(0.0, 1.0, n)
    out = np.stack([np.interp(xs, positions, lab[:, i]) for i in range(3)], axis=1)
    rgb = from_oklab(out)
    return [tuple(float(v) for v in row) for row in rgb], [float(x) for x in xs]


def sk(c: RGB, a: float = 1.0) -> int:
    """(r, g, b) + alpha -> 0xAARRGGBB int accepted by every skia call."""
    r, g, b = c[0], c[1], c[2]
    ai = int(round(min(1.0, max(0.0, a)) * 255))
    ri = int(round(min(1.0, max(0.0, r)) * 255))
    gi = int(round(min(1.0, max(0.0, g)) * 255))
    bi = int(round(min(1.0, max(0.0, b)) * 255))
    return (ai << 24) | (ri << 16) | (gi << 8) | bi


def luma(c: RGB) -> float:
    return float(to_oklab(c)[0])
