"""Рендер эпизода про шлюз: шесть сцен, единый визуальный язык."""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280
SS = 2


def X(v):
    return int(round(v * SS))


def P(*pts):
    return [(X(a), X(b)) for a, b in pts]


def XY(a, b):
    return (X(a), X(b))


def F(size):
    from vgen.palette import font
    return font(size)


BG = (8, 14, 24)
GRID = (30, 58, 86, 26)
STEEL = (120, 138, 160)
STEEL_L = (176, 196, 220)
WATER_TOP = (54, 138, 196)
WATER_BOT = (14, 52, 92)
GOLD = (255, 196, 96)
CREAM = (255, 236, 176)
CYAN = (150, 228, 255)
INK = (10, 16, 26)


def backdrop(d):
    d.rectangle(P((0, 0), (W, H)), fill=BG)
    for y in range(0, H, 40):
        d.line(P((0, y), (W, y)), fill=GRID, width=1)
    for x in range(0, W, 40):
        d.line(P((x, 0), (x, H)), fill=GRID, width=1)


def title(d, text, y=44, color=CYAN, size=34):
    d.text(XY(32, y), text, font=F(size), fill=color)


def card_bg(d, x, y, w, h, a=232):
    d.rounded_rectangle(P((x, y), (x + w, y + h)), radius=X(14),
                        fill=(10, 18, 30, a), outline=(120, 180, 220, 60), width=2)


# ---------------------------------------------------------------- scene 1: хук
def scene_hook(d, t, ctx):
    cx0, cx1, cy0, cy1 = 60, 660, 380, 1120
    # вода
    for yy in range(cy0 + 90, cy1):
        k = (yy - cy0 - 90) / max(1, cy1 - cy0 - 90)
        d.line(P((cx0, yy), (cx1, yy)), fill=lerp3((54, 138, 196), (12, 40, 74), k ** 0.8))
    # волны
    pts = [(x, cy0 + 90 + 3 * math.sin(x / 34 + t * 2.4)) for x in range(cx0, cx1, 5)]
    d.line(P(*pts), fill=(170, 228, 250, 200), width=X(3))
    # стены камеры
    d.rectangle(P((0, 380), (cx0, cy1)), fill=(72, 78, 90))
    d.rectangle(P((cx1, 380), (W, cy1)), fill=(72, 78, 90))
    # створки ворот внизу и подпись
    for sgn in (-1, 1):
        base = 360 + sgn * 120
        d.polygon(P((base, cy1 - 120), (base + sgn * 96, cy1 - 30),
                    (base + sgn * 96, cy1 + 40), (base, cy1 + 130)),
                  fill=(118, 136, 158), outline=(176, 198, 220))
    d.text(XY(96, cy0 + 34), "камера шлюза", font=F(22), fill=(150, 186, 214))
    # корабль
    ship_big(d, t)
    # хук
    hook = "26 МЕТРОВ"
    size = 96
    while size > 40:
        f = F(size)
        bb = d.textbbox((0, 0), hook, font=f, stroke_width=X(7))
        if bb[2] - bb[0] <= X(W) - X(56):
            break
        size -= 3
    f = F(size)
    bb = d.textbbox((0, 0), hook, font=f, stroke_width=X(7))
    d.text(((X(W) - (bb[2] - bb[0])) / 2 - bb[0], X(120)), hook, font=f,
           fill=CREAM, stroke_width=X(7), stroke_fill=INK)
    sub = "БЕЗ ЕДИНОГО КРАНА"
    bb2 = d.textbbox((0, 0), sub, font=F(40), stroke_width=X(5))
    d.text(((X(W) - (bb2[2] - bb2[0])) / 2 - bb2[0], X(240)), sub, font=F(40),
           fill=(214, 236, 250), stroke_width=X(5), stroke_fill=INK)


