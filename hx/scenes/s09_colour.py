"""s09_colour   201.25 - 226.76   c3a, c3b          B8  ->  B9

The band slams back and the sheet itself tears open: light, not yet colour. The two walk over the
first hill; what was enormous in the choruses draws on once more, knee-high, and each thing is
answered as they pass. On the top the child turns to the friend; the friend smiles; the child
answers with its first small smile; their hands join and colour opens from them in a ring. The one
piece of the scribble that stayed winds itself up into the small tangle on its string.

CUE SHEET (song's clock; lines by 0-based LRC index, paraphrased; no lyric text)
  201.25        B8 is the first frame (rip = 0: the held curtains, the shaft, the four hands)
  201.25 - 201.52  THE SHEET RIPS on the slam: weather.tear up between the two from nothing to full in
                eight frames, its flash (strongest three frames in); the shaft of B8 goes under it (0.45 s);
                the curtains break into curling pieces that fly and are rubbed away, the lid into lumps
                that drift off (S.curtain rip=, the lid of B8's camera); scraps of the dark sheet thrown
                out and falling (avoiding the heads); broad pale shafts out of the tear onto the land
  201.25 - 201.75  the two are thrown back a step toward each other, arms left reaching (AP.s09)
  201.25 - 203.40  the land behind draws itself on across the still frame (far layer 201.25 - 203.0,
                middle 201.6 - 203.4, the friend's house on the far hill with it), pale light on the
                slopes, the night sky's pale disc; the plain's ground goes under it (201.6 - 203.4)
  201.6  - 205.0   they catch their breath (panting dies down by 205.0)
  202.05 - 203.75  the piece that stays comes up among the lid's pieces over the child; 203.25 - 208.25
                it sinks to ride behind and above it, half a second late
  203.27 idx 57 (it held on until now) 203.30 the child turns round to the friend (feet stepped,
                not slid); 203.46 the friend half turns to it, grinning
  203.0  - 205.0   pale buds grow up along the hill
  203.52 203.89 204.27  three crows land on the roof of the friend's far house (half beats)
  205.02        they set off right, a step a beat (the friend half a beat ahead); the camera travels
                with them (205.02 - 210.40, one eased move, the ground kept where B8 had it)
  205.92 idx 58 (it got through those voices, those postures, those hurts)
  207.26 hit    three small balloons draw on ahead of them, tails at the child; the two look up
                207.64 the crossed-out words empty out; 208.02 the outlines round into soap bubbles
                that float up and off (two burst on eighth notes, 209.14 and 209.89; one rises away)
  208.76 hit    three small children draw on, their backs to us, on the slope beyond the crest; the
                friend greets them (208.88), they turn round (209.02 - 210.05, one after another) and
                are just children with dot faces; the middle one lifts a hand (209.60); the child
                answers with a small wave of its own (209.26 - 210.18)
  210.26 hit    the split house draws on, knee-high, between the two; both stoop to it (210.58 - 210.90,
                the performance's stoop slowed here)
  210.88        four hands push the halves together on the attack (to 211.20); 211.24, 211.39 two strips
                of amber tape lay themselves across the seam
  211.765       they go on up: two steps to the top (X9, X9 + 180) by 213.2, the camera with them;
                the small children are taken back one per half beat (211.77 - 213.05)
  213.14 idx 60 (it does not want to leave) 213.35 the child stops on the top and turns to look back
                the way they came (the tear, the path, the mended house); 214.0 the friend turns to wait
  214.60        the child turns round to the friend (a real turn, feet stepped)
  214.77 - 216.10  the camera pushes in on the two faces (idx 61, 214.87): heads 177 px; the small
                house is taken back meanwhile at the bottom of the frame (214.77 - 215.77)
  216.07 - 216.98  the friend's face opens into its smile
  217.13 - 217.48  the child answers with its first small smile (217.33), its tufts standing up;
                the friend holds out a hand (217.00), the child takes it (217.72); a small amber warmth
                comes up where the hands meet (217.36 - 217.84). Nothing else moves
  217.84 idx 62 (the world is suddenly filled with colour) THE RING opens from the joined hands:
                inside it the same drawing on warm paper in pastel; it reaches the top edge about
                219.2, the sides 221.2, the corners 222.1 and is past the frame at 222.95; flowers open
                on the eighth notes just behind its edge (hills.ring_bloom); the camera eases back to
                B9's frame (217.84 - 222.84)
  218.14 - 222.0   they look about them, down, then up (AP.s09)
  220.39        the ring passes the far house: its crows fly up as birds, toward the sun (eighth notes)
  219.80 - 223.80  the piece winds itself up (gloom.wind_up): its loose end comes down and dangles
                behind the child (220.76), stroke after stroke is wound into the small knot; the child
                looks up at it (221.44)
  223.40 - 224.80  the child reaches back for the dangling end (AP's string cue 223.5), takes it
                (223.86) and brings it down to its hip: the small tangle bobbing on its string
  222.84 - 226.51  the camera still at B9's frame; they stand hand in hand, alive
  226.51        B9 (S.joined): day skin, the hill world at afternoon gold, the two hand in hand on the
                top, the small tangle on its string

THE PERFORMANCE   AP.s09(_ap_t(t), ground=ground_y): its own cues, its clock slowed through the stoop
                  to the house (_ap_t, 210.53 - 211.30), with these work-rounds laid over it here: the
                  feet held or stepped through its turns and stoops (_feet), its two waves brought below
                  the chest (_waves), the reach for the string made visible (_reach).
LAYERS            S.plain_base (going), S.hill_world (both skins), S.curtain(rip=), weather's tear,
                  tear_shafts, scraps, land's small_voices and small_house, people's person, things'
                  bubble, tape, crow_land, crow_fly, S.pair, gloom's remnant and wind_up; day.ring with
                  one scene function (_world) drawn in both skins.
"""
from __future__ import annotations

