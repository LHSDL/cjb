"""应用配置。"""

from __future__ import annotations

import os
from pathlib import Path


def default_database_path() -> Path:
    """返回数据库路径，允许通过环境变量覆盖。"""
    configured = os.getenv("MEETING_ASSISTANT_DB")
    if configured:
        return Path(configured).expanduser()
    return Path("data") / "meeting_assistant.db"

