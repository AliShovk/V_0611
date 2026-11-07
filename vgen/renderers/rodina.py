"""«Родина-мать зовёт» (Волгоград): 85 м, меч 33 м, 1959–1967. Skia-рендер.

Сцены: hook (силуэт и 85 м) → build (1959–1967) → sword (33 м / 14 т) →
core (преднапряжённый железобетон и тросы) → wind (раскачка и ветер) → final (рассвет).

Интерфейс: render(name, t, ctx) -> PIL.Image 1080x1920.
"""
import math

import skia

from vgen.kit import Canvas, W, H, lin, rad, rgba

NIGHT = "#050a14"
DEEP = "#0a1626"
STONE = "#b9c4d0"
STONE_D = "#7b8794"
GOLD = "#ffc45e"
CREAM = "#f6f1e4"
RED = "#d94a3d"
CYAN = "#8fd8ff"

BASE = 1560
HORIZON = 1400


def _sp(color, width, alph=255):
    return skia.Paint(AntiAlias=True, Color=rgba(color, alph / 255.0),
                      Style=skia.Paint.kStroke_Style, StrokeWidth=width)


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def mix(c1, c2, k):
    k = max(0.0, min(1.0, k))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[j] + (b[j] - a[j]) * k) for j in range(3))


def k_of(ctx, t, win):
    if ctx and ctx.get("scene_dur"):
        return max(0.0, min(1.0, ctx["scene_t"] / ctx["scene_dur"]))
    t0, t1 = win
    return max(0.0, min(1.0, (t - t0) / max(0.1, t1 - t0)))


# ---------- фон ----------

def sky(cv, t, dawn=0.0):
    cv.rect(0, 0, W, HORIZON, fill=lin(0, 0, 0, HORIZON, [
        (0.0, "#04080f"), (0.45, mix("#0a1730", "#26344a", dawn)),
        (0.78, mix("#1d2a3d", "#7c5a52", dawn)), (1.0, mix("#33404f", "#e2a273", dawn))]))
    for i in range(40):
        x = (i * 173) % W
        y = 60 + (i * 211) % 780
        a = 0.30 * (0.5 + 0.5 * math.sin(t * 1.1 + i)) * (1 - dawn)
        if a > 0.02:
            cv.circle(x, y, 1.3, fill="#dce9ff", alpha=a)


def mound(cv, t):
    """Мамаев курган: два плана склона и дорожка."""
    far = skia.Path()
    far.moveTo(0, HORIZON - 120)
    for x in range(0, W + 60, 60):
        far.lineTo(x, HORIZON - 120 + 40 * math.sin(x * 0.006 + 0.8))
    far.lineTo(W, H)
    far.lineTo(0, H)
    far.close()
    cv.path(far, fill="#111d2b")

    near = skia.Path()
    near.moveTo(0, HORIZON + 60)
    for x in range(0, W + 60, 60):
        near.lineTo(x, HORIZON + 60 + 55 * math.sin(x * 0.009 + 2.4))
    near.lineTo(W, H)
    near.lineTo(0, H)
    near.close()
    cv.path(near, fill=lin(0, HORIZON, 0, H, [(0, "#1b2a3a"), (1, "#070d15")]))
    # дорожка к подножию
    cv.poly([(470, H), (610, H), (556, HORIZON + 120), (524, HORIZON + 120)],
            fill="#2a3a4c", alpha=0.55)


_BG = {}


def static_bg():
    if "img" not in _BG:
        c2 = Canvas()
        sky(c2, 0, 0)
        mound(c2, 0)
        _BG["img"] = c2.surface.makeImageSnapshot()
    return _BG["img"]


# ---------- статуя ----------

