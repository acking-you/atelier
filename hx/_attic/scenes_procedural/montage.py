"""Montage world: p1a, p1b, v2b, p2a, p2b (see hx/DESIGN.md, shot list).

Everyday places cut on the bar lines behind a child who stays the same (p1a), fall away into fog
while torn scraps of an old picture drift by (p1b); the desk-path of the exam hall (v2b); the same
places again, now walked through with the amber mote (p2a); the scraps gathered into an armful as the
wind rises and whites the view out (p2b). Lines are addressed by LRC index only.
"""
from __future__ import annotations

import math

import skia

from hx.kit import cloud, figures, lights, look, scraps
from hx.timeline import smoothstep
from mv.engine import palette as P
from mv.engine import prims

from . import _montage_people as people
from . import _montage_places as places
from ._montage_paper import H01, HS, cut_rect, hex_rgb

SECTIONS = ("p1a", "p1b", "v2b", "p2a", "p2b")

W, H = 1920, 1080
GY = places.GY
HC = 300.0                       # the child's height in these medium shots
CX = 0.38 * W                    # where the child stands in p1a
CX2 = 0.42 * W                   # where the child walks in place in p2a / p2b
SLOW = 0.30                      # stride of the slow slumped steps (one step per two beats)
STRIDE = 0.40                    # p2a stride (one step per beat)

_DUMMY = skia.Surface(4, 4)


def _anchors(**kw):
    """Anchors of a child pose without drawing it on the frame (a 4 px scratch canvas)."""
    return figures.draw(_DUMMY.getCanvas(), "child", shadow=0.0, **kw)


def _beatpos(tl, t):
    k, f = tl.beat_at(t)
    return k + f


def _first_beat_after(tl, t):
    return math.ceil(_beatpos(tl, t) - 1e-6)


def _bar_index(tl, sec, t):
    bars = tl.bars_between(sec.t0 - 0.01, sec.t1 + 0.01)
    i = 0
    for k, b in enumerate(bars):
        if t >= b - 1e-6:
            i = k
    return i, float(bars[i])


def _cloud_rect(under, cx=W / 2, half=820.0):
    """An overhead mass inside the frame (its ends taper), underside at `under`, centred on cx."""
    top = 30.0
    l, r = max(-30.0, cx - half), min(W + 30.0, cx + half)
    return (l, top, r, top + (under - top) / 0.8)


def _child(ctx, x, pose, facing=1, eye="half", **kw):
    return figures.draw(ctx.canvas, "child", x, kw.pop("y", GY), HC, pose, facing=facing, eye=eye, t=ctx.t, **kw)


# ------------------------------------------------------------------------------------------------
# passers-by (p1a / p1b)
# ------------------------------------------------------------------------------------------------
_CROWD = {"classroom": (4, True), "street": (8, None), "dusk": (5, None)}


def _passers(ctx, place, t_place, alpha=1.0):
    n, kid = _CROWD.get(place, (0, None))
    if n == 0:
        return
    tl = ctx.tl
    eb = people.eased_beats(tl, ctx.t) - people.eased_beats(tl, t_place)
    figs = []
    for i in range(n):
        seed = sum(map(ord, place)) * 7 + i
        tr = people.build(seed, kid)
        d = H01(seed, 301)
        sc = 1.0 - 0.36 * d
        h = (250 + 30 * H01(seed, 302) if tr["kid"] else 440 + 70 * H01(seed, 303)) * sc
        dr = 1 if H01(seed, 304) < 0.55 else -1
        v = (0.22 + 0.06 * H01(seed, 305)) * h
        x0 = -150 + 2200 * (i + 0.3 + 0.5 * H01(seed, 306)) / n
        x = x0 + dr * v * eb
        if -260 < x < W + 260:
            figs.append((d, x, h, dr, seed, tr, v))
    figs.sort(key=lambda f: -f[0])
    for d, x, h, dr, seed, tr, v in figs:
        y = GY - 26 - 74 * d
        col = P.mix(hex_rgb("6E7684"), look.FOG_PALE, 0.25 + 0.55 * d)
        people.draw(ctx.canvas, x, y, h, eb * 0.5, seed, col, dr, alpha, tr, 0.22)


