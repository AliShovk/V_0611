"""Эпизод «Озеро Восток» — 4 км льда над водой, изолированной 15 млн лет.

Формат cartoon_engine, 9:16: разрез ледяного щита, керновый бур,
пузырьки древнего воздуха, подледниковое озеро.
"""
import math
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon_engine import FFMPEG, S, W, H, FPS, ease, label, leader, lerp, synthesize, audio_duration, font_path
from cartoon_mariana import draw_caption, phrase_cues

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "storage", "cartoon-vostok")
F_LABEL = ImageFont.truetype(font_path(), S(30))
F_TICK = ImageFont.truetype(font_path(), S(23))
F_BIG = ImageFont.truetype(font_path(), S(52))

TEXT = ("Под антарктическим льдом лежит озеро, которого не касался воздух пятнадцать миллионов лет. "
        "Озеро Восток: четыре километра льда над водой. "
        "Этот лёд хранит пузырьки воздуха, которым сотни тысяч лет — по ним читают древний климат. "
        "В две тысячи двенадцатом году бур наконец дошёл до воды. "
        "В ней нашли бактерий, которые живут без солнца — на минералах и кислороде. "
        "Самое древнее озеро планеты, и мы знаем о нём меньше, чем о поверхности Марса.")

SKY = 150
LAKE_Y = 1010
BOTTOM = 1150


def y_for(m):
    """0..3750 м -> от поверхности до воды."""
    return SKY + 44 + (m / 3750.0) * (LAKE_Y - SKY - 44)


def depth_at(p):
    if p < 0.10:
        return (p / 0.10) * 120
    if p < 0.78:
        return 120 + ((p - 0.10) / 0.68) * (3750 - 120)
    return 3750 + min(1.0, (p - 0.78) / 0.22) * 180


BUBBLES = []
rnd = random.Random(11)
for i in range(70):
    BUBBLES.append((rnd.uniform(16, W - 16), rnd.uniform(SKY + 70, LAKE_Y - 40),
                    rnd.uniform(2.5, 6.0), rnd.uniform(0, 6.28)))


def ice_layer(d, y0, y1, c0, c1):
    for yy in range(int(y0), int(y1), 3):
        k = (yy - y0) / max(1, (y1 - y0))
        d.rectangle([0, S(yy), S(W), S(yy + 3)], fill=lerp(c0, c1, k))


