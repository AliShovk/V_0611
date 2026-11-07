"""Эпизод про тоннелепроходческий щит: городской разрез, ротор, обделка."""
import math
import os
import random

from PIL import Image, ImageDraw

from vgen.renderers.skyscraper import caption as hl_caption, progress

W, H, SS = 720, 1280, 2
ART = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art")

TUN_Y = 1052
TUN_R = 104
HEAD1 = 690

CITY = Image.open(os.path.join(ART, "tbm_city.png")).convert("RGBA").resize((W * SS, H * SS), Image.LANCZOS)
TBM = Image.open(os.path.join(ART, "tbm_side.png")).convert("RGBA").transpose(Image.FLIP_LEFT_RIGHT)
DISC = Image.open(os.path.join(ART, "tbm_disc.png")).convert("RGBA")

GOLD = (255, 196, 96)
CREAM = (255, 236, 176)
CYAN = (150, 228, 255)
LIME = (198, 240, 92)
WHITE = (238, 244, 255)
DIM = (150, 170, 200)


def X(v):
    return int(round(v * SS))


def P(*pts):
    return [(X(a), X(b)) for a, b in pts]


def XY(a, b):
    return (X(a), X(b))


def F(size):
    from vgen.palette import font
    return font(size)


def tunnel(d, head_x, complete=False):
    x1 = HEAD1 + 60 if complete else head_x
    d.rounded_rectangle(P((10, TUN_Y - TUN_R), (x1, TUN_Y + TUN_R)), radius=X(TUN_R),
                        fill=(8, 11, 18))
    rnd = random.Random(int(head_x))
    for i in range(int((x1 - 10) / 16)):
        bx = 10 + i * 16
        d.polygon(P((bx, TUN_Y - TUN_R - 10 - rnd.randint(0, 8)),
                    (bx + 10, TUN_Y - TUN_R - 4),
                    (bx, TUN_Y - TUN_R + 6)), fill=(74, 60, 46, 200))
        d.polygon(P((bx, TUN_Y + TUN_R - 6),
                    (bx + 10, TUN_Y + TUN_R + 4),
                    (bx, TUN_Y + TUN_R + 10 + rnd.randint(0, 8))), fill=(74, 60, 46, 200))


def rings(d, head_x, upto=None):
    """Обделка: замкнутые кольца из блоков за щитом."""
    x = 60
    limit = head_x - 70 if upto is None else upto
    while x < limit:
        k = min(1.0, max(0.0, (limit - x) / 60))
        a = int(240 * k)
        d.ellipse([X(x - 46), X(TUN_Y - TUN_R), X(x + 46), X(TUN_Y + TUN_R)],
                  outline=(158, 152, 142, a), width=X(20))
        d.ellipse([X(x - 46), X(TUN_Y - TUN_R), X(x + 46), X(TUN_Y + TUN_R)],
                  outline=(196, 190, 178, int(a * 0.55)), width=X(3))
        for ang in (-155, -110, -65, 65, 110, 155, 0, 180):
            ax = x + math.cos(math.radians(ang)) * (TUN_R - 9)
            ay = TUN_Y + math.sin(math.radians(ang)) * (TUN_R - 9)
            bx = x + math.cos(math.radians(ang)) * (TUN_R + 9)
            by = TUN_Y + math.sin(math.radians(ang)) * (TUN_R + 9)
            d.line(P((ax, ay), (bx, by)), fill=(92, 88, 82, a), width=2)
        x += 50


def floor_strip(d, head_x):
    d.rectangle(P((14, TUN_Y + TUN_R - 14), (head_x, TUN_Y + TUN_R + 4)),
                fill=(64, 58, 50, 235))
    d.line(P((14, TUN_Y + TUN_R - 14), (head_x, TUN_Y + TUN_R - 14)),
           fill=(120, 110, 96, 200), width=X(3))


