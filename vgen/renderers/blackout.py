"""«Что будет, если исчезнет электричество на неделю» — разноцветный flat vector.

Палитра яркая, фон кремовый, толстые обводки, простые человечки. Skia через vgen.kit.
Интерфейс: render(name, t, ctx) -> PIL.Image 1080x1920.
"""
import math

import skia

from vgen.kit import Canvas, W, H, lin, rad, rgba

INK = "#1B1B2F"
CREAM = "#FFF6E9"
CORAL = "#FF6B5A"
TEAL = "#17B3A3"
YELLOW = "#FFC93C"
BLUE = "#3D7BFF"
PURPLE = "#8B5CF6"
GREEN = "#3ECF8E"
GREY = "#C9C6D8"
WHITE = "#FFFFFF"


def _sp(color, width, alph=255):
    return skia.Paint(AntiAlias=True, Color=rgba(color, alph / 255.0),
                      Style=skia.Paint.kStroke_Style, StrokeWidth=width,
                      StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap)


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def k_of(ctx, t, win):
    if ctx and ctx.get("scene_dur"):
        return max(0.0, min(1.0, ctx["scene_t"] / ctx["scene_dur"]))
    t0, t1 = win
    return max(0.0, min(1.0, (t - t0) / max(0.1, t1 - t0)))


def card(cv, x0, y0, x1, y1, fill=WHITE, r=26, shadow=True):
    if shadow:
        cv.rrect(x0 + 6, y0 + 10, x1 + 6, y1 + 10, r, fill="#00000018")
    cv.rrect(x0, y0, x1, y1, r, fill=fill, stroke=INK, width=6)


def person(cv, x, y, s=1.0, body=CORAL, phase=0.0):
    """Простой человечек: голова, туловище, руки-ноги."""
    bob = 4 * math.sin(phase)
    cv.circle(x, y - 96 * s + bob, 22 * s, fill=YELLOW, stroke=INK, width=5 * s)
    cv.rrect(x - 26 * s, y - 68 * s + bob, x + 26 * s, y + 6 * s, 16 * s,
             fill=body, stroke=INK, width=5 * s)
    cv.line(x - 26 * s, y - 46 * s + bob, x - 46 * s, y - 16 * s + bob, INK, 7 * s)
    cv.line(x + 26 * s, y - 46 * s + bob, x + 46 * s, y - 16 * s + bob, INK, 7 * s)
    cv.line(x - 12 * s, y + 6 * s, x - 18 * s, y + 44 * s, INK, 8 * s)
    cv.line(x + 12 * s, y + 6 * s, x + 18 * s, y + 44 * s, INK, 8 * s)


def drift(cv, t, color=CORAL, n=16, y0=200, y1=1700, alpha=0.35, r=6):
    """Медленно летящие точки — кадр не стоит, даже если сцена статичная."""
    for i in range(n):
        px = ((i * 137 + t * 90) % (W + 120)) - 60
        py = y0 + ((i * 211 + t * 40) % max(1, (y1 - y0)))
        cv.circle(px, py, r * (0.6 + 0.6 * ((i % 3) / 2.0)), fill=color, alpha=alpha)


def label(cv, s, size, y, color=INK, x=540, alpha=1.0, stroke=None, sw=0, glow=None):
    cv.text(s, x, y, size, fill=color, center=True, alpha=alpha, stroke=stroke, stroke_w=sw, glow=glow)


def badge(cv, text, cx, cy, fill=YELLOW, size=44, pad=34):
    w = cv.text_w(text, size) + pad * 2
    cv.rrect(cx - w / 2, cy - size * 0.9, cx + w / 2, cy + size * 0.55, 22,
             fill=fill, stroke=INK, width=5)
    cv.text(text, cx, cy + size * 0.16, size, fill=INK, center=True)


# ---------- фоны ----------

def sky_bright(cv, t, dim=0.0):
    top = "#9FE0FF" if dim < 0.5 else "#3A4667"
    bot = "#DDF3FF" if dim < 0.5 else "#2A3350"
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, top), (1, bot)]))
    if dim < 0.5:
        cv.circle(850, 250, 120, fill=YELLOW, alpha=0.95)
        cv.circle(850, 250, 160, fill=YELLOW, alpha=0.25)


