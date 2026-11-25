"""frame(t): every picture of the film is a pure function of the recording's time.

    r = Renderer(scale=0.5)
    rgba = r.render(61.2)          # (h, w, 4) uint8
    rgba = r.render_frame(1836)    # frame n is sampled at (n + 0.5) / 30

For each frame the Renderer builds the hx.chalk Frame (night paper, identity camera), calls the scene
whose SPAN holds the time (hx/scenes), runs the kit's finish (bloom, vignette, fade, grain), draws
the sharp overlays a scene asked for, resizes, and draws the lyric line last. The picture is always
drawn at 1920x1080 (the paper's tooth is made of device pixels); `scale` only sizes what is returned.
See hx/chalk/README.md.
"""
from __future__ import annotations

import numpy as np
import skia
from PIL import Image

from mv.engine import prims

from . import lyrics
from .chalk.core import FPS, H, W, Frame
from .timeline import get_timeline


def frame_time(n: int) -> float:
    return (n + 0.5) / FPS


class Renderer:
    def __init__(self, scale: float = 1.0, debug: bool = False):
        self.tl = get_timeline()
        self.scale, self.debug = float(scale), debug
        self.w, self.h = int(round(W * scale)), int(round(H * scale))
        self.surface = skia.Surface(W, H)

    def render_frame(self, n: int) -> np.ndarray:
        return self.render(frame_time(n))

    def frame(self, t: float) -> Frame:
        """The drawn, unfinished Frame at t (for tools that want to look inside)."""
        from . import scenes
        F = Frame(min(max(0.0, t), self.tl.duration), "night", self.tl, surface=self.surface)
        scenes.draw(F)
        return F

    def render(self, t: float) -> np.ndarray:
        """The finished frame at t: the picture, sharp overlays, then the lyric line."""
        F = self.frame(t)
        out = F.finish()
        if F.overlays:
            c = skia.Surface(out).getCanvas()
            for fn in F.overlays:
                fn(c)
        if (self.w, self.h) != (W, H):
            out = np.asarray(Image.fromarray(out).resize((self.w, self.h), Image.LANCZOS))
        out = lyrics.overlay(out, self.tl, t, self.scale)
        if self.debug:
            out = self._overlay(out, t)
        return out

    def _overlay(self, rgba: np.ndarray, t: float) -> np.ndarray:
        """The debug strip. Numbers only: section id, bar.beat, time, frame, LRC index."""
        arr = np.array(rgba)
        c = skia.Surface(arr).getCanvas()
        c.scale(self.scale, self.scale)
        tl = self.tl
        sec = tl.section_at(min(t, tl.duration))
        bar, bb, _f = tl.bar_at(t)
        _k, bf = tl.beat_at(t)
        cue = tl.cue_at(t)
        c.drawRect(skia.Rect.MakeLTRB(0, 0, 900, 54), skia.Paint(Color=0xB0000000))
        c.drawCircle(30, 27, 15.0 * (1.0 - bf) ** 2 + 5.0,
                     skia.Paint(AntiAlias=True, Color=0xFFFF5040 if bb == 0 else 0xFFFFFFFF))
        font = skia.Font(prims.resolve_typeface(("Menlo", "Courier New", "Helvetica Neue"), "0123456789"), 26)
        label = (f"{sec.id} bar {bar:02d}.{bb + 1}  t {t:7.3f}  f {int(t * FPS):05d}"
                 f"  lrc {cue.lrc if cue else '--'}")
        c.drawString(label, 60, 36, font, skia.Paint(AntiAlias=True, Color=0xFFFFFFFF))
        return arr


_RENDERERS: dict = {}


def get_renderer(scale: float = 1.0, debug: bool = False) -> Renderer:
    key = (round(scale, 4), debug)
    if key not in _RENDERERS:
        _RENDERERS[key] = Renderer(scale, debug)
    return _RENDERERS[key]
