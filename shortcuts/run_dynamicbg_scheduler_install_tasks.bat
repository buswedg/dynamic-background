@echo off

call "%~dp0_ensure_admin.bat" "%~f0" %*
if %errorlevel% neq 0 exit /b

set "SCRIPT_PATH=%~dp0..\Install-Task.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_PATH%"
pause
