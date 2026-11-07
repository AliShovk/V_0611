"""Библиотека иконок-«героев»: объёмные, с градиентом, свечением и своей анимацией.

draw_icon(cv, name, cx, cy, size, t, c1, c2) — size ≈ диаметр в пикселях.
ICONS — список доступных имён (проверяется валидатором).
"""
import math

import skia

from vgen.kit import lin, rad


def _halo(cv, cx, cy, s, col):
    cv.circle(cx, cy, s * 0.78, fill=rad(cx, cy, s * 0.78, [(0, col + "70"), (0.6, col + "22"), (1, col + "00")]))


def _poly(pts, cx, cy, u):
    return [(cx + x * u, cy + y * u) for x, y in pts]


def _path(cx, cy, u, cmds):
    p = skia.Path()
    for c in cmds:
        k, a = c[0], c[1:]
        a = [(cx + v * u) if i % 2 == 0 else (cy + v * u) for i, v in enumerate(a)]
        {"M": p.moveTo, "L": p.lineTo, "Q": p.quadTo, "C": p.cubicTo}[k](*a)
    p.close()
    return p


def gear(cv, cx, cy, u, t, c1, c2):
    n, step, rot = 10, 2 * math.pi / 10, t * 0.5
    pts = []
    for i in range(n):
        a = rot + i * step
        for r, d in ((38, -0.30), (48, -0.17), (48, 0.17), (38, 0.30)):
            pts.append((cx + u * r * math.cos(a + d * step * 1.9), cy + u * r * math.sin(a + d * step * 1.9)))
    cv.poly(pts, fill=lin(cx - 50 * u, cy - 50 * u, cx + 50 * u, cy + 50 * u, [(0, "#f3f7fd"), (0.5, "#9fb0c8"), (1, "#4c5a70")]),
            shadow=(0, 6 * u, 8 * u, "#000a"))
    cv.circle(cx, cy, 27 * u, stroke="#ffffff", width=3 * u, alpha=0.55)
    cv.circle(cx, cy, 17 * u, fill="#0b1220")
    cv.circle(cx, cy, 17 * u, stroke=c1, width=3 * u, alpha=0.9)


def bolt(cv, cx, cy, u, t, c1, c2):
    pts = _poly([(10, -52), (-28, 6), (-3, 6), (-12, 52), (30, -10), (4, -10)], cx, cy, u)
    cv.poly(pts, fill="#ffd34f", blur=14 * u, alpha=0.8)
    cv.poly(pts, fill=lin(cx, cy - 52 * u, cx, cy + 52 * u, [(0, "#fffbd0"), (0.5, "#ffc830"), (1, "#ff7a1a")]),
            shadow=(0, 5 * u, 6 * u, "#0009"))
    cv.poly(pts, stroke="#fff6c0", width=2 * u, alpha=0.7)


def drop(cv, cx, cy, u, t, c1, c2):
    p = _path(cx, cy, u, [("M", 0, -52), ("C", 30, -14, 40, 6, 40, 20), ("C", 40, 42, 22, 54, 0, 54),
                          ("C", -22, 54, -40, 42, -40, 20), ("C", -40, 6, -30, -14, 0, -52)])
    cv.path(p, fill=lin(cx, cy - 52 * u, cx, cy + 54 * u, [(0, "#c8f6ff"), (0.5, "#35b8ee"), (1, "#0b5fa8")]),
            shadow=(0, 6 * u, 8 * u, "#0009"))
    cv.oval(cx - 24 * u, cy + 4 * u, cx - 8 * u, cy + 34 * u, fill="#ffffff", alpha=0.55, blur=2 * u)


