"""Studio-движок: любой ролик из декларативных сцен project.json.

project["theme"] — тема по умолчанию; project["scenes"][i]:
  {"id","shot","anchor","title", ...поля шота..., "theme"?, "plate"?, "cam"?}
Тайминги берутся из word-разметки озвучки: anchor (старт сцены) и at (появление элемента).
"""
import json
import os
import re
import subprocess

from vgen import postfx
from vgen.kit import Canvas, W, H, lin
from vgen.studio import themes
from vgen.studio.icons import ICONS
from vgen.studio.shots import SHOTS, LISTS, Ctx, ease

FPS = int(os.environ.get("VGEN_FPS", "30"))
XFADE = 0.32
POST = os.environ.get("VGEN_STUDIO_POST", "0") == "1"


# --- таймлайн ---------------------------------------------------------------------

def find(marks, needle, after=0.0):
    needle = needle.lower().strip()
    for (st, _, w) in marks:
        if st >= after - 0.01 and needle in w.lower():
            return st
    return None


def fake_marks(narration, wps=2.7):
    toks = [re.sub(r"[^\wё-]", "", w, flags=re.U) for w in narration.split()]
    toks = [w for w in toks if w]
    return [(0.25 + i / wps, 0.3, w) for i, w in enumerate(toks)], 0.25 + len(toks) / wps + 0.6


def timeline(project, marks, total):
    scenes = [dict(s) for s in project["scenes"]]
    n = len(scenes)
    prev = 0.0
    for i, sc in enumerate(scenes):
        t0 = 0.0
        if i > 0:
            t0 = find(marks, sc.get("anchor", ""), prev + 0.6) if sc.get("anchor") else None
            if t0 is None:
                t0 = sc.get("t0", total * i / n)
            t0 = max(t0, prev + 2.0)
        sc["_t0"], prev = round(t0, 2), t0
    for i, sc in enumerate(scenes):
        sc["_t1"] = scenes[i + 1]["_t0"] if i + 1 < n else round(total, 2)
        t0, dur = sc["_t0"], sc["_t1"] - sc["_t0"]
        sc["_vt"] = (find(marks, sc["at"], t0 - 0.05) if sc.get("at") else None) or t0 + 0.5
        key = LISTS.get(sc.get("shot"))
        if key:
            items = sc[key] = [({"text": x} if isinstance(x, str) else dict(x)) for x in sc[key]]
            for j, it in enumerate(items):
                tt = find(marks, it["at"], t0 - 0.05) if it.get("at") else None
                it["_t"] = tt if tt is not None else t0 + 0.45 + max(0.0, dur - 1.6) * 0.65 * j / max(1, len(items))
    return scenes


def captions(narration, marks, keywords):
    toks = [w for w in narration.split() if re.search(r"\w", w)]
    if len(toks) != len(marks):                       # TTS мог слить/разбить слова — масштабируем
        marks = [marks[min(len(marks) - 1, int(i * len(marks) / max(1, len(toks))))] for i in range(len(toks))]
    cues, i = [], 0
    while i < len(toks):
        j = i
        while j + 1 < len(toks) and (j - i + 1) < 4 and not toks[j].endswith((",", ".", "!", "?", "—", ":")):
            j += 1
        words = [w.strip(" ,.!?—:;«»") for w in toks[i:j + 1]]
        cues.append((marks[i][0], marks[j][0] + marks[j][1], words))
        i = j + 1
    kw = [k.lower() for k in keywords]
    return [(s, e, [(w, any(k in w.lower() for k in kw) or bool(re.search(r"\d", w))) for w in ws]) for s, e, ws in cues]


# --- кадр -------------------------------------------------------------------------

def _scene(cv, tl, sc, t, project):
    theme = sc.get("theme") or project.get("theme", "studio")
    th = themes.palette(theme)
    ctx = Ctx(t, sc, th, theme)
    mode = sc.get("cam", "push")
    k = ease(ctx.st / ctx.dur)
    fg = {"push": 1 + 0.045 * k, "pull": 1.045 - 0.045 * k, "none": 1.0}.get(mode, 1.0)
    plate = sc.get("plate")
    if plate and not os.path.isabs(plate):
        plate = os.path.join(tl["base"], plate)
    if plate and not os.path.exists(plate):
        plate = None
    cv.save()
    cv.zoom(1 + (fg - 1) * 0.5, 540, 1000)
    themes.backdrop(cv, theme, t, k, plate)
    cv.restore()
    cv.rect(0, 0, W, 560, fill=lin(0, 0, 0, 560, [(0, "#04081099"), (1, "#04081000")]))
    cv.save()
    cv.zoom(fg, 540, 1000)
    SHOTS[sc["shot"]](cv, ctx)
    cv.restore()
    return th


