# -*- coding: utf-8 -*-
"""把判题结果 + 代码体检 + 能力评估组装成一份报告 spec（全自动，无需人工写）。"""


def _fail_desc(tests):
    if not tests:
        return "没有测试数据"
    from collections import Counter
    c = Counter(tests)
    parts = []
    for k in ("AC", "WA", "TLE", "RE"):
        if c.get(k):
            parts.append(f"{k} {c[k]}")
    return "，".join(parts)


def build_spec(sid, name, results, scan, meta, profile, official=None, org="指针科技", contest="CSP-J 2026 复赛"):
    local_total = sum(r.get("score", 0) for r in results.values())
    has_scores = bool(official) and any((official.get("scores") or {}).values())
    mode = "detail" if has_scores else "code"
    scores = official or {}

    problems = []
    for idx, p in enumerate(meta):
        r = results.get(p["slug"], {})
        s = scan.get(p["slug"], {})
        tests = r.get("tests") or []
        ac = tests.count("AC")
        total_tests = len(tests)
        status = r.get("status", "缺交")

        if status in ("缺交", "空目录"):
            brief = "未提交"
        elif status == "CE":
            brief = "编译失败"
        else:
            brief = f"{total_tests} 个点过 {ac}，本地 {r.get('score', 0)} 分"

        health = []
        if s.get("bad_io"):
            health.append("freopen 文件名错（" + "、".join(s.get("freopen") or []) + "）")
        if s.get("no_read"):
            health.append("没有读入语句")
        if s.get("const_only"):
            health.append("疑似写死输出")
        if not health:
            health.append("文件读写正常")
        if s.get("bytes"):
            health.append(f"代码 {s['bytes']} 字节")

        rows = [
            ["测试点", f"通过 {ac}/{total_tests}" if total_tests else "无数据"],
            ["失败分布", _fail_desc(tests)],
            ["代码体检", "；".join(health)],
        ]

        if status == "CE":
            verdict = "这份代码没有编译通过，后面的测试点都没有跑到。先解决语法或类型错误。"
        elif status in ("缺交", "空目录"):
            verdict = "这题没有提交代码，本场没有可分析的实现。"
        elif ac == total_tests and total_tests:
            verdict = "全部测试点通过，实现是正确的。"
        elif "TLE" in tests and tests.count("TLE") > total_tests * 0.3:
            verdict = f"有 {tests.count('TLE')} 个点超时，说明做法本身的复杂度超出了数据范围，换个算法比调常数更有效。"
        elif r.get("score", 0) == 0:
            verdict = "有代码但测试点全错，通常是题意理解或输出格式的问题，先从样例开始对。"
        else:
            verdict = f"拿到了 {r.get('score', 0)} 分，部分测试点没通过，边界和特殊数据还要再想。"

        advice = p.get("advice") or "对照题面重写一遍输入输出，再逐点检查。"

        blocks = [
            {"t": "h2", "x": f"{idx+2}.1 题目要点"},
            {"t": "p", "x": p.get("summary", "")},
            {"t": "h2", "x": f"{idx+2}.2 代码原文"},
            {"t": "code"},
            {"t": "h2", "x": f"{idx+2}.3 测试结果"},
            {"t": "table", "head": ["项目", "结果"], "w": [3.0, 13.6], "rows": rows},
            {"t": "h2", "x": f"{idx+2}.4 失分点"},
            {"t": "p", "x": verdict},
            {"t": "h2", "x": f"{idx+2}.5 怎么改"},
            {"t": "p", "x": advice},
        ]
        item = {"no": p.get("no", f"第{idx+1}题"), "title": p["title"], "pid": p.get("pid", ""),
                "slug": p["slug"], "brief": brief, "blocks": blocks}
        if mode == "detail":
            item["score"] = scores.get(p["slug"], 0)
        problems.append(item)

    weak_names = "、".join(w["name"] for w in profile["weak"])
    summary = [
        {"t": "p", "x": "这次先用自动分析出一版，重点看最前面的能力画像和弱项。", "bold": True},
        {"t": "bullets", "items": [
            ["① ", f"先补「{profile['weak'][0]['name']}」：{profile['weak'][0]['fix']}"],
            ["② ", f"再补「{profile['weak'][1]['name']}」：{profile['weak'][1]['fix']}"],
            ["③ ", "下一次交卷前，用两分钟对照题面检查文件名、输入顺序、输出格式。"],
        ]},
        {"t": "p", "x": f"本地评测总分 {local_total}，薄弱项集中在 {weak_names}。"},
    ]

    return {
        "name": name, "adm": sid, "mode": mode,
        "scores": scores if has_scores else {}, "total": (official.get("total") if has_scores else None),
        "contest_label": contest, "org_line": org, "file_tag": "CSP-J2026",
        "profile": profile,
        "lead": f"先看能力画像和弱项，后面是逐题分析。本地评测总分 {local_total}。",
        "problems": problems,
        "summary": summary,
    }
