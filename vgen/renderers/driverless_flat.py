"""Город без водителей — flat design, 7 сцен по 55–60 с.

Палитра: бирюза, синий, оранжевый, белый, светло-серый.
Плоские заливки, чёткие контуры, мягкие тени, без фото и 3D.
Камера (наезды/панорамы/склейки) — в vgen/camera.py, здесь только композиция.
"""
import math
import random

import skia

from vgen.kit import Canvas, W, H, lin, rgba

TEAL = "#17B3A3"
BLUE = "#2D6CDF"
ORANGE = "#FF8A3D"
WHITE = "#FFFFFF"
GREY = "#E8EEF4"
GREY_D = "#C9D6E3"
INK = "#0F2438"
GREEN = "#3ECF8E"
RED = "#F2544B"
CREAM = "#FFF6E9"

SKY_TOP = "#DFF3F5"
SKY_BOT = "#F7FBFF"


def _sp(color, width, alph=255):
    return skia.Paint(AntiAlias=True, Color=rgba(color, alph / 255.0),
                      Style=skia.Paint.kStroke_Style, StrokeWidth=width,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def k_of(ctx, t, win):
    if ctx and ctx.get("scene_dur"):
        return max(0.0, min(1.0, ctx["scene_t"] / ctx["scene_dur"]))
    t0, t1 = win
    return max(0.0, min(1.0, (t - t0) / max(0.1, t1 - t0)))


def label(cv, s, size, y, color=INK, x=540, alpha=1.0, stroke=None, sw=0):
    cv.text(s, x, y, size, fill=color, center=True, alpha=alpha, stroke=stroke, stroke_w=sw)


def card(cv, x0, y0, x1, y1, fill=WHITE, r=22, shadow=True, stroke=None, sw=0):
    if shadow:
        cv.rrect(x0 + 5, y0 + 8, x1 + 5, y1 + 8, r, fill="#0F243818")
    cv.rrect(x0, y0, x1, y1, r, fill=fill, stroke=stroke, width=sw)


# ---------- общие объекты ----------

def car_top(cv, x, y, w=54, h=96, body=BLUE, t=0.0, roof=None, sensor=False, alpha=1.0):
    """Машина сверху: кузов, крыша, фары. sensor — лидар на крыше."""
    cv.rrect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, w * 0.28, fill=body, alpha=alpha,
             shadow=(0, 6, 10, "#0F243826"))
    cv.rrect(x - w * 0.3, y - h * 0.22, x + w * 0.3, y + h * 0.26, w * 0.18,
             fill=roof or "#0F2438", alpha=0.25 * alpha)
    cv.rrect(x - w * 0.34, y - h * 0.46, x + w * 0.34, y - h * 0.3, 4, fill=WHITE, alpha=0.85 * alpha)
    if sensor:
        cv.circle(x, y - h * 0.06, w * 0.16, fill=TEAL, alpha=alpha)
        cv.circle(x, y - h * 0.06, w * 0.1, fill=WHITE, alpha=alpha)
    # фары
    cv.circle(x - w * 0.3, y + h * 0.44, 4, fill="#FFF2C4", alpha=alpha)
    cv.circle(x + w * 0.3, y + h * 0.44, 4, fill="#FFF2C4", alpha=alpha)


def pedestrian(cv, x, y, s=1.0, alpha=1.0, color=ORANGE):
    cv.circle(x, y - 26 * s, 10 * s, fill=INK, alpha=alpha)
    cv.rrect(x - 9 * s, y - 14 * s, x + 9 * s, y + 12 * s, 7 * s, fill=color, alpha=alpha)
    cv.line(x - 8 * s, y + 12 * s, x - 12 * s, y + 30 * s, INK, 5 * s, alpha=alpha)
    cv.line(x + 8 * s, y + 12 * s, x + 12 * s, y + 30 * s, INK, 5 * s, alpha=alpha)


