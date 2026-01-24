"""SQLite database layer for the Student Attendance System (SAS).

Implements:
- Connection management (SQLite)
- Schema initialization based on the ERD in the design document
- Small helpers for executing queries
- Password hashing/verification helpers

Only the DB + model layer is implemented for now (UI / workflows will be
added later).
"""

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
    """Return a UUID string suitable for VARCHAR(36) PKs."""
    return str(uuid.uuid4())


def utc_now_iso() -> str:
    """UTC timestamp in ISO format without timezone suffix (SQLite-friendly)."""
    return datetime.utcnow().replace(microsecond=0).isoformat(sep=" ")


# -----------------------------
# Password hashing helpers
# -----------------------------


@dataclass(frozen=True)
class PasswordHash:
    algo: str
    iterations: int
    salt_hex: str
    hash_hex: str

    def encode(self) -> str:
        # Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
        return f"{self.algo}${self.iterations}${self.salt_hex}${self.hash_hex}"


def hash_password(password: str, *, iterations: int = 210_000, salt: bytes | None = None) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256.

    Returns an encoded string that includes algorithm, iterations, and salt.
    """
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    ph = PasswordHash("pbkdf2_sha256", iterations, salt.hex(), dk.hex())
    return ph.encode()


def verify_password(password: str, encoded: str) -> bool:
    """Verify a password against an encoded hash created by `hash_password`."""
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


# -----------------------------
# Database
# -----------------------------


class Database:
    """Thin wrapper around sqlite3 with schema initialization."""

    def __init__(self, db_path: str = "sas.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # Ensure FK constraints
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
        """Create tables if they don't already exist."""

        # NOTE: SQLite uses TEXT for VARCHAR; we keep names close to the ERD.
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
                status TEXT NOT NULL,
                reason TEXT NOT NULL,
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
