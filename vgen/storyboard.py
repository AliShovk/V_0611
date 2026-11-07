"""Storyboard: сцены с якорными словами + расчёт таймингов из word-разметки."""
import json
import os


def word_time(marks, needle, default):
    needle = needle.lower()
    for (start, _, word) in marks:
        if needle in word.lower():
            return start
    return default


def build(project, voice_info, out_dir):
    total = voice_info["total"]
    scenes = []
    for sc in project["scenes"]:
        t0 = word_time(voice_info["marks"], sc["anchor"], sc.get("t0", 0.0))
        scenes.append({
            "id": sc["id"],
            "title": sc["title"],
            "t0": round(t0, 2),
            "anchor": sc["anchor"],
            "camera": sc.get("camera", "wide"),
            "objects": sc["objects"],
            "labels": sc.get("labels", []),
            "note": sc.get("note", ""),
        })
    for i, sc in enumerate(scenes):
        fixed = project["scenes"][i].get("t1_fixed")
        sc["t1"] = fixed if fixed else (scenes[i + 1]["t0"] if i + 1 < len(scenes) else round(total, 2))
    data = {"episode": project["title"], "total": round(total, 2), "scenes": scenes}
    path = os.path.join(out_dir, "storyboard.json")
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return data, path
