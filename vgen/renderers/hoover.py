"""Плотина Гувера: почему её не залили одним куском. Рисунок на vgen.kit (Skia).

Сцены: hook (раскалённый монолит) → heat (гидратация, трещины) → blocks (блоки 1,5 м)
→ pipes (937 км труб, холодная вода) → grout (цементация швов) → final (вид с высоты).

Интерфейс: render(name, t, ctx) -> PIL.Image 1080x1920.
"""
import math

import skia

from vgen.kit import Canvas, W, H, lin, rad, rgba

SKY_TOP = "#050b16"
SKY_MID = "#0d1a2b"
SKY_LOW = "#2b3a4a"
ROCK = "#1a2430"
ROCK_LIT = "#2b3a48"
CONCRETE = "#b6c1cd"
CONCRETE_D = "#8794a3"
HOT = "#ff5a1e"
HOT_LIT = "#ffc04a"
COOL = "#5ec8ff"
CREAM = "#f4efe4"
GOLD = "#ffc45e"

HORIZON = 1430
BASE = 1560


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

def sky(cv, t):
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, HORIZON, [
        (0.0, SKY_TOP), (0.5, SKY_MID), (0.82, "#3c4a58"), (1.0, "#6b6250")]))
    cv.rect(0, 700, W, HORIZON, fill=rad(540, HORIZON - 120, 820, [
        (0.0, "#7c6a4e30"), (1.0, "#00000000")]))
    # редкие звёзды, медленно гаснут к «рассвету»
    for i in range(34):
        x = (i * 137.5) % W
        y = 80 + (i * 211) % 760
        a = 0.35 * (0.6 + 0.4 * math.sin(t * 0.9 + i))
        cv.circle(x, y, 1.2, fill="#d8e6ff", alpha=a)


def canyon(cv, t):
    """Скалы по краям кадра — три плана глубины."""
    far = skia.Path()
    far.moveTo(0, HORIZON - 260)
    for x in range(0, W + 40, 90):
        far.lineTo(x, HORIZON - 260 + 60 * math.sin(x * 0.011 + 1.2))
    far.lineTo(W, H)
    far.lineTo(0, H)
    far.close()
    cv.path(far, fill="#16202c")

    near = skia.Path()
    near.moveTo(0, HORIZON - 620)
    for x in range(0, 300, 40):
        near.lineTo(x, HORIZON - 620 + 70 * math.sin(x * 0.02))
    near.lineTo(210, H)
    near.lineTo(0, H)
    near.close()
    cv.path(near, fill=lin(0, 900, 300, H, [(0, "#212c38"), (1, "#0b121a")]))

    r = skia.Path()
    r.moveTo(W, HORIZON - 560)
    for x in range(W, W - 320, -40):
        r.lineTo(x, HORIZON - 560 + 90 * math.sin(x * 0.017 + 2.0))
    r.lineTo(W - 240, H)
    r.lineTo(W, H)
    r.close()
    cv.path(r, fill=lin(W, 900, W - 320, H, [(0, "#232e3a"), (1, "#0b121a")]))


def water(cv, t):
    top = 1700
    cv.rect(0, top, W, H, fill=lin(0, top, 0, H, [(0, "#17364d"), (1, "#0a1a26")]))
    p = skia.Path()
    for i in range(9):
        y = top + 16 + i * 22
        for x in range(0, W, 26):
            yy = y + 5 * math.sin((x + t * 120) * 0.02 + i)
            if x == 0:
                p.moveTo(x, yy)
            else:
                p.lineTo(x, yy)
    cv.path(p, stroke="#7fd2ff", width=1.4, alpha=0.275)


_BG = {}


def static_bg():
    """Небо, скалы и вода рисуем один раз на процесс: они почти не меняются."""
    if "img" not in _BG:
        c2 = Canvas()
        sky(c2, 0.0)
        canyon(c2, 0.0)
        water(c2, 0.0)
        _BG["img"] = c2.surface.makeImageSnapshot()
    return _BG["img"]


# ---------- плотина ----------

