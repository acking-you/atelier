"""The breakdown, the silence and the last chorus on the hill, then the outro along the ridge.
bd, hush2 and c3a are one continuous take; c3b and out follow the same walk."""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import skia

from mv.engine import palette as P
from mv.engine import prims

from hx.kit import birds, cloud, figures as F, lights, look, scraps

from . import _hill_set as S
from ._hill_world import (BD_CAM, BD_UNDER, CHILD_BD_X, CHILD_H, FRIEND_H, ONSETS, T_OUT0, T_OUT_STOP, T_RING,
                          T_STEP, T_WALK0, T_WALK1, TL, World, ease, fig, friend_bd, grade_at, holes_bd,
                          jump_squat, kick_breath, lid_rect, lit_at, out_back, out_cubic, paint, run_at, ss,
                          stride_at, walk_arm, walk_phase, walk_x)

H01, HS = prims.hash01, prims.hash_sym
W, H = S.W, S.H
T_TEAR = 201.25
CHILD_IN = CHILD_BD_X - 85.0 + 32.0          # where the child stands in the last shaft
FRIEND_IN = CHILD_BD_X - 85.0 - 28.0
GAP = CHILD_IN - FRIEND_IN
STEP_STRIDE = 0.25                            # three small steps into the light


def child_x(t):
    if t < T_STEP:
        return CHILD_BD_X
    return CHILD_BD_X + (CHILD_IN - CHILD_BD_X) * ss(T_STEP + 0.05, T_STEP + 1.15, t) + walk_x(t)


def _screen(cam, x):
    return cam.pt(x, float(S.ground_y(x)), 1.0)


def _scaled(canvas, x, y, sx, sy):
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(sx, sy)
    canvas.translate(-x, -y)


# ---------------------------------------------------------------------------------------------
# the lid, the crows, the light through the holes
# ---------------------------------------------------------------------------------------------
def _lid_bd(cam, t, holes, tear=0.0, density=1.0, widen=0.0):
    rect = lid_rect(BD_CAM, BD_CAM, BD_UNDER, widen=widen + 700.0)
    seam = None
    sh = lid_drift(t) * BD_CAM.zd(S.D_LID)          # holes stay put while the lid body drifts past
    hs = [(x - sh, y, r, a) for x, y, r, a in (h["hole"] for h in holes)]
    seam_pts = list(hs)
    # as the rip opens through them the holes hand over to it: they close inside the widening tear
    k = 1.0 - ss(T_TEAR, T_TEAR + 0.6, t)
    hs = [(x, y, r, a * k) for x, y, r, a in hs] if k > 0.001 else []
    if seam_pts:
        # the rip runs through the holes (the kit composes holes and tear as one mask)
        l, _, r, _ = rect
        srt = sorted(seam_pts, key=lambda q: q[0])
        seam = [(l - 0.1 * (r - l), srt[0][1])] + [(q[0], q[1]) for q in srt] + [(r + 0.1 * (r - l), srt[-1][1])]
    return dict(rect=rect, density=density, heavy=0.45, churn=0.9 + 1.4 * ss(T_TEAR, T_TEAR + 1, t), holes=hs,
                tear=tear, seam=seam, seed=9, lit=P.mix(look.PEACH, look.AMBER, 0.4), rim=0.3)


def lid_drift(t):
    return 6.0 * (t - 182.3) + 28.0 * max(0.0, t - T_TEAR)


def _wheel_center(cam):
    return cam.pt(*BD_CAM.inv(1380, 540, S.D_LID), S.D_LID)


def _crows(t, cam, tear_xy):
    """Wheeling low over the fog; ON the tear they burst outward from it (fast, then slowing) and
    become ordinary small birds."""
    n = 15
    ts = min(t, T_TEAR)
    f = birds.flock_wheel(n, ts, _wheel_center(cam), 230.0, seed=4, speed=0.45)
    xs, ys, hd, ph = f["x"], f["y"], f["heading"], f["phase"]
    sm = 0.0
    if t > T_TEAR:
        s = t - T_TEAR
        tx, ty = tear_xy
        ids = np.arange(n)
        ang = np.arctan2(ys - ty, xs - tx) + 0.5 * HS(ids, 450) - 0.35
        dist = (700 + 500 * H01(ids, 451)) * (1 - np.exp(-s / (0.7 + 0.5 * H01(ids, 452))))
        xs = xs + np.cos(ang) * dist + 25 * s * HS(ids, 453)
        ys = ys + np.sin(ang) * dist * 0.8 - 18 * s
        hd = ang
        sm = ss(T_TEAR + 0.3, T_TEAR + 3.0, t)
        ph = ph + s * 6.283 * birds.flap_rate(sm) * 0.3
    return dict(xs=xs, ys=ys, s=16.0, phases=ph, headings=hd, banks=f["bank"], scales=f["scale"], small=sm)


def _behind_holes(holes, strength):
    def fn(c):
        if strength <= 0:
            return
        for h in holes:
            x, y, r, a = h["hole"]
            prims.glow(c, x, y, r * 1.8, look.PEACH, 0.35 * a * strength)
    return fn


