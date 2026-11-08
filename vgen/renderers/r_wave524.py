"""6. Волна 524 метра, залив Литуйя 1958. Разрез залива, холодные тона."""
import math
import random

import skia

from vgen.reels import base as B
from vgen.kit import W, H, lin

SKY = "#c9dce6"
SKY2 = "#7a9db3"
ROCK = "#3c4a52"
ROCK_L = "#5a6b74"
SNOW = "#eef5f8"
SEA = "#12384a"
FOAM = "#ffffff"
GREEN = "#274a3c"


def _bay(cv, t):
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#e6f0f5"), (0.35, SKY), (0.55, SKY2), (1, "#4a6474")]))
    # дальние горы
    cv.poly([(-40, 780), (120, 480), (260, 700), (380, 420), (520, 700), (660, 500), (800, 760),
             (960, 560), (1120, 800), (1120, 1000), (-40, 1000)], fill="#8fa6b5", alpha=0.8)
    # левый склон — крутой
    cv.poly([(-40, 1600), (-40, 520), (300, 380), (520, 760), (620, 1200), (700, 1600)],
            fill=ROCK)
    cv.poly([(-40, 520), (300, 380), (420, 520), (120, 640)], fill=SNOW, alpha=0.9)
    # правый склон
    cv.poly([(1120, 1600), (1120, 420), (860, 500), (740, 820), (700, 1200), (680, 1600)],
            fill=ROCK_L)
    cv.poly([(1120, 420), (860, 500), (820, 560), (1120, 500)], fill=SNOW, alpha=0.85)
    # вода
    cv.rect(0, 1180, W, H, fill=SEA)


def _trees(cv, t, alpha=1.0, stripped=0.0):
    rnd = random.Random(6)
    for i in range(60):
        x = rnd.randint(0, W)
        y = rnd.randint(1120, 1600)
        if stripped > rnd.random():
            # поваленные
            cv.line(x, y, x + 46, y - 6, "#1c2a20", 3, alpha=alpha * 0.8)
        else:
            h = rnd.randint(18, 46)
            cv.poly([(x - 9, y), (x + 9, y), (x, y - h)], fill="#1f3a2c", alpha=alpha)


def scene_hook(cv, t, ctx):
    k = B.kof(ctx, t, (0, 8))
    _bay(cv, t)
    _trees(cv, t)
    # вода на дне залива
    cv.rect(0, 1300, W, H, fill=SEA)
    if k > 0.04:
        a = B.ease((k - 0.04) / 0.2)
        B.text(cv, "ЗАЛИВ ЛИТУЙЯ · АЛЯСКА · 1958", 200, 28, "#1c3340", a)
        B.big_number(cv, "524 М", 340, 160, "#ffffff", (SEA, 16), a, "#0d222c", 8)
        B.text(cv, "ВЫСОТА ВОЛНЫ", 410, 34, "#0d222c", a)
    B.grain(cv, 5, 7, 0.16)


def scene_quake(cv, t, ctx):
    k = B.kof(ctx, t, (8, 16))
    cv.save()
    cv.c.translate(8 * math.sin(t * 9) * (1 - k), 6 * math.cos(t * 11) * (1 - k))
    _bay(cv, t)
    _trees(cv, t)
    # обвал
    if k > 0.15:
        a = B.ease((k - 0.15) / 0.4)
        for i in range(26):
            rnd = random.Random(i)
            x = 760 + rnd.randint(-60, 220)
            y = 520 + rnd.randint(0, 500) + 260 * a * rnd.random()
            cv.circle(x, y, rnd.randint(6, 22), fill="#4a5a62", alpha=a * 0.9)
        cv.poly([(700, 560), (900, 640), (860, 900), (700, 860)], fill="#5a6b74", alpha=0.6 * a)
    cv.restore()
    if k > 0.1:
        a = B.ease((k - 0.1) / 0.25)
        B.text(cv, "ЗЕМЛЕТРЯСЕНИЕ ОБРУШИЛО МИЛЛИОНЫ ТОНН ПОРОДЫ", 200, 28, "#0d222c", a)
    B.grain(cv, 6, 15, 0.2)


def scene_wave(cv, t, ctx):
    k = B.kof(ctx, t, (16, 24))
    _bay(cv, t)
    _trees(cv, t, 1.0, stripped=0.7 * k)
    # волна поднимается по склону
    top = 1180 - 700 * B.ease(k)
    p = skia.Path()
    p.moveTo(540, 1600)
    p.cubicTo(430, 1400, 470, top + 180, 560, top)
    p.lineTo(700, top + 60)
    p.cubicTo(720, top + 300, 660, 1400, 640, 1600)
    p.close()
    cv.path(p, fill=SEA, alpha=0.92)
    cv.c.drawPath(p, B.sp(FOAM, 6, 220))
    # отметка 524
    if k > 0.4:
        a = B.ease((k - 0.4) / 0.3)
        y = 470
        cv.line(120, y, 980, y, "#ffd08a", 3, alpha=a * 0.8)
        B.text(cv, "524 М", 780, y - 20, 44, "#ffd08a", a)
    if k > 0.1:
        B.text(cv, "ВОЛНА ВЗМЕТНУЛАСЬ ПО СКЛОНУ", 200, 30, "#0d222c", B.ease((k - 0.1) / 0.25))
    B.grain(cv, 6, 23, 0.2)


def scene_final(cv, t, ctx):
    k = B.kof(ctx, t, (24, 32))
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#0e1a22"), (1, "#243a44")]))
    # сравнение высот
    h1 = 700 * B.ease(k)
    cv.rect(300, 1400 - h1, 420, 1400, fill=SEA, stroke=FOAM, width=3)
    cv.rect(700, 1400 - h1 * 0.73, 820, 1400, fill="#8a7a5a", stroke="#e6dcc4", width=3)
    cv.line(120, 1400, 980, 1400, "#e6f0f5", 3)
    B.text(cv, "524 М", 360, 1400 - h1 - 30, 40, "#bfe6ff", B.ease(k))
    B.text(cv, "381 М", 760, 1400 - h1 * 0.73 - 30, 34, "#e6dcc4", B.ease(k))
    B.text(cv, "ВОЛНА", 360, 1470, 28, "#bfe6ff")
    B.text(cv, "ЭМПАЙР-СТЕЙТ", 760, 1470, 26, "#e6dcc4")
    if k > 0.55:
        B.text(cv, "ЛЕС СНЕСЛО ДО СКАЛЫ", 1660, 32, "#ffd08a", B.ease((k - 0.55) / 0.3))
    B.grain(cv, 6, 31, 0.2)


SCENES = {"hook": scene_hook, "quake": scene_quake, "wave": scene_wave, "final": scene_final}


def render(name, t, ctx=None, finish=False):
    return B.render(name, t, ctx, SCENES)
