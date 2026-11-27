# -*- coding: utf-8 -*-
"""信息学学习规划（重排版）：现状 → 三型诊断 → 3月目标 → 方案 → GESP之后"""

from docx import Document
import sys
from docx.shared import Cm, Pt, RGBColor
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

import argparse
import datetime
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "assets")

_ap = argparse.ArgumentParser(description="生成指针学生信息学规划书")
_ap.add_argument("--name", required=True, help="学生姓名，如 张三")
_ap.add_argument("--grade", default="初二", help="年级：初一 / 初二 / 初三 / 初四，默认 初二")
_ap.add_argument("--date", default="", help="编制日期，默认今天")
_ap.add_argument("--out", default=os.getcwd(), help="输出目录，默认当前目录")
_ap.add_argument("--exam-year", default="", help="中考年份，默认按年级推算（大庆初中四年制）")
_ap.add_argument("--passcode", default="", help="访问口令")
_args = _ap.parse_args()
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "common"))
import guard as _guard
_guard.require(_args.passcode)


NAME = _args.name
GRADE = _args.grade
if _args.date:
    DATE = _args.date
else:
    _today = datetime.date.today()
    DATE = f"{_today.year} 年 {_today.month} 月 {_today.day} 日"
OUTDIR = _args.out
os.makedirs(OUTDIR, exist_ok=True)
OUTPATH = os.path.join(OUTDIR, f"{NAME}_信息学学习规划.docx")

# 大庆初中是四年制（初一—初四）。学年从 9 月开始。
_GRADE_IDX = {"初一": 1, "初二": 2, "初三": 3, "初四": 4}
_today = datetime.date.today()
if _today.month >= 9:
    _school_year = _today.year
else:
    _school_year = _today.year - 1

if _args.exam_year:
    EXAM_YEAR = int(_args.exam_year)
else:
    _idx = _GRADE_IDX.get(GRADE)
    if _idx is None:
        raise SystemExit(f"未知年级：{GRADE}，请用 初一/初二/初三/初四，或直接给 --exam-year")
    EXAM_YEAR = _school_year + 5 - _idx

# 中考年 6 月，粗算还剩几个月
_exam_date = datetime.date(EXAM_YEAR, 6, 20)
MONTHS_LEFT = max(1, round((_exam_date - _today).days / 30.4))

FONT = "微软雅黑"
NAVY = "1F3864"
NAVY_SOFT = "2E5496"
WHITE = "FFFFFF"
AMBER = "A5650A"
AMBER_BG = "FFF6DC"
RED = "C00000"
RED_BG = "FBE9E9"
GREEN = "2E7D32"
BLUE_BG = "EEF1F7"
LINE = "BFBFBF"
HEAD_BG = "DCE3EF"
LIGHT_ROW = "F7F9FC"
DARKTXT = "262626"
MIDTXT = "595959"

CW = 17.0


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def cell_margins(cell, top=60, start=100, bottom=60, end=100):
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for tag, val in (("w:top", top), ("w:start", start), ("w:bottom", bottom), ("w:end", end)):
        el = OxmlElement(tag)
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tcPr.append(mar)


def table_borders(table, color=LINE, sz=4):
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    table._tbl.tblPr.append(borders)


def no_borders(table):
    boundaries = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        boundaries.append(el)
    table._tbl.tblPr.append(boundaries)


def widths(table, cm_list):
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    table._tbl.tblPr.append(layout)
    table.autofit = False
    for row in table.rows:
        for idx, w in enumerate(cm_list):
            row.cells[idx].width = Cm(w)
    for idx, gc in enumerate(table._tbl.tblGrid.findall(qn("w:gridCol"))):
        if idx < len(cm_list):
            gc.set(qn("w:w"), str(int(cm_list[idx] * 567)))


def style_run(run, size, bold=False, color=DARKTXT, font=FONT):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia"):
        rFonts.set(qn(attr), font)


def first_para(cell):
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    return p


def spacer(pt=7):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = Pt(pt)
    style_run(p.add_run(""), 1)


doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(1.4)
sec.bottom_margin = Cm(1.2)
sec.left_margin = Cm(2.0)
sec.right_margin = Cm(2.0)

normal = doc.styles["Normal"]
normal.font.name = FONT
normal.font.size = Pt(10)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.space_after = Pt(0)
normal.paragraph_format.line_spacing = 1.35


