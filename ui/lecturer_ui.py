from __future__ import annotations

from dataclasses import dataclass

from Database.database import Database
from models.lecturer import Lecturer
from ui.common import ConsoleIO, Table, DASH
from services.attendance_service import AttendanceService


@dataclass
class LecturerUI:
    db: Database
    lecturer: Lecturer

    def run(self) -> None:
        service = AttendanceService(self.db)
        while True:
            pending = service.count_pending_requests_for_lecturer(self.lecturer.user_id)

            ConsoleIO.screen("LECTURER DASHBOARD")
            print(f"User: {self.lecturer.full_name} (ID: {self.lecturer.lecturer_id})")
            print(f"Pending Requests: {pending}")
            print(DASH)
            print("1. Create Attendance Session")
            print("2. Record Attendance")
            print("3. Approve/Reject Absence/Late Requests")
            print("4. Summarize Attendance")
            print("5. Export Attendance Report (Excel)")
            print("0. Logout")
            print(DASH)
            choice = ConsoleIO.ask("Selection: ")

            if choice == "1":
                self.create_session(service)
            elif choice == "2":
                self.record_attendance(service)
            elif choice == "3":
                self.process_requests(service)
            elif choice == "4":
                self.summarize(service)
            elif choice == "5":
                self.export_report(service)
            elif choice == "0":
                return
            else:
                ConsoleIO.invalid_menu()

    def create_session(self, service: AttendanceService) -> None:
        ConsoleIO.screen("CREATE SESSION")
        class_name = ConsoleIO.ask("Enter Course/Class ID: ")
        date = ConsoleIO.ask_date("Session Date (YYYY-MM-DD): ")
        start_time = ConsoleIO.ask_time("Start Time (HH:MM): ")
        duration = ConsoleIO.ask_int("Duration (minutes): ", min_value=1, max_value=600)
        require_pin = ConsoleIO.confirm("Require PIN? (Y/N): ")
        pin = None
        if require_pin:
            p = ConsoleIO.ask_pin(
                "If Yes, enter PIN (4–6 digits) or leave blank to auto-generate: ",
                allow_blank=True,
            )
            pin = p if p else None

        # auto generate pin if required and not provided
        if require_pin and not pin:
            import random
            pin = str(random.randint(1000, 999999))

        session = service.create_session(
            lecturer_user_id=self.lecturer.user_id,
            class_name=class_name,
            date=date,
            start_time=start_time,
            duration_minutes=duration,
            require_pin=require_pin,
            pin=pin,
        )

        print(DASH)
        print("Session created successfully.")
        print(f"Session ID: {session.session_id}")
        if require_pin:
            print(f"PIN (if enabled): {session.pin}")
        print("Status: OPEN")

    def record_attendance(self, service: AttendanceService) -> None:
        ConsoleIO.screen("RECORD  ATTENDANCE")
        session_id = ConsoleIO.ask("Enter Session ID: ")
        # verify session belongs to lecturer
        s = self.db.query_one("SELECT LecturerUserID FROM AttendanceSession WHERE SessionID=?", (session_id,))
        if not s:
            print("Session ID not found.")
            return
        if s["LecturerUserID"] != self.lecturer.user_id:
            print("You do not own this session.")
            return

        while True:
            rows = service.list_session_students(session_id)
            print(DASH)
            table_rows = [[r["StudentID"], r["StudentName"], r["CurrentStatus"]] for r in rows]
            Table(headers=["StudentID", "StudentName", "Current Status"], rows=table_rows).render()
            print(DASH)
            print("Actions:")
            print("1. Update a student status")
            print("2. Mark all as Present (batch)")
            print("3. Close session")
            print("0. Back")
            choice = ConsoleIO.ask("Selection: ")

            if choice == "1":
                student_id = ConsoleIO.ask("Enter StudentID: ")
                print("New Status: 1. Present  2. Late  3. Absent  4. Excused")
                s_choice = ConsoleIO.ask("Selection: ")
                mapping = {"1": "Present", "2": "Late", "3": "Absent", "4": "Excused"}
                status = mapping.get(s_choice)
                if not status:
                    ConsoleIO.invalid_menu()
                    continue
                note = ConsoleIO.ask("Optional Note: ", allow_blank=True) or None
                if not ConsoleIO.confirm("Confirm (Y/N): "):
                    continue
                ok, msg = service.update_student_status(
                    session_id=session_id,
                    student_id=student_id,
                    status=status,
                    note=note,
                )
                print(msg)
            elif choice == "2":
                if ConsoleIO.confirm("Confirm (Y/N): "):
                    service.mark_all_present(session_id)
                    print("Batch update done.")
            elif choice == "3":
                if ConsoleIO.confirm("Confirm (Y/N): "):
                    ok = service.close_session(session_id, self.lecturer.user_id)
                    print("Closed." if ok else "Failed to close session.")
                    return
            elif choice == "0":
                return
            else:
                ConsoleIO.invalid_menu()

    def process_requests(self, service: AttendanceService) -> None:
        ConsoleIO.screen("PROCESS REQUESTS")
        print("Filter: 1. Pending only  2. All")
        f = ConsoleIO.ask("Selection: ")
        pending_only = True if f == "1" else False if f == "2" else None
        if pending_only is None:
            ConsoleIO.invalid_menu()
            return

        while True:
            reqs = service.list_requests_for_lecturer(self.lecturer.user_id, pending_only=pending_only)
            print(DASH)
            if not reqs:
                print("(No requests.)")
                return

            rows = []
            for r in reqs[:50]:
                short_reason = (r.reason[:20] + "...") if len(r.reason) > 23 else r.reason
                rows.append([r.request_id, r.session_id or "", r.request_type, short_reason, r.status])
            Table(headers=["RequestID", "SessionID", "Type", "Reason", "Status"], rows=rows).render()
            print(DASH)
            rid = ConsoleIO.ask("Enter RequestID to process (or 0 to back): ")
            if rid == "0":
                return
            print("Action: 1. Approve  2. Reject")
            action = ConsoleIO.ask("Selection: ")

            if action not in ("1", "2"):
                ConsoleIO.invalid_menu()
                continue
            comment = ConsoleIO.ask("Lecturer Comment (optional): ", allow_blank=True) or None
            if not ConsoleIO.confirm("Confirm (Y/N): "):
                continue
            ok, msg = service.process_request(
                lecturer_user_id=self.lecturer.user_id,
                request_id=rid,
                approve=(action == "1"),
                lecturer_comment=comment,
            )
            print(msg if ok else msg)

    def summarize(self, service: AttendanceService) -> None:
        ConsoleIO.screen("SUMMARIZE ATTENDANCE")
        class_name = ConsoleIO.ask("Enter Course/Class ID: ")
        dr = ConsoleIO.ask_date_range()
        summary = service.summarize_class(class_name=class_name, date_from=dr.start, date_to=dr.end)
        print(DASH)
        if not summary:
            print("(No data.)")
            return
        rows = []
        for r in summary:
            rows.append([r["StudentID"], str(r["Present"]), str(r["Late"]), str(r["Absent"]), r["AttendanceRate"]])
        Table(headers=["StudentID", "Present", "Late", "Absent", "Attendance Rate"], rows=rows).render()

    def export_report(self, service: AttendanceService) -> None:
        ConsoleIO.screen("EXPORT REPORT")
        class_name = ConsoleIO.ask("Enter Course/Class ID: ")
        dr = ConsoleIO.ask_date_range()
        out_path = ConsoleIO.ask("Enter output file path (e.g., reports/CSE101_Attendance.xlsx): ")
        if not ConsoleIO.confirm("Confirm export (Y/N): "):
            return
        ok, msg = service.export_report_xlsx(
            class_name=class_name, date_from=dr.start, date_to=dr.end, output_path=out_path
        )
        print(DASH)
        print(msg)
        if ok:
            print(f"Output: {out_path}")