def tree(cv, x, y, s=1.0, alpha=1.0):
    cv.rrect(x - 4 * s, y, x + 4 * s, y + 26 * s, 2, fill="#9A6B45", alpha=alpha)
    cv.circle(x, y - 6 * s, 20 * s, fill=GREEN, alpha=alpha)
    cv.circle(x - 14 * s, y + 6 * s, 14 * s, fill="#35B77E", alpha=alpha)
    cv.circle(x + 14 * s, y + 6 * s, 14 * s, fill="#4BD79A", alpha=alpha)


_BG = {}


def _blocks(cv, greens):
    block = 240
    for gy in range(-1, 8):
        for gx in range(-1, 5):
            x = gx * block + 90
            y = gy * block + 90
            if x < -200 or x > W + 200:
                continue
            rnd = random.Random(gx * 31 + gy * 7)
            gr = rnd.random()
            if gr < greens * 0.55:
                cv.rrect(x, y, x + block - 40, y + block - 40, 18, fill="#D9F0E4")
                tree(cv, x + 60, y + 80, 1.0)
                tree(cv, x + 140, y + 150, 0.85)
                cv.rrect(x + 40, y + 150, x + 130, y + 200, 8, fill="#B7E4CD")
            else:
                h = 60 + rnd.randint(0, 80)
                cv.rrect(x, y + (140 - h), x + block - 60, y + block - 40, 14, fill=GREY)
                cv.rrect(x + 14, y + (140 - h) + 18, x + block - 74, y + block - 70, 10,
                         fill="#DCE8F3")
                for i in range(3):
                    cv.rect(x + 24 + i * 34, y + block - 96, x + 50 + i * 34, y + block - 66,
                            fill="#B9D3E8")
    road_w = 70
    for gx in range(0, 5):
        cv.rect(gx * block + 40 - road_w / 2, 0, gx * block + 40 + road_w / 2, H,
                fill="#CBD8E4")
    for gy in range(0, 7):
        cv.rect(0, gy * block + 40 - road_w / 2, W, gy * block + 40 + road_w / 2,
                fill="#CBD8E4")


def city_bg(greens):
    key = round(greens, 2)
    if key not in _BG:
        c2 = Canvas()
        c2.rect(0, 0, W, H, fill=SKY_BOT)
        _blocks(c2, greens)
        _BG[key] = c2.surface.makeImageSnapshot()
    return _BG[key]


def city_top(cv, t, greens=0.0, jam=0.0, sensors=False, offset=0.0, cars=True):
    """Город сверху: кэш кварталов + движущиеся машины."""
    cv.c.drawImage(city_bg(greens), 0, 0)

    block = 240
    if cars:
        for i in range(16):
            lane = i % 5
            vertical = i % 2 == 0
            speed = 0.09 + (i % 3) * 0.03
            p = ((i * 0.137 + t * speed) % 1.0)
            if vertical:
                x = lane * block + 40 + offset + (14 if i % 4 else -14)
                y = p * H
                car_top(cv, x, y, 26, 48, [BLUE, TEAL, ORANGE][i % 3], sensor=sensors)
            else:
                x = p * W
                y = (i % 7) * block + 40 + (14 if i % 4 else -14)
                cv.save()
                cv.c.rotate(90, x, y)
                car_top(cv, x, y, 26, 48, [TEAL, BLUE, GREY_D][i % 3], sensor=sensors)
                cv.restore()

    if jam > 0.01:
        for i in range(8):
            x = 40 + i * 70 + offset
            cv.circle(x, 640, 9, fill=RED, alpha=0.75 * jam)
            cv.circle(x, 640, 18, fill=RED, alpha=0.18 * jam, blur=8)


def signal_arc(cv, x1, y1, x2, y2, p, color=TEAL):
    if p <= 0:
        return
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 40
    path = skia.Path()
    path.moveTo(x1, y1)
    path.quadTo(mx, my, x2, y2)
    cv.c.drawPath(path, _sp(color, 3, int(180 * min(1, p))))


