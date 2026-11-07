"""Stage 6 — анимация кадров и сборка mp4.

Скорость: кадры рендерятся параллельно (ProcessPoolExecutor), а сборка идёт
одним проходом ffmpeg из последовательности кадров вместе с озвучкой и SFX.
Раньше было три кодирования подряд (silent → mixed → final) — это и съедало время.
"""
import json
import math
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor

from PIL import Image

from vgen import sfx
from vgen.voice import FFMPEG
from vgen import renderers


def module(name):
    import importlib
    return importlib.import_module(f"vgen.renderers.{name}")

FPS = 30
JPEG = os.environ.get("FRAME_JPEG") == "1"
W, H = 720, 1280
SS = 2


def word_time(marks, needle, default):
    if not needle:
        return default
    needle = needle.lower()
    for (start, _, word) in marks:
        if needle in word.lower():
            return start
    return default


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def _render_one(job):
    """Один кадр в отдельном процессе. Всё, что нужно, приходит в job."""
    (i, t, name, prev, blend_k, ctx, frames_dir, renderer) = job
    mod = module(renderer)
    if prev:
        img_a = mod.render(prev, t, ctx).convert("RGBA")
        img_b = mod.render(name, t, ctx).convert("RGBA")
        img = Image.blend(img_a, img_b, blend_k)
    else:
        img = mod.render(name, t, ctx).convert("RGBA")
    if JPEG:
        img.convert("RGB").save(os.path.join(frames_dir, f"f{i:05d}.jpg"), quality=95)
    else:
        img.convert("RGB").save(os.path.join(frames_dir, f"f{i:05d}.png"))
    return i


