"""Город без водителей: поток машин, парковки, улицы, перекрёстки. Skia-рендер.

Детализация намеренно простая — важна динамика: машины едут, свет тянется,
камера ведёт кадр. Интерфейс: render(name, t, ctx) -> PIL.Image 1080x1920.
"""
import math
import random

import skia

from vgen.kit import Canvas, W, H, lin, rad, rgba

INK = "#050a14"
DEEP = "#0a1626"
ROAD = "#141f2e"
LANE = "#3a4a5e"
CYAN = "#67e8ff"
GOLD = "#ffc45e"
CREAM = "#f3f7ff"
RED = "#ff5a4a"
GREEN = "#3ee08a"


def _sp(color, width, alph=255):
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


# ---------- фон ----------

def skyline(cv, base, t, lit=True):
    rnd = random.Random(7)
    x = -40
    while x < W + 40:
        w = rnd.randint(70, 150)
        h = rnd.randint(160, 420)
        cv.rect(x, base - h, x + w, base, fill="#0d1826")
        win = skia.Path()
        for wy in range(int(base - h + 16), int(base) - 14, 26):
            for wx in range(int(x + 10), int(x + w - 10), 22):
                if rnd.random() < 0.35:
                    win.addRect(skia.Rect(wx, wy, wx + 8, wy + 12))
        if lit:
            cv.path(win, fill="#ffcf7a", alpha=0.55)
        x += w + rnd.randint(8, 26)


def road_persp(cv, t, hz=620):
    """Дорога с перспективой: сходятся края, разметка бежит навстречу."""
    cv.poly([(0, H), (W, H), (700, hz), (380, hz)], fill=ROAD)
    cv.poly([(0, H), (300, H), (470, hz), (380, hz)], fill="#101a27")
    cv.poly([(W, H), (780, H), (700, hz), (610, hz)], fill="#101a27")
    # разметка: пунктир, бегущий вниз
    for i in range(14):
        p = ((i / 14 + t * 0.6) % 1.0)
        y1 = hz + (H - hz) * p
        y2 = hz + (H - hz) * min(1.0, p + 0.045)
        x1 = 540 + (y1 - hz) * 0.02
        x2 = 540 + (y2 - hz) * 0.02
        w1 = 3 + (y1 - hz) * 0.02
        cv.line(x1, y1, x2, y2, "#dbe6f2", w1, alpha=0.8)


def car_front(cv, x, y, s, t, color=CYAN, glow=True):
    """Машина «навстречу»: тёмный силуэт, фары, блик."""
    cv.rrect(x - 46 * s, y - 20 * s, x + 46 * s, y + 26 * s, 12 * s, fill="#0b1220")
    cv.rrect(x - 34 * s, y - 44 * s, x + 34 * s, y - 6 * s, 10 * s, fill="#16233a")
    for dx in (-30, 30):
        if glow:
            cv.circle(x + dx * s, y + 18 * s, 26 * s, fill=color, alpha=0.18, blur=18 * s)
        cv.circle(x + dx * s, y + 18 * s, 6 * s, fill="#ffffff")


def car_top(cv, x, y, w, h, color, t, glow=True):
    cv.rrect(x, y, x + w, y + h, 6, fill=color)
    cv.rrect(x + 6, y + 4, x + w - 6, y + h * 0.45, 4, fill="#0b1220", alpha=0.55)
    if glow:
        cv.rrect(x, y + h - 12, x + w, y + h, 4, fill=CYAN, alpha=0.35, blur=6)


# ---------- сцены ----------

def scene_hook(cv, t, ctx):
    k = k_of(ctx, t, (0, 7))
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#03060d"), (0.55, "#0a1626"), (1, "#132033")]))
    skyline(cv, 700, t)
    cv.rect(0, 690, W, H, fill="#0b1420")
    road_persp(cv, t, 640)
    # машины навстречу, разного масштаба
    for i in range(7):
        p = ((i * 0.19 + t * 0.55) % 1.0)
        y = 660 + (H - 660) * (p ** 1.7)
        s = 0.25 + p * 1.5
        x = 540 + (i - 3) * 120 * (0.3 + p)
        car_front(cv, x, y, s, t)
    # свет фар тянется по асфальту
    for i in range(5):
        p = ((i * 0.27 + t * 0.45) % 1.0)
        y = 700 + (H - 700) * p
        cv.line(540 - 150, y, 540 + 150, y, CYAN, 2, alpha=0.12)

    if k > 0.05:
        a = ease((k - 0.05) / 0.2)
        cv.text("ГОРОД", 540, 300, 150, fill="#ffffff", center=True, stroke=INK, stroke_w=14, alpha=a)
        cv.text("БЕЗ ВОДИТЕЛЕЙ", 540, 440, 96, fill=GOLD, center=True, stroke=INK, stroke_w=12, alpha=a)
    if k > 0.45:
        label(cv, "МАШИНЫ БЕЗ РУЛЯ МЕНЯЮТ УЛИЦЫ", 34, 530, "#9fd8ff",
              alpha=ease((k - 0.45) / 0.3))