def _hud(cv, tl, th, t):
    project = tl["project"]
    cv.rect(0, 1660, W, H, fill=lin(0, 1660, 0, H, [(0, "#05070f00"), (1, "#05070fe6")]))
    cv.rrect(36, 40, 176, 92, 14, fill="#0b1220", alpha=0.8)
    cv.rrect(36, 40, 176, 92, 14, stroke="#e8f2ff", width=2.5)
    cv.text("VGEN", 106, 77, 30, fill="#fff", center=True)
    tag = project.get("tag", "ИНЖЕНЕРИЯ")
    tw = cv.text_w(tag, 24)
    cv.rrect(36, 104, 36 + tw + 40, 148, 12, fill="#0b1220", alpha=0.8)
    cv.rrect(36, 104, 36 + tw + 40, 148, 12, stroke=th["warm"], width=2.5)
    cv.text(tag, 36 + (tw + 40) / 2, 135, 24, fill="#ffe3d6", center=True)
    cur = None
    for (s, e, ws) in tl["cues"]:
        if s <= t + 0.05:
            cur = (s, e, ws)
    if cur and t <= cur[1] + 0.35:
        words = cur[2]
        size = 58
        sp = size * 0.3
        while sum(cv.text_w(w, size) for w, _ in words) + sp * (len(words) - 1) > 940 and size > 34:
            size -= 2
            sp = size * 0.3
        tot = sum(cv.text_w(w, size) for w, _ in words) + sp * (len(words) - 1)
        cv.rrect(540 - tot / 2 - 34, 1640 - size - 10, 540 + tot / 2 + 34, 1640 + 26, 22, fill="#050a14", alpha=0.74)
        x = 540 - tot / 2
        for w, hl in words:
            cv.text(w, x, 1640, size, fill=th["accent2"] if hl else "#fff")
            x += cv.text_w(w, size) + sp
    k = min(1.0, t / tl["total"])
    cv.line(40, 1862, 1040, 1862, "#ffffff", 5, alpha=0.18)
    cv.line(40, 1862, 40 + 1000 * k, 1862, th["accent2"], 5)
    cv.poly([(40 + 1000 * k - 9, 1850), (40 + 1000 * k + 9, 1850), (40 + 1000 * k, 1866)], fill=th["accent2"])


def render_frame(tl, t, finish=True):
    scenes = tl["scenes"]
    idx = 0
    for j, sc in enumerate(scenes):
        if t >= sc["_t0"]:
            idx = j
    cv = Canvas()
    th = None
    if idx > 0 and t - scenes[idx]["_t0"] < XFADE:
        _scene(cv, tl, scenes[idx - 1], t, tl["project"])
        a = ease((t - scenes[idx]["_t0"]) / XFADE)
        cv.c.saveLayerAlpha(None, int(255 * a))
        th = _scene(cv, tl, scenes[idx], t, tl["project"])
        cv.c.restore()
    else:
        th = _scene(cv, tl, scenes[idx], t, tl["project"])
    _hud(cv, tl, th, t)
    img = cv.to_pil()
    return postfx.finish(img, grain_amt=3, vig=0.22) if (finish and POST) else img


# --- проверка проекта --------------------------------------------------------------

