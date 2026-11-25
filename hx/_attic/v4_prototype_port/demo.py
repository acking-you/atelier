"""hx.chalk.demo: the prototype's four key scenes on the kit, and the proof images.

The scenes are registered on the song's clock by hx/scenes/demo_*.py (stand-ins: a real scene with an
overlapping SPAN wins over them): the room 0-36 (draws itself on with the beats, the title, then the
uncut change into the classroom from 33.0), the plain 58.6-80 (the pull-back at 60.27), the colour
ring 213-227 and the day field 227-244. They are examples of the API, not the film's scenes.

    PYTHONPATH=. .venv/bin/python -m hx.chalk.demo            # everything into hx/_review/v4_core/
    PYTHONPATH=. .venv/bin/python -m hx.chalk.demo stills pullback change crops cost clips before flicker
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np

from . import title
from .core import A, C, Cam, Frame, H, W, chalk, ease, ease_out, fill, htab, mix, seg, smudge, spline, wash
from .day import cloud, ring, sky, sun, tear_light
from .figure import F_CALL, HOLD, STOPPED, Pose, figure, walk
from .gloom import ceiling, gloom, on_string
from .props import (back_figure, board, bud, chair, crow, cushion, desk, door, floorboards, flower, footprints, grass, hill,
                    house, lamp, night_wall, phone, plain_ground, pupil, rug, sofa, table3, tree, voice, wall_drawing,
                    window, window_day, window_night)
from .sketch import Sketch, morph
from .weather import glow, ground_shadow, moon_pool, rain

OUT = Path(__file__).resolve().parents[1] / "_review" / "v4_core"
PROTO = Path(__file__).resolve().parents[1] / "_tmp" / "proto_chalk"

# ==========================================================================
# the room at night (intro, first verse) and its change into the classroom
# ==========================================================================
FLOOR = 742.0
SOFA_X, SOFA_W = 230.0, 760.0
WIN = (1300.0, 170.0, 1670.0, 560.0)
T_CHANGE = (33.0, 35.9)
SOFA_CLING = Pose(pel=(-0.07, 0.105), lean=1.02, bend=0.30, neck=-0.18, look=(0.05, -0.22), eye=0.62, brow=0.0,
                  mouth=-0.15, hf=(0.10, -0.16), hb=(0.20, -0.02), ef=1.0, eb=-1.0, ff=(-0.335, 0.03), fb=(-0.44, 0.022),
                  kf=-1.0, kb=-1.0, af=-0.5, ab=-0.25, hair=0.0, open=0.5, front=1.0)


def room_set(drawing_gap=12.0, apart=0.6) -> dict:
    """The room as named sets, back to front."""
    return dict(far=table3(1790, FLOOR + 2, 1.3, 420, C.CHALK_DIM, 0.9, apart=apart) + lamp(132, FLOOR + 4, 520, 440, C.CHALK_DIM, 0.85),
                win=window(*WIN, seed=200), pic=wall_drawing(1140, 418, 1.0, gap=drawing_gap, seed=300),
                rug=rug(640, FLOOR + 62, 500, 50), sofa=sofa(SOFA_X, FLOOR + 2, SOFA_W, 100),
                cushion=cushion(SOFA_X + 185, FLOOR - 150, 1.0, -0.5, 120))


def _room_light(F, a=1.0, day=0.0):
    l, tp, r, b = WIN
    smudge(F, (l + r) / 2, (tp + b) / 2, 520, 420, mix(C.MOON, (0.80, 0.84, 0.92), day), (0.16 + 0.06 * day) * a, "soft",
           additive=True, power=1.5)
    moon_pool(F, l - 20, r + 10, FLOOR + 14, (1.0 - 0.25 * day) * a)


def room(F: Frame, crows=1):
    """key1. In the intro the set draws itself on with the beats; the child is drawn last; then the
    scribble grows. From 13 s on it is the prototype's picture (static camera)."""
    t, tl = F.t, F.tl
    S = room_set()
    if t < 13.0:
        S["sofa"].on_beats(tl, 1.0, every=1.0, dur=1.6)            # one part of the sofa per beat
        S["cushion"].on_beats(tl, 6.6, dur=1.2)
        S["win"].on_beats(tl, 3.6, every=0.5, dur=1.2)             # the window, a line per half beat
        S["pic"].on_beats(tl, 7.4, every=0.25, dur=0.8)
        S["far"].on_beats(tl, 8.0, every=1.0, dur=1.5, by=2)       # table, each chair, the lamp: one per beat
        S["rug"].on_beats(tl, 9.4, every=0.5, dur=1.2)
    lit = F.ramp(0.3, 2.5)
    night_wall(F, FLOOR - 24, a=lit)
    floorboards(F, FLOOR, a=0.22 * lit, draw=F.seg(0.26, 1.0))             # first the skirting line shoots across
    glass = F.ramp(4.3, 6.0)                                       # the pane fills in once its frame stands
    _room_light(F, glass)
    l, tp, r, b = WIN
    S["rug"].draw(F)
    S["far"].draw(F)
    if glass > 0.0:
        if glass < 1.0:
            F.c.saveLayerAlpha(None, int(255 * glass))
        window_night(F, l, tp, r, b, crows=crows)
        if glass < 1.0:
            F.c.restore()
    S["win"].draw(F)
    S["pic"].draw(F)
    S["sofa"].draw(F)
    S["cushion"].draw(F)
    smudge(F, SOFA_X + SOFA_W / 2, FLOOR + 14, SOFA_W * 0.56, 26, C.GLOOM, 0.75 * F.ramp(4.0, 6.5), "soft")   # contact shade
    # the child, clinging to the armrest, breathing
    x0, y0, h = 815.0, FLOOR - 124.0, 380.0
    born = F.seg(9.2, 12.0)
    smudge(F, x0 + 60, y0 - 60, 330, 210, C.MOON, 0.10 * born, "soft", additive=True)
    br = math.sin(t * 2 * math.pi / 4.2)
    P = SOFA_CLING.but(bend=SOFA_CLING["bend"] + 0.04 * br, pel=(SOFA_CLING["pel"][0], SOFA_CLING["pel"][1] + 0.004 * br))
    if born > 0.0:
        figure(F, x0, y0, h, P, "child", 1, seed=3, grab={"f": (946, FLOOR - 132), "b": (972, FLOOR - 190)}, draw=born)
    phone(F, 690, FLOOR + 58, 1.15, 0.0, draw=F.seg(10.0, 10.6))
    # the weight: a mass with two lobes, and a stray run of the scribbling hand over the child
    g = F.seg(10.6, 13.0)
    if g > 0.0:
        gloom(F, 500, 340, 320, 120, seed=6, loops=22, halo=0.6, grow=g, a=min(1.0, g * 3))
        gloom(F, 730, 308, 440, 156, seed=4, loops=46, grow=g, a=min(1.0, g * 3),
              strands=((570, 504, 770, 562, 1),) if g >= 1.0 else ())
    title.draw(F, cx=900.0)        # 60 px left of centre: the title is 622 px wide and the curtain rail starts at x 1230


