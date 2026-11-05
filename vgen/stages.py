"""Stage 1+8 — research.md, sources.md и проверка чисел.

Research не «выдумывает устройство»: он берёт только те факты, что лежат в
project.json (поле facts), у каждого факта обязателен source id. Fact check
сверяет числа из сценария с этими фактами и падает, если числа не совпали.
"""
import json
import os
import re

NUM = re.compile(r"\d+[.,]?\d*")


def norm_num(s):
    return s.replace(",", ".").replace(" ", "")


PHRASES = {
    "двадцать шесть": 26, "двадцать пять": 25, "двадцать семь": 27, "двадцать восемь": 28,
    "тридцать": 30, "сорок": 40, "пятьдесят": 50, "шестьдесят": 60,
    "семьдесят": 70, "восемьдесят": 80, "девяносто": 90,
    "сто": 100, "двести": 200, "триста": 300, "тысяча": 1000,
}
UNITS = {
    "ноль": 0, "один": 1, "одна": 1, "два": 2, "две": 2, "три": 3, "четыре": 4,
    "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9, "десять": 10,
}


def numbers_in(text):
    """Числительные: цифры + составные числительные словами."""
    low = text.lower()
    found = {norm_num(m.group(0)) for m in NUM.finditer(text)}
    for phrase, val in sorted(PHRASES.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"\b{phrase}", low):
            found.add(str(val))
            low = re.sub(rf"\b{phrase}", " ", low)
    for w, v in UNITS.items():
        if re.search(rf"\b{w}\b", low):
            found.add(str(v))
    return found


def write_research(project, out_dir):
    facts = project["facts"]
    lines = [f"# Research: {project['title']}", "",
             f"Статус: {project.get('status', 'n/a')}", ""]
    for f in facts:
        lines.append(f"- **{f['id']}** — {f['claim']}")
        if f.get("value"):
            lines.append(f"  - значение: `{f['value']}`")
        lines.append(f"  - источник: [{f['source']}]")
    lines += ["", "## Чего в ролике быть не должно", ""]
    for x in project.get("avoid", []):
        lines.append(f"- {x}")
    path = os.path.join(out_dir, "research.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path


def write_sources(project, out_dir):
    lines = [f"# Источники: {project['title']}", ""]
    for s in project["sources"]:
        lines.append(f"## [{s['id']}] {s['org']}")
        lines.append(f"- {s['title']}")
        lines.append(f"- {s['url']}")
        lines.append(f"- дата проверки: {s.get('checked', project.get('today', 'n/a'))}")
        if s.get("note"):
            lines.append(f"- примечание: {s['note']}")
        lines.append("")
    path = os.path.join(out_dir, "sources.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path


def engineering(project, out_dir):
    """Стадия 2: принцип, путь нагрузки/воды, обязательные детали."""
    e = project["engineering"]
    lines = [f"# Engineering: {project['title']}", "",
             f"**Принцип:** {e['principle']}", "",
             "## Передача нагрузки / движение среды", ""]
    for step in e["chain"]:
        lines.append(f"1. {step}")
    lines += ["", "## Обязательные детали (3–5)", ""]
    for d in e["details"]:
        lines.append(f"- {d}")
    if e.get("must_not_show"):
        lines += ["", "## Запрещено показывать", ""]
        for x in e["must_not_show"]:
            lines.append(f"- {x}")
    path = os.path.join(out_dir, "engineering.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path


def write_script(project, out_dir):
    s = project["script"]
    lines = [f"# Script: {project['title']}", "",
             f"**Хук:** {s['hook']}", "", "## Дикторский текст", ""]
    for i, line in enumerate(s["lines"], 1):
        lines.append(f"{i}. {line}")
    lines += ["", f"_Слов: {len(s['narration'].split())}. Цель: 45–60 с._"]
    path = os.path.join(out_dir, "script.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path


def check(project, out_dir):
    """Fact check: числа сценария должны быть в facts."""
    allowed = set()
    for f in project["facts"]:
        allowed |= numbers_in(f["claim"])
        if f.get("value"):
            allowed |= numbers_in(str(f["value"]))
    text = project["script"]["narration"] + " " + project["script"]["hook"]
    used = numbers_in(text)
    missing = sorted(used - allowed)
    report = {
        "checked_numbers": sorted(used),
        "known_numbers": sorted(allowed),
        "unsupported": missing,
        "passed": not missing,
    }
    path = os.path.join(out_dir, "factcheck.json")
    json.dump(report, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return report
