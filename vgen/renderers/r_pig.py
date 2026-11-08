"""4. Свиная война 1859. Морская карта: сетка, флаги, корабли."""
import math

import skia

from vgen.reels import base as B
from vgen.kit import W, H, lin

SEA = "#153a4a"
SEA_D = "#0d2836"
SAND = "#d8c49c"
INK = "#16232a"
US = "#2f5d9e"
UK = "#a8323a"


def _map(cv, t):
    cv.clear(SEA)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#183f50"), (0.5, "#123646"), (1, "#0c2836")]))
    for x in range(0, W, 90):
        cv.line(x, 0, x, H, "#ffffff", 1, alpha=0.06)
    for y in range(0, H, 90):
        cv.line(0, y, W, y, "#ffffff", 1, alpha=0.06)
    # береговые линии
    cv.poly([(-20, 300), (240, 260), (420, 380), (470, 620), (360, 860), (120, 900), (-20, 820)],
            fill=SAND, alpha=0.95)
    cv.poly([(760, 900), (980, 840), (1100, 980), (1080, 1300), (860, 1420), (700, 1280)],
            fill=SAND, alpha=0.9)
    # остров
    cv.poly([(400, 1080), (520, 1010), (660, 1060), (700, 1180), (600, 1280), (450, 1250)],
            fill="#c9b389", stroke="#7c6642", width=4)
    for i in range(4):
        cv.circle(480 + i * 50, 1140 + (i % 2) * 40, 12, fill="#7c6642", alpha=0.35)


def _flag(cv, x, y, col, w=70, h=44, alpha=1.0, wave=0.0):
    cv.line(x, y, x, y - 130, "#e8dcc0", 4, alpha=alpha)
    p = skia.Path()
    p.moveTo(x, y - 130)
    for i in range(9):
        p.lineTo(x + w * (i + 1) / 8, y - 130 + 4 * math.sin(i + wave))
    p.lineTo(x + w, y - 130 + h)
    for i in range(9):
        p.lineTo(x + w * (8 - i) / 8, y - 130 + h + 4 * math.sin(8 - i + wave))
    p.close()
    cv.path(p, fill=col, alpha=alpha)


def _boat(cv, x, y, s=1.0, col="#22303a", alpha=1.0):
    cv.poly([(x - 60 * s, y - 14 * s), (x + 60 * s, y - 14 * s), (x + 44 * s, y + 12 * s),
             (x - 44 * s, y + 12 * s)], fill=col, alpha=alpha)
    cv.rect(x - 26 * s, y - 52 * s, x + 6 * s, y - 14 * s, fill=col, alpha=alpha)
    cv.line(x - 30 * s, y - 60 * s, x - 30 * s, y - 14 * s, col, 3 * s, alpha=alpha)


def _pig(cv, x, y, s=1.0, alpha=1.0, col="#b57f74"):
    B.ellipse(cv, x, y - 30 * s, 46 * s, 30 * s, fill=col, alpha=alpha)
    cv.circle(x + 42 * s, y - 34 * s, 18 * s, fill=col, alpha=alpha)
    cv.circle(x + 58 * s, y - 34 * s, 8 * s, fill="#8c5a52", alpha=alpha)
    cv.circle(x + 60 * s, y - 36 * s, 2.5 * s, fill=INK, alpha=alpha)
    cv.circle(x + 46 * s, y - 44 * s, 3 * s, fill=INK, alpha=alpha)
    for dx in (-26, -8, 10, 26):
        cv.line(x + dx * s, y - 8 * s, x + dx * s, y + 12 * s, col, 7 * s, alpha=alpha)


def scene_hook(cv, t, ctx):
    k = B.kof(ctx, t, (0, 8))
    _map(cv, t)
    _flag(cv, 470, 1100, US, 70, 44, 1.0, t)
    _flag(cv, 620, 1120, UK, 70, 44, 1.0, t + 2)
    _pig(cv, 540, 1180, 1.0)
    if k > 0.04:
        a = B.ease((k - 0.04) / 0.2)
        B.text(cv, "ОСТРОВ САН-ХУАН · 1859", 210, 32, "#f0e2bf", a)
        B.big_number(cv, "ВОЙНА", 330, 130, "#ffffff", (US, 14), a, "#0a1820", 8)
        B.text(cv, "ИЗ-ЗА ОДНОЙ СВИНЬИ", 400, 40, "#ffd08a", a)
    B.grain(cv, 6, 6, 0.18)