# ------------------------------------------------------------------------------------------------
# p1a / p1b
# ------------------------------------------------------------------------------------------------
P1_PLACES = ("classroom", "street", "dusk", "dusk")


def _p1_walk(ctx):
    """Slow steps from line 13: (phase, x, scroll)."""
    tl = ctx.tl
    k0 = _first_beat_after(tl, tl.cue(13).t)
    k_end = _beatpos(tl, tl.section("p1a").t1)
    k_stop = _beatpos(tl, tl.cue(16).t)
    bp = min(_beatpos(tl, ctx.t), k_stop)
    ph = max(0.0, bp - k0) / 4.0
    ph_end = max(0.0, k_end - k0) / 4.0
    x = CX + SLOW * HC * min(ph, ph_end)
    scroll = SLOW * HC * max(0.0, ph - ph_end)
    return ph, x, scroll, k0


def _moth(ctx, lamp, t_on, alpha=1.0):
    if lamp is None or ctx.t < t_on - 0.3:
        return
    a = smoothstep(t_on - 0.3, t_on + 0.6, ctx.t) * alpha
    lx, ly = lamp
    lights.moth(ctx, lx, ly + 4, ctx.t, r=44, alpha=0.85 * a)
    tl = ctx.tl
    k0 = _first_beat_after(tl, t_on)
    times = [tl.beat_time(k + 0.36 + 0.3 * H01(k, 311)) for k in range(k0, k0 + 24) if H01(k, 312) < 0.55]
    lights.chirp_rings(ctx, lx, ly + 4, ctx.t, times, life=1.2, radius=64, alpha=0.3 * a)


def _p1a(ctx):
    tl, t, c = ctx.tl, ctx.t, ctx.canvas
    i, t_bar = _bar_index(tl, ctx.sec, t)
    place = P1_PLACES[min(i, 3)]
    ph, x, scroll, _k0 = _p1_walk(ctx)
    pose = figures.stand(0.72)
    if ph > 0:
        pose = figures.blend(pose, figures.walk(ph, 0.72, SLOW), min(1.0, ph * 3.0))
    t_place = tl.bars_between(ctx.sec.t0 - 0.01, ctx.sec.t1)[min(i, 2)]
    with look.graded(ctx):
        lamp = places.draw(c, place, places.BASE + scroll)
        _passers(ctx, place, float(t_place))
        cloud.draw(ctx, _cloud_rect(352, x + 60, 760), heavy=0.6, seed=4)
        _moth(ctx, lamp, tl.cue(12).t)
        _child(ctx, x, pose, eye="half")


def _p1b(ctx):
    tl, t, c = ctx.tl, ctx.t, ctx.canvas
    ph, x, scroll, _k0 = _p1_walk(ctx)
    t15, t16, t17 = tl.cue(15).t, tl.cue(16).t, tl.cue(17).t
    fade_place = 1.0 - smoothstep(48.6, 51.2, t)
    stop = smoothstep(t16 - 0.25, t16 + 0.3, t)
    reach_w = smoothstep(t16 + 0.1, t16 + 0.8, t) * (1.0 - smoothstep(t17, t17 + 0.9, t))
    drop = smoothstep(t17, t17 + 1.0, t)
    pose = figures.blend(figures.walk(ph, 0.8, SLOW), figures.stand(0.7), stop)
    target = (0.40, 0.60)
    pose = figures.blend(pose, figures.reach(figures.stand(0.45), target), reach_w)
    pose = figures.blend(pose, figures.stand(0.95), drop * (1.0 - reach_w))
    with look.graded(ctx):
        places.draw(c, "open", places.BASE + scroll * 0.6)
        if fade_place > 0.002:
            places.draw(c, "dusk", places.BASE + scroll, fade_place)
            _passers(ctx, "dusk", tl.section("p1a").t0 + 6.0, fade_place * 0.8)
        look.fog_bank(c, (-40, 420, W + 40, 900), t, 0.6 + 0.4 * (1 - fade_place), seed=6,
                      alpha=0.25 + 0.35 * (1 - fade_place))
        cloud.draw(ctx, _cloud_rect(352 + 30 * drop, x + 60, 760), heavy=0.6 + 0.3 * drop, seed=4)
        an = _child(ctx, x, pose, eye="half", head_tilt=-0.15 * drop)
    # the scraps: a memory of colour, keeping about half of it
    with look.graded(ctx, sat=0.55, cool=0.3):
        a_d = smoothstep(t15 + 0.4, t15 + 1.8, t) * (1.0 - smoothstep(t16, t16 + 0.6, t))
        if a_d > 0.003:
            scraps.drifting(c, t, (x - 900, 430, x + 820, 720), n=9, seed=2, scale=0.30, alpha=a_d, speed=40)
        a_a = smoothstep(t16, t16 + 0.6, t)
        if a_a > 0.003:
            fit = 0.25 + 0.6 * smoothstep(t16, t16 + 1.4, t) - 0.55 * drop
            hx, hy = an["hand_n"]
            cy = hy - 12 + 230 * drop * drop
            scraps.assembled(c, hx + 70, cy, scale=0.30 * (1 - 0.15 * drop), fit=max(0.0, fit), t=t, seed=1,
                             alpha=a_a * (1 - 0.75 * drop), rot=-4 + 14 * drop)
    ctx.post.fade_color = look.INK
    ctx.post.fade = 0.92 * smoothstep(t17, 55.9, t)


