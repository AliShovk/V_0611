"""Стройлайфхак №1 «Дюбель в газобетоне» — чистая векторная версия.

Иллюстрации — SVG (art/gazo/*.svg), растеризованы Inkscape в 1200px.
Сцены меняются кросс-фейдом, без наложений и прозрачных карточек.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon_engine import (FFMPEG, S, W, H, FPS, ease, audio_duration,
                            load_or_synthesize, font_path)
from cartoon_mariana import phrase_cues
import sfx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "art", "gazo")
OUT = os.path.join(ROOT, "storage", "cartoon-gazobeton-v2")

CREAM = (244, 240, 231)
NAVY = (38, 48, 92)
RED = (214, 60, 45)
GREY = (138, 144, 160)
BLUE = (198, 215, 240)

F_HEAD = ImageFont.truetype(font_path(), S(20))
F_SMALL = ImageFont.truetype(font_path(), S(15))
F_CARD = ImageFont.truetype(font_path(), S(58))
F_CARD_SUB = ImageFont.truetype(font_path(), S(24))

TEXT = ("В газобетон обычный дюбель не держит — он там просто проворачивается. "
        "Газобетон — это застывшая пена: плотность втрое ниже кирпича, четыреста килограммов на куб против тысячи шестисот. "
        "Поэтому стену легко проткнуть пальцем, а крепёж вырывается вместе с куском блока. "
        "Через месяц полка с таким крепежом падает вместе с телевизором. "
        "Для газобетона делают дюбели с крупной резьбой: они цепляются за весь блок, а не за крошку. "
        "Ещё надёжнее химический анкер — клей схватывает пустоты. "
        "Правило простое: если стена крошится под пальцем — обычный дюбель не ваш.")

IMG_W = S(660)
IMG_Y = S(250)


def load(name):
    img = Image.open(os.path.join(ART, name + ".png")).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    # вписываем в квадрат 620x620 без искажений
    box = S(660)
    ratio = min(box / img.width, box / img.height)
    img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.LANCZOS)
    canvas = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    canvas.alpha_composite(img, ((box - img.width) // 2, (box - img.height) // 2))
    return canvas


SCENES = {k: load(k) for k in ("wall", "chart", "fall", "fix")}


def spaced(d, xy, text, font, fill, tracking):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking


def headline(d, text, alpha=255):
    size = 84
    limit = S(W) - S(48)
    while size > 38:
        f = ImageFont.truetype(font_path(), S(size))
        bbox = d.textbbox((0, 0), text, font=f)
        if bbox[2] - bbox[0] <= limit:
            break
        size -= 4
    bbox = d.textbbox((0, 0), text, font=f)
    d.text(((S(W) - (bbox[2] - bbox[0])) / 2 - bbox[0], S(120)), text, font=f,
           fill=NAVY + (alpha,))


def caption(d, text):
    """Субтитр: белый текст на плотной плашке, всегда внутри кадра."""
    if not text:
        return
    size = 34
    limit = S(W) - S(120)
    while size > 24:
        f = ImageFont.truetype(font_path(), S(size))
        if d.textbbox((0, 0), text, font=f)[2] <= limit:
            break
        size -= 2
    f = ImageFont.truetype(font_path(), S(size))
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = S(22), S(14)
    w = tw + pad_x * 2
    h = th + pad_y * 2
    x0 = (S(W) - w) / 2
    y0 = S(H) - S(140) - h / 2
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=S(14), fill=NAVY)
    d.text((x0 + pad_x - bbox[0], y0 + pad_y - bbox[1]), text, font=f, fill=(255, 255, 255))


def paste_scene(frame, name, alpha=255, dy=0):
    if alpha <= 0 or name == "card":
        return
    layer = SCENES[name].copy()
    if alpha < 255:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha / 255)))
    frame.alpha_composite(layer, (S(50), IMG_Y + dy))


def main():
    os.makedirs(OUT, exist_ok=True)
    audio, marks = load_or_synthesize(TEXT, OUT)
    total = audio_duration(audio)
    cues = phrase_cues(marks, TEXT)

    def sentence_times():
        tokens = TEXT.split()
        starts = []
        for idx, token in enumerate(tokens):
            if idx == 0 or tokens[idx - 1].endswith((".", "!", "?")):
                starts.append(marks[min(idx, len(marks) - 1)][0] if marks else 0.0)
        return starts

    st = sentence_times() + [total] * 10
    timeline = [
        ("wall", 0.0),
        ("chart", st[1]),
        ("fall", st[3]),
        ("fix", st[4]),
        ("card", st[6]),
    ]
    print("voice", round(total, 2), "s | сцены:", [(n, round(t, 2)) for n, t in timeline])

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
    ci = 0
    for i in range(start, n):
        t = i / FPS
        while ci + 1 < len(cues) and cues[ci + 1][0] <= t:
            ci += 1
        word = cues[ci][2] if t >= cues[ci][0] - 0.05 else (cues[ci - 1][2] if ci else "")

        frame = Image.new("RGBA", (S(W), S(H)), CREAM + (255,))
        d = ImageDraw.Draw(frame, "RGBA")

        # какой сцене принадлежит кадр
        idx = 0
        for k, (_, t0) in enumerate(timeline):
            if t >= t0:
                idx = k
        name, t0 = timeline[idx]
        fade = ease(min(1.0, (t - t0) / 0.45)) if idx > 0 else 1.0

        if idx > 0 and fade < 1.0:
            paste_scene(frame, timeline[idx - 1][0], alpha=int(255 * (1 - fade)))
        paste_scene(frame, name, alpha=int(255 * fade), dy=int((1 - fade) * S(14)))

        d = ImageDraw.Draw(frame, "RGBA")

        # шапка и низ
        d.ellipse([S(30), S(44), S(40), S(54)], fill=RED)
        spaced(d, (S(48), S(38)), "СТРОЙЛАЙФХАК · КРЕПЁЖ", F_HEAD, NAVY, S(2))
        d.text((S(48), S(68)), "Гайкавинт · выпуск 1", font=F_SMALL, fill=GREY)
        d.text((S(36), S(H) - S(276)), "Гайкавинт · Объездная 35", font=F_SMALL, fill=GREY)

        # подписи под сценами
        if name == "fix" and fade > 0.4:
            d.text((S(70), S(940)), "крупная резьба", font=F_SMALL, fill=NAVY)
            d.text((S(420), S(940)), "химический анкер", font=F_SMALL, fill=NAVY)

        # заголовки
        if name == "wall":
            headline(d, "Дюбель не держит")
        elif name == "chart":
            headline(d, "400 против 1600")
        elif name == "fall":
            headline(d, "Полка падает")
        elif name == "fix":
            headline(d, "Правильный крепёж")

        # финальная карточка — плотная плашка
        if name == "card":
            k = ease(min(1.0, (t - t0) / 0.4))
            top = int(S(H) * 0.34)
            d.rectangle([0, top, S(W), top + S(430)], fill=NAVY)
            d.text((S(56), top + S(70)), "ГАЗОБЕТОН", font=F_CARD, fill=(255, 244, 220))
            d.text((S(56), top + S(150)), "≠ КИРПИЧ", font=F_CARD, fill=(255, 244, 220))
            d.line([(S(56), top + S(240)), (S(300), top + S(240))], fill=(255, 200, 120), width=S(6))
            d.text((S(56), top + S(270)), "крошится под пальцем —", font=F_CARD_SUB, fill=(226, 232, 244))
            d.text((S(56), top + S(312)), "обычный дюбель не ваш", font=F_CARD_SUB, fill=(226, 232, 244))

        caption(d, word)
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
