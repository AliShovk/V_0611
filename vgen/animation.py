"""Stage 6 — анимация кадров и сборка mp4."""
import json
import os
import subprocess

from PIL import Image

from vgen import sfx
from vgen.voice import FFMPEG
from vgen.renderers import lock

FPS = 30
W, H = 720, 1280
SS = 2


def word_time(marks, needle, default):
    needle = needle.lower()
    for (start, _, word) in marks:
        if needle in word.lower():
            return start
    return default


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def build(project, voice, storyboard, out_dir, renderer="lock"):
    total = voice["total"]
    marks = voice["marks"]
    anchors = project["timeline"]

    t_pump = word_time(marks, anchors["pump"], total * 0.45)
    t_eight = word_time(marks, anchors["eight"], total * 0.65)
    t_gates = word_time(marks, anchors["gates_close"], total * 0.30)
    t_panama = word_time(marks, anchors["panama"], total * 0.78)
    t_end = word_time(marks, anchors["end"], total * 0.95)

    scenes = storyboard["scenes"]
    frames_dir = os.path.join(out_dir, "assets", "frames")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        if f.endswith(".png"):
            os.remove(os.path.join(frames_dir, f))

    n = int(total * FPS)
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
               "scene_t": 0.0, "scene_dur": 1.0}

        # сцена по времени
        idx = 0
        for j, sc in enumerate(scenes):
            if t >= sc["t0"]:
                idx = j
        name = scenes[idx]["id"]
        ctx["scene_t"] = t - scenes[idx]["t0"]
        ctx["scene_dur"] = max(0.1, scenes[idx]["t1"] - scenes[idx]["t0"])

        # кроссфейд 0.35 с на стыке
        if idx > 0 and t - scenes[idx]["t0"] < 0.35:
            prev = scenes[idx - 1]["id"]
            a = ease((t - scenes[idx]["t0"]) / 0.35)
            img_a = lock.render(prev, t, ctx).convert("RGBA")
            img_b = lock.render(name, t, ctx).convert("RGBA")
            img = Image.blend(img_a, img_b, a)
        else:
            img = lock.render(name, t, ctx).convert("RGBA")

        img.convert("RGB").save(os.path.join(frames_dir, f"f{i:05d}.png"))
        if i % 200 == 0:
            print("frame", i, "/", n)

    silent = os.path.join(out_dir, "assets", "video_silent.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames_dir, "f%05d.png"),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent], check=True)

    # SFX
    events = [(0.02, "boom", 0.5), (t_gates, "crack", 0.35), (t_pump, "hiss", 0.45),
              (t_eight, "pop", 0.35), (t_panama, "chime", 0.45), (t_end - 0.4, "whoosh", 0.3)]
    fx = sfx.build_track(total, events, os.path.join(out_dir, "assets", "sfx.wav"))

    mixed = os.path.join(out_dir, "assets", "video_mixed.mp4")
    sfx.mix(silent, voice["wav"], fx, mixed, video_sfx_gain=0.75)

    final = os.path.join(out_dir, "final.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", mixed,
                    "-vf", "scale=1080:1920:flags=lanczos",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", final], check=True)
    return final
