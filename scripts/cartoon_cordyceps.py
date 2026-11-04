"""Эпизод «Кордицепс» — гриб, который управляет муравьём.

Арт нарисован в SVG и отрендерен Inkscape (art/*.svg -> art/*.png),
анимация и субтитры — PIL поверх готовых слоёв.
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
OUT = os.path.join(ROOT, "storage", "cartoon-cordyceps")
F_LABEL = ImageFont.truetype(font_path(), S(30))
F_TICK = ImageFont.truetype(font_path(), S(23))
F_BIG = ImageFont.truetype(font_path(), S(50))

TEXT = ("В джунглях есть гриб, который управляет муравьём. "
        "Споры кордицепса падают на тело и прорастают внутрь. "
        "Муравей теряет страх высоты: гриб ведёт его вверх и заставляет вцепиться в лист "
        "на высоте двадцать пять сантиметров — там прохладно и влажно. "
        "Он умирает, а через две-три недели из его головы вырастает плодовое тело "
        "и выстреливает спорами в новых муравьёв. "
        "Один гриб — четыре миллиона лет эволюции управления чужим телом.")

BG = Image.open(os.path.join(ART, "bg.png")).convert("RGBA").resize((S(W), S(H)), Image.LANCZOS)
ANT = Image.open(os.path.join(ART, "ant.png")).convert("RGBA")
STALK = Image.open(os.path.join(ART, "stalk.png")).convert("RGBA")
WOUND = Image.open(os.path.join(ART, "wound.png")).convert("RGBA")

ANT_W = int(S(W) * 0.60)
ANT_H = int(ANT.height * ANT_W / ANT.width)
ANT_IMG = ANT.resize((ANT_W, ANT_H), Image.LANCZOS)
WOUND_W = int(ANT_W * 0.34)
WOUND_IMG = WOUND.resize((WOUND_W, int(WOUND.height * WOUND_W / WOUND.width)), Image.LANCZOS)

ANT_X, ANT_Y = int(S(W) * 0.06), int(S(H) * 0.475)
STALK_X = ANT_X + int(ANT_W * 0.74)
STALK_BASE_Y = ANT_Y + int(ANT_H * 0.26)
STALK_MAX_H = int(S(H) * 0.42)

SPORES = [(random.uniform(0.05, 0.95), random.uniform(0.0, 1.0), random.uniform(2.0, 4.4))
          for _ in range(46)]


def _scaled(img, height):
    if height < 8:
        return None
    w = max(2, int(img.width * height / img.height))
    return img.resize((w, height), Image.LANCZOS)


def draw_frame(t, total):
    p = min(1.0, t / max(0.1, total * 0.96))
    frame = BG.copy()

    # --- фазы ---
    walk = ease(min(1.0, p / 0.22))            # муравей идёт по листу
    climb = ease(min(1.0, max(0.0, (p - 0.18) / 0.22)))  # поднимается и замирает
    dead = ease(min(1.0, max(0.0, (p - 0.42) / 0.10)))
    grow = ease(min(1.0, max(0.0, (p - 0.52) / 0.40)))

    ax = ANT_X + int((1 - climb) * S(W) * 0.30 * (1 - walk * 0.35))
    ay = ANT_Y - int(climb * S(H) * 0.055)
    tilt = -climb * 16 + math.sin(t * 6) * 1.2 * (1 - dead)
    ant = ANT_IMG.rotate(tilt, resample=Image.BICUBIC, expand=True)

    # --- стебель (за муравьём) ---
    if grow > 0.02:
        h = int(STALK_MAX_H * grow)
        st = _scaled(STALK, h)
        if st:
            frame.alpha_composite(st, (STALK_X - st.width // 2, STALK_BASE_Y - st.height))

    # --- воротник мицелия в точке выхода ---
    if grow > 0.05:
        col = ImageDraw.Draw(frame, "RGBA")
        cw = S(13) + S(6) * grow
        col.ellipse([STALK_X - cw, STALK_BASE_Y - cw * 0.5, STALK_X + cw, STALK_BASE_Y + cw * 0.5],
                    fill=(232, 214, 172, 190), outline=(180, 152, 106, 220), width=S(2))

    # --- муравей ---
    shadow = Image.new("RGBA", (ant.width + 60, 46), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([24, 8, ant.width + 36, 40], fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    frame.alpha_composite(shadow, (ax - 30, ay + ant.height - 44))
    frame.alpha_composite(ant, (ax, ay))

    # --- рана и мицелий на голове ---
    if climb > 0.4:
        wx = ax + int(ant.width * 0.70)
        wy = ay + int(ant.height * 0.14)
        frame.alpha_composite(WOUND_IMG, (wx, wy))

    # --- споры ---
    d = ImageDraw.Draw(frame, "RGBA")
    fall_p = min(1.0, t / max(0.1, total * 0.5))
    for i, (sx, off, r) in enumerate(SPORES):
        y = (off + fall_p * 1.35) % 1.0
        x = sx * S(W) + math.sin(t * 0.9 + i) * S(14)
        alpha = int(150 * (1 - y * 0.5) * min(1.0, p * 4))
        if alpha <= 0:
            continue
        yy = S(H) * 0.06 + y * S(H) * 0.52
        d.ellipse([x - S(r), yy - S(r * 0.7), x + S(r), yy + S(r * 0.7)],
                  fill=(246, 232, 186, alpha))

    # --- вылет спор в финале ---
    if grow > 0.75:
        burst = ease(min(1.0, (grow - 0.75) / 0.25))
        st_top = STALK_BASE_Y - int(STALK_MAX_H * grow)
        for i in range(16):
            ang = -math.pi / 2 + (i - 8) * 0.16
            dist = burst * S(W) * 0.20 * (0.6 + (i % 5) * 0.12)
            bx = STALK_X + math.cos(ang) * dist
            by = st_top + math.sin(ang) * dist * 0.7
            rr = S(2.4) * (1 - burst * 0.4)
            d.ellipse([bx - rr, by - rr, bx + rr, by + rr], fill=(255, 240, 198, int(220 * (1 - burst * 0.6))))

    # --- подписи ---
    if climb > 0.55:
        d.rounded_rectangle([S(44), S(150), S(320), S(212)], radius=S(14), fill=(14, 26, 24, 220))
        d.text((S(60), S(160)), "лист на высоте 25 см", font=F_LABEL, fill=(214, 246, 226))
        d.line([(S(322), S(186)), (S(W * 0.30), S(H * 0.545))], fill=(150, 226, 190, 200), width=S(3))
        d.ellipse([S(W * 0.30) - S(5), S(H * 0.545) - S(5), S(W * 0.30) + S(5), S(H * 0.545) + S(5)],
                  fill=(150, 226, 190, 210))
    if grow > 0.30:
        d.rounded_rectangle([S(390), S(300), S(660), S(392)], radius=S(14), fill=(16, 28, 26, 225))
        d.text((S(406), S(312)), "плодовое тело", font=F_LABEL, fill=(255, 226, 168))
        d.text((S(406), S(350)), "растёт из головы", font=F_TICK, fill=(206, 236, 220))
        d.line([(S(520), S(394)), (S(STALK_X - S(6)), S(STALK_BASE_Y + S(6)))],
               fill=(255, 226, 168, 200), width=S(3))
        d.ellipse([S(STALK_X - S(6)) - S(6), S(STALK_BASE_Y + S(6)) - S(6),
                   S(STALK_X - S(6)) + S(6), S(STALK_BASE_Y + S(6)) + S(6)], fill=(255, 226, 168, 210))
    if p > 0.80:
        d.rounded_rectangle([S(70), S(940), S(650), S(1040)], radius=S(18), fill=(10, 22, 20, 215))
        d.text((S(92), S(956)), "4 млн лет", font=F_BIG, fill=(255, 226, 158))
        d.text((S(92), S(1004)), "эволюции управления чужим телом", font=F_LABEL, fill=(200, 236, 218))

    return frame


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
        frame = draw_frame(t, total)
        d = ImageDraw.Draw(frame, "RGBA")
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
