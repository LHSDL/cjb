import pytest

from meeting_assistant.db import Database
from meeting_assistant.repositories import ActionItemRepository, MeetingRepository
from meeting_assistant.services import ActionItemService, MeetingService
from meeting_assistant.validators import ValidationError


@pytest.fixture
def services(db_path):
    database = Database(db_path)
    database.initialize()
    meetings = MeetingRepository(database)
    return MeetingService(meetings), ActionItemService(
        ActionItemRepository(database), meetings
    )


def create_meeting(meeting_service):
    return meeting_service.create_meeting(
        title="接口联调会",
        meeting_type="项目会",
        meeting_date="2026-08-07",
        record_text="确认接口联调范围和负责人。",
    )


def test_create_action_item_with_pending_status(services):
    meeting_service, action_service = services
    meeting = create_meeting(meeting_service)

    item = action_service.create_action_item(
        meeting_id=meeting.id,
        content="完成接口联调",
        owner="王芳",
        due_date="2026-08-14",
    )

    assert item.meeting_id == meeting.id
    assert item.content == "完成接口联调"
    assert item.owner == "王芳"
    assert item.due_date == "2026-08-14"
    assert item.status == "pending"
    assert item.completed_at is None


def test_create_action_item_allows_unconfirmed_owner_and_date(services):
    meeting_service, action_service = services
    meeting = create_meeting(meeting_service)

    item = action_service.create_action_item(
        meeting_id=meeting.id,
        content="确认评审安排",
        owner="  ",
        due_date=None,
    )

    assert item.owner is None
    assert item.due_date is None


def test_create_action_item_rejects_missing_meeting(services):
    _, action_service = services

    with pytest.raises(LookupError, match="会议不存在：999"):
        action_service.create_action_item(
            meeting_id=999,
            content="完成接口联调",
            owner="王芳",
            due_date="2026-08-14",
        )


def test_update_action_item(services):
    meeting_service, action_service = services
    meeting = create_meeting(meeting_service)
    item = action_service.create_action_item(
        meeting_id=meeting.id,
        content="完成接口联调",
        owner="王芳",
        due_date="2026-08-14",
    )

    updated = action_service.update_action_item(
        item.id,
        content="完成接口联调并提交报告",
        owner="李明",
        due_date="2026-08-15",
    )

    assert updated.content == "完成接口联调并提交报告"
    assert updated.owner == "李明"
    assert updated.due_date == "2026-08-15"


def test_complete_action_item_is_idempotent(services):
    meeting_service, action_service = services
    meeting = create_meeting(meeting_service)
    item = action_service.create_action_item(
        meeting_id=meeting.id,
        content="完成接口联调",
        owner="王芳",
        due_date="2026-08-14",
    )

    first = action_service.complete_action_item(item.id)
    second = action_service.complete_action_item(item.id)

    assert first.status == "completed"
    assert first.completed_at is not None
    assert second.completed_at == first.completed_at


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"content": " "}, "行动项内容不能为空"),
        ({"content": "办" * 501}, "行动项内容不能超过 500 个字符"),
        ({"due_date": "下周五"}, "截止日期必须使用 YYYY-MM-DD 格式"),
    ],
)
def test_create_action_item_rejects_invalid_input(services, changes, message):
    meeting_service, action_service = services
    meeting = create_meeting(meeting_service)
    values = {
        "meeting_id": meeting.id,
        "content": "完成接口联调",
        "owner": "王芳",
        "due_date": "2026-08-14",
    }
    values.update(changes)

    with pytest.raises(ValidationError, match=message):
        action_service.create_action_item(**values)


def test_update_and_complete_missing_action_report_clear_error(services):
    _, action_service = services

    with pytest.raises(LookupError, match="行动项不存在：999"):
        action_service.update_action_item(
            999, content="更新", owner=None, due_date=None
        )
    with pytest.raises(LookupError, match="行动项不存在：999"):
        action_service.complete_action_item(999)

