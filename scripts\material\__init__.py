"""素材管理模块。

提供本地图片/视频素材的向量化存储、语义搜索、同步管理能力。
素材通过大模型生成描述 → OpenAI Embedding API 向量化 → Chroma 向量数据库存储。
"""

from .config import get_material_config, update_material_config
from .search import search_materials
from .sync import sync_materials

__all__ = [
    "get_material_config",
    "update_material_config",
    "search_materials",
    "sync_materials",
]
