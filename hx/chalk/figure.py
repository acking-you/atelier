"""hx.chalk.figure: the two characters. A chalk figure that acts: a pose is a small dictionary of
numbers, the body is solved from it in three dimensions (so it can turn round, lie down and roll
over), projected flat, and drawn as a child would draw it: a big round head, a hatched garment,
line limbs with mitts. Read hx/chalk/doc/figure.md.

Body units: 1.0 = standing height. In the body's own frame x = forward, y = up, z = toward its near
side; the origin is the ground point under the figure. Three rotations, in this order:
  turn   the body about its own vertical axis through the pelvis, in quarter turns:
         0 profile (facing the way `face` points), 1 front (facing us), 2 profile the other way,
         -1 the back view. A real rotation: limbs foreshorten, the face slides round the head.
  (flat) the result is projected on the picture plane: X toward `face`, Y up;
  rot    the whole flat figure about the ground point (lying down: + lays the head toward `face`).
Every in-between of two poses is a valid drawing (mixp, mixg): there is no anatomy to get wrong.
A figure laid down by `rot` is drawn with mass (the lying construction: a rounded back that rests on
the surface, trouser legs, limbs folded in the picture); how far follows `rot` alone, so upright
figures are untouched and every blend between lying and upright passes through it smoothly.

figure(F, x, y, h, pose, skin) takes the WORLD ground point and the world standing height and draws
through F.cam; the detail follows the height on screen (h * zoom) and cross-fades.
"""
from __future__ import annotations

import math

import numpy as np
import skia

from .core import C, Frame, blob, chalk, disc, fill, hand, hatch, mix, path_of, ramp, rnd, rsym, scrib, smudge, spline, vn

__all__ = ["Pose", "mixp", "mixg", "mixs", "rebase", "solve", "pose_joints", "aim_hand", "aim_foot", "swap_sides", "alive", "act", "lag", "turn_round",
           "Skin", "SKINS", "CHILD_NIGHT", "FRIEND_NIGHT", "CHILD_DAY", "FRIEND_DAY",
           "figure", "walk", "walk_to", "walk_away", "WALK_BEAT", "Walk", "run", "curl_pose",
           "sit_up_pose", "curl_up_pose", "slide_off_pose", "roll_over_pose", "SIT_CURL", "EDGE_CURL", "lay_pose",
           "STAND", "STOPPED", "LOOK_UP", "REACH", "SIT_HUG", "SIT_LIFT", "ASLEEP", "JUMP", "HOLD",
           "FRONT", "BACK_STAND", "CURL", "CURL_EASE", "CLING", "LIE_UP", "LIE_PHONE", "SIT_EDGE", "SIT_FLOOR", "SIT_SOFA",
           "F_STAND", "F_CALL", "F_OFFER", "F_PART", "F_CROUCH", "F_SMILE",
           "R_HEAD", "TORSO", "THIGH", "SHIN", "UPPER", "FORE", "PEL0", "SHO", "HIP"]

HALF_PI = math.pi / 2.0
R_HEAD = 0.155          # head radius
TORSO = 0.27            # pelvis to neck
THIGH = 0.205
SHIN = 0.205
UPPER = 0.165           # upper arm
FORE = 0.165            # forearm (the mitt adds about 0.03)
PEL0 = 0.414            # standing pelvis height (the legs a little bent: 0.424 would lock the knees)
SHO = 0.086             # shoulder half width (lateral)
HIP = 0.045             # hip half width
OPEN_K = 0.42           # how far `open` = 1 turns a profile toward us (quarter turns)

_DEF = dict(
    pel=(0.0, PEL0),    # pelvis in the picture (X toward face, Y up), relative to the ground point
    pz=0.0,             # pelvis shifted sideways (toward the near side): weight on one leg, seen from the front
    lean=0.0,           # spine angle from vertical, + = forward
    bend=0.0,           # spine curl, + = hunched (head comes forward and down)
    roll=0.0,           # spine leaning sideways (toward the near side), seen from the front or the back
    neck=0.0,           # head nod about the neck, + = forward/down
    tilt=0.0,           # head tipped in the picture plane, + = toward `face`
    turn=0.0,           # the body's turn in quarter turns: 0 profile, 1 front, 2 other profile, -1 back
    hturn=0.0,          # the head turned further than the body (quarter turns, same sense)
    open=0.7,           # 0 flat profile .. 1: a profile opened toward us (spreads shoulders and hips)
    rot=0.0,            # the whole figure rotated in the picture about the ground point, + = toward `face`
    look=(0.30, 0.0),   # where the face sits in the head disc: x forward, y up, -1..1
    gaze=(0.0, 0.0),    # the pupils inside the eyes: x forward, y up, -1..1
    eye=1.0,            # 0 closed, 0.5 half, 1 open, 1.3 wide
    lid=0.0,            # 0..1 heavy lids: a drawn lid line with a drooping outer end, bags under the eyes
    blink=0.0,          # 0..1 closes the eyes on top of `eye`
    joy=0.0,            # 0..1 the lower lids push up: soft domes, then smiling arcs
    brow=0.0,           # 0..1 worried brows (inner ends up)
    lift=0.0,           # 0..1 brows lifted (surprise, hope)
    mouth=0.0,          # -1 turned down .. 0 flat .. 1 smile .. 1.5 the friend's wide smile
    mopen=0.0,          # 0..1 open mouth
    blush=0.0,          # 0..1 warm cheeks
    spark=0.0,          # 0..1 a point of light in the eyes
    hf=(0.02, -0.322),  # near hand, relative to its shoulder (forward, up)
    hb=(0.045, -0.318),  # far hand
    hfz=0.0, hbz=0.0,   # hands out sideways, away from the body (visible from the front and the back)
    ef=-1.0, eb=-1.0,   # elbow side (-1 = elbow behind the arm's line; blends through 0)
    ff=(-0.012, 0.0),   # near foot (ankle on the ground), relative to the ground point (forward, up)
    fb=(0.022, 0.0),    # far foot
    ffz=0.0, fbz=0.0,   # feet apart sideways
    kf=1.0, kb=1.0,     # knee side (+ = forward)
    af=0.0, ab=0.0,     # foot pitch, + = toe up
    hair=0.5,           # 0 drooping .. 1 standing up
    sway=0.0,           # follow-through of hair, scarf and hem: + = left behind toward -X (set it from the motion)
    bob=0.0,            # the same vertically: + = flying up (falling), - = pressed down (rising)
    chest=0.0,          # -1..1 breath: the chest fuller or emptier
    press=0.0,          # 0..1 the crown flattened by a weight resting on it
    front=0.0,          # > 0.5: legs are drawn in front of the garment (knees up)
    over=0.0,           # > 0.5: the far arm is drawn over the head too (arms raised); < -0.5: the near arm goes BEHIND the head too
    lgw=0.0,            # 0..1, a LYING figure only: its legs are laid by the two angles below, not by their ankles (a roll)
    lgf=(0.0, 0.0),     # near leg as it is seen: the directions of its thigh and of its shin, radians (0 = toward `face`, + = up)
    lgb=(0.0, 0.0),     # far leg
)
_FLAGS = ("front", "over")
_PAIRS = tuple(k for k in _DEF if isinstance(_DEF[k], tuple))
_NUMS = tuple(k for k in _DEF if k not in _FLAGS and k not in _PAIRS)


class Pose(dict):
    def __init__(self, base=None, **kw):
        super().__init__(_DEF if base is None else base)
        for k, v in kw.items():
            if k not in _DEF:
                raise KeyError(k)
            self[k] = v

    def but(self, **kw):
        return Pose(self, **kw)


def mixp(a: Pose, b: Pose, w: float) -> Pose:
    """Blend two poses (the two layer flags `front` and `over` switch at the half-way point)."""
    w = min(1.0, max(0.0, float(w)))
    out = Pose()
    for k in _NUMS:
        out[k] = a[k] + (b[k] - a[k]) * w
    for k in _PAIRS:
        p, q = a[k], b[k]
        out[k] = (p[0] + (q[0] - p[0]) * w, p[1] + (q[1] - p[1]) * w)
    for k in _FLAGS:
        out[k] = a[k] if w < 0.5 else b[k]
    return out


def mixg(a: Pose, b: Pose, w: dict, default: float) -> Pose:
    """Blend with a different weight per key (overlapping action: the eyes lead, then the head, the
    spine, the hands; the hair arrives last)."""
    out = Pose()
    for k in _DEF:
        ww = min(1.0, max(0.0, float(w.get(k, default))))
        if k in _FLAGS:
            out[k] = a[k] if ww < 0.5 else b[k]
        elif k in _PAIRS:
            out[k] = (a[k][0] + (b[k][0] - a[k][0]) * ww, a[k][1] + (b[k][1] - a[k][1]) * ww)
        else:
            out[k] = a[k] + (b[k] - a[k]) * ww
    return out


def swap_sides(P: Pose) -> Pose:
    """The same drawing seen as the mirrored figure: figure(.., P, face) and figure(.., swap_sides(P), -face)
    are the same picture (near and far limbs change names, turn becomes 2 - turn). Use it after a
    turn-round to go on with poses that face the new way (walk_to gives such poses)."""
    return P.but(hf=P["hb"], hb=P["hf"], hfz=P["hbz"], hbz=P["hfz"], ef=P["eb"], eb=P["ef"], ff=P["fb"], fb=P["ff"],
                 ffz=P["fbz"], fbz=P["ffz"], kf=P["kb"], kb=P["kf"], af=P["ab"], ab=P["af"], turn=2.0 - P["turn"],
                 hturn=-P["hturn"], pz=-P["pz"], roll=-P["roll"])


def mixs(a: Pose, b: Pose, w: float, feet: bool = True, hands: bool = False) -> Pose:
    """mixp for two poses whose `rot` or `turn` differ much (lying down, sitting up, rolling over):
    the ankles (and with hands=True the hands) travel in straight lines in the picture, so feet that
    rest on a seat in both poses rest on it all the way. About 0.4 ms."""
    P = mixp(a, b, w)
    if 0.0 < w < 1.0:
        Ja, Jb = _seen_joints(a), _seen_joints(b)
        for on, kind, aim in ((feet, "an_", aim_foot), (hands, "ha_", aim_hand)):
            if on:
                for which in ("f", "b"):
                    k = kind + which
                    P = aim(P, which, Ja[k] + (Jb[k] - Ja[k]) * w, True)
    return P


def rebase(P: Pose, dx: float = 0.0, dy: float = 0.0) -> Pose:
    """The same drawing with its ground point moved by (dx, dy) body units as seen (x toward `face`, y
    up): figure(F, x + face * h * dx, y - h * dy, h, rebase(P, dx, dy)) is figure(F, x, y, h, P). Use it
    to give two poses one ground point before blending them (a pose on the seat and one on the floor:
    rebase(SIT_SOFA, 0, -seat_height / h) has its ground point on the floor under the seat)."""
    d = _unrot(P, (dx, dy), True)
    return P.but(pel=(P["pel"][0] - d[0], P["pel"][1] - d[1]), ff=(P["ff"][0] - d[0], P["ff"][1] - d[1]),
                 fb=(P["fb"][0] - d[0], P["fb"][1] - d[1]))


def _seen_joints(P):
    """Hands and ankles as seen (after rot), in body units from the ground point."""
    J = solve(P)
    c_, s_ = math.cos(P["rot"]), math.sin(P["rot"])
    return {k: np.array([J[k][0] * c_ + J[k][1] * s_, -J[k][0] * s_ + J[k][1] * c_]) for k in ("an_f", "an_b", "ha_f", "ha_b")}


def _seen(P, **kw):
    """A pose with hands (hf, hb) and ankles (ff, fb) placed where they are to be seen."""
    for k, pt in kw.items():
        P = (aim_hand if k[0] == "h" else aim_foot)(P, k[1], pt, True)
    return P


def _fwd(v, a):
    """Rotate vector v 'forward' by a (up turns toward +x)."""
    ca, sa = math.cos(a), math.sin(a)
    return np.array([v[0] * ca + v[1] * sa, -v[0] * sa + v[1] * ca])


def ik2(a, b, l1, l2, side, stretch=1.06):
    """Middle joint of a flat 2-bone chain from a to b. side=+1 puts it counter-clockwise of a->b."""
    a3, b3 = np.array([a[0], a[1], 0.0]), np.array([b[0], b[1], 0.0])
    m, e = _ik3(a3, b3, l1, l2, side, stretch)
    return m[:2], e[:2]


_YUP = np.array([0.0, 1.0, 0.0])


def _ik3(a, b, l1, l2, side, stretch=1.06):
    """Middle joint of a 2-bone chain from a to b in the body's space. The joint bends in the plane
    that holds the limb and the sagittal direction (side = +1: counter-clockwise of a->b seen from the
    near side; fractions pass through the straight limb, so a blend never snaps)."""
    d = b - a
    dist = math.sqrt(float(d @ d))
    reach = l1 + l2
    if dist > reach * stretch:
        b = a + d * (reach * stretch / dist)
        d = b - a
        dist = reach * stretch
    if dist >= reach * 0.9995:
        return a + d * (l1 / reach), b
    if dist < 1e-6:
        e1 = np.array([0.0, -1.0, 0.0])
    else:
        e1 = d / dist
    dist = max(dist, abs(l1 - l2) + 1e-4)
    ca = max(-1.0, min(1.0, (l1 * l1 + dist * dist - l2 * l2) / (2.0 * l1 * dist)))
    sa = math.sqrt(1.0 - ca * ca)
    pl = math.hypot(e1[0], e1[1])
    e2 = np.array([-e1[1], e1[0], 0.0])
    if pl < 0.999:                                   # a limb held out sideways: the joint hangs down (or points up)
        e2 = e2 + _YUP * (1.0 - pl)
        e2 = e2 - e1 * float(e2 @ e1)
    n = math.sqrt(float(e2 @ e2))
    e2 = e2 / n if n > 1e-9 else _YUP
    s = max(-1.0, min(1.0, float(side)))
    return a + l1 * (ca * e1 + s * sa * e2), b


def _splay(a, m, b, k):
    """A bent limb's middle joint leans outward (sideways) by k times its distance from the limb's
    chord: invisible in a profile; from the front it makes knees and elbows read."""
    c = (a + b) * 0.5
    d = m - c
    off = math.sqrt(float(d @ d))
    if off < 1e-4:
        return m
    return np.array([m[0], m[1], m[2] + k * off])


