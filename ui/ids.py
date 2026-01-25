from __future__ import annotations

def short_id(value: str, *, keep: int = 6) -> str:
    """Shorten IDs for display (optional)."""
    if not value:
        return value
    return value if len(value) <= keep else value[:keep]