import math
from functools import lru_cache

from hx import story
from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk import acting_pair as AP

from . import _shared as S

SPAN = (201.25, 226.76)
START, END = "B8", "B9"

X5, X9, FLOOR = story.X5, story.X9, story.FLOOR
T_RIP, T_COL = story.BAND_SLAM, story.T_COLOUR
CAM8, CAM9 = S.CAM[START], S.CAM[END]
H1, H2, H3 = story.HITS_3

# ---------------------------------------------------------------------------------------------
# the camera
# ---------------------------------------------------------------------------------------------
Z_WALK = 0.85
OFF = (FLOOR - CAM8.cy)                                  # ground under the two to the camera's centre (272: B8's framing)
WALK = (205.015, 210.40)                                 # the camera travels with the walk
HOUSE_X = X9 - 120.0                                     # the small house (AP.s09's default house_x)
CLIMB = (211.765, 213.40)                                # the last two steps to the top
TOP_X = X9 + 10.0
PUSH = (214.765, 216.10)                                 # in on the two faces
CLOSE = Cam(X9 + 90.0, 330.0, 1.5)                       # heads 177 px
PULL = (T_COL, 222.84)                                   # back to the wide frame of B9 while the ring opens


def _walk_cam(x):
    return Cam(x, float(ground_y(x)) - OFF, Z_WALK)


def _cam(t):
    if t < WALK[0]:
        return CAM8
    if t < CLIMB[0]:
        return _walk_cam(CAM8.cx + (HOUSE_X - CAM8.cx) * ease(seg(t, *WALK)))
    if t < PUSH[0]:
        return _walk_cam(HOUSE_X + (TOP_X - HOUSE_X) * ease(seg(t, *CLIMB)))
    if t < PULL[0]:
        return Cam.ease(_walk_cam(TOP_X), CLOSE, seg(t, *PUSH))
    return Cam.ease(CLOSE, CAM9, seg(t, *PULL))


# ---------------------------------------------------------------------------------------------
# the rip and its light
# ---------------------------------------------------------------------------------------------
RIP = (X5 + 60.0, 300.0, X5 + 250.0, -340.0)            # up between the curtains and out of the frame
RIP_HW = 120.0
RIP_C = (X5 + 155.0, -20.0)                              # where its light comes from
L8 = lid_for(CAM8, hang=PART_HANG)


@lru_cache(maxsize=1)
def _grips8():
    return S.calm_grips(AP.hold_B8(T_RIP), T_RIP)


def _rim(G, t, act, k8, d8):
    """Pale light from the tear on a figure: B8's rim at the rip, then from where the tear is."""
    if G.day:
        return None
    J = act.joints()
    hx_, hy_ = J["head"]
    dx, dy = RIP_C[0] - hx_, RIP_C[1] - hy_
    n = math.hypot(dx, dy) + 1e-9
    dv = (max(-0.8, min(0.8, dx / n * 1.6)), -1.0)
    w = ease(seg(t, T_RIP + 0.10, T_RIP + 0.80))
    d = (d8[0] + (dv[0] - d8[0]) * w, -1.0)
    k = k8 + (0.30 + 0.40 * math.exp(-max(0.0, n - 300.0) / 700.0) - k8) * w
    return S.shaft_rim(G, k, d)


