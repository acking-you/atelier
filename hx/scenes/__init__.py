"""Scene registry: scene modules are registered by TIME SPAN on the song's clock.

A scene module in this package defines

    SPAN = (t0, t1)            # seconds of the recording it draws: t0 <= t < t1  (or SPANS = ((a, b), ...))
    def draw(F): ...           # F is the hx.chalk Frame (see hx/chalk/README.md)

and the registry picks the module whose span holds F.t. Spans of different modules may not overlap
(an overlap is an error at load). Modules named demo_* are stand-ins: they may be overlapped, and a
real scene wins over them. A time nobody draws gets the placeholder (night paper, one chalk ground
line, the child standing at mid size), so stills and renders never fail. A module that fails to
import is skipped with a message on stderr, or stops everything when HX_STRICT=1 (hx.render sets it).
Modules whose names start with an underscore are helpers and are not registered.
"""
from __future__ import annotations

import importlib
import os
import pkgutil
import sys
import traceback

_SPANS: list = []                # (t0, t1, draw, module name, is a demo)
_LOADED = False


def _load() -> None:
    global _LOADED
    if _LOADED:
        return
    found = []
    for m in pkgutil.iter_modules(__path__):
        if m.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"{__name__}.{m.name}")
        except Exception:
            # a still may be asked for while another author's module is mid-edit; a render never tolerates it
            if os.environ.get("HX_STRICT"):
                raise
            print(f"[scenes] {m.name} failed to import and is skipped:\n{traceback.format_exc(limit=2)}", file=sys.stderr)
            continue
        spans = getattr(mod, "SPANS", None) or ([mod.SPAN] if hasattr(mod, "SPAN") else [])
        for t0, t1 in spans:
            if not t1 > t0:
                raise RuntimeError(f"scene {m.name}: empty span ({t0}, {t1})")
            found.append((float(t0), float(t1), mod.draw, m.name, m.name.startswith("demo_")))
    found.sort(key=lambda s: (s[4], s[0]))               # real scenes first, each group by time
    for i, a in enumerate(found):
        for b in found[i + 1:]:
            if a[4] == b[4] and a[3] != b[3] and a[0] < b[1] and b[0] < a[1]:
                raise RuntimeError(f"scenes {a[3]} ({a[0]}-{a[1]}) and {b[3]} ({b[0]}-{b[1]}) overlap")
    _SPANS[:] = found
    _LOADED = True


def placeholder(F) -> None:
    """Stand-in for a time nobody draws yet."""
    from ..chalk import core as k
    from ..chalk.figure import STAND, figure
    from ..chalk.weather import ground_shadow
    k.chalk(F, k.A((-20, 760), (1940, 763)), k.C.CHALK_DIM, 4.2, 0.85, 11, wob=1.2)
    ground_shadow(F, 968, 762, 90, 0.7)
    figure(F, 960, 760, 300, STAND, "child", seed=3)


def scene_at(t: float):
    """The draw function for time t (the placeholder if nobody draws it)."""
    _load()
    for t0, t1, fn, _name, _demo in _SPANS:
        if t0 <= t < t1:
            return fn
    return placeholder


def draw(F) -> None:
    scene_at(F.t)(F)


def spans() -> list:
    """[(t0, t1, module name), ...] of every registered span, by time."""
    _load()
    return sorted((t0, t1, name) for t0, t1, _fn, name, _demo in _SPANS)
