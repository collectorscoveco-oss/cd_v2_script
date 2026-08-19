@echo off
setlocal EnableExtensions
title SonarDeck Studio Launcher
cd /d "%~dp0.."

echo ========================================
echo SonarDeck Studio Launcher
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

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo ERROR: Python was not found on PATH.
  echo Run scripts\setup_windows.bat first, or install Python and enable Add to PATH.
  echo.
  pause
  exit /b 1
)

if not exist "bridge\config.json" (
  echo Creating bridge\config.json from bridge\config.example.json...
  copy "bridge\config.example.json" "bridge\config.json" >nul
)

echo Installing/updating SonarDeck Studio UI dependencies...
cd /d "%~dp0..\ui"
call npm install
if errorlevel 1 (
  echo.
  echo ERROR: npm install failed.
  pause
  exit /b 1
)
cd /d "%~dp0.."

echo Starting Python bridge API on http://127.0.0.1:8765 ...
start "SonarDeck API" cmd /k "cd /d ""%cd%"" && %PYTHON_CMD% -m bridge.web_api --host 127.0.0.1 --port 8765"

echo Starting React UI on http://127.0.0.1:5173 ...
start "SonarDeck Studio" cmd /k "cd /d ""%cd%\ui"" && npm run dev"

timeout /t 3 >nul
start http://127.0.0.1:5173

echo.
echo If the browser does not load immediately, wait 5-10 seconds and refresh.
echo Keep the two SonarDeck command windows open while using the modern UI.
echo.
pause
