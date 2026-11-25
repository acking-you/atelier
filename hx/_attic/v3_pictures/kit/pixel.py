"""The pixel stage: the film is pixel art, 384x216 real pixels shown five times enlarged.

Scenes still draw in logical 1920x1080 units; one real pixel is `PX` = 5 logical units, sampled at
the centre of its 5x5 block (so edges come out hard, with no blending). Then the picture is
banded: lightness is snapped to `LEVELS` steps (with an ordered 4x4 dither only in a narrow zone
around each band edge) and chroma to a coarse lattice in OKLab. Anything soft a scene paints
(a glow, a sky gradient, a mist) therefore comes out as flat bands with a stippled edge.

What this asks of whoever draws:
- nothing thinner than one pixel: strokes and gaps of at least `PX` units (thinner things vanish
  or flicker); use `px(n)` for sizes given in real pixels;
- hard shapes, flat tones, shading as a second and third shape; no mask blur as a way of drawing
  form (blur only where a stippled falloff is wanted: light, mist);
- things that travel are moved by whole pixels: `snap(v)` every layer offset and every figure
  position, otherwise their edges crawl. Camera and parallax offsets read `ctx.tc` (true time,
  30 steps a second) and are snapped; everything else reads `ctx.t`, which advances 15 times a
  second (animation on twos);
- no continuous zoom: a change of size is a cut, or a move in whole pixels.
"""
from __future__ import annotations

import numpy as np

PX = 5
PW, PH = 384, 216
LEVELS = 30            # lightness steps between black and white
CHROMA_STEP = 0.022    # lattice of the two OKLab chroma axes
DITHER = 0.25          # width of the stippled zone, as a share of one band (0 = hard bands)

_BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32)
_THRESH = np.tile((_BAYER + 0.5) / 16.0 - 0.5, (PH // 4, PW // 4))            # -0.5..0.5, screen-fixed


def px(n: float) -> float:
    """n real pixels in logical units."""
    return n * PX


def snap(v):
    """Round a logical coordinate (scalar or array) to the pixel grid."""
    if isinstance(v, np.ndarray):
        return np.round(v / PX) * PX
    return round(v / PX) * PX


def sample(full: np.ndarray) -> np.ndarray:
    """(1080, 1920, 3+) uint8 -> (216, 384, 3) float32 0..1: the centre of every 5x5 block."""
    return full[PX // 2::PX, PX // 2::PX, :3].astype(np.float32) / 255.0


def _to_oklab(rgb: np.ndarray) -> np.ndarray:
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    l_ = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m_ = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s_ = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return np.stack([0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
                     1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
                     0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_], axis=-1)


def _to_srgb(lab: np.ndarray) -> np.ndarray:
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = np.stack([4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
                    -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
                    -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_], axis=-1)
    rgb = np.clip(rgb, 0.0, 1.0)
    return np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * rgb ** (1 / 2.4) - 0.055)


def band(low: np.ndarray, dither: float = DITHER, levels: int = LEVELS) -> np.ndarray:
    """(216, 384, 3) float 0..1 -> uint8, banded in OKLab with the ordered dither."""
    lab = _to_oklab(low)
    d = _THRESH * dither
    lab[..., 0] = np.round(lab[..., 0] * levels + d) / levels
    lab[..., 1] = np.round(lab[..., 1] / CHROMA_STEP) * CHROMA_STEP          # chroma is snapped, never stippled
    lab[..., 2] = np.round(lab[..., 2] / CHROMA_STEP) * CHROMA_STEP
    return (_to_srgb(lab) * 255.0 + 0.5).astype(np.uint8)


def dissolve(a: np.ndarray, b: np.ndarray, w: float) -> np.ndarray:
    """Ordered-dither dissolve between two pixel pictures (w 0 = a, 1 = b): no blended colours."""
    if w <= 0.0:
        return a
    if w >= 1.0:
        return b
    take = (_THRESH + 0.5) < w
    return np.where(take[..., None], b, a)


def enlarge(low: np.ndarray, out_w: int, out_h: int) -> np.ndarray:
    """(216, 384, 3) uint8 -> (out_h, out_w, 4) RGBA; exact at 1920x1080, box-filtered otherwise."""
    big = np.repeat(np.repeat(low, PX, axis=0), PX, axis=1)
    if (out_w, out_h) != (PW * PX, PH * PX):
        from PIL import Image
        big = np.asarray(Image.fromarray(big).resize((out_w, out_h), Image.BOX))
    out = np.empty((out_h, out_w, 4), dtype=np.uint8)
    out[..., :3] = big
    out[..., 3] = 255
    return out


def preview(draw_fn, out=None, bg=(0.42, 0.42, 0.44), zoom: int = PX, dither: float = DITHER) -> np.ndarray:
    """For kit authors: run `draw_fn(canvas)` (logical 1920x1080 units) through the pixel stage
    outside the film and return the (216, 384, 3) picture; `out` saves it as a PNG enlarged
    `zoom` times (nearest). Crop the result yourself to compare with a reference."""
    import skia
    from PIL import Image
    arr = np.zeros((PH * PX, PW * PX, 4), dtype=np.uint8)
    surface = skia.Surface(arr)
    canvas = surface.getCanvas()
    canvas.clear(skia.Color4f(bg[0], bg[1], bg[2], 1.0))
    draw_fn(canvas)
    surface.flushAndSubmit()
    low = band(sample(arr), dither)
    if out is not None:
        Image.fromarray(low).resize((PW * zoom, PH * zoom), Image.NEAREST).save(out)
    return low
