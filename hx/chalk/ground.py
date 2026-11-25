"""hx.chalk.ground: the one ground line of the film.

Skirting board, classroom floor, kerb, horizon, the foot of the hills: always the SAME stroke (same
ends, same seed, same hand), so that it never jumps when the set around it changes. Every scene
draws it with ground_line(F); a set never draws a floor line of its own.
"""
from __future__ import annotations

import numpy as np

from .core import C, Frame, chalk

__all__ = ["GROUND_X", "GROUND_Y", "ground_line"]

GROUND_X = (-3000.0, 15000.0)     # its two ends in the world: fixed, so its wobble is fixed
GROUND_Y = 742.0
_XS = np.linspace(GROUND_X[0], GROUND_X[1], 901)


def ground_line(F: Frame, curve=None, a: float = 0.9, w: float = 4.2, col=None, span=None, seed: int = 20,
                grain: str = "dense"):
    """Draw the ground line. curve: None for the flat line at world y 742, or a function of an array
    of world x giving world y (a hill contour: it should be 742 where the land is flat). span =
    (xa, xb): only the part between these world x exists (drawing it on from a point, rubbing it
    out toward a point). col: default cold chalk at night, pencil in the day skin. Returns the
    world point of its right-hand tip."""
    ys = np.full_like(_XS, GROUND_Y) if curve is None else np.asarray(curve(_XS), dtype=np.float64)
    P = np.stack([_XS, ys], axis=1)
    f = (0.0, 1.0)
    if span is not None:
        L = GROUND_X[1] - GROUND_X[0]
        f = (min(1.0, max(0.0, (span[0] - GROUND_X[0]) / L)), min(1.0, max(0.0, (span[1] - GROUND_X[0]) / L)))
        if f[1] <= f[0]:
            return None
    col = F.pick(C.CHALK_COOL, C.PENCIL) if col is None else col
    return chalk(F, P, col, w, a, seed=seed, taper=1.0, draw=f, grain=grain)