def _fold_flat(a, b, l1, l2, side, g=None, low=None):
    """Middle joint of a 2-bone chain from a to b folded in the picture plane (side = +1: counter-
    clockwise of a->b; fractions pass through the foreshortened limb). With g (the unit vector 'up')
    and low: the joint is not let below the height low along g: the limb foreshortens instead (a
    knee that would sink into the seat turns toward us and stays on it)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    dist = math.hypot(dx, dy)
    reach = l1 + l2
    if dist >= reach * 0.9995:
        return np.array([a[0] + dx * l1 / dist, a[1] + dy * l1 / dist])
    e1x, e1y = (dx / dist, dy / dist) if dist > 1e-6 else (0.0, -1.0)
    dist = max(dist, abs(l1 - l2) + 1e-4)
    ca = max(-1.0, min(1.0, (l1 * l1 + dist * dist - l2 * l2) / (2.0 * l1 * dist)))
    sa = l1 * math.sqrt(1.0 - ca * ca)
    bx, by = a[0] + l1 * ca * e1x, a[1] + l1 * ca * e1y
    f = max(-1.0, min(1.0, float(side)))
    if low is not None:
        ey = sa * (-e1y * g[0] + e1x * g[1])
        y0 = bx * g[0] + by * g[1]
        if y0 + f * ey < low and abs(ey) > 1e-9:
            f = max(-1.0, min(1.0, (low - y0) / ey))
    return np.array([bx - f * sa * e1y, by + f * sa * e1x])


_U = np.linspace(0.0, 1.0, 7)
_B0, _B1, _B2 = (1.0 - _U) ** 2, 2.0 * _U * (1.0 - _U), _U ** 2


def solve(P: Pose) -> dict:
    """The joints of a pose, flat in the picture, in body units, before `rot` and before the mirror
    of `face` (X toward `face`, Y up, origin = the ground point). Keys (arrays of 2): pel neck head
    sh_f sh_b el_f el_b ha_f ha_b hip_f hip_b kn_f kn_b an_f an_b heel_f toe_f heel_b toe_b tan0 tan1
    (unit tangents of the spine at the pelvis and at the neck); spine (7, 2); hang (the head's angle
    from vertical, + forward); hang_s (the same before the turn); ct, st (cos and sin of the turn),
    se (sin of the turn with the `open` cheat: what spreads shoulders and hips); near ('f' or 'b':
    whose limbs are on our side)."""
    yt = P["turn"] * HALF_PI
    ct, st = math.cos(yt), math.sin(yt)
    ye = yt + OPEN_K * P["open"] * ct * abs(ct) * HALF_PI
    se = math.sin(ye)
    px, py = P["pel"]
    pz = P["pz"]
    lean, bend = P["lean"], P["bend"]
    ux, uy = math.sin(lean), math.cos(lean)
    L = TORSO * (1.0 - 0.06 * abs(bend))
    nx, ny = px + ux * L, py + uy * L
    k = bend * TORSO * 0.42
    qx, qy = px + ux * TORSO * 0.5 - uy * k, py + uy * TORSO * 0.5 + ux * k
    sx = _B0 * px + _B1 * qx + _B2 * nx
    sy = _B0 * py + _B1 * qy + _B2 * ny
    t1x, t1y = nx - qx, ny - qy
    n1 = math.hypot(t1x, t1y) + 1e-9
    t1x, t1y = t1x / n1, t1y / n1
    nk = max(-0.8, min(0.8, P["neck"]))
    cn, sn = math.cos(nk), math.sin(nk)
    hdx, hdy = t1x * cn + t1y * sn, -t1x * sn + t1y * cn
    hx, hy = nx + hdx * R_HEAD * 0.88, ny + hdy * R_HEAD * 0.88
    rl = P["roll"]
    crl, srl = math.cos(rl), math.sin(rl)

    def flat(p):                                     # a point of the body's space -> the picture
        return np.array([px + (p[0] - px) * ct - p[2] * se, p[1]])

    def up3(x, y, zl=0.0):                           # a point of the upper body (it rolls about the pelvis)
        dy = y - py
        return np.array([x, py + dy * crl - zl * srl, pz + dy * srl + zl * crl])

    spine = np.stack([px + (sx - px) * ct - (pz + (sy - py) * srl) * se, py + (sy - py) * crl], axis=1)
    pel, neck = spine[0], spine[6]
    v = flat(up3(hx, hy)) - neck
    if P["tilt"]:
        v = _fwd(v, P["tilt"])
    head = neck + v

    def unit(d, fallback):
        n = math.hypot(d[0], d[1])
        return d / n if n > 1e-6 else fallback

    ctrl = flat(up3(qx, qy))
    tan0 = unit(ctrl - pel, np.array([0.0, 1.0]))
    tan1 = unit(neck - ctrl, tan0)
    out = dict(pel=pel, spine=spine, neck=neck, head=head, hang=math.atan2(v[0], v[1]), hang_s=math.atan2(hdx, hdy),
               tan0=tan0, tan1=tan1, ct=ct, st=st, se=se, near="f" if ct >= 0.0 else "b")
    for w, sg in (("f", 1.0), ("b", -1.0)):
        sh = up3(sx[5], sy[5], sg * SHO)
        hh = P["h" + w]
        el, ha = _ik3(sh, sh + np.array([hh[0], hh[1], sg * P["h" + w + "z"]]), UPPER, FORE, P["e" + w])
        hip = np.array([px, py, pz + sg * HIP])
        ft = P["f" + w]
        kn, an = _ik3(hip, np.array([ft[0], ft[1] + 0.014, sg * (HIP + P["f" + w + "z"])]), THIGH, SHIN, P["k" + w])
        pitch = P["a" + w]
        he = _fwd((-0.020, -0.006), -pitch)
        to = _fwd((0.074, -0.006), -pitch)
        heel = an + np.array([he[0], he[1], 0.0])
        toe = an + np.array([to[0], to[1] - 0.012 * max(0.0, st), sg * (0.008 + 0.040 * st * st)])
        el = _splay(sh, el, ha, sg * 0.45)
        kn = _splay(hip, kn, an, sg * 0.40)
        out["sh_" + w], out["el_" + w], out["ha_" + w] = flat(sh), flat(el), flat(ha)
        out["hip_" + w], out["kn_" + w], out["an_" + w] = flat(hip), flat(kn), flat(an)
        out["heel_" + w], out["toe_" + w] = flat(heel), flat(toe)
    lie = _lie_w(P)
    if lie > 0.0:                                    # lying: knees and elbows fold in the picture, at full length (mass, not sticks)
        sgn = max(-1.0, min(1.0, ct / 0.30))                     # (rolling over, turn about 1: the folds pass through the limb seen end on)
        g = (-math.sin(P["rot"]), math.cos(P["rot"]))            # 'up' as the figure is seen: knees stay above the surface
        for w in ("f", "b"):
            for a_, m_, b_, l1, l2, key, low in (("hip_", "kn_", "an_", THIGH, SHIN, "k", 0.034),
                                                 ("sh_", "el_", "ha_", UPPER, FORE, "e", None)):
                m2 = _fold_flat(out[a_ + w], out[b_ + w], l1, l2, P[key + w] * sgn, g, low)
                out[m_ + w] = out[m_ + w] + (m2 - out[m_ + w]) * lie
            if P["lgw"] > 0.0:                       # the leg laid by its two angles as seen (rolling over: the knee swings over)
                q1, q2 = P["lg" + w][0] + P["rot"], P["lg" + w][1] + P["rot"]
                kn2 = out["hip_" + w] + np.array([THIGH * math.cos(q1), THIGH * math.sin(q1)])
                an2 = kn2 + np.array([SHIN * math.cos(q2), SHIN * math.sin(q2)])
                lg = min(1.0, P["lgw"]) * lie
                out["kn_" + w] = out["kn_" + w] + (kn2 - out["kn_" + w]) * lg
                out["an_" + w] = out["an_" + w] + (an2 - out["an_" + w]) * lg
            for k_, v in (("heel_", (-0.020, -0.006)), ("toe_", (0.074, -0.006))):      # the foot too lies in the picture
                q = _fwd(v, -P["a" + w])
                q = out["an_" + w] + np.array([q[0] * sgn, q[1]])
                out[k_ + w] = out[k_ + w] + (q - out[k_ + w]) * lie
    if P["rot"]:                                     # tipped or laid in the picture: no toe or heel goes under the surface it is on
        sr_, cr_ = math.sin(P["rot"]), math.cos(P["rot"])           # (the foot foreshortens instead, as if it turned toward us)
        wr = min(1.0, abs(P["rot"]) / 0.12)
        for k_ in ("heel_f", "toe_f", "heel_b", "toe_b"):
            q = out[k_]
            dy = 0.006 - (-q[0] * sr_ + q[1] * cr_)
            if dy > 0.0:
                out[k_] = np.array([q[0] - sr_ * dy * wr, q[1] + cr_ * dy * wr])
    return out


_JOINTS = ("head", "neck", "pel", "ha_f", "ha_b", "el_f", "el_b", "sh_f", "sh_b", "hip_f", "hip_b", "an_f", "an_b", "kn_f",
           "kn_b", "toe_f", "toe_b")


def _head_frame(P: Pose, J: dict, face: int):
    """The head's frame on screen: (ha, fw, dn, chh, shh, ly, ub, sg): its tilt, the unit vectors
    toward the face side and down the face (y down), cos and sin of the head's own turn, the face's
    height in the head after the turn, how far the face has turned away (0..1) and the side it leaves by."""
    ha = max(-0.5, min(0.5, 0.7 * J["hang_s"] * J["ct"])) + P["tilt"] + P["rot"] + 0.8 * P["roll"] * J["se"]
    cha, sha = math.cos(ha), math.sin(ha)
    yh = (P["turn"] + P["hturn"]) * HALF_PI
    chh, shh = math.cos(yh), math.sin(yh)
    ly = max(-1.15, min(1.15, P["look"][1] - 0.8 * J["hang_s"] * max(0.0, J["st"])))
    ub = ramp(max(0.0, -shh), 0.0, 0.8)
    return ha, np.array([face * cha, sha]), np.array([-face * sha, cha]), chh, shh, ly, ub, (1.0 if chh >= 0.0 else -1.0)


def _extras(out: dict, P: Pose, J: dict, face: int):
    """R, up, crown and mouth for the joint dictionary."""
    R = out["R"]
    hc = out["head"]
    d = hc - out["neck"]
    n = math.hypot(d[0], d[1])
    up = d / n if n > 1e-9 else np.array([0.0, -1.0])
    ha, fw, dn, chh, shh, ly, ub, sg = _head_frame(P, J, face)
    out["up"] = up
    out["crown"] = hc + up * (R * (1.0 - 0.17 * P["press"]))
    out["top"] = np.array([hc[0], hc[1] - R * (1.0 - 0.17 * P["press"] * max(0.0, -up[1]))])
    out["mouth"] = hc + fw * (sg * (0.40 * P["look"][0] * abs(chh) + 2.0 * ub) * R) + dn * ((0.57 - ly * 0.34) * R)
    return out


def pose_joints(P: Pose, x: float, y: float, h: float, face: int = 1, kind: str = "child") -> dict:
    """The world joints of a pose without drawing it (what figure() returns): head neck pel ha_f ha_b
    el_f el_b sh_f sh_b hip_f hip_b an_f an_b kn_f kn_b toe_f toe_b (arrays of 2), R (head radius),
    crown (the top of the skull: where the strand leaves; on a lying head it points sideways), top
    (the highest point of the head as it is seen) and back (the top of the back: the highest part of
    the garment; on a lying figure the hump of its back): where a weight rests; up (unit vector from
    the neck to the head, y down) and mouth. kind: whose garment ("child" | "friend"). About 0.15 ms."""
    J = solve(P)
    cr, sr = math.cos(P["rot"]), math.sin(P["rot"])
    face = 1 if face >= 0 else -1
    fh = face * h
    out = {}
    for k in _JOINTS:
        p = J[k]
        out[k] = np.array([x + fh * (p[0] * cr + p[1] * sr), y - h * (-p[0] * sr + p[1] * cr)])
    out["R"] = R_HEAD * h
    bk, top, fr, hemc = _torso(P, J, kind)
    G = np.vstack([bk, top[None, :], fr[::-1], hemc[None, :]])
    out["back"] = _back_of(np.stack([x + fh * (G[:, 0] * cr + G[:, 1] * sr), y - h * (-G[:, 0] * sr + G[:, 1] * cr)], axis=1), h)
    return _extras(out, P, J, face)


def _aim(P: Pose, key: str, zkey: str, sg: float, cur, target) -> Pose:
    """Move a hand or a foot so that it shows at a picture point, by the shortest move in space."""
    yt = P["turn"] * HALF_PI
    ct = math.cos(yt)
    se = math.sin(yt + OPEN_K * P["open"] * ct * abs(ct) * HALF_PI)
    dX, dY = float(target[0] - cur[0]), float(target[1] - cur[1])
    n = ct * ct + se * se + 1e-9
    v = P[key]
    return P.but(**{key: (v[0] + dX * ct / n, v[1] + dY), zkey: P[zkey] - sg * dX * se / n})


def _unrot(P, target, seen):
    t = np.asarray(target, dtype=np.float64)
    if not seen or not P["rot"]:
        return t
    c_, s_ = math.cos(P["rot"]), math.sin(P["rot"])
    return np.array([t[0] * c_ - t[1] * s_, t[0] * s_ + t[1] * c_])


def aim_hand(P: Pose, which: str, target, seen: bool = False) -> Pose:
    """The pose with one hand ('f' near, 'b' far) aimed at a point of the picture in body units
    relative to the ground point: as solve() gives them (before `rot`), or with seen=True as the
    figure is seen (after `rot`: what you want for a lying figure). Works at any turn. If the point
    is out of reach the arm stretches toward it."""
    sg = 1.0 if which == "f" else -1.0
    J = solve(P)
    return _aim(P, "h" + which, "h" + which + "z", sg, J["sh_" + which] + _flat_hand(P, which, J), _unrot(P, target, seen))


def _flat_hand(P, which, J):
    """Where the hand target (not the clamped hand) shows, relative to its shoulder."""
    sg = 1.0 if which == "f" else -1.0
    hh = P["h" + which]
    return np.array([hh[0] * J["ct"] - sg * P["h" + which + "z"] * J["se"], hh[1]])


def aim_foot(P: Pose, which: str, target, seen: bool = False) -> Pose:
    """The pose with one ankle ('f' near, 'b' far) on a point of the picture in body units (before
    `rot`, or as seen with seen=True)."""
    sg = 1.0 if which == "f" else -1.0
    J = solve(P)
    px = P["pel"][0]
    ft = P["f" + which]
    cur = np.array([px + (ft[0] - px) * J["ct"] - sg * (HIP + P["f" + which + "z"]) * J["se"], ft[1] + 0.014])
    return _aim(P, "f" + which, "f" + which + "z", sg, cur, _unrot(P, target, seen))


# --------------------------------------------------------------------------
# skins
# --------------------------------------------------------------------------
class Skin:
    """The colours of a character on one paper. kind: 'child' | 'friend' (build and hair). line: the
    outline; arm / leg: None for a plain line limb, or the tone a limb is coloured with inside its
    outline (a sleeve, a trouser leg); hand / shoe: None for the line colour, or the mitt's and the
    shoe's own; garment + garment2 (base tone and zigzag); face + face2; hair + hair_line; feature
    (eyes, mouth); knock (what is rubbed out behind the figure); blush (colour) and blush0 (how warm
    the cheeks are at rest); scarf; edge (dusty edge of the line); halo (rub out behind the limbs);
    soft (0..1: softer, lighter outlines: the day skins)."""

    def __init__(self, **kw):
        self.arm = self.leg = self.shoe = self.hand = None
        self.blush0 = 0.0
        self.soft = 0.0
        self.halo = True
        self.__dict__.update(kw)


CHILD_NIGHT = Skin(kind="child", line=C.CHALK, garment=(0.33, 0.42, 0.66), garment2=(0.60, 0.70, 0.90),
                   face=(0.80, 0.83, 0.89), face2=(0.94, 0.94, 0.93), hair=(0.25, 0.32, 0.54),
                   hair_line=(0.55, 0.64, 0.85), feature=(0.07, 0.08, 0.13), knock=C.KNOCK,
                   blush=mix(C.AMBER_PALE, C.AMBER, 0.30), scarf=None, edge=0.34, grain="dense")
FRIEND_NIGHT = Skin(kind="friend", line=C.AMBER, garment=(0.80, 0.42, 0.10), garment2=(0.99, 0.70, 0.26),
                    face=(0.98, 0.80, 0.48), face2=(1.0, 0.90, 0.66), hair=(0.80, 0.42, 0.12),
                    hair_line=(0.96, 0.62, 0.22), feature=(0.20, 0.09, 0.03), knock=C.KNOCK, blush=(1.0, 0.62, 0.36),
                    scarf=(0.98, 0.50, 0.20), edge=0.38, grain="dense")
_SLATE = mix(C.PENCIL, (0.26, 0.33, 0.52), 0.62)
CHILD_DAY = Skin(kind="child", line=mix(C.PENCIL, _SLATE, 0.35), arm=C.SKIN, hand=C.SKIN, blush0=0.22, leg=mix(_SLATE, C.JUMPER, 0.30),
                 shoe=mix(C.PENCIL, C.CORAL, 0.22), garment=C.JUMPER, garment2=mix(C.JUMPER, C.CREAM, 0.55),
                 face=C.SKIN, face2=mix(C.SKIN, C.CREAM, 0.65), hair=_SLATE, hair_line=mix(_SLATE, C.JUMPER, 0.55),
                 feature=mix(C.PENCIL, (0.16, 0.10, 0.12), 0.4), knock=C.DAY, blush=C.ROSE, scarf=None, edge=0.20,
                 grain="dense", halo=False, soft=1.0)
_CHESTNUT = mix(C.PENCIL, C.COAT, 0.42)
FRIEND_DAY = Skin(kind="friend", line=mix(C.PENCIL, C.CORAL, 0.30), arm=mix(C.SKIN, C.COAT, 0.12),
                  hand=mix(C.SKIN, C.COAT, 0.12), blush0=0.30,
                  leg=mix(C.CORAL, C.PENCIL, 0.42), shoe=mix(C.PENCIL, C.CORAL, 0.30), garment=C.COAT,
                  garment2=mix(C.COAT, C.CREAM, 0.50), face=mix(C.SKIN, C.CREAM, 0.15), face2=mix(C.SKIN, C.CREAM, 0.7),
                  hair=_CHESTNUT, hair_line=mix(_CHESTNUT, C.COAT, 0.55), feature=mix(C.PENCIL, (0.30, 0.14, 0.08), 0.5),
                  knock=C.DAY, blush=C.ROSE, scarf=C.CORAL, edge=0.20, grain="dense", halo=False, soft=1.0)

SKINS = {"child": (CHILD_NIGHT, CHILD_DAY), "friend": (FRIEND_NIGHT, FRIEND_DAY)}

# tufts on the crown: (azimuth from the face direction in rad, + toward the near side; angle from the top; length in R)
_TUFTS_CHILD = ((2.95, 1.02, 0.62), (3.70, 0.62, 0.52), (2.05, 0.50, 0.56), (0.45, 0.42, 0.60), (5.25, 0.56, 0.52),
                (4.45, 0.92, 0.46))
_TUFTS_FRIEND = ((1.25, 0.20, 0.21), (1.75, 0.36, 0.15))      # one small sprout of two hairs, off the middle (never two horns)
# garment half widths (hem, shoulder): seen from the side, seen from the front; and how far the hem hangs below the pelvis
_GARMENT = {"child": ((0.106, 0.080), (0.118, 0.102), 0.040), "friend": ((0.150, 0.066), (0.172, 0.084), 0.085)}


# --------------------------------------------------------------------------
# the lying construction (a figure laid down by `rot`: asleep on the sofa, curled, on its back)
# --------------------------------------------------------------------------
# A lying figure is drawn with mass: the garment becomes one rounded shape that lies on the surface
# (the ground point's level), its upper side standing out as the back, its zigzag following the curve;
# the legs become trouser legs (two tapering shapes each) instead of lines. How far this is on follows
# `rot` alone (_lie_w), so every blend between a lying and an upright pose passes through it smoothly
# and upright poses are drawn exactly as before.
_LIE_R0, _LIE_R1 = 0.30, 0.85          # |rot| where the lying construction begins and where it is complete
_LIE_OUT = np.array([0.15, 0.42, 0.60, 0.70, 0.72, 0.66, 0.48, 0.12])      # the upper side stands out further (per station, hem to neck)
_LIE_FLAT = np.array([1.0, 1.0, 1.0, 0.9, 0.7, 0.4, 0.15, 0.0])           # the lower side is laid on the surface
_LIE_BREATH = np.array([0.15, 0.45, 0.8, 1.0, 1.0, 0.8, 0.5, 0.2])        # where the breath lifts the back
_LIE_AIR = 0.075                       # how far a breath lifts the back (of its height above the spine)
_LIE_TAIL = 0.055                      # the hem end reaches this much further (it covers the seat of the trousers)
_LIE_LEG = (0.054, 0.040, 0.032, 0.026)        # trouser leg: radius at the hip, the knee (thigh, shin), the ankle (body units)
_LIE_TONE = ((0.34, 0.41, 0.60), 0.92)         # the night skin's trousers: one plain rubbed tone (the day skin uses its `leg`)
_LIE_ARM = (0.22, 0.16)                        # a lying figure's arm: how much wider its line, how much more of it the skin's colour
# a lying figure being drawn on: its limbs come one after the other (far leg, near leg, far arm, near arm), each from..to
# of the limbs' share of `draw`; within a leg the thigh, then the shin, then the foot
_LIE_ON = ((0.00, 0.34), (0.24, 0.58), (0.52, 0.78), (0.72, 1.00))


def _lie_w(P) -> float:
    """0..1: how far the lying construction is on (0 = the upright drawing, untouched)."""
    r = abs(P["rot"])
    if r <= _LIE_R0:
        return 0.0
    v = min(1.0, (r - _LIE_R0) / (_LIE_R1 - _LIE_R0))
    return v * v * (3.0 - 2.0 * v)


def _lie_torso(lie, core, nrm, bk, fr, top, hemc, tan0, cr, sr, sw, chest):
    """The garment's anchors (bk, fr: 8 stations from the hem to the neck; top, hemc) of a lying figure,
    in the body's frame: the side that is up stands out further and rises with the breath, the side
    that is down is laid on the surface, the hem end reaches further and is rounded off. sw: the
    swell of the breath already in bk and fr (per station). Returns (bk, fr, top, hemc, up) where up
    is +1 if the fr side is the upper one, else -1."""
    g = np.array([-sr, cr])                                    # 'up' as the figure is seen
    up = 1.0 if float((nrm[1:7] @ g).sum()) >= 0.0 else -1.0
    U, D = (fr, bk) if up > 0.0 else (bk, fr)
    U2 = core + (U - core) * ((1.0 + _LIE_OUT) * (1.0 + _LIE_BREATH * (_LIE_AIR * chest)) / sw)[:, None]
    yD = D @ g
    yt = np.where(yD < 0.004, 0.004, yD - np.minimum(yD - 0.004, 0.055) * _LIE_FLAT)
    D2 = D + np.outer(yt - yD, g)
    h2 = hemc - tan0 * _LIE_TAIL
    yh = float(h2 @ g)
    if yh < 0.004:
        h2 = h2 + g * (0.004 - yh)
    U3, D3 = U + (U2 - U) * lie, D + (D2 - D) * lie
    h3 = hemc + (h2 - hemc) * lie
    return ((D3, U3) if up > 0.0 else (U3, D3)) + (top, h3, up)


def _round(P, k: float, m: int = 4):
    """A closed polygon P (N, 2; not repeated) rounded into a closed Catmull-Rom curve through its
    points, k = 0..1 of the way (0 = the polygon itself, sampled as densely)."""
    n = len(P)
    f = (np.arange(m) / m)[None, :, None]
    p0, p1, p2, p3 = (np.roll(P, 1, 0)[:, None, :], P[:, None, :], np.roll(P, -1, 0)[:, None, :], np.roll(P, -2, 0)[:, None, :])
    lin = p1 + (p2 - p1) * f
    if k <= 0.0:
        return lin.reshape(n * m, 2)
    cr_ = 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)
    return (lin + (cr_ - lin) * min(1.0, k)).reshape(n * m, 2)


def _lie_zigzag(Dw, Uw, gap: float, seed: int, slant: float = 0.55, over: float = 0.22, jit: float = 0.3):
    """The zigzag that follows a lying back: rows across the shape between its lower side Dw and its
    upper side Uw (world polylines, station by station, tail to neck), leaning along it by `slant`
    (in gaps), turning short of or over the outline. Returns a world polyline, or None."""
    mid = (Dw + Uw) * 0.5
    seg = np.hypot(np.diff(mid[:, 0]), np.diff(mid[:, 1]))
    L = float(seg.sum())
    m = int(L / gap)
    if m < 2:
        return None
    s = np.concatenate([[0.0], np.cumsum(seg)]) / L
    wd = float(np.hypot(*(Uw - Dw).T).mean()) + 1e-9
    sl = slant * 0.5 * wd / L                                  # the lean, as a fraction of the length
    tau = np.linspace(0.0, 1.0, 4)
    out = []
    for i in range(m):
        uc = (i + 0.5 + jit * rsym(seed * 71 + i, 13)) / m
        v0 = 0.02 - over * gap / wd * (2.0 * rnd(seed * 53 + i, 29) - 1.25)
        v1 = 0.98 + over * gap / wd * (2.0 * rnd(seed * 59 + i, 31) - 1.25)
        u = np.clip(uc - sl + 2.0 * sl * tau, 0.0, 1.0)
        v = v0 + (v1 - v0) * tau
        dx, dy = np.interp(u, s, Dw[:, 0]), np.interp(u, s, Dw[:, 1])
        ux, uy = np.interp(u, s, Uw[:, 0]), np.interp(u, s, Uw[:, 1])
        row = np.stack([dx + (ux - dx) * v, dy + (uy - dy) * v], axis=1)
        out.append(row if i % 2 == 0 else row[::-1])
    return np.vstack(out)


def _lie_hatch(F, Dw, Uw, poly, col, gap, w, a, seed, grain, wob, draw):
    """Colour a lying garment in with the zigzag that follows its back (see core.hatch)."""
    if a <= 0.003 or draw <= 0.0:
        return
    z = F.cam.zoom
    tone = 1.0 - ramp(gap * z, 1.6, 3.0)
    if tone > 0.0:
        fill(F, poly, col, a * min(1.0, w / gap) * tone * draw, grain)
        if tone >= 1.0:
            return
    Z = _lie_zigzag(Dw, Uw, gap, seed)
    if Z is None:
        return
    Q, s = hand(Z, seed + 17, F.k, wob, max(5.0, gap * 1.2), 0.6, z)
    if draw < 1.0:
        L = s[-1] * draw
        m_ = s <= L
        if m_.sum() < 2:
            return
        Q = Q[m_]
    ws, a = F.lw(w, a * (1.0 - tone), 1.0)
    F.c.drawPath(path_of(F.cam.pts(Q)), F.pen(col, ws, a, grain))


def _torso(P, J, kind: str = "child"):
    """The garment's anchors of a pose in the body's frame, as figure() draws them (without the swing
    of a coat's hem): (bk, top, fr, hemc), lying construction included."""
    (wb_p, wt_p), (wb_f, wt_f), hem = _GARMENT[kind]
    fl2 = min(1.0, abs(J["se"])) ** 2
    wb, wt = wb_p + (wb_f - wb_p) * fl2, wt_p + (wt_f - wt_p) * fl2
    sp = J["spine"]
    core = np.vstack([sp[0] - J["tan0"] * hem, sp])
    uu = np.linspace(0.0, 1.0, len(core))
    d = np.gradient(core, axis=0)
    ln = np.hypot(d[:, 0], d[:, 1])
    if float(ln.min()) < 1e-6:
        d, ln = np.tile(J["tan0"], (len(core), 1)), np.ones(len(core))
    nrm = np.stack([d[:, 1] / ln, -d[:, 0] / ln], axis=1)
    half = (wb + (wt - wb) * uu ** 0.85) * (1.0 - 0.36 * np.clip((uu - 0.80) / 0.20, 0.0, 1.0) ** 2)
    sw = 1.0 + 0.055 * P["chest"] * np.exp(-((uu - 0.62) / 0.26) ** 2)
    half = half * sw
    fr, bk = core + nrm * half[:, None], core - nrm * half[:, None]
    top = sp[-1] + J["tan1"] * 0.012
    hemc = (fr[0] + bk[0]) / 2 - J["tan0"] * 0.012
    lie = _lie_w(P)
    if lie > 0.0:
        bk, fr, top, hemc, _ = _lie_torso(lie, core, nrm, bk, fr, top, hemc, J["tan0"], math.cos(P["rot"]), math.sin(P["rot"]),
                                          sw, P["chest"])
    return bk, top, fr, hemc


def _back_of(G, h: float):
    """The top of the back: the highest part of the garment's outline G (world points), taken softly
    so that it does not jump from point to point while the figure moves."""
    w = np.exp(-(G[:, 1] - G[:, 1].min()) / (0.022 * h))
    return (G * w[:, None]).sum(0) / w.sum()


def _capsule(c0, r0, c1, r1, n: int = 7):
    """The closed outline round two circles (a tapering sausage), world points; it starts and ends
    beside c0, on its left seen from c0 toward c1."""
    d = c1 - c0
    L = math.hypot(d[0], d[1])
    ang = math.atan2(d[1], d[0])
    ph = math.acos(max(-1.0, min(1.0, (r0 - r1) / L))) if L > 1e-6 else HALF_PI
    a0 = ang + np.linspace(ph, 2.0 * math.pi - ph, n + 2)
    a1 = ang + np.linspace(-ph, ph, n)
    return np.vstack([np.stack([c0[0] + np.cos(a0) * r0, c0[1] + np.sin(a0) * r0], axis=1),
                      np.stack([c1[0] + np.cos(a1) * r1, c1[1] + np.sin(a1) * r1], axis=1)])


# --------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------
def figure(F: Frame, x: float, y: float, h: float, P: Pose, skin="child", face: int = 1, seed: int = 0,
           a: float = 1.0, grab: dict | None = None, draw: float = 1.0, t: float | None = None, rim=None) -> dict:
    """Draw a figure on the world ground point (x, y) with world standing height h.

    skin: "child" | "friend" (the night or day skin follows F.skin) or a Skin. face: +1 looks right, -1 left.
    grab: {'f': (X, Y)} / {'b': ...} pins a hand to a world point (holding hands, an armrest).
    draw: 0..1, the figure draws itself on (limbs first, then garment, head, face; a lying figure: the
    back first, then limb after limb, the zigzag, head, face). a: pressure.
    t: the clock of the idle sway of hair and scarf (default F.tb, which stands still in the silences).
    rim: (colour, side) or (colour, side, strength): light on one side (side +1 from the right, -1 from
    the left, or a direction (dx, dy) with y down).
    Returns world joints (see pose_joints).
    """
    tb = F.tb if t is None else t
    if isinstance(skin, str):
        skin = SKINS[skin][1 if F.day else 0]
    face = 1 if face >= 0 else -1
    rot = P["rot"]
    cr, sr = math.cos(rot), math.sin(rot)
    fh = face * h
    if grab:
        for which, pt in grab.items():
            bx, by = (pt[0] - x) / fh, (y - pt[1]) / h
            P = aim_hand(P, which, (bx * cr - by * sr, bx * sr + by * cr))
    J = solve(P)
    ct, st, se = J["ct"], J["st"], J["se"]
    lie = _lie_w(P)                                # 0 upright .. 1 lying: the lying construction

    def S(p):
        return np.array([x + fh * (p[0] * cr + p[1] * sr), y - h * (-p[0] * sr + p[1] * cr)])

    def SS(arr):
        arr = np.asarray(arr)
        return np.stack([x + fh * (arr[:, 0] * cr + arr[:, 1] * sr), y - h * (-arr[:, 0] * sr + arr[:, 1] * cr)], axis=1)

    cam, c = F.cam, F.c
    z = cam.zoom
    hs = h * z                                     # height on screen: decides the level of detail
    soft = skin.soft
    lw, ow = 0.0245 * h, (0.017 - 0.0045 * soft) * h        # limb and outline widths (floors 1.9 and 1.5 px: they fade below)
    wob = min(1.15, max(0.16, hs / 300.0)) * 0.85 / z
    big = ramp(hs, 130.0, 170.0)                   # 0..1: close enough for the inner hatching
    mid = ramp(hs, 96.0, 124.0)                    # 0..1: mitts, coloured limbs, hair strokes
    step = 6.0 if hs >= 150 else 3.0
    kn = skin.knock
    kl = kn if skin.halo else None                 # rub-out behind limbs
    line, grain = skin.line, skin.grain
    edge = skin.edge * ramp(hs, 84.0, 130.0)       # a far figure is drawn with a plain thin line
    if hs < 96.0:
        kl = None
    la = a * (1.0 - 0.20 * soft)                   # pressure of the outline
    out = {k: S(J[k]) for k in _JOINTS}
    R = R_HEAD * h
    Rs = R * z
    out["R"] = R
    friend = skin.kind == "friend"
    sd0 = seed * 97

    d_limb = min(1.0, draw / 0.45)
    d_seq = d_tone = None                          # lying and being drawn on: the limbs' share of `draw` (they come one by one)
    if lie > 0.0 and draw < 1.0:                   # lying: the back is drawn first (see the garment), then the limbs
        d_limb = min(1.0, max(0.0, (draw - 0.17 * lie) / (0.45 - 0.14 * lie)))
        d_seq = d_limb

    def d_sub(d, a_, b_):
        """Lying and being drawn on: the progress of a part that is drawn from a_ to b_ of d."""
        return d + (min(1.0, max(0.0, (d - a_) / (b_ - a_))) - d) * lie

    d_garm = min(1.0, max(0.0, (draw - 0.3) / 0.35))
    d_head = min(1.0, max(0.0, (draw - 0.5) / 0.3))
    d_face = min(1.0, max(0.0, (draw - 0.86) / 0.14))
    d_hair = ramp(d_head, 0.5, 1.0)

    # the two sides keep their hand (seed) whichever way the figure is mirrored
    sdk = {"f": (7, 8, 5, 6), "b": (1, 2, 3, 4)} if face > 0 else {"b": (7, 8, 5, 6), "f": (1, 2, 3, 4)}
    near = J["near"]
    far = "b" if near == "f" else "f"
    flat_ = min(1.0, abs(se))                      # 0 profile .. 1 seen from the front or the back
    dimf = 0.86 + 0.14 * flat_                     # the far limbs are a little fainter in a profile
    ovf = ramp(flat_, 0.64, 0.80)                  # from the front both arms lie over the garment (turn about 0.42 to 0.52)

    rimc = None
    if rim is not None:
        rcol, rdir = rim[0], rim[1]
        rstr = float(rim[2]) if len(rim) > 2 else 1.0
        if isinstance(rdir, (int, float)):
            rdir = (float(rdir), -0.25)
        rn = math.hypot(rdir[0], rdir[1]) + 1e-9
        rimc = (rcol, np.array([rdir[0] / rn, rdir[1] / rn]), rstr)

    def curve(p0, pj, p1):
        a_, j_, b_ = S(p0), S(pj), S(p1)
        # a soft joint: the corner is rounded, like an arm drawn in one go
        m0, m1 = a_ + (j_ - a_) * 0.72, j_ + (b_ - j_) * 0.28
        return spline(np.array([a_, m0, j_ * 0.5 + (m0 + m1) * 0.25, m1, b_]), 14)

    def limb(cur, sd, dim, core, al=1.0, lw=lw, ck=0.62):
        al = al * dim
        if core is None or mid <= 0.0:
            chalk(F, cur, line if core is None else mix(line, core, 0.35), lw, a * al, sd0 + sd, wob, taper=0.72,
                  under=kl if al >= 0.85 else None,
                  edge=edge, step=step, draw=d_limb, grain=grain, floor=1.9)
        else:
            # a coloured limb: the pencil contour first, the pastel over its middle
            chalk(F, cur, line, lw * 1.06, la * al, sd0 + sd, wob, taper=0.72, edge=edge, step=step, draw=d_limb,
                  grain=grain, floor=1.9)
            chalk(F, cur, core, lw * ck, a * al * mid, sd0 + sd + 300, wob, taper=0.7, edge=0.0, step=step, draw=d_limb,
                  grain="dense", floor=1.0, var=0.12)
        if rimc is not None and d_limb >= 1.0:
            off = rimc[1] * (lw * 0.42)
            chalk(F, cur + off, rimc[0], lw * 0.5, a * al * al * 0.7 * rimc[2], sd0 + sd + 600, wob, taper=0.5, edge=0.15,
                  step=step, grain=grain, floor=1.2)

    def foot(w, dim):
        sd = sdk[w][3]
        heel, toe = S(J["heel_" + w]), S(J["toe_" + w])
        up_ = S(J["an_" + w]) - (heel + toe) / 2
        cur = np.array([heel, (heel + toe) / 2 + up_ * 0.25, toe])
        chalk(F, cur, line if skin.shoe is None else skin.shoe, lw * 1.28, a * dim, sd0 + sd, wob * 0.5, taper=0.8,
              under=kl, edge=edge, step=step, draw=d_limb, grain=grain, floor=2.4)

    def mitt(w, dim, al=1.0):
        if d_limb < 1.0:
            return
        sd = sdk[w][1]
        q, e = S(J["ha_" + w]), S(J["el_" + w])
        solid = al >= 0.85                       # a copy that is fading in over its other layer rubs nothing out (no grey hand)
        ko = kl is not None and solid
        al = a * al * dim
        col = line if skin.hand is None else skin.hand
        if mid <= 0.0:
            if ko:
                disc(F, q[0], q[1], 0.0225 * h * 1.5, kn, 0.9 * al, None, floor=1.95)
            disc(F, q[0], q[1], 0.0225 * h, col, al, grain, floor=1.3)
            return
        d = q - e
        n = math.hypot(d[0], d[1])
        d = d / n if n > 1e-6 * h else np.array([0.0, 1.0])
        c0 = q + d * (0.012 * h)
        ang = math.atan2(d[1], d[0])
        nr = np.array([d[1], -d[0]])
        if nr[0] * face - 0.3 * nr[1] < 0.0:        # the thumb: on the forward, upper side
            nr = -nr
        th = q + nr * (0.021 * h) - d * (0.002 * h)
        if ko:
            fill(F, blob(c0[0], c0[1], 0.041 * h, 0.033 * h, sd0 + sd, 0.04, 12, ang), kn, 0.9 * al)
        M = blob(c0[0], c0[1], 0.031 * h, 0.0235 * h, sd0 + sd, 0.07, 14, ang)
        if skin.hand is None:
            fill(F, M, col, al, grain)
            disc(F, th[0], th[1], 0.0115 * h, col, al, grain)
        else:
            if solid:
                fill(F, M, kn, 0.9 * al)
            fill(F, M, col, al, "dense")
            disc(F, th[0], th[1], 0.0115 * h, col, al, "dense")
            chalk(F, np.vstack([M, M[1:3]]), line, ow * 0.62, la * al * 0.85, sd0 + sd + 1, wob * 0.4, taper=0.7, edge=0.0,
                  step=3.0, grain=grain, floor=1.1)

    def arm(w, dim, al=1.0):
        nonlocal d_limb
        if al <= 0.003:
            return
        if d_seq is not None:                       # (drawn on: the far arm, then the near one, after the legs)
            d_limb = d_sub(d_seq, *_LIE_ON[2 if w == far else 3])
        if lie > 0.0:                               # lying: a fuller arm beside the body's mass (a sleeve, not a stick)
            limb(curve(J["sh_" + w], J["el_" + w], J["ha_" + w]), sdk[w][0], dim, skin.arm, al, lw * (1.0 + _LIE_ARM[0] * lie),
                 0.62 + _LIE_ARM[1] * lie)
        else:
            limb(curve(J["sh_" + w], J["el_" + w], J["ha_" + w]), sdk[w][0], dim, skin.arm, al)
        mitt(w, dim, al)

    def trouser(w, dim):
        """A lying figure's leg as a mass: shin and thigh as two tapering shapes, the thigh on top."""
        sd = sdk[w][2]
        k = lie ** 0.6
        r0, r1, r2, r3 = (max(r * h * k, lw * 0.5) for r in _LIE_LEG)
        hp_, kn_, an_ = S(J["hip_" + w]), S(J["kn_" + w]), S(J["an_" + w])
        on = ramp(lie, 0.0, 0.35)
        al = a * dim * on
        tc, ta, tg = (_LIE_TONE[0], _LIE_TONE[1], "dense") if skin.leg is None else (skin.leg, 0.86, "dense")
        if skin.leg is None and friend:              # (the friend's are of its own amber: never a cold tone on it)
            tc = mix(skin.garment, kn, 0.40)
        for j, (c0, q0, c1, q1) in enumerate(((an_, r3, kn_, r2), (hp_, r0, kn_, r1))):
            dj = d_limb if d_seq is None else d_sub(d_limb, (0.30, 0.0)[j], (0.80, 0.50)[j])     # (drawn on: the thigh, then the shin;
            df = ramp(dj, 0.2, 0.8) if d_seq is None else ramp(d_tone, 0.0, 1.0)                  # their tone is rubbed in after the line)
            fa = al * df
            M = _capsule(c0, q0, c1, q1)
            pth = F.path(M, True)
            c.drawPath(pth, F.paint(kn, 0.94 * fa * on * df, None))      # (coming on, the tone leads the rub-out: no pale ghost)
            c.drawPath(pth, F.paint(tc, ta * fa, tg))
            chalk(F, np.vstack([M, M[:3]]), line, ow * 0.92, la * al, sd0 + sd + 700 + j, wob * 0.8, taper=0.7,
                  edge=edge if w == near else 0.0, step=step, draw=dj, grain=grain, floor=1.5)

    def leg(w, dim):
        nonlocal d_limb, d_tone
        if d_seq is not None:                       # (drawn on: the far leg, then the near one; the foot closes each)
            w0, w1 = _LIE_ON[0 if w == far else 1]
            d_limb = d_sub(d_seq, w0, w1)
            d_tone = d_sub(d_seq, (w0 + w1) * 0.5, w1 + (w1 - w0) * 0.5)
        dl = d_limb
        if lie > 0.0:
            trouser(w, dim)
            k = 1.0 - ramp(lie, 0.10, 0.55)
            if k > 0.0:
                limb(curve(J["hip_" + w], J["kn_" + w], J["an_" + w]), sdk[w][2], dim, skin.leg, k)
        else:
            limb(curve(J["hip_" + w], J["kn_" + w], J["an_" + w]), sdk[w][2], dim, skin.leg)
        if d_seq is not None:
            d_limb = d_sub(dl, 0.75, 1.0)
        foot(w, dim)

    def legs():
        leg(far, dimf)
        leg(near, 1.0)

    # ---- far arm, legs ---------------------------------------------------------
    # (an arm that changes layer is drawn in the lower layer at full pressure and fades in in the upper one)
    if P["over"] <= 0.5 and ovf < 1.0:
        arm(far, dimf)
    if P["front"] <= 0.5:
        legs()

    # ---- the head's frame (needed by the scarf too) -----------------------------
    hc, nk = out["head"], out["neck"]
    ha, fw, dn, chh, shh, ly, ub, sg = _head_frame(P, J, face)
    sway, bob, hr = P["sway"], P["bob"], P["hair"]

    def scarf_tails(al):
        if al <= 0.003:
            return
        # two tails from the back of the neck: they hang, trail behind and wave a little
        base = nk + (hc - nk) * 0.16 + fw * (-0.30 * R * chh) + dn * (0.04 * R)
        for i, (ln_, ph, dy) in enumerate(((0.36, 0.0, 0.03), (0.27, 1.3, 0.09))):
            q = np.linspace(0.0, 1.0, 9)
            wav = np.sin(tb * 5.2 - q * 4.2 + ph + seed) * (0.010 + 0.020 * abs(sway)) * q
            bk = -face * (0.35 * chh + 0.95 * sway)                       # how far the tail trails toward -X
            k_ = min(1.0, abs(bk))
            xs = base[0] + h * ln_ * q * bk * (0.5 + 0.5 * q) + h * 0.05 * (i - 0.5) * q * abs(shh)
            ys = base[1] + h * (dy * q + wav + ln_ * q * (0.25 + 0.75 * q) * 0.66 * (1.0 - 0.75 * k_) - 0.10 * bob * q * q)
            chalk(F, np.stack([xs, ys], axis=1), skin.scarf, lw * 1.35, a * al * d_hair, sd0 + 20 + i, wob * 0.6,
                  taper=0.55, under=kn if al >= 1.0 else None, edge=edge, step=step, grain=grain, floor=2.5)

    tails_back = ramp(shh, 0.25, 0.6)              # from the front the tails hang behind the body
    if skin.scarf is not None and d_head > 0.0:
        scarf_tails(tails_back)

    # ---- garment ---------------------------------------------------------------
    (wb_p, wt_p), (wb_f, wt_f), hem = _GARMENT[skin.kind]
    fl2 = flat_ * flat_
    wb, wt = wb_p + (wb_f - wb_p) * fl2, wt_p + (wt_f - wt_p) * fl2
    sp = J["spine"]
    low = sp[0] - J["tan0"] * hem
    core = np.vstack([low, sp])
    uu = np.linspace(0.0, 1.0, len(core))
    d = np.gradient(core, axis=0)
    ln = np.hypot(d[:, 0], d[:, 1])
    if float(ln.min()) < 1e-6:
        d, ln = np.tile(J["tan0"], (len(core), 1)), np.ones(len(core))
    nrm = np.stack([d[:, 1] / ln, -d[:, 0] / ln], axis=1)          # forward side
    half = (wb + (wt - wb) * uu ** 0.85) * (1.0 - 0.36 * np.clip((uu - 0.80) / 0.20, 0.0, 1.0) ** 2)
    half = half * (1.0 + 0.055 * P["chest"] * np.exp(-((uu - 0.62) / 0.26) ** 2))
    fr, bk = core + nrm * half[:, None], core - nrm * half[:, None]
    if friend:                                      # the hem of the coat swings behind
        sh_ = np.array([-(0.05 * sway), 0.02 * bob])
        fr[0], bk[0] = fr[0] + sh_, bk[0] + sh_
        fr[1], bk[1] = fr[1] + sh_ * 0.4, bk[1] + sh_ * 0.4
    top = sp[-1] + J["tan1"] * 0.012
    hemc = (fr[0] + bk[0]) / 2 - J["tan0"] * 0.012
    gpoly = SS(np.vstack([bk, top[None, :], fr[::-1], hemc[None, :]]))
    d_out = d_garm
    if lie > 0.0:                                   # lying: one rounded shape laid on the surface, the back standing out
        bk, fr, top, hemc, g_up = _lie_torso(lie, core, nrm, bk, fr, top, hemc, J["tan0"], cr, sr,
                                             1.0 + 0.055 * P["chest"] * np.exp(-((uu - 0.62) / 0.26) ** 2), P["chest"])
        gpoly = np.vstack([bk, top[None, :], fr[::-1], hemc[None, :]])
        out["back"] = _back_of(SS(gpoly), h)
        gpoly = SS(_round(gpoly, lie * 3.0))
        d_out = d_garm + (min(1.0, draw / 0.22) - d_garm) * lie          # the back is drawn first, as one line
    else:
        out["back"] = _back_of(gpoly, h)
    if d_out > 0.0 and d_garm <= 0.0:
        chalk(F, np.vstack([gpoly, gpoly[:2]]), line, ow, la * 0.95, sd0 + 13, wob, taper=0.7, edge=edge,
              step=step, draw=d_out, grain=grain, floor=1.5)
    if d_garm > 0.0:
        # a paling figure still hides what is behind it (see the head); a lying one is drawn on without a pop
        fill(F, gpoly, kn, 0.94 * min(1.0, 2.6 * a) * (min(1.0, d_garm / 0.3) if lie > 0.0 else 1.0))
        far_ = 1.0 - ramp(hs, 84.0, 140.0)           # a far figure: the garment is one rubbed tone, hardly a zigzag
        fill(F, gpoly, mix(skin.garment, skin.garment2, 0.30 * far_), min(1.0, 0.50 + 0.22 * soft + 0.40 * far_) * a * d_garm,
             "mid" if far_ < 0.5 else "dense")
        gap = 0.034 * h                              # under 3 px on screen the zigzag closes up into tone
        gang = -face * (HALF_PI + 0.62 * ct - rot)
        lz = ramp(lie, 0.0, 0.4)                    # lying: the zigzag follows the curve of the back
        for g_, k_ in (("dense", big), ("mid", 1.0 - big)):
            ha_ = a * (0.95 - 0.25 * soft) * k_ * (1.0 - 0.7 * far_)
            if lz < 1.0:
                hatch(F, gpoly, skin.garment2, gang, gap, gap * 0.56, ha_ * (1.0 - lz), sd0 + 11,
                      grain=g_, wob=wob, draw=d_garm, over=0.22)
            if lz > 0.0:
                _lie_hatch(F, SS(bk if g_up > 0.0 else fr), SS(fr if g_up > 0.0 else bk), gpoly, skin.garment2, gap, gap * 0.56,
                           ha_ * lz, sd0 + 11, g_, wob, d_garm)
        chalk(F, np.vstack([gpoly, gpoly[:2]]), line, ow, la * 0.95, sd0 + 13, wob, taper=0.7, edge=edge,
              step=step, draw=d_out, grain=grain, floor=1.5)
        if rimc is not None:
            side_pts = fr if (rimc[1][0] * face * cr >= 0.0) else bk
            if lie > 0.5:                           # lying: the side that is turned to the light as it is seen
                side_pts = fr if float((SS(fr[1:-1]).mean(0) - SS(bk[1:-1]).mean(0)) @ rimc[1]) >= 0.0 else bk
            rp = SS(side_pts[1:-1]) + rimc[1] * (ow * 0.5)
            chalk(F, rp, rimc[0], ow * 1.25, a * 0.9 * rimc[2], sd0 + 14, wob, taper=0.3, edge=0.2, step=step,
                  grain=grain, floor=1.4)
    if P["front"] > 0.5:
        legs()
    if P["over"] <= 0.5 and ovf > 0.0:
        arm(far, dimf, ovf)
        arm(near, 1.0)                              # seen from the front or the back the arms hang under the head

    # ---- scarf (friend) --------------------------------------------------------
    if skin.scarf is not None and d_head > 0.0:
        scarf_tails(1.0 - tails_back)
        if mid > 0.0:                                # the band round the neck
            b0 = nk + (hc - nk) * 0.10
            wv = fw * (0.062 * h * (0.75 + 0.25 * flat_))
            chalk(F, np.array([b0 - wv, b0 + dn * (0.012 * h), b0 + wv]), skin.scarf, lw * 1.5, a * mid * d_hair, sd0 + 22, wob * 0.5,
                  taper=0.7, edge=edge, step=step, grain=grain, floor=2.0)

    # ---- head ----------------------------------------------------------------
    lx = P["look"][0]
    fdx = sg * (0.58 * lx * abs(chh) + 2.7 * ub)   # the face disc slides forward and off the head as it turns away
    ftx = sg * (0.40 * lx * abs(chh) + 2.0 * ub)
    fvis = 1.0 - ramp(ub, 0.15, 0.5)
    hp = blob(hc[0], hc[1], R * 1.03, R * 0.975, sd0 + 31, rough=0.022, n=34, rot=face * ha)
    press = P["press"]
    if press > 0.0:                                  # a weight on the crown: the top of the head gives
        q = hp - hc
        u_, v_ = q @ fw, q @ dn
        top_ = v_ < 0.0
        v_ = np.where(top_, v_ * (1.0 - 0.17 * press), v_)
        u_ = u_ * (1.0 + 0.05 * press * np.clip(-v_ / R + 0.3, 0.0, 1.0))
        hp = hc + np.outer(u_, fw) + np.outer(v_, dn)
    fr_ = R * (0.90 if friend else 1.0)
    fc = hc + fw * (fdx * R) + dn * ((0.44 - ly * 0.72 + (0.14 if friend else 0.0)) * R)
    hl = skin.hair_line
    tcol = hl if not soft else mix(skin.hair, hl, 0.35)      # chalk strands at night, the hair's own pastel by day

    def L(px_, py_):
        return hc + fw * px_ + dn * py_

    def strand(P_, w_, al, sd, floor=1.8, col=None):
        """A lock of hair: one pressed stroke of the chalk's side, pointed at the tip (a filled leaf, far
        cheaper than a line; its tip boils on twos)."""
        ws = w_ * z
        if ws < floor:
            al, w_ = al * ws / floor, floor / z
        n = len(P_)
        jit = (0.5 / z) * min(1.0, hs / 200.0)
        P_ = P_ + _LEAF_U[n][:, None] * np.array([rsym(sd + F.k * 7919, 1), rsym(sd + F.k * 7919, 2)]) * jit
        d = np.gradient(P_, axis=0)
        ln = np.hypot(d[:, 0], d[:, 1]) + 1e-9
        nr = np.stack([-d[:, 1] / ln, d[:, 0] / ln], axis=1) * (_LEAF_W[n] * (0.56 * w_))[:, None]
        poly = np.vstack([P_ + nr, (P_ - nr)[::-1]])
        col = tcol if col is None else col
        al = al * d_hair
        if hs >= 150.0 and edge > 0.0:
            fill(F, np.vstack([P_ + nr * 1.7, (P_ - nr * 1.7)[::-1]]), col, al * edge, "sparse")
        fill(F, poly, col, al, grain)

    def tufts(which):
        """The tufts of the crown: which = 0 those behind the head, 1 those on our side and on the rim."""
        for i, (az, pol, ln_) in enumerate(_TUFTS_FRIEND if friend else _TUFTS_CHILD):
            if hs < 110.0 and i >= (0 if friend else 3):
                continue
            sp_, cp_ = math.sin(pol), math.cos(pol)
            bx, bz = sp_ * math.cos(az), sp_ * math.sin(az)
            X, dep = bx * chh - bz * shh, bx * shh + bz * chh       # across the head, toward us
            if (dep >= -0.2) != bool(which):
                continue
            rj = rnd(seed * 13 + i, 4)
            ln2 = R * ln_ * (0.8 + 0.4 * rj) * (0.72 + 0.48 * hr)
            # it stands on the rim of the head where the crown shows it, and grows outward from the skull;
            # drooping hair falls, glad hair stands up
            o = np.array([X, cp_])
            o = o / (math.hypot(o[0], o[1]) + 1e-9)
            wig = 0.10 * math.sin(tb * 2.2 + i * 1.7) * ramp(hr, 0.5, 0.8) + 0.30 * rsym(seed * 13 + i, 5)
            g = _fwd(np.array([o[0], o[1] + 0.35 * hr]), wig)
            g = g / (math.hypot(g[0], g[1]) + 1e-9)
            b0 = L(o[0] * R * 0.93, -o[1] * R * 0.93)
            tip = L(o[0] * R * 0.93 + g[0] * ln2, -(o[1] * R * 0.93 + g[1] * ln2))
            tip = tip + np.array([-face * sway * ln2 * 0.9, (1.0 - hr) * ln2 * 0.80 - bob * ln2 * 0.6])
            v_ = tip - b0                                # blown or drooping, a lock keeps its length
            tip = b0 + v_ * (ln2 * (1.0 + 0.12 * min(1.0, abs(sway))) / (math.hypot(v_[0], v_[1]) + 1e-9))
            mid_ = (b0 + tip) / 2 + (fw * g[0] - dn * g[1]) * (ln2 * 0.22)
            strand(spline(np.array([b0 - (b0 - hc) * 0.22, mid_, tip]), 8), ow * (1.3 if friend else 1.55), a,
                   sd0 + 50 + i, floor=1.8 if friend else 2.8)

    def ponytail():
        # at the back of the head: it sticks out behind a profile, hangs down the middle of a back view
        base = L(-0.86 * chh * R, -0.34 * R)
        for i, (dl, da) in enumerate(((1.0, 0.0), (0.8, 0.5), (0.72, -0.45))):
            if i and hs < 110.0:
                break
            bkx = -(0.50 * chh + da * 0.42 * (abs(chh) + 0.5 * abs(shh)))
            tip = base + fw * (bkx * R * dl) + np.array([-face * 0.75 * sway * R * dl, 0.0]) \
                + np.array([0.0, (0.66 - 0.4 * abs(sway) - da * 0.30 * abs(chh) - 0.5 * bob) * R * dl])
            tip = tip + np.array([math.sin(tb * 4.0 + i) * R * 0.05, 0.0])
            mid_ = (base + tip) / 2 + fw * (-0.10 * R * chh) + np.array([0.0, -R * 0.16 * dl])
            strand(spline(np.array([base, mid_, tip]), 10), ow * 1.9, a, sd0 + 40 + i, floor=2.8)

    if P["over"] < -0.5 and ovf < 1.0:              # over = -1: the near arm too is raised BEHIND the head (the face stays free)
        arm(near, 1.0, 1.0 - ovf)
    if d_head > 0.0:
        hpath = F.path(hp, True)
        tufts(0)
        if friend and shh > 0.15:                    # seen from the front the ponytail is behind the head
            ponytail()
        hk = ramp(d_head, 0.4, 0.85) if lie > 0.0 else 1.0         # (a lying figure is drawn on in the film's first seconds: the line, then the tone)
        c.drawPath(hpath, F.paint(kn, 0.96 * min(1.0, 2.6 * a) * hk, None))    # (its own garment must not show through its head)
        c.drawPath(hpath, F.paint(skin.face, 0.92 * a * hk, None))
        k_ = ramp(Rs, 30.0, 38.0)
        if k_ > 0.0 and fvis > 0.0:
            hatch(F, hp, skin.face2, face * (0.6 + ha), R * 0.22, R * 0.13, 0.42 * a * k_ * hk, sd0 + 32, grain="sparse",
                  wob=wob, clip=True, draw=d_head)
        # hair cap: the head disc minus the face disc
        fsx, fsy = cam.to_screen(fc[0], fc[1])
        fp = skia.Path()
        fp.addCircle(float(fsx), float(fsy), float(fr_ * z))
        c.save()
        c.clipPath(hpath, skia.ClipOp.kIntersect, True)
        c.clipPath(fp, skia.ClipOp.kDifference, True)
        c.drawPath(hpath, F.paint(skin.hair, 0.96 * a * hk, "dense"))
        if big > 0.0:
            hatch(F, hp, hl, face * (1.2 + ha), R * 0.17, R * 0.08, (0.6 - 0.2 * soft) * a * big * hk, sd0 + 33, grain="mid",
                  wob=wob * 0.6)
        c.restore()
        if rimc is not None:
            c.save()
            c.clipPath(hpath, skia.ClipOp.kIntersect, True)
            q = hc + rimc[1] * (R * 0.95)
            smudge(F, q[0], q[1], R * 0.85, R * 1.1, rimc[0], 0.42 * a * rimc[2], "soft", power=1.3)
            c.restore()
        # outline
        chalk(F, np.vstack([hp, hp[1:4]]), line, ow, la, sd0 + 34, wob * 0.7, taper=0.75, edge=edge,
              step=step, draw=d_head, grain=grain, floor=1.5)
        if rimc is not None:
            an = math.atan2(rimc[1][1], rimc[1][0]) + np.linspace(-1.05, 1.05, 14)
            rp = np.stack([hc[0] + np.cos(an) * R * 1.05, hc[1] + np.sin(an) * R * 1.0], axis=1)
            chalk(F, rp, rimc[0], ow * 1.3, a * 0.95 * rimc[2], sd0 + 35, wob * 0.5, taper=0.2, edge=0.25, step=step,
                  grain=grain, floor=1.5)
        tufts(1)
        if friend and shh <= 0.15:
            ponytail()
        if not friend and big > 0.0 and fvis > 0.0:
            # a ragged fringe over the forehead
            for i, o in enumerate((-0.45, 0.0, 0.42)):
                b0 = fc + (fw * math.sin(o * 0.9) - dn * math.cos(o * 0.9)) * fr_
                fl_ = min(0.20 + 0.12 * rnd(seed * 17 + i, 6), 0.60 * max(0.1, 0.50 + 0.38 * ly))     # never into the eyes
                tip = b0 + dn * R * fl_ + fw * R * 0.10 * rsym(seed * 17 + i, 7)
                strand(spline(np.array([b0 - dn * R * 0.06, (b0 + tip) / 2 + fw * R * 0.02, tip]), 8), ow * 1.9, a * big * fvis,
                       sd0 + 58 + i, col=skin.hair)

    # ---- face ----------------------------------------------------------------
    if d_face > 0.0 and fvis > 0.0:
        _face(F, P, skin, L, hc, R, Rs, a * fvis * d_face, seed, wob, ftx, ly, lx * chh, hpath if ub > 0.0 else None, fp, face, fw, dn)

    # ---- near arm --------------------------------------------------------------
    if P["over"] > 0.5:
        arm(far, 0.9 + 0.1 * flat_)
        arm(near, 1.0)
    elif ovf < 1.0 and P["over"] >= -0.5:
        arm(near, 1.0, 1.0 - ovf)
    return _extras(out, P, J, face)


_EX = np.linspace(-1.6, 1.6, 25)        # eye outlines are sampled this wide (in eye radii): room for the gaze
_LEAF_U = {n: np.linspace(0.0, 1.0, n) ** 1.5 for n in (3, 8, 10)}
_LEAF_W = {n: (1.0 - np.linspace(0.0, 1.0, n)) ** 0.85 * np.minimum(1.0, np.linspace(0.0, 1.0, n) / 0.16 + 0.35) for n in (3, 8, 10)}


def _face(F, P, skin, L, hc, R, Rs, af, seed, wob, ftx, ly, lxe, hpath, fpath, face, fw, dn):
    """The features, in the head's frame: L(px, py) maps (toward the face side, down) to the world."""
    c = F.c
    fcol = skin.feature
    sd0 = seed * 97
    cx_ = ftx * R
    cy_ = (0.10 - ly * 0.34) * R
    sep = 0.37 * R * (1.0 - 0.42 * min(1.0, abs(lxe)))
    fw_ = 0.085 * R                              # feature line width (floor 1.2 px)
    full = ramp(Rs, 12.5, 14.5)                  # under about 13 px of head radius: two dots only
    fine = ramp(Rs, 24.0, 32.0)                  # lids, bags, brows, the spark
    eye = max(0.0, P["eye"])
    joy, brow, lift, lid = P["joy"], P["brow"], P["lift"], P["lid"]
    blink = min(1.0, max(0.0, P["blink"]))
    gx, gy = P["gaze"]
    opn = min(1.0, eye) * (1.0 - blink) * (1.0 - ramp(joy, 0.55, 1.0))     # how far the upper lid is open
    er = 0.125 * R * (1.0 + (0.42 * (eye - 1.0) / 0.3 if eye > 1.0 else 0.0))
    clipped = hpath is not None
    if clipped:                                    # a face turning away: it leaves over the edge of the head
        c.save()
        c.clipPath(hpath, skia.ClipOp.kIntersect, True)
        c.clipPath(fpath, skia.ClipOp.kIntersect, True)

    def feat(pts, w_, a_, sd, wob_=0.0, taper=0.6, n=8):
        chalk(F, spline(np.array(pts), n) if len(pts) > 2 and n else np.array(pts), fcol, w_, a_, sd, wob_,
              taper=taper, edge=0.0, step=3.0, floor=1.2)

    bl = min(1.0, P["blush"] + skin.blush0)
    k_ = ramp(Rs, 14.0, 18.0)
    if skin.blush is not None and bl > 0.02 and k_ > 0.0:
        for sgn in (-1, 1):
            q = L(cx_ + sgn * sep * 1.42, cy_ + 0.31 * R)
            smudge(F, q[0], q[1], R * 0.27, R * 0.19, skin.blush, min(1.0, 0.62 * bl) * af * k_, "mid", power=1.3)

    for sgn in (-1, 1):
        e0x, e0y = cx_ + sgn * sep, cy_
        if full < 1.0:
            q = L(e0x, e0y)
            disc(F, q[0], q[1], 0.125 * R * (0.7 + 0.3 * min(1.0, eye)), fcol, af * (1.0 - full), None, floor=0.95)
        if full <= 0.0:
            continue
        a_ = af * full
        sd = sd0 + 60 + sgn
        xs = _EX * er
        xn = _EX / 1.3
        # the line where the lids meet: a sleeping curve, or the arc of a smile
        y_sleep = er * (0.52 - 0.72 * xn * xn)
        y_joy = er * (-0.62 + 1.10 * xn * xn)
        yc = y_sleep + (y_joy - y_sleep) * joy
        droop = lid * 0.30 * er * (xn * sgn) * (1.0 - joy)                 # the outer end hangs
        y_up = -1.30 * er + (0.45 * er) * lid * (1.0 - 0.5 * joy) + droop
        yu = y_up + (yc - y_up) * (1.0 - opn)
        yl = 1.3 * er + (y_joy + 0.10 * er - 1.3 * er) * min(1.0, joy * 1.15)
        px_, py_ = gx * 0.55 * er, -gy * 0.45 * er                          # the pupil in its socket
        circ = np.sqrt(np.maximum(0.0, er * er - (xs - px_) ** 2))
        top = np.maximum(py_ - circ, yu)
        bot = np.minimum(py_ + circ, yl)
        m = (bot - top) > 0.06 * er
        if float(yu.max()) <= py_ - er and float(yl.min()) >= py_ + er:        # nothing cuts it: a plain dot
            q = L(e0x + px_, e0y + py_)
            fill(F, blob(q[0], q[1], er * 0.98, er * 1.06, seed * 7 + sgn, 0.05, 14), fcol, a_)
        elif m.sum() >= 2:
            ii = np.nonzero(m)[0]
            poly = np.vstack([np.stack([xs[ii], top[ii]], axis=1), np.stack([xs[ii], bot[ii]], axis=1)[::-1]])
            fill(F, np.array([L(e0x + p[0], e0y + p[1]) for p in poly]), fcol, a_)
        sp_ = P["spark"] * fine
        if sp_ > 0.02 and m.sum() >= 4:
            q = L(e0x + px_ + er * 0.28, e0y + max(py_ - er * 0.34, float(top[12]) + er * 0.26))
            disc(F, q[0], q[1], er * 0.27, skin.face2, a_ * sp_, None, floor=0.9)
        # the upper lid: drawn when it is heavy or when it comes down
        la_ = max(lid * 0.9, ramp(1.0 - opn, 0.12, 0.45))
        if fine <= 0.0:
            la_ = 1.0 if opn < 0.3 else 0.0
        if la_ > 0.03:
            pts = [L(e0x + xs[i], e0y + min(yu[i], yl[i])) for i in (4, 8, 12, 16, 20)]
            feat(pts, fw_ * (0.80 + 0.2 * la_), a_ * la_, sd, wob * 0.2, 0.65)
        # the lower lid of a smile
        if joy > 0.08 and fine > 0.0 and opn > 0.12:
            pts = [L(e0x + xs[i], e0y + yl[i]) for i in (6, 12, 18)]
            feat(pts, fw_ * 0.7, a_ * fine * ramp(joy, 0.08, 0.4), sd + 4, wob * 0.2, 0.6)
        # bags under tired eyes
        if lid > 0.1 and fine > 0.0:
            scrib(F, spline(np.array([L(e0x - er * 1.0, e0y + er * 1.55), L(e0x, e0y + er * 1.92),
                                      L(e0x + er * 1.0, e0y + er * 1.55)]), 6), fcol, fw_ * 0.55,
                  a_ * 0.5 * lid * (1.0 - 0.7 * joy) * fine, None)
        # brows: the inner end rises when worried, the whole brow when surprised
        kb = max(brow, lift)
        if kb > 0.12 and fine > 0.0:
            base = e0y - er * (2.05 + 0.85 * lift + (0.42 * (eye - 1.0) / 0.3 if eye > 1.0 else 0.0))
            inner = L(e0x - sgn * er * 1.15, base - brow * er * 0.95)
            outer = L(e0x + sgn * er * 1.45, base + brow * er * 0.45)
            midp = (inner + outer) / 2 - dn * (lift * er * 0.30)
            feat([inner, midp, outer], fw_ * 0.8, a_ * 0.9 * fine * ramp(kb, 0.12, 0.4), sd0 + 66 + sgn, 0.0, 0.5, 6)
    if full > 0.0:
        a_ = af * full
        mo, mop = P["mouth"], min(1.0, max(0.0, P["mopen"]))
        mx, my = cx_, cy_ + 0.47 * R
        am = min(1.0, abs(mo))
        mw = R * (0.165 + 0.07 * am + 0.07 * max(0.0, mo - 1.0)) * (1.0 - 0.34 * mop * (1.0 - am))
        xn = np.linspace(-1.0, 1.0, 11)
        bow = 1.0 - xn * xn
        ye = -0.07 * mo * R                                        # the corners of the mouth
        yy = ye + mo * R * 0.155 * bow                             # the line of the lips
        if mop > 0.06:
            rnd_ = np.sqrt(bow)
            po = max(0.0, min(1.0, mo))
            yu = ye + mo * R * 0.155 * (1.0 - 0.72 * mop) * bow - mop * R * 0.085 * (1.0 - am) * rnd_
            yl = ye + (max(0.0, mo) * R * 0.155 * bow) * (1.0 - mop) + mop * R * (0.13 + 0.10 * po) * rnd_ \
                + min(0.0, mo) * R * 0.05 * bow
            yl = np.maximum(yl, yu)
            poly = np.vstack([np.stack([xn * mw, yu], axis=1), np.stack([xn * mw, yl], axis=1)[::-1]])
            fill(F, np.array([L(mx + p[0], my + p[1]) for p in poly]), fcol, a_)
            yy = yu
        feat([L(mx + xn[i] * mw, my + yy[i]) for i in (0, 2, 5, 8, 10)], fw_ * 0.9, a_, sd0 + 68, wob * 0.2)
    if clipped:
        c.restore()


# --------------------------------------------------------------------------
# pose library (ground point: under the feet when standing, under the pelvis on the surface it sits or lies on)
# --------------------------------------------------------------------------
_TIRED = dict(eye=0.55, lid=1.0, brow=0.55, mouth=-0.35, hair=0.08)       # the child's resting face

STAND = Pose()
FRONT = Pose(turn=1.0, look=(0.0, 0.0), hf=(0.0, -0.31), hb=(0.0, -0.31), hfz=0.035, hbz=0.035, ff=(0.0, 0.0),
             fb=(0.0, 0.0), ffz=0.012, fbz=0.012)
BACK_STAND = Pose(turn=-1.0, pel=(0.0, 0.398), lean=0.05, bend=0.25, neck=0.2, hf=(0.0, -0.315), hb=(0.0, -0.315),
                  hfz=0.03, hbz=0.03, ff=(0.0, 0.0), fb=(0.0, 0.0), ffz=0.01, fbz=0.01, hair=0.1, **{k: v for k, v in _TIRED.items() if k != "hair"})
STOPPED = Pose(pel=(0.0, 0.395), lean=0.12, bend=0.45, neck=0.30, look=(0.30, -0.70), hf=(0.035, -0.325),
               hb=(0.02, -0.325), ff=(-0.02, 0.0), fb=(0.015, 0.0), open=0.5, **_TIRED)
LOOK_UP = Pose(pel=(0.0, 0.412), lean=-0.06, bend=-0.20, neck=-0.32, look=(0.42, 0.80), eye=1.2, lid=0.35, lift=0.7,
               brow=0.2, mouth=0.1, mopen=0.4, hf=(0.03, -0.31), hb=(0.07, -0.29), ff=(-0.02, 0.0), fb=(0.03, 0.0),
               hair=0.7, open=0.7)
REACH = Pose(pel=(0.03, 0.392), lean=0.24, bend=0.05, neck=-0.30, look=(0.62, 0.36), eye=1.1, lid=0.3, lift=0.4,
             mouth=0.2, hf=(0.30, 0.10), hb=(-0.06, -0.29), eb=1.0, ff=(0.10, 0.0), fb=(-0.10, 0.012), ab=-0.55,
             hair=0.72, open=0.45)
SIT_HUG = Pose(pel=(-0.06, 0.055), lean=0.38, bend=0.60, neck=0.30, look=(0.30, -0.62), hf=(0.215, -0.085),
               hb=(0.13, -0.11), ef=-1.0, eb=-1.0, ff=(0.165, 0.0), fb=(0.125, 0.0), open=0.35, front=1.0,
               **dict(_TIRED, hair=0.05, brow=0.7, mouth=-0.45))
SIT_LIFT = SIT_HUG.but(lean=0.20, bend=0.16, neck=-0.30, look=(0.45, 0.58), eye=1.2, lid=0.4, brow=0.12, lift=0.6,
                       mouth=0.1, mopen=0.4, hf=(0.245, -0.05), hb=(0.15, -0.10), hair=0.65)
JUMP = Pose(pel=(0.0, 0.60), lean=-0.06, bend=-0.2, neck=-0.25, look=(0.25, 0.3), eye=1.0, joy=1.0, mouth=1.0,
            mopen=0.7, blush=1.0, hf=(-0.17, 0.25), hb=(0.17, 0.27), ef=1.0, eb=-1.0, ff=(-0.15, 0.33), fb=(0.13, 0.36),
            kf=1.0, kb=1.0, af=-0.9, ab=-0.5, hair=1.0, open=1.0, bob=-0.3)
# hand in hand: the near hand held forward (pin it with grab={"f": point}); the free far hand is held a little
# behind the hip (hanging straight it would show under the hem between the legs)
HOLD = Pose(pel=(0.0, 0.412), lean=0.0, bend=-0.05, neck=-0.1, look=(0.45, 0.12), eye=1.0, joy=0.75, mouth=0.9,
            blush=0.8, hf=(0.19, -0.19), hb=(-0.17, -0.245), eb=-1.0, ff=(-0.02, 0.0), fb=(0.03, 0.0), hair=0.8, open=1.0)


def _laid(P: Pose, pel, lf=None, lb=None, **hands) -> Pose:
    """A pose laid out as it is SEEN, in body units from the ground point (x toward `face`, y up; the
    surface it lies on is y = 0): the pelvis at pel; lf / lb = (a1, a2): the near / far leg folded so
    that its thigh points a1 and its shin a2 (degrees; 0 = toward `face`, 90 = up: for figures that lie,
    whose limbs fold in the picture); ff / fb instead: the ankles; hf / hb: the hands. The angles of the
    legs as they then lie are noted in the pose (lgf, lgb: what a roll with lgw blends from and to)."""
    P = P.but(pel=tuple(_unrot(P, pel, True)))
    for which, ang in (("f", lf), ("b", lb)):
        if ang is not None:
            hp_ = _seen_pt(P, solve(P)["hip_" + which])
            q1, q2 = math.radians(ang[0]), math.radians(ang[1])
            P = aim_foot(P, which, (hp_[0] + THIGH * math.cos(q1) + SHIN * math.cos(q2),
                                    hp_[1] + THIGH * math.sin(q1) + SHIN * math.sin(q2)), True)
    P = _seen(P, **hands)
    J = solve(P)
    ang = []
    for which in ("f", "b"):
        h_, k_, a_ = (_seen_pt(P, J[n + which]) for n in ("hip_", "kn_", "an_"))
        ang.append((math.atan2(k_[1] - h_[1], k_[0] - h_[0]), math.atan2(a_[1] - k_[1], a_[0] - k_[0]) % (2.0 * math.pi)))
    return P.but(lgf=ang[0], lgb=ang[1])


def _seen_pt(P, p):
    c_, s_ = math.cos(P["rot"]), math.sin(P["rot"])
    return np.array([p[0] * c_ + p[1] * s_, -p[0] * s_ + p[1] * c_])


lay_pose = _laid                        # public: lay_pose(P, pel, lf=None, lb=None, hf=, hb=, ff=, fb=)


def curl_pose(tense: float = 1.0) -> Pose:
    """Curled up on its side, facing us, the head toward `face` (on the sofa: on the right armrest),
    the back rounded, the knees drawn up before the belly. tense = 1: asleep but clenched (the film's
    opening: a tight ball, the shoulders up, the head tucked in, a fist under the chin); tense = 0: at
    ease (the coda: the back longer and lower, the head lying back, a hand hanging off the seat).
    Ground point: on the seat, (CURL_X, SOFA_SEAT_Y); the hips lie 0.08 h to the left of it, the head
    0.27 h to its right. (Solves and aims, 0.6 ms: build it once, or blend CURL and CURL_EASE.)"""
    k = min(1.0, max(0.0, float(tense)))
    m = lambda a_, b_: b_ + (a_ - b_) * k          # (tense, at ease)
    P = Pose(turn=0.60, rot=m(1.08, 1.12), lean=0.0, bend=m(1.0, 0.55), neck=m(0.0, -0.12), tilt=m(0.12, 0.04),
             look=(0.10, m(-0.25, -0.12)), eye=0.0, lid=m(1.0, 0.3), brow=m(0.75, 0.0), mouth=m(-0.35, 0.3), blush=m(0.0, 0.3),
             ef=-1.0, eb=-1.0, kf=1.0, kb=1.0, af=m(-2.0, -2.15), ab=m(-2.0, -1.9), hair=m(0.0, 0.25), open=0.4, front=1.0)
    return _laid(P, (-0.077, m(0.084, 0.092)), (m(-7.0, -16.0), m(190.0, 186.0)), (m(4.0, -6.0), m(191.0, 181.0)),
                 hf=(m(0.125, 0.125), m(0.100, -0.040)), hb=(m(0.152, 0.235), m(0.078, 0.165)))


CURL = curl_pose(1.0)
CURL_EASE = curl_pose(0.0)
ASLEEP = CURL
# lying, awake, propped a little, the head lifted, both hands clutching the top of the armrest under its chin, hair on end
CLING = _laid(CURL.but(rot=0.97, bend=0.72, neck=-0.50, tilt=-0.10, look=(0.2, 0.05), eye=0.5, lid=1.0, brow=0.8, mouth=-0.45,
                       hair=0.9, over=1.0),
              (-0.077, 0.084), (-7.0, 190.0), (4.0, 191.0), hf=(0.200, 0.150), hb=(0.243, 0.165))
# on its back, knees up, feet on the seat, a hand on the belly, looking up
LIE_UP = _laid(Pose(turn=2.0, rot=1.10, lean=0.0, bend=0.35, neck=-0.05, tilt=-0.05, look=(0.55, 0.15), gaze=(0.6, 0.1), eye=0.9,
                    lid=0.8, brow=0.4, mouth=-0.1, ef=-1.0, eb=-1.0, kf=1.0, kb=1.0, af=-1.0, ab=-1.0, hair=0.3, open=0.3, front=1.0),
               (-0.066, 0.100), (140.0, 268.0), (138.0, 262.0), hf=(-0.02, 0.17), hb=(-0.10, 0.04))
# lying, turned a little toward us, a hand (the phone) at the ear, smiling
LIE_PHONE = _laid(LIE_UP.but(turn=1.6, look=(0.2, 0.1), gaze=(0.0, 0.0), eye=1.0, lid=0.2, brow=0.0, lift=0.3, mouth=0.9, joy=0.45,
                             blush=0.7, hair=0.75, over=1.0, eb=1.0),
                  (-0.066, 0.100), (140.0, 268.0), (134.0, 262.0), hf=(-0.04, 0.10), hb=(0.375, 0.235))
# sitting on the seat, three-quarter to us, hugging its knees (ground point: on the seat under the hips)
SIT_SOFA = Pose(pel=(0.0, 0.058), turn=0.55, lean=0.22, bend=0.55, neck=0.25, look=(0.30, -0.5), hf=(0.24, -0.14),
                hb=(0.20, -0.17), ff=(0.19, 0.0), fb=(0.16, 0.0), open=0.4, front=1.0, **dict(_TIRED, hair=0.05))
# sitting on the front edge of the sofa, three-quarter to us, the feet dangling (ground point: on the
# FLOOR under the hips, so that it blends with the standing poses: the child slides off and stands; the
# hips are 0.366 up: on a seat 120 world units high for h = 380)
SIT_EDGE = Pose(pel=(-0.02, 0.366), turn=0.55, lean=0.10, bend=0.45, neck=0.22, look=(0.30, -0.45), hf=(0.07, -0.275),
                hb=(0.10, -0.265), ff=(0.20, 0.150), fb=(0.185, 0.162), af=-0.30, ab=-0.30, open=0.4, front=1.0, **_TIRED)
# sitting on the floor, legs folded, hands in the lap (ground point: on the floor under the hips)
SIT_FLOOR = Pose(pel=(0.0, 0.058), turn=0.25, lean=0.08, bend=0.45, neck=0.30, look=(0.30, -0.55), hf=(0.11, -0.27),
                 hb=(0.13, -0.26), ff=(0.20, 0.0), fb=(0.24, 0.0), kf=1.0, kb=1.0, open=0.5, front=1.0, **_TIRED)


# --------------------------------------------------------------------------
# between lying and upright: three moves as poses of w = 0..1 (space only: the timing is the animator's)
# --------------------------------------------------------------------------
def _tangents(x, Y):
    """Slopes of a smooth path through the rows of Y at the places x that never overshoots a key
    (monotone cubic): a value that is the same in two neighbouring keys stays put between them."""
    h = np.diff(x)
    d = np.diff(Y, axis=0) / h[:, None]
    m = np.zeros_like(Y)
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, len(x) - 1):
        a_, b_ = d[i - 1], d[i]
        ok = a_ * b_ > 0.0
        w1, w2 = 2.0 * h[i] + h[i - 1], h[i] + 2.0 * h[i - 1]
        m[i] = np.where(ok, (w1 + w2) / (w1 / np.where(ok, a_, 1.0) + w2 / np.where(ok, b_, 1.0)), 0.0)
    return m


