# -*- coding: utf-8 -*-
"""本地判题：编译选手代码，用自备测试数据打分（CSP 用）。

用法：
  python judge.py --submissions ./answers --data ./data --problems problems.json --out result.json

目录约定：
  <submissions>/<考号>/<slug>/<slug>.cpp
  <data>/<pid>/1.in, 1.ans, 2.in, ...

problems.json：
  {"problems":[{"slug":"travel","pid":"P17827","points":5}, ...],
   "time_limit":1.5}
"""
import argparse
import sys
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor


def norm(s):
    lines = [ln.rstrip() for ln in s.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def compile_one(gxx, src, exe, timeout=60):
    msg = ""
    env = dict(os.environ)
    tmp = os.path.join(os.path.dirname(exe), "tmp")
    os.makedirs(tmp, exist_ok=True)
    env["TMP"] = env["TEMP"] = env["TMPDIR"] = tmp
    for std in ("c++14", "c++17"):
        try:
            p = subprocess.run([gxx, f"-std={std}", "-O2", "-pipe", "-o", exe, src],
                               capture_output=True, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return False, "编译超时"
        if p.returncode == 0:
            return True, ""
        msg = (p.stdout + p.stderr).decode("utf-8", "replace")
    return False, msg


def run_one(task, cfg):
    sid, slug, pid, points = task
    row = {"id": sid, "slug": slug, "score": 0, "status": "ok", "tests": [], "msg": ""}
    d = os.path.join(cfg["submissions"], sid, slug)
    if not os.path.isdir(d):
        row["status"] = "缺交"
        return row
    files = [f for f in os.listdir(d) if f.lower().endswith((".cpp", ".c"))]
    if not files:
        row["status"] = "空目录"
        return row

    work = os.path.join(cfg["work"], f"{sid}_{slug}")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work, exist_ok=True)
    exe = os.path.join(work, "prog.exe")
    ok, msg = compile_one(cfg["gxx"], os.path.join(d, files[0]), exe)
    if not ok:
        row["status"] = "CE"
        row["msg"] = msg[:400]
        shutil.rmtree(work, ignore_errors=True)
        return row

    tdir = os.path.join(cfg["data"], pid)
    total = len([f for f in os.listdir(tdir) if f.endswith(".in")])
    passed = 0
    for i in range(1, total + 1):
        inp = open(os.path.join(tdir, f"{i}.in"), "rb").read()
        exp = open(os.path.join(tdir, f"{i}.ans"), "rb").read().decode("utf-8", "replace")
        for f in os.listdir(work):
            if f.endswith((".in", ".out")):
                os.remove(os.path.join(work, f))
        open(os.path.join(work, f"{slug}.in"), "wb").write(inp)
        try:
            p = subprocess.run([exe], cwd=work, capture_output=True, timeout=cfg["time_limit"])
            rc, to = p.returncode, False
        except subprocess.TimeoutExpired:
            rc, to = None, True
        of = os.path.join(work, f"{slug}.out")
        got = open(of, "rb").read().decode("utf-8", "replace") if os.path.exists(of) else ""
        if to:
            v = "TLE"
        elif rc != 0:
            v = "RE"
        elif norm(got) == norm(exp):
            v = "AC"
            passed += 1
        else:
            v = "WA"
        row["tests"].append(v)
    row["score"] = passed * points
    row["total"] = total
    shutil.rmtree(work, ignore_errors=True)
    return row


def main():
    ap = argparse.ArgumentParser(description="本地判题（CSP 风格）")
    ap.add_argument("--submissions", required=True, help="代码根目录 <考号>/<slug>/<slug>.cpp")
    ap.add_argument("--data", required=True, help="测试数据目录 <pid>/<i>.in|.ans")
    ap.add_argument("--problems", required=True, help="题目配置 JSON")
    ap.add_argument("--out", default="result.json")
    ap.add_argument("--gxx", default="g++", help="g++ 路径")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--ids", nargs="*", default=None, help="只跑这些考号")
    ap.add_argument("--passcode", default="", help="访问口令")
    args = ap.parse_args()
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))
    import guard
    guard.require(args.passcode)


    conf = json.load(open(args.problems, encoding="utf-8"))
    probs = conf["problems"]
    cfg = {
        "submissions": args.submissions,
        "data": args.data,
        "gxx": args.gxx,
        "time_limit": conf.get("time_limit", 1.5),
        "work": os.path.join(os.path.dirname(os.path.abspath(args.out)), "_work"),
    }
    os.makedirs(cfg["work"], exist_ok=True)

    ids = args.ids or sorted(d for d in os.listdir(args.submissions)
                             if os.path.isdir(os.path.join(args.submissions, d)))
    tasks = [(sid, p["slug"], p["pid"], p.get("points", 10)) for sid in ids for p in probs]

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(lambda t: run_one(t, cfg), tasks))

    json.dump(results, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    by = {(r["id"], r["slug"]): r for r in results}
    print(f"选手 {len(ids)} 人，题目 {len(probs)} 道")
    for sid in ids:
        scores = [by[(sid, p['slug'])]["score"] for p in probs]
        print(f"  {sid}: " + " ".join(f"{p['slug']}={by[(sid, p['slug'])]['score']}" for p in probs)
              + f"  合计 {sum(scores)}")
    print("saved", args.out)


if __name__ == "__main__":
    main()
