"""输入验证器。"""

from datetime import date


class ValidationError(ValueError):
    """用户输入不满足业务规则。"""


def required_text(value: str, *, label: str, maximum: int) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValidationError(f"{label}不能为空")
    if len(normalized) > maximum:
        raise ValidationError(f"{label}不能超过 {maximum} 个字符")
    return normalized


def absolute_date(value: str, *, label: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValidationError(f"{label}必须使用 YYYY-MM-DD 格式") from error
    normalized = parsed.isoformat()
    if normalized != value:
        raise ValidationError(f"{label}必须使用 YYYY-MM-DD 格式")
    return normalized


def optional_text(value: str | None, *, label: str, maximum: int) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip()
    if len(normalized) > maximum:
        raise ValidationError(f"{label}不能超过 {maximum} 个字符")
    return normalized


def optional_absolute_date(value: str | None, *, label: str) -> str | None:
    if value is None or not value.strip():
        return None
    return absolute_date(value.strip(), label=label)


def action_status(value: str | None) -> str | None:
    if value is None:
        return None
    if value not in {"pending", "completed"}:
        raise ValidationError("状态只能是 pending 或 completed")
    return value