# ---------------------------------------------------------------------------------------------
# the performance's clock: AP.s09 stoops to the house in 0.24 s (six frames: a jerk for this tired
# child). A smooth local warp of its time slows the stoop to about eleven frames and lets the push
# that follows land on the measured attack at 210.88; outside 210.53 .. 211.30 it is the song's time
# ---------------------------------------------------------------------------------------------
STOOP_W = (210.53, 210.90, 211.30, 0.115)               # slower from, held back most at, caught up by, how far (s)


def _ap_t(t):
    a, b, c, d = STOOP_W
    if t <= a or t >= c:
        return t
    return t - d * (ease(seg(t, a, b)) if t < b else 1.0 - ease(seg(t, b, c)))


# ---------------------------------------------------------------------------------------------
# planted feet (work-round: figure.turn_round and AP.s09's stoops slide the feet): through these
# windows each foot is held where it stood, or steps to where it ends, one foot after the other
# ---------------------------------------------------------------------------------------------
FEET = (("c", 203.30, 203.97),                           # the child turns round toward the friend (the look, 203.30)
        ("f", 203.46, 203.97), ("f", 204.12, 204.61),    # the friend's half turn and back
        ("c", 210.40, 211.62),                           # the child stoops to the house, pushes, stands
        ("f", 210.37, 211.765),                          # the friend stoops, pushes, stands, turns to go on
        ("f", 213.95, 214.60))                           # the friend turns round to wait for the child


def _act_of(D, who):
    return D.child if who == "c" else D.friend


def _ankles(a):
    J = a.joints()
    return float(J["an_f"][0]), float(J["an_b"][0])


def _lifts(a):
    """How high each ankle stands over the ground under it (the rig's own, kept while pinned)."""
    J = a.joints()
    return tuple(float(ground_y(float(J[k][0]))) - float(J[k][1]) for k in ("an_f", "an_b"))


@lru_cache(maxsize=1)
def _feet_plan():
    plan = []
    for who, ta, tb in FEET:
        a0, a1 = _act_of(AP.s09(ta, ground=ground_y), who), _act_of(AP.s09(tb, ground=ground_y), who)
        s0, s1, h0, h1 = _ankles(a0), _ankles(a1), _lifts(a0), _lifts(a1)
        if abs(s0[0] - s1[1]) + abs(s0[1] - s1[0]) < abs(s0[0] - s1[0]) + abs(s0[1] - s1[1]):
            s1, h1 = (s1[1], s1[0]), (h1[1], h1[0])
        d = (abs(s1[0] - s0[0]), abs(s1[1] - s0[1]))
        first = 0 if d[0] >= d[1] else 1
        plan.append((who, ta, tb, s0, s1, h0, h1, d, first))
    return tuple(plan)


def _feet(D, t):
    for who, ta, tb, s0, s1, h0, h1, d, first in _feet_plan():
        if not ta < t < tb:
            continue
        u = (t - ta) / (tb - ta)
        xs, lifts = [], []
        for i in (0, 1):
            if d[i] < 4.0:
                w, lift = ease(u), 0.0
            else:
                a0, a1 = (0.0, 0.5) if (i == first or d[1 - i] < 4.0) else (0.5, 1.0)
                if d[1 - i] < 4.0:
                    a0, a1 = 0.15, 0.85
                v = seg(u, a0, a1)
                w, lift = ease(v), 10.0 * math.sin(math.pi * v)
            xs.append(s0[i] + (s1[i] - s0[i]) * w)
            lifts.append(lift + h0[i] + (h1[i] - h0[i]) * w)
        a = _act_of(D, who)
        cur = _ankles(a)
        if abs(cur[0] - xs[1]) + abs(cur[1] - xs[0]) < abs(cur[0] - xs[0]) + abs(cur[1] - xs[1]):
            xs, lifts = xs[::-1], lifts[::-1]
        P = a.pose
        for k, wx, lf in zip(("f", "b"), xs, lifts):
            ay = float(ground_y(wx)) - lf
            P = aim_foot(P, k, ((wx - a.x) / (a.face * a.h), (a.y - ay) / a.h))
        a.pose = P


