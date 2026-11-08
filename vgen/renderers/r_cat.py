"""1. ЦРУ и кошка-шпион. Нуар, военная оптика, зелёный фосфор."""
import math

import skia

from vgen.kit import W, H, lin, rgba
from vgen.reels import base as B

BG = "#070b09"
GREEN = "#b6f26a"
GREEN_D = "#4f7a2e"
AMBER = "#ffb347"
PAPER = "#e6f0d2"
INK = "#05080a"


def _cat(cv, x, y, s=1.0, col="#0d1410", rim=GREEN, t=0.0, alpha=1.0):
    # тело
    body = skia.Path()
    body.moveTo(x - 120 * s, y)
    body.cubicTo(x - 120 * s, y - 70 * s, x + 20 * s, y - 80 * s, x + 80 * s, y - 40 * s)
    body.cubicTo(x + 110 * s, y - 20 * s, x + 100 * s, y + 10 * s, x + 60 * s, y + 12 * s)
    body.lineTo(x - 100 * s, y + 12 * s)
    body.close()
    cv.path(body, fill=col, alpha=alpha)
    cv.c.drawPath(body, B.sp(rim, 3, 170 * alpha))
    # голова
    hx, hy = x + 96 * s, y - 46 * s
    cv.circle(hx, hy, 34 * s, fill=col, alpha=alpha)
    cv.poly([(hx - 26 * s, hy - 18 * s), (hx - 20 * s, hy - 52 * s), (hx - 2 * s, hy - 26 * s)],
            fill=col, alpha=alpha)
    cv.poly([(hx + 26 * s, hy - 18 * s), (hx + 20 * s, hy - 52 * s), (hx + 2 * s, hy - 26 * s)],
            fill=col, alpha=alpha)
    # глаза
    cv.circle(hx + 10 * s, hy - 4 * s, 4.5 * s, fill=GREEN, alpha=alpha)
    cv.circle(hx + 22 * s, hy - 4 * s, 4.5 * s, fill=GREEN, alpha=alpha)
    # хвост
    p = skia.Path()
    p.moveTo(x - 118 * s, y + 2 * s)
    p.cubicTo(x - 190 * s, y - 30 * s, x - 170 * s, y - 110 * s, x - 120 * s, y - 96 * s)
    cv.c.drawPath(p, B.sp(col, 14 * s, 255 * alpha))
    cv.c.drawPath(p, B.sp(rim, 3, 130 * alpha))


def _antenna(cv, x, y, t, s=1.0, alpha=1.0):
    cv.line(x, y, x + 46 * s, y - 74 * s, "#8a9a6a", 3, alpha=alpha)
    cv.circle(x + 46 * s, y - 74 * s, 7, fill=GREEN, alpha=alpha * (0.7 + 0.3 * math.sin(t * 6)))
    cv.circle(x + 46 * s, y - 74 * s, 22, fill=GREEN, alpha=0.10 * alpha, blur=14)


def scene_hook(cv, t, ctx):
    k = B.kof(ctx, t, (0, 8))
    cv.clear(BG)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#050907"), (0.6, "#0a120d"), (1, "#03060a")]))
    # крыши
    for i in range(6):
        x = -40 + i * 210
        cv.rect(x, 980 + (i % 3) * 40, x + 190, 1500, fill="#0a1210")
        cv.rect(x + 40, 1010 + (i % 3) * 40, x + 80, 1060, fill=AMBER, alpha=0.10)
    B.rays(cv, 300, 300, t, 12, GREEN, 0.04)
    B.dust(cv, t, 26, GREEN, 0.18)
    _cat(cv, 380, 980, 1.2, "#18241c", "#d6ff9e", t)
    _antenna(cv, 500, 910, t, 1.2)
    if k > 0.04:
        a = B.ease((k - 0.04) / 0.2)
        B.text(cv, "АГЕНТ 1960-х", 210, 34, GREEN_D, a)
        B.big_number(cv, "КОШКА-ШПИОН", 330, 84, PAPER, (GREEN, 18), a)
        B.text(cv, "МИКРОФОН · ПЕРЕДАТЧИК · АНТЕННА", 400, 26, GREEN, a * 0.9)
    B.grain(cv, 12, 3, 0.5)
    B.scanlines(cv, 5, 0.10)
    cv.rrect(0, 0, W, H, 0, fill="#000000", alpha=0.0)


