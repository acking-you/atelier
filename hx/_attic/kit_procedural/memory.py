"""hx.kit.memory: what weighs on the child, as pixel things. The home objects (the table with three
chairs, the door, the faceless adults, the strip of light under a door with two pairs of feet)
and the school objects (pupils, desks, the desk row, the lunch table, the ring of backs, the
whisper, the scribble, the speech balloon, the board, the pointing hand).

Every object takes its base point (x, y) in logical units (usually the middle of its foot line),
a height h (or a width where noted), `manner`, `t`, `seed`, `facing`, `alpha`, and:
- manner "thing": an object in a place, in that place's colours (`colors={"base": ..., "shade":
  ..., "light": ..., "dark": ..., "id": ..., "accent": ..., "face": ..., "bag": ..., "line": ...}`
  override the defaults);
- manner "loom": a towering flat silhouette in three mist tones (`tones` top..base, default
  `loom_tones(depth)`), darker toward the top, stippled into the mist at its base (`dissolve`
  share of the height), only its identifying detail kept as a lifted tone;
- manner "cutout": a knee-high paper prop, pale paper with the object drawn flat on it, a darker
  back edge and a little stand; `tip` 0..1 lays it over flat away from us (with a small bounce).

Pixel-native: each object is drawn at its real-pixel size with anti-aliasing off (roles: base,
shade, light, dark, id, accent, face, bag, line), coloured by the manner and cached as a sprite
keyed by everything it depends on (size in whole pixels, stepped pose, stepped parameters), then
blitted five times enlarged at a snapped position. Cycles are stepped (a walk is four poses).
Faceless means no eyes, no mouth; nobody is drawn cruel. No text anywhere.
"""
from __future__ import annotations

import functools
import math

import numpy as np
import skia

from mv.engine import prims
from mv.engine.palette import hex_rgb, mix, shade

from hx.kit import _thg_px as X
from hx.kit import look
from hx.kit.pixel import PX, snap
from hx.kit.scraps import loom_tones

H01, HS = prims.hash01, prims.hash_sym
BAG = 9
_ROLES = dict(X.ROLE_NAMES, bag=BAG)

PEOPLE = dict(base=hex_rgb("5E6878"), shade=hex_rgb("4B5464"), light=hex_rgb("74808F"), dark=hex_rgb("363D4B"),
              face=hex_rgb("7E8794"), bag=hex_rgb("444C5E"), line=hex_rgb("2A2F3C"), id=hex_rgb("8A919C"))
WOOD = dict(base=hex_rgb("8A5F42"), shade=hex_rgb("6A4632"), light=hex_rgb("A87B58"), dark=hex_rgb("3F2C22"),
            accent=hex_rgb("DCD3C2"), id=hex_rgb("A87B58"))
DOOR = dict(base=hex_rgb("5D5048"), shade=hex_rgb("4A3F39"), light=hex_rgb("7A6B60"), dark=hex_rgb("151A28"),
            id=hex_rgb("C9A86A"), accent=look.AMBER)
DESK = dict(base=hex_rgb("9A7A58"), shade=hex_rgb("7A5E44"), light=hex_rgb("B89A74"), dark=hex_rgb("4A505C"),
            id=hex_rgb("B89A74"))
BOARD = dict(base=hex_rgb("7A6450"), shade=hex_rgb("2F4A44"), light=hex_rgb("9A8470"), dark=hex_rgb("4A3C30"),
             accent=hex_rgb("D9DCD6"), id=hex_rgb("D9DCD6"))
for _d in (PEOPLE, WOOD, DOOR, DESK, BOARD):
    for _k in _d:
        _d[_k] = X.flat(_d[_k])
THREAD = X.flat(hex_rgb("23283A"))
SIGN = dict(base=hex_rgb("C9CCD2"), line=THREAD, dark=THREAD)
CUT_PAPER = hex_rgb("E4DCCB")
CUT_BACK = hex_rgb("A99F8E")
CUT_INK = hex_rgb("4A4E5C")


# =============================================================================================
# the machinery: draw at pixel size -> roles -> manner -> sprite -> blit
# =============================================================================================
def _palette(defaults: dict, colors) -> dict:
    d = dict(defaults)
    if colors:
        d.update(colors)
    return {_ROLES[k]: v for k, v in d.items() if k in _ROLES}


def _tip_frac(tip: float) -> float:
    """Visible height share of a prop falling away from us (eased fall, one small bounce)."""
    tip = max(0.0, min(1.0, tip))
    if tip < 0.72:
        u = tip / 0.72
        a = u * u
    elif tip < 0.88:
        a = 1.0 - 0.10 * math.sin(math.pi * (tip - 0.72) / 0.16)
    else:
        a = 1.0
    return math.cos(a * math.pi / 2)


