@echo off
setlocal EnableExtensions
title SonarDeck Studio Native Desktop
cd /d "%~dp0.."

echo ============================================
echo SonarDeck Studio - Native Desktop Mode
echo ============================================
echo Project: %cd%
echo.

where npm >nul 2>nul
if errorlevel 1 (
  echo ERROR: npm was not found. Install Node.js LTS, then try again.
  pause
  exit /b 1
)

where cargo >nul 2>nul
if errorlevel 1 (
  echo ERROR: Rust/Cargo was not found.
  echo.
  echo Tauri needs Rust. Install it from:
  echo   https://rustup.rs
  echo.
  echo After installing Rust, close this window, open a NEW Command Prompt,
  echo then run this script again.
  pause
  exit /b 1
)

set PYTHON_CMD=
where py >nul 2>nul
if not errorlevel 1 set PYTHON_CMD=py -3
if "%PYTHON_CMD%"=="" (
  where python >nul 2>nul
  if not errorlevel 1 set PYTHON_CMD=python
)
if "%PYTHON_CMD%"=="" (
  echo ERROR: Python was not found.
  pause
  exit /b 1
)

if not exist "bridge\config.json" (
  echo Creating bridge\config.json from example...
  copy "bridge\config.example.json" "bridge\config.json" >nul
)

echo Installing/updating UI dependencies...
cd /d "%~dp0..\ui"
call npm install
if errorlevel 1 (
  echo ERROR: npm install failed.
  pause
  exit /b 1
)
cd /d "%~dp0.."

echo Stopping old SonarDeck listeners on 8765 and 5173...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8765,5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>nul

echo Starting Python bridge API on http://127.0.0.1:8765 for local access and 0.0.0.0 for LAN clients ...
start "SonarDeck API" cmd /k "cd /d ""%cd%"" && %PYTHON_CMD% -m bridge.web_api --host 0.0.0.0 --port 8765"

echo Starting native Tauri desktop app...
cd /d "%~dp0..\ui"
call npm run desktop:dev
if errorlevel 1 (
  echo.
  echo ERROR: Tauri desktop app failed to start.
  echo If this is your first time, install Rust from https://rustup.rs
  pause
  exit /b 1
)
