from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database, utc_now_iso


@dataclass
class LeaveRequest:
   

    request_id: str  
    student_user_id: str
    lecturer_user_id: str
    session_id: Optional[str]
    request_type: str 
    status: str 
    reason: str
    evidence_path: Optional[str] = None
    note: Optional[str] = None
    created_at: str = ""

    @classmethod
    def create(
        cls,
        *,
        request_id: str,
        student_user_id: str,
        lecturer_user_id: str,
        session_id: Optional[str],
        request_type: str,
        reason: str,
        status: str = "PENDING",
        evidence_path: Optional[str] = None,
        note: Optional[str] = None,
    ) -> "LeaveRequest":
        return cls(
            request_id=request_id,
            student_user_id=student_user_id,
            lecturer_user_id=lecturer_user_id,
            session_id=session_id,
            request_type=request_type,
            status=status,
            reason=reason,
            evidence_path=evidence_path,
            note=note,
            created_at=utc_now_iso(),
        )

    def save(self, db: Database) -> None:
        db.execute(
            """
            INSERT INTO LeaveRequest (
                RequestID, StudentUserID, LecturerUserID, SessionID, type, status, reason, evidencePath, note, createdAt
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(RequestID) DO UPDATE SET
                StudentUserID=excluded.StudentUserID,
                LecturerUserID=excluded.LecturerUserID,
                SessionID=excluded.SessionID,
                type=excluded.type,
                status=excluded.status,
                reason=excluded.reason,
                evidencePath=excluded.evidencePath,
                note=excluded.note,
                createdAt=excluded.createdAt
            """,
            (
                self.request_id,
                self.student_user_id,
                self.lecturer_user_id,
                self.session_id,
                self.request_type,
                self.status,
                self.reason,
                self.evidence_path,
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
        def _col(*names: str, default=None):
            for name in names:
                try:
                    v = row[name]
                    if v is not None:
                        return v
                except Exception:
                    pass
            return default

        req_type = _col("type", "request_type", "RequestType", default="Absent")
        req_type = str(req_type)  

        return cls(
            request_id=str(_col("RequestID", "request_id", default="")),
            student_user_id=str(_col("StudentUserID", "student_user_id", default="")),
            lecturer_user_id=str(_col("LecturerUserID", "lecturer_user_id", default="")),
            session_id=_col("SessionID", "session_id", default=None),
            request_type=req_type, 
            status=str(_col("status", default="PENDING")),
            reason=str(_col("reason", default="")),
            evidence_path=_col("evidencePath", "evidence_path", default=None),
            note=_col("note", default=None),
            created_at=str(_col("createdAt", "created_at", default="")),
        )

 

    def set_status(self, db: Database, status: str, *, note: Optional[str] = None) -> None:
        self.status = status
        if note is not None:
            self.note = note
        self.save(db)
    