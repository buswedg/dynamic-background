import argparse

from dynamic_background import tasks
from dynamic_background.core import config
from dynamic_background.core.logger import setup_logger
from dynamic_background.core.utils import enable_ansi_utf8

enable_ansi_utf8()


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Dynamic Background Tool: Extract wallpapers or schedule themes")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to run")

    schedule_parser = subparsers.add_parser(
        "schedule", help="Scan backgrounds directory and update the scheduler registry"
    )
    schedule_parser.add_argument(
        "--backgrounds-dir",
        default=str(config.settings.backgrounds_dir),
        help="Directory containing extracted theme folders with triggers.json to scan",
    )

    extract_parser = subparsers.add_parser("extract", help="Extract dynamic wallpapers from HEIC or DDW zip packages")
    extract_parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input file path or directory containing dynamic wallpapers",
    )
    extract_parser.add_argument(
        "-o",
        "--output",
        default="images/output",
        help="Output directory root for extracted wallpaper assets",
    )

    return parser


def main() -> None:
    """Run the CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    setup_logger(verbose=args.verbose)

    if args.command == "extract":
        tasks.run_extract(args.input, args.output)
    elif args.command == "schedule":
        tasks.run_schedule_scan(args.backgrounds_dir)


if __name__ == "__main__":
    main()
