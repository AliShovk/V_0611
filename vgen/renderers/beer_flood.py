"""Пивной потоп в Лондоне, 1814: лопнувшая цистерна, волна портера, улица.

Тёмный вектор: ночной Лондон, янтарная волна, тёплые фонари. 5 сцен.
"""
import math
import random

import skia

from vgen.kit import Canvas, W, H, lin, rad, rgba

NIGHT = "#06090f"
BRICK = "#2a2118"
BRICK_L = "#3a2e22"
BEER = "#b8721f"
BEER_L = "#e0a044"
FOAM = "#ffe9c9"
CREAM = "#fff3e0"
GOLD = "#ffc45e"
LAMP = "#ffd79a"
INK = "#0b0f16"

GROUND = 1420


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


# ---------- Лондон ----------

def sky(cv, t):
    cv.rect(0, 0, W, GROUND, fill=lin(0, 0, 0, GROUND, [
        (0, "#04070d"), (0.55, "#0b1220"), (1, "#221a16")]))
    for i in range(26):
        x = (i * 173) % W
        y = 60 + (i * 211) % 600
        cv.circle(x, y, 1.2, fill="#cfd9e6", alpha=0.25)


def house(cv, x, y, w, h, lit=1.0, alpha=1.0):
    cv.rect(x, y - h, x + w, y, fill=BRICK, alpha=alpha)
    cv.rect(x, y - h, x + w, y - h + 10, fill=BRICK_L, alpha=alpha)
    for r in range(int(h // 62)):
        for c in range(max(1, int(w // 54))):
            wx = x + 16 + c * 54
            wy = y - h + 34 + r * 62
            if wx + 30 < x + w - 8 and wy + 34 < y - 20:
                on = random.Random(int(x + r * 7 + c * 13)).random() < 0.55
                col = LAMP if on else "#3a3126"
                cv.rect(wx, wy, wx + 30, wy + 34, fill=col, alpha=(0.85 if on else 0.6) * lit * alpha)


def london(cv, t, flash=0.0):
    sky(cv, t)
    base = GROUND
    xs = -30
    rnd = random.Random(3)
    while xs < W + 40:
        w = rnd.randint(110, 170)
        h = rnd.randint(320, 520)
        house(cv, xs, base, w, h, lit=1.0 if flash < 0.5 else 0.4)
        xs += w + rnd.randint(6, 20)
    cv.rect(0, GROUND - 10, W, H, fill="#15100c")


def lamp_post(cv, x, t, h=260):
    cv.line(x, GROUND, x, GROUND - h, "#1d1712", 8)
    cv.circle(x, GROUND - h - 6, 16, fill=LAMP, alpha=0.9, blur=8)
    cv.circle(x, GROUND - h - 6, 34, fill=LAMP, alpha=0.10, blur=26)


def vat(cv, x, y, w, h, alpha=1.0, crack=0.0, hoops=5):
    """Деревянная цистерна: клёпки, обручи, трещина."""
    cv.rrect(x - w / 2, y - h, x + w / 2, y, w * 0.16, fill=lin(x - w / 2, 0, x + w / 2, 0,
                                                             [(0, "#6b4a26"), (0.4, "#a97840"), (1, "#4a3018")]),
             alpha=alpha)
    for i in range(hoops):
        yy = y - h + h * (i + 0.6) / (hoops + 0.2)
        cv.rect(x - w / 2 - 4, yy, x + w / 2 + 4, yy + 12, fill="#2b2b2f", alpha=alpha)
    for i in range(9):
        xx = x - w / 2 + (i + 0.5) * w / 9
        cv.line(xx, y - h + 14, xx, y - 6, "#3a2410", 2, alpha=0.5 * alpha)
    if crack > 0.02:
        p = skia.Path()
        p.moveTo(x + w * 0.1, y - h * 0.7)
        p.lineTo(x + w * 0.22, y - h * 0.45)
        p.lineTo(x + w * 0.12, y - h * 0.2)
        cv.c.drawPath(p, _sp("#1a0f06", 4 + 10 * crack, int(240 * crack)))
        # струя
        for i in range(3):
            cv.line(x + w * 0.16, y - h * 0.45, x + w * 0.16 + 120 * crack + i * 8,
                    y - h * 0.1 + i * 30, BEER_L, 8 - i * 2, alpha=0.8 * crack)


def beer_wave(cv, t, level, amp=18, alpha=1.0, foam=True):
    cv.rect(0, level, W, H, fill=lin(0, level, 0, H, [(0, BEER), (0.5, "#8d5314"), (1, "#4a2a0c")]),
            alpha=alpha)
    p = skia.Path()
    for x in range(-20, W + 40, 14):
        y = level + amp * math.sin(x * 0.011 + t * 1.6)
        (p.moveTo if x == -20 else p.lineTo)(x, y)
    cv.c.drawPath(p, _sp(FOAM, 6, int(200 * alpha)))
    if foam:
        for i in range(20):
            x = (i * 97 + t * 60) % W
            y = level + 10 + 12 * math.sin(i + t * 2)
            cv.circle(x, y, 4 + (i % 3) * 2, fill=FOAM, alpha=0.5 * alpha)


# ---------- сцены ----------

def scene_hook(cv, t, ctx):
    k = k_of(ctx, t, (0, 8))
    london(cv, t)
    lamp_post(cv, 160, t)
    lamp_post(cv, 930, t)
    beer_wave(cv, t, 1180 + 10 * math.sin(t * 1.4), 22)
    # люди на крыше
    for i in range(3):
        x = 620 + i * 70
        y = 1010
        cv.circle(x, y - 30, 12, fill=CREAM)
        cv.rrect(x - 12, y - 16, x + 12, y + 20, 8, fill="#2d3a4a")
    if k > 0.05:
        a = ease((k - 0.05) / 0.2)
        cv.text("1 400 000", 540, 330, 150, fill="#ffffff", center=True, stroke=INK,
                stroke_w=12, glow=(BEER_L, 26), alpha=a)
        label(cv, "ЛИТРОВ ПИВА НА УЛИЦЕ", 38, 400, GOLD, alpha=a)
    if k > 0.5:
        label(cv, "ЛОНДОН · 1814", 34, 470, "#e8c9a0", alpha=ease((k - 0.5) / 0.3))


def scene_vat(cv, t, ctx):
    k = k_of(ctx, t, (8, 17))
    cv.clear("#0a0d12")
    # интерьер пивоварни: фермы, чан
    for i in range(4):
        x = 120 + i * 260
        cv.line(x, 0, x, 1000, "#1b2634", 10)
        cv.line(x, 300, x + 260, 300, "#1b2634", 6)
    cv.rect(0, 1000, W, H, fill="#12161d")
    vat(cv, 540, 1000, 520, 700, crack=ease(max(0.0, (k - 0.45) / 0.55)))
    # мелкие бочки
    for i in range(5):
        x = 130 + i * 200
        cv.rrect(x - 46, 940, x + 46, 1010, 10, fill="#7a5426")
    if k > 0.1:
        a = ease((k - 0.1) / 0.25)
        label(cv, "ЧАН С ПОРТЕРОМ", 40, 220, CREAM, alpha=a)
        label(cv, "ДЕРЕВО И ОБРУЧИ", 28, 272, "#c9a678", alpha=a)
    if k > 0.55:
        label(cv, "ТРЕЩИНА", 40, 1300, "#ffb37a", alpha=ease((k - 0.55) / 0.3))


def scene_burst(cv, t, ctx):
    k = k_of(ctx, t, (17, 26))
    cv.clear("#080b11")
    # силуэт пивоварни
    for i in range(3):
        cv.rect(80 + i * 320, 380, 340 + i * 320, 1180, fill="#131a24")
    # разорванный чан: две половины разъезжаются
    gap = 160 * ease(k)
    vat(cv, 420 - gap, 1180, 300, 520, alpha=0.95, crack=1.0, hoops=4)
    vat(cv, 700 + gap, 1180, 300, 520, alpha=0.95, crack=0.6, hoops=3)
    # клёпки летят
    for i in range(14):
        ph = (t * 1.3 + i * 0.11) % 1.0
        x = 540 + (i - 7) * 70 * ph
        y = 900 - 300 * math.sin(ph * math.pi) + 60
        cv.save()
        cv.c.rotate(ph * 220, x, y)
        cv.rrect(x - 12, y - 34, x + 12, y + 34, 4, fill="#8a5f2c", alpha=0.95 * (1 - ph * 0.6))
        cv.restore()
    # брызги из разрыва
    for i in range(24):
        ph = (t * 1.7 + i * 0.09) % 1.0
        bx = 540 + (i - 12) * 22 * ph
        by = 760 - 260 * math.sin(ph * math.pi) * (0.5 + 0.5 * (i % 3) / 2)
        cv.circle(bx, by, 3 + (i % 4) * 3, fill=FOAM, alpha=0.65 * (1 - ph))
    # стена пива
    beer_wave(cv, t, 1120 - 40 * math.sin(t * 2), 30)
    # обломки на волне
    for i in range(6):
        fx = (i * 170 + t * 30) % W
        fy = 1180 + 18 * math.sin(t * 2 + i)
        cv.save()
        cv.c.rotate(20 + i * 12, fx, fy)
        cv.rrect(fx - 22, fy - 8, fx + 22, fy + 8, 3, fill="#8a5f2c", alpha=0.85)
        cv.restore()
    p = skia.Path()
    p.moveTo(0, 1120)
    p.cubicTo(280, 980 - 60 * ease(k), 760, 1040, W, 980 - 40 * ease(k))
    p.lineTo(W, H)
    p.lineTo(0, H)
    p.close()
    cv.path(p, fill=BEER, alpha=0.75)
    for i in range(8):
        cv.circle(200 + i * 120, 980 - 30 * math.sin(t * 3 + i), 10 + (i % 3) * 5,
                  fill=FOAM, alpha=0.4)

    if k > 0.06:
        a = ease((k - 0.06) / 0.2)
        label(cv, "ЦЕПНАЯ РЕАКЦИЯ", 46, 220, CREAM, alpha=a)
        label(cv, "СОРВАЛО СОСЕДНИЕ ЁМКОСТИ", 30, 278, GOLD, alpha=a)


def scene_street(cv, t, ctx):
    k = k_of(ctx, t, (26, 35))
    london(cv, t)
    lamp_post(cv, 220, t)
    # волна уже по грудь, окна подвалов залиты
    beer_wave(cv, t, 1080, 16)
    for i in range(3):
        x = 330 + i * 250
        cv.rrect(x, 1180, x + 120, 1330, 8, fill="#20180f", stroke="#4a3a26", width=3)
        cv.rrect(x + 8, 1180, x + 112, 1220, 6, fill=BEER_L, alpha=0.85)
    # люди в окнах верхних этажей и на крыше
    for i in range(3):
        x = 380 + i * 230
        cv.rrect(x - 30, 840, x + 30, 920, 6, fill="#2b3744", stroke="#4a3a26", width=3)
        cv.circle(x, 866, 13, fill=CREAM)
        cv.rrect(x - 13, 880, x + 13, 918, 8, fill="#33414f")
    for i in range(2):
        x = 300 + i * 480
        cv.circle(x, 700, 14, fill=CREAM)
        cv.rrect(x - 14, 714, x + 14, 774, 10, fill="#33414f")
    if k > 0.1:
        a = ease((k - 0.1) / 0.25)
        label(cv, "ПОДВАЛЫ ЗАТОПЛЕНЫ", 42, 240, CREAM, alpha=a)
        label(cv, "ЛЮДИ ЗАПЕРТЫ В ДОМАХ", 30, 296, "#ffb37a", alpha=a)


def scene_final(cv, t, ctx):
    k = k_of(ctx, t, (35, 43))
    london(cv, t, flash=0.2)
    beer_wave(cv, t, 1200, 12, alpha=0.9)
    if k > 0.05:
        a = ease((k - 0.05) / 0.25)
        cv.text("9", 540, 520, 300, fill="#ffffff", center=True, stroke=INK, stroke_w=14,
                glow=(GOLD, 26), alpha=a)
        label(cv, "ЧЕЛОВЕК ПОГИБЛИ", 44, 590, GOLD, alpha=a)
    if k > 0.45:
        a = ease((k - 0.45) / 0.3)
        label(cv, "ЭТО НЕ ВЫДУМКА", 40, 1180, CREAM, alpha=a)
        label(cv, "ПРОМЫШЛЕННАЯ КАТАСТРОФА", 28, 1230, "#ffb37a", alpha=a)


SCENES = {
    "hook": scene_hook,
    "vat": scene_vat,
    "burst": scene_burst,
    "street": scene_street,
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
