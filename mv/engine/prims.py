"""Drawing primitives: dithered gradients, cached sprites, stateless particles, text blocks.

Rules these primitives encode (technical_plan item 4):
  * opaque gradients are dithered by skia; translucent ones are not (see linear_paint) and are
    only masked by the grain, so wide dark ramps must be opaque;
  * blur happens once, at sprite-bake time, on a small surface - never per
    frame on the full frame and never under an upscale transform;
  * particles have no state: position is a closed form of (id, age), with
    all randomness hashed from the id;
  * text is rasterised once per block and afterwards only the image moves.

Colours are (r, g, b) tuples (see palette.py). Coordinates are logical
1920x1080 pixels unless a function says otherwise.
"""
from __future__ import annotations

from typing import Callable, Sequence

import numpy as np
import skia

from . import palette
from .palette import sk

LINEAR = skia.SamplingOptions(skia.FilterMode.kLinear)
MIP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
NEAREST = skia.SamplingOptions()


# --------------------------------------------------------------------------
# hashing (all randomness in the film comes from here)
# --------------------------------------------------------------------------
def hash_u32(ids, salt: int = 0) -> np.ndarray:
    """Integer hash of ids (any int array or scalar) with a salt -> uint32."""
    x = np.atleast_1d(np.asarray(ids, dtype=np.int64)).astype(np.uint64)
    x = x + np.uint64(((int(salt) & 0xFFFFFFFF) + 1) * 0x9E3779B97F4A7C15 & 0xFFFFFFFFFFFFFFFF)
    x ^= x >> np.uint64(30)
    x *= np.uint64(0xBF58476D1CE4E5B9)          # uint64 arrays wrap silently, as intended
    x ^= x >> np.uint64(27)
    x *= np.uint64(0x94D049BB133111EB)
    x ^= x >> np.uint64(31)
    out = (x & np.uint64(0xFFFFFFFF)).astype(np.uint32)
    return out if np.ndim(ids) else out[0]


def hash01(ids, salt: int = 0):
    """Hash -> float64 in [0, 1). Scalar in, scalar out."""
    h = hash_u32(ids, salt) / 4294967296.0
    return h if np.ndim(h) else float(h)


def hash_sym(ids, salt: int = 0):
    """Hash -> float64 in [-1, 1)."""
    return hash01(ids, salt) * 2.0 - 1.0


def value_noise(x, seed: int = 0):
    """Smooth 1-D value noise in [0, 1], period-free, C1 continuous."""
    x = np.asarray(x, dtype=np.float64)
    i = np.floor(x).astype(np.int64)
    f = x - i
    f = f * f * (3.0 - 2.0 * f)
    out = hash01(i, seed) * (1.0 - f) + hash01(i + 1, seed) * f
    return out if np.ndim(out) else float(out)


# --------------------------------------------------------------------------
# gradients (always dithered)
# --------------------------------------------------------------------------
def torn_polygons(keys, n: int = 9, jitter: float = 0.30, r_min: float = 0.70, wide: float = 1.0, tall: float = 1.0):
    """Unit outlines of torn paper shapes, one per key: (a, b) arrays of shape (len(keys), n),
    offsets from the centre for radius 1. n vertices on jittered angles (each wanders by
    `jitter` of the angular step, the whole polygon is turned by a hashed angle) with radii in
    r_min..1, stretched `wide` along a and `tall` along b.

    The one polygon of flaked pigment in the film: the ridges' blotches (landscape.flake_blotch),
    the blank post faces and the shards of the survey sheets all call this, so a chip is the
    same kind of shape wherever it lies. Pure: hashed from the keys alone."""
    keys = np.atleast_1d(np.asarray(keys, dtype=np.int64))[:, None]
    j = np.arange(n, dtype=np.int64)[None, :]
    kj = keys * 16 + j
    ang = 2.0 * np.pi * (j + jitter * hash_sym(kj, 75)) / n + 6.283 * hash01(keys, 76)
    rr = r_min + (1.0 - r_min) * hash01(kj, 77)
    return np.cos(ang) * rr * wide, np.sin(ang) * rr * tall


