"""Материалы и свет для рендереров: градиенты, тени, фаска, металл, стекло.

Задача модуля — убрать «плоскую заливку» из кадров. Все функции работают
в координатах 1x (например, 1080x1920) и возвращают готовый RGBA-слой,
поэтому рендерер остаётся простым: собрал слои, наложил, нарисовал текст.

Правило: свет задаётся один раз на кадр (Light), все объекты его слушаются —
тогда кадр выглядит цельным, а не набором наклеек.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageDraw, ImageFilter


# ---------- свет ----------

@dataclass
class Light:
    """Один источник света на кадр: направление и цвет."""
    x: float = 0.35          # 0..1 положение по ширине
    y: float = 0.15          # 0..1 положение по высоте
    color: tuple = (255, 244, 226)
    ambient: tuple = (26, 34, 52)
    strength: float = 1.0

    def tint(self, amount: float) -> tuple:
        """Смешать ambient с цветом света (amount 0..1)."""
        a, c = self.ambient, self.color
        k = max(0.0, min(1.0, amount * self.strength))
        return tuple(int(a[i] + (c[i] - a[i]) * k) for i in range(3))


# ---------- низкоуровневые ----------

def _lerp(c1, c2, k):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3))


def vgradient(size, top, bottom):
    """Вертикальный градиент как отдельный слой."""
    w, h = size
    col = Image.new("RGB", (1, h))
    px = col.load()
    for y in range(h):
        px[0, y] = _lerp(top, bottom, y / max(1, h - 1))
    return col.resize((w, h), Image.BILINEAR)


def gradient_mask(size, top=255, bottom=0, gamma=1.0):
    """Маска-градиент (для мягких переходов и дымки)."""
    w, h = size
    m = Image.new("L", (1, h))
    px = m.load()
    for y in range(h):
        k = (y / max(1, h - 1)) ** gamma
        px[0, y] = int(top + (bottom - top) * k)
    return m.resize((w, h), Image.BILINEAR)


def rounded_mask(size, box, radius, blur=0):
    w, h = size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle(box, radius=radius, fill=255)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return m


def shadow(size, box, radius=24, offset=(0, 18), blur=26, opacity=120):
    """Мягкая тень под объектом (ambient occlusion в грубом приближении)."""
    w, h = size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    ox, oy = offset
    d.rounded_rectangle([box[0] + ox, box[1] + oy, box[2] + ox, box[3] + oy],
                        radius=radius, fill=opacity)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    layer.putalpha(m)
    return layer


def rim(size, box, radius, light: Light, width=6, strength=0.9, blur=1):
    """Светлая кромка сверху-слева — читается как объём."""
    w, h = size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle(box, radius=radius, outline=255, width=width)
    # гасим нижнюю часть: свет сверху
    grad = gradient_mask((w, h), top=255, bottom=40, gamma=1.4)
    m = ImageChops.multiply(m, grad)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    col = light.tint(strength)
    layer = Image.new("RGBA", (w, h), col + (255,))
    layer.putalpha(m)
    return layer


def bevel(size, box, radius, depth=10, light: Light | None = None):
    """Фаска: верхняя грань светлее, нижняя темнее."""
    w, h = size
    light = light or Light()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    depth = max(1, min(depth, int((box[3] - box[1]) // 3), int((box[2] - box[0]) // 3)))
    for i in range(depth):
        alpha = int(90 * (1 - i / depth))
        col = light.tint(0.75)
        l = Image.new("RGBA", (w, h), col + (alpha,))
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle([box[0] + i, box[1] + i, box[2] - i, box[3] - i],
                                            radius=radius, outline=255, width=1)
        m = ImageChops.multiply(m, gradient_mask((w, h), 255, 30, 1.2))
        l.putalpha(m)
        out = Image.alpha_composite(out, l)
        dark = Image.new("RGBA", (w, h), (0, 0, 0, alpha))
        m2 = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m2).rounded_rectangle([box[0] + i, box[1] + i, box[2] - i, box[3] - i],
                                             radius=radius, outline=255, width=1)
        m2 = ImageChops.multiply(m2, gradient_mask((w, h), 0, 140, 1.0))
        dark.putalpha(m2)
        out = Image.alpha_composite(out, dark)
    return out


# ---------- материалы ----------

def metal(size, box, radius, light: Light, base=(120, 132, 150), top=(210, 222, 238),
          bottom=(52, 60, 74), streak=True):
    """Металл: вертикальный градиент + блик + тёмный низ + микро-штрихи."""
    w, h = size
    m = rounded_mask(size, box, radius)
    body = vgradient(size, top, bottom)
    if streak:
        s = Image.new("RGB", size, base)
        d = ImageDraw.Draw(s)
        for i in range(0, w, 7):
            d.line([(i, 0), (i, h)], fill=_lerp(base, top, 0.06))
        body = Image.blend(body, s, 0.25)
    grad = gradient_mask(size, 255, 0, 0.9)
    body = Image.composite(body, Image.new("RGB", size, _lerp(base, bottom, 0.4)), grad)
    layer = body.convert("RGBA")
    layer.putalpha(m)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out = Image.alpha_composite(out, layer)
    out = Image.alpha_composite(out, rim(size, box, radius, light, width=4, strength=0.85))
    return out


def glass(size, box, radius, light: Light, tint=(150, 210, 235), alpha=110):
    """Стекло: полупрозрачная заливка + косая полоса блика."""
    w, h = size
    m = rounded_mask(size, box, radius)
    body = Image.new("RGBA", size, tint + (alpha,))
    body.putalpha(ImageChops.multiply(m, Image.new("L", size, alpha)))
    out = Image.alpha_composite(Image.new("RGBA", size, (0, 0, 0, 0)), body)
    sheen = Image.new("RGBA", size, (255, 255, 255, 0))
    sm = Image.new("L", size, 0)
    sd = ImageDraw.Draw(sm)
    sd.polygon([(box[0], box[3]), (box[0] + (box[2] - box[0]) * 0.55, box[1]),
                (box[0] + (box[2] - box[0]) * 0.72, box[1]), (box[0] + 40, box[3])], fill=90)
    sm = ImageChops.multiply(sm, m)
    sheen.putalpha(sm.filter(ImageFilter.GaussianBlur(6)))
    return Image.alpha_composite(out, sheen)


def concrete(size, box, radius, light: Light, base=(150, 146, 138)):
    """Бетон: заливка + зерно + тёмный низ."""
    w, h = size
    m = rounded_mask(size, box, radius)
    body = vgradient(size, _lerp(base, (255, 255, 255), 0.12), _lerp(base, (0, 0, 0), 0.35))
    layer = body.convert("RGBA")
    layer.putalpha(m)
    import random
    rnd = random.Random(3)
    spec = ImageDraw.Draw(layer)
    for _ in range(int((box[2] - box[0]) * (box[3] - box[1]) / 380)):
        x = rnd.randint(box[0], box[2])
        y = rnd.randint(box[1], box[3])
        c = rnd.choice([(120, 116, 108), (176, 172, 164), (96, 92, 86)])
        spec.point((x, y), fill=c + (90,))
    return Image.alpha_composite(layer, rim(size, box, radius, light, 3, 0.5))


# ---------- фон ----------

def backdrop(size, light: Light, horizon=0.72, haze=True, ground=(20, 22, 30),
             sky_top=(10, 14, 24), sky_bottom=(26, 34, 54)):
    """Фон сцены: небо с градиентом, дымка у горизонта, земля/пол."""
    w, h = size
    img = vgradient(size, sky_top, sky_bottom).convert("RGBA")
    hy = int(h * horizon)
    # свечение от источника света
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gx, gy = int(w * light.x), int(h * light.y)
    r = int(w * 0.55)
    gd.ellipse([gx - r, gy - r, gx + r, gy + r], fill=light.color + (36,))
    glow = glow.filter(ImageFilter.GaussianBlur(int(w * 0.12)))
    img = Image.alpha_composite(img, glow)
    if haze:
        mist = Image.new("RGBA", size, (0, 0, 0, 0))
        md = ImageDraw.Draw(mist)
        band = int(h * 0.05)
        for i in range(band):
            a = int(46 * (1 - abs(i - band / 2) / (band / 2)))
            md.rectangle([0, hy - band + i, w, hy - band + i + 1], fill=light.tint(0.35) + (a,))
        img = Image.alpha_composite(img, mist.filter(ImageFilter.GaussianBlur(6)))
    # земля
    g = Image.new("RGBA", size, (0, 0, 0, 0))
    gd2 = ImageDraw.Draw(g)
    gd2.rectangle([0, hy, w, h], fill=ground + (255,))
    gg = gradient_mask(size, 0, 255, 0.6)
    g.putalpha(ImageChops.multiply(Image.new("L", size, 255), gg))
    img = Image.alpha_composite(img, g)
    # отражение света на полу
    refl = Image.new("RGBA", size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    rd.ellipse([w * 0.05, hy + 20, w * 0.95, h], fill=light.color + (18,))
    img = Image.alpha_composite(img, refl.filter(ImageFilter.GaussianBlur(40)))
    return img


def grade(img, contrast=1.05, sat=1.04, warm=(1.04, 1.0, 0.97)):
    from PIL import ImageEnhance
    out = ImageEnhance.Contrast(img.convert("RGB")).enhance(contrast)
    out = ImageEnhance.Color(out).enhance(sat)
    r, g, b = out.split()
    r = r.point(lambda v: min(255, int(v * warm[0])))
    b = b.point(lambda v: min(255, int(v * warm[2])))
    return Image.merge("RGB", (r, g, b))