def dam_wall(cv, hot=0.0, alpha=1.0, detail=True, t=0.0, pipes=0.0, grout=0.0):
    """Стена плотины: трапеция в каньоне, внутри — температура/трубы."""
    top, bot = 980, BASE
    tl, tr = 300, 780
    bl, br = 240, 840
    wall = [(tl, top), (tr, top), (br, bot), (bl, bot)]
    base = mix(CONCRETE_D, CONCRETE, 0.5)
    cv.poly(wall, fill=base, alpha=alpha)
    # объём: световая кромка слева, тень справа
    cv.poly([(tl, top), (tl + 46, top), (bl + 40, bot), (bl, bot)], fill="#e6eef7", alpha=0.55 * alpha)
    cv.poly([(tr - 40, top), (tr, top), (br, bot), (br - 40, bot)], fill="#5b6675", alpha=0.5 * alpha)

    if hot > 0.01:
        # раскалённая масса внутри
        glow = skia.Path()
        glow.moveTo(tl + 20, top + 18)
        glow.lineTo(tr - 20, top + 18)
        glow.lineTo(br - 34, bot - 12)
        glow.lineTo(bl + 34, bot - 12)
        glow.close()
        cv.path(glow, fill=rad(540, 1250, 560, [
            (0.0, mix("#6a1a08", HOT_LIT, hot)),
            (0.45, HOT),
            (1.0, "#4a0f04")]), alpha=min(1.0, hot * 1.1) * alpha)
        # «кипящие» прожилки
        for i in range(7):
            y = 1050 + i * 62
            wob = 12 * math.sin(t * 2.2 + i)
            cv.line(tl + 40 - wob, y, tr - 40 + wob, y + 26, "#ffe08a", 2.2, blur=6, alpha=0.35 * hot * alpha)

    if detail:
        # бетонные блоки (сетка колонн) — пути, чтобы не плодить drawRect
        seams = skia.Path()
        x = tl + 60
        while x < tr - 40:
            seams.moveTo(x, top)
            seams.lineTo(x + 14, bot)
            x += 62
        for y in range(top + 34, bot - 8, 58):
            k = (y - top) / (bot - top)
            seams.moveTo(tl + 60 * k, y)
            seams.lineTo(tr - 60 * k, y)
        cv.c.drawPath(seams, _sp("#33404f", 1.6, int(110 * alpha)))

    if pipes > 0.01:
        p = skia.Path()
        for i, y in enumerate(range(top + 70, bot - 20, 74)):
            for j in range(4):
                xx = tl + 80 + j * 150
                yy = y + (i % 2) * 26
                p.moveTo(xx, yy)
                p.lineTo(xx + 86, yy + 18)
                p.lineTo(xx + 86, yy + 52)
                p.lineTo(xx + 150, yy + 70)
        cv.c.drawPath(p, _sp("#8ea6bd", 3.2, int(255 * min(1.0, pipes))))
        # вода в трубах бежит
        wtr = skia.Path()
        for i, y in enumerate(range(top + 70, bot - 20, 74)):
            for j in range(4):
                xx = tl + 80 + j * 150
                yy = y + (i % 2) * 26
                off = ((t * 130 + i * 37 + j * 21) % 90)
                wtr.moveTo(xx + off * 0.4, yy + off * 0.19)
                wtr.lineTo(xx + off * 0.4 + 12, yy + off * 0.19 + 4)
        cv.c.drawPath(wtr, _sp(COOL, 2.6, int(230 * min(1.0, pipes))))

    if grout > 0.01:
        g = skia.Path()
        for i, y in enumerate(range(top + 70, bot - 20, 74)):
            for j in range(4):
                xx = tl + 80 + j * 150
                yy = y + (i % 2) * 26
                g.moveTo(xx, yy)
                g.lineTo(xx + 86, yy + 18)
        cv.c.drawPath(g, _sp("#cfd8e2", 3.0, int(240 * min(1.0, grout))))


def label(cv, s, size, y, color=CREAM, x=540, glow=None, alpha=1.0, stroke=None, sw=0):
    cv.text(s, x, y, size, fill=color, center=True, glow=glow, alpha=alpha, stroke=stroke, stroke_w=sw)


# ---------- сцены ----------

