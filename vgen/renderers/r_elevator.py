"""7. Лифт Эмпайр-стейт, 1945. Разрез здания, 1940-е, красно-серый."""
import math

import skia

from vgen.reels import base as B
from vgen.kit import W, H, lin

NIGHT = "#101317"
STONE = "#3a3f45"
STONE_L = "#4c525a"
WARM = "#ffd9a0"
RED = "#e0503a"
CREAM = "#f2efe6"


def _building(cv, t, floors=22, top=360, bottom=1500):
    x0, x1 = 300, 780
    cv.rect(x0, top, x1, bottom, fill=STONE)
    # ступени
    for i in range(5):
        w = 40 - i * 6
        cv.rect(x0 + 20 + i * 10, top - 40 + i * 34, x1 - 20 - i * 10, top + 10, fill=STONE_L)
    cv.rect(520, top - 200, 560, top - 40, fill=STONE_L)
    cv.rect(500, top - 226, 580, top - 196, fill=STONE_L)
    # окна
    for f in range(floors):
        y = top + 40 + f * ((bottom - top - 60) / floors)
        for c in range(5):
            x = x0 + 30 + c * 88
            lit = math.sin(f * 1.7 + c * 2.3) > -0.2
            cv.rect(x, y, x + 54, y + 40, fill=WARM if lit else "#232830",
                    alpha=0.85 if lit else 0.9)
    # шахта лифта
    cv.rect(500, top + 60, 580, bottom, fill="#0a0d11", alpha=0.9)
    for i in range(floors):
        y = top + 60 + i * ((bottom - top - 60) / floors)
        cv.line(500, y, 580, y, "#2e343b", 2)


def _plane(cv, x, y, s=1.0, alpha=1.0):
    cv.poly([(x - 40 * s, y), (x + 40 * s, y - 6 * s), (x + 40 * s, y + 8 * s), (x - 40 * s, y + 10 * s)],
            fill="#8a9099", alpha=alpha)
    cv.poly([(x - 6 * s, y - 2 * s), (x + 26 * s, y - 2 * s), (x + 10 * s, y - 34 * s),
             (x - 16 * s, y - 34 * s)], fill="#8a9099", alpha=alpha)
    cv.poly([(x - 30 * s, y + 4 * s), (x - 10 * s, y + 4 * s), (x - 18 * s, y + 28 * s),
             (x - 34 * s, y + 28 * s)], fill="#8a9099", alpha=alpha)
    cv.circle(x - 34 * s, y + 2 * s, 5 * s, stroke="#e6dcc4", width=2, alpha=alpha)


def scene_hook(cv, t, ctx):
    k = B.kof(ctx, t, (0, 8))
    cv.clear(NIGHT)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#0b0e12"), (0.6, "#141a20"), (1, "#0a0c10")]))
    _building(cv, t)
    _plane(cv, 200 + 220 * B.ease(k) + 20 * math.sin(t * 3), 520, 1.2)
    if k > 0.04:
        a = B.ease((k - 0.04) / 0.2)
        B.text(cv, "НЬЮ-ЙОРК · 28 ИЮЛЯ 1945", 200, 28, "#c9d0d8", a)
        B.big_number(cv, "B-25", 300, 96, CREAM, (RED, 12), a, "#0a0c10", 6)
        B.text(cv, "ВРЕЗАЛСЯ В ЭМПАЙР-СТЕЙТ", 366, 32, "#ff9a7a", a)
    B.grain(cv, 9, 3, 0.3)


def scene_impact(cv, t, ctx):
    k = B.kof(ctx, t, (8, 15))
    cv.clear(NIGHT)
    _building(cv, t)
    _plane(cv, 640, 520, 1.3, 0.9)
    if k > 0.2:
        a = B.ease((k - 0.2) / 0.3)
        cv.circle(700, 540, 90 * a, fill="#ffd9a0", alpha=0.5 * a, blur=30)
        for i in range(10):
            cv.circle(700 + 120 * a * math.cos(i * 0.7), 540 + 120 * a * math.sin(i * 0.7),
                      10, fill="#ffb347", alpha=a * 0.8)
        B.text(cv, "УДАР ПРИШЁЛСЯ НА 79-Й ЭТАЖ", 220, 30, "#ffe9c9", a)
    if k > 0.55:
        B.text(cv, "БЕТТИ ЛУ ОЛИВЕР БЫЛА В ЛИФТЕ", 290, 30, CREAM, B.ease((k - 0.55) / 0.3))
    B.grain(cv, 9, 11, 0.3)


def scene_fall(cv, t, ctx):
    k = B.kof(ctx, t, (15, 23))
    cv.clear("#080a0d")
    # тёмная шахта
    cv.rect(200, 0, 880, H, fill="#0d1116")
    for y in range(0, H, 90):
        cv.line(200, y, 880, y, "#1c222a", 3)
    cv.line(260, 0, 260, H, "#2a323c", 4)
    cv.line(820, 0, 820, H, "#2a323c", 4)
    # кабина падает
    cy = 150 + 1100 * B.ease(k)
    cv.rrect(430, cy, 650, cy + 190, 8, fill="#3a424c", stroke="#8a9199", width=4)
    cv.rect(470, cy + 20, 610, cy + 90, fill="#1a1f26")
    # линии скорости
    for i in range(8):
        x = 280 + i * 72
        cv.line(x, cy - 260, x, cy - 60, "#ffffff", 2, alpha=0.18)
    if k > 0.15:
        a = B.ease((k - 0.15) / 0.3)
        B.text(cv, "ТРОСЫ ОБОРВАЛИСЬ", 120, 40, CREAM, a)
        B.text(cv, "≈300 МЕТРОВ ВНИЗ", 178, 30, "#ff9a7a", a)
    if k > 0.6:
        B.text(cv, "И ВЫЖИЛА", 1600, 44, "#ffd08a", B.ease((k - 0.6) / 0.3))
    B.grain(cv, 8, 19, 0.28)


def scene_final(cv, t, ctx):
    k = B.kof(ctx, t, (23, 30))
    cv.clear("#0b0d11")
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#101419"), (1, "#1a2129")]))
    _building(cv, t, 16, 420, 1500)
    if k > 0.05:
        a = B.ease((k - 0.05) / 0.25)
        B.big_number(cv, "75", 640, 230, CREAM, (RED, 10), a, "#0a0c10", 8)
        B.text(cv, "ЭТАЖЕЙ ПАДЕНИЯ", 710, 36, "#ffd08a", a)
        B.text(cv, "РЕКОРД, КОТОРЫЙ ПЕРЕЖИЛИ", 780, 26, "#c9d0d8", a)
    B.grain(cv, 9, 27, 0.3)


SCENES = {"hook": scene_hook, "impact": scene_impact, "fall": scene_fall, "final": scene_final}


def render(name, t, ctx=None, finish=False):
    return B.render(name, t, ctx, SCENES)
