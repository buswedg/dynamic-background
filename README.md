# Dynamic Background

Schedule and synchronize time-of-day dynamic wallpapers on Windows using Task Scheduler, with a built-in extractor utility to unpack macOS HEIC wallpapers and WinDynamicDesktop DDW themes.

## Features

- **Task Scheduler Integration** — Automatically keeps wallpapers synchronized throughout the day based on custom time-based triggers.
- **Simple Config Updates** — Scheduled tasks call the orchestrator dynamically at runtime, so `schedule.json` changes apply without re-registering Task Scheduler jobs.
- **HEIC & DDW Extraction** — Built-in utility to extract images, metadata, and generate compatible time-of-day triggers from macOS `.heic` and WinDynamicDesktop `.ddw`/`.zip` wallpaper packages.
- **Windows PowerShell Hybrid** — Python owns configuration generation and media extraction; PowerShell owns all OS work (Task Scheduler, wallpaper).

---

## Requirements

**Supported platforms: Windows only.** Wallpaper scheduling relies on Windows Task Scheduler and the `user32` wallpaper API.

- [Python](https://www.python.org/) 3.11–3.13 (in PATH, Direct CLI)
- [Poetry](https://python-poetry.org/) (installed globally)
- **Windows**: Task Scheduler + `user32` wallpaper API for scheduling (the Python side alone can also run on Linux for extraction only).

---

## Installation

### Direct CLI/TUI

Run `setup.bat` from the repo root. It will:
- Copy the `.dist` config templates into live files for you (see table below)
- Create a local virtual environment (`.venv/`)
- Install all runtime dependencies

For development tooling (pytest, ruff), run `setup.bat --dev` instead.

| Template | Live File | Purpose |
|----------|-----------|---------|
| `config.dist.toml` | `config.toml` | Scheduler background directories and image quality settings. |
| `schedule.dist.json` | `schedule.json` | Active time-of-day weekly scheduler mappings. |

---

## Configuration

No `.env` files or environment variables are read — all settings live in `config.toml` (plus the `schedule.json` schedule and per-theme `triggers.json` files).

### 1. Application Settings (`config.toml`)

Edit the `config.toml` at the project root:

| Key | Purpose |
|-----|---------|
| `[scheduler] backgrounds_dir` | Directory containing extracted wallpapers for background scheduling (absolute, or relative to the project root). |
| `[extractor] target_aspect` | Target aspect ratio for cropping (`null` disables cropping). |
| `[extractor] force_resolution` | Force images to `[width, height]` (`null` keeps the original). |
| `[extractor] jpeg_quality` | JPEG compression quality (1-100; `null` disables re-compression). |

### 2. Theme Structure (`triggers.json`)

For the scheduler to recognize a theme, it must be a folder containing a `triggers.json` configuration file and its referenced images:

```text
BACKGROUNDS_DIR/
└── BackgroundName/
    ├── triggers.json
    ├── Image_1.jpg
    ├── Image_2.jpg
    └── ...
```

`triggers.json` defines when each image is applied during the day; times use the `HH:MM:SS` 24-hour clock:

```json
{
  "triggers": [
    { "time": "00:00:00", "image": "Fuji_1.jpg" },
    { "time": "05:00:00", "image": "Fuji_0.jpg" },
    { "time": "12:00:00", "image": "Fuji_3.jpg" }
  ]
}
```

### 3. Weekly Schedule (`schedule.json`)

Edit the `schedule.json` at the project root to map days of the week to theme names:

```json
{
  "schedule": {
    "Mon": "Fuji",
    "Fri": "Monterey"
  }
}
```

Any days not specified default to picking a random theme from the registry (stable for that day).

---

## Usage

### Launcher

`run.bat` with no args (or `run.bat help`) shows the full usage. Run commands in the local virtual environment with `run.bat <command>`:

```powershell
.\run.bat schedule
.\run.bat extract -i images/input -o images/output
```

Re-run `schedule` any time you add or remove themes to rebuild the registry (`data/backgrounds.json`), then map the week in `schedule.json`.

### PowerShell Automation

This project is a Windows hybrid: Python owns configuration generation and media extraction, while PowerShell owns all OS work (Task Scheduler, wallpaper). Three scripts are shipped:

| Script | Purpose |
|--------|---------|
| `Install-Task.ps1` | Registers the `DynamicBackground-LogOnOrSchedule-Run` Task Scheduler job (run once from an elevated PowerShell terminal). |
| `Background-Scheduler.ps1` | The scheduled task's entry point — coordinates theme selection and background application at runtime. |
| `Set-Background.ps1` | Applies a single theme's time-of-day triggers to the desktop wallpaper. |

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install-Task.ps1
```

---

## CLI Reference

### Top-Level Commands

| Command | Description |
|---------|-------------|
| `schedule [--backgrounds-dir <dir>]` | Scan the backgrounds directory and rebuild the theme registry (`data/backgrounds.json`). |
| `extract -i <path> [-o <dir>]` | Extract dynamic wallpapers from HEIC or DDW/zip packages into the output directory (default `images/output`). |

Global flags: `-v/--verbose` enables DEBUG logging.
