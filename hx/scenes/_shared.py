"""hx.scenes._shared: the ten hand-off pictures, the layers the scene modules share, the joining rule.

A helper, not a scene (the registry skips names that start with an underscore). Read hx/scenes/README.md.

    from . import _shared as S

    def draw(F):
        if S.joined(F, "B4", "B5"):          # the last 0.25 s before the end hand-off: the hand-off picture, drawn here
            return
        ...                                  # your scene, built from the layers below; its first frame is S.handoff(F, "B4")

Every layer takes WORLD coordinates and maps them through F.cam; none of them sets the camera. A
frame is a pure function of time: what acts takes numbers computed from F.t, what is merely alive
runs on the boil clock by itself. No lyric text anywhere: lines are LRC indices and times.

    PYTHONPATH=. .venv/bin/python -m hx.scenes._shared ends s05_pre2       # your two ends against the hand-off pictures
    PYTHONPATH=. .venv/bin/python hx/_review/v4_scenes/_shared/proofs.py   # the ten pictures, sheets, costs, flicker
"""
from __future__ import annotations

import math

import numpy as np

from hx import story
from hx.chalk import *                                   # noqa: F401,F403
from hx.chalk import acting_child as AC
from hx.chalk import acting_pair as AP
from hx.chalk.weather import glow as _glow               # (friend() and pair() have an argument named glow)
from hx.story import FLOOR, HANDOFF, ROOM2_DX, X5, X9

__all__ = ["JOIN", "T", "CAM", "NAMES", "HIGH", "SEAM", "HOUSE", "CROW_TIMES", "B8_TREMBLE", "EMPTY_GHOST", "HEAD_CLEAR",
           "handoff", "joined", "hold", "child", "friend", "pair", "far_friend", "scribble", "cloud_between", "lid", "high_cloud", "clear_of", "tangle_on_string",
           "room_set", "room_light", "crow_wire", "bare", "plain_base", "sky_gap", "curtain", "calm_grips", "hill_world", "hill_ground", "sun_shadow",
           "rain_k", "rain_back", "rain_front", "amber_rim", "shaft_rim"]

JOIN = 0.25                                              # seconds before a hand-off in which a module draws only the hand-off picture
T = {n: h["t"] for n, h in HANDOFF.items()}              # the hand-off times
CAM = {n: Cam(*h["cam"]) for n, h in HANDOFF.items()}    # the hand-off cameras
NAMES = tuple(HANDOFF)

HIGH = HANDOFF["B7"]["cloud"]                            # the high cloud of B7: the curtains of s08 and s09 open out of it
SEAM = PART_GAP                                          # X5 + 180: where acting_pair.s08 parts the curtain
HOUSE = (layer_x(Cam(X9 + 90.0, 480.0, 0.75), 1585.0, FAR), FAR)     # the friend's house on the far hills (hills(house=HOUSE))
B8_TREMBLE = 0.5                                         # the shiver of the held strands in the long silence (world units)
EMPTY_GHOST = 0.16                                       # the ghost of the sheet's rim on the empty place (room_set empty=)

# the crows of the first verse: when each touches down on the wire (eleven in the end), and where
CROW_TIMES = tuple([24.265 + 0.75 * j for j in range(6)] + [29.5, 30.3, 32.3, 33.0, 33.8])


# ---------------------------------------------------------------------------------------------
# rain: one number of the song's time, the story's amounts at the hand-offs
# ---------------------------------------------------------------------------------------------
def rain_k(t: float) -> float:
    """The rain on the plain as rainfall's intensity: weather.rain_amount's curve made to pass through
    story.HANDOFF (0.6 hanging in the first silence, B2; 0.25 at B6, gone by 162; 0 at every other
    hand-off). It begins thinly at 54.6, falls with the band (58.6 to 59.0), thins from 75.5, stops by
    87; the storm from 138.2 (1.5 by 138.8), thinning from 150.1."""
    k = 0.60 * ramp(t, 54.6, 55.9) + 0.40 * ramp(t, 58.6, 59.0) - 0.50 * ramp(t, 75.5, 79.5) - 0.50 * ramp(t, 80.5, 87.0)
    k += 1.5 * ramp(t, 138.2, 138.8) - 1.05 * ramp(t, 150.1, 152.5) - 0.20 * ramp(t, 154.0, 157.6) - 0.25 * ramp(t, T["B6"], 162.0)
    return max(0.0, k)


def rain_back(F: Frame, k: float | None = None) -> None:
    """The far rain (before the ground line and the figures). k: default rain_k(F.t)."""
    rainfall(F, rain_k(F.t) if k is None else k, "back")


