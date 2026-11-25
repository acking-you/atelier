"""hx.chalk.sketch: a set is data. Named strokes and fills that draw themselves on, are un-drawn,
and turn into the strokes of another set.

A prop is a function returning a Sketch (an ordered list of Stroke and Fill items in paint order,
each with a name such as "sofa.back"). Because a set is data, a scene change is never a cut:

    S = props.sofa(230, 744)                  # world coordinates
    S.on_beats(F.tl, 3.0, every=1)            # one part per beat from the first beat after 3.0 s
    S.sub("sofa.arm_r").set_off(30.0, 31.2)   # that part is wiped off again later
    S.draw(F)                                 # every item at its own stage for F.t

An item's stage comes from its times on the song's clock: on = (t0, t1) draws it on (the chalk tip
leads, the pressure builds behind it), off = (t0, t1) takes it back from both ends and leaves a rubbed
ghost that fades. morph(A, B, w, pairs) is the set between two sets: only DECLARED pairs travel.
"""
from __future__ import annotations

import math

import numpy as np

from .core import A, C, Frame, chalk, disc, ease, fill, fit, hand, hatch, mix, ramp, rsym, seg, smooth

GHOST = 0.20                     # pressure of the rubbed ghost a wiped stroke leaves
_STATE = ("name", "on", "off", "pon", "poff")


class Stroke:
    """One chalk line: world points P, colour, world width w, pressure a, seed, a name, and any
    keyword of core.chalk (wob, taper, edge, grain, step, var, under, floor)."""
    __slots__ = ("P", "col", "w", "a", "seed", "kw") + _STATE

    def __init__(self, P, col=C.CHALK, w=4.0, a=1.0, seed=0, name="", **kw):
        self.P = np.asarray(P, dtype=np.float64)
        self.col, self.w, self.a, self.seed, self.kw, self.name = col, float(w), float(a), int(seed), kw, name
        self.on = self.off = self.pon = self.poff = None

    def copy(self, **ch):
        s = Stroke.__new__(Stroke)
        for k in Stroke.__slots__:
            setattr(s, k, getattr(self, k))
        s.kw = dict(self.kw)
        for k, v in ch.items():
            setattr(s, k, v)
        return s

    @property
    def cx(self) -> float:
        return float(self.P[:, 0].mean())


class Fill:
    """A coloured-in area: closed world outline P, optional rub-out (knock colour), optional rubbed
    base tone (alpha `base`), then a zigzag (angle, gap, line width w, alpha a; a = 0 for none)."""
    __slots__ = ("P", "col", "ang", "gap", "w", "a", "seed", "knock", "base", "grain", "clip") + _STATE

    def __init__(self, P, col, ang=0.8, gap=10.0, w=5.0, a=0.8, seed=0, knock=None, base=0.0, grain="mid",
                 clip=False, name=""):
        self.P = np.asarray(P, dtype=np.float64)
        self.col, self.ang, self.gap, self.w, self.a, self.seed = col, ang, float(gap), float(w), float(a), int(seed)
        self.knock, self.base, self.grain, self.clip, self.name = knock, base, grain, clip, name
        self.on = self.off = self.pon = self.poff = None

    def copy(self, **ch):
        f = Fill.__new__(Fill)
        for k in Fill.__slots__:
            setattr(f, k, getattr(self, k))
        for k, v in ch.items():
            setattr(f, k, v)
        return f

    @property
    def cx(self) -> float:
        return float(self.P[:, 0].mean())