_SEEN4 = ("an_f", "an_b", "ha_f", "ha_b")


class _Move:
    """A move through key poses, all on one ground point: move(w) is the pose at w = 0..1. Every number
    of the pose travels through the keys on a smooth path that does not overshoot them; ankles and
    hands travel on such paths as they are SEEN (so a hand planted in two neighbouring keys stays
    planted while the body turns over it); the two layer flags switch half-way between two keys."""

    def __init__(self, keys):
        self.x = np.array([k[0] for k in keys], dtype=np.float64)
        self.P = [k[1] for k in keys]
        self.V = np.array([[P[k] for k in _NUMS] + [c for k in _PAIRS for c in P[k]] for P in self.P])
        self.S = np.array([np.concatenate([_seen_joints(P)[k] for k in _SEEN4]) for P in self.P])
        self.mV, self.mS = _tangents(self.x, self.V), _tangents(self.x, self.S)

    def __call__(self, w: float) -> Pose:
        x = self.x
        w = min(1.0, max(0.0, float(w)))
        i = min(len(x) - 2, int(np.searchsorted(x, w, side="right")) - 1)
        h = x[i + 1] - x[i]
        t = (w - x[i]) / h
        t2, t3 = t * t, t * t * t
        c0, c1, c2, c3 = 2 * t3 - 3 * t2 + 1, (t3 - 2 * t2 + t) * h, -2 * t3 + 3 * t2, (t3 - t2) * h
        v = c0 * self.V[i] + c1 * self.mV[i] + c2 * self.V[i + 1] + c3 * self.mV[i + 1]
        P = Pose(self.P[i] if t < 0.5 else self.P[i + 1])
        n = len(_NUMS)
        for j, k in enumerate(_NUMS):
            P[k] = float(v[j])
        for j, k in enumerate(_PAIRS):
            P[k] = (float(v[n + 2 * j]), float(v[n + 2 * j + 1]))
        if 0.0 < t < 1.0:
            q = c0 * self.S[i] + c1 * self.mS[i] + c2 * self.S[i + 1] + c3 * self.mS[i + 1]
            for j, k in enumerate(_SEEN4):
                P = (aim_foot if k[0] == "a" else aim_hand)(P, k[-1], q[2 * j:2 * j + 2], True)
        return P


