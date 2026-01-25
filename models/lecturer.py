from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database
from models.user import User


@dataclass
class Lecturer(User):
    """Lecturer role.

    Table mapping:
    - User (base)
    - Lecturer (role-specific)
    """

    lecturer_id: str = ""

    def save(self, db: Database) -> None:
        super().save(db)
        db.execute(
            """
            INSERT INTO Lecturer (UserID, LecturerID)
            VALUES (?, ?)
            ON CONFLICT(UserID) DO UPDATE SET
                LecturerID=excluded.LecturerID
            """,
            (self.user_id, self.lecturer_id),
        )

    @classmethod
    def load_by_user_id(cls, db: Database, user_id: str) -> Optional["Lecturer"]:
        row = db.query_one(
            """
            SELECT u.*, l.LecturerID
            FROM User u
            JOIN Lecturer l ON l.UserID = u.UserID
            WHERE u.UserID = ?
            """,
            (user_id,),
        )
        return cls.from_join_row(row) if row else None

    @classmethod
    def from_join_row(cls, row) -> "Lecturer":
        base = User.from_row(row)
        return cls(
            **base.__dict__,
            lecturer_id=row["LecturerID"],
        )

 
    def create_attendance_session(self, date: str) -> None:
        raise NotImplementedError("Workflow/UI will be implemented later")

    def summarize_attendance(self, section_id: str) -> None:
        raise NotImplementedError("Workflow/UI will be implemented later")

    def approve_absence_request(self) -> None:
        raise NotImplementedError("Workflow/UI will be implemented later")

    def reject_absence_request(self, reason: str) -> None:
        raise NotImplementedError("Workflow/UI will be implemented later")

    def export_attendance_report(self, section_id: str) -> None:
        raise NotImplementedError("Workflow/UI will be implemented later")

    def record_attendance(self) -> str:
        raise NotImplementedError("Workflow/UI will be implemented later")
