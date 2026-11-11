"""Приклеивает фирменную концовку (GPTunnel / QANTCORE) ко финальному mp4.

Концовка живёт в assets/outro/gptunnel.mp4 (720x1280, 30 fps, со звуком).
Она приводится к 1080x1920 и склеивается с роликом через filter_complex concat.
"""
import os
import subprocess

from imageio_ffmpeg import get_ffmpeg_exe

FF = get_ffmpeg_exe()
DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "assets", "outro", "gptunnel.mp4")


def has_audio(path):
    out = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stderr
    return "Audio:" in out


def probe_duration(path):
    out = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stderr
    for line in out.splitlines():
        if "Duration:" in line:
            hms = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = hms.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def attach(final, outro=None, out_dir=None, crf=19):
    """Возвращает путь к новому файлу с концовкой (или исходный, если концовки нет)."""
    outro = outro or DEFAULT
    if not os.path.exists(outro):
        print(f"  ! концовка не найдена: {outro}")
        return final
    out_dir = out_dir or os.path.dirname(final)
    dst = os.path.join(out_dir, "final_outro.mp4")

    v_out = ("scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
             "crop=1080:1920,setsar=1,fps=30,format=yuv420p")
    a_out = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"

    if has_audio(outro):
        graph = (f"[1:v]{v_out}[v1];[1:a]{a_out}[a1];[0:v]{v_out}[v0];[0:a]{a_out}[a0];"
                 f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]")
    else:
        dur = probe_duration(outro)
        graph = (f"[1:v]{v_out}[v1];[0:v]{v_out}[v0];[0:a]{a_out}[a0];"
                 f"anullsrc=r=48000:cl=stereo,atrim=0:{dur:.3f}[a1];"
                 f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]")

    cmd = [FF, "-y", "-v", "error", "-i", final, "-i", outro,
           "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-color_range", "tv",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", dst]
    subprocess.run(cmd, check=True)

    if os.path.getsize(dst) > 0:
        return dst
    return final
