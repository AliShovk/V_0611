"""9. Цутому Ямагути: две бомбы. Пепельная палитра, красный, бумага."""
import math
import random

import skia

from vgen.reels import base as B
from vgen.kit import W, H, lin

ASH = "#1a1a1c"
ASH_L = "#2c2c30"
RED = "#c0392b"
EMBER = "#ff7a45"
CREAM = "#efe6d8"
PAPER = "#d9cdb8"


def _city(cv, y=1200, col="#101012", alpha=1.0, burn=0.0):
    rnd = random.Random(11)
    x = -30
    while x < W + 40:
        w = rnd.randint(70, 150)
        h = rnd.randint(120, 420)
        cv.rect(x, y - h, x + w - 10, y, fill=col, alpha=alpha)
        if burn > 0:
            for i in range(3):
                wx = x + 14 + i * 32
                wy = y - h + 24 + rnd.randint(0, 60)
                cv.rect(wx, wy, wx + 20, wy + 24, fill=EMBER, alpha=burn * 0.8)
        x += w


def _cloud(cv, x, y, s=1.0, alpha=1.0, t=0.0):
    # гриб: ножка + шляпка
    cv.poly([(x - 26 * s, y), (x + 26 * s, y), (x + 44 * s, y - 300 * s), (x - 44 * s, y - 300 * s)],
            fill="#3a3632", alpha=alpha)
    for i in range(7):
        ang = math.pi + i * (math.pi / 6)
        cx = x + math.cos(ang) * 150 * s
        cy = y - 300 * s + math.sin(ang) * 90 * s
        cv.circle(cx, cy, (90 + 18 * math.sin(i + t)) * s, fill="#4a443e", alpha=alpha * 0.9)
    cv.circle(x, y - 320 * s, 150 * s, fill="#57504a", alpha=alpha)


def scene_hook(cv, t, ctx):
    k = B.kof(ctx, t, (0, 8))
    cv.clear(ASH)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#101013"), (0.5, "#1d1c1e"), (1, "#0c0c0e")]))
    _city(cv, 1250, "#0a0a0c", 1.0, 0.0)
    _cloud(cv, 700, 1180, 1.15, 0.9, t)
    if k > 0.04:
        a = B.ease((k - 0.04) / 0.2)
        B.text(cv, "ХИРОСИМА · 6 АВГУСТА 1945", 220, 28, "#d9cdb8", a)
        B.big_number(cv, "2 БОМБЫ", 340, 104, CREAM, (RED, 14), a, "#0a0a0c", 8)
        B.text(cv, "ОДИН ЧЕЛОВЕК", 410, 36, "#ff9a7a", a)
    B.dust(cv, t, 30, "#d9cdb8", 0.10)
    B.grain(cv, 9, 3, 0.3)


def scene_hiro(cv, t, ctx):
    k = B.kof(ctx, t, (8, 15))
    cv.clear("#0e0e10")
    _city(cv, 1300, "#0a0a0c", 1.0, 0.0)
    if k < 0.55:
        _cloud(cv, 640, 1200, 1.0, 0.85, t)
    if k > 0.25:
        a = B.ease((k - 0.25) / 0.3)
        # вспышка
        cv.circle(640, 500, 300 * a, fill="#fff3e0", alpha=0.35 * a, blur=60)
        cv.rect(0, 0, W, H, fill="#ffffff", alpha=0.18 * a)
        B.text(cv, "ОН БЫЛ В 3 КМ ОТ ЭПИЦЕНТРА", 300, 30, "#ffe9c9", a)
        B.text(cv, "ПОЛУЧИЛ ОЖОГИ — И ВЫЖИЛ", 360, 26, "#ff9a7a", a)
    B.dust(cv, t, 40, "#d9cdb8", 0.14)
    B.grain(cv, 9, 12, 0.3)


def scene_train(cv, t, ctx):
    k = B.kof(ctx, t, (15, 22))
    cv.clear("#141213")
    # вагон поезда: окна и силуэт
    cv.rect(80, 520, 1000, 1200, fill="#1e1a1a")
    for i in range(4):
        cv.rect(130 + i * 220, 580, 330 + i * 220, 860, fill="#2a2422", stroke="#4a3a32", width=3)
    for i in range(4):
        cv.circle(230 + i * 220, 760, 34, fill="#0e0c0c")
        cv.circle(230 + i * 220, 700, 26, fill="#0e0c0c")
    # движение: рельсы, шпалы, дым за окном
    for i in range(10):
        x = (i * 150 + t * 320) % (W + 200) - 100
        cv.line(x, 1180, x + 110, 1180, "#4a3a32", 4, alpha=0.7)
    for i in range(8):
        x = (i * 170 + t * 420) % (W + 240) - 120
        cv.line(x, 1140, x, 1210, "#2a2422", 6, alpha=0.6)
    for i in range(6):
        px = (i * 210 + t * 260) % (W + 200) - 100
        cv.circle(px, 1050, 26 + 6 * math.sin(t * 3 + i), fill="#3a3430", alpha=0.25)
    # пейзаж за окнами: быстрые силуэты и вспышки света
    for i in range(4):
        for j in range(3):
            px = (i * 260 + j * 90 + t * 520) % (W + 200) - 100
            cv.poly([(px, 860), (px + 40, 700), (px + 80, 860)], fill="#241e1a", alpha=0.55)
    for i in range(4):
        fl = 0.25 + 0.35 * abs(math.sin(t * 7 + i * 1.7))
        cv.rect(130 + i * 220, 580, 330 + i * 220, 860, fill="#ffd9a0", alpha=fl * 0.22)
    if k > 0.1:
        a = B.ease((k - 0.1) / 0.3)
        B.text(cv, "ТРИ ДНЯ СПУСТЯ — НАГАСАКИ", 260, 34, CREAM, a)
        B.text(cv, "9 АВГУСТА", 320, 40, "#ff9a7a", a)
    B.grain(cv, 9, 19, 0.3)


def scene_final(cv, t, ctx):
    k = B.kof(ctx, t, (22, 30))
    cv.clear("#101012")
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#121214"), (1, "#1e1c1c")]))
    _cloud(cv, 540, 1250, 0.9, 0.35, t)
    _city(cv, 1350, "#0a0a0c", 0.9, 0.0)
    if k > 0.05:
        a = B.ease((k - 0.05) / 0.25)
        B.text(cv, "ОН ВЫЖИЛ ДВАЖДЫ", 420, 54, CREAM, a)
        B.text(cv, "В 2009 ГОДУ ЭТО ПРИЗНАЛИ ОФИЦИАЛЬНО", 1360, 28, "#d9cdb8", a)
        B.text(cv, "УМЕР В 2010-М В 93 ГОДА", 1420, 28, "#ff9a7a", a)
    B.grain(cv, 9, 27, 0.3)


SCENES = {"hook": scene_hook, "hiro": scene_hiro, "train": scene_train, "final": scene_final}


def render(name, t, ctx=None, finish=False):
    return B.render(name, t, ctx, SCENES)
