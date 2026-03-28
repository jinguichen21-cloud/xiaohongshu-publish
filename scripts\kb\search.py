"""知识库关键词检索。

支持精确匹配（exact）和模糊匹配（fuzzy）。
reply/template 匹配 content+keywords；qa 匹配 question+answer。
支持 type、template_type 过滤。
"""

from __future__ import annotations

from .storage import list_entries


def _searchable_text(entry: dict) -> str:
    """根据 type 获取可检索文本。"""
    t = entry.get("type", "")
    keywords = " ".join(entry.get("keywords") or [])
    if t == "qa":
        q = entry.get("question") or ""
        a = entry.get("answer") or ""
        return f"{q} {a} {keywords}".strip()
    if t == "template":
        tt = entry.get("template_type") or ""
        c = entry.get("content") or ""
        return f"{tt} {c} {keywords}".strip()
    c = entry.get("content") or ""
    return f"{c} {keywords}".strip()


def _matches_filter(
    entry: dict,
    entry_type: str | None,
    template_type: str | None,
) -> bool:
    """检查条目是否满足 type、template_type 过滤。"""
    if entry_type and entry.get("type") != entry_type:
        return False
    if template_type and entry.get("template_type") != template_type:
        return False
    return True


def search(
    query: str,
    mode: str = "fuzzy",
    limit: int = 10,
    entry_type: str | None = None,
    template_type: str | None = None,
) -> dict:
    """按 query 检索知识库。

    Args:
        query: 检索关键词。
        mode: exact（精确）或 fuzzy（模糊）。
        limit: 最多返回条数。
        entry_type: 可选，过滤 type。
        template_type: 可选，过滤 template_type。

    Returns:
        {"results": [...], "count": N}
    """
    entries = list_entries()
    if not query.strip():
        return {"results": [], "count": 0}

    query_lower = query.strip().lower()
    matched: list[tuple[dict, float]] = []

    for e in entries:
        if not _matches_filter(e, entry_type, template_type):
            continue
        searchable = _searchable_text(e)
        searchable_lower = searchable.lower()

        if mode == "exact":
            if query_lower in searchable_lower:
                score = 1.0
                matched.append((e, score))
        else:
            if query_lower in searchable_lower:
                idx = searchable_lower.find(query_lower)
                score = 1.0 - (idx * 0.001)
                matched.append((e, score))

    matched.sort(key=lambda x: -x[1])
    results = [e for e, _ in matched[:limit]]
    return {"results": results, "count": len(results)}