def scene_hook(cv, t, ctx):
    k = k_of(ctx, t, (0, 6))
    cv.c.drawImage(static_bg(), 0, 0)
    # наезд камеры: стена приближается
    z = 1.02 + 0.55 * ease(k)
    cv.save()
    cv.zoom(z, 540, 1250)
    dam_wall(cv, hot=ease((k - 0.35) / 0.5), t=t, detail=False)
    cv.restore()
    # рентген: рамка «стена стала прозрачной»
    if k > 0.30:
        a = ease((k - 0.30) / 0.4)
        cv.rect(0, 880, W, 880 + 4, fill=COOL, alpha=0.25 * a)
        label(cv, "ВНУТРИ — РАСКАЛЁННЫЙ БЕТОН", 30, 930, "#9fd8ff", alpha=a)
    # блик-свип пересекает кадр ~ раз в 1,6 с
    sweep_x = ((t * 620) % 1500) - 200
    cv.poly([(sweep_x, 0), (sweep_x + 90, 0), (sweep_x + 300, H), (sweep_x + 210, H)],
            fill="#ffe9b0", alpha=0.05)

    # тепло идёт от стены: волны и пульсация с первого кадра
    shimmer = skia.Path()
    for i in range(9):
        yy = 1000 + i * 46
        dx = 16 * math.sin(t * 2.6 + i * 0.9)
        shimmer.moveTo(300 + dx, yy)
        shimmer.lineTo(780 + dx, yy + 10)
    cv.c.drawPath(shimmer, _sp("#ffb066", 2.0, int(120 * (0.35 + 0.65 * ease(k)))))

    # 125 ЛЕТ
    if k > 0.55:
        a = ease((k - 0.55) / 0.30)
        cv.text("125", 540, 640, 320, fill="#ffffff", center=True,
                stroke="#2a1400", stroke_w=14, glow=("#ff9a1f", 34), alpha=a)
        label(cv, "ЛЕТ ОСТЫВАНИЯ", 48, 716, "#ffd479", alpha=a,
              stroke="#170a00", sw=8)


def scene_heat(cv, t, ctx):
    k = k_of(ctx, t, (6, 14))
    cv.clear("#080e18")
    # разрез формы
    x0, x1, y0, y1 = 150, 930, 560, 1520
    cv.rrect(x0 - 18, y0 - 18, x1 + 18, y1 + 18, 10, fill="#131c28")
    hotk = ease(k / 0.75)
    cv.rect(x0, y0, x1, y1, fill=mix("#8d98a6", "#c8441a", hotk))
    # слой заливки сверху
    if k < 0.6:
        fill_h = (y1 - y0) * (0.15 + 0.85 * ease(k / 0.55))
        cv.rect(x0, y1 - fill_h, x1, y1, fill=mix("#b6c1cd", "#d9762c", hotk * 0.8))
        cv.rect(x0, y1 - fill_h, x1, y1 - fill_h + 8, fill="#e9f2fb", alpha=0.8)
    # струя бетона
    if k < 0.45:
        jw = 26 + 8 * math.sin(t * 9)
        cv.rect(520 - jw, 250, 520 + jw, y1 - 300, fill="#cfd8e2", alpha=0.85)
        cv.rect(520 - jw + 8, 250, 520 + jw - 8, y1 - 300, fill="#eef6ff", alpha=0.5)
    # тепловые волны
    for i in range(24):
        y = y0 + 30 + i * 38
        wob = 10 * math.sin(t * 3 + i * 0.7)
        cv.line(x0 + 24 + wob, y, x1 - 24 - wob, y + 8, "#ffd08a", 2,
                blur=8, alpha=0.30 * hotk)
    # трещины — появляются после прогрева
    if k > 0.55:
        a = ease((k - 0.55) / 0.35)
        path = skia.Path()
        for i in range(5):
            xx = x0 + 70 + i * 150
            path.moveTo(xx, y0 + 60)
            yy = y0 + 60
            while yy < y1 - 40:
                yy += 46
                xx += 18 * math.sin(yy * 0.05 + i)
                path.lineTo(xx, yy)
        cv.c.drawPath(path, _sp("#20140c", 3.4, int(230 * a)))
    # термометр
    cv.rrect(1000, 700, 1040, 1380, 18, fill="#101823")
    cv.rrect(1004, 700 + (1380 - 700) * (1 - hotk), 1036, 1376, 14,
             fill=lin(0, 700, 0, 1380, [(0, "#ff3b30"), (1, "#ffb347")]))
    label(cv, "гидратация цемента", 34, 520, "#8fd0ff", alpha=0.9)
    if k > 0.2:
        temp = int(20 + 55 * hotk)
        label(cv, "+%d°C" % temp, 84, 640, mix(CREAM, "#ff8a4a", hotk), x=880)
    label(cv, "ВНУТРИ МАССИВА", 30, 1600, "#7f8fa0", alpha=0.9)


