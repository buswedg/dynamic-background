@echo off
setlocal
cd /d "%~dp0"

set "CONFIG_ONLY="
set "DEV="
for %%a in (%*) do (
    if /i "%%~a"=="--config" set "CONFIG_ONLY=1"
    if /i "%%~a"=="--dev" set "DEV=1"
)

if defined CONFIG_ONLY goto :copy_configs

echo Checking Python...
if not defined PYTHON if exist .python set /p PYTHON=<.python
if not defined PYTHON set "PYTHON=python"
"%PYTHON%" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found ^(set PYTHON or add it to PATH^).
    exit /b 1
)
"%PYTHON%" -c "import sys; raise SystemExit(0 if (3, 11) <= sys.version_info[:2] <= (3, 14) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.11-3.14 is required.
    exit /b 1
)

echo Checking Poetry...
"%PYTHON%" -m poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Poetry not found. Install it first ^(pip install poetry^).
    exit /b 1
)

echo Configuring in-project virtualenv...
"%PYTHON%" -m poetry config virtualenvs.in-project true

echo Installing dependencies...
if defined DEV (
    "%PYTHON%" -m poetry install --with dev
) else (
    "%PYTHON%" -m poetry install
)
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    exit /b 1
)

:copy_configs
echo Copying configuration templates...
if not exist "config.toml" (
    if exist "config.dist.toml" (
        copy "config.dist.toml" "config.toml" >nul
        echo [+] Created config.toml from template.
    )
)
if not exist "schedule.json" (
    if exist "schedule.dist.json" (
        copy "schedule.dist.json" "schedule.json" >nul
        echo [+] Created schedule.json from template.
    )
)

echo.
echo [OK] Setup complete.
echo Next: review the generated config files, then launch with run.bat (see README).
endlocal
