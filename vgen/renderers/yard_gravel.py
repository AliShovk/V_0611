"""Отсыпка заезда из щебня: 5 сцен, рисованный маркер/карандаш стиль."""
import math
import random

import skia

from vgen.kit import W, H, lin
from vgen.reels import base as B

PAPER = "#fbf6ec"
INK = "#2f2a24"
GREEN = "#4f8f4a"
ORANGE = "#e07b39"
BROWN = "#a9743f"
SOIL = "#8a6440"
BLUE = "#4a86b8"
GRAVEL1 = "#b8b2a4"
GRAVEL2 = "#cfc9bb"
GRAVEL3 = "#e2ddd2"
GREY = "#6f6a62"
RED = "#c2452e"


def rline(cv, x0, y0, x1, y1, color=INK, w=5, t=0.0, seed=0, alpha=1.0):
    """Дрожащая линия — эффект рисунка от руки."""
    rnd = random.Random(int(seed * 97 + x0 + y0))
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 46))
    pts = [(x0, y0)]
    for i in range(1, n):
        k = i / n
        jx = rnd.uniform(-1.6, 1.6)
        jy = rnd.uniform(-1.6, 1.6)
        pts.append((x0 + (x1 - x0) * k + jx, y0 + (y1 - y0) * k + jy))
    pts.append((x1, y1))
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], color, w, alpha=alpha)


def rrect(cv, x0, y0, x1, y1, color=INK, w=5, seed=0, alpha=1.0):
    rline(cv, x0, y0, x1, y0, color, w, 0, seed, alpha)
    rline(cv, x1, y0, x1, y1, color, w, 0, seed + 1, alpha)
    rline(cv, x1, y1, x0, y1, color, w, 0, seed + 2, alpha)
    rline(cv, x0, y1, x0, y0, color, w, 0, seed + 3, alpha)


def paper(cv, t):
    cv.clear(PAPER)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#fdfaf2"), (1, "#f3ecdd")]))
    rnd = random.Random(5)
    for _ in range(60):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        cv.circle(x, y, rnd.randint(30, 120), fill="#d9cdb4", alpha=0.03)


def leaves(cv, t, alpha=0.9):
    rnd = random.Random(11)
    for i in range(7):
        ax = rnd.randint(20, 220) if i % 2 == 0 else rnd.randint(880, 1060)
        ay = rnd.randint(40, 1500)
        cv.save()
        cv.c.rotate(rnd.randint(0, 360) + 3 * math.sin(t + i), ax, ay)
        cv.oval(ax - 16, ay - 34, ax + 16, ay + 34, fill=GREEN, alpha=0.16 * alpha)
        cv.line(ax, ay - 40, ax, ay + 40, GREEN, 2, alpha=0.25 * alpha)
        cv.restore()


def badge(cv, x, y, n, r=38, color=ORANGE):
    cv.circle(x, y, r, fill=color)
    cv.circle(x, y, r, stroke="#ffffff", width=3)
    cv.text(str(n), x, y + int(r * 0.36), int(r * (1.15 if len(str(n)) == 1 else 0.78)), fill="#ffffff", center=True)


def check_icon(cv, x, y, s=1.0, color=GREEN):
    cv.circle(x, y, 16 * s, stroke=color, width=4)
    cv.line(x - 7 * s, y, x - 2 * s, y + 6 * s, color, 4 * s)
    cv.line(x - 2 * s, y + 6 * s, x + 8 * s, y - 7 * s, color, 4 * s)


def gravel_fill(cv, x0, y0, x1, y1, seed=1, color=GRAVEL1, n=140, alpha=1.0):
    rnd = random.Random(seed)
    cv.rect(x0, y0, x1, y1, fill=color, alpha=alpha)
    for _ in range(n):
        px = rnd.uniform(x0, x1)
        py = rnd.uniform(y0, y1)
        rr = rnd.uniform(2.5, 6)
        cv.circle(px, py, rr, fill=rnd.choice([GRAVEL2, GRAVEL3, "#9c968a"]), alpha=0.9 * alpha)
        cv.circle(px, py, rr, stroke="#8a8478", width=1, alpha=0.5 * alpha)


