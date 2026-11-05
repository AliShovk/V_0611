"""5-секундный пример: AI-растр как фон + текст + озвучка.

Запуск:
  python tools/ai_bg_5s.py
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vgen import voice
from vgen.palette import font

W, H = 1080, 1920
FPS = 30
DUR = 5.0
SRC = r"C:\Users\Ali PC\cloudflare-img\hero_ev.png"
OUT = r"C:\Users\Ali PC\Vgen_041126\out\ai_bg_demo"
CYAN = (86, 226, 255)
WHITE = (240, 248, 255)


def fit(img, w, h, zoom=1.0, pan=(0.0, 0.0)):
    """Кроп под 9:16 с зумом и панорамой."""
    tr = w / h
    iw, ih = img.size
    if iw / ih > tr:
        nh = int(ih / zoom)
        nw = int(nh * tr)
    else:
        nw = int(iw / zoom)
        nh = int(nw / tr)
    nw, nh = min(nw, iw), min(nh, ih)
    cx = iw / 2 + pan[0] * (iw - nw) / 2
    cy = ih / 2 + pan[1] * (ih - nh) / 2
    box = (int(cx - nw / 2), int(cy - nh / 2), int(cx + nw / 2), int(cy + nh / 2))
    return img.crop(box).resize((w, h), Image.LANCZOS)


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def main():
    os.makedirs(OUT, exist_ok=True)
    frames = os.path.join(OUT, "frames")
    os.makedirs(frames, exist_ok=True)

    base = Image.open(SRC).convert("RGB")
    voice.build({"script": {"narration": "На скорости воздух забирает почти половину запаса хода."}}, OUT)

    n = int(DUR * FPS)
    for i in range(n):
        t = i / FPS
        k = ease(t / DUR)
        zoom = 1.10 - 0.08 * k
        pan = (-0.35 + 0.7 * k, 0.10 - 0.2 * k)
        img = fit(base, W, H, zoom, pan).convert("RGBA")

        # виньетка
        v = Image.new("L", (W, H), 0)
        vd = ImageDraw.Draw(v)
        vd.ellipse([-W * 0.35, -H * 0.2, W * 1.35, H * 1.2], fill=255)
        v = v.filter(ImageFilter.GaussianBlur(160))
        dark = Image.new("RGBA", (W, H), (2, 6, 14, 190))
        img = Image.composite(img, Image.alpha_composite(img, dark), v)

        d = ImageDraw.Draw(img, "RGBA")

        # заголовок появляется
        a = ease((t - 0.35) / 0.7)
        if a > 0:
            fs = 120
            ft = font(fs)
            bb = d.textbbox((0, 0), "ВОЗДУХ", font=ft)
            x = (W - (bb[2] - bb[0])) / 2
            d.text((x, 150), "ВОЗДУХ", font=ft, fill=(255, 255, 255, int(255 * a)))
            sub = "забирает запас хода"
            b2 = d.textbbox((0, 0), sub, font=font(36))
            d.text(((W - (b2[2] - b2[0])) / 2, 150 + (bb[3] - bb[1]) + 28), sub, font=font(36),
                   fill=(86, 226, 255, int(235 * a)))

        # плашка-субтитр с рамкой вокруг −40%
        a2 = ease((t - 1.1) / 0.6)
        if a2 > 0:
            text = "-40% на трассе"
            f = font(44)
            bb = d.textbbox((0, 0), text, font=f)
            tw = bb[2] - bb[0]
            pad = 36
            y = 1600
            d.rounded_rectangle([(W - tw) / 2 - pad, y - 18, (W + tw) / 2 + pad, y + 74],
                                radius=20, fill=(6, 12, 22, int(215 * a2)),
                                outline=(40, 70, 92, int(255 * a2)), width=3)
            d.text(((W - tw) / 2, y), text, font=f, fill=(230, 238, 248, int(255 * a2)))
            d.rounded_rectangle([(W - tw) / 2 - 14, y - 10, (W - tw) / 2 + 168, y + 62],
                                radius=12, outline=(86, 226, 255, int(255 * a2)), width=5)

        # прогресс
        yy = 1862
        d.line([(40, yy), (W - 40, yy)], fill=(45, 60, 78, 220), width=4)
        d.line([(40, yy), (40 + (W - 80) * (t / DUR), yy)], fill=(255, 206, 84, 255), width=4)

        img.convert("RGB").save(os.path.join(frames, f"f{i:05d}.png"))

    silent = os.path.join(OUT, "silent.mp4")
    subprocess.run([voice.FFMPEG, "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames, "f%05d.png"),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-pix_fmt", "yuv420p", silent], check=True)

    final = os.path.join(OUT, "ai_bg_5s.mp4")
    subprocess.run([voice.FFMPEG, "-y", "-v", "error", "-i", silent,
                    "-i", os.path.join(OUT, "voice.wav"),
                    "-map", "0:v", "-map", "1:a", "-af", "apad", "-t", str(DUR),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", final], check=True)
    print("ok", final)


if __name__ == "__main__":
    main()
