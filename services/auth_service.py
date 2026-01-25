from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from Database.database import Database
from models.user import User

Role = Literal["student", "lecturer", "admin", "unknown"]


@dataclass
class AuthService:
    db: Database

    def login(self, username: str, password: str) -> Optional[User]:
        return User.login(self.db, username, password)

    def detect_role(self, user_id: str) -> Role:
        if self.db.query_one("SELECT 1 FROM Student WHERE UserID=?", (user_id,)):
            return "student"
        if self.db.query_one("SELECT 1 FROM Lecturer WHERE UserID=?", (user_id,)):
            return "lecturer"
        if self.db.query_one("SELECT 1 FROM Administrator WHERE UserID=?", (user_id,)):
            return "admin"
        return "unknown"
