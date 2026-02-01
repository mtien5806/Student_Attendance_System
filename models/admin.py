from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database
from .user import User


@dataclass
class Administrator(User):

    admin_id: str = ""

    def save(self, db: Database) -> None:
        super().save(db)
        db.execute(
            """
            INSERT INTO Administrator (UserID, AdminID)
            VALUES (?, ?)
            ON CONFLICT(UserID) DO UPDATE SET
                AdminID=excluded.AdminID
            """,
            (self.user_id, self.admin_id),
        )

    @classmethod
    def load_by_user_id(cls, db: Database, user_id: str) -> Optional["Administrator"]:
        row = db.query_one(
            """
            SELECT u.*, a.AdminID
            FROM User u
            JOIN Administrator a ON a.UserID = u.UserID
            WHERE u.UserID = ?
            """,
            (user_id,),
        )
        return cls.from_join_row(row) if row else None

    @classmethod
    def from_join_row(cls, row) -> "Administrator":
        base = User.from_row(row)
        return cls(
            **base.__dict__,
            admin_id=row["AdminID"],
        )


    def manage_attendance(self) -> None:
        raise NotImplementedError("Workflow/UI will be implemented later")

    def search_attendance(self) -> None:
        raise NotImplementedError("Workflow/UI will be implemented later")
        