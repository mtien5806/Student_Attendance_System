from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database, new_uuid, utc_now_iso


@dataclass
class AttendanceSession:
    session_id: str
    lecturer_user_id: str
    date: str  # YYYY-MM-DD
    class_name: str
    status: str  # OPEN/CLOSED/...
    created_at: str  # ISO datetime

    @classmethod
    def create(
        cls,
        *,
        lecturer_user_id: str,
        date: str,
        class_name: str,
        status: str = "OPEN",
    ) -> "AttendanceSession":
        return cls(
            session_id=new_uuid(),
            lecturer_user_id=lecturer_user_id,
            date=date,
            class_name=class_name,
            status=status,
            created_at=utc_now_iso(),
        )

    def save(self, db: Database) -> None:
        db.execute(
            """
            INSERT INTO AttendanceSession (SessionID, LecturerUserID, date, className, status, createdAt)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(SessionID) DO UPDATE SET
                LecturerUserID=excluded.LecturerUserID,
                date=excluded.date,
                className=excluded.className,
                status=excluded.status,
                createdAt=excluded.createdAt
            """,
            (
                self.session_id,
                self.lecturer_user_id,
                self.date,
                self.class_name,
                self.status,
                self.created_at,
            ),
        )

    @classmethod
    def load_by_id(cls, db: Database, session_id: str) -> Optional["AttendanceSession"]:
        row = db.query_one("SELECT * FROM AttendanceSession WHERE SessionID=?", (session_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_by_lecturer(cls, db: Database, lecturer_user_id: str) -> list["AttendanceSession"]:
        rows = db.query_all(
            "SELECT * FROM AttendanceSession WHERE LecturerUserID=? ORDER BY createdAt DESC",
            (lecturer_user_id,),
        )
        return [cls.from_row(r) for r in rows]

    @classmethod
    def from_row(cls, row) -> "AttendanceSession":
        return cls(
            session_id=row["SessionID"],
            lecturer_user_id=row["LecturerUserID"],
            date=row["date"],
            class_name=row["className"],
            status=row["status"],
            created_at=row["createdAt"],
        )

    def close_session(self, db: Database) -> None:
        self.status = "CLOSED"
        self.save(db)