def scene_blocks(cv, t, ctx):
    k = k_of(ctx, t, (14, 24))
    cv.clear("#080e18")
    sky(cv, t)
    canyon(cv, t)
    water(cv, t)
    top, bot = 640, 1500
    # монолит раскалывается → колонны блоков расходятся
    split = ease((k - 0.08) / 0.42)
    fade_mono = 1.0 - ease((k - 0.05) / 0.30)
    if fade_mono > 0.02:
        cv.poly([(240, top), (840, top), (860, bot), (220, bot)],
                fill="#aab5c2", alpha=fade_mono)
    cols, rows = 7, 9
    cw = 600.0 / cols
    ch = (bot - top) / rows
    for r in range(rows):
        for c in range(cols):
            x = 240 + c * cw + 8
            y = top + r * ch + 6
            # волна укладки: блоки появляются колоннами снизу вверх
            on = 0.30 + 0.70 * ease((k - 0.12 - c * 0.03 - r * 0.012) / 0.22)
            gap = 34 * (1 - split) * 0.6
            xx = x + (c - cols / 2) * gap
            warm = max(0.0, 0.55 - (k - 0.2) * 1.1 - r * 0.02)
            cv.rrect(xx, y, xx + cw - 14, y + ch - 12, 5,
                     fill=mix("#c3cdd8", "#ef7a3a", warm), alpha=on)
            cv.rrect(xx, y, xx + cw - 14, y + 3, 3, fill="#eef5fc", alpha=0.45 * on)
    # размер слоя 1,5 м
    if k > 0.45:
        a = ease((k - 0.45) / 0.3)
        y = top + 3 * ch
        cv.line(880, y, 980, y, "#ffd479", 2.4, alpha=a)
        cv.line(880, y + ch, 980, y + ch, "#ffd479", 2.4, alpha=a)
        cv.line(930, y, 930, y + ch, "#ffd479", 2.0, alpha=a)
        label(cv, "1,5 м", 34, y + ch * 0.6, "#ffd479", x=1010, alpha=a)
    label(cv, "ТЫСЯЧИ БЛОКОВ В КОЛОННАХ", 34, 520, "#a9c6e0", alpha=0.95)


