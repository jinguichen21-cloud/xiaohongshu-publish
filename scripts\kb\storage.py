"""知识库 JSONL 存储。

条目 schema：id, type, schema_version, created_at, updated_at, keywords, category, meta
类型变体：reply(content), qa(question,answer), template(template_type,content)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import get_kb_path

ENTRIES_FILE = "entries.jsonl"
META_FILE = "meta.json"
SCHEMA_VERSION = 1
VALID_TYPES = ("reply", "qa", "template")


def _ensure_dir(path: Path) -> None:
    """确保目录存在，不存在则创建。"""
    path.mkdir(parents=True, exist_ok=True)


def _entries_path() -> Path:
    """获取 entries.jsonl 的完整路径。"""
    base = get_kb_path()
    _ensure_dir(base)
    return base / ENTRIES_FILE


def _meta_path() -> Path:
    """获取 meta.json 的完整路径。"""
    return get_kb_path() / META_FILE


def _validate_entry(
    entry_type: str,
    content: str | None,
    question: str | None,
    answer: str | None,
    template_type: str | None,
) -> None:
    """按 type 校验必填字段。"""
    if entry_type not in VALID_TYPES:
        raise ValueError(f"type 必须是 {VALID_TYPES} 之一，当前: {entry_type}")
    if entry_type == "reply" and not (content or "").strip():
        raise ValueError("reply 类型必须提供 content")
    if entry_type == "qa":
        if not (question or "").strip():
            raise ValueError("qa 类型必须提供 question")
        if not (answer or "").strip():
            raise ValueError("qa 类型必须提供 answer")
    if entry_type == "template":
        if not (template_type or "").strip():
            raise ValueError("template 类型必须提供 template_type")
        if not (content or "").strip():
            raise ValueError("template 类型必须提供 content")


def add_entry(
    entry_type: str,
    content: str | None = None,
    question: str | None = None,
    answer: str | None = None,
    template_type: str | None = None,
    keywords: list[str] | None = None,
    category: str | None = None,
    meta: dict | None = None,
) -> dict:
    """添加知识库条目。

    Args:
        entry_type: 必填，reply|qa|template。
        content: reply/template 的回复话术。
        question: qa 的问题。
        answer: qa 的答案。
        template_type: template 的场景类型。
        keywords: 可选关键词列表。
        category: 可选分类。
        meta: 可选扩展字段。

    Returns:
        包含 status 和 id 的字典。
    """
    _validate_entry(entry_type, content, question, answer, template_type)

    base = get_kb_path()
    _ensure_dir(base)
    path = _entries_path()

    entry_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "id": entry_id,
        "type": entry_type,
        "schema_version": SCHEMA_VERSION,
        "created_at": now,
        "updated_at": now,
        "keywords": keywords or [],
        "category": category or "",
        "meta": meta or {},
    }

    if entry_type == "reply":
        entry["content"] = (content or "").strip()
    elif entry_type == "qa":
        entry["question"] = (question or "").strip()
        entry["answer"] = (answer or "").strip()
    elif entry_type == "template":
        entry["template_type"] = (template_type or "").strip()
        entry["content"] = (content or "").strip()

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {"status": "ok", "id": entry_id, "entry": entry}


def list_entries() -> list[dict]:
    """列出所有知识库条目。跳过无 type 的非法条目。"""
    path = _entries_path()
    if not path.exists():
        return []

    entries: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if not e.get("type"):
                    continue
                entries.append(e)
            except json.JSONDecodeError:
                continue
    return entries


def delete_entry(entry_id: str) -> dict:
    """按 id 删除条目。

    Returns:
        {"status": "ok"} 或 {"status": "not_found"}
    """
    path = _entries_path()
    if not path.exists():
        return {"status": "not_found"}

    entries = list_entries()
    kept = [e for e in entries if e.get("id") != entry_id]
    if len(kept) == len(entries):
        return {"status": "not_found"}

    with open(path, "w", encoding="utf-8") as f:
        for e in kept:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    return {"status": "ok"}


def get_entry_by_id(entry_id: str) -> dict | None:
    """按 id 获取单条条目。"""
    for e in list_entries():
        if e.get("id") == entry_id:
            return e
    return None
