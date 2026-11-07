"""Шрифты и палитра эпизодов."""
import os
from PIL import ImageFont

SS = 2
_CACHE = {}


def font_path():
    for cand in (os.environ.get("FONT_BOLD"),
                 "C:/Windows/Fonts/msyhbd.ttc",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
                 "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        if cand and os.path.exists(cand):
            return cand
    raise FileNotFoundError("Нет шрифта с кириллицей: задайте FONT_BOLD")


def font(size):
    if size not in _CACHE:
        _CACHE[size] = ImageFont.truetype(font_path(), int(round(size * SS)))
    return _CACHE[size]
