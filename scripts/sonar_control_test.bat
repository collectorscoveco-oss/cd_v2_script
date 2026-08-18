@echo off
setlocal
cd /d "%~dp0\.."
py -3 -m bridge.tools_sonar_control_test %*
pause