def rain_front(F: Frame, k: float | None = None) -> None:
    """The rain of the figures' plane, its splashes, the drops near the lens (after the figures and the scribble)."""
    rainfall(F, rain_k(F.t) if k is None else k, "front")


# ---------------------------------------------------------------------------------------------
# the two figures
# ---------------------------------------------------------------------------------------------
def amber_rim(k: float = 1.0):
    """figure()'s rim for the friend's light on the child (the friend is always on its right)."""
    return (C.AMBER, 1, k)


def shaft_rim(F: Frame, k: float = 1.0, from_=(0.35, -1.0)):
    """figure()'s rim for pale light falling on a figure from above (the thin place, the shaft)."""
    return (light_col(F), from_, k)


def _shade(F: Frame, act, a: float, w: float = 0.27) -> None:
    ground_shadow(F, act.x + 4.0 * act.face, act.y + 5.0, w * act.h, 0.62 * a * act.a)


def child(F: Frame, act, rim=None, a: float = 1.0, shadow: float = 1.0) -> dict:
    """The child: an Act of the acting modules (AC.s01(F.t) .., AC.hold_B3(F.t), a Duet's .child) drawn
    with the story's seed, height and skin, on its contact shadow. rim: amber_rim(k) / shaft_rim(F, k)
    or None. a: pressure on top of the Act's own. shadow: 0..1 (0 on the sofa). Returns figure()'s
    joints (pinned hands applied)."""
    if shadow > 0.0 and act.draw > 0.0:
        _shade(F, act, shadow * a * min(1.0, act.draw * 2.0))
    return act.show(F, a=a, **({} if rim is None else {"rim": rim}))


def friend(F: Frame, act, rim=None, a: float = 1.0, glow: float = 1.0, wet: float = 0.0, shadow: float = 1.0) -> dict:
    """The friend (an acting_pair Act): its amber glow, its contact shadow, the figure. glow: 0..1
    (nothing on the day paper); wet: 0..1 its reflection on wet ground. Returns the joints."""
    J = act.joints()
    if glow > 0.0 and not F.day:
        amber_glow(F, act.x, act.y, act.y - (J["head"][1] - J["R"]), a=glow * a * act.a, wet=wet)
    if shadow > 0.0 and F.day:
        _shade(F, act, shadow * a)
    return act.show(F, a=a, **({} if rim is None else {"rim": rim}))


def pair(F: Frame, D, child_rim=None, friend_rim=None, a: float = 1.0, glow: float = 1.0, wet: float = 0.0,
         shadow: float = 1.0, warm: float = 0.0):
    """Both figures of a Duet (AP.s06(F.t) .., AP.hold_B7(F.t)) in its order. warm: 0..1 the friend's
    warmth on the child once they touch (D.num["warm"] in s06; 1 at B6 and B7): an amber rim on the
    child's right side (unless you give child_rim) and a small glow where the hands meet
    (D.pts["hands"], or the hand on the shoulder). The other arguments as child() and friend().
    Returns (child joints, friend joints or None)."""
    if child_rim is None and warm > 0.0 and not F.day:
        child_rim = amber_rim(0.5 * warm)
    jc = jf = None
    for who in D.order:
        if who == "f" and D.friend is not None:
            jf = friend(F, D.friend, friend_rim, a, glow, wet, shadow)
        elif who == "c":
            jc = child(F, D.child, child_rim, a, shadow)
    touch = D.pts.get("hands") or D.pts.get("shoulder")
    if warm > 0.0 and touch is not None and D.friend is not None and not F.day:
        _glow(F, touch[0], touch[1], 46.0, 40.0, a=0.28 * warm * a)
    return jc, jf


def far_friend(F: Frame, act, wet: float = 1.0, glow: float = 0.6) -> dict:
    """The far friend of the first chorus (AP.s03_friend(F.t)): a warm point in the cold frame. Its
    glow (kept under 0.6: a full glow washes its thin limbs out), its reflection on the wet ground,
    the figure; as it leaves (num["point"]) it becomes a point of amber light."""
    p = act.num.get("point", 0.0)
    on = min(1.0, act.draw * 1.5)
    amber_glow(F, act.x, FLOOR, act.h, a=glow * on * (1.0 - 0.5 * p), wet=wet * on * (1.0 - p))
    J = act.show(F)
    if p > 0.0:
        amber_point(F, act.x, FLOOR - 0.5 * act.h, a=p)
    return J