def _under(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(prefix + ".")


class Sketch:
    """An ordered collection of named Strokes and Fills (paint order). Sketches add up with +."""

    def __init__(self, items=(), name: str = ""):
        self.items = []
        for it in items:
            self.items.extend(it.items if isinstance(it, Sketch) else it if isinstance(it, (list, tuple)) else [it])
        if name:                                         # prefix the names: Sketch([...], "sofa")
            for it in self.items:
                it.name = f"{name}.{it.name}" if it.name else name

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __add__(self, other):
        return Sketch([self, other])

    def __radd__(self, other):
        return Sketch([other, self]) if other else self

    def __getitem__(self, key):
        """S[i] / S[i:j] by position, S["sofa.back"] one item, S["sofa"] the sub-sketch of that prefix."""
        if isinstance(key, slice):
            return Sketch(self.items[key])
        if isinstance(key, str):
            for it in self.items:
                if it.name == key:
                    return it
            return self.sub(key)
        return self.items[key]

    def names(self) -> list:
        return [it.name for it in self.items]

    def strokes(self) -> list:
        return [it for it in self.items if isinstance(it, Stroke)]

    def sub(self, *prefixes) -> "Sketch":
        """The items named `prefix` or `prefix.something` (same objects: setting times on them sticks)."""
        return Sketch([it for it in self.items if any(_under(it.name, p) for p in prefixes)])

    def without(self, *prefixes) -> "Sketch":
        return Sketch([it for it in self.items if not any(_under(it.name, p) for p in prefixes)])

    def place(self, dx: float = 0.0, dy: float = 0.0, scale: float = 1.0, origin=(0.0, 0.0)) -> "Sketch":
        """A copy moved and scaled in the world: P -> (P - origin) * scale + origin + (dx, dy); widths,
        hatch gaps and the hand wobble scale with it."""
        o = np.asarray(origin, dtype=np.float64)
        out = []
        for it in self.items:
            c = it.copy(P=(it.P - o) * scale + o + (dx, dy), w=it.w * scale)
            if isinstance(c, Fill):
                c.gap = it.gap * scale
            elif scale != 1.0:
                c.kw["wob"] = c.kw.get("wob", 1.0) * min(1.3, max(0.3, scale))
            out.append(c)
        return Sketch(out)

    # ---- times on the song's clock ----------------------------------------------------
    def set_on(self, t0: float, t1: float) -> "Sketch":
        """Every item draws itself on between t0 and t1 (all at once)."""
        for it in self.items:
            it.on = (t0, t1)
        return self

    def set_off(self, t0: float, t1: float) -> "Sketch":
        """Every item is wiped off between t0 and t1 (retreat, then the ghost fades)."""
        for it in self.items:
            it.off = (t0, t1)
        return self

    def groups(self, by: int | None = None) -> list:
        """Runs of items that belong together: 'x.fill' goes with 'x' (by=None), or items sharing
        the first `by` parts of their names (by=1: a whole prop)."""
        out, last = [], None
        for it in self.items:
            n = it.name
            key = ".".join(n.split(".")[:by]) if by else (n[:-5] if n.endswith(".fill") else n)
            if out and key and key == last:
                out[-1].append(it)
            else:
                out.append([it])
            last = key
        return out

    def spread(self, t0: float, every: float, dur: float, by: int | None = None, attr: str = "on") -> float:
        """Give each group its span: group i starts at t0 + i * every seconds and takes dur seconds
        (attr 'on' = draw on, 'off' = wipe off). A group's strokes follow each other inside the span;
        its fill is coloured in as the outline closes (and leaves first). Returns the end time."""
        end = t0
        for i, g in enumerate(self.groups(by)):
            ta = t0 + i * every
            lines = [x for x in g if isinstance(x, Stroke)]
            n = max(1, len(lines))
            for j, s in enumerate(lines):
                a0 = ta + dur * 0.7 * j / n
                setattr(s, attr, (a0, a0 + dur * (0.3 + 0.7 / n)))
            for f in (x for x in g if isinstance(x, Fill)):
                setattr(f, attr, (ta + 0.75 * dur, ta + 1.6 * dur) if attr == "on" else (ta, ta + 0.7 * dur))
            end = ta + dur * (1.6 if attr == "on" and len(lines) < len(g) else 1.0)
        return end

    def on_beats(self, tl, t0: float, every: float = 1.0, dur: float = 1.0, by: int | None = None) -> float:
        """Draw on with the music: one group per `every` beats (0.5 = per half beat) from the first
        beat at or after t0; each takes `dur` beats. tl is F.tl. Returns the end time in seconds."""
        k0 = math.ceil((t0 - tl.beat0) / tl.beat_s - 1e-6)
        return self.spread(tl.beat_time(k0), every * tl.beat_s, dur * tl.beat_s, by, "on")

    def off_beats(self, tl, t0: float, every: float = 1.0, dur: float = 1.0, by: int | None = None) -> float:
        """Wipe off with the music (see on_beats)."""
        k0 = math.ceil((t0 - tl.beat0) / tl.beat_s - 1e-6)
        return self.spread(tl.beat_time(k0), every * tl.beat_s, dur * tl.beat_s, by, "off")

    # ---- painting -----------------------------------------------------------------------
    def draw(self, F: Frame, d: float | None = None, a: float = 1.0, thin: float = 1.0, tint=None,
             tint_w: float = 0.0, overlap: float = 0.25) -> None:
        """Paint the set at F.t.

        d: optional progress 0..1 of the whole set in authoring order (items overlap by `overlap`);
           it combines with the items' own on/off times. a: pressure of the whole set.
        thin: line-width factor, tint/tint_w: fade toward a colour (far sets: dimmer, thinner, hazier).
        """
        n = len(self.items)
        if n == 0 or a <= 0.003:
            return
        t = F.t
        for i, it in enumerate(self.items):
            p_on = it.pon if it.pon is not None else (seg(t, *it.on) if it.on else 1.0)
            if d is not None and d < 1.0:
                s0 = (i / n) * (1.0 - overlap)
                p_on = min(p_on, seg(d, s0, s0 + overlap + 1.0 / n))
            p_off = it.poff if it.poff is not None else (seg(t, *it.off) if it.off else 0.0)
            if p_on <= 0.0 or p_off >= 1.0:
                continue
            col = it.col if tint is None else mix(it.col, tint, tint_w)
            (_stroke if isinstance(it, Stroke) else _fill)(F, it, col, p_on, p_off, a, thin)


def _stroke(F, it, col, p_on, p_off, a, thin):
    kw, w, a = it.kw, it.w * thin, it.a * a
    if p_off > 0.0:
        # wiped off: the line is taken back from both ends; what the rubbing leaves fades after it
        g = ramp(p_off, 0.0, 0.25) * (1.0 - ramp(p_off, 0.45, 1.0))
        if g > 0.0:
            # two rubbed passes, the wider one fainter: a smear with a soft edge, not a band
            for gw, ga in ((3.6, 0.5), (2.0, 0.6)):
                chalk(F, it.P, col, w * gw + 3.0, a * GHOST * ga * g, it.seed, kw.get("wob", 1.0), taper=0.6, grain="soft",
                      edge=0.0, boil=0.0, step=kw.get("step", 6.0), var=0.35, baked=kw.get("baked", False), floor=3.0)
        q = ease(seg(p_off, 0.0, 0.6))
        if q < 1.0:
            chalk(F, it.P, col, w, a * (1.0 - 0.3 * q), it.seed, draw=(0.5 * q, 1.0 - 0.5 * q), **kw)
    elif p_on < 1.0:
        # drawn on: the tip leads, the pressure builds behind it
        tip = chalk(F, it.P, col, w, a * (0.75 + 0.25 * p_on), it.seed, draw=(0.0, 0.5 * p_on + 0.5 * ease(p_on)),
                    lead=14.0 * w, **kw)
        if tip is not None:
            disc(F, tip[0], tip[1], w * 0.75, col if F.day else mix(col, C.CHALK, 0.6), 0.95 * a, None, floor=1.4)
    else:
        chalk(F, it.P, col, w, a, it.seed, **kw)


def _fill(F, it, col, p_on, p_off, a, thin):
    vis = 1.0 - p_off
    if it.knock is not None:
        fill(F, it.P, it.knock, 0.93 * a * min(1.0, p_on * 2.5) * vis)
    if it.base > 0.0:
        fill(F, it.P, col, it.base * a * p_on * vis, "mid")
    if it.a > 0.0:
        dr = p_on if p_off <= 0.0 else (0.0, 1.0 - ease(seg(p_off, 0.0, 0.6)))
        hatch(F, it.P, col, it.ang, it.gap, it.w * thin, it.a * a, it.seed, grain=it.grain, draw=dr, clip=it.clip)


# --------------------------------------------------------------------------
# one set turning into another
# --------------------------------------------------------------------------
OFF, MOVE, ON = (0.0, 0.50), (0.20, 0.80), (0.50, 1.0)      # when the three things happen, in w


def _resolve(A, B, pairs) -> dict:
    """{id(stroke of B): stroke of A} for the declared pairs (names, or prefixes paired in order)."""
    sa, sb = A.strokes(), B.strokes()
    out, used = {}, set()
    for na, nb in pairs:
        la = [s for s in sa if _under(s.name, na) and id(s) not in used]
        lb = [s for s in sb if _under(s.name, nb) and id(s) not in out]
        if not la or not lb:
            raise KeyError(f"morph pair {na!r} -> {nb!r}: no free stroke of that name in the {'first' if not la else 'second'} set")
        for x, y in zip(la, lb):
            out[id(y)] = x
            used.add(id(x))
    return out


def _arclen(P):
    return np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])


