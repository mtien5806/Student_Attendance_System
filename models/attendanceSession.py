from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database, utc_now_iso


@dataclass
class AttendanceSession:
   

    session_id: str
    lecturer_user_id: str
    date: str  
    class_name: str
    status: str 
    created_at: str 

   
    start_time: Optional[str] = None 
    duration_minutes: Optional[int] = None
    require_pin: bool = False
    pin: Optional[str] = None

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        lecturer_user_id: str,
        class_name: str,
        date: str,
        start_time: Optional[str],
        duration_minutes: Optional[int],
        require_pin: bool,
        pin: Optional[str],
        status: str = "OPEN",
    ) -> "AttendanceSession":
        return cls(
            session_id=session_id,
            lecturer_user_id=lecturer_user_id,
            date=date,
            class_name=class_name,
            status=status,
            created_at=utc_now_iso(),
            start_time=start_time,
            duration_minutes=duration_minutes,
            require_pin=require_pin,
            pin=pin,
        )

    def save(self, db: Database) -> None:
        db.execute(
            """
            INSERT INTO AttendanceSession (
                SessionID, LecturerUserID, date, className, status, createdAt,
                startTime, durationMinutes, requirePIN, pin
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(SessionID) DO UPDATE SET
                LecturerUserID=excluded.LecturerUserID,
                date=excluded.date,
                className=excluded.className,
                status=excluded.status,
                createdAt=excluded.createdAt,
                startTime=excluded.startTime,
                durationMinutes=excluded.durationMinutes,
                requirePIN=excluded.requirePIN,
                pin=excluded.pin
            """,
            (
                self.session_id,
                self.lecturer_user_id,
                self.date,
                self.class_name,
                self.status,
                self.created_at,
                self.start_time,
                self.duration_minutes,
                1 if self.require_pin else 0,
                self.pin,
            ),
        )

    @classmethod
    def load_by_id(cls, db: Database, session_id: str) -> Optional["AttendanceSession"]:
        row = db.query_one("SELECT * FROM AttendanceSession WHERE SessionID=?", (session_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_by_lecturer(cls, db: Database, lecturer_user_id: str) -> list["AttendanceSession"]:
        rows = db.query_all(
            "SELECT * FROM AttendanceSession WHERE LecturerUserID=? ORDER BY createdAt DESC",
            (lecturer_user_id,),
        )
        return [cls.from_row(r) for r in rows]

    @classmethod
    def from_row(cls, row) -> "AttendanceSession":
        def _col(name: str, default=None):
            try:
                return row[name]
            except Exception:
                return default

        return cls(
            session_id=row["SessionID"],
            lecturer_user_id=row["LecturerUserID"],
            date=row["date"],
            class_name=row["className"],
            status=row["status"],
            created_at=row["createdAt"],
            start_time=_col("startTime"),
            duration_minutes=_col("durationMinutes"),
            require_pin=bool(_col("requirePIN", 0) or 0),
            pin=_col("pin"),
        )

    def close(self, db: Database) -> None:
        self.status = "CLOSED"
        self.save(db)
