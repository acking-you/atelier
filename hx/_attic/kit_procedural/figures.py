"""hx.kit.figures: the child and the friend as pixel-art sprites, their poses, contact and hero shadows.

Local rig frame: x points the way the figure faces, y is up, units of the nominal standing height
h, the ground (or the seat) at y = 0. Limb angles are absolute and measured from straight down,
positive swinging forward (pi/2 = horizontal forward, pi = straight up). The rig is posed in these
units, then every shape is built at real-pixel resolution and rasterised by _fig_draw (flat
materials, one-pixel outline, rim light, face stamped in whole pixels). See hx/kit/README.md.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields

import numpy as np
import skia

from mv.engine.palette import hex_rgb, mix, sk

from hx.kit import _fig_draw as D
from hx.kit._fig_geom import dirv, frame_pts, lerp_pts, rot, segment
from hx.kit import _fig_face as FACE
from hx.kit import pixel
from hx.kit.pixel import PX

PI = math.pi

# --------------------------------------------------------------------------------------------
# colours
# --------------------------------------------------------------------------------------------
INK = hex_rgb("0E1320")
DUSK = hex_rgb("34406B")
TEAL = hex_rgb("1F4E5A")
AMBER = hex_rgb("F7C873")


def _h(x):
    return hex_rgb(x)


_PROP_COLS = dict(
    p_dark=_h("191C28"), p_body=_h("2A2E3E"), p_tray=_h("B9B2A2"), p_tray_sh=_h("8E887A"),
    p_bowl=_h("E6E1D6"), p_bowl_sh=_h("B8B2A6"), p_food=_h("C98E5A"),
    p_pack=_h("4A5468"), p_pack_sh=_h("353C4D"), p_pack_lt=_h("5E6A82"), p_strap=_h("272C3B"),
)
_SCREENS = {"cold": (_h("BFDDF0"), _h("F4FAFF")), "warm": (_h("FFD08A"), _h("FFF3D6")),
            "dark": (_h("20232F"), _h("2E3242"))}

_COLS = {
    "child": dict(
        line=INK, cloth=_h("2A2E44"), cloth_sh=_h("1A1D2C"), cloth_lt=_h("373C56"), cloth_dk=_h("13151F"),
        acc=_h("D9CFBC"), acc_sh=_h("A79E8D"),
        leg=_h("5D6379"), leg_sh=_h("484D62"), leg_lt=_h("70778F"),
        shoe=_h("D8CFB8"), shoe_sh=_h("ABA18A"), sole=_h("EFE8D8"),
        skin=_h("F0DCC8"), skin_sh=_h("D5B79F"), blush=_h("EBA79A"),
        hair=_h("1E1F29"), hair_sh=_h("121319"), hair_lt=_h("4C4F64"), clip=_h("1E1F29"), clip_sh=_h("121319"),
        collar=_h("2C3150"),
        lash=_h("151827"), iris=_h("56688C"), iris_dk=_h("2B3552"), hl=_h("F6F4EE"), sclera=_h("E9E5DD"),
        mouth=_h("9A5A55"), mouth_in=_h("4A2228"), tongue=_h("D47F7C"), brow=_h("1F2131"),
    ),
    "friend": dict(
        line=_h("22140F"), cloth=_h("F3BC3E"), cloth_sh=_h("D48A22"), cloth_lt=_h("FBD978"), cloth_dk=_h("A8661A"),
        acc=_h("F5EEDD"), acc_sh=_h("C9BC9F"),
        leg=_h("3C2E37"), leg_sh=_h("2A2027"), leg_lt=_h("54424E"),
        shoe=_h("EEE4CC"), shoe_sh=_h("CDBE9C"), sole=_h("A69676"),
        skin=_h("F3D3B5"), skin_sh=_h("DDB08E"), blush=_h("EE9C8A"),
        hair=_h("8C5333"), hair_sh=_h("67391F"), hair_lt=_h("B07449"), clip=_h("DA4A61"), clip_sh=_h("A3324A"),
        collar=_h("F4EFE4"),
        lash=_h("2A1810"), iris=_h("9A5B22"), iris_dk=_h("5A3112"), hl=_h("FFF8EA"), sclera=_h("F3EEE4"),
        mouth=_h("A24F49"), mouth_in=_h("5A1E24"), tongue=_h("E3807C"), brow=_h("67391F"),
    ),
}
_TEAL_LT = _h("6FA8A8")
_TEAL_COLS = dict(cloth=TEAL, cloth_sh=mix(TEAL, INK, 0.45), cloth_lt=mix(TEAL, _TEAL_LT, 0.35),
                  cloth_dk=mix(TEAL, INK, 0.65), collar=TEAL)
_PAL_CACHE: dict = {}


def _palette(who: str, tint: float, screen: str | None, cushion_color) -> np.ndarray:
    key = (who, round(float(tint), 2), screen, tuple(round(float(c), 3) for c in cushion_color))
    pal = _PAL_CACHE.get(key)
    if pal is not None:
        return pal
    cols = dict(_PROP_COLS)
    cols.update(_COLS[who])
    if who == "child" and tint > 0:
        for k, v in _TEAL_COLS.items():
            cols[k] = mix(cols[k], v, tint)
    sc = _SCREENS.get(screen or "cold", _SCREENS["cold"])
    cols["p_screen"], cols["p_screen_hi"] = sc
    cc = tuple(cushion_color)
    cols["p_cush"], cols["p_cush_sh"], cols["p_cush_lt"] = cc, mix(cc, INK, 0.3), mix(cc, (1, 1, 1), 0.18)
    cols["flat"] = (0, 0, 0)
    pal = np.zeros((256, 3), np.float32)
    for name, i in D.M.items():
        pal[i] = [min(1.0, max(0.0, v)) for v in cols.get(name, (1, 0, 1))]
    pal = _band_centre(pal)
    if len(_PAL_CACHE) > 64:
        _PAL_CACHE.clear()
    _PAL_CACHE[key] = pal
    return pal


def _band_centre(rgb: np.ndarray) -> np.ndarray:
    """Move colours to the centre of their band of the pixel stage, so its ordered dither leaves a
    flat colour flat (no stray stipple on skin or cloth)."""
    lab = pixel._to_oklab(rgb)
    lab[..., 0] = np.round(lab[..., 0] * pixel.LEVELS) / pixel.LEVELS
    lab[..., 1] = np.round(lab[..., 1] / pixel.CHROMA_STEP) * pixel.CHROMA_STEP
    lab[..., 2] = np.round(lab[..., 2] / pixel.CHROMA_STEP) * pixel.CHROMA_STEP
    return (pixel._to_srgb(lab) * 255.0 + 0.5).astype(np.uint8)


# --------------------------------------------------------------------------------------------
# proportions (units of h): a big head with its hair about 40 % of the height, short legs
# --------------------------------------------------------------------------------------------
THIGH, SHIN, ANKLE = 0.150, 0.140, 0.035
HIP = THIGH + SHIN + ANKLE              # 0.325: standing pelvis height
UPPER, FORE = 0.125, 0.105


@dataclass(frozen=True)
class Props:
    head: float          # radius of the skull (the hair stands out round it)
    spine: float         # pelvis to neck
    thigh: float
    shin: float
    upper: float
    fore: float
    hand: float
    leg_r: float         # trouser / legging radius at the hip
    hem: float           # hem below the pelvis
    girth: float         # torso width scale


CHILD = Props(0.142, 0.30, THIGH, SHIN, UPPER, FORE, 0.036, 0.054, 0.0, 1.0)
FRIEND = Props(0.136, 0.30, THIGH, SHIN, UPPER, FORE, 0.034, 0.032, 0.025, 0.95)
HERO = Props(0.080, 0.40, 0.27, 0.25, 0.21, 0.19, 0.040, 0.050, 0.02, 0.95)


def _lerp_props(a: Props, b: Props, w: float) -> Props:
    return Props(*[getattr(a, f.name) * (1 - w) + getattr(b, f.name) * w for f in fields(Props)])


# --------------------------------------------------------------------------------------------
# poses
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Pose:
    """Joint angles and offsets of the rig (all floats, so any two poses blend)."""
    rx: float = 0.0          # pelvis offset forward (h)
    ry: float = 0.0          # pelvis offset up from standing height (h)
    roll: float = 0.0        # whole body tipped forward about the pelvis (rad)
    lean: float = 0.03       # spine from vertical, + forward
    slump: float = 0.7       # 0 upright .. 1 rounded back, head forward and down
    nod: float = 0.05        # head pitch, + down
    turn: float = 0.3        # 0 near profile .. 0.6 full three-quarter toward the viewer
    thigh_n: float = 0.03
    shin_n: float = 0.0
    foot_n: float = 0.0      # shoe angle, + toe up
    thigh_f: float = -0.04
    shin_f: float = -0.06
    foot_f: float = 0.0
    arm_n: float = 0.10
    fore_n: float = 0.28
    hand_n: float = 0.0      # 0 relaxed / holding .. 1 open palm
    arm_f: float = -0.04
    fore_f: float = 0.12
    hand_f: float = 0.0
    plant: float = 1.0       # 1 = lowest contact point rests on y = 0
    legs_front: float = 0.0  # >= 0.5: near leg drawn over the body (knees up); >= 1.5 both
    arm_front: float = 0.0   # >= 0.5: near arm drawn over the head
    fist_n: float = 0.0      # 0 .. 1 fingers curled (holding, a fist)
    fist_f: float = 0.0
    squash: float = 0.0      # landing squash of the body (run)
    farm_front: float = 0.0  # >= 0.5: far arm drawn over the legs (both hands in front of the knees)
    spread_n: float = 0.0    # front/back view: 0 the arm swings toward the viewer .. 1 out to the side
    spread_f: float = 0.0
    look: float = 0.0        # >= 0.5: the head looks back over the shoulder


def blend(a: Pose, b: Pose, w: float) -> Pose:
    """In-between of two poses (w = 0 gives a, 1 gives b)."""
    w = float(min(1.0, max(0.0, w)))
    return Pose(*[getattr(a, f.name) * (1 - w) + getattr(b, f.name) * w for f in fields(Pose)])


def _with(p: Pose, **kw) -> Pose:
    d = {f.name: getattr(p, f.name) for f in fields(Pose)}
    d.update(kw)
    return Pose(**d)


def stand(slump: float = 0.7) -> Pose:
    return Pose(slump=slump)


def _joints(p: Pose) -> dict:
    return _skeleton(p, CHILD, p.slump, 0.0)


def curled() -> Pose:
    """Deep in the sofa corner: knees pulled up in front of the chest, feet together at the seat
    edge, the head bowed, both arms wrapped round a big hugged cushion that covers the lower face
    (draw(..., cushion=True)); 'seat' is the contact. Reads best with view='front' (v1a, coda)."""
    b = Pose(roll=-0.12, lean=-0.04, slump=1.0, nod=0.55, turn=0.5, thigh_n=2.40, shin_n=-0.12, foot_n=0.0,
             thigh_f=2.32, shin_f=-0.18, foot_f=0.0, fist_n=0.5, fist_f=0.5, legs_front=1.0)
    j = _joints(b)
    c = _cushion_centre(j, CHILD)
    b = reach(b, c + np.array((0.07, -0.05)), "n", elbow=-1)
    return reach(b, c + np.array((-0.04, -0.02)), "f", elbow=-1)


def _cushion_centre(j, pr) -> np.ndarray:
    """Where a hugged cushion sits on raised knees: from the knee tops up over the lower face."""
    top = j["Hc"][1] - pr.head * 0.40
    bot = max(j["K_n"][1], j["K_f"][1]) - 0.02
    x = (j["K_n"][0] + j["K_f"][0] + j["Hc"][0]) / 3.0 + 0.02
    return np.array((x, 0.5 * (top + bot)))


def sit_floor(slump: float = 0.8, hold: float = 1.0) -> Pose:
    """On the floor, back to a wall, knees up high, forearms on the knees, both hands together on
    top of the knees (hold 0 = hands resting lower on the shins)."""
    b = Pose(lean=-0.10, slump=slump, nod=0.30, turn=0.4, thigh_n=2.30, shin_n=-0.10, foot_n=0.05,
             thigh_f=2.20, shin_f=-0.16, foot_f=0.0, hand_n=0.0, fist_n=0.6, fist_f=0.6, legs_front=1.0,
             farm_front=1.0)
    j = _joints(b)
    top = j["K_n"] + np.array((0.02, 0.0))
    low = lerp_pts(j["K_n"], j["A_n"], 0.35) + np.array((0.05, 0.0))
    tg = lerp_pts(low, top, hold)
    b = reach(b, tg, "n", elbow=-1)
    return reach(b, tg + np.array((-0.020, -0.010)), "f", elbow=-1)


def phone_look(slump: float = 0.8) -> Pose:
    """Seated on the floor, knees up, both hands in front of the knees holding something at knee
    height (anchor 'hold'), the head bowed toward it (draw(..., phone='cold'))."""
    b = _with(sit_floor(slump), nod=0.40, thigh_n=2.05, shin_n=-0.30, thigh_f=1.98, shin_f=-0.34)
    j = _joints(b)
    tg = j["K_n"] + np.array((0.06, 0.03))
    b = reach(b, tg, "n", elbow=-1)
    return reach(b, tg + np.array((-0.018, -0.006)), "f", elbow=-1)


def sit_cross(slump: float = 0.15) -> Pose:
    """Cross-legged on the floor, three-quarter toward the viewer: knees out to both sides, the
    shins crossed in front, hands together in the lap (best with view='front')."""
    b = Pose(lean=-0.03, slump=slump, nod=0.15, turn=0.6,
             thigh_n=1.95, shin_n=-1.10, foot_n=-0.55, thigh_f=-1.95, shin_f=1.10, foot_f=0.5,
             fist_n=0.3, fist_f=0.3, legs_front=2.0, farm_front=1.0)
    j = _joints(b)
    lap = j["P"] + np.array((0.04, 0.06))
    b = reach(b, lap, "n", elbow=1)
    return reach(b, lap + np.array((-0.02, 0.004)), "f", elbow=-1)


def _ik(hip, tgt, l1: float, l2: float):
    d = np.asarray(tgt, float) - np.asarray(hip, float)
    L = min(max(math.hypot(d[0], d[1]), 1e-4), l1 + l2 - 1e-4)
    base = math.atan2(d[0], -d[1])
    c = (l1 * l1 + L * L - l2 * l2) / (2 * l1 * L)
    th = base + math.acos(max(-1.0, min(1.0, c)))
    knee = np.asarray(hip, float) + l1 * dirv(th)
    e = np.asarray(tgt, float) - knee
    return th, math.atan2(e[0], -e[1])


def _smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _gait(phase: float, stride: float, duty: float, lift: float, hip_y: float, kick: float = 0.0):
    """Leg angles for a phase-locked cycle: each stance foot stays put while the root advances
    stride per cycle (the caller moves x by stride * h * phase)."""
    out = []
    for off, hx in ((0.0, 0.01), (0.5, -0.01)):
        p = (phase + off) % 1.0
        half = duty * 0.5
        if p < duty:
            fx = stride * (half - p)
            fy = ANKLE
            fa = 0.18 * (1 - p / (0.2 * duty)) if p < 0.2 * duty else 0.0
            if p > 0.7 * duty:
                fa = -0.55 * (p - 0.7 * duty) / (0.3 * duty)
        else:
            q = (p - duty) / (1 - duty)
            fx = stride * (-half + 2 * half * _smooth(q)) - kick * math.sin(PI * q) * (1 - q)
            fy = ANKLE + lift * math.sin(PI * q) ** 0.9
            fa = -0.55 * (1 - q) ** 2 + 0.2 * _smooth((q - 0.6) / 0.4)
        th, sh = _ik((hx, hip_y), (fx, fy), THIGH, SHIN)
        out.append((th, sh, fa))
    return out


STEPS = 8          # poses per walk / run cycle: the cycle is shown as sprite frames


def _step(phase: float) -> float:
    return math.floor((phase % 1.0) * STEPS + 1e-6) / STEPS


def walk(phase: float, slump: float = 0.7, stride: float = 0.40) -> Pose:
    """Walk cycle in 8 sprite frames; phase 0..1 per two steps. Advance the figure by stride * h
    per cycle. High slump is the heavy slumped walk (head low, short arm swing)."""
    ph = _step(phase)
    ry = -0.022 + 0.012 * (1 - math.cos(4 * PI * ph)) * 0.5
    (tn, sn, fn), (tf, sf, ff) = _gait(ph, stride, 0.60, 0.045 * (1 - 0.45 * slump), HIP + ry)
    sw = (0.34 - 0.20 * slump) * math.cos(2 * PI * ph)
    return Pose(ry=ry, lean=0.05, slump=slump, nod=0.06, turn=0.15, thigh_n=tn, shin_n=sn, foot_n=fn,
                thigh_f=tf, shin_f=sf, foot_f=ff, arm_n=0.06 - sw, fore_n=0.22 - sw * 0.8,
                arm_f=0.02 + sw, fore_f=0.18 + sw * 1.0, plant=0.0, fist_n=0.15, fist_f=0.15)


def walk_light(phase: float, stride: float = 0.56) -> Pose:
    """The lighter walk of the late film: upright, a longer stride, a free arm swing, a small bounce."""
    ph = _step(phase)
    ry = -0.030 + 0.022 * (1 - math.cos(4 * PI * ph)) * 0.5
    (tn, sn, fn), (tf, sf, ff) = _gait(ph, stride, 0.58, 0.06, HIP + ry)
    sw = 0.50 * math.cos(2 * PI * ph)
    return Pose(ry=ry, lean=0.06, slump=0.12, nod=-0.06, turn=0.15, thigh_n=tn, shin_n=sn, foot_n=fn,
                thigh_f=tf, shin_f=sf, foot_f=ff, arm_n=0.08 - sw, fore_n=0.40 - sw * 0.9,
                arm_f=0.08 + sw, fore_f=0.40 + sw * 0.9, plant=0.0, fist_n=0.3, fist_f=0.3)


def run(phase: float, stride: float = 0.95) -> Pose:
    """Run cycle in 8 sprite frames with a short flight phase (plant 0: the cycle places the feet)."""
    ph = _step(phase)
    ry = -0.050 + 0.03 * abs(math.sin(2 * PI * ph + 0.6))
    (tn, sn, fn), (tf, sf, ff) = _gait(ph, stride, 0.36, 0.12, HIP + ry, kick=0.10)
    sw = 0.75 * math.cos(2 * PI * ph)
    return Pose(ry=ry, lean=0.24, slump=0.1, nod=-0.1, turn=0.15, thigh_n=tn, shin_n=sn, foot_n=fn,
                thigh_f=tf, shin_f=sf, foot_f=ff, arm_n=0.2 - sw, fore_n=1.6 - sw * 0.5,
                arm_f=0.2 + sw, fore_f=1.6 + sw * 0.5, plant=0.0, fist_n=0.7, fist_f=0.7,
                squash=0.05 * _strike(ph, 0.12))


def _strike(ph: float, width: float) -> float:
    """1 at a foot strike (phase 0 and 0.5), falling to 0 over `width` of the cycle."""
    return max(0.0, 1.0 - min(ph % 0.5, 0.5) / width)


def lean_wind(phase: float, slump: float = 0.5, stride: float = 0.26, hug: float = 1.0) -> Pose:
    """Walking bent into a head wind, an armful hugged to the chest (hug 0 = arms down)."""
    p = walk(phase, slump, stride)
    p = _with(p, lean=0.30, nod=0.10, fist_n=0.6 * hug, fist_f=0.6 * hug, hand_n=0.0, hand_f=0.0)
    if hug <= 0.0:
        return p
    j = _joints(p)
    chest = j["C"] + j["d1"] * 0.05 + np.array((0.10, 0.0))
    q = reach(p, chest, "n", elbow=-1)
    q = reach(q, chest + np.array((-0.02, 0.03)), "f", elbow=-1)
    return blend(p, q, hug)


def reach_up(slump: float = 0.15) -> Pose:
    """On tiptoe, the near arm stretched up, palm open, the face lifted."""
    return Pose(ry=0.03, lean=-0.06, slump=slump, nod=-0.40, turn=0.4, thigh_n=0.02, shin_n=0.0, foot_n=-0.85,
                thigh_f=-0.05, shin_f=-0.03, foot_f=-0.85, arm_n=2.85, fore_n=3.0, hand_n=1.0,
                arm_f=0.05, fore_f=0.2, arm_front=1.0, spread_n=0.3)


def arms_open(slump: float = 0.3) -> Pose:
    """Both arms raised out to the sides, palms up, the face lifted (best with view='front')."""
    return Pose(lean=-0.02, slump=slump, nod=-0.25, turn=0.6, thigh_n=0.06, thigh_f=-0.07, shin_f=-0.07,
                arm_n=1.55, fore_n=1.85, hand_n=1.0, arm_f=-1.45, fore_f=-1.75, hand_f=1.0,
                spread_n=1.0, spread_f=1.0)


def hand_out(slump: float = 0.2) -> Pose:
    """The near arm offered forward, palm up."""
    return Pose(lean=0.02, slump=slump, nod=0.05, turn=0.4, arm_n=1.05, fore_n=1.45, hand_n=1.0,
                arm_f=-0.02, fore_f=0.15)


def take_hand(slump: float = 0.4) -> Pose:
    """The near hand reaching forward and down to take another's hand."""
    return Pose(lean=0.05, slump=slump, nod=0.15, turn=0.4, arm_n=0.75, fore_n=1.05, hand_n=0.3, fist_n=0.55,
                arm_f=-0.02, fore_f=0.15)