def draw_frame(d, t, total, text):
    p = min(1.0, t / max(0.1, total * 0.95))
    m = depth_at(p)
    # небо над щитом
    for yy in range(0, S(SKY)):
        d.line([(0, yy), (S(W), yy)], fill=lerp((176, 208, 236), (222, 238, 250), yy / S(SKY)))
    d.ellipse([S(560), S(38), S(628), S(106)], fill=(252, 250, 236, 90))
    # снежная поверхность со застругами
    d.rectangle([0, S(SKY - 26), S(W), S(SKY + 8)], fill=(250, 252, 255))
    for i in range(9):
        x = i * 84 + 20
        d.arc([S(x), S(SKY - 30), S(x + 76), S(SKY + 4)], 200, 340, fill=(214, 228, 242), width=S(3))
    # станция
    d.rectangle([S(58), S(SKY - 84), S(150), S(SKY - 22)], fill=(226, 96, 72))
    d.polygon([(S(52), S(SKY - 84)), (S(156), S(SKY - 84)), (S(104), S(SKY - 106))], fill=(176, 64, 52))
    d.rectangle([S(76), S(SKY - 70), S(100), S(SKY - 46)], fill=(255, 232, 170))
    d.line([(S(104), S(SKY - 106)), (S(104), S(SKY - 152))], fill=(90, 96, 104), width=S(3))
    # толща льда
    ice_layer(d, SKY + 8, y_for(1200), (236, 244, 252), (206, 226, 242))
    ice_layer(d, y_for(1200), y_for(2600), (206, 226, 242), (166, 200, 230))
    ice_layer(d, y_for(2600), LAKE_Y, (166, 200, 230), (120, 168, 214))
    # горизонтальные годовые слои
    for i, mm in enumerate(range(90, 3700, 190)):
        yy = y_for(mm)
        d.line([(0, S(yy)), (S(W), S(yy))], fill=(255, 255, 255, 60), width=S(2))
    # пузырьки древнего воздуха
    if m > 250:
        for (bx, by, br, ph) in BUBBLES:
            if m < (by - SKY) / (LAKE_Y - SKY) * 3600 - 150:
                continue
            drift = math.sin(t * 1.2 + ph) * 2.2
            a = int(180 + 60 * math.sin(t * 2 + ph) ** 2)
            d.ellipse([S(bx + drift - br), S(by - br), S(bx + drift + br), S(by + br)],
                      fill=(255, 255, 255, a), outline=(96, 152, 202, 235), width=S(2))
            d.ellipse([S(bx + drift - br * 0.4), S(by - br * 0.6),
                       S(bx + drift + br * 0.1), S(by - br * 0.1)], fill=(255, 255, 255, 240))
    # линейка глубины
    rx = 54
    d.line([(S(rx), S(SKY + 8)), (S(rx), S(LAKE_Y))], fill=(255, 255, 255, 170), width=S(3))
    for meters, name in ((0, "0"), (1000, "1 000"), (2000, "2 000"), (3000, "3 000"), (3750, "3 750")):
        yy = y_for(meters)
        d.line([(S(rx - 2), S(yy)), (S(rx + 20), S(yy))], fill=(255, 255, 255, 230), width=S(3))
        d.text((S(rx + 26), S(yy - 13)), name, font=F_TICK, fill=(255, 255, 255),
               stroke_width=S(3), stroke_fill=(40, 60, 84))
    # керновый бур
    bx = 452
    by = y_for(m)
    d.line([(S(bx), S(SKY - 50)), (S(bx), S(by - 118))], fill=(96, 108, 124, 210), width=S(5))
    d.rounded_rectangle([S(bx - 30), S(by - 118), S(bx + 30), S(by - 8)], radius=S(10),
                        fill=(206, 214, 226), outline=(120, 132, 150), width=S(3))
    d.rounded_rectangle([S(bx - 17), S(by - 106), S(bx + 17), S(by - 22)], radius=S(6),
                        fill=(250, 252, 255), outline=(160, 176, 194), width=S(2))
    for i in range(5):
        yy = by - 96 + i * 16
        d.line([(S(bx - 15), S(yy)), (S(bx + 15), S(yy))], fill=(196, 214, 232), width=S(2))
    d.polygon([(S(bx - 30), S(by - 8)), (S(bx + 30), S(by - 8)), (S(bx), S(by + 22))],
              fill=(150, 164, 182))
    d.polygon([(S(bx - 10), S(by - 8)), (S(bx + 10), S(by - 8)), (S(bx), S(by + 8))],
              fill=(96, 108, 124))
    # плашка глубины
    lab_y = max(SKY + 30, min(LAKE_Y - 80, by - 130))
    label(d, 508, lab_y, f"{int(m)} м", (255, 214, 140), size=F_LABEL)
    # озеро
    for yy in range(S(LAKE_Y), S(BOTTOM)):
        k = (yy - S(LAKE_Y)) / max(1, S(BOTTOM) - S(LAKE_Y))
        d.line([(0, yy), (S(W), yy)], fill=lerp((46, 96, 132), (14, 34, 54), k))
    d.rectangle([0, S(LAKE_Y), S(W), S(LAKE_Y + 5)], fill=(196, 232, 248))
    for i in range(16):
        wx = (i * 97 + 30) % (W - 40)
        wy = LAKE_Y + 24 + ((i * 61) % 96) + math.sin(t * 1.4 + i) * 4
        d.line([(S(wx), S(wy)), (S(wx + 34), S(wy))], fill=(150, 210, 236, 110), width=S(3))
    d.polygon([(0, S(BOTTOM)), (S(W), S(BOTTOM)), (S(W), S(H)), (0, S(H))], fill=(46, 42, 40))
    if m > 3700:
        glow = 0.5 + 0.5 * math.sin(t * 2)
        d.rectangle([0, S(LAKE_Y), S(W), S(LAKE_Y + 6)], fill=(150, 220, 240, int(160 * glow)))
        label(d, 74, LAKE_Y + 26, "озеро Восток", (150, 226, 246), size=F_LABEL)
    # карточка фактов
    if t > total * 0.16:
        d.rounded_rectangle([S(372), S(150), S(700), S(258)], radius=S(16),
                            fill=(16, 32, 48, 210), outline=(160, 214, 246, 140), width=S(2))
        d.text((S(390), S(160)), "4 км льда", font=F_BIG, fill=(255, 255, 255))
        if t > total * 0.30:
            d.text((S(390), S(216)), "15 млн лет без воздуха", font=F_LABEL, fill=(186, 226, 250))
    # врезка: пузырёк воздуха = древний климат
    if t > total * 0.34:
        ix, iy, iw, ih = 66, 726, 316, 202
        d.rounded_rectangle([S(ix), S(iy), S(ix + iw), S(iy + ih)], radius=S(16),
                            fill=(14, 28, 42, 232), outline=(170, 220, 248, 190), width=S(3))
        d.text((S(ix + 14), S(iy + 10)), "воздух возрастом", font=F_TICK, fill=(186, 226, 250))
        d.text((S(ix + 14), S(iy + 40)), "400 000 лет", font=F_LABEL, fill=(255, 214, 140))
        for i in range(3):
            cx = ix + 50 + i * 70
            cy = iy + 120 + math.sin(t * 1.6 + i) * 8
            r = 22 - i * 3
            d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], fill=(255, 255, 255, 60),
                      outline=(186, 226, 250, 200), width=S(2))
        d.text((S(ix + 14), S(iy + ih - 34)), "CO₂, метан, пыль", font=F_TICK, fill=(150, 200, 232))
        leader(d, ix + iw + 4, iy + 44, 330, y_for(900), colour=(186, 226, 250), alpha=200)
    draw_caption(d, text, y=BOTTOM + 24)


def main():
    os.makedirs(OUT, exist_ok=True)
    audio, marks = synthesize(TEXT, OUT)
    total = audio_duration(audio)
    cues = phrase_cues(marks, TEXT)
    print(f"voice {total:.2f}s, cues {len(cues)}")

    frames_dir = os.path.join(OUT, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))

    n = int(total * FPS)
    ci = 0
    for i in range(n):
        t = i / FPS
        while ci + 1 < len(cues) and cues[ci + 1][0] <= t:
            ci += 1
        word = cues[ci][2] if t >= cues[ci][0] - 0.05 else (cues[ci - 1][2] if ci else "")
        img = Image.new("RGB", (S(W), S(H)), (12, 18, 26))
        d = ImageDraw.Draw(img, "RGBA")
        draw_frame(d, t, total, word)
        img.resize((W, H), Image.LANCZOS).save(os.path.join(frames_dir, f"f{i:05d}.png"))
        if i % 200 == 0:
            print("frame", i, "/", n)

    video = os.path.join(OUT, "video.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames_dir, "f%05d.png"), "-i", audio,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                    video], check=True)
    print("video", video)


if __name__ == "__main__":
    main()