def scene_pipes(cv, t, ctx):
    k = k_of(ctx, t, (24, 39))
    cv.clear("#050a12")
    x0, y0, x1, y1 = 80, 470, 1000, 1580
    cool = ease((k - 0.15) / 0.70)

    # бетон как полупрозрачная среда: трубы видны «внутри»
    cv.rrect(x0, y0, x1, y1, 16, fill=mix("#8a2f12", "#7f8b99", cool), alpha=0.55)
    cv.rrect(x0, y0, x1, y1, 16, fill=lin(0, y0, 0, y1, [
        (0, "#ffffff18"), (0.5, "#00000000"), (1, "#00000055")]))
    for i in range(160):
        xx = x0 + 20 + (i * 97) % (x1 - x0 - 40)
        yy = y0 + 20 + (i * 173) % (y1 - y0 - 40)
        cv.circle(xx, yy, 1.6, fill="#ffffff", alpha=0.06)

    rows = 11
    step = (y1 - y0 - 130) / rows
    shadow, body, light = skia.Path(), skia.Path(), skia.Path()
    for i in range(rows):
        y = y0 + 75 + i * step
        yy = y + (6 if i % 2 == 0 else -6)
        shadow.moveTo(x0 + 74, yy + 5)
        shadow.lineTo(x1 - 74, yy + 5)
        body.moveTo(x0 + 74, yy)
        body.lineTo(x1 - 74, yy)
        light.moveTo(x0 + 74, yy - 3)
        light.lineTo(x1 - 74, yy - 3)
    cv.c.drawPath(shadow, _sp("#000000", 20, 120))
    cv.c.drawPath(body, _sp("#c9d4e0", 16))
    cv.c.drawPath(light, _sp("#ffffff", 5, 150))

    for direction in (1, -1):
        flow = skia.Path()
        for i in range(rows):
            y = y0 + 75 + i * step + (6 if i % 2 == 0 else -6)
            for j in range(6):
                span = x1 - x0 - 160
                off = (t * 300 * direction + j * 160 + i * 90) % span
                xx = x0 + 80 + off
                flow.moveTo(xx, y)
                flow.lineTo(xx + 40, y)
        cv.c.drawPath(flow, _sp(COOL, 7, 200))

    # торец разреза: толщина бетона и торцы труб с холодной водой
    cv.poly([(x1, y0 + 10), (x1 + 58, y0 + 40), (x1 + 58, y1 - 20), (x1, y1 - 10)],
            fill=lin(x1, y0, x1 + 58, y0, [(0, "#8d99a6"), (1, "#4c5865")]))
    cv.poly([(x1, y0 + 10), (x1 + 18, y0 + 20), (x1 + 18, y1 - 14), (x1, y1 - 10)],
            fill="#aeb9c6", alpha=0.8)
    for i in range(rows):
        y = y0 + 75 + i * step + (6 if i % 2 == 0 else -6)
        cv.oval(x1 + 6, y - 11, x1 + 42, y + 11, fill="#d7e2ee")
        cv.oval(x1 + 11, y - 8, x1 + 37, y + 8, fill="#1a2632")
        cv.oval(x1 + 15, y - 5, x1 + 33, y + 5, fill=COOL, alpha=0.9)
    cv.rrect(x0, y0, x1, y1, 16, stroke="#dbe6f2", width=3, alpha=0.75)
    hatch = skia.Path()
    for i in range(26):
        yy = y0 + 8 + i * 42
        hatch.moveTo(x0 - 2, yy)
        hatch.lineTo(x0 + 26, yy + 22)
        hatch.moveTo(x1 + 2, yy)
        hatch.lineTo(x1 - 26, yy + 22)
    cv.c.drawPath(hatch, _sp("#9fb2c6", 2.0, 90))

    for i in range(9):
        yy = y0 + 120 + i * 120
        cv.circle(x0 + 14, yy, 10 + 5 * math.sin(t * 1.8 + i), fill="#bfe9ff", alpha=0.28)
        cv.circle(x1 - 14, yy, 10 + 5 * math.sin(t * 1.8 + i + 1.6), fill="#bfe9ff", alpha=0.28)

    cv.text("вода из реки →", x0 + 30, y0 - 40, 30, fill="#9fd8ff", alpha=0.95)
    cv.text("← ледяная вода", x1 - 30, y0 - 40, 30, fill="#9fd8ff", alpha=0.95, center=True)

    if k > 0.5:
        a = ease((k - 0.5) / 0.32)
        cv.rrect(110, 1610, 970, 1780, 16, fill="#0d1a26", alpha=a)
        cv.rrect(110, 1610, 970, 1780, 16, stroke=COOL, width=2, alpha=0.4 * a)
        for i in range(4):
            cv.circle(190 + i * 66, 1695, 24, fill="#16324a", alpha=a)
            cv.circle(190 + i * 66, 1695, 13 + 4 * math.sin(t * 4 + i), fill=COOL, alpha=0.85 * a)
        cv.text("холодильная установка", 490, 1678, 30, fill="#9fd8ff", alpha=a, center=True)
        cv.text("1000 т льда в сутки", 490, 1738, 36, fill=CREAM, alpha=a, center=True)

    label(cv, "937 КМ ТРУБ ВНУТРИ БЕТОНА", 40, 400, "#bfe9ff", glow=(COOL, 18), alpha=0.95)
    label(cv, "РАЗРЕЗ БЛОКА", 28, 1638, "#7f93a8", alpha=0.9)


