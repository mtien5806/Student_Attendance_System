from __future__ import annotations

from datetime import datetime
from getpass import getpass
from typing import Literal, Optional

from Database.database import Database
from models.user import User
from models.student import Student
from models.lecturer import Lecturer
from models.admin import Administrator
from models.system import System
from models.attendanceSession import AttendanceSession
from models.attendanceRecord import AttendanceRecord

Role = Literal["student", "lecturer", "admin", "unknown"]


def _input_non_empty(prompt: str) -> str:
    while True:
        s = input(prompt).strip()
        if s:
            return s
        print("Vui lòng nhập giá trị hợp lệ.")


def bootstrap_message_if_empty(db: Database) -> None:
    row = db.query_one("SELECT COUNT(*) AS c FROM User")
    if row and row["c"] == 0:
        print("  Database đang trống (chưa có tài khoản).")
        print("   Bạn có thể seed tài khoản demo bằng lệnh: python main.py --seed")
        print()


def seed_demo_data(db: Database) -> None:
    """Tạo tài khoản demo để test nhanh.

    - admin / admin123
    - lec1  / lec123
    - stu1  / stu123
    """
    System("SAS").save(db)

    if User.load_by_username(db, "admin"):
        print("Demo data already exists (username 'admin' found).")
        return

    admin_user = Administrator.create(
        full_name="Admin User",
        username="admin",
        password="admin123",
        email="admin@sas.local",
    )
    admin_user.admin_id = "AD001"
    admin_user.save(db)

    lec_user = Lecturer.create(
        full_name="Lecturer One",
        username="lec1",
        password="lec123",
        email="lec1@sas.local",
    )
    lec_user.lecturer_id = "LEC001"
    lec_user.save(db)

    stu_user = Student.create(
        full_name="Student One",
        username="stu1",
        password="stu123",
        email="stu1@sas.local",
    )
    stu_user.student_id = "STU001"
    stu_user.major_name = "Software Engineering"
    stu_user.save(db)

    print(" Seed demo data thành công.")
    print("   admin / admin123")
    print("   lec1  / lec123")
    print("   stu1  / stu123")


def detect_role(db: Database, user_id: str) -> Role:
    if db.query_one("SELECT 1 FROM Student WHERE UserID=?", (user_id,)):
        return "student"
    if db.query_one("SELECT 1 FROM Lecturer WHERE UserID=?", (user_id,)):
        return "lecturer"
    if db.query_one("SELECT 1 FROM Administrator WHERE UserID=?", (user_id,)):
        return "admin"
    return "unknown"


def login_flow(db: Database, *, max_attempts: int = 5) -> Optional[User]:
    print("===== STUDENT ATTENDANCE SYSTEM (SAS) =====")
    print(f"Đăng nhập (tối đa {max_attempts} lần sai).")
    print("------------------------------------------")

    for attempt in range(1, max_attempts + 1):
        username = _input_non_empty("Username: ")
        password = getpass("Password: ")

        user = User.login(db, username, password)
        if user:
            print(" Đăng nhập thành công.")
            return user

        remain = max_attempts - attempt
        print(f" Sai username/password. Còn {remain} lần thử.")
        if remain == 0:
            print(" Nhập sai quá số lần cho phép. Thoát chương trình.")
            return None

    return None


def role_menu_router(db: Database, user: User) -> None:
    role = detect_role(db, user.user_id)

    if role == "student":
        s = Student.load_by_user_id(db, user.user_id)
        student_menu(s or user)
    elif role == "lecturer":
        l = Lecturer.load_by_user_id(db, user.user_id)
        lecturer_menu(l or user)
    elif role == "admin":
        a = Administrator.load_by_user_id(db, user.user_id)
        admin_menu(a or user)
    else:
        unknown_menu(user)


def _print_profile(user: User) -> None:
    print("\n----- THÔNG TIN TÀI KHOẢN -----")
    print(f"UserID   : {user.user_id}")
    print(f"Họ tên   : {user.full_name}")
    print(f"Username : {user.username}")
    print(f"Email    : {user.email or ''}")
    print(f"SĐT      : {user.phone_number or ''}")
    print(f"Địa chỉ  : {user.address or ''}")
    print(f"Ngày sinh: {user.birth_date or ''}")
    print("-------------------------------\n")


def student_menu(user: User) -> None:
    while True:
        print("\n===== MENU STUDENT =====")
        print("1) Xem thông tin cá nhân")
        print("2) (Stub) Điểm danh")
        print("3) (Stub) Xem lịch sử điểm danh")
        print("4) Đăng xuất")
        print("0) Thoát chương trình")
        choice = input("Chọn: ").strip()

        if choice == "1":
            _print_profile(user)
        elif choice in ("2", "3"):
            print("  Chức năng này sẽ làm ở bước tiếp theo (chưa implement).")
        elif choice == "4":
            print(" Đã đăng xuất.")
            return
        elif choice == "0":
            raise SystemExit(0)
        else:
            print("Lựa chọn không hợp lệ.")