def statue(cv, cx, base_y, h, phase=0.0, sway=7.0, sword=True, detail=True, alpha=1.0,
           color=STONE):
    """Женская фигура: широкий подол, торс, поднятая рука с мечом.

    h — высота фигуры без меча. Наклон задаётся поворотом вокруг ступней.
    """
    ang = sway * 0.02 * math.sin(phase)
    u = h / 100.0

    cv.save()
    cv.c.rotate(ang, cx, base_y)

    def X(dx):
        return cx + dx * u

    def Y(dy):
        return base_y - dy * u

    # --- подол и торс одним силуэтом
    body = skia.Path()
    body.moveTo(X(-46), Y(0))
    body.cubicTo(X(-40), Y(18), X(-34), Y(34), X(-30), Y(48))   # левый край подола
    body.cubicTo(X(-24), Y(58), X(-22), Y(64), X(-24), Y(70))   # талия
    body.cubicTo(X(-27), Y(76), X(-26), Y(82), X(-20), Y(86))   # плечо
    body.lineTo(X(-9), Y(89))
    body.lineTo(X(9), Y(89))
    body.lineTo(X(21), Y(86))
    body.cubicTo(X(27), Y(81), X(26), Y(75), X(23), Y(70))
    body.cubicTo(X(21), Y(63), X(23), Y(57), X(29), Y(48))
    body.cubicTo(X(33), Y(33), X(39), Y(17), X(46), Y(0))
    body.close()
    cv.path(body, fill=color, alpha=alpha)

    # тень на правой половине
    shade = skia.Path()
    shade.moveTo(X(4), Y(88))
    shade.cubicTo(X(20), Y(84), X(22), Y(70), X(26), Y(48))
    shade.cubicTo(X(31), Y(32), X(40), Y(16), X(46), Y(0))
    shade.lineTo(X(18), Y(0))
    shade.cubicTo(X(22), Y(30), X(14), Y(60), X(4), Y(88))
    shade.close()
    cv.path(shade, fill="#000000", alpha=0.16 * alpha)

    # --- шея и голова
    cv.line(X(0), Y(84), X(0), Y(93), color, 9 * u, alpha=alpha)
    cv.circle(X(0), Y(96.5), 7.4 * u, fill=color, alpha=alpha)

    # --- левая рука опущена вдоль тела
    cv.line(X(21), Y(85), X(33), Y(74), color, 8 * u, alpha=alpha)
    cv.line(X(33), Y(74), X(31), Y(60), color, 8 * u, alpha=alpha)
    cv.circle(X(31), Y(58), 3.6 * u, fill=color, alpha=alpha)

    # --- правая рука поднята к мечу
    hand_x, hand_y = X(-24), Y(112)
    cv.line(X(-20), Y(84), X(-26), Y(98), color, 9 * u, alpha=alpha)
    cv.line(X(-26), Y(98), hand_x, hand_y, color, 8 * u, alpha=alpha)
    cv.circle(hand_x, hand_y, 4.4 * u, fill=color, alpha=alpha)

    # --- меч
    if sword:
        tip_y = hand_y - 52 * u
        w_top, w_bot = 1.9 * u, 4.4 * u
        blade = skia.Path()
        blade.moveTo(hand_x - w_bot, hand_y)
        blade.lineTo(hand_x + w_bot, hand_y)
        blade.lineTo(hand_x + w_top, tip_y + 6 * u)
        blade.lineTo(hand_x, tip_y)
        blade.lineTo(hand_x - w_top, tip_y + 6 * u)
        blade.close()
        cv.path(blade, fill="#eef3f9", alpha=alpha)
        cv.line(hand_x - 0.4 * u, hand_y, hand_x - 0.4 * u, tip_y + 8 * u,
                "#ffffff", 1.4 * u, alpha=0.7 * alpha)
        # гарда
        cv.line(hand_x - 8 * u, hand_y + 1 * u, hand_x + 8 * u, hand_y + 1 * u,
                "#c9d3de", 3.2 * u, alpha=alpha)

    if detail:
        folds = skia.Path()
        for d in (-30, -18, -6, 8, 20, 32):
            folds.moveTo(X(d), Y(46))
            folds.lineTo(X(d * 1.5), Y(2))
        cv.c.drawPath(folds, _sp("#000000", 1.8 * u, int(46 * alpha)))
        # лицо: только тень, без черт
        cv.circle(X(1.6), Y(96), 4.6 * u, fill="#000000", alpha=0.10 * alpha)

    cv.restore()