def class_set() -> dict:
    """The classroom from the back: every back is turned without anyone meaning it; one desk stands
    apart. The window is the room's window (it never leaves the picture)."""
    lone = Sketch([desk(390, FLOOR + 44, 1.5, 1300, C.CHALK_COOL, 1.0), chair(280, FLOOR + 48, 1.35, 1, 1310, C.CHALK_COOL, 0.95)], "lone")
    rows = Sketch([pupil(x_, FLOOR - 4, 0.80, 1400 + j * 20, C.CHALK_FAR, 0.95, f"b{j}") for j, x_ in enumerate((800, 985, 1170, 1355, 1540))]
                  + [pupil(x_, FLOOR + 96, 1.08, 1500 + j * 20, C.CHALK_DIM, 0.95, f"f{j}") for j, x_ in enumerate((760, 990, 1220, 1450, 1680))],
                  "rows")
    return dict(lone=lone, board=board(620.0, 176.0, 1230.0, 446.0), rows=rows, door=door(40, 236, 196, FLOOR))


# what travels where; every other line of the room is wiped off, every other line of the classroom draws on
ROOM_TO_CLASS = (("sofa", "lone"), ("pic.left", "board.frame"), ("pic.right", "board.ledge"), ("pic.fig0", "board.text0"),
                 ("pic.fig1", "board.text1"), ("pic.fig2", "board.text2"), ("lamp", "door"),
                 ("table.top", "rows.f4.chair"), ("table.leg_l", "rows.f4.leg_l"), ("table.leg_r", "rows.f4.leg_r"),
                 ("table.chair_l.seat", "rows.b4.chair"), ("table.chair_l.leg_b", "rows.b4.leg_l"),
                 ("table.chair_l.leg_f", "rows.b4.leg_r"))