def push_up(lift: float = 0.0) -> Pose:
    """Both arms shoving upward, on tiptoe (the friend against the haze); lift > 0 is a jump, the
    feet that far (h) off the ground, knees tucked a little."""
    k = min(1.0, max(0.0, lift / 0.08))
    return Pose(ry=0.03 + lift, lean=-0.08, slump=0.0, nod=-0.55, turn=0.45, thigh_n=0.08 + 0.55 * k,
                shin_n=-0.02 - 0.75 * k, foot_n=-0.8, thigh_f=-0.08 + 0.45 * k, shin_f=-0.1 - 0.8 * k, foot_f=-0.8,
                arm_n=2.75, fore_n=2.95, hand_n=1.0, arm_f=2.55, fore_f=2.85, hand_f=1.0, arm_front=1.0,
                plant=1.0 - k, spread_n=0.5, spread_f=0.5)


def hold_string(slump: float = 0.35) -> Pose:
    """The near hand raised to shoulder height, closed round a string (anchor 'hand_n')."""
    return Pose(lean=0.02, slump=slump, nod=-0.1, arm_n=1.35, fore_n=2.45, hand_n=0.0, fist_n=1.0,
                arm_f=-0.02, fore_f=0.15)


def carry(slump: float = 0.6) -> Pose:
    """Both forearms forward at the waist, carrying something flat (draw(..., tray=True))."""
    b = Pose(lean=0.04, slump=slump, nod=0.25, turn=0.35, fist_n=0.5, fist_f=0.5)
    j = _joints(b)
    tg = j["P"] + np.array((0.17, 0.07))
    b = reach(b, tg, "n", elbow=-1)
    return reach(b, tg + np.array((-0.02, 0.012)), "f", elbow=-1)


