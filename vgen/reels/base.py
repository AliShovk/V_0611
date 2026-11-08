"""Общая библиотека для серии «Истории, в которые невозможно поверить».

Каждый ролик — свой стиль (палитра, фактура, типографика), общие только примитивы.
"""
import math
import random

import skia

from vgen.kit import Canvas, W, H, lin, rad, rgba

INK = "#0a0d12"


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def kof(ctx, t, win):
    if ctx and ctx.get("scene_dur"):
        return max(0.0, min(1.0, ctx["scene_t"] / ctx["scene_dur"]))
    t0, t1 = win
    return max(0.0, min(1.0, (t - t0) / max(0.1, t1 - t0)))


def sp(color, width, alph=255):
    alph = max(0, min(255, int(alph)))
    return skia.Paint(AntiAlias=True, Color=rgba(color, alph / 255.0),
                      Style=skia.Paint.kStroke_Style, StrokeWidth=width,
                      StrokeCap=skia.Paint.kRound_Cap)


def ellipse(cv, cx, cy, rx, ry, **kw):
    cv.oval(cx - rx, cy - ry, cx + rx, cy + ry, **kw)


def text(cv, s, *a, alpha=None, stroke=None, sw=8, glow=None, x=540, center=True):
    """Два стиля: (y, size, color[, alpha]) или (x, y, size, color[, alpha])."""
    al = 1.0 if alpha is None else float(alpha)
    if len(a) == 3:
        y, size, color = a
    elif len(a) == 4:
        if isinstance(a[3], str):
            x, y, size, color = a
        else:
            y, size, color, al = a
    elif len(a) >= 5:
        if isinstance(a[3], str):
            x, y, size, color = a[:4]
            al = a[4]
        else:
            y, size, color, al = a[:4]
    else:
        raise TypeError("B.text: нужно 3-5 аргументов")
    al = max(0.0, min(1.0, float(al)))
    cv.text(s, x, y, size, fill=color, center=center, alpha=al, stroke=stroke,
            stroke_w=sw, glow=glow)


def label(cv, s, y, size, color="#ffffff", alpha=1.0, x=540, stroke=None, sw=8, glow=None):
    text(cv, s, x, y, size, color, alpha, stroke=stroke, sw=sw, glow=glow)


def grain(cv, strength=10, seed=7, alpha=0.5):
    rnd = random.Random(seed)
    for _ in range(int(strength * 22)):
        x = rnd.randint(0, W)
        y = rnd.randint(0, H)
        cv.circle(x, y, 1, fill="#ffffff" if rnd.random() > 0.5 else "#000000",
                  alpha=abs(alpha * rnd.random() * 0.35))


def vignette(cv, color=INK, a=0.55):
    cv.rect(0, 0, W, H, fill=color, alpha=a)


def scanlines(cv, step=6, alpha=0.10):
    for y in range(0, H, step):
        cv.rect(0, y, W, y + 1, fill="#000000", alpha=alpha)


def rays(cv, cx, cy, t, n=14, color="#ffffff", alpha=0.08, r=1400):
    for i in range(n):
        ang = i * (2 * math.pi / n) + t * 0.15
        x2 = cx + math.cos(ang) * r
        y2 = cy + math.sin(ang) * r
        p = skia.Path()
        p.moveTo(cx, cy)
        p.lineTo(x2 - 90 * math.sin(ang), y2 + 90 * math.cos(ang))
        p.lineTo(x2 + 90 * math.sin(ang), y2 - 90 * math.cos(ang))
        p.close()
        cv.path(p, fill=color, alpha=abs(alpha * (0.5 + 0.5 * math.sin(i + t))))


def person(cv, x, y, s=1.0, color="#1b2430", skin="#e6c9a8", alpha=1.0):
    cv.circle(x, y - 30 * s, 10 * s, fill=skin, alpha=alpha)
    cv.rrect(x - 9 * s, y - 20 * s, x + 9 * s, y + 4 * s, 7 * s, fill=color, alpha=alpha)
    cv.line(x - 7 * s, y + 4 * s, x - 11 * s, y + 30 * s, color, 4 * s, alpha=alpha)
    cv.line(x + 7 * s, y + 4 * s, x + 11 * s, y + 30 * s, color, 4 * s, alpha=alpha)
    cv.line(x - 7 * s, y - 12 * s, x - 16 * s, y + 6 * s, color, 3.5 * s, alpha=alpha)
    cv.line(x + 7 * s, y - 12 * s, x + 16 * s, y + 6 * s, color, 3.5 * s, alpha=alpha)


