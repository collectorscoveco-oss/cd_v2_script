@echo off
setlocal
cd /d "%~dp0\.."
py -3 -m bridge.virtual_deck
if errorlevel 1 pause