def h1(num, title):
    t = doc.add_table(rows=1, cols=1)
    no_borders(t)
    widths(t, [CW])
    c = t.rows[0].cells[0]
    shade(c, NAVY)
    cell_margins(c, top=65, start=130, bottom=65, end=130)
    c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = first_para(c)
    p.paragraph_format.line_spacing = 1.0
    style_run(p.add_run(f"{num}  "), 11, True, "FFC000")
    style_run(p.add_run(title), 11.5, True, WHITE)
    spacer(4)


def para(parts, size=10, after=4, indent=0, keep=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(after)
    pf.line_spacing = 1.33
    if indent:
        pf.left_indent = Cm(indent)
    if keep:
        pf.keep_with_next = True
    pf.keep_together = True
    if isinstance(parts, str):
        parts = [(parts, False, DARKTXT)]
    for text, bold, color in parts:
        style_run(p.add_run(text), size, bold, color)
    return p


def bullet(parts, size=10, after=3, mark="·", mark_color=NAVY_SOFT):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(after)
    pf.line_spacing = 1.32
    pf.left_indent = Cm(0.45)
    pf.first_line_indent = Cm(-0.45)
    style_run(p.add_run(mark + " "), size, True, mark_color)
    if isinstance(parts, str):
        parts = [(parts, False, DARKTXT)]
    for text, bold, color in parts:
        style_run(p.add_run(text), size, bold, color)
    return p


def table(headers, rows, cols_w, hsize=8.8, bsize=8.6, first_bold=True):
    has_head = any(h.strip() for h in headers)
    t = doc.add_table(rows=len(rows) + (1 if has_head else 0), cols=len(headers))
    table_borders(t, color=LINE, sz=4)
    widths(t, cols_w)
    offset = 0
    if has_head:
        offset = 1
        for i, htext in enumerate(headers):
            c = t.rows[0].cells[i]
            shade(c, HEAD_BG)
            cell_margins(c, top=50, start=95, bottom=50, end=95)
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = first_para(c)
            p.paragraph_format.line_spacing = 1.1
            style_run(p.add_run(htext), hsize, True, NAVY)
    for ridx, vals in enumerate(rows):
        row = t.rows[ridx + offset]
        bg = LIGHT_ROW if ridx % 2 == 0 else WHITE
        for cidx, txt in enumerate(vals):
            c = row.cells[cidx]
            shade(c, bg)
            cell_margins(c, top=50, start=95, bottom=50, end=95)
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = first_para(c)
            p.paragraph_format.line_spacing = 1.3
            if cidx == 0 and first_bold:
                style_run(p.add_run(txt), bsize, True, NAVY_SOFT)
            else:
                style_run(p.add_run(txt), bsize, False, DARKTXT)
    spacer(4)
    return t


def callout(parts, bg=AMBER_BG, accent="BF8F00", size=9.8):
    t = doc.add_table(rows=1, cols=1)
    no_borders(t)
    widths(t, [CW])
    c = t.rows[0].cells[0]
    shade(c, bg)
    cell_margins(c, top=80, start=150, bottom=80, end=150)
    tcPr = c._tc.get_or_add_tcPr()
    bdr = OxmlElement("w:tcBorders")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "24")
    left.set(qn("w:color"), accent)
    bdr.append(left)
    tcPr.append(bdr)
    p = first_para(c)
    p.paragraph_format.line_spacing = 1.35
    for text, bold, color in parts:
        style_run(p.add_run(text), size, bold, color)
    spacer(4)


# ================= 标题 =================
LOGO = os.path.join(ASSETS, "logo.jpg")

pl = doc.add_paragraph()
pl.paragraph_format.space_before = Pt(0)
pl.paragraph_format.space_after = Pt(4)
pl.paragraph_format.line_spacing = 1.0
pl.add_run().add_picture(LOGO, width=Cm(2.7))

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(2)
p.paragraph_format.line_spacing = 1.0
style_run(p.add_run("信息学学习规划"), 20, True, NAVY)

p2 = doc.add_paragraph()
p2.paragraph_format.space_before = Pt(0)
p2.paragraph_format.space_after = Pt(9)
p2.paragraph_format.line_spacing = 1.0
style_run(p2.add_run(f"{NAME}　·　{GRADE}　·　{DATE}"), 9.5, False, MIDTXT)

