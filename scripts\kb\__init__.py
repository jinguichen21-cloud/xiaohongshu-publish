"""回复评论知识库模块。

提供本地知识库的存储、关键词检索、向量检索能力。
"""

from .config import get_kb_path
from .storage import add_entry, delete_entry, list_entries

__all__ = ["get_kb_path", "add_entry", "list_entries", "delete_entry"]
