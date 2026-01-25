from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database, new_uuid, utc_now_iso


@dataclass
class AttendanceReport:
    report_id: str
    managed_by_admin_user_id: Optional[str] = None
    summarized_by_lecturer_user_id: Optional[str] = None
    file_name: Optional[str] = None
    created_at: str = ""
    title: Optional[str] = None

    @classmethod
    def create(
        cls,
        *,
        title: Optional[str] = None,
        file_name: Optional[str] = None,
        managed_by_admin_user_id: Optional[str] = None,
        summarized_by_lecturer_user_id: Optional[str] = None,
    ) -> "AttendanceReport":
        return cls(
            report_id=new_uuid(),
            managed_by_admin_user_id=managed_by_admin_user_id,
            summarized_by_lecturer_user_id=summarized_by_lecturer_user_id,
            file_name=file_name,
            created_at=utc_now_iso(),
            title=title,
        )

    def save(self, db: Database) -> None:
        db.execute(
            """
            INSERT INTO AttendanceReport (
                ReportID, ManagedByAdminUserID, SummarizedByLecturerUserID, fileName, createdAt, title
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(ReportID) DO UPDATE SET
                ManagedByAdminUserID=excluded.ManagedByAdminUserID,
                SummarizedByLecturerUserID=excluded.SummarizedByLecturerUserID,
                fileName=excluded.fileName,
                createdAt=excluded.createdAt,
                title=excluded.title
            """,
            (
                self.report_id,
                self.managed_by_admin_user_id,
                self.summarized_by_lecturer_user_id,
                self.file_name,
                self.created_at,
                self.title,
            ),
        )

    @classmethod
    def load_by_id(cls, db: Database, report_id: str) -> Optional["AttendanceReport"]:
        row = db.query_one("SELECT * FROM AttendanceReport WHERE ReportID=?", (report_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def from_row(cls, row) -> "AttendanceReport":
        return cls(
            report_id=row["ReportID"],
            managed_by_admin_user_id=row["ManagedByAdminUserID"],
            summarized_by_lecturer_user_id=row["SummarizedByLecturerUserID"],
            file_name=row["fileName"],
            created_at=row["createdAt"],
            title=row["title"],
        )


    def generate(self, session_id: str) -> None:
        raise NotImplementedError("Will be implemented with summary/export workflows")

    def export_to_excel(self) -> None:
        raise NotImplementedError("Will be implemented with Excel export")
