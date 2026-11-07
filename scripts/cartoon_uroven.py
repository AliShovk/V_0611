"""Стройлайфхак №2 «Уровень врёт» — в стиле референса: тёмный фон, цветные чипы,
крупный заголовок в две строки разными цветами, караоке-субтитры.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon_engine import (FFMPEG, S, W, H, FPS, ease, audio_duration,
                            load_or_synthesize, font_path)
import sfx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "art", "gazo")
OUT = os.path.join(ROOT, "storage", "cartoon-uroven")

BG_C = (9, 13, 26)
GRID = (22, 30, 50)
NAVY = (17, 24, 41)
CYAN = (127, 230, 242)
AMBER = (255, 196, 92)
RED = (255, 91, 74)
GREEN = (75, 224, 139)
WHITE = (255, 255, 255)
MUTED = (154, 166, 191)

F_CHIP = ImageFont.truetype(font_path(), S(17))
F_SECTION = ImageFont.truetype(font_path(), S(13))
F_HEAD = ImageFont.truetype(font_path(), S(54))
F_CAP = ImageFont.truetype(font_path(), S(30))
F_SMALL = ImageFont.truetype(font_path(), S(14))

TEXT = ("Пузырьковый уровень врёт, и вы об этом не узнаете. "
        "Проверка занимает десять секунд. "
        "Приложите уровень к стене и запомните, где стоит пузырёк. "
        "Переверните его на сто восемьдесят градусов и приложите к тому же месту. "
        "Если пузырёк ушёл в сторону — врёт уровень, а не стена. "
        "И вся плитка, которую вы по нему положили, завалена: восемь миллиметров на метр видно глазом. "
        "Хороший инструмент показывает одно и то же в обе стороны.")

BOX = S(620)
ART_Y = S(250)


def load(name):
    img = Image.open(os.path.join(ART, name + ".png")).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    ratio = min(BOX / img.width, BOX / img.height)
    img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.LANCZOS)
    canvas = Image.new("RGBA", (BOX, BOX), (0, 0, 0, 0))
    canvas.alpha_composite(img, ((BOX - img.width) // 2, (BOX - img.height) // 2))
    return canvas


SCENES = {k: load(n) for k, n in (("l1", "d_level1"), ("l2", "d_level2"), ("l3", "d_level3"))}


def background():
    img = Image.new("RGB", (S(W), S(H)), BG_C)
    d = ImageDraw.Draw(img)
    step = S(56)
    for x in range(0, S(W), step):
        d.line([(x, 0), (x, S(H))], fill=GRID, width=1)
    for y in range(0, S(H), step):
        d.line([(0, y), (S(W), y)], fill=GRID, width=1)
    veil = Image.new("L", (S(W), S(H)), 0)
    vd = ImageDraw.Draw(veil)
    vd.ellipse([-S(120), -S(160), S(W) + S(120), S(H) + S(160)], fill=90)
    veil = veil.filter(ImageFilter.GaussianBlur(S(120)))
    dark = Image.new("RGB", (S(W), S(H)), (4, 7, 14))
    return Image.composite(img, dark, veil).convert("RGBA")


BASE = background()


def shadowed(img, spread=26, alpha=110):
    mask = img.getchannel("A").filter(ImageFilter.GaussianBlur(S(spread)))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.putalpha(mask.point(lambda v: int(v * alpha / 255)))
    return shadow


SCENE_SHADOW = {k: shadowed(v) for k, v in SCENES.items()}


def chip(d, xy, text, font, border, color):
    x, y = xy
    w = d.textlength(text, font=font) + S(28)
    d.rounded_rectangle([x, y, x + w, y + S(38)], radius=S(9), fill=(17, 26, 44), outline=border, width=S(2))
    d.text((x + S(14), y + S(10)), text, font=font, fill=color)


def headline(d, lines):
    """lines: [(текст, цвет), ...] — каждая строка своим цветом."""
    y = S(150)
    for text, color in lines:
        bbox = d.textbbox((0, 0), text, font=F_HEAD)
        x = (S(W) - (bbox[2] - bbox[0])) / 2 - bbox[0]
        d.text((x, y), text, font=F_HEAD, fill=color)
        y += S(66)


def build_phrases(marks, group=3):
    phrases = []
    i = 0
    while i < len(marks):
        chunk = marks[i:i + group]
        phrases.append({"start": chunk[0][0], "words": [c[2] for c in chunk],
                        "times": [c[0] for c in chunk]})
        i += group
    return phrases


def karaoke(d, ph, t):
    words = ph["words"]
    widths = [d.textlength(w + " ", font=F_CAP) for w in words]
    total = sum(widths)
    x = (S(W) - total) / 2
    y = S(H) - S(250)
    pad = S(18)
    d.rounded_rectangle([x - pad, y - pad, x + total + pad, y + S(46) + pad], radius=S(12), fill=(13, 20, 36))
    # уголки рамки
    for cx in (x - pad, x + total + pad):
        for cy in (y - pad, y + S(46) + pad):
            d.line([(cx - S(6), cy), (cx + S(6), cy)], fill=CYAN, width=S(2))
            d.line([(cx, cy - S(6)), (cx, cy + S(6))], fill=CYAN, width=S(2))
    active = 0
    for i, wt in enumerate(ph["times"]):
        if t >= wt:
            active = i
    for i, w in enumerate(words):
        d.text((x, y), w, font=F_CAP, fill=CYAN if i == active else (232, 238, 250))
        x += widths[i]


def main():
    os.makedirs(OUT, exist_ok=True)
    audio, marks = load_or_synthesize(TEXT, OUT)
    total = audio_duration(audio)
    phrases = build_phrases(marks)

    def sentence_times():
        tokens = TEXT.split()
        starts = []
        for idx, token in enumerate(tokens):
            if idx == 0 or tokens[idx - 1].endswith((".", "!", "?")):
                starts.append(marks[min(idx, len(marks) - 1)][0] if marks else 0.0)
        return starts

    st = sentence_times() + [total] * 10
    timeline = [
        ("l1", 0.0, ("ПРОВЕРКА", RED), ([("Уровень", WHITE), ("врёт", RED)])),
        ("l2", st[3], ("10 СЕКУНД", CYAN), ([("Переверни", WHITE), ("на 180°", CYAN)])),
        ("l3", st[5], ("РЕЗУЛЬТАТ", AMBER), ([("Плитка", WHITE), ("завалена", AMBER)])),
        ("card", st[6], ("ИТОГ", GREEN), None),
    ]
    print("voice", round(total, 2), "| сцены:", [(n, round(x, 2)) for n, x, _, _ in timeline])

    track = sfx.build_track(total, [
        (0.02, "boom", 0.45),
        (st[3], "whoosh", 0.3),
        (st[5], "crack", 0.4),
        (st[6], "chime", 0.45),
    ], os.path.join(OUT, "sfx.wav"))

    frames_dir = os.path.join(OUT, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    start = int(os.environ.get("START_FRAME", "0"))
    if start == 0:
        for f in os.listdir(frames_dir):
            os.remove(os.path.join(frames_dir, f))

    n = min(int(total * FPS), int(os.environ.get("MAX_FRAMES", "1000000")))
    for i in range(start, n):
        t = i / FPS
        frame = BASE.copy()
        d = ImageDraw.Draw(frame, "RGBA")

        idx = 0
        for k, (_, t0, _, _) in enumerate(timeline):
            if t >= t0:
                idx = k
        name, t0, (section, section_color), lines = timeline[idx]
        fade = ease(min(1.0, (t - t0) / 0.45)) if idx > 0 else 1.0

        # шапка
        chip(d, (S(28), S(30)), "ГАЙКАВИНТ", F_CHIP, (60, 74, 104), WHITE)
        chip(d, (S(28), S(78)), section, F_SECTION, section_color, section_color)

        # прогресс-бар
        bar_x, bar_y, bar_w = S(28), S(124), S(W) - S(56)
        d.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + S(7)], radius=S(4), fill=(28, 38, 60))
        filled = int(bar_w * min(1.0, t / total))
        if filled > 0:
            d.rounded_rectangle([bar_x, bar_y, bar_x + filled, bar_y + S(7)], radius=S(4), fill=CYAN)

        if name != "card":
            zoom = 1.0 + 0.04 * min(1.0, (t - t0) / 3.0)
            size = int(BOX * zoom)
            img = SCENES[name].resize((size, size), Image.LANCZOS)
            sh = SCENE_SHADOW[name].resize((size, size), Image.LANCZOS)
            px, py = (S(W) - size) // 2, ART_Y + (BOX - size) // 2
            if fade < 1.0:
                img.putalpha(img.getchannel("A").point(lambda v: int(v * fade)))
                sh.putalpha(sh.getchannel("A").point(lambda v: int(v * fade)))
            frame.alpha_composite(sh, (px + S(10), py + S(26)))
            frame.alpha_composite(img, (px, py))
        else:
            top = int(S(H) * 0.28)
            d.rectangle([0, top, S(W), top + S(430)], fill=NAVY)
            d.line([(0, top), (S(W), top)], fill=GREEN, width=S(5))
            d.text((S(48), top + S(56)), "ПРОВЕРКА —", font=F_HEAD, fill=WHITE)
            d.text((S(48), top + S(122)), "10 СЕКУНД", font=F_HEAD, fill=GREEN)
            d.line([(S(48), top + S(214)), (S(250), top + S(214))], fill=GREEN, width=S(6))
            d.text((S(48), top + S(246)), "переверни уровень —", font=F_CAP, fill=MUTED)
            d.text((S(48), top + S(294)), "пузырёк должен остаться", font=F_CAP, fill=WHITE)

        if lines:
            headline(d, lines)

        ph = phrases[0]
        for p in phrases:
            if t >= p["start"]:
                ph = p
        karaoke(d, ph, t)

        d.text((S(28), S(H) - S(56)), "Гайкавинт · Объездная 35", font=F_SMALL, fill=(90, 100, 124))

        frame.convert("RGB").resize((W, H), Image.LANCZOS).save(
            os.path.join(frames_dir, f"f{i:05d}.png"))
        if i % 250 == 0:
            print("frame", i, "/", n)

    if os.environ.get("SKIP_ENCODE"):
        print("кадры готовы")
        return

    silent = os.path.join(OUT, "video_silent.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames_dir, "f%05d.png"), "-i", audio,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                    silent], check=True)
    final = os.path.join(OUT, "final.mp4")
    sfx.mix(silent, audio, track, final, video_sfx_gain=0.7)
    print("video", final)


if __name__ == "__main__":
    main()
