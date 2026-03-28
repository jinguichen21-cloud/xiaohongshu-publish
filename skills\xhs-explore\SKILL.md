---
name: xhs-explore
description: |
  小红书内容发现与分析技能。搜索笔记、浏览首页、查看详情、获取用户资料。
  当用户要求搜索小红书、查看笔记详情、浏览首页、查看用户主页、查看我的帖子/点赞数/评论时触发。
---

# 小红书内容发现

你是"小红书内容发现助手"。帮助用户搜索、浏览和分析小红书内容。

## 输入判断

按优先级判断：

1. 用户要求"搜索笔记 / 找内容 / 搜关键词"：执行搜索流程。
2. 用户要求"查看笔记详情 / 看这篇帖子"：执行详情获取流程。
3. 用户要求"首页推荐 / 浏览首页"：执行首页 Feed 获取。
4. 用户要求"查看用户主页 / 看看这个博主"：执行用户资料获取。
5. 用户要求查看「我的」相关信息（如我的帖子、我的帖子的点赞数、我的帖子的评论信息等）：执行「获取我的相关信息」流程（先 my-profile，再按需获取详情）。

## 必做约束

- 所有操作需要已登录的 Chrome 浏览器。
- `feed_id` 和 `xsec_token` 必须配对使用，从搜索结果或首页 Feed 中获取。
- **搜索 + 详情**：用户要求搜索并查看笔记详情时，必须执行 `get-feed-detail` 获取正文、发布时间等。**禁止**因担心触发扫码验证而默认跳过；应先尝试，遇验证再按失败处理流程引导用户。
- 结果应结构化呈现，突出关键字段。
- CLI 输出为 JSON 格式。
- **当所有需要浏览器的操作完成后**，执行 `cli.py close-browser`。不要在中间步骤（如 search 后紧接着 get-feed-detail）关闭；也无需等待后续非浏览器操作（如分析报告生成）完成后再关闭。

## 工作流程

### 首页 Feed 列表

获取小红书首页推荐内容：

```bash
uv run python scripts/cli.py list-feeds
```

输出 JSON 包含 `feeds` 数组和 `count`，每个 feed 包含 `id`、`xsec_token`、`note_card`（标题、封面、互动数据等）。

### 搜索笔记

```bash
# 基础搜索
uv run python scripts/cli.py search-feeds --keyword "春招"

# 带筛选搜索
uv run python scripts/cli.py search-feeds \
  --keyword "春招" \
  --sort-by 最新 \
  --note-type 图文

# 完整筛选
uv run python scripts/cli.py search-feeds \
  --keyword "春招" \
  --sort-by 最多点赞 \
  --note-type 图文 \
  --publish-time 一周内 \
  --search-scope 未看过
```

#### 搜索筛选参数

| 参数             | 可选值                                   |
| ---------------- | ---------------------------------------- |
| `--sort-by`      | 综合、最新、最多点赞、最多评论、最多收藏 |
| `--note-type`    | 不限、视频、图文                         |
| `--publish-time` | 不限、一天内、一周内、半年内             |
| `--search-scope` | 不限、已看过、未看过、已关注             |
| `--location`     | 不限、同城、附近                         |

#### 搜索结果字段

输出 JSON 包含：

- `feeds`：笔记列表，每项包含 `id`、`xsec_token`、`note_card`（标题、封面、用户信息、互动数据）
- `count`：结果数量

### 获取笔记详情

从搜索结果或首页 Feed 中取 `id` 和 `xsec_token`，获取完整内容：

```bash
# 基础详情
uv run python scripts/cli.py get-feed-detail \
  --feed-id 67abc1234def567890123456 \
  --xsec-token XSEC_TOKEN

# 加载全部评论
uv run python scripts/cli.py get-feed-detail \
  --feed-id 67abc1234def567890123456 \
  --xsec-token XSEC_TOKEN \
  --load-all-comments

# 加载全部评论（展开子评论）
uv run python scripts/cli.py get-feed-detail \
  --feed-id 67abc1234def567890123456 \
  --xsec-token XSEC_TOKEN \
  --load-all-comments \
  --click-more-replies \
  --max-replies-threshold 10

# 限制评论数量
uv run python scripts/cli.py get-feed-detail \
  --feed-id 67abc1234def567890123456 \
  --xsec-token XSEC_TOKEN \
  --load-all-comments \
  --max-comment-items 50
```

