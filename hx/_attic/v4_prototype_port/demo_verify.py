# Verification scene, written from hx/chalk/README.md alone (evidence: hx/_review/v4_core/verify/).
# A shelter of six strokes draws on a stroke a beat, the child trudges in under its scribble and
# stops, the friend waits, it rains (100-107.3); nothing moves but the boil (107.5-117.5: the stretch
# the flicker is measured on); the camera pushes in and pulls back (118-123); the shelter is taken
# away a stroke a beat (from 123). A stand-in: a real scene with an overlapping SPAN wins over it.
from hx.chalk import *

SPAN = (100.0, 128.0)

GY = 760.0                     # the ground
X0, X1 = 250.0, 840.0          # the child's walk
T_WALK = 100.0                 # first step
H = 300.0                      # the child's height (this module's own H; the kit's frame height is not used here)


def shelter():
    col, w = C.CHALK_COOL, 4.6
    return Sketch([
        Stroke(A((1010, GY), (1012, 392)), col, w, 0.95, seed=31, name="post_l"),
        Stroke(A((1500, GY), (1497, 400)), col, w, 0.95, seed=32, name="post_r"),
        Stroke(A((950, 404), (1255, 330), (1560, 410)), col, w + 0.6, 0.95, seed=33, name="roof"),
        Stroke(A((1090, 640), (1420, 638)), col, w, 0.95, seed=34, name="bench"),
        Stroke(A((1120, 640), (1118, GY)), C.CHALK_DIM, w - 0.8, 0.9, seed=35, name="leg_l"),
        Stroke(A((1392, 639), (1394, GY)), C.CHALK_DIM, w - 0.8, 0.9, seed=36, name="leg_r"),
    ], name="shelter")


def draw(F):
    close = Cam.at(X1 + 60, GY - 190, 1.6)
    if F.t < 120.5:
        F.cam = Cam.ease(Cam(), close, F.seg(118.0, 120.0))          # push in on the two
    else:
        F.cam = Cam.ease(close, Cam(), F.seg(121.0, 123.0))          # and pull back

    with F.depth(0.4):                                   # a far ridge: moves less than the set
        chalk(F, spline(A((-600, 640), (200, 600), (700, 650), (1300, 590), (1900, 640), (2600, 610)), 60),
              C.CHALK_FAR, 3.4, 0.7, seed=21)

    chalk(F, A((-1400, GY), (3300, GY)), C.CHALK_COOL, 4.2, 0.9, seed=20, taper=1.0)

    S = shelter()
    S.on_beats(F.tl, 100.0)
    S.off_beats(F.tl, 123.0)
    S.draw(F)

    fx = 1255.0
    glow(F, fx, GY - 150, 260, 250, a=0.16)
    ground_shadow(F, fx, GY + 4, 100, 0.6)
    figure(F, fx, GY, 290, STAND, "friend", -1, seed=5)

    W = walk_to(F.t, X0, X1, H, start=T_WALK)             # the trudge in, feet planted, to a stop at X1
    ground_shadow(F, W.x + 10, GY + 4, 110, 0.7)
    J = figure(F, W.x, GY, H, W.pose, "child", W.face, seed=3)
    gloom(F, J["head"][0] - 40, J["head"][1] - 205, 300, 100, seed=4, loops=30)

    with F.screen():
        rain(F, 0, 0, 1920, 1080, n=160, a=0.4, seed=7)
