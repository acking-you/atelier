"""The lyric line, drawn on the finished frame from the LRC stamps.

Off unless the environment variable HX_LYRICS is set (`--lyrics` on hx.still and hx.render):

    HX_LYRICS=<path to the .lrc file>   line text is read from that file at render time
    HX_LYRICS=placeholder               layout test: counting numerals of the same length

No line text lives in this package: a line is addressed by its 0-based LRC index, and the
timeline carries only stamps and character counts. A voice sings the line, so the whole line
is shown at once: it fades in just before its stamp and leaves at the blank stamp that closes
its phrase, or just before the next line.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import skia

from mv.engine import palette, prims
from mv.engine.palette import sk

ENV = "HX_LYRICS"
PLACEHOLDER = "placeholder"
_FILL = "一二三四五六七八九十"

SIZE = 52.0            # px at 1080p
TRACKING = 0.16        # em between characters
GROUP_GAP = 0.62       # em between the phrase groups of a line
BASELINE_Y = 0.888     # of the frame height
LEAD_S = 0.32          # fade-in ends on the stamp
FADE_S = 0.40
GAP_S = 0.10           # air before the next line's fade-in
RISE = 7.0             # px the line rises while it fades in
W, H = 1920, 1080


def source() -> str | None:
    return os.environ.get(ENV) or None


def _read_groups(path: Path) -> dict[int, list[str]]:
    out = {}
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines()):
        m = re.match(r"\[(\d+):(\d+(?:\.\d+)?)\](.*)", raw)
        if m and m.group(3).split():
            out[i] = m.group(3).split()
    return out


class Lyrics:
    def __init__(self, tl, src: str):
        text = None if src == PLACEHOLDER else _read_groups(Path(src))
        self.rows = []                                   # (t_in, t_out, groups)
        for k, c in enumerate(tl.cues):
            if text is None:
                it = iter(_FILL[i % len(_FILL)] for i in range(c.n_chars))
                groups = ["".join(next(it) for _ in range(n)) for n in c.groups]
            else:
                groups = text[c.lrc]
            t_out = c.t_end + 0.25
            if k + 1 < len(tl.cues):
                t_out = min(t_out, tl.cues[k + 1].t - LEAD_S - GAP_S)
            self.rows.append((c.t - LEAD_S, max(t_out, c.t + 1.0), groups))
        chars = "".join("".join(g) for _a, _b, g in self.rows) or "0"
        self.font = skia.Font(prims.resolve_typeface(prims.SERIF_CJK, chars, weight=600), SIZE)
        self.font.setSubpixel(True)
        self.font.setEdging(skia.Font.Edging.kAntiAlias)

    def active(self, t: float):
        return [r for r in self.rows if r[0] <= t < r[1]]

    def _layout(self, groups):
        xs, chars, x = [], [], 0.0
        for gi, g in enumerate(groups):
            if gi:
                x += SIZE * (GROUP_GAP - TRACKING)
            for ch, w in zip(g, self.font.getWidths(self.font.textToGlyphs(g))):
                xs.append(x)
                chars.append(ch)
                x += w + SIZE * TRACKING
        total = x - SIZE * TRACKING
        x0 = (W - total) / 2.0
        return chars, [x0 + v for v in xs], x0, x0 + total

    def draw(self, canvas: skia.Canvas, t: float, under_luma: float) -> None:
        """under_luma: mean luma 0..1 of the finished picture behind the line (sets the backing's strength)."""
        for t_in, t_out, groups in self.active(t):
            a_in = min(1.0, (t - t_in) / LEAD_S)
            fade = min(a_in, max(0.0, (t_out - t) / FADE_S))
            if fade <= 0.0:
                continue
            fade = fade * fade * (3.0 - 2.0 * fade)
            chars, xs, x0, x1 = self._layout(groups)
            y = H * BASELINE_Y + RISE * (1.0 - a_in) ** 2
            # a soft ink cloud behind the line; stronger the brighter the picture under it
            scrim = 0.22 + 0.40 * min(1.0, max(0.0, (under_luma - 0.18) / 0.42))
            pad_x, pad_y = SIZE * 1.3, SIZE * 0.40
            cloud = skia.Paint(AntiAlias=True, Color=sk(palette.INK, scrim * fade),
                               MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, SIZE * 0.55))
            canvas.drawRoundRect(skia.Rect.MakeLTRB(x0 - pad_x, y - SIZE * 0.86 - pad_y, x1 + pad_x,
                                                    y + SIZE * 0.14 + pad_y), SIZE, SIZE, cloud)
            halo = skia.Paint(AntiAlias=True, Color=sk(palette.INK, 0.70 * fade),
                              MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.5))
            edge = skia.Paint(AntiAlias=True, Color=sk(palette.INK, 0.50 * fade), Style=skia.Paint.kStroke_Style,
                              StrokeWidth=2.2, StrokeJoin=skia.Paint.kRound_Join)
            face = skia.Paint(AntiAlias=True, Color=sk(palette.PAPER, fade))
            for paint in (halo, edge, face):
                for ch, cx in zip(chars, xs):
                    canvas.drawString(ch, cx, y, self.font, paint)


_CACHE: dict = {}


def overlay(rgba: np.ndarray, tl, t: float, scale: float) -> np.ndarray:
    """The frame with the lyric line of time t drawn on it (a copy), or the frame itself."""
    src = source()
    if not src:
        return rgba
    subs = _CACHE.get(src)
    if subs is None:
        subs = _CACHE[src] = Lyrics(tl, src)
    if not subs.active(t):
        return rgba
    arr = np.array(rgba)
    h, w = arr.shape[:2]
    band = arr[int(h * 0.82):int(h * 0.92), int(w * 0.25):int(w * 0.75):4, :3]
    under = float(band.mean()) / 255.0
    c = skia.Surface(arr).getCanvas()
    c.scale(scale, scale)
    subs.draw(c, t, under)
    return arr
