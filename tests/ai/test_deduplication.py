from meeting_assistant.ai.deduplication import merge_duplicate_actions
from meeting_assistant.ai.models import ActionSuggestion, SourceReference


def suggestion(
    content,
    *,
    owner="王芳",
    expression="下周五",
    due_date="2026-08-14",
    line="L001",
    quote="王芳负责接口联调，下周五前完成",
):
    return ActionSuggestion(
        content=content,
        owner=owner,
        owner_needs_confirmation=owner is None,
        due_date_expression=expression,
        due_date=due_date,
        due_date_needs_confirmation=due_date is None,
        sources=[SourceReference(line_id=line, quote=quote)],
        warnings=[],
    )


def test_merges_obvious_duplicate_tasks_and_preserves_sources():
    items = [
        suggestion("完成接口联调"),
        suggestion(
            "接口联调",
            line="L002",
            quote="接口联调由王芳推进，需要在下周五前完成",
        ),
    ]

    merged = merge_duplicate_actions(items)

    assert len(merged) == 1
    assert merged[0].content == "完成接口联调"
    assert {source.line_id for source in merged[0].sources} == {"L001", "L002"}


def test_conflicting_owner_or_date_is_marked_for_confirmation():
    items = [
        suggestion("完成接口联调"),
        suggestion(
            "接口联调",
            owner="李明",
            expression="下周一",
            due_date="2026-08-10",
            line="L002",
            quote="李明负责接口联调，下周一完成",
        ),
    ]

    merged = merge_duplicate_actions(items)

    assert merged[0].owner is None
    assert merged[0].owner_needs_confirmation is True
    assert merged[0].due_date is None
    assert merged[0].due_date_needs_confirmation is True
    assert len(merged[0].warnings) == 2


def test_does_not_merge_different_tasks():
    merged = merge_duplicate_actions(
        [suggestion("完成接口联调"), suggestion("整理测试报告")]
    )

    assert len(merged) == 2