# ---------------------------------------------------------------------------------------------
# the two waves to the small children (AP.s09 waves at shoulder height: the arm crosses the big
# head and reads as a hand over the face, or at the mouth): the waving hand comes lower, before the chest
# ---------------------------------------------------------------------------------------------
def _waves(D, t):
    for a, (t0, t1, t2, t3), dy in ((D.friend, (H2 + 0.12, H2 + 0.42, H2 + 0.78, H2 + 1.08), 0.13),
                                    (D.child, (H2 + 0.50, H2 + 0.80, H2 + 1.12, H2 + 1.42), 0.12)):
        k = AP._ramp(t, t0, t1) * (1.0 - AP._ramp(t, t2, t3))
        if k > 0.0:
            hf = a.pose["hf"]
            a.pose = a.pose.but(hf=(hf[0] + 0.03 * k, hf[1] - dy * k))


# ---------------------------------------------------------------------------------------------
# the piece of the scribble that stays
# ---------------------------------------------------------------------------------------------
RIDE = (-200.0, -520.0)                                  # where it rides: behind and above the child's ground point
WIND = (219.80, 223.80)


def _ride(t):
    gx = AP.s09(t - 0.5, ground=ground_y).child.x        # it lags half a second
    return gx + RIDE[0], float(ground_y(gx)) + RIDE[1]


def _piece(t):
    """Where the piece rides (before it comes down to the hand)."""
    x, y = _ride(t)
    k = ease(seg(t, T_RIP + 2.0, T_RIP + 7.0))
    x0, y0 = AP.hold_B8(T_RIP).child.x - 60.0, 150.0
    return x0 + (x - x0) * min(1.0, 0.3 + k), y0 + (y - y0) * k


DANGLE = (X9 - 95.0, float(ground_y(X9)) - 235.0)        # where the loose end hangs, behind the child's back, until it is taken
REACH = (223.40, 223.86, 224.25, 224.80)                 # the free hand goes back up to it (AP's string cue), takes it, comes down
TAKE = (223.70, 223.86)


def _reach(D, t):
    """AP.s09 reaches back for the string with its far hand behind its head (hidden there); here
    the hand goes to where the end dangles, left of the head, and comes down to the hip with it."""
    w = ease(seg(t, REACH[0], REACH[1])) * (1.0 - ease(seg(t, REACH[2], REACH[3])))
    if w <= 0.0:
        return
    a = D.child
    tgt = ((DANGLE[0] - a.x) / a.h * a.face, (a.y - DANGLE[1]) / a.h)
    a.pose = mixp(a.pose, aim_hand(a.pose, "b", tgt), w)


def _gloom_piece(G, t, D, piece, jc):
    """The piece that stays: drawn by the curtains' rip until 211.65, then by itself; from 219.8 it
    winds itself up, its loose end dangling behind the child, which reaches back and takes it."""
    if t < T_RIP + 10.4:                                 # (the rip's own pieces carry it until then: the same picture)
        return
    if t < WIND[0]:
        remnant(G, *piece)
        return
    take = ease(seg(t, *TAKE))
    hand = tuple(jc["ha_b"])
    hand = (DANGLE[0] + (hand[0] - DANGLE[0]) * take, DANGLE[1] + (hand[1] - DANGLE[1]) * take)
    fl = float_at(G, hand, rise=STRING["rise"], lean=-STRING["lean"])
    m = ease(seg(t, 220.4, 223.6))
    x, y = piece[0] + (fl[0] - piece[0]) * m, piece[1] + (fl[1] - piece[1]) * m
    wind_up(G, x, y, seg(t, *WIND), hand)


# ---------------------------------------------------------------------------------------------
# the three groups, knee-high
# ---------------------------------------------------------------------------------------------
VOICES = ((5190.0, 175.0), (5470.0, 170.0), (5300.0, 60.0))
POPS = (209.14, 209.89, None)                            # two burst on eighth notes, the third rises out of the frame
BACKS = ((5880.0, 140.0, 14), (5955.0, 152.0, 15), (6030.0, 134.0, 16))


