"""10. Тунгусский взрыв 1908. Аэрофото тайги, радиальный повал, без кратера."""
import math
import random

import skia

from vgen.reels import base as B
from vgen.kit import W, H, lin

FOREST = "#16301f"
FOREST_L = "#27492e"
ASH = "#c9b79a"
FIRE = "#ffb347"
CREAM = "#fff3e0"
INK = "#0a140d"


def _taiga(cv, t, alpha=1.0):
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#0f2418"), (0.5, FOREST), (1, "#0b1a12")]))
    rnd = random.Random(3)
    for i in range(220):
        x = rnd.randint(0, W)
        y = rnd.randint(0, H)
        r = rnd.randint(3, 9)
        cv.circle(x, y, r, fill=FOREST_L, alpha=0.55 * alpha)


def _fallen(cv, cx, cy, t, spread=520, n=70, alpha=1.0, direction=0.6):
    """Деревья лежат радиально от центра."""
    rnd = random.Random(9)
    for i in range(n):
        ang = rnd.uniform(0, math.pi * 2)
        r0 = 30 + rnd.random() * spread
        x = cx + math.cos(ang) * r0
        y = cy + math.sin(ang) * r0 * 0.75
        L = 26 + rnd.random() * 40
        cv.line(x, y, x + math.cos(ang) * L, y + math.sin(ang) * L * 0.75, "#2e4a32", 3,
                alpha=alpha)


def _blast(cv, cx, cy, k):
    if k <= 0:
        return
    r = 80 + 420 * B.ease(k)
    cv.circle(cx, cy, r, fill=FIRE, alpha=0.16 * (1 - k), blur=70)
    cv.circle(cx, cy, r * 0.55, fill=CREAM, alpha=0.5 * (1 - k), blur=40)
    for i in range(18):
        ang = i * 0.35
        d = r * (0.7 + 0.4 * math.sin(i))
        cv.circle(cx + math.cos(ang) * d, cy + math.sin(ang) * d * 0.7, 5, fill=FIRE,
                  alpha=0.5 * (1 - k))


def scene_hook(cv, t, ctx):
    k = B.kof(ctx, t, (0, 8))
    _taiga(cv, t)
    _fallen(cv, 540, 1100, t, 380, 40, 0.8)
    if k > 0.04:
        a = B.ease((k - 0.04) / 0.2)
        B.text(cv, "ПОДКАМЕННАЯ ТУНГУСКА · 30 ИЮНЯ 1908", 200, 26, ASH, a)
        B.big_number(cv, "БЕЗ КРАТЕРА", 320, 86, CREAM, (FIRE, 14), a, INK, 8)
        B.text(cv, "ВЗРЫВ СНЁС ТАЙГУ", 390, 34, "#ffd08a", a)
    B.grain(cv, 7, 4, 0.22)


def scene_blast(cv, t, ctx):
    k = B.kof(ctx, t, (8, 16))
    _taiga(cv, t)
    _fallen(cv, 540, 900, t, 300 + 280 * k, 60, 0.7)
    _blast(cv, 540, 700, min(1.0, k / 0.6))
    if k > 0.1:
        a = B.ease((k - 0.1) / 0.25)
        B.text(cv, "НЕБЕСНОЕ ТЕЛО ВЗОРВАЛОСЬ В ВОЗДУХЕ", 200, 26, CREAM, a)
    B.grain(cv, 8, 11, 0.26)


def scene_after(cv, t, ctx):
    k = B.kof(ctx, t, (16, 24))
    _taiga(cv, t)
    _fallen(cv, 540, 980, t, 560, 130, 1.0)
    if k > 0.05:
        a = B.ease((k - 0.05) / 0.25)
        B.ellipse(cv, 540, 980, 520, 380, stroke="#e6dcc4", width=3, alpha=0.35 * a)
        B.text(cv, "МИЛЛИОНЫ СТВОЛОВ В ОДНОМ НАПРАВЛЕНИИ", 240, 28, CREAM, a)
    B.grain(cv, 7, 18, 0.22)


def scene_final(cv, t, ctx):
    k = B.kof(ctx, t, (24, 31))
    _taiga(cv, t, 0.7)
    _fallen(cv, 540, 1050, t, 500, 90, 0.7)
    if k > 0.05:
        a = B.ease((k - 0.05) / 0.25)
        B.ellipse(cv, 540, 1050, 300, 220, fill="#0a140d", alpha=0.7 * a)
        B.text(cv, "КРАТЕРА ТАК И НЕ НАШЛИ", 500, 40, "#ffd08a", a)
    if k > 0.45:
        a = B.ease((k - 0.45) / 0.3)
        B.text(cv, "ТУНГУССКИЙ ФЕНОМЕН", 1320, 48, CREAM, a)
        B.text(cv, "ТАЙНА БЕЗ УДАРНОЙ ВОРОНКИ", 1380, 26, ASH, a)
    B.grain(cv, 7, 26, 0.22)


SCENES = {"hook": scene_hook, "blast": scene_blast, "after": scene_after, "final": scene_final}


def render(name, t, ctx=None, finish=False):
    return B.render(name, t, ctx, SCENES)
