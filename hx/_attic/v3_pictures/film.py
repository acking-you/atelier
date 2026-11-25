"""The whole film: one picture per shot (hx/shots.py, pictures in hx/art/), a slow camera, and
drawn weather and light on top. See hx/DESIGN.md."""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
from scipy import ndimage as ndi

from mv.engine import prims
from mv.engine.palette import sk

from .. import credits
from ..kit import lights, look
from ..shots import PALE, SHOTS, index_at, span
from ..timeline import smoothstep

SECTIONS = ("intro", "v1a", "v1b", "p1a", "p1b", "hush1", "c1a", "c1b", "inter", "v2a", "v2b", "p2a", "p2b",
            "c2a", "c2b", "br_a", "br_b", "br_c", "bd", "hush2", "c3a", "c3b", "out", "coda")

ART = Path(__file__).resolve().parent.parent / "art"
W, H = 1920.0, 1080.0
COLD_RAIN = (0.74, 0.82, 0.96)
K = 0.6                         # drawn weather uses 3-unit pixels, the size of the pictures' own
SAMPLING = skia.SamplingOptions(skia.CubicResampler.CatmullRom())
TITLE_PX, CRED_PX = 62.0, 27.0


@lru_cache(maxsize=6)
def _art(name: str) -> skia.Image:
    img = skia.Image.open(str(ART / f"{name}.png"))
    if img is None:
        raise FileNotFoundError(f"hx/art/{name}.png")
    return img.makeRasterImage()


def _ease(kind: str, u: float) -> float:
    if kind == "out":
        u = min(1.0, max(0.0, u))
        return 1.0 - (1.0 - u) ** 3
    if kind == "io":
        return smoothstep(0.0, 1.0, u)
    return min(1.35, max(0.0, u))            # a drift keeps drifting through the dissolve that follows


def _view(i: int, t: float, iw: int, ih: int) -> skia.Rect:
    """The part of shot i's picture the camera shows at t."""
    s = SHOTS[i]
    t0, t1 = span(i)
    e = _ease(s.ease, (t - t0) / (s.move or (t1 - t0)))
    z = max(1.0, s.z[0] + (s.z[1] - s.z[0]) * e)
    x = 0.5 + s.at[0] + (s.at[2] - s.at[0]) * e
    y = 0.5 + s.at[1] + (s.at[3] - s.at[1]) * e
    half = 0.5 / z
    x, y = min(1.0 - half, max(half, x)), min(1.0 - half, max(half, y))
    return skia.Rect.MakeLTRB((x - half) * iw, (y - half) * ih, (x + half) * iw, (y + half) * ih)


@lru_cache(maxsize=24)
def _patch(base: str, var: str, kind: str, box) -> skia.Image:
    """What differs in picture `var` from picture `base`, as an image with a soft mask: `var` is
    `base` repainted with one thing changed (a pose, closed eyes), so laying this patch over `base`
    changes only that thing and leaves the rest of the picture perfectly still.
    The mask keeps the big connected differences (the thing that moved) and drops thin or
    scattered ones (a repainted rain streak, a pixel of drift); `box` = (l, t, r, b) as shares of
    the picture limits it further."""
    from PIL import Image
    A = Image.open(ART / f"{base}.png").convert("RGB")
    B = Image.open(ART / f"{var}.png").convert("RGB")
    if B.size != A.size:
        B = B.resize(A.size, Image.LANCZOS)
    a, b = np.asarray(A).astype(np.int16), np.asarray(B)
    d = np.abs(a - b).sum(axis=-1)
    small = kind in ("blink", "hold", "loop")           # eyes, wings: a finer mask
    m = ndi.binary_opening(d > (84 if small else 66), structure=np.ones((3, 3), bool), iterations=1 if small else 2)
    if box is not None:
        h, w = m.shape
        keep = np.zeros_like(m)
        keep[int(box[1] * h):int(box[3] * h), int(box[0] * w):int(box[2] * w)] = True
        m &= keep
    lab, n = ndi.label(m)
    if n:
        idx = np.arange(1, n + 1)
        area = ndi.sum(m, lab, idx)
        weight = ndi.sum(d, lab, idx)
        if kind == "loop":                              # every wing
            good = idx[area >= 14]
        elif small:                                     # the two eyes (and their reflection)
            good = idx[np.argsort(-weight)[:4]]
            good = good[(area[good - 1] >= 10) & (weight[good - 1] >= 0.25 * float(weight.max()))]
        else:
            good = idx[area >= max(60.0, 0.015 * float(area.max()))]
        m = np.isin(lab, good)
    m = ndi.binary_dilation(m, iterations=5 if small else 12)
    m = ndi.binary_fill_holes(m)
    alpha = np.clip(ndi.gaussian_filter(m.astype(np.float32), 2.0 if small else 3.0), 0.0, 1.0)
    if not small and m.sum() > 400:
        # the repaint may tint the figure a little differently: bring the patch's colours back to
        # the base's (same things inside the mask, in another pose), so only the pose changes
        fa, fb = a[m].astype(np.float32), b[m].astype(np.float32)
        gain = np.clip(fa.std(axis=0) / np.maximum(fb.std(axis=0), 1.0), 0.8, 1.25)
        b = np.clip((b.astype(np.float32) - fb.mean(axis=0)) * gain + fa.mean(axis=0), 0.0, 255.0).astype(np.uint8)
    rgba = np.dstack([b, (alpha * 255.0 + 0.5).astype(np.uint8)])
    return skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType,
                                alphaType=skia.kUnpremul_AlphaType).makeRasterImage()