def car(cv, x, y, s=1.0, alpha=1.0, color=BLUE):
    cv.rrect(x - 90 * s, y - 46 * s, x + 90 * s, y, 14 * s, fill=color, alpha=alpha)
    cv.rrect(x - 52 * s, y - 86 * s, x + 44 * s, y - 40 * s, 12 * s, fill=color, alpha=alpha)
    cv.rect(x - 46 * s, y - 80 * s, x - 4 * s, y - 48 * s, fill="#cfe6f5", alpha=alpha)
    cv.rect(x - 2 * s, y - 80 * s, x + 36 * s, y - 48 * s, fill="#cfe6f5", alpha=alpha)
    for dx in (-56, 54):
        cv.circle(x + dx * s, y + 2 * s, 22 * s, fill="#2f2a24", alpha=alpha)
        cv.circle(x + dx * s, y + 2 * s, 9 * s, fill="#d9d3c6", alpha=alpha)


def scene_hook(cv, t, ctx):
    k = B.kof(ctx, t, (0, 7))
    paper(cv, t)
    leaves(cv, t)
    # дорожка в перспективе
    cv.poly([(300, 1500), (780, 1500), (660, 980), (420, 980)], fill=GRAVEL2)
    gravel_fill(cv, 430, 990, 650, 1490, 3, GRAVEL2, 60)
    car(cv, 540, 1080, 1.35)
    rrect(cv, 300, 1500, 780, 1500, INK, 6, 1, 0.0)
    if k > 0.03:
        a = B.ease((k - 0.03) / 0.2)
        cv.rrect(70, 120, 1010, 380, 22, fill="#fdf7e8", alpha=0.9 * a)
        B.label(cv, "ЗАЕЗД НА УЧАСТОК", 205, 62, INK, a)
        B.label(cv, "ИЗ ЩЕБНЯ", 285, 88, ORANGE, a)
        B.label(cv, "8 ШАГОВ · БЕЗ ЛУЖ", 352, 38, GREY, a)
    B.grain(cv, 4, 2, 0.10)


def scene_mark(cv, t, ctx):
    k = B.kof(ctx, t, (7, 15))
    paper(cv, t)
    leaves(cv, t, 0.7)
    badge(cv, 120, 210, "1–2")
    B.label(cv, "РАЗМЕТКА", 250, 44, INK, B.ease(k * 2))
    # план сверху
    cv.poly([(180, 520), (900, 520), (980, 1420), (100, 1420)], fill="#efe6d2")
    rrect(cv, 180, 520, 900, 520, INK, 4, 2, 0.8)
    rrect(cv, 100, 1420, 980, 1420, INK, 4, 3, 0.8)
    rline(cv, 180, 520, 100, 1420, INK, 4, 0, 4, 0.8)
    rline(cv, 900, 520, 980, 1420, INK, 4, 0, 5, 0.8)
    # колышки
    for (px, py) in [(180, 520), (900, 520), (100, 1420), (980, 1420)]:
        rline(cv, px, py, px, py - 46, BROWN, 7, 0, px)
    # размеры
    if k > 0.25:
        a = B.ease((k - 0.25) / 0.2)
        rline(cv, 180, 620, 900, 620, ORANGE, 3, 0, 7, a)
        B.label(cv, "ШИРИНА 3,5–5 М", 596, 34, ORANGE, a)
    if k > 0.5:
        a = B.ease((k - 0.5) / 0.2)
        rline(cv, 960, 560, 960, 1380, ORANGE, 3, 0, 8, a)
        B.label(cv, "ДЛИНА", 1250, 30, ORANGE, a, x=880)
        B.label(cv, "ОТ 5 М", 1290, 30, ORANGE, a, x=880)
    B.grain(cv, 4, 9, 0.10)


def scene_dig(cv, t, ctx):
    k = B.kof(ctx, t, (15, 22))
    paper(cv, t)
    badge(cv, 120, 210, 3)
    B.label(cv, "СНЯТЬ ГРУНТ", 250, 44, INK, B.ease(k * 2))
    # разрез грунта
    cv.rect(90, 760, 990, 1300, fill=SOIL)
    cv.rect(90, 760, 990, 830, fill=GREEN, alpha=0.85)
    for i in range(7):
        cv.circle(160 + i * 120, 800, 18, fill=GREEN, alpha=0.9)
    # яма
    pit_l = 300
    pit_r = 780
    cv.rect(pit_l, 830, pit_r, 1240, fill="#5f4128")
    for i in range(5):
        rline(cv, 360 + i * 60, 900 + i * 20, 420 + i * 60, 1180, "#3f2c1a", 2, 0, i, 0.4)
    # стрелка глубины
    if k > 0.2:
        a = B.ease((k - 0.2) / 0.25)
        rline(cv, pit_r + 60, 830, pit_r + 60, 1120, RED, 4, 0, 11, a)
        cv.poly([(pit_r + 60, 1140), (pit_r + 44, 1106), (pit_r + 76, 1106)], fill=RED, alpha=a)
        B.label(cv, "25–40 СМ", 990, 34, RED, a)
    if k > 0.55:
        a = B.ease((k - 0.55) / 0.25)
        cv.text("+ корни и трава", 130, 1240, 30, fill="#f2e6d0", alpha=a)
    B.grain(cv, 4, 15, 0.10)


