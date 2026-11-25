"""s08_part   182.30 - 201.25   bd, hush2 (to the slam)          B7  ->  B8

The set-back before the release, and the long silence. The high cloud comes down again as a curtain
all round the two; the child pales and sits; the friend fights the dark open with its whole body; a
shaft of pale light falls through the gap onto the child, who lifts its head into it and stands;
in the silence the child puts its own hands up beside the friend's and both hang back on the strands.

CUE SHEET (song's clock; lines by 0-based LRC index, paraphrased; no lyric text)
  182.30        B7: the first frame is S.handoff(F, "B7"): close two-shot (4390, 500, 1.3), the friend's hand
                on the child's upper arm, the high cloud (its loops kept off the heads), the first hill
  182.50        the friend looks up; 182.75 the child looks up (AP.s08)
  182.60-184.81 the camera pulls back to B8's frame (4390, 470, 0.85), landing on line 53
  182.75-183.75 the high cloud opens out across the sky into the lid (S.curtain spread; its lid follows the
                pull back, then hangs as B8 has it)
  183.12 idx 52 (thoughts of leaving) the lid comes down: tongues of dark fall to the ground all round
                them (drop 183.0 - 185.14, a heavy fall); 183.3 the child's eyes go dull, its head sinks
  183.60-185.10 the friend's amber warmth leaves the child (rim and the glow at the hand), its line pales
  184.34        attack: the friend's arm thrown up against the falling dark (a puff of pale dust where it hits)
  184.81 idx 53 (the light gives way to haze) the last pale strip of horizon is gone: the curtain hangs
                to the ground all round them
  185.14        attack: the friend is pressed down, its hand leaves the child; 184.9-186.3 the child squats and
                sits where it stood, forehead on its knees (its feet stay planted)
  185.40-186.02 the friend turns its back to us, toward the curtain
  186.26 186.65 attacks: two shoves with both hands; each time the curtain gives a strand's width at the seam,
                a hair of light shows above its head, and it falls shut again; dust shaken out
  187.56        attack: it finds the seam and plunges both hands in (the grips; the fringe of strands)
  187.84 idx 54 (surprise at how hard the friend fights to part it)
  188.14        attack: a heave apart: two strands come aside, the light opens; 188.45 it slips, a foot shoots
                out, the opening half closes; it plants its feet again
  188.90        attack: the great heave: four strands a side; the shaft opens (lit), and its light swings out of
                the gap onto the child (188.90-189.40), a pool on the ground round it; the strands under load
                tremble; the camera pushes in on the child (188.90-190.50, head 151 px)
  189.60        the child stirs and lifts its head into the light (the full head lift, 1.25 s): its face catches
                it; 190.95 it looks at the friend's straining back
  191.00-192.95 the camera eases back to B8's frame while the child stands (191.32-191.88, feet planted) and
  191.90        the friend heaves once more on the strong attack
  192.20-193.00 the held strands calm (tremble 1.8 -> 0.5); the camera is still from 192.95 to the end
  hush2 193.00-201.25 TRUE SILENCE: the boil is held; what moves is the two figures, their hands shivering on
                still edges (S.calm_grips), the dust in the shaft on the true time
  193.20-195.40 the friend holds on tiptoe, sagging slowly; the child watches, half lifts a hand (194.4) and
                lets it sink
  195.50-196.80 the child puts first one hand, then both, up on the left bunch beside the friend's
  196.90        the friend's relief; it lets that side go
  197.20-198.25 both turn under their bunches (turning steps, a foot at a time) and walk them outward; the
                opening comes over the child: the bent light becomes the shaft (197.3-198.8); both hang back
  199.10        a look over the shoulders
  200.20        a breath in; 200.62 they pull once more (the measured attack 200.78 falls in the pull),
                held from 200.88
  201.00        B8 (S.joined): the parted curtains held by four hands, the shaft, dust on the true time

THE PERFORMANCE   D = AP.s08(F.t) as written (cue table AP.S08_T), with the feet pinned here (see _feet).
THE SCRIBBLE      one S.curtain call from the first frame, behind the two (at spread = drop = 0 it is B7's
                  cloud); its loops are kept off the heads by gloom's own avoid clip until the dark is down.
                  The grips are S.calm_grips throughout (the edges never shiver; the hands do).
THE LIGHT         the opening's own gap_light (S.curtain's, drawn here so that the dust runs on the true time
                  from its first frame), and a fan of the same light bent out of the gap over the child while
                  the opening lies right of it; the shaft rim on both (B8's), a glow on the child's face.
PAINT ORDER       plain base . hill ground . gap light . curtains . bent light . dust puffs . the two . face glow
"""
from functools import lru_cache