def _screen_disc(c, x, y, r, color, a):
    if a <= 0.004 or r <= 1:
        return
    p = prims.radial_paint((x, y), r, color, a, power=1.6)
    p.setBlendMode(skia.BlendMode.kScreen)
    c.drawCircle(x, y, r, p)


def _attacks(ctx, holes, cam, fade):
    """Each attack: a flash in the hole, the shaft sweeping down to the hill in about 5 frames, a
    puff of dust and pollen where it lands, the lit patch blooming."""
    t = ctx.t
    c = ctx.canvas
    biggest = {h["i"] for h in sorted(holes, key=lambda h: -h["size"])[:5]}
    pxs, pds, prs, pal = [], [], [], []
    for h in holes:
        x, y, r, a = h["hole"]
        fx, fy = h["foot"]
        st = h["size"]
        ti = ONSETS[h["i"]][0]
        s = t - ti
        flash = math.exp(-max(0.0, s) / 0.035) if s < 0.25 else 0.0
        _screen_disc(c, x, y, r * 1.5, look.PAPER, 0.35 * flash)
        if flash > 0.01:
            prims.glow(ctx.glow, x, y, r * 2.0, look.PAPER, 0.8 * flash)
        _screen_disc(c, x, y, r * 1.3, look.AMBER, 0.24 * a * fade)
        e = out_cubic(s / 0.17)
        ex, ey = x + (fx - x) * e, (y + r * 0.2) + (fy - y - r * 0.2) * e
        look.shaft(ctx, x, y + r * 0.2, ex, ey, r * 1.1, (r * 1.1) + (r * 0.8 + 30 * st) * e, color=look.AMBER,
                   alpha=(0.20 + 0.16 * st) * min(1.0, a) * fade * (1 + 0.6 * flash),
                   dust=0.8 if h["i"] in biggest else 0.0, seed=h["i"], glow=0.5)
        land = s - 0.15
        if land > 0:
            bloom = out_back(land / 0.4, 2.0)
            pxs.append(h["wx"])
            pds.append(8.0)
            prs.append((60 + 70 * st) * (0.5 + 0.5 * bloom))
            pal.append(0.55 * fade * min(1.0, bloom))
            if land < 1.2:
                _puff(ctx, cam, h["wx"], land, st, h["i"])
    S.soft_patches(c, cam, pxs, pds, prs, P.mix(look.MEADOW, look.MEADOW_LIGHT, 0.5), pal, squash=0.26)
    S.soft_patches(c, cam, pxs, pds, [r * 0.7 for r in prs], look.AMBER, [a * 0.45 for a in pal], squash=0.24,
                   additive=True)


def _puff(ctx, cam, wx, s, st, seed):
    """A ring of dust kicked out where a shaft lands, and pollen lifting from it."""
    gx, gy = cam.pt(wx, float(S.ground_y(wx)) + 8.0, 1.0)
    z = cam.zd(1.0)
    n = 22
    ids = np.arange(n) + seed * 97
    ang = 6.283 * (np.arange(n) + 0.5 * H01(ids, 460)) / n
    rr = (20 + (90 + 60 * st) * out_cubic(s / 0.7)) * (0.7 + 0.5 * H01(ids, 461)) * z
    xs = gx + np.cos(ang) * rr
    ys = gy + np.sin(ang) * rr * 0.28 - 10 * z * s
    a = (1 - s / 1.2) ** 1.5
    prims.draw_dots(ctx.canvas, xs, ys, 1.8 * z ** 0.5, P.mix(look.PAPER, look.AMBER, 0.4), alphas=np.full(n, 0.55 * a))
    up = gy - (40 + 70 * H01(ids[:10], 462)) * z * out_cubic(s / 1.0)
    prims.draw_dots(ctx.canvas, gx + 40 * HS(ids[:10], 463) * z * (0.4 + s), up, 1.3, look.AMBER,
                    alphas=np.full(10, 0.7 * a))


def _bump(t):
    """The camera's small bump on each attack, decaying in about 0.3 s (screen px)."""
    b = 0.0
    for ti, st in ONSETS:
        s = t - ti
        if 0 <= s < 0.5:
            b += (4 + 7 * st) * math.exp(-s / 0.09) * math.cos(s * 32)
    return b


# ---------------------------------------------------------------------------------------------
# the camera of the long take
# ---------------------------------------------------------------------------------------------
PUSH = S.Cam(180.0, 545.0, 0.93)                # the breath before the release
RELEASE = S.Cam(150.0, 400.0, 0.68)             # pulled back and craned up: far more sky


def _cam_take(ctx):
    t = ctx.t
    drift = ss(193.0, 200.4, t) * 7.0 + 14.0 * ss(182.3, 193.0, t)
    cam = S.Cam(drift - 14.0, BD_CAM.cy, BD_CAM.z * (1 + 0.025 * ss(182.3, 193.0, t)) + 0.01 * ss(193.0, 200.4, t))
    if t > 200.4:
        cam = S.Cam.lerp(cam, PUSH, ss(200.4, T_TEAR, t))
    if t > T_TEAR:
        cam = S.Cam.lerp(cam, RELEASE, ease(T_TEAR, T_TEAR + 1.8, t, lambda u: out_back(u, 0.8)))
    if t > T_WALK0 - 0.3:
        mid = child_x(t) - GAP * 0.5 + 60.0 + 24.0 * max(0.0, t - T_WALK0)
        k = ss(204.0, 213.1, t)
        follow = S.Cam(mid, 470.0 + 40.0 * k + (float(S.ground_y(mid)) - S.CREST_Y) * 0.9, 0.9 * (1 + 0.16 * k))
        cam = S.Cam.lerp(cam, follow, ss(T_WALK0 - 0.3, 206.8, t))
    loud = t > T_TEAR
    by = _bump(t) if t < 193.5 else 0.0
    z = cam.z * (kick_breath(ctx) if loud else 1.0)
    return S.Cam(cam.cx, cam.cy - by / max(z, 0.1), z)


