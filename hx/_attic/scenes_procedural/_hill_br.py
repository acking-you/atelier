"""The bridge on the hill: br_a (the scraps fly), br_b (warm rain, first green), br_c (the hands)."""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import skia

from mv.engine import palette as P
from mv.engine import prims

from hx.kit import birds, figures as F, lights, look, scraps

from . import _hill_set as S
from ._hill_world import (CHILD_H, FRIEND_H, TL, World, bar_waves, ease, fig, figure, grade_at, kick_breath,
                          lid_pts, lid_rect, lit_at, out_back, out_cubic, paint, ss)

HS, H01 = prims.hash_sym, prims.hash01
W, H = S.W, S.H

BRA_CAM0 = S.Cam(0.0, 550.0, 1.0)
BRB_CAM0 = S.Cam(-60.0, 600.0, 1.55)
BRC_CAM0 = S.Cam(-2.0, 642.0, 4.30)
# the thin tear left by c2b, upper right, fixed in the lid layer
TEAR_SEAM = [BRA_CAM0.inv(x, y, S.D_LID) for x, y in ((980, 230), (1390, 168), (1820, 214))]
TEAR_C = BRA_CAM0.inv(1390, 172, S.D_LID)
K0 = 212                                      # the first scrap lifts on this beat
LID_STREAM = 30.0                             # the lid streams to the right (lid-layer px/s)


def _stream(t):
    return LID_STREAM * (t - 158.86)


def _crows(t, cam, n=13, small=0.0):
    cx, cy = cam.pt(-650.0, 300.0, S.D_LID)
    f = birds.flock_wheel(n, t, (cx, cy), 230.0 * cam.zd(S.D_LID), seed=2, speed=0.55)
    return dict(xs=f["x"], ys=f["y"], s=15.0 * cam.zd(S.D_LID), phases=f["phase"], headings=f["heading"],
                banks=f["bank"], scales=f["scale"], small=small)


def _tear_xy(cam, t):
    return cam.pt(TEAR_C[0] + _stream(t), TEAR_C[1], S.D_LID)


def _seam(cam, t):
    return lid_pts(cam, [(x + _stream(t), y) for x, y in TEAR_SEAM])


def _tear_glow(cam, t, strength):
    def fn(c):
        x, y = _tear_xy(cam, t)
        prims.glow(c, x, y, 420 * cam.zd(S.D_LID), look.FOG_LIGHT, 0.55 * strength)
    return fn


def _wind(ctx, strength, alpha=0.45):
    look.wind(ctx.canvas, (0, 0, W, 860), ctx.t, strength=strength, angle=-7, seed=4, n=110, alpha=alpha)


# ---------------------------------------------------------------------------------------------
# br_a: medium-close as the arms open, then one long crane up and back with the paper birds
# ---------------------------------------------------------------------------------------------
CAM_CLOSE = S.Cam(25.0, 690.0, 3.0)
CAM_WIDE = S.Cam(70.0, 490.0, 1.0)


def _cam_bra(ctx):
    t = ctx.t
    u = ss(159.6, 168.2, t)
    cam = S.Cam.lerp(CAM_CLOSE, CAM_WIDE, u)
    drift = ss(168.2, 172.0, t)
    return S.Cam(cam.cx + 18 * drift, cam.cy - 8 * drift, cam.z * kick_breath(ctx) * (1 + 0.02 * drift))


