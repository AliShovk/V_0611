"""Рендер «как небоскрёбы не падают от ветра» в стиле night-vector.

Формат референса: тёмное звёздное небо, плоский вектор, медленный дрейф камеры,
крупные субтитры с подсветкой ключевых слов, HUD с числами и жёлтый прогресс-бар.
"""
import math
import random
from PIL import Image, ImageDraw

W, H, SS = 720, 1280, 2
HORIZON = 1010

SKY_TOP = (7, 11, 26)
SKY_BOT = (22, 32, 58)
LIME = (198, 240, 92)
WHITE = (238, 244, 255)
DIM = (150, 170, 200)

TOWER_X = 360
GROUND = HORIZON + 60


def X(v):
    return int(round(v * SS))


def P(*pts):
    return [(X(a), X(b)) for a, b in pts]


def XY(a, b):
    return (X(a), X(b))


def F(size):
    from vgen.palette import font
    return font(size)


def lerp3(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


STARS = [(random.Random(7).uniform(0, W), random.Random(11 + i).uniform(0, 760),
          random.Random(23 + i).uniform(0.6, 1.9)) for i in range(90)]


def sky(d, t, drift=0.0):
    for yy in range(0, H):
        k = yy / H
        d.line(P((0, yy), (W, yy)), fill=lerp3(SKY_TOP, SKY_BOT, min(1.0, k * 1.5)))
    for (sx, sy, r) in STARS:
        x = (sx + drift * 6) % W
        a = int(120 + 90 * math.sin(t * 1.4 + sx))
        d.ellipse(P((x - r, sy - r), (x + r, sy + r)), fill=(220, 232, 255, max(40, a)))
    # дымка у горизонта
    for i in range(5):
        yy = HORIZON - 120 + i * 26
        d.rectangle(P((0, yy), (W, yy + 26)), fill=(90, 120, 170, 10))


def city(d, t):
    rnd = random.Random(3)
    x = -20
    while x < W + 20:
        w = rnd.randint(34, 74)
        h = rnd.randint(70, 210)
        d.rectangle(P((x, HORIZON - h), (x + w, HORIZON + 40)), fill=(14, 20, 38))
        for wy in range(int(HORIZON - h + 12), HORIZON - 6, 16):
            for wx in range(x + 8, x + w - 8, 14):
                if rnd.random() < 0.45:
                    d.rectangle(P((wx, wy), (wx + 5, wy + 7)), fill=(255, 214, 120, 90))
        x += w + rnd.randint(4, 12)
    d.rectangle(P((0, HORIZON + 40), (W, H)), fill=(8, 12, 22))


def tower_bent(d, cx, base_y, height, width, bend, color=(34, 44, 70), edge=(90, 110, 150),
               floors=40, sign=1):
    """Башня с изгибом: смещение растёт кверху квадратично."""
    top = base_y - height
    left_pts = []
    right_pts = []
    for i in range(floors + 1):
        k = i / floors
        y = base_y - height * k
        off = bend * (k ** 2.4) * sign
        w = width * (1 - 0.22 * k)
        left_pts.append((cx - w / 2 + off, y))
        right_pts.append((cx + w / 2 + off, y))
    poly = left_pts + right_pts[::-1]
    d.polygon(P(*poly), fill=color, outline=edge)
    # окна
    for i in range(0, floors, 2):
        k = i / floors
        y = base_y - height * k
        off = bend * (k ** 2.4) * sign
        w = width * (1 - 0.22 * k)
        d.line(P((cx - w / 2 + off + 6, y), (cx + w / 2 + off - 6, y)),
               fill=(120, 160, 220, 26), width=2)
    return top, left_pts, right_pts


def wind(d, t, intensity=1.0, y0=300, y1=900):
    for i in range(9):
        ph = (t * 0.55 + i * 0.11) % 1.0
        x = -140 + ph * (W + 280)
        y = y0 + (i * 71) % (y1 - y0)
        ln = 60 + 40 * math.sin(i * 1.7)
        d.line(P((x, y), (x + ln, y - 6)), fill=(190, 220, 255, int(70 * intensity)), width=2)


def vortex(d, t, cx, side):
    """Вихрь, срывающийся с угла башни."""
    for k in range(7):
        ang = t * 2.2 + k * 0.9
        r = 16 + k * 8
        ox = cx + side * (30 + r * 0.7)
        oy = 380 + k * 22 + 8 * math.sin(ang)
        d.arc(P((ox - r, oy - r * 0.6), (ox + r, oy + r * 0.6)),
              math.degrees(ang) % 360, (math.degrees(ang) + 220) % 360,
              fill=(150, 210, 255, 150), width=2)


def hud(d, text, sub="", x=None, y=42):
    if x is None:
        x = W - 24
    bb = d.textbbox((0, 0), text, font=F(40))
    w = bb[2] - bb[0]
    d.text(XY(x - w, y), text, font=F(40), fill=WHITE)
    if sub:
        bb2 = d.textbbox((0, 0), sub, font=F(18))
        d.text(XY(x - (bb2[2] - bb2[0]), y + 44), sub, font=F(18), fill=DIM)


def progress(d, t, total):
    y = H - 14
    d.line(P((0, y), (W, y)), fill=(70, 90, 120, 120), width=X(3))
    k = max(0.0, min(1.0, t / max(0.1, total)))
    d.line(P((0, y), (W * k, y)), fill=(255, 214, 90, 230), width=X(3))
    tx = W * k
    d.polygon(P((tx - 6, y - 12), (tx + 6, y - 12), (tx, y - 2)), fill=(255, 244, 200))


def caption(d, text, hl=(), y=1090):
    """Крупный субтитр с подсветкой ключевых слов, до двух строк."""
    if not text:
        return
    words = text.split()
    hl_norm = {w.lower().strip(".,!?—:;«»()") for w in hl}
    f = F(34)
    max_w = X(W) - X(56)
    lines, cur = [], []
    for w in words:
        trial = " ".join(cur + [w])
        bb = d.textbbox((0, 0), trial, font=f, stroke_width=X(4))
        if bb[2] - bb[0] > max_w and cur:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)
    lines = lines[-2:]
    line_h = X(46)
    y0 = X(y) - (len(lines) - 1) * line_h
    # подложка
    top = y0 - X(18)
    bot = y0 + line_h * len(lines) + X(2)
    d.rounded_rectangle([X(24), top, X(W) - X(24), bot], radius=X(14), fill=(4, 8, 16, 135))
    for li, line in enumerate(lines):
        total_w = d.textbbox((0, 0), " ".join(line), font=f, stroke_width=X(4))
        x = (X(W) - (total_w[2] - total_w[0])) / 2 - total_w[0]
        yy = y0 + li * line_h
        for w in line:
            color = LIME if w.lower().strip(".,!?—:;«»()") in hl_norm else WHITE
            d.text((x, yy), w, font=f, fill=color, stroke_width=X(4), stroke_fill=(6, 10, 20, 220))
            bb = d.textbbox((0, 0), w + " ", font=f, stroke_width=X(4))
            x += bb[2] - bb[0]


