"""检测会议原文中的提示注入表达。"""

from __future__ import annotations

import re
from dataclasses import dataclass


INJECTION_PATTERNS = (
    re.compile(r"忽略.{0,12}(规则|指令|要求)", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?(previous|prior).{0,20}instructions?", re.IGNORECASE),
    re.compile(r"(system|developer)\s*prompt", re.IGNORECASE),
    re.compile(r"不要遵守.{0,20}(规则|要求|指令)", re.IGNORECASE),
    re.compile(r"改变.{0,8}输出格式", re.IGNORECASE),
    re.compile(r"为每位.{0,20}生成\s*\d+\s*条", re.IGNORECASE),
)


@dataclass(frozen=True, slots=True)
class SecurityWarning:
    line_id: str
    reason: str


def is_injection_text(text: str) -> bool:
    return any(pattern.search(text) for pattern in INJECTION_PATTERNS)


def detect_injection(lines: dict[str, str]) -> list[SecurityWarning]:
    return [
        SecurityWarning(
            line_id=line_id,
            reason="检测到疑似提示注入文本，已作为不可信数据处理",
        )
        for line_id, text in lines.items()
        if is_injection_text(text)
    ]