def br_a(ctx):
    t = ctx.t
    cam = _cam_bra(ctx)
    pulse = ctx.pulse(0.3)
    sat, cool = grade_at(t)
    lid = dict(rect=lid_rect(BRA_CAM0, BRA_CAM0, 360.0, widen=700.0), density=1.0, heavy=0.55, churn=2.2,
               tear=0.24, seam=lid_pts(BRA_CAM0, TEAR_SEAM), seed=5)
    waves = bar_waves(158.86, 171.0, -1600.0, speed=1100.0, strength=1.0, d=1, every=4) \
        + bar_waves(158.86, 171.0, -1600.0, speed=1300.0, strength=0.45, d=1, every=2)
    w = World(t, cam, {"lid": 0.75, "overcast": 0.25}, lit=lit_at(t), lid=lid, sway=1.1, gust=0.35 + 0.2 * pulse,
              wind_dir=1.0, crows=_crows(t, cam), behind_lid=_tear_glow(cam, t, 1.0), waves=tuple(waves), flow=4.5,
              lid_ref=BRA_CAM0, lid_dx=_stream(t),
              fringe=0.45)
    open_w = ease(158.86, 159.45, t, out_back)
    hug = F.Pose(slump=0.5, lean=0.08, nod=0.2, arm_n=0.65, fore_n=2.2, arm_f=0.55, fore_f=2.05)
    arms = F.blend(F.arms_open(0.35), F.stand(0.45), 0.30 * ss(166.5, 170.5, t))
    # the arms give a little lift as each scrap leaves
    lift = sum(math.exp(-(t - TL.beat_time(K0 + k)) / 0.3) for k in range(12) if t >= TL.beat_time(K0 + k))
    arms = replace(arms, arm_n=arms.arm_n + 0.10 * min(1.0, lift), arm_f=arms.arm_f - 0.10 * min(1.0, lift))
    pose = F.blend(hug, arms, open_w)
    look_up = 0.15 + 0.45 * ss(160.0, 165.0, t)
    with look.graded(ctx, sat, cool):
        paint(ctx, w)
        a = figure(ctx, cam, "child", 0.0, CHILD_H, pose, 1, wind=1.0, wind_dir=1, head_tilt=look_up, eye="half",
                   mood=-0.3 + 0.2 * ss(160, 168, t), rim=0.3)
    figure(ctx, cam, "friend", -120.0, FRIEND_H, F.stand(0.2), 1, wind=0.9, wind_dir=1,
           head_tilt=0.35 * ss(160, 166, t), eye="open", rim=0.3)
    near_tear = _scraps(ctx, cam, a, sat)
    # light from the tear flickers over the hill as the birds cross it
    tx, ty = _tear_xy(cam, t)
    fx, fy = cam.pt(260.0, S.CREST_Y + 30, 1.0)
    fl = 0.5 + 0.5 * math.sin(t * 7.3) * math.sin(t * 3.1 + 1.0)
    look.shaft(ctx, tx, ty + 20, fx, fy, 70 * cam.zd(S.D_LID), 420 * cam.zd(1.0) ** 0.5, color=look.PAPER,
               alpha=0.05 + 0.07 * near_tear * fl, dust=0.0, glow=0.3)
    _wind(ctx, 0.45 + 0.55 * pulse, alpha=0.55)
    ctx.post.exposure = 0.92
    ctx.post.vignette = 1.15


