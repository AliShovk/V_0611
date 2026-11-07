"""Generic 2D explainer-cartoon engine: narration + captions + scene renderer.

Scene modes:
  heat      — ground cross-section with magma, heat arrows, temperature badges
  depth     — vertical water column with depth ruler and pressure markers
  permafrost— soil cross-section with ice wedges, thaw layer, methane bubbles
"""
import json
import math
import os
import re
import random
import subprocess

import edge_tts
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = (
    os.environ.get("FFMPEG")
    or next((p for p in (
        os.path.join(ROOT, ".venv", "Lib", "site-packages", "imageio_ffmpeg",
                     "binaries", "ffmpeg-win-x86_64-v7.1.exe"),
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
    ) if os.path.exists(p)), None)
)
if not FFMPEG:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FONT_BOLD = os.environ.get("FONT_BOLD") or "C:/Windows/Fonts/msyhbd.ttc"


def font_path():
    """Первый найденный шрифт с кириллицей."""
    for cand in (os.environ.get("FONT_BOLD"), FONT_BOLD,
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"):
        if cand and os.path.exists(cand):
            return cand
    raise FileNotFoundError("Не найден шрифт с кириллицей: задайте FONT_BOLD")
VOICE = "ru-RU-SvetlanaNeural"
W, H = 720, 1280
SS = 2
FPS = 30


def S(v):
    return int(round(v * SS))


def font(size):
    return ImageFont.truetype(font_path(), S(size))


F_WORD = font(52)
F_LABEL = font(34)
F_TICK = font(26)


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ voice
def _speak(text, voice, path, tries=12):
    """Один кусок текста -> mp3 + word marks. Edge TTS часто отдаёт NoAudioReceived."""
    import asyncio
    import time

    async def run():
        marks = []
        com = edge_tts.Communicate(text, voice, boundary="WordBoundary")
        with open(path, "wb") as f:
            async for ch in com.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    marks.append((ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]))
        return marks

    last = None
    for attempt in range(tries):
        try:
            marks = asyncio.run(run())
            if os.path.getsize(path) > 2000:
                return marks
            last = f"tiny file {os.path.getsize(path)} B"
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(3.0 + attempt * 2.5)
    raise RuntimeError(f"TTS chunk failed: {last}")


def synthesize(text, out_dir, voice=None):
    """Озвучка по предложениям: устойчиво к сбоям и даёт естественные паузы."""
    os.makedirs(out_dir, exist_ok=True)
    voice = voice or VOICE
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    parts, marks, offset = [], [], 0.0
    for i, sentence in enumerate(sentences):
        path = os.path.join(out_dir, f"part{i:02d}.mp3")
        chunk = _speak(sentence, voice, path)
        dur = audio_duration(path)
        for (st, du, word) in chunk:
            marks.append((st + offset, du, word))
        offset += dur
        parts.append(path)
    audio = os.path.join(out_dir, "voice.mp3")
    lst = os.path.join(out_dir, "parts.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in parts:
            f.write("file '" + os.path.basename(p) + "'\n")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c:a", "libmp3lame", "-b:a", "192k", audio], check=True)
    with open(os.path.join(out_dir, "marks.json"), "w", encoding="utf-8") as f:
        json.dump(marks, f, ensure_ascii=False)
    return audio, marks


def load_or_synthesize(text, out_dir, voice=None):
    """Переиспользует готовую озвучку и word-разметку (Edge TTS бывает недоступен)."""
    audio = os.path.join(out_dir, "voice.mp3")
    marks_path = os.path.join(out_dir, "marks.json")
    if os.path.exists(audio) and os.path.getsize(audio) > 2000 and os.path.exists(marks_path):
        with open(marks_path, encoding="utf-8") as f:
            marks = [tuple(x) for x in json.load(f)]
        return audio, marks
    return synthesize(text, out_dir, voice)


def audio_duration(path):
    out = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True,
                         text=True, errors="ignore").stderr
    for line in out.splitlines():
        if "Duration" in line:
            hms = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = hms.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def build_cues(marks):
    cues = []
    i = 0
    while i < len(marks):
        s0, d0, w0 = marks[i]
        lab, end = w0, s0 + d0
        if i + 1 < len(marks) and d0 < 0.32 and len(w0) <= 8:
            s1, d1, w1 = marks[i + 1]
            lab, end = f"{w0} {w1}", s1 + d1
            i += 1
        cues.append((s0, end, lab))
        i += 1
    return cues


