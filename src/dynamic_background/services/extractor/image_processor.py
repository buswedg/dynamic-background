import logging
from pathlib import Path

from PIL import Image

from dynamic_background.core import config

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process and optimize background images using the configured constraints."""

    def process_image_from_object(self, img_obj: Image.Image, destination_dir: str | Path, target_name: str) -> None:
        """Process and save an in-memory PIL Image object."""
        try:
            destination_path = Path(destination_dir) / f"{target_name}.jpg"
            Path(destination_dir).mkdir(parents=True, exist_ok=True)

            img = img_obj

            # Crop to target aspect ratio if configured
            if config.settings.target_aspect is not None:
                img = self._enforce_aspect(img, target_aspect=config.settings.target_aspect)

            # Resize to forced resolution if configured
            if config.settings.force_resolution is not None:
                img = img.resize(config.settings.force_resolution, Image.Resampling.LANCZOS)

            # Save as JPEG with configured quality
            if img.mode != "RGB":
                img = img.convert("RGB")

            quality = config.settings.jpeg_quality if config.settings.jpeg_quality is not None else 95
            img.save(destination_path, format="JPEG", quality=quality)

        except Exception as e:
            logger.error(f"Failed to process image object for {target_name}: {e}")

    def _enforce_aspect(self, img: Image.Image, target_aspect: float) -> Image.Image:
        """Crop an image from the center to a target aspect ratio, if necessary."""
        img_aspect = img.width / img.height

        if abs(img_aspect - target_aspect) < 0.01:
            return img

        if img_aspect > target_aspect:
            target_height = img.height
            target_width = int(target_height * target_aspect)
        else:
            target_width = img.width
            target_height = int(target_width / target_aspect)

        left = (img.width - target_width) / 2
        top = (img.height - target_height) / 2
        right = (img.width + target_width) / 2
        bottom = (img.height + target_height) / 2

        return img.crop((left, top, right, bottom))
