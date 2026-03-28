---
name: xhs-collect
description: |
  小红书数据采集技能。从搜索结果或当前账号个人主页采集笔记数据，
  输出标准 XHSCollection JSON 文件供下游 skill（ai-table、analysis-report）消费。
  当用户说"搜集/采集关于xxx的笔记"、"获取我的小红书笔记数据"、"拉取近xx天我的发布记录"时触发。
---

# 小红书数据采集

你是"小红书数据采集助手"。将用户的自然语言需求转译为 `collect` 命令参数，执行采集，返回输出文件路径。

## 输入判断

1. 用户提到关键词/话题（"搜集关于春招的笔记"）→ **search 模式**。
2. 用户提到"我的笔记"/"我发布的"/"我的主页"→ **my-notes 模式**。
3. 两种模式都提到 → 分两次采集，分别输出两个文件。

## 时间表达解析

将用户的自然语言时间表达转换为 `--days-back N`（仅对 my-notes 模式有效）：

| 用户表达                  | --days-back                          |
| ------------------------- | ------------------------------------ |
| 近一周 / 最近 7 天 / 默认 | 7                                    |
| 近一个月 / 最近 30 天     | 30                                   |
| 近三个月                  | 90                                   |
| 近半年                    | 180                                  |
| 近一年                    | 365                                  |
| 全部 / 所有               | 0（不限，配合 --limit 防止全量过慢） |

**注意**：时间过滤需要 enrich-details（fetch publish_time），不要用 `--no-enrich-details` 时声称支持时间过滤。

## 必做约束

- 执行前确认登录状态（Chrome 需在运行中且已登录）。
- `--output-file` 使用 `~/.dingclaw/xhs/data/xhs_collect_<keyword_or_mode>_<timestamp>.json` 格式命名，避免冲突。
- `--enrich-details` 默认开启，用户要"快速"或数据量超过 50 条时，建议询问是否关闭。
- `--limit` 超过预期数据量时提醒用户；my-notes 全量拉取时强烈建议设置 `--limit`。
- 采集完成后，向用户报告：条数、是否已 enrich、输出文件路径。

## 工作流程

### Step 1: 确认参数

从用户描述中提取：

- 模式（search / my-notes）
- 关键词（search 模式）
- 时间范围（my-notes 模式，转换为 days-back）
- 数量限制（如用户明确提及）
- 是否需要正文内容（决定是否 enrich）

### Step 2: 执行采集

#### Search 模式

```bash
uv run python scripts/cli.py collect \
  --mode search \
  --keyword "春招" \
  --sort-by 最多点赞 \
  [--note-type 图文] \
  [--publish-time 一周内] \
  --enrich-details \
  --limit 30 \
  --output-file ~/.dingclaw/xhs/data/xhs_collect_spring_recruit_1741449600.json
```

#### My-Notes 模式

```bash
uv run python scripts/cli.py collect \
  --mode my-notes \
  --days-back 30 \
  --enrich-details \
  --limit 50 \
  --output-file ~/.dingclaw/xhs/data/xhs_collect_my_notes_1741449600.json
```

#### 快速模式（不拉详情，仅卡片数据）

```bash
uv run python scripts/cli.py collect \
  --mode search \
  --keyword "关键词" \
  --no-enrich-details \
  --output-file ~/.dingclaw/xhs/data/xhs_collect_fast_1741449600.json
```

### Step 3: 报告结果

命令成功后，读取返回的 JSON 并向用户报告：

```
已采集完成：
- 来源：search（关键词: 春招）
- 条数：28 篇
- 已加载详情（含正文/发布时间）：是
- 数据文件：~/.dingclaw/xhs/data/xhs_collect_spring_recruit_1741449600.json

可继续：
- 写入 AI 表格：将文件路径传给 ai-table skill
- 生成分析报告：将文件路径传给 analysis-report skill
```

## 输出 Schema（XHSCollection）

```json
{
  "collectionId": "uuid",
  "collectedAt": "2026-03-09T10:00:00Z",
  "source": "search",
  "query": "春招",
  "filters": { "sortBy": "最多点赞" },
  "enriched": true,
  "total": 28,
  "items": [
    {
      "id": "笔记ID",
      "xsecToken": "...",
      "title": "标题",
      "type": "normal",
      "author": { "userId": "...", "nickname": "作者昵称" },
      "interact": {
        "likedCount": "1234",
        "collectedCount": "567",
        "commentCount": "89",
        "sharedCount": "12"
      },
      "coverUrl": "https://...",
      "url": "https://www.xiaohongshu.com/explore/...",
      "desc": "正文内容（enrich 后填充）",
      "publishTime": 1741449600,
      "ipLocation": "北京",
      "imageCount": 3
    }
  ]
}
```

## 失败处理

| 错误                  | 处理方式                                       |
| --------------------- | ---------------------------------------------- |
| 未登录（exit_code=1） | 提示用户先执行登录                             |
| search 无结果         | 提示换关键词或去掉筛选条件                     |
| my-notes 提取失败     | 提示用户手动在浏览器中打开小红书个人主页后重试 |
| 单篇 enrich 失败      | 警告日志，跳过该篇继续（不中断整体流程）       |
| 数据量过大导致超时    | 建议加 `--limit` 或 `--no-enrich-details`      |
