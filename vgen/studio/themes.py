"""Темы-фоны: каждая рисует многослойный задник с параллаксом и мягким движением.

backdrop(cv, theme, t, k): k — прогресс камеры сцены (0..1), даёт сдвиг слоёв.
Каждая тема несёт палитру: accent / accent2 / warm — шоты берут цвета отсюда.
"""
import math
import random

from vgen.kit import W, H, lin, rad

THEMES = {
    "dusk":      dict(accent="#7fe4ff", accent2="#ffc45e", warm="#ff8a5c", ink="#070d1a"),
    "space":     dict(accent="#8fd8ff", accent2="#ffcf6e", warm="#ff9a6a", ink="#04060f"),
    "ocean":     dict(accent="#7ff0ff", accent2="#ffe08a", warm="#ff9a7a", ink="#03121f"),
    "blueprint": dict(accent="#8fe0ff", accent2="#ffd166", warm="#ff8a7a", ink="#06142a"),
    "studio":    dict(accent="#7fe4ff", accent2="#ffc45e", warm="#ff8a5c", ink="#070a12"),
    "neon":      dict(accent="#39f0ff", accent2="#ff4fd8", warm="#ffd34f", ink="#0b0120"),
}


def palette(name):
    return THEMES.get(name, THEMES["studio"])


def _skyline(cv, base, seed, col, hmin, hmax, win=None):
    rnd = random.Random(seed)
    x = -20
    while x < W + 20:
        w, h = rnd.randint(50, 120), rnd.randint(hmin, hmax)
        cv.rect(x, base - h, x + w, base + 400, fill=col)
        if win:
            for yy in range(int(base - h + 14), int(base - 10), 19):
                for xx in range(int(x + 8), int(x + w - 10), 15):
                    if rnd.random() < 0.30:
                        cv.rect(xx, yy, xx + 5, yy + 8, fill=win, alpha=rnd.uniform(0.35, 0.95))
        x += w + rnd.randint(0, 8)


def _stars(cv, t, n, ymax, seed=11, drift=0.0):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, ymax)
        a = rnd.uniform(0.25, 0.95) * (0.7 + 0.3 * math.sin(t * 1.3 + x))
        cv.circle((x + drift) % W, y, rnd.uniform(0.7, 1.9), fill="#dfeaff", alpha=max(0.0, a * (1 - y / (ymax * 1.2))))


def dusk(cv, t, k):
    hz = 1540
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, hz + 80, [
        (0.00, "#050a18"), (0.40, "#0d1c3d"), (0.68, "#2a3f6e"), (0.88, "#a45f6a"), (1.00, "#f0a066")]))
    cv.rect(0, 700, W, H, fill=rad(760, hz + 20, 980, [(0, "#ffb26be0"), (0.35, "#ff8a5c55"), (1, "#ff7a5000")]))
    _stars(cv, t, 110, 760)
    for i, (cx, cy, w, h, a) in enumerate([(220, 880, 560, 54, .20), (820, 1010, 640, 62, .17), (480, 1190, 700, 50, .16)]):
        x = (cx + t * (6 + 3 * i)) % (W + 600) - 300
        cv.oval(x - w / 2, cy - h / 2, x + w / 2, cy + h / 2, fill="#ffb3a0", alpha=a, blur=26)
    _skyline(cv, hz + 10, 3, "#6a4a66", 90, 230)
    cv.rect(0, 1380, W, hz + 80, fill=lin(0, 1380, 0, hz + 80, [(0, "#c9806800"), (1, "#c98068f2")]))
    _skyline(cv, hz + 90 - 20 * k, 8, "#241d3b", 70, 190, win="#ffd98a")
    _skyline(cv, hz + 190 - 40 * k, 21, "#0e1226", 60, 150, win="#ffe9b0")
    cv.rect(0, hz + 150, W, H, fill=lin(0, hz + 150, 0, H, [(0, "#0e1226"), (1, "#05070f")]))


def space(cv, t, k):
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#02030a"), (0.5, "#0a0f2e"), (1, "#1b1042")]))
    for (x, y, r, c) in [(260, 520, 520, "#5b2a9a"), (860, 1100, 600, "#0f6f8f"), (500, 1500, 520, "#7a2a6a")]:
        cv.circle(x + 20 * math.sin(t * .2 + x), y, r, fill=rad(x, y, r, [(0, c + "66"), (1, c + "00")]))
    _stars(cv, t, 260, 1500, drift=t * 3 + 30 * k)
    _stars(cv, t, 70, 1500, seed=5, drift=t * 8 + 80 * k)
    # лимб планеты внизу, атмосферное свечение
    cy, r = 2650 - 60 * k, 1250
    cv.circle(W * 0.62, cy, r + 40, fill=rad(W * 0.62, cy, r + 140, [(0.86, "#6ec8ff88"), (1, "#6ec8ff00")]))
    cv.circle(W * 0.62, cy, r, fill=rad(W * 0.5, cy - r * 0.9, r * 1.5, [(0, "#2d6fb8"), (0.5, "#13335f"), (1, "#050b1c")]))
    cv.circle(W * 0.62, cy, r, stroke="#9fdcff", width=4, alpha=0.55, blur=2)


