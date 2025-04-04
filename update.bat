@echo off
setlocal EnableDelayedExpansion

echo Updating Enhanced Developer's Toolkit...

REM Check if Git is installed
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Git is not installed or not in PATH. 
    echo Manual update required.
    goto :activate_venv
)

REM Check if this is a git repository
if not exist ".git" (
    echo Warning: This does not appear to be a git repository.
    echo Manual update required.
    goto :activate_venv
)

REM Pull latest changes
echo Pulling latest changes from repository...
git pull
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Failed to pull latest changes. 
    echo There may be local modifications or network issues.
)

:activate_venv
REM Activate virtual environment
if not exist "venv" (
    echo Virtual environment not found. Setting up from scratch...
    call setup.bat
    goto :eof
)

call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Update pip itself
echo Updating pip...
python -m pip install --upgrade pip

REM Update dependencies
echo Updating dependencies...
python -m pip install -r requirements.txt --upgrade

echo.
echo Update completed!
echo Run 'run_with_proxy.bat' to start the Enhanced Developer's Toolkit
echo.

pause 