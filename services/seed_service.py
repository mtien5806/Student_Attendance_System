from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TypedDict

from Database.database import Database
from models.admin import Administrator
from models.lecturer import Lecturer
from models.student import Student
from models.system import System
from models.user import User


class _DemoUser(TypedDict):
    role: str 
    full_name: str
    username: str
    password: str
    email: str
    role_id: str           
    major_name: Optional[str]


@dataclass
class SeedService:
    db: Database


    DEMO_USERS: list[_DemoUser] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.DEMO_USERS is None:
            self.DEMO_USERS = [
                {
                    "role": "admin",
                    "full_name": "Admin User",
                    "username": "admin",
                    "password": "admin@123",
                    "email": "admin@ut.edu.vn",
                    "role_id": "AD001",
                    "major_name": None,
                },
                {
                    "role": "lecturer",
                    "full_name": "Nguyen Van A",
                    "username": "NguyenVanA",
                    "password": "A@123",
                    "email": "A@ut.edu.vn",
                    "role_id": "NVA001",
                    "major_name": None,
                },
                {
                    "role": "student",
                    "full_name": "Vo Minh Tien",
                    "username": "Minh_Tien",
                    "password": "tien@123",
                    "email": "tien@ut.edu.vn",
                    "role_id": "STU001",
                    "major_name": "Software Engineering",
                },
                {
                    "role": "student",
                    "full_name": "Vo Thai Bao",
                    "username": "Thai_Bao",
                    "password": "bao@123",
                    "email": "bao@ut.edu.vn",
                    "role_id": "STU002",
                    "major_name": "Software Engineering",
                },
                {
                    "role": "student",
                    "full_name": "Le Trung Hau",
                    "username": "Trung_Hau",
                    "password": "hau@123",
                    "email": "hau@ut.edu.vn",
                    "role_id": "STU003",
                    "major_name": "Software Engineering",
                },
                {
                    "role": "student",
                    "full_name": "Y Cam Hao",
                    "username": "Cam_Hao",
                    "password": "hao@123",
                    "email": "hao@ut.edu.vn",
                    "role_id": "STU004",
                    "major_name": "Software Engineering",
                },
            ]

    def seed_demo(self, *, reset: bool = False) -> bool:
        System("SAS").save(self.db)

        if reset:
            self._reset_all_data()

        for u in self.DEMO_USERS:
            self._upsert_user(u)

        return True

    def get_demo_credentials(self) -> list[tuple[str, str]]:
        """Dùng cho ui.seed để in ra tài khoản demo đúng 100%."""
        return [(u["username"], u["password"]) for u in self.DEMO_USERS]

   
    def _upsert_user(self, info: _DemoUser) -> None:
        existing = User.load_by_username(self.db, info["username"])
        user_id = existing.user_id if existing else None

        role = info["role"].lower().strip()

        if role == "admin":
            admin = Administrator.create(
                full_name=info["full_name"],
                username=info["username"],
                password=info["password"],
                email=info["email"],
                user_id=user_id,
            )
            admin.admin_id = info["role_id"]
            admin.save(self.db)
            return

        if role == "lecturer":
            lec = Lecturer.create(
                full_name=info["full_name"],
                username=info["username"],
                password=info["password"],
                email=info["email"],
                user_id=user_id,
            )
            lec.lecturer_id = info["role_id"]
            lec.save(self.db)
            return

        if role == "student":
            stu = Student.create(
                full_name=info["full_name"],
                username=info["username"],
                password=info["password"],
                email=info["email"],
                user_id=user_id,
            )
            stu.student_id = info["role_id"]
            stu.major_name = info["major_name"]
            stu.save(self.db)
            return

        raise ValueError(f"Unknown role in seed data: {info['role']}")

    def _reset_all_data(self) -> None:
     
      
        for table in [
            "AttendanceRecord",
            "LeaveRequest",
            "Warning",
            "AttendanceSession",
            "Student",
            "Lecturer",
            "Administrator",
            "User",
        ]:
            try:
                self.db.execute(f"DELETE FROM {table}")
            except Exception:
                pass
