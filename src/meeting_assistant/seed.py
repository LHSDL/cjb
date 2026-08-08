"""可重复执行的演示数据。"""

from __future__ import annotations

from meeting_assistant.services import ActionItemService, MeetingService


DEMO_MEETINGS = (
    {
        "title": "接口联调推进会",
        "meeting_type": "项目会",
        "meeting_date": "2026-08-07",
        "record_text": (
            "王芳负责接口联调，下周五前完成。接口联调由王芳推进，"
            "需要在下周五前完成。李明负责整理测试报告。"
        ),
        "actions": (
            ("完成接口联调", "王芳", "2026-08-14"),
            ("整理测试报告", "李明", "2026-08-12"),
            ("确认联调环境", None, "2026-08-10"),
        ),
    },
    {
        "title": "方案评审会",
        "meeting_type": "评审会",
        "meeting_date": "2026-08-08",
        "record_text": (
            "团队决定采用方案 A。赵敏负责补充异常处理设计，"
            "陈晨负责核对数据库约束，负责人稍后确认发布窗口。"
        ),
        "actions": (
            ("补充异常处理设计", "赵敏", "2026-08-11"),
            ("核对数据库约束", "陈晨", "2026-08-13"),
            ("确认发布窗口", None, None),
        ),
    },
    {
        "title": "项目周例会",
        "meeting_type": "例会",
        "meeting_date": "2026-08-06",
        "record_text": (
            "本周完成会议模块。孙宁负责准备演示数据，周琪负责整理 README。"
        ),
        "actions": (
            ("准备演示数据", "孙宁", "2026-08-09"),
            ("整理 README", "周琪", "2026-08-10"),
        ),
    },
)


def seed_demo(
    meeting_service: MeetingService,
    action_service: ActionItemService,
) -> tuple[int, int]:
    """补齐演示数据并返回本次新增的会议数、行动项数。"""
    created_meetings = 0
    created_actions = 0
    existing_meetings = {
        (meeting.title, meeting.meeting_date): meeting
        for meeting in meeting_service.list_meetings()
    }

    for sample in DEMO_MEETINGS:
        key = (sample["title"], sample["meeting_date"])
        meeting = existing_meetings.get(key)
        if meeting is None:
            meeting = meeting_service.create_meeting(
                title=sample["title"],
                meeting_type=sample["meeting_type"],
                meeting_date=sample["meeting_date"],
                record_text=sample["record_text"],
            )
            existing_meetings[key] = meeting
            created_meetings += 1

        existing_contents = {
            item.content
            for item in action_service.list_action_items(meeting_id=meeting.id)
        }
        for content, owner, due_date in sample["actions"]:
            if content in existing_contents:
                continue
            action_service.create_action_item(
                meeting_id=meeting.id,
                content=content,
                owner=owner,
                due_date=due_date,
            )
            existing_contents.add(content)
            created_actions += 1

    return created_meetings, created_actions

