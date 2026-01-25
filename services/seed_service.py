from __future__ import annotations

from dataclasses import dataclass

from Database.database import Database
from models.admin import Administrator
from models.lecturer import Lecturer
from models.student import Student
from models.system import System
from models.user import User


@dataclass
class SeedService:
    db: Database

    def seed_demo(self) -> bool:
        System("SAS").save(self.db)

        if User.load_by_username(self.db, "admin"):
            return False

        admin_user = Administrator.create(
            full_name="Admin User",
            username="admin",
            password="admin123",
            email="admin@sas.local",
        )
        admin_user.admin_id = "AD001"
        admin_user.save(self.db)

        lec_user = Lecturer.create(
            full_name="Lecturer One",
            username="lec1",
            password="lec123",
            email="lec1@sas.local",
        )
        lec_user.lecturer_id = "LEC001"
        lec_user.save(self.db)

        stu_user = Student.create(
            full_name="Student One",
            username="stu1",
            password="stu123",
            email="stu1@sas.local",
        )
        stu_user.student_id = "STU001"
        stu_user.major_name = "Software Engineering"
        stu_user.save(self.db)

        return True
