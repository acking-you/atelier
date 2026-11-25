"""s06_storm   138.20 - 158.86   c2a, c2b          B5  ->  B6

The storm at its worst, and then the turning of the film: the friend comes through it, crouches
before the child and holds out a hand; the child takes it.

CUE SHEET (lines by 0-based LRC index and time, paraphrased; no lyric text)
  138.20        B5: bare sheet, the child at X5, head down, the large cloud (first frame = S.handoff B5)
  c2a 138.20 - 150.10   the storm at its worst
  138.265 idx 41  (it has thought of leaving) the downbeat: the plain shoots out from the child (1.2 s), the
                  rain slants in (S.rain_k: 1.5 by 138.8), the cloud lifts off its head and opens into the lid
  138.365       the pull-back, 1.4 s, to the wide frame of land.tower_layout(X5, 2); it lands on the bar
                  line 139.765 (the strongest attack) with sheet lightning behind the lid, and goes on
                  very slowly to 144.2 (the last twelfth of the zoom): the child still getting smaller
  138.465       the child turns its back (0.55 s) and walks away into the mist, in place, a step a beat
                  (footfalls 139.765, 140.515 ..); its line goes a notch paler with every step (to 0.38; in
                  the wide frame never under 0.55, or the thin line is lost); mist thickens before it
  139.8 - 143.5 idx 42 (existing like this): the lid comes lower than in the first chorus (hang 235 ->
                  268 px) and bellies over the child; lightning again on the attacks 141.572 and 143.07
  144.265 idx 43  (because of the voices, the postures, the hurts) hit 1: the voices land (camera jolt,
                  a flash of the whole sheet); the knees give; the lid sags
  145.765       hit 2: the backs; the child squats; a belly of the lid starts down toward it
  146.515       an amber dotted trail runs in along the ground line from the right edge (a mark every
                  eighth of a beat): somebody has walked all that way
  147.265       hit 3: the house lands and cracks apart; the child sits, its forehead on its knees;
                  at the end of the trail the amber figure comes up (0.6 s), walking, leaning into the rain,
                  an arm before its face, a step a beat, leaving a mark for every step
  147.3 - 148.4 the belly comes down onto the bowed head
  148.0 - 148.75  its loops come down over the child, head and all: the body is gone under them, only the
                  round of the head shows, its own outline laid over the loops (148.5)
  147.515 - 151.765   the push in, ONE move, from the wide frame to the two-shot of B6 (it lands on the
                  bar line); the friend grows in it; the lid rises back to 235 px
  c2b 150.10 - 158.86
  150.265 idx 45  (it does not want to leave) the friend runs the last steps, brakes (151.02), crouches
                  before the child, not touching; the towers lose their pressure (150.265 - 151.765); the
                  friend's glow reaches the child (rim) and the loops that face it
  151.3         the child, under the loops: someone is there: a window opens in the loops inside the round
                  of its head and its eyes are there, sliding toward the friend; its line takes a notch back
  151.3 - 154.4   the friend waits with a soft, careful face (no grin); its smile opens with the take
  152.36  idx 46  (perhaps, having tried being loved) the open hand, low, at the edge of the loops (attack
                  152.364); the child's line stops fading; the camera creeps in on the two (152.515 -
                  154.395: heads 175 px); the child peeks: the window widens (152.7 - 153.25, on 153.124)
  153.35        the child's hand pushes out through the loops, stops, goes back in (153.68),
  154.395       comes out again and takes the hand (the strongest attack of the phrase): a pulse of
                  warmth on the hands; the loops over its face and knees fall away; amber rubs off on its
                  hand and runs up its forearm (154.45 - 155.5), stays there while they look up and soaks
                  into the rim of B6 (157.45 - 158.35); the rim on its right side and the glow on the hands stay
  154.70, 155.01  the friend's free hand brushes twice over the bowed head: first the hood of loops
                  goes back off the head, then all of it slides off the back, lies behind the child and
                  is rubbed away (by 156.1); the belly of the lid lifts (154.7 - 156.2), pale dust falls
                  from it, the strand is drawn out taut for a moment: the child is still tied
  154.84  idx 47  (one begins to look up toward the future) the child lifts its head (1.25 s, a blink on
                  the way), looks at the friend; its line comes back; the towers un-draw behind them
                  (154.765 - 157.2: voices, backs, house)
  155.6 - 157.0 the lid wears thin in ONE place above them; a guess of light under it
  156.265 - 158.3   the camera eases back to B6's frame while both look up (157.01, on the attack)
  158.61        B6 (S.joined): camera (4390, 590, 1.2); the plain, the lid with its thin pale place, the
                  child sitting, the friend crouched, hands joined, both looking up; rain 0.25

THE PERFORMANCE   D = AP.s06(F.t, t_turn=138.465, step=0.75): the turn follows the burst by a fifth of a
                  second, and the steps into the mist fall on the beats. The child's pressure is set here
                  (Act.a), the kit's curve taken in steps.
PAINT ORDER       plain, mist, far rain . the guess of light . ground line . amber trail . the three groups .
                  lightning . the lid and the strand (after the figures until 140.6, while the cloud still
                  lies on the head) . the two . the touch, the amber on the forearm . the loops over the
                  child (windows for its eyes and the two hands) . the round of its head over them . the
                  friend's light on them . the mist it walked into . near rain . flash (the hits; a little
                  with each lightning)
"""
import math

