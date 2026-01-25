from __future__ import annotations

from Database.database import Database
from services.seed_service import SeedService


class Seeder:
    def __init__(self, db: Database) -> None:
        self.db = db

    def run(self) -> None:
        ok = SeedService(self.db).seed_demo()
        if ok:
            print(" Seed demo data thành công.")
            print("   admin / admin123")
            print("   lec1  / lec123")
            print("   stu1  / stu123")
        else:
            print("Demo data already exists (username 'admin' found).")