# ---------------------------------------------------------------------------------------------
# the scribble
# ---------------------------------------------------------------------------------------------
def scribble(F: Frame, cloud, J: dict, k: float = 1.0, slack: float = 0.8, a: float = 1.0, strand_: float = 1.0,
             dust: float = 0.5, tug=None):
    """The cloud over the child, its belly resting on the child's crown, and the strand from the crown
    up into it; a little pale dust falling from it. cloud = (cx, cy, rx, ry): story.HANDOFF[..]["cloud"]
    at a hand-off (ease it after the child between them: it is heavy). J: the child's joints. k: how
    far the belly has come down on the crown (1 at every hand-off). strand_: 0..1 how far the strand
    has been drawn from the crown (0: none; it exists from 31.58). With k = 1, slack = 0.8 this is
    gloom.handoff_gloom's call for B1 .. B5. Draw it after the child. Returns the cloud's Tip (.band)."""
    crown = J["crown"]
    Tp = gloom(F, *cloud, a=a, rest=(crown[0], crown[1] + 6.0, k), avoid=[(J["head"][0], J["head"][1], J["R"])], tug=tug)
    if strand_ > 0.0:
        strand(F, crown, Tp.band.root(crown[0] + 40.0, 0.4), slack=slack, a=a, draw=strand_)
    if dust > 0.0:
        gloom_dust(F, cloud[0] - 0.8 * cloud[2], cloud[0] + 0.8 * cloud[2], 0.0, band=Tp.band, a=dust * a)
    return Tp


def cloud_between(a: str, b: str, w: float, x: float | None = None):
    """The cloud's numbers (cx, cy, rx, ry) between two hand-offs: story.HANDOFF[a]["cloud"] at
    w = 0, [b]'s at w = 1 (exactly). x: the child's ground x now (ease it: the cloud is heavy and
    lags): the centre then hangs 30 units left of it, as at every hand-off."""
    ca, cb = HANDOFF[a]["cloud"], HANDOFF[b]["cloud"]
    w = min(1.0, max(0.0, float(w)))
    c = tuple(cb) if w >= 1.0 else tuple(ca) if w <= 0.0 else tuple(p + (q - p) * w for p, q in zip(ca, cb))
    return c if x is None else (x - 30.0,) + c[1:]


HEAD_CLEAR = 1.3                                         # high_cloud: how far (in head radii) its loose loops keep off a head


def clear_of(*joints, k: float = 1.0) -> list:
    """The avoid= discs (gloom, ceiling, lid) that keep the scribble's loose loops off these heads: a
    loop ending on a head reads as a strand, and only the child is tied to the scribble (until
    173.5). joints: figure joints (None is skipped). The disc also keeps the scribble's tone off the
    head: no larger than HEAD_CLEAR head radii, or the hole shows round the hair. k: 0..1 how far
    they are kept off (ease it to 0 over 0.4 s or more before handing the scribble to a form that has
    no avoid=, such as S.curtain: at k = 0 the loops hang as gloom draws them by themselves)."""
    if k <= 0.0:
        return []
    return [(J["head"][0], J["head"][1], k * HEAD_CLEAR * J["R"]) for J in joints if J is not None]


def high_cloud(F: Frame, heads=(), a: float = 1.0, clear: float = 1.0, **kw):
    """The high cloud of B7 (gloom(F, *HIGH)) with its loose hanging loops kept off the figures'
    heads (clear_of). heads: the joints of the figures under it (pair()'s (jc, jf)). clear: clear_of's
    k (1 at B7; s08 eases it to 0 before S.curtain takes the cloud over: at clear = 0 these are the same
    strokes as S.curtain(F, None, None, spread=0, drop=0, light=0), which is drawn before the figures). kw goes to gloom (draw=, grow=, tug=).
    After the figures. Returns gloom's Tip."""
    return gloom(F, *HIGH, a=a, avoid=clear_of(*heads, k=clear), **kw)


def tangle_on_string(F: Frame, hand, face: int = 1, a: float = 1.0):
    """The small tangle on its string over the hand that holds it (the child's hand at its hip): what
    gloom.handoff_gloom draws at B9 (face +1) and B10 (face -1). Lean the float yourself while the
    child runs (gloom.float_at). After the figures. Returns where the string meets the tangle."""
    return on_string(F, *float_at(F, hand, rise=STRING["rise"], lean=-face * STRING["lean"]), hand, a=a)