# ---------------------------------------------------------------------------------------------
# c3a: the release
# ---------------------------------------------------------------------------------------------
CUT_BEATS = (276, 278, 280)


def _passes(x, t0):
    lo, hi = t0, T_WALK1
    if child_x(hi) < x:
        return hi
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if child_x(mid) < x else (lo, mid)
    return hi


def _cutouts(t):
    """(kind, world x, stand) of the three cut-outs: pop up with overshoot on their beat, fall
    flat as the child passes, bounce once."""
    out = []
    for j, k in enumerate(CUT_BEATS):
        tb = TL.beat_time(k)
        if t < tb:
            continue
        x = child_x(tb + 1.7) + 26.0 + 10.0 * j
        stand = out_back((t - tb) / 0.35, 2.4)
        tt = _passes(x - 8.0, tb)
        s = t - tt
        if s > 0:
            fall = min(1.0, (s / 0.38) ** 2)
            stand = stand * (1 - fall)
            if s > 0.38:
                stand += 0.16 * math.exp(-(s - 0.38) / 0.14) * abs(math.sin((s - 0.38) * 15))
        out.append((j, x, stand))
    return out


def _tear_amount(t):
    if t < T_TEAR:
        return 0.0
    return 0.55 * out_back((t - T_TEAR) / 0.5, 1.2) + 0.30 * ss(T_TEAR + 0.5, 204.0, t)


def _swell(t):
    """Exposure/bloom swell: up over about 0.6 s, then a long settle."""
    if t < T_TEAR:
        return 0.0
    x = (t - T_TEAR) / 0.6
    return out_cubic(x) * (1 - 0.45 * ss(1.0, 6.0, x))


def _burst(ctx, cam, t, x0):
    """Pollen and petals thrown up by the gust front running outward from under the tear."""
    s0 = t - T_TEAR
    if s0 <= 0 or s0 > 6.0:
        return
    n = 140
    ids = np.arange(n)
    side = np.where(H01(ids, 470) < 0.5, -1.0, 1.0)
    dist = 80 + 1500 * H01(ids, 471) ** 0.8
    launch = dist / 1300.0
    s = s0 - launch
    on = (s > 0) & (s < 3.2)
    if not on.any():
        return
    ids, side, dist, s = ids[on], side[on], dist[on], s[on]
    wx = x0 + side * dist + side * (60 + 120 * H01(ids, 472)) * s
    wy = S.ground_y(wx) + 40 * H01(ids, 473) - (160 + 220 * H01(ids, 474)) * s + 70 * s * s
    sx, sy = cam.pt(wx, wy, 1.0)
    a = np.clip(1 - s / 3.2, 0, 1) * np.clip(s / 0.15, 0, 1)
    petal = H01(ids, 475) < 0.35
    prims.draw_dots(ctx.canvas, sx[~petal], sy[~petal], 1.6, P.mix(look.AMBER, look.PAPER, 0.5),
                    alphas=0.8 * a[~petal])
    for k, col in enumerate(look.FLOWERS):
        m = petal & ((ids % 5) == k)
        if m.any():
            prims.draw_dots(ctx.canvas, sx[m], sy[m], 3.0, P.mix(col, look.PAPER, 0.45), alphas=0.85 * a[m])


def _god_rays(ctx, x, y, a, t):
    if a <= 0.01:
        return
    for k in range(7):
        ang = math.radians(-38 + 76 * k / 6 + 7 * math.sin(t * 0.45 + k * 1.3) + 4 * HS(k, 480))
        ln = 1100
        fx, fy = x + math.sin(ang) * ln, y + math.cos(ang) * ln
        look.shaft(ctx, x, y, fx, fy, 60, 260 + 120 * H01(k, 481), color=look.PEACH,
                   alpha=a * (0.06 + 0.04 * H01(k, 482)) * (0.7 + 0.3 * math.sin(t * 1.3 + k)), dust=0.0,
                   seed=40 + k, glow=0.4)