def caption(d, word, y=1088):
    if not word:
        return
    bbox = d.textbbox((0, 0), word, font=F_WORD, stroke_width=S(6))
    x = (S(W) - (bbox[2] - bbox[0])) / 2 - bbox[0]
    d.text((x, S(y)), word, font=F_WORD, fill=(255, 255, 255),
           stroke_width=S(6), stroke_fill=(28, 36, 46))


def label(d, x, y, text, colour, plate=(26, 34, 44, 195), size=None):
    f = size or F_LABEL
    bbox = d.textbbox((0, 0), text, font=f)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.rounded_rectangle([S(x - 12), S(y - 8), S(x + w + 16), S(y + h + 16)],
                        radius=S(12), fill=plate)
    d.text((S(x), S(y)), text, font=f, fill=colour)
    return x + w + 16, y + h / 2


def leader(d, x1, y1, x2, y2, colour=(190, 210, 230), alpha=190):
    d.line([(S(x1), S(y1)), (S(x2), S(y2))], fill=(*colour, alpha), width=S(3))
    d.ellipse([S(x2 - 5), S(y2 - 5), S(x2 + 5), S(y2 + 5)], fill=(*colour, alpha))


def character(d, x, y, t, walking=False, shiver=False, scale=1.0,
              coat=(231, 116, 48), coat_dark=(172, 78, 26), skin=(246, 198, 158)):
    s = scale
    bob = abs(math.sin(t * 7)) * 3 if walking else 0
    if shiver:
        x += math.sin(t * 26) * 1.8
    body_top = y - 104 * s - bob
    swing = math.sin(t * 9) * 10 if walking else 0
    d.line([(S(x - 9 * s), S(y - 42 * s)), (S(x - 11 * s + swing), S(y))], fill=coat_dark, width=S(10 * s))
    d.line([(S(x + 9 * s), S(y - 42 * s)), (S(x + 11 * s - swing), S(y))], fill=coat_dark, width=S(10 * s))
    d.rounded_rectangle([S(x - 22 * s), S(body_top + 28), S(x + 22 * s), S(y - 36 * s)],
                        radius=S(12 * s), fill=coat)
    arm_y = body_top + 46
    up = -20 if shiver else 16
    d.line([(S(x - 20 * s), S(arm_y)), (S(x - 34 * s), S(arm_y + up))], fill=coat_dark, width=S(9 * s))
    d.line([(S(x + 20 * s), S(arm_y)), (S(x + 34 * s), S(arm_y + up))], fill=coat_dark, width=S(9 * s))
    d.ellipse([S(x - 18 * s), S(body_top), S(x + 18 * s), S(body_top + 42 * s)],
              fill=skin, outline=(150, 96, 60), width=S(2))
    d.pieslice([S(x - 21 * s), S(body_top - 7), S(x + 21 * s), S(body_top + 34 * s)],
               180, 360, fill=coat)