import numpy as np

from hx import story
from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk import acting_pair as AP
from hx.chalk.figure import _head_frame                  # (where the eyes sit in a head: for the window in the loops)

from . import _shared as S

SPAN = (138.20, 158.86)
START, END = "B5", "B6"

X5, FLOOR = story.X5, story.FLOOR
HITS = story.HITS_2
CLOUD5 = story.HANDOFF["B5"]["cloud"]
AX = CLOUD5[0]                                           # the lid's anchor to the end of s06 (4270)
L2 = tower_layout(X5, 2)
CAM5, CAM6, WIDE = S.CAM[START], S.CAM[END], L2.cam
CLOSE = Cam(X5 + 92.0, 562.0, 1.5)                       # the hand: heads 175 px

PERF = dict(t_turn=138.465, step=0.75)
T_BURST = 138.265
T_PULL = (138.365, 139.765)
T_DRIFT = (139.0, 144.2)                                 # ... and goes on, very slowly, while the child walks away
T_PUSH = (147.515, 151.765)
T_CREEP = (152.515, 154.395)
T_BACK = (156.265, 158.30)
T_TAKE, T_LIFT, T_UP, T_ENTER, T_RUN = 154.40, 154.84, 157.01, 147.265, 150.265
T_THIN = (155.6, 157.0)
T_OFF = 154.765                                          # the towers un-draw from here
HANG_LOW = 268.0


def _jolt(t: float) -> float:
    return sum(math.exp(-(t - h) / 0.09) * math.cos((t - h) * 38.0) for h in HITS if 0.0 <= t - h < 0.6)


def _cam(t: float) -> Cam:
    if t < T_PUSH[0]:
        c = Cam.lerp(CAM5, WIDE, 0.925 * ease(seg(t, *T_PULL)) + 0.075 * ease(seg(t, *T_DRIFT)))
    elif t < T_CREEP[0]:
        c = Cam.ease(WIDE, CAM6, seg(t, *T_PUSH))
    elif t < T_BACK[0]:
        c = Cam.ease(CAM6, CLOSE, seg(t, *T_CREEP))
    else:
        c = Cam.ease(CLOSE, CAM6, seg(t, *T_BACK))
    j = _jolt(t)                                         # the three hits (the last dies away under the first frames of the push in)
    return Cam(c.cx, c.cy + 30.0 * j / c.zoom, c.zoom * (1.0 + 0.016 * j)) if j else c


# sheet lightning inside the lid while the storm is at its worst: (attack, screen x, strength); it swells in a fifth
# of a second and dies away (the three hits have their own flash of the whole sheet)
_BOLTS = ((139.765, 1280.0, 1.0), (141.572, 400.0, 0.7), (143.07, 1560.0, 0.85))


def _bolt(t: float) -> float:
    """How much sheet lightning there is (0..about 0.8): the strength of the flicker of the whole sheet."""
    return sum(k * _flick(t, tb) for tb, _, k in _BOLTS)


def _flick(t: float, tb: float) -> float:
    return sum(q * ramp(t, tb + d - 0.1, tb + d + 0.1) * math.exp(-max(0.0, t - tb - d) / 0.26) for d, q in ((0.0, 1.0), (0.3, 0.55)))