输出包含：笔记完整内容、图片列表、互动数据、评论列表。数据会写入本地数据库；若已配置钉钉多维表，会同步写入 AI 表格。

#### ⚠️ get-feed-detail 使用限制与推荐流程

**重要：** `get-feed-detail` 可能触发小红书扫码验证（反爬机制）。**禁止**因担心失败而默认跳过详情获取。正确做法：

1. **先尝试**：用户要求搜索并查看详情时，必须执行 `search-feeds` 后**主动调用** `get-feed-detail` 获取详情。
2. **先测单篇**：批量场景下，先用第 1 篇笔记调用 `get-feed-detail` 测试是否可行。
3. **如遇验证**：若报错 `笔记不可访问：触发了小红书验证，需要在浏览器中扫码完成验证后重试`，则：
   - 明确告知用户：「触发了小红书扫码验证，需要您在 Chrome 中手动打开笔记页面完成扫码。」
   - 提供笔记 URL（可从 `https://www.xiaohongshu.com/explore/{feed_id}` 构建），让用户在浏览器中打开并完成验证。
   - 用户确认完成验证后，再重试 `get-feed-detail` 或继续批量获取。
4. **降级方案**：若用户无法完成验证或选择跳过，则使用 `search-feeds` 的基础互动数据（标题、作者、点赞数等）生成报告，并注明 `enriched=false`，说明未包含正文/发布时间等维度。

### 获取用户主页

```bash
uv run python scripts/cli.py user-profile \
  --user-id USER_ID \
  --xsec-token XSEC_TOKEN
```

输出包含：用户基本信息、粉丝/关注数、笔记列表。

### 收尾：关闭浏览器

所有需要浏览器的探索操作完成后，关闭浏览器 tab（无需等待后续分析、报告等非浏览器步骤）：

```bash
uv run  scripts/cli.py close-browser
```

### 获取我的相关信息

当用户询问「我的帖子」「我的帖子的点赞数」「我的帖子的评论信息」等时，分两步执行：

1. **第一步**：执行 `my-profile` 获取最新用户信息和笔记列表。
2. **第二步**：根据用户具体需求，从第一步返回的笔记列表中取 `id` 和 `xsec_token`，调用 `get-feed-detail` 获取点赞数、评论等详情。

```bash
# 第一步：获取当前账号主页及笔记列表（无需参数）
uv run  scripts/cli.py my-profile
```

输出 JSON 包含用户基本信息和 `notes` 数组，每项含 `id`、`xsec_token`、`note_card` 等。

```bash
# 第二步：获取某篇笔记的点赞数、评论等详情（从第一步结果中取 id 和 xsec_token）
uv run  scripts/cli.py get-feed-detail \
  --feed-id NOTE_ID \
  --xsec-token XSEC_TOKEN \
  --load-all-comments
```

若用户仅需笔记列表，完成第一步即可；若需点赞数、评论等互动数据，再执行第二步。

## 结果呈现

搜索结果应按以下格式呈现给用户：

1. **笔记列表**：每条笔记展示标题、作者、互动数据。
2. **详情内容**：完整的笔记正文、图片、评论。
3. **用户资料**：基本信息 + 代表作列表。
4. **数据表格**：使用 markdown 表格展示关键指标。

## 失败处理

- **未登录**：提示用户先执行登录（参考 xhs-auth）。
- **搜索无结果**：建议更换关键词或调整筛选条件。
- **笔记不可访问**：分两种情况处理：
  - **扫码验证**：报错含「触发了小红书验证」→ 按上文「get-feed-detail 使用限制」流程，引导用户在浏览器中完成验证后重试。
  - **其他**：私密笔记、已删除、内容不存在等 → 提示用户该笔记无法访问。
- **用户主页不可访问**：用户可能已注销或设置隐私。
- **浏览器操作完成后**：务必调用 `cli.py close-browser`，否则 tab 会保持打开。不要在 search → get-feed-detail 之间关闭；也无需等分析报告等非浏览器步骤完成后再关。
