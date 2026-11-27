# -*- coding: utf-8 -*-
"""按学生档案里的知识点掌握度做差距分析（CSP-J 第二轮范围，不含时间安排）。

用法：
  python analyze.py --profile 学生.json [--goal two|three|four] [--out analysis.json]

学生档案（JSON）：
  {
    "name": "张三", "grade": "初二",
    "awards": [{"name": "CSP-J 2026 第一轮", "level": "二等"}],
    "mastery": {"L1-01": 3, "L1-05": 2, ...},
    "notes": "做题慢，遇到长题面容易跳过"
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
STAGES = KNOW.get("stages", {})
GOALS = {"two": ["problem1", "problem2"],
         "three": ["problem1", "problem2", "problem3"],
         "four": ["problem1", "problem2", "problem3", "problem4"]}


def analyze(profile, goal="two"):
    mastery = profile.get("mastery", {})
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
        if cur < TARGET:
            gaps.append({"id": i, "module": item["module"], "stage": item["stage"],
                         "name": item["name"], "current": cur})
    gaps.sort(key=lambda g: (g["stage"], g["current"], g["id"]))

    problems = []
    for key, p in KNOW["exam"].items():
        vals = [int(mastery.get(i, 0) or 0) for i in p["need"]]
        ratio = (sum(min(v, TARGET) for v in vals) / (len(vals) * TARGET)) if vals else 0
        problems.append({"key": key, "name": p["name"], "ready": round(ratio * 100),
                         "points": round(p["points"] * ratio)})

    stages = []
    for s in sorted(STAGES):
        items = [x["id"] for x in KNOW["items"] if str(x["stage"]) == s]
        vals = [min(int(mastery.get(i, 0) or 0), TARGET) for i in items]
        ratio = (sum(vals) / (len(vals) * TARGET)) if vals else 0
        stages.append({"stage": int(s), "name": STAGES[s]["name"], "goal": STAGES[s]["goal"],
                       "ready": round(ratio * 100),
                       "missing": [i for i in items if int(mastery.get(i, 0) or 0) < TARGET]})

    return {
        "name": profile.get("name", ""), "grade": profile.get("grade", ""),
        "goal": goal, "gaps": gaps, "problems": problems, "stages": stages,
        "goal_points": sum(p["points"] for p in problems[:len(keys)]),
        "goal_full": 100 * len(keys),
        "awards": profile.get("awards", []), "notes": profile.get("notes", ""),
    }


def summary_text(a):
    lines = [f"{a['name']}（{a['grade']}）知识点盘点", ""]
    lines.append("分题准备度：")
    for p in a["problems"]:
        lines.append(f"  {p['name']}：{p['ready']}%，约 {p['points']} 分")
    lines.append(f"  目标合计约 {a['goal_points']} / {a['goal_full']}")
    lines.append("")
    lines.append("四个阶段：")
    for s in a["stages"]:
        lines.append(f"  {s['name']}：{s['ready']}%　缺 {len(s['missing'])} 个点")
    lines.append("")
    lines.append("当前该补的知识点（按阶段顺序）：")
    for g in a["gaps"][:10]:
        lines.append(f"  阶段{g['stage']}　{g['id']} {g['name']}（当前 {g['current']}/4）")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="知识点差距分析（CSP-J）")
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
