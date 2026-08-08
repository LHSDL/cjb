"""会议与行动项业务服务。"""

from __future__ import annotations

from datetime import datetime, timezone

from meeting_assistant.models import Meeting
from meeting_assistant.repositories import MeetingRepository
from meeting_assistant.validators import absolute_date, required_text


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