# ------------------------------------------------------------------------------------------------
# v2b: the desk-path
# ------------------------------------------------------------------------------------------------
CXV = 0.5 * W
N_PUP = 17
_PUP = None


def _pupils_plan():
    """Static plan in beats since v2b began: speeds, starts, and who is shouldered off where."""
    global _PUP
    if _PUP is not None:
        return _PUP
    pups = []
    for i in range(N_PUP):
        v = 62 + 66 * H01(i, 401)
        x0 = -2100 + 3800 * (i + 0.5) / N_PUP + 190 * HS(i, 402)
        pups.append(dict(i=i, v=v, x0=x0, h=262 + 56 * H01(i, 403), lane=HS(i, 404), out=None))
    ev = []
    for a in pups:
        for b in pups:
            if b["v"] > a["v"] and b["x0"] < a["x0"]:
                u = (a["x0"] - b["x0"]) / (b["v"] - a["v"])
                xm = a["x0"] + a["v"] * u
                if 0.5 < u < 17 and 120 < xm < W - 120 and abs(xm - CXV) > 280:
                    ev.append((u, a["i"], b["i"], xm))
    ev.sort()
    for u, ia, ib, xm in ev:
        a, b = pups[ia], pups[ib]
        if a["out"] is None and (b["out"] is None or b["out"][0] > u):
            a["out"] = (u, xm, ib)
    _PUP = pups
    return pups


def _sheet(c, x, y, w, rot, flip, alpha, col=hex_rgb("E6E2D6")):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(max(0.08, abs(flip)), 1.0)
    path = cut_rect(-w / 2, -w * 0.68, w / 2, w * 0.68, int(w), 0.5)
    c.drawPath(path, prims.fill(P.shade(col, -0.10 * (1 - abs(flip))), alpha))
    if flip > 0.3:
        pr = prims.stroke(hex_rgb("8E96A3"), 1.2, 0.4 * alpha)
        for k in range(4):
            yk = -w * 0.45 + k * w * 0.24
            c.drawLine(-w * 0.34, yk, w * 0.2, yk, pr)
    c.restore()


