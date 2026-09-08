@echo off
setlocal
cd /d "%~dp0\.."
if "%~1"=="" (
  echo Usage: scripts\simulate_event.bat BTN_05_PRESS
  echo Example: scripts\simulate_event.bat BTN_08_LONG
  pause
  exit /b 1
)
py -3 -m bridge.main --dry-event %*
pause
