@echo off
echo Starting Developer's Toolkit...

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if requirements are installed
if not exist "venv\Lib\site-packages\fastapi" (
    echo Installing requirements...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to install requirements
        pause
        exit /b 1
    )
)

REM Start the server
echo Starting server...
python standalone_mcp_server.py
if %ERRORLEVEL% NEQ 0 (
    echo Error: Server failed to start
    pause
    exit /b 1
)

=== Mars Weather Agent Connection Info ===

Connection URL (click or copy to Cursor):
cursor://connect/eyJ0eXBlIjoibWNwIiwidmVyc2lvbiI6IjIwMjQtMTEtMDUiLCJlbmRwb2ludCI6Imh0dHA6Ly8xMjcuMC4wLjE6NzA3MC9tZXNzYWdlcy8iLCJpZCI6IjEyMzQ1Njc4LTkwYWItY2RlZi0xMjM0LTU2Nzg5MGFiY2RlZiIsIm5hbWUiOiJNYXJzIFdlYXRoZXIgQWdlbnQifQ==

Or run this command in your terminal:
mcp-proxy --sse-port 9999 -- python standalone_mcp_server.py

Server is running on port 9999
======================================= 

pause 