_SEAT = 120.0 / 380.0                   # the sofa's seat above the floor, in the child's body units (story.py)
SIT_CURL = rebase(SIT_SOFA, 40.0 / 380.0, 0.0)           # SIT_SOFA from the curl's ground point (its hips 40 world units left of it)
EDGE_CURL = rebase(SIT_EDGE, 15.0 / 380.0, _SEAT)        # SIT_EDGE from the curl's ground point (sitting 15 world units left of it)

# sitting up from the curl: the weight goes onto the near hand and the far forearm; the back comes up over the
# hips while the legs still lie folded and the head still hangs; the feet are gathered in, the knees come up, the
# hands go round them; the head comes up last
_UP_FACE = dict(eye=0.3, lid=1.0, brow=0.85, mouth=-0.42, hair=0.03, gaze=(0.0, -0.5))
_UP_A = _laid(CURL.but(rot=0.92, bend=0.88, neck=0.26, tilt=0.20, af=-2.14, ab=-2.14, **_UP_FACE), (-0.080, 0.080),
              ff=(-0.094, 0.058), fb=(-0.056, 0.026), hf=(0.088, 0.014), hb=(0.185, 0.016))
_UP_B = _laid(CURL.but(rot=0.56, bend=0.70, neck=0.46, tilt=0.14, af=-1.72, ab=-1.72, **dict(_UP_FACE, eye=0.4)), (-0.088, 0.070),
              ff=(-0.072, 0.046), fb=(-0.034, 0.022), hf=(0.062, 0.012), hb=(0.150, 0.014))