def linear_paint(p0, p1, colors: Sequence, positions=None, alpha: float = 1.0, n: int = 20,
                 alphas: Sequence[float] | None = None) -> skia.Paint:
    """Paint with an OKLab-resampled linear gradient from p0 to p1 (dithered, see below).

    alphas (one per input colour) makes the gradient fade; it is resampled linearly.
    """
    cols, pos = palette.ramp(colors, positions, n)
    if alphas is None:
        ints = [sk(c, alpha) for c in cols]
    else:
        src = np.linspace(0, 1, len(colors)) if positions is None else np.asarray(positions)
        al = np.interp(pos, src, np.asarray(alphas, dtype=np.float64)) * alpha
        ints = [sk(c, a) for c, a in zip(cols, al)]
    # Opaque gradients get skia's ordered dither. Translucent ones must not: several stacked
    # layers carry the same dither phase and add up to a visible screen pattern (measured: 16x
    # the noise floor with four layers). They are therefore rounded by the 8-bit canvas without
    # dither; the grain, added afterwards, masks their band edges but does not remove them.
    # Keep wide dark ramps opaque and use translucent gradients for short falloffs.
    p = skia.Paint(AntiAlias=True, Dither=(alphas is None and alpha >= 0.999))
    p.setShader(skia.GradientShader.MakeLinear([tuple(p0), tuple(p1)], ints, pos))
    return p


def radial_paint(center, radius: float, color, alpha: float = 1.0, power: float = 2.0,
                 inner: float = 0.0, n: int = 16, color_edge=None) -> skia.Paint:
    """Radial falloff: alpha * (1 - r)^power from `inner` (0..1) out to radius."""
    xs = np.linspace(0.0, 1.0, n)
    fall = np.clip(1.0 - np.clip((xs - inner) / max(1e-6, 1.0 - inner), 0.0, 1.0), 0.0, 1.0) ** power
    cols = [color if color_edge is None else palette.mix(color_edge, color, float(f)) for f in fall]
    ints = [sk(c, alpha * float(f)) for c, f in zip(cols, fall)]
    p = skia.Paint(AntiAlias=True)        # translucent by nature: not dithered, see linear_paint
    p.setShader(skia.GradientShader.MakeRadial(tuple(center), float(radius), ints, [float(x) for x in xs]))
    return p


def fill_rect_gradient(canvas, rect, colors, positions=None, horizontal: bool = False, alpha: float = 1.0):
    """Vertical (or horizontal) dithered gradient over rect = (l, t, r, b)."""
    l, t, r, b = rect
    p = linear_paint((l, t), (r, t) if horizontal else (l, b), colors, positions, alpha)
    canvas.drawRect(skia.Rect.MakeLTRB(l, t, r, b), p)


def glow(canvas, x: float, y: float, radius: float, color, alpha: float = 1.0, power: float = 2.0,
         additive: bool = False, inner: float = 0.0):
    """Soft radial light without blur: alpha * (1 - r/radius)^power beyond the `inner` core.

    A radial gradient (measured faster than an upscaled sprite). Scale the canvas for
    an elliptical glow, and clip it to what can be seen: the cost is per covered pixel.
    """
    if alpha <= 0.002 or radius <= 0.5:
        return
    p = radial_paint((x, y), radius, color, alpha, power, inner)
    if additive:
        p.setBlendMode(skia.BlendMode.kPlus)
    canvas.drawCircle(x, y, radius, p)


def fill(color, alpha: float = 1.0, aa: bool = True, blend=None) -> skia.Paint:
    p = skia.Paint(AntiAlias=aa, Color=sk(color, alpha))
    if blend is not None:
        p.setBlendMode(blend)
    return p


def stroke(color, width: float, alpha: float = 1.0, round_cap: bool = True) -> skia.Paint:
    p = skia.Paint(AntiAlias=True, Color=sk(color, alpha), Style=skia.Paint.kStroke_Style, StrokeWidth=width)
    if round_cap:
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def poly_path(xs, ys, close: bool = False) -> skia.Path:
    """Polyline path from coordinate arrays."""
    path = skia.Path()
    path.addPoly([skia.Point(float(x), float(y)) for x, y in zip(xs, ys)], close)
    return path


