from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import re 

from Database.database import Database, utc_now_iso
from models.attendanceSession import AttendanceSession
from models.attendanceRecord import AttendanceRecord
from models.leaveRequest import LeaveRequest
from models.warning import Warning
from models.user import User

from services.id_generator import IdGenerator


@dataclass
class AttendanceService:
    db: Database
    @staticmethod
    def normalize_session_id(raw: str) -> str:
        s = (raw or "").strip()

        # cho phép user paste "<S001>"
        if s.startswith("<") and s.endswith(">"):
            s = s[1:-1].strip()

        # nếu user lỡ paste cả chuỗi dài, vẫn trích được Sxxx
        m = re.search(r"(S\d+)", s, re.IGNORECASE)
        if m:
            return m.group(1).upper()

        return s.upper()


    def count_warnings(self, student_user_id: str) -> int:
        row = self.db.query_one("SELECT COUNT(*) AS c FROM Warning WHERE StudentUserID=?", (student_user_id,))
        return int(row["c"]) if row else 0

    def count_pending_requests_for_student(self, student_user_id: str) -> int:
        row = self.db.query_one(
            "SELECT COUNT(*) AS c FROM LeaveRequest WHERE StudentUserID=? AND status='PENDING'",
            (student_user_id,),
        )
        return int(row["c"]) if row else 0

    def count_pending_requests_for_lecturer(self, lecturer_user_id: str) -> int:
        row = self.db.query_one(
            "SELECT COUNT(*) AS c FROM LeaveRequest WHERE LecturerUserID=? AND status='PENDING'",
            (lecturer_user_id,),
        )
        return int(row["c"]) if row else 0


    def create_session(
        self,
        *,
        lecturer_user_id: str,
        class_name: str,
        date: str,
        start_time: str,
        duration_minutes: int,
        require_pin: bool,
        pin: Optional[str],
    ) -> AttendanceSession:
        gen = IdGenerator(self.db)
        session_id = gen.next_id("S", "AttendanceSession", "SessionID", width=3)
        session = AttendanceSession.create(
            session_id=session_id,
            lecturer_user_id=lecturer_user_id,
            class_name=class_name,
            date=date,
            start_time=start_time,
            duration_minutes=duration_minutes,
            require_pin=require_pin,
            pin=pin,
            status="OPEN",
        )
        session.save(self.db)
        return session

    def close_session(self, session_id: str, lecturer_user_id: str) -> bool:
        session = AttendanceSession.load_by_id(self.db, session_id)
        if not session or session.lecturer_user_id != lecturer_user_id:
            return False
        session.status = "CLOSED"
        session.save(self.db)
        # Ensure Absent records for non-check-in students 
        self._ensure_absent_records_on_close(session=session)
        # After close, run warning checks
        self.generate_warnings_for_all_students(class_name=session.class_name, threshold_absent=3)
        return True

    
    def _ensure_absent_records_on_close(self, *, session: AttendanceSession) -> None:
        """When a session closes, create Absent records for students without any record in that session."""
        students = self.db.query_all("SELECT UserID FROM Student")
        for s in students:
            uid = s["UserID"]
            existed = AttendanceRecord.load_by_session_and_student(self.db, session_id=session.session_id, student_user_id=uid)
            if existed:
                continue
            AttendanceRecord.create(
                session_id=session.session_id,
                student_user_id=uid,
                status="Absent",
                check_time=None,
                note=None,
            ).save(self.db)

    def is_session_open(self, session: AttendanceSession) -> bool:
        if session.status != "OPEN":
            return False
        # If we have time/duration, treat as expired after end time.
        if session.start_time and session.duration_minutes:
            try:
                start = datetime.strptime(f"{session.date} {session.start_time}", "%Y-%m-%d %H:%M")
                end = start + timedelta(minutes=int(session.duration_minutes))
                if datetime.now() > end:
                    return False
            except Exception:
                pass
        return True


    def student_check_in(self, *, student_user_id: str, session_id: str, pin: Optional[str]) -> tuple[bool, str]:
        session_id = self.normalize_session_id(session_id)
        
        session = AttendanceSession.load_by_id(self.db, session_id)
        if not session:
            return False, "Session ID not found."
        if not self.is_session_open(session):
            return False, "Session is closed or expired."

        if session.require_pin:
            if not pin:
                return False, "PIN is required."
            if session.pin and pin != session.pin:
                return False, "Invalid or expired PIN."

        existed = AttendanceRecord.load_by_session_and_student(
            self.db, session_id=session_id, student_user_id=student_user_id
        )
        if existed:
            return False, "Attendance already recorded for this student in the session."

        record = AttendanceRecord.create(
            session_id=session_id,
            student_user_id=student_user_id,
            status="Present",
            check_time=utc_now_iso(),
            note=None,
        )
        record.save(self.db)
        return True, "Check-in successful."

    def view_attendance(
        self,
        *,
        student_user_id: str,
        class_name: Optional[str],
        date_from: Optional[str],
        date_to: Optional[str],
    ) -> tuple[list[dict], dict]:
        where = ["ar.StudentUserID=?"]
        params: list[object] = [student_user_id]

        if class_name:
            where.append("s.className=?")
            params.append(class_name)
        if date_from:
            where.append("s.date>=?")
            params.append(date_from)
        if date_to:
            where.append("s.date<=?")
            params.append(date_to)

        rows = self.db.query_all(
            f"""
            SELECT ar.SessionID, s.date, s.startTime, ar.status, ar.note, s.className
            FROM AttendanceRecord ar
            JOIN AttendanceSession s ON s.SessionID = ar.SessionID
            WHERE {' AND '.join(where)}
            ORDER BY s.date DESC, COALESCE(s.startTime,'') DESC
            """,
            params,
        )

        summary = {"Present": 0, "Late": 0, "Absent": 0, "Excused": 0}
        items: list[dict] = []
        for r in rows:
            status = r["status"]
            if status in summary:
                summary[status] += 1
            items.append(
                {
                    "SessionID": r["SessionID"],
                    "Date": r["date"],
                    "Time": r["startTime"] or "",
                    "Status": status,
                    "Note": r["note"] or "-",
                    "ClassName": r["className"],
                }
            )
        return items, summary

  
    def submit_request(
        self,
        *,
        student_user_id: str,
        session_id: str,
        request_type: str,
        reason: str,
        evidence_path: Optional[str],
    ) -> tuple[bool, str]:
        session = AttendanceSession.load_by_id(self.db, session_id)
        if not session:
            return False, "Session ID not found."

        gen = IdGenerator(self.db)
        request_id = gen.next_id("R", "LeaveRequest", "RequestID", width=3)

        req = LeaveRequest.create(
            request_id=request_id,
            student_user_id=student_user_id,
            lecturer_user_id=session.lecturer_user_id,
            session_id=session_id,
            request_type=request_type,
            reason=reason,
            evidence_path=evidence_path,
            status="PENDING",
            note=None,
        )
        req.save(self.db)
        return True, "Request submitted."

    def list_requests_for_student(self, student_user_id: str) -> list[LeaveRequest]:
        return LeaveRequest.list_for_student(self.db, student_user_id)

    def list_requests_for_lecturer(self, lecturer_user_id: str, *, pending_only: bool) -> list[LeaveRequest]:
        return LeaveRequest.list_for_lecturer(self.db, lecturer_user_id, pending_only=pending_only)

    def process_request(
        self,
        *,
        lecturer_user_id: str,
        request_id: str,
        approve: bool,
        lecturer_comment: Optional[str],
    ) -> tuple[bool, str]:
        req = LeaveRequest.load_by_id(self.db, request_id)
        if not req or req.lecturer_user_id != lecturer_user_id:
            return False, "Request not found."
        if req.status not in ("PENDING", "APPROVED", "REJECTED"):
            return False, "Invalid request status."

        new_status = "APPROVED" if approve else "REJECTED"
        req.set_status(self.db, new_status, note=lecturer_comment)

        # If approved, sync attendance record (spec: approved Absent -> Excused, approved Late -> Late)
        if new_status == "APPROVED" and req.session_id:
            att_status = "Excused" if req.request_type == "Absent" else "Late"
            rec = AttendanceRecord.load_by_session_and_student(
                self.db, session_id=req.session_id, student_user_id=req.student_user_id
            )
            if rec:
                rec.status = att_status
                # keep check_time as-is; lecturer comment becomes note if provided
                if lecturer_comment:
                    rec.note = lecturer_comment
                rec.updated_at = utc_now_iso()
                rec.save(self.db)
            else:
                AttendanceRecord.create(
                    session_id=req.session_id,
                    student_user_id=req.student_user_id,
                    status=att_status,
                    check_time=None,
                    note=lecturer_comment,
                ).save(self.db)

        return True, f"Request {new_status}."


    def list_session_students(self, session_id: str) -> list[dict]:
        # Show current records for a session
        rows = self.db.query_all(
            """
            SELECT s.UserID AS StudentUserID, s.StudentID, u.fullname,
                   COALESCE(ar.status,'Absent') AS status
            FROM Student s
            JOIN User u ON u.UserID = s.UserID
            LEFT JOIN AttendanceRecord ar
                ON ar.StudentUserID = s.UserID AND ar.SessionID = ?
            ORDER BY u.fullname
            """,
            (session_id,),
        )
        return [
            {"StudentID": r["StudentID"], "StudentName": r["fullname"], "CurrentStatus": r["status"], "UserID": r["StudentUserID"]}
            for r in rows
        ]

    def update_student_status(
        self,
        *,
        session_id: str,
        student_id: str,
        status: str,
        note: Optional[str],
    ) -> tuple[bool, str]:
        # Find student user
        s = self.db.query_one("SELECT UserID FROM Student WHERE StudentID=?", (student_id,))
        if not s:
            return False, "Student ID not found."
        student_user_id = s["UserID"]

        rec = AttendanceRecord.load_by_session_and_student(self.db, session_id=session_id, student_user_id=student_user_id)
        if rec:
            rec.status = status
            rec.note = note
            rec.updated_at = utc_now_iso()
            rec.save(self.db)
            return True, "Updated."
        # create missing
        rec = AttendanceRecord.create(session_id=session_id, student_user_id=student_user_id, status=status, check_time=None, note=note)
        rec.save(self.db)
        return True, "Created."

    def mark_all_present(self, session_id: str) -> None:
        students = self.db.query_all("SELECT UserID FROM Student")
        for s in students:
            uid = s["UserID"]
            rec = AttendanceRecord.load_by_session_and_student(self.db, session_id=session_id, student_user_id=uid)
            if not rec:
                AttendanceRecord.create(session_id=session_id, student_user_id=uid, status="Present", check_time=utc_now_iso(), note=None).save(self.db)
            else:
                rec.status = "Present"
                rec.updated_at = utc_now_iso()
                rec.save(self.db)

    def summarize_class(
        self,
        *,
        class_name: str,
        date_from: Optional[str],
        date_to: Optional[str],
    ) -> list[dict]:
        where = ["s.className=?"]
        params: list[object] = [class_name]
        if date_from:
            where.append("s.date>=?")
            params.append(date_from)
        if date_to:
            where.append("s.date<=?")
            params.append(date_to)

        rows = self.db.query_all(
            f"""
            SELECT st.StudentID, u.fullname,
                   SUM(CASE WHEN ar.status='Present' THEN 1 ELSE 0 END) AS Present,
                   SUM(CASE WHEN ar.status='Late' THEN 1 ELSE 0 END) AS Late,
                   SUM(CASE WHEN ar.status='Absent' THEN 1 ELSE 0 END) AS Absent,
                   SUM(CASE WHEN ar.status='Excused' THEN 1 ELSE 0 END) AS Excused,
                   COUNT(ar.RecordID) AS Total
            FROM Student st
            JOIN User u ON u.UserID = st.UserID
            LEFT JOIN AttendanceRecord ar ON ar.StudentUserID = st.UserID
            LEFT JOIN AttendanceSession s ON s.SessionID = ar.SessionID
            WHERE {' AND '.join(where)}
            GROUP BY st.StudentID, u.fullname
            ORDER BY u.fullname
            """,
            params,
        )
        out = []
        for r in rows:
            total = int(r["Total"] or 0)
            present = int(r["Present"] or 0)
            rate = f"{int(round((present / total) * 100))}%" if total else "0%"
            out.append(
                {
                    "StudentID": r["StudentID"],
                    "Present": int(r["Present"] or 0),
                    "Late": int(r["Late"] or 0),
                    "Absent": int(r["Absent"] or 0),
                    "Excused": int(r["Excused"] or 0),
                    "AttendanceRate": rate,
                    "StudentName": r["fullname"],
                }
            )
        return out

    def export_report_xlsx(
        self,
        *,
        class_name: str,
        date_from: Optional[str],
        date_to: Optional[str],
        output_path: str,
    ) -> tuple[bool, str]:
        try:
            from openpyxl import Workbook
        except Exception:
            return False, "Missing dependency: openpyxl (pip install openpyxl)"

        summary = self.summarize_class(class_name=class_name, date_from=date_from, date_to=date_to)

        wb = Workbook()
        ws = wb.active
        if ws is None:  # để Pylance hết báo + tránh None runtime
            ws = wb.create_sheet(title="Attendance Report")
        else:
            ws.title = "Attendance Report"


        ws.append(["Course/Class ID", class_name])
        ws.append(["From", date_from or ""])
        ws.append(["To", date_to or ""])
        ws.append([])
        ws.append(["StudentID", "StudentName", "Present", "Late", "Absent", "Excused", "Attendance Rate"])

        for r in summary:
            ws.append([r["StudentID"], r["StudentName"], r["Present"], r["Late"], r["Absent"], r["Excused"], r["AttendanceRate"]])

        try:
            wb.save(output_path)
        except Exception as e:
            return False, f"Export failed: {e}"
        return True, "Export completed successfully."

    def generate_warnings_for_all_students(self, *, class_name: str, threshold_absent: int = 3) -> None:
    
        rows = self.db.query_all(
            """
            SELECT ar.StudentUserID, COUNT(*) AS AbsentCount
            FROM AttendanceRecord ar
            JOIN AttendanceSession s ON s.SessionID = ar.SessionID
            WHERE s.className=? AND ar.status='Absent'
            GROUP BY ar.StudentUserID
            HAVING COUNT(*) >= ?
            """,
            (class_name, threshold_absent),
        )
        if not rows:
            return

        gen = IdGenerator(self.db)
        for r in rows:
            student_uid = r["StudentUserID"]
            existed = self.db.query_one(
                """
                SELECT 1 FROM Warning
                WHERE StudentUserID=? AND className=? AND message LIKE ?
                LIMIT 1
                """,
                (student_uid, class_name, f"%{threshold_absent}%"),
            )
            if existed:
                continue
            wid = gen.next_id("W", "Warning", "WarningID", width=3)
            msg = f"Absence threshold reached ({threshold_absent})"
            Warning(
                warning_id=wid,
                student_user_id=student_uid,
                system_name="SAS",
                class_name=class_name,
                message=msg,
                created_at=utc_now_iso(),
            ).save(self.db)


    def search_attendance_records(
        self,
        *,
        by: str,
        keyword: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> list[dict]:
        """Search attendance records for Admin dashboard (spec 8.7.1)."""
        where = []
        params: list[object] = []

        if by == "student_id":
            where.append("st.StudentID=?")
            params.append(keyword)
        elif by == "session_id":
            where.append("ar.SessionID=?")
            params.append(keyword)
        elif by == "class_name":
            where.append("s.className=?")
            params.append(keyword)
        elif by == "date_range":
            # keyword unused
            pass
        else:
            return []

        if date_from:
            where.append("s.date>=?")
            params.append(date_from)
        if date_to:
            where.append("s.date<=?")
            params.append(date_to)

        clause = ("WHERE " + " AND ".join(where)) if where else ("WHERE 1=1")
        rows = self.db.query_all(
            f"""
            SELECT ar.RecordID, ar.SessionID, s.className, s.date, st.StudentID, u.fullname,
                   ar.status, ar.checkTime, ar.note
            FROM AttendanceRecord ar
            JOIN AttendanceSession s ON s.SessionID = ar.SessionID
            JOIN Student st ON st.UserID = ar.StudentUserID
            JOIN User u ON u.UserID = ar.StudentUserID
            {clause}
            ORDER BY s.date DESC, ar.checkTime DESC
            """,
            params,
        )
        return [
            {
                "RecordID": r["RecordID"],
                "SessionID": r["SessionID"],
                "ClassName": r["className"],
                "Date": r["date"],
                "StudentID": r["StudentID"],
                "StudentName": r["fullname"],
                "Status": r["status"],
                "CheckTime": r["checkTime"] or "",
                "Note": r["note"] or "",
            }
            for r in rows
        ]

    def delete_attendance_record(self, *, session_id: str, student_id: str) -> tuple[bool, str]:
        s = self.db.query_one("SELECT UserID FROM Student WHERE StudentID=?", (student_id,))
        if not s:
            return False, "Student ID not found."
        self.db.execute(
            "DELETE FROM AttendanceRecord WHERE SessionID=? AND StudentUserID=?",
            (session_id, s["UserID"]),
        )
        return True, "Deleted."