def _cutout(roles: np.ndarray, pal: dict, tipf: float) -> np.ndarray:
    m = roles > 0
    out = X.rgba(*roles.shape)
    paper = CUT_PAPER
    for r, col in pal.items():
        sel = roles == r
        if not sel.any():
            continue
        if r in (X.DARK, X.LINE, X.ID):
            c = mix(CUT_INK, col, 0.25)
        elif r == X.ACCENT:
            c = mix(paper, col, 0.6)
        elif r == X.SHADE:
            c = mix(paper, col, 0.42)
        else:
            c = mix(paper, col, 0.28)
        X.put(out, sel, c)
    big = m.shape[0] >= 16
    if big:                                                  # the drawn contour, inside the cut edge
        X.put(out, m & ~X.erode(m), mix(CUT_INK, paper, 0.25))
    margin = X.dilate(m, diag=True) & ~m                     # the paper margin round the drawing
    X.put(out, margin, paper)
    sheet = m | margin
    back = X.shift(sheet, 1, -1) & ~sheet                    # the thickness of the board behind
    X.put(out, back, CUT_BACK)
    rows = np.nonzero(sheet.any(1))[0]
    if len(rows):                                            # the stand: a strut behind, to the right
        bot = rows[-1]
        cols = np.nonzero(sheet[bot])[0]
        hh = bot - rows[0] + 1
        x0 = cols[-1]
        n = max(2, int(hh * 0.35))
        for j in range(n):
            yy, xx = bot - j, x0 + max(1, n // 2) - j // 2
            if 0 <= yy < out.shape[0] and 0 <= xx < out.shape[1] and out[yy, xx, 3] == 0:
                X.put(out, (np.arange(out.shape[0])[:, None] == yy) & (np.arange(out.shape[1])[None, :] == xx), CUT_BACK)
    edge = X.dilate(out[..., 3] > 0) & ~(out[..., 3] > 0)
    X.put(out, edge, mix(CUT_INK, look.INK, 0.4))
    if tipf < 0.999:
        out = X.tip_rows(out, tipf)
    return out


def _render(name, draw, ext, hpx, params: tuple, manner, defaults, colors, tones, tip, facing, outline,
            dissolve, side, loom_accent, depth, loom_dark=(X.LINE,)):
    """Sprite of one object: draw(g, *params) in local units (1 = h), extents (xmin, xmax, ymin,
    ymax) in those units; origin at local (0, 0)."""
    fc = 1 if facing >= 0 else -1
    tq = int(round(_tip_frac(tip) * 16)) if manner == "cutout" else 16
    tones = tones or loom_tones(depth)
    key = (name, hpx, params, manner, fc,
           tuple(sorted((k, X.qc(v)) for k, v in colors.items())) if colors else None,
           tuple(X.qc(c) for c in tones) if manner == "loom" else None, tq, outline is not None,
           round(dissolve, 2), side)

    def make():
        xm = max(abs(ext[0]), abs(ext[1]))
        pad = 4
        w = int(math.ceil(2 * xm * hpx)) + 2 * pad
        top = int(math.ceil(ext[3] * hpx)) + pad
        bot = int(math.ceil(max(0.0, -ext[2]) * hpx)) + pad
        g = X.Pen(w, top + bot, w // 2, top, hpx, fc)
        draw(g, *params)
        roles = g.roles()
        pal = _palette(defaults, colors)
        if manner == "loom":
            mask = roles > 0
            acc = roles == X.ACCENT
            idm = (roles == X.ID) | (acc if loom_accent is None else np.zeros_like(acc))
            dark = np.isin(roles, loom_dark)
            out = X.loom_colorize(mask, tones, idm, acc if loom_accent is not None else None, loom_accent,
                                  dissolve, side, darkmask=dark)
        elif manner == "cutout":
            out = _cutout(roles, pal, tq / 16.0)
        else:
            out = X.colorize(roles, pal, outline=outline)
        return X.Sprite(out, g.ox, g.oy)
    return X.memo(key, make)


def _hpx(h: float) -> int:
    return max(4, int(round(h / PX)))


def _put(canvas, sp, x, y, alpha):
    X.blit(canvas, sp, x, y, alpha)


_PPL_DARK = (X.LINE, X.DARK)          # in the mist people keep their hair as a darker shape


def _outline_for(manner, defaults, colors, on: bool):
    if manner != "thing" or not on:
        return None
    d = dict(defaults)
    if colors:
        d.update(colors)
    return shade(d.get("dark", d["base"]), -0.06)


# =============================================================================================
# people: one figure drawn into a pen at (cx, s): s scales the figure inside the sprite unit
# =============================================================================================
def _traits(seed: int, kid: bool):
    return dict(_traits_c(int(seed), bool(kid)))


@functools.lru_cache(maxsize=4096)
def _traits_c(seed: int, kid: bool):
    return tuple(dict(hair=int(H01(seed, 1) * 4), skirt=H01(seed, 2) < (0.4 if kid else 0.35),
                      coat=(not kid) and H01(seed, 3) < 0.6, wide=0.92 + 0.18 * H01(seed, 4),
                      tall=0.94 + 0.10 * H01(seed, 5), hood=kid and H01(seed, 6) < 0.6,
                      seed=seed).items())


def _bumpy(cx, cy, rx, ry, seed, amp, bumps, a0=0.0, a1=2 * math.pi, n=30):
    """Points round an ellipse whose edge rises in soft tufts (hair)."""
    ph = H01(seed, 21) * 6.283
    pts = []
    for j in range(n + 1):
        a = a0 + (a1 - a0) * j / n
        r = 1.0 + amp * (0.5 + 0.5 * math.cos(bumps * a + ph)) * (1.0 if math.sin(a) > -0.3 else 0.3)
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    return pts


def _hair(g, cx, hc, hrx, hry, style: int, kid: bool, view: str, seed: int, sh: float):
    """Head and hair: `view` back (hair covers the head), front (a plain face, no features, under a
    fringe) or side (facing +x: the face is the front lower quarter). Styles: kid 0 short crop,
    1 bob, 2 ponytail, 3 tufts; adult 0 short, 1 bob, 2 long, 3 cap."""
    amp, bumps = (0.16, 7) if (kid and style in (0, 3)) else (0.08, 6)
    if kid and style == 3:
        amp, bumps = 0.24, 9
    cap = (not kid) and style == 3
    bob = style == 1
    long_ = (not kid) and style == 2
    tail = kid and style == 2
    head = _bumpy(cx, hc, hrx * 1.06, hry * 1.04, seed, 0.0 if cap else amp, bumps)
    # hair falling below the head first (behind the face in the front view)
    if bob or long_:
        low = (hc - hry * 1.05) if bob else (sh - 0.02)
        side = 1.14 if view != "side" else 1.0
        x0 = cx - hrx * side
        x1 = cx + hrx * side if view != "side" else cx + hrx * 0.1
        g.poly([(x0, hc), (x1, hc), (x1, low + 0.01), (cx, low - 0.005), (x0, low + 0.01)], X.DARK)
    if tail:
        if view == "side":
            g.poly([(cx - hrx * 0.7, hc + hry * 0.3), (cx - hrx * 1.5, hc - hry * 0.2), (cx - hrx * 1.35, hc - hry * 1.3),
                    (cx - hrx * 1.05, hc - hry * 0.4), (cx - hrx * 0.6, hc)], X.DARK)
        elif view == "back":
            g.poly([(cx - hrx * 0.28, hc - hry * 0.3), (cx + hrx * 0.28, hc - hry * 0.3), (cx + hrx * 0.16, hc - hry * 1.6),
                    (cx - hrx * 0.16, hc - hry * 1.6)], X.DARK)
    g.poly(head, X.DARK)
    if cap:                                                  # a cap: dome, band and brim
        g.poly(_bumpy(cx, hc + hry * 0.15, hrx * 1.12, hry * 0.95, seed, 0.0, 1, 0.0, math.pi, 12), BAG)
        if view == "side":
            g.poly([(cx + hrx * 0.6, hc + hry * 0.30), (cx + hrx * 1.75, hc + hry * 0.18), (cx + hrx * 1.7, hc + hry * 0.05),
                    (cx + hrx * 0.6, hc + hry * 0.10)], BAG)
        elif view == "front":
            g.rect(cx - hrx * 1.2, hc + hry * 0.05, cx + hrx * 1.2, hc + hry * 0.22, BAG, 1, 1)
    if view == "front":
        g.oval(cx, hc - hry * 0.18, hrx * 0.80, hry * 0.78, X.FACE)
        if not cap:                                          # the fringe
            fr = _bumpy(cx, hc, hrx * 1.06, hry * 1.04, seed, amp, bumps, 0.0, math.pi, 16)
            yb = hc + hry * 0.18
            fr += [(cx - hrx * 0.5, yb - hry * 0.12), (cx - hrx * 0.1, yb), (cx + hrx * 0.4, yb - hry * 0.15),
                   (cx + hrx * 0.8, yb)]
            g.poly(fr, X.DARK)
    elif view == "side":
        pts = [(cx + hrx * 0.10, hc + hry * 0.10)]
        for j in range(9):
            a = math.radians(-115 + 140 * j / 8)
            pts.append((cx + hrx * 1.0 * math.cos(a), hc + hry * 0.98 * math.sin(a)))
        g.poly(pts, X.FACE)
        if not cap:                                          # fringe over the brow
            g.poly([(cx - hrx * 0.2, hc + hry * 1.0), (cx + hrx * 1.08, hc + hry * 0.45), (cx + hrx * 0.95, hc + hry * 0.15),
                    (cx + hrx * 0.5, hc + hry * 0.30), (cx + hrx * 0.1, hc + hry * 0.2)], X.DARK)


def _walk_legs(step: int):
    """(near knee, near foot, far knee, far foot) as (dx, dy) shares of the hip height."""
    a = ((0.18, 0.50), (0.36, 0.0), (-0.10, 0.50), (-0.30, 0.04))      # contact: near leg ahead
    b = ((0.03, 0.50), (0.02, 0.0), (0.16, 0.52), (-0.12, 0.20))       # passing: far leg lifted
    if step % 4 == 0:
        return a
    if step % 4 == 1:
        return b
    if step % 4 == 2:
        return (a[2], a[3], a[0], a[1])
    return (b[2], b[3], b[0], b[1])


def _person(g, cx, s, kid: bool, view: str, step, tr: dict, bag: bool = False, arms=True, hand_to=None):
    """A faceless person, feet at (cx, 0), standing s tall: hair, neck, shoulders, a jacket or coat
    with arms, legs; a school bag on pupils. view: back | front | side (standing) | walk (side,
    `step` 0..3). Side views face +x (the pen mirrors for facing -1). hand_to: (x, y) the near
    hand reaches to (holding a hand). No eyes, no mouth."""
    s = s * tr["tall"]
    wd = tr["wide"]
    if kid:
        hc, hrx, hry, sh, hip, shw, leg = 0.80, 0.135, 0.145, 0.64, 0.34, 0.165, 0.055
    else:
        hc, hrx, hry, sh, hip, shw, leg = 0.905, 0.072, 0.082, 0.80, 0.46, 0.135, 0.040
    shw *= wd
    bob = 0.012 if (view == "walk" and step % 2 == 1) else 0.0
    big = s * g.u >= 30

    def P(x, y):
        return (cx + x * s, (y + bob) * s)

    def R(x0, y0, x1, y1, role, mw=1, mh=1):
        a, b = P(x0, y0)
        c, d = P(x1, y1)
        g.rect(a, b, c, d, role, mw, mh)

    def PO(pts, role):
        g.poly([P(a, b) for a, b in pts], role)

    def L(pts, role, w):
        g.line([P(a, b) for a, b in pts], role, w * s)

    hem = 0.36 if tr["coat"] else hip
    seed = tr["seed"]
    hx_ = lambda: (cx, (hc + bob) * s, hrx * s, hry * s, (sh + bob) * s)
    if view in ("back", "front"):
        # legs and shoes
        R(-0.085 * wd, 0.0, -0.012, hip + 0.02, X.SHADE)
        R(0.012, 0.0, 0.085 * wd, hip + 0.02, X.SHADE)
        R(-0.09 * wd, 0.0, -0.010, 0.025, X.DARK)
        R(0.010, 0.0, 0.09 * wd, 0.025, X.DARK)
        if tr["skirt"]:
            PO([(-shw * 0.8, hip + 0.08), (shw * 0.8, hip + 0.08), (shw * 1.05, hip - 0.10), (-shw * 1.05, hip - 0.10)],
               X.BASE)
        # the jacket: sloping shoulders, a little narrower at the hem; the lee half in shade
        body = [(-shw * 0.45, sh + 0.012), (shw * 0.45, sh + 0.012), (shw * 0.92, sh - 0.025), (shw * 0.88, hem),
                (-shw * 0.88, hem), (-shw * 0.92, sh - 0.025)]
        if tr["coat"]:
            body[3], body[4] = (shw * 1.0, hem), (-shw * 1.0, hem)
        PO(body, X.BASE)
        PO([(shw * 0.2, sh + 0.01), (shw * 0.45, sh + 0.012), (shw * 0.92, sh - 0.025), body[3], (shw * 0.2, hem)],
           X.SHADE)
        if arms:
            for sd, role in ((-1, X.BASE), (1, X.SHADE)):
                PO([(sd * shw * 0.80, sh - 0.01), (sd * shw * 1.02, sh - 0.04), (sd * shw * 1.10, hip + 0.04),
                    (sd * shw * 0.86, hip + 0.04)], role)
                R(sd * shw * 0.86, hip - 0.005, sd * shw * 1.08, hip + 0.04, X.FACE)       # hand
                if big:
                    R(sd * shw * 0.86 - 0.004, hip + 0.06, sd * shw * 0.86 + 0.004, sh - 0.10, 0, 1)
        # neck, collar or hood
        R(-0.03 if not kid else -0.04, sh - 0.01, 0.03 if not kid else 0.04, hc - hry * 0.7, X.FACE)
        if tr.get("hood") and view == "back":
            PO([(-shw * 0.55, sh + 0.005), (shw * 0.55, sh + 0.005), (shw * 0.35, sh - 0.09), (-shw * 0.35, sh - 0.09)],
               X.SHADE)
        elif big:
            R(-shw * 0.42, sh - 0.005, shw * 0.42, sh + 0.018, X.LIGHT, 1, 1)
        if bag and view == "back":
            PO([(-shw * 0.72, sh - 0.06), (shw * 0.72, sh - 0.06), (shw * 0.75, hip + 0.03), (-shw * 0.75, hip + 0.03)], BAG)
            if big:
                R(-shw * 0.72, sh - 0.14, shw * 0.72, sh - 0.12, X.DARK, 1, 1)                # the flap
        elif bag and view == "front":
            R(-shw * 0.62, hip + 0.10, -shw * 0.50, sh + 0.005, BAG, 1)
            R(shw * 0.50, hip + 0.10, shw * 0.62, sh + 0.005, BAG, 1)
        _hair(g, *hx_()[:4], tr["hair"], kid, view, seed, hx_()[4])
        return
    # side views (facing +x)
    tw = (0.10 if kid else 0.075) * wd
    if view == "walk":
        nk, nf, fk, ff = _walk_legs(step)
    else:
        nk, nf, fk, ff = (0.02, 0.5), (0.03, 0.0), (-0.02, 0.5), (-0.03, 0.0)
    hy = hip + 0.02

    def leg_pts(k, f):
        return [(0.0, hy), (k[0] * hip, k[1] * hip), (f[0] * hip, f[1] * hip)]
    lw = leg * 1.8
    if bag:
        PO([(-tw - 0.10, sh - 0.03), (-tw + 0.01, sh - 0.02), (-tw + 0.01, hip + 0.04), (-tw - 0.10, hip + 0.06)], BAG)
    fl = leg_pts(fk, ff)
    L(fl, X.SHADE, lw)                                                         # far leg
    R(fl[2][0] - 0.02, fl[2][1], fl[2][0] + 0.055, fl[2][1] + 0.028, X.DARK)
    if arms and view == "walk":                                                # far arm swings with the near leg
        L([(0.0, sh - 0.03), (nf[0] * hip * 0.45, hip + 0.04)], X.SHADE, 0.05 if not kid else 0.065)
    nl = leg_pts(nk, nf)
    L(nl, X.SHADE, lw)
    R(nl[2][0] - 0.02, nl[2][1], nl[2][0] + 0.055, nl[2][1] + 0.028, X.DARK)
    if tr["skirt"]:
        PO([(-tw, hip + 0.08), (tw, hip + 0.08), (tw * 1.45, hip - 0.10), (-tw * 1.35, hip - 0.10)], X.BASE)
    body = [(-tw, sh - 0.01), (-tw * 0.3, sh + 0.012), (tw * 0.6, sh + 0.008), (tw * 1.0, sh - 0.05),
            (tw * (1.25 if tr["coat"] else 0.95), hem), (-tw * (1.25 if tr["coat"] else 1.05), hem)]
    PO(body, X.BASE)
    if tr.get("hood"):
        PO([(-tw * 1.15, sh + 0.01), (-tw * 0.1, sh + 0.02), (-tw * 0.2, sh - 0.08), (-tw * 1.05, sh - 0.07)], X.SHADE)
    R(-0.025 if not kid else -0.035, sh - 0.01, 0.025 if not kid else 0.035, hc - hry * 0.7, X.FACE)
    if bag:
        L([(-tw * 0.2, sh + 0.01), (tw * 0.5, hip + 0.10)], BAG, 0.02)           # the strap
    _hair(g, cx + 0.005 * s, (hc + bob) * s, hrx * s, hry * s, tr["hair"], kid, "side", seed, (sh + bob) * s)
    if arms:
        aw = 0.05 if not kid else 0.065
        if hand_to is not None:
            L([(0.02, sh - 0.03), ((hand_to[0] - cx) / s, hand_to[1] / s - bob)], X.BASE, aw)
        elif view == "walk":
            hx2, hy2 = ff[0] * hip * 0.45, hip + 0.04
            L([(0.0, sh - 0.03), (hx2, hy2)], X.BASE, aw)
            R(hx2 - 0.02, hy2 - 0.03, hx2 + 0.02, hy2 + 0.005, X.FACE)
        else:
            L([(0.0, sh - 0.03), (0.02, hip + 0.03)], X.BASE, aw)
            R(0.0, hip - 0.01, 0.04, hip + 0.025, X.FACE)


def _ppl_ext(kid=False):
    return (-0.45, 0.45, -0.02, 1.1)


def _ppl_outline(manner, colors, h):
    if manner != "thing" or _hpx(h) < 24:
        return None
    d = dict(PEOPLE)
    if colors:
        d.update(colors)
    return shade(d["dark"], -0.08)


def adult(canvas, x: float, y: float, h: float, manner: str = "thing", t: float = 0.0, seed: int = 0,
          pose: str = "turned", phase: float = 0.0, facing: int = 1, alpha: float = 1.0, colors=None,
          tones=None, depth: float = 0.6, tip: float = 0.0, dissolve: float = 0.18):
    """A faceless adult silhouette, feet at (x, y), h tall. pose "stand" (seen from behind),
    "turned" (side-on, turned away, standing), "walk_away" (side-on walking toward `facing`, four
    stepped poses from `phase` 0..1 = two steps). Coat or skirt, hair from seed."""
    tr = _traits(seed, False)
    view = {"stand": "back", "turned": "side", "walk_away": "walk", "front": "front"}.get(pose, "side")
    step = int((phase % 1.0) * 4) if view == "walk" else 0
    sp = _render("adult", lambda g, v, st, _sd: _person(g, 0.0, 1.0, False, v, st, tr), _ppl_ext(), _hpx(h),
                 (view, step, seed % 997), manner, PEOPLE, colors, tones, tip, facing, _ppl_outline(manner, colors, h),
                 dissolve, "bottom", None, depth, _PPL_DARK)
    _put(canvas, sp, x, y, alpha)


def pupil(canvas, x: float, y: float, h: float, manner: str = "thing", t: float = 0.0, seed: int = 0,
          view: str = "back", phase: float | None = None, bag: bool = True, facing: int = 1, alpha: float = 1.0,
          colors=None, tones=None, depth: float = 0.6, tip: float = 0.0, dissolve: float = 0.18):
    """A faceless schoolchild, feet at (x, y), h tall (big head, child proportions). view "back",
    "front" (a plain pale face, no features) or "side"; with `phase` (0..1 = two steps) the side
    view walks in four stepped poses. Hair, skirt and build from seed."""
    tr = _traits(seed, True)
    v = view
    if view == "side":
        v = "walk" if phase is not None else "side"
    step = int(((phase or 0.0) % 1.0) * 4) if v == "walk" else 0
    sp = _render("pupil", lambda g, vv, st, b, _sd: _person(g, 0.0, 1.0, True, vv, st, tr, bag=b), _ppl_ext(True),
                 _hpx(h), (v, step, bool(bag), seed % 997), manner, PEOPLE, colors, tones, tip, facing,
                 _ppl_outline(manner, colors, h), dissolve, "bottom", None, depth, _PPL_DARK)
    _put(canvas, sp, x, y, alpha)


def passerby(canvas, x: float, y: float, h: float, manner: str = "thing", t: float = 0.0, seed: int = 0,
             phase: float | None = None, facing: int = 1, alpha: float = 1.0, colors=None, kid: bool | None = None,
             tones=None, depth: float = 0.6, tip: float = 0.0):
    """A faceless passer-by on a street, side-on, walking (phase) or standing; a child (shorter,
    with a bag) when `kid` (default from seed, about a third)."""
    kid = (H01(seed, 11) < 0.33) if kid is None else kid
    if kid:
        pupil(canvas, x, y, h * 0.62, manner, t, seed, "side", phase, True, facing, alpha, colors, tones, depth, tip)
    else:
        adult(canvas, x, y, h, manner, t, seed, "walk_away" if phase is not None else "turned", phase or 0.0,
              facing, alpha, colors, tones, depth, tip)


def family_trio(canvas, x: float, y: float, h: float, manner: str = "thing", t: float = 0.0, seed: int = 0,
                phase: float = 0.0, facing: int = 1, alpha: float = 1.0, colors=None, tones=None,
                depth: float = 0.6, tip: float = 0.0):
    """A small one walking between two adults, holding both their hands (h = the adults' height;
    x the child's feet). Side-on, walking toward `facing`, four stepped poses."""
    step = int((phase % 1.0) * 4)
    ta, tb, tc = _traits(seed * 3 + 1, False), _traits(seed * 3 + 2, False), _traits(seed * 3 + 3, True)
    ta["coat"], tb["skirt"] = True, True

    def draw(g, st, _sd):
        kh = 0.58
        hand_y = 0.30
        _person(g, -0.40, 1.0, False, "walk", st, ta, hand_to=(-0.10, hand_y))
        _person(g, 0.40, 1.0, False, "walk", (st + 2) % 4, tb, hand_to=(0.10, hand_y))
        _person(g, 0.0, kh, True, "walk", (st + 1) % 4, tc, arms=False)
        g.line([(0.0, kh * 0.62), (-0.10, hand_y)], X.BASE, 0.04)
        g.line([(0.0, kh * 0.62), (0.10, hand_y)], X.BASE, 0.04)
    sp = _render("trio", draw, (-0.8, 0.8, -0.02, 1.1), _hpx(h), (step, seed % 997), manner, PEOPLE, colors,
                 tones, tip, facing, _ppl_outline(manner, colors, h), 0.18, "bottom", None, depth, _PPL_DARK)
    _put(canvas, sp, x, y, alpha)


# =============================================================================================
# home
# =============================================================================================
def _table_draw(g, chairs, sq, bowl):
    split = sq / 8.0
    d = 0.55 * split
    sag = 0.30 * min(1.0, split * 1.6)
    # the small chair, front-on, behind the table in the middle: left at the gap
    if chairs >= 1:
        g.rect(-0.13, 0.0, -0.105, 0.30, X.DARK)
        g.rect(0.105, 0.0, 0.13, 0.30, X.DARK)
        g.rect(-0.14, 0.27, 0.14, 0.31, X.BASE)
        g.rect(-0.13, 0.31, -0.10, 0.70, X.BASE)
        g.rect(0.10, 0.31, 0.13, 0.70, X.BASE)
        g.rect(-0.13, 0.63, 0.13, 0.70, X.LIGHT)
        g.rect(-0.13, 0.49, 0.13, 0.52, X.SHADE)
    for side in (-1, 1):
        o = side * d
        # adult chair, side-on, facing the table
        if (side == -1 and chairs >= 2) or (side == 1 and chairs >= 3):
            bx = side * 0.93 + o
            fx = side * 0.70 + o
            g.rect(min(bx, bx - side * 0.04), 0.0, max(bx, bx - side * 0.04), 1.0, X.BASE)
            g.rect(min(fx, fx + side * 0.04), 0.0, max(fx, fx + side * 0.04), 0.34, X.SHADE)
            g.rect(min(bx, fx), 0.32, max(bx, fx), 0.37, X.BASE)
            g.rect(min(bx, bx - side * 0.06), 0.90, max(bx, bx - side * 0.06), 1.0, X.LIGHT)
            g.rect(min(bx, fx), 0.14, max(bx, fx), 0.16, X.SHADE)
        # half the table: outer leg, top slab, the broken inner end sagging
        out_x = side * 0.62 + o
        in_x = side * 0.015 + o
        leg = side * 0.55 + o
        g.rect(min(leg, leg + side * 0.05), 0.0, max(leg, leg + side * 0.05), 0.56, X.BASE)
        ys = sag if split > 0 else 0.0
        jag = [(in_x, 0.62 - ys), (in_x - side * 0.02, 0.595 - ys), (in_x + side * 0.015, 0.575 - ys),
               (in_x - side * 0.01, 0.55 - ys)]
        top = [(out_x, 0.62), (out_x, 0.55)] + jag[::-1]
        g.poly(top, X.BASE)
        g.poly([(out_x, 0.62), (out_x, 0.60), (in_x, 0.60 - ys), (in_x, 0.62 - ys)], X.LIGHT)
        g.poly([(out_x - side * 0.03, 0.55), (out_x - side * 0.03, 0.50), (in_x, 0.50 - ys), (in_x, 0.55 - ys)],
               X.SHADE)
    if split <= 0.0:
        g.rect(-0.03, 0.55, 0.03, 0.62, X.BASE)                           # no crack while whole
        g.rect(-0.03, 0.60, 0.03, 0.62, X.LIGHT)
        g.rect(-0.03, 0.50, 0.03, 0.55, X.SHADE)
    if bowl:
        bx = -0.36 - d
        by = 0.62 - (sag * 0.36 / 0.62 if split > 0 else 0.0)
        g.poly([(bx - 0.08, by + 0.06), (bx + 0.08, by + 0.06), (bx + 0.05, by), (bx - 0.05, by)], X.ACCENT)


def table(canvas, x: float, y: float, h: float, manner: str = "thing", t: float = 0.0, seed: int = 0,
          chairs: int = 3, split: float = 0.0, bowl: int = 0, facing: int = 1, alpha: float = 1.0, colors=None,
          tones=None, depth: float = 0.6, tip: float = 0.0, outline: bool = True, dissolve: float = 0.18):
    """The small dining table with three chairs (two side-on at the ends, the small one front-on in
    the middle behind it), feet at (x, y), h = chair-back height (the table is 1.25 h wide).
    chairs 3..0 (dropping right, left, then the small one); split 0..1 (eight steps) breaks it down
    the middle: the halves move apart with their chairs, their broken ends sag, and the small chair
    is left alone at the gap; bowl=1 sets one bowl at the left place."""
    sq = int(round(max(0.0, min(1.0, split)) * 8))
    ext = (-1.0 - 0.55, 1.0 + 0.55, -0.02, 1.05)
    sp = _render("table", _table_draw, ext, _hpx(h), (int(chairs), sq, int(bool(bowl))), manner, WOOD, colors,
                 tones, tip, facing, _outline_for(manner, WOOD, colors, outline), dissolve, "bottom", None, depth)
    _put(canvas, sp, x, y, alpha)


def _door_draw(g, oq, lq):
    op = oq / 6.0
    lit = lq / 4.0
    g.rect(-0.34, -0.0, 0.34, 0.035, X.SHADE)                       # the step
    g.rect(-0.30, 0.0, 0.30, 1.0, X.BASE)                           # the frame
    g.rect(-0.30, 0.95, 0.30, 1.0, X.LIGHT)
    g.rect(-0.30, 0.0, -0.26, 0.95, X.LIGHT)
    g.rect(0.25, 0.0, 0.30, 0.95, X.SHADE)
    if op <= 0.0:
        g.rect(-0.25, 0.035, 0.25, 0.95, X.SHADE)                   # the door leaf
        g.rect(-0.25, 0.035, 0.22, 0.93, X.BASE)
        g.rect(-0.17, 0.56, 0.14, 0.86, X.SHADE)
        g.rect(-0.17, 0.12, 0.14, 0.46, X.SHADE)
        g.rect(0.13, 0.47, 0.19, 0.52, X.ID, 1, 1)                  # the knob
        g.rect(-0.255, 0.948, 0.255, 0.95, X.ID, 1, 1)              # the frame line round the leaf
        g.rect(-0.255, 0.035, -0.25, 0.95, X.ID, 1, 1)
        if lit > 0:
            g.rect(-0.22, 0.035, 0.22, 0.05, X.ACCENT, 1, 1)        # light under the door
        return
    g.rect(-0.25, 0.035, 0.25, 0.95, X.ACCENT if lit > 0 else X.DARK)  # the doorway
    leaf = 0.50 * math.cos(op * math.pi * 0.42)                     # the leaf swings in on the left hinge
    g.poly([(-0.25, 0.035), (-0.25 + leaf, 0.07), (-0.25 + leaf, 0.91), (-0.25, 0.95)], X.SHADE)
    if leaf > 0.12:
        g.rect(-0.25 + leaf - 0.05, 0.47, -0.25 + leaf - 0.02, 0.52, X.ID, 1, 1)
    g.rect(-0.255, 0.948, 0.255, 0.95, X.ID, 1, 1)


def door(canvas, x: float, y: float, h: float, manner: str = "thing", t: float = 0.0, seed: int = 0,
         open: float = 0.0, lit: float = 0.0, glow=None, facing: int = 1, alpha: float = 1.0, colors=None,
         tones=None, depth: float = 0.6, tip: float = 0.0, outline: bool = True, dissolve: float = 0.18,
         spill: float = 1.0):
    """A front door in its frame standing alone, feet (the step) at (x, y), h = frame height (0.6 h
    wide). open 0..1 (six steps) swings the leaf in on its hinge; lit 0..1 fills the doorway with
    warm light (a closed lit door shows a strip under it) and lays a stepped spill of light on the
    ground in front (`spill` 0 to leave it out); with `glow` (a canvas) the light's energy goes there
    too. In the loom manner the light stays warm."""
    oq = int(round(max(0.0, min(1.0, open)) * 6))
    lq = int(math.ceil(max(0.0, min(1.0, lit)) * 4))
    pal_lit = dict(DOOR)
    if colors:
        pal_lit.update(colors)
    acc = pal_lit["accent"]
    sp = _render("door", _door_draw, (-0.4, 0.4, -0.02, 1.02), _hpx(h), (oq, lq), manner, DOOR, colors, tones,
                 tip, facing, _outline_for(manner, DOOR, colors, outline), dissolve, "bottom",
                 acc if lq > 0 else None, depth)
    _put(canvas, sp, x, y, alpha)
    if lit > 0 and manner != "cutout":
        w = 0.50 * h
        if oq > 0 and spill > 0:
            n = 3
            for j in range(n):                                         # the spill: three widening bands
                y0 = snap(y) + j * max(PX, snap(0.025 * h))
                y1 = y0 + max(PX, snap(0.025 * h))
                ww = w * (1.0 + 0.35 * (j + 1))
                r = skia.Rect.MakeLTRB(snap(x - ww / 2), y0, snap(x + ww / 2), y1)
                canvas.drawRect(r, prims.fill(acc, alpha * lit * spill * (0.55 - 0.15 * j), aa=False))
        if glow is not None:
            hh = 0.92 * h if oq > 0 else 0.05 * h
            glow.drawRect(skia.Rect.MakeLTRB(snap(x - w / 2), snap(y - hh), snap(x + w / 2), snap(y)),
                          prims.fill(acc, 0.8 * lit * alpha, aa=False))
            if oq > 0:
                glow.drawRect(skia.Rect.MakeLTRB(snap(x - w), snap(y), snap(x + w), snap(y + 0.08 * h)),
                              prims.fill(acc, 0.35 * lit * alpha * spill, aa=False))


def feet_light(canvas, x: float, y: float, w: float, t: float = 0.0, seed: int = 0, apart: float = 0.0,
               gone: float = 0.0, color=None, glow=None, alpha: float = 1.0, floor=None):
    """The strip of light under a closed door, centred on (x, y) (y = the floor line), w logical
    wide: one pixel of light (two from 300 units up) with a stepped spill on the floor, broken by
    the shadows of two pairs of feet. `apart` 0..1 moves the pairs from close together to the
    strip's ends; `gone` 0..1 walks the right pair out to the side and dims the strip by half."""
    col = look.AMBER if color is None else color
    k = 1.0 - 0.5 * max(0.0, min(1.0, gone))
    col = mix(look.INK, col, k)
    xl, xr = snap(x - w / 2), snap(x + w / 2)
    th = PX * (2 if w >= 300 else 1)
    yb = snap(y)
    fill = prims.fill(col, alpha, aa=False)
    canvas.drawRect(skia.Rect.MakeLTRB(xl, yb - th, xr, yb), fill)
    for j in range(2):                                               # spill on the floor, stepped
        a = alpha * (0.42 - 0.18 * j) * k
        canvas.drawRect(skia.Rect.MakeLTRB(xl - PX * (j + 1), yb + j * PX, xr + PX * (j + 1), yb + (j + 1) * PX),
                        prims.fill(col, a, aa=False))
    if glow is not None:
        glow.drawRect(skia.Rect.MakeLTRB(xl, yb - th, xr, yb + PX), prims.fill(col, 0.7 * alpha * k, aa=False))
    shadow = prims.fill(look.INK if floor is None else floor, alpha, aa=False)
    sh_soft = prims.fill(look.INK if floor is None else floor, alpha * 0.55, aa=False)
    ap = max(0.0, min(1.0, apart))
    foot = max(PX, snap(w * 0.035))
    for j, sgn in enumerate((-1, 1)):
        c = x + sgn * w * (0.07 + 0.31 * ap)
        if j == 1 and gone > 0:
            c += w * 0.55 * min(1.0, gone / 0.6)
            if c > x + w / 2 + foot * 2:
                continue
        for f in (-1, 1):                                            # two feet a pixel apart
            fx = snap(c + f * (foot / 2 + PX * 0.5)) - (foot if f < 0 else 0)
            canvas.drawRect(skia.Rect.MakeLTRB(max(xl, fx), yb - th, min(xr, fx + foot), yb), shadow)
            canvas.drawRect(skia.Rect.MakeLTRB(fx - PX * (1 if f < 0 else 0), yb, fx + foot + PX * (1 if f > 0 else 0),
                                               yb + 2 * PX), sh_soft)


# =============================================================================================
# school
# =============================================================================================
def _desk_draw(g, chair):
    if chair:                                                        # the chair behind, its back above the desk
        g.rect(-0.21, 0.0, -0.18, 0.98, X.DARK)
        g.rect(0.18, 0.0, 0.21, 0.98, X.DARK)
        g.rect(-0.20, 0.74, 0.20, 0.96, X.BASE)
        g.rect(-0.20, 0.92, 0.20, 0.96, X.LIGHT)
    g.rect(-0.34, 0.0, -0.30, 0.62, X.DARK)
    g.rect(0.30, 0.0, 0.34, 0.62, X.DARK)
    g.rect(-0.32, 0.18, 0.32, 0.21, X.DARK)
    g.rect(-0.33, 0.47, 0.33, 0.62, X.SHADE)                         # the book box
    g.rect(-0.37, 0.62, 0.37, 0.67, X.BASE)                          # the top
    g.rect(-0.37, 0.65, 0.37, 0.67, X.LIGHT)


def desk(canvas, x: float, y: float, h: float, manner: str = "thing", t: float = 0.0, seed: int = 0,
         chair: bool = True, facing: int = 1, alpha: float = 1.0, colors=None, tones=None, depth: float = 0.6,
         tip: float = 0.0, outline: bool = True, dissolve: float = 0.18):
    """A school desk seen from the front with its chair tucked behind (the chair back shows above
    the top), feet at (x, y), h = chair-back height (desk top at 0.66 h)."""
    sp = _render("desk", _desk_draw, (-0.42, 0.42, -0.02, 1.02), _hpx(h), (bool(chair),), manner, DESK, colors,
                 tones, tip, facing, _outline_for(manner, DESK, colors, outline), dissolve, "bottom", None, depth)
    _put(canvas, sp, x, y, alpha)


def _desk_row_draw(g, n):
    dw = 1.15
    x0 = -n * dw / 2
    for i in range(n):
        a, b = x0 + i * dw, x0 + (i + 1) * dw
        for lx in (a + 0.04, b - 0.10):
            g.rect(lx, 0.0, lx + 0.06, 0.93, X.DARK)
        g.rect(a + 0.04, 0.26, b - 0.04, 0.29, X.DARK)
        g.rect(a + 0.02, 0.78, b - 0.02, 0.93, X.SHADE)               # the book tray
        g.rect(a, 0.93, b - 0.025, 1.0, X.BASE)                       # the top, a seam between desks
        g.rect(a, 0.975, b - 0.025, 1.0, X.LIGHT)


def desk_row(canvas, x: float, y: float, h: float, n: int = 8, manner: str = "thing", t: float = 0.0,
             seed: int = 0, facing: int = 1, alpha: float = 1.0, colors=None, tones=None, depth: float = 0.6,
             tip: float = 0.0, outline: bool = True, dissolve: float = 0.18):
    """Desks end to end, side-on, as a narrow knee-high path: centre of its foot line at (x, y),
    h = height of the tops (each desk 1.15 h long)."""
    hw = n * 1.15 / 2 + 0.05
    sp = _render("deskrow", _desk_row_draw, (-hw, hw, -0.02, 1.02), _hpx(h), (int(n),), manner, DESK, colors,
                 tones, tip, facing, _outline_for(manner, DESK, colors, outline), dissolve, "bottom", None, depth)
    _put(canvas, sp, x, y, alpha)


def _lunch_draw(g, n, seed):
    slot = 0.36
    hw = n * slot / 2
    g.rect(-hw - 0.22, 0.50, hw + 0.22, 0.56, X.DARK)                   # the table edge beyond the backs
    g.rect(-hw - 0.22, 0.545, hw + 0.22, 0.56, X.LIGHT)
    for ex in (-hw - 0.20, hw + 0.16):
        g.rect(ex, 0.0, ex + 0.04, 0.50, X.DARK)
    g.rect(-hw - 0.05, 0.22, hw + 0.05, 0.27, X.DARK)                   # the seats
    for i in range(n + 1):
        bx = -hw + i * slot - 0.015
        g.rect(bx, 0.0, bx + 0.03, 0.22, X.DARK)
    for i in range(n):
        cx = -hw + (i + 0.5) * slot + 0.012 * HS(seed * 41 + i, 6)
        k = seed * 41 + i
        hc = 0.79 + 0.045 * HS(k, 1)
        sh = 0.60 + 0.03 * HS(k, 2)
        role = X.BASE if i % 2 == 0 else X.SHADE
        sw = slot / 2 + 0.008
        g.poly([(cx - sw, 0.27), (cx + sw, 0.27), (cx + sw, sh - 0.05), (cx + sw * 0.55, sh + 0.01),
                (cx - sw * 0.55, sh + 0.01), (cx - sw, sh - 0.05)], role)                 # shoulders and back
        if H01(k, 7) < 0.5 and g.u >= 24:                                                   # a hood
            g.poly([(cx - sw * 0.5, sh + 0.005), (cx + sw * 0.5, sh + 0.005), (cx + sw * 0.32, sh - 0.08),
                    (cx - sw * 0.32, sh - 0.08)], X.SHADE if role == X.BASE else X.BASE)
        g.rect(cx - 0.035, sh - 0.01, cx + 0.035, hc - 0.08, X.FACE)
        _hair(g, cx, hc, 0.125, 0.135, int(H01(k, 5) * 4), True, "back", k, sh)
        g.rect(cx - 0.12, 0.27, cx + 0.12, 0.44, X.LINE)                                     # the chair back
        if g.u >= 30:
            g.rect(cx - 0.10, 0.30, cx + 0.10, 0.41, 0, 1, 1)
            g.rect(cx - 0.10, 0.345, cx + 0.10, 0.365, X.LINE, 1, 1)


def lunch_table(canvas, x: float, y: float, h: float, n: int = 12, manner: str = "thing", t: float = 0.0,
                seed: int = 0, facing: int = 1, alpha: float = 1.0, colors=None, tones=None, depth: float = 0.6,
                tip: float = 0.0, dissolve: float = 0.18):
    """One long table seen from behind the bench, filled shoulder to shoulder with n seated backs
    and no gap (alternate tones keep them apart), feet at (x, y), h = height of the heads
    (0.36 h a place)."""
    hw = n * 0.36 / 2 + 0.3
    sp = _render("lunch", _lunch_draw, (-hw, hw, -0.02, 1.0), _hpx(h), (int(n), seed % 997), manner, PEOPLE,
                 colors, tones, tip, facing, _ppl_outline(manner, colors, h), dissolve, "bottom", None, depth,
                 _PPL_DARK)
    _put(canvas, sp, x, y, alpha)


def ring_of_backs(canvas, x: float, y: float, r: float, n: int = 9, manner: str = "thing", t: float = 0.0,
                  seed: int = 0, h: float = 200.0, turned=1.0, squash: float = 0.34, who: str = "pupil",
                  rot: float = 0.0, alpha: float = 1.0, colors=None, tones=None, depth: float = 0.6,
                  tip: float = 0.0, near: float = 0.15):
    """Figures standing in a ring round the ground point (x, y) (radius r logical, seen from above
    by `squash`), h tall (the near side `near` larger). turned 0..1 (one value or one per member):
    0 = facing the centre, 1 = back to the centre (turning through side-on). Seen from here the
    far side then shows backs, the near side plain faceless fronts. who: "pupil" | "adult"."""
    tv = list(turned) if hasattr(turned, "__len__") else [float(turned)] * n
    mem = []
    for i in range(n):
        th = 2 * math.pi * (i + 0.5) / n + rot
        cx, cy = math.cos(th), math.sin(th)
        mem.append((cy, i, th, cx))
    mem.sort()
    for cy, i, th, cx in mem:
        tau = max(0.0, min(1.0, tv[i]))
        # heading: from inward (-cx, -cy) through a quarter turn to outward (cx, cy)
        a_in = math.atan2(-cy, -cx)
        a = a_in + math.pi * tau
        hx_, hy_ = math.cos(a), math.sin(a)
        if hy_ > 0.45:
            view, fc = "front", 1
        elif hy_ < -0.45:
            view, fc = "back", 1
        else:
            view, fc = "side", (1 if hx_ >= 0 else -1)
        px_ = x + r * cx
        py_ = y + squash * r * cy
        hh = h * (1.0 + near * cy)
        sd = seed * 31 + i
        if who == "adult":
            adult(canvas, px_, py_, hh, manner, t, sd, {"front": "front", "back": "stand"}.get(view, "turned"),
                  0.0, fc, alpha, colors, tones, depth, tip)
        else:
            pupil(canvas, px_, py_, hh, manner, t, sd, view, None, H01(sd, 9) < 0.7, fc, alpha, colors, tones,
                  depth, tip)


# =============================================================================================
# the scribble, the balloon, the whisper, the board, the hand
# =============================================================================================
def _scribble_pts(seed: int, loops: float):
    """A ball of thread: `loops` uneven turns whose centre wanders (fewer turns when small)."""
    n = int(loops * 12) + 4
    s = np.linspace(0.0, 1.0, n)
    p = [H01(seed, k) * 6.283 for k in range(6)]
    turn = 6.283 * loops * s + p[0]
    rad = 0.22 + 0.10 * np.sin(6.283 * 1.7 * s + p[1])
    cx = 0.20 * np.sin(6.283 * (0.9 + 0.3 * H01(seed, 7)) * s + p[2])
    cy = 0.14 * np.cos(6.283 * (0.7 + 0.3 * H01(seed, 8)) * s + p[3])
    return cx + rad * np.cos(turn), cy + rad * 0.85 * np.sin(turn * (1.0 + 0.08 * H01(seed, 9)))


def _scribble_into(g, cx, cy, size, seed, grow, role=X.LINE, width=0.0):
    loops = max(1.5, min(7.0, size * g.u / 5.0))
    xs, ys = _scribble_pts(seed, loops)
    m = max(2, int(len(xs) * max(0.0, min(1.0, grow))))
    g.line([(cx + a * size, cy + b * size) for a, b in zip(xs[:m], ys[:m])], role, width)


def scribble(canvas, x: float, y: float, size: float, seed: int = 0, grow: float = 1.0, manner: str = "thing",
             t: float = 0.0, color=None, alpha: float = 1.0, tones=None, depth: float = 0.6, tip: float = 0.0):
    """The tangle of dark thread (whispers, the speech that never comes out, the hanging signs),
    centred on (x, y), about `size` logical across; grow 0..1 (sixteen steps) draws it out from its
    start. One-pixel thread (two from about 60 px across)."""
    gq = int(round(max(0.0, min(1.0, grow)) * 16))
    if gq == 0:
        return
    col = THREAD if color is None else color
    sp = _render("scribble", lambda g, gg, sd: _scribble_into(g, 0.0, 0.5, 1.0, sd, gg / 16.0,
                                                               width=0.03 if g.u >= 60 else 0.0),
                 (-0.55, 0.55, -0.05, 1.05), _hpx(size), (gq, seed % 9973), manner, dict(line=col, base=col),
                 None, tones, tip, 1, None, 0.0, "bottom", None, depth)
    _put(canvas, sp, x, y + size * 0.5, alpha)


def _balloon_draw(g, cq, fill, gq, seed, tail):
    rx, ry = 0.5, 0.34
    cy = 0.62
    gap = math.radians(16 + (1 - cq / 8.0) * 80)                    # never closes
    a0 = math.pi / 4 + gap / 2                                         # the gap centred at the upper right
    n = 40
    pts = [(rx * math.cos(a), cy + ry * math.sin(a)) for a in
           [a0 + (2 * math.pi - gap) * j / n for j in range(n + 1)]]
    tx = -0.18 * tail
    if fill:
        g.oval(0.0, cy, rx, ry, X.BASE)
        g.poly([(tx - 0.06, cy - ry + 0.04), (tx + 0.08, cy - ry + 0.02), (tx - 0.14, 0.0)], X.BASE)
    w = 0.025 if g.u >= 50 else 0.0
    g.line(pts, X.LINE, w)
    g.line([(tx - 0.06, cy - ry * 0.93), (tx - 0.14, 0.0), (tx + 0.08, cy - ry * 0.96)], X.LINE, w)
    if gq > 0:
        _scribble_into(g, 0.0, cy, 0.62, seed, gq / 16.0, X.LINE, w * 0.8)


def balloon(canvas, x: float, y: float, w: float, seed: int = 0, closed: float = 0.0, grow: float = 1.0,
            manner: str = "thing", t: float = 0.0, fill: bool | None = None, hang: float = 0.0, tail: int = 1,
            alpha: float = 1.0, colors=None, tones=None, depth: float = 0.6, tip: float = 0.0,
            dissolve: float = 0.0):
    """A speech balloon: an outline that never closes (closed 0..1 shrinks the gap at its upper right
    to a pixel or two, never shut), a tail down to (x, y), scribble inside (grow 0..1), never
    characters. w = width (logical). fill: a pale face (default on for the loom and cutout signs,
    off for the thing). hang > 0 hangs it on a one-pixel thread that long from its top (the signs)."""
    fill = (manner != "thing") if fill is None else fill
    cq = int(round(max(0.0, min(1.0, closed)) * 8))
    gq = int(round(max(0.0, min(1.0, grow)) * 16))
    sp = _render("balloon", _balloon_draw, (-0.6, 0.6, -0.02, 1.0), _hpx(w), (cq, bool(fill), gq, seed % 9973,
                 int(tail)), manner, SIGN, colors, tones, tip, 1, None, dissolve, "bottom", None, depth)
    _put(canvas, sp, x, y, alpha)
    if hang > 0:
        pal = dict(SIGN)
        if colors:
            pal.update(colors)
        col = pal["line"] if manner == "thing" else (tones or loom_tones(depth))[0]
        top = y - 0.96 * w
        canvas.drawRect(skia.Rect.MakeLTRB(snap(x), snap(top - hang), snap(x) + PX, snap(top)),
                        prims.fill(col, alpha, aa=False))


def _whisper_draw(g, fq, seed):
    # A (left) leans in toward B's ear; B (right) seen from behind, its ear turned to A
    g.poly([(-0.66, 0.0), (-0.10, 0.0), (-0.12, 0.30), (-0.26, 0.42), (-0.52, 0.42), (-0.64, 0.30)], X.BASE)
    g.poly([(0.12, 0.0), (0.66, 0.0), (0.64, 0.30), (0.52, 0.42), (0.26, 0.42), (0.14, 0.30)], X.SHADE)
    g.poly([(-0.36, 0.40), (-0.24, 0.40), (-0.12, 0.54), (-0.24, 0.57)], X.BASE)            # A's neck, leaning
    g.rect(0.34, 0.40, 0.42, 0.52, X.SHADE)
    g.oval(-0.14, 0.66, 0.15, 0.165, X.DARK)                                                # A's head, tipped in
    g.poly([(-0.02, 0.52), (0.03, 0.56), (0.03, 0.70), (-0.04, 0.76)], X.FACE)              # faceless front
    g.oval(0.38, 0.68, 0.155, 0.175, X.DARK)                                                # B's head
    g.rect(0.21, 0.62, 0.245, 0.71, X.FACE, 1, 1)                                           # B's ear
    if fq > 0:                                                                              # the thread passes over
        f = fq / 12.0
        n = 24
        m = max(2, int(n * f) + 1)
        arc = [(0.03 + 0.18 * j / n, 0.62 + 0.10 * math.sin(math.pi * j / n) + 0.03 * math.sin(3 * math.pi * j / n))
               for j in range(n + 1)]
        g.line(arc[:m], X.LINE, 0.015 if g.u >= 80 else 0.0)
        hx, hy = arc[m - 1]
        _scribble_into(g, hx, hy + 0.10, 0.20, seed, 0.4 + 0.6 * f, X.LINE, 0.0)


def whisper(canvas, x: float, y: float, h: float, manner: str = "thing", t: float = 0.0, seed: int = 0,
            flow: float = 0.0, facing: int = 1, alpha: float = 1.0, colors=None, tones=None, depth: float = 0.6,
            tip: float = 0.0, dissolve: float = 0.25):
    """Two heads and shoulders leaning together, mouth to ear, base at (x, y), h tall (the busts
    1.25 h wide); a dark thread rises from the one's mouth and arcs over into the other's ear,
    a scribble knot at its head; flow 0..1 (twelve steps). Faceless; a cupped hand, nothing more."""
    fq = int(round(max(0.0, min(1.0, flow)) * 12))
    sp = _render("whisper", _whisper_draw, (-0.66, 0.66, -0.02, 1.2), _hpx(h), (fq, seed % 9973), manner, PEOPLE,
                 colors, tones, tip, facing, None, dissolve, "bottom", None, depth)
    _put(canvas, sp, x, y, alpha)


def _board_draw(g, n, scq, sidx, ladder, stand, seed):
    leg = 0.30 if stand else 0.0
    H = 0.44
    if stand:
        g.line([(-0.36, leg + 0.1), (-0.46, 0.0)], X.DARK, 0.03)
        g.line([(0.36, leg + 0.1), (0.46, 0.0)], X.DARK, 0.03)
        g.line([(-0.40, 0.08), (0.40, 0.08)], X.DARK, 0.015)
    g.rect(-0.5, leg, 0.5, leg + H, X.BASE)                            # the frame
    g.rect(-0.47, leg + 0.04, 0.47, leg + H - 0.025, X.SHADE)           # the slate
    g.rect(-0.47, leg + 0.02, 0.47, leg + 0.04, X.LIGHT)                # the chalk tray
    rows = 3 if ladder else 1
    per = n if not ladder else max(1, (n + rows - 1) // rows)
    k = 0
    for r in range(rows):
        cy = leg + 0.04 + (H - 0.065) * (r + 0.5) / rows
        cnt = min(per, n - k)
        for j in range(cnt):
            if ladder:
                cx = -0.36 + 0.16 * r + (0.72 - 0.16 * r) * (j + 0.5) / per - 0.04
            else:
                cx = -0.47 + 0.94 * (j + 0.5) / cnt
            sz = min(0.82 * 0.94 / max(cnt, 1), (H - 0.1) / rows * 0.92)
            _scribble_into(g, cx, cy, sz, seed * 17 + k, 1.0, X.ACCENT, 0.0)
            if sidx is not None and k == sidx and scq > 0:            # scratched out, rough strokes
                for m in range(scq):
                    yy = cy - sz * 0.4 + sz * 0.8 * (m + 0.5) / 6
                    g.line([(cx - sz * 0.55, yy - sz * 0.10 * HS(m, 3)), (cx + sz * 0.55, yy + sz * 0.22)],
                           X.ACCENT, 0.012 if g.u >= 120 else 0.0)
            k += 1


def board(canvas, x: float, y: float, w: float, manner: str = "thing", t: float = 0.0, seed: int = 0, n: int = 5,
          scratched: int | None = None, scratch: float = 0.0, ladder: bool = False, stand: bool | None = None,
          alpha: float = 1.0, colors=None, tones=None, depth: float = 0.6, tip: float = 0.0,
          outline: bool = True, dissolve: float = 0.18):
    """A blackboard w logical wide (0.44 w tall), base at (x, y) (the bottom of the frame, or the
    feet of its easel when `stand`, default on outside the thing manner): a row (or with `ladder` a
    ladder of three rows) of n chalk scribbles; scribble `scratched` gets scratched out with rough
    strokes as scratch goes 0..1 (six steps). Scribble only: nothing like writing."""
    stand = (manner != "thing") if stand is None else stand
    scq = int(round(max(0.0, min(1.0, scratch)) * 6))
    sp = _render("board", _board_draw, (-0.52, 0.52, -0.02, 0.8), _hpx(w),
                 (int(n), scq, scratched, bool(ladder), bool(stand), seed % 997), manner, BOARD, colors, tones, tip,
                 1, _outline_for(manner, BOARD, colors, outline), dissolve, "bottom", None, depth)
    _put(canvas, sp, x, y, alpha)


def _hand_draw(g):
    g.poly([(-0.20, 1.0), (0.20, 1.0), (0.17, 0.70), (-0.17, 0.70)], X.BASE)              # sleeve
    g.rect(-0.18, 0.63, 0.18, 0.71, X.SHADE)                                              # cuff
    g.oval(0.0, 0.50, 0.17, 0.15, X.BASE)                                                 # back of the hand
    g.rect(-0.16, 0.50, 0.16, 0.65, X.BASE)
    for fx in (-0.115, -0.045):                                                           # folded fingers
        g.oval(fx, 0.385, 0.05, 0.055, X.BASE)
    g.poly([(0.13, 0.60), (0.22, 0.52), (0.18, 0.38), (0.09, 0.40)], X.BASE)              # thumb
    g.rect(-0.04, 0.10, 0.08, 0.46, X.BASE)                                               # the finger
    g.oval(0.02, 0.10, 0.06, 0.07, X.BASE)
    g.line([(-0.08, 0.34), (-0.08, 0.43)], X.LINE, 0.0)
    g.line([(0.09, 0.40), (0.15, 0.46)], X.LINE, 0.0)


def pointing_hand(canvas, x: float, y: float, h: float, manner: str = "loom", t: float = 0.0, seed: int = 0,
                  facing: int = 1, alpha: float = 1.0, colors=None, tones=None, depth: float = 0.6,
                  tip: float = 0.0, dissolve: float = 0.25):
    """A big hand coming down out of the cloud, the index finger pointing down: the fingertip at
    (x, y), the sleeve h above it. In the loom manner it fades up into the cloud (darkest at the
    top, stippled away there); the folded fingers are its only detail. A plain hand, not a claw."""
    sp = _render("hand", lambda g: _hand_draw(g), (-0.25, 0.25, -0.02, 1.0), _hpx(h), (), manner, PEOPLE,
                 colors, tones, tip, facing, None, dissolve, "top", None, depth)
    _put(canvas, sp, x, y, alpha)


def shards(canvas, x: float, y: float, h: float, manner: str = "loom", t: float = 0.0, seed: int = 0,
           n: int = 3, spread: float = 0.9, alpha: float = 1.0, tones=None, depth: float = 0.6,
           dissolve: float = 0.22):
    """The standing shards of the torn picture: n pieces upright side by side round (x, y), the
    tallest h (thin wrapper of scraps.shard; the middle one is the kept piece)."""
    from hx.kit import scraps
    order = [scraps.KEPT] + [i for i in (1, 7, 10, 4, 8) if i != scraps.KEPT]
    for j in range(n):
        i = order[j % len(order)]
        off = (j - (n - 1) / 2) * h * 0.45 * spread
        hh = h * (1.0 if j == (n - 1) // 2 else 0.62 + 0.25 * H01(seed * 7 + j, 3))
        scraps.shard(canvas, i, x + off, y, hh, manner, tones or loom_tones(depth), alpha, dissolve,
                     lean=8 * HS(seed * 7 + j, 4))
