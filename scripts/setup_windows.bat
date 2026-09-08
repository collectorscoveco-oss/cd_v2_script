@echo off
setlocal
cd /d "%~dp0\.."

echo ========================================
echo SonarDeck Windows setup
echo ========================================

echo Installing Python requirements...
py -3 -m pip install -r bridge\requirements.txt
if errorlevel 1 (
  echo.
  echo Setup failed while installing requirements.
  pause
  exit /b 1
)

if not exist bridge\config.json (
  echo Creating bridge\config.json from default template...
  copy bridge\config.example.json bridge\config.json >nul
) else (
  echo bridge\config.json already exists. Keeping your local config.
)

echo.
echo Setup complete.
echo.
echo Next steps:
echo   1. Open SteelSeries GG / Sonar.
echo   2. Run scripts\run_virtual_deck.bat now to test without Arduino.
echo   3. When Arduino arrives, flash firmware\sonardeck_v1\sonardeck_v1.ino.
echo   4. Then run scripts\run_bridge.bat for hardware control.
echo.
pause
