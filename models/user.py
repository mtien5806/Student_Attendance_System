from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Self


from Database.database import Database, hash_password, new_uuid, verify_password


@dataclass
class User:
    """Base user class.

    Mirrors the `User` class in the class diagram and the `User` table in the ERD.
    """

    user_id: str
    full_name: str
    email: Optional[str] = None
    password_hash: str = ""
    phone_number: Optional[str] = None
    address: Optional[str] = None
    username: str = ""
    birth_date: Optional[str] = None  # YYYY-MM-DD

    @classmethod
    def create(
        cls,
        *,
        full_name: str,
        username: str,
        password: str,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        address: Optional[str] = None,
        birth_date: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Self:  
        return cls(
            user_id=user_id or new_uuid(),
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            phone_number=phone_number,
            address=address,
            username=username,
            birth_date=birth_date,
        )

    def save(self, db: Database) -> None:
        db.execute(
            """
            INSERT INTO User (UserID, fullname, email, password, phoneNumber, address, username, birthDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(UserID) DO UPDATE SET
                fullname=excluded.fullname,
                email=excluded.email,
                password=excluded.password,
                phoneNumber=excluded.phoneNumber,
                address=excluded.address,
                username=excluded.username,
                birthDate=excluded.birthDate
            """,
            (
                self.user_id,
                self.full_name,
                self.email,
                self.password_hash,
                self.phone_number,
                self.address,
                self.username,
                self.birth_date,
            ),
        )

    @classmethod
    def load_by_id(cls, db: Database, user_id: str) -> Optional[Self]:  
        row = db.query_one("SELECT * FROM User WHERE UserID=?", (user_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def load_by_username(cls, db: Database, username: str) -> Optional[Self]:  
        row = db.query_one("SELECT * FROM User WHERE username=?", (username,))
        return cls.from_row(row) if row else None

    @classmethod
    def from_row(cls, row) -> Self:  
        return cls(
            user_id=row["UserID"],
            full_name=row["fullname"],
            email=row["email"],
            password_hash=row["password"],
            phone_number=row["phoneNumber"],
            address=row["address"],
            username=row["username"],
            birth_date=row["birthDate"],
        )

    @staticmethod
    def login(db: Database, username: str, password: str) -> Optional["User"]:
        """Authenticate user.

        Returns the User if credentials are valid, else None.
        """
        user = User.load_by_username(db, username)
        if not user:
            return None
        return user if verify_password(password, user.password_hash) else None