def crowd(cv, t, y, n=8, color="#1b2430", alpha=1.0, wobble=1.0, x0=60, dx=115):
    for i in range(n):
        person(cv, x0 + i * dx, y + 5 * wobble * math.sin(t * 2 + i), 0.9 + 0.15 * (i % 3),
               color, alpha=alpha)


def dust(cv, t, n=40, color="#ffffff", alpha=0.25, speed=18):
    for i in range(n):
        x = (i * 127 + t * speed * (0.5 + (i % 5) / 5)) % W
        y = (i * 211 + t * speed * 0.6) % H
        cv.circle(x, y, 1 + (i % 3), fill=color,
                  alpha=abs(alpha * (0.4 + 0.6 * math.sin(i + t))))


def ship(cv, x, y, s=1.0, hull="#20293a", deck="#c9d6e4", steam=True, alpha=1.0):
    cv.poly([(x - 150 * s, y - 30 * s), (x + 150 * s, y - 30 * s), (x + 110 * s, y + 20 * s),
             (x - 110 * s, y + 20 * s)], fill=hull, alpha=alpha)
    cv.rect(x - 110 * s, y - 62 * s, x + 70 * s, y - 30 * s, fill=deck, alpha=alpha)
    for i in range(4):
        cx = x - 90 * s + i * 44 * s
        cv.circle(cx, y - 48 * s, 5 * s, fill=INK, alpha=0.75 * alpha)
    if steam:
        cv.rect(x - 40 * s, y - 108 * s, x + 6 * s, y - 62 * s, fill="#31394a", alpha=alpha)
        cv.rect(x - 18 * s, y - 140 * s, x - 8 * s, y - 100 * s, fill="#31394a", alpha=alpha)


def wave(cv, t, level, amp=18, color="#1d4f6b", foam="#dff2ff", alpha=1.0):
    cv.rect(0, level, W, H, fill=color, alpha=alpha)
    p = skia.Path()
    pts = []
    for x in range(-20, W + 40, 12):
        pts.append((x, level + amp * math.sin(x * 0.012 + t * 1.8)))
    p.moveTo(pts[0][0], pts[0][1])
    for x, y in pts[1:]:
        p.lineTo(x, y)
    cv.c.drawPath(p, sp(foam, 5, 190 * alpha))


def spiral(cv, cx, cy, t, r0=40, r1=520, turns=3.2, color="#ffffff", alpha=0.35, width=7):
    p = skia.Path()
    steps = 260
    for i in range(steps + 1):
        k = i / steps
        ang = t * 1.2 + k * turns * 2 * math.pi
        rr = r0 + (r1 - r0) * k
        x = cx + math.cos(ang) * rr
        y = cy + math.sin(ang) * rr * 0.62
        (p.moveTo if i == 0 else p.lineTo)(x, y)
    cv.c.drawPath(p, sp(color, width, 255 * alpha))


def treeline(cv, y, color="#0d1a16", alpha=1.0, n=26, seed=5, hmin=60, hmax=160):
    rnd = random.Random(seed)
    for i in range(n):
        x = i * (W // n) + rnd.randint(-10, 10)
        h = rnd.randint(hmin, hmax)
        cv.poly([(x - 18, y), (x + 18, y), (x, y - h)], fill=color, alpha=alpha)


def big_number(cv, s, y, size, color="#ffffff", glow=None, alpha=1.0, stroke=INK, sw=12):
    cv.text(s, 540, y, size, fill=color, center=True, alpha=max(0.0, min(1.0, alpha)),
            stroke=stroke, stroke_w=sw, glow=glow)


def caption(cv, txt, hl=(), size=50, y=1726, bar_y0=1662, bar_y1=1750, fill="#0b0f16",
            color="#fff4e2", hl_color="#ffd08a"):
    if not txt:
        return
    words = txt.split()
    width = sum(cv.text_w(w + " ", size) for w in words)
    while width > 930 and size > 26:
        size -= 3
        width = sum(cv.text_w(w + " ", size) for w in words)
    x = 540 - width / 2
    cv.rrect(540 - width / 2 - 26, bar_y0, 540 + width / 2 + 26, bar_y1, 16, fill=fill, alpha=0.84)
    for w in words:
        col = hl_color if any(h.lower() in w.lower() for h in hl) else color
        cv.text(w, x, y, size, fill=col)
        x += cv.text_w(w + " ", size)


def render(name, t, ctx, scenes, cap=True):
    ctx = ctx or {}
    cv = Canvas()
    cv.save()
    cv.c.translate(3 * math.sin(t * 0.6), 2 * math.cos(t * 0.5))
    scenes[name](cv, t, ctx)
    cv.restore()
    if cap:
        caption(cv, ctx.get("caption_text", ""), ctx.get("caption_hl", ()))
    return cv.to_pil()