def build(project, voice, storyboard, out_dir, renderer="lock"):
    total = voice["total"]
    marks = voice["marks"]
    anchors = project.get("timeline") or {}

    t_pump = word_time(marks, anchors.get("pump", ""), total * 0.45)
    t_eight = word_time(marks, anchors.get("eight", ""), total * 0.65)
    t_gates = word_time(marks, anchors.get("gates_close", ""), total * 0.30)
    t_panama = word_time(marks, anchors.get("panama", ""), total * 0.78)
    t_end = word_time(marks, anchors.get("end", ""), total * 0.95)
    mod = module(project.get("renderer", "lock"))
    rname = project.get("renderer", "lock")

    # субтитры с подсветкой ключевых слов (стиль night-vector)
    hl_keys = [k.lower() for k in project.get("keywords", [])]
    hl_cues = []
    if project.get("caption_style") == "highlight":
        toks = project["script"]["narration"].split()
        i = 0
        while i < len(toks):
            j = i
            while (j + 1 < len(toks) and (j - i + 1) < 4
                   and not toks[j].endswith((",", ".", "!", "?"))):
                j += 1
            st = marks[min(i, len(marks) - 1)][0] if marks else 0.0
            en = marks[min(j, len(marks) - 1)][1] if marks else st + 1.0
            hl_cues.append((st, en, " ".join(toks[i:j + 1])))
            i = j + 1

    scenes = storyboard["scenes"]
    frames_dir = os.path.join(out_dir, "assets", "frames")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        if f.endswith(".png") or f.endswith(".jpg"):
            os.remove(os.path.join(frames_dir, f))

    n = int(total * FPS)

    # план кадров считаем заранее: в воркеры уходят только простые типы
    jobs = []
    for i in range(n):
        t = i / FPS

        level = 0.06 + 0.94 * ease((t - t_pump) / max(0.6, t_eight - t_pump))
        gate_k = ease((t - t_gates) / 1.1)
        steps_done = 0
        if t >= t_eight:
            steps_done = 1
        if t >= t_panama:
            steps_done = 2
        if t >= t_end - 1.0:
            steps_done = 3
        ctx = {"level": level, "gate_k": gate_k, "steps_done": steps_done,
               "scene_t": 0.0, "scene_dur": 1.0, "total": total,
               "caption_text": "", "caption_hl": ()}
        if hl_cues:
            cur = None
            for (st, en, txt) in hl_cues:
                if st <= t:
                    cur = txt
            if cur:
                ctx["caption_text"] = cur
                ctx["caption_hl"] = tuple(
                    w for w in cur.split()
                    if any(k in w.lower() for k in hl_keys))

        idx = 0
        for j, sc in enumerate(scenes):
            if t >= sc["t0"]:
                idx = j
        name = scenes[idx]["id"]
        ctx["scene_t"] = t - scenes[idx]["t0"]
        ctx["scene_dur"] = max(0.1, scenes[idx]["t1"] - scenes[idx]["t0"])

        prev = None
        blend_k = 0.0
        if idx > 0 and t - scenes[idx]["t0"] < 0.35:
            prev = scenes[idx - 1]["id"]
            blend_k = ease((t - scenes[idx]["t0"]) / 0.35)

        jobs.append((i, t, name, prev, blend_k, ctx, frames_dir, rname))

    # параллельный рендер; число процессов = ядра - 1, но не больше 8
    workers = int(os.environ.get("VGEN_WORKERS") or
                  max(1, min(8, (os.cpu_count() or 2))))
    done = 0
    if workers == 1:
        for job in jobs:
            _render_one(job)
            done += 1
            if done % 200 == 0:
                print("frame", done, "/", n, flush=True)
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for _ in ex.map(_render_one, jobs, chunksize=8):
                done += 1
                if done % 200 == 0:
                    print("frame", done, "/", n, "workers", workers, flush=True)

    # SFX
    if anchors:
        events = [(0.02, "boom", 0.5), (t_gates, "crack", 0.35), (t_pump, "hiss", 0.45),
                  (t_eight, "pop", 0.35), (t_panama, "chime", 0.45), (t_end - 0.4, "whoosh", 0.3)]
    else:
        events = [(0.02, "boom", 0.5), (total * 0.45, "pop", 0.3),
                  (total * 0.7, "chime", 0.4), (total - 0.6, "whoosh", 0.3)]
    fx = sfx.build_track(total, events, os.path.join(out_dir, "assets", "sfx.wav"))

    final = os.path.join(out_dir, "final.mp4")
    pattern = os.path.join(frames_dir, "f%05d.jpg" if JPEG else "f%05d.png")
    preset = project.get("preset") or "faster"
    crf = str(project.get("crf") or 19)

    kb = ("zoompan=z='min(1+0.0012*on,1.16)':x='iw/2-(iw/zoom/2)':"
          "y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,") if project.get("kenburns") else ""

    if project.get("post"):
        vf = (kb + "split=2[a][b];"
              # bloom считаем на половинном разрешении: визуально то же, вдвое дешевле
              "[b]scale=540:960:flags=bilinear,gblur=sigma=6,"
              "scale=1080:1920:flags=bilinear,"
              "eq=brightness=-0.06:contrast=1.05[glow];"
              "[a][glow]blend=all_mode=screen:all_opacity=0.30[bl];"
              "[bl]colorbalance=rs=0.03:gs=0.0:bs=-0.03,"
              "eq=contrast=1.05:saturation=1.06,"
              "vignette=angle=PI/5,"
              "scale=1080:1920:flags=lanczos:in_range=full:out_range=tv,format=yuv420p[v]")
    else:
        vf = (kb + "scale=1080:1920:flags=lanczos:in_range=full:out_range=tv,"
              "format=yuv420p[v]")

    # один проход: кадры + голос + SFX → финал
    af = "[2:a]volume=0.75[fx];[1:a][fx]amix=inputs=2:duration=first:dropout_transition=0[a]"
    cmd = [FFMPEG, "-y", "-v", "error",
           "-framerate", str(FPS), "-i", pattern,
           "-i", voice["wav"], "-i", fx,
           "-filter_complex", f"[0:v]{vf};{af}",
           "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", preset, "-crf", crf,
           "-pix_fmt", "yuv420p", "-color_range", "tv",
           "-c:a", "aac", "-b:a", "160k",
           "-movflags", "+faststart", final]
    subprocess.run(cmd, check=True)
    return {"final": final, "frames": n, "total": total, "workers": workers}