def scene_hook(d, t, ctx):
    sky(d, t)
    city(d, t)
    top, _, _ = tower_bent(d, TOWER_X, GROUND, 760, 86, 0, color=(30, 40, 64))
    wind(d, t, 0.6)
    # шпиль
    d.line(P((TOWER_X, top), (TOWER_X, top - 90)), fill=(190, 205, 230), width=X(4))
    hud(d, "828 м", "высота")
    caption(d, ctx.get("caption_text", ""), ctx.get("caption_hl", ()), 1080)


def scene_wind(d, t, ctx):
    sky(d, t, drift=3)
    city(d, t)
    sway = 26 * math.sin(t * 1.5)
    top, _, _ = tower_bent(d, TOWER_X + 40, GROUND, 800, 90, sway, color=(32, 42, 68))
    wind(d, t, 1.0, 240, 940)
    vortex(d, t, TOWER_X + 40, -1)
    vortex(d, t, TOWER_X + 40, 1)
    hud(d, f"{abs(sway)/12:.1f} м", "отклонение")
    caption(d, ctx.get("caption_text", ""), ctx.get("caption_hl", ()), 1080)


def scene_damper(d, t, ctx):
    sky(d, t)
    # разрез верхушки башни
    cx = TOWER_X
    d.polygon(P((cx - 150, 250), (cx + 150, 250), (cx + 120, 980), (cx - 120, 980)),
              fill=(16, 22, 38), outline=(90, 110, 150))
    sway_ang = 0.06 * math.sin(t * 1.4)
    d.line(P((cx, 980), (cx + 150 * math.sin(sway_ang), 250)), fill=(60, 76, 108, 120), width=2)
    # тросы и шар
    ax, ay = cx, 300
    ball_ang = -sway_ang * 2.2 - 0.09 * math.sin(t * 1.9)
    bx = ax + math.sin(ball_ang) * 380
    by = ay + math.cos(ball_ang) * 380
    for s in (-1, 1):
        d.line(P((ax + s * 26, ay), (bx + s * 4, by - 30)), fill=(200, 214, 236), width=2)
    d.ellipse(P((bx - 62, by - 62), (bx + 62, by + 62)), fill=(210, 216, 226),
              outline=(150, 160, 176), width=3)
    d.ellipse(P((bx - 40, by - 46), (bx - 10, by - 16)), fill=(244, 248, 252, 90))
    d.text(XY(bx - 58, by + 76), "660 тонн", font=F(24), fill=LIME)
    hud(d, "660 т", "маятник")
    caption(d, ctx.get("caption_text", ""), ctx.get("caption_hl", ()), 1100)