# ------------------------------------------------------------------ scenes
def scene_heat(cfg, d, t, total):
    """Danakil-like: hot ground cross-section, magma, heat, acid pools."""
    sky_a, sky_b = cfg["sky"]
    for y in range(0, S(H)):
        d.line([(0, y), (S(W), y)], fill=lerp(sky_a, sky_b, y / S(H)))
    # acid pools on the surface
    d.rectangle([S(0), S(760), S(W), S(905)], fill=(226, 222, 196))
    for i, (px, pr, col) in enumerate(((120, 96, (150, 196, 92)), (330, 120, (196, 214, 96)),
                                       (560, 86, (126, 186, 96)))):
        d.ellipse([S(px - pr), S(852 - pr * 0.32), S(px + pr), S(852 + pr * 0.32)], fill=col)
        d.ellipse([S(px - pr * 0.7), S(846 - pr * 0.22), S(px + pr * 0.7), S(846 + pr * 0.22)],
                  fill=lerp(col, (255, 255, 255), 0.25))
    # sulfur crust
    for i, bx in enumerate(range(30, W, 78)):
        d.polygon([(S(bx), S(760)), (S(bx + 34), S(742)), (S(bx + 62), S(766)), (S(bx + 30), S(772))],
                  fill=(236, 214, 120))
    # ground strata
    d.rectangle([S(0), S(905), S(W), S(H)], fill=(120, 96, 84))
    for i, yy in enumerate(range(940, H, 58)):
        d.line([(S(0), S(yy)), (S(W), S(yy + 10))],
               fill=lerp((150, 116, 96), (92, 70, 64), i / 6), width=S(3))
    # magma layer with glow
    glow = 0.55 + 0.45 * math.sin(t * 2.2)
    d.rectangle([S(0), S(1150), S(W), S(H)], fill=(196, 74, 32))
    for i, yy in enumerate(range(1150, H, 26)):
        d.line([(S(0), S(yy)), (S(W), S(yy + 6))],
               fill=lerp((246, 150, 60), (216, 92, 40), i / 5), width=S(2))
    for bx in (110, 300, 520):
        r = 40 + 12 * math.sin(t * 1.6 + bx)
        d.ellipse([S(bx - r), S(H - 90 - r * 0.4), S(bx + r), S(H - 90 + r * 0.4)],
                  fill=(255, 214, 130))
    # heat arrows rising out of the magma
    p = ease((t - total * 0.18) / 1.2)
    if p > 0:
        for i, ax in enumerate((150, 360, 570)):
            for k in range(4):
                ph = (t * 0.55 + k * 0.25 + i * 0.1) % 1.0
                ay = 1140 - ph * 300
                col = lerp((255, 190, 110), (255, 244, 200), 1 - ph)
                a = int(230 * p * (1 - abs(ph - 0.5)))
                d.polygon([(S(ax - 13), S(ay)), (S(ax + 13), S(ay)), (S(ax), S(ay - 28))],
                          fill=(*col, max(0, a)))
                d.rectangle([S(ax - 5), S(ay), S(ax + 5), S(ay + 30)], fill=(*col, max(0, a)))
    character(d, 520, 760, t, shiver=(t > total * 0.5), scale=0.95,
              coat=(246, 246, 246), coat_dark=(200, 202, 208), skin=(238, 190, 150))
    if t > total * 0.12:
        lx, ly = label(d, 42, 470, "+49°", (255, 196, 120))
        leader(d, lx, ly, 120, 700)
    if t > total * 0.45:
        lx, ly = label(d, 470, 980, "+180°", (255, 220, 150))
        leader(d, lx - 8, ly, 380, 1220)


