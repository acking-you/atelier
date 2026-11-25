"""Painting the hill world for one frame, and the schedules shared by every hill section
(the light, the grade, the walk, the friend's fight with the haze)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np

from mv.engine import palette as P
from mv.engine import prims

from hx.kit import birds, cloud, figures as F, look
from hx.timeline import get_timeline, smoothstep

from . import _hill_set as S

TL = get_timeline()
H01, HS = prims.hash01, prims.hash_sym
CHILD_H, FRIEND_H = 140.0, 146.0


def ss(a, b, x):
    return smoothstep(a, b, x)


def clamp01(x):
    return min(1.0, max(0.0, x))


def out_cubic(u):
    u = clamp01(u)
    return 1 - (1 - u) ** 3


def out_back(u, k=1.6):
    """Ease-out with a little overshoot (about 10 % at k = 1.6), settling at 1."""
    u = clamp01(u)
    v = u - 1
    return 1 + (k + 1) * v ** 3 + k * v ** 2


def ease(t0, t1, t, fn=out_cubic):
    return fn(clamp01((t - t0) / (t1 - t0)))


def kick_breath(ctx, amount=1.0):
    """A camera breath on the kicks (zoom factor) for loud sections."""
    return 1.0 + 0.007 * amount * ctx.kick


def bar_waves(t0, t1, x0, speed=900.0, strength=0.8, d=1, every=4):
    """A gust wave on each bar downbeat between t0 and t1, rolling from world x0 in direction d."""
    out = []
    k = 0
    for bt in TL.beats_between(t0 - 6.0, t1):
        kk = int(round((bt - TL.beat_time(0)) / TL.beat_s))
        if kk % every == 0:
            out.append((float(bt), x0, speed, strength * (0.8 + 0.4 * H01(kk, 440)), d))
        k += 1
    return out


# ---------------------------------------------------------------------------------------------
# the climb: grade saturation, coolness and light level by time (gradual; colour only at 217.84)
# ---------------------------------------------------------------------------------------------
T_RING = TL.cue(62).t            # 217.84


def grade_at(t):
    """(sat, cool) of the world's grade outside the colour ring."""
    keys = [(158.0, 0.13, 0.95), (170.8, 0.15, 0.85), (176.0, 0.22, 0.70), (182.3, 0.24, 0.65),
            (182.31, 0.12, 0.85), (193.0, 0.13, 0.80), (201.25, 0.16, 0.70), (205.0, 0.36, 0.35),
            (213.0, 0.44, 0.25), (T_RING, 0.46, 0.22)]
    ts = [k[0] for k in keys]
    return float(np.interp(t, ts, [k[1] for k in keys])), float(np.interp(t, ts, [k[2] for k in keys]))


def lit_at(t):
    keys = [(158.0, 0.30), (170.8, 0.34), (178.0, 0.48), (182.3, 0.50), (182.31, 0.28), (193.0, 0.30),
            (201.25, 0.34), (204.5, 0.85), (213.0, 0.95), (220.0, 1.0)]
    return float(np.interp(t, [k[0] for k in keys], [k[1] for k in keys]))


# ---------------------------------------------------------------------------------------------
# walking: phase-locked to the beat (one step per beat), stride easing; x integrated from it
# ---------------------------------------------------------------------------------------------
BEAT = TL.beat_s
T_WALK0 = TL.beat_time(270)       # 202.76: the two start walking
T_WALK1 = TL.beat_time(284)       # 213.26: they stop (seven full cycles)
T_OUT0 = TL.section("out").t0
T_OUT_STOP = 243.5


def stride_at(t):
    """Stride (in h) of the walk/run, 0 while standing."""
    if T_WALK0 <= t < T_WALK1:
        return 0.40 + 0.15 * ss(T_WALK0, 207.5, t)
    if T_OUT0 <= t < T_OUT_STOP:
        return 0.55 + 0.45 * run_at(t)
    return 0.0


def run_at(t):
    """Bursts of running in the outro: two bars out of the eight, eased in and out."""
    w = 0.0
    for b0 in (232.77, 238.77):
        w = max(w, ss(b0 - 0.4, b0 + 0.3, t) * (1 - ss(b0 + 2.4, b0 + 3.0, t)))
    return w


_TAB = None


def _table():
    global _TAB
    if _TAB is None:
        ts = np.arange(150.0, 250.0, 1 / 240)
        v = np.array([stride_at(float(t)) for t in ts]) * CHILD_H / (2 * BEAT)
        # runs cover ground faster: a run cycle is still one stride per two beats, stride bigger
        x = np.concatenate([[0.0], np.cumsum(v[:-1]) / 240])
        _TAB = (ts, x)
    return _TAB


