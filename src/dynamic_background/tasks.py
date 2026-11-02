import logging
from pathlib import Path

from dynamic_background.services.extractor.extractor import Extractor
from dynamic_background.services.scheduler import BackgroundScheduler

logger = logging.getLogger(__name__)


# --- Schedule Operations ---


def run_schedule_scan(backgrounds_dir: str | Path) -> None:
    """Scan the backgrounds directory and update the theme registry."""
    BackgroundScheduler(backgrounds_dir).update_schedule_config()


def run_extract(input_path: str | Path, output_dir: str | Path) -> None:
    """Extract dynamic wallpapers from HEIC or DDW packages."""
    Extractor(output_dir).extract_from_path(input_path)
