"""确定性合并模型返回的明显重复行动项。"""

from __future__ import annotations

import re

from meeting_assistant.ai.models import ActionSuggestion, SourceReference


LEADING_VERBS = re.compile(r"^(完成|负责|推进|跟进|进行|提交|整理|开展)")


def _normalized_content(content: str) -> str:
    normalized = re.sub(r"[\s，。；：、,.!?！？;:]", "", content)
    return LEADING_VERBS.sub("", normalized)


def _same_task(left: ActionSuggestion, right: ActionSuggestion) -> bool:
    left_text = _normalized_content(left.content)
    right_text = _normalized_content(right.content)
    if left_text == right_text:
        return True
    shorter, longer = sorted((left_text, right_text), key=len)
    return len(shorter) >= 4 and shorter in longer


def _unique_sources(items: list[ActionSuggestion]) -> list[SourceReference]:
    seen: set[tuple[str, str]] = set()
    sources: list[SourceReference] = []
    for item in items:
        for source in item.sources:
            key = (source.line_id, source.quote)
            if key not in seen:
                seen.add(key)
                sources.append(source)
    return sources


def _merge_group(items: list[ActionSuggestion]) -> ActionSuggestion:
    first = items[0]
    owners = {item.owner for item in items if item.owner is not None}
    due_dates = {item.due_date for item in items if item.due_date is not None}
    expressions = {
        item.due_date_expression
        for item in items
        if item.due_date_expression is not None
    }
    warnings = list(dict.fromkeys(warning for item in items for warning in item.warnings))

    owner = next(iter(owners)) if len(owners) == 1 else None
    if len(owners) > 1:
        warnings.append("重复任务的负责人存在冲突，需要人工确认")

    due_date = next(iter(due_dates)) if len(due_dates) == 1 else None
    expression = next(iter(expressions)) if len(expressions) == 1 else None
    if len(due_dates) > 1 or len(expressions) > 1:
        due_date = None
        expression = None
        warnings.append("重复任务的截止日期存在冲突，需要人工确认")

    return first.model_copy(
        update={
            "owner": owner,
            "owner_needs_confirmation": owner is None,
            "due_date_expression": expression,
            "due_date": due_date,
            "due_date_needs_confirmation": due_date is None,
            "sources": _unique_sources(items),
            "warnings": list(dict.fromkeys(warnings)),
        }
    )


def merge_duplicate_actions(
    actions: list[ActionSuggestion],
) -> list[ActionSuggestion]:
    groups: list[list[ActionSuggestion]] = []
    for action in actions:
        for group in groups:
            if _same_task(group[0], action):
                group.append(action)
                break
        else:
            groups.append([action])
    return [_merge_group(group) for group in groups]
