"""Эпизод «Океан внутри Земли» — формат cartoon_engine, 9:16.

Вертикальный разрез: бурим от поверхности до переходной зоны (410–660 км),
где рингвудит держит воду в кристаллической решётке.
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon_engine import FFMPEG, S, W, H, FPS, ease, label, leader, lerp, synthesize, audio_duration, font_path
from cartoon_mariana import draw_caption, phrase_cues

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "storage", "cartoon-ocean")
F_LABEL = ImageFont.truetype(font_path(), S(31))
F_TICK = ImageFont.truetype(font_path(), S(23))
F_BIG = ImageFont.truetype(font_path(), S(54))

TEXT = ("Внутри Земли больше воды, чем во всех океанах вместе. "
        "Не в пещерах и не в подземных морях — прямо в камне. "
        "На глубине от четырёхсот до семисот километров лежит минерал рингвудит. "
        "Его кристаллическая решётка удерживает воду: не жидкую, а встроенную в структуру. "
        "В кубометре такой породы до трёх процентов воды по весу. "
        "Капля кажется мелочью, но объём переходной зоны огромен: в ней спрятано от одного до трёх океанов. "
        "Мы знаем это по алмазам: они выносят рингвудит с такой глубины на поверхность.")

TOP_Y, BOTTOM_Y = 150, 1010
# (метры глубины, доля высоты кадра) — кора сжата, переходная зона крупным планом
STOPS = [(0, 0.0), (35, 0.10), (410, 0.42), (660, 0.62), (2900, 1.0)]


def frac_for_depth(m):
    for i in range(len(STOPS) - 1):
        m0, f0 = STOPS[i]
        m1, f1 = STOPS[i + 1]
        if m <= m1:
            k = (m - m0) / (m1 - m0)
            return f0 + (f1 - f0) * ease(k)
    return 1.0


def y_for(m):
    return TOP_Y + frac_for_depth(m) * (BOTTOM_Y - TOP_Y)


def depth_at(p):
    """p 0..1 -> метры; держимся в переходной зоне основную часть ролика."""
    if p < 0.12:
        return (p / 0.12) * 35
    if p < 0.34:
        return 35 + ((p - 0.12) / 0.22) * (410 - 35)
    if p < 0.72:
        return 410 + ((p - 0.34) / 0.38) * (660 - 410)
    return 660 + ((p - 0.72) / 0.28) * (2900 - 660)


def rock(d, y0, y1, c0, c1, grain=26):
    for i in range(int(y0), int(y1), 3):
        k = (i - y0) / max(1, (y1 - y0))
        d.rectangle([0, S(i), S(W), S(i + 3)], fill=lerp(c0, c1, k))
    step = grain
    for row, yy in enumerate(range(int(y0) + 8, int(y1) - 6, step)):
        for xx in range(6 + (row % 2) * step // 2, W - 6, step):
            jitter = ((xx * 7 + yy * 13) % 11) / 11.0
            r = 3 + jitter * 4
            shade = lerp(c0, (255, 255, 255), 0.10 + jitter * 0.12)
            d.ellipse([S(xx - r), S(yy - r * 0.7), S(xx + r), S(yy + r * 0.7)], fill=shade)


def draw_frame(d, t, total, text):
    p = min(1.0, t / max(0.1, total * 0.95))
    m = depth_at(p)
    # небо и поверхность
    d.rectangle([0, 0, S(W), S(TOP_Y - 42)], fill=(178, 216, 238))
    d.rectangle([0, S(TOP_Y - 42), S(W), S(TOP_Y)], fill=(96, 158, 92))
    # слои
    rock(d, TOP_Y, y_for(410), (150, 132, 116), (128, 106, 92))
    rock(d, y_for(410), y_for(660), (86, 118, 168), (60, 92, 148), grain=22)
    rock(d, y_for(660), BOTTOM_Y, (92, 74, 70), (58, 44, 44), grain=30)
    zy0, zy1 = y_for(410), y_for(660)
    if m > 330:
        d.rectangle([0, S(zy0), S(W), S(zy1)], outline=(120, 196, 255, 130), width=S(4))
    # линейка глубин
    rx = 50
    d.line([(S(rx), S(TOP_Y)), (S(rx), S(BOTTOM_Y))], fill=(236, 244, 252, 170), width=S(3))
    for meters, name in ((0, "0"), (35, "35"), (410, "410"), (660, "660"), (2900, "2 900")):
        yy = y_for(meters)
        d.line([(S(rx - 12), S(yy)), (S(rx + 12), S(yy))], fill=(236, 244, 252, 220), width=S(3))
        d.text((S(rx + 16), S(yy - 13)), name, font=F_TICK, fill=(255, 255, 255),
               stroke_width=S(3), stroke_fill=(24, 30, 40))
    d.text((S(rx + 16), S(TOP_Y - 46)), "км", font=F_TICK, fill=(30, 60, 40))
    # подписи слоёв
    for yy, name in ((TOP_Y + 30, "кора"), (452, "верхняя мантия"),
                     (zy0 + (zy1 - zy0) / 2 - 14, "переходная зона"),
                     (y_for(1250), "нижняя мантия")):
        d.text((S(300), S(yy)), name, font=F_TICK, fill=(240, 246, 252),
               stroke_width=S(3), stroke_fill=(20, 26, 34))
    # буровой снаряд справа
    bx = 612
    by = y_for(m)
    d.line([(S(bx), S(TOP_Y - 40)), (S(bx), S(by - 132))], fill=(226, 232, 240, 150), width=S(4))
    d.rectangle([S(bx - 7), S(by - 140), S(bx + 7), S(by - 84)], fill=(206, 214, 224))
    d.rounded_rectangle([S(bx - 26), S(by - 84), S(bx + 26), S(by - 6)], radius=S(10), fill=(230, 236, 244))
    d.polygon([(S(bx - 26), S(by - 6)), (S(bx + 26), S(by - 6)), (S(bx), S(by + 26))], fill=(198, 206, 216))
    for i in range(3):
        d.line([(S(bx - 20), S(by - 68 + i * 20)), (S(bx + 20), S(by - 68 + i * 20))],
               fill=(176, 186, 198), width=S(3))
    # плашка глубины рядом со снарядом
    lab_y = max(TOP_Y + 6, min(BOTTOM_Y - 70, by - 150))
    lw, lh = label(d, 462, lab_y, f"{int(m)} км", (255, 214, 140), size=F_LABEL)
    # зёрна рингвудита в переходной зоне
    if m > 380:
        for i in range(9):
            gx = 108 + (i % 3) * 96
            gy = zy0 + 34 + (i // 3) * 50
            r = 14 + (i % 3) * 3 + math.sin(t * 2 + i) * 2
            d.ellipse([S(gx - r), S(gy - r), S(gx + r), S(gy + r)], fill=(104, 182, 240, 225))
            d.ellipse([S(gx - r + 5), S(gy - r + 5), S(gx + r - 5), S(gy + r - 5)],
                      fill=(150, 212, 250, 200))
    # врезка-лупа
    if m > 520:
        ix, iy, iw, ih = 60, 700, 382, 250
        d.rounded_rectangle([S(ix), S(iy), S(ix + iw), S(iy + ih)], radius=S(18),
                            fill=(16, 28, 42, 236), outline=(120, 196, 255, 200), width=S(3))
        d.text((S(ix + 16), S(iy + 12)), "рингвудит: вода в решётке", font=F_TICK, fill=(158, 206, 244))
        leader(d, ix + iw - 10, iy + 8, 210, zy1 - 4, colour=(140, 206, 255), alpha=230)
        for i in range(10):
            gx = ix + 44 + (i % 5) * 74
            gy = iy + 84 + (i // 5) * 82
            d.ellipse([S(gx - 20), S(gy - 20), S(gx + 20), S(gy + 20)],
                      fill=(66, 98, 144), outline=(150, 206, 250), width=S(3))
            cx, cy = gx + math.sin(t * 3 + i) * 3, gy + math.cos(t * 2.4 + i) * 3
            d.ellipse([S(cx - 13), S(cy - 13), S(cx + 13), S(cy + 13)], outline=(190, 226, 252), width=S(2))
            d.ellipse([S(cx - 7), S(cy - 7), S(cx + 7), S(cy + 7)], fill=(156, 216, 250))
    # цифры: одна плашка в две строки
    if m > 800:
        d.rounded_rectangle([S(72), S(300), S(430), S(396)], radius=S(12), fill=(20, 28, 40, 225))
        d.text((S(88), S(310)), "до 3 % воды по весу", font=F_LABEL, fill=(176, 214, 246))
        if m > 1600:
            d.text((S(88), S(350)), "= 1–3 океана воды", font=F_LABEL, fill=(255, 214, 140))
    # алмаз поднимается и уносит зерно
    if m > 1500:
        k = min(1.0, (m - 1500) / 900)
        dy = y_for(660) - k * (y_for(660) - 300)
        dx = 560
        d.polygon([(S(dx), S(dy - 26)), (S(dx + 22), S(dy - 6)), (S(dx), S(dy + 26)),
                   (S(dx - 22), S(dy - 6))], fill=(198, 236, 246), outline=(255, 255, 255), width=S(3))
        lx, ly = label(d, dx + 34, dy - 16, "алмаз", (214, 240, 250), size=F_TICK)
        for i in range(3):
            sp = (t * 1.6 + i * 0.4) % 1.0
            if sp < 0.5:
                d.ellipse([S(dx - 7), S(dy - 36 - i * 12), S(dx + 7), S(dy - 22 - i * 12)],
                          fill=(255, 255, 255, int(200 * (1 - sp * 2))))
    draw_caption(d, text, y=1052)


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
        img = Image.new("RGB", (S(W), S(H)), (10, 14, 20))
        d = ImageDraw.Draw(img, "RGBA")
        draw_frame(d, t, total, word)
        img.resize((W, H), Image.LANCZOS).save(os.path.join(frames_dir, f"f{i:05d}.png"))
        if i % 150 == 0:
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
