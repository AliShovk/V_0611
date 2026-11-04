"""Эпизод «Молния» — 30 000 °C против 5 800 °C у Солнца.

Каждое действие в кадре привязано к конкретному слову в озвучке:
слово найдено в word-boundary разметке Edge TTS -> берётся его время старта.
"""
import math
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon_engine import FFMPEG, S, W, H, FPS, ease, lerp, synthesize, audio_duration, font_path
from cartoon_mariana import draw_caption, phrase_cues

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "art")
OUT = os.path.join(ROOT, "storage", "cartoon-lightning")
F_LABEL = ImageFont.truetype(font_path(), S(30))
F_TICK = ImageFont.truetype(font_path(), S(23))
F_BIG = ImageFont.truetype(font_path(), S(46))

TEXT = ("Внутри грозовой тучи накапливается заряд. "
        "Когда напряжение пробивает воздух, бьёт молния. "
        "В канале молнии температура до тридцати тысяч градусов. "
        "Это в пять раз горячее поверхности Солнца. "
        "Воздух вокруг мгновенно расширяется — мы слышим гром. "
        "И всё это длится меньше секунды. "
        "Самая длинная молния растянулась на семьсот километров.")

BG = Image.open(os.path.join(ART, "storm.png")).convert("RGBA").resize((S(W), S(H)), Image.LANCZOS)
BOLT = Image.open(os.path.join(ART, "bolt.png")).convert("RGBA")
SUN = Image.open(os.path.join(ART, "sun.png")).convert("RGBA")

BOLT_H = int(S(H) * 0.52)
BOLT_IMG = BOLT.resize((int(BOLT.width * BOLT_H / BOLT.height), BOLT_H), Image.LANCZOS)
BOLT_X = int(S(W) * 0.40)
BOLT_Y = int(S(H) * 0.20)
SUN_H = int(S(W) * 0.185)
SUN_IMG = SUN.resize((SUN_H, SUN_H), Image.LANCZOS)

