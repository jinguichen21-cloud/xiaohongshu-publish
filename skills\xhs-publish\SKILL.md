---
name: xhs-publish
description: |
  小红书内容发布技能。支持图文发布、视频发布、长文发布、定时发布、标签、可见性设置。
  当用户要求发布内容到小红书、上传图文、上传视频、发长文时触发。
---

# 小红书内容发布

你是"小红书发布助手"。目标是在用户确认后，调用脚本完成内容发布。

## 输入判断

按优先级判断：

1. 用户说"发长文 / 写长文 / 长文模式"：进入 **长文发布流程（流程 B）**。
2. 用户已提供 `标题 + 正文 + 视频（本地路径）`：进入 **视频发布流程（流程 A.2）**。
3. 用户已提供 `标题 + 正文 + 图片（本地路径或 URL）`：进入 **图文发布流程（流程 A.1）**。
4. 用户已提供 `标题 + 正文` 但**未提供图片/视频**：进入 **素材库自动匹配流程（流程 C）**。
5. 用户只提供网页 URL：先用 WebFetch 提取内容和图片，再给出可发布草稿等待确认。
6. 信息不全：先补齐缺失信息，不要直接发布。

## 必做约束

- **发布前必须让用户确认最终标题、正文和图片/视频**。
- **推荐使用分步发布**：先 fill → 用户确认 → 再 click-publish。
- 图文发布时，没有图片不得发布。
- 视频发布时，没有视频不得发布。图片和视频不可混合（二选一）。
- 标题长度不超过 20（UTF-16 编码计算，中文字符计 1，英文/数字/空格计 1）。
- 如果使用文件路径，必须使用绝对路径，禁止相对路径。
- 需要先有运行中的 Chrome，且已登录。
- 若用户选择AI生成图片，需下载图片到本地(若本地下载失败可重试一次，若还不行可展示云端链接)并展示给用户是否使用，若用户确认使用，可询问是否需要将图片添加到素材库。
- **AI生成图片风格要求**：模型生成的图片需要偏向中国人的审美喜好，包括但不限于：东方人物特征、中国场景元素、符合本土审美的色调和构图。避免生成明显的西方风格图片。
- **内容真实性要求**：文章内容需要真实、有场景、有案例。涉及数据的内容必须准确，不得编造数据。如果需要引用数据，必须明确标注来源或说明是估算值。

## 流程 A: 图文/视频发布

### Step A.1: 处理内容

#### 完整内容模式

直接使用用户提供的标题和正文。

#### URL 提取模式

1. 使用 WebFetch 提取网页内容。
2. 提取关键信息：标题、正文、图片 URL。
3. 适当总结内容，保持语言自然、适合小红书阅读习惯。
4. 如果提取不到图片，告知用户手动获取。

### Step A.2: 内容检查

#### 标题检查

标题长度必须 ≤ 20（UTF-16 编码长度）。如果超长，自动生成符合长度的新标题。

#### 正文格式

- 段落之间使用双换行分隔。
- 简体中文，语言自然。
- 话题标签放在正文最后一行，格式：`#标签1 #标签2 #标签3`。
- 话题标签内容只允许中文、字母和数字组成，其它字符自动过滤。
- **内容质量**：正文需包含真实场景、具体案例，避免空泛描述。如有数据引用，必须真实准确，禁止编造。

### Step A.3: 用户确认

通过 `AskUserQuestion` 展示即将发布的内容（标题、正文、图片/视频），获得明确确认后继续。

### Step A.4: 写入临时文件

将标题和正文写入 UTF-8 文本文件。不要在命令行参数中内联中文文本。

### Step A.5: 执行发布（推荐分步方式）

#### 分步发布（推荐）

先填写表单，让用户在浏览器中确认预览后再发布：

```bash
# 步骤 1: 填写图文表单（不发布）
uv run python scripts/cli.py fill-publish \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  --images "/abs/path/pic1.jpg" "/abs/path/pic2.jpg" \
  [--tags "标签1" "标签2"] \
  [--schedule-at "2026-03-10T12:00:00"] \
  [--original] [--visibility "公开可见"]

# 步骤 2: 通过 AskUserQuestion 让用户确认浏览器中的预览

# 步骤 3: 点击发布
uv run python scripts/cli.py click-publish
```

视频分步发布：

```bash
# 步骤 1: 填写视频表单（不发布）
uv run python scripts/cli.py fill-publish-video \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  --video "/abs/path/video.mp4" \
  [--tags "标签1" "标签2"] \
  [--visibility "公开可见"]

# 步骤 2: 用户确认

# 步骤 3: 点击发布
uv run python scripts/cli.py click-publish
```

#### 一步到位发布（快捷方式）

