"""领域数据对象。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Meeting:
    id: int
    title: str
    meeting_type: str
    meeting_date: str
    record_text: str
    created_at: str
    updated_at: str