def lid(F: Frame, ax: float, crown=None, thin: float = 0.0, slack: float = 0.8, hang: float = 235.0, cam: Cam | None = None, **kw):
    """The scribble as a lid over the plain (the choruses, the bridge), made for the camera in force,
    and the strand from the child up into it. ax: its anchor (the cx of the cloud it opened out of:
    X2 - 30 in chorus 1, 4270 from B5 to B6, moving to 4390 as it gathers into B7's high cloud).
    crown: where the strand leaves the child (J["crown"], a fist; None: no strand). thin: 0..1 the
    thin pale place over the two (F.ramp(155.6, 157.0); 1 at B6). hang: how low it hangs (screen px).
    kw goes to gloom.ceiling: cloud=, spread= (a cloud opening into the lid and back), sag=, rest=,
    avoid=, amount= (the unravelling), draw=. With thin = 1 and the camera of B6 this is
    gloom.handoff_gloom's call for B6. After the light (sky_gap) and the ground line, BEFORE the
    figures. Returns ceiling's Tip (.band)."""
    x, r, th = THIN_PLACE
    Tp = ceiling(F, ax=ax, thin=(x, r, th * thin) if thin > 0.0 else None, **kw, **lid_for(cam or F.cam, hang=hang))
    if crown is not None:
        strand(F, crown, Tp.band.root(crown[0] + 40.0, 0.3), slack=slack)
    return Tp


def sky_gap(F: Frame, k: float = 1.0) -> None:
    """The guess of light under the thin pale place of the lid (155.6 to 173.5; k = 1 at B6). Before
    the ground line and the lid."""
    x = THIN_PLACE[0]
    gap_light(F, x, 60.0, F.cam.view()[1] - 40.0, x, 170.0, FLOOR, a=0.45, open_=k)


def calm_grips(D, t: float):
    """The two grips of AP.s08(t) / AP.hold_B8(t) with their shiver taken out: (left, right) world
    points for the curtains, so that the opening's edges stand still while the hands shiver on them
    by a unit (the long silence is then still but for breath, hands and dust). (None, None) before
    the hands are in."""
    gl, gr = D.pts.get("grip_l"), D.pts.get("grip_r")
    k = D.num.get("tremble", 0.0)
    if gl is None or gr is None or k <= 0.0:
        return gl, gr
    (ax, ay), (bx, by) = AP._tremble(t, k), AP._tremble(t + 0.37, k)     # as s08 and hold_B8 add it
    return (gl[0] - ax, gl[1] - ay), (gr[0] - bx, gr[1] - by)


def curtain(F: Frame, left, right, tremble: float = 0.0, light: float = 1.0, spread: float = 1.0, drop: float = 1.0,
            rip=None, stays=None, cam: Cam | None = None, dust_t=None):
    """The scribble let down as two curtains and parted at the seam where acting_pair.s08 opens it
    (SEAM = X5 + 180), with the light through the opening: one call for the whole of s08 and for the
    rip of s09. left, right: the grips (D.pts["grip_l"], D.pts["grip_r"]; None: shut). tremble: the
    shiver of the held strands. light: 0..1 strength of the shaft. spread, drop: the high cloud of B7
    opening into the lid, the lid coming down (both 0 at B7, 1 from about 184.3). rip: seconds since
    201.25 (None before), stays: the piece that stays. cam: the camera the lid is made for (default
    F.cam; s09 passes CAM["B8"] once its camera travels). dust_t: the clock of the dust in the shaft
    (F.t in the long silence). After the land, before the figures. Returns curtains' Tip."""
    L = lid_for(cam or F.cam, hang=PART_HANG)
    if left is not None and right is not None and light > 0.0 and rip is None:
        G = curtain_gap(cam or F.cam, SEAM, None, left, right, s=L["s"])
        gap_light(F, *G, a=light, open_=min(1.0, G[4] / 40.0), t=dust_t)
    kw = dict(cloud=band_cloud(*HIGH), spread=spread) if spread < 1.0 else {}
    return curtains(F, ax=HIGH[0], drop=drop, gap=SEAM, left=left, right=right, strands=None, tremble=tremble, rip=rip,
                    stays=stays, **kw, **L)


# ---------------------------------------------------------------------------------------------
# the room
# ---------------------------------------------------------------------------------------------
def crow_wire(F: Frame, dx: float = 0.0, times=CROW_TIMES):
    """The wire under the eaves as the crows have left it at F.t: (wire polyline, their places). Each
    landing dips the wire and sets it swinging."""
    l, _, r, _ = story.WINDOW
    xs = perches(l + 26.0 + dx, r - 26.0 + dx, len(times))
    dips = [(xs[j], 5.0 * (1.0 + swing(F.t - times[j])), 70.0) for j in range(len(times)) if F.t >= times[j] - 0.1]
    return wire_pts(dips=dips, dx=dx), xs