def _v2b(ctx):
    tl, t, c = ctx.tl, ctx.t, ctx.canvas
    sec = ctx.sec
    u = people.eased_beats(tl, t) - people.eased_beats(tl, sec.t0)
    t31 = tl.cue(31).t
    sit = smoothstep(t31, t31 + 1.3, t)
    part = smoothstep(t31 + 0.6, t31 + 2.5, t)
    pups = _pupils_plan()
    col_on = P.mix(hex_rgb("687080"), look.FOG_PALE, 0.35)
    on_path, off_path, flutters = [], [], []
    for p in pups:
        out = p["out"]
        tr = dict(people.build(1000 + p["i"], True), lean=0.08 + 0.04 * H01(p["i"], 410), swing=0.42)
        if out is None or u < out[0]:
            x = p["x0"] + p["v"] * u
            if not (-200 < x < W + 200):
                continue
            near = math.exp(-((x - CXV) / (230 + 120 * part)) ** 2)
            y = places.PATH_FEET + 6 * p["lane"] * (1 - near) - (10 + 10 * part) * near
            sc = 1.0 - 0.06 * near - 0.04 * part * near
            col = P.mix(col_on, look.FOG_PALE, 0.25 * near * part)
            on_path.append((y, x, p["h"] * sc, u * 0.5, p["i"], tr, col))
        else:
            u0, xm, _ib = out
            s = min(1.0, (u - u0) / 0.9)
            s = s * s * (3 - 2 * s)
            x = xm + 26 * s
            y = places.PATH_FEET + (places.FLOOR_Y + 10 + 12 * H01(p["i"], 405) - places.PATH_FEET) * s
            y -= 22 * math.sin(math.pi * s)
            ts = (u - u0) * tl.beat_s
            grey = smoothstep(0.4, 2.2, ts)
            alpha = 1.0 - 0.45 * grey - 0.55 * smoothstep(3.5, 6.5, ts)
            col = P.mix(col_on, look.FOG_PALE, grey)
            off_path.append((y, x, p["h"], s, p["i"], tr, col, alpha))
            for k in range(1 + (p["i"] % 2)):
                flutters.append((ts, xm + 30 * HS(p["i"] + k, 406), p["i"] * 3 + k))
    with look.graded(ctx):
        places.draw(c, "hall", places.BASE)
        cloud.draw(ctx, _cloud_rect(320, CXV, 900), heavy=0.55, seed=9)
        on_path.sort(key=lambda r: r[0])
        for y, x, h, ph, i, tr, col in on_path:
            people.draw(c, x, y, h, ph, 1000 + i, col, 1, 1.0, tr, 0.12)
        pose = figures.blend(figures.stand(0.75), figures.sit_cross(0.2), sit)
        eye = "closed" if sit > 0.55 else "half"
        _child(ctx, CXV, pose, eye=eye, y=places.PATH_FEET + 4, head_tilt=-0.05 * (1 - sit))
        off_path.sort(key=lambda r: r[0])
        for y, x, h, s, i, tr, col, alpha in off_path:
            people.draw(c, x, y, h, 0.25 * s, 1000 + i, col, 1, alpha, tr, 0.2 * alpha, stand=s)
        for ts, x0, k in flutters:              # loose sheets fluttering down to the floor
            if ts > 6.0:
                continue
            f = min(1.0, ts / 2.4)
            x = x0 + 70 * HS(k, 407) * f + 22 * math.sin(ts * 3.1 + k)
            y = places.PATH_FEET - 130 + (places.FLOOR_Y + 14 - places.PATH_FEET + 130) * (f ** 1.4)
            rot = 40 * HS(k, 408) + 90 * f * HS(k, 409)
            flip = math.cos(ts * 4.0 + k) if f < 1 else 0.25
            _sheet(c, x, y, 26, rot, flip, 1.0 - smoothstep(4.0, 6.0, ts))
    # one sheet folds itself into a paper plane and drifts past the child
    with look.graded(ctx, sat=0.6, cool=0.3):
        tf0, tf1 = t31 + 1.4, t31 + 2.3
        if t > tf0 - 1.2:
            if t < tf1:
                x = CXV - 560 + 60 * (t - tf0)
                y = 520 + 26 * math.sin(t * 2.2)
                fold = smoothstep(tf0, tf1, t)
                _sheet(c, x, y, 34 * (1 - 0.6 * fold), 20 * math.sin(t * 1.7), math.cos(t * 3.0) * (1 - fold) + fold,
                       smoothstep(tf0 - 1.2, tf0 - 0.6, t) * (1 - fold))
                if fold > 0.05:
                    scraps.paper_bird(c, x, y, 30 * fold, 0.0, 6, color=hex_rgb("E6E2D6"), alpha=fold)
            else:
                g = (t - tf1) / 4.2
                x = CXV - 560 + 54 + 1250 * g
                y = 520 + 150 * smoothstep(0, 0.6, g) + 14 * math.sin(t * 1.6) + 40 * g * g
                scraps.paper_bird(c, x, y, 30, 0.12 * math.sin(t * 2.0), 8 + 6 * math.sin(t * 1.3),
                                  color=hex_rgb("E6E2D6"))


# ------------------------------------------------------------------------------------------------
# p2a
# ------------------------------------------------------------------------------------------------
P2_PLACES = ("stair", "dusk", "street", "play")


