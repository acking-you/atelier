"""Proof pictures and clips of kit pieces, without a scene module.

    from hx.chalk import *
    from hx.chalk.proof import still, sheet, clip, flicker

    def d(F):                                  # any draw function of a Frame, as in a scene
        F.cam = Cam.at(900, 600, 1.4)
        figure(F, 900, 742, 380, STAND, "child", seed=3)

    still(d, 14.0, "hx/_review/v4_kit/figure/stand.png")                    # one finished frame at 14.0 s
    sheet(d, [14.0 + i / 15 for i in range(12)], "…/stand_12.jpg", cols=4)   # contact sheet, time labels
    sheet(d, 12, "…/x.jpg", t0=14.0, t1=16.0)                                # 12 frames spread over a stretch
    clip(d, 14.0, 20.0, "…/stand.mp4")                                       # 30 fps h264, one process
    print(flicker(d, 14.0, 17.0))                                            # boil-step / inside-pair numbers

`skin="day"` starts the frame on the warm paper. `crop=(l, t, r, b)` in screen px cuts the result
(stills and sheet tiles), so that a small thing can be shown at 100 percent. Sheets label each tile
with its time only (numbers, never words of the song).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import skia
from PIL import Image, ImageDraw

from .core import FPS, H, W, Frame

LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
_SURF: list = []


def frame(draw, t: float, skin: str = "night") -> np.ndarray:
    """The finished RGB frame (H, W, 3) of draw(F) at time t."""
    if not _SURF:
        _SURF.append(skia.Surface(W, H))
    F = Frame(float(t), skin, surface=_SURF[0])
    draw(F)
    out = F.finish()
    if F.overlays:
        c = skia.Surface(out).getCanvas()
        for fn in F.overlays:
            fn(c)
    return np.ascontiguousarray(out[..., :3])


def _cut(arr, crop):
    if crop is None:
        return arr
    l, t, r, b = (int(v) for v in crop)
    return arr[max(0, t):min(H, b), max(0, l):min(W, r)]


def still(draw, t: float, path, skin: str = "night", crop=None) -> np.ndarray:
    arr = _cut(frame(draw, t, skin), crop)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path)
    return arr


def sheet(draw, times, path, cols: int = 4, tile=(640, 360), skin: str = "night", crop=None,
          t0: float | None = None, t1: float | None = None, label: bool = True) -> None:
    """Contact sheet. `times`: a list of times, or a count spread evenly over t0..t1.
    `draw` may also be a list of draw functions as long as `times` (one picture each)."""
    if isinstance(times, int):
        times = [t0 + (t1 - t0) * i / max(1, times - 1) for i in range(times)]
    draws = draw if isinstance(draw, (list, tuple)) else [draw] * len(times)
    tw, th = tile
    rows = (len(times) + cols - 1) // cols
    out = Image.new("RGB", (cols * tw + (cols + 1) * 4, rows * th + (rows + 1) * 4), (0, 0, 0))
    for i, (d, t) in enumerate(zip(draws, times)):
        im = Image.fromarray(_cut(frame(d, t, skin), crop)).resize((tw, th), Image.LANCZOS)
        if label:
            g = ImageDraw.Draw(im)
            g.rectangle((0, 0, 86, 18), fill=(0, 0, 0))
            g.text((4, 3), f"{t:8.3f}", fill=(255, 255, 255))
        out.paste(im, (4 + (i % cols) * (tw + 4), 4 + (i // cols) * (th + 4)))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    out.save(path, quality=90)


def _frames(draw, t0: float, t1: float, skin: str):
    for n in range(int(round(t0 * FPS)), int(round(t1 * FPS))):
        yield frame(draw, (n + 0.5) / FPS, skin)


def clip(draw, t0: float, t1: float, path, skin: str = "night", crf: int = 18) -> None:
    """A silent 30 fps clip of draw(F) over t0..t1 (frame times as in the film)."""
    from mv.encode import FFMPEG
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                             "-preset", "veryfast", "-crf", str(crf), str(path)], stdin=subprocess.PIPE)
    for arr in _frames(draw, t0, t1, skin):
        proc.stdin.write(arr.tobytes())
    proc.stdin.close()
    proc.wait()


def flicker(draw, t0: float, t1: float, skin: str = "night") -> dict:
    """Frame-to-frame change of the rendered frames: mean abs luma difference (levels) and percent of
    pixels over 8 levels, on boil steps and inside the pairs. Motion counts too: measure a still stretch.
    Targets: under 1.2 levels and 6 percent on a boil step, about zero inside a pair."""
    step, inside, prev, pk = [], [], None, None
    for n in range(int(round(t0 * FPS)), int(round(t1 * FPS))):
        t = (n + 0.5) / FPS
        k = Frame.boil_index(t)
        y = frame(draw, t, skin).astype(np.float32) @ LUMA
        if prev is not None:
            d = np.abs(y - prev)
            (inside if k == pk else step).append((float(d.mean()), float((d > 8.0).mean() * 100.0)))
        prev, pk = y, k
    s, i = np.asarray(step or [(0, 0)]), np.asarray(inside or [(0, 0)])
    return {"step_levels": round(float(s[:, 0].mean()), 3), "step_pct_over8": round(float(s[:, 1].mean()), 2),
            "step_max": round(float(s[:, 0].max()), 3), "inside_levels": round(float(i[:, 0].mean()), 3),
            "inside_max": round(float(i[:, 0].max()), 3), "frames": len(step) + len(inside) + 1}