def room_light(F: Frame, mood: str = "night", dx: float = 0.0, a: float = 1.0) -> None:
    """The window's light in the room at dx: its glow on the wall round the frame and its pool on the
    floor (night: cold and slanting; eve: one long pale pool; sunset: gold going to orange). After
    R.back(F), before R.view(F). room_set calls it; call it yourself round a declared change."""
    if a <= 0.0:
        return
    m = "evening" if mood in ("eve", "evening") else mood
    l, t_, r, b = (story.WINDOW[0] + dx, story.WINDOW[1], story.WINDOW[2] + dx, story.WINDOW[3])
    window_glow(F, l, t_, r, b, a, m)
    if m == "evening":
        window_pool(F, l - 20.0, r + 10.0, FLOOR + 14.0, a, -0.9, 380.0, mood=m)
    else:
        window_pool(F, l - 20.0, r + 10.0, FLOOR + 14.0, a, mood=m)


def room_set(F: Frame, mood: str = "night", dx: float = 0.0, R=None, light: float = 1.0, pane_rain: float = 0.0,
             crow_times=None, crow_leave=None, drawing: float = 1.0, empty: float = 0.0, phone_lit: float = 0.0,
             phone_a: float = 1.0, lamp_lit: float = 1.0, cushion: bool = True, wall_off=None):
    """The room where it stands, complete and in paint order up to the sofa: dressing, the window's
    light, what the window shows (the amber window lit), rain on the pane, the crows on the wire, the
    GROUND LINE, wall, window, lamp (lit in the coda), shelf, table, rug, the family drawing on the
    wall, the phone on the rug, the sofa, the cushion.

    mood: "night" (dx 0), "eve" (dx ROOM2_DX), "sunset" (dx ROOM3_DX, on the day skin).
    R: your own Place with its schedule (sets.room_on, room_on_coda): default room(mood, dx=dx). R may
    also be a declared change (sets.room_to_class(w), plain_to_room(w), room_to_corridor(w) ..: a
    Change at this dx): it is then drawn whole (R.draw(F): the leaving set's groups, then the
    arriving set's) and the wall drawing and the phone are laid over it (they touch nothing of the
    room); take them off with the room (wall_off, phone_a), and cushion is the Change's own.
    light: 0..1 the window's glow and pool (room_light). pane_rain: rain_window's k (0.6 in the first
    verse). crow_times: when each crow lands (CROW_TIMES; None: no crows), crow_leave: when each flies
    up. drawing: pressure of the family drawing (torn; taped in the coda; 0: none). empty: the empty
    place where it hung (its two pins and a faint ghost of the sheet): the evening room, while the
    child carries the two halves in its jumper (55 to 162; B3 has empty = 1, drawing = 0). wall_off:
    (t0, t1) the drawing or the empty place taken back from its ends with the room (Sketch.set_off;
    None: it stays). phone_lit: its screen (pale; amber in the coda), phone_a: its pressure (0: not
    on the rug). lamp_lit: the coda's lamp. cushion=False: draw R["cushion"] yourself after a child
    that lies on the sofa. Returns R."""
    R = room(mood, dx=dx) if R is None else R
    change = isinstance(R, Change)
    sunset = mood == "sunset"
    R.back(F)
    room_light(F, mood, dx, light)
    wire = None
    if crow_times is not None:
        wire, xs = crow_wire(F, dx, crow_times)
    R.view(F, **({} if wire is None else {"wire": wire}))
    if pane_rain > 0.0:
        rain_window(F, *R.rect(PANE), pane_rain)
    if crow_times is not None:
        with F.clip(rect=R.rect(story.WINDOW)):
            crows_on_wire(F, wire, crow_times, xs, leave=crow_leave)
    ground_line(F)
    if change:
        R.draw(F)
    else:
        R.draw(F, "wall", "window", "lamp")
    if sunset and lamp_lit > 0.0:
        lamp_light(F, story.LAMP_X + dx, FLOOR, 520.0, lamp_lit)
    if not change:
        R.draw(F, "shelf", "table", "rug")
    _wall(F, dx, drawing, empty, sunset, wall_off)
    if phone_a > 0.0:
        px, py = story.PHONE
        phone(F, px + dx, py, lit=phone_lit, warm=1.0 if sunset else 0.0, a=phone_a)
    if not change:
        R.draw(F, "sofa")
        if cushion:
            R.draw(F, "cushion")
    return R


