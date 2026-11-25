"""s07_bridge   158.86 - 182.30   br_a, br_b, br_c          B6  ->  B7

The bridge: work done together, quiet and concrete. The two unpick the scribble a line at a time, tape the
torn drawing and let it go far off, the child opens the fist that held the strand, the scribble gathers
up high, the long line they pulled out becomes the first hill, they stand, and the child's eyes open.

CUE SHEET (song's clock; lines by 0-based LRC index, paraphrased; no lyric text)
  158.86        B6: the first frame is S.handoff(F, "B6"): the two-shot under the thinned lid, hands joined,
                both looking up, the light under the thin place, rain 0.25 (gone by 162), puddles
  br_a 158.86   idx 48 (the scars: leave them to memory)
  158.95-159.60 a loose end slips out of the lid between them and hangs (its tip leading); the friend sees it,
                lets the hand go (the glow on the joined hands goes with it), reaches FORWARD for it
  160.0         pull 1 (attack 160.015): the friend falls back on its bottom; a long dark line comes out of the
                lid and lies down in coils along the ground to the right; the lid gives a little, the light
                under it grows a little (after every pull)
  161.9         pull 2 (attack 161.884): both hands, leaning far back; it holds the end out to the child
  162.75-164.75 the camera eases in to the two and their hands (heads 177 px)
  163.3-163.9   the child takes the two halves out of its jumper (they come up at its lap over 10 frames)
  164.9         pull 3 (attack 164.885): the child's own small pull; the friend is glad
  165.63 166.39 a strip of amber tape on each attack (7 frames each), the friend's hand running along it; the
                tear still shows
  167.1         the child lifts the mended drawing and lets it go (attack 167.137); it floats up, shrinking,
                drifts back the way they came (left) and comes to rest far off at 170.70, a breath of pale light
                round it, two pins (the first on the attack 170.887): kept. Both watch it go, eyes on it
  167.30-169.70 the camera eases back and left to the wide frame: the sky, the drawing, the far horizon
  167.9         pull 4, together (attack 167.88): the line's upper end comes out of the lid and falls (168.15-169.05)
  169.006       far off on the horizon the split house draws itself on (a stroke a frame), its halves lean apart;
  169.773       they come together (to 170.40), the tear still showing
  169.30-169.80 (unseen) the strand that ran from the lid to the crown runs on down behind the child to its far hand
  br_b 170.80   idx 49 (letting go is how something better comes)
  170.80-172.50 the camera pushes in on the child (heads 168 px); its fist comes up before its face: the strand
                comes out from behind its head and runs from the fist (171.35-172.40): it has held it all along.
                It looks up along the strand (172.2), back at the fist (172.62-173.24, slowed), squeezes, the
                strand trembling (173.2)
  173.511       it opens the fist (attack): the strand slips out, floats up swaying and is drawn into the lid
                (to 175.30); its eyes follow it up
  173.55-175.55 the lid rises and gathers into the high cloud of B7 (the light under it goes with it)
  173.6-174.8   the plain's furrows and puddles give way to the hills' own ground (S.hill_ground's a)
  174.25-177.50 the camera eases back and right to show the land
  175.009       it opens the other hand too (attack): it lets the line go
  175.0-178.2   the long line on the ground straightens, the near end first, lifts into the shape of a hill and
                settles as its contour, the ground swelling under it (_s07.hill_line on hills' hill_rise)
  br_c 178.26   idx 50 (do not be afraid, said twice)
  178.45-179.51 the friend gets up, the child gets up; the friend's hand comes to rest on its shoulder (attack
                179.508), the glow where they touch comes back
  178.50-181.20 the camera eases in to the close two-shot of B7 (heads 153 px)
  181.0         both the child's hands close over the friend's hand (attack 181.005); 180.92-181.32 the friend's
                other hand comes over them (both hands on both hands), goes back by 181.98
  181.42-181.80 the child lifts its face and its eyes open fully, a blink on the way, for the first time (its lids
                are kept from lifting all the way before this): open on the attack 181.76
  182.05        B7 (S.joined): camera (4390, 500, 1.3); the plain with the first hill; both standing, the friend's
                hand on the child's upper arm; the high cloud; no strand, no rain

THE PERFORMANCE   AP.s07 on a clock of its own in two places (_tau: the look back down at the fist and the
                  eyes opening take more frames); the child's lids capped until the clasp (_child); the
                  friend's scarf kept from sticking out while it turns to us, its other hand at the clasp
                  (_friend); both watch the rising drawing (look_to on its place).
THE LINE          _s07 (line_pts, draw_line, hill_line): the line on the ground lies where it fell (unravel
                  drags its coils with the hand), and is the same stroke when it becomes the hill.
THE STRAND        _s07.strand_line along crown .. hidden fist .. fist .. floating free.
THE LID           ceiling with B6's numbers while the camera is closer than B6, the frame's when wider
                  (_lid_nums), amount down 0.12 a pull, the thin place and its light going as it gathers
                  (spread to band_cloud(*HIGH)); from 175.55 S.high_cloud after the figures.
PAINT ORDER       plain (ground, mist, far rain) . light under the thin place . ground line / hills' ground .
                  far house . lid . strand . the line . the two (the drawing between them while it is taped) .
                  the glow where they touch . the drawing . high cloud . near rain
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from hx import story
from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk import acting_pair as AP
from hx.chalk.land import _small_cols                    # the knee-high house's tones (read only)
from hx.chalk.weather import glow as wglow

from . import _s07 as L7
from . import _shared as S

SPAN = (158.86, 182.30)
START, END = "B6", "B7"

X5, FLOOR = story.X5, story.FLOOR
XF = X5 + 180.0
AX6 = story.HANDOFF["B5"]["cloud"][0]                    # the lid's anchor at B6 (4270)
HIGH = S.HIGH
C6, C7 = S.CAM["B6"], S.CAM["B7"]
T6 = S.T["B6"]

# ---------------------------------------------------------------------------------------------
# cues
# ---------------------------------------------------------------------------------------------
TT = dict(AP.S07_T)
P1, P2, P3, P4 = TT["pulls"]
T_REL, T_FIST, T_FIST2, T_LAY, T_RISE, T_STAND, T_CLASP, T_OPEN = (TT["release"], TT["fist"], TT["fist2"], TT["lay"], TT["rise"],
                                                                  TT["stand"], TT["clasp"], TT["open"])
END_DROP = (158.95, 159.60)                              # a loose end slips out of the lid between them
LET0, LET_DUR, LET_LAG = 168.15, 0.50, 0.40              # the pull together brings the line's upper end out of the lid: it falls
T_PINNED = 170.70                                        # the drawing has come to rest far off
WATCH = (168.30, 170.80)                                 # both watch it go (their eyes on it)
GATHER = (173.55, 175.55)                                # the lid rises and gathers into the high cloud
HILL = (175.0, 178.2)
HOUSE_ON = 169.006                                       # the far house draws on (a stroke a frame or two)
HOUSE_SHUT = (169.773, 170.40)                           # its halves come together
FCLASP = (180.92, 181.32, 181.68, 181.98)                # the friend's other hand comes over the child's two hands, and back
HID = (169.30, 169.80)                                   # the strand runs on from the crown down behind the child to its far hand
SLIDE = (171.35, 172.40)                                 # it slides off the head: it runs from the fist
FLOAT = (173.52, 175.30)                                 # let go: its lower end floats up into the gathering scribble

# ---------------------------------------------------------------------------------------------
# places
# ---------------------------------------------------------------------------------------------
END_PT = (X5 + 102.0, FLOOR - 128.0)                     # the performance's loose end (pts["end"])
G1 = (X5 + 100.0, FLOOR - 160.0)                         # the friend's first grip on it
PILE = (X5 + 192.0, FLOOR - 6.0)                         # where the pulled line first touches the ground
FALL = (X5 + 104.0, FLOOR - 4.0)                         # where its upper end comes down when it falls out of the lid
PIN = (3200.0, 330.0)                                    # the mended drawing, pinned far off (left of B8's frame)
HOUSE_X, HOUSE_W = 3112.0, 64.0                          # the far house on the horizon (left of B8's frame)
HANDS6 = AP.hold_B6(T6).pts["hands"]                     # the joined hands of B6
SHOULDER = AP.hold_B7(S.T["B7"]).pts["shoulder"]         # where the friend's hand comes to rest (B7)

# ---------------------------------------------------------------------------------------------
# camera
# ---------------------------------------------------------------------------------------------
C_TAPE = Cam(4396.0, 612.0, 1.5)
C_WIDE = Cam(3900.0, 470.0, 0.95)
C_FIST = Cam(4352.0, 585.0, 1.42)
C_HILL = Cam(4660.0, 520.0, 0.92)


def _cam(t):
    c = Cam.ease(C6, C_TAPE, seg(t, 162.75, 164.75))
    c = Cam.ease(c, C_WIDE, seg(t, 167.30, 169.70))
    c = Cam.ease(c, C_FIST, seg(t, 170.80, 172.50))
    c = Cam.ease(c, C_HILL, seg(t, 174.25, 177.50))
    return Cam.ease(c, C7, seg(t, 178.50, 181.20))


def _lid_nums(cam):
    """lid_for's numbers: B6's while the camera is closer than B6 (the lid stays where it hangs), the frame's
    when it is wider or higher (its upper edge must stay above the frame top)."""
    z = min(cam.zoom, C6.zoom)
    top = min(cam.view()[1], C6.view()[1])
    k = 1.0 / z
    return dict(s=k, y=top + 235.0 * k, depth=365.0 * k)


# ---------------------------------------------------------------------------------------------
def _pulled(t):
    """The pulls made so far, each counted as the lid gives after it (0 .. 4)."""
    return sum(ease(seg(t, tp + 0.05, tp + 1.0)) for tp in TT["pulls"])


def _amount(t):
    """How much of the lid is left: it gives a little after every pull."""
    return 1.0 - 0.12 * _pulled(t)


def _rain(t):
    return 0.25 * (1.0 - ramp(t, T6, 162.0))


def _wet(t):
    return 1.0 - ramp(t, 160.4, 171.0)


# The performance is played on its own clock in two places, so that two quick moves of AP.s07 take the frames a
# tired child needs: the look from the strand back down to the fist (172.85, 0.38 s in the kit) and the eyes
# opening fully (open, 0.26 s: a snap of three frames). Knots (t, performance time); the clock is the song's
# elsewhere and at both ends.
_WARP = ((172.20, 172.20), (172.55, 172.65), (172.62, 172.85), (173.24, 173.24),
         (181.20, 181.20), (181.42, 181.52), (181.80, 181.70), (182.00, 182.00))
_WT, _WP = np.array([k[0] for k in _WARP]), np.array([k[1] for k in _WARP])


def _tau(t):
    if t <= _WT[0] or t >= _WT[-1] or (_WT[3] <= t <= _WT[4]):
        return t
    return float(np.interp(t, _WT, _WP))


# The friend alone on a clock of its own in two more places: its turn toward us to cast the line (175.08, 0.40 s:
# its legs swing round in five frames) and its getting up (178.45, 0.30 s: legs tucked in four frames) start a
# little earlier out of a hold and take twice the frames. Each stretch: (t, friend's performance time) knots.
_WARP_F = (((174.78, 174.78), (174.86, 175.08), (175.50, 175.48), (175.90, 175.90)),
           ((178.10, 178.10), (178.30, 178.45), (178.80, 178.75), (179.20, 179.20)))


def _tau_f(t):
    for K in _WARP_F:
        if K[0][0] < t < K[-1][0]:
            return float(np.interp(t, [k[0] for k in K], [k[1] for k in K]))
    return _tau(t)


def _act(a, P):
    return AP.Act(P, a.x, a.y, a.face, a.grab, a.h, a.skin, a.seed, a.a, a.draw, a.lift)


def _child(D, t):
    """What this scene adds to the child's performance: until the clasp its lids never quite lift (the kit's
    surprise and wonder open them as wide as B7 does): its eyes open fully for the first time at 181.7."""
    k = ramp(t, 159.0, 159.9) * (1.0 - ramp(t, 181.30, 181.62))
    if k <= 0.0:
        return
    c = D.child
    P = c.pose
    lid, eye = P["lid"], P["eye"]
    P = P.but(lid=lid + k * max(0.0, 0.45 - lid), eye=eye - k * max(0.0, eye - 1.05))
    D.child = _act(c, P)


def _friend(D, t):
    """What this scene adds to the friend's performance: its scarf does not stick out like a bar while it turns
    to us to cast the line (the kit's follow-through throws it far forward there); for a moment its other hand
    comes over the child's two hands on its shoulder (both its hands on both of the child's)."""
    f = D.friend
    P = f.pose
    if 174.8 < t < 177.2 and P["sway"] < -0.2:
        P = P.but(sway=-0.2 + 0.25 * (P["sway"] + 0.2))
    a0, a1, b0, b1 = FCLASP
    w = ease(seg(t, a0, a1)) * (1.0 - ease(seg(t, b0, b1)))
    if w > 0.0:
        own = np.asarray(f.joints()["ha_b"], dtype=np.float64)
        pt = own + (np.array([SHOULDER[0] + 10.0, SHOULDER[1] + 16.0]) - own) * w
        P = aim_hand(P, "b", ((pt[0] - f.x) / (f.face * f.h), (f.y - pt[1]) / f.h))
    if P is not f.pose:
        D.friend = _act(f, P)


def _drawing(t, D):
    """(centre, s, rot) of the mended drawing after it is let go: it floats up, shrinking, drifts back the way
    they came and comes to rest far off."""
    hl, hr = D.pts["half_l"], D.pts["half_r"]
    c0 = (0.5 * (hl[0] + hr[0]), 0.5 * (hl[1] + hr[1]))
    u = seg(t, T_REL, T_PINNED)
    ux = ease(seg(u, 0.15, 1.0))
    uy = ease_out(u, 1.7)
    x = c0[0] + (PIN[0] - c0[0]) * ux
    y = c0[1] + (PIN[1] - c0[1]) * uy - 50.0 * math.sin(math.pi * seg(u, 0.35, 1.0))
    s = 0.62 * (1.0 - 0.50 * ease(u))
    rot = 0.11 * math.sin(2.4 * math.pi * u) * (1.0 - u) + 0.05 * ease(u)
    return (x, y), s, rot


def _held(F, D, t):
    """The two halves, held (until the release), or the mended drawing rising and pinned."""
    if D.pts["half_l"] is None or D.num["halves"] <= 0.0:
        return
    if t < T_REL:
        family_held(F, D.pts["half_l"], D.pts["half_r"], 0.62, taped=D.num["taped"], a=D.num["halves"])
        return
    (cx, cy), s, rot = _drawing(t, D)
    g = 62.0 * s
    e = (math.cos(rot), math.sin(rot))
    k = ramp(t, T_PINNED - 0.9, T_PINNED + 0.4)
    if k > 0.0:                                          # kept: a breath of pale light round it in the dark sky
        wglow(F, cx, cy - 30.0 * s, 150.0 * s + 30.0, 120.0 * s + 26.0, col=light_col(F), a=0.16 * k)
    family_held(F, (cx - g * e[0], cy - g * e[1]), (cx + g * e[0], cy + g * e[1]), s, taped=2.0)
    if t > T_PINNED - 0.1:
        P = family(cx, cy - 30.0 * s, s, taped=2, rot=rot, pins=True).sub("pic.pin_l", "pic.pin_r")
        P["pic.pin_l"].on = (T_PINNED - 0.05, T_PINNED + 0.20)
        P["pic.pin_r"].on = (T_PINNED + 0.12, T_PINNED + 0.37)
        P.draw(F)


def _house(F, t):
    if t < HOUSE_ON - 0.05:
        return
    col, tone, kn = _small_cols(False)
    sp = 0.13 * (1.0 - ease(seg(t, *HOUSE_SHUT)))
    Hs = house(HOUSE_X, FLOOR, HOUSE_W, 600, col, sp, 0.75, 2.4, fill=tone, roof=mix(tone, kn, 0.45), name="fh", detail=1, knock=kn)
    lines = Hs.without(*[n for n in Hs.names() if n.endswith((".fill", ".hatch"))])
    fills = Hs.sub(*[n for n in Hs.names() if n.endswith((".fill", ".hatch"))])
    lines.spread(HOUSE_ON, 0.50 / max(1, len(lines.items) - 1), 0.16)     # the outline a stroke a frame or two
    fills.set_on(HOUSE_ON + 0.55, HOUSE_ON + 0.95)                         # then its tone is rubbed in (no blot ahead
    Hs.draw(F)                                                             # of the line on the misty horizon)


# ---------------------------------------------------------------------------------------------
# the line
# ---------------------------------------------------------------------------------------------
def _fallen(hand):
    """Where the line's upper stretch lies once it has fallen: from its free end, in two lazy coils before
    their feet, up to the hand that holds it (24 points)."""
    G = L7.coils(FALL, 330.0, face=-1, seed=47)[::-1]
    H = L7.hang(FALL, hand, 8)
    return L7.resample(np.vstack([G, H[1:]]), 24)


def _line(t, D, Tp):
    """The line as a polyline (mass end first): None before it exists. Returns (P, draw)."""
    if t < END_DROP[0]:
        return None, 0.0
    if t < P1 - 0.05:                                    # the loose end hangs between them; the friend's hand comes to it
        root = Tp.band.root(X5 + 125.0, 0.15)
        k = ease(seg(t, 159.62, 159.95))
        hand = (END_PT[0] + (G1[0] - END_PT[0]) * k, END_PT[1] + (G1[1] - END_PT[1]) * k)
        tail = 40.0 + 32.0 * k
        A_ = strand_pts(hand, root, 0.7, 42, 0.0, t, 24)[::-1]
        u = np.linspace(0.0, 1.0, 6)
        Dd = np.stack([hand[0] + 4.0 * u, hand[1] + tail * u], axis=1)
        return np.vstack([A_, Dd[1:]]), ease_out(seg(t, *END_DROP), 1.6)
    hand = D.pts["line"]
    out = 500.0 * D.num["pulls"] + 72.0
    lie = out - max(0.0, FLOOR - 6.0 - hand[1])
    G = L7.coils(PILE, lie, 1, 41)
    if t < LET0:
        root = Tp.band.root(X5 + 125.0, 0.15)
        A_ = strand_pts(hand, root, 1.0 - D.num["busy"], 42, 0.0, t, 24)[::-1]
    else:                                                # its upper end has come out of the lid: it falls, the far end first
        A1 = _fallen(hand)
        if t < LET0 + LET_DUR + LET_LAG:
            root = Tp.band.root(X5 + 125.0, 0.15)
            A0 = strand_pts(hand, root, 1.0 - D.num["busy"], 42, 0.0, t, 24)[::-1]
            q = np.linspace(0.0, 1.0, 24)
            g = np.clip((t - LET0 - LET_LAG * q) / LET_DUR, 0.0, 1.0) ** 2
            A_ = A0 + (A1 - A0) * g[:, None]
        else:
            A_ = A1
    Dh = L7.hang(hand, PILE, 10)
    return np.vstack([A_, Dh[1:], G[1:]]), 1.0


# ---------------------------------------------------------------------------------------------
# the strand
# ---------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _fist_at_open():
    """Where the fist is the moment it opens (the strand slips out there and is left behind by the hand)."""
    p = AP.s07(_tau(T_FIST)).pts["fist"]
    return np.array([float(p[0]), float(p[1])])


def _strand(F, t, Jc, Tp):
    """The strand from the child into the scribble: from its crown (B6) .. on down behind its head and body
    to its far hand (hidden) .. out of the fist when the fist comes up, sliding off the head .. let go, it
    floats up into the gathering scribble, swaying, and is drawn in."""
    crown = np.asarray(Jc["crown"], dtype=np.float64)
    hand = np.asarray(Jc["ha_b"], dtype=np.float64)
    fl = seg(t, *FLOAT)
    if fl > 0.0:                                         # the hand has opened: the strand's end is free where the fist was
        hand = _fist_at_open()
    sl = ease(seg(t, *SLIDE))
    base_x = crown[0] + (hand[0] - crown[0]) * sl
    root = np.asarray(Tp.band.root(base_x + 40.0, 0.3), dtype=np.float64)
    if t < HID[0]:
        L7.strand_line(F, strand_pts(crown, root, 0.8, 12, 0.0, F.t))
        return
    rise = ease(seg(fl, 0.0, 0.85))
    if fl > 0.0:                                         # it floats up toward where it hangs from
        hand = hand + (root - hand) * 0.62 * rise
    mid = hand + 0.5 * (root - hand)
    cw = crown + (mid - crown) * sl                      # the crown waypoint slides onto the line from fist to mass
    trem = 2.4 * seg(t, T_FIST - 0.30, T_FIST - 0.12) * (1.0 - seg(t, T_FIST, T_FIST + 0.1))
    up = strand_pts(cw, root, 0.8 - 0.5 * sl + 0.6 * rise, 12, trem, F.t)
    q = np.linspace(0.0, 1.0, 12)
    dv = cw - hand
    ln = float(np.hypot(*dv)) + 1e-6
    sway = (0.22 * np.sin(math.pi * q) + 0.10 * np.sin(2.0 * math.pi * q + 0.6 + 3.0 * fl)) * ln * rise
    lo = np.stack([hand[0] + dv[0] * q - dv[1] / ln * sway, hand[1] + dv[1] * q + dv[0] / ln * sway], axis=1)
    lu = float(np.hypot(*(root - cw))) + 1e-6
    v_up = np.linspace(0.0, 1.0, len(up))
    v_lo = np.linspace(-ln / lu, 0.0, 12)
    P = np.vstack([lo[:-1], up])
    v = np.concatenate([v_lo[:-1], v_up])
    grow = ease(seg(t, *HID))
    d0 = v_lo[0] * grow                                 # the hidden stretch runs on down from the crown
    d0 = d0 + (0.999 - d0) * ease(seg(fl, 0.45, 1.0))   # then it is drawn up into the scribble from its free end
    L7.strand_line(F, P, v, draw=(d0, 1.0))


def _touch(F, t):
    """S.pair's small glow where they touch: the joined hands of B6 as they part; the hand on the shoulder."""
    k = 1.0 - ramp(t, 159.30, 159.75)
    if k > 0.0:
        wglow(F, HANDS6[0], HANDS6[1], 46.0, 40.0, a=0.28 * k)
    k = ramp(t, T_STAND - 0.15, T_STAND + 0.35)
    if k > 0.0:
        wglow(F, SHOULDER[0], SHOULDER[1], 46.0, 40.0, a=0.28 * k)