def lerp3(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def ship_big(d, t, x=360, y=560, s=1.0):
    ln, hh = 380 * s, 92 * s
    d.polygon(P((x - ln / 2, y - hh / 2), (x + ln / 2, y - hh / 2),
                (x + ln / 2 - 30, y + hh / 2), (x - ln / 2 + 30, y + hh / 2)),
              fill=(118, 40, 38), outline=(206, 104, 84))
    d.line(P((x - ln / 2 + 8, y + 8), (x + ln / 2 - 34, y + 8)), fill=(226, 140, 110, 180), width=3)
    # контейнеры
    cols = ((214, 92, 60), (70, 132, 198), (232, 180, 66), (96, 168, 128), (150, 116, 190))
    for row in range(2):
        for i in range(6 - row):
            bx = x - ln * 0.44 + i * 52
            by = y - hh / 2 - 26 - row * 26
            d.rectangle(P((bx, by), (bx + 48, by + 24)), fill=cols[(i + row) % 5],
                        outline=(36, 40, 48))
    # надстройка
    bx = x + ln * 0.30
    d.rectangle(P((bx, y - hh / 2 - 50), (bx + 46, y - hh / 2)), fill=(236, 238, 244),
                outline=(150, 160, 174))
    d.rectangle(P((bx + 6, y - hh / 2 - 44), (bx + 40, y - hh / 2 - 14)), fill=(58, 90, 124))


# ------------------------------------------------------------- scene 2: принцип
CY0, CY1 = 470, 1080


def y_lvl(level, cy0=CY0, cy1=CY1):
    return cy1 - (cy1 - cy0) * level


def scene_water(d, t, ctx):
    lvl = ctx["level"]
    # стены
    d.rectangle(P((0, CY0 - 60), (96, CY1 + 40)), fill=(70, 76, 88))
    d.rectangle(P((560, CY0 - 60), (W, CY1 + 40)), fill=(70, 76, 88))
    for i in range(10):
        d.line(P((8, CY0 - 40 + i * 60), (88, CY0 - 36 + i * 60)), fill=(96, 104, 118, 90), width=2)
        d.line(P((568, CY0 - 40 + i * 60), (W - 8, CY0 - 36 + i * 60)), fill=(96, 104, 118, 90), width=2)
    d.rectangle(P((96, CY1), (560, CY1 + 40)), fill=(54, 60, 72))
    # вода
    ys = y_lvl(lvl)
    for yy in range(int(math.ceil(ys)), CY1):
        k = (yy - ys) / max(1, CY1 - ys)
        d.line(P((110, yy), (546, yy)), fill=lerp3(WATER_TOP, WATER_BOT, k ** 0.7))
    pts = [(x, ys + 2.6 * math.sin(x / 30 + t * 3)) for x in range(110, 546, 4)]
    d.line(P(*pts), fill=(172, 230, 252, 210), width=X(3))
    # пузырьки при наполнении
    for i in range(14):
        ph = (t * 0.55 + i * 0.13) % 1.0
        bx = 130 + (i * 47) % 380
        by = CY1 - ph * (CY1 - ys)
        d.ellipse(P((bx - 3, by - 3), (bx + 3, by + 3)), fill=(210, 240, 255, int(120 * (1 - ph))))
    # корабль
    ship_big(d, t, x=328, y=ys + 26, s=0.62)
    # шкала справа
    for m in (0, 8, 17, 26):
        frac = m / 26.0
        yy = CY1 - (CY1 - CY0) * frac
        d.line(P((598, yy), (622, yy)), fill=(160, 196, 224, 200), width=2)
        d.text(XY(628, yy - 12), str(m), font=F(20), fill=(158, 192, 220))
    yy = CY1 - (CY1 - CY0) * lvl
    d.ellipse(P((590, yy - 7), (604, yy + 7)), fill=GOLD)
    # метры
    metres = 26 * lvl
    d.text(XY(36, 210), f"+{metres:0.0f} м", font=F(64), fill=CYAN)
    d.text(XY(38, 290), "уровень в камере", font=F(22), fill=(150, 186, 214))
    title(d, "ВСЁ ДЕЛАЕТ ВОДА", 96, CREAM, 36)
    card_bg(d, 34, 968, W - 68, 76)
    d.text(XY(54, 986), "вода из соседней камеры · насосов нет", font=F(24), fill=(196, 222, 244))


# --------------------------------------------------------------- scene 3: ворота
def ease_scene(ctx):
    k = ctx.get("scene_t", 0.0) / max(0.1, ctx.get("scene_dur", 1.0))
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def scene_gates(d, t, ctx):
    k = max(ctx["gate_k"], ease_scene(ctx))
    cy = 700
    # камера
    d.rectangle(P((0, 380), (W, cy - 150)), fill=(16, 24, 36))
    d.rectangle(P((0, cy + 160), (W, H)), fill=(52, 58, 70))
    # створки
    for sgn in (-1, 1):
        base = (W / 2) + sgn * 120
        tipx = base + sgn * (110 - 40 * k)
        d.polygon(P((base, cy - 150), (tipx, cy - 40), (tipx, cy + 40), (base, cy + 150)),
                  fill=(126, 144, 166), outline=(180, 200, 222))
        for i in range(5):
            yy = cy - 120 + i * 60
            d.line(P((base, yy), (tipx - sgn * 6, yy + 12 * sgn)), fill=(96, 112, 132), width=3)
    # зазор
    gap = 40 - 40 * k
    if gap > 3:
        d.rectangle(P((W / 2 - gap, cy - 150), (W / 2 + gap, cy + 150)), fill=(70, 210, 240, 70))
    # водовод в полу
    d.rectangle(P((60, cy + 128), (W - 60, cy + 176)), fill=(30, 44, 60),
                outline=(90, 130, 160), width=2)
    for i in range(7):
        ax = 90 + i * 82
        d.polygon(P((ax, cy + 140), (ax + 34, cy + 152), (ax, cy + 164)),
                  fill=(120, 210, 246, 190))
    # стояки вверх: вода поднимается в камеру
    for rx in (250, 470):
        d.rectangle(P((rx - 14, cy + 40), (rx + 14, cy + 128)), fill=(30, 44, 60),
                    outline=(90, 130, 160), width=2)
        for k in range(3):
            ay = cy + 118 - k * 26
            d.polygon(P((rx - 9, ay + 10), (rx + 9, ay + 10), (rx, ay)), fill=(120, 210, 246, 200))
    # затвор
    d.ellipse(P((352, cy + 140), (378, cy + 166)), fill=(24, 36, 50), outline=(255, 196, 96), width=2)
    d.line(P((365, cy + 128), (365, cy + 178)), fill=(255, 196, 96), width=3)
    d.text(XY(70, cy + 186), "водовод в полу · затвор открыт", font=F(20), fill=(150, 196, 224))

    title(d, "ВОДА ИДЁТ ПО ВОДОВОДУ", 96, CREAM, 32)
    card_bg(d, 34, 990, W - 68, 84)
    d.text(XY(54, 1004), "затворы в полу открыты —", font=F(24), fill=(196, 222, 244))
    d.text(XY(54, 1036), "камера наполняется самотёком", font=F(24), fill=(196, 222, 244))


# --------------------------------------------------------------- scene 4: ступени
def scene_steps(d, t, ctx):
    steps_done = ctx["steps_done"]
    base_y = 1000
    w_ch, h_ch = 190, 210
    for i in range(3):
        x0 = 70 + i * 200
        y0 = base_y - i * 210
        active = i < steps_done
        # камера-ступень
        d.rectangle(P((x0, y0 - h_ch), (x0 + w_ch, y0)), fill=(20, 28, 42) if active else (14, 20, 30),
                    outline=GOLD if active else (70, 88, 106), width=3)
        # вода
        if active:
            wl = min(1.0, ctx["level"])
            wy = y0 - h_ch * 0.55 * wl
            for yy in range(int(math.ceil(wy)), y0):
                kk = max(0.0, (yy - wy) / max(1, y0 - wy))
                d.line(P((x0 + 4, yy), (x0 + w_ch - 4, yy)), fill=lerp3(WATER_TOP, WATER_BOT, kk ** 0.7))
        d.text(XY(x0 + 10, y0 - h_ch + 12), f"камера {i + 1}", font=F(20),
               fill=(200, 220, 240) if active else (110, 128, 146))
        d.text(XY(x0 + 10, y0 - h_ch + 40), "+8,7 м", font=F(28),
               fill=GOLD if active else (96, 112, 130))
        # стрелка вверх
        if active:
            ax = x0 + w_ch + 16
            d.polygon(P((ax - 9, y0 - 40), (ax + 9, y0 - 40), (ax, y0 - 74)), fill=GOLD)
    title(d, "ТРИ СТУПЕНИ · 26 М", 96, CREAM, 34)
    card_bg(d, 34, 1046, W - 68, 70)
    d.text(XY(54, 1060), "шлюзы Гатун: 3 камеры по 8,7 м", font=F(24), fill=(196, 222, 244))


# --------------------------------------------------------------- scene 5: масштаб
def scene_compare(d, t, ctx):
    # дом 9 этажей против 26 м
    ground = 1010
    bh = 420.0  # 26 м в одном масштабе для обоих объектов
    d.rectangle(P((420, ground - bh), (560, ground)), fill=(24, 34, 48),
                outline=(120, 160, 190), width=2)
    step = bh / 9.0
    for i in range(9):
        yy = ground - i * step
        d.rectangle(P((428, yy - step + 6), (552, yy - 6)), fill=(255, 226, 150, 22),
                    outline=(160, 190, 210, 60))
    d.text(XY(420, ground + 10), "9 этажей", font=F(24), fill=(190, 214, 236))
    # столб 26 м
    d.rectangle(P((250, ground - bh), (330, ground)), fill=(255, 196, 96, 46),
                outline=GOLD, width=3)
    for m in range(0, 27, 2):
        yy = ground - m / 26 * bh
        d.line(P((250, yy), (262, yy)), fill=(255, 226, 160, 120), width=1)
    d.text(XY(150, ground - bh - 8), "26 м", font=F(46), fill=GOLD)
    title(d, "ЭТО ВЫСОТА ДЕВЯТИЭТАЖКИ", 96, CREAM, 30)
    card_bg(d, 34, 1060, W - 68, 70)
    d.text(XY(54, 1074), "без крана и лебёдки", font=F(24), fill=(196, 222, 244))


# ---------------------------------------------------------------- scene 6: финал
def scene_final(d, t, ctx):
    card_bg(d, 34, 330, W - 68, 300)
    d.text(XY(58, 360), "Панамский канал", font=F(44), fill=CREAM)
    d.text(XY(58, 424), "шлюзы Гатун · 1914", font=F(26), fill=(170, 206, 236))
    d.line(P((58, 466), (W - 58, 466)), fill=(255, 196, 96, 160), width=3)
    d.text(XY(58, 484), "3 камеры · 26 м · без крана", font=F(30), fill=GOLD)
    d.text(XY(58, 536), "200 млн литров воды за проход", font=F(22), fill=(180, 210, 236))
    d.text(XY(58, 572), "всё — гравитацией и разницей уровней", font=F(22), fill=(180, 210, 236))
    # маленький силуэт корабля на воде
    for yy in range(700, 900):
        k = (yy - 700) / 200
        d.line(P((0, yy), (W, yy)), fill=lerp3((36, 110, 168), (10, 36, 66), k))
    pts = [(x, 700 + 4 * math.sin(x / 40 + t * 2)) for x in range(0, W, 6)]
    d.line(P(*pts), fill=(170, 228, 250, 180), width=3)
    ship_big(d, t, x=360, y=742, s=0.55)


SCENES = {
    "hook": scene_hook,
    "water": scene_water,
    "gates": scene_gates,
    "steps": scene_steps,
    "compare": scene_compare,
    "final": scene_final,
}


def render(name, t, ctx):
    img = Image.new("RGB", (X(W), X(H)), BG)
    d = ImageDraw.Draw(img, "RGBA")
    backdrop(d)
    SCENES[name](d, t, ctx)
    return img
