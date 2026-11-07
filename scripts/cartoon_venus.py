"""Эпизод «Венера» — сутки длиннее года. 35 секунд.

Как и в «Молнии»: каждое действие привязано к слову из озвучки
(word-boundary разметка Edge TTS), а не к доле таймлайна.
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon_engine import FFMPEG, S, W, H, FPS, ease, lerp, synthesize, audio_duration, load_or_synthesize, font_path
from cartoon_mariana import draw_caption, phrase_cues

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "art")
OUT = os.path.join(ROOT, "storage", "cartoon-venus")
F_LABEL = ImageFont.truetype(font_path(), S(30))
F_TICK = ImageFont.truetype(font_path(), S(23))
F_BIG = ImageFont.truetype(font_path(), S(54))
F_HUGE = ImageFont.truetype(font_path(), S(64))

TEXT = ("Сутки на этой планете длиннее года. "
        "И Солнце там встаёт на западе. "
        "Она проворачивается вокруг оси двести сорок три земных дня, "
        "а год длится всего двести двадцать пять. "
        "Под облаками из серной кислоты поверхность раскалена до четырёхсот шестидесяти четырёх градусов, "
        "а давление — как на километровой глубине океана. "
        "Она ближе к Солнцу, чем Земля, но не самая близкая. "
        "Что это за планета? Венера.")

BG = Image.open(os.path.join(ART, "space.png")).convert("RGBA").resize((S(W), S(H)), Image.LANCZOS)
VENUS = Image.open(os.path.join(ART, "venus.png")).convert("RGBA")
SUN = Image.open(os.path.join(ART, "sun.png")).convert("RGBA")
MERC = Image.open(os.path.join(ART, "mercury.png")).convert("RGBA")

VEN_D = int(S(W) * 0.44)
VENUS_IMG = VENUS.resize((VEN_D, VEN_D), Image.LANCZOS)
VEN_CX, VEN_CY = S(W) // 2, int(S(H) * 0.36)
SUN_D = int(S(W) * 0.15)
SUN_IMG = SUN.resize((SUN_D, SUN_D), Image.LANCZOS)
MERC_D = int(S(W) * 0.10)
MERC_IMG = MERC.resize((MERC_D, MERC_D), Image.LANCZOS)
SUN_POS = (S(W) - SUN_D - S(34), S(60))


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


def card(d, x, y, w, h, alpha=225):
    d.rounded_rectangle([x, y, x + w, y + h], radius=S(16), fill=(10, 14, 28, alpha))


def arrow_arc(d, cx, cy, r, a0, a1, colour, width, arrow=True):
    box = [cx - r, cy - r, cx + r, cy + r]
    d.arc(box, a0, a1, fill=colour, width=width)
    if arrow:
        ang = math.radians(a1)
        tipx = cx + r * math.cos(ang)
        tipy = cy + r * math.sin(ang)
        for s in (1, -1):
            d.line([(tipx, tipy),
                    (tipx - S(16) * math.cos(ang - s * 0.45),
                     tipy - S(16) * math.sin(ang - s * 0.45))], fill=colour, width=width)


def main():
    os.makedirs(OUT, exist_ok=True)
    audio, marks = load_or_synthesize(TEXT, OUT)
    total = audio_duration(audio)
    cues = phrase_cues(marks, TEXT)

    ev = {
        "spin": word_time(marks, "вращается", total * 0.06, 1),
        "d243": word_time(marks, "сорок", total * 0.18),
        "d225": word_time(marks, "двадцать", total * 0.34),
        "longer": word_time(marks, "длиннее", total * 0.46),
        "retro": word_time(marks, "обратную", total * 0.56),
        "west": word_time(marks, "западе", total * 0.65),
        "acid": word_time(marks, "серной", total * 0.72),
        "temp": word_time(marks, "четырёхсот", total * 0.80),
        "press": word_time(marks, "давление", total * 0.88),
        "merc": word_time(marks, "меркурий", total * 0.95),
    }
    print("voice", round(total, 2), "s | events:", {k: round(v, 2) for k, v in ev.items()})

    frames_dir = os.path.join(OUT, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))

    n = int(total * FPS)
    start = int(os.environ.get('START_FRAME', '0'))
    ci = 0
    for i in range(start, n):
        t = i / FPS
        while ci + 1 < len(cues) and cues[ci + 1][0] <= t:
            ci += 1
        word = cues[ci][2] if t >= cues[ci][0] - 0.05 else (cues[ci - 1][2] if ci else "")

        frame = BG.copy()

        # Солнце
        sun = SUN_IMG.copy()
        sun.putalpha(sun.getchannel("A").point(lambda v: int(v * 0.95)))
        frame.alpha_composite(sun, SUN_POS)

        d = ImageDraw.Draw(frame, "RGBA")

        # орбиты
        ox, oy = SUN_POS[0] + SUN_D // 2, SUN_POS[1] + SUN_D // 2
        orbit_a = ease(min(1.0, max(0.0, (t - ev["spin"]) / 1.2)))
        if orbit_a > 0:
            r1 = int(S(W) * 0.86)
            d.arc([ox - r1, oy - r1, ox + r1, oy + r1], 200, 320,
                  fill=(120, 150, 210, int(90 * orbit_a)), width=S(2))
            d.arc([ox - int(r1 * 0.78), oy - int(r1 * 0.78), ox + int(r1 * 0.78), oy + int(r1 * 0.78)],
                  205, 315, fill=(120, 150, 210, int(60 * orbit_a)), width=S(2))

        # Меркурий
        if t >= ev["merc"] - 0.2:
            k = ease(min(1.0, (t - ev["merc"] + 0.2) / 0.6))
            mx = ox - int(S(W) * 0.30 * k)
            my = oy + int(S(H) * 0.10 * k)
            m = MERC_IMG.copy()
            m.putalpha(m.getchannel("A").point(lambda v: int(v * k)))
            frame.alpha_composite(m, (mx, my))
            d = ImageDraw.Draw(frame, "RGBA")
            d.text((mx - S(4), my + MERC_D + S(2)), "Меркурий", font=F_TICK,
                   fill=(198, 214, 238), stroke_width=S(3), stroke_fill=(6, 8, 16))

        # Венера: подлёт и вращение
        approach = ease(min(1.0, max(0.0, (t - ev["spin"] + 0.4) / 1.6)))
        scale = 0.82 + 0.18 * approach
        spin_sign = -1.0 if t >= ev["retro"] else 1.0
        tilt = spin_sign * math.sin(t * 0.9) * 3.0
        vw = int(VEN_D * scale)
        ven = VENUS_IMG.resize((vw, vw), Image.LANCZOS).rotate(tilt, resample=Image.BICUBIC)
        # свечение
        glow = Image.new("RGBA", (vw + 80, vw + 80), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([40, 40, vw + 40, vw + 40], fill=(255, 214, 140, 34))
        glow = glow.filter(ImageFilter.GaussianBlur(14))
        frame.alpha_composite(glow, (VEN_CX - vw // 2 - 40, VEN_CY - vw // 2 - 40))
        frame.alpha_composite(ven, (VEN_CX - vw // 2, VEN_CY - vw // 2))
        d = ImageDraw.Draw(frame, "RGBA")

        # стрелки вращения (меняют направление на «обратную»)
        if t >= ev["spin"]:
            ak = ease(min(1.0, (t - ev["spin"]) / 0.9))
            r = int(vw * 0.60)
            if spin_sign > 0:
                a0, a1 = -120, -20
            else:
                a0, a1 = -20, -120
            arrow_arc(d, VEN_CX, VEN_CY, r,
                      a0, a0 + (a1 - a0) * (0.35 + 0.65 * ak),
                      (255, 226, 160, int(210 * ak)), S(5))

        # карточки: сутки и год
        if t >= ev["d243"]:
            k = ease(min(1.0, (t - ev["d243"]) / 0.5))
            card(d, S(34), int(S(H) * 0.545), S(300), S(96), int(220 * k))
            num = int(243 * min(1.0, (t - ev["d243"]) / 1.1))
            d.text((S(52), int(S(H) * 0.552)), f"{num} дн", font=F_HUGE, fill=(255, 226, 160))
            d.text((S(52), int(S(H) * 0.605)), "оборот вокруг оси", font=F_TICK, fill=(186, 204, 232))

        if t >= ev["d225"]:
            k = ease(min(1.0, (t - ev["d225"]) / 0.5))
            card(d, S(W) - S(334), int(S(H) * 0.545), S(300), S(96), int(220 * k))
            num = int(225 * min(1.0, (t - ev["d225"]) / 1.1))
            d.text((S(W) - S(316), int(S(H) * 0.552)), f"{num} дн", font=F_HUGE, fill=(168, 226, 246))
            d.text((S(W) - S(316), int(S(H) * 0.605)), "год на Венере", font=F_TICK, fill=(186, 204, 232))

        # «сутки длиннее года»
        if t >= ev["longer"]:
            k = ease(min(1.0, (t - ev["longer"]) / 0.5))
            card(d, S(34), int(S(H) * 0.655), S(W) - S(68), S(74), int(235 * k))
            d.text((S(54), int(S(H) * 0.665)), "сутки длиннее года", font=F_LABEL,
                   fill=(255, 236, 176))
            d.line([(S(56), int(S(H) * 0.706)), (S(56) + int((S(W) - S(120)) * k), int(S(H) * 0.706))],
                   fill=(255, 196, 96, int(220 * k)), width=S(4))

        # ретроградное вращение
        if t >= ev["retro"]:
            k = ease(min(1.0, (t - ev["retro"]) / 0.5))
            d.text((S(40), int(S(H) * 0.475)), "вращение обратное", font=F_LABEL,
                   fill=(255, 214, 150), stroke_width=S(3), stroke_fill=(6, 8, 16))
            if k > 0.4:
                d.text((S(40), int(S(H) * 0.508)), "Солнце встаёт на западе", font=F_TICK,
                       fill=(196, 216, 240), stroke_width=S(3), stroke_fill=(6, 8, 16))

        # серная кислота
        if t >= ev["acid"]:
            k = ease(min(1.0, (t - ev["acid"]) / 0.5))
            d.text((S(W) - S(268), int(S(H) * 0.475)), "облака: серная кислота", font=F_TICK,
                   fill=(230, 216, 180), stroke_width=S(3), stroke_fill=(6, 8, 16))

        # температура и давление
        if t >= ev["temp"]:
            k = ease(min(1.0, (t - ev["temp"]) / 0.5))
            card(d, S(34), int(S(H) * 0.742), S(326), S(96), int(225 * k))
            d.text((S(52), int(S(H) * 0.750)), "464 °C", font=F_HUGE, fill=(255, 168, 120))
            d.text((S(52), int(S(H) * 0.804)), "на поверхности", font=F_TICK, fill=(214, 200, 196))

        if t >= ev["press"]:
            k = ease(min(1.0, (t - ev["press"]) / 0.5))
            card(d, S(W) - S(334), int(S(H) * 0.742), S(300), S(96), int(225 * k))
            d.text((S(W) - S(316), int(S(H) * 0.750)), "92 атм", font=F_HUGE, fill=(168, 214, 246))
            d.text((S(W) - S(316), int(S(H) * 0.804)), "как на 1 км глубины", font=F_TICK,
                   fill=(196, 210, 232))

        draw_caption(d, word, y=S(H) - S(150))
        frame.convert("RGB").resize((W, H), Image.LANCZOS).save(
            os.path.join(frames_dir, f"f{i:05d}.png"))
        if i % 250 == 0:
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