def lecturer_menu(user: User) -> None:
    while True:
        print("\n===== MENU LECTURER =====")
        print("1) Xem thông tin cá nhân")
        print("2) (Stub) Tạo session điểm danh")
        print("3) (Stub) Ghi nhận điểm danh")
        print("4) (Stub) Duyệt đơn xin vắng/trễ")
        print("5) Đăng xuất")
        print("0) Thoát chương trình")
        choice = input("Chọn: ").strip()

        if choice == "1":
            _print_profile(user)
        elif choice in ("2", "3", "4"):
            print("  Chức năng này sẽ làm ở bước tiếp theo (chưa implement).")
        elif choice == "5":
            print(" Đã đăng xuất.")
            return
        elif choice == "0":
            raise SystemExit(0)
        else:
            print("Lựa chọn không hợp lệ.")


def admin_menu(user: User) -> None:
    while True:
        print("\n===== MENU ADMIN =====")
        print("1) Xem thông tin cá nhân")
        print("2) (Stub) Quản lý điểm danh")
        print("3) (Stub) Tìm kiếm điểm danh")
        print("4) Đăng xuất")
        print("0) Thoát chương trình")
        choice = input("Chọn: ").strip()

        if choice == "1":
            _print_profile(user)
        elif choice in ("2", "3"):
            print("  Chức năng này sẽ làm ở bước tiếp theo (chưa implement).")
        elif choice == "4":
            print(" Đã đăng xuất.")
            return
        elif choice == "0":
            raise SystemExit(0)
        else:
            print("Lựa chọn không hợp lệ.")


def unknown_menu(user: User) -> None:
    while True:
        print("\n===== MENU USER (UNKNOWN ROLE) =====")
        print("1) Xem thông tin cá nhân")
        print("2) Đăng xuất")
        print("0) Thoát chương trình")
        choice = input("Chọn: ").strip()

        if choice == "1":
            _print_profile(user)
        elif choice == "2":
            print(" Đã đăng xuất.")
            return
        elif choice == "0":
            raise SystemExit(0)
        else:
            print("Lựa chọn không hợp lệ.")
def lecturer_create_session_flow(db: Database, lecturer_user) -> None:
    """Lecturer tạo session OPEN và lưu DB."""
    print("\n--- TẠO SESSION ĐIỂM DANH ---")
    class_name = _input_non_empty("Nhập tên lớp (className): ")
    date = input("Nhập ngày (YYYY-MM-DD) [bỏ trống = hôm nay]: ").strip()
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    session = AttendanceSession.create(
        lecturer_user_id=_user_id(lecturer_user),
        date=date,
        class_name=class_name,
        status="OPEN",
    )
    session.save(db)

    print("\n Tạo session thành công!")
    print(f"SessionID (mã để SV nhập): {session.session_id}")
    print(f"Class: {session.class_name} | Date: {session.date} | Status: {session.status}\n")


def student_take_attendance_flow(db: Database, student_user) -> None:
    """Student nhập SessionID để điểm danh."""
    print("\n--- STUDENT ĐIỂM DANH ---")
    session_id = _input_non_empty("Nhập SessionID: ")

    session = AttendanceSession.load_by_id(db, session_id)
    if not session:
        print(" SessionID không tồn tại.")
        return

    if session.status != "OPEN":
        print(f" Session đang ở trạng thái '{session.status}' nên không thể điểm danh.")
        return

    # Nếu đã có record rồi thì không tạo lại
    existed = AttendanceRecord.load_by_session_and_student(
        db, session_id=session_id, student_user_id=_user_id(student_user)
    )
    if existed:
        print(f" Bạn đã điểm danh session này rồi. Trạng thái hiện tại: {existed.status}")
        return

    record = AttendanceRecord.create(
        session_id=session_id,
        student_user_id=_user_id(student_user),
        status="Present",
        check_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        note=None,
    )
    record.save(db)
    print(" Điểm danh thành công! Status = Present")


def lecturer_view_session_records_flow(db: Database, lecturer_user) -> None:
    """Lecturer xem danh sách record của session."""
    print("\n--- XEM ATTENDANCE RECORD CỦA SESSION ---")

    # show sessions of this lecturer (gợi ý)
    sessions = AttendanceSession.list_by_lecturer(db, _user_id(lecturer_user))
    if sessions:
        print("Danh sách session gần đây:")
        for s in sessions[:10]:
            print(f"- {s.session_id} | {s.date} | {s.class_name} | {s.status}")
    else:
        print("(Chưa có session nào)")

    session_id = _input_non_empty("\nNhập SessionID cần xem: ")
    session = AttendanceSession.load_by_id(db, session_id)
    if not session:
        print(" SessionID không tồn tại.")
        return

    if session.lecturer_user_id != _user_id(lecturer_user):
        print(" Session này không thuộc lecturer hiện tại.")
        return

    records = AttendanceRecord.list_for_session(db, session_id)
    if not records:
        print(" Chưa có student nào điểm danh session này.")
        return

    print(f"\n--- Records for Session {session.session_id} ({session.class_name} - {session.date}) ---")
    for r in records:
        print(f"- StudentUserID: {r.student_user_id} | Status: {r.status} | Time: {r.check_time or ''} | Note: {r.note or ''}")
    print()
