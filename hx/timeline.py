"""The song's clock: sections, lyric cues (index and time only), beat and bar grid, curves.

Read from hx/data/timeline.json (built by `python -m hx.analyze`). Everything is a pure
function of the recording's time in seconds; video time 0 is audio time 0.
"""
from __future__ import annotations

import bisect
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parent / "data" / "timeline.json"


def smoothstep(a: float, b: float, x: float) -> float:
    if b == a:
        return 1.0 if x >= b else 0.0
    u = min(1.0, max(0.0, (x - a) / (b - a)))
    return u * u * (3.0 - 2.0 * u)


@dataclass(frozen=True)
class Section:
    id: str
    t0: float
    t1: float
    kind: str            # intro verse pre silence chorus interlude bridge breakdown outro coda
    hope: float
    loud: float          # mean loudness 0..1
    lrc: tuple           # LRC line indices sung in it
    index: int

    @property
    def dur(self) -> float:
        return self.t1 - self.t0

    def u(self, t: float) -> float:
        """Position through the section, 0 at t0 and 1 at t1 (leaves the range outside it)."""
        return (t - self.t0) / (self.t1 - self.t0)


@dataclass(frozen=True)
class Cue:
    lrc: int             # 0-based line index in the LRC file
    t: float             # the line's stamp
    t_end: float         # the line may stay up until here
    n_chars: int
    groups: tuple        # character count of each phrase group of the line
    next_is_text: bool
    section: str


class Timeline:
    def __init__(self, data: dict):
        m = data["meta"]
        self.meta = m
        self.duration, self.fps, self.n_frames = m["duration"], m["fps"], m["n_frames"]
        self.beat0, self.beat_s, self.bpm = m["beat0"], m["beat_s"], m["bpm"]
        self.audio, self.lrc_path = m["audio"], m["lrc"]
        self.sections = [Section(s["id"], s["t0"], s["t1"], s["kind"], s["hope"], s["loud"], tuple(s["lrc"]), i)
                         for i, s in enumerate(data["sections"])]
        self._sec = {s.id: s for s in self.sections}
        self._sec_t0 = [s.t0 for s in self.sections]
        self.cues = [Cue(c["lrc"], c["t"], c["t_end"], c["n_chars"], tuple(c["groups"]), c["next_is_text"],
                         c["section"]) for c in data["cues"]]
        self._cue = {c.lrc: c for c in self.cues}
        self._cue_t = [c.t for c in self.cues]
        self.beats = np.asarray(data["beats"])
        self.bars = np.asarray(data["bars"])
        self._hope_t = np.asarray([h[0] for h in data["hope"]])
        self._hope_v = np.asarray([h[1] for h in data["hope"]])
        self.onsets = np.asarray(data["onsets"]).reshape(-1, 2)
        self._hz = m["curve_hz"]
        self._curves = {k: np.asarray(v, dtype=np.float64) for k, v in data["curves"].items()}

    # ---- sections and cues ----------------------------------------------------
    def section(self, sid: str) -> Section:
        return self._sec[sid]

    def section_at(self, t: float) -> Section:
        return self.sections[max(0, bisect.bisect_right(self._sec_t0, t) - 1)]

    def cue(self, lrc: int) -> Cue:
        return self._cue[lrc]

    def cue_at(self, t: float) -> Cue | None:
        """The line being sung at t (from its stamp to its t_end), else None."""
        i = bisect.bisect_right(self._cue_t, t) - 1
        if i < 0:
            return None
        c = self.cues[i]
        return c if t < c.t_end else None

    # ---- grid -------------------------------------------------------------------
    def beat_at(self, t: float) -> tuple[int, float]:
        """(beat number k, fraction through it). k is negative before the first beat."""
        x = (t - self.beat0) / self.beat_s
        k = math.floor(x)
        return k, x - k

    def beat_time(self, k: float) -> float:
        return self.beat0 + self.beat_s * k

    def bar_at(self, t: float) -> tuple[int, int, float]:
        """(bar number, beat inside the bar from 0, fraction through the bar)."""
        i = max(0, int(np.searchsorted(self.bars, t, side="right")) - 1)
        b0 = float(self.bars[i])
        b1 = float(self.bars[i + 1]) if i + 1 < len(self.bars) else b0 + 4 * self.beat_s
        return i, int((t - b0) / self.beat_s + 1e-6), (t - b0) / (b1 - b0)

    def beats_between(self, t0: float, t1: float) -> np.ndarray:
        return self.beats[(self.beats >= t0) & (self.beats < t1)]

    def bars_between(self, t0: float, t1: float) -> np.ndarray:
        return self.bars[(self.bars >= t0) & (self.bars < t1)]

    def onsets_between(self, t0: float, t1: float, min_strength: float = 0.0) -> np.ndarray:
        """Rows (time, strength 0..1) of the recording's measured attacks in [t0, t1)."""
        o = self.onsets
        return o[(o[:, 0] >= t0) & (o[:, 0] < t1) & (o[:, 1] >= min_strength)]

    # ---- curves -----------------------------------------------------------------
    def curve(self, name: str, t: float) -> float:
        """loud (slow loudness), fast (quick envelope), hit (attacks), kick (low attacks), bright: all 0..1."""
        v = self._curves[name]
        x = min(max(t, 0.0) * self._hz, len(v) - 1.0)
        i = int(x)
        j = min(i + 1, len(v) - 1)
        return float(v[i] + (v[j] - v[i]) * (x - i))

    def hope(self, t: float) -> float:
        """The film's one dial: 0 = the weight at the start, 1 = the world in colour."""
        i = int(np.searchsorted(self._hope_t, t, side="right")) - 1
        if i < 0:
            return float(self._hope_v[0])
        if i + 1 >= len(self._hope_t):
            return float(self._hope_v[-1])
        w = smoothstep(self._hope_t[i], self._hope_t[i + 1], t)
        return float(self._hope_v[i] + (self._hope_v[i + 1] - self._hope_v[i]) * w)


@lru_cache(maxsize=1)
def get_timeline() -> Timeline:
    return Timeline(json.loads(DATA.read_text()))