def look_back(slump: float = 0.4) -> Pose:
    """Standing, the head turned back over the shoulder (the body still faces forward)."""
    return Pose(lean=0.0, slump=slump, nod=-0.05, turn=0.2, look=1.0, arm_n=0.05, fore_n=0.15,
                arm_f=-0.08, fore_f=0.05)


def reach(base: Pose, target, side: str = "n", elbow: int = -1, who: str = "child") -> Pose:
    """base with one arm solved to put the wrist at target (rig units, relative to the head
    centre when target is given as ('head', dx, dy), else absolute local x, y)."""
    pr = CHILD if who == "child" else FRIEND
    sl = base.slump * (1.0 if who == "child" else 0.18)
    j = _skeleton(base, pr, sl, 0.0)
    if isinstance(target, tuple) and target and target[0] == "head":
        tg = j["Hc"] + j["fh"] * target[1] * pr.head + j["uh"] * target[2] * pr.head
    else:
        tg = np.asarray(target, float)
    S = j["S_" + side]
    af = 0.12 * sl
    d = tg - S
    L = min(max(math.hypot(d[0], d[1]), 1e-4), UPPER + FORE - 1e-4)
    bse = math.atan2(d[0], -d[1])
    c = (UPPER * UPPER + L * L - FORE * FORE) / (2 * UPPER * L)
    a_up = bse + elbow * math.acos(max(-1.0, min(1.0, c)))
    E = S + UPPER * dirv(a_up)
    e = tg - E
    a_fo = math.atan2(e[0], -e[1])
    r = base.roll
    return _with(base, **{"arm_" + side: a_up + r - af, "fore_" + side: a_fo + r - af})


def phone_ear(base: Pose | None = None, who: str = "child") -> Pose:
    """The near hand at the ear (a phone: draw(..., phone='warm')) on top of any base pose."""
    b = base if base is not None else stand(0.4)
    p = reach(b, ("head", -0.05, -0.30), "n", elbow=1, who=who)
    return _with(p, hand_n=0.2, fist_n=0.55, arm_front=1.0)


def wave(t: float, slump: float = 0.2, side: str = "n") -> Pose:
    """One arm up, the hand waving (t in seconds, stepped to sprite frames). side='f' waves with
    the far arm, so phone_ear(wave(t, side='f')) waves with a phone at the ear."""
    w = math.sin(math.floor(t * 6.4) / 6.4 * 2 * PI * 1.6)
    kw = {"arm_" + side: 2.2, "fore_" + side: 2.75 + 0.32 * w, "hand_" + side: 1.0, "spread_" + side: 0.6}
    if side == "n":
        kw.update(arm_f=-0.02, fore_f=0.15, arm_front=1.0)
    else:
        kw.update(arm_n=-0.02, fore_n=0.15)
    return Pose(lean=0.0, slump=slump, nod=-0.05, turn=0.45, **kw)


def hero_stand() -> Pose:
    """The film-hero stance of the wall shadow: chest out, feet apart, fists on hips."""
    return Pose(lean=-0.06, slump=0.0, nod=-0.18, turn=0.6, thigh_n=0.22, shin_n=0.16, foot_n=0.1,
                thigh_f=-0.20, shin_f=-0.14, arm_n=0.85, fore_n=-0.55, arm_f=-0.85, fore_f=0.55,
                fist_n=1.0, fist_f=1.0)


POSES = {
    "stand": stand, "curled": curled, "sit_floor": sit_floor, "sit_cross": sit_cross,
    "phone_look": phone_look, "phone_ear": phone_ear, "walk": walk, "walk_light": walk_light, "run": run,
    "lean_wind": lean_wind, "reach_up": reach_up, "arms_open": arms_open, "hand_out": hand_out,
    "take_hand": take_hand, "push_up": push_up, "hold_string": hold_string, "wave": wave,
    "hero_stand": hero_stand, "carry": carry, "look_back": look_back,
}


def pose(name: str, *args, **kw) -> Pose:
    """Named preset, e.g. pose('walk', 0.25, slump=0.9)."""
    return POSES[name](*args, **kw)


# --------------------------------------------------------------------------------------------
# skeleton
# --------------------------------------------------------------------------------------------
_JN = ("P", "C", "N", "S_n", "S_f", "E_n", "W_n", "E_f", "W_f", "H_n", "H_f", "K_n", "A_n", "K_f", "A_f")


def _skeleton(p: Pose, pr: Props, slump: float, head_tilt: float):
    s = slump
    P = np.array((p.rx, HIP + p.ry))
    lean0 = p.lean + 0.06 * s
    lean2 = lean0 + 0.26 * s
    d0, d2 = dirv(PI - lean0), dirv(PI - lean2)
    C = P + d0 * pr.spine * 0.5
    N = C + d2 * pr.spine * 0.5
    ha = 0.25 * lean2 + p.nod + 0.22 * s - head_tilt
    if ha > 0.6:            # a deep bow is carried by the neck, the face never tips into a wedge
        ha = 0.6 + (ha - 0.6) * 0.35
    tw = min(1.0, max(0.0, 0.4 + p.turn))
    S_n = N - d2 * 0.050 + np.array((0.012 + 0.03 * tw, 0.0))
    S_f = N - d2 * 0.045 + np.array((-0.012 - 0.03 * tw, 0.004))
    af = 0.12 * s
    E_n = S_n + pr.upper * dirv(p.arm_n + af)
    W_n = E_n + pr.fore * dirv(p.fore_n + af)
    E_f = S_f + pr.upper * dirv(p.arm_f + af)
    W_f = E_f + pr.fore * dirv(p.fore_f + af)
    H_n = P + np.array((0.01 + 0.025 * tw, 0.0))
    H_f = P - np.array((0.01 + 0.025 * tw, 0.0))
    K_n = H_n + pr.thigh * dirv(p.thigh_n)
    A_n = K_n + pr.shin * dirv(p.shin_n)
    K_f = H_f + pr.thigh * dirv(p.thigh_f)
    A_f = K_f + pr.shin * dirv(p.shin_f)
    pts = np.array([P, C, N, S_n, S_f, E_n, W_n, E_f, W_f, H_n, H_f, K_n, A_n, K_f, A_f])
    if p.roll:
        pts = P + rot(pts - P, p.roll)
    j = dict(zip(_JN, pts))
    r = p.roll
    j["d0"] = dirv(PI - lean0 - r)
    j["d2"] = dirv(PI - lean2 - r)
    j["d1"] = dirv(PI - 0.5 * (lean0 + lean2) - r)
    j["ha"] = ha + r
    j["fn"] = p.foot_n - r
    j["ff"] = p.foot_f - r
    j["fore_n"] = p.fore_n + af + r
    j["fore_f"] = p.fore_f + af + r
    j["tw"] = tw
    uh = np.array((math.sin(j["ha"]), math.cos(j["ha"])))
    fh = np.array((uh[1], -uh[0]))
    j["uh"], j["fh"] = uh, fh
    # head centre: the skull sits on a short neck, a little forward of it
    j["Hc"] = j["N"] + uh * pr.head * 1.12 + fh * pr.head * 0.10
    if p.plant > 0:
        cands = [j["P"] - j["d0"] * 0.05, j["K_n"] - np.array((0, 0.045)), j["K_f"] - np.array((0, 0.045))]
        for A, fa in ((j["A_n"], j["fn"]), (j["A_f"], j["ff"])):
            ff = np.array((math.cos(fa), math.sin(fa)))
            uf = np.array((-ff[1], ff[0]))
            cands += [A - ff * 0.040 - uf * 0.035, A + ff * 0.090 - uf * 0.035]
        if abs(p.roll) > 0.3:
            cands += [j["Hc"] - np.array((0, pr.head * 1.1))]
        lo = min(c[1] for c in cands)
        shift = np.array((0.0, -lo * p.plant))
        for k in _JN + ("Hc",):
            j[k] = j[k] + shift
    return j


