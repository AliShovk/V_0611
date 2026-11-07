"""Бурдж-Халифа v2: ветер, ступенчатая форма, Y-ядро. Рисунок на vgen.kit (Skia).

Интерфейс как у остальных рендереров: render(name, t, ctx) -> PIL.Image 1080x1920.
"""
import math
import random

import skia

from vgen import postfx
from vgen.kit import Canvas, W, H, lin, rad

INK = "#060c18"
CREAM = "#fff3d6"
GOLD = "#ffc45e"
CYAN = "#8fe6ff"
STEEL = "#9fb4cc"
DEEP = "#0b1a2e"

HORIZON = 1560
BASE_X = 540


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


# ---------- фон ----------

def sky(cv, t, dusk=True):
    top = "#040814" if dusk else "#071022"
    mid = "#122murky" if False else "#122a4d"
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, HORIZON + 60, [
        (0.00, top), (0.42, mid), (0.70, "#3b5a86"), (0.88, "#b87a68"), (1.00, "#f2b07a")]))
    # свечение у горизонта
    cv.rect(0, 900, W, H, fill=rad(540, HORIZON, 900, [
        (0.0, "#ffbe7ae0"), (0.4, "#ff8f5c40"), (1.0, "#ff7a5000")]))
    rnd = random.Random(7)
    for _ in range(120):
        x, y = rnd.uniform(0, W), rnd.uniform(0, 820)
        a = rnd.uniform(0.2, 0.85) * (0.65 + 0.35 * math.sin(t * 1.1 + x * 0.05))
        cv.circle(x, y, rnd.uniform(0.7, 1.6), fill="#e6f0ff", alpha=max(0.0, a * (1 - y / 950)))


def city(cv, base, seed, col, hmin, hmax, win="#ffd27a", t=0.0):
    rnd = random.Random(seed)
    dim, bright = skia.Path(), skia.Path()
    x = -30
    while x < W + 30:
        w = rnd.randint(46, 118)
        h = rnd.randint(hmin, hmax)
        cv.rect(x, base - h, x + w, base + 200, fill=col)
        if win:
            for wy in range(int(base - h + 12), int(base) - 8, 18):
                for wx in range(int(x + 8), int(x + w - 8), 16):
                    if rnd.random() < 0.35:
                        r = skia.Rect(wx, wy, wx + 5, wy + 8)
                        (bright if rnd.random() < 0.4 else dim).addRect(r)
        x += w + rnd.randint(6, 22)
    cv.path(dim, fill=win, alpha=0.32)
    cv.path(bright, fill=win, alpha=0.72)


def haze(cv, y, height=180, alpha=0.28, col="#ffcf9e"):
    cv.rect(0, y - height, W, y, fill=lin(0, y - height, 0, y, [
        (0.0, col + "00"), (1.0, col + format(int(alpha * 255), "02x"))]))


def wind_streaks(cv, t, y0=300, y1=1400, n=26, alpha=0.5):
    rnd = random.Random(13)
    for i in range(n):
        y = rnd.uniform(y0, y1)
        sp = rnd.uniform(420, 900)
        x = (W + 200 - (t * sp + rnd.uniform(0, 900)) % (W + 500))
        ln = rnd.uniform(80, 260)
        a = alpha * (0.35 + 0.65 * rnd.random())
        cv.line(x, y, x + ln, y - rnd.uniform(4, 18), "#cfe9ff", width=rnd.uniform(1.2, 2.6), alpha=a)


# ---------- башня ----------

