"""Private: the face of a figure, stamped in whole pixels onto the sprite buffer of _fig_draw.

Features are placed relative to the head centre pixel (so a still head gives the same pixels every
frame) and drawn from small hand-made patterns in three sizes: `s` (wide shots, head radius 3 to
5.5 px: eyes are one or two dark pixels), `m` (standard, the 48 px sprites: 2x3 eyes with one
highlight) and `l` (close, 110 to 130 px figures: big eyes with lash, iris, pupil, highlights, brows,
nose and a shaped mouth). Pixels are written only where the face skin is, so a fringe, a hand or a
phone in front of the face stays in front.
"""
from __future__ import annotations

import numpy as np

from hx.kit._fig_draw import M


def size_class(rpx: float) -> str:
    if rpx < 3.2:
        return ""
    if rpx < 5.5:
        return "s"
    if rpx < 11.0:
        return "m"
    return "l"


class _Pen:
    def __init__(self, mat, part, face_part):
        self.mat, self.part, self.fp = mat, part, face_part
        self.H, self.W = mat.shape

    def put(self, x, y, m):
        x, y = int(x), int(y)
        if 0 <= x < self.W and 0 <= y < self.H and self.part[y, x] == self.fp:
            self.mat[y, x] = M[m]

    def row(self, x0, x1, y, m):
        for x in range(int(min(x0, x1)), int(max(x0, x1)) + 1):
            self.put(x, y, m)


EYE_Y = -0.12          # eye centre below the head centre (head radii)


def layout(front: bool, tw: float):
    """Face centre line and the eyes [(offset along the face direction, narrow, outer sign)]."""
    if front:
        return 0.0, [(-0.40, 0, -1), (0.40, 0, 1)]
    xc = 0.55 - 0.30 * tw
    sep = 0.24 + 0.18 * tw
    eyes = [(xc - sep, 0, -1)]
    if tw >= 0.45:
        eyes.append((xc + sep, 1, 1))
    return xc, eyes


def eye_box(rpx: float):
    """(width, height) of a close eye in pixels."""
    return max(4, int(round(0.44 * rpx))), max(6, int(round(0.58 * rpx)))


def eye_top(rpx: float) -> float:
    """Top of the eye (its lid line) in head radii above the head centre."""
    k = size_class(rpx)
    half = {"s": 1.0, "m": 1.5, "l": eye_box(rpx)[1] / 2.0}.get(k, 1.0)
    return EYE_Y + half / max(rpx, 1e-6)


