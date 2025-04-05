@echo off
:: Project Chimera Status Tool for Windows
:: Shows running services and provides options to start/stop

setlocal enabledelayedexpansion

echo.
echo ================================================
echo           PROJECT CHIMERA STATUS TOOL          
echo ================================================
echo.

:: Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.9+
    goto :eof
)

:: Check running services
echo Checking running services...
echo.

set WEB_RUNNING=0
set CODE_RUNNING=0
set TOOLS_RUNNING=0

:: Check for Web Server
netstat -ano | findstr ":8000" >nul
if %ERRORLEVEL% EQU 0 (
    echo [RUNNING] Web Server (port 8000)
    set WEB_RUNNING=1
) else (
    echo [STOPPED] Web Server (port 8000)
)

:: Look for python processes that might be MCP servers
tasklist /fi "imagename eq python.exe" /fo list | findstr "chimera_stdio_mcp" >nul
if %ERRORLEVEL% EQU 0 (
    echo [RUNNING] MCP Server processes detected
    set CODE_RUNNING=1
) else (
    echo [STOPPED] MCP Server processes
)

echo.
echo ------------------------------------------------
echo.

:: Show options based on what's running
if %WEB_RUNNING% EQU 1 (
    echo 1. STOP all services
    echo 2. Restart all services
) else (
    echo 1. START services (simplified mode)
    echo 2. START services (full mode)
)

echo 3. Run system check
echo 4. Exit

echo.
set /p CHOICE="Enter your choice (1-4): "

if "%CHOICE%"=="1" (
    if %WEB_RUNNING% EQU 1 (
        echo Stopping all services...
        taskkill /f /im uvicorn.exe >nul 2>&1
        taskkill /f /im python.exe /fi "windowtitle eq *chimera*" >nul 2>&1
        echo Services stopped.
    ) else (
        echo Starting services in simplified mode...
        start cmd /c "easy_start.bat"
        echo Web server starting...
    )
) else if "%CHOICE%"=="2" (
    if %WEB_RUNNING% EQU 1 (
        echo Restarting all services...
        taskkill /f /im uvicorn.exe >nul 2>&1
        taskkill /f /im python.exe /fi "windowtitle eq *chimera*" >nul 2>&1
        timeout /t 2 >nul
        start cmd /c "start_chimera.bat"
        echo Services restarting...
    ) else (
        echo Starting services in full mode...
        start cmd /c "start_chimera.bat"
        echo All services starting...
    )
) else if "%CHOICE%"=="3" (
    echo Running system check...
    python check_system.py
    pause
) else if "%CHOICE%"=="4" (
    echo Exiting...
    goto :eof
) else (
    echo Invalid choice.
)

echo.
echo Press any key to return to the status screen...
pause >nul
cls
%0

endlocal 