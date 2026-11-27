# -*- coding: utf-8 -*-
"""代码体检：文件读写、读入、写死输出等静态问题。"""
import os
import re

FRE = re.compile(r'freopen\s*\(\s*"([^"]+)"')
READ = re.compile(r"\b(cin\s*>>|scanf\s*\(|getchar|fgets|fscanf)")
CONST = re.compile(r'(cout\s*<<\s*"[\d\s\.\-]+"|printf\s*\(\s*"[\d\s\.\-]+")')


def scan_one(code_dir, slug):
    out = {"exists": False, "files": [], "bytes": 0, "freopen": [],
           "bad_io": False, "no_read": False, "const_only": False}
    if not os.path.isdir(code_dir):
        return out
    files = [f for f in os.listdir(code_dir) if f.lower().endswith((".cpp", ".c"))]
    if not files:
        return out
    out["exists"] = True
    out["files"] = files
    text = open(os.path.join(code_dir, files[0]), "rb").read().decode("utf-8", "ignore")
    out["bytes"] = len(text)
    names = FRE.findall(text)
    out["freopen"] = names
    out["bad_io"] = any(n.endswith(".in") and n != f"{slug}.in" for n in names)
    out["no_read"] = not bool(READ.search(text))
    out["const_only"] = bool(CONST.search(text)) and len(text) < 400
    return out


def scan_all(archive, ids, slugs):
    res = {}
    for sid in ids:
        res[sid] = {slug: scan_one(os.path.join(archive, sid, slug), slug) for slug in slugs}
    return res
