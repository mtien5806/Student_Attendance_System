from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from ui.console import ConsoleIO, DateRange, TITLE_BAR, DASH


@dataclass(frozen=True)
class Table:
    headers: Sequence[str]
    rows: Sequence[Sequence[str]]

    def render(self) -> None:
        # Simple fixed-width table (console friendly)
        widths = [len(h) for h in self.headers]
        for row in self.rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))

        def fmt_row(row: Sequence[str]) -> str:
            parts = []
            for i, cell in enumerate(row):
                parts.append(cell.ljust(widths[i]))
            return " | ".join(parts)

        print(fmt_row(list(self.headers)))
        print(" | ".join("-" * w for w in widths))
        for r in self.rows:
            print(fmt_row(r))


__all__ = ["ConsoleIO", "DateRange", "Table", "TITLE_BAR", "DASH"]
