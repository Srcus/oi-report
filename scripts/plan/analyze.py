# -*- coding: utf-8 -*-
"""按学生档案里的知识点掌握度做差距分析。

用法：
  python analyze.py --profile 学生.json [--goal two|three|four] [--out analysis.json]

学生档案（JSON）：
  {
    "name": "张三", "grade": "初二", "weekly_hours": 4,
    "awards": [{"name": "CSP-J 2026 第一轮", "level": "二等"}],
    "mastery": {"L1-01": 3, "L1-05": 2, ...}
  }

掌握度：0 不会 / 1 听过 / 2 会套模板 / 3 能独立写 / 4 能变形。
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
KNOW = json.load(open(os.path.join(HERE, "knowledge.json"), encoding="utf-8"))
ITEMS = {x["id"]: x for x in KNOW["items"]}
TARGET = KNOW.get("target_level", 3)
GOALS = {"two": ["problem1", "problem2"],
         "three": ["problem1", "problem2", "problem3"],
         "four": ["problem1", "problem2", "problem3", "problem4"]}


def analyze(profile, goal="two"):
    mastery = profile.get("mastery", {})
    hours = float(profile.get("weekly_hours") or 4)
    keys = GOALS.get(goal, GOALS["two"])
    required = []
    for k in keys:
        for i in KNOW["exam"][k]["need"]:
            if i not in required:
                required.append(i)

    gaps = []
    for i in required:
        item = ITEMS[i]
        cur = int(mastery.get(i, 0) or 0)
        need = max(0, TARGET - cur)
        if need:
            gaps.append({"id": i, "module": item["module"], "name": item["name"],
                         "current": cur, "need": need, "hours": item["hours"] * need / 2.0})

    total_hours = sum(g["hours"] for g in gaps)
    weeks = round(total_hours / hours, 1) if hours else 0

    problems = []
    for key, p in KNOW["exam"].items():
        vals = [int(mastery.get(i, 0) or 0) for i in p["need"]]
        ratio = (sum(min(v, TARGET) for v in vals) / (len(vals) * TARGET)) if vals else 0
        problems.append({"key": key, "name": p["name"], "ready": round(ratio * 100),
                         "points": round(p["points"] * ratio)})

    order = {"L1": 0, "L2": 1, "L3": 2, "L4": 3}
    gaps.sort(key=lambda g: (order.get(g["module"], 9), g["current"], g["hours"]))

    return {
        "name": profile.get("name", ""), "grade": profile.get("grade", ""),
        "weekly_hours": hours, "goal": goal,
        "gaps": gaps, "total_hours": round(total_hours, 1), "weeks_needed": weeks,
        "problems": problems,
        "goal_points": sum(p["points"] for p in problems[:len(keys)]),
        "goal_full": 100 * len(keys),
        "awards": profile.get("awards", []), "notes": profile.get("notes", ""),
    }


def summary_text(a):
    lines = [f"{a['name']}（{a['grade']}）知识点盘点", ""]
    lines.append(f"目标：前{'两' if a['goal']=='two' else '三' if a['goal']=='three' else '四'}题。"
                 f"按每周 {a['weekly_hours']:g} 小时算，补齐到能独立写约需 {a['weeks_needed']:g} 周"
                 f"（{a['total_hours']:g} 课时）。")
    lines.append("")
    lines.append("分题预估：")
    for p in a["problems"]:
        lines.append(f"  {p['name']}：准备度 {p['ready']}%，约 {p['points']} 分")
    lines.append(f"  目标合计约 {a['goal_points']} / {a['goal_full']}")
    lines.append("")
    lines.append("优先补的知识点：")
    for g in a["gaps"][:10]:
        lines.append(f"  {g['id']} {g['name']}（当前 {g['current']}/4，约 {g['hours']:.0f} 课时）")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="知识点差距分析")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--goal", choices=["two", "three", "four"], default="two")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    profile = json.load(open(args.profile, encoding="utf-8"))
    a = analyze(profile, args.goal)
    print(summary_text(a))
    if args.out:
        json.dump(a, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\nsaved", args.out)


if __name__ == "__main__":
    main()