def scene_grout(cv, t, ctx):
    k = k_of(ctx, t, (39, 49))
    cv.clear("#060c14")
    cv.c.drawImage(static_bg(), 0, 0)
    top, bot = 940, BASE
    tl, tr, bl, br = 300, 780, 240, 840

    wall = [(tl, top), (tr, top), (br, bot), (bl, bot)]
    cv.poly(wall, fill=mix("#c8d3df", "#aab6c3", 0.5))
    cv.poly([(tl, top), (tl + 40, top), (bl + 34, bot), (bl, bot)], fill="#e9f1f8", alpha=0.6)

    cols, rows = 6, 7
    cw = (tr - tl) / cols
    ch = (bot - top) / rows
    gaps = skia.Path()
    for c in range(cols + 1):
        x = tl + c * cw
        gaps.moveTo(x, top)
        gaps.lineTo(x, bot)
    for r in range(rows + 1):
        y = top + r * ch
        gaps.moveTo(tl, y)
        gaps.lineTo(tr, y)
    cv.c.drawPath(gaps, _sp("#3d4a58", 4.0, 200))

    fill = skia.Path()
    for r in range(rows):
        level = max(0.0, min(1.0, (k * 1.25 - r * 0.06)))
        if level <= 0:
            continue
        for c in range(cols):
            x = tl + c * cw
            fill.moveTo(x + 2, bot - (r + 1) * ch + ch * (1 - level))
            fill.lineTo(x + 2, bot - r * ch)
            fill.moveTo(x, bot - (r + 1) * ch + ch * (1 - level))
            fill.lineTo(x + cw, bot - (r + 1) * ch + ch * (1 - level))
    cv.c.drawPath(fill, _sp("#ffd479", 3.4, 210))

    if k > 0.45:
        a = ease((k - 0.45) / 0.4)
        g = skia.Path()
        for r in range(rows):
            for c in range(cols):
                x = tl + c * cw + cw * 0.25
                y = top + r * ch + ch * 0.5
                g.moveTo(x, y)
                g.lineTo(x + cw * 0.5, y + 6)
        cv.c.drawPath(g, _sp("#eef4fa", 3.0, int(220 * a)))

    if k > 0.25:
        a = ease((k - 0.25) / 0.35)
        label(cv, "ШВЫ ЗАПОЛНЯЮТ РАСТВОРОМ", 34, 880, "#ffd479", alpha=a)
    if k > 0.62:
        a = ease((k - 0.62) / 0.3)
        label(cv, "ОДНА ПЛОТИНА", 92, 820, "#ffffff", glow=(GOLD, 24), alpha=a,
              stroke="#1a1000", sw=10)


def shot_aerial(cv, t, k):
    """Общий план: водохранилище, плотина, солнце."""
    cv.rect(0, 0, W, 900, fill=lin(0, 0, 0, 900, [
        (0, "#0a1a2e"), (0.55, "#2c4056"), (1, "#c98a5a")]))
    cv.circle(240, 300, 90, fill="#ffe0a8", blur=48, alpha=0.5)
    cv.circle(240, 300, 40, fill="#fff4d8", blur=12, alpha=0.9)
    for side in (-1, 1):
        pth = skia.Path()
        base_x = 0 if side < 0 else W
        pth.moveTo(base_x, 380)
        for i in range(6):
            xx = base_x + side * (60 + i * 42)
            pth.lineTo(xx, 380 + i * 40 + 20 * math.sin(i * 1.7))
        pth.lineTo(base_x + side * 300, H)
        pth.lineTo(base_x, H)
        pth.close()
        cv.path(pth, fill=lin(base_x, 380, base_x + side * 300, H,
                              [(0, "#2c3745"), (1, "#0a1018")]))
    cv.rect(180, 560, 900, 900, fill=lin(0, 560, 0, 900, [(0, "#123c5c"), (1, "#1f5c80")]))
    cv.rect(180, 560, 900, 900, fill=rad(540, 700, 420, [(0, "#4aa3cf55"), (1, "#00000000")]))
    body = [(300, 900), (780, 900), (860, 1180), (220, 1180)]
    cv.poly(body, fill=lin(0, 900, 0, 1180, [(0, "#eef4fa"), (0.5, "#c6d1dc"), (1, "#8d9aa6")]))
    cv.poly([(300, 900), (780, 900), (800, 940), (280, 940)], fill="#ffffff")
    for i in range(5):
        x = 330 + i * 105
        cv.rrect(x, 830, x + 34, 905, 6, fill="#dfe8f1")
        cv.rrect(x + 6, 812, x + 28, 836, 4, fill="#c3cfdb")
    for i in range(16):
        x = 330 + i * 26
        cv.line(x, 1180, x + 8, 1330 + 40 * math.sin(t * 1.8 + i), "#e8f6ff", 5, alpha=0.35)
    cv.rect(160, 1170, 920, 1210, fill="#ffffff", alpha=0.25, blur=18)
    cv.rect(0, 1200, W, H, fill=lin(0, 1200, 0, H, [(0, "#16405a"), (1, "#05121c")]))
    for i in range(8):
        yy = 1240 + i * 46
        dx = 26 * math.sin(t * 1.7 + i * 0.8)
        cv.line(-40 + dx, yy, W + 40 + dx, yy, "#9fd8ff",
                7 - i * 0.6, alpha=0.14)


