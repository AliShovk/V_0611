"""2. Танцующая чума 1518. Гравюра на пергаменте, чернила, штриховка."""
import math
import random

import skia

from vgen.reels import base as B
from vgen.kit import W, H, lin

PAPER = "#e7d9b8"
PAPER_D = "#d3c09a"
INK = "#2b1d12"
RED = "#8d2f1d"


def _paper(cv, t):
    cv.clear(PAPER)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#efe3c6"), (0.5, "#e5d5b2"), (1, "#d8c49c")]))
    rnd = random.Random(4)
    for _ in range(70):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        cv.circle(x, y, rnd.randint(20, 90), fill="#b79f78", alpha=0.035)
    # пятна времени
    for i in range(8):
        x, y = (i * 173) % W, (i * 311) % H
        cv.circle(x, y, 40 + i * 6, fill="#8a6b45", alpha=0.04)


def _hatch(cv, x0, y0, x1, y1, step=9, alpha=0.25):
    n = int((x1 - x0 + y1 - y0) / step)
    for i in range(n):
        cv.line(x0 + i * step, y1, x0 + i * step + (y1 - y0), y0, INK, 1.5, alpha=alpha)


def _dancer(cv, x, y, s=1.0, t=0.0, phase=0.0, col=INK, alpha=1.0):
    a1 = 0.8 * math.sin(t * 2.4 + phase)
    a2 = 0.8 * math.sin(t * 2.4 + phase + 1.3)
    cv.circle(x, y - 120 * s, 13 * s, fill=col, alpha=alpha)
    # торс
    cv.line(x, y - 106 * s, x, y - 56 * s, col, 11 * s, alpha=alpha)
    # руки вверх
    cv.line(x, y - 100 * s, x - 40 * s * math.cos(a1), y - 152 * s * math.sin(a1 + 1.2), col, 7 * s,
            alpha=alpha)
    cv.line(x, y - 100 * s, x + 40 * s * math.cos(a2), y - 152 * s * math.sin(a2 + 1.2), col, 7 * s,
            alpha=alpha)
    # ноги
    cv.line(x, y - 56 * s, x - 26 * s, y, col, 8 * s, alpha=alpha)
    cv.line(x, y - 56 * s, x + 26 * s, y - 6 * s * math.sin(t * 2 + phase), col, 8 * s, alpha=alpha)


def _houses(cv, y=1180):
    for i in range(7):
        x = -30 + i * 170
        h = 300 + (i % 4) * 70
        cv.poly([(x, y), (x + 150, y), (x + 150, y - h), (x + 75, y - h - 90), (x, y - h)],
                fill="#cbb68e", stroke=INK, width=4)
        for r in range(3):
            cv.rect(x + 26 + (r % 2) * 40, y - h + 40 + r * 70, x + 62 + (r % 2) * 40,
                    y - h + 80 + r * 70, fill="#f2e6c9", stroke=INK, width=2)
        _hatch(cv, x + 8, y - h + 10, x + 140, y - 30, 14, 0.10)


def scene_hook(cv, t, ctx):
    k = B.kof(ctx, t, (0, 8))
    _paper(cv, t)
    _houses(cv)
    cv.rect(0, 1180, W, H, fill="#cdb992")
    _hatch(cv, 0, 1180, W, H, 12, 0.08)
    _dancer(cv, 420, 1180, 1.5, t, 0)
    _dancer(cv, 620, 1180, 1.3, t, 1.7)
    _dancer(cv, 800, 1180, 1.2, t, 3.1)
    for i in range(5):
        B.person(cv, 150 + i * 80, 1230, 0.7, "#4a3524", "#e2cba6")
    if k > 0.04:
        a = B.ease((k - 0.04) / 0.2)
        B.text(cv, "СТРАСБУРГ · ИЮЛЬ", 200, 34, "#6b5138", a)
        B.big_number(cv, "1518", 330, 168, INK, (RED, 10), a, INK, 4)
        B.text(cv, "ТАНЦУЮТ И НЕ МОГУТ ОСТАНОВИТЬСЯ", 400, 26, RED, a)
    B.grain(cv, 6, 9, 0.22)


def scene_spread(cv, t, ctx):
    k = B.kof(ctx, t, (8, 17))
    _paper(cv, t)
    # солнце-луна дуга
    cv.circle(540, 980, 300, stroke="#7a6344", width=3, alpha=0.5)
    ang = -math.pi / 2 + k * math.pi
    cv.circle(540 + math.cos(ang) * 300, 980 + math.sin(ang) * 300, 26, fill="#e8a03c" if k < 0.5 else "#c9d6e4")
    # толпа
    for i in range(14):
        x = 40 + i * 72
        y = 1180 + 14 * (i % 3)
        _dancer(cv, x, y, 0.55 + 0.1 * (i % 3), t, i * 0.9)
    if k > 0.05:
        a = B.ease((k - 0.05) / 0.25)
        B.text(cv, "К АВГУСТУ", 220, 36, "#6b5138", a)
        B.big_number(cv, "400", 380, 200, RED, (RED, 12), a, INK, 4)
        B.text(cv, "ЧЕЛОВЕК ТАНЦУЮТ", 450, 34, INK, a)
    if k > 0.55:
        B.text(cv, "ДНИ И НОЧИ", 1380, 30, "#6b5138", B.ease((k - 0.55) / 0.3))
    B.grain(cv, 6, 15, 0.22)


def scene_collapse(cv, t, ctx):
    k = B.kof(ctx, t, (17, 25))
    _paper(cv, t)
    cv.rect(0, 1200, W, H, fill="#c9b48d")
    # падающие
    for i in range(7):
        x = 90 + i * 130
        s = 0.9
        cv.save()
        cv.c.translate(x, 1200)
        cv.c.rotate(20 + i * 8)
        _dancer(cv, 0, 0, s * 0.8, t, i)
        cv.restore()
    for i in range(4):
        B.person(cv, 200 + i * 180, 1300, 0.8, "#3a2818", "#e2cba6")
    if k > 0.1:
        a = B.ease((k - 0.1) / 0.25)
        B.text(cv, "ЛЮДИ ПАДАЛИ ОТ ИСТОЩЕНИЯ", 260, 40, INK, a)
    B.grain(cv, 6, 21, 0.22)


def scene_mystery(cv, t, ctx):
    k = B.kof(ctx, t, (25, 33))
    _paper(cv, t)
    # музыканты
    for i in range(3):
        x = 250 + i * 260
        B.person(cv, x, 1250, 1.1, "#3a2818", "#e2cba6")
        cv.line(x + 20, 1150, x + 70, 1090, INK, 6)
        cv.circle(x + 76, 1084, 12, stroke=INK, width=4)
    if k > 0.05:
        a = B.ease((k - 0.05) / 0.25)
        B.text(cv, "ВЛАСТИ НАНЯЛИ МУЗЫКАНТОВ", 250, 40, INK, a)
        B.text(cv, "НЕ ПОМОГЛО", 320, 34, RED, a)
    if k > 0.45:
        a = B.ease((k - 0.45) / 0.3)
        cv.text("?", 540, 800, 380, fill=RED, center=True, alpha=a * 0.9)
        B.text(cv, "ПРИЧИНУ НЕ ЗНАЮТ ДО СИХ ПОР", 1000, 36, INK, a)
    B.grain(cv, 7, 27, 0.24)


SCENES = {"hook": scene_hook, "spread": scene_spread, "collapse": scene_collapse,
          "mystery": scene_mystery}


def render(name, t, ctx=None, finish=False):
    return B.render(name, t, ctx, SCENES)
