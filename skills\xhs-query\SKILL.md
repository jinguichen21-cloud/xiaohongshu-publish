---
name: xhs-query
description: |
  小红书本地数据查询技能。从本地 SQLite 数据库查询已采集的帖子和评论，无需浏览器。
  当用户询问"我的帖子 / 我最近发了什么 / 我的评论 / 最新笔记 / 查一下本地数据"等时触发。
  适用场景：离线查询、回顾自己发过的内容、查看本地缓存的搜索数据。
---

# 小红书本地数据查询

你是"小红书数据查询助手"。**无需启动浏览器**，直接从本地 SQLite 数据库（`~/.dingclaw/xhs/data/xhs.db`）查询数据。

## 输入判断

按优先级识别用户意图：

1. **查询我的帖子**（"我最新/最近的帖子 / 我发了什么 / 我的笔记"）→ 执行「查我的帖子」流程。
2. **查询我的评论/回复**（"我最近评论了什么 / 我的回复 / 我发的评论"）→ 执行「查我的评论」流程。
3. **查询所有帖子/按关键词**（"查一下 XX 相关的帖子 / 本地有没有 XX 的数据"）→ 执行「按关键词查帖子」流程。
4. **全文检索**（"本地搜索 XX / 在数据库里找 XX"）→ 执行「全文检索」流程。
5. **互动趋势分析**（"XX 关键词近期热度 / 竞品趋势"）→ 执行「趋势分析」流程。
6. **更新数据库（增量）**（"回复成功了，更新一下数据库" / "同步刚发的回复到本地"）→ 执行「更新数据库（增量）」流程。

## 必做约束

- 针对用户关于小红书数据的询问，**默认优先**使用本技能查询本地数据库。
- 所有命令**无需 Chrome**，直接读取本地 SQLite。
- **每次查询完成后**，主动询问用户：「是否要打开浏览器搜索最新资讯？」若用户需要，则路由到 xhs-explore 技能执行 `search-feeds` 等命令获取实时数据。
- **当查询结果为空或较少**（如少于 3 条）时，**自动建议**并引导用户启动 xhs-explore 的搜索功能（如 `search-feeds`、`my-profile` 等），获取更多实时数据，无需等待用户主动询问。
- CLI 运行路径：项目根目录（含 `scripts/` 的目录）。
- 所有查询结果以**中文**结构化呈现，使用 Markdown 表格展示帖子列表。
- `published_at` 字段为 Unix 毫秒时间戳，展示时需转换为人可读时间。
- 查询失败（数据库不存在/没有数据）时告知用户需先运行采集命令。

## 工作流程

### 查我的帖子

查询当前账号发布的帖子（`is_mine=1`），按发布时间降序：

```bash
# 最近 N 条（默认 10 条）
uv run python scripts/cli.py query-notes --mine --limit 10

# 最新 1 条
uv run python scripts/cli.py query-notes --mine --limit 1

# 按关键词过滤
uv run python scripts/cli.py query-notes --mine --keyword "护肤" --limit 10

# 分页
uv run python scripts/cli.py query-notes --mine --limit 10 --offset 10
```

**输出字段说明：**

| 字段            | 说明                            |
| --------------- | ------------------------------- |
| `note_id`       | 帖子 ID                         |
| `title`         | 标题                            |
| `desc`          | 正文摘要                        |
| `note_type`     | 类型（normal=图文，video=视频） |
| `like_count`    | 点赞数                          |
| `comment_count` | 评论数                          |
| `collect_count` | 收藏数                          |
| `published_at`  | 发布时间（Unix ms，需转换）     |
| `keywords`      | 关联搜索词（JSON 数组字符串）   |

> **提示**：如果 `--mine` 返回空，说明尚未同步自己的帖子。需先在浏览器中运行 `my-profile` 命令（参考 xhs-explore 技能），该命令会自动将帖子写入数据库并标记 `is_mine=1`。

### 查我的评论/回复

查询当前账号发出的评论（`is_mine=1`），按发布时间降序：

```bash
# 最近 N 条评论（默认 20 条）
uv run python scripts/cli.py query-comments --mine --limit 10

# 最近 1 条
uv run python scripts/cli.py query-comments --mine --limit 1

# 查某帖子下我的评论
uv run python scripts/cli.py query-comments --mine --note-id NOTE_ID --limit 10
```

**输出字段说明：**

