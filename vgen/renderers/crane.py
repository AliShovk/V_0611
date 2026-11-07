"""Рендер эпизода про башенный кран: шесть сцен, одна геометрия крана."""
import math
from PIL import Image, ImageDraw

W, H, SS = 720, 1280, 2


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
STEEL = (150, 168, 190)
STEEL_D = (96, 110, 128)
GOLD = (255, 196, 96)
CREAM = (255, 236, 176)
CYAN = (150, 228, 255)
INK = (10, 16, 26)

MAST_X = 250
MAST_W = 46
MAST_TOP = 392
GROUND = 1120
JIB_END = 648
CJIB_END = 168


def lerp3(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def backdrop(d):
    d.rectangle(P((0, 0), (W, H)), fill=BG)
    for y in range(0, H, 40):
        d.line(P((0, y), (W, y)), fill=GRID, width=1)
    for x in range(0, W, 40):
        d.line(P((x, 0), (x, H)), fill=GRID, width=1)


def lattice(d, x0, y0, x1, y1, w, seg=44, color=STEEL, width=3):
    """Решётчатая балка от (x0,y0) до (x1,y1) шириной w."""
    d.line(P((x0, y0 - w / 2), (x1, y1 - w / 2)), fill=color, width=X(width))
    d.line(P((x0, y0 + w / 2), (x1, y1 + w / 2)), fill=color, width=X(width))
    n = max(2, int(abs(x1 - x0) / seg) + int(abs(y1 - y0) / seg))
    for i in range(n):
        k0 = i / n
        k1 = (i + 1) / n
        ax = x0 + (x1 - x0) * k0
        ay = y0 + (y1 - y0) * k0
        bx = x0 + (x1 - x0) * k1
        by = y0 + (y1 - y0) * k1
        if i % 2 == 0:
            d.line(P((ax, ay - w / 2), (bx, by + w / 2)), fill=STEEL_D, width=X(2))
        else:
            d.line(P((ax, ay + w / 2), (bx, by - w / 2)), fill=STEEL_D, width=X(2))


def crane(d, ctx):
    load_x = ctx.get("trolley", 380)
    load_y = ctx.get("load_y", 760)
    cw = ctx.get("cw", 1.0)

    # фундамент
    d.rectangle(P((MAST_X - 62, GROUND), (MAST_X + 62, GROUND + 34)), fill=(70, 78, 92))
    d.rectangle(P((MAST_X - 44, GROUND - 14), (MAST_X + 44, GROUND)), fill=(96, 106, 122))
    # башня
    lattice(d, MAST_X, MAST_TOP, MAST_X, GROUND - 10, MAST_W)
    # оголовок
    d.polygon(P((MAST_X - 26, MAST_TOP), (MAST_X + 26, MAST_TOP), (MAST_X, MAST_TOP - 62)),
              fill=(120, 136, 158), outline=(176, 196, 220))
    # стрела и противовесная консоль
    lattice(d, MAST_X + 12, MAST_TOP + 10, JIB_END, MAST_TOP + 10, 30)
    lattice(d, MAST_X - 12, MAST_TOP + 10, CJIB_END, MAST_TOP + 10, 30)
    # ванты
    d.line(P((MAST_X, MAST_TOP - 62), (JIB_END - 60, MAST_TOP + 4)), fill=(196, 212, 232, 200), width=2)
    d.line(P((MAST_X, MAST_TOP - 62), (MAST_X + 200, MAST_TOP + 4)), fill=(196, 212, 232, 200), width=2)
    d.line(P((MAST_X, MAST_TOP - 62), (CJIB_END + 14, MAST_TOP + 4)), fill=(196, 212, 232, 200), width=2)
    # противовес
    for i in range(3):
        d.rectangle(P((CJIB_END + 6, MAST_TOP + 16 + i * 18), (CJIB_END + 54, MAST_TOP + 30 + i * 18)),
                    fill=lerp3((120, 124, 132), (168, 172, 180), i / 2),
                    outline=(200, 204, 212))
    # кабина
    d.rectangle(P((MAST_X + 26, MAST_TOP + 26), (MAST_X + 74, MAST_TOP + 62)),
                fill=(232, 236, 244), outline=(150, 160, 176))
    d.rectangle(P((MAST_X + 32, MAST_TOP + 32), (MAST_X + 68, MAST_TOP + 50)), fill=(64, 110, 150))
    # тележка
    d.rectangle(P((load_x - 26, MAST_TOP + 14), (load_x + 26, MAST_TOP + 34)),
                fill=(255, 196, 96), outline=(180, 130, 50), width=2)
    d.ellipse(P((load_x - 20, MAST_TOP + 28), (load_x - 8, MAST_TOP + 40)), fill=(40, 44, 52))
    d.ellipse(P((load_x + 8, MAST_TOP + 28), (load_x + 20, MAST_TOP + 40)), fill=(40, 44, 52))
    d.text(XY(load_x - 24, MAST_TOP - 18), "тележка", font=F(18), fill=(255, 214, 150))
    # канат и крюк
    d.line(P((load_x, MAST_TOP + 28), (load_x, load_y - 26)), fill=(214, 224, 238), width=X(3))
    d.polygon(P((load_x - 10, load_y - 26), (load_x + 10, load_y - 26),
                (load_x + 7, load_y - 4), (load_x - 7, load_y - 4)),
              fill=(190, 200, 214), outline=(120, 130, 146))
    # груз
    d.rectangle(P((load_x - 54, load_y), (load_x + 54, load_y + 66)), fill=(196, 200, 206),
                outline=(120, 128, 140), width=2)
    for i in range(2):
        d.line(P((load_x - 54, load_y + 22 + i * 22), (load_x + 54, load_y + 22 + i * 22)),
               fill=(150, 156, 166), width=2)
    d.line(P((load_x - 40, load_y + 8), (load_x - 40, load_y + 58)), fill=(150, 156, 166), width=2)
    d.line(P((load_x + 40, load_y + 8), (load_x + 40, load_y + 58)), fill=(150, 156, 166), width=2)
    return load_x, load_y


def card_bg(d, x, y, w, h, a=232):
    d.rounded_rectangle(P((x, y), (x + w, y + h)), radius=X(14),
                        fill=(10, 18, 30, a), outline=(120, 180, 220, 60), width=2)


def title(d, text, y=44, color=CYAN, size=30):
    d.text(XY(32, y), text, font=F(size), fill=color)


def scene_hook(d, t, ctx):
    cx = dict(ctx)
    cx["trolley"] = 592
    cx["load_y"] = 560
    load_x, load_y = crane(d, cx)
    txt = "50 ТОНН"
    bb = d.textbbox((0, 0), txt, font=F(96), stroke_width=X(7))
    d.text(((X(W) - (bb[2] - bb[0])) / 2 - bb[0], X(120)), txt, font=F(96),
           fill=CREAM, stroke_width=X(7), stroke_fill=INK)
    sub = "НА КОНЦЕ СТРЕЛЫ"
    bb2 = d.textbbox((0, 0), sub, font=F(34), stroke_width=X(5))
    d.text(((X(W) - (bb2[2] - bb2[0])) / 2 - bb2[0], X(232)), sub, font=F(34),
           fill=(214, 236, 250), stroke_width=X(5), stroke_fill=INK)


def scene_balance(d, t, ctx):
    load_x, load_y = crane(d, ctx)
    # силы
    d.line(P((load_x, load_y + 70), (load_x, load_y + 170)), fill=(255, 120, 96), width=X(5))
    d.polygon(P((load_x - 12, load_y + 160), (load_x + 12, load_y + 160), (load_x, load_y + 190)),
              fill=(255, 120, 96))
    d.text(XY(load_x + 18, load_y + 96), "груз", font=F(22), fill=(255, 160, 140))
    cwx = CJIB_END + 30
    d.line(P((cwx, MAST_TOP + 74), (cwx, MAST_TOP + 10)), fill=(150, 226, 190), width=X(5))
    d.polygon(P((cwx - 12, MAST_TOP + 20), (cwx + 12, MAST_TOP + 20), (cwx, MAST_TOP - 10)),
              fill=(150, 226, 190))
    d.text(XY(cwx - 20, MAST_TOP - 44), "противовес", font=F(22), fill=(150, 226, 190))
    title(d, "МОМЕНТ ГРУЗА = МОМЕНТ ПРОТИВОВЕСА", 96, CREAM, 26)
    card_bg(d, 34, 980, W - 68, 80)
    d.text(XY(54, 996), "груз · вылет  =  противовес · плечо", font=F(24), fill=(196, 222, 244))


def scene_trolley(d, t, ctx):
    k = 0.5 + 0.45 * math.sin(min(1.0, ctx.get("scene_t", 0) / max(0.1, ctx.get("scene_dur", 1))) * math.pi - math.pi / 2)
    cx = dict(ctx)
    cx["trolley"] = 330 + 250 * k
    cx["load_y"] = 820
    load_x, load_y = crane(d, cx)
    # дуга допустимой нагрузки
    for i in range(12):
        kk = i / 11
        xx = 330 + 250 * kk
        yy = 700 + 60 * kk
        d.ellipse(P((xx - 3, yy - 3), (xx + 3, yy + 3)), fill=(255, 196, 96, 150))
    d.text(XY(330, 660), "чем дальше груз —", font=F(22), fill=(255, 214, 150))
    d.text(XY(330, 688), "тем меньше допустимый вес", font=F(22), fill=(255, 214, 150))
    title(d, "ТЕЛЕЖКА ИДЁТ ПО СТРЕЛЕ", 96, CREAM, 28)
    card_bg(d, 34, 980, W - 68, 80)
    d.text(XY(54, 996), "грузоподъёмность зависит от вылета", font=F(24), fill=(196, 222, 244))


def scene_pulley(d, t, ctx):
    crane(d, ctx)
    # врезка с полиспастом
    bx, by, bw, bh = 210, 640, 470, 370
    card_bg(d, bx, by, bw, bh, 240)
    d.text(XY(bx + 16, by + 12), "крюковая подвеска", font=F(22), fill=CYAN)
    # неподвижный блок
    d.ellipse(P((bx + 60, by + 66), (bx + 104, by + 110)), fill=(40, 50, 66),
              outline=(190, 204, 222), width=2)
    # подвижный блок
    d.ellipse(P((bx + 60, by + 176), (bx + 104, by + 220)), fill=(40, 50, 66),
              outline=(255, 196, 96), width=2)
    # ветви каната
    d.line(P((bx + 82, by + 110), (bx + 82, by + 176)), fill=(226, 236, 250), width=3)
    d.line(P((bx + 60, by + 88), (bx + 240, by + 88)), fill=(226, 236, 250), width=3)
    d.line(P((bx + 60, by + 198), (bx + 240, by + 198)), fill=(226, 236, 250), width=3)
    d.line(P((bx + 240, by + 88), (bx + 240, by + 198)), fill=(226, 236, 250), width=3)
    # барабан лебёдки
    d.rectangle(P((bx + 250, by + 70), (bx + 330, by + 216)), fill=(30, 40, 54),
                outline=(150, 170, 190), width=2)
    for i in range(6):
        yy = by + 80 + i * 22
        d.line(P((bx + 254, yy), (bx + 326, yy)), fill=(190, 204, 222, 160), width=2)
    d.text(XY(bx + 16, by + 250), "2 ветви каната → натяжение вдвое меньше веса", font=F(19),
           fill=(196, 222, 244))
    d.text(XY(bx + 84, by + 118), "ветвь 1", font=F(17), fill=(190, 214, 236))
    d.text(XY(bx + 84, by + 226), "ветвь 2", font=F(17), fill=(190, 214, 236))
    d.text(XY(bx + 256, by + 116), "барабан", font=F(17), fill=(190, 214, 236))
    title(d, "ЛЕБЁДКА И БЛОКИ", 96, CREAM, 28)


def scene_mast(d, t, ctx):
    crane(d, ctx)
    # стрелки сжатия вдоль башни
    for side in (-1, 1):
        for i in range(6):
            yy = MAST_TOP + 40 + i * 100
            xx = MAST_X + side * (MAST_W / 2 - 6)
            d.polygon(P((xx - 7, yy), (xx + 7, yy), (xx, yy + 24)), fill=(255, 196, 96, 220))
    # растяжение вант
    d.line(P((MAST_X, MAST_TOP - 58), (JIB_END - 70, MAST_TOP + 12)), fill=(150, 226, 190, 220), width=X(4))
    d.text(XY(MAST_X + 60, MAST_TOP - 30), "ванты — растяжение", font=F(18), fill=(150, 226, 190))
    d.text(XY(MAST_X + 40, MAST_TOP + 250), "башня — сжатие", font=F(22), fill=(255, 214, 150))
    # болтовой стык
    bx = 480
    card_bg(d, bx, 620, 210, 190)
    d.text(XY(bx + 12, 632), "стык секций", font=F(20), fill=CYAN)
    for i in range(2):
        yy = 672 + i * 56
        d.rectangle(P((bx + 20, yy), (bx + 190, yy + 40)), fill=(60, 72, 88), outline=(150, 168, 190))
        for j in range(5):
            d.ellipse(P((bx + 30 + j * 34, yy + 6), (bx + 38 + j * 34, yy + 14)), fill=(220, 226, 236))
    d.text(XY(bx + 12, 784), "секции на болтах", font=F(20), fill=(196, 222, 244))
    title(d, "ПОЧЕМУ БАШНЯ НЕ ЛОМАЕТСЯ", 96, CREAM, 26)


def scene_final(d, t, ctx):
    cx = dict(ctx)
    cx["trolley"] = 430
    cx["load_y"] = 700
    crane(d, cx)
    card_bg(d, 34, 120, W - 68, 300, 248)
    d.text(XY(58, 144), "Башенный кран", font=F(44), fill=CREAM)
    d.text(XY(58, 206), "принцип: баланс моментов", font=F(26), fill=(170, 206, 236))
    d.line(P((58, 246), (W - 58, 246)), fill=(255, 196, 96, 170), width=3)
    d.text(XY(58, 262), "груз · вылет = противовес · плечо", font=F(24), fill=GOLD)
    d.text(XY(58, 304), "башня — на сжатие, ванты — на растяжение", font=F(21), fill=(180, 210, 236))
    d.text(XY(58, 338), "полиспаст снижает натяжение троса", font=F(21), fill=(180, 210, 236))
    d.text(XY(58, 372), "секции наращиваются сверху", font=F(21), fill=(180, 210, 236))


SCENES = {
    "hook": scene_hook,
    "balance": scene_balance,
    "trolley": scene_trolley,
    "pulley": scene_pulley,
    "mast": scene_mast,
    "final": scene_final,
}


def render(name, t, ctx):
    img = Image.new("RGB", (X(W), X(H)), BG)
    d = ImageDraw.Draw(img, "RGBA")
    backdrop(d)
    SCENES[name](d, t, ctx)
    return img
