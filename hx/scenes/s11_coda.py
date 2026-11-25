"""s11_coda   244.50 - 258.87   coda          B10  ->  (the end: a slow lift toward warm paper)

Home. The piano alone, as at the start: the room of the first seconds draws itself on round the child,
on warm paper at sunset; the child ties what is left of the scribble to the armrest, climbs onto the
sofa and curls up as in the film's first image, but at ease. The phone that nobody called rings; the
child answers, smiles; across the street the friend waves from its window, and the child waves back.
The camera lifts away and the sheet goes toward plain warm paper.

CUE SHEET (song's clock; lines by 0-based LRC index and time, paraphrased; no lyric text)
  B10 244.50      the first frame is S.handoff(F, "B10") (proved: 0.00 levels): the bare warm sheet toned to
                  evening, the child alone at X10 = 9000 facing left, its long shadow, the tangle on its string;
                  camera (8660, 540, 1.0), which holds the whole room until 248.4
  idx 64 244.64   (the first line of the first verse again: clinging to the sofa, bleary, hair on end)
    244.765       the child walks left, a step a beat (244.765, 245.515), to the right end of the sofa
    244.77        attack: the sofa draws on, the first thing in the room as at 3.27 (back, arms, seat); pastel
                  dust sinks from the fresh lines until 249.4
    244.97        attack: the window frame, then its bars; the sunset view comes up behind it (245.5 - 246.7),
                  the amber window across the street lit from the start
    245.3 - 247.0 the room's light: window glow, the orange pool on the floor; the bare sheet's long shadow goes
                  (245.3 - 246.6), a contact shadow stays while it stands
    245.57        attack: sill and wall lines;  245.86 attack: rail, curtains, the lamp;  246.3 the rug
    246.32 - 247.49  it bends at the armrest and ties the string with both hands going round each other; the
                  bow draws on as they go; the string slips behind the bending child (246.38 - 246.68)
    246.78        the table and its chairs; the phone, quietly, on the floor at the sofa's foot
    246.9 - 247.4 the lamp comes on (warm cone, gold pool)
    247.49        attack: the knot pulled tight; the tangle floats above the armrest on its string, small,
                  bobbing less; the blanket and the pulled-away chair (two chairs still apart); the left half of
                  the family drawing on the wall
    247.57 - 248.11 it straightens up slowly from the knot as it walks off (this scene eases it: 16 frames)
    247.765       two more steps to the front of the sofa
    247.80        the right half of the drawing; 248.14, 248.33 two strips of amber tape (the tear still shows)
    248.4 - 250.9 the camera comes in on the sofa to the framing of the film's first image (s01 at 12.0 s)
    249.30        it turns toward us and gets up onto the edge of the seat (0.6 s)
    249.92 - 251.0 it curls up as at 9.3 s, at ease: slow breath, the eyes close as the head comes down
                  (the piano is silent 248.5 - 250.75: only the child and the dust move)
  idx 65 250.74   (sunset; the phone connects; it is you)
    250.74        the phone lights amber: a warm place on the floor and up the sofa's front
    251.41        first ring (brackets, a hop): it stirs, a crack of bleary eye
    251.83        second ring: the eyes open, it looks; the camera begins its push-in (to 254.0: head 150 px)
    252.37        third ring: it stretches out and rolls onto its back, the arm that lay under it reaching down
    252.61        fourth ring: its hop carries the phone up into the hand (252.62 - 252.87)
    252.87        fifth ring, the strongest attack: picked up; brought up, stood upright on the way
    253.60        at its ear, the amber face of the phone against the cheek, its light round the head
    253.75        attack: it smiles (over 0.6 s); 254.08 - 254.9 it says something into the phone, two short
                  phrases on the half beats
    254.45 - 255.0 in the amber window across the street a small amber figure rises (AP.window_friend)
    255.0         and waves, a sweep every half beat; 255.12 - 257.1 the child's free hand comes up off its belly
                  and waves back in time, then sinks
    255.2 - 258.6 chalk dust turns and falls in the window's light and over the room (true time)
    255.5 - 258.6 the camera lifts slowly away to the whole room, open above; the picture holds
    256.6 - 258.6 the sheet fades toward plain warm paper (F.post.fade to 0.76, C.EVE_PAPER): not a full stop;
                  the tangle still there, small, two chairs apart, the drawing taped, the tear showing

THE PERFORMANCE   D = AP.s11(F.t, smile=253.75, wave=900): from hold_B10. This scene lays over it: the slow
                  straightening after the knot (_rise), the waking and the talk (_face), the wave back (_wave).
LAYERS            paper_tone (as B10), S.room_set("sunset", ROOM3_DX, R=room_on_coda's Place, drawing=0, phone_a=0,
                  cushion=False), the wall drawing on its own times, the room's dust, the window friend clipped to
                  FAR_WINDOW, the phone's light and the phone on the floor, the shadows, the string when it is behind
                  the child, S.child, the cushion, the phone in the hand, the string, the tangle, the end's dust, the fade.
"""
from __future__ import annotations

