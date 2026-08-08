"""对模型 JSON 中的原文依据进行严格校验。"""

from __future__ import annotations

from meeting_assistant.ai.models import RawAnalysis, SourceReference


class AIOutputValidationError(ValueError):
    """模型输出没有通过业务校验。"""


def _validate_sources(
    sources: list[SourceReference], lines: dict[str, str], *, subject: str
) -> str:
    quoted_text: list[str] = []
    for source in sources:
        line = lines.get(source.line_id)
        if line is None:
            raise AIOutputValidationError(f"{subject}的来源行 {source.line_id} 不存在")
        if source.quote not in line:
            raise AIOutputValidationError(
                f"{subject}的引用不是原文的连续子串：{source.line_id}"
            )
        quoted_text.append(source.quote)
    return "\n".join(quoted_text)


def validate_raw_analysis(raw: RawAnalysis, lines: dict[str, str]) -> None:
    for index, decision in enumerate(raw.decisions, start=1):
        _validate_sources(decision.sources, lines, subject=f"第{index}条决策")

    for index, action in enumerate(raw.action_items, start=1):
        subject = f"第{index}条行动项"
        evidence = _validate_sources(action.sources, lines, subject=subject)
        if action.owner is not None and action.owner not in evidence:
            raise AIOutputValidationError(f"{subject}的负责人没有原文依据")
        if (
            action.due_date_expression is not None
            and action.due_date_expression not in evidence
        ):
            raise AIOutputValidationError(f"{subject}的日期表达没有原文依据")

