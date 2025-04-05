@echo off
:: Project Chimera startup script for Windows
setlocal enabledelayedexpansion

echo Starting Project Chimera...

:: Get absolute path to project root
set PROJECT_DIR=%~dp0
set PROJECT_DIR=%PROJECT_DIR:~0,-1%
echo Project directory: %PROJECT_DIR%

:: Check if virtual environment exists
if not exist "%PROJECT_DIR%\venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found at %PROJECT_DIR%\venv\Scripts\activate.bat
    echo Please run setup.bat to create the virtual environment
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment
call "%PROJECT_DIR%\venv\Scripts\activate.bat"

:: Set Python path
set PYTHONPATH=%PROJECT_DIR%

:: Create missing schema file if needed
set SCHEMA_DIR=%PROJECT_DIR%\src\schemas
set CONTEXT_SCHEMA=%SCHEMA_DIR%\context_schemas.py

if not exist "%CONTEXT_SCHEMA%" (
    echo Creating missing context_schemas.py file...
    if not exist "%SCHEMA_DIR%" mkdir "%SCHEMA_DIR%"
    
    (
        echo """Context schemas for Chimera API."""
        echo.
        echo from typing import Dict, List, Optional, Union, Any
        echo from pydantic import BaseModel, Field
        echo.
        echo.
        echo class ContextItem^(BaseModel^):
        echo     """Base class for context items."""
        echo     type: str = Field^(..., description="Type of context item"^)
        echo     content: Any = Field^(..., description="Content of the context item"^)
        echo     metadata: Dict[str, Any] = Field^(default_factory=dict, description="Additional metadata"^)
        echo.
        echo.
        echo class CodeContext^(BaseModel^):
        echo     """Context information from code files."""
        echo     items: List[ContextItem] = Field^(default_factory=list, description="List of context items"^)
        echo     workspace_root: Optional[str] = Field^(None, description="Root directory of the workspace"^)
        echo     timestamp: Optional[str] = Field^(None, description="Timestamp when context was collected"^)
        echo.
        echo.
        echo class ContextRequest^(BaseModel^):
        echo     """Request to store context."""
        echo     context: CodeContext = Field^(..., description="Context to store"^)
        echo     session_id: str = Field^(..., description="Session identifier"^)
        echo     overwrite: bool = Field^(False, description="Whether to overwrite existing context"^)
        echo.
        echo.
        echo class ContextResponse^(BaseModel^):
        echo     """Response with stored context."""
        echo     success: bool = Field^(..., description="Whether the operation was successful"^)
        echo     context_id: Optional[str] = Field^(None, description="ID of the stored context"^)
        echo     message: Optional[str] = Field^(None, description="Additional information"^)
    ) > "%CONTEXT_SCHEMA%"
    
    echo Created context_schemas.py file
)

:: Start FastAPI web server
echo Starting Web Server...
start /b cmd /c "uvicorn src.chimera_core.api.app:app --reload --host 0.0.0.0 --port 8000"
set WEB_PID=!ERRORLEVEL!

:: Wait a moment for the server to start
timeout /t 3 > nul

:: Start MCP servers
echo Starting Code Analysis Server...
start /b cmd /c "python -m src.chimera_stdio_mcp.server --service code_analysis"
set CODE_PID=!ERRORLEVEL!

echo Starting Tools Server...
start /b cmd /c "python -m src.chimera_stdio_mcp.server --service tools"
set TOOLS_PID=!ERRORLEVEL!

echo.
echo Project Chimera Services Started:
echo.
echo Web server: http://localhost:8000
echo MCP servers running in background
echo.
echo To stop all services, press Ctrl+C

:: Wait for user to press Ctrl+C
echo Press Ctrl+C to stop all services
pause > nul

:: Cleanup
echo Stopping all services...
taskkill /f /im uvicorn.exe > nul 2>&1
taskkill /f /im python.exe > nul 2>&1

:: Deactivate virtual environment
call "%PROJECT_DIR%\venv\Scripts\deactivate.bat"

endlocal 