def burj(cv, cx, base, height, t, sway=1.0, detail=True, lit=True):
    """Ступенчатая спираль: ярусы сужаются и поворачиваются; верх качается."""
    tiers = 26
    win_lit, win_dim = skia.Path(), skia.Path()
    phase = math.sin(t * 1.35)
    for i in range(tiers):
        k = i / tiers
        y1 = base - height * k
        y0 = base - height * (k + 1 / tiers)
        w = (0.145 * (1 - k) ** 0.62 + 0.016) * height
        shift = sway * 42 * (k ** 2.1) * phase
        twist = math.sin(k * math.pi * 3.2 + t * 0.2) * w * 0.06
        col_mix = 0.35 + 0.65 * k
        fill = lin(cx - w / 2 + shift, 0, cx + w / 2 + shift, 0, [
            (0.0, "#0d2136"), (0.35, "#1c4d70"), (0.62, "#276c93"), (1.0, "#0a1a2b")])
        cv.poly([(cx - w / 2 + shift + twist, y0), (cx + w / 2 + shift + twist, y0),
                 (cx + w / 2 + shift, y1), (cx - w / 2 + shift, y1)], fill=fill)
        # световая кромка слева
        cv.line(cx - w / 2 + shift + twist, y0, cx - w / 2 + shift, y1,
                "#bfe6ff", width=max(0.8, 2.2 * (1 - k)), alpha=0.55)
        if detail and w > 12:
            rnd = random.Random(i * 31 + 5)
            cols = max(2, int(w / 11))
            for c in range(cols):
                wx = cx - w / 2 + shift + (c + 0.5) * w / cols
                for wy in range(int(y0) + 4, int(y1) - 3, 9):
                    if rnd.random() < 0.5:
                        r = skia.Rect(wx - 1.6, wy, wx + 1.6, wy + 3.4)
                        (win_lit if rnd.random() < 0.45 else win_dim).addRect(r)
    if not win_dim.isEmpty():
        cv.path(win_dim, fill="#ffe3a8", alpha=0.28)
    if not win_lit.isEmpty():
        cv.path(win_lit, fill="#fff0c4", alpha=0.62)
    # шпиль
    top_y = base - height
    cv.poly([(cx - 6, top_y + 30), (cx + 6, top_y + 30), (cx + 1.2, top_y - 62), (cx - 1.2, top_y - 62)],
            fill=lin(cx - 6, 0, cx + 6, 0, [(0.0, "#22475f"), (0.5, "#9fd0e6"), (1.0, "#16303f")]))
    cv.circle(cx, top_y - 64, 8, fill="#ff6a5a", alpha=0.25, blur=6)
    cv.circle(cx, top_y - 64, 3.2, fill="#ff6a5a")


def dimension(cv, x, y1, y2, label, col="#fff3d6"):
    cv.line(x, y1, x, y2, col, width=2.4, alpha=0.9)
    for yy in (y1, y2):
        cv.line(x - 14, yy, x + 14, yy, col, width=2.4, alpha=0.9)
    cv.text(label, x + 22, (y1 + y2) / 2 + 8, 34, fill=col, shadow=(0, 3, 8, "#000a"))


def headline(cv, lines, y=150, size=78):
    for i, (s, col) in enumerate(lines):
        cv.text(s, W / 2, y + i * (size + 14), size, fill=col, center=True,
                stroke="#04070e", stroke_w=8, shadow=(0, 8, 16, "#000c"))


def badge(cv, tag="ВЕТЕР"):
    cv.rrect(56, 56, 236, 118, 12, fill="#0a1626cc", stroke="#8fe6ff66", width=2)
    cv.text("VGEN", 76, 96, 30, fill="#ffffff")
    cv.rrect(56, 130, 300, 186, 12, fill="#08131fdd", stroke="#8fe6ff55", width=2)
    cv.text(tag, 74, 166, 26, fill=CYAN)


# ---------- сцены ----------


_BG = {}


def _bg_image(seed, hmin, hmax):
    """Небо + город рисуются один раз и переиспользуются как картинка."""
    key = (seed, hmin, hmax)
    if key in _BG:
        return _BG[key]
    c2 = Canvas()
    sky(c2, 0.0)
    city(c2, HORIZON, seed, "#0a1526", hmin, hmax)
    _BG[key] = c2.surface.makeImageSnapshot()
    return _BG[key]


