from dataclasses import dataclass
from typing import Any, TypedDict

# --- Config ---


def _as_str(value: Any, default: str = "") -> str:
    """Coerce value to str, falling back to default when missing."""
    return str(value) if value is not None else default


def _as_int(value: Any, default: int | None = None) -> int | None:
    """Coerce value to int, falling back to default when missing or invalid."""
    if value is not None:
        try:
            return int(value)
        except (ValueError, TypeError):
            pass
    return default


def _as_float(value: Any, default: float | None = None) -> float | None:
    """Coerce value to float, falling back to default when missing or invalid."""
    if value is not None:
        try:
            return float(value)
        except (ValueError, TypeError):
            pass
    return default


def _as_resolution(value: Any) -> tuple[int, int] | None:
    """Coerce a [width, height] list to a tuple, or None when absent or invalid."""
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        return (int(value[0]), int(value[1]))
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True)
class FileConfig:
    """Shape of config.toml — one field per documented key."""

    backgrounds_dir: str = "images/example"
    target_aspect: float | None = None
    force_resolution: tuple[int, int] | None = None
    jpeg_quality: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileConfig":
        """Build a FileConfig from raw TOML data, coercing values tolerantly."""
        scheduler = data.get("scheduler") or {}
        extractor = data.get("extractor") or {}
        return cls(
            backgrounds_dir=_as_str(scheduler.get("backgrounds_dir"), "images/example"),
            target_aspect=_as_float(extractor.get("target_aspect"), None),
            force_resolution=_as_resolution(extractor.get("force_resolution")),
            jpeg_quality=_as_int(extractor.get("jpeg_quality"), None),
        )


# --- Theme Files ---


class TriggerEntry(TypedDict):
    """A single time-of-day background trigger."""

    time: str
    image: str


class TriggersFile(TypedDict):
    """Shape of a theme's triggers.json."""

    triggers: list[TriggerEntry]


class ScheduleFile(TypedDict, total=False):
    """Shape of schedule.json — day names mapped to a theme or a list of themes."""

    schedule: dict[str, str | list[str]]


# Theme registry: theme key -> absolute path to the theme's triggers.json.
BackgroundsFile = dict[str, str]