def scene_parking(cv, t, ctx):
    k = k_of(ctx, t, (7, 16))
    cv.rect(0, 0, W, H, fill="#070e18")
    # вид сверху: квартал и парковка
    cv.rect(0, 0, W, 380, fill="#0b1522")
    skyline(cv, 380, t, lit=True)
    lot = (80, 420, 1000, 1180)
    cv.rect(*lot, fill="#101a28")
    # разметка парковки
    for r in range(4):
        for c in range(6):
            x = 110 + c * 148
            y = 450 + r * 180
            cv.line(x, y, x, y + 150, LANE, 2, alpha=0.5)

    # машины уезжают: парковка пустеет, на её месте поднимается квартал
    left = int(24 * (1 - ease(k / 0.8)))
    idx = 0
    for r in range(4):
        for c in range(6):
            idx += 1
            if idx > left:
                continue
            x = 118 + c * 148
            y = 460 + r * 180
            cv.rrect(x, y, x + 110, y + 60, 8, fill="#2b3b52")
            cv.rrect(x + 10, y + 8, x + 100, y + 32, 6, fill="#0d1624", alpha=0.6)
            cv.circle(x + 22, y + 52, 8, fill="#0a1119")

    # новый квартал
    grow = ease((k - 0.25) / 0.6)
    if grow > 0.02:
        for i in range(5):
            bx = 120 + i * 180
            bh = 120 * grow + 60 * (i % 3)
            cv.rrect(bx, 1180 - bh, bx + 140, 1180, 12, fill="#1c2c42", alpha=min(1.0, grow * 1.4))
            cv.rrect(bx + 16, 1180 - bh + 18, bx + 124, 1160, 8, fill="#ffcf7a", alpha=0.28 * grow)

    if k > 0.12:
        a = ease((k - 0.12) / 0.25)
        label(cv, "ПАРКОВКИ УХОДЯТ С УЛИЦ", 40, 1320, CREAM, alpha=a)
        label(cv, "НА ИХ МЕСТЕ — ДОМА И СКВЕРЫ", 36, 1388, "#d6ecff", alpha=a)
    label(cv, "95% ВРЕМЕНИ МАШИНА СТОИТ", 32, 1650, GOLD, alpha=0.95)


def scene_streets(cv, t, ctx):
    k = k_of(ctx, t, (16, 25))
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#050b14"), (1, "#0d1a2a")]))
    skyline(cv, 620, t)
    # улица сверху: полосы сужаются, появляются деревья и велодорожка
    shrink = ease(k / 0.7)
    road_w = 620 - 200 * shrink
    x0 = 540 - road_w / 2
    cv.rect(x0, 660, x0 + road_w, H, fill=ROAD)
    cv.line(x0 + 6, 660, x0 + 6, H, "#2a3a4e", 3)
    cv.line(x0 + road_w - 6, 660, x0 + road_w - 6, H, "#2a3a4e", 3)
    # полосы
    for i in range(3):
        x = x0 + road_w * (i + 1) / 4
        for j in range(9):
            p = ((j / 9 + t * 0.5) % 1.0)
            y = 700 + (H - 700) * p
            cv.line(x, y, x, y + 46, "#dbe6f2", 3, alpha=0.5)
    # машины едут плотным потоком
    for i in range(10):
        p = ((i * 0.11 + t * 0.42) % 1.0)
        y = 680 + (H - 680) * p
        lane = i % 3
        x = x0 + road_w * (lane + 0.5) / 3
        s = 0.4 + p * 1.2
        cv.rrect(x - 32 * s, y, x + 32 * s, y + 54 * s, 8 * s, fill=["#2b6fff", "#22c1a6", "#ff8a4a"][i % 3],
                 alpha=0.9)
        cv.rrect(x - 24 * s, y + 8 * s, x + 24 * s, y + 26 * s, 6 * s, fill="#0b1220", alpha=0.5)

    # велодорожка и деревья появляются
    if shrink > 0.15:
        a = min(1.0, (shrink - 0.15) / 0.5)
        bx = x0 - 54
        cv.rect(bx, 660, bx + 40, H, fill="#123a2e", alpha=0.85 * a)
        for j in range(7):
            yy = 700 + j * 170
            cv.circle(bx + 20, yy, 16 * a + 4, fill=GREEN, alpha=0.75 * a)
        cv.circle(bx + 20, 640, 10, fill="#ffd479", alpha=a)

    if k > 0.1:
        a = ease((k - 0.1) / 0.25)
        label(cv, "ПОЛОСЫ СТАНОВЯТСЯ УЖЕ", 38, 300, CREAM, alpha=a)
        label(cv, "МЕСТО — ПЕШЕХОДАМ И ДЕРЕВЬЯМ", 34, 366, "#d6ecff", alpha=a)