_UP_C = _laid(CURL.but(rot=0.22, bend=0.62, neck=0.50, tilt=0.05, turn=0.57, af=-0.75, ab=-0.75, look=(0.25, -0.5),
                       **dict(_UP_FACE, eye=0.5, brow=0.7)), (-0.098, 0.060),
              ff=(-0.040, 0.020), fb=(0.012, 0.016), hf=(0.000, 0.110), hb=(0.085, 0.090))
_SIT_UP = _Move(((0.0, CURL), (0.24, _UP_A), (0.50, _UP_B), (0.76, _UP_C), (1.0, SIT_CURL)))

# curling up (the coda): from the edge it draws its legs up onto the seat, lets itself down sideways onto a forearm,
# the legs folding in behind; the head goes down last; the hand slips off the seat
_DN_A = _laid(SIT_CURL.but(lean=0.14, bend=0.50, neck=0.12, look=(0.3, -0.3), hair=0.12, mouth=-0.2, brow=0.4, af=0.05, ab=0.05),
              (-0.085, 0.058), ff=(0.010, 0.016), fb=(0.060, 0.014), hf=(0.030, 0.105), hb=(0.135, 0.050))
_DN_B = _laid(CURL_EASE.but(rot=0.55, bend=0.50, neck=-0.10, tilt=-0.05, eye=0.5, lid=0.8, brow=0.3, mouth=0.0, blush=0.15,
                            af=-0.42, ab=-0.42, hair=0.2), (-0.082, 0.070),
              ff=(-0.050, 0.034), fb=(-0.010, 0.018), hf=(0.075, 0.012), hb=(0.175, 0.016))
