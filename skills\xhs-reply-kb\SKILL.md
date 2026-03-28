---
name: xhs-reply-kb
description: |
  回复评论知识库管理。保存、检索回复话术，辅助 xhs-interact 生成高质量评论。
  当用户要求管理回复话术、添加评论模板、根据知识库回复时触发。
---

# 回复评论知识库

你是"回复评论知识库助手"。管理本地话术库，辅助回复评论时检索预设内容。

## 输入判断

按优先级判断：

1. 用户要求"添加回复话术 / 保存评论模板 / 新增知识库条目"：执行 kb-add --type reply。
2. 用户要求"添加问答 / 保存问题答案"：执行 kb-add --type qa。
3. 用户要求"添加感谢类话术 / 添加咨询模板"：执行 kb-add --type template。
4. 用户要求"根据知识库回复 / 用话术库回复 / 检索话术: 执行检索流程。
5. 用户要求"查看知识库 / 列出话术 / 管理知识库"：执行 kb-list。
6. 用户要求"删除话术 / 移除知识库条目"：执行 kb-delete。
7. 用户要求"重建向量索引"：执行 kb-rebuild-index。

## 必做约束

- 知识库操作无需 Chrome，纯本地执行。
- 存储目录：`XHS_KB_PATH` 环境变量 > `config.yaml` 中 `knowledge_base.path` > 默认 `~/.dingclaw/xhs/knowledge_base`。
- 向量检索需安装 `uv sync --extra kb-vector`。
- CLI 输出 JSON 格式。
- `--type` 必填（reply|qa|template），各类型有对应必填字段。

## CLI 参数说明

调用前请根据命令和 type 核对必填参数，避免因参数缺失导致失败。

### kb-add 参数

| 参数              | 必填   | 说明                                                  |
| ----------------- | ------ | ----------------------------------------------------- |
| `--type`          | ✓      | 条目类型：`reply` \| `qa` \| `template`               |
| `--content`       | 见下表 | 回复话术文本（reply/template 必填）                   |
| `--question`      | 见下表 | 问题（qa 必填）                                       |
| `--answer`        | 见下表 | 答案（qa 必填）                                       |
| `--template-type` | 见下表 | 模板场景类型（template 必填，如 感谢/咨询/投诉/种草） |
| `--keywords`      |        | 关键词，逗号分隔，可选                                |
| `--category`      |        | 分类，可选                                            |

**type 与必填参数对照：**

| type       | 必填参数                                          |
| ---------- | ------------------------------------------------- |
| `reply`    | `--type reply`、`--content`                       |
| `qa`       | `--type qa`、`--question`、`--answer`             |
| `template` | `--type template`、`--template-type`、`--content` |

### kb-search 参数

| 参数              | 必填 | 说明                                |
| ----------------- | ---- | ----------------------------------- |
| `--query`         | ✓    | 检索关键词                          |
| `--mode`          |      | 匹配模式：`fuzzy`（默认）\| `exact` |
| `--limit`         |      | 最多返回条数，默认 10               |
| `--type`          |      | 过滤 type：reply \| qa \| template  |
| `--template-type` |      | 过滤 template_type                  |

### kb-search-vector 参数

| 参数              | 必填 | 说明                               |
| ----------------- | ---- | ---------------------------------- |
| `--query`         | ✓    | 检索 query                         |
| `--top-k`         |      | 返回 top-k 条，默认 5              |
| `--type`          |      | 过滤 type：reply \| qa \| template |
| `--template-type` |      | 过滤 template_type                 |

### kb-delete 参数

| 参数   | 必填 | 说明            |
| ------ | ---- | --------------- |
| `--id` | ✓    | 要删除的条目 ID |

### kb-rebuild-index 参数

| 参数              | 必填 | 说明                            |
| ----------------- | ---- | ------------------------------- |
| `--type`          |      | 仅重建指定 type 的条目          |
| `--template-type` |      | 仅重建指定 template_type 的条目 |

### kb-list 参数

无参数。

## 工作流程

### 添加回复话术（reply）

```bash
uv run python scripts/cli.py kb-add \
  --type reply \
  --content "感谢分享，写得很好" \
  --keywords "感谢,分享" \
  --category "通用"
```

### 添加问答式知识（qa）

```bash
uv run python scripts/cli.py kb-add \
  --type qa \
  --question "产品好不好用" \
  --answer "很好用，推荐购买"
```

### 添加特定类型话术（template）

```bash
uv run python scripts/cli.py kb-add \
  --type template \
  --template-type "感谢" \
  --content "感谢支持，期待下次光临"
```

### 检索流程

1. 优先使用关键词检索。
2. 如果关键词检索结果为空，则使用向量检索。

### 关键词检索

```bash
# 模糊匹配（默认）
uv run python scripts/cli.py kb-search --query "感谢" --limit 5

# 精确匹配
uv run python scripts/cli.py kb-search --query "感谢分享" --mode exact --limit 5

# 按 type 过滤
uv run python scripts/cli.py kb-search --query "产品" --type qa

# 按 template_type 过滤
uv run python scripts/cli.py kb-search --query "支持" --template-type "感谢"
```

### 向量相似度检索（RAG）

```bash
uv run python scripts/cli.py kb-search-vector \
  --query "用户问产品好不好用" \
  --top-k 3

# 按 type 过滤
uv run python scripts/cli.py kb-search-vector --query "感谢" --type template --top-k 3
```

### 列出所有条目

```bash
uv run python scripts/cli.py kb-list
```

### 删除条目

```bash
uv run python scripts/cli.py kb-delete --id <条目ID>
```

### 重建向量索引

```bash
uv run python scripts/cli.py kb-rebuild-index
```

## 与 xhs-interact 协作

当用户需要"根据知识库回复这条评论"时：

1. 获取笔记/评论上下文（如笔记标题、评论内容）。
2. 执行 `kb-search-vector --query "笔记标题 + 评论内容" --top-k 3` 检索相关话术。
3. 将检索结果呈现给用户，或由用户确认后选用一条（qa 类型用 answer，reply/template 用 content）。
4. 执行 `reply-comment` 或 `post-comment` 发送选中的话术。

## 失败处理

- **向量检索失败**：提示安装 `uv sync --extra kb-vector`；或先用 `kb-search` 关键词检索。
- **存储目录不可写**：检查 `XHS_KB_PATH` 或 `knowledge_base.path` 配置。
- **知识库为空**：提示用户先执行 `kb-add` 添加话术。
- **必填字段缺失**：根据 type 检查 content、question、answer、template-type 是否提供。
