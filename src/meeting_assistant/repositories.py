"""SQLite 数据访问。"""

from __future__ import annotations

from meeting_assistant.db import Database
from meeting_assistant.models import ActionItem, Meeting


def _meeting_from_row(row) -> Meeting:
    return Meeting(**dict(row))


def _action_item_from_row(row) -> ActionItem:
    return ActionItem(**dict(row))


class MeetingRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(
        self,
        *,
        title: str,
        meeting_type: str,
        meeting_date: str,
        record_text: str,
        timestamp: str,
    ) -> Meeting:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO meetings (
                    title, meeting_type, meeting_date, record_text,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    meeting_type,
                    meeting_date,
                    record_text,
                    timestamp,
                    timestamp,
                ),
            )
            row = connection.execute(
                "SELECT * FROM meetings WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return _meeting_from_row(row)

    def get(self, meeting_id: int) -> Meeting | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
            ).fetchone()
        return _meeting_from_row(row) if row else None

    def list(self) -> list[Meeting]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM meetings ORDER BY meeting_date DESC, id DESC"
            ).fetchall()
        return [_meeting_from_row(row) for row in rows]


class ActionItemRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(
        self,
        *,
        meeting_id: int,
        content: str,
        owner: str | None,
        due_date: str | None,
        timestamp: str,
    ) -> ActionItem:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO action_items (
                    meeting_id, content, owner, due_date, status,
                    completed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'pending', NULL, ?, ?)
                """,
                (meeting_id, content, owner, due_date, timestamp, timestamp),
            )
            row = connection.execute(
                "SELECT * FROM action_items WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return _action_item_from_row(row)

    def get(self, action_id: int) -> ActionItem | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM action_items WHERE id = ?", (action_id,)
            ).fetchone()
        return _action_item_from_row(row) if row else None

    def update(
        self,
        action_id: int,
        *,
        content: str,
        owner: str | None,
        due_date: str | None,
        timestamp: str,
    ) -> ActionItem | None:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE action_items
                SET content = ?, owner = ?, due_date = ?, updated_at = ?
                WHERE id = ?
                """,
                (content, owner, due_date, timestamp, action_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT * FROM action_items WHERE id = ?", (action_id,)
            ).fetchone()
        return _action_item_from_row(row)

    def complete(self, action_id: int, *, timestamp: str) -> ActionItem | None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE action_items
                SET status = 'completed', completed_at = ?, updated_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (timestamp, timestamp, action_id),
            )
            row = connection.execute(
                "SELECT * FROM action_items WHERE id = ?", (action_id,)
            ).fetchone()
        return _action_item_from_row(row) if row else None

    def list(
        self,
        *,
        owner: str | None = None,
        status: str | None = None,
        due_before: str | None = None,
        meeting_id: int | None = None,
    ) -> list[ActionItem]:
        clauses: list[str] = []
        parameters: list[object] = []
        if owner is not None:
            clauses.append("owner = ?")
            parameters.append(owner)
        if status is not None:
            clauses.append("status = ?")
            parameters.append(status)
        if due_before is not None:
            clauses.append("due_date <= ?")
            parameters.append(due_before)
        if meeting_id is not None:
            clauses.append("meeting_id = ?")
            parameters.append(meeting_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        query = (
            "SELECT * FROM action_items"
            f"{where} ORDER BY COALESCE(due_date, '9999-12-31'), id"
        )
        with self.database.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [_action_item_from_row(row) for row in rows]