# --------------------------------------------------------------------------------------------
# shapes (rig units; head shapes in head radii, x toward the face, y up)
# --------------------------------------------------------------------------------------------
_SHOE = np.array([(-0.042, -0.035), (0.084, -0.035), (0.096, -0.020), (0.088, -0.004), (0.050, 0.010),
                  (0.010, 0.018), (-0.030, 0.018), (-0.046, 0.002)])
_BOOT = np.array([(-0.036, -0.035), (0.076, -0.035), (0.084, -0.018), (0.070, 0.000), (0.040, 0.010),
                  (0.036, 0.020), (-0.034, 0.020)])
_FACE_Q = np.array([(-0.62, 0.45), (0.98, 0.45), (1.04, -0.02), (0.98, -0.44), (0.80, -0.78), (0.45, -0.98),
                    (0.02, -0.96), (-0.38, -0.78), (-0.62, -0.36)])
_FACE_P = np.array([(-0.40, 0.45), (0.98, 0.45), (1.06, 0.00), (1.02, -0.36), (0.88, -0.70), (0.55, -0.95),
                    (0.15, -0.95), (-0.18, -0.80), (-0.40, -0.40)])
_FACE_F = np.array([(-0.96, 0.45), (0.96, 0.45), (1.00, -0.05), (0.88, -0.52), (0.52, -0.88), (0.0, -0.99),
                    (-0.52, -0.88), (-0.88, -0.52), (-1.00, -0.05)])
# the child's tufts: (angle from up toward the face, deg; length; half width deg; lean deg)
_TUFTS_C = ((-168, 0.20, 13, -18), (-142, 0.30, 14, -24), (-114, 0.32, 13, -20), (-86, 0.34, 12, -14),
            (-58, 0.32, 12, -10), (-30, 0.28, 11, -6), (-3, 0.26, 10, 4), (24, 0.28, 11, 14),
            (52, 0.26, 11, 22), (80, 0.24, 12, 30), (106, 0.20, 12, 40))
_TUFTS_CF = ((-150, 0.24, 13, -26), (-118, 0.30, 13, -20), (-88, 0.32, 12, -12), (-60, 0.30, 12, -8),
             (-32, 0.30, 11, -6), (-6, 0.32, 11, -2), (20, 0.30, 11, 6), (46, 0.32, 12, 10),
             (74, 0.30, 12, 14), (102, 0.26, 13, 22), (132, 0.22, 13, 26), (156, 0.18, 12, 20))
def _tuft_outline(tufts, base, lag, fl, cx=0.0, cy=0.0):
    """Jagged hair silhouette: a round mass with pointed tufts (head radii)."""
    pts = []
    occupied = []
    for i, (a, ln, hw, lean) in enumerate(tufts):
        f = fl[i % len(fl)]
        tip = a + lean - lag * (30 + 10 * f) * (1 if a < 150 else 0.5)
        occupied.append((a - hw, a + hw))
        pts.append((a - hw, base))
        pts.append((tip, base + ln * (1 + 0.12 * f * min(1.0, abs(lag)))))
        pts.append((a + hw, base))
    lo, hi = tufts[0][0] - tufts[0][2], tufts[-1][0] + tufts[-1][2]
    for a in np.arange(hi + 12, lo + 360 - 6, 16.0):
        pts.append((a, base * 0.92))
    out = []
    for a, r in sorted(pts, key=lambda q: q[0] if q[0] >= lo - 1 else q[0] + 360):
        ra = math.radians(a)
        out.append((cx + math.sin(ra) * r, cy + math.cos(ra) * r))
    return np.array(out)


def _bob_outline(front: bool, lag: float):
    """The friend's bob: a round cap over the skull, sides swelling past the cheeks to the jaw, a
    blunt cut whose ends turn in a little."""
    cut = -0.86
    xb, xf = (-1.0, 1.0) if front else (-1.04, 0.94)
    pts = [(xf * 1.04, cut + 0.04), (xf * 1.22, -0.30), (xf * 1.24, 0.20)]
    for a in np.linspace(62, -62, 9):
        ra = math.radians(a)
        pts.append((math.sin(ra) * 1.20 * (xf if a > 0 else -xb), 0.12 + math.cos(ra) * 1.16))
    pts += [(-xb * -1.24, 0.20), (-xb * -1.22 + 0.05 * lag, -0.30), (-xb * -1.06 + 0.05 * lag, cut),
            (-xb * -0.86, cut - 0.03), (0.0, cut + 0.04), (xf * 0.86, cut - 0.03)]
    return np.array(pts)


def _fringe(child: bool, front: bool, tw: float, rpx: float, lag: float = 0.0) -> np.ndarray:
    """The hair over the forehead (head radii, x toward the face), built round the eyes so the
    locks fall between and beside them: the child's jagged locks reach below the eye line and the
    lid line sits partly under the hair; the friend's straight fringe stops at the brows, with side
    hair framing the cheeks."""
    xc, eyes = FACE.layout(front, tw)
    k = FACE.size_class(rpx)
    et = FACE.eye_top(rpx)
    one = 1.0 / max(rpx, 1e-6)                       # one pixel in head radii
    big = k == "l"
    ehw = (FACE.eye_box(rpx)[0] / 2.0) * one if big else one
    xb = -1.00 if front else -0.42 - 0.20 * tw       # the back edge of the face
    xf = 1.00 if front else 1.04
    top = [(xb - 0.30, 0.62), (xf + 0.14, 0.62)]
    if not child:
        fb = et + (0.20 if big else 1.6 * one)
        pts = top + [(xf + 0.14, -0.80), (xf - 0.10, -0.78), (xf - 0.12, fb)]
        xs = np.arange(xf - 0.12, xb + 0.20, -0.20)
        for i, x in enumerate(xs[1:]):
            pts.append((x, fb + (0.05 if (big and i % 2 == 0) else 0.0)))
        pts += [(xb + 0.20, fb), (xb + 0.18, -0.80), (xb - 0.12, -0.86)]
        return np.array(pts)
    root = et + (0.24 if big else 1.6 * one)
    tips = [(xf - 0.03, EYE_DROP_FRONT)]
    ex = sorted(((x, n) for x, n, _ in eyes), reverse=True)
    for i, (x, n) in enumerate(ex):
        cover = 0.16 if big else -0.5 * one           # close: the tip hides a little of the lid
        tips.append((x - 0.15 * ehw, et - cover))
        if i + 1 < len(ex):
            tips.append(((x + ex[i + 1][0]) * 0.5, -0.12 - (0.22 if big else 0.10)))
    tips.append((ex[-1][0] - ehw - (0.12 if big else 0.10), -0.36))
    tips.append((xb + 0.06, -0.58))
    pts = top + [(xf + 0.10, 0.25)]
    prev = None
    for x, y in tips:
        if prev is not None:
            mx = (prev + x) * 0.5
            if big and abs(prev - x) > 0.30:
                q = (prev * 2 + x) / 3, (prev + 2 * x) / 3
                pts += [(q[0], root), (q[0] - 0.05, root - 0.20), ((q[0] + q[1]) * 0.5, root + 0.02),
                        (q[1] - 0.05, root - 0.16), (q[1], root)]
            else:
                pts.append((mx, root))
        pts.append((x - 0.07 * lag, y))
        prev = x
    pts += [(xb - 0.10, -0.12), (xb - 0.30, 0.50)]
    return np.array(pts)


EYE_DROP_FRONT = -0.44


def _blink(t: float, key: int) -> bool:
    """A blink about every 4 s lasting one or two frames, irregular per figure."""
    from mv.engine import prims
    per = 4.0
    u = t / per + prims.hash01(key, 91)
    k = math.floor(u)
    start = 0.15 + 0.7 * prims.hash01(k * 17 + key, 92)
    x = (u - k - start) * per
    return 0.0 <= x <= 0.13


