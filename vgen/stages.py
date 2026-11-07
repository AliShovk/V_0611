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


HUNDREDS = {"сто": 100, "ста": 100, "двухсот": 200, "трёхсот": 300, "трехсот": 300,
            "четырёхсот": 400, "четырехсот": 400, "пятисот": 500, "шестисот": 600,
            "семисот": 700, "восьмисот": 800, "девятисот": 900, "двести": 200, "триста": 300, "четыреста": 400,
            "пятьсот": 500, "шестьсот": 600, "семьсот": 700, "восемьсот": 800,
            "девятьсот": 900}
TENS = {"двадцать": 20, "двадцати": 20, "тридцати": 30, "сорока": 40,
        "пятидесяти": 50, "шестидесяти": 60, "семидесяти": 70, "восьмидесяти": 80,
        "девяноста": 90, "тридцать": 30, "сорок": 40, "пятьдесят": 50,
        "шестьдесят": 60, "семьдесят": 70, "восемьдесят": 80, "девяносто": 90}
THOUS = {"тысяча": 1000, "тысячи": 1000, "тысячу": 1000, "тысяч": 1000, "тысяче": 1000}
ORD = {"первого": 1, "второго": 2, "третьего": 3, "четвёртого": 4, "четвертого": 4,
       "пятого": 5, "шестого": 6, "седьмого": 7, "восьмого": 8, "девятого": 9,
       "десятого": 10, "первый": 1, "второй": 2, "третий": 3, "пятый": 5}
PHRASES = {"полтора": "1.5", "полторы": "1.5", "полтораста": "150"}
TEENS = {"одиннадцать": 11, "двенадцать": 12, "тринадцать": 13, "четырнадцать": 14,
         "пятнадцать": 15, "шестнадцать": 16, "семнадцать": 17, "восемнадцать": 18,
         "девятнадцать": 19}
UNITS = {"ноль": 0, "двух": 2, "трёх": 3, "трех": 3, "четырёх": 4, "четырех": 4,
         "пяти": 5, "шести": 6, "семи": 7, "восьми": 8, "девяти": 9, "десяти": 10, "один": 1, "одна": 1, "два": 2, "две": 2, "три": 3, "четыре": 4,
         "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9, "десять": 10}


def numbers_in(text):
    """Числительные: цифры и составные («восемьсот двадцать восемь» -> 828)."""
    found = {norm_num(m.group(0)) for m in NUM.finditer(text)}
    low = text.lower()
    for w, v in PHRASES.items():
        if w in re.findall(r"[а-яё]+", low):
            found.add(v)
    words = re.findall(r"[А-Яа-яЁё]+|[^А-Яа-яЁё]+", text.lower())
    cur = 0
    active = False
    for w in words:
        if not w[0].isalpha():
            # дефис и запятая разрывают числительное: «шести-восьми» — это 6 и 8
            if ("-" in w or "–" in w or "," in w) and active:
                found.add(str(cur))
                cur, active = 0, False
            continue
        val = None
        if w in HUNDREDS:
            val = HUNDREDS[w]
        elif w in TENS:
            val = TENS[w]
        elif w in TEENS:
            val = TEENS[w]
        elif w in UNITS:
            val = UNITS[w]
        elif w in ORD:
            val = ORD[w]
        elif w in THOUS:
            # «тысяча девятьсот тридцать пятого» = 1000 + 900 + 30 + 5
            cur = (cur if cur else 1) * 1000
            active = True
            continue
        if val is None:
            if active:
                found.add(str(cur))
                cur, active = 0, False
            continue
        # сотни начинают новый разряд, десятки/единицы добавляются
        if w in HUNDREDS:
            if cur >= 1000:
                cur += val
            elif cur >= 100 or not active:
                cur = val
            else:
                cur = val
        elif w in HUNDREDS:
            found.add(str(cur))
            cur = val
        else:
            cur += val
        active = True
    if active:
        found.add(str(cur))
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