def scene_xray(cv, t, ctx):
    k = B.kof(ctx, t, (8, 16))
    cv.clear("#04070a")
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#061015"), (0.5, "#0a1a18"), (1, "#04070a")]))
    cv.rect(90, 140, 990, 1500, fill="#06120f", stroke=GREEN_D, width=3)
    cv.text("РЕНТГЕН", 130, 200, 26, fill=GREEN_D)
    _cat(cv, 330, 900, 1.9, "#0a1613", GREEN, t, alpha=0.9)
    # устройства
    for i, (dx, dy, rr) in enumerate([(600, 780, 16), (700, 800, 12), (760, 700, 10)]):
        cv.circle(dx, dy, rr, fill="#0c1a16", stroke=GREEN, width=2)
        cv.circle(dx, dy, rr * 0.45, fill=GREEN, alpha=0.7)
        cv.text(["МИКРОФОН", "ПЕРЕДАТЧИК", "АНТЕННА"][i], 130, 1180 + i * 70, 26, fill=GREEN,
                alpha=0.85)
    cv.line(760, 700, 780, 610, "#8a9a6a", 3)
    B.scanlines(cv, 4, 0.14)
    B.grain(cv, 8, 11, 0.4)
    if k > 0.1:
        B.text(cv, "ТЕХНИКА РАБОТАЛА", 1500, 34, GREEN, B.ease((k - 0.1) / 0.3) * 0.9)


def scene_walk(cv, t, ctx):
    k = B.kof(ctx, t, (16, 25))
    cv.clear(BG)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#060b09"), (1, "#0b0f0c")]))
    # улица и фургон наблюдения
    cv.rect(0, 1200, W, H, fill="#0a100d")
    for i in range(9):
        cv.line(0, 1240 + i * 40, W, 1240 + i * 40, "#131c17", 2)
    cv.rrect(640, 1010, 940, 1200, 16, fill="#111a15", stroke=GREEN_D, width=2)
    cv.rect(670, 1040, 760, 1100, fill=GREEN, alpha=0.13)
    B.text(cv, "НАБЛЮДЕНИЕ", 790, 1240, 22, GREEN_D)
    # кошка уходит вправо
    cx = 300 + 260 * B.ease(k)
    _cat(cv, cx, 1200, 1.0, "#0c130f", GREEN, t)
    _antenna(cv, cx + 120, 1130, t, 1.0)
    for i in range(2):
        B.person(cv, 700 + i * 60, 1300, 0.9, "#1b2620")
    B.dust(cv, t, 18, GREEN, 0.12)
    if k > 0.1:
        a = B.ease((k - 0.1) / 0.25)
        B.text(cv, "ОНА ШЛА КУДА ХОТЕЛА", 260, 62, PAPER, a)
        B.text(cv, "ОПЕРАТОРЫ БЫЛИ БЕССИЛЬНЫ", 330, 28, GREEN, a * 0.9)
    B.grain(cv, 10, 21, 0.45)


def scene_final(cv, t, ctx):
    k = B.kof(ctx, t, (25, 32))
    cv.clear("#060a08")
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#070d0b"), (1, "#0b1410")]))
    B.rays(cv, 540, 700, t, 10, GREEN, 0.03)
    _cat(cv, 400, 1100, 1.3, "#18241c", "#d6ff9e", t, alpha=0.95)
    # штамп
    if k > 0.25:
        a = B.ease((k - 0.25) / 0.3)
        cv.save()
        cv.c.rotate(-8, 540, 700)
        cv.rrect(240, 600, 840, 800, 14, stroke="#e8604c", width=8, alpha=a)
        cv.text("ПРОЕКТ ЗАКРЫТ", 540, 700, 62, fill="#e8604c", center=True, alpha=a)
        cv.text("1967", 540, 770, 44, fill="#e8604c", center=True, alpha=a)
        cv.restore()
    if k > 0.05:
        B.text(cv, "СЛИШКОМ НЕЗАВИСИМА", 1240, 44, PAPER, B.ease((k - 0.05) / 0.2))
        B.text(cv, "ДАЖЕ ДЛЯ ЦРУ", 1310, 30, GREEN, B.ease((k - 0.05) / 0.2) * 0.9)
    B.grain(cv, 12, 31, 0.5)
    B.scanlines(cv, 5, 0.08)


SCENES = {"hook": scene_hook, "xray": scene_xray, "walk": scene_walk, "final": scene_final}


def render(name, t, ctx=None, finish=False):
    return B.render(name, t, ctx, SCENES)
