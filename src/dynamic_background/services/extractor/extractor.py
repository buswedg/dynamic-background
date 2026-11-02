import logging
from pathlib import Path

from dynamic_background.core import config
from dynamic_background.services.extractor.formats.ddw import DDWExtractor
from dynamic_background.services.extractor.formats.heic import HEICExtractor

logger = logging.getLogger(__name__)

SUPPORTED_EXTS = {".heic", ".heif", ".zip", ".ddw"}


class Extractor:
    """Dispatch wallpaper extraction to format-specific extractors."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        if not self.output_dir.is_absolute():
            self.output_dir = config.PROJECT_ROOT / self.output_dir

    @staticmethod
    def get_extractor_for_file(file_path: str | Path) -> HEICExtractor | DDWExtractor | None:
        """Return the extractor matching the file extension, or None."""
        ext = Path(file_path).suffix.lower()
        if ext in (".heic", ".heif"):
            return HEICExtractor()
        if ext in (".zip", ".ddw"):
            return DDWExtractor()
        return None

    def extract_from_path(self, input_path: str | Path) -> None:
        """Extract wallpapers from a single file or a directory of files."""
        input_path = Path(input_path)
        if not input_path.is_absolute():
            input_path = config.PROJECT_ROOT / input_path

        if not input_path.exists():
            logger.error(f"Input path '{input_path}' does not exist.")
            return

        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)

        if input_path.is_file():
            files_to_process = [(input_path, self.output_dir)]
        else:
            files_to_process = []
            for file_path in sorted(input_path.rglob("*")):
                if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTS:
                    continue
                rel_dir = file_path.parent.relative_to(input_path)
                target_dir = self.output_dir if rel_dir == Path(".") else self.output_dir / rel_dir
                files_to_process.append((file_path, target_dir))

        processed_count = 0
        for file_path, target_dir in files_to_process:
            extractor = self.get_extractor_for_file(file_path)
            if extractor:
                try:
                    extractor.extract(file_path, target_dir)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")

        logger.info(f"Done. Processed {processed_count} files.")