# --------------------------------------------------------------------------------------------
# the builder
# --------------------------------------------------------------------------------------------
class _Fig:
    """Builds one figure's shapes into a Sprite (three-quarter / profile, front or back)."""

    def __init__(self, who, p: Pose, pr: Props, B: D.Sprite, *, view, t, wind_l, seed, head_tilt, flat,
                 face):
        self.who, self.child = who, who == "child"
        self.p, self.pr, self.B = p, pr, B
        self.view = view
        self.back = view in ("back", "back_front")
        self.t, self.seed, self.flat = t, seed, flat
        self.face_args = face
        s = p.slump * (1.0 if self.child else 0.18)
        self.slump = s
        j = _skeleton(p, pr, s, head_tilt)
        self.j = j
        self.k = FACE.size_class(pr.head * B.s)      # "", s, m, l
        self.big = self.k == "l"
        self.mid = self.k in ("m", "l")
        self.tw = 0.0 if view == "side" else j["tw"]
        # life, in whole pixels and rarely: breathing lifts head and shoulders one pixel
        if not flat and B.s * 5 >= 200:
            if math.sin(2 * PI * t / 3.9 + seed * 1.7 + (0.0 if self.child else 1.3)) > 0.45:
                up = np.array((0.0, B.px(1)))
                for kk in ("N", "S_n", "S_f", "Hc"):
                    j[kk] = j[kk] + up
        tq = math.floor(t * 5.0) / 5.0                # follow-through moves five times a second
        self.fl = [math.sin(tq * (5.3 + i * 0.9) + i * 1.7) for i in range(6)]
        gait = 1.0 - min(1.0, p.plant)
        sway = max(-1.0, min(1.0, (p.arm_f - p.arm_n) / 0.6)) * gait
        self.lag = wind_l * (0.8 + 0.2 * self.fl[0]) + 0.35 * sway
        self.seat = _smooth((max(p.thigh_n, p.thigh_f) - 0.9 - p.roll) / 1.1)

    def d(self, n):
        """n pixels at close size, at least one."""
        return max(1, int(round(n * self.B.s * 5 / 600.0)))

    # ---- legs ------------------------------------------------------------------------------
    def leg(self, side):
        B, j, pr = self.B, self.j, self.pr
        H, K, A, fa = j["H_" + side], j["K_" + side], j["A_" + side], j["f" + side]
        near = side == "n"
        lr = pr.leg_r
        B.part(cast=True)
        if self.child:
            path = segment(H, K, lr, lr * 0.94, bulge=0.02)
            shin = segment(K, A + (K - A) * 0.08, lr * 0.94, lr * 0.98, bulge=0.01)
        else:
            path = segment(H, K, lr, lr * 0.85, bulge=0.03)
            shin = segment(K, A, lr * 0.85, lr * 0.72, bulge=0.04, bulge_b=0.0)
        B.formed(path, "leg" if near else "leg_sh", "leg_sh" if near else None, None, d=self.d(2))
        B.formed(shin, "leg" if near else "leg_sh", "leg_sh" if near else None, None, d=self.d(2))
        ff = np.array((math.cos(fa), math.sin(fa)))
        uf = np.array((-ff[1], ff[0]))
        if self.child:
            B.part(cast=True)
            sh = frame_pts(A, ff, uf, _SHOE)
            det = []
            if self.mid:
                sy = -0.035 + B.px(1)
                det.append(("f", B.path(frame_pts(A, ff, uf, [(-0.06, -0.06), (0.12, -0.06), (0.12, sy), (-0.06, sy)]),
                                        False), B.code("sole")))
            B.formed(sh, "shoe" if near else "shoe_sh", "shoe_sh", None, d=self.d(2), details=det)
        else:
            tk = (K - A) / (np.linalg.norm(K - A) + 1e-9)
            B.part(cast=True)
            shaft = segment(A, A + tk * 0.115, 0.036, 0.038)
            B.formed(shaft, "shoe" if near else "shoe_sh", "shoe_sh", None, d=self.d(2))
            B.formed(frame_pts(A, ff, uf, _BOOT), "shoe" if near else "shoe_sh", "shoe_sh", None, d=self.d(2))
            if self.mid:
                B.fill(segment(A + tk * 0.108, A + tk * 0.120, 0.040, 0.040), "acc" if near else "shoe_sh")

    # ---- arms, hands -----------------------------------------------------------------------
    def arm(self, side, S=None, E=None, W=None, a=None):
        B, j, pr, p = self.B, self.j, self.pr, self.p
        S = j["S_" + side] if S is None else S
        E = j["E_" + side] if E is None else E
        W = j["W_" + side] if W is None else W
        a = j["fore_" + side] if a is None else a
        o = getattr(p, "hand_" + side)
        fist = getattr(p, "fist_" + side)
        near = side == "n" or self.view in ("front", "back_front")
        tdir = (W - E) / (np.linalg.norm(W - E) + 1e-9)
        if self.child:
            r0, r1, r2 = 0.040, 0.036, 0.036
        else:
            r0, r1, r2 = 0.032, 0.029, 0.029
        self.hand(W + tdir * 0.004, tdir, o, fist, near)
        B.part(cast=True)
        sl = segment(S, E, r0, r1, bulge=0.02)
        fo = segment(E, W - tdir * r2 * 0.7, r1, r2, bulge=0.01)
        base = "cloth" if near else "cloth_sh"
        det = []
        if self.big:
            det.append(("f", B.path(segment(W - tdir * 0.022, W, r2 * 1.05, r2 * 1.05)), B.code("cloth_sh" if near else "cloth_dk")))
        B.formed(sl, base, "cloth_sh" if near else "cloth_dk", None, d=self.d(2))
        B.formed(fo, base, "cloth_sh" if near else "cloth_dk", None, d=self.d(2), details=det)
        if not self.child and self.big and near:
            B.fill(segment(W - tdir * 0.032, W - tdir * 0.018, r2 * 1.08, r2 * 1.08), "cloth_lt")

    def hand(self, W, tdir, o, f, near):
        """A small mitten at wide and standard size; palm, thumb and finger slits when close."""
        B, pr = self.B, self.pr
        hs = pr.hand * (1.45 if self.big else 1.1)
        skin = "skin" if near else "skin_sh"
        if not self.big:
            B.part(cast=True)
            c = W + tdir * hs * (0.55 + 0.25 * o - 0.15 * f)
            B.fill(D_ellipse(c, tdir, hs * (0.80 + 0.35 * o - 0.1 * f), hs * 0.72), skin)
            return
        n = np.array((-tdir[1], tdir[0]))
        if n[1] < 0:
            n = -n
        o = min(1.0, max(0.0, o))
        f = min(1.0, max(0.0, f)) * (1 - o * 0.6)
        fing = lerp_pts(lerp_pts(_FING_RELAX, _FING_OPEN, o), _FING_FIST, f)
        thumb = lerp_pts(lerp_pts(_THUMB_RELAX, _THUMB_OPEN, o), _THUMB_FIST, f)
        Pm = lambda loc: frame_pts(W, tdir, n, loc, hs * 1.1)      # noqa: E731
        B.part(cast=True)
        hp = B.fill(Pm(np.vstack([_PALM[:3], fing[1:7], _PALM[5:]])), skin)
        det = []
        if o > 0.35 or f > 0.5:
            for k in range(3):
                tip = lerp_pts(fing[2 + k], fing[3 + k], 0.5)
                det.append(("s", _seg_path(B, Pm(np.array([tip - (0.30 if f < 0.5 else 0.12, 0.0), tip + (0.05, 0.0)]))),
                            B.code("skin_sh"), 1.0))
        B.clip(hp, det)
        B.part(cast=True)
        B.fill(Pm(thumb), skin)

    # ---- torso -----------------------------------------------------------------------------
    def torso(self):
        B, j, pr, p = self.B, self.j, self.pr, self.p
        P, C, N = j["P"], j["C"], j["N"]
        d0, d1, d2 = j["d0"], j["d1"], j["d2"]
        f0, f1, f2 = _perp(d0), _perp(d1), _perp(d2)
        tw, seat, s = self.tw, self.seat, self.slump
        g = pr.girth * (1 + 0.6 * p.squash)
        lagv = np.array((self.lag, 0.0))
        fl = self.fl[1]
        if self.child:
            wf, wb, wsh = (0.106 + 0.040 * tw) * g, (0.100 + 0.028 * tw) * g, 0.090 * g
            hem = pr.hem
            flare = 0.0
        else:
            wf, wb, wsh = (0.092 + 0.034 * tw) * g, (0.088 + 0.022 * tw) * g, 0.074 * g
            hem = pr.hem * (1 - 0.6 * seat)
            flare = 0.038 * (1 - 0.7 * seat)
        wf_low = wf * (1 - 0.35 * seat)
        hem_f = P - d0 * hem + f0 * (wf_low + flare) + lagv * 0.02
        hem_b = P - d0 * hem - f0 * (wb + flare) + lagv * 0.05 * (0.7 + 0.3 * fl)
        pts = np.array([
            hem_f,
            P + d0 * 0.10 + f0 * wf * 1.02,
            C + d1 * 0.05 + f1 * wf * 0.94,
            N - d2 * 0.05 + f2 * wsh * 0.95,
            N + d2 * 0.005 + f2 * 0.030,
            N + d2 * 0.005 - f2 * 0.030,
            N - d2 * 0.055 - f2 * (wsh * 1.15 + 0.02 * s),
            C - f1 * (wb + 0.030 * s),
            P + d0 * 0.06 - f0 * wb,
            hem_b,
        ])
        if p.roll < 0.3:
            pts[:, 1] = np.maximum(pts[:, 1], B.px(1) if self.seat > 0.5 else 0.0)
        hood_first = self.back
        if not hood_first:
            self.hood(N, d2, f2, lagv, fl)
        B.part(cast=True)
        det = []
        front = not self.back
        if self.big:
            # ribbed hem band (child) / a line of shade at the coat's lower edge
            hb = [hem_b, hem_f, hem_f + d0 * 0.022, hem_b + d0 * 0.022]
            det.append(("f", B.path(np.array(hb), False), B.code("cloth_sh")))
        if not self.child and front and self.mid:
            # placket: buttons down the front edge
            for u in (0.18, 0.42, 0.66, 0.88):
                bq = lerp_pts(P - d0 * hem * 0.6, N - d2 * 0.06, u) + lerp_pts(f0, f2, u) * (wf * (0.42 + 0.25 * tw))
                if self.big:
                    det.append(("f", B.path(D_ellipse(bq, (1, 0), 0.011, 0.011)), B.code("acc")))
                else:
                    q = B.P(bq)
                    det.append(("f", _px_rect(q), B.code("acc")))
        B.formed(pts, "cloth", "cloth_sh", "cloth_lt" if (not self.child or self.big) else None,
                 d=self.d(3), dl=self.d(1), details=det)
        if front and self.mid:
            if self.child:
                # kangaroo pocket
                B.part(cast=True)
                top_b = P + d0 * 0.105 + f0 * (wf * (0.10 - 0.25 * (1 - tw)))
                top_f = P + d0 * 0.105 + f0 * wf * 0.72
                bot_f = P + d0 * 0.020 + f0 * wf * 0.96
                bot_b = P + d0 * 0.020 - f0 * wf * (0.20 - 0.25 * (1 - tw))
                pk = np.array([top_b, top_f, bot_f, bot_b])
                pdet = [("f", B.path(np.array([top_b, top_f, top_f - d0 * 0.016, top_b - d0 * 0.016]), False),
                         B.code("cloth_sh"))] if self.big else []
                B.formed(pk, "cloth", "cloth_sh", None, d=self.d(2), details=pdet, smooth_=False)
            else:
                for u, w in ((0.0, 1.0),):
                    B.part(cast=True)
                    c0 = P + d0 * 0.035 + f0 * wf * (0.62 + 0.1 * tw)
                    pk = np.array([c0 - f0 * 0.040 + d0 * 0.035, c0 + f0 * 0.040 + d0 * 0.035,
                                   c0 + f0 * 0.042 - d0 * 0.035, c0 - f0 * 0.042 - d0 * 0.035])
                    flap_y = 0.016
                    pdet = [("s", _seg_path(B, B.P(np.array([c0 - f0 * 0.04 + d0 * flap_y, c0 + f0 * 0.04 + d0 * flap_y]))),
                             B.code("line"), 1.0)]
                    B.formed(pk, "cloth", "cloth_sh", None, d=self.d(2), details=pdet, smooth_=False)
        if hood_first:
            self.hood(N, d2, f2, lagv, fl)

    def hood(self, N, d2, f2, lagv, fl):
        """Hood down: bunched behind the neck (front views), lying on the back (back view)."""
        B = self.B
        hb = N - f2 * 0.052 - d2 * 0.018 + lagv * 0.03 * (0.6 + 0.4 * fl)
        B.part(cast=True)
        if self.back:
            loc = [(0.075, 0.030), (0.010, 0.050), (-0.060, 0.030), (-0.070, -0.040), (-0.030, -0.110),
                   (0.030, -0.100), (0.070, -0.040)]
            hood = frame_pts(hb + f2 * 0.025, f2, d2, np.array(loc))
            det = []
            if self.mid:
                det.append(("s", _seg_path(B, B.P(frame_pts(hb + f2 * 0.025, f2, d2, np.array(
                    [(0.05, 0.0), (0.0, -0.06), (-0.045, -0.01)])))), B.code("cloth_sh"), 1.0))
            B.formed(hood, "cloth", "cloth_sh", None, d=self.d(2), details=det)
        else:
            loc = [(0.060, 0.040), (0.005, 0.058), (-0.050, 0.044), (-0.072, 0.000), (-0.056, -0.050),
                   (-0.008, -0.060), (0.045, -0.025)]
            hood = frame_pts(hb, f2, d2, np.array(loc))
            det = []
            if self.mid:
                op = frame_pts(hb, f2, d2, np.array([(0.050, 0.028), (0.016, 0.040), (-0.016, 0.026),
                                                     (-0.006, -0.010), (0.030, -0.016)]))
                det.append(("f", B.path(op), B.code("cloth_dk")))
            B.formed(hood, "cloth", "cloth_sh", None, d=self.d(2), details=det)

    def strings(self):
        """The hoodie's two pale drawstrings (child, seen from the front side)."""
        if not self.child or self.back or not self.k:
            return
        B, j = self.B, self.j
        N, d2 = j["N"], j["d2"]
        f2 = _perp(d2)
        tw = self.tw
        B.part(cast=False, recv=False)
        ln = max(0.07, B.px(2.2))
        gap = max(0.036 * (0.4 + 0.6 * tw), B.px(2))
        x0 = 0.030 + 0.020 * tw
        for k in range(2 if tw > 0.25 else 1):
            root = N - d2 * 0.050 + f2 * (x0 + gap * k)
            ang = -0.10 + 0.35 * self.lag + 0.03 * k
            tip = root + np.array((math.sin(ang), -math.cos(ang))) * (ln + 0.006 * k)
            B.stroke(np.array([root, tip]), "acc", 1.0 if not self.big else 2.0)

    def collar(self):
        if self.child or self.back or not self.mid:
            return
        B, j = self.B, self.j
        N, d2 = j["N"], j["d2"]
        f2 = _perp(d2)
        B.part(cast=False, recv=False)
        a0 = N - d2 * 0.010 + f2 * 0.020
        B.fill(np.array([a0 + f2 * 0.022, a0 - f2 * 0.030, a0 - d2 * 0.040 + f2 * 0.004]), "collar", False)

    # ---- head ------------------------------------------------------------------------------
    def head(self):
        B, j, pr = self.B, self.j, self.pr
        Hc, uh, fh = j["Hc"], j["uh"], j["fh"]
        looking_back = self.p.look >= 0.5
        if looking_back:
            fh = -fh
            uh = np.array((-uh[0], uh[1]))
        R = pr.head
        tw = self.tw if not looking_back else max(0.0, self.tw - 0.25)
        HL = lambda loc: frame_pts(Hc, fh, uh, np.asarray(loc, float), R)      # noqa: E731
        lag = self.lag
        child = self.child
        back = self.back
        # neck
        B.part(cast=False)
        B.fill(segment(j["N"] - j["d2"] * 0.01, Hc - uh * R * 0.7, 0.030, 0.030), "skin_sh")
        # the hair mass behind the head
        B.part(cast=True)
        if child:
            mass = _tuft_outline(_TUFTS_C, 1.32, lag, self.fl, -0.08, 0.04)
        else:
            mass = _bob_outline(False, lag)
        hdet = self._hair_lights(HL, back)
        self.mass_path = B.formed(HL(mass), "hair", "hair_sh", "hair_lt" if not child else None, d=self.d(3),
                                  dl=self.d(2), details=hdet, smooth_=child is False)
        if child and self.k in ("m", "l"):
            # the cowlick
            B.part(cast=True)
            pts = HL(np.array([(-0.10, 1.10), (-0.04, 1.36), (-0.14, 1.52), (-0.32, 1.50)]))
            B.stroke(pts, "hair", 1.0 if not self.big else 2.0)
        if back:
            # turned away: only the edge of a cheek and the ear show past the hair
            B.part(cast=False, recv=False)
            B.fill(HL(np.array([(0.80, -0.20), (1.02, -0.30), (0.96, -0.70), (0.70, -0.86), (0.62, -0.50)])), "skin_sh")
            B.part(cast=True)
            back_hair = mass * 0.97 + np.array((0.0, -0.02))
            B.fill(HL(back_hair), "hair", smooth_=not child)
            B.clip(B.path(HL(back_hair), not child), self._hair_lights(HL, True))
            if not child and self.mid:
                self._clip_rose(HL, (0.78, 0.46))
            return
        # face
        self.face_part = B.part(cast=True, recv=False)
        face = lerp_pts(_FACE_P, _FACE_Q, tw)
        B.formed(HL(face), "skin", "skin_sh" if self.big else None, None, d=self.d(2))
        # ear
        if self.mid:
            B.part(cast=False, recv=False)
            ec = (-0.50 - 0.10 * tw, -0.20)
            B.fill(HL(D_ellipse(ec, (1, 0), 0.15, 0.20)), "skin")
        # fringe and side locks
        B.part(cast=False, recv=False)
        if child:
            fr = _fringe(True, False, tw, R * B.s, lag)
            B.formed(HL(fr), "hair", "hair_sh", None, d=self.d(2), smooth_=False,
                     details=self._hair_lights(HL, False, fringe=True))
            B.clip_last(self.mass_path)
        else:
            bg = _fringe(False, False, tw, R * B.s, lag)
            B.formed(HL(bg), "hair", "hair_sh", "hair_lt", d=self.d(2), dl=self.d(1), smooth_=False)
            B.clip_last(self.mass_path)
            if self.k:
                self._clip_rose(HL, (0.50 + 0.10 * tw, 0.50))
        self._stamp_face(Hc, fh, uh, R, tw, front=False)

    def _hair_lights(self, HL, back, fringe=False):
        """The few lighter clusters of the hair (on the lit side) and, close, a few dark strands."""
        B = self.B
        out = []
        if not self.mid:
            return out
        lsx = 1.0 if B.L[0] * B.f > 0 else -1.0       # light from the face side (+) or the back (-)
        if self.child:
            if fringe:
                return _hair_clusters(B, HL, lsx, True, self.big)
            out += _hair_clusters(B, HL, lsx if back else -1.0, False, self.big)
            if self.big:
                for a0, a1, r0 in ((-20, -110, 0.70), (10, -60, 0.55), (-60, -150, 0.80)):
                    q = [(math.sin(math.radians(a)) * (r0 + 0.25 * u), 0.08 + math.cos(math.radians(a)) * (r0 + 0.25 * u))
                         for a, u in ((a0, 0.0), ((a0 + a1) / 2, 0.5), (a1, 1.0))]
                    out.append(("s", _seg_path(B, B.P(HL(np.array(q)))), B.code("hair_sh"), 1.0))
        else:
            band = [(math.sin(math.radians(a)) * r, 0.06 + math.cos(math.radians(a)) * r)
                    for a, r in ((-70, 0.98), (-30, 1.04), (10, 1.04), (50, 0.98), (40, 0.84), (5, 0.88),
                                 (-30, 0.88), (-66, 0.84))]
            out.append(("f", B.path(HL(np.array(band))), B.code("hair_lt")))
        return out

    def _clip_rose(self, HL, at):
        B = self.B
        B.part(cast=True, recv=False)
        cx, cy = at
        el = HL(D_ellipse((cx, cy), (0.6, 0.8), 0.20, 0.10))
        if self.big:
            B.formed(el, "clip", "clip_sh", None, d=1)
        else:
            B.fill(el, "clip")

    def _stamp_face(self, Hc, fh, uh, R, tw, front):
        if self.flat or not self.k or self.face_args is None:
            return
        B = self.B
        hc = B.P(Hc)
        fhp = np.array((fh[0] * B.f, -fh[1]))
        uhp = np.array((uh[0] * B.f, -uh[1]))
        rpx = R * B.s
        fa = dict(self.face_args)
        fp = self.face_part
        lx = B.L[0] or -1

        def go(mat, part, ox, oy):
            FACE.stamp(mat, part, ox, oy, face_part=fp, hc=hc, fh=fhp, uh=uhp, rpx=rpx, tw=tw, front=front,
                       tired=self.child, light_x=lx, **fa)
        B.face = go
        B.marks["head_px"] = hc

    # ---- props -----------------------------------------------------------------------------
    def cushion(self):
        B, j = self.B, self.j
        if self._knees_up():
            c = _cushion_centre(j, self.pr)
            top = j["Hc"][1] - self.pr.head * 0.40
            hh = max(0.06, top - c[1])
            ww = 0.135
            ax, bx = np.array((0.0, 1.0)), np.array((1.0, 0.0))
        else:
            c = lerp_pts((j["W_n"] + j["W_f"]) * 0.5, j["C"], 0.35) + j["d1"] * 0.03
            ax = j["d1"]
            bx = _perp(ax)
            hh, ww = 0.085, 0.105
        pts = frame_pts(c, bx, ax, np.array([(1.0, 1.0), (0.0, 0.86), (-1.0, 1.04), (-0.88, 0.0), (-1.04, -1.0),
                                             (0.0, -0.86), (1.02, -0.98), (0.90, 0.0)]) * (ww, hh))
        B.part(cast=True)
        det = []
        if self.big:
            det.append(("s", _seg_path(B, B.P(frame_pts(c, bx, ax, np.array([(-0.5, 0.15), (0.0, 0.05), (0.45, 0.2)]) * (ww, hh)))),
                        B.code("p_cush_sh"), 1.0))
        B.formed(pts, "p_cush", "p_cush_sh", "p_cush_lt", d=self.d(4), dl=self.d(1), details=det)
        B.marks["cushion"] = c

    def _knees_up(self):
        return self.seat > 0.5 and self.p.legs_front < 1.5

    def phone(self, kind):
        B, j = self.B, self.j
        hn = j["W_n"] + dirv(j["fore_n"]) * self.pr.hand * 0.6
        hf = j["W_f"] + dirv(j["fore_f"]) * self.pr.hand * 0.6
        at_ear = self.p.arm_front >= 0.5 and hn[1] > j["N"][1]
        w, hh = max(0.030, B.px(2)), max(0.054, B.px(3))
        if at_ear:
            c = hn + np.array((0.0, 0.015))
            up = dirv(PI - 0.15)
        elif np.linalg.norm(hn - hf) < 0.12:
            c = (hn + hf) * 0.5 + np.array((0.0, 0.020))
            up = dirv(PI + 0.25)
        else:
            c = hn + np.array((0.0, 0.025))
            up = dirv(PI + 0.25)
        side = _perp(up)
        B.part(cast=True, recv=False)
        pts = frame_pts(c, side, up, np.array([(-w / 2, -hh / 2), (w / 2, -hh / 2), (w / 2, hh / 2), (-w / 2, hh / 2)]))
        if at_ear:
            B.fill(pts, "p_body", False)
            if self.mid:
                B.fill(frame_pts(c, side, up, np.array([(w / 2, -hh / 2), (w / 2 + B.px(1), -hh / 2),
                                                        (w / 2 + B.px(1), hh / 2), (w / 2, hh / 2)])),
                       "p_screen", False)
        else:
            sc = "p_screen" if kind != "dark" else "p_dark"
            inner = frame_pts(c, side, up, np.array([(-w / 2, -hh / 2), (w / 2, -hh / 2), (w / 2, hh / 2),
                                                     (-w / 2, hh / 2)]) * (0.7 if self.big else 1.0))
            B.fill(pts, "p_body", False)
            B.fill(inner, sc, False)
            if self.big and kind != "dark":
                B.fill(frame_pts(c, side, up, np.array([(-w / 2, hh * 0.05), (w * 0.2, hh * 0.3),
                                                        (w * 0.2, hh * 0.35), (-w / 2, hh * 0.1)]) * 0.7),
                       "p_screen_hi", False)
        B.marks["phone"] = c

    def tray(self):
        B, j = self.B, self.j
        hn = j["W_n"] + dirv(j["fore_n"]) * self.pr.hand * 0.5
        hf = j["W_f"] + dirv(j["fore_f"]) * self.pr.hand * 0.5
        c = (hn + hf) * 0.5 + np.array((0.02, 0.012))
        L, T = 0.20, max(0.016, B.px(1))
        B.part(cast=True)
        slab = np.array([c + (-L * 0.40, 0.0), c + (L * 0.60, 0.0), c + (L * 0.56, -T), c + (-L * 0.36, -T)])
        B.formed(slab, "p_tray", "p_tray_sh", None, d=1, smooth_=False)
        B.part(cast=True)
        bw = c + (L * 0.12, 0.0)
        bowl = np.array([bw + (-0.040, 0.0), bw + (0.040, 0.0), bw + (0.030, 0.026), bw + (-0.030, 0.026)])
        B.formed(bowl, "p_bowl", "p_bowl_sh", None, d=1, smooth_=False)
        cup = c + (L * 0.42, 0.0)
        B.part(cast=True)
        B.formed(np.array([cup + (-0.016, 0.0), cup + (0.016, 0.0), cup + (0.018, 0.036), cup + (-0.018, 0.036)]),
                 "p_bowl", "p_bowl_sh", None, d=1, smooth_=False)
        B.marks["tray"] = c

    def backpack(self, behind: bool):
        B, j = self.B, self.j
        N, P, d1 = j["N"], j["P"], j["d1"]
        f1 = _perp(d1)
        C = j["C"]
        if behind:
            B.part(cast=True)
            top = N - d1 * 0.03 - f1 * 0.07
            bot = P + d1 * 0.06 - f1 * 0.08
            pts = np.array([top + f1 * 0.04, top - f1 * 0.07, bot - f1 * 0.09, bot + f1 * 0.03])
            B.formed(pts, "p_pack", "p_pack_sh", "p_pack_lt", d=self.d(3), dl=self.d(1))
            if self.mid:
                B.part(cast=True)
                pk = lerp_pts(top, bot, 0.6) - f1 * 0.10
                B.formed(np.array([pk + f1 * 0.03 + d1 * 0.04, pk - f1 * 0.035 + d1 * 0.04, pk - f1 * 0.04 - d1 * 0.05,
                                   pk + f1 * 0.03 - d1 * 0.05]), "p_pack", "p_pack_sh", None, d=1)
        else:
            B.part(cast=False, recv=False)
            w = max(1.0, 0.020 * B.s)
            a = j["S_n"] + d1 * 0.01 - f1 * 0.03
            b = C - d1 * 0.06 + f1 * 0.02
            if self.back:
                a, b = j["S_n"] + d1 * 0.01 + f1 * 0.0, C - d1 * 0.03 - f1 * 0.03
            B.stroke(np.array([a, b]), "p_strap", w)

    # ---- assembly --------------------------------------------------------------------------
    def build(self, cushion=False, phone=None, tray=False, backpack=False):
        p = self.p
        if backpack and not self.back:
            self.backpack(True)
        if p.farm_front < 0.5:
            self.arm("f")
        if p.legs_front < 1.5:
            self.leg("f")
        if p.legs_front < 0.5:
            self.leg("n")
        self.torso()
        self.collar()
        if p.legs_front >= 1.5:
            self.leg("f")
        if p.legs_front >= 0.5:
            self.leg("n")
        if backpack and self.back:
            self.backpack(True)
        if p.farm_front >= 0.5:
            self.arm("f")
        hug = cushion and self._knees_up()          # a cushion on the knees covers the lower face
        if cushion and not hug:
            self.cushion()
        if tray:
            self.tray()
        if phone and p.arm_front < 0.5:
            self.phone(phone)
        if p.arm_front < 0.5 and not hug:
            self.arm("n")
        self.strings()
        if backpack:
            self.backpack(False)
        self.head()
        if hug:
            self.cushion()
            self.arm("n")
        if phone and p.arm_front >= 0.5:
            self.phone(phone)
        if p.arm_front >= 0.5:
            self.arm("n")


