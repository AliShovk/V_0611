"""Предпросмотр без озвучки: контактные листы сцен, галерея тем, короткий клип.

  python -m vgen.studio.preview episodes/x/project.json            # листы по сценам
  python -m vgen.studio.preview episodes/x/project.json --scene id # крупно одна сцена (5 кадров)
  python -m vgen.studio.preview episodes/x/project.json --themes   # хук во всех темах
  python -m vgen.studio.preview episodes/x/project.json --clip 0:4 # mp4 (без звука) окна 0–4 c
Использует out/<slug>/words.json, если озвучка уже есть; иначе синтетическая разметка слов.
"""
import argparse
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

from vgen import postfx
from vgen.studio import engine, themes


def _marks(project, out):
    wj = os.path.join(out, "words.json")
    if os.path.exists(wj):
        d = json.load(open(wj, encoding="utf-8"))
        return [tuple(m) for m in d["marks"]], d["total"], True
    m, total = engine.fake_marks(project["script"]["narration"])
    return m, total, False


def _label(img, text):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width, 34], fill=(0, 0, 0))
    d.text((8, 9), text, fill=(255, 220, 140))
    return img


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--scene")
    ap.add_argument("--themes", action="store_true")
    ap.add_argument("--clip")
    ap.add_argument("--out", default="out")
    ap.add_argument("--no-post", action="store_true")
    a = ap.parse_args(argv)
    project = json.load(open(a.project, encoding="utf-8"))
    out = os.path.join(a.out, project["slug"])
    pv = os.path.join(out, "preview")
    os.makedirs(pv, exist_ok=True)
    engine.POST = not a.no_post
    marks, total, real = _marks(project, out)
    errs, warns = engine.validate(project)
    for e in errs:
        print("✗", e)
    for w in warns:
        print("⚠", w)
    if errs:
        return 1
    base = os.path.dirname(os.path.abspath(a.project))
    tl = engine.make_tl(project, marks, total, base)
    print(("тайминги из озвучки" if real else "тайминги СИНТЕТИЧЕСКИЕ (озвучки нет)"), "· %.1f с" % total)
    for sc in tl["scenes"]:
        print("  %-10s %-8s %5.2f–%5.2f" % (sc["id"], sc["shot"], sc["_t0"], sc["_t1"]))

    if a.themes:
        cells = []
        for name in themes.THEMES:
            p2 = json.loads(json.dumps(project))
            p2["theme"] = name
            for s in p2["scenes"]:
                s.pop("theme", None)
            t2 = engine.make_tl(p2, marks, total, base)
            sc = t2["scenes"][0]
            cells.append(_label(engine.render_frame(t2, sc["_t0"] + 1.6).resize((360, 640)), name))
        sheet = Image.new("RGB", (360 * 3, 640 * 2))
        for i, c in enumerate(cells):
            sheet.paste(c, ((i % 3) * 360, (i // 3) * 640))
        path = os.path.join(pv, "themes.png")
        sheet.save(path)
        print(path)
        return 0

    if a.clip:
        t0, t1 = [float(x) for x in a.clip.split(":")]
        fr = os.path.join(pv, "clip")
        os.makedirs(fr, exist_ok=True)
        n = int((t1 - t0) * engine.FPS)
        for i in range(n):
            engine.render_frame(tl, t0 + i / engine.FPS).save(os.path.join(fr, "c%04d.jpg" % i), quality=92)
        mp4 = os.path.join(pv, "clip.mp4")
        ff = os.environ.get("FFMPEG") or "ffmpeg"
        subprocess.run([ff, "-y", "-v", "error", "-framerate", str(engine.FPS), "-i", os.path.join(fr, "c%04d.jpg"),
                        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", mp4], check=True)
        print(mp4)
        return 0

    if a.scene:
        sc = next(s for s in tl["scenes"] if s["id"] == a.scene)
        d = sc["_t1"] - sc["_t0"]
        ts = [sc["_t0"] + d * f for f in (0.06, 0.25, 0.5, 0.75, 0.97)]
        cells = [_label(engine.render_frame(tl, t).resize((432, 768)), "%s t=%.1f" % (sc["id"], t)) for t in ts]
        sheet = Image.new("RGB", (432 * 5, 768))
        for i, c in enumerate(cells):
            sheet.paste(c, (i * 432, 0))
        path = os.path.join(pv, "scene_%s.png" % a.scene)
        sheet.save(path)
        print(path)
        return 0

    paths = []
    scs = tl["scenes"]
    for g in range(0, len(scs), 3):
        grp = scs[g:g + 3]
        sheet = Image.new("RGB", (360 * 3, 640 * len(grp)))
        for r, sc in enumerate(grp):
            d = sc["_t1"] - sc["_t0"]
            for c, f in enumerate((0.12, 0.55, 0.95)):
                t = sc["_t0"] + d * f
                sheet.paste(_label(engine.render_frame(tl, t).resize((360, 640)), "%s/%s t=%.1f" % (sc["id"], sc["shot"], t)),
                            (c * 360, r * 640))
        path = os.path.join(pv, "sheet_%02d.png" % (g // 3 + 1))
        sheet.save(path)
        paths.append(path)
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
