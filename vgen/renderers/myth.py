"""Миф про закрытие приложений: flat-vector в стиле референса.

Тёмный фон, крупный заголовок (белый + красный), верхняя UI-плашка с разделом
и прогрессом, нижняя карточка-субтитр. Пост — одним проходом ffmpeg.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

from vgen.palette import font
from vgen.renderers.ev import caption, progress

W, H, SS = 720, 1280, 2

CYAN = (86, 226, 255)
RED = (255, 74, 74)
WHITE = (240, 246, 252)
GREY = (140, 158, 176)
GREEN = (110, 220, 150)
NAVY = (8, 12, 22)


def X(v):
    return int(round(v * SS))


def P(*pts):
    return [(X(a), X(b)) for a, b in pts]


def XY(a, b):
    return (X(a), X(b))


def F(s):
    return font(s)


def bg(t=0.0):
    img = Image.new("RGB", (X(W), X(H)), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(X(H)):
        k = y / X(H)
        d.line([(0, y), (X(W), y)], fill=(int(7 + 5 * k), int(11 + 8 * k), int(20 + 13 * k)))
    # едва заметная комнатная сетка, как в референсе
    for gx in range(0, W, 48):
        d.line(P((gx, 380), (gx, 980)), fill=(13, 22, 34))
    for gy in range(380, 980, 48):
        d.line(P((0, gy), (W, gy)), fill=(13, 22, 34))
    # линия стола
    d.line(P((0, 960), (W, 960)), fill=(22, 36, 52), width=X(2))
    return img.convert("RGBA")


def top_ui(d, section, t, total):
    d.rounded_rectangle(P((26, 30), (168, 74)), radius=X(10), outline=(60, 150, 170), width=X(2))
    d.text(XY(38, 40), "VGEN.AI", font=F(20), fill=WHITE)
    d.text(XY(26, 92), "РАЗДЕЛ", font=F(13), fill=GREY)
    d.rounded_rectangle(P((96, 86), (168, 116)), radius=X(8), fill=(16, 60, 84))
    d.text(XY(106, 92), section, font=F(15), fill=CYAN)
    # тонкий прогресс раздела
    d.line(P((182, 101), (W - 26, 101)), fill=(28, 44, 60), width=X(3))
    k = max(0.0, min(1.0, t / max(0.1, total)))
    d.line(P((182, 101), (182 + (W - 208) * k, 101)), fill=CYAN, width=X(3))


def headline(d, top, bottom, sub=None):
    from vgen.renderers.ev import fit_size
    fs = fit_size(top, 74, 560)
    b = d.textbbox((0, 0), top, font=F(fs))
    d.text(XY((W - (b[2] - b[0]) / SS) / 2, 140), top, font=F(fs), fill=WHITE)
    fb = min(fs, fit_size(bottom, 74, 560))
    b2 = d.textbbox((0, 0), bottom, font=F(fb))
    d.text(XY((W - (b2[2] - b2[0]) / SS) / 2, 218), bottom, font=F(fb), fill=RED)
    if sub:
        bs = d.textbbox((0, 0), sub, font=F(22))
        d.text(XY((W - (bs[2] - bs[0]) / SS) / 2, 300), sub, font=F(22), fill=GREY)


def phone(d, x, y, w=250, h=470, screen=(10, 18, 28), border=(90, 108, 126)):
    d.rounded_rectangle(P((x, y), (x + w, y + h)), radius=X(26), fill=(12, 18, 26),
                        outline=border, width=X(3))
    d.rounded_rectangle(P((x + 8, y + 8), (x + w - 8, y + h - 8)), radius=X(20), fill=screen)
    # вырез
    d.rounded_rectangle(P((x + w / 2 - 26, y + 14), (x + w / 2 + 26, y + 26)), radius=X(6), fill=(4, 8, 12))


def app_icon(d, x, y, size, col, glyph=None, alpha=255, angle=0.0):
    d.rounded_rectangle(P((x, y), (x + size, y + size)), radius=X(size * 0.24),
                        fill=col + (alpha,), outline=(255, 255, 255, int(alpha * 0.25)), width=X(2))
    if glyph:
        b = d.textbbox((0, 0), glyph, font=F(int(size * 0.42)))
        d.text(XY(x + size / 2 - (b[2] - b[0]) / SS / 2, y + size / 2 - (b[3] - b[1]) / SS / 2),
               glyph, font=F(int(size * 0.42)), fill=(255, 255, 255, alpha))


def no_sign(d, x, y, r, alpha=255):
    d.ellipse(P((x - r, y - r), (x + r, y + r)), outline=(255, 80, 80, alpha), width=X(9))
    d.line(P((x - r * 0.66, y - r * 0.66), (x + r * 0.66, y + r * 0.66)),
           fill=(255, 80, 80, alpha), width=X(9))


def bars(d, x, y, w, labels, colors, k=1.0, grow=0.0):
    for i, (lab, col) in enumerate(zip(labels, colors)):
        yy = y + i * 74
        d.text(XY(x, yy - 4), lab, font=F(18), fill=GREY)
        d.rounded_rectangle(P((x, yy + 26), (x + w, yy + 46)), radius=X(10), fill=(24, 34, 46))
        val = min(1.0, max(0.06, (0.35 + 0.5 * ((i * 37) % 10) / 10) * k + grow * (i + 1) * 0.12))
        d.rounded_rectangle(P((x, yy + 26), (x + w * val, yy + 46)), radius=X(10), fill=col)


def battery(d, x, y, w=180, h=80, fill=0.4, label="%"):
    d.rounded_rectangle(P((x, y), (x + w, y + h)), radius=X(14), outline=(200, 215, 230), width=X(4))
    d.rectangle(P((x + w + 4, y + h * 0.3), (x + w + 14, y + h * 0.7)), fill=(200, 215, 230))
    col = GREEN if fill > 0.5 else (255, 190, 80) if fill > 0.22 else RED
    d.rounded_rectangle(P((x + 6, y + 6), (x + w - 6, y + 6 + (h - 12) * fill)), radius=X(10), fill=col)
    d.text(XY(x + w / 2 - 16, y + h + 10), label, font=F(20), fill=col)


def card(d, title, body, accent=CYAN, y=520):
    d.rounded_rectangle(P((52, y), (W - 52, y + 260)), radius=X(20), fill=(12, 20, 32, 240),
                        outline=accent + (200,), width=X(3))
    d.text(XY(80, y + 26), title, font=F(26), fill=accent)
    # перенос тела
    words = body.split()
    line, lines = "", []
    for w in words:
        t = (line + " " + w).strip()
        if d.textbbox((0, 0), t, font=F(22))[2] / SS > W - 150:
            lines.append(line)
            line = w
        else:
            line = t
    if line:
        lines.append(line)
    for i, ln in enumerate(lines[:5]):
        d.text(XY(80, y + 76 + i * 34), ln, font=F(22), fill=(220, 230, 242))


_SWEEP = {}


def sweep(img, t, alpha=26):
    """Мягкий плавающий блик: слабая подсветка, не засвечивает текст."""
    key = img.size
    if key not in _SWEEP:
        w, h = key
        m = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(m)
        d.ellipse([-w * 0.45, -h * 0.1, w * 0.45, h * 0.42], fill=255)
        _SWEEP[key] = m.filter(ImageFilter.GaussianBlur(int(w * 0.14)))
    mask = _SWEEP[key].point(lambda v: int(v * alpha / 255.0))
    layer = Image.new("RGBA", img.size, (120, 205, 245, 255))
    layer.putalpha(mask)
    x = int(W * SS * (0.15 + 0.7 * (0.5 + 0.5 * math.sin(t * 0.55))))
    y = int(H * SS * (0.15 + 0.1 * math.sin(t * 0.4)))
    shifted = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shifted.alpha_composite(layer, (x - img.width // 2, y - img.height // 4))
    return Image.alpha_composite(img.convert("RGBA"), shifted).convert("RGB")


def camera(img, t, amp=0.028, speed=0.5, scene_t=None):
    """Дрейф + смена плана внутри сцены: каждые ~3.2 с новый «кадр».

    Смена плана — это честный монтажный приём: одна и та же картинка
    читается как три разных ракурса, и ролик не залипает на одном изображении.
    """
    w, h = img.size
    punch = 0.0
    if scene_t is not None:
        shot = int(scene_t // 3.2)
        zooms = (0.0, 0.10, 0.04, 0.13)
        punch = zooms[shot % len(zooms)]
        # короткий «наезд» в первые 0.35 с нового плана
        frac = scene_t % 3.2
        if frac < 0.35 and shot > 0:
            punch += 0.03 * (1 - frac / 0.35)
    k = 1.0 + punch + amp * (0.5 + 0.5 * math.sin(t * speed))
    nw, nh = int(w * k), int(h * k)
    dx = int((nw - w) * (0.5 + 0.35 * math.sin(t * speed * 0.7)))
    dy = int((nh - h) * (0.5 + 0.35 * math.cos(t * speed * 0.6)))
    return img.resize((nw, nh), Image.BILINEAR).crop((dx, dy, dx + w, dy + h))


def scene_hook(t, ctx):
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    phone(d, 236 + 6 * math.sin(t * 0.9), 430, 250, 470)
    # знак — под иконками, чтобы не перечёркивать их
    pulse = 1.0 + 0.02 * math.sin(t * 3.0)
    no_sign(d, 360, 670, 120 * pulse, 225)
    # иконки летят вверх, но не заходят в зону заголовка
    icons = [("#2f6f9e", "▶"), ("#8a4d8a", "◎"), ("#2f7a5e", "✦"), ("#a8642f", "▲")]
    for i, (col, g) in enumerate(icons):
        ph = (t * 0.55 + i * 0.25) % 1.0
        y = 660 - ph * 210
        alpha = int(230 * (1 - ph * 0.75))
        app_icon(d, 262 + (i % 2) * 80 + 5 * math.sin(t * 2 + i), y, 64,
                 tuple(int(col[j:j + 2], 16) for j in (1, 3, 5)), g, alpha)
    headline(d, "ЗАКРЫВАЕШЬ", "ПРИЛОЖЕНИЯ ЗРЯ", None)
    top_ui(d, "МИФ", t, ctx.get("total", 50))
    return img


def scene_freeze(t, ctx):
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    phone(d, 240, 430, 240, 450)
    app_icon(d, 286, 520, 150, (40, 90, 130), "◎", 255)
    # «zzz» над приложением
    for i in range(3):
        a = int(220 - i * 55)
        drift = math.sin(t * 1.6 + i) * 8
        d.text(XY(430 + i * 14 + drift, 470 - i * 34 - (t * 12) % 30), "z",
               font=F(34 + i * 8), fill=(120, 180, 210, a))
    d.rounded_rectangle(P((486, 600), (600, 648)), radius=X(10), fill=(16, 40, 54))
    d.text(XY(498, 610), "СПИТ", font=F(20), fill=CYAN)
    headline(d, "В ФОНЕ ОНО", "ЗАМОРОЖЕНО", "система не даёт ему работать")
    top_ui(d, "ФОН", t, ctx.get("total", 50))
    return img


def scene_relaunch(t, ctx):
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    phone(d, 40, 470, 210, 400)
    app_icon(d, 78, 540, 132, (40, 90, 130), "◎", 255)
    # стрелки перезапуска
    d.arc(P((230, 590), (330, 690)), 300, 240, fill=CYAN, width=X(6))
    d.polygon(P((318, 566), (338, 596), (302, 598)), fill=CYAN)
    d.text(XY(238, 706), "заново", font=F(18), fill=CYAN)
    bars(d, 368, 470, 280, ["ПАМЯТЬ", "СЕТЬ", "ЦП"], [(120, 200, 240), (90, 220, 170), (255, 170, 90)],
         k=min(1.0, t / 2.0))
    headline(d, "ОН СТАРТУЕТ", "ЗАНОВО", "и тратит заряд на запуск")
    top_ui(d, "ЗАПУСК", t, ctx.get("total", 50))
    return img


def scene_apple(t, ctx):
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    slide = 60 * max(0.0, 1 - t / 0.8)
    # карточка-цитата
    d.rounded_rectangle(P((56, 420 + slide), (W - 56, 760 + slide)), radius=X(22), fill=(14, 22, 34, 245),
                        outline=(70, 90, 110), width=X(3))
    d.text(XY(88, 452), "APPLE", font=F(30), fill=WHITE)
    d.line(P((88, 496), (250, 496)), fill=RED, width=X(4))
    card_text = "«Принудительное закрытие приложений не продлевает работу от батареи»"
    words = card_text.split()
    line, lines = "", []
    for w in words:
        tt = (line + " " + w).strip()
        if d.textbbox((0, 0), tt, font=F(26))[2] / SS > W - 210:
            lines.append(line); line = w
        else:
            line = tt
    if line:
        lines.append(line)
    for i, ln in enumerate(lines):
        d.text(XY(88, 528 + i * 46), ln, font=F(28), fill=(230, 240, 252))
    d.text(XY(88, 706), "support.apple.com · официальная поддержка", font=F(20), fill=GREY)
    headline(d, "ЭТО НЕ", "ЭКОНОМИТ", None)
    top_ui(d, "ФАКТ", t, ctx.get("total", 50))
    return img


def scene_truth(t, ctx):
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    # три иконки: яркость, энергосбережение, сигнал
    items = [("ЯРКОСТЬ", (255, 214, 120)), ("ЭНЕРГО", (120, 220, 150)), ("СИГНАЛ", (120, 190, 240))]
    for i, (lab, col) in enumerate(items):
        x = 96 + i * 190
        d.rounded_rectangle(P((x, 470), (x + 150, 620)), radius=X(18), fill=(12, 20, 30, 240),
                            outline=col + (200,), width=X(3))
        d.ellipse(P((x + 48, 500), (x + 102, 554)), outline=col, width=X(5))
        d.text(XY(x + 20, 572), lab, font=F(17), fill=col)
    battery(d, 210, 720, 240, 90, 0.86, "86%")
    headline(d, "ЧТО РЕАЛЬНО", "РАБОТАЕТ", "яркость · энергосбережение · сигнал")
    top_ui(d, "ПОЛЬЗА", t, ctx.get("total", 50))
    return img


def scene_final(t, ctx):
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    phone(d, 250, 440, 220, 420)
    # галочка
    k = min(1.0, t / 0.9)
    seg1 = (330 - 300) * min(1.0, k * 2) + 300
    d.line(P((300, 640), (seg1, 640 + (676 - 640) * min(1.0, k * 2))), fill=GREEN, width=X(12))
    if k > 0.5:
        f2 = (k - 0.5) * 2
        d.line(P((330, 676), (330 + (392 - 330) * f2, 676 + (590 - 676) * f2)), fill=GREEN, width=X(12))
    d.text(XY(214, 900), "свайп не экономит заряд", font=F(22), fill=GREY)
    headline(d, "ЭТО ПРОСТО", "РИТУАЛ", "батарею экономит не свайп")
    top_ui(d, "ИТОГ", t, ctx.get("total", 50))
    return img


SCENES = {"hook": scene_hook, "freeze": scene_freeze, "relaunch": scene_relaunch,
          "apple": scene_apple, "truth": scene_truth, "final": scene_final}


def render(name, t, ctx):
    img = SCENES[name](t, ctx).convert("RGB")
    img = sweep(img, t)
    img = camera(img, t, scene_t=ctx.get("scene_t"))
    d = ImageDraw.Draw(img, "RGBA")
    caption(d, ctx.get("caption_text", ""), ctx.get("caption_hl", ()), 1120)
    progress(d, t, ctx.get("total", 50))
    return img