def city(cv, base, t, lit=True, dim=0.0):
    palette = [BLUE, PURPLE, TEAL, CORAL, "#FF9F1C"]
    xs = [-40, 90, 210, 330, 450, 570, 690, 810, 930, 1050]
    hs = [240, 360, 300, 440, 330, 390, 270, 460, 320, 380]
    for i, x in enumerate(xs):
        h = hs[i]
        w = 120
        col = palette[i % len(palette)]
        if dim > 0:
            col = "#5B6178"
        cv.rrect(x, base - h, x + w, base, 12, fill=col, stroke=INK, width=6)
        # окна
        dot = YELLOW if lit else "#3A3F55"
        for r in range(int(h // 60)):
            for c in range(2):
                wx = x + 22 + c * 48
                wy = base - h + 26 + r * 60
                if wy < base - 26:
                    cv.rrect(wx, wy, wx + 30, wy + 30, 6, fill=dot, stroke=INK, width=3)


# ---------- сцены ----------

def scene_hook(cv, t, ctx):
    k = k_of(ctx, t, (0, 8))
    dark = ease((k - 0.35) / 0.25)
    sky_bright(cv, t, dim=dark)
    city(cv, 1250, t, lit=dark < 0.5, dim=dark)
    cv.rect(0, 1250, W, H, fill="#7ED0A0" if dark < 0.5 else "#39584C", )

    # выключатель
    cv.rrect(120, 260, 320, 460, 24, fill=WHITE, stroke=INK, width=7)
    ang = -38 * ease((k - 0.28) / 0.12) + 38
    cv.save()
    cv.c.rotate(ang, 220, 420)
    cv.rrect(196, 280, 244, 410, 18, fill=CORAL if dark < 0.5 else GREY, stroke=INK, width=6)
    cv.restore()

    # облака
    for i in range(3):
        cx = ((t * 40 + i * 380) % 1300) - 120
        cy = 520 + i * 90
        cv.circle(cx, cy, 46, fill=WHITE, alpha=0.9)
        cv.circle(cx + 54, cy + 8, 34, fill=WHITE, alpha=0.9)
        cv.circle(cx - 52, cy + 12, 30, fill=WHITE, alpha=0.9)

    if k > 0.2:
        a = ease((k - 0.2) / 0.25)
        cv.text("7", 540, 900, 320, fill=WHITE, center=True, stroke=INK, stroke_w=16, alpha=a)
        label(cv, "ДНЕЙ БЕЗ СВЕТА", 56, 990, INK, alpha=a, stroke=WHITE, sw=10)

    for i in range(3):
        person(cv, 250 + i * 300, 1560, 1.0, [CORAL, BLUE, TEAL][i], phase=t * 2 + i)


def scene_fridge(cv, t, ctx):
    k = k_of(ctx, t, (8, 18))
    cv.rect(0, 0, W, H, fill="#E8F7FF")
    cv.rect(0, 1420, W, H, fill="#CFEFFF")

    # холодильник
    x0, y0, x1, y1 = 300, 300, 780, 1250
    cv.rrect(x0 + 8, y0 + 12, x1 + 8, y1 + 12, 30, fill="#00000018")
    cv.rrect(x0, y0, x1, y1, 30, fill=WHITE, stroke=INK, width=7)
    cv.line(x0, y0 + 330, x1, y0 + 330, INK, 6)
    cv.rrect(x0 + 60, y0 + 120, x0 + 96, y0 + 240, 14, fill=GREY, stroke=INK, width=5)
    cv.rrect(x0 + 60, y0 + 400, x0 + 96, y0 + 520, 14, fill=GREY, stroke=INK, width=5)

    # термометр и рост температуры
    temp = 4 + 18 * ease(k)
    hy = 1150 - temp * 26
    cv.rrect(860, 340, 930, 1150, 30, fill=WHITE, stroke=INK, width=6)
    cv.rrect(872, hy, 918, 1138, 20, fill=CORAL if temp > 8 else TEAL)
    cv.circle(895, 1160, 40, fill=CORAL if temp > 8 else TEAL, stroke=INK, width=6)
    cv.text("+%d°" % int(temp), 895, 300, 54, fill=INK, center=True)

    # еда внутри: портится
    foods = [(400, 480, YELLOW, "сыр"), (560, 480, CORAL, "мясо"), (400, 900, GREEN, "салат")]
    for i, (fx, fy, col, name) in enumerate(foods):
        rot = (k - i * 0.05) * 40
        cv.save()
        cv.c.rotate(rot, fx + 50, fy + 40)
        cv.rrect(fx, fy, fx + 100, fy + 80, 16,
                 fill=col if k < 0.55 else "#8E8A78", stroke=INK, width=5)
        cv.restore()

    drift(cv, t, "#BEE7FF", 18, 320, 1200, 0.35, 8)
    for i in range(4):
        yy = 1320 - ((t * 120 + i * 90) % 320)
        cv.circle(540 + 40 * math.sin(t * 2 + i), yy, 10, fill="#FFFFFF", alpha=0.25)
    if k > 0.15:
        a = ease((k - 0.15) / 0.25)
        badge(cv, "4 ЧАСА", 540, 1420, YELLOW, 56, alpha) if False else badge(cv, "4 ЧАСА", 540, 1400, YELLOW, 54)
        label(cv, "ХОЛОДИЛЬНИК БЕЗ СВЕТА", 30, 1480, INK)

    if k > 0.6:
        a = ease((k - 0.6) / 0.3)
        label(cv, "ПОЛНАЯ МОРОЗИЛКА — ДО 48 ЧАСОВ", 30, 1540, INK, alpha=a)


def scene_water(cv, t, ctx):
    k = k_of(ctx, t, (18, 27))
    cv.rect(0, 0, W, H, fill="#DFF6FF")
    cv.rect(0, 1460, W, H, fill="#9FD9F0")

    # водонапорная башня: ноги, бак, крыша
    cv.poly([(430, 620), (462, 1180), (500, 1180), (520, 620)], fill="#7FB8FF", stroke=INK, width=6)
    cv.poly([(560, 620), (580, 620), (618, 1180), (656, 1180)], fill="#7FB8FF", stroke=INK, width=6)
    cv.rrect(400, 400, 680, 640, 26, fill=BLUE, stroke=INK, width=7)
    cv.poly([(386, 400), (694, 400), (540, 300)], fill=YELLOW, stroke=INK, width=6)
    cv.line(400, 520, 680, 520, INK, 5)
    for i in range(3):
        cv.circle(450 + i * 90, 470, 8, fill=WHITE, stroke=INK, width=3)

    # труба от башни к насосу
    cv.line(540, 1180, 540, 1300, INK, 10)
    cv.line(540, 1300, 360, 1300, INK, 10)

    # насос с колесом
    cv.rrect(180, 1230, 360, 1390, 22, fill=CORAL, stroke=INK, width=7)
    cv.circle(270, 1310, 46, fill=WHITE, stroke=INK, width=6)
    ang = (t * 150) % 360 if k < 0.45 else 0
    cv.save()
    cv.c.rotate(ang, 270, 1310)
    for i in range(3):
        cv.line(270, 1310, 270 + 40 * math.cos(i * 2.09), 1310 + 40 * math.sin(i * 2.09), INK, 7)
    cv.restore()

    # молния и её исчезновение
    if k < 0.5:
        cv.poly([(760, 250), (820, 250), (780, 330), (830, 330), (750, 430), (780, 350),
                 (730, 350)], fill=YELLOW, stroke=INK, width=6)

    # кран и ведро
    cv.rrect(820, 700, 900, 760, 12, fill=GREY, stroke=INK, width=6)
    cv.line(860, 760, 860, 860, INK, 10)
    cv.rrect(800, 1180, 920, 1320, 14, fill=PURPLE, stroke=INK, width=6)
    cv.line(800, 1210, 920, 1210, INK, 5)
    for i in range(2 if k > 0.5 else 4):
        dy = ((t * 240 + i * 180) % 300)
        cv.circle(860, 880 + dy, 11, fill=BLUE, alpha=0.9)

    drift(cv, t, BLUE, 14, 200, 1400, 0.18, 7)
    for i in range(3):
        rr = 40 + 40 * ((t * 0.6 + i * 0.3) % 1.0)
        cv.circle(540, 1300, rr, stroke="#FFFFFF", width=3, alpha=0.18)
    person(cv, 260, 1660, 1.05, TEAL, phase=t * 2)

    if k > 0.18:
        label(cv, "БЕЗ СВЕТА НЕ РАБОТАЮТ НАСОСЫ", 38, 200, INK, alpha=ease((k - 0.18) / 0.3))
    if k > 0.55:
        label(cv, "ВОДУ НАБИРАЮТ ЗАРАНЕЕ", 32, 256, CORAL, alpha=ease((k - 0.55) / 0.3))


def scene_hospital(cv, t, ctx):
    k = k_of(ctx, t, (27, 36))
    cv.rect(0, 0, W, H, fill="#F3F0FF")
    cv.rect(0, 1440, W, H, fill="#DCD4FF")

    # больница
    cv.rrect(140, 520, 940, 1400, 26, fill=WHITE, stroke=INK, width=8)
    cv.rect(280, 340, 380, 560, fill=WHITE, stroke=INK, width=7)
    # крест
    cv.rect(470, 640, 610, 700, fill=CORAL)
    cv.rect(510, 600, 570, 740, fill=CORAL)
    for r in range(3):
        for c in range(4):
            cv.rrect(300 + c * 150, 820 + r * 150, 400 + c * 150, 900 + r * 150, 10,
                     fill="#BFE3FF" if (r + c) % 2 else YELLOW, stroke=INK, width=4)

    # генератор снаружи: корпус, вентилятор, кабель в больницу, канистра
    cv.rrect(690, 1180, 960, 1400, 18, fill=YELLOW, stroke=INK, width=7)
    cv.rrect(712, 1204, 838, 1300, 10, fill="#FFE9A8", stroke=INK, width=5)
    cv.circle(775, 1252, 34, fill=WHITE, stroke=INK, width=5)
    cv.save()
    cv.c.rotate((t * 300) % 360, 775, 1252)
    cv.line(775, 1252, 775, 1222, INK, 6)
    cv.line(775, 1252, 800, 1268, INK, 6)
    cv.restore()
    cv.line(690, 1340, 600, 1340, INK, 10)          # кабель к зданию
    cv.line(600, 1340, 600, 1300, INK, 10)
    cv.line(864, 1230, 864, 1180, INK, 8)
    cv.poly([(864, 1170), (846, 1208), (864, 1208), (852, 1244), (884, 1196), (864, 1196)],
            fill=CORAL, stroke=INK, width=4)
    # канистра с топливом
    cv.rrect(880, 1300, 950, 1390, 10, fill=CORAL, stroke=INK, width=6)
    cv.line(900, 1300, 906, 1282, INK, 6)

    # кислород/койки
    cv.rrect(220, 1150, 430, 1210, 12, fill=WHITE, stroke=INK, width=5)
    cv.rrect(220, 1210, 430, 1290, 10, fill=TEAL, stroke=INK, width=5)

    # импульсы от генератора к зданию
    for i in range(3):
        p = (t * 0.9 + i * 0.33) % 1.0
        gx = 690 - 90 * p
        cv.circle(gx, 1340, 9, fill=YELLOW, alpha=0.9)
    blink = abs(math.sin(t * 3))
    cv.circle(250, 420, 14, fill=CORAL if blink > 0.5 else "#FFD3CE")
    if k > 0.15:
        a = ease((k - 0.15) / 0.3)
        label(cv, "БОЛЬНИЦЫ ПЕРЕХОДЯТ НА ГЕНЕРАТОРЫ", 36, 240, INK, alpha=a)
    if k > 0.55:
        a = ease((k - 0.55) / 0.3)
        badge(cv, "ТОПЛИВО НА СУТКИ", 540, 1560, YELLOW, 44)
        label(cv, "ЗАПАС НЕ БЕСКОНЕЧНЫЙ", 30, 1640, INK, alpha=a)


def scene_phone(cv, t, ctx):
    k = k_of(ctx, t, (36, 45))
    cv.rect(0, 0, W, H, fill="#FFF0F6")
    cv.rect(0, 1440, W, H, fill="#FFD9E6")

    # телефон
    cv.rrect(330, 300, 750, 1300, 44, fill=WHITE, stroke=INK, width=8)
    cv.rrect(360, 340, 720, 1180, 28, fill="#E9F7FF", stroke=INK, width=5)
    cv.line(450, 1225, 630, 1225, INK, 10)

    # вышка связи и батарея у её основания
    tx = 540
    cv.poly([(tx - 46, 1120), (tx + 46, 1120), (tx + 16, 640), (tx - 16, 640)],
            fill="#B9C6D6", stroke=INK, width=6)
    for i in range(3):
        yy = 720 + i * 130
        cv.line(tx - 34 + i * 6, yy, tx + 34 - i * 6, yy, INK, 5)
    cv.circle(tx, 620, 16, fill=CORAL, stroke=INK, width=5)
    for i in range(3):
        a = 0.25 + 0.55 * abs(math.sin(t * 2 + i * 0.6))
        cv.c.drawArc(skia.Rect(tx - 60 - i * 40, 560 - i * 40, tx + 60 + i * 40, 680 + i * 40),
                     215, 110, False, _sp(BLUE, 7, int(255 * a)))
    # батарея-резерв
    cv.rrect(tx - 92, 1150, tx + 92, 1250, 16, fill=GREEN, stroke=INK, width=6)
    cv.rrect(tx + 92, 1180, tx + 116, 1220, 8, fill=INK)
    for i in range(3):
        cv.rect(tx - 76 + i * 52, 1170, tx - 32 + i * 52, 1230, fill=YELLOW, alpha=0.9)

    # оплата: терминал и наличные
    cv.rrect(180, 1360, 380, 1560, 18, fill=PURPLE, stroke=INK, width=7)
    cv.rrect(210, 1390, 350, 1450, 8, fill=WHITE, stroke=INK, width=4)
    cv.rrect(760, 1380, 900, 1560, 14, fill=GREEN, stroke=INK, width=7)
    cv.text("₽", 830, 1500, 90, fill=INK, center=True)

    if k > 0.25:
        label(cv, "СВЯЗЬ ДЕРЖИТСЯ НА БАТАРЕЯХ", 34, 220, INK, alpha=ease((k - 0.25) / 0.3))
    if k > 0.6:
        label(cv, "КАРТЫ НЕ РАБОТАЮТ — НУЖНЫ НАЛИЧНЫЕ", 30, 1700, CORAL,
              alpha=ease((k - 0.6) / 0.3))


def scene_traffic(cv, t, ctx):
    k = k_of(ctx, t, (45, 51))
    cv.rect(0, 0, W, H, fill="#FFF9E8")
    cv.rect(0, 1120, W, H, fill="#4A4A5E")
    cv.rect(0, 1300, W, 1322, fill=YELLOW)
    cv.rect(0, 1520, W, 1542, fill=YELLOW)
    # зебра
    for i in range(7):
        cv.rect(60 + i * 140, 1330, 150 + i * 140, 1510, fill=WHITE, alpha=0.85)

    # светофор на столбе
    cv.line(840, 360, 840, 1120, INK, 12)
    cv.rrect(760, 250, 920, 560, 26, fill=INK)
    blink = int(t * 2) % 2
    cv.circle(840, 310, 34, fill=YELLOW if blink else "#5B5B70")
    cv.circle(840, 400, 34, fill="#5B5B70")
    cv.circle(840, 490, 34, fill="#5B5B70")

    # машины стоят
    for i, (cx, col) in enumerate([(90, CORAL), (330, BLUE)]):
        cv.rrect(cx, 1140, cx + 210, 1260, 22, fill=col, stroke=INK, width=6)
        cv.rrect(cx + 44, 1100, cx + 166, 1150, 14, fill=WHITE, stroke=INK, width=5)
        cv.circle(cx + 52, 1272, 26, fill=INK)
        cv.circle(cx + 158, 1272, 26, fill=INK)

    # заправка с перечёркнутой колонкой
    cv.rrect(90, 620, 420, 1060, 20, fill=PURPLE, stroke=INK, width=7)
    cv.rrect(130, 700, 380, 820, 12, fill=WHITE, stroke=INK, width=5)
    cv.rrect(200, 880, 300, 1000, 12, fill=GREY, stroke=INK, width=6)
    cv.line(180, 860, 320, 1020, CORAL, 12)
    cv.text("0", 255, 960, 64, fill=INK, center=True)

    for i in range(3):
        p = (t * 0.8 + i * 0.3) % 1.0
        cv.circle(300 - 60 * p, 1120 - 40 * p, 16 * (1 - p) + 4, fill="#C9C6D8", alpha=0.35)
    if k > 0.18:
        a = ease((k - 0.18) / 0.3)
        label(cv, "СВЕТОФОРЫ ВЫКЛЮЧЕНЫ", 40, 180, INK, alpha=a)
        label(cv, "ЗАПРАВКИ НЕ КАЧАЮТ ТОПЛИВО", 30, 1760, WHITE, alpha=a)


def scene_final(cv, t, ctx):
    k = k_of(ctx, t, (51, 59))
    dawn = ease(k)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [
        (0.0, "#FFD9A0"), (0.55, "#FFB27A"), (1.0, "#FFE9C0")]))
    cv.circle(540, 1150 - 120 * dawn, 220, fill=YELLOW, alpha=0.55)
    city(cv, 1450, t, lit=True)
    cv.rect(0, 1450, W, H, fill="#5FBF8F")

    for i in range(3):
        person(cv, 260 + i * 280, 1620, 1.0, [CORAL, BLUE, PURPLE][i], phase=t * 2 + i * 0.5)

    if k > 0.1:
        a = ease((k - 0.1) / 0.25)
        label(cv, "ЧЕРЕЗ НЕДЕЛЮ СВЕТ ВЕРНЁТСЯ", 44, 420, INK, alpha=a, stroke=WHITE, sw=8)
    if k > 0.45:
        a = ease((k - 0.45) / 0.3)
        label(cv, "НО ГОТОВИТЬСЯ ЛУЧШЕ ЗАРАНЕЕ", 34, 500, "#5A2A00", alpha=a)