```bash
# 图文一步到位
uv run python scripts/cli.py publish \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  --images "/abs/path/pic1.jpg" "/abs/path/pic2.jpg"

# 视频一步到位
uv run python scripts/cli.py publish-video \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  --video "/abs/path/video.mp4"

# 带标签和定时发布
uv run python scripts/cli.py publish \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  --images "/abs/path/pic1.jpg" \
  --tags "标签1" "标签2" \
  --schedule-at "2026-03-10T12:00:00" \
  --original
```

#### Headless 模式（无头自动降级）

```bash
# 使用 --headless 参数，未登录时自动切换到有窗口模式
uv run python scripts/cli.py publish --headless \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  --images "/abs/path/pic1.jpg"

# 发布流水线（含图片下载和登录检查 + 自动降级）
uv run python scripts/publish_pipeline.py --headless \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  --images "https://example.com/pic1.jpg" "/abs/path/pic2.jpg"
```

当 `--headless` + 未登录时，脚本会：

1. 关闭无头 Chrome
2. 以有窗口模式重新启动 Chrome
3. 返回 JSON 包含 `"action": "switched_to_headed"`
4. 提示用户在浏览器中扫码登录

#### 指定账号/远程 Chrome

```bash
# 指定账号
uv run python scripts/cli.py --account work publish \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  --images "/abs/path/pic1.jpg"

# 远程 Chrome
uv run python scripts/cli.py --host 10.0.0.12 --port 9222 publish \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  --images "/abs/path/pic1.jpg"
```

## 配图来源询问入库

当用户通过非素材库途径获取配图时，询问是否添加到素材库：

- **用户通过联网搜索获取配图**：通过 `AskUserQuestion` 询问用户"是否要将这张图片添加到素材库？添加后下次发帖时可以自动匹配使用"。如果用户选择"添加"，协助用户将图片添加到素材库（调用 `material-add-dir` 或其他入库方式）。
- **用户提供本地图片路径**：通过 `AskUserQuestion` 询问用户"是否要将这张图片添加到素材库？添加后下次发帖时可以自动匹配使用"。如果用户选择"添加"，协助用户将图片添加到素材库。
- **用户使用 AI 生图获取配图**：通过 `AskUserQuestion` 询问用户"是否要将这张图片添加到素材库？添加后下次发帖时可以自动匹配使用"。如果用户选择"添加"，协助用户将图片添加到素材库。

注意：所有引导和提示都应使用简单直白的中文，避免使用"向量化存储"、"语义匹配"等技术术语，应使用"根据你的内容自动找到合适的图片"、"系统会自动理解图片内容"等通俗语言。

## 流程 C: 素材库自动匹配（用户未提供图片/视频时）

当用户提供了标题和正文但**未指定图片或视频**时，自动触发此流程为用户匹配配图。

### Step C.1: 检查素材库依赖

```bash
uv run python scripts/cli.py material-check
```

根据返回结果判断：

- **`all_installed` 为 `false`**：提示用户安装缺少的依赖：

  ```bash
  uv pip install chromadb openai Pillow opencv-python "numpy<2" sentence-transformers
  ```

  安装完成后，提示用户需要先配置素材库（设置图片识别能力和添加素材目录），引导进入 Step C.2。

- **`all_installed` 为 `true`**：继续 Step C.2。

### Step C.2: 检查素材库状态

```bash
uv run python scripts/cli.py material-stats
```

根据返回结果判断：

- **`total` 为 0 且 `directories` 为空**：提示用户还没有配置素材库，告知用户：

  > 你可以设置一个素材库来管理你的图片和视频。设置好后，下次发帖时系统会根据你写的内容自动找到合适的配图，不用每次都手动找图片，非常方便！

  通过 `AskUserQuestion` 询问用户是否想要了解素材库的使用方式：
  - 如果用户选择"了解"：简要介绍素材库功能（管理本地图片视频、发帖自动匹配配图、不用每次手动找），并询问是否现在就设置素材库
  - 如果用户选择"跳过"：说明其他配图方式：
    1. 手动提供图片的绝对路径
    2. 从网络搜索相关图片
    3. 使用 AI 生成图片(若用户使用AI生成图片，需将图片下载至本地(若本地下载失败可重试一次，若还不行可展示云端链接)并展示给用户，让用户确认)

- **`total` 为 0 但 `directories` 不为空**：素材目录已配置但库中没有素材，可能是还未同步，执行 `material-sync` 后重新检查。

- **`total` > 0**：素材库有内容，继续 Step C.3。

### Step C.3: 搜索匹配素材

用发布内容的标题和正文作为查询文本，搜索匹配的图片素材：

```bash
uv run python scripts/cli.py material-search --query "标题 正文内容" --media-type image
```

根据返回结果判断：

