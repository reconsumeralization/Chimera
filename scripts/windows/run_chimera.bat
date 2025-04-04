@echo off
:: Project Chimera startup script for Windows
echo Starting Project Chimera...

:: Check for Python environment
if not exist venv\Scripts\activate.bat (
    echo Error: Virtual environment not found. Please run setup.bat first.
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Set paths
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..
set RUN_SCRIPT=%PROJECT_ROOT%\scripts\common\run_all.py

:: Handle command line arguments
set ARGS=

:: Check for --enable-data-collection flag
if "%1"=="--enable-data-collection" (
    set ARGS=%ARGS% --enable-data-collection
    shift
)

:: Check for --no-ui flag
if "%1"=="--no-ui" (
    set ARGS=%ARGS% --no-ui
    shift
)

:: Check for --no-browser flag
if "%1"=="--no-browser" (
    set ARGS=%ARGS% --no-browser
    shift
)

:: Check for --log-level flag
if "%1"=="--log-level" (
    set ARGS=%ARGS% --log-level=%2
    shift
    shift
)

:: Run the Python script
echo Running: python %RUN_SCRIPT% %ARGS%
python %RUN_SCRIPT% %ARGS%

:: Deactivate virtual environment
call venv\Scripts\deactivate.bat 