import math

import numpy as np

from hx import story
from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk import acting_pair as AP
from hx.chalk.gloom import _string_pts

from . import _shared as S

SPAN = (244.50, 258.87)
START, END = "B10", None

DX = story.ROOM3_DX
FLOOR = story.FLOOR
T = dict(AP.S11_T, smile=253.75, wave=900.0)             # the performance's cues: the smile on the measured attack; its
                                                         # small wave is this scene's (_wave: a hand raised, in time with the friend's)
TT, TG = T["tie"], T["tight"]
CUE_KW = {k: v for k, v in T.items() if AP.S11_T.get(k) != v}
STRAIGHTEN = (TG + 0.08, TG + 0.62)                      # it straightens up from the knot over 16 frames, walking off
WAVE = (255.12, 255.55, 256.55, 257.1)                   # the free hand up, waving, down

# ---- the camera -------------------------------------------------------------------------------------
CAM_B10 = S.CAM["B10"]                                   # (8660, 540, 1.0): the whole room, as the intro saw it
CAM_CURL = Cam(919.9 + DX, 493.8, 1.142)                 # the film's first image of the child on the sofa (s01 at 12.0 s)
CAM_CALL = Cam(8680.0, 525.0, 1.27)                      # the head 150 px; the phone above the lyric band; the far window in
CAM_END = Cam(8770.0, 455.0, 0.93)                       # lifted away: the whole room again, open above
T_IN = (248.4, 250.9)
T_CALL = (251.83, 254.0)
T_LIFT = (255.5, 258.6)

# ---- things ---------------------------------------------------------------------------------------------
PHONE_XY = (AP.s11(253.0).pts["reach"][0], FLOOR + 14.0)  # under the hand that will reach down (the rug's far edge)
PHONE_ON = (246.78, 247.08)
PHONE_LIT = (250.74, 250.96)
HOP = (252.62, 252.87)                                   # the fourth ring's hop carries it up into the hand
LEAN_TIED = 10.0                                         # the tangle above the armrest: clear of the drawing and of the head
T_BEHIND = (TT + 0.06, TT + 0.36)                        # the string slips behind the child as it bends to the armrest
T_SOFA = T["sit"] + 0.30                                 # in front again: the child is on the seat
RISE = 330.0                                             # the string's length (gloom.STRING)
WALL_ON = ((247.49, ("pic.l", "pic.pin_l")), (247.80, ("pic.r", "pic.pin_r", "pic.tear")))
TAPE_ON = (248.14, 248.33)
LAMP_ON = (246.9, 247.4)
FADE = (256.6, 258.6, 0.76)                              # toward plain warm paper: not a full stop
ROOM_DUST = (244.77, 249.4)                              # dust sinks from the room's fresh lines, as from the intro's
DUST_LIFE = 0.9


def _cam(t: float) -> Cam:
    c = CAM_B10
    if t > T_IN[0]:
        c = Cam.ease(c, CAM_CURL, seg(t, *T_IN))
    if t > T_CALL[0]:
        c = Cam.ease(c, CAM_CALL, seg(t, *T_CALL))
    if t > T_LIFT[0]:
        c = Cam.ease(c, CAM_END, seg(t, *T_LIFT))
    return c


_LEGS = ("ff", "fb", "af", "ab", "kf", "kb", "ffz", "fbz", "front")


