"""Быстрый звуковой дизайн: синтез SFX и подмешивание к озвучке.

Кинды: boom, whoosh, pop, riser, chime, tick, crack.
"""
import math
import os
import subprocess

import numpy as np

from vgen.voice import FFMPEG

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _env(n, attack=0.01, decay=0.3, power=2.0):
    a = max(1, int(attack * SR))
    d = max(1, n - a)
    env = np.concatenate([np.linspace(0, 1, a), np.linspace(1, 0, d) ** power])
    return env[:n]


def gen(kind, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    rnd = np.random.default_rng(abs(hash(kind)) % 2 ** 32)

    if kind == "boom":
        sig = np.sin(2 * np.pi * (58 - 18 * t / dur) * t) * 0.9
        sig += rnd.normal(0, 0.25, n) * np.exp(-t * 26)
        return sig * _env(n, 0.004, dur, 2.6) * 0.9

    if kind == "whoosh":
        noise = rnd.normal(0, 1, n)
        k = np.hanning(9)
        noise = np.convolve(noise, k / k.sum(), mode="same")
        sweep = np.sin(2 * np.pi * (300 + 1500 * t / dur) * t) * 0.25
        return (noise * 0.8 + sweep) * _env(n, 0.05, dur, 1.8) * 0.55

    if kind == "pop":
        f = 900 - 500 * t / dur
        return np.sin(2 * np.pi * f * t) * _env(n, 0.003, dur, 3.2) * 0.5

    if kind == "riser":
        f = 180 + 620 * (t / dur) ** 1.6
        sig = np.sin(2 * np.pi * f * t) * 0.5
        sig += rnd.normal(0, 0.12, n)
        return sig * np.linspace(0.05, 1.0, n) ** 1.4 * 0.45

    if kind == "chime":
        sig = (np.sin(2 * np.pi * 880 * t) * 0.5 + np.sin(2 * np.pi * 1320 * t) * 0.3
               + np.sin(2 * np.pi * 1760 * t) * 0.15)
        return sig * _env(n, 0.006, dur, 2.2) * 0.42

    if kind == "tick":
        return np.sin(2 * np.pi * 1500 * t) * _env(n, 0.002, dur, 3.0) * 0.35

    if kind == "hiss":
        noise = rnd.normal(0, 1, n)
        noise = np.convolve(noise, np.hanning(7) / np.hanning(7).sum(), mode="same")
        env = np.exp(-t * 2.2) * np.minimum(1.0, t * 22)
        return (noise * 0.7 + np.sin(2 * np.pi * 3200 * t) * 0.05) * env * 0.5

    if kind == "crack":
        noise = rnd.normal(0, 1, n)
        noise = np.convolve(noise, np.hanning(5) / np.hanning(5).sum(), mode="same")
        sig = noise * np.exp(-t * 18) + np.sin(2 * np.pi * 120 * t) * np.exp(-t * 9)
        return sig * 0.85

    raise ValueError(f"unknown sfx kind: {kind}")


DUR = {"boom": 0.9, "whoosh": 0.45, "pop": 0.18, "riser": 0.8,
       "chime": 1.1, "tick": 0.07, "crack": 1.2, "hiss": 1.0}


def build_track(total, events, path):
    """events: [(time, kind, gain)] -> wav на всю длину ролика."""
    n = int((total + 0.4) * SR)
    track = np.zeros(n, dtype=np.float32)
    for when, kind, gain in events:
        clip = gen(kind, DUR[kind]).astype(np.float32) * gain
        start = int(when * SR)
        end = min(n, start + clip.size)
        if start >= n:
            continue
        track[start:end] += clip[:end - start]
    peak = float(np.max(np.abs(track))) or 1.0
    if peak > 0.98:
        track = track / peak * 0.98
    pcm = (track * 32767).astype(np.int16)
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


def mix(video_in, narration, sfx_wav, video_out, video_sfx_gain=0.85):
    """Подмешивает SFX к озвучке и пересобирает mp4 без перекодирования видео."""
    subprocess.run([FFMPEG, "-y", "-v", "error",
                    "-i", video_in, "-i", narration, "-i", sfx_wav,
                    "-filter_complex",
                    f"[1:a]volume=1.0[vo];[2:a]volume={video_sfx_gain}[fx];"
                    "[vo][fx]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", video_out], check=True)
    return video_out
