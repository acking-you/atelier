"""Room world: intro, v1a, v1b, inter, v2a, coda (see hx/DESIGN.md, "Room world").

One living room in world units (hx/scenes/_room_set.py) seen through one virtual camera (pan and
zoom). Light tells the hour: night grey-blue (intro, v1a, v1b), late afternoon warming (inter), a
low persimmon sun in a muted room (v2a), a warm open-window sunset in colour (coda).
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from mv.engine import prims
from mv.engine.palette import mix
from hx.kit import birds, cloud, figures as fig, lights, look, scraps
from hx.timeline import get_timeline, smoothstep

from . import _room_props as P
from . import _room_set as S
from ._room_set import R, hx

SECTIONS = ("intro", "v1a", "v1b", "inter", "v2a", "coda")
CROSSFADE = {"inter": 1.2, "coda": 1.5}

W, H = 1920, 1080
CHILD_H = 245.0
SOFA_X = 830.0          # where the curled child sits on the sofa
CLOUD_SEED = 11


def _lerp(a, b, w):
    if isinstance(a, dict):
        keys = set(a) | set(b)
        return {k: a.get(k, 0.0) * (1 - w) + b.get(k, 0.0) * w for k in keys}
    if isinstance(a, tuple):
        return tuple(x + (y - x) * w for x, y in zip(a, b))
    return a + (b - a) * w


def _blend(A, B, w):
    return {k: _lerp(A[k], B[k], w) if k in B else A[k] for k in A}


# the light of each hour: sky mood, the outside colours, the room's modulation, the window spill
NIGHT = dict(mood={"overcast": 0.55, "night": 0.45}, facade=hx("3A404E"), glass=hx("232834"), roofs=hx("2C3240"),
             far=(0.40, 0.44, 0.58), near=(0.58, 0.63, 0.78), top=0.80, spill=hx("8A9AB0"), spill_a=0.10)
DUSK = dict(mood={"overcast": 1.0, "sunset": 0.0}, facade=hx("4A4A53"), glass=hx("2C2E36"), roofs=hx("3A3C46"),
            far=(0.28, 0.27, 0.32), near=(0.52, 0.50, 0.54), top=0.78, spill=hx("A0A4AC"), spill_a=0.10)
LATE = dict(mood={"overcast": 0.25, "sunset": 0.75}, facade=hx("76584E"), glass=hx("33292A"), roofs=hx("5E4644"),
            far=(0.34, 0.28, 0.29), near=(0.76, 0.58, 0.46), top=0.8, spill=hx("F0B07A"), spill_a=0.15)
SUNSET = dict(mood={"sunset": 1.0}, facade=hx("6A4C45"), glass=hx("2A2224"), roofs=hx("54403F"),
              far=(0.27, 0.22, 0.25), near=(0.56, 0.43, 0.38), top=0.78, spill=hx("F0834D"), spill_a=0.10)
GOLD = dict(mood={"sunset": 0.55, "golden": 0.45}, facade=hx("C08A68"), glass=hx("6A5258"), roofs=hx("A27466"),
            far=(0.70, 0.58, 0.54), near=(1.0, 0.88, 0.75), top=0.9, spill=hx("F7C873"), spill_a=0.20,
            street=hx("A48676"))


# ---------------------------------------------------------------------------------------------
# camera
# ---------------------------------------------------------------------------------------------
def _ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _camera(ctx):
    sid, t = ctx.sec.id, ctx.t
    if sid == "intro":
        e = _ease(t / 12.27) * 0.85 + 0.15 * min(1.0, max(0.0, t / 12.27))
        return _lerp((1350.0, 742.0, 0.70), (1100.0, 752.0, 0.86), e)
    if sid in ("v1a", "coda"):
        return (1165.0, 735.0, 2.0 + 0.03 * min(1.2, ctx.u))
    if sid == "v1b":
        e = _ease(ctx.ts / 5.5)
        cx, cy, z = _lerp((1430.0, 742.0, 1.02), (1690.0, 738.0, 1.16), e)
        return cx, cy, z + 0.03 * min(1.2, ctx.u)
    if sid == "inter":
        return (1700.0, 770.0, 1.20 + 0.05 * min(1.2, max(0.0, ctx.u)))
    # v2a: close on the phone, easing back with line 28
    e = _ease((t - ctx.tl.cue(28).t) / 4.5)
    return _lerp((1130.0, 925.0, 2.0), (1300.0, 860.0, 0.86), e)


def _apply(ctx, cam):
    cx, cy, z = cam
    m = skia.Matrix()
    m.setTranslate(W / 2, H / 2)
    m.preScale(z, z)
    m.preTranslate(-cx, -cy)
    ctx.room_cam = m
    ctx.canvas.save()
    ctx.canvas.concat(m)
    ctx.glow.save()
    ctx.glow.concat(m)
    return (cx - W / 2 / z, cy - H / 2 / z, cx + W / 2 / z, cy + H / 2 / z)


# ---------------------------------------------------------------------------------------------
# shared pieces
# ---------------------------------------------------------------------------------------------
def _room(ctx, view, L, open_w=0.0, sway=0.0, outside_extra=None):
    c = ctx.canvas
    S.outside(c, L["mood"], L["facade"], L["glass"], L["roofs"], street=L.get("street"))
    if outside_extra is not None:
        outside_extra(c)
    c.saveLayer(R(*view), None)
    S.draw_bake(c)
    S.sashes(c, open_w)
    S.curtains(c, ctx.t, sway)
    S.modulate(c, view, L["far"], L["near"], L["top"])
    c.restore()
    S.spill(c, L["spill"], L["spill_a"])


@lru_cache(maxsize=1)
def _crow_sites():
    """Crows along the two wires under the eave: irregular gaps and sizes; four sit from the
    start of v1b, the rest land one per beat from k=32."""
    tl = get_timeline()
    sites = []
    for wire, x0 in ((0, 1512.0), (1, 1526.0)):
        x, i = x0, 0
        while x < 1952:
            sites.append((x, wire, 26 + 15 * float(prims.hash01(wire * 50 + i, 601)), wire * 50 + i))
            x += 30 + 34 * float(prims.hash01(wire * 50 + i, 602)) + (26 if prims.hash01(i, 603) < 0.2 else 0)
            i += 1
    order = np.argsort(prims.hash01(np.arange(len(sites)), 604))
    out = []
    for rank, j in enumerate(order[:17]):
        x, wire, s, sd = sites[j]
        t_land = None if rank < 4 else tl.beat_time(32 + rank - 4)
        facing = 1 if prims.hash01(sd, 605) < 0.6 else -1
        out.append((x, S.wire_y(wire, x), s, sd, facing, t_land, rank))
    return out


def _crows(c, t, upto=17, landing=True, alpha=1.0):
    cs = [q for q in _crow_sites() if q[6] < upto]
    if not cs:
        return
    birds.perched_row(c, [q[0] for q in cs], [q[1] for q in cs], [q[2] for q in cs], t,
                      [q[3] for q in cs], [q[4] for q in cs], alpha=alpha,
                      t_land=[q[5] if landing else None for q in cs])


def _cloud(ctx, rect, heavy=0.55, density=1.0, taper=0.2):
    """The gloom: always a ceiling mass (its top above the frame), over a world rect."""
    cloud.draw(ctx, rect, heavy=heavy, density=density, seed=CLOUD_SEED, taper=taper)


def _child(ctx, x, y, pose, facing=1, **kw):
    return fig.draw(ctx.canvas, "child", x, y, CHILD_H, pose, facing=facing, t=ctx.t, **kw)


def _face_glow(ctx, a, color, alpha, radius=70.0):
    if alpha <= 0.003:
        return
    hx_, hy = a["head"]
    p = prims.radial_paint((hx_, hy), radius, color, alpha, 1.6)
    p.setBlendMode(skia.BlendMode.kScreen)
    ctx.canvas.drawCircle(hx_, hy, radius, p)
    prims.glow(ctx.glow, hx_, hy, radius * 0.8, color, alpha * 0.5)


# ---------------------------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------------------------
def _intro(ctx, view):
    t = ctx.t
    ctx.post.fade = 1.0 - smoothstep(0.0, 2.6, t)
    ctx.post.fade_color = look.INK
    with look.graded(ctx):
        _room(ctx, view, NIGHT, outside_extra=lambda c: _crows(c, t, upto=2, landing=False))
        a_t = smoothstep(2.5, 4.2, t) * (1 - smoothstep(8.8, 10.5, t))
        a_c = smoothstep(3.3, 5.0, t) * (1 - smoothstep(8.8, 10.4, t))
        P.title_card(ctx.canvas, 905.0, 560.0, a_t, a_c)
        _child(ctx, SOFA_X, S.SEAT, fig.curled(), eye="closed", cushion=True)
        _cloud(ctx, (-300, -150, 2900, 560), heavy=0.55, taper=0.12)


def _tv(ctx):
    """The cold TV light from off screen left, flickering with the `fast` curve."""
    fl = 0.85 + 0.15 * float(prims.hash01(ctx.frame // 2, 707))
    return (0.55 + 0.45 * ctx.fast) * fl


def _v1a(ctx, view):
    t, c = ctx.t, ctx.canvas
    l6 = ctx.tl.cue(6)
    rise = smoothstep(l6.t, l6.t + 1.6, t) * (1 - smoothstep(l6.t_end - 0.9, l6.t_end + 0.1, t))
    look_up = smoothstep(l6.t + 0.5, l6.t + 1.3, t) * (1 - smoothstep(l6.t_end - 0.8, l6.t_end - 0.1, t))
    tv = _tv(ctx)
    cold = hx("9FB6DA")
    with look.graded(ctx):
        _room(ctx, view, NIGHT, outside_extra=lambda c: _crows(c, t, upto=2, landing=False))
        p = prims.radial_paint((-60, 820), 1300, cold, 0.36 * tv, 1.25)
        p.setBlendMode(skia.BlendMode.kScreen)
        c.drawRect(R(*view), p)
        q = prims.radial_paint((860, 870), 420, cold, 0.30 * tv, 1.5)
        q.setBlendMode(skia.BlendMode.kScreen)
        c.drawCircle(860, 870, 420, q)
        fig.hero_shadow(c, 1290.0, S.SEAT + 4, 262.0, rise, t, alpha=0.42 + 0.18 * tv)
        _child(ctx, SOFA_X, S.SEAT, fig.curled(), eye="open" if look_up > 0.5 else "half",
               head_tilt=0.05 * look_up, cushion=True)
        _cloud(ctx, (-500, 240, 1160, 830), heavy=0.62, taper=0.12)
    prims.glow(ctx.glow, 0, 800, 600, cold, 0.10 * tv)


def _v1b(ctx, view):
    t, c = ctx.t, ctx.canvas
    l9 = ctx.tl.cue(9)
    with look.graded(ctx):
        _room(ctx, view, NIGHT, outside_extra=lambda c: _crows(c, t))
        a = _child(ctx, 1650.0, 1000.0, fig.stand(0.78), facing=1, eye="open", head_tilt=0.22)
        grow = smoothstep(l9.t + 0.1, l9.t_end - 0.3, t)
        up = smoothstep(l9.t_end - 1.4, l9.t_end + 1.9, t)
        cx, cy = a["chest"]
        P.scribble(c, cx + 14 + 40 * up, cy - 6 - 640 * up, grow, t, scale=1.0 + 0.3 * up,
                   alpha=1.0 - smoothstep(l9.t_end + 1.2, l9.t_end + 2.1, t))
        heavy = 0.55 + 0.35 * smoothstep(l9.t_end + 0.6, l9.t_end + 2.4, t)
        _cloud(ctx, (500, 40, 2900, 400), heavy=heavy, taper=0.1)


def _inter(ctx, view):
    t, c = ctx.t, ctx.canvas
    w = smoothstep(ctx.sec.t0, ctx.sec.t1, t)
    L = _blend(DUSK, LATE, w)
    hit = 91.0
    with look.graded(ctx):
        _room(ctx, view, L, outside_extra=lambda c: _crows(c, t, upto=5, landing=False))
        a = _child(ctx, 1585.0, 990.0, fig.sit_floor(0.85), facing=1, eye="half")
        _cloud(ctx, (600, 40, 2900, 470), heavy=0.45, density=0.8, taper=0.1)
    # the window warms toward sunset (kept warm outside the grade, a little)
    warm = look.PERSIMMON
    c.save()
    c.clipPath(S.panes_path(), doAntiAlias=True)
    p = prims.linear_paint((0, S.OPEN[1]), (0, S.OPEN[3]), [look.AMBER, warm, warm], [0, .55, 1],
                           alphas=[0.04 * w, 0.16 * w, 0.24 * w])
    p.setBlendMode(skia.BlendMode.kScreen)
    c.drawRect(R(*S.OPEN), p)
    c.restore()
    p = prims.radial_paint((1735, 600), 700, warm, 0.10 * w, 1.6)
    p.setBlendMode(skia.BlendMode.kScreen)
    c.drawCircle(1735, 600, 700, p)
    # the mote: hovers near the child, then settles on the sill as a steady glow
    settle = smoothstep(85.5, 88.6, t)
    dx, dy = lights.wander(5, t, 26.0)
    hx0, hy0 = a["head"]
    x0, y0 = hx0 - 70 + dx, hy0 - 40 + dy
    x1, y1 = 1800.0, S.SILL - 8
    arc = math.sin(math.pi * settle) * 60
    mx, my = x0 + (x1 - x0) * settle, y0 + (y1 - y0) * settle - arc
    lights.motes(ctx, [mx], [my], 1.15, [lights.flicker(5, t) * (1 - settle) + 0.9 * settle])
    lit = smoothstep(hit - 0.03, hit + 0.12, t)
    hx_, hy_ = a["hold"]
    P.phone(c, hx_ + 4, hy_ - 4, 34.0, -18.0, lit=lit)
    _face_glow(ctx, a, P.COLD, 0.30 * lit)


def _opp_lit(ctx):
    """With line 28 the opposite windows light one by one on beats: (window index, light 0..1)."""
    tl, t = ctx.tl, ctx.t
    t28 = tl.cue(28).t
    k = 0
    while tl.beat_time(k) < t28 - 0.05:
        k += 1
    order = [4, 0, 7, 2, 5, 8, 3]
    return [(j, smoothstep(tl.beat_time(k + n), tl.beat_time(k + n) + 0.25, t)) for n, j in enumerate(order)]


def _lit_windows(c, lit):
    c.save()
    c.clipRect(R(1748, 478, 1950, 736))
    warm, glow_c = hx("F2B66E"), hx("FFD79A")
    for j, a in lit:
        if a <= 0.01:
            continue
        wx, wy, ww, wh = S.OPP_WINDOWS[j]
        c.drawRect(R(wx, wy, wx + ww, wy + wh), S.vgrad(wy, wy + wh, [glow_c, warm], alpha=a))
        n = 2 + int(prims.hash01(j, 620) < 0.5)
        for i in range(n):
            u = (i + 0.6 + 0.3 * float(prims.hash_sym(j * 7 + i, 621))) / (n + 0.4)
            fh = wh * (0.42 + 0.22 * float(prims.hash01(j * 7 + i, 622)))
            fx, fb = wx + ww * u, wy + wh + 1
            hr = fh * 0.17
            col = hx("4A2E24")
            c.drawPath(S.rr(fx - fh * 0.2, fb - fh * 0.62, fx + fh * 0.2, fb + 4, fh * 0.16), prims.fill(col, 0.85 * a))
            c.drawCircle(fx + hr * 0.2 * float(prims.hash_sym(j * 7 + i, 623)), fb - fh * 0.62 - hr * 0.9, hr,
                         prims.fill(col, 0.85 * a))
    c.restore()


def _v2a(ctx, view):
    t, c = ctx.t, ctx.canvas
    w = smoothstep(ctx.sec.t0, ctx.sec.t1, t)
    cx0, cy0 = 1180.0, 1062.0
    pose = fig.phone_look(0.85)
    lit = _opp_lit(ctx)
    with look.graded(ctx):
        _room(ctx, view, SUNSET, outside_extra=lambda c: _crows(c, t, upto=3, landing=False))
    # warm light that stays warm: the sun, its shaft and patch on the floor, the lit windows
    c.save()
    c.clipRect(R(1515, 478, 1722, 736))
    sx, sy = 1606.0, 590.0
    prims.glow(c, sx, sy, 260, look.PERSIMMON, 0.45, 1.6)
    c.drawCircle(sx, sy, 76, prims.radial_paint((sx - 14, sy - 16), 96, hx("FFB27A"), 1.0, 0.25,
                                                color_edge=look.PERSIMMON))
    c.restore()
    prims.glow(ctx.glow, sx, sy, 180, look.PERSIMMON, 0.6)
    _lit_windows(c, lit)
    patch = S.poly(S.wobbly([(1240, 1000), (1690, 1000), (1270, 1310), (640, 1310)], 3, 640, sub=3))
    S.soft(c, patch, look.PERSIMMON, 0.42, 30, blend=skia.BlendMode.kScreen)
    look.shaft(ctx, 1625, 600, 1060, 1170, 320, 640, color=look.PERSIMMON, alpha=0.20, dust=1, seed=3, glow=0.4)
    with look.graded(ctx):
        P.floor_shadow(c, "child", cx0, cy0, CHILD_H, pose, -1, lean=2.5, squash=0.16, alpha=0.75)
        a = _child(ctx, cx0, cy0, pose, facing=-1, eye="half")
        top = 20 + 100 * w
        _cloud(ctx, (-400, top, 2900, top + 440), heavy=0.55 + 0.25 * w, density=0.9, taper=0.1)
    hx_, hy_ = a["hold"]
    scroll = ctx.beat + smoothstep(0.0, 0.35, ctx.beat_frac)
    P.phone(c, hx_ - 2, hy_ - 6, 40.0, 14.0, lit=1.0, scroll=scroll)
    _face_glow(ctx, a, P.COLD, 0.2, 80.0)
    prims.glow(ctx.glow, hx_, hy_, 40, P.COLD, 0.25)


def _coda(ctx, view):
    t, c, tl = ctx.t, ctx.canvas, ctx.tl
    cue = tl.cue(65)
    g = cue.groups
    tot = float(sum(g)) or 1.0
    g2 = cue.t + (cue.t_end - cue.t) * g[0] / tot
    g3 = cue.t + (cue.t_end - cue.t) * (g[0] + g[1]) / tot
    ctx.post.fade = 0.88 * smoothstep(254.5, 258.85, t)
    ctx.post.fade_color = look.PAPER

    def outside_extra(c):
        birds.perched(c, 1628, S.wire_y(1, 1628), 40, t, seed=4, facing=-1, small=1.0)
        # the friend, down the street: walks in with the second group, waves with the third
        u = smoothstep(g2 - 2.0, g3, t)
        fxp = 1450 + 160 * u
        fh = 48.0
        if t < g3:
            ph = (fxp - 1450) / (0.55 * fh)
            pose = fig.phone_ear(fig.walk(ph % 1.0, 0.1, 0.55), who="friend")
        else:
            pose = fig.reach(fig.wave(t), ("head", 0.0, -0.45), "f", elbow=1, who="friend")
        fig.draw(c, "friend", fxp, 740, fh, pose, facing=1, t=t, shadow=0.3)

    lift = smoothstep(g2 - 0.2, g2 + 1.0, t)
    ring_on = smoothstep(cue.t, cue.t + 0.12, t)
    with look.graded(ctx):
        _room(ctx, view, GOLD, open_w=1.0, sway=1.0, outside_extra=outside_extra)
        look.shaft(ctx, 1720, 560, 1240, 1160, 380, 620, color=look.AMBER, alpha=0.16, dust=1, seed=5, glow=0.3)
        scraps.paper_bird(c, 1562, 738, size=24, phase=1.4, heading=-8, color=look.PAPER)
        pose = fig.blend(fig.curled(), fig.phone_ear(fig.curled()), lift)
        a = _child(ctx, SOFA_X, S.SEAT, pose, eye="open" if t > g2 else "half", tint=0.8, cushion=True,
                   smile=0.55 * smoothstep(g3, g3 + 1.2, t))
        bx, by = cloud.small(ctx, 1120, 610 + 6 * math.sin(t * 0.7), 150)
        cloud.string(c, bx, by, S.SOFA[1] - 26, S.ARM_TOP + 2, t)
        c.drawCircle(S.SOFA[1] - 26, S.ARM_TOP + 4, 3.5, prims.fill(hx("6A6F78")))
    hx_, hy_ = a["hold"]
    ex, ey = a["hand_n"]
    px, py = hx_ + (ex - hx_) * lift, hy_ - 10 + (ey - hy_ + 10) * lift
    P.phone(c, px, py, 30.0, -70 * (1 - lift) + 10 * lift, lit=ring_on, light=P.WARM_SCREEN)
    rings = [cue.t + 1.5 * k + d for k in range(4) for d in (0.0, 0.35) if cue.t + 1.5 * k + d < g2]
    lights.chirp_rings(ctx, px, py, t, rings, life=1.0, radius=46, color=look.AMBER, alpha=0.4)
    _face_glow(ctx, a, P.WARM_SCREEN, 0.22 * ring_on, 60.0)
    prims.glow(ctx.glow, px, py, 36, look.AMBER, 0.5 * ring_on)


_DRAW = {"intro": _intro, "v1a": _v1a, "v1b": _v1b, "inter": _inter, "v2a": _v2a, "coda": _coda}


def draw(ctx):
    view = _apply(ctx, _camera(ctx))
    _DRAW[ctx.sec.id](ctx, view)
    ctx.canvas.restore()
    ctx.glow.restore()