def scene_shape(d, t, ctx):
    sky(d, t, drift=2)
    wind(d, t, 0.8)
    base = 1020
    # три силуэта: коробка, сужение, закрутка
    d.rectangle(P((120, base - 520), (230, base)), fill=(26, 34, 54), outline=(80, 96, 128))
    d.text(XY(112, base + 12), "коробка", font=F(20), fill=DIM)

    d.polygon(P((320, base), (332, base - 540), (420, base - 540), (436, base)),
              fill=(28, 38, 62), outline=(90, 110, 150))
    d.text(XY(322, base + 12), "сужение", font=F(20), fill=DIM)

    for i in range(14):
        k = i / 13
        y0 = base - 540 * k
        y1 = base - 540 * (k + 1 / 13)
        off = 26 * math.sin(k * 2.6) + (k * 22)
        d.polygon(P((500 + off, y0), (590 + off * 1.4, y0), (600 + off * 1.5, y1), (510 + off, y1)),
                  fill=lerp3((34, 44, 72), (46, 60, 92), k), outline=None)
    d.text(XY(506, base + 12), "закрутка 120°", font=F(20), fill=LIME)
    hud(d, "120°", "закрутка")
    caption(d, ctx.get("caption_text", ""), ctx.get("caption_hl", ()), 1100)


def scene_numbers(d, t, ctx):
    sky(d, t)
    city(d, t)
    tower_bent(d, TOWER_X, GROUND, 720, 70, 10 * math.sin(t), color=(28, 36, 58))
    # три плашки
    items = [("660 т", "вес маятника"), ("120°", "закрутка башни"), ("24 %", "минус ветровая нагрузка")]
    y = 300
    for i, (big, small) in enumerate(items):
        a = 255 if t > ctx.get("scene_t0", 0) + i * 0.45 else 90
        d.rounded_rectangle(P((44, y), (W - 44, y + 96)), radius=X(14),
                            fill=(12, 18, 32, 220), outline=(120, 160, 210, 60), width=2)
        d.text(XY(64, y + 16), big, font=F(44), fill=LIME if i == 0 else WHITE)
        d.text(XY(230, y + 34), small, font=F(22), fill=DIM)
        y += 116
    hud(d, "24 %", "меньше нагрузки")
    caption(d, ctx.get("caption_text", ""), ctx.get("caption_hl", ()), 1100)


def scene_final(d, t, ctx):
    sky(d, t)
    city(d, t)
    top, _, _ = tower_bent(d, TOWER_X, GROUND, 780, 80, 18 * math.sin(t * 1.2), color=(30, 40, 66))
    wind(d, t, 0.5)
    caption(d, ctx.get("caption_text", ""), ctx.get("caption_hl", ()), 1080)


SCENES = {
    "hook": scene_hook,
    "wind": scene_wind,
    "damper": scene_damper,
    "shape": scene_shape,
    "numbers": scene_numbers,
    "final": scene_final,
}


def render(name, t, ctx):
    img = Image.new("RGB", (X(W), X(H)), SKY_TOP)
    d = ImageDraw.Draw(img, "RGBA")
    SCENES[name](d, t, ctx)
    progress(d, t, ctx.get("total", 60.0))
    return img
