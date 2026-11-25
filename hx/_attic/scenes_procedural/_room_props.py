"""Room props: the phone, the scribbled thread of line 9, the title card, a figure's floor shadow."""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from mv.engine import prims
from mv.engine.palette import mix, sk
from hx import credits
from hx.kit import figures, look

from ._room_set import R, rr

INK = look.INK
COLD = look.hex_rgb("B9D2EE")
WARM_SCREEN = look.hex_rgb("FFD9A0")


# ---------------------------------------------------------------------------------------------
# the phone
# ---------------------------------------------------------------------------------------------
def phone(c, x, y, size, rot, lit=0.0, light=COLD, scroll=None, alpha=1.0):
    """A phone centred at (x, y), `size` px tall, tilted `rot` degrees. lit 0..1 lights its screen;
    scroll (float rows) slides a column of pale bars (no glyphs) up the screen."""
    w, h = size * 0.52, size
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.drawPath(rr(-w / 2, -h / 2, w / 2, h / 2, w * 0.18), prims.fill(look.hex_rgb("1A1D25"), alpha))
    if lit > 0.01:
        sw, sh = w * 0.84, h * 0.88
        scr = rr(-sw / 2, -sh / 2, sw / 2, sh / 2, w * 0.12)
        c.drawPath(scr, prims.fill(mix(look.hex_rgb("2A3140"), light, 0.55 * lit), alpha))
        if scroll is not None:
            c.save()
            c.clipPath(scr, doAntiAlias=True)
            pitch = sh * 0.16
            off = (scroll % 1.0) * pitch
            k0 = int(math.floor(scroll))
            for j in range(-1, 8):
                ry = -sh / 2 + pitch * 0.6 + j * pitch - off
                k = k0 + j
                ln = 0.45 + 0.45 * float(prims.hash01(k, 501))
                c.drawPath(rr(-sw * 0.40, ry, -sw * 0.40 + sw * 0.8 * ln, ry + pitch * 0.42, pitch * 0.2),
                           prims.fill(mix(light, (1, 1, 1), 0.3), 0.55 * lit * alpha))
            c.restore()
    c.restore()


# ---------------------------------------------------------------------------------------------
# the scribble (line 9): thread knotting at the chest, rising as a bubble that never closes
# ---------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _tangle():
    xs, ys = [], []
    n1 = 240                                   # the knot at the chest
    i = np.arange(n1)
    ang = i * 0.62 + 2.0 * np.sin(i * 0.053)
    r = 5 + 24 * (i / n1) ** 0.7 * (0.55 + 0.45 * prims.hash01(i // 7, 510))
    xs.append(r * np.cos(ang) + 3 * prims.hash_sym(i, 511))
    ys.append(r * np.sin(ang) * 0.8 + 3 * prims.hash_sym(i, 512))
    n2 = 90                                    # it rises, wobbling (the bubble's tail)
    u = np.arange(1, n2 + 1) / n2
    xs.append(18 * np.sin(u * 7.0) * (1 - u) + 26 * u + 4 * prims.hash_sym(np.arange(n2), 513))
    ys.append(-30 - 80 * u + 4 * prims.hash_sym(np.arange(n2), 514))
    n3 = 430                                   # the bubble: a tangled, unclosed loop
    j = np.arange(n3)
    a = math.pi * 0.62 + 2 * math.pi * 0.86 * (j / n3) + 0.35 * np.sin(j * 0.21)
    rad = 1 + 0.12 * np.sin(j * 0.47 + 1) + 0.08 * prims.hash_sym(j // 5, 515)
    cx, cy = 18.0, -205.0
    xs.append(cx + 104 * rad * np.cos(a) + 10 * np.cos(j * 0.93))
    ys.append(cy + 80 * rad * np.sin(a) + 10 * np.sin(j * 0.93 + 0.4))
    x, y = np.concatenate(xs), np.concatenate(ys)
    seg = np.hypot(np.diff(x), np.diff(y))
    return x, y, np.concatenate([[0.0], np.cumsum(seg)])


def scribble(c, x, y, grow, t, scale=1.0, alpha=1.0):
    if grow <= 0.002 or alpha <= 0.01:
        return
    tx, ty, cum = _tangle()
    n = int(np.searchsorted(cum, grow * cum[-1])) + 1
    n = max(2, min(n, len(tx)))
    k = np.arange(n)
    wob = 1.6 * np.sin(t * 2.3 + k * 0.7)
    px = x + scale * (tx[:n] + wob)
    py = y + scale * (ty[:n] + np.cos(t * 1.9 + k * 0.5))
    path = prims.poly_path(px, py)
    for width, a, blur in ((7.0, 0.16, 3.0), (2.4, 0.85, 0.8)):
        p = prims.stroke(INK, width * scale, a * alpha)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        c.drawPath(path, p)


# ---------------------------------------------------------------------------------------------
# title card: on the wall above the sofa, in the grey, small
# ---------------------------------------------------------------------------------------------
TITLE_PX = 80.0          # world px; the intro camera shows it at about 64 px
CRED_PX = 32.0


def title_card(c, x, y, a_title, a_cred):
    paper = look.PAPER
    if a_title > 0.01:
        img = prims.text_image(credits.title(), prims.SERIF_CJK, TITLE_PX, paper, tracking=0.55)
        prims.draw_image(c, img, x, y, alpha=0.82 * a_title, sampling=prims.MIP)
    if a_cred > 0.01:
        img = prims.text_image(credits.artist(), prims.SERIF_CJK, CRED_PX, paper, tracking=0.4)
        prims.draw_image(c, img, x, y + 76, alpha=0.7 * a_cred, sampling=prims.MIP)
        roles = credits.roles()[:2]
        line = "　　".join(f"{r}　{n}" for r, n in roles)
        if line:
            img = prims.text_image(line, prims.SERIF_CJK, CRED_PX * 0.86, paper, tracking=0.3)
            prims.draw_image(c, img, x, y + 122, alpha=0.6 * a_cred, sampling=prims.MIP)


# ---------------------------------------------------------------------------------------------
# a figure's long shadow on the floor
# ---------------------------------------------------------------------------------------------
_SHADOW_CF = {}


def floor_shadow(c, who, x, y, h, pose, facing, lean=2.6, squash=0.33, alpha=0.6, blur=5.0, **kw):
    """The figure laid on the floor from its feet: up maps to (-lean, +squash) * length, and its
    width turns into the floor's depth (foreshortened)."""
    p = skia.Paint(Alphaf=float(alpha))
    p.setColorFilter(skia.ColorFilters.Blend(sk(INK), skia.BlendMode.kSrcIn))
    p.setImageFilter(skia.ImageFilters.Blur(blur, blur))
    reach = h * (lean + 0.6)
    c.saveLayer(R(x - reach - 60, y - 80, x + 0.8 * h, y + 0.5 * h + 60), p)
    c.save()
    c.concat(skia.Matrix.MakeAll(0.3, lean, x, 0.42, -squash, y, 0, 0, 1))
    figures.draw(c, who, 0, 0, h, pose, facing=facing, shadow=0.0, **kw)
    c.restore()
    c.restore()