def _wall(F: Frame, dx: float, drawing: float, empty: float, taped: bool, off) -> None:
    """The family drawing on the wall at story.WALL_DRAWING + dx, or the empty place where it hung."""
    wx, wy = story.WALL_DRAWING
    if empty > 0.0:
        Wd = wall_drawing(wx + dx, wy, day=F.day)
        ghost = Wd.sub("pic.l.sheet", "pic.r.sheet").without("pic.l.sheet.fill", "pic.r.sheet.fill")
        pins = Wd.sub("pic.pin_l", "pic.pin_r")
        if off is not None:
            ghost.set_off(*off)
            pins.set_off(*off)
        ghost.draw(F, a=EMPTY_GHOST * empty)
        pins.draw(F, a=empty)
    if drawing > 0.0:
        Wd = wall_drawing(wx + dx, wy, taped=taped, day=F.day)
        if off is not None:
            Wd.set_off(*off)
        Wd.draw(F, a=drawing)


# ---------------------------------------------------------------------------------------------
# the bare sheet, the plain, the hill world
# ---------------------------------------------------------------------------------------------
def bare(F: Frame, hour: float = 1.0) -> None:
    """The bare sheet: the ground line only (on the day skin the sheet toned toward evening first)."""
    if F.day:
        paper_tone(F, hour)
    ground_line(F)


def plain_base(F: Frame, vx: float = X5, k: float | None = None, a: float = 1.0, wet: float | None = None, hill: bool = False,
               reach=None, far: float = 1.0) -> None:
    """The plain of the choruses behind everything: its ground (tone, furrows, puddles, far shapes),
    the mist on the horizon, the far rain. NOT the ground line (ground_line(F), or hill_ground(F) once
    the first hill exists: after the light). vx: where the furrows run to (story.X2 in chorus 1,
    story.X5 from chorus 2 on; fixed for a scene). k: the rain (default rain_k(F.t)). a: pressure of
    ground and mist (0 on a bare sheet: only the far rain is drawn then, as at B2 and B5; bring it up
    over 6 frames or more while reach spreads the ground out from the child). wet: the puddles
    (default: there while it rains; let them dry later yourself). hill=True: the ground marks stop at
    the foot of the first hill (from 175 on)."""
    k = rain_k(F.t) if k is None else k
    if a > 0.0:
        wet = min(1.0, k / 0.25) if wet is None else wet
        plain(F, vx=vx, a=a, haze=0.4, wet=wet, rain=min(1.0, k), far=far, reach=reach, end=FLAT_TO if hill else None)
        mist(F, a=a)
    rainfall(F, k, "back")


def hill_ground(F: Frame, rise: float = 1.0, a: float = 1.0) -> float:
    """The night land before the sheet rips: the hills' own near ground (it covers the plain's
    furrows below the line: change over with a, 6 frames or more, before the hill is born at 175.0),
    the first hill alone (rise 0..1: hill_rise(w) while it is born, 1 from 178.2), no far layers, no
    light; it draws the ground line. Returns the rise drawn."""
    return hills(F, rise=rise, back=0.0, lit=0.0, a=a)


def sun_shadow(F: Frame, act, hour: float = 0.0, a: float = 1.0, rise: float = 0.0) -> None:
    """The shadows of a figure in the low sun of the day skin (the sun stands on the right: the long
    one falls to the left and toward us) and its contact shadow. act: the figure's Act; hour as
    hill_world's; rise: the land's rise there (0: the flat line, the bare sheet of B10). The long one
    lets go of the feet in a jump (Act.lift). Before the figure (draw it with shadow=0); nothing on
    the night paper."""
    if not F.day or a <= 0.0:
        return
    lift = getattr(act, "lift", 0.0)
    gy = act.y + lift
    long_shadow(F, act.x, gy, act.h, act.x + 3000.0, a=0.85 * a, length=1.35 + 0.45 * hour, fall=0.20 - 0.03 * hour,
                lift=lift, curve=land_curve(rise) if rise > 0.0 else None, seed=getattr(act, "seed", 3))
    ground_shadow(F, act.x, gy + 3.0, 0.26 * act.h, 0.6 * a / (1.0 + lift / 60.0))


