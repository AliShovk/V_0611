"""Пост-обработка кадра: bloom, грейд, зерно, виньетка, хроматика, резкость.

Применять к финальному кадру перед записью — это то, что отличает
«плоскую инфографику» от кадра, который выглядит как продукт.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

# --- параметры по умолчанию (подобраны под тёмный фон + циан/оранжевый) ---
BLOOM_THRESHOLD = 205      # с чего начинается свечение
BLOOM_RADIUS = 18
BLOOM_GAIN = 0.26
GRAIN = 4
VIGNETTE = 0.30
CHROMA = 1                 # сдвиг каналов в пикселях на краях
SHARPEN = 58              # unsharp percent


def _np(img):
    return np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0


def _pil(a):
    return Image.fromarray(np.clip(a * 255.0, 0, 255).astype(np.uint8))


def bloom(img, threshold=BLOOM_THRESHOLD, radius=BLOOM_RADIUS, gain=BLOOM_GAIN):
    a = _np(img)
    lum = a.max(axis=2, keepdims=True)
    mask = np.clip((lum - threshold / 255.0) / max(1e-3, 1 - threshold / 255.0), 0, 1)
    bright = _pil(a * mask)
    glow = bright.filter(ImageFilter.GaussianBlur(radius))
    g = _np(glow)
    return _pil(1.0 - (1.0 - a) * (1.0 - g * gain))


def grade(img, lift=0.012, gamma=0.98, gain=(1.04, 1.0, 0.96), sat=1.04):
    a = _np(img)
    a = a + lift
    a = np.power(np.clip(a, 0, 1), gamma)
    a = a * np.array(gain, dtype=np.float32)
    out = _pil(a)
    out = ImageEnhance.Color(out).enhance(sat)
    return ImageEnhance.Contrast(out).enhance(1.03)


def vignette(img, strength=VIGNETTE):
    w, h = img.size
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    r = np.sqrt(((x - cx) / (w * 0.62)) ** 2 + ((y - cy) / (h * 0.62)) ** 2)
    mask = np.clip(1.0 - strength * np.clip(r - 0.55, 0, 1.6) ** 1.4, 0.25, 1.0)[..., None]
    a = _np(img) * mask
    return _pil(a)


def grain(img, amount=GRAIN, seed=11):
    rng = np.random.default_rng(seed)
    a = _np(img)
    n = rng.normal(0, amount / 255.0, a.shape[:2] + (1,)).astype(np.float32)
    return _pil(a + n)


def chroma(img, shift=CHROMA):
    if shift <= 0:
        return img
    r, g, b = img.split()
    r = r.transform(r.size, Image.AFFINE, (1, 0, -shift, 0, 1, 0), resample=Image.BILINEAR)
    b = b.transform(b.size, Image.AFFINE, (1, 0, shift, 0, 1, 0), resample=Image.BILINEAR)
    return Image.merge("RGB", (r, g, b))


def sharpen(img, percent=SHARPEN):
    return img.filter(ImageFilter.UnsharpMask(radius=2.0, percent=percent, threshold=3))


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
