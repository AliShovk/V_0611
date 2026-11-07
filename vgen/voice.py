"""Stage 7 — озвучка Edge TTS, субтитры SRT, word-разметка для синхронизации."""
import asyncio
import hashlib
import random
import json
import os
import re
import subprocess
import time

import edge_tts

VOICE = os.environ.get("VOICE", "ru-RU-SvetlanaNeural")
RATE = os.environ.get("VOICE_RATE", "-4%")


def ffmpeg_bin():
    explicit = os.environ.get("FFMPEG")
    if explicit and os.path.exists(explicit):
        return explicit
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


FFMPEG = ffmpeg_bin()


def _say(text, path, voice, tries=8):
    async def run():
        marks = []
        com = edge_tts.Communicate(text, voice, rate=RATE, boundary="WordBoundary")
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
            last = f"tiny {os.path.getsize(path)}B"
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(min(20, 3 + attempt * 3) + random.uniform(0, 1.5))
    raise RuntimeError(f"TTS failed: {last}")


def duration(path):
    out = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True,
                         text=True, errors="ignore").stderr
    for line in out.splitlines():
        if "Duration" in line:
            h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def _split_narration(narration):
    """Длинные фразы режем по запятым: Edge TTS чаще срывается на длинных кусках."""
    out = []
    for sent in [x.strip() for x in re.split(r"(?<=[.!?])\s+", narration) if x.strip()]:
        if len(sent) <= 120:
            out.append(sent)
            continue
        cur = ""
        for piece in [p.strip() for p in sent.split(",") if p.strip()]:
            if not cur:
                cur = piece
            elif len(cur) + len(piece) < 95:
                cur = cur + ", " + piece
            else:
                out.append(cur + ",")
                cur = piece
        if cur:
            out.append(cur)
    return out


def build(project, out_dir):
    """voice.mp3 + voice.wav + words.json + subtitles.srt"""
    narration = project["script"]["narration"]
    sentences = _split_narration(narration)
    cache_dir = os.path.join(out_dir, "tts_cache")
    os.makedirs(cache_dir, exist_ok=True)
    parts, marks, offset = [], [], 0.0
    for i, sentence in enumerate(sentences):
        key = hashlib.md5((sentence + VOICE + RATE).encode("utf-8")).hexdigest()[:16]
        cached = os.path.join(cache_dir, key + ".mp3")
        meta = os.path.join(cache_dir, key + ".json")
        path = os.path.join(out_dir, f"part{i:02d}.mp3")
        if os.path.exists(cached) and os.path.getsize(cached) > 2000 and os.path.exists(meta):
            chunk = [tuple(x) for x in json.load(open(meta, encoding="utf-8"))]
            with open(cached, "rb") as src, open(path, "wb") as dst:
                dst.write(src.read())
        else:
            chunk = _say(sentence, path, VOICE)
            with open(path, "rb") as src, open(cached, "wb") as dst:
                dst.write(src.read())
            json.dump(chunk, open(meta, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(0.9)
        dur = duration(path)
        for (st, d, w) in chunk:
            marks.append((st + offset, d, w))
        offset += dur
        parts.append(path)

    mp3 = os.path.join(out_dir, "voice.mp3")
    lst = os.path.join(out_dir, "parts.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in parts:
            f.write("file '" + os.path.basename(p) + "'\n")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", os.path.abspath(lst),
                    "-c:a", "libmp3lame", "-b:a", "192k", os.path.abspath(mp3)], check=True)
    wav = os.path.join(out_dir, "voice.wav")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", mp3, "-ar", "44100", "-ac", "1", wav],
                   check=True)
    total = duration(wav)
    json.dump({"total": total, "marks": marks},
              open(os.path.join(out_dir, "words.json"), "w", encoding="utf-8"),
              ensure_ascii=False)

    # SRT: фразы по 2–3 слова
    cues, i = [], 0
    tokens = narration.split()
    while i < len(tokens):
        j = i
        while j + 1 < len(tokens) and (j - i + 1) < 3:
            if tokens[j].endswith((",", ".", "!", "?", "—")):
                break
            j += 1
        start = marks[i][0] if i < len(marks) else (cues[-1][1] if cues else 0)
        end = marks[min(j, len(marks) - 1)][1] if marks else start + 1.0
        text = " ".join(w.strip("—,") for w in tokens[i:j + 1]).rstrip(".,!?")
        cues.append((start, end, text))
        i = j + 1

    def ts(sec):
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

    lines = []
    for n, (a, b, text) in enumerate(cues, 1):
        lines += [str(n), f"{ts(a)} --> {ts(b)}", text, ""]
    srt = os.path.join(out_dir, "subtitles.srt")
    open(srt, "w", encoding="utf-8").write("\n".join(lines))
    return {"mp3": mp3, "wav": wav, "total": total, "marks": marks, "srt": srt}
