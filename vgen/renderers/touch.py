"""Как экран понимает касание: ёмкостная сетка под стеклом."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

from vgen import postfx
from vgen.palette import font
from vgen.renderers.ev import caption, progress

W, H, SS = 720, 1280, 2
ART = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art")
PHONE = Image.open(os.path.join(ART, "phone.png")).convert("RGBA")

CYAN = (86, 226, 255)
CYAN_D = (28, 120, 150)
CREAM = (255, 232, 196)
WHITE = (240, 248, 255)
GREY = (150, 172, 190)
ORANGE = (255, 150, 90)


def X(v):
    return int(round(v * SS))


def P(*pts):
    return [(X(a), X(b)) for a, b in pts]


def XY(a, b):
    return (X(a), X(b))


def F(s):
    return font(s)


def bg(t=0.0):
    img = Image.new("RGB", (X(W), X(H)), (6, 10, 18))
    d = ImageDraw.Draw(img)
    for y in range(X(H)):
        k = y / X(H)
        d.line([(0, y), (X(W), y)], fill=(int(7 + 5 * k), int(11 + 8 * k), int(20 + 12 * k)))
    # едва заметная сетка
    for gx in range(0, W, 40):
        d.line(P((gx, 0), (gx, H)), fill=(14, 26, 40))
    for gy in range(0, H, 40):
        d.line(P((0, gy), (W, gy)), fill=(14, 26, 40))
    return img.convert("RGBA")


_PCACHE = {}


def _phone_assets(width):
    w = X(width)
    if w not in _PCACHE:
        p = PHONE.resize((w, int(PHONE.height * w / PHONE.width)), Image.LANCZOS)
        halo = p.filter(ImageFilter.GaussianBlur(18))
        a = halo.split()[-1].point(lambda v: int(v * 0.55))
        tint = Image.new("RGBA", halo.size, (60, 200, 255, 0))
        tint.putalpha(a)
        _PCACHE[w] = (p, tint)
    return _PCACHE[w]


def phone(img, cx, cy, width=520, glow=0.0):
    p, tint = _phone_assets(width)
    if glow > 0:
        t = tint.copy()
        t.putalpha(tint.split()[-1].point(lambda v: int(v * glow)))
        img.alpha_composite(t, (int(X(cx) - p.width / 2), int(X(cy) - p.height / 2)))
    img.alpha_composite(p, (int(X(cx) - p.width / 2), int(X(cy) - p.height / 2)))
    return img


def finger(img, x, y, s=1.0, angle=0.0, alpha=1.0):
    """Палец сверху-сбоку: капсула + подушечка."""
    pad_w, pad_h = 120 * s, 150 * s
    f = Image.new("RGBA", (X(pad_w * 2.2), X(pad_h * 2.4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(f)
    d.rounded_rectangle(P((pad_w * 0.55, pad_h * 0.35), (pad_w * 1.5, pad_h * 2.0)),
                        radius=X(pad_w * 0.45), fill=(226, 178, 146, int(255 * alpha)),
                        outline=(120, 80, 60, int(220 * alpha)), width=X(4))
    d.ellipse(P((pad_w * 0.5, pad_h * 0.2), (pad_w * 1.5, pad_h * 1.15)),
              fill=(238, 192, 160, int(255 * alpha)), outline=(120, 80, 60, int(220 * alpha)), width=X(4))
    d.ellipse(P((pad_w * 0.78, pad_h * 0.42), (pad_w * 1.2, pad_h * 0.82)),
              fill=(248, 214, 186, int(210 * alpha)))
    if angle:
        f = f.rotate(angle, resample=Image.BICUBIC, expand=False)
    img.alpha_composite(f, (int(X(x) - f.width / 2), int(X(y) - f.height / 2)))


def ripple(d, x, y, r, alpha):
    for i, k in enumerate((1.0, 1.6, 2.2)):
        d.ellipse(P((x - r * k, y - r * k), (x + r * k, y + r * k)),
                  outline=(86, 226, 255, int(alpha * (0.7 - i * 0.2))), width=X(3))


def headline(d, top, bottom=None, sub=None, y=120, accent=CYAN):
    from vgen.renderers.ev import fit_size
    fs = fit_size(top, 86, 640)
    b = d.textbbox((0, 0), top, font=F(fs))
    d.text(XY((W - (b[2] - b[0]) / SS) / 2, y), top, font=F(fs), fill=WHITE,
           stroke_width=X(3), stroke_fill=(6, 10, 16, 170))
    if bottom:
        fb = min(fs, fit_size(bottom, 86, 640))
        b2 = d.textbbox((0, 0), bottom, font=F(fb))
        d.text(XY((W - (b2[2] - b2[0]) / SS) / 2, y + 104), bottom, font=F(fb), fill=accent,
               stroke_width=X(3), stroke_fill=(6, 10, 16, 170))
    if sub:
        bs = d.textbbox((0, 0), sub, font=F(25))
        d.text(XY((W - (bs[2] - bs[0]) / SS) / 2, y + (212 if bottom else 108)), sub,
               font=F(25), fill=GREY)


def badge(d, tag="КАСАНИЕ"):
    d.rounded_rectangle(P((26, 28), (132, 66)), radius=X(8), outline=(236, 244, 252), width=X(2))
    d.text(XY(36, 36), "VGEN", font=F(22), fill=WHITE)
    d.rounded_rectangle(P((26, 74), (176, 104)), radius=X(8), fill=(10, 40, 56, 220),
                        outline=CYAN_D, width=X(2))
    d.text(XY(34, 80), tag, font=F(18), fill=CYAN)


def scene_hook(t, ctx):
    img = bg().convert("RGBA")
    k = min(1.0, t / max(0.1, ctx.get("scene_dur", 6)))
    phone(img, 360, 880, 540, glow=0.6)
    d = ImageDraw.Draw(img, "RGBA")
    # точка касания и расходящиеся волны
    tx, ty = 300, 700
    pulse = (t * 1.6) % 1.0
    ripple(d, tx, ty, 40 + 90 * pulse, 180 * (1 - pulse))
    # палец подходит сверху
    fy = 380 + 300 * min(1.0, k * 1.4)
    finger(img, tx, fy, 0.85)
    d = ImageDraw.Draw(img, "RGBA")
    headline(d, "ЭКРАН НЕ ЧУВСТВУЕТ", "НАЖАТИЕ", "он чувствует твоё электричество", 96, CYAN)
    badge(d)
    return img


def layer(d, y, h, fill, edge):
    d.rectangle(P((40, y), (W - 40, y + h)), fill=fill, outline=edge, width=X(2))


def scene_stack(t, ctx):
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    # разрез: палец, стекло, слой электродов, дисплей
    finger(img, 430, 470, 0.9)
    d = ImageDraw.Draw(img, "RGBA")
    layer(d, 560, 30, (120, 160, 185, 90), (170, 210, 235, 220))
    d.text(XY(56, 528), "стекло", font=F(22), fill=CREAM)
    layer(d, 600, 26, (26, 90, 110, 230), (86, 226, 255, 235))
    d.text(XY(56, 632), "сетка электродов", font=F(22), fill=CYAN)
    layer(d, 636, 34, (18, 26, 38, 240), (70, 90, 120, 220))
    d.text(XY(56, 676), "дисплей", font=F(22), fill=GREY)
    layer(d, 680, 60, (12, 18, 26, 245), (40, 56, 74, 220))
    # силовые линии поля к пальцу
    for i in range(7):
        x = 300 + i * 26
        d.arc(P((x - 30, 470), (x + 30, 610)), 200, 340, fill=(86, 226, 255, 150), width=X(2))
    d.ellipse(P((392, 574), (468, 606)), outline=CYAN, width=X(3))
    headline(d, "ПОД СТЕКЛОМ", "СЕТКА", "прозрачные электроды из ITO", 96)
    badge(d)
    return img


def scene_grid(t, ctx):
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    x0, y0, x1, y1 = 90, 420, 630, 940
    cols, rows = 8, 10
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    # электроды
    for i in range(cols + 1):
        x = x0 + i * cw
        d.line(P((x, y0), (x, y1)), fill=(40, 96, 120, 200), width=X(2))
    for j in range(rows + 1):
        y = y0 + j * ch
        d.line(P((x0, y), (x1, y)), fill=(40, 96, 120, 200), width=X(2))
    # точка касания между узлами
    tx, ty = x0 + 3.35 * cw, y0 + 5.6 * ch
    for i in range(cols):
        for j in range(rows):
            cx, cy = x0 + (i + 0.5) * cw, y0 + (j + 0.5) * ch
            dist = math.hypot(cx - tx, cy - ty)
            a = max(0, 1 - dist / (cw * 2.2))
            if a > 0.02:
                d.ellipse(P((cx - 10, cy - 10), (cx + 10, cy + 10)),
                          fill=(86, 226, 255, int(210 * a)))
    ripple(d, tx, ty, 26, 220)
    d.line(P((tx, 380), (tx, 1000)), fill=(120, 200, 225, 90), width=X(1))
    d.line(P((60, ty), (660, ty)), fill=(120, 200, 225, 90), width=X(1))
    d.text(XY(tx + 12, 356), "X", font=F(22), fill=CYAN)
    d.text(XY(36, ty - 12), "Y", font=F(22), fill=CYAN)
    headline(d, "КООРДИНАТЫ", "МЕЖДУ УЗЛАМИ", "интерполяция точнее электрода", 96)
    badge(d)
    return img


def scene_chip(t, ctx):
    img = bg().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    # контроллер
    d.rounded_rectangle(P((240, 700), (480, 880)), radius=X(18), fill=(14, 34, 48, 255),
                        outline=CYAN, width=X(4))
    d.text(XY(268, 736), "КОНТРОЛЛЕР", font=F(28), fill=CYAN)
    d.text(XY(268, 786), "120 Гц", font=F(46), fill=WHITE)
    d.text(XY(268, 840), "опрос сетки", font=F(20), fill=GREY)
    # входы X/Y
    for i, y in enumerate((740, 800, 860)):
        d.line(P((150, y), (240, y)), fill=(86, 226, 255, 170), width=X(3))
        d.ellipse(P((142, y - 6), (158, y + 6)), fill=CYAN)
    # выход координат
    d.line(P((480, 790), (580, 790)), fill=ORANGE, width=X(4))
    d.polygon(P((580, 778), (604, 790), (580, 802)), fill=ORANGE)
    d.text(XY(500, 748), "x, y", font=F(26), fill=ORANGE)
    # тактовая дорожка
    for i in range(12):
        x = 90 + i * 26
        d.line(P((x, 980), (x, 1010 if i % 2 == 0 else 1000)), fill=(70, 110, 130), width=X(3))
    d.text(XY(90, 1024), "каждый такт — новое касание", font=F(20), fill=GREY)
    headline(d, "КОНТРОЛЛЕР", "СЧИТАЕТ", "по двум осям за один такт", 96)
    badge(d)
    return img


def scene_final(t, ctx):
    img = bg().convert("RGBA")
    phone(img, 360, 760, 470, glow=0.4)
    d = ImageDraw.Draw(img, "RGBA")
    rows = [("120 Гц", "частота опроса", CYAN), ("~10 мс", "до реакции", ORANGE), ("0", "нужно давления", WHITE)]
    y = 470
    for big, small, col in rows:
        d.text(XY(70, y), big, font=F(48), fill=col)
        d.text(XY(70, y + 58), small, font=F(22), fill=GREY)
        y += 130
    headline(d, "ТВОЙ ПАЛЕЦ", "ПРОВОДНИК", "экран просто измеряет ёмкость", 96, CYAN)
    badge(d)
    return img


SCENES = {"hook": scene_hook, "stack": scene_stack, "grid": scene_grid,
          "chip": scene_chip, "final": scene_final}


def render(name, t, ctx):
    img = SCENES[name](t, ctx).convert("RGBA")
    # пост-обработка делается одним проходом ffmpeg (project.post = true):
    # так дешевле в 10 раз и текст не выгорает
    art = img.convert("RGB")
    d = ImageDraw.Draw(art, "RGBA")
    caption(d, ctx.get("caption_text", ""), ctx.get("caption_hl", ()), 1148)
    progress(d, t, ctx.get("total", 58.0))
    return art