def take(ctx):
    """bd, hush2 and c3a: one continuous take."""
    t = ctx.t
    cam = _cam_take(ctx)
    z = cam.zd(1.0)
    holes = holes_bd(t, cam)
    tear = _tear_amount(t)
    flood = ss(T_TEAR, T_TEAR + 2.5, t)
    sw = _swell(t)
    sat, cool = grade_at(t)
    lid = _lid_bd(BD_CAM, t, holes_bd(t, BD_CAM), tear)
    sky = {"overcast": 0.75 * (1 - flood), "golden": 0.25 * (1 - flood) + 0.3 * flood, "day": 0.7 * flood}
    cuts = _cutouts(t)
    x0 = float(np.mean([h["wx"] for h in holes])) if holes else 0.0
    if holes:
        tx = float(np.mean([h["hole"][0] for h in holes]))
        ty = float(np.mean([h["hole"][1] for h in holes]))
    else:
        tx, ty = W * 0.4, 380.0

    def near(c):
        for j, x, stand in cuts:
            bx, by = cam.pt(x, float(S.ground_y(x)) + 62.0, 1.0)
            S.draw_cutout(c, j, bx, by, 64.0 * z, stand, P.mix(look.PAPER, look.FOG_PALE, 0.45), look.DUSK)

    waves = []
    if t > T_TEAR - 0.1:
        waves.append((T_TEAR, x0, 1300.0, 1.4, 0))
        waves += [(float(b), -1600.0, 1000.0, 0.6, 1) for b in TL.beats_between(T_TEAR + 1.4, t + 0.01)[::2]]
    w = World(t, cam, sky, lit=lit_at(t), lid=lid, fog=1.0 - 0.3 * flood,
              sway=(0.45 if t < 193.0 else 0.22 if t < T_TEAR else 0.85), gust=0.1 * flood, wind_dir=1.0,
              crows=_crows(t, cam, (tx, ty)), behind_lid=_behind_holes(holes, 0.35 * flood), near_extra=near,
              roofs=0.0, lid_ref=BD_CAM, lid_dx=lid_drift(t), lid_alpha=1.0 - 0.45 * ss(203.0, 210.0, t), waves=tuple(waves), flow=(1.6 if t < 193.0 else 1.0) + 2.0 * flood, fringe=0.4 + 0.15 * flood)
    # the child: watches, then three small steps into the light at the strongest attack, head lifting
    cx = child_x(t)
    if t < T_STEP:
        cpose, cface = F.stand(0.6), -1
        ctilt = 0.25 + 0.15 * ss(184.5, 186.0, t)
        ceye = "open"
    elif t < T_WALK0 - 0.3:
        stepw = ss(T_STEP - 0.05, T_STEP + 0.15, t) * (1 - ss(T_STEP + 1.05, T_STEP + 1.35, t))
        ph = (cx - CHILD_BD_X) / (STEP_STRIDE * CHILD_H)
        cpose = F.blend(F.stand(0.55 - 0.15 * ss(T_STEP + 1.0, T_STEP + 3.0, t)), F.walk(ph, 0.55, STEP_STRIDE), stepw)
        cface = -1
        ctilt = 0.25 + 0.55 * ss(T_STEP + 0.9, T_STEP + 2.6, t) * (1 - 0.4 * ss(T_TEAR + 0.5, T_WALK0 - 0.3, t))
        ceye = "closed" if 193.4 < t < 200.6 else "open"
    else:
        slump = 0.6 - 0.3 * ss(T_WALK0, 208.0, t)
        stride = max(0.40, stride_at(t))
        ww = ss(T_WALK0 - 0.3, T_WALK0 + 0.3, t) * (1 - ss(T_WALK1 - 0.2, T_WALK1 + 0.3, t))
        cpose = F.blend(F.stand(slump), F.walk(walk_phase(t), slump, stride), ww)
        cface = 1
        ctilt = 0.15 + 0.2 * (1 - flood)
        ceye = "open"
    mood = -0.3 + 0.3 * ss(T_STEP, 196.0, t) + 0.3 * ss(T_TEAR, 206.0, t)
    with look.graded(ctx, sat, cool):
        paint(ctx, w)
        x_s, y_s = _screen(cam, cx)
        fig(ctx.canvas, "child", x_s, y_s, CHILD_H * z, cpose, cface, head_tilt=ctilt, eye=ceye, t=t,
            wind=0.15 + 0.3 * flood, wind_dir=1, mood=mood, rim=0.3 + 0.4 * flood)
    _attacks(ctx, holes, cam, fade=1.0 - ss(T_TEAR + 0.2, T_TEAR + 2.5, t))
    _god_rays(ctx, tx, ty, flood * (1 - 0.5 * ss(206.0, 212.0, t)), t)
    _burst(ctx, cam, t, x0)
    # the friend: squat, leap (palms up ON the attack), land; then beside the child
    if t < T_WALK0 - 0.3:
        fx, push, hop, mv = friend_bd(t)
        fx = min(fx, cx - 40.0) if t > T_STEP else fx
        ph = fx / (0.6 * FRIEND_H)
        moving = abs(mv) > 0 and push < 0.5
        base = F.walk(ph, 0.2, 0.6) if moving else F.stand(0.1)
        fpose = F.blend(base, F.push_up(), push)
        fface = -1 if mv < 0 and push < 0.5 else 1
        after = ss(T_STEP + 0.6, T_STEP + 2.0, t)
        fpose = F.blend(fpose, F.stand(0.1), after)
        ftilt = 0.3 + 0.4 * after
        dy = -hop * 0.26 * FRIEND_H
        squat = max([jump_squat(t - ti) * (0.6 + 0.4 * st) for ti, st in ONSETS]) * (1 - after)
        fsmile = 0.25 * after * ss(194.0, 197.0, t)
    else:
        fx = child_x(t) - GAP
        ww = ss(T_WALK0 - 0.3, T_WALK0 + 0.3, t) * (1 - ss(T_WALK1 - 0.2, T_WALK1 + 0.3, t))
        fpose = F.blend(F.stand(0.1), F.walk(walk_phase(t), 0.1, max(0.40, stride_at(t)) * CHILD_H / FRIEND_H), ww)
        fface, ftilt, dy, fsmile, squat = 1, 0.2, 0.0, 0.3, 0.0
    fxs, fys = _screen(cam, fx)
    _scaled(ctx.canvas, fxs, fys, 1 + 0.06 * squat, 1 - 0.14 * squat)
    fig(ctx.canvas, "friend", fxs, fys + dy * z, FRIEND_H * z, fpose, fface, head_tilt=ftilt, eye="open",
        smile=fsmile, t=t, wind=0.1 + 0.3 * flood, wind_dir=1, rim=0.5, mood=0.5)
    ctx.canvas.restore()
    if t > 192.5:
        pa = ss(192.5, 194.5, t) * (1 - 0.5 * flood)
        l_, _ = cam.pt(FRIEND_IN - 260, 0, 1.0)
        r_, _ = cam.pt(CHILD_IN + 260, 0, 1.0)
        lights.pollen(ctx, (l_, 300, r_, 820), t=t, n=70, seed=3, alpha=0.65 * pa, drift=(4.0, -2.0), glow=0.5)
    if flood > 0:
        # the air is full of light: pollen streaming on the wind across the whole frame
        lights.pollen(ctx, (0, 0, W, 860), t=t, n=150, seed=8, alpha=0.55 * flood, drift=(70.0, -14.0), glow=0.3)
        wash = prims.linear_paint((0, 0), (W * 0.6, H), [look.PEACH, look.AMBER, look.AMBER], (0, 0.5, 1),
                                  alphas=[0.16 * flood, 0.06 * flood, 0.0])
        wash.setBlendMode(skia.BlendMode.kScreen)
        ctx.canvas.drawRect(skia.Rect.MakeWH(W, H), wash)
        prims.glow(ctx.glow, tx, ty, 700, look.PEACH, 0.35 * flood + 0.25 * sw)
    ctx.post.exposure = 0.93 + 0.06 * flood + 0.10 * sw
    ctx.post.bloom = 1.0 + 0.12 * flood + 0.45 * sw
    ctx.post.vignette = 1.15 - 0.2 * flood


