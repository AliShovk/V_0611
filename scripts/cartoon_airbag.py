"""Эпизод «Подушка безопасности» — инженерная визуализация на SDF.

Подушка рисуется полем расстояний (scripts/sdf.py): нормали из градиента,
свет Ламберта, блик, рим-лайт, изолинии каждые 9 px. Всё остальное — PIL.
События привязаны к словам озвучки, время в кадре идёт в миллисекундах.
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon_engine import (FFMPEG, S, W, H, FPS, ease, lerp, audio_duration,
                            load_or_synthesize, font_path)
from cartoon_mariana import draw_caption, phrase_cues
import sdf
import sfx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "storage", "airbag")
F_LABEL = ImageFont.truetype(font_path(), S(28))
F_TICK = ImageFont.truetype(font_path(), S(22))
F_BIG = ImageFont.truetype(font_path(), S(56))
F_HUGE = ImageFont.truetype(font_path(), S(92))
F_HOOK = ImageFont.truetype(font_path(), S(50))

TEXT = ("Пятьдесят миллисекунд — быстрее, чем человек моргает. "
        "Датчик удара замыкает цепь за десять миллисекунд. "
        "Газогенератор сжигает заряд, и за двадцать миллисекунд подушка наполняется азотом. "
        "К пятидесяти ткань уже перед лицом водителя. "
        "Потом газ стравливается, чтобы подушка не сломала шею. "
        "На экране всё замедлено примерно в четыреста раз.")

BG_TOP, BG_BOT = (9, 16, 28), (4, 8, 14)
HUB = (250, 640)
FACE_X = 520

# область, где считаем SDF (1x координаты)
BOX = (150, 470, 620, 800)


def blueprint(w, h):
    """Тёмный инженерный фон с сеткой."""
    img = Image.new("RGBA", (w, h), BG_TOP + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(0, h, 12):
        d.line([(0, y), (w, y)], fill=lerp(BG_TOP, BG_BOT, y / h))
    step = S(40)
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=(70, 140, 180, 16), width=1)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=(70, 140, 180, 16), width=1)
    return img


def draw_wheel(d, alpha=255):
    cx, cy = S(HUB[0]), S(HUB[1])
    r = S(118)
    # обод
    d.arc([cx - r, cy - r * 0.92, cx + r, cy + r * 0.92], 0, 360,
          fill=(120, 134, 152, alpha), width=S(16))
    d.arc([cx - r, cy - r * 0.92, cx + r, cy + r * 0.92], 0, 360,
          fill=(176, 192, 210, alpha), width=S(3))
    # спицы
    for ang in (-90, -18, 162):
        a = math.radians(ang)
        d.line([(cx, cy), (cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.86)],
               fill=(104, 118, 136, alpha), width=S(12))
    # ступица
    d.rounded_rectangle([cx - S(34), cy - S(30), cx + S(34), cy + S(30)],
                        radius=S(8), fill=(92, 104, 122, alpha), outline=(158, 174, 192, alpha),
                        width=S(2))
    # колонка
    d.polygon([(cx - S(28), cy - S(16)), (cx - S(28), cy + S(16)),
               (S(60), cy + S(22)), (S(60), cy - S(22))],
              fill=(74, 86, 102, alpha), outline=(120, 134, 152, alpha))
    # модуль газогенератора
    d.rounded_rectangle([cx - S(18), cy - S(14), cx + S(22), cy + S(14)], radius=S(5),
                        fill=(196, 128, 60, alpha), outline=(240, 180, 110, alpha), width=S(2))


def draw_driver(d, alpha=255, lean=0.0):
    hx, hy = S(FACE_X + lean * 16), S(560)
    # торс
    d.rounded_rectangle([hx - S(70), hy + S(44), hx + S(96), hy + S(300)], radius=S(28),
                        fill=(38, 48, 64, alpha), outline=(96, 116, 140, alpha), width=S(2))
    # шея и голова
    d.rectangle([hx - S(22), hy + S(18), hx + S(22), hy + S(62)], fill=(38, 48, 64, alpha))
    d.ellipse([hx - S(54), hy - S(56), hx + S(54), hy + S(56)],
              fill=(44, 55, 72, alpha), outline=(104, 124, 148, alpha), width=S(2))
    # профиль носа
    d.polygon([(hx - S(50), hy - S(8)), (hx - S(64), hy + S(6)), (hx - S(50), hy + S(16))],
              fill=(44, 55, 72, alpha))


def airbag_sdf(px, py, k, wrinkles=1.0):
    """Поле расстояний подушки при раскрытии k (0..1)."""
    # три «лепестка», сглаженно объединённых
    e1 = sdf.sd_ellipse(px, py, HUB[0] + 46 * k, HUB[1] - 6, 34 + 84 * k, 28 + 62 * k)
    e2 = sdf.sd_ellipse(px, py, HUB[0] + 118 * k, HUB[1] - 14, 38 + 104 * k, 32 + 80 * k)
    e3 = sdf.sd_ellipse(px, py, HUB[0] + 170 * k, HUB[1] - 22, 28 + 72 * k, 24 + 60 * k)
    d = sdf.smin(e1, e2, 46)
    d = sdf.smin(d, e3, 46)
    # плоская площадка контакта у лица
    d = sdf.smax(d, -(px - (FACE_X - 54)), 8.0)

    # складки ткани
    if wrinkles > 0.01:
        theta = np.arctan2(py - HUB[1], px - HUB[0])
        grow = 0.28 + 0.72 * min(1.0, k * 1.5)
        fold = (np.sin(theta * 9.0 + 5.0 * k + px * 0.05) * 2.4
                + np.sin(theta * 17.0 - 3.0 + py * 0.03) * 1.1
                + np.sin(px * 0.26 + py * 0.18) * 0.45)
        d = d + fold * wrinkles * grow * 2.2
    return d


def ms_at(t, ev):
    """Видео-время -> миллисекунды процесса (по словам диктора)."""
    anchors = [(0.0, 0.0), (ev["t10"], 10.0), (ev["t20"], 20.0),
               (ev["t50"], 50.0), (ev["deflate"], 56.0), (ev["end"], 70.0)]
    for i in range(len(anchors) - 1):
        t0, m0 = anchors[i]
        t1, m1 = anchors[i + 1]
        if t <= t1:
            k = 0.0 if t1 <= t0 else (t - t0) / (t1 - t0)
            return m0 + (m1 - m0) * max(0.0, min(1.0, k))
    return 70.0


def main():
    os.makedirs(OUT, exist_ok=True)
    audio, marks = load_or_synthesize(TEXT, OUT)
    total = audio_duration(audio)
    cues = phrase_cues(marks, TEXT)

    def word_time(needle, default, occurrence=1):
        needle = needle.lower()
        seen = 0
        for (start, dur, word) in marks:
            if needle in word.lower():
                seen += 1
                if seen == occurrence:
                    return start
        return default

    ev = {
        "hook_end": 1.7,
        "t10": word_time("десять", total * 0.28),
        "t20": word_time("двадцать", total * 0.48),
        "t50": word_time("пятидесяти", total * 0.68),
        "deflate": word_time("стравливается", total * 0.84),
        "slowmo": word_time("четыреста", total * 0.94),
        "end": total * 0.99,
    }
    print("voice", round(total, 2), "| events:", {k: round(v, 2) for k, v in ev.items()})

    sfx_events = [
        (0.02, "boom", 0.5),
        (ev["t10"], "tick", 0.4),
        (ev["t20"], "whoosh", 0.45),
        (ev["t20"], "pop", 0.3),
        (ev["t50"], "chime", 0.35),
        (ev["deflate"], "hiss", 0.5),
        (ev["slowmo"], "tick", 0.3),
    ]
    track = sfx.build_track(total, sfx_events, os.path.join(OUT, "sfx.wav"))

    frames_dir = os.path.join(OUT, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    start = int(os.environ.get("START_FRAME", "0"))
    if start == 0 and not os.environ.get("KEEP_FRAMES"):
        for f in os.listdir(frames_dir):
            os.remove(os.path.join(frames_dir, f))

    base = blueprint(S(W), S(H))
    n = int(total * FPS)
    end = min(n, int(os.environ.get("MAX_FRAMES", "1000000")) + start)
    ci = 0

    bx0, by0, bx1, by1 = [S(v) for v in BOX]
    bw, bh = bx1 - bx0, by1 - by0

    for i in range(start, end):
        t = i / FPS
        while ci + 1 < len(cues) and cues[ci + 1][0] <= t:
            ci += 1
        word = cues[ci][2] if t >= cues[ci][0] - 0.05 else (cues[ci - 1][2] if ci else "")

        ms = ms_at(t, ev)
        k = min(1.0, ms / 50.0)
        k_ease = ease(k)
        deflate_k = max(0.0, min(1.0, (ms - 56.0) / 14.0))

        frame = base.copy()
        d = ImageDraw.Draw(frame, "RGBA")

        # водитель и руль
        draw_driver(d, alpha=255, lean=deflate_k * 0.15)
        draw_wheel(d, alpha=255)

        # створки крышки модуля
        if ms > 3:
            flap = min(1.0, (ms - 3) / 12.0)
            hx, hy = S(HUB[0]), S(HUB[1])
            for sgn in (-1, 1):
                tipx = hx + sgn * S(40 + 26 * flap)
                tipy = hy + sgn * S(30 + 18 * flap)
                d.polygon([(hx + sgn * S(6), hy - S(10)), (hx + sgn * S(30), hy - S(16)),
                           (tipx, tipy - sgn * S(6)), (tipx - sgn * S(10), tipy + sgn * S(10))],
                          fill=(60, 70, 86, 235), outline=(140, 158, 178, 235))

        # --- SDF-подушка ---
        if ms > 1.0:
            px, py = sdf.grid(bw, bh, bx0, by0)
            SC = float(S(1))
            kk = k_ease * (1.0 - 0.10 * deflate_k)
            field = airbag_sdf(px / SC, py / SC, kk,
                               wrinkles=1.0 - 0.75 * k_ease + 1.6 * deflate_k) * SC
            rgba = sdf.to_rgba(field, (0.88, 0.87, 0.82), seam=S(19.0),
                               spec_power=12, spec_gain=0.30, rim_gain=0.20,
                               ambient=0.44)
            bag = Image.fromarray(rgba, "RGBA").filter(ImageFilter.GaussianBlur(S(0.7)))
            frame.alpha_composite(bag, (bx0, by0))
            d = ImageDraw.Draw(frame, "RGBA")

            if k_ease > 0.72:
                touch = Image.new("RGBA", (S(140), S(160)), (0, 0, 0, 0))
                ImageDraw.Draw(touch).ellipse([S(30), S(30), S(110), S(130)], fill=(0, 0, 0, 90))
                touch = touch.filter(ImageFilter.GaussianBlur(S(10)))
                frame.alpha_composite(touch, (S(FACE_X) - S(96), S(560) - S(80)))

            # контур подушки — инженерная обводка
            mask = (field < 0).astype(np.uint8) * 255
            edge = Image.fromarray(mask, "L").filter(ImageFilter.FIND_EDGES)
            edge = edge.point(lambda v: 255 if v > 40 else 0)
            glow = Image.new("RGBA", (bw, bh), (120, 226, 255, 0))
            glow.putalpha(edge.point(lambda v: int(v * 0.55)))
            frame.alpha_composite(glow, (bx0, by0))
            d = ImageDraw.Draw(frame, "RGBA")

        # струи газа
        if 2 < ms < 22:
            gk = 1.0 - (ms - 2) / 20.0
            for j in range(9):
                ang = -0.5 + j * 0.12
                ln = S(22) + S(44) * (1 - gk)
                x1 = S(HUB[0]) + S(20) + math.cos(ang) * ln
                y1 = S(HUB[1]) + math.sin(ang) * ln
                d.line([(S(HUB[0]) + S(18), S(HUB[1])), (x1, y1)],
                       fill=(255, 176, 96, int(150 * gk)), width=S(3))

        # --- счётчик мс ---
        txt = f"{int(round(ms))} мс"
        d.text((S(36), S(58)), txt, font=F_HUGE, fill=(150, 228, 255))
        d.text((S(38), S(160)), "процесс раскрытия", font=F_TICK, fill=(140, 176, 204))
        d.text((S(38), S(190)), "замедлено ~×400", font=F_TICK,
               fill=(240, 180, 110) if t > ev["slowmo"] else (110, 140, 168))

        # --- таймлайн ---
        ty = S(1070)
        d.line([(S(56), ty), (S(W) - S(56), ty)], fill=(90, 130, 160, 200), width=S(3))
        for m in range(0, 71, 10):
            x = S(56) + (S(W) - S(112)) * m / 70.0
            d.line([(x, ty - S(10)), (x, ty + S(10))], fill=(120, 160, 190, 220), width=S(2))
            d.text((x - S(12), ty + S(16)), str(m), font=F_TICK, fill=(126, 156, 182))
        d.text((S(16), ty + S(18)), "мс", font=F_TICK, fill=(126, 156, 182))
        mx = S(56) + (S(W) - S(112)) * min(70.0, ms) / 70.0
        d.ellipse([mx - S(9), ty - S(9), mx + S(9), ty + S(9)], fill=(255, 196, 96))
        d.line([(mx, ty - S(26)), (mx, ty - S(6))], fill=(255, 196, 96, 190), width=S(3))

        # --- хук в первые секунды ---
        if t < ev["hook_end"]:
            fade = 1.0 if t < ev["hook_end"] - 0.5 else max(0.0, (ev["hook_end"] - t) / 0.5)
            d.text((S(40), S(250)), "50 МС", font=F_HOOK,
                   fill=(255, 236, 176, int(255 * fade)),
                   stroke_width=S(5), stroke_fill=(10, 16, 26, int(230 * fade)))
            d.text((S(40), S(316)), "быстрее, чем моргнуть", font=F_LABEL,
                   fill=(206, 226, 246, int(240 * fade)),
                   stroke_width=S(4), stroke_fill=(10, 16, 26, int(200 * fade)))

        # подписи этапов
        stages = [(ev["t10"], "10 мс — датчик замкнул цепь", (180, 214, 240)),
                  (ev["t20"], "20 мс — газогенератор наполнил подушку", (255, 206, 150)),
                  (ev["t50"], "50 мс — ткань перед лицом", (160, 236, 200))]
        active = [i for i, (t0, _, _) in enumerate(stages) if t >= t0]
        for idx, (t0, line, col) in enumerate(stages):
            if idx not in active:
                continue
            last = active and idx == active[-1]
            alpha = 255 if last else 120
            d.text((S(60), S(900 + idx * 44)), line, font=F_LABEL, fill=col + (alpha,))

        if not (t >= ev["deflate"] and t < ev["deflate"] + 0.4):
            draw_caption(d, word, y=S(H) - S(120))

        frame.convert("RGB").save(os.path.join(frames_dir, f"f{i:05d}.png"))
        if i % 200 == 0:
            print("frame", i, "/", n)

    silent = os.path.join(OUT, "video_silent.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames_dir, "f%05d.png"), "-i", audio,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                    silent], check=True)
    final = os.path.join(OUT, "final.mp4")
    sfx.mix(silent, audio, track, final, video_sfx_gain=0.75)
    print("video", final)


if __name__ == "__main__":
    main()
