@echo off
setlocal
cd /d "%~dp0.."
if not exist "ui\node_modules" (
  echo First run: installing SonarDeck Studio UI dependencies...
  cd /d "%~dp0..\ui"
  call npm install
  if errorlevel 1 exit /b 1
  cd /d "%~dp0.."
)
start "SonarDeck API" cmd /k "cd /d %cd% && py -m bridge.web_api --host 127.0.0.1 --port 8765"
cd /d "%~dp0..\ui"
start "SonarDeck Studio" cmd /k "npm run dev"
timeout /t 2 >nul
start http://127.0.0.1:5173
