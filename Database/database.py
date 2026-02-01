from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Optional


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat(sep=" ")


@dataclass(frozen=True)
class PasswordHash:
    algo: str
    iterations: int
    salt_hex: str
    hash_hex: str

    def encode(self) -> str:
        return f"{self.algo}${self.iterations}${self.salt_hex}${self.hash_hex}"


def hash_password(password: str, *, iterations: int = 210_000, salt: bytes | None = None) -> str:
    
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    ph = PasswordHash("pbkdf2_sha256", iterations, salt.hex(), dk.hex())
    return ph.encode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iters_s, salt_hex, hash_hex = encoded.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(candidate, expected)
    except Exception:
        return False


class Database:

    def __init__(self, db_path: str = "sas.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def close(self) -> None:
        self.conn.close()

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        cur = self.conn.execute(sql, tuple(params))
        self.conn.commit()
        return cur

    def executemany(self, sql: str, seq_of_params: Iterable[Iterable[Any]]) -> sqlite3.Cursor:
        cur = self.conn.executemany(sql, [tuple(p) for p in seq_of_params])
        self.conn.commit()
        return cur

    def query_one(self, sql: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
        cur = self.conn.execute(sql, tuple(params))
        return cur.fetchone()

    def query_all(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        cur = self.conn.execute(sql, tuple(params))
        return cur.fetchall()

    def initialize(self) -> None:

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS User (
                UserID TEXT PRIMARY KEY,
                fullname TEXT NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                phoneNumber TEXT,
                address TEXT,
                username TEXT UNIQUE NOT NULL,
                birthDate TEXT
            );
            """
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS Student (
                UserID TEXT PRIMARY KEY,
                StudentID TEXT UNIQUE NOT NULL,
                majorName TEXT,
                FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE
            );
            """
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS Lecturer (
                UserID TEXT PRIMARY KEY,
                LecturerID TEXT UNIQUE NOT NULL,
                FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE
            );
            """
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS Administrator (
                UserID TEXT PRIMARY KEY,
                AdminID TEXT UNIQUE NOT NULL,
                FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE
            );
            """
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS System (
                SystemName TEXT PRIMARY KEY
            );
            """
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS Warning (
                WarningID TEXT PRIMARY KEY,
                StudentUserID TEXT NOT NULL,
                systemName TEXT NOT NULL,
                className TEXT,
                message TEXT NOT NULL,
                createdAt TEXT NOT NULL,
                FOREIGN KEY (StudentUserID) REFERENCES Student(UserID) ON DELETE CASCADE,
                FOREIGN KEY (systemName) REFERENCES System(SystemName) ON DELETE RESTRICT
            );
            """
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS AttendanceSession (
                SessionID TEXT PRIMARY KEY,
                LecturerUserID TEXT NOT NULL,
                date TEXT NOT NULL,
                startTime TEXT,
                durationMinutes INTEGER,
                requirePIN INTEGER,
                pin TEXT,
                className TEXT NOT NULL,
                status TEXT NOT NULL,
                createdAt TEXT NOT NULL,
                FOREIGN KEY (LecturerUserID) REFERENCES Lecturer(UserID) ON DELETE CASCADE
            );
            """
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS AttendanceRecord (
                RecordID TEXT PRIMARY KEY,
                SessionID TEXT NOT NULL,
                StudentUserID TEXT NOT NULL,
                status TEXT NOT NULL,
                checkTime TEXT,
                note TEXT,
                updatedAt TEXT NOT NULL,
                FOREIGN KEY (SessionID) REFERENCES AttendanceSession(SessionID) ON DELETE CASCADE,
                FOREIGN KEY (StudentUserID) REFERENCES Student(UserID) ON DELETE CASCADE,
                UNIQUE (SessionID, StudentUserID)
            );
            """
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS LeaveRequest (
                RequestID TEXT PRIMARY KEY,
                StudentUserID TEXT NOT NULL,
                LecturerUserID TEXT NOT NULL,
                SessionID TEXT,
                type TEXT,
                status TEXT NOT NULL,
                reason TEXT NOT NULL,
                evidencePath TEXT,
                note TEXT,
                createdAt TEXT NOT NULL,
                FOREIGN KEY (StudentUserID) REFERENCES Student(UserID) ON DELETE CASCADE,
                FOREIGN KEY (LecturerUserID) REFERENCES Lecturer(UserID) ON DELETE CASCADE
            );
            """
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS AttendanceReport (
                ReportID TEXT PRIMARY KEY,
                ManagedByAdminUserID TEXT,
                SummarizedByLecturerUserID TEXT,
                fileName TEXT,
                createdAt TEXT NOT NULL,
                title TEXT,
                FOREIGN KEY (ManagedByAdminUserID) REFERENCES Administrator(UserID) ON DELETE SET NULL,
                FOREIGN KEY (SummarizedByLecturerUserID) REFERENCES Lecturer(UserID) ON DELETE SET NULL
            );
            """
        )

    def ensure_schema_extras(self) -> None:

        def has_column(table: str, col: str) -> bool:
            rows = self.query_all(f"PRAGMA table_info({table});")
            return any(r["name"] == col for r in rows)


        try:
            if not has_column("AttendanceSession", "startTime"):
                self.execute("ALTER TABLE AttendanceSession ADD COLUMN startTime TEXT;")
            if not has_column("AttendanceSession", "durationMinutes"):
                self.execute("ALTER TABLE AttendanceSession ADD COLUMN durationMinutes INTEGER;")
            if not has_column("AttendanceSession", "requirePIN"):
                self.execute("ALTER TABLE AttendanceSession ADD COLUMN requirePIN INTEGER;")
            if not has_column("AttendanceSession", "pin"):
                self.execute("ALTER TABLE AttendanceSession ADD COLUMN pin TEXT;")
        except Exception:
       
            pass

  
        try:
            if not has_column("LeaveRequest", "SessionID"):
                self.execute("ALTER TABLE LeaveRequest ADD COLUMN SessionID TEXT;")
            if not has_column("LeaveRequest", "type"):
                self.execute("ALTER TABLE LeaveRequest ADD COLUMN type TEXT;")
            if not has_column("LeaveRequest", "evidencePath"):
                self.execute("ALTER TABLE LeaveRequest ADD COLUMN evidencePath TEXT;")
        except Exception:
            pass


        try:
            if not has_column("Warning", "className"):
                self.execute("ALTER TABLE Warning ADD COLUMN className TEXT;")
        except Exception:
            pass


        try:
            self.execute("CREATE INDEX IF NOT EXISTS idx_record_session ON AttendanceRecord(SessionID);")
            self.execute("CREATE INDEX IF NOT EXISTS idx_record_student ON AttendanceRecord(StudentUserID);")
            self.execute("CREATE INDEX IF NOT EXISTS idx_session_class ON AttendanceSession(className, date);")
            self.execute("CREATE INDEX IF NOT EXISTS idx_leave_lecturer ON LeaveRequest(LecturerUserID, status);")
            self.execute("CREATE INDEX IF NOT EXISTS idx_warning_student ON Warning(StudentUserID, createdAt);")
        except Exception:
            pass
        try:
            if not has_column("User", "failedAttempts"):
                self.execute("ALTER TABLE User ADD COLUMN failedAttempts INTEGER DEFAULT 0;")
            if not has_column("User", "lockUntil"):
                self.execute("ALTER TABLE User ADD COLUMN lockUntil TEXT;")
        except Exception:
            pass