# ---------------------------------------------------------------------------------------------
# c3b: the close two-shot, the smile, the flowers; the colour ring and the biggest move of the film
# ---------------------------------------------------------------------------------------------
def _stop_x():
    return child_x(T_WALK1 + 0.6)


S.FOOT_X = _stop_x() - GAP / 2
T_CLOSE = TL.beat_time(286)                    # 214.77: the cut to the close two-shot, on the downbeat
T_OPEN = 221.5
SOFT = 190.0
T_FULL = 220.6


def _cams_c3b():
    mid = _stop_x() - GAP / 2
    gy = float(S.ground_y(mid))
    medium = S.Cam(mid + 60.0, gy - 210.0, 1.25)
    close0 = S.Cam(mid - 25.0, gy - 0.40 * CHILD_H, 3.2)
    close1 = S.Cam(mid + 10.0, gy - 0.44 * CHILD_H, 3.8)
    wide = S.Cam(mid + 140.0, gy - 400.0, 0.8)
    high = S.Cam(mid + 200.0, gy - 470.0, 0.74)
    return medium, close0, close1, wide, high


def _cam_c3b(ctx):
    t = ctx.t
    medium, close0, close1, wide, high = _cams_c3b()
    if t < T_CLOSE:
        cam = S.Cam(medium.cx + 30 * ss(213.1, T_CLOSE, t), medium.cy, medium.z * (1 + 0.04 * ss(213.1, T_CLOSE, t)))
    else:
        cam = S.Cam.lerp(close0, close1, ss(T_CLOSE, T_RING, t))
        if t > T_RING:
            cam = S.Cam.lerp(cam, wide, ease(T_RING + 0.25, T_OPEN, t, lambda u: u * u * u * (u * (6 * u - 15) + 10)))
        if t > T_OPEN:
            cam = S.Cam.lerp(cam, high, ss(T_OPEN, 226.8, t))
    return S.Cam(cam.cx, cam.cy, cam.z * kick_breath(ctx, 0.8))


def ring_radius(t, cx, cy):
    """From nothing at line 62's stamp to past the farthest corner (plus the soft edge) at T_FULL."""
    far = max(math.hypot(cx - x, cy - y) for x in (0, W) for y in (0, H)) + SOFT + 20.0
    u = (t - T_RING) / (T_FULL - T_RING)
    if u >= 1.0:
        return far + (t - T_FULL) * 400.0
    u = max(0.0, u)
    return far * (0.25 * u + 0.75 * (1 - (1 - u) ** 2))


