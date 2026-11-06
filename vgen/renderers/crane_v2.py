"""Башенный кран v2: сцена-хук на vgen.kit (Skia) — сумерки, объём, камера, параллакс.

Интерфейс тот же, что у остальных рендереров: render(name, t, ctx) -> PIL.Image 1080x1920.
Пока реализован только `hook`; остальные сцены переносятся по тому же шаблону.
"""
import math
import random

from vgen import postfx
from vgen.kit import Canvas, W, H, lin, rad, tube, truss

# палитра
INK = "#070d1a"
CREAM = "#fff1c4"
GOLD = "#ffc45e"
CYAN = "#7fe4ff"
PAINT = "#f2b624"
PAINT_D = "#8a5a08"
PAINT_L = "#ffe9a0"

HORIZON = 1540
MAST_X = 300
JIB_Y = 780
JIB_END = 960
TROLLEY_X = 835


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


# --- фон ---------------------------------------------------------------------

def sky(cv, t):
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, HORIZON + 80, [
        (0.00, "#050a18"), (0.40, "#0d1c3d"), (0.68, "#2a3f6e"),
        (0.88, "#a45f6a"), (1.00, "#f0a066")]))
    # закатное свечение за городом
    cv.rect(0, 700, W, H, fill=rad(760, HORIZON + 20, 980, [
        (0.0, "#ffb26be0"), (0.35, "#ff8a5c55"), (1.0, "#ff7a5000")]))
    rnd = random.Random(11)
    for _ in range(110):
        x, y = rnd.uniform(0, W), rnd.uniform(0, 760)
        a = rnd.uniform(0.25, 0.9) * (0.7 + 0.3 * math.sin(t * 1.3 + x))
        cv.circle(x, y, rnd.uniform(0.7, 1.7), fill="#dfeaff", alpha=max(0.0, a * (1 - y / 900)))
    # дрейфующие облака
    for i, (cx, cy, w, h, a) in enumerate([(220, 880, 560, 54, 0.20), (820, 1010, 640, 62, 0.17),
                                           (480, 1190, 700, 50, 0.16), (940, 760, 420, 36, 0.13)]):
        x = (cx + t * (6 + 3 * i)) % (W + 600) - 300
        cv.oval(x - w / 2, cy - h / 2, x + w / 2, cy + h / 2, fill="#ffb3a0", alpha=a, blur=26)


def small_crane(cv, x, base, h, col):
    """Силуэт дальнего крана."""
    cv.rect(x - 2.5, base - h, x + 2.5, base, fill=col)
    cv.rect(x - h * 0.45, base - h, x + h * 0.55, base - h + 3, fill=col)
    cv.line(x, base - h - 16, x + h * 0.5, base - h, col, 1.2)
    cv.line(x, base - h - 16, x - h * 0.4, base - h, col, 1.2)
    cv.rect(x - h * 0.45, base - h, x - h * 0.3, base - h + 9, fill=col)


def skyline(cv, base, seed, col, hmin, hmax, win=None, cranes=0, t=0.0):
    rnd = random.Random(seed)
    x = -20
    while x < W + 20:
        w = rnd.randint(50, 120)
        h = rnd.randint(hmin, hmax)
        cv.rect(x, base - h, x + w, base + 400, fill=col)
        if win:
            for yy in range(int(base - h + 14), int(base - 10), 19):
                for xx in range(int(x + 8), int(x + w - 10), 15):
                    if rnd.random() < 0.30:
                        cv.rect(xx, yy, xx + 5, yy + 8, fill=win, alpha=rnd.uniform(0.35, 0.95))
        x += w + rnd.randint(0, 8)
    r2 = random.Random(seed + 5)
    for _ in range(cranes):
        small_crane(cv, r2.uniform(80, W - 80), base - 40, r2.randint(150, 230), col)


def ground_fog(cv, y0, y1, color):
    cv.rect(0, y0, W, y1, fill=lin(0, y0, 0, y1, [(0, color + "00"), (1, color + "f2")]))


