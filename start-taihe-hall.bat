@echo off
setlocal
cd /d "%~dp0"
set PORT=4173
set URL=http://127.0.0.1:%PORT%/taihe-hall-3d-prototype.html

echo Starting Taihe Hall 3D local viewer...
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  start "Taihe Hall 3D Server" /min python -m http.server %PORT%
  timeout /t 2 >nul
  start "" "%URL%"
  echo Opened %URL%
  echo Keep this window or the server window open while viewing.
  pause
  exit /b
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  start "Taihe Hall 3D Server" /min py -m http.server %PORT%
  timeout /t 2 >nul
  start "" "%URL%"
  echo Opened %URL%
  echo Keep this window or the server window open while viewing.
  pause
  exit /b
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-taihe-hall.ps1" -Port %PORT%