def shot_crest(cv, t, k):
    """Крупный план гребня: башни, сброс воды, водяная пыль."""
    cv.rect(0, 0, W, H, fill=lin(0, 0, 0, H, [(0, "#0a1622"), (1, "#1d3346")]))
    cv.circle(180, 260, 220, fill="#ffd9a0", blur=120, alpha=0.35)
    # гребень крупно
    cv.poly([(-60, 900), (1140, 900), (1140, 1120), (-60, 1120)],
            fill=lin(0, 900, 0, 1120, [(0, "#f2f7fc"), (0.6, "#c8d3de"), (1, "#7f8b97")]))
    cv.rect(-60, 880, 1140, 906, fill="#ffffff")
    for i in range(4):
        x = 90 + i * 270
        cv.rrect(x, 700, x + 96, 910, 10, fill="#e4ecf4")
        cv.rrect(x + 14, 660, x + 82, 712, 8, fill="#cfdae5")
        cv.rrect(x + 30, 600, x + 66, 664, 6, fill="#b9c6d3")
    # вода льётся вниз
    for i in range(16):
        x = 40 + i * 64 + 6 * math.sin(t * 3 + i)
        cv.line(x, 1120, x + 6, 1600 + 120 * math.sin(t * 2.2 + i * 0.7), "#eaf8ff",
                6 - i * 0.08, alpha=0.28)
    # пыль
    for i in range(16):
        px = (i * 137 + t * 240) % W
        py = 1180 + ((i * 211 + t * 520) % 700)
        cv.circle(px, py, 2 + (i % 3), fill="#ffffff", alpha=0.18)
    cv.rect(0, 1560, W, H, fill=lin(0, 1560, 0, H, [(0, "#0d2c40"), (1, "#05121c")]))
    for i in range(10):
        yy = 1600 + i * 30
        cv.line(0, yy, W, yy + 6 * math.sin(t * 2 + i), "#9fd8ff", 5, alpha=0.10)


def scene_final(cv, t, ctx):
    k = k_of(ctx, t, (49, 60))
    cv.clear("#04080f")
    if k < 0.34:
        cv.save()
        cv.zoom(1.0 + 0.16 * ease(k / 0.34), 540, 1000)
        cv.c.translate(24 * math.sin(t * 0.6), 12 * math.cos(t * 0.45))
        shot_aerial(cv, t, k)
        cv.restore()
    elif k < 0.70:
        kk = (k - 0.34) / 0.36
        cv.save()
        cv.zoom(1.18 - 0.14 * ease(kk), 540, 950)
        cv.c.translate(30 * math.sin(t * 0.9), 0)
        shot_crest(cv, t, kk)
        cv.restore()
    else:
        kk = (k - 0.70) / 0.30
        cv.save()
        cv.zoom(1.16 - 0.10 * ease(kk), 540, 1000)
        shot_aerial(cv, t, kk)
        cv.restore()
        cv.rect(0, 1000, W, H, fill="#04080f", alpha=0.25)

    if k > 0.2:
        a = ease((k - 0.2) / 0.3)
        label(cv, "ИНЖЕНЕРИЯ ПОБЕДИЛА ТЕПЛО", 52, 470, "#ffffff",
              glow=(GOLD, 22), alpha=a, stroke="#160c00", sw=9)
    if k > 0.72:
        a = ease((k - 0.72) / 0.22)
        label(cv, "март 1935 · Плотина Гувера", 36, 548, "#ffd479", alpha=a)


SCENES = {
    "hook": scene_hook,
    "heat": scene_heat,
    "blocks": scene_blocks,
    "pipes": scene_pipes,
    "grout": scene_grout,
    "final": scene_final,
}


def caption(cv, text, hl):
    """Крупный субтитр с подсветкой ключевого слова."""
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
        col = "#ffd479" if any(h.lower() in w.lower() for h in hl) else "#f4efe4"
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