def _voices(G, t):
    if t < H1 - 0.1:
        return
    if t < 208.6:
        V = small_voices(VOICES, (4752.0, 470.0), rx=70.0, ry=42.0, a=0.8)
        V.hit(H1)
        words = [n for n in V.names() if ".row" in n or ".cross" in n]          # (land.md's sub("svoice0.row") matches none)
        V.sub(*words).set_off(207.64, 207.98)                                  # they empty on the eighth note after the hit
        V.sub(*[f"svoice{i}.balloon" for i in range(3)]).set_off(208.015, 208.36)   # and round into bubbles on the beat
        V.draw(G)
    for i, (x, y) in enumerate(VOICES):
        age = t - 208.03 - 0.06 * i
        if age < 0.0:
            continue
        r = 44.0 * (0.75 + 0.25 * ease(seg(age, 0.0, 0.35)))
        bx, by = float_up(x, y, age, seed=3 + i, rise=70.0)
        p = 0.0 if POPS[i] is None else seg(t, POPS[i], POPS[i] + 0.24)
        bubble(G, bx, by, r, seed=3 + i, a=ease(seg(age, 0.0, 0.25)), pop=p)


def _backs(G, t):
    if t < H2 - 0.1 or t > 213.1:
        return
    for i, (x, h, sd) in enumerate(BACKS):
        y = float(ground_y(x))
        dr = seg(t, H2 - 0.066 + 0.09 * i, H2 + 0.40 + 0.09 * i)
        w = ease(seg(t, 209.015 + 0.125 * i, 209.80 + 0.125 * i))
        off = seg(t, 211.765 + 0.375 * i, 212.30 + 0.375 * i)
        up = ease(seg(t, 209.60, 210.00)) * (1.0 - ease(seg(t, 211.0, 211.5))) if i == 1 else 0.0
        P = mixp(P_REST, P_WAVE, up)
        person(G, x, y, h, P, "pupil", -1, seed=sd, a=0.9, draw=dr, off=off, wave=up, col=C.CHALK_COOL,
               wag=math.sin((t - 209.8) * 9.0) * up, **turned(w))


def _house(G, t, D):
    if t < H3 - 0.1 or t > 216.0:
        return
    split = 0.10 * (1.0 - D.num["push"]) if t < 212.0 else 0.0
    Hs = small_house(HOUSE_X, ground_y, split=split, a=0.8)
    Hs.hit(H3)
    Hs.off(214.765, 1.0)
    Hs.draw(G)
    if t >= 211.2:
        wx, wy = Hs.anchors["wall"]
        rx, ry = Hs.anchors["roof"]
        for (x0, y0, x1, y1, t0, sd) in ((wx - 26.0, wy - 5.0, wx + 25.0, wy + 4.0, 211.24, 561),
                                         (rx - 22.0, ry + 3.0, rx + 23.0, ry - 4.0, 211.39, 562)):
            Tp = tape(x0, y0, x1, y1, 14.0, seg(t, t0, t0 + 0.25), seed=sd)
            Tp.set_off(214.80, 215.50)
            Tp.draw(G)


# ---------------------------------------------------------------------------------------------
# the last crows, on the roof of the far house
# ---------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _roof():
    """Three perches on the roof of the friend's house on the far layer (hills.home's geometry for
    hills(house=S.HOUSE): 96 wide, standing on the far contour), in that layer's coordinates."""
    x, w = S.HOUSE[0], 96.0
    y = float(layer_y(x, FAR)) + 5.0
    h, rh = w * 0.62, w * 0.46
    lx, ly = x - w / 2 - w * 0.10, y - h + 4.0
    ax_, ay = x + w * 0.02, y - h - rh
    rx, ry = x + w / 2 + w * 0.10, y - h + 2.0
    return ((lx + (ax_ - lx) * 0.55, ly + (ay - ly) * 0.55), (ax_ + (rx - ax_) * 0.12, ay + (ry - ay) * 0.12),
            (ax_ + (rx - ax_) * 0.62, ay + (ry - ay) * 0.62))


CROW_LAND = (203.515, 203.89, 204.265)
CROW_S = (0.42, 0.38, 0.40)


@lru_cache(maxsize=1)
def _crow_go():
    """When the ring's edge passes the roof: each crow takes off on the next eighth note."""
    px, py = _roof()[0]
    for j in range(2000):
        t = T_COL + j * 0.005
        cam = _cam(t)
        dc = cam.depth(FAR)
        sx, sy = dc.to_screen(px, py)
        ox, oy = cam.to_screen(X9 + 90.0, 360.0)
        if math.hypot(sx - ox, sy - oy) < _ring_r(t) - 30.0:
            k = math.ceil((t - 0.265) / 0.375)
            return 0.265 + 0.375 * k
    return 230.0