def _ring_front(ctx, rx, ry, rad, a, t):
    """The leading edge: a thin band of light and a front of petals and pollen blown outward."""
    if a <= 0.01 or rad < SOFT:
        return
    r0 = max(1.0, rad - SOFT * 0.75)
    r1 = rad - SOFT * 0.25
    r2 = rad + 30
    stops = [0.0, r0 / r2, r1 / r2, 1.0]
    p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kScreen)
    pk = look.PEACH
    p.setShader(skia.GradientShader.MakeRadial((rx, ry), r2, [P.sk(pk, 0), P.sk(pk, 0), P.sk(pk, 0.32 * a),
                                                              P.sk(pk, 0)], stops))
    ctx.canvas.drawRect(skia.Rect.MakeWH(W, H), p)
    n = 160
    ids = np.arange(n)
    ang = 6.283 * H01(ids, 490)
    rr = r1 + 70 * HS(ids, 491) + 40 * np.sin(t * 3 + ids)
    xs, ys = rx + np.cos(ang) * rr, ry + np.sin(ang) * rr * 0.9 - 20 * H01(ids, 492)
    vis = (xs > -20) & (xs < W + 20) & (ys > -20) & (ys < H * 0.86)
    for k, col in enumerate(look.FLOWERS):
        m = vis & ((ids % 5) == k)
        if m.any():
            prims.draw_dots(ctx.canvas, xs[m], ys[m], 3.2, col, alphas=np.full(int(m.sum()), 0.85 * a))
    m = vis & (ids % 3 == 0)
    prims.draw_dots(ctx.canvas, xs[m] + 9, ys[m] - 6, 1.6, look.AMBER, alphas=np.full(int(m.sum()), 0.9 * a))


def _lens_birds(ctx, t, t0):
    """After the colour arrives: paper birds and small birds sweep past close to the lens."""
    for i in range(6):
        ti = t0 + 0.75 * i + 0.3 * H01(i, 500)
        s = t - ti
        if not 0 <= s < 1.6:
            continue
        d = 1 if i % 2 == 0 else -1
        x = (W / 2 - d * (W / 2 + 200)) + d * (W + 400) * (s / 1.6)
        y = 180 + 380 * H01(i, 501) - 120 * s + 30 * math.sin(s * 4)
        if i % 3 == 2:
            birds.flying(ctx.canvas, x, y, 70 + 30 * H01(i, 502), s * 6.283 * birds.flap_rate(1.0),
                         heading=0.0 if d > 0 else math.pi, small=1.0)
        else:
            scraps.paper_bird(ctx.canvas, x, y, size=90 + 60 * H01(i, 503), phase=s * 6.283 * 1.4 + i,
                              heading=(-10 if d > 0 else 190), tex=(i * 5) % 12)


def c3b(ctx):
    t = ctx.t
    cam = _cam_c3b(ctx)
    z = cam.zd(1.0)
    xc = _stop_x()
    sat0, cool0 = grade_at(min(t, T_RING))
    after = ss(T_RING, 221.0, t)
    lid_a = 0.55 * (1.0 - ss(215.2, T_RING - 0.1, t))
    lid = None
    if lid_a > 0.002:
        holes = holes_bd(213.0, BD_CAM)
        lid = _lid_bd(BD_CAM, t, holes, 0.85 + 0.15 * ss(213.1, T_RING, t))
    whites = [(cam.pt(-900 + 900 * k + 300 * H01(k, 400), 0, 0.08)[0] - 4 * (t - T_RING), 140 + 90 * H01(k, 401),
               (190 + 160 * H01(k, 402)) * cam.zd(0.08), 20 + k) for k in range(4)]
    t61 = TL.cue(61).t
    beats = TL.beats_between(t61 - 0.05, 240.0)
    cl_open = {c: float(beats[i]) for i, c in enumerate(S.FOOT_IDS[:4]) if i < len(beats)}
    cx_now = child_x(t)
    mx, my = cam.pt(cx_now - GAP / 2, float(S.ground_y(cx_now)) - 0.55 * CHILD_H, 1.0)
    rad = ring_radius(t, mx, my) if t >= T_RING else 0.0

    def open_fn(ids, xs, ys):
        out = np.zeros(len(ids))
        for n, c in enumerate(ids):
            tb = cl_open.get(int(c))
            if tb is not None and t > tb:
                out[n] = out_back((t - tb) / 0.45, 2.4)
        if t >= T_RING:
            sx, sy = cam.pt(xs, ys, 1.0)
            d = np.hypot(sx - mx, sy - my) + 80 * prims.hash01(np.arange(len(ids)), 504)
            u = np.clip((rad - SOFT * 0.5 - d) / 260.0, 0, 1)
            v = u - 1
            back = 1 + 3.4 * v ** 3 + 2.4 * v ** 2
            out = np.maximum(out, np.where(u > 0, back, 0.0))
        if t > 222.5:
            out[:] = 1.0
        return out

    bow = (mx, my, rad - SOFT * 0.4, 130.0, 1.0 - ss(T_FULL, T_FULL + 0.8, t)) if T_RING <= t < T_FULL + 0.8 else None
    w = World(t, cam, {"day": 0.85, "golden": 0.15}, lit=lit_at(t), lid=lid, lid_alpha=lid_a, lid_ref=BD_CAM, lid_dx=lid_drift(t), fog=0.6, sway=0.75,
              gust=0.1, flowers=open_fn, roofs=after, whites=whites, white_alpha=ss(T_RING - 0.3, T_RING + 1.2, t),
              crows=None, bow=bow, flow=2.5, fringe=0.0 if T_CLOSE <= t < T_RING + 1.5 else 0.5)
    ww = 1 - ss(T_WALK1 - 0.2, T_WALK1 + 0.3, t)
    cpose = F.blend(F.stand(0.3 - 0.1 * after), F.walk(walk_phase(t), 0.3, 0.55), ww)
    cface = 1 if t < 216.0 else -1
    tint = ease(T_RING, T_RING + 0.45, t)
    csmile = 0.5 * ease(T_RING + 0.08, T_RING + 0.9, t)
    cmood = 0.1 * ss(T_CLOSE, T_RING, t) + 0.5 * ease(T_RING, T_RING + 1.5, t)

    def world():
        paint(ctx, w)
        x_s, y_s = _screen(cam, cx_now)
        fig(ctx.canvas, "child", x_s, y_s, CHILD_H * z, cpose, cface, tint=tint, smile=csmile, eye="open",
            head_tilt=0.1 if t < 216 else 0.05, t=t, wind=0.15, wind_dir=1, mood=cmood, rim=0.5)

    if t < T_RING:
        with look.graded(ctx, sat0, cool0):
            world()
    else:
        look.reveal(ctx, world, mx, my, rad, soft=SOFT, sat=sat0, cool=cool0)
    turn = ease(t61, t61 + 0.9, t)
    fpose = F.blend(F.walk(walk_phase(t), 0.1, 0.55), F.stand(0.1), 1 - ww)
    fpose = replace(fpose, turn=0.45 * turn)
    fxn = cx_now - GAP
    fxs, fys = _screen(cam, fxn)
    fig(ctx.canvas, "friend", fxs, fys, FRIEND_H * z, fpose, 1, smile=0.15 + 0.75 * turn, eye="open",
        head_tilt=0.05, t=t, wind=0.15, wind_dir=1, mood=0.3 + 0.6 * turn, rim=0.5)
    if T_RING <= t < T_FULL + 0.6:
        _ring_front(ctx, mx, my, rad, 1.0 - ss(T_FULL - 0.3, T_FULL + 0.6, t), t)
    if t > 220.0:
        _paper_birds(ctx, t, 220.0)
        _lens_birds(ctx, t, T_FULL)
    ctx.post.exposure = 1.08 + 0.04 * after
    ctx.post.bloom = 1.3
    ctx.post.vignette = 0.95


