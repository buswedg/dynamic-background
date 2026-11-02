import json
import logging
from pathlib import Path

from dynamic_background.core import config
from dynamic_background.models import BackgroundsFile, ScheduleFile

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """Scan the backgrounds directory and rebuild the theme registry."""

    def __init__(self, backgrounds_dir: str | Path) -> None:
        self.backgrounds_dir = Path(backgrounds_dir)

    def clean_theme_name(self, name: str) -> str:
        """Clean a theme directory name to a simple dictionary key style."""
        safe = "".join([c for c in name if c.isalnum() or c in (" ", "-", "_")]).strip()
        return safe.lower().replace(" ", "_").replace("-", "_")

    def update_schedule_config(self) -> None:
        """Scan for themes with triggers.json and update the registry files."""
        logger.info(f"Scanning for themes in: {self.backgrounds_dir}")
        if not self.backgrounds_dir.exists():
            logger.error(f"Backgrounds directory does not exist: {self.backgrounds_dir}")
            return

        discovered_themes: BackgroundsFile = {}
        for entry in self.backgrounds_dir.iterdir():
            if entry.is_dir():
                triggers_file = entry / "triggers.json"
                if triggers_file.exists():
                    theme_key = self.clean_theme_name(entry.name)
                    # Save absolute path with forward slashes for cross-compatibility
                    abs_path = str(triggers_file.resolve()).replace("\\", "/")
                    discovered_themes[theme_key] = abs_path
                    logger.info(f"  - Discovered theme: '{theme_key}' -> {abs_path}")

        if not discovered_themes:
            logger.warning("No themes with triggers.json were found.")
            return

        # Write out backgrounds.json
        backgrounds_path = config.settings.backgrounds_json_path
        backgrounds_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            backgrounds_path.write_text(json.dumps(discovered_themes, indent=2), encoding="utf-8")
            logger.info(f"Successfully updated backgrounds registry at: {backgrounds_path}")
        except Exception as e:
            logger.error(f"Failed to write backgrounds registry: {e}")

        # Initialize schedule.json if not present
        schedule_path = config.settings.schedule_path
        if not schedule_path.exists():
            try:
                schedule_file: ScheduleFile = {"schedule": {}}
                schedule_path.write_text(json.dumps(schedule_file, indent=2), encoding="utf-8")
                logger.info(f"Initialized default schedule config at: {schedule_path}")
            except Exception as e:
                logger.error(f"Failed to initialize schedule config: {e}")
