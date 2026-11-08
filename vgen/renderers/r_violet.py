"""8. Вайолет Джессоп: три корабля, три катастрофы. Океан и лайнеры."""
import math

import skia

from vgen.reels import base as B
from vgen.kit import W, H, lin

SEA = "#0d2a3c"
SEA_L = "#1c4a63"
SKY = "#0a1620"
HULL = "#1b2836"
DECK = "#d9c8a4"
RED = "#c9453a"
CREAM = "#f0e6d2"


def _ocean(cv, t, sink=0.0):
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#08131c"), (0.4, SKY), (0.62, "#123246"), (1, "#06161f")]))
    for i in range(5):
        y = 1150 + i * 40
        p = skia.Path()
        for x in range(0, W + 20, 20):
            (p.moveTo if x == 0 else p.lineTo)(x, y + 4 * math.sin(x * 0.02 + t * 1.4 + i))
        cv.c.drawPath(p, B.sp("#7fb3c9", 2, 50))


def _liner(cv, x, y, s=1.0, sink=0.0, alpha=1.0, funnel=4):
    cv.save()
    cv.c.translate(x, y)
    cv.c.rotate(-18 * sink)
    w = 300 * s
    # корпус
    cv.poly([(-w, 0), (w, 0), (w * 0.86, 46 * s), (-w * 0.9, 54 * s)], fill=HULL, alpha=alpha)
    cv.poly([(-w * 0.98, 0), (w * 0.98, 0), (w * 0.94, 16 * s), (-w * 0.96, 18 * s)],
            fill=RED, alpha=alpha)
    # палубы
    for i in range(3):
        cv.rect(-w * (0.86 - i * 0.08), -46 * s - i * 34 * s, w * (0.82 - i * 0.12),
                -46 * s - i * 34 * s + 30 * s, fill=DECK, alpha=alpha * (0.95 - i * 0.1))
    # трубы
    for i in range(funnel):
        fx = -w * 0.5 + i * 74 * s
        cv.rect(fx, -160 * s, fx + 40 * s, -70 * s, fill="#b5482f", alpha=alpha)
        cv.rect(fx, -160 * s, fx + 40 * s, -150 * s, fill="#1a1a1a", alpha=alpha)
    # дым
    for i in range(3):
        cv.circle(-w * 0.4 + i * 40 * s, -200 * s - i * 26 * s, 24 * s, fill="#c9d6e4",
                  alpha=0.10 * alpha)
    cv.restore()


def scene_hook(cv, t, ctx):
    k = B.kof(ctx, t, (0, 8))
    _ocean(cv, t)
    _liner(cv, 540, 1180, 1.1, 0.0, 1.0, 4)
    if k > 0.04:
        a = B.ease((k - 0.04) / 0.2)
        B.text(cv, "ВАЙОЛЕТ ДЖЕССОП", 210, 30, "#9fc6d8", a)
        B.big_number(cv, "3 КОРАБЛЯ", 330, 96, CREAM, (RED, 12), a, "#06161f", 8)
        B.text(cv, "3 КАТАСТРОФЫ · 3 ВЫЖИВАНИЯ", 400, 32, "#ffd08a", a)
    B.grain(cv, 7, 4, 0.24)


def scene_olympic(cv, t, ctx):
    k = B.kof(ctx, t, (8, 15))
    _ocean(cv, t)
    _liner(cv, 420, 1150, 1.0, 0.0, 1.0, 4)
    # второй корабль таранит
    _liner(cv, 900, 1120, 0.6, 0.0, 0.9, 2)
    if k > 0.2:
        a = B.ease((k - 0.2) / 0.3)
        cv.circle(760, 1140, 60 * a, fill="#ffd9a0", alpha=0.35 * a, blur=24)
        B.text(cv, "1911 · «ОЛИМПИК» СТОЛКНОВЕНИЕ", 260, 34, CREAM, a)
    B.grain(cv, 7, 12, 0.24)


def scene_titanic(cv, t, ctx):
    k = B.kof(ctx, t, (15, 22))
    _ocean(cv, t)
    _liner(cv, 540, 1120, 1.1, sink=k, funnel=4)
    if k > 0.1:
        a = B.ease((k - 0.1) / 0.3)
        B.text(cv, "1912 · «ТИТАНИК»", 300, 44, CREAM, a)
        B.text(cv, "ОНА ВЫЖИЛА", 360, 30, "#ffd08a", a)
    B.grain(cv, 7, 18, 0.24)


def scene_britannic(cv, t, ctx):
    k = B.kof(ctx, t, (22, 30))
    _ocean(cv, t)
    _liner(cv, 480, 1100, 1.0, sink=0.6 * k, funnel=4)
    if k > 0.2:
        a = B.ease((k - 0.2) / 0.3)
        for i in range(8):
            cv.circle(300 + i * 70, 900 + (i % 3) * 40, 8, fill="#ffb347", alpha=a * 0.7)
        B.text(cv, "1916 · «БРИТАННИК» ПОДОРВАЛСЯ НА МИНЕ", 240, 28, CREAM, a)
    if k > 0.55:
        a = B.ease((k - 0.55) / 0.3)
        cv.rrect(150, 1330, 930, 1600, 20, fill="#0b1c26", stroke="#ffd08a", width=3, alpha=a)
        B.text(cv, "МИСС НЕПОТОПЛЯЕМАЯ", 540, 1450, 46, "#ffd08a", a)
        B.text(cv, "ТРИ КОРАБЛЯ · НИ ОДНОГО ШАНСА", 540, 1520, 24, "#cfe0ea", a)
    B.grain(cv, 7, 25, 0.24)


SCENES = {"hook": scene_hook, "olympic": scene_olympic, "titanic": scene_titanic,
          "britannic": scene_britannic}


def render(name, t, ctx=None, finish=False):
    return B.render(name, t, ctx, SCENES)
