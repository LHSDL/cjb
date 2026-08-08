"""命令行入口。"""

from __future__ import annotations

import sqlite3

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from meeting_assistant.ai.analyzer import AIAnalyzer
from meeting_assistant.ai.client import (
    AIAnalysisError,
    AIConfigurationError,
    DashScopeClient,
    DashScopeSettings,
)
from meeting_assistant.config import default_database_path
from meeting_assistant.db import Database
from meeting_assistant.repositories import ActionItemRepository, MeetingRepository
from meeting_assistant.seed import seed_demo
from meeting_assistant.services import UNSET, ActionItemService, MeetingService
from meeting_assistant.validators import ValidationError


app = typer.Typer(help="会议记录与行动项协同助手")
meeting_app = typer.Typer(help="管理会议记录")
action_app = typer.Typer(help="管理行动项")
ai_app = typer.Typer(help="使用千问分析会议记录")
app.add_typer(meeting_app, name="meeting")
app.add_typer(action_app, name="action")
app.add_typer(ai_app, name="ai")
console = Console()


def _services() -> tuple[MeetingService, ActionItemService]:
    database = Database(default_database_path())
    database.initialize()
    meeting_repository = MeetingRepository(database)
    return MeetingService(meeting_repository), ActionItemService(
        ActionItemRepository(database), meeting_repository
    )


def _ai_analyzer() -> AIAnalyzer:
    settings = DashScopeSettings.from_env()
    return AIAnalyzer(DashScopeClient(settings), model_name=settings.model)


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


def _source_text(sources) -> str:
    return "\n".join(f"{source.line_id}: {source.quote}" for source in sources)


def _print_ai_analysis(analysis) -> None:
    console.print(
        Panel(
            analysis.summary,
            title="AI 会议摘要",
            subtitle=f"模型：{analysis.model}",
        )
    )

    decisions = Table(title="AI 决策建议")
    decisions.add_column("决策")
    decisions.add_column("原文来源")
    for decision in analysis.decisions:
        decisions.add_row(decision.content, _source_text(decision.sources))
    console.print(decisions)

    actions = Table(title="AI 行动项建议")
    actions.add_column("任务")
    actions.add_column("负责人")
    actions.add_column("截止日期")
    actions.add_column("原文来源")
    actions.add_column("提示")
    for item in analysis.action_items:
        confirmations = []
        if item.owner_needs_confirmation:
            confirmations.append("负责人待确认")
        if item.due_date_needs_confirmation:
            confirmations.append("日期待确认")
        confirmations.extend(item.warnings)
        actions.add_row(
            item.content,
            item.owner or "待确认",
            item.due_date or "待确认",
            _source_text(item.sources),
            "；".join(confirmations) or "-",
        )
    console.print(actions)

    if analysis.security_warnings:
        console.print(
            Panel(
                "\n".join(f"- {warning}" for warning in analysis.security_warnings),
                title="安全警告",
                border_style="yellow",
            )
        )
    console.print("[yellow]以上仅为 AI 建议，建议未写入正式行动项。[/yellow]")


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
    content: str | None = typer.Option(None, "--content"),
    owner: str | None = typer.Option(None, "--owner"),
    due_date: str | None = typer.Option(None, "--due-date"),
    clear_owner: bool = typer.Option(False, "--clear-owner"),
    clear_due_date: bool = typer.Option(False, "--clear-due-date"),
) -> None:
    """局部编辑行动项；清空字段需要显式 clear 选项。"""
    try:
        if owner is not None and clear_owner:
            raise ValidationError("--owner 与 --clear-owner 不能同时使用")
        if due_date is not None and clear_due_date:
            raise ValidationError("--due-date 与 --clear-due-date 不能同时使用")
        _, actions = _services()
        item = actions.update_action_item(
            action_id,
            content=content if content is not None else UNSET,
            owner=None if clear_owner else owner if owner is not None else UNSET,
            due_date=(
                None
                if clear_due_date
                else due_date
                if due_date is not None
                else UNSET
            ),
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


@ai_app.command("check-config")
def check_ai_config() -> None:
    """检查百炼配置，不发送会议内容且不显示密钥。"""
    try:
        settings = DashScopeSettings.from_env()
        console.print("[green]AI 配置完整[/green]")
        console.print(f"模型：{settings.model}")
        console.print(f"接口：{settings.base_url}")
        console.print("API Key：已设置（内容已隐藏）")
    except AIConfigurationError as error:
        _abort(error)


@ai_app.command("analyze")
def analyze_meeting(
    meeting_id: int,
    json_output: bool = typer.Option(False, "--json", help="输出机器可读 JSON"),
) -> None:
    """使用千问分析已有会议；结果只作建议，不写数据库。"""
    try:
        meetings, _ = _services()
        meeting = meetings.get_meeting(meeting_id)
        analysis = _ai_analyzer().analyze(meeting)
        if json_output:
            console.print(analysis.model_dump_json(indent=2))
        else:
            _print_ai_analysis(analysis)
    except (
        AIAnalysisError,
        ValidationError,
        LookupError,
        sqlite3.Error,
        OSError,
    ) as error:
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
