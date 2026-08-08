import pytest

from meeting_assistant.db import Database
from meeting_assistant.repositories import ActionItemRepository, MeetingRepository
from meeting_assistant.services import ActionItemService, MeetingService
from meeting_assistant.validators import ValidationError


@pytest.fixture
def populated_services(db_path):
    database = Database(db_path)
    database.initialize()
    meeting_repository = MeetingRepository(database)
    meeting_service = MeetingService(meeting_repository)
    action_service = ActionItemService(
        ActionItemRepository(database), meeting_repository
    )
    first = meeting_service.create_meeting(
        title="接口会",
        meeting_type="项目会",
        meeting_date="2026-08-07",
        record_text="接口事项。",
    )
    second = meeting_service.create_meeting(
        title="评审会",
        meeting_type="评审会",
        meeting_date="2026-08-08",
        record_text="评审事项。",
    )
    action_service.create_action_item(
        meeting_id=first.id,
        content="接口联调",
        owner="王芳",
        due_date="2026-08-14",
    )
    completed = action_service.create_action_item(
        meeting_id=first.id,
        content="提交报告",
        owner="李明",
        due_date="2026-08-20",
    )
    action_service.complete_action_item(completed.id)
    action_service.create_action_item(
        meeting_id=second.id,
        content="整理材料",
        owner="王芳",
        due_date=None,
    )
    return action_service, first, second


def test_filter_action_items_by_owner(populated_services):
    service, _, _ = populated_services
    assert {item.content for item in service.list_action_items(owner="王芳")} == {
        "接口联调",
        "整理材料",
    }


def test_filter_action_items_by_status(populated_services):
    service, _, _ = populated_services
    items = service.list_action_items(status="completed")
    assert [item.content for item in items] == ["提交报告"]


def test_filter_action_items_by_due_date(populated_services):
    service, _, _ = populated_services
    items = service.list_action_items(due_before="2026-08-14")
    assert [item.content for item in items] == ["接口联调"]


def test_filter_action_items_by_meeting(populated_services):
    service, first, _ = populated_services
    assert len(service.list_action_items(meeting_id=first.id)) == 2


def test_filters_can_be_combined(populated_services):
    service, first, _ = populated_services
    items = service.list_action_items(
        owner="王芳", status="pending", meeting_id=first.id
    )
    assert [item.content for item in items] == ["接口联调"]


def test_filter_rejects_invalid_status_and_date(populated_services):
    service, _, _ = populated_services
    with pytest.raises(ValidationError, match="状态只能是 pending 或 completed"):
        service.list_action_items(status="done")
    with pytest.raises(ValidationError, match="截止日期必须使用 YYYY-MM-DD 格式"):
        service.list_action_items(due_before="下周五")