def _rise(c, t: float) -> None:
    """The child straightens from the knot slowly, walking off as it does (the performance stands it
    up in 0.17 s: the head flies 30 units a frame). The upper body is eased from its pose at the knot
    into the performance's over STRAIGHTEN; the legs are the performance's own (the walk's planted feet)."""
    u = seg(t, *STRAIGHTEN)
    if u <= 0.0 or u >= 1.0:
        return
    a = AP.s11(STRAIGHTEN[0], **CUE_KW).child.pose
    e = ease(u)
    c.pose = mixg(a, c.pose, {k: 1.0 for k in _LEGS}, e)


def _face(c, t: float) -> None:
    """This scene's face over the performance: asleep through the first ring, a crack of bleary eye on
    it, fully open on the second; after the smile it says something into the phone."""
    P = c.pose
    r1, r2 = T["ring"], T["look"]
    if r1 <= t < r2 + 0.4:
        cap = 0.32 * ramp(t, r1 + 0.10, r1 + 0.32) + 0.73 * ramp(t, r2 + 0.04, r2 + 0.30)
        lid = 1.0 - 0.7 * ramp(t, r2 + 0.04, r2 + 0.30)
        P = P.but(eye=min(P["eye"], cap), lid=max(P["lid"], lid))
    talk = ramp(t, 254.08, 254.2) * (1.0 - ramp(t, 254.78, 254.92))
    if talk > 0.0:                                       # two short phrases on the half beats
        m = 0.5 - 0.5 * math.cos(2.0 * math.pi * (t - 254.08) / 0.375)
        P = P.but(mopen=max(P["mopen"], 0.75 * talk * m), mouth=P["mouth"] - 0.25 * talk * m)
    c.pose = P


def _wave(c, t: float) -> None:
    """The free hand comes up off the belly and waves, in time with the friend's sweeps across the
    street (a sweep every half beat from 255.0), then sinks back."""
    up = ease(seg(t, WAVE[0], WAVE[1])) * (1.0 - ease(seg(t, WAVE[2], WAVE[3])))
    if up <= 0.0:
        return
    w = ramp(t, WAVE[1] - 0.2, WAVE[1] + 0.1) * (1.0 - ramp(t, WAVE[2] - 0.25, WAVE[2]))
    s = math.sin(2.0 * math.pi * (t - 255.0) / 0.75 + 0.5 * math.pi)
    hx, hy = c.pose["hf"]
    c.pose = c.pose.but(hf=(hx + 0.22 * up, hy + 0.10 * up + 0.05 * s * w))


def _phone_at(D, t: float):
    """Where the phone is: (centre x, centre y, rot, lie, how far it has come up to the ear) or None
    before it is drawn. On the floor under the reach; the fourth ring's hop lifts it into the hand;
    from `grab` held by its lower third and stood upright on the way to the ear."""
    held = D.pts["phone"]
    if held is None:
        if t < PHONE_ON[0]:
            return None
        x, y = PHONE_XY
        y += (D.pts["reach"][1] - y) * ease(seg(t, *HOP))
        return x, y, -0.07, 1.0, 0.0
    up = ease(seg(t, T["grab"], T["ear"]))
    ang = -0.07 + (-1.95 + 0.07) * up
    off = 0.20 * PHONE_LEN * up                          # from the hand's point at the grab to its lower third at the ear
    return held[0] + off * math.cos(ang), held[1] + off * math.sin(ang), ang, 1.0 - up, up


def _phone_light(F, at, t: float) -> None:
    """The amber call's light round the phone, before what it lies on or is held against: on the floor and
    the sofa's front, then round the hand and the head."""
    lit = ramp(t, *PHONE_LIT)
    if at is None or lit <= 0.0:
        return
    x, y, _, _, up = at
    floor = 1.0 - up
    if floor > 0.0:                                      # up the sofa's front and out over the rug: a warm place in the room
        glow(F, x, y - 34.0, 175.0, 105.0, C.AMBER_GLOW, 0.36 * lit * floor, power=1.3)
        glow(F, x, y - 6.0, 70.0, 34.0, C.SUN_HALO, 0.45 * lit * floor, power=1.2)
    glow(F, x, y - 4.0, 120.0 + 25.0 * up, 70.0 + 50.0 * up, C.AMBER_GLOW, (0.30 + 0.08 * up) * lit)


