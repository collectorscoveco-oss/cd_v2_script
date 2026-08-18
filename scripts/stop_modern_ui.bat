@echo off
setlocal EnableExtensions
title Stop SonarDeck Studio

echo Stopping SonarDeck Studio background processes on ports 8765 and 5173...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8765,5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ } | ForEach-Object { Write-Host ('Stopping PID ' + $_); Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

echo Done.
pause