def scene_cross(cv, t, ctx):
    k = k_of(ctx, t, (25, 34))
    cv.rect(0, 0, W, H, fill="#050b14")
    cx, cy = 540, 900
    # перекрёсток сверху
    cv.rect(0, cy - 150, W, cy + 150, fill=ROAD)
    cv.rect(cx - 150, 0, cx + 150, H, fill=ROAD)
    cv.rect(cx - 150, cy - 150, cx + 150, cy + 150, fill="#111c2b")
    # зебра
    for i in range(7):
        cv.rect(cx - 130 + i * 38, cy - 150, cx - 116 + i * 38, cy - 30, fill="#dbe6f2", alpha=0.25)
        cv.rect(cx - 130 + i * 38, cy + 30, cx - 116 + i * 38, cy + 150, fill="#dbe6f2", alpha=0.25)

    # машины проезжают перекрёсток без остановки, «договариваясь»
    for i in range(6):
        p = ((i / 6 + t * 0.35) % 1.0)
        x = -200 + (W + 400) * p
        cv.rrect(x, cy - 110, x + 150, cy - 40, 10, fill=["#2b6fff", "#ff8a4a", "#22c1a6"][i % 3],
                 stroke="#e8f2ff", width=2)
        cv.rrect(x + 16, cy - 100, x + 60, cy - 50, 6, fill="#0b1220", alpha=0.5)
        cv.line(x + 150, cy - 75, x + 210, cy - 75, CYAN, 3, alpha=0.4)
    for i in range(4):
        p = ((i / 4 + t * 0.28 + 0.4) % 1.0)
        y = -200 + (H + 400) * p
        cv.rrect(cx - 110, y, cx - 40, y + 150, 10, fill=["#22c1a6", "#ffd479"][i % 2],
                 stroke="#e8f2ff", width=2)
        cv.line(cx - 75, y + 150, cx - 75, y + 210, CYAN, 3, alpha=0.4)

    # бордюры и стрелки — геометрия читается
    cv.rect(cx - 150, cy - 150, cx + 150, cy + 150, stroke="#2f4459", width=4)
    cv.line(cx - 150, 0, cx - 150, H, "#2f4459", 4)
    cv.line(cx + 150, 0, cx + 150, H, "#2f4459", 4)
    cv.line(0, cy - 150, W, cy - 150, "#2f4459", 4)
    cv.line(0, cy + 150, W, cy + 150, "#2f4459", 4)
    for ax in (300, 780):
        cv.poly([(ax, cy - 60), (ax + 40, cy - 90), (ax, cy - 120)], fill="#9fd8ff", alpha=0.35)
        cv.poly([(ax, cy + 60), (ax - 40, cy + 90), (ax, cy + 120)], fill="#9fd8ff", alpha=0.35)
    # радиусы связи между машинами
    for i in range(3):
        r = 90 + 40 * math.sin(t * 2 + i)
        cv.circle(cx, cy, r, stroke=CYAN, width=2, alpha=0.22)

    if k > 0.2:
        a = ease((k - 0.2) / 0.3)
        label(cv, "СВЕТОФОРЫ ПОЧТИ НЕ НУЖНЫ", 38, 240, CREAM, alpha=a)
        label(cv, "МАШИНЫ ДОГОВАРИВАЮТСЯ САМИ", 34, 306, "#d6ecff", alpha=a)
    label(cv, "ПЕРЕКРЁСТОК БЕЗ ОСТАНОВОК", 32, 1700, GOLD, alpha=0.95)


