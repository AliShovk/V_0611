"""Почему маяк не смывает 30-метровой волной. Skia, тёмное море, 6 сцен."""
import math

import skia

from vgen.kit import Canvas, W, H, lin, rad, rgba

NIGHT = "#040a14"
SEA_D = "#07182a"
SEA_L = "#0e3350"
FOAM = "#dfefff"
STONE = "#c9d4e0"
STONE_D = "#8a99a8"
GOLD = "#ffc45e"
RED = "#ff6a5a"
CYAN = "#8fd8ff"

BASE = 1500


def _sp(color, width, alph=255):
    alph = max(0, min(255, int(alph)))
    return skia.Paint(AntiAlias=True, Color=rgba(color, alph / 255.0),
                      Style=skia.Paint.kStroke_Style, StrokeWidth=width,
                      StrokeCap=skia.Paint.kRound_Cap)


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def k_of(ctx, t, win):
    if ctx and ctx.get("scene_dur"):
        return max(0.0, min(1.0, ctx["scene_t"] / ctx["scene_dur"]))
    t0, t1 = win
    return max(0.0, min(1.0, (t - t0) / max(0.1, t1 - t0)))


def label(cv, s, size, y, color=FOAM, x=540, alpha=1.0, stroke=NIGHT, sw=8):
    cv.text(s, x, y, size, fill=color, center=True, alpha=alpha, stroke=stroke, stroke_w=sw)


# ---------- море ----------

def sky(cv, t, dawn=0.0):
    cv.rect(0, 0, W, 1100, fill=lin(0, 0, 0, 1100, [
        (0, "#04070f"), (0.5, "#081422"), (1, "#123049")]))
    if dawn > 0.02:
        cv.rect(0, 0, W, 1100, fill=lin(0, 0, 0, 1100,
                                        [(0, "#1b2c44"), (1, "#f0a878")]), alpha=0.35 * dawn)
        cv.circle(760, 980, 160, fill="#ffd9a0", alpha=0.45 * dawn, blur=70)


def sea(cv, t, level=BASE, amp=26, cols=(SEA_D, SEA_L)):
    cv.rect(0, level - 40, W, H, fill=lin(0, level, 0, H, [(0, cols[1]), (1, cols[0])]))
    for band in range(7):
        p = skia.Path()
        y0 = level + band * 62
        for x in range(-20, W + 40, 12):
            y = y0 + amp * math.sin(x * 0.012 + t * (1.1 + band * 0.15) + band)
            (p.moveTo if x == -20 else p.lineTo)(x, y)
        cv.c.drawPath(p, _sp("#9fd8ff" if band % 2 else "#5f9cc4", 2.5,
                             max(20, 90 - band * 10)))


def spray(cv, t, x, y, n=18, power=1.0, alpha=0.6):
    for i in range(n):
        ph = (t * 1.6 + i * 0.37) % 1.0
        px = x + (i - n / 2) * 9 * power + 26 * math.sin(ph * 4 + i)
        py = y - 90 * power * math.sin(ph * math.pi) * (0.4 + 0.6 * (i % 3) / 2)
        r = 2 + 3 * (i % 4)
        cv.circle(px, py, r, fill=FOAM, alpha=alpha * (1 - ph) * 0.9)


def big_wave(cv, t, x0, height, power=1.0, alpha=1.0):
    """Стена воды, поднимающаяся справа от башни."""
    h = height * power
    p = skia.Path()
    p.moveTo(x0 + 380, BASE + 60)
    p.cubicTo(x0 + 300, BASE - h * 0.25, x0 + 240, BASE - h * 0.8, x0 + 120, BASE - h)
    p.cubicTo(x0 + 40, BASE - h * 1.02, x0 - 40, BASE - h * 0.85, x0 - 70, BASE - h * 0.55)
    p.lineTo(x0 - 70, BASE + 60)
    p.close()
    cv.path(p, fill=lin(0, BASE - h, 0, BASE, [(0, "#bfe6ff"), (0.35, "#3d86b8"), (1, "#0b2740")]),
            alpha=alpha)
    # пена по гребню
    for i in range(16):
        px = x0 + 120 - i * 12
        py = BASE - h + 18 * math.sin(i * 1.3 + t * 5)
        cv.circle(px, py, 5 + (i % 3) * 3, fill=FOAM, alpha=0.55 * alpha)
    spray(cv, t, x0 + 60, BASE - h * 0.9, 22, 1.2, 0.5 * alpha)


