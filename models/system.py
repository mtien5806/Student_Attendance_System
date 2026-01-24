from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database, new_uuid, utc_now_iso
from models.warning import Warning


@dataclass
class System:
    """Represents the system actor that can generate warnings."""

    system_name: str

    def save(self, db: Database) -> None:
        db.execute(
            """
            INSERT INTO System (SystemName)
            VALUES (?)
            ON CONFLICT(SystemName) DO NOTHING
            """,
            (self.system_name,),
        )

    @classmethod
    def load(cls, db: Database, system_name: str) -> Optional["System"]:
        row = db.query_one("SELECT SystemName FROM System WHERE SystemName=?", (system_name,))
        return cls(system_name=row["SystemName"]) if row else None

    def send_warning(self, db: Database, *, student_user_id: str, message: str) -> Warning:
        """Create and persist a warning for a student."""
        self.save(db)
        warning = Warning(
            warning_id=new_uuid(),
            student_user_id=student_user_id,
            system_name=self.system_name,
            message=message,
            created_at=utc_now_iso(),
        )
        warning.save(db)
        return warning