def draw_machine(frame, head_x, spin=0.0, body=True):
    """Машина в разрезе: яркий оранжевый щит и светлый ротор на забое."""
    d = ImageDraw.Draw(frame, "RGBA")
    r = TUN_R * 0.97
    face_l = head_x - 2 * r
    if body:
        x0 = head_x - 2 * r - 250
        d.rounded_rectangle(P((x0, TUN_Y - r + 10), (face_l + 26, TUN_Y + r - 10)),
                            radius=X(22), fill=(224, 154, 60, 255), outline=(70, 38, 12, 255), width=X(5))
        d.rectangle(P((x0 + 10, TUN_Y - r + 24), (face_l + 16, TUN_Y - r + 44)),
                    fill=(255, 214, 142, 235))
        for i in range(3):
            bx = x0 + 42 + i * 62
            d.rectangle(P((bx, TUN_Y - r + 14), (bx + 12, TUN_Y + r - 14)), fill=(150, 90, 28, 255))
        d.rounded_rectangle(P((x0 + 24, TUN_Y - 40), (x0 + 92, TUN_Y + 4)),
                            radius=X(8), fill=(150, 214, 238, 255), outline=(40, 40, 48, 255), width=X(3))
        # гидродомкраты: от торца кольца до корпуса
        for yy in (TUN_Y - 66, TUN_Y - 22, TUN_Y + 22, TUN_Y + 66):
            d.rectangle(P((x0 - 92, yy - 12), (x0 + 6, yy + 12)),
                        fill=(232, 236, 244, 255), outline=(44, 48, 58, 255), width=X(3))
            d.rectangle(P((x0 - 92, yy - 5), (x0 - 16, yy + 5)), fill=(168, 180, 198, 255))
            d.rectangle(P((x0 - 104, yy - 16), (x0 - 90, yy + 16)), fill=(108, 118, 136, 255))

    # ротор: светлый диск с резцами
    d.ellipse([X(head_x - 2 * r), X(TUN_Y - r), X(head_x), X(TUN_Y + r)],
              fill=(150, 166, 190, 255), outline=(238, 246, 255, 255), width=X(6))
    for i in range(6):
        ang = math.radians(spin + i * 60)
        cx = head_x - r + math.cos(ang) * r * 0.62
        cy = TUN_Y + math.sin(ang) * r * 0.62
        d.line([XY(head_x - r, TUN_Y), (int(cx * SS), int(cy * SS))],
               fill=(226, 236, 250, 235), width=X(9))
    for i in range(14):
        ang = math.radians(spin * 1.0 + i * (360 / 14))
        cx = head_x - r + math.cos(ang) * (r - 12)
        cy = TUN_Y + math.sin(ang) * (r - 12)
        d.ellipse([int((cx - 9) * SS), int((cy - 9) * SS), int((cx + 9) * SS), int((cy + 9) * SS)],
                  fill=(246, 250, 255, 255), outline=(60, 66, 78, 255), width=X(2))
    d.ellipse([X(head_x - r - 26), X(TUN_Y - 26), X(head_x - r + 26), X(TUN_Y + 26)],
              fill=(184, 198, 218, 255), outline=(52, 58, 70, 255), width=X(3))


def callout(d, text, tx, ty, ax, ay, color=(255, 236, 176)):
    d.line(P((tx, ty), (ax, ay)), fill=color, width=X(2))
    d.ellipse(P((ax - 5, ay - 5), (ax + 5, ay + 5)), fill=color)
    bb = d.textbbox((0, 0), text, font=F(19))
    d.rectangle(P((tx - 6, ty - 26), (tx + 6 + (bb[2] - bb[0]) / SS, ty + 4)), fill=(6, 10, 18, 210))
    d.text(XY(tx, ty - 22), text, font=F(19), fill=color)


def dust(d, head_x, t):
    rnd = random.Random(int(t * 7))
    for i in range(14):
        px = head_x - 20 - rnd.uniform(0, 60)
        py = TUN_Y + rnd.uniform(-TUN_R, TUN_R)
        r = rnd.uniform(3, 9)
        d.ellipse(P((px - r, py - r), (px + r, py + r)), fill=(180, 160, 130, rnd.randint(20, 55)))


def hud(d, text, sub="", y=40):
    x = W - 26
    bb = d.textbbox((0, 0), text, font=F(38))
    d.text(XY(x - (bb[2] - bb[0]), y), text, font=F(38), fill=WHITE)
    if sub:
        bb2 = d.textbbox((0, 0), sub, font=F(17))
        d.text(XY(x - (bb2[2] - bb2[0]), y + 42), sub, font=F(17), fill=DIM)


def label(d, text, x, y, color=CREAM, size=24):
    d.text(XY(x, y), text, font=F(size), fill=color, stroke_width=X(3), stroke_fill=(6, 10, 18, 220))


def scene_hook(t, ctx):
    img = CITY.copy()
    d = ImageDraw.Draw(img, "RGBA")
    tunnel(d, 340)
    rings(d, 340, upto=60)
    draw_machine(img, 340, t * 22)
    d = ImageDraw.Draw(img, "RGBA")
    floor_strip(d, 340)
    dust(d, 340, t)
    hud(d, "18 м", "глубина")
    label(d, "сверху город этого не замечает", 30, 150, CREAM, 24)
    return img


