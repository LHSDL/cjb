import pytest

from meeting_assistant.db import Database
from meeting_assistant.repositories import MeetingRepository
from meeting_assistant.services import MeetingService
from meeting_assistant.validators import ValidationError


@pytest.fixture
def meeting_service(db_path):
    database = Database(db_path)
    database.initialize()
    return MeetingService(MeetingRepository(database))


def test_create_meeting_persists_business_date(meeting_service):
    created = meeting_service.create_meeting(
        title="接口联调会",
        meeting_type="项目会",
        meeting_date="2026-08-07",
        record_text="确认接口联调范围和负责人。",
    )

    loaded = meeting_service.get_meeting(created.id)

    assert loaded.title == "接口联调会"
    assert loaded.meeting_type == "项目会"
    assert loaded.meeting_date == "2026-08-07"
    assert loaded.record_text == "确认接口联调范围和负责人。"


def test_list_meetings_orders_latest_business_date_first(meeting_service):
    common = {"meeting_type": "例会", "record_text": "会议记录"}
    meeting_service.create_meeting(
        title="周一会议", meeting_date="2026-08-03", **common
    )
    meeting_service.create_meeting(
        title="周五会议", meeting_date="2026-08-07", **common
    )

    meetings = meeting_service.list_meetings()

    assert [meeting.title for meeting in meetings] == ["周五会议", "周一会议"]


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"title": "   "}, "会议标题不能为空"),
        ({"meeting_type": ""}, "会议类型不能为空"),
        ({"meeting_date": "2026/08/07"}, "会议日期必须使用 YYYY-MM-DD 格式"),
        ({"record_text": "\n\t"}, "会议记录不能为空"),
        ({"record_text": "会" * 50_001}, "会议记录不能超过 50000 个字符"),
        ({"title": "会" * 101}, "会议标题不能超过 100 个字符"),
        ({"meeting_type": "会" * 51}, "会议类型不能超过 50 个字符"),
    ],
)
def test_create_meeting_rejects_invalid_input(meeting_service, changes, message):
    values = {
        "title": "接口联调会",
        "meeting_type": "项目会",
        "meeting_date": "2026-08-07",
        "record_text": "确认接口联调范围和负责人。",
    }
    values.update(changes)

    with pytest.raises(ValidationError, match=message):
        meeting_service.create_meeting(**values)


def test_get_missing_meeting_reports_clear_error(meeting_service):
    with pytest.raises(LookupError, match="会议不存在：999"):
        meeting_service.get_meeting(999)