def validate(project, marks=None):
    """-> (errors, warnings). Ошибки блокируют сборку."""
    errs, warns = [], []
    narr = project.get("script", {}).get("narration", "")
    nw = " ".join(narr.lower().split())
    facts_txt = json.dumps(project.get("facts", []), ensure_ascii=False).lower() + " " + nw
    for i, sc in enumerate(project.get("scenes", [])):
        sid = sc.get("id", f"#{i}")
        if sc.get("shot") not in SHOTS:
            errs.append(f"{sid}: неизвестный shot {sc.get('shot')!r}; есть: {', '.join(SHOTS)}")
            continue
        if sc.get("theme") and sc["theme"] not in themes.THEMES:
            errs.append(f"{sid}: неизвестная theme {sc['theme']!r}; есть: {', '.join(themes.THEMES)}")
        if i > 0 and sc.get("anchor") and sc["anchor"].lower() not in nw:
            errs.append(f"{sid}: anchor {sc['anchor']!r} не найден в narration")
        need = {"hook": ["title"], "stat": ["title", "value"], "compare": ["title", "items"], "steps": ["title", "steps"],
                "flow": ["title", "nodes"], "chart": ["title", "bars"], "callout": ["title", "callouts"],
                "outro": ["title", "bullets"]}[sc["shot"]]
        for f in need:
            if f not in sc:
                errs.append(f"{sid}: у shot {sc['shot']} нет поля {f!r}")
        icons = [sc.get("icon")] + [x.get("icon") for k in LISTS.values() for x in sc.get(k, []) if isinstance(x, dict)]
        for ic in icons:
            if ic and ic not in ICONS:
                errs.append(f"{sid}: нет иконки {ic!r}; есть: {', '.join(ICONS)}")
        for key in LISTS.values():
            for it in sc.get(key, []):
                if isinstance(it, dict) and it.get("at") and it["at"].lower() not in nw:
                    errs.append(f"{sid}: at {it['at']!r} не найден в narration")
        if sc.get("at") and sc["at"].lower() not in nw:
            errs.append(f"{sid}: at {sc['at']!r} не найден в narration")
        if sc["shot"] in ("hook", "outro") and len(sc.get("title", "")) > 28:
            warns.append(f"{sid}: заголовок длиннее 28 символов — будет мелким")
        texts = json.dumps({k: v for k, v in sc.items() if k not in ("id", "shot", "anchor", "at", "theme", "cam", "plate", "icon")},
                           ensure_ascii=False)
        for num in set(re.findall(r"\d+(?:[ \u00a0]\d{3})*(?:[.,]\d+)?", texts)):
            n = num.strip().replace(" ", "").replace("\u00a0", "")
            if n and n not in ("0", "1") and n.replace(",", ".") not in facts_txt.replace(" ", "").replace(",", "."):
                warns.append(f"{sid}: число {num.strip()} не найдено в facts/narration — подтвердите источником")
    return errs, warns


# --- сборка ------------------------------------------------------------------------

_TL = None


def _init(tl):
    global _TL
    _TL = tl


def _work(i):
    p = os.path.join(_TL["frames"], "f%05d.jpg" % i)
    render_frame(_TL, i / FPS).convert("RGB").save(p, quality=95)
    return i


def make_tl(project, marks, total, base, frames=None):
    return {"project": project, "scenes": timeline(project, marks, total), "total": total, "base": base,
            "cues": captions(project["script"]["narration"], marks, project.get("keywords", [])), "frames": frames}


def build(project, vinfo, out_dir, base=None):
    from vgen import sfx
    errs, warns = validate(project)
    for w in warns:
        print("  ⚠", w)
    if errs:
        raise SystemExit("studio: ошибки проекта:\n  " + "\n  ".join(errs))
    base = base or os.path.join("episodes", project["slug"])
    frames = os.path.join(out_dir, "frames")
    os.makedirs(frames, exist_ok=True)
    total = vinfo["total"]
    tl = make_tl(project, vinfo["marks"], total, base, frames)
    n = int(total * FPS) + 1
    workers = min(os.cpu_count() or 1, int(os.environ.get("VGEN_WORKERS", "8")))
    if workers > 1:
        import multiprocessing as mp
        with mp.Pool(workers, initializer=_init, initargs=(tl,)) as pool:
            for k, _ in enumerate(pool.imap_unordered(_work, range(n), chunksize=4)):
                if k % 150 == 0:
                    print("frame", k, "/", n)
    else:
        _init(tl)
        for i in range(n):
            _work(i)
    silent = os.path.join(out_dir, "assets", "video_silent.mp4")
    os.makedirs(os.path.dirname(silent), exist_ok=True)
    subprocess.run([sfx.FFMPEG, "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(frames, "f%05d.jpg"),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", silent], check=True)
    events = [(0.02, "boom", 0.5)]
    for sc in tl["scenes"][1:]:
        events.append((sc["_t0"], "whoosh", 0.28))
    for sc in tl["scenes"]:
        for key in LISTS.values():
            for it in sc.get(key, []):
                events.append((it["_t"], "pop", 0.22))
        if sc["shot"] == "stat":
            events.append((sc["_vt"], "pop", 0.4))
    events.append((total - 0.9, "chime", 0.4))
    fx = sfx.build_track(total, sorted(events), os.path.join(out_dir, "assets", "sfx.wav"))
    final = os.path.join(out_dir, "final.mp4")
    sfx.mix(silent, vinfo["wav"], fx, final, video_sfx_gain=0.75)
    return final