def _scraps(ctx, cam, a, sat):
    """The armful, and each lifted scrap unfolding into a paper bird that spirals up to the tear.
    Paths live in the world (start on the hill, end in the lid layer) so the crane gives parallax.
    Returns how many birds are near the tear (for the flicker of its light)."""
    t = ctx.t
    hx, hy = a["hold"]
    zc = cam.zd(1.0)
    n_left = 12 - sum(1 for k in range(12) if t >= TL.beat_time(K0 + k))
    sx0, sy0 = cam.inv(hx, hy - 4 * zc, 1.0)
    tx0, ty0 = TEAR_C[0] + LID_STREAM * (t - 158.86), TEAR_C[1]
    near = 0.0
    with look.graded(ctx, max(sat, 0.42), 0.35):
        if n_left > 0:
            scraps.armful(ctx.canvas, hx, hy - 6 * zc, scale=0.10 * zc, t=t, seed=3, n=n_left, spread=0.75)
        for k in range(12):
            tk = TL.beat_time(K0 + k)
            if t < tk:
                continue
            i = 11 - k
            s = (t - tk) / 6.5
            if s >= 1.0:
                continue
            e = s ** 0.8
            cx, cy = sx0 + 60 + 50 * HS(k, 201), sy0 - 300 - 80 * H01(k, 202)
            tx, ty = tx0 + 160 * HS(k, 203), ty0 + 26 * HS(k, 204)
            px = (1 - e) ** 2 * sx0 + 2 * (1 - e) * e * cx + e * e * tx
            py = (1 - e) ** 2 * sy0 + 2 * (1 - e) * e * cy + e * e * ty
            # a rising spiral round the path, widest early
            R = 75.0 * (1 - e) * min(1.0, (t - tk) * 2.5)
            ang = (t - tk) * 2.6 + 6.283 * H01(k, 206)
            px += R * math.cos(ang)
            py += 0.45 * R * math.sin(ang)
            d = 1.0 + (S.D_LID - 1.0) * e ** 0.7
            x, y = cam.pt(px, py, d)
            vx = -R * 2.6 * math.sin(ang) + (tx - sx0)
            vy = 0.45 * R * 2.6 * math.cos(ang) + (ty - sy0) * 0.6
            wf = ease(tk + 0.05, tk + 0.65, t, out_cubic)
            flutter = 35.0 * math.sin((t - tk) * 17.0) * (1 - wf)
            size = (24.0 + 6.0 * H01(k, 205)) * cam.zd(d) * (1.0 - 0.35 * e)
            al = 1.0 - ss(0.82, 1.0, s)
            heading = math.degrees(math.atan2(vy, vx)) * wf + flutter
            scraps.unfold(ctx.canvas, i, x, y, wf, size=size, phase=t * 6.283 * 2.4 + k, heading=heading, alpha=al)
            near += math.exp(-((s - 0.9) / 0.08) ** 2)
    return min(1.5, near)


# ---------------------------------------------------------------------------------------------
# br_b: a slow push; rain builds; green spreads as a front from where the first drops land
# ---------------------------------------------------------------------------------------------
GREEN_X0, GREEN_D0, GREEN_T0 = -40.0, 30.0, 171.3


def _patches():
    out = []
    for p in range(44):
        x = -760.0 + 1400.0 * H01(p, 210)
        d = 8.0 + 300.0 * H01(p, 211) ** 1.3
        if abs(x) < 90 and d < 45:
            x += 160.0
        dist = math.hypot(x - GREEN_X0, (d - GREEN_D0) * 2.2)
        out.append((x, d, GREEN_T0 + dist / 190.0 + 0.4 * H01(p, 212), 50.0 + 95.0 * H01(p, 213)))
    return out


BRB_PATCHES = _patches()


def green_patches(ctx, cam, t, strength=1.0):
    xs, ds, rs, al = [], [], [], []
    for p, (x, d, tp, r) in enumerate(BRB_PATCHES):
        if t < tp:
            continue
        g = ease(tp, tp + 1.4, t, out_back)
        for j in range(3):
            q = p * 3 + j
            xs.append(x + r * 0.7 * HS(q, 214))
            ds.append(d + r * 0.25 * HS(q, 215))
            rs.append(r * (0.45 + 0.5 * H01(q, 216)) * (0.35 + 0.65 * g))
            al.append(0.40 * min(1.0, g) * strength * (0.6 + 0.4 * H01(q, 217)))
    S.soft_patches(ctx.canvas, cam, xs, ds, rs, P.mix(look.MEADOW, look.MEADOW_LIGHT, 0.3), al, squash=0.34)


def _low_sun(ctx, x, y, r, a):
    p = prims.radial_paint((x, y), r, look.PERSIMMON, a, power=2.0)
    p.setBlendMode(skia.BlendMode.kScreen)
    ctx.canvas.drawCircle(x, y, r, p)
    prims.glow(ctx.glow, x, y, r * 0.8, look.AMBER, a * 0.7)