# --------------------------------------------------------------------------
# cached sprites
# --------------------------------------------------------------------------
_SPRITES: dict = {}


def sprite(key, w: int, h: int, draw_fn: Callable[[skia.Canvas], None], blur: float = 0.0,
           alpha_only: bool = False, mips: bool = False) -> skia.Image:
    """Render draw_fn once into a w x h image (optionally blurred) and cache it by key.

    With alpha_only the result is an A8 mask: draw it with a paint whose colour
    or shader supplies the colour (so one mask serves every palette).
    The key must capture everything draw_fn depends on.
    """
    img = _SPRITES.get(key)
    if img is not None:
        return img
    arr = np.zeros((int(h), int(w), 4), dtype=np.uint8)
    surf = skia.Surface(arr)
    c = surf.getCanvas()
    if blur > 0:
        lp = skia.Paint()
        lp.setImageFilter(skia.ImageFilters.Blur(blur, blur))
        c.saveLayer(None, lp)
        draw_fn(c)
        c.restore()
    else:
        draw_fn(c)
    surf.flushAndSubmit()
    img = mask_image(arr[..., 3]) if alpha_only else skia.Image.fromarray(arr.copy())
    if mips:
        img = img.withDefaultMipmaps() or img
    _SPRITES[key] = img
    return img


def mask_image(alpha: np.ndarray, mips: bool = False) -> skia.Image:
    """uint8 (h, w) array -> A8 skia image (tinted by the paint that draws it)."""
    a = np.ascontiguousarray(alpha, dtype=np.uint8)
    img = skia.Image.frombytes(a.tobytes(), (a.shape[1], a.shape[0]), skia.kAlpha_8_ColorType)
    if mips:
        img = img.withDefaultMipmaps() or img
    return img


def soft_disc(size: int = 64, hardness: float = 0.0) -> skia.Image:
    """A8 soft round sprite (gaussian-ish falloff), for particle atlases and halos."""
    def draw(c):
        r = size / 2.0
        c.drawCircle(r, r, r, radial_paint((r, r), r, (1, 1, 1), 1.0, 2.2, inner=hardness))
    return sprite(("soft_disc", size, round(hardness, 3)), size, size, draw, alpha_only=True)


def draw_image(canvas, img: skia.Image, x: float, y: float, scale: float = 1.0, alpha: float = 1.0,
               anchor=(0.5, 0.5), color=None, blend=None, rotation: float = 0.0, scale_y: float | None = None,
               sampling=LINEAR):
    """Draw an image/sprite with its anchor point at (x, y). color tints A8 masks."""
    if alpha <= 0.002:
        return
    p = skia.Paint(AntiAlias=True)
    if color is not None:
        p.setColor(sk(color, alpha))
    else:
        p.setAlphaf(float(alpha))
    if blend is not None:
        p.setBlendMode(blend)
    sy = scale if scale_y is None else scale_y
    canvas.save()
    canvas.translate(x, y)
    if rotation:
        canvas.rotate(rotation)
    canvas.scale(scale, sy)
    canvas.drawImage(img, -anchor[0] * img.width(), -anchor[1] * img.height(), sampling, p)
    canvas.restore()


# --------------------------------------------------------------------------
# stateless particles
# --------------------------------------------------------------------------
def emitter(clock: float, rate: float, life: float, id0: int = 0, max_n: int = 4000):
    """Slots of a constant-rate emitter alive at `clock`.

    Particle n is born at clock time n / rate and lives `life` seconds.
    Returns (ids int64, age seconds). Use the ids as hash keys. Because the
    clock is the timeline's particle clock, particles hang during freezes.
    """
    if rate <= 0 or life <= 0:
        z = np.zeros(0)
        return z.astype(np.int64), z
    hi = int(np.floor(clock * rate))
    lo = max(int(np.floor((clock - life) * rate)) + 1, hi - max_n + 1)
    n = np.arange(lo, hi + 1, dtype=np.int64)
    return n + id0, clock - n / rate


