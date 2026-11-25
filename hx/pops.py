"""Pop scan: where does the picture jump from one frame to the next?

    PYTHONPATH=. .venv/bin/python -m hx.pops 36.27 58.60 [--workers 3] [--top 12] [--out hx/_review/pops]

Renders every frame of the span and measures each frame step two ways: the mean change of the whole
picture (levels of luma, 0..255) and the change of the worst 96 px block (a figure, a prop or a line
that jumps shows there even when the whole picture hardly changes). A step is listed when it stands
out from its neighbourhood (the 21 steps round it): the whole picture more than 3 times the local
median and over 2 levels, or the worst block more than 3.5 times its local median and over 28 levels.
Steps inside a pair of frames (the boil does not move there) are also listed when they change more
than 1.2 levels: something is not on twos, or acts.

Not every listed step is a fault: a hit of the band, a fast gesture and a camera jolt are meant.
The scan only says where to look. For the --top worst steps it writes a picture: before | after |
difference x 6, named by the time of the later frame.
"""
from __future__ import annotations

import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np

FPS = 30
LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
BLOCK = 96


def _chunk(job):
    f0, f1 = job
    from hx.chalk.core import Frame
    from hx.frame import Renderer
    r, prev, rows = Renderer(1.0), None, []
    for f in range(f0 - 1, f1):
        y = r.render_frame(f)[..., :3].astype(np.float32) @ LUMA
        if prev is not None:
            d = np.abs(y - prev)
            h, w = d.shape
            b = d[:h // BLOCK * BLOCK, :w // BLOCK * BLOCK].reshape(h // BLOCK, BLOCK, w // BLOCK, BLOCK).mean((1, 3))
            by, bx = np.unravel_index(int(b.argmax()), b.shape)
            t0, t1 = (f - 0.5) / FPS, (f + 0.5) / FPS
            rows.append((f, float(d.mean()), float(b.max()), int(bx) * BLOCK + BLOCK // 2, int(by) * BLOCK + BLOCK // 2,
                         int(Frame.boil_index(t0) == Frame.boil_index(t1))))
        prev = y
    return rows


def scan(t0: float, t1: float, workers: int = 3) -> np.ndarray:
    """Rows (frame, mean change, worst block, block x, block y, inside-pair flag) for every step into a frame of the span."""
    f0, f1 = max(1, int(round(t0 * FPS))), int(round(t1 * FPS))
    workers = max(1, min(workers, (f1 - f0) // 30 or 1))
    cuts = [f0 + (f1 - f0) * i // workers for i in range(workers + 1)]
    jobs = [(cuts[i], cuts[i + 1]) for i in range(workers) if cuts[i + 1] > cuts[i]]
    if len(jobs) == 1:
        parts = [_chunk(jobs[0])]
    else:
        with mp.get_context("spawn").Pool(len(jobs)) as p:
            parts = p.map(_chunk, jobs)
    return np.asarray([row for part in parts for row in part], dtype=np.float64)


def flags(rows: np.ndarray) -> list[tuple]:
    out = []
    n = len(rows)
    for i in range(n):
        lo, hi = max(0, i - 10), min(n, i + 11)
        same = rows[lo:hi][rows[lo:hi, 5] == rows[i, 5]]
        med_m = float(np.median(same[:, 1])) if len(same) else 0.0
        med_b = float(np.median(same[:, 2])) if len(same) else 0.0
        f, m, b, bx, by, inside = rows[i]
        why = []
        if m > max(2.0, 3.0 * med_m):
            why.append(f"picture {m:.2f} (local {med_m:.2f})")
        if b > max(28.0, 3.5 * med_b):
            why.append(f"block {b:.0f} at ({int(bx)}, {int(by)}) (local {med_b:.0f})")
        if inside and m > 1.2 and not why:
            why.append(f"inside a pair {m:.2f}")
        if why:
            out.append((int(f), (f + 0.5) / FPS, m, b, "; ".join(why)))
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)

    def opt(name, default, cast):
        if name in argv:
            i = argv.index(name)
            v = cast(argv[i + 1])
            del argv[i:i + 2]
            return v
        return default

    workers, top = opt("--workers", 3, int), opt("--top", 12, int)
    out = Path(opt("--out", "hx/_review/pops", str))
    t0, t1 = float(argv[0]), float(argv[1])
    rows = scan(t0, t1, workers)
    fl = flags(rows)
    steps, inside = rows[rows[:, 5] == 0], rows[rows[:, 5] == 1]
    print(f"{t0:.2f}-{t1:.2f}: {len(rows) + 1} frames; boil steps mean {steps[:, 1].mean() if len(steps) else 0:.2f} levels, "
          f"inside pairs mean {inside[:, 1].mean() if len(inside) else 0:.2f}; {len(fl)} steps stand out")
    for f, t, m, b, why in fl:
        print(f"  t={t:8.3f} frame {f:5d}: {why}")
    if fl and top > 0:
        from PIL import Image

        from hx.frame import Renderer
        out.mkdir(parents=True, exist_ok=True)
        r = Renderer(1.0)
        worst = sorted(fl, key=lambda x: -(x[2] / 2.0 + x[3] / 28.0))[:top]
        for f, t, m, b, why in worst:
            a, c = r.render_frame(f - 1)[..., :3].copy(), r.render_frame(f)[..., :3].copy()
            d = np.clip(np.abs(a.astype(np.float32) @ LUMA - c.astype(np.float32) @ LUMA) * 6.0, 0, 255).astype(np.uint8)
            pic = np.hstack([a[::2, ::2], c[::2, ::2], np.repeat(d[::2, ::2, None], 3, axis=2)])
            Image.fromarray(pic).save(out / f"pop_{t:08.3f}.jpg", quality=88)
        print(f"  pictures of the {len(worst)} worst: {out}/pop_<time>.jpg")
    return fl


if __name__ == "__main__":
    main()
