"""The film as a list of shots on the recording's clock.

A shot shows one picture from hx/art/ (painted by `python -m hx.concept`), moved by a slow camera
and dressed with drawn weather and light (hx/scenes/film.py). A shot lasts until the next one
begins. Times are seconds of the recording: section starts, bar lines, beats, line stamps and
measured attacks from hx/data/timeline.json. The story each shot tells is in hx/DESIGN.md.

Camera: `z` = (zoom at the start, zoom at the end), 1 = the whole picture; `at` = (x0, y0, x1, y1),
the view centre's offset from the picture's centre at start and end, as a share of the picture
(positive x looks right, positive y looks down; clamped so the view stays inside the picture);
`ease` "lin" drifts at constant speed, "out" starts fast and settles, "io" eases both ends;
`move` = seconds the move takes (default: the whole shot).
`fade` = seconds of dissolve from the previous shot (0 = cut). `flip` mirrors the picture (the child
stays on the left of the friend from her first appearance to the end).
`fx` = drawn layers, each a tuple whose first item names it:
  ("rain", amount[, slant])   ("litrain", amount)      ("wind", strength)     ("mist", density)
  ("pollen", n)               ("pulse", amount)        beat pulse of the exposure
  ("flash", strength)         a burst of light on the cut, decaying
  ("tv", amount)              cold flicker of a television off-screen
  ("dark", e0, e1)            exposure from e0 to e1 over the shot
  ("to", colour, t0, t1, amount)   mix toward a colour between two absolute times
  ("hits", strength)          a small burst on each measured attack of the breakdown
  ("ring", t0, t1, cx, cy)    the picture is cold and colourless outside a ring that opens from
                              (cx, cy) (shares of the frame) between two absolute times
  ("grade", sat, cool)        the picture keeps only `sat` of its colour and takes a cold cast
                              (colour comes last in this film: before LRC line 62 nothing is fully
                              saturated)
  ("rainbox", amount, (l, t, r, b))   rain seen through a window: only inside that part of the picture
  ("title",)                  title and credits
  ("alt", picture, mode[, arg[, box]])   a second pose of the same picture (the picture repainted
                              with one thing changed), laid over it while the mode says so:
                              "walk" = on every off-beat (arg = beats per stride, default 1),
                              "blink" = a blink now and then, "hold" = between arg = (t0, t1),
                              "rest" = always, except just after each attack of the breakdown,
                              "loop" = half of every arg seconds (a wingbeat);
                              box = (l, t, r, b) limits the change to a part of the picture
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass

INK = (0.055, 0.075, 0.125)
MIST = (0.80, 0.84, 0.90)
PAPER = (0.914, 0.851, 0.737)
PALE = (0.30, 0.70)             # grade outside the ring of colour: (share of colour kept, cold cast)
WIN_INTRO = (0.635, 0.31, 0.85, 0.62)
WIN_CROWS = (0.30, 0.07, 0.74, 0.49)


@dataclass(frozen=True)
class Shot:
    t0: float
    art: str
    z: tuple = (1.0, 1.05)
    at: tuple = (0.0, 0.0, 0.0, 0.0)
    ease: str = "lin"
    move: float | None = None
    fade: float = 0.0
    fx: tuple = ()
    flip: bool = False


S = Shot
RAIN, STORM = ("rain", 0.55), ("rain", 1.0, -0.32)

SHOTS: tuple = (
    # --- intro, verse 1: the room at night ---
    S(0.0, "intro", (1.0, 1.10), (0.0, 0.0, -0.035, 0.03),
      fx=(("title",), ("to", INK, 1.6, 0.0, 1.0), ("rainbox", 0.5, WIN_INTRO))),
    S(12.265, "v1a_plain", (1.0, 1.04), (0.0, 0.0, -0.01, 0.0), fx=(("tv", 1.0),)),
    S(16.2, "v1a", (1.04, 1.09), (-0.01, 0.0, 0.01, -0.01), fade=1.1,
      fx=(("tv", 1.0), ("alt", "v1a_k", "hold", (17.5, 20.7)))),
    S(21.5, "v1a_plain", (1.09, 1.12), (0.01, -0.01, -0.01, 0.0), fade=1.1, fx=(("tv", 0.7),)),
    S(24.265, "v1b_crows_a", (1.0, 1.04), (0.0, 0.0, 0.0, -0.015), fx=(("rainbox", 0.6, WIN_CROWS),)),
    S(27.265, "v1b_crows", (1.04, 1.09), (0.0, -0.015, 0.0, -0.035), fade=1.6, fx=(("rainbox", 0.6, WIN_CROWS),)),
    S(30.265, "v1b_door", (1.07, 1.035), (0.0, 0.02, 0.0, 0.005)),
    S(33.265, "v1b_door_b", (1.035, 1.0), (0.0, 0.005, 0.0, -0.01), fade=1.5),
    # --- pre-chorus 1: wherever I am; the home that came apart ---
    S(36.265, "p1a_class", (1.05, 1.05), (-0.02, 0.0, 0.02, 0.0)),
    S(39.265, "p1a_street", (1.0, 1.06), (0.0, 0.0, 0.0, 0.01),
      fx=(RAIN, ("alt", "p1a_street_b", "walk", 2), ("alt", "p1a_street_k", "blink"))),
    S(42.265, "p1a_lamp", (1.08, 1.04), (0.0, -0.02, 0.0, -0.01), fx=(RAIN, ("alt", "p1a_lamp_k", "blink"))),
    S(45.265, "p1a_walk", (1.06, 1.06), (-0.03, 0.0, 0.03, 0.0), fx=(RAIN, ("alt", "p1a_walk_b", "walk", 2))),
    S(48.265, "p1b_table", (1.10, 1.0), (0.0, -0.02, 0.0, 0.0), fx=(("mist", 0.5), ("alt", "p1b_table_b", "walk", 2))),
    S(52.36, "p1b_pieces", (1.0, 1.06), (0.0, 0.0, 0.01, -0.02), fx=(("mist", 0.4),)),
    S(54.64, "p1b_sink", (1.04, 1.08), (0.0, 0.0, 0.0, 0.02), fade=0.5, fx=(("to", INK, 54.9, 55.95, 0.9),)),
    # --- silence, chorus 1: the plain ---
    S(56.0, "c1a_before", (1.12, 1.14), fx=(("dark", 0.42, 0.42),)),
    S(58.6, "c1a_before", (1.14, 1.10), fx=(("dark", 0.55, 1.0),)),
    S(59.515, "c1a_mid", (1.06, 1.02), fx=(RAIN, ("alt", "c1a_mid_b", "walk", 1))),
    S(60.265, "c1a_wide", (1.55, 1.0), (0.0, 0.06, 0.0, 0.0), "out", 3.6,
      fx=(RAIN, ("wind", 0.8), ("mist", 0.6), ("pulse", 0.05), ("flash", 0.10))),
    S(64.765, "c1a_whispers", (1.0, 1.07), ease="out", fx=(RAIN, ("wind", 0.6), ("pulse", 0.06))),
    S(66.265, "c1a_backs", (1.0, 1.07), ease="out", fx=(RAIN, ("wind", 0.6), ("pulse", 0.06))),
    S(67.765, "c1a_doors", (1.0, 1.09), ease="out", fx=(RAIN, ("wind", 0.6), ("pulse", 0.06))),
    S(70.7, "c1a_mid", (1.10, 1.06), (0.0, -0.01, 0.0, 0.0), fx=(RAIN,)),
    S(72.265, "c1b_ribbon", (1.10, 1.0), (-0.04, 0.0, 0.0, 0.0), "out", fx=(("rain", 0.35), ("mist", 0.4))),
    S(75.52, "c1b_mote", (1.0, 1.05), (0.0, 0.0, -0.01, 0.0), fx=(("rain", 0.2), ("alt", "c1b_mote_k", "blink"))),
    S(78.5, "c1b_calm", (1.07, 1.0), fade=0.9, fx=(("rain", 0.12), ("mist", 0.4))),
    # --- interlude, verse 2 ---
    S(80.5, "inter", (1.05, 1.0), fade=1.2),
    S(86.5, "inter_sill", (1.0, 1.05), (0.0, 0.01, 0.0, -0.01), fade=1.0),
    S(91.0, "inter_phone", (1.0, 1.02), fx=(("flash", 0.12),)),
    S(91.765, "v2a_phone", (1.0, 1.07), (0.0, 0.0, 0.02, 0.02), fx=(("pulse", 0.03), ("pollen", 16))),
    S(96.265, "v2a_windows_a", (1.08, 1.055), (0.02, -0.02, 0.014, -0.014), fx=(("pulse", 0.03),)),
    S(98.515, "v2a_windows", (1.055, 1.0), (0.014, -0.014, 0.0, 0.0), fade=2.6, fx=(("pulse", 0.03),)),
    S(103.765, "v2b_path", (1.06, 1.06), (-0.025, 0.0, 0.025, 0.0),
      fx=(("pulse", 0.04), ("alt", "v2b_path_b", "walk", 1))),
    S(108.265, "v2b_ring", (1.0, 1.05), (0.0, 0.0, 0.01, -0.01), fx=(("pulse", 0.03),)),
    S(111.265, "v2b_whisper", (1.0, 1.06), (0.0, 0.0, 0.015, 0.0), fx=(("pulse", 0.03),)),
    # --- pre-chorus 2 ---
    S(115.765, "p2a_lunch", (1.07, 1.07), (-0.03, 0.0, 0.03, 0.0)),
    S(118.765, "p2a_houses", (1.07, 1.07), (-0.03, 0.0, 0.03, 0.0),
      fx=(("rain", 0.4), ("alt", "p2a_houses_b", "walk", 1))),
    S(121.765, "p2a_lamp", (1.07, 1.07), (-0.03, 0.0, 0.03, 0.0), fx=(("rain", 0.4), ("alt", "p2a_lamp_b", "walk", 1))),
    S(124.765, "p2a_reach", (1.0, 1.10), (0.0, 0.0, 0.03, -0.04), fx=(("rain", 0.4),)),
    S(127.765, "p2b_swirl", (1.0, 1.06), fx=(("wind", 0.5), ("pulse", 0.04))),
    S(131.69, "p2b_armful", (1.0, 1.05), fx=(("wind", 0.7), ("pulse", 0.05), ("alt", "p2b_armful_k", "blink"))),
    S(134.18, "p2b_armful", (1.05, 1.30), (0.0, 0.0, 0.0, -0.03), "io",
      fx=(("wind", 1.0), ("pulse", 0.06), ("to", MIST, 136.9, 138.2, 0.96))),
    # --- chorus 2: the storm ---
    S(138.2, "c2a_lean", (1.0, 1.07), fade=0.5,
      fx=(STORM, ("wind", 1.0), ("pulse", 0.07), ("alt", "c2a_lean_b", "walk", 1), ("to", MIST, 138.75, 138.2, 0.96))),
    S(141.265, "c1a_wide", (1.28, 1.12), (0.0, 0.05, 0.0, 0.02), "out",
      fx=(STORM, ("wind", 1.0), ("mist", 0.7), ("pulse", 0.07), ("dark", 0.85, 0.85))),
    S(144.265, "c1a_whispers", (1.24, 1.34), (0.0, -0.02, 0.0, -0.02), "out",
      fx=(STORM, ("wind", 1.0), ("pulse", 0.08), ("dark", 0.85, 0.85))),
    S(145.765, "c1a_backs", (1.24, 1.34), (0.0, -0.03, 0.0, -0.03), "out",
      fx=(STORM, ("wind", 1.0), ("pulse", 0.08), ("dark", 0.85, 0.85))),
    S(147.265, "c1a_doors", (1.22, 1.32), (0.0, 0.0, 0.0, 0.0), "out",
      fx=(STORM, ("wind", 1.0), ("pulse", 0.08), ("dark", 0.85, 0.85))),
    S(148.765, "c2a_storm", (1.0, 1.06), fx=(STORM, ("wind", 1.0), ("pulse", 0.08), ("alt", "c2a_storm_b", "walk", 1))),
    S(150.1, "c2a_lean", (1.10, 1.14), (0.0, -0.01, 0.0, -0.01),
      fx=(STORM, ("wind", 0.9), ("alt", "c2a_lean_b", "walk", 1))),
    S(151.765, "c2b_beside", (1.0, 1.06), fx=(("rain", 0.7), ("wind", 0.5), ("pulse", 0.05)), flip=True),
    S(154.84, "c2b_up", (1.10, 1.10), (0.0, 0.045, 0.0, -0.045), "io", fx=(("rain", 0.5),), flip=True),
    # --- bridge: the hill ---
    S(158.86, "br_a_birds", (1.0, 1.07), (0.0, 0.0, 0.02, -0.02), fade=0.4,
      fx=(("wind", 0.8), ("pulse", 0.04), ("alt", "br_a_birds_f", "loop", 0.4, (0.3, 0.0, 1.0, 0.62))), flip=True),
    S(164.515, "br_a_sky", (1.0, 1.08), (0.0, 0.02, 0.0, -0.02),
      fx=(("wind", 0.6), ("pulse", 0.04), ("alt", "br_a_sky_f", "loop", 0.4)), flip=True),
    S(167.515, "br_a_keep", (1.0, 1.05), fx=(("wind", 0.5), ("pulse", 0.04), ("alt", "br_a_keep_k", "blink")),
      flip=True),
    S(170.765, "br_b_rain", (1.0, 1.06), fx=(("litrain", 0.8), ("pulse", 0.04), ("grade", 0.62, 0.12))),
    S(174.515, "br_b_face", (1.0, 1.06), (0.0, 0.01, 0.0, -0.01),
      fx=(("litrain", 0.6), ("pulse", 0.03), ("grade", 0.62, 0.12))),
    S(178.265, "br_c_offer", (1.0, 1.03), fx=(("litrain", 0.3), ("alt", "br_c_offer_k", "blink"), ("grade", 0.66, 0.10))),
    S(180.265, "br_c_hands", (1.03, 1.09), (0.0, 0.0, 0.0, 0.01), "out",
      fx=(("litrain", 0.3), ("flash", 0.18), ("alt", "br_c_hands_k", "blink"), ("grade", 0.66, 0.10))),
    # --- breakdown, silence ---
    S(182.3, "bd_haze", (1.0, 1.03)),
    S(184.34, "bd_push1", (1.0, 1.05), fx=(("hits", 0.06), ("alt", "bd_push1_b", "rest"))),
    S(188.9, "bd_push", (1.0, 1.05), fx=(("hits", 0.06), ("alt", "bd_push_b", "rest"))),
    S(191.9, "bd_step", (1.0, 1.04), fx=(("flash", 0.35),)),
    S(193.0, "hush2_shafts", (1.0, 1.07), fade=0.8, fx=(("pollen", 50), ("to", INK, 200.45, 201.25, 0.22))),
    # --- chorus 3: the sky opens, colour ---
    S(201.25, "c3a_tear_s", (1.30, 1.0), (0.03, -0.04, 0.0, 0.0), "out", 2.6,
      fx=(("flash", 0.8), ("pulse", 0.035), ("grade", 0.60, 0.22), ("alt", "c3a_tear_s_b", "walk", 1),
          ("alt", "c3a_tear_s_f", "loop", 0.36, (0.0, 0.0, 1.0, 0.56)))),
    S(204.265, "c3a_walk", (1.05, 1.05), (-0.02, 0.0, 0.02, 0.0),
      fx=(("pulse", 0.035), ("pollen", 30), ("alt", "c3a_walk_b", "walk", 1), ("grade", 0.58, 0.22),
          ("alt", "c3a_walk_f", "loop", 0.36, (0.0, 0.0, 1.0, 0.47)))),
    S(207.265, "c3a_cutouts", (1.08, 1.08), (-0.035, 0.0, 0.035, 0.0),
      fx=(("pulse", 0.035), ("alt", "c3a_cutouts_b", "walk", 1), ("grade", 0.50, 0.30))),
    S(210.265, "c3a_fallen", (1.0, 1.05),
      fx=(("pulse", 0.03), ("alt", "c3a_fallen_b", "walk", 1), ("grade", 0.50, 0.30))),
    S(213.1, "c3b_smile", (1.0, 1.07), (0.0, 0.0, -0.01, -0.01),
      fx=(("pulse", 0.025), ("pollen", 30), ("alt", "c3b_smile_k", "blink"), ("grade", 0.62, 0.35)), flip=True),
    S(217.84, "c3b_full", (1.14, 1.0), ease="out", move=7.0,
      fx=(("ring", 217.84, 220.6, 0.5, 0.56), ("pulse", 0.025), ("pollen", 40))),
    S(223.515, "c3b_sky", (1.08, 1.08), (0.0, 0.035, 0.0, -0.035), fade=0.8,
      fx=(("pulse", 0.02), ("alt", "c3b_sky_f", "loop", 0.4, (0.0, 0.0, 1.0, 0.85)))),
    # --- outro, coda ---
    S(226.765, "out_ridge", (1.08, 1.08), (-0.035, 0.0, 0.035, 0.0),
      fx=(("pulse", 0.025), ("pollen", 40), ("alt", "out_ridge_b", "walk", 1))),
    S(232.765, "out_kite", (1.0, 1.05), (0.0, 0.0, 0.0, -0.012),
      fx=(("pulse", 0.025), ("pollen", 30), ("alt", "out_kite_b", "walk", 1))),
    S(235.765, "out_cloud", (1.0, 1.05), (0.0, 0.01, 0.0, -0.01),
      fx=(("pulse", 0.02), ("pollen", 30), ("alt", "out_cloud_k", "blink"))),
    S(238.765, "out_gold", (1.0, 1.07), fade=1.0, fx=(("pulse", 0.02), ("pollen", 30), ("alt", "out_gold_b", "walk", 1))),
    S(244.5, "coda_sofa", (1.0, 1.05), fade=1.5),
    S(250.74, "coda_ring", (1.0, 1.04)),
    S(252.6, "coda_call", (1.0, 1.07), (0.0, 0.0, 0.01, 0.0),
      fx=(("to", PAPER, 254.5, 258.6, 0.92), ("alt", "coda_call_k", "blink"))),
)

_T0 = [s.t0 for s in SHOTS]
END = 258.87


def index_at(t: float) -> int:
    return max(0, bisect_right(_T0, t) - 1)


def span(i: int) -> tuple:
    """(start, end) of shot i."""
    return SHOTS[i].t0, (SHOTS[i + 1].t0 if i + 1 < len(SHOTS) else END)
