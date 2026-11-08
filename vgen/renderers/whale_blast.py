"""Взорванный кит, Орегон 1970: пляж, туша, динамит, разлёт кусков.

Тёмный вектор: песок, море, толпа, взрыв. 5 сцен.
"""
import math
import random

import skia

from vgen.kit import Canvas, W, H, lin, rad, rgba

NIGHT = "#0a1018"
SAND = "#c9a878"
SAND_D = "#9c7c50"
SEA = "#173a4e"
SEA_L = "#245a70"
SKY1 = "#f0b27a"
SKY2 = "#7d5a6a"
CREAM = "#fff4e2"
INK = "#0d1219"
GOLD = "#ffc45e"
RED = "#f2544b"
BLOOD = "#8c3a2a"

HOR = 860
SAND_Y = 900


def _sp(color, width, alph=255):
    alph = max(0, min(255, int(alph)))
    return skia.Paint(AntiAlias=True, Color=rgba(color, alph / 255.0),
                      Style=skia.Paint.kStroke_Style, StrokeWidth=width,
                      StrokeCap=skia.Paint.kRound_Cap)


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def k_of(ctx, t, win):
    if ctx and ctx.get("scene_dur"):
        return max(0.0, min(1.0, ctx["scene_t"] / ctx["scene_dur"]))
    t0, t1 = win
    return max(0.0, min(1.0, (t - t0) / max(0.1, t1 - t0)))


def label(cv, s, size, y, color=CREAM, x=540, alpha=1.0, stroke=INK, sw=8):
    cv.text(s, x, y, size, fill=color, center=True, alpha=alpha, stroke=stroke, stroke_w=sw)


def beach(cv, t, dawn=0.0):
    cv.rect(0, 0, W, SAND_Y, fill=lin(0, 0, 0, HOR, [
        (0, "#1a2230"), (0.5, "#3d3a44"), (1, "#c98a62")]))
    cv.rect(0, 0, W, HOR, fill=lin(0, 0, 0, HOR,
                                   [(0, "#243040"), (0.6, "#7a5a5a"), (1, "#e8a878")]), alpha=0.6 + 0.4 * dawn)
    cv.circle(300, HOR - 40, 90, fill="#ffd9a0", alpha=0.5 * dawn + 0.15, blur=50)
    cv.rect(0, HOR, W, SAND_Y, fill=SEA)
    for i in range(5):
        y = HOR + 10 + i * 16
        p = skia.Path()
        for x in range(0, W + 20, 20):
            yy = y + 3 * math.sin(x * 0.03 + t * 1.6 + i)
            (p.moveTo if x == 0 else p.lineTo)(x, yy)
        cv.c.drawPath(p, _sp("#bfe6ff", 2, 60))
    cv.rect(0, SAND_Y, W, H, fill=lin(0, SAND_Y, 0, H, [(0, SAND), (1, SAND_D)]))
    for i in range(40):
        x = (i * 137) % W
        y = SAND_Y + 20 + (i * 71) % 500
        cv.circle(x, y, 2, fill="#7d5f3c", alpha=0.35)


def whale(cv, x, y, s=1.0, alpha=1.0, red=0.0):
    """Кит на песке: тёмная туша, хвост, плавники."""
    body = skia.Path()
    body.moveTo(x - 260 * s, y + 40 * s)
    body.cubicTo(x - 220 * s, y - 90 * s, x + 40 * s, y - 120 * s, x + 180 * s, y - 40 * s)
    body.cubicTo(x + 240 * s, y - 10 * s, x + 250 * s, y + 30 * s, x + 200 * s, y + 60 * s)
    body.cubicTo(x + 60 * s, y + 90 * s, x - 140 * s, y + 90 * s, x - 260 * s, y + 40 * s)
    body.close()
    cv.path(body, fill=lin(0, y - 120 * s, 0, y + 90 * s,
                           [(0, "#4a5666"), (0.6, "#2b3542"), (1, "#1a222c")]), alpha=alpha)
    # хвост
    cv.poly([(x + 200 * s, y + 50 * s), (x + 300 * s, y - 10 * s), (x + 290 * s, y + 30 * s),
             (x + 340 * s, y + 60 * s), (x + 250 * s, y + 70 * s)], fill="#2b3542", alpha=alpha)
    # брюхо
    cv.poly([(x - 230 * s, y + 40 * s), (x + 180 * s, y + 55 * s), (x + 120 * s, y + 85 * s),
             (x - 150 * s, y + 80 * s)], fill="#b9c6d4", alpha=0.5 * alpha)
    if red > 0:
        for i in range(6):
            cv.circle(x - 100 * s + i * 60 * s, y + 30 * s + 10 * math.sin(i), 14 * s,
                      fill=BLOOD, alpha=0.7 * red * alpha)


