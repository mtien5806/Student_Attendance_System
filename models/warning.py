from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database


@dataclass
class Warning:
    warning_id: str
    student_user_id: str
    system_name: str
    message: str
    created_at: str  # ISO datetime

    def save(self, db: Database) -> None:
        db.execute(
            """
            INSERT INTO Warning (WarningID, StudentUserID, systemName, message, createdAt)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(WarningID) DO UPDATE SET
                StudentUserID=excluded.StudentUserID,
                systemName=excluded.systemName,
                message=excluded.message,
                createdAt=excluded.createdAt
            """,
            (self.warning_id, self.student_user_id, self.system_name, self.message, self.created_at),
        )

    @classmethod
    def load_by_id(cls, db: Database, warning_id: str) -> Optional["Warning"]:
        row = db.query_one("SELECT * FROM Warning WHERE WarningID=?", (warning_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_for_student(cls, db: Database, student_user_id: str) -> list["Warning"]:
        rows = db.query_all(
            "SELECT * FROM Warning WHERE StudentUserID=? ORDER BY createdAt DESC", (student_user_id,)
        )
        return [cls.from_row(r) for r in rows]

    @classmethod
    def from_row(cls, row) -> "Warning":
        return cls(
            warning_id=row["WarningID"],
            student_user_id=row["StudentUserID"],
            system_name=row["systemName"],
            message=row["message"],
            created_at=row["createdAt"],
        )

    # stub
    def send_warning(self) -> None:
        raise NotImplementedError("Use System.send_warning(...) for now")