def scene_face(t, ctx):
    img = Image.new("RGBA", (X(W), X(H)), (7, 10, 17, 255))
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse(P((-70, 250), (W + 70, H - 110)), fill=(13, 17, 26))
    face_h = X(760)
    face = DISC.resize((face_h, int(DISC.height * face_h / DISC.width)), Image.LANCZOS)
    face = face.rotate(-t * 22, resample=Image.BICUBIC)
    img.alpha_composite(face, (X(360) - face.width // 2, X(250)))
    d = ImageDraw.Draw(img, "RGBA")
    hud(d, "Ø 6 м", "диаметр щита")
    label(d, "ротор с дисковыми резцами", 30, 150, CREAM, 24)
    label(d, "1–3 оборота в минуту", 30, 188, DIM, 20)
    return img


def scene_shield(t, ctx):
    img = CITY.copy()
    d = ImageDraw.Draw(img, "RGBA")
    tunnel(d, 560)
    rings(d, 560, upto=150)
    draw_machine(img, 560, t * 22)
    d = ImageDraw.Draw(img, "RGBA")
    floor_strip(d, 560)
    for i, yy in enumerate((TUN_Y - 56, TUN_Y - 18, TUN_Y + 20, TUN_Y + 58)):
        ln = 34 + 8 * math.sin(t * 3 + i)
        d.rectangle(P((452, yy - 9), (452 + ln, yy + 9)), fill=(58, 66, 80, 240),
                    outline=(160, 176, 198), width=2)
        d.rectangle(P((452 + ln, yy - 4), (452 + ln + 22, yy + 4)), fill=(206, 216, 232, 240))
    label(d, "домкраты упираются в кольцо", 30, 150, CREAM, 24)
    rr = TUN_R * 0.97
    callout(d, "ротор", 470, 880, 560 - rr, TUN_Y - 30)
    callout(d, "щит", 250, 930, 560 - 2 * rr - 120, TUN_Y)
    hud(d, "1,5 м", "ход за цикл")
    return img


def scene_lining(t, ctx):
    img = CITY.copy()
    d = ImageDraw.Draw(img, "RGBA")
    k = min(1.0, ctx.get("scene_t", 0) / max(0.1, ctx.get("scene_dur", 1)))
    head = 240 + 380 * k
    tunnel(d, head)
    rings(d, head, upto=max(60, head - 380))
    draw_machine(img, head, t * 22)
    d = ImageDraw.Draw(img, "RGBA")
    floor_strip(d, head)
    label(d, "кольца обделки встают следом", 30, 150, CREAM, 24)
    label(d, "6–8 блоков · 1,5 м", 30, 188, LIME, 20)
    hud(d, "15 м", "за сутки")
    return img


def scene_final(t, ctx):
    img = CITY.copy()
    d = ImageDraw.Draw(img, "RGBA")
    tunnel(d, HEAD1, complete=True)
    rings(d, HEAD1 + 200, upto=HEAD1 + 40)
    for i in range(9):
        x = 70 + i * 74
        d.ellipse(P((x - 4, TUN_Y - TUN_R + 16), (x + 4, TUN_Y - TUN_R + 24)), fill=(255, 240, 190))
    hud(d, "6 м", "диаметр тоннеля")
    label(d, "готовый тоннель · город цел", 30, 150, CREAM, 24)
    return img


SCENES = {
    "hook": scene_hook,
    "face": scene_face,
    "shield": scene_shield,
    "lining": scene_lining,
    "final": scene_final,
}


def zoom(img, cx, cy, k):
    cw, ch = X(W) / k, X(H) / k
    box = (int(cx * SS - cw / 2), int(cy * SS - ch / 2),
           int(cx * SS + cw / 2), int(cy * SS + ch / 2))
    return img.crop(box).resize((X(W), X(H)), Image.LANCZOS)


def render(name, t, ctx):
    img = SCENES[name](t, ctx).convert("RGBA")
    if name == "shield":
        img = zoom(img, 400, 1010, 1.34)
    elif name == "lining":
        img = zoom(img, 420, 1010, 1.28)
    d = ImageDraw.Draw(img, "RGBA")
    hl_caption(d, ctx.get("caption_text", ""), ctx.get("caption_hl", ()), 1120)
    progress(d, t, ctx.get("total", 60.0))
    return img.convert("RGB")