_DN_C = _laid(CURL_EASE.but(rot=0.98, bend=0.52, neck=-0.42, tilt=-0.08, eye=0.3, lid=0.6, brow=0.1, mouth=0.15, blush=0.25,
                            af=-1.56, ab=-1.56), (-0.078, 0.088),
              ff=(-0.095, 0.046), fb=(-0.056, 0.030), hf=(0.130, 0.020), hb=(0.230, 0.150))
_CURL_UP = _Move(((0.0, EDGE_CURL), (0.30, _DN_A), (0.56, _DN_B), (0.80, _DN_C), (1.0, CURL_EASE)))

# rolling over (the coda: the phone rings): awake on its side; as the body rolls onto its back the folded legs swing
# up over the belly (laid by their angles: lgw, so the knee swings over at full length instead of turning end on) and
# the feet come down on the seat; the arm that lay under it drops off the seat and reaches down, leaning; the hand
# comes up to the ear
def _swung(P: Pose, pel, lf, lb, **hands) -> Pose:
    """_laid with the legs given by their angles lf / lb (degrees) outright (lgw = 1): a key of a roll."""
    P = _laid(P, pel, lf, lb, **hands)
    return P.but(lgw=1.0, lgf=(math.radians(lf[0]), math.radians(lf[1])), lgb=(math.radians(lb[0]), math.radians(lb[1])))


