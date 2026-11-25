"""Flicker and smoothness check, at full resolution, on an encoded clip or on freshly rendered frames.

    python -m hx.motion output/x.mp4 [more.mp4 ...]     # decode (mv.encode.FFMPEG) and measure
    python -m hx.motion 58.6 80.5 [t0 t1 ...]           # render those seconds (no lyric line) and measure

For each pair of consecutive frames: the mean absolute luma difference in levels (0..255) and the
share of pixels that move by more than 8 levels. The picture boils on twos, so the changes are
reported apart: on a boil step (between two pairs) and inside a pair (the two frames that share a
boil index; the parity is found from the data). For a static camera the kit's targets are: boil
step under 1.2 levels mean and under 6 percent of pixels; inside a pair essentially zero. Rain, a
churning scribble or a camera move add to it; a hard cut measures 10 to 40 levels.
"""
from __future__ import annotations

import multiprocessing as mp
import subprocess
import sys
from pathlib import Path

import numpy as np

W, H, FPS = 1920, 1080, 30
LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def _diff(a: np.ndarray, b: np.ndarray):
    d = np.abs(a - b)
    return float(d.mean()), float((d > 8.0).mean() * 100.0)


def measure_file(path) -> np.ndarray:
    """Rows (mean abs luma difference, percent of pixels over 8 levels) for each consecutive frame pair."""
    from mv.encode import FFMPEG
    proc = subprocess.Popen([FFMPEG, "-hide_banner", "-loglevel", "error", "-i", str(path), "-f", "rawvideo",
                             "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    out, prev, n = [], None, W * H * 3
    while True:
        buf = proc.stdout.read(n)
        if len(buf) < n:
            break
        y = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 3).astype(np.float32) @ LUMA
        if prev is not None:
            out.append(_diff(prev, y))
        prev = y
    proc.wait()
    return np.asarray(out)


def _render_chunk(rng):
    from hx.frame import Renderer
    r, out, prev = Renderer(1.0), [], None
    for f in range(rng[0], rng[1] + rng[2]):                     # one frame more: the step into the next chunk
        y = r.render_frame(f)[..., :3].astype(np.float32) @ LUMA
        if prev is not None:
            out.append(_diff(prev, y))
        prev = y
    return out


def measure_render(t0: float, t1: float, workers: int = 8) -> np.ndarray:
    f0, f1 = int(t0 * FPS) // 2 * 2, int(t1 * FPS)
    cuts = [f0 + (f1 - f0) * i // workers for i in range(workers + 1)]
    with mp.get_context("spawn").Pool(workers) as p:
        parts = p.map(_render_chunk, [(cuts[i], cuts[i + 1], int(i + 1 < workers)) for i in range(workers)
                                      if cuts[i + 1] > cuts[i]])
    return np.asarray([row for part in parts for row in part])


def summary(d: np.ndarray) -> dict:
    """Split the frame-to-frame changes into boil steps and inside-pair changes (lower parity = inside)."""
    a, b = d[0::2], d[1::2]
    if a[:, 0].mean() > b[:, 0].mean():
        a, b = b, a
    f = lambda x: dict(mean=float(x[:, 0].mean()), p95=float(np.percentile(x[:, 0], 95)), max=float(x[:, 0].max()),
                       share=float(x[:, 1].mean()), share_max=float(x[:, 1].max()))
    return dict(frames=len(d) + 1, pair=f(a), step=f(b))


def report(src, d: np.ndarray | None = None) -> str:
    d = measure_file(src) if d is None else d
    s = summary(d)
    size = f", {Path(src).stat().st_size / 1e6:.1f} MB" if Path(str(src)).exists() else ""
    line = (f"{Path(str(src)).name}: {s['frames']} frames{size}\n"
            f"   boil step   : mean {s['step']['mean']:.2f} levels (p95 {s['step']['p95']:.2f}, max {s['step']['max']:.2f}), "
            f"pixels over 8 levels {s['step']['share']:.2f} % (max {s['step']['share_max']:.2f} %)\n"
            f"   inside pair : mean {s['pair']['mean']:.3f} levels (max {s['pair']['max']:.3f}), "
            f"pixels over 8 levels {s['pair']['share']:.3f} % (max {s['pair']['share_max']:.3f} %)")
    print(line)
    return line


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and not args[0].replace(".", "").isdigit():
        for path in args:
            report(path)
    else:
        for a, b in zip(args[0::2], args[1::2]):
            report(f"{a}-{b} s", measure_render(float(a), float(b)))