# --- кран --------------------------------------------------------------------

def mast(cv):
    top, bot = JIB_Y - 10, H + 60
    cells = int((bot - top) / 92)
    # два «пояса»: левый темнее, правый на свету закатного неба
    tw = 66
    truss(cv, MAST_X, top, MAST_X, bot, tw * 2, cells, w=8, rungs=True)
    # стыки секций
    for i in range(cells + 1):
        y = top + i * (bot - top) / cells
        cv.rrect(MAST_X - tw - 7, y - 4, MAST_X + tw + 7, y + 4, 2, fill="#d89a14")
        cv.rect(MAST_X - tw - 7, y - 4, MAST_X + tw + 7, y - 2, fill=PAINT_L, alpha=0.7)


def apex_and_jibs(cv, t):
    # оголовок
    truss(cv, MAST_X, JIB_Y - 8, MAST_X, JIB_Y - 215, 66, 4, w=6, rungs=True)
    cv.poly([(MAST_X - 34, JIB_Y - 205), (MAST_X + 34, JIB_Y - 205), (MAST_X, JIB_Y - 260)], fill="#d89a14")
    # стрела и противовесная консоль
    truss(cv, MAST_X, JIB_Y, JIB_END, JIB_Y, 62, 20, w=6)
    truss(cv, MAST_X, JIB_Y + 4, 70, JIB_Y + 4, 46, 7, w=6)
    # тяги
    for (px, py) in [(620, JIB_Y - 31), (915, JIB_Y - 31), (110, JIB_Y - 19)]:
        tube(cv, MAST_X, JIB_Y - 254, px, py, 2.6, "#cfd8e6", "#4a5568", "#ffffff", glow=False)
    # огни
    blink = 0.5 + 0.5 * math.sin(t * 5.0)
    for (x, y) in [(MAST_X, JIB_Y - 270), (JIB_END + 4, JIB_Y - 33), (66, JIB_Y - 24)]:
        cv.circle(x, y, 26, fill=rad(x, y, 26, [(0, "#ff4040"), (1, "#ff404000")]), alpha=0.25 + 0.75 * blink)
        cv.circle(x, y, 5, fill="#ff8080")
    # противовес
    for i in range(3):
        y = JIB_Y + 28 + i * 40
        cv.rrect(84, y, 214, y + 36, 3, fill=lin(0, y, 0, y + 36, [(0, "#9aa1ad"), (1, "#4c525d")]),
                 shadow=(0, 3, 4, "#0008"))
        cv.rect(88, y + 2, 210, y + 5, fill="#e3e8ef", alpha=0.65)
        cv.line(100, y + 18, 198, y + 18, "#3a3f49", 1.4)
    # кабина (на подвесе под стрелой)
    for dx in (86, 168):
        tube(cv, MAST_X + dx, JIB_Y + 31, MAST_X + dx, JIB_Y + 26, 6, "#9aa3b0", "#3c4552", "#e8eef6", glow=False)
    cv.rrect(MAST_X + 70, JIB_Y + 24, MAST_X + 178, JIB_Y + 104, 8,
             fill=lin(0, JIB_Y + 24, 0, JIB_Y + 104, [(0, "#fbfcfe"), (1, "#aeb7c4")]),
             shadow=(0, 6, 8, "#0009"))
    cv.rrect(MAST_X + 90, JIB_Y + 38, MAST_X + 164, JIB_Y + 80, 5,
             fill=lin(0, JIB_Y + 38, 0, JIB_Y + 80, [(0, "#ffe7a4"), (1, "#e2923c")]))
    cv.line(MAST_X + 94, JIB_Y + 44, MAST_X + 128, JIB_Y + 44, "#ffffffa0", 3)


