# -*- coding: utf-8 -*-
"""按 spec(JSON) 渲染学员代码诊断报告（docx）。

三种模式：
  detail —— 有 T1~T4 分题成绩，报告里带每题分数
  total  —— 只有总分，不提每题分数
  code   —— 没有任何成绩，纯代码分析
"""
import json
import sys
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ARCHIVE = os.path.join(ROOT, "luogu-submit", "input", "answers")
SPEC_DIR = os.path.join(HERE, "specs")
OUT = os.path.join(HERE, "out")
LOGO = ""


def bar(score, full=5):
    score = max(0, min(full, int(score)))
    return "█" * score + "░" * (full - score) + f"  {score}"
os.makedirs(OUT, exist_ok=True)
os.makedirs(SPEC_DIR, exist_ok=True)

CN_FONT = "微软雅黑"
MONO = "Consolas"
ACCENT = RGBColor(0x1F, 0x3B, 0x73)
GRAY = RGBColor(0x59, 0x59, 0x59)
CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八"]


def set_cn(run, font=CN_FONT):
    run.font.name = font
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), font)


def shade(paragraph, color="F2F2F2"):
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    pPr.append(shd)


def add_code(doc, path):
    code = open(path, encoding="utf-8", errors="replace").read().replace("\t", "    ")
    lines = code.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after = Pt(10)
    pf.line_spacing = 1.0
    pf.left_indent = Cm(0.3)
    shade(p)
    run = p.add_run()
    for i, line in enumerate(lines):
        if i:
            run.add_break()
        run.add_text(f"{i + 1:>3}  {line}")
    run.font.name = MONO
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")


def add_table(doc, header, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, hh in enumerate(header):
        cell = t.rows[0].cells[i]
        cell.text = ""
        r = cell.paragraphs[0].add_run(hh)
        r.bold = True
        r.font.size = Pt(9.5)
        set_cn(r)
        shade(cell.paragraphs[0], "DCE6F1")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(9.5)
            set_cn(r)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def h(doc, text, level=1):
    p = doc.add_heading(level=level)
    r = p.add_run(text)
    r.font.color.rgb = ACCENT
    r.font.name = CN_FONT
    r._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), CN_FONT)


