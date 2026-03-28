"""知识库路径配置。

优先级：XHS_KB_PATH 环境变量 > config.yaml > 默认 ~/.dingclaw/xhs/knowledge_base
"""

from __future__ import annotations

import os
from pathlib import Path


def _load_config_path() -> str | None:
    """从配置文件读取 knowledge_base.path。"""
    candidates = [
        Path.home() / ".dingclaw" / "xhs" / "config.yaml",
        Path.cwd() / "config.yaml",
        Path(__file__).resolve().parent.parent.parent / "config.yaml",
    ]
    try:
        import yaml
    except ImportError:
        return None

    for p in candidates:
        if p.exists():
            try:
                with open(p, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict):
                    kb = data.get("knowledge_base")
                    if isinstance(kb, dict) and "path" in kb:
                        return str(kb["path"])
                    if isinstance(kb, str):
                        return kb
            except Exception:
                pass
    return None


def get_kb_path() -> Path:
    """获取知识库根目录（绝对路径）。

    优先级：
    1. 环境变量 XHS_KB_PATH
    2. config.yaml 中的 knowledge_base.path
    3. 默认 ~/.dingclaw/xhs/knowledge_base
    """
    env_path = os.environ.get("XHS_KB_PATH")
    if env_path:
        return Path(env_path).resolve()

    config_path = _load_config_path()
    if config_path:
        return Path(config_path).resolve()

    return (Path.home() / ".dingclaw" / "xhs" / "knowledge_base").resolve()
