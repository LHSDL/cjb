from meeting_assistant.db import Database


def test_initialize_creates_tables_indexes_and_foreign_keys(db_path):
    database = Database(db_path)

    database.initialize()

    with database.connect() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }
        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(action_items)"
        ).fetchall()

    assert {"meetings", "action_items"}.issubset(tables)
    assert {
        "idx_action_items_meeting_id",
        "idx_action_items_owner",
        "idx_action_items_status",
        "idx_action_items_due_date",
    }.issubset(indexes)
    assert foreign_keys[0][2] == "meetings"


def test_initialize_is_idempotent(db_path):
    database = Database(db_path)

    database.initialize()
    database.initialize()

    with database.connect() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' "
            "AND name IN ('meetings', 'action_items')"
        ).fetchone()[0]

    assert count == 2
