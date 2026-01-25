from __future__ import annotations

from dataclasses import dataclass

from Database.database import Database


@dataclass
class IdGenerator:
    """Generates human-friendly IDs like S001, R012, W003.

    Stored IDs are TEXT, so this generator scans existing IDs and increments.
    """

    db: Database

    def next_id(self, prefix: str, table: str, column: str, *, width: int = 3) -> str:
        row = self.db.query_one(
            f"SELECT {column} AS id FROM {table} WHERE {column} LIKE ? ORDER BY {column} DESC LIMIT 1",
            (f"{prefix}%",),
        )
        if not row or not row["id"]:
            return f"{prefix}{'1'.zfill(width)}"
        last = str(row["id"])
        num = 0
        try:
            num = int(last.replace(prefix, ""))
        except Exception:
            num = 0
        return f"{prefix}{str(num + 1).zfill(width)}"
