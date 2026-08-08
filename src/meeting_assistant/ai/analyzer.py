"""编排千问调用与所有确定性后处理。"""

from __future__ import annotations

from pydantic import ValidationError

from meeting_assistant.ai.client import AIAnalysisError, LLMClient
from meeting_assistant.ai.date_resolver import resolve_date
from meeting_assistant.ai.deduplication import merge_duplicate_actions
from meeting_assistant.ai.models import (
    AIAnalysis,
    ActionSuggestion,
    RawAnalysis,
)
from meeting_assistant.ai.prompts import build_prompt
from meeting_assistant.ai.security import detect_injection, is_injection_text
from meeting_assistant.ai.validation import (
    AIOutputValidationError,
    validate_raw_analysis,
)
from meeting_assistant.models import Meeting


class AIAnalyzer:
    def __init__(self, client: LLMClient, *, model_name: str | None = None):
        self.client = client
        self.model_name = model_name or getattr(client, "model_name", "unknown-model")

    def analyze(self, meeting: Meeting) -> AIAnalysis:
        prompt = build_prompt(meeting)
        response_text = self.client.complete(prompt)
        try:
            raw = RawAnalysis.model_validate_json(response_text)
        except ValidationError as error:
            raise AIAnalysisError(
                "模型返回的JSON无效，会议与手工行动项功能仍可使用"
            ) from error

        try:
            validate_raw_analysis(raw, prompt.lines)
        except AIOutputValidationError as error:
            raise AIAnalysisError(
                f"模型输出校验失败：{error}。会议与手工行动项功能仍可使用"
            ) from error

        security_warnings = list(raw.security_warnings)
        security_warnings.extend(
            f"{warning.line_id}：{warning.reason}"
            for warning in detect_injection(prompt.lines)
        )

        decisions = []
        for decision in raw.decisions:
            if any(is_injection_text(source.quote) for source in decision.sources):
                security_warnings.append(
                    f"已忽略由疑似提示注入文本支撑的决策：{decision.content}"
                )
                continue
            decisions.append(decision)

        suggestions: list[ActionSuggestion] = []
        for action in raw.action_items:
            if any(is_injection_text(source.quote) for source in action.sources):
                security_warnings.append(
                    f"已忽略由疑似提示注入文本支撑的行动项：{action.content}"
                )
                continue
            resolved = resolve_date(action.due_date_expression, meeting.meeting_date)
            warnings = [resolved.warning] if resolved.warning else []
            suggestions.append(
                ActionSuggestion(
                    content=action.content,
                    owner=action.owner,
                    owner_needs_confirmation=action.owner is None,
                    due_date_expression=action.due_date_expression,
                    due_date=resolved.value,
                    due_date_needs_confirmation=resolved.needs_confirmation,
                    sources=action.sources,
                    warnings=warnings,
                )
            )

        return AIAnalysis(
            model=self.model_name,
            summary=raw.summary,
            decisions=decisions,
            action_items=merge_duplicate_actions(suggestions),
            security_warnings=list(dict.fromkeys(security_warnings)),
        )
