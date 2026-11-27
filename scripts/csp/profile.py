# -*- coding: utf-8 -*-
"""能力评估：把判题结果和代码体检映射成六个维度。"""

FIX = {
    "读题与细节": "养成先写输入输出、再写逻辑的习惯。提交前对照题面检查三件事：文件名、输入顺序、输出格式。",
    "代码实现": "每次提交前本地编译一次；数组按上限 +5 开；用 1 开始的下标时把 n+1 算进去。",
    "复杂度意识": "读题先看数据范围：n≤5000 想 O(n²)，n≤2e5 只能 O(n log n)。写完估一次运算量再提交。",
    "知识点": "这周补这块：先看一遍模板，再做 3 道同类题，做完对拍。",
    "分析与建模": "拿到题先手算样例，把「输入怎么变成输出」用自己的话写一行，再想每一步维护什么。",
    "应试策略": "每题至少交一版能跑的代码；先写暴力拿部分分，再想优化，不要交空文件。",
}

ORDER = ["读题与细节", "代码实现", "复杂度意识", "知识点", "分析与建模", "应试策略"]


def _score(start, deduct):
    return max(1, min(5, start - deduct))


def assess(total, results, scan, meta):
    """results: {slug: {score,status,tests,total}}；scan: {slug: {...}}；meta: 题目列表"""
    ce = sum(1 for r in results.values() if r.get("status") == "CE")
    re_cnt = sum(1 for r in results.values() if "RE" in (r.get("tests") or []))
    all_tests = sum(len(r.get("tests") or []) for r in results.values())
    tle = sum((r.get("tests") or []).count("TLE") for r in results.values())
    tle_ratio = (tle / all_tests) if all_tests else 0
    missing = sum(1 for r in results.values() if r.get("status") == "缺交")
    zero_code = sum(1 for r in results.values() if r.get("status") == "ok" and r.get("score", 0) == 0)
    bad_io = [s for s, v in scan.items() if v.get("bad_io")]
    hardcode = [s for s, v in scan.items() if v.get("const_only")]

    weak_tags = []
    for p in meta:
        r = results.get(p["slug"], {})
        full = p.get("points", 5) * (r.get("total") or 20)
        pct = (r.get("score", 0) / full * 100) if full else 0
        if pct < 40:
            weak_tags += [t for t in p.get("tags", []) if t not in weak_tags]

    dims = []
    # 读题与细节
    d = 0
    if bad_io:
        d += 2
    dims.append(("读题与细节", _score(5, d),
                 ("freopen 文件名写错：" + "、".join(bad_io)) if bad_io else "文件读写和输入格式没有发现问题"))
    # 代码实现
    d = 0
    if ce >= 2:
        d += 3
    elif ce == 1:
        d += 2
    if re_cnt >= 1:
        d += 1
    dims.append(("代码实现", _score(5, d),
                 (f"编译失败 {ce} 题，" if ce else "") + (f"{re_cnt} 题运行出错" if re_cnt else "运行稳定")))
    # 复杂度意识
    d = 3 if tle_ratio > 0.5 else 2 if tle_ratio > 0.25 else 1 if tle_ratio > 0 else 0
    dims.append(("复杂度意识", _score(5, d),
                 f"超时占失败点 {tle_ratio*100:.0f}%" if tle else "没有超时"))
    # 知识点
    d = min(2, len(weak_tags))
    dims.append(("知识点", _score(5, d),
                 ("薄弱：" + "、".join(weak_tags)) if weak_tags else "覆盖了本场涉及的知识点"))
    # 分析与建模
    d = 2 if zero_code >= 2 else 1 if zero_code == 1 else 0
    dims.append(("分析与建模", _score(5, d),
                 f"{zero_code} 题有代码但 0 分" if zero_code else "思路方向正确"))
    # 应试策略
    d = 0
    if missing:
        d += min(2, missing)
    if hardcode:
        d += 2
    dims.append(("应试策略", _score(5, d),
                 ("缺交 " + "、".join(s for s, r in results.items() if r.get("status") == "缺交")) if missing
                 else ("写死输出：" + "、".join(hardcode)) if hardcode else "四题都交了，没有空文件"))

    dimensions = [{"name": n, "score": s, "evidence": e} for n, s, e in dims]
    ranked = sorted(dimensions, key=lambda x: (x["score"], ORDER.index(x["name"])))
    weak = []
    for w in ranked[:2]:
        fix = FIX[w["name"]]
        if w["name"] == "知识点" and weak_tags:
            fix = f"这周补 {'、'.join(weak_tags)}：先看模板，再做 3 道同类题，做完对拍。"
        weak.append({"name": w["name"], "score": w["score"], "why": w["evidence"], "fix": fix})

    best = ranked[-1]
    summary = (f"总分 {total}。相对最稳的是「{best['name']}」，最需要补的是「{weak[0]['name']}」"
               f"和「{weak[1]['name']}」。")
    return {
        "dimensions": dimensions,
        "weak": weak,
        "summary": summary,
        "total_line": "评分说明：每项 5 分起步，按判题与代码体检的证据扣分，最低 1 分。",
    }