def _crows(G, t):
    if t < CROW_LAND[0] - 0.3:
        return
    go = _crow_go()
    with G.depth(FAR):
        for i, (x, y) in enumerate(_roof()):
            s = CROW_S[i]
            tg = go + 0.13 * i
            if t < tg:
                crow_land(G, x, y, s, seed=520 + i, face=-1 if i == 1 else 1, u=(t - CROW_LAND[i] + 0.15) / 0.26, hunch=0.6)
            else:
                crow_fly(G, x, y, s, seed=520 + i, face=1, u=(t - tg) / 4.2, to=(1350.0 + 150 * i, -520.0 - 70 * i), hunch=0.6, beats=13.0)


# ---------------------------------------------------------------------------------------------
# the ring
# ---------------------------------------------------------------------------------------------
def _ring_r(t):
    if t < T_COL:
        return 0.0
    return 1330.0 * ease_out(seg(t, T_COL, 223.60), 1.4) + 20.0


# ---------------------------------------------------------------------------------------------
# the scene in either skin
# ---------------------------------------------------------------------------------------------
def _world(G, t, D, piece):
    since = t - T_RIP
    k_on = seg(t, T_RIP, 203.0)
    night = not G.day
    c, f = D.child, D.friend
    if night and t < 203.5:
        S.plain_base(G, X5, 0.0, a=1.0 - ease(seg(t, 201.6, 203.4)), hill=True)
    bloom = 1.0
    if G.day and t < 224.0:
        H = D.pts["ring"]
        bloom = ring_bloom(G, H[0], H[1], _ring_r, T_COL, cam_at=_cam)
    S.hill_world(G, back=(k_on, seg(t, 201.6, 203.4)) if night else 1.0, lit=k_on, light=k_on, figures=(c, f), bloom=bloom,
                 grow=ease(seg(t, 203.0, 205.0)), skip=(c.x - 70.0, f.x + 70.0), tree_a=1.0 if t > 203.4 else 0.0)
    if night and since >= 0.0:
        op = seg(t, T_RIP, T_RIP + 8.0 / 30.0)
        gl, gr = _grips8()
        if since < 0.5:                                  # the shaft of B8 goes as the sheet tears
            Gp = curtain_gap(CAM8, S.SEAM, None, gl, gr, s=L8["s"])
            gap_light(G, *Gp, a=1.0 - ease(seg(since, 0.0, 0.45)), open_=min(1.0, Gp[4] / 40.0), t=t)
        if op > 0.0:
            tear_shafts(G, *RIP, X5 - 700.0, X5 + 1500.0, 782.0, RIP_HW, op)
        _crows(G, t)
        if since < 10.4:
            S.curtain(G, gl, gr, S.B8_TREMBLE, rip=since, stays=piece, cam=CAM8)
        tear(G, *RIP, RIP_HW, op, since)
    elif G.day:
        _crows(G, t)
    if night:
        _voices(G, t)
        _backs(G, t)
        _house(G, t, D)
    if t < WIND[0]:                                      # the piece rides behind the two; winding up, it is the child's: after them
        _gloom_piece(G, t, D, piece, None)
    crim = _rim(G, t, c, 0.7, (0.5, -1.0))
    frim = _rim(G, t, f, 0.5, (-0.5, -1.0))
    warm = ease(seg(t, 217.36, 217.84))                  # the friend's warmth where the hands meet, just before the ring
    jc, jf = S.pair(G, D, child_rim=crim, friend_rim=frim, shadow=0.0 if G.day else 1.0, warm=warm)
    if night and 0.0 <= since < 8.0:
        scraps(G, *RIP, since, hw=RIP_HW, avoid=[(*jc["head"], jc["R"] * 1.1), (*jf["head"], jf["R"] * 1.1)])
    if t >= WIND[0]:
        _gloom_piece(G, t, D, piece, jc)


def draw(F):
    if S.joined(F, START, END):                          # the last 0.25 s: the hand-off picture B9
        return
    t = F.t
    D = AP.s09(_ap_t(t), ground=ground_y)
    _feet(D, t)
    _waves(D, t)
    _reach(D, t)
    F.cam = _cam(t)
    piece = _piece(t)
    if t >= T_COL:
        ring(F, lambda G: _world(G, t, D, piece), *D.pts["ring"], _ring_r(t), turn=t - T_COL)
    else:
        _world(F, t, D, piece)