def platform(cv, cx, base_y, w=250):
    cv.poly([(cx - w / 2, base_y), (cx + w / 2, base_y),
             (cx + w / 2 + 26, base_y + 46), (cx - w / 2 - 26, base_y + 46)],
            fill=lin(0, base_y, 0, base_y + 46, [(0, "#2c3a4b"), (1, "#131d29")]))


def label(cv, s, size, y, color=CREAM, x=540, glow=None, alpha=1.0, stroke=None, sw=0):
    cv.text(s, x, y, size, fill=color, center=True, glow=glow, alpha=alpha, stroke=stroke, stroke_w=sw)


# ---------- сцены ----------

def scene_hook(cv, t, ctx):
    k = k_of(ctx, t, (0, 7))
    cv.c.drawImage(static_bg(), 0, 0)
    cv.save()
    cv.zoom(1.04 + 0.30 * ease(k), 540, 1200)
    statue(cv, 540 + 8 * math.sin(t * 0.9), BASE - 20, 640, phase=t * 1.1, sway=9, detail=True)
    cv.restore()
    platform(cv, 540, BASE - 40, 260)

    # ветровые штрихи
    for i in range(9):
        yy = 480 + i * 96
        dx = ((t * 520 + i * 130) % 1400) - 200
        cv.line(dx, yy, dx + 150, yy - 10, "#9fc4e0", 2.2, alpha=0.16)
    # блик-свип и пыль с первого кадра
    sw_x = ((t * 700) % 1600) - 260
    cv.poly([(sw_x, 0), (sw_x + 80, 0), (sw_x + 260, H), (sw_x + 180, H)],
            fill="#ffe9b0", alpha=0.05)
    for i in range(14):
        px = ((i * 137 + t * 300) % (W + 100)) - 50
        py = 900 + ((i * 211 + t * 90) % 620)
        cv.circle(px, py, 2.0, fill="#cfe4f7", alpha=0.25)

    if k > 0.12:
        a = ease((k - 0.12) / 0.25)
        cv.text("85", 540, 300, 250, fill="#ffffff", center=True,
                stroke="#0a1420", stroke_w=16, glow=(GOLD, 30), alpha=a)
        label(cv, "МЕТРОВ БЕТОНА, КОТОРЫЙ КАЧАЕТСЯ", 38, 366, "#ffd479", alpha=a,
              stroke="#0a1420", sw=8)


def scene_build(cv, t, ctx):
    k = k_of(ctx, t, (7, 18))
    cv.c.drawImage(static_bg(), 0, 0)
    cv.save()
    cv.zoom(1.04 + 0.18 * ease(k), 540, 1000)
    platform(cv, 540, BASE - 40, 260)

    h_full = 640
    base_y = BASE - 40
    poured = base_y - h_full * ease(k / 0.85)

    # лёгкий контур будущей фигуры
    statue(cv, 540, base_y, h_full, phase=t * 0.5, sway=2, detail=False,
           alpha=0.22, color="#7e8d9e")

    # залитая часть — плотная
    cv.save()
    cv.c.clipRect(skia.Rect(0, poured, W, base_y + 10))
    statue(cv, 540, base_y, h_full, phase=t * 0.5, sway=2, detail=False,
           alpha=0.92, color="#aab6c3")
    cv.restore()
    cv.line(430, poured, 650, poured, "#ffffff", 3, alpha=0.7)

    # леса: стойки, диагонали, настилы — вокруг фигуры, не «штрих-код»
    left, right = 400, 690
    scaf = skia.Path()
    for x in (left, left + 34, right - 34, right):
        scaf.moveTo(x, base_y)
        scaf.lineTo(x, poured - 90)
    levels = 6
    for i in range(levels):
        y = base_y - (base_y - (poured - 90)) * (i + 1) / (levels + 1)
        scaf.moveTo(left - 20, y)
        scaf.lineTo(right + 20, y)
        if i % 2 == 0:
            scaf.moveTo(left - 20, y)
            scaf.lineTo(right + 20, y + 58)
        else:
            scaf.moveTo(right + 20, y)
            scaf.lineTo(left - 20, y + 58)
    cv.c.drawPath(scaf, _sp("#5f7285", 2.4, 190))

    # кран справа
    cx = 830
    cv.line(cx, base_y, cx, base_y - 560, "#54677a", 6)
    cv.line(cx - 210, base_y - 540, cx + 120, base_y - 540, "#54677a", 5)
    cv.line(cx + 120, base_y - 540, cx + 120, base_y - 470, "#54677a", 3)
    cv.line(cx, base_y - 560, cx - 160, base_y - 540, "#54677a", 3)
    cv.circle(cx + 120, base_y - 462, 12, fill="#54677a")
    cv.poly([(cx - 40, base_y), (cx + 40, base_y), (cx + 26, base_y - 34), (cx - 26, base_y - 34)], fill="#42566a")
    cv.line(cx + 120, base_y - 462, cx + 120, base_y - 360, "#54677a", 2.5)
    cv.line(cx + 104, base_y - 360, cx + 136, base_y - 360, "#54677a", 3)

    cv.restore()
    # струя бетона из крюка
    if 0.08 < k < 0.9:
        hx, hy = cx + 120, base_y - 360
        off = 14 * math.sin(t * 4)
        cv.line(hx, hy, hx + off, hy + 120, "#cfd8e2", 7, alpha=0.55)
        cv.circle(hx + off, hy + 130, 8, fill="#e6eef6", alpha=0.5)
    if k > 0.1:
        a = ease((k - 0.1) / 0.2)
        year = int(1959 + 8 * k)
        label(cv, str(year), 116, 340, "#ffffff", alpha=a, stroke="#0a1420", sw=10)
        label(cv, "СТРОИТЕЛЬСТВО МАМАЕВА КУРГАНА", 30, 398, "#9fc4e0", alpha=a)