def _baked(s: Stroke):
    """The stroke's points with its hand wobble already in them, and, for an outline that closes on
    its start (with or without the overshoot of props.closed), the arc length of the closed part
    (0 for an open line)."""
    P = s.P
    u = _arclen(P)
    back = np.hypot(P[:, 0] - P[0, 0], P[:, 1] - P[0, 1]) < 0.004 * u[-1] + 1e-9
    back &= u > 0.5 * u[-1]
    ring = float(u[int(np.argmax(back))]) if len(P) > 3 and back.any() else 0.0
    if s.kw.get("baked"):
        return P, ring
    return hand(P, s.seed, 0, s.kw.get("wob", 1.0), s.kw.get("step", 6.0), 0.0, 1.0)[0], ring


def _length(P) -> float:
    return float(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])).sum())


def _as_ring(P, ring: float, n: int):
    """n points once round a stroke: round its closed part, or, for an open line, there and back."""
    if ring > 0.0:
        u = _arclen(P)
        q = np.linspace(0.0, min(ring, u[-1]), n, endpoint=False)
        return np.stack([np.interp(q, u, P[:, 0]), np.interp(q, u, P[:, 1])], axis=1)
    h = n // 2
    return np.vstack([fit(P, h + 1)[:-1], fit(P[::-1], n - h + 1)[:-1]])


