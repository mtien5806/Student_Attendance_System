from __future__ import annotations

import sys

from Database.database import Database
from console_ui import (
    bootstrap_message_if_empty,
    login_flow,
    role_menu_router,
    seed_demo_data,
)


def main() -> None:
    db = Database("sas.db")
    db.initialize()

    if "--seed" in sys.argv:
        seed_demo_data(db)
        db.close()
        return

    bootstrap_message_if_empty(db)

    user = login_flow(db, max_attempts=5)
    if not user:
        db.close()
        return

    role_menu_router(db, user)
    db.close()


if __name__ == "__main__":
    main()
