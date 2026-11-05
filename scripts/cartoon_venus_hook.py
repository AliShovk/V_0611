"""Эпизод «Венера» — сутки длиннее года. Хук с 0-й секунды, ответ в конце.

Всё привязано к словам озвучки (word boundaries Edge TTS), плюс синтезированные
звуковые акценты (scripts/sfx.py) на появление карточек и развязку.
"""
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon_engine import (FFMPEG, S, W, H, FPS, ease, lerp, audio_duration,
                            load_or_synthesize, font_path)
from cartoon_mariana import draw_caption, phrase_cues
import sfx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "art")
OUT = os.path.join(ROOT, "storage", "cartoon-venus-hook")
F_LABEL = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", S(30))
F_TICK = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", S(23))
F_BIG = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", S(54))
F_HUGE = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", S(64))
F_HOOK = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", S(62))
F_ANSWER = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", S(96))

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

VEN_D = int(S(W) * 0.44)
VENUS_IMG = VENUS.resize((VEN_D, VEN_D), Image.LANCZOS)
VEN_CX, VEN_CY = S(W) // 2, int(S(H) * 0.36)
SUN_D = int(S(W) * 0.15)
SUN_IMG = SUN.resize((SUN_D, SUN_D), Image.LANCZOS)
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


def arrow_arc(d, cx, cy, r, a0, a1, colour, width):
    d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=colour, width=width)
    ang = math.radians(a1)
    tipx, tipy = cx + r * math.cos(ang), cy + r * math.sin(ang)
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
        "spin": word_time(marks, "проворачивается", total * 0.16),
        "d243": word_time(marks, "сорок", total * 0.24),
        "d225": word_time(marks, "двадцать", total * 0.34),
        "longer": word_time(marks, "длиннее", 0.12),
        "west": word_time(marks, "западе", total * 0.14),
        "acid": word_time(marks, "серной", total * 0.56),
        "temp": word_time(marks, "четырёхсот", total * 0.66),
        "press": word_time(marks, "давление", total * 0.78),
        "answer": word_time(marks, "венера", total * 0.95),
    }
    print("voice", round(total, 2), "s | events:", {k: round(v, 2) for k, v in ev.items()})

    # звуковые акценты
    sfx_events = [
        (0.02, "boom", 0.55),
        (0.02, "whoosh", 0.45),
        (ev["west"] - 0.10, "whoosh", 0.35),
        (ev["spin"] - 0.05, "pop", 0.30),
        (ev["d243"], "pop", 0.32),
        (ev["d225"], "pop", 0.32),
        (ev["longer"], "whoosh", 0.30),
        (ev["acid"], "tick", 0.28),
        (ev["temp"], "boom", 0.34),
        (ev["press"], "pop", 0.30),
        (max(0.0, ev["answer"] - 0.85), "riser", 0.34),
        (ev["answer"], "chime", 0.5),
    ]
    track = sfx.build_track(total, sfx_events, os.path.join(OUT, "sfx.wav"))

    frames_dir = os.path.join(OUT, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    start = int(os.environ.get("START_FRAME", "0"))
    if start == 0 and not os.environ.get("KEEP_FRAMES"):
        for f in os.listdir(frames_dir):
            os.remove(os.path.join(frames_dir, f))

    n = int(total * FPS)
    end = min(n, int(os.environ.get("MAX_FRAMES", "1000000")) + start)
    ci = 0
    for i in range(start, end):
        t = i / FPS
        while ci + 1 < len(cues) and cues[ci + 1][0] <= t:
            ci += 1
        word = cues[ci][2] if t >= cues[ci][0] - 0.05 else (cues[ci - 1][2] if ci else "")

        frame = BG.copy()
        sun = SUN_IMG.copy()
        sun.putalpha(sun.getchannel("A").point(lambda v: int(v * 0.95)))
        frame.alpha_composite(sun, SUN_POS)
        d = ImageDraw.Draw(frame, "RGBA")

        # --- Венера ---
        approach = ease(min(1.0, max(0.0, t / 1.1)))
        scale = 0.80 + 0.20 * approach
        tilt = math.sin(t * 0.9) * 3.0
        vw = int(VEN_D * scale)
        ven = VENUS_IMG.resize((vw, vw), Image.LANCZOS).rotate(tilt, resample=Image.BICUBIC)
        glow = Image.new("RGBA", (vw + 80, vw + 80), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([40, 40, vw + 40, vw + 40], fill=(255, 214, 140, 34))
        glow = glow.filter(ImageFilter.GaussianBlur(14))
        frame.alpha_composite(glow, (VEN_CX - vw // 2 - 40, VEN_CY - vw // 2 - 40))
        frame.alpha_composite(ven, (VEN_CX - vw // 2, VEN_CY - vw // 2))
        d = ImageDraw.Draw(frame, "RGBA")

        # стрелка вращения
        r = int(vw * 0.60)
        arrow_arc(d, VEN_CX, VEN_CY, r, -120, -30, (255, 226, 160, 190), S(5))

        # --- хук с 0-й секунды ---
        if t < 1.75:
            k = ease(min(1.0, t / 0.22))
            fade = 1.0 if t < 1.2 else max(0.0, 1 - (t - 1.2) / 0.55)
            txt = "СУТКИ ДЛИННЕЕ ГОДА?"
            f_hook = F_HOOK
            size = 62
            while size > 34:
                f_hook = ImageFont.truetype(font_path(), S(size))
                bbox = d.textbbox((0, 0), txt, font=f_hook, stroke_width=S(6))
                if bbox[2] - bbox[0] <= S(W) - S(48):
                    break
                size -= 2
            bbox = d.textbbox((0, 0), txt, font=f_hook, stroke_width=S(6))
            tw = bbox[2] - bbox[0]
            x = (S(W) - tw) / 2 - bbox[0]
            y = int(S(H) * 0.09)
            for layer, alpha in ((S(10), int(70 * fade)), (S(5), int(120 * fade))):
                d.text((x, y), txt, font=f_hook, fill=(255, 120, 60, int(alpha * k)),
                       stroke_width=layer, stroke_fill=(255, 120, 60, int(alpha * k)))
            d.text((x, y), txt, font=f_hook, fill=(255, 244, 214, int(255 * fade * k)),
                   stroke_width=S(6), stroke_fill=(12, 14, 26, int(235 * fade)))

        # --- карточки ---
        hide = t >= ev["answer"] - 0.15
        if t >= ev["d243"] and not hide:
            k = ease(min(1.0, (t - ev["d243"]) / 0.35))
            card(d, S(34), int(S(H) * 0.545), S(300), S(96), int(220 * k))
            num = int(243 * min(1.0, (t - ev["d243"]) / 0.9))
            d.text((S(52), int(S(H) * 0.552)), f"{num} дн", font=F_HUGE, fill=(255, 226, 160))
            d.text((S(52), int(S(H) * 0.605)), "оборот вокруг оси", font=F_TICK, fill=(186, 204, 232))

        if t >= ev["d225"] and not hide:
            k = ease(min(1.0, (t - ev["d225"]) / 0.35))
            card(d, S(W) - S(334), int(S(H) * 0.545), S(300), S(96), int(220 * k))
            num = int(225 * min(1.0, (t - ev["d225"]) / 0.9))
            d.text((S(W) - S(316), int(S(H) * 0.552)), f"{num} дн", font=F_HUGE, fill=(168, 226, 246))
            d.text((S(W) - S(316), int(S(H) * 0.605)), "год на планете", font=F_TICK,
                   fill=(186, 204, 232))

        if t >= ev["longer"] and not hide:
            k = ease(min(1.0, (t - ev["longer"]) / 0.35))
            card(d, S(34), int(S(H) * 0.655), S(W) - S(68), S(70), int(235 * k))
            d.text((S(54), int(S(H) * 0.663)), "сутки длиннее года", font=F_LABEL,
                   fill=(255, 236, 176))
            d.line([(S(56), int(S(H) * 0.702)),
                    (S(56) + int((S(W) - S(120)) * k), int(S(H) * 0.702))],
                   fill=(255, 196, 96, int(220 * k)), width=S(4))

        # --- запад ---
        if t >= ev["west"] and not hide:
            k = ease(min(1.0, (t - ev["west"]) / 0.4))
            d.text((S(40), int(S(H) * 0.470)), "Солнце встаёт на западе", font=F_LABEL,
                   fill=(255, 214, 150), stroke_width=S(3), stroke_fill=(6, 8, 16))

        if t >= ev["acid"] and not hide:
            d.text((S(W) - S(286), int(S(H) * 0.470)), "облака: серная кислота", font=F_TICK,
                   fill=(230, 216, 180), stroke_width=S(3), stroke_fill=(6, 8, 16))

        if t >= ev["temp"] and not hide:
            k = ease(min(1.0, (t - ev["temp"]) / 0.35))
            card(d, S(34), int(S(H) * 0.742), S(326), S(96), int(225 * k))
            d.text((S(52), int(S(H) * 0.750)), "464 °C", font=F_HUGE, fill=(255, 168, 120))
            d.text((S(52), int(S(H) * 0.804)), "на поверхности", font=F_TICK, fill=(214, 200, 196))

        if t >= ev["press"] and not hide:
            k = ease(min(1.0, (t - ev["press"]) / 0.35))
            card(d, S(W) - S(334), int(S(H) * 0.742), S(300), S(96), int(225 * k))
            d.text((S(W) - S(316), int(S(H) * 0.750)), "92 атм", font=F_HUGE, fill=(168, 214, 246))
            d.text((S(W) - S(316), int(S(H) * 0.804)), "как на 1 км глубины", font=F_TICK,
                   fill=(196, 210, 232))

        # --- развязка ---
        if t >= ev["answer"] - 0.15:
            k = ease(min(1.0, (t - ev["answer"] + 0.15) / 0.35))
            box_h = int(S(H) * 0.30)
            veil = Image.new("RGBA", (S(W), S(H)), (2, 4, 10, 0))
            ImageDraw.Draw(veil).rectangle([0, 0, S(W), S(H)], fill=(2, 4, 10, int(210 * k)))
            frame.alpha_composite(veil, (0, 0))
            box = Image.new("RGBA", (S(W), box_h), (4, 8, 18, 0))
            bd = ImageDraw.Draw(box)
            bd.rectangle([0, 0, S(W), box_h], fill=(4, 8, 18, int(235 * k)))
            frame.alpha_composite(box, (0, int(S(H) * 0.33)))
            d = ImageDraw.Draw(frame, "RGBA")
            txt = "ВЕНЕРА"
            bbox = d.textbbox((0, 0), txt, font=F_ANSWER, stroke_width=S(8))
            x = (S(W) - (bbox[2] - bbox[0])) / 2 - bbox[0]
            d.text((x, int(S(H) * 0.375)), txt, font=F_ANSWER, fill=(255, 236, 176, int(255 * k)),
                   stroke_width=S(8), stroke_fill=(20, 14, 8, int(230 * k)))
            sub = "самая горячая планета — хотя Меркурий ближе"
            bbox2 = d.textbbox((0, 0), sub, font=F_TICK, stroke_width=S(4))
            d.text(((S(W) - (bbox2[2] - bbox2[0])) / 2 - bbox2[0], int(S(H) * 0.465)), sub,
                   font=F_TICK, fill=(212, 226, 246, int(235 * k)),
                   stroke_width=S(4), stroke_fill=(10, 12, 20))

        if not hide:
            draw_caption(d, word, y=S(H) - S(150))
        frame.convert("RGB").resize((W, H), Image.LANCZOS).save(
            os.path.join(frames_dir, f"f{i:05d}.png"))
        if i % 250 == 0:
            print("frame", i, "/", n)

    silent = os.path.join(OUT, "video_silent.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames_dir, "f%05d.png"), "-i", audio,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                    silent], check=True)
    final = os.path.join(OUT, "final.mp4")
    sfx.mix(silent, audio, track, final, video_sfx_gain=0.8)
    print("video", final)


if __name__ == "__main__":
    main()