def hill_world(F: Frame, hour: float = 0.0, gone: float = 0.0, back=1.0, lit: float = 1.0, light: float = 1.0,
               figures=(), bloom=1.0, grow: float | None = None, skip=None, tree_a: float = 1.0) -> float:
    """The hill world in the skin of F (give it to day.ring: it is drawn twice): sky, the three layers
    of hills with the friend's house, the tree, the shadows of the figures, flowers; it draws the
    ground line. hour: 0 afternoon gold .. 1 evening. gone: 0..1 the un-drawing (242.0 to 244.2).
    back, lit, light: the night land after the rip (the far layers drawing on, the pale light on the
    slopes, the sky's): all 1 by day. figures: the Acts whose shadows lie on the land (sun_shadow:
    they stay when the land is rubbed out). bloom: flowers' open_ (hills.ring_bloom while the ring
    passes); grow: their stems (default: they go with gone). skip: (xa, xb) no flowers at the
    figures' feet. tree_a: pressure of the tree at x 6840 (0: none). Returns the rise drawn: the
    figures stand on ground_y(x, r)."""
    sky(F, hour, gone=gone, light=light)
    r = hills(F, back=back, lit=lit, hour=hour, gone=gone, house=HOUSE)
    k = tree_a * (1.0 - seg(gone, 0.0, 0.3))
    if k > 0.0:
        tree(F, 6840.0, hour=hour, a=k)
    for act in figures:
        if act is not None:
            sun_shadow(F, act, hour, rise=r)
    g = (1.0 - seg(gone, 0.1, 0.5)) if grow is None else grow
    if g > 0.0:
        flowers(F, 4700.0, 9300.0, 150, seed=2, open_=bloom, grow=g, rise=r, skip=skip)
    return r


# ---------------------------------------------------------------------------------------------
# the ten hand-off pictures
# ---------------------------------------------------------------------------------------------
def hold(name: str, t: float):
    """The figures' rest state at a hand-off: an Act (B1 .. B5) or a Duet (B6 .. B10)."""
    if name in AC.CHILD_HANDOFF:
        return AC.CHILD_HANDOFF[name][1](t)
    if name == "B9":
        return AP.hold_B9(t, ground=ground_y)
    return AP.PAIR_HANDOFF[name](t)


def _b_room(F, name):
    H = HANDOFF[name]
    if name == "B1":
        room_set(F, "night", 0.0, pane_rain=0.6, crow_times=CROW_TIMES)
    else:
        room_set(F, "eve", ROOM2_DX, drawing=0.0, empty=1.0, phone_lit=0.85)    # the halves are in its jumper
    J = child(F, hold(name, F.t))
    scribble(F, H["cloud"], J)


def _b_bare(F, name):
    H = HANDOFF[name]
    k = H["rain"]
    rain_back(F, k)
    bare(F)
    J = child(F, hold(name, F.t))
    scribble(F, H["cloud"], J)
    rain_front(F, k)


def _b6(F):
    k = HANDOFF["B6"]["rain"]
    D = hold("B6", F.t)
    plain_base(F, X5, k)
    sky_gap(F)
    ground_line(F)
    lid(F, HANDOFF["B5"]["cloud"][0], D.child.joints()["crown"], thin=1.0, avoid=clear_of(D.friend.joints()))
    pair(F, D, wet=0.6, warm=1.0)                    # where they touch, amber rubs off on the child
    rain_front(F, k)


def _b7(F):
    D = hold("B7", F.t)
    plain_base(F, X5, 0.0, hill=True)
    hill_ground(F)
    jc, jf = pair(F, D, warm=1.0)
    high_cloud(F, heads=(jc, jf))


def _b8(F):
    D = hold("B8", F.t)
    gl, gr = calm_grips(D, F.t)
    plain_base(F, X5, 0.0, hill=True)
    hill_ground(F)
    curtain(F, gl, gr, B8_TREMBLE, cam=CAM["B8"], dust_t=F.t)
    pair(F, D, child_rim=shaft_rim(F, 0.7, (0.5, -1.0)), friend_rim=shaft_rim(F, 0.5, (-0.5, -1.0)))


def _b9(F):
    D = hold("B9", F.t)
    c, f = D.child, D.friend
    hill_world(F, figures=(c, f), skip=(c.x - 70.0, f.x + 70.0))
    pair(F, D, shadow=0.0)
    tangle_on_string(F, D.pts["string"], 1)


def _b10(F):
    D = hold("B10", F.t)
    bare(F)
    sun_shadow(F, D.child, 1.0)
    child(F, D.child, shadow=0.0)
    tangle_on_string(F, D.pts["string"], -1)


