"""Prepare analysis context from XHSCollection JSON data for the current model to generate a report.

Usage:
    python generate_report.py <input.json> [--output out.md]

Outputs a JSON payload (system_prompt + user_message + suggested_output_path) to stdout.
The current model reads this and writes the final Markdown report directly.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Allow importing prompt_loader from the same scripts/ directory
sys.path.insert(0, str(Path(__file__).parent))
from prompt_loader import load_prompt

OUTPUT_DIR = Path.home() / ".dingclaw" / "store-insight-report"


def _parse_number(value: str | int | float) -> float:
    """Convert XHS numeric string (may contain '万') to float."""
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "")
    if s.endswith("万"):
        try:
            return float(s[:-1]) * 10_000
        except ValueError:
            return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _convert_table_format(data: dict) -> dict:
    """将 store-ai-table-writer 输出的表格格式转换为 XHSCollection 格式。
    
    检测特征：存在 "rows" 字段且不存在 "items" 字段。
    """
    if "rows" in data and "items" not in data:
        rows = data.get("rows", [])
        # 从第一行提取元数据（采集关键词、数据来源）
        first_row = rows[0] if rows else {}
        
        items = []
        for row in rows:
            items.append({
                "id": row.get("笔记ID", ""),
                "title": row.get("标题", ""),
                "author": {
                    "userId": row.get("作者ID", ""),
                    "nickname": row.get("作者", "")
                },
                "type": "video" if row.get("类型") == "视频" else "normal",
                "interact": {
                    "likedCount": str(row.get("点赞数", 0)),
                    "collectedCount": str(row.get("收藏数", 0)),
                    "commentCount": str(row.get("评论数", 0)),
                    "sharedCount": str(row.get("分享数", 0))
                },
                "publishTime": row.get("发布时间", 0),
                "ipLocation": row.get("发布地", ""),
                "imageCount": row.get("图片数", 0),
                "desc": row.get("正文摘要", ""),
                "url": row.get("原链接", ""),
                "coverUrl": row.get("封面图", "")
            })
        return {
            "source": first_row.get("数据来源", data.get("数据来源", "unknown")),
            "query": first_row.get("采集关键词", data.get("采集关键词", "")),
            "enriched": True,
            "collectedAt": data.get("written_at", ""),
            "items": items
        }
    return data


def _build_user_message(collection: dict) -> str:
    """Serialize collection data into the user message sent to OpenAI."""
    payload = {
        "source": collection.get("source", "unknown"),
        "query": collection.get("query", ""),
        "enriched": collection.get("enriched", False),
        # to_dict() outputs camelCase "collectedAt"; also handle snake_case
        "collected_at": collection.get("collectedAt") or collection.get("collected_at", ""),
        "total_items": len(collection.get("items", [])),
        "items": collection.get("items", []),
    }
    data_str = json.dumps(payload, ensure_ascii=False, indent=2)
    return f"请基于以下 XHSCollection JSON 数据生成分析报告：\n\n```json\n{data_str}\n```"



def main() -> None:
    parser = argparse.ArgumentParser(
        description="准备分析上下文，输出给当前模型直接生成分析报告"
    )
    parser.add_argument("input", help="XHSCollection JSON 文件路径")
    parser.add_argument(
        "--output",
        help="建议的报告输出文件路径（默认自动生成到 output/ 目录）",
    )
    args = parser.parse_args()

    # --- 参数校验 ---
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误：输入文件不存在：{input_path}", file=sys.stderr)
        sys.exit(1)

    # --- 读取数据 ---
    with open(input_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    # --- 格式转换（支持 store-ai-table-writer 输出的表格格式）---
    collection = _convert_table_format(raw_data)

    items = collection.get("items", [])
    if not items:
        print("警告：items 为空", file=sys.stderr)
    else:
        print(f"准备分析上下文：{len(items)} 条笔记数据…", file=sys.stderr)

    # --- 输出上下文供当前模型直接分析 ---
    system_prompt = load_prompt()
    user_message = _build_user_message(collection)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = (collection.get("query") or collection.get("source", "unknown")).replace("/", "_").replace(" ", "_")[:30]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    suggested_output = args.output or str(OUTPUT_DIR / f"report_{label}_{timestamp}.md")

    print(json.dumps({
        "meta": {
            "suggested_output_path": suggested_output,
            "total_items": len(items),
            "query": collection.get("query", ""),
            "source": collection.get("source", "unknown"),
        },
        "system_prompt": system_prompt,
        "user_message": user_message,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
