from __future__ import annotations

import sys

from Database.database import Database
from ui.auth_router import AuthRouter
from ui.seed import Seeder


def main() -> None:
    import os
    db_path = os.path.join(os.path.dirname(__file__), "sas.db")
    db = Database(db_path)

    db.initialize()
    db.ensure_schema_extras()

    if "--seed" in sys.argv:
        Seeder(db).run()
        db.close()
        return

    AuthRouter(db).run()


if __name__ == "__main__":
    main()