# ---------------------------------------------------------------------------------------------
def draw(F):
    if S.joined(F, START, END):                          # the last 0.25 s: the hand-off picture B7
        return
    t = F.t
    D = AP.s07(_tau(t))
    tf = _tau_f(t)
    if tf != _tau(t):
        D.friend = AP.s07(tf).friend
    F.cam = _cam(t)
    k_rain = _rain(t)
    wet = _wet(t)
    hill = t >= HILL[0]
    w_hill = seg(t, *HILL)

    # the eyes on the drawing while it rises and goes
    kw_ = ramp(t, WATCH[0], WATCH[0] + 0.4) * (1.0 - ramp(t, WATCH[1], WATCH[1] + 0.4))
    if kw_ > 0.0:
        (dx, dy), _s, _r = _drawing(t, D)
        D.child = _act(D.child, AP.look_to(D.child.pose, D.child.x, D.child.y, D.child.h, 1, (dx, dy), kw_, 0.3))
        D.friend = _act(D.friend, AP.look_to(D.friend.pose, D.friend.x, D.friend.y, D.friend.h, -1, (dx, dy), kw_, 0.3))

    _child(D, t)
    _friend(D, t)

    # ---- the plain, the light under the thin place, the ground ------------------------------
    S.plain_base(F, X5, k_rain, wet=wet, hill=hill)
    sp = 1.0 - seg(t, *GATHER)                           # the lid gathers into the high cloud
    if sp > 0.0:                                         # the guess of light under the thin place (S.sky_gap), a little
        x = THIN_PLACE[0]                                # stronger with every pull, going as the lid gathers
        gap_light(F, x, 60.0, F.cam.view()[1] - 40.0, x, 170.0, FLOOR, a=0.45 + 0.05 * _pulled(t), open_=sp)
    if t < 173.6:
        ground_line(F)
    elif not hill:
        S.hill_ground(F, 0.0, a=ramp(t, 173.6, 174.8))
    else:
        S.hill_ground(F, hill_rise(w_hill))
    _house(F, t)

    # ---- the lid, thinning with every pull, gathering; the strand; the line ------------------
    Jc0, Jf0 = D.child.joints(), D.friend.joints()
    Tp = None
    if sp > 0.0:
        x, r, th = THIN_PLACE
        kw = {}
        if sp < 1.0:
            kw = dict(cloud=band_cloud(*HIGH), spread=sp)
        ax = AX6 + (HIGH[0] - AX6) * ease(1.0 - sp)
        Tp = ceiling(F, ax=ax, thin=(x, r, th * sp), avoid=S.clear_of(Jf0), amount=_amount(t), **kw, **_lid_nums(F.cam))
        if t < FLOAT[1]:
            _strand(F, t, Jc0, Tp)
    P, d = _line(t, D, Tp)
    if P is not None:
        if t < HILL[0]:
            L7.draw_line(F, P, draw=d)
        else:
            L7.hill_line(F, P, w_hill)

    # ---- the two ----------------------------------------------------------------------------
    jc = jf = None
    for who in D.order:
        if who == "f":
            jf = S.friend(F, D.friend, wet=0.6 * wet)
        else:
            jc = S.child(F, D.child, rim=S.amber_rim(0.5))
        if who == D.order[0] and D.order == "cf" and t < T_REL:
            _held(F, D, t)
    _touch(F, t)
    if not (D.order == "cf" and t < T_REL):
        _held(F, D, t)
    if sp <= 0.0:
        S.high_cloud(F, heads=(jc, jf))
    S.rain_front(F, k_rain)
