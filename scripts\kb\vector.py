"""知识库向量检索（RAG）。

使用 ChromaDB 持久化向量，支持内置嵌入。
按 type 构建索引文本；支持 type、template_type 过滤。
"""

from __future__ import annotations

from pathlib import Path

from .config import get_kb_path
from .storage import list_entries

COLLECTION_NAME = "xhs_reply_kb"
CHROMA_DIR = "chroma"


def _get_chroma_path() -> Path:
    """ChromaDB 持久化目录。"""
    return get_kb_path() / CHROMA_DIR


def _text_for_index(entry: dict) -> str:
    """按 type 构建向量索引文本。"""
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


def _get_client():
    """获取 ChromaDB 持久化客户端（延迟导入）。"""
    import chromadb

    path = str(_get_chroma_path())
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=path)


def _get_collection():
    """获取或创建 collection。"""
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_to_vector_store(entry: dict) -> None:
    """将条目添加到向量存储。"""
    text = _text_for_index(entry)
    if not text.strip():
        return
    coll = _get_collection()
    coll.upsert(
        ids=[entry["id"]],
        documents=[text],
        metadatas=[{}],
    )


def remove_from_vector_store(entry_id: str) -> None:
    """从向量存储删除条目。"""
    try:
        coll = _get_collection()
        coll.delete(ids=[entry_id])
    except Exception:
        pass


def search_vector(
    query: str,
    top_k: int = 5,
    entry_type: str | None = None,
    template_type: str | None = None,
) -> dict:
    """向量相似度检索。

    Returns:
        {"results": [{"id": ..., "content"/"answer": ..., "score": ...}, ...], "count": N}
    """
    entries = list_entries()
    filtered = [e for e in entries if _matches_filter(e, entry_type, template_type)]
    if not filtered:
        return {"results": [], "count": 0}

    try:
        coll = _get_collection()
    except Exception as e:
        return {
            "results": [],
            "count": 0,
            "error": f"向量库初始化失败（请安装 chromadb: uv sync --extra kb-vector）: {e}",
        }

    try:
        out = coll.query(query_texts=[query], n_results=min(top_k, len(filtered)))
    except Exception as e:
        return {"results": [], "count": 0, "error": str(e)}

    ids = out.get("ids", [[]])[0] or []
    distances = out.get("distances", [[]])[0] or []

    entry_map = {e["id"]: e for e in filtered}
    results = []
    for i, eid in enumerate(ids):
        if eid not in entry_map:
            continue
        e = entry_map[eid]
        dist = distances[i] if i < len(distances) else 0
        score = 1.0 - dist if dist <= 1 else max(0, 1.0 - dist)
        results.append(
            {
                **e,
                "score": round(score, 4),
            }
        )

    return {"results": results, "count": len(results)}


def rebuild_index(
    entry_type: str | None = None,
    template_type: str | None = None,
) -> dict:
    """全量重建向量索引。支持 type、template_type 过滤（仅重建匹配条目）。"""
    entries = list_entries()
    filtered = [e for e in entries if _matches_filter(e, entry_type, template_type)]
    if not filtered:
        return {"status": "ok", "message": "无匹配条目，无需重建"}

    try:
        client = _get_client()
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        coll = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        ids = [e["id"] for e in filtered]
        documents = [_text_for_index(e) for e in filtered]
        metadatas = [{}] * len(filtered)
        coll.add(ids=ids, documents=documents, metadatas=metadatas)
        return {"status": "ok", "message": f"已重建 {len(filtered)} 条索引"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
