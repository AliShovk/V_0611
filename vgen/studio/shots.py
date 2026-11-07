"""Типы сцен (shots). Каждый: fn(cv, ctx) — рисует контент сцены поверх фона.

hook · stat · compare · steps · flow · chart · callout · outro
Раскладка 1080x1920: шапка 40–150, заголовок ~330, контент 400–1560, субтитры 1600–1760.
"""
import math
import re

from vgen.kit import lin, rad
from vgen.studio.icons import draw_icon

CREAM = "#fff1c4"
MUTED = "#c3d2ea"


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def ease_out(k):
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


def pop(p):
    return 0.86 + 0.14 * p + 0.04 * math.sin(p * math.pi)


def fmt(v, dec=0):
    return f"{v:,.{dec}f}".replace(",", " ").replace(".", ",")


class Ctx:
    def __init__(self, t, sc, th, theme_name):
        self.t, self.sc, self.th, self.theme = t, sc, th, theme_name
        self.t0, self.t1 = sc["_t0"], sc["_t1"]
        self.st, self.dur = t - self.t0, max(0.1, self.t1 - self.t0)

    def p(self, at, dur=0.45):
        return ease((self.t - at) / dur)


# --- текст --------------------------------------------------------------------

def wrap(cv, text, size, max_w):
    lines, cur = [], ""
    text = re.sub(r"(\d) (?=\d{3}\b)", "\\1\u00a0", text)       # «300 000» не рвём переносом
    for w in text.split(" "):
        trial = (cur + " " + w).strip()
        if cv.text_w(trial, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def fit(cv, text, max_w, size, min_size=38, max_lines=2, one_line_min=None):
    if one_line_min:                       # сначала пробуем уместить в одну строку
        s = size
        while s >= one_line_min:
            if cv.text_w(text, s) <= max_w:
                return s, [text]
            s -= 4
    s = size
    while s > min_size:
        ls = wrap(cv, text, s, max_w)
        if len(ls) <= max_lines and all(cv.text_w(l, s) <= max_w for l in ls):
            return s, ls
        s -= 4
    return min_size, wrap(cv, text, min_size, max_w)


def heading(cv, ctx, text, y=330, size=76, max_w=960, color=CREAM):
    p = ctx.p(ctx.t0 + 0.05, 0.4)
    if p <= 0:
        return y
    s, lines = fit(cv, text, max_w, size)
    for i, l in enumerate(lines):
        cv.text(l, 540, y + i * s * 1.08 + (1 - p) * 22, s, fill=color, stroke=ctx.th["ink"], stroke_w=s * 0.16,
                center=True, shadow=(0, 6, 8, "#000b"), alpha=p)
    return y + len(lines) * s * 1.08


def note(cv, ctx, text, y, at, size=44, max_w=900, color=MUTED):
    p = ctx.p(at, 0.5)
    if p <= 0 or not text:
        return
    for i, l in enumerate(wrap(cv, text, size, max_w)[:3]):
        cv.text(l, 540, y + i * size * 1.25 + (1 - p) * 14, size, fill=color, center=True, alpha=p,
                stroke=ctx.th["ink"], stroke_w=size * 0.2)


def pill(cv, ctx, text, y, p, size=52, color=None):
    color = color or ctx.th["accent"]
    tw = cv.text_w(text, size)
    y = y + (1 - p) * 18
    cv.rrect(540 - tw / 2 - 34, y - size - 6, 540 + tw / 2 + 34, y + 22, 20, fill="#08101e", alpha=0.78 * p)
    cv.rrect(540 - tw / 2 - 34, y - size - 6, 540 + tw / 2 + 34, y + 22, 20, stroke=color, width=3, alpha=p)
    cv.text(text, 540, y, size, fill="#e6f8ff", center=True, alpha=p)


def hero(cv, ctx, name, cx, cy, size, bob=14):
    if not name:
        return
    p = ctx.p(ctx.t0 + 0.1, 0.6)
    if p <= 0:
        return
    cv.save()
    cv.zoom(0.7 + 0.3 * ease_out((ctx.t - ctx.t0 - 0.1) / 0.6), cx, cy)
    draw_icon(cv, name, cx, cy + bob * math.sin(ctx.t * 1.6), size, ctx.t, ctx.th["accent"], ctx.th["accent2"])
    cv.restore()


# --- шоты ---------------------------------------------------------------------

def hook(cv, ctx):
    sc, th = ctx.sc, ctx.th
    a = ctx.p(ctx.t0 + 0.15, 0.45)
    if a > 0:
        s, lines = fit(cv, sc["title"], 980, sc.get("size", 200), min_size=90, max_lines=2, one_line_min=140)
        cv.save()
        cv.zoom(pop(a), 540, 360)
        for i, l in enumerate(lines):
            y = 380 + i * s * 1.02
            cv.text(l, 540, y, s, fill=lin(0, y - s, 0, y + 10, [(0, "#fffbe6"), (0.55, "#ffd77a"), (1, th["accent2"])]),
                    stroke=th["ink"], stroke_w=s * 0.09, center=True, glow=(th["warm"], 26),
                    shadow=(0, 8, 10, "#000c"), alpha=a)
        cv.restore()
        yb = 380 + len(lines) * s * 1.02
    else:
        yb = 600
    if sc.get("subtitle"):
        pill(cv, ctx, sc["subtitle"], yb + 70, ctx.p(ctx.t0 + 0.55, 0.5), 52, th["accent"])
    hero(cv, ctx, sc.get("icon"), 540, 1130, sc.get("icon_size", 600))


def stat(cv, ctx):
    sc, th = ctx.sc, ctx.th
    heading(cv, ctx, sc["title"], 330, 68)
    hero(cv, ctx, sc.get("icon"), 540, 760, 400)
    vt = sc["_vt"]
    k = ease_out((ctx.t - vt) / 0.65)
    v = float(sc["value"]) * k
    dec = sc.get("decimals", 0)
    txt = (sc.get("prefix", "") + fmt(v, dec) + sc.get("suffix", ""))
    full = sc.get("prefix", "") + fmt(float(sc["value"]), dec) + sc.get("suffix", "")
    size = 300
    while cv.text_w(full, size) > 940 and size > 90:
        size -= 6
    p = ctx.p(vt - 0.1, 0.3)
    if p > 0:
        bump = 1 + 0.06 * math.sin(min(1.0, max(0.0, (ctx.t - vt - 1.2) / 0.35)) * math.pi)
        cv.save()
        cv.zoom(bump, 540, 1100)
        cv.text(txt, 540, 1160, size, fill=lin(0, 1160 - size, 0, 1160, [(0, "#fffbe6"), (1, th["accent2"])]),
                stroke=th["ink"], stroke_w=size * 0.07, center=True, glow=(th["warm"], 30),
                shadow=(0, 10, 12, "#000c"), alpha=p)
        cv.restore()
    if sc.get("unit"):
        a = ctx.p(vt + 0.2, 0.5)
        if a > 0:
            us = 74
            while cv.text_w(sc["unit"], us) > 940 and us > 36:
                us -= 2
            cv.text(sc["unit"], 540, 1270 + (1 - a) * 14, us, fill=th["accent"], center=True, alpha=a,
                    stroke=th["ink"], stroke_w=10)
    note(cv, ctx, sc.get("note", ""), 1380, vt + 0.9)


def compare(cv, ctx):
    sc, th = ctx.sc, ctx.th
    items = sc["items"]
    n = len(items)
    heading(cv, ctx, sc["title"], 330, 68)
    base, maxh = 1400, 560
    bw = 300 if n == 2 else 250
    gap = 70 if n == 2 else 40
    x0 = 540 - (n * bw + (n - 1) * gap) / 2
    vmax = max(float(i["value"]) for i in items)
    cols = [th["accent"], th["accent2"], th["warm"]]
    cv.line(60, base + 2, 1020, base + 2, "#ffffff", 3, alpha=0.35)
    for j, it in enumerate(items):
        k = ease_out((ctx.t - it["_t"]) / 1.1)
        if k <= 0:
            continue
        x = x0 + j * (bw + gap)
        h = max(14, maxh * float(it["value"]) / vmax) * k
        c = cols[j % 3]
        cv.rrect(x, base - h, x + bw, base + 4, 22, fill=lin(0, base - h, 0, base, [(0, c), (1, c + "b0")]),
                 shadow=(0, 8, 14, "#000b"))
        cv.rrect(x, base - h, x + bw, base - h + 14, 7, fill="#ffffff", alpha=0.35)
        cv.rrect(x - 4, base - h - 4, x + bw + 4, base + 8, 24, stroke=c, width=6, blur=10, alpha=0.45)
        v = float(it["value"]) * k
        txt = fmt(v, it.get("decimals", 0)) + (" " + it["unit"] if it.get("unit") else "")
        s = 78
        while cv.text_w(txt, s) > bw + gap - 10 and s > 40:
            s -= 4
        cv.text(txt, x + bw / 2, base - h - 28, s, fill="#fff", stroke=th["ink"], stroke_w=10, center=True)
        if it.get("icon"):
            draw_icon(cv, it["icon"], x + bw / 2, base - h - 28 - s - 100, 170, ctx.t, th["accent"], th["accent2"])
        sz, ls = fit(cv, it["label"], bw + gap - 6, 46, 30, 2)
        for i, l in enumerate(ls):
            cv.text(l, x + bw / 2, base + 70 + i * sz * 1.15, sz, fill=CREAM, center=True, alpha=k)
    if sc.get("badge"):
        a = ctx.p(max(i["_t"] for i in items) + 1.0, 0.45)
        if a > 0:
            bx, by, bs = x0 + bw / 2, base - maxh * 0.62, 104   # над низкой колонкой — там пусто
            cv.save()
            cv.zoom(pop(a), bx, by)
            tw = cv.text_w(sc["badge"], bs)
            cv.rrect(bx - tw / 2 - 36, by - bs - 6, bx + tw / 2 + 36, by + 26, 34, fill="#0b1220", alpha=0.9 * a,
                     shadow=(0, 8, 14, "#000a"))
            cv.rrect(bx - tw / 2 - 36, by - bs - 6, bx + tw / 2 + 36, by + 26, 34, stroke=th["accent2"], width=5, alpha=a)
            cv.text(sc["badge"], bx, by, bs, fill=th["accent2"], center=True, glow=(th["warm"], 16), alpha=a)
            cv.restore()


def steps(cv, ctx):
    sc, th = ctx.sc, ctx.th
    st = sc["steps"]
    n = len(st)
    heading(cv, ctx, sc["title"], 330, 68)
    ch, gap = 210, 26
    y0 = 430 + (1130 - (n * ch + (n - 1) * gap)) / 2
    latest = max([i for i, s in enumerate(st) if ctx.t >= s["_t"]], default=-1)
    for i, s in enumerate(st):
        p = ctx.p(s["_t"], 0.5)
        if p <= 0:
            continue
        y = y0 + i * (ch + gap)
        dx = (1 - ease_out(p)) * 220
        act = i == latest
        cv.card(60 + dx, y, 1020 + dx, y + ch, th["accent2"] if act else th["accent"], 28, 0.88, glow=act, a=p)
        cv.circle(170 + dx, y + ch / 2, 70, fill=lin(0, y, 0, y + ch, [(0, "#1d3358"), (1, "#0b1424")]), alpha=p)
        cv.circle(170 + dx, y + ch / 2, 70, stroke=th["accent"], width=3, alpha=p)
        if s.get("icon"):
            draw_icon(cv, s["icon"], 170 + dx, y + ch / 2, 104, ctx.t, th["accent"], th["accent2"], halo=False)
        else:
            cv.text(str(i + 1), 170 + dx, y + ch / 2 + 28, 84, fill=th["accent2"], center=True)
        sz, ls = fit(cv, s["title"], 640, 52, 34, 2)
        ty = y + (ch / 2 + 16 if not s.get("sub") else 80) - (sz * 0.6 if len(ls) > 1 and not s.get("sub") else 0)
        for k2, l in enumerate(ls):
            cv.text(l, 290 + dx, ty + k2 * sz * 1.1, sz, fill="#fff", alpha=p)
        if s.get("sub"):
            for k2, l in enumerate(wrap(cv, s["sub"], 34, 660)[:2]):
                cv.text(l, 290 + dx, y + 80 + len(ls) * sz * 1.05 + k2 * 40, 34, fill=MUTED, alpha=p)
        if i < n - 1 and ctx.t >= st[i + 1]["_t"] - 0.1:
            kk = ease((ctx.t - st[i + 1]["_t"] + 0.1) / 0.4)
            cv.line(170, y + ch - 2, 170, y + ch + gap * kk + 2, th["accent"], 6, alpha=0.8)


def flow(cv, ctx):
    sc, th = ctx.sc, ctx.th
    nodes = sc["nodes"]
    n = len(nodes)
    heading(cv, ctx, sc["title"], 330, 68)
    xs = [300, 780] if n == 2 else [190, 540, 890]
    r = 170 if n == 2 else 128
    cy = 900
    for i in range(n - 1):
        t_arr = nodes[i + 1]["_t"] - 0.15
        k = ease((ctx.t - t_arr) / 0.5)
        if k > 0:
            xa, xb = xs[i] + r + 18, xs[i + 1] - r - 18
            xe = xa + (xb - xa) * k
            cv.line(xa, cy, xe, cy, th["accent2"], 10, alpha=0.9)
            cv.poly([(xe, cy - 22), (xe + 34, cy), (xe, cy + 22)], fill=th["accent2"], alpha=min(1.0, k * 2))
            for d in range(3):
                px = xa + ((ctx.t * 0.6 + d / 3) % 1) * (xe - xa)
                cv.circle(px, cy, 7, fill="#fff", alpha=0.85)
    for i, nd in enumerate(nodes):
        p = ctx.p(nd["_t"], 0.5)
        if p <= 0:
            continue
        cx = xs[i]
        cv.save()
        cv.zoom(pop(p), cx, cy)
        cv.circle(cx, cy, r, fill=lin(0, cy - r, 0, cy + r, [(0, "#1c3158"), (1, "#0a1224")]), shadow=(0, 10, 16, "#000b"), alpha=p)
        cv.circle(cx, cy, r, stroke=th["accent"], width=4, alpha=p)
        cv.circle(cx, cy, r, stroke=th["accent"], width=10, blur=12, alpha=0.4 * p)
        draw_icon(cv, nd.get("icon", "gear"), cx, cy, r * 1.25, ctx.t, th["accent"], th["accent2"], halo=False)
        cv.restore()
        sz, ls = fit(cv, nd["label"], 2 * r + 30, 48, 30, 2)
        for k2, l in enumerate(ls):
            cv.text(l, cx, cy + r + 80 + k2 * sz * 1.15, sz, fill=CREAM, center=True, alpha=p)
    note(cv, ctx, sc.get("note", ""), 1380, nodes[-1]["_t"] + 0.6)


def chart(cv, ctx):
    sc, th = ctx.sc, ctx.th
    bars = sc["bars"]
    n = len(bars)
    heading(cv, ctx, sc["title"], 330, 68)
    base, maxh = 1300, 700
    vmax = max(float(b["value"]) for b in bars) * 1.08
    slot = 900 / n
    bw = slot * 0.62
    hl = sc.get("hl")
    cv.line(80, base + 2, 1000, base + 2, "#ffffff", 3, alpha=0.35)
    for g in range(1, 5):
        cv.line(80, base - maxh * g / 4.3, 1000, base - maxh * g / 4.3, "#ffffff", 1.5, alpha=0.08)
    pts = []
    for j, b in enumerate(bars):
        k = ease_out((ctx.t - b["_t"]) / 0.9)
        x = 90 + slot * j + (slot - bw) / 2
        h = max(8, maxh * float(b["value"]) / vmax) * max(k, 0.0)
        c = th["accent2"] if hl == j else th["accent"]
        if sc.get("kind") == "line":
            pts.append((x + bw / 2, base - h, k, b))
        elif k > 0:
            cv.rrect(x, base - h, x + bw, base + 4, 14, fill=lin(0, base - h, 0, base, [(0, c), (1, c + "b0")]), shadow=(0, 6, 10, "#000a"))
            cv.rrect(x, base - h, x + bw, base - h + 10, 5, fill="#ffffff", alpha=0.35)
            if hl == j:
                cv.rrect(x - 3, base - h - 3, x + bw + 3, base + 6, 16, stroke=c, width=6, blur=10, alpha=0.5)
        if k > 0:
            s = 44
            txt = fmt(float(b["value"]) * k, b.get("decimals", 0)) + ("%" if sc.get("percent") else "")
            while cv.text_w(txt, s) > slot - 6 and s > 24:
                s -= 2
            cv.text(txt, x + bw / 2, base - h - 20, s, fill="#fff", stroke=th["ink"], stroke_w=8, center=True)
            sz, ls = fit(cv, b["label"], slot - 8, 34, 22, 2)
            for i, l in enumerate(ls):
                cv.text(l, x + bw / 2, base + 56 + i * sz * 1.15, sz, fill=CREAM, center=True, alpha=min(1, k * 2))
    if sc.get("kind") == "line":
        vis = [p for p in pts if p[2] > 0]
        for a, b2 in zip(vis, vis[1:]):
            cv.line(a[0], a[1], b2[0], b2[1], th["accent"], 8)
        for (x, y, k, _) in vis:
            cv.circle(x, y, 14, fill="#fff")
            cv.circle(x, y, 22, fill=th["accent"], alpha=0.4, blur=6)
    note(cv, ctx, sc.get("note", ""), 1440, bars[-1]["_t"] + 0.8, 40)


def callout(cv, ctx):
    sc, th = ctx.sc, ctx.th
    heading(cv, ctx, sc["title"], 330, 68)
    hero(cv, ctx, sc.get("icon"), 540, 900, sc.get("icon_size", 360))
    cs = sc["callouts"]
    ys = {1: [900], 2: [660, 1180], 3: [620, 940, 1260]}.get(len(cs), [620, 860, 1100, 1340][:len(cs)])
    for i, c in enumerate(cs):
        p = ctx.p(c["_t"], 0.5)
        if p <= 0:
            continue
        side = c.get("side", "left" if i % 2 == 0 else "right")
        y = ys[i]
        x0, x1 = (36, 410) if side == "left" else (690, 1044)
        dx = (1 - ease_out(p)) * (-160 if side == "left" else 160)
        ex = x1 if side == "left" else x0
        tx = 540 + (-120 if side == "left" else 120)
        k = ease((ctx.t - c["_t"]) / 0.5)
        cv.line(ex + dx, y, ex + (tx - ex) * k + dx, y + (900 - y) * 0.35 * k, th["accent2"], 4, alpha=0.9)
        cv.circle(ex + (tx - ex) * k + dx, y + (900 - y) * 0.35 * k, 9, fill=th["accent2"], alpha=k)
        sz, ls = fit(cv, c["text"], x1 - x0 - 40, 42, 28, 3)
        h = 40 + len(ls) * sz * 1.2
        cv.card(x0 + dx, y - h / 2, x1 + dx, y + h / 2, th["accent"], 22, 0.9, a=p)
        for k2, l in enumerate(ls):
            cv.text(l, x0 + 24 + dx, y - h / 2 + 24 + sz * 0.95 + k2 * sz * 1.2, sz, fill="#fff", alpha=p)


def outro(cv, ctx):
    sc, th = ctx.sc, ctx.th
    heading(cv, ctx, sc["title"], 330, 76)
    bl = sc["bullets"]
    n = len(bl)
    ch = 210
    y0 = 430
    cv.card(60, y0, 1020, y0 + n * ch + 40, th["accent"], 34, 0.9, a=ctx.p(ctx.t0 + 0.1, 0.5))
    for i, b in enumerate(bl):
        p = ctx.p(b["_t"], 0.5)
        if p <= 0:
            continue
        y = y0 + 40 + i * ch
        dx = (1 - ease_out(p)) * 120
        draw_icon(cv, "check", 150 + dx, y + 80, 96, ctx.t, halo=False)
        sz, ls = fit(cv, b["text"], 700, 54, 34, 2)
        for k2, l in enumerate(ls):
            cv.text(l, 240 + dx, y + 72 + (k2 - (len(ls) - 1) / 2) * sz * 1.15 + sz * 0.3, sz, fill="#fff", alpha=p)
    if sc.get("cta"):
        a = ctx.p(bl[-1]["_t"] + 0.8, 0.5)
        if a > 0:
            pulse = 1 + 0.02 * math.sin(ctx.t * 4)
            cv.save()
            cv.zoom(pulse, 540, y0 + n * ch + 160)
            pill(cv, ctx, sc["cta"], y0 + n * ch + 170, a, 50, th["accent2"])
            cv.restore()


SHOTS = {"hook": hook, "stat": stat, "compare": compare, "steps": steps, "flow": flow,
         "chart": chart, "callout": callout, "outro": outro}
LISTS = {"compare": "items", "steps": "steps", "flow": "nodes", "chart": "bars", "callout": "callouts", "outro": "bullets"}