# ---------- сцены ----------

def scene_today(cv, t, ctx):
    k = k_of(ctx, t, (0, 6))
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, SKY_TOP), (1, SKY_BOT)]))
    city_top(cv, t, greens=0.0, jam=1.0)
    # пробка крупным планом сверху
    for i in range(6):
        car_top(cv, 200 + i * 130, 700 + 20 * math.sin(t * 1.5 + i), 70, 120,
                [BLUE, TEAL, ORANGE][i % 3])
        cv.circle(200 + i * 130, 760, 10, fill=RED, alpha=0.8)
    # светофоры
    for i, x in enumerate((140, 540, 900)):
        cv.rrect(x - 16, 300, x + 16, 400, 8, fill=INK)
        cv.circle(x, 320, 9, fill=RED if int(t * 2 + i) % 2 else "#3A4A5E")
        cv.circle(x, 350, 9, fill="#3A4A5E")
        cv.circle(x, 380, 9, fill=GREEN if int(t * 2 + i) % 2 else "#3A4A5E")
    pedestrian(cv, 470, 980, 1.0)
    pedestrian(cv, 610, 1020, 0.9, color=BLUE)

    if k > 0.05:
        a = ease((k - 0.05) / 0.2)
        cv.text("СЕГОДНЯ", 540, 200, 120, fill=INK, center=True, alpha=a)
        label(cv, "ПРОБКИ И СВЕТОФОРЫ", 42, 1160, BLUE, alpha=a)
    if k > 0.5:
        label(cv, "30% ТРАФИКА — ПОИСК ПАРКОВКИ", 34, 1230, ORANGE,
              alpha=ease((k - 0.5) / 0.3))


def scene_gone(cv, t, ctx):
    k = k_of(ctx, t, (6, 13))
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, SKY_TOP), (1, SKY_BOT)]))
    city_top(cv, t, sensors=k > 0.4)

    # водители «исчезают»: серые силуэты тают
    for i in range(4):
        x = 210 + i * 210
        y = 820
        fade = max(0.0, 1.0 - k * 2.2 - i * 0.05)
        if fade > 0.02:
            cv.circle(x, y - 30, 22, fill="#7A8FA6", alpha=0.55 * fade)
            cv.rrect(x - 20, y - 8, x + 20, y + 40, 12, fill="#7A8FA6", alpha=0.45 * fade)
        # сенсор на крыше появляется
        sp = ease((k - 0.35) / 0.3)
        if sp > 0:
            car_top(cv, x, y, 76, 130, [BLUE, TEAL, ORANGE][i % 3], sensor=False)
            cv.circle(x, y - 8, 10, fill=TEAL, alpha=sp)
            for r in (26, 44, 62):
                cv.circle(x, y - 8, r * sp, stroke=TEAL, width=2, alpha=0.35 * sp)

    if k > 0.1:
        a = ease((k - 0.1) / 0.25)
        label(cv, "ВОДИТЕЛИ ИСЧЕЗАЮТ", 44, 250, INK, alpha=a)
        label(cv, "ЛИДАРЫ И КАМЕРЫ НА КРЫШЕ", 32, 1160, BLUE, alpha=a)