def _paper_birds(ctx, t, t0, n=9):
    for i in range(n):
        ti = t0 + 0.6 * i
        if t < ti:
            continue
        s = t - ti
        d = 1 if H01(i, 410) > 0.35 else -1
        x = (W * (0.1 + 0.8 * H01(i, 411))) + d * s * (40 + 30 * H01(i, 412))
        y = 120 + 260 * H01(i, 413) - s * 6 + 10 * math.sin(s * 1.3 + i)
        a = min(1.0, s / 1.0)
        scraps.paper_bird(ctx.canvas, x, y, size=16 + 12 * H01(i, 414), phase=s * 6.283 * 1.6 + i,
                          heading=(0 if d > 0 else 180) - 8, alpha=a, tex=i % 12)


# ---------------------------------------------------------------------------------------------
# out: along the ridge in full colour; the gloom is a small cloud on a string; the light lowers
# ---------------------------------------------------------------------------------------------
RUNS = (232.77, 238.77)


def gold_at(t):
    k = (t - T_OUT0) / 3.0
    if k <= 0:
        return 0.0
    b = math.floor(k)
    return min(1.0, (b + ss(0.0, 0.6, k - b)) / 6.0)


def _squash(t):
    """A squash as each run starts and as it ends, recovering quickly."""
    q = 0.0
    for b0 in RUNS:
        for te in (b0 - 0.1, b0 + 2.75):
            s = t - te
            if 0 <= s < 0.6:
                q += math.exp(-s / 0.12) * math.sin(min(math.pi, s * 18))
    return q


def _sun_flare(ctx, sx, sy, a):
    if a <= 0.01:
        return
    c = ctx.canvas
    _screen_disc(c, sx, sy, 900, look.AMBER, 0.30 * a)
    _screen_disc(c, sx, sy, 160, look.PAPER, 0.55 * a)
    prims.glow(ctx.glow, sx, sy, 600, look.AMBER, 0.45 * a)
    vx, vy = W / 2 - sx, H * 0.45 - sy
    for k, (f, r, col) in enumerate(((0.45, 40, look.PEACH), (0.8, 22, look.AMBER), (1.25, 70, look.ROSE),
                                     (1.6, 30, look.PEACH))):
        _screen_disc(c, sx + vx * f, sy + vy * f, r, col, 0.10 * a)
    p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kScreen)
    p.setShader(skia.GradientShader.MakeLinear([(sx - 700, sy), (sx + 700, sy)],
                                               [P.sk(look.PEACH, 0), P.sk(look.PEACH, 0.18 * a), P.sk(look.PEACH, 0)],
                                               [0.0, 0.5, 1.0]))
    c.drawRect(skia.Rect.MakeLTRB(sx - 700, sy - 3, sx + 700, sy + 3), p)