def person(cv, x, y, s=1.0, color="#2b3a4a", alpha=1.0):
    cv.circle(x, y - 34 * s, 10 * s, fill="#e8c9a0", alpha=alpha)
    cv.rrect(x - 9 * s, y - 24 * s, x + 9 * s, y, 7 * s, fill=color, alpha=alpha)
    cv.line(x - 8 * s, y, x - 12 * s, y + 26 * s, INK, 4 * s, alpha=alpha)
    cv.line(x + 8 * s, y, x + 12 * s, y + 26 * s, INK, 4 * s, alpha=alpha)


def crowd(cv, t, n=9, y=1300, run=0.0, alpha=1.0):
    for i in range(n):
        x = 70 + i * 110
        if run > 0:
            x += run * 120 * (1 if i % 2 else -0.8) * math.sin(t * 3 + i)
        person(cv, x, y + 6 * math.sin(t * 2 + i), 1.0,
               ["#2b3a4a", "#4a3a2a", "#1f3340"][i % 3], alpha)


def explosion(cv, t, k, cx=540, cy=980):
    if k <= 0:
        return
    r = 60 + 320 * ease(k)
    cv.circle(cx, cy, r * 0.7, fill="#ffd9a0", alpha=0.35 * (1 - k), blur=30)
    cv.circle(cx, cy, r * 0.45, fill="#fff3d0", alpha=0.5 * (1 - k), blur=16)
    # куски
    for i in range(26):
        ang = i * 0.62
        sp = 0.6 + (i % 5) * 0.18
        dx = math.cos(ang) * (60 + 320 * ease(k) * sp)
        dy = -math.sin(ang) * (40 + 360 * ease(k) * sp) + 160 * k * k
        rr = 10 + (i % 4) * 8
        col = BLOOD if i % 3 == 0 else "#2b3542"
        cv.circle(cx + dx, cy + dy, rr * (1 - 0.4 * k), fill=col, alpha=0.9)


# ---------- сцены ----------

def scene_hook(cv, t, ctx):
    k = k_of(ctx, t, (0, 8))
    beach(cv, t, dawn=0.4)
    whale(cv, 540, 1180, 1.0)
    # динамит: шашки
    for i in range(4):
        x = 400 + i * 90
        cv.rrect(x - 14, 1240, x + 14, 1330, 6, fill=RED)
        cv.rect(x - 14, 1262, x + 14, 1272, fill=INK)
        cv.line(x, 1240, x + 10, 1200, "#d9b36a", 3)
    crowd(cv, t, 6, 1420, 0, 0.95)
    if k > 0.05:
        a = ease((k - 0.05) / 0.2)
        cv.text("8 ТОНН", 540, 300, 130, fill="#ffffff", center=True, stroke=INK,
                stroke_w=12, glow=(GOLD, 24), alpha=a)
        label(cv, "И 450 КГ ДИНАМИТА", 40, 372, GOLD, alpha=a)
    if k > 0.5:
        label(cv, "ОРЕГОН · 1970", 34, 440, "#e8c9a0", alpha=ease((k - 0.5) / 0.3))


def scene_whale(cv, t, ctx):
    k = k_of(ctx, t, (7, 14))
    beach(cv, t, dawn=0.55)
    whale(cv, 540, 1210, 1.05)
    crowd(cv, t, 5, 1440, 0, 0.9)
    if k > 0.05:
        a = ease((k - 0.05) / 0.2)
        label(cv, "КАШАЛОТ", 40, 250, CREAM, alpha=a)
        label(cv, "ВОСЕМЬ ТОНН НА ПЕСКЕ", 30, 306, GOLD, alpha=a)
    if k > 0.4:
        label(cv, "ФЛОРЕНС, ОРЕГОН · 1970", 30, 380, "#e8c9a0", alpha=ease((k - 0.4) / 0.3))


def scene_setup(cv, t, ctx):
    k = k_of(ctx, t, (8, 16))
    beach(cv, t, dawn=0.8)
    whale(cv, 540, 1180, 0.9)
    # ящики с взрывчаткой и рабочие
    for i in range(3):
        x = 300 + i * 120
        cv.rrect(x - 40, 1290, x + 40, 1370, 6, fill="#a8742c", stroke=INK, width=3)
        cv.text("TNT", x, 1342, 22, fill=CREAM, center=True)
    person(cv, 250, 1330, 1.1, "#2b3a4a")
    person(cv, 800, 1330, 1.1, "#4a3a2a")
    # толпа и журналисты
    crowd(cv, t, 8, 1500, 0)
    for i in range(2):
        x = 640 + i * 90
        cv.line(x, 1400, x, 1470, INK, 5)
        cv.rrect(x - 22, 1330, x + 22, 1400, 6, fill="#1f2a36", stroke=CREAM, width=3)
    if k > 0.1:
        a = ease((k - 0.1) / 0.25)
        label(cv, "ЗРИТЕЛИ И ЖУРНАЛИСТЫ", 36, 230, CREAM, alpha=a)
        label(cv, "ЗАКЛАДЫВАЮТ ВЗРЫВЧАТКУ", 26, 285, "#ffd08a", alpha=a)