# hand shapes (hand-length units, x along the forearm, y across)
_PALM = np.array([(-0.18, -0.36), (0.28, -0.46), (0.62, -0.40), (0.70, 0.02), (0.62, 0.32), (0.30, 0.40), (-0.18, 0.32)])
_FING_OPEN = np.array([(0.50, -0.42), (0.95, -0.40), (1.20, -0.30), (1.27, -0.12), (1.24, 0.06), (1.12, 0.20),
                       (0.86, 0.28), (0.50, 0.30)])
_FING_RELAX = np.array([(0.50, -0.42), (0.86, -0.52), (1.04, -0.62), (1.10, -0.48), (1.06, -0.24), (0.96, -0.04),
                        (0.80, 0.14), (0.50, 0.28)])
_FING_FIST = np.array([(0.48, -0.44), (0.78, -0.50), (0.92, -0.38), (0.94, -0.12), (0.92, 0.10), (0.84, 0.22),
                       (0.68, 0.30), (0.48, 0.30)])
_THUMB_OPEN = np.array([(0.10, 0.26), (0.40, 0.52), (0.68, 0.74), (0.80, 0.66), (0.60, 0.40), (0.34, 0.16)])
_THUMB_RELAX = np.array([(0.12, 0.26), (0.46, 0.46), (0.78, 0.46), (0.80, 0.34), (0.52, 0.26), (0.30, 0.10)])
_THUMB_FIST = np.array([(0.30, 0.22), (0.62, 0.26), (0.90, 0.14), (0.86, 0.02), (0.58, 0.08), (0.32, 0.06)])


