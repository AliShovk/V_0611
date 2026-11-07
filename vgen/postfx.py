"""Быстрая пост-обработка кадра: bloom, грейд, хроматика, виньетка, зерно.

Всё на C-операциях PIL (LUT, ImageChops, blur) — на 1440x2560 около 0.2 с
вместо ~3 с у numpy-версии в post.py.
"""
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

BLOOM_THRESHOLD = 205
BLOOM_RADIUS = 9          # радиус размытия в копии 1/4 кадра
BLOOM_GAIN = 0.22
GRAIN = 4
VIGNETTE = 0.30
CHROMA = 1
SHARPEN = 55


@lru_cache(maxsize=8)
def _grade_lut(lift=4, gamma=0.98, gain=(1.05, 1.0, 0.95)):
    luts = []
    for g in gain:
        lut = []
        for i in range(256):
            v = i / 255.0 + lift / 255.0
            v = max(0.0, min(1.0, v)) ** gamma
            lut.append(max(0, min(255, int(v * g * 255))))
        luts.append(lut)
    return luts


def grade(img, sat=1.03):
    r, g, b = img.split()
    lr, lg, lb = _grade_lut()
    out = Image.merge("RGB", (r.point(lr), g.point(lg), b.point(lb)))
    return ImageEnhance.Color(out).enhance(sat)


def bloom(img, threshold=BLOOM_THRESHOLD, gain=BLOOM_GAIN):
    w, h = img.size
    small = img.resize((max(1, w // 4), max(1, h // 4)), Image.BILINEAR)
    lum = small.convert("L")
    lim = int(threshold)
    mask = lum.point(lambda v: 0 if v < lim else int(255 * (v - lim) / max(1, 255 - lim)))
    glow = small.filter(ImageFilter.GaussianBlur(BLOOM_RADIUS))
    glow = Image.composite(glow, Image.new("RGB", small.size, (0, 0, 0)), mask)
    glow = glow.resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))
    return Image.blend(img, ImageChops.add(img, glow), gain)


def chroma(img, shift=CHROMA):
    if shift <= 0:
        return img
    r, g, b = img.split()
    r = r.transform(r.size, Image.AFFINE, (1, 0, -shift, 0, 1, 0), resample=Image.BILINEAR)
    b = b.transform(b.size, Image.AFFINE, (1, 0, shift, 0, 1, 0), resample=Image.BILINEAR)
    return Image.merge("RGB", (r, g, b))


@lru_cache(maxsize=4)
def _vignette_mask(size, strength=VIGNETTE):
    w, h = size
    m = Image.new("L", (max(1, w // 2), max(1, h // 2)), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([-w * 0.15, -h * 0.12, w * 0.65, h * 0.62], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(max(8, w // 20))).resize((w, h), Image.BILINEAR)
    return m.point(lambda v: int(255 * (1 - strength * (1 - v / 255.0))))


def vignette(img, strength=VIGNETTE):
    mask = _vignette_mask(img.size, strength)
    dark = Image.new("RGB", img.size, (4, 8, 14))
    return Image.composite(img, ImageChops.multiply(img, dark), mask)


@lru_cache(maxsize=4)
def _noise(size, amount=GRAIN):
    import random
    rnd = random.Random(7)
    n = Image.new("L", (max(1, size[0] // 2), max(1, size[1] // 2)))
    px = n.load()
    for y in range(n.height):
        for x in range(n.width):
            px[x, y] = 128 + rnd.randint(-amount, amount)
    return n.resize(size, Image.BILINEAR)


def grain(img, amount=GRAIN):
    n = _noise(img.size, amount).convert("RGB")
    neutral = Image.new("RGB", img.size, (128, 128, 128))
    return Image.blend(img, ImageChops.add(img, ImageChops.subtract(n, neutral)), 0.5)


def sharpen(img, percent=SHARPEN):
    return img.filter(ImageFilter.UnsharpMask(radius=1.6, percent=percent, threshold=4))


def finish(img, bloom_on=True, grain_amt=GRAIN, vig=VIGNETTE, chroma_shift=CHROMA):
    out = img.convert("RGB")
    if bloom_on:
        out = bloom(out)
    out = grade(out)
    out = chroma(out, chroma_shift)
    out = sharpen(out)
    out = vignette(out, vig)
    if grain_amt:
        out = grain(out, grain_amt)
    return out


if __name__ == "__main__":
    import sys

    src, dst = sys.argv[1], sys.argv[2]
    finish(Image.open(src)).save(dst)
    print("saved", dst)