def _lightning(F) -> None:
    for tb, sx, k in _BOLTS:
        e = _flick(F.t, tb)
        if e > 0.01:
            with F.screen():
                smudge(F, sx, 250.0, 640.0, 280.0, C.MOON, 0.85 * k * e, "glow", additive=True)
                smudge(F, sx + 60.0, 280.0, 260.0, 150.0, C.MOON, 0.70 * k * e, "glow", additive=True)


def _trail():
    """The friend's way in: the dotted trail from the right edge of the wide frame to where it comes
    up (a mark every eighth of a beat, 146.515 to 147.265), and a mark for every step it takes."""
    xa, xb, n = X5 + 6100.0, X5 + 1085.0, 34
    i = np.arange(n)
    steps = (148.015, 148.765, 149.515, 150.265, 150.525, 150.765)
    return ((xa + (xb - xa) * i / n, 146.515 + (T_ENTER - 146.515) * i / n),
            (np.asarray([AP.s06(tb, **PERF).friend.x for tb in steps]), np.asarray(steps) + 0.12))


_TRAIL = _trail()


# ---------------------------------------------------------------------------------------------
# the loops let down over the child (148.5), and how they come off it again
# ---------------------------------------------------------------------------------------------
_SH_DX = np.linspace(-176.0, 124.0, 76)                  # world x from the child's ground point
_SH_S = 0.45                                             # their hand: small loops, pressed hard (the shawl's)
_G = FLOOR + 4.0


def _prof(*pts):
    xs, ys = zip(*pts)
    y = np.interp(_SH_DX, xs, ys)
    y = np.convolve(np.pad(y, 2, mode="edge"), np.ones(5) / 5.0, mode="valid")           # a hand does not rule its edges
    return np.minimum(_G, y + 7.0 * (2.0 * vn(_SH_DX / 31.0 + 3.7, 41) - 1.0) * np.clip((_G - y) / 40.0, 0.0, 1.0))


# the upper edge of the loops over the child sitting at dx = 0 (its bowed head: centre (36, -138), radius 59;
# hips -23, knees +22, toes +86), as world y: a bell hanging from the belly that rests on its head, over the whole
# head (its round is laid over it, a window keeps the eyes) and down in front of the face to the toes
_P_FULL = _prof((-176, _G), (-150, _G), (-140, 690), (-126, 596), (-108, 540), (-84, 522), (20, 518), (58, 524), (82, 548), (98, 590),
                (106, 644), (110, 700), (114, _G), (124, _G))
_P_OPEN = _prof((-176, _G), (-150, _G), (-140, 690), (-126, 596), (-108, 540), (-84, 522), (20, 526), (30, 630), (40, _G), (100, _G))
_P_BACK = _prof((-176, _G), (-158, _G), (-146, 700), (-128, 640), (-100, 612), (-62, 618), (-34, 664), (-14, _G), (100, _G))
_P_HEAP = _prof((-176, _G), (-168, 716), (-150, 684), (-124, 668), (-98, 676), (-74, 704), (-58, _G), (100, _G))


def _shroud(F, x: float, down: float, front: float, hood: float, off: float, gone: float, avoid) -> None:
    """The loops of the lid's belly lying over the sitting child at ground x (drawn after it): its
    body and its head are gone under them (the scene lays the head's outline over them, and keeps a
    window for the eyes and a way out for the hand: avoid). down 0..1: let down from the belly to
    the ground; front: the part over the knees fallen away (the hand came out); hood: pushed back
    off the head (the first brush); off: slid off the back onto the ground (the second); gone: what
    lies there rubbed away. The same scribble (seed, churn), its strokes following the band."""
    if down <= 0.0 or gone >= 1.0:
        return
    top = _P_FULL + (_P_OPEN - _P_FULL) * front
    top = top + (_P_BACK - top) * hood
    top = top + (_P_HEAP - top) * off
    bot = top + (_G - top) * down
    dx = -30.0 * off
    B = Band(x + _SH_DX + dx, top, bot, AX + dx, _SH_S, floor=FLOOR + 3.0)
    mass(F, B, story.GLOOM_SEED, 1.0 - ramp(gone, 0.75, 1.0), (ease(gone), 1.0), core=1.0 - 0.8 * off, halo=1.0 - 0.6 * off,
         avoid=avoid if hood < 1.0 else ())


