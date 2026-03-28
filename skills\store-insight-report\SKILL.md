---
name: store-insight-report
description: |
  数据分析报告技能。基于 XHSCollection JSON 数据，生成结构化 Markdown 分析报告。
  当用户说"分析这批数据"/"给我出报告"/"帮我分析小红书笔记数据"时触发。
  输入：XHSCollection JSON 文件路径，或 pipeline 输出的分析上下文 JSON。
  输出：完整 Markdown 报告内容（必须直接呈现给用户），可选写入文件。
  无需任何外部 API Key，由当前模型自身完成分析。
---

# 数据分析报告技能

你是"数据分析助手"。**由你自己直接分析数据并生成报告**，无需任何外部 AI API、无需运行任何脚本。

## 两种调用方式

### 方式 A：直接调用（用户提供 JSON 文件路径）

用户提供 XHSCollection JSON 文件路径，你读取后生成报告。

### 方式 B：被 solo-store-pipeline 调用

pipeline 委托本 skill 处理报告生成。你在 store-insight-report 项目根目录执行 `generate_report.py <collection.json>`，或直接调用本 skill 传入 JSON 路径。脚本输出分析上下文 JSON，你解析后用 `system_prompt` + `user_message` 生成报告，**并将完整报告内容直接输出给用户**。

---

## 方式 A 执行步骤（直接调用）

**输入判断**：用户应提供 XHSCollection JSON 文件路径。若未提供，提示："请先提供 XHSCollection JSON 文件路径，可自行生成或直接传入 JSON 数据。"

**Step 1**：读取 `prompts/analysis_prompt.md` 作为分析指令。

**Step 2**：读取用户提供的 JSON 文件内容。

**Step 3**：严格按照 `analysis_prompt.md` 的维度和格式要求，直接生成完整 Markdown 报告。

**Step 4**：将报告写入 `~/.dingclaw/store-insight-report/report_<关键词>_<YYYYMMDD_HHMMSS>.md`，并**将完整报告内容直接呈现给用户**。

---

## 方式 B 执行步骤（pipeline 集成）

当 pipeline 输出中包含 `=== SOLO_STORE_REPORT_JSON ===` 标记的 JSON 块时：

**Step 1**：解析每个 JSON 块，提取 `system_prompt`、`user_message`、`meta`。

**Step 2**：以 `system_prompt` 为分析指令、`user_message` 为数据输入，**直接生成完整 Markdown 报告**。

**Step 3**：**立即将报告内容输出给用户**（核心产出，不可省略）。可选：写入 `meta.suggested_output_path` 持久化。

> ⚠️ 报告内容必须直接呈现在对话中，不能只说"报告已生成"或"已写入文件"。

---

## generate_report.py 输出格式（供 pipeline 解析）

```json
{
  "meta": {
    "suggested_output_path": "~/.dingclaw/store-insight-report/report_xxx.md",
    "total_items": 28,
    "query": "关键词",
    "source": "search"
  },
  "system_prompt": "分析指令（来自 analysis_prompt.md）",
  "user_message": "请基于以下 XHSCollection JSON 数据生成分析报告：\n\n```json\n{...}\n```"
}
```

---

## 失败处理

| 错误           | 处理方式                                              |
| -------------- | ----------------------------------------------------- |
| 输入文件不存在 | 提示用户检查路径，或自行生成/直接传入 XHSCollection JSON 数据 |
| items 为空     | 仍生成报告，注明"无数据"                              |
