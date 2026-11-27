---
name: oi-report
description: 信息学竞赛与学员报告工具集，三种模式：CSP 代码诊断报告（docx）、AtCoder ABC 代码诊断报告（docx）、学生信息学学习规划书（docx）。用户说"给我出 CSP 报告""看看这几个人的 ABC""给某某做一份学习规划"时使用。
whenToUse: 用户提出生成/批量生成学员代码诊断报告、比赛成绩分析报告或学习规划书，且材料是代码、提交记录或成绩表。
---

# 信息学报告工具集

一个技能，三种报告。先判断用户要哪一种，再走对应流程。

| 用户说 | 走哪个模式 | 入口脚本 |
|---|---|---|
| "出 CSP 报告""分析这几个人的代码" | **CSP 诊断** | `scripts/csp/judge.py` + `scripts/csp/render.py` |
| "看看这几个人的 ABC""出一份 AtCoder 报告" | **AtCoder 诊断** | `scripts/atcoder/fetch_submissions.py` + `scripts/atcoder/render_report.py` |
| "做一份学习规划""家长会材料" | **学习规划** | `scripts/plan/build_plan.py` |

三种报告共用一套排版（`scripts/common/style.py`）：微软雅黑 + Consolas、A4、代码块带行号、表格统一宽度。

---

## 〇、口令（先做这一步）

本工具集受口令保护。**每次调用脚本前，先向用户索取口令**，用 --passcode <口令> 传入，或让用户设置环境变量 OI_REPORT_KEY。

- 不要猜测口令，也不要把它写进报告或代码。
- 口令错误时脚本会直接退出（退出码 2），此时向用户要正确的口令，不要绕过脚本。
- 口令只是使用门槛，不是数据加密；敏感学生数据仍然不要离开本地。

## 一、CSP 代码诊断

适用：有一批选手的代码（每人一题一个 `.cpp`），可能还有真实成绩。

### 1. 本地判题（可选，但有成绩时必须做）

```bash
python scripts/csp/judge.py \
  --submissions ./answers --data ./data \
  --problems examples/csp/problems.json --out result.json
```

- 目录约定：`answers/<考号>/<slug>/<slug>.cpp`，`data/<pid>/1.in|1.ans`
- `problems.json`：`{"problems":[{"slug":"travel","pid":"P17827","points":5}],"time_limit":1.5}`
- 输出每个考号每题得分、TLE/RE/CE 明细

### 2. 写 spec

每人一份 JSON，格式见 `examples/csp/specs/spec_zhangsan.json`。核心字段：

| 字段 | 说明 |
|---|---|
| `mode` | `detail`（有分题成绩）/ `total`（只有总分）/ `code`（无成绩，纯代码分析） |
| `scores` / `total` | 分题成绩、总分（`detail` 模式用） |
| `problems[]` | `no` `title` `pid` `slug` `score` `brief` `blocks[]` |
| `blocks[]` | `h2` / `p` / `code` / `table` / `bullets` |
| `summary[]` | 同样的 block 结构 |

`code` 块从 `--archive/<考号>/<slug>/<slug>.cpp` 取代码。

### 3. 渲染

```bash
python scripts/csp/render.py --specs ./specs --archive ./answers --out ./out
```

---

## 二、AtCoder ABC 诊断

### 1. 抓提交

```bash
python scripts/atcoder/fetch_submissions.py --contest abc484 --users alice bob --out ./cache
```

会把**每一次**提交都下载下来（`attempts/<pid>_<序号>_<结果>.cpp`），并生成 `index.json`。数据来自 AtCoder Problems 公开 API 和 AtCoder 提交页，脚本限速 1.2 秒/次。

### 2. 写分析数据

格式见 `examples/abc484_red_apple.json`。重点：对比第一次 WA 和最后一次 AC，写清"卡在哪、改了什么才过"。

### 3. 渲染

```bash
python scripts/atcoder/render_report.py --data data/alice.json --cache ./cache --out ./out
```

---

## 三、学习规划书

```bash
python scripts/plan/build_plan.py --name 张三 --grade 初二 --out ./out
```

- `--grade`：初一 / 初二 / 初三 / 初四（大庆初中四年制，中考年自动推算）
- `--exam-year`：直接指定中考年，覆盖推算
- 产出 `张三_信息学学习规划.docx`，含 logo、当天日期

需要转 PDF 时用 office_convert 工具，把 docx 转成 pdf 再交付。

---

## 四、写作口径

- 中文，老师的口气。不写"值得注意的是""综上所述"。
- 讲行号和数字，不讲感悟：说"第 21 行把 30 写成 8"。
- 不贴能力标签。卡住写卡在哪，过了写清为什么对。
- 分数低时先找"改一处就能拿分"的地方，最后一段给下一步动作。
- 不写与本次报告无关的学习建议。

详细规则见 `references/tone.md` 与 `references/diagnoses.md`。

## 五、数据与隐私

- **学生姓名、考号、代码、成绩不进仓库**。仓库只放脚本和模板，数据留在本地工作区。
- 生成报告前确认输出目录不在仓库里（`.gitignore` 已排除 `out/`、`cache/`、`data/`）。
- 学习规划里的机构 logo、本地政策与分数线属于内部资料，公开仓库请先替换成占位符。

## 六、依赖

```bash
pip install python-docx openpyxl
```

本地判题需要 `g++`（Windows 可用 w64devkit 的 g++.exe，`--gxx` 指定路径）。
