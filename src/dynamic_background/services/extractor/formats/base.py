from pathlib import Path

from dynamic_background.services.extractor.image_processor import ImageProcessor


class BaseExtractor:
    """Base class for dynamic background theme extractors."""

    def __init__(self, image_processor: ImageProcessor | None = None) -> None:
        self.processor = image_processor or ImageProcessor()

    def extract(self, file_path: str | Path, output_root: str | Path) -> None:
        """Extract images, metadata, and triggers from file_path into output_root."""
        raise NotImplementedError