# ---------- маяк ----------

def tower(cv, cx, base_y, h, curved=True, alpha=1.0, lamp=True, t=0.0, beam=1.0):
    top_w, base_w = (62, 150) if curved else (120, 120)
    p = skia.Path()
    p.moveTo(cx - top_w / 2, base_y - h)
    p.lineTo(cx + top_w / 2, base_y - h)
    if curved:
        p.cubicTo(cx + top_w / 2 + 46, base_y - h * 0.55,
                  cx + base_w / 2 + 12, base_y - h * 0.22, cx + base_w / 2, base_y)
    else:
        p.lineTo(cx + base_w / 2, base_y)
    p.lineTo(cx - base_w / 2, base_y)
    if curved:
        p.cubicTo(cx - base_w / 2 - 12, base_y - h * 0.22,
                  cx - top_w / 2 - 46, base_y - h * 0.55, cx - top_w / 2, base_y - h)
    else:
        p.lineTo(cx - top_w / 2, base_y - h)
    p.close()
    cv.path(p, fill=lin(cx - base_w / 2, 0, cx + base_w / 2, 0,
                        [(0, "#eef5fb"), (0.45, STONE), (1, STONE_D)]), alpha=alpha)
    # полосы и окна
    for i in range(4):
        y = base_y - h * (0.18 + i * 0.19)
        cv.rect(cx - base_w / 2 - 4, y, cx + base_w / 2 + 4, y + 14, fill=RED, alpha=0.75 * alpha)
    # фонарь
    cv.rrect(cx - 46, base_y - h - 58, cx + 46, base_y - h, 10, fill="#22384c", alpha=alpha)
    if lamp:
        cv.circle(cx, base_y - h - 29, 26, fill=GOLD, alpha=alpha, blur=16)
        cv.circle(cx, base_y - h - 29, 12, fill="#fff6d8", alpha=alpha)
    # крыша
    cv.poly([(cx - 50, base_y - h - 58), (cx + 50, base_y - h - 58), (cx, base_y - h - 96)],
            fill="#22384c", alpha=alpha)
    if beam and lamp:
        for s in (-1, 1):
            sweep = math.sin(t * 1.2) * 0.6
            bx = cx + s * (60 + 420 * abs(math.cos(t * 1.2)))
            cv.poly([(cx, base_y - h - 29), (bx + s * 180, base_y - h - 29 - 120 + 240 * sweep),
                     (bx + s * 180, base_y - h - 29 + 60 + 240 * sweep)],
                    fill="#ffe9b0", alpha=0.10 * beam * alpha)


def rock(cv, cx, y, w=460, h=150):
    p = skia.Path()
    p.moveTo(cx - w / 2, y + h)
    p.cubicTo(cx - w / 2 + 40, y, cx - 120, y - 30, cx - 40, y - 10)
    p.cubicTo(cx + 40, y - 34, cx + 140, y - 6, cx + w / 2, y + h)
    p.close()
    cv.path(p, fill=lin(cx - w / 2, y, cx + w / 2, y + h,
                        [(0, "#42566a"), (0.5, "#2b3a49"), (1, "#131d28")]))


# ---------- сцены ----------

def scene_hook(cv, t, ctx):
    k = k_of(ctx, t, (0, 8))
    sky(cv, t)
    sea(cv, t, BASE, 30)
    rock(cv, 540, BASE - 20)
    tower(cv, 540, BASE - 30, 700, True, t=t, beam=1.0)
    big_wave(cv, t, 620, 620, power=0.8 + 0.25 * ease(k))
    if k > 0.05:
        a = ease((k - 0.05) / 0.2)
        cv.text("30", 540, 300, 260, fill="#ffffff", center=True,
                stroke=NIGHT, stroke_w=14, glow=(CYAN, 30), alpha=a)
        label(cv, "МЕТРОВ ВОДЫ", 46, 372, GOLD, alpha=a)
    if k > 0.45:
        label(cv, "И ОН СТОИТ", 60, 460, FOAM, alpha=ease((k - 0.45) / 0.3))