def _eyes_at(act, J):
    """World centres of the child's face and of its two eyes as the figure draws them (figure._face:
    the features sit about (ftx R, (0.10 - ly 0.34) R) in the head's own frame, the eyes sep to
    either side): (middle, eye one, eye two)."""
    P = act.pose
    ha, fw, dn, chh, shh, ly, ub, sg = _head_frame(P, solve(P), act.face)
    R = J["R"]
    ftx = sg * (0.40 * P["look"][0] * abs(chh) + 2.0 * ub)
    sep = 0.37 * R * (1.0 - 0.42 * min(1.0, abs(P["look"][0] * chh)))
    mid = J["head"] + fw * (ftx * R) + dn * ((0.10 - ly * 0.34) * R)
    return mid, mid - fw * sep, mid + fw * sep


def _head_line(F, act, J, a: float) -> None:
    """The round of the child's head laid over the loops that cover it: the very stroke figure()
    draws for its outline (same blob, seed, width, wobble, grain), so that nothing doubles or jumps
    when the loops leave the head and the figure's own line takes over."""
    if a <= 0.0:
        return
    P, h, face = act.pose, act.h, act.face
    hs = h * F.cam.zoom
    ha = _head_frame(P, solve(P), face)[0]
    hc, R, sd0 = J["head"], J["R"], act.seed * 97
    hp = blob(hc[0], hc[1], R * 1.03, R * 0.975, sd0 + 31, rough=0.022, n=34, rot=face * ha)
    sk = CHILD_NIGHT
    chalk(F, np.vstack([hp, hp[1:4]]), sk.line, 0.017 * h, a, sd0 + 34, min(1.15, max(0.16, hs / 300.0)) * 0.85 / F.cam.zoom * 0.7,
          taper=0.75, edge=sk.edge * ramp(hs, 84.0, 130.0), step=6.0 if hs >= 150 else 3.0, grain=sk.grain, floor=1.5)


