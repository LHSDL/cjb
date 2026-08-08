import pytest

from meeting_assistant.ai.date_resolver import resolve_date


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("今天", "2026-08-07"),
        ("明天", "2026-08-08"),
        ("后天", "2026-08-09"),
        ("本周一", "2026-08-03"),
        ("下周五", "2026-08-14"),
        ("下下周日", "2026-08-23"),
        ("2026-08-20", "2026-08-20"),
        ("2026年8月20日", "2026-08-20"),
        ("8月20日", "2026-08-20"),
    ],
)
def test_resolves_supported_dates_from_meeting_date(expression, expected):
    result = resolve_date(expression, "2026-08-07")

    assert result.value == expected
    assert result.needs_confirmation is False
    assert result.warning is None


@pytest.mark.parametrize("expression", [None, "尽快", "近期", "月底前", "2026-02-30"])
def test_ambiguous_or_invalid_dates_need_confirmation(expression):
    result = resolve_date(expression, "2026-08-07")

    assert result.value is None
    assert result.needs_confirmation is True
    assert result.warning

