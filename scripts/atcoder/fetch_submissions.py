# -*- coding: utf-8 -*-
"""拉取 AtCoder 某场比赛里指定选手的全部提交与源码。

数据来源：
  - 提交记录：AtCoder Problems 公开 API（kenkoooo.com）
  - 源码：AtCoder 提交详情页（公开可访问）

用法：
  python fetch_submissions.py --contest abc484 --users alice bob --out ./cache

产物：
  <out>/<contest>/<user>/attempts/<pid>_<序号>_<结果>.cpp
  <out>/<contest>/<user>/index.json    每题尝试数、最终结果、得分、用时
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
RESOURCES = "https://kenkoooo.com/atcoder/resources/contests.json"
SUBMISSIONS = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user={user}&from_second={start}"
API_FROM = "https://kenkoooo.com/atcoder/atcoder-api/v3/from/{epoch}"
SUBMISSION_PAGE = "https://atcoder.jp/contests/{contest}/submissions/{sid}"


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    return urllib.request.urlopen(req, timeout=timeout).read()


def get_json(url, timeout=30):
    return json.loads(get(url, timeout))


def contest_start(contest):
    for x in get_json(RESOURCES):
        if x["id"] == contest:
            return x["start_epoch_second"], x["title"]
    raise SystemExit(f"找不到比赛 {contest}（示例：abc484）")


def fetch_code(contest, sub_id, retries=4):
    url = SUBMISSION_PAGE.format(contest=contest, sid=sub_id)
    for attempt in range(retries):
        try:
            h = get(url).decode("utf-8", "ignore")
            m = re.search(r'<pre[^>]*id="submission-code"[^>]*>(.*?)</pre>', h, re.S)
            return html.unescape(m.group(1)) if m else ""
        except Exception as e:  # 限流或临时错误
            if attempt == retries - 1:
                print(f"  ! 拉取失败 {sub_id}: {type(e).__name__}", file=sys.stderr)
                return ""
            time.sleep(3 * (attempt + 1))
    return ""


def fetch_user(contest, user, start, out):
    subs = [x for x in get_json(SUBMISSIONS.format(user=user, start=start - 1800))
            if x.get("contest_id") == contest]
    subs.sort(key=lambda x: x["epoch_second"])
    if not subs:
        print(f"{user}: 这场比赛没有提交")
        return None

    root = os.path.join(out, contest, user)
    adir = os.path.join(root, "attempts")
    os.makedirs(adir, exist_ok=True)

    per_problem = {}
    for k, s in enumerate(subs, 1):
        pid = s["problem_id"]
        name = f'{pid}_{k:02d}_{s["result"]}.cpp'
        path = os.path.join(adir, name)
        if not os.path.exists(path):
            code = fetch_code(contest, s["id"])
            open(path, "w", encoding="utf-8").write(code)
            time.sleep(1.2)
        per_problem.setdefault(pid, []).append({
            "file": f"attempts/{name}",
            "result": s["result"],
            "point": s["point"],
            "ms": s["execution_time"],
            "language": s["language"],
            "epoch": s["epoch_second"],
        })

    index = {"user": user, "contest": contest, "problems": {}}
    total = 0.0
    for pid, lst in sorted(per_problem.items()):
        lst.sort(key=lambda x: x["epoch"])
        best = max(x["point"] for x in lst)
        total += best
        index["problems"][pid] = {
            "attempts": len(lst),
            "verdicts": [x["result"] for x in lst],
            "final": lst[-1]["result"],
            "score": best,
            "ms": lst[-1]["ms"],
            "language": lst[-1]["language"],
            "files": [x["file"] for x in lst],
        }
    index["score"] = total
    json.dump(index, open(os.path.join(root, "index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"{user}: {len(subs)} 次提交，得分 {total:g}")
    for pid, d in index["problems"].items():
        print(f"  {pid}  {d['attempts']} 次  {'/'.join(d['verdicts'])}  → {d['final']} ({d['score']:g})")
    return index


def main():
    ap = argparse.ArgumentParser(description="拉取 AtCoder ABC 提交与源码")
    ap.add_argument("--contest", required=True, help="比赛 id，如 abc484")
    ap.add_argument("--users", nargs="+", required=True, help="选手 handle，空格分隔")
    ap.add_argument("--out", default="cache", help="缓存目录（默认 ./cache）")
    args = ap.parse_args()

    start, title = contest_start(args.contest)
    os.makedirs(args.out, exist_ok=True)
    print(f"{title}  ({args.contest})  开始于 {datetime.datetime.fromtimestamp(start):%Y-%m-%d %H:%M}")
    for u in args.users:
        try:
            fetch_user(args.contest, u, start, args.out)
        except urllib.error.HTTPError as e:
            print(f"{u}: HTTP {e.code}", file=sys.stderr)


if __name__ == "__main__":
    main()
