"""3. Великая война с эму, 1932. Киножурнал: сепия, зерно, перфорация."""
import math
import random

import skia

from vgen.reels import base as B
from vgen.kit import W, H, lin

BG = "#d9c8a4"
BG_D = "#c2ad84"
INK = "#2a2118"
KHAKI = "#6e5c3c"
RED = "#8c2f1e"


def _film(cv, t, flicker=True):
    cv.clear(BG)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#e2d3b1"), (0.5, "#d5c29c"), (1, "#c0aa80")]))
    rnd = random.Random(8)
    for _ in range(50):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        cv.circle(x, y, rnd.randint(30, 120), fill="#8a6f45", alpha=0.03)
    # перфорация
    for y in range(30, H, 74):
        for x in (16, W - 44):
            cv.rrect(x, y, x + 28, y + 40, 6, fill="#f3e8cc", stroke="#9c8560", width=2)
    if flicker:
        cv.rect(0, 0, W, H, fill="#3a2c18", alpha=0.05 + 0.03 * math.sin(t * 14))
    # царапины
    for i in range(3):
        x = (i * 397 + t * 22) % W
        cv.line(x, 0, x + 6, H, "#ffffff", 1, alpha=0.18)


def _emu(cv, x, y, s=1.0, alpha=1.0, run=0.0, phase=0.0, col="#3a3024"):
    leg = 26 * s * math.sin(run * 6 + phase)
    # тело
    B.ellipse(cv, x, y - 92 * s, 62 * s, 46 * s, fill=col, alpha=alpha)
    # шея и голова
    p = skia.Path()
    p.moveTo(x - 40 * s, y - 118 * s)
    p.cubicTo(x - 66 * s, y - 180 * s, x - 58 * s, y - 236 * s, x - 30 * s, y - 250 * s)
    cv.c.drawPath(p, B.sp(col, 16 * s, 255 * alpha))
    cv.circle(x - 26 * s, y - 258 * s, 14 * s, fill=col, alpha=alpha)
    cv.poly([(x - 16 * s, y - 262 * s), (x + 6 * s, y - 256 * s), (x - 16 * s, y - 248 * s)],
            fill="#c9a24a", alpha=alpha)
    cv.circle(x - 32 * s, y - 262 * s, 3 * s, fill="#f2e6c9", alpha=alpha)
    # хвост
    for i in range(4):
        cv.line(x + 50 * s, y - 104 * s, x + 86 * s - i * 6 * s, y - 122 * s + i * 12 * s, col,
                5 * s, alpha=alpha * 0.8)
    # ноги
    cv.line(x - 10 * s, y - 60 * s, x - 10 * s + leg, y, col, 8 * s, alpha=alpha)
    cv.line(x + 16 * s, y - 60 * s, x + 16 * s - leg, y, col, 8 * s, alpha=alpha)


def _soldier(cv, x, y, s=1.0, alpha=1.0):
    B.person(cv, x, y, s, "#4c4030", "#e2c16a", alpha)
    # винтовка/пулемёт
    cv.line(x + 10 * s, y - 60 * s, x + 96 * s, y - 96 * s, "#2b2418", 8 * s, alpha=alpha)
    cv.circle(x + 100 * s, y - 98 * s, 6 * s, fill="#2b2418", alpha=alpha)


def scene_hook(cv, t, ctx):
    k = B.kof(ctx, t, (0, 8))
    _film(cv, t)
    # поле
    cv.rect(0, 1180, W, H, fill=BG_D)
    for i in range(12):
        cv.line(0, 1190 + i * 26, W, 1190 + i * 26, "#a58c60", 2, alpha=0.5)
    _soldier(cv, 300, 1180, 1.4)
    _soldier(cv, 430, 1180, 1.3)
    for i in range(3):
        _emu(cv, 640 + i * 90, 1180, 0.7, 1.0, t + i)
    if k > 0.04:
        a = B.ease((k - 0.04) / 0.2)
        B.text(cv, "ЗАПАДНАЯ АВСТРАЛИЯ · 1932", 210, 30, "#5c4a30", a)
        B.big_number(cv, "ВОЙНА С ЭМУ", 340, 96, INK, None, a, "#3a2c18", 6)
        B.text(cv, "АРМИЯ ПРОТИВ ПТИЦ", 410, 34, RED, a)
    B.grain(cv, 10, 4, 0.35)
    B.scanlines(cv, 4, 0.06)


