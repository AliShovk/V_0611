"""Прототип: сцена крана на новом слое материалов (vgen/kit.py).

Рисует один кадр 1080x1920 напрямую (без апскейла из 720) и сохраняет PNG.
  python tools/proto_crane.py out.png
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vgen import kit_pil as kit
from vgen.palette import font

W, H = 1080, 1920
LIGHT = kit.Light(x=0.22, y=0.10, color=(255, 236, 206), ambient=(22, 30, 46))


def text(d, xy, s, size, fill=(240, 246, 252), stroke=0, sfill=(6, 10, 16)):
    d.text(xy, s, font=font(size), fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return d.textbbox(xy, s, font=font(size))


def text_stack(d, x, y, items, gap=22):
    """Кладёт строки одну под другой по измеренной высоте — без наложений."""
    for s, size, fill, stroke in items:
        b = text(d, (x, y), s, size, fill, stroke)
        y = b[3] + gap
    return y


def mast(img, x, y_top, y_bot, width, seg=64):
    """Решётчатая башня из металлических сегментов с фаской."""
    d = ImageDraw.Draw(img, "RGBA")
    seg_top = y_top
    while seg_top < y_bot:
        y2 = min(y_bot, seg_top + seg)
        box = [x - width // 2, seg_top + 4, x + width // 2, y2 - 4]
        img.alpha_composite(kit.shadow(img.size, box, radius=6, offset=(0, 8), blur=14, opacity=90))
        img.alpha_composite(kit.metal(img.size, box, 6, LIGHT))
        img.alpha_composite(kit.bevel(img.size, box, 6, 6, LIGHT))
        d = ImageDraw.Draw(img, "RGBA")
        # раскос внутри сегмента
        d.line([box[0] + 6, y2 - 10, box[2] - 6, seg_top + 10], fill=(70, 84, 104, 220), width=4)
        d.line([box[0] + 6, seg_top + 10, box[2] - 6, y2 - 10], fill=(70, 84, 104, 220), width=4)
        seg_top = y2
    return img


def cable(img, pts, width=5, color=(196, 206, 220)):
    d = ImageDraw.Draw(img, "RGBA")
    d.line(pts, fill=(0, 0, 0, 120), width=width + 3)
    d.line(pts, fill=color, width=width)
    return img


def main(out_path):
    img = kit.backdrop((W, H), LIGHT, horizon=0.805,
                       sky_top=(8, 12, 22), sky_bottom=(30, 40, 62), ground=(18, 20, 28))
    d = ImageDraw.Draw(img, "RGBA")

    MAST_X, MAST_TOP, MAST_BOT = 430, 560, 1560
    JIB_Y = 520

    # башня
    img = mast(img, MAST_X, MAST_TOP, MAST_BOT, 84, seg=58)

    # стрела и противовес
    jib = [MAST_X - 120, JIB_Y - 26, 930, JIB_Y + 26]
    img.alpha_composite(kit.shadow(img.size, jib, 8, (0, 10), 18, 80))
    img.alpha_composite(kit.metal(img.size, jib, 8, LIGHT, top=(220, 230, 244), bottom=(48, 56, 70)))
    img.alpha_composite(kit.bevel(img.size, jib, 8, 8, LIGHT))

    cw = [MAST_X - 205, JIB_Y + 26, MAST_X - 55, JIB_Y + 168]
    img.alpha_composite(kit.shadow(img.size, cw, 10, (0, 12), 16, 110))
    img.alpha_composite(kit.concrete(img.size, cw, 10, LIGHT, base=(124, 120, 112)))

    # трос, крюк, груз
    img = cable(img, [(820, JIB_Y + 20), (820, 980)], 9)
    img = cable(img, [(820, JIB_Y - 8), (MAST_X, JIB_Y - 34)], 5)

    hook_box = [762, 980, 878, 1084]
    img.alpha_composite(kit.shadow(img.size, hook_box, 14, (0, 14), 22, 120))
    img.alpha_composite(kit.metal(img.size, hook_box, 14, LIGHT))
    img.alpha_composite(kit.bevel(img.size, hook_box, 14, 10, LIGHT))

    load = [700, 1100, 940, 1330]
    img.alpha_composite(kit.shadow(img.size, load, 10, (0, 18), 26, 130))
    img.alpha_composite(kit.concrete(img.size, load, 10, LIGHT, base=(158, 150, 138)))

    d = ImageDraw.Draw(img, "RGBA")
    d.line([708, 1164, 932, 1164], fill=(112, 106, 98, 190), width=5)
    text(d, (726, 1196), "50 ТОНН", 34, (255, 244, 226), 2)
    img = cable(img, [(820, 1084), (748, 1130)], 4)
    img = cable(img, [(820, 1084), (892, 1130)], 4)

    # контактные тени
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([690, 1290, 950, 1348], fill=(0, 0, 0, 150))
    d.ellipse([360, 1544, 500, 1592], fill=(0, 0, 0, 175))

    # заголовок в своей зоне
    text_stack(d, 70, 52, [
        ("50 ТОНН", 92, (245, 249, 255), 3),
        ("держит противовес", 34, (120, 214, 235), 2),
        ("башня работает на сжатие", 23, (170, 186, 206), 0),
    ], gap=18)

    img = kit.grade(img.convert("RGB"), 1.05, 1.05).convert("RGBA")
    img.convert("RGB").save(out_path)
    print("saved", out_path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "proto_crane.png")