import numpy as np
import skia

from hx import story
from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk import acting_pair as AP

from . import _shared as S

SPAN = (182.30, 201.25)
START, END = "B7", "B8"

X5, FLOOR = story.X5, story.FLOOR
CAM7, CAM8 = S.CAM[START], S.CAM[END]
CLOSE = Cam(4300.0, 560.0, 1.28)                         # the head lift into the shaft: head 151 px

A = AP.S08_T["attacks"]
T_CLEAR = (183.40, 184.00)                               # the loops kept off the heads (B7) until the dark comes down behind them
T_SPREAD = (182.75, 183.75)                              # the cloud opens out into the lid
T_DROP = (183.00, 185.14)                                # the lid comes down to the ground all round them
T_BACK = (182.60, 184.81)                                # the pull back to B8's frame
T_IN = (188.90, 190.50)                                  # push in on the child in the shaft
T_OUT = (191.00, 192.95)                                 # back to B8's frame as it stands
T_WARM = (183.60, 185.10)                                # the friend's warmth leaves the child (the hand is off at A[1])
T_SWEEP = (188.90, 189.40)                               # the beam swings from the opening onto the child
T_UNBEND = (197.30, 198.80)                              # the opening has come over the child: the beam is the shaft
T_CALM = (192.20, 193.00)                                # the held strands calm down before the silence
AIM = 4200.0                                             # where the bent beam lands: its axis passes the lifted head and the standing one
SHOVES = ((A[2], 1.1, 410.0), (A[3], 1.4, 394.0))       # the curtain gives under the two shoves (strands a side) and swings back
PRE_Y = 346.0                                            # where the hands will go in (LG / RG at A[4])

BENT = dict(half=150.0, a=0.20, soft=0.8)                # the bent light: how far past AIM, strength, penumbra


def _cam(t):
    if t < T_IN[0]:
        return Cam.ease(CAM7, CAM8, seg(t, *T_BACK))
    if t < T_OUT[0]:
        return Cam.ease(CAM8, CLOSE, seg(t, *T_IN))
    return Cam.ease(CLOSE, CAM8, seg(t, *T_OUT))


def _shove(t):
    """How far the curtain gives under the shoves (strands a side) and the height of the hands."""
    p = max(k * ease(seg(t, ta - 0.10, ta + 0.10)) * (1.0 - ease(seg(t, ta + 0.14, ta + 0.70))) for ta, k, _ in SHOVES)
    (t1, _, y1), (t2, _, y2) = SHOVES
    return p, y1 + (y2 - y1) * ease(seg(t, t2 - 0.10, t2 + 0.10))


# dust shaken out of the curtain where the friend's hands hit it: (attack, world x, world y)
_PUFFS = ((A[0], 4392.0, 380.0), (A[2], 4400.0, 410.0), (A[2], 4560.0, 410.0), (A[3], 4390.0, 394.0), (A[3], 4566.0, 390.0),
          (A[4], 4480.0, 346.0), (A[5], 4422.0, 368.0), (A[5], 4538.0, 368.0))


def _puffs(F, t):
    col = (0.62, 0.68, 0.84)
    for j, (ta, x, y) in enumerate(_PUFFS):
        u = t - ta + 0.06
        if u <= 0.0 or u > 1.6:
            continue
        i = np.arange(12)
        vx = 70.0 * (htab(i, 7, 300 + j) - 0.5)
        vy = 20.0 + 40.0 * htab(i, 11, 310 + j)
        fall = vy * u + 90.0 * u * u
        xs = x + 26.0 * (htab(i, 5, 320 + j) - 0.5) + vx * u
        ys = y + 20.0 * (htab(i, 3, 330 + j) - 0.5) + fall
        k = ramp(u, 0.0, 0.2) * (1.0 - ramp(u, 0.6, 1.6))
        specks(F, xs, ys, 1.2 + 1.4 * htab(i, 17, 340 + j), col, 0.8 * k, "dense")