def _hair_clusters(B, HL, side, fringe, big):
    """The child's lighter locks: two or three clusters of strands fanning from the crown on the
    lit side (side -1: toward the back of the head / screen left in front views)."""
    if fringe:
        groups = [((0.55, 0.60), (0.10, -0.36), 2), ((-0.20, 0.60), (-0.06, -0.38), 2)]
    else:
        groups = [((-0.30 * -side, 1.12), (-0.30 * -side, -0.30), 3), ((0.30 * -side, 1.16), (0.18 * -side, -0.26), 2),
                  ((-0.98 * -side, 0.70), (-0.10 * -side, -0.42), 2)]
    w = 0.24 if big else 0.22
    out = []
    for (x0, y0), (dx, dy), n in groups:
        for k in range(n):
            o = (k - (n - 1) / 2) * (0.16 if big else 0.20)
            a = (x0 + o, y0)
            b = (x0 + o + dx * (1 - 0.15 * abs(o) * 4), y0 + dy * (1 - 0.2 * k))
            out.append(("f", B.path(HL(_lens(a, b, w)), False), B.code("hair_lt")))
    return out


def _perp(v):
    return np.array((v[1], -v[0]))


def D_ellipse(c, ax, rx, ry, n=12):
    ax = np.asarray(ax, float)
    ax = ax / (np.linalg.norm(ax) or 1.0)
    ay = np.array((-ax[1], ax[0]))
    th = np.linspace(0, 2 * PI, n, endpoint=False)
    return np.asarray(c, float) + np.outer(np.cos(th) * rx, ax) + np.outer(np.sin(th) * ry, ay)


def _lens(a, b, w):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = math.hypot(d[0], d[1]) or 1e-6
    n = np.array((-d[1], d[0])) / L
    return np.array([a + n * w * 0.5, a + d * 0.45 + n * w * 0.5, b, a + d * 0.45 - n * w * 0.5, a - n * w * 0.5])


def _seg_path(B, q):
    path = skia.Path()
    path.moveTo(float(q[0, 0]), float(q[0, 1]))
    for x, y in q[1:]:
        path.lineTo(float(x), float(y))
    return path


def _px_rect(q):
    path = skia.Path()
    path.addRect(skia.Rect.MakeXYWH(math.floor(q[0]), math.floor(q[1]), 1.0, 1.0))
    return path


# --------------------------------------------------------------------------------------------
# public drawing
# --------------------------------------------------------------------------------------------
_SHADOW_COL = INK


def contact_shadow(canvas, x: float, y: float, width: float, alpha: float = 0.35, color=_SHADOW_COL,
                   squash: float = 0.20, stipple: bool = False):
    """Flat hard-edged elliptical contact shadow centred at (x, y), built from whole pixels
    (stipple=True: an ordered half-tone instead of a translucent tone)."""
    if alpha <= 0.003 or width <= 1:
        return
    X, Y, gx, gy = D.device_snap(canvas, x, y)
    rx = max(1.0, width / (2 * PX))
    ry = max(1.0, rx * squash)
    paint = skia.Paint(AntiAlias=False, Color=sk(color, 1.0 if stipple else min(1.0, alpha)))
    path = skia.Path()
    n = int(math.ceil(ry))
    for r in range(-n, n):
        yc = (r + 0.5) / ry
        if abs(yc) >= 1:
            continue
        half = int(round(rx * math.sqrt(1 - yc * yc)))
        if half <= 0:
            continue
        for c in range(-half, half):
            if stipple and D._BAYER[(gy + r) % 4, (gx + c) % 4] >= alpha * 1.6:
                continue
            if stipple:
                path.addRect(skia.Rect.MakeXYWH(X + c * PX, Y + r * PX, PX, PX))
        if not stipple:
            path.addRect(skia.Rect.MakeXYWH(X - half * PX, Y + r * PX, 2 * half * PX, PX))
    canvas.drawPath(path, paint)


