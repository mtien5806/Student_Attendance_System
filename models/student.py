from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database
from models.user import User


@dataclass
class Student(User):
 
    student_id: str = ""
    major_name: Optional[str] = None

    def save(self, db: Database) -> None:
        super().save(db)
        db.execute(
            """
            INSERT INTO Student (UserID, StudentID, majorName)
            VALUES (?, ?, ?)
            ON CONFLICT(UserID) DO UPDATE SET
                StudentID=excluded.StudentID,
                majorName=excluded.majorName
            """,
            (self.user_id, self.student_id, self.major_name),
        )

    @classmethod
    def load_by_user_id(cls, db: Database, user_id: str) -> Optional["Student"]:
        row = db.query_one(
            """
            SELECT u.*, s.StudentID, s.majorName
            FROM User u
            JOIN Student s ON s.UserID = u.UserID
            WHERE u.UserID = ?
            """,
            (user_id,),
        )
        return cls.from_join_row(row) if row else None

    @classmethod
    def from_join_row(cls, row) -> "Student":
        base = User.from_row(row)
        return cls(
            **base.__dict__,
            student_id=row["StudentID"],
            major_name=row["majorName"],
        )

    # stubs (workflow sau)
    def take_attendance(self) -> None:
        raise NotImplementedError("Workflow/UI will be implemented later")

    def view_attendance(self) -> None:
        raise NotImplementedError("Workflow/UI will be implemented later")

    def receive_warning(self) -> None:
        raise NotImplementedError("Workflow/UI will be implemented later")

    def submit_absence_request(self, reason: str) -> None:
        raise NotImplementedError("Workflow/UI will be implemented later")
