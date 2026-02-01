from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Database.database import Database
from models.admin import Administrator
from models.lecturer import Lecturer
from models.student import Student
from models.user import User
from ui.common import ConsoleIO, TITLE_BAR, DASH
from services.auth_service import AuthService


@dataclass
class AuthRouter:
    db: Database

    def run(self) -> None:
        while True:
            ConsoleIO.header("STUDENT ATTENDANCE SYSTEM")
            print("1. Login")
            print("2. Exit")
            print("-" * 50)
            sel = ConsoleIO.ask("Selection: ")

            if sel == "1":
                user = self._login_flow()
                if user:
                    self._route(user)
            elif sel == "2":
                raise SystemExit(0)
            else:
                ConsoleIO.invalid_menu()

    def _login_flow(self) -> Optional[User]:
        ConsoleIO.screen("LOGIN")
        auth = AuthService(self.db)

        while True:
            username = ConsoleIO.ask("Username (0 to cancel): ")
            if username == "0":
                return None

            password = ConsoleIO.ask_password("Password: ")
            print("-" * 50)

            user = auth.login(username, password)
            if user:
                return user

            if auth.last_error == "LOCKED":
                if auth.remaining_seconds is not None:
                    mins = max(1, (auth.remaining_seconds + 59) // 60)
                    print(f"Account locked. Please try again after ~{mins} minute(s).")
                else:
                    print("Account locked. Please try again later.")
                return None

            print("Username or password is incorrect.")


    def _route(self, user: User) -> None:
        role = AuthService(self.db).detect_role(user.user_id)
        if role == "student":
            s = Student.load_by_user_id(self.db, user.user_id)
            from ui.student_ui import StudentUI
            StudentUI(self.db, s).run()  # type: ignore[arg-type]
            return
        if role == "lecturer":
            l = Lecturer.load_by_user_id(self.db, user.user_id)
            from ui.lecturer_ui import LecturerUI
            LecturerUI(self.db, l).run()  # type: ignore[arg-type]
            return
        if role == "admin":
            a = Administrator.load_by_user_id(self.db, user.user_id)
            from ui.admin_ui import AdminUI
            AdminUI(self.db, a).run()  # type: ignore[arg-type]
            return

      
        ConsoleIO.screen("USER")
        print(f"User: {user.full_name} (ID: {user.user_id})")
        print(DASH)
        ConsoleIO.ask("Press Enter to logout...", allow_blank=True)
