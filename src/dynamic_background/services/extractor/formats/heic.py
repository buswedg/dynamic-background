import ast
import base64
import json
import logging
import plistlib
import re
from pathlib import Path
from typing import Any

import pillow_heif
from PIL import Image
from pillow_heif import open_heif, register_heif_opener

from dynamic_background.core.utils import seconds_to_hms
from dynamic_background.models import TriggerEntry, TriggersFile
from dynamic_background.services.extractor.formats.base import BaseExtractor
from dynamic_background.services.extractor.image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class HEICExtractor(BaseExtractor):
    """Process and extract dynamic wallpapers from Apple HEIC/HEIF files."""

    def __init__(self, image_processor: ImageProcessor | None = None) -> None:
        super().__init__(image_processor)
        register_heif_opener()
        Image.MAX_IMAGE_PIXELS = None  # Disable decompression bomb check for large wallpapers
        pillow_heif.options.DISABLE_SECURITY_LIMITS = True  # Bypass libheif security limits

    def extract(self, file_path: str | Path, output_root: str | Path) -> None:
        """Process a single HEIC file: extract all images and metadata into a subfolder."""
        try:
            heif_file = open_heif(file_path)
            base_name = Path(file_path).stem

            file_output_folder = Path(output_root) / base_name
            file_output_folder.mkdir(parents=True, exist_ok=True)

            logger.info(f"Processing HEIC: {file_path}")
            logger.info(f"    - Found {len(heif_file)} images")

            for i, img in enumerate(heif_file):
                image = Image.frombytes(
                    img.mode,
                    img.size,
                    img.data,
                    "raw",
                    img.mode,
                    img.stride,
                )
                self.processor.process_image_from_object(image, file_output_folder, target_name=f"{base_name}_{i}")

            logger.info(f"    - Extracted all images to {file_output_folder}")

            self.extract_metadata(heif_file, file_output_folder)
            logger.info("    - Extracted metadata and generated triggers")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    def extract_metadata(self, heif_file: Any, output_folder: str | Path) -> None:
        """Extract XMP metadata and attempt to parse dynamic wallpaper solar/time info."""
        metadata = {
            "size": heif_file.size,
            "mode": heif_file.mode,
            "has_alpha": heif_file.has_alpha,
            "xmp_found": False,
        }

        xmp_data = heif_file.info.get("xmp")
        if xmp_data:
            try:
                xmp_str = xmp_data.decode("utf-8", errors="ignore") if isinstance(xmp_data, bytes) else xmp_data

                # Save raw XMP for reference
                (Path(output_folder) / "metadata.xmp").write_text(xmp_str, encoding="utf-8")

                metadata["xmp_found"] = True

                # Heuristic to find base64 encoded plists often found in dynamic wallpapers
                plist_candidates = re.findall(r"([A-Za-z0-9+/=]{100,})", xmp_str)

                for i, candidate in enumerate(plist_candidates):
                    try:
                        decoded = base64.b64decode(candidate)
                        if decoded.startswith(b"bplist") or decoded.strip().startswith(b"<?xml"):
                            try:
                                plist_data = plistlib.loads(decoded)
                                metadata[f"plist_{i}"] = plist_data

                                # Save decoded plist as a separate file
                                (Path(output_folder) / f"metadata_{i}.plist").write_bytes(decoded)
                            except Exception:
                                pass
                    except Exception:
                        pass

            except Exception as e:
                metadata["xmp_error"] = str(e)

        # Save all gathered metadata to JSON
        metadata_path = Path(output_folder) / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=4, default=str), encoding="utf-8")

        # Generate Triggers
        triggers_path = Path(output_folder) / "triggers.json"
        self.create_triggers(metadata, output_folder, triggers_path)

    def create_triggers(self, metadata: dict[str, Any], image_folder: str | Path, output_path: str | Path) -> None:
        """Generate a triggers JSON file based on the extracted HEIC metadata."""
        triggers: list[TriggerEntry] = []

        # Identify available plist entries in metadata
        keys_to_check = sorted([k for k in metadata if k.startswith("plist_")])
        if not keys_to_check:
            return

        # Use the first found plist (usually the main one)
        plist_data = metadata[keys_to_check[0]]
        if isinstance(plist_data, str):
            try:
                plist_data = ast.literal_eval(plist_data)
            except Exception as e:
                logger.error(f"    - Error parsing metadata plist: {e}")
                return

        if not plist_data or not isinstance(plist_data, dict) or ("ti" not in plist_data and "si" not in plist_data):
            return

        # Extract items mapping time/solar data to image indices
        items = plist_data.get("ti", [])
        if not items and "si" in plist_data:
            # Fallback for solar-based metadata: distribute across a 24h cycle
            si_items = plist_data["si"]
            for idx, si in enumerate(si_items):
                items.append({"t": idx / len(si_items), "i": si["i"]})

        # Build the triggers list
        base_name = Path(image_folder).name
        for item in items:
            try:
                t_val = float(item["t"])
                img_index = int(item["i"])

                total_seconds = t_val * 24 * 3600
                time_str = seconds_to_hms(total_seconds)

                image_filename = f"{base_name}_{img_index}.jpg"

                triggers.append({"time": time_str, "image": image_filename})
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"    - Skipping invalid trigger item {item}: {e}")

        # Sort triggers chronologically
        triggers.sort(key=lambda x: x["time"])

        if triggers:
            try:
                triggers_file: TriggersFile = {"triggers": triggers}
                Path(output_path).write_text(json.dumps(triggers_file, indent=2), encoding="utf-8")
            except Exception as e:
                logger.error(f"    - Error saving triggers: {e}")