_RO_A = _laid(CURL_EASE.but(neck=-0.26, tilt=-0.04, eye=0.55, lid=0.6, brow=0.05, lift=0.15, mouth=0.15, hair=0.35,
                            gaze=(-0.3, -0.4)), (-0.077, 0.092),
              ff=(-0.101, 0.049), fb=(-0.061, 0.032), hf=(0.125, -0.040), hb=(0.235, 0.165)).but(lgw=1.0)
_RO_B = _swung(CURL_EASE.but(turn=0.74, rot=1.125, bend=0.46, neck=-0.28, tilt=-0.05, look=(0.10, -0.07), eye=0.55, lid=0.6,
                             brow=0.0, lift=0.2, mouth=0.12, mopen=0.15, hair=0.38, af=-1.9, ab=-1.8, gaze=(-0.3, -0.4)),
               (-0.075, 0.094), (30.0, 205.0), (38.0, 203.0), hf=(0.090, 0.030), hb=(0.233, 0.140))
_RO_C = _swung(CURL_EASE.but(turn=1.0, rot=1.13, bend=0.28, neck=-0.20, tilt=-0.06, look=(0.12, 0.0), eye=0.45, lid=0.6,
                             brow=0.0, lift=0.3, mouth=0.1, mopen=0.45, hair=0.45, blush=0.35, af=-1.5, ab=-1.5),
               (-0.070, 0.098), (85.0, 238.0), (90.0, 222.0), hf=(-0.045, 0.150), hb=(0.210, 0.050))
_RO_E = _swung(LIE_PHONE.but(turn=1.40, rot=1.30, hturn=-0.32, tilt=0.08, neck=0.10, look=(0.25, -0.25), eye=0.95, lid=0.3,
                             mouth=0.35, joy=0.1, lift=0.35, blush=0.5, hair=0.6, eb=0.0, gaze=(0.0, -0.5)),
               (-0.066, 0.090), (150.0, 250.0), (144.0, 226.0), hf=(-0.04, 0.10), hb=(0.120, -0.272))
_RO_F = _swung(LIE_PHONE.but(hturn=-0.12, look=(0.22, -0.05), mouth=0.6, joy=0.25, blush=0.6, hair=0.7, gaze=(0.0, -0.2)),
               (-0.066, 0.100), (143.0, 263.0), (137.0, 257.0), hf=(-0.04, 0.10), hb=(0.285, 0.050))
_ROLL = _Move(((0.0, CURL_EASE), (0.12, _RO_A), (0.30, _RO_B), (0.45, _RO_C), (0.64, _RO_E), (0.83, _RO_F), (1.0, LIE_PHONE)))


def sit_up_pose(w: float) -> Pose:
    """Sitting up on the sofa, w = 0..1: from CURL to SIT_CURL (SIT_SOFA hugging its knees, drawn from
    the curl's ground point). Draw every w at the curl's ground point (CURL_X, SOFA_SEAT_Y). Space only:
    ease w, add anticipation and overshoot, wrap it in alive(). 0.4 ms."""
    return _SIT_UP(w)


def curl_up_pose(w: float) -> Pose:
    """Curling up on the sofa (the coda), w = 0..1: from EDGE_CURL (SIT_EDGE on the front edge of the
    seat, drawn from the curl's ground point) to CURL_EASE. Draw every w at the curl's ground point. 0.3 ms."""
    return _CURL_UP(w)


def roll_over_pose(w: float) -> Pose:
    """Rolling over from its side onto its back (the coda: the phone rings), w = 0..1: from CURL_EASE to
    LIE_PHONE by way of waking (0.12), the knees swinging up over the belly (0.30 to 0.45), the roll onto
    its back with the arm that lay under it reaching down in front of the sofa (0.64: the hand `ha_b`) and
    that hand coming up (0.83) to the ear. Draw every w at the curl's ground point. Space only. 0.4 ms."""
    return _ROLL(w)


def _off_move(dx: float, seat: float):
    s0 = rebase(SIT_CURL, dx, -seat)
    edge = rebase(SIT_EDGE.but(hair=0.03, look=(0.3, -0.6), neck=0.3), 135.0 / 380.0, 0.0)
    rise = STOPPED.but(pel=(-0.205, 0.338), lean=0.50, bend=0.55, neck=0.12, turn=0.25, look=(0.3, -0.8), hair=0.0,
                       hf=(0.10, -0.24), hb=(0.12, -0.23))
    rise = _seen(rise, hf=(-0.225, 0.500))
    return _Move(((0.0, s0), (0.34, edge), (0.66, rise), (1.0, STOPPED)))


_OFF = {}


def slide_off_pose(w: float, dx: float = 225.0 / 380.0, seat: float = _SEAT):
    """Sliding off the sofa and standing beside it, w = 0..1: from SIT_CURL (sitting on the seat) by way
    of the front edge to STOPPED on the floor, dx body units further toward `face` than the curl's
    ground point (default: story.X1) and `seat` below it. Returns (pose, dx, dy): draw it at
    (x + face * h * dx, y - h * dy) where (x, y) is the curl's ground point: the floor point where it
    will stand, for every w (at w = 0 that is the same drawing as SIT_CURL at the curl's point). 0.3 ms."""
    key = (round(dx, 5), round(seat, 5))
    if key not in _OFF:
        _OFF[key] = _off_move(dx, seat)
    return _OFF[key](w), dx, -seat

# the friend
# (the hands rest on the coat, above its hem: hanging straight they would show under the hem between the legs)
F_STAND = Pose(lean=0.02, neck=-0.05, look=(0.36, 0.06), mouth=0.6, hair=0.8, blush=0.4, hf=(-0.005, -0.285),
               hb=(0.04, -0.290))
F_SMILE = F_STAND.but(look=(0.42, 0.10), neck=-0.1, joy=0.8, mouth=1.4, mopen=0.55, blush=1.0, lift=0.3)
F_CALL = Pose(pel=(0.0, 0.41), lean=0.14, bend=0.0, neck=-0.22, look=(0.55, 0.22), eye=1.1, lift=0.5, mouth=0.6,
              mopen=0.8, hf=(-0.11, 0.30), hb=(0.13, 0.10), ef=1.0, eb=-1.0, ff=(-0.07, 0.0), fb=(0.07, 0.0), hair=0.8,
              open=0.8, sway=0.3, blush=0.5)
# crouched in front of the sitting child (the two-shot of the second chorus: the friend's ground point 180
# world units from the child's): sitting back on its heels with an upright back, so that its head stays
# clear of the child's bowed head; hands on the knees
F_CROUCH = Pose(pel=(-0.075, 0.170), lean=0.16, bend=0.22, neck=-0.12, look=(0.50, 0.0), eye=1.0, mouth=0.5,
                hf=(0.13, -0.16), hb=(0.17, -0.15), ff=(0.03, 0.0), fb=(0.085, 0.0), af=0.0, ab=0.0, hair=0.7, open=0.5,
                front=1.0, blush=0.4)
# the same crouch, the near hand held out low and open in front of the child's knees (ha_f)
F_OFFER = F_CROUCH.but(lean=0.25, neck=-0.16, look=(0.52, -0.05), mouth=0.75, lift=0.25, hf=(0.285, -0.150), sway=0.1)
F_PART = Pose(pel=(-0.02, 0.385), lean=-0.10, bend=-0.25, neck=-0.15, look=(0.15, 0.85), eye=0.9, brow=0.5,
              mouth=-0.2, mopen=0.5, hf=(-0.21, 0.24), hb=(0.21, 0.25), ef=1.0, eb=-1.0, ff=(-0.16, 0.0),
              fb=(0.15, 0.0), af=0.0, ab=0.0, hair=0.9, open=1.0, sway=0.4)


# --------------------------------------------------------------------------
# aliveness and follow-through
# --------------------------------------------------------------------------
def alive(P: Pose, t: float, seed: int = 0, breath: float = 1.0, blink: float = 1.0, shift: float = 1.0,
          rate: float = 0.27) -> Pose:
    """A held pose, alive: breathing (rate breaths a second, on the true time t), a blink now and then
    (deterministic from t and the seed), and slow small shifts of weight. breath / blink / shift scale
    the three (0 = off). Use it on every hold: figure(F, x, y, h, alive(STOPPED, F.t, 3), ...)."""
    out = Pose(P)
    if breath:
        ph = t * rate + rnd(seed, 71)
        b = math.sin(2.0 * math.pi * ph)
        b = (b + 0.25 * math.sin(4.0 * math.pi * ph + 0.6)) * breath          # in a little faster than out
        lying = min(1.0, abs(P["rot"]) / 0.8)
        up = 1.0 - lying
        out["chest"] = P["chest"] + 0.9 * b
        out["bend"] = P["bend"] - 0.034 * b * (0.12 + 0.88 * up)       # (lying: the back rises, the head stays where it rests)
        out["neck"] = P["neck"] - 0.016 * b * (0.3 + 0.7 * up)
        out["pel"] = (P["pel"][0], P["pel"][1] + 0.0022 * b * up)
        out["hf"] = (P["hf"][0], P["hf"][1] + 0.0045 * b * up)
        out["hb"] = (P["hb"][0], P["hb"][1] + 0.0045 * b * up)
    if blink:
        out["blink"] = max(P["blink"], blink * _blink(t, seed))
    if shift:
        if P["rot"]:
            shift = shift * (1.0 - 0.65 * min(1.0, abs(P["rot"]) / 0.8))      # a lying body hardly shifts its weight
        s1 = float(vn(t * 0.21 + rnd(seed, 72) * 50.0, seed + 9)) - 0.5
        s2 = float(vn(t * 0.16 + rnd(seed, 73) * 50.0, seed + 10)) - 0.5
        out["lean"] = out["lean"] + 0.016 * s1 * shift
        out["pz"] = P["pz"] + 0.010 * s2 * shift
        out["roll"] = P["roll"] + 0.020 * s2 * shift
        out["tilt"] = P["tilt"] + 0.020 * s1 * shift
    return out


def _blink(t: float, seed: int) -> float:
    """0..1: a blink of about a fifth of a second every three to six seconds, sometimes two in a row."""
    cell = 3.7
    best = 0.0
    for i in (int(math.floor(t / cell)), int(math.floor(t / cell)) - 1):
        t0 = (i + 0.15 + 0.7 * rnd(seed * 31 + i, 81)) * cell
        for t1 in ((t0, t0 + 0.34) if rnd(seed * 31 + i, 82) > 0.72 else (t0,)):
            u = t - t1
            if 0.0 <= u < 0.24:
                best = max(best, min(1.0, u / 0.06) if u < 0.10 else max(0.0, 1.0 - (u - 0.10) / 0.14))
    return best


def turn_round(a: Pose, b: Pose, w: float, lead: float = 0.30, hop: float = 1.0) -> Pose:
    """A turn from pose a to pose b (their `turn` keys differ) as a small piece of acting, w = 0..1:
    the eyes and the head lead (by `lead` of the turn), the body follows on an ease, the weight dips,
    the feet are picked up one after the other (hop = 0: they pivot on the ground) and the hair is
    left behind. About 12 frames for a half turn reads well. Every step is a real view of the figure:
    never a mirror flip."""
    w = min(1.0, max(0.0, float(w)))
    e = w * w * (3.0 - 2.0 * w)
    hd = min(1.0, w * (1.0 + lead) / 0.85)
    hd = hd * hd * (3.0 - 2.0 * hd)
    P = mixg(a, b, dict(look=hd, gaze=hd, eye=hd, lid=hd, brow=hd, lift=hd, neck=hd, tilt=hd, hair=min(1.0, w * 0.8)), e)
    dt = b["turn"] - a["turn"]
    arc = math.sin(math.pi * w)
    P["hturn"] = P["hturn"] + dt * (hd - e)                     # the head is ahead of the body on the way
    P["pel"] = (P["pel"][0], P["pel"][1] - 0.012 * arc)
    P["bend"] = P["bend"] + 0.06 * arc
    if hop:
        up = 0.030 * hop
        P["ff"] = (P["ff"][0], P["ff"][1] + up * max(0.0, math.sin(2.0 * math.pi * min(w, 0.5))))
        P["fb"] = (P["fb"][0], P["fb"][1] + up * max(0.0, -math.sin(2.0 * math.pi * max(w, 0.5))))
    P["sway"] = P["sway"] + 0.5 * arc * (1.0 if dt * math.cos((a["turn"] + dt * e) * HALF_PI + HALF_PI) >= 0.0 else -1.0)
    return P


