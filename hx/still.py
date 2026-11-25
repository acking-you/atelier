"""Stills and contact sheets.

    python -m hx.still --t 61.2 --out hx/_review/x.jpg [--scale 0.5] [--debug] [--lyrics placeholder]
    python -m hx.still --sheet v1a,v1b --n 8 --out hx/_review/v1.jpg      # n frames spread over those sections
    python -m hx.still --sheet 58.6:80.5 --n 12 --out hx/_review/c1.jpg   # or over a time range
    python -m hx.still --video output/x.mp4 --sheet 0:258 --n 24 --out hx/_review/film.jpg   # from an encoded file

The picture is drawn by hx.chalk at 1920x1080 and resized by --scale (1.0 to judge the chalk at 100
percent). A sheet tile is 480 px wide with its time and section id burnt in; --cols sets the grid.
"""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from . import lyrics
from .frame import get_renderer
from .timeline import get_timeline


def save(rgb: np.ndarray, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb[..., :3]).save(out, quality=90)


def _times(tl, spec: str, n: int) -> list[float]:
    if ":" in spec:
        a, b = (float(x) for x in spec.split(":"))
    else:
        ids = spec.split(",")
        a, b = tl.section(ids[0]).t0, tl.section(ids[-1]).t1
    b = min(b, tl.duration - 0.05)
    return [a + (b - a) * (i + 0.5) / n for i in range(n)]


def _video_frame(path: str, t: float, w: int, h: int) -> np.ndarray:
    from mv.encode import FFMPEG
    raw = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                          "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--t", type=float)
    ap.add_argument("--sheet", help="section ids 'a,b' (first to last) or a time range 't0:t1'")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--lyrics", metavar="LRC")
    ap.add_argument("--video", help="take the sheet's frames from this encoded file instead of rendering")
    a = ap.parse_args(argv)
    if a.lyrics:
        os.environ[lyrics.ENV] = a.lyrics
    tl = get_timeline()
    if a.sheet is None:
        save(get_renderer(a.scale, a.debug).render(a.t), Path(a.out))
        return
    tw, th = 480, 270
    times = _times(tl, a.sheet, a.n)
    rows = (len(times) + a.cols - 1) // a.cols
    sheet = Image.new("RGB", (a.cols * tw, rows * th))
    r = None if a.video else get_renderer(0.25, a.debug)
    for i, t in enumerate(times):
        img = Image.fromarray(_video_frame(a.video, t, tw, th) if a.video else r.render(t)[..., :3])
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, 92, 15), fill=(0, 0, 0))
        d.text((3, 2), f"{t:7.2f} {tl.section_at(t).id}", fill=(255, 255, 255))
        sheet.paste(img, ((i % a.cols) * tw, (i // a.cols) * th))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out, quality=88)


if __name__ == "__main__":
    main()
