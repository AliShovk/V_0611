"""Стройлайфхак №1 — тёмная «дорогая» версия в стиле референса.

Тёмный фон с сеткой и виньеткой, плашки-чипы, прогресс-бар, крупный заголовок
с акцентным словом, объёмные SVG-иллюстрации с тенью и караоке-субтитры.
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
OUT = os.path.join(ROOT, "storage", "cartoon-gazobeton-v3")

BG = (11, 17, 32)
GRID = (23, 32, 54)
NAVY = (17, 24, 41)
CYAN = (127, 230, 242)
WHITE = (255, 255, 255)
MUTED = (154, 166, 191)
RED = (255, 91, 74)

F_CHIP = ImageFont.truetype(font_path(), S(17))
F_SECTION = ImageFont.truetype(font_path(), S(13))
F_HEAD = ImageFont.truetype(font_path(), S(52))
F_CAP = ImageFont.truetype(font_path(), S(30))
F_SMALL = ImageFont.truetype(font_path(), S(14))

TEXT = ("В газобетон обычный дюбель не держит — он там просто проворачивается. "
        "Газобетон — это застывшая пена: плотность втрое ниже кирпича, четыреста килограммов на куб против тысячи шестисот. "
        "Поэтому стену легко проткнуть пальцем, а крепёж вырывается вместе с куском блока. "
        "Через месяц полка с таким крепежом падает вместе с телевизором. "
        "Для газобетона делают дюбели с крупной резьбой: они цепляются за весь блок, а не за крошку. "
        "Ещё надёжнее химический анкер — клей схватывает пустоты. "
        "Правило простое: если стена крошится под пальцем — обычный дюбель не ваш.")

BOX = S(690)
ART_Y = S(300)


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


SCENES = {k: load("d_" + k) for k in ("wall", "chart", "fall", "fix")}


def background():
    img = Image.new("RGB", (S(W), S(H)), BG)
    d = ImageDraw.Draw(img)
    step = S(56)
    for x in range(0, S(W), step):
        d.line([(x, 0), (x, S(H))], fill=GRID, width=1)
    for y in range(0, S(H), step):
        d.line([(0, y), (S(W), y)], fill=GRID, width=1)
    # виньетка
    veil = Image.new("L", (S(W), S(H)), 0)
    vd = ImageDraw.Draw(veil)
    vd.ellipse([-S(120), -S(160), S(W) + S(120), S(H) + S(160)], fill=90)
    veil = veil.filter(ImageFilter.GaussianBlur(S(120)))
    dark = Image.new("RGB", (S(W), S(H)), (4, 7, 14))
    img = Image.composite(img, dark, veil)
    return img.convert("RGBA")


BASE = background()


def shadowed(img, spread=26, alpha=110):
    """Тень под иллюстрацией: размытый силуэт со смещением."""
    mask = img.getchannel("A").filter(ImageFilter.GaussianBlur(S(spread)))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.putalpha(mask.point(lambda v: int(v * alpha / 255)))
    return shadow


SCENE_SHADOW = {k: shadowed(v) for k, v in SCENES.items()}


def chip(d, xy, text, font, fill_border, fill_text, pad=S(14)):
    x, y = xy
    w = d.textlength(text, font=font) + pad * 2
    h = S(38)
    d.rounded_rectangle([x, y, x + w, y + h], radius=S(9), fill=(17, 26, 44), outline=fill_border, width=S(2))
    d.text((x + pad, y + S(10)), text, font=font, fill=fill_text)
    return w


def headline(d, lines, accent):
    y = S(150)
    for line in lines:
        words = line.split()
        total = sum(d.textlength(w + " ", font=F_HEAD) for w in words)
        x = (S(W) - total) / 2
        for w in words:
            color = CYAN if w.strip(".,!—").lower() == accent.lower() else WHITE
            d.text((x, y), w + " ", font=F_HEAD, fill=color)
            x += d.textlength(w + " ", font=F_HEAD)
        y += S(64)


def karaoke(d, phrases, t):
    """Текущая фраза; активное слово — бирюзовое."""
    idx = 0
    for i, ph in enumerate(phrases):
        if t >= ph["start"]:
            idx = i
    ph = phrases[idx]
    words = ph["words"]
    widths = [d.textlength(w + " ", font=F_CAP) for w in words]
    total = sum(widths)
    x0 = (S(W) - total) / 2
    y = S(H) - S(150)
    pad = S(18)
    d.rounded_rectangle([x0 - pad, y - pad, x0 + total + pad, y + S(46) + pad],
                        radius=S(14), fill=(13, 20, 36))
    x = x0
    active = ph["active"]
    for i, w in enumerate(words):
        color = CYAN if i == active else (232, 238, 250)
        d.text((x, y), w, font=F_CAP, fill=color)
        x += widths[i]


def build_phrases(marks, group=3):
    phrases = []
    i = 0
    while i < len(marks):
        chunk = marks[i:i + group]
        start = chunk[0][0]
        phrases.append({"start": start, "words": [c[2] for c in chunk],
                        "times": [c[0] for c in chunk], "active": 0})
        i += group
    return phrases


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
    timeline = [("wall", 0.0, (["Дюбель", "не держит"], "держит")),
                ("chart", st[1], (["400", "против 1600"], "1600")),
                ("fall", st[3], (["Полка", "падает"], "падает")),
                ("fix", st[4], (["Правильный", "крепёж"], "крепёж")),
                ("card", st[6], (None, None))]
    print("voice", round(total, 2), "| сцены:", [(n, round(x, 2)) for n, x, _ in timeline])

    track = sfx.build_track(total, [
        (0.02, "boom", 0.45),
        (st[1], "pop", 0.3),
        (st[3], "crack", 0.4),
        (st[4], "whoosh", 0.3),
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
        for k, (_, t0, _) in enumerate(timeline):
            if t >= t0:
                idx = k
        name, t0, (lines, accent) = timeline[idx]
        fade = ease(min(1.0, (t - t0) / 0.45)) if idx > 0 else 1.0

        # шапка
        chip(d, (S(28), S(30)), "ГАЙКАВИНТ", F_CHIP, (60, 74, 104), WHITE)
        chip(d, (S(W) - S(150), S(30)), "КРЕПЁЖ", F_SECTION, (42, 120, 134), CYAN)
        # прогресс
        bar_x, bar_y, bar_w = S(28), S(84), S(W) - S(56)
        d.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + S(6)], radius=S(3), fill=(28, 38, 60))
        d.rounded_rectangle([bar_x, bar_y, bar_x + int(bar_w * t / total), bar_y + S(6)],
                            radius=S(3), fill=CYAN)

        # иллюстрация с тенью и лёгким зумом
        if name != "card":
            zoom = 1.0 + 0.04 * min(1.0, (t - t0) / 3.0) if idx > 0 else 1.0 + 0.02 * t / 3
            size = int(BOX * zoom)
            img = SCENES[name].resize((size, size), Image.LANCZOS)
            sh = SCENE_SHADOW[name].resize((size, size), Image.LANCZOS)
            px = (S(W) - size) // 2
            py = ART_Y + (BOX - size) // 2
            if fade < 1.0:
                img.putalpha(img.getchannel("A").point(lambda v: int(v * fade)))
                sh.putalpha(sh.getchannel("A").point(lambda v: int(v * fade)))
            frame.alpha_composite(sh, (px + S(12), py + S(28)))
            frame.alpha_composite(img, (px, py))
        else:
            k = ease(min(1.0, (t - t0) / 0.4))
            top = int(S(H) * 0.30)
            d.rectangle([0, top, S(W), top + S(440)], fill=NAVY)
            d.line([(0, top), (S(W), top)], fill=CYAN, width=S(5))
            d.text((S(48), top + S(60)), "ГАЗОБЕТОН", font=F_HEAD, fill=CYAN)
            d.text((S(48), top + S(124)), "≠ КИРПИЧ", font=F_HEAD, fill=WHITE)
            d.line([(S(48), top + S(220)), (S(260), top + S(220))], fill=RED, width=S(6))
            d.text((S(48), top + S(250)), "крошится под пальцем —", font=F_CAP, fill=MUTED)
            d.text((S(48), top + S(296)), "обычный дюбель не ваш", font=F_CAP, fill=WHITE)

        if lines:
            headline(d, lines, accent)

        if name == "fix":
            d.text((S(66), S(1000)), "крупная резьба", font=F_SECTION, fill=MUTED)
            d.text((S(452), S(1000)), "химический анкер", font=F_SECTION, fill=MUTED)

        # караоке
        ph = phrases[0]
        for i2, p in enumerate(phrases):
            if t >= p["start"]:
                ph = p
        active = 0
        for i2, wt in enumerate(ph["times"]):
            if t >= wt:
                active = i2
        ph["active"] = active
        karaoke(d, [ph], t)

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
