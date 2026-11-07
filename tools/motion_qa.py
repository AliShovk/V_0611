"""Проверка «кадр не залипает»: сколько движения в каждой сцене.

  python tools/motion_qa.py out/<ep>/final.mp4 out/<ep>/storyboard.json [--fps 3]

Считает среднюю разницу между соседними кадрами (0–100) и число визуальных
событий (пиков движения). Сцена со score ниже порога — кандидат на переделку.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vgen.voice import FFMPEG

THRESHOLD = 1.2        # средняя разница 0–100 (референс даёт ~3.0)
MIN_EVENTS = 2         # сколько раз картинка заметно меняется внутри сцены
EVENT_DIFF = 1.5       # порог «события» на кадр


def extract(video, fps, outdir, scale=180):
    pattern = os.path.join(outdir, "f%05d.png")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", video,
                    "-vf", f"fps={fps},scale={scale}:-1,format=gray",
                    pattern], check=True)
    return sorted(os.path.join(outdir, f) for f in os.listdir(outdir) if f.endswith(".png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("storyboard")
    ap.add_argument("--fps", type=float, default=3.0)
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    a = ap.parse_args()

    board = json.load(open(a.storyboard, encoding="utf-8"))
    scenes = board["scenes"]
    total = board["total"]

    with tempfile.TemporaryDirectory() as tmp:
        files = extract(a.video, a.fps, tmp)
        diffs = []
        prev = None
        for f in files:
            arr = np.asarray(Image.open(f), dtype=np.int16)
            if prev is not None:
                diffs.append(float(np.abs(arr - prev).mean()) / 255.0 * 100.0)
            prev = arr

    times = [i / a.fps for i in range(len(diffs))]
    print(f"кадров: {len(files)}, движение по кадрам: {len(diffs)}\n")
    bad = []
    for sc in scenes:
        idx = [i for i, t in enumerate(times) if sc["t0"] <= t < sc["t1"]]
        if not idx:
            continue
        vals = [diffs[i] for i in idx]
        if sc["t1"] - sc["t0"] < 2.5:
            print(f"—    {sc['id']:<10} {sc['t0']:>6.2f}–{sc['t1']:<6.2f} короткая сцена, не оцениваем")
            continue
        score = float(np.mean(vals))
        events = int(sum(1 for v in vals if v >= EVENT_DIFF))
        alive = float(np.mean([1 if v > 0.15 else 0 for v in vals]))
        flag = "OK " if score >= a.threshold and alive >= 0.5 else "СТАТИКА"
        print(f"{flag} {sc['id']:<10} {sc['t0']:>6.2f}–{sc['t1']:<6.2f} "
              f"score {score:5.2f}  живых {alive*100:3.0f}%  событий {events}")
        if flag != "OK ":
            bad.append(sc["id"])

    hook = [diffs[i] for i, t in enumerate(times) if t < 2.0]
    if hook:
        print(f"\nхук (0–2 с): score {np.mean(hook):.2f}, событий "
              f"{sum(1 for v in hook if v >= EVENT_DIFF)}")
    print("\nитог:", "все сцены живые" if not bad else "переделать: " + ", ".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
