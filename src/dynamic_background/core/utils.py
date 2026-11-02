import contextlib
import json
import logging
import os
import sys
import tomllib
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# --- Platform Setup ---


def enable_ansi_utf8() -> None:
    """Enable ANSI escape sequences and UTF-8 output on Windows consoles."""
    if sys.platform != "win32":
        return
    os.system("")
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(Exception):
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]


# --- Formatting ---


def safe_int(value: Any, default: int | None = None) -> int | None:
    """Convert value to int, returning default on failure."""
    try:
        return int(value)
    except (ValueError, TypeError, OverflowError):
        return default


def seconds_to_dhms(seconds: Any) -> str:
    """Convert a duration in seconds to a human-readable days/hours/minutes/seconds string."""
    try:
        seconds = int(seconds)
    except (ValueError, TypeError, OverflowError):
        return "N/A"
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{days}d {hours}h {minutes}m {secs}s"


def seconds_to_hms(seconds: float | int) -> str:
    """Convert seconds to a 24-hour clock string in HH:MM:SS format."""
    try:
        seconds = float(seconds)
    except (ValueError, TypeError, OverflowError):
        return "00:00:00"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# --- File I/O ---


def read_toml(path: str | Path | None, default: Any = None) -> Any:
    """Load data from a TOML file with specified fallback."""
    fallback = {} if default is None else default
    if not path:
        return fallback

    p = Path(path)
    if not p.exists():
        return fallback

    try:
        with p.open("rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.error(f"Failed to read TOML from {path}: {e}")

    return fallback


def read_json(path: str | Path | None, default: Any = None) -> Any:
    """Load data from a JSON file with specified fallback."""
    fallback = {} if default is None else default
    if not path:
        return fallback

    p = Path(path)
    if not p.exists():
        return fallback

    try:
        with p.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read JSON from {path}: {e}")

    return fallback


def write_json(path: str | Path | None, data: Any, indent: int = 4) -> bool:
    """Save data to a JSON file safely with formatting."""
    if not path:
        return False
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to write JSON to {path}: {e}")
        return False