def br_b(ctx):
    t = ctx.t
    u = ss(170.765, 178.265, t)
    cam = S.Cam(-60.0 + 15 * u, 600.0 + 20 * u, (1.42 * (1.85 / 1.42) ** u) * kick_breath(ctx, 0.6))
    sat, cool = grade_at(t)
    drain = ss(171.0, 178.0, t)
    lid = dict(rect=lid_rect(BRB_CAM0, BRB_CAM0, 300.0, widen=700.0), density=1.0 - 0.55 * drain,
               heavy=0.5, churn=1.6, tear=0.24 + 0.08 * u, seam=lid_pts(BRB_CAM0, TEAR_SEAM), seed=5, lit=look.PEACH)
    waves = bar_waves(170.765, 178.3, -1600.0, speed=900.0, strength=0.5, d=1, every=4)
    w = World(t, cam, {"lid": 0.55, "overcast": 0.3, "sunset": 0.15}, lit=lit_at(t), lid=lid, sway=0.55,
              gust=0.18, wind_dir=1.0, crows=_crows(t, cam), behind_lid=_tear_glow(cam, t, 1.0), waves=tuple(waves),
              flow=2.0, fringe=0.45, lid_ref=BRB_CAM0, lid_dy=-120.0 * drain, lid_dx=_stream(t))
    tilt = ease(170.8, 172.6, t)
    eye = "closed" if t > 171.6 else "half"
    offer = ease(171.2, 172.2, t, out_back)
    with look.graded(ctx, sat, cool):
        paint(ctx, w)
        figure(ctx, cam, "child", 0.0, CHILD_H, F.stand(0.5 - 0.2 * tilt), -1, head_tilt=0.9 * tilt, eye=eye,
               wind=0.3, wind_dir=1, mood=-0.1 + 0.2 * tilt, rim=0.4)
    green_patches(ctx, cam, t)
    _low_sun(ctx, -120, 600, 900, 0.20 + 0.12 * u)
    figure(ctx, cam, "friend", -125.0, FRIEND_H, F.blend(F.stand(0.2), F.hand_out(), offer), 1, eye="open",
           head_tilt=0.15 * min(1.0, offer), wind=0.3, wind_dir=1, rim=0.5)
    look.rain(ctx, (0, 0, W, H), amount=0.15 + 0.65 * ease(170.8, 175.5, t, lambda v: v * v * (3 - 2 * v)),
              slant=-0.14, seed=2, lit_side="left", lit_reach=0.55)
    ctx.post.exposure = 0.95 + 0.04 * u
    ctx.post.vignette = 1.1


# ---------------------------------------------------------------------------------------------
# br_c: the hands. A slow push-in; the rain slows as if time held; a soft amber bloom at contact
# ---------------------------------------------------------------------------------------------
T_TAKE = TL.beat_time(240)              # 180.27


def _rain_time(t):
    """The rain's own clock: it slows to a quarter around the contact (numerically integrated)."""
    a = 179.4
    if t <= a:
        return t
    ts = np.linspace(a, t, 40)
    rate = 1.0 - 0.75 * np.array([ss(179.4, 180.3, v) for v in ts])
    return a + float(np.trapezoid(rate, ts))


