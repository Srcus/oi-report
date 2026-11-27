# -*- coding: utf-8 -*-
"""按 Humanizer-zh / plainspoken-writing 的关键词与结构规则扫一遍正文"""
import re
import io
import builtins
from docx import Document

_buf = io.StringIO()
_orig_print = builtins.print


def print(*args, **kwargs):
    kwargs["file"] = _buf
    _orig_print(*args, **kwargs)

DOC = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\信息学特长生规划书.docx"

d = Document(DOC)
lines = []
for tb in d.tables:
    for r in tb.rows:
        for c in r.cells:
            for p in c.paragraphs:
                if p.text.strip():
                    lines.append(p.text.strip())
for p in d.paragraphs:
    if p.text.strip():
        lines.append(p.text.strip())

text = "\n".join(lines)

# 1) 关键词类
LEX = {
    "结构胶水": ["首先", "其次", "最后", "值得注意的是", "综上所述", "综合来看", "总体而言", "不难发现", "显而易见", "众所周知", "毋庸置疑"],
    "空洞词": ["至关重要", "不可或缺", "显著提升", "深度赋能", "深度探讨", "赋能", "闭环", "无缝"],
    "模板句": ["在当今", "随着", "背景下", "时代背景"],
    "交流腔": ["感谢您的", "期待与您", "让我们一起", "希望这对您有帮助", "如有疑问"],
    "口号收尾": ["让我们共同", "未来可期", "携手共进", "拭目以待"],
    "虚词密集": ["极为", "十分", "非常", "极其", "充分"],
}

print("=== 1. 词表命中 ===")
total = 0
for cat, words in LEX.items():
    for w in words:
        n = text.count(w)
        if n:
            total += n
            print(f"  [{cat}] {w} × {n}")
print(f"  合计 {total} 处")

# 2) 结构类
print("\n=== 2. 结构模式 ===")
not_x_but_y = re.findall(r"不是[^，。；]{1,20}，[而就]是[^。]{0,30}", text)
print(f"  不是X而是Y：{len(not_x_but_y)} 处")
for s in not_x_but_y:
    print("    " + s)

dash = text.count("——")
print(f"  破折号「——」：{dash} 处")

bujin = re.findall(r"不仅[^。]{0,40}而且", text)
print(f"  不仅…而且：{len(bujin)} 处")

# 三段式排比：同一句里三个顿号并列 + 结尾四字概括
print(f"  括号注释：{text.count('（')} 处")
print(f"  箭头「→」：{text.count('→')} 处")

# 3) 密度判据（plainspoken：200 字内同类 ≥3 次才算）
print("\n=== 3. 密度判据 ===")
print(f"  正文总字数（去空白）：{len(re.sub(r'\\s', '', text))}")

# 4) 引用/引号检查
print("\n=== 4. 标点 ===")
print(f"  直角引号「」：{text.count('「')} 处")
print(f"  英文直引号：{text.count(chr(34))} 处")

print("\n=== 全文 ===")
print(text)