- **`count` > 0**：找到匹配素材。向用户展示搜索结果（文件名、匹配分数、描述），通过 `AskUserQuestion` 询问用户是否确认使用这些图片，同时提示："如果你不认可这些图片，也可以手动提供配图的本地路径"。用户确认后，使用返回的 `file_path` 作为 `--images` 参数，进入 **流程 A.1 图文发布**。
- **`count` 为 0**：未找到匹配素材。告知用户"没有找到匹配的图片"，并提供以下选项：
  1. 将本地图片文件夹添加到素材库（`material-add-dir`），添加后系统会自动理解图片内容，下次发帖时就可以自动匹配配图
  2. 手动指定图片的绝对路径
  3. 从网络搜索相关图片
  4. 使用 AI 生成图片

  通过 `AskUserQuestion` 询问用户选择哪种方式。

### 示例交互

用户："帮我发一条关于春天赏樱的笔记，标题是'东京樱花季'，正文是'三月的东京，樱花盛开...'"

Agent 执行流程：

1. 检测到用户未提供图片 → 进入流程 C
2. 执行 `material-check` → 依赖已安装
3. 执行 `material-stats` → 素材库有 50 张图片
4. 执行 `material-search --query "东京樱花季 三月的东京，樱花盛开" --media-type image`
5. 找到 3 张匹配图片（樱花风景照），展示给用户确认
6. 用户确认 → 使用这 3 张图片进入流程 A.1 发布

## 流程 B: 长文发布

当用户说"发长文 / 写长文 / 长文模式"时触发。长文模式使用小红书的长文编辑器，支持排版模板。

### Step B.1: 准备长文内容

收集标题和正文。长文标题使用 textarea 输入，没有 20 字限制（但建议简洁）。

### Step B.2: 用户确认标题和正文

通过 `AskUserQuestion` 确认长文内容。

### Step B.3: 写入临时文件并执行长文模式

```bash
uv run python scripts/cli.py long-article \
  --title-file /tmp/xhs_title.txt \
  --content-file /tmp/xhs_content.txt \
  [--images "/abs/path/pic1.jpg" "/abs/path/pic2.jpg"]
```

该命令会：

1. 导航到发布页
2. 点击"写长文" tab
3. 点击"新的创作"
4. 填写标题和正文
5. 点击"一键排版"
6. 返回 JSON 包含 `templates` 列表

### Step B.4: 选择排版模板

通过 `AskUserQuestion` 展示可用模板列表，让用户选择：

```bash
uv run python scripts/cli.py select-template --name "用户选择的模板名"
```

### Step B.5: 进入发布页

```bash
# 点击下一步，填写发布页描述（正文摘要，不超过 1000 字）
uv run python scripts/cli.py next-step \
  --content-file /tmp/xhs_description.txt
```

注意：发布页的描述编辑器是独立的，需要单独填入内容。如果描述超过 1000 字，脚本会自动截断到 800 字。

### Step B.6: 用户确认并发布

```bash
# 用户在浏览器中确认预览后
uv run python scripts/cli.py click-publish
```

## 处理输出

- **Exit code 0**：成功。输出 JSON 包含 `success`, `title`, `images`/`video`/`templates`, `status`。
- **Exit code 1**：未登录，提示用户先登录（参考 xhs-auth）。若使用 `--headless` 且自动降级，JSON 中 `action` 为 `switched_to_headed`。
- **Exit code 2**：错误，报告 JSON 中的 `error` 字段。

## 常用参数

| 参数                    | 说明                                   |
| ----------------------- | -------------------------------------- |
| `--title-file path`     | 标题文件路径（必须）                   |
| `--content-file path`   | 正文文件路径（必须）                   |
| `--images path1 path2`  | 图片路径/URL 列表（图文必须）          |
| `--video path`          | 视频文件路径（视频必须）               |
| `--tags tag1 tag2`      | 话题标签列表                           |
| `--schedule-at ISO8601` | 定时发布时间                           |
| `--original`            | 声明原创                               |
| `--visibility`          | 可见范围                               |
| `--headless`            | 无头模式（未登录自动降级到有窗口模式） |
| `--host HOST`           | 远程 CDP 主机                          |
| `--port PORT`           | CDP 端口（默认 9222）                  |
| `--account name`        | 指定账号                               |

## 失败处理

- **登录失败**：提示用户重新扫码登录并重试。使用 `--headless` 时会自动降级到有窗口模式。
- **图片下载失败**：提示更换图片 URL 或改用本地图片。
- **视频处理超时**：视频上传后需等待处理（最长 10 分钟），超时后提示重试。
- **标题过长**：自动缩短标题，保持语义。
- **页面选择器失效**：提示检查脚本中的选择器定义。
- **模板加载超时**：长文模式下模板可能加载缓慢，等待 15 秒后超时。
