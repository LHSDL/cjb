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