def scene_depth(cfg, d, t, total):
    """Mariana-like: vertical water column, depth ruler, pressure, sub."""
    for y in range(0, S(H)):
        k = y / S(H)
        d.line([(0, y), (S(W), y)], fill=lerp((64, 150, 186), (6, 18, 34), k ** 0.75))
    # light shafts
    for i, sx in enumerate((120, 300, 500)):
        a = int(28 * (1 - t / max(1, total)))
        d.polygon([(S(sx - 40), S(0)), (S(sx + 40), S(0)), (S(sx + 130), S(760)), (S(sx - 90), S(760))],
                  fill=(210, 240, 255, max(0, a)))
    # depth ruler
    d.line([(S(620), S(120)), (S(620), S(1160))], fill=(180, 205, 225, 170), width=S(3))
    for mark, meters in ((120, "0"), (330, "1 000"), (560, "4 000"), (860, "8 000"), (1120, "11 000")):
        d.line([(S(606), S(mark)), (S(636), S(mark))], fill=(200, 220, 240, 200), width=S(3))
        d.text((S(640), S(mark - 14)), meters, font=F_TICK, fill=(214, 232, 246))
    # sea floor
    d.polygon([(S(0), S(1180)), (S(150), S(1150)), (S(330), S(1195)), (S(520), S(1160)),
               (S(720), S(1190)), (S(720), S(H)), (S(0), S(H))], fill=(34, 44, 58))
    # creatures (simple silhouettes)
    for i, (fx, fy, s_) in enumerate(((120, 320, 1.0), (250, 520, 0.7), (430, 700, 0.55),
                                      (180, 900, 0.4), (520, 980, 0.35))):
        drift = math.sin(t * 0.6 + i) * 14
        x, y = fx + drift, fy
        d.ellipse([S(x - 26 * s_), S(y - 12 * s_), S(x + 26 * s_), S(y + 12 * s_)],
                  fill=(150, 190, 210, 190))
        d.polygon([(S(x + 24 * s_), S(y)), (S(x + 44 * s_), S(y - 12 * s_)),
                   (S(x + 44 * s_), S(y + 12 * s_))], fill=(150, 190, 210, 190))
    # descending probe
    p = ease(t / max(1.0, total * 0.9))
    py = 140 + p * 940
    d.rounded_rectangle([S(300), S(py), S(360), S(py + 76)], radius=S(14), fill=(236, 240, 244))
    d.ellipse([S(322), S(py + 10), S(338), S(py + 26)], fill=(120, 200, 235))
    d.line([(S(330), S(py - 26)), (S(330), S(py))], fill=(230, 236, 242), width=S(4))
    # pressure badge follows the probe
    if p > 0.05:
        bar = int(p * 1100)
        lx, ly = label(d, 40, max(150, py - 40), f"{bar} атм", (255, 208, 150))
        leader(d, lx, ly, 300, py + 38)
    character(d, 130, 1150, t, scale=0.72, coat=(240, 180, 60), coat_dark=(190, 130, 30))


def scene_permafrost(cfg, d, t, total):
    """Permafrost: soil cross-section, thaw layer grows, methane bubbles."""
    sky_a, sky_b = cfg["sky"]
    for y in range(0, S(H)):
        d.line([(0, y), (S(W), y)], fill=lerp(sky_a, sky_b, y / S(H)))
    d.rectangle([S(0), S(300), S(W), S(320)], fill=(226, 234, 242))       # horizon line
    # tundra ground
    d.rectangle([S(0), S(320), S(W), S(430)], fill=(150, 138, 106))
    d.rectangle([S(0), S(320), S(W), S(342)], fill=(206, 226, 206))
    for i, bx in enumerate(range(0, W, 46)):
        d.line([(S(bx), S(322)), (S(bx + 8), S(300))], fill=(120, 160, 130), width=S(3))
    # permafrost body
    d.rectangle([S(0), S(430), S(W), S(H)], fill=(146, 160, 172))
    for i, yy in enumerate(range(470, H, 62)):
        d.line([(S(0), S(yy)), (S(W), S(yy + 8))], fill=(132, 148, 162), width=S(3))
    # ice wedges
    for wx in (150, 360, 570):
        d.polygon([(S(wx - 46), S(440)), (S(wx + 46), S(440)),
                   (S(wx + 16), S(1120)), (S(wx - 16), S(1120))],
                  fill=(206, 228, 240), outline=(168, 200, 220))
    # thaw layer grows with time
    thaw = 430 + ease(t / max(1.0, total * 0.85)) * 420
    d.rectangle([S(0), S(430), S(W), S(thaw)], fill=(120, 106, 84))
    d.line([(S(0), S(thaw)), (S(W), S(thaw))], fill=(244, 226, 190), width=S(5))
    if t > total * 0.3:
        lx, ly = label(d, 470, max(470, thaw - 96), "проталина", (255, 220, 170))
        leader(d, lx - 6, ly, 400, thaw)
    # methane bubbles rising through the column
    p = ease((t - total * 0.28) / 1.0)
    if p > 0:
        for i in range(14):
            ph = (t * 0.42 + i * 0.13) % 1.0
            bx = 90 + (i * 47) % 540
            by = (thaw + 40) - ph * (thaw + 40 - 420)
            r = 5 + (i % 3) * 3
            d.ellipse([S(bx - r), S(by - r), S(bx + r), S(by + r)],
                      fill=(226, 240, 235, int(200 * p)))
    character(d, 560, 330, t, shiver=(t > total * 0.55), scale=0.8,
              coat=(70, 110, 150), coat_dark=(40, 70, 100))
    if t > total * 0.15:
        lx, ly = label(d, 36, 210, "−12°", (170, 214, 250))
        leader(d, lx, ly, 120, 300)