def _phone(F, D, t: float, at) -> dict | None:
    """The phone itself: drawn on quietly, lit amber on 250.74, ringing, hopped into the hand, held up to the
    ear. Drawn as the child would draw it, its lit face to us all the way (its light on the cheek), the
    empty lines of the screen going quiet as it comes up."""
    if at is None:
        return None
    x, y, rot, lie, up = at
    return phone(F, x, y, lit=ramp(t, *PHONE_LIT), warm=1.0, rot=rot, lie=lie, rings=RING_TIMES, bars=1.0 - 0.7 * up,
                 halo=1.0 - 0.6 * up, draw=seg(t, *PHONE_ON))


def _float(F, D, t: float):
    """Where the small tangle floats and where its string ends: in the hand (B10's call: rise 330, lean
    110), at the knot once the hands are at the armrest, then above the armrest on its string's length,
    bobbing less. Returns (x, y, end of the string, how much of the bow is drawn)."""
    tie = D.pts["tie"]
    hand = D.pts["string"] if t < TG else tie
    if TT + 0.3 < t < TG:                                # once the hands are at the armrest the string's end is the knot
        k = ease(seg(t, TT + 0.3, TT + 0.5))
        hand = (hand[0] + (tie[0] - hand[0]) * k, hand[1] + (tie[1] - hand[1]) * k)
    w = ease(seg(t, TT, TG + 0.15))
    x, y = float_at(F, hand, rise=RISE, lean=110.0 + (LEAN_TIED - 110.0) * w, bob=1.0 - 0.4 * w)
    return x, y, hand, seg(t, TT + 0.5, TG)


def _line(F, x, y, hand, bow: float, a: float = 1.0) -> None:
    """The string (gloom.on_string's own strokes and seeds), its bow round the armrest drawn on as the
    hands go round each other (at bow = 1 this is on_string(..., tie=True) without the tangle)."""
    if a <= 0.0:
        return
    st, _ = _string_pts(x, y, hand)
    chalk(F, st, C.PENCIL, 2.6, 0.9 * a, 771, wob=0.8, taper=0.8, edge=0.15)
    if bow > 0.0:
        hx, hy = hand
        P = spline(A((hx, hy), (hx - 13, hy - 9), (hx - 17, hy + 3), (hx, hy), (hx + 15, hy - 7), (hx + 16, hy + 5), (hx, hy),
                     (hx + 5, hy + 15)), 26)
        chalk(F, P, C.PENCIL, 2.4, 0.9 * a, 772, wob=0.5, taper=0.8, edge=0.15, draw=bow)


def _wall(F, t: float) -> None:
    """The family drawing on the wall, taped: a half on each of two attacks, then the two strips of tape."""
    Wd = wall_drawing(story.WALL_DRAWING[0] + DX, story.WALL_DRAWING[1], taped=True, day=True)
    for t0, names in WALL_ON:
        Wd.sub(*names).spread(t0, 0.0, 0.45, by=2)
    for j, t0 in enumerate(TAPE_ON):
        Wd.sub(f"pic.tape{j}").set_on(t0, t0 + 0.23)
    Wd.draw(F)


def _room_dust(F, R, t: float, least: float = 70.0) -> None:
    """Pastel dust let go where the tip has been on the room's fresh lines (s01's gesture of the intro,
    on the warm paper): it sinks, drifts and goes out over DUST_LIFE seconds."""
    pts = []
    for it in R.all():
        if not isinstance(it, Stroke) or not it.on or not (it.on[0] <= t < it.on[1] + DUST_LIFE):
            continue
        P = it.P
        u = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])
        if u[-1] < least:
            continue
        m = min(14, int(u[-1] / 50.0) + 2)
        for j in range(m):
            p = (j + 0.5 + 0.4 * rsym(it.seed * 31 + j, 3)) / m
            g = t - (it.on[0] + p * (it.on[1] - it.on[0]))
            if 0.0 <= g < DUST_LIFE:
                f = (0.5 * p + 0.5 * ease(p)) * u[-1]
                pts.append((float(np.interp(f, u, P[:, 0])), float(np.interp(f, u, P[:, 1])), g, it.seed * 31 + j))
    col = mix(C.EVE_LOW, C.PENCIL, 0.45)
    for lo, hi in ((0.0, 0.3), (0.3, 0.6), (0.6, 0.9)):
        q = [(x + 9.0 * rsym(j, 5) * g, y + 4.0 + 30.0 * g + 60.0 * g * g) for x, y, g, j in pts if lo <= g < hi]
        if q:
            xs, ys = zip(*q)
            specks(F, xs, ys, 1.9, col, 0.7 * (1.0 - (lo + 0.15) / DUST_LIFE) ** 1.3, "mid")