def scene_shape(cv, t, ctx):
    k = k_of(ctx, t, (8, 17))
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#061020"), (1, "#0b1d2e")]))
    # две башни: прямая и изогнутая
    tower(cv, 300, 1200, 520, curved=False, lamp=False, beam=0)
    tower(cv, 780, 1200, 520, curved=True, lamp=False, beam=0)
    # линии потока вокруг
    for i, (cx, curved) in enumerate([(300, False), (780, True)]):
        for j in range(5):
            p = skia.Path()
            y0 = 760 + j * 70
            p.moveTo(cx - 220, y0)
            if curved:
                p.cubicTo(cx - 120, y0 - 20, cx - 110, y0 + 40, cx - 60, y0 + 30)
                p.cubicTo(cx + 60, y0 + 40, cx + 140, y0 - 10, cx + 240, y0 + 10)
            else:
                p.lineTo(cx + 240, y0)
            cv.c.drawPath(p, _sp(CYAN, 2.5, int(120 + 80 * math.sin(t * 2 + j))))
        if not curved:
            spray(cv, t, cx + 90, 900, 16, 0.9, 0.7)

    label(cv, "ПРЯМАЯ СТЕНА", 30, 1300, "#9fb4c8")
    label(cv, "ИЗОГНУТЫЙ ПРОФИЛЬ", 30, 1300, "#9fb4c8", x=780)
    if k > 0.2:
        a = ease((k - 0.2) / 0.3)
        label(cv, "ВОДА ОБТЕКАЕТ, А НЕ БЬЁТ", 40, 220, FOAM, alpha=a)
        label(cv, "ФОРМА ВАЖНЕЕ ТОЛЩИНЫ СТЕН", 28, 1370, GOLD, alpha=a)


def scene_stone(cv, t, ctx):
    k = k_of(ctx, t, (17, 26))
    cv.clear("#071120")
    # разрез кладки: блоки с замком
    x0, y0, bw, bh = 240, 420, 300, 120
    for row in range(4):
        for col in range(2):
            x = x0 + col * bw
            y = y0 + row * bh
            p = skia.Path()
            # ласточкин хвост: скошенные торцы
            p.moveTo(x + 12, y)
            p.lineTo(x + bw - 12, y)
            p.lineTo(x + bw, y + bh / 2)
            p.lineTo(x + bw - 12, y + bh)
            p.lineTo(x + 12, y + bh)
            p.lineTo(x, y + bh / 2)
            p.close()
            cv.path(p, fill=lin(x, y, x, y + bh, [(0, "#dbe6f2"), (1, "#93a3b4")]))
            cv.c.drawPath(p, _sp("#3f5266", 3))
    # стрелки нагрузки
    for i in range(3):
        y = y0 + 40 + i * 110
        cv.line(x0 - 90, y, x0 - 10, y + 10, GOLD, 4)
        cv.poly([(x0 - 14, y + 6), (x0 - 30, y - 4), (x0 - 30, y + 20)], fill=GOLD)
    if k > 0.15:
        a = ease((k - 0.15) / 0.3)
        label(cv, "ГРАНИТНЫЕ БЛОКИ ЗАМКОМ", 40, 240, FOAM, alpha=a)
        label(cv, "КАЖДЫЙ ЦЕПЛЯЕТСЯ ЗА СОСЕДЕЙ", 26, 980, "#9fd8ff", alpha=a)
        label(cv, "1759 · ЭДДИСТОУН", 30, 1600, GOLD, alpha=a)