def scene_sword(cv, t, ctx):
    k = k_of(ctx, t, (18, 28))
    cv.clear("#050a14")
    # меч крупным планом, качается
    ph = t * 2.2
    tilt = 6 * math.sin(ph)
    cv.save()
    cv.c.rotate(tilt, 540, 900)
    # рукоять
    cv.rrect(500, 1180, 580, 1450, 16, fill=lin(0, 1180, 0, 1450, [(0, "#9aa7b5"), (1, "#5d6a78")]))
    # клинок
    blade = skia.Path()
    blade.moveTo(512, 1180)
    blade.lineTo(568, 1180)
    blade.lineTo(552, 300)
    blade.lineTo(540, 220)
    blade.lineTo(528, 300)
    blade.close()
    cv.path(blade, fill=lin(0, 220, 0, 1180, [(0, "#ffffff"), (0.5, "#cfdae6"), (1, "#8f9dab")]))
    cv.path(blade, fill=lin(500, 0, 580, 0, [(0, "#00000030"), (0.45, "#ffffff20"), (1, "#00000055")]))
    cv.restore()
    # блик
    gx = ((t * 420) % 900) - 150
    cv.line(gx, 300, gx + 120, 1150, "#ffffff", 3, alpha=0.25)

    if k > 0.3:
        a = ease((k - 0.3) / 0.3)
        label(cv, "33 м", 96, 1560, "#ffffff", alpha=a, stroke="#0a1420", sw=10)
        label(cv, "14 ТОНН СТАЛИ", 44, 1620, "#ffd479", alpha=a)
    label(cv, "МЕЧ", 34, 200, "#9fc4e0", alpha=0.9)


