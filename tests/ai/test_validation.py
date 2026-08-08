import pytest

from meeting_assistant.ai.models import RawAnalysis
from meeting_assistant.ai.validation import AIOutputValidationError, validate_raw_analysis


def analysis_with_action(**changes):
    action = {
        "content": "完成接口联调",
        "owner": "王芳",
        "due_date_expression": "下周五",
        "sources": [
            {"line_id": "L001", "quote": "王芳负责接口联调，下周五前完成"}
        ],
    }
    action.update(changes)
    return RawAnalysis.model_validate(
        {
            "summary": "会议安排了接口联调。",
            "decisions": [],
            "action_items": [action],
            "security_warnings": [],
        }
    )


def test_accepts_exact_source_owner_and_date_expression():
    raw = analysis_with_action()
    validate_raw_analysis(raw, {"L001": "王芳负责接口联调，下周五前完成。"})


def test_rejects_unknown_source_line():
    raw = analysis_with_action(
        sources=[{"line_id": "L999", "quote": "王芳负责接口联调"}]
    )

    with pytest.raises(AIOutputValidationError, match="L999 不存在"):
        validate_raw_analysis(raw, {"L001": "原文"})


def test_rejects_quote_not_present_in_source_line():
    raw = analysis_with_action(
        sources=[{"line_id": "L001", "quote": "李明负责接口联调"}]
    )

    with pytest.raises(AIOutputValidationError, match="引用不是原文的连续子串"):
        validate_raw_analysis(raw, {"L001": "王芳负责接口联调。"})


def test_rejects_invented_owner_and_date_expression():
    raw = analysis_with_action(owner="李明")
    with pytest.raises(AIOutputValidationError, match="负责人.*没有原文依据"):
        validate_raw_analysis(raw, {"L001": "王芳负责接口联调，下周五前完成。"})

    raw = analysis_with_action(due_date_expression="下周一")
    with pytest.raises(AIOutputValidationError, match="日期表达.*没有原文依据"):
        validate_raw_analysis(raw, {"L001": "王芳负责接口联调，下周五前完成。"})


def test_decision_source_is_validated_too():
    raw = RawAnalysis.model_validate(
        {
            "summary": "会议决定采用方案A。",
            "decisions": [
                {
                    "content": "采用方案A",
                    "sources": [{"line_id": "L001", "quote": "决定采用方案B"}],
                }
            ],
            "action_items": [],
            "security_warnings": [],
        }
    )

    with pytest.raises(AIOutputValidationError, match="引用不是原文的连续子串"):
        validate_raw_analysis(raw, {"L001": "会议决定采用方案A。"})