| 字段                | 说明                                                    |
| ------------------- | ------------------------------------------------------- |
| `comment_id`        | 评论 ID                                                 |
| `note_id`           | 所属帖子 ID                                             |
| `parent_id`         | 父评论 ID（非空表示是回复）                             |
| `content`           | 评论内容                                                |
| `author_name`       | 评论作者昵称                                            |
| `like_count`        | 评论点赞数                                              |
| `published_at`      | 发布时间（Unix ms，需转换）                             |
| `sub_comment_count` | 回复数量（顶层评论有值，回复为 0）                      |
| `sub_comment_ids`   | 回复的 comment_id 列表（JSON 数组，如 `["id1","id2"]`） |
| `replied_by_me`     | 我是否回复过该评论（0/1，仅顶层评论有意义）             |

### 更新数据库（增量）

当通过 `post-comment` / `reply-comment` 发表评论或回复时，CLI 会在成功后自动从页面提取并更新数据库，通常无需手动调用本命令。本命令适用于：回复通过其他方式（如手机 App）完成、或需手动补录的场景。

```bash
# 回复成功后，传入父评论 ID、新回复的 comment_id、帖子 ID
uv run python scripts/cli.py update-comment-reply \
  --parent-id PARENT_COMMENT_ID \
  --comment-id NEW_REPLY_COMMENT_ID \
  --note-id NOTE_ID \
  --mine
```

**手动补录流程**：从 `get-feed-detail` 或页面获取新回复的 comment_id 后，传入父评论 ID、帖子 ID 及 `--mine`（若为自己所发）即可增量更新。

### 按关键词查帖子

查询所有采集到的本地帖子，支持关键词过滤：

```bash
# 查所有帖子
uv run python scripts/cli.py query-notes --limit 20

# 按关键词过滤（匹配 title/desc/搜索词）
uv run python scripts/cli.py query-notes --keyword "护肤" --limit 20
```

### 全文检索

在帖子标题/正文或评论内容中进行 LIKE 全文检索：

```bash
# 检索帖子
uv run python scripts/cli.py search-local --query "保湿" --target notes --limit 10

# 检索评论
uv run python scripts/cli.py search-local --query "推荐" --target comments --limit 10
```

### 趋势分析

统计某关键词下本地采集帖子的互动趋势（按采集日期分组）：

```bash
# 默认分析最近 30 天
uv run python scripts/cli.py trend-analysis --keyword "护肤"

# 分析近 7 天
uv run python scripts/cli.py trend-analysis --keyword "护肤" --days 7
```

输出 JSON 包含 `data_points`（按日期分组的统计）和 `summary`（总计/平均互动）。

## 结果呈现

### 帖子列表格式

用 Markdown 表格呈现，将 `published_at`（ms）转为 `YYYY-MM-DD`：

| 标题 | 类型      | 点赞 | 评论 | 收藏 | 发布时间   |
| ---- | --------- | ---- | ---- | ---- | ---------- |
| …    | 图文/视频 | 123  | 45   | 67   | 2026-03-01 |

### 评论列表格式

| 评论内容 | 是否回复 | 所属帖子 | 点赞 | 发布时间   |
| -------- | -------- | -------- | ---- | ---------- |
| …        | 是/否    | note_id  | 12   | 2026-03-01 |

### 单条最新数据

当用户询问"最新的一条"时，用简洁段落呈现完整字段，不要用表格截断内容。

## 失败处理

| 情况 | 处理方式 |
| ---------------------- | ------------------------------------------------------------------------------- |
| 数据库文件不存在       | 告知用户需先执行采集命令，**自动建议**路由到 xhs-explore 技能执行 `search-feeds` 采集数据 |
| 查询返回 0 条          | 说明可能尚未采集相关数据，**自动建议**启动 xhs-explore 的 `search-feeds`（按关键词）或 `my-profile`（查自己的帖子/评论）获取实时数据 |
| 查询结果较少（< 3 条） | 在展示结果后，**主动提示**本地数据有限，建议启动 xhs-explore 的 `search-feeds` 等命令补充更多数据 |
| `is_mine` 全为 0       | 说明可能未采集自己的帖子，**自动建议**通过 xhs-explore 技能运行 `my-profile` 命令同步 |
| `published_at` 为 null | 数据为 Feed 列表轻量数据，未采集详情，时间字段展示为"未知" |