def scene_blast(cv, t, ctx):
    k = k_of(ctx, t, (16, 25))
    beach(cv, t, dawn=0.6)
    if k < 0.12:
        whale(cv, 540, 1180, 1.0)
    explosion(cv, t, min(1.0, k / 0.7))
    if k > 0.12:
        # туша рвётся на две половины и разлетается
        fly = ease(min(1.0, (k - 0.12) / 0.30))
        a = max(0.0, 1.0 - 0.5 * k)
        cv.save()
        cv.c.clipRect(skia.Rect.MakeLTRB(0, 900, 540, 1500))
        whale(cv, 540 - 330 * fly, 1180 - 260 * fly, 1.0, alpha=a, red=1.0)
        cv.restore()
        cv.save()
        cv.c.clipRect(skia.Rect.MakeLTRB(540, 900, W, 1500))
        whale(cv, 540 + 380 * fly, 1180 - 300 * fly, 0.85, alpha=a, red=1.0)
        cv.restore()
    # люди бегут
    crowd(cv, t, 8, 1450, run=min(1.0, k * 2.0), alpha=0.95)
    if k > 0.05:
        a = ease((k - 0.05) / 0.2)
        label(cv, "ВМЕСТО КУСОЧКОВ — КУСКИ", 38, 220, CREAM, alpha=a)
        label(cv, "ЖИР И ПЛОТЬ ПО ОКРУГЕ", 28, 276, "#ffd08a", alpha=a)


def scene_after(cv, t, ctx):
    k = k_of(ctx, t, (25, 32))
    beach(cv, t, dawn=0.5)
    whale(cv, 540, 1240, 1.0, alpha=0.85, red=0.9)
    # куски вокруг и раздавленная машина
    for i in range(14):
        x = 90 + (i * 97) % 900
        y = 1180 + (i * 53) % 460
        rr = 10 + (i % 4) * 9
        cv.circle(x, y, rr, fill=BLOOD if i % 2 else "#2b3542", alpha=0.85)
    cv.rrect(720, 1350, 940, 1440, 14, fill="#7a8fa6", stroke=INK, width=4)
    cv.circle(770, 1450, 26, fill=INK)
    cv.circle(890, 1450, 26, fill=INK)
    cv.poly([(760, 1350), (820, 1300), (860, 1350)], fill=BLOOD, alpha=0.9)
    if k > 0.1:
        a = ease((k - 0.1) / 0.25)
        label(cv, "КУСОК РАЗДАВИЛ МАШИНУ", 34, 230, CREAM, alpha=a)


def scene_final(cv, t, ctx):
    k = k_of(ctx, t, (32, 40))
    beach(cv, t, dawn=1.0)
    whale(cv, 540, 1250, 0.8, alpha=0.5, red=0.5)
    if k > 0.05:
        a = ease((k - 0.05) / 0.25)
        label(cv, "ЛЮДИ НЕ ПОСТРАДАЛИ", 40, 300, CREAM, alpha=a)
        label(cv, "КРОМЕ РЕПУТАЦИИ ВЛАСТЕЙ", 28, 356, "#ffd08a", alpha=a)
    if k > 0.45:
        a = ease((k - 0.45) / 0.3)
        label(cv, "САМОЕ АБСУРДНОЕ ВИДЕО В ИСТОРИИ ТВ", 28, 1180, GOLD, alpha=a)


SCENES = {
    "hook": scene_hook,
    "whale": scene_whale,
    "setup": scene_setup,
    "blast": scene_blast,
    "after": scene_after,
    "final": scene_final,
}


def caption(cv, text, hl):
    if not text:
        return
    size = 50
    words = text.split()
    width = sum(cv.text_w(w + " ", size) for w in words)
    while width > 930 and size > 26:
        size -= 3
        width = sum(cv.text_w(w + " ", size) for w in words)
    x = 540 - width / 2
    cv.rrect(540 - width / 2 - 26, 1756, 540 + width / 2 + 26, 1844, 18, fill="#0b0f16", alpha=0.84)
    for w in words:
        col = "#ffd08a" if any(h.lower() in w.lower() for h in hl) else CREAM
        cv.text(w, x, 1820, size, fill=col)
        x += cv.text_w(w + " ", size)


def render(name, t, ctx=None, finish=False):
    ctx = ctx or {}
    cv = Canvas()
    cv.save()
    cv.c.translate(3 * math.sin(t * 0.5), 2 * math.cos(t * 0.4))
    SCENES[name](cv, t, ctx)
    cv.restore()
    caption(cv, ctx.get("caption_text", ""), ctx.get("caption_hl", ()))
    return cv.to_pil()
