import json

import pytest
from pydantic import ValidationError

from meeting_assistant.ai.models import RawAnalysis


def valid_payload():
    return {
        "summary": "会议明确了接口联调安排。",
        "decisions": [
            {
                "content": "采用方案A",
                "sources": [{"line_id": "L002", "quote": "决定采用方案A"}],
            }
        ],
        "action_items": [
            {
                "content": "完成接口联调",
                "owner": "王芳",
                "due_date_expression": "下周五",
                "sources": [
                    {
                        "line_id": "L001",
                        "quote": "王芳负责接口联调，下周五前完成",
                    }
                ],
            }
        ],
        "security_warnings": [],
    }


def test_raw_analysis_accepts_expected_json_contract():
    analysis = RawAnalysis.model_validate_json(json.dumps(valid_payload()))

    assert analysis.action_items[0].owner == "王芳"
    assert analysis.action_items[0].due_date_expression == "下周五"
    assert analysis.decisions[0].sources[0].line_id == "L002"


def test_raw_analysis_rejects_extra_fields():
    payload = valid_payload()
    payload["unexpected"] = "不能静默接收"

    with pytest.raises(ValidationError):
        RawAnalysis.model_validate(payload)


def test_raw_analysis_rejects_more_than_twenty_actions():
    payload = valid_payload()
    payload["action_items"] = payload["action_items"] * 21

    with pytest.raises(ValidationError):
        RawAnalysis.model_validate(payload)


def test_raw_analysis_rejects_overlong_summary():
    payload = valid_payload()
    payload["summary"] = "会" * 301

    with pytest.raises(ValidationError):
        RawAnalysis.model_validate(payload)

