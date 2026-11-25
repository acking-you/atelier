"""Hand-off check: is the frame after each hand-off the same picture as the frame before it?

    PYTHONPATH=. .venv/bin/python -m hx.handoff [B3 B4 ...] [--out hx/_review/handoff]

For every hand-off time in hx/story.py it renders the last frame of the earlier module and the
first frame of the later one (consecutive frames of the film) and, for comparison, the two frame
steps before and after. A clean hand-off changes no more than its neighbours do (a boil step, a
breath): the numbers of the middle column should sit between those of the outer ones. It writes a
picture per hand-off: before | after | difference x 8, and prints mean change (levels), share of
pixels over 8 levels, and the worst 96 px block (where a pop would be).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

from .frame import FPS, Renderer
from .story import HANDOFF

LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def _stats(a, b):
    d = np.abs(a.astype(np.float32) @ LUMA - b.astype(np.float32) @ LUMA)
    h, w = d.shape
    blocks = d[:h // 96 * 96, :w // 96 * 96].reshape(h // 96, 96, w // 96, 96).mean((1, 3))
    by, bx = np.unravel_index(int(blocks.argmax()), blocks.shape)
    return float(d.mean()), float((d > 8).mean() * 100), float(blocks.max()), (int(bx) * 96 + 48, int(by) * 96 + 48), d


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    out = Path("hx/_review/handoff")
    if "--out" in argv:
        i = argv.index("--out")
        out = Path(argv[i + 1])
        del argv[i:i + 2]
    out.mkdir(parents=True, exist_ok=True)
    names = argv or list(HANDOFF)
    r = Renderer(1.0)
    worst = 0.0
    for name in names:
        t = HANDOFF[name]["t"]
        n = int(np.ceil(t * FPS - 0.5))          # first frame whose time (n + 0.5) / FPS is >= t
        fr = {k: r.render_frame(k)[..., :3].copy() for k in range(n - 3, n + 3)}
        rows = []
        for k in range(n - 2, n + 3):
            m, share, blk, at, d = _stats(fr[k - 1], fr[k])
            rows.append((k, m, share, blk, at))
            if k == n:
                diff = np.clip(d * 8.0, 0, 255).astype(np.uint8)
                pic = np.hstack([fr[k - 1][::2, ::2], fr[k][::2, ::2], np.repeat(diff[::2, ::2, None], 3, axis=2)])
                Image.fromarray(pic).save(out / f"{name}_{t:.2f}.jpg", quality=90)
        base = max(x[1] for x in rows if x[0] != n)
        baseb = max(x[3] for x in rows if x[0] != n)
        mid = next(x for x in rows if x[0] == n)
        flag = "ok" if mid[1] <= max(1.2, base * 1.5) and mid[3] <= max(6.0, baseb * 1.8) else "POP"
        worst = max(worst, mid[1])
        print(f"{name} t={t:7.2f} frame {n}: change {mid[1]:5.2f} levels, {mid[2]:5.2f} % over 8, worst block {mid[3]:5.1f} at {mid[4]}"
              f"   (neighbours: {base:4.2f} levels, block {baseb:4.1f})   {flag}")
    return worst


if __name__ == "__main__":
    main()
