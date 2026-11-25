"""Fog world: the hush before the first chorus, and both choruses on the wide fog plain.

hush1  near-dark: the faint rim of the child, the cloud settling over it.
c1a    the plain; the tiny child walks away to the right and thins bar by bar; wind on the beat;
       the three kinds of looming shapes come out of the fog on k = 86, 88, 90; crows wheel.
c1b    the child stops; a ribbon of amber motes crosses from the far lit doorway (the friend stands
       there, small); the child turns solid, looks back, one mote rests in the open hand; the
       shapes sink back; calm from the band's drop.
c2a    out of a pale white-out: storm, lower cloud, hard wind, the shapes bigger and closer on
       k = 192, 194, 196; the child leans into the wind holding the scraps, thinning less.
c2b    the friend steps in from the left and stands beside the child in a warm pocket of clearer
       air; both look up and the view tilts up to a first thin slit in the cloud.
Lines are addressed by LRC index (see hx/DESIGN.md)."""
from __future__ import annotations

import math

import numpy as np
import skia

from mv.engine import palette as P, prims

from hx.kit import birds, cloud, figures, lights, look, scraps
from hx.kit.figures import blend
from hx.timeline import smoothstep

from . import _fog_loom as loom
from . import _fog_plain as plain

SECTIONS = ("hush1", "c1a", "c1b", "c2a", "c2b")
CROSSFADE = {"c2a": 0.5}

W, H = 1920, 1080
HZ = plain.HZ
WIND_ANGLE = 184.0                                  # streaks travel left, a touch upward