def walk_x(t):
    """World x travelled by the child since the walk began (0 before T_WALK0)."""
    ts, x = _table()
    return float(np.interp(t, ts, x))


def walk_phase(t):
    """Walk/run cycle phase 0..1 (two steps per cycle, one step per beat)."""
    if T_WALK0 <= t < T_WALK1:
        return ((t - T_WALK0) / (2 * BEAT)) % 1.0
    if T_OUT0 <= t < T_OUT_STOP:
        return ((t - T_OUT0) / (2 * BEAT)) % 1.0
    return 0.0


# ---------------------------------------------------------------------------------------------
# the breakdown: one hole per measured attack, the friend under each, the child stepping in
# ---------------------------------------------------------------------------------------------
BD_CAM = S.Cam(0.0, 520.0, 0.80)
ONSETS = [(float(a), float(b)) for a, b in TL.onsets_between(184.0, 192.2, 0.4)]
CHILD_BD_X = 430.0                 # where the child watches from (world)
T_STEP = max(ONSETS, key=lambda o: o[1])[0]      # the strongest attack (191.90)


HOLE_SLANT = 0.30                  # the sun is up-left behind the haze: a hole sits up-left of its foot
BD_UNDER = 448.0                   # the haze's underside on screen in the wide shot


def _hole_screen(i, sx):
    fy = float(S.ground_y(sx)) + 4.0
    hx, hy = BD_CAM.pt(sx, fy, 1.0)
    yy = BD_UNDER - 40.0 - 120.0 * H01(i, 310)
    return hx - HOLE_SLANT * (hy - yy), yy


def _spots():
    """Where the friend stands for each attack: a wandering path (short hops between close attacks),
    nudged so that no two holes merge; the strongest last one opens just beside the child."""
    xs, placed = [], []
    x, tp = -240.0, 182.6
    last = len(ONSETS) - 1
    for i, (ti, st) in enumerate(ONSETS):
        r = 40.0 + 52.0 * st
        if i == last:
            nx = CHILD_BD_X - 85.0
        else:
            want = -600.0 + 900.0 * H01(i, 300)
            reach = 70.0 + 340.0 * max(0.0, ti - tp - 0.1)
            nx = x + max(-reach, min(reach, want - x))
            for off in [0.0] + [s * k * 45.0 for k in range(1, 9) for s in (1, -1)]:
                cand = min(330.0, max(-640.0, nx + off))
                hx, hy = _hole_screen(i, cand)
                if all(math.hypot(hx - px, hy - py) > 1.25 * (r + pr) for px, py, pr in placed):
                    nx = cand
                    break
        xs.append(nx)
        placed.append((*_hole_screen(i, nx), r))
        x, tp = nx, ti
    return xs


SPOTS = _spots()


def jump_height(s):
    """A leap that peaks ON the attack (s = 0): quick rise, slower fall, 0 outside."""
    if -0.15 < s < 0.0:
        return 1.0 - (s / 0.15) ** 2
    if 0.0 <= s < 0.22:
        return 1.0 - (s / 0.22) ** 2
    return 0.0


def jump_squat(s):
    """The crouch before the leap and the give of the landing."""
    return math.exp(-((s + 0.22) / 0.06) ** 2) + 0.7 * math.exp(-((s - 0.27) / 0.06) ** 2)


def friend_bd(t):
    """(x, push weight, hop, moving speed sign) of the friend in bd/hush2."""
    x = -240.0
    tp = 182.6
    mv = 0.0
    for (ti, _), sx in zip(ONSETS, SPOTS):
        a, b = tp + 0.12, ti - 0.10
        if b <= a:
            a, b = tp, ti
        w = ss(a, b, t)
        if a < t < b:
            mv = math.copysign(1.0, sx - x) if abs(sx - x) > 1 else 0.0
        x = x + (sx - x) * w
        tp = ti
    # after the last attack the friend eases half a step aside to share the shaft with the child
    x += -28.0 * ss(T_STEP + 0.2, T_STEP + 1.2, t)
    push = 0.0
    hop = 0.0
    for ti, st in ONSETS:
        push = max(push, ss(ti - 0.42, ti - 0.12, t) * (1 - ss(ti + 0.35, ti + 0.75, t)))
        hop = max(hop, jump_height(t - ti) * (0.6 + 0.4 * st))
    if t > T_STEP + 0.5:
        push = push * (1 - ss(T_STEP + 0.5, T_STEP + 1.6, t))
    return x, push, hop, mv


