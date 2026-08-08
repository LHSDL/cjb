"""会议与行动项业务服务。"""

from __future__ import annotations

from datetime import datetime, timezone

from meeting_assistant.models import ActionItem, Meeting
from meeting_assistant.repositories import ActionItemRepository, MeetingRepository
from meeting_assistant.validators import (
    absolute_date,
    action_status,
    optional_absolute_date,
    optional_text,
    required_text,
)


UNSET = object()


class MeetingService:
    def __init__(self, repository: MeetingRepository):
        self.repository = repository

    def create_meeting(
        self,
        *,
        title: str,
        meeting_type: str,
        meeting_date: str,
        record_text: str,
    ) -> Meeting:
        title = required_text(title, label="会议标题", maximum=100)
        meeting_type = required_text(meeting_type, label="会议类型", maximum=50)
        meeting_date = absolute_date(meeting_date, label="会议日期")
        record_text = required_text(record_text, label="会议记录", maximum=50_000)
        timestamp = datetime.now(timezone.utc).isoformat()
        return self.repository.create(
            title=title,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            record_text=record_text,
            timestamp=timestamp,
        )

    def get_meeting(self, meeting_id: int) -> Meeting:
        meeting = self.repository.get(meeting_id)
        if meeting is None:
            raise LookupError(f"会议不存在：{meeting_id}")
        return meeting

    def list_meetings(self) -> list[Meeting]:
        return self.repository.list()


class ActionItemService:
    def __init__(
        self,
        repository: ActionItemRepository,
        meeting_repository: MeetingRepository,
    ):
        self.repository = repository
        self.meeting_repository = meeting_repository

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_action_item(
        self,
        *,
        meeting_id: int,
        content: str,
        owner: str | None,
        due_date: str | None,
    ) -> ActionItem:
        if self.meeting_repository.get(meeting_id) is None:
            raise LookupError(f"会议不存在：{meeting_id}")
        return self.repository.create(
            meeting_id=meeting_id,
            content=required_text(content, label="行动项内容", maximum=500),
            owner=optional_text(owner, label="负责人", maximum=100),
            due_date=optional_absolute_date(due_date, label="截止日期"),
            timestamp=self._timestamp(),
        )

    def update_action_item(
        self,
        action_id: int,
        *,
        content: str | object = UNSET,
        owner: str | None | object = UNSET,
        due_date: str | None | object = UNSET,
    ) -> ActionItem:
        current = self.repository.get(action_id)
        if current is None:
            raise LookupError(f"行动项不存在：{action_id}")
        next_content = current.content if content is UNSET else content
        next_owner = current.owner if owner is UNSET else owner
        next_due_date = current.due_date if due_date is UNSET else due_date
        if not isinstance(next_content, str):
            raise TypeError("行动项内容必须是字符串")
        if next_owner is not None and not isinstance(next_owner, str):
            raise TypeError("负责人必须是字符串或空值")
        if next_due_date is not None and not isinstance(next_due_date, str):
            raise TypeError("截止日期必须是字符串或空值")
        item = self.repository.update(
            action_id,
            content=required_text(next_content, label="行动项内容", maximum=500),
            owner=optional_text(next_owner, label="负责人", maximum=100),
            due_date=optional_absolute_date(next_due_date, label="截止日期"),
            timestamp=self._timestamp(),
        )
        if item is None:  # 防御并发删除；当前版本不提供删除命令。
            raise LookupError(f"行动项不存在：{action_id}")
        return item

    def complete_action_item(self, action_id: int) -> ActionItem:
        item = self.repository.complete(action_id, timestamp=self._timestamp())
        if item is None:
            raise LookupError(f"行动项不存在：{action_id}")
        return item

    def list_action_items(
        self,
        *,
        owner: str | None = None,
        status: str | None = None,
        due_before: str | None = None,
        meeting_id: int | None = None,
    ) -> list[ActionItem]:
        normalized_owner = (
            optional_text(owner, label="负责人", maximum=100)
            if owner is not None
            else None
        )
        normalized_due = optional_absolute_date(due_before, label="截止日期")
        return self.repository.list(
            owner=normalized_owner,
            status=action_status(status),
            due_before=normalized_due,
            meeting_id=meeting_id,
        )
