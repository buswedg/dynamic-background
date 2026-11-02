import logging
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from dynamic_background.core.utils import read_toml
from dynamic_background.models import FileConfig

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Documented defaults applied when config.toml is absent. When the file exists,
# extractor keys that are missing or null disable the option (see README).
DEFAULT_CONFIG_DATA: dict[str, Any] = {
    "scheduler": {"backgrounds_dir": "images/example"},
    "extractor": {
        "target_aspect": 1.7777777777777777,
        "force_resolution": [3840, 2160],
        "jpeg_quality": 90,
    },
}


def _load_file_config() -> FileConfig:
    """Read config.toml and coerce its contents into a FileConfig model."""
    data = read_toml(PROJECT_ROOT / "config.toml")
    if not isinstance(data, dict) or not data:
        data = DEFAULT_CONFIG_DATA

    known = {"scheduler", "extractor"}
    for key in data:
        if key not in known:
            logger.warning(f"Ignoring unknown config.toml key '{key}'.")

    known_fields = {f.name for f in fields(FileConfig)}
    for section in ("scheduler", "extractor"):
        section_data = data.get(section)
        if isinstance(section_data, dict):
            for key in section_data:
                if key not in known_fields:
                    logger.warning(f"Ignoring unknown config.toml key '{section}.{key}'.")

    return FileConfig.from_dict(data)


@dataclass(frozen=True)
class Settings:
    """All runtime configuration settings, loaded from config.toml."""

    backgrounds_dir: Path
    target_aspect: float | None
    force_resolution: tuple[int, int] | None
    jpeg_quality: int | None
    backgrounds_json_path: Path
    schedule_path: Path

    @classmethod
    def load(cls, file: FileConfig) -> "Settings":
        """Build runtime settings, resolving project-relative paths."""
        backgrounds = Path(file.backgrounds_dir)
        if not backgrounds.is_absolute():
            backgrounds = PROJECT_ROOT / backgrounds
        return cls(
            backgrounds_dir=backgrounds.resolve(),
            target_aspect=file.target_aspect,
            force_resolution=file.force_resolution,
            jpeg_quality=file.jpeg_quality,
            backgrounds_json_path=PROJECT_ROOT / "data" / "backgrounds.json",
            schedule_path=PROJECT_ROOT / "schedule.json",
        )


settings = Settings.load(_load_file_config())
