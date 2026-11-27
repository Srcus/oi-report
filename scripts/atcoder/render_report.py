# -*- coding: utf-8 -*-
"""按分析数据（JSON）渲染 AtCoder ABC 代码诊断报告（docx）。

用法：
  python render_report.py --data examples/abc484_red_apple.json --cache ./cache --out ./out

数据格式见 SKILL.md 与 examples/ 下的样例；代码文件的相对路径以 --cache 为基准。
"""
import argparse
import json
import os
import re
import sys

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "common"))
import style as S  # noqa: E402


def trim(src):
    """去掉竞赛模板，只保留 main 之后的部分。"""
    lines = src.splitlines()
    for i, l in enumerate(lines):
        if "signed main" in l or re.match(r"\s*int main\s*\(", l):
            return "\n".join(["// 模板部分（宏、常用函数）已省略，下面从 main 开始。", ""] + lines[i:])
    return src


def resolve(data, cache, p):
    f = p["file"]
    if os.path.isabs(f):
        return f
    return os.path.join(cache, data.get("contest", ""), data["user"], f)


def build(data, cache, out):
    contest_title = data.get("contest_title") or data.get("contest", "AtCoder")
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin = Cm(2.0)
    doc.styles["Normal"].font.name = S.CN_FONT
    doc.styles["Normal"].font.size = Pt(10.5)
    doc.styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), S.CN_FONT)

    p = doc.add_paragraph()
    p.alignment = 1
    r = p.add_run(f"{contest_title}\n代码诊断报告")
    r.bold = True
    r.font.size = Pt(24)
    r.font.color.rgb = S.ACCENT
    S.set_cn(r)
    S.para(doc, f"选手：{data['user']}　　语言：{data.get('language', 'C++')}　　"
                f"得分 {data.get('score', '')}" + (f" / {data['full']}" if data.get("full") else ""),
           gray=True)
    doc.add_paragraph()

    S.h(doc, "一、成绩概览")
    rows = [[p_["letter"], p_["title"], str(p_["points"]), p_["result"],
             f"{p_.get('ms', '')} ms", str(p_.get("attempts", 1))] for p_ in data["problems"]]
    S.add_table(doc, ["题号", "题目", "分值", "结果", "用时", "提交次数"], rows,
                [1.4, 6.4, 1.4, 1.6, 1.8, 2.4])
    if data.get("summary"):
        S.para(doc, data["summary"])

    for idx, p_ in enumerate(data["problems"]):
        n = idx + 2
        S.h(doc, f"{S.CN_NUM[idx]}、{p_['letter']} 题　{p_['title']}"
                f"（{p_['points']} 分，{p_['result']}）")
        S.h(doc, f"{n}.1 题意", level=2)
        S.para(doc, p_.get("statement", ""))
        S.h(doc, f"{n}.2 代码", level=2)
        src = resolve(data, cache, p_)
        if os.path.exists(src):
            tmp = os.path.join(out, "_tmp", f"{data['user']}_{p_['pid']}.cpp")
            os.makedirs(os.path.dirname(tmp), exist_ok=True)
            open(tmp, "w", encoding="utf-8").write(trim(open(src, encoding="utf-8").read()))
            S.add_code(doc, tmp)
        else:
            S.para(doc, "（未找到该题的源码文件）", gray=True)
        S.h(doc, f"{n}.3 分析", level=2)
        S.add_table(doc, ["要点", "说明"], p_.get("rows", []), [4.2, 12.4])
        S.h(doc, f"{n}.4 {'为什么这样写是对的' if p_['result'] == 'AC' else '问题所在'}", level=2)
        S.para(doc, p_.get("verdict", ""))
        S.h(doc, f"{n}.5 建议", level=2)
        S.para(doc, p_.get("advice", ""))

    S.h(doc, f"{S.CN_NUM[len(data['problems'])]}、总结")
    for t in data.get("closing", []):
        S.para(doc, t)

    path = os.path.join(out, f"{data['user']}_{data.get('contest') or data.get('contest_title', 'abc')}_report.docx")
    doc.save(path)
    return path


def main():
    ap = argparse.ArgumentParser(description="渲染 AtCoder 报告")
    ap.add_argument("--data", nargs="+", required=True, help="分析数据 JSON（可多个）")
    ap.add_argument("--cache", default="cache", help="源码缓存目录")
    ap.add_argument("--out", default="out", help="输出目录")
    ap.add_argument("--passcode", default="", help="访问口令")
    args = ap.parse_args()
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))
    import guard
    guard.require(args.passcode)

    os.makedirs(args.out, exist_ok=True)
    for f in args.data:
        data = json.load(open(f, encoding="utf-8"))
        print(build(data, args.cache, args.out))


if __name__ == "__main__":
    main()