callout([
    ("目标　", True, AMBER),
    (f"{EXAM_YEAR} 年 5 月，大庆信息学特长校考，四校共 16 人。信息学考到 200/400，中考过 443 分，零批次录取。", True, DARKTXT),
    (f"　距离中考还有 {MONTHS_LEFT} 个月。", False, MIDTXT),
], bg=BLUE_BG, accent=NAVY, size=10)

# ================= 一、现状 =================
h1("一", f"{NAME}目前的情况")

para("大体是两件事：语法还没熟，做题时又不太愿意自己想。两样加在一起，就是上课听得懂、自己写不出来。", size=10, after=6)

table(
    ["维度", "现状", "具体表现"],
    [
        ("语法", "还不太熟", "简单题能写。输入输出、循环边界、格式这些地方不稳，题目稍微一变就出错"),
        ("思考", "不主动", "遇到没见过的题，多数时候停在那儿，或者直接问。很少自己先拆一拆"),
        ("结果", "两处卡住", "GESP 一级考了几次没过；初中到现在没拿过编程类奖项，这一条后面第五节会说，是报名的硬条件"),
    ],
    [2.0, 4.6, 10.4],
)

# ================= 二、三型 =================
h1("二", "他不主动思考，是哪一种？")

callout([
    ("先花一分钟判断　", True, AMBER),
    ("拿一道他做过的题，把代码关掉，让他讲一遍思路。", True, DARKTXT),
    ("\n讲不下去，或者只是把代码念一遍 → A　　讲得清楚、一碰键盘就卡 → B　　讲得出，但两句就带过去 → C", False, MIDTXT),
])

table(
    ["", "是什么情况", "怎么判断", "怎么办"],
    [
        ("A\n听懂了，没学会",
         "上课听得懂，其实是把写法记住了。问他为什么这么写，说不出来；数字一换、条件一变，就写不出来。",
         "讲做过的题，讲到一半讲不下去；或者只会照着代码念。",
         "退回去，两个月不学新算法。每天一道题：读题、把变量列出来、写三行思路、再动手。全程自己做，不看题解。"),
        ("B\n会，但不敢写",
         "思路有，讲得也明白，就是不敢下笔。怕写错，宁可空着，或者一直改。",
         "讲得清楚，但让他当场写，前面十分钟不动键盘；或者写完反复删，一直不交。",
         "把题降到他八成都做得出来的难度。先写三行思路再碰键盘，每题都交一次，错了没关系。这阶段练的是敢写，不是写对。"),
        ("C\n觉得跟他没关系",
         "你讲他就听，但不会主动问，也不愿意多写一行。",
         "讲得出，但一两句就带过；布置任务先谈条件；一提练习就不说话，或者换话题。",
         "别再给长线规划。让他做一个自己想要的程序，小游戏、自动签到、抓数据都行，两周做出一个能看见结果的。"),
    ],
    [3.0, 4.8, 4.2, 5.0],
)

para([
    ("容易出错的地方：", True, RED),
    ("把他当成 B，逼他写思路，他写不出，越练越抵触；当成 A，反复练早会的，他觉得没意思；当成 C，加课就跑了。", False, MIDTXT),
], size=9.3, after=6)

para([
    ("今天先不下结论也行。跟家长说「我先观察两周」，比当场给孩子贴个标签稳妥。", True, NAVY),
], size=9.8, after=4)

# ================= 三、阶段一目标 =================
h1("三", "第一阶段目标：2027 年 3 月 GESP 一级")

table(
    ["", ""],
    [
        ("考什么", "2027 年 3 月，CCF GESP 一级，C++。一级一年考四次：3、6、9、12 月各一次"),
        ("目标", "60 分通过，争取 75 分以上"),
        ("为什么考", "一级考的全是语法，正好用来检验这几个月语法有没有过关"),
        ("考到哪一级", "只考一级。往上考对特长校考没有加分，不用花那个时间"),
    ],
    [2.6, 14.4],
)

# ================= 四、方案 =================
h1("四", "3 月之前：语法和读题")

para([("语法（占大部分时间）", True, NAVY)], size=10.2, after=3)
para("顺序：输入输出和格式 → 变量和数据类型 → 分支 → 循环和边界 → 数组 → 字符串 → 函数 → 排序。", size=9.8, after=3, indent=0.45)
para("他最容易错的三处：输出多空格少换行、循环边界、数组下标。这三块单独多练。", size=9.8, after=6, indent=0.45)