def scene_smart(cv, t, ctx):
    k = k_of(ctx, t, (13, 22))
    cv.rect(0, 0, W, H, fill="#EEF6FF")
    # дорога сверху
    cv.rect(0, 640, W, 1280, fill="#CBD8E4")
    for i in range(6):
        y = 660 + i * 100
        cv.line(0, y, W, y, "#E9F1F8", 3, alpha=0.8)
    # поток: три машины в ряд, синхронно
    for i in range(3):
        x = 150 + i * 330
        y = 900 + 10 * math.sin(t * 2 + i)
        car_top(cv, x, y, 82, 140, [BLUE, TEAL, ORANGE][i % 3], sensor=True)
    # сигналы между машинами
    for i in range(2):
        signal_arc(cv, 190 + i * 330, 830, 480 + i * 330, 830,
                   ((t * 0.7 + i * 0.4) % 1.0))
    # пешеход переходит, машина уступает
    pedestrian(cv, 540, 1260 - 40 * math.sin(t * 1.2), 1.2, color=ORANGE)
    cv.circle(540, 1180, 60 + 8 * math.sin(t * 3), stroke=GREEN, width=4, alpha=0.5)
    # схема сети
    nodes = [(160, 420), (400, 360), (640, 400), (880, 340)]
    for i in range(len(nodes) - 1):
        signal_arc(cv, *nodes[i], *nodes[i + 1], 1.0)
    for (x, y) in nodes:
        cv.circle(x, y, 12, fill=TEAL)
        cv.circle(x, y, 22, stroke=TEAL, width=2, alpha=0.4)

    if k > 0.08:
        a = ease((k - 0.08) / 0.25)
        label(cv, "МАШИНЫ ДОГОВАРИВАЮТСЯ", 42, 220, INK, alpha=a)
        label(cv, "УСТУПАЮТ И ТОРМОЗЯТ САМИ", 32, 1390, BLUE, alpha=a)


def scene_change(cv, t, ctx):
    k = k_of(ctx, t, (22, 32))
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, SKY_TOP), (1, "#F2FFF8")]))
    # парковка превращается в парк
    morph = ease(k / 0.75)
    cv.rect(0, 0, W, H, fill="#E7EDF4")
    # места парковки
    for r in range(4):
        for c in range(4):
            x = 90 + c * 230
            y = 260 + r * 230
            if (r * 4 + c) / 16.0 < morph:
                cv.rrect(x, y, x + 200, y + 200, 18, fill="#D9F0E4")
                tree(cv, x + 60, y + 90, 1.0)
                tree(cv, x + 150, y + 140, 0.8)
            else:
                cv.rrect(x, y, x + 200, y + 200, 12, fill="#DDE6EF")
                cv.rrect(x + 40, y + 60, x + 160, y + 150, 10, fill="#B9C9D8")
                cv.text("P", x + 100, y + 135, 54, fill=WHITE, center=True)

    # машины уезжают с парковки
    for i in range(4):
        p = min(1.0, max(0.0, k * 1.6 - i * 0.18))
        if 0 < p < 1:
            cv.rrect(120 + i * 230 + 60 * p, 300 + 230 * (i % 3) - 120 * p, 260 + i * 230,
                     420 + 230 * (i % 3) - 120 * p, 10, fill=BLUE, alpha=0.9 * (1 - p))

    # велодорожка и такси
    cv.rect(0, 1240, W, 1330, fill="#C6F0E2")
    for i in range(10):
        cv.rect(40 + i * 110, 1278, 110 + i * 110, 1292, fill="#8FDCC4")
    car_top(cv, 540, 1430, 96, 170, TEAL, sensor=True)
    cv.circle(540, 1430, 120, stroke=TEAL, width=3, alpha=0.25)
    cv.text("ТАКСИ", 540, 1500, 34, fill=INK, center=True)

    if k > 0.12:
        a = ease((k - 0.12) / 0.25)
        label(cv, "ПАРКОВКИ — В ПАРКИ", 46, 190, INK, alpha=a)
        label(cv, "ТАКСИ ПРИЕЗЖАЕТ ПО ЗАПРОСУ", 30, 1640, BLUE, alpha=a)