def draw(F):
    if S.joined(F, START, END):                          # the last 0.25 s: the hand-off picture B6
        return
    t = F.t
    D = AP.s06(t, **PERF)
    c, f = D.child, D.friend
    if f is not None:
        # while it waits with its hand held out it does not grin: a soft, careful face (the kit's is a smile);
        # the smile opens with the take
        wt = F.ramp(151.3, 151.9) * (1.0 - F.ramp(T_TAKE + 0.1, T_TAKE + 0.6))
        if wt > 0.0:
            P = f.pose
            f.pose = P.but(mouth=P["mouth"] + (0.22 - P["mouth"]) * 0.75 * wt, brow=P["brow"] + (0.40 - P["brow"]) * 0.8 * wt,
                           lift=P["lift"] * (1.0 - 0.6 * wt))
    F.cam = _cam(t)
    zoom = F.cam.zoom
    # its pressure: it goes a notch with every step into the mist (the beats 139.765 .. 144.265); far away the thin
    # line would be lost under 0.55; it stops fading when the hand is held out and comes back from the take (the kit's)
    gone = sum(F.ramp(139.765 + 0.75 * i, 140.065 + 0.75 * i) for i in range(7)) / 7.0
    back = 1.0 - (1.0 - 0.3 * F.ramp(152.4, T_TAKE)) * (1.0 - F.ramp(T_TAKE, T_UP))
    notice = 0.10 * F.ramp(151.25, 151.75) * (1.0 - back)      # someone is there: its line takes a notch back
    c.a = max(1.0 - 0.62 * gone + 0.62 * back + notice, (0.55 - 0.17 * ramp(zoom, 0.3, 0.9)) * F.ramp(138.3, 139.0))
    Jc = c.joints()
    Jf = f.joints() if f is not None else None
    head = (float(Jc["head"][0]), float(Jc["head"][1]), float(Jc["R"]))
    crown = Jc["crown"]

    # ---- the plain shoots out from the child; mist; far rain ---------------------------------
    k_rain = S.rain_k(t) if t < 157.6 else story.HANDOFF[END]["rain"]      # (rain_k ends a rounding short of B6's 0.25: a drop)
    r = 7600.0 * ease_out(F.seg(T_BURST, T_BURST + 1.2), 2.2)
    S.plain_base(F, X5, k_rain, a=F.ramp(T_BURST, T_BURST + 0.25), reach=(X5, r) if r < 7600.0 else None)
    thin = F.ramp(*T_THIN)
    if thin > 0.0:
        S.sky_gap(F, thin)
    ground_line(F)

    # ---- the amber trail along the ground line: the way the friend has come ----------------------
    if 146.4 < t < 153.3:
        footsteps(F, *_TRAIL[0], s=2.3, a=1.0 - F.ramp(149.6, 151.0), col=C.AMBER, face=-1, life=9.0, rest=0.45)
        footsteps(F, *_TRAIL[1], a=0.9 * (1.0 - F.ramp(151.2, 153.2)), col=C.AMBER, face=-1, life=7.0, rest=0.3)

    # ---- the three groups ---------------------------------------------------------------------
    if HITS[0] - 0.1 < t < T_OFF + 2.5:
        T = towers(L2)
        T.house = tower_house(L2, split=house_crack(t, HITS[2], L2.house["split"]))
        T.hit(HITS)
        T.off(T_OFF, 2.4)
        k = F.ramp(T_RUN, 151.765)
        T.draw(F, a=1.0 - 0.62 * k, thin=1.0 - 0.48 * k, dark=1.0 - F.ramp(151.0, 156.5))

    # ---- the scribble: the cloud opens into the lid; its belly comes down; the thin place --------
    w = seg(t, T_BURST, 139.9)
    lifted = ease(seg(w, 0.0, 0.3))
    hang = 235.0 + (HANG_LOW - 235.0) * (F.ramp(139.8, 143.5) - F.ramp(T_PUSH[0], T_PUSH[1]))
    cower = (0.3 * F.ramp(140.5, 144.0) + 0.7 * D.num["cower"]) * (1.0 - F.ramp(154.9, 156.2))
    sack = (0.22 * F.ramp(HITS[1], HITS[1] + 0.8) + 0.78 * F.ramp(HITS[2], HITS[2] + 1.15)) * (1.0 - F.ramp(154.70, 156.2))
    lid_cam = F.cam if t < T_PUSH[1] else CAM6
    s = 1.0 / lid_cam.zoom
    kw = {}
    if w < 1.0:
        kw.update(cloud=band_cloud(*CLOUD5, rest=(crown[0], crown[1] + 6.0, 1.0 - lifted)), spread=w)
    if cower > 0.0:
        kw.update(sag=(X5 + 40.0, 80.0 * s * cower, 600.0 * s))
    if sack > 0.0:
        kw.update(rest=(head[0], head[1] - head[2] + 8.0, sack))
    avoid = []
    hole = 1.0 - seg(w, 0.45, 0.8)
    if hole > 0.0:
        avoid.append((head[0], head[1], head[2] * hole))
    if Jf is not None:
        # (while the belly's dark lies behind the friend's head the hole is the head's own size, or it shows as a ring)
        avoid += S.clear_of(Jf, k=F.ramp(150.3, 151.0) * (0.78 + 0.22 * F.ramp(155.2, 156.4)))
    taut = F.ramp(154.95, 155.45) * (1.0 - F.ramp(155.9, 157.3))        # the strand is drawn out as the belly lifts: it is still tied
    before = t >= 140.6                                  # the lid behind the figures once it has lifted clear of the child

    def lid():
        Tp = S.lid(F, AX, None, thin=thin, hang=hang, cam=lid_cam, avoid=avoid, **kw)
        strand(F, crown, Tp.band.root(crown[0] + 40.0, 0.4 - 0.1 * w), slack=0.8 - 0.55 * taut)
        return Tp

    _lightning(F)                                        # behind the lid: its loops stand before the light
    if before:
        Tp = lid()
        lift = F.ramp(154.8, 155.5) * (1.0 - F.ramp(156.5, 157.5))            # pale dust as the belly lifts off them
        if lift > 0.0:
            gloom_dust(F, X5 - 160.0, X5 + 300.0, 0.0, fall=200.0, n=26, band=Tp.band, a=0.7 * lift, seed=78)

    # ---- the two --------------------------------------------------------------------------------
    warm = D.num["warm"]
    near = F.ramp(150.6, 151.8) if f is not None else 0.0
    rim = S.amber_rim(0.22 * near + 0.28 * warm) if near > 0.0 else None
    far = 0.0 if f is None else ramp(f.h * zoom, 80.0, 240.0)
    S.pair(F, D, child_rim=rim, glow=0.6 + 0.4 * far, wet=1.0 - 0.4 * F.ramp(152.5, 157.6), warm=warm)

    if not before:
        Tp = lid()
        dust = 0.5 * (1.0 - F.ramp(T_BURST, T_BURST + 0.6))
        if dust > 0.0:
            gloom_dust(F, CLOUD5[0] - 0.8 * CLOUD5[2], CLOUD5[0] + 0.8 * CLOUD5[2], 0.0, band=Tp.band, a=dust)

    # ---- the touch: a pulse of warmth where the hands meet (on the attack 154.395) -----------------
    pulse = F.ramp(T_TAKE - 0.1, T_TAKE + 0.1) * math.exp(-max(0.0, t - T_TAKE) / 0.4)
    if pulse > 0.004 and D.pts["hands"] is not None:
        glow(F, D.pts["hands"][0], D.pts["hands"][1], 120.0, a=0.34 * pulse)

    # ---- amber rubs off on its hand and runs a little way up its forearm -----------------------
    # (it stays on the arm while they look up and soaks into the rim of B6 as the camera settles: gone by 158.35)
    am = 1.0 - F.ramp(157.45, 158.35)
    if 0.0 < warm and am > 0.0:
        u = np.linspace(0.0, 0.62, 12)[:, None]
        P = Jc["ha_f"][None, :] * (1.0 - u) + Jc["el_f"][None, :] * u
        chalk(F, P, C.AMBER, 7.5, 0.9 * am, seed=57, wob=0.5, taper=0.7, edge=0.2, draw=ease_out(F.seg(T_TAKE + 0.05, T_TAKE + 1.1), 2.0),
              boil=0)

    # ---- the loops over the child, and their going ---------------------------------------------
    down = F.ramp(148.015, 148.765)
    if down > 0.0 and t < 156.2:
        b = D.num["brush"]
        R = head[2]
        # its eyes in the round of the head: when the child knows someone is there (151.3) the loops part over its two
        # eyes; as it peeks out at the open hand (152.6 - 153.15, on the attack 153.124) they part over its face; the
        # first brush pushes the hood back: the window becomes the whole head
        mid, e1, e2 = _eyes_at(c, Jc)
        k = F.ramp(152.6, 153.15)                                   # the two openings run together over the face
        er = R * (0.22 * F.ramp(151.25, 151.6) + 0.42 * k)
        u = ease(min(1.0, b / 0.6))
        hc = np.array(head[:2])
        avoid = [tuple(map(float, e + (mid - e) * k + (hc - (e + (mid - e) * k)) * u)) + (er + (1.06 * R - er) * u,) for e in (e1, e2)]
        reach = ramp(float(Jc["ha_f"][0]) - c.x, 57.0, 72.0)          # the hand pushing out through the loops
        if reach > 0.0:
            avoid.append((float(Jc["ha_f"][0]), float(Jc["ha_f"][1]), 0.042 * c.h * reach))
        if Jf is not None:                                         # the friend's open hand is not under the child's loops
            avoid.append((float(Jf["ha_f"][0]), float(Jf["ha_f"][1]), 0.05 * f.h))
        _shroud(F, c.x, down, front=F.ramp(T_TAKE - 0.05, T_TAKE + 0.33), hood=ease(min(1.0, b)), off=ease(max(0.0, b - 1.0)),
                gone=F.seg(155.25, 156.15), avoid=[q for q in avoid if q[2] > 0.5])
        _head_line(F, c, Jc, 0.85 * c.a * ramp(down, 0.15, 0.5) * (1.0 - 0.5 * F.ramp(T_TAKE - 0.05, T_TAKE + 0.33)) * (1.0 - ramp(b, 0.3, 0.65)))     # only the round of its head shows

        if near > 0.0 and b < 2.0:                         # the friend's light on the loops that face it
            glow(F, c.x + 74.0, FLOOR - 92.0, 150.0, 120.0, a=0.16 * near * (1.0 - 0.5 * b))

    # ---- the mist it walks into; the near rain; the flash of each hit ---------------------------
    d = 0.6 * F.ramp(139.0, 144.0) * (1.0 - F.ramp(T_RUN, 152.0))
    if d > 0.0:
        mist(F, slab=(0.0, d))
    S.rain_front(F, k_rain)
    fl = 0.22 * sum(decay(t - h, 0.16) for h in HITS) + 0.06 * _bolt(t)       # the hits; the lightning lights the sheet a little
    if fl > 0.001:
        flash(F, fl)