para([("读题（每天十几分钟）", True, NAVY)], size=10.2, after=3)
para("不写代码，只讲：这道题给了什么、要什么、中间要记什么。一天三道，一道一分钟。", size=9.8, after=2, indent=0.45)
para("写代码之前先写三行：输入是什么、输出是什么、分几步从输入做到输出。", size=9.8, after=6, indent=0.45)

callout([
    ("课上和在家都按这三条来　", True, AMBER),
    ("不看题解。卡满 30 分钟、思路也写下来了，才可以看；看完关掉，自己重写一遍。", False, DARKTXT),
    ("\n每题都要交一次，错了也算做过。错题重写一遍，不许看一眼就算懂。", False, DARKTXT),
    ("\n每天 70 分钟：20 分钟读题写思路（不碰键盘），40 分钟写代码自己测，10 分钟记下卡在哪儿。", False, MIDTXT),
], bg=AMBER_BG, accent="BF8F00", size=9.6)

callout([
    ("为什么先补语法　", True, RED),
    ("他现在写不出来，不是因为不知道该用什么算法，是语法还没熟。语法不过关就去学算法，每道题都卡在输入和边界上，算法也学不进去。", False, DARKTXT),
], bg=RED_BG, accent=RED, size=9.4)

# ================= 五、之后 =================
h1("五", "考完 GESP 之后：准备 CSP")

_csp_years = [y for y in (EXAM_YEAR - 2, EXAM_YEAR - 1) if y >= 2027]
_rows = [
    ("2027.03—06", "简单算法：枚举、模拟、排序、贪心、二分、前缀和与差分、STL；语法洞随题补", "真题前两题 ≥150/200"),
    ("2027.06 看一次", "到了 150 就上进阶算法（递归分治、搜索、DP）；没到就把前两题练到基本不丢分", "决定暑假练什么"),
]
for _i, _y in enumerate(_csp_years):
    if len(_csp_years) == 1:
        _label = f"{_y}.07—10"
        _what = "CSP-J：第一轮拿等级证书（也是报名条件），第二轮主攻前两题"
    elif _i == 0:
        _label = f"{_y}.09—10"
        _what = "第一次 CSP-J：第一轮拿等级证书，第二轮当练兵，熟悉考场节奏"
    else:
        _label = f"{_y}.07—10"
        _what = "第二次 CSP-J，校考前最后一次：主攻前两题满分"
    _rows.append((_label, _what, "第一轮必过；第二轮 150+" if _i == 0 and len(_csp_years) > 1 else "第二轮 200+"))

_rows.append((f"{EXAM_YEAR}.03—05", "四题制模拟，按 3 小时做整卷；5 月中校考", "校考 ≥200/400"))
_rows.append((f"{EXAM_YEAR}.06", "中考", "≥ 443 分"))

table(
    ["时间", "做什么", "达到什么程度"],
    _rows,
    [3.2, 9.6, 4.2],
)

if len(_csp_years) > 1:
    para([
        ("CSP 有两次机会。", True, NAVY),
        ("第一次练手，把第一轮证书拿到手；第二次（初四上）才是拿结果的那次。两次之间多出来的一年，正好补语法漏洞和进阶算法。", False, MIDTXT),
    ], size=9.6, after=4)
else:
    para([
        ("第一轮不管走哪条路都要考。", True, NAVY),
        ("证书是报名的硬条件；6 月那次只看暑假练什么、目标定多少。", False, MIDTXT),
    ], size=9.6, after=4)

spacer(4)
p = doc.add_paragraph()
p.paragraph_format.line_spacing = 1.2
style_run(p.add_run("阶段划分和知识点顺序，按 CCF 大纲整理的两份开源材料排的：github.com/challeger/CSP（CSP-J 学习路线）、OI-Wiki（oi-wiki.org）。"), 7.8, False, "595959")

p = doc.add_paragraph()
p.paragraph_format.line_spacing = 1.2
style_run(p.add_run(f"数据来源：CCF GESP 官网 · 大庆市教育局网络问政 · 2026 年中考录取方案及特长生成绩汇总。政策以 {EXAM_YEAR} 年官方文件为准。"), 7.8, False, "8C8C8C")

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(3)
p.paragraph_format.line_spacing = 1.2
style_run(p.add_run("指针科技　·　教学内部材料"), 7.8, True, "595959")

doc.save(OUTPATH)
print("saved", OUTPATH)











