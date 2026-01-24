from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database, new_uuid, utc_now_iso


@dataclass
class LeaveRequest:
    request_id: str
    student_user_id: str
    lecturer_user_id: str
    status: str  # PENDING/APPROVED/REJECTED
    reason: str
    note: Optional[str] = None
    created_at: str = ""

    @classmethod
    def create(
        cls,
        *,
        student_user_id: str,
        lecturer_user_id: str,
        reason: str,
        status: str = "PENDING",
        note: Optional[str] = None,
    ) -> "LeaveRequest":
        return cls(
            request_id=new_uuid(),
            student_user_id=student_user_id,
            lecturer_user_id=lecturer_user_id,
            status=status,
            reason=reason,
            note=note,
            created_at=utc_now_iso(),
        )

    def save(self, db: Database) -> None:
        db.execute(
            """
            INSERT INTO LeaveRequest (RequestID, StudentUserID, LecturerUserID, status, reason, note, createdAt)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(RequestID) DO UPDATE SET
                StudentUserID=excluded.StudentUserID,
                LecturerUserID=excluded.LecturerUserID,
                status=excluded.status,
                reason=excluded.reason,
                note=excluded.note,
                createdAt=excluded.createdAt
            """,
            (
                self.request_id,
                self.student_user_id,
                self.lecturer_user_id,
                self.status,
                self.reason,
                self.note,
                self.created_at,
            ),
        )

    @classmethod
    def load_by_id(cls, db: Database, request_id: str) -> Optional["LeaveRequest"]:
        row = db.query_one("SELECT * FROM LeaveRequest WHERE RequestID=?", (request_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_for_student(cls, db: Database, student_user_id: str) -> list["LeaveRequest"]:
        rows = db.query_all(
            "SELECT * FROM LeaveRequest WHERE StudentUserID=? ORDER BY createdAt DESC",
            (student_user_id,),
        )
        return [cls.from_row(r) for r in rows]

    @classmethod
    def list_for_lecturer(cls, db: Database, lecturer_user_id: str, *, pending_only: bool = False) -> list["LeaveRequest"]:
        if pending_only:
            rows = db.query_all(
                """
                SELECT * FROM LeaveRequest
                WHERE LecturerUserID=? AND status='PENDING'
                ORDER BY createdAt DESC
                """,
                (lecturer_user_id,),
            )
        else:
            rows = db.query_all(
                "SELECT * FROM LeaveRequest WHERE LecturerUserID=? ORDER BY createdAt DESC",
                (lecturer_user_id,),
            )
        return [cls.from_row(r) for r in rows]

    @classmethod
    def from_row(cls, row) -> "LeaveRequest":
        return cls(
            request_id=row["RequestID"],
            student_user_id=row["StudentUserID"],
            lecturer_user_id=row["LecturerUserID"],
            status=row["status"],
            reason=row["reason"],
            note=row["note"],
            created_at=row["createdAt"],
        )

    def set_status(self, db: Database, status: str) -> None:
        self.status = status
        self.save(db)
