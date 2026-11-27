# oi-report

信息学竞赛与学员报告工具集，一个技能三种输出：

| 模式 | 输入 | 输出 |
|---|---|---|
| **CSP 诊断** | 选手代码 + 可选的本地判题数据 | 每人的 CSP 代码诊断报告（docx） |
| **AtCoder 诊断** | AtCoder handle + 比赛 id | 每人的 ABC 代码诊断报告（docx） |
| **学习规划** | 学生姓名 + 年级 | 两页 A4 学习规划书（docx） |

三种报告共用一套排版：微软雅黑 + Consolas、A4、代码块带行号、表格列宽统一。

## 安装

```bash
pip install python-docx openpyxl
```

作为 DSH 技能使用：把整个目录放到 `~/.dsh/skills/oi-report/`，之后直接说

> 给这几个人出一下 abc484 的报告

## 快速开始

### CSP

```bash
# 1. 本地判题（可选）
python scripts/csp/judge.py --submissions ./answers --data ./data \
  --problems examples/csp/problems.json --out result.json

# 2. 渲染（每人一份 spec JSON，格式见 examples/csp/spec_zhangsan.json）
python scripts/csp/render.py --specs ./specs --archive ./answers --out ./out
```

### AtCoder

```bash
# 1. 抓提交（会下载每一次提交的源码）
python scripts/atcoder/fetch_submissions.py --contest abc484 --users alice bob --out ./cache

# 2. 渲染
python scripts/atcoder/render_report.py --data data/alice.json --cache ./cache --out ./out
```

### 学习规划

```bash
python scripts/plan/build_plan.py --name 张三 --grade 初二 --out ./out
```

## 目录

```
scripts/
├── common/style.py              共用排版
├── csp/judge.py                 本地判题
├── csp/render.py                CSP 报告渲染
├── atcoder/fetch_submissions.py 抓提交
├── atcoder/render_report.py     ABC 报告渲染
└── plan/build_plan.py           学习规划
references/                      写作口径、诊断模型、政策
examples/                        可直接跑通的样例
```

## 隐私

仓库只放脚本和模板。**学生姓名、考号、代码、成绩都留在本地**，不要提交进来；`.gitignore` 已排除 `out/`、`cache/`、`data/`。

学习规划里的机构 logo 与本地政策属于内部资料，公开前请替换成占位符。

## License

MIT