def room_to_class(F: Frame, w: float):
    """One continuous transformation, no cut: w = 0 the room, 1 the classroom. The child, the weight
    and the window never leave the picture."""
    t = F.t
    R, K = room_set(), class_set()
    night_wall(F, FLOOR - 24)
    floorboards(F, FLOOR)
    l, tp, r, b = WIN
    day = ease(seg(w, 0.35, 0.95))
    _room_light(F, 1.0, day)
    window_night(F, l, tp, r, b, crows=3)
    if day > 0:
        window_day(F, l, tp, r, b, day)
    A_ = R["sofa"] + R["cushion"] + R["pic"] + R["far"] + R["rug"] + R["win"].sub("window.rail", "window.curtain")
    B_ = K["lone"] + K["board"] + K["rows"] + K["door"]
    morph(A_, B_, w, ROOM_TO_CLASS, seed=7).draw(F)
    R["win"].without("window.rail", "window.curtain").draw(F)
    # the child has got up and trudges on, in place, while the world re-draws itself around it
    cx, cy, ch = 520.0 + 40 * w, FLOOR + 104.0, 310.0
    P, _ = walk((t * 0.62) % 1.0, 0.0)
    ground_shadow(F, cx + 10, cy + 4, 120, 0.8)
    hd = figure(F, cx, cy, ch, P, "child", 1, seed=3)["head"]
    gloom(F, hd[0] - 40, hd[1] - 205, 300, 100, seed=4, loops=30, strands=((hd[0] - 170, hd[1] - 118, hd[0] + 20, hd[1] - 74, 1),))


def room_scene(F: Frame):
    if F.t < T_CHANGE[0]:
        room(F)
    else:
        w = F.seg(*T_CHANGE)
        room_to_class(F, ease(w) * 0.5 + w * 0.5)


# ==========================================================================
# the plain (first chorus, wide) and the pull-back
# ==========================================================================
HORIZON = 736.0
K_PLAIN = 300.0 / 78.0           # the plain is laid out in the wide framing's units; the world is K times that
CHILD_X = 770.0
T_PULL = (60.27, 62.27)
T_HITS = (64.77, 66.27, 67.77)


