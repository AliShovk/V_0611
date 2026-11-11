"""Оркестратор: research → engineering → script → factcheck → voice → storyboard → animation."""
import argparse
import json
import os
import shutil
import sys

from vgen import stages, voice as voice_mod, storyboard as sb_mod, animation, outro as outro_mod


def load(project_path):
    with open(project_path, encoding="utf-8") as f:
        return json.load(f)


def run(project_path, out_root="out", skip_voice=False):
    project = load(project_path)
    name = project["slug"]
    out = os.path.join(out_root, name)
    os.makedirs(out, exist_ok=True)
    os.makedirs(os.path.join(out, "assets"), exist_ok=True)

    print(f"[1/8] research: {project['title']}")
    research = stages.write_research(project, out)
    sources = stages.write_sources(project, out)

    print("[2/8] engineering")
    eng = stages.engineering(project, out)

    print("[3/8] script")
    scr = stages.write_script(project, out)

    print("[4/8] fact check (gate)")
    check = stages.check(project, out)
    if not check["passed"]:
        print("  ✗ неподтверждённые числа:", ", ".join(check["unsupported"]))
        print("  выпуск возвращён на доработку, рендер не запускаю")
        return {"ok": False, "stage": "factcheck", "unsupported": check["unsupported"], "out": out}
    print("  ✓ все числа подтверждены источниками")

    print("[5/8] voice + subtitles")
    vinfo = voice_mod.build(project, out)
    print(f"  {vinfo['total']:.2f} с, {len(vinfo['marks'])} слов")

    print("[6/8] storyboard")
    board, board_path = sb_mod.build(project, vinfo, out)

    print("[7/8] animation + encode")
    built = animation.build(project, vinfo, board, out)
    final = built["final"] if isinstance(built, dict) else built

    if project.get("outro", True):
        print("[7b/8] концовка GPTunnel")
        final = outro_mod.attach(final, project.get("outro_file"), out)

    print("[8/8] готово")
    total = vinfo["total"]
    if final.endswith("final_outro.mp4"):
        total += outro_mod.probe_duration(project.get("outro_file") or outro_mod.DEFAULT)
    return {"ok": True, "out": out, "final": final, "duration": round(total, 2),
            "scenes": len(board["scenes"]), "artifacts": sorted(os.listdir(out))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Инженерный объясняющий генератор")
    ap.add_argument("project", help="путь к project.json")
    ap.add_argument("--out", default="out")
    ap.add_argument("--factcheck-only", action="store_true")
    args = ap.parse_args(argv)
    project = load(args.project)
    out = os.path.join(args.out, project["slug"])
    os.makedirs(out, exist_ok=True)
    if args.factcheck_only:
        r = stages.check(project, out)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["passed"] else 1
    res = run(args.project, args.out)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