def draw(F):
    if S.joined(F, START, END):                          # (never True: s11 has no end hand-off)
        return
    t = F.t
    F.set_skin("day")
    F.cam = _cam(t)
    D = AP.s11(t, **CUE_KW)
    c = D.child
    _rise(c, t)
    _face(c, t)
    _wave(c, t)

    # ---- the room -----------------------------------------------------------------------------------
    paper_tone(F, 1.0)                                   # the sheet as B10 left it
    R = room("sunset", dx=DX)
    room_on_coda(R, F.tl)
    S.room_set(F, "sunset", DX, R=R, light=F.ramp(245.3, 247.0), drawing=0.0, phone_a=0.0, lamp_lit=F.ramp(*LAMP_ON), cushion=False)
    if t >= WALL_ON[0][0]:
        _wall(F, t)
    if ROOM_DUST[0] <= t < ROOM_DUST[1]:
        _room_dust(F, R, t)
    W = AP.window_friend(t)
    if W.a > 0.0:
        cx, cy, ww, wh = R.pt(FAR_WINDOW)
        with F.clip(rect=(cx - 0.5 * ww, cy - 0.5 * wh, cx + 0.5 * ww, cy + 0.5 * wh)):
            W.show(F)

    # ---- the child --------------------------------------------------------------------------------------
    at = _phone_at(D, t)
    _phone_light(F, at, t)
    on_floor = t < HOP[0]                                # from the hop on it is in front of the hand that takes it
    if on_floor:
        _phone(F, D, t, at)
    long_k = 1.0 - F.ramp(245.3, 246.6)                  # the bare sheet's long shadow goes as the room's light comes
    if long_k > 0.0:
        S.sun_shadow(F, c, 1.0, a=long_k)
    stand_k = (1.0 - long_k) * (1.0 - ramp(t, T["sit"], T["sit"] + 0.3))
    # the string: in front of the child while it is in its hand; behind it from the bend to the armrest
    # (the child stands in front of the sofa: the part over the child slips behind over nine frames);
    # in front again once the child is on the seat (its head on the armrest, the knot at the outer end)
    fx, fy, end, bow = _float(F, D, t)
    front = 1.0 - seg(t, *T_BEHIND)
    if T_BEHIND[0] <= t < T_SOFA:
        _line(F, fx, fy, end, bow)
    J = S.child(F, c, shadow=stand_k)
    R["cushion"].draw(F)
    if not on_floor:
        _phone(F, D, t, at)
    if t < T_BEHIND[1]:
        _line(F, fx, fy, end, bow, front)
    elif t >= T_SOFA:
        _line(F, fx, fy, end, bow)
    tangle(F, fx, fy, 56.0, 42.0, loops=6.0, seed=11, w=1.0)

    # ---- the end --------------------------------------------------------------------------------------
    k = ramp(t, T_LIFT[0] - 0.3, T_LIFT[0] + 0.9)
    if k > 0.0:                                          # a little chalk dust falls, turning in the window's light (on true time)
        l, t_, r, b = story.WINDOW
        dust(F, l - 260.0 + DX, t_ + 40.0, r + 40.0 + DX, FLOOR + 90.0, n=46, col=mix(C.SUN_CORE, C.CREAM, 0.5), a=0.85 * k, seed=78,
             t=t, drift=0.035, size=1.5)
        v = CAM_END.view(60)
        dust(F, v[0], v[1], v[2], FLOOR - 40.0, n=44, a=0.75 * k, seed=77, t=t, drift=0.025, size=1.3)
    F.post.fade = FADE[2] * ease(F.seg(*FADE[:2]))
    F.post.fade_col = C.EVE_PAPER