_PICTURES = {"B1": lambda F: _b_room(F, "B1"), "B2": lambda F: _b_bare(F, "B2"), "B3": lambda F: _b_room(F, "B3"),
             "B4": lambda F: _b_bare(F, "B4"), "B5": lambda F: _b_bare(F, "B5"), "B6": _b6, "B7": _b7, "B8": _b8,
             "B9": _b9, "B10": _b10}


def handoff(F: Frame, name: str) -> None:
    """The complete hand-off picture `name` ("B1" .. "B10") at F.t, exactly as story.HANDOFF gives it:
    camera, skin, set, light, things, the figures in their rest state (alive, not acting), the
    scribble, rain, finish. A function of time: near the hand-off it is the living rest state."""
    H = HANDOFF[name]
    if H["skin"] != F.skin:
        F.set_skin(H["skin"])
    F.cam = CAM[name]
    _PICTURES[name](F)


def joined(F: Frame, start: str | None, end: str | None) -> bool:
    """The joining rule. Call it first in draw(F) with the names of the hand-offs your module starts
    from and ends on (None for s01's start and s11's end):

        if S.joined(F, "B4", "B5"):
            return

    In the last JOIN (0.25) seconds before the end hand-off it draws handoff(F, end) and returns True:
    your own drawing must have arrived at that state before then, and both neighbours draw the same
    code there. Otherwise it draws nothing and returns False. It never draws the start: your own
    drawing at your first frame must be the picture handoff(F, start) (prove it with
    python -m hx.handoff, and at the same instant with python -m hx.scenes._shared ends <module>)."""
    if start is not None and F.t < T[start] - 1e-9 or end is not None and F.t >= T[end]:
        raise ValueError(f"joined({start}, {end}) called at {F.t:.3f}, outside that span")
    if end is not None and F.t >= T[end] - JOIN - 1e-6:
        handoff(F, end)
        return True
    return False


# ---------------------------------------------------------------------------------------------
# the animator's check of a module's two ends (same time, two drawings: no boil step between them)
# ---------------------------------------------------------------------------------------------
def check_ends(module: str, out: str = "hx/_review/v4_scenes/ends") -> list:
    """python -m hx.scenes._shared ends s05_pre2

    The module's own drawing against the hand-off pictures at the SAME times: at its first frame
    against handoff(F, START) (it must start from that picture; a first move that has just begun
    shows as a fraction of a level), and at its last frame before the joined() window against
    handoff(F, END) (it must have arrived: about 0; the last ease of a move may show as a fraction
    of a level). Prints the mean change in levels, the share of
    pixels over 8 levels and the worst 96 px block; writes own | hand-off | difference x 8."""
    import importlib
    from pathlib import Path

    from PIL import Image

    from hx.chalk import proof
    mod = importlib.import_module(f"hx.scenes.{module}")
    luma = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    rows = []
    for which, name in (("start", mod.START), ("end", mod.END)):
        if name is None:
            continue
        n = math.ceil(T[name] * FPS - 0.5) if which == "start" else math.ceil((T[name] - JOIN) * FPS - 0.5) - 1
        t = (n + 0.5) / FPS
        own = proof.frame(mod.draw, t)
        ref = proof.frame(lambda F: handoff(F, name), t)
        d = np.abs(own.astype(np.float32) @ luma - ref.astype(np.float32) @ luma)
        blk = d[:H // 96 * 96, :W // 96 * 96].reshape(H // 96, 96, W // 96, 96).mean((1, 3))
        by, bx = np.unravel_index(int(blk.argmax()), blk.shape)
        rows.append((which, name, t, float(d.mean()), float((d > 8).mean() * 100.0), float(blk.max()), (int(bx) * 96 + 48, int(by) * 96 + 48)))
        Path(out).mkdir(parents=True, exist_ok=True)
        diff = np.repeat(np.clip(d * 8.0, 0, 255).astype(np.uint8)[::2, ::2, None], 3, axis=2)
        Image.fromarray(np.hstack([own[::2, ::2], ref[::2, ::2], diff])).save(Path(out) / f"{module}_{which}_{name}.jpg", quality=90)
        print(f"{module} {which:5s} {name:3s} t={t:8.3f}: {rows[-1][3]:5.2f} levels, {rows[-1][4]:5.2f} % over 8, "
              f"worst block {rows[-1][5]:5.1f} at {rows[-1][6]}")
    return rows


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "ends":
        for m in sys.argv[2:]:
            check_ends(m)
    else:
        print("usage: python -m hx.scenes._shared ends <module> [<module> ...]      (e.g. s05_pre2)")