def scene_shot(cv, t, ctx):
    k = B.kof(ctx, t, (8, 16))
    _map(cv, t)
    # фермер и огород
    cv.rect(120, 1080, 520, 1400, fill="#8a6f45", stroke=INK, width=3)
    for i in range(4):
        cv.line(150, 1140 + i * 60, 490, 1140 + i * 60, "#5c4a30", 3, alpha=0.6)
        for j in range(6):
            cv.circle(170 + j * 60, 1130 + i * 60, 9, fill="#6f8c4a", alpha=0.8)
    _pig(cv, 380, 1160, 0.9)
    B.person(cv, 620, 1200, 1.3, "#2b3a4a", "#e8c9a0")
    cv.line(650, 1140, 730, 1100, "#2b2418", 7)
    if k > 0.25:
        a = B.ease((k - 0.25) / 0.3)
        for i in range(6):
            cv.circle(740 + i * 26, 1090 - i * 8, 4, fill="#ffd08a", alpha=a * (0.8 - i * 0.1))
        B.text(cv, "ФЕРМЕР ЗАСТРЕЛИЛ СВИНЬЮ", 250, 34, "#ffe9c9", a)
    if k > 0.6:
        B.text(cv, "СВИНЬЯ БЫЛА БРИТАНСКОЙ", 320, 30, "#ff9a7a", B.ease((k - 0.6) / 0.3))
    B.grain(cv, 6, 14, 0.18)


def scene_standoff(cv, t, ctx):
    k = B.kof(ctx, t, (16, 25))
    _map(cv, t)
    # солдаты США слева, британцы справа
    for i in range(4):
        B.person(cv, 150 + i * 60, 1180, 0.9, US, "#e8c9a0")
        B.person(cv, 780 + i * 60, 1180, 0.9, UK, "#e8c9a0")
    # корабли на воде
    _boat(cv, 260, 820, 1.4, "#1b2a33")
    _boat(cv, 760, 780, 1.5, "#2a2118")
    _flag(cv, 210, 800, US, 56, 36, 0.95, t)
    _flag(cv, 710, 760, UK, 56, 36, 0.95, t + 1.5)
    # линия противостояния
    cv.line(540, 700, 540, 1300, "#ffd08a", 3, alpha=0.5)
    if k > 0.1:
        a = B.ease((k - 0.1) / 0.25)
        B.text(cv, "США ПРИСЛАЛИ СОЛДАТ", 240, 32, "#f0e2bf", a)
        B.text(cv, "БРИТАНИЯ — КОРАБЛИ", 300, 32, "#ffd08a", a)
    B.grain(cv, 6, 22, 0.18)


def scene_final(cv, t, ctx):
    k = B.kof(ctx, t, (25, 33))
    _map(cv, t)
    if k > 0.05:
        a = B.ease((k - 0.05) / 0.25)
        B.big_number(cv, "12", 560, 300, "#ffffff", (US, 10), a, "#0a1820", 8)
        B.text(cv, "ЛЕТ СОВМЕСТНОЙ ОККУПАЦИИ", 640, 36, "#f0e2bf", a)
    if k > 0.5:
        a = B.ease((k - 0.5) / 0.3)
        _pig(cv, 540, 1180, 1.0, a)
        B.text(cv, "ЕДИНСТВЕННАЯ ЖЕРТВА — СВИНЬЯ", 1300, 34, "#ffd08a", a)
    B.grain(cv, 6, 30, 0.18)


SCENES = {"hook": scene_hook, "shot": scene_shot, "standoff": scene_standoff, "final": scene_final}


def render(name, t, ctx=None, finish=False):
    return B.render(name, t, ctx, SCENES)
