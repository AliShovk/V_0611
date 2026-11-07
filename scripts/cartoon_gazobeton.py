"""Эпизод «Дюбель в газобетоне» — стройлайфхак №1.

Формат: вертикальный ролик 9:16, плоская инфографика, слово-синхронизация.
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon_engine import (FFMPEG, S, W, H, FPS, ease, lerp, audio_duration,
                            load_or_synthesize, font_path)
from cartoon_mariana import draw_caption, phrase_cues
import sfx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "storage", "cartoon-gazobeton")

CREAM = (240, 235, 223)
NAVY = (38, 48, 92)
RED = (214, 60, 45)
GREY = (150, 158, 176)
BLUE = (198, 215, 240)
SAND = (226, 214, 190)

F_MID = ImageFont.truetype(font_path(), S(64))
F_LABEL = ImageFont.truetype(font_path(), S(21))
F_TICK = ImageFont.truetype(font_path(), S(17))
F_SMALL = ImageFont.truetype(font_path(), S(14))
F_CARD = ImageFont.truetype(font_path(), S(54))

TEXT = ("В газобетон обычный дюбель не держит — он там просто проворачивается. "
        "Газобетон — это застывшая пена: плотность втрое ниже кирпича, четыреста килограммов на куб против тысячи шестисот. "
        "Поэтому стену легко проткнуть пальцем, а крепёж вырывается вместе с куском блока. "
        "Через месяц полка с таким крепежом падает вместе с телевизором. "
        "Для газобетона делают дюбели с крупной резьбой: они цепляются за весь блок, а не за крошку. "
        "Ещё надёжнее химический анкер — клей схватывает пустоты. "
        "Правило простое: если стена крошится под пальцем — обычный дюбель не ваш.")

FLOOR = int(S(H) * 0.74)


def spaced(d, xy, text, font, fill, tracking):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking


def headline(d, text, alpha=255):
    size = 92
    limit = S(W) - S(48)
    while size > 40:
        f = ImageFont.truetype(font_path(), S(size))
        bbox = d.textbbox((0, 0), text, font=f)
        if bbox[2] - bbox[0] <= limit:
            break
        size -= 4
    bbox = d.textbbox((0, 0), text, font=f)
    d.text(((S(W) - (bbox[2] - bbox[0])) / 2 - bbox[0], S(126)), text, font=f,
           fill=NAVY + (alpha,))


def wall(d, x0, y0, w, h, rows=4, cols=4, colour=NAVY):
    bw, bh = w // cols, h // rows
    for r in range(rows):
        for c in range(cols + 1):
            x = x0 + c * bw - (bw // 2 if r % 2 else 0)
            y = y0 + r * bh
            if x + bw < x0 or x > x0 + w:
                continue
            d.rectangle([max(x0, x), y, min(x0 + w, x + bw), y + bh], outline=colour, width=S(2))


def screw(d, cx, cy, angle, scale=1.0, colour=NAVY):
    """Дюбель-гвоздь: шляпка, стержень, витки резьбы."""
    s = scale
    d.ellipse([cx - S(13) * s, cy - S(13) * s, cx + S(13) * s, cy + S(13) * s], outline=colour, width=S(2))
    d.line([(cx, cy + S(11) * s), (cx, cy + S(58) * s)], fill=colour, width=S(5))
    for k in range(5):
        yy = cy + S(18 + k * 8) * s
        wob = math.sin(angle + k) * S(3)
        d.line([(cx - S(6) * s + wob, yy), (cx + S(6) * s + wob, yy)], fill=colour, width=S(2))


def shelf(d, x, y, w, tilt=0.0, alpha=255):
    """Полка с телевизором; tilt в градусах для падения."""
    layer = Image.new("RGBA", (S(W), S(H)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rectangle([x, y, x + w, y + S(10)], fill=NAVY + (alpha,))
    ld.rectangle([x + S(8), y - S(16), x + w - S(8), y], outline=NAVY + (alpha,), width=S(3))
    # телевизор
    ld.rectangle([x + S(18), y - S(74), x + w - S(18), y - S(18)], outline=NAVY + (alpha,), width=S(3))
    ld.rectangle([x + S(30), y - S(62), x + w - S(30), y - S(30)], fill=BLUE + (alpha,))
    return layer.rotate(tilt, resample=Image.BICUBIC, center=(x + w // 2, y))


def coarse_dowel(d, cx, cy, prog):
    """Спец-дюбель с крупной резьбой."""
    k = ease(prog)
    d.rounded_rectangle([cx - S(16), cy - S(46), cx + S(16), cy + S(46)], radius=S(6),
                        outline=NAVY, width=S(3))
    for i in range(6):
        yy = cy - S(36) + i * S(13) * k
        d.line([(cx - S(22), yy), (cx + S(22), yy - S(4))], fill=NAVY, width=S(3))
    d.line([(cx, cy + S(46)), (cx, cy + S(70))], fill=NAVY, width=S(4))


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
    ev = {
        "spin": st[0] + 1.2,
        "density": st[1],
        "fall": st[3],
        "fix": st[4],
        "answer": st[6],
    }
    print("voice", round(total, 2), "s | events:", {k: round(v, 2) for k, v in ev.items()})

    track = sfx.build_track(total, [
        (0.02, "boom", 0.5),
        (ev["spin"], "tick", 0.3),
        (ev["density"] + 0.4, "pop", 0.3),
        (ev["fall"], "crack", 0.45),
        (ev["fix"] - 0.2, "riser", 0.3),
        (ev["fix"] + 0.6, "pop", 0.3),
        (ev["answer"], "chime", 0.45),
    ], os.path.join(OUT, "sfx.wav"))

    frames_dir = os.path.join(OUT, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    start = int(os.environ.get("START_FRAME", "0"))
    if start == 0:
        for f in os.listdir(frames_dir):
            os.remove(os.path.join(frames_dir, f))

    n = int(total * FPS)
    n = min(n, int(os.environ.get("MAX_FRAMES", "1000000")))
    ci = 0
    for i in range(start, n):
        t = i / FPS
        while ci + 1 < len(cues) and cues[ci + 1][0] <= t:
            ci += 1
        word = cues[ci][2] if t >= cues[ci][0] - 0.05 else (cues[ci - 1][2] if ci else "")

        frame = Image.new("RGB", (S(W), S(H)), CREAM)
        d = ImageDraw.Draw(frame, "RGBA")

        # шапка
        d.ellipse([S(30), S(44), S(40), S(54)], fill=RED)
        spaced(d, (S(48), S(38)), "СТРОЙЛАЙФХАК · КРЕПЁЖ", F_LABEL, NAVY, S(2))
        d.text((S(48), S(66)), "Гайкавинт · выпуск 1", font=F_SMALL, fill=GREY)

        # пол
        d.rectangle([0, FLOOR, S(W), S(H)], fill=SAND)
        d.line([(0, FLOOR), (S(W), FLOOR)], fill=GREY, width=S(2))

        # стена из газобетона
        wall(d, S(60), S(430), S(600), S(430), rows=4, cols=4)

        # сцена 1: дюбель проворачивается
        if t < ev["density"]:
            angle = t * 9
            screw(d, S(360), S(560), angle, 1.6)
            headline(d, "Дюбель не держит")
            if t >= ev["spin"]:
                d.arc([S(300), S(500), S(420), S(620)], 40, 320, fill=RED, width=S(4))
                d.text((S(70), S(300)), "проворачивается", font=F_TICK, fill=RED)

        # сцена 2: плотность
        elif t < ev["fall"]:
            k = ease(min(1.0, (t - ev["density"]) / 0.6))
            headline(d, "400 против 1600")
            d.text((S(70), S(300)), "ПЛОТНОСТЬ, КГ/М³", font=F_TICK, fill=GREY)
            d.rectangle([S(70), S(330), S(70) + int(S(150) * k), S(380)], fill=BLUE, outline=NAVY, width=S(2))
            d.text((S(236), S(338)), "газобетон 400", font=F_TICK, fill=NAVY)
            d.rectangle([S(70), S(400), S(70) + int(S(500) * k), S(450)], fill=NAVY)
            d.text((S(586), S(408)), "кирпич 1600", font=F_TICK, fill=NAVY)

        # сцена 3: полка падает
        elif t < ev["fix"]:
            k = ease(min(1.0, (t - ev["fall"]) / 1.2))
            tilt = -18 * k
            y = int(S(520) + k * S(120))
            headline(d, "Полка падает")
            layer = shelf(d, S(150), y, S(430), tilt)
            frame = frame.convert("RGBA")
            frame.alpha_composite(layer)
            frame = frame.convert("RGB")
            d = ImageDraw.Draw(frame, "RGBA")
            if k > 0.6:
                for a in range(3):
                    d.arc([S(120 + a * 30), S(700), S(260 + a * 30), S(760)], 200, 340, fill=GREY, width=S(3))

        # сцена 4: правильный крепёж
        elif t < ev["answer"]:
            k = ease(min(1.0, (t - ev["fix"]) / 0.8))
            coarse_dowel(d, S(250), S(500), k)
            coarse_dowel(d, S(470), S(500), k)
            headline(d, "Правильный крепёж")
            d.text((S(70), S(300)), "для газобетона:", font=F_TICK, fill=GREY)
            d.text((S(70), S(330)), "крупная резьба", font=F_TICK, fill=NAVY)
            d.text((S(70), S(360)), "или химический анкер", font=F_TICK, fill=NAVY)

        # сцена 5: ответ
        else:
            k = ease(min(1.0, (t - ev["answer"]) / 0.5))
            d.rounded_rectangle([S(60), S(430), S(W) - S(60), S(700)], radius=S(18),
                                fill=NAVY + (int(235 * k),))
            d.text((S(96), S(480)), "ГАЗОБЕТОН", font=F_CARD, fill=(255, 240, 210, int(255 * k)))
            d.text((S(96), S(548)), "≠ КИРПИЧ", font=F_CARD, fill=(255, 240, 210, int(255 * k)))
            d.text((S(96), S(628)), "крошится под пальцем —\nобычный дюбель не ваш",
                   font=F_TICK, fill=(220, 228, 240, int(230 * k)))

        d.text((S(36), S(H) - S(206)), "Гайкавинт · Объездная 35", font=F_SMALL, fill=GREY)
        draw_caption(d, word, y=H - 172)
        frame.resize((W, H), Image.LANCZOS).save(os.path.join(frames_dir, f"f{i:05d}.png"))
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
