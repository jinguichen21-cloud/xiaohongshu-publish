"""Prompt loader for analysis report skill.

Fallback chain:
1. Remote API (if PROMPT_API_URL env var is set)
2. Local prompts/analysis_prompt.md

Env vars:
  PROMPT_API_URL   - Base URL of the prompt management API (e.g. https://api.example.com)
  PROMPT_API_KEY   - Bearer token for the prompt API (optional)
"""
from __future__ import annotations

import os
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
DEFAULT_PROMPT_FILE = PROMPTS_DIR / "analysis_prompt.md"
DEFAULT_PROMPT_NAME = "analysis_report"


def _fetch_from_api(prompt_name: str) -> str | None:
    """Fetch prompt content from remote API.

    Returns None if PROMPT_API_URL is not configured or the request fails.
    """
    api_url = os.getenv("PROMPT_API_URL", "").rstrip("/")
    if not api_url:
        return None

    try:
        import requests  # type: ignore[import-untyped]

        api_key = os.getenv("PROMPT_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        resp = requests.get(
            f"{api_url}/prompts/{prompt_name}",
            headers=headers,
            timeout=5,
        )
        if resp.ok:
            data = resp.json()
            # Support both {"content": "..."} and plain text responses
            if isinstance(data, dict):
                return data.get("content") or data.get("prompt")
            if isinstance(data, str):
                return data
    except Exception as exc:  # noqa: BLE001
        print(f"[prompt_loader] 远程 API 获取失败，回退到本地文件：{exc}")

    return None


def load_prompt(
    prompt_name: str = DEFAULT_PROMPT_NAME,
    local_file: Path | None = None,
) -> str:
    """Load prompt with API-first fallback to local file.

    Args:
        prompt_name: Logical name used when calling the remote API.
        local_file: Override the default local prompt file path.

    Returns:
        Prompt text as a string.
    """
    # 1. Try remote API
    remote = _fetch_from_api(prompt_name)
    if remote:
        return remote

    # 2. Fall back to local file
    target = local_file or DEFAULT_PROMPT_FILE
    if not target.exists():
        raise FileNotFoundError(f"本地 prompt 文件不存在：{target}")
    return target.read_text(encoding="utf-8")