def plain(F: Frame, hits=3.0, friend=1.0, line=1.0):
    """key2, in the units of its wide framing (draw it inside F.place(0, 0, K_PLAIN)).
    hits: 0..3, how many of the three towering groups have drawn themselves on."""
    hy = HORIZON
    plain_ground(F, hy, a=line)
    far = mix(C.CHALK_FAR, C.CHALK_DIM, 0.45)
    near = mix(C.CHALK_FAR, C.CHALK_DIM, 0.85)
    tgt = (CHILD_X, hy - 90)
    # 1 the voices: balloons full of crossed-out lines, their tails aimed at the child
    v = voice(1085, 262, 250, 136, tgt, 830, C.CHALK_FAR, 0.95, 4.4, lines=5, name="v0") \
        + voice(650, 322, 200, 112, tgt, 810, far, 0.95, 4.4, lines=4, name="v1") \
        + voice(1500, 250, 150, 84, tgt, 850, C.CHALK_FAR, 0.8, 3.6, lines=3, name="v2")
    v.draw(F, d=seg(hits, 0.0, 1.0))
    # 3 the hurt: the house that came apart (far)
    house(1385, hy + 4, 400, 600, far, split=0.10, a=0.95, lw=4.6, fill=(0.17, 0.20, 0.32)).draw(F, d=seg(hits, 2.0, 3.0))
    # 2 the postures: turned backs, enormous, nearer
    bk = back_figure(476, hy + 6, 470, 720, far, 0.9, 4.4, tilt=0.2, name="b0") \
        + back_figure(292, hy + 14, 560, 740, near, 0.95, 5.0, lean=0.012, tilt=-0.15, name="b1") \
        + back_figure(96, hy + 26, 640, 700, near, 1.0, 5.4, tilt=0.1, name="b2")
    bk.draw(F, d=seg(hits, 1.0, 2.0))
    # they sink into the dark above; the weight grown to a sky
    wash(F, A((-40, -40), (1960, -40), (1960, 520), (-40, 520)), C.PAPER_DEEP, 0, 520, [0.85, 0.6, 0.25, 0.0], "soft")
    ceiling(F, 0.0, 1920.0, 92.0)
    # rain in front of everything, in screen space (its size does not follow the camera), down to the horizon
    sy = F.cam.to_screen(0.0, hy + 40)[1]
    with F.screen(), F.clip(rect=(0, 0, W, sy)):
        rain(F, 0, 0, W, H, n=210, slant=0.24, ln=44, col=C.CHALK_BLUE, a=0.42, w=2.2, seed=9)
    # the friend, far away: the one warm sign
    if friend > 0:
        fx, fy = 1752.0, hy - 4
        glow(F, fx, fy - 30, 300, 210, a=0.26 * friend, power=1.8)
        glow(F, fx, fy - 30, 100, 86, a=0.42 * friend, power=1.4)
        smudge(F, fx - 40, fy + 22, 260, 18, C.AMBER, 0.30 * friend, "mid", additive=True)
        figure(F, fx, fy, 60, F_CALL.but(sway=0.5), "friend", -1, seed=5, a=friend)
    # the child, small, at the end of its own long trail
    cx, cy = CHILD_X, hy + 4
    footprints(F, 40, cx - 34, cy + 16, 20, 0.95, C.CHALK_DIM, 1.5)
    smudge(F, cx, cy - 26, 230, 120, C.MOON, 0.16, "soft", additive=True)
    ground_shadow(F, cx + 8, cy + 2, 62, 0.8)
    return figure(F, cx, cy, 78, STOPPED, "child", 1, seed=3)


def plain_cam(t: float) -> Cam:
    """Close on the child (300 px tall, zoom 1), then the pull-back to the wide framing (78 px, zoom 0.26)."""
    k = K_PLAIN
    close = Cam.at(CHILD_X * k, (HORIZON + 4) * k, 1.0, 900.0, 790.0)
    wide = Cam(960.0 * k, 540.0 * k, 1.0 / k)
    return Cam.ease(close, wide, seg(t, *T_PULL))


def plain_scene(F: Frame):
    t = F.t
    F.cam = plain_cam(t)
    hits = sum(seg(t, th, th + 0.45) for th in T_HITS)
    with F.place(0.0, 0.0, K_PLAIN):
        plain(F, hits, friend=F.ramp(70.7, 71.5), line=1.0)