def _fg_birds(ctx, t):
    for i in range(5):
        ti = T_OUT0 + 2.0 + 3.4 * i
        s = t - ti
        if not 0 <= s < 1.8:
            continue
        x = W + 150 - (W + 300) * s / 1.8
        y = 160 + 300 * H01(i, 510) + 40 * math.sin(s * 3)
        for j in range(1 + i % 3):
            birds.flying(ctx.canvas, x + 70 * j, y + 30 * HS(i * 3 + j, 511), 46 + 14 * H01(j, 512),
                         s * 6.283 * birds.flap_rate(1.0) + j, heading=math.pi, small=1.0)


def out(ctx):
    t = ctx.t
    gw = gold_at(t)
    cx = child_x(t)
    fx = cx - 78.0 - 10.0 * math.sin(t * 0.4)
    lead = 120.0 + 260.0 * ss(T_OUT0, 241.0, t)
    cam = S.Cam(cx + lead, float(S.ground_y(cx + lead)) - 240.0, 0.95 * kick_breath(ctx))
    z = cam.zd(1.0)
    whites = [(((-700 + 760 * k + 260 * H01(k, 420)) - 0.12 * cam.cx - 3.0 * (t - T_OUT0)) % 2600 - 300,
               110 + 120 * H01(k, 421), 200 + 180 * H01(k, 422), 30 + k) for k in range(5)]
    f = birds.flock_wheel(8, t, (1250 + 80 * math.sin(t * 0.2), 250), 160.0, seed=8, speed=0.7, small=1.0)
    crows = dict(xs=f["x"], ys=f["y"], s=14.0, phases=f["phase"], headings=f["heading"], banks=f["bank"],
                 scales=f["scale"], small=1.0, color=P.mix(birds.SMALL, look.INK, 0.15 * gw))
    waves = tuple((float(b), -3000.0 + 0 * b, 1100.0, 0.6, 1) for b in TL.beats_between(T_OUT0 - 4, t + 0.01)[::4])
    w = World(t, cam, {"day": 1 - gw, "golden": 0.85 * gw, "sunset": 0.15 * gw}, lit=1.0, gold=0.8 * gw, fog=0.5,
              sway=0.6, gust=0.2, wind_dir=-1.0, flowers=lambda ids, xs, ys: np.ones(len(ids)), roofs=1.0,
              whites=whites, crows=crows, waves=waves, flow=2.0, fringe=0.6)
    stop = ss(242.8, T_OUT_STOP, t)
    run = run_at(t)
    ph = walk_phase(t) if t < T_OUT_STOP else 0.0
    st = 0.55 + 0.45 * run
    gait = F.blend(F.walk(ph, 0.3, st), F.run(ph, max(0.6, st)), run)
    cpose = F.blend(walk_arm(gait, F.hold_string()), F.hold_string(0.3), stop)
    fgait = F.blend(F.walk(ph, 0.1, st * CHILD_H / FRIEND_H), F.run(ph, max(0.6, st) * CHILD_H / FRIEND_H), run)
    fpose = F.blend(walk_arm(fgait, F.hold_string(0.1)), F.hold_string(0.1), stop)
    sq = _squash(t)
    paint(ctx, w)
    c = ctx.canvas
    sun_x, sun_y = W * 0.92, 380.0 + 230.0 * gw
    _sun_flare(ctx, sun_x, sun_y, gw)
    fxs, fys = _screen(cam, fx)
    _scaled(c, fxs, fys, 1 + 0.05 * sq, 1 - 0.10 * sq)
    fa = fig(c, "friend", fxs, fys, FRIEND_H * z, fpose, 1, eye="open", smile=0.5, head_tilt=0.15, t=t, wind=0.35,
             wind_dir=-1, mood=0.8, rim=0.4 + 0.4 * gw)
    c.restore()
    hx, hy = fa["hand_n"]
    tug = ctx.pulse(0.25, every=2)
    kx = hx - 300 * z + 40 * math.sin(t * 0.7) - 30 * tug
    ky = max(80.0, hy - 430 * z + 30 * math.sin(t * 1.1) - 22 * tug)
    S.draw_kite(c, hx, hy, kx, ky, 26.0 * z, t, scraps.WAX["ray"])
    cxs, cys = _screen(cam, cx)
    _scaled(c, cxs, cys, 1 + 0.06 * sq, 1 - 0.12 * sq)
    ca = fig(c, "child", cxs, cys, CHILD_H * z, cpose, 1, tint=1.0, smile=0.4 + 0.1 * run, eye="open",
             head_tilt=0.1, t=t, wind=0.35, wind_dir=-1, mood=0.6, rim=0.4 + 0.4 * gw)
    c.restore()
    hxc, hyc = ca["hand_n"]
    bx, by = cloud.small(ctx, hxc - 115 * z, hyc - 190 * z, 125 * z, t=t, seed=3)
    cloud.string(c, bx, by, hxc, hyc, t, seed=1)
    _paper_birds(ctx, t, T_OUT0 - 4.0, n=4)
    _fg_birds(ctx, t)
    ctx.post.exposure = 1.06 - 0.04 * gw
    ctx.post.bloom = 1.2 + 0.25 * gw
    ctx.post.vignette = 0.95
