"""Прототип: сцена-хук крана v2 (vgen.kit / Skia) против старого рендерера.

  python tools/proto_crane_v2.py            # before_after.png + crane_hook_v2.mp4 (3 c)
  python tools/proto_crane_v2.py --still    # только PNG
"""
import os
import subprocess
import sys
from multiprocessing import Pool

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from vgen import postfx                      # noqa: E402
from vgen.renderers import crane, crane_v2   # noqa: E402


def _ffmpeg():
    if os.environ.get("FFMPEG"):
        return os.environ["FFMPEG"]
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


FFMPEG = _ffmpeg()

OUT = os.path.join(ROOT, "out", "crane_v2_proto")
FPS, DUR = 30, 3.0


def _frame(i):
    p = os.path.join(OUT, "frames", "f%05d.png" % i)
    crane_v2.render("hook", i / FPS).save(p)
    return p


def still(t=1.6):
    os.makedirs(OUT, exist_ok=True)
    old = crane.render("hook", t, {}).resize((1080, 1920), Image.LANCZOS)
    old = postfx.finish(old)                 # старый кадр тоже с пост-обработкой — честно
    new = crane_v2.render("hook", t)
    sheet = Image.new("RGB", (1080 * 2 + 30, 1920 + 90), (14, 18, 28))
    sheet.paste(old, (0, 90))
    sheet.paste(new, (1110, 90))
    d = ImageDraw.Draw(sheet)
    from vgen.palette import font
    d.text((20, 20), "ДО  (PIL-примитивы)", font=font(26), fill=(255, 170, 150))
    d.text((1130, 20), "ПОСЛЕ  (vgen.kit / Skia)", font=font(26), fill=(150, 240, 200))
    path = os.path.join(OUT, "before_after.png")
    sheet.convert("RGB").resize((sheet.width // 2, sheet.height // 2), Image.LANCZOS).save(path)
    print(path)


def video():
    os.makedirs(os.path.join(OUT, "frames"), exist_ok=True)
    n = int(DUR * FPS)
    with Pool() as pool:
        pool.map(_frame, range(n))
    mp4 = os.path.join(OUT, "crane_hook_v2.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", os.path.join(OUT, "frames", "f%05d.png"),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], check=True)
    print(mp4)


if __name__ == "__main__":
    still()
    if "--still" not in sys.argv:
        video()
