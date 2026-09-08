@echo off
setlocal
cd /d "%~dp0\.."
echo This will replace bridge\config.json with the current SonarDeck default mapping.
copy /Y bridge\config.example.json bridge\config.json
if errorlevel 1 (
  echo Failed to reset config.
  pause
  exit /b 1
)
echo Config reset complete.
pause
