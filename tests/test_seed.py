from meeting_assistant.db import Database
from meeting_assistant.repositories import ActionItemRepository, MeetingRepository
from meeting_assistant.seed import seed_demo
from meeting_assistant.services import ActionItemService, MeetingService


def test_seed_demo_is_idempotent_and_meets_sample_size(db_path):
    database = Database(db_path)
    database.initialize()
    meeting_repository = MeetingRepository(database)
    meetings = MeetingService(meeting_repository)
    actions = ActionItemService(ActionItemRepository(database), meeting_repository)

    first = seed_demo(meetings, actions)
    second = seed_demo(meetings, actions)

    assert first == (3, 8)
    assert second == (0, 0)
    assert len(meetings.list_meetings()) == 3
    assert len(actions.list_action_items()) == 8


def test_seed_demo_preserves_meeting_date_as_relative_date_baseline(db_path):
    database = Database(db_path)
    database.initialize()
    meeting_repository = MeetingRepository(database)
    meetings = MeetingService(meeting_repository)
    actions = ActionItemService(ActionItemRepository(database), meeting_repository)

    seed_demo(meetings, actions)

    by_title = {meeting.title: meeting for meeting in meetings.list_meetings()}
    assert by_title["接口联调推进会"].meeting_date == "2026-08-07"
    assert "下周五" in by_title["接口联调推进会"].record_text