STRIKE_POINT = (BOLT_X + BOLT_IMG.width // 2 - int(S(W) * 0.02), BOLT_Y + BOLT_H)


def word_time(marks, needle, default):
    """Время первого произнесённого слова, содержащего needle."""
    needle = needle.lower()
    for (start, dur, word) in marks:
        clean = word.lower().strip(".,!?—:;«»()")
        if clean.startswith(needle) or needle in clean:
            return start
    return default


def main():
    os.makedirs(OUT, exist_ok=True)
    audio, marks = synthesize(TEXT, OUT)
    total = audio_duration(audio)
    cues = phrase_cues(marks, TEXT)

    ev = {
        "charge": word_time(marks, "накапливается", total * 0.10),
        "crack": word_time(marks, "пробивает", total * 0.24),
        "strike": word_time(marks, "молния", total * 0.32),
        "temp": word_time(marks, "тридцати", total * 0.44),
        "sun": word_time(marks, "солнца", total * 0.56),
        "thunder": word_time(marks, "гром", total * 0.68),
        "second": word_time(marks, "секунды", total * 0.78),
        "long": word_time(marks, "семьсот", total * 0.88),
    }
    print("voice", round(total, 2), "s | events:", {k: round(v, 2) for k, v in ev.items()})

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

        frame = BG.copy()
        d = ImageDraw.Draw(frame, "RGBA")

        # --- 1. заряд в туче ---
        if t >= ev["charge"] - 0.15:
            k = ease(min(1.0, (t - ev["charge"] + 0.15) / max(0.6, ev["strike"] - ev["charge"])))
            rnd = random.Random(int(t * 6))
            for j in range(int(3 + k * 7)):
                ax = rnd.uniform(0.08, 0.92) * S(W)
                ay = rnd.uniform(0.17, 0.28) * S(H)
                ln = rnd.uniform(S(14), S(30)) * (0.5 + k)
                d.line([(ax, ay), (ax + rnd.uniform(-1, 1) * ln, ay + ln * 0.8)],
                       fill=(190, 230, 255, int(120 + 120 * k)), width=S(2))

        # --- 2. пробой ---
        if t >= ev["crack"]:
            k = ease(min(1.0, (t - ev["crack"]) / max(0.25, ev["strike"] - ev["crack"])))
            glow = int(70 * k)
            d.rectangle([0, S(H) * 0.16, S(W), S(H) * 0.44], fill=(150, 205, 255, glow))

        # --- 3. удар ---
        if t >= ev["strike"]:
            dt = t - ev["strike"]
            flicker = 1.0 if dt < 0.18 else (0.55 if (dt % 0.22) < 0.09 else 1.0)
            if dt < 2.2:
                alpha = int(255 * flicker * max(0.25, 1 - dt / 2.4))
                bolt = BOLT_IMG.copy()
                bolt.putalpha(bolt.getchannel("A").point(lambda v: int(v * alpha / 255)))
                frame.alpha_composite(bolt, (BOLT_X, BOLT_Y))
                if dt < 0.16:
                    d.rectangle([0, 0, S(W), S(H)], fill=(235, 245, 255, int(150 * (1 - dt / 0.16))))
            # след канала: держится, пока говорим про температуру
            else:
                hold = max(0.0, ev["sun"] - t)
                base = 0.34 if hold > 0 else 0.14
                a = base + 0.06 * math.sin(t * 9.0)
                ghost = BOLT_IMG.copy()
                ghost.putalpha(ghost.getchannel("A").point(lambda v: int(v * a)))
                frame.alpha_composite(ghost, (BOLT_X, BOLT_Y))

        # --- 4. температура ---
        if t >= ev["temp"]:
            k = ease(min(1.0, (t - ev["temp"]) / 0.5))
            px, py = S(44), int(S(H) * 0.155)
            d.rounded_rectangle([px, py, px + S(330), py + S(112)], radius=S(16),
                                fill=(12, 14, 24, int(225 * k)))
            d.text((px + S(16), py + S(12)), "30 000 °C", font=F_BIG, fill=(255, 232, 160))
            d.text((px + S(18), py + S(74)), "в канале молнии", font=F_TICK, fill=(186, 214, 245))

        # --- 5. Солнце ---
        if t >= ev["sun"]:
            k = ease(min(1.0, (t - ev["sun"]) / 0.7))
            sx = S(W) - SUN_IMG.width - S(46)
            sy = int(S(H) * 0.145)
            sun = SUN_IMG.copy()
            sun.putalpha(sun.getchannel("A").point(lambda v: int(v * k)))
            frame.alpha_composite(sun, (sx, sy))
            d.text((sx - S(6), sy + SUN_IMG.height + S(6)), "5 800 °C", font=F_LABEL,
                   fill=(255, 226, 170), stroke_width=S(3), stroke_fill=(10, 12, 20))
            d.text((sx - S(6), sy + SUN_IMG.height + S(48)), "Солнце", font=F_TICK,
                   fill=(206, 226, 246), stroke_width=S(3), stroke_fill=(10, 12, 20))
            if k > 0.7:
                d.text((S(58), int(S(H) * 0.245)), "в 5 раз горячее", font=F_LABEL,
                       fill=(255, 232, 160), stroke_width=S(3), stroke_fill=(10, 12, 20))

        # --- 6. гром: ударная волна ---
        if t >= ev["thunder"]:
            dt = t - ev["thunder"]
            for r_i in range(3):
                age = (dt - r_i * 0.28) % 1.6
                if age < 0:
                    continue
                rr = S(28) + age * S(148)
                alpha = int(120 * max(0.0, 1 - age / 1.6))
                d.ellipse([STRIKE_POINT[0] - rr, STRIKE_POINT[1] - rr * 0.42,
                           STRIKE_POINT[0] + rr, STRIKE_POINT[1] + rr * 0.42],
                          outline=(255, 240, 200, alpha), width=S(4))
            if dt < 1.6:
                d.text((STRIKE_POINT[0] - S(52), STRIKE_POINT[1] + S(26)), "гром", font=F_LABEL,
                       fill=(255, 226, 170))

        # --- 7. длительность ---
        if t >= ev["second"]:
            k = ease(min(1.0, (t - ev["second"]) / 0.45))
            bx, by = S(44), int(S(H) * 0.325)
            d.rounded_rectangle([bx, by, bx + S(320), by + S(96)], radius=S(14),
                                fill=(12, 14, 24, int(215 * k)))
            d.text((bx + S(16), by + S(10)), "≈ 0,2 секунды", font=F_LABEL, fill=(206, 236, 255))
            d.text((bx + S(16), by + S(52)), "длится один разряд", font=F_TICK, fill=(150, 186, 220))

        # --- 8. самая длинная молния ---
        if t >= ev["long"]:
            k = ease(min(1.0, (t - ev["long"]) / 0.8))
            width = int(S(W) * 1.1 * k)
            horiz = BOLT_IMG.rotate(90, expand=True)
            horiz = horiz.resize((max(8, width), int(horiz.height * 0.36)), Image.LANCZOS)
            frame.alpha_composite(horiz, (int(S(W) * 0.02), int(S(H) * 0.50)))
            if k > 0.6:
                d.rounded_rectangle([S(44), int(S(H) * 0.545), S(400), int(S(H) * 0.545) + S(74)],
                                    radius=S(12), fill=(12, 14, 24, 215))
                d.text((S(60), int(S(H) * 0.545) + S(16)), "709 км — рекорд", font=F_LABEL,
                       fill=(255, 226, 170))

        draw_caption(d, word, y=S(H) - S(150))
        frame.convert("RGB").resize((W, H), Image.LANCZOS).save(
            os.path.join(frames_dir, f"f{i:05d}.png"))
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