def ballistic(p0, v0, tau, g=(0.0, 0.0), k=(0.0, 0.0), dwint=0.0):
    """Closed-form position p0 + v0*tau + 0.5*g*tau^2 + k*dwint (technical_plan item 2).

    p0, v0: (x, y) arrays or scalars; tau: age on the particle clock;
    dwint = Wint(t) - Wint(t_spawn) is the wind path integral; k its gain in px.
    Returns (x, y).
    """
    x = p0[0] + v0[0] * tau + 0.5 * g[0] * tau * tau + k[0] * dwint
    y = p0[1] + v0[1] * tau + 0.5 * g[1] * tau * tau + k[1] * dwint
    return x, y


def _levels(alphas, n_levels: int):
    a = np.clip(np.asarray(alphas, dtype=np.float64), 0.0, 1.0)
    q = np.minimum((a * n_levels).astype(int), n_levels - 1)
    return a, q


def draw_dots(canvas, xs, ys, radius: float, color, alphas=None, alpha: float = 1.0,
              levels: int = 6, additive: bool = False):
    """Batch of round dots of one radius. Per-dot alpha is bucketed into `levels` draw calls."""
    xs = np.asarray(xs, dtype=np.float64)
    if not len(xs):
        return
    ys = np.asarray(ys, dtype=np.float64)
    p = skia.Paint(AntiAlias=True, StrokeWidth=2.0 * radius, StrokeCap=skia.Paint.kRound_Cap)
    if additive:
        p.setBlendMode(skia.BlendMode.kPlus)
    if alphas is None:
        p.setColor(sk(color, alpha))
        canvas.drawPoints(skia.Canvas.kPoints_PointMode, [skia.Point(float(x), float(y)) for x, y in zip(xs, ys)], p)
        return
    a, q = _levels(alphas, levels)
    for lv in range(levels):
        sel = (q == lv) & (a > 0.004)
        if not sel.any():
            continue
        p.setColor(sk(color, alpha * (lv + 0.5) / levels))
        canvas.drawPoints(skia.Canvas.kPoints_PointMode,
                          [skia.Point(float(x), float(y)) for x, y in zip(xs[sel], ys[sel])], p)


def draw_streaks(canvas, x0, y0, x1, y1, width: float, color, alphas=None, alpha: float = 1.0,
                 levels: int = 4, additive: bool = False):
    """Batch of line segments (rain streaks, hatch ticks) as one draw call per alpha level."""
    x0 = np.asarray(x0, dtype=np.float64)
    if not len(x0):
        return
    pts = np.stack([x0, np.asarray(y0, float), np.asarray(x1, float), np.asarray(y1, float)], axis=1)
    p = skia.Paint(AntiAlias=True, StrokeWidth=width, StrokeCap=skia.Paint.kRound_Cap)
    if additive:
        p.setBlendMode(skia.BlendMode.kPlus)

    def emit(rows, a):
        p.setColor(sk(color, a))
        out = []
        for ax, ay, bx, by in rows:
            out.append(skia.Point(float(ax), float(ay)))
            out.append(skia.Point(float(bx), float(by)))
        canvas.drawPoints(skia.Canvas.kLines_PointMode, out, p)

    if alphas is None:
        emit(pts, alpha)
        return
    a, q = _levels(alphas, levels)
    for lv in range(levels):
        sel = (q == lv) & (a > 0.004)
        if sel.any():
            emit(pts[sel], alpha * (lv + 0.5) / levels)


def draw_sprites(canvas, img: skia.Image, xs, ys, scales, color, alphas=None, alpha: float = 1.0,
                 rotations=None, additive: bool = False):
    """Batch of one A8 sprite at many positions/scales/alphas in a single drawAtlas call."""
    xs = np.asarray(xs, dtype=np.float64)
    n = len(xs)
    if not n:
        return
    ys = np.asarray(ys, dtype=np.float64)
    sc = np.broadcast_to(np.asarray(scales, dtype=np.float64), (n,))
    rot = np.zeros(n) if rotations is None else np.asarray(rotations, dtype=np.float64)
    al = np.full(n, alpha) if alphas is None else np.clip(np.asarray(alphas, float), 0, 1) * alpha
    w, h = img.width(), img.height()
    cs, sn = np.cos(rot) * sc, np.sin(rot) * sc
    tx = xs - (cs * w / 2 - sn * h / 2)
    ty = ys - (sn * w / 2 + cs * h / 2)
    xf = [skia.RSXform(float(a), float(b), float(c), float(d)) for a, b, c, d in zip(cs, sn, tx, ty)]
    tex = [skia.Rect.MakeWH(w, h)] * n
    cols = [sk(color, float(a)) for a in al]
    paint = skia.Paint(AntiAlias=True)
    if additive:
        paint.setBlendMode(skia.BlendMode.kPlus)
    canvas.drawAtlas(img, xf, tex, cols, skia.BlendMode.kDstIn if img.isAlphaOnly() else skia.BlendMode.kModulate,
                     LINEAR, None, paint)