# ==========================================================================
# the field (third chorus, the colour moment, the outro)
# ==========================================================================
HILL_FAR = spline(A((-60, 640), (220, 566), (520, 528), (840, 570), (1140, 640)), 40)
HILL_MID = spline(A((-60, 716), (420, 700), (760, 664), (1040, 612), (1330, 560), (1620, 548), (1980, 610)), 50)
HILL_NEAR = spline(A((-60, 742), (300, 716), (700, 704), (980, 706), (1400, 722), (1980, 700)), 60)
PAIR_X, PAIR_H = 970.0, 276.0
T_RING = 217.84


def ground_y(x):
    return float(np.interp(x, HILL_NEAR[:, 0], HILL_NEAR[:, 1]))


RING_AT = (PAIR_X, ground_y(PAIR_X - 72) + 5 - PAIR_H * 0.55)          # between the two: where the ring opens


def field(F: Frame, tear=1.0):
    """key3 / the two halves of key4: the same hill in two skins (F.skin): night chalk after the sky
    is torn, and full crayon colour."""
    t, day = F.tq, F.day
    joy = 1.0 if day else 0.6
    pen = F.pick(C.CHALK_DIM, C.PENCIL)
    if day:
        sky(F)
        sun(F, 1640.0, 176.0, 88.0)
        for j, (cx_, cy_, cs) in enumerate(((420, 150, 1.0), (1030, 96, 0.8), (760, 250, 0.6))):
            cloud(F, cx_ + 14 * math.sin(t * 0.25 + j), cy_, cs, 630 + j)
    else:
        # what is left of the storm, pushed to the sides
        gloom(F, 300, 96, 470, 130, seed=21, loops=30, w=1.1, halo=0.7, edge=0.0, a=0.9)
        gloom(F, 1880, 330, 240, 120, seed=22, loops=14, w=1.0, halo=0.6, edge=0.0, a=0.8)
        if tear > 0:
            tear_light(F, tear)
    # hills, far to near
    hill(F, HILL_FAR, seed=641, ang=0.5, c1=C.LIME, c2=C.GREEN, night=(0.20, 0.25, 0.39))
    hill(F, HILL_MID, seed=651, ang=-0.6, night=(0.18, 0.23, 0.36))
    # the house on the hill, whole again and showing its mend; the crows are still there: only birds now
    hx_, hy_ = 1500.0, float(np.interp(1500, HILL_MID[:, 0], HILL_MID[:, 1])) + 6
    house(hx_, hy_, 150, 600, pen, split=0.0, a=0.95, lw=3.6, fill=F.pick((0.20, 0.25, 0.38), (1.0, 0.86, 0.60)),
          roof=F.pick((0.25, 0.29, 0.44), C.RED)).draw(F)
    tape = A((hx_ - 13, hy_ - 86), (hx_ + 13, hy_ - 92), (hx_ + 15, hy_ - 76), (hx_ - 11, hy_ - 70), (hx_ - 13, hy_ - 86))
    fill(F, tape, F.pick(C.AMBER, C.AMBER_PALE), 0.95, "dense")
    chalk(F, tape, C.AMBER_DEEP, 2.0, 0.9, 681, wob=0.3, edge=0.0)
    for j, (dx, dy) in enumerate(((-40, -131), (10, -180), (50, -140))):
        crow(F, hx_ + dx, hy_ + dy, 0.5, 520 + j, face=-1 if j != 2 else 1)
    hill(F, HILL_NEAR, seed=661, ang=0.9, front=True, night=(0.16, 0.21, 0.33))
    tree(F, 250.0, ground_y(250.0) + 4)
    # flowers and grass on the near hill
    if day:
        grass(F, -20, 1940, 760, 150, C.GREEN_DEEP, 5, 10, 30, 2.6, 0.8, yj=40)
        grass(F, -20, 1940, 900, 150, C.GREEN_DEEP, 6, 16, 44, 3.2, 0.8, yj=90)
        grass(F, -20, 1940, 880, 90, C.LIME, 7, 14, 40, 3.0, 0.8, yj=100)
    else:
        grass(F, -20, 1940, 760, 130, C.CHALK_FAR, 5, 10, 30, 2.4, 0.7, yj=40)
        grass(F, -20, 1940, 900, 130, C.CHALK_FAR, 6, 16, 44, 2.8, 0.7, yj=90)
    i = np.arange(46)
    fx = 40 + htab(i, 7, 901) * (1920 - 80)
    fd = htab(i, 11, 903) ** 1.3
    cols = (C.RED, C.PINK, C.ORANGE, C.PURPLE, C.SUN, C.PINK, C.RED)
    for j in np.argsort(fd):
        x_ = float(fx[j])
        if abs(x_ - PAIR_X) < 150 and fd[j] < 0.25:
            continue
        y_, hh, sw = ground_y(x_) + 12 + fd[j] * 150, 30 + 44 * fd[j], 0.25 * math.sin(t * 1.6 + j * 1.3)
        if day:
            flower(F, x_, y_, hh, cols[j % len(cols)], seed=950 + int(j), sway=sw)
        else:
            bud(F, x_, y_, hh, seed=950 + int(j), sway=sw)
    # the two, hand in hand
    h = PAIR_H
    cx_, fx_ = PAIR_X - 72, PAIR_X + 72
    cy_, fy_ = ground_y(cx_) + 5, ground_y(fx_) + 5
    bob = 0.012 * math.sin(F.t * 2 * math.pi / 1.5)
    hold = (PAIR_X, cy_ - h * (0.46 + bob))
    if not day:
        glow(F, fx_, fy_ - 130, 300, 280, a=0.20)
    ground_shadow(F, cx_ + 10, cy_ + 2, 64, 0.6)
    ground_shadow(F, fx_ - 10, fy_ + 2, 64, 0.6)
    Pc = HOLD.but(joy=joy, mouth=0.4 + 0.5 * joy, hb=(-0.10, -0.17), eb=1.0, pel=(0.0, 0.402 + bob), eye=1.0)
    Pf = HOLD.but(joy=joy, mouth=0.9, mopen=0.6 * joy, hb=(-0.14, 0.02), eb=1.0, sway=0.3, pel=(0.0, 0.402 - bob))
    J = figure(F, cx_, cy_, h, Pc, "child", 1, seed=3, grab={"f": hold})
    on_string(F, cx_ - 200, cy_ - h - 120 + 8 * math.sin(t * 0.9), J["ha_b"])       # the weight: small, carried
    figure(F, fx_, fy_, h * 1.02, Pf, "friend", -1, seed=5, grab={"f": hold})


