from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Optional

from Database.database import Database, verify_password
from models.user import User

Role = Literal["student", "lecturer", "admin", "unknown"]


def _parse_iso(dt_s: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(dt_s)
    except Exception:
        return None


def _utc_now() -> datetime:
    return datetime.utcnow().replace(microsecond=0)


@dataclass
class AuthService:
    db: Database

    
    last_error: Optional[str] = None       
    locked_until: Optional[str] = None       
    remaining_seconds: Optional[int] = None  

    def login(self, username: str, password: str) -> Optional[User]:
        """
        - Nếu sai >= 5 lần liên tiếp => khóa 5 phút.
        - Nếu đang bị khóa => không cho login dù đúng password.
        """
        self.last_error = None
        self.locked_until = None
        self.remaining_seconds = None

        row = self.db.query_one(
            "SELECT UserID, password, failedAttempts, lockUntil FROM User WHERE username=?",
            (username,),
        )
        if not row:
            self.last_error = "INVALID"
            return None

        user_id = row["UserID"]
        lock_until_s = row["lockUntil"] if "lockUntil" in row.keys() else None
        if lock_until_s:
            lock_dt = _parse_iso(lock_until_s)
            if lock_dt is not None:
                now = _utc_now()
                if now < lock_dt:
                    self.last_error = "LOCKED"
                    self.locked_until = lock_until_s
                    self.remaining_seconds = int((lock_dt - now).total_seconds())
                    return None
            else:
                self.db.execute("UPDATE User SET lockUntil=NULL WHERE UserID=?", (user_id,))

        ok = verify_password(password, row["password"])
        if ok:
            self.db.execute(
                "UPDATE User SET failedAttempts=0, lockUntil=NULL WHERE UserID=?",
                (user_id,),
            )
            return User.load_by_id(self.db, user_id)

        # login sai
        failed = int(row["failedAttempts"] or 0) + 1

        if failed >= 5:
            lock_dt = _utc_now() + timedelta(minutes=5)
            lock_until_s = lock_dt.isoformat(sep=" ")
            self.db.execute(
                "UPDATE User SET failedAttempts=?, lockUntil=? WHERE UserID=?",
                (failed, lock_until_s, user_id),
            )
            self.last_error = "LOCKED"
            self.locked_until = lock_until_s
            self.remaining_seconds = int((lock_dt - _utc_now()).total_seconds())
            return None

        
        self.db.execute(
            "UPDATE User SET failedAttempts=? WHERE UserID=?",
            (failed, user_id),
        )
        self.last_error = "INVALID"
        return None

    def detect_role(self, user_id: str) -> Role:
        if self.db.query_one("SELECT 1 FROM Student WHERE UserID=?", (user_id,)):
            return "student"
        if self.db.query_one("SELECT 1 FROM Lecturer WHERE UserID=?", (user_id,)):
            return "lecturer"
        if self.db.query_one("SELECT 1 FROM Administrator WHERE UserID=?", (user_id,)):
            return "admin"
        return "unknown"