def scene_core(cv, t, ctx):
    k = k_of(ctx, t, (21, 36))
    cv.clear("#060c16")
    if k < 0.45:
        kk = k / 0.45
        cv.save()
        cv.zoom(1.0 + 0.10 * ease(kk), 540, 900)
        shell_top, shell_bot = 260, 1500
        x0, x1 = 320, 760
        shell = skia.Path()
        shell.moveTo(x0 + 40, shell_top)
        shell.cubicTo(x0, shell_top + 300, x0 + 20, shell_bot - 300, x0 + 60, shell_bot)
        shell.lineTo(x1 - 60, shell_bot)
        shell.cubicTo(x1 - 20, shell_bot - 300, x1, shell_top + 300, x1 - 40, shell_top)
        shell.close()
        cv.path(shell, fill="#121d2b")
        cv.c.drawPath(shell, _sp("#7f8d9c", 4.0))
        ribs = skia.Path()
        for i in range(9):
            xx = x0 + 70 + i * 34
            ribs.moveTo(xx, shell_top + 40)
            ribs.lineTo(xx + 10, shell_bot - 30)
        cv.c.drawPath(ribs, _sp("#2f3f52", 3.0))
        # тросы с бегущим импульсом
        ten = skia.Path()
        for i in range(7):
            xx = x0 + 84 + i * 46
            ten.moveTo(xx, shell_bot - 40)
            ten.lineTo(xx + 6 * math.sin(t * 1.4 + i), shell_top + 46)
        cv.c.drawPath(ten, _sp(CYAN, 2.4, 170))
        pulse = skia.Path()
        for i in range(7):
            xx = x0 + 84 + i * 46
            p = (t * 0.9 + i * 0.13) % 1.0
            yy = shell_bot - 50 - p * (shell_bot - shell_top - 100)
            pulse.moveTo(xx - 7, yy)
            pulse.lineTo(xx + 7, yy)
        cv.c.drawPath(pulse, _sp("#ffffff", 5.0, 200))
        for i in range(7):
            cv.circle(x0 + 84 + i * 46, shell_bot - 40, 7, fill="#8fd8ff", alpha=0.85)
            cv.circle(x0 + 84 + i * 46, shell_top + 46, 6, fill="#8fd8ff", alpha=0.6)
        cv.restore()
        label(cv, "ПРЕДНАПРЯЖЁННЫЙ ЖЕЛЕЗОБЕТОН", 32, 210, "#9fc4e0", alpha=0.95)
        label(cv, "ТОНКАЯ ОБОЛОЧКА, РЁБРА, ТРОСЫ", 28, 1620, "#ffd479", alpha=0.9)
    else:
        kk = (k - 0.45) / 0.55
        # крупный план анкеров и натянутых тросов
        cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#08111c"), (1, "#0d1a28")]))
        cv.save()
        cv.c.translate(0, -40 * ease(kk))
        for i in range(6):
            x = 150 + i * 150
            cv.line(x, 300, x + 24 * math.sin(t * 1.2 + i), 1500, "#2b3b4f", 8)
            cv.line(x + 2, 300, x + 26 * math.sin(t * 1.2 + i), 1500, CYAN, 2.4, alpha=0.55)
            p = (t * 0.8 + i * 0.17) % 1.0
            yy = 1500 - p * 1200
            cv.circle(x + 24 * math.sin(t * 1.2 + i) * p, yy, 9, fill="#ffffff", alpha=0.85)
            cv.rrect(x - 34, 1480, x + 46, 1530, 8, fill="#233546")
            cv.rrect(x - 34, 262, x + 46, 306, 8, fill="#233546")
            cv.circle(x + 6, 1505, 10, fill=COOL if False else "#8fd8ff", alpha=0.9)
        cv.restore()
        label(cv, "ТРОСЫ РАБОТАЮТ НА РАСТЯЖЕНИЕ", 32, 240, "#ffd479", alpha=0.95)
        label(cv, "БЕТОН — НА СЖАТИЕ", 30, 1650, "#9fc4e0", alpha=0.9)


def scene_wind(cv, t, ctx):
    k = k_of(ctx, t, (39, 49))
    cv.c.drawImage(static_bg(), 0, 0)
    cv.save()
    cv.zoom(1.14 + 0.14 * ease(k), 540, 1100)
    statue(cv, 540, BASE - 40, 660, phase=t * 3.0, sway=38, detail=True)
    cv.restore()
    platform(cv, 540, BASE - 40, 240)

    # ветер: линии, пыль, трава
    for i in range(12):
        yy = 380 + i * 78
        dx = ((t * 1400 + i * 160) % 1500) - 260
        cv.line(dx, yy, dx + 190, yy - 14, "#a8cbe6", 2.6, alpha=0.20)
    for i in range(44):
        px = ((i * 97 + t * 1400) % (W + 120)) - 60
        py = 780 + ((i * 151 + t * 40) % 800)
        cv.circle(px, py, 1.8 + (i % 3) * 0.8, fill="#cfe4f7", alpha=0.22)
    for i in range(22):
        gx = 60 + i * 46
        sway_g = 8 * math.sin(t * 3.2 + i)
        cv.line(gx, BASE - 6, gx + sway_g, BASE - 44, "#2f4a3f", 2.2, alpha=0.5)
    # колебание: пунктир до вертикали
    ph = math.sin(t * 1.6) * 16
    cv.line(540, BASE - 700, 540, BASE - 40, "#ffd479", 1.5, alpha=0.25)
    cv.line(540 + ph, BASE - 700, 540 + ph, BASE - 40, "#ff8a5c", 2.0, alpha=0.35)

    if k > 0.2:
        a = ease((k - 0.2) / 0.3)
        label(cv, "ВЕТЕР РАСКАЧИВАЕТ 85 МЕТРОВ БЕТОНА", 32, 180, "#ffd479", alpha=a)
    if k > 0.55:
        a = ease((k - 0.55) / 0.3)
        label(cv, "ЗА КОЛЕБАНИЯМИ СЛЕДЯТ ДАТЧИКИ", 30, 1660, "#9fc4e0", alpha=a)