def _turned(R, onto):
    """Ring R started at the point, and run in the sense, that lie closest to the ring `onto`."""
    n = len(R)
    idx = (np.arange(n)[None, :] + np.arange(n)[:, None]) % n            # [shift, i]
    best, cost = R, np.inf
    for Q in (R, R[::-1]):
        c = ((Q[idx] - onto[None, :, :]) ** 2).sum((1, 2))
        k = int(c.argmin())
        if c[k] < cost:
            best, cost = Q[idx[k]], float(c[k])
    return best


def _travel(sa: Stroke, sb: Stroke, wi: float, seed: int) -> Stroke:
    """Stroke sa on its way to sb: both resampled by arc length, the change running along the line.
    Two open lines travel end to end. If either is a closed outline both are taken as rings (an open
    line as its own there-and-back), turned to lie closest to each other: an outline flattens into
    a line, a line opens into an outline, and nothing is unrolled across the picture."""
    if wi <= 0.0:
        return sa
    if wi >= 1.0:
        return sb
    (Pa, ra), (Pb, rb) = _baked(sa), _baked(sb)
    n = int(min(160, max(24, max(_length(Pa), _length(Pb)) / 8.0)))
    st, lap = 0.35, 0
    if ra > 0.0 or rb > 0.0:
        Pa, Pb = _as_ring(Pa, ra, n), _as_ring(Pb, rb, n)
        if rb > 0.0 and ra <= 0.0:
            Pb = _turned(Pb, Pa)                         # the stroke starts where the open line starts
        else:
            Pa = _turned(Pa, Pb)
        lap = max(2, n // 14)                            # it closes over its own start, as closed() does
    else:
        Pa, Pb = fit(Pa, n), fit(Pb, n)
        if ((Pa - Pb[::-1]) ** 2).sum() < ((Pa - Pb) ** 2).sum():        # do not cross over on the way
            Pb = Pb[::-1]
    e = smooth(wi * (1.0 + st) - st * np.linspace(0.0, 1.0, n))[:, None]
    P = Pa + (Pb - Pa) * e
    if lap:
        P = np.vstack([P, P[:lap + 1]])
    mid = Pb.mean(0) - Pa.mean(0)
    P = P + np.array([-mid[1], mid[0]]) * (0.06 * math.sin(math.pi * wi) * rsym(seed * 31 + sa.seed, 2))
    src = sa if wi < 0.5 else sb
    kw = dict(src.kw)
    kw.pop("under", None)
    kw["baked"] = True
    kw["wob"] = sa.kw.get("wob", 1.0) + (sb.kw.get("wob", 1.0) - sa.kw.get("wob", 1.0)) * wi
    a = (sa.a + (sb.a - sa.a) * wi) * (1.0 - 0.4 * math.sin(math.pi * wi))      # a line on its way is pressed lightly
    return Stroke(P, mix(sa.col, sb.col, wi), sa.w + (sb.w - sa.w) * wi, a, src.seed, name=sb.name, **kw)


def morph(A, B, w: float, pairs=(), stagger: float = 0.5, seed: int = 0) -> Sketch:
    """The set between A and B at w in 0..1 (draw it with .draw(F)).

    pairs: ((name_in_A, name_in_B), ...). A name is one stroke, or a prefix whose strokes are paired
    in order ("sofa" -> "desk"). Only those travel (window to window, ground line to ground line),
    by arc-length resampling, the change running along each line. Everything else of A is wiped off
    first (w 0..0.5), everything else of B draws on last (w 0.5..1); the pairs travel in between.
    Each of the three sweeps the picture from left to right; `stagger` = how much of its time the
    sweep takes (0 = all at once). Fills leave before, and arrive after, their outlines.
    """
    A, B = Sketch([A]), Sketch([B])
    if w <= 0.0:
        return A
    if w >= 1.0:
        return B
    pair = _resolve(A, B, pairs)
    gone = {id(s) for s in pair.values()}
    xs = [it.cx for it in A] + [it.cx for it in B]
    x0, span = min(xs), max(1.0, max(xs) - min(xs))

    def window(ph, x):
        d = ph[1] - ph[0]
        s0 = ph[0] + d * stagger * min(1.0, max(0.0, (x - x0) / span))
        return s0, s0 + d * (1.0 - stagger)

    arrive = {s.name: window(MOVE, 0.5 * (pair[id(s)].cx + s.cx)) for s in B.strokes() if id(s) in pair}
    waits = {id(pair[id(s)]) for s in B.strokes() if id(s) in pair and w <= arrive[s.name][0]}
    out = []
    for it in A:
        if id(it) in gone:
            if id(it) in waits:                          # not off yet: it stays in its own place in the paint
                out.append(it)                           # order, under the fills that hide parts of it
            continue
        p = seg(w, *window(OFF, it.cx))
        if isinstance(it, Fill):
            p = min(1.0, p * 1.6)
        if p < 1.0:
            out.append(it.copy(poff=max(p, it.poff or 0.0)))
    for it in B:
        if isinstance(it, Stroke):
            if id(it) in pair:
                sa = pair[id(it)]
                if id(sa) not in waits:
                    out.append(_travel(sa, it, seg(w, *arrive[it.name]), seed))
            else:
                p = seg(w, *window(ON, it.cx))
                if p > 0.0:
                    out.append(it.copy(pon=p))
        else:
            stem = it.name[:-5] if it.name.endswith(".fill") else ""
            if stem in arrive:                           # its outline travels: colour it in once that has arrived
                t1 = min(1.0, arrive[stem][1] + 0.18)
                p = seg(w, min(arrive[stem][1], t1 - 0.1), t1)
            else:
                p = seg(seg(w, *window(ON, it.cx)), 0.4, 1.0)
            if p > 0.0:
                out.append(it.copy(pon=p))
    return Sketch(out)


# --------------------------------------------------------------------------
# two shorthands for single strokes
# --------------------------------------------------------------------------
def line(x0, y0, x1, y1, col=C.CHALK, w=4.0, a=1.0, seed=0, name="", **kw) -> Stroke:
    """A straight stroke between two world points."""
    return Stroke(A((x0, y0), (x1, y1)), col, w, a, seed, name, **kw)


def closed(P, col=C.CHALK, w=4.0, a=1.0, seed=0, name="", **kw) -> Stroke:
    """A closed outline that overshoots its start a little, as a child closes a shape."""
    P = np.asarray(P, dtype=np.float64)
    n = max(2, len(P) // 12)
    return Stroke(np.vstack([P, P[1:n + 1]]), col, w, a, seed, name, **kw)