# ---------------------------------------------------------------------------------------------
# planted feet (work-rounds for acting_pair.s08): the child sits down and stands up where it stands
# without its feet sliding; the friend's feet do not shuffle in and out on the shoves; in the two
# turning steps (197.2) a foot travels to where it lands instead of jumping there at the half-way point
# ---------------------------------------------------------------------------------------------
T_TURN = AP.S08_T["turn"]
SIT_PIN = (183.60, 191.35, 191.75)                       # feet held from here; let go to the standing pose's over the rise
F_TURN0 = (A[1] + 0.26, A[1] + 0.88)                     # the friend's turn to the curtain (written mirrored until its middle)
F_HOLD = (186.05, 187.85)                                # the friend's feet stay where its turn put them through the shoves
C_TURN = (T_TURN, T_TURN + 1.00)                         # the windows of acting_pair's two turning steps
F_TURN = (T_TURN + 0.05, T_TURN + 1.05)


def _ankles(act):
    J = act.joints()
    return float(J["an_f"][0]), float(J["an_b"][0])


@lru_cache(maxsize=1)
def _feet_plan():
    c = lambda u: AP.s08(u).child                        # noqa: E731
    f = lambda u: AP.s08(u).friend                       # noqa: E731
    return dict(sit=(_ankles(c(SIT_PIN[0])), _ankles(c(SIT_PIN[2] + 0.05))), shove=_ankles(f(F_HOLD[0])),
                fturn0=(_ankles(f(F_TURN0[0] + 1e-4)), _ankles(f(F_TURN0[1] - 1e-4))),
                cturn=(_ankles(c(C_TURN[0] + 1e-4)), _ankles(c(C_TURN[1] - 1e-4))),
                fturn=(_ankles(f(F_TURN[0] + 1e-4)), _ankles(f(F_TURN[1] - 1e-4))))


def _pin(act, xf, xb):
    """The Act with its two ankles at world x xf, xb (their heights as the pose has them)."""
    P = act.pose
    for k, wx in (("f", xf), ("b", xb)):
        P = aim_foot(P, k, ((wx - act.x) / (act.face * act.h), P["f" + k][1] + 0.014))
    act.pose = P


def _step(act, t, win, ends):
    """A turning step: the near foot travels to its place in the first half while the far one stands,
    then the far foot travels while the near one stands (the rig lifts each in its half)."""
    w = (t - win[0]) / (win[1] - win[0])
    if not 0.0 < w < 1.0:
        return
    (f0, b0), (f1, b1) = ends
    if w < 0.5:
        _pin(act, f0 + (f1 - f0) * ease(w / 0.5), b0)
    else:
        _pin(act, f1, b0 + (b1 - b0) * ease((w - 0.5) / 0.5))


def _feet(D, t):
    P = _feet_plan()
    if SIT_PIN[0] < t < SIT_PIN[2]:
        (f0, b0), (f1, b1) = P["sit"]
        k = ease(seg(t, SIT_PIN[1], SIT_PIN[2]))
        _pin(D.child, f0 + (f1 - f0) * k, b0 + (b1 - b0) * k)
    w = (t - F_TURN0[0]) / (F_TURN0[1] - F_TURN0[0])
    if 0.0 < w < 1.0:                                    # in place: one foot steps across while the other stands, then the other
        (sf, sb), (ef, eb) = P["fturn0"]                 # (face -1 at the start: its "b" foot moves first; face +1 at the end)
        if D.friend.face < 0:
            _pin(D.friend, sf, sb + (ef - sb) * ease(w / 0.5))
        else:
            _pin(D.friend, ef, sf + (eb - sf) * ease((w - 0.5) / 0.5))
            # written for face +1 from the middle of the turn on, but its sway still has the sign of the other way of
            # writing it (swap_sides leaves sway as it is): the scarf's tails would jump across; negated they swing
            # over to hang down its back (sway is 0 at the end of the turn)
            D.friend.pose = D.friend.pose.but(sway=-D.friend.pose["sway"])
    if F_HOLD[0] < t < F_HOLD[1]:
        _pin(D.friend, *P["shove"])
    _step(D.child, t, C_TURN, P["cturn"])
    _step(D.friend, t, F_TURN, P["fturn"])