def trolley_and_load(cv, t, show_tag=1.0):
    sway = 1.8 * math.sin(t * 2.3 + 0.4) * (0.4 + 0.6 * ease(t / 1.2))
    tx, ty = TROLLEY_X, JIB_Y + 36
    # тележка
    cv.rrect(tx - 36, ty - 12, tx + 36, ty + 20, 5, fill=lin(0, ty - 12, 0, ty + 20, [(0, "#ffb347"), (1, "#c4691a")]),
             shadow=(0, 4, 5, "#0009"))
    for dx in (-22, 22):
        cv.circle(tx + dx, ty + 24, 8, fill="#181c24")
        cv.circle(tx + dx - 2, ty + 22, 3, fill="#ffffff55")
    cv.save()
    cv.rotate(sway, tx, ty)
    # канат
    hook_y = JIB_Y + 305
    cv.line(tx - 4, ty + 22, tx - 4, hook_y, "#2a313d", 4)
    cv.line(tx + 4, ty + 22, tx + 4, hook_y, "#2a313d", 4)
    cv.line(tx - 4.8, ty + 22, tx - 4.8, hook_y, "#d6deea", 1.2, alpha=0.8)
    # крюковая подвеска
    cv.rrect(tx - 24, hook_y, tx + 24, hook_y + 52, 8, fill=lin(0, hook_y, 0, hook_y + 52, [(0, "#ffd04a"), (1, "#b87d10")]),
             shadow=(0, 4, 5, "#000a"))
    for dx in (-10, 10):
        cv.circle(tx + dx, hook_y + 20, 9, fill="#12161e")
        cv.circle(tx + dx, hook_y + 20, 3.2, fill="#8a94a6")
    cv.line(tx, hook_y + 52, tx, hook_y + 74, "#3a4150", 10)
    # груз: плита с объёмом (фронт + верх + бок)
    lx0, lx1, ly0, ly1 = tx - 140, tx + 100, JIB_Y + 495, JIB_Y + 615
    ox, oy = 44, -26
    for (ax, ay) in [(lx0 + 22, ly0), (lx1 - 14, ly0)]:   # стропы
        tube(cv, tx, hook_y + 74, ax, ay, 5, "#ff8a2a", "#7a3208", "#ffd0a0")
        cv.circle(ax, ay, 8, fill="#cfd5df", stroke=None)
    # тень груза на дымке не нужна — груз высоко
    cv.poly([(lx0, ly0), (lx1, ly0), (lx1 + ox, ly0 + oy), (lx0 + ox, ly0 + oy)],
            fill=lin(0, ly0 + oy, 0, ly0, [(0, "#e5e9ef"), (1, "#bcc3cd")]))
    cv.poly([(lx1, ly0), (lx1 + ox, ly0 + oy), (lx1 + ox, ly1 + oy), (lx1, ly1)],
            fill=lin(lx1, 0, lx1 + ox, 0, [(0, "#7c8491"), (1, "#4d5460")]))
    cv.rect(lx0, ly0, lx1, ly1, fill=lin(lx0, ly0, lx1, ly1, [(0, "#b9c0ca"), (1, "#7b838f")]),
            shadow=(0, 10, 12, "#000b"))
    for i in range(1, 4):
        y = ly0 + i * (ly1 - ly0) / 4
        cv.line(lx0, y, lx1, y, "#4b525d", 2.2)
        cv.line(lx0, y + 2, lx1, y + 2, "#ffffff40", 1.2)
    cv.line(lx0 + 2, ly0 + 2, lx1 - 2, ly0 + 2, "#ffffffa0", 2.2)
    # бирка 50 т
    a = ease(show_tag)
    if a > 0:
        cx, cy = (lx0 + lx1) / 2, (ly0 + ly1) / 2
        cv.rrect(cx - 94, cy - 40, cx + 94, cy + 40, 12, fill="#0b1220", stroke=None,
                 shadow=(0, 4, 8, "#0009"), alpha=0.92 * a)
        cv.rrect(cx - 94, cy - 40, cx + 94, cy + 40, 12, stroke=CYAN, width=3, alpha=a)
        cv.text("50 т", cx, cy + 22, 66, fill=CREAM, center=True, alpha=a, glow=(GOLD, 8))
    cv.restore()