def _blinking(t: float, t0: float, seed: int) -> bool:
    k = math.floor((t - t0) / 3.4)
    start = t0 + 3.4 * k + 1.1 + 1.7 * prims.hash01(int(k), 400 + seed)
    return start <= t < start + 0.14


def _alt_on(ctx, f, i: int, t: float) -> bool:
    """Whether the second pose of an ("alt", picture, mode, arg[, box]) layer shows at t."""
    mode, arg = f[2], (f[3] if len(f) > 3 else None)
    if mode == "walk":                      # the stride lands on the beat; the passing pose on the off-beat
        k, frac = ctx.tl.beat_at(t)
        return ((k + frac) / float(arg or 1)) % 1.0 >= 0.5
    if mode == "blink":
        return _blinking(t, SHOTS[i].t0, i)
    if mode == "hold":                      # between two absolute times
        return arg[0] <= t < arg[1]
    if mode == "loop":                      # every arg seconds, half of the time
        return (t % float(arg)) >= 0.5 * float(arg)
    if mode == "rest":                      # the resting pose, except just after each measured attack
        return not any(0.0 <= t - float(o[0]) < 0.30 for o in ctx.tl.onsets_between(184.0, 192.2, 0.4))
    raise ValueError(mode)


def _layer(ctx, i: int, t: float, alpha: float = 1.0) -> None:
    """Shot i as it looks at t: its picture through its camera, plus the second poses that are on."""
    s = SHOTS[i]
    canvas = ctx.canvas
    img = _art(s.art)
    src = _view(i, t, img.width(), img.height())
    dst = skia.Rect.MakeWH(W, H)
    if alpha < 1.0:
        canvas.saveLayerAlpha(None, int(round(255 * alpha)))
    canvas.save()
    if s.flip:                              # the picture mirrored (keeps who stands on which side)
        canvas.translate(W, 0.0)
        canvas.scale(-1.0, 1.0)
    canvas.drawImageRect(img, src, dst, SAMPLING, None, skia.Canvas.kFast_SrcRectConstraint)
    for f in s.fx:
        if f[0] == "alt" and _alt_on(ctx, f, i, t):
            patch = _patch(s.art, f[1], f[2], f[4] if len(f) > 4 else None)
            canvas.drawImageRect(patch, src, dst, SAMPLING, None, skia.Canvas.kFast_SrcRectConstraint)
    for f in s.fx:
        if f[0] == "rainbox":               # rain seen through a window: clipped to a part of the picture
            l, tp, r, b = f[2]
            iw, ih = img.width(), img.height()
            box = skia.Rect.MakeLTRB((l * iw - src.left()) / src.width() * W, (tp * ih - src.top()) / src.height() * H,
                                     (r * iw - src.left()) / src.width() * W, (b * ih - src.top()) / src.height() * H)
            canvas.save()
            canvas.clipRect(box)
            canvas.scale(K, K)
            look.rain(ctx, (box.left() / K, box.top() / K, box.right() / K, box.bottom() / K), amount=f[1], slant=-0.14,
                      seed=17, alpha=0.42, color=COLD_RAIN, splash=0.0, canvas=canvas)
            canvas.restore()
    canvas.restore()
    if alpha < 1.0:
        canvas.restore()


def _pictures(ctx, i: int, t: float) -> None:
    s = SHOTS[i]
    if s.fade > 0.0 and i > 0 and t < s.t0 + s.fade:
        _layer(ctx, i - 1, t)
        _layer(ctx, i, t, smoothstep(s.t0, s.t0 + s.fade, t))
    else:
        _layer(ctx, i, t)


def _burst(canvas, a: float) -> None:
    if a > 0.004:
        canvas.drawPaint(skia.Paint(Color=sk((1.0, 0.97, 0.90), min(1.0, a)), BlendMode=skia.BlendMode.kScreen))


