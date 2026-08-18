@echo off
setlocal
cd /d "%~dp0\.."
py -3 -m bridge.main
pause