def br_c(ctx):
    t = ctx.t
    u = ss(178.265, 182.3, t)
    cam = S.Cam(-2.0, 642.0 + 6 * u, 4.20 * (4.6 / 4.2) ** u)
    sat, cool = grade_at(t)
    lid = dict(rect=lid_rect(BRC_CAM0, BRC_CAM0, 150.0, widen=700.0), density=0.5, heavy=0.4, churn=0.8,
               tear=0.2, seam=lid_pts(BRC_CAM0, TEAR_SEAM), seed=5, lit=look.PEACH)
    w = World(t, cam, {"overcast": 0.55, "lid": 0.25, "sunset": 0.2}, lit=lit_at(t), lid=lid, sway=0.3,
              crows=None, behind_lid=_tear_glow(cam, t, 1.0), flow=0.8, lid_ref=BRC_CAM0, lid_dx=_stream(t))
    xf, xc = -46.0, 44.0
    zc = cam.zd(1.0)
    hf, hc = FRIEND_H * zc, CHILD_H * zc
    fx, fy = cam.pt(xf, S.CREST_Y, 1.0)
    cx, cy = cam.pt(xc, S.CREST_Y, 1.0)
    c0 = TL.cue(50).t
    offer = ease(c0 - 0.05, c0 + 0.6, t)
    took = ease(T_TAKE - 0.25, T_TAKE + 0.08, t)
    grip = ease(T_TAKE, T_TAKE + 0.35, t)
    exhale = ss(T_TAKE + 0.3, T_TAKE + 1.4, t)
    fpose = F.blend(F.stand(0.2), F.reach(F.hand_out(), (0.25, 0.45), side="n", who="friend"), offer)
    fpose = replace(fpose, hand_n=fpose.hand_n * (1 - 0.6 * grip))
    with look.graded(ctx, sat, cool):
        paint(ctx, w)
        veil = prims.linear_paint((0, 0), (0, H), [look.FOG_PALE, look.FOG_PALE, look.FOG_LIGHT], (0, 0.5, 1),
                                  alphas=[0.0, 0.16, 0.30])
        ctx.canvas.drawRect(skia.Rect.MakeWH(W, H), veil)
    _low_sun(ctx, -200, 420, 1300, 0.22)
    look.rain(ctx, (0, 0, W, H), amount=0.22 * (1 - ss(180.6, 181.9, t)), slant=-0.14, seed=2, lit_side="left",
              lit_reach=0.5, t=_rain_time(t))
    fa = fig(ctx.canvas, "friend", fx, fy, hf, fpose, 1, eye="open", smile=0.25 + 0.2 * took, t=t, shadow=0.0,
             wind=0.15, wind_dir=1, rim=0.6, mood=0.4)
    hx, hy = fa["hand_n"]
    tgt = ((cx - hx) / hc - 0.035, (cy - hy) / hc + 0.01)
    full = F.reach(F.take_hand(0.25 - 0.12 * exhale), tgt, side="n", elbow=-1)
    hes = 0.38 * ss(178.85, 179.3, t) * (1 - ss(179.45, 179.95, t)) + 0.12 * ss(179.95, 180.05, t)
    pose = F.blend(F.stand(0.5 - 0.2 * exhale), full, max(hes, took))
    pose = replace(pose, hand_n=0.3 + 0.2 * (1 - took))
    with look.graded(ctx, sat, cool, bounds=(cx - hc * 0.6, cy - hc * 1.1, cx + hc * 0.6, H)):
        fig(ctx.canvas, "child", cx, cy, hc, pose, -1, eye="half", head_tilt=0.0, t=t, shadow=0.0, wind=0.12,
            wind_dir=1, mood=-0.2 + 0.5 * exhale, rim=0.4)
    # the contact: a soft amber bloom from the joined hands, a few motes rising
    if t >= T_TAKE:
        s = t - T_TAKE
        # a soft halo around and behind the clasped hands: hollow in the middle on the canvas so the
        # fingers stay readable, the energy on the glow
        r = 300.0 * out_cubic(s / 1.2)
        a = min(1.0, s / 0.12) * (1 - 0.35 * ss(1.2, 3.5, s))
        if r > 8:
            p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kScreen)
            p.setShader(skia.GradientShader.MakeRadial((hx, hy), r, [P.sk(look.AMBER, 0), P.sk(look.AMBER, 0.05 * a),
                                                                    P.sk(look.AMBER, 0)], [0.0, 0.45, 1.0]))
            ctx.canvas.drawCircle(hx, hy, r, p)
        prims.glow(ctx.glow, hx, hy, max(r, 4.0), look.AMBER, 0.20 * a)
        ids = np.arange(7)
        age = s - 0.25 * ids
        on = age > 0
        if on.any():
            mx = hx + 40 * HS(ids, 220) + 18 * np.sin(age * 1.7 + ids)
            my = hy - 70 * age - 10 * H01(ids, 221)
            al = np.clip(age / 0.4, 0, 1) * np.clip(1 - age / 3.2, 0, 1)
            lights.motes(ctx, mx[on], my[on], size=1.2, alphas=al[on])
    ctx.post.exposure = 1.0
    ctx.post.bloom = 1.2 + 0.25 * ss(T_TAKE, T_TAKE + 1.2, t)
    ctx.post.vignette = 1.2
