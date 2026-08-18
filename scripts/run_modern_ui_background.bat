@echo off
setlocal EnableExtensions
title SonarDeck Studio Background Launcher
cd /d "%~dp0.."

echo Starting SonarDeck Studio in the background...
cscript //nologo "%~dp0run_modern_ui_background.vbs"
if errorlevel 1 (
  echo.
  echo ERROR: SonarDeck Studio background launch failed.
  echo Try scripts\run_modern_ui.bat to see detailed errors.
  echo.
  pause
  exit /b 1
)

echo.
echo SonarDeck Studio is starting in the background.
echo Browser URL: http://127.0.0.1:5173
echo To stop it later, run: scripts\stop_modern_ui.bat
timeout /t 4 >nul
