import json

from typer.testing import CliRunner

import meeting_assistant.cli as cli
from meeting_assistant.ai.client import AIAnalysisError
from meeting_assistant.ai.models import (
    AIAnalysis,
    ActionSuggestion,
    RawDecision,
    SourceReference,
)
from meeting_assistant.db import Database
from meeting_assistant.repositories import ActionItemRepository


runner = CliRunner()


class StubAnalyzer:
    def __init__(self, result):
        self.result = result
        self.meetings = []

    def analyze(self, meeting):
        self.meetings.append(meeting)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def analysis_result():
    source = SourceReference(
        line_id="L001", quote="王芳负责接口联调，下周五前完成"
    )
    return AIAnalysis(
        model="qwen-test",
        summary="会议明确了接口联调安排。",
        decisions=[
            RawDecision(content="采用方案A", sources=[source.model_copy()])
        ],
        action_items=[
            ActionSuggestion(
                content="完成接口联调",
                owner="王芳",
                owner_needs_confirmation=False,
                due_date_expression="下周五",
                due_date="2026-08-14",
                due_date_needs_confirmation=False,
                sources=[source],
                warnings=[],
            )
        ],
        security_warnings=["L003：检测到疑似提示注入文本"],
    )


def prepare_database(db_path):
    environment = {"MEETING_ASSISTANT_DB": str(db_path)}
    seeded = runner.invoke(cli.app, ["seed-demo"], env=environment)
    assert seeded.exit_code == 0
    return environment


def test_root_help_lists_ai_command_group():
    result = runner.invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    assert "ai" in result.stdout


def test_ai_check_config_never_prints_api_key(monkeypatch):
    secret = "private-test-value"
    environment = {
        "DASHSCOPE_API_KEY": secret,
        "DASHSCOPE_BASE_URL": "https://dashscope.example/v1",
        "DASHSCOPE_MODEL": "qwen-test",
    }

    result = runner.invoke(cli.app, ["ai", "check-config"], env=environment)

    assert result.exit_code == 0
    assert "qwen-test" in result.stdout
    assert "配置完整" in result.stdout
    assert secret not in result.stdout


def test_ai_analyze_json_is_parseable_and_does_not_write_actions(
    db_path, monkeypatch
):
    environment = prepare_database(db_path)
    before = len(ActionItemRepository(Database(db_path)).list())
    analyzer = StubAnalyzer(analysis_result())
    monkeypatch.setattr(cli, "_ai_analyzer", lambda: analyzer)

    result = runner.invoke(
        cli.app, ["ai", "analyze", "1", "--json"], env=environment
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["action_items"][0]["due_date"] == "2026-08-14"
    assert analyzer.meetings[0].meeting_date == "2026-08-07"
    assert len(ActionItemRepository(Database(db_path)).list()) == before


def test_ai_analyze_default_output_shows_summary_actions_sources_and_warning(
    db_path, monkeypatch
):
    environment = prepare_database(db_path)
    monkeypatch.setattr(
        cli, "_ai_analyzer", lambda: StubAnalyzer(analysis_result())
    )

    result = runner.invoke(cli.app, ["ai", "analyze", "1"], env=environment)

    assert result.exit_code == 0
    assert "会议明确了接口联调安排" in result.stdout
    assert "完成接口联调" in result.stdout
    assert "L001" in result.stdout
    assert "提示注入" in result.stdout
    assert "建议未写入正式行动项" in result.stdout


def test_ai_failure_is_safe_and_existing_commands_still_work(db_path, monkeypatch):
    environment = prepare_database(db_path)
    monkeypatch.setattr(
        cli,
        "_ai_analyzer",
        lambda: StubAnalyzer(
            AIAnalysisError("模型调用失败，会议与手工行动项功能仍可使用")
        ),
    )

    failed = runner.invoke(cli.app, ["ai", "analyze", "1"], env=environment)
    meetings = runner.invoke(cli.app, ["meeting", "list"], env=environment)

    assert failed.exit_code == 1
    assert "手工行动项功能仍可使用" in failed.stdout
    assert meetings.exit_code == 0
    assert "接口联调推进会" in meetings.stdout

