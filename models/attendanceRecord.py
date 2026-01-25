from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database, new_uuid, utc_now_iso


@dataclass
class AttendanceRecord:
    record_id: str
    session_id: str
    student_user_id: str
    status: str  
    check_time: Optional[str] = None
    note: Optional[str] = None
    updated_at: str = ""

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        student_user_id: str,
        status: str,
        check_time: Optional[str] = None,
        note: Optional[str] = None,
    ) -> "AttendanceRecord":
        return cls(
            record_id=new_uuid(),
            session_id=session_id,
            student_user_id=student_user_id,
            status=status,
            check_time=check_time,
            note=note,
            updated_at=utc_now_iso(),
        )

    def save(self, db: Database) -> None:
        db.execute(
            """
            INSERT INTO AttendanceRecord (RecordID, SessionID, StudentUserID, status, checkTime, note, updatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(RecordID) DO UPDATE SET
                SessionID=excluded.SessionID,
                StudentUserID=excluded.StudentUserID,
                status=excluded.status,
                checkTime=excluded.checkTime,
                note=excluded.note,
                updatedAt=excluded.updatedAt
            """,
            (
                self.record_id,
                self.session_id,
                self.student_user_id,
                self.status,
                self.check_time,
                self.note,
                self.updated_at,
            ),
        )

    @classmethod
    def load_by_id(cls, db: Database, record_id: str) -> Optional["AttendanceRecord"]:
        row = db.query_one("SELECT * FROM AttendanceRecord WHERE RecordID=?", (record_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def load_by_session_and_student(
        cls, db: Database, *, session_id: str, student_user_id: str
    ) -> Optional["AttendanceRecord"]:
        row = db.query_one(
            "SELECT * FROM AttendanceRecord WHERE SessionID=? AND StudentUserID=?",
            (session_id, student_user_id),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def list_for_session(cls, db: Database, session_id: str) -> list["AttendanceRecord"]:
        rows = db.query_all("SELECT * FROM AttendanceRecord WHERE SessionID=?", (session_id,))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def from_row(cls, row) -> "AttendanceRecord":
        return cls(
            record_id=row["RecordID"],
            session_id=row["SessionID"],
            student_user_id=row["StudentUserID"],
            status=row["status"],
            check_time=row["checkTime"],
            note=row["note"],
            updated_at=row["updatedAt"],
        )

    def update_status(self, db: Database, status: str) -> None:
        self.status = status
        self.updated_at = utc_now_iso()
        self.save(db)
