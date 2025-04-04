@echo off
echo Starting Chimera Core Server...
cd %~dp0\..\..
python scripts/start_core_server.py
pause 