def scene_hook(cv, t):
    cv.clear(INK)
    cv.c.drawImage(_bg_image(5, 60, 260), 0, 0)
    wind_streaks(cv, t, 220, 1500, 22, 0.35)
    burj(cv, BASE_X, HORIZON, 1120, t, sway=1.15)
    haze(cv, HORIZON, 220, 0.30)
    dimension(cv, 830, HORIZON - 1120, HORIZON, "828 м")
    headline(cv, [("828 МЕТРОВ", "#ffffff"), ("163 ЭТАЖА", GOLD)], 150, 74)
    cv.text("и башня качается", W / 2, 372, 40, fill=CYAN, center=True,
            stroke="#04070e", stroke_w=5)
    badge(cv, "ВЕТЕР")


def scene_shape(cv, t):
    cv.clear(INK)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#08111f"), (1, "#0d1c33")]))
    # три силуэта: труба / сужение / ступени
    x0, base, h = 170, 1320, 760
    for i, (label, kind) in enumerate([("ТРУБА", "tube"), ("СУЖЕНИЕ", "taper"), ("СПИРАЛЬ", "step")]):
        cx = x0 + i * 330
        if kind == "tube":
            cv.rect(cx - 70, base - h, cx + 70, base, fill="#1d3a4a")
            cv.rect(cx - 70, base - h, cx - 62, base, fill="#3f7ba0", alpha=0.6)
        elif kind == "taper":
            cv.poly([(cx - 88, base), (cx + 88, base), (cx + 30, base - h), (cx - 30, base - h)],
                    fill="#20486a")
            cv.line(cx - 88, base, cx - 30, base - h, "#63a8cc", width=3, alpha=0.6)
        else:
            for k in range(14):
                kk = k / 14
                w = 90 * (1 - kk) + 14
                cv.rect(cx - w, base - h * kk - h / 14, cx + w, base - h * kk - h / 14 + 6,
                        fill="#245a80" if k % 2 else "#1a405e")
            cv.poly([(cx - 5, base - h + 6), (cx + 5, base - h + 6), (cx + 1, base - h - 40),
                     (cx - 1, base - h - 40)], fill="#9fd0e6")
        cv.text(label, cx, base + 52, 30, fill="#e6f4ff" if kind == "step" else "#b6c9da", center=True)
        # вихри с подветренной стороны
        for j in range(4):
            yy = base - h * (0.25 + 0.18 * j)
            ph = (t * 1.4 + j * 0.4) % 1.0
            r = 16 + 10 * math.sin(ph * math.pi)
            cv.circle(cx + (60 if kind == "tube" else 84), yy, r, stroke="#8fe6ff", width=2,
                      alpha=0.65 if kind == "tube" else 0.3)
    headline(cv, [("ФОРМА ГАСИТ", GOLD), ("ВИХРИ", "#ffffff")], 140, 76)
    cv.text("ступени сбивают фазу срыва", W / 2, 360, 34, fill=CYAN, center=True, stroke="#04070e", stroke_w=4)
    badge(cv, "ФОРМА")


def scene_vortex(cv, t):
    cv.clear(INK)
    cv.rect(0, 0, W, H, fill=rad(540, 900, 900, [(0, "#123055"), (1, "#050b16")]))
    # вид сверху: план башни и вихри по очереди
    cx, cy = 540, 980
    cv.circle(cx, cy, 230, fill="#0d2237", stroke="#4a89ad", width=4, alpha=0.9)
    # Y-план
    for k in range(3):
        ang = math.radians(90 + k * 120)
        cv.line(cx, cy, cx + 185 * math.cos(ang), cy + 185 * math.sin(ang), "#5aa8cc", width=30, alpha=0.85)
    cv.circle(cx, cy, 46, fill="#1d4d6b")
    # вихри: чередуются с двух сторон
    for i in range(8):
        side = 1 if i % 2 == 0 else -1
        y = cy - 150 + i * 42
        ph = (t * 1.1 + i * 0.22) % 1.0
        r = 22 + 16 * math.sin(ph * math.pi)
        a = 0.25 + 0.55 * math.sin(ph * math.pi)
        ang0 = math.radians(t * 60 + i * 26)
        rr = 210 + 26 * math.sin(ph * 6)
        cv.circle(cx + math.cos(ang0) * rr, y + math.sin(ang0) * 0 + (cy - y) * 0.0,
                  r, stroke="#8fe6ff", width=3, alpha=a)
    # набегающий поток
    for i in range(9):
        y = 820 + i * 40
        x = 1080 - ((t * 300 + i * 60) % 1200)
        cv.line(x, y, x + 120, y, "#cfe9ff", width=2, alpha=0.28)
    headline(cv, [("ВИХРИ СРЫВАЮТСЯ", "#ffffff"), ("ПО ОЧЕРЕДИ", CYAN)], 140, 62)
    cv.text("с подветренной стороны", W / 2, 330, 32, fill="#9fb4cc", center=True)
    badge(cv, "ВИХРИ")


