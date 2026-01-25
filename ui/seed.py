from __future__ import annotations

import sys

from Database.database import Database
from services.seed_service import SeedService


class Seeder:
    def __init__(self, db: Database) -> None:
        self.db = db

    def run(self) -> None:
        reset = "--reset" in sys.argv

        svc = SeedService(self.db)
        svc.seed_demo(reset=reset)

        print("Seed demo data thành công.")
        if reset:
            print("(Database đã được reset trước khi seed.)")

        for username, password in svc.get_demo_credentials():
            print(f"  {username} / {password}")
