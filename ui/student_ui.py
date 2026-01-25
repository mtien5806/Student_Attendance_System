from __future__ import annotations

from dataclasses import dataclass

from Database.database import Database
from models.student import Student
from ui.common import ConsoleIO, Table, DASH
from services.attendance_service import AttendanceService


@dataclass
class StudentUI:
    db: Database
    student: Student

    def run(self) -> None:
        service = AttendanceService(self.db)
        while True:
            warnings = service.count_warnings(self.student.user_id)
            pending = service.count_pending_requests_for_student(self.student.user_id)

            ConsoleIO.screen("STUDENT DASHBOARD")
            print(f"User: {self.student.full_name} (ID: {self.student.student_id})")
            print(f"Warnings: {warnings} | Pending Requests: {pending}")
            print(DASH)
            print("1. Take Attendance (Check-in)")
            print("2. View Attendance")
            print("3. Submit Absence/Late Request")
            print("4. View Attendance Warnings")
            print("0. Logout")
            print(DASH)
            choice = ConsoleIO.ask("Selection: ")

            if choice == "1":
                self.take_attendance(service)
            elif choice == "2":
                self.view_attendance(service)
            elif choice == "3":
                self.submit_request(service)
            elif choice == "4":
                self.view_warnings()
            elif choice == "0":
                return
            else:
                ConsoleIO.invalid_menu()

    def take_attendance(self, service: AttendanceService) -> None:
        ConsoleIO.screen("TAKE ATTENDANCE")
        session_id = ConsoleIO.ask("Enter Session ID: ")
        pin = ConsoleIO.ask_pin("Enter PIN (if required): ", allow_blank=True)
        ok, msg = service.student_check_in(
            student_user_id=self.student.user_id,
            session_id=session_id,
            pin=pin if pin else None,
        )
        print(DASH)
        print(msg)

    def view_attendance(self, service: AttendanceService) -> None:
        ConsoleIO.screen("VIEW ATTENDANCE")
        class_id = ConsoleIO.ask("Enter Course/Class ID (or leave blank to list all): ", allow_blank=True) or None
        dr = ConsoleIO.ask_date_range()
        items, summary = service.view_attendance(
            student_user_id=self.student.user_id,
            class_name=class_id,
            date_from=dr.start,
            date_to=dr.end,
        )
        print(DASH)
        if not items:
            print("(No attendance records found.)")
            return

        rows = []
        for r in items:
            rows.append([r["SessionID"], r["Date"], r["Time"], r["Status"], r["Note"]])
        Table(
            headers=["SessionID", "Date", "Time", "Status", "Note"],
            rows=rows,
        ).render()
        print(DASH)
        print(
            f"Summary: Present={summary.get('Present',0)}, Late={summary.get('Late',0)}, "
            f"Absent={summary.get('Absent',0)}"
        )

    def submit_request(self, service: AttendanceService) -> None:
        ConsoleIO.screen("SUBMIT REQUEST")
        session_id = ConsoleIO.ask("Enter Session ID: ")
        print("Request Type: 1. Absent   2. Late")
        t = ConsoleIO.ask("Selection: ")
        request_type = "Absent" if t == "1" else "Late" if t == "2" else ""
        if not request_type:
            ConsoleIO.invalid_menu()
            return
        reason = ConsoleIO.ask("Reason (text): ")
        evidence = ConsoleIO.ask("Optional Evidence File Path (leave blank if none): ", allow_blank=True) or None
        if not ConsoleIO.confirm("Confirm submission (Y/N): "):
            return
        ok, msg = service.submit_request(
            student_user_id=self.student.user_id,
            session_id=session_id,
            request_type=request_type,
            reason=reason,
            evidence_path=evidence,
        )
        print(DASH)
        print(msg)

    def view_warnings(self) -> None:
        ConsoleIO.screen("WARNINGS")
        rows = self.db.query_all(
            """
            SELECT WarningID, createdAt, className, message
            FROM Warning
            WHERE StudentUserID=?
            ORDER BY createdAt DESC
            """,
            (self.student.user_id,),
        )
        print(DASH)
        if not rows:
            print("(No warnings.)")
            return
        table_rows = [[r["WarningID"], r["createdAt"][:10], r["className"] or "", r["message"]] for r in rows]
        Table(headers=["WarningID", "Date", "Course/Class", "Message"], rows=table_rows).render()
