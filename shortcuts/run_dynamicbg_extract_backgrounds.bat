@echo off
cd /d "%~dp0.."
call run.bat extract -i images\input -o images\output
pause
