"""Domain models for the Student Attendance System (SAS).

At this stage, we only implement:
- Class structure (matching the class diagram)
- Persistence methods to/from SQLite (matching the ERD)

Higher-level workflows / console menus will be added later.
"""

from .user import User
from .student import Student
from .lecturer import Lecturer
from .admin import Administrator
from .system import System
from .warning import Warning
from .attendanceSession import AttendanceSession
from .attendanceRecord import AttendanceRecord
from .leaveRequest import LeaveRequest
from .attendanceReport import AttendanceReport

__all__ = [
    "User",
    "Student",
    "Lecturer",
    "Administrator",
    "System",
    "Warning",
    "AttendanceSession",
    "AttendanceRecord",
    "LeaveRequest",
    "AttendanceReport",
]
