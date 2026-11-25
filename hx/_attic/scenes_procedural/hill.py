"""Hill world: the bridge, the breakdown, the long silence, the last chorus and the outro.

One afternoon on one gentle grass hill above a sea of fog, seen through one virtual camera
(see _hill_set.Cam). Sections are addressed by LRC index and time only.
"""
from __future__ import annotations

from . import _hill_br as BR
from . import _hill_late as LATE

SECTIONS = ("br_a", "br_b", "br_c", "bd", "hush2", "c3a", "c3b", "out")
CROSSFADE = {"br_a": 0.4}

_DRAW = {"br_a": BR.br_a, "br_b": BR.br_b, "br_c": BR.br_c, "bd": LATE.take, "hush2": LATE.take,
         "c3a": LATE.take, "c3b": LATE.c3b, "out": LATE.out}


def draw(ctx):
    _DRAW[ctx.sec.id](ctx)