def draw(F):
    if S.joined(F, START, END):                          # the last 0.25 s: the hand-off picture B8
        return
    t = F.t
    D = AP.s08(t)
    _feet(D, t)
    F.cam = _cam(t)
    gl, gr = S.calm_grips(D, t)
    if gl is None:                                       # before the hands are in: the curtain gives a little under the shoves
        sh, sy = _shove(t)
        if sh > 0.0:
            sw0 = STRAND_W * lid_for(CAM8, hang=PART_HANG)["s"]
            gl, gr = (S.SEAM - sh * sw0, sy), (S.SEAM + sh * sw0, sy)
    lit = D.num["lit"]
    ccam = F.cam if t < T_BACK[1] else CAM8              # the lid follows the pull back, then hangs where B8 has it

    S.plain_base(F, X5, 0.0, hill=True)
    S.hill_ground(F)
    clear = 1.0 - ease(seg(t, *T_CLEAR))
    if gl is not None:                                   # the light through the opening (S.curtain's own, drawn here)
        G = curtain_gap(ccam, S.SEAM, None, gl, gr, s=lid_for(ccam, hang=PART_HANG)["s"])
        come = F.ramp(A[4] - 0.01, A[4] + 0.20) if t >= A[4] - 0.01 else 1.0       # (the hair of light as the hands go in: 6 frames)
        gap_light(F, *G, a=(0.45 + 0.55 * lit) * come, open_=min(1.0, G[4] / 40.0), t=t)
    # the scribble: B7's high cloud opens into the lid and comes down as the curtains (one call from the first frame,
    # behind the two); its loose loops are kept off the heads as high_cloud keeps them until the dark has come down
    # behind them (S.curtain has no avoid=: the same clip that gloom's avoid= makes, round the whole call)
    cl, cr = (gl, gr) if gl is not None else ((S.SEAM, PRE_Y), (S.SEAM, PRE_Y))     # (grips on the seam: the fringe hangs there)
    trem = S.B8_TREMBLE + 1.3 * F.ramp(A[4], A[5]) * (1.0 - F.ramp(*T_CALM))          # the strands under load; calm for the silence
    discs = S.clear_of(D.child.joints(), D.friend.joints(), k=clear)
    if discs:
        F.c.save()
        for ox, oy, rr in discs:
            sx, sy = F.cam.to_screen(ox, oy)
            P = skia.Path()
            P.addCircle(float(sx), float(sy), float(rr * F.cam.zoom))
            F.c.clipPath(P, skia.ClipOp.kDifference, True)
    S.curtain(F, cl, cr, trem, light=0.0, spread=seg(t, *T_SPREAD), drop=ease(seg(t, *T_DROP)), cam=ccam)
    if discs:
        F.c.restore()
    # the beam: the light through the gap bent onto the child while the opening lies right of it
    k_sp = lit * (1.0 - F.ramp(*T_UNBEND))
    if k_sp > 0.0:
        G0 = curtain_gap(ccam, S.SEAM, None, gl, gr, s=lid_for(ccam, hang=PART_HANG)["s"])
        sw = ease(F.seg(*T_SWEEP))
        xr = G0[3] + G0[4]                               # the fan keeps the shaft's right edge; its left edge swings out past the child
        xl = (G0[3] - G0[4]) + (AIM - BENT["half"] - (G0[3] - G0[4])) * sw
        shaft(F, G0[0], G0[1], G0[2], 0.5 * (xl + xr), 0.5 * (xr - xl), FLOOR, a=BENT["a"] * k_sp,
              alphas=(0.3, 0.55, 0.85, 1.0), soft=BENT["soft"], top=0.4)
        light_pool(F, AIM + 40.0, FLOOR + 6.0, 210.0, a=0.30 * k_sp * sw)
    _puffs(F, t)                                         # (the dust is the curtain's: behind the figures)
    warm = 1.0 - F.ramp(*T_WARM)
    crim = S.shaft_rim(F, 0.7 * lit, (0.5, -1.0)) if lit > 0.0 else None
    frim = S.shaft_rim(F, 0.5 * lit, (-0.5, -1.0)) if lit > 0.0 else None
    jc, jf = S.pair(F, D, child_rim=crim, friend_rim=frim, warm=warm)
    if k_sp > 0.0:
        up = F.ramp(189.6, 190.85)
        glow(F, jc["head"][0], jc["head"][1], 120.0, col=light_col(F), a=(0.06 + 0.12 * up) * k_sp)
