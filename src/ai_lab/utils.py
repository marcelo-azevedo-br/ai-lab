from __future__ import annotations

from datetime import datetime, UTC
import re


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def compact_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    cleaned = cleaned.strip("-")
    return cleaned or "run"