SCENES = {
    "hook": scene_hook,
    "fridge": scene_fridge,
    "water": scene_water,
    "hospital": scene_hospital,
    "phone": scene_phone,
    "traffic": scene_traffic,
    "final": scene_final,
}


def caption(cv, text, hl):
    if not text:
        return
    size = 54
    words = text.split()
    width = sum(cv.text_w(w + " ", size) for w in words)
    while width > 940 and size > 30:
        size -= 3
        width = sum(cv.text_w(w + " ", size) for w in words)
    x = 540 - width / 2
    base = 1790
    for w in words:
        col = CORAL if any(h.lower() in w.lower() for h in hl) else INK
        cv.text(w, x, base, size, fill=col, stroke=WHITE, stroke_w=7,
                shadow=(0, 4, 8, "#00000033"))
        x += cv.text_w(w + " ", size)


def render(name, t, ctx=None, finish=False):
    ctx = ctx or {}
    k = 0.0
    if ctx.get("scene_dur"):
        k = max(0.0, min(1.0, ctx["scene_t"] / ctx["scene_dur"]))
    cv = Canvas()
    cv.save()
    cv.c.translate(5 * math.sin(t * 0.6), 4 * math.cos(t * 0.45))
    cv.zoom(1.03 + 0.10 * ease(k), 540, 1000)
    SCENES[name](cv, t, ctx)
    cv.restore()
    caption(cv, ctx.get("caption_text", ""), ctx.get("caption_hl", ()))
    return cv.to_pil()