def flame(cv, cx, cy, u, t, c1, c2):
    fl = 1 + 0.05 * math.sin(t * 9) + 0.03 * math.sin(t * 15)
    o = _path(cx, cy, u, [("M", 0, -54 * fl), ("C", 16, -30, 40, -14, 36, 18), ("C", 33, 40, 16, 54, 0, 54),
                          ("C", -18, 54, -38, 40, -35, 18), ("C", -34, 2, -22, -6, -16, -22),
                          ("C", -8, -6, -4, -14, 0, -54 * fl)])
    cv.path(o, fill="#ff7a1a", blur=14 * u, alpha=0.7)
    cv.path(o, fill=lin(cx, cy - 54 * u, cx, cy + 54 * u, [(0, "#ffd34f"), (0.5, "#ff7a1a"), (1, "#d6231a")]),
            shadow=(0, 4 * u, 6 * u, "#0008"))
    i = _path(cx, cy + 14 * u, u * 0.62, [("M", 0, -42 * fl), ("C", 14, -20, 30, -6, 28, 18), ("C", 26, 36, 12, 44, 0, 44),
                                           ("C", -14, 44, -28, 36, -27, 18), ("C", -26, 2, -10, -10, 0, -42 * fl)])
    cv.path(i, fill=lin(cx, cy - 20 * u, cx, cy + 50 * u, [(0, "#fffbd0"), (1, "#ffc830")]))


def snow(cv, cx, cy, u, t, c1, c2):
    cv.circle(cx, cy, 44 * u, fill="#bfefff", blur=16 * u, alpha=0.35)
    for i in range(6):
        a = t * 0.2 + i * math.pi / 3
        ex, ey = cx + 48 * u * math.cos(a), cy + 48 * u * math.sin(a)
        cv.line(cx, cy, ex, ey, "#e8fbff", 6 * u)
        for f, ln in ((0.55, 15), (0.8, 10)):
            bx, by = cx + 48 * u * f * math.cos(a), cy + 48 * u * f * math.sin(a)
            for s in (-1, 1):
                cv.line(bx, by, bx + ln * u * math.cos(a + s * 0.75), by + ln * u * math.sin(a + s * 0.75), "#e8fbff", 4.5 * u)
    cv.circle(cx, cy, 6 * u, fill="#ffffff")