def scene_logistics(cv, t, ctx):
    k = k_of(ctx, t, (32, 42))
    cv.rect(0, 0, W, H, fill="#EEF6FF")

    # склад сверху
    cv.rrect(60, 120, 1020, 460, 22, fill=GREY)
    cv.rrect(90, 150, 990, 260, 14, fill="#D7E3EF")
    for i in range(6):
        cv.rect(110 + i * 148, 150, 230 + i * 148, 260, fill="#C3D4E4")
    cv.text("СКЛАД", 540, 330, 44, fill=INK, center=True)
    cv.text("ЗАКАЗЫ → МАРШРУТ → ДОСТАВКА", 540, 392, 26, fill=BLUE, center=True)
    # конвейер с посылками
    cv.rect(120, 420, 960, 470, fill="#B9C9D8")
    for i in range(7):
        p = ((i / 7 + t * 0.3) % 1.0)
        x = 120 + 840 * p
        cv.rrect(x, 424, x + 54, 464, 6, fill=ORANGE)
        cv.line(x + 8, 444, x + 46, 444, WHITE, 3, alpha=0.7)

    # дорога с грузовиком
    cv.rect(0, 520, W, 780, fill="#CBD8E4")
    for i in range(5):
        cv.line(0, 540 + i * 50, W, 540 + i * 50, "#E9F1F8", 2, alpha=0.6)
    tx = 60 + ((t * 150) % 900)
    cv.rrect(tx, 580, tx + 300, 700, 16, fill=ORANGE, shadow=(0, 8, 12, "#0F243826"))
    cv.rrect(tx + 300, 606, tx + 390, 700, 12, fill=BLUE)
    cv.text("ГРУЗ", tx + 150, 650, 38, fill=WHITE, center=True)
    for wx in (tx + 60, tx + 150, tx + 340):
        cv.circle(wx, 706, 22, fill=INK)
        cv.circle(wx, 706, 9, fill=GREY)

    # тротуар и роботы-курьеры
    cv.rect(0, 800, W, 980, fill="#DCE7F1")
    for i in range(3):
        rx = 120 + i * 330 + 40 * math.sin(t * 1.2 + i)
        cv.rrect(rx - 44, 860, rx + 44, 940, 14, fill=WHITE, stroke=INK, width=4)
        cv.circle(rx - 20, 952, 11, fill=INK)
        cv.circle(rx + 20, 952, 11, fill=INK)
        cv.circle(rx, 846, 8, fill=TEAL)
        cv.rrect(rx - 16, 884, rx + 16, 916, 5, fill=ORANGE)

    # сеть и узлы
    for i in range(3):
        signal_arc(cv, 180 + i * 330, 1020, 340 + i * 330, 1020, ((t + i * 0.3) % 1), BLUE)
    for i in range(3):
        cv.circle(180 + i * 330, 1020, 10, fill=BLUE)
        cv.circle(340 + i * 330, 1020, 10, fill=BLUE)

    # нижняя полоса: цифры
    cv.rrect(120, 1120, 960, 1300, 20, fill=WHITE, shadow=(0, 8, 12, "#0F243826"))
    cv.text("24/7", 300, 1230, 74, fill=TEAL, center=True)
    cv.text("без водителя", 300, 1270, 26, fill=INK, center=True)
    cv.text("40 мин", 760, 1230, 66, fill=ORANGE, center=True)
    cv.text("время доставки", 760, 1270, 26, fill=INK, center=True)

    if k > 0.1:
        a = ease((k - 0.1) / 0.25)
        label(cv, "ЛОГИСТИКА БЕЗ ЛЮДЕЙ", 44, 1400, INK, alpha=a)
        label(cv, "ОДНА СЕТЬ НА ВЕСЬ ГОРОД", 30, 1456, BLUE, alpha=a)


