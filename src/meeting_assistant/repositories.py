"""SQLite 数据访问。"""

from __future__ import annotations

from meeting_assistant.db import Database
from meeting_assistant.models import Meeting


def _meeting_from_row(row) -> Meeting:
    return Meeting(**dict(row))


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
