@echo off
:: Project Chimera simplified startup script for Windows
:: Created for accessibility - fewer components, clearer feedback
setlocal enabledelayedexpansion

echo ==============================================
echo    Project Chimera - Simplified Startup
echo ==============================================
echo.

:: Get absolute path to project root
set PROJECT_DIR=%~dp0
set PROJECT_DIR=%PROJECT_DIR:~0,-1%
echo [INFO] Project directory: %PROJECT_DIR%

:: Check if virtual environment exists
if not exist "%PROJECT_DIR%\venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found
    echo [HELP] Please run setup.bat first to create the environment
    echo        Or run: python -m venv venv
    echo        Then:   venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call "%PROJECT_DIR%\venv\Scripts\activate.bat"

:: Set Python path
set PYTHONPATH=%PROJECT_DIR%

:: Create/update required schema files
echo [INFO] Checking for required schema files...
set SCHEMA_DIR=%PROJECT_DIR%\src\schemas
if not exist "%SCHEMA_DIR%" mkdir "%SCHEMA_DIR%"

:: Start just the FastAPI server (most important component)
echo.
echo [INFO] Starting Web API Server only (simplified mode)...
echo [INFO] For full functionality, use start_chimera.bat instead
echo.
echo [INFO] Server starting at http://localhost:8000
echo [INFO] Press Ctrl+C to stop the server when finished
echo.

:: Start the server in the foreground for easier monitoring
uvicorn src.chimera_core.api.app:app --reload --host 0.0.0.0 --port 8000

:: Cleanup - this will run when the user presses Ctrl+C
echo.
echo [INFO] Stopping server...
call "%PROJECT_DIR%\venv\Scripts\deactivate.bat"
echo [INFO] Server stopped.

endlocal 