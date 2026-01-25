from __future__ import annotations

from dataclasses import dataclass

from Database.database import Database
from models.admin import Administrator
from ui.common import ConsoleIO, Table, DASH
from services.attendance_service import AttendanceService


@dataclass
class AdminUI:
    db: Database
    admin: Administrator

    def run(self) -> None:
        service = AttendanceService(self.db)
        while True:
            ConsoleIO.screen("ADMINISTRATOR DASHBOARD")
            print(f"User: {self.admin.full_name} (ID: {self.admin.admin_id})")
            print(DASH)
            print("1. Search Attendance")
            print("2. Manage Attendance")
            print("0. Logout")
            print(DASH)
            choice = ConsoleIO.ask("Selection: ")

            if choice == "1":
                self.search_attendance(service)
            elif choice == "2":
                self.manage_attendance(service)
            elif choice == "0":
                return
            else:
                ConsoleIO.invalid_menu()

    def search_attendance(self, service: AttendanceService) -> None:
        ConsoleIO.screen("SEARCH ATTENDANCE")
        print("Search by: 1. StudentID  2. SessionID  3. Course/Class  4. Date Range")
        sel = ConsoleIO.ask("Selection: ")
        by_map = {"1": "student_id", "2": "session_id", "3": "class_name", "4": "date_range"}
        by = by_map.get(sel)
        if not by:
            ConsoleIO.invalid_menu()
            return

        keyword = ""
        dr_start = dr_end = None
        if by != "date_range":
            keyword = ConsoleIO.ask("Enter keyword/value: ")
        else:
            dr = ConsoleIO.ask_date_range()
            dr_start, dr_end = dr.start, dr.end

        rows = service.search_attendance_records(by=by, keyword=keyword, date_from=dr_start, date_to=dr_end)
        print(DASH)
        if not rows:
            print("(No matching records.)")
            return
        table_rows = []
        for r in rows[:80]:
            table_rows.append([r["SessionID"], r["Date"], r["ClassName"], r["StudentID"], r["Status"]])
        Table(headers=["SessionID", "Date", "Course/Class", "StudentID", "Status"], rows=table_rows).render()

    def manage_attendance(self, service: AttendanceService) -> None:
        ConsoleIO.screen("MANAGE ATTENDANCE")
        while True:
            print("Actions:")
            print("1. Add missing attendance record")
            print("2. Edit attendance status")
            print("3. Delete duplicated/incorrect record")
            print("0. Back")
            print(DASH)
            choice = ConsoleIO.ask("Selection: ")

            if choice == "1":
                self._add_or_edit(service, create_missing=True)
            elif choice == "2":
                self._add_or_edit(service, create_missing=False)
            elif choice == "3":
                self._delete_record(service)
            elif choice == "0":
                return
            else:
                ConsoleIO.invalid_menu()

    def _add_or_edit(self, service: AttendanceService, *, create_missing: bool) -> None:
        session_id = ConsoleIO.ask("Enter Session ID: ")
        student_id = ConsoleIO.ask("Enter Student ID: ")

        print("New Status: 1. Present  2. Late  3. Absent  4. Excused")
        s_choice = ConsoleIO.ask("Selection: ")
        mapping = {"1": "Present", "2": "Late", "3": "Absent", "4": "Excused"}
        status = mapping.get(s_choice)
        if not status:
            ConsoleIO.invalid_menu()
            return
        note = ConsoleIO.ask("Reason/Note: ", allow_blank=True) or None
        if not ConsoleIO.confirm("Confirm (Y/N): "):
            return

        ok, msg = service.update_student_status(
            session_id=session_id,
            student_id=student_id,
            status=status,
            note=note,
            create_if_missing=create_missing,
        )

        print(msg)

    def _delete_record(self, service: AttendanceService) -> None:
        session_id = ConsoleIO.ask("Enter Session ID: ")
        student_id = ConsoleIO.ask("Enter Student ID: ")
        if not ConsoleIO.confirm("Confirm (Y/N): "):
            return
        ok, msg = service.delete_attendance_record(session_id=session_id, student_id=student_id)
        print(msg)