# --------------------------------------------------------------------------
# text blocks (rendered once; the only strings the film ever draws)
# --------------------------------------------------------------------------
DRAWN_STRINGS: set[str] = set()      # every string ever rasterised; scanned by mv.textscan
_FONT_MGR = skia.FontMgr()
_TYPEFACES: dict = {}

SERIF_CJK = ("Songti SC", "STHeiti")
SANS_CJK = ("Hiragino Sans GB", "STHeiti")
NUMERALS = ("DIN Condensed", "DIN Alternate", "Helvetica Neue")


def resolve_typeface(families: Sequence[str], text: str, weight: int = 400) -> skia.Typeface:
    """First family in the chain that exists and has a real glyph for every character.

    Raises if none does: a silent fallback to tofu boxes is never acceptable.
    """
    key = (tuple(families), weight, "".join(sorted(set(text))))
    tf = _TYPEFACES.get(key)
    if tf is not None:
        return tf
    style = skia.FontStyle(weight, skia.FontStyle.kNormal_Width, skia.FontStyle.kUpright_Slant)
    chars = [ch for ch in text if not ch.isspace()]
    for fam in families:
        cand = _FONT_MGR.matchFamilyStyle(fam, style)
        if cand is None:
            continue
        glyphs = skia.Font(cand, 32).textToGlyphs("".join(chars)) if chars else []
        if all(g != 0 for g in glyphs):
            _TYPEFACES[key] = cand
            return cand
    raise RuntimeError(f"no typeface in {list(families)} covers the requested text")


def text_image(text: str, families: Sequence[str], size: float, color, alpha: float = 1.0,
               tracking: float = 0.0, weight: int = 400, vertical: bool = False) -> skia.Image:
    """Rasterise one text block once (cached). tracking is in em.

    vertical=True stacks the glyphs top to bottom by manual placement.
    The image has a padding of size/4 px on every side.
    """
    key = ("text", text, tuple(families), round(size, 2), tuple(round(c, 4) for c in color),
           round(alpha, 3), round(tracking, 3), weight, vertical)
    img = _SPRITES.get(key)
    if img is not None:
        return img
    DRAWN_STRINGS.add(text)
    tf = resolve_typeface(families, text, weight)
    font = skia.Font(tf, size)
    font.setSubpixel(True)
    font.setEdging(skia.Font.Edging.kAntiAlias)
    glyphs = font.textToGlyphs(text)
    widths = font.getWidths(glyphs)
    m = font.getMetrics()
    pad = size / 4.0
    paint = skia.Paint(AntiAlias=True, Color=sk(color, alpha))
    if vertical:
        step = size * (1.0 + tracking)
        w = int(np.ceil(max(widths) + 2 * pad))
        h = int(np.ceil(step * (len(text) - 1) + size + 2 * pad))

        def draw(c):
            for i, (ch, gw) in enumerate(zip(text, widths)):
                c.drawString(ch, (w - gw) / 2.0, pad + i * step - m.fAscent * 0.92, font, paint)
    else:
        total = sum(widths) + tracking * size * max(0, len(text) - 1)
        w = int(np.ceil(total + 2 * pad))
        h = int(np.ceil(-m.fAscent + m.fDescent + 2 * pad))

        def draw(c):
            x = pad
            for ch, gw in zip(text, widths):
                c.drawString(ch, x, pad - m.fAscent, font, paint)
                x += gw + tracking * size
    return sprite(key, w, h, draw)