def scene_scatter(cv, t, ctx):
    k = B.kof(ctx, t, (8, 16))
    _film(cv, t)
    cv.rect(0, 1100, W, H, fill=BG_D)
    # стая разбегается
    for i in range(9):
        dx = 60 + i * 110
        dy = 1100 + (i % 3) * 40
        run = t * 1.4 + i
        _emu(cv, dx + 40 * math.sin(run * 0.6), dy, 0.55 + 0.1 * (i % 3), 1.0, run, i)
    _soldier(cv, 200, 1360, 1.2)
    for i in range(5):
        cv.circle(260 + i * 40, 1180 + i * 26, 4, fill="#2b2418", alpha=0.4 + 0.3 * math.sin(t * 9 + i))
    if k > 0.08:
        a = B.ease((k - 0.08) / 0.25)
        B.text(cv, "ОНИ РАЗБЕГАЛИСЬ И МЕНЯЛИ НАПРАВЛЕНИЕ", 250, 32, INK, a)
    B.grain(cv, 10, 12, 0.35)


def scene_tally(cv, t, ctx):
    k = B.kof(ctx, t, (16, 24))
    _film(cv, t)
    cv.rect(0, 900, W, H, fill="#cdb994")
    if k > 0.08:
        a = B.ease((k - 0.08) / 0.3)
        B.text(cv, "ИТОГ КАМПАНИИ", 300, 40, "#5c4a30", a)
        B.big_number(cv, "< 1000", 640, 220, RED, (RED, 10), a, "3a2c18", 6)
        B.text(cv, "УНИЧТОЖЕННЫХ ЭМУ", 720, 36, INK, a)
    # штамп "ПРОВАЛ"
    if k > 0.55:
        a = B.ease((k - 0.55) / 0.3)
        cv.save()
        cv.c.rotate(-6, 540, 1160)
        cv.rrect(200, 1050, 880, 1260, 12, stroke=RED, width=8, alpha=a)
        cv.text("ПРОВАЛ", 540, 1190, 110, fill=RED, center=True, alpha=a)
        cv.restore()
    B.grain(cv, 9, 18, 0.33)


def scene_final(cv, t, ctx):
    k = B.kof(ctx, t, (24, 31))
    cv.clear("#2a2118")
    # газетная страница
    cv.rect(70, 170, 1010, 1700, fill="#e3d4b2", stroke="#8a7448", width=3)
    cv.rect(110, 210, 970, 330, fill="#2a2118")
    cv.text("THE EMU WAR", 540, 300, 62, fill="#e3d4b2", center=True)
    for i in range(4):
        cv.rect(120, 380 + i * 60, 950, 396 + i * 60, fill="#5c4a30", alpha=0.5)
    _emu(cv, 400, 1000, 1.1, 1.0, t, 0)
    _soldier(cv, 720, 1000, 1.0)
    cv.rect(120, 1120, 950, 1560, fill="#cfbd98", stroke="#8a7448", width=2)
    for i in range(6):
        cv.rect(150, 1160 + i * 60, 920, 1176 + i * 60, fill="#5c4a30", alpha=0.35)
    B.text(cv, "ЕДИНСТВЕННАЯ ВОЙНА,", 1660, 42, "#e3d4b2", 1.0)
    B.text(cv, "ПРОИГРАННАЯ ПТИЦАМ", 1720, 42, "#e0a03c", 1.0)
    B.grain(cv, 8, 24, 0.2)


SCENES = {"hook": scene_hook, "scatter": scene_scatter, "tally": scene_tally, "final": scene_final}


def render(name, t, ctx=None, finish=False):
    return B.render(name, t, ctx, SCENES)