# --- кадр --------------------------------------------------------------------

def hook(cv, t):
    k = ease(t / 3.2)
    cam = 1.0 + 0.06 * k
    bg = 1.0 + 0.03 * k

    cv.save()
    cv.zoom(bg, 700, 1000)
    sky(cv, t)
    skyline(cv, HORIZON + 10, 3, "#6a4a66", 90, 230, cranes=3)
    cv.restore()

    cv.save()
    cv.zoom(cam, 700, 1000)
    mast(cv)
    apex_and_jibs(cv, t)
    trolley_and_load(cv, t, show_tag=(t - 0.7) / 0.5)
    cv.restore()

    cv.save()
    cv.zoom(bg * 1.01, 700, 1000)
    ground_fog(cv, 1380, HORIZON + 80, "#c98068")
    skyline(cv, HORIZON + 90, 8, "#241d3b", 70, 190, win="#ffd98a", t=t)
    skyline(cv, HORIZON + 190, 21, "#0e1226", 60, 150, win="#ffe9b0", t=t)
    cv.restore()
    cv.rect(0, HORIZON + 190, W, H, fill=lin(0, HORIZON + 190, 0, H, [(0, "#0e1226"), (1, "#05070f")]))

    # затемнение сверху под заголовок и снизу под субтитры
    cv.rect(0, 0, W, 560, fill=lin(0, 0, 0, 560, [(0, "#04081099"), (1, "#04081000")]))
    cv.rect(0, 1700, W, H, fill=lin(0, 1700, 0, H, [(0, "#05070f00"), (1, "#05070fe6")]))

    # брендовые чипы
    cv.rrect(36, 40, 176, 92, 14, fill="#0b1220", alpha=0.8)
    cv.rrect(36, 40, 176, 92, 14, stroke="#e8f2ff", width=2.5)
    cv.text("VGEN", 106, 77, 30, fill="#ffffff", center=True)
    cv.rrect(36, 104, 232, 148, 12, fill="#0b1220", alpha=0.8)
    cv.rrect(36, 104, 232, 148, 12, stroke="#ff7a5a", width=2.5)
    cv.text("ИНЖЕНЕРИЯ", 134, 135, 24, fill="#ffd2c4", center=True)

    # заголовок: появление с упругим «ударом»
    a = ease((t - 0.15) / 0.45)
    if a > 0:
        s = 0.86 + 0.14 * a + 0.035 * math.sin(a * math.pi)
        cv.save()
        cv.zoom(s, W / 2, 330)
        cv.text("50 ТОНН", W / 2, 360, 196, fill=lin(0, 200, 0, 380, [(0, "#fffbe6"), (0.55, "#ffd77a"), (1, "#f09a2a")]),
                stroke=INK, stroke_w=18, center=True, glow=("#ffb347", 28), shadow=(0, 8, 10, "#000c"),
                alpha=a)
        cv.restore()
    a2 = ease((t - 0.55) / 0.5)
    if a2 > 0:
        txt = "НА КОНЦЕ СТРЕЛЫ"
        tw = cv.text_w(txt, 52)
        y = 470 + (1 - a2) * 18
        cv.rrect(W / 2 - tw / 2 - 34, y - 54, W / 2 + tw / 2 + 34, y + 22, 18, fill="#08101e", alpha=0.78 * a2)
        cv.rrect(W / 2 - tw / 2 - 34, y - 54, W / 2 + tw / 2 + 34, y + 22, 18, stroke=CYAN, width=3, alpha=a2)
        cv.text(txt, W / 2, y, 52, fill="#d9f6ff", center=True, alpha=a2)


SCENES = {"hook": hook}


def render(name, t, ctx=None, finish=True):
    cv = Canvas()
    SCENES[name](cv, t)
    img = cv.to_pil()
    if finish:
        img = postfx.finish(img, grain_amt=3, vig=0.22)
    return img
