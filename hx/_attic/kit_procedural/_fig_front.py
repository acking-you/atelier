"""Private: the figures seen straight from the front (view='front') or straight from behind
(view='back_front'), for standing, walking toward / away, sitting with knees up, cross-legged and
the arms out to the sides. The heights of every joint come from the three-quarter skeleton of the
same Pose; a swing forward in that skeleton becomes depth (foreshortened), `Pose.spread_*` swings an
arm out to the side instead.
"""
from __future__ import annotations

import math

import numpy as np

from hx.kit import figures as F
from hx.kit._fig_geom import segment

PI = math.pi


class Front(F._Fig):
    def __init__(self, who, p, pr, B, *, view, t, wind_l, seed, head_tilt, face):
        super().__init__(who, p, pr, B, view=view, t=t, wind_l=wind_l, seed=seed, head_tilt=head_tilt,
                         flat=False, face=face)
        self.back = view == "back_front"
        self.tw = 1.0
        j = self.j
        self.cx = float(j["P"][0])
        cx = self.cx
        self.sw = (0.126 if self.child else 0.104) * pr.girth
        self.hw = (0.128 if self.child else 0.124) * pr.girth
        seated = self.seat > 0.5
        self.mode = "cross" if p.legs_front >= 1.5 else ("knees" if seated else "stand")
        depth = -1.0 if self.back else 1.0            # a step toward the viewer comes down the screen
        # legs
        for side, sx in (("n", 1.0), ("f", -1.0)):
            H, K, A = j["H_" + side], j["K_" + side], j["A_" + side]
            if self.mode == "stand":
                fk = (K[0] - cx) * 0.25 * depth
                fa = (A[0] - cx) * 0.35 * depth
                j["H_" + side] = np.array((cx + sx * 0.050, H[1]))
                j["K_" + side] = np.array((cx + sx * 0.054, K[1] - fk))
                j["A_" + side] = np.array((cx + sx * 0.056, A[1] - fa))
            elif self.mode == "knees":
                j["H_" + side] = np.array((cx + sx * 0.052, H[1]))
                j["K_" + side] = np.array((cx + sx * 0.058, max(K[1], A[1] + 0.12)))
                j["A_" + side] = np.array((cx + sx * 0.056, A[1]))
            else:
                seat_y = min(H[1], 0.06)
                j["H_" + side] = np.array((cx + sx * 0.050, H[1]))
                j["K_" + side] = np.array((cx + sx * 0.190, seat_y + 0.030))
                j["A_" + side] = np.array((cx - sx * 0.040, seat_y + 0.026))
        # arms: heights from the skeleton, sideways reach from spread / hands together
        hn, hf = j["W_n"], j["W_f"]
        together = 1.0 - F._smooth((np.linalg.norm(hn - hf) - 0.06) / 0.08)
        together *= F._smooth(((hn[0] + hf[0]) * 0.5 - cx - 0.0) / 0.06)
        Ny = j["N"][1]
        for side, sx in (("n", 1.0), ("f", -1.0)):
            S, E, W = j["S_" + side], j["E_" + side], j["W_" + side]
            sp = getattr(p, "spread_" + side)
            S2 = np.array((cx + sx * self.sw * 0.86, Ny - 0.058))
            dyE, dyW = E[1] - S[1], W[1] - S[1]
            latE = (1 - sp) * 0.018 + sp * abs(E[0] - S[0])
            latW = (1 - sp) * 0.016 + sp * abs(W[0] - S[0])
            if sp < 0.5:
                latW = latW * (1 - together) + (0.030 - self.sw * 0.86) * together
                latE = latE * (1 - 0.6 * together)
            E2 = S2 + np.array((sx * latE, dyE))
            W2 = S2 + np.array((sx * latW, dyW))
            j["S_" + side], j["E_" + side], j["W_" + side] = S2, E2, W2
            v = W2 - E2
            j["fore_" + side] = math.atan2(v[0], -v[1])
        # the head straight on; a nod drops the face features, a lifted head raises them
        j["Hc"] = np.array((cx, j["Hc"][1]))
        self.pitch = float(j["ha"])
        j["uh"], j["fh"] = np.array((0.0, 1.0)), np.array((1.0, 0.0))
        j["C"] = np.array((cx, j["C"][1]))
        j["N"] = np.array((cx, Ny))
        j["d0"] = j["d1"] = j["d2"] = np.array((0.0, 1.0))

    # ---- legs ------------------------------------------------------------------------------
    def leg(self, side):
        B, j, pr = self.B, self.j, self.pr
        H, K, A = j["H_" + side], j["K_" + side], j["A_" + side]
        near = True
        lr = pr.leg_r * (1.08 if self.child else 1.0)
        base = "leg"
        B.part(cast=True)
        if self.mode == "knees":
            path = segment(A + np.array((0.0, 0.02)), K, lr * 1.05, lr * 1.10)
            B.formed(path, base, "leg_sh", None, d=self.d(3))
        elif self.mode == "cross":
            B.formed(segment(H, K, lr * 1.05, lr), base, "leg_sh", None, d=self.d(2))
            B.formed(segment(K, A, lr, lr * 0.9), base, "leg_sh", None, d=self.d(2))
        else:
            B.formed(segment(H, K, lr, lr * 0.96), base, "leg_sh", None, d=self.d(2))
            B.formed(segment(K, A + np.array((0.0, 0.02)), lr * 0.96, lr * 0.98 if self.child else lr * 0.75),
                     base, "leg_sh", None, d=self.d(2))
        self.shoe(side, A)

    def shoe(self, side, A):
        B = self.B
        near = True
        B.part(cast=True)
        if self.mode == "cross":
            sx = 1.0 if side == "n" else -1.0
            c = A + np.array((-sx * 0.035, -0.006))
            B.formed(F.D_ellipse(c, (1, 0), 0.034, 0.026), "shoe" if near else "shoe_sh", "shoe_sh", None, d=1)
            return
        ax, ay = A[0], A[1] - F.ANKLE
        w = 0.040 if self.child else 0.036
        if self.child:
            pts = np.array([(ax - w, ay), (ax + w, ay), (ax + w * 1.02, ay + 0.022), (ax + w * 0.7, ay + 0.044),
                            (ax - w * 0.7, ay + 0.044), (ax - w * 1.02, ay + 0.022)])
        else:
            pts = np.array([(ax - w, ay), (ax + w, ay), (ax + w, ay + 0.11), (ax - w, ay + 0.11)])
        det = []
        if self.mid:
            sy = ay + B.px(1)
            det.append(("f", B.path(np.array([(ax - 0.1, ay - 0.05), (ax + 0.1, ay - 0.05), (ax + 0.1, sy),
                                              (ax - 0.1, sy)]), False), B.code("sole" if self.child else "shoe_sh")))
            if not self.child:
                det.append(("f", B.path(np.array([(ax - 0.1, ay + 0.095), (ax + 0.1, ay + 0.095), (ax + 0.1, ay + 0.12),
                                                  (ax - 0.1, ay + 0.12)]), False), B.code("acc")))
        B.formed(pts, "shoe" if near else "shoe_sh", "shoe_sh", None, d=self.d(2), details=det,
                 smooth_=not self.child)

    # ---- torso -----------------------------------------------------------------------------
    def torso(self):
        B, j, pr, p = self.B, self.j, self.pr, self.p
        cx = self.cx
        Py, Ny = j["P"][1], j["N"][1]
        sw, hw = self.sw, self.hw
        if self.mode != "stand":
            hem = Py - 0.02
        else:
            hem = Py - pr.hem
        flare = 0.0 if self.child else 0.02
        lag = self.lag * 0.04
        pts = np.array([(cx - 0.030, Ny + 0.006), (cx - sw * 0.72, Ny - 0.022), (cx - sw, Ny - 0.070),
                        (cx - sw * 1.02, (Ny + hem) * 0.5), (cx - hw - flare + lag, hem + 0.02), (cx - hw - flare + lag, hem),
                        (cx + hw + flare + lag, hem), (cx + hw + flare + lag, hem + 0.02), (cx + sw * 1.02, (Ny + hem) * 0.5),
                        (cx + sw, Ny - 0.070), (cx + sw * 0.72, Ny - 0.022), (cx + 0.030, Ny + 0.006)])
        if self.back:
            self.hood_back(Ny)
        B.part(cast=True)
        det = []
        if self.big:
            det.append(("f", B.path(np.array([(cx - 0.3, hem - 0.1), (cx + 0.3, hem - 0.1), (cx + 0.3, hem + 0.022),
                                              (cx - 0.3, hem + 0.022)]), False), B.code("cloth_sh")))
        if not self.child and not self.back and self.mid:
            for u in (0.15, 0.40, 0.65):
                by = hem + 0.03 + u * (Ny - 0.07 - hem - 0.03)
                if self.big:
                    det.append(("f", B.path(F.D_ellipse((cx, by), (1, 0), 0.011, 0.011)), B.code("acc")))
                else:
                    det.append(("f", F._px_rect(B.P(np.array((cx, by)))), B.code("acc")))
        B.formed(pts, "cloth", "cloth_sh", "cloth_lt" if (not self.child or self.big) else None,
                 d=self.d(3), dl=self.d(1), details=det, smooth_=False)
        if self.back:
            return
        if self.child:
            # the hood lying round the neck as a collar, the neck's V inside it
            B.part(cast=True)
            B.formed(np.array([(cx - 0.085, Ny + 0.012), (cx + 0.085, Ny + 0.012), (cx + 0.030, Ny - 0.080),
                               (cx - 0.030, Ny - 0.080)]), "cloth", "cloth_sh", None, d=self.d(2), smooth_=False)
            B.part(cast=False, recv=False)
            B.fill(np.array([(cx - 0.042, Ny + 0.014), (cx + 0.042, Ny + 0.014), (cx, Ny - 0.050)]), "skin_sh", False)
            if self.mid and self.mode != "knees":
                B.part(cast=True)
                y0, y1 = hem + 0.020, hem + 0.105
                B.formed(np.array([(cx - 0.062, y1), (cx + 0.062, y1), (cx + 0.082, y0), (cx - 0.082, y0)]),
                         "cloth", "cloth_sh", None, d=self.d(2), smooth_=False)
        else:
            if self.mid and self.mode == "stand":
                for sx in (-1.0, 1.0):
                    B.part(cast=True)
                    c0 = np.array((cx + sx * 0.068, hem + 0.060))
                    pk = np.array([c0 + (-0.036, 0.030), c0 + (0.036, 0.030), c0 + (0.036, -0.032), c0 + (-0.036, -0.032)])
                    pdet = [("s", F._seg_path(B, B.P(np.array([c0 + (-0.036, 0.014), c0 + (0.036, 0.014)]))),
                             B.code("line"), 1.0)]
                    B.formed(pk, "cloth", "cloth_sh", None, d=self.d(2), details=pdet, smooth_=False)
            B.part(cast=False, recv=False)
            B.fill(np.array([(cx - 0.040, Ny + 0.012), (cx + 0.040, Ny + 0.012), (cx, Ny - 0.040)]), "collar", False)

    def hood_back(self, Ny):
        B, cx = self.B, self.cx
        B.part(cast=True)
        pts = np.array([(cx - 0.090, Ny + 0.010), (cx + 0.090, Ny + 0.010), (cx + 0.080, Ny - 0.060),
                        (cx + 0.030, Ny - 0.130), (cx - 0.030, Ny - 0.130), (cx - 0.080, Ny - 0.060)])
        det = []
        if self.mid:
            det.append(("s", F._seg_path(B, B.P(np.array([(cx - 0.06, Ny - 0.01), (cx, Ny - 0.09), (cx + 0.06, Ny - 0.01)]))),
                        B.code("cloth_sh"), 1.0))
        self._hood_pts = pts
        B.formed(pts, "cloth", "cloth_sh", None, d=self.d(2), details=det)

    def hood(self, *a):
        return

    def strings(self):
        if not self.child or self.back or not self.k:
            return
        B, j, cx = self.B, self.j, self.cx
        Ny = j["N"][1]
        B.part(cast=False, recv=False)
        ln = max(0.075, B.px(2.4))
        gap = max(0.026, B.px(1.5))
        for sx in (-1.0, 1.0):
            root = np.array((cx + sx * gap, Ny - 0.050))
            tip = root + np.array((0.25 * self.lag * 0.1, -ln))
            B.stroke(np.array([root, tip]), "acc", 1.0 if not self.big else 2.0)

    def collar(self):
        return

    # ---- head ------------------------------------------------------------------------------
    def head(self):
        B, j, pr = self.B, self.j, self.pr
        Hc = j["Hc"]
        R = pr.head
        HL = lambda loc: F.frame_pts(Hc, np.array((1.0, 0.0)), np.array((0.0, 1.0)), np.asarray(loc, float), R)  # noqa: E731
        child, back, lag = self.child, self.back, self.lag
        B.part(cast=True)
        if child:
            mass = F._tuft_outline(F._TUFTS_CF, 1.34, lag, self.fl, 0.0, 0.04)
        else:
            mass = F._bob_outline(True, lag)
        mass_path = B.formed(HL(mass), "hair", "hair_sh", "hair_lt" if not child else None, d=self.d(3),
                             dl=self.d(2), details=self._hair_lights_front(HL, back), smooth_=not child)
        if child and self.mid:
            B.part(cast=True)
            B.stroke(HL(np.array([(0.04, 1.14), (0.10, 1.40), (0.0, 1.56), (-0.18, 1.54)])), "hair",
                     1.0 if not self.big else 2.0)
        if self.mid:
            for sx in (-1.0, 1.0):
                B.part(cast=True, recv=False)
                B.fill(HL(F.D_ellipse((sx * 0.98, -0.20), (1, 0), 0.16, 0.21)), "skin" if not back else "skin_sh")
        if back:
            B.part(cast=True)
            inner = mass * np.array((0.97, 0.98)) + np.array((0.0, -0.02))
            B.fill(HL(inner), "hair", smooth_=not child)
            B.clip(B.path(HL(inner), not child), self._hair_lights_front(HL, True))
            if not child and self.k:
                self._clip_rose(HL, (0.66, 0.50))
            return
        self.face_part = B.part(cast=True, recv=False)
        B.formed(HL(F._FACE_F), "skin", "skin_sh" if self.big else None, None, d=self.d(2))
        B.part(cast=False, recv=False)
        if child:
            B.formed(HL(F._fringe(True, True, 1.0, R * B.s, lag)), "hair", "hair_sh", None, d=self.d(2), smooth_=False,
                     details=self._hair_lights_front(HL, False, fringe=True))
            B.clip_last(mass_path)
        else:
            B.formed(HL(F._fringe(False, True, 1.0, R * B.s, lag)), "hair", "hair_sh", "hair_lt", d=self.d(2), dl=self.d(1), smooth_=False)
            B.clip_last(mass_path)
            if self.k:
                self._clip_rose(HL, (-0.58, 0.52))
        # features: a bowed head lowers them, a lifted one raises them
        sh = -0.30 * max(-1.0, min(1.0, self.pitch))
        self._stamp_face(Hc + np.array((0.0, sh * R)), np.array((1.0, 0.0)), np.array((0.0, 1.0)), R, 1.0, front=True)

    def _hair_lights_front(self, HL, back, fringe=False):
        B = self.B
        out = []
        if not self.mid:
            return out
        lsx = -1.0 if B.L[0] * B.f < 0 else 1.0
        if self.child:
            if fringe:
                return F._hair_clusters(B, HL, lsx, True, self.big)
            out += F._hair_clusters(B, HL, lsx, False, self.big)
        else:
            band = [(math.sin(math.radians(a)) * r, 0.06 + math.cos(math.radians(a)) * r)
                    for a, r in ((-62, 1.00), (-25, 1.06), (25, 1.06), (62, 1.00), (55, 0.86), (20, 0.92),
                                 (-20, 0.92), (-55, 0.86))]
            out.append(("f", B.path(HL(np.array(band))), B.code("hair_lt")))
        return out

    # ---- arms ------------------------------------------------------------------------------
    def arm(self, side, *a):
        super().arm(side)

    def backpack(self, behind: bool):
        B, j, cx = self.B, self.j, self.cx
        Py, Ny = j["P"][1], j["N"][1]
        if behind:
            B.part(cast=True)
            w = self.sw * (0.95 if self.back else 1.12)
            pts = np.array([(cx - w, Ny - 0.04), (cx + w, Ny - 0.04), (cx + w * 1.02, Py + 0.05), (cx - w * 1.02, Py + 0.05)])
            det = []
            if self.back and self.mid:
                det.append(("f", B.path(np.array([(cx - w * 0.6, Py + 0.16), (cx + w * 0.6, Py + 0.16),
                                                  (cx + w * 0.6, Py + 0.07), (cx - w * 0.6, Py + 0.07)]), False),
                            B.code("p_pack_sh")))
            B.formed(pts, "p_pack", "p_pack_sh", "p_pack_lt", d=self.d(3), dl=self.d(1), details=det)
        else:
            B.part(cast=False, recv=False)
            w = max(1.0, 0.020 * B.s)
            for sx in (-1.0, 1.0):
                a = np.array((cx + sx * self.sw * 0.55, Ny - 0.02))
                b = np.array((cx + sx * self.sw * 0.62, Ny - 0.16))
                B.stroke(np.array([a, b]), "p_strap", w)

    # ---- assembly --------------------------------------------------------------------------
    def build(self, cushion=False, phone=None, tray=False, backpack=False):
        p = self.p
        if backpack and not self.back:
            self.backpack(True)
        if self.mode == "stand":
            self.leg("f")
            self.leg("n")
        self.torso()
        if backpack and self.back:
            self.backpack(True)
        if self.mode != "stand":
            self.leg("f")
            self.leg("n")
        arms_over_head = p.arm_front >= 0.5
        if not arms_over_head:
            if self.back:
                self.arm("n")
                self.arm("f")
            else:
                self.arm("f")
                self.arm("n")
        hug = cushion and self._knees_up()
        if cushion and not hug:
            self.cushion()
        if tray:
            self.tray()
        if phone and not arms_over_head:
            self.phone(phone)
            self._hands_over_phone()
        self.strings()
        if backpack:
            self.backpack(False)
        self.head()
        if hug:
            self.cushion()
            # both arms round the cushion, the hands meeting on its lower front
            j, cx = self.j, self.cx
            c = F._cushion_centre(j, self.pr)
            for side, sx in (("f", -1.0), ("n", 1.0)):
                j["E_" + side] = np.array((cx + sx * (self.sw + 0.012), c[1] + 0.005))
                j["W_" + side] = np.array((cx + sx * 0.050, c[1] - 0.040))
                v = j["W_" + side] - j["E_" + side]
                j["fore_" + side] = math.atan2(v[0], -v[1])
                self.arm(side)
        if arms_over_head:
            if phone:
                self.phone(phone)
            self.arm("f")
            self.arm("n")

    def _hands_over_phone(self):
        j = self.j
        for side in ("n", "f"):
            W = j["W_" + side]
            tdir = (W - j["E_" + side]) / (np.linalg.norm(W - j["E_" + side]) + 1e-9)
            self.hand(W + tdir * 0.004, tdir, 0.0, 0.6, side == "n")