def _p2a(ctx):
    tl, t, c = ctx.tl, ctx.t, ctx.canvas
    sec = ctx.sec
    i, t_bar = _bar_index(tl, sec, t)
    place = P2_PLACES[min(i, 3)]
    k0 = _beatpos(tl, sec.t0)
    k_stop = _first_beat_after(tl, tl.cue(35).t + 0.9)
    bp = min(_beatpos(tl, t), k_stop)
    ph = (bp - k0) / 2.0
    ph_bar = (min(_beatpos(tl, t_bar), k_stop) - k0) / 2.0
    scroll = min(places.BASE + STRIDE * HC * (ph - ph_bar), places.NW - W)
    t_stop = tl.beat_time(k_stop)
    up = smoothstep(t_stop - 0.1, t_stop + 0.7, t)
    pose = figures.blend(figures.walk(ph, 0.6, STRIDE), figures.reach_up(), up)
    t35 = tl.cue(35).t
    an = _anchors(x=CX2, y_feet=GY, h=HC, pose=figures.reach_up(), t=t)
    hx, hy = an["hand_n"]
    # the underside sinks to meet the raised palm (it presses a little way in)
    under = 360 + (hy - 58 - 360) * smoothstep(t35, t_stop + 0.6, t)
    dent = smoothstep(t_stop + 0.5, t_stop + 1.6, t) if up > 0.01 else 0.0
    with look.graded(ctx):
        lamp = places.draw(c, place, scroll)
        cloud.draw(ctx, _cloud_rect(under, CX2 + 60, 760), heavy=0.6, seed=4)
        if dent > 0:
            # the dent: the underside gives a little round the palm and lets a paler grey through.
            # (drawn here, not with cloud holes: their layer clips an in-frame mass at its rect)
            c.save()
            c.translate(hx + 2, hy - 18)
            c.scale(1.0, 0.7)
            prims.glow(c, 0, 0, 74, cloud.GLOOM[3], 0.5 * dent, 1.2)
            prims.glow(c, 0, -6, 46, look.FOG_LIGHT, 0.55 * dent, 1.6)
            c.restore()
            # a thin leak of paler grey from the dent
            for k in range(5):
                ph_k = (t * (0.35 + 0.1 * k) + H01(k, 501)) % 1.0
                lx = hx - 30 + 60 * H01(k, 502) + 8 * math.sin(t + k)
                ly0 = hy - 6 + 120 * ph_k
                c.drawLine(lx, ly0, lx + 4 * math.sin(t * 0.7 + k), ly0 + 36 + 30 * H01(k, 503),
                           prims.stroke(look.FOG_LIGHT, 2.0 + 1.5 * H01(k, 504), 0.35 * dent * math.sin(math.pi * ph_k)))
        moth_on = place == "dusk"
        if moth_on:
            _moth(ctx, lamp, tl.cue(34).t)
        an = _child(ctx, CX2, pose, eye="half" if up < 0.5 else "open", head_tilt=0.35 * up)
    # the amber mote: near the shoulder, off to the moth with line 34, back before the next place
    sx, sy = an["shoulder"]
    wx, wy = lights.wander(7, t, 1.0)
    mx, my = sx - 46 + 14 * wx, sy - 64 + 12 * wy
    t34 = tl.cue(34).t
    go = smoothstep(t34, t34 + 1.1, t) * (1.0 - smoothstep(t34 + 1.4, t34 + 1.95, t))
    if go > 0 and lamp is not None and moth_on:
        qx, qy, _hd = lights.moth_pos(lamp[0], lamp[1] + 4, t + 1.3, 58, 3)
        mx, my = mx + (qx - mx) * go, my + (qy - my) * go
    lights.mote(ctx, mx, my, 1.15, smoothstep(sec.t0 - 0.2, sec.t0 + 0.8, t), 7, t)


# ------------------------------------------------------------------------------------------------
# p2b
# ------------------------------------------------------------------------------------------------
N_SWIRL = 24