def holes_bd(t, cam: S.Cam):
    """Holes in screen space for cloud.draw, plus their shafts (hole xy, foot xy, size, amount)."""
    out = []
    widen = 1.0 + 0.16 * ss(193.0, 200.6, t) + 0.25 * ss(201.0, 204.0, t)
    zl = cam.zd(S.D_LID)
    for i, ((ti, st), sx) in enumerate(zip(ONSETS, SPOTS)):
        if t < ti:
            continue
        amt = min(1.0, out_back((t - ti) / 0.22, 2.2)) * (0.62 + 0.38 * st)
        foot_y = float(S.ground_y(sx)) + 4.0
        fx, fy = cam.pt(sx, foot_y, 1.0)
        wx, wy = BD_CAM.inv(*_hole_screen(i, sx), S.D_LID)
        hx, hy = cam.pt(wx, wy, S.D_LID)
        r = (40.0 + 52.0 * st) * widen * zl
        out.append(dict(hole=(hx, hy, r, amt), foot=(fx, fy), size=st, amt=amt, i=i, wx=sx))
    return out


# ---------------------------------------------------------------------------------------------
# one frame of the world (everything inside the grade); figures and light are the caller's
# ---------------------------------------------------------------------------------------------
@dataclass
class World:
    t: float
    cam: S.Cam
    sky: dict
    lit: float = 0.3
    gold: float = 0.0
    lid: dict | None = None            # cloud.draw kwargs in screen space (rect, density, holes, ...)
    fog: float = 1.0
    sway: float = 0.5
    gust: float = 0.0
    wind_dir: float = 1.0
    flowers: object = None             # open_fn(cluster_ids, xs, ys)
    roofs: float = 0.0                 # 1 = the far roofs in full colour
    whites: list = field(default_factory=list)   # (x, y, w, seed) white clouds in screen space
    crows: dict | None = None          # draw_flock kwargs
    near_extra: object = None          # fn(canvas) drawn after the tufts
    behind_lid: object = None          # fn(canvas) drawn on the sky before the lid (light behind tears)
    waves: tuple = ()                  # gust waves through the grass (see _hill_set.wave_rot)
    bow: tuple | None = None           # grass bowing at a ring's edge (screen cx, cy, radius, width, strength)
    flow: float = 1.0                  # speed of the fog sea
    lid_alpha: float = 1.0
    lid_ref: object = None             # the camera the lid is laid out for (its kwargs are in that screen)
    lid_dy: float = 0.0                # extra lift of the lid (screen px)
    lid_dx: float = 0.0                # the lid streaming sideways (lid-layer px), as a translation
    white_alpha: float = 1.0
    fringe: float = 0.0                # foreground grass along the bottom edge (its brightness; 0 = none)
    after_lid: object = None           # fn(canvas) drawn after the lid (birds in the sky)


def lid_rect(ref: S.Cam, cam: S.Cam, under: float, hgt: float = 1600.0, dx: float = 0.0, widen: float = 0.0):
    """A whole-sky lid fixed in the lid layer: laid out on screen for the reference camera `ref`
    (underside at screen y `under`, crowns well above the frame), seen through `cam`."""
    top = under - 0.8 * hgt
    l, t_ = ref.inv(-320.0 - widen, top, S.D_LID)
    r, b = ref.inv(2240.0 + widen, top + hgt, S.D_LID)
    l, r = l + dx, r + dx
    return (*cam.pt(l, t_, S.D_LID), *cam.pt(r, b, S.D_LID))


def lid_pts(cam: S.Cam, pts):
    return [tuple(float(v) for v in cam.pt(x, y, S.D_LID)) for x, y in pts]