def scene_safety(cv, t, ctx):
    k = k_of(ctx, t, (34, 43))
    cv.rect(0, 0, W, H, fill="#050b14")
    skyline(cv, 700, t, lit=False)
    road_persp(cv, t, 640)
    # зоны видимости автопилота
    for i in range(3):
        y = 760 + i * 200
        cv.poly([(540 - 90 - i * 40, y), (540 + 90 + i * 40, y),
                 (540 + 260 + i * 60, y + 180), (540 - 260 - i * 60, y + 180)],
                fill=CYAN, alpha=0.05 + 0.02 * i)
    car_front(cv, 540, 1120, 1.4, t)
    for a in (0.35, 0.7, 1.0):
        r = 140 + 60 * math.sin(t * 1.6 + a)
        cv.circle(540, 1120, r * a, stroke=GREEN, width=3, alpha=0.28)

    if k > 0.15:
        a = ease((k - 0.15) / 0.3)
        label(cv, "94% АВАРИЙ — ОШИБКА ЧЕЛОВЕКА", 40, 320, CREAM, alpha=a)
        label(cv, "У АВТОПИЛОТА РЕАКЦИЯ БЫСТРЕЕ", 30, 380, GREEN, alpha=a)
    if k > 0.55:
        label(cv, "НО ПЕРЕХОДНЫЙ ПЕРИОД — САМЫЙ ОПАСНЫЙ", 28, 1660, RED,
              alpha=ease((k - 0.55) / 0.3))


def scene_final(cv, t, ctx):
    k = k_of(ctx, t, (43, 52))
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#040810"), (0.6, "#0a1626"), (1, "#14243a")]))
    # сетка кварталов сверху
    for i in range(5):
        y = 300 + i * 300
        cv.rect(0, y, W, y + 120, fill="#101c2b")
    for i in range(4):
        x = 140 + i * 260
        cv.rect(x, 0, x + 120, H, fill="#101c2b")
    # поток машин по сетке
    for i in range(14):
        p = ((i / 14 + t * 0.22) % 1.0)
        horiz = i % 2 == 0
        if horiz:
            y = 330 + (i % 5) * 300
            x = -100 + (W + 200) * p
            cv.rrect(x, y + 30, x + 110, y + 86, 8, fill=[CYAN, "#2b6fff", GOLD][i % 3], alpha=0.85)
        else:
            x = 170 + (i % 4) * 260
            y = -100 + (H + 200) * p
            cv.rrect(x + 30, y, x + 86, y + 110, 8, fill=[CYAN, "#22c1a6", GOLD][i % 3], alpha=0.85)
    # светящиеся «умные» перекрёстки
    for i in range(4):
        for j in range(5):
            cv.circle(170 + i * 260, 330 + j * 300, 8 + 3 * math.sin(t * 3 + i + j), fill=CYAN, alpha=0.5)

    # переход к рассвету
    dawn = ease((k - 0.35) / 0.5)
    if dawn > 0.02:
        cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#ffb26b"), (1, "#ff8a5c")]),
                alpha=0.16 * dawn)

    if k > 0.1:
        a = ease((k - 0.1) / 0.3)
        label(cv, "ГОРОД СТАНОВИТСЯ ТИШЕ", 44, 1300, CREAM, alpha=a)
        label(cv, "И БОЛЬШЕ МЕСТА — ЛЮДЯМ", 32, 1370, GOLD, alpha=a)


SCENES = {
    "hook": scene_hook,
    "parking": scene_parking,
    "streets": scene_streets,
    "cross": scene_cross,
    "safety": scene_safety,
    "final": scene_final,
}


def caption(cv, text, hl):
    if not text:
        return
    size = 52
    words = text.split()
    width = sum(cv.text_w(w + " ", size) for w in words)
    while width > 940 and size > 28:
        size -= 3
        width = sum(cv.text_w(w + " ", size) for w in words)
    x = 540 - width / 2
    for w in words:
        col = GOLD if any(h.lower() in w.lower() for h in hl) else CREAM
        cv.text(w, x, 1790, size, fill=col, stroke=INK, stroke_w=7,
                shadow=(0, 4, 10, "#000000cc"))
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
