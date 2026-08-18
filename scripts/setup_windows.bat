@echo off
setlocal
cd /d "%~dp0\.."
py -3 -m pip install -r bridge\requirements.txt
if errorlevel 1 pause