def scene_core(cv, t):
    cv.clear(INK)
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#060d19"), (1, "#0b1b2e")]))
    # разрез: три крыла и ядро
    cx, cy = 540, 900
    cv.circle(cx, cy, 290, fill="#0a1a2b", stroke="#33607f", width=3)
    for k in range(3):
        ang = math.radians(90 + k * 120 + t * 26)
        cv.line(cx, cy, cx + 250 * math.cos(ang), cy + 250 * math.sin(ang), "#2f6f95", width=58)
        cv.line(cx, cy, cx + 250 * math.cos(ang), cy + 250 * math.sin(ang), "#4b9cc4", width=28, alpha=0.75)
    cv.circle(cx, cy, 72, fill="#0f2a3f", stroke="#8fe6ff", width=3)
    cv.text("ЯДРО", cx, cy + 12, 26, fill=CYAN, center=True)
    # скручивание
    for k in range(3):
        a0 = 20 + k * 120 + t * 22
        pts = [(cx + 190 * math.cos(math.radians(a0 + j * 6)),
                cy + 190 * math.sin(math.radians(a0 + j * 6))) for j in range(11)]
        cv.poly(pts, close=False, stroke="#ffc45e", width=4, alpha=0.75)
    headline(cv, [("Y-ЯДРО", GOLD), ("ДЕРЖИТ СКРУЧИВАНИЕ", "#ffffff")], 140, 62)
    badge(cv, "ЯДРО")
    cv.text("три крыла + центральный ствол", W / 2, 1700, 36, fill="#c2d4e4", center=True)


def scene_final(cv, t):
    cv.clear(INK)
    cv.c.drawImage(_bg_image(9, 50, 220), 0, 0)
    wind_streaks(cv, t, 260, 1400, 14, 0.25)
    burj(cv, BASE_X, HORIZON, 1120, t, sway=1.4)
    haze(cv, HORIZON, 200, 0.26)
    # отклонение верха
    top = HORIZON - 1120
    dx = 26 * 1.4 * math.sin(t * 0.9)
    cv.line(860, top, 860 + dx, top, "#ffc45e", width=3)
    cv.text("1,5 м", 872, top - 22, 38, fill=GOLD, stroke="#04070e", stroke_w=4)
    headline(cv, [("СНАРУЖИ СТОИТ", "#ffffff"), ("ВНУТРИ ДЫШИТ", GOLD)], 150, 62)
    badge(cv, "ИТОГ")


SCENES = {"hook": scene_hook, "shape": scene_shape, "vortex": scene_vortex,
          "core": scene_core, "final": scene_final}


def render(name, t, ctx=None, finish=False):
    cv = Canvas()
    # наезд камеры делается в ffmpeg (kenburns), чтобы не платить за пиксели в Python
    cv.save()
    cv.c.translate(4 * math.sin(t * 0.7), 3 * math.cos(t * 0.5))
    SCENES[name](cv, t)
    cv.restore()
    img = cv.to_pil()
    if finish:
        img = postfx.finish(img, grain_amt=3)
    # по умолчанию без пост-обработки: проект использует ffmpeg-цепочку (post: true)
    return img
