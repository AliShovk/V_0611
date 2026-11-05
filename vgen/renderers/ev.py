"""EV-объяснялка в стиле night-neon: тёмный фон, циан, крупный заголовок, плашки."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

from vgen.palette import font

W, H, SS = 720, 1280, 2
ART = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art")

CAR = Image.open(os.path.join(ART, "ev_car2.png")).convert("RGBA")

CYAN = (86, 226, 255)
CYAN_DIM = (44, 120, 150)
WHITE = (240, 248, 255)
GREY = (150, 172, 190)
RED = (255, 92, 92)
YELLOW = (255, 226, 120)
BG1 = (6, 10, 22)
BG2 = (10, 22, 42)


def X(v):
    return int(round(v * SS))


def P(*pts):
    return [(X(a), X(b)) for a, b in pts]


def XY(a, b):
    return (X(a), X(b))


def F(size):
    return font(size)


def bg(t=0.0):
    img = Image.new("RGB", (X(W), X(H)), BG1)
    d = ImageDraw.Draw(img)
    for y in range(X(H)):
        k = y / X(H)
        c = tuple(int(BG1[i] + (BG2[i] - BG1[i]) * k) for i in range(3))
        d.line([(0, y), (X(W), y)], fill=c)
    # звёзды
    rnd = random.Random(7)
    for _ in range(90):
        x, y = rnd.randrange(X(W)), rnd.randrange(X(760))
        r = rnd.choice([1, 1, 1, 2])
        d.ellipse([x, y, x + r, y + r], fill=(190, 215, 240))
    # wireframe город
    rnd = random.Random(21)
    for i in range(11):
        bw = rnd.randint(40, 96)
        bx = rnd.randint(-20, W - 20)
        bh = rnd.randint(90, 300)
        top = 760 - bh
        d.rectangle(P((bx, top), (bx + bw, 760)), outline=(30, 110, 140), width=X(2))
        for k in range(1, 4):
            yy = top + (bh * k / 4)
            d.line(P((bx, yy), (bx + bw, yy)), fill=(24, 90, 118), width=X(1))
    # дорога
    d.rectangle(P((0, 950), (W, 1280)), fill=(9, 14, 24))
    d.rectangle(P((0, 950), (W, 962)), fill=(16, 30, 44))
    for i in range(7):
        x = (i * 130 + (t * 260) % 130)
        d.rectangle(P((x, 1092), (x + 70, 1098)), fill=(50, 70, 88))
    # отражение-блик
    d.polygon(P((520, 950), (720, 950), (720, 1280), (300, 1280)), fill=(18, 44, 66))
    return img


def car_img(width):
    h = int(CAR.height * width / CAR.width)
    return CAR.resize((X(width), X(h)), Image.LANCZOS)


def paste_car(img, cx, cy, width=560, bob=0.0):
    c = car_img(width)
    img.alpha_composite(c, (int(X(cx) - c.width / 2), int(X(cy) - c.height / 2 + bob * SS)))


def fit_size(text, start, max_w):
    size = start
    while size > 34:
        b = ImageDraw.Draw(Image.new("RGB", (10, 10))).textbbox((0, 0), text, font=F(size))
        if (b[2] - b[0]) / SS <= max_w:
            break
        size -= 4
    return size


def headline(d, top, bottom=None, sub=None):
    fs = fit_size(top, 92, 640)
    bb = d.textbbox((0, 0), top, font=F(fs))
    tw = bb[2] - bb[0]
    d.text(XY((W - tw / SS) / 2, 128), top, font=F(fs), fill=WHITE)
    if bottom:
        fb = min(fs, fit_size(bottom, 92, 640))
        bb2 = d.textbbox((0, 0), bottom, font=F(fb))
        tw2 = bb2[2] - bb2[0]
        d.text(XY((W - tw2 / SS) / 2, 236), bottom, font=F(fb), fill=CYAN)
    if sub:
        bbs = d.textbbox((0, 0), sub, font=F(28))
        d.text(XY((W - (bbs[2] - bbs[0]) / SS) / 2, 350), sub, font=F(28), fill=GREY)


def badge(d, label="VGEN", tag="ИНЖЕНЕРИЯ"):
    d.rounded_rectangle(P((26, 28), (132, 66)), radius=X(8), outline=(230, 240, 255), width=X(2))
    d.text(XY(36, 36), label, font=F(22), fill=WHITE)
    d.rounded_rectangle(P((26, 74), (150, 104)), radius=X(8), fill=(12, 44, 62), outline=CYAN_DIM, width=X(2))
    d.text(XY(34, 80), tag, font=F(18), fill=CYAN)


def caption(d, text, hl_words=(), y=1150):
    """Плашка-субтитр: ключевое слово в рамке, как в референсе."""
    if not text:
        return
    words = text.split()
    f = F(34)
    space = 10
    widths = [d.textbbox((0, 0), w, font=f)[2] - d.textbbox((0, 0), w, font=f)[0] for w in words]

    # перенос на 2 строки
    maxw = X(W - 80)
    lines, cur, curw = [], [], 0
    for w, ww in zip(words, widths):
        add = ww / SS + (space if cur else 0)
        if curw + add > W - 90 and cur:
            lines.append((cur, curw))
            cur, curw = [w], ww / SS
        else:
            cur.append(w)
            curw += add
    if cur:
        lines.append((cur, curw))

    lh = 54
    total_h = len(lines) * lh + 34
    top = y - total_h / 2
    d.rounded_rectangle(P((28, top), (W - 28, top + total_h)), radius=X(18),
                        fill=(6, 12, 22, 216), outline=(40, 70, 92), width=X(2))
    hl = {w.lower().strip(".,!?—") for w in hl_words}
    yy = top + 17
    for line, lw in lines:
        x = (W - lw) / 2
        for w in line:
            ww = d.textbbox((0, 0), w, font=f)[2] / SS
            key = w.lower().strip(".,!?—")
            if key in hl:
                d.rounded_rectangle(P((x - 8, yy - 5), (x + ww + 8, yy + 44)),
                                    radius=X(9), outline=CYAN, width=X(3))
                d.text(XY(x, yy), w, font=f, fill=WHITE)
                x += ww + space
            else:
                d.text(XY(x, yy), w, font=f, fill=(216, 228, 240))
                x += ww + space
        yy += lh


def progress(d, t, total, y=1262):
    d.line(P((24, y), (W - 24, y)), fill=(40, 54, 70), width=X(3))
    k = max(0.0, min(1.0, t / max(0.1, total)))
    d.line(P((24, y), (24 + (W - 48) * k, y)), fill=(255, 206, 84), width=X(3))
    px = 24 + (W - 48) * k
    d.polygon(P((px - 7, y - 9), (px + 7, y - 9), (px, y + 4)), fill=(255, 238, 170))


def speed_lines(d, t, y, n=9, color=(60, 150, 190)):
    for i in range(n):
        off = (t * 420 + i * 90) % 900
        x = -120 + off
        ln = 60 + (i % 3) * 40
        d.line(P((x, y + (i % 5) * 14), (x + ln, y + (i % 5) * 14)), fill=color, width=X(3))


def scene_hook(t, ctx):
    img = bg(t).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    headline(d, "130 КМ/Ч", "ЗАПАС −40%", "почему электромобиль теряет ход")
    speed_lines(d, t, 700)
    paste_car(img, 360, 830, 620, math.sin(t * 3) * 2)
    d = ImageDraw.Draw(img, "RGBA")
    badge(d)
    return img


def scene_drag(t, ctx):
    img = bg(t).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    headline(d, "СОПРОТИВЛЕНИЕ", "КАК V²", "сила растёт квадратично")
    # две стрелки скорости
    for i, (label, k) in enumerate((("×2", 1.0), ("×4", 2.0))):
        y = 560 + i * 150
        d.text(XY(60, y - 40), label, font=F(34), fill=CYAN if i else GREY)
        ln = 200 * k
        d.line(P((150, y), (150 + ln, y)), fill=CYAN if i else GREY, width=X(8))
        d.polygon(P((150 + ln, y - 14), (150 + ln + 26, y), (150 + ln, y + 14)),
                  fill=CYAN if i else GREY)
    # формула-плашка
    d.rounded_rectangle(P((60, 880), (660, 1010)), radius=X(16), fill=(8, 20, 34, 230),
                        outline=CYAN_DIM, width=X(3))
    d.text(XY(96, 910), "F ~ v²", font=F(64), fill=WHITE)
    d.text(XY(96, 976), "скорость вдвое → тяга вчетверо", font=F(22), fill=GREY)
    badge(d)
    return img


def scene_power(t, ctx):
    img = bg(t).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    headline(d, "МОЩНОСТЬ", "КАК V³", "энергия уходит на воздух")
    # график: кривая куба
    ox, oy = 110, 980
    ex, ey = 620, 560
    d.line(P((ox, oy), (ex, oy)), fill=(90, 120, 140), width=X(3))
    d.line(P((ox, oy), (ox, ey)), fill=(90, 120, 140), width=X(3))
    pts = []
    for i in range(41):
        k = i / 40
        pts.append((ox + (ex - ox) * k, oy - (oy - ey) * (k ** 3)))
    d.line([XY(a, b) for a, b in pts], fill=CYAN, width=X(6), joint="curve")
    # движущаяся точка
    k = 0.35 + 0.6 * (0.5 + 0.5 * math.sin(t * 0.9))
    px, py = ox + (ex - ox) * k, oy - (oy - ey) * (k ** 3)
    d.ellipse(P((px - 10, py - 10), (px + 10, py + 10)), fill=WHITE, outline=CYAN, width=X(3))
    d.text(XY(px - 30, py - 54), "×8", font=F(28), fill=YELLOW)
    d.text(XY(450, 1000), "скорость →", font=F(20), fill=GREY)
    badge(d)
    return img


def battery(d, x, y, w, h, fill_k, label, value, color=CYAN):
    d.rounded_rectangle(P((x, y), (x + w, y + h)), radius=X(14), outline=(120, 150, 170), width=X(4))
    d.rounded_rectangle(P((x + 4, y + h - (h - 10) * fill_k), (x + w - 4, y + h - 6)),
                        radius=X(10), fill=color)
    d.text(XY(x, y + h + 14), label, font=F(30), fill=WHITE)
    d.text(XY(x, y - 52), value, font=F(34), fill=color)


def scene_compare(t, ctx):
    img = bg(t).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    headline(d, "ЗАПАС ХОДА", "−40%", "кВт·ч на 100 км")
    battery(d, 96, 560, 150, 400, 0.62, "90 КМ/Ч", "15", (90, 220, 200))
    battery(d, 474, 560, 150, 400, 0.98, "130 КМ/Ч", "25", RED)
    d.line(P((330, 540), (330, 1010)), fill=(50, 70, 90), width=X(3))
    badge(d)
    return img


def scene_final(t, ctx):
    img = bg(t).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    headline(d, "ВИНОВАТ", "ВОЗДУХ", "чем быстрее — тем дороже километр")
    rows = [("×4", "тяга при ×2 скорости"), ("×8", "мощность при ×2 скорости"), ("−40%", "запас хода на трассе")]
    for i, (big, small) in enumerate(rows):
        y = 520 + i * 150
        d.text(XY(90, y), big, font=F(54), fill=CYAN if i < 2 else RED)
        d.text(XY(260, y + 12), small, font=F(24), fill=GREY)
    badge(d)
    return img


SCENES = {
    "hook": scene_hook,
    "drag": scene_drag,
    "power": scene_power,
    "compare": scene_compare,
    "final": scene_final,
}


def render(name, t, ctx):
    img = SCENES[name](t, ctx).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    caption(d, ctx.get("caption_text", ""), ctx.get("caption_hl", ()), 1148)
    progress(d, t, ctx.get("total", 70.0))
    return img.convert("RGB")
