@echo off
setlocal EnableExtensions
title SonarDeck Studio Release
cd /d "%~dp0.."

echo ========================================
echo SonarDeck Studio Release
echo Project: %cd%
echo ========================================
echo.

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo ERROR: Python was not found on PATH.
  echo Install Python 3.11+ and ensure Add to PATH is enabled.
  echo.
  pause
  exit /b 1
)

if not exist "bridge\config.json" (
  echo Creating bridge\config.json from bridge\config.example.json...
  copy "bridge\config.example.json" "bridge\config.json" >nul
)

echo Stopping any old SonarDeck listeners on port 8765...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ } | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>nul

echo Starting release server on http://127.0.0.1:8765 ...
start "SonarDeck Release" cmd /k "cd /d ""%cd%"" && %PYTHON_CMD% -m bridge.web_api --host 0.0.0.0 --port 8765"

timeout /t 3 >nul
start http://127.0.0.1:8765

echo.
echo If the browser does not load immediately, wait 5-10 seconds and refresh.
echo Use the browser URL above on another device to open the same release on your LAN.
echo.
pause
