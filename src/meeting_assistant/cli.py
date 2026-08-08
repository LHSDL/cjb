"""命令行入口。"""

from __future__ import annotations

import sqlite3

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from meeting_assistant.config import default_database_path
from meeting_assistant.db import Database
from meeting_assistant.repositories import ActionItemRepository, MeetingRepository
from meeting_assistant.seed import seed_demo
from meeting_assistant.services import ActionItemService, MeetingService
from meeting_assistant.validators import ValidationError


app = typer.Typer(help="会议记录与行动项协同助手")
meeting_app = typer.Typer(help="管理会议记录")
action_app = typer.Typer(help="管理行动项")
app.add_typer(meeting_app, name="meeting")
app.add_typer(action_app, name="action")
console = Console()


def _services() -> tuple[MeetingService, ActionItemService]:
    database = Database(default_database_path())
    database.initialize()
    meeting_repository = MeetingRepository(database)
    return MeetingService(meeting_repository), ActionItemService(
        ActionItemRepository(database), meeting_repository
    )


def _abort(error: Exception) -> None:
    console.print(f"[red]错误：{error}[/red]")
    raise typer.Exit(code=1)


def _meeting_table(meetings) -> Table:
    table = Table(title="会议列表")
    table.add_column("ID", justify="right")
    table.add_column("日期")
    table.add_column("类型")
    table.add_column("标题")
    for meeting in meetings:
        table.add_row(
            str(meeting.id),
            meeting.meeting_date,
            meeting.meeting_type,
            meeting.title,
        )
    return table


def _action_table(items) -> Table:
    table = Table(title="行动项")
    table.add_column("ID", justify="right")
    table.add_column("会议", justify="right")
    table.add_column("状态")
    table.add_column("负责人")
    table.add_column("截止日期")
    table.add_column("内容")
    for item in items:
        status = "已完成" if item.status == "completed" else "待完成"
        table.add_row(
            str(item.id),
            str(item.meeting_id),
            status,
            item.owner or "待确认",
            item.due_date or "待确认",
            item.content,
        )
    return table


@meeting_app.command("add")
def add_meeting(
    title: str = typer.Option(..., "--title", prompt="会议标题"),
    meeting_type: str = typer.Option(..., "--meeting-type", prompt="会议类型"),
    meeting_date: str = typer.Option(..., "--meeting-date", prompt="会议日期 YYYY-MM-DD"),
    record_text: str = typer.Option(..., "--record-text", prompt="会议记录"),
) -> None:
    """新增会议。"""
    try:
        meetings, _ = _services()
        meeting = meetings.create_meeting(
            title=title,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            record_text=record_text,
        )
        console.print(f"[green]已创建会议 #{meeting.id}：{meeting.title}[/green]")
    except (ValidationError, LookupError, sqlite3.Error, OSError) as error:
        _abort(error)


@meeting_app.command("list")
def list_meetings() -> None:
    """查看会议列表。"""
    try:
        meetings, _ = _services()
        console.print(_meeting_table(meetings.list_meetings()))
    except (sqlite3.Error, OSError) as error:
        _abort(error)


@meeting_app.command("show")
def show_meeting(meeting_id: int) -> None:
    """查看会议详情及行动项。"""
    try:
        meetings, actions = _services()
        meeting = meetings.get_meeting(meeting_id)
        console.print(
            Panel(
                meeting.record_text,
                title=f"#{meeting.id} {meeting.title}",
                subtitle=f"{meeting.meeting_date} · {meeting.meeting_type}",
            )
        )
        console.print(_action_table(actions.list_action_items(meeting_id=meeting_id)))
    except (ValidationError, LookupError, sqlite3.Error, OSError) as error:
        _abort(error)


@action_app.command("add")
def add_action(
    meeting_id: int = typer.Option(..., "--meeting-id"),
    content: str = typer.Option(..., "--content", prompt="行动项内容"),
    owner: str | None = typer.Option(None, "--owner"),
    due_date: str | None = typer.Option(None, "--due-date"),
) -> None:
    """手工新增行动项。"""
    try:
        _, actions = _services()
        item = actions.create_action_item(
            meeting_id=meeting_id,
            content=content,
            owner=owner,
            due_date=due_date,
        )
        console.print(f"[green]已创建行动项 #{item.id}[/green]")
    except (ValidationError, LookupError, sqlite3.Error, OSError) as error:
        _abort(error)


@action_app.command("edit")
def edit_action(
    action_id: int,
    content: str = typer.Option(..., "--content", prompt="行动项内容"),
    owner: str | None = typer.Option(None, "--owner"),
    due_date: str | None = typer.Option(None, "--due-date"),
) -> None:
    """编辑行动项。"""
    try:
        _, actions = _services()
        item = actions.update_action_item(
            action_id, content=content, owner=owner, due_date=due_date
        )
        console.print(f"[green]已更新行动项 #{item.id}[/green]")
    except (ValidationError, LookupError, sqlite3.Error, OSError) as error:
        _abort(error)


@action_app.command("complete")
def complete_action(action_id: int) -> None:
    """完成行动项；重复执行不会覆盖首次完成时间。"""
    try:
        _, actions = _services()
        item = actions.complete_action_item(action_id)
        console.print(f"[green]行动项 #{item.id} 已完成[/green]")
    except (LookupError, sqlite3.Error, OSError) as error:
        _abort(error)


@action_app.command("list")
def list_actions(
    owner: str | None = typer.Option(None, "--owner"),
    status: str | None = typer.Option(None, "--status"),
    due_before: str | None = typer.Option(None, "--due-before"),
    meeting_id: int | None = typer.Option(None, "--meeting-id"),
) -> None:
    """筛选行动项。截止日期筛选包含指定日期当天。"""
    try:
        _, actions = _services()
        console.print(
            _action_table(
                actions.list_action_items(
                    owner=owner,
                    status=status,
                    due_before=due_before,
                    meeting_id=meeting_id,
                )
            )
        )
    except (ValidationError, sqlite3.Error, OSError) as error:
        _abort(error)


@app.command("seed-demo")
def seed_demo_command() -> None:
    """幂等补齐 3 场会议和 8 条行动项的演示数据。"""
    try:
        meetings, actions = _services()
        meeting_count, action_count = seed_demo(meetings, actions)
        console.print(
            f"[green]演示数据完成：新增 {meeting_count} 场会议、"
            f"{action_count} 条行动项[/green]"
        )
    except (ValidationError, LookupError, sqlite3.Error, OSError) as error:
        _abort(error)


if __name__ == "__main__":
    app()