def paint(ctx, w: World):
    c = ctx.canvas
    cam = w.cam
    g = S.tones(w.lit, w.gold)
    look.sky(c, (0, 0, S.W, S.H), w.sky)
    for (x, y, wd, sd) in w.whites:
        white_cloud(c, x, y, wd, sd, w.gold, w.white_alpha)
    S.draw_far(c, cam, g, w.roofs)
    S.draw_fog_sea(c, cam, g, w.t, w.fog, w.flow)
    S.draw_mid(c, cam, g, w.t, w.fog, w.flow)
    if w.behind_lid is not None:
        w.behind_lid(c)
    if w.lid is not None:
        if w.lid_alpha < 0.999:
            c.saveLayerAlpha(None, int(255 * max(0.0, w.lid_alpha)))
        n = c.getSaveCount()
        if w.lid_ref is not None:
            # the lid is laid out once for its reference camera and moved as a whole: its rect never
            # changes size, so the cloud's lobe count never jumps while the camera moves
            ref = w.lid_ref
            ox, oy = cam.pt(*ref.inv(0.0, 0.0, S.D_LID), S.D_LID)
            sc = cam.zd(S.D_LID) / ref.zd(S.D_LID)
            c.save()
            c.translate(ox, oy + w.lid_dy)
            c.scale(sc, sc)
            c.translate(w.lid_dx * ref.zd(S.D_LID), 0.0)
        _haze_foot(c, w.lid)
        cloud.draw(ctx, **w.lid)
        c.restoreToCount(n)
        if w.lid_alpha < 0.999:
            c.restore()
    if w.crows is not None:
        birds.draw_flock(c, **w.crows)
    if w.after_lid is not None:
        w.after_lid(c)
    S.draw_near(c, cam, g)
    light = P.mix((1, 1, 1), (1.0, 0.86, 0.66), w.gold)
    dim = 0.34 + 0.66 * w.lit ** 1.2
    light = tuple(v * dim for v in light)
    S.draw_tufts(c, cam, w.t, w.sway, light, w.gust, w.wind_dir, w.waves, w.bow)
    if w.flowers is not None:
        S.draw_flowers(c, cam, w.t, w.flowers, light, w.sway)
    if w.near_extra is not None:
        w.near_extra(c)
    if w.fringe > 0:
        S.draw_fringe(c, cam, w.t, light, w.sway, w.waves, w.fringe)


def _haze_foot(c, lid):
    """A soft hanging veil below the lid's underside so its lower edge never reads as a ruled line."""
    l, tp, r, b = lid["rect"]
    und = tp + 0.8 * (b - tp)
    if und < -50 or und > S.H:
        return
    dens = float(lid.get("density", 1.0)) * (1.0 - min(1.0, float(lid.get("tear", 0.0)) * 1.4)) ** 2
    col = cloud.GLOOM[3]
    sp = 0.07 * (b - tp)
    p = prims.linear_paint((0, und - sp), (0, und + 2.2 * sp), [col, col, col], (0, 0.3, 1),
                           alphas=[0.0, 0.55 * dens, 0.0])
    import skia
    c.drawRect(skia.Rect.MakeLTRB(-S.W, und - sp, 2 * S.W, und + 2.2 * sp), p)


def white_cloud(c, x, y, w, seed, gold=0.0, alpha=1.0):
    """A soft fair-weather cloud: overlapping soft discs, a dome over a flatter, faintly shaded base."""
    n = 11
    ids = np.arange(n) + seed * 53
    u = (np.arange(n) + 0.5) / n - 0.5 + 0.03 * HS(ids, 430)
    dome = np.sqrt(np.maximum(0.05, 1 - (2 * u) ** 2))
    r = w * (0.10 + 0.10 * H01(ids, 431)) * (0.5 + 0.7 * dome)
    xs = x + u * w * 0.95
    ys = y - dome * w * 0.12 - r * 0.2 + w * 0.02 * HS(ids, 432)
    disc = prims.soft_disc(64, 0.55)
    base = P.mix(look.hex_rgb("C9D2DE"), look.PERSIMMON, 0.25 * gold)
    top = P.mix(look.hex_rgb("FFFDF7"), look.PEACH, 0.35 * gold)
    if alpha <= 0.01:
        return
    prims.draw_sprites(c, disc, xs, ys + r * 0.30, r / 26.0, base, alpha=0.9 * alpha)
    prims.draw_sprites(c, disc, xs, ys - r * 0.06, r / 29.0, top, alpha=alpha)


WHITE = (look.hex_rgb("FFFDF8"), look.hex_rgb("F6F1E8"), look.hex_rgb("E6E3E0"), look.hex_rgb("CFD3DA"))


def walk_arm(base, arm_src):
    """A walk/run pose with the near arm taken from another pose (string or kite line held up)."""
    return replace(base, arm_n=arm_src.arm_n, fore_n=arm_src.fore_n, hand_n=arm_src.hand_n)


import inspect as _inspect

_FIG_ARGS = set(_inspect.signature(F.draw).parameters)


def fig(canvas, who, x, y, h, pose, facing, **kw):
    """figures.draw, passing the newer arguments (mood, rim) only when the kit has them."""
    kw = {k: v for k, v in kw.items() if k in _FIG_ARGS}
    return F.draw(canvas, who, x, y, h, pose, facing, **kw)


def figure(ctx, cam, who, wx, h_world, pose, facing, **kw):
    """Draw a figure standing at world x on the ground; returns its anchors."""
    x, y = cam.pt(wx, S.ground_y(wx), 1.0)
    dy = kw.pop("dy", 0.0)
    return fig(ctx.canvas, who, x, y + dy * cam.zd(1.0), h_world * cam.zd(1.0), pose, facing, t=ctx.t, **kw)