def _title(t: float):
    a_t = smoothstep(2.5, 4.2, t) * (1.0 - smoothstep(8.8, 10.5, t))
    a_c = smoothstep(3.3, 5.0, t) * (1.0 - smoothstep(8.8, 10.4, t))

    def draw(c):
        x, y, paper = 960.0, 120.0, look.PAPER
        if a_t > 0.01:
            img = prims.text_image(credits.title(), prims.SERIF_CJK, TITLE_PX, paper, tracking=0.55)
            prims.draw_image(c, img, x, y, alpha=0.9 * a_t, sampling=prims.MIP)
        if a_c > 0.01:
            img = prims.text_image(credits.artist(), prims.SERIF_CJK, CRED_PX, paper, tracking=0.4)
            prims.draw_image(c, img, x, y + 76, alpha=0.78 * a_c, sampling=prims.MIP)
            line = "　　".join(f"{r}　{n}" for r, n in credits.roles()[:2])
            if line:
                img = prims.text_image(line, prims.SERIF_CJK, CRED_PX * 0.86, paper, tracking=0.3)
                prims.draw_image(c, img, x, y + 122, alpha=0.68 * a_c, sampling=prims.MIP)
    return draw


def draw(ctx) -> None:
    t = ctx.tc
    i = index_at(t)
    s = SHOTS[i]
    t0, t1 = span(i)
    u = (t - t0) / (t1 - t0)
    c, post = ctx.canvas, ctx.post
    fx = {f[0]: f for f in s.fx}

    if "ring" in fx:
        _n, r0, r1, cx, cy = fx["ring"]
        w = min(1.0, max(0.0, (t - r0) / (r1 - r0)))
        far = math.hypot(max(cx, 1.0 - cx) * W, max(cy, 1.0 - cy) * H) + 90.0
        reach = far * (0.05 * min(1.0, w * 12.0) + 0.95 * w ** 1.35)        # visible at once, then gathering speed
        look.reveal(ctx, lambda: _pictures(ctx, i, t), cx * W, cy * H, reach, soft=70.0, sat=PALE[0], cool=PALE[1])
    elif "grade" in fx:
        with look.graded(ctx, sat=fx["grade"][1], cool=fx["grade"][2]):
            _pictures(ctx, i, t)
    else:
        _pictures(ctx, i, t)

    # drawn weather, in 3-unit pixels over the picture (canvas and glow share the scaled frame)
    c.save()
    ctx.glow.save()
    c.scale(K, K)
    ctx.glow.scale(K, K)
    full = (0.0, 0.0, W / K, H / K)
    beat = ctx.pulse(0.30)
    if "mist" in fx:
        look.fog_band(c, (-200.0, 0.50 * H / K, W / K + 200.0, 0.80 * H / K), ctx.t, density=fx["mist"][1],
                      speed=26.0, seed=i, alpha=0.30)
    if "rain" in fx:
        f = fx["rain"]
        look.rain(ctx, full, amount=f[1], slant=f[2] if len(f) > 2 else -0.16, seed=11, alpha=0.5, color=COLD_RAIN,
                  ground=(0.62 * H / K, 0.80 * H / K), canvas=c)
    if "litrain" in fx:
        look.rain(ctx, full, amount=fx["litrain"][1], slant=-0.10, seed=12, alpha=0.7, lit_side="left",
                  lit_reach=0.95, ground=(0.66 * H / K, 0.80 * H / K), canvas=c)
    if "wind" in fx:
        look.wind(c, (0.0, 0.0, W / K, 0.80 * H / K), ctx.t, strength=fx["wind"][1] * (0.45 + 0.55 * beat),
                  seed=5, alpha=0.40)
    if "pollen" in fx:
        lights.pollen(ctx, (0.0, 0.10 * H / K, W / K, 0.78 * H / K), n=int(fx["pollen"][1]), seed=3, alpha=0.7,
                      color=look.SUN_GOLD, glow=0.3)
    c.restore()
    ctx.glow.restore()

    # light
    if "pulse" in fx:
        post.exposure *= 1.0 + fx["pulse"][1] * beat
    if "tv" in fx:
        k = prims.hash01(int(ctx.t * 7.5), 31)
        post.exposure *= 1.0 + fx["tv"][1] * (0.05 * (k - 0.5) + 0.05 * (ctx.fast - 0.3))
    if "dark" in fx:
        post.exposure *= fx["dark"][1] + (fx["dark"][2] - fx["dark"][1]) * smoothstep(0.0, 1.0, u)
    if "flash" in fx:
        _burst(c, fx["flash"][1] * math.exp(-(t - t0) / 0.24))
    if "hits" in fx:
        a = 0.0
        for o in ctx.tl.onsets_between(184.0, 192.2, 0.4):
            if t >= o[0]:
                a += fx["hits"][1] * float(o[1]) * math.exp(-(t - float(o[0])) / 0.16)
        _burst(c, a)
    if "to" in fx:
        _n, colour, a0, a1, amount = fx["to"]
        post.fade = amount * min(1.0, max(0.0, (t - a0) / (a1 - a0)))
        post.fade_color = colour
    if "title" in fx:
        ctx.overlay(_title(t))
