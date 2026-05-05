from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re


TEXT_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".json",
    ".csv",
    ".tsv",
    ".yaml",
    ".yml",
    ".html",
    ".xml",
}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def read_textish(path: Path, limit: int) -> str | None:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return None
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def strip_model_reasoning(text: str) -> str:
    patterns = [
        r"<\s*think\b[^>]*>.*?(?:<\s*/\s*think\s*>|$)",
        r"&lt;\s*think\b.*?&gt;.*?(?:&lt;\s*/\s*think\s*&gt;|$)",
    ]
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()
