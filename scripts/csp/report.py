# -*- coding: utf-8 -*-
"""一条命令出 CSP 报告：判题 → 体检 → 能力评估 → 渲染。

  python report.py --ids HL-J00889 --archive ./answers --data ./data \
      --problems csp2026.json --out ./out --passcode pointer

默认 auto：全自动生成文字。加 --mode spec 则读取 <out>/specs/<id>.json（agent 精修版）。
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "common"))

import guard  # noqa: E402
import judge  # noqa: E402
import scan as scanner  # noqa: E402
import profile  # noqa: E402
import autospec  # noqa: E402
import render  # noqa: E402


def run_judge(ids, args, probs):
    cfg = {
        "submissions": args.archive,
        "data": args.data,
        "gxx": args.gxx,
        "time_limit": args.time_limit,
        "work": os.path.join(args.out, "_work"),
    }
    os.makedirs(cfg["work"], exist_ok=True)
    tasks = [(sid, p["slug"], p.get("pid", p["slug"]), p.get("points", 10)) for sid in ids for p in probs]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        rows = list(ex.map(lambda t: judge.run_one(t, cfg), tasks))
    by = {}
    for r in rows:
        by.setdefault(r["id"], {})[r["slug"]] = r
    return by


def load_offline(ids, args, probs):
    """不判题时，用上次的 result.json。"""
    path = os.path.join(args.out, "judge_result.json")
    if not os.path.exists(path):
        raise SystemExit("没有测试数据时必须提供 --data，或先用 judge.py 生成 judge_result.json")
    rows = json.load(open(path, encoding="utf-8"))
    by = {}
    for r in rows:
        if r["id"] in ids:
            by.setdefault(r["id"], {})[r["slug"]] = r
    return by


def main():
    ap = argparse.ArgumentParser(description="CSP 报告一键生成")
    ap.add_argument("--ids", nargs="+", required=True, help="准考证号，可多个")
    ap.add_argument("--archive", required=True, help="代码目录 <考号>/<slug>/<slug>.cpp")
    ap.add_argument("--data", default="", help="测试数据目录 <pid>/<i>.in|.ans（不给则用旧 judge_result.json）")
    ap.add_argument("--problems", required=True, help="题目配置 JSON（含 title/tags/summary/advice）")
    ap.add_argument("--scores", default="", help="可选：成绩表 xlsx（含 准考证号/姓名/分题列）")
    ap.add_argument("--names", default="", help="可选：{考号: 姓名} JSON")
    ap.add_argument("--out", default="out")
    ap.add_argument("--mode", choices=["auto", "spec"], default="spec",
                    help="spec=精修版（默认，读 <out>/specs/<id>.json）；auto=规则快速版")
    ap.add_argument("--logo", default="", help="封面 logo；默认 assets/logo.jpg")
    ap.add_argument("--gxx", default="g++")
    ap.add_argument("--time-limit", type=float, default=1.5)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--passcode", default="")
    args = ap.parse_args()
    guard.require(args.passcode)

    os.makedirs(args.out, exist_ok=True)
    conf = json.load(open(args.problems, encoding="utf-8"))
    probs = conf["problems"]
    slugs = [p["slug"] for p in probs]

    official = {}
    if args.names and os.path.exists(args.names):
        names = json.load(open(args.names, encoding="utf-8"))
        official = {k: {"name": v, "scores": {}, "total": None} for k, v in names.items()}
    if args.scores and os.path.exists(args.scores):
        official.update(load_scores(args.scores, slugs))

    print(f"处理 {len(args.ids)} 人，{len(probs)} 道题")
    if args.mode == "spec" and len(args.ids) > 8:
        print("提示：人数较多，可加 --mode auto 先用规则版快速出稿，再挑重点精修。")
    by = run_judge(args.ids, args, probs) if args.data else load_offline(args.ids, args, probs)
    json.dump([r for d in by.values() for r in d.values()],
              open(os.path.join(args.out, "judge_result.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    scans = scanner.scan_all(args.archive, args.ids, slugs)
    logo = args.logo or os.path.join(os.path.dirname(os.path.dirname(HERE)), "assets", "logo.png")
    render.LOGO = logo if os.path.exists(logo) else ""
    render.OUT = args.out

    for sid in args.ids:
        res = by.get(sid, {})
        info = official.get(sid, {})
        name = info.get("name") or sid
        prof = profile.assess(sum(r.get("score", 0) for r in res.values()), res, scans[sid], probs)
        spec = autospec.build_spec(sid, name, res, scans[sid], probs, prof, official=info or None)
        spec["logo"] = render.LOGO

        if args.mode == "spec":
            p = os.path.join(args.out, "specs", f"{sid}.json")
            if os.path.exists(p):
                spec = json.load(open(p, encoding="utf-8"))
                print(f"  {sid}: 使用 spec 版 {p}")
            else:
                print(f"  {sid}: 没有找到 {p}，回退 auto（批量时可显式 --mode auto）")

        render.ARCHIVE = args.archive
        print("  " + render.build(spec))

    if args.mode == "auto":
        auto_hint = ("本次为 auto 模式（规则生成）。需要逐题细分析时，"
                     "准备 <out>/specs/<考号>.json 后改用 --mode spec。")
    else:
        auto_hint = ("本次为 spec 模式：找到的 spec 直接使用，没找到的回退 auto。"
                     "如需批量快速出稿，加 --mode auto。")
    print(auto_hint)


def load_scores(path, slugs):
    from openpyxl import load_workbook
    wb = load_workbook(path)
    ws = wb[wb.sheetnames[0]]
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        sid = str(row[0]).strip()
        out[sid] = {"name": row[1] if len(row) > 1 else sid,
                    "scores": {s: row[2 + i] for i, s in enumerate(slugs) if 2 + i < len(row)},
                    "total": row[2 + len(slugs)] if len(row) > 2 + len(slugs) else None}
    return out


if __name__ == "__main__":
    main()
