@echo off
setlocal EnableDelayedExpansion

echo Starting Enhanced Developer's Toolkit with MCP proxy...

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

REM Install required packages with more detailed error handling
echo Installing required packages...
python -m pip install -U pip
echo First installing core dependencies...
python -m pip install wheel setuptools --no-warn-script-location
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Failed to install core dependencies, but continuing...
)

echo Now installing remaining requirements...
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Some requirements may not have installed correctly. 
    echo We'll try to continue anyway...
    echo Installing minimum required packages individually...
    python -m pip install fastapi uvicorn jinja2
)

REM Create required directories if they don't exist
if not exist "templates" mkdir templates
if not exist "static\js" mkdir static\js
if not exist "static\css" mkdir static\css

REM Check if psutil is properly installed
python -c "import psutil" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Warning: psutil module is not properly installed. Using simplified port checker.
    python simple_port_checker.py > ports.txt
) else (
    REM Use the full port checker if psutil works
    echo Checking port availability with enhanced checker...
    python port_checker.py > ports.txt
)

REM If port checker script failed, use the simple one
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Enhanced port checker failed. Using simplified port checker.
    python simple_port_checker.py > ports.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Warning: All port checkers failed. Using hardcoded ports.
        set WEB_PORT=9991
        set MCP_PORT=9992
        goto :start_servers
    )
)

set /p WEB_PORT_LINE=<ports.txt
set /p MCP_PORT_LINE=<ports.txt
del ports.txt 2>nul

REM Extract the port numbers
echo %WEB_PORT_LINE% | findstr /C:"Web port:" >nul
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=3" %%a in ("%WEB_PORT_LINE%") do set WEB_PORT=%%a
) else (
    set WEB_PORT=9991
)

echo %MCP_PORT_LINE% | findstr /C:"MCP port:" >nul
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=3" %%a in ("%MCP_PORT_LINE%") do set MCP_PORT=%%a
) else (
    set MCP_PORT=9992
)

:start_servers
echo Web server will run on port %WEB_PORT%
echo MCP proxy will run on port %MCP_PORT%

REM Start the UI server in a new window with the determined port
start "UI Server" cmd /c "venv\Scripts\python.exe main.py --port %WEB_PORT%"

REM Wait a moment for the UI server to start
timeout /t 2 /nobreak >nul

REM Start the MCP proxy on the determined port
echo Starting MCP server with proxy on port %MCP_PORT%...
start "MCP Proxy" cmd /c "venv\Scripts\python.exe -m mcp.proxy --sse-port %MCP_PORT% -- python mcp_server.py --mcp-port %MCP_PORT%"

echo Server started successfully
echo You can now connect to the Developer's Toolkit in Cursor.
echo.

REM Show connection information
set CURSOR_URL_BASE=cursor://connect/eyJ0eXBlIjogIm1jcCIsICJ2ZXJzaW9uIjogIjIwMjQtMTEtMDUiLCAiZW5kcG9pbnQiOiAiaHR0cDovLzEyNy4wLjAuMTolTUNQX1BPUlQlL21lc3NhZ2VzLyIsICJpZCI6ICJmMDg2NTQxYi02YjcwLTRhMjAtYTFjZS05NmNhOTI3ZTBhNzQiLCAibmFtZSI6ICJFbmhhbmNlZCBEZXZlbG9wZXIncyBUb29sa2l0In0=
set CURSOR_URL=!CURSOR_URL_BASE:MCP_PORT=%MCP_PORT%!

echo Connection URL: http://127.0.0.1:%MCP_PORT%/messages/
echo CLI Command: mcp-proxy --sse-port %MCP_PORT% -- python mcp_server.py
echo Cursor URL: !CURSOR_URL!
echo.

pause 