def field_scene(F: Frame):
    """213-217.84 night; then the ring opens from between the two (key4 at 219.0) and reaches past the
    frame in five seconds; from then on only the day render is paid for (key3 at 232)."""
    t = F.t
    R = 1250.0 * ease_out(seg(t, T_RING, T_RING + 5.0), 1.6) + 20.0 if t >= T_RING else 0.0
    ring(F, field, RING_AT[0], RING_AT[1], R, turn=t - T_RING)


# ==========================================================================
# proof images (hx/_review/v4_core)
# ==========================================================================
STILLS = (("still_room_14.0.png", 14.0), ("still_plain_72.0.png", 72.0), ("still_ring_219.0.png", 219.0),
          ("still_field_232.0.png", 232.0))
CLIPS = (("clip_room_13-23.mp4", 13.0, 23.0), ("clip_plain_70-80.mp4", 70.0, 80.0))


def _renderer():
    from ..frame import Renderer
    return Renderer(1.0)


def _save(arr, name):
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.ascontiguousarray(arr[..., :3])).save(OUT / name)
    print("wrote", OUT / name)


def _strip(times, name, cols=2, cw=960, ch=540):
    from PIL import Image
    r = _renderer()
    rows = (len(times) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * ch), (12, 14, 22))
    for i, t in enumerate(times):
        sheet.paste(Image.fromarray(r.render(t)[..., :3]).resize((cw, ch), Image.LANCZOS), ((i % cols) * cw, (i // cols) * ch))
    OUT.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT / name)
    print("wrote", OUT / name)


def stills():
    r = _renderer()
    for name, t in STILLS:
        _save(r.render(t), name)


def pullback():
    """Eight frames across the two seconds of the pull-back, and the first and last at full size."""
    _strip([T_PULL[0] + (T_PULL[1] - T_PULL[0]) * i / 7.0 for i in range(8)], "strip_pullback.png")
    r = _renderer()
    _save(r.render(T_PULL[0]), "pullback_close.png")
    _save(r.render(T_PULL[1]), "pullback_wide.png")


def change():
    """Eight frames across the room-to-classroom change."""
    _strip([T_CHANGE[0] + (T_CHANGE[1] - T_CHANGE[0]) * i / 7.0 for i in range(8)], "strip_room_to_class.png")


def crops():
    """The room still against the prototype's key1_room.png: three crops at 100 percent, new left."""
    from PIL import Image
    new = Image.open(OUT / STILLS[0][0]).convert("RGB")
    old = Image.open(PROTO / "out" / "key1_room.png").convert("RGB")
    boxes = ((560, 400, 1040, 720), (1240, 150, 1720, 470), (200, 180, 680, 500), (900, 700, 1380, 1020))
    sheet = Image.new("RGB", (480 * 2 + 12, 320 * len(boxes) + 4 * (len(boxes) - 1)), (0, 0, 0))
    for i, bx in enumerate(boxes):
        sheet.paste(new.crop(bx), (0, i * 324))
        sheet.paste(old.crop(bx), (492, i * 324))
    sheet.save(OUT / "crops_room_new_left_proto_right.png")
    print("wrote", OUT / "crops_room_new_left_proto_right.png")


def cost():
    """Frame cost at 1080p on one core: median over consecutive frames, draw + finish (no encode)."""
    r = _renderer()
    lines = []
    for name, t0 in (("room", 14.0), ("room_to_class", 34.5), ("plain close", 59.5), ("plain pull-back", 61.0), ("plain wide", 72.0),
                     ("ring (two renders)", 219.0), ("field day", 232.0)):
        r.render(t0)
        ts = []
        for i in range(12):
            a = time.perf_counter()
            r.render(t0 + (i + 1) / 30.0)
            ts.append(time.perf_counter() - a)
        lines.append(f"{name:20s} {np.median(ts) * 1000:6.0f} ms  (max {max(ts) * 1000:.0f})")
        print(lines[-1])
    return lines


def clips():
    """The two 10 s clips through hx.render at the final settings (1920x1080, 30 fps, no lyric line)."""
    from ..render import render
    OUT.mkdir(parents=True, exist_ok=True)
    for name, t0, t1 in CLIPS:
        print(render(OUT / name, t0, t1))


def _proto_frame(job):
    """One finished frame of the PROTOTYPE (hx/_tmp/proto_chalk, imported read-only), as bytes."""
    name, n = job
    if str(PROTO) not in sys.path:
        sys.path.insert(0, str(PROTO))
        sys.dont_write_bytecode = True                   # leave the prototype's folder as it is
    import proto
    t = (n + 0.5) / 30.0
    F = proto.Frame(t)
    (proto.scene_room if name == "room" else proto.scene_plain)(F, t)
    return F.finish().tobytes()


def before():
    """The prototype's flicker, measured the same way: 10 s of its room and of its plain, as rendered
    and through the same encoder (before_proto_*.mp4)."""
    import multiprocessing as mp
    import subprocess
    from mv.render import FFMPEG, encoder_args
    from .. import motion
    OUT.mkdir(parents=True, exist_ok=True)
    lines = []
    for (_clip, t0, t1), name in zip(CLIPS, ("room", "plain")):
        path = OUT / f"before_proto_{name}.mp4"
        proc = subprocess.Popen([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
                                 "-s", f"{W}x{H}", "-r", "30", "-i", "-", "-an", *encoder_args(False, 30), str(path)],
                                stdin=subprocess.PIPE)
        d, prev = [], None
        with mp.get_context("spawn").Pool(8) as pool:
            for buf in pool.imap(_proto_frame, [(name, n) for n in range(int(t0 * 30), int(t1 * 30))], chunksize=4):
                proc.stdin.write(buf)
                y = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 4)[..., :3].astype(np.float32) @ motion.LUMA
                if prev is not None:
                    d.append(motion._diff(prev, y))
                prev = y
        proc.stdin.close()
        proc.wait()
        lines.append(motion.report(f"prototype {name}, as rendered", np.asarray(d)))
        lines.append(motion.report(path))
    (OUT / "flicker_before.txt").write_text("\n".join(lines) + "\n")
    return lines


def flicker():
    """flicker.txt: the numbers before (the prototype) and after (the kit), as rendered and as encoded."""
    from .. import motion
    after = []
    for name, t0, t1 in CLIPS:
        after.append(motion.report(f"kit {name[5:-4]}, as rendered", motion.measure_render(t0, t1)))
        after.append(motion.report(OUT / name))
    b = OUT / "flicker_before.txt"
    text = ("Flicker with a static camera: mean absolute luma difference between consecutive frames (levels, 0..255) and the\n"
            "share of pixels moving by more than 8 levels, at 1920x1080, 30 fps (python -m hx.motion). The picture boils on twos:\n"
            "'boil step' is the change between two pairs of frames, 'inside pair' between the two frames of a pair.\n"
            "Targets: boil step under 1.2 levels and under 6 percent; inside a pair essentially zero; a 10 s clip under 25 MB.\n\n"
            "BEFORE (the prototype hx/_tmp/proto_chalk: tooth and grain re-seated on every boil step)\n"
            + (b.read_text() if b.exists() else "   not measured: run `python -m hx.chalk.demo before`\n")
            + "\nAFTER (hx.chalk: tooth fixed to the screen, only stroke geometry boils, large zigzags seated)\n"
            + "\n".join(after) + "\n")
    (OUT / "flicker.txt").write_text(text)
    print("wrote", OUT / "flicker.txt")


def consecutive():
    """Three consecutive DECODED frames of each clip, cropped at 100 percent, side by side (the first two
    are a pair; the third is the next boil step), and under each step its difference, eight times amplified."""
    import subprocess
    from PIL import Image
    from mv.render import FFMPEG
    for (name, _t0, _t1), box in zip(CLIPS, ((560, 300, 1040, 660), (560, 500, 1040, 860))):
        raw = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-ss", "4.0", "-i", str(OUT / name), "-frames:v", "3",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        fr = np.frombuffer(raw, dtype=np.uint8).reshape(3, H, W, 3)[:, box[1]:box[3], box[0]:box[2]].astype(np.int16)
        w, h = box[2] - box[0], box[3] - box[1]
        sheet = Image.new("RGB", (3 * w + 8, 2 * h + 4), (0, 0, 0))
        for i in range(3):
            sheet.paste(Image.fromarray(fr[i].astype(np.uint8)), (i * (w + 4), 0))
            if i:
                sheet.paste(Image.fromarray(np.clip(np.abs(fr[i] - fr[i - 1]) * 8, 0, 255).astype(np.uint8)), (i * (w + 4), h + 4))
        out = OUT / f"consecutive_{name[5:-4]}.png"
        sheet.save(out)
        print("wrote", out)


def main(argv):
    todo = argv or ["stills", "pullback", "change", "crops", "cost", "clips", "consecutive", "before", "flicker"]
    for name in todo:
        globals()[name]()


if __name__ == "__main__":
    main(sys.argv[1:])
