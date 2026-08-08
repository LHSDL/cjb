from types import SimpleNamespace

import httpx
import pytest
from openai import APITimeoutError

from meeting_assistant.ai.client import (
    AIAnalysisError,
    AIConfigurationError,
    DashScopeClient,
    DashScopeSettings,
)
from meeting_assistant.ai.prompts import PromptRequest


class FakeCompletions:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def fake_sdk(outcomes):
    completions = FakeCompletions(outcomes)
    return SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    ), completions


def response(content):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def prompt():
    return PromptRequest(system="只返回JSON", user='{"task":"test"}', lines={})


def settings():
    return DashScopeSettings(
        api_key="test-key",
        base_url="https://dashscope.example/v1",
        model="qwen-test",
        timeout_seconds=30,
    )


def test_settings_load_from_explicit_env_file(tmp_path, monkeypatch):
    for name in ("DASHSCOPE_API_KEY", "DASHSCOPE_BASE_URL", "DASHSCOPE_MODEL"):
        monkeypatch.delenv(name, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DASHSCOPE_API_KEY=test-key\n"
        "DASHSCOPE_BASE_URL=https://dashscope.example/v1\n"
        "DASHSCOPE_MODEL=qwen-test\n",
        encoding="utf-8",
    )

    loaded = DashScopeSettings.from_env(env_file)

    assert loaded.api_key == "test-key"
    assert loaded.model == "qwen-test"


def test_settings_reject_missing_values(tmp_path, monkeypatch):
    for name in ("DASHSCOPE_API_KEY", "DASHSCOPE_BASE_URL", "DASHSCOPE_MODEL"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(AIConfigurationError, match="DASHSCOPE_API_KEY"):
        DashScopeSettings.from_env(tmp_path / "missing.env")


def test_client_sends_json_mode_non_thinking_request():
    sdk, completions = fake_sdk([response('{"ok":true}')])
    client = DashScopeClient(settings(), sdk_client=sdk)

    content = client.complete(prompt())

    assert content == '{"ok":true}'
    request = completions.calls[0]
    assert request["model"] == "qwen-test"
    assert request["response_format"] == {"type": "json_object"}
    assert request["extra_body"] == {"enable_thinking": False}
    assert request["temperature"] == 0.1
    assert "max_tokens" not in request


def test_client_retries_timeout_once_then_returns_safe_error():
    timeout = APITimeoutError(request=httpx.Request("POST", "https://example.test"))
    sdk, completions = fake_sdk([timeout, timeout])
    client = DashScopeClient(settings(), sdk_client=sdk)

    with pytest.raises(AIAnalysisError, match="模型调用超时"):
        client.complete(prompt())

    assert len(completions.calls) == 2


def test_client_rejects_empty_model_content():
    sdk, _ = fake_sdk([response(None)])
    client = DashScopeClient(settings(), sdk_client=sdk)

    with pytest.raises(AIAnalysisError, match="模型返回了空内容"):
        client.complete(prompt())

