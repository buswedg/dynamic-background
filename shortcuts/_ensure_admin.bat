@echo off

fltmc >nul 2>&1
if %errorLevel%==0 (
    exit /b 0
)

set "ELEVATED=0"
for %%a in (%*) do if "%%~a"=="-elevated" set "ELEVATED=1"

if "%ELEVATED%"=="1" (
    echo Elevation failed. UAC is likely disabled or restricted in Safe Mode.
    pause
    exit /b 1
)

echo Requesting administrator privileges...
powershell -Command "Start-Process cmd.exe -ArgumentList '/k \"\"%~1\" %* -elevated\"' -Verb RunAs"
exit /b 2