def building(cv, cx, cy, u, t, c1, c2):
    for (x0, y0, x1, y1, seed) in [(-44, -8, -14, 52, 1), (-14, -52, 22, 52, 2), (22, -26, 46, 52, 3)]:
        cv.rect(cx + x0 * u, cy + y0 * u, cx + x1 * u, cy + y1 * u,
                fill=lin(cx + x0 * u, 0, cx + x1 * u, 0, [(0, "#6f87b0"), (1, "#2c3a58")]), shadow=(0, 4 * u, 6 * u, "#0008"))
        for r in range(int((y1 - y0) // 11) - 1):
            for c in range(max(1, int((x1 - x0) // 11) - 1)):
                on = (r * 7 + c * 3 + seed + int(t * 0.8)) % 4 != 0
                cv.rect(cx + (x0 + 5 + c * 11) * u, cy + (y0 + 6 + r * 11) * u, cx + (x0 + 10 + c * 11) * u, cy + (y0 + 12 + r * 11) * u,
                        fill="#ffe08a" if on else "#16213a", alpha=0.95)
    cv.rect(cx - 52 * u, cy + 52 * u, cx + 52 * u, cy + 56 * u, fill="#0b1220")


def car(cv, cx, cy, u, t, c1, c2):
    body = _path(cx, cy, u, [("M", -50, 18), ("L", -50, 2), ("Q", -48, -6, -30, -9), ("L", -18, -27), ("Q", -14, -31, -6, -31),
                             ("L", 20, -31), ("Q", 28, -31, 34, -23), ("L", 44, -9), ("Q", 52, -7, 52, 2), ("L", 52, 18)])
    cv.path(body, fill=lin(cx, cy - 31 * u, cx, cy + 18 * u, [(0, "#bff3ff"), (0.45, c1), (1, "#0e5d8a")]), shadow=(0, 6 * u, 8 * u, "#000a"))
    cv.poly(_poly([(-22, -9), (-12, -24), (18, -24), (30, -9)], cx, cy, u), fill="#0b1c2c", alpha=0.9)
    cv.line(cx - 14 * u, cy - 21 * u, cx + 4 * u, cy - 21 * u, "#ffffff", 2.5 * u, alpha=0.5)
    for wx in (-28, 30):
        cv.circle(cx + wx * u, cy + 18 * u, 12 * u, fill="#10151f")
        cv.circle(cx + wx * u, cy + 18 * u, 6 * u, fill="#9fb0c8")
    cv.circle(cx + 50 * u, cy - 1 * u, 5 * u, fill="#fff6c0", blur=3 * u)


def planet(cv, cx, cy, u, t, c1, c2):
    for front in (False, True):
        cv.save()
        cv.rotate(-18, cx, cy)
        if front:
            cv.clip(cx - 90 * u, cy, cx + 90 * u, cy + 90 * u)
        cv.oval(cx - 64 * u, cy - 17 * u, cx + 64 * u, cy + 17 * u, stroke=lin(cx - 64 * u, 0, cx + 64 * u, 0, [(0, "#ffe9b0"), (1, "#c98a3a")]), width=8 * u)
        cv.restore()
        if not front:
            cv.circle(cx, cy, 34 * u, fill=rad(cx - 12 * u, cy - 14 * u, 52 * u, [(0, "#ffe2b0"), (0.5, "#d9803f"), (1, "#4a2418")]),
                      shadow=(0, 5 * u, 8 * u, "#0009"))


def rocket(cv, cx, cy, u, t, c1, c2):
    fl = 1 + 0.18 * math.sin(t * 22)
    cv.poly(_poly([(-12, 24), (12, 24), (0, 24 + 34 * fl)], cx, cy, u), fill="#ff9a1a", blur=4 * u)
    cv.poly(_poly([(-7, 24), (7, 24), (0, 24 + 22 * fl)], cx, cy, u), fill="#fff1a0")
    for s in (-1, 1):
        cv.poly(_poly([(s * 20, 6), (s * 38, 36), (s * 20, 26)], cx, cy, u), fill="#e0453a")
    body = _path(cx, cy, u, [("M", 0, -54), ("C", 24, -32, 26, 0, 21, 28), ("L", -21, 28), ("C", -26, 0, -24, -32, 0, -54)])
    cv.path(body, fill=lin(cx - 24 * u, 0, cx + 24 * u, 0, [(0, "#f4f7fc"), (0.6, "#c4cddb"), (1, "#7d8aa0")]), shadow=(0, 5 * u, 7 * u, "#0009"))
    cv.circle(cx, cy - 14 * u, 10 * u, fill="#0b1c2c")
    cv.circle(cx, cy - 14 * u, 7 * u, fill=c1)


def clock(cv, cx, cy, u, t, c1, c2):
    cv.circle(cx, cy, 48 * u, fill=lin(cx, cy - 48 * u, cx, cy + 48 * u, [(0, "#1d2c4d"), (1, "#0a1224")]), shadow=(0, 6 * u, 8 * u, "#000a"))
    cv.circle(cx, cy, 48 * u, stroke=c1, width=6 * u)
    for i in range(12):
        a = i * math.pi / 6
        r0 = 38 if i % 3 == 0 else 42
        cv.line(cx + r0 * u * math.sin(a), cy - r0 * u * math.cos(a), cx + 45 * u * math.sin(a), cy - 45 * u * math.cos(a), "#e8f2ff", 3 * u)
    ma, ha = t * 1.2, t * 0.1
    cv.line(cx, cy, cx + 34 * u * math.sin(ma), cy - 34 * u * math.cos(ma), c2, 4 * u)
    cv.line(cx, cy, cx + 22 * u * math.sin(ha), cy - 22 * u * math.cos(ha), "#ffffff", 5 * u)
    cv.circle(cx, cy, 5 * u, fill=c2)


def battery(cv, cx, cy, u, t, c1, c2):
    lv = 0.3 + 0.7 * ((t * 0.35) % 1)
    cv.rrect(cx - 44 * u, cy - 28 * u, cx + 36 * u, cy + 28 * u, 8 * u, fill="#0b1424", shadow=(0, 6 * u, 8 * u, "#000a"))
    cv.rrect(cx + 36 * u, cy - 11 * u, cx + 48 * u, cy + 11 * u, 4 * u, fill="#c9d4e6")
    col = "#5dff9a" if lv > 0.5 else "#ffd34f"
    cv.rrect(cx - 38 * u, cy - 22 * u, cx - 38 * u + 68 * u * lv, cy + 22 * u, 5 * u, fill=lin(0, cy - 22 * u, 0, cy + 22 * u, [(0, col), (1, "#1f9a5a")]))
    cv.rrect(cx - 44 * u, cy - 28 * u, cx + 36 * u, cy + 28 * u, 8 * u, stroke="#e8f2ff", width=4 * u)


def atom(cv, cx, cy, u, t, c1, c2):
    for ang in (0, 60, 120):
        cv.save()
        cv.rotate(ang, cx, cy)
        cv.oval(cx - 50 * u, cy - 18 * u, cx + 50 * u, cy + 18 * u, stroke=c1, width=3.2 * u, alpha=0.9)
        cv.restore()
    for i, ang in enumerate((0, 60, 120)):
        a = t * 2.2 + i * 2.1
        x, y = 50 * math.cos(a), 18 * math.sin(a)
        r = math.radians(ang)
        ex, ey = cx + (x * math.cos(r) - y * math.sin(r)) * u, cy + (x * math.sin(r) + y * math.cos(r)) * u
        cv.circle(ex, ey, 6 * u, fill=c2, blur=0)
        cv.circle(ex, ey, 10 * u, fill=c2, alpha=0.35, blur=4 * u)
    cv.circle(cx, cy, 11 * u, fill=rad(cx - 3 * u, cy - 3 * u, 14 * u, [(0, "#fff"), (1, "#ff6a5a")]))


def wind(cv, cx, cy, u, t, c1, c2):
    for i, (y, x0, x1) in enumerate([(-24, -46, 14), (0, -46, 34), (24, -46, 4)]):
        dx = 5 * math.sin(t * 2 + i * 1.3)
        p = skia.Path()
        p.moveTo(cx + (x0 + dx) * u, cy + y * u)
        p.lineTo(cx + (x1 + dx) * u, cy + y * u)
        p.cubicTo(cx + (x1 + 22 + dx) * u, cy + y * u, cx + (x1 + 22 + dx) * u, cy + (y - 26) * u, cx + (x1 + dx - 4) * u, cy + (y - 26) * u)
        cv.path(p, stroke=c1 if i != 1 else "#ffffff", width=7 * u, alpha=0.95)


def thermo(cv, cx, cy, u, t, c1, c2):
    lv = 0.45 + 0.45 * (0.5 + 0.5 * math.sin(t))
    cv.rrect(cx - 13 * u, cy - 50 * u, cx + 13 * u, cy + 24 * u, 13 * u, fill="#0b1424", shadow=(0, 6 * u, 8 * u, "#000a"))
    cv.circle(cx, cy + 32 * u, 22 * u, fill="#0b1424")
    top = cy + 22 * u - 64 * u * lv
    cv.rrect(cx - 5 * u, top, cx + 5 * u, cy + 30 * u, 5 * u, fill="#ff4a3a")
    cv.circle(cx, cy + 32 * u, 17 * u, fill=rad(cx - 5 * u, cy + 27 * u, 24 * u, [(0, "#ff9a8a"), (1, "#d6231a")]))
    cv.rrect(cx - 13 * u, cy - 50 * u, cx + 13 * u, cy + 24 * u, 13 * u, stroke="#e8f2ff", width=4 * u)
    for i in range(5):
        cv.line(cx + 20 * u, cy - 36 * u + i * 13 * u, cx + (34 if i % 2 == 0 else 28) * u, cy - 36 * u + i * 13 * u, "#e8f2ff", 3 * u)


def scale(cv, cx, cy, u, t, c1, c2):
    ang = 7 * math.sin(t * 1.2)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    cv.rrect(cx - 4 * u, cy - 40 * u, cx + 4 * u, cy + 46 * u, 3 * u, fill=lin(cx - 4 * u, 0, cx + 4 * u, 0, [(0, "#ffe9a0"), (1, "#b8820f")]))
    cv.poly(_poly([(-26, 52), (26, 52), (14, 40), (-14, 40)], cx, cy, u), fill="#b8820f")
    bx0, by0, bx1, by1 = cx - 46 * u * ca, cy - 36 * u - 46 * u * sa, cx + 46 * u * ca, cy - 36 * u + 46 * u * sa
    cv.line(bx0, by0, bx1, by1, "#ffe9a0", 6 * u)
    for (x, y) in ((bx0, by0), (bx1, by1)):
        cv.line(x, y, x - 20 * u, y + 34 * u, "#cdd6e6", 2.4 * u)
        cv.line(x, y, x + 20 * u, y + 34 * u, "#cdd6e6", 2.4 * u)
        cv.poly([(x - 26 * u, y + 34 * u), (x + 26 * u, y + 34 * u), (x + 16 * u, y + 44 * u), (x - 16 * u, y + 44 * u)],
                fill=lin(0, y + 34 * u, 0, y + 44 * u, [(0, "#ffe9a0"), (1, "#b8820f")]))
    cv.circle(cx, cy - 36 * u, 6 * u, fill="#fff3c0")


def question(cv, cx, cy, u, t, c1, c2):
    cv.circle(cx, cy, 46 * u, fill=lin(cx, cy - 46 * u, cx, cy + 46 * u, [(0, "#2c4a8a"), (1, "#0e1b3c")]), shadow=(0, 6 * u, 8 * u, "#000a"))
    cv.circle(cx, cy, 46 * u, stroke=c1, width=5 * u)
    cv.text("?", cx, cy + 34 * u, 100 * u, fill="#ffffff", center=True, glow=(c1, 10 * u))


def check(cv, cx, cy, u, t, c1, c2):
    cv.circle(cx, cy, 46 * u, fill=lin(cx, cy - 46 * u, cx, cy + 46 * u, [(0, "#3fe08a"), (1, "#0f7a45")]), shadow=(0, 6 * u, 8 * u, "#000a"))
    p = skia.Path()
    p.moveTo(cx - 22 * u, cy + 2 * u)
    p.lineTo(cx - 6 * u, cy + 18 * u)
    p.lineTo(cx + 24 * u, cy - 16 * u)
    cv.path(p, stroke="#ffffff", width=10 * u)


_FN = {"gear": gear, "bolt": bolt, "drop": drop, "flame": flame, "snow": snow, "building": building, "car": car,
       "planet": planet, "rocket": rocket, "clock": clock, "battery": battery, "atom": atom, "wind": wind,
       "thermo": thermo, "scale": scale, "question": question, "check": check}
ICONS = sorted(_FN)

_HALO = {"bolt": "#ffd34f", "flame": "#ff7a1a", "drop": "#35b8ee", "snow": "#bfefff", "rocket": "#ff9a1a", "atom": "#7fe4ff"}


def draw_icon(cv, name, cx, cy, size, t=0.0, c1="#7fe4ff", c2="#ffc45e", halo=True):
    fn = _FN.get(name)
    if fn is None:
        raise KeyError("нет иконки %r; доступны: %s" % (name, ", ".join(ICONS)))
    u = size / 110.0
    if halo:
        _halo(cv, cx, cy, size, _HALO.get(name, c1))
    fn(cv, cx, cy, u, t, c1, c2)