def _ss(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _band(c, rect, t, density, color, speed, seed, alpha, size):
    look.fog_band(c, rect, t, density, color, speed, seed, alpha, size)


def _with(p, **kw):
    d = {f: getattr(p, f) for f in p.__dataclass_fields__}
    d.update(kw)
    return type(p)(**d)


def draw(ctx):
    sid = ctx.sec.id
    if sid == "hush1":
        _hush(ctx)
    elif sid in ("c1a", "c1b"):
        _chorus1(ctx)
    else:
        _chorus2(ctx)


# =========================================================================== hush1
def _hush(ctx):
    t, c = ctx.t, ctx.canvas
    t0, t1 = ctx.sec.t0, ctx.sec.t1
    k = _ss((t - t0) / (t1 - t0))
    with look.graded(ctx):
        prims.fill_rect_gradient(c, (0, 0, W, H), [look.INK, P.mix(look.INK, look.FOG_DEEP, 0.55),
                                                   P.mix(look.INK, look.FOG_DEEP, 0.75), look.INK],
                                 [0.0, 0.52, 0.66, 1.0])
        settle = -150.0 * (1.0 - k) ** 1.5           # the cloud comes down and settles, no rhythm
        cloud.draw(ctx, (-180, -440 + settle, 2100, 440 + settle), t=t, heavy=0.8, churn=0.5, seed=2,
                   density=0.9)
        x, y, h = 1010.0, 858.0, 250.0
        pose = figures.stand(0.9)
        # the faint rim: a pale, softened ghost of the figure set just behind it
        rim = skia.Paint()
        rim.setColorFilter(skia.ColorFilters.Blend(P.sk(look.FOG_LIGHT, 1.0), skia.BlendMode.kSrcIn))
        rim.setImageFilter(skia.ImageFilters.Blur(2.5, 2.5))
        rim.setAlphaf(0.55 + 0.25 * k)
        c.saveLayer(skia.Rect.MakeLTRB(x - h * 0.6, y - h * 1.15, x + h * 0.6, y + 20), rim)
        c.translate(4.0, -3.0)
        figures.draw(c, "child", x, y, h, pose, facing=1, t=t, shadow=0.0, eye="closed")
        c.restore()
        figures.draw(c, "child", x, y, h, pose, facing=1, t=t, shadow=0.0, eye="closed")
    ctx.post.fade = 0.90 - 0.14 * _ss((t - t0) / 2.2)
    ctx.post.fade_color = look.INK


# =========================================================================== shared machinery
import inspect

_FIG_KW = set(inspect.signature(figures.draw).parameters)
C0 = (W / 2.0, H / 2.0)
# parallax weights of the layers (1 = the ground the child stands on)
P_SKY, P_LID, P_FAR, P_LOOM, P_GROUND, P_NEAR, P_CROWS = 0.32, 0.45, 0.6, 0.9, 1.0, 1.2, 0.55


def _fig(c, who, x, y, h, pose, mood=None, **kw):
    if mood is not None and "mood" in _FIG_KW:
        kw["mood"] = mood
    return figures.draw(c, who, x, y, h, pose, **kw)


def _ease_io(u):
    u = min(1.0, max(0.0, u))
    return 0.5 - 0.5 * math.cos(math.pi * u)


def _ss_v(a, b, x):
    u = np.clip((x - a) / (b - a), 0.0, 1.0)
    return u * u * (3 - 2 * u)


def _curve_v(tl, name, ts):
    v = tl._curves[name]
    return np.interp(np.maximum(ts, 0.0) * tl._hz, np.arange(len(v)), v)


def _integ(tl, t0, t, f, surge=0.0, rate=40.0):
    """Integral over [t0, t] of f(ts) * (1 + surge * kick): a clock that runs at the weather's
    speed (on a fixed absolute grid, so it is smooth from frame to frame)."""
    if t <= t0:
        return t - t0
    g = np.arange(math.ceil(t0 * rate), math.floor(t * rate) + 1) / rate
    ts = np.unique(np.concatenate([[t0], g, [t]]))
    v = f(ts)
    if surge:
        v = v * (1.0 + surge * _curve_v(tl, "kick", ts))
    return float(((v[1:] + v[:-1]) * 0.5 * np.diff(ts)).sum())


def _noise(t, seed):
    return 2.0 * (float(prims.value_noise(np.array([t]), seed)[0]) - 0.5)


def _burst(a, attack=10.0, tau=0.8):
    return 0.0 if a <= 0 else (1.0 - math.exp(-a * attack)) * math.exp(-a / tau)


class Cam:
    """World point F shown at the frame centre with zoom z (for the ground layer); a layer of
    parallax weight p sees zoom 1 + (z - 1) p and focus C0 + (F - C0) p; dy tilts everything."""

    def __init__(self, z, fx, fy, dy=0.0):
        self.z, self.f, self.dy = z, (fx, fy), dy

    def _zp(self, p):
        return 1.0 + (self.z - 1.0) * p, C0[0] + (self.f[0] - C0[0]) * p, C0[1] + (self.f[1] - C0[1]) * p

    def push(self, c, p):
        zp, fx, fy = self._zp(p)
        c.save()
        c.translate(C0[0], C0[1] + self.dy)
        c.scale(zp, zp)
        c.translate(-fx, -fy)

    def map(self, p, x, y):
        zp, fx, fy = self._zp(p)
        return C0[0] + zp * (x - fx), C0[1] + self.dy + zp * (y - fy)

    def unmap(self, p, sx, sy):
        zp, fx, fy = self._zp(p)
        return fx + (sx - C0[0]) / zp, fy + (sy - C0[1] - self.dy) / zp

    def zoom(self, p=1.0):
        return self._zp(p)[0]


def _blend_cam(a, b, m):
    za, zb = math.log(a[0]), math.log(b[0])
    return (math.exp(za + (zb - za) * m), a[1] + (b[1] - a[1]) * m, a[2] + (b[2] - a[2]) * m)


def _gusts(c, ctx, wf, y0, y1, seed, alpha=0.10):
    """Gust waves running leftward through the grass: soft pale swells launched on even beats."""
    tl = ctx.tl
    k0 = ctx.beat
    for k in (k0, k0 - 1, k0 - 2, k0 - 3, k0 - 4, k0 - 5):
        a = ctx.t - tl.beat_time(k)
        if a < 0 or a > 4.5:
            continue
        x = 2200.0 - 620.0 * a
        y = y0 + (y1 - y0) * float(prims.hash01(k, seed))
        env = math.sin(math.pi * min(1.0, a / 4.5))
        c.save()
        c.translate(x, y)
        c.scale(1.0, 0.10)
        prims.glow(c, 0, 0, 520, look.FOG_LIGHT, alpha * wf * env, 1.6)
        c.restore()


def _fog_layer(c, cam, p, rect, clock, color, speed, seed, alpha, size, hole=None):
    """A fog sheet on parallax layer p, streaming with `clock`; hole = (sx, sy, r) clears it softly."""
    cam.push(c, p)
    if hole is None:
        _band(c, rect, clock, 1.0, color, speed, seed, alpha, size)
    else:
        l, tp, r, b = rect
        c.saveLayer(skia.Rect.MakeLTRB(l, tp, r, b), None)
        _band(c, rect, clock, 1.0, color, speed, seed, alpha, size)
        hx, hy = cam.unmap(p, hole[0], hole[1])
        rr = hole[2] / cam.zoom(p)
        ex = prims.radial_paint((hx, hy), rr, (0, 0, 0), hole[3], power=1.2, inner=0.25)
        ex.setBlendMode(skia.BlendMode.kDstOut)
        c.drawCircle(hx, hy, rr, ex)
        c.restore()
    c.restore()


def _lid_stream(c, cam, clock, w, k, y0, col):
    """Dark rags streaming under the lid's belly."""
    if w < 0.03:
        return
    cam.push(c, P_LID + 0.05)
    plain.sheet(c, (-300, y0 - 170, W + 300, y0 + 110), clock, 260.0 * k, col, 0.36 * w, 5, 1.6)
    c.restore()


def _sheets(c, cam, clock, w, k, dark=1.0):
    """Fog sheets streaming across the plain at three depths (faster when nearer)."""
    for p, rect, sp, col, al, sd in ((0.62, (-300, 420, W + 300, 680), 200.0, look.FOG_LIGHT, 0.30, 1),
                                     (0.9, (-300, 560, W + 300, 830), 420.0, look.FOG_LIGHT, 0.40, 2),
                                     (0.95, (-300, 560, W + 300, 800), 300.0, P.mix(look.FOG, look.FOG_DEEP, 0.4), 0.26, 4),
                                     (1.1, (-300, 680, W + 300, 900), 700.0, look.FOG_PALE, 0.30, 3)):
        cam.push(c, p)
        if sd == 4:
            al *= dark
        if al < 0.01:
            c.restore()
            continue
        plain.sheet(c, rect, clock, sp * k, col, al * (0.6 + 0.4 * w), sd, 1.0 + 0.15 * sd)
        c.restore()


# =========================================================================== chorus 1
C1_ARC0 = plain.arc_at_x(980.0)
STRIDE = 0.40


def _child1(ctx):
    """World position, size, pose, facing and dissolve of the child in c1a / c1b."""
    tl, t = ctx.tl, ctx.t
    tw0 = tl.beat_time(78)
    t_stop = tl.section("c1b").t0
    cyc = 4 * tl.beat_s                              # one step per two beats
    ph = (min(t, t_stop) - tw0) / cyc
    h0 = 100.0
    x, y = plain.path_at(C1_ARC0 + ph * STRIDE * h0)
    h = h0 * (0.6 + 0.4 * (y - 640.0) / 100.0)
    pose = figures.walk(ph % 1.0, slump=0.92, stride=STRIDE)
    stop = _ss((t - t_stop) / 0.8)
    if stop > 0:
        pose = blend(pose, figures.stand(0.88), stop)
    # continuous thinning from the downbeat; back to solid when the ribbon lands
    t1 = tl.beat_time(80)
    u = min(1.0, max(0.0, (t - t1) / 9.6))
    thin = 1.0 - (1.0 - u) ** 1.8
    t_land = tl.beat_time(96) + 1.6
    solid = _ss((t - (t_land - 0.3)) / 1.6)
    dis = thin * (1.0 - solid)
    alpha = 1.0 - 0.1 * dis
    # the turn to look back: head lifts first, then the body comes round through three-quarter
    k = _ss((t - (t_land + 0.25)) / 0.9)
    facing, head_tilt = 1, 0.18 * _ss((t - t_land) / 0.5)
    if k > 0:
        if k < 0.5:
            pose = _with(pose, turn=0.6 * _ss(k * 2))
        else:
            facing = -1
            pose = _with(pose, turn=0.6 - 0.32 * _ss((k - 0.5) * 2))
    hand = ctx.line_ramp(25, 0.0, 1.1)
    eye = "half"
    if hand > 0:
        tgt = figures.reach(pose, ("head", 1.9, -2.7))
        pose = blend(pose, _with(tgt, hand_n=1.0, nod=0.42), hand)
        head_tilt *= 1.0 - hand
        eye = "open"
    return x, y, h, pose, facing, dis, alpha, head_tilt, eye


def _cam1(ctx, x, y, h):
    tl, t = ctx.tl, ctx.t
    t1 = tl.beat_time(80)
    zc = 3.7 + 0.15 * _ss((t - 58.6) / 1.7)
    tgt = (1060.0, 846.0)                           # the child's feet in the close shot
    close = (zc, x - (tgt[0] - C0[0]) / zc, y - (tgt[1] - C0[1]) / zc)
    zw = 1.12 + 0.30 * _ease_io((t - t1 - 0.5) / 14.5)
    wide = (zw, 880.0 + 170.0 * _ease_io((t - t1 - 0.3) / 12.0) + 0.35 * (x - 1000.0) + 10.0 * _noise(t * 0.15, 3), 522.0 - 8.0 * _ss((t - t1) / 10.0))
    m = loom.back_out((t - t1) / 0.8, 0.9) if t > t1 else 0.0
    cam = _blend_cam(close, wide, m)
    # line 25: a gentle push-in to a medium shot of the open hand and the face
    q = _ease_io((t - tl.cue(25).t) / 3.0)
    if q > 0:
        zp = 260.0 / h
        tg = (960.0, 790.0)
        cam = _blend_cam(cam, (zp, x - (tg[0] - C0[0]) / zp, y - (tg[1] - C0[1]) / zp), q)
    return Cam(*cam)


def _wind1(tl):
    t1, t_rib = tl.beat_time(80), tl.beat_time(96)

    def f(ts):
        w = 0.35 + 0.65 * _ss_v(t1 - 0.4, t1 + 0.2, ts)
        w = w * (1.0 - 0.72 * _ss_v(t_rib, t_rib + 2.5, ts))
        return w * (1.0 - 0.7 * _ss_v(78.2, 79.6, ts))
    return f


def _chorus1(ctx):
    tl, t, c = ctx.tl, ctx.t, ctx.canvas
    x, y, h, pose, facing, dis, alpha, head_tilt, eye = _child1(ctx)
    cam = _cam1(ctx, x, y, h)
    t_rib = tl.beat_time(96)
    t_land = t_rib + 1.6
    t0 = tl.section("c1a").t0
    wf = _wind1(tl)
    w_now = float(wf(np.array([t]))[0])
    clock = _integ(tl, t0, t, wf, surge=1.4) + t0         # fog and streak clock
    far = _ss((t - (t_rib - 0.8)) / 1.6)
    ents = [tl.beat_time(86 + 2 * i) for i in range(3)]
    sink = _ease_io((t - (tl.cue(25).t - 0.3)) / 3.5)
    crow_t = _integ(tl, t0, t, lambda ts: 0.7 + 0.9 * _ss_v(ents[0], ents[2] + 1.0, ts)
                    - 0.6 * _ss_v(78.0, 80.0, ts)) + t0
    # each entry presses the picture darker for a moment
    ctx.post.exposure *= 1.0 - sum(0.07 * _burst(t - e, 14.0, 0.9) for e in ents)
    with look.graded(ctx):
        cam.push(c, P_SKY)
        plain.sky(c, 0.0, 400.0, lid=(200.0, cloud.GLOOM[2]))
        c.restore()
        cam.push(c, P_FAR)
        plain.draw_planes(c, (0,))
        plain.doorway_house(c, 0.0, far)
        _band(c, (-260, HZ - 120, W + 260, HZ + 50), clock, 1.0, look.FOG_PALE, 50.0, 3, 0.72, 1.2)
        c.restore()
        cam.push(c, P_GROUND)
        plain.draw_planes(c, (1,))
        _gusts(c, ctx, w_now, 700.0, 830.0, 5, 0.16)
        c.restore()
        cam.push(c, P_LOOM)
        loom.draw_kind(c, 1, "c1", t, ents[1], 0.6, 0.0, sink, 1.0, 0.09, bend=7.0, sway_t=clock)
        loom.draw_kind(c, 0, "c1", t, ents[0], 0.55, 0.12, sink, 1.6, 0.09, sway_t=clock)
        c.restore()
        cam.push(c, P_LID)
        cloud.draw(ctx, (-180, -640, 2100, 530), t=t, heavy=0.1, churn=1.0 + 0.8 * w_now, seed=2, density=0.92)
        c.restore()
        _fog_layer(c, cam, P_LID + 0.05, (-260, 200, W + 260, 420), clock, look.FOG, 95.0, 21, 0.45, 1.6)
        _fog_layer(c, cam, 0.95, (-260, 520, W + 260, 770), clock, P.mix(look.FOG, look.FOG_PALE, 0.6), 150.0, 7,
                   0.55 + 0.12 * ctx.kick * w_now, 1.4)
        _lid_stream(c, cam, clock, w_now, 1.3, 270.0, cloud.GLOOM[2])
        _sheets(c, cam, clock, w_now, 1.35)
        cam.push(c, P_GROUND)
        loom.draw_kind(c, 2, "c1", t, ents[2], 0.45, 0.22, sink, 1.0, 0.08, sway_t=clock)
        anc = _fig(c, "child", x, y, h, pose, mood=-0.7 + 0.5 * sink, facing=facing, alpha=alpha, dissolve=dis,
                   eye=eye, head_tilt=head_tilt, wind=0.45 * w_now, wind_dir=-1, t=t, shadow=0.3, seed=7)
        c.restore()
        cam.push(c, P_NEAR)
        plain.draw_planes(c, (2,))
        _gusts(c, ctx, w_now, 900.0, 1040.0, 9, 0.08)
        c.restore()
        _fog_layer(c, cam, P_NEAR, (-260, 860, W + 260, 1100), clock, look.FOG, 210.0, 11, 0.26, 1.8)
        cam.push(c, P_CROWS)
        fl = birds.flock_wheel(11, crow_t, (1150.0, 330.0), 340.0, seed=4, speed=0.9, squash=0.33)
        birds.draw_flock(c, fl["x"], fl["y"], 15.0, fl["phase"], fl["heading"], fl["bank"], fl["scale"],
                         alpha=0.78 - 0.25 * sink)
        c.restore()
        s = (0.30 + 0.70 * ctx.pulse(0.30)) * w_now
        look.wind(c, (0, 80, W, 840), clock, s, WIND_ANGLE, seed=3, n=210, speed=1700, alpha=0.7)
    # outside the grade: the lit doorway and the friend by it, the ribbon, the mote
    cam.push(c, P_FAR)
    plain.doorway_light(ctx, 0.0, far)
    if far > 0.01:
        _fig(c, "friend", plain.DOOR[0] + 24, plain.DOOR[1] + 2, 40.0, figures.stand(0.2), mood=0.3, facing=1,
             alpha=0.85 * far, eye="open", t=t, shadow=0.0)
    c.restore()
    if t <= t_rib:
        return
    sh = cam.map(1.0, *anc["shoulder"])
    hs = h * cam.zoom()
    dx, dy = cam.map(P_FAR, plain.DOOR[0] + 18, HZ - 22)
    path = [(dx, dy), (dx + (sh[0] - dx) * 0.35, dy - 70), (dx + (sh[0] - dx) * 0.72, sh[1] - 1.1 * hs),
            (sh[0] + 0.55 * hs, sh[1] - 0.55 * hs), (sh[0] + 0.62 * hs, sh[1] + 0.05 * hs),
            (sh[0] + 0.2 * hs, sh[1] + 0.12 * hs), sh]
    a = t - t_rib
    head = _ease_io(a / 1.6) if a < 1.6 else 1.0 + (a - 1.6) * 0.5
    if head < 1.6:
        lights.ribbon(ctx, path, 40, head, seed=5, size=0.9, alpha=0.95, trail=0.42, spread=8.0)
        if head < 1.0:                                   # the bright leading head
            pts = np.asarray(path)
            seg = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
            hx = float(np.interp(head * seg[-1], seg, pts[:, 0]))
            hy = float(np.interp(head * seg[-1], seg, pts[:, 1]))
            lights.mote(ctx, hx, hy, size=1.7, alpha=1.0, seed=4)
    # the soft warm pulse where it lands
    b = _burst(t - t_land, 12.0, 0.9)
    if b > 0.01:
        prims.glow(c, sh[0], sh[1], 30 + 0.9 * hs, look.AMBER, 0.2 * b, 1.6)
        prims.glow(ctx.glow, sh[0], sh[1], 30 + 0.9 * hs, look.AMBER, 0.4 * b, 1.6)
    if t >= t_land - 0.05:
        # one mote stays: by the shoulder, then into the open hand with line 25
        mv = ctx.line_ramp(25, -0.2, 1.3)
        hx, hy = cam.map(1.0, *anc["hand_n"])
        wx, wy = lights.wander(9, t, 6.0 * (1 - mv) + 1.5)
        mx = sh[0] + (hx - sh[0]) * mv + wx
        my = sh[1] - 8 + (hy - 6 - sh[1] + 8) * mv + wy
        lights.mote(ctx, mx, my, size=0.75 + 0.35 * mv, alpha=_ss((t - t_land + 0.05) * 4), seed=9)


# =========================================================================== chorus 2
C2_ARC0 = plain.arc_at_x(820.0)
LID2 = 300.0                                          # the lower underside in the storm
H2 = 132.0


def _lid2_rect():
    top = -1150.0
    return (-200.0, top, 2120.0, top + (LID2 - top) / 0.8)


def _child2(ctx):
    tl, t = ctx.tl, ctx.t
    s2a, s2b = tl.section("c2a"), tl.section("c2b")
    cyc = 4 * tl.beat_s
    ph = (min(t, s2b.t0) - s2a.t0) / cyc
    x, y = plain.path_at(C2_ARC0 + ph * 0.26 * H2)
    calm = _ss((t - s2b.t0) / 2.0)
    x -= 6.0 * ctx.kick * (1.0 - calm)                # shoved back on the kicks, fighting forward
    return x, y


def _cam2(ctx, x, y, t_end=False):
    tl = ctx.tl
    t = tl.section("c2b").t1 - 0.3 if t_end else ctx.t
    s2a = tl.section("c2a")
    t47 = tl.cue(47).t
    calm = _ss((t - tl.section("c2b").t0) / 2.0)
    z = 1.10 + 0.26 * _ease_io((t - s2a.t0) / 12.5)
    hand = (1.0 - 0.7 * calm)
    fx = 860.0 + 90.0 * _ease_io((t - s2a.t0) / 12.0) + 0.5 * (x - 880.0) + hand * (12.0 * _noise(t * 0.9, 21) + 5.0 * _noise(t * 2.3, 22))
    fy = 528.0 + hand * (6.0 * _noise(t * 0.8, 23) + 3.0 * _noise(t * 2.1, 24))
    if not t_end:
        fy -= 10.0 * ctx.kick * (1.0 - calm)
    cam = (z, fx, fy)
    q = _ease_io((t - 150.3) / 3.6)
    if q > 0:
        zp = 300.0 / H2
        tg = (1010.0, 690.0)
        cam = _blend_cam(cam, (zp, x - (tg[0] - C0[0]) / zp, y - (tg[1] - C0[1]) / zp), q)
    dy = 130.0 * _ss((t - (t47 + 0.5)) / 3.2) + 6.0 * max(0.0, t - (t47 + 3.7))
    return Cam(*cam, dy=dy)


def _wind2(tl):
    s2b = tl.section("c2b")
    t_friend = tl.beat_time(204)

    def f(ts):
        return 1.0 - 0.35 * _ss_v(s2b.t0, s2b.t0 + 2.0, ts) - 0.3 * _ss_v(t_friend, t_friend + 2.5, ts)
    return f


def _chorus2(ctx):
    tl, t, c = ctx.tl, ctx.t, ctx.canvas
    s2a, s2b = tl.section("c2a"), tl.section("c2b")
    t_friend = tl.beat_time(204)                      # 151.77
    t47 = tl.cue(47).t
    x, y = _child2(ctx)
    cam = _cam2(ctx, x, y)
    calm2 = _ss((t - s2b.t0) / 2.0)
    pocket = _ss((t - t_friend) / 2.4)
    wf = _wind2(tl)
    w_now = float(wf(np.array([t]))[0])
    clock = _integ(tl, s2a.t0, t, wf, surge=1.6) * 1.0 + s2a.t0
    h = H2
    cyc = 4 * tl.beat_s
    ph = (min(t, s2b.t0) - s2a.t0) / cyc
    pose = figures.lean_wind(ph % 1.0, slump=0.55, stride=0.26, hug=1.0)
    st = _ss((t - s2b.t0) / 0.9)
    if st > 0:
        pose = blend(pose, _with(figures.lean_wind(0.25, slump=0.45, stride=0.0, hug=1.0), lean=0.18), st)
    u = min(1.0, max(0.0, (t - tl.beat_time(186)) / 9.6))
    dis = 0.7 * (1.0 - (1.0 - u) ** 1.8) * (1.0 - _ss((t - (t_friend - 0.4)) / 1.8))
    look_up = _ss((t - t47) / 1.1)
    tone = tuple(P.mix(a, b, calm2 * 0.7) for a, b in zip(cloud.STORM, cloud.GLOOM))
    lift = 0.22 * _ss((t - (t47 + 1.0)) / 3.5)
    tone = tuple(P.mix(a, b, lift) for a, b in zip(tone, cloud.PALE))
    pale = 1.0 - _ss((t - s2a.t0) / 1.6)
    hole = _ss((t - (t47 + 1.4)) / 3.0)
    # the slit sits where it will be seen above the two once the tilt is done
    hole_w = _cam2(ctx, x, y, t_end=True).unmap(P_LID, 1000.0, 215.0)
    hole_s = cam.map(P_LID, *hole_w)
    ents = [tl.beat_time(192 + 2 * i) for i in range(3)]
    ctx.post.exposure *= 1.0 - sum(0.09 * _burst(t - e, 18.0, 0.8) for e in ents)
    # the warm dome around the two: grows, pushing the fog outward
    fx1 = x - 0.19 * h
    dome_c = cam.map(P_GROUND, x - 0.2 * h, y - 0.55 * h)
    dome_r = 40.0 + 520.0 * loom.back_out((t - t_friend) / 2.6, 0.5) * cam.zoom() / 2.0 if t > t_friend else 0.0
    dome = (dome_c[0], dome_c[1], dome_r, 0.75 * pocket) if dome_r > 41 else None
    sway = 2.4 - 1.0 * calm2
    with look.graded(ctx):
        cam.push(c, P_SKY)
        plain.sky(c, 0.0, 1300.0, pale=0.5 * pale, lid=(-420.0, tone[2]))
        c.restore()
        if hole > 0:                                   # paler sky behind the coming slit, no sun
            prims.glow(c, hole_s[0], hole_s[1], 360, P.mix(look.FOG, look.FOG_PALE, 0.8), 0.9, 1.2)
        cam.push(c, P_FAR)
        plain.draw_planes(c, (0,))
        _band(c, (-260, HZ - 130, W + 260, HZ + 60), clock, 1.0, look.FOG_PALE, 60.0, 13, 0.75, 1.3)
        c.restore()
        cam.push(c, P_GROUND)
        plain.draw_planes(c, (1,))
        _gusts(c, ctx, w_now * 1.4, 730.0, 840.0, 15, 0.12)
        c.restore()
        cam.push(c, P_LOOM)
        loom.draw_kind(c, 1, "c2", t, ents[1], 0.2, 0.0, 0.45 * pocket, sway, 0.10, bend=8.0, reach=0.3,
                       sway_t=clock)
        loom.draw_kind(c, 0, "c2", t, ents[0], 0.2, 0.05, pocket, sway, 0.10, reach=0.3, sway_t=clock,
                       fade=1.0 - pocket)
        c.restore()
        cam.push(c, P_LID)
        holes = [(hole_w[0], hole_w[1], 260.0, 0.04 + 0.16 * hole)] if hole > 0 else ()
        cloud.draw(ctx, _lid2_rect(), t=t, heavy=0.6 - 0.2 * calm2, churn=2.5 - 1.3 * calm2, seed=5,
                   tone=tone, holes=holes, seam=None)
        c.restore()
        _fog_layer(c, cam, P_LID + 0.05, (-260, LID2 - 80, W + 260, LID2 + 160), clock, look.FOG, 150.0, 23, 0.45, 1.6)
        _fog_layer(c, cam, 0.95, (-260, 540, W + 260, 800), clock, P.mix(look.FOG, look.FOG_PALE, 0.55), 240.0,
                   17, 0.55 + 0.15 * ctx.kick * w_now, 1.5, hole=dome)
        _lid_stream(c, cam, clock, w_now * (1.0 - calm2), 1.5, LID2, tone[2])
        _sheets(c, cam, clock, w_now, 1.4, dark=1.0 - calm2)
        cam.push(c, P_GROUND)
        loom.draw_kind(c, 2, "c2", t, ents[2], 0.2, 0.1, 0.45 * pocket, sway, 0.08, reach=0.3, sway_t=clock)
        c.restore()
        cam.push(c, P_NEAR)
        plain.draw_planes(c, (2,))
        _gusts(c, ctx, w_now * 1.4, 900.0, 1040.0, 19, 0.10)
        c.restore()
        _fog_layer(c, cam, P_NEAR, (-260, 860, W + 260, 1100), clock, look.FOG, 320.0, 29, 0.28, 1.8, hole=dome)
        cam.push(c, P_CROWS)
        fl = birds.flock_wheel(24, clock, (980.0, 300.0), 560.0, seed=9, speed=1.5, squash=0.36)
        birds.draw_flock(c, fl["x"], fl["y"], 19.0, fl["phase"], fl["heading"], fl["bank"], fl["scale"],
                         alpha=0.85 - 0.25 * calm2)
        c.restore()
        s = (0.55 + 0.45 * ctx.pulse(0.26)) * w_now
        if dome is None:
            look.wind(c, (0, 40, W, 840), clock, s, WIND_ANGLE + 3, seed=11, n=170, speed=1900, alpha=0.6)
        else:                                          # streaks part round the dome
            c.saveLayer(skia.Rect.MakeLTRB(0, 0, W, 860), None)
            look.wind(c, (0, 40, W, 840), clock, s, WIND_ANGLE + 3, seed=11, n=170, speed=1900, alpha=0.6)
            ex = prims.radial_paint(dome[:2], dome[2] * 1.1, (0, 0, 0), 0.95 * pocket, power=0.8, inner=0.3)
            ex.setBlendMode(skia.BlendMode.kDstOut)
            c.drawCircle(dome[0], dome[1], dome[2] * 1.1, ex)
            c.restore()
        if pale > 0:
            c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), prims.fill(look.FOG_LIGHT, 0.8 * pale ** 1.5))
    # the warm pocket of clearer air around the two
    if dome is not None:
        c.save()
        c.translate(*dome[:2])
        c.scale(1.0, 0.8)
        prims.glow(c, 0, 0, dome[2], P.mix(look.FOG_LIGHT, look.PAPER, 0.45), 0.36 * pocket, 1.5)
        prims.glow(c, 0, 0, dome[2] * 0.6, P.mix(look.PAPER, look.AMBER, 0.35), 0.15 * pocket, 1.8)
        c.restore()
    cam.push(c, P_GROUND)
    # the friend steps in from the left (two cycles = four steps) and stands beside
    if t > t_friend - 0.1:
        hf = 134.0
        fy = y - 3.0
        fc = (t - t_friend) / (2 * tl.beat_s)          # one step per beat
        if fc < 2.0:
            fp = figures.walk(fc % 1.0, slump=0.2, stride=0.40)
            fx = fx1 - (2.0 - fc) * 0.40 * hf
        else:
            fp, fx = figures.stand(0.2), fx1
        fp = blend(fp, figures.stand(0.2), _ss((fc - 1.85) / 0.4)) if fc < 2.3 else fp
        _fig(c, "friend", fx, fy, hf, fp, mood=0.4, facing=1, alpha=_ss((t - t_friend) / 1.0), eye="open",
             head_tilt=0.75 * look_up, wind=0.55 * w_now, wind_dir=-1, t=t, shadow=0.3, seed=3)
    with look.graded(ctx, sat=look.sat_for(ctx.hope) + 0.18 * pocket,
                     bounds=(x - 200, y - h * 1.6, x + 200, y + 40)):
        a = _fig(c, "child", x, y, h, pose, mood=-0.5 + 0.6 * pocket, facing=1, dissolve=dis,
                 head_tilt=0.75 * look_up, wind=0.4 + 0.6 * w_now, wind_dir=-1, t=t, shadow=0.3, seed=11)
        hx, hy = a["hold"]
        scraps.armful(c, hx, hy, scale=0.11, t=t + 2.5 * (clock - s2a.t0), seed=2, alpha=0.85 - 0.3 * dis)
    c.restore()
    # a little paler light falls from the rip onto the two faces
    if hole > 0:
        hx, hy = cam.map(P_GROUND, x - 0.1 * h, y - 0.85 * h)
        prims.glow(c, hx, hy, 0.75 * h * cam.zoom(), P.mix(look.FOG_LIGHT, look.CREAM_CLOUD, 0.4), 0.16 * hole, 1.6)