def scene_layers(cv, t, ctx):
    k = B.kof(ctx, t, (22, 33))
    paper(cv, t)
    badge(cv, 120, 210, "4–6")
    B.label(cv, "ПИРОГ ЗАЕЗДА", 250, 44, INK, min(1.0, k * 5))
    # разрез сверху вниз: мелкий, средний, крупный, геотекстиль, грунт
    x0, x1 = 140, 940
    base = 1480
    bands = [
        ("МЕЛКИЙ 5–20 ММ", 110, "#e8e2d6", GREY),
        ("СРЕДНИЙ 20–40 ММ", 150, "#cdc6b6", "#8a8478"),
        ("КРУПНЫЙ 40–70 ММ", 210, "#b0a998", "#6f6a62"),
        ("ГЕОТЕКСТИЛЬ", 60, "#9fb3c8", "#3c5a75"),
        ("ГРУНТ", 150, "#8a6440", "#4a3320"),
    ]
    y = base
    for i, (name, h, col, edge) in enumerate(bands):
        y2 = y - h
        a = max(0.15, min(1.0, (k - i * 0.03) / 0.06))
        cv.rect(x0, y2, x1, y, fill=col, alpha=a)
        cv.rect(x0, y2, x1, y, stroke=edge, width=4, alpha=a)
        if "ММ" in name:
            for j in range(9):
                px = x0 + 30 + j * 84
                cv.circle(px, y2 + h * 0.3, 9, fill=edge, alpha=0.5 * a)
                cv.circle(px + 34, y2 + h * 0.7, 13, fill=edge, alpha=0.35 * a)
        B.label(cv, name, y2 + h * 0.62, 32, "#1f1a14" if i < 3 else "#f4ece0", a, x=(x0 + x1) / 2)
        y = y2
    # размеры справа
    if k > 0.25:
        a = B.ease((k - 0.25) / 0.25)
        B.label(cv, "СЛОИ 15–20 / 10–15 / 5–10 СМ", 1340, 30, GREY, a)
        B.label(cv, "КАЖДЫЙ — ПОД ВИБРОПЛИТУ", 1392, 32, "#b4531f", a)
    B.grain(cv, 4, 22, 0.10)


def scene_finish(cv, t, ctx):
    k = B.kof(ctx, t, (33, 40))
    paper(cv, t)
    leaves(cv, t, 0.8)
    # готовый заезд с бордюром
    cv.poly([(340, 1520), (760, 1520), (650, 900), (450, 900)], fill=GRAVEL3)
    gravel_fill(cv, 450, 910, 650, 1510, 31, GRAVEL3, 40)
    for sx in (330, 770):
        cv.poly([(sx - 26, 1520), (sx + 26, 1520), (sx + 10, 880), (sx - 10, 880)], fill="#d8d2c4")
        rrect(cv, sx - 26, 1500, sx + 26, 1520, GREY, 3, sx, 0.9)
    car(cv, 540, 1000, 1.05)
    if k > 0.05:
        a = B.ease((k - 0.05) / 0.2)
        B.label(cv, "БОРТ ДЕРЖИТ КРАЯ", 220, 48, INK, a)
    if k > 0.35:
        a = B.ease((k - 0.35) / 0.3)
        B.label(cv, "УКЛОН 2–3%", 392, 44, "#b4531f", a)
        B.label(cv, "СРОК 10–20 ЛЕТ", 452, 44, "#2f6b2c", a)
    if k > 0.6:
        a = B.ease((k - 0.6) / 0.3)
        cv.rrect(120, 1180, 960, 1420, 16, fill="#fdf7e8", stroke=GREEN, width=3, alpha=a)
        check_icon(cv, 180, 1240, 1.1)
        B.label(cv, "БЫСТРО · БЮДЖЕТНО", 1300, 36, INK, a, x=560)
        B.label(cv, "И БЕЗ ЛУЖ ВЕСНОЙ", 1352, 36, "#2f6b2c", a, x=560)
    B.grain(cv, 4, 30, 0.10)


SCENES = {"hook": scene_hook, "mark": scene_mark, "dig": scene_dig, "layers": scene_layers,
          "finish": scene_finish}


def render(name, t, ctx=None, finish=False):
    return B.render(name, t, ctx, SCENES)
