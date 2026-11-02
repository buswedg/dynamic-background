import io
import json
import logging
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image

from dynamic_background.core import config
from dynamic_background.core.utils import seconds_to_hms
from dynamic_background.models import TriggerEntry, TriggersFile
from dynamic_background.services.extractor.formats.base import BaseExtractor
from dynamic_background.services.extractor.image_processor import ImageProcessor

logger = logging.getLogger(__name__)

DDW_IMAGE_EXTS = (".jpg", ".jpeg", ".png")


class DDWExtractor(BaseExtractor):
    """Process and extract dynamic wallpapers from DDW (WinDynamicDesktop) zip archives."""

    def __init__(self, image_processor: ImageProcessor | None = None) -> None:
        super().__init__(image_processor)

    def extract(self, file_path: str | Path, output_root: str | Path) -> None:
        """Determine if a file is a zip/ddw and process it."""
        if not zipfile.is_zipfile(file_path):
            logger.error(f"File is not a valid zip archive: {file_path}")
            return

        logger.info(f"Processing DDW/ZIP: {file_path}")

        with zipfile.ZipFile(file_path, "r") as outer_zip:
            namelist = outer_zip.namelist()

            # Check if it has any nested .ddw files
            nested_ddws = [f for f in namelist if f.lower().endswith(".ddw")]

            if nested_ddws:
                # Extract each nested DDW
                for ddw_name in nested_ddws:
                    logger.info(f"  - Extracting nested DDW: {ddw_name}")
                    ddw_bytes = outer_zip.read(ddw_name)
                    self.extract_ddw_theme(ddw_bytes, ddw_name, output_root)
            else:
                # The zip file itself is the DDW theme
                ddw_bytes = Path(file_path).read_bytes()
                self.extract_ddw_theme(ddw_bytes, Path(file_path).name, output_root)

    def extract_ddw_theme(self, ddw_zip_bytes: bytes, theme_filename: str, output_root: str | Path) -> None:
        """Extract and process images and metadata from a DDW zip package."""
        with zipfile.ZipFile(io.BytesIO(ddw_zip_bytes)) as ddw_zip:
            namelist = ddw_zip.namelist()

            # Find JSON theme metadata file
            json_files = [f for f in namelist if f.lower().endswith(".json")]
            if not json_files:
                logger.warning(f"  [!] No JSON theme file found in {theme_filename}")
                return

            metadata_file = json_files[0]
            with ddw_zip.open(metadata_file) as f:
                metadata = json.load(f)

            display_name = metadata.get("displayName", "DDW Theme")
            image_pattern = metadata.get("imageFilename", "")
            logger.info(f"Processing DDW theme: {display_name}")
            logger.info(f"    - Image Pattern: {image_pattern}")

            # Define output directory based on JSON name or display name
            base_name = Path(theme_filename).stem
            # Clean name for filesystem
            safe_name = "".join([c for c in base_name if c.isalnum() or c in (" ", "-", "_")]).strip()
            safe_name = safe_name.replace(" ", "_")

            file_output_folder = Path(output_root) / safe_name
            file_output_folder.mkdir(parents=True, exist_ok=True)

            # Extract and process all images
            image_files = [f for f in namelist if f.lower().endswith(DDW_IMAGE_EXTS)]
            logger.info(f"    - Found {len(image_files)} images to extract")

            extracted_images: dict[int, str] = {}

            # Determine if we can bypass processing completely
            bypass_processing = (
                config.settings.target_aspect is None
                and config.settings.force_resolution is None
                and config.settings.jpeg_quality is None
            )

            for img_name in image_files:
                try:
                    base_img_name = Path(img_name).stem
                    parts = base_img_name.split("_")
                    if not parts or not parts[-1].isdigit():
                        logger.warning(f"    - Skipping image with non-standard name format: {img_name}")
                        continue
                    img_index = int(parts[-1])

                    target_name = f"{safe_name}_{img_index}"

                    if bypass_processing:
                        ext = Path(img_name).suffix.lower()
                        destination_path = file_output_folder / f"{target_name}{ext}"
                        destination_path.write_bytes(ddw_zip.read(img_name))
                        extracted_images[img_index] = f"{target_name}{ext}"
                    else:
                        with ddw_zip.open(img_name) as img_f:
                            img_data = img_f.read()
                            image = Image.open(io.BytesIO(img_data))

                        self.processor.process_image_from_object(image, file_output_folder, target_name=target_name)
                        extracted_images[img_index] = f"{target_name}.jpg"
                except Exception as e:
                    logger.error(f"    - Error processing image {img_name}: {e}")

            # Generate triggers.json
            self.generate_ddw_triggers(metadata, extracted_images, file_output_folder)

            # Save theme.json in output folder as metadata.json for consistency
            (file_output_folder / "metadata.json").write_text(json.dumps(metadata, indent=4), encoding="utf-8")

    def generate_ddw_triggers(
        self,
        metadata: dict[str, Any],
        extracted_images: dict[int, str],
        output_folder: str | Path,
    ) -> None:
        """Construct a triggers.json based on standard day/night/sunrise/sunset intervals."""
        triggers: list[TriggerEntry] = []

        sunrise_list = metadata.get("sunriseImageList") or []
        day_list = metadata.get("dayImageList") or []
        sunset_list = metadata.get("sunsetImageList") or []
        night_list = metadata.get("nightImageList") or []

        time_blocks = [
            {"list": sunrise_list, "start": 6 * 3600, "duration": 2 * 3600},
            {"list": day_list, "start": 8 * 3600, "duration": 10 * 3600},
            {"list": sunset_list, "start": 18 * 3600, "duration": 2 * 3600},
            {"list": night_list, "start": 20 * 3600, "duration": 10 * 3600},
        ]

        for block in time_blocks:
            img_list = block["list"]
            start_secs = block["start"]
            duration = block["duration"]

            if not img_list:
                continue

            num_images = len(img_list)
            step = duration / num_images

            for idx, img_idx in enumerate(img_list):
                if img_idx not in extracted_images:
                    logger.warning(
                        f"    - Warning: Image index {img_idx} from theme list not found in extracted images"
                    )
                    continue

                time_offset = start_secs + idx * step
                time_offset = time_offset % (24 * 3600)

                time_str = seconds_to_hms(time_offset)
                image_name = extracted_images[img_idx]

                triggers.append({"time": time_str, "image": image_name})

        # Sort triggers chronologically
        triggers.sort(key=lambda x: x["time"])

        if triggers:
            triggers_path = Path(output_folder) / "triggers.json"
            triggers_file: TriggersFile = {"triggers": triggers}
            triggers_path.write_text(json.dumps(triggers_file, indent=2), encoding="utf-8")
            logger.info(f"    - Extracted all images and generated triggers at {triggers_path}")
