from __future__ import annotations

from dataclasses import dataclass
from getpass import getpass
from typing import Optional


DASH = "-" * 50
TITLE_BAR = "=" * 50


@dataclass(frozen=True)
class DateRange:
    start: Optional[str]
    end: Optional[str]


class ConsoleIO:
    """Console UI helpers that enforce the spec's input conventions."""

    @staticmethod
    def header(title: str) -> None:
        print(TITLE_BAR)
        print(f"{title:^50}")
        print(TITLE_BAR)

    @staticmethod
    def screen(tag: str) -> None:
        print(f"[{tag}]")  # spec style

    @staticmethod
    def ask(prompt: str, *, allow_blank: bool = False) -> str:
        while True:
            s = input(prompt).strip()
            if s or allow_blank:
                return s
            print("Invalid menu selection. Please try again.")

    @staticmethod
    def ask_password(prompt: str = "Password: ") -> str:
        return getpass(prompt)

    @staticmethod
    def confirm(prompt: str = "Confirm (Y/N): ") -> bool:
        while True:
            s = input(prompt).strip().lower()
            if s in ("y", "yes"):
                return True
            if s in ("n", "no"):
                return False
            print("Please enter Y or N.")

    @staticmethod
    def ask_date(prompt: str) -> str:
        while True:
            s = ConsoleIO.ask(prompt)
            if ConsoleIO._is_date(s):
                return s
            print("Date format: YYYY-MM-DD (e.g., 2026-01-15).")

    @staticmethod
    def ask_time(prompt: str) -> str:
        while True:
            s = ConsoleIO.ask(prompt)
            if ConsoleIO._is_time(s):
                return s
            print("Time format: HH:MM (24-hour format, e.g., 07:30).")

    @staticmethod
    def ask_int(prompt: str, *, min_value: int | None = None, max_value: int | None = None) -> int:
        while True:
            s = ConsoleIO.ask(prompt)
            try:
                n = int(s)
            except ValueError:
                print("Please enter a number.")
                continue
            if min_value is not None and n < min_value:
                print(f"Value must be >= {min_value}.")
                continue
            if max_value is not None and n > max_value:
                print(f"Value must be <= {max_value}.")
                continue
            return n

    @staticmethod
    def ask_pin(prompt: str, *, allow_blank: bool = False) -> str:
        while True:
            s = ConsoleIO.ask(prompt, allow_blank=allow_blank)
            if allow_blank and s == "":
                return ""
            if s.isdigit() and 4 <= len(s) <= 6:
                return s
            print("PIN format: 4–6 digits (e.g., 123456).")

    @staticmethod
    def ask_date_range() -> DateRange:
        start = ConsoleIO.ask("Optional Date Range: From (YYYY-MM-DD): ", allow_blank=True)
        end = ConsoleIO.ask(" To (YYYY-MM-DD): ", allow_blank=True)
        if start and not ConsoleIO._is_date(start):
            print("Date format must be YYYY-MM-DD.")
            start = ""
        if end and not ConsoleIO._is_date(end):
            print("Date format must be YYYY-MM-DD.")
            end = ""
        return DateRange(start=start or None, end=end or None)

    @staticmethod
    def invalid_menu() -> None:
        print("Invalid menu selection. Please try again.")

    @staticmethod
    def _is_date(s: str) -> bool:
        if len(s) != 10:
            return False
        if s.count("-") != 2:
            return False
        y, m, d = s.split("-", 2)
        return y.isdigit() and m.isdigit() and d.isdigit()

    @staticmethod
    def _is_time(s: str) -> bool:
        if len(s) != 5 or s[2] != ":":
            return False
        hh, mm = s.split(":", 1)
        if not (hh.isdigit() and mm.isdigit()):
            return False
        return 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59
