from typer.testing import CliRunner

from meeting_assistant.cli import app


runner = CliRunner()


def test_cli_help_lists_core_command_groups():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "meeting" in result.stdout
    assert "action" in result.stdout
    assert "seed-demo" in result.stdout


def test_seed_command_and_meeting_list_use_configured_database(db_path):
    environment = {"MEETING_ASSISTANT_DB": str(db_path)}

    seeded = runner.invoke(app, ["seed-demo"], env=environment)
    listed = runner.invoke(app, ["meeting", "list"], env=environment)

    assert seeded.exit_code == 0
    assert "新增 3 场会议、8 条行动项" in seeded.stdout
    assert listed.exit_code == 0
    assert "接口联调推进会" in listed.stdout
    assert "2026-08-07" in listed.stdout


def test_meeting_add_rejects_empty_record_with_nonzero_exit(db_path):
    result = runner.invoke(
        app,
        [
            "meeting",
            "add",
            "--title",
            "空记录测试",
            "--meeting-type",
            "测试会",
            "--meeting-date",
            "2026-08-08",
            "--record-text",
            " ",
        ],
        env={"MEETING_ASSISTANT_DB": str(db_path)},
    )

    assert result.exit_code == 1
    assert "会议记录不能为空" in result.stdout
