"""5. Озеро Пеньер, 1980. Спутниковый вид сверху + разрез шахты."""
import math

import skia

from vgen.reels import base as B
from vgen.kit import W, H, lin

WATER = "#123c4a"
WATER_D = "#08222b"
LAND = "#33502f"
LAND_D = "#24391f"
SALT = "#e6dcc4"
RED = "#e0563f"
CREAM = "#fff6e8"


def _swamp(cv, t):
    cv.clear(LAND_D)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#2c4527"), (1, "#1c3018")]))
    # каналы и растительность
    for i in range(9):
        cv.line(0, 200 + i * 190, W, 160 + i * 190, "#4a6b3a", 8, alpha=0.35)
    for i in range(40):
        x = (i * 149) % W
        y = (i * 233) % H
        cv.circle(x, y, 6 + (i % 4) * 3, fill="#3f5c2f", alpha=0.5)
    # озеро
    B.ellipse(cv, 540, 900, 400, 330, fill=WATER, stroke="#0a2a33", width=6)
    B.ellipse(cv, 540, 880, 360, 290, fill=lin(0, 600, 0, 1200, [(0, "#1a5464"), (0.6, WATER), (1, WATER_D)]))


def scene_hook(cv, t, ctx):
    k = B.kof(ctx, t, (0, 8))
    _swamp(cv, t)
    # буровая платформа
    cv.rect(500, 860, 580, 960, fill=RED)
    cv.line(540, 860, 540, 700, "#d9cfae", 6)
    cv.poly([(540, 700), (620, 740), (540, 780)], fill="#d9cfae")
    B.spiral(cv, 540, 900, 0, 40, 240, 2.4, "#ffffff", 0.25, 4)
    if k > 0.04:
        a = B.ease((k - 0.04) / 0.2)
        B.text(cv, "ЛУИЗИАНА · 20 НОЯБРЯ 1980", 200, 30, "#d9e8c9", a)
        B.big_number(cv, "ОЗЕРО", 320, 120, CREAM, None, a, "#0a1c14", 8)
        B.text(cv, "УХОДИТ ПОД ЗЕМЛЮ", 390, 42, "#a8e6c9", a)
    B.grain(cv, 5, 5, 0.16)


def scene_drill(cv, t, ctx):
    k = B.kof(ctx, t, (8, 17))
    cv.clear("#08141a")
    # разрез: сверху озеро, ниже соляная шахта
    cv.rect(0, 0, W, 700, fill=lin(0, 0, 0, 700, [(0, "#0d2c36"), (1, "#0a2029")]))
    cv.rect(0, 300, W, 520, fill=WATER, alpha=0.9)
    cv.rect(0, 520, W, 700, fill="#2b2418")
    cv.rect(0, 700, W, 1500, fill=lin(0, 700, 0, 1500, [(0, "#3a3630"), (0.4, SALT), (1, "#b9ab8c")]))
    # шахта
    for i in range(3):
        cv.rect(120 + i * 300, 900, 380 + i * 300, 1180, fill="#0e1a18", alpha=0.65)
        cv.rect(120 + i * 300, 900, 380 + i * 300, 1180, stroke="#8a795a", width=3)
    # бур
    cv.line(540, 320, 540, 900 - 60 * k, "#d9cfae", 10)
    cv.poly([(540, 900 - 60 * k), (560, 860 - 60 * k), (520, 860 - 60 * k)], fill=RED)
    # вода рвётся вниз
    if k > 0.4:
        a = B.ease((k - 0.4) / 0.4)
        for i in range(9):
            cv.line(420 + i * 30, 520, 420 + i * 30 + 20 * math.sin(i), 900, WATER, 12,
                    alpha=0.85 * a)
        B.ellipse(cv, 540, 900, 90, 40, fill=WATER_D, alpha=a)
    if k > 0.1:
        a = B.ease((k - 0.1) / 0.25)
        B.text(cv, "БУР ПРОБИЛ ПОТОЛОК СОЛЯНОЙ ШАХТЫ", 180, 30, CREAM, a)
    B.grain(cv, 5, 13, 0.16)


def scene_whirl(cv, t, ctx):
    k = B.kof(ctx, t, (17, 26))
    _swamp(cv, t)
    B.spiral(cv, 540, 880, t, 60, 380 * (0.4 + 0.6 * k), 3.4, "#bfe6ff", 0.55, 8)
    B.spiral(cv, 540, 880, t * 1.4, 40, 200 * (0.3 + 0.7 * k), 3.0, "#ffffff", 0.4, 5)
    # воронка
    B.ellipse(cv, 540, 880, 200 * k, 160 * k, fill="#04161c", alpha=0.85)
    # баржи и платформа затягиваются
    for i, (bx, by) in enumerate([(300, 780), (790, 830), (420, 1010)]):
        s = 1 - 0.5 * k
        cv.save()
        cv.c.translate(bx, by)
        cv.c.rotate(k * (120 + i * 40))
        cv.rrect(-50 * s, -16 * s, 50 * s, 16 * s, 4, fill="#8a5f2c")
        cv.restore()
    # обратное течение
    if k > 0.45:
        a = B.ease((k - 0.45) / 0.3)
        for i in range(3):
            y = 1250 + i * 90
            cv.line(900, y, 300, y, "#a8e6c9", 5, alpha=a * 0.8)
            cv.poly([(300, y), (340, y - 16), (340, y + 16)], fill="#a8e6c9", alpha=a * 0.8)
        B.text(cv, "ТЕЧЕНИЕ РАЗВЕРНУЛОСЬ", 1560, 30, "#a8e6c9", a)
    if k > 0.08:
        B.text(cv, "ВОРОНКА ЗАТЯНУЛА ПЛАТФОРМУ, БАРЖИ, ДЕРЕВЬЯ", 230, 28, CREAM, B.ease((k - 0.08) / 0.25))
    B.grain(cv, 5, 21, 0.16)


def scene_final(cv, t, ctx):
    k = B.kof(ctx, t, (26, 33))
    _swamp(cv, t)
    B.ellipse(cv, 540, 880, 360, 290, fill=lin(0, 600, 0, 1200, [(0, "#2a7a8a"), (0.6, WATER), (1, WATER_D)]))
    if k > 0.05:
        a = B.ease((k - 0.05) / 0.25)
        B.text(cv, "НИКТО НЕ ПОГИБ", 520, 70, CREAM, a)
        B.text(cv, "ЧЕРЕЗ 2 ДНЯ ОЗЕРО НАПОЛНИЛОСЬ", 1340, 30, "#a8e6c9", a)
        B.text(cv, "ТЕПЕРЬ ОНО СОЛЁНОЕ И ГЛУБЖЕ", 1400, 30, "#ffd08a", a)
    B.grain(cv, 5, 29, 0.16)


SCENES = {"hook": scene_hook, "drill": scene_drill, "whirl": scene_whirl, "final": scene_final}


def render(name, t, ctx=None, finish=False):
    return B.render(name, t, ctx, SCENES)