def stamp(mat, part, ox, oy, *, face_part, hc, fh, uh, rpx, tw, front, lid, mouth, blush, brow, glad,
          light_x=-1, tired=False):
    """lid: open | half | heavy | closed | up; mouth: none | flat | sad | small | smile | open | o;
    blush: 0/1/2; brow: flat | worried | glad (close only); glad: closed eyes arch up (^ ^);
    tired: a faint shadow under the close eyes."""
    k = size_class(rpx)
    if not k:
        return
    pen = _Pen(mat, part, face_part)
    hc = np.asarray(hc, float) - (ox, oy)
    fh = np.asarray(fh, float)
    uh = np.asarray(uh, float)
    fx = 1 if fh[0] >= 0 else -1                 # screen direction the face looks toward

    def at(a, b):
        q = hc + fh * a * rpx + uh * b * rpx
        return int(np.floor(q[0])), int(np.floor(q[1]))

    xc, eyes = layout(front, tw)
    ey_b = EYE_Y
    mx_a, my_b = (xc + 0.12 * (1 - tw) if not front else 0.0), -0.60
    hl_side = light_x if front else -fx          # highlight toward the light / the back of the eye

    for a, narrow, outer in eyes:
        ex, ey = at(a, ey_b)
        osgn = outer * fx                        # screen direction of the outer corner
        if k == "s":
            _eye_s(pen, ex, ey, lid)
        elif k == "m":
            _eye_m(pen, ex, ey, lid, narrow, hl_side, osgn)
        else:
            _eye_l(pen, ex, ey, rpx, lid, narrow, hl_side, osgn, brow, glad, tired)
        if blush and (k == "l" or (k == "m" and blush > 1)):
            by = ey + (2 if k == "m" else eye_box(rpx)[1] // 2 + 2)
            if k == "m":
                pen.put(ex - (0 if osgn > 0 else 1) + osgn, by, "blush")
            else:
                pen.row(ex - 1 + osgn, ex + osgn, by, "blush")
    mx, my = at(mx_a, my_b)
    if k == "l":
        nx, ny = at(xc + 0.14 * tw if not front else 0.0, -0.36)
        pen.put(nx, ny, "skin_sh")
    _mouth(pen, k, mx, my, mouth, fx if not front else 1)


def _eye_s(pen, ex, ey, lid):
    if lid in ("open", "up"):
        pen.put(ex, ey - 1, "lash")
        pen.put(ex, ey, "iris_dk")
    else:
        pen.put(ex, ey, "lash")


def _eye_m(pen, ex, ey, lid, narrow, hl_side, osgn):
    # two columns: the inner one and the one on the outer side
    cols = [ex, ex + osgn] if not narrow else [ex]
    ci = cols[0] if hl_side * osgn < 0 else cols[-1]          # highlight column
    r0, r1, r2 = ey - 1, ey, ey + 1
    for c in cols:
        if lid == "open":
            pen.put(c, r0, "lash")
            pen.put(c, r1, "iris_dk")
            pen.put(c, r2, "iris")
        elif lid == "up":
            pen.put(c, r0, "lash")
            pen.put(c, r1, "iris")
            pen.put(c, r2, "sclera")
        elif lid == "half":
            pen.put(c, r1, "lash")
            pen.put(c, r2, "iris")
        elif lid == "heavy":
            pen.put(c, r1, "lash")
            pen.put(c, r2, "iris_dk")
        else:                                                 # closed: a short lash line
            pen.put(c, r2, "lash")
    if lid in ("open", "up") and not narrow:
        pen.put(ci, r1, "hl")
    elif lid == "half" and not narrow:
        pen.put(ci, r2, "hl")


def _eye_l(pen, ex, ey, rpx, lid, narrow, hl_side, osgn, brow, glad, tired=False):
    ew, eh = eye_box(rpx)
    ew -= 2 if narrow else 0
    # columns from the inner corner (toward the face centre) to the outer corner
    xs = [ex - osgn * (ew // 2) + osgn * i for i in range(ew)]
    top = ey - eh // 2
    bot = top + eh - 1
    if lid == "closed":
        # resting: a line sagging in the middle; glad: an arch (^)
        for i, x in enumerate(xs):
            edge = i == 0 or i == ew - 1
            if glad:
                pen.put(x, ey + (1 if edge else 0), "lash")
            else:
                pen.put(x, ey + (0 if edge else 1), "lash")
        if not glad:
            pen.put(xs[-1] + osgn, ey - 1, "lash")
    else:
        drop = {"open": 0, "up": 0, "half": int(round(eh * 0.34)), "heavy": int(round(eh * 0.46))}[lid]
        lt = top + drop
        for x in xs:                                          # the lid line, two pixels thick
            pen.put(x, lt, "lash")
            pen.put(x, lt + 1, "lash")
        pen.put(xs[-1] + osgn, lt + 1, "lash")                # outer flick
        pen.put(xs[-1] + osgn, lt + 2, "lash")
        inner = xs[1:-1] if ew >= 4 else xs
        for y in range(lt + 2, bot + 1):
            last = y == bot
            for i, x in enumerate(xs):
                side = i == 0 or i == ew - 1
                if side:
                    if not last:
                        pen.put(x, y, "sclera")
                    continue
                if lid == "up" and y >= bot - 1:
                    pen.put(x, y, "sclera")
                elif y <= lt + 3 or lid == "heavy":
                    pen.put(x, y, "iris_dk")
                else:
                    pen.put(x, y, "iris")
        # pupil: the middle of the iris, one row under the shadow
        if lid != "heavy":
            pc = inner[max(0, len(inner) // 2 - 1):len(inner) // 2 + 1] if len(inner) >= 4 else inner[len(inner) // 2:][:1]
            for y in range(lt + 3, min(bot - 1, lt + 6)):
                for x in pc:
                    pen.put(x, y, "iris_dk")
        if lid != "heavy":
            hx = inner[0] if hl_side * osgn < 0 else inner[-1]
            pen.put(hx, lt + 2, "hl")
            if bot - lt >= 5:
                pen.put(hx, lt + 3, "hl")
                pen.put(hx + (osgn if hx == inner[0] else -osgn), lt + 2, "hl")
                lo = inner[-1] if hx == inner[0] else inner[0]
                pen.put(lo, bot - 1, "hl")
        if lid in ("half", "heavy") or tired:
            pen.row(xs[1], xs[-2], bot + 1, "skin_sh")         # tired lower lid
    if brow and lid != "closed":
        by = top - 2
        bx = [ex - osgn * (ew // 2) + osgn * i for i in range(ew - 1)]
        for i, x in enumerate(bx):
            dy = 0
            if brow == "worried":
                dy = -1 if i <= 1 else 0
            elif brow == "glad":
                dy = -1 if 0 < i < len(bx) - 1 else 0
            pen.put(x, by + dy, "brow")


def _mouth(pen, k, mx, my, kind, fx):
    if kind == "none" or not k:
        return
    if k == "s":
        if kind in ("smile", "open"):
            pen.put(mx, my, "mouth" if kind == "smile" else "mouth_in")
        return
    if k == "m":
        if kind in ("flat", "sad"):
            pen.row(mx - 1, mx, my, "mouth")
        elif kind == "small":
            pen.put(mx - 1, my - 1, "mouth")
            pen.put(mx, my, "mouth")
            pen.put(mx + 1, my - 1, "mouth")
        elif kind == "smile":
            pen.put(mx - 2, my - 1, "mouth")
            pen.row(mx - 1, mx, my, "mouth")
            pen.put(mx + 1, my - 1, "mouth")
        elif kind == "open":
            pen.row(mx - 1, mx + 1, my - 1, "mouth_in")
            pen.put(mx - 1, my, "mouth_in")
            pen.put(mx, my, "tongue")
            pen.put(mx + 1, my, "mouth_in")
        elif kind == "o":
            pen.row(mx - 1, mx, my - 1, "mouth_in")
            pen.row(mx - 1, mx, my, "mouth_in")
        return
    # close
    if kind == "flat":
        pen.row(mx - 1, mx + 1, my, "mouth")
    elif kind == "sad":
        pen.row(mx - 1, mx + 1, my, "mouth")
        pen.put(mx - 2, my + 1, "mouth")
        pen.put(mx + 2, my + 1, "mouth")
    elif kind == "small":
        pen.row(mx - 1, mx + 1, my, "mouth")
        pen.put(mx - 2, my - 1, "mouth")
        pen.put(mx + 2, my - 1, "mouth")
    elif kind == "smile":
        pen.row(mx - 1, mx + 1, my + 1, "mouth")
        pen.put(mx - 2, my, "mouth")
        pen.put(mx + 2, my, "mouth")
        pen.put(mx - 3, my - 1, "mouth")
        pen.put(mx + 3, my - 1, "mouth")
    elif kind == "open":
        pen.row(mx - 3, mx + 3, my - 1, "mouth_in")
        pen.row(mx - 2, mx + 2, my, "mouth_in")
        pen.row(mx - 1, mx + 1, my + 1, "tongue")
        pen.row(mx - 1, mx, my, "tongue")
        pen.put(mx - 2, my + 1, "mouth_in")
        pen.put(mx + 2, my + 1, "mouth_in")
        pen.row(mx - 1, mx + 1, my + 2, "mouth_in")
    elif kind == "o":
        pen.row(mx - 1, mx, my - 1, "mouth_in")
        pen.row(mx - 2, mx + 1, my, "mouth_in")
        pen.row(mx - 1, mx, my + 1, "mouth_in")
        pen.row(mx - 1, mx, my, "tongue")
