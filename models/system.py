from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database, utc_now_iso
from models.warning import Warning
from services.id_generator import IdGenerator


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

    def send_warning(
        self,
        db: Database,
        *,
        student_user_id: str,
        class_name: Optional[str],
        message: str,
    ) -> Warning:
        """Create and persist a warning for a student.

        Uses W### style IDs via IdGenerator (consistent with spec 8.5.4).
        """
        self.save(db)
        wid = IdGenerator(db).next_id("W", "Warning", "WarningID", width=3)
        warning = Warning(
            warning_id=wid,
            student_user_id=student_user_id,
            system_name=self.system_name,
            class_name=class_name,
            message=message,
            created_at=utc_now_iso(),
        )
        warning.save(db)
        return warning
