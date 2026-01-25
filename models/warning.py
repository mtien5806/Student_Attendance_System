from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database


@dataclass
class Warning:
    """Attendance warning shown in Student dashboard (spec 8.5.4)."""

    warning_id: str  # W003 style handled by service
    student_user_id: str
    system_name: str
    class_name: Optional[str]
    message: str
    created_at: str  # ISO datetime

    def save(self, db: Database) -> None:
        db.execute(
            """
            INSERT INTO Warning (WarningID, StudentUserID, systemName, className, message, createdAt)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(WarningID) DO UPDATE SET
                StudentUserID=excluded.StudentUserID,
                systemName=excluded.systemName,
                className=excluded.className,
                message=excluded.message,
                createdAt=excluded.createdAt
            """,
            (
                self.warning_id,
                self.student_user_id,
                self.system_name,
                self.class_name,
                self.message,
                self.created_at,
            ),
        )

    @classmethod
    def load_by_id(cls, db: Database, warning_id: str) -> Optional["Warning"]:
        row = db.query_one("SELECT * FROM Warning WHERE WarningID=?", (warning_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_for_student(cls, db: Database, student_user_id: str) -> list["Warning"]:
        rows = db.query_all(
            "SELECT * FROM Warning WHERE StudentUserID=? ORDER BY createdAt DESC",
            (student_user_id,),
        )
        return [cls.from_row(r) for r in rows]

    @classmethod
    def from_row(cls, row) -> "Warning":
        def _col(name: str, default=None):
            try:
                return row[name]
            except Exception:
                return default

        return cls(
            warning_id=row["WarningID"],
            student_user_id=row["StudentUserID"],
            system_name=row["systemName"],
            class_name=_col("className"),
            message=row["message"],
            created_at=row["createdAt"],
        )
