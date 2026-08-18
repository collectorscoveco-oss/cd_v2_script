@echo off
setlocal
cd /d "%~dp0.."
if not exist "ui\node_modules" (
  echo Installing SonarDeck Studio UI dependencies...
  cd /d "%~dp0..\ui"
  call npm install
  if errorlevel 1 exit /b 1
  cd /d "%~dp0.."
)
echo SonarDeck Studio UI dependencies are ready.
pause