SCENES = {"heat": scene_heat, "depth": scene_depth, "permafrost": scene_permafrost}


def render(name, text, scene_key, cfg, out_dir):
    audio, marks = synthesize(text, out_dir)
    total = audio_duration(audio)
    cues = build_cues(marks)
    frames = os.path.join(out_dir, "frames")
    os.makedirs(frames, exist_ok=True)
    for f in os.listdir(frames):
        os.remove(os.path.join(frames, f))

    n = int(round((total + 0.5) * FPS))
    rnd = random.Random(3)
    parts = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(14, 44),
              rnd.choice([1.3, 1.8, 2.4])) for _ in range(90)]
    draw_scene = SCENES[scene_key]

    for f in range(n):
        t = f / FPS
        img = Image.new("RGB", (S(W), S(H)), (30, 40, 52))
        d = ImageDraw.Draw(img, "RGBA")
        draw_scene(cfg, d, t, total)
        for (x0, y0, sp, sz) in parts:
            x = (x0 + math.sin(t * 0.7 + x0) * 10) % W
            y = (y0 + sp * t) % H
            d.ellipse([S(x), S(y), S(x + sz), S(y + sz)], fill=(255, 255, 255, 70))
        word = None
        for k, (s0, e0, lab) in enumerate(cues):
            nxt = cues[k + 1][0] if k + 1 < len(cues) else e0 + 0.4
            if s0 - 0.05 <= t < max(e0 + 0.12, nxt - 0.02):
                word = lab
                break
        caption(d, word)
        img.resize((W, H), Image.LANCZOS).save(os.path.join(frames, f"{f:04d}.png"))

    out = os.path.join(ROOT, "storage", f"{name}.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames, "%04d.png"), "-i", audio,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print(f"{name}: {total:.1f}s, {n} frames -> {out}")
    return out


EPISODES = [
    ("cartoon-danakil",
     "Данакиль — самое жаркое обитаемое место на планете. Днём здесь плюс сорок девять, "
     "а земля под ногами горячее кипятка. Под коркой соли лежит магма: она подходит так близко, "
     "что вода в лужах закипает, а воздух пахнет серой. В этих лужах кислота: она разъедает одежду "
     "за минуты. Люди живут здесь тысячу лет и добывают соль. Самый жаркий день в году для них обычный.",
     "heat", {"sky": ((236, 214, 186), (244, 226, 200))}),
    ("cartoon-mariana",
     "Океан кажется глубоким, но настоящая бездна начинается глубже километра. "
     "В Марианской впадине одиннадцать тысяч метров: если бросить туда Эверест, вершина останется под водой. "
     "На дне давление больше тысячи атмосфер, а свет не доходит совсем. "
     "И всё равно там есть жизнь: рыбы, креветки и микробы, которые живут без солнца. "
     "Каждый спуск туда — это часы падения в полной темноте.",
     "depth", {}),
    ("cartoon-permafrost",
     "Вечная мерзлота кажется вечной только на вид. Под тонким слоем почвы лежит лёд, "
     "и он держит землю как бетон. Пока мороз держится, лёд не тает, а дома стоят на сваях. "
     "Когда почва теплеет, лёд превращается в воду, и земля проседает. "
     "Вместе с водой освобождается метан: он был заморожен тысячи лет. "
     "Чем глубже проталина, тем больше газа уходит в воздух.",
     "permafrost", {"sky": ((206, 220, 234), (232, 240, 246))}),
]


if __name__ == "__main__":
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for name, text, scene, cfg in EPISODES:
        if only and only != name:
            continue
        render(name, text, scene, cfg, os.path.join(ROOT, "storage", "cartoons", name))