def _swirl(ctx, cx, cy, front, gather, chest):
    tl, t, c = ctx.tl, ctx.t, ctx.canvas
    tau = _beatpos(tl, t) - _beatpos(tl, ctx.sec.t0)
    n = int(6 + 18 * smoothstep(ctx.sec.t0, ctx.sec.t0 + 4.0, t) * (0.6 + 0.4 * ctx.loud))
    for i in range(min(n, N_SWIRL)):
        a = 6.283 * H01(i, 601) + 6.283 * (0.07 * tau + 0.006 * tau * tau) * (0.7 + 0.6 * H01(i, 602))
        if (math.sin(a) > 0) != front:
            continue
        r = (300 + 360 * H01(i, 603)) * (1 - gather) + 10 * ctx.pulse(0.2)
        x = cx + math.cos(a) * r + (chest[0] - cx) * gather
        y = cy + math.sin(a) * min(150.0, r * 0.32) - 60 * HS(i, 604) * (1 - gather) + (chest[1] - cy) * gather
        rot = 60 * HS(i, 605) + 90 * tau * 0.1 * HS(i, 606)
        flip = math.cos(tau * (0.5 + 0.5 * H01(i, 607)) + 6.28 * H01(i, 608))
        s = 0.30 * (0.8 + 0.4 * H01(i, 609)) * (1 - 0.3 * gather)
        scraps.draw_piece(c, i % scraps.N_PIECES, x, y, s, rot, 1.0 - gather, flip, 0.18, 14)


def _p2b(ctx):
    tl, t, c = ctx.tl, ctx.t, ctx.canvas
    sec = ctx.sec
    i, _tb = _bar_index(tl, sec, t)
    place = "play" if i < 2 else "open"
    t38, t39 = tl.cue(38).t, tl.cue(39).t
    hold = smoothstep(t38, t38 + 0.9, t)
    gather = smoothstep(t38 + 0.2, t38 + 1.5, t)
    wind = smoothstep(t39, t39 + 2.2, t)
    white = smoothstep(137.0, 138.2, t)
    holdp = figures.lean_wind(0.0, 0.45, 0.0, 1.0)
    pose = figures.blend(figures.stand(0.6), holdp, 0.55 * hold + 0.3 * wind)
    an = _anchors(x=CX2, y_feet=GY, h=HC, pose=pose, t=t, wind=wind)
    chest = an["chest"]
    cx, cy = CX2, GY - 0.55 * HC
    bounds = (-60, 260, W + 60, 900)
    with look.graded(ctx):
        places.draw(c, place, places.BASE)
        cloud.draw(ctx, _cloud_rect(350 + 20 * wind, CX2 + 60, 760 + 300 * wind), heavy=0.6 + 0.2 * wind, churn=1 + 1.2 * wind, seed=4)
        if wind > 0:
            look.wind(c, (0, 200, W, 860), t, strength=wind * (0.55 + 0.45 * ctx.pulse(0.3)), angle=-6, seed=3,
                      n=int(40 + 60 * wind), alpha=0.4)
    with look.graded(ctx, sat=0.55, cool=0.3, bounds=bounds):
        _swirl(ctx, cx, cy, False, gather, chest)
    with look.graded(ctx, bounds=(CX2 - 260, GY - HC - 80, CX2 + 260, GY + 40)):
        _child(ctx, CX2, pose, eye="half", wind=wind, wind_dir=-1, head_tilt=0.12 * (1 - hold))
    with look.graded(ctx, sat=0.55, cool=0.3, bounds=bounds):
        _swirl(ctx, cx, cy, True, gather, chest)
        if gather > 0.01:
            scraps.armful(c, chest[0] + 6, chest[1] + 8, 0.22, t * (1 + 4 * wind), seed=2, n=12,
                          spread=1.0 + 0.06 * wind * math.sin(t * 23), alpha=gather)
    if white > 0:
        look.fog_bank(c, (-60, 0, W + 60, H), t, 1.0, colors=(look.FOG_PALE, look.FOG_LIGHT, look.FOG_LIGHT),
                      speeds=(60, 120, 220), seed=8, alpha=0.8 * white)
        c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), prims.fill(P.mix(look.FOG_PALE, look.FOG_LIGHT, 0.6), 0.85 * white))
        look.wind(c, (0, 0, W, H), t, strength=1.0, angle=-6, seed=5, n=80, alpha=0.35 * (1 - 0.5 * white))


_DRAW = {"p1a": _p1a, "p1b": _p1b, "v2b": _v2b, "p2a": _p2a, "p2b": _p2b}


def draw(ctx):
    _DRAW[ctx.sec.id](ctx)