def scene_fail(cv, t, ctx):
    k = k_of(ctx, t, (42, 51))
    cv.rect(0, 0, W, H, fill="#0F2438")
    # большая панель диспетчерской
    cv.rrect(50, 140, 1030, 900, 26, fill="#16324A")
    cv.rrect(70, 160, 1010, 300, 18, fill="#0B1B2A")
    cv.text("ДИСПЕТЧЕРСКИЙ ЦЕНТР", 540, 245, 40, fill=WHITE, center=True)
    blink = 0.55 + 0.45 * abs(math.sin(t * 4))
    cv.circle(900, 230, 14, fill=RED, alpha=blink)

    for i in range(3):
        x = 90 + i * 320
        cv.rrect(x, 330, x + 290, 620, 16, fill="#0B1B2A")
        p = skia.Path()
        for j in range(18):
            xx = x + 24 + j * 14
            yy = 520 - 55 * math.sin(j * 0.6 + t * 3 + i)
            (p.moveTo if j == 0 else p.lineTo)(xx, yy)
        cv.c.drawPath(p, _sp(TEAL if i != 1 else RED, 3))
        cv.text(["СВЯЗЬ", "ЗАДЕРЖКА", "МАРШРУТЫ"][i], x + 24, 360, 24, fill="#9FD8FF")

    # тревоги списком
    alerts = [("СБОЙ СЕТИ", RED), ("ПОТЕРЯ СВЯЗИ", ORANGE), ("КИБЕРАТАКА", RED)]
    for i, (txt, col) in enumerate(alerts):
        a = min(1.0, max(0.0, (t * 0.9 + i * 0.15) % 1.6))
        cv.rrect(90, 650 + i * 80, 990, 716 + i * 80, 14, fill="#0B1B2A", alpha=0.9)
        cv.circle(130, 683 + i * 80, 12, fill=col, alpha=blink)
        cv.text(txt, 170, 696 + i * 80, 32, fill=WHITE)

    # машины встают
    for i in range(4):
        x = 170 + i * 220
        y = 1120
        car_top(cv, x, y, 74, 128, [BLUE, TEAL, ORANGE][i % 3], sensor=True, alpha=0.92)
        cv.circle(x, y, 84, stroke=RED if i % 2 == 0 else ORANGE, width=4, alpha=0.55)
        cv.text("STOP", x, y + 8, 20, fill=WHITE, center=True, alpha=0.9)

    if k > 0.15:
        a = ease((k - 0.15) / 0.3)
        label(cv, "СБОЙ СЕТИ", 52, 70, WHITE, alpha=a)
        label(cv, "ЧАСТЬ МАШИН ВСТАЁТ В БЕЗОПАСНОМ РЕЖИМЕ", 24, 980, "#FFD1CC", alpha=a)


def scene_final(cv, t, ctx):
    k = k_of(ctx, t, (51, 60))
    dawn = ease(k)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H,
                                 [(0, "#CFEFF2"), (0.55, "#EAF7FF"), (1, "#FFF3E4")]))
    cv.circle(820, 320, 130, fill="#FFD9A0", alpha=0.7)
    city_top(cv, t, greens=1.0, sensors=True, offset=0)
    # люди гуляют
    for i in range(5):
        pedestrian(cv, 160 + i * 190, 1500 + 8 * math.sin(t * 2 + i), 1.0,
                   color=[ORANGE, BLUE, TEAL][i % 3])
    cv.rect(0, 1560, W, H, fill="#E9F6EE", alpha=0.85)

    if k > 0.05:
        a = ease((k - 0.05) / 0.25)
        cv.text("НОВАЯ СИСТЕМА", 540, 1180, 64, fill=INK, center=True, alpha=a)
    if k > 0.35:
        a = ease((k - 0.35) / 0.25)
        label(cv, "ГОТОВЫ ЛИ МЫ ДОВЕРИТЬ ЕЙ ЖИЗНИ?", 34, 1250, BLUE, alpha=a)


SCENES = {
    "today": scene_today,
    "gone": scene_gone,
    "smart": scene_smart,
    "change": scene_change,
    "logistics": scene_logistics,
    "fail": scene_fail,
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
    # плашка под субтитр
    cv.rrect(540 - width / 2 - 26, 1760, 540 + width / 2 + 26, 1846, 18, fill="#0F2438", alpha=0.82)
    for w in words:
        col = "#FFD08A" if any(h.lower() in w.lower() for h in hl) else WHITE
        cv.text(w, x, 1822, size, fill=col)
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