DEFAULT_MOOD = {"child": 0.0, "friend": 0.4}     # used when a scene passes no `mood`; the renderer sets it
                                                  # from the film's hope dial before every scene draws


def set_default_mood(child: float, friend: float) -> None:
    DEFAULT_MOOD["child"], DEFAULT_MOOD["friend"] = float(child), float(friend)


def _face_state(who, eye, smile, mood, t, seed, blink, head_tilt):
    sad, glad = max(0.0, -mood), max(0.0, mood)
    if eye == "closed":
        lid = "closed"
    elif eye == "up":
        lid = "up"
    else:
        v = {"open": 0.10, "half": 0.45, "wide": 0.0}.get(eye, 0.45) + 0.28 * sad - 0.18 * glad
        lid = "open" if v < 0.30 else ("half" if v < 0.62 else "heavy")
        if blink and _blink(t, seed * 7 + (0 if who == "child" else 3)):
            lid = "closed"
    if smile > 0.02:
        mouth = "small" if smile < 0.35 else ("smile" if smile < 0.7 else "open")
    else:
        c = 0.9 * mood
        mouth = "sad" if c < -0.55 else ("flat" if c < 0.28 else ("small" if mood < 0.75 else "open"))
    blush = 2 if (smile > 0.3 or mood > 0.7) else (1 if (who == "friend" and mood > -0.2) or mood > 0.5 else 0)
    brow = "worried" if (sad > 0.35 or lid == "up") else ("glad" if glad > 0.5 or smile > 0.5 else "flat")
    happy_closed = lid == "closed" and eye == "closed" and (smile > 0.5 or mood > 0.65)
    return dict(lid=lid, mouth=mouth, blush=blush, brow=brow, glad=happy_closed)


def draw(canvas, who: str, x: float, y_feet: float, h: float, pose: Pose | None = None, facing: int = 1,
         tint: float = 0.0, alpha: float = 1.0, dissolve: float = 0.0, eye: str = "half", smile: float = 0.0,
         head_tilt: float = 0.0, wind: float = 0.0, t: float = 0.0, wind_dir: int | None = None,
         shadow: float = 0.35, cushion: bool = False, cushion_color=(0.55, 0.47, 0.52), seed: int = 0,
         mood: float | None = None, light=(-0.6, -0.8), rim=None, blink: bool = True, view: str = "three",
         phone: str | None = None, tray: bool = False, backpack: bool = False) -> dict:
    """Draw the child ('child') or the friend ('friend') as a pixel sprite; return anchors in canvas
    coordinates. See hx/kit/README.md for every parameter."""
    p = pose if pose is not None else stand()
    if isinstance(rim, (int, float)):                 # a bare strength: a pale warm edge light
        rim = ((0.93, 0.87, 0.76), float(rim))
    pr = CHILD if who == "child" else FRIEND
    X, Y, gx, gy = D.device_snap(canvas, x, y_feet)
    s = h / PX
    wd = (-facing if wind_dir is None else wind_dir)
    wind_l = float(wind) * wd * facing
    dis = float(min(1.0, max(0.0, dissolve)))
    m = float(DEFAULT_MOOD.get(who, 0.0) if mood is None else mood)
    face = _face_state(who, eye, smile, m, t, seed, blink, head_tilt)
    if view in ("front", "back_front"):
        from hx.kit import _fig_front
        B = D.Sprite(s, facing, light)
        fig = _fig_front.Front(who, p, pr, B, view=view, t=t, wind_l=wind_l, seed=seed, head_tilt=head_tilt,
                               face=face)
    else:
        B = D.Sprite(s, facing, light)
        fig = _Fig(who, p, pr, B, view=view, t=t, wind_l=wind_l, seed=seed, head_tilt=head_tilt, flat=False,
                   face=face)
    fig.build(cushion=cushion, phone=phone, tray=tray, backpack=backpack)
    j = fig.j
    anchors = _anchors(j, pr, X, Y, h, facing, B)
    if alpha <= 0.003:
        return anchors
    if shadow > 0:
        ground = [q for q in (j["A_n"], j["A_f"], j["K_n"], j["K_f"], j["P"]) if q[1] < 0.09]
        if ground:
            xs = [q[0] for q in ground]
            cx = 0.5 * (min(xs) + max(xs)) + 0.015
            wdt = (max(xs) - min(xs) + 0.26) * h
            contact_shadow(canvas, X + facing * cx * h, Y, wdt, shadow * alpha * (1 - 0.5 * dis), squash=0.16)
    rs = D.raster(B)
    if rs is None:
        return anchors
    mat, part, ox, oy = rs
    pal = _palette(who, tint, phone, cushion_color)
    rgb, a = D.finish(B, mat, part, pal, outline=s * 5 >= 40, rim=rim, inner=s * 5 >= 150)
    a = D.stipple(a, alpha, gx + ox, gy + oy)
    flecks = []
    if dis > 0:
        lee = (1 if wd > 0 else -1) if wind > 0.05 else -facing
        a, flecks = D.dissolve(rgb, a, dis, lee, t, seed, gx + ox, gy + oy)
    D.blit(canvas, rgb, a, X, Y, ox, oy)
    if flecks:
        m_ = canvas.getTotalMatrix()
        tx, ty = (m_.getTranslateX(), m_.getTranslateY()) if m_.isTranslate() else (0.0, 0.0)
        for fx_, fy_, c in flecks:
            canvas.drawRect(skia.Rect.MakeXYWH(fx_ * PX - tx, fy_ * PX - ty, PX, PX),
                            skia.Paint(Color=skia.Color(int(c[0]), int(c[1]), int(c[2]), 255)))
    return anchors


def _anchors(j, pr, X, Y, h, facing, B=None) -> dict:
    def c(q):
        return (float(X + facing * q[0] * h), float(Y - q[1] * h))
    R = pr.head
    hand_n = j["W_n"] + dirv(j["fore_n"]) * pr.hand * 0.5
    hand_f = j["W_f"] + dirv(j["fore_f"]) * pr.hand * 0.5
    eye = j["Hc"] + j["fh"] * 0.45 * R - j["uh"] * 0.12 * R
    out = {
        "head": c(j["Hc"]), "eye": c(eye), "top": c(j["Hc"] + j["uh"] * R * 1.40),
        "chest": c(j["C"] + np.array((j["d1"][1], -j["d1"][0])) * 0.05),
        "shoulder": c(j["S_n"]), "elbow_n": c(j["E_n"]),
        "hand_n": c(hand_n), "hand_f": c(hand_f), "hold": c((hand_n + hand_f) * 0.5),
        "foot_n": c(j["A_n"] - np.array((0, ANKLE))), "foot_f": c(j["A_f"] - np.array((0, ANKLE))),
        "hip": c(j["P"]), "seat": c(j["P"] - j["d0"] * 0.05),
        "ear": c(j["Hc"] - j["fh"] * 0.30 * R - j["uh"] * 0.15 * R),
    }
    if B is not None:
        for k in ("phone", "tray"):
            if k in B.marks:
                out[k] = c(B.marks[k])
    return out


# --------------------------------------------------------------------------------------------
# the hero wall shadow
# --------------------------------------------------------------------------------------------
def hero_shadow(canvas, x: float, y_base: float, h: float, rise: float, t: float, color=INK,
                alpha: float = 0.6, facing: int = 1, soft: float = 1.0):
    """Flat hard-edged wall shadow standing up, in ten steps, from the curled lump (rise 0) into a
    caped film hero about 1.45 h tall (rise 1) whose cape lifts in steps. `soft` is ignored."""
    r = float(min(1.0, max(0.0, rise)))
    e = _smooth(math.floor(r * 10 + 1e-6) / 10.0)
    tq = math.floor(t * 5.0) / 5.0
    pz = blend(curled(), hero_stand(), e)
    pr = _lerp_props(CHILD, HERO, e)
    hh = h * (1.0 + 0.45 * e)
    X, Y, gx, gy = D.device_snap(canvas, x, y_base)
    B = D.Sprite(hh / PX, facing, flat=True)
    fig = _Fig("child", pz, pr, B, view="three", t=tq, wind_l=-0.4 * e, seed=0, head_tilt=0.0, flat=True,
               face=None)
    fig.build()
    if e > 0.02:
        B.part(cast=False)
        B.fill(_cape(fig.j, e, tq), "flat", False)
    rs = D.raster(B)
    if rs is None:
        return
    mat = rs[0]
    a = np.where(mat > 0, 255, 0).astype(np.uint8)
    rgb = np.empty(mat.shape + (3,), np.uint8)
    rgb[...] = [int(round(v * 255)) for v in color]
    D.blit(canvas, rgb, a, X, Y, rs[2], rs[3], alpha_layer=alpha)


def _cape(j, e, t):
    """The hero's cape: hung from the shoulders, its free edge lifting and rippling in wind."""
    N, d2 = j["N"], j["d2"]
    f2 = np.array((d2[1], -d2[0]))
    back, down = -f2, -d2
    top_f = N - d2 * 0.02 + f2 * 0.04
    top_b = N - d2 * 0.03 - f2 * 0.06
    L = 0.62 * e * e
    lift = 0.12 + 0.38 * e + 0.08 * math.sin(t * 1.9) + 0.04 * math.sin(t * 3.7 + 1)
    pts = [top_f, top_b]
    n = 6
    for i in range(1, n + 1):
        u = i / n
        ang = lift * (0.3 + 0.7 * u)
        dvec = down * math.cos(ang) + back * math.sin(ang)
        pts.append(top_b + dvec * L * u + back * (0.05 * u + 0.025 * math.sin(t * 4.2 - u * 5.0) * u))
    tip = pts[-1]
    root = N + down * L * 0.92 + back * 0.03
    for u in (0.33, 0.66):
        pts.append(tip * (1 - u) + root * u + down * 0.03 * math.sin(t * 5.1 + u * 7) * e)
    pts.append(root)
    pts.append(N + down * L * 0.45 + back * 0.02)
    return np.array(pts)
