"""hx.chalk.title: the title and the credit lines, written in chalk in the upper middle.

The text is read from hx/credits.py (the materials) at render time; none of it is typed here. The
glyph outlines are filled through the chalk tooth with a slightly uneven pressure and a dusty edge,
on the frame itself (before bloom and grain), in screen space whatever the camera does.
A scene calls title.draw(F); the Renderer does not.
"""
from __future__ import annotations

import skia

from mv.engine import prims

from .. import credits
from .core import C, Frame, ramp, rnd, rsym

FAMILIES = ("Kaiti SC", "STKaiti", "Songti SC", "STHeiti")
TITLE_PX, CRED_PX = 62.0, 27.0
_LINES: dict = {}


def _line(parts, size: float, tracking: float, gaps, cx: float, y: float, seed: int):
    """Glyph outlines of `parts` (strings set on one line, `gaps` em between them), centred on (cx, y):
    [(path, pressure), ...], each glyph a little off the line as a hand writes."""
    key = (tuple(parts), size, tracking, tuple(gaps), cx, y, seed)
    if key not in _LINES:
        font = skia.Font(prims.resolve_typeface(FAMILIES, "".join(parts)), size)
        font.setSubpixel(True)
        cells, x = [], 0.0
        for i, part in enumerate(parts):
            if i:
                x += size * (gaps[(i - 1) % len(gaps)] - tracking)
            glyphs = font.textToGlyphs(part)
            for g, w in zip(glyphs, font.getWidths(glyphs)):
                cells.append((g, x, w))
                x += w + size * tracking
        x0 = cx - (x - size * tracking) / 2.0
        out = []
        for i, (g, gx, w) in enumerate(cells):
            p = font.getPath(g)
            if p is None or p.isEmpty():
                continue
            m = skia.Matrix()
            m.setRotate(1.6 * rsym(seed + i, 1), w / 2.0, -size * 0.36)
            m.postTranslate(x0 + gx + size * 0.012 * rsym(seed + i, 2), y + size * 0.36 + size * 0.022 * rsym(seed + i, 3))
            q = skia.Path()
            p.transform(m, q)
            out.append((q, 0.80 + 0.20 * rnd(seed + i, 4)))
        _LINES[key] = out
    return _LINES[key]


def _chalk(F: Frame, line, col, a: float, edge_w: float, t_in: float, stagger: float):
    """Each glyph arrives a moment after the one before it (written, not switched on)."""
    for i, (path, press) in enumerate(line):
        k = a * ramp(t_in, i * stagger, i * stagger + 0.5)
        if k > 0.01:
            F.c.drawPath(path, F.pen(col, edge_w, 0.30 * k * press, "sparse"))
            F.c.drawPath(path, F.paint(col, k * press, "mid"))


def draw(F: Frame, t0: float = 2.0, t1: float = 10.5, y: float = 150.0, cx: float = 960.0) -> None:
    """The title (centre about screen y) and the credit lines under it, visible from t0 to t1 with a soft fade."""
    t = F.t
    if not (t0 < t < t1):
        return
    out = 1.0 - ramp(t, t1 - 1.7, t1)
    col = F.pick(C.CHALK, C.PENCIL)
    _chalk(F, _line((credits.title(),), TITLE_PX, 0.30, (), cx, y, 11), col, 0.95 * out, 2.4, t - t0, 0.10)
    tc = t - t0 - 0.9
    if tc > 0.0:
        _chalk(F, _line((credits.artist(),), CRED_PX, 0.34, (), cx, y + 80.0, 31), col, 0.80 * out, 1.5, tc, 0.05)
        parts = [s for pair in credits.roles()[:2] for s in pair]
        if parts:
            _chalk(F, _line(parts, CRED_PX * 0.86, 0.26, (1.0, 2.2), cx, y + 126.0, 51), col, 0.70 * out, 1.4, tc - 0.3, 0.03)
