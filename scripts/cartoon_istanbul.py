"""Эпизод «Стамбульский марафон» — инфографика в стиле плоского контура.

Кремовый верх, голубая вода, тёмно-синие линии, крупные цифры и подпись события.
Всё привязано к словам озвучки (word boundaries Edge TTS).
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
OUT = os.path.join(ROOT, "storage", "cartoon-istanbul")

CREAM = (240, 235, 223)
WATER = (198, 215, 240)
NAVY = (38, 48, 92)
RED = (214, 60, 45)
GREY = (150, 158, 176)

F_BIG = ImageFont.truetype(font_path(), S(96))
F_MID = ImageFont.truetype(font_path(), S(64))
F_LABEL = ImageFont.truetype(font_path(), S(21))
F_TICK = ImageFont.truetype(font_path(), S(17))
F_SMALL = ImageFont.truetype(font_path(), S(14))

TEXT = ("Из Азии в Европу — за одно утро. "
        "А придумали этот марафон в 1979 году: немецкие туристы приезжают в Стамбул с безумной идеей. "
        "34 туриста и турецкие бегуны стартуют в Азии — и впервые марафон бежит по мосту через Босфор. "
        "Первым финиширует турок Хасан Сайлан: два часа тридцать пять минут. "
        "Так родился единственный марафон на двух континентах. "
        "Сначала — «Азия — Европа», потом «Евразийский», а с 2013 года — Стамбульский. "
        "В 2011-м толпа бегунов раскачала мост: после этого массовому забегу запретили по нему бежать — только идти. "
        "Этой осенью — сорок восьмой старт.")

HORIZON = int(S(H) * 0.60)


def word_time(marks, needle, default, occurrence=1):
    needle = needle.lower()
    seen = 0
    for (start, dur, word) in marks:
        clean = word.lower().strip(".,!?—:;«»()")
        if needle in clean:
            seen += 1
            if seen == occurrence:
                return start
    return default


def spaced(d, xy, text, font, fill, tracking):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking


def waves(d, phase):
    for row, y in enumerate(range(HORIZON + S(16), S(H), S(26))):
        dash = S(14)
        gap = S(10)
        shift = int((phase * 18 + row * 11) % (dash + gap))
        x = -dash + shift
        while x < S(W):
            d.arc([x, y, x + dash, y + S(8)], 200, 340, fill=(172, 192, 228), width=S(2))
            x += dash + gap


def skyline(d, x0, colour, width):
    """Силуэт города: дома, купол мечети, два минарета."""
    base = HORIZON
    x = x0
    for w, h in ((64, 92), (54, 70), (74, 104)):
        d.rectangle([x, base - S(h), x + S(w), base], outline=colour, width=width)
        for r in range(2):
            for c in range(2):
                wx, wy = x + S(9) + c * S(18), base - S(h) + S(12) + r * S(22)
                d.rectangle([wx, wy, wx + S(8), wy + S(10)], outline=colour, width=width)
        x += S(w) + S(12)

    # мечеть
    cx = x + S(74)
    d.rectangle([cx - S(58), base - S(60), cx + S(58), base], outline=colour, width=width)
    d.arc([cx - S(58), base - S(118), cx + S(58), base - S(30)], 180, 360, fill=colour, width=width)
    for mx in (cx - S(80), cx + S(80)):
        d.line([(mx, base), (mx, base - S(150))], fill=colour, width=width)
        d.ellipse([mx - S(4), base - S(159), mx + S(4), base - S(151)], fill=colour)
    x = cx + S(104)

    for w, h in ((56, 72), (70, 96), (52, 62)):
        d.rectangle([x, base - S(h), x + S(w), base], outline=colour, width=width)
        x += S(w) + S(12)


def bridge(d, prog, sway, colour, width):
    """Висячий мост: пилоны, настил и провисающие тросы."""
    if prog <= 0:
        return
    deck_y = HORIZON - S(38)
    x1, x2 = S(80), S(W) - S(80)
    sway = int(sway)
    tower = S(168) * prog
    for tx in (x1, x2):
        d.line([(tx + sway, deck_y), (tx + sway, deck_y - tower)], fill=colour, width=width + 1)
        d.line([(tx - S(9) + sway, deck_y - tower), (tx + S(9) + sway, deck_y - tower)], fill=colour, width=width)
        d.line([(tx - S(9) + sway, deck_y - tower * 0.62), (tx + S(9) + sway, deck_y - tower * 0.62)],
               fill=colour, width=width)
    # настил
    d.line([(x1 + sway, deck_y), (x2 + sway, deck_y)], fill=colour, width=width + 1)
    # два пролёта тросов (провис вниз)
    mid = (x1 + x2) // 2
    for a, b in ((x1, mid), (mid, x2)):
        pts = []
        for i in range(0, 21):
            k = i / 20
            px = a + (b - a) * k
            py = deck_y - tower + math.sin(math.pi * k) * tower * 0.72 * prog
            pts.append((px + sway, py))
        d.line(pts, fill=colour, width=width, joint="curve")
        for i in range(1, 10):
            k = i / 10
            px = a + (b - a) * k
            py = deck_y - tower + math.sin(math.pi * k) * tower * 0.72 * prog
            d.line([(px + sway, py), (px + sway, deck_y)], fill=colour, width=max(1, width - 1))


def runner(d, x, y, colour, phase, scale=1.0):
    """Бегущая фигурка из линий."""
    s = scale
    bob = math.sin(phase * 6) * S(2)
    y += bob
    d.ellipse([x - S(6) * s, y - S(46) * s, x + S(6) * s, y - S(34) * s], outline=colour, width=S(2))
    d.line([(x, y - S(34) * s), (x, y - S(16) * s)], fill=colour, width=S(2))
    arm = math.sin(phase * 6) * S(10)
    d.line([(x, y - S(30) * s), (x + arm, y - S(18) * s)], fill=colour, width=S(2))
    d.line([(x, y - S(30) * s), (x - arm, y - S(18) * s)], fill=colour, width=S(2))
    leg = math.sin(phase * 6) * S(9)
    d.line([(x, y - S(16) * s), (x + leg, y)], fill=colour, width=S(2))
    d.line([(x, y - S(16) * s), (x - leg, y)], fill=colour, width=S(2))


def headline(d, text, alpha=255, scale=1.0):
    """Крупный заголовок, который сам ужимается под ширину кадра."""
    size = 96
    limit = S(W) - S(48)
    while size > 40:
        f = ImageFont.truetype(font_path(), S(size))
        bbox = d.textbbox((0, 0), text, font=f)
        if bbox[2] - bbox[0] <= limit:
            break
        size -= 4
    bbox = d.textbbox((0, 0), text, font=f)
    x = (S(W) - (bbox[2] - bbox[0])) / 2 - bbox[0]
    d.text((x, S(126)), text, font=f, fill=NAVY + (alpha,))


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
        "hook": 0.0,
        "y1979": st[1],
        "tourists": st[2],
        "bridge": st[2] + 2.2,
        "sailan": st[3],
        "time235": st[3] + 1.4,
        "continent": st[4],
        "names": st[5],
        "sway": st[6],
        "final": st[7],
    }
    print("voice", round(total, 2), "s | events:", {k: round(v, 2) for k, v in ev.items()})

    sfx_events = [
        (0.02, "boom", 0.5),
        (0.02, "whoosh", 0.35),
        (ev["y1979"], "pop", 0.35),
        (ev["tourists"], "pop", 0.35),
        (ev["bridge"] - 0.2, "whoosh", 0.35),
        (ev["time235"], "tick", 0.3),
        (ev["continent"], "chime", 0.3),
        (ev["names"], "pop", 0.25),
        (ev["sway"], "crack", 0.35),
        (ev["final"] - 0.4, "riser", 0.3),
        (ev["final"], "chime", 0.45),
    ]
    track = sfx.build_track(total, sfx_events, os.path.join(OUT, "sfx.wav"))

    frames_dir = os.path.join(OUT, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    start = int(os.environ.get("START_FRAME", "0"))
    if start == 0:
        for f in os.listdir(frames_dir):
            os.remove(os.path.join(frames_dir, f))

    n = int(total * FPS)
    n = min(n, int(os.environ.get("MAX_FRAMES", "1000000")))
    end = n
    ci = 0
    for i in range(start, end):
        t = i / FPS
        while ci + 1 < len(cues) and cues[ci + 1][0] <= t:
            ci += 1
        word = cues[ci][2] if t >= cues[ci][0] - 0.05 else (cues[ci - 1][2] if ci else "")

        frame = Image.new("RGB", (S(W), S(H)), CREAM)
        d = ImageDraw.Draw(frame, "RGBA")

        # вода
        d.rectangle([0, HORIZON, S(W), S(H)], fill=WATER)
        waves(d, t)

        # шапка
        d.ellipse([S(30), S(44), S(40), S(54)], fill=RED)
        spaced(d, (S(48), S(38)), "ИСТОРИЯ · СТАМБУЛЬСКИЙ МАРАФОН", F_LABEL, NAVY, S(2))
        d.text((S(48), S(66)), "1979 → 2026", font=F_SMALL, fill=GREY)

        # сцена: город появляется в начале
        city_in = ease(min(1.0, t / 1.2))
        skyline(d, S(20) - int((1 - city_in) * S(60)), NAVY, S(2))

        # мост
        bp = ease(min(1.0, t / 1.4))
        sway = 0.0
        if t >= ev["sway"]:
            sway = math.sin((t - ev["sway"]) * 6.0) * S(4) * max(0.0, 1 - (t - ev["sway"]) / 3.0) + S(2)
        bridge(d, bp, sway, NAVY, S(2))

        # бегуны по мосту
        if bp > 0.6:
            for k, off in enumerate((0.0, 0.06, 0.12)):
                prog = ((t * 0.10 + off) % 1.0)
                rx = S(96) + (S(W) - S(200)) * prog
                runner(d, rx, HORIZON - S(39), NAVY, t + k, 1.2)

        # подписи континентов
        if t >= ev["bridge"]:
            d.text((S(24), HORIZON + S(28)), "ЕВРОПА", font=F_LABEL, fill=NAVY)
            d.text((S(W) - S(104), HORIZON + S(28)), "АЗИЯ", font=F_LABEL, fill=NAVY)

        # крупные цифры/заголовки по сценам
        if t < ev["y1979"] - 0.2:
            headline(d, "Из Азии в Европу")
        elif t < ev["tourists"] - 0.2:
            headline(d, "1979")
        elif t < ev["bridge"]:
            headline(d, "34 туриста")
        elif t < ev["sailan"] - 0.2:
            headline(d, "Босфор")
            d.text((S(48), S(236)), "первый забег по мосту", font=F_TICK, fill=NAVY)
        elif t < ev["continent"] - 0.2:
            headline(d, "2 ч 35 мин")
            d.text((S(48), S(236)), "Хасан Сайлан, первый финишёр", font=F_TICK, fill=NAVY)
        elif t < ev["names"] - 0.2:
            headline(d, "Два континента")
        elif t < ev["sway"] - 0.3:
            label = "Азия — Европа"
            if t >= ev["names"] + 1.8:
                label = "Евразийский"
            if t >= ev["names"] + 3.6:
                label = "Стамбульский"
            headline(d, label)
        elif t < ev["final"] - 0.3:
            headline(d, "2011: мост раскачали")
            d.text((S(48), S(236)), "массовому забегу — только идти", font=F_TICK, fill=NAVY)
        else:
            headline(d, "48-й старт")

        # источник
        d.text((S(36), S(H) - S(206)), "источник: IIS · germanroadraces.de", font=F_SMALL, fill=GREY)

        draw_caption(d, word, y=H - 172)
        frame.resize((W, H), Image.LANCZOS).save(os.path.join(frames_dir, f"f{i:05d}.png"))
        if i % 250 == 0:
            print("frame", i, "/", n)

    if os.environ.get("SKIP_ENCODE"):
        print("кадры готовы:", start, "-", end)
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