_ACT = (  # group of keys: (start, end) of its move inside u = 0..1
    (("look", "gaze", "eye", "lid", "blink", "brow", "lift", "spark"), (0.00, 0.50)),
    (("neck", "tilt", "hturn"), (0.08, 0.66)),
    (("lean", "bend", "roll", "pel", "pz", "turn", "rot", "chest", "press", "open", "ff", "fb", "ffz", "fbz", "kf", "kb",
      "af", "ab", "front", "over", "lgw", "lgf", "lgb"), (0.16, 0.82)),
    (("hf", "hb", "hfz", "hbz", "ef", "eb"), (0.26, 0.94)),
    (("mouth", "mopen", "joy", "blush"), (0.34, 0.86)),
    (("hair", "sway", "bob"), (0.46, 1.00)),
)
_ACT_OF = {k: se_ for keys, se_ in _ACT for k in keys}


def act(a: Pose, b: Pose, u: float, ant: float = 0.07, over: float = 0.07, blink: float = 0.0) -> Pose:
    """One move from pose a to pose b with overlapping action, u = 0..1 over the whole move: the eyes
    lead, then the head, the spine and the feet, the hands, the mouth; the hair arrives last. ant: a
    small dip the other way before the head and the spine go (anticipation); over: how far they
    overshoot before settling; blink = 1 adds a blink on the way (the head-lift at its usual timing:
    about 1.2 s for the whole move). When the two poses differ in `rot` or `turn` (lying down, sitting
    up) the ankles travel in straight lines, as in mixs. Every in-between is a drawing: use it for any
    acted change of pose. 0.15 ms (0.5 ms with the ankles)."""
    u = min(1.0, max(0.0, float(u)))
    out = Pose()
    for k in _DEF:
        t0, t1 = _ACT_OF[k]
        v = min(1.0, max(0.0, (u - t0) / (t1 - t0)))
        w = v * v * (3.0 - 2.0 * v)
        if k in _FLAGS:
            out[k] = a[k] if w < 0.5 else b[k]
            continue
        if t0 >= 0.08 and k not in ("ff", "fb", "ffz", "fbz", "rot", "turn"):
            if over and v > 0.6:
                w += over * math.sin(math.pi * (v - 0.6) / 0.4) * (1.6 if k == "hair" else 1.0)
            if ant and 0.08 <= t0 <= 0.2:
                e = (u - t0 + 0.14) / 0.22                 # the dip begins a little before the move
                if 0.0 < e < 1.0:
                    w -= ant * math.sin(math.pi * e) ** 2
        if k in _PAIRS:
            out[k] = (a[k][0] + (b[k][0] - a[k][0]) * w, a[k][1] + (b[k][1] - a[k][1]) * w)
        else:
            out[k] = a[k] + (b[k] - a[k]) * w
    if blink:
        out["blink"] = max(out["blink"], blink * math.exp(-((u - 0.40) / 0.075) ** 2))
    if 0.0 < u < 1.0 and (abs(a["rot"] - b["rot"]) > 0.25 or abs(a["turn"] - b["turn"]) > 0.25):
        # lying down, sitting up, rolling over: the ankles travel straight in the picture (see mixs)
        v = min(1.0, max(0.0, (u - 0.16) / 0.66))
        w = v * v * (3.0 - 2.0 * v)
        Ja, Jb = _seen_joints(a), _seen_joints(b)
        for which in ("f", "b"):
            out = aim_foot(out, which, Ja["an_" + which] + (Jb["an_" + which] - Ja["an_" + which]) * w, True)
    return out


def lag(pose_at, t: float, x_at=None, h: float = 1.0, face: int = 1, k: float = 1.0, dt: float = 0.10):
    """Follow-through without state: the pose pose_at(t) with `sway` and `bob` set from how fast the
    head has been moving over the last dt seconds (hair, scarf tails and the hem of the coat are
    left behind and arrive late). pose_at: a function of time giving a Pose; x_at: a function of time
    giving the figure's world x (if it travels); h: its world height; k: strength."""
    P1, P0 = pose_at(t), pose_at(t - dt)
    J1, J0 = solve(P1), solve(P0)

    def headp(P, J):
        c_, s_ = math.cos(P["rot"]), math.sin(P["rot"])
        p = J["head"]
        return p[0] * c_ + p[1] * s_, -p[0] * s_ + p[1] * c_

    (ax, ay), (bx, by) = headp(P1, J1), headp(P0, J0)
    vx = (ax - bx) / dt
    if x_at is not None:
        vx += face * (x_at(t) - x_at(t - dt)) / (dt * h)
    vy = (ay - by) / dt
    return P1.but(sway=max(-1.0, min(1.0, P1["sway"] + 0.9 * k * vx)), bob=max(-1.0, min(1.0, P1["bob"] - 0.9 * k * vy)))


# --------------------------------------------------------------------------
# cycles
# --------------------------------------------------------------------------
def walk(ph: float, m: float = 0.0):
    """Travel cycle. ph counts cycles (one cycle = two steps); m = mood, 0 trudging .. 1 light.

    Returns (pose, advance) where advance = distance travelled since ph = 0, in body units.
    The stance foot is planted: body advance and foot path cancel exactly (no sliding).
    """
    L = lambda a, b: a + (b - a) * m
    S, D, lift = L(0.31, 0.42), L(0.64, 0.58), L(0.034, 0.085)
    v = S / D

    def foot(p):
        p = p % 1.0
        if p < D:
            x = S / 2 - v * p
            late = max(0.0, (p / D - 0.72) / 0.28)
            early = max(0.0, 1.0 - p / (D * 0.16))
            pitch = -L(0.30, 0.75) * late ** 1.5 + L(0.06, 0.30) * early ** 1.5       # heel strike, then roll off the toe
            return (x, 0.05 * (1 - math.cos(pitch)) + 0.045 * abs(math.sin(min(0.0, pitch)))), pitch
        q = (p - D) / (1.0 - D)
        e = q * q * (3 - 2 * q)
        x = -S / 2 + S * (e * 0.85 + q * 0.15)
        p0 = L(0.30, 0.75)
        yb = 0.05 * (1 - math.cos(p0)) + 0.045 * abs(math.sin(p0))        # where the stance left it: no pop at toe-off
        y = yb * (1 - q) ** 2 + lift * math.sin(math.pi * min(1.0, q * 1.08)) ** 0.9
        pitch = -L(0.30, 0.75) * (1 - q) ** 1.6 + L(0.06, 0.30) * q ** 2
        return (x, y), pitch

    ff, af = foot(ph)
    fb, ab = foot(ph + 0.5)
    ylow = math.sqrt(max(0.01, 0.405 ** 2 - (S * 0.5) ** 2)) - L(0.022, 0.006)
    yhigh = 0.398 - L(0.022, 0.002)
    py = ylow + (yhigh - ylow) * math.sin(2 * math.pi * ph) ** 2
    sw = L(0.13, 0.42)
    aa = sw * math.sin(2 * math.pi * (ph + 0.02))        # each arm goes with the opposite leg
    al = L(0.325, 0.30)
    hf = (math.sin(aa) * al + L(0.035, 0.03), -math.cos(aa) * al)
    hb = (math.sin(-aa) * al + L(0.035, 0.03), -math.cos(-aa) * al)
    nod = L(0.035, 0.03) * math.sin(4 * math.pi * ph + 0.6)
    side = math.sin(2 * math.pi * (ph + 0.03))            # weight over the standing foot (seen from the back or the front)
    P = Pose(pel=(0.0, py), pz=-0.020 * side, roll=0.045 * side, lean=L(0.20, 0.07) + 0.02 * math.sin(4 * math.pi * ph),
             bend=L(0.45, 0.0), neck=L(0.30, -0.05) + nod, look=(L(0.34, 0.42), L(-0.70, 0.10)),
             eye=L(0.55, 1.0), lid=L(1.0, 0.0), brow=L(0.55, 0.0), mouth=L(-0.35, 0.6), blush=L(0.0, 0.5), hf=hf, hb=hb,
             ef=-1.0, eb=-1.0, ff=ff, fb=fb, af=af, ab=ab, hair=L(0.08, 0.8), sway=L(0.0, 0.25), open=L(0.42, 0.5),
             bob=-L(0.10, 0.25) * math.cos(4 * math.pi * ph + 0.9))
    return P, v * ph


WALK_BEAT = 1.0 / 1.5            # cycles a second for one step per beat (a beat is 0.75 s): walk_to(..., rate=WALK_BEAT)


def walk_away(ph: float, m: float = 0.0, toward: bool = False, depth: float = 0.22):
    """The walk seen from behind (or, toward=True, from the front): walking away from us into the
    picture. Returns (pose, advance): advance = body units walked into the depth since ph = 0. The
    figure does not travel in x; the scene shrinks it with the distance, for example
    s = 1 / (1 + 0.35 * advance): draw it with height h * s at y = horizon + (y0 - horizon) * s.
    depth: how much higher on the paper a foot or a hand is drawn when it is further away."""
    P, adv = walk(ph, m)
    k = -depth if toward else depth
    return P.but(turn=1.0 if toward else -1.0, ff=(P["ff"][0], P["ff"][1] + k * (P["ff"][0] + 0.16)),
                 fb=(P["fb"][0], P["fb"][1] + k * (P["fb"][0] + 0.16)), hf=(P["hf"][0], P["hf"][1] + k * P["hf"][0]),
                 hb=(P["hb"][0], P["hb"][1] + k * P["hb"][0]), hfz=0.02, hbz=0.02), adv


class Walk(tuple):
    """What walk_to returns: (pose, x, face, t0, t1), also by name."""
    __slots__ = ()
    pose = property(lambda self: self[0])
    x = property(lambda self: self[1])
    face = property(lambda self: self[2])
    t0 = property(lambda self: self[3])
    t1 = property(lambda self: self[4])


def _step(a: Pose, b: Pose, w: float, key: str, lift: float):
    """One step between two poses: the foot `key` ('ff' / 'fb') stays planted, the other is lifted
    across. Returns (pose, body shift in body units that keeps the planted foot where it is)."""
    P = mixp(a, b, w)
    other, pitch = ("fb", "ab") if key == "ff" else ("ff", "af")
    P[other] = (P[other][0], P[other][1] + lift * math.sin(math.pi * w) ** 0.9)
    P[pitch] = P[pitch] - 0.25 * math.sin(math.pi * w) ** 2
    return P, _ankle_x(a, key) - _ankle_x(P, key)


def _ankle_x(P: Pose, key: str) -> float:
    """Where an ankle shows in the picture (x, body units from the ground point)."""
    yt = P["turn"] * HALF_PI
    ct = math.cos(yt)
    se = math.sin(yt + OPEN_K * P["open"] * ct * abs(ct) * HALF_PI)
    sg = 1.0 if key == "ff" else -1.0
    px = P["pel"][0]
    return px + (P[key][0] - px) * ct - sg * (HIP + P[key + "z"]) * se


def walk_to(t: float, x0: float, x1: float, h: float, *, start: float | None = None, arrive: float | None = None,
            m: float = 0.0, rate: float | None = None, rest: Pose | None = None, rest0: Pose | None = None) -> Walk:
    """Walk from world x0 to world x1 and stop there, feet planted all the way.

        W = walk_to(F.t, 250, 840, 300, start=100.0)             # or arrive=106.5
        J = figure(F, W.x, ground_y, 300, W.pose, "child", W.face, seed=3)

    t: now. h: world standing height. start / arrive: when the first step begins, or when the figure
    has come to rest (give one). m: mood of the walk, 0 trudge .. 1 light. rate: cycles a second (two
    steps each; default 0.62 for the trudge to 0.92; 1 / 1.5 is a step a beat). rest: the pose it ends
    in (default STOPPED for a trudge, STAND otherwise); rest0: the pose it starts from (default: rest).
    One step out of rest0, whole steps of the cycle (their length adapts a little so that the last one
    ends on x1), one step into rest: before W.t0 the result is (rest0, x0), after W.t1 it is (rest, x1).
    """
    rest = (STOPPED if m < 0.5 else STAND) if rest is None else rest
    rest0 = rest if rest0 is None else rest0
    rate = 0.62 + 0.30 * m if rate is None else rate
    face = 1 if x1 >= x0 else -1
    dist = abs(x1 - x0) / h
    W0, stride = walk(0.0, m)[0], walk(1.0, m)[1]
    s2, a0 = W0["ff"][0], W0["fb"][0]                    # the leading and the trailing foot at a contact
    # n steps of the cycle between the step out and the step in; the foot that leads at the end is ff when n is even
    n = max(1, round((dist - rest0["fb"][0] + rest["ff"][0] - s2 + a0) / (0.5 * stride)))
    lead = "ff" if n % 2 == 0 else "fb"
    # step-length factor: the feet are measured where they show (the hips are a little apart in the picture)
    off = (_ankle_x(W0, "fb") - a0) * (2.0 if lead == "ff" else 0.0)
    q = max(0.3, (dist - _ankle_x(rest0, "fb") + _ankle_x(rest, lead) + off) / (0.5 * stride * n + s2 - a0))

    def cyc(ph):
        P, adv = walk(ph, m)
        return P.but(ff=(P["ff"][0] * q, P["ff"][1]), fb=(P["fb"][0] * q, P["fb"][1])), adv * q

    half = 0.5 / rate
    t0 = start if start is not None else (arrive - (n + 2) * half if arrive is not None else 0.0)
    t1 = t0 + (n + 2) * half
    lift = 0.03 + 0.04 * m
    if t <= t0:
        return Walk((rest0, x0, face, t0, t1))
    if t >= t1:
        return Walk((rest, x1, face, t0, t1))
    xa = _ankle_x(rest0, "fb") - _ankle_x(cyc(0.0)[0], "fb")       # the body after the step out
    u = (t - t0) / half
    if u < 1.0:
        P, dx = _step(rest0, cyc(0.0)[0], u * u, "fb", lift)
    elif u < n + 1.0:
        P, dx = cyc((u - 1.0) * 0.5)
        dx += xa
    else:
        Pe, adv = cyc(n * 0.5)
        P, dx = _step(Pe, rest, 1.0 - (n + 2.0 - u) ** 2, lead, lift)
        dx += xa + adv
    return Walk((P, x0 + face * h * dx, face, t0, t1))


def run(ph: float):
    """Running cycle with a flight phase. Returns (pose, advance)."""
    S0, S1, D = 0.19, -0.23, 0.36
    v = (S0 - S1) / D

    def foot(p):
        p = p % 1.0
        if p < D:
            x = S0 - v * p
            late = max(0.0, (p / D - 0.6) / 0.4)
            pitch = -0.9 * late ** 1.3
            return (x, 0.06 * abs(math.sin(pitch))), pitch
        q = (p - D) / (1.0 - D)
        e = q * q * (3 - 2 * q)
        x = S1 + (S0 - S1) * e - 0.05 * math.sin(math.pi * q) * (1 - q)
        y = 0.06 * math.sin(0.9) * (1 - q) ** 2 + 0.135 * math.sin(math.pi * q ** 0.8) ** 1.2 * (1 - 0.35 * q)
        pitch = -0.9 * (1 - q) ** 0.9 - 0.5 * math.sin(math.pi * q) + 0.35 * q ** 3
        return (x, y), pitch

    ff, af = foot(ph)
    fb, ab = foot(ph + 0.5)
    py = 0.358 + 0.034 * math.cos(4 * math.pi * (ph - 0.43))
    s = math.sin(2 * math.pi * (ph + 0.05))
    hf = (0.05 + 0.15 * s, -0.14 + 0.09 * s)
    hb = (0.05 - 0.15 * s, -0.14 - 0.09 * s)
    P = Pose(pel=(0.0, py), lean=0.24 + 0.03 * math.sin(4 * math.pi * ph), bend=-0.05, neck=-0.2,
             look=(0.5, 0.18), eye=1.0, joy=0.8, mouth=0.9, mopen=0.6, blush=0.8, hf=hf, hb=hb, ef=-1.0, eb=-1.0,
             ff=ff, fb=fb, af=af, ab=ab, hair=1.0, sway=0.75, open=0.45,
             bob=-0.5 * math.cos(4 * math.pi * (ph - 0.30)))
    return P, v * ph
