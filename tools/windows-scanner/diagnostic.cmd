@echo off
setlocal
cd /d "%~dp0"
echo Starting Cachito BLE v6 diagnostic mode...
py -3 -u "%~dp0cachito_scan_gui_v6.py"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo Cachito exited with code %RC%.
pause
exit /b %RC%