def ocean(cv, t, k):
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#0d7fb5"), (0.35, "#085385"), (0.7, "#04284a"), (1, "#010912")]))
    for i in range(7):
        x = 120 + i * 150 + 40 * math.sin(t * .35 + i)
        cv.poly([(x, -50), (x + 90, -50), (x + 420 + 60 * math.sin(t * .3 + i * 2), 1500), (x + 160, 1500)],
                fill=lin(0, 0, 0, 1500, [(0, "#bfefff44"), (1, "#bfefff00")]), alpha=0.5, blur=14)
    rnd = random.Random(4)
    for i in range(46):
        x = rnd.uniform(0, W) + 14 * math.sin(t + i)
        y = (rnd.uniform(0, H) - t * rnd.uniform(30, 90) - 120 * k) % H
        cv.circle(x, y, rnd.uniform(2, 7), stroke="#d8f6ff", width=1.5, alpha=rnd.uniform(.2, .6))
    cv.rect(0, 1500, W, H, fill=lin(0, 1500, 0, H, [(0, "#01091200"), (1, "#010912f0")]))


def blueprint(cv, t, k):
    cv.rect(0, 0, W, H, fill=rad(W / 2, 760, 1500, [(0, "#0f3a6e"), (1, "#050f22")]))
    for x in range(0, W + 1, 60):
        cv.line(x, 0, x, H, "#7fc4ff", 1.2 if x % 300 else 2.4, alpha=0.07 if x % 300 else 0.16)
    for y in range(int(-(k * 60) % 60), H + 1, 60):
        cv.line(0, y, W, y, "#7fc4ff", 1.2 if (y // 60) % 5 else 2.4, alpha=0.07 if (y // 60) % 5 else 0.16)
    for r in (260, 430, 640):
        cv.circle(W / 2, 880, r, stroke="#7fc4ff", width=1.6, alpha=0.10)
    for (x, y) in [(40, 40), (W - 40, 40), (40, H - 40), (W - 40, H - 40)]:
        cv.line(x - 26, y, x + 26, y, "#8fe0ff", 2, alpha=0.5)
        cv.line(x, y - 26, x, y + 26, "#8fe0ff", 2, alpha=0.5)


def studio(cv, t, k):
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#0a1020"), (1, "#05070d")]))
    cv.rect(0, 0, W, H, fill=rad(W / 2, 760, 980, [(0, "#2a3f6bcc"), (0.6, "#14203a55"), (1, "#05070d00")]))
    rnd = random.Random(2)
    for i in range(18):
        x, y, r = rnd.uniform(0, W), rnd.uniform(200, 1500), rnd.uniform(18, 70)
        cv.circle(x + 20 * math.sin(t * .4 + i), y, r, fill="#8fb4ff", alpha=0.05 + 0.03 * math.sin(t + i), blur=10)
    cv.oval(W / 2 - 480, 1380 - 40 * k, W / 2 + 480, 1500 - 40 * k, fill=rad(W / 2, 1440, 480, [(0, "#6f9cff55"), (1, "#6f9cff00")]))


def neon(cv, t, k):
    hz = 1050
    cv.rect(0, 0, W, hz, fill=lin(0, 0, 0, hz, [(0, "#0b0120"), (0.7, "#2a0a4a"), (1, "#5a1470")]))
    _stars(cv, t, 80, 800, seed=9)
    cv.circle(W / 2, hz - 40, 330, fill=lin(0, hz - 370, 0, hz + 290, [(0, "#ffe34f"), (0.5, "#ff7a5c"), (1, "#ff2fb4")]))
    for i in range(7):                     # полосы на солнце
        y = hz - 40 + i * 36
        cv.rect(W / 2 - 340, y, W / 2 + 340, y + 4 + i * 3, fill="#2a0a4a")
    cv.rect(0, hz, W, H, fill=lin(0, hz, 0, H, [(0, "#2a0a4a"), (1, "#07010f")]))
    for i in range(-14, 15):               # сетка пола (перспектива)
        cv.line(W / 2 + i * 30, hz, W / 2 + i * 190, H, "#ff4fd8", 2.2, alpha=0.55)
    for j in range(14):
        p = ((j + (t * 0.35) % 1) / 14) ** 2.2
        y = hz + p * (H - hz)
        cv.line(0, y, W, y, "#39f0ff", 1.5 + 3 * p, alpha=0.25 + 0.4 * p)
    cv.rect(0, hz - 6, W, hz + 8, fill="#ff4fd8", alpha=0.7, blur=8)


def plate(cv, path, t, k, dim=0.38):
    """AI/фото-фон: cover с наездом и панорамой + затемнение под текст."""
    cv.image_cover(path, zoom=1.12 + 0.10 * k, pan=(-0.5 + k, 0.1 - 0.2 * k))
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#04081099"), (0.35, "#04081022"), (0.7, "#04081033"), (1, "#040810dd")]))
    cv.rect(0, 0, W, H, fill="#050a14", alpha=dim * 0.5)


DRAW = {"dusk": dusk, "space": space, "ocean": ocean, "blueprint": blueprint, "studio": studio, "neon": neon}


def backdrop(cv, theme, t, k, plate_path=None):
    if plate_path:
        plate(cv, plate_path, t, k)
    else:
        DRAW.get(theme, studio)(cv, t, k)