def shot_wide(cv, t, dawn=0.0):
    cv.rect(0, 0, W, HORIZON, fill=lin(0, 0, 0, HORIZON, [
        (0.0, "#050a14"), (0.4, mix("#0b1830", "#3a3f52", dawn)),
        (0.75, mix("#20304a", "#a06a58", dawn)), (1.0, mix("#33404f", "#f0b483", dawn))]))
    if dawn > 0.05:
        cv.circle(430, 1050, 260, fill="#ffd9a0", blur=90, alpha=0.35 * dawn)
    mound(cv, t)
    platform(cv, 540, BASE - 40, 300)
    statue(cv, 540, BASE - 40, 660, phase=t * 0.5, sway=4, detail=True,
           color=mix(STONE_D, "#fff2e0", dawn))


def scene_final(cv, t, ctx):
    k = k_of(ctx, t, (49, 58))
    if k < 0.45:
        kk = k / 0.45
        cv.save()
        cv.zoom(1.0 + 0.12 * ease(kk), 540, 1200)
        shot_wide(cv, t, dawn=0.25 * ease(kk))
        cv.restore()
    else:
        kk = (k - 0.45) / 0.55
        cv.save()
        cv.zoom(1.14 - 0.10 * ease(kk), 540, 1150)
        shot_wide(cv, t, dawn=1.0)
        cv.restore()
        cv.rect(0, 0, W, H, fill="#2a1a10", alpha=0.10)

    if k > 0.15:
        a = ease((k - 0.15) / 0.3)
        label(cv, "РОДИНА-МАТЬ ЗОВЁТ", 62, 300, "#ffffff", glow=(GOLD, 24), alpha=a,
              stroke="#160c00", sw=10)
    if k > 0.6:
        a = ease((k - 0.6) / 0.25)
        label(cv, "Волгоград · 1967", 36, 372, "#ffd479", alpha=a)


SCENES = {
    "hook": scene_hook,
    "build": scene_build,
    "sword": scene_sword,
    "core": scene_core,
    "wind": scene_wind,
    "final": scene_final,
}


def caption(cv, text, hl):
    if not text:
        return
    size = 54
    words = text.split()
    width = sum(cv.text_w(w + " ", size) for w in words)
    while width > 940 and size > 30:
        size -= 3
        width = sum(cv.text_w(w + " ", size) for w in words)
    x = 540 - width / 2
    base = 1790
    for w in words:
        col = "#ffd479" if any(h.lower() in w.lower() for h in hl) else "#f6f1e4"
        cv.text(w, x, base, size, fill=col, stroke="#050a12", stroke_w=7,
                shadow=(0, 4, 10, "#000000cc"))
        x += cv.text_w(w + " ", size)


def render(name, t, ctx=None, finish=False):
    ctx = ctx or {}
    cv = Canvas()
    cv.save()
    cv.c.translate(5 * math.sin(t * 0.6), 4 * math.cos(t * 0.45))
    SCENES[name](cv, t, ctx)
    cv.restore()
    caption(cv, ctx.get("caption_text", ""), ctx.get("caption_hl", ()))
    return cv.to_pil()