def scene_base(cv, t, ctx):
    k = k_of(ctx, t, (26, 34))
    sky(cv, t)
    sea(cv, t, BASE - 60, 22)
    rock(cv, 540, BASE - 120, 560, 150)
    # анкеры в скалу
    for i in range(5):
        x = 420 + i * 60
        cv.line(x, BASE - 110, x + 8, BASE + 20, "#8fa6bb", 7)
        cv.circle(x + 8, BASE + 20, 8, fill="#5f7488")
    tower(cv, 540, BASE - 110, 640, True, t=t, beam=0.6)
    # волна бьётся о скалу
    big_wave(cv, t, 720, 260, power=0.8)
    if k > 0.15:
        a = ease((k - 0.15) / 0.3)
        label(cv, "ВОЛНА ЛОМАЕТСЯ О СКАЛУ", 40, 220, FOAM, alpha=a)
        label(cv, "А НЕ О СТЕНУ", 34, 276, GOLD, alpha=a)


def scene_door(cv, t, ctx):
    k = k_of(ctx, t, (34, 41))
    sky(cv, t)
    sea(cv, t, BASE, 26)
    rock(cv, 540, BASE - 20)
    tower(cv, 540, BASE - 30, 760, True, t=t, beam=0.8)
    # линия гребня волны
    cy = BASE - 470
    cv.line(80, cy, 1000, cy, RED, 3, alpha=0.7)
    cv.text("ГРЕБЕНЬ ВОЛНЫ", 700, cy - 18, 26, fill="#ffd1cc", center=True)
    # дверь выше
    cv.rrect(600, cy - 190, 660, cy - 110, 6, fill="#22384c", stroke=FOAM, width=3)
    label(cv, "ДВЕРЬ ВЫШЕ ГРЕБНЯ", 30, cy - 220, "#9fd8ff", x=700)
    if k > 0.2:
        label(cv, "ВХОД ПОДНЯТ НАД ВОДОЙ", 38, 220, FOAM, alpha=ease((k - 0.2) / 0.3))


def scene_final(cv, t, ctx):
    k = k_of(ctx, t, (41, 49))
    dawn = ease(k)
    sky(cv, t, dawn=dawn)
    sea(cv, t, BASE, 20)
    rock(cv, 540, BASE - 20)
    tower(cv, 540, BASE - 30, 720, True, t=t, beam=1.0)
    if k > 0.1:
        a = ease((k - 0.1) / 0.3)
        label(cv, "МАЯК НЕ СОПРОТИВЛЯЕТСЯ", 40, 260, FOAM, alpha=a)
        label(cv, "ОН ОБТЕКАЕТ ВОЛНУ", 56, 330, GOLD, alpha=a)
    if k > 0.55:
        label(cv, "ЭДДИСТОУН · 1759", 28, 1760, "#cfe6ff", alpha=ease((k - 0.55) / 0.3))


SCENES = {
    "hook": scene_hook,
    "shape": scene_shape,
    "stone": scene_stone,
    "base": scene_base,
    "door": scene_door,
    "final": scene_final,
}


def caption(cv, text, hl):
    if not text:
        return
    size = 50
    words = text.split()
    width = sum(cv.text_w(w + " ", size) for w in words)
    while width > 930 and size > 26:
        size -= 3
        width = sum(cv.text_w(w + " ", size) for w in words)
    x = 540 - width / 2
    cv.rrect(540 - width / 2 - 26, 1758, 540 + width / 2 + 26, 1844, 18, fill="#040a14", alpha=0.82)
    for w in words:
        col = "#ffd08a" if any(h.lower() in w.lower() for h in hl) else FOAM
        cv.text(w, x, 1820, size, fill=col)
        x += cv.text_w(w + " ", size)


def render(name, t, ctx=None, finish=False):
    ctx = ctx or {}
    cv = Canvas()
    cv.save()
    cv.c.translate(3 * math.sin(t * 0.5), 2 * math.cos(t * 0.4))
    SCENES[name](cv, t, ctx)
    cv.restore()
    caption(cv, ctx.get("caption_text", ""), ctx.get("caption_hl", ()))
    return cv.to_pil()
