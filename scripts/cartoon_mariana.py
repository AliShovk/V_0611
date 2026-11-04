"""Эпизод «Марианская впадина» в формате cartoon_engine: 2D-мультик 9:16.

Озвучка Edge (Светлана) -> word boundaries -> кадры PIL -> mp4.
Глубина, давление и свет привязаны к таймингу речи.
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon_engine import (FFMPEG, S, SS, W, H, FPS, caption, character, ease,
                            label, leader, lerp, synthesize, audio_duration,
                            build_cues, font_path)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "storage", "cartoon")
F_WORD = ImageFont.truetype(font_path(), S(50))
F_LABEL = ImageFont.truetype(font_path(), S(32))
F_TICK = ImageFont.truetype(font_path(), S(24))
F_BIG = ImageFont.truetype(font_path(), S(58))

TEXT = ("Океан кажется глубоким, но настоящая бездна начинается ниже километра. "
        "Мы опускаемся в Марианскую впадину — одиннадцать тысяч метров вниз. "
        "На четырёх километрах давление уже четыреста атмосфер. "
        "Глубже восьми не проходит ни один луч света: там всегда ночь. "
        "На дне давление тысяча сто атмосфер — как если бы на ладонь поставили три автомобиля. "
        "И всё равно там живут рыбы, которые никогда не видели солнца.")

BASE_Y = 1112
TOP_Y = 96


def phrase_cues(marks, text, max_words=3):
    """Субтитры фразами по 2-3 слова; границы предложений и запятых соблюдаются."""
    tokens = text.split()
    cues = []
    i = 0
    while i < len(tokens):
        j = i
        while j + 1 < len(tokens) and (j - i + 1) < max_words:
            if tokens[j].endswith((",", ".", "!", "?", "—")):
                break
            j += 1
        words = tokens[i:j + 1]
        start = marks[i][0] if i < len(marks) else (cues[-1][1] if cues else 0)
        end = marks[min(j, len(marks) - 1)][1] if marks else start + 1.0
        label_text = " ".join(w.strip("—") for w in words).rstrip(",.!?—").strip()
        cues.append((start, end, label_text))
        i = j + 1
    return cues


def draw_caption(d, text, y=1108):
    """Субтитр в одну-две строки, шрифт ужимается под ширину кадра."""
    if not text:
        return
    max_w = S(W) - S(56)
    size = 50
    while size > 34:
        f = ImageFont.truetype(font_path(), S(size))
        if d.textbbox((0, 0), text, font=f, stroke_width=S(6))[2] <= max_w:
            break
        size -= 2
    f = ImageFont.truetype(font_path(), S(size))
    bbox = d.textbbox((0, 0), text, font=f, stroke_width=S(6))
    x = (S(W) - (bbox[2] - bbox[0])) / 2 - bbox[0]
    d.text((x, S(y)), text, font=f, fill=(255, 255, 255),
           stroke_width=S(6), stroke_fill=(18, 24, 34))


def depth_at(p):
    """p: 0..1 -> метры. Ступени: 0-4000 быстро, потом 8000, потом 11000."""
    if p < 0.22:
        return (p / 0.22) * 4000
    if p < 0.60:
        return 4000 + ((p - 0.22) / 0.38) * 4000
    return 8000 + (min(1.0, (p - 0.60) / 0.36)) * 3000


def y_for_depth(m):
    return TOP_Y + (m / 11000.0) * (BASE_Y - TOP_Y)


def water_colour(m):
    k = (m / 11000.0) ** 0.7
    return lerp((86, 172, 205), (5, 15, 30), k)


def fish(d, x, y, s, col, t, i, flip=False):
    drift = math.sin(t * 0.9 + i * 1.7) * 12
    x += drift
    body = [S(x - 26 * s), S(y - 11 * s), S(x + 24 * s), S(y + 11 * s)]
    d.ellipse(body, fill=col)
    tail = [(S(x + 22 * s), S(y)), (S(x + 44 * s), S(y - 13 * s)), (S(x + 44 * s), S(y + 13 * s))]
    d.polygon(tail, fill=col)
    if not flip:
        d.ellipse([S(x - 16 * s), S(y - 5 * s), S(x - 10 * s), S(y + 1 * s)], fill=(20, 26, 34))


def draw_frame(d, t, total, cues_writer):
    m = depth_at(min(1.0, t / max(0.1, total * 0.94)))
    # вода
    for yy in range(0, S(H)):
        m_here = ((yy / S(H)) * 11000) / 1.0
        d.line([(0, yy), (S(W), yy)], fill=water_colour(min(11000, m_here)))
    # столбы света сверху, гаснут с глубиной
    fade = max(0.0, 1.0 - m / 5200)
    if fade > 0.02:
        for i, sx in enumerate((110, 300, 520)):
            a = int(30 * fade)
            d.polygon([(S(sx - 34), 0), (S(sx + 34), 0), (S(sx + 120), S(900)), (S(sx - 96), S(900))],
                      fill=(205, 236, 255, a))
    # морской снег
    for i in range(26):
        sy = (i * 173 + t * 16 * (1 + i % 3)) % H
        sx = (i * 271) % W
        a = int(70 * max(0.0, 1 - m / 9000))
        d.ellipse([S(sx), S(sy), S(sx + 4), S(sy + 4)], fill=(226, 240, 250, max(0, a)))
    # дно
    floor = y_for_depth(11000)
    d.polygon([(0, S(floor)), (S(140), S(floor - 20)), (S(320), S(floor + 16)),
               (S(520), S(floor - 12)), (S(W), S(floor + 6)), (S(W), S(H)), (0, S(H))],
              fill=(26, 34, 46))
    # линейка глубины
    rx = 62
    d.line([(S(rx), S(TOP_Y)), (S(rx), S(BASE_Y))], fill=(186, 208, 226, 160), width=S(3))
    for meters, name in ((0, "0"), (1000, "1 000"), (4000, "4 000"),
                         (8000, "8 000"), (11000, "11 000")):
        yy = y_for_depth(meters)
        d.line([(S(rx - 14), S(yy)), (S(rx + 14), S(yy))], fill=(200, 220, 240, 210), width=S(3))
        d.text((S(rx + 22), S(yy - 15)), name, font=F_TICK, fill=(214, 232, 246))
    # маркер текущей глубины
    my = y_for_depth(m)
    d.ellipse([S(rx - 9), S(my - 9), S(rx + 9), S(my + 9)], fill=(255, 196, 96))
    d.line([(S(rx), S(my)), (S(250), S(my))], fill=(255, 196, 96, 120), width=S(2))
    lab_y = max(TOP_Y + 8, min(BASE_Y - 40, my - 16))
    d.text((S(256), S(lab_y)), f"{int(m):,}".replace(",", " ") + " м",
           font=F_LABEL, fill=(255, 214, 140))
    # аппарат с прожектором
    sx, sy = 470, my
    cone = int(46 * max(0.15, fade))
    d.polygon([(S(sx - 18), S(sy + 30)), (S(sx + 18), S(sy + 30)),
               (S(sx + 150), S(sy + 190)), (S(sx - 150), S(sy + 190))],
              fill=(200, 230, 245, cone))
    d.rounded_rectangle([S(sx - 34), S(sy - 26), S(sx + 34), S(sy + 40)],
                        radius=S(14), fill=(232, 238, 244))
    d.ellipse([S(sx - 12), S(sy - 12), S(sx + 12), S(sy + 12)], fill=(120, 200, 235))
    d.line([(S(sx), S(sy - 52)), (S(sx), S(sy - 26))], fill=(232, 238, 244), width=S(4))
    # рыбы по глубинам
    for i, (meters, fx, fs, col) in enumerate(((600, 120, 0.9, (150, 200, 220, 170)),
                                               (2200, 300, 0.75, (140, 190, 215, 160)),
                                               (4200, 520, 0.6, (160, 200, 225, 150)),
                                               (7000, 150, 0.5, (175, 205, 230, 140)),
                                               (9200, 380, 0.42, (190, 215, 235, 130)))):
        fy = y_for_depth(meters)
        if m > meters - 250:
            fish(d, fx, fy, fs, col, t, i)
    # придонная рыба с фонарём
    if m > 10400:
        fy = floor - 34
        fish(d, 200, fy, 0.8, (18, 26, 36), t, 9)
        d.line([(S(214), S(fy - 10)), (S(232), S(fy - 34))], fill=(40, 50, 60), width=S(3))
        d.ellipse([S(226), S(fy - 42), S(240), S(fy - 28)], fill=(255, 232, 150))
    # бейдж давления, держится слева вверху
    if m > 180:
        bar = int(m / 10)
        label(d, 96, 300, f"{bar} атм", (255, 208, 150), size=F_LABEL)
    # бейдж «свет» на глубине
    if m > 7600:
        label(d, 96, 380, "свет: 0", (176, 208, 232), size=F_LABEL)
    # субтитры
    draw_caption(d, cues_writer, y=1108)


def main():
    os.makedirs(OUT, exist_ok=True)
    audio, marks = synthesize(TEXT, OUT)
    total = audio_duration(audio)
    cues = phrase_cues(marks, TEXT)
    print(f"voice {total:.2f}s, words {len(marks)}, cues {len(cues)}")

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
        img = Image.new("RGB", (S(W), S(H)), (8, 16, 26))
        d = ImageDraw.Draw(img, "RGBA")
        draw_frame(d, t, total, word)
        img.resize((W, H), Image.LANCZOS).save(os.path.join(frames_dir, f"f{i:05d}.png"))
        if i % 120 == 0:
            print("frame", i, "/", n)

    video = os.path.join(OUT, "video.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames_dir, "f%05d.png"),
                    "-i", audio, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", video], check=True)
    print("video", video)


if __name__ == "__main__":
    main()
