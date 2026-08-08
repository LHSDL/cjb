"""以会议日期为唯一基准解析明确日期表达。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta


WEEKDAYS = {
    "一": 0,
    "二": 1,
    "三": 2,
    "四": 3,
    "五": 4,
    "六": 5,
    "日": 6,
    "天": 6,
}


@dataclass(frozen=True, slots=True)
class ResolvedDate:
    value: str | None
    needs_confirmation: bool
    warning: str | None


def _confirmed(value: date) -> ResolvedDate:
    return ResolvedDate(value=value.isoformat(), needs_confirmation=False, warning=None)


def _unconfirmed(reason: str) -> ResolvedDate:
    return ResolvedDate(value=None, needs_confirmation=True, warning=reason)


def _safe_date(year: int, month: int, day: int) -> ResolvedDate:
    try:
        return _confirmed(date(year, month, day))
    except ValueError:
        return _unconfirmed("日期表达无效，需要人工确认")


def resolve_date(expression: str | None, meeting_date: str) -> ResolvedDate:
    if expression is None or not expression.strip():
        return _unconfirmed("会议原文未明确截止日期")

    base = date.fromisoformat(meeting_date)
    normalized = expression.strip()
    normalized = re.sub(r"(之前|以前|前完成|前)$", "", normalized).strip()

    relative_days = {"今天": 0, "明天": 1, "后天": 2}
    if normalized in relative_days:
        return _confirmed(base + timedelta(days=relative_days[normalized]))

    week_match = re.fullmatch(r"(本周|下周|下下周)([一二三四五六日天])", normalized)
    if week_match:
        week_offset = {"本周": 0, "下周": 1, "下下周": 2}[week_match.group(1)]
        monday = base - timedelta(days=base.weekday())
        target = monday + timedelta(
            weeks=week_offset, days=WEEKDAYS[week_match.group(2)]
        )
        return _confirmed(target)

    try:
        return _confirmed(date.fromisoformat(normalized))
    except ValueError:
        pass

    chinese_full = re.fullmatch(r"(\d{4})年(\d{1,2})月(\d{1,2})日?", normalized)
    if chinese_full:
        return _safe_date(*map(int, chinese_full.groups()))

    month_day = re.fullmatch(r"(\d{1,2})月(\d{1,2})日?", normalized)
    if month_day:
        month, day = map(int, month_day.groups())
        return _safe_date(base.year, month, day)

    return _unconfirmed(f"无法唯一解析日期表达“{expression.strip()}”")

