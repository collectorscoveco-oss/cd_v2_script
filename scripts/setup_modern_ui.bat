@echo off
setlocal EnableExtensions
title SonarDeck Studio Setup
cd /d "%~dp0.."

echo ========================================
echo SonarDeck Studio Setup
echo Project: %cd%
echo ========================================
echo.

where npm >nul 2>nul
if errorlevel 1 (
  echo ERROR: npm was not found on PATH.
  echo Install Node.js LTS from https://nodejs.org/ then reopen Command Prompt.
  echo.
  pause
  exit /b 1
)

if not exist "bridge\config.json" (
  echo Creating bridge\config.json from bridge\config.example.json...
  copy "bridge\config.example.json" "bridge\config.json" >nul
)

echo Installing SonarDeck Studio UI dependencies...
cd /d "%~dp0..\ui"
call npm install
if errorlevel 1 (
  echo.
  echo ERROR: npm install failed.
  pause
  exit /b 1
)

echo.
echo SonarDeck Studio UI dependencies are ready.
echo Next run: scripts\run_modern_ui.bat
echo.
pause
