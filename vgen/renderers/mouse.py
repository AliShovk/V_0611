"""Пиксельная анимация: как мышь видит поверхность.

Рисуем на маленьком холсте 270x480 и растягиваем NEAREST до 1080x1920 —
отсюда настоящая пиксельная сетка, а не имитация фильтром.
"""
import math
import os
import random

from PIL import Image, ImageDraw

from vgen.palette import font
from vgen.renderers.ev import fit_size

LW, LH, SCALE = 270, 480, 4
W, H = LW * SCALE, LH * SCALE

BG = (12, 14, 28)
BG2 = (15, 18, 34)
INK = (232, 240, 252)
DIM = (120, 138, 168)
CYAN = (88, 226, 255)
MAG = (255, 96, 160)
AMBER = (255, 200, 90)
RED = (255, 84, 84)
GREEN = (120, 230, 150)


def F(s):
    return font(s)


def frame():
    img = Image.new("RGB", (LW, LH), BG)
    d = ImageDraw.Draw(img)
    # пиксельная «сетка» фона
    for y in range(0, LH, 8):
        for x in range(0, LW, 8):
            if (x // 8 + y // 8) % 2 == 0:
                d.rectangle([x, y, x + 7, y + 7], fill=BG2)
    return img, d


def text(d, xy, s, size=10, fill=INK):
    d.text((int(xy[0]), int(xy[1])), s, font=F(size), fill=fill)


def text_c(d, y, s, size=12, fill=INK):
    while size > 6 and d.textbbox((0, 0), s, font=F(size))[2] > LW - 14:
        size -= 1
    b = d.textbbox((0, 0), s, font=F(size))
    d.text((int((LW - (b[2] - b[0])) / 2), y), s, font=F(size), fill=fill)


def wrap(d, s, size, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textbbox((0, 0), t, font=F(size))[2] > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def caption_box(d, s, y=400, size=11, hl=()):
    lines = wrap(d, s, size, LW - 24)
    h = 6 + len(lines) * (size + 4)
    d.rectangle([6, y, LW - 6, y + h], fill=(6, 8, 18), outline=(46, 84, 110))
    yy = y + 4
    for ln in lines:
        b = d.textbbox((0, 0), ln, font=F(size))
        x = (LW - (b[2] - b[0])) // 2
        for w in ln.split():
            ww = d.textbbox((0, 0), w, font=F(size))[2]
            key = w.lower().strip(".,!?—")
            col = CYAN if key in {h.lower() for h in hl} else INK
            d.text((x, yy), w, font=F(size), fill=col)
            x += ww + d.textbbox((0, 0), " ", font=F(size))[2]
        yy += size + 4


def hud(d, s, sub=""):
    text(d, (LW - 8 - d.textbbox((0, 0), s, font=F(12))[2], 8), s, 12, INK)
    if sub:
        text(d, (LW - 8 - d.textbbox((0, 0), sub, font=F(8))[2], 24), sub, 8, DIM)


def mouse_side(d, x, y, s=1.0):
    """Мышь в профиль, пикселями."""
    w, h = int(64 * s), int(34 * s)
    d.rectangle([x, y, x + w, y + h], fill=(196, 204, 220), outline=(60, 68, 90))
    d.rectangle([x, y, x + w, y + int(h * 0.55)], fill=(222, 228, 240))
    d.rectangle([x + int(w * 0.30), y - int(3 * s), x + int(w * 0.55), y + int(4 * s)],
                fill=(150, 158, 178))
    # шнур/антенна
    d.line([x + int(w * 0.85), y, x + int(w * 0.85) + 8, y - 10], fill=(120, 128, 150))
    # подсветка снизу
    d.rectangle([x + int(w * 0.40), y + h, x + int(w * 0.60), y + h + 2], fill=CYAN)


def desk(d, y):
    d.rectangle([0, y, LW, LH], fill=(30, 24, 40))
    for i in range(0, LW, 12):
        d.rectangle([i, y, i + 6, y + 2], fill=(44, 36, 58))
    d.line([0, y, LW, y], fill=(70, 60, 90))


def texture(d, ox, oy, w, h, seed=5, dark=False):
    """Микрорельеф: случайные пиксельные кластеры."""
    rnd = random.Random(seed)
    base = (26, 30, 48) if dark else (44, 40, 56)
    d.rectangle([ox, oy, ox + w, oy + h], fill=base)
    for _ in range(int(w * h / 14)):
        px = ox + rnd.randrange(0, w)
        py = oy + rnd.randrange(0, h)
        c = rnd.choice([(70, 64, 88), (58, 54, 74), (86, 78, 104), (40, 38, 54)])
        sz = rnd.choice([1, 1, 2, 2, 3])
        d.rectangle([px, py, px + sz, py + sz], fill=c)


def scene_hook(t, ctx):
    img, d = frame()
    desk(d, 330)
    slide = int(60 * min(1.0, t / 0.9))
    mouse_side(d, 20 + slide, 296, 1.1)
    bx = 50 + slide
    # луч вниз и точка
    d.polygon([(bx + 20, 330), (bx + 46, 330), (bx + 62, 402), (bx - 2, 402)], fill=(40, 90, 120))
    pulse = 1 + 0.6 * math.sin(t * 7)
    rr = int(4 * pulse)
    d.ellipse([bx + 30 - rr, 400 - rr, bx + 30 + rr, 402 + rr], fill=RED)
    # вспышка кадров
    for i in range(3):
        if (t * 8 + i * 0.3) % 1 < 0.25:
            d.rectangle([20 + i * 8, 250, 26 + i * 8, 256], fill=AMBER)
    text_c(d, 44, "МЫШЬ НЕ ЧУВСТВУЕТ СТОЛ", 12, INK)
    text_c(d, 62, "ОНА ЕГО ФОТОГРАФИРУЕТ", 12, MAG)
    text(d, (20, 130), "1000+ КАДРОВ В СЕКУНДУ", 9, CYAN)
    text(d, (20, 146), f"кадр {int(t * 1000) % 100000:05d}", 8, AMBER)
    caption_box(d, "камера внутри делает тысячи снимков", 404, 11, ("камера", "тысячи"))
    hud(d, "1000/с", "снимков")
    return img


def scene_inside(t, ctx):
    img, d = frame()
    # разрез корпуса
    d.rectangle([40, 150, 230, 300], fill=(196, 204, 220), outline=(60, 68, 90))
    d.rectangle([40, 150, 230, 200], fill=(222, 228, 240))
    d.rectangle([48, 208, 222, 292], fill=(24, 26, 40))
    # плата
    d.rectangle([60, 250, 210, 288], fill=(22, 74, 60), outline=(40, 120, 96))
    for i in range(6):
        d.rectangle([70 + i * 22, 258, 78 + i * 22, 266], fill=(30, 100, 80))
    # сенсор
    d.rectangle([120, 236, 148, 258], fill=(30, 34, 52), outline=CYAN)
    text(d, (122, 240), "CMOS", 7, CYAN)
    # линза
    d.ellipse([118, 210, 150, 242], fill=(70, 120, 150), outline=(150, 220, 250))
    d.ellipse([126, 218, 142, 234], fill=(180, 240, 255))
    # LED
    d.rectangle([76, 236, 100, 252], fill=(60, 40, 30), outline=(120, 80, 50))
    on = (t * 4) % 1 < 0.6
    d.ellipse([80, 238, 96, 252], fill=(255, 120, 90) if on else (120, 40, 40))
    if on:
        d.ellipse([84, 242, 92, 248], fill=(255, 220, 180))
    text(d, (78, 254), "LED", 8, AMBER)
    # световой конус
    d.polygon([(132, 244), (132, 300), (96, 330), (168, 330)], fill=(60, 30, 30))
    for i in range(6):
        ph = (t * 0.9 + i / 6) % 1.0
        py = int(248 + ph * 80)
        half = int(4 + ph * 16)
        d.rectangle([132 - half, py, 132 + half, py + 1], fill=(140, 70, 56))
    gl = int(10 * (0.5 + 0.5 * math.sin(t * 2.2)))
    d.rectangle([122 + gl, 216, 126 + gl, 226], fill=(230, 250, 255))
    # окно «что видит сенсор» — бегущая текстура
    wx, wy, ww, wh = 128, 258, 96, 36
    d.rectangle([wx, wy, wx + ww, wy + wh], fill=(20, 30, 44), outline=CYAN)
    rnd2 = random.Random(5)
    sh = int((t * 70) % ww)
    for _ in range(150):
        px = rnd2.randrange(0, ww); py = rnd2.randrange(0, wh)
        sz = rnd2.choice([2, 3, 4])
        sx = wx + (px - sh) % ww
        d.rectangle([sx, wy + py, min(wx + ww, sx + sz), wy + py + sz], fill=(120, 140, 170))
    text(d, (wx, wy - 9), "сенсор", 6, CYAN)
    # бегущий блик по корпусу
    gx = int(44 + ((t * 90) % 180))
    d.rectangle([gx, 152, gx + 6, 198], fill=(238, 244, 252))
    scan = 42 + int((t * 70) % 186)
    d.rectangle([scan, 152, scan + 3, 296], fill=(60, 140, 180))
    k = 0.5 + 0.5 * math.sin(t * 3.4)
    d.polygon([(132, 244), (132, 300), (96, 330), (168, 330)], fill=(int(50 + 40 * k), int(26 + 20 * k), int(26 + 16 * k)))
    text_c(d, 44, "ВНУТРИ МЫШИ", 12, INK)
    text_c(d, 64, "LED + ЛИНЗА + КАМЕРА", 10, CYAN)
    caption_box(d, "светодиод светит, линза строит картинку", 404, 11, ("линза",))
    hud(d, "внутри", "оптика")
    return img


def scene_surface(t, ctx):
    img, d = frame()
    ox, oy, w, h = 20, 150, 230, 170
    d.rectangle([ox, oy, ox + w, oy + h], fill=(34, 32, 48))
    rnd = random.Random(11)
    shift = int((t * 55) % w)
    for _ in range(260):
        px = rnd.randrange(0, w)
        py = rnd.randrange(0, h)
        c = rnd.choice([(70, 64, 88), (58, 54, 74), (92, 84, 110), (44, 40, 58)])
        sz = rnd.choice([2, 3, 4, 6])
        sx = ox + (px - shift) % w
        d.rectangle([sx, oy + py, min(ox + w, sx + sz), oy + py + sz], fill=c)
    d.rectangle([ox + 4, oy + 4, ox + 74, oy + 58], outline=AMBER)
    text(d, (ox + 6, oy + 6), "кадр", 7, AMBER)
    for gx in range(ox, ox + w, 10):
        d.line([gx, oy, gx, oy + h], fill=(30, 60, 80))
    for gy in range(oy, oy + h, 10):
        d.line([ox, gy, ox + w, gy], fill=(30, 60, 80))
    sy = oy + int((t * 90) % h)
    d.rectangle([ox, sy, ox + w, sy + 2], fill=(120, 220, 255))
    text_c(d, 44, "ЧТО ВИДИТ СЕНСОР", 12, INK)
    text_c(d, 64, "МИКРОРЕЛЬЕФ ПОД МЫШЬЮ", 9, DIM)
    caption_box(d, "каждый кадр — кусочек микрорельефа", 404, 11, ("микрорельеф",))
    hud(d, "3200 dpi", "разрешение")
    return img


_PAT = {}


def _pattern(w, h):
    key = (w, h)
    if key not in _PAT:
        rnd = random.Random(21)
        blocks = []
        for _ in range(150):
            blocks.append((rnd.randrange(0, w - 6), rnd.randrange(0, h - 6), rnd.choice([2, 3, 4])))
        _PAT[key] = blocks
    return _PAT[key]


def mini_frame(d, x, y, off, label, col):
    w, h = 96, 68
    d.rectangle([x, y, x + w, y + h], fill=(28, 30, 46), outline=col)
    for (px, py, sz) in _pattern(w, h):
        sx = x + (px - off) % (w - sz)
        d.rectangle([sx, y + py, sx + sz, y + py + sz], fill=(168, 176, 204))
    text(d, (x + 2, y + 2), label, 7, col)


def scene_frames(t, ctx):
    img, d = frame()
    off = int(2 + 14 * (0.5 + 0.5 * math.sin(t * 1.9)))
    mini_frame(d, 24, 140, 0, "КАДР 1", CYAN)
    mini_frame(d, 148, 140, off, "КАДР 2", AMBER)
    # стрелка сдвига
    d.line([124, 176, 144, 176], fill=MAG)
    d.polygon([(144, 172), (150, 176), (144, 180)], fill=MAG)
    text(d, (108, 184), f"+{off} px", 8, MAG)
    # полоса сопоставления
    best = int(8 + 8 * math.sin(t * 1.7))
    for i in range(18):
        h2 = int(6 + 26 * math.exp(-((i - best) ** 2) / 6))
        d.rectangle([26 + i * 12, 300 - h2, 34 + i * 12, 300], fill=CYAN if i == best else (40, 90, 110))
    d.line([26, 300, 242, 300], fill=(70, 90, 110))
    text(d, (26, 304), "поиск максимального совпадения", 7, DIM)
    text_c(d, 44, "ДВА КАДРА — ОДИН СДВИГ", 12, INK)
    text_c(d, 64, "СЕНСОР ИЩЕТ СМЕЩЕНИЕ ПАТТЕРНА", 9, DIM)
    caption_box(d, "сравнил два кадра и нашёл сдвиг", 404, 11, ("сдвиг",))
    hud(d, "+6 px", "сдвиг за кадр")
    return img


def scene_chip(t, ctx):
    img, d = frame()
    # сенсор и вычисление
    d.rectangle([86, 150, 184, 230], fill=(16, 40, 58), outline=CYAN)
    text_c(d, 158, "СЕНСОР", 10, CYAN)
    text_c(d, 176, "Δx Δy", 14, INK)
    # входы кадров
    for i, y in enumerate((140, 240)):
        d.line([40, y, 86, y], fill=CYAN)
        mini_frame(d, 10, y - 20, int((t * 46 + i * 17) % 90), f"N{i+1}", AMBER if i else CYAN)
        ph = (t * 1.4 + i * 0.5) % 1.0
        d.rectangle([int(40 + ph * 44), y - 1, int(40 + ph * 44) + 3, y + 1], fill=(230, 250, 255))
    # выход
    d.line([184, 190, 232, 190], fill=MAG)
    d.polygon([(232, 186), (240, 190), (232, 194)], fill=MAG)
    text(d, (192, 172), f"dx={int(2 + 14 * abs(math.sin(t * 2.4)))}", 7, MAG)
    # формула
    text_c(d, 262, "сдвиг × разрешение = перемещение", 9, DIM)
    text_c(d, 284, "1000 Гц → 1000 измерений в секунду", 9, INK)
    text_c(d, 44, "СЕНСОР СЧИТАЕТ", 12, INK)
    text_c(d, 64, "НЕ КАРТИНКУ, А СДВИГ", 10, CYAN)
    caption_box(d, "на выходе — не фото, а dx и dy", 404, 11, ("dx", "dy"))
    hud(d, "1000 Гц", "опрос")
    return img


def scene_final(t, ctx):
    img, d = frame()
    desk(d, 300)
    # курсор едет по столу
    cx = int(40 + (t * 30) % 180)
    mouse_side(d, cx, 270, 0.9)
    # курсор на «экране»
    d.rectangle([20, 110, 250, 210], fill=(18, 22, 36), outline=(70, 90, 120))
    px = int(30 + (t * 34) % 190)
    py = int(140 + 20 * math.sin(t * 2))
    d.polygon([(px, py), (px, py + 12), (px + 4, py + 9), (px + 7, py + 14), (px + 10, py + 12), (px + 7, py + 8), (px + 12, py + 7)],
              fill=INK)
    text_c(d, 44, "НА ВЫХОДЕ — КУРСОР", 12, INK)
    text_c(d, 64, "МЫШЬ ВИДИТ ДВИЖЕНИЕ", 10, MAG)
    caption_box(d, "движение руки стало движением курсора", 404, 11, ("курсор",))
    hud(d, "готово", "сигнал")
    return img


SCENES = {"hook": scene_hook, "inside": scene_inside, "surface": scene_surface,
          "frames": scene_frames, "chip": scene_chip, "final": scene_final}


def render(name, t, ctx):
    img = SCENES[name](t, ctx).convert("RGB")
    # квантуем палитру: сглаженные края шрифта превращаются в честные пиксели
    img = img.quantize(colors=24, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    big = img.resize((W, H), Image.NEAREST)
    d = ImageDraw.Draw(big, "RGBA")
    for y in range(0, H, 8):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 36))
    return big