def para(doc, text, size=10.5, bold=False, gray=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.4
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.bold = bold
    if gray:
        r.font.color.rgb = GRAY
    set_cn(r)


def bullet(doc, text, prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.35
    if prefix:
        r0 = p.add_run(prefix)
        r0.bold = True
        r0.font.size = Pt(10.5)
        set_cn(r0)
    r = p.add_run(text)
    r.font.size = Pt(10.5)
    set_cn(r)


def render_block(doc, b, adm, slug):
    t = b["t"]
    if t == "h2":
        h(doc, b["x"], 2)
    elif t == "p":
        para(doc, b["x"], bold=b.get("bold", False), gray=b.get("gray", False))
    elif t == "code":
        path = b.get("path") or os.path.join(ARCHIVE, adm, slug, f"{slug}.cpp")
        if os.path.exists(path):
            add_code(doc, path)
        else:
            para(doc, "（本题未提交，无代码可分析）", gray=True)
    elif t == "table":
        add_table(doc, b["head"], b["rows"], b.get("w"))
    elif t == "bullets":
        for item in b["items"]:
            bullet(doc, item[1], item[0] if isinstance(item, list) else None)
    else:
        raise ValueError(t)


def build(spec):
    mode = spec.get("mode", "detail")
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.0)

    normal = doc.styles["Normal"]
    normal.font.name = CN_FONT
    normal.font.size = Pt(10.5)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)

    # 封面
    for _ in range(2):
        doc.add_paragraph()
    logo = spec.get("logo") or LOGO
    if logo and os.path.exists(logo):
        lp = doc.add_paragraph()
        lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        lp.add_run().add_picture(logo, width=Cm(7.5))
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(spec.get("contest_label", "CSP-J 2026 复赛"))
    r.font.size = Pt(30)
    r.bold = True
    r.font.color.rgb = ACCENT
    set_cn(r)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("代码诊断报告")
    r.font.size = Pt(30)
    r.bold = True
    r.font.color.rgb = ACCENT
    set_cn(r)
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"{spec['name']}　{spec['adm']}")
    run.font.size = Pt(16)
    set_cn(run)
    for _ in range(2):
        doc.add_paragraph()

    s = spec.get("scores") or {}
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if mode == "detail":
        vals = [s.get(k) for k in ("travel", "string", "and", "card")]
        if all(v not in (None, "") for v in vals):
            line = (f"真实成绩　T1 {vals[0]}　T2 {vals[1]}　T3 {vals[2]}"
                    f"　T4 {vals[3]}　总分 {spec.get('total')} / 400")
        else:
            line = "代码分析"
    elif mode == "total":
        line = f"复赛总分　{spec.get('total')} / 400"
    else:
        line = "代码分析"
    r = p.add_run(line)
    r.font.size = Pt(12)
    r.font.color.rgb = GRAY
    set_cn(r)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(spec.get("org_line", ""))
    r.font.size = Pt(10.5)
    r.font.color.rgb = GRAY
    set_cn(r)
    doc.add_page_break()

    # 能力画像（可选）
    has_profile = bool(spec.get("profile"))
    sec = 1
    if has_profile:
        prof = spec["profile"]
        h(doc, "一、能力画像")
        if prof.get("summary"):
            para(doc, prof["summary"])
        rows = [[d["name"], bar(d["score"]), d.get("evidence", "")] for d in prof["dimensions"]]
        add_table(doc, ["能力维度", "评分", "依据"], rows, [3.2, 3.0, 10.4])
        if prof.get("total_line"):
            para(doc, prof["total_line"], gray=True)
        h(doc, "二、弱项与补强")
        for w in prof.get("weak", []):
            para(doc, f"{w['name']}（{w['score']} 分）", bold=True)
            para(doc, w["why"])
            para(doc, w["fix"])
        sec = 3

    # 概览
    h(doc, f"{CN_NUM[sec-1]}、代码概览" if mode == "code" else f"{CN_NUM[sec-1]}、成绩概览")
    para(doc, spec["lead"])
    rows = []
    if mode == "detail":
        for pr in spec["problems"]:
            rows.append([pr["no"], pr["title"], pr["pid"], "100", str(pr.get("score", "")), pr["brief"]])
        rows.append(["合计", "", "", "400", str(spec.get("total", "")), ""])
        add_table(doc, ["题号", "题目", "洛谷", "满分", "得分", "核心问题"], rows,
                  [1.8, 2.4, 2.0, 1.4, 1.4, 7.6])
    else:
        for pr in spec["problems"]:
            rows.append([pr["no"], pr["title"], pr["pid"], pr["brief"]])
        add_table(doc, ["题号", "题目", "洛谷", "核心问题"], rows, [1.8, 2.4, 2.2, 10.2])

    # 各题
    for idx, pr in enumerate(spec["problems"]):
        title = f"{CN_NUM[idx + sec]}、{pr['no']}　{pr['title']}"
        if mode == "detail":
            title += f"（{pr.get('score')} / 100）"
        h(doc, title)
        for b in pr["blocks"]:
            render_block(doc, b, spec["adm"], pr["slug"])

    # 总结
    h(doc, f"{CN_NUM[len(spec['problems']) + sec]}、总结与训练建议")
    for b in spec["summary"]:
        render_block(doc, b, spec["adm"], "")

    prefix = f"{spec['name']}_" if spec.get('name') and spec['name'] != spec['adm'] else ""
    name = f"{prefix}{spec['adm']}_{spec.get('file_tag', 'CSP-J2026')}_代码诊断报告.docx"
    path = os.path.join(OUT, name)
    doc.save(path)
    return path


def main():
    import argparse
    ap = argparse.ArgumentParser(description="渲染 CSP 代码诊断报告")
    ap.add_argument("--specs", required=True, help="spec JSON 目录")
    ap.add_argument("--archive", default="", help="代码目录 <考号>/<slug>/<slug>.cpp")
    ap.add_argument("--out", default="out", help="输出目录")
    ap.add_argument("--logo", default="", help="封面 logo 图片路径")
    ap.add_argument("--passcode", default="", help="访问口令")
    args = ap.parse_args()
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common"))
    import guard
    guard.require(args.passcode)

    global ARCHIVE, OUT, LOGO
    if args.archive:
        ARCHIVE = args.archive
    if args.logo:
        LOGO = args.logo
    OUT = args.out
    os.makedirs(OUT, exist_ok=True)
    files = sorted(f for f in os.listdir(args.specs) if f.endswith(".json"))
    ok = 0
    for f in files:
        spec = json.load(open(os.path.join(args.specs, f), encoding="utf-8"))
        try:
            print(build(spec))
            ok += 1
        except Exception as e:
            print("FAIL", f, e)
    print(f"rendered {ok}/{len(files)}")


if __name__ == "__main__":
    main()
