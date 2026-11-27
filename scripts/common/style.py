# -*- coding: utf-8 -*-
"""报告排版的基础函数（python-docx）。"""
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

CN_FONT = "微软雅黑"
MONO = "Consolas"
ACCENT = RGBColor(0x1F, 0x3B, 0x73)
GRAY = RGBColor(0x59, 0x59, 0x59)
CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]


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
