@echo off
echo Running Enhanced Developer's Toolkit Environment Fix...

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Run the environment fix script
python fix_environment.py

REM Pause at the end
pause 