"""Золотые Ворота: фото-растр для настроения + SVG-схема для объяснения."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from vgen.palette import font
from vgen.renderers.ev import caption, progress

W, H, SS = 720, 1280, 2
ART = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art")
PHOTOS = r"C:\Users\Ali PC\cloudflare-img"

def _prep(path, width=1500):
    im = Image.open(path).convert("RGB")
    if im.width > width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    return im


FOG = _prep(os.path.join(PHOTOS, "San_francisco_in_fog_with_rays.jpg"))
SUNSET = _prep(os.path.join(PHOTOS, "Golden_Gate_Bridge_at_sunset_1.jpg"))
BRIDGE = Image.open(os.path.join(ART, "gg_bridge.png")).convert("RGBA")

ORANGE = (196, 74, 48)
CREAM = (255, 236, 210)
CYAN = (120, 214, 235)
WHITE = (245, 248, 252)
GREY = (160, 172, 186)


def X(v):
    return int(round(v * SS))


def P(*pts):
    return [(X(a), X(b)) for a, b in pts]


def XY(a, b):
    return (X(a), X(b))


def F(s):
    return font(s)


def fill(img, w, h, zoom=1.0, pan=(0.0, 0.0)):
    tr = w / h
    iw, ih = img.size
    if iw / ih > tr:
        nh = int(ih / zoom); nw = int(nh * tr)
    else:
        nw = int(iw / zoom); nh = int(nw / tr)
    nw, nh = min(nw, iw), min(nh, ih)
    cx = iw / 2 + pan[0] * (iw - nw) / 2
    cy = ih / 2 + pan[1] * (ih - nh) / 2
    return img.crop((int(cx - nw / 2), int(cy - nh / 2), int(cx + nw / 2), int(cy + nh / 2))).resize((w, h), Image.LANCZOS)


def grade(img, warm=1.06, contrast=1.06, sat=0.92):
    img = ImageEnhance.Color(img).enhance(sat)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Brightness(img).enhance(0.95)
    r, g, b = img.split()
    r = r.point(lambda v: min(255, int(v * warm)))
    b = b.point(lambda v: min(255, int(v * 0.94)))
    return Image.merge("RGB", (r, g, b))


FOG_GRADED = grade(FOG)
SUNSET_GRADED = grade(SUNSET, 1.08, 1.04, 0.95)

_VIG = {}


def vignette(img, strength=170):
    """Маска виньетки считается один раз, дальше только composite."""
    key = (img.size, strength)
    if key not in _VIG:
        v = Image.new("L", img.size, 0)
        d = ImageDraw.Draw(v)
        d.ellipse([-img.width * 0.3, -img.height * 0.18, img.width * 1.3, img.height * 1.18], fill=255)
        v = v.filter(ImageFilter.GaussianBlur(120))
        dark = Image.new("RGBA", img.size, (4, 8, 14, strength))
        _VIG[key] = Image.composite(Image.new("RGBA", img.size, (255, 255, 255, 255)),
                                    Image.new("RGBA", img.size, (0, 0, 0, 0)), v)
        _VIG[key + ("dark",)] = dark
    mask = _VIG[key]
    return Image.composite(img.convert("RGBA"), Image.alpha_composite(img.convert("RGBA"), _VIG[key + ("dark",)]), mask)


NOISE = None


def grain(img, amount=4, seed=3):
    """Быстрый шум: один раз готовим тайл, дальше только blend на C-скорости."""
    global NOISE
    if NOISE is None or NOISE.size != img.size:
        import numpy as np
        rnd = np.random.default_rng(seed)
        n = rnd.integers(-amount, amount + 1, size=(img.height, img.width, 1), dtype=np.int16)
        base = np.asarray(img, dtype=np.int16)
        NOISE = Image.fromarray(np.clip(base + n, 0, 255).astype(np.uint8)).convert("RGB")
        NOISE = Image.blend(img, NOISE, 0.55)
    return NOISE.copy()


_SCRIM = {}


def scrim(img, y1=0, y2=430, alpha=120):
    """Готовая подложка под заголовок (кэш), иначе рисуем 100 полос каждый кадр."""
    key = (img.size, y1, y2, alpha)
    if key not in _SCRIM:
        sc = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sc)
        for yy in range(y1, y2, 4):
            k = 1 - (yy - y1) / max(1, y2 - y1)
            sd.rectangle([0, yy, img.width, yy + 4], fill=(4, 8, 14, int(alpha * k)))
        _SCRIM[key] = sc
    return Image.alpha_composite(img, _SCRIM[key])


def headline(d, top, bottom=None, sub=None, y=120, color2=ORANGE):
    from vgen.renderers.ev import fit_size
    fs = fit_size(top, 90, 640)
    b = d.textbbox((0, 0), top, font=F(fs))
    d.text(XY((W - (b[2] - b[0]) / SS) / 2, y), top, font=F(fs), fill=WHITE,
           stroke_width=X(4), stroke_fill=(6, 10, 16, 190))
    if bottom:
        fb = min(fs, fit_size(bottom, 90, 640))
        b2 = d.textbbox((0, 0), bottom, font=F(fb))
        d.text(XY((W - (b2[2] - b2[0]) / SS) / 2, y + 108), bottom, font=F(fb), fill=color2,
               stroke_width=X(4), stroke_fill=(6, 10, 16, 190))
    if sub:
        bs = d.textbbox((0, 0), sub, font=F(26))
        d.text(XY((W - (bs[2] - bs[0]) / SS) / 2, y + (216 if bottom else 112)), sub,
               font=F(26), fill=GREY, stroke_width=X(3), stroke_fill=(6, 10, 16, 170))


def badge(d, label="VGEN", tag="ЗОЛОТЫЕ ВОРОТА"):
    d.rounded_rectangle(P((26, 28), (132, 66)), radius=X(8), outline=(240, 244, 250), width=X(2))
    d.text(XY(36, 36), label, font=F(22), fill=WHITE)
    d.rounded_rectangle(P((26, 74), (232, 104)), radius=X(8), fill=(40, 18, 12, 220),
                        outline=ORANGE, width=X(2))
    d.text(XY(34, 80), tag, font=F(17), fill=CREAM)


def dark_bg():
    img = Image.new("RGB", (X(W), X(H)), (7, 11, 18))
    d = ImageDraw.Draw(img)
    for y in range(X(H)):
        k = y / X(H)
        c = (int(8 + 6 * k), int(13 + 10 * k), int(21 + 14 * k))
        d.line([(0, y), (X(W), y)], fill=c)
    for i in range(60):
        rnd = random.Random(i * 3)
        x, y = rnd.randrange(X(W)), rnd.randrange(X(700))
        d.point((x, y), fill=(190, 205, 225))
    return img.convert("RGBA")


def bridge(img, cx, cy, width, alpha=1.0, blur=0.0):
    w = X(width)
    b = BRIDGE.resize((w, int(BRIDGE.height * w / BRIDGE.width)), Image.LANCZOS)
    if blur:
        b = b.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 1:
        a = b.split()[-1].point(lambda v: int(v * alpha))
        b.putalpha(a)
    img.alpha_composite(b, (int(X(cx) - b.width / 2), int(X(cy) - b.height / 2)))
    return img


def bracket(d, x1, x2, y, label, color=CREAM):
    d.line(P((x1, y), (x2, y)), fill=color, width=X(3))
    for xx in (x1, x2):
        d.line(P((xx, y - 12), (xx, y + 12)), fill=color, width=X(3))
    b = d.textbbox((0, 0), label, font=F(24))
    d.rectangle(P(((x1 + x2) / 2 - (b[2] - b[0]) / SS / 2 - 10, y - 44),
                  ((x1 + x2) / 2 + (b[2] - b[0]) / SS / 2 + 10, y - 6)), fill=(6, 10, 16, 220))
    d.text(XY((x1 + x2) / 2 - (b[2] - b[0]) / SS / 2, y - 40), label, font=F(24), fill=color)


def dim_v(d, x, y1, y2, label, color=CREAM):
    d.line(P((x, y1), (x, y2)), fill=color, width=X(3))
    for yy in (y1, y2):
        d.line(P((x - 12, yy), (x + 12, yy)), fill=color, width=X(3))
    d.text(XY(x + 18, (y1 + y2) / 2 - 14), label, font=F(24), fill=color,
           stroke_width=X(3), stroke_fill=(6, 10, 16, 200))


def scene_hook(t, ctx):
    k = t / max(0.1, ctx.get("scene_dur", 6))
    img = fill(FOG_GRADED, X(W), X(H), 1.04 + 0.05 * k, (-0.15 + 0.3 * k, 0.05)).convert("RGBA")
    img = vignette(img, 150)
    img = scrim(img, 0, 470, 150)
    d = ImageDraw.Draw(img, "RGBA")
    headline(d, "1280 МЕТРОВ", "НА ДВУХ ТРОСАХ", None, 118, ORANGE)
    d.rounded_rectangle(P((60, 1050), (660, 1122)), radius=X(14), fill=(40, 16, 10, 205),
                        outline=ORANGE, width=X(3))
    d.text(XY(92, 1070), "ЗОЛОТЫЕ ВОРОТА · 1937", font=F(26), fill=CREAM)
    badge(d)
    return img


def scene_cables(t, ctx):
    img = dark_bg()
    bridge(img, 360, 760, 780, 1.0)
    d = ImageDraw.Draw(img, "RGBA")
    # главный трос и подвески
    d.line(P((180, 610), (540, 610)), fill=CREAM, width=X(3))
    bracket(d, 196, 524, 560, "главный трос")
    bracket(d, 300, 420, 980, "подвески")
    headline(d, "ВЕСЬ ВЕС", "НА ТРОСАХ", "трос толщиной почти метр", 140, ORANGE)
    badge(d)
    return img


def scene_towers(t, ctx):
    img = dark_bg()
    bridge(img, 360, 820, 1500, 1.0)
    d = ImageDraw.Draw(img, "RGBA")
    dim_v(d, 620, 330, 760, "227 м", CREAM)
    headline(d, "ДВЕ БАШНИ", "227 МЕТРОВ", "выше воды", 140, ORANGE)
    badge(d)
    return img


def ship(d, x, y, s=1.0):
    d.polygon(P((x, y), (x + 210 * s, y), (x + 196 * s, y + 26 * s), (x + 18 * s, y + 26 * s)),
              fill=(30, 44, 58, 255), outline=(90, 110, 130))
    d.rectangle(P((x + 40 * s, y - 26 * s), (x + 150 * s, y - 2 * s)), fill=(40, 58, 74, 255))
    d.rectangle(P((x + 150 * s, y - 46 * s), (x + 186 * s, y - 2 * s)), fill=(224, 230, 238, 255))
    for i in range(5):
        d.rectangle(P((x + (52 + i * 18) * s, y - 20 * s), (x + (62 + i * 18) * s, y - 8 * s)),
                    fill=(255, 214, 120, 210))


def scene_deck(t, ctx):
    img = dark_bg()
    # вода
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle(P((0, 980), (W, 1280)), fill=(10, 22, 32))
    for i in range(9):
        y = 1000 + i * 26
        d.line(P((20, y), (W - 20, y)), fill=(18, 40, 56), width=X(2))
    # палуба
    d.rectangle(P((0, 700), (W, 742)), fill=(58, 54, 48))
    d.rectangle(P((0, 742), (W, 772)), fill=(40, 26, 22))
    # ферма
    for i in range(0, 720, 40):
        d.line(P((i, 742), (i + 20, 772)), fill=(150, 70, 50), width=X(3))
        d.line(P((i + 20, 742), (i, 772)), fill=(150, 70, 50), width=X(3))
    # корабль под мостом
    ship(d, 240 + 10 * math.sin(t * 0.6), 950, 1.15)
    dim_v(d, 60, 772, 980, "67 м", CREAM)
    headline(d, "ПОД МОСТОМ", "67 МЕТРОВ", "проходят океанские суда", 140, ORANGE)
    badge(d)
    return img


def scene_final(t, ctx):
    img = fill(SUNSET_GRADED, X(W), X(H), 1.02 + 0.04 * (t / max(0.1, ctx.get("scene_dur", 6))), (0.1, 0.0)).convert("RGBA")
    img = vignette(img, 160)
    img = scrim(img, 0, 470, 140)
    d = ImageDraw.Draw(img, "RGBA")
    headline(d, "1937", "ДВА ТРОСА", "с тех пор он стоит", 150, ORANGE)
    badge(d)
    return img


SCENES = {"hook": scene_hook, "cables": scene_cables, "towers": scene_towers,
          "deck": scene_deck, "final": scene_final}


def render(name, t, ctx):
    img = SCENES[name](t, ctx).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    caption(d, ctx.get("caption_text", ""), ctx.get("caption_hl", ()), 1148)
    progress(d, t, ctx.get("total", 66.0))
    return img.convert("